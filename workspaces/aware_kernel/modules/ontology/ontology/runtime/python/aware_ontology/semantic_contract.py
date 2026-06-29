from __future__ import annotations

from aware_code.module_semantic_contract import (
    ModuleCapabilityExecutionPolicyDescriptor,
    ModuleSemanticContract,
    ModuleSemanticArtifactLeafOwnershipDescriptor,
    ModuleSemanticManifestResolutionDescriptor,
    ModuleSemanticMaterializationArtifactOutputDescriptor,
    ModuleSemanticLanguageMaterializationProfileDescriptor,
    ModuleSemanticMaterializationRuntimeContextDescriptor,
    ModuleSemanticMaterializationRuntimeDescriptor,
    ModuleSemanticPackageRoleDescriptor,
    ModuleSemanticRuntimeProjectionPackageDescriptor,
    ModuleSemanticWorkflowDescriptor,
    ModuleSemanticWorkflowInstructionDescriptor,
)
from aware_code.semantic_materialization import (
    SEMANTIC_MATERIALIZATION_CAPABILITY,
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_ENTRYPOINT,
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY,
    SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_ISOLATE_TARGET_MANIFESTS,
    SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_KEY,
)
from aware_code.semantic_package.schemas import (
    CapabilityParticipationDescriptor,
)
from aware_meta.semantic_contract import (
    META_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY,
    META_MATERIALIZATION_DELTA_ADAPTER_METADATA,
    META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
    META_MATERIALIZATION_REQUIRED_PROJECTIONS,
    META_MATERIALIZATION_ARTIFACT_OUTPUTS,
    META_OBJECT_CONFIG_GRAPH_SEMANTIC_OPERATION_TYPES,
    META_OBJECT_CONFIG_GRAPH_SUPPORTED_FUNCTION_CALL_OPERATION_TYPES,
    META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA,
    META_SEMANTIC_PROJECTION_MUTATION_SCOPE_PAYLOADS,
    META_SEMANTIC_SCOPE_KEYS,
    META_SEMANTIC_SOURCE_MEANING_CAPABILITY,
    META_SEMANTIC_SOURCE_MEANING_CAPABILITY_METADATA,
)
from aware_meta.semantic_operation_resolution import (
    META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY,
    META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION,
)
from aware_meta.semantic_projection_mutation_scope import (
    META_SEMANTIC_PROJECTION_MUTATION_SCOPES_METADATA_KEY,
)
from aware_ontology.semantic_runtime_catalog import (
    ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY,
    ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_ROLE,
    ONTOLOGY_RUNTIME_ARTIFACT_SET_CONTRACT_VERSION,
    ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY,
)


ONTOLOGY_PACKAGE_ROLE = "aware_ontology.ontology"
ONTOLOGY_PROVIDER_OWNER = "aware_ontology.provider"
ONTOLOGY_MATERIALIZATION_REQUIRED_PROJECTIONS = (
    *META_MATERIALIZATION_REQUIRED_PROJECTIONS,
    "OntologyConfig",
    "OntologyPackage",
)
ONTOLOGY_MATERIALIZATION_OWNER_SEQUENCE = (ONTOLOGY_PROVIDER_OWNER,)
ONTOLOGY_RUNTIME_ONTOLOGY_PACKAGE_NAMES = (
    "storage-ontology",
    "content-ontology",
    "code-ontology",
    "history-ontology",
    "meta-ontology",
    "ontology-ontology",
)

