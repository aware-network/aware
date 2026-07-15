from __future__ import annotations

import ast
from pathlib import Path
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
    def __init__(
        self, rows: list[dict], count: int = 1, backend_name: str = "postgres"
    ):
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
    register_sql_metadata(
        metadata, class_fqn=f"{CanonicalModel.__module__}.{CanonicalModel.__name__}"
    )
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
async def test_model_query_builder_uses_session_contract(monkeypatch):
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
    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(
        current_session_ctx, "current_session", lambda kind="any": session
    )

    results = (
        await CanonicalModel.query()
        .where(EqFilter(column="status", value="active"))
        .order_by(QueryOrder(column="displayname", direction=SortOrder.ASC))
        .page(limit=10, offset=0)
        .all()
    )

    assert session.last_query_spec == _active_spec()
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

    monkeypatch.setattr(
        current_session_ctx, "current_session", lambda kind="any": session
    )

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

    monkeypatch.setattr(
        current_session_ctx, "current_session", lambda kind="any": session
    )

    result = await CanonicalModel.first_query(spec)

    assert result and result.id == sample_id
    assert session.last_query_spec is not None
    assert session.last_query_spec.page is not None
    assert session.last_query_spec.page.limit == 1


@pytest.mark.asyncio
async def test_first_query_does_not_swallow_contract_errors(monkeypatch):
    clear_sql_metadata_registry()
    _bind_canonical_metadata()

    class FailingSession(FakeSession):
        async def execute_query_spec(self, **kwargs):  # noqa: ANN003
            raise ValueError("strict query failure")

    session = FailingSession(rows=[])
    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(
        current_session_ctx, "current_session", lambda kind="any": session
    )

    with pytest.raises(ValueError, match="strict query failure"):
        await CanonicalModel.first_query(_active_spec())


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
async def test_query_builder_where_uses_canonical_metadata(monkeypatch, caplog):
    from aware_orm.session.session import Session

    clear_sql_metadata_registry()
    _bind_canonical_metadata()

    sample_id = uuid4()
    backend = FallbackQuerySpecBackend(
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
    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(
        current_session_ctx, "current_session", lambda kind="any": session
    )

    with caplog.at_level("WARNING"):
        results = (
            await CanonicalModel.query()
            .where(EqFilter(column="displayname", value="Alice"))
            .all()
        )

    assert backend.last_sql and "display_name" in backend.last_sql
    assert results and results[0].displayname == "Alice"
    assert not any("SQL_METADATA_MISSING" in rec.message for rec in caplog.records)


@pytest.mark.asyncio
async def test_query_builder_sqlite_backend_uses_queryspec_not_graphsql(monkeypatch):
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

    monkeypatch.setattr(
        current_session_ctx, "current_session", lambda kind="any": session
    )
    monkeypatch.setattr(
        "aware_orm.models.query_mixin.get_graphsql_generator",
        lambda *_args, **_kwargs: pytest.fail(
            "sqlite query builder should not use GraphSQL"
        ),
    )

    results = (
        await CanonicalModel.query()
        .where(EqFilter(column="displayname", value="Alice"))
        .all()
    )

    assert session.last_query_spec is not None
    assert results and results[0].displayname == "Alice"


@pytest.mark.asyncio
async def test_by_id_sqlite_backend_uses_queryspec_not_graphsql(monkeypatch):
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

    monkeypatch.setattr(
        current_session_ctx, "current_session", lambda kind="any": session
    )
    monkeypatch.setattr(
        "aware_orm.models.query_mixin.get_graphsql_generator",
        lambda *_args, **_kwargs: pytest.fail("sqlite by_id should not use GraphSQL"),
    )

    result = await CanonicalModel.by_id(sample_id)

    assert session.last_query_spec is not None
    assert result and result.displayname == "Alice"


@pytest.mark.asyncio
async def test_explicit_graph_query_rejects_sqlite_backend_before_generator(
    monkeypatch,
):
    clear_sql_metadata_registry()
    metadata = _bind_canonical_metadata()

    session = FakeSession([], backend_name="sqlite")
    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(
        current_session_ctx, "current_session", lambda kind="any": session
    )
    monkeypatch.setattr(
        "aware_orm.models.query_mixin.get_graphsql_generator",
        lambda *_args, **_kwargs: pytest.fail(
            "sqlite explicit graph query should fail before generator use"
        ),
    )

    with pytest.raises(RuntimeError, match="GraphSQL eager loading is not supported"):
        await CanonicalModel.get_graph_by_id(uuid4(), sql_metadata=metadata)

    assert session.last_sql is None


@pytest.mark.asyncio
async def test_query_builder_count_uses_queryspec_contract(monkeypatch, caplog):
    clear_sql_metadata_registry()
    _bind_canonical_metadata()

    session = FakeSession(rows=[], count=2)
    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(
        current_session_ctx, "current_session", lambda kind="any": session
    )

    with caplog.at_level("WARNING"):
        result = (
            await CanonicalModel.query()
            .where(EqFilter(column="status", value="active"))
            .count()
        )

    assert session.last_query_spec is not None
    assert session.last_query_count is True
    assert result == 2
    assert not any("SQL_METADATA_MISSING" in rec.message for rec in caplog.records)


def test_query_mixin_async_legacy_helpers_are_removed() -> None:
    removed_helpers = {
        "get_by_id",
        "get",
        "get_list",
        "batch_get",
        "count",
        "exists",
        "find_by_id",
        "find",
        "find_all",
    }

    assert removed_helpers.isdisjoint(vars(QueryMixin))


def test_by_id_cached_uses_identity_map_only(monkeypatch):
    sample_id = uuid4()
    cached = CanonicalModel(id=sample_id, displayname="Cached", status="active")
    session = FakeSession(rows=[])
    session.imap_add(cached)

    from aware_orm.session import current_session_ctx

    monkeypatch.setattr(
        current_session_ctx, "current_session", lambda kind="any": session
    )

    result = CanonicalModel.by_id_cached(sample_id)

    assert result is cached
    assert session.last_sql is None
    assert session.reads == [(CanonicalModel, sample_id)]


def test_query_mixin_cache_only_legacy_aliases_are_removed() -> None:
    removed_helpers = _removed_cache_only_helpers()

    assert removed_helpers.isdisjoint(vars(QueryMixin))


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "AGENTS.md").exists():
            return parent
    raise AssertionError("Could not locate repository root")


