from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol
from uuid import UUID

from aware_code.semantic_package.schemas import (
    CapabilityBundleDescriptor,
    CapabilityParticipationDescriptor,
    CapabilityProfileDescriptor,
)

AWARE_MODULE_SEMANTIC_CONTRACT_EXPORT_NAME = "AWARE_MODULE_SEMANTIC_CONTRACT"


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticArtifactBinding:
    """Workspace-facing package binding for semantic artifact ownership."""

    module_id: str | None
    package_name: str
    language: str
    surface: str
    manifest_kind: str
    manifest_relative_path: str
    package_root: str
    sources_root: str
    package_kind: str | None = None
    semantic_contract_provider_key: str | None = None
    semantic_contract_role: str | None = None
    semantic_contract_name: str | None = None
    semantic_contract_module: str | None = None


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticArtifactLeafOwnershipRequest:
    """Request passed to semantic packages for generated artifact-leaf claims."""

    workspace_root: Path
    owner: WorkspaceSemanticArtifactBinding
    leaf: WorkspaceSemanticArtifactBinding


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticArtifactProduction:
    """Generic producer pointer for a semantic-package materialized artifact."""

    provider_key: str
    producer_key: str
    producer_kind: str | None = None
    provider_payload: Mapping[str, object] | None = None
    input_code_package_id: UUID | None = None
    input_object_instance_graph_commit_id: UUID | None = None
    input_digest: str | None = None
    output_digest: str | None = None
    emission_payload: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticArtifactLeafOwnershipClaim:
    """Semantic-package claim that a nested artifact leaf is owner-generated."""

    owned: bool
    owner_semantic_package_manifest: str
    ownership_role: str
    artifact_manifest_kind: str
    artifact_package_root: str
    production: WorkspaceSemanticArtifactProduction | None = None


class WorkspaceSemanticArtifactLeafOwnershipResolver(Protocol):
    """Callable protocol for semantic artifact-leaf ownership providers."""

    def __call__(
        self,
        *,
        request: WorkspaceSemanticArtifactLeafOwnershipRequest,
    ) -> WorkspaceSemanticArtifactLeafOwnershipClaim | None: ...


@dataclass(frozen=True, slots=True)
class ModuleCapabilityExecutionPolicyDescriptor:
    """Module-owned execution policy for a capability/owner pair."""

    capability: str
    semantic_owner: str
    callable_module: str | None = None
    callable_name: str | None = None
    required_semantic_scope_keys: tuple[str, ...] = ()
    priority: int = 100
    applies_when: str = "always"


@dataclass(frozen=True, slots=True)
class ModuleSemanticSyntaxLaneDescriptor:
    """Module-owned syntax lane truth for later token/grammar composition."""

    lane_key: str
    semantic_owner: str
    compiler_owner: str
    grammar_rules: tuple[str, ...] = ()
    semantic_token_types: tuple[str, ...] = ()
    semantic_token_modifiers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ModuleSemanticGrammarRuleFieldDescriptor:
    """Provider-owned grammar field declaration for source-anchor coverage."""

    field_path: str
    field_role: str | None = None
    value_kind: str | None = None
    required: bool = False
    child_rule_refs: tuple[str, ...] = ()
    token_literals: tuple[str, ...] = ()
    provider_payload: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ModuleSemanticGrammarRuleDescriptor:
    """Provider-owned grammar rule declaration.

    This is the semantic-contract side of grammar ownership. The current
    tree-sitter grammar remains the compatibility backend, while providers
    incrementally declare enough rule structure for source-anchor validation
    and future parser generation.
    """

    semantic_owner: str
    rule_name: str
    language: str = "aware"
    grammar_backend: str = "tree_sitter.aware"
    top_level: bool = False
    section_type: str | None = None
    fields: tuple[ModuleSemanticGrammarRuleFieldDescriptor, ...] = ()
    child_rule_refs: tuple[str, ...] = ()
    literal_tokens: tuple[str, ...] = ()
    source_anchor_fields: tuple[str, ...] = ()
    generation_status: str = "declaration_only"
    priority: int = 100
    provider_payload: Mapping[str, object] | None = None

    @property
    def declared_anchor_fields(self) -> tuple[str, ...]:
        """Return every source-anchor field declared by this rule."""

        return tuple(
            dict.fromkeys(
                field
                for field in (
                    *(item.field_path for item in self.fields),
                    *self.source_anchor_fields,
                )
                if field.strip()
            )
        )

    def declares_anchor_field(self, field_path: str) -> bool:
        """Return True when this rule declares a source anchor field."""

        normalized = field_path.strip()
        return bool(normalized) and normalized in self.declared_anchor_fields


