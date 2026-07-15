from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Annotated
from typing import cast
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel

from aware_comms.http import utils as http_utils
from aware_comms.http.endpoint import (
    HttpEndpointAuthCallback,
    HttpEndpointCallback,
    HttpEndpointHandler,
    HttpEndpointMetadata,
    HttpRouteKey,
)

logger = logging.getLogger(__name__)


class HttpModelRouter(BaseModel):
    """Base router for handling HTTP endpoints for a route group."""

    route_type: HttpRouteKey
    handlers: dict[type[BaseModel], HttpEndpointHandler]

    def _create_endpoint_handler(
        self, endpoint_metadata: HttpEndpointMetadata, server_requires_auth: bool
    ) -> Callable[..., Awaitable[BaseModel]]:
        if server_requires_auth and endpoint_metadata.requires_auth:

            async def handler_with_auth(
                request_data: Annotated[dict[str, object], Body()],
                user_id: Annotated[UUID, Depends(http_utils.get_current_user_id)],
            ) -> BaseModel:
                request = endpoint_metadata.request_model.model_validate(request_data)
                return await self._handle_request(request, user_id)

            return handler_with_auth

        async def handler(
            request_data: Annotated[dict[str, object], Body()],
        ) -> BaseModel:
            request = endpoint_metadata.request_model.model_validate(request_data)
            return await self._handle_request(request)

        return handler

    async def _handle_request(
        self, request: BaseModel, user_id: UUID | None = None
    ) -> BaseModel:
        request_type = type(request)
        handler = self.handlers.get(request_type)
        if not handler:
            request_dict = {
                "type": request_type.__name__,
                "dict": (
                    request.model_dump()
                    if hasattr(request, "model_dump")
                    else str(request)
                ),
            }
            logger.error("No handler found. Request debug info: %s", request_dict)
            raise HTTPException(
                status_code=400,
                detail=(
                    f"No handler found for request of type: {request_type.__name__}. "
                    f"Available handlers: {[h.__name__ for h in self.handlers.keys()]}"
                ),
            )
        if user_id is None:
            callback = cast(HttpEndpointCallback, handler.callback)
            return await callback(request)
        callback = cast(HttpEndpointAuthCallback, handler.callback)
        return await callback(request, user_id)

    def validate_endpoints(self, app_type: str) -> None:
        from aware_comms.http.registry import http_registry

        mandatory_endpoint_types = http_registry.get_endpoints_metadata(
            app_type=app_type, route_type=self.route_type
        )

        request_types = self.handlers.keys()
        for endpoint_metadata in mandatory_endpoint_types:
            if endpoint_metadata.request_model not in request_types:
                raise ValueError(
                    f"No handler found for mandatory request type: {endpoint_metadata.request_model}"
                )

        for handler_request_type, handler in self.handlers.items():
            endpoint_metadata = http_registry.get_endpoint_metadata(
                app_type=app_type,
                route_type=self.route_type,
                request_model=handler_request_type,
            )
            request_type, response_type = handler.get_request_and_response_types()
            if handler_request_type != request_type:
                raise ValueError(
                    f"Wrong key/value at handler mapping: {handler_request_type} != {request_type}"
                )
            if endpoint_metadata.request_model != request_type:
                raise ValueError(
                    f"Request model for {request_type} does not match registry: {endpoint_metadata.request_model} != {request_type}"
                )
            if endpoint_metadata.response_model != response_type:
                raise ValueError(
                    f"Response model for {request_type} does not match registry: {endpoint_metadata.response_model} != {response_type}"
                )

    def register(self, app_type: str, server_requires_auth: bool) -> APIRouter:
        from aware_comms.http.registry import http_registry

        router = APIRouter()
        endpoint_metadatas = http_registry.get_endpoints_metadata(
            app_type=app_type, route_type=self.route_type
        )
        for endpoint_metadata in endpoint_metadatas:
            router.add_api_route(
                path=endpoint_metadata.get_normalized_path(prefix=self.route_type),
                endpoint=self._create_endpoint_handler(
                    endpoint_metadata=endpoint_metadata,
                    server_requires_auth=server_requires_auth,
                ),
                methods=[endpoint_metadata.method],
                response_model=endpoint_metadata.response_model,
            )
        return router


__all__ = ["HttpModelRouter"]