def _legacy_async_helper_offenders(target_paths: tuple[str, ...]) -> list[str]:
    repo_root = _repo_root()
    offenders: list[str] = []

    for relative_path in target_paths:
        path = repo_root / relative_path
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative_path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(
                node.func, ast.Attribute
            ):
                continue
            helper_name = node.func.attr
            if helper_name in {"get_by_id", "get_list"}:
                offenders.append(f"{relative_path}:{node.lineno}: {ast.unparse(node)}")
                continue
            if helper_name == "get":
                keyword_names = {
                    keyword.arg for keyword in node.keywords if keyword.arg
                }
                if keyword_names & {"filters", "field_name", "field_value"}:
                    offenders.append(
                        f"{relative_path}:{node.lineno}: {ast.unparse(node)}"
                    )

    return offenders


def _legacy_cache_only_helper_offenders(target_paths: tuple[str, ...]) -> list[str]:
    repo_root = _repo_root()
    offenders: list[str] = []
    removed_helpers = _removed_cache_only_helpers()

    for relative_path in target_paths:
        path = repo_root / relative_path
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative_path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(
                node.func, ast.Attribute
            ):
                continue
            if node.func.attr in removed_helpers:
                offenders.append(f"{relative_path}:{node.lineno}: {ast.unparse(node)}")

    return offenders


def _removed_cache_only_helpers() -> set[str]:
    return {"get_by_id" + "_sync", "get_by_id" + "_cached"}


def test_low_risk_product_async_consumers_use_canonical_query_helpers() -> None:
    target_paths = (
        "workspaces/aware_kernel/modules/storage/ontology/runtime/python/aware_storage/blob_handlers.py",
        "workspaces/aware_kernel/modules/storage/ontology/runtime/python/aware_storage/utils.py",
        "workspaces/aware_network/modules/storage/services/storage/aware_storage_service/api_service_protocol.py",
        "workspaces/aware_network/modules/economy/ontology/runtime/python/aware_economy/canonical/transaction/authority.py",
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/graph/instance/commit/plane_holder.py",
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/graph/instance/orm_persistence.py",
    )
    offenders = _legacy_async_helper_offenders(target_paths)

    assert offenders == []


def test_experience_product_async_consumers_use_canonical_query_helpers() -> None:
    target_paths = (
        "workspaces/aware_network/modules/experience/ontology/runtime/python/aware_experience/program/program_config_impl_loader.py",
        "workspaces/aware_network/modules/experience/ontology/runtime/python/aware_experience/program/program_graph_binding_reader.py",
        "workspaces/aware_network/modules/experience/ontology/runtime/python/aware_experience/program/program_run_receipt_loader.py",
    )
    offenders = _legacy_async_helper_offenders(target_paths)

    assert offenders == []


