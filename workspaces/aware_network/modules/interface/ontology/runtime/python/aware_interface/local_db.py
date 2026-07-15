from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast
from uuid import UUID

from aware_orm.session.backends import SqlitePersistenceConfig
from aware_orm.session.session import Session as ORMSession


class _QuerySession(Protocol):
    connection: object | None

    async def execute_query(self, sql: str, *params: object) -> list[dict[str, object]]: ...


@dataclass(frozen=True, slots=True)
class InterfaceLocalDbConfig:
    registry_path: Path
    environment_id: UUID
    database_path: Path | str

    def sqlite_config(self) -> SqlitePersistenceConfig:
        return SqlitePersistenceConfig(
            database_path=self.database_path,
            registry_path=self.registry_path,
            environment_id=self.environment_id,
        )


class InterfaceLocalDb:
    """Module-owned local DB handle for the interface backend.

    This surface intentionally stays narrow:
    - explicit registry-backed sqlite config in
    - canonical ORM sqlite session factory out
    - no host-side SQL root discovery
    """

    _config: InterfaceLocalDbConfig
    _sqlite_config: SqlitePersistenceConfig

    def __init__(self, *, config: InterfaceLocalDbConfig) -> None:
        self._config = config
        self._sqlite_config = config.sqlite_config()

    @property
    def config(self) -> InterfaceLocalDbConfig:
        return self._config

    @property
    def database_target(self) -> str:
        return self._sqlite_config.database_target()

    @property
    def resolved_registry_path(self) -> Path:
        return self._sqlite_config.resolved_registry_path()

    def new_session(self) -> ORMSession:
        return ORMSession(
            skip_db=False,
            backend_name="sqlite",
            sqlite_backend_config=self._sqlite_config,
        )

    async def ensure_ready(self) -> None:
        _ = await self.list_tables()

    async def list_tables(self) -> tuple[str, ...]:
        rows = await self.execute_query(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = $1
            ORDER BY name
            """,
            "table",
        )
        tables: list[str] = []
        for row in rows:
            name = str(row.get("name") or "").strip()
            if not name:
                continue
            tables.append(name)
        return tuple(tables)

    async def table_exists(self, table_name: str) -> bool:
        rows = await self.execute_query(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = $1 AND name = $2
            LIMIT 1
            """,
            "table",
            table_name,
        )
        return bool(rows)

    async def execute_query(self, sql: str, *params: object) -> list[dict[str, object]]:
        orm_session = cast(_QuerySession, self.new_session())
        try:
            rows = await orm_session.execute_query(sql, *params)
            normalized_rows: list[dict[str, object]] = []
            for row in rows:
                normalized_rows.append({str(key): value for key, value in row.items()})
            return normalized_rows
        finally:
            self.close_session(cast(ORMSession, orm_session))

    @staticmethod
    def close_session(orm_session: ORMSession) -> None:
        connection = orm_session.connection
        if isinstance(connection, sqlite3.Connection):
            connection.close()
            orm_session.connection = None


__all__ = [
    "InterfaceLocalDb",
    "InterfaceLocalDbConfig",
]
