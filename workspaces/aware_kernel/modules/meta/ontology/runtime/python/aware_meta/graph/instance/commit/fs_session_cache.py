from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from aware_utils.logging import logger

from aware_meta.graph.instance.commit.contract import JsonObject
from aware_meta.graph.instance.commit.fs_backend import (
    _file_stat_payload,
    _path_is_relative_to,
    _try_read_json_object,
)
from aware_meta.graph.instance.commit.state_index import (
    CommitStateIndex,
    CommitStateRow,
    CommitStateRowMaps,
)


@dataclass(frozen=True, slots=True)
class _SnapshotStateRowsRead:
    payload: JsonObject
    state_rows: tuple[CommitStateRow, ...]
    state_row_maps: CommitStateRowMaps | None = None


@dataclass(frozen=True, slots=True)
class _JsonFileCacheEntry:
    file_size: int
    file_mtime_ns: int
    file_ctime_ns: int
    payload: JsonObject


class _SessionJsonFileCache:
    """Bounded per-process JSON read cache for hot immutable lane files."""

    def __init__(self, *, max_entries: int) -> None:
        self._max_entries = max(max_entries, 1)
        self._cache: OrderedDict[Path, _JsonFileCacheEntry] = OrderedDict()
        self._lock = Lock()
        self._hit_count = 0
        self._miss_count = 0
        self._store_count = 0
        self._stale_evict_count = 0
        self._lru_evict_count = 0
        self._explicit_evict_count = 0

    def read_json_object(self, path: Path, *, error_message: str) -> JsonObject:
        payload = self.try_read_json_object(
            path,
            log_prefix=error_message,
        )
        if payload is None:
            raise ValueError(error_message)
        return payload

    def try_read_json_object(self, path: Path, *, log_prefix: str) -> JsonObject | None:
        try:
            file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(path)
        except Exception as exc:
            logger.warning("%s: %s", log_prefix, exc)
            return None

        cache_key = path.expanduser().resolve()
        with self._lock:
            cached = self._cache.get(cache_key)
            if cached is not None:
                if (
                    cached.file_size == file_size
                    and cached.file_mtime_ns == file_mtime_ns
                    and cached.file_ctime_ns == file_ctime_ns
                ):
                    self._cache.move_to_end(cache_key)
                    self._hit_count += 1
                    return cached.payload
                self._cache.pop(cache_key, None)
                self._stale_evict_count += 1
            self._miss_count += 1

        payload = _try_read_json_object(path, log_prefix=log_prefix)
        if payload is None:
            return None

        with self._lock:
            self._cache[cache_key] = _JsonFileCacheEntry(
                file_size=file_size,
                file_mtime_ns=file_mtime_ns,
                file_ctime_ns=file_ctime_ns,
                payload=payload,
            )
            self._cache.move_to_end(cache_key)
            self._store_count += 1
            while len(self._cache) > self._max_entries:
                self._cache.popitem(last=False)
                self._lru_evict_count += 1
        return payload

    def invalidate_path(self, path: Path) -> None:
        cache_key = path.expanduser().resolve()
        with self._lock:
            if self._cache.pop(cache_key, None) is not None:
                self._explicit_evict_count += 1

    def invalidate_under(self, root: Path) -> None:
        resolved_root = root.expanduser().resolve()
        with self._lock:
            evicted = 0
            for cache_key in tuple(self._cache.keys()):
                if not _path_is_relative_to(cache_key, resolved_root):
                    continue
                self._cache.pop(cache_key, None)
                evicted += 1
            self._explicit_evict_count += evicted

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._hit_count = 0
            self._miss_count = 0
            self._store_count = 0
            self._stale_evict_count = 0
            self._lru_evict_count = 0
            self._explicit_evict_count = 0

    def snapshot_metrics(self) -> dict[str, int]:
        with self._lock:
            return {
                "hit_count": max(int(self._hit_count), 0),
                "miss_count": max(int(self._miss_count), 0),
                "store_count": max(int(self._store_count), 0),
                "stale_evict_count": max(int(self._stale_evict_count), 0),
                "lru_evict_count": max(int(self._lru_evict_count), 0),
                "explicit_evict_count": max(int(self._explicit_evict_count), 0),
                "entry_count": max(int(len(self._cache)), 0),
                "max_entries": max(int(self._max_entries), 0),
            }


@dataclass(frozen=True, slots=True)
class _SnapshotStateRowsReadCacheEntry:
    file_size: int
    file_mtime_ns: int
    file_ctime_ns: int
    read: _SnapshotStateRowsRead


