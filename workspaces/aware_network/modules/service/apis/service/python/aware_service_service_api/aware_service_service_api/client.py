# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import SERVICE__OPERATION__INVOKE_ENDPOINT_REF
from aware_service_service_dto.comms.models.service import ServiceOperationRequest, ServiceOperationResponse


class ServiceOperationCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def invoke(self, request: ServiceOperationRequest) -> ServiceOperationResponse:
        """Invoke a canonical Service operation envelope through the Service service boundary."""
        return cast(
            ServiceOperationResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=SERVICE__OPERATION__INVOKE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.operation = ServiceOperationCapabilityClient(client)


class AwareServiceServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.service = ServiceApiClient(client)


__all__ = [
    "AwareServiceServiceApiClient",
    "ServiceApiClient",
    "ServiceOperationCapabilityClient",
]
