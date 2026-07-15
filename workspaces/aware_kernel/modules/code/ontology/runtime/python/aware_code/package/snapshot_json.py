from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
import os
from pathlib import Path
from uuid import UUID

from aware_meta.graph.instance.commit.perf_trace import commit_perf_span


def stable_json_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(dict(payload), separators=(",", ":"), sort_keys=True)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def read_json_object_or_none(path: Path) -> dict[str, object] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(raw, dict):
        return None
    result: dict[str, object] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            return None
        result[key] = value
    return result


def atomic_write_json(
    path: Path,
    payload: Mapping[str, object],
    *,
    sort_keys: bool = True,
    phase_prefix: str | None = None,
    category: str = "code_package.snapshot_json",
    metadata: Mapping[str, object] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    base_metadata = dict(metadata or {})
    if phase_prefix is None:
        encoded = json.dumps(dict(payload), separators=(",", ":"), sort_keys=sort_keys)
        with open(tmp, "w", encoding="utf-8") as file_handle:
            file_handle.write(encoded)
            file_handle.flush()
            os.fsync(file_handle.fileno())
        tmp.replace(path)
        return
    with commit_perf_span(
        phase=f"{phase_prefix}.encode",
        category=category,
        metadata=base_metadata,
    ):
        encoded = json.dumps(dict(payload), separators=(",", ":"), sort_keys=sort_keys)
    write_metadata = {**base_metadata, "byte_count": len(encoded)}
    with commit_perf_span(
        phase=f"{phase_prefix}.write_fsync",
        category=category,
        metadata=write_metadata,
    ):
        with open(tmp, "w", encoding="utf-8") as file_handle:
            file_handle.write(encoded)
            file_handle.flush()
            os.fsync(file_handle.fileno())
    with commit_perf_span(
        phase=f"{phase_prefix}.replace",
        category=category,
        metadata=write_metadata,
    ):
        tmp.replace(path)


def head_string(head: object, key: str) -> str | None:
    if not isinstance(head, Mapping):
        return None
    value = head.get(key)
    if isinstance(value, str) and value.strip():
        return value
    return None


def head_uuid(head: object, key: str) -> UUID | None:
    value = head_string(head, key)
    if value is None:
        return None
    try:
        return UUID(value)
    except ValueError:
        return None


def payload_int(payload: Mapping[str, object], key: str) -> int | None:
    value = payload.get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None
