from __future__ import annotations

import asyncio
from collections import OrderedDict
from collections.abc import AsyncIterator, Iterable, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
import hashlib
import inspect
import json
import os
from pathlib import Path
from threading import Lock
import time
from typing import cast
from uuid import UUID

from aware_history_ontology.lane.lane import Lane
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_branch_id,
    stable_object_instance_graph_commit_id,
)
from aware_orm.session.autobind import disable_autobind
from aware_utils.logging import logger

from aware_meta.graph.instance.commit.contract import (
    CommitActionDescriptor,
    JsonObject,
    LaneHeadCommitReceipt,
    LaneHeadWatcher,
    ObjectInstanceGraphCommitEnvelope,
    ObjectInstanceGraphCommitHealthMetadata,
    ObjectInstanceGraphCommitIdentityMetadata,
    ObjectInstanceGraphCommitIdentitySidecar,
    ObjectInstanceGraphCommitRef,
    ObjectInstanceGraphSnapshotHealthMetadata,
    OigiHistoryDomainCommitProjection,
)

try:
    import fcntl  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]


HEAD_VERSION = 1
COMMIT_META_VERSION = 1
OBJECT_INSTANCE_GRAPH_COMMIT_REF_INDEX_VERSION = 1
OBJECT_INSTANCE_GRAPH_COMMIT_HEALTH_INDEX_VERSION = 1
OBJECT_INSTANCE_GRAPH_COMMIT_ENVELOPE_INDEX_VERSION = 1
OBJECT_INSTANCE_GRAPH_COMMIT_IDENTITY_SIDECAR_INDEX_VERSION = 1
OIGI_HISTORY_DOMAIN_COMMIT_PROJECTION_INDEX_VERSION = 1
OBJECT_INSTANCE_GRAPH_SNAPSHOT_HEALTH_INDEX_VERSION = 1
_AWARE_ROOT_ENV = "AWARE_ROOT"


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


def _atomic_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as file_handle:
        _ = file_handle.write(data)
        file_handle.flush()
        os.fsync(file_handle.fileno())
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


def _json_optional_string(payload: JsonObject, key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str):
        return value
    return None


def _json_optional_uuid(payload: JsonObject, key: str) -> UUID | None:
    value = _json_optional_string(payload, key)
    if value is None:
        return None
    return UUID(value)


def _json_optional_int(payload: JsonObject, key: str) -> int | None:
    value = payload.get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _json_required_string(payload: JsonObject, key: str) -> str:
    value = _json_optional_string(payload, key)
    if value is None:
        raise ValueError(f"Missing required JSON string: {key}")
    return value


def _json_required_uuid(payload: JsonObject, key: str) -> UUID:
    value = _json_optional_uuid(payload, key)
    if value is None:
        raise ValueError(f"Missing required JSON UUID: {key}")
    return value


def _json_required_datetime(payload: JsonObject, key: str) -> datetime:
    value = _json_required_string(payload, key)
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    return datetime.fromisoformat(normalized)


def _json_mapping(payload: JsonObject, key: str) -> JsonObject:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Missing required JSON object: {key}")
    return _coerce_json_object(
        value,
        error_message=f"Invalid JSON object for key: {key}",
    )


def _enum_json_value(value: object) -> str:
    raw_value = getattr(value, "value", value)
    return str(raw_value)


def _datetime_json_value(value: datetime) -> str:
    text = value.isoformat()
    return text[:-6] + "Z" if text.endswith("+00:00") else text


def _file_stat_payload(path: Path) -> tuple[int, int, int]:
    stat = path.stat()
    return int(stat.st_size), int(stat.st_mtime_ns), int(stat.st_ctime_ns)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _path_is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


_SESSION_JSON_FILE_CACHE = _SessionJsonFileCache(
    max_entries=_env_int(
        "AWARE_META_FS_JSON_CACHE_MAX_ENTRIES",
        8192,
        minimum=64,
    )
)


def _clear_fs_store_session_read_cache_for_tests() -> None:
    _SESSION_JSON_FILE_CACHE.clear()


def _snapshot_fs_store_session_read_cache_metrics() -> dict[str, int]:
    return _SESSION_JSON_FILE_CACHE.snapshot_metrics()


def _commit_payload(commit: ObjectInstanceGraphCommit) -> JsonObject:
    return _coerce_json_object(
        commit.model_dump(mode="json", exclude_none=True),
        error_message=f"Commit {commit.commit.id} did not serialize to a JSON object",
    )


def _object_instance_graph_commit_ref_id(commit: ObjectInstanceGraphCommit) -> UUID:
    return stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
        commit_id=commit.commit.id,
    )


def _object_instance_graph_commit_ref_payload(
    *,
    branch_id: UUID,
    projection_hash: str,
    commit: ObjectInstanceGraphCommit,
) -> JsonObject:
    object_instance_graph_commit_id = _object_instance_graph_commit_ref_id(commit)
    return {
        "v": OBJECT_INSTANCE_GRAPH_COMMIT_REF_INDEX_VERSION,
        "object_instance_graph_commit_id": str(object_instance_graph_commit_id),
        "domain_commit_id": str(commit.commit.id),
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "object_instance_graph_identity_id": str(
            commit.object_instance_graph_identity_id
        ),
        "object_instance_graph_id": str(commit.object_instance_graph_id),
        "graph_hash_post": commit.graph_hash_post,
    }


def object_instance_graph_commit_envelope_from_commit(
    *,
    branch_id: UUID,
    projection_hash: str,
    commit: ObjectInstanceGraphCommit,
) -> ObjectInstanceGraphCommitEnvelope:
    return ObjectInstanceGraphCommitEnvelope(
        commit_id=commit.commit.id,
        lane_id=commit.commit.lane_id,
        key=commit.commit.key,
        author_id=commit.commit.author_id,
        created_at=commit.commit.created_at,
        status=_enum_json_value(commit.commit.status),
        parent_commit_ids=tuple(
            parent.parent_commit_id for parent in commit.commit.commit_parents
        ),
        object_instance_graph_commit_id=_object_instance_graph_commit_ref_id(commit),
        object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
        object_instance_graph_id=commit.object_instance_graph_id,
        object_instance_graph_key=commit.object_instance_graph_key,
        object_instance_graph_name=commit.object_instance_graph_name,
        object_instance_graph_description=commit.object_instance_graph_description,
        root_class_config_id=commit.root_class_config_id,
        root_source_object_id=commit.root_source_object_id,
        graph_hash_pre=commit.graph_hash_pre,
        graph_hash_post=commit.graph_hash_post,
        projection_hash=commit.projection_hash or projection_hash,
        source_language=_enum_json_value(commit.source_language),
    )


def _object_instance_graph_commit_envelope_payload(
    *,
    branch_id: UUID,
    projection_hash: str,
    commit: ObjectInstanceGraphCommit,
) -> JsonObject:
    envelope = object_instance_graph_commit_envelope_from_commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit=commit,
    )
    payload: JsonObject = {
        "v": OBJECT_INSTANCE_GRAPH_COMMIT_ENVELOPE_INDEX_VERSION,
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "commit_id": str(envelope.commit_id),
        "lane_id": str(envelope.lane_id),
        "key": envelope.key,
        "author_id": str(envelope.author_id),
        "created_at": _datetime_json_value(envelope.created_at),
        "status": envelope.status,
        "parent_commit_ids": [
            str(parent_id) for parent_id in envelope.parent_commit_ids
        ],
        "object_instance_graph_commit_id": str(
            envelope.object_instance_graph_commit_id
        ),
        "object_instance_graph_identity_id": str(
            envelope.object_instance_graph_identity_id
        ),
        "object_instance_graph_id": str(envelope.object_instance_graph_id),
        "object_instance_graph_key": envelope.object_instance_graph_key,
        "object_instance_graph_name": envelope.object_instance_graph_name,
        "root_class_config_id": str(envelope.root_class_config_id),
        "root_source_object_id": str(envelope.root_source_object_id),
        "graph_hash_pre": envelope.graph_hash_pre,
        "graph_hash_post": envelope.graph_hash_post,
        "source_language": envelope.source_language,
    }
    if envelope.object_instance_graph_description is not None:
        payload["object_instance_graph_description"] = (
            envelope.object_instance_graph_description
        )
    if envelope.projection_hash is not None:
        payload["commit_projection_hash"] = envelope.projection_hash
    return payload


def _object_instance_graph_commit_envelope_from_payload(
    *,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    payload: JsonObject,
) -> ObjectInstanceGraphCommitEnvelope:
    if payload.get("branch_id") != str(branch_id):
        raise ValueError(f"OIG commit envelope branch mismatch: {commit_id}")
    if payload.get("projection_hash") != projection_hash:
        raise ValueError(f"OIG commit envelope projection mismatch: {commit_id}")
    if payload.get("commit_id") != str(commit_id):
        raise ValueError(f"OIG commit envelope id mismatch: {commit_id}")
    parent_values = payload.get("parent_commit_ids")
    if not isinstance(parent_values, list):
        raise ValueError(f"OIG commit envelope parent list missing: {commit_id}")
    parent_commit_ids = tuple(UUID(str(parent_id)) for parent_id in parent_values)
    return ObjectInstanceGraphCommitEnvelope(
        commit_id=commit_id,
        lane_id=_json_required_uuid(payload, "lane_id"),
        key=_json_required_string(payload, "key"),
        author_id=_json_required_uuid(payload, "author_id"),
        created_at=_json_required_datetime(payload, "created_at"),
        status=_json_required_string(payload, "status"),
        parent_commit_ids=parent_commit_ids,
        object_instance_graph_commit_id=_json_required_uuid(
            payload,
            "object_instance_graph_commit_id",
        ),
        object_instance_graph_identity_id=_json_required_uuid(
            payload,
            "object_instance_graph_identity_id",
        ),
        object_instance_graph_id=_json_required_uuid(
            payload,
            "object_instance_graph_id",
        ),
        object_instance_graph_key=_json_required_string(
            payload,
            "object_instance_graph_key",
        ),
        object_instance_graph_name=_json_required_string(
            payload,
            "object_instance_graph_name",
        ),
        object_instance_graph_description=_json_optional_string(
            payload,
            "object_instance_graph_description",
        ),
        root_class_config_id=_json_required_uuid(payload, "root_class_config_id"),
        root_source_object_id=_json_required_uuid(payload, "root_source_object_id"),
        graph_hash_pre=_json_required_string(payload, "graph_hash_pre"),
        graph_hash_post=_json_required_string(payload, "graph_hash_post"),
        projection_hash=_json_optional_string(payload, "commit_projection_hash"),
        source_language=_json_required_string(payload, "source_language"),
    )


