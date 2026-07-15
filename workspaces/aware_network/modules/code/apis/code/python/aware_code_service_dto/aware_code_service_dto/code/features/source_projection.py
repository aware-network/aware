from __future__ import annotations

# Standard
from typing import (
    Literal,
    TYPE_CHECKING,
)

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Service Dto
from aware_code_service_dto.code.service import (
    CodeServiceRequest,
    CodeServiceResponse,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_service_dto.code.features.package_delta import CodePackageDelta
    from aware_code_service_dto.code.features.package_layout import CodePackageLayoutContract
    from aware_code_service_dto.code.features.section_delta import CodeSectionDeltaSet
    from aware_code_service_dto.code.features.section_delta import CodeSectionRef
    from aware_code_service_dto.code.features.semantic_contract import CodeSemanticContract


class CodeSourceProjectionEventRef(BaseModel):
    """Semantic event reference accepted by the Code-owned source_projection capability."""

    # Attributes
    event_key: str
    semantic_key: str | None = Field(default=None)
    verb: str | None = Field(default=None)
    subject_type: str | None = Field(default=None)
    source: str | None = Field(default=None)
    source_refs: list[str] = Field(default_factory=list)
    payload: JsonObject | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeSourceProjectionActionBinding(BaseModel):
    """Source-projection action binding over one semantic event."""

    # Attributes
    action_key: str
    event_key: str
    action_type: str = Field(default="source_projection")
    policy_key: str | None = Field(default=None)
    product_intent: str | None = Field(default=None)
    target_language: str | None = Field(default=None)
    target_section: CodeSectionRef | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeSourceProjectionSkippedEvent(BaseModel):
    """Skipped event/action evidence returned by a source_projection provider."""

    # Attributes
    event_key: str | None = Field(default=None)
    action_key: str | None = Field(default=None)
    semantic_key: str | None = Field(default=None)
    reason: str
    metadata: JsonObject | None = Field(default=None)


class CodeSourceProjectionRequest(BaseModel):
    """API-owned request envelope for semantic-event source projection."""

    # Attributes
    provider_key: str
    semantic_owner: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    package_root: str | None = Field(default=None)
    sources_root: str | None = Field(default=None)
    product_intent: str | None = Field(default=None)
    target_language: str | None = Field(default=None)
    baseline_fingerprint: str | None = Field(default=None)
    baseline_fingerprint_algorithm: str = Field(default="sha256")
    layout_contract: CodePackageLayoutContract | None = Field(default=None)
    semantic_contract: CodeSemanticContract | None = Field(default=None)
    events: list[CodeSourceProjectionEventRef] = Field(default_factory=list)
    action_bindings: list[CodeSourceProjectionActionBinding] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class CodeSourceProjectionResult(BaseModel):
    """API-owned result envelope for provider-produced source projection."""

    # Attributes
    provider_key: str
    semantic_owner: str | None = Field(default=None)
    projected: bool = Field(default=False)
    delta_set: CodeSectionDeltaSet | None = Field(default=None)
    diagnostics: list[str] = Field(default_factory=list)
    skipped_events: list[CodeSourceProjectionSkippedEvent] = Field(default_factory=list)
    fingerprint: str | None = Field(default=None)
    receipt_refs: list[str] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class ValidateCodeSourceProjectionRequest(CodeServiceRequest):
    """Validate source_projection request/result evidence before provider or consumer use."""

    # Discriminator Tag
    operation: Literal["validate_source_projection"] = "validate_source_projection"

    # Attributes
    projection: CodeSourceProjectionRequest
    result: CodeSourceProjectionResult | None = Field(default=None)
    strict: bool = Field(default=True)


class ValidateCodeSourceProjectionResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["validate_source_projection"] = "validate_source_projection"

    # Attributes
    valid: bool = Field(default=False)
    diagnostics: list[str] = Field(default_factory=list)
    event_count: int = Field(default=0)
    action_count: int = Field(default=0)
    skipped_event_count: int = Field(default=0)
    has_delta_set: bool = Field(default=False)


class NormalizeCodeSourceProjectionRequest(CodeServiceRequest):
    """Normalize source_projection request/result evidence into stable DTO shape."""

    # Discriminator Tag
    operation: Literal["normalize_source_projection"] = "normalize_source_projection"

    # Attributes
    projection: CodeSourceProjectionRequest
    result: CodeSourceProjectionResult | None = Field(default=None)


class NormalizeCodeSourceProjectionResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["normalize_source_projection"] = "normalize_source_projection"

    # Attributes
    projection: CodeSourceProjectionRequest | None = Field(default=None)
    result: CodeSourceProjectionResult | None = Field(default=None)


class FingerprintCodeSourceProjectionRequest(CodeServiceRequest):
    """Fingerprint source_projection request/result evidence for preview and receipt correlation."""

    # Discriminator Tag
    operation: Literal["fingerprint_source_projection"] = "fingerprint_source_projection"

    # Attributes
    projection: CodeSourceProjectionRequest
    result: CodeSourceProjectionResult | None = Field(default=None)
    algorithm: str = Field(default="sha256")


class FingerprintCodeSourceProjectionResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["fingerprint_source_projection"] = "fingerprint_source_projection"

    # Attributes
    fingerprint: str | None = Field(default=None)
    event_count: int = Field(default=0)
    action_count: int = Field(default=0)
    has_delta_set: bool = Field(default=False)


class ResolveCodeSourceProjectionPackageDeltaRequest(CodeServiceRequest):
    """Resolve provider-produced source_projection output into a CodePackageDelta."""

    # Discriminator Tag
    operation: Literal["resolve_source_projection_package_delta"] = "resolve_source_projection_package_delta"

    # Attributes
    projection: CodeSourceProjectionRequest
    result: CodeSourceProjectionResult
    layout_contract: CodePackageLayoutContract | None = Field(default=None)
    semantic_contract: CodeSemanticContract | None = Field(default=None)
    strict: bool = Field(default=True)


class ResolveCodeSourceProjectionPackageDeltaResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_source_projection_package_delta"] = "resolve_source_projection_package_delta"

    # Attributes
    resolved: bool = Field(default=False)
    package_delta: CodePackageDelta | None = Field(default=None)
    diagnostics: list[str] = Field(default_factory=list)
    event_count: int = Field(default=0)
    action_count: int = Field(default=0)
    skipped_event_count: int = Field(default=0)
    entry_count: int = Field(default=0)
    path_count: int = Field(default=0)
