from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.compose import compose_object_config_graphs
from aware_meta.graph.config.lane.projection import compose_ocg_seed_schema_graph
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_overlay import ClassConfigOverlay
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipType,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_identity import (
    ObjectConfigGraphIdentity,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.config.object_config_graph_overlay import (
    ObjectConfigGraphOverlay,
)
from aware_meta_ontology.graph.config.object_config_graph_relationship import (
    ObjectConfigGraphRelationship,
)
from aware_meta_ontology.graph.config.object_config_graph_relationship_class import (
    ObjectConfigGraphRelationshipClass,
)
from aware_meta_ontology.graph.instance.object_instance_graph_identity import (
    ObjectInstanceGraphIdentity,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphNodeSelection,
)
from aware_meta_ontology.graph.projection.object_projection_graph_identity import (
    ObjectProjectionGraphIdentity,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)
from aware_meta_ontology.graph.projection.object_projection_graph_observable import (
    ObjectProjectionGraphObservable,
)
from aware_meta_ontology.graph.projection.object_projection_graph_relationship import (
    ObjectProjectionGraphRelationship,
)
from aware_meta.graph.config.stable_ids import (
    stable_object_config_graph_identity_id,
    stable_object_projection_graph_identity_id,
)
from aware_meta.graph.projection.stable_ids import (
    stable_object_projection_graph_observable_id,
)


def _make_ocg(*, name: str, ocg_hash: str) -> ObjectConfigGraph:
    return ObjectConfigGraph(
        id=uuid4(),
        name=name,
        description=None,
        hash=ocg_hash,
        fqn_prefix=f"{name}_pkg",
        language=CodeLanguage.aware,
    )


class _CaptureTimings:
    def __init__(self) -> None:
        self.durations: dict[str, float] = {}
        self.metrics: dict[str, object] = {}

    def add(self, name: str, duration_s: float) -> object:
        self.durations[name] = duration_s
        return None

    def metric(self, key: str, value: object) -> object:
        self.metrics[key] = value
        return None


def test_compose_object_config_graphs_merges_duplicate_nodes_after_container_rebind() -> (
    None
):
    composite_id = uuid4()
    class_config = ClassConfig(
        id=uuid4(),
        class_fqn="aware_storage.default.bucket.StorageBucket",
        name="StorageBucket",
    )
    node_id = uuid4()
    class_config.object_config_graph_node_id = node_id

    environment_graph = _make_ocg(name="environment", ocg_hash="sha256:environment")
    semantic_graph = _make_ocg(name="storage", ocg_hash="sha256:storage")
    environment_graph.object_config_graph_nodes.append(
        ObjectConfigGraphNode(
            id=node_id,
            type=ObjectConfigGraphNodeType.class_,
            node_key=class_config.class_fqn,
            class_config=class_config.model_copy(deep=True),
            object_config_graph_id=environment_graph.id,
        )
    )
    semantic_graph.object_config_graph_nodes.append(
        ObjectConfigGraphNode(
            id=node_id,
            type=ObjectConfigGraphNodeType.class_,
            node_key=class_config.class_fqn,
            class_config=class_config.model_copy(deep=True),
            object_config_graph_id=semantic_graph.id,
        )
    )

    out = compose_object_config_graphs(
        ocgs=[environment_graph, semantic_graph],
        composite_id=composite_id,
        composite_name="Composed",
        composite_hash="sha256:composed",
        composite_fqn_prefix="aware_composite",
    )

    matching_nodes = [
        node for node in out.object_config_graph_nodes if node.id == node_id
    ]
    assert len(matching_nodes) == 1
    assert matching_nodes[0].object_config_graph_id == composite_id


def test_compose_object_config_graphs_requires_explicit_composite_fqn_prefix() -> None:
    with pytest.raises(
        ValueError,
        match="requires explicit composite_fqn_prefix",
    ):
        compose_object_config_graphs(
            ocgs=[_make_ocg(name="source", ocg_hash="sha256:source")],
            composite_id=uuid4(),
            composite_name="Composed",
            composite_hash="sha256:composed",
            composite_fqn_prefix="",
        )


def test_compose_object_config_graphs_merges_relationships_with_thin_target_refs() -> (
    None
):
    composite_id = uuid4()
    source_id = uuid4()
    relationship_id = uuid4()
    class_config_id = uuid4()
    target_class_config_id = uuid4()
    class_relationship_id = uuid4()
    relationship_class_id = uuid4()
    target_graph = _make_ocg(name="target", ocg_hash="sha256:target")
    target_node = ObjectConfigGraphNode(
        id=target_class_config_id,
        type=ObjectConfigGraphNodeType.class_,
        node_key="target.Target",
        object_config_graph_id=target_graph.id,
        class_config=ClassConfig(
            id=target_class_config_id,
            class_fqn="target.Target",
            name="Target",
        ),
    )
    target_graph.object_config_graph_nodes.append(target_node)
    relationship = ClassConfigRelationship(
        id=class_relationship_id,
        class_config_id=class_config_id,
        target_class_config_id=target_class_config_id,
        relationship_key="source.target",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=False,
    )
    relationship_class = ObjectConfigGraphRelationshipClass(
        id=relationship_class_id,
        object_config_graph_relationship_id=relationship_id,
        class_config_id=class_config_id,
    )
    first = _make_ocg(name="first", ocg_hash="sha256:first")
    first.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            id=relationship_id,
            object_config_graph_id=source_id,
            target_object_config_graph_id=target_graph.id,
            target_object_config_graph=target_graph,
            class_config_relationships=[relationship],
            object_config_graph_relationship_classes=[relationship_class],
        )
    )
    second = _make_ocg(name="second", ocg_hash="sha256:second")
    second.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            id=relationship_id,
            object_config_graph_id=uuid4(),
            target_object_config_graph_id=target_graph.id,
            target_object_config_graph=target_graph,
            class_config_relationships=[relationship.model_copy()],
            object_config_graph_relationship_classes=[relationship_class.model_copy()],
        )
    )

    out = compose_object_config_graphs(
        ocgs=[first, second, target_graph],
        composite_id=composite_id,
        composite_name="Composed",
        composite_hash="sha256:composed",
        composite_fqn_prefix="aware_composite",
    )

    assert len(out.object_config_graph_relationships) == 1
    out_relationship = out.object_config_graph_relationships[0]
    assert out_relationship.object_config_graph_id == composite_id
    assert out_relationship.target_object_config_graph is not target_graph
    assert out_relationship.target_object_config_graph is not None
    assert out_relationship.target_object_config_graph.id == target_graph.id
    assert out_relationship.target_object_config_graph.object_config_graph_nodes == []


