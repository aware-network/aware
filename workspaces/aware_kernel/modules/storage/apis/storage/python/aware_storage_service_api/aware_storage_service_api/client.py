# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import (
    STORAGE__BLOB__DESCRIBE_ENDPOINT_REF,
    STORAGE__BLOB__REGISTER_ENDPOINT_REF,
    STORAGE__MEDIA__RESOLVE_ENDPOINT_REF,
)
from aware_storage_service_dto.storage.service_operation import (
    DescribeStorageBlobRequest,
    DescribeStorageBlobResponse,
    RegisterStorageBlobRequest,
    RegisterStorageBlobResponse,
    ResolveStorageMediaRequest,
    ResolveStorageMediaResponse,
)


class StorageBlobCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def describe(self, request: DescribeStorageBlobRequest) -> DescribeStorageBlobResponse:
        """Describe one StorageBlob metadata record by object id."""
        return cast(
            DescribeStorageBlobResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=STORAGE__BLOB__DESCRIBE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def register(self, request: RegisterStorageBlobRequest) -> RegisterStorageBlobResponse:
        """Register commit-backed StorageBlob metadata for bytes already stored on the Storage data-plane."""
        return cast(
            RegisterStorageBlobResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=STORAGE__BLOB__REGISTER_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class StorageMediaCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve(self, request: ResolveStorageMediaRequest) -> ResolveStorageMediaResponse:
        """Resolve one StorageBlob into renderer-safe media descriptors without embedding raw bytes."""
        return cast(
            ResolveStorageMediaResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=STORAGE__MEDIA__RESOLVE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class StorageApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.blob = StorageBlobCapabilityClient(client)
        self.media = StorageMediaCapabilityClient(client)


class AwareStorageServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.storage = StorageApiClient(client)


__all__ = [
    "AwareStorageServiceApiClient",
    "StorageApiClient",
    "StorageBlobCapabilityClient",
    "StorageMediaCapabilityClient",
]
