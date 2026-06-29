from __future__ import annotations

# Standard
from enum import Enum
from typing import (
    Literal,
    TYPE_CHECKING,
)
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Service Dto
from aware_code_service_dto.code.features.package_common import CodePackagePathRole
from aware_code_service_dto.code.features.package_distribution import CodeLanguage
from aware_code_service_dto.code.service import (
    CodeServiceRequest,
    CodeServiceResponse,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_service_dto.code.features.content_plan import CodeContentPlan


class CodePackageDeltaKind(Enum):
    """Raw Code delta operation kind."""

    create = "create"
    update = "update"
    delete = "delete"


class CodePackageDeltaAuthorityKind(Enum):
    """How a raw CodePackageDelta entered the Code API boundary."""

    local_fs_view = "local_fs_view"
    remote_workspace_view = "remote_workspace_view"
    code_package_delta = "code_package_delta"
    semantic_materialization = "semantic_materialization"
    tool_materialization = "tool_materialization"


class CodePackageDeltaProducerRef(BaseModel):
    """Generic producer pointer for CodePackageDelta output."""

    # Attributes
    provider_key: str
    producer_key: str
    producer_kind: str | None = Field(default=None)
    provider_payload: JsonObject | None = Field(default=None)


class CodePackageDeltaProduction(BaseModel):
    """One producer emission for CodePackageDelta output."""

    # Attributes
    producer: CodePackageDeltaProducerRef
    input_code_package_id: UUID | None = Field(default=None)
    input_object_instance_graph_commit_id: UUID | None = Field(default=None)
    input_digest: str | None = Field(default=None)
    output_digest: str | None = Field(default=None)
    emission_payload: JsonObject | None = Field(default=None)


class CodePackageDeltaPath(BaseModel):
    """One package-relative code path delta."""

    # Attributes
    relative_path: str
    kind: CodePackageDeltaKind
    content_text: str | None = Field(default=None)
    content_plan: CodeContentPlan | None = Field(default=None)
    before_hash: str | None = Field(default=None)
    after_hash: str | None = Field(default=None)
    size_bytes: int | None = Field(default=None)
    language: CodeLanguage | None = Field(default=None)
    is_structural: bool | None = Field(default=None)
    path_role: CodePackagePathRole = Field(default=CodePackagePathRole.authored_source)
    production: CodePackageDeltaProduction | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodePackageDelta(BaseModel):
    """API-owned CodePackage delta DTO for local and remote semantic operations."""

    # Attributes
    package_name: str | None = Field(default=None)
    package_root: str | None = Field(default=None)
    sources_root: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    authority: CodePackageDeltaAuthorityKind | None = Field(default=None)
    authority_kind: str | None = Field(default=None)
    source_revision_id: str | None = Field(default=None)
    production: CodePackageDeltaProduction | None = Field(default=None)
    paths: list[CodePackageDeltaPath] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class NormalizeCodePackageDeltaRequest(CodeServiceRequest):
    """Normalize raw package delta input into the public CodePackageDelta DTO."""

    # Discriminator Tag
    operation: Literal["normalize_package_delta"] = "normalize_package_delta"

    # Attributes
    delta: CodePackageDelta


class NormalizeCodePackageDeltaResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["normalize_package_delta"] = "normalize_package_delta"

    # Attributes
    delta: CodePackageDelta | None = Field(default=None)


class FingerprintCodePackageDeltaRequest(CodeServiceRequest):
    """Fingerprint a CodePackageDelta for cache/status/materialization receipts."""

    # Discriminator Tag
    operation: Literal["fingerprint_package_delta"] = "fingerprint_package_delta"

    # Attributes
    delta: CodePackageDelta
    algorithm: str = Field(default="sha256")


class FingerprintCodePackageDeltaResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["fingerprint_package_delta"] = "fingerprint_package_delta"

    # Attributes
    fingerprint: str | None = Field(default=None)
    path_count: int = Field(default=0)


class CodePackageDeltaApplyResult(BaseModel):
    """Result of applying a CodePackageDelta through the CodePackage mutation boundary."""

    # Attributes
    applied_path_count: int = Field(default=0)
    created_path_count: int = Field(default=0)
    updated_path_count: int = Field(default=0)
    deleted_path_count: int = Field(default=0)
    deleted_missing_path_count: int = Field(default=0)
    skipped_path_count: int = Field(default=0)
