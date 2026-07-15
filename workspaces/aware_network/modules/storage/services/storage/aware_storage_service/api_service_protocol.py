from __future__ import annotations

import os
import re
from dataclasses import dataclass
from uuid import UUID

from aware_storage.handlers.impl.blob import storage_blob as storage_blob_handler
from aware_storage.stable_ids import stable_storage_blob_id
from aware_storage_ontology.blob.storage_blob import StorageBlob
from aware_storage_service_dto.storage.media import (
    StorageBlobMetadata,
    StorageMediaDisposition,
    StorageMediaResolution,
    StorageOperationReceipt,
)
from aware_storage_service_dto.storage.service_operation import (
    DescribeStorageBlobRequest,
    DescribeStorageBlobResponse,
    RegisterStorageBlobRequest,
    RegisterStorageBlobResponse,
    ResolveStorageMediaRequest,
    ResolveStorageMediaResponse,
)
from aware_types import JsonObject

from .http_file_ops import read_local_blob_metadata


_SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def build_aware_storage_service_protocol_handler(
    *,
    media_base_url: str | None = None,
) -> object:
    return _AwareStorageServiceProtocolHandler(
        support=_StorageProtocolSupport(media_base_url=media_base_url)
    )


@dataclass(frozen=True, slots=True)
class _StorageProtocolSupport:
    media_base_url: str | None = None

    def resolved_media_base_url(self) -> str | None:
        raw = self.media_base_url or os.environ.get("AWARE_STORAGE_MEDIA_BASE_URL")
        if raw is None:
            return None
        value = raw.strip().rstrip("/")
        return value or None

    def receipt(
        self,
        *,
        operation: str,
        status: str,
        metadata: StorageBlobMetadata | None = None,
        extra: dict[str, object] | None = None,
    ) -> StorageOperationReceipt:
        payload: dict[str, object] = dict(extra or {})
        return StorageOperationReceipt(
            operation=operation,
            status=status,
            object_id=metadata.object_id if metadata is not None else None,
            sha=metadata.sha if metadata is not None else None,
            size_bytes=metadata.size_bytes if metadata is not None else None,
            mime_type=metadata.mime_type if metadata is not None else None,
            backend_kind="storage-service",
            data_plane="storage",
            metadata=JsonObject(payload),
        )

    def media_resolution(
        self,
        *,
        request: ResolveStorageMediaRequest,
        metadata: StorageBlobMetadata,
    ) -> StorageMediaResolution:
        scheme = (request.preferred_uri_scheme or "storage").strip() or "storage"
        uri = f"{scheme}://blob/{metadata.object_id}"
        http_url = None
        base_url = self.resolved_media_base_url()
        if request.include_http_url and base_url is not None:
            http_url = f"{base_url}/crud/download?object_id={metadata.object_id}"

        filename = request.filename
        disposition = _disposition_value(request.disposition)
        content_disposition = None
        if filename:
            content_disposition = f'{disposition}; filename="{filename}"'

        return StorageMediaResolution(
            media_ref=request.media_ref,
            object_id=metadata.object_id,
            sha=metadata.sha,
            mime_type=metadata.mime_type,
            size_bytes=metadata.size_bytes,
            uri=uri,
            uri_scheme=scheme,
            http_url=http_url,
            cache_control="public, max-age=31536000, immutable",
            etag=metadata.sha,
            content_disposition=content_disposition,
            filename=filename,
            metadata=JsonObject(
                {
                    "data_plane": "storage",
                    "http_url_available": http_url is not None,
                }
            ),
        )


