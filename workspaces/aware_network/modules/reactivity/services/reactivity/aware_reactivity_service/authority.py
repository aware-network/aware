from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from typing import TypeAlias
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_environment_service_dto.environment.environment import (
    LaneCommitReceiptNotification,
)
from aware_reactivity.stable_ids import (
    stable_event_id,
    stable_action_execution_id,
    stable_action_feedback_id,
)
from aware_reactivity_service_dto.reactivity.action_execution import ActionExecution
from aware_reactivity_service_dto.reactivity.action_execution import (
    ReactivityActionExecutionClaimRequest,
    ReactivityActionExecutionClaimResponse,
)
from aware_reactivity_service_dto.reactivity.action_feedback import ActionFeedback
from aware_reactivity_service_dto.reactivity.action_terminal import ActionTerminal
from aware_reactivity_service_dto.reactivity.bridge_event import (
    ActorReactivityBridgeEvent,
)
from aware_reactivity_service_dto.reactivity.event_meaning import (
    ReactivityEventMeaningProviderIntent,
    ReactivityEventMeaningProviderResolveRequest,
    ReactivityEventMeaningProviderResolveResponse,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityActionLifecycleSubscriptionRequest,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityActionLifecycleSubscriptionResponse,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityActionLifecyclePublishRequest,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityActionLifecyclePublishResponse,
)
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntent,
)
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntentResolveRequest,
)
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntentResolveResponse,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityEventSubscriptionRequest,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityEventSubscriptionResponse,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivitySemanticEventPublishRequest,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivitySemanticEventPublishResponse,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleEnsureRequest,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleEnsureResponse,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleListRequest,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleListResponse,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityServiceStatusRequest,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityServiceStatusResponse,
)

from .policy_registry import ReactivityPolicyRegistry
from .action_execution_claim import claim_action_execution
from .subscription_action_resolver import (
    IdentityServiceApiClientLike,
    identity_service_api_route_ready,
    resolve_action_intents,
)

ActionLifecycleEvent: TypeAlias = (
    ReactivityActionIntent | ActionExecution | ActionFeedback | ActionTerminal
)
_SEMANTIC_EVENT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://reactivity/semantic-bridge-event/v0",
)
_EVENT_MEANING_PROVIDER_INTENT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://reactivity/event-meaning-provider-intent/v0",
)


@dataclass(slots=True)
class _StreamSubscription[T]:
    predicate: Callable[[T], bool]
    queue: asyncio.Queue[T] = field(default_factory=asyncio.Queue)


