from __future__ import annotations

from typing import Any

_LAZY_EXPORTS = {
    "ActorRolesV1ServiceProviderInput": (
        "aware_identity_service.view_state_providers",
        "ActorRolesV1ServiceProviderInput",
    ),
    "IdentityServiceViewFulfillmentEvidenceV1": (
        "aware_identity_service.view_state_providers",
        "IdentityServiceViewFulfillmentEvidenceV1",
    ),
    "LOCAL_IDENTITY_ACTOR_KEY": (
        "aware_identity_service.local_sdk",
        "LOCAL_IDENTITY_ACTOR_KEY",
    ),
    "LOCAL_IDENTITY_COUNTRY_CODE": (
        "aware_identity_service.local_sdk",
        "LOCAL_IDENTITY_COUNTRY_CODE",
    ),
    "LOCAL_IDENTITY_LANGUAGE_CODE": (
        "aware_identity_service.local_sdk",
        "LOCAL_IDENTITY_LANGUAGE_CODE",
    ),
    "LOCAL_IDENTITY_NAMESPACE": (
        "aware_identity_service.local_sdk",
        "LOCAL_IDENTITY_NAMESPACE",
    ),
    "LOCAL_IDENTITY_PROVIDER_KEY": (
        "aware_identity_service.local_sdk",
        "LOCAL_IDENTITY_PROVIDER_KEY",
    ),
    "LOCAL_IDENTITY_STATE_VERSION": (
        "aware_identity_service.local_sdk",
        "LOCAL_IDENTITY_STATE_VERSION",
    ),
    "LocalIdentityAdmissionResult": (
        "aware_identity_service.local_sdk",
        "LocalIdentityAdmissionResult",
    ),
    "LocalIdentityApiClient": (
        "aware_identity_service.local_sdk",
        "LocalIdentityApiClient",
    ),
    "LocalIdentityExecutionIdentity": (
        "aware_identity_service.local_sdk",
        "LocalIdentityExecutionIdentity",
    ),
    "actor_roles_view_state": (
        "aware_identity_service.view_state_providers",
        "actor_roles_view_state",
    ),
    "actor_roles_view_state_from_input": (
        "aware_identity_service.view_state_providers",
        "actor_roles_view_state_from_input",
    ),
    "actor_roles_view_state_from_result": (
        "aware_identity_service.view_state_providers",
        "actor_roles_view_state_from_result",
    ),
    "build_aware_identity_service_protocol_handler": (
        "aware_identity_service.api_service_protocol",
        "build_aware_identity_service_protocol_handler",
    ),
    "build_local_identity_api_client": (
        "aware_identity_service.local_sdk",
        "build_local_identity_api_client",
    ),
    "build_service_bindings": (
        "aware_identity_service.service_bindings",
        "build_service_bindings",
    ),
    "ensure_local_identity_admission": (
        "aware_identity_service.local_sdk",
        "ensure_local_identity_admission",
    ),
    "register_service_plugins": (
        "aware_identity_service.service_providers",
        "register_plugins",
    ),
    "resolve_local_identity_execution_identity": (
        "aware_identity_service.local_sdk",
        "resolve_local_identity_execution_identity",
    ),
    "stable_actor_id": (
        "aware_identity_service.local_sdk",
        "stable_actor_id",
    ),
    "stable_identity_id": (
        "aware_identity_service.local_sdk",
        "stable_identity_id",
    ),
    "stable_identity_profile_id": (
        "aware_identity_service.local_sdk",
        "stable_identity_profile_id",
    ),
    "start_identity_actor_commit_environment_fanout": (
        "aware_identity_service.service_startup",
        "start_identity_actor_commit_environment_fanout",
    ),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(
            f"module 'aware_identity_service' has no attribute {name!r}"
        )
    module_name, attr_name = target
    from importlib import import_module

    return getattr(import_module(module_name), attr_name)


__all__ = [
    "ActorRolesV1ServiceProviderInput",
    "IdentityServiceViewFulfillmentEvidenceV1",
    "LOCAL_IDENTITY_ACTOR_KEY",
    "LOCAL_IDENTITY_COUNTRY_CODE",
    "LOCAL_IDENTITY_LANGUAGE_CODE",
    "LOCAL_IDENTITY_NAMESPACE",
    "LOCAL_IDENTITY_PROVIDER_KEY",
    "LOCAL_IDENTITY_STATE_VERSION",
    "LocalIdentityAdmissionResult",
    "LocalIdentityApiClient",
    "LocalIdentityExecutionIdentity",
    "actor_roles_view_state",
    "actor_roles_view_state_from_input",
    "actor_roles_view_state_from_result",
    "build_aware_identity_service_protocol_handler",
    "build_local_identity_api_client",
    "build_service_bindings",
    "ensure_local_identity_admission",
    "register_service_plugins",
    "resolve_local_identity_execution_identity",
    "stable_actor_id",
    "stable_identity_id",
    "stable_identity_profile_id",
    "start_identity_actor_commit_environment_fanout",
]
