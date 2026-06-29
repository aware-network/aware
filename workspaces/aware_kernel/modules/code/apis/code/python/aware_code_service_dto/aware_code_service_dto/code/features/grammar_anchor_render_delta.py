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
from aware_code_service_dto.code.features.grammar_anchor_binding import CodeGrammarAnchorBindingResolutionStatus
from aware_code_service_dto.code.features.package_distribution import CodeLanguage
from aware_code_service_dto.code.service import (
    CodeServiceRequest,
    CodeServiceResponse,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_service_dto.code.features.grammar_anchor_binding import CodeGrammarAnchorBinding
    from aware_code_service_dto.code.features.grammar_anchor_binding import CodeGrammarAnchorTextEvidence
    from aware_code_service_dto.code.features.grammar_anchor_binding import CodeGrammarAnchorTextTargetEvidence
    from aware_code_service_dto.code.features.grammar_anchor_binding import CodeGraphFieldSelector
    from aware_code_service_dto.code.features.package_delta import CodePackageDelta


class CodeGrammarAnchorRenderSource(BaseModel):
    """Source text context accepted by the grammar-anchor renderer."""

    # Attributes
    source_key: str
    language: CodeLanguage = Field(default=CodeLanguage.aware)
    relative_path: str | None = Field(default=None)
    source_text: str | None = Field(default=None)
    before_hash: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeGrammarAnchorRenderTargetKind(Enum):
    """Render target resolution mode for one grammar-anchor render replacement."""

    grammar_anchor = "grammar_anchor"
    text_span = "text_span"


class CodeGrammarAnchorRenderSpanTarget(BaseModel):
    """Typed byte-span target for render deltas that cannot yet use parser anchors."""

    # Attributes
    target_key: str | None = Field(default=None)
    source_key: str | None = Field(default=None)
    relative_path: str | None = Field(default=None)
    language: CodeLanguage | None = Field(default=None)
    byte_start: int
    byte_end: int
    before_text_hash: str | None = Field(default=None)
    before_source_hash: str | None = Field(default=None)
    graph_selector: CodeGraphFieldSelector | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeGrammarAnchorRenderReplacement(BaseModel):
    """Replacement requested for one grammar-anchor binding."""

    # Attributes
    replacement_key: str | None = Field(default=None)
    binding_key: str | None = Field(default=None)
    source_key: str | None = Field(default=None)
    target_kind: CodeGrammarAnchorRenderTargetKind = Field(default=CodeGrammarAnchorRenderTargetKind.grammar_anchor)
    span_target: CodeGrammarAnchorRenderSpanTarget | None = Field(default=None)
    replacement_text: str
    before_text_hash: str | None = Field(default=None)
    event_ref: str | None = Field(default=None)
    semantic_key: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeGrammarAnchorRenderEntry(BaseModel):
    """One resolved grammar-anchor render operation."""

    # Attributes
    replacement_key: str | None = Field(default=None)
    binding_key: str | None = Field(default=None)
    source_key: str | None = Field(default=None)
    relative_path: str | None = Field(default=None)
    target_kind: CodeGrammarAnchorRenderTargetKind = Field(default=CodeGrammarAnchorRenderTargetKind.grammar_anchor)
    span_target: CodeGrammarAnchorRenderSpanTarget | None = Field(default=None)
    text_evidence: CodeGrammarAnchorTextEvidence | None = Field(default=None)
    text_target: CodeGrammarAnchorTextTargetEvidence | None = Field(default=None)
    before_source_hash: str | None = Field(default=None)
    after_source_hash: str | None = Field(default=None)
    applied: bool = Field(default=False)
    skipped_reason: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class ResolveCodeGrammarAnchorRenderDeltaRequest(CodeServiceRequest):
    """Resolve grammar-anchor graph-to-source replacements into guarded Code deltas."""

    # Discriminator Tag
    operation: Literal["resolve_grammar_anchor_render_delta"] = "resolve_grammar_anchor_render_delta"

    # Attributes
    package_name: str | None = Field(default=None)
    package_root: str | None = Field(default=None)
    sources_root: str | None = Field(default=None)
    baseline_fingerprint: str | None = Field(default=None)
    baseline_fingerprint_algorithm: str = Field(default="sha256")
    bindings: list[CodeGrammarAnchorBinding] = Field(default_factory=list)
    sources: list[CodeGrammarAnchorRenderSource] = Field(default_factory=list)
    replacements: list[CodeGrammarAnchorRenderReplacement] = Field(default_factory=list)
    strict: bool = Field(default=True)
    metadata: JsonObject | None = Field(default=None)


class ResolveCodeGrammarAnchorRenderDeltaResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_grammar_anchor_render_delta"] = "resolve_grammar_anchor_render_delta"

    # Attributes
    resolved: bool = Field(default=False)
    status: CodeGrammarAnchorBindingResolutionStatus = Field(default=CodeGrammarAnchorBindingResolutionStatus.blocked)
    diagnostics: list[str] = Field(default_factory=list)
    render_entries: list[CodeGrammarAnchorRenderEntry] = Field(default_factory=list)
    package_delta: CodePackageDelta | None = Field(default=None)
    binding_count: int = Field(default=0)
    source_count: int = Field(default=0)
    replacement_count: int = Field(default=0)
    render_entry_count: int = Field(default=0)
    path_count: int = Field(default=0)
