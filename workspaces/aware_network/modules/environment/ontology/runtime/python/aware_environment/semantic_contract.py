from __future__ import annotations

from aware_code.module_semantic_contract import (
    ModuleCapabilityExecutionPolicyDescriptor,
    ModuleSemanticContract,
    ModuleSemanticManifestResolutionDescriptor,
    ModuleSemanticMaterializationArtifactOutputDescriptor,
    ModuleSemanticMaterializationRuntimeContextDescriptor,
    ModuleSemanticMaterializationRuntimeDescriptor,
    ModuleSemanticPackageRoleDescriptor,
    ModuleSemanticRuntimeProjectionPackageDescriptor,
)
from aware_code.semantic_materialization import (
    SEMANTIC_MATERIALIZATION_CAPABILITY,
)
from aware_code.semantic_package.schemas import CapabilityParticipationDescriptor
from aware_ontology.semantic_contract import (
    ONTOLOGY_MATERIALIZATION_REQUIRED_PROJECTIONS,
)


ENVIRONMENT_ENVIRONMENT_CONFIG_PROVIDER_OWNER = (
    "aware_environment.environment_config.provider"
)
ENVIRONMENT_PROFILE_PROVIDER_OWNER = "aware_environment.profile.provider.deprecated"
ENVIRONMENT_PROVIDER_OWNER = ENVIRONMENT_ENVIRONMENT_CONFIG_PROVIDER_OWNER
ENVIRONMENT_ENVIRONMENT_CONFIG_REQUIRED_PROJECTIONS = (
    *ONTOLOGY_MATERIALIZATION_REQUIRED_PROJECTIONS,
    "EnvironmentConfigPackage",
    "EnvironmentConfig",
    "EnvironmentProfileConfig",
    "EnvironmentSessionConfig",
)
ENVIRONMENT_PROFILE_REQUIRED_PROJECTIONS: tuple[str, ...] = ()
ENVIRONMENT_MATERIALIZATION_REQUIRED_PROJECTIONS = (
    ENVIRONMENT_ENVIRONMENT_CONFIG_REQUIRED_PROJECTIONS
)
ENVIRONMENT_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES = ("environment-ontology",)
ENVIRONMENT_MATERIALIZATION_OWNER_SEQUENCE = (
    ENVIRONMENT_ENVIRONMENT_CONFIG_PROVIDER_OWNER,
)

ENVIRONMENT_MATERIALIZATION_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
        metadata={
            "runtime_artifact_policy": "ontology_owned_pointer_only",
            "semantic_package_root": "EnvironmentConfigPackage",
            "topology_root": "EnvironmentConfig",
        },
    )
    for semantic_owner in ENVIRONMENT_MATERIALIZATION_OWNER_SEQUENCE
)

ENVIRONMENT_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY = (
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=ENVIRONMENT_ENVIRONMENT_CONFIG_PROVIDER_OWNER,
        callable_module="aware_environment.materialization.environment_workspace_provider",
        callable_name="materialize",
        priority=90,
    ),
)

ENVIRONMENT_PACKAGE_ROLES = (
    ModuleSemanticPackageRoleDescriptor(
        role=ENVIRONMENT_ENVIRONMENT_CONFIG_PROVIDER_OWNER,
        contract="aware.semantic_provider",
        package_kind="runtime",
        capabilities=(SEMANTIC_MATERIALIZATION_CAPABILITY,),
        owns_manifest_kinds=("aware_environment_toml",),
    ),
)

ENVIRONMENT_MANIFEST_RESOLUTION = (
    ModuleSemanticManifestResolutionDescriptor(
        semantic_owner=ENVIRONMENT_ENVIRONMENT_CONFIG_PROVIDER_OWNER,
        manifest_kind="aware_environment_toml",
        filename="aware.environment.toml",
        contract="aware.environment",
        loader_module="aware_environment.manifest.environment_loader",
        loader_name="load_aware_environment_spec",
        workspace_manifest_kind="environment",
        package_role=ENVIRONMENT_ENVIRONMENT_CONFIG_PROVIDER_OWNER,
        semantic_package_family="environment",
        semantic_package_kind="environment_config_package",
        semantic_projection_name="EnvironmentConfigPackage",
        semantic_root_kind="environment_config",
        code_package_surface="environment",
        semantic_package_metadata={
            "package_section_name": "environment",
            "package_name_attribute": "handle",
            "package_name_template": "{value}-environment",
        },
        workspace_materialization_order=90,
        workspace_materialization_branch="lane",
        workspace_materialization_commit=True,
        workspace_materialization_primary=True,
        copy_code_package_metadata_keys=("environment_handle", "package_kind"),
        priority=90,
    ),
)