def test_compose_object_config_graphs_rejects_conflicting_relationship_children() -> (
    None
):
    composite_id = uuid4()
    target_graph = _make_ocg(name="target", ocg_hash="sha256:target")
    relationship_id = uuid4()
    class_config_id = uuid4()
    target_class_config_id = uuid4()
    class_relationship_id = uuid4()
    first = _make_ocg(name="first", ocg_hash="sha256:first")
    first.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            id=relationship_id,
            object_config_graph_id=first.id,
            target_object_config_graph_id=target_graph.id,
            class_config_relationships=[
                ClassConfigRelationship(
                    id=class_relationship_id,
                    class_config_id=class_config_id,
                    target_class_config_id=target_class_config_id,
                    relationship_key="source.target",
                    relationship_type=ClassConfigRelationshipType.many_to_one,
                    forward_required=False,
                )
            ],
        )
    )
    second = _make_ocg(name="second", ocg_hash="sha256:second")
    second.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            id=relationship_id,
            object_config_graph_id=second.id,
            target_object_config_graph_id=target_graph.id,
            class_config_relationships=[
                ClassConfigRelationship(
                    id=class_relationship_id,
                    class_config_id=class_config_id,
                    target_class_config_id=target_class_config_id,
                    relationship_key="source.other_target",
                    relationship_type=ClassConfigRelationshipType.many_to_one,
                    forward_required=False,
                )
            ],
        )
    )

    with pytest.raises(
        ValueError,
        match="Conflicting object_config_graph_relationship entry",
    ):
        compose_object_config_graphs(
            ocgs=[first, second, target_graph],
            composite_id=composite_id,
            composite_name="Composed",
            composite_hash="sha256:composed",
            composite_fqn_prefix="aware_composite",
        )