def _object_instance_graph_commit_envelope_from_commit_payload(
    *,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    payload: JsonObject,
) -> ObjectInstanceGraphCommitEnvelope:
    commit_payload = _json_mapping(payload, "commit")
    if _json_required_uuid(commit_payload, "id") != commit_id:
        raise ValueError(f"OIG commit payload id mismatch: {commit_id}")
    parent_values = commit_payload.get("commit_parents") or []
    if not isinstance(parent_values, list):
        raise ValueError(f"OIG commit parent list missing: {commit_id}")
    parent_commit_ids: list[UUID] = []
    for parent_value in parent_values:
        if not isinstance(parent_value, dict):
            raise ValueError(f"Invalid OIG commit parent payload: {commit_id}")
        parent_payload = _coerce_json_object(
            parent_value,
            error_message=f"Invalid OIG commit parent payload: {commit_id}",
        )
        parent_commit_ids.append(
            _json_required_uuid(parent_payload, "parent_commit_id")
        )
    oigi_id = _json_required_uuid(payload, "object_instance_graph_identity_id")
    return ObjectInstanceGraphCommitEnvelope(
        commit_id=commit_id,
        lane_id=_json_required_uuid(commit_payload, "lane_id"),
        key=_json_required_string(commit_payload, "key"),
        author_id=_json_required_uuid(commit_payload, "author_id"),
        created_at=_json_required_datetime(commit_payload, "created_at"),
        status=_json_required_string(commit_payload, "status"),
        parent_commit_ids=tuple(parent_commit_ids),
        object_instance_graph_commit_id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=oigi_id,
            commit_id=commit_id,
        ),
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=_json_required_uuid(
            payload,
            "object_instance_graph_id",
        ),
        object_instance_graph_key=_json_required_string(
            payload,
            "object_instance_graph_key",
        ),
        object_instance_graph_name=_json_required_string(
            payload,
            "object_instance_graph_name",
        ),
        object_instance_graph_description=_json_optional_string(
            payload,
            "object_instance_graph_description",
        ),
        root_class_config_id=_json_required_uuid(payload, "root_class_config_id"),
        root_source_object_id=_json_required_uuid(payload, "root_source_object_id"),
        graph_hash_pre=_json_required_string(payload, "graph_hash_pre"),
        graph_hash_post=_json_required_string(payload, "graph_hash_post"),
        projection_hash=_json_optional_string(payload, "projection_hash")
        or projection_hash,
        source_language=_json_required_string(payload, "source_language"),
    )


def _commit_parent_ids_from_commit_payload(
    *,
    commit_id: UUID,
    commit_payload: JsonObject,
) -> tuple[UUID, ...]:
    parent_values = commit_payload.get("commit_parents") or []
    if not isinstance(parent_values, list):
        raise ValueError(f"OIG commit parent list missing: {commit_id}")
    parent_commit_ids: list[UUID] = []
    for parent_value in parent_values:
        if not isinstance(parent_value, dict):
            raise ValueError(f"Invalid OIG commit parent payload: {commit_id}")
        parent_payload = _coerce_json_object(
            parent_value,
            error_message=f"Invalid OIG commit parent payload: {commit_id}",
        )
        parent_commit_ids.append(
            _json_required_uuid(parent_payload, "parent_commit_id")
        )
    return tuple(parent_commit_ids)


def _commit_class_instance_ids_from_payload(
    *,
    commit_id: UUID,
    payload: JsonObject,
) -> tuple[UUID, ...]:
    root_change_values = payload.get("object_instance_graph_changes") or []
    if not isinstance(root_change_values, list):
        raise ValueError(f"OIG commit change list missing: {commit_id}")
    class_instance_ids: set[UUID] = set()
    for root_change_value in root_change_values:
        if not isinstance(root_change_value, dict):
            raise ValueError(f"Invalid OIG root change payload: {commit_id}")
        root_change_payload = _coerce_json_object(
            root_change_value,
            error_message=f"Invalid OIG root change payload: {commit_id}",
        )
        class_change_values = root_change_payload.get("class_instance_changes") or []
        if not isinstance(class_change_values, list):
            raise ValueError(f"Invalid OIG class change list: {commit_id}")
        for class_change_value in class_change_values:
            if not isinstance(class_change_value, dict):
                raise ValueError(f"Invalid OIG class change payload: {commit_id}")
            class_change_payload = _coerce_json_object(
                class_change_value,
                error_message=f"Invalid OIG class change payload: {commit_id}",
            )
            class_instance_ids.add(
                _json_required_uuid(class_change_payload, "class_instance_id")
            )
    return tuple(sorted(class_instance_ids, key=str))


def _commit_class_instance_ids_from_commit(
    commit: ObjectInstanceGraphCommit,
) -> tuple[UUID, ...]:
    class_instance_ids: set[UUID] = set()
    for root_change in commit.object_instance_graph_changes:
        for class_change in root_change.class_instance_changes:
            class_instance_id = class_change.class_instance_id
            if isinstance(class_instance_id, UUID):
                class_instance_ids.add(class_instance_id)
    return tuple(sorted(class_instance_ids, key=str))


def _object_instance_graph_commit_identity_sidecar_payload_from_sidecar(
    *,
    branch_id: UUID,
    projection_hash: str,
    sidecar: ObjectInstanceGraphCommitIdentitySidecar,
    file_size: int,
    file_mtime_ns: int,
    file_ctime_ns: int,
) -> JsonObject:
    return {
        "v": OBJECT_INSTANCE_GRAPH_COMMIT_IDENTITY_SIDECAR_INDEX_VERSION,
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "commit_id": str(sidecar.commit_id),
        "object_instance_graph_identity_id": str(
            sidecar.object_instance_graph_identity_id
        ),
        "object_instance_graph_id": str(sidecar.object_instance_graph_id),
        "parent_commit_ids": [
            str(parent_id) for parent_id in sidecar.parent_commit_ids
        ],
        "class_instance_ids": [
            str(class_instance_id) for class_instance_id in sidecar.class_instance_ids
        ],
        "file_size": file_size,
        "file_mtime_ns": file_mtime_ns,
        "file_ctime_ns": file_ctime_ns,
    }


def _object_instance_graph_commit_identity_sidecar_from_commit(
    *,
    commit: ObjectInstanceGraphCommit,
) -> ObjectInstanceGraphCommitIdentitySidecar:
    return ObjectInstanceGraphCommitIdentitySidecar(
        commit_id=commit.commit.id,
        object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
        object_instance_graph_id=commit.object_instance_graph_id,
        parent_commit_ids=tuple(
            parent.parent_commit_id for parent in commit.commit.commit_parents
        ),
        class_instance_ids=_commit_class_instance_ids_from_commit(commit),
    )


def _object_instance_graph_commit_identity_sidecar_from_payload(
    *,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    payload: JsonObject,
) -> ObjectInstanceGraphCommitIdentitySidecar:
    if payload.get("branch_id") != str(branch_id):
        raise ValueError(f"OIG commit identity sidecar branch mismatch: {commit_id}")
    if payload.get("projection_hash") != projection_hash:
        raise ValueError(
            f"OIG commit identity sidecar projection mismatch: {commit_id}"
        )
    if payload.get("commit_id") != str(commit_id):
        raise ValueError(f"OIG commit identity sidecar id mismatch: {commit_id}")
    parent_values = payload.get("parent_commit_ids")
    class_instance_values = payload.get("class_instance_ids")
    if not isinstance(parent_values, list):
        raise ValueError(
            f"OIG commit identity sidecar parent list missing: {commit_id}"
        )
    if not isinstance(class_instance_values, list):
        raise ValueError(f"OIG commit identity sidecar class list missing: {commit_id}")
    return ObjectInstanceGraphCommitIdentitySidecar(
        commit_id=commit_id,
        object_instance_graph_identity_id=_json_required_uuid(
            payload,
            "object_instance_graph_identity_id",
        ),
        object_instance_graph_id=_json_required_uuid(
            payload,
            "object_instance_graph_id",
        ),
        parent_commit_ids=tuple(UUID(str(parent_id)) for parent_id in parent_values),
        class_instance_ids=tuple(
            UUID(str(class_instance_id)) for class_instance_id in class_instance_values
        ),
    )


def _object_instance_graph_commit_identity_sidecar_from_commit_payload(
    *,
    commit_id: UUID,
    payload: JsonObject,
) -> ObjectInstanceGraphCommitIdentitySidecar:
    commit_payload = _json_mapping(payload, "commit")
    if _json_required_uuid(commit_payload, "id") != commit_id:
        raise ValueError(f"OIG commit payload id mismatch: {commit_id}")
    return ObjectInstanceGraphCommitIdentitySidecar(
        commit_id=commit_id,
        object_instance_graph_identity_id=_json_required_uuid(
            payload,
            "object_instance_graph_identity_id",
        ),
        object_instance_graph_id=_json_required_uuid(
            payload,
            "object_instance_graph_id",
        ),
        parent_commit_ids=_commit_parent_ids_from_commit_payload(
            commit_id=commit_id,
            commit_payload=commit_payload,
        ),
        class_instance_ids=_commit_class_instance_ids_from_payload(
            commit_id=commit_id,
            payload=payload,
        ),
    )


