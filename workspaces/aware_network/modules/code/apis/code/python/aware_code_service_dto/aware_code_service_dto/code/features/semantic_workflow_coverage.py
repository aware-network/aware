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
    from aware_code_service_dto.code.features.semantic_contract import CodeSemanticContract


class CodeSemanticWorkflowCoverageStatus(Enum):
    """Code-owned semantic workflow coverage status."""

    covered = "covered"
    blocked = "blocked"
    skipped = "skipped"


class CodeSemanticWorkflowCoverageDiagnostic(BaseModel):
    """Diagnostic emitted while resolving semantic workflow grammar/source coverage."""

    # Attributes
    severity: str = Field(default="error")
    reason: str
    message: str
    provider_key: str | None = Field(default=None)
    workflow_key: str | None = Field(default=None)
    ref_kind: str | None = Field(default=None)
    ref: str | None = Field(default=None)
    rule_name: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticWorkflowGrammarRuleEvidence(BaseModel):
    """Grammar-rule evidence attached to a semantic workflow graph-binding ref."""

    # Attributes
    grammar_profile_key: str
    rule_name: str
    provider_key: str
    lane_key: str
    semantic_owner: str
    compiler_owner: str
    code_section_type: str | None = Field(default=None)
    semantic_token_types: list[str] = Field(default_factory=list)
    semantic_token_modifiers: list[str] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticWorkflowGraphBindingCoverage(BaseModel):
    """Coverage result for one workflow graph-binding ref."""

    # Attributes
    graph_binding_ref: str
    rule_name: str
    covered: bool = Field(default=False)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticWorkflowCoverageEntry(BaseModel):
    """Coverage entry for one provider-owned semantic workflow."""

    # Attributes
    provider_key: str
    workflow_key: str
    semantic_owner: str
    stage_keys: list[str] = Field(default_factory=list)
    status: CodeSemanticWorkflowCoverageStatus = Field(default=CodeSemanticWorkflowCoverageStatus.blocked)
    covered: bool = Field(default=False)
    grammar_profile_refs: list[str] = Field(default_factory=list)
    source_meaning_refs: list[str] = Field(default_factory=list)
    ontology_feature_refs: list[str] = Field(default_factory=list)
    graph_binding_refs: list[str] = Field(default_factory=list)
    grammar_rule_evidence: list[CodeSemanticWorkflowGrammarRuleEvidence] = Field(default_factory=list)
    graph_binding_coverage: list[CodeSemanticWorkflowGraphBindingCoverage] = Field(default_factory=list)
    diagnostics: list[CodeSemanticWorkflowCoverageDiagnostic] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class ResolveCodeSemanticWorkflowCoverageRequest(CodeServiceRequest):
    """Resolve workflow grammar/source/graph-binding coverage from semantic contracts."""

    # Discriminator Tag
    operation: Literal["resolve_semantic_workflow_coverage"] = "resolve_semantic_workflow_coverage"

    # Attributes
    profile_key: str | None = Field(default=None)
    language: str = Field(default="aware")
    backend_key: str | None = Field(default=None)
    provider_keys: list[str] = Field(default_factory=list)
    workflow_keys: list[str] = Field(default_factory=list)
    semantic_contracts: list[CodeSemanticContract] = Field(default_factory=list)
    include_current_code_sections: bool = Field(default=False)
    strict: bool = Field(default=True)
    metadata: JsonObject | None = Field(default=None)


class ResolveCodeSemanticWorkflowCoverageResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_semantic_workflow_coverage"] = "resolve_semantic_workflow_coverage"

    # Attributes
    status: CodeSemanticWorkflowCoverageStatus = Field(default=CodeSemanticWorkflowCoverageStatus.blocked)
    covered: bool = Field(default=False)
    entries: list[CodeSemanticWorkflowCoverageEntry] = Field(default_factory=list)
    diagnostics: list[CodeSemanticWorkflowCoverageDiagnostic] = Field(default_factory=list)
    missing_provider_keys: list[str] = Field(default_factory=list)
    invalid_rule_names: list[str] = Field(default_factory=list)
    provider_count: int = Field(default=0)
    workflow_count: int = Field(default=0)
    covered_workflow_count: int = Field(default=0)
