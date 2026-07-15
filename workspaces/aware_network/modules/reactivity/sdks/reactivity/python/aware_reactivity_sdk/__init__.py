from __future__ import annotations

from importlib import import_module
from typing import Any

from aware_reactivity_sdk.client import (
    AwareReactivitySdk,
    ReactivityGeneratedApiClient,
    ReactivitySdkClient,
    ReactivitySdkError,
    build_action_lifecycle_subscription_request,
    build_event_subscription_request,
)

_LAZY_EXPORTS = {
    "ActorSubscriptionConditionEvaluator": (
        "aware_reactivity_sdk.service_host",
        "ActorSubscriptionConditionEvaluator",
    ),
    "ActorSubscriptionSource": (
        "aware_reactivity_sdk.service_host",
        "ActorSubscriptionSource",
    ),
    "AgentReactivityActionExecutor": (
        "aware_reactivity_sdk.service_host",
        "AgentReactivityActionExecutor",
    ),
    "AgentReactivityBridgeService": (
        "aware_reactivity_sdk.service_host",
        "AgentReactivityBridgeService",
    ),
    "BridgeEventWatcher": (
        "aware_reactivity_sdk.service_host",
        "BridgeEventWatcher",
    ),
    "LaneKey": (
        "aware_reactivity_sdk.service_host",
        "LaneKey",
    ),
    "LaneMaterializedActorSubscriptionSource": (
        "aware_reactivity_sdk.service_host",
        "LaneMaterializedActorSubscriptionSource",
    ),
    "PrimaryFallbackActorSubscriptionSource": (
        "aware_reactivity_sdk.service_host",
        "PrimaryFallbackActorSubscriptionSource",
    ),
    "ReactivityActionExecutor": (
        "aware_reactivity_sdk.service_host",
        "ReactivityActionExecutor",
    ),
    "ReactivityEventDispatcherService": (
        "aware_reactivity_sdk.service_host",
        "ReactivityEventDispatcherService",
    ),
    "parse_actor_subscription_payload": (
        "aware_reactivity_sdk.service_host",
        "parse_actor_subscription_payload",
    ),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value

__all__ = [
    "ActorSubscriptionConditionEvaluator",
    "ActorSubscriptionSource",
    "AwareReactivitySdk",
    "AgentReactivityActionExecutor",
    "AgentReactivityBridgeService",
    "BridgeEventWatcher",
    "LaneKey",
    "LaneMaterializedActorSubscriptionSource",
    "PrimaryFallbackActorSubscriptionSource",
    "ReactivityGeneratedApiClient",
    "ReactivityActionExecutor",
    "ReactivityEventDispatcherService",
    "ReactivitySdkClient",
    "ReactivitySdkError",
    "build_action_lifecycle_subscription_request",
    "build_event_subscription_request",
    "parse_actor_subscription_payload",
]
