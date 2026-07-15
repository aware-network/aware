from __future__ import annotations

import os

import pytest

from aware_orm.session.session import Session
from aware_orm.testing import db_test_database


def _skip_if_db_unavailable() -> str | None:
    if os.getenv("AWARE_DB_TEST_ADMIN_URL") or os.getenv("AWARE_DB_TEST_URL"):
        return None
    return "AWARE_DB_TEST_ADMIN_URL or AWARE_DB_TEST_URL is required for Postgres runtime proof."


@pytest.mark.asyncio
@pytest.mark.db
async def test_postgres_session_runtime_commit_query_update_and_delete() -> None:
    reason = _skip_if_db_unavailable()
    if reason:
        pytest.skip(reason)

    asyncpg = pytest.importorskip("asyncpg")

    async with db_test_database() as db_url:
        conn = await asyncpg.connect(db_url)
        try:
            await conn.execute("CREATE SCHEMA ci_runtime;")
            await conn.execute(
                """
CREATE TABLE ci_runtime.events (
  id TEXT PRIMARY KEY NOT NULL,
  status TEXT NOT NULL,
  total INTEGER NOT NULL
);
""".strip()
            )

            session = Session(connection=conn, skip_db=False, backend_name="db")
            session.add_insert(
                "INSERT INTO ci_runtime.events(id, status, total) VALUES($1, $2, $3)",
                ("evt-1", "open", 10),
            )
            await session.commit()

            rows = await session.execute_query(
                "SELECT id, status, total FROM ci_runtime.events WHERE status = $1",
                "open",
            )
            assert rows == [{"id": "evt-1", "status": "open", "total": 10}]

            session.add_update(
                "UPDATE ci_runtime.events SET status = $1, total = $2 WHERE id = $3",
                ("closed", 15, "evt-1"),
            )
            await session.commit()

            updated = await session.execute_query(
                "SELECT id, status, total FROM ci_runtime.events WHERE id = $1",
                "evt-1",
            )
            assert updated == [{"id": "evt-1", "status": "closed", "total": 15}]

            session.add_delete("DELETE FROM ci_runtime.events WHERE id = $1", ("evt-1",))
            await session.commit()
            assert await session.execute_query("SELECT id FROM ci_runtime.events") == []
        finally:
            await conn.close()