@dataclass(slots=True)
class ReactivityServiceAuthority:
    """In-process authority backing the generated Reactivity service protocol."""

    service_id: str = "reactivity"
    upstream_source: str = "environment_service_api_fanout"
    identity_api_client: IdentityServiceApiClientLike | None = None
    _environment_fanout_attached: bool = False
    _environment_fanout_running: bool = False
    _environment_fanout_error: str | None = None
    _events: list[ActorReactivityBridgeEvent] = field(default_factory=list)
    _events_by_id: dict[UUID, ActorReactivityBridgeEvent] = field(default_factory=dict)
    _action_events: list[ActionLifecycleEvent] = field(default_factory=list)
    _policy_registry: ReactivityPolicyRegistry = field(
        default_factory=ReactivityPolicyRegistry
    )
    _event_environment_ids: dict[UUID, UUID] = field(default_factory=dict)
    _event_subscriptions: list[_StreamSubscription[ActorReactivityBridgeEvent]] = field(
        default_factory=list
    )
    _action_subscriptions: list[_StreamSubscription[ActionLifecycleEvent]] = field(
        default_factory=list
    )
    _action_execution_claim_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def get_status(
        self,
        request: ReactivityServiceStatusRequest,
    ) -> ReactivityServiceStatusResponse:
        identity_route_ready = (
            self.identity_api_client is not None or identity_service_api_route_ready()
        )
        blockers: list[str] = []
        if not self._environment_fanout_attached:
            blockers.append("environment_fanout_not_attached")
        elif not self._environment_fanout_running:
            blockers.append(
                "environment_fanout_error"
                if self._environment_fanout_error
                else "environment_fanout_stopped"
            )
        if not identity_route_ready:
            blockers.append("identity_subscription_route_unavailable")
        active = (
            self._environment_fanout_attached
            and self._environment_fanout_running
            and identity_route_ready
            and not self._environment_fanout_error
        )
        return ReactivityServiceStatusResponse(
            request_id=request.request_id,
            service_id=self.service_id,
            active=active,
            upstream_source=self.upstream_source,
            environment_fanout_attached=self._environment_fanout_attached,
            environment_fanout_running=self._environment_fanout_running,
            identity_subscription_route_ready=identity_route_ready,
            blockers=blockers,
            info="ready" if active else "blocked",
            error=self._environment_fanout_error,
        )

    def set_environment_fanout_lifecycle(
        self,
        *,
        attached: bool,
        running: bool,
        error: str | None = None,
    ) -> None:
        self._environment_fanout_attached = attached
        self._environment_fanout_running = running
        self._environment_fanout_error = error

    async def subscribe_events(
        self,
        request: ReactivityEventSubscriptionRequest,
    ) -> ReactivityEventSubscriptionResponse:
        return ReactivityEventSubscriptionResponse(
            subscriber_id=request.subscriber_id,
            accepted=True,
            upstream_source=self.upstream_source,
            resume_after_event_id=request.resume_after_event_id,
        )

    async def publish_semantic_event(
        self,
        request: ReactivitySemanticEventPublishRequest,
    ) -> ReactivitySemanticEventPublishResponse:
        error = _semantic_event_publish_validation_error(request)
        if error is not None:
            return ReactivitySemanticEventPublishResponse(
                request_id=request.request_id,
                accepted=False,
                event_id=request.event.event_id,
                error=error,
            )

        event = request.event
        existing = self._events_by_id.get(event.event_id)
        if existing is not None:
            if existing != event:
                return ReactivitySemanticEventPublishResponse(
                    request_id=request.request_id,
                    accepted=False,
                    event_id=event.event_id,
                    error="event_id_conflict",
                )
            return ReactivitySemanticEventPublishResponse(
                request_id=request.request_id,
                accepted=True,
                published=False,
                duplicate=True,
                event_id=event.event_id,
                info=f"semantic event already published by {request.publisher_id}",
            )

        await self.publish_event(event)
        return ReactivitySemanticEventPublishResponse(
            request_id=request.request_id,
            accepted=True,
            published=True,
            duplicate=False,
            event_id=event.event_id,
            info=f"semantic event published by {request.publisher_id}",
        )

    async def ensure_policy_bundle(
        self,
        request: ReactivityPolicyBundleEnsureRequest,
    ) -> ReactivityPolicyBundleEnsureResponse:
        return self._policy_registry.ensure_bundle(request)

    async def list_policy_bundles(
        self,
        request: ReactivityPolicyBundleListRequest,
    ) -> ReactivityPolicyBundleListResponse:
        return self._policy_registry.list_bundles(request)

    async def resolve_event_meaning_provider_intent(
        self,
        request: ReactivityEventMeaningProviderResolveRequest,
    ) -> ReactivityEventMeaningProviderResolveResponse:
        event = request.event
        if not event.event_type.strip():
            return ReactivityEventMeaningProviderResolveResponse(
                request_id=request.request_id,
                accepted=False,
                error="event.event_type is required",
            )
        providers = self._policy_registry.resolve_event_meaning_providers(
            event_type=event.event_type,
            event_config_id=request.event_config_id,
            resolver_key=request.resolver_key,
            environment_id=self._event_environment_ids.get(event.event_id),
        )
        if not providers:
            return ReactivityEventMeaningProviderResolveResponse(
                request_id=request.request_id,
                accepted=True,
                info="no event meaning provider registered",
            )
        if len(providers) != 1:
            return ReactivityEventMeaningProviderResolveResponse(
                request_id=request.request_id,
                accepted=False,
                error=f"event meaning provider is ambiguous: {len(providers)} matches",
            )
        provider = providers[0]
        intent_id = uuid5(
            _EVENT_MEANING_PROVIDER_INTENT_NAMESPACE,
            f"{event.event_id}:{provider.event_config_meaning_resolver_config_id}",
        )
        return ReactivityEventMeaningProviderResolveResponse(
            request_id=request.request_id,
            accepted=True,
            intent=ReactivityEventMeaningProviderIntent(
                intent_id=intent_id,
                event=event,
                owner_ref=provider.owner_ref,
                policy_key=provider.policy_key,
                resolver_key=provider.resolver_key,
                event_config_id=provider.event_config_id,
                event_config_meaning_resolver_config_id=(
                    provider.event_config_meaning_resolver_config_id
                ),
                action_config_id=provider.action_config_id,
                api_capability_endpoint_id=provider.api_capability_endpoint_id,
            ),
            info="one event meaning provider intent resolved",
        )

    def stream_events(
        self,
        request: ReactivityEventSubscriptionRequest,
    ) -> AsyncIterator[ActorReactivityBridgeEvent]:
        predicate = _event_predicate(request)
        subscription = _StreamSubscription[ActorReactivityBridgeEvent](
            predicate=predicate
        )
        self._event_subscriptions.append(subscription)
        replay_events = (
            tuple(event for event in self._events if predicate(event))
            if request.include_replay
            else ()
        )

        async def _stream() -> AsyncIterator[ActorReactivityBridgeEvent]:
            try:
                for event in replay_events:
                    yield event
                while True:
                    yield await subscription.queue.get()
            finally:
                if subscription in self._event_subscriptions:
                    self._event_subscriptions.remove(subscription)

        return _stream()

    async def subscribe_action_lifecycle(
        self,
        request: ReactivityActionLifecycleSubscriptionRequest,
    ) -> ReactivityActionLifecycleSubscriptionResponse:
        return ReactivityActionLifecycleSubscriptionResponse(
            subscriber_id=request.subscriber_id,
            accepted=True,
            upstream_source=self.upstream_source,
            resume_after_action_execution_id=request.resume_after_action_execution_id,
        )

    async def resolve_action_intents(
        self,
        request: ReactivityActionIntentResolveRequest,
    ) -> ReactivityActionIntentResolveResponse:
        return await resolve_action_intents(
            request=request,
            policy_registry=self._policy_registry,
            identity_api_client=self.identity_api_client,
            environment_id=self._event_environment_ids.get(request.event_id),
        )

    async def claim_action_execution(
        self,
        request: ReactivityActionExecutionClaimRequest,
    ) -> ReactivityActionExecutionClaimResponse:
        return await claim_action_execution(
            request,
            lock=self._action_execution_claim_lock,
        )

    async def publish_action_lifecycle(
        self,
        request: ReactivityActionLifecyclePublishRequest,
    ) -> ReactivityActionLifecyclePublishResponse:
        events = _canonical_action_lifecycle_events(request)
        if not events:
            return ReactivityActionLifecyclePublishResponse(
                request_id=request.request_id,
                accepted=False,
                info="no lifecycle event payload supplied",
                error="empty_lifecycle_publish",
            )

        for event in events:
            await self._publish_action_event(event)

        return ReactivityActionLifecyclePublishResponse(
            request_id=request.request_id,
            accepted=True,
            published_count=len(events),
            action_intent_id=_first_action_intent_id(events),
            action_execution_id=_first_action_execution_id(events),
            action_feedback_id=_first_action_feedback_id(events),
            info=f"published action lifecycle events from {request.publisher_id}",
        )

    def stream_action_lifecycle(
        self,
        request: ReactivityActionLifecycleSubscriptionRequest,
    ) -> AsyncIterator[ActionLifecycleEvent]:
        predicate = _action_predicate(request)
        subscription = _StreamSubscription[ActionLifecycleEvent](predicate=predicate)
        self._action_subscriptions.append(subscription)
        replay_events = (
            tuple(event for event in self._action_events if predicate(event))
            if request.include_replay
            else ()
        )

        async def _stream() -> AsyncIterator[ActionLifecycleEvent]:
            try:
                for event in replay_events:
                    yield event
                while True:
                    yield await subscription.queue.get()
            finally:
                if subscription in self._action_subscriptions:
                    self._action_subscriptions.remove(subscription)

        return _stream()

    async def publish_event(self, event: ActorReactivityBridgeEvent) -> None:
        existing = self._events_by_id.get(event.event_id)
        if existing is not None:
            if existing != event:
                raise ValueError(
                    f"Reactivity semantic event id conflict for {event.event_id}"
                )
            return
        self._events_by_id[event.event_id] = event
        self._events.append(event)
        for subscription in tuple(self._event_subscriptions):
            if subscription.predicate(event):
                await subscription.queue.put(event)

    async def process_environment_commit_receipt(
        self,
        receipt: LaneCommitReceiptNotification,
    ) -> tuple[ActorReactivityBridgeEvent, ...]:
        if receipt.environment_id is None:
            return ()

        resolved_events = self._policy_registry.resolve_events_for_operation_label(
            receipt.operation_label,
            environment_id=receipt.environment_id,
        )
        events = tuple(
            _bridge_event_from_environment_receipt(
                receipt=receipt,
                environment_id=receipt.environment_id,
                event_config_id=resolved.event_config_id,
                event_type=resolved.event_type,
                source=self.upstream_source,
                event_config_condition_config_id=(
                    resolved.event_config_condition_config_id
                ),
            )
            for resolved in resolved_events
        )
        for event in events:
            self._event_environment_ids[event.event_id] = receipt.environment_id
            await self.publish_event(event)
        return events

    async def publish_execution(self, *, execution: ActionExecution) -> None:
        await self._publish_action_event(_canonical_action_execution(execution))

    async def publish_feedback(self, *, feedback: ActionFeedback) -> None:
        await self._publish_action_event(_canonical_action_feedback(feedback))

    async def publish_terminal(self, *, terminal: ActionTerminal) -> None:
        await self._publish_action_event(terminal)

    async def _publish_action_event(self, event: ActionLifecycleEvent) -> None:
        self._action_events.append(event)
        for subscription in tuple(self._action_subscriptions):
            if subscription.predicate(event):
                await subscription.queue.put(event)

    def attach_dispatcher(self, dispatcher: object) -> None:
        subscribe_events = getattr(dispatcher, "subscribe_events")
        set_action_feedback_publisher = getattr(
            dispatcher,
            "set_action_feedback_publisher",
        )
        subscribe_events(watcher=self.publish_event)
        set_action_feedback_publisher(action_feedback_publisher=self)