@dataclass(frozen=True, slots=True)
class ModuleSemanticPackageRoleDescriptor:
    """Module-owned package semantic role truth."""

    role: str
    contract: str
    package_kind: str | None = None
    capabilities: tuple[str, ...] = ()
    owns_manifest_kinds: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ModuleSemanticWorkflowInstructionDescriptor:
    """Provider-owned instructions attached to a semantic workflow stage."""

    instruction_key: str
    title: str
    body: str
    instruction_kind: str = "natural_language"
    audience: str = "agent"
    stage_keys: tuple[str, ...] = ()
    required: bool = True
    source_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ModuleSemanticWorkflowDescriptor:
    """Provider-owned workflow truth consumed by Workspace genesis/catalog rails."""

    workflow_key: str
    semantic_owner: str
    stage_keys: tuple[str, ...]
    instructions: tuple[ModuleSemanticWorkflowInstructionDescriptor, ...]
    description: str | None = None
    instruction_refs: tuple[str, ...] = ()
    capability_refs: tuple[str, ...] = ()
    capability_profile_refs: tuple[str, ...] = ()
    grammar_profile_refs: tuple[str, ...] = ()
    source_meaning_refs: tuple[str, ...] = ()
    ontology_feature_refs: tuple[str, ...] = ()
    graph_binding_refs: tuple[str, ...] = ()
    expected_artifact_refs: tuple[str, ...] = ()
    expected_proof_refs: tuple[str, ...] = ()
    expected_receipt_refs: tuple[str, ...] = ()
    diagnostic_refs: tuple[str, ...] = ()
    policy_refs: tuple[str, ...] = ()
    required: bool = True
    priority: int = 100
    provider_payload: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ModuleSemanticManifestResolutionDescriptor:
    """Module-owned manifest resolution truth for semantic package entrypoints."""

    semantic_owner: str
    manifest_kind: str
    filename: str
    contract: str
    loader_module: str
    loader_name: str
    workspace_manifest_kind: str | None = None
    package_role: str | None = None
    semantic_package_family: str | None = None
    semantic_package_kind: str | None = None
    semantic_projection_name: str | None = None
    semantic_root_kind: str | None = None
    code_package_surface: str | None = None
    code_package_surface_by_package_kind: Mapping[str, str] | None = None
    workspace_materialization_order: int | None = None
    workspace_materialization_branch: str | None = None
    workspace_materialization_commit: bool | None = None
    workspace_materialization_primary: bool | None = None
    copy_code_package_metadata_keys: tuple[str, ...] = ()
    semantic_package_metadata: Mapping[str, object] | None = None
    priority: int = 100


@dataclass(frozen=True, slots=True)
class ModuleSemanticArtifactLeafOwnershipDescriptor:
    """Module-owned contract for generated package leaves owned by a semantic package."""

    semantic_owner: str
    owner_manifest_kinds: tuple[str, ...]
    artifact_manifest_kinds: tuple[str, ...]
    callable_module: str
    callable_name: str
    priority: int = 100
    ownership_role: str = "semantic_generated_artifact"


