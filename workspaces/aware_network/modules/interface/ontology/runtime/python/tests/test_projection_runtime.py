from __future__ import annotations

from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

import pytest

from aware_interface import (
    InterfaceLaneStores,
    InterfaceLocalDb,
    InterfaceLocalDbConfig,
    InterfaceMaterializedLane,
    InterfaceProjectionPlanBundle,
    InterfaceProjectionRuntime,
)
from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.builder import (
    build_object_instance_graph_from_class_instances,
)
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    make_ocg_node,
    make_relationship,
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
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipType,
)
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
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
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_orm.db.schema_registry import (
    DBSchemaRegistry,
    build_db_schema_registry_entry,
    write_db_schema_registry,
)
from aware_orm.models.base_model import BaseORMModel
from aware_orm.projection.plan import (
    ProjectionAssociationPlan,
    ProjectionColumnPlan,
    ProjectionPlan,
    ProjectionPlanCache,
    ProjectionTablePlan,
)


_REPO_ROOT = Path(__file__).resolve().parents[8]
_INTERFACE_DB_SQL_ROOT = _REPO_ROOT / "workspaces" / "aware_network" / "modules" / "interface" / "services" / "interface" / "db" / "sqlite"
_USER_FQN = test_class_fqn("User")


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
          friend_id TEXT,
          PRIMARY KEY (branch_id, projection_hash, id)
        );
        """.strip()
        + "\n",
        encoding="utf-8",
    )
    _ = (schema_root / "002_user_friend_projection.sql").write_text(
        """

        CREATE TABLE user_friend_projection (
          branch_id TEXT NOT NULL,
          projection_hash TEXT NOT NULL,
          id TEXT NOT NULL,
          source_user_id TEXT NOT NULL,
          target_user_id TEXT NOT NULL,
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
) -> tuple[InterfaceLocalDb, InterfaceLaneStores, InterfaceProjectionRuntime]:
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
    return db, stores, InterfaceProjectionRuntime(db=db, stores=stores)


def _make_ocg_and_opg() -> tuple[
    ObjectConfigGraph,
    ObjectProjectionGraph,
    ClassConfig,
    AttributeConfig,
    ClassConfigRelationship,
]:
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
    friend_rel = make_relationship(
        class_config_id=user_cc.id,
        target_class_config_id=user_cc.id,
        relationship_type=ClassConfigRelationshipType.many_to_one,
        relationship_key="user.friend",
        forward_required=False,
    )

    ocg = ObjectConfigGraph(
        name="projection-runtime-test",
        description=None,
        hash="0",
        fqn_prefix="tests.interface.projection",
        language=CodeLanguage.python,
        object_config_graph_nodes=[],
    )
    ocg.object_config_graph_nodes = [
        make_ocg_node(
            object_config_graph_id=ocg.id,
            type=ObjectConfigGraphNodeType.class_,
            class_config=user_cc,
        ),
        make_ocg_node(
            object_config_graph_id=ocg.id,
            type=ObjectConfigGraphNodeType.relationship,
            class_config_relationship=friend_rel,
        ),
    ]

    opg = ObjectProjectionGraph(
        name="projection-runtime-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="projection-runtime-hash",
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
    return ocg, opg, user_cc, name_cfg, friend_rel


def _make_plan(
    *,
    opg: ObjectProjectionGraph,
    user_cc: ClassConfig,
    name_cfg: AttributeConfig,
    friend_rel: ClassConfigRelationship,
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
                    ProjectionColumnPlan(
                        column_name="friend_id",
                        source="fk_attribute",
                        relationship_id=friend_rel.id,
                        direction="forward",
                        sql_type_hint="TEXT",
                    ),
                ),
            ),
        ),
        associations=(
            ProjectionAssociationPlan(
                association_table_key="projection.user_friend_projection",
                relationship_id=friend_rel.id,
                source_fk_column="source_user_id",
                target_fk_column="target_user_id",
            ),
        ),
    )


