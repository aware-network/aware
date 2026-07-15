from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import msgpack
from pathlib import Path
from uuid import UUID

from aware_meta.graph.config.compose import compose_object_config_graphs
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_environment.environment_config.manifest.schema.environment_composition_manifest import (
    EnvironmentCompositionManifest,
)
from aware_environment.environment_config.manifest.schema.environment_manifest import (
    EnvironmentManifest,
)


@dataclass(frozen=True, slots=True)
class EnvironmentRuntimeCompositionProof:
    status: str
    manifest_path: str
    environment_id: str | None = None
    environment_title: str | None = None
    ocg_id: str | None = None
    ocg_hash: str | None = None
    module_count: int = 0
    source_ocg_ids: tuple[str, ...] = ()
    source_opg_ids: tuple[str, ...] = ()
    composed_opg_count: int = 0
    portal_relationship_count: int = 0
    error: str | None = None

    @property
    def valid(self) -> bool:
        return self.status == "available" and self.error is None

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema": "aware.environment.environment_runtime_composition_proof.v1",
            "status": self.status,
            "manifest_path": self.manifest_path,
            "module_count": self.module_count,
            "source_ocg_ids": list(self.source_ocg_ids),
            "source_opg_ids": list(self.source_opg_ids),
            "composed_opg_count": self.composed_opg_count,
            "portal_relationship_count": self.portal_relationship_count,
        }
        if self.environment_id is not None:
            payload["environment_id"] = self.environment_id
        if self.environment_title is not None:
            payload["environment_title"] = self.environment_title
        if self.ocg_id is not None:
            payload["ocg_id"] = self.ocg_id
        if self.ocg_hash is not None:
            payload["ocg_hash"] = self.ocg_hash
        if self.error is not None:
            payload["error"] = self.error
        return payload


def prove_environment_runtime_composition(
    *,
    manifest_path: Path,
    workspace_root: Path | None = None,
) -> EnvironmentRuntimeCompositionProof:
    resolved_manifest_path = manifest_path.expanduser().resolve()
    try:
        composition = EnvironmentCompositionManifest.model_validate_json(
            resolved_manifest_path.read_text(encoding="utf-8")
        )
        ocgs = tuple(
            _load_module_ocgs(
                composition=composition,
                manifest_path=resolved_manifest_path,
                workspace_root=workspace_root,
            )
        )
        return prove_environment_runtime_composition_from_ocgs(
            composition=composition,
            manifest_path=resolved_manifest_path,
            ocgs=ocgs,
        )
    except Exception as exc:
        return EnvironmentRuntimeCompositionProof(
            status="missing",
            manifest_path=resolved_manifest_path.as_posix(),
            error=str(exc),
        )


def prove_environment_runtime_composition_from_ocgs(
    *,
    composition: EnvironmentCompositionManifest,
    manifest_path: Path,
    ocgs: tuple[ObjectConfigGraph, ...],
) -> EnvironmentRuntimeCompositionProof:
    resolved_manifest_path = manifest_path.expanduser().resolve()
    try:
        composed = compose_object_config_graphs(
            ocgs=ocgs,
            composite_id=UUID(str(composition.environment.id)),
            composite_name=composition.environment.title or "Aware Environment",
            composite_hash=composition.ocg_hash,
            composite_fqn_prefix="aware_environment",
        )
        source_ocg_ids = tuple(str(ocg.id) for ocg in ocgs if ocg.id is not None)
        source_opg_ids = tuple(
            str(opg.id)
            for ocg in ocgs
            for opg in ocg.object_projection_graphs
            if opg.id is not None
        )
        return EnvironmentRuntimeCompositionProof(
            status="available",
            manifest_path=resolved_manifest_path.as_posix(),
            environment_id=str(composition.environment.id),
            environment_title=composition.environment.title,
            ocg_id=str(composed.id),
            ocg_hash=str(composed.hash),
            module_count=len(tuple(composition.modules or ())),
            source_ocg_ids=tuple(sorted(source_ocg_ids)),
            source_opg_ids=tuple(sorted(source_opg_ids)),
            composed_opg_count=len(tuple(composed.object_projection_graphs or ())),
            portal_relationship_count=_portal_relationship_count(composed),
        )
    except Exception as exc:
        return EnvironmentRuntimeCompositionProof(
            status="missing",
            manifest_path=resolved_manifest_path.as_posix(),
            environment_id=str(composition.environment.id),
            environment_title=composition.environment.title,
            ocg_hash=str(composition.ocg_hash),
            module_count=len(tuple(composition.modules or ())),
            error=str(exc),
        )


def _load_module_ocgs(
    *,
    composition: EnvironmentCompositionManifest,
    manifest_path: Path,
    workspace_root: Path | None,
) -> tuple[ObjectConfigGraph, ...]:
    ocgs: list[ObjectConfigGraph] = []
    for module in composition.modules:
        module_manifest_path = Path(module.manifest_path)
        if not module_manifest_path.is_absolute():
            base_root = (
                workspace_root.resolve()
                if workspace_root is not None
                else manifest_path.parent
            )
            module_manifest_path = (base_root / module_manifest_path).resolve()
        ocgs.append(
            _load_module_ocg_from_runtime_artifact(
                module_manifest_path=module_manifest_path
            )
        )
    return tuple(ocgs)


def _load_module_ocg_from_runtime_artifact(
    *,
    module_manifest_path: Path,
) -> ObjectConfigGraph:
    manifest = EnvironmentManifest.model_validate_json(
        module_manifest_path.read_text(encoding="utf-8")
    )
    snapshot_path = Path(manifest.ocg.snapshot)
    if not snapshot_path.is_absolute():
        snapshot_path = module_manifest_path.parent / snapshot_path
    payload = msgpack.unpackb(snapshot_path.resolve().read_bytes(), raw=False)
    if not isinstance(payload, Mapping):
        raise RuntimeError(
            "Environment composition proof OCG snapshot must contain a mapping "
            f"payload (manifest={module_manifest_path}, snapshot={snapshot_path})"
        )
    return ObjectConfigGraph.model_validate(payload)


def _portal_relationship_count(ocg: ObjectConfigGraph) -> int:
    return sum(
        len(tuple(getattr(opg, "object_projection_graph_relationships", ()) or ()))
        for opg in tuple(getattr(ocg, "object_projection_graphs", ()) or ())
    )


__all__ = [
    "EnvironmentRuntimeCompositionProof",
    "prove_environment_runtime_composition",
    "prove_environment_runtime_composition_from_ocgs",
]
