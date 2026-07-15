from __future__ import annotations

from typing import Any

from .api_service_protocol import build_aware_code_service_protocol_handler
from .local_api_client import (
    LocalCodeServiceApiConfig,
    LocalCodeServiceAwareApiClient,
    LocalCodeServiceSemanticOwnershipProvider,
    LocalCodeServiceSemanticScopeProvider,
    LocalCodeServiceSourceOwnershipProvider,
    build_local_code_service_api_client,
    dispatch_code_service_protocol_endpoint,
)
from .service_bindings import build_service_bindings
from .service_providers import register_plugins as register_service_plugins

_LAZY_EXPORTS = {
    "CODE_EDITOR_PROVIDER_REF": (
        "aware_code_service.view_state_providers",
        "CODE_EDITOR_PROVIDER_REF",
    ),
    "CODE_PACKAGE_SELECTOR_PROVIDER_REF": (
        "aware_code_service.view_state_providers",
        "CODE_PACKAGE_SELECTOR_PROVIDER_REF",
    ),
    "CodeEditorV1ServiceProviderInput": (
        "aware_code_service.view_state_providers",
        "CodeEditorV1ServiceProviderInput",
    ),
    "CodePackageSelectorV1ServiceProviderInput": (
        "aware_code_service.view_state_providers",
        "CodePackageSelectorV1ServiceProviderInput",
    ),
    "CodeServiceViewFulfillmentEvidenceV1": (
        "aware_code_service.view_state_providers",
        "CodeServiceViewFulfillmentEvidenceV1",
    ),
    "CodeReplicaCodeSnapshotV1": (
        "aware_code_service.ontology_replica_snapshot",
        "CodeReplicaCodeSnapshotV1",
    ),
    "CodeReplicaLatestSnapshotV1": (
        "aware_code_service.ontology_replica_snapshot",
        "CodeReplicaLatestSnapshotV1",
    ),
    "CodeReplicaPackageSnapshotV1": (
        "aware_code_service.ontology_replica_snapshot",
        "CodeReplicaPackageSnapshotV1",
    ),
    "CodeReplicaReadModels": (
        "aware_code_service.ontology_replica_snapshot",
        "CodeReplicaReadModels",
    ),
    "CodeReplicaSectionSnapshotV1": (
        "aware_code_service.ontology_replica_snapshot",
        "CodeReplicaSectionSnapshotV1",
    ),
    "code_editor_view_state": (
        "aware_code_service.view_state_providers",
        "code_editor_view_state",
    ),
    "code_editor_view_state_from_ontology_replica": (
        "aware_code_service.ontology_replica_snapshot",
        "code_editor_view_state_from_ontology_replica",
    ),
    "code_editor_view_state_from_input": (
        "aware_code_service.view_state_providers",
        "code_editor_view_state_from_input",
    ),
    "code_editor_view_state_from_response": (
        "aware_code_service.view_state_providers",
        "code_editor_view_state_from_response",
    ),
    "code_package_selector_view_state": (
        "aware_code_service.view_state_providers",
        "code_package_selector_view_state",
    ),
    "code_package_selector_view_state_from_ontology_replica": (
        "aware_code_service.ontology_replica_snapshot",
        "code_package_selector_view_state_from_ontology_replica",
    ),
    "code_package_selector_view_state_from_input": (
        "aware_code_service.view_state_providers",
        "code_package_selector_view_state_from_input",
    ),
    "code_package_selector_view_state_from_response": (
        "aware_code_service.view_state_providers",
        "code_package_selector_view_state_from_response",
    ),
    "read_code_latest_snapshot_from_ontology_replica": (
        "aware_code_service.ontology_replica_snapshot",
        "read_code_latest_snapshot_from_ontology_replica",
    ),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module 'aware_code_service' has no attribute {name!r}")
    module_name, attr_name = target
    from importlib import import_module

    return getattr(import_module(module_name), attr_name)


__all__ = [
    "LocalCodeServiceApiConfig",
    "LocalCodeServiceAwareApiClient",
    "LocalCodeServiceSemanticOwnershipProvider",
    "LocalCodeServiceSemanticScopeProvider",
    "LocalCodeServiceSourceOwnershipProvider",
    "CODE_EDITOR_PROVIDER_REF",
    "CODE_PACKAGE_SELECTOR_PROVIDER_REF",
    "CodeEditorV1ServiceProviderInput",
    "CodePackageSelectorV1ServiceProviderInput",
    "CodeReplicaCodeSnapshotV1",
    "CodeReplicaLatestSnapshotV1",
    "CodeReplicaPackageSnapshotV1",
    "CodeReplicaReadModels",
    "CodeReplicaSectionSnapshotV1",
    "CodeServiceViewFulfillmentEvidenceV1",
    "build_aware_code_service_protocol_handler",
    "build_local_code_service_api_client",
    "build_service_bindings",
    "code_editor_view_state",
    "code_editor_view_state_from_ontology_replica",
    "code_editor_view_state_from_input",
    "code_editor_view_state_from_response",
    "code_package_selector_view_state",
    "code_package_selector_view_state_from_ontology_replica",
    "code_package_selector_view_state_from_input",
    "code_package_selector_view_state_from_response",
    "dispatch_code_service_protocol_endpoint",
    "read_code_latest_snapshot_from_ontology_replica",
    "register_service_plugins",
]
