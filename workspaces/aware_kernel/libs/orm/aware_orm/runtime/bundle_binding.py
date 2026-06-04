"""Bundle rail: bind ORM graph entities to ORM classes from an environment bundle.

This is an adapter:
- reads `bundle.bindings` (JSON) and the ORM graph binding snapshot (msgpack)
- delegates actual binding logic to SSOT `graph_binding.py`

It intentionally does NOT install GraphSQL runtime or relationship strategies.
Those are orchestrated by `bundle_runtime_install.py`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .errors import BundleInstallError
from .graph_artifacts import OrmGraphBindingSnapshot
from .graph_binding import (
    bind_entities_by_fqn,
    index_entities_from_msgpack,
)


@dataclass(slots=True)
class BindingEntry:
    class_fqn: str
    canonical_class_config_id: str


@dataclass(slots=True)
class BindingManifest:
    version: str
    bindings: list[BindingEntry]
    planner_version: str | None = None


@dataclass(slots=True)
class BindingInstallResult:
    bound_count: int
    missing_classes: list[str]
    planner_version: str | None = None


def install_bindings_from_payload(
    *,
    bindings: bytes | None,
    orm_graph_binding_snapshot_bytes: bytes,
    strict: bool = False,
) -> BindingInstallResult:
    if not bindings:
        if strict:
            raise BundleInstallError("Environment bundle missing bindings manifest")
        return BindingInstallResult(bound_count=0, missing_classes=[], planner_version=None)

    manifest = _parse_binding_manifest(bindings)
    try:
        entity_index = index_entities_from_msgpack(orm_graph_binding_snapshot_bytes)
    except Exception as exc:
        # Bundle rail uses an explicit ORM-native graph binding snapshot artifact.
        raise BundleInstallError(
            "Environment bundle orm_graph_binding_snapshot_bytes must be a msgpack of "
            f"{OrmGraphBindingSnapshot.__name__}: {exc}"
        ) from exc

    pairs = [(e.class_fqn, e.canonical_class_config_id) for e in manifest.bindings]
    try:
        result = bind_entities_by_fqn(bindings=pairs, entity_index=entity_index, strict=strict)
    except RuntimeError as exc:
        raise BundleInstallError(str(exc)) from exc

    return BindingInstallResult(
        bound_count=result.bound_count,
        missing_classes=result.missing_classes,
        planner_version=manifest.planner_version,
    )


def install_bindings_from_bundle(bundle: Any, *, strict: bool = False) -> BindingInstallResult:
    return install_bindings_from_payload(
        bindings=getattr(bundle, "bindings", None),
        orm_graph_binding_snapshot_bytes=getattr(bundle, "orm_graph_binding_snapshot_bytes", b""),
        strict=strict,
    )


def _parse_binding_manifest(payload: bytes) -> BindingManifest:
    try:
        data = json.loads(payload.decode("utf-8"))
    except Exception as exc:
        raise BundleInstallError(f"Bindings manifest is not valid JSON: {exc}") from exc

    version = data.get("version")
    if version is None:
        raise BundleInstallError("Bindings manifest missing version")

    planner_version = data.get("planner_version")
    bindings: list[BindingEntry] = []
    for raw_entry in data.get("bindings", []):
        if not isinstance(raw_entry, dict):
            continue
        class_fqn = raw_entry.get("class_fqn")
        entity_id = raw_entry.get("canonical_entity_id") or raw_entry.get(
            "canonical_class_config_id"
        )
        if class_fqn and entity_id:
            bindings.append(
                BindingEntry(
                    class_fqn=class_fqn,
                    canonical_class_config_id=str(entity_id),
                )
            )

    return BindingManifest(version=version, planner_version=planner_version, bindings=bindings)
