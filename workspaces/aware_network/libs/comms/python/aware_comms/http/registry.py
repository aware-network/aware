from __future__ import annotations

import logging
from typing import Protocol

from pydantic import BaseModel

from aware_comms.http.endpoint import (
    HttpEndpointMetadata,
    HttpRouteKey,
    HttpRouteMetadata,
)

logger = logging.getLogger(__name__)


class HttpServerLike(Protocol):
    app_type: str
    route_metadata: list[HttpRouteMetadata]


class HttpEndpointRegistry:
    """Registry of HTTP endpoints for all service apps."""

    def __init__(self) -> None:
        self.servers: list[HttpServerLike] = []
        self._server_map: dict[str, HttpServerLike] = {}

    def get_server(self, app_type: str) -> HttpServerLike | None:
        logger.debug("Getting server for %s", app_type)
        return self._server_map.get(app_type)

    def register_server(self, server: HttpServerLike) -> None:
        self.validate_unique_request_models()
        self.servers.append(server)
        self._server_map[server.app_type] = server

    def validate_unique_request_models(self) -> None:
        for server in self.servers:
            request_models: list[type[BaseModel]] = []
            for route in server.route_metadata:
                for endpoint in route.endpoint_list:
                    if endpoint.request_model in request_models:
                        raise ValueError(
                            f"Duplicate request model found in app {server.app_type}: {endpoint.request_model.__name__}"
                        )
                    request_models.append(endpoint.request_model)

    def get_app_routes(self, app_type: str) -> list[HttpRouteMetadata] | None:
        server = self.get_server(app_type)
        if server is None:
            return None
        return server.route_metadata

    def get_endpoint_metadata(
        self,
        app_type: str,
        route_type: HttpRouteKey,
        request_model: type[BaseModel],
    ) -> HttpEndpointMetadata:
        endpoints_metadata = self.get_endpoints_metadata(app_type, route_type)
        for endpoint_metadata in endpoints_metadata:
            if endpoint_metadata.request_model == request_model:
                return endpoint_metadata
        raise ValueError(
            f"No endpoint found for app={app_type}, route_type={route_type}, request={request_model}"
        )

    def get_endpoints_metadata(
        self, app_type: str, route_type: HttpRouteKey
    ) -> list[HttpEndpointMetadata]:
        route_metadatas = self.get_app_routes(app_type)
        if route_metadatas is None:
            raise ValueError(f"No routes found for app={app_type}")

        for route_metadata in route_metadatas:
            if route_metadata.route_type == route_type:
                return route_metadata.endpoint_list
        raise ValueError(f"No route found for app={app_type}, route_type={route_type}")


http_registry = HttpEndpointRegistry()

__all__ = ["HttpEndpointRegistry", "http_registry"]
