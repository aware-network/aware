# @code-under-test: ../../aware_orm/models/query_mixin.py

from __future__ import annotations

from typing import Any, Sequence
from uuid import uuid4

import pytest

from aware_orm.models.query_mixin import QueryMixin
from aware_orm.runtime.sql_metadata import SQLRuntimeMetadata


class GraphModel(QueryMixin):
    """Lightweight model used for QueryMixin graph tests."""


class FakeSession:
    def __init__(self, results: Sequence[dict[str, Any]]):
        self.results = list(results)
        self.skip_db = False
        self.executed = []
        self._added = []

    async def execute_query(self, sql: str, *params):
        self.executed.append((sql, params))
        return self.results

    def imap_get(self, *_args, **_kwargs):
        return None

    def imap_add(self, instance):
        self._added.append(instance)

    def log_read(self, *_args, **_kwargs):
        return None


class DummyGenerator:
    def __init__(self, sql_metadata, **kwargs):
        self.sql_metadata = sql_metadata
        self.kwargs = kwargs

    def generate_select_by_id(self, obj_id):
        return "SELECT graph FROM stub", (obj_id,)

    def generate_select_many(self, filters=None, limit=None, offset=None):
        return "SELECT graph_list FROM stub", (filters, limit, offset)


def _metadata() -> SQLRuntimeMetadata:
    return SQLRuntimeMetadata(
        class_config_id=uuid4(),
        table_schema="public",
        table_name="graph_model",
        column_by_attribute={},
        persisted_attributes=frozenset(),
        fk_owner_by_attribute={},
        fk_columns_by_attribute={},
        join_chain_by_attribute={},
    )


@pytest.mark.asyncio
async def test_get_graph_by_id_hydrates_instance(monkeypatch):
    record = {
        "graph": {
            "id": str(uuid4()),
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": None,
        }
    }
    session = FakeSession([record])
    monkeypatch.setattr("aware_orm.session.current_session_ctx.current_session", lambda: session)
    monkeypatch.setattr(
        "aware_orm.models.query_mixin.get_graphsql_generator",
        lambda *args, **kwargs: DummyGenerator(*args, **kwargs),
    )

    result = await GraphModel.get_graph_by_id(uuid4(), sql_metadata=_metadata())

    assert isinstance(result, GraphModel)
    assert session.executed[0][0] == "SELECT graph FROM stub"


@pytest.mark.asyncio
async def test_get_graph_by_id_returns_none_when_empty(monkeypatch):
    session = FakeSession([])
    monkeypatch.setattr("aware_orm.session.current_session_ctx.current_session", lambda: session)

    monkeypatch.setattr(
        "aware_orm.models.query_mixin.get_graphsql_generator",
        lambda *args, **kwargs: DummyGenerator(*args, **kwargs),
    )
    result = await GraphModel.get_graph_by_id(uuid4(), sql_metadata=_metadata())
    assert result is None


@pytest.mark.asyncio
async def test_get_graph_list_returns_instances(monkeypatch):
    graph_payload = [
        {
            "id": str(uuid4()),
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": None,
        }
    ]
    session = FakeSession([{"graph": graph_payload}])
    monkeypatch.setattr("aware_orm.session.current_session_ctx.current_session", lambda: session)

    monkeypatch.setattr(
        "aware_orm.models.query_mixin.get_graphsql_generator",
        lambda *args, **kwargs: DummyGenerator(*args, **kwargs),
    )
    results = await GraphModel.get_graph_list(limit=5, offset=2, sql_metadata=_metadata())

    assert len(results) == 1
    assert isinstance(results[0], GraphModel)
    sql, params = session.executed[0]
    assert sql == "SELECT graph_list FROM stub"
    assert params[1] == 5 and params[2] == 2


@pytest.mark.asyncio
async def test_get_graph_list_skip_db_returns_empty(monkeypatch):
    session = FakeSession([])
    session.skip_db = True
    monkeypatch.setattr("aware_orm.session.current_session_ctx.current_session", lambda: session)

    monkeypatch.setattr(
        "aware_orm.models.query_mixin.get_graphsql_generator",
        lambda *args, **kwargs: DummyGenerator(*args, **kwargs),
    )
    results = await GraphModel.get_graph_list(limit=1, sql_metadata=_metadata())
    assert results == []
    assert session.executed == []
