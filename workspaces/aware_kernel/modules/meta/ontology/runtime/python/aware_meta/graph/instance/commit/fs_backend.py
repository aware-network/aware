from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
import ctypes
import hashlib
import json
import os
from pathlib import Path
from typing import cast

from aware_utils.logging import logger

from aware_meta.graph.instance.commit.contract import JsonObject


_AWARE_ROOT_ENV = "AWARE_ROOT"
_CURRENT_DURABLE_WRITE_TRANSACTION: ContextVar[DurableWriteTransaction | None] = (
    ContextVar("aware_meta_durable_write_transaction", default=None)
)
_LIBC: ctypes.CDLL | None = None


def _env_int(name: str, default: int, *, minimum: int) -> int:
    raw_value = (os.getenv(name) or "").strip()
    if not raw_value:
        return default
    try:
        value = int(raw_value)
    except Exception:
        return default
    return value if value >= minimum else default


def _resolve_aware_root(root_dir: Path | None) -> Path:
    if root_dir is None:
        raw_root = (os.getenv(_AWARE_ROOT_ENV) or "").strip()
        if raw_root:
            return Path(raw_root).expanduser().resolve()
        raise RuntimeError(
            "FSCommitStore requires explicit root_dir or AWARE_ROOT; "
            "public kernel runtime must not discover repository roots"
        )
    return Path(root_dir).expanduser().resolve()


def _resolve_oig_root(root_dir: Path | None) -> Path:
    return _resolve_aware_root(root_dir) / ".aware" / "oig"


@dataclass(frozen=True, slots=True)
class DurableWriteTransactionStats:
    status: str
    write_count: int = 0
    syncfs_count: int = 0
    file_fsync_count: int = 0
    directory_fsync_count: int = 0

    def to_dict(self) -> dict[str, int | str]:
        return {
            "status": self.status,
            "write_count": self.write_count,
            "syncfs_count": self.syncfs_count,
            "file_fsync_count": self.file_fsync_count,
            "directory_fsync_count": self.directory_fsync_count,
        }


class DurableWriteTransaction:
    """Group durable file sync for append-owned commit truth writes."""

    def __init__(self) -> None:
        self._paths: list[Path] = []
        self._directories: set[Path] = set()
        self._committed = False
        self._stats = DurableWriteTransactionStats(status="open")

    @property
    def write_count(self) -> int:
        return len(self._paths)

    @property
    def committed(self) -> bool:
        return self._committed

    def stats_snapshot(self) -> dict[str, int | str]:
        return self._stats.to_dict()

    def atomic_write(self, path: Path, data: str) -> None:
        if self._committed:
            raise RuntimeError("Durable write transaction is already committed")
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as file_handle:
            _ = file_handle.write(data)
            file_handle.flush()
        _ = tmp.replace(path)
        self._paths.append(path)
        self._directories.add(path.parent)

    def commit(self) -> DurableWriteTransactionStats:
        if self._committed:
            return self._stats
        write_count = len(self._paths)
        if write_count == 0:
            self._stats = DurableWriteTransactionStats(status="empty")
            self._committed = True
            return self._stats

        syncfs_count = 0
        file_fsync_count = 0
        directory_fsync_count = 0
        if _syncfs_path(next(iter(self._directories))):
            syncfs_count = 1
            status = "syncfs_committed"
        else:
            for path in self._paths:
                with open(path, "rb") as file_handle:
                    os.fsync(file_handle.fileno())
                    file_fsync_count += 1
            for directory in self._directories:
                if _fsync_directory(directory):
                    directory_fsync_count += 1
            status = "file_fsync_committed"
        self._stats = DurableWriteTransactionStats(
            status=status,
            write_count=write_count,
            syncfs_count=syncfs_count,
            file_fsync_count=file_fsync_count,
            directory_fsync_count=directory_fsync_count,
        )
        self._committed = True
        return self._stats


def current_durable_write_transaction() -> DurableWriteTransaction | None:
    return _CURRENT_DURABLE_WRITE_TRANSACTION.get()


@contextmanager
def grouped_durable_write_transaction() -> Iterator[DurableWriteTransaction]:
    current = current_durable_write_transaction()
    if current is not None:
        yield current
        return

    transaction = DurableWriteTransaction()
    token = _CURRENT_DURABLE_WRITE_TRANSACTION.set(transaction)
    try:
        yield transaction
    finally:
        try:
            transaction.commit()
        finally:
            _CURRENT_DURABLE_WRITE_TRANSACTION.reset(token)


def _atomic_write(path: Path, data: str) -> None:
    transaction = current_durable_write_transaction()
    if transaction is not None:
        transaction.atomic_write(path, data)
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as file_handle:
        _ = file_handle.write(data)
        file_handle.flush()
        os.fsync(file_handle.fileno())
    _ = tmp.replace(path)


def _syncfs_path(path: Path) -> bool:
    libc = _libc()
    if libc is None or not hasattr(libc, "syncfs"):
        return False
    fd = -1
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        result = int(libc.syncfs(fd))
        return result == 0
    except Exception:
        return False
    finally:
        if fd >= 0:
            os.close(fd)


def _libc() -> ctypes.CDLL | None:
    global _LIBC
    if _LIBC is not None:
        return _LIBC
    try:
        _LIBC = ctypes.CDLL(None, use_errno=True)
    except Exception:
        return None
    return _LIBC


def _fsync_directory(path: Path) -> bool:
    fd = -1
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        os.fsync(fd)
        return True
    except Exception:
        return False
    finally:
        if fd >= 0:
            os.close(fd)


def _atomic_write_rebuildable_sidecar(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as file_handle:
        _ = file_handle.write(data)
        file_handle.flush()
    _ = tmp.replace(path)


def _dump_json(payload: JsonObject) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _coerce_json_object(payload: object, *, error_message: str) -> JsonObject:
    if not isinstance(payload, dict):
        raise ValueError(error_message)
    source = cast(dict[object, object], payload)
    typed_payload: JsonObject = {}
    for raw_key, raw_value in source.items():
        if not isinstance(raw_key, str):
            raise ValueError(error_message)
        typed_payload[raw_key] = raw_value
    return typed_payload


def _coerce_json_object_view(payload: object, *, error_message: str) -> JsonObject:
    if not isinstance(payload, dict):
        raise ValueError(error_message)
    for raw_key in payload:
        if not isinstance(raw_key, str):
            raise ValueError(error_message)
    return cast(JsonObject, payload)


def _read_json_object(path: Path, *, error_message: str) -> JsonObject:
    try:
        raw_payload = cast(object, json.loads(path.read_text(encoding="utf-8")))
        return _coerce_json_object(
            raw_payload,
            error_message=error_message,
        )
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(error_message) from exc


def _try_read_json_object(path: Path, *, log_prefix: str) -> JsonObject | None:
    try:
        raw_payload = cast(object, json.loads(path.read_text(encoding="utf-8")))
        return _coerce_json_object(
            raw_payload,
            error_message=f"{log_prefix}: invalid JSON object",
        )
    except Exception as exc:
        logger.warning("%s: %s", log_prefix, exc)
        return None


def _file_stat_payload(path: Path) -> tuple[int, int, int]:
    stat = path.stat()
    return int(stat.st_size), int(stat.st_mtime_ns), int(stat.st_ctime_ns)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _path_is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
