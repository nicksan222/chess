"""Proposed off-board wire paths, anchored to exported PCB contacts and case parts.

Waypoints describe clearance routes, not a supplier cable model. Cut lengths
include service slack; its final dressing and bend radii remain physical checks.
"""

from cad.harness.base.pcb import PcbSnapshot
from shared import dimensions as d
from shared.dimensions import rear_panel as rear
from shared.electronics.harness import HarnessWire

Point3D = tuple[float, float, float]


def wire_route(wire: HarnessWire, pcb: PcbSnapshot) -> tuple[Point3D, ...]:
    connector = next(part for part in pcb.parts if part.reference == wire.connector)
    if connector.wire_exit_mm is None:
        raise ValueError(f"{connector.reference} must declare its wire exit")
    exit_y, exit_height = connector.wire_exit_mm
    contact_x = connector.pin_positions_mm[wire.cavity][0]
    cavity = int(wire.cavity) - 1
    if wire.connector == "J2":
        start = (
            contact_x,
            connector.position_mm[1] - exit_y,
            d.PCB_TOP_Z_MM + exit_height / 2,
        )
        # Approach the solder pads from the module's left edge, keeping the
        # conductor outside the underside components until its endpoint.
        pad_x, pad_y = d.PANEL_OLED_PAD_POSITIONS_MM[cavity]
        target_x = d.PANEL_OLED_CENTER_MM[0] + pad_x
        target_y = d.PANEL_OLED_CENTER_MM[1] + pad_y
        lane_x = target_x - 8 - cavity * 2
        route_y = start[1] - 3 - (3 - cavity) * 2
        # Separate crossing approaches vertically, below the plate and outside
        # the module's SMD envelope. Each wire then rises into its real pad.
        route_z = d.PCB_TOP_Z_MM + 0.5 + cavity * 0.9
        return (
            start,
            (contact_x, route_y, start[2]),
            (contact_x, route_y, route_z),
            (lane_x, route_y, route_z),
            (lane_x, target_y, route_z),
            (target_x, target_y, d.PANEL_OLED_PCB_BOTTOM_Z_MM - 0.8),
            (target_x, target_y, d.PANEL_OLED_PCB_BOTTOM_Z_MM),
        )
    if wire.connector == "J4":
        start = (
            contact_x,
            connector.position_mm[1] + exit_y,
            d.PCB_UNDERSIDE_Z_MM - exit_height / 2,
        )
        z = d.CASE_REAR_APERTURE_CENTER_Z_MM
        route_y = start[1] + 3
        if wire.far_part == "BARREL_JACK":
            target = (
                d.CASE_JACK_APERTURE_CENTER_X_MM + (-1.5 if cavity == 0 else 1.5),
                rear.REAR_PANEL_Y_MM
                - d.CASE_JACK_PANEL_THICKNESS_MM
                - rear.JACK_BODY_MM[0]
                - 0.1,
                z,
            )
        else:
            target = (
                d.CASE_ROCKER_APERTURE_CENTER_X_MM
                + (
                    -rear.ROCKER_TERMINAL_PITCH_MM / 2
                    if cavity == 2
                    else rear.ROCKER_TERMINAL_PITCH_MM / 2
                ),
                rear.REAR_PANEL_Y_MM
                - rear.ROCKER_BODY_MM[1]
                - rear.ROCKER_TERMINAL_LENGTH_MM
                - rear.ROCKER_RECEPTACLE_MM[1]
                - 0.1,
                z,
            )
        # Return conductors pass below their paired wire before rising to the terminal.
        route_z = z - 3.0 if cavity in (1, 3) else z
        if wire.far_part == "POWER_SWITCH":
            side_x = (
                d.CASE_ROCKER_APERTURE_CENTER_X_MM
                - rear.ROCKER_BODY_MM[0] / 2
                - 4
                - (cavity - 2) * 3
            )
            approach_y = target[1] - 3
            exit_y = start[1] + 3 + (cavity - 2) * 3
            return (
                start,
                (contact_x, exit_y, start[2]),
                (contact_x, exit_y, route_z),
                (side_x, exit_y, route_z),
                (side_x, approach_y, route_z),
                (target[0], approach_y, route_z),
                target,
            )
        points = (
            start,
            (contact_x, start[1] + 3, route_z),
            (contact_x, route_y, route_z),
            (target[0], route_y, route_z),
            target,
        )
        return tuple(
            point for i, point in enumerate(points) if i == 0 or point != points[i - 1]
        )
    raise ValueError(f"No mechanical wire path for {wire.connector}")