@dataclass(frozen=True, slots=True)
class ModuleSemanticMaterializationInputDescriptor:
    """Module-owned declaration for inputs accepted by semantic materialization.

    This is the target-side contract. A provider declares the package/materializer
    inputs it can consume so another semantic provider can emit a package request
    without Workspace importing either provider's internal compile-plan model.
    """

    semantic_owner: str
    input_key: str
    input_kind: str = "artifact"
    artifact_family: str | None = None
    artifact_role: str | None = None
    package_family: str | None = None
    semantic_kind: str | None = None
    runtime_contract_version: str | None = None
    callable_module: str | None = None
    callable_name: str | None = None
    required: bool = True
    priority: int = 100
    provider_payload: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ModuleSemanticMaterializationArtifactOutputDescriptor:
    """Module-owned declaration for artifacts emitted by semantic materialization.

    This is a producer declaration contract, not a Workspace data model. Semantic
    providers declare stable output identities here; Workspace may later record
    matching materialization receipts as generic revision artifact refs without
    importing provider-specific modules.
    """

    semantic_owner: str
    producer_key: str
    output_key: str
    artifact_family: str
    producer_provider_key: str | None = None
    artifact_role: str = "runtime"
    output_kind: str = "artifact"
    package_output_key: str | None = None
    artifact_relpath: str | None = None
    artifact_path_pattern: str | None = None
    manifest_relpath: str | None = None
    media_type: str | None = None
    runtime_contract_version: str | None = None
    required_for: tuple[str, ...] = ()
    authoritative_artifact_scope: bool = False
    required: bool = True
    priority: int = 100
    provider_payload: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ModuleSemanticMaterializationCodePackageDeltaOutputDescriptor:
    """Module-owned declaration for CodePackageDelta outputs.

    Artifact outputs identify materialization receipts and deployable evidence.
    CodePackageDelta outputs identify applyable code transport emitted by the
    provider and consumed by Workspace/SDK checkout rails.
    """

    semantic_owner: str
    producer_key: str
    output_key: str
    producer_provider_key: str | None = None
    authority_kind: str = "semantic_materialization"
    package_output_key: str | None = None
    runtime_contract_version: str | None = None
    required_for: tuple[str, ...] = ()
    required: bool = True
    priority: int = 100
    provider_payload: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ModuleSemanticMaterializationPackageOutputDescriptor:
    """Module-owned declaration for semantic packages emitted by materialization.

    This is the producer-side scheduling contract. The producer identifies the
    target provider input and the artifact output that fulfills that input;
    Workspace only validates descriptor compatibility and schedules the target.
    """

    semantic_owner: str
    producer_key: str
    output_key: str
    target_provider_key: str
    target_input_key: str
    target_semantic_owner: str | None = None
    target_package_family: str | None = None
    target_semantic_kind: str | None = None
    input_artifact_producer_key: str | None = None
    input_artifact_output_key: str | None = None
    input_artifact_family: str | None = None
    target_code_package_manifest_kind: str | None = None
    target_code_package_surface: str | None = None
    runtime_contract_version: str | None = None
    required_for: tuple[str, ...] = ()
    required: bool = True
    priority: int = 100
    provider_payload: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ModuleSemanticRuntimeProjectionPackageDescriptor:
    """Provider-owned projection ownership for a runtime ontology package."""

    package_name: str
    projection_names: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ModuleSemanticMaterializationRuntimeDescriptor:
    """Provider-owned runtime context requirements for materialization execution."""

    semantic_owner: str
    runtime_ontology_package_names: tuple[str, ...] = ()
    lane_projection_name: str | None = None
    required_projection_names: tuple[str, ...] = ()
    runtime_projection_packages: tuple[
        ModuleSemanticRuntimeProjectionPackageDescriptor, ...
    ] = ()
    environment_handle: str | None = None
    include_package_dependency_closure: bool = False
    priority: int = 100


