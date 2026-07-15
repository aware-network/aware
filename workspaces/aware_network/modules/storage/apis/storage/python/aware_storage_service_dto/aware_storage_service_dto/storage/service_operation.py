from __future__ import annotations

# Standard
from functools import lru_cache
from typing import (
    ClassVar,
    Literal,
    TYPE_CHECKING,
)
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Storage Service Dto
from aware_storage_service_dto.storage.media import StorageMediaDisposition

if TYPE_CHECKING:
    from aware_storage_service_dto.storage.media import StorageBlobMetadata
    from aware_storage_service_dto.storage.media import StorageMediaRef
    from aware_storage_service_dto.storage.media import StorageMediaResolution
    from aware_storage_service_dto.storage.media import StorageOperationReceipt


class StorageServiceRequest(BaseModel):
    """
    Storage service operation DTOs.
    The generated Product A API is the control-plane boundary. It registers and
    resolves commit-backed StorageBlob metadata, then returns media descriptors
    for Storage-owned byte transport. Raw media bytes are intentionally absent
    from these payloads.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "register_blob": "aware_storage_service_dto.storage.service_operation.RegisterStorageBlobRequest",
        "describe_blob": "aware_storage_service_dto.storage.service_operation.DescribeStorageBlobRequest",
        "resolve_media": "aware_storage_service_dto.storage.service_operation.ResolveStorageMediaRequest",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownStorageServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownStorageServiceRequest(StorageServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class StorageServiceResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    error: str | None = Field(default=None)
    receipt: StorageOperationReceipt | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "register_blob": "aware_storage_service_dto.storage.service_operation.RegisterStorageBlobResponse",
        "describe_blob": "aware_storage_service_dto.storage.service_operation.DescribeStorageBlobResponse",
        "resolve_media": "aware_storage_service_dto.storage.service_operation.ResolveStorageMediaResponse",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownStorageServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownStorageServiceResponse(StorageServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class RegisterStorageBlobRequest(StorageServiceRequest):
    # Discriminator Tag
    operation: Literal["register_blob"] = "register_blob"

    # Attributes
    object_id: UUID | None = Field(default=None)
    sha: str
    mime_type: str = Field(default="application/octet-stream")
    size_bytes: int
    bucket_id: UUID | None = Field(default=None)
    object_key: str | None = Field(default=None)
    path_local: str | None = Field(default=None)


class RegisterStorageBlobResponse(StorageServiceResponse):
    # Discriminator Tag
    operation: Literal["register_blob"] = "register_blob"

    # Attributes
    metadata: StorageBlobMetadata | None = Field(default=None)


class DescribeStorageBlobRequest(StorageServiceRequest):
    # Discriminator Tag
    operation: Literal["describe_blob"] = "describe_blob"

    # Attributes
    object_id: UUID


class DescribeStorageBlobResponse(StorageServiceResponse):
    # Discriminator Tag
    operation: Literal["describe_blob"] = "describe_blob"

    # Attributes
    metadata: StorageBlobMetadata | None = Field(default=None)


class ResolveStorageMediaRequest(StorageServiceRequest):
    # Discriminator Tag
    operation: Literal["resolve_media"] = "resolve_media"

    # Attributes
    media_ref: StorageMediaRef
    require_ownership: bool = Field(default=False)
    include_http_url: bool = Field(default=True)
    preferred_uri_scheme: str | None = Field(default=None)
    filename: str | None = Field(default=None)
    disposition: StorageMediaDisposition = Field(default=StorageMediaDisposition.inline)


class ResolveStorageMediaResponse(StorageServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_media"] = "resolve_media"

    # Attributes
    metadata: StorageBlobMetadata | None = Field(default=None)
    resolution: StorageMediaResolution | None = Field(default=None)
