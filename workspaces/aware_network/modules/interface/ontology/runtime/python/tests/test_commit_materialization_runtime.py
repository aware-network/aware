from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

import pytest

from aware_interface import (
    InterfaceCommitMaterializer,
    InterfaceLaneStores,
    InterfaceLocalDb,
    InterfaceLocalDbConfig,
    InterfaceMaterializationPostHashMismatchError,
    LocalCommitRecord,
    LocalLaneHeadRecord,
    LocalSnapshotRecord,
)
from aware_orm.db.schema_registry import (
    DBSchemaRegistry,
    build_db_schema_registry_entry,
    write_db_schema_registry,
)
from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.builder import (
    build_object_instance_graph_from_class_instances,
)
from aware_meta.graph.instance.commit.builder import build_object_instance_graph_commit
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
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
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


_REPO_ROOT = Path(__file__).resolve().parents[8]
_INTERFACE_DB_SQL_ROOT = _REPO_ROOT / "workspaces" / "aware_network" / "modules" / "interface" / "services" / "interface" / "db" / "sqlite"
_USER_FQN = test_class_fqn("User")
_TEST_OIGI_ID = uuid4()


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])


def _write_registry(*, tmp_path: Path, environment_id: UUID) -> Path:
    registry_path = tmp_path / "runtime" / "db.schema.registry.json"
    entry = build_db_schema_registry_entry(
        package_kind="state",
        backend_targets=("sqlite",),
        sql_root=_INTERFACE_DB_SQL_ROOT,
        source_label="interface-db",
        relative_to=registry_path.parent,
    )
    _ = write_db_schema_registry(
        path=registry_path,
        registry=DBSchemaRegistry(environment_id=environment_id, entries=[entry]),
    )
    return registry_path


def _build_runtime(
    tmp_path: Path,
) -> tuple[InterfaceLaneStores, InterfaceCommitMaterializer]:
    environment_id = uuid4()
    registry_path = _write_registry(tmp_path=tmp_path, environment_id=environment_id)
    db = InterfaceLocalDb(
        config=InterfaceLocalDbConfig(
            database_path=tmp_path / "state" / "interface.sqlite",
            registry_path=registry_path,
            environment_id=environment_id,
        )
    )
    stores = InterfaceLaneStores(db=db)
    return stores, InterfaceCommitMaterializer(stores=stores)


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


def _indexes_json_for_graph() -> str:
    return json.dumps(
        {"instance_map": {}, "classcfg_map": {}}, sort_keys=True, separators=(",", ":")
    )


def _descriptor_count(semantics: dict[str, object] | None) -> int:
    if semantics is None:
        return 0
    value = semantics.get("descriptor_count")
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise ValueError(f"Invalid descriptor_count payload: {value!r}")


async def _save_commit(
    stores: InterfaceLaneStores,
    commit: ObjectInstanceGraphCommit,
    *,
    branch_id: UUID,
) -> None:
    parent_commit_id = None
    if commit.commit.commit_parents:
        parent_commit_id = str(commit.commit.commit_parents[0].parent_commit_id)
    await stores.save_commit(
        LocalCommitRecord(
            branch_id=str(branch_id),
            id=str(commit.commit.id),
            commit_id=str(commit.commit.id),
            projection_hash=str(commit.projection_hash or ""),
            parent_commit_id=parent_commit_id,
            graph_hash_pre=str(commit.graph_hash_pre or ""),
            graph_hash_post=str(commit.graph_hash_post or ""),
            object_instance_graph_id=str(commit.object_instance_graph_id),
            object_instance_graph_commit_id=str(commit.id),
            payload_json=commit.model_dump_json(exclude_none=True),
        )
    )


@pytest.mark.asyncio
async def test_commit_materializer_bootstraps_from_stored_commits_and_persists_snapshot(
    tmp_path: Path,
) -> None:
    stores, materializer = _build_runtime(tmp_path)

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
    user_id = uuid4()
    graph_id = uuid4()

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

    user_a = User(id=user_id, name="a")
    ci1 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=user_a
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

    user_b = User(id=user_id, name="b")
    ci2 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=user_b
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
        branch_id=branch_id,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        author_id=author_id,
    )
    assert c1 is not None
    c2 = build_object_instance_graph_commit(
        old=g1,
        new=g2,
        branch_id=branch_id,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        author_id=author_id,
        parent_commit_id=c1.commit.id,
    )
    assert c2 is not None

    await _save_commit(stores, c1, branch_id=branch_id)
    await stores.save_commit(
        LocalCommitRecord(
            branch_id=str(branch_id),
            id=str(c2.commit.id),
            commit_id=str(c2.commit.id),
            projection_hash=opg.projection_hash,
            parent_commit_id=None,
            graph_hash_pre=str(c2.graph_hash_pre or ""),
            graph_hash_post=str(c2.graph_hash_post or ""),
            object_instance_graph_id=str(c2.object_instance_graph_id),
            object_instance_graph_commit_id=str(c2.id),
            payload_json=c2.model_dump_json(exclude_none=True),
        )
    )
    await stores.save_lane_head(
        LocalLaneHeadRecord(
            id="lane-main",
            branch_id=str(branch_id),
            projection_hash=opg.projection_hash,
            head_commit_id=str(c2.commit.id),
            graph_hash_post=g2.hash,
            object_instance_graph_id=str(graph_id),
            root_object_instance_id=(
                str(g2.root_class_instance_id)
                if g2.root_class_instance_id is not None
                else None
            ),
            v=1,
        )
    )

    state = await materializer.materialize_lane_head(
        branch_id=str(branch_id),
        projection_hash=opg.projection_hash,
        lane_id="lane-main",
        ocg=ocg,
        opg=opg,
    )

    assert state.snapshot_commit_id is None
    assert state.applied_commit_ids == (str(c1.commit.id), str(c2.commit.id))
    assert state.graph.hash == g2.hash
    assert state.graph.model_dump(mode="json", exclude_none=True) == g2.model_dump(
        mode="json", exclude_none=True
    )
    assert _descriptor_count(state.last_semantics) >= 1

    persisted_snapshot = await stores.load_snapshot(
        branch_id=str(branch_id),
        snapshot_id=str(c2.commit.id),
        projection_hash=opg.projection_hash,
    )
    assert persisted_snapshot is not None
    assert persisted_snapshot.commit_id == str(c2.commit.id)


