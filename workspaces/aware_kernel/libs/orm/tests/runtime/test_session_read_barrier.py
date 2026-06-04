from __future__ import annotations

import pytest

from aware_orm.session.execution_guard import scoped_execution_mode
from aware_orm.session.session import Session


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