def test_compose_object_config_graphs_keeps_namespace_only_topology() -> None:
    ocg1 = _make_ocg(name="schema", ocg_hash="sha256:schema")
    ocg2 = _make_ocg(name="external", ocg_hash="sha256:external")
    node = ObjectConfigGraphNode(
        id=uuid4(),
        type=ObjectConfigGraphNodeType.class_,
        node_key="external.Node",
        object_config_graph_id=ocg2.id,
    )
    ocg2.object_config_graph_nodes.append(node)
    timings = _CaptureTimings()

    out = compose_object_config_graphs(
        ocgs=[ocg1, ocg2],
        composite_id=uuid4(),
        composite_name="Composed",
        composite_hash="sha256:composed",
        composite_fqn_prefix="aware_composite",
        timings=timings,
        timing_prefix="seed_schema_view.compose",
    )

    assert [item.id for item in out.object_config_graph_nodes] == [node.id]
    assert "seed_schema_view.compose.merge_nodes" in timings.durations


def test_compose_ocg_seed_schema_graph_keeps_namespace_only_topology() -> None:
    schema_graph = _make_ocg(name="schema", ocg_hash="sha256:schema")
    external_graph = _make_ocg(name="external", ocg_hash="sha256:external")
    external_node = ObjectConfigGraphNode(
        id=uuid4(),
        type=ObjectConfigGraphNodeType.class_,
        node_key="external.Node",
        object_config_graph_id=external_graph.id,
    )
    external_graph.object_config_graph_nodes.append(external_node)
    timings = _CaptureTimings()

    out = compose_ocg_seed_schema_graph(
        schema_graph=schema_graph,
        external_graphs=[external_graph],
        timings=timings,
    )

    assert [item.id for item in out.object_config_graph_nodes] == [external_node.id]
    assert timings.metrics["seed_schema_view_effective_external_graph_count"] == 1


def test_compose_ocg_seed_schema_graph_uses_opg_required_schema_scope() -> None:
    schema_graph = _make_ocg(name="schema", ocg_hash="sha256:schema")
    external_graph = _make_ocg(name="external", ocg_hash="sha256:external")
    schema_class = ClassConfig(
        id=uuid4(),
        name="ObjectConfigGraph",
        class_fqn="aware_meta.ObjectConfigGraph",
    )
    external_class = ClassConfig(
        id=uuid4(),
        name="Unused",
        class_fqn="aware_external.Unused",
    )
    schema_graph.object_config_graph_nodes.append(
        ObjectConfigGraphNode(
            id=uuid4(),
            type=ObjectConfigGraphNodeType.class_,
            node_key="aware_meta.ObjectConfigGraph",
            object_config_graph_id=schema_graph.id,
            class_config=schema_class,
            class_config_id=schema_class.id,
        )
    )
    external_graph.object_config_graph_nodes.append(
        ObjectConfigGraphNode(
            id=uuid4(),
            type=ObjectConfigGraphNodeType.class_,
            node_key="aware_external.Unused",
            object_config_graph_id=external_graph.id,
            class_config=external_class,
            class_config_id=external_class.id,
        )
    )
    opg = ObjectProjectionGraph(
        id=uuid4(),
        object_config_graph_id=schema_graph.id,
        name="ObjectConfigGraph",
        language=CodeLanguage.aware,
        projection_hash="sha256:opg:object-config-graph",
    )
    opg.object_projection_graph_nodes.append(
        ObjectProjectionGraphNode(
            class_config_id=schema_class.id,
            object_projection_graph_id=opg.id,
            is_root=True,
            selection=ObjectProjectionGraphNodeSelection.one,
        )
    )
    timings = _CaptureTimings()

    out = compose_ocg_seed_schema_graph(
        schema_graph=schema_graph,
        external_graphs=[external_graph],
        object_projection_graph=opg,
        timings=timings,
    )

    assert out is schema_graph
    assert timings.metrics["seed_schema_view_effective_external_graph_count"] == 0
    assert timings.metrics["seed_schema_view_cache_hit"] is False
    assert "seed_schema_view.compose.merge_nodes" not in timings.durations