def _bridge_event_from_environment_receipt(
    *,
    receipt: LaneCommitReceiptNotification,
    environment_id: UUID,
    event_config_id: UUID,
    event_type: str,
    source: str,
    event_config_condition_config_id: UUID | None,
) -> ActorReactivityBridgeEvent:
    activation_id = uuid5(
        _SEMANTIC_EVENT_NAMESPACE,
        ":".join(
            (
                event_type.casefold().strip(),
                str(environment_id),
                str(receipt.branch_id),
                receipt.projection_hash,
                str(receipt.commit_id),
                str(event_config_condition_config_id or ""),
            )
        ),
    )
    return ActorReactivityBridgeEvent(
        event_id=stable_event_id(
            config_id=event_config_id,
            activation_id=activation_id,
        ),
        event_config_id=event_config_id,
        activation_id=activation_id,
        event_type=event_type,
        source=source,
        created_at_unix_ms=receipt.created_at_unix_ms or 0,
        branch_id=receipt.branch_id,
        projection_hash=receipt.projection_hash,
        commit_id=receipt.commit_id,
        event_config_condition_config_id=event_config_condition_config_id,
        root_object_id=receipt.root_object_id,
        object_instance_graph_id=receipt.object_instance_graph_id,
        object_instance_graph_commit_id=receipt.object_instance_graph_commit_id,
        graph_hash_post=receipt.graph_hash_post,
    )


