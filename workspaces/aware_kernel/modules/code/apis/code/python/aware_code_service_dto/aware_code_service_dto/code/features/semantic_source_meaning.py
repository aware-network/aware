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
    from aware_code_service_dto.code.features.grammar_anchor_binding import CodeGraphFieldSelector
    from aware_code_service_dto.code.features.package_delta import CodePackageDelta
    from aware_code_service_dto.code.features.semantic_analysis import CodeSemanticAnalysisChangePreview
    from aware_code_service_dto.code.features.semantic_analysis import CodeSemanticDelta
    from aware_code_service_dto.code.features.semantic_analysis import CodeSemanticEvent
    from aware_code_service_dto.code.features.semantic_analysis import CodeSemanticTypedOperation


class CodeSemanticSourceMeaningBinding(BaseModel):
    """Declarative source-to-semantic meaning binding over a grammar anchor."""

    # Attributes
    binding_key: str
    language: str = Field(default="aware")
    grammar_profile_key: str | None = Field(default=None)
    grammar_rule_name: str
    anchor_field_path: str
    graph_selector: CodeGraphFieldSelector
    semantic_subject_type: str
    semantic_key_template: str
    semantic_field: str
    anchor_role: str | None = Field(default=None)
    value_domain: str | None = Field(default=None)
    event_key_template: str | None = Field(default=None)
    event_type: str = Field(default="semantic_change")
    condition_keys: list[str] = Field(default_factory=list)
    required: bool = Field(default=True)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticSourceMeaningContract(BaseModel):
    """Code-owned source meaning contract consumed by Workspace and SDK clients."""

    # Attributes
    contract_version: str = Field(default="aware.code.semantic-source-meaning-binding.v1")
    provider_key: str
    semantic_owner: str
    grammar_profile_key: str | None = Field(default=None)
    supported_languages: list[str] = Field(default_factory=list)
    bindings: list[CodeSemanticSourceMeaningBinding] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticSourceMeaningSource(BaseModel):
    """Source text accepted by the semantic source meaning resolver."""

    # Attributes
    source_key: str
    source_text: str
    language: str = Field(default="aware")
    grammar_profile_key: str | None = Field(default=None)
    relative_path: str | None = Field(default=None)
    before_hash: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticSourceDeltaMeaningResolutionMode(Enum):
    """How Code resolved semantic source meaning for a delta-shaped request."""

    source_pair_snapshot = "source_pair_snapshot"
    delta_with_snapshot_fallback = "delta_with_snapshot_fallback"
    delta_with_index_ref = "delta_with_index_ref"
    blocked = "blocked"


class CodeSemanticSourceIndexRef(BaseModel):
    """Opaque source-index reference supplied by Workspace/service session state."""

    # Attributes
    ref_kind: str
    cache_kind: str | None = Field(default=None)
    cache_key: str | None = Field(default=None)
    source_session_id: str | None = Field(default=None)
    source_delta_fingerprint: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    source_revision_id: str | None = Field(default=None)
    source_keys: list[str] = Field(default_factory=list)
    source_hashes: JsonObject | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticSourceDeltaMeaningInput(BaseModel):
    """Delta-shaped source meaning input with explicit source/index context."""

    # Attributes
    delta: CodePackageDelta
    baseline_source_index_ref: CodeSemanticSourceIndexRef | None = Field(default=None)
    current_source_index_ref: CodeSemanticSourceIndexRef | None = Field(default=None)
    baseline_sources: list[CodeSemanticSourceMeaningSource] = Field(default_factory=list)
    current_sources: list[CodeSemanticSourceMeaningSource] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class ResolveCodeSemanticSourceMeaningRequest(CodeServiceRequest):
    """Resolve declarative source meaning through Code-owned grammar source indexes."""

    # Discriminator Tag
    operation: Literal["resolve_semantic_source_meaning"] = "resolve_semantic_source_meaning"

    # Attributes
    contract: CodeSemanticSourceMeaningContract
    current_sources: list[CodeSemanticSourceMeaningSource] = Field(default_factory=list)
    baseline_sources: list[CodeSemanticSourceMeaningSource] = Field(default_factory=list)
    include_noop: bool = Field(default=False)
    metadata: JsonObject | None = Field(default=None)


class ResolveCodeSemanticSourceMeaningResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_semantic_source_meaning"] = "resolve_semantic_source_meaning"

    # Attributes
    resolved: bool = Field(default=False)
    status: str = Field(default="blocked")
    diagnostics: list[str] = Field(default_factory=list)
    contract_version: str | None = Field(default=None)
    provider_key: str | None = Field(default=None)
    semantic_owner: str | None = Field(default=None)
    binding_count: int = Field(default=0)
    resolved_binding_count: int = Field(default=0)
    changed_binding_count: int = Field(default=0)
    semantic_deltas: list[CodeSemanticDelta] = Field(default_factory=list)
    semantic_events: list[CodeSemanticEvent] = Field(default_factory=list)
    typed_operations: list[CodeSemanticTypedOperation] = Field(default_factory=list)
    change_preview: CodeSemanticAnalysisChangePreview | None = Field(default=None)
    source_index_evidence: JsonObject = Field(default_factory=JsonObject)
    metadata: JsonObject | None = Field(default=None)


class ResolveCodeSemanticSourceDeltaMeaningRequest(CodeServiceRequest):
    """Resolve declarative source meaning from a CodePackageDelta plus baseline context."""

    # Discriminator Tag
    operation: Literal["resolve_semantic_source_delta_meaning"] = "resolve_semantic_source_delta_meaning"

    # Attributes
    contract: CodeSemanticSourceMeaningContract
    input: CodeSemanticSourceDeltaMeaningInput
    include_noop: bool = Field(default=False)
    metadata: JsonObject | None = Field(default=None)


class ResolveCodeSemanticSourceDeltaMeaningResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_semantic_source_delta_meaning"] = "resolve_semantic_source_delta_meaning"

    # Attributes
    resolved: bool = Field(default=False)
    status: str = Field(default="blocked")
    meaning_resolution_mode: CodeSemanticSourceDeltaMeaningResolutionMode = Field(
        default=CodeSemanticSourceDeltaMeaningResolutionMode.blocked
    )
    diagnostics: list[str] = Field(default_factory=list)
    required_context: list[str] = Field(default_factory=list)
    contract_version: str | None = Field(default=None)
    provider_key: str | None = Field(default=None)
    semantic_owner: str | None = Field(default=None)
    binding_count: int = Field(default=0)
    resolved_binding_count: int = Field(default=0)
    changed_binding_count: int = Field(default=0)
    semantic_deltas: list[CodeSemanticDelta] = Field(default_factory=list)
    semantic_events: list[CodeSemanticEvent] = Field(default_factory=list)
    typed_operations: list[CodeSemanticTypedOperation] = Field(default_factory=list)
    change_preview: CodeSemanticAnalysisChangePreview | None = Field(default=None)
    source_index_evidence: JsonObject = Field(default_factory=JsonObject)
    metadata: JsonObject | None = Field(default=None)
