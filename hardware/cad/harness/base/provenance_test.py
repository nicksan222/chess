"""CAD source provenance covers every file that can change generation."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from . import provenance


class ProvenanceTest(unittest.TestCase):
    def test_justfile_and_shared_build_support_affect_the_source_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hardware = root / "hardware"
            (hardware / "cad").mkdir(parents=True)
            (hardware / "shared").mkdir()
            (root / ".devcontainer").mkdir()
            (hardware / "cad" / "model.py").write_text("MODEL = 1\n")
            (hardware / "shared" / "dimensions.py").write_text("SIZE = 1\n")
            (hardware / "cad" / "justfile").write_text("generate:\n")
            (hardware / "build_support.py").write_text("SUPPORT = 1\n")
            (root / ".devcontainer" / "Dockerfile").write_text("FROM scratch\n")
            (root / "pyproject.toml").write_text("[tool]\n")

            with patch.object(provenance, "HARDWARE", hardware):
                original = provenance.source_digest()
                for path in (
                    hardware / "cad" / "justfile",
                    hardware / "build_support.py",
                ):
                    with self.subTest(path=path.name):
                        previous = path.read_text()
                        path.write_text(previous + "# changed\n")
                        self.assertNotEqual(provenance.source_digest(), original)
                        path.write_text(previous)