class _StorageBlobCapabilityHandler:
    def __init__(self, *, support: _StorageProtocolSupport) -> None:
        self._support = support

    async def register(
        self,
        request: RegisterStorageBlobRequest,
    ) -> RegisterStorageBlobResponse:
        try:
            sha = _normalize_sha(request.sha)
            expected_id = stable_storage_blob_id(sha=sha)
            if request.object_id is not None and request.object_id != expected_id:
                raise ValueError(
                    "object_id does not match StorageBlob.id derived from sha "
                    f"(object_id={request.object_id} blob_id={expected_id})"
                )
            blob = await storage_blob_handler.create(
                sha=sha,
                mime_type=request.mime_type,
                size_bytes=request.size_bytes,
            )
            if request.bucket_id is not None:
                blob.bucket_id = request.bucket_id
            if request.object_key:
                blob.object_key = request.object_key
            if request.path_local:
                blob.path_local = request.path_local

            metadata = _metadata_from_blob(blob)
            return RegisterStorageBlobResponse(
                request_id=request.request_id,
                success=True,
                metadata=metadata,
                receipt=self._support.receipt(
                    operation=request.operation,
                    status="succeeded",
                    metadata=metadata,
                    extra={"ontology_handler": "StorageBlob.create"},
                ),
            )
        except Exception as exc:
            return RegisterStorageBlobResponse(
                request_id=request.request_id,
                success=False,
                error=str(exc),
                metadata=None,
                receipt=self._support.receipt(
                    operation=request.operation,
                    status="failed",
                    extra={"error": str(exc)},
                ),
            )

    async def describe(
        self,
        request: DescribeStorageBlobRequest,
    ) -> DescribeStorageBlobResponse:
        try:
            metadata = await _resolve_metadata(request.object_id)
            return DescribeStorageBlobResponse(
                request_id=request.request_id,
                success=True,
                metadata=metadata,
                receipt=self._support.receipt(
                    operation=request.operation,
                    status="succeeded",
                    metadata=metadata,
                ),
            )
        except Exception as exc:
            return DescribeStorageBlobResponse(
                request_id=request.request_id,
                success=False,
                error=str(exc),
                metadata=None,
                receipt=self._support.receipt(
                    operation=request.operation,
                    status="failed",
                    extra={"error": str(exc)},
                ),
            )


class _StorageMediaCapabilityHandler:
    def __init__(self, *, support: _StorageProtocolSupport) -> None:
        self._support = support

    async def resolve(
        self,
        request: ResolveStorageMediaRequest,
    ) -> ResolveStorageMediaResponse:
        try:
            metadata = await _resolve_metadata(request.media_ref.object_id)
            resolution = self._support.media_resolution(
                request=request,
                metadata=metadata,
            )
            return ResolveStorageMediaResponse(
                request_id=request.request_id,
                success=True,
                metadata=metadata,
                resolution=resolution,
                receipt=self._support.receipt(
                    operation=request.operation,
                    status="succeeded",
                    metadata=metadata,
                    extra={"uri_scheme": resolution.uri_scheme},
                ),
            )
        except Exception as exc:
            return ResolveStorageMediaResponse(
                request_id=request.request_id,
                success=False,
                error=str(exc),
                metadata=None,
                resolution=None,
                receipt=self._support.receipt(
                    operation=request.operation,
                    status="failed",
                    extra={"error": str(exc)},
                ),
            )


class _StorageApiServiceProtocolHandler:
    def __init__(self, *, support: _StorageProtocolSupport) -> None:
        self.blob = _StorageBlobCapabilityHandler(support=support)
        self.media = _StorageMediaCapabilityHandler(support=support)


class _AwareStorageServiceProtocolHandler:
    def __init__(self, *, support: _StorageProtocolSupport) -> None:
        self.storage = _StorageApiServiceProtocolHandler(support=support)


def _normalize_sha(value: str) -> str:
    sha = value.strip().lower()
    if not _SHA_RE.fullmatch(sha):
        raise ValueError("sha must be a 64-char lowercase hex SHA-256 digest")
    return sha


def _metadata_from_blob(blob: StorageBlob) -> StorageBlobMetadata:
    if blob.id is None:
        raise ValueError("StorageBlob metadata is missing id")
    return StorageBlobMetadata(
        object_id=blob.id,
        sha=_normalize_sha(blob.sha),
        mime_type=blob.mime_type or "application/octet-stream",
        size_bytes=int(blob.size_bytes or 0),
        object_key=blob.object_key,
        path_local=blob.path_local,
        bucket_id=blob.bucket_id,
    )


async def _resolve_metadata(object_id: UUID) -> StorageBlobMetadata:
    blob = await StorageBlob.by_id(object_id)
    if blob is not None:
        return _metadata_from_blob(blob)

    local_meta = read_local_blob_metadata(object_id)
    if local_meta is not None:
        return StorageBlobMetadata(
            object_id=local_meta.id,
            sha=_normalize_sha(local_meta.sha),
            mime_type=local_meta.mime_type,
            size_bytes=local_meta.size_bytes,
            object_key=f"{local_meta.sha[:2]}/{local_meta.sha[2:]}",
        )

    raise FileNotFoundError(f"StorageBlob not found: {object_id}")


def _disposition_value(value: StorageMediaDisposition | str) -> str:
    if isinstance(value, StorageMediaDisposition):
        return value.value
    return str(value)


__all__ = ["build_aware_storage_service_protocol_handler"]