def test_compose_object_config_graphs_merges_overlays_by_language() -> None:
    cls_a = uuid4()
    cls_b = uuid4()

    ocg1 = _make_ocg(name="a", ocg_hash="sha256:a")
    overlay1_id = uuid4()
    overlay1 = ObjectConfigGraphOverlay(
        id=overlay1_id,
        language=CodeLanguage.sql,
        object_config_graph_id=ocg1.id,
        class_config_overlays=[
            ClassConfigOverlay(
                id=uuid4(),
                object_config_graph_overlay_id=overlay1_id,
                class_config_id=cls_a,
                rendered_name="enum_",
                lang_flags=None,
            )
        ],
    )
    ocg1.object_config_graph_overlays.append(overlay1)

    ocg2 = _make_ocg(name="b", ocg_hash="sha256:b")
    overlay2_id = uuid4()
    overlay2 = ObjectConfigGraphOverlay(
        id=overlay2_id,
        language=CodeLanguage.sql,
        object_config_graph_id=ocg2.id,
        class_config_overlays=[
            ClassConfigOverlay(
                id=uuid4(),
                object_config_graph_overlay_id=overlay2_id,
                class_config_id=cls_b,
                rendered_name="select_",
                lang_flags=None,
            )
        ],
    )
    ocg2.object_config_graph_overlays.append(overlay2)

    composite_id = uuid4()
    out = compose_object_config_graphs(
        ocgs=[ocg1, ocg2],
        composite_id=composite_id,
        composite_name="Composed",
        composite_hash="sha256:composed",
        composite_fqn_prefix="aware_composite",
    )

    assert out.id == composite_id
    assert out.fqn_prefix == "aware_composite"
    assert out.language == CodeLanguage.aware

    sql_overlays = [
        o for o in out.object_config_graph_overlays if o.language == CodeLanguage.sql
    ]
    assert len(sql_overlays) == 1
    sql_overlay = sql_overlays[0]

    expected_overlay_id = uuid5(
        NAMESPACE_URL, f"aware:ocg:{composite_id}:overlay:{CodeLanguage.sql.value}"
    )
    assert sql_overlay.id == expected_overlay_id
    assert sql_overlay.object_config_graph_id == composite_id

    by_class: dict[UUID, ClassConfigOverlay] = {
        co.class_config_id: co for co in sql_overlay.class_config_overlays
    }
    assert by_class[cls_a].rendered_name == "enum_"
    assert by_class[cls_b].rendered_name == "select_"
    assert by_class[cls_a].object_config_graph_overlay_id == expected_overlay_id
    assert by_class[cls_b].object_config_graph_overlay_id == expected_overlay_id


def test_compose_object_config_graphs_fails_on_overlay_conflict() -> None:
    cls_id = uuid4()

    ocg1 = _make_ocg(name="a", ocg_hash="sha256:a")
    overlay1_id = uuid4()
    ocg1.object_config_graph_overlays.append(
        ObjectConfigGraphOverlay(
            id=overlay1_id,
            language=CodeLanguage.sql,
            object_config_graph_id=ocg1.id,
            class_config_overlays=[
                ClassConfigOverlay(
                    id=uuid4(),
                    object_config_graph_overlay_id=overlay1_id,
                    class_config_id=cls_id,
                    rendered_name="enum_",
                    lang_flags=None,
                )
            ],
        )
    )

    ocg2 = _make_ocg(name="b", ocg_hash="sha256:b")
    overlay2_id = uuid4()
    ocg2.object_config_graph_overlays.append(
        ObjectConfigGraphOverlay(
            id=overlay2_id,
            language=CodeLanguage.sql,
            object_config_graph_id=ocg2.id,
            class_config_overlays=[
                ClassConfigOverlay(
                    id=uuid4(),
                    object_config_graph_overlay_id=overlay2_id,
                    class_config_id=cls_id,
                    rendered_name="enum__different",
                    lang_flags=None,
                )
            ],
        )
    )

    with pytest.raises(ValueError, match="Conflicting overlay class"):
        compose_object_config_graphs(
            ocgs=[ocg1, ocg2],
            composite_id=uuid4(),
            composite_name="Composed",
            composite_hash="sha256:composed",
            composite_fqn_prefix="aware_composite",
        )


def test_compose_object_config_graphs_fails_on_projection_hash_collision() -> None:
    ocg1 = _make_ocg(name="a", ocg_hash="sha256:a")
    ocg2 = _make_ocg(name="b", ocg_hash="sha256:b")

    ocg1.object_projection_graphs.append(
        ObjectProjectionGraph(
            id=uuid4(),
            object_config_graph_id=ocg1.id,
            name="A",
            language=CodeLanguage.aware,
            projection_hash="sha256:opg:dupe",
        )
    )
    ocg2.object_projection_graphs.append(
        ObjectProjectionGraph(
            id=uuid4(),
            object_config_graph_id=ocg2.id,
            name="B",
            language=CodeLanguage.aware,
            projection_hash="sha256:opg:dupe",
        )
    )

    with pytest.raises(
        ValueError, match="Duplicate ObjectProjectionGraph\\.projection_hash"
    ):
        compose_object_config_graphs(
            ocgs=[ocg1, ocg2],
            composite_id=uuid4(),
            composite_name="Composed",
            composite_hash="sha256:composed",
            composite_fqn_prefix="aware_composite",
        )


