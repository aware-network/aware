from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel, StrictStr

from aware_comms.http.endpoint import HttpRouteKey, HttpRouteMetadata
from aware_comms.http.file.router import FileRouter
from aware_comms.http.router import HttpModelRouter

logger = logging.getLogger(__name__)


class HttpServerConfig(BaseModel):
    requires_auth: bool
    requires_file_operations: bool = False


class HttpServer(BaseModel):
    """Http Server that manages http routers by route type."""

    app_type: StrictStr
    config: HttpServerConfig
    route_metadata: list[HttpRouteMetadata]
    routers: dict[HttpRouteKey, HttpModelRouter]
    file_router: FileRouter | None = None

    def get_router(self, router_type: HttpRouteKey) -> HttpModelRouter:
        return self.routers[router_type]

    def validate_routers(self) -> None:
        from aware_comms.http.registry import http_registry

        app_routes = http_registry.get_app_routes(self.app_type)
        if app_routes is None:
            if len(self.routers.keys()) == 0:
                logger.info(
                    "No http routes for app=%s, skipping validation.", self.app_type
                )
                return
            raise ValueError(f"No routes found for app={self.app_type}")

        router_types = [route.route_type for route in app_routes]
        logger.info(
            "Validating mandatory routers: %s",
            ", ".join(router_types),
        )
        for router_type in router_types:
            try:
                router = self.get_router(router_type)
            except KeyError:
                raise ValueError(
                    f"Router for route type {router_type} not registered"
                ) from None
            try:
                router.validate_endpoints(self.app_type)
            except ValueError as exc:
                raise ValueError(
                    f"App {self.app_type} router {router_type} failed validation: {exc}"
                ) from exc

    def register(self) -> list[APIRouter]:
        server_config = self.config
        api_routers: list[APIRouter] = []
        for route in self.route_metadata:
            try:
                router = self.get_router(route.route_type)
            except KeyError:
                raise ValueError(
                    f"Router for route type {route.route_type} not registered"
                ) from None
            api_routers.append(
                router.register(
                    app_type=self.app_type,
                    server_requires_auth=server_config.requires_auth,
                )
            )

        if server_config.requires_file_operations:
            if self.file_router is None:
                raise ValueError(
                    f"Server {self.app_type} requires file operations but no file router is registered"
                )
            api_routers.append(self.file_router.register())
        return api_routers


__all__ = ["HttpServer", "HttpServerConfig"]