@dataclass(frozen=True, slots=True)
class ModuleSemanticMaterializationRuntimeContextDescriptor:
    """Provider-owned runtime context resolver for Workspace materialization."""

    semantic_owner: str
    callable_module: str
    callable_name: str
    required: bool = False
    priority: int = 100
    provider_payload: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ModuleSemanticMaterializationExecutionContextDescriptor:
    """Provider-owned semantic execution context resolver declaration."""

    semantic_owner: str
    context_key: str
    callable_module: str
    callable_name: str
    required: bool = False
    priority: int = 100
    provider_payload: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ModuleSemanticMaterializationToolingDescriptor:
    """Provider-owned tooling requirement for semantic materialization."""

    semantic_owner: str
    tooling_key: str
    languages: tuple[str, ...] = ()
    required_for: tuple[str, ...] = ()
    manifest_presence_path: tuple[str, ...] = ()
    required: bool = False
    priority: int = 100
    provider_payload: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ModuleSemanticLanguageMaterializationProfileDescriptor:
    """Provider-owned default language materialization profile policy."""

    semantic_owner: str
    profile_key: str
    producer_key: str | None = None
    artifact_family: str | None = None
    code_package_languages: tuple[str, ...] = ()
    workspace_manifest_kinds: tuple[str, ...] = ()
    code_package_manifest_kinds: tuple[str, ...] = ()
    semantic_package_metadata_matches: Mapping[str, tuple[str, ...]] | None = None
    include_sqlite_target: bool = False
    sqlite_renderer_profile: str | None = None
    sqlite_renderer_profile_metadata_key: str | None = None
    sqlite_renderer_profile_by_metadata_value: Mapping[str, str] | None = None
    required_for: tuple[str, ...] = ()
    required: bool = False
    priority: int = 100
    provider_payload: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ModuleSemanticContract:
    """Shared module semantic truth consumed by semantic packages and LSP."""

    provider_key: str
    semantic_scope_keys: tuple[str, ...] = ()
    capability_participation: tuple[CapabilityParticipationDescriptor, ...] = ()
    capability_execution_policy: tuple[
        ModuleCapabilityExecutionPolicyDescriptor, ...
    ] = ()
    capability_profiles: tuple[CapabilityProfileDescriptor, ...] = ()
    capability_bundles: tuple[CapabilityBundleDescriptor, ...] = ()
    syntax_lanes: tuple[ModuleSemanticSyntaxLaneDescriptor, ...] = ()
    grammar_rule_declarations: tuple[
        ModuleSemanticGrammarRuleDescriptor,
        ...,
    ] = ()
    package_roles: tuple[ModuleSemanticPackageRoleDescriptor, ...] = ()
    semantic_workflows: tuple[ModuleSemanticWorkflowDescriptor, ...] = ()
    manifest_resolution: tuple[
        ModuleSemanticManifestResolutionDescriptor,
        ...,
    ] = ()
    artifact_leaf_ownership: tuple[
        ModuleSemanticArtifactLeafOwnershipDescriptor,
        ...,
    ] = ()
    materialization_artifact_outputs: tuple[
        ModuleSemanticMaterializationArtifactOutputDescriptor,
        ...,
    ] = ()
    materialization_code_package_delta_outputs: tuple[
        ModuleSemanticMaterializationCodePackageDeltaOutputDescriptor,
        ...,
    ] = ()
    materialization_inputs: tuple[
        ModuleSemanticMaterializationInputDescriptor,
        ...,
    ] = ()
    materialization_package_outputs: tuple[
        ModuleSemanticMaterializationPackageOutputDescriptor,
        ...,
    ] = ()
    materialization_runtime: tuple[
        ModuleSemanticMaterializationRuntimeDescriptor,
        ...,
    ] = ()
    materialization_runtime_context: tuple[
        ModuleSemanticMaterializationRuntimeContextDescriptor,
        ...,
    ] = ()
    materialization_execution_context: tuple[
        ModuleSemanticMaterializationExecutionContextDescriptor,
        ...,
    ] = ()
    materialization_tooling: tuple[
        ModuleSemanticMaterializationToolingDescriptor,
        ...,
    ] = ()
    materialization_language_profiles: tuple[
        ModuleSemanticLanguageMaterializationProfileDescriptor,
        ...,
    ] = ()

    def capability_participation_for(
        self,
        *,
        capability: str,
    ) -> tuple[CapabilityParticipationDescriptor, ...]:
        return tuple(
            item
            for item in self.capability_participation
            if item.capability == capability
        )

    def capability_profiles_for(
        self,
        *,
        capability: str,
    ) -> tuple[CapabilityProfileDescriptor, ...]:
        return tuple(
            item for item in self.capability_profiles if item.capability == capability
        )

    def capability_execution_policy_for(
        self,
        *,
        capability: str,
    ) -> tuple[ModuleCapabilityExecutionPolicyDescriptor, ...]:
        return tuple(
            item
            for item in self.capability_execution_policy
            if item.capability == capability
        )

    def grammar_rule_declarations_for(
        self,
        *,
        semantic_owner: str | None = None,
        rule_name: str | None = None,
        grammar_backend: str | None = None,
        language: str | None = None,
    ) -> tuple[ModuleSemanticGrammarRuleDescriptor, ...]:
        """Return provider-declared grammar rule structure."""

        normalized_semantic_owner = _normalized_optional_text(semantic_owner)
        normalized_rule_name = _normalized_optional_text(rule_name)
        normalized_grammar_backend = _normalized_optional_text(grammar_backend)
        normalized_language = _normalized_optional_text(language)
        return tuple(
            sorted(
                (
                    descriptor
                    for descriptor in self.grammar_rule_declarations
                    if (
                        normalized_semantic_owner is None
                        or descriptor.semantic_owner == normalized_semantic_owner
                    )
                    and (
                        normalized_rule_name is None
                        or descriptor.rule_name == normalized_rule_name
                    )
                    and (
                        normalized_grammar_backend is None
                        or descriptor.grammar_backend == normalized_grammar_backend
                    )
                    and (
                        normalized_language is None
                        or descriptor.language == normalized_language
                    )
                ),
                key=lambda item: (
                    item.priority,
                    item.semantic_owner,
                    item.rule_name,
                ),
            )
        )

    def capability_bundles_for(
        self,
        *,
        capability: str,
    ) -> tuple[CapabilityBundleDescriptor, ...]:
        return tuple(
            item for item in self.capability_bundles if item.capability == capability
        )

    def package_role_for(
        self,
        *,
        role: str,
    ) -> ModuleSemanticPackageRoleDescriptor | None:
        return next(
            (item for item in self.package_roles if item.role == role),
            None,
        )

    def manifest_resolution_for(
        self,
        *,
        semantic_owner: str | None = None,
        manifest_kind: str | None = None,
        filename: str | None = None,
        workspace_manifest_kind: str | None = None,
    ) -> tuple[ModuleSemanticManifestResolutionDescriptor, ...]:
        """Return provider-owned manifest resolution descriptors."""

        normalized_semantic_owner = _normalized_optional_text(semantic_owner)
        normalized_manifest_kind = _normalized_optional_text(manifest_kind)
        normalized_filename = _normalized_optional_text(filename)
        normalized_workspace_manifest_kind = _normalized_optional_text(
            workspace_manifest_kind
        )
        return tuple(
            sorted(
                (
                    descriptor
                    for descriptor in self.manifest_resolution
                    if (
                        normalized_semantic_owner is None
                        or descriptor.semantic_owner == normalized_semantic_owner
                    )
                    and (
                        normalized_manifest_kind is None
                        or descriptor.manifest_kind == normalized_manifest_kind
                    )
                    and (
                        normalized_filename is None
                        or descriptor.filename == normalized_filename
                    )
                    and (
                        normalized_workspace_manifest_kind is None
                        or descriptor.workspace_manifest_kind
                        == normalized_workspace_manifest_kind
                    )
                ),
                key=lambda item: (
                    item.priority,
                    item.semantic_owner,
                    item.manifest_kind,
                    item.filename,
                ),
            )
        )

    def semantic_workflows_for(
        self,
        *,
        semantic_owner: str | None = None,
        workflow_key: str | None = None,
        stage_key: str | None = None,
    ) -> tuple[ModuleSemanticWorkflowDescriptor, ...]:
        """Return provider-declared semantic workflows."""

        normalized_semantic_owner = _normalized_optional_text(semantic_owner)
        normalized_workflow_key = _normalized_optional_text(workflow_key)
        normalized_stage_key = _normalized_optional_text(stage_key)
        return tuple(
            sorted(
                (
                    descriptor
                    for descriptor in self.semantic_workflows
                    if (
                        normalized_semantic_owner is None
                        or descriptor.semantic_owner == normalized_semantic_owner
                    )
                    and (
                        normalized_workflow_key is None
                        or descriptor.workflow_key == normalized_workflow_key
                    )
                    and _descriptor_includes_optional_token(
                        tokens=descriptor.stage_keys,
                        token=normalized_stage_key,
                    )
                ),
                key=lambda item: (
                    item.priority,
                    item.semantic_owner,
                    item.workflow_key,
                ),
            )
        )

    def artifact_leaf_ownership_for(
        self,
        *,
        semantic_owner: str | None = None,
        owner_manifest_kind: str | None = None,
        artifact_manifest_kind: str | None = None,
    ) -> tuple[ModuleSemanticArtifactLeafOwnershipDescriptor, ...]:
        normalized_semantic_owner = _normalized_optional_text(semantic_owner)
        normalized_owner_manifest_kind = _normalized_optional_text(owner_manifest_kind)
        normalized_artifact_manifest_kind = _normalized_optional_text(
            artifact_manifest_kind
        )

        return tuple(
            sorted(
                (
                    descriptor
                    for descriptor in self.artifact_leaf_ownership
                    if (
                        normalized_semantic_owner is None
                        or descriptor.semantic_owner == normalized_semantic_owner
                    )
                    and _descriptor_includes_optional_token(
                        tokens=descriptor.owner_manifest_kinds,
                        token=normalized_owner_manifest_kind,
                    )
                    and _descriptor_includes_optional_token(
                        tokens=descriptor.artifact_manifest_kinds,
                        token=normalized_artifact_manifest_kind,
                    )
                ),
                key=lambda item: (
                    item.priority,
                    item.semantic_owner,
                    item.callable_module,
                    item.callable_name,
                ),
            )
        )

    def materialization_artifact_outputs_for(
        self,
        *,
        semantic_owner: str | None = None,
        producer_key: str | None = None,
        output_key: str | None = None,
        artifact_family: str | None = None,
        required_for: str | None = None,
    ) -> tuple[ModuleSemanticMaterializationArtifactOutputDescriptor, ...]:
        """Return provider-declared semantic materialization artifact outputs."""

        normalized_semantic_owner = _normalized_optional_text(semantic_owner)
        normalized_producer_key = _normalized_optional_text(producer_key)
        normalized_output_key = _normalized_optional_text(output_key)
        normalized_artifact_family = _normalized_optional_text(artifact_family)
        normalized_required_for = _normalized_optional_text(required_for)

        return tuple(
            sorted(
                (
                    descriptor
                    for descriptor in self.materialization_artifact_outputs
                    if (
                        normalized_semantic_owner is None
                        or descriptor.semantic_owner == normalized_semantic_owner
                    )
                    and (
                        normalized_producer_key is None
                        or descriptor.producer_key == normalized_producer_key
                    )
                    and (
                        normalized_output_key is None
                        or descriptor.output_key == normalized_output_key
                    )
                    and (
                        normalized_artifact_family is None
                        or descriptor.artifact_family == normalized_artifact_family
                    )
                    and _descriptor_includes_optional_token(
                        tokens=descriptor.required_for,
                        token=normalized_required_for,
                    )
                ),
                key=lambda item: (
                    item.priority,
                    item.semantic_owner,
                    item.producer_key,
                    item.output_key,
                ),
            )
        )

    def materialization_inputs_for(
        self,
        *,
        semantic_owner: str | None = None,
        input_key: str | None = None,
        input_kind: str | None = None,
        artifact_family: str | None = None,
        package_family: str | None = None,
        semantic_kind: str | None = None,
    ) -> tuple[ModuleSemanticMaterializationInputDescriptor, ...]:
        """Return provider-declared semantic materialization inputs."""

        normalized_semantic_owner = _normalized_optional_text(semantic_owner)
        normalized_input_key = _normalized_optional_text(input_key)
        normalized_input_kind = _normalized_optional_text(input_kind)
        normalized_artifact_family = _normalized_optional_text(artifact_family)
        normalized_package_family = _normalized_optional_text(package_family)
        normalized_semantic_kind = _normalized_optional_text(semantic_kind)

        return tuple(
            sorted(
                (
                    descriptor
                    for descriptor in self.materialization_inputs
                    if (
                        normalized_semantic_owner is None
                        or descriptor.semantic_owner == normalized_semantic_owner
                    )
                    and (
                        normalized_input_key is None
                        or descriptor.input_key == normalized_input_key
                    )
                    and (
                        normalized_input_kind is None
                        or descriptor.input_kind == normalized_input_kind
                    )
                    and (
                        normalized_artifact_family is None
                        or descriptor.artifact_family == normalized_artifact_family
                    )
                    and (
                        normalized_package_family is None
                        or descriptor.package_family == normalized_package_family
                    )
                    and (
                        normalized_semantic_kind is None
                        or descriptor.semantic_kind == normalized_semantic_kind
                    )
                ),
                key=lambda item: (
                    item.priority,
                    item.semantic_owner,
                    item.input_key,
                ),
            )
        )

    def materialization_code_package_delta_outputs_for(
        self,
        *,
        semantic_owner: str | None = None,
        producer_key: str | None = None,
        output_key: str | None = None,
        authority_kind: str | None = None,
        required_for: str | None = None,
    ) -> tuple[
        ModuleSemanticMaterializationCodePackageDeltaOutputDescriptor,
        ...,
    ]:
        """Return provider-declared semantic CodePackageDelta outputs."""

        normalized_semantic_owner = _normalized_optional_text(semantic_owner)
        normalized_producer_key = _normalized_optional_text(producer_key)
        normalized_output_key = _normalized_optional_text(output_key)
        normalized_authority_kind = _normalized_optional_text(authority_kind)
        normalized_required_for = _normalized_optional_text(required_for)

        return tuple(
            sorted(
                (
                    descriptor
                    for descriptor in self.materialization_code_package_delta_outputs
                    if (
                        normalized_semantic_owner is None
                        or descriptor.semantic_owner == normalized_semantic_owner
                    )
                    and (
                        normalized_producer_key is None
                        or descriptor.producer_key == normalized_producer_key
                    )
                    and (
                        normalized_output_key is None
                        or descriptor.output_key == normalized_output_key
                    )
                    and (
                        normalized_authority_kind is None
                        or descriptor.authority_kind == normalized_authority_kind
                    )
                    and _descriptor_includes_optional_token(
                        tokens=descriptor.required_for,
                        token=normalized_required_for,
                    )
                ),
                key=lambda item: (
                    item.priority,
                    item.semantic_owner,
                    item.producer_key,
                    item.output_key,
                ),
            )
        )

    def materialization_package_outputs_for(
        self,
        *,
        semantic_owner: str | None = None,
        producer_key: str | None = None,
        output_key: str | None = None,
        target_provider_key: str | None = None,
        target_input_key: str | None = None,
        required_for: str | None = None,
    ) -> tuple[ModuleSemanticMaterializationPackageOutputDescriptor, ...]:
        """Return provider-declared semantic package materialization outputs."""

        normalized_semantic_owner = _normalized_optional_text(semantic_owner)
        normalized_producer_key = _normalized_optional_text(producer_key)
        normalized_output_key = _normalized_optional_text(output_key)
        normalized_target_provider_key = _normalized_optional_text(target_provider_key)
        normalized_target_input_key = _normalized_optional_text(target_input_key)
        normalized_required_for = _normalized_optional_text(required_for)

        return tuple(
            sorted(
                (
                    descriptor
                    for descriptor in self.materialization_package_outputs
                    if (
                        normalized_semantic_owner is None
                        or descriptor.semantic_owner == normalized_semantic_owner
                    )
                    and (
                        normalized_producer_key is None
                        or descriptor.producer_key == normalized_producer_key
                    )
                    and (
                        normalized_output_key is None
                        or descriptor.output_key == normalized_output_key
                    )
                    and (
                        normalized_target_provider_key is None
                        or descriptor.target_provider_key
                        == normalized_target_provider_key
                    )
                    and (
                        normalized_target_input_key is None
                        or descriptor.target_input_key == normalized_target_input_key
                    )
                    and _descriptor_includes_optional_token(
                        tokens=descriptor.required_for,
                        token=normalized_required_for,
                    )
                ),
                key=lambda item: (
                    item.priority,
                    item.semantic_owner,
                    item.producer_key,
                    item.output_key,
                ),
            )
        )

    def materialization_runtime_for(
        self,
        *,
        semantic_owner: str | None = None,
    ) -> tuple[ModuleSemanticMaterializationRuntimeDescriptor, ...]:
        """Return provider-declared runtime requirements for materialization."""

        normalized_semantic_owner = _normalized_optional_text(semantic_owner)
        return tuple(
            sorted(
                (
                    descriptor
                    for descriptor in self.materialization_runtime
                    if (
                        normalized_semantic_owner is None
                        or descriptor.semantic_owner == normalized_semantic_owner
                    )
                ),
                key=lambda item: (item.priority, item.semantic_owner),
            )
        )

    def materialization_execution_context_for(
        self,
        *,
        semantic_owner: str | None = None,
        context_key: str | None = None,
    ) -> tuple[ModuleSemanticMaterializationExecutionContextDescriptor, ...]:
        """Return provider-declared semantic materialization context resolvers."""

        normalized_semantic_owner = _normalized_optional_text(semantic_owner)
        normalized_context_key = _normalized_optional_text(context_key)
        return tuple(
            sorted(
                (
                    descriptor
                    for descriptor in self.materialization_execution_context
                    if (
                        normalized_semantic_owner is None
                        or descriptor.semantic_owner == normalized_semantic_owner
                    )
                    and (
                        normalized_context_key is None
                        or descriptor.context_key == normalized_context_key
                    )
                ),
                key=lambda item: (
                    item.priority,
                    item.semantic_owner,
                    item.context_key,
                ),
            )
        )

    def materialization_runtime_context_for(
        self,
        *,
        semantic_owner: str | None = None,
    ) -> tuple[ModuleSemanticMaterializationRuntimeContextDescriptor, ...]:
        """Return provider-declared runtime context resolvers."""

        normalized_semantic_owner = _normalized_optional_text(semantic_owner)
        return tuple(
            sorted(
                (
                    descriptor
                    for descriptor in self.materialization_runtime_context
                    if (
                        normalized_semantic_owner is None
                        or descriptor.semantic_owner == normalized_semantic_owner
                    )
                ),
                key=lambda item: (
                    item.priority,
                    item.semantic_owner,
                    item.callable_module,
                    item.callable_name,
                ),
            )
        )

    def materialization_tooling_for(
        self,
        *,
        semantic_owner: str | None = None,
        tooling_key: str | None = None,
        required_for: str | None = None,
    ) -> tuple[ModuleSemanticMaterializationToolingDescriptor, ...]:
        """Return provider-declared tooling requirements."""

        normalized_semantic_owner = _normalized_optional_text(semantic_owner)
        normalized_tooling_key = _normalized_optional_text(tooling_key)
        normalized_required_for = _normalized_optional_text(required_for)
        return tuple(
            sorted(
                (
                    descriptor
                    for descriptor in self.materialization_tooling
                    if (
                        normalized_semantic_owner is None
                        or descriptor.semantic_owner == normalized_semantic_owner
                    )
                    and (
                        normalized_tooling_key is None
                        or descriptor.tooling_key == normalized_tooling_key
                    )
                    and _descriptor_includes_optional_token(
                        tokens=descriptor.required_for,
                        token=normalized_required_for,
                    )
                ),
                key=lambda item: (
                    item.priority,
                    item.semantic_owner,
                    item.tooling_key,
                ),
            )
        )

    def materialization_language_profiles_for(
        self,
        *,
        semantic_owner: str | None = None,
        profile_key: str | None = None,
        producer_key: str | None = None,
        artifact_family: str | None = None,
        required_for: str | None = None,
    ) -> tuple[ModuleSemanticLanguageMaterializationProfileDescriptor, ...]:
        """Return provider-declared language materialization profile policy."""

        normalized_semantic_owner = _normalized_optional_text(semantic_owner)
        normalized_profile_key = _normalized_optional_text(profile_key)
        normalized_producer_key = _normalized_optional_text(producer_key)
        normalized_artifact_family = _normalized_optional_text(artifact_family)
        normalized_required_for = _normalized_optional_text(required_for)
        return tuple(
            sorted(
                (
                    descriptor
                    for descriptor in self.materialization_language_profiles
                    if (
                        normalized_semantic_owner is None
                        or descriptor.semantic_owner == normalized_semantic_owner
                    )
                    and (
                        normalized_profile_key is None
                        or descriptor.profile_key == normalized_profile_key
                    )
                    and (
                        normalized_producer_key is None
                        or descriptor.producer_key == normalized_producer_key
                    )
                    and (
                        normalized_artifact_family is None
                        or descriptor.artifact_family == normalized_artifact_family
                    )
                    and _descriptor_includes_optional_token(
                        tokens=descriptor.required_for,
                        token=normalized_required_for,
                    )
                ),
                key=lambda item: (
                    item.priority,
                    item.semantic_owner,
                    item.profile_key,
                ),
            )
        )


