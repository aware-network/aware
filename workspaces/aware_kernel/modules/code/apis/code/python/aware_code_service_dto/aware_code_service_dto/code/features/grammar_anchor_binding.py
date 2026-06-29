from __future__ import annotations

# Standard
from enum import Enum
from typing import Literal
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


class CodeGrammarAnchorBindingDirection(Enum):
    """Direction supported by one grammar-anchor graph binding."""

    bidirectional = "bidirectional"
    source_to_graph = "source_to_graph"
    graph_to_source = "graph_to_source"


class CodeGrammarAnchorBindingResolutionStatus(Enum):
    """Resolution status for grammar-anchor graph binding evidence."""

    resolved = "resolved"
    blocked = "blocked"
    skipped = "skipped"


class CodeGraphFieldSelector(BaseModel):
    """Code-owned graph selector for one semantic graph field."""

    # Attributes
    provider_key: str | None = Field(default=None)
    semantic_owner: str | None = Field(default=None)
    subject_kind: str | None = Field(default=None)
    subject_type: str | None = Field(default=None)
    semantic_key: str | None = Field(default=None)
    object_key: str | None = Field(default=None)
    field_path: str | None = Field(default=None)
    field_name: str | None = Field(default=None)
    class_config_id: UUID | None = Field(default=None)
    class_fqn: str | None = Field(default=None)
    class_name: str | None = Field(default=None)
    class_config_attribute_config_id: UUID | None = Field(default=None)
    attribute_config_id: UUID | None = Field(default=None)
    attribute_name: str | None = Field(default=None)
    attribute_path: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeGraphAttributeSelector(CodeGraphFieldSelector):
    """Compatibility selector for one OCG class attribute field."""

    # Attributes
    compatibility_selector_kind: str = Field(default="ocg_attribute")


class CodeGrammarAnchorBinding(BaseModel):
    """Binding from one tree-sitter grammar rule field anchor to one graph selector."""

    # Attributes
    binding_key: str
    language: str = Field(default="aware")
    grammar_profile_key: str | None = Field(default=None)
    provider_key: str | None = Field(default=None)
    lane_key: str | None = Field(default=None)
    grammar_rule_name: str
    anchor_field_path: str
    anchor_role: str = Field(default="graph_attribute_value")
    graph_selector: CodeGraphFieldSelector
    value_domain: str = Field(default="text")
    direction: CodeGrammarAnchorBindingDirection = Field(default=CodeGrammarAnchorBindingDirection.bidirectional)
    renderer_key: str | None = Field(default=None)
    render_policy_key: str | None = Field(default=None)
    compatibility_section_type: str | None = Field(default=None)
    compatibility_segment_name: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeGrammarAnchorFixture(BaseModel):
    """Source fixture used to prove a grammar anchor resolves through the parser."""

    # Attributes
    fixture_key: str
    source_text: str
    binding_key: str | None = Field(default=None)
    expected_text: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeGrammarAnchorTextEvidence(BaseModel):
    """Resolved parser evidence for one grammar-anchor graph binding."""

    # Attributes
    binding_key: str
    fixture_key: str | None = Field(default=None)
    language: str = Field(default="aware")
    grammar_rule_name: str
    anchor_field_path: str
    parser_node_kind: str | None = Field(default=None)
    anchor_node_kind: str | None = Field(default=None)
    relative_path: str | None = Field(default=None)
    content_part_text_id: UUID | None = Field(default=None)
    content_part_text_segment_id: UUID | None = Field(default=None)
    byte_start: int
    byte_end: int
    text: str | None = Field(default=None)
    text_hash: str | None = Field(default=None)
    resolved_object_key: str | None = Field(default=None)
    resolved_attribute_id: UUID | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeGrammarAnchorGraphChangeDraft(BaseModel):
    """Draft graph change implied by a source text change over a grammar anchor."""

    # Attributes
    binding_key: str
    operation: str = Field(default="update")
    graph_selector: CodeGraphFieldSelector
    before_value: str | None = Field(default=None)
    after_value: str | None = Field(default=None)
    text_evidence: CodeGrammarAnchorTextEvidence | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeGrammarAnchorTextTargetEvidence(BaseModel):
    """Text target evidence for a graph-to-source update over a grammar anchor."""

    # Attributes
    binding_key: str
    graph_selector: CodeGraphFieldSelector
    text_evidence: CodeGrammarAnchorTextEvidence | None = Field(default=None)
    replacement_text: str | None = Field(default=None)
    before_hash: str | None = Field(default=None)
    after_hash: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class ValidateCodeGrammarAnchorBindingRequest(CodeServiceRequest):
    """Validate grammar-anchor graph bindings and optional parse fixtures."""

    # Discriminator Tag
    operation: Literal["validate_grammar_anchor_binding"] = "validate_grammar_anchor_binding"

    # Attributes
    bindings: list[CodeGrammarAnchorBinding] = Field(default_factory=list)
    fixtures: list[CodeGrammarAnchorFixture] = Field(default_factory=list)
    strict: bool = Field(default=True)


class ValidateCodeGrammarAnchorBindingResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["validate_grammar_anchor_binding"] = "validate_grammar_anchor_binding"

    # Attributes
    valid: bool = Field(default=False)
    status: CodeGrammarAnchorBindingResolutionStatus = Field(default=CodeGrammarAnchorBindingResolutionStatus.blocked)
    diagnostics: list[str] = Field(default_factory=list)
    binding_count: int = Field(default=0)
    fixture_count: int = Field(default=0)
    evidence: list[CodeGrammarAnchorTextEvidence] = Field(default_factory=list)


class ResolveCodeGrammarAnchorBindingEvidenceRequest(CodeServiceRequest):
    """Resolve grammar-anchor fixtures into byte evidence and read-only graph/text drafts."""

    # Discriminator Tag
    operation: Literal["resolve_grammar_anchor_binding_evidence"] = "resolve_grammar_anchor_binding_evidence"

    # Attributes
    bindings: list[CodeGrammarAnchorBinding] = Field(default_factory=list)
    fixtures: list[CodeGrammarAnchorFixture] = Field(default_factory=list)
    replacement_values: JsonObject | None = Field(default=None)
    strict: bool = Field(default=True)


class ResolveCodeGrammarAnchorBindingEvidenceResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_grammar_anchor_binding_evidence"] = "resolve_grammar_anchor_binding_evidence"

    # Attributes
    resolved: bool = Field(default=False)
    status: CodeGrammarAnchorBindingResolutionStatus = Field(default=CodeGrammarAnchorBindingResolutionStatus.blocked)
    diagnostics: list[str] = Field(default_factory=list)
    evidence: list[CodeGrammarAnchorTextEvidence] = Field(default_factory=list)
    graph_change_drafts: list[CodeGrammarAnchorGraphChangeDraft] = Field(default_factory=list)
    text_targets: list[CodeGrammarAnchorTextTargetEvidence] = Field(default_factory=list)
    binding_count: int = Field(default=0)
    fixture_count: int = Field(default=0)
    evidence_count: int = Field(default=0)
