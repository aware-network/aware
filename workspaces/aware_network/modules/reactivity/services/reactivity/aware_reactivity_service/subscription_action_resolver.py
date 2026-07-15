from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, cast
from uuid import UUID

from aware_code.types import JsonObject
from aware_identity_service_api import AwareIdentityServiceApiClient
from aware_identity_service_dto.actor.subscription import ActorSubscriptionBridgeConfig
from aware_identity_service_dto.actor.subscription import (
    ActorSubscriptionResolveRequest,
)
from aware_identity_service_dto.actor.subscription import ActorSubscriptionResolveResult
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntent,
)
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntentResolveRequest,
)
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntentResolveResponse,
)
from aware_service_runtime.api_ingress.host_context import (
    ServiceApiHostContext,
    current_service_api_host_context,
)
from aware_service_runtime.local_service_host_api_client import (
    build_service_api_client_for_api_package,
)
from aware_reactivity.stable_ids import (
    stable_action_config_id,
    stable_action_intent_id,
)

from .policy_registry import (
    DISABLED_CONDITION_RESOLUTION_MODE,
    ReactivityPolicyRegistry,
    ReactivityResolvedPolicyActionBinding,
)

_IDENTITY_SERVICE_API_PACKAGE_NAME = "identity-service-api"


class _ResolveActorSubscriptionsCapability(Protocol):
    async def resolve_actor_subscriptions(
        self,
        request: ActorSubscriptionResolveRequest,
    ) -> ActorSubscriptionResolveResult: ...


class _IdentityApiClient(Protocol):
    @property
    def resolve_actor_subscriptions(self) -> _ResolveActorSubscriptionsCapability: ...


class IdentityServiceApiClientLike(Protocol):
    @property
    def identity(self) -> _IdentityApiClient: ...


@dataclass(frozen=True, slots=True)
class _ResolvedActionSelection:
    event_config_action_config_id: UUID | None
    action_config_id: UUID | None
    action_type: str | None


async def resolve_action_intents(
    *,
    request: ReactivityActionIntentResolveRequest,
    policy_registry: ReactivityPolicyRegistry,
    identity_api_client: IdentityServiceApiClientLike | None = None,
    environment_id: UUID | None = None,
) -> ReactivityActionIntentResolveResponse:
    if request.event_config_condition_config_id is None:
        return ReactivityActionIntentResolveResponse(
            request_id=request.request_id,
            accepted=False,
            error="event_config_condition_config_id is required",
        )

    client = identity_api_client or _build_identity_service_api_client()
    if client is None:
        return ReactivityActionIntentResolveResponse(
            request_id=request.request_id,
            accepted=False,
            error="identity-service-api dependency route unavailable",
        )

    identity_request = ActorSubscriptionResolveRequest(
        request_id=request.request_id,
        actor_id=None,
        event_config_condition_config_id=request.event_config_condition_config_id,
        object_instance_graph_identity_id=request.object_instance_graph_id,
        object_instance_graph_branch_id=request.object_instance_graph_branch_id,
        include_disabled=request.include_disabled_subscriptions,
        include_inactive=request.include_inactive_subscriptions,
    )
    identity_result = (
        await client.identity.resolve_actor_subscriptions.resolve_actor_subscriptions(
            identity_request
        )
    )
    action_bindings = (
        policy_registry.resolve_action_bindings_for_event_condition_config(
            request.event_config_condition_config_id,
            environment_id=environment_id,
        )
    )
    condition_resolution_mode = (
        policy_registry.resolve_event_condition_config_resolution_mode(
            request.event_config_condition_config_id,
            environment_id=environment_id,
        )
    )
    allow_subscription_action_fallback = (
        condition_resolution_mode != DISABLED_CONDITION_RESOLUTION_MODE
    )
    scoped_subscriptions = _filter_subscriptions_for_event_scope(
        request=request,
        subscriptions=identity_result.subscriptions,
    )
    intents = [
        _build_intent(
            request=request,
            subscription=subscription,
            selection=selection,
        )
        for subscription in scoped_subscriptions
        for selection in _select_actions_for_subscription(
            request=request,
            subscription=subscription,
            action_bindings=action_bindings,
            allow_subscription_action_fallback=allow_subscription_action_fallback,
        )
    ]
    intents.sort(
        key=lambda intent: (
            -intent.subscription_priority,
            str(getattr(intent, "intent_key", "")),
            str(intent.actor_subscription_id),
            str(intent.event_config_action_config_id or ""),
            intent.action_type or "",
        )
    )
    return ReactivityActionIntentResolveResponse(
        request_id=request.request_id,
        accepted=True,
        intents=intents,
        info=f"{len(intents)} action intent(s) resolved",
    )


