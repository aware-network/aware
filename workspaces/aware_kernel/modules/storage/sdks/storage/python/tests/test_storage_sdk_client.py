from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_storage_sdk import AwareStorageSdk, StorageMediaRef
from aware_storage_service_dto.storage.media import (
    StorageBlobMetadata,
    StorageMediaResolution,
)
from aware_storage_service_dto.storage.service_operation import (
    DescribeStorageBlobResponse,
    RegisterStorageBlobResponse,
    ResolveStorageMediaResponse,
)


class _BlobClient:
    def __init__(self) -> None:
        self.register_request = None
        self.describe_request = None

    async def register(self, request):
        self.register_request = request
        return RegisterStorageBlobResponse(
            success=True,
            metadata=StorageBlobMetadata(
                object_id=uuid4(),
                sha=request.sha,
                mime_type=request.mime_type,
                size_bytes=request.size_bytes,
            ),
        )

    async def describe(self, request):
        self.describe_request = request
        return DescribeStorageBlobResponse(
            success=True,
            metadata=StorageBlobMetadata(
                object_id=request.object_id,
                sha="a" * 64,
                mime_type="image/png",
                size_bytes=12,
            ),
        )


class _MediaClient:
    def __init__(self) -> None:
        self.resolve_request = None

    async def resolve(self, request):
        self.resolve_request = request
        object_id = request.media_ref.object_id
        metadata = StorageBlobMetadata(
            object_id=object_id,
            sha="b" * 64,
            mime_type="image/png",
            size_bytes=20,
        )
        return ResolveStorageMediaResponse(
            success=True,
            metadata=metadata,
            resolution=StorageMediaResolution(
                media_ref=request.media_ref,
                object_id=object_id,
                sha=metadata.sha,
                mime_type=metadata.mime_type,
                size_bytes=metadata.size_bytes,
                uri=f"storage://blob/{object_id}",
                uri_scheme="storage",
                http_url="http://storage.local/crud/download?object_id=x",
                etag=metadata.sha,
            ),
        )


@pytest.mark.asyncio
async def test_storage_sdk_wraps_generated_api_client() -> None:
    blob = _BlobClient()
    media = _MediaClient()
    api_client = SimpleNamespace(storage=SimpleNamespace(blob=blob, media=media))
    sdk = AwareStorageSdk(api_client=api_client)
    object_id = uuid4()
    media_ref_id = uuid4()
    media_ref = StorageMediaRef(
        object_id=media_ref_id,
        uri=f"storage://blob/{media_ref_id}",
        mime_type="image/png",
    )

    registered = await sdk.register_blob(
        sha="a" * 64,
        mime_type="image/png",
        size_bytes=12,
    )
    described = await sdk.describe_blob(object_id=object_id)
    resolved = await sdk.resolve_media(media_ref=media_ref)

    assert registered.metadata is not None
    assert blob.register_request.sha == "a" * 64
    assert described.metadata is not None
    assert blob.describe_request.object_id == object_id
    assert resolved.resolution is not None
    assert media.resolve_request.media_ref == media_ref
    assert resolved.resolution.uri == f"storage://blob/{media_ref_id}"
    assert resolved.resolution.media_ref == media_ref
