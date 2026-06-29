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
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id
from aware_code_ontology.code.code_enums import CodeLanguage

from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.builder import (
    build_object_instance_graph_from_class_instances,
)
from aware_meta.graph.instance.commit.builder import build_object_instance_graph_commit
from aware_meta.graph.instance.commit.fs_store import (
    FSCommitStore,
    FSSnapshotStore,
    _clear_fs_store_session_read_cache_for_tests,
    _snapshot_fs_store_session_read_cache_metrics,
)
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
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
    *,
    name_cfg: AttributeConfig,
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
async def test_materializer_and_snapshot_store_do_not_load_full_commit_map(
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
    snaps = FSSnapshotStore()
    mat = OIGMaterializer(commits=store, snaps=snaps)

    await store.append(
        branch_id=branch_id, projection_hash=opg.projection_hash, commit=c1
    )
    await store.append(
        branch_id=branch_id, projection_hash=opg.projection_hash, commit=c2
    )

    # Ensure snapshot dir exists so `nearest_at_or_before` walks ancestry (streaming).
    (
        tmp_path / ".aware" / "oig" / str(branch_id) / opg.projection_hash / "snapshots"
    ).mkdir(parents=True)

    async def _boom(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(
            "FSCommitStore._load_commit_map must not be used for streaming materialization"
        )

    monkeypatch.setattr(FSCommitStore, "_load_commit_map", _boom, raising=True)

    out, _ = await mat.get(
        branch_id=branch_id,
        ocg=ocg,
        opg=opg,
        commit_id=c2.commit.id,
        oig_id=graph_id,
    )
    assert out.hash == g2.hash


@pytest.mark.asyncio
async def test_fs_commit_store_resolves_typed_oig_commit_id_from_ref_index(
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

    branch_id = uuid4()
    graph_id: UUID = uuid4()
    user_id = uuid4()
    object_instance_graph_identity_id = uuid4()

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
    commit = build_object_instance_graph_commit(
        old=g0,
        new=g1,
        object_projection_graph=opg,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        branch_id=branch_id,
        author_id=uuid4(),
    )
    assert commit is not None

    store = FSCommitStore()
    await store.append(
        branch_id=branch_id, projection_hash=opg.projection_hash, commit=commit
    )

    object_instance_graph_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        commit_id=commit.commit.id,
    )

    async def _boom(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(
            "indexed OIG commit ref resolution must not walk HEAD or lineage"
        )

    monkeypatch.setattr(FSCommitStore, "head_commit", _boom, raising=True)

    resolved = await store.domain_commit_id_for_object_instance_graph_commit_id(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
    )
    assert resolved == commit.commit.id

    lineage = [
        item
        async for item in store.iter_lineage_forward(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            head_commit_id=object_instance_graph_commit_id,
            stop_at_commit_id=None,
        )
    ]
    assert [item.commit.id for item in lineage] == [commit.commit.id]

    materialized, _indexes = await OIGMaterializer(commits=store).get(
        branch_id=branch_id,
        ocg=ocg,
        opg=opg,
        commit_id=object_instance_graph_commit_id,
        oig_id=graph_id,
    )
    assert materialized.hash == g1.hash


@pytest.mark.asyncio
async def test_fs_store_session_read_cache_reuses_hot_lane_json(
    tmp_path, monkeypatch
) -> None:
    (tmp_path / ".aware").mkdir()
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path))
    _clear_fs_store_session_read_cache_for_tests()

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
    user_id = uuid4()
    object_instance_graph_identity_id = uuid4()

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
    commit = build_object_instance_graph_commit(
        old=g0,
        new=g1,
        object_projection_graph=opg,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        branch_id=branch_id,
        author_id=uuid4(),
    )
    assert commit is not None

    store = FSCommitStore()
    snapshots = FSSnapshotStore()
    await store.append(
        branch_id=branch_id, projection_hash=opg.projection_hash, commit=commit
    )
    await snapshots.put(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        commit_id=commit.commit.id,
        oig=g1,
        indexes={"class_instance_ids": []},
    )

    _clear_fs_store_session_read_cache_for_tests()

    head_first = await store.head(
        branch_id=branch_id, projection_hash=opg.projection_hash
    )
    head_second = await store.head(
        branch_id=branch_id, projection_hash=opg.projection_hash
    )
    assert head_first == head_second

    commit_first = await store.get_commit(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        commit_id=commit.commit.id,
    )
    commit_second = await store.get_commit(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        commit_id=commit.commit.id,
    )
    assert commit_first is not None
    assert commit_second is not None
    assert commit_first.commit.id == commit_second.commit.id

    snapshot_first = await snapshots.get(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        commit_id=commit.commit.id,
    )
    snapshot_second = await snapshots.get(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        commit_id=commit.commit.id,
    )
    assert snapshot_first is not None
    assert snapshot_second is not None
    assert snapshot_first[0].hash == snapshot_second[0].hash

    metrics = _snapshot_fs_store_session_read_cache_metrics()
    assert metrics["hit_count"] >= 4
    assert metrics["miss_count"] >= 4
