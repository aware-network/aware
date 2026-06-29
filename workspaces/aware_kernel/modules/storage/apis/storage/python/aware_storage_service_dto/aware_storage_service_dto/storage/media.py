from __future__ import annotations

# Standard
from enum import Enum
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class StorageMediaDisposition(Enum):
    """
    Storage media DTOs.
    Contract:
    - Blob bytes are data-plane payloads and are not embedded in generated API
    JSON requests or responses.
    - StorageBlob metadata remains the commit-backed reference truth.
    - Renderers resolve media through Storage API descriptors and then fetch
    bytes through a Storage-owned data-plane transport.
    """

    inline = "inline"
    attachment = "attachment"


class StorageBlobRef(BaseModel):
    # Attributes
    object_id: UUID | None = Field(default=None)
    sha: str | None = Field(default=None)


class StorageMediaRef(BaseModel):
    # Attributes
    object_id: UUID
    uri: str | None = Field(default=None)
    uri_scheme: str = Field(default="storage")
    media_kind: str | None = Field(default=None)
    mime_type: str | None = Field(default=None)
    sha: str | None = Field(default=None)
    variant_key: str | None = Field(default=None)
    rendition_key: str | None = Field(default=None)
    filename: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class StorageBlobMetadata(BaseModel):
    # Attributes
    object_id: UUID
    sha: str
    mime_type: str = Field(default="application/octet-stream")
    size_bytes: int = Field(default=0)
    object_key: str | None = Field(default=None)
    path_local: str | None = Field(default=None)
    bucket_id: UUID | None = Field(default=None)


class StorageMediaResolution(BaseModel):
    # Attributes
    media_ref: StorageMediaRef
    object_id: UUID
    sha: str
    mime_type: str = Field(default="application/octet-stream")
    size_bytes: int = Field(default=0)
    uri: str
    uri_scheme: str = Field(default="storage")
    http_url: str | None = Field(default=None)
    cache_control: str | None = Field(default=None)
    etag: str | None = Field(default=None)
    content_disposition: str | None = Field(default=None)
    filename: str | None = Field(default=None)
    expires_at: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class StorageOperationReceipt(BaseModel):
    # Attributes
    operation: str
    status: str = Field(default="succeeded")
    object_id: UUID | None = Field(default=None)
    sha: str | None = Field(default=None)
    size_bytes: int | None = Field(default=None)
    mime_type: str | None = Field(default=None)
    backend_kind: str = Field(default="storage-service")
    data_plane: str = Field(default="storage")
    metadata: JsonObject = Field(default_factory=JsonObject)
