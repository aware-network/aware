from __future__ import annotations

from pathlib import Path

from aware_api_runtime.manifest.loader import load_aware_api_toml_spec
from aware_api_runtime.semantic_contract import (
    AWARE_API_SEMANTIC_CONTRACT,
    API_CAPABILITY_PARTICIPATION,
    API_MANIFEST_RESOLUTION,
    API_MATERIALIZATION_INPUTS,
    API_MATERIALIZATION_REQUIRED_PROJECTIONS,
    API_MATERIALIZATION_RUNTIME,
    API_MATERIALIZATION_RUNTIME_CONTEXT,
    API_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES,
    API_PROVIDER_OWNER,
    API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA,
    API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION,
    API_SEMANTIC_WORKFLOWS,
)
from aware_api_runtime.semantic_function_refs import (
    API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
    API_CAPABILITY_ENDPOINT_CREATE_OPERATION,
    API_CAPABILITY_CREATE_OPERATION,
    API_CREATE_FUNCTION_REF,
    API_CREATE_OPERATION,
    API_SEMANTIC_FUNCTION_CALL_BINDING_REFS,
    API_SEMANTIC_FUNCTION_REFS,
    API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY,
    API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION,
    API_SEMANTIC_OPERATION_TYPES,
)
from aware_api_runtime.semantic_package import api_semantic_package_metadata
from aware_code.module_plugin_registry import AwareModulePluginRegistry

_RUNTIME_CONTEXT_CONTRACT = (
    "API-owned Workspace semantic materialization runtime context"
)
_API_MODULE_ROOT = Path(__file__).resolve().parents[4]


def _bootstrap_api_module_plugin() -> None:
    AwareModulePluginRegistry.clear()
    AwareModulePluginRegistry.ensure_module_plugins_registered_from_module_roots(
        module_roots=(_API_MODULE_ROOT,),
    )


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_api_declares_compile_plan_materialization_input() -> None:
    assert len(API_MATERIALIZATION_INPUTS) == 1
    descriptor = API_MATERIALIZATION_INPUTS[0]

    assert descriptor.semantic_owner == API_PROVIDER_OWNER
    assert descriptor.input_key == "aware_api.compile_plan"
    assert descriptor.input_kind == "compile_plan"
    assert descriptor.artifact_family == "api_compile_plan"
    assert descriptor.artifact_role == "compile_plan"
    assert descriptor.package_family == "api"
    assert descriptor.semantic_kind == "api_package"
    assert descriptor.runtime_contract_version == "aware.api.compile_plan.v1"


def test_api_declares_meta_side_semantic_operation_contract() -> None:
    contract = AWARE_API_SEMANTIC_CONTRACT

    assert contract.capability_participation == API_CAPABILITY_PARTICIPATION
    operation_resolution = (
        API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION[0]
    )
    assert operation_resolution.capability == (
        API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY
    )
    assert operation_resolution.semantic_owner == API_PROVIDER_OWNER
    assert operation_resolution.metadata == (
        API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA
    )
    assert operation_resolution.metadata["contract_version"] == (
        API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION
    )
    assert operation_resolution.metadata["callable_module"] == (
        "aware_api_runtime.semantic_functions.resolution"
    )
    assert operation_resolution.metadata["callable_name"] == (
        "resolve_api_semantic_function_call_plan_previews"
    )
    assert operation_resolution.metadata["supported_semantic_operation_types"] == (
        API_SEMANTIC_OPERATION_TYPES
    )
    assert operation_resolution.metadata["semantic_operation_type_refs"] == (
        API_SEMANTIC_OPERATION_TYPES
    )
    assert {
        API_CREATE_OPERATION,
        API_CAPABILITY_CREATE_OPERATION,
        API_CAPABILITY_ENDPOINT_CREATE_OPERATION,
    }.issubset(set(operation_resolution.metadata["semantic_operation_type_refs"]))
    assert operation_resolution.metadata["function_call_binding_refs"] == (
        API_SEMANTIC_FUNCTION_CALL_BINDING_REFS
    )
    assert operation_resolution.metadata["ontology_function_refs"] == tuple(
        sorted(API_SEMANTIC_FUNCTION_REFS)
    )
    assert {
        API_CREATE_FUNCTION_REF,
        API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
    }.issubset(set(operation_resolution.metadata["ontology_function_refs"]))
    assert operation_resolution.metadata["semantic_apply_boundary"] == (
        "ontology_function_call"
    )
    assert operation_resolution.metadata["mutates"] is False
    assert operation_resolution.metadata["execution_status"] == "not_requested"
    workflow = API_SEMANTIC_WORKFLOWS[0]
    assert API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY in (
        workflow.capability_refs
    )
    assert "api.semantic_function_call.plan_preview" in workflow.expected_proof_refs
    assert "api.semantic_operation_function_call_resolution" in (
        workflow.expected_receipt_refs
    )
    assert workflow.grammar_profile_refs == (
        "workspace.code.grammar_profile.semantic_contracts",
    )
    assert workflow.source_meaning_refs == ("aware_api.semantic_source_meaning",)
    assert not any(
        str(ref).startswith("aware_meta.")
        for ref in operation_resolution.metadata["semantic_operation_type_refs"]
    )


