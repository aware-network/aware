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
    from aware_code_service_dto.code.features.semantic_source_meaning import CodeSemanticSourceMeaningContract


class CodeGrammarProfileResolutionStatus(Enum):
    """Code-owned grammar profile resolution status."""

    resolved = "resolved"
    blocked = "blocked"
    skipped = "skipped"


class CodeGrammarBackendDescriptor(BaseModel):
    """Code-owned grammar backend descriptor for one language/profile resolver."""

    # Attributes
    backend_key: str
    language: str
    parser_kind: str | None = Field(default=None)
    grammar_contract_version: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeGrammarProfileDiagnostic(BaseModel):
    """Diagnostic emitted while resolving a Code grammar profile."""

    # Attributes
    severity: str = Field(default="error")
    reason: str
    message: str
    provider_key: str | None = Field(default=None)
    lane_key: str | None = Field(default=None)
    rule_name: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeGrammarRuleBinding(BaseModel):
    """Binding between a semantic syntax lane and a parser grammar rule."""

    # Attributes
    rule_name: str
    provider_key: str
    lane_key: str
    semantic_owner: str
    compiler_owner: str
    code_section_type: str | None = Field(default=None)
    semantic_token_types: list[str] = Field(default_factory=list)
    semantic_token_modifiers: list[str] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class CodeGrammarRuleDeclaration(BaseModel):
    """Provider-owned grammar declaration visible through the Code boundary."""

    # Attributes
    provider_key: str
    semantic_owner: str
    rule_name: str
    language: str = Field(default="aware")
    grammar_backend: str = Field(default="tree_sitter.aware")
    declared_anchor_fields: list[str] = Field(default_factory=list)
    top_level: bool = Field(default=False)
    generation_status: str = Field(default="declaration_only")
    metadata: JsonObject | None = Field(default=None)


class CodeGrammarAnchorCoverageDiagnostic(BaseModel):
    """Source-anchor coverage diagnostic emitted from provider declarations."""

    # Attributes
    severity: str = Field(default="error")
    reason: str
    message: str
    provider_key: str
    semantic_owner: str
    binding_key: str
    grammar_rule_name: str
    anchor_field_path: str
    metadata: JsonObject | None = Field(default=None)


class CodeGrammarProfile(BaseModel):
    """Code-owned grammar profile assembled from semantic package contracts."""

    # Attributes
    profile_key: str
    language: str
    backend_key: str | None = Field(default=None)
    backend: CodeGrammarBackendDescriptor | None = Field(default=None)
    provider_keys: list[str] = Field(default_factory=list)
    lane_keys: list[str] = Field(default_factory=list)
    grammar_rules: list[str] = Field(default_factory=list)
    code_section_types: list[str] = Field(default_factory=list)
    rule_bindings: list[CodeGrammarRuleBinding] = Field(default_factory=list)
    rule_declarations: list[CodeGrammarRuleDeclaration] = Field(default_factory=list)
    missing_rule_declarations: list[str] = Field(default_factory=list)
    anchor_diagnostics: list[CodeGrammarAnchorCoverageDiagnostic] = Field(default_factory=list)
    diagnostics: list[CodeGrammarProfileDiagnostic] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class ResolveCodeGrammarProfileRequest(CodeServiceRequest):
    """Resolve a grammar profile from semantic contracts and/or provider keys."""

    # Discriminator Tag
    operation: Literal["resolve_grammar_profile"] = "resolve_grammar_profile"

    # Attributes
    profile_key: str | None = Field(default=None)
    language: str = Field(default="aware")
    backend_key: str | None = Field(default=None)
    provider_keys: list[str] = Field(default_factory=list)
    semantic_contracts: list[CodeSemanticContract] = Field(default_factory=list)
    include_declaration_coverage: bool = Field(default=False)
    source_meaning_contracts: list[CodeSemanticSourceMeaningContract] = Field(default_factory=list)
    strict_anchor_coverage: bool = Field(default=False)
    include_current_code_sections: bool = Field(default=False)
    strict: bool = Field(default=True)
    metadata: JsonObject | None = Field(default=None)


class ResolveCodeGrammarProfileResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_grammar_profile"] = "resolve_grammar_profile"

    # Attributes
    status: CodeGrammarProfileResolutionStatus = Field(default=CodeGrammarProfileResolutionStatus.blocked)
    resolved: bool = Field(default=False)
    profile: CodeGrammarProfile | None = Field(default=None)
    diagnostics: list[CodeGrammarProfileDiagnostic] = Field(default_factory=list)
    missing_provider_keys: list[str] = Field(default_factory=list)
    invalid_rule_names: list[str] = Field(default_factory=list)
    missing_rule_declarations: list[str] = Field(default_factory=list)
    anchor_diagnostics: list[CodeGrammarAnchorCoverageDiagnostic] = Field(default_factory=list)
    provider_count: int = Field(default=0)
    lane_count: int = Field(default=0)
    rule_count: int = Field(default=0)
    declaration_rule_count: int = Field(default=0)
    anchor_diagnostic_count: int = Field(default=0)