def _descriptor_includes_optional_token(
    *,
    tokens: tuple[str, ...],
    token: str | None,
) -> bool:
    if token is None:
        return True
    normalized_tokens = frozenset(
        normalized
        for value in tokens
        for normalized in (_normalized_optional_text(value),)
        if normalized is not None
    )
    return not normalized_tokens or token in normalized_tokens


def _normalized_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


__all__ = [
    "AWARE_MODULE_SEMANTIC_CONTRACT_EXPORT_NAME",
    "ModuleCapabilityExecutionPolicyDescriptor",
    "ModuleSemanticArtifactLeafOwnershipDescriptor",
    "ModuleSemanticContract",
    "ModuleSemanticGrammarRuleDescriptor",
    "ModuleSemanticGrammarRuleFieldDescriptor",
    "ModuleSemanticManifestResolutionDescriptor",
    "ModuleSemanticMaterializationArtifactOutputDescriptor",
    "ModuleSemanticMaterializationCodePackageDeltaOutputDescriptor",
    "ModuleSemanticMaterializationExecutionContextDescriptor",
    "ModuleSemanticMaterializationInputDescriptor",
    "ModuleSemanticLanguageMaterializationProfileDescriptor",
    "ModuleSemanticMaterializationPackageOutputDescriptor",
    "ModuleSemanticMaterializationRuntimeDescriptor",
    "ModuleSemanticMaterializationRuntimeContextDescriptor",
    "ModuleSemanticPackageRoleDescriptor",
    "ModuleSemanticRuntimeProjectionPackageDescriptor",
    "ModuleSemanticSyntaxLaneDescriptor",
    "ModuleSemanticWorkflowDescriptor",
    "ModuleSemanticWorkflowInstructionDescriptor",
    "WorkspaceSemanticArtifactBinding",
    "WorkspaceSemanticArtifactLeafOwnershipClaim",
    "WorkspaceSemanticArtifactLeafOwnershipRequest",
    "WorkspaceSemanticArtifactProduction",
    "WorkspaceSemanticArtifactLeafOwnershipResolver",
]
