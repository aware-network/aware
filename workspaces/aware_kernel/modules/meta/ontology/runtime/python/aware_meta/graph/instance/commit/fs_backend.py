from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import cast

from aware_utils.logging import logger

from aware_meta.graph.instance.commit.contract import JsonObject


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
