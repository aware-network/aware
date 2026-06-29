from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest
from _pytest.monkeypatch import MonkeyPatch

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_history_ontology.lane.lane import Lane
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphNodeSelection,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)

from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.builder import (
    build_object_instance_graph_from_class_instances,
)
from aware_meta.graph.instance.commit import committer as committer_module
from aware_meta.graph.instance.commit.builder import (
    extract_object_instance_graph_commit_root_metadata,
)
from aware_meta.graph.instance.commit.committer import (
    FSLaneCommitter,
    LaneStateIndexPreHashMismatchError,
)
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.state_index import (
    CommitStateIndex,
    build_commit_state_index,
)
from aware_meta.graph.instance.diff import diff_object_instance_graph_changes
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    make_rooted_object_instance_graph,
    test_class_fqn,
)


_USER_FQN = test_class_fqn("ShallowCommitUser")
_TEST_OIGI_ID = uuid4()


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])


def _make_ocg_and_opg(
    *,
    name_cfg: AttributeConfig,
) -> tuple[ObjectConfigGraph, ObjectProjectionGraph, ClassConfig]:
    user_cc = make_class_config(
        "ShallowCommitUser",
        class_fqn=_USER_FQN,
        class_config_attribute_configs=[],
    )
    user_cc.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=user_cc.id,
            attribute_config=name_cfg,
            name=name_cfg.name,
            position=0,
        )
    ]

    ocg = ObjectConfigGraph(
        name="test",
        description=None,
        hash="0",
        fqn_prefix="test",
        language=CodeLanguage.python,
        object_config_graph_nodes=[],
    )
    ocg.object_config_graph_nodes = [
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=user_cc.class_fqn,
            class_config=user_cc,
            object_config_graph_id=ocg.id,
        ),
    ]

    opg = ObjectProjectionGraph(
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="lane",
        supports_virtual_build=True,
        object_config_graph_id=ocg.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    opg.object_projection_graph_nodes = [
        ObjectProjectionGraphNode(
            class_config_id=user_cc.id,
            object_projection_graph_id=opg.id,
            is_root=True,
            selection=ObjectProjectionGraphNodeSelection.one,
        ),
    ]

    return ocg, opg, user_cc


@pytest.mark.asyncio
async def test_lane_shallow_append_uses_state_index_without_before_oig(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    name_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    ocg, opg, user_cc = _make_ocg_and_opg(name_cfg=name_cfg)

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str

    author_id = uuid4()
    branch_id = uuid4()
    graph_id: UUID = uuid4()
    user_id: UUID = uuid4()

    g0 = make_rooted_object_instance_graph(
        object_config_graph=ocg,
        object_projection_graph=opg,
        root_source_object_id=user_id,
        root_class_config_id=user_cc.id,
        oig_id=graph_id,
        key="g",
        name="g",
        description="d",
    )
    ci1 = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="a"),
    )
    g1 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci1,
        class_instances=[ci1],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    changes = diff_object_instance_graph_changes(
        old=g0,
        new=g1,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
    )
    pre_state_index = build_commit_state_index(g0)
    graph_hash_pre = pre_state_index.compute_hash()
    graph_hash_post = compute_hash(g1, index=build_index(g1))
    root_metadata = extract_object_instance_graph_commit_root_metadata(graph=g0)

    def _fail_full_oig_hash(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("shallow append must not hash a hydrated before_oig")

    monkeypatch.setattr(
        committer_module,
        "compute_oig_lane_hash_state",
        _fail_full_oig_hash,
    )

    store = FSCommitStore(root_dir=tmp_path)
    committer = FSLaneCommitter(store=store)
    commit_id = uuid4()
    commit = await committer.commit_to_lane_shallow(
        lane=Lane(branch_id=branch_id, lane_hash=opg.projection_hash),
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        object_instance_graph_id=graph_id,
        pre_state_index=pre_state_index,
        root_metadata=root_metadata,
        changes=changes,
        graph_hash_pre=graph_hash_pre,
        graph_hash_post=graph_hash_post,
        author_id=author_id,
        commit_id=commit_id,
        source_language=ocg.language,
    )

    assert commit is not None
    assert commit.commit.id == commit_id
    assert commit.commit.commit_parents == []
    assert commit.object_instance_graph_changes == changes
    assert commit.object_instance_graph_key == root_metadata.object_instance_graph_key
    assert commit.root_source_object_id == root_metadata.root_source_object_id
    assert commit.graph_hash_pre == graph_hash_pre
    assert commit.graph_hash_post == graph_hash_post
    perf = committer.last_commit_perf_profile_snapshot()
    assert perf.get("state_index_hash_ms", -1) >= 0
    assert perf.get("head_resolve_ms", -1) >= 0
    assert perf.get("build_commit_payload_ms", -1) >= 0
    assert perf.get("validate_commit_payload_ms", -1) >= 0
    assert perf.get("append_ms", -1) >= 0

    head = await store.head(branch_id=branch_id, projection_hash=opg.projection_hash)
    assert head is not None
    assert head["commit_id"] == str(commit_id)
    assert head["graph_hash_post"] == graph_hash_post
    assert head["object_instance_graph_id"] == str(graph_id)


@pytest.mark.asyncio
async def test_lane_shallow_append_rejects_state_index_prehash_mismatch(
    tmp_path: Path,
) -> None:
    name_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    ocg, opg, user_cc = _make_ocg_and_opg(name_cfg=name_cfg)

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str

    branch_id = uuid4()
    graph_id: UUID = uuid4()
    user_id: UUID = uuid4()
    g0 = make_rooted_object_instance_graph(
        object_config_graph=ocg,
        object_projection_graph=opg,
        root_source_object_id=user_id,
        root_class_config_id=user_cc.id,
        oig_id=graph_id,
        key="g",
        name="g",
        description="d",
    )
    ci1 = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="a"),
    )
    g1 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci1,
        class_instances=[ci1],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    with pytest.raises(LaneStateIndexPreHashMismatchError) as exc:
        _ = await FSLaneCommitter(
            store=FSCommitStore(root_dir=tmp_path)
        ).commit_shallow(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            object_instance_graph_identity_id=_TEST_OIGI_ID,
            object_instance_graph_id=graph_id,
            pre_state_index=CommitStateIndex(rows=()),
            root_metadata=extract_object_instance_graph_commit_root_metadata(graph=g0),
            changes=diff_object_instance_graph_changes(
                old=g0,
                new=g1,
                object_instance_graph_identity_id=_TEST_OIGI_ID,
            ),
            graph_hash_pre=build_commit_state_index(g0).compute_hash(),
            graph_hash_post=compute_hash(g1, index=build_index(g1)),
            author_id=uuid4(),
            source_language=ocg.language,
        )

    assert exc.value.details.branch_id == branch_id
    assert exc.value.details.projection_hash == opg.projection_hash
    assert exc.value.details.object_instance_graph_id == graph_id
