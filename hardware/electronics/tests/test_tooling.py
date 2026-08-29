"""Zero-install Schemdraw venv wiring."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


class ElectronicsToolingTest(unittest.TestCase):
    def test_runner_bootstraps_a_local_venv(self) -> None:
        tool = (REPO / "tools" / "electronics").read_text()
        self.assertIn(".cache/electronics", tool)
        self.assertIn("hardware/electronics/requirements.txt", tool)
        self.assertIn("schemdraw", (REPO / "hardware" / "electronics" / "requirements.txt").read_text())
        self.assertNotIn("kicad", tool.lower())
        self.assertNotIn("docker", tool.lower())

    def test_devcontainer_installs_python_not_kicad(self) -> None:
        dockerfile = (REPO / ".devcontainer" / "Dockerfile").read_text()
        self.assertIn("python3", dockerfile)
        post = (REPO / ".devcontainer" / "post-create.sh").read_text()
        self.assertIn("./tools/check", post)
        self.assertNotIn("kicad", post.lower())
        spec = json.loads((REPO / ".devcontainer" / "devcontainer.json").read_text())
        self.assertNotIn("KICAD_IMAGE", spec.get("containerEnv", {}))
        self.assertNotIn("initializeCommand", spec)


if __name__ == "__main__":
    unittest.main()
