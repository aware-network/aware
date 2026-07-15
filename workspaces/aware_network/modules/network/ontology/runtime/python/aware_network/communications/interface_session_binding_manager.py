"""
Interface session binding manager.

Maintains in-memory bindings for active WebSocket connections originating from
interface clients.

Important: This module is deliberately **graph/ORM agnostic**. Any durable
bindings (audit trail, identity host resolution, etc.) must be produced via the
runtime OIG commit pipeline. The network layer is transport-only.
"""

# @doc-ref: ../../docs/interface_session_binding_manager.md
# @test-ref: ../../tests/test_interface_session_binding_manager.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import ClassVar, Dict, Iterable, List, Optional
from uuid import UUID, NAMESPACE_URL, uuid4, uuid5

from aware_utils.logging import logger

from aware_network.network.node.manager import network_node_manager


@dataclass(slots=True)
class InterfaceSessionBindingContext:
    connection_id: UUID
    interface_id: UUID
    interface_session_id: UUID
    identity_id: UUID
    interface_identity_id: UUID
    interface_identity_network_node_id: UUID
    interface_session_network_binding_id: UUID
    last_seen_at: datetime


class InterfaceSessionBindingManager:
    """Singleton manager used by the node duplex server and router."""

    _instance: ClassVar[Optional["InterfaceSessionBindingManager"]] = None

    def __init__(self) -> None:
        self._bindings: Dict[UUID, InterfaceSessionBindingContext] = {}
        # Reverse index for token-based HTTP auth. The token is a capability
        # scoped to this live websocket binding, not a stable identifier.
        self._bindings_by_session_token: Dict[UUID, InterfaceSessionBindingContext] = {}
        self._namespace = uuid5(NAMESPACE_URL, "aware://interface-session-binding/v1")

    @classmethod
    def instance(cls) -> "InterfaceSessionBindingManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def register_connection(self, *, connection_id: UUID, payload: dict) -> InterfaceSessionBindingContext:
        """Register (or refresh) the binding for a websocket connection.

        This creates deterministic, transport-scoped binding identifiers so
        clients can correlate acknowledgements, without persisting anything to a
        backing store.
        """
        interface_id = UUID(payload["interface_id"])
        session_id = UUID(payload["interface_session_id"])
        identity_id = UUID(payload["identity_id"])

        now = datetime.now(UTC)

        node_id = network_node_manager.hosted_node_id

        interface_identity_id = uuid5(self._namespace, f"interface_identity:{interface_id}:{identity_id}")
        interface_identity_network_node_id = uuid5(
            self._namespace,
            f"interface_identity_network_node:{interface_identity_id}:{node_id}",
        )
        # IMPORTANT: this id doubles as the HTTP bearer token for fetching bundle
        # artifacts (manifest + msgpack). It must be unguessable, so we do NOT
        # derive it deterministically from connection_id.
        #
        # Lifetime: valid only while this websocket binding is active.
        interface_session_network_binding_id = uuid4()

        existing = self._bindings.get(connection_id)
        if existing is not None:
            self._bindings_by_session_token.pop(existing.interface_session_network_binding_id, None)

        context = InterfaceSessionBindingContext(
            connection_id=connection_id,
            interface_id=interface_id,
            interface_session_id=session_id,
            identity_id=identity_id,
            interface_identity_id=interface_identity_id,
            interface_identity_network_node_id=interface_identity_network_node_id,
            interface_session_network_binding_id=interface_session_network_binding_id,
            last_seen_at=now,
        )
        self._bindings[connection_id] = context
        self._bindings_by_session_token[interface_session_network_binding_id] = context
        return context

    async def update_identity(self, *, connection_id: UUID, identity_id: UUID) -> InterfaceSessionBindingContext:
        """Update the identity bound to an active connection without rotating its session token.

        This is used for token-based authentication flows where the connection may be
        registered before an identity is known (e.g. `actor_id=null`), then upgraded
        to an authenticated identity via `token_login`.

        NOTE:
        - The HTTP bearer token (`interface_session_network_binding_id`) is preserved so
          clients do not need a second register round-trip to fetch artifacts.
        - Derived transport identifiers are recomputed deterministically from the new identity.
        """

        context = self._bindings.get(connection_id)
        if context is None:
            raise KeyError(connection_id)

        node_id = network_node_manager.hosted_node_id
        context.identity_id = identity_id
        context.interface_identity_id = uuid5(
            self._namespace,
            f"interface_identity:{context.interface_id}:{identity_id}",
        )
        context.interface_identity_network_node_id = uuid5(
            self._namespace,
            f"interface_identity_network_node:{context.interface_identity_id}:{node_id}",
        )
        context.last_seen_at = datetime.now(UTC)
        return context

    async def record_heartbeat(self, *, connection_id: UUID) -> None:
        context = self._bindings.get(connection_id)
        if context is None:
            logger.warning("Heartbeat received for unknown connection %s", connection_id)
            return

        context.last_seen_at = datetime.now(UTC)

    async def disconnect(self, *, connection_id: UUID) -> None:
        ctx = self._bindings.pop(connection_id, None)
        if ctx is not None:
            self._bindings_by_session_token.pop(ctx.interface_session_network_binding_id, None)

    async def get_binding(self, *, connection_id: UUID) -> Optional[InterfaceSessionBindingContext]:
        return self._bindings.get(connection_id)

    async def get_binding_by_session_token(self, *, session_token: UUID) -> Optional[InterfaceSessionBindingContext]:
        return self._bindings_by_session_token.get(session_token)

    async def get_active_bindings_for_identity(self, identity_id: UUID) -> List[InterfaceSessionBindingContext]:
        return [ctx for ctx in self._bindings.values() if ctx.identity_id == identity_id]

    async def iter_active_bindings(self) -> Iterable[InterfaceSessionBindingContext]:
        return list(self._bindings.values())
