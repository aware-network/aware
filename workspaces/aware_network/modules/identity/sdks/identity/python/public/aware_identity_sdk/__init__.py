from __future__ import annotations

__all__ = [
    "ActorCommitsV1ProviderInput",
    "ActorReadClient",
    "ActorRolesV1ProviderInput",
    "ActorSubscriptionsV1ProviderInput",
    "DEFAULT_IDENTITY_SDK_SOURCE",
    "IdentityAdmission",
    "IdentityAdmissionV1ProviderInput",
    "IdentityAdmissionProfile",
    "IdentityApiClient",
    "IdentityGateSnapshot",
    "IdentityGateStatus",
    "IdentitySdkClient",
    "IdentitySdkError",
    "RawOntologyDeltaV1",
    "ViewProviderProvenanceV1",
    "actor_commits_v1_provider_input_from_client",
    "actor_commits_view_state",
    "actor_commits_view_state_from_input",
    "actor_commits_view_state_from_result",
    "actor_roles_v1_provider_input_from_client",
    "actor_roles_view_state",
    "actor_roles_view_state_from_input",
    "actor_roles_view_state_from_result",
    "actor_subscriptions_v1_provider_input_from_client",
    "actor_subscriptions_view_state",
    "actor_subscriptions_view_state_from_input",
    "actor_subscriptions_view_state_from_result",
    "build_identity_gate_snapshot",
    "identity_admission_v1_provider_input",
    "identity_admission_view_state",
    "identity_admission_view_state_from_input",
]

_EXPORTS = {
    "DEFAULT_IDENTITY_SDK_SOURCE": "aware_identity_sdk.client",
    "IdentityAdmission": "aware_identity_sdk.client",
    "IdentityAdmissionProfile": "aware_identity_sdk.client",
    "IdentityApiClient": "aware_identity_sdk.client",
    "IdentityGateSnapshot": "aware_identity_sdk.client",
    "IdentityGateStatus": "aware_identity_sdk.client",
    "IdentitySdkClient": "aware_identity_sdk.client",
    "IdentitySdkError": "aware_identity_sdk.client",
    "build_identity_gate_snapshot": "aware_identity_sdk.client",
    "ActorCommitsV1ProviderInput": "aware_identity_sdk.view_state_providers",
    "ActorReadClient": "aware_identity_sdk.view_state_providers",
    "ActorRolesV1ProviderInput": "aware_identity_sdk.view_state_providers",
    "ActorSubscriptionsV1ProviderInput": "aware_identity_sdk.view_state_providers",
    "IdentityAdmissionV1ProviderInput": "aware_identity_sdk.view_state_providers",
    "RawOntologyDeltaV1": "aware_identity_sdk.view_state_providers",
    "ViewProviderProvenanceV1": "aware_identity_sdk.view_state_providers",
    "actor_commits_v1_provider_input_from_client": (
        "aware_identity_sdk.view_state_providers"
    ),
    "actor_commits_view_state": "aware_identity_sdk.view_state_providers",
    "actor_commits_view_state_from_input": ("aware_identity_sdk.view_state_providers"),
    "actor_commits_view_state_from_result": ("aware_identity_sdk.view_state_providers"),
    "actor_roles_v1_provider_input_from_client": (
        "aware_identity_sdk.view_state_providers"
    ),
    "actor_roles_view_state": "aware_identity_sdk.view_state_providers",
    "actor_roles_view_state_from_input": "aware_identity_sdk.view_state_providers",
    "actor_roles_view_state_from_result": "aware_identity_sdk.view_state_providers",
    "actor_subscriptions_v1_provider_input_from_client": (
        "aware_identity_sdk.view_state_providers"
    ),
    "actor_subscriptions_view_state": "aware_identity_sdk.view_state_providers",
    "actor_subscriptions_view_state_from_input": (
        "aware_identity_sdk.view_state_providers"
    ),
    "actor_subscriptions_view_state_from_result": (
        "aware_identity_sdk.view_state_providers"
    ),
    "identity_admission_v1_provider_input": ("aware_identity_sdk.view_state_providers"),
    "identity_admission_view_state": "aware_identity_sdk.view_state_providers",
    "identity_admission_view_state_from_input": (
        "aware_identity_sdk.view_state_providers"
    ),
}


def __getattr__(name: str) -> object:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module 'aware_identity_sdk' has no attribute {name!r}")
    from importlib import import_module

    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value
