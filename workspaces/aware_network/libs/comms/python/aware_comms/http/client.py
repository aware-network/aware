from __future__ import annotations

import logging
import os
from ssl import SSLContext

import httpx
from pydantic import BaseModel

from aware_comms.app.config import get_app_config
from aware_comms.http.endpoint import HttpRouteKey
from aware_comms.http.registry import http_registry

logger = logging.getLogger(__name__)


class HTTPClient:
    """HTTP Client for making requests to service endpoints."""

    def __init__(
        self,
        app_type: str,
        route_type: HttpRouteKey,
        timeout: float = 120.0,
    ):
        self.app_type: str = app_type
        self.route_type: HttpRouteKey = route_type
        self.timeout: float = timeout

    async def request(
        self, request: BaseModel, headers: dict[str, str] | None = None
    ) -> BaseModel:
        logger.debug(
            "Starting HTTP request for %s - %s", self.app_type, self.route_type
        )

        app_config = get_app_config(self.app_type)
        endpoint_config = http_registry.get_endpoint_metadata(
            app_type=self.app_type,
            route_type=self.route_type,
            request_model=type(request),
        )
        url = endpoint_config.get_normalized_url(
            app_config=app_config, prefix=self.route_type
        )
        logger.info("Constructed URL: %s", url)

        verify: str | bool | SSLContext = True
        if os.getenv("ENVIRONMENT") == "dev":
            verify = False

        request_model = endpoint_config.request_model
        if not isinstance(request, request_model):
            raise TypeError(f"Request data must be of type {request_model}")

        async with httpx.AsyncClient(verify=verify) as client:
            response = await client.request(
                method=endpoint_config.method,
                url=url,
                json=request.model_dump(mode="json"),
                headers=headers,
                timeout=self.timeout,
            )
            _ = response.raise_for_status()
            return endpoint_config.response_model.model_validate_json(response.text)


__all__ = ["HTTPClient"]
