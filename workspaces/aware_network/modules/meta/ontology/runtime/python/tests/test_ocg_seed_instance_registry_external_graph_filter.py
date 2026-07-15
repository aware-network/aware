from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.lane.common import (
    clone_object_instance_graph_for_validation,
    count_object_instance_graph_change_operations,
)
from aware_meta.graph.config.lane import common as lane_common
from aware_meta.graph.config.lane import seed_commit as seed_commit_module
from aware_meta.graph.config.lane.projection import (
    _seed_schema_view_graph_without_seen_entries,
    compose_ocg_seed_schema_graph,
    resolve_ocg_seed_projection_context,
)
from aware_meta.graph.config.lane.registry import collect_lane_instance_models
from aware_meta.graph.instance.commit.contract import ObjectInstanceGraphCommitEnvelope
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.attribute.attribute_value_link import AttributeValueLink
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorRole,
)
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_instance_attribute import ClassInstanceAttribute
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.config.object_config_graph_relationship import (
    ObjectConfigGraphRelationship,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphNodeSelection,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)


def _new_graph(*, name: str) -> ObjectConfigGraph:
    # Minimal graph; OIG seed materialization doesn't run here.
    return ObjectConfigGraph(
        name=name,
        description=None,
        hash="0",
        fqn_prefix="test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )


def _graph_with_seed_projection(
    *,
    name: str,
    projection_hash: str,
) -> ObjectConfigGraph:
    graph = _new_graph(name=name)
    class_config = ClassConfig(
        class_fqn=f"test.{name}.ObjectConfigGraph",
        name="ObjectConfigGraph",
    )
    graph.object_config_graph_nodes = [
        ObjectConfigGraphNode(
            object_config_graph_id=graph.id,
            type=ObjectConfigGraphNodeType.class_,
            node_key=class_config.class_fqn,
            class_config=class_config,
        )
    ]
    opg_id = uuid4()
    graph.object_projection_graphs = [
        ObjectProjectionGraph(
            id=opg_id,
            object_config_graph_id=graph.id,
            language=CodeLanguage.aware,
            name="ObjectConfigGraph",
            projection_hash=projection_hash,
            object_projection_graph_nodes=[
                ObjectProjectionGraphNode(
                    object_projection_graph_id=opg_id,
                    class_config_id=class_config.id,
                    is_root=True,
                    selection=ObjectProjectionGraphNodeSelection.one,
                )
            ],
            object_projection_graph_edges=[],
            object_projection_graph_relationships=[],
        )
    ]
    return graph


def test_seed_validation_size_gate_counts_nested_change_operations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    value_change = SimpleNamespace(
        attribute_value_link_changes=[
            SimpleNamespace(
                child_attribute_value_change=SimpleNamespace(
                    attribute_value_link_changes=[]
                )
            )
        ]
    )
    root_changes = [
        SimpleNamespace(
            class_instance_changes=[
                SimpleNamespace(
                    attribute_changes=[
                        SimpleNamespace(value_root_change=value_change),
                    ]
                )
            ],
            class_instance_relationship_changes=[],
        ),
        SimpleNamespace(
            class_instance_changes=[],
            class_instance_relationship_changes=[
                SimpleNamespace(),
                SimpleNamespace(),
            ],
        ),
    ]

    nested_change_count = count_object_instance_graph_change_operations(root_changes)

    monkeypatch.setenv("AWARE_OCG_SEED_APPLY_HASH_VALIDATE_MAX_CHANGES", "6")
    skip_validation, max_changes = (
        seed_commit_module._seed_apply_hash_validation_size_gate(  # noqa: SLF001
            change_count=nested_change_count,
        )
    )

    assert len(root_changes) == 2
    assert nested_change_count == 9
    assert max_changes == 6
    assert skip_validation is True


def test_collect_lane_instances_ignores_unrelated_external_graphs() -> None:
    ocg = _new_graph(name="a")
    ext = _new_graph(name="b")

    result = collect_lane_instance_models(ocg=ocg, external_graphs=[ext])
    assert ocg.id in result
    assert ext.id not in result


def test_collect_lane_instances_ignores_unreferenced_kernel_code_graph() -> None:
    ocg = _new_graph(name="service")
    code_graph = _new_graph(name="aware_code")

    result = collect_lane_instance_models(ocg=ocg, external_graphs=[code_graph])
    assert ocg.id in result
    assert code_graph.id not in result


def test_collect_lane_instances_includes_referenced_external_graphs() -> None:
    ocg = _new_graph(name="a")
    ext = _new_graph(name="b")

    ocg.object_config_graph_relationships = [
        ObjectConfigGraphRelationship(
            object_config_graph_id=ocg.id,
            target_object_config_graph_id=ext.id,
        )
    ]

    result = collect_lane_instance_models(ocg=ocg, external_graphs=[ext])
    assert ocg.id in result
    assert ext.id in result


def test_collect_lane_instances_keeps_referenced_external_graph_shallow() -> None:
    ocg = _new_graph(name="a")
    ext = _new_graph(name="b")
    ext_node = ObjectConfigGraphNode(
        object_config_graph_id=ext.id,
        type=ObjectConfigGraphNodeType.class_,
        node_key="b.External",
    )
    ext.object_config_graph_nodes = [ext_node]

    ocg.object_config_graph_relationships = [
        ObjectConfigGraphRelationship(
            object_config_graph_id=ocg.id,
            target_object_config_graph_id=ext.id,
        )
    ]

    result = collect_lane_instance_models(ocg=ocg, external_graphs=[ext])

    assert ext.id in result
    assert ext_node.id not in result
    assert isinstance(result[ext.id], ObjectConfigGraph)
    assert result[ext.id].object_config_graph_nodes == []


def test_collect_lane_instances_does_not_walk_hydrated_target_graph_ref() -> None:
    ocg = _new_graph(name="a")
    ext = _new_graph(name="b")
    ext_node = ObjectConfigGraphNode(
        object_config_graph_id=ext.id,
        type=ObjectConfigGraphNodeType.class_,
        node_key="b.External",
    )
    ext.object_config_graph_nodes = [ext_node]

    ocg.object_config_graph_relationships = [
        ObjectConfigGraphRelationship(
            object_config_graph_id=ocg.id,
            target_object_config_graph_id=ext.id,
            target_object_config_graph=ext,
        )
    ]

    result = collect_lane_instance_models(ocg=ocg, external_graphs=[])

    assert ocg.id in result
    assert ext.id not in result
    assert ext_node.id not in result


def test_seed_projection_prefers_owner_graph_over_copied_projection_identity() -> None:
    ocg = _new_graph(name="dto")
    copied_graph = _graph_with_seed_projection(
        name="copied",
        projection_hash="sha256:test:copied",
    )
    owner_graph = _graph_with_seed_projection(
        name="owner",
        projection_hash="sha256:test:owner",
    )
    copied_graph.object_projection_graphs[0].id = owner_graph.object_projection_graphs[
        0
    ].id
    copied_graph.object_projection_graphs[0].object_config_graph_id = owner_graph.id

    schema_graph, opg = resolve_ocg_seed_projection_context(
        ocg=ocg,
        external_graphs=(copied_graph, owner_graph),
        opg_name="ObjectConfigGraph",
    )

    assert schema_graph.id == owner_graph.id
    assert opg.projection_hash == "sha256:test:owner"


def test_seed_schema_view_filters_copied_external_entries_before_compose() -> None:
    owner_graph = _graph_with_seed_projection(
        name="owner",
        projection_hash="sha256:test:owner",
    )
    external_graph = _graph_with_seed_projection(
        name="external",
        projection_hash="sha256:test:external",
    )
    owner_node = owner_graph.object_config_graph_nodes[0]
    unique_external_class = ClassConfig(
        class_fqn="test.external.UniqueExternal",
        name="UniqueExternal",
    )
    unique_external_node = ObjectConfigGraphNode(
        object_config_graph_id=external_graph.id,
        type=ObjectConfigGraphNodeType.class_,
        node_key=unique_external_class.class_fqn,
        class_config=unique_external_class,
    )
    conflicting_copied_owner_node = ObjectConfigGraphNode(
        id=owner_node.id,
        object_config_graph_id=external_graph.id,
        type=ObjectConfigGraphNodeType.class_,
        node_key="test.external.ConflictingOwnerCopy",
        class_config=ClassConfig(
            class_fqn="test.external.ConflictingOwnerCopy",
            name="ConflictingOwnerCopy",
        ),
    )
    external_graph.object_config_graph_nodes = [
        conflicting_copied_owner_node,
        unique_external_node,
    ]
    owner_opg = owner_graph.object_projection_graphs[0]
    owner_opg.object_projection_graph_nodes.append(
        ObjectProjectionGraphNode(
            object_projection_graph_id=owner_opg.id,
            class_config_id=unique_external_class.id,
            is_root=False,
            selection=ObjectProjectionGraphNodeSelection.all,
        )
    )

    schema_view = compose_ocg_seed_schema_graph(
        schema_graph=owner_graph,
        external_graphs=(external_graph,),
        object_projection_graph=owner_opg,
    )

    node_ids = [node.id for node in schema_view.object_config_graph_nodes]
    assert node_ids.count(owner_node.id) == 1
    assert unique_external_node.id in node_ids


def test_seed_schema_view_entry_filter_uses_shallow_graph_copy(
    monkeypatch,
) -> None:
    owner_graph = _graph_with_seed_projection(
        name="owner",
        projection_hash="sha256:test:owner",
    )
    external_graph = _graph_with_seed_projection(
        name="external",
        projection_hash="sha256:test:external",
    )
    owner_node = owner_graph.object_config_graph_nodes[0]
    copied_owner_node = ObjectConfigGraphNode(
        id=owner_node.id,
        object_config_graph_id=external_graph.id,
        type=ObjectConfigGraphNodeType.class_,
        node_key="test.external.OwnerCopy",
        class_config=ClassConfig(
            class_fqn="test.external.OwnerCopy",
            name="OwnerCopy",
        ),
    )
    unique_external_node = external_graph.object_config_graph_nodes[0]
    external_graph.object_config_graph_nodes = [
        copied_owner_node,
        unique_external_node,
    ]
    original_model_copy = ObjectConfigGraph.model_copy

    def fail_deep_model_copy(self, *, update=None, deep: bool = False):
        if deep:
            raise AssertionError("seed schema filtering must not deep-copy OCGs")
        return original_model_copy(self, update=update, deep=deep)

    monkeypatch.setattr(ObjectConfigGraph, "model_copy", fail_deep_model_copy)

    filtered = _seed_schema_view_graph_without_seen_entries(
        graph=external_graph,
        seen_entry_ids_by_collection={
            "object_config_graph_nodes": {owner_node.id},
        },
    )

    assert filtered is not None
    assert filtered is not external_graph
    assert filtered.hash == ""
    assert filtered.object_config_graph_nodes == [unique_external_node]
    assert external_graph.object_config_graph_nodes == [
        copied_owner_node,
        unique_external_node,
    ]


def test_collect_lane_instances_filters_to_declared_relationship_graph_ids() -> None:
    ocg = _new_graph(name="a")
    ext_included = _new_graph(name="b")
    ext_excluded = _new_graph(name="c")

    ocg.object_config_graph_relationships = [
        ObjectConfigGraphRelationship(
            object_config_graph_id=ocg.id,
            target_object_config_graph_id=ext_included.id,
        )
    ]

    result = collect_lane_instance_models(
        ocg=ocg,
        external_graphs=[ext_included, ext_excluded],
    )
    assert ocg.id in result
    assert ext_included.id in result
    assert ext_excluded.id not in result


def test_seed_apply_hash_validation_size_gate_respects_threshold(
    monkeypatch,
) -> None:
    monkeypatch.setenv("AWARE_OCG_SEED_APPLY_HASH_VALIDATE_MAX_CHANGES", "2")

    skipped, max_changes = (
        seed_commit_module._seed_apply_hash_validation_size_gate(  # noqa: SLF001
            change_count=3,
        )
    )

    assert skipped is True
    assert max_changes == 2


def test_validation_clone_uses_public_copy_for_attribute_free_class_instances(
    monkeypatch,
) -> None:
    graph_id = uuid4()
    class_instance = ClassInstance.model_construct(
        id=uuid4(),
        object_instance_graph_id=graph_id,
        class_config_id=uuid4(),
        source_object_id=uuid4(),
        class_instance_attributes=[],
    )
    graph = ObjectInstanceGraph.model_construct(
        id=graph_id,
        root_class_instance_id=class_instance.id,
        root_class_instance=class_instance,
        class_instances=[class_instance],
        class_instance_relationships=[],
    )
    changes = [
        SimpleNamespace(
            class_instance_changes=[
                SimpleNamespace(class_instance_id=class_instance.id)
            ],
            class_instance_relationship_changes=[],
        )
    ]

    def fail_deepcopy(_: object) -> object:
        raise AssertionError("attribute-free validation clone must not deepcopy")

    monkeypatch.setattr(lane_common.copy, "deepcopy", fail_deepcopy)

    clone = clone_object_instance_graph_for_validation(graph, changes=changes)

    assert clone is not graph
    assert clone.class_instances[0] is not class_instance
    assert clone.class_instances[0].id == class_instance.id
    assert clone.root_class_instance is clone.class_instances[0]


def test_validation_clone_uses_model_construction_for_attributed_class_instances(
    monkeypatch,
) -> None:
    graph_id = uuid4()
    root_value = AttributeValue.model_construct(
        id=uuid4(),
        type_descriptor_id=uuid4(),
        primitive_value={"value": "before"},
        child_links=[
            AttributeValueLink.model_construct(
                id=uuid4(),
                attribute_value_id=uuid4(),
                child_id=uuid4(),
                role=AttributeTypeDescriptorRole.value_,
                position=0,
                identity_key=None,
                child=AttributeValue.model_construct(
                    id=uuid4(),
                    type_descriptor_id=uuid4(),
                    primitive_value={"child": "before"},
                    child_links=[],
                    enum_option_id=None,
                    class_instance_id=None,
                    inline_value_instance_id=None,
                ),
            )
        ],
        enum_option_id=None,
        class_instance_id=None,
        inline_value_instance_id=None,
    )
    attribute = Attribute.model_construct(
        id=uuid4(),
        owner_key=uuid4(),
        attribute_config_id=uuid4(),
        value_root_id=root_value.id,
        value_root=root_value,
    )
    edge = ClassInstanceAttribute.model_construct(
        id=uuid4(),
        class_instance_id=uuid4(),
        attribute_id=attribute.id,
        attribute=attribute,
    )
    class_instance = ClassInstance.model_construct(
        id=edge.class_instance_id,
        object_instance_graph_id=graph_id,
        class_config_id=uuid4(),
        source_object_id=uuid4(),
        class_instance_attributes=[edge],
    )
    graph = ObjectInstanceGraph.model_construct(
        id=graph_id,
        root_class_instance_id=class_instance.id,
        root_class_instance=class_instance,
        class_instances=[class_instance],
        class_instance_relationships=[],
    )
    changes = [
        SimpleNamespace(
            class_instance_changes=[
                SimpleNamespace(class_instance_id=class_instance.id)
            ],
            class_instance_relationship_changes=[],
        )
    ]

    def fail_deepcopy(_: object) -> object:
        raise AssertionError("attributed validation clone must not deepcopy")

    monkeypatch.setattr(lane_common.copy, "deepcopy", fail_deepcopy)

    clone = clone_object_instance_graph_for_validation(graph, changes=changes)
    cloned_instance = clone.class_instances[0]
    cloned_edge = cloned_instance.class_instance_attributes[0]
    cloned_attribute = cloned_edge.attribute
    cloned_value = cloned_attribute.value_root

    assert clone is not graph
    assert cloned_instance is not class_instance
    assert cloned_edge is not edge
    assert cloned_attribute is not attribute
    assert cloned_value is not root_value
    assert cloned_value.child_links[0] is not root_value.child_links[0]
    assert cloned_value.child_links[0].child is not root_value.child_links[0].child
    assert cloned_value.primitive_value == {"value": "before"}
    assert clone.root_class_instance is cloned_instance


def test_validation_clone_avoids_deepcopy_for_unclassified_change_payload(
    monkeypatch,
) -> None:
    graph_id = uuid4()
    class_instance = ClassInstance.model_construct(
        id=uuid4(),
        object_instance_graph_id=graph_id,
        class_config_id=uuid4(),
        source_object_id=uuid4(),
        class_instance_attributes=[],
    )
    graph = ObjectInstanceGraph.model_construct(
        id=graph_id,
        root_class_instance_id=class_instance.id,
        root_class_instance=class_instance,
        class_instances=[class_instance],
        class_instance_relationships=[],
    )
    changes = [
        SimpleNamespace(
            class_instance_changes=[],
            class_instance_relationship_changes=[],
        )
    ]

    def fail_deepcopy(_: object) -> object:
        raise AssertionError("non-empty validation changes must not deepcopy")

    monkeypatch.setattr(lane_common.copy, "deepcopy", fail_deepcopy)

    clone = clone_object_instance_graph_for_validation(graph, changes=changes)

    assert clone is not graph
    assert clone.class_instances[0] is not class_instance
    assert clone.class_instances[0].id == class_instance.id
    assert clone.root_class_instance is clone.class_instances[0]


@pytest.mark.asyncio
async def test_ensure_ocg_seeded_lane_reuses_nonempty_projection_head(
    monkeypatch,
) -> None:
    ocg = _new_graph(name="service")
    branch_id = uuid4()
    commit_id = uuid4()
    projection_hash = "sha256:test:projection"

    def fail_build_seed_plan(**_: object) -> object:
        raise AssertionError("non-empty lane should not rebuild the seed OIG plan")

    class FakeStore:
        async def head(self, **_: object) -> dict[str, str]:
            return {
                "commit_id": str(commit_id),
                "graph_hash_post": "sha256:test:post",
                "object_instance_graph_id": str(ocg.id),
            }

    monkeypatch.setattr(
        seed_commit_module,
        "_build_ocg_seed_plan_and_commit",
        fail_build_seed_plan,
    )

    plan = await seed_commit_module.ensure_ocg_seeded_lane(
        ocg=ocg,
        branch_id=branch_id,
        ocg_hash=str(ocg.hash),
        projection_hash_override=projection_hash,
        store=FakeStore(),
    )

    assert plan.seeded is False
    assert plan.branch_id == branch_id
    assert plan.projection_hash == projection_hash
    assert plan.commit_id == commit_id
    assert plan.object_instance_graph_id == ocg.id
    assert plan.changes == []


@pytest.mark.asyncio
async def test_ensure_ocg_seeded_lane_validates_existing_seed_from_envelope(
    tmp_path,
    monkeypatch,
) -> None:
    ocg = _new_graph(name="service")
    branch_id = uuid4()
    commit_id = uuid4()
    projection_hash = "sha256:test:projection"
    placeholder_oig = ObjectInstanceGraph.model_construct(
        id=ocg.id,
        class_instances=[],
        class_instance_relationships=[],
    )
    plan = seed_commit_module.OCGSeedPlan(
        seeded=False,
        branch_id=branch_id,
        projection_hash=projection_hash,
        object_instance_graph_id=ocg.id,
        root_object_id=ocg.id,
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
        commit_id=commit_id,
        changes=[],
        before_oig=placeholder_oig,
        after_oig=placeholder_oig,
        objects_by_id={ocg.id: ocg},
    )
    envelope = ObjectInstanceGraphCommitEnvelope(
        commit_id=commit_id,
        lane_id=uuid4(),
        key=str(commit_id),
        author_id=uuid4(),
        created_at=seed_commit_module.SEED_CREATED_AT,
        status=seed_commit_module.DEFAULT_OCG_COMMIT_STATUS.value,
        parent_commit_ids=(),
        object_instance_graph_commit_id=uuid4(),
        object_instance_graph_identity_id=uuid4(),
        object_instance_graph_id=ocg.id,
        object_instance_graph_key="seed",
        object_instance_graph_name="Seed",
        object_instance_graph_description=None,
        root_class_config_id=uuid4(),
        root_source_object_id=ocg.id,
        graph_hash_pre=plan.graph_hash_pre,
        graph_hash_post=plan.graph_hash_post,
        projection_hash=projection_hash,
        source_language=CodeLanguage.aware.value,
    )

    def fake_build_seed_plan(**_: object) -> tuple[object, object]:
        return plan, object()

    class FakeStore:
        aware_root = tmp_path

        async def head(self, **_: object) -> dict[str, str]:
            return {}

        async def get_commit_envelope(self, **_: object) -> object:
            return envelope

        async def get_commit(self, **_: object) -> object:
            raise AssertionError("existing seed validation must not read full body")

    monkeypatch.setattr(
        seed_commit_module,
        "_build_ocg_seed_plan_and_commit",
        fake_build_seed_plan,
    )

    actual = await seed_commit_module.ensure_ocg_seeded_lane(
        ocg=ocg,
        branch_id=branch_id,
        ocg_hash=str(ocg.hash),
        store=FakeStore(),
    )

    assert actual is plan
