from __future__ import annotations

from aware_code.module_semantic_contract import (
    ModuleSemanticManifestResolutionDescriptor,
    ModuleSemanticPackageLayoutDescriptor,
    ModuleSemanticPackageRoleDescriptor,
    ModuleSemanticRegistryDescriptor,
    ModuleSemanticRuntimeProjectionPackageDescriptor,
)
from aware_code.semantic_capability_keys import (
    SEMANTIC_ANALYSIS_CAPABILITY,
    SEMANTIC_MATERIALIZATION_CAPABILITY,
)


EXPERIENCE_PROVIDER_OWNER = "aware_experience.provider"
EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY = (
    "semantic_operation_function_call_resolution"
)

EXPERIENCE_PACKAGE_ROLES = (
    ModuleSemanticPackageRoleDescriptor(
        role=EXPERIENCE_PROVIDER_OWNER,
        contract="aware.semantic_provider",
        package_kind="runtime",
        capabilities=(
            "diagnostics",
            "semantic_tokens",
            SEMANTIC_ANALYSIS_CAPABILITY,
            SEMANTIC_MATERIALIZATION_CAPABILITY,
            "semantic_source_meaning",
            EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY,
        ),
        owns_manifest_kinds=("aware_experience_toml",),
    ),
)

EXPERIENCE_MANIFEST_RESOLUTION = (
    ModuleSemanticManifestResolutionDescriptor(
        semantic_owner=EXPERIENCE_PROVIDER_OWNER,
        manifest_kind="aware_experience_toml",
        filename="aware.experience.toml",
        contract="aware.experience",
        loader_module="aware_experience.manifest.loader",
        loader_name="load_aware_experience_toml_spec",
        workspace_manifest_kind="experience",
        package_role=EXPERIENCE_PROVIDER_OWNER,
        semantic_package_family="experience",
        semantic_package_kind="experience_package",
        semantic_projection_name="ExperiencePackage",
        semantic_root_kind="environment_experience",
        code_package_surface="experience",
        workspace_materialization_order=200,
        workspace_materialization_branch="semantic",
        workspace_materialization_commit=True,
        workspace_materialization_primary=True,
        copy_code_package_metadata_keys=(
            "fqn_prefix",
            "package_kind",
            "environment_handle",
        ),
        semantic_package_metadata={
            "dependency_attribute_name": "dependencies",
            "workspace_materialization_runtime_index": "workspace_experience",
        },
        priority=200,
    ),
)

EXPERIENCE_PACKAGE_LAYOUT = (
    ModuleSemanticPackageLayoutDescriptor(
        semantic_owner=EXPERIENCE_PROVIDER_OWNER,
        manifest_kinds=("aware_experience_toml",),
        callable_module="aware_experience.semantic_package_layout",
        callable_name="resolve_experience_python_package_layout",
        priority=100,
    ),
)

EXPERIENCE_RUNTIME_PROJECTION_PACKAGES = (
    ModuleSemanticRuntimeProjectionPackageDescriptor(
        package_name="experience-ontology",
        projection_names=(
            "ActionExperience",
            "ActuatorConfig",
            "ActuatorInvocationActionConfig",
            "ConnectorConfig",
            "ConnectorProvider",
            "EnvironmentExperience",
            "EnvironmentExperienceProfileConfig",
            "EnvironmentExperienceProfile",
            "EnvironmentTopologySeed",
            "ExperiencePackage",
            "ExperiencePackageApiPackage",
            "ExperiencePackageAttentionPackage",
            "ExperiencePackageDependency",
            "ExperiencePackageSdkPackage",
            "ExperienceInvocationActionConfig",
            "ProgramConfig",
            "ProgramConfigGraph",
            "ProgramImpl",
            "ProjectionExperience",
            "ProjectionExperienceGraph",
            "ProjectionExperienceOIGI",
            "ProjectionExperienceSectionGraphBinding",
            "SensorConfig",
            "SensorInvocationActionConfig",
        ),
    ),
    ModuleSemanticRuntimeProjectionPackageDescriptor(
        package_name="api-ontology",
        projection_names=("Api", "ApiPackage"),
    ),
    ModuleSemanticRuntimeProjectionPackageDescriptor(
        package_name="code-ontology",
        projection_names=("CodePackage",),
    ),
    ModuleSemanticRuntimeProjectionPackageDescriptor(
        package_name="identity-ontology",
        projection_names=("ActorConfig", "RoleConfig"),
    ),
    ModuleSemanticRuntimeProjectionPackageDescriptor(
        package_name="meta-ontology",
        projection_names=("ObjectInstanceGraphIdentity",),
    ),
    ModuleSemanticRuntimeProjectionPackageDescriptor(
        package_name="environment-ontology",
        projection_names=("ThreadConfig",),
    ),
)

AWARE_MODULE_SEMANTIC_REGISTRY_DESCRIPTOR = ModuleSemanticRegistryDescriptor(
    provider_key="aware_experience",
    package_roles=EXPERIENCE_PACKAGE_ROLES,
    manifest_resolution=EXPERIENCE_MANIFEST_RESOLUTION,
    package_layout=EXPERIENCE_PACKAGE_LAYOUT,
    runtime_projection_packages=EXPERIENCE_RUNTIME_PROJECTION_PACKAGES,
)

__all__ = [
    "AWARE_MODULE_SEMANTIC_REGISTRY_DESCRIPTOR",
    "EXPERIENCE_MANIFEST_RESOLUTION",
    "EXPERIENCE_PACKAGE_ROLES",
    "EXPERIENCE_PACKAGE_LAYOUT",
    "EXPERIENCE_PROVIDER_OWNER",
    "EXPERIENCE_RUNTIME_PROJECTION_PACKAGES",
    "EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY",
]