class _SessionSnapshotStateRowsReadCache:
    """Structured cache for snapshot-state rows already validated in-process."""

    def __init__(self, *, max_entries: int) -> None:
        self._max_entries = max(max_entries, 1)
        self._cache: OrderedDict[Path, _SnapshotStateRowsReadCacheEntry] = OrderedDict()
        self._lock = Lock()
        self._hit_count = 0
        self._miss_count = 0
        self._store_count = 0
        self._stale_evict_count = 0
        self._lru_evict_count = 0
        self._explicit_evict_count = 0
        self._map_upgrade_count = 0

    def try_read(
        self,
        path: Path,
        *,
        file_size: int,
        file_mtime_ns: int,
        file_ctime_ns: int,
    ) -> _SnapshotStateRowsRead | None:
        cache_key = path.expanduser().resolve()
        with self._lock:
            cached = self._cache.get(cache_key)
            if cached is None:
                self._miss_count += 1
                return None
            if (
                cached.file_size != file_size
                or cached.file_mtime_ns != file_mtime_ns
                or cached.file_ctime_ns != file_ctime_ns
            ):
                self._cache.pop(cache_key, None)
                self._stale_evict_count += 1
                self._miss_count += 1
                return None
            self._cache.move_to_end(cache_key)
            self._hit_count += 1
            return cached.read

    def with_state_row_maps(
        self,
        path: Path,
        *,
        file_size: int,
        file_mtime_ns: int,
        file_ctime_ns: int,
        read: _SnapshotStateRowsRead,
    ) -> _SnapshotStateRowsRead | None:
        if read.state_row_maps is not None:
            return read
        try:
            read_with_maps = _SnapshotStateRowsRead(
                payload=read.payload,
                state_rows=read.state_rows,
                state_row_maps=CommitStateIndex(rows=read.state_rows).row_maps(),
            )
        except Exception:
            return None
        self.store_read(
            path,
            file_size=file_size,
            file_mtime_ns=file_mtime_ns,
            file_ctime_ns=file_ctime_ns,
            read=read_with_maps,
        )
        with self._lock:
            self._map_upgrade_count += 1
        return read_with_maps

    def store_path(
        self,
        path: Path,
        *,
        payload: JsonObject,
        state_rows: tuple[CommitStateRow, ...],
        state_row_maps: CommitStateRowMaps | None = None,
    ) -> None:
        try:
            file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(path)
        except Exception:
            return
        self.store_read(
            path,
            file_size=file_size,
            file_mtime_ns=file_mtime_ns,
            file_ctime_ns=file_ctime_ns,
            read=_SnapshotStateRowsRead(
                payload=payload,
                state_rows=state_rows,
                state_row_maps=state_row_maps,
            ),
        )

    def store_read(
        self,
        path: Path,
        *,
        file_size: int,
        file_mtime_ns: int,
        file_ctime_ns: int,
        read: _SnapshotStateRowsRead,
    ) -> None:
        cache_key = path.expanduser().resolve()
        with self._lock:
            self._cache[cache_key] = _SnapshotStateRowsReadCacheEntry(
                file_size=file_size,
                file_mtime_ns=file_mtime_ns,
                file_ctime_ns=file_ctime_ns,
                read=read,
            )
            self._cache.move_to_end(cache_key)
            self._store_count += 1
            while len(self._cache) > self._max_entries:
                self._cache.popitem(last=False)
                self._lru_evict_count += 1

    def invalidate_path(self, path: Path) -> None:
        cache_key = path.expanduser().resolve()
        with self._lock:
            if self._cache.pop(cache_key, None) is not None:
                self._explicit_evict_count += 1

    def invalidate_under(self, root: Path) -> None:
        resolved_root = root.expanduser().resolve()
        with self._lock:
            evicted = 0
            for cache_key in tuple(self._cache.keys()):
                if not _path_is_relative_to(cache_key, resolved_root):
                    continue
                self._cache.pop(cache_key, None)
                evicted += 1
            self._explicit_evict_count += evicted

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._hit_count = 0
            self._miss_count = 0
            self._store_count = 0
            self._stale_evict_count = 0
            self._lru_evict_count = 0
            self._explicit_evict_count = 0
            self._map_upgrade_count = 0

    def snapshot_metrics(self) -> dict[str, int]:
        with self._lock:
            return {
                "state_rows_hit_count": max(int(self._hit_count), 0),
                "state_rows_miss_count": max(int(self._miss_count), 0),
                "state_rows_store_count": max(int(self._store_count), 0),
                "state_rows_stale_evict_count": max(
                    int(self._stale_evict_count),
                    0,
                ),
                "state_rows_lru_evict_count": max(int(self._lru_evict_count), 0),
                "state_rows_explicit_evict_count": max(
                    int(self._explicit_evict_count),
                    0,
                ),
                "state_rows_map_upgrade_count": max(int(self._map_upgrade_count), 0),
                "state_rows_entry_count": max(int(len(self._cache)), 0),
                "state_rows_max_entries": max(int(self._max_entries), 0),
            }
