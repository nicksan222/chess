"""Tool-independent helpers for publishing generated artifact sets."""

from __future__ import annotations

import fcntl
import hashlib
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def staged_output(destination: Path) -> Generator[Path]:
    """Publish a complete generated directory or leave the previous one intact.

    A sibling staging directory keeps generation away from reviewed output. An
    advisory lock serializes writers. Publication uses directory renames and
    rolls the previous directory back if the new rename fails. There is a brief
    window between those two renames when the destination path is absent.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    lock_path = Path(tempfile.gettempdir()) / (
        "chess-build-"
        + hashlib.sha256(str(destination.resolve()).encode()).hexdigest()[:16]
        + ".lock"
    )
    with lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with tempfile.TemporaryDirectory(
            prefix=".hardware-build-", dir=destination.parent
        ) as temporary:
            stage = Path(temporary) / "generated"
            stage.mkdir()
            yield stage
            backup = Path(temporary) / "previous"
            if destination.exists():
                destination.rename(backup)
            try:
                stage.rename(destination)
            except BaseException:
                if backup.exists():
                    backup.rename(destination)
                raise
