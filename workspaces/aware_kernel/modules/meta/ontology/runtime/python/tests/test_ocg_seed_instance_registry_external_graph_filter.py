from __future__ import annotations

from uuid import uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.lane import seed_commit as seed_commit_module
from aware_meta.graph.config.lane.projection import (
    compose_ocg_seed_schema_graph,
    resolve_ocg_seed_projection_context,
)
from aware_meta.graph.config.lane.registry import collect_lane_instance_models
from aware_meta.graph.instance.commit.fs_store import ObjectInstanceGraphCommitEnvelope
from aware_meta_ontology.class_.class_config import ClassConfig
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
