from __future__ import annotations
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

import pytest

from aware_interface import (
    InterfaceCommitMaterializer,
    InterfaceLaneStores,
    InterfaceLaneSyncResult,
    InterfaceLaneSyncService,
    InterfaceLocalDb,
    InterfaceLocalDbConfig,
    InterfaceProjectionPlanBundle,
    InterfaceProjectionRuntime,
    InterfaceRemoteLaneMaterialization,
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
    make_ocg_node,
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
from aware_orm.db.schema_registry import (
    DBSchemaRegistry,
    build_db_schema_registry_entry,
    write_db_schema_registry,
)
from aware_orm.models.base_model import BaseORMModel
from aware_orm.projection.plan import (
    ProjectionColumnPlan,
    ProjectionPlan,
    ProjectionPlanCache,
    ProjectionTablePlan,
)


_REPO_ROOT = Path(__file__).resolve().parents[8]
_INTERFACE_DB_SQL_ROOT = _REPO_ROOT / "workspaces" / "aware_network" / "modules" / "interface" / "services" / "interface" / "db" / "sqlite"
_USER_FQN = test_class_fqn("User")
_TEST_OIGI_ID = uuid4()


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])


def _write_projection_sql_root(*, tmp_path: Path) -> Path:
    sql_root = tmp_path / "projection_sql"
    schema_root = sql_root / "projection"
    schema_root.mkdir(parents=True, exist_ok=True)
    _ = (schema_root / "001_user_projection.sql").write_text(
        """
        CREATE TABLE user_projection (
          branch_id TEXT NOT NULL,
          projection_hash TEXT NOT NULL,
          id TEXT NOT NULL,
          name TEXT,
          PRIMARY KEY (branch_id, projection_hash, id)
        );
        """.strip()
        + "\n",
        encoding="utf-8",
    )
    return sql_root


def _write_registry(
    *, tmp_path: Path, environment_id: UUID, projection_sql_root: Path
) -> Path:
    registry_path = tmp_path / "runtime" / "db.schema.registry.json"
    entries = [
        build_db_schema_registry_entry(
            package_kind="state",
            backend_targets=("sqlite",),
            sql_root=_INTERFACE_DB_SQL_ROOT,
            source_label="interface-db",
            relative_to=registry_path.parent,
        ),
        build_db_schema_registry_entry(
            package_kind="state",
            backend_targets=("sqlite",),
            sql_root=projection_sql_root,
            source_label="projection-runtime-test",
            relative_to=registry_path.parent,
        ),
    ]
    _ = write_db_schema_registry(
        path=registry_path,
        registry=DBSchemaRegistry(environment_id=environment_id, entries=entries),
    )
    return registry_path


def _build_runtime(
    tmp_path: Path,
) -> tuple[
    InterfaceLaneStores, InterfaceCommitMaterializer, InterfaceProjectionRuntime
]:
    environment_id = uuid4()
    projection_sql_root = _write_projection_sql_root(tmp_path=tmp_path)
    registry_path = _write_registry(
        tmp_path=tmp_path,
        environment_id=environment_id,
        projection_sql_root=projection_sql_root,
    )
    db = InterfaceLocalDb(
        config=InterfaceLocalDbConfig(
            database_path=tmp_path / "state" / "interface.sqlite",
            registry_path=registry_path,
            environment_id=environment_id,
        )
    )
    stores = InterfaceLaneStores(db=db)
    materializer = InterfaceCommitMaterializer(stores=stores)
    projector = InterfaceProjectionRuntime(db=db, stores=stores)
    return stores, materializer, projector


