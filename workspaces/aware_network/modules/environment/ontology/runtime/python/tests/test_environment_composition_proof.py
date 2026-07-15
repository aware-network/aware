from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from uuid import uuid4

import msgpack

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_environment.environment_config.composition_proof import (
    prove_environment_runtime_composition,
    prove_environment_runtime_composition_from_ocgs,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_relationship import (
    ObjectProjectionGraphRelationship,
)
from aware_environment.environment_config.manifest.schema.environment_composition_manifest import (
    EnvironmentCompositionManifest,
    EnvironmentCompositionModule,
)
from aware_environment.environment_config.manifest.schema.environment_manifest import (
    EnvironmentDescriptor,
)


def test_environment_composition_proof_accepts_closed_portal_targets() -> None:
    target_graph, target_opg = _graph_with_projection(name="target")
    source_graph, source_opg = _graph_with_projection(name="source")
    source_opg.object_projection_graph_relationships = [
        _portal_relationship(
            source_opg_id=source_opg.id,
            target_opg_id=target_opg.id,
        )
    ]

    proof = prove_environment_runtime_composition_from_ocgs(
        composition=_composition(),
        manifest_path=Path(
            "/workspace/.aware/environment/runtime/environment.manifest.json"
        ),
        ocgs=(source_graph, target_graph),
    )

    assert proof.valid is True
    assert proof.status == "available"
    assert proof.composed_opg_count == 2
    assert proof.portal_relationship_count == 1
    assert proof.error is None


def test_environment_composition_proof_rejects_dangling_portal_targets() -> None:
    source_graph, source_opg = _graph_with_projection(name="source")
    source_opg.object_projection_graph_relationships = [
        _portal_relationship(
            source_opg_id=source_opg.id,
            target_opg_id=uuid4(),
        )
    ]

    proof = prove_environment_runtime_composition_from_ocgs(
        composition=_composition(),
        manifest_path=Path(
            "/workspace/.aware/environment/runtime/environment.manifest.json"
        ),
        ocgs=(source_graph,),
    )

    assert proof.valid is False
    assert proof.status == "missing"
    assert proof.error is not None
    assert "Dangling portal relationship" in proof.error


def test_environment_composition_proof_loads_module_ocg_snapshot(
    tmp_path: Path,
) -> None:
    source_graph, source_opg = _graph_with_projection(name="source")
    target_graph, target_opg = _graph_with_projection(name="target")
    source_opg.object_projection_graph_relationships = [
        _portal_relationship(
            source_opg_id=source_opg.id,
            target_opg_id=target_opg.id,
        )
    ]
    source_manifest_path = _write_module_runtime_manifest(
        root=tmp_path,
        module_id="source",
        graph=source_graph,
    )
    target_manifest_path = _write_module_runtime_manifest(
        root=tmp_path,
        module_id="target",
        graph=target_graph,
    )
    composition = EnvironmentCompositionManifest(
        version="1.0",
        built_at=datetime(2026, 5, 15, tzinfo=UTC),
        environment=EnvironmentDescriptor(
            id=str(uuid4()),
            title="Kernel",
            canonical_language="aware",
        ),
        ocg_hash="sha256:environment",
        modules=[
            EnvironmentCompositionModule(
                module_id="source",
                manifest_path=source_manifest_path.relative_to(tmp_path).as_posix(),
            ),
            EnvironmentCompositionModule(
                module_id="target",
                manifest_path=target_manifest_path.relative_to(tmp_path).as_posix(),
            ),
        ],
    )
    composition_path = tmp_path / "environment.composition.json"
    composition_path.write_text(
        composition.model_dump_json(),
        encoding="utf-8",
    )

    proof = prove_environment_runtime_composition(
        manifest_path=composition_path,
        workspace_root=tmp_path,
    )

    assert proof.valid is True
    assert proof.composed_opg_count == 2
    assert proof.portal_relationship_count == 1
    assert proof.source_ocg_ids == tuple(
        sorted((str(source_graph.id), str(target_graph.id)))
    )


def _composition() -> EnvironmentCompositionManifest:
    return EnvironmentCompositionManifest(
        version="1.0",
        built_at=datetime(2026, 5, 15, tzinfo=UTC),
        environment=EnvironmentDescriptor(
            id=str(uuid4()),
            title="Kernel",
            canonical_language="aware",
        ),
        ocg_hash="sha256:environment",
        modules=[
            EnvironmentCompositionModule(
                module_id="source",
                manifest_path="modules/source/.aware/environment/runtime/environment.manifest.json",
            )
        ],
    )


def _graph_with_projection(
    *,
    name: str,
) -> tuple[ObjectConfigGraph, ObjectProjectionGraph]:
    graph_id = uuid4()
    opg = ObjectProjectionGraph(
        id=uuid4(),
        object_config_graph_id=graph_id,
        name=f"{name}_projection",
        projection_hash=f"sha256:{name}",
        language=CodeLanguage.aware,
    )
    graph = ObjectConfigGraph(
        id=graph_id,
        name=f"{name}_graph",
        hash=f"sha256:{name}",
        fqn_prefix=f"aware_{name}",
        language=CodeLanguage.aware,
        object_projection_graphs=[opg],
    )
    return graph, opg


def _write_module_runtime_manifest(
    *,
    root: Path,
    module_id: str,
    graph: ObjectConfigGraph,
) -> Path:
    runtime_root = root / "modules" / module_id / ".aware" / "environment" / "runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)
    snapshot_path = runtime_root / "ocg.snapshot.msgpack"
    snapshot_path.write_bytes(
        msgpack.packb(
            graph.model_dump(mode="json", exclude_none=True),
            use_bin_type=True,
        )
    )
    manifest_path = runtime_root / "environment.manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "version": "1.0",
                "built_at": "2026-05-15T00:00:00Z",
                "environment": {
                    "id": str(uuid4()),
                    "title": module_id,
                    "canonical_language": "aware",
                },
                "ocg": {
                    "canonical_id": str(graph.id),
                    "hash": "sha256:snapshot",
                    "semantic_hash": graph.hash,
                    "snapshot": snapshot_path.name,
                },
                "ocg_binding_snapshot": {
                    "file": "bindings.msgpack",
                    "hash": "sha256:bindings",
                },
                "opg_index": {
                    "file": "opg.index.json",
                    "entries": [],
                },
            }
        ),
        encoding="utf-8",
    )
    return manifest_path


def _portal_relationship(
    *,
    source_opg_id: object,
    target_opg_id: object,
) -> ObjectProjectionGraphRelationship:
    return ObjectProjectionGraphRelationship(
        object_projection_graph_id=source_opg_id,
        target_object_projection_graph_id=target_opg_id,
        class_config_relationship_id=uuid4(),
        source_object_projection_graph_node_id=uuid4(),
        target_object_projection_graph_node_id=uuid4(),
    )