def _build_identity_service_api_client() -> IdentityServiceApiClientLike | None:
    host_context = current_service_api_host_context()
    if host_context is None:
        return None
    invoker = build_service_api_client_for_api_package(
        host_context.service_api_dependency_routes,
        api_package_name=_IDENTITY_SERVICE_API_PACKAGE_NAME,
        actor_id=host_context.operation_context.actor_id,
        invocation_context=_host_invocation_context_payload(host_context),
    )
    if invoker is None:
        return None
    return cast(IdentityServiceApiClientLike, AwareIdentityServiceApiClient(invoker))


def identity_service_api_route_ready() -> bool:
    """Report whether the current ServiceHost request can route to Identity API."""

    return _build_identity_service_api_client() is not None


def _host_invocation_context_payload(
    host_context: ServiceApiHostContext,
) -> JsonObject | None:
    if host_context.invocation_context is None:
        return None
    return cast(JsonObject, dict(host_context.invocation_context))


def _filter_subscriptions_for_event_scope(
    *,
    request: ReactivityActionIntentResolveRequest,
    subscriptions: Sequence[ActorSubscriptionBridgeConfig],
) -> tuple[ActorSubscriptionBridgeConfig, ...]:
    branch_scope_id = request.object_instance_graph_branch_id or request.branch_id
    filtered: list[ActorSubscriptionBridgeConfig] = []
    for subscription in subscriptions:
        if (
            request.event_config_condition_config_scope_id is not None
            and subscription.event_config_condition_config_scope_id
            != request.event_config_condition_config_scope_id
        ):
            continue
        if (
            request.object_instance_graph_id is not None
            and subscription.object_instance_graph_identity_id
            != request.object_instance_graph_id
        ):
            continue
        if (
            subscription.object_instance_graph_branch_id is not None
            and subscription.object_instance_graph_branch_id != branch_scope_id
        ):
            continue
        if not request.include_disabled_subscriptions and not subscription.is_enabled:
            continue
        if (
            not request.include_inactive_subscriptions
            and subscription.status != "active"
        ):
            continue
        filtered.append(subscription)
    return tuple(filtered)


def _select_actions_for_subscription(
    *,
    request: ReactivityActionIntentResolveRequest,
    subscription: ActorSubscriptionBridgeConfig,
    action_bindings: Sequence[ReactivityResolvedPolicyActionBinding],
    allow_subscription_action_fallback: bool,
) -> tuple[_ResolvedActionSelection, ...]:
    action_type_filters = {item for item in request.action_type_filters if item}
    action_binding_filters = set(request.event_config_action_config_id_filters)
    selected_binding_ids = set(subscription.event_config_action_config_ids)
    selected: list[_ResolvedActionSelection] = []

    for binding in action_bindings:
        if (
            selected_binding_ids
            and binding.event_config_action_config_id not in selected_binding_ids
        ):
            continue
        if subscription.action_type and binding.action_type != subscription.action_type:
            continue
        if action_type_filters and binding.action_type not in action_type_filters:
            continue
        if (
            action_binding_filters
            and binding.event_config_action_config_id not in action_binding_filters
        ):
            continue
        selected.append(
            _ResolvedActionSelection(
                event_config_action_config_id=binding.event_config_action_config_id,
                action_config_id=binding.action_config_id,
                action_type=binding.action_type,
            )
        )

    if (
        selected
        or action_bindings
        or subscription.action_type is None
        or not allow_subscription_action_fallback
    ):
        return tuple(selected)

    if action_type_filters and subscription.action_type not in action_type_filters:
        return ()
    if action_binding_filters and not selected_binding_ids.intersection(
        action_binding_filters
    ):
        return ()
    if selected_binding_ids:
        return tuple(
            _ResolvedActionSelection(
                event_config_action_config_id=event_config_action_config_id,
                action_config_id=None,
                action_type=subscription.action_type,
            )
            for event_config_action_config_id in sorted(
                selected_binding_ids,
                key=str,
            )
        )
    return (
        _ResolvedActionSelection(
            event_config_action_config_id=None,
            action_config_id=None,
            action_type=subscription.action_type,
        ),
    )