@pytest.mark.asyncio
async def test_commit_materializer_resumes_from_nearest_stored_snapshot(
    tmp_path: Path,
) -> None:
    stores, materializer = _build_runtime(tmp_path)

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
    user_id = uuid4()
    graph_id = uuid4()

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

    user_a = User(id=user_id, name="a")
    ci1 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=user_a
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

    user_b = User(id=user_id, name="b")
    ci2 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=user_b
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
        branch_id=branch_id,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        author_id=author_id,
    )
    assert c1 is not None
    c2 = build_object_instance_graph_commit(
        old=g1,
        new=g2,
        branch_id=branch_id,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        author_id=author_id,
        parent_commit_id=c1.commit.id,
    )
    assert c2 is not None

    await _save_commit(stores, c1, branch_id=branch_id)
    await _save_commit(stores, c2, branch_id=branch_id)
    await stores.save_lane_head(
        LocalLaneHeadRecord(
            id="lane-main",
            branch_id=str(branch_id),
            projection_hash=opg.projection_hash,
            head_commit_id=str(c2.commit.id),
            graph_hash_post=g2.hash,
            object_instance_graph_id=str(graph_id),
            root_object_instance_id=(
                str(g2.root_class_instance_id)
                if g2.root_class_instance_id is not None
                else None
            ),
            v=1,
        )
    )
    await stores.save_snapshot(
        LocalSnapshotRecord(
            id=str(c1.commit.id),
            branch_id=str(branch_id),
            projection_hash=opg.projection_hash,
            commit_id=str(c1.commit.id),
            oig_json=g1.model_dump_json(exclude_none=True),
            indexes_json=_indexes_json_for_graph(),
            v=1,
        )
    )

    state = await materializer.materialize_lane_head(
        branch_id=str(branch_id),
        projection_hash=opg.projection_hash,
        lane_id="lane-main",
        ocg=ocg,
        opg=opg,
    )

    assert state.snapshot_commit_id == str(c1.commit.id)
    assert state.applied_commit_ids == (str(c2.commit.id),)
    assert state.graph.hash == g2.hash
    assert state.graph.model_dump(mode="json", exclude_none=True) == g2.model_dump(
        mode="json", exclude_none=True
    )


@pytest.mark.asyncio
async def test_commit_materializer_raises_typed_post_hash_mismatch_with_semantics(
    tmp_path: Path,
) -> None:
    stores, materializer = _build_runtime(tmp_path)

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
    user_id = uuid4()
    graph_id = uuid4()

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

    user_a = User(id=user_id, name="a")
    ci1 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=user_a
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
        branch_id=branch_id,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        author_id=author_id,
    )
    assert commit is not None
    bad_payload = cast(object, json.loads(commit.model_dump_json(exclude_none=True)))
    if not isinstance(bad_payload, dict):
        raise AssertionError("Expected commit payload to decode to a JSON object")
    bad_payload["graph_hash_post"] = "bad-hash"

    await stores.save_commit(
        LocalCommitRecord(
            branch_id=str(branch_id),
            id=str(commit.commit.id),
            commit_id=str(commit.commit.id),
            projection_hash=opg.projection_hash,
            parent_commit_id=None,
            graph_hash_pre=str(commit.graph_hash_pre or ""),
            graph_hash_post="bad-hash",
            object_instance_graph_id=str(commit.object_instance_graph_id),
            object_instance_graph_commit_id=str(commit.id),
            payload_json=json.dumps(bad_payload, sort_keys=True, separators=(",", ":")),
        )
    )
    await stores.save_lane_head(
        LocalLaneHeadRecord(
            id="lane-main",
            branch_id=str(branch_id),
            projection_hash=opg.projection_hash,
            head_commit_id=str(commit.commit.id),
            graph_hash_post="bad-hash",
            object_instance_graph_id=str(graph_id),
            root_object_instance_id=(
                str(g1.root_class_instance_id)
                if g1.root_class_instance_id is not None
                else None
            ),
            v=1,
        )
    )

    with pytest.raises(InterfaceMaterializationPostHashMismatchError) as exc_info:
        _ = await materializer.materialize_lane_head(
            branch_id=str(branch_id),
            projection_hash=opg.projection_hash,
            lane_id="lane-main",
            ocg=ocg,
            opg=opg,
        )

    details = exc_info.value.details
    assert details.expected_hash == "bad-hash"
    assert details.branch_id == str(branch_id)
    assert _descriptor_count(details.semantics) >= 1