def test_compose_object_config_graphs_portal_validation_can_be_disabled() -> None:
    ocg = _make_ocg(name="a", ocg_hash="sha256:a")
    source_opg_id = uuid4()
    missing_target_opg_id = uuid4()

    source_opg = ObjectProjectionGraph(
        id=source_opg_id,
        object_config_graph_id=ocg.id,
        name="network_node",
        language=CodeLanguage.aware,
        projection_hash="sha256:opg:network_node",
    )
    source_opg.object_projection_graph_relationships.append(
        ObjectProjectionGraphRelationship(
            id=uuid4(),
            object_projection_graph_id=source_opg_id,
            target_object_projection_graph_id=missing_target_opg_id,
            class_config_relationship_id=uuid4(),
            source_object_projection_graph_node_id=uuid4(),
            target_object_projection_graph_node_id=uuid4(),
        )
    )
    ocg.object_projection_graphs.append(source_opg)

    with pytest.raises(ValueError, match="Dangling portal relationship"):
        compose_object_config_graphs(
            ocgs=[ocg],
            composite_id=uuid4(),
            composite_name="Composed",
            composite_hash="sha256:composed",
            composite_fqn_prefix="aware_composite",
        )

    out = compose_object_config_graphs(
        ocgs=[ocg],
        composite_id=uuid4(),
        composite_name="Composed",
        composite_hash="sha256:composed",
        composite_fqn_prefix="aware_composite",
        validate_portals=False,
    )
    assert out is not None


def test_compose_object_config_graphs_ignores_runtime_oigi_children_when_merging_opgis() -> (
    None
):
    source = _make_ocg(name="environment", ocg_hash="sha256:environment")
    source.fqn_prefix = "aware_environment"
    opg_id = uuid4()
    ocgi_id = uuid4()
    opgi_id = uuid4()
    source.object_config_graph_identity = ObjectConfigGraphIdentity(
        id=ocgi_id,
        key="aware_environment",
        label="ocg:aware_environment",
        object_projection_graph_identities=[
            ObjectProjectionGraphIdentity(
                id=opgi_id,
                object_config_graph_identity_id=ocgi_id,
                object_projection_graph_id=opg_id,
                projection_name="Environment",
                label="opg:environment",
            )
        ],
    )
    source.object_projection_graphs.append(
        ObjectProjectionGraph(
            id=opg_id,
            object_config_graph_id=source.id,
            name="environment",
            language=CodeLanguage.aware,
            projection_hash="sha256:opg:environment",
        )
    )
    duplicate = source.model_copy(deep=True)
    duplicate_ocgi = duplicate.object_config_graph_identity
    assert duplicate_ocgi is not None
    duplicate_ocgi.object_projection_graph_identities[
        0
    ].object_instance_graph_identities.append(
        ObjectInstanceGraphIdentity(
            id=uuid4(),
            object_projection_graph_identity_id=opgi_id,
            object_instance_graph_id=uuid4(),
            label="runtime head",
        )
    )

    out = compose_object_config_graphs(
        ocgs=[source, duplicate],
        composite_id=uuid4(),
        composite_name="Composed",
        composite_hash="sha256:composed",
        composite_fqn_prefix="aware_environment",
    )

    out_ocgi = out.object_config_graph_identity
    assert out_ocgi is not None
    identities = out_ocgi.object_projection_graph_identities
    assert len(identities) == 1
    assert identities[0].id == opgi_id
    assert identities[0].object_instance_graph_identities == []


def test_compose_object_config_graphs_rejects_projection_identity_descriptor_conflict() -> (
    None
):
    source = _make_ocg(name="environment", ocg_hash="sha256:environment")
    source.fqn_prefix = "aware_environment"
    opg_id = uuid4()
    ocgi_id = uuid4()
    opgi_id = uuid4()
    source.object_config_graph_identity = ObjectConfigGraphIdentity(
        id=ocgi_id,
        key="aware_environment",
        label="ocg:aware_environment",
        object_projection_graph_identities=[
            ObjectProjectionGraphIdentity(
                id=opgi_id,
                object_config_graph_identity_id=ocgi_id,
                object_projection_graph_id=opg_id,
                projection_name="Environment",
                label="opg:environment",
            )
        ],
    )
    source.object_projection_graphs.append(
        ObjectProjectionGraph(
            id=opg_id,
            object_config_graph_id=source.id,
            name="environment",
            language=CodeLanguage.aware,
            projection_hash="sha256:opg:environment",
        )
    )
    conflicting = source.model_copy(deep=True)
    conflicting_ocgi = conflicting.object_config_graph_identity
    assert conflicting_ocgi is not None
    conflicting_ocgi.object_projection_graph_identities[0].label = "different"

    with pytest.raises(
        ValueError, match="Conflicting object_projection_graph_identity entry"
    ):
        compose_object_config_graphs(
            ocgs=[source, conflicting],
            composite_id=uuid4(),
            composite_name="Composed",
            composite_hash="sha256:composed",
            composite_fqn_prefix="aware_environment",
        )


