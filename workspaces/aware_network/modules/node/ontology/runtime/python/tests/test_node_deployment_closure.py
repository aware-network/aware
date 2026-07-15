from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_node.deployment_closure import (
    NODE_RUNTIME_CLOSURE_SCHEMA,
    build_node_runtime_closure_payload,
)
from aware_service_ontology.stable_ids import stable_service_config_id


def test_node_runtime_closure_preserves_node_bundle_binding() -> None:
    node_config_id = uuid4()
    result = SimpleNamespace(
        node_toml_path=Path("modules/node/nodes/authority/aware.node.toml"),
        workspace_root=Path("."),
        node_package=SimpleNamespace(id=uuid4(), name="aware-network-node"),
        node_config=SimpleNamespace(id=node_config_id, name="authority"),
        package_head_commit_id=uuid4(),
        package_object_instance_graph_commit_id=uuid4(),
        node_config_object_instance_graph_commit_id=uuid4(),
        source_code_package_id=uuid4(),
        node_config_environment_targets=(),
        node_config_ontology_targets=(),
        node_config_service_targets=(),
        node_config_interface_targets=(),
    )

    closure = build_node_runtime_closure_payload(
        result=result,
        workspace_semantic_package_selection_intents=(
            {
                "package_kind": "node",
                "package_key": "aware-network-node",
                "package_name": "aware-network-node",
                "semantic_package_id": str(uuid4()),
                "semantic_root_kind": "node_config",
                "semantic_root_id": str(node_config_id),
                "manifest_path": "modules/node/nodes/authority/aware.node.toml",
                "code_semantic_package_binding_id": "node-binding-id",
                "semantic_binding_module_package_id": "ontology_authority_node",
                "semantic_binding_module_relative_package_root": (
                    "modules/node/nodes/authority"
                ),
                "semantic_binding_status": "bound",
            },
        ),
    )

    selection = closure["node_selection"]["package_selection"]
    assert selection["code_semantic_package_binding_id"] == "node-binding-id"
    assert selection["semantic_binding_module_package_id"] == "ontology_authority_node"
    assert selection["semantic_binding_module_relative_package_root"] == (
        "modules/node/nodes/authority"
    )


def test_node_runtime_closure_resolves_service_target_by_stable_root_id() -> None:
    service_config_id = stable_service_config_id(name="aware_ontology")
    result = SimpleNamespace(
        node_toml_path=Path("modules/node/nodes/authority/aware.node.toml"),
        workspace_root=Path("."),
        node_package=SimpleNamespace(id=uuid4(), name="aware-network-node"),
        node_config=SimpleNamespace(id=uuid4(), name="authority"),
        package_head_commit_id=uuid4(),
        package_object_instance_graph_commit_id=uuid4(),
        node_config_object_instance_graph_commit_id=uuid4(),
        source_code_package_id=uuid4(),
        node_config_environment_targets=(),
        node_config_ontology_targets=(),
        node_config_service_targets=(
            SimpleNamespace(
                service_name="aware_ontology",
                code_packages=(
                    SimpleNamespace(
                        slot_key="runtime",
                        package_name="aware-ontology-service",
                        language="aware",
                    ),
                ),
            ),
        ),
        node_config_interface_targets=(),
    )

    closure = build_node_runtime_closure_payload(
        result=result,
        workspace_semantic_package_selection_intents=(
            {
                "package_kind": "service",
                "package_key": "aware-ontology-service",
                "semantic_package_family": "service",
                "semantic_package_id": str(uuid4()),
                "semantic_root_kind": "service_config",
                "semantic_root_id": str(service_config_id),
                "manifest_path": (
                    "workspaces/aware_network/modules/ontology/services/"
                    "ontology/aware.service.toml"
                ),
            },
        ),
    )

    assert closure["schema"] == NODE_RUNTIME_CLOSURE_SCHEMA
    assert closure["required_python_packages"] == (
        "aware-node-service",
        "aware-service-service",
    )
    runtime_inputs = closure["runtime_inputs"]
    assert runtime_inputs == [
        {
            "runtime_kind": "service",
            "target_name": "aware_ontology",
            "package_selection": {
                "family_key": "service",
                "package_kind": "service",
                "package_name": "aware-ontology-service",
                "manifest_path": (
                    "workspaces/aware_network/modules/ontology/services/"
                    "ontology/aware.service.toml"
                ),
                "semantic_package_id": runtime_inputs[0]["package_selection"][
                    "semantic_package_id"
                ],
                "semantic_root_kind": "service_config",
                "semantic_root_id": str(service_config_id),
            },
            "manifest_path": (
                "workspaces/aware_network/modules/ontology/services/"
                "ontology/aware.service.toml"
            ),
            "code_packages": [
                {
                    "slot_key": "runtime",
                    "package_name": "aware-ontology-service",
                    "language": "aware",
                }
            ],
        }
    ]


