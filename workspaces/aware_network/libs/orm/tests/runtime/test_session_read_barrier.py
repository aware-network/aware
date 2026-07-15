from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel, ValidationError

from aware_orm.models.base_model import BaseORMModel
from aware_orm.runtime.sql_metadata import SQLRuntimeMetadata
from aware_orm.session.execution_guard import scoped_execution_mode
from aware_orm.session.session import Session


class RequiredRelationship(BaseModel):
    name: str


class StrictReadModel(BaseORMModel):
    name: str
    related: RequiredRelationship
    related_id: UUID | None = None


class RecordingBackend:
    name = "db"

    def __init__(self) -> None:
        self.read_calls: list[tuple[str, tuple[object, ...]]] = []

    async def execute_read(self, sql: str, params: tuple[object, ...]):
        self.read_calls.append((sql, params))
        return [{"ok": True}]


@pytest.mark.asyncio
async def test_execute_query_rejects_db_reads_inside_write_execution_mode() -> None:
    backend = RecordingBackend()
    session = Session(skip_db=False, backend=backend)

    with scoped_execution_mode("write"):
        with pytest.raises(PermissionError, match="DB/GraphSQL reads are not allowed"):
            await session.execute_query("SELECT 1")

    assert backend.read_calls == []


@pytest.mark.asyncio
async def test_execute_query_allows_reads_outside_write_execution_mode() -> None:
    backend = RecordingBackend()
    session = Session(skip_db=False, backend=backend)

    rows = await session.execute_query("SELECT $1", "value")

    assert rows == [{"ok": True}]
    assert backend.read_calls == [("SELECT $1", ("value",))]


@pytest.mark.asyncio
async def test_execute_query_propagates_read_guard_failures(monkeypatch) -> None:
    from aware_orm.session import execution_guard

    backend = RecordingBackend()
    session = Session(skip_db=False, backend=backend)

    def fail_guard() -> str:
        raise RuntimeError("read guard failed")

    monkeypatch.setattr(execution_guard, "current_execution_mode", fail_guard)

    with pytest.raises(RuntimeError, match="read guard failed"):
        await session.execute_query("SELECT 1")

    assert backend.read_calls == []


def test_deserialize_to_model_propagates_missing_required_relationship_validation() -> (
    None
):
    StrictReadModel._sql_runtime_metadata = SQLRuntimeMetadata(  # type: ignore[assignment]
        class_config_id=uuid4(),
        table_schema="public",
        table_name="strict_read_model",
        column_by_attribute={
            "name": "name",
            "related_id": "related_id",
        },
        persisted_attributes=frozenset({"id", "name", "related_id"}),
        fk_owner_by_attribute={},
        fk_columns_by_attribute={},
        join_chain_by_attribute={},
    )
    session = Session(skip_db=False, backend=RecordingBackend())
    row_id = uuid4()
    related_id = uuid4()

    with pytest.raises(ValidationError) as exc_info:
        session._deserialize_to_model(
            StrictReadModel,
            {
                "id": str(row_id),
                "name": "owner",
                "related_id": str(related_id),
            },
        )

    assert any(
        error.get("type") == "missing" and error.get("loc") == ("related",)
        for error in exc_info.value.errors()
    )
