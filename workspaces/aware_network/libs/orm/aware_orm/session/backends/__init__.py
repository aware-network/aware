"""Persistence backend registry for ORM sessions."""

from .protocol import PersistenceBackendProtocol, QuerySpecBackendProtocol, QueryResult
from .database import DatabasePersistenceBackend
from .noop_backend import NoopPersistenceBackend
from .sqlite_backend import SqlitePersistenceBackend, SqlitePersistenceConfig
from .resolver import resolve_backend

__all__ = [
    "PersistenceBackendProtocol",
    "QuerySpecBackendProtocol",
    "QueryResult",
    "DatabasePersistenceBackend",
    "NoopPersistenceBackend",
    "SqlitePersistenceBackend",
    "SqlitePersistenceConfig",
    "resolve_backend",
]
