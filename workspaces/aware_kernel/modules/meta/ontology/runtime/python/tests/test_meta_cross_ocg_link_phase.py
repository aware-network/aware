from __future__ import annotations

from uuid import uuid4

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.builder import ObjectConfigGraphBuildResult
from aware_meta.graph.config.cross_ocg import link_cross_ocg_relationships
from aware_meta.graph.config.stable_ids import (
    stable_object_config_graph_relationship_id,
)
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipType,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph


def test_meta_cross_ocg_link_phase_materializes_relationship() -> None:
    source_graph = _graph(name="source")
    target_graph = _graph(name="target")
    relationship = _relationship()
    result = ObjectConfigGraphBuildResult(
        graph=source_graph,
        cross_relationships_by_target_ocg={target_graph.id: [relationship]},
        cross_class_configs_by_target_ocg={},
        package_materialization_receipt=None,
    )

    rel_map = link_cross_ocg_relationships(
        build_results_by_language={CodeLanguage.aware: result},
        external_graphs=[target_graph],
    )

    assert (source_graph.id, target_graph.id) in rel_map
    assert len(source_graph.object_config_graph_relationships) == 1
    ocg_rel = source_graph.object_config_graph_relationships[0]
    assert ocg_rel.id == stable_object_config_graph_relationship_id(
        object_config_graph_id=source_graph.id,
        target_object_config_graph_id=target_graph.id,
    )
    assert ocg_rel.target_object_config_graph_id == target_graph.id
    assert ocg_rel.class_config_relationships == [relationship]


def test_meta_cross_ocg_link_phase_preserves_multiple_relationships() -> None:
    source_graph = _graph(name="source")
    target_graph = _graph(name="target")
    relationships = [_relationship(), _relationship()]
    result = ObjectConfigGraphBuildResult(
        graph=source_graph,
        cross_relationships_by_target_ocg={target_graph.id: relationships},
        cross_class_configs_by_target_ocg={},
        package_materialization_receipt=None,
    )

    link_cross_ocg_relationships(
        build_results_by_language={CodeLanguage.aware: result},
        external_graphs=[target_graph],
    )

    assert len(source_graph.object_config_graph_relationships) == 1
    ocg_rel = source_graph.object_config_graph_relationships[0]
    assert ocg_rel.class_config_relationships == relationships
    assert len({rel.id for rel in ocg_rel.class_config_relationships}) == 2


def _graph(*, name: str) -> ObjectConfigGraph:
    return ObjectConfigGraph(
        id=uuid4(),
        name=f"{name}_graph",
        hash=f"sha256:{name}",
        fqn_prefix=f"aware_{name}",
        language=CodeLanguage.aware,
    )


def _relationship() -> ClassConfigRelationship:
    return ClassConfigRelationship(
        id=uuid4(),
        relationship_key=f"rel_{uuid4().hex}",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=False,
        class_config_id=uuid4(),
        target_class_config_id=uuid4(),
    )
