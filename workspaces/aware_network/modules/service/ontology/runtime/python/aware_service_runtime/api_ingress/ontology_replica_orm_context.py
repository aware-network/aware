from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID


class ServiceOntologyReplicaOrmSessionProtocol(Protocol):
    skip_db: bool

    @property
    def branch_id(self) -> UUID: ...

    async def execute_query_spec(
        self,
        *,
        sql_metadata: Any,
        query_spec: Any,
        source_class_fqn: str | None,
        count: bool = False,
    ) -> list[dict[str, object]]: ...

    def imap_get(self, cls: type[Any], obj_id: UUID) -> Any | None: ...

    def imap_add(self, instance: object) -> None: ...

    def log_read(self, model_cls: type[Any], obj_id: UUID) -> None: ...

    def _deserialize_to_model(
        self,
        model_class: type[Any],
        row_data: dict[str, object],
    ) -> Any: ...

    def add_insert(self, sql: str, params: tuple[object, ...]) -> None: ...

    def add_update(self, sql: str, params: tuple[object, ...]) -> None: ...

    def add_delete(self, sql: str, params: tuple[object, ...]) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


def current_service_ontology_replica_orm_session() -> (
    ServiceOntologyReplicaOrmSessionProtocol | None
):
    from aware_service_runtime.api_ingress.host_context import (
        current_service_api_host_context,
    )

    host_context = current_service_api_host_context()
    if host_context is None:
        return None
    return host_context.ontology_replica_orm_session


def require_service_ontology_replica_orm_session() -> (
    ServiceOntologyReplicaOrmSessionProtocol
):
    session = current_service_ontology_replica_orm_session()
    if session is None:
        raise RuntimeError(
            "Service ontology replica ORM session requires an active Service API "
            "host context with ontology replica ORM projection configured."
        )
    return session


__all__ = [
    "ServiceOntologyReplicaOrmSessionProtocol",
    "current_service_ontology_replica_orm_session",
    "require_service_ontology_replica_orm_session",
]
