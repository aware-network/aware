from __future__ import annotations

from typing import cast
from uuid import UUID

from aware_code.types import JsonObject
from aware_identity_service_dto.identity.admission import (
    IdentitySignupViaProfileRequest,
)
from aware_reactivity_service_api import AwareReactivityServiceApiClient
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyActionConfigSpec,
    ReactivityPolicyBundleEnsureRequest,
    ReactivityPolicyBundleSpec,
    ReactivityPolicyConditionConfigSpec,
    ReactivityPolicyEventActionBindingSpec,
    ReactivityPolicyEventConditionBindingSpec,
    ReactivityPolicyEventConfigSpec,
)
from aware_service_runtime.api_ingress.host_context import ServiceApiHostContext
from aware_service_runtime.local_service_host_api_client import (
    build_service_api_client_for_api_package,
)

REACTIVITY_SERVICE_API_PACKAGE_NAME = "reactivity-service-api"
IDENTITY_ADMISSION_OPERATION_LABEL = "Identity.signup_via_profile"
IDENTITY_ADMITTED_EVENT_NAME = "identity.admitted"
IDENTITY_ADMISSION_REACTIVITY_OWNER_REF = "identity"
IDENTITY_ADMISSION_REACTIVITY_POLICY_KEY = "identity.admission"
IDENTITY_ADMISSION_REACTIVITY_SEMANTIC_SOURCE_REF = "identity.admission"
IDENTITY_DISCOVERY_INDEX_PROFILE_ACTION = "identity.discovery.index_profile"
IDENTITY_ADMISSION_REACTIVITY_SUBSCRIBER_ID = "identity.service"


async def ensure_identity_admission_reactivity_policy(
    *,
    host_context: ServiceApiHostContext,
    request: IdentitySignupViaProfileRequest,
    actor_id: UUID | None,
) -> None:
    if not _has_service_api_dependency_route(
        host_context=host_context,
        api_package_name=REACTIVITY_SERVICE_API_PACKAGE_NAME,
    ):
        return

    invoker = build_service_api_client_for_api_package(
        host_context.service_api_dependency_routes,
        api_package_name=REACTIVITY_SERVICE_API_PACKAGE_NAME,
        actor_id=actor_id,
        invocation_context=_host_invocation_context_payload(host_context),
    )
    if invoker is None:
        return

    client = AwareReactivityServiceApiClient(invoker)
    response = await client.reactivity.policy.ensure_bundle(
        build_identity_admission_reactivity_policy_request(request=request)
    )
    if not response.accepted:
        raise RuntimeError(
            "Identity admission Reactivity policy registration was rejected: "
            f"{response.error or response.info or response.status}"
        )


def build_identity_admission_reactivity_policy_request(
    *,
    request: IdentitySignupViaProfileRequest,
) -> ReactivityPolicyBundleEnsureRequest:
    return ReactivityPolicyBundleEnsureRequest(
        request_id=request.request_id,
        subscriber_id=IDENTITY_ADMISSION_REACTIVITY_SUBSCRIBER_ID,
        bundle=ReactivityPolicyBundleSpec(
            owner_ref=IDENTITY_ADMISSION_REACTIVITY_OWNER_REF,
            policy_key=IDENTITY_ADMISSION_REACTIVITY_POLICY_KEY,
            version=1,
            semantic_source_ref=IDENTITY_ADMISSION_REACTIVITY_SEMANTIC_SOURCE_REF,
            condition_configs=[
                ReactivityPolicyConditionConfigSpec(
                    name=IDENTITY_ADMISSION_OPERATION_LABEL,
                    description="Identity admission signup operation completed.",
                )
            ],
            event_configs=[
                ReactivityPolicyEventConfigSpec(
                    name=IDENTITY_ADMITTED_EVENT_NAME,
                    description="Identity admission completed.",
                    event_type="condition",
                )
            ],
            action_configs=[
                ReactivityPolicyActionConfigSpec(
                    name=IDENTITY_DISCOVERY_INDEX_PROFILE_ACTION,
                    description="Index the admitted identity for discovery consumers.",
                    action_type=IDENTITY_DISCOVERY_INDEX_PROFILE_ACTION,
                )
            ],
            event_condition_bindings=[
                ReactivityPolicyEventConditionBindingSpec(
                    event_config_name=IDENTITY_ADMITTED_EVENT_NAME,
                    condition_config_name=IDENTITY_ADMISSION_OPERATION_LABEL,
                )
            ],
            event_action_bindings=[
                ReactivityPolicyEventActionBindingSpec(
                    event_config_name=IDENTITY_ADMITTED_EVENT_NAME,
                    action_config_name=IDENTITY_DISCOVERY_INDEX_PROFILE_ACTION,
                )
            ],
        ),
    )


def _has_service_api_dependency_route(
    *,
    host_context: ServiceApiHostContext,
    api_package_name: str,
) -> bool:
    return any(
        route.api_package_name == api_package_name
        for route in host_context.service_api_dependency_routes
    )


def _host_invocation_context_payload(
    host_context: ServiceApiHostContext,
) -> JsonObject | None:
    if host_context.invocation_context is None:
        return None
    return cast(JsonObject, dict(host_context.invocation_context))


__all__ = [
    "IDENTITY_ADMISSION_OPERATION_LABEL",
    "IDENTITY_ADMISSION_REACTIVITY_OWNER_REF",
    "IDENTITY_ADMISSION_REACTIVITY_POLICY_KEY",
    "IDENTITY_ADMISSION_REACTIVITY_SEMANTIC_SOURCE_REF",
    "IDENTITY_ADMISSION_REACTIVITY_SUBSCRIBER_ID",
    "IDENTITY_ADMITTED_EVENT_NAME",
    "IDENTITY_DISCOVERY_INDEX_PROFILE_ACTION",
    "REACTIVITY_SERVICE_API_PACKAGE_NAME",
    "build_identity_admission_reactivity_policy_request",
    "ensure_identity_admission_reactivity_policy",
]
