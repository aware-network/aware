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
from aware_code_service_dto.code.service import (
    CodeServiceRequest,
    CodeServiceResponse,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_service_dto.code.features.package_delta import CodePackageDelta
    from aware_code_service_dto.code.features.package_delta import CodePackageDeltaProduction
    from aware_code_service_dto.code.features.package_layout import CodePackageLayoutContract
    from aware_code_service_dto.code.features.semantic_contract import CodeSemanticContract


class CodeSectionDeltaOperationKind(Enum):
    """Section-delta operation kind accepted at the Code API boundary."""

    replace_segment = "replace_segment"
    replace_section = "replace_section"
    insert_before_section = "insert_before_section"
    insert_after_section = "insert_after_section"
    delete_section = "delete_section"


class CodeSegmentContentDomain(Enum):
    """Value domain accepted or emitted by a section segment delta."""

    raw_segment_text = "raw_segment_text"
    semantic_segment_value = "semantic_segment_value"


class CodeNestedMemberInsertPosition(Enum):
    """Nested member insertion position inside a resolved parent section."""

    end = "end"


class CodeSegmentRenderPolicyResolutionStatus(Enum):
    """Segment render policy resolution status."""

    resolved = "resolved"
    blocked = "blocked"
    skipped = "skipped"


class CodeSectionRef(BaseModel):
    """Stable section identity plus parser evidence for a package-relative file."""

    # Attributes
    package_name: str | None = Field(default=None)
    relative_path: str
    language: str | None = Field(default=None)
    section_type: str
    section_id: UUID | None = Field(default=None)
    qualname: str | None = Field(default=None)
    identity_hash: str | None = Field(default=None)
    semantic_key: str | None = Field(default=None)
    source_refs: list[str] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class CodeSegmentRef(BaseModel):
    """Stable segment identity and optional byte/hash evidence inside a section."""

    # Attributes
    segment_name: str
    before_segment_hash: str | None = Field(default=None)
    byte_start: int | None = Field(default=None)
    byte_end: int | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeNestedMemberInsertAnchor(BaseModel):
    """Parser-backed nested member insertion anchor inside a parent CodeSectionRef."""

    # Attributes
    member_section_type: str
    member_qualname: str | None = Field(default=None)
    insert_position: CodeNestedMemberInsertPosition = Field(default=CodeNestedMemberInsertPosition.end)


class CodeSegmentRenderPolicy(BaseModel):
    """Code-owned policy for mapping semantic segment values to raw parser segments."""

    # Attributes
    policy_key: str
    language: str
    section_type: str
    segment_name: str
    content_text_domain: CodeSegmentContentDomain = Field(default=CodeSegmentContentDomain.raw_segment_text)
    rendered_content_text_domain: CodeSegmentContentDomain = Field(default=CodeSegmentContentDomain.raw_segment_text)
    before_hash_domains: list[CodeSegmentContentDomain] = Field(default_factory=list)
    after_hash_domain: CodeSegmentContentDomain = Field(default=CodeSegmentContentDomain.raw_segment_text)
    parser_segment_scope: str | None = Field(default=None)
    renderer_key: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeSegmentRenderPolicyDiagnostic(BaseModel):
    """Diagnostic emitted while resolving Code segment render policies."""

    # Attributes
    severity: str = Field(default="error")
    reason: str
    message: str
    language: str | None = Field(default=None)
    section_type: str | None = Field(default=None)
    segment_name: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeSectionDeltaEntry(BaseModel):
    """One section/segment delta requested against parsed Code section truth."""

    # Attributes
    operation: CodeSectionDeltaOperationKind
    section_ref: CodeSectionRef
    segment_ref: CodeSegmentRef | None = Field(default=None)
    nested_member_insert_anchor: CodeNestedMemberInsertAnchor | None = Field(default=None)
    content_text: str | None = Field(default=None)
    before_hash: str | None = Field(default=None)
    after_hash: str | None = Field(default=None)
    event_ref: str | None = Field(default=None)
    semantic_key: str | None = Field(default=None)
    provider_key: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeSectionDeltaSet(BaseModel):
    """API-owned section-delta DTO for semantic-event to CodePackageDelta resolution."""

    # Attributes
    package_name: str | None = Field(default=None)
    package_root: str | None = Field(default=None)
    sources_root: str | None = Field(default=None)
    baseline_fingerprint: str | None = Field(default=None)
    baseline_fingerprint_algorithm: str = Field(default="sha256")
    production: CodePackageDeltaProduction | None = Field(default=None)
    entries: list[CodeSectionDeltaEntry] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class ValidateCodeSectionDeltaRequest(CodeServiceRequest):
    """Validate section/segment delta intent before resolver execution."""

    # Discriminator Tag
    operation: Literal["validate_section_delta"] = "validate_section_delta"

    # Attributes
    delta_set: CodeSectionDeltaSet
    strict: bool = Field(default=True)


class ValidateCodeSectionDeltaResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["validate_section_delta"] = "validate_section_delta"

    # Attributes
    valid: bool = Field(default=False)
    diagnostics: list[str] = Field(default_factory=list)
    entry_count: int = Field(default=0)


class NormalizeCodeSectionDeltaRequest(CodeServiceRequest):
    """Normalize section/segment delta intent into stable Code API DTO shape."""

    # Discriminator Tag
    operation: Literal["normalize_section_delta"] = "normalize_section_delta"

    # Attributes
    delta_set: CodeSectionDeltaSet


class NormalizeCodeSectionDeltaResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["normalize_section_delta"] = "normalize_section_delta"

    # Attributes
    delta_set: CodeSectionDeltaSet | None = Field(default=None)


class FingerprintCodeSectionDeltaRequest(CodeServiceRequest):
    """Fingerprint a section-delta set for semantic event and resolver receipts."""

    # Discriminator Tag
    operation: Literal["fingerprint_section_delta"] = "fingerprint_section_delta"

    # Attributes
    delta_set: CodeSectionDeltaSet
    algorithm: str = Field(default="sha256")


class FingerprintCodeSectionDeltaResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["fingerprint_section_delta"] = "fingerprint_section_delta"

    # Attributes
    fingerprint: str | None = Field(default=None)
    entry_count: int = Field(default=0)


class ResolveCodeSectionDeltaPackageDeltaRequest(CodeServiceRequest):
    """Resolve a section-delta set to a package text delta."""

    # Discriminator Tag
    operation: Literal["resolve_section_delta_package_delta"] = "resolve_section_delta_package_delta"

    # Attributes
    delta_set: CodeSectionDeltaSet
    layout_contract: CodePackageLayoutContract | None = Field(default=None)
    semantic_contract: CodeSemanticContract | None = Field(default=None)
    strict: bool = Field(default=True)


class ResolveCodeSectionDeltaPackageDeltaResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_section_delta_package_delta"] = "resolve_section_delta_package_delta"

    # Attributes
    resolved: bool = Field(default=False)
    package_delta: CodePackageDelta | None = Field(default=None)
    diagnostics: list[str] = Field(default_factory=list)
    entry_count: int = Field(default=0)
    path_count: int = Field(default=0)


class ResolveCodeSegmentRenderPolicyRequest(CodeServiceRequest):
    """Resolve Code-owned render policy metadata for one or more section segments."""

    # Discriminator Tag
    operation: Literal["resolve_segment_render_policy"] = "resolve_segment_render_policy"

    # Attributes
    language: str = Field(default="aware")
    section_type: str | None = Field(default=None)
    segment_name: str | None = Field(default=None)
    include_unsupported: bool = Field(default=False)
    strict: bool = Field(default=True)
    metadata: JsonObject | None = Field(default=None)


class ResolveCodeSegmentRenderPolicyResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_segment_render_policy"] = "resolve_segment_render_policy"

    # Attributes
    status: CodeSegmentRenderPolicyResolutionStatus = Field(default=CodeSegmentRenderPolicyResolutionStatus.blocked)
    resolved: bool = Field(default=False)
    policies: list[CodeSegmentRenderPolicy] = Field(default_factory=list)
    diagnostics: list[CodeSegmentRenderPolicyDiagnostic] = Field(default_factory=list)
    policy_count: int = Field(default=0)
