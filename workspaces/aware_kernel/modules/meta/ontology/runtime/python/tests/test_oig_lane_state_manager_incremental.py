from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from aware_history_ontology.branch.branch import Branch
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.instance.object_instance_graph_branch import (
    ObjectInstanceGraphBranch,
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
from aware_code_ontology.code.code_enums import CodeLanguage

from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.builder import (
    build_object_instance_graph_from_class_instances,
)
from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.fs_store import FSCommitStore, FSSnapshotStore
from aware_meta.graph.instance.commit.lane_state_manager import OIGLaneStateManager
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.instance.diff import diff_object_instance_graph_changes
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    make_rooted_object_instance_graph,
    test_class_fqn,
)


_USER_FQN = test_class_fqn("User")
_TEST_OIGI_ID = uuid4()


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])


def _make_ocg_and_opg(
    *, name_cfg: AttributeConfig
) -> tuple[ObjectConfigGraph, ObjectProjectionGraph, ClassConfig]:
    user_cc = make_class_config(
        "User", class_fqn=_USER_FQN, class_config_attribute_configs=[]
    )
    user_cc.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=user_cc.id,
            attribute_config=name_cfg,
            name=name_cfg.name,
            position=0,
        ),
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
            class_config_id=user_cc.id,
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
async def test_lane_state_manager_applies_appended_commit_incrementally(
    tmp_path, monkeypatch
) -> None:
    (tmp_path / ".aware").mkdir()
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path))

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
    graph_id: UUID = uuid4()
    user_id = uuid4()

    branch = Branch(id=uuid4(), name="b", is_main=False)
    oig_branch = ObjectInstanceGraphBranch(
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        branch=branch,
        branch_id=branch.id,
    )

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

    ci2 = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="b"),
    )
    g2 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci2,
        class_instances=[ci2],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    changes1 = diff_object_instance_graph_changes(
        old=g0,
        new=g1,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
    )
    changes2 = diff_object_instance_graph_changes(
        old=g1,
        new=g2,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
    )

    store = FSCommitStore()
    snaps = FSSnapshotStore()
    mat = OIGMaterializer(commits=store, snaps=snaps)
    lane_mgr = OIGLaneStateManager(commits=store, snaps=snaps, materializer=mat)
    committer = FSLaneCommitter(store)

    c1 = await committer.commit(
        branch_id=branch.id,
        projection_hash=opg.projection_hash,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        object_instance_graph_id=graph_id,
        before_oig=g0,
        changes=changes1,
        graph_hash_pre=g0.hash,
        graph_hash_post=g1.hash,
        author_id=author_id,
        commit_id=uuid4(),
        source_language=ocg.language,
    )
    assert c1 is not None

    st1 = await lane_mgr.ensure_loaded(
        branch=oig_branch, ocg=ocg, opg=opg, commit_id=c1.commit.id
    )
    assert st1.oig.hash == g1.hash
    assert len(oig_branch.object_instance_graph_lanes) == 1
    assert st1.lane is oig_branch.object_instance_graph_lanes[0]
    assert st1.lane.lane.lane_hash == opg.projection_hash
    assert st1.lane.lane.head_commit_id == c1.commit.id

    # Ensure on_commit_appended uses the fast-path (no full re-materialization).
    async def _should_not_be_called(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(
            "OIGMaterializer.get should not be called in incremental fast-path"
        )

    lane_mgr._mat.get = _should_not_be_called  # type: ignore[method-assign]

    c2 = await committer.commit(
        branch_id=branch.id,
        projection_hash=opg.projection_hash,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        object_instance_graph_id=graph_id,
        before_oig=g1,
        changes=changes2,
        graph_hash_pre=g1.hash,
        graph_hash_post=g2.hash,
        author_id=author_id,
        commit_id=uuid4(),
        source_language=ocg.language,
    )
    assert c2 is not None

    st2 = await lane_mgr.on_commit_appended(
        branch=oig_branch, ocg=ocg, opg=opg, commit=c2
    )
    assert st2.head_commit_id == c2.commit.id
    assert st2.oig.hash == g2.hash
    assert st2.lane is st1.lane
    assert st2.lane.lane.head_commit_id == c2.commit.id

    cached = lane_mgr.get_oig(branch_id=branch.id, projection_hash=opg.projection_hash)
    assert cached.hash == g2.hash
