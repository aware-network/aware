from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, TextIO

from .contracts import WorkspaceRepositoryBinding


class WorkspaceObservationLeaseUnavailable(RuntimeError):
    pass


class WorkspaceRepositoryObservationLease(Protocol):
    def acquire(self) -> None: ...

    def release(self) -> None: ...


class FileWorkspaceRepositoryObservationLease:
    """Non-blocking OS advisory writer lease for one repository root."""

    def __init__(
        self,
        *,
        binding: WorkspaceRepositoryBinding,
        lease_path: Path | None = None,
    ) -> None:
        self.binding = binding
        self.lease_path = lease_path or (
            binding.root_path / ".aware" / "workspace" / "observation" / "writer.lock"
        )
        self._stream: TextIO | None = None

    def acquire(self) -> None:
        if self._stream is not None:
            return
        self.lease_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(
            self.lease_path,
            os.O_RDWR | os.O_CREAT,
            0o600,
        )
        stream = os.fdopen(descriptor, "r+", encoding="utf-8")
        try:
            _lock_nonblocking(stream)
        except OSError as exc:
            stream.close()
            raise WorkspaceObservationLeaseUnavailable(
                "A maintained Workspace observer already owns repository root "
                f"{self.binding.root_path}"
            ) from exc
        stream.seek(0)
        stream.truncate()
        stream.write(
            json.dumps(
                {
                    "binding_key": self.binding.binding_key,
                    "pid": os.getpid(),
                    "acquired_at": datetime.now(UTC).isoformat(),
                },
                sort_keys=True,
            )
            + "\n"
        )
        stream.flush()
        os.fsync(stream.fileno())
        self._stream = stream

    def release(self) -> None:
        stream = self._stream
        self._stream = None
        if stream is None:
            return
        try:
            _unlock(stream)
        finally:
            stream.close()


def _lock_nonblocking(stream: TextIO) -> None:
    if os.name == "nt":
        import msvcrt

        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        return
    import fcntl

    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock(stream: TextIO) -> None:
    if os.name == "nt":
        import msvcrt

        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
