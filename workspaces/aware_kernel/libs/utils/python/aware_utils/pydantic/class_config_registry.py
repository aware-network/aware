"""ClassConfig registry for non-ORM (Pydantic/DTO) packages.

Why this exists
---------------
The canonical runtime needs `ClassConfig.value_mode` (GRAPH_REF vs INLINE_VALUE) to
encode/decode CLASS-typed values without heuristics.

For ORM packages, ClassConfigs are installed via the OCG→ORM binding rail and are
available through `aware_orm.registry.ORMModelRegistry`.

DTO-only packages intentionally do NOT install ORM artifacts, but they still ship
`_aware/ocg.binding.snapshot.msgpack` so runtimes can deterministically learn:
- `ClassConfig.value_mode`
- class-level semantic flags (`is_edge`)

This module keeps an in-memory registry of ClassConfig payloads loaded from those
binding snapshot artifacts.

Notes
-----
- This registry stores *raw JSON dicts* (not ORM-bound objects) to keep it usable by
  DTO packages without pulling in ORM runtime dependencies.
- Higher layers (runtime index builders) can `model_validate` these dicts into the
  generated `aware_meta_ontology.class_.class_config.ClassConfig` type.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from importlib.resources import files
import threading
from typing import Any, Iterable

import msgpack

from aware_utils.logging import logger


DEFAULT_ARTIFACTS_DIR = "_aware"
OCG_BINDING_SNAPSHOT_FILENAME = "ocg.binding.snapshot.msgpack"


@dataclass(frozen=True, slots=True)
class RegisteredClassConfigPayload:
    class_config_id: str
    payload: dict[str, Any]
    source: str | None = None


_lock = threading.Lock()
_registered_packages: set[str] = set()
_class_config_payloads_by_id: dict[str, RegisteredClassConfigPayload] = {}


def register_class_configs_from_binding_snapshot_bytes(
    snapshot_bytes: bytes,
    *,
    source: str | None = None,
) -> int:
    """Register ClassConfig payloads from an `ocg.binding.snapshot.msgpack` payload."""
    try:
        decoded = msgpack.loads(snapshot_bytes, raw=False)
    except Exception as exc:
        raise ValueError(f"Invalid binding snapshot msgpack bytes: {exc}") from exc

    if not isinstance(decoded, dict):
        raise TypeError(f"Binding snapshot must decode to dict, got {type(decoded).__name__}")

    nodes = decoded.get("object_config_graph_nodes")
    if not isinstance(nodes, list):
        raise TypeError("Binding snapshot missing object_config_graph_nodes list")

    count = 0
    with _lock:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            cc = node.get("class_config")
            if not isinstance(cc, dict):
                continue
            cc_id = cc.get("id")
            if not isinstance(cc_id, str) or not cc_id:
                continue
            _class_config_payloads_by_id[cc_id] = RegisteredClassConfigPayload(
                class_config_id=cc_id,
                payload=cc,
                source=source,
            )
            count += 1
    return count


def register_pydantic_package_class_configs(
    *,
    package_prefix: str,
    artifacts_dir: str = DEFAULT_ARTIFACTS_DIR,
    strict: bool = False,
) -> int:
    """Register ClassConfig payloads from a generated package resource."""
    with _lock:
        if package_prefix in _registered_packages:
            return 0
        _registered_packages.add(package_prefix)

    try:
        pkg = import_module(package_prefix)
        root = files(pkg)
        snapshot_path = root.joinpath(artifacts_dir, OCG_BINDING_SNAPSHOT_FILENAME)
        if not snapshot_path.is_file():
            if strict:
                raise FileNotFoundError(
                    f"Missing {OCG_BINDING_SNAPSHOT_FILENAME} under {package_prefix}/{artifacts_dir}"
                )
            return 0
        return register_class_configs_from_binding_snapshot_bytes(
            snapshot_path.read_bytes(),
            source=f"{package_prefix}/{artifacts_dir}/{OCG_BINDING_SNAPSHOT_FILENAME}",
        )
    except Exception as exc:
        if strict:  # pragma: no cover
            raise
        logger.critical(
            "Package bootstrap (pydantic): failed to register class config snapshot for %s: %s",
            package_prefix,
            exc,
        )
        return 0


def iter_registered_class_config_payloads() -> Iterable[RegisteredClassConfigPayload]:
    """Iterate over registered ClassConfig payloads (stable order)."""
    with _lock:
        values = list(_class_config_payloads_by_id.values())
    values.sort(key=lambda v: v.class_config_id)
    return values


def get_registered_class_config_payload(*, class_config_id: str) -> dict[str, Any] | None:
    """Return the raw ClassConfig payload dict for a class_config_id, if registered."""
    with _lock:
        entry = _class_config_payloads_by_id.get(class_config_id)
    return dict(entry.payload) if entry is not None else None


def iter_pydantic_package_class_config_payloads(
    *,
    package_prefix: str,
    artifacts_dir: str = DEFAULT_ARTIFACTS_DIR,
    strict: bool = False,
) -> Iterable[RegisteredClassConfigPayload]:
    """Read ClassConfig payloads directly from one generated DTO package snapshot."""
    try:
        pkg = import_module(package_prefix)
        root = files(pkg)
        snapshot_path = root.joinpath(artifacts_dir, OCG_BINDING_SNAPSHOT_FILENAME)
        if not snapshot_path.is_file():
            if strict:
                raise FileNotFoundError(
                    f"Missing {OCG_BINDING_SNAPSHOT_FILENAME} under {package_prefix}/{artifacts_dir}"
                )
            return ()
        decoded = msgpack.loads(snapshot_path.read_bytes(), raw=False)
    except Exception as exc:
        if strict:  # pragma: no cover
            raise
        logger.critical(
            "Package bootstrap (pydantic): failed to read class config snapshot for %s: %s",
            package_prefix,
            exc,
        )
        return ()

    if not isinstance(decoded, dict):
        if strict:
            raise TypeError(f"Binding snapshot must decode to dict, got {type(decoded).__name__}")
        return ()
    nodes = decoded.get("object_config_graph_nodes")
    if not isinstance(nodes, list):
        if strict:
            raise TypeError("Binding snapshot missing object_config_graph_nodes list")
        return ()

    entries: list[RegisteredClassConfigPayload] = []
    source = f"{package_prefix}/{artifacts_dir}/{OCG_BINDING_SNAPSHOT_FILENAME}"
    for node in nodes:
        if not isinstance(node, dict):
            continue
        cc = node.get("class_config")
        if not isinstance(cc, dict):
            continue
        cc_id = cc.get("id")
        if not isinstance(cc_id, str) or not cc_id:
            continue
        entries.append(
            RegisteredClassConfigPayload(
                class_config_id=cc_id,
                payload=cc,
                source=source,
            )
        )
    entries.sort(key=lambda item: item.class_config_id)
    return tuple(entries)


__all__ = [
    "DEFAULT_ARTIFACTS_DIR",
    "OCG_BINDING_SNAPSHOT_FILENAME",
    "RegisteredClassConfigPayload",
    "get_registered_class_config_payload",
    "iter_registered_class_config_payloads",
    "iter_pydantic_package_class_config_payloads",
    "register_class_configs_from_binding_snapshot_bytes",
    "register_pydantic_package_class_configs",
]