ONTOLOGY_MATERIALIZATION_DELTA_ADAPTER_METADATA: dict[str, object] = {
    **META_MATERIALIZATION_DELTA_ADAPTER_METADATA,
    "callable_module": "aware_ontology.materialization.workspace_provider",
    "callable_name": SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_ENTRYPOINT,
    "bridge_provider_key": "aware_meta",
    "bridge_semantic_owner": "aware_meta.object_config_graph",
}
ONTOLOGY_MATERIALIZATION_CAPABILITY_METADATA: dict[str, object] = {
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY: (
        ONTOLOGY_MATERIALIZATION_DELTA_ADAPTER_METADATA
    ),
}
ONTOLOGY_SEMANTIC_SOURCE_MEANING_CAPABILITY_METADATA: dict[str, object] = {
    **META_SEMANTIC_SOURCE_MEANING_CAPABILITY_METADATA,
    "bridge_provider_key": "aware_meta",
    "bridge_semantic_owner": "aware_meta.object_config_graph",
    "bridge_contract": (
        "Ontology provider exposes Meta OCG semantic-source meaning for "
        "ontology package consumers while keeping Workspace routed through "
        "aware_ontology."
    ),
}
ONTOLOGY_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA: dict[
    str,
    object,
] = {
    **META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA,
    "contract_version": (
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION
    ),
    "supported_semantic_operation_types": (
        META_OBJECT_CONFIG_GRAPH_SUPPORTED_FUNCTION_CALL_OPERATION_TYPES
    ),
    "semantic_operation_type_refs": META_OBJECT_CONFIG_GRAPH_SEMANTIC_OPERATION_TYPES,
    META_SEMANTIC_PROJECTION_MUTATION_SCOPES_METADATA_KEY: (
        META_SEMANTIC_PROJECTION_MUTATION_SCOPE_PAYLOADS
    ),
    "bridge_provider_key": "aware_meta",
    "bridge_semantic_owner": "aware_meta.object_config_graph",
    "semantic_apply_boundary": "ontology_function_call",
    "mutates": False,
    "execution_status": "not_requested",
    "provider_contract": (
        "Ontology exposes Meta-owned ObjectConfigGraph semantic operation "
        "FunctionCall resolution for ontology package consumers while keeping "
        "Workspace routed through aware_ontology."
    ),
}

ONTOLOGY_MATERIALIZATION_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
        metadata=ONTOLOGY_MATERIALIZATION_CAPABILITY_METADATA,
    )
    for semantic_owner in ONTOLOGY_MATERIALIZATION_OWNER_SEQUENCE
)
ONTOLOGY_SEMANTIC_SOURCE_MEANING_CAPABILITY_PARTICIPATION = (
    CapabilityParticipationDescriptor(
        capability=META_SEMANTIC_SOURCE_MEANING_CAPABILITY,
        semantic_owner=ONTOLOGY_PROVIDER_OWNER,
        metadata=ONTOLOGY_SEMANTIC_SOURCE_MEANING_CAPABILITY_METADATA,
    ),
)
ONTOLOGY_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION = (
    CapabilityParticipationDescriptor(
        capability=(META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY),
        semantic_owner=ONTOLOGY_PROVIDER_OWNER,
        metadata=(
            ONTOLOGY_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA
        ),
    ),
)
ONTOLOGY_CAPABILITY_PARTICIPATION = (
    *ONTOLOGY_MATERIALIZATION_CAPABILITY_PARTICIPATION,
    *ONTOLOGY_SEMANTIC_SOURCE_MEANING_CAPABILITY_PARTICIPATION,
    *ONTOLOGY_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION,
)

ONTOLOGY_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
        callable_module="aware_ontology.materialization.workspace_provider",
        callable_name="materialize",
        priority=20,
    )
    for semantic_owner in ONTOLOGY_MATERIALIZATION_OWNER_SEQUENCE
)

ONTOLOGY_PACKAGE_ROLES = (
    ModuleSemanticPackageRoleDescriptor(
        role=ONTOLOGY_PACKAGE_ROLE,
        contract="aware.ontology",
        package_kind="ontology",
    ),
    ModuleSemanticPackageRoleDescriptor(
        role=ONTOLOGY_PROVIDER_OWNER,
        contract="aware.semantic_provider",
        package_kind="runtime",
        capabilities=(
            META_SEMANTIC_SOURCE_MEANING_CAPABILITY,
            META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY,
            SEMANTIC_MATERIALIZATION_CAPABILITY,
        ),
        owns_manifest_kinds=("aware_ontology_toml",),
    ),
)