def test_agent_lane_resolution_uses_canonical_query_helpers() -> None:
    target_paths = (
        "workspaces/aware_agent/modules/agent/runtime/aware_agent/lane_resolution.py",
    )
    offenders = _legacy_async_helper_offenders(target_paths)

    assert offenders == []


def test_identity_legacy_test_helpers_are_absent() -> None:
    target_paths = (
        "workspaces/aware_network/modules/identity/ontology/runtime/python/tests/helper/user_registry.py",
        "workspaces/aware_network/modules/identity/ontology/runtime/python/tests/helper/organization_registry.py",
    )
    repo_root = _repo_root()
    existing_paths = [
        relative_path
        for relative_path in target_paths
        if (repo_root / relative_path).exists()
    ]

    assert existing_paths == []


def test_network_acl_uses_canonical_query_helpers() -> None:
    target_paths = (
        "workspaces/aware_network/modules/network/ontology/runtime/python/aware_network/network/acl.py",
    )
    offenders = _legacy_async_helper_offenders(target_paths)

    assert offenders == []


def test_agent_turn_service_uses_canonical_query_helpers() -> None:
    target_paths = (
        "workspaces/aware_agent/modules/agent/runtime/aware_agent/inference/service/agent_turn_service.py",
    )
    offenders = _legacy_async_helper_offenders(target_paths)

    assert offenders == []


def test_identity_runtime_cache_only_consumers_use_by_id_cached() -> None:
    target_paths = (
        "workspaces/aware_network/modules/identity/ontology/runtime/python/aware_identity/handlers/impl/human/human.py",
        "workspaces/aware_network/modules/identity/ontology/runtime/python/aware_identity/handlers/impl/identity/identity.py",
        "workspaces/aware_network/modules/identity/ontology/runtime/python/aware_identity/handlers/impl/memory/memory_working_attention_frame.py",
        "workspaces/aware_network/modules/identity/ontology/runtime/python/aware_identity/handlers/impl/memory/memory_working_item.py",
        "workspaces/aware_network/modules/identity/ontology/runtime/python/aware_identity/handlers/impl/memory/memory_semantic.py",
        "workspaces/aware_network/modules/identity/ontology/runtime/python/aware_identity/handlers/impl/memory/memory_procedural.py",
        "workspaces/aware_network/modules/identity/ontology/runtime/python/aware_identity/handlers/impl/actor/actor_focus_scope.py",
        "workspaces/aware_network/modules/identity/ontology/runtime/python/aware_identity/handlers/impl/actor/actor.py",
        "workspaces/aware_network/modules/identity/ontology/runtime/python/aware_identity/actor/focus.py",
    )
    offenders = _legacy_cache_only_helper_offenders(target_paths)

    assert offenders == []


def test_kernel_runtime_cache_only_consumers_use_by_id_cached() -> None:
    target_paths = (
        "workspaces/aware_kernel/modules/content/ontology/runtime/python/aware_content/handlers/impl/part/content_part_text_segment.py",
        "workspaces/aware_kernel/modules/content/ontology/runtime/python/aware_content/handlers/impl/part/content_part.py",
        "workspaces/aware_kernel/modules/content/ontology/runtime/python/aware_content/handlers/impl/part/content_part_content.py",
        "workspaces/aware_kernel/modules/content/ontology/runtime/python/aware_content/handlers/impl/part/content_part_text_style.py",
        "workspaces/aware_kernel/modules/content/ontology/runtime/python/aware_content/handlers/impl/part/content_part_text.py",
        "workspaces/aware_kernel/modules/storage/ontology/runtime/python/aware_storage/utils.py",
        "workspaces/aware_kernel/modules/storage/ontology/runtime/python/aware_storage/handlers/impl/blob/storage_blob.py",
        "workspaces/aware_kernel/modules/storage/ontology/runtime/python/aware_storage/handlers/impl/bucket/storage_bucket.py",
        "workspaces/aware_kernel/modules/storage/ontology/runtime/python/aware_storage/blob_handlers.py",
        "workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime/handlers/impl/api/api_capability_endpoint.py",
    )
    offenders = _legacy_cache_only_helper_offenders(target_paths)

    assert offenders == []
