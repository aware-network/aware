from __future__ import annotations

from pathlib import Path

import pytest

from aware_code.module_semantic_contract import (
    WorkspaceSemanticArtifactBinding,
    WorkspaceSemanticArtifactLeafOwnershipRequest,
)


_TEST_FILE = Path(__file__).resolve()
_KERNEL_WORKSPACE_ROOT = _TEST_FILE.parents[6]
_KERNEL_MODULES_ROOT = _KERNEL_WORKSPACE_ROOT / "modules"


def _prepend_runtime_roots(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for module_id in ("code", "meta", "ontology"):
        monkeypatch.syspath_prepend(
            str(_KERNEL_MODULES_ROOT / module_id / "ontology" / "runtime" / "python")
        )


def test_ontology_semantic_contract_declares_package_roles_and_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_code.semantic_materialization import (
        SEMANTIC_MATERIALIZATION_CAPABILITY,
        SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY,
        SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_ISOLATE_TARGET_MANIFESTS,
        SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_KEY,
        SEMANTIC_PROVIDER_DELTA_FUNCTIONAL_MATERIALIZATION_KEY,
        SEMANTIC_PROVIDER_DELTA_OPERATION_EXECUTION_PROJECTION_NAME_KEY,
    )
    from aware_meta.semantic_contract import (
        META_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY,
        META_LANGUAGE_MATERIALIZATION_GENERATED_FILES_OUTPUT_KEY,
        META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_OUTPUT_KEY,
        META_LANGUAGE_MATERIALIZATION_PACKAGE_OUTPUT_KEY,
        META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
        META_MATERIALIZATION_REQUIRED_PROJECTIONS,
        META_OBJECT_CONFIG_GRAPH_SEMANTIC_OPERATION_TYPES,
        META_OBJECT_CONFIG_GRAPH_SUPPORTED_FUNCTION_CALL_OPERATION_TYPES,
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA,
        META_SEMANTIC_PROJECTION_MUTATION_SCOPE_PAYLOADS,
    )
    from aware_ontology.semantic_contract import (
        AWARE_ONTOLOGY_SEMANTIC_CONTRACT,
        ONTOLOGY_CAPABILITY_PARTICIPATION,
        ONTOLOGY_FUNCTION_IMPL_COVERAGE_PROOF_REF,
        ONTOLOGY_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY,
        ONTOLOGY_MATERIALIZATION_CAPABILITY_PARTICIPATION,
        ONTOLOGY_MATERIALIZATION_DELTA_ADAPTER_METADATA,
        ONTOLOGY_MATERIALIZATION_ARTIFACT_OUTPUTS,
        ONTOLOGY_MATERIALIZATION_REQUIRED_PROJECTIONS,
        ONTOLOGY_MATERIALIZATION_RUNTIME,
        ONTOLOGY_MATERIALIZATION_RUNTIME_CONTEXT,
        ONTOLOGY_MANIFEST_RESOLUTION,
        ONTOLOGY_PACKAGE_ROLE,
        ONTOLOGY_PROVIDER_OWNER,
        ONTOLOGY_RUNTIME_ONTOLOGY_PACKAGE_NAMES,
        ONTOLOGY_SEMANTIC_WORKFLOWS,
        ONTOLOGY_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA,
        ONTOLOGY_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION,
        ONTOLOGY_SEMANTIC_SOURCE_MEANING_CAPABILITY_METADATA,
        ONTOLOGY_SEMANTIC_SOURCE_MEANING_CAPABILITY_PARTICIPATION,
    )
    from aware_ontology.semantic_runtime_catalog import (
        ONTOLOGY_RUNTIME_ARTIFACT_SET_ACTIVATION_POLICY,
        ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY,
        ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_ROLE,
        ONTOLOGY_RUNTIME_ARTIFACT_SET_CONTRACT_VERSION,
        ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY,
        ONTOLOGY_RUNTIME_ARTIFACT_SET_REQUIRED_FOR,
    )
    from aware_meta.semantic_operation_resolution import (
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_TYPE_UPDATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_LOAD_POLICY_UPDATE_OPERATION,
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY,
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION,
    )
    from aware_meta.semantic_projection_mutation_scope import (
        META_SEMANTIC_PROJECTION_MUTATION_SCOPES_METADATA_KEY,
    )

    contract = AWARE_ONTOLOGY_SEMANTIC_CONTRACT

    assert contract.provider_key == "aware_ontology"
    assert contract.capability_participation == ONTOLOGY_CAPABILITY_PARTICIPATION
    assert (
        contract.capability_execution_policy
        == ONTOLOGY_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY
    )
    assert ONTOLOGY_MATERIALIZATION_REQUIRED_PROJECTIONS == (
        *META_MATERIALIZATION_REQUIRED_PROJECTIONS,
        "OntologyConfig",
        "OntologyPackage",
    )

    ontology_role = contract.package_role_for(role=ONTOLOGY_PACKAGE_ROLE)
    assert ontology_role is not None
    assert ontology_role.contract == "aware.ontology"
    assert ontology_role.package_kind == "ontology"

    provider_role = contract.package_role_for(role=ONTOLOGY_PROVIDER_OWNER)
    assert provider_role is not None
    assert provider_role.contract == "aware.semantic_provider"
    assert provider_role.package_kind == "runtime"
    assert provider_role.capabilities == (
        "semantic_source_meaning",
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY,
        SEMANTIC_MATERIALIZATION_CAPABILITY,
    )
    assert provider_role.owns_manifest_kinds == ("aware_ontology_toml",)
    assert len(contract.artifact_leaf_ownership) == 1
    artifact_ownership = contract.artifact_leaf_ownership[0]
    assert artifact_ownership.semantic_owner == ONTOLOGY_PROVIDER_OWNER
    assert artifact_ownership.owner_manifest_kinds == ("aware_ontology_toml",)
    assert artifact_ownership.artifact_manifest_kinds == ("pyproject_toml",)
    assert artifact_ownership.callable_module == (
        "aware_ontology.semantic_artifact_ownership"
    )
    assert artifact_ownership.callable_name == (
        "resolve_workspace_semantic_artifact_leaf_ownership"
    )

    runtime = ONTOLOGY_MATERIALIZATION_RUNTIME[0]
    assert runtime.semantic_owner == ONTOLOGY_PROVIDER_OWNER
    assert runtime.runtime_ontology_package_names == (
        ONTOLOGY_RUNTIME_ONTOLOGY_PACKAGE_NAMES
    )
    assert runtime.lane_projection_name == "OntologyPackage"
    assert runtime.required_projection_names == (
        ONTOLOGY_MATERIALIZATION_REQUIRED_PROJECTIONS
    )
    assert runtime.runtime_projection_packages[0].package_name == "ontology-ontology"
    assert runtime.runtime_projection_packages[0].projection_names == (
        "OntologyConfig",
        "OntologyPackage",
    )
    assert runtime.environment_handle == "workspace-semantic-materialization"
    assert runtime.include_package_dependency_closure is False

    runtime_context = ONTOLOGY_MATERIALIZATION_RUNTIME_CONTEXT[0]
    assert runtime_context.semantic_owner == ONTOLOGY_PROVIDER_OWNER
    assert runtime_context.callable_module == ("aware_meta.runtime.graph_context")
    assert runtime_context.callable_name == (
        "build_meta_workspace_materialization_runtime_context"
    )
    assert runtime_context.required is True
    assert runtime_context.provider_payload is not None
    assert runtime_context.provider_payload["runtime_ontology_package_names"] == (
        ONTOLOGY_RUNTIME_ONTOLOGY_PACKAGE_NAMES
    )
    assert runtime_context.provider_payload[
        SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_KEY
    ] == (
        SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_ISOLATE_TARGET_MANIFESTS
    )

    assert contract.semantic_workflows == ONTOLOGY_SEMANTIC_WORKFLOWS
    workflow = ONTOLOGY_SEMANTIC_WORKFLOWS[0]
    assert workflow.workflow_key == "ontology.package.materialization"
    assert workflow.semantic_owner == ONTOLOGY_PROVIDER_OWNER
    assert "semantic.ontology.verify_runtime_coverage" in workflow.stage_keys
    assert workflow.ontology_feature_refs == (
        "aware_ontology.OntologyConfig",
        "aware_ontology.OntologyPackage",
    )
    assert workflow.expected_proof_refs == (
        "workspace.semantic_materialization.receipt",
        ONTOLOGY_FUNCTION_IMPL_COVERAGE_PROOF_REF,
    )
    assert workflow.provider_payload is not None
    assert workflow.provider_payload["coverage_contract"] == (
        "native_function_impl_or_runtime_handler_delegation"
    )

    manifest_resolution = ONTOLOGY_MANIFEST_RESOLUTION[0]
    assert {
        "stable_ids_ownership",
        "stable_ids_parity_policy",
        "stable_ids_resolution_policy",
    }.issubset(set(manifest_resolution.copy_code_package_metadata_keys))

    materialization_policy = ONTOLOGY_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY[0]
    assert materialization_policy.semantic_owner == ONTOLOGY_PROVIDER_OWNER
    assert materialization_policy.callable_module == (
        "aware_ontology.materialization.workspace_provider"
    )
    assert materialization_policy.callable_name == "materialize"

    participation = ONTOLOGY_MATERIALIZATION_CAPABILITY_PARTICIPATION[0]
    assert (
        participation.metadata[SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY]
        == ONTOLOGY_MATERIALIZATION_DELTA_ADAPTER_METADATA
    )
    assert (
        ONTOLOGY_MATERIALIZATION_DELTA_ADAPTER_METADATA["callable_module"]
        == "aware_ontology.materialization.workspace_provider"
    )
    assert (
        ONTOLOGY_MATERIALIZATION_DELTA_ADAPTER_METADATA["callable_name"]
        == "materialize_delta"
    )
    assert (
        ONTOLOGY_MATERIALIZATION_DELTA_ADAPTER_METADATA[
            SEMANTIC_PROVIDER_DELTA_FUNCTIONAL_MATERIALIZATION_KEY
        ]
        is True
    )
    assert (
        ONTOLOGY_MATERIALIZATION_DELTA_ADAPTER_METADATA[
            SEMANTIC_PROVIDER_DELTA_OPERATION_EXECUTION_PROJECTION_NAME_KEY
        ]
        == "ObjectConfigGraphPackage"
    )
    source_meaning = ONTOLOGY_SEMANTIC_SOURCE_MEANING_CAPABILITY_PARTICIPATION[0]
    assert source_meaning.capability == "semantic_source_meaning"
    assert source_meaning.semantic_owner == ONTOLOGY_PROVIDER_OWNER
    assert source_meaning.metadata == (
        ONTOLOGY_SEMANTIC_SOURCE_MEANING_CAPABILITY_METADATA
    )
    source_meaning_contract = source_meaning.metadata["source_meaning_contract"]
    assert isinstance(source_meaning_contract, dict)
    assert source_meaning_contract["provider_key"] == "aware_meta"
    assert source_meaning_contract["semantic_owner"] == (
        "aware_meta.object_config_graph"
    )
    bindings = source_meaning_contract["bindings"]
    assert isinstance(bindings, list)
    binding = bindings[0]
    assert isinstance(binding, dict)
    binding_metadata = binding["metadata"]
    assert isinstance(binding_metadata, dict)
    action_bindings = binding_metadata["action_bindings"]
    assert isinstance(action_bindings, list)
    action_binding = action_bindings[0]
    assert isinstance(action_binding, dict)
    function_call_binding = action_binding["function_call_binding"]
    assert isinstance(function_call_binding, dict)
    assert function_call_binding["function_ref"] == (
        "aware_meta_ontology.attribute.attribute_config."
        "AttributeConfig.update_primitive"
    )
    operation_resolution = (
        ONTOLOGY_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION[0]
    )
    assert operation_resolution.capability == (
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY
    )
    assert operation_resolution.semantic_owner == ONTOLOGY_PROVIDER_OWNER
    assert operation_resolution.metadata == (
        ONTOLOGY_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA
    )
    assert operation_resolution.metadata["contract_version"] == (
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION
    )
    assert operation_resolution.metadata["callable_module"] == (
        "aware_meta.semantic_operation_resolution"
    )
    assert operation_resolution.metadata["callable_name"] == (
        "resolve_meta_semantic_operation_function_call_plan_previews"
    )
    assert operation_resolution.metadata["supported_semantic_operation_types"] == (
        META_OBJECT_CONFIG_GRAPH_SUPPORTED_FUNCTION_CALL_OPERATION_TYPES
    )
    assert operation_resolution.metadata["semantic_operation_type_refs"] == (
        META_OBJECT_CONFIG_GRAPH_SEMANTIC_OPERATION_TYPES
    )
    assert operation_resolution.metadata[
        META_SEMANTIC_PROJECTION_MUTATION_SCOPES_METADATA_KEY
    ] == (META_SEMANTIC_PROJECTION_MUTATION_SCOPE_PAYLOADS)
    projection_scopes = operation_resolution.metadata[
        META_SEMANTIC_PROJECTION_MUTATION_SCOPES_METADATA_KEY
    ]
    assert isinstance(projection_scopes, tuple)
    projection_scope = projection_scopes[0]
    assert isinstance(projection_scope, dict)
    assert projection_scope["projection_name"] == "ObjectConfigGraphPackage"
    assert "ObjectConfigGraph" in projection_scope["projection_refs"]
    assert "ObjectProjectionGraph" in projection_scope["projection_refs"]
    assert "ObjectInstanceGraph" in projection_scope["object_graph_refs"]
    assert projection_scope["package_selectors"] == {
        "manifest_kind": "aware_toml",
        "package_kind": "ontology",
        "semantic_kind": "object_config_graph_package",
    }
    assert (
        operation_resolution.metadata["supported_semantic_operation_types"]
        == META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA[
            "supported_semantic_operation_types"
        ]
    )
    assert (
        operation_resolution.metadata["semantic_operation_type_refs"]
        == META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA[
            "semantic_operation_type_refs"
        ]
    )
    supported_operation_types = set(
        operation_resolution.metadata["supported_semantic_operation_types"]
    )
    assert {
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_TYPE_UPDATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_LOAD_POLICY_UPDATE_OPERATION,
    }.issubset(supported_operation_types)
    semantic_operation_refs = set(
        operation_resolution.metadata["semantic_operation_type_refs"]
    )
    assert {
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_CREATE_OPERATION,
    }.issubset(semantic_operation_refs)
    assert operation_resolution.metadata["bridge_provider_key"] == "aware_meta"
    assert (
        operation_resolution.metadata["bridge_semantic_owner"]
        == "aware_meta.object_config_graph"
    )
    assert operation_resolution.metadata["mutates"] is False
    assert operation_resolution.metadata["execution_status"] == "not_requested"

    assert contract.materialization_artifact_outputs == (
        ONTOLOGY_MATERIALIZATION_ARTIFACT_OUTPUTS
    )
    assert tuple(
        output.output_key for output in ONTOLOGY_MATERIALIZATION_ARTIFACT_OUTPUTS
    ) == (
        META_LANGUAGE_MATERIALIZATION_GENERATED_FILES_OUTPUT_KEY,
        META_LANGUAGE_MATERIALIZATION_PACKAGE_OUTPUT_KEY,
        META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_OUTPUT_KEY,
        ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY,
    )
    meta_language_outputs = tuple(
        output
        for output in ONTOLOGY_MATERIALIZATION_ARTIFACT_OUTPUTS
        if output.producer_key == META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY
    )
    for output in meta_language_outputs:
        assert output.semantic_owner == ONTOLOGY_PROVIDER_OWNER
        assert output.producer_provider_key == "aware_meta"
        assert output.producer_key == META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY
        assert output.artifact_family == META_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY
        assert output.provider_payload is not None
        assert output.provider_payload["bridge_provider_key"] == "aware_meta"
    runtime_artifact_set_output = next(
        output
        for output in ONTOLOGY_MATERIALIZATION_ARTIFACT_OUTPUTS
        if output.output_key == ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY
    )
    assert runtime_artifact_set_output.semantic_owner == ONTOLOGY_PROVIDER_OWNER
    assert runtime_artifact_set_output.producer_provider_key == "aware_ontology"
    assert (
        runtime_artifact_set_output.producer_key
        == ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY
    )
    assert (
        runtime_artifact_set_output.artifact_family
        == ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY
    )
    assert (
        runtime_artifact_set_output.artifact_role
        == ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_ROLE
    )
    assert runtime_artifact_set_output.output_kind == "materialization_detail"
    assert (
        runtime_artifact_set_output.runtime_contract_version
        == ONTOLOGY_RUNTIME_ARTIFACT_SET_CONTRACT_VERSION
    )
    assert runtime_artifact_set_output.required_for == (
        ONTOLOGY_RUNTIME_ARTIFACT_SET_REQUIRED_FOR
    )
    assert runtime_artifact_set_output.provider_payload is not None
    assert runtime_artifact_set_output.provider_payload["receipt_field"] == (
        ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY
    )
    assert runtime_artifact_set_output.provider_payload["activation_policy"] == (
        ONTOLOGY_RUNTIME_ARTIFACT_SET_ACTIVATION_POLICY
    )
    assert runtime_artifact_set_output.provider_payload["activation_allowed"] is False


def test_ontology_semantic_contract_resolves_through_module_plugin_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_code.module_plugin_registry import AwareModulePluginRegistry
    from aware_code.semantic_materialization import (
        SEMANTIC_MATERIALIZATION_CAPABILITY,
    )
    from aware_ontology.semantic_contract import (
        ONTOLOGY_MATERIALIZATION_ARTIFACT_OUTPUTS,
        ONTOLOGY_MATERIALIZATION_RUNTIME,
        ONTOLOGY_MATERIALIZATION_RUNTIME_CONTEXT,
        ONTOLOGY_PROVIDER_OWNER,
    )
    from aware_ontology.semantic_runtime_catalog import (
        ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY,
        ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY,
    )

    AwareModulePluginRegistry.ensure_module_plugins_registered_from_repo_root(
        repo_root=_KERNEL_WORKSPACE_ROOT,
        replace_existing=True,
    )

    contract = AwareModulePluginRegistry.module_semantic_contract_for_provider_key(
        "aware_ontology"
    )
    assert contract is not None
    assert contract.provider_key == "aware_ontology"
    assert (
        AwareModulePluginRegistry.semantic_materialization_runtime_for_provider_key(
            provider_key="aware_ontology",
            semantic_owner=ONTOLOGY_PROVIDER_OWNER,
        )
        == ONTOLOGY_MATERIALIZATION_RUNTIME
    )
    assert (
        AwareModulePluginRegistry.semantic_materialization_runtime_context_for_provider_key(
            provider_key="aware_ontology",
            semantic_owner=ONTOLOGY_PROVIDER_OWNER,
        )
        == ONTOLOGY_MATERIALIZATION_RUNTIME_CONTEXT
    )
    resolved_artifact_outputs = AwareModulePluginRegistry.semantic_materialization_artifact_outputs_for_provider_key(
        provider_key="aware_ontology",
        semantic_owner=ONTOLOGY_PROVIDER_OWNER,
        producer_key=("aware_meta.object_config_graph.language_materialization"),
        artifact_family="ocg_language_materialization",
        required_for="workspace_revision",
    )
    assert {output.output_key for output in resolved_artifact_outputs} == {
        output.output_key
        for output in ONTOLOGY_MATERIALIZATION_ARTIFACT_OUTPUTS
        if output.producer_key
        == "aware_meta.object_config_graph.language_materialization"
        and output.artifact_family == "ocg_language_materialization"
        and "workspace_revision" in output.required_for
    }
    assert all(
        output.semantic_owner == ONTOLOGY_PROVIDER_OWNER
        for output in resolved_artifact_outputs
    )
    runtime_artifact_set_outputs = AwareModulePluginRegistry.semantic_materialization_artifact_outputs_for_provider_key(
        provider_key="aware_ontology",
        semantic_owner=ONTOLOGY_PROVIDER_OWNER,
        producer_key=ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY,
        artifact_family=ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY,
        required_for="workspace_revision",
    )
    assert tuple(output.output_key for output in runtime_artifact_set_outputs) == (
        ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY,
    )
    assert runtime_artifact_set_outputs[0].producer_provider_key == "aware_ontology"
    materializer = AwareModulePluginRegistry.resolve_semantic_capability_provider(
        provider_key="aware_ontology",
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
    )
    assert materializer is not None
    assert materializer.provider_key == "aware_ontology"
    assert materializer.semantic_owner == ONTOLOGY_PROVIDER_OWNER
    assert materializer.callable_module == (
        "aware_ontology.materialization.workspace_provider"
    )
    assert materializer.callable_name == "materialize"


def test_ontology_artifact_leaf_ownership_resolves_generated_python_package(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.semantic_artifact_ownership import (
        resolve_workspace_semantic_artifact_leaf_ownership,
    )

    workspace_root = tmp_path / "repo"
    module_root = workspace_root / "modules" / "hub"
    ontology_root = module_root / "structure" / "ontology"
    ontology_root.mkdir(parents=True)
    (module_root / "aware.ontology.toml").write_text(
        "\n".join(
            (
                "aware_ontology = 1",
                "",
                "[ontology]",
                'package_name = "hub-ontology"',
                'fqn_prefix = "aware_hub"',
                'source_manifest = "structure/ontology/aware.toml"',
                "",
            )
        ),
        encoding="utf-8",
    )
    (ontology_root / "aware.toml").write_text("aware = 1\n", encoding="utf-8")
    (ontology_root / "python" / "aware_hub_ontology").mkdir(parents=True)
    (ontology_root / "python" / "pyproject.toml").write_text(
        '[project]\nname = "aware-hub-ontology"\n',
        encoding="utf-8",
    )
    owner = WorkspaceSemanticArtifactBinding(
        module_id=None,
        package_name="hub-ontology",
        language="aware",
        surface="ontology",
        manifest_kind="aware_ontology_toml",
        manifest_relative_path="modules/hub/aware.ontology.toml",
        package_root="modules/hub",
        sources_root="modules/hub/structure/ontology/aware",
        package_kind="ontology",
        semantic_contract_provider_key="aware_ontology",
    )
    leaf = WorkspaceSemanticArtifactBinding(
        module_id=None,
        package_name="aware-hub-ontology",
        language="python",
        surface="runtime",
        manifest_kind="pyproject_toml",
        manifest_relative_path=("modules/hub/structure/ontology/python/pyproject.toml"),
        package_root="modules/hub/structure/ontology/python",
        sources_root="modules/hub/structure/ontology/python",
        package_kind="python_package",
    )

    claim = resolve_workspace_semantic_artifact_leaf_ownership(
        request=WorkspaceSemanticArtifactLeafOwnershipRequest(
            workspace_root=workspace_root,
            owner=owner,
            leaf=leaf,
        )
    )

    assert claim is not None
    assert claim.owned is True
    assert claim.owner_semantic_package_manifest == "modules/hub/aware.ontology.toml"
    assert claim.artifact_package_root == "modules/hub/structure/ontology/python"
    assert claim.production is not None
    assert claim.production.provider_key == "aware_ontology"


def test_ontology_artifact_leaf_ownership_rejects_runtime_package(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.semantic_artifact_ownership import (
        resolve_workspace_semantic_artifact_leaf_ownership,
    )

    workspace_root = tmp_path / "repo"
    module_root = workspace_root / "modules" / "hub"
    module_root.mkdir(parents=True)
    (module_root / "aware.ontology.toml").write_text(
        "\n".join(
            (
                "aware_ontology = 1",
                "",
                "[ontology]",
                'package_name = "hub-ontology"',
                'fqn_prefix = "aware_hub"',
                'source_manifest = "structure/ontology/aware.toml"',
                "",
            )
        ),
        encoding="utf-8",
    )
    owner = WorkspaceSemanticArtifactBinding(
        module_id=None,
        package_name="hub-ontology",
        language="aware",
        surface="ontology",
        manifest_kind="aware_ontology_toml",
        manifest_relative_path="modules/hub/aware.ontology.toml",
        package_root="modules/hub",
        sources_root="modules/hub/structure/ontology/aware",
        package_kind="ontology",
        semantic_contract_provider_key="aware_ontology",
    )
    leaf = WorkspaceSemanticArtifactBinding(
        module_id=None,
        package_name="aware-hub",
        language="python",
        surface="runtime",
        manifest_kind="pyproject_toml",
        manifest_relative_path="modules/hub/runtime/pyproject.toml",
        package_root="modules/hub/runtime",
        sources_root="modules/hub/runtime",
        package_kind="python_package",
    )

    claim = resolve_workspace_semantic_artifact_leaf_ownership(
        request=WorkspaceSemanticArtifactLeafOwnershipRequest(
            workspace_root=workspace_root,
            owner=owner,
            leaf=leaf,
        )
    )

    assert claim is None


def test_ontology_artifact_leaf_ownership_resolves_declared_runtime_package(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.semantic_artifact_ownership import (
        resolve_workspace_semantic_artifact_leaf_ownership,
    )

    workspace_root = tmp_path / "repo"
    module_root = workspace_root / "modules" / "hub"
    runtime_root = module_root / "runtime"
    runtime_root.mkdir(parents=True)
    (module_root / "aware.ontology.toml").write_text(
        "\n".join(
            (
                "aware_ontology = 1",
                "",
                "[ontology]",
                'package_name = "hub-ontology"',
                'fqn_prefix = "aware_hub"',
                'source_manifest = "structure/ontology/aware.toml"',
                "",
                "[runtime]",
                'manifest = "runtime/pyproject.toml"',
                'project_name = "aware-hub"',
                'import_root = "aware_hub"',
                "",
            )
        ),
        encoding="utf-8",
    )
    (runtime_root / "pyproject.toml").write_text(
        '[project]\nname = "aware-hub"\n',
        encoding="utf-8",
    )
    owner = WorkspaceSemanticArtifactBinding(
        module_id=None,
        package_name="hub-ontology",
        language="aware",
        surface="ontology",
        manifest_kind="aware_ontology_toml",
        manifest_relative_path="modules/hub/aware.ontology.toml",
        package_root="modules/hub",
        sources_root="modules/hub/structure/ontology/aware",
        package_kind="ontology",
        semantic_contract_provider_key="aware_ontology",
    )
    leaf = WorkspaceSemanticArtifactBinding(
        module_id=None,
        package_name="aware-hub",
        language="python",
        surface="runtime",
        manifest_kind="pyproject_toml",
        manifest_relative_path="modules/hub/runtime/pyproject.toml",
        package_root="modules/hub/runtime",
        sources_root="modules/hub/runtime",
        package_kind="python_package",
    )

    claim = resolve_workspace_semantic_artifact_leaf_ownership(
        request=WorkspaceSemanticArtifactLeafOwnershipRequest(
            workspace_root=workspace_root,
            owner=owner,
            leaf=leaf,
        )
    )

    assert claim is not None
    assert claim.owned is True
    assert claim.owner_semantic_package_manifest == "modules/hub/aware.ontology.toml"
    assert claim.artifact_package_root == "modules/hub/runtime"
    assert claim.ownership_role == "semantic_runtime_handler_package"
    assert claim.production is not None
    assert claim.production.provider_key == "aware_ontology"
    assert claim.production.producer_key == "aware_ontology.runtime_handler_package"