ONTOLOGY_MANIFEST_RESOLUTION = (
    ModuleSemanticManifestResolutionDescriptor(
        semantic_owner=ONTOLOGY_PROVIDER_OWNER,
        manifest_kind="aware_ontology_toml",
        filename="aware.ontology.toml",
        contract="aware.ontology",
        loader_module="aware_ontology.manifest.loader",
        loader_name="load_aware_ontology_toml_spec",
        workspace_manifest_kind="ontology",
        package_role=ONTOLOGY_PACKAGE_ROLE,
        semantic_package_family="ontology",
        semantic_package_kind="ontology_package",
        semantic_projection_name="OntologyPackage",
        semantic_root_kind="ontology_package",
        code_package_surface="structure",
        workspace_materialization_order=25,
        workspace_materialization_branch="semantic",
        workspace_materialization_commit=True,
        workspace_materialization_primary=True,
        copy_code_package_metadata_keys=(
            "fqn_prefix",
            "source_manifest",
            "semantic_runtime_manifest_path",
            "dependency_package_names",
            "package_root",
            "sources_root",
            "runtime_manifest",
            "runtime_project_name",
            "runtime_import_root",
            "stable_ids_ownership",
            "stable_ids_parity_policy",
            "stable_ids_resolution_policy",
            "function_impl_ownership",
            "function_impl_parity_policy",
            "language_materialization_targets",
            "layout_profile",
            "layout_source_dir",
            "layout_generated_dir",
            "layout_runtime_dir",
            "layout_orm_models_dir",
            "layout_output_dirs",
            "declared_semantic_contract_provider_key",
            "declared_semantic_contract_role",
            "declared_semantic_contract_module",
            "declared_semantic_contract_owns_manifest_kinds",
            "declared_semantic_contract_capabilities",
        ),
        priority=20,
    ),
)

ONTOLOGY_ARTIFACT_LEAF_OWNERSHIP = (
    ModuleSemanticArtifactLeafOwnershipDescriptor(
        semantic_owner=ONTOLOGY_PROVIDER_OWNER,
        owner_manifest_kinds=("aware_ontology_toml",),
        artifact_manifest_kinds=("pyproject_toml",),
        callable_module="aware_ontology.semantic_artifact_ownership",
        callable_name="resolve_workspace_semantic_artifact_leaf_ownership",
        priority=100,
    ),
)


def _ontology_meta_language_artifact_output(
    descriptor: ModuleSemanticMaterializationArtifactOutputDescriptor,
) -> ModuleSemanticMaterializationArtifactOutputDescriptor:
    provider_payload = dict(descriptor.provider_payload or {})
    provider_payload.update(
        {
            "bridge_provider_key": "aware_meta",
            "bridge_semantic_owner": descriptor.semantic_owner,
            "bridge_contract": (
                "Ontology provider bridges Meta OCG language materialization "
                "outputs after raw OCG leaf materialization."
            ),
        }
    )
    return ModuleSemanticMaterializationArtifactOutputDescriptor(
        semantic_owner=ONTOLOGY_PROVIDER_OWNER,
        producer_key=descriptor.producer_key,
        output_key=descriptor.output_key,
        artifact_family=descriptor.artifact_family,
        producer_provider_key="aware_meta",
        artifact_role=descriptor.artifact_role,
        output_kind=descriptor.output_kind,
        package_output_key=descriptor.package_output_key,
        artifact_relpath=descriptor.artifact_relpath,
        artifact_path_pattern=descriptor.artifact_path_pattern,
        manifest_relpath=descriptor.manifest_relpath,
        media_type=descriptor.media_type,
        runtime_contract_version=descriptor.runtime_contract_version,
        required_for=descriptor.required_for,
        required=descriptor.required,
        priority=descriptor.priority,
        provider_payload=provider_payload,
    )


ONTOLOGY_MATERIALIZATION_ARTIFACT_OUTPUTS = tuple(
    _ontology_meta_language_artifact_output(descriptor)
    for descriptor in META_MATERIALIZATION_ARTIFACT_OUTPUTS
    if descriptor.producer_key == META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY
    and descriptor.artifact_family == META_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY
) + (
    ModuleSemanticMaterializationArtifactOutputDescriptor(
        semantic_owner=ONTOLOGY_PROVIDER_OWNER,
        producer_key=ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY,
        output_key=ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY,
        artifact_family=ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY,
        producer_provider_key="aware_ontology",
        artifact_role=ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_ROLE,
        output_kind="materialization_detail",
        media_type="application/json",
        runtime_contract_version=ONTOLOGY_RUNTIME_ARTIFACT_SET_CONTRACT_VERSION,
        required_for=(
            "workspace_revision",
            "runtime_index",
            "service_boot",
        ),
        priority=10,
        provider_payload={
            "receipt_field": ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY,
            "dto_class_ref": (
                "aware_ontology_service_dto.runtime." "OntologyRuntimeArtifactSet"
            ),
            "activation_policy": ("workspace_revision_or_service_lifecycle_required"),
            "activation_allowed": False,
        },
    ),
)

