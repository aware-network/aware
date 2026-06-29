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
    from aware_code_service_dto.code.features.semantic_contract import CodeSemanticContract


class CodeSemanticAnalysisDiagnostic(BaseModel):
    """Semantic-analysis diagnostic evidence returned by a provider preview."""

    # Attributes
    severity: str
    code: str
    message: str
    source_path: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticAnalysisDependencyRequirement(BaseModel):
    """Semantic-analysis dependency requirement returned by a provider preview."""

    # Attributes
    dependency_key: str
    provider_key: str
    package_name: str
    required_state: str = Field(default="materialized")
    dependency_kind: str = Field(default="semantic_package")
    semantic_owner: str | None = Field(default=None)
    manifest_kind: str | None = Field(default=None)
    package_selector: JsonObject | None = Field(default=None)
    reason: str | None = Field(default=None)
    source_refs: list[str] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticDelta(BaseModel):
    """Provider-owned semantic before/after candidate derived from a CodePackageDelta."""

    # Attributes
    delta_key: str
    semantic_key: str
    verb: str
    subject_type: str
    source: str
    source_refs: list[str] = Field(default_factory=list)
    before_payload: JsonObject | None = Field(default=None)
    after_payload: JsonObject | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticEvent(BaseModel):
    """Provider-owned semantic event candidate derived from semantic deltas."""

    # Attributes
    event_key: str
    semantic_key: str
    verb: str
    subject_type: str
    source: str
    event_type: str = Field(default="semantic_change")
    source_refs: list[str] = Field(default_factory=list)
    delta_keys: list[str] = Field(default_factory=list)
    condition_keys: list[str] = Field(default_factory=list)
    payload: JsonObject | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticTypedOperation(BaseModel):
    """Provider-neutral typed mutation intent derived from semantic source meaning."""

    # Attributes
    operation_key: str
    operation_family: str
    semantic_operation_type: str
    semantic_key: str
    semantic_subject_type: str
    field_path: str | None = Field(default=None)
    event_key: str | None = Field(default=None)
    source: str
    source_refs: list[str] = Field(default_factory=list)
    before_payload: JsonObject | None = Field(default=None)
    after_payload: JsonObject | None = Field(default=None)
    requires_baseline_object_identity: bool = Field(default=False)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticFunctionCallBinding(BaseModel):
    """Function-call action policy over a semantic event."""

    # Attributes
    binding_key: str
    event_key: str
    function_ref: str
    receiver_semantic_key_template: str | None = Field(default=None)
    argument_bindings: JsonObject | None = Field(default=None)
    argument_ref_bindings: JsonObject | None = Field(default=None)
    constant_arguments: JsonObject | None = Field(default=None)
    result_semantic_key_template: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticActionBinding(BaseModel):
    """Declarative action policy over one semantic event."""

    # Attributes
    action_key: str
    event_key: str
    action_type: str
    description: str | None = Field(default=None)
    function_call_binding: CodeSemanticFunctionCallBinding | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticAnalysisChangePreview(BaseModel):
    """Provider-owned semantic-analysis preview over one CodePackageDelta."""

    # Attributes
    changed_source_files: list[str] = Field(default_factory=list)
    affected_semantic_keys: list[str] = Field(default_factory=list)
    required_materializations: list[str] = Field(default_factory=list)
    required_semantic_dependencies: list[CodeSemanticAnalysisDependencyRequirement] = Field(default_factory=list)
    semantic_deltas: list[CodeSemanticDelta] = Field(default_factory=list)
    semantic_events: list[CodeSemanticEvent] = Field(default_factory=list)
    typed_operations: list[CodeSemanticTypedOperation] = Field(default_factory=list)
    action_bindings: list[CodeSemanticActionBinding] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class PreviewCodeSemanticAnalysisPackageDeltaRequest(CodeServiceRequest):
    """Preview semantic meaning for one CodePackageDelta without materialization."""

    # Discriminator Tag
    operation: Literal["preview_semantic_analysis_package_delta"] = "preview_semantic_analysis_package_delta"

    # Attributes
    provider_key: str | None = Field(default=None)
    semantic_owner: str | None = Field(default=None)
    workspace_root: str | None = Field(default=None)
    package_root: str | None = Field(default=None)
    manifest_path: str | None = Field(default=None)
    source_files: list[str] = Field(default_factory=list)
    delta: CodePackageDelta
    layout_contract: CodePackageLayoutContract | None = Field(default=None)
    semantic_contract: CodeSemanticContract | None = Field(default=None)
    include_provider_payload: bool = Field(default=False)
    strict: bool = Field(default=True)
    metadata: JsonObject | None = Field(default=None)


class PreviewCodeSemanticAnalysisPackageDeltaResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["preview_semantic_analysis_package_delta"] = "preview_semantic_analysis_package_delta"

    # Attributes
    previewed: bool = Field(default=False)
    provider_key: str | None = Field(default=None)
    semantic_owner: str | None = Field(default=None)
    delta_fingerprint: str | None = Field(default=None)
    diagnostics: list[CodeSemanticAnalysisDiagnostic] = Field(default_factory=list)
    change_preview: CodeSemanticAnalysisChangePreview | None = Field(default=None)
    blockers: list[str] = Field(default_factory=list)
    available: bool = Field(default=False)
    provider_payload: JsonObject | None = Field(default=None)
