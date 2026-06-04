# @code-under-test: ../../aware_orm/session/session.py
# @code-under-test: ../../aware_orm/session/backends/database.py
# @code-under-test: ../../aware_orm/session/backends/noop_backend.py

from types import SimpleNamespace

import pytest

from aware_orm.session.session import Session
from aware_orm.session.backends import (
    DatabasePersistenceBackend,
    NoopPersistenceBackend,
)


class FakeRecord(dict):
    """Simple dict subclass so dict(record) yields a copy like asyncpg.Record."""


class FakeTransaction:
    """Async context manager mimicking asyncpg transaction."""

    def __init__(self, connection):
        self.connection = connection

    async def __aenter__(self):
        self.connection.tx_entered += 1
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.connection.tx_exited += 1


class FakeConnection:
    """Minimal async connection implementation for backend testing."""

    def __init__(self):
        self.fetch_calls = []
        self.exec_calls = []
        self.tx_entered = 0
        self.tx_exited = 0
        self._fetch_result = []

    def prime_fetch(self, rows):
        self._fetch_result = rows

    async def fetch(self, sql, *params):
        self.fetch_calls.append((sql, params))
        return self._fetch_result

    async def execute(self, sql, *params):
        self.exec_calls.append(("execute", sql, params))

    async def executemany(self, sql, params_list):
        # Store a list copy so assertions can inspect values.
        self.exec_calls.append(("executemany", sql, list(params_list)))

    def transaction(self):
        return FakeTransaction(self)


class FakeAsyncpgConnection(FakeConnection):
    """Fake asyncpg connection that tracks set_type_codec calls."""

    def __init__(self):
        super().__init__()
        self.type_codec_calls = []
        self.call_order = []

    async def set_type_codec(self, typename, *, encoder, decoder, schema):  # matches asyncpg kw-only
        self.type_codec_calls.append((typename, encoder, decoder, schema))
        self.call_order.append(("codec", typename))

    async def fetch(self, sql, *params):
        self.call_order.append(("fetch", sql))
        return await super().fetch(sql, *params)

    async def execute(self, sql, *params):
        self.call_order.append(("execute", sql))
        return await super().execute(sql, *params)

    async def executemany(self, sql, params_list):
        self.call_order.append(("executemany", sql))
        return await super().executemany(sql, params_list)

    async def close(self):
        self.call_order.append(("close", None))


@pytest.mark.asyncio
async def test_database_backend_commit_with_connection():
    session = Session(skip_db=False)
    backend = DatabasePersistenceBackend(session)
    session._backend = backend  # ensure Session helpers target our backend

    connection = FakeConnection()
    session.connection = connection

    session.add_delete("DELETE FROM meta.object WHERE id = $1", ("dead",))
    session.add_insert("INSERT INTO meta.object(id, name) VALUES($1, $2)", ("new-id", "demo"))
    session.add_update("UPDATE meta.object SET name = $1 WHERE id = $2", ("updated", "new-id"))

    connection.prime_fetch([FakeRecord({"id": "new-id"})])
    rows = await backend.execute_read("SELECT * FROM meta.object", tuple())
    assert rows == [{"id": "new-id"}]
    assert connection.fetch_calls == [("SELECT * FROM meta.object", tuple())]

    await backend.commit()

    # DELETE executes first, then INSERT, then UPDATE
    expected = [
        ("execute", "DELETE FROM meta.object WHERE id = $1", ("dead",)),
        (
            "execute",
            "INSERT INTO meta.object(id, name) VALUES($1, $2)",
            ("new-id", "demo"),
        ),
        (
            "execute",
            "UPDATE meta.object SET name = $1 WHERE id = $2",
            ("updated", "new-id"),
        ),
    ]
    assert connection.exec_calls == expected
    assert connection.tx_entered == 1
    assert connection.tx_exited == 1
    assert session._pending_inserts == []
    assert session._pending_updates == []
    assert session._pending_deletes == []


@pytest.mark.asyncio
async def test_database_backend_skip_db_leaves_queue_untouched():
    session = Session(skip_db=True)
    backend = DatabasePersistenceBackend(session)

    session.add_insert("INSERT INTO meta.object(id) VALUES($1)", ("queued",))
    assert backend.has_pending_operations() is True

    await backend.commit()
    # skip_db=True means commit is a no-op and operations remain for offline inspection
    assert session._pending_inserts == [("INSERT INTO meta.object(id) VALUES($1)", ("queued",))]


@pytest.mark.asyncio
async def test_noop_backend_captures_operations_and_rolls_back():
    session = Session(skip_db=True)
    backend = NoopPersistenceBackend(session)

    backend.enqueue_insert("INSERT INTO demo.table(id) VALUES($1)", ("noop",))
    backend.enqueue_update("UPDATE demo.table SET name = $1 WHERE id = $2", ("noop-name", "noop"))
    backend.enqueue_delete("DELETE FROM demo.table WHERE id = $1", ("noop",))

    result = await backend.execute_read("SELECT * FROM demo.table", tuple())
    assert result == []

    # Commit is a no-op for skip-db sessions
    await backend.commit()
    assert backend.has_pending_operations() is True

    await backend.rollback()
    assert backend.has_pending_operations() is False
    assert session._pending_inserts == []
    assert session._pending_updates == []
    assert session._pending_deletes == []


@pytest.mark.asyncio
async def test_database_backend_asyncpg_installs_json_codecs(monkeypatch):
    from aware_code.types.json import JsonObject
    from aware_orm.session.backends import database as db_backend

    session = Session(skip_db=False)
    backend = DatabasePersistenceBackend(session)
    session._backend = backend

    fake_conn = FakeAsyncpgConnection()

    async def _fake_connect(_url):
        return fake_conn

    monkeypatch.setenv("DATABASE_URL", "postgresql://example.invalid/db")
    monkeypatch.setattr(db_backend, "asyncpg", SimpleNamespace(connect=_fake_connect))

    session.add_insert("INSERT INTO demo.table(data) VALUES($1)", (JsonObject({}),))
    await backend.commit()

    assert [t for (t, _, _, _) in fake_conn.type_codec_calls] == ["json", "jsonb"]
    assert fake_conn.call_order[:2] == [("codec", "json"), ("codec", "jsonb")]
