"""Tool-independent helpers for publishing generated artifact sets."""

from __future__ import annotations

import fcntl
import hashlib
import shutil
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def staged_output(destination: Path) -> Generator[Path]:
    """Publish a complete directory, restoring or retaining previous output.

    A sibling staging directory keeps generation away from reviewed output. An
    advisory lock serializes writers. Publication uses directory renames and
    rolls the previous directory back if the new rename fails. There is a brief
    window between those two renames when the destination path is absent.
    If rollback also fails, the raised error names the retained backup path.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    lock_path = Path(tempfile.gettempdir()) / (
        "chess-build-"
        + hashlib.sha256(str(destination.resolve()).encode()).hexdigest()[:16]
        + ".lock"
    )
    with lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        temporary = Path(
            tempfile.mkdtemp(prefix=".hardware-build-", dir=destination.parent)
        )
        retain_temporary = False
        try:
            stage = temporary / "generated"
            stage.mkdir()
            yield stage
            backup = temporary / "previous"
            if destination.exists():
                destination.rename(backup)
            try:
                stage.rename(destination)
            except BaseException as publication_error:
                if backup.exists():
                    try:
                        backup.rename(destination)
                    except BaseException as rollback_error:
                        retain_temporary = True
                        recovery_path = backup.resolve()
                        message = "Artifact publication and rollback failed; previous output retained for recovery at "
                        error = RuntimeError(message + str(recovery_path))
                        error.add_note(
                            f"Original publication failure: {publication_error!r}"
                        )
                        raise error from rollback_error
                raise
        finally:
            if not retain_temporary:
                shutil.rmtree(temporary)
