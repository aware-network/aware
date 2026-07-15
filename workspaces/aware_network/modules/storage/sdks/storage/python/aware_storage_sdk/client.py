from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from aware_storage_service_dto.storage.media import (
    StorageMediaDisposition,
    StorageMediaRef,
)
from aware_storage_service_dto.storage.service_operation import (
    DescribeStorageBlobRequest,
    DescribeStorageBlobResponse,
    RegisterStorageBlobRequest,
    RegisterStorageBlobResponse,
    ResolveStorageMediaRequest,
    ResolveStorageMediaResponse,
)


class StorageSdkError(RuntimeError):
    pass


class StorageBlobCapabilityClient(Protocol):
    async def register(
        self,
        request: RegisterStorageBlobRequest,
    ) -> RegisterStorageBlobResponse: ...

    async def describe(
        self,
        request: DescribeStorageBlobRequest,
    ) -> DescribeStorageBlobResponse: ...


class StorageMediaCapabilityClient(Protocol):
    async def resolve(
        self,
        request: ResolveStorageMediaRequest,
    ) -> ResolveStorageMediaResponse: ...


class StorageApiNamespaceClient(Protocol):
    @property
    def blob(self) -> StorageBlobCapabilityClient: ...

    @property
    def media(self) -> StorageMediaCapabilityClient: ...


class StorageGeneratedApiClient(Protocol):
    @property
    def storage(self) -> StorageApiNamespaceClient: ...


@dataclass(frozen=True, slots=True)
class AwareStorageSdk:
    api_client: StorageGeneratedApiClient

    async def register_blob(
        self,
        *,
        sha: str,
        mime_type: str,
        size_bytes: int,
        object_id: UUID | None = None,
        actor_id: UUID | None = None,
    ) -> RegisterStorageBlobResponse:
        response = await self.api_client.storage.blob.register(
            RegisterStorageBlobRequest(
                actor_id=actor_id,
                object_id=object_id,
                sha=sha,
                mime_type=mime_type,
                size_bytes=size_bytes,
            )
        )
        _raise_if_failed(response, operation="register_blob")
        return response

    async def describe_blob(
        self,
        *,
        object_id: UUID,
        actor_id: UUID | None = None,
    ) -> DescribeStorageBlobResponse:
        response = await self.api_client.storage.blob.describe(
            DescribeStorageBlobRequest(actor_id=actor_id, object_id=object_id)
        )
        _raise_if_failed(response, operation="describe_blob")
        return response

    async def resolve_media(
        self,
        *,
        media_ref: StorageMediaRef,
        actor_id: UUID | None = None,
        include_http_url: bool = True,
        preferred_uri_scheme: str | None = None,
        filename: str | None = None,
        disposition: StorageMediaDisposition = StorageMediaDisposition.inline,
    ) -> ResolveStorageMediaResponse:
        response = await self.api_client.storage.media.resolve(
            ResolveStorageMediaRequest(
                actor_id=actor_id,
                media_ref=media_ref,
                include_http_url=include_http_url,
                preferred_uri_scheme=preferred_uri_scheme,
                filename=filename,
                disposition=disposition,
            )
        )
        _raise_if_failed(response, operation="resolve_media")
        if response.resolution is None:
            raise StorageSdkError("Storage media resolution response is missing resolution.")
        return response


def build_storage_sdk(*, api_client: StorageGeneratedApiClient) -> AwareStorageSdk:
    return AwareStorageSdk(api_client=api_client)


def _raise_if_failed(response: object, *, operation: str) -> None:
    success = bool(getattr(response, "success", False))
    if success:
        return
    error = getattr(response, "error", None) or f"Storage SDK {operation} failed."
    raise StorageSdkError(str(error))


__all__ = [
    "AwareStorageSdk",
    "StorageApiNamespaceClient",
    "StorageBlobCapabilityClient",
    "StorageGeneratedApiClient",
    "StorageMediaCapabilityClient",
    "StorageMediaDisposition",
    "StorageMediaRef",
    "StorageSdkError",
    "build_storage_sdk",
]
