from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from aware_orm.filters import EqFilter, RelationPathFilter, SortOrder
from aware_orm.models.base_model import BaseORMModel
from aware_orm.models.query_mixin import QueryMixin
from aware_orm.query_spec import PredicateGroup, QueryOrder, QueryPage, QuerySpec
from aware_orm.runtime.sql_metadata import (
    SQLRuntimeMetadata,
    clear_sql_metadata_registry,
    register_sql_metadata,
)


class BuilderSession:
    skip_db = False

    def __init__(self, rows: list[dict], count: int = 0):
        self.rows = rows
        self.count = count
        self.last_query_spec: QuerySpec | None = None
        self.last_count: bool | None = None
        self.reads: list[tuple[type, UUID]] = []
        self._imap = {}

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
        return [{"count": self.count}] if count else self.rows

    def imap_get(self, cls, obj_id):
        return self._imap.get((cls, obj_id))

    def imap_add(self, instance):
        if instance.id:
            self._imap[(type(instance), instance.id)] = instance

    def log_read(self, cls, obj_id):
        self.reads.append((cls, obj_id))

    def _deserialize_to_model(self, cls, payload):
        return cls(**payload)


class BuilderModel(QueryMixin, BaseORMModel):
    id: UUID = uuid4()
    displayname: str = "Alice"
    status: str = "active"
    total: int = 0


def _bind_builder_metadata() -> SQLRuntimeMetadata:
    metadata = SQLRuntimeMetadata(
        class_config_id=uuid4(),
        table_schema="public",
        table_name="builder_model",
        column_by_attribute={
            "id": "id",
            "displayname": "display_name",
            "status": "status",
            "total": "total",
        },
        persisted_attributes=frozenset({"id", "displayname", "status", "total"}),
        fk_owner_by_attribute={},
        fk_columns_by_attribute={},
        join_chain_by_attribute={},
    )
    register_sql_metadata(metadata, class_fqn=BuilderModel.get_registry_key())
    return metadata


@pytest.mark.asyncio
async def test_model_query_builder_all_uses_field_refs_and_queryspec(monkeypatch):
    clear_sql_metadata_registry()
    _bind_builder_metadata()
    sample_id = uuid4()
    session = BuilderSession(
        [
            {
                "id": str(sample_id),
                "display_name": "Alice",
                "displayname": "Alice",
                "status": "active",
                "total": 25,
            }
        ]
    )
    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(
        current_session_ctx, "current_session", lambda kind="any": session
    )

    results = await (
        BuilderModel.query()
        .where(BuilderModel.f.status.eq("active"))
        .where(BuilderModel.f.total.gte(10))
        .order_by(BuilderModel.f.displayname.desc())
        .limit(5)
        .offset(2)
        .all()
    )

    assert results and results[0].id == sample_id
    assert session.last_query_spec is not None
    assert isinstance(session.last_query_spec.where, PredicateGroup)
    assert session.last_query_spec.where.op == "and"
    assert session.last_query_spec.order_by == (
        QueryOrder(column="displayname", direction=SortOrder.DESC),
    )
    assert session.last_query_spec.page == QueryPage(limit=5, offset=2)
    assert session.reads == [(BuilderModel, sample_id)]


@pytest.mark.asyncio
async def test_model_query_builder_first_and_count(monkeypatch):
    clear_sql_metadata_registry()
    _bind_builder_metadata()
    sample_id = uuid4()
    session = BuilderSession(
        [
            {
                "id": str(sample_id),
                "display_name": "Alice",
                "displayname": "Alice",
                "status": "active",
                "total": 25,
            }
        ],
        count=7,
    )
    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(
        current_session_ctx, "current_session", lambda kind="any": session
    )

    first = await BuilderModel.query().where(BuilderModel.f.status.eq("active")).first()
    count = await BuilderModel.query().where(BuilderModel.f.status.eq("active")).count()

    assert first and first.id == sample_id
    assert count == 7
    assert session.last_count is True


