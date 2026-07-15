from __future__ import annotations

from uuid import UUID, uuid4

import pytest

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
from aware_meta.graph.instance.commit.committer import FSLaneCommitter, LaneCommitError
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


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])


def _make_ocg_and_opgs(
    *, name_cfg: AttributeConfig
) -> tuple[
    ObjectConfigGraph, ClassConfig, ObjectProjectionGraph, ObjectProjectionGraph
]:
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

    opg_a = ObjectProjectionGraph(
        name="lane-a",
        description=None,
        language=CodeLanguage.python,
        projection_hash="lane-a",
        supports_virtual_build=True,
        object_config_graph_id=ocg.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    opg_a.object_projection_graph_nodes = [
        ObjectProjectionGraphNode(
            class_config_id=user_cc.id,
            object_projection_graph_id=opg_a.id,
            is_root=True,
            selection=ObjectProjectionGraphNodeSelection.one,
        ),
    ]

    opg_b = ObjectProjectionGraph(
        name="lane-b",
        description=None,
        language=CodeLanguage.python,
        projection_hash="lane-b",
        supports_virtual_build=True,
        object_config_graph_id=ocg.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    opg_b.object_projection_graph_nodes = [
        ObjectProjectionGraphNode(
            class_config_id=user_cc.id,
            object_projection_graph_id=opg_b.id,
            is_root=True,
            selection=ObjectProjectionGraphNodeSelection.one,
        ),
    ]

    return ocg, user_cc, opg_a, opg_b


@pytest.mark.asyncio
async def test_lane_commits_are_isolated_by_projection_hash(
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
    ocg, user_cc, opg_a, opg_b = _make_ocg_and_opgs(name_cfg=name_cfg)

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str

    author_id = uuid4()
    branch_id = uuid4()
    oigi_id_a = uuid4()
    oigi_id_b = uuid4()

    graph_id_a: UUID = uuid4()
    graph_id_b: UUID = uuid4()
    user_id: UUID = uuid4()

    g0_a = make_rooted_object_instance_graph(
        object_config_graph=ocg,
        object_projection_graph=opg_a,
        root_source_object_id=user_id,
        root_class_config_id=user_cc.id,
        oig_id=graph_id_a,
        key="g",
        name="g",
        description="d",
    )
    g0_b = make_rooted_object_instance_graph(
        object_config_graph=ocg,
        object_projection_graph=opg_b,
        root_source_object_id=user_id,
        root_class_config_id=user_cc.id,
        oig_id=graph_id_b,
        key="g",
        name="g",
        description="d",
    )

    ci_a = build_class_instance(
        object_instance_graph_id=graph_id_a,
        class_config=user_cc,
        source=User(id=user_id, name="a"),
    )
    g1_a = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg_a.id,
        root_class_instance=ci_a,
        class_instances=[ci_a],
        class_instance_relationships=[],
        oig_id=graph_id_a,
    )

    ci_b = build_class_instance(
        object_instance_graph_id=graph_id_b,
        class_config=user_cc,
        source=User(id=user_id, name="b"),
    )
    g1_b = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg_b.id,
        root_class_instance=ci_b,
        class_instances=[ci_b],
        class_instance_relationships=[],
        oig_id=graph_id_b,
    )

    changes_a = diff_object_instance_graph_changes(
        old=g0_a,
        new=g1_a,
        object_instance_graph_identity_id=oigi_id_a,
    )
    changes_b = diff_object_instance_graph_changes(
        old=g0_b,
        new=g1_b,
        object_instance_graph_identity_id=oigi_id_b,
    )

    committer = FSLaneCommitter()
    c_a = await committer.commit(
        branch_id=branch_id,
        projection_hash=opg_a.projection_hash,
        object_instance_graph_identity_id=oigi_id_a,
        object_instance_graph_id=graph_id_a,
        before_oig=g0_a,
        changes=changes_a,
        graph_hash_pre=g0_a.hash,
        graph_hash_post=g1_a.hash,
        author_id=author_id,
        commit_id=uuid4(),
        source_language=ocg.language,
    )
    assert c_a is not None

    # Same branch, different projection_hash => different lane (must succeed).
    c_b = await committer.commit(
        branch_id=branch_id,
        projection_hash=opg_b.projection_hash,
        object_instance_graph_identity_id=oigi_id_b,
        object_instance_graph_id=graph_id_b,
        before_oig=g0_b,
        changes=changes_b,
        graph_hash_pre=g0_b.hash,
        graph_hash_post=g1_b.hash,
        author_id=author_id,
        commit_id=uuid4(),
        source_language=ocg.language,
    )
    assert c_b is not None

    mat = OIGMaterializer()
    out_a, _ = await mat.get(
        branch_id=branch_id,
        ocg=ocg,
        opg=opg_a,
        commit_id=c_a.commit.id,
        oig_id=graph_id_a,
    )
    out_b, _ = await mat.get(
        branch_id=branch_id,
        ocg=ocg,
        opg=opg_b,
        commit_id=c_b.commit.id,
        oig_id=graph_id_b,
    )
    assert out_a.hash == g1_a.hash
    assert out_b.hash == g1_b.hash

    # Guardrail: mixing a different OIG id into an existing lane is rejected.
    with pytest.raises(LaneCommitError):
        await committer.commit(
            branch_id=branch_id,
            projection_hash=opg_a.projection_hash,
            object_instance_graph_identity_id=oigi_id_b,
            object_instance_graph_id=graph_id_b,
            before_oig=g0_b,
            changes=changes_b,
            graph_hash_pre=g0_b.hash,
            graph_hash_post=g1_b.hash,
            author_id=author_id,
            commit_id=uuid4(),
            source_language=ocg.language,
        )
