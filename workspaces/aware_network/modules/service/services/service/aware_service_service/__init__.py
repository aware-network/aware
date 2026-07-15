"""Standalone Service host bootstrap package."""

from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORT_MODULES = {
    "AwareServiceServiceProtocolHandler": "aware_service_service.api_service_protocol",
    "LOCAL_ENVIRONMENT_API_ENDPOINT": "aware_service_service.environment_api_client",
    "ServiceHostApp": "aware_service_service.app",
    "ServiceHostArtifactConfig": "aware_service_service.config",
    "ServiceHostAppConfig": "aware_service_service.config",
    "ServiceHostBootstrapConfig": "aware_service_service.config",
    "ServiceHostEconomyConfig": "aware_service_service.config",
    "ServiceHostEnvironmentConfig": "aware_service_service.config",
    "ServiceHostIpcConfig": "aware_service_service.config",
    "ServiceHostIpcServer": "aware_service_service.ipc",
    "ServiceHostImplementationPackageConfig": "aware_service_service.config",
    "ServiceHostOntologyReplicaConfig": "aware_service_service.config",
    "ServiceHostReferencePackageConfig": "aware_service_service.config",
    "ServiceHostLocalAuthorityResult": "aware_service_service.local_authority",
    "ServiceContractAccessContextBootstrapError": (
        "aware_service_service.economy.contract_access_client"
    ),
    "ServiceContractAccessContextBootstrapResult": (
        "aware_service_service.economy.contract_access_client"
    ),
    "ServiceContractAccessContextEnsureResult": (
        "aware_service_service.economy.contract_access_client"
    ),
    "ServiceOntologyReplicaApplyOutcome": (
        "aware_service_service.ontology.replica.state"
    ),
    "ServiceOntologyReplicaStateStore": "aware_service_service.ontology.replica.state",
    "ServiceOntologyReplicaSubscriptionSpec": (
        "aware_service_service.ontology.replica.state"
    ),
    "ServiceOntologyReplicaWorker": "aware_service_service.ontology.replica.worker",
    "EnvironmentApiServiceOntologyCommitSource": (
        "aware_service_service.ontology.replica.projector"
    ),
    "LocalFsServiceOntologyCommitSource": (
        "aware_service_service.ontology.replica.projector"
    ),
    "MetaLaneStoreServiceOntologyCommitSource": (
        "aware_service_service.ontology.replica.projector"
    ),
    "ServiceOntologyCommitSource": "aware_service_service.ontology.replica.projector",
    "ProjectedClassInstance": "aware_service_service.ontology.replica.query",
    "ProjectedRelationship": "aware_service_service.ontology.replica.query",
    "ServiceOntologyProjectionApplyStats": (
        "aware_service_service.ontology.replica.projector"
    ),
    "ServiceOntologyProjectionStore": (
        "aware_service_service.ontology.replica.projector"
    ),
    "ServiceOntologyReplicaQuery": "aware_service_service.ontology.replica.query",
    "build_environment_api_client_for_service_host_config": (
        "aware_service_service.environment_api_client"
    ),
    "build_aware_service_service_protocol_handler": (
        "aware_service_service.api_service_protocol"
    ),
    "build_service_bindings": "aware_service_service.service_bindings",
    "bootstrap_service_contract_access_context": (
        "aware_service_service.economy.contract_access_client"
    ),
    "bootstrap_service_contract_access_invocation_context": (
        "aware_service_service.economy.contract_access_client"
    ),
    "ensure_service_contract_access_context": (
        "aware_service_service.economy.contract_access_client"
    ),
    "ensure_service_contract_access_invocation_context": (
        "aware_service_service.economy.contract_access_client"
    ),
    "build_service_host_app": "aware_service_service.environment_api_client",
    "build_service_host_app_from_bootstrap_config": (
        "aware_service_service.environment_api_client"
    ),
    "ensure_service_host_from_workspace_revision_plan": (
        "aware_service_service.local_authority"
    ),
    "service_host_status_payload": "aware_service_service.local_authority",
    "service_host_status_payload_from_state_path": (
        "aware_service_service.local_authority"
    ),
    "stop_service_host": "aware_service_service.local_authority",
}

__all__ = tuple(_EXPORT_MODULES)


def __getattr__(name: str) -> Any:
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted((*globals(), *__all__))
