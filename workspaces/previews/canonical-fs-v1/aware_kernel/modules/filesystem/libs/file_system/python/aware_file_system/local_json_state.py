"""Cross-process-safe JSON state publication for compatibility Issue caches."""

from __future__ import annotations

import json
import os
import stat
import tempfile
from collections.abc import Callable, Mapping
from fcntl import LOCK_EX, LOCK_SH, LOCK_UN, flock
from pathlib import Path
from typing import BinaryIO, cast

type JsonDocument = dict[str, object]


def read_json_state_document(
    *,
    state_path: Path,
    default: Mapping[str, object] | None = None,
) -> JsonDocument:
    """Read one complete JSON document while excluding a committing writer."""

    with _StateLock(state_path=state_path, exclusive=False):
        return _read_unlocked(state_path=state_path, default=default)


def write_json_state_document(
    *,
    state_path: Path,
    document: Mapping[str, object],
) -> None:
    """Atomically replace one JSON document under the shared writer lock."""

    with _StateLock(state_path=state_path, exclusive=True):
        _write_unlocked(state_path=state_path, document=document)


def update_json_state_document(
    *,
    state_path: Path,
    update: Callable[[JsonDocument], Mapping[str, object]],
    default: Mapping[str, object] | None = None,
) -> JsonDocument:
    """Serialize a complete read/modify/write transaction across processes."""

    with _StateLock(state_path=state_path, exclusive=True):
        current = _read_unlocked(state_path=state_path, default=default)
        updated = dict(update(current))
        _write_unlocked(state_path=state_path, document=updated)
        return updated


class _StateLock:
    def __init__(self, *, state_path: Path, exclusive: bool) -> None:
        self._state_path: Path = state_path
        self._exclusive: bool = exclusive
        self._handle: BinaryIO | None = None

    def __enter__(self) -> None:
        parent = self._state_path.parent
        parent.mkdir(parents=True, exist_ok=True)
        lock_path = parent / f".{self._state_path.name}.lock"
        handle = lock_path.open("a+b")
        try:
            flock(handle.fileno(), LOCK_EX if self._exclusive else LOCK_SH)
        except BaseException:
            handle.close()
            raise
        self._handle = handle

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        del exc_type, exc, traceback
        handle = self._handle
        if handle is None:
            return
        try:
            flock(handle.fileno(), LOCK_UN)
        finally:
            handle.close()
            self._handle = None


def _read_unlocked(
    *,
    state_path: Path,
    default: Mapping[str, object] | None,
) -> JsonDocument:
    if not state_path.exists():
        return dict(default or {})
    try:
        payload = cast(object, json.loads(state_path.read_text(encoding="utf-8")))
    except Exception as exc:
        raise ValueError(f"Invalid JSON state at {state_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(  # noqa: TRY004 - malformed persisted state is a value error
            f"Invalid JSON state at {state_path}: root must be an object"
        )
    return cast(JsonDocument, payload)


def _write_unlocked(*, state_path: Path, document: Mapping[str, object]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(dict(document), indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    existing_mode = (
        stat.S_IMODE(state_path.stat().st_mode) if state_path.exists() else 0o664
    )
    descriptor, raw_temp_path = tempfile.mkstemp(
        prefix=f".{state_path.name}.",
        suffix=".tmp",
        dir=state_path.parent,
    )
    temp_path = Path(raw_temp_path)
    try:
        os.fchmod(descriptor, existing_mode)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            _ = handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, state_path)
        directory_descriptor = os.open(
            state_path.parent,
            os.O_RDONLY | os.O_DIRECTORY,
        )
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        _ = temp_path.unlink(missing_ok=True)


__all__ = [
    "JsonDocument",
    "read_json_state_document",
    "update_json_state_document",
    "write_json_state_document",
]
