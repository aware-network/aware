from __future__ import annotations

from aware_code.module_semantic_contract import (
    ModuleCapabilityExecutionPolicyDescriptor,
    ModuleSemanticContract,
    ModuleSemanticManifestResolutionDescriptor,
    ModuleSemanticMaterializationRuntimeContextDescriptor,
    ModuleSemanticMaterializationRuntimeDescriptor,
    ModuleSemanticPackageRoleDescriptor,
    ModuleSemanticRuntimeProjectionPackageDescriptor,
)
from aware_code.semantic_materialization import (
    SEMANTIC_MATERIALIZATION_CAPABILITY,
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_ENTRYPOINT,
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY,
    SEMANTIC_PROVIDER_DELTA_FUNCTIONAL_MATERIALIZATION_KEY,
    SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_CONTRACT_VERSION,
    SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_KEY,
    SEMANTIC_PROVIDER_DELTA_REQUEST_CONTRACT_VERSION,
    SEMANTIC_PROVIDER_DELTA_RESULT_CONTRACT_VERSION,
)
from aware_code.semantic_package.schemas import CapabilityParticipationDescriptor


CODE_SECTION_OWNER = "aware_code.section"
CODE_MODULE_OWNER = "aware_code.module"
CODE_PROVIDER_OWNER = "aware_code.provider"
CODE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES = ("code-ontology",)
CODE_MATERIALIZATION_REQUIRED_PROJECTIONS = ("CodePackage",)

CODE_PROVIDER_DELTA_OPERATION: dict[str, object] = {
    "case_key": "aware_code.code_package_text_snapshot.delta",
    "provider_operation_type": "code_package.text_snapshot",
    "ontology_subject_kind": "code_package",
    "operation_family": "upsert",
    "source_projection_policy": "public_graph_only_ready",
    "workspace_delta_first_mode": "public_graph_only_ready",
    "workspace_delta_first_ready": True,
}
CODE_PROVIDER_DELTA_PRODUCT_READINESS: dict[str, object] = {
    "readiness_kind": "aware_code.code_package_delta_product_readiness",
    "contract_version": SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_CONTRACT_VERSION,
    "provider_contract_version": "aware.code.code-package-delta-coverage.v1",
    "provider_key": "aware_code",
    "status": "ready",
    "reason": "code_package_text_snapshot_delta_ready",
    "default_policy": "ready_operations_only",
    "fallback_policy": "explicit_fallback_required",
    "operation_count": 1,
    "ready_operation_count": 1,
    "render_all_required_operation_count": 0,
    "blocked_operation_count": 0,
    "workspace_delta_first_default_policy": (
        "public_lifecycle_ready_operations_only"
    ),
    "workspace_delta_first_ready_operation_count": 1,
    "workspace_delta_first_mode_counts": {"public_graph_only_ready": 1},
    "workspace_delta_first_ready_operations": (CODE_PROVIDER_DELTA_OPERATION,),
    "ready_operations": (CODE_PROVIDER_DELTA_OPERATION,),
    "render_all_required_operations": (),
    "blocked_operations": (),
}
CODE_MATERIALIZATION_DELTA_ADAPTER_METADATA: dict[str, object] = {
    "callable_module": "aware_code.materialization.workspace_provider",
    "callable_name": SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_ENTRYPOINT,
    "request_contract_version": SEMANTIC_PROVIDER_DELTA_REQUEST_CONTRACT_VERSION,
    "result_contract_version": SEMANTIC_PROVIDER_DELTA_RESULT_CONTRACT_VERSION,
    SEMANTIC_PROVIDER_DELTA_FUNCTIONAL_MATERIALIZATION_KEY: True,
    SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_KEY: (
        CODE_PROVIDER_DELTA_PRODUCT_READINESS
    ),
}
CODE_MATERIALIZATION_CAPABILITY_METADATA: dict[str, object] = {
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY: (
        CODE_MATERIALIZATION_DELTA_ADAPTER_METADATA
    ),
}

CODE_CAPABILITY_PARTICIPATION = (
    CapabilityParticipationDescriptor(
        capability="semantic_tokens",
        semantic_owner=CODE_SECTION_OWNER,
    ),
    CapabilityParticipationDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=CODE_PROVIDER_OWNER,
        metadata=CODE_MATERIALIZATION_CAPABILITY_METADATA,
    ),
)

CODE_CAPABILITY_EXECUTION_POLICY = (
    ModuleCapabilityExecutionPolicyDescriptor(
        capability="semantic_tokens",
        semantic_owner=CODE_SECTION_OWNER,
        callable_name="_sections_provider",
        priority=130,
    ),
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=CODE_PROVIDER_OWNER,
        callable_module="aware_code.materialization.workspace_provider",
        callable_name="materialize",
        priority=20,
    ),
)

CODE_PACKAGE_ROLES = (
    ModuleSemanticPackageRoleDescriptor(
        role=CODE_MODULE_OWNER,
        contract="aware.code_module",
        package_kind="module",
        owns_manifest_kinds=("aware_module_toml",),
    ),
    ModuleSemanticPackageRoleDescriptor(
        role=CODE_PROVIDER_OWNER,
        contract="aware.semantic_provider",
        package_kind="runtime",
        capabilities=(SEMANTIC_MATERIALIZATION_CAPABILITY,),
        owns_manifest_kinds=("pyproject_toml", "setup_py", "pubspec_yaml"),
    ),
)