def _make_materialized_lane(
    *,
    branch_id: UUID,
    projection_hash: str,
    graph: ObjectInstanceGraph,
    target_commit_id: UUID,
) -> InterfaceMaterializedLane:
    return InterfaceMaterializedLane(
        branch_id=str(branch_id),
        projection_hash=projection_hash,
        target_commit_id=str(target_commit_id),
        snapshot_commit_id=None,
        applied_commit_ids=(str(target_commit_id),),
        graph=graph,
        indexes={"instance_map": {}, "classcfg_map": {}},
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


def _build_snapshot_pair(
    *,
    ocg: ObjectConfigGraph,
    opg: ObjectProjectionGraph,
    user_cc: ClassConfig,
    friend_rel: ClassConfigRelationship,
) -> tuple[ObjectInstanceGraph, ObjectInstanceGraph]:
    class User(BaseORMModel):
        name: str

    graph_id = uuid4()
    root_user_id = uuid4()
    friend_user_id = uuid4()

    root_user = User(id=root_user_id, name="root")
    friend_user = User(id=friend_user_id, name="friend")
    root_ci = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=root_user
    )
    friend_ci = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=friend_user
    )
    relationship = ClassInstanceRelationship(
        object_instance_graph_id=graph_id,
        class_config_relationship_id=friend_rel.id,
        source_class_instance_id=root_ci.id,
        target_class_instance_id=friend_ci.id,
    )
    graph_one = build_object_instance_graph_from_class_instances(
        key="projection-runtime",
        name="projection-runtime",
        description="projection-runtime",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=root_ci,
        class_instances=[root_ci, friend_ci],
        class_instance_relationships=[relationship],
        oig_id=graph_id,
    )

    root_user_v2 = User(id=root_user_id, name="root-v2")
    root_ci_v2 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=root_user_v2
    )
    graph_two = build_object_instance_graph_from_class_instances(
        key="projection-runtime",
        name="projection-runtime",
        description="projection-runtime",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=root_ci_v2,
        class_instances=[root_ci_v2],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    return graph_one, graph_two


def test_projection_runtime_uses_artifact_ref_projection_plan_bundle(
    tmp_path: Path,
) -> None:
    _ocg, opg, user_cc, name_cfg, friend_rel = _make_ocg_and_opg()
    plan = _make_plan(
        opg=opg, user_cc=user_cc, name_cfg=name_cfg, friend_rel=friend_rel
    )
    bundle = _make_projection_bundle(tmp_path=tmp_path, plan=plan)

    recovered = bundle.resolve_plan(projection_hash=opg.projection_hash)
    assert recovered == plan
    assert bundle.enum_option_value_by_id == {}


@pytest.mark.asyncio
async def test_projection_runtime_projects_lane_rows_and_updates_cursor(
    tmp_path: Path,
) -> None:
    db, stores, runtime = _build_runtime(tmp_path)
    ocg, opg, user_cc, name_cfg, friend_rel = _make_ocg_and_opg()
    plan = _make_plan(
        opg=opg, user_cc=user_cc, name_cfg=name_cfg, friend_rel=friend_rel
    )
    bundle = _make_projection_bundle(tmp_path=tmp_path, plan=plan)
    runtime.register_bundle(bundle)

    graph_one, graph_two = _build_snapshot_pair(
        ocg=ocg,
        opg=opg,
        user_cc=user_cc,
        friend_rel=friend_rel,
    )
    branch_id = uuid4()

    result_one = await runtime.project_materialized_lane(
        branch_id=str(branch_id),
        materialized_lane=_make_materialized_lane(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            graph=graph_one,
            target_commit_id=uuid4(),
        ),
    )
    assert result_one.projected is True
    assert result_one.class_row_count == 2
    assert result_one.association_row_count == 1

    user_rows_one = await db.execute_query(
        """
        SELECT branch_id, projection_hash, id, name, friend_id
        FROM user_projection
        WHERE branch_id = $1 AND projection_hash = $2
        ORDER BY id ASC
        """,
        str(branch_id),
        opg.projection_hash,
    )
    assert len(user_rows_one) == 2
    assert sorted(cast(str, row["name"]) for row in user_rows_one) == ["friend", "root"]
    root_row = next(row for row in user_rows_one if row["name"] == "root")
    friend_row = next(row for row in user_rows_one if row["name"] == "friend")
    assert root_row["friend_id"] == friend_row["id"]
    assert friend_row["friend_id"] is None

    association_rows_one = await db.execute_query(
        """
        SELECT id, source_user_id, target_user_id
        FROM user_friend_projection
        WHERE branch_id = $1 AND projection_hash = $2
        ORDER BY id ASC
        """,
        str(branch_id),
        opg.projection_hash,
    )
    assert len(association_rows_one) == 1
    assert association_rows_one[0]["source_user_id"] == root_row["id"]
    assert association_rows_one[0]["target_user_id"] == friend_row["id"]

    cursor_one = await stores.load_projection_cursor(
        branch_id=str(branch_id),
        cursor_id=result_one.cursor_id,
        projection_hash=opg.projection_hash,
    )
    assert cursor_one is not None
    assert cursor_one.head_commit_id == result_one.head_commit_id

    replay_same_head = await runtime.project_materialized_lane(
        branch_id=str(branch_id),
        materialized_lane=_make_materialized_lane(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            graph=graph_one,
            target_commit_id=UUID(result_one.head_commit_id),
        ),
    )
    assert replay_same_head.projected is False

    result_two = await runtime.project_materialized_lane(
        branch_id=str(branch_id),
        materialized_lane=_make_materialized_lane(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            graph=graph_two,
            target_commit_id=uuid4(),
        ),
    )
    assert result_two.projected is True
    assert result_two.class_row_count == 1
    assert result_two.association_row_count == 0

    user_rows_two = await db.execute_query(
        """
        SELECT id, name, friend_id
        FROM user_projection
        WHERE branch_id = $1 AND projection_hash = $2
        ORDER BY id ASC
        """,
        str(branch_id),
        opg.projection_hash,
    )
    assert user_rows_two == [
        {
            "id": user_rows_two[0]["id"],
            "name": "root-v2",
            "friend_id": None,
        }
    ]

    association_rows_two = await db.execute_query(
        """
        SELECT id
        FROM user_friend_projection
        WHERE branch_id = $1 AND projection_hash = $2
        """,
        str(branch_id),
        opg.projection_hash,
    )
    assert association_rows_two == []

    cursor_two = await stores.load_projection_cursor(
        branch_id=str(branch_id),
        cursor_id=result_two.cursor_id,
        projection_hash=opg.projection_hash,
    )
    assert cursor_two is not None
    assert cursor_two.head_commit_id == result_two.head_commit_id
