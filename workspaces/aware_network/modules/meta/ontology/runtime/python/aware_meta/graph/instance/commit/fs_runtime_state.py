from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from aware_meta.graph.instance.commit.fs_backend import _env_int
from aware_meta.graph.instance.commit.fs_session_cache import (
    _SessionJsonFileCache,
    _SessionSnapshotStateRowsReadCache,
)

try:
    import fcntl  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]


_SESSION_JSON_FILE_CACHE = _SessionJsonFileCache(
    max_entries=_env_int(
        "AWARE_META_FS_JSON_CACHE_MAX_ENTRIES",
        8192,
        minimum=64,
    )
)
_SESSION_SNAPSHOT_STATE_ROWS_READ_CACHE = _SessionSnapshotStateRowsReadCache(
    max_entries=_env_int(
        "AWARE_META_FS_STATE_ROWS_READ_CACHE_MAX_ENTRIES",
        4096,
        minimum=64,
    )
)


def _clear_fs_store_session_read_cache_for_tests() -> None:
    _SESSION_JSON_FILE_CACHE.clear()
    _SESSION_SNAPSHOT_STATE_ROWS_READ_CACHE.clear()


def _snapshot_fs_store_session_read_cache_metrics() -> dict[str, int]:
    return {
        **_SESSION_JSON_FILE_CACHE.snapshot_metrics(),
        **_SESSION_SNAPSHOT_STATE_ROWS_READ_CACHE.snapshot_metrics(),
    }


@asynccontextmanager
async def _lane_append_lock(*, lock_path: Path) -> AsyncIterator[None]:
    """Cross-process lock for lane appends."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    with open(lock_path, "a+", encoding="utf-8") as file_handle:
        if fcntl is not None:
            while True:
                try:
                    fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    await asyncio.sleep(0.01)
        try:
            yield
        finally:
            if fcntl is not None:
                try:
                    fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
                except Exception:
                    pass
