# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import API__OPERATION__INVOKE_ENDPOINT_REF
from aware_api_service_dto.comms.models.api import ApiOperationRequest, ApiOperationResponse


class ApiOperationCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def invoke(self, request: ApiOperationRequest) -> ApiOperationResponse:
        """Invoke a canonical API operation envelope through the API service boundary."""
        return cast(
            ApiOperationResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=API__OPERATION__INVOKE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ApiApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.operation = ApiOperationCapabilityClient(client)


class AwareApiServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.api = ApiApiClient(client)


__all__ = [
    "AwareApiServiceApiClient",
    "ApiApiClient",
    "ApiOperationCapabilityClient",
]
