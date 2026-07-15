from __future__ import annotations

# Standard
from enum import Enum
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
    from aware_code_service_dto.code.features.grammar_anchor_render_delta import (
        ResolveCodeGrammarAnchorRenderDeltaRequest,
    )
    from aware_code_service_dto.code.features.package_delta import CodePackageDelta
    from aware_code_service_dto.code.features.package_layout import CodePackageLayoutContract
    from aware_code_service_dto.code.features.section_delta import CodeSectionDeltaSet
    from aware_code_service_dto.code.features.semantic_contract import CodeSemanticContract


class CodeGeneratedMaterializationDeltaMode(Enum):
    """Generated materialization delta status accepted at the Code API boundary."""

    package_delta_ready = "package_delta_ready"
    grammar_anchor_render_ready = "grammar_anchor_render_ready"
    section_delta_ready = "section_delta_ready"
    fallback_full_render = "fallback_full_render"
    blocked = "blocked"
    not_required = "not_required"


class CodeGeneratedRendererDeltaOperationKind(Enum):
    """Renderer operation shape behind one generated materialization delta entry."""

    replace_anchor = "replace_anchor"
    replace_section = "replace_section"
    insert_section = "insert_section"
    delete_section = "delete_section"
    fallback_full_render = "fallback_full_render"