def _semantic_event_publish_validation_error(
    request: ReactivitySemanticEventPublishRequest,
) -> str | None:
    if not request.publisher_id.strip():
        return "publisher_id is required"
    event = request.event
    if not event.event_type.strip():
        return "event.event_type is required"
    if not event.source.strip():
        return "event.source is required"
    if not event.projection_hash.strip():
        return "event.projection_hash is required"
    expected_event_id = stable_event_id(
        config_id=event.event_config_id,
        activation_id=event.activation_id,
    )
    if event.event_id != expected_event_id:
        return "event.event_id does not match canonical EventConfig/activation identity"
    if event.created_at_unix_ms < 0:
        return "event.created_at_unix_ms must be non-negative"
    return None


def _canonical_action_lifecycle_events(
    request: ReactivityActionLifecyclePublishRequest,
) -> tuple[ActionLifecycleEvent, ...]:
    events: list[ActionLifecycleEvent] = []
    intent = request.intent
    if intent is not None:
        events.append(intent)

    execution = request.execution
    if execution is not None:
        execution = _canonical_action_execution(execution)
        events.append(execution)

    feedback = request.feedback
    if feedback is not None:
        feedback = _canonical_action_feedback(feedback)
        events.append(feedback)

    terminal = request.terminal
    if terminal is not None:
        events.append(terminal)

    return tuple(events)


