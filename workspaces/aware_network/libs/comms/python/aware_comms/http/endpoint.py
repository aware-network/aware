from __future__ import annotations

import collections.abc
import inspect
from collections.abc import Awaitable, Callable
from enum import Enum
from typing import get_args, get_origin, get_type_hints
from uuid import UUID

from pydantic import BaseModel

from aware_comms.app.config import AppConfig

HttpRouteKey = str


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class HttpErrorType(str, Enum):
    VALIDATION_ERROR = "validation_error"
    HTTP_ERROR = "http_error"


class HttpErrorMessage(BaseModel):
    type: HttpErrorType
    message: str


class HttpEndpointMetadata(BaseModel):
    endpoint: str
    method: HttpMethod
    requires_auth: bool = True
    request_model: type[BaseModel]
    response_model: type[BaseModel]

    def get_normalized_path(self, prefix: str) -> str:
        normalized_prefix = f"/{prefix.strip('/')}"
        ep = self.endpoint.lstrip("/")
        return f"{normalized_prefix}/{ep}"

    def get_normalized_url(self, app_config: AppConfig, prefix: str) -> str:
        base_url = app_config.full_url.rstrip("/")
        return f"{base_url}{self.get_normalized_path(prefix)}"


HttpEndpointCallback = Callable[[BaseModel], Awaitable[BaseModel]]
HttpEndpointAuthCallback = Callable[[BaseModel, UUID], Awaitable[BaseModel]]


class HttpEndpointHandler(BaseModel):
    callback: HttpEndpointCallback | HttpEndpointAuthCallback

    def get_request_and_response_types(
        self,
    ) -> tuple[type[BaseModel], type[BaseModel]]:
        callback_type_hints = get_type_hints(self.callback)
        callback_signature = inspect.signature(self.callback)
        parameters = list(callback_signature.parameters.values())
        if len(parameters) < 1:
            raise ValueError("Callback must have at least one argument.")

        request_type = callback_type_hints.get(parameters[0].name)
        response_type = callback_type_hints.get("return")

        if not isinstance(request_type, type) or not issubclass(
            request_type, BaseModel
        ):
            raise ValueError("Callback request type must be a pydantic BaseModel.")

        origin = get_origin(response_type)
        if origin in (Awaitable, collections.abc.Coroutine):
            response_args = get_args(response_type)
            response_type = response_args[-1] if response_args else None

        if not isinstance(response_type, type) or not issubclass(
            response_type, BaseModel
        ):
            raise ValueError("Callback response type must be a pydantic BaseModel.")

        return request_type, response_type


class HttpRouteMetadata(BaseModel):
    route_type: HttpRouteKey
    endpoint_list: list[HttpEndpointMetadata]


__all__ = [
    "HttpEndpointAuthCallback",
    "HttpEndpointCallback",
    "HttpEndpointHandler",
    "HttpEndpointMetadata",
    "HttpErrorMessage",
    "HttpErrorType",
    "HttpMethod",
    "HttpRouteKey",
    "HttpRouteMetadata",
]
