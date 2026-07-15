"""Collection of duplex (bidirectional) connections for a service app."""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field

from aware_comms.duplex.base import DuplexBase, DuplexSide
from aware_comms.duplex.websocket.registry import ws_registry

logger = logging.getLogger(__name__)


@runtime_checkable
class ServerRegisterable(Protocol):
    def register(self) -> APIRouter: ...


class DuplexCollection(BaseModel):
    """Mapping of supported duplex handlers for a given app."""

    duplex_list: dict[tuple[str, DuplexSide], DuplexBase[object, object]] = Field(
        default_factory=dict
    )

    def register_duplex(self, duplex: DuplexBase[object, object]) -> None:
        key = (
            (
                duplex.client_type
                if duplex.side == DuplexSide.SERVER
                else duplex.server_type
            ),
            duplex.side,
        )
        logger.info("Registering duplex: %s -> %s", key, type(duplex).__name__)
        self.duplex_list[key] = duplex

    def validate_duplex_managers(self, app_type: str) -> None:
        seen: set[tuple[type, str, str]] = set()
        for duplex in self.duplex_list.values():
            key = (type(duplex), duplex.client_type, duplex.server_type)
            if key in seen:
                raise ValueError(f"Duplicate duplex instance found for {app_type}")
            seen.add(key)

        expected_incoming_clients = ws_registry.get_valid_connections(
            app_type, as_client=True
        )
        expected_outgoing_servers = ws_registry.get_valid_connections(
            app_type, as_client=False
        )

        for client_app in expected_incoming_clients:
            if (client_app, DuplexSide.SERVER) not in self.duplex_list:
                raise ValueError(
                    f"Missing server duplex instance for connection {client_app} -> {app_type}"
                )

        for server_app in expected_outgoing_servers:
            if (server_app, DuplexSide.CLIENT) not in self.duplex_list:
                raise ValueError(
                    f"Missing client duplex instance for connection {app_type} -> {server_app}"
                )

        for (target_app, side), duplex in self.duplex_list.items():
            if side == DuplexSide.SERVER:
                if target_app not in expected_incoming_clients:
                    raise ValueError(
                        f"Unexpected server duplex instance found for {target_app} -> {app_type}"
                    )
                if not (
                    duplex.server_type == app_type and duplex.client_type == target_app
                ):
                    message = (
                        f"Invalid server configuration for {target_app} -> {app_type}. Expected "
                        f"client={target_app}, server={app_type}"
                    )
                    raise ValueError(message)
            elif side == DuplexSide.CLIENT:
                if target_app not in expected_outgoing_servers:
                    raise ValueError(
                        f"Unexpected client duplex instance found for {app_type} -> {target_app}"
                    )
                if not (
                    duplex.client_type == app_type and duplex.server_type == target_app
                ):
                    message = (
                        f"Invalid client configuration for {app_type} -> {target_app}. Expected "
                        f"client={app_type}, server={target_app}"
                    )
                    raise ValueError(message)
            else:
                raise ValueError(f"Unknown duplex side: {side}")

    def register(self, app_type: str) -> list[APIRouter]:
        self.validate_duplex_managers(app_type)

        api_routers: list[APIRouter] = []
        for (_target_app, side), duplex in self.duplex_list.items():
            if side == DuplexSide.SERVER and isinstance(duplex, ServerRegisterable):
                api_routers.append(duplex.register())
        return api_routers

    def get_client(self, server_app_type: str):
        return self.duplex_list.get((server_app_type, DuplexSide.CLIENT))

    def get_server(self, client_app_type: str):
        return self.duplex_list.get((client_app_type, DuplexSide.SERVER))

    def get_duplex(self, app_type: str, side: DuplexSide):
        return self.duplex_list.get((app_type, side))

    def get_ws_connection(self, connection_id: UUID):
        for duplex in self.duplex_list.values():
            connection = duplex.get_ws_connection(connection_id)
            if connection:
                return duplex
        return None

    def get_wrtc_connection(self, connection_id: UUID):
        for duplex in self.duplex_list.values():
            connection = duplex.get_wrtc_connection(connection_id)
            if connection:
                return duplex
        return None


__all__ = ["DuplexCollection"]
