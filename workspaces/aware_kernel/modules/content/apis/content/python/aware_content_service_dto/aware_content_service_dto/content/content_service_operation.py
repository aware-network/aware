from __future__ import annotations

# Standard
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


class ContentTextPartV1(BaseModel):
    """
    Content service operation DTOs.
    Contract:
    - Content API is a read/render and package materialization boundary over
    Content ontology truth.
    - DTOs carry Content ids and Experience-safe reference ids, not Social,
    provider, or workspace-specific payloads.
    - Blob-backed text fails closed unless the concrete service has an explicit
    blob store path.
    """

    # Attributes
    content_part_content_id: UUID | None = Field(default=None)
    content_part_id: UUID | None = Field(default=None)
    content_part_text_id: UUID | None = Field(default=None)
    position: int = Field(default=0)
    part_key: str | None = Field(default=None)
    media_type: str = Field(default="text/plain")
    text: str = Field(default="")
    digest_algorithm: str = Field(default="sha256")
    digest: str | None = Field(default=None)
    size_bytes: int = Field(default=0)
    source_kind: str = Field(default="inline_text")
    provenance: JsonObject = Field(default_factory=JsonObject)


class ContentTextResolutionV1(BaseModel):
    # Attributes
    content_id: UUID
    content_key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    media_type: str = Field(default="text/plain")
    text: str = Field(default="")
    parts: list[ContentTextPartV1] = Field(default_factory=list)
    digest_algorithm: str = Field(default="sha256")
    digest: str | None = Field(default=None)
    size_bytes: int = Field(default=0)
    source_kind: str = Field(default="inline_text")
    provenance: JsonObject = Field(default_factory=JsonObject)


class ContentPackageExportPartV1(BaseModel):
    # Attributes
    part_key: str
    position: int = Field(default=0)
    modality_type: str = Field(default="text")
    content_part_type: str = Field(default="text")
    media_type: str = Field(default="text/plain")
    text: str | None = Field(default=None)
    raw_path: str | None = Field(default=None)
    uri: str | None = Field(default=None)
    provider_id: str | None = Field(default=None)
    digest_algorithm: str = Field(default="sha256")
    digest: str | None = Field(default=None)
    size_bytes: int | None = Field(default=None)
    aware_content_mapping: JsonObject = Field(default_factory=JsonObject)
    provenance: JsonObject = Field(default_factory=JsonObject)


class ContentPackageArtifactProjectionV1(BaseModel):
    # Attributes
    output_key: str = Field(default="content")
    artifact_key: str
    artifact_family: str = Field(default="workspace_content")
    artifact_role: str = Field(default="coordination_content")
    required_for: list[str] = Field(default_factory=list)
    producer_provider_key: str
    producer_key: str
    producer_kind: str = Field(default="service_export")
    materialization_index: int | None = Field(default=None)
    relative_path: str
    uri: str | None = Field(default=None)
    media_type: str = Field(default="text/plain")
    digest_algorithm: str = Field(default="sha256")
    digest: str | None = Field(default=None)
    size_bytes: int | None = Field(default=None)
    runtime_contract_version: str = Field(default="aware.content.package_export.v1")
    provider_payload: JsonObject = Field(default_factory=JsonObject)
    receipt_payload: JsonObject = Field(default_factory=JsonObject)


class ContentPackageExportDocumentV1(BaseModel):
    # Attributes
    export_kind: str = Field(default="content_package_export")
    contract_version: str = Field(default="aware.content.package_export.v1")
    package_name: str
    package_root: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    title: str | None = Field(default=None)
    package_kind: str = Field(default="content")
    source_provider_key: str
    source_ref: str
    runtime_contract_version: str = Field(default="aware.content.package_export.v1")
    content_key: str | None = Field(default=None)
    content_title: str | None = Field(default=None)
    target_path: str
    media_type: str = Field(default="text/plain")
    digest_algorithm: str = Field(default="sha256")
    digest: str | None = Field(default=None)
    size_bytes: int | None = Field(default=None)
    content_text: str | None = Field(default=None)
    parts: list[ContentPackageExportPartV1] = Field(default_factory=list)
    artifact: ContentPackageArtifactProjectionV1 | None = Field(default=None)
    aware_content_mapping: JsonObject = Field(default_factory=JsonObject)
    provider_payload: JsonObject = Field(default_factory=JsonObject)
    provenance: JsonObject = Field(default_factory=JsonObject)


