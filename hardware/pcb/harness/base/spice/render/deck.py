"""Assemble a validated registry into an executable ngspice circuit file."""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

from ...connections import Endpoint, NetConnection
from ...net import Net
from ...registry import BoardRegistry
from .analysis import render_analysis
from .measurement import render_measurement
from .model import render_model
from .nodes import NodeMap
from .number import spice_number
from .source import render_source
from .state import render_state


def render_deck(board: BoardRegistry, scenario_name: str) -> str:
    """Produce one self-checking ngspice deck from board and scenario declarations.

    Validation runs first, so every source net and measured endpoint is known.
    Each component must supply an electrical model supported by the converter;
    an unsupported part fails rather than disappearing from the simulation.
    The emitted control block measures every requirement for this scenario and
    exits with failure when a result falls outside its inclusive pass band.
    """
    scenario = board.scenario(scenario_name)
    board.validate()
    assignments = {
        endpoint: connection
        for component in board.components()
        for endpoint, connection in component.pin_connections()
    }
    net_by_endpoint = {
        endpoint: connection.net
        for endpoint, connection in assignments.items()
        if isinstance(connection, NetConnection)
    }
    nodes = NodeMap(tuple(set(net_by_endpoint.values())), scenario.ground_net)
    rows = [
        f"Harness scenario: {scenario.name}",
        *nodes.comments(),
        f".temp {spice_number(scenario.temperature_celsius)}",
        *(render_source(source, nodes) for source in scenario.sources),
    ]
    selected = board.components()
    if scenario.component_references is not None:
        references = set(scenario.component_references)
        if not references or len(references) != len(scenario.component_references):
            raise ValueError(
                "simulation component selection must be nonempty and unique"
            )
        if references - {part.reference for part in selected}:
            raise ValueError("simulation selection contains unknown components")
        selected = tuple(part for part in selected if part.reference in references)
        rows.append(
            "* Explicit component scope: "
            + ", ".join(part.reference for part in selected)
        )
    states = {state.reference: state for state in scenario.states}
    if len(states) != len(scenario.states) or states.keys() - {
        part.reference for part in selected
    }:
        raise ValueError("state stimuli must uniquely name selected components")
    overrides = {
        (override.reference, override.parameter.name): override.parameter
        for override in scenario.model_overrides
    }
    if len(overrides) != len(scenario.model_overrides) or any(
        reference not in {part.reference for part in selected}
        for reference, _ in overrides
    ):
        raise ValueError("parameter corners must uniquely name selected components")
    for component in selected:
        model = component.simulation_model()
        if model is None:
            raise ValueError(f"{component.reference}: no SPICE model declared")
        if any(
            name not in {parameter.name for parameter in model.parameters}
            for reference, name in overrides
            if reference == component.reference
        ):
            raise ValueError("unknown model parameter corner")
        model = replace(
            model,
            parameters=tuple(
                overrides.get((component.reference, parameter.name), parameter)
                for parameter in model.parameters
            ),
        )
        if model.key in {"open_drain_sensor", "button_contact"}:
            rows.append(
                render_state(component.reference, states.get(component.reference))
            )
        elif component.reference in states:
            raise ValueError(
                f"{component.reference}: model does not support on/off stimuli"
            )
        terminal_nets: list[Net] = []
        for pin in model.terminals:
            endpoint = Endpoint(component.reference, str(pin))
            if endpoint not in net_by_endpoint:
                raise ValueError(
                    f"{component.reference}/{pin}: model terminal is not connected"
                )
            terminal_nets.append(net_by_endpoint[endpoint])
        rows.append(
            render_model(component.reference, model, tuple(terminal_nets), nodes)
        )
    rows.extend(
        (render_analysis(scenario.analysis), ".control", "set numdgt=15", "run")
    )
    controls: list[str] = []
    seen: set[str] = set()
    for reference, requirement in board.spice_requirements():
        if requirement.scenario != scenario.name:
            continue
        index = sum(
            1 for earlier in seen if earlier.startswith(f"result_{reference.lower()}_")
        )
        result = f"result_{reference.lower()}_{index}"
        if not re.fullmatch(r"result_[a-z0-9_]+", result) or result in seen:
            raise ValueError(f"unsafe or duplicate SPICE result name: {result}")
        seen.add(result)
        controls.append(
            render_measurement(
                result, requirement, scenario.analysis, net_by_endpoint, nodes
            )
        )
        controls.append(f"print {result}")
        minimum, maximum = requirement.allowed.minimum, requirement.allowed.maximum
        # Stop ngspice when the measured value lies outside the inclusive band.
        # This proves only that the selected simulator model met this assertion.
        controls.extend(
            (
                f"if {result} < {spice_number(minimum)}",
                f'echo "ASSERTION FAILED: {result} below {spice_number(minimum)}"',
                "quit 1",
                "end",
                f"if {result} > {spice_number(maximum)}",
                f'echo "ASSERTION FAILED: {result} above {spice_number(maximum)}"',
                "quit 1",
                "end",
            )
        )
    rows.extend((*controls, "quit 0", ".endc", ".end", ""))
    return "\n".join(rows)


def write_deck(board: BoardRegistry, scenario_name: str, path: Path) -> Path:
    """Write the generated text to a `.cir` file and return its path.

    Writing does not run ngspice. A runner may use the file independently;
    verification must inspect ngspice's exit code and measured values.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_deck(board, scenario_name))
    return path