def test_api_compile_plan_input_resolves_through_registry() -> None:
    _bootstrap_api_module_plugin()
    descriptors = (
        AwareModulePluginRegistry.semantic_materialization_inputs_for_provider_key(
            provider_key="aware_api",
            semantic_owner=API_PROVIDER_OWNER,
            input_key="aware_api.compile_plan",
            input_kind="compile_plan",
            artifact_family="api_compile_plan",
            package_family="api",
            semantic_kind="api_package",
        )
    )

    assert descriptors == API_MATERIALIZATION_INPUTS


def test_api_meta_mutation_contract_resolves_through_registry() -> None:
    _bootstrap_api_module_plugin()
    contract = AwareModulePluginRegistry.module_semantic_contract_for_provider_key(
        "aware_api"
    )

    assert contract is not None
    assert (
        API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION[0]
        in contract.capability_participation
    )
    provider_role = contract.package_role_for(role=API_PROVIDER_OWNER)
    assert provider_role is not None
    assert API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY in (
        provider_role.capabilities
    )


def test_api_materialization_runtime_uses_ontology_package_names() -> None:
    assert len(API_MATERIALIZATION_RUNTIME) == 1
    descriptor = API_MATERIALIZATION_RUNTIME[0]

    assert descriptor.semantic_owner == API_PROVIDER_OWNER
    assert (
        descriptor.runtime_ontology_package_names
        == API_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
    )
    assert descriptor.lane_projection_name == "ApiPackage"
    assert descriptor.required_projection_names == (
        API_MATERIALIZATION_REQUIRED_PROJECTIONS
    )
    projection_packages = {
        package.package_name: package.projection_names
        for package in descriptor.runtime_projection_packages
    }
    assert projection_packages["api-ontology"] == ("Api", "ApiPackage")
    assert projection_packages["code-ontology"] == (
        "CodePackage",
        "CodePackageConfig",
    )
    assert descriptor.include_package_dependency_closure is True


def test_api_declares_api_owned_materialization_runtime_context() -> None:
    assert len(API_MATERIALIZATION_RUNTIME_CONTEXT) == 1
    descriptor = API_MATERIALIZATION_RUNTIME_CONTEXT[0]

    assert descriptor.semantic_owner == API_PROVIDER_OWNER
    assert (
        descriptor.callable_module
        == "aware_api_runtime.runtime_context.workspace_materialization"
    )
    assert descriptor.callable_name == (
        "build_api_workspace_materialization_runtime_context"
    )
    assert descriptor.required is True
    assert descriptor.provider_payload == {
        "contract": _RUNTIME_CONTEXT_CONTRACT,
        "runtime_ontology_package_names": (
            API_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
        ),
    }


def test_api_runtime_context_resolves_through_registry() -> None:
    _bootstrap_api_module_plugin()
    resolve_contexts = (
        AwareModulePluginRegistry.semantic_materialization_runtime_context_for_provider_key
    )
    descriptors = resolve_contexts(
        provider_key="aware_api",
        semantic_owner=API_PROVIDER_OWNER,
    )

    assert descriptors == API_MATERIALIZATION_RUNTIME_CONTEXT


