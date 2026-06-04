"""Testing utilities for ORM operations without database dependency."""

from __future__ import annotations
import os
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from urllib.parse import urlparse, urlunparse
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from aware_orm.session.session import Session

from aware_orm.session.session_context import SessionContext


class TestSessionContext(SessionContext):
    """Minimal SessionContext implementation for testing."""

    def __init__(self, session: "Session", branch_id: UUID | None = None):
        self._session = session
        self._branch_id = branch_id or uuid4()

    @property
    def session(self) -> "Session":
        return self._session

    def set_session(self, new_session: "Session") -> "TestSessionContext":
        """Create a new TestSessionContext with the given session."""
        return TestSessionContext(new_session, self._branch_id)

    @property
    def branch_id(self) -> UUID:
        return self._branch_id


# Create a test-specific context variable
_test_ctx: ContextVar[TestSessionContext] = ContextVar("_test_ctx")


@contextmanager
def set_test_session_context(context: TestSessionContext):
    """Temporarily set a test session context."""
    token = _test_ctx.set(context)
    try:
        yield context
    finally:
        _test_ctx.reset(token)


def get_test_session_context() -> TestSessionContext:
    """Get current test session context."""
    try:
        return _test_ctx.get()
    except LookupError:
        raise RuntimeError("No test session context active. Use within test_session() or scratch_test_session()")


@asynccontextmanager
async def isolated_test_session():
    """
    Create a completely isolated test session that bypasses all context systems.

    This is the simplest form - just creates a session and ensures ORM operations
    work without any context dependencies.

    Usage:
        async with isolated_test_session() as session:
            # Direct session operations
            repo = await Repository.build(...)
            # Session is automatically available to ORM operations
    """
    from aware_orm.session.session import Session
    from aware_orm.session import current_session_ctx

    # Create isolated session
    session = Session(connection=None, skip_db=True)
    test_context = TestSessionContext(session)

    # Override the current_session function globally during this context
    original_functions = {
        "current_session": current_session_ctx.current_session,
        "current_session_context": current_session_ctx.current_session_context,
        "current_branch_id": current_session_ctx.current_branch_id,
    }

    def mock_current_session():
        return session

    def mock_current_session_context():
        return test_context

    def mock_current_branch_id(kind="any"):
        return test_context.branch_id

    # Apply overrides
    current_session_ctx.current_session = mock_current_session
    current_session_ctx.current_session_context = mock_current_session_context
    current_session_ctx.current_branch_id = mock_current_branch_id

    try:
        yield session
    finally:
        # Restore original functions
        for name, func in original_functions.items():
            setattr(current_session_ctx, name, func)


@asynccontextmanager
async def test_session():
    """
    Create a test session context for offline ORM operations.

    This creates a session that queues operations but doesn't execute them
    against a real database. Perfect for testing repository operations.

    Usage:
        async with test_session():
            repo = await Repository.build(...)
            change = await repo.update_from_file_changes()
            # All operations are queued but not executed
    """
    async with isolated_test_session() as session:
        yield session


@asynccontextmanager
async def scratch_test_session():
    """
    Create a scratch test session that automatically rolls back.

    This is similar to scratch_uow but designed for testing without
    requiring a live runtime context.

    Usage:
        async with scratch_test_session():
            # All operations are sandboxed and automatically rolled back
            repo = await Repository.build(...)
            change = await repo.update_from_file_changes()
    """
    async with isolated_test_session() as session:
        # All operations are automatically isolated and "rolled back"
        # when the context exits since skip_db=True
        yield session


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _replace_db_name(database_url: str, db_name: str) -> str:
    parsed = urlparse(database_url)
    path = f"/{db_name}"
    return urlunparse(parsed._replace(path=path))


@asynccontextmanager
async def db_test_database(
    *,
    admin_url: str | None = None,
    db_name: str | None = None,
    drop_on_exit: bool = True,
):
    """Create a temporary Postgres database for DB-backed ORM/runtime tests.

    The admin URL must point to a database with privileges to CREATE/DROP DATABASE.
    """
    admin_url = admin_url or os.getenv("AWARE_DB_TEST_ADMIN_URL") or os.getenv("AWARE_DB_TEST_URL")
    if not admin_url:
        bootstrap_url = os.getenv("AWARE_DB_TEST_BOOTSTRAP_URL") or os.getenv("AWARE_DB_TEST_URL")
        if bootstrap_url and os.getenv("AWARE_DB_TEST_BOOTSTRAP"):
            from aware_orm.bootstrap.postgres import ensure_postgres_container_for_url

            ensure_postgres_container_for_url(bootstrap_url)
            admin_url = _replace_db_name(bootstrap_url, "postgres")
    if not admin_url:
        raise RuntimeError("db_test_database requires AWARE_DB_TEST_ADMIN_URL (or pass admin_url explicitly).")

    try:
        import asyncpg  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("asyncpg is required for db_test_database") from exc

    db_name = db_name or f"aware_test_{uuid4().hex}"
    database_url = _replace_db_name(admin_url, db_name)

    conn = await asyncpg.connect(admin_url)
    try:
        await conn.execute(f"CREATE DATABASE {_quote_ident(db_name)};")
    finally:
        await conn.close()

    try:
        yield database_url
    finally:
        if not drop_on_exit:
            return
        conn = await asyncpg.connect(admin_url)
        try:
            await conn.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = $1 AND pid <> pg_backend_pid();",
                db_name,
            )
            await conn.execute(f"DROP DATABASE IF EXISTS {_quote_ident(db_name)};")
        finally:
            await conn.close()