def _canonical_action_execution(execution: ActionExecution) -> ActionExecution:
    if execution.action_execution_id is not None:
        return execution
    return execution.model_copy(
        update={
            "action_execution_id": stable_action_execution_id(
                action_intent_id=execution.action_intent_id,
                execution_key=execution.execution_key,
            )
        }
    )


def _canonical_action_feedback(feedback: ActionFeedback) -> ActionFeedback:
    if feedback.action_feedback_id is not None:
        return feedback
    return feedback.model_copy(
        update={
            "action_feedback_id": stable_action_feedback_id(
                action_execution_id=feedback.action_execution_id,
                sequence=feedback.sequence,
            )
        }
    )


def _first_action_intent_id(events: tuple[ActionLifecycleEvent, ...]) -> UUID | None:
    for event in events:
        action_intent_id = getattr(event, "action_intent_id", None)
        if action_intent_id is not None:
            return action_intent_id
    return None


def _first_action_execution_id(events: tuple[ActionLifecycleEvent, ...]) -> UUID | None:
    for event in events:
        action_execution_id = getattr(event, "action_execution_id", None)
        if action_execution_id is not None:
            return action_execution_id
    return None


def _first_action_feedback_id(events: tuple[ActionLifecycleEvent, ...]) -> UUID | None:
    for event in events:
        action_feedback_id = getattr(event, "action_feedback_id", None)
        if action_feedback_id is not None:
            return action_feedback_id
    return None


def _event_predicate(
    request: ReactivityEventSubscriptionRequest,
) -> Callable[[ActorReactivityBridgeEvent], bool]:
    event_types = set(request.event_type_filters)
    branch_ids = set(request.branch_filters)
    projection_hashes = set(request.projection_hash_filters)
    object_instance_graph_ids = set(request.object_instance_graph_filters)
    resume_after_event_id = request.resume_after_event_id
    resume_seen = resume_after_event_id is None

    def _matches(event: ActorReactivityBridgeEvent) -> bool:
        nonlocal resume_seen
        if not resume_seen:
            resume_seen = event.event_id == resume_after_event_id
            return False
        if event_types and event.event_type not in event_types:
            return False
        if branch_ids and event.branch_id not in branch_ids:
            return False
        if projection_hashes and event.projection_hash not in projection_hashes:
            return False
        if (
            object_instance_graph_ids
            and event.object_instance_graph_id not in object_instance_graph_ids
        ):
            return False
        return True

    return _matches


def _action_predicate(
    request: ReactivityActionLifecycleSubscriptionRequest,
) -> Callable[[ActionLifecycleEvent], bool]:
    event_ids = set(request.event_id_filters)
    action_intent_ids = set(request.action_intent_id_filters)
    action_execution_ids = set(request.action_execution_id_filters)
    action_types = set(request.action_type_filters)
    branch_ids = set(request.branch_filters)
    projection_hashes = set(request.projection_hash_filters)
    resume_after_action_execution_id = request.resume_after_action_execution_id
    resume_seen = resume_after_action_execution_id is None

    def _matches(event: ActionLifecycleEvent) -> bool:
        nonlocal resume_seen
        action_execution_id = getattr(event, "action_execution_id", None)
        if not resume_seen:
            resume_seen = action_execution_id == resume_after_action_execution_id
            return False
        if event_ids and event.event_id not in event_ids:
            return False
        action_intent_id = getattr(event, "action_intent_id", None)
        if action_intent_ids and action_intent_id not in action_intent_ids:
            return False
        if action_execution_ids and action_execution_id not in action_execution_ids:
            return False
        action_type = getattr(event, "action_type", None)
        if action_types and action_type not in action_types:
            return False
        branch_id = getattr(event, "branch_id", None)
        if branch_ids and branch_id not in branch_ids:
            return False
        projection_hash = getattr(event, "projection_hash", None)
        if projection_hashes and projection_hash not in projection_hashes:
            return False
        return True

    return _matches


__all__ = [
    "ActionLifecycleEvent",
    "ReactivityServiceAuthority",
]
