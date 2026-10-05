"""Offline regressions: no provider process, model request or real session mutation."""

import argparse
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

TEAM = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, TEAM / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


agents = load("agents")
usage = load("usage")
setup = load("setup")


def options(**overrides):
    values = {
        "command": "up",
        "roles": [],
        "session": None,
        "plugin": False,
        "fresh": False,
        "no_attach": True,
        "dry_run": False,
        "dangerous": False,
        "harness": None,
    }
    return argparse.Namespace(**(values | overrides))


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fleet = agents.Fleet(options())
        self.fleet.state = Path(self.temp.name) / "state"
        self.addCleanup(self.fleet.unlock)
        self.start_result = SimpleNamespace(returncode=0, stdout="", stderr="")

    def fake_up(self, existing=(), workspace="ws"):
        fleet = self.fleet
        fleet.doctor = Mock()
        fleet.ensure_server = Mock()
        fleet.workspace_id = Mock(return_value=workspace)
        fleet.herdr_json = Mock(return_value={"result": {"agents": list(existing)}})
        fleet.herdr_command = Mock(return_value=SimpleNamespace(returncode=0))
        fleet.start_role = Mock()
        return fleet

    def test_default_roster_and_role_files(self):
        self.assertEqual(
            {role for role, _ in self.fleet.selected_roles()},
            {
                "lead",
                "developer",
                "firmware-engineer",
                "hardware-engineer",
                "mechanical-engineer",
                "qa",
                "reviewer",
                "pushback",
            },
        )
        self.assertEqual(
            set(self.fleet.roles) - set(self.fleet.defaults),
            {
                "manufacturing-engineer",
                "test-engineer",
                "devops-engineer",
                "pm",
                "upgrade-reviewer",
                "pr-maker",
            },
        )
        self.assertEqual(self.fleet.maximum - len(self.fleet.defaults), 2)
        self.assertEqual(
            {path.stem for path in (TEAM / "roles").glob("*.md")},
            set(self.fleet.roles),
        )
        self.assertTrue(
            all(work["harness"] == "claude" for work in self.fleet.kinds.values())
        )

    def test_invalid_session_and_unknown_role(self):
        for session in ("../escape", "", "-bad", "x" * 65):
            with self.subTest(session=session), self.assertRaises(agents.LauncherError):
                agents.Fleet(options(session=session))
        with self.assertRaisesRegex(agents.LauncherError, "unknown agent"):
            agents.Fleet(options(roles=["missing"]))

    def test_fresh_and_reset_reject_partial_selectors(self):
        for override in ({"fresh": True}, {"command": "reset"}):
            with (
                self.subTest(override=override),
                self.assertRaises(agents.LauncherError),
            ):
                agents.Fleet(options(roles=["lead"], **override))

    def test_dry_run_never_runs_preflight_or_creates_state(self):
        self.fleet.options.dry_run = True
        self.fleet.doctor = Mock(side_effect=AssertionError("preflight called"))
        with contextlib.redirect_stdout(io.StringIO()):
            self.fleet.up()
        self.assertFalse(self.fleet.state.exists())

    def test_requested_cap_checked_before_preflight(self):
        self.fleet.options.roles = list(self.fleet.roles)
        self.fleet.doctor = Mock()
        with self.assertRaisesRegex(agents.LauncherError, "max_agents"):
            self.fleet.up()
        self.fleet.doctor.assert_not_called()

    def test_incremental_starts_cannot_exceed_cap(self):
        existing = [
            {"name": name, "workspace_id": "ws"}
            for name in self.fleet.defaults + ["test-engineer", "devops-engineer"]
        ]
        fleet = self.fake_up(existing)
        fleet.options.roles = ["pr-maker"]
        with self.assertRaisesRegex(agents.LauncherError, "MAX_AGENTS"):
            fleet.up()
        fleet.start_role.assert_not_called()
        fleet.herdr_command.assert_not_called()

    def test_foreign_role_conflict_does_not_mutate(self):
        fleet = self.fake_up([{"name": "lead", "workspace_id": "other"}])
        with self.assertRaisesRegex(agents.LauncherError, "another workspace"):
            fleet.up()
        fleet.herdr_command.assert_not_called()

    def test_existing_roles_reused_and_lock_released(self):
        existing = [
            {"name": name, "workspace_id": "ws"} for name in self.fleet.defaults
        ]
        fleet = self.fake_up(existing)
        with contextlib.redirect_stdout(io.StringIO()):
            fleet.up()
        fleet.start_role.assert_not_called()
        self.assertIsNone(fleet.lockfile)
        self.assertEqual(fleet.state.stat().st_mode & 0o777, 0o700)

    def test_mutation_lock_is_exclusive(self):
        self.fleet.lock()
        other = agents.Fleet(options())
        other.state = self.fleet.state
        self.addCleanup(other.unlock)
        with self.assertRaisesRegex(agents.LauncherError, "another launcher"):
            other.lock()

    def test_claude_argv_and_private_brief(self):
        self.fleet.lock()
        self.fleet.herdr_command = Mock(return_value=self.start_result)
        with contextlib.redirect_stdout(io.StringIO()):
            self.fleet.start_role("developer", "build", "pane")
        argv = self.fleet.herdr_command.call_args.args
        self.assertIn("--append-system-prompt-file", argv)
        self.assertIn("sonnet", argv)
        self.assertNotIn("--dangerously-skip-permissions", argv)
        prompt = self.fleet.state / "developer.md"
        self.assertEqual(prompt.stat().st_mode & 0o777, 0o600)
        self.assertIn("Herdr session: chess.", prompt.read_text())

    def test_codex_blocked_brief_keeps_startup_pending(self):
        self.fleet.lock()
        self.fleet.kinds["build"] = {
            "harness": "codex",
            "model": "-",
            "effort": "medium",
        }
        blocked = SimpleNamespace(
            returncode=1, stdout="", stderr='{"error":{"code":"agent_blocked"}}'
        )
        self.fleet.herdr_command = Mock(side_effect=[self.start_result, blocked])
        with self.assertRaises(agents.StartupPending):
            self.fleet.start_role("developer", "build", "new")
        self.assertEqual(
            self.fleet.herdr_command.call_args.args[:2], ("agent", "prompt")
        )

    def test_permission_bypass_is_explicit(self):
        self.fleet.lock()
        self.fleet.options.dangerous = True
        self.fleet.herdr_command = Mock(return_value=self.start_result)
        with contextlib.redirect_stdout(io.StringIO()):
            self.fleet.start_role("developer", "build", "pane")
        self.assertIn(
            "--dangerously-skip-permissions", self.fleet.herdr_command.call_args.args
        )

    def test_codex_adapter_sends_brief_after_start(self):
        self.fleet.lock()
        self.fleet.kinds["build"] = {
            "harness": "codex",
            "model": "-",
            "effort": "medium",
        }
        self.fleet.validate()
        self.fleet.herdr_command = Mock(return_value=self.start_result)
        with contextlib.redirect_stdout(io.StringIO()):
            self.fleet.start_role("developer", "build", "pane")
        start, prompt = self.fleet.herdr_command.call_args_list
        self.assertIn("codex", start.args)
        self.assertNotIn("--model", start.args)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", start.args)
        self.assertEqual(prompt.args[:3], ("agent", "prompt", "developer"))

    def test_pi_harness_overrides_kind_with_brief_and_no_subagents(self):
        self.fleet.lock()
        self.fleet.harness = "pi"
        self.fleet.options.dangerous = True
        self.fleet.herdr_command = Mock(return_value=self.start_result)
        with contextlib.redirect_stdout(io.StringIO()):
            self.fleet.start_role("developer", "build", "pane")
        argv = self.fleet.herdr_command.call_args.args
        self.assertEqual(argv[argv.index("--kind") + 1], "pi")
        self.assertEqual(
            argv[argv.index("--append-system-prompt") + 1],
            str(self.fleet.state / "developer.md"),
        )
        self.assertEqual(argv[argv.index("--exclude-tools") + 1], "subagent")
        self.assertEqual(argv[argv.index("--thinking") + 1], "medium")
        self.assertNotIn("--model", argv)
        self.assertNotIn("sonnet", argv)
        self.assertFalse(any(arg.startswith("--dangerously") for arg in argv))
        self.assertEqual(self.fleet.herdr_command.call_count, 1)

    def test_picker_selects_harness_only_when_interactive(self):
        tty = Mock(isatty=Mock(return_value=True))
        with (
            patch.object(agents.sys, "stdin", tty),
            patch.object(agents.sys, "stdout", tty),
            patch("builtins.input", side_effect=["9", "2"]),
            patch("builtins.print"),
        ):
            self.fleet.choose_harness()
        self.assertEqual(self.fleet.harness, "pi")
        self.assertEqual(self.fleet.settings("review")["harness"], "pi")

        fleet = agents.Fleet(options())
        with patch("builtins.input") as prompt:
            fleet.choose_harness()  # unittest stdin/stdout are not both terminals
        prompt.assert_not_called()
        self.assertEqual(fleet.settings("build")["model"], "sonnet")

    def test_picker_enter_keeps_fleet_defaults_and_eof_aborts(self):
        tty = Mock(isatty=Mock(return_value=True))
        with (
            patch.object(agents.sys, "stdin", tty),
            patch.object(agents.sys, "stdout", tty),
            patch("builtins.print"),
        ):
            with patch("builtins.input", return_value=""):
                self.fleet.choose_harness()
            self.assertIsNone(self.fleet.harness)
            with (
                patch("builtins.input", side_effect=EOFError),
                self.assertRaisesRegex(agents.LauncherError, "no harness chosen"),
            ):
                self.fleet.choose_harness()

    def test_doctor_checks_pi_login_without_model_request(self):
        self.fleet.validate_container = Mock()
        self.fleet.harness = "pi"
        ready = SimpleNamespace(returncode=0, stdout='{"status":"ready"}')
        with (
            patch.object(agents.shutil, "which", return_value="/bin/tool"),
            patch.object(agents, "call", return_value=ready) as call,
            patch.object(self.fleet, "pi_provider", return_value="openai-codex"),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.fleet.doctor()
        self.assertEqual(
            [item.args[0] for item in call.call_args_list],
            [
                ["herdr", "--version"],
                ["pi", "--version"],
                ["pi", "auth", "check", "--provider", "openai-codex", "--json"],
            ],
        )
        missing = SimpleNamespace(returncode=1, stdout='{"status":"missing"}')
        with (
            patch.object(agents.shutil, "which", return_value="/bin/tool"),
            patch.object(agents, "call", return_value=missing),
            patch.object(self.fleet, "pi_provider", return_value="openai-codex"),
            contextlib.redirect_stdout(io.StringIO()),
            self.assertRaisesRegex(agents.LauncherError, "Pi is not signed in"),
        ):
            self.fleet.doctor()

    def test_plugin_workspace_guard(self):
        self.fleet.plugin = True
        with (
            patch.dict(os.environ, {"HERDR_WORKSPACE_ID": "other"}),
            self.assertRaisesRegex(agents.LauncherError, "did not originate"),
        ):
            self.fleet.guard_workspace("ws")

    def test_wrong_plugin_rejected_before_transport(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(agents, "call") as call,
        ):
            with self.assertRaisesRegex(agents.LauncherError, "not chess.team"):
                agents.Fleet(options(plugin=True))
            call.assert_not_called()

    def test_stop_selected_role_does_not_close_foreign_pane(self):
        fleet = self.fake_up()
        fleet.options.roles = ["developer"]
        fleet.validate_container = Mock()
        fleet.server_running = Mock(return_value=True)
        fleet.herdr_json.return_value = {
            "result": {
                "agents": [
                    {"name": "developer", "workspace_id": "ws", "pane_id": "ours"},
                    {"name": "developer", "workspace_id": "other", "pane_id": "theirs"},
                ]
            }
        }
        fleet.down()
        fleet.herdr_command.assert_called_once_with("pane", "close", "ours")

    def test_failed_start_closes_only_new_pane(self):
        fleet = self.fake_up()
        fleet.options.roles = ["developer"]
        fleet.herdr_json.side_effect = [
            {"result": {"agents": []}},
            {"result": {"root_pane": {"pane_id": "new"}}},
        ]
        fleet.start_role.side_effect = agents.LauncherError("provider failed")
        with (
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(agents.LauncherError),
        ):
            fleet.up()
        fleet.herdr_command.assert_called_with("pane", "close", "new", check=False)

    def test_doctor_only_uses_version_and_auth_status(self):
        self.fleet.validate_container = Mock()
        auth = SimpleNamespace(returncode=0, stdout='{"loggedIn":true}')
        with (
            patch.object(agents.shutil, "which", return_value="/bin/tool"),
            patch.object(agents, "call", return_value=auth) as call,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.fleet.doctor()
        self.assertEqual(
            [item.args[0] for item in call.call_args_list],
            [
                ["herdr", "--version"],
                ["claude", "--version"],
                ["claude", "auth", "status"],
            ],
        )

    def test_invalid_configuration_fails_before_mutation(self):
        cases = [
            ("defaults", "lead", "nonempty list"),
            ("defaults", ["lead", "lead"], "duplicate"),
            ("defaults", ["unknown"], "unknown default"),
            ("roles", {"lead": []}, "roles must map"),
            ("kinds", [], "kinds must map"),
            ("maximum", True, "positive"),
        ]
        for field, value, message in cases:
            fleet = agents.Fleet(options())
            setattr(fleet, field, value)
            with (
                self.subTest(field=field, value=value),
                self.assertRaisesRegex(agents.LauncherError, message),
            ):
                fleet.validate()

    def test_invalid_provider_and_effort_are_rejected(self):
        for settings in (
            {"harness": "unknown", "model": "-", "effort": "medium"},
            {"harness": "claude", "model": "", "effort": "medium"},
            {"harness": "claude", "model": "sonnet", "effort": "unsupported"},
        ):
            self.fleet.kinds["build"] = settings
            with (
                self.subTest(settings=settings),
                self.assertRaises(agents.LauncherError),
            ):
                self.fleet.validate()

    def test_hardware_role_brief_contains_interface_and_evidence_contracts(self):
        self.fleet.lock()
        self.fleet.herdr_command = Mock(return_value=self.start_result)
        with contextlib.redirect_stdout(io.StringIO()):
            self.fleet.start_role("hardware-engineer", "engineering", "pane")
        brief = (self.fleet.state / "hardware-engineer.md").read_text()
        for requirement in (
            "typed pins",
            "eight TCA9554",
            "hand-maintained Pi pin",
            "bench measurements",
            "definition/evidence/",
        ):
            self.assertIn(requirement, brief)
        argv = self.fleet.herdr_command.call_args.args
        self.assertIn("opus", argv)
        self.assertIn("high", argv)

    def test_os_launch_failure_is_reported_as_launcher_error(self):
        with (
            patch.object(
                agents.subprocess,
                "run",
                side_effect=FileNotFoundError("missing executable"),
            ),
            self.assertRaisesRegex(agents.LauncherError, "cannot run"),
        ):
            agents.call(["missing"])

    def test_default_roster_cannot_exceed_cap(self):
        self.fleet.maximum = len(self.fleet.defaults) - 1
        with self.assertRaisesRegex(agents.LauncherError, "default_agents exceeds"):
            self.fleet.validate()

    def test_retired_roles_are_not_accepted(self):
        for role in ("student", "scenario"):
            with (
                self.subTest(role=role),
                self.assertRaisesRegex(agents.LauncherError, "unknown agent"),
            ):
                agents.Fleet(options(roles=[role]))

    def test_specialists_use_deliberate_engineering_models(self):
        for role in (
            "hardware-engineer",
            "mechanical-engineer",
            "manufacturing-engineer",
        ):
            settings = self.fleet.kinds[self.fleet.roles[role]]
            self.assertEqual((settings["model"], settings["effort"]), ("opus", "high"))

    def test_workspace_is_bound_to_checkout_not_generic_label(self):
        self.fleet.herdr_json = Mock(
            return_value={
                "result": {
                    "workspaces": [
                        {"workspace_id": "foreign", "label": "chess-team"},
                        {"workspace_id": "ours", "label": self.fleet.workspace},
                    ]
                }
            }
        )
        self.assertEqual(self.fleet.workspace_id(), "ours")
        with patch.object(agents, "REPO", Path(self.temp.name) / "another-checkout"):
            other = agents.Fleet(options())
        self.assertNotEqual(other.workspace, self.fleet.workspace)

    def test_matching_managed_workspace_must_have_correct_checkout(self):
        self.fleet.herdr_json = Mock(
            return_value={
                "result": {
                    "workspaces": [
                        {
                            "workspace_id": "ws",
                            "label": self.fleet.workspace,
                            "worktree": {"checkout_path": self.temp.name},
                        },
                    ]
                }
            }
        )
        with self.assertRaisesRegex(agents.LauncherError, "checkout does not match"):
            self.fleet.workspace_id()

    def test_duplicate_bound_workspaces_fail_closed(self):
        self.fleet.herdr_json = Mock(
            return_value={
                "result": {
                    "workspaces": [
                        {"workspace_id": name, "label": self.fleet.workspace}
                        for name in ("a", "b")
                    ]
                }
            }
        )
        with self.assertRaisesRegex(agents.LauncherError, "duplicate"):
            self.fleet.workspace_id()

    def test_named_transport_ignores_inherited_socket_but_preserves_config(self):
        environment = {
            "HERDR_SOCKET_PATH": "/foreign.sock",
            "HERDR_SESSION": "foreign",
            "HERDR_WORKSPACE_ID": "foreign",
            "HERDR_PLUGIN_ID": "foreign",
            "HERDR_MACHINE_ID": "foreign",
            "HERDR_CONFIG_PATH": "/custom/config.toml",
        }
        with patch.dict(os.environ, environment), patch.object(agents, "call") as call:
            self.fleet.herdr_command("workspace", "list")
        self.assertEqual(call.call_args.args[0][:3], ["herdr", "--session", "chess"])
        actual = call.call_args.kwargs["env"]
        self.assertEqual(actual["HERDR_CONFIG_PATH"], "/custom/config.toml")
        for key in environment.keys() - {"HERDR_CONFIG_PATH"}:
            self.assertNotIn(key, actual)

    def test_plugin_transport_keeps_invoking_context(self):
        self.fleet.plugin = True
        with (
            patch.dict(os.environ, {"HERDR_SOCKET_PATH": "/plugin.sock"}),
            patch.object(agents, "call") as call,
        ):
            self.fleet.herdr_command("workspace", "list")
        self.assertNotIn("--session", call.call_args.args[0])
        self.assertEqual(
            call.call_args.kwargs["env"]["HERDR_SOCKET_PATH"], "/plugin.sock"
        )

    def test_server_environment_preserves_config_and_removes_nested_markers(self):
        self.fleet.server_running = Mock(side_effect=[False, True])
        environment = {
            "HERDR_CONFIG_PATH": "/custom/config.toml",
            "HERDR_SOCKET_PATH": "/foreign.sock",
            "CLAUDECODE": "1",
            "CLAUDE_CODE_OAUTH_TOKEN": "test-only-token",
        }
        with (
            patch.dict(os.environ, environment),
            patch.object(agents.subprocess, "Popen") as popen,
        ):
            self.fleet.ensure_server()
        actual = popen.call_args.kwargs["env"]
        self.assertEqual(actual["HERDR_CONFIG_PATH"], environment["HERDR_CONFIG_PATH"])
        self.assertEqual(actual["CLAUDE_CODE_OAUTH_TOKEN"], "test-only-token")
        self.assertNotIn("CLAUDECODE", actual)
        self.assertNotIn("HERDR_SOCKET_PATH", actual)

    def test_provider_startup_dialog_and_timeout_are_preserved(self):
        self.fleet.lock()
        for code in ("agent_not_ready", "agent_blocked", "timeout"):
            for stream in ("stderr", "stdout"):
                result = SimpleNamespace(returncode=1, stderr="", stdout="")
                setattr(result, stream, json.dumps({"error": {"code": code}}))
                self.fleet.herdr_command = Mock(return_value=result)
                with (
                    self.subTest(code=code, stream=stream),
                    self.assertRaisesRegex(agents.StartupPending, "kept pane"),
                ):
                    self.fleet.start_role("hardware-engineer", "engineering", "new")

    def test_protocol_error_parser_handles_non_json_stderr_and_invalid_payloads(self):
        result = SimpleNamespace(
            stderr="warning", stdout='{"error":{"code":"timeout"}}'
        )
        self.assertEqual(agents.protocol_error_code(result), "timeout")
        for payload in ("", "not JSON", "[]", '{"error":null}'):
            result = SimpleNamespace(stderr=payload, stdout="")
            self.assertIsNone(agents.protocol_error_code(result))

    def test_up_does_not_close_a_startup_dialog(self):
        fleet = self.fake_up()
        fleet.options.roles = ["hardware-engineer"]
        fleet.herdr_json.side_effect = [
            {"result": {"agents": []}},
            {"result": {"root_pane": {"pane_id": "new"}}},
        ]
        fleet.start_role.side_effect = agents.StartupPending("answer trust prompt")
        with self.assertRaises(agents.StartupPending):
            fleet.up()
        self.assertFalse(
            any(
                call.args[:2] == ("pane", "close")
                for call in fleet.herdr_command.call_args_list
            )
        )


class SetupAndUsageTests(unittest.TestCase):
    def test_setup_rejects_host_before_filesystem_or_tool_mutation(self):
        with (
            patch.object(setup.Path, "exists", return_value=False),
            patch.object(setup.Path, "mkdir") as mkdir,
            patch.object(setup.subprocess, "run") as run,
            self.assertRaisesRegex(SystemExit, "inside the devcontainer"),
        ):
            setup.main()
        mkdir.assert_not_called()
        run.assert_not_called()

    def test_optional_reviewr_failure_does_not_block_required_setup(self):
        def result(argv, **_kwargs):
            return SimpleNamespace(
                returncode=1 if argv[1:3] == ["plugin", "install"] else 0
            )

        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(setup.Path, "home", return_value=Path(directory)),
            patch.object(setup, "require_container"),
            patch.object(setup.subprocess, "run", side_effect=result) as run,
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            setup.main()
        self.assertIn("optional Reviewr installation failed", output.getvalue())
        commands = [call.args[0] for call in run.call_args_list]
        self.assertIn(["herdr", "integration", "install", "claude"], commands)
        self.assertIn(["herdr", "integration", "install", "codex"], commands)
        self.assertIn(["herdr", "integration", "install", "pi"], commands)
        self.assertIn(["pi", "--version"], commands)
        self.assertTrue(any(command[1:3] == ["plugin", "link"] for command in commands))
        self.assertIn(["claude", "--version"], commands)

    def test_hook_normalization_is_idempotent_preserves_custom_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            path = home / ".claude/settings.json"
            path.parent.mkdir()
            command = f'bash "{home}/.claude/hooks/herdr-agent-state.sh" session'
            group = {"hooks": [{"type": "command", "command": command}]}
            custom = {"hooks": [{"command": "echo custom && " + command}]}
            path.write_text(
                json.dumps(
                    {"unrelated": True, "hooks": {"Stop": [group, group, custom]}}
                )
            )
            setup.portable_claude_hooks(home)
            first = path.read_text()
            setup.portable_claude_hooks(home)
            self.assertEqual(path.read_text(), first)
            settings = json.loads(first)
            self.assertTrue(settings["unrelated"])
            self.assertEqual(len(settings["hooks"]["Stop"]), 2)
            self.assertEqual(settings["hooks"]["Stop"][1], custom)

    def test_usage_deduplicates_streams_and_skips_malformed_records(self):
        now = datetime(2026, 1, 1, tzinfo=UTC)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "session.jsonl"

            def record(tokens):
                return {
                    "type": "assistant",
                    "timestamp": now.isoformat(),
                    "sessionId": "s",
                    "message": {
                        "id": "m",
                        "model": "sonnet",
                        "usage": {"input_tokens": tokens},
                    },
                }

            path.write_text(
                "\n".join([json.dumps(record(2)), json.dumps(record(8)), "{truncated"])
            )
            report = usage.collect_report(Path(directory), 24, now)
            self.assertEqual(report["messages"], 1)
            self.assertEqual(report["sessions"], 1)
            self.assertEqual(report["input_tokens"], 8)
            self.assertEqual(report["malformed_records"], 1)

    def test_usage_missing_logs_and_invalid_hours(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                usage.collect_report(Path(directory) / "missing", 24)
            for hours in (0, -1, float("nan"), float("inf"), 1e300):
                with self.subTest(hours=hours), self.assertRaises(ValueError):
                    usage.collect_report(Path(directory), hours)


if __name__ == "__main__":
    unittest.main()