ONTOLOGY_MATERIALIZATION_LANGUAGE_PROFILES = (
    ModuleSemanticLanguageMaterializationProfileDescriptor(
        semantic_owner=ONTOLOGY_PROVIDER_OWNER,
        profile_key="aware_ontology.ontology.default_language_materialization",
        producer_key=META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
        artifact_family=META_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY,
        code_package_languages=("aware",),
        code_package_manifest_kinds=("aware_ontology_toml",),
        include_sqlite_target=True,
        required_for=("workspace_revision",),
        provider_payload={
            "contract": (
                "Ontology wrappers declare default Meta OCG language "
                "materialization policy through the Ontology semantic contract."
            ),
        },
        priority=20,
    ),
)

ONTOLOGY_MATERIALIZATION_RUNTIME = (
    ModuleSemanticMaterializationRuntimeDescriptor(
        semantic_owner=ONTOLOGY_PROVIDER_OWNER,
        runtime_ontology_package_names=ONTOLOGY_RUNTIME_ONTOLOGY_PACKAGE_NAMES,
        lane_projection_name="OntologyPackage",
        required_projection_names=(ONTOLOGY_MATERIALIZATION_REQUIRED_PROJECTIONS),
        runtime_projection_packages=(
            ModuleSemanticRuntimeProjectionPackageDescriptor(
                package_name="ontology-ontology",
                projection_names=(
                    "OntologyConfig",
                    "OntologyPackage",
                ),
            ),
        ),
        environment_handle="workspace-semantic-materialization",
        include_package_dependency_closure=False,
        priority=20,
    ),
)

ONTOLOGY_MATERIALIZATION_RUNTIME_CONTEXT = (
    ModuleSemanticMaterializationRuntimeContextDescriptor(
        semantic_owner=ONTOLOGY_PROVIDER_OWNER,
        callable_module="aware_meta.runtime.graph_context",
        callable_name="build_meta_workspace_materialization_runtime_context",
        required=True,
        priority=20,
        provider_payload={
            "contract": (
                "Ontology-owned Workspace semantic materialization " "runtime context"
            ),
            "runtime_context_graph_publication_mode": "runtime_only",
            "runtime_ontology_package_names": (ONTOLOGY_RUNTIME_ONTOLOGY_PACKAGE_NAMES),
            SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_KEY: (
                SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_ISOLATE_TARGET_MANIFESTS
            ),
        },
    ),
)

ONTOLOGY_FUNCTION_IMPL_COVERAGE_PROOF_REF = "meta.function_impl.coverage"

ONTOLOGY_SEMANTIC_WORKFLOWS = (
    ModuleSemanticWorkflowDescriptor(
        workflow_key="ontology.package.materialization",
        semantic_owner=ONTOLOGY_PROVIDER_OWNER,
        description=(
            "Ontology package materialization and revision-readiness workflow."
        ),
        stage_keys=(
            "workspace.genesis.understand",
            "workspace.genesis.plan",
            "semantic.ontology.materialize",
            "semantic.ontology.verify_runtime_coverage",
        ),
        instructions=(
            ModuleSemanticWorkflowInstructionDescriptor(
                instruction_key="ontology.package.function_impl_coverage",
                title="Verify ontology function implementation coverage",
                body=(
                    "Materialize ontology packages only after Meta can prove "
                    "each workflow feature has typed operation closure and "
                    "FunctionImpl coverage through either native .aware "
                    "FunctionImpl source or strict runtime-handler delegation."
                ),
                stage_keys=(
                    "workspace.genesis.plan",
                    "semantic.ontology.verify_runtime_coverage",
                ),
                source_refs=(
                    "workspaces/aware_kernel/modules/ontology/ontology/runtime/python/aware_ontology/semantic_contract.py",
                    "aware.ontology.toml",
                ),
            ),
        ),
        capability_refs=(
            SEMANTIC_MATERIALIZATION_CAPABILITY,
            META_SEMANTIC_SOURCE_MEANING_CAPABILITY,
            META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY,
        ),
        capability_profile_refs=("module.aware_ontology",),
        source_meaning_refs=("aware_ontology.semantic_source_meaning",),
        ontology_feature_refs=(
            "aware_ontology.OntologyConfig",
            "aware_ontology.OntologyPackage",
        ),
        graph_binding_refs=(
            "aware_ontology.ontology_config",
            "aware_ontology.ontology_package",
        ),
        expected_artifact_refs=(ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY,),
        expected_proof_refs=(
            "workspace.semantic_materialization.receipt",
            ONTOLOGY_FUNCTION_IMPL_COVERAGE_PROOF_REF,
        ),
        expected_receipt_refs=(
            "workspace.semantic_materialization",
            "meta.semantic_workflow_closure",
        ),
        diagnostic_refs=("meta.semantic_diagnostics",),
        policy_refs=(
            "function_impl_ownership",
            "function_impl_parity_policy",
        ),
        priority=20,
        provider_payload={
            "coverage_contract": "native_function_impl_or_runtime_handler_delegation",
            "runtime_ontology_package_names": ONTOLOGY_RUNTIME_ONTOLOGY_PACKAGE_NAMES,
        },
    ),
)

