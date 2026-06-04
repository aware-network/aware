from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from aware_orm.graph.plan_cache import GraphPlan, GraphPlanCache
from aware_orm.graph.config_registry import GraphConfigRegistry, TableDescriptor
from aware_orm.graph.runtime import GraphSQLRuntime
from aware_orm.models.base_model import BaseORMModel
from aware_orm.models.query_mixin import QueryMixin
from aware_orm.runtime.sql_metadata import (
    SQLRuntimeMetadata,
    register_sql_metadata,
    clear_sql_metadata_registry,
)


class FakeGraphSession:
    def __init__(self, graph_payload):
        self.graph_payload = graph_payload
        self.skip_db = False
        self._backend_name = "postgres"

    def imap_get(self, cls, obj_id):
        return None

    def imap_add(self, obj):
        pass

    def log_read(self, cls, obj_id):
        pass

    async def execute_query(self, sql: str, *params):
        return [{"graph": self.graph_payload}]

    def _deserialize_to_model(self, cls, payload):
        return cls(**payload)


class GraphCanonicalModel(QueryMixin, BaseORMModel):
    id: UUID = uuid4()
    displayname: str = "Alice"
    status: str = "active"


def _install_canonical_runtime():
    GraphSQLRuntime.reset()
    clear_sql_metadata_registry()

    metadata = SQLRuntimeMetadata(
        class_config_id=uuid4(),
        table_schema="public",
        table_name="canonical_model",
        column_by_attribute={"displayname": "display_name", "status": "status"},
        persisted_attributes=frozenset({"displayname", "status"}),
        fk_owner_by_attribute={},
        fk_columns_by_attribute={},
        join_chain_by_attribute={},
    )
    register_sql_metadata(
        metadata,
        class_fqn=f"{GraphCanonicalModel.__module__}.{GraphCanonicalModel.__name__}",
    )
    GraphCanonicalModel._sql_runtime_metadata = metadata  # type: ignore[assignment]

    plan = GraphPlan(
        root_table_key="public.canonical_model",
        root_projection_fields=("id", "display_name", "status"),
    )
    cache = GraphPlanCache([plan])
    registry = GraphConfigRegistry(
        [TableDescriptor(uuid4(), "public", "canonical_model", ("id", "display_name", "status"))]
    )
    GraphSQLRuntime.install(cache, registry)
    return metadata


@pytest.mark.asyncio
async def test_get_graph_by_id_uses_plan(monkeypatch):
    metadata = _install_canonical_runtime()

    sample_id = uuid4()
    session = FakeGraphSession({"id": str(sample_id), "displayname": "Alice", "status": "active"})

    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(current_session_ctx, "current_session", lambda kind="any": session)

    result = await GraphCanonicalModel.get_graph_by_id(sample_id, sql_metadata=metadata)
    assert result and result.displayname == "Alice"

    stats = GraphSQLRuntime.plan_stats()
    assert stats["hits"].get("public.canonical_model") == 1
