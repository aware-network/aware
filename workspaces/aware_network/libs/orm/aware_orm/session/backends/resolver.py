"""
Backend resolver driven by environment configuration.
"""

from __future__ import annotations

import os
from typing import Protocol

from aware_orm._support import logger

from .database import DatabasePersistenceBackend
from .fs_backend import FsPersistenceBackend
from .noop_backend import NoopPersistenceBackend
from .protocol import PersistenceBackendProtocol, SessionBackendState
from .sqlite_backend import SqlitePersistenceBackend, SqlitePersistenceConfig


class SessionResolverState(SessionBackendState, Protocol):
    """Session surface required by backend resolution."""

    sqlite_backend_config: SqlitePersistenceConfig | None


def resolve_backend(session: SessionResolverState, backend_name: str | None = None) -> PersistenceBackendProtocol:
    """
    Resolve the persistence backend for the provided session.

    Args:
        session: Session instance requesting the backend.
        backend_name: Optional explicit backend name; otherwise read from env.

    Returns:
        PersistenceBackendProtocol implementation.
    """
    explicit = (backend_name or "").strip().lower()
    if explicit == "sqlite":
        config = session.sqlite_backend_config
        if config is None:
            raise ValueError(
                "Explicit sqlite backend requires sqlite_backend_config "
                "(database_path, registry_path, environment_id)."
            )
        session.skip_db = False
        setattr(session, "_backend_name", "sqlite")
        logger.debug("Using sqlite persistence backend")
        return SqlitePersistenceBackend(session, config=config)

    configured = os.getenv("AWARE_PERSISTENCE_BACKEND", "")
    name = configured.strip().lower()
    if explicit:
        name = explicit
    if not name:
        name = "noop" if session.skip_db else "db"

    if name == "db":
        logger.debug("Using database persistence backend")
        setattr(session, "_backend_name", "db")
        return DatabasePersistenceBackend(session)

    if name == "noop":
        logger.debug("Using noop persistence backend (skip_db=True)")
        setattr(session, "_backend_name", "noop")
        return NoopPersistenceBackend(session)

    if name == "fs":
        logger.debug("Using filesystem persistence backend")
        session.skip_db = False  # ensure ORM paths operate normally
        setattr(session, "_backend_name", "fs")
        return FsPersistenceBackend(session)

    raise ValueError(f"Unknown persistence backend: {name}")