AWARE_ONTOLOGY_SEMANTIC_CONTRACT = ModuleSemanticContract(
    provider_key="aware_ontology",
    semantic_scope_keys=META_SEMANTIC_SCOPE_KEYS,
    capability_participation=ONTOLOGY_CAPABILITY_PARTICIPATION,
    capability_execution_policy=(ONTOLOGY_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY),
    package_roles=ONTOLOGY_PACKAGE_ROLES,
    semantic_workflows=ONTOLOGY_SEMANTIC_WORKFLOWS,
    manifest_resolution=ONTOLOGY_MANIFEST_RESOLUTION,
    artifact_leaf_ownership=ONTOLOGY_ARTIFACT_LEAF_OWNERSHIP,
    materialization_artifact_outputs=ONTOLOGY_MATERIALIZATION_ARTIFACT_OUTPUTS,
    materialization_language_profiles=ONTOLOGY_MATERIALIZATION_LANGUAGE_PROFILES,
    materialization_runtime=ONTOLOGY_MATERIALIZATION_RUNTIME,
    materialization_runtime_context=ONTOLOGY_MATERIALIZATION_RUNTIME_CONTEXT,
)
AWARE_MODULE_SEMANTIC_CONTRACT = AWARE_ONTOLOGY_SEMANTIC_CONTRACT


__all__ = [
    "AWARE_MODULE_SEMANTIC_CONTRACT",
    "AWARE_ONTOLOGY_SEMANTIC_CONTRACT",
    "ONTOLOGY_ARTIFACT_LEAF_OWNERSHIP",
    "ONTOLOGY_CAPABILITY_PARTICIPATION",
    "ONTOLOGY_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY",
    "ONTOLOGY_MATERIALIZATION_CAPABILITY_METADATA",
    "ONTOLOGY_MATERIALIZATION_CAPABILITY_PARTICIPATION",
    "ONTOLOGY_MATERIALIZATION_DELTA_ADAPTER_METADATA",
    "ONTOLOGY_MANIFEST_RESOLUTION",
    "ONTOLOGY_MATERIALIZATION_ARTIFACT_OUTPUTS",
    "ONTOLOGY_MATERIALIZATION_LANGUAGE_PROFILES",
    "ONTOLOGY_MATERIALIZATION_OWNER_SEQUENCE",
    "ONTOLOGY_MATERIALIZATION_REQUIRED_PROJECTIONS",
    "ONTOLOGY_MATERIALIZATION_RUNTIME",
    "ONTOLOGY_MATERIALIZATION_RUNTIME_CONTEXT",
    "ONTOLOGY_FUNCTION_IMPL_COVERAGE_PROOF_REF",
    "ONTOLOGY_SEMANTIC_WORKFLOWS",
    "ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY",
    "ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_ROLE",
    "ONTOLOGY_RUNTIME_ARTIFACT_SET_CONTRACT_VERSION",
    "ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY",
    "ONTOLOGY_RUNTIME_ONTOLOGY_PACKAGE_NAMES",
    "ONTOLOGY_PACKAGE_ROLE",
    "ONTOLOGY_PACKAGE_ROLES",
    "ONTOLOGY_PROVIDER_OWNER",
    "ONTOLOGY_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA",
    "ONTOLOGY_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION",
    "ONTOLOGY_SEMANTIC_SOURCE_MEANING_CAPABILITY_METADATA",
    "ONTOLOGY_SEMANTIC_SOURCE_MEANING_CAPABILITY_PARTICIPATION",
]
