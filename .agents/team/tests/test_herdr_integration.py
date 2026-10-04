"""Optional native Herdr smoke tests; never start a provider or make model calls.

HERDR_TEST_BIN=/absolute/path/to/herdr just agents-test
The normal offline suite skips these tests when that variable is not set.
"""

import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from test_team import agents, options


@unittest.skipUnless(
    os.environ.get("HERDR_TEST_BIN"), "set HERDR_TEST_BIN for native smoke tests"
)
class HerdrIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.binary = str(Path(os.environ["HERDR_TEST_BIN"]).resolve())
        self.temp = tempfile.TemporaryDirectory(prefix="chess-herdr-test-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.repo = self.home / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        config = self.home / "config.toml"
        config.write_text("onboarding = false\n")
        self.environment = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("HERDR_")
        }
        self.environment.update(HOME=str(self.home), HERDR_CONFIG_PATH=str(config))
        self.session = "chess-smoke-test"
        self.server = subprocess.Popen(
            [self.binary, "--session", self.session, "server"],
            env=self.environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.addCleanup(self.stop_server)
        for _ in range(50):
            # `status server` can exit zero while reporting a stopped server.
            # Wait for a successful socket API read, not just a CLI exit code.
            if self.command("workspace", "list").returncode == 0:
                break
            if self.server.poll() is not None:
                self.fail("isolated Herdr server exited before readiness")
            time.sleep(0.1)
        else:
            self.fail("isolated Herdr server did not become ready")
        for patcher in (
            patch.dict(os.environ, self.environment, clear=True),
            patch.dict(os.environ, {"HERDR_BIN_PATH": self.binary}),
            patch.object(agents, "REPO", self.repo),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.fleet = agents.Fleet(options(command="down", session=self.session))
        self.addCleanup(self.fleet.unlock)

    def command(self, *arguments):
        return subprocess.run(
            [self.binary, "--session", self.session, *arguments],
            env=self.environment,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )

    def stop_server(self):
        if self.server.poll() is None:
            self.command("server", "stop")
            try:
                self.server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server.terminate()
                self.server.wait(timeout=5)

    def workspace(self, label):
        result = self.command(
            "workspace",
            "create",
            "--cwd",
            str(self.repo),
            "--label",
            label,
            "--no-focus",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["result"]["workspace"]["workspace_id"]

    def remaining_workspaces(self):
        result = self.command("workspace", "list")
        self.assertEqual(result.returncode, 0, result.stderr)
        return {
            item["workspace_id"]
            for item in json.loads(result.stdout)["result"]["workspaces"]
        }

    def test_checkout_binding_transport_and_owned_only_stop(self):
        owned = self.workspace(self.fleet.workspace)
        foreign = self.workspace("chess-team")
        with patch.dict(
            os.environ,
            {"HERDR_SOCKET_PATH": "/foreign.sock", "HERDR_SESSION": "foreign"},
        ):
            self.assertEqual(self.fleet.workspace_id(), owned)
            self.fleet.down()
        self.assertEqual(self.remaining_workspaces(), {foreign})

    def test_native_error_response_is_read_from_stderr(self):
        # An absent pane fails before process launch, even if Claude is installed.
        result = self.command(
            "agent",
            "start",
            "never-launched",
            "--kind",
            "claude",
            "--pane",
            "nonexistent",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(agents.protocol_error_code(result), "agent_pane_not_found")

    def test_plugin_action_uses_verified_socket_session_and_workspace(self):
        owned = self.workspace(self.fleet.workspace)
        foreign = self.workspace("other-team")
        status = json.loads(self.command("status", "--json").stdout)
        context = {
            "HERDR_PLUGIN_ID": "chess.team",
            "HERDR_PLUGIN_ACTION_ID": "chess.team.stop",
            "HERDR_WORKSPACE_ID": owned,
            "HERDR_SESSION": self.session,
            "HERDR_SOCKET_PATH": status["server"]["socket"],
        }
        with patch.dict(os.environ, context):
            plugin = agents.Fleet(options(command="down", session=None, plugin=True))
            try:
                self.assertEqual(plugin.session, self.session)
                plugin.down()
            finally:
                plugin.unlock()
        self.assertEqual(self.remaining_workspaces(), {foreign})
