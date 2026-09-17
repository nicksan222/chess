"""Filesystem failure coverage for shared artifact publication."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from build_support import staged_output


class StagedOutputTest(unittest.TestCase):
    def test_publication_rename_failure_restores_previous_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"
            output.mkdir()
            (output / "old").write_text("reviewed")
            stage_path: Path | None = None
            path_type = type(output)
            original_rename = path_type.rename

            def fail_stage_rename(path: Path, target: Path) -> Path:
                if path == stage_path:
                    raise OSError("publication rename failed")
                return original_rename(path, target)

            with (
                patch.object(
                    path_type, "rename", autospec=True, side_effect=fail_stage_rename
                ),
                self.assertRaisesRegex(OSError, "publication rename failed"),
                staged_output(output) as stage,
            ):
                stage_path = stage
                (stage / "new").write_text("complete")
            self.assertEqual([path.name for path in output.iterdir()], ["old"])
            self.assertEqual((output / "old").read_text(), "reviewed")


if __name__ == "__main__":
    unittest.main()