def _make_ocg_and_opg() -> (
    tuple[ObjectConfigGraph, ObjectProjectionGraph, ClassConfig, AttributeConfig]
):
    name_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
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
        name="lane-sync-test",
        description=None,
        hash="0",
        fqn_prefix="tests.interface.lane_sync",
        language=CodeLanguage.python,
        object_config_graph_nodes=[],
    )
    ocg.object_config_graph_nodes = [
        make_ocg_node(
            object_config_graph_id=ocg.id,
            type=ObjectConfigGraphNodeType.class_,
            class_config=user_cc,
        ),
    ]

    opg = ObjectProjectionGraph(
        name="lane-sync-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="lane-sync-hash",
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
    return ocg, opg, user_cc, name_cfg


def _make_projection_plan(
    *,
    opg: ObjectProjectionGraph,
    user_cc: ClassConfig,
    name_cfg: AttributeConfig,
) -> ProjectionPlan:
    return ProjectionPlan(
        projection_hash=opg.projection_hash,
        opg_name=opg.name,
        dialect="sqlite",
        tables=(
            ProjectionTablePlan(
                table_key="projection.user_projection",
                class_config_id=user_cc.id,
                primary_key=("branch_id", "projection_hash", "id"),
                columns=(
                    ProjectionColumnPlan(
                        column_name="branch_id",
                        source="branch_id",
                        sql_type_hint="TEXT",
                        nullable=False,
                    ),
                    ProjectionColumnPlan(
                        column_name="projection_hash",
                        source="projection_hash",
                        sql_type_hint="TEXT",
                        nullable=False,
                    ),
                    ProjectionColumnPlan(
                        column_name="id",
                        source="id",
                        sql_type_hint="TEXT",
                        nullable=False,
                    ),
                    ProjectionColumnPlan(
                        column_name="name",
                        source="attribute",
                        attribute_config_id=name_cfg.id,
                        sql_type_hint="TEXT",
                    ),
                ),
            ),
        ),
        associations=(),
    )


def _make_projection_bundle(
    *,
    tmp_path: Path,
    plan: ProjectionPlan,
) -> InterfaceProjectionPlanBundle:
    return InterfaceProjectionPlanBundle(
        manifest_path=tmp_path / "artifact-ref-backed-projection-plan.json",
        plan_cache=ProjectionPlanCache((plan,)),
        enum_option_value_by_id={},
    )


def _remote_from_commit(
    *,
    branch_id: UUID,
    commit: ObjectInstanceGraphCommit,
    include_payload: bool = True,
) -> InterfaceRemoteLaneMaterialization:
    return InterfaceRemoteLaneMaterialization(
        branch_id=str(branch_id),
        projection_hash=str(commit.projection_hash or ""),
        commit_id=str(commit.commit.id),
        graph_hash_post=str(commit.graph_hash_post or ""),
        object_instance_graph_id=str(commit.object_instance_graph_id),
        root_object_id=str(commit.root_source_object_id),
        head_version=1,
        commit_payload=(
            cast(dict[str, object], commit.model_dump(mode="json", exclude_none=True))
            if include_payload
            else None
        ),
    )


@dataclass
class _FakeLaneSyncSource:
    latest: InterfaceRemoteLaneMaterialization | None
    commits_by_id: dict[str, InterfaceRemoteLaneMaterialization]
    watch_events: tuple[InterfaceRemoteLaneMaterialization, ...] = ()
    load_latest_calls: int = 0
    load_commit_calls: list[str] = field(default_factory=list)

    async def load_latest(
        self,
        *,
        branch_id: str,
        projection_hash: str,
    ) -> InterfaceRemoteLaneMaterialization | None:
        self.load_latest_calls += 1
        _ = (branch_id, projection_hash)
        return self.latest

    async def load_commit(
        self,
        *,
        branch_id: str,
        projection_hash: str,
        commit_id: str,
    ) -> InterfaceRemoteLaneMaterialization | None:
        _ = (branch_id, projection_hash)
        self.load_commit_calls.append(commit_id)
        return self.commits_by_id.get(commit_id)

    def watch_lane(
        self,
        *,
        branch_id: str,
        projection_hash: str,
        include_initial: bool = True,
    ) -> AsyncIterator[InterfaceRemoteLaneMaterialization]:
        async def _watch() -> AsyncIterator[InterfaceRemoteLaneMaterialization]:
            _ = (branch_id, projection_hash, include_initial)
            for event in self.watch_events:
                yield event

        return _watch()


@pytest.mark.asyncio
async def test_lane_sync_backfills_lineage_materializes_and_projects(
    tmp_path: Path,
) -> None:
    stores, materializer, projector = _build_runtime(tmp_path)
    ocg, opg, user_cc, name_cfg = _make_ocg_and_opg()
    plan = _make_projection_plan(opg=opg, user_cc=user_cc, name_cfg=name_cfg)
    bundle = _make_projection_bundle(tmp_path=tmp_path, plan=plan)
    projector.register_bundle(bundle)

    class User(BaseORMModel):
        name: str

    author_id = uuid4()
    branch_id = uuid4()
    user_id = uuid4()
    graph_id = uuid4()
    lane_id = "lane-main"

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

    source = _FakeLaneSyncSource(
        latest=_remote_from_commit(
            branch_id=branch_id, commit=c2, include_payload=False
        ),
        commits_by_id={
            str(c1.commit.id): _remote_from_commit(branch_id=branch_id, commit=c1),
            str(c2.commit.id): _remote_from_commit(branch_id=branch_id, commit=c2),
        },
    )
    service = InterfaceLaneSyncService(
        source=source,
        stores=stores,
        materializer=materializer,
        projector=projector,
    )

    result = await service.sync_lane_head(
        branch_id=str(branch_id),
        projection_hash=opg.projection_hash,
        lane_id=lane_id,
        ocg=ocg,
        opg=opg,
    )

    assert result.advanced is True
    assert result.head_commit_id == str(c2.commit.id)
    assert result.previous_head_commit_id is None
    assert result.fetched_commit_ids == (str(c1.commit.id), str(c2.commit.id))
    assert result.materialized_lane is not None
    assert result.materialized_lane.graph.hash == g2.hash
    assert result.projection_result is not None
    assert result.projection_result.projected is True

    stored_head = await stores.load_lane_head(
        branch_id=str(branch_id),
        lane_id=lane_id,
        projection_hash=opg.projection_hash,
    )
    assert stored_head is not None
    assert stored_head.head_commit_id == str(c2.commit.id)

    stored_c1 = await stores.load_commit(
        branch_id=str(branch_id),
        commit_id=str(c1.commit.id),
        projection_hash=opg.projection_hash,
    )
    stored_c2 = await stores.load_commit(
        branch_id=str(branch_id),
        commit_id=str(c2.commit.id),
        projection_hash=opg.projection_hash,
    )
    assert stored_c1 is not None
    assert stored_c2 is not None
    assert source.load_commit_calls == [str(c2.commit.id), str(c1.commit.id)]

    rows = await stores.db.execute_query(
        """
        SELECT id, name
        FROM user_projection
        WHERE branch_id = $1 AND projection_hash = $2
        ORDER BY id ASC
        """,
        str(branch_id),
        opg.projection_hash,
    )
    assert len(rows) == 1
    assert rows[0]["name"] == "b"


@pytest.mark.asyncio
async def test_lane_sync_noops_when_local_head_is_already_current(
    tmp_path: Path,
) -> None:
    stores, materializer, projector = _build_runtime(tmp_path)
    ocg, opg, user_cc, name_cfg = _make_ocg_and_opg()
    plan = _make_projection_plan(opg=opg, user_cc=user_cc, name_cfg=name_cfg)
    bundle = _make_projection_bundle(tmp_path=tmp_path, plan=plan)
    projector.register_bundle(bundle)

    class User(BaseORMModel):
        name: str

    author_id = uuid4()
    branch_id = uuid4()
    user_id = uuid4()
    graph_id = uuid4()
    lane_id = "lane-main"

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

    seed_source = _FakeLaneSyncSource(
        latest=_remote_from_commit(branch_id=branch_id, commit=commit),
        commits_by_id={
            str(commit.commit.id): _remote_from_commit(
                branch_id=branch_id, commit=commit
            )
        },
    )
    service = InterfaceLaneSyncService(
        source=seed_source,
        stores=stores,
        materializer=materializer,
        projector=projector,
    )
    seeded = await service.sync_lane_head(
        branch_id=str(branch_id),
        projection_hash=opg.projection_hash,
        lane_id=lane_id,
        ocg=ocg,
        opg=opg,
    )
    assert seeded.advanced is True

    source = _FakeLaneSyncSource(
        latest=_remote_from_commit(
            branch_id=branch_id, commit=commit, include_payload=False
        ),
        commits_by_id={
            str(commit.commit.id): _remote_from_commit(
                branch_id=branch_id, commit=commit
            )
        },
    )
    service = InterfaceLaneSyncService(
        source=source,
        stores=stores,
        materializer=materializer,
        projector=projector,
    )

    result = await service.sync_lane_head(
        branch_id=str(branch_id),
        projection_hash=opg.projection_hash,
        lane_id=lane_id,
        ocg=ocg,
        opg=opg,
    )

    assert result.advanced is False
    assert result.head_commit_id == str(commit.commit.id)
    assert result.previous_head_commit_id == str(commit.commit.id)
    assert result.fetched_commit_ids == ()
    assert result.materialized_lane is None
    assert result.projection_result is None
    assert source.load_commit_calls == []


@pytest.mark.asyncio
async def test_lane_sync_watch_lane_advances_on_streamed_updates(
    tmp_path: Path,
) -> None:
    stores, materializer, projector = _build_runtime(tmp_path)
    ocg, opg, user_cc, name_cfg = _make_ocg_and_opg()
    plan = _make_projection_plan(opg=opg, user_cc=user_cc, name_cfg=name_cfg)
    bundle = _make_projection_bundle(tmp_path=tmp_path, plan=plan)
    projector.register_bundle(bundle)

    class User(BaseORMModel):
        name: str

    author_id = uuid4()
    branch_id = uuid4()
    user_id = uuid4()
    graph_id = uuid4()
    lane_id = "lane-main"

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

    source = _FakeLaneSyncSource(
        latest=None,
        commits_by_id={
            str(c1.commit.id): _remote_from_commit(branch_id=branch_id, commit=c1),
            str(c2.commit.id): _remote_from_commit(branch_id=branch_id, commit=c2),
        },
        watch_events=(
            _remote_from_commit(branch_id=branch_id, commit=c1, include_payload=False),
            _remote_from_commit(branch_id=branch_id, commit=c2, include_payload=False),
        ),
    )
    service = InterfaceLaneSyncService(
        source=source,
        stores=stores,
        materializer=materializer,
        projector=projector,
    )

    results: list[InterfaceLaneSyncResult] = []
    async for sync_result in service.watch_lane(
        branch_id=str(branch_id),
        projection_hash=opg.projection_hash,
        lane_id=lane_id,
        ocg=ocg,
        opg=opg,
        include_initial=False,
    ):
        results.append(sync_result)
        if len(results) == 2:
            break

    assert [result.head_commit_id for result in results] == [
        str(c1.commit.id),
        str(c2.commit.id),
    ]
    assert all(result.advanced for result in results)

    stored_head = await stores.load_lane_head(
        branch_id=str(branch_id),
        lane_id=lane_id,
        projection_hash=opg.projection_hash,
    )
    assert stored_head is not None
    assert stored_head.head_commit_id == str(c2.commit.id)

    rows = await stores.db.execute_query(
        """
        SELECT name
        FROM user_projection
        WHERE branch_id = $1 AND projection_hash = $2
        ORDER BY id ASC
        """,
        str(branch_id),
        opg.projection_hash,
    )
    assert len(rows) == 1
    assert rows[0]["name"] == "b"