def _oigi_history_domain_commit_projection_payload(
    *,
    projection: OigiHistoryDomainCommitProjection,
) -> JsonObject:
    return {
        "v": OIGI_HISTORY_DOMAIN_COMMIT_PROJECTION_INDEX_VERSION,
        "domain_commit_id": str(projection.domain_commit_id),
        "domain_branch_id": str(projection.domain_branch_id),
        "domain_projection_hash": projection.domain_projection_hash,
        "domain_lane_id": str(projection.domain_lane_id),
        "history_commit_id": str(projection.history_commit_id),
        "object_instance_graph_identity_id": str(
            projection.object_instance_graph_identity_id
        ),
        "object_instance_graph_id": str(projection.object_instance_graph_id),
        "oigi_projection_hash": projection.oigi_projection_hash,
        "oigi_lane_commit_id": str(projection.oigi_lane_commit_id),
        "oigi_graph_hash_post": projection.oigi_graph_hash_post,
    }


def _oigi_history_domain_commit_projection_from_payload(
    *,
    branch_id: UUID,
    projection_hash: str,
    domain_commit_id: UUID,
    payload: JsonObject,
) -> OigiHistoryDomainCommitProjection:
    if payload.get("v") != OIGI_HISTORY_DOMAIN_COMMIT_PROJECTION_INDEX_VERSION:
        raise ValueError(
            "OIGI history domain commit projection index version mismatch: "
            + str(domain_commit_id)
        )
    if payload.get("object_instance_graph_id") != str(branch_id):
        raise ValueError(
            "OIGI history domain commit projection branch mismatch: "
            + str(domain_commit_id)
        )
    if payload.get("oigi_projection_hash") != projection_hash:
        raise ValueError(
            "OIGI history domain commit projection hash mismatch: "
            + str(domain_commit_id)
        )
    if payload.get("domain_commit_id") != str(domain_commit_id):
        raise ValueError(
            "OIGI history domain commit projection id mismatch: "
            + str(domain_commit_id)
        )
    return OigiHistoryDomainCommitProjection(
        domain_commit_id=domain_commit_id,
        domain_branch_id=_json_required_uuid(payload, "domain_branch_id"),
        domain_projection_hash=_json_required_string(
            payload,
            "domain_projection_hash",
        ),
        domain_lane_id=_json_required_uuid(payload, "domain_lane_id"),
        history_commit_id=_json_required_uuid(payload, "history_commit_id"),
        object_instance_graph_identity_id=_json_required_uuid(
            payload,
            "object_instance_graph_identity_id",
        ),
        object_instance_graph_id=_json_required_uuid(
            payload,
            "object_instance_graph_id",
        ),
        oigi_projection_hash=_json_required_string(payload, "oigi_projection_hash"),
        oigi_lane_commit_id=_json_required_uuid(payload, "oigi_lane_commit_id"),
        oigi_graph_hash_post=_json_required_string(payload, "oigi_graph_hash_post"),
    )


def _commit_object_projection_graph_id(
    commit: ObjectInstanceGraphCommit,
) -> UUID | None:
    object_instance_graph = getattr(commit, "object_instance_graph", None)
    if object_instance_graph is None:
        return None
    value = getattr(object_instance_graph, "object_projection_graph_id", None)
    return value if isinstance(value, UUID) else None


def _commit_meta_payload(
    commit_action: CommitActionDescriptor | None,
) -> JsonObject | None:
    if commit_action is None:
        return None

    payload: JsonObject = {
        "v": COMMIT_META_VERSION,
        "operation_label": commit_action.operation_label,
    }
    if commit_action.call_target is not None:
        payload["call_target"] = commit_action.call_target
    if commit_action.function_id is not None:
        payload["function_id"] = str(commit_action.function_id)
    if commit_action.object_id is not None:
        payload["object_id"] = str(commit_action.object_id)
    if commit_action.class_instance_identity_id is not None:
        payload["class_instance_identity_id"] = str(
            commit_action.class_instance_identity_id
        )
    return payload


def _commit_payload_matches(
    existing: JsonObject, commit: ObjectInstanceGraphCommit
) -> bool:
    return (
        _json_optional_string(existing, "graph_hash_post") == commit.graph_hash_post
        and _json_optional_string(existing, "graph_hash_pre") == commit.graph_hash_pre
        and _json_optional_string(existing, "projection_hash") == commit.projection_hash
    )


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