def _build_intent(
    *,
    request: ReactivityActionIntentResolveRequest,
    subscription: ActorSubscriptionBridgeConfig,
    selection: _ResolvedActionSelection,
) -> ReactivityActionIntent:
    action_config_id = selection.action_config_id
    if action_config_id is None:
        action_type = str(selection.action_type or "").strip()
        if not action_type:
            raise ValueError(
                "Reactivity action intent resolution requires ActionConfig identity."
            )
        action_config_id = stable_action_config_id(name=action_type)
    action_ref = (
        selection.event_config_action_config_id
        or action_config_id
        or selection.action_type
        or ""
    )
    intent_key = _subscription_intent_key(
        actor_subscription_id=subscription.id,
        action_ref=action_ref,
    )
    action_intent_id = stable_action_intent_id(
        event_id=request.event_id,
        config_id=action_config_id,
        intent_key=intent_key,
    )
    return ReactivityActionIntent(
        action_intent_id=action_intent_id,
        intent_key=intent_key,
        event_id=request.event_id,
        event_config_id=request.event_config_id,
        activation_id=request.activation_id,
        event_type=request.event_type,
        source=request.source,
        branch_id=request.branch_id,
        projection_hash=request.projection_hash,
        commit_id=request.commit_id,
        actor_id=subscription.actor_id,
        target_actor_id=request.target_actor_id,
        actor_subscription_id=subscription.id,
        event_config_condition_config_scope_id=(
            subscription.event_config_condition_config_scope_id
        ),
        event_config_condition_config_id=subscription.event_config_condition_config_id,
        event_config_action_config_id=selection.event_config_action_config_id,
        action_config_id=action_config_id,
        action_type=selection.action_type,
        root_object_id=request.root_object_id,
        object_instance_graph_id=request.object_instance_graph_id,
        object_instance_graph_commit_id=request.object_instance_graph_commit_id,
        object_instance_graph_branch_id=(
            request.object_instance_graph_branch_id or request.branch_id
        ),
        focus_scope_id=request.focus_scope_id,
        focus_id=request.focus_id,
        view_id=request.view_id,
        interface_id=request.interface_id,
        window_id=request.window_id,
        window_layout_id=request.window_layout_id,
        window_section_id=request.window_section_id,
        visible_window_section_ids=list(request.visible_window_section_ids or []),
        graph_hash_post=request.graph_hash_post,
        subscription_filter_config=subscription.filter_config,
        subscription_priority=subscription.priority,
    )


def _subscription_intent_key(
    *,
    actor_subscription_id: UUID,
    action_ref: object,
) -> str:
    """
    Derive the actor-free ontology ActionIntent key for subscription callers.

    Subscription provenance participates only in this caller-owned opaque key;
    canonical ActionIntent identity is generated from Event, ActionConfig, and
    the resulting intent key.
    """

    return f"{actor_subscription_id}:{action_ref}"


__all__ = [
    "IdentityServiceApiClientLike",
    "identity_service_api_route_ready",
    "resolve_action_intents",
]