ENVIRONMENT_MATERIALIZATION_ARTIFACT_OUTPUTS = (
    ModuleSemanticMaterializationArtifactOutputDescriptor(
        semantic_owner=ENVIRONMENT_ENVIRONMENT_CONFIG_PROVIDER_OWNER,
        producer_provider_key="aware_environment",
        producer_key="aware_environment.environment.runtime_module_support_file",
        output_key="environment_runtime_module_support_file",
        artifact_family="environment_runtime",
        artifact_role="module_runtime_support_file",
        artifact_path_pattern="**",
        manifest_relpath="aware.environment.toml",
        media_type="application/msgpack",
        runtime_contract_version=(
            "aware.environment.environment_runtime_module_support_file.v1"
        ),
        required_for=("deployment", "runtime_index"),
        provider_payload={
            "contract": (
                "Environment-owned EnvironmentConfig runtime support artifact "
                "ref emitted as WorkspaceRevision artifact truth."
            )
        },
    ),
)

ENVIRONMENT_MATERIALIZATION_RUNTIME = (
    ModuleSemanticMaterializationRuntimeDescriptor(
        semantic_owner=ENVIRONMENT_ENVIRONMENT_CONFIG_PROVIDER_OWNER,
        runtime_ontology_package_names=(
            ENVIRONMENT_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
        ),
        lane_projection_name="EnvironmentConfigPackage",
        required_projection_names=(ENVIRONMENT_ENVIRONMENT_CONFIG_REQUIRED_PROJECTIONS),
        runtime_projection_packages=(
            ModuleSemanticRuntimeProjectionPackageDescriptor(
                package_name="environment-ontology",
                projection_names=(
                    "EnvironmentConfigPackage",
                    "EnvironmentConfig",
                    "EnvironmentProfileConfig",
                    "EnvironmentSessionConfig",
                ),
            ),
        ),
        environment_handle="workspace-semantic-materialization",
        include_package_dependency_closure=True,
        priority=90,
    ),
)

ENVIRONMENT_MATERIALIZATION_RUNTIME_CONTEXT = (
    ModuleSemanticMaterializationRuntimeContextDescriptor(
        semantic_owner=ENVIRONMENT_ENVIRONMENT_CONFIG_PROVIDER_OWNER,
        callable_module="aware_environment.materialization.runtime_context",
        callable_name="build_environment_workspace_materialization_runtime_context",
        required=True,
        priority=90,
        provider_payload={
            "contract": (
                "Environment-owned EnvironmentConfigPackage Workspace "
                "semantic materialization runtime context"
            ),
            "runtime_ontology_package_names": (
                ENVIRONMENT_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
            ),
        },
    ),
)

AWARE_ENVIRONMENT_SEMANTIC_CONTRACT = ModuleSemanticContract(
    provider_key="aware_environment",
    capability_participation=ENVIRONMENT_MATERIALIZATION_CAPABILITY_PARTICIPATION,
    capability_execution_policy=(
        ENVIRONMENT_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY
    ),
    package_roles=ENVIRONMENT_PACKAGE_ROLES,
    manifest_resolution=ENVIRONMENT_MANIFEST_RESOLUTION,
    materialization_artifact_outputs=ENVIRONMENT_MATERIALIZATION_ARTIFACT_OUTPUTS,
    materialization_runtime=ENVIRONMENT_MATERIALIZATION_RUNTIME,
    materialization_runtime_context=ENVIRONMENT_MATERIALIZATION_RUNTIME_CONTEXT,
)
AWARE_MODULE_SEMANTIC_CONTRACT = AWARE_ENVIRONMENT_SEMANTIC_CONTRACT


__all__ = [
    "AWARE_MODULE_SEMANTIC_CONTRACT",
    "AWARE_ENVIRONMENT_SEMANTIC_CONTRACT",
    "ENVIRONMENT_ENVIRONMENT_CONFIG_PROVIDER_OWNER",
    "ENVIRONMENT_ENVIRONMENT_CONFIG_REQUIRED_PROJECTIONS",
    "ENVIRONMENT_MANIFEST_RESOLUTION",
    "ENVIRONMENT_MATERIALIZATION_ARTIFACT_OUTPUTS",
    "ENVIRONMENT_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY",
    "ENVIRONMENT_MATERIALIZATION_CAPABILITY_PARTICIPATION",
    "ENVIRONMENT_MATERIALIZATION_OWNER_SEQUENCE",
    "ENVIRONMENT_MATERIALIZATION_REQUIRED_PROJECTIONS",
    "ENVIRONMENT_MATERIALIZATION_RUNTIME",
    "ENVIRONMENT_MATERIALIZATION_RUNTIME_CONTEXT",
    "ENVIRONMENT_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES",
    "ENVIRONMENT_PACKAGE_ROLES",
    "ENVIRONMENT_PROFILE_PROVIDER_OWNER",
    "ENVIRONMENT_PROFILE_REQUIRED_PROJECTIONS",
    "ENVIRONMENT_PROVIDER_OWNER",
]