def test_node_runtime_closure_prefers_materialized_service_over_registry_placeholder() -> (
    None
):
    service_config_id = stable_service_config_id(name="aware_ontology")
    service_package_id = uuid4()
    result = SimpleNamespace(
        node_toml_path=Path("modules/node/nodes/authority/aware.node.toml"),
        workspace_root=Path("."),
        node_package=SimpleNamespace(id=uuid4(), name="aware-network-node"),
        node_config=SimpleNamespace(id=uuid4(), name="authority"),
        package_head_commit_id=uuid4(),
        package_object_instance_graph_commit_id=uuid4(),
        node_config_object_instance_graph_commit_id=uuid4(),
        source_code_package_id=uuid4(),
        node_config_environment_targets=(),
        node_config_ontology_targets=(),
        node_config_service_targets=(
            SimpleNamespace(service_name="aware_ontology", code_packages=()),
        ),
        node_config_interface_targets=(),
    )

    materialized_entry = {
        "source": "workspace_materialization",
        "package_kind": "service",
        "package_key": "aware-ontology-service",
        "semantic_package_family": "service",
        "semantic_package_id": str(service_package_id),
        "semantic_root_kind": "service_config",
        "semantic_root_id": str(service_config_id),
        "manifest_path": "modules/ontology/services/ontology/aware.service.toml",
    }
    registry_placeholder = {
        "source": "workspace_local_semantic_package_registry",
        "package_kind": "service",
        "package_key": "aware-ontology-service",
        "package_name": "aware-ontology-service",
        "semantic_package_family": "service",
        "semantic_package_id": str(service_package_id),
        "semantic_root_kind": "service_config",
        "semantic_root_id": str(service_config_id),
        "manifest_path": "modules/ontology/services/ontology/aware.service.toml",
    }

    closure = build_node_runtime_closure_payload(
        result=result,
        workspace_semantic_package_selection_intents=(
            materialized_entry,
            registry_placeholder,
        ),
    )

    service_input = closure["runtime_inputs"][0]
    assert service_input["runtime_kind"] == "service"
    assert service_input["package_selection"]["source"] == "workspace_materialization"
    assert service_input["package_selection"]["semantic_package_id"] == str(
        service_package_id
    )


def test_node_runtime_closure_ignores_service_activation_evidence() -> None:
    service_config_id = stable_service_config_id(name="aware_ontology")
    service_package_id = uuid4()
    result = SimpleNamespace(
        node_toml_path=Path("modules/node/nodes/authority/aware.node.toml"),
        workspace_root=Path("."),
        node_package=SimpleNamespace(id=uuid4(), name="aware-network-node"),
        node_config=SimpleNamespace(id=uuid4(), name="authority"),
        package_head_commit_id=uuid4(),
        package_object_instance_graph_commit_id=uuid4(),
        node_config_object_instance_graph_commit_id=uuid4(),
        source_code_package_id=uuid4(),
        node_config_environment_targets=(),
        node_config_ontology_targets=(),
        node_config_service_targets=(
            SimpleNamespace(service_name="aware_ontology", code_packages=()),
        ),
        node_config_interface_targets=(),
    )
    main_service = {
        "source": "workspace_materialization",
        "package_kind": "service",
        "package_key": "aware-ontology-service",
        "semantic_package_family": "service",
        "semantic_package_id": str(service_package_id),
        "semantic_root_kind": "service_config",
        "semantic_root_id": str(service_config_id),
        "manifest_path": "modules/ontology/services/ontology/aware.service.toml",
    }
    activation_config = {
        **main_service,
        "package_key": (
            "aware-ontology-service:activation:service-config:aware_ontology"
        ),
        "semantic_package_id": str(service_config_id),
        "semantic_root_kind": "service_activation_config",
    }

    closure = build_node_runtime_closure_payload(
        result=result,
        workspace_semantic_package_selection_intents=(
            main_service,
            activation_config,
        ),
    )

    selection = closure["runtime_inputs"][0]["package_selection"]
    assert selection["semantic_package_id"] == str(service_package_id)
    assert selection["semantic_root_kind"] == "service_config"


def test_node_runtime_closure_fails_for_distinct_materialized_service_matches() -> None:
    service_config_id = stable_service_config_id(name="aware_ontology")
    result = SimpleNamespace(
        node_toml_path=Path("modules/node/nodes/authority/aware.node.toml"),
        workspace_root=Path("."),
        node_package=SimpleNamespace(id=uuid4(), name="aware-network-node"),
        node_config=SimpleNamespace(id=uuid4(), name="authority"),
        node_config_environment_targets=(),
        node_config_ontology_targets=(),
        node_config_service_targets=(
            SimpleNamespace(service_name="aware_ontology", code_packages=()),
        ),
        node_config_interface_targets=(),
    )

    with pytest.raises(RuntimeError, match="matches=2"):
        build_node_runtime_closure_payload(
            result=result,
            workspace_semantic_package_selection_intents=(
                {
                    "source": "workspace_materialization",
                    "package_kind": "service",
                    "package_key": "aware-ontology-service",
                    "semantic_package_id": str(uuid4()),
                    "semantic_root_kind": "service_config",
                    "semantic_root_id": str(service_config_id),
                    "manifest_path": (
                        "modules/ontology/services/ontology/aware.service.toml"
                    ),
                },
                {
                    "source": "workspace_materialization",
                    "package_kind": "service",
                    "package_key": "aware-ontology-service",
                    "semantic_package_id": str(uuid4()),
                    "semantic_root_kind": "service_config",
                    "semantic_root_id": str(service_config_id),
                    "manifest_path": (
                        "modules/other_ontology/services/ontology/aware.service.toml"
                    ),
                },
            ),
        )