class FSCommitStore:
    """Filesystem-backed commit store per `(branch_id, projection_hash)`."""

    _lane_head_watchers: set[LaneHeadWatcher] = set()
    _aware_root: Path
    _oig_root: Path

    def __init__(self, root_dir: Path | None = None) -> None:
        self._aware_root = _resolve_aware_root(root_dir)
        self._oig_root = _resolve_oig_root(root_dir)
        self._commit_envelope_read_metrics: dict[str, int] = {
            "commit_envelope_index_hit_count": 0,
            "commit_envelope_full_body_fallback_count": 0,
            "commit_envelope_missing_commit_file_count": 0,
            "commit_envelope_fallback_failure_count": 0,
            "commit_identity_sidecar_index_hit_count": 0,
            "commit_identity_sidecar_full_body_fallback_count": 0,
            "commit_identity_sidecar_missing_commit_file_count": 0,
            "commit_identity_sidecar_fallback_failure_count": 0,
        }

    @property
    def aware_root(self) -> Path:
        return self._aware_root

    def _lane_dir(self, branch_id: UUID, projection_hash: str) -> Path:
        return self._oig_root / str(branch_id) / projection_hash

    def _commits_dir(self, branch_id: UUID, projection_hash: str) -> Path:
        return self._lane_dir(branch_id, projection_hash) / "commits"

    def commit_file_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> Path:
        return self._commits_dir(branch_id, projection_hash) / f"{commit_id}.json"

    def commit_envelope_read_metrics_snapshot(self) -> dict[str, int]:
        return dict(self._commit_envelope_read_metrics)

    def _increment_commit_envelope_read_metric(self, key: str) -> None:
        self._commit_envelope_read_metrics[key] = (
            self._commit_envelope_read_metrics.get(key, 0) + 1
        )

    def _object_instance_graph_commit_ref_index_dir(
        self, branch_id: UUID, projection_hash: str
    ) -> Path:
        return (
            self._lane_dir(branch_id, projection_hash)
            / "indexes"
            / "object_instance_graph_commits"
        )

    def _object_instance_graph_commit_health_index_dir(
        self, branch_id: UUID, projection_hash: str
    ) -> Path:
        return self._lane_dir(branch_id, projection_hash) / "indexes" / "commit_health"

    def _object_instance_graph_commit_health_index_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> Path:
        return (
            self._object_instance_graph_commit_health_index_dir(
                branch_id, projection_hash
            )
            / f"{commit_id}.json"
        )

    def _object_instance_graph_commit_envelope_index_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> Path:
        return (
            self._lane_dir(branch_id, projection_hash)
            / "indexes"
            / "commit_envelopes"
            / f"{commit_id}.json"
        )

    def _object_instance_graph_commit_identity_sidecar_index_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> Path:
        return (
            self._lane_dir(branch_id, projection_hash)
            / "indexes"
            / "commit_identity_sidecars"
            / f"{commit_id}.json"
        )

    def _oigi_history_domain_commit_projection_index_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        domain_commit_id: UUID,
    ) -> Path:
        return (
            self._lane_dir(branch_id, projection_hash)
            / "indexes"
            / "oigi_history_domain_commits"
            / f"{domain_commit_id}.json"
        )

    def _object_instance_graph_commit_ref_index_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        object_instance_graph_commit_id: UUID,
    ) -> Path:
        return (
            self._object_instance_graph_commit_ref_index_dir(branch_id, projection_hash)
            / f"{object_instance_graph_commit_id}.json"
        )

    def _write_object_instance_graph_commit_health_index(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
    ) -> None:
        commit_path = (
            self._commits_dir(branch_id, projection_hash) / f"{commit.commit.id}.json"
        )
        if not commit_path.exists():
            return
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(commit_path)
        payload: JsonObject = {
            "v": OBJECT_INSTANCE_GRAPH_COMMIT_HEALTH_INDEX_VERSION,
            "branch_id": str(branch_id),
            "projection_hash": projection_hash,
            "commit_id": str(commit.commit.id),
            "object_instance_graph_id": str(commit.object_instance_graph_id),
            "object_instance_graph_identity_id": str(
                commit.object_instance_graph_identity_id
            ),
            "graph_hash_post": str(commit.graph_hash_post or ""),
            "parent_count": len(commit.commit.commit_parents),
            "file_size": file_size,
            "file_mtime_ns": file_mtime_ns,
            "file_ctime_ns": file_ctime_ns,
            "file_sha256": _file_sha256(commit_path),
        }
        path = self._object_instance_graph_commit_health_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit.commit.id,
        )
        if path.exists():
            existing_payload = _try_read_json_object(
                path,
                log_prefix=f"Existing OIG commit health index is unreadable: {path}",
            )
            if existing_payload == payload:
                return
        _atomic_write(path, _dump_json(payload))
        _SESSION_JSON_FILE_CACHE.invalidate_path(path)

    def _write_object_instance_graph_commit_ref_index(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
    ) -> None:
        object_instance_graph_commit_id = _object_instance_graph_commit_ref_id(commit)
        payload = _object_instance_graph_commit_ref_payload(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
        )
        path = self._object_instance_graph_commit_ref_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
        )
        if path.exists():
            existing_payload = _read_json_object(
                path,
                error_message=f"Existing OIG commit ref index is unreadable: {path}",
            )
            if existing_payload != payload:
                raise ValueError(
                    f"Existing OIG commit ref index differs: {object_instance_graph_commit_id}"
                )
            return
        _atomic_write(path, _dump_json(payload))
        _SESSION_JSON_FILE_CACHE.invalidate_path(path)

    def _write_object_instance_graph_commit_envelope_index(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
    ) -> None:
        commit_path = (
            self._commits_dir(branch_id, projection_hash) / f"{commit.commit.id}.json"
        )
        if not commit_path.exists():
            return
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(commit_path)
        payload = _object_instance_graph_commit_envelope_payload(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
        )
        payload["file_size"] = file_size
        payload["file_mtime_ns"] = file_mtime_ns
        payload["file_ctime_ns"] = file_ctime_ns
        path = self._object_instance_graph_commit_envelope_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit.commit.id,
        )
        if path.exists():
            existing_payload = _try_read_json_object(
                path,
                log_prefix=f"Existing OIG commit envelope index is unreadable: {path}",
            )
            if existing_payload == payload:
                return
        _atomic_write(path, _dump_json(payload))
        _SESSION_JSON_FILE_CACHE.invalidate_path(path)

    def _write_object_instance_graph_commit_identity_sidecar_index(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
    ) -> None:
        commit_path = (
            self._commits_dir(branch_id, projection_hash) / f"{commit.commit.id}.json"
        )
        if not commit_path.exists():
            return
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(commit_path)
        payload = _object_instance_graph_commit_identity_sidecar_payload_from_sidecar(
            branch_id=branch_id,
            projection_hash=projection_hash,
            sidecar=_object_instance_graph_commit_identity_sidecar_from_commit(
                commit=commit,
            ),
            file_size=file_size,
            file_mtime_ns=file_mtime_ns,
            file_ctime_ns=file_ctime_ns,
        )
        path = self._object_instance_graph_commit_identity_sidecar_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit.commit.id,
        )
        if path.exists():
            existing_payload = _try_read_json_object(
                path,
                log_prefix=(
                    "Existing OIG commit identity sidecar index is unreadable: "
                    + str(path)
                ),
            )
            if existing_payload == payload:
                return
        _atomic_write(path, _dump_json(payload))
        _SESSION_JSON_FILE_CACHE.invalidate_path(path)

    def _remove_stale_object_instance_graph_commit_ref_index(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        object_instance_graph_commit_id: UUID,
        domain_commit_id: UUID,
    ) -> None:
        path = self._object_instance_graph_commit_ref_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
        )
        if not path.exists():
            return
        existing_payload = _read_json_object(
            path,
            error_message=f"Existing stale OIG commit ref index is unreadable: {path}",
        )
        if (
            existing_payload.get("domain_commit_id") != str(domain_commit_id)
            or existing_payload.get("branch_id") != str(branch_id)
            or existing_payload.get("projection_hash") != projection_hash
        ):
            raise ValueError(
                "Refusing to remove OIG commit ref index for a different domain commit: "
                + f"{object_instance_graph_commit_id}"
            )
        path.unlink()
        _SESSION_JSON_FILE_CACHE.invalidate_path(path)

    def _repair_existing_commit_identity_metadata(
        self,
        *,
        commit_path: Path,
        existing_commit_payload: JsonObject,
        commit: ObjectInstanceGraphCommit,
    ) -> UUID | None:
        existing_oig_id = _json_optional_uuid(
            existing_commit_payload,
            "object_instance_graph_id",
        )
        if existing_oig_id != commit.object_instance_graph_id:
            raise ValueError(
                "Existing commit OIG id differs from payload: " + f"{commit.commit.id}"
            )
        existing_oigi_id = _json_optional_uuid(
            existing_commit_payload,
            "object_instance_graph_identity_id",
        )
        if existing_oigi_id is None:
            raise ValueError(
                "Existing commit missing object_instance_graph_identity_id: "
                + f"{commit.commit.id}"
            )
        if existing_oigi_id == commit.object_instance_graph_identity_id:
            return None

        stale_ref_id = stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=existing_oigi_id,
            commit_id=commit.commit.id,
        )
        _atomic_write(commit_path, _dump_json(_commit_payload(commit)))
        _SESSION_JSON_FILE_CACHE.invalidate_path(commit_path)
        return stale_ref_id

    def ocg_delta_hint_path(
        self, *, branch_id: UUID, projection_hash: str, commit_id: UUID
    ) -> Path:
        return (
            self._lane_dir(branch_id, projection_hash)
            / "hints"
            / "ocg_deltas"
            / f"{commit_id}.json"
        )

    def put_ocg_delta_hint(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        payload: JsonObject,
    ) -> bool:
        """Persist an OCGΔ hint payload for a commit (idempotent, fail-closed on mismatch)."""
        path = self.ocg_delta_hint_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )

        def _read_existing_hint() -> JsonObject:
            return _read_json_object(
                path,
                error_message=f"Existing OCGΔ hint is unreadable: {path}",
            )

        if path.exists():
            existing = _read_existing_hint()
            if existing == payload:
                return False
            if existing.get("v") != payload.get("v"):
                _atomic_write(path, _dump_json(payload))
                _SESSION_JSON_FILE_CACHE.invalidate_path(path)
                existing = _read_existing_hint()
            if existing != payload:
                raise ValueError(
                    f"Existing OCGΔ hint differs from expected payload: {path}"
                )
            return True

        _atomic_write(path, _dump_json(payload))
        _SESSION_JSON_FILE_CACHE.invalidate_path(path)
        existing = _read_existing_hint()
        if existing != payload:
            raise ValueError(
                f"Existing OCGΔ hint differs from expected payload: {path}"
            )
        return True

    @classmethod
    def register_lane_head_watcher(cls, watcher: LaneHeadWatcher) -> None:
        cls._lane_head_watchers.add(watcher)

    @classmethod
    def unregister_lane_head_watcher(cls, watcher: LaneHeadWatcher) -> None:
        cls._lane_head_watchers.discard(watcher)

    @classmethod
    async def _dispatch_lane_head_watchers(cls, receipt: LaneHeadCommitReceipt) -> None:
        if not cls._lane_head_watchers:
            return

        for watcher in tuple(cls._lane_head_watchers):
            try:
                result = watcher(receipt)
                if inspect.isawaitable(result):
                    await result
            except Exception as exc:
                logger.warning("Lane head watcher failed: %s", exc)

    async def get_commit(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphCommit | None:
        commit_path = (
            self._commits_dir(branch_id, projection_hash) / f"{commit_id}.json"
        )
        if not commit_path.exists():
            self._increment_commit_envelope_read_metric(
                "commit_envelope_missing_commit_file_count"
            )
            return None
        try:
            payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                commit_path,
                log_prefix=f"Failed reading commit {commit_id}",
            )
            if payload is None:
                return None
            with disable_autobind():
                return ObjectInstanceGraphCommit.model_validate(payload)
        except Exception as exc:
            logger.warning("Failed reading commit %s: %s", commit_id, exc)
            return None

    async def get_commit_envelope(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphCommitEnvelope | None:
        commit_path = (
            self._commits_dir(branch_id, projection_hash) / f"{commit_id}.json"
        )
        if not commit_path.exists():
            return None
        envelope_path = self._object_instance_graph_commit_envelope_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(commit_path)
        if envelope_path.exists():
            payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                envelope_path,
                log_prefix=f"Failed reading commit envelope {commit_id}",
            )
            if payload is not None:
                try:
                    if (
                        payload.get("v")
                        == OBJECT_INSTANCE_GRAPH_COMMIT_ENVELOPE_INDEX_VERSION
                        and _json_optional_int(payload, "file_size") == file_size
                        and _json_optional_int(payload, "file_mtime_ns")
                        == file_mtime_ns
                        and _json_optional_int(payload, "file_ctime_ns")
                        == file_ctime_ns
                    ):
                        self._increment_commit_envelope_read_metric(
                            "commit_envelope_index_hit_count"
                        )
                        return _object_instance_graph_commit_envelope_from_payload(
                            branch_id=branch_id,
                            projection_hash=projection_hash,
                            commit_id=commit_id,
                            payload=payload,
                        )
                except Exception as exc:
                    logger.warning(
                        "Failed parsing commit envelope %s: %s", commit_id, exc
                    )

        self._increment_commit_envelope_read_metric(
            "commit_envelope_full_body_fallback_count"
        )
        payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
            commit_path,
            log_prefix=f"Failed reading commit envelope fallback {commit_id}",
        )
        if payload is None:
            self._increment_commit_envelope_read_metric(
                "commit_envelope_fallback_failure_count"
            )
            return None
        try:
            return _object_instance_graph_commit_envelope_from_commit_payload(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                payload=payload,
            )
        except Exception as exc:
            logger.warning(
                "Failed parsing commit envelope fallback %s: %s", commit_id, exc
            )
            self._increment_commit_envelope_read_metric(
                "commit_envelope_fallback_failure_count"
            )
            return None

    async def get_commit_identity_sidecar(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphCommitIdentitySidecar | None:
        commit_path = (
            self._commits_dir(branch_id, projection_hash) / f"{commit_id}.json"
        )
        if not commit_path.exists():
            self._increment_commit_envelope_read_metric(
                "commit_identity_sidecar_missing_commit_file_count"
            )
            return None
        sidecar_path = self._object_instance_graph_commit_identity_sidecar_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(commit_path)
        if sidecar_path.exists():
            payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                sidecar_path,
                log_prefix=f"Failed reading commit identity sidecar {commit_id}",
            )
            if payload is not None:
                try:
                    if (
                        payload.get("v")
                        == OBJECT_INSTANCE_GRAPH_COMMIT_IDENTITY_SIDECAR_INDEX_VERSION
                        and _json_optional_int(payload, "file_size") == file_size
                        and _json_optional_int(payload, "file_mtime_ns")
                        == file_mtime_ns
                        and _json_optional_int(payload, "file_ctime_ns")
                        == file_ctime_ns
                    ):
                        self._increment_commit_envelope_read_metric(
                            "commit_identity_sidecar_index_hit_count"
                        )
                        return (
                            _object_instance_graph_commit_identity_sidecar_from_payload(
                                branch_id=branch_id,
                                projection_hash=projection_hash,
                                commit_id=commit_id,
                                payload=payload,
                            )
                        )
                except Exception as exc:
                    logger.warning(
                        "Failed parsing commit identity sidecar %s: %s",
                        commit_id,
                        exc,
                    )

        self._increment_commit_envelope_read_metric(
            "commit_identity_sidecar_full_body_fallback_count"
        )
        payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
            commit_path,
            log_prefix=f"Failed reading commit identity sidecar fallback {commit_id}",
        )
        if payload is None:
            self._increment_commit_envelope_read_metric(
                "commit_identity_sidecar_fallback_failure_count"
            )
            return None
        try:
            sidecar = (
                _object_instance_graph_commit_identity_sidecar_from_commit_payload(
                    commit_id=commit_id,
                    payload=payload,
                )
            )
        except Exception as exc:
            logger.warning(
                "Failed parsing commit identity sidecar fallback %s: %s",
                commit_id,
                exc,
            )
            self._increment_commit_envelope_read_metric(
                "commit_identity_sidecar_fallback_failure_count"
            )
            return None

        sidecar_payload = (
            _object_instance_graph_commit_identity_sidecar_payload_from_sidecar(
                branch_id=branch_id,
                projection_hash=projection_hash,
                sidecar=sidecar,
                file_size=file_size,
                file_mtime_ns=file_mtime_ns,
                file_ctime_ns=file_ctime_ns,
            )
        )
        try:
            _atomic_write(sidecar_path, _dump_json(sidecar_payload))
            _SESSION_JSON_FILE_CACHE.invalidate_path(sidecar_path)
        except Exception as exc:
            logger.warning(
                "Failed writing repaired commit identity sidecar %s: %s",
                commit_id,
                exc,
            )
        return sidecar

    async def get_oigi_history_domain_commit_projection(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        domain_commit_id: UUID,
    ) -> OigiHistoryDomainCommitProjection | None:
        path = self._oigi_history_domain_commit_projection_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            domain_commit_id=domain_commit_id,
        )
        if not path.exists():
            return None
        payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
            path,
            log_prefix=f"Failed reading OIGI history projection index {domain_commit_id}",
        )
        if payload is None:
            return None
        try:
            return _oigi_history_domain_commit_projection_from_payload(
                branch_id=branch_id,
                projection_hash=projection_hash,
                domain_commit_id=domain_commit_id,
                payload=payload,
            )
        except Exception as exc:
            logger.warning(
                "Failed parsing OIGI history projection index %s: %s",
                domain_commit_id,
                exc,
            )
            return None

    def put_oigi_history_domain_commit_projection(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        projection: OigiHistoryDomainCommitProjection,
    ) -> bool:
        path = self._oigi_history_domain_commit_projection_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            domain_commit_id=projection.domain_commit_id,
        )
        payload = _oigi_history_domain_commit_projection_payload(
            projection=projection,
        )
        if path.exists():
            existing_payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                path,
                log_prefix=(
                    "Existing OIGI history projection index is unreadable: " + str(path)
                ),
            )
            if existing_payload == payload:
                return False
        _atomic_write(path, _dump_json(payload))
        _SESSION_JSON_FILE_CACHE.invalidate_path(path)
        return True

    async def get_commit_identity_metadata(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphCommitIdentityMetadata | None:
        commit_path = (
            self._commits_dir(branch_id, projection_hash) / f"{commit_id}.json"
        )
        if not commit_path.exists():
            return None
        payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
            commit_path,
            log_prefix=f"Failed reading commit identity metadata {commit_id}",
        )
        if payload is None:
            return None
        object_instance_graph_id = _json_optional_uuid(
            payload,
            "object_instance_graph_id",
        )
        object_instance_graph_identity_id = _json_optional_uuid(
            payload,
            "object_instance_graph_identity_id",
        )
        if (
            object_instance_graph_id is None
            or object_instance_graph_identity_id is None
        ):
            return None
        return ObjectInstanceGraphCommitIdentityMetadata(
            object_instance_graph_id=object_instance_graph_id,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
        )

    async def get_commit_health_metadata(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphCommitHealthMetadata | None:
        commit_path = (
            self._commits_dir(branch_id, projection_hash) / f"{commit_id}.json"
        )
        if not commit_path.exists():
            return None
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(commit_path)
        health_path = self._object_instance_graph_commit_health_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if not health_path.exists():
            return None
        payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
            health_path,
            log_prefix=f"Failed reading commit health metadata {commit_id}",
        )
        if payload is None:
            return None
        if payload.get("v") != OBJECT_INSTANCE_GRAPH_COMMIT_HEALTH_INDEX_VERSION:
            return None
        if payload.get("branch_id") != str(branch_id):
            return None
        if payload.get("projection_hash") != projection_hash:
            return None
        if payload.get("commit_id") != str(commit_id):
            return None
        if _json_optional_int(payload, "file_size") != file_size:
            return None
        if _json_optional_int(payload, "file_mtime_ns") != file_mtime_ns:
            return None
        if _json_optional_int(payload, "file_ctime_ns") != file_ctime_ns:
            return None
        if _json_optional_string(payload, "file_sha256") != _file_sha256(commit_path):
            return None

        object_instance_graph_id = _json_optional_uuid(
            payload,
            "object_instance_graph_id",
        )
        object_instance_graph_identity_id = _json_optional_uuid(
            payload,
            "object_instance_graph_identity_id",
        )
        graph_hash_post = _json_optional_string(payload, "graph_hash_post")
        parent_count = _json_optional_int(payload, "parent_count")
        file_sha256 = _json_optional_string(payload, "file_sha256")
        if (
            object_instance_graph_id is None
            or object_instance_graph_identity_id is None
            or not graph_hash_post
            or parent_count is None
            or not file_sha256
        ):
            return None
        return ObjectInstanceGraphCommitHealthMetadata(
            commit_id=commit_id,
            projection_hash=projection_hash,
            object_instance_graph_id=object_instance_graph_id,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            graph_hash_post=graph_hash_post,
            parent_count=parent_count,
            file_size=file_size,
            file_mtime_ns=file_mtime_ns,
            file_ctime_ns=file_ctime_ns,
            file_sha256=file_sha256,
        )

    def write_commit_health_metadata(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
    ) -> None:
        self._write_object_instance_graph_commit_health_index(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
        )

    async def head(self, *, branch_id: UUID, projection_hash: str) -> JsonObject | None:
        head_path = self._lane_dir(branch_id, projection_hash) / "HEAD.json"
        if not head_path.exists():
            return None
        return _SESSION_JSON_FILE_CACHE.try_read_json_object(
            head_path,
            log_prefix="Failed reading HEAD",
        )

    async def iter_lane_heads_by_projection(
        self,
        *,
        projection_hash: str,
    ) -> AsyncIterator[tuple[UUID, JsonObject]]:
        projection = projection_hash.strip()
        if not projection or not self._oig_root.exists():
            return

        try:
            branch_dirs = sorted(
                (path for path in self._oig_root.iterdir() if path.is_dir()),
                key=lambda path: path.name,
            )
        except Exception:
            return

        for branch_dir in branch_dirs:
            try:
                branch_id = UUID(branch_dir.name)
            except Exception:
                continue

            head = await self.head(branch_id=branch_id, projection_hash=projection)
            if head is None:
                continue
            if _json_optional_string(head, "commit_id") is None:
                continue
            yield branch_id, head

    async def head_commit(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
    ) -> ObjectInstanceGraphCommit | None:
        head = await self.head(branch_id=branch_id, projection_hash=projection_hash)
        if head is None:
            return None
        commit_id_text = _json_optional_string(head, "commit_id")
        if commit_id_text is None:
            return None
        try:
            return await self.get_commit(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=UUID(commit_id_text),
            )
        except Exception:
            return None

    async def head_for_lane(self, *, lane: Lane) -> JsonObject | None:
        return await self.head(branch_id=lane.branch_id, projection_hash=lane.lane_hash)

    async def head_commit_for_lane(
        self, *, lane: Lane
    ) -> ObjectInstanceGraphCommit | None:
        return await self.head_commit(
            branch_id=lane.branch_id, projection_hash=lane.lane_hash
        )

    async def domain_commit_id_for_object_instance_graph_commit_id(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        object_instance_graph_commit_id: UUID,
    ) -> UUID | None:
        """Resolve a typed OIG commit wrapper id to its domain commit id in O(1).

        New commit writes maintain a sidecar index. The HEAD check is a bounded
        compatibility repair for stores written before the index existed.
        """

        path = self._object_instance_graph_commit_ref_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
        )
        if path.exists():
            payload = _read_json_object(
                path,
                error_message=f"Invalid OIG commit ref index JSON object: {path}",
            )
            indexed_id = _json_optional_uuid(payload, "object_instance_graph_commit_id")
            domain_commit_id = _json_optional_uuid(payload, "domain_commit_id")
            if (
                indexed_id != object_instance_graph_commit_id
                or domain_commit_id is None
            ):
                raise ValueError(f"Invalid OIG commit ref index payload: {path}")
            return domain_commit_id

        head_commit = await self.head_commit(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        if head_commit is None:
            return None
        if (
            _object_instance_graph_commit_ref_id(head_commit)
            != object_instance_graph_commit_id
        ):
            return None

        self._write_object_instance_graph_commit_ref_index(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=head_commit,
        )
        return head_commit.commit.id

    async def domain_commit_refs_for_object_instance_graph_commit_id(
        self,
        *,
        projection_hash: str,
        object_instance_graph_commit_id: UUID,
    ) -> tuple[ObjectInstanceGraphCommitRef, ...]:
        """Find branches containing an indexed typed OIG commit wrapper id."""

        projection = projection_hash.strip()
        if not projection or not self._oig_root.exists():
            return ()

        refs: list[ObjectInstanceGraphCommitRef] = []
        try:
            branch_dirs = sorted(
                (path for path in self._oig_root.iterdir() if path.is_dir()),
                key=lambda path: path.name,
            )
        except Exception:
            return ()

        for branch_dir in branch_dirs:
            try:
                branch_id = UUID(branch_dir.name)
            except Exception:
                continue

            path = self._object_instance_graph_commit_ref_index_path(
                branch_id=branch_id,
                projection_hash=projection,
                object_instance_graph_commit_id=object_instance_graph_commit_id,
            )
            if path.exists():
                payload = _read_json_object(
                    path,
                    error_message=f"Invalid OIG commit ref index JSON object: {path}",
                )
                indexed_id = _json_optional_uuid(
                    payload,
                    "object_instance_graph_commit_id",
                )
                domain_commit_id = _json_optional_uuid(payload, "domain_commit_id")
                indexed_projection = _json_optional_string(payload, "projection_hash")
                indexed_branch_id = _json_optional_uuid(payload, "branch_id")
                if (
                    indexed_id != object_instance_graph_commit_id
                    or domain_commit_id is None
                    or indexed_projection != projection
                    or indexed_branch_id != branch_id
                ):
                    raise ValueError(f"Invalid OIG commit ref index payload: {path}")
                refs.append(
                    ObjectInstanceGraphCommitRef(
                        branch_id=branch_id,
                        projection_hash=projection,
                        object_instance_graph_commit_id=object_instance_graph_commit_id,
                        domain_commit_id=domain_commit_id,
                        object_instance_graph_identity_id=_json_optional_uuid(
                            payload,
                            "object_instance_graph_identity_id",
                        ),
                        object_instance_graph_id=_json_optional_uuid(
                            payload,
                            "object_instance_graph_id",
                        ),
                        graph_hash_post=_json_optional_string(
                            payload,
                            "graph_hash_post",
                        ),
                    )
                )
                continue

            domain_commit_id = (
                await self.domain_commit_id_for_object_instance_graph_commit_id(
                    branch_id=branch_id,
                    projection_hash=projection,
                    object_instance_graph_commit_id=object_instance_graph_commit_id,
                )
            )
            if domain_commit_id is not None:
                indexed_payload: Mapping[str, object] = {}
                if path.exists():
                    indexed_payload = _read_json_object(
                        path,
                        error_message=(
                            f"Invalid OIG commit ref index JSON object: {path}"
                        ),
                    )
                refs.append(
                    ObjectInstanceGraphCommitRef(
                        branch_id=branch_id,
                        projection_hash=projection,
                        object_instance_graph_commit_id=object_instance_graph_commit_id,
                        domain_commit_id=domain_commit_id,
                        object_instance_graph_identity_id=(
                            _json_optional_uuid(
                                indexed_payload,
                                "object_instance_graph_identity_id",
                            )
                        ),
                        object_instance_graph_id=_json_optional_uuid(
                            indexed_payload,
                            "object_instance_graph_id",
                        ),
                        graph_hash_post=_json_optional_string(
                            indexed_payload,
                            "graph_hash_post",
                        ),
                    )
                )

        return tuple(refs)

    async def domain_commit_refs_for_object_instance_graph_commit_ids(
        self,
        *,
        projection_hash: str,
        object_instance_graph_commit_ids: Iterable[UUID],
        allow_head_fallback: bool = True,
    ) -> dict[UUID, tuple[ObjectInstanceGraphCommitRef, ...]]:
        """Find branches containing indexed typed OIG commit wrapper ids in one pass."""

        projection = projection_hash.strip()
        requested_ids = frozenset(object_instance_graph_commit_ids)
        refs_by_id: dict[UUID, list[ObjectInstanceGraphCommitRef]] = {
            object_instance_graph_commit_id: []
            for object_instance_graph_commit_id in requested_ids
        }
        if not projection or not requested_ids or not self._oig_root.exists():
            return {key: tuple(value) for key, value in refs_by_id.items()}

        try:
            branch_dirs = sorted(
                (path for path in self._oig_root.iterdir() if path.is_dir()),
                key=lambda path: path.name,
            )
        except Exception:
            return {key: tuple(value) for key, value in refs_by_id.items()}

        seen_refs: set[tuple[UUID, UUID, UUID]] = set()
        for branch_dir in branch_dirs:
            try:
                branch_id = UUID(branch_dir.name)
            except Exception:
                continue

            index_dir = self._object_instance_graph_commit_ref_index_dir(
                branch_id,
                projection,
            )
            if not index_dir.is_dir():
                continue
            for path in sorted(index_dir.glob("*.json"), key=lambda item: item.name):
                try:
                    object_instance_graph_commit_id = UUID(path.stem)
                except Exception:
                    continue
                if object_instance_graph_commit_id not in requested_ids:
                    continue
                payload = _read_json_object(
                    path,
                    error_message=f"Invalid OIG commit ref index JSON object: {path}",
                )
                indexed_id = _json_optional_uuid(
                    payload,
                    "object_instance_graph_commit_id",
                )
                domain_commit_id = _json_optional_uuid(payload, "domain_commit_id")
                indexed_projection = _json_optional_string(payload, "projection_hash")
                indexed_branch_id = _json_optional_uuid(payload, "branch_id")
                if (
                    indexed_id != object_instance_graph_commit_id
                    or domain_commit_id is None
                    or indexed_projection != projection
                    or indexed_branch_id != branch_id
                ):
                    raise ValueError(f"Invalid OIG commit ref index payload: {path}")
                ref_key = (
                    object_instance_graph_commit_id,
                    branch_id,
                    domain_commit_id,
                )
                if ref_key not in seen_refs:
                    seen_refs.add(ref_key)
                    refs_by_id[object_instance_graph_commit_id].append(
                        ObjectInstanceGraphCommitRef(
                            branch_id=branch_id,
                            projection_hash=projection,
                            object_instance_graph_commit_id=object_instance_graph_commit_id,
                            domain_commit_id=domain_commit_id,
                            object_instance_graph_identity_id=_json_optional_uuid(
                                payload,
                                "object_instance_graph_identity_id",
                            ),
                            object_instance_graph_id=_json_optional_uuid(
                                payload,
                                "object_instance_graph_id",
                            ),
                            graph_hash_post=_json_optional_string(
                                payload,
                                "graph_hash_post",
                            ),
                        )
                    )

        fallback_requested_ids = frozenset(
            object_instance_graph_commit_id
            for object_instance_graph_commit_id, refs in refs_by_id.items()
            if not refs
        )
        if not fallback_requested_ids or not allow_head_fallback:
            return {key: tuple(value) for key, value in refs_by_id.items()}

        for branch_dir in branch_dirs:
            try:
                branch_id = UUID(branch_dir.name)
            except Exception:
                continue

            head_commit = await self.head_commit(
                branch_id=branch_id,
                projection_hash=projection,
            )
            if head_commit is None:
                continue
            object_instance_graph_commit_id = _object_instance_graph_commit_ref_id(
                head_commit
            )
            if object_instance_graph_commit_id not in fallback_requested_ids:
                continue
            self._write_object_instance_graph_commit_ref_index(
                branch_id=branch_id,
                projection_hash=projection,
                commit=head_commit,
            )
            ref_key = (
                object_instance_graph_commit_id,
                branch_id,
                head_commit.commit.id,
            )
            if ref_key in seen_refs:
                continue
            seen_refs.add(ref_key)
            refs_by_id[object_instance_graph_commit_id].append(
                ObjectInstanceGraphCommitRef(
                    branch_id=branch_id,
                    projection_hash=projection,
                    object_instance_graph_commit_id=object_instance_graph_commit_id,
                    domain_commit_id=head_commit.commit.id,
                    object_instance_graph_identity_id=(
                        head_commit.object_instance_graph_identity_id
                    ),
                    object_instance_graph_id=head_commit.object_instance_graph_id,
                    graph_hash_post=head_commit.graph_hash_post,
                )
            )

        return {key: tuple(value) for key, value in refs_by_id.items()}

    @staticmethod
    def _elapsed_ms(*, started: float, ended: float | None = None) -> int:
        stop = time.monotonic() if ended is None else ended
        return max(int((stop - started) * 1000), 0)

    async def _load_commit_map(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
    ) -> dict[str, ObjectInstanceGraphCommit]:
        commits_dir = self._commits_dir(branch_id, projection_hash)
        commit_map: dict[str, ObjectInstanceGraphCommit] = {}
        if not commits_dir.exists():
            return commit_map

        for entry in commits_dir.glob("*.json"):
            try:
                data = _SESSION_JSON_FILE_CACHE.read_json_object(
                    entry,
                    error_message=f"Invalid commit JSON object: {entry}",
                )
                with disable_autobind():
                    commit = ObjectInstanceGraphCommit.model_validate(data)
                commit_map[str(commit.commit.id)] = commit
            except Exception:
                continue
        return commit_map

    async def iter_lineage_forward(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        head_commit_id: UUID,
        stop_at_commit_id: UUID | None,
    ) -> AsyncIterator[ObjectInstanceGraphCommit]:
        chain: list[ObjectInstanceGraphCommit] = []
        current_commit_id: UUID | None = head_commit_id
        seen_commit_ids: set[UUID] = set()

        while (
            current_commit_id is not None and current_commit_id not in seen_commit_ids
        ):
            seen_commit_ids.add(current_commit_id)
            lookup_commit_id = current_commit_id
            commit = await self.get_commit(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=lookup_commit_id,
            )
            if commit is None:
                domain_commit_id = (
                    await self.domain_commit_id_for_object_instance_graph_commit_id(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        object_instance_graph_commit_id=current_commit_id,
                    )
                )
                if domain_commit_id is not None:
                    lookup_commit_id = domain_commit_id
                    commit = await self.get_commit(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=lookup_commit_id,
                    )
            if commit is None:
                raise ValueError(
                    f"Missing commit file for {current_commit_id} in lane ({branch_id}, {projection_hash})"
                )

            chain.append(commit)
            if stop_at_commit_id is not None and stop_at_commit_id in {
                current_commit_id,
                lookup_commit_id,
            }:
                break

            parents = commit.commit.commit_parents
            if len(parents) > 1:
                raise ValueError(
                    f"Non-linear commit {commit.commit.id} has {len(parents)} parents"
                )
            current_commit_id = parents[0].parent_commit_id if parents else None

        for commit in reversed(chain):
            if stop_at_commit_id is not None and commit.commit.id == stop_at_commit_id:
                continue
            yield commit

    async def put_commit_file(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
        commit_action: CommitActionDescriptor | None = None,
    ) -> bool:
        if not commit.graph_hash_post:
            raise ValueError(
                f"put_commit_file requires commit.graph_hash_post (commit_id={commit.commit.id})"
            )
        if commit.projection_hash and commit.projection_hash != projection_hash:
            raise ValueError(
                f"put_commit_file projection_hash mismatch: lane={projection_hash} commit={commit.projection_hash}"
            )

        commits_dir = self._commits_dir(branch_id, projection_hash)
        commits_dir.mkdir(parents=True, exist_ok=True)
        commit_path = commits_dir / f"{commit.commit.id}.json"
        commit_payload = _commit_payload(commit)

        if commit_path.exists():
            existing_commit_payload = _read_json_object(
                commit_path,
                error_message=f"Existing commit is unreadable: {commit_path}",
            )
            if not _commit_payload_matches(existing_commit_payload, commit):
                raise ValueError(
                    f"Existing commit differs from payload: {commit.commit.id}"
                )
            stale_ref_id = self._repair_existing_commit_identity_metadata(
                commit_path=commit_path,
                existing_commit_payload=existing_commit_payload,
                commit=commit,
            )
            wrote_commit = stale_ref_id is not None
        else:
            _atomic_write(commit_path, _dump_json(commit_payload))
            _SESSION_JSON_FILE_CACHE.invalidate_path(commit_path)
            stale_ref_id = None
            wrote_commit = True

        meta_payload = _commit_meta_payload(commit_action)
        if meta_payload is not None:
            meta_path = commits_dir / f"{commit.commit.id}.meta.json"
            if meta_path.exists():
                existing_meta_payload = _read_json_object(
                    meta_path,
                    error_message=f"Existing commit metadata is unreadable: {meta_path}",
                )
                if existing_meta_payload != meta_payload:
                    raise ValueError(
                        f"Existing commit metadata differs: {commit.commit.id}"
                    )
            else:
                _atomic_write(meta_path, _dump_json(meta_payload))
                _SESSION_JSON_FILE_CACHE.invalidate_path(meta_path)

        self._write_object_instance_graph_commit_ref_index(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
        )
        self._write_object_instance_graph_commit_envelope_index(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
        )
        self._write_object_instance_graph_commit_identity_sidecar_index(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
        )
        self._write_object_instance_graph_commit_health_index(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
        )
        if self._repair_head_commit_identity_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
        ):
            wrote_commit = True
        if stale_ref_id is not None:
            self._remove_stale_object_instance_graph_commit_ref_index(
                branch_id=branch_id,
                projection_hash=projection_hash,
                object_instance_graph_commit_id=stale_ref_id,
                domain_commit_id=commit.commit.id,
            )

        return wrote_commit

    def _repair_head_commit_identity_metadata(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
    ) -> bool:
        head_path = self._lane_dir(branch_id, projection_hash) / "HEAD.json"
        if not head_path.exists():
            return False
        head_payload = _read_json_object(
            head_path,
            error_message=f"Existing HEAD is unreadable: {head_path}",
        )
        head_commit_id = _json_optional_uuid(head_payload, "commit_id")
        if head_commit_id != commit.commit.id:
            return False

        head_graph_hash_post = _json_optional_string(head_payload, "graph_hash_post")
        if head_graph_hash_post and head_graph_hash_post != commit.graph_hash_post:
            raise ValueError(
                "Existing HEAD graph_hash_post differs from commit payload: "
                + f"{commit.commit.id}"
            )
        head_oig_id = _json_optional_uuid(head_payload, "object_instance_graph_id")
        if head_oig_id is not None and head_oig_id != commit.object_instance_graph_id:
            raise ValueError(
                "Existing HEAD object_instance_graph_id differs from commit payload: "
                + f"{commit.commit.id}"
            )

        expected_oig_commit_id = str(_object_instance_graph_commit_ref_id(commit))
        if _json_optional_string(
            head_payload, "object_instance_graph_commit_id"
        ) == expected_oig_commit_id and _json_optional_string(
            head_payload, "object_instance_graph_id"
        ) == str(
            commit.object_instance_graph_id
        ):
            return False

        repaired_payload = dict(head_payload)
        repaired_payload["object_instance_graph_id"] = str(
            commit.object_instance_graph_id
        )
        repaired_payload["object_instance_graph_commit_id"] = expected_oig_commit_id
        repaired_payload["v"] = HEAD_VERSION
        _atomic_write(
            head_path,
            _dump_json(
                _coerce_json_object(
                    repaired_payload,
                    error_message=f"Repaired HEAD did not serialize: {head_path}",
                )
            ),
        )
        _SESSION_JSON_FILE_CACHE.invalidate_path(head_path)
        return True

    async def append(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
        root_object_id: UUID | None = None,
        commit_action: CommitActionDescriptor | None = None,
        object_projection_graph_identity_id: UUID | None = None,
    ) -> dict[str, int]:
        append_total_started = time.monotonic()
        perf: dict[str, int] = {}

        if not commit.graph_hash_post:
            raise ValueError(
                f"Lane append requires commit.graph_hash_post (commit_id={commit.commit.id})"
            )
        if commit.projection_hash and commit.projection_hash != projection_hash:
            raise ValueError(
                f"Lane append projection_hash mismatch: lane={projection_hash} commit={commit.projection_hash}"
            )
        if (
            root_object_id is not None
            and root_object_id != commit.root_source_object_id
        ):
            raise ValueError(
                f"Lane append root_object_id mismatch: explicit={root_object_id} "
                + f"commit.root_source_object_id={commit.root_source_object_id}"
            )

        lock_path = self._lane_dir(branch_id, projection_hash) / "locks" / "append.lock"
        lock_wait_started = time.monotonic()
        lock_acquired = 0.0
        lock_released = 0.0

        async with _lane_append_lock(lock_path=lock_path):
            lock_acquired = time.monotonic()
            perf["lock_wait_ms"] = self._elapsed_ms(
                started=lock_wait_started, ended=lock_acquired
            )
            lane_dir = self._lane_dir(branch_id, projection_hash)

            head_read_started = time.monotonic()
            head = await self.head(branch_id=branch_id, projection_hash=projection_hash)
            perf["head_read_ms"] = self._elapsed_ms(started=head_read_started)

            head_commit_id = (
                _json_optional_uuid(head, "commit_id") if head is not None else None
            )
            previous_hash = (
                _json_optional_string(head, "graph_hash_post")
                if head is not None
                else None
            )
            previous_oig_id = (
                _json_optional_string(head, "object_instance_graph_id")
                if head is not None
                else None
            )
            if previous_oig_id is not None and previous_oig_id != str(
                commit.object_instance_graph_id
            ):
                raise ValueError(
                    f"Lane OIG id mismatch: branch_id={branch_id} "
                    + f"projection_hash={projection_hash} head_object_instance_graph_id={previous_oig_id} "
                    + f"commit_object_instance_graph_id={commit.object_instance_graph_id}"
                )

            validation_started = time.monotonic()
            parents = commit.commit.commit_parents
            if len(parents) > 1:
                raise ValueError(
                    f"Non-linear commit {commit.commit.id} has {len(parents)} parents"
                )
            parent_id = parents[0].parent_commit_id if parents else None

            if head_commit_id is None and parent_id is not None:
                raise ValueError(f"First commit {commit.id} must not have a parent")
            if head_commit_id is not None and parent_id != head_commit_id:
                raise ValueError(
                    f"Lane parent mismatch: parent={parent_id} expected={head_commit_id}"
                )
            if (
                previous_hash
                and commit.graph_hash_pre
                and previous_hash != commit.graph_hash_pre
            ):
                raise ValueError(
                    f"HEAD mismatch: expected graph_hash_pre={previous_hash}, "
                    + f"got {commit.graph_hash_pre} for commit {commit.id}"
                )
            perf["validation_ms"] = self._elapsed_ms(started=validation_started)

            commits_dir = self._commits_dir(branch_id, projection_hash)
            commits_dir.mkdir(parents=True, exist_ok=True)
            commit_path = commits_dir / f"{commit.commit.id}.json"
            commit_payload = _commit_payload(commit)

            write_commit_started = time.monotonic()
            if commit_path.exists():
                existing_commit_payload = _read_json_object(
                    commit_path,
                    error_message=f"Existing commit is unreadable: {commit_path}",
                )
                if not _commit_payload_matches(existing_commit_payload, commit):
                    raise ValueError(
                        f"Existing commit differs from append payload: {commit.commit.id}"
                    )
                stale_ref_id = self._repair_existing_commit_identity_metadata(
                    commit_path=commit_path,
                    existing_commit_payload=existing_commit_payload,
                    commit=commit,
                )
            else:
                _atomic_write(commit_path, _dump_json(commit_payload))
                _SESSION_JSON_FILE_CACHE.invalidate_path(commit_path)
                stale_ref_id = None
            perf["write_commit_file_ms"] = self._elapsed_ms(
                started=write_commit_started
            )

            write_ref_index_started = time.monotonic()
            self._write_object_instance_graph_commit_ref_index(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit=commit,
            )
            self._write_object_instance_graph_commit_envelope_index(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit=commit,
            )
            self._write_object_instance_graph_commit_identity_sidecar_index(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit=commit,
            )
            self._write_object_instance_graph_commit_health_index(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit=commit,
            )
            if stale_ref_id is not None:
                self._remove_stale_object_instance_graph_commit_ref_index(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    object_instance_graph_commit_id=stale_ref_id,
                    domain_commit_id=commit.commit.id,
                )
            perf["write_commit_ref_index_ms"] = self._elapsed_ms(
                started=write_ref_index_started
            )

            meta_payload = _commit_meta_payload(commit_action)
            if meta_payload is not None:
                write_meta_started = time.monotonic()
                meta_path = commits_dir / f"{commit.commit.id}.meta.json"
                if meta_path.exists():
                    existing_meta_payload = _read_json_object(
                        meta_path,
                        error_message=f"Existing commit metadata is unreadable: {meta_path}",
                    )
                    if existing_meta_payload != meta_payload:
                        raise ValueError(
                            f"Existing commit metadata differs from append metadata: {commit.commit.id}"
                        )
                else:
                    _atomic_write(meta_path, _dump_json(meta_payload))
                    _SESSION_JSON_FILE_CACHE.invalidate_path(meta_path)
                perf["write_meta_file_ms"] = self._elapsed_ms(
                    started=write_meta_started
                )
            else:
                perf["write_meta_file_ms"] = 0

            resolved_root_object_id = (
                commit.root_source_object_id
                if root_object_id is None
                else root_object_id
            )
            head_payload: JsonObject = {
                "commit_id": str(commit.commit.id),
                "graph_hash_post": commit.graph_hash_post,
                "object_instance_graph_id": str(commit.object_instance_graph_id),
                "root_object_id": str(resolved_root_object_id),
                "object_instance_graph_commit_id": str(
                    _object_instance_graph_commit_ref_id(commit)
                ),
                "v": HEAD_VERSION,
            }
            write_head_started = time.monotonic()
            head_path = lane_dir / "HEAD.json"
            _atomic_write(head_path, _dump_json(head_payload))
            _SESSION_JSON_FILE_CACHE.invalidate_path(head_path)
            perf["write_head_ms"] = self._elapsed_ms(started=write_head_started)

            receipt = LaneHeadCommitReceipt(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit.commit.id,
                object_instance_graph_commit_id=_object_instance_graph_commit_ref_id(
                    commit
                ),
                created_at_unix_ms=int(commit.commit.created_at.timestamp() * 1000),
                graph_hash_post=commit.graph_hash_post,
                object_instance_graph_id=commit.object_instance_graph_id,
                object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
                object_instance_graph_branch_id=stable_object_instance_graph_branch_id(
                    object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
                    branch_id=branch_id,
                ),
                object_projection_graph_id=_commit_object_projection_graph_id(commit),
                object_projection_graph_identity_id=object_projection_graph_identity_id,
                root_object_id=resolved_root_object_id,
                author_id=commit.commit.author_id,
                commit_action=commit_action,
                class_instance_identity_id=(
                    None
                    if commit_action is None
                    else commit_action.class_instance_identity_id
                ),
            )
            watcher_dispatch_started = time.monotonic()
            await self._dispatch_lane_head_watchers(receipt)
            perf["dispatch_watcher_ms"] = self._elapsed_ms(
                started=watcher_dispatch_started
            )
            lock_released = time.monotonic()

        perf["lock_hold_ms"] = self._elapsed_ms(
            started=lock_acquired, ended=lock_released
        )
        perf["total_ms"] = self._elapsed_ms(started=append_total_started)
        return perf

    async def append_for_lane(
        self,
        *,
        lane: Lane,
        commit: ObjectInstanceGraphCommit,
        root_object_id: UUID | None = None,
    ) -> None:
        _ = await self.append(
            branch_id=lane.branch_id,
            projection_hash=lane.lane_hash,
            commit=commit,
            root_object_id=root_object_id,
        )