@pytest.mark.asyncio
async def test_model_query_agent_sugar_uses_queryspec_backend(monkeypatch):
    clear_sql_metadata_registry()
    _bind_builder_metadata()
    sample_id = uuid4()
    session = BuilderSession(
        [
            {
                "id": str(sample_id),
                "display_name": "Alice",
                "displayname": "Alice",
                "status": "active",
                "total": 25,
            }
        ],
        count=1,
    )
    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(
        current_session_ctx, "current_session", lambda kind="any": session
    )

    by_id = await BuilderModel.by_id(sample_id)

    assert by_id and by_id.id == sample_id
    assert session.last_query_spec is not None
    assert isinstance(session.last_query_spec.where, EqFilter)
    assert session.last_query_spec.where.column == "id"
    assert session.last_query_spec.where.value == sample_id
    assert session.last_query_spec.page == QueryPage(limit=1)

    first = await BuilderModel.one(status="active", displayname="Alice")

    assert first and first.id == sample_id
    assert isinstance(session.last_query_spec.where, PredicateGroup)
    assert session.last_query_spec.where.op == "and"
    assert [
        (predicate.column, predicate.value)
        for predicate in session.last_query_spec.where.predicates
    ] == [("status", "active"), ("displayname", "Alice")]
    assert session.last_query_spec.page == QueryPage(limit=1)

    alias_first = await BuilderModel.first(status="active")
    assert alias_first and alias_first.id == sample_id

    rows = await (
        BuilderModel.where(status="active")
        .order_by(BuilderModel.f.total.desc())
        .limit(10)
        .all()
    )
    many = await BuilderModel.many(status="active")
    count = await BuilderModel.where(status="active").count()

    assert [row.id for row in rows] == [sample_id]
    assert [row.id for row in many] == [sample_id]
    assert count == 1
    assert session.last_count is True


def test_model_query_agent_sugar_rejects_unknown_fields():
    with pytest.raises(ValueError, match="unknown field 'missing'"):
        BuilderModel.where(missing="value")


def test_model_query_match_helpers_compose_exact_filters():
    query_spec = (
        BuilderModel.where(status="active")
        .match(total=10)
        .match_if_present(displayname="", id=None)
        .match_when(True, total=25)
        .match_when(False, total=999)
        .match_unless(False, displayname="Alice")
        .match_unless(True, status="archived")
        .spec()
    )

    assert isinstance(query_spec.where, PredicateGroup)
    assert [
        (predicate.column, predicate.value) for predicate in query_spec.where.predicates
    ] == [
        ("status", "active"),
        ("total", 10),
        ("displayname", ""),
        ("total", 25),
        ("displayname", "Alice"),
    ]


def test_model_query_match_helpers_reject_unknown_fields():
    with pytest.raises(ValueError, match=r"BuilderModel\.match\(\).*'missing'"):
        BuilderModel.where(status="active").match(missing="value")
    with pytest.raises(
        ValueError,
        match=r"BuilderModel\.match_if_present\(\).*'missing'",
    ):
        BuilderModel.query().match_if_present(missing=None)
    with pytest.raises(ValueError, match=r"BuilderModel\.match_when\(\).*'missing'"):
        BuilderModel.query().match_when(False, missing="value")
    with pytest.raises(ValueError, match=r"BuilderModel\.match_unless\(\).*'missing'"):
        BuilderModel.query().match_unless(True, missing="value")


def test_model_query_builder_spec_and_relation_field_refs():
    query_spec = (
        BuilderModel.query()
        .where(BuilderModel.f.status.eq("active"))
        .where(BuilderModel.f.relation("products").sku.eq("ABC123"))
        .order_by(BuilderModel.f.total.asc())
        .page(limit=10, offset=20)
        .spec()
    )

    assert isinstance(query_spec.where, PredicateGroup)
    relation_filter = query_spec.where.predicates[1]
    assert isinstance(relation_filter, RelationPathFilter)
    assert relation_filter.path == "products"
    assert relation_filter.field == "sku"
    assert relation_filter.operator == "eq"
    assert relation_filter.value == "ABC123"
    assert query_spec.order_by == (QueryOrder(column="total", direction=SortOrder.ASC),)
    assert query_spec.page == QueryPage(limit=10, offset=20)


@pytest.mark.asyncio
async def test_model_query_keeps_queryspec_await_compatibility(monkeypatch):
    clear_sql_metadata_registry()
    _bind_builder_metadata()
    sample_id = uuid4()
    session = BuilderSession(
        [
            {
                "id": str(sample_id),
                "display_name": "Alice",
                "displayname": "Alice",
                "status": "active",
                "total": 25,
            }
        ]
    )
    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(
        current_session_ctx, "current_session", lambda kind="any": session
    )
    spec = QuerySpec(where=EqFilter(column="status", value="active"))

    results = await BuilderModel.query(spec)

    assert results and results[0].id == sample_id
    assert session.last_query_spec is spec
