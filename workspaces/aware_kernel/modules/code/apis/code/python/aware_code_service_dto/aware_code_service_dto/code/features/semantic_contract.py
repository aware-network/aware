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
from aware_code_service_dto.code.features.package_distribution import CodeLanguage
from aware_code_service_dto.code.service import (
    CodeServiceRequest,
    CodeServiceResponse,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_service_dto.code.features.package_layout import CodePackageLayoutContract


class CodeCapabilityParticipationDescriptor(BaseModel):
    """Provider-owned capability participation declaration."""

    # Attributes
    capability: str
    semantic_owner: str
    metadata: JsonObject | None = Field(default=None)


class CodeCapabilityExecutionPolicyDescriptor(BaseModel):
    """Provider-owned capability execution policy declaration."""

    # Attributes
    capability: str
    semantic_owner: str
    callable_module: str | None = Field(default=None)
    callable_name: str | None = Field(default=None)
    required_semantic_scope_keys: list[str] = Field(default_factory=list)
    priority: int = Field(default=100)
    applies_when: str = Field(default="always")


class CodeCapabilityProfileDescriptor(BaseModel):
    """Provider-owned capability profile declaration."""

    # Attributes
    capability: str
    name: str
    semantic_owners: list[str] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class CodeCapabilityBundleDescriptor(BaseModel):
    """Provider-owned capability bundle declaration."""

    # Attributes
    capability: str
    name: str
    capabilities: list[str] = Field(default_factory=list)
    semantic_owners: list[str] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticSyntaxLaneDescriptor(BaseModel):
    """Syntax lane truth for semantic tokens and grammar composition."""

    # Attributes
    lane_key: str
    semantic_owner: str
    compiler_owner: str
    grammar_rules: list[str] = Field(default_factory=list)
    semantic_token_types: list[str] = Field(default_factory=list)
    semantic_token_modifiers: list[str] = Field(default_factory=list)


class CodeSemanticGrammarRuleFieldDescriptor(BaseModel):
    """Provider-owned grammar field declaration for source-anchor coverage."""

    # Attributes
    field_path: str
    field_role: str | None = Field(default=None)
    value_kind: str | None = Field(default=None)
    required: bool = Field(default=False)
    child_rule_refs: list[str] = Field(default_factory=list)
    token_literals: list[str] = Field(default_factory=list)
    provider_payload: JsonObject | None = Field(default=None)


class CodeSemanticGrammarRuleDescriptor(BaseModel):
    """Provider-owned grammar rule declaration exposed through Code."""

    # Attributes
    semantic_owner: str
    rule_name: str
    language: str = Field(default="aware")
    grammar_backend: str = Field(default="tree_sitter.aware")
    top_level: bool = Field(default=False)
    section_type: str | None = Field(default=None)
    fields: list[CodeSemanticGrammarRuleFieldDescriptor] = Field(default_factory=list)
    child_rule_refs: list[str] = Field(default_factory=list)
    literal_tokens: list[str] = Field(default_factory=list)
    source_anchor_fields: list[str] = Field(default_factory=list)
    generation_status: str = Field(default="declaration_only")
    priority: int = Field(default=100)
    provider_payload: JsonObject | None = Field(default=None)


class CodeSemanticPackageRoleDescriptor(BaseModel):
    """Semantic package role truth exposed through the Code API boundary."""

    # Attributes
    role: str
    contract: str
    package_kind: str | None = Field(default=None)
    capabilities: list[str] = Field(default_factory=list)
    owns_manifest_kinds: list[str] = Field(default_factory=list)


class CodeSemanticWorkflowInstructionDescriptor(BaseModel):
    """Provider-owned instruction payload attached to a semantic workflow."""

    # Attributes
    instruction_key: str
    title: str
    body: str
    instruction_kind: str = Field(default="natural_language")
    audience: str = Field(default="agent")
    stage_keys: list[str] = Field(default_factory=list)
    required: bool = Field(default=True)
    source_refs: list[str] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticWorkflowDescriptor(BaseModel):
    """Provider-owned semantic workflow descriptor exposed through Code."""

    # Attributes
    workflow_key: str
    semantic_owner: str
    stage_keys: list[str] = Field(default_factory=list)
    instructions: list[CodeSemanticWorkflowInstructionDescriptor] = Field(default_factory=list)
    description: str | None = Field(default=None)
    instruction_refs: list[str] = Field(default_factory=list)
    capability_refs: list[str] = Field(default_factory=list)
    capability_profile_refs: list[str] = Field(default_factory=list)
    grammar_profile_refs: list[str] = Field(default_factory=list)
    source_meaning_refs: list[str] = Field(default_factory=list)
    ontology_feature_refs: list[str] = Field(default_factory=list)
    graph_binding_refs: list[str] = Field(default_factory=list)
    expected_artifact_refs: list[str] = Field(default_factory=list)
    expected_proof_refs: list[str] = Field(default_factory=list)
    expected_receipt_refs: list[str] = Field(default_factory=list)
    diagnostic_refs: list[str] = Field(default_factory=list)
    policy_refs: list[str] = Field(default_factory=list)
    required: bool = Field(default=True)
    priority: int = Field(default=100)
    provider_payload: JsonObject | None = Field(default=None)


class CodeSemanticArtifactLeafOwnershipDescriptor(BaseModel):
    """Generated artifact leaf ownership declaration."""

    # Attributes
    semantic_owner: str
    owner_manifest_kinds: list[str] = Field(default_factory=list)
    artifact_manifest_kinds: list[str] = Field(default_factory=list)
    callable_module: str
    callable_name: str
    priority: int = Field(default=100)
    ownership_role: str = Field(default="semantic_generated_artifact")


class CodeSemanticMaterializationInputDescriptor(BaseModel):
    """Materialization input declaration accepted by a semantic provider."""

    # Attributes
    semantic_owner: str
    input_key: str
    input_kind: str = Field(default="artifact")
    artifact_family: str | None = Field(default=None)
    artifact_role: str | None = Field(default=None)
    package_family: str | None = Field(default=None)
    semantic_kind: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    callable_module: str | None = Field(default=None)
    callable_name: str | None = Field(default=None)
    required: bool = Field(default=True)
    priority: int = Field(default=100)
    provider_payload: JsonObject | None = Field(default=None)


class CodeSemanticMaterializationArtifactOutputDescriptor(BaseModel):
    """Materialization artifact output declaration emitted by a semantic provider."""

    # Attributes
    semantic_owner: str
    producer_key: str
    output_key: str
    artifact_family: str
    producer_provider_key: str | None = Field(default=None)
    artifact_role: str = Field(default="runtime")
    output_kind: str = Field(default="artifact")
    package_output_key: str | None = Field(default=None)
    artifact_relpath: str | None = Field(default=None)
    artifact_path_pattern: str | None = Field(default=None)
    manifest_relpath: str | None = Field(default=None)
    media_type: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    required_for: list[str] = Field(default_factory=list)
    required: bool = Field(default=True)
    priority: int = Field(default=100)
    provider_payload: JsonObject | None = Field(default=None)


class CodeSemanticMaterializationCodePackageDeltaOutputDescriptor(BaseModel):
    """Materialization CodePackageDelta output declaration emitted by a semantic provider."""

    # Attributes
    semantic_owner: str
    producer_key: str
    output_key: str
    producer_provider_key: str | None = Field(default=None)
    authority_kind: str = Field(default="semantic_materialization")
    package_output_key: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    required_for: list[str] = Field(default_factory=list)
    required: bool = Field(default=True)
    priority: int = Field(default=100)
    provider_payload: JsonObject | None = Field(default=None)


class CodeSemanticGeneratedCodePackageDeclaration(BaseModel):
    """Concrete generated Code package declaration derived from semantic package truth."""

    # Attributes
    source_manifest_path: str | None = Field(default=None)
    semantic_owner: str | None = Field(default=None)
    role: str | None = Field(default=None)
    language: CodeLanguage = Field(default=CodeLanguage.python)
    package_name: str
    package_root: str
    sources_root: str | None = Field(default=None)
    manifest_kind: str
    manifest_path: str
    code_package_surface: str | None = Field(default=None)
    materialization_source: str | None = Field(default=None)
    renderer_kind: str | None = Field(default=None)
    renderer_profile: str | None = Field(default=None)
    source_is_runtime: bool = Field(default=False)
    public_checkout_default: bool = Field(default=False)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticMaterializationPackageOutputDescriptor(BaseModel):
    """Materialization package output declaration emitted by a semantic provider."""

    # Attributes
    semantic_owner: str
    producer_key: str
    output_key: str
    target_provider_key: str
    target_input_key: str
    target_semantic_owner: str | None = Field(default=None)
    target_package_family: str | None = Field(default=None)
    target_semantic_kind: str | None = Field(default=None)
    input_artifact_producer_key: str | None = Field(default=None)
    input_artifact_output_key: str | None = Field(default=None)
    input_artifact_family: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    required_for: list[str] = Field(default_factory=list)
    required: bool = Field(default=True)
    priority: int = Field(default=100)
    provider_payload: JsonObject | None = Field(default=None)


class CodeSemanticRuntimeProjectionPackageDescriptor(BaseModel):
    """Projection ownership for a runtime ontology package."""

    # Attributes
    package_name: str
    projection_names: list[str] = Field(default_factory=list)


class CodeSemanticMaterializationRuntimeDescriptor(BaseModel):
    """Provider-owned runtime context requirement for materialization execution."""

    # Attributes
    semantic_owner: str
    runtime_ontology_package_names: list[str] = Field(default_factory=list)
    lane_projection_name: str | None = Field(default=None)
    required_projection_names: list[str] = Field(default_factory=list)
    runtime_projection_packages: list[CodeSemanticRuntimeProjectionPackageDescriptor] = Field(default_factory=list)
    environment_handle: str | None = Field(default=None)
    include_package_dependency_closure: bool = Field(default=False)
    priority: int = Field(default=100)


class CodeSemanticMaterializationRuntimeContextDescriptor(BaseModel):
    """Provider-owned runtime context resolver declaration."""

    # Attributes
    semantic_owner: str
    callable_module: str
    callable_name: str
    required: bool = Field(default=False)
    priority: int = Field(default=100)
    provider_payload: JsonObject | None = Field(default=None)


class CodeSemanticMaterializationExecutionContextDescriptor(BaseModel):
    """Provider-owned execution context resolver declaration."""

    # Attributes
    semantic_owner: str
    context_key: str
    callable_module: str
    callable_name: str
    required: bool = Field(default=False)
    priority: int = Field(default=100)
    provider_payload: JsonObject | None = Field(default=None)


class CodeSemanticManifestResolutionDescriptor(BaseModel):
    """Provider-owned manifest resolution declaration for semantic package entrypoints."""

    # Attributes
    semantic_owner: str
    manifest_kind: str
    filename: str
    contract: str
    loader_module: str
    loader_name: str
    workspace_manifest_kind: str | None = Field(default=None)
    package_role: str | None = Field(default=None)
    semantic_package_family: str | None = Field(default=None)
    semantic_package_kind: str | None = Field(default=None)
    semantic_projection_name: str | None = Field(default=None)
    semantic_root_kind: str | None = Field(default=None)
    code_package_surface: str | None = Field(default=None)
    code_package_surface_by_package_kind: JsonObject | None = Field(default=None)
    workspace_materialization_order: int | None = Field(default=None)
    workspace_materialization_branch: str | None = Field(default=None)
    workspace_materialization_commit: bool | None = Field(default=None)
    workspace_materialization_primary: bool | None = Field(default=None)
    copy_code_package_metadata_keys: list[str] = Field(default_factory=list)
    semantic_package_metadata: JsonObject | None = Field(default=None)
    priority: int = Field(default=100)


class CodeSemanticManifestResolutionMatch(BaseModel):
    """Ordered manifest-resolution match exposed by the Code API boundary."""

    # Attributes
    provider_key: str
    semantic_contract: CodeSemanticContract
    manifest_resolution: CodeSemanticManifestResolutionDescriptor
    semantic_contract_module: str | None = Field(default=None)


class CodeSemanticScopePackageRef(BaseModel):
    """Provider-neutral package coordinates accepted by Code semantic scope providers."""

    # Attributes
    package_name: str
    package_root: str = Field(default=".")
    manifest_path: str
    language: CodeLanguage = Field(default=CodeLanguage.aware)
    metadata: JsonObject | None = Field(default=None)
    semantic_packages: list[JsonObject] = Field(default_factory=list)


class CodeSemanticMaterializationScopeDependency(BaseModel):
    """Provider-owned dependency ref required by semantic materialization scope closure."""

    # Attributes
    package_name: str
    provider_key: str | None = Field(default=None)
    semantic_owner: str | None = Field(default=None)
    manifest_kind: str | None = Field(default=None)
    dependency_kind: str = Field(default="semantic_package")
    required_state: str = Field(default="materialized")
    semantic_package_family: str | None = Field(default=None)
    semantic_package_kind: str | None = Field(default=None)
    semantic_package_name: str | None = Field(default=None)
    source_refs: list[str] = Field(default_factory=list)
    reason: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticScopeResolution(BaseModel):
    """Provider-neutral semantic-scope resolution exposed by the Code API boundary."""

    # Attributes
    scope_key: str
    provider_key: str
    payload: JsonObject = Field(default_factory=JsonObject)
    materialization_dependencies: list[CodeSemanticMaterializationScopeDependency] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticContract(BaseModel):
    """API-owned DTO for the full shared Code semantic contract."""

    # Attributes
    provider_key: str
    semantic_scope_keys: list[str] = Field(default_factory=list)
    capability_participation: list[CodeCapabilityParticipationDescriptor] = Field(default_factory=list)
    capability_execution_policy: list[CodeCapabilityExecutionPolicyDescriptor] = Field(default_factory=list)
    capability_profiles: list[CodeCapabilityProfileDescriptor] = Field(default_factory=list)
    capability_bundles: list[CodeCapabilityBundleDescriptor] = Field(default_factory=list)
    syntax_lanes: list[CodeSemanticSyntaxLaneDescriptor] = Field(default_factory=list)
    grammar_rule_declarations: list[CodeSemanticGrammarRuleDescriptor] = Field(default_factory=list)
    package_roles: list[CodeSemanticPackageRoleDescriptor] = Field(default_factory=list)
    semantic_workflows: list[CodeSemanticWorkflowDescriptor] = Field(default_factory=list)
    artifact_leaf_ownership: list[CodeSemanticArtifactLeafOwnershipDescriptor] = Field(default_factory=list)
    materialization_artifact_outputs: list[CodeSemanticMaterializationArtifactOutputDescriptor] = Field(
        default_factory=list
    )
    materialization_code_package_delta_outputs: list[CodeSemanticMaterializationCodePackageDeltaOutputDescriptor] = (
        Field(default_factory=list)
    )
    materialization_inputs: list[CodeSemanticMaterializationInputDescriptor] = Field(default_factory=list)
    materialization_package_outputs: list[CodeSemanticMaterializationPackageOutputDescriptor] = Field(
        default_factory=list
    )
    materialization_runtime: list[CodeSemanticMaterializationRuntimeDescriptor] = Field(default_factory=list)
    materialization_runtime_context: list[CodeSemanticMaterializationRuntimeContextDescriptor] = Field(
        default_factory=list
    )
    materialization_execution_context: list[CodeSemanticMaterializationExecutionContextDescriptor] = Field(
        default_factory=list
    )
    manifest_resolution: list[CodeSemanticManifestResolutionDescriptor] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticContractSpecSection(BaseModel):
    """One generated reader-facing SPEC section derived from a Code semantic contract."""

    # Attributes
    section_key: str
    title: str
    body: str
    item_count: int = Field(default=0)
    source_fields: list[str] = Field(default_factory=list)


class CodeSemanticContractSpecDeclaration(BaseModel):
    """Generated reader-facing SPEC declaration derived from a Code semantic contract."""

    # Attributes
    provider_key: str
    title: str
    summary: str
    markdown: str
    sections: list[CodeSemanticContractSpecSection] = Field(default_factory=list)
    generated_code_packages: list[CodeSemanticGeneratedCodePackageDeclaration] = Field(default_factory=list)
    source_contract_digest: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeSemanticProviderBinding(BaseModel):
    """API-owned semantic provider/package binding ref."""

    # Attributes
    provider_key: str
    provider_role: str | None = Field(default=None)
    provider_name: str | None = Field(default=None)
    provider_module: str | None = Field(default=None)
    package_fqn: str | None = Field(default=None)
    manifest_kind: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    semantic_package_metadata: JsonObject | None = Field(default=None)


class DescribeCodeSemanticContractRequest(CodeServiceRequest):
    """Describe one semantic contract by provider or package coordinates."""

    # Discriminator Tag
    operation: Literal["describe_semantic_contract"] = "describe_semantic_contract"

    # Attributes
    provider_key: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    package_fqn: str | None = Field(default=None)
    include_layout: bool = Field(default=True)
    include_spec_declaration: bool = Field(default=False)


class DescribeCodeSemanticContractResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["describe_semantic_contract"] = "describe_semantic_contract"

    # Attributes
    semantic_contract: CodeSemanticContract | None = Field(default=None)
    layout_contract: CodePackageLayoutContract | None = Field(default=None)
    provider_binding: CodeSemanticProviderBinding | None = Field(default=None)
    spec_declaration: CodeSemanticContractSpecDeclaration | None = Field(default=None)


class ValidateCodeSemanticContractRequest(CodeServiceRequest):
    """Validate an externally supplied Code semantic contract DTO."""

    # Discriminator Tag
    operation: Literal["validate_semantic_contract"] = "validate_semantic_contract"

    # Attributes
    semantic_contract: CodeSemanticContract
    strict: bool = Field(default=True)


class ValidateCodeSemanticContractResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["validate_semantic_contract"] = "validate_semantic_contract"

    # Attributes
    valid: bool = Field(default=False)
    diagnostics: list[str] = Field(default_factory=list)


class NormalizeCodeSemanticContractRequest(CodeServiceRequest):
    """Normalize a runtime-adapted semantic contract into the public DTO shape."""

    # Discriminator Tag
    operation: Literal["normalize_semantic_contract"] = "normalize_semantic_contract"

    # Attributes
    semantic_contract: CodeSemanticContract


class NormalizeCodeSemanticContractResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["normalize_semantic_contract"] = "normalize_semantic_contract"

    # Attributes
    semantic_contract: CodeSemanticContract | None = Field(default=None)


class FindCodeSemanticManifestResolutionRequest(CodeServiceRequest):
    """Resolve semantic manifest descriptors through Code-owned contract truth."""

    # Discriminator Tag
    operation: Literal["find_manifest_resolution"] = "find_manifest_resolution"

    # Attributes
    provider_key: str | None = Field(default=None)
    manifest_kind: str | None = Field(default=None)
    filename: str | None = Field(default=None)
    workspace_manifest_kind: str | None = Field(default=None)


class FindCodeSemanticManifestResolutionResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["find_manifest_resolution"] = "find_manifest_resolution"

    # Attributes
    matches: list[CodeSemanticManifestResolutionMatch] = Field(default_factory=list)


class ResolveCodeSemanticScopeRequest(CodeServiceRequest):
    """Resolve provider-owned semantic scope through the Code-owned registry."""

    # Discriminator Tag
    operation: Literal["resolve_semantic_scope"] = "resolve_semantic_scope"

    # Attributes
    package_ref: CodeSemanticScopePackageRef
    workspace_root: str = Field(default=".")
    provider_keys: list[str] = Field(default_factory=list)
    scope_keys: list[str] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class ResolveCodeSemanticScopeResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_semantic_scope"] = "resolve_semantic_scope"

    # Attributes
    resolved: bool = Field(default=False)
    resolutions: list[CodeSemanticScopeResolution] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    resolution_count: int = Field(default=0)