def test_node_runtime_closure_fails_without_materialized_service_bundle() -> None:
    result = SimpleNamespace(
        node_toml_path=Path("aware.node.toml"),
        workspace_root=Path("."),
        node_package=SimpleNamespace(id=uuid4(), name="aware-network-node"),
        node_config=SimpleNamespace(id=uuid4(), name="authority"),
        node_config_environment_targets=(),
        node_config_ontology_targets=(),
        node_config_service_targets=(
            SimpleNamespace(service_name="aware_ontology", code_packages=()),
        ),
        node_config_interface_targets=(),
    )

    with pytest.raises(RuntimeError, match="could not resolve declared target"):
        build_node_runtime_closure_payload(
            result=result,
            workspace_semantic_package_selection_intents=(),
        )


def test_node_runtime_closure_resolves_dependency_ontology_target() -> None:
    ontology_package_id = uuid4()
    result = SimpleNamespace(
        node_toml_path=Path("modules/node/nodes/authority/aware.node.toml"),
        workspace_root=Path("."),
        node_package=SimpleNamespace(id=uuid4(), name="aware-network-node"),
        node_config=SimpleNamespace(id=uuid4(), name="authority"),
        node_config_environment_targets=(),
        node_config_ontology_targets=(
            SimpleNamespace(package_name="storage-ontology"),
        ),
        node_config_service_targets=(),
        node_config_interface_targets=(),
    )

    closure = build_node_runtime_closure_payload(
        result=result,
        workspace_semantic_package_selection_intents=(
            {
                "source": "workspace_materialization",
                "package_kind": "ontology",
                "package_key": "storage-ontology",
                "package_name": "storage-ontology",
                "semantic_package_id": str(uuid4()),
                "semantic_root_kind": "OntologyConfig",
                "semantic_root_id": str(uuid4()),
                "manifest_path": "modules/storage/ontology/aware.ontology.toml",
            },
            {
                "source": "workspace_dependency_semantic_package_lock",
                "dependency_id": "aware_kernel",
                "workspace_dependency_revision_id": "workspace-revision:kernel",
                "export_ref": (
                    "workspace://aware_kernel#semantic-contracts/aware_ontology/"
                    "semantic-packages/storage-ontology@workspace-revision:kernel"
                ),
                "package_kind": "ontology",
                "package_key": "storage-ontology",
                "package_name": "storage-ontology",
                "manifest_path": "modules/storage/ontology/aware.ontology.toml",
                "semantic_package_id": str(ontology_package_id),
                "semantic_package_family": "ontology",
                "semantic_package_kind": "ontology_package",
                "semantic_root_kind": "OntologyPackage",
                "semantic_root_id": str(ontology_package_id),
                "source_code_package_id": "storage-code-package-id",
                "code_semantic_provider_registration_id": (
                    "aware-ontology-provider-registration-id"
                ),
                "code_semantic_package_binding_id": (
                    "storage-code-semantic-binding-id"
                ),
                "semantic_binding_module_package_id": "ontology",
                "semantic_binding_module_package_kind": "ontology",
                "semantic_binding_module_relative_package_root": (
                    "modules/storage/ontology"
                ),
                "semantic_binding_manifest_relative_path": (
                    "modules/storage/ontology/aware.ontology.toml"
                ),
                "semantic_binding_contract_module": (
                    "aware_ontology.semantic_contract"
                ),
                "semantic_binding_contract_name": "aware.semantic_provider",
                "semantic_binding_contract_role": "aware_ontology.provider",
                "semantic_binding_owned_manifest_kinds": ("aware_ontology_toml",),
                "semantic_binding_status": "bound",
            },
        ),
    )

    runtime_inputs = closure["runtime_inputs"]
    selection = runtime_inputs[0]["package_selection"]
    assert runtime_inputs[0]["runtime_kind"] == "ontology"
    assert selection["package_name"] == "storage-ontology"
    assert selection["source"] == "workspace_dependency_semantic_package_lock"
    assert selection["semantic_root_kind"] == "OntologyPackage"
    assert selection["semantic_root_id"] == str(ontology_package_id)
    assert selection["dependency_id"] == "aware_kernel"
    assert selection["workspace_dependency_revision_id"] == (
        "workspace-revision:kernel"
    )
    assert selection["code_semantic_package_binding_id"] == (
        "storage-code-semantic-binding-id"
    )
    assert selection["semantic_binding_module_package_id"] == "ontology"
    assert selection["semantic_binding_module_relative_package_root"] == (
        "modules/storage/ontology"
    )
