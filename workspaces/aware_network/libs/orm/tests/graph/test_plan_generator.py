from uuid import uuid4

from aware_orm.graph.plan_cache import GraphPlan, PlanStep, GraphPlanCache
from aware_orm.graph.config_registry import GraphConfigRegistry, TableDescriptor
from aware_orm.graph.runtime import GraphSQLRuntime
from aware_orm.query.graph_spec import GraphScopeFilter, GraphSpec
from aware_orm.runtime.sql_metadata import SQLRuntimeMetadata
from aware_orm.sql_generator.graph_generator_plan import get_graphsql_generator


def setup_runtime():
    plan = GraphPlan(
        root_table_key="public.users",
        steps=(
            PlanStep(
                table_key="public.profiles",
                via_relationship_id=None,
                uses_collection=False,
                join_condition="public.users.profile_id = public.profiles.id",
                projection_fields=("id", "name"),
                parent_table_key="public.users",
                depth=1,
            ),
        ),
        root_projection_fields=("id", "profile_id", "name"),
    )
    cache = GraphPlanCache([plan])
    registry = GraphConfigRegistry(
        [
            TableDescriptor(uuid4(), "public", "users", ("id", "profile_id", "name")),
            TableDescriptor(uuid4(), "public", "profiles", ("id", "name")),
        ]
    )
    GraphSQLRuntime.install(cache, registry)


def teardown_runtime():
    GraphSQLRuntime.reset()


def test_plan_generator_by_id():
    setup_runtime()
    try:
        metadata = SQLRuntimeMetadata(
            class_config_id=uuid4(),
            table_schema="public",
            table_name="users",
            column_by_attribute={"status": "status"},
            persisted_attributes=frozenset({"status"}),
            fk_owner_by_attribute={},
            fk_columns_by_attribute={},
            join_chain_by_attribute={},
        )

        generator = get_graphsql_generator(
            metadata,
            source_class_fqn="tests.DummyOC",
        )
        sql, params = generator.generate_select_by_id("123")
        expected = (
            "SELECT json_build_object('id', roots.id, 'profile_id', roots.profile_id, 'name', roots.name, "
            "'profiles', (SELECT json_build_object('id', step_1.id, 'name', step_1.name) "
            "FROM public.profiles step_1 WHERE roots.profile_id = step_1.id LIMIT 1)) AS graph "
            "FROM public.users roots WHERE roots.id = $1"
        )
        assert sql == expected
        assert params == ("123",)
    finally:
        teardown_runtime()


def test_plan_generator_select_many():
    setup_runtime()
    try:
        metadata = SQLRuntimeMetadata(
            class_config_id=uuid4(),
            table_schema="public",
            table_name="users",
            column_by_attribute={"status": "status"},
            persisted_attributes=frozenset({"status"}),
            fk_owner_by_attribute={},
            fk_columns_by_attribute={},
            join_chain_by_attribute={},
        )

        generator = get_graphsql_generator(
            metadata,
            source_class_fqn="tests.DummyOC",
        )
        from aware_orm.filters import EqFilter

        filters = [EqFilter(column="status", value="active")]
        sql, params = generator.generate_select_many(filters=filters, limit=10, offset=0)
        expected_where = "roots.status = $1"
        assert expected_where in sql
        assert sql.startswith("SELECT COALESCE(json_agg(graph), '[]'::json) AS graph FROM (SELECT")
        assert params == ("active", 10, 0)
    finally:
        teardown_runtime()


def test_plan_generator_nested_cardinality_and_scope_contract():
    plan = GraphPlan(
        root_table_key="public.users",
        steps=(
            PlanStep(
                table_key="public.profiles",
                via_relationship_id=None,
                uses_collection=False,
                join_condition="public.users.profile_id = public.profiles.id",
                projection_fields=("id", "avatar_id", "name"),
                parent_table_key="public.users",
                depth=1,
            ),
            PlanStep(
                table_key="public.avatars",
                via_relationship_id=None,
                uses_collection=True,
                join_condition="public.profiles.avatar_id = public.avatars.id",
                projection_fields=("id", "url"),
                parent_table_key="public.profiles",
                depth=2,
            ),
        ),
        root_projection_fields=("id", "profile_id", "branch_id", "status"),
    )
    cache = GraphPlanCache([plan])
    registry = GraphConfigRegistry(
        [
            TableDescriptor(uuid4(), "public", "users", ("id", "profile_id", "branch_id", "status")),
            TableDescriptor(uuid4(), "public", "profiles", ("id", "avatar_id", "name")),
            TableDescriptor(uuid4(), "public", "avatars", ("id", "url")),
        ]
    )
    GraphSQLRuntime.install(cache, registry)
    try:
        metadata = SQLRuntimeMetadata(
            class_config_id=uuid4(),
            table_schema="public",
            table_name="users",
            column_by_attribute={
                "id": "id",
                "branch_id": "branch_id",
                "status": "status",
            },
            persisted_attributes=frozenset({"id", "branch_id", "status"}),
            fk_owner_by_attribute={},
            fk_columns_by_attribute={},
            join_chain_by_attribute={},
        )
        graph_spec = GraphSpec(
            max_depth=2,
            branch_id="branch-a",
            projection_scope=(GraphScopeFilter(column="status", value="active"),),
        )

        generator = get_graphsql_generator(metadata, source_class_fqn="tests.User", graph_spec=graph_spec)
        sql, params = generator.generate_select_by_id("user-1")

        assert "'profiles', (SELECT json_build_object" in sql
        assert "'avatars', COALESCE((SELECT json_agg(json_build_object" in sql
        assert "roots.branch_id = $2" in sql
        assert "roots.status = $3" in sql
        assert params == ("user-1", "branch-a", "active")
        assert generator.contract.max_depth == 2
        assert generator.contract.includes[0].cardinality == "one"
        assert generator.contract.includes[0].children[0].cardinality == "many"
    finally:
        teardown_runtime()