def test_api_runtime_context_callable_resolves_through_registry() -> None:
    _bootstrap_api_module_plugin()
    resolve_contexts = (
        AwareModulePluginRegistry.resolve_semantic_materialization_runtime_context_resolvers
    )
    resolvers = resolve_contexts(
        provider_key="aware_api",
        semantic_owner=API_PROVIDER_OWNER,
    )

    assert len(resolvers) == 1
    resolver = resolvers[0]
    assert resolver.provider_key == "aware_api"
    assert resolver.semantic_owner == API_PROVIDER_OWNER
    assert (
        resolver.callable_module
        == "aware_api_runtime.runtime_context.workspace_materialization"
    )
    assert resolver.callable_name == (
        "build_api_workspace_materialization_runtime_context"
    )
    assert resolver.required is True


def test_api_manifest_resolution_declares_generated_python_package_metadata_resolver(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    api_root = workspace_root / "modules" / "code" / "apis" / "code"
    manifest_path = api_root / "aware.api.toml"
    _write(
        manifest_path,
        "\n".join(
            (
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "code-service-api"',
                'fqn_prefix = "aware_code_service_api"',
                "version_number = 1",
                "",
                "[build]",
                'sources_dir = "bindings"',
                'compilation_mode = "api_ontology"',
                "",
                "[targets.python]",
                'root_dir = "python"',
                "",
                "[targets.python.public_package]",
                'package_dir = "aware_code_service_api"',
                "",
                "[targets.python.service_protocol]",
                'package_dir = "aware_code_service_protocol"',
                "",
                "[[dependencies]]",
                'package_name = "code-service-dto"',
                "",
                "[[semantic_package_exports]]",
                'kind = "api_dto"',
                'package_name = "code-service-dto"',
                'manifest_path = "dto/aware.toml"',
                "",
            )
        ),
    )
    _write(
        api_root / "dto" / "aware.toml",
        "\n".join(
            (
                "aware = 1",
                "",
                "[package]",
                'package_name = "code-service-dto"',
                'fqn_prefix = "aware_code_service_dto"',
                'kind = "api"',
                "",
            )
        ),
    )
    for package_dir, package_name in (
        ("aware_code_service_api", "aware_code_service_api"),
        ("aware_code_service_protocol", "aware_code_service_protocol"),
        ("aware_code_service_dto", "aware_code_service_dto"),
    ):
        _write(
            api_root / "python" / package_dir / "pyproject.toml",
            "\n".join(
                (
                    "[project]",
                    f'name = "{package_name}"',
                    'version = "0.1.0"',
                    "",
                )
            ),
        )
        _write(
            api_root / "python" / package_dir / package_dir / "__init__.py",
            "",
        )

    resolver_metadata = API_MANIFEST_RESOLUTION[0].semantic_package_metadata
    assert resolver_metadata is not None
    assert resolver_metadata["metadata_resolver_module"] == (
        "aware_api_runtime.semantic_package"
    )
    assert resolver_metadata["metadata_resolver_name"] == (
        "api_semantic_package_metadata"
    )

    manifest_spec = load_aware_api_toml_spec(toml_path=manifest_path)
    metadata = api_semantic_package_metadata(
        workspace_root=workspace_root,
        package_root=api_root,
        manifest_path=manifest_path,
        manifest_spec=manifest_spec,
    )

    targets = {
        target["role"]: target
        for target in metadata["language_materialization_targets"]
    }
    assert targets["public_package"] == {
        "role": "public_package",
        "language": "python",
        "output_dir": "python/aware_code_service_api",
        "import_root": "aware_code_service_api",
        "package_name": "aware_code_service_api",
        "materialization_source": "api",
        "code_package_surface": "api",
    }
    assert targets["service_protocol_package"] == {
        "role": "service_protocol_package",
        "language": "python",
        "output_dir": "python/aware_code_service_protocol",
        "import_root": "aware_code_service_protocol",
        "package_name": "aware_code_service_protocol",
        "materialization_source": "api",
        "code_package_surface": "api",
    }
    assert targets["api_dto"] == {
        "role": "api_dto",
        "language": "python",
        "output_dir": "python/aware_code_service_dto",
        "import_root": "aware_code_service_dto",
        "package_name": "aware_code_service_dto",
        "materialization_source": "api",
        "code_package_surface": "api",
    }
