from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from aware_orm.filters import EqFilter, SortOrder
from aware_orm.models.base_model import BaseORMModel
from aware_orm.models.query_mixin import QueryMixin
from aware_orm.query_spec import QueryOrder, QueryPage, QuerySpec
from aware_orm.runtime.sql_metadata import (
    SQLRuntimeMetadata,
    register_sql_metadata,
    clear_sql_metadata_registry,
)


class FakeSession:
    def __init__(self, rows: list[dict], count: int = 1, backend_name: str = "postgres"):
        self.rows = rows
        self.count = count
        self.skip_db = False
        self._backend_name = backend_name
        self._imap: dict[tuple[type, UUID], BaseORMModel] = {}
        self.reads: list[tuple[type, UUID]] = []
        self.last_sql: str | None = None
        self.last_params: tuple | None = None
        self.last_query_spec: QuerySpec | None = None
        self.last_query_count: bool | None = None

    def imap_get(self, cls, obj_id):
        return self._imap.get((cls, obj_id))

    def imap_add(self, obj):
        if getattr(obj, "id", None):
            self._imap[(obj.__class__, obj.id)] = obj

    def log_read(self, cls, obj_id):
        self.reads.append((cls, obj_id))

    async def execute_query(self, sql: str, *params):
        self.last_sql = sql
        self.last_params = params
        if "COUNT" in sql.upper():
            return [{"count": self.count}]
        return self.rows

    async def execute_query_spec(
        self,
        *,
        sql_metadata,
        query_spec: QuerySpec,
        source_class_fqn: str | None,
        count: bool = False,
    ):
        self.last_query_spec = query_spec
        self.last_query_count = count
        if count:
            return [{"count": self.count}]
        return self.rows

    def _deserialize_to_model(self, cls, payload):
        return cls(**payload)


class FallbackQuerySpecBackend:
    name = "fallback"

    def __init__(self, rows: list[dict] | None = None):
        self.rows = rows or []
        self.last_sql: str | None = None
        self.last_params: tuple | None = None

    def enqueue_insert(self, sql, params):  # noqa: ANN001
        raise AssertionError("not used")

    def enqueue_update(self, sql, params):  # noqa: ANN001
        raise AssertionError("not used")

    def enqueue_delete(self, sql, params):  # noqa: ANN001
        raise AssertionError("not used")

    def has_pending_operations(self):
        return False

    def get_pending_counts(self):
        return {"inserts": 0, "updates": 0, "deletes": 0}

    def clear_pending(self):
        return None

    async def execute_read(self, sql, params):  # noqa: ANN001
        self.last_sql = sql
        self.last_params = params
        return self.rows

    async def commit(self):
        return None

    async def rollback(self):
        return None


class StructuredQuerySpecBackend(FallbackQuerySpecBackend):
    def __init__(self, rows: list[dict] | None = None):
        super().__init__(rows)
        self.last_query_spec: QuerySpec | None = None
        self.last_count: bool | None = None

    async def execute_query_spec(
        self,
        *,
        sql_metadata,
        query_spec: QuerySpec,
        source_class_fqn: str | None,
        count: bool = False,
    ):
        self.last_query_spec = query_spec
        self.last_count = count
        return [{"count": 7}] if count else self.rows


class CanonicalModel(QueryMixin, BaseORMModel):
    id: UUID = uuid4()
    displayname: str = "Alice"
    status: str = "active"


def _bind_canonical_metadata():
    from aware_meta_ontology.class_.class_config import ClassConfig

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
    register_sql_metadata(metadata, class_fqn=f"{CanonicalModel.__module__}.{CanonicalModel.__name__}")
    CanonicalModel._sql_runtime_metadata = metadata  # type: ignore[assignment]
    CanonicalModel._class_config = ClassConfig(
        id=uuid4(),
        name="CanonicalModel",
        class_fqn=f"{CanonicalModel.__module__}.{CanonicalModel.__name__}",
        description="Canonical model",
    )
    return metadata


def _active_spec() -> QuerySpec:
    return QuerySpec(
        where=EqFilter(column="status", value="active"),
        order_by=(QueryOrder(column="displayname", direction=SortOrder.ASC),),
        page=QueryPage(limit=10, offset=0),
    )