class FSSnapshotStore:
    """Filesystem-backed snapshot + index store per `(branch_id, projection_hash, commit_id)`."""

    _aware_root: Path
    _oig_root: Path

    def __init__(self, *, root_dir: Path | None = None) -> None:
        self._aware_root = _resolve_aware_root(root_dir)
        self._oig_root = _resolve_oig_root(root_dir)

    @property
    def aware_root(self) -> Path:
        return self._aware_root

    def _lane_dir(self, branch_id: UUID, projection_hash: str) -> Path:
        return self._oig_root / str(branch_id) / projection_hash

    def _snapshot_health_index_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> Path:
        return (
            self._lane_dir(branch_id, projection_hash)
            / "indexes"
            / "snapshot_health"
            / f"{commit_id}.json"
        )

    def has_snapshot(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> bool:
        return (
            self._lane_dir(branch_id, projection_hash)
            / "snapshots"
            / f"{commit_id}.json"
        ).exists()

    def _write_snapshot_health_index(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        oig: ObjectInstanceGraph,
    ) -> None:
        snapshot_path = (
            self._lane_dir(branch_id, projection_hash)
            / "snapshots"
            / f"{commit_id}.json"
        )
        if not snapshot_path.exists():
            return
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(snapshot_path)
        payload: JsonObject = {
            "v": OBJECT_INSTANCE_GRAPH_SNAPSHOT_HEALTH_INDEX_VERSION,
            "branch_id": str(branch_id),
            "projection_hash": projection_hash,
            "commit_id": str(commit_id),
            "object_instance_graph_id": str(oig.id),
            "graph_hash": str(oig.hash or ""),
            "file_size": file_size,
            "file_mtime_ns": file_mtime_ns,
            "file_ctime_ns": file_ctime_ns,
            "file_sha256": _file_sha256(snapshot_path),
        }
        path = self._snapshot_health_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if path.exists():
            existing_payload = _try_read_json_object(
                path,
                log_prefix=f"Existing OIG snapshot health index is unreadable: {path}",
            )
            if existing_payload == payload:
                return
        _atomic_write(path, _dump_json(payload))
        _SESSION_JSON_FILE_CACHE.invalidate_path(path)

    async def put(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        oig: ObjectInstanceGraph,
        indexes: JsonObject,
    ) -> None:
        lane_dir = self._lane_dir(branch_id, projection_hash)
        snapshots_dir = lane_dir / "snapshots"
        indexes_dir = lane_dir / "indexes"
        snapshots_dir.mkdir(parents=True, exist_ok=True)
        indexes_dir.mkdir(parents=True, exist_ok=True)

        try:
            oig_json = _dump_json(
                _coerce_json_object(
                    oig.model_dump(mode="json", exclude_none=True),
                    error_message="ObjectInstanceGraph snapshot did not serialize to a JSON object",
                )
            )
        except Exception:
            oig_json = oig.model_dump_json(exclude_none=True)

        snapshot_path = snapshots_dir / f"{commit_id}.json"
        index_path = indexes_dir / f"{commit_id}.json"
        _atomic_write(snapshot_path, oig_json)
        _atomic_write(index_path, _dump_json({"v": 1, **indexes}))
        _SESSION_JSON_FILE_CACHE.invalidate_path(snapshot_path)
        _SESSION_JSON_FILE_CACHE.invalidate_path(index_path)

    async def get_snapshot_health_metadata(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphSnapshotHealthMetadata | None:
        snapshot_path = (
            self._lane_dir(branch_id, projection_hash)
            / "snapshots"
            / f"{commit_id}.json"
        )
        if not snapshot_path.exists():
            return None
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(snapshot_path)
        health_path = self._snapshot_health_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if not health_path.exists():
            return None
        payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
            health_path,
            log_prefix=f"Failed reading snapshot health metadata {commit_id}",
        )
        if payload is None:
            return None
        if payload.get("v") != OBJECT_INSTANCE_GRAPH_SNAPSHOT_HEALTH_INDEX_VERSION:
            return None
        if payload.get("branch_id") != str(branch_id):
            return None
        if payload.get("projection_hash") != projection_hash:
            return None
        if payload.get("commit_id") != str(commit_id):
            return None
        if _json_optional_int(payload, "file_size") != file_size:
            return None
        if _json_optional_int(payload, "file_mtime_ns") != file_mtime_ns:
            return None
        if _json_optional_int(payload, "file_ctime_ns") != file_ctime_ns:
            return None
        if _json_optional_string(payload, "file_sha256") != _file_sha256(snapshot_path):
            return None
        object_instance_graph_id = _json_optional_uuid(
            payload,
            "object_instance_graph_id",
        )
        graph_hash = _json_optional_string(payload, "graph_hash")
        file_sha256 = _json_optional_string(payload, "file_sha256")
        if object_instance_graph_id is None or graph_hash is None or not file_sha256:
            return None
        return ObjectInstanceGraphSnapshotHealthMetadata(
            commit_id=commit_id,
            object_instance_graph_id=object_instance_graph_id,
            graph_hash=graph_hash,
            file_size=file_size,
            file_mtime_ns=file_mtime_ns,
            file_ctime_ns=file_ctime_ns,
            file_sha256=file_sha256,
        )

    def write_snapshot_health_metadata(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        oig: ObjectInstanceGraph,
    ) -> None:
        self._write_snapshot_health_index(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            oig=oig,
        )

    async def get(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> tuple[ObjectInstanceGraph, JsonObject] | None:
        lane_dir = self._lane_dir(branch_id, projection_hash)
        snapshot_path = lane_dir / "snapshots" / f"{commit_id}.json"
        if not snapshot_path.exists():
            return None

        try:
            snapshot_payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                snapshot_path,
                log_prefix=f"Failed reading snapshot for {commit_id}",
            )
            if snapshot_payload is None:
                return None
            snapshot = ObjectInstanceGraph.model_validate(snapshot_payload)
            index_path = lane_dir / "indexes" / f"{commit_id}.json"
            indexes = (
                dict(
                    _SESSION_JSON_FILE_CACHE.read_json_object(
                        index_path,
                        error_message=f"Invalid snapshot index JSON object: {index_path}",
                    )
                )
                if index_path.exists()
                else {}
            )
            return snapshot, indexes
        except Exception as exc:
            logger.warning("Failed reading snapshot for %s: %s", commit_id, exc)
            return None

    async def nearest_at_or_before(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID | None,
    ) -> tuple[UUID, ObjectInstanceGraph, JsonObject] | None:
        lane_dir = self._lane_dir(branch_id, projection_hash)
        snapshots_dir = lane_dir / "snapshots"
        if not snapshots_dir.exists():
            return None

        target_commit_id = commit_id
        commits = FSCommitStore(root_dir=self._aware_root)
        if target_commit_id is None:
            head = await commits.head(
                branch_id=branch_id,
                projection_hash=projection_hash,
            )
            if head is None:
                return None
            target_commit_id = _json_optional_uuid(head, "commit_id")
            if target_commit_id is None:
                return None

        current_commit_id: UUID | None = target_commit_id
        visited_commit_ids: set[UUID] = set()
        while (
            current_commit_id is not None
            and current_commit_id not in visited_commit_ids
        ):
            visited_commit_ids.add(current_commit_id)

            snapshot = await self.get(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=current_commit_id,
            )
            if snapshot is not None:
                graph_snapshot, indexes = snapshot
                return current_commit_id, graph_snapshot, indexes

            commit = await commits.get_commit(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=current_commit_id,
            )
            if commit is None:
                return None

            parents = commit.commit.commit_parents
            if len(parents) > 1:
                raise ValueError(
                    f"Non-linear commit {commit.commit.id} has {len(parents)} parents"
                )
            current_commit_id = parents[0].parent_commit_id if parents else None

        return None
