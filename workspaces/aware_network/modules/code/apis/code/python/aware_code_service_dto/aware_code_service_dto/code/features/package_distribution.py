from __future__ import annotations

# Standard
from enum import Enum
from functools import lru_cache
from typing import (
    ClassVar,
    Literal,
)
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class CodeLanguage(Enum):
    """
    CodePackage distribution DTOs for Product A consumers.
    Contract:
    - Hub can expose search/describe/resolve/download/publish over these DTOs.
    - The DTOs describe package artifact truth and replay locks, not executable
    plugin activation.
    - Publish registers an already-staged artifact lock with Hub authority truth;
    binary upload/storage transport is intentionally separate.
    - CodeModule/module aggregate layout is intentionally out of scope here.
    """

    aware = "aware"
    dart = "dart"
    python = "python"
    sql = "sql"


class CodePackageServiceRequest(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "discover_code_package_channel_heads": "aware_code_service_dto.code.features.package_distribution.DiscoverCodePackageChannelHeadsRequest",
        "search_code_package": "aware_code_service_dto.code.features.package_distribution.SearchCodePackageRequest",
        "describe_code_package": "aware_code_service_dto.code.features.package_distribution.DescribeCodePackageRequest",
        "resolve_code_package": "aware_code_service_dto.code.features.package_distribution.ResolveCodePackageRequest",
        "download_code_package": "aware_code_service_dto.code.features.package_distribution.DownloadCodePackageRequest",
        "publish_code_package": "aware_code_service_dto.code.features.package_distribution.PublishCodePackageRequest",
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
            return UnknownCodePackageServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownCodePackageServiceRequest(CodePackageServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class CodePackageServiceResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "discover_code_package_channel_heads": "aware_code_service_dto.code.features.package_distribution.DiscoverCodePackageChannelHeadsResponse",
        "search_code_package": "aware_code_service_dto.code.features.package_distribution.SearchCodePackageResponse",
        "describe_code_package": "aware_code_service_dto.code.features.package_distribution.DescribeCodePackageResponse",
        "resolve_code_package": "aware_code_service_dto.code.features.package_distribution.ResolveCodePackageResponse",
        "download_code_package": "aware_code_service_dto.code.features.package_distribution.DownloadCodePackageResponse",
        "publish_code_package": "aware_code_service_dto.code.features.package_distribution.PublishCodePackageResponse",
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
            return UnknownCodePackageServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownCodePackageServiceResponse(CodePackageServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class CodePackageRef(BaseModel):
    # Attributes
    package_name: str
    language: CodeLanguage | None = Field(default=None)
    surface: str | None = Field(default=None)
    channel: str = Field(default="stable")
    version: str | None = Field(default=None)
    revision_id: str | None = Field(default=None)
    digest: str | None = Field(default=None)


class CodePackageArtifactLock(BaseModel):
    # Attributes
    artifact_url: str
    sha256: str
    size_bytes: int | None = Field(default=None)
    media_type: str | None = Field(default=None)
    archive_format: str | None = Field(default=None)
    revision_id: str | None = Field(default=None)
    published_at: str | None = Field(default=None)


class CodePackageDescriptor(BaseModel):
    # Attributes
    package_name: str
    language: CodeLanguage
    surface: str
    manifest_kind: str
    manifest_relative_path: str
    package_root: str
    sources_root: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    version: str | None = Field(default=None)
    revision_id: str | None = Field(default=None)
    digest: str | None = Field(default=None)
    artifact_media_type: str | None = Field(default=None)
    artifact_size_bytes: int | None = Field(default=None)
    download_handle: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class CodePackageChannelHead(BaseModel):
    # Attributes
    package_name: str
    language: CodeLanguage | None = Field(default=None)
    surface: str | None = Field(default=None)
    channel: str = Field(default="stable")
    revision_id: str
    updated_at: str | None = Field(default=None)
    publisher_execution_id: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class CodePackageDiscoveryEntry(BaseModel):
    # Attributes
    channel_head: CodePackageChannelHead
    descriptor: CodePackageDescriptor | None = Field(default=None)
    artifact_lock: CodePackageArtifactLock | None = Field(default=None)


class DiscoverCodePackageChannelHeadsRequest(CodePackageServiceRequest):
    # Discriminator Tag
    operation: Literal["discover_code_package_channel_heads"] = "discover_code_package_channel_heads"

    # Attributes
    query: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    language: CodeLanguage | None = Field(default=None)
    surface: str | None = Field(default=None)
    channel: str | None = Field(default=None)
    authority_base_url: str | None = Field(default=None)
    index_url: str | None = Field(default=None)
    limit: int = Field(default=50)


class DiscoverCodePackageChannelHeadsResponse(CodePackageServiceResponse):
    # Discriminator Tag
    operation: Literal["discover_code_package_channel_heads"] = "discover_code_package_channel_heads"

    # Attributes
    authority_source_url: str | None = Field(default=None)
    entries: list[CodePackageDiscoveryEntry] = Field(default_factory=list)


class SearchCodePackageRequest(CodePackageServiceRequest):
    # Discriminator Tag
    operation: Literal["search_code_package"] = "search_code_package"

    # Attributes
    query: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    language: CodeLanguage | None = Field(default=None)
    surface: str | None = Field(default=None)
    channel: str = Field(default="stable")
    authority_base_url: str | None = Field(default=None)
    index_url: str | None = Field(default=None)
    limit: int = Field(default=50)


class SearchCodePackageResponse(CodePackageServiceResponse):
    # Discriminator Tag
    operation: Literal["search_code_package"] = "search_code_package"

    # Attributes
    authority_source_url: str | None = Field(default=None)
    descriptors: list[CodePackageDescriptor] = Field(default_factory=list)


class DescribeCodePackageRequest(CodePackageServiceRequest):
    # Discriminator Tag
    operation: Literal["describe_code_package"] = "describe_code_package"

    # Attributes
    selector: CodePackageRef
    authority_base_url: str | None = Field(default=None)
    index_url: str | None = Field(default=None)


class DescribeCodePackageResponse(CodePackageServiceResponse):
    # Discriminator Tag
    operation: Literal["describe_code_package"] = "describe_code_package"

    # Attributes
    authority_source_url: str | None = Field(default=None)
    descriptor: CodePackageDescriptor | None = Field(default=None)


class ResolveCodePackageRequest(CodePackageServiceRequest):
    # Discriminator Tag
    operation: Literal["resolve_code_package"] = "resolve_code_package"

    # Attributes
    selector: CodePackageRef
    authority_base_url: str | None = Field(default=None)
    index_url: str | None = Field(default=None)


class ResolveCodePackageResponse(CodePackageServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_code_package"] = "resolve_code_package"

    # Attributes
    authority_source_url: str | None = Field(default=None)
    selector: CodePackageRef
    descriptor: CodePackageDescriptor
    artifact_lock: CodePackageArtifactLock


class DownloadCodePackageRequest(CodePackageServiceRequest):
    # Discriminator Tag
    operation: Literal["download_code_package"] = "download_code_package"

    # Attributes
    selector: CodePackageRef
    authority_base_url: str | None = Field(default=None)
    index_url: str | None = Field(default=None)


class DownloadCodePackageResponse(CodePackageServiceResponse):
    # Discriminator Tag
    operation: Literal["download_code_package"] = "download_code_package"

    # Attributes
    authority_source_url: str | None = Field(default=None)
    selector: CodePackageRef
    artifact_lock: CodePackageArtifactLock


class PublishCodePackageRequest(CodePackageServiceRequest):
    # Discriminator Tag
    operation: Literal["publish_code_package"] = "publish_code_package"

    # Attributes
    descriptor: CodePackageDescriptor
    artifact_lock: CodePackageArtifactLock
    channel: str = Field(default="stable")
    authority_base_url: str | None = Field(default=None)
    index_url: str | None = Field(default=None)
    publisher_execution_id: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)


class PublishCodePackageResponse(CodePackageServiceResponse):
    # Discriminator Tag
    operation: Literal["publish_code_package"] = "publish_code_package"

    # Attributes
    authority_source_url: str | None = Field(default=None)
    selector: CodePackageRef | None = Field(default=None)
    descriptor: CodePackageDescriptor | None = Field(default=None)
    artifact_lock: CodePackageArtifactLock | None = Field(default=None)
    accepted: bool = Field(default=False)