class CodeGeneratedMaterializationTargetRef(BaseModel):
    """Renderer/materialization target identity for generated artifact deltas."""

    # Attributes
    target_key: str | None = Field(default=None)
    target_index: int | None = Field(default=None)
    provider_key: str | None = Field(default=None)
    semantic_owner: str | None = Field(default=None)
    target_language: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    package_root: str | None = Field(default=None)
    sources_root: str | None = Field(default=None)
    renderer_key: str | None = Field(default=None)
    renderer_kind: str | None = Field(default=None)
    renderer_profile: str | None = Field(default=None)
    materialization_source: str | None = Field(default=None)
    artifact_family: str | None = Field(default=None)
    artifact_role: str | None = Field(default=None)
    output_key: str | None = Field(default=None)
    relative_path: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeGeneratedRendererAnchorRef(BaseModel):
    """Renderer-owned anchor identity inside one generated artifact."""

    # Attributes
    anchor_key: str
    anchor_path: str | None = Field(default=None)
    anchor_role: str | None = Field(default=None)
    renderer_key: str | None = Field(default=None)
    renderer_profile: str | None = Field(default=None)
    materialization_source: str | None = Field(default=None)
    target_language: str | None = Field(default=None)
    section_type: str | None = Field(default=None)
    segment_name: str | None = Field(default=None)
    graph_selector: JsonObject | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeGeneratedMaterializationEventRef(BaseModel):
    """Semantic event reference accepted by generated materialization delta producers."""

    # Attributes
    event_key: str
    semantic_key: str | None = Field(default=None)
    verb: str | None = Field(default=None)
    subject_type: str | None = Field(default=None)
    source: str | None = Field(default=None)
    source_refs: list[str] = Field(default_factory=list)
    payload: JsonObject | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeGeneratedMaterializationActionBinding(BaseModel):
    """Action binding from one semantic event to one generated materialization target."""

    # Attributes
    action_key: str
    event_key: str
    action_type: str = Field(default="generated_materialization_delta")
    target: CodeGeneratedMaterializationTargetRef | None = Field(default=None)
    policy_key: str | None = Field(default=None)
    renderer_key: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeGeneratedRendererDeltaOperation(BaseModel):
    """One structured renderer operation that explains a generated artifact delta."""

    # Attributes
    operation_key: str | None = Field(default=None)
    kind: CodeGeneratedRendererDeltaOperationKind = Field(
        default=CodeGeneratedRendererDeltaOperationKind.replace_anchor
    )
    target: CodeGeneratedMaterializationTargetRef | None = Field(default=None)
    anchor: CodeGeneratedRendererAnchorRef | None = Field(default=None)
    renderer_key: str | None = Field(default=None)
    renderer_profile: str | None = Field(default=None)
    before_hash: str | None = Field(default=None)
    after_hash: str | None = Field(default=None)
    content_text: str | None = Field(default=None)
    replacement_text: str | None = Field(default=None)
    event_refs: list[str] = Field(default_factory=list)
    semantic_keys: list[str] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class CodeGeneratedMaterializationDeltaEntry(BaseModel):
    """One renderer-generated materialization delta entry."""

    # Attributes
    entry_key: str | None = Field(default=None)
    mode: CodeGeneratedMaterializationDeltaMode = Field(default=CodeGeneratedMaterializationDeltaMode.blocked)
    target: CodeGeneratedMaterializationTargetRef
    package_delta: CodePackageDelta | None = Field(default=None)
    grammar_anchor_render_delta: ResolveCodeGrammarAnchorRenderDeltaRequest | None = Field(default=None)
    section_delta: CodeSectionDeltaSet | None = Field(default=None)
    artifact_family: str | None = Field(default=None)
    artifact_role: str | None = Field(default=None)
    artifact_key: str | None = Field(default=None)
    relative_path: str | None = Field(default=None)
    before_hash: str | None = Field(default=None)
    after_hash: str | None = Field(default=None)
    renderer_operations: list[CodeGeneratedRendererDeltaOperation] = Field(default_factory=list)
    event_refs: list[str] = Field(default_factory=list)
    semantic_keys: list[str] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class CodeGeneratedMaterializationSkippedTarget(BaseModel):
    """Skipped target evidence returned by a generated materialization delta producer."""

    # Attributes
    target: CodeGeneratedMaterializationTargetRef | None = Field(default=None)
    reason: str
    event_refs: list[str] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class CodeGeneratedMaterializationDeltaRequest(BaseModel):
    """API-owned request envelope for renderer-generated materialization deltas."""

    # Attributes
    provider_key: str
    semantic_owner: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    package_root: str | None = Field(default=None)
    sources_root: str | None = Field(default=None)
    product_intent: str | None = Field(default=None)
    baseline_fingerprint: str | None = Field(default=None)
    baseline_fingerprint_algorithm: str = Field(default="sha256")
    layout_contract: CodePackageLayoutContract | None = Field(default=None)
    semantic_contract: CodeSemanticContract | None = Field(default=None)
    events: list[CodeGeneratedMaterializationEventRef] = Field(default_factory=list)
    action_bindings: list[CodeGeneratedMaterializationActionBinding] = Field(default_factory=list)
    targets: list[CodeGeneratedMaterializationTargetRef] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class CodeGeneratedMaterializationDeltaResult(BaseModel):
    """API-owned result envelope for renderer-generated materialization deltas."""

    # Attributes
    provider_key: str
    semantic_owner: str | None = Field(default=None)
    available: bool = Field(default=False)
    mode: CodeGeneratedMaterializationDeltaMode = Field(default=CodeGeneratedMaterializationDeltaMode.blocked)
    entries: list[CodeGeneratedMaterializationDeltaEntry] = Field(default_factory=list)
    skipped_targets: list[CodeGeneratedMaterializationSkippedTarget] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    fingerprint: str | None = Field(default=None)
    receipt_refs: list[str] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class ValidateCodeGeneratedMaterializationDeltaRequest(CodeServiceRequest):
    """Validate generated materialization delta request/result evidence."""

    # Discriminator Tag
    operation: Literal["validate_generated_materialization_delta"] = "validate_generated_materialization_delta"

    # Attributes
    delta_request: CodeGeneratedMaterializationDeltaRequest
    result: CodeGeneratedMaterializationDeltaResult | None = Field(default=None)
    strict: bool = Field(default=True)