@pytest.mark.asyncio
async def test_query_spec_model_query_uses_session_contract(monkeypatch):
    clear_sql_metadata_registry()
    _bind_canonical_metadata()

    sample_id = uuid4()
    rows = [
        {
            "id": str(sample_id),
            "display_name": "Alice",
            "displayname": "Alice",
            "status": "active",
        }
    ]
    session = FakeSession(rows, count=1)
    spec = _active_spec()
    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(current_session_ctx, "current_session", lambda kind="any": session)

    results = await CanonicalModel.query(spec)

    assert session.last_query_spec is spec
    assert session.last_query_count is False
    assert results and results[0].displayname == "Alice"
    assert session.reads == [(CanonicalModel, sample_id)]


@pytest.mark.asyncio
async def test_count_query_uses_session_contract(monkeypatch):
    clear_sql_metadata_registry()
    _bind_canonical_metadata()

    session = FakeSession(rows=[], count=3)
    spec = _active_spec()
    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(current_session_ctx, "current_session", lambda kind="any": session)

    result = await CanonicalModel.count_query(spec)

    assert result == 3
    assert session.last_query_spec is spec
    assert session.last_query_count is True


@pytest.mark.asyncio
async def test_first_query_caps_queryspec_page_limit(monkeypatch):
    clear_sql_metadata_registry()
    _bind_canonical_metadata()

    sample_id = uuid4()
    session = FakeSession(
        [
            {
                "id": str(sample_id),
                "display_name": "Alice",
                "displayname": "Alice",
                "status": "active",
            }
        ]
    )
    spec = QuerySpec(where=EqFilter(column="status", value="active"))
    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(current_session_ctx, "current_session", lambda kind="any": session)

    result = await CanonicalModel.first_query(spec)

    assert result and result.id == sample_id
    assert session.last_query_spec is not None
    assert session.last_query_spec.page is not None
    assert session.last_query_spec.page.limit == 1


@pytest.mark.asyncio
async def test_query_spec_model_query_does_not_swallow_contract_errors(monkeypatch):
    clear_sql_metadata_registry()
    _bind_canonical_metadata()

    class FailingSession(FakeSession):
        async def execute_query_spec(self, **kwargs):  # noqa: ANN003
            raise ValueError("strict query failure")

    session = FailingSession(rows=[])
    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(current_session_ctx, "current_session", lambda kind="any": session)

    with pytest.raises(ValueError, match="strict query failure"):
        await CanonicalModel.query(_active_spec())


@pytest.mark.asyncio
async def test_session_execute_query_spec_prefers_structured_backend_hook():
    from aware_orm.session.session import Session

    clear_sql_metadata_registry()
    metadata = _bind_canonical_metadata()
    sample_id = uuid4()
    backend = StructuredQuerySpecBackend(
        [
            {
                "id": str(sample_id),
                "display_name": "Alice",
                "displayname": "Alice",
                "status": "active",
            }
        ]
    )
    session = Session(skip_db=False, backend=backend)
    spec = _active_spec()

    rows = await session.execute_query_spec(
        sql_metadata=metadata,
        query_spec=spec,
        source_class_fqn=CanonicalModel.get_registry_key(),
    )

    assert rows and rows[0]["id"] == str(sample_id)
    assert backend.last_query_spec is spec
    assert backend.last_count is False
    assert backend.last_sql is None


@pytest.mark.asyncio
async def test_session_execute_query_spec_falls_back_to_sql_generation():
    from aware_orm.session.session import Session

    clear_sql_metadata_registry()
    metadata = _bind_canonical_metadata()
    backend = FallbackQuerySpecBackend([])
    session = Session(skip_db=False, backend=backend)

    await session.execute_query_spec(
        sql_metadata=metadata,
        query_spec=_active_spec(),
        source_class_fqn=CanonicalModel.get_registry_key(),
    )

    assert backend.last_sql is not None
    assert "SELECT * FROM public.canonical_model" in backend.last_sql
    assert "WHERE status = $1" in backend.last_sql
    assert "ORDER BY display_name ASC" in backend.last_sql


@pytest.mark.asyncio
async def test_get_list_uses_canonical_metadata(monkeypatch, caplog):
    clear_sql_metadata_registry()
    _bind_canonical_metadata()

    sample_id = uuid4()
    rows = [
        {
            "id": str(sample_id),
            "display_name": "Alice",
            "displayname": "Alice",
            "status": "active",
        }
    ]
    session = FakeSession(rows)
    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(current_session_ctx, "current_session", lambda kind="any": session)

    with caplog.at_level("WARNING"):
        results = await CanonicalModel.get_list(filters=[EqFilter(column="displayname", value="Alice")], eager=False)

    assert session.last_sql and "display_name" in session.last_sql
    assert results and results[0].displayname == "Alice"
    assert not any("SQL_METADATA_MISSING" in rec.message for rec in caplog.records)


