from __future__ import annotations

from aware_code.module_semantic_contract import (
    ModuleSemanticManifestResolutionDescriptor,
    ModuleSemanticPackageRoleDescriptor,
    ModuleSemanticRegistryDescriptor,
    ModuleSemanticRuntimeProjectionPackageDescriptor,
)
from aware_code.semantic_capability_keys import (
    SEMANTIC_ANALYSIS_CAPABILITY,
    SEMANTIC_MATERIALIZATION_CAPABILITY,
)


API_PROVIDER_OWNER = "aware_api.provider"
API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY = (
    "semantic_operation_function_call_resolution"
)

API_PACKAGE_ROLES = (
    ModuleSemanticPackageRoleDescriptor(
        role=API_PROVIDER_OWNER,
        contract="aware.semantic_provider",
        package_kind="runtime",
        capabilities=(
            SEMANTIC_ANALYSIS_CAPABILITY,
            "diagnostics",
            "semantic_tokens",
            API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY,
            SEMANTIC_MATERIALIZATION_CAPABILITY,
        ),
        owns_manifest_kinds=("aware_api_toml",),
    ),
)

API_MANIFEST_RESOLUTION = (
    ModuleSemanticManifestResolutionDescriptor(
        semantic_owner=API_PROVIDER_OWNER,
        manifest_kind="aware_api_toml",
        filename="aware.api.toml",
        contract="aware.api",
        loader_module="aware_api_runtime.manifest.loader",
        loader_name="load_aware_api_toml_spec",
        workspace_manifest_kind="api",
        package_role=API_PROVIDER_OWNER,
        semantic_package_family="api",
        semantic_package_kind="api_package",
        semantic_projection_name="ApiPackage",
        semantic_root_kind="api",
        code_package_surface="api",
        workspace_materialization_order=100,
        workspace_materialization_branch="semantic",
        workspace_materialization_commit=True,
        workspace_materialization_primary=True,
        copy_code_package_metadata_keys=("fqn_prefix", "package_kind"),
        semantic_package_metadata={
            "dependency_attribute_name": "dependencies",
            "metadata_resolver_module": "aware_api_runtime.semantic_package",
            "metadata_resolver_name": "api_semantic_package_metadata",
        },
        priority=100,
    ),
)

API_RUNTIME_PROJECTION_PACKAGES = (
    ModuleSemanticRuntimeProjectionPackageDescriptor(
        package_name="api-ontology",
        projection_names=("Api", "ApiCall", "ApiPackage"),
    ),
    ModuleSemanticRuntimeProjectionPackageDescriptor(
        package_name="code-ontology",
        projection_names=("CodePackage", "CodePackageConfig"),
    ),
)

AWARE_MODULE_SEMANTIC_REGISTRY_DESCRIPTOR = ModuleSemanticRegistryDescriptor(
    provider_key="aware_api",
    package_roles=API_PACKAGE_ROLES,
    manifest_resolution=API_MANIFEST_RESOLUTION,
    runtime_projection_packages=API_RUNTIME_PROJECTION_PACKAGES,
)

__all__ = [
    "API_MANIFEST_RESOLUTION",
    "API_PACKAGE_ROLES",
    "API_PROVIDER_OWNER",
    "API_RUNTIME_PROJECTION_PACKAGES",
    "API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY",
    "AWARE_MODULE_SEMANTIC_REGISTRY_DESCRIPTOR",
]
