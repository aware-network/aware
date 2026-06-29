from __future__ import annotations

import importlib
import os
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from aware_meta.receipts.notifications import (
    LaneCommitReceiptNotification,
)
from aware_identity_service_dto.actor.reactivity_execution import (
    ActorReactivityActionExecutionRequest,
)
from aware_identity_service_dto.actor.reactivity_execution import (
    ActorReactivityActionExecutionResult,
)
from aware_identity_service_dto.actor.subscription import (
    ActorSubscriptionBridgeConfig,
)
from aware_reactivity_service_dto.reactivity.action_execution import ActionExecution
from aware_reactivity_service_dto.reactivity.action_feedback import ActionFeedback
from aware_reactivity_service_dto.reactivity.action_terminal import ActionTerminal
from aware_reactivity_service_dto.reactivity.bridge_event import (
    ActorReactivityBridgeEvent,
)
from aware_reactivity_service_dto.reactivity.event_condition_binding_resolution import (
    EventConditionBindingResolution,
)

LaneKey = tuple[UUID, str]
BridgeEventWatcher = Callable[[ActorReactivityBridgeEvent], Awaitable[None] | None]


class PersistedReactivityEvidence(Protocol):
    """Marker protocol for persisted reactivity evidence payloads."""


class ActorSubscriptionSource(Protocol):
    async def list_subscriptions(
        self,
        *,
        receipt: LaneCommitReceiptNotification | None = None,
        trigger_projection_hash: str | None = None,
    ) -> list[ActorSubscriptionBridgeConfig]: ...


@runtime_checkable
class ReactivityActionExecutor(Protocol):
    async def execute(
        self, *, request: ActorReactivityActionExecutionRequest
    ) -> ActorReactivityActionExecutionResult: ...


class ReactivityActionFeedbackPublisher(Protocol):
    async def publish_execution(self, *, execution: ActionExecution) -> None: ...

    async def publish_feedback(self, *, feedback: ActionFeedback) -> None: ...

    async def publish_terminal(self, *, terminal: ActionTerminal) -> None: ...


AgentReactivityActionExecutor = ReactivityActionExecutor


class ActorSubscriptionConditionEvaluator(Protocol):
    async def evaluate(
        self,
        *,
        receipt: LaneCommitReceiptNotification,
        event_config_condition_config_id: UUID,
    ) -> bool: ...

    async def resolve_binding(
        self,
        *,
        event_config_condition_config_id: UUID,
    ) -> EventConditionBindingResolution | None: ...


class ReactivityEvidenceWriter(Protocol):
    async def persist_for_binding(
        self,
        *,
        receipt: LaneCommitReceiptNotification,
        activation_id: UUID,
        event_type: str,
        source: str,
        actor_subscription_id: UUID | None,
        target_actor_id: UUID | None,
        binding: EventConditionBindingResolution,
    ) -> PersistedReactivityEvidence: ...


class ReactivityEventDispatcherService:
    """SDK-owned local constructor for the Reactivity dispatcher facade."""

    def __new__(cls, *args: object, **kwargs: object) -> object:
        service_class = get_local_reactivity_event_dispatcher_service_class()
        return service_class(*args, **kwargs)

    @classmethod
    def from_env(cls) -> object | None:
        service_class = get_local_reactivity_event_dispatcher_service_class()
        return service_class.from_env()


AgentReactivityBridgeService = ReactivityEventDispatcherService


class PrimaryFallbackActorSubscriptionSource:
    """SDK-owned local constructor for the Reactivity fallback source."""

    def __new__(cls, *args: object, **kwargs: object) -> object:
        source_class = get_local_primary_fallback_actor_subscription_source_class()
        return source_class(*args, **kwargs)


class LaneMaterializedActorSubscriptionSource:
    """SDK-owned local constructor for the Reactivity lane source."""

    def __new__(cls, *args: object, **kwargs: object) -> object:
        source_class = get_local_lane_materialized_actor_subscription_source_class()
        return source_class(*args, **kwargs)


def get_local_reactivity_event_dispatcher_service_class() -> type[object]:
    return _RetiredLocalReactivityEventDispatcherService


def get_local_primary_fallback_actor_subscription_source_class() -> type[object]:
    return _load_local_reactivity_attr(
        "aware_reactivity.subscription_sources",
        "PrimaryFallbackActorSubscriptionSource",
    )


def get_local_lane_materialized_actor_subscription_source_class() -> type[object]:
    return _load_local_reactivity_attr(
        "aware_reactivity.subscription_sources",
        "LaneMaterializedActorSubscriptionSource",
    )


def parse_actor_subscription_payload(
    payload: object,
) -> list[ActorSubscriptionBridgeConfig]:
    parser = _load_local_reactivity_attr(
        "aware_reactivity.subscription_sources",
        "parse_actor_subscription_payload",
    )
    return parser(payload)


def _load_local_reactivity_attr(module_name: str, attr_name: str) -> Any:
    module = importlib.import_module(module_name)
    return getattr(module, attr_name)


def _is_enabled_env(*names: str) -> bool:
    for name in names:
        raw = (os.environ.get(name) or "").strip().lower()
        if raw in {"1", "true", "yes", "y", "on"}:
            return True
    return False


class _RetiredLocalReactivityEventDispatcherService:
    def __init__(self, *args: object, **kwargs: object) -> None:
        enabled = bool(kwargs.get("enabled", args[0] if args else False))
        if enabled:
            raise RuntimeError(_RETIRED_LOCAL_DISPATCHER_MESSAGE)

    @classmethod
    def from_env(cls) -> object | None:
        if _is_enabled_env(
            "AWARE_REACTIVITY_DISPATCHER_ENABLED",
            "AWARE_NODE_AGENT_REACTIVITY_BRIDGE_ENABLED",
        ):
            raise RuntimeError(_RETIRED_LOCAL_DISPATCHER_MESSAGE)
        return None

    def start(self) -> None:
        return None

    def stop(self) -> None:
        return None


_RETIRED_LOCAL_DISPATCHER_MESSAGE = (
    "The Reactivity SDK no longer imports the deprecated local "
    "dispatcher. Use a Reactivity service host backed by Meta/Workspace "
    "materialized runtime truth; the local mailbox turn-engine dispatcher is "
    "retired until that clean owner is available."
)


__all__ = [
    "ActorReactivityBridgeEvent",
    "ActorSubscriptionBridgeConfig",
    "ActorSubscriptionConditionEvaluator",
    "ActorSubscriptionSource",
    "AgentReactivityActionExecutor",
    "AgentReactivityBridgeService",
    "BridgeEventWatcher",
    "LaneKey",
    "LaneMaterializedActorSubscriptionSource",
    "PersistedReactivityEvidence",
    "PrimaryFallbackActorSubscriptionSource",
    "ReactivityActionExecutor",
    "ReactivityActionFeedbackPublisher",
    "ReactivityEventDispatcherService",
    "ReactivityEvidenceWriter",
    "get_local_lane_materialized_actor_subscription_source_class",
    "get_local_primary_fallback_actor_subscription_source_class",
    "get_local_reactivity_event_dispatcher_service_class",
    "parse_actor_subscription_payload",
]