@pytest.mark.asyncio
async def test_get_list_sqlite_backend_falls_back_to_row_query(monkeypatch):
    clear_sql_metadata_registry()
    _bind_canonical_metadata()

    sample_id = uuid4()
    session = FakeSession(
        [
            {
                "id": str(sample_id),
                "display_name": "Alice",
                "displayname": "Alice",
                "status": "active",
            }
        ],
        backend_name="sqlite",
    )
    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(current_session_ctx, "current_session", lambda kind="any": session)
    monkeypatch.setattr(
        "aware_orm.models.query_mixin.get_graphsql_generator",
        lambda *_args, **_kwargs: pytest.fail("sqlite get_list should not use GraphSQL"),
    )

    results = await CanonicalModel.get_list(filters=[EqFilter(column="displayname", value="Alice")])

    assert session.last_sql and "display_name" in session.last_sql
    assert results and results[0].displayname == "Alice"


@pytest.mark.asyncio
async def test_get_by_id_sqlite_backend_falls_back_to_row_query(monkeypatch):
    clear_sql_metadata_registry()
    _bind_canonical_metadata()

    sample_id = uuid4()
    session = FakeSession(
        [
            {
                "id": str(sample_id),
                "display_name": "Alice",
                "displayname": "Alice",
                "status": "active",
            }
        ],
        backend_name="sqlite",
    )
    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(current_session_ctx, "current_session", lambda kind="any": session)
    monkeypatch.setattr(
        "aware_orm.models.query_mixin.get_graphsql_generator",
        lambda *_args, **_kwargs: pytest.fail("sqlite get_by_id should not use GraphSQL"),
    )

    result = await CanonicalModel.get_by_id(sample_id)

    assert session.last_sql and "canonical_model" in session.last_sql
    assert result and result.displayname == "Alice"


@pytest.mark.asyncio
async def test_explicit_graph_query_rejects_sqlite_backend_before_generator(monkeypatch):
    clear_sql_metadata_registry()
    metadata = _bind_canonical_metadata()

    session = FakeSession([], backend_name="sqlite")
    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(current_session_ctx, "current_session", lambda kind="any": session)
    monkeypatch.setattr(
        "aware_orm.models.query_mixin.get_graphsql_generator",
        lambda *_args, **_kwargs: pytest.fail("sqlite explicit graph query should fail before generator use"),
    )

    with pytest.raises(RuntimeError, match="GraphSQL eager loading is not supported"):
        await CanonicalModel.get_graph_by_id(uuid4(), sql_metadata=metadata)

    assert session.last_sql is None


@pytest.mark.asyncio
async def test_count_uses_canonical_metadata(monkeypatch, caplog):
    clear_sql_metadata_registry()
    _bind_canonical_metadata()

    session = FakeSession(rows=[], count=2)
    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(current_session_ctx, "current_session", lambda kind="any": session)

    with caplog.at_level("WARNING"):
        result = await CanonicalModel.count(filters=[EqFilter(column="status", value="active")])

    assert session.last_sql and "status" in session.last_sql
    assert result == 2
    assert not any("SQL_METADATA_MISSING" in rec.message for rec in caplog.records)


def test_get_by_id_cached_uses_identity_map_only(monkeypatch):
    sample_id = uuid4()
    cached = CanonicalModel(id=sample_id, displayname="Cached", status="active")
    session = FakeSession(rows=[])
    session.imap_add(cached)

    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(current_session_ctx, "current_session", lambda kind="any": session)

    result = CanonicalModel.get_by_id_cached(sample_id)

    assert result is cached
    assert session.last_sql is None
    assert session.reads == [(CanonicalModel, sample_id)]


def test_get_by_id_sync_aliases_get_by_id_cached(monkeypatch):
    sample_id = uuid4()
    sentinel = CanonicalModel(id=sample_id, displayname="Alias", status="active")
    seen: dict[str, UUID] = {}

    def _fake_cached(cls, obj_id):  # noqa: ANN001
        seen["obj_id"] = obj_id
        return sentinel

    monkeypatch.setattr(CanonicalModel, "get_by_id_cached", classmethod(_fake_cached))

    result = CanonicalModel.get_by_id_sync(sample_id)

    assert result is sentinel
    assert seen["obj_id"] == sample_id