class ValidateCodeGeneratedMaterializationDeltaResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["validate_generated_materialization_delta"] = "validate_generated_materialization_delta"

    # Attributes
    valid: bool = Field(default=False)
    diagnostics: list[str] = Field(default_factory=list)
    event_count: int = Field(default=0)
    action_count: int = Field(default=0)
    target_count: int = Field(default=0)
    entry_count: int = Field(default=0)
    skipped_target_count: int = Field(default=0)
    renderer_operation_count: int = Field(default=0)
    package_delta_entry_count: int = Field(default=0)
    grammar_anchor_render_entry_count: int = Field(default=0)
    section_delta_entry_count: int = Field(default=0)


class NormalizeCodeGeneratedMaterializationDeltaRequest(CodeServiceRequest):
    """Normalize generated materialization delta request/result evidence."""

    # Discriminator Tag
    operation: Literal["normalize_generated_materialization_delta"] = "normalize_generated_materialization_delta"

    # Attributes
    delta_request: CodeGeneratedMaterializationDeltaRequest
    result: CodeGeneratedMaterializationDeltaResult | None = Field(default=None)


class NormalizeCodeGeneratedMaterializationDeltaResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["normalize_generated_materialization_delta"] = "normalize_generated_materialization_delta"

    # Attributes
    delta_request: CodeGeneratedMaterializationDeltaRequest | None = Field(default=None)
    result: CodeGeneratedMaterializationDeltaResult | None = Field(default=None)


class FingerprintCodeGeneratedMaterializationDeltaRequest(CodeServiceRequest):
    """Fingerprint generated materialization delta request/result evidence."""

    # Discriminator Tag
    operation: Literal["fingerprint_generated_materialization_delta"] = "fingerprint_generated_materialization_delta"

    # Attributes
    delta_request: CodeGeneratedMaterializationDeltaRequest
    result: CodeGeneratedMaterializationDeltaResult | None = Field(default=None)
    algorithm: str = Field(default="sha256")


class FingerprintCodeGeneratedMaterializationDeltaResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["fingerprint_generated_materialization_delta"] = "fingerprint_generated_materialization_delta"

    # Attributes
    fingerprint: str | None = Field(default=None)
    event_count: int = Field(default=0)
    action_count: int = Field(default=0)
    target_count: int = Field(default=0)
    entry_count: int = Field(default=0)
    renderer_operation_count: int = Field(default=0)
    package_delta_entry_count: int = Field(default=0)
    grammar_anchor_render_entry_count: int = Field(default=0)
    section_delta_entry_count: int = Field(default=0)


class ResolveCodeGeneratedMaterializationPackageDeltaRequest(CodeServiceRequest):
    """Resolve renderer-generated materialization output into a CodePackageDelta."""

    # Discriminator Tag
    operation: Literal["resolve_generated_materialization_package_delta"] = (
        "resolve_generated_materialization_package_delta"
    )

    # Attributes
    delta_request: CodeGeneratedMaterializationDeltaRequest
    result: CodeGeneratedMaterializationDeltaResult
    layout_contract: CodePackageLayoutContract | None = Field(default=None)
    semantic_contract: CodeSemanticContract | None = Field(default=None)
    strict: bool = Field(default=True)


class ResolveCodeGeneratedMaterializationPackageDeltaResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_generated_materialization_package_delta"] = (
        "resolve_generated_materialization_package_delta"
    )

    # Attributes
    resolved: bool = Field(default=False)
    package_delta: CodePackageDelta | None = Field(default=None)
    diagnostics: list[str] = Field(default_factory=list)
    event_count: int = Field(default=0)
    action_count: int = Field(default=0)
    target_count: int = Field(default=0)
    skipped_target_count: int = Field(default=0)
    entry_count: int = Field(default=0)
    path_count: int = Field(default=0)
    renderer_operation_count: int = Field(default=0)
    package_delta_entry_count: int = Field(default=0)
    grammar_anchor_render_entry_count: int = Field(default=0)
    section_delta_entry_count: int = Field(default=0)
