from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.builder import (
    build_object_instance_graph_from_class_instances,
)
from aware_meta.graph.instance.commit.builder import build_object_instance_graph_commit
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.graph.instance.commit.snapshot_state_rows import (
    _trusted_attribute_type_descriptor_from_snapshot_state_payload,
)
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.instance.commit.perf_trace import (
    CommitPerfTraceRecorder,
    active_commit_perf_trace,
)
from aware_meta.primitive.config.builder import build_primitive_config
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


def test_trusted_state_row_descriptor_hydration_preserves_decode_relations() -> None:
    primitive_type_id = uuid4()
    primitive_config_id = uuid4()
    primitive_desc = _trusted_attribute_type_descriptor_from_snapshot_state_payload(
        {
            "id": str(uuid4()),
            "kind": "primitive",
            "collection_kind": "single",
            "primitive_config_id": str(primitive_config_id),
            "primitive_config": {
                "id": str(primitive_config_id),
                "primitive_type_id": str(primitive_type_id),
                "primitive_type": {
                    "id": str(primitive_type_id),
                    "signature": "string",
                    "base_type": "string",
                    "constraints": None,
                    "item_type_id": None,
                    "key_type_id": None,
                    "value_type_id": None,
                },
            },
        }
    )

    assert primitive_desc.kind == Kind.primitive
    assert primitive_desc.primitive_config is not None
    assert primitive_desc.primitive_config.primitive_type_id == primitive_type_id
    assert (
        primitive_desc.primitive_config.primitive_type.base_type
        == CodePrimitiveBaseType.string
    )

    enum_config_id = uuid4()
    enum_option_id = uuid4()
    enum_desc = _trusted_attribute_type_descriptor_from_snapshot_state_payload(
        {
            "id": str(uuid4()),
            "kind": "enum",
            "collection_kind": "single",
            "enum_config_id": str(enum_config_id),
            "enum_config": {
                "id": str(enum_config_id),
                "enum_fqn": "aware_test.SampleEnum",
                "name": "SampleEnum",
                "enum_options": [
                    {
                        "id": str(enum_option_id),
                        "enum_config_id": str(enum_config_id),
                        "value": "enabled",
                        "label": "enabled",
                        "description": None,
                        "position": 0,
                    }
                ],
            },
        }
    )

    assert enum_desc.kind == Kind.enum
    assert enum_desc.enum_config is not None
    assert enum_desc.enum_config.enum_options[0].id == enum_option_id
    assert enum_desc.enum_config.enum_options[0].value == "enabled"


def _primitive_desc() -> AttributeTypeDescriptor:
    primitive_config = build_primitive_config(
        build_code_primitive_type(base_type=CodePrimitiveBaseType.string)
    )
    return AttributeTypeDescriptor(
        kind=Kind.primitive,
        child_links=[],
        primitive_config=primitive_config,
        primitive_config_id=primitive_config.id,
    )


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
    recorder = CommitPerfTraceRecorder(default_category="meta.oig_materializer")
    with active_commit_perf_trace(recorder):
        out, _indexes = await materializer.get(
            branch_id=branch_id,
            ocg=ocg,
            opg=opg,
            commit_id=c2.commit.id,
            oig_id=graph_id,
            timings=timings,
        )

    assert out.hash == g2.hash
    phases = {event.phase for event in recorder.snapshot()}
    assert {
        "oig_materializer.get.index_build",
        "oig_materializer.get.head_read",
        "oig_materializer.get.resolve_target_commit",
        "oig_materializer.get.snapshot_lookup",
        "oig_materializer.get.bootstrap_lineage_load",
        "oig_materializer.get.bootstrap_hash",
        "oig_materializer.get.replay_validate_body",
        "oig_materializer.get.replay_pre_hash",
        "oig_materializer.get.replay_apply_changes",
        "oig_materializer.get.replay_post_hash",
        "oig_materializer.get.snapshot_index_build",
        "oig_materializer.get.snapshot_write",
    }.issubset(phases)
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

    exact_timings = RecordingTimings()
    exact_recorder = CommitPerfTraceRecorder(default_category="meta.oig_materializer")
    with active_commit_perf_trace(exact_recorder):
        exact_out, _exact_indexes = await materializer.get(
            branch_id=branch_id,
            ocg=ocg,
            opg=opg,
            commit_id=c2.commit.id,
            oig_id=graph_id,
            timings=exact_timings,
        )

    assert exact_out.hash == g2.hash
    exact_phases = {event.phase for event in exact_recorder.snapshot()}
    assert {
        "oig_materializer.get.snapshot_lookup",
        "oig_snapshot_store.nearest.try_state_graph",
        "oig_snapshot_store.state_graph.read_rows",
        "oig_snapshot_store.state_rows.read_payload",
        "oig_snapshot_store.state_rows.validate_payload",
        "oig_snapshot_store.state_graph.hydrate_graph",
        "oig_snapshot_store.state_graph.graph_metadata",
        "oig_snapshot_store.state_graph.payload_shape",
        "oig_snapshot_store.state_graph.hydrate_class_instances",
        "oig_snapshot_store.state_graph.hydrate_relationships",
        "oig_snapshot_store.state_graph.resolve_root",
        "oig_snapshot_store.state_graph.construct_graph",
        "oig_snapshot_store.state_graph.read_snapshot_index",
        "oig_materializer.get.snapshot_descriptor_hydration",
        "oig_materializer.get.exact_snapshot_return",
    }.issubset(exact_phases)
    assert "oig_snapshot_store.get.validate_snapshot_model" not in exact_phases
    assert "oig_snapshot_store.state_graph.validate_class_instances" not in exact_phases
    assert "oig_snapshot_store.state_graph.validate_relationships" not in exact_phases
    assert exact_timings.metrics["oig_materializer_base_snapshot_hit"] is True
    assert exact_timings.metrics["oig_materializer_applied_commit_count"] == 0
    assert isinstance(
        exact_timings.metrics["oig_materializer_snapshot_descriptor_hydration_ms"],
        int,
    )

    exact_attribute = exact_out.class_instances[0].attributes[0]
    exact_descriptor = exact_attribute.value_root.type_descriptor
    assert exact_descriptor.primitive_config is not None
    assert (
        exact_descriptor.primitive_config.primitive_type.base_type
        == CodePrimitiveBaseType.string
    )