class ContentPackageMaterializedArtifactRefV1(BaseModel):
    # Attributes
    content_package_id: UUID | None = Field(default=None)
    content_id: UUID | None = Field(default=None)
    domain_commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    service_host_receipt_ref: str | None = Field(default=None)
    output_key: str
    artifact_key: str
    status: str = Field(default="available")
    artifact_family: str | None = Field(default=None)
    artifact_role: str | None = Field(default=None)
    required_for: list[str] = Field(default_factory=list)
    producer_provider_key: str | None = Field(default=None)
    producer_key: str | None = Field(default=None)
    producer_kind: str | None = Field(default=None)
    materialization_index: int | None = Field(default=None)
    digest_algorithm: str | None = Field(default="sha256")
    digest: str | None = Field(default=None)
    relative_path: str | None = Field(default=None)
    uri: str | None = Field(default=None)
    media_type: str | None = Field(default=None)
    size_bytes: int | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    provider_payload: JsonObject = Field(default_factory=JsonObject)
    receipt_payload: JsonObject = Field(default_factory=JsonObject)


class ContentPackageMaterializationResultV1(BaseModel):
    # Attributes
    content_package_id: UUID | None = Field(default=None)
    content_id: UUID | None = Field(default=None)
    domain_commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    service_host_receipt_ref: str | None = Field(default=None)
    package_name: str
    content_key: str | None = Field(default=None)
    source_provider_key: str
    source_ref: str
    target_path: str
    media_type: str = Field(default="text/plain")
    digest_algorithm: str = Field(default="sha256")
    digest: str | None = Field(default=None)
    size_bytes: int | None = Field(default=None)
    artifact_refs: list[ContentPackageMaterializedArtifactRefV1] = Field(default_factory=list)
    aware_content_mapping: JsonObject = Field(default_factory=JsonObject)
    provenance: JsonObject = Field(default_factory=JsonObject)


class ContentOperationReceipt(BaseModel):
    # Attributes
    operation: str
    status: str = Field(default="succeeded")
    content_id: UUID | None = Field(default=None)
    content_package_id: UUID | None = Field(default=None)
    domain_commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    service_host_receipt_ref: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    digest_algorithm: str = Field(default="sha256")
    digest: str | None = Field(default=None)
    size_bytes: int | None = Field(default=None)
    backend_kind: str = Field(default="content-service")
    metadata: JsonObject = Field(default_factory=JsonObject)


class ContentServiceRequest(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "resolve_content_text": "aware_content_service_dto.content.content_service_operation.ResolveContentTextRequest",
        "materialize_content_package": "aware_content_service_dto.content.content_service_operation.MaterializeContentPackageRequest",
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
            return UnknownContentServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownContentServiceRequest(ContentServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ContentServiceResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    error: str | None = Field(default=None)
    receipt: ContentOperationReceipt | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "resolve_content_text": "aware_content_service_dto.content.content_service_operation.ResolveContentTextResponse",
        "materialize_content_package": "aware_content_service_dto.content.content_service_operation.MaterializeContentPackageResponse",
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
            return UnknownContentServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownContentServiceResponse(ContentServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ResolveContentTextRequest(ContentServiceRequest):
    # Discriminator Tag
    operation: Literal["resolve_content_text"] = "resolve_content_text"

    # Attributes
    content_id: UUID | None = Field(default=None)
    content_class_instance_identity_id: UUID | None = Field(default=None)
    content_class_config_id: UUID | None = Field(default=None)
    media_type: str = Field(default="text/plain")
    include_parts: bool = Field(default=True)
    max_chars: int | None = Field(default=None)


class ResolveContentTextResponse(ContentServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_content_text"] = "resolve_content_text"

    # Attributes
    resolution: ContentTextResolutionV1 | None = Field(default=None)


class MaterializeContentPackageRequest(ContentServiceRequest):
    # Discriminator Tag
    operation: Literal["materialize_content_package"] = "materialize_content_package"

    # Attributes
    package_export: ContentPackageExportDocumentV1


class MaterializeContentPackageResponse(ContentServiceResponse):
    # Discriminator Tag
    operation: Literal["materialize_content_package"] = "materialize_content_package"

    # Attributes
    materialization: ContentPackageMaterializationResultV1 | None = Field(default=None)