CODE_MANIFEST_RESOLUTION = (
    ModuleSemanticManifestResolutionDescriptor(
        semantic_owner=CODE_MODULE_OWNER,
        manifest_kind="aware_module_toml",
        filename="aware.module.toml",
        contract="aware.code_module",
        loader_module="aware_code.module_manifest.loader",
        loader_name="load_aware_module_spec",
        workspace_manifest_kind="module",
        package_role=CODE_MODULE_OWNER,
        code_package_surface="structure",
        priority=-50,
    ),
    ModuleSemanticManifestResolutionDescriptor(
        semantic_owner=CODE_PROVIDER_OWNER,
        manifest_kind="pyproject_toml",
        filename="pyproject.toml",
        contract="aware.semantic_provider",
        loader_module="aware_code.package.manifest_loader",
        loader_name="load_pyproject_toml_package_manifest",
        package_role=CODE_PROVIDER_OWNER,
        semantic_package_family="code",
        semantic_package_kind="code_package",
        semantic_projection_name="CodePackage",
        semantic_root_kind="code_package",
        code_package_surface="runtime",
        copy_code_package_metadata_keys=(
            "package_manager_name_key",
            "package_dependency_names",
            "package_dependency_keys",
        ),
        priority=20,
    ),
    ModuleSemanticManifestResolutionDescriptor(
        semantic_owner=CODE_PROVIDER_OWNER,
        manifest_kind="setup_py",
        filename="setup.py",
        contract="aware.semantic_provider",
        loader_module="aware_code.package.manifest_loader",
        loader_name="load_setup_py_package_manifest",
        package_role=CODE_PROVIDER_OWNER,
        semantic_package_family="code",
        semantic_package_kind="code_package",
        semantic_projection_name="CodePackage",
        semantic_root_kind="code_package",
        code_package_surface="runtime",
        priority=21,
    ),
    ModuleSemanticManifestResolutionDescriptor(
        semantic_owner=CODE_PROVIDER_OWNER,
        manifest_kind="pubspec_yaml",
        filename="pubspec.yaml",
        contract="aware.semantic_provider",
        loader_module="aware_code.package.manifest_loader",
        loader_name="load_pubspec_yaml_package_manifest",
        package_role=CODE_PROVIDER_OWNER,
        semantic_package_family="code",
        semantic_package_kind="code_package",
        semantic_projection_name="CodePackage",
        semantic_root_kind="code_package",
        code_package_surface="runtime",
        priority=22,
    ),
)

CODE_MATERIALIZATION_RUNTIME = (
    ModuleSemanticMaterializationRuntimeDescriptor(
        semantic_owner=CODE_PROVIDER_OWNER,
        runtime_ontology_package_names=(
            CODE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
        ),
        lane_projection_name="CodePackage",
        required_projection_names=CODE_MATERIALIZATION_REQUIRED_PROJECTIONS,
        runtime_projection_packages=(
            ModuleSemanticRuntimeProjectionPackageDescriptor(
                package_name="code-ontology",
                projection_names=("CodePackage",),
            ),
        ),
        include_package_dependency_closure=True,
        priority=20,
    ),
)
CODE_MATERIALIZATION_RUNTIME_CONTEXT = (
    ModuleSemanticMaterializationRuntimeContextDescriptor(
        semantic_owner=CODE_PROVIDER_OWNER,
        callable_module="aware_code.materialization.runtime_context",
        callable_name="build_code_workspace_materialization_runtime_context",
        required=True,
        priority=20,
        provider_payload={
            "contract": "Code-owned Workspace semantic materialization runtime context",
            "runtime_ontology_package_names": (
                CODE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
            ),
        },
    ),
)

AWARE_CODE_SEMANTIC_CONTRACT = ModuleSemanticContract(
    provider_key="aware_code",
    capability_participation=CODE_CAPABILITY_PARTICIPATION,
    capability_execution_policy=CODE_CAPABILITY_EXECUTION_POLICY,
    package_roles=CODE_PACKAGE_ROLES,
    manifest_resolution=CODE_MANIFEST_RESOLUTION,
    materialization_runtime=CODE_MATERIALIZATION_RUNTIME,
    materialization_runtime_context=CODE_MATERIALIZATION_RUNTIME_CONTEXT,
)
AWARE_MODULE_SEMANTIC_CONTRACT = AWARE_CODE_SEMANTIC_CONTRACT


__all__ = [
    "AWARE_CODE_SEMANTIC_CONTRACT",
    "AWARE_MODULE_SEMANTIC_CONTRACT",
    "CODE_CAPABILITY_EXECUTION_POLICY",
    "CODE_CAPABILITY_PARTICIPATION",
    "CODE_MANIFEST_RESOLUTION",
    "CODE_MATERIALIZATION_CAPABILITY_METADATA",
    "CODE_MATERIALIZATION_DELTA_ADAPTER_METADATA",
    "CODE_MATERIALIZATION_REQUIRED_PROJECTIONS",
    "CODE_MATERIALIZATION_RUNTIME",
    "CODE_MATERIALIZATION_RUNTIME_CONTEXT",
    "CODE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES",
    "CODE_MODULE_OWNER",
    "CODE_PACKAGE_ROLES",
    "CODE_PROVIDER_OWNER",
    "CODE_PROVIDER_DELTA_PRODUCT_READINESS",
    "CODE_SECTION_OWNER",
]