def test_compose_object_config_graphs_prefers_source_opgi_over_composite_opgi() -> None:
    composite_view = _make_ocg(name="environment", ocg_hash="sha256:environment")
    composite_view.fqn_prefix = "aware_environment"
    source = _make_ocg(name="environment", ocg_hash="sha256:environment")
    source.fqn_prefix = "aware_environment_source"
    opg_id = uuid4()
    composite_ocgi_id = stable_object_config_graph_identity_id(key="aware_environment")
    source_ocgi_id = stable_object_config_graph_identity_id(
        key="aware_environment_source"
    )
    composite_opgi_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=composite_ocgi_id,
        object_projection_graph_id=opg_id,
    )
    source_opgi_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=source_ocgi_id,
        object_projection_graph_id=opg_id,
    )

    def make_opg(*, object_config_graph_id: UUID) -> ObjectProjectionGraph:
        return ObjectProjectionGraph(
            id=opg_id,
            object_config_graph_id=object_config_graph_id,
            name="environment",
            language=CodeLanguage.aware,
            projection_hash="sha256:opg:environment",
        )

    def make_opgi(
        *,
        object_config_graph_identity_id: UUID,
        object_projection_graph_identity_id: UUID,
        observable_kind: str | None,
        observable_label: str | None,
    ) -> ObjectProjectionGraphIdentity:
        observable_id = stable_object_projection_graph_observable_id(
            object_projection_graph_identity_id=object_projection_graph_identity_id,
            observable_key="default",
        )
        return ObjectProjectionGraphIdentity(
            id=object_projection_graph_identity_id,
            object_config_graph_identity_id=object_config_graph_identity_id,
            object_projection_graph_id=opg_id,
            projection_name="Environment",
            label="opg:environment",
            object_projection_graph_observables=[
                ObjectProjectionGraphObservable(
                    id=observable_id,
                    object_projection_graph_identity_id=object_projection_graph_identity_id,
                    key="environment:default",
                    observable_key="default",
                    kind=observable_kind,
                    label=observable_label,
                    is_default=True,
                )
            ],
        )

    composite_view.object_config_graph_identity = ObjectConfigGraphIdentity(
        id=composite_ocgi_id,
        key="aware_environment",
        label="ocg:aware_environment",
        object_projection_graph_identities=[
            make_opgi(
                object_config_graph_identity_id=composite_ocgi_id,
                object_projection_graph_identity_id=composite_opgi_id,
                observable_kind=None,
                observable_label="legacy composite observable",
            )
        ],
    )
    composite_view.object_projection_graphs.append(
        make_opg(object_config_graph_id=composite_view.id)
    )
    source.object_config_graph_identity = ObjectConfigGraphIdentity(
        id=source_ocgi_id,
        key="aware_environment_source",
        label="ocg:aware_environment_source",
        object_projection_graph_identities=[
            make_opgi(
                object_config_graph_identity_id=source_ocgi_id,
                object_projection_graph_identity_id=source_opgi_id,
                observable_kind="construct",
                observable_label="source observable",
            )
        ],
    )
    source.object_projection_graphs.append(make_opg(object_config_graph_id=source.id))

    out = compose_object_config_graphs(
        ocgs=[composite_view, source],
        composite_id=uuid4(),
        composite_name="Composed",
        composite_hash="sha256:composed",
        composite_fqn_prefix="aware_environment",
    )

    out_ocgi = out.object_config_graph_identity
    assert out_ocgi is not None
    identities = out_ocgi.object_projection_graph_identities
    assert len(identities) == 1
    assert identities[0].id == source_opgi_id
    assert identities[0].object_config_graph_identity_id == source_ocgi_id
    assert identities[0].object_projection_graph_observables[0].kind == "construct"
    assert (
        identities[0].object_projection_graph_observables[0].label
        == "source observable"
    )
