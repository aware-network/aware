from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.builder import (
    build_object_instance_graph_from_class_instances,
)
from aware_meta.graph.instance.commit.builder import build_object_instance_graph_commit
from aware_meta.graph.instance.commit.fs_store import FSCommitStore, FSSnapshotStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    make_rooted_object_instance_graph,
    test_class_fqn,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
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
from aware_orm.models.base_model import BaseORMModel


_USER_FQN = test_class_fqn("ProfileUser")
_TEST_OIGI_ID = uuid4()


class RecordingTimings:
    def __init__(self) -> None:
        self.metrics: dict[str, object] = {}

    def metric(self, key: str, value: object) -> None:
        self.metrics[key] = value


class User(BaseORMModel):
    name: str


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])


def _make_ocg_and_opg(
    *,
    name_cfg: AttributeConfig,
) -> tuple[ObjectConfigGraph, ObjectProjectionGraph]:
    user_cc = make_class_config(
        "ProfileUser",
        class_fqn=_USER_FQN,
        class_config_attribute_configs=[],
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
        name="profile-test",
        description=None,
        hash="0",
        fqn_prefix="profile_test",
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
        name="profile-test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="profile-lane",
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

    return ocg, opg


@pytest.mark.asyncio
async def test_oig_materializer_profiles_no_snapshot_lineage_reuse(
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
    ocg, opg = _make_ocg_and_opg(name_cfg=name_cfg)
    user_cc = ocg.object_config_graph_nodes[0].class_config
    assert user_cc is not None

    branch_id = uuid4()
    graph_id: UUID = uuid4()
    user_id = uuid4()

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

    c1 = build_object_instance_graph_commit(
        old=g0,
        new=g1,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        branch_id=branch_id,
        author_id=uuid4(),
    )
    assert c1 is not None
    c2 = build_object_instance_graph_commit(
        old=g1,
        new=g2,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        branch_id=branch_id,
        author_id=uuid4(),
        parent_commit_id=c1.commit.id,
    )
    assert c2 is not None

    store = FSCommitStore()
    snapshots = FSSnapshotStore()
    materializer = OIGMaterializer(commits=store, snaps=snapshots)
    await store.append(
        branch_id=branch_id, projection_hash=opg.projection_hash, commit=c1
    )
    await store.append(
        branch_id=branch_id, projection_hash=opg.projection_hash, commit=c2
    )

    timings = RecordingTimings()
    out, _indexes = await materializer.get(
        branch_id=branch_id,
        ocg=ocg,
        opg=opg,
        commit_id=c2.commit.id,
        oig_id=graph_id,
        timings=timings,
    )

    assert out.hash == g2.hash
    assert timings.metrics["oig_materializer_base_snapshot_hit"] is False
    assert (
        timings.metrics["oig_materializer_bootstrap_lineage_loaded_commit_count"] == 2
    )
    assert timings.metrics["oig_materializer_replay_reused_bootstrap_lineage"] is True
    assert timings.metrics["oig_materializer_replay_loaded_commit_count"] == 2
    assert timings.metrics["oig_materializer_applied_commit_count"] == 2
    assert timings.metrics["oig_materializer_snapshot_written"] is True

    for key in (
        "oig_materializer_total_ms",
        "oig_materializer_index_build_ms",
        "oig_materializer_head_read_ms",
        "oig_materializer_snapshot_lookup_ms",
        "oig_materializer_bootstrap_lineage_load_ms",
        "oig_materializer_replay_validation_ms",
        "oig_materializer_replay_pre_hash_ms",
        "oig_materializer_replay_apply_ms",
        "oig_materializer_replay_post_hash_ms",
        "oig_materializer_snapshot_index_build_ms",
        "oig_materializer_snapshot_write_ms",
    ):
        value = timings.metrics[key]
        assert isinstance(value, int)
        assert value >= 0
