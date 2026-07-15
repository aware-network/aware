from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from dataclasses import dataclass, replace
from typing import Protocol, cast
from uuid import UUID

from aware_experience.action_dispatch.bridge import ActionDispatchBridgeResult
from aware_experience.reactivity_transition_dispatcher import (
    build_action_intent_resolve_request,
)
from aware_experience.supervisor.manager import (
    ExperienceSessionFeatureLease,
    ExperienceSessionFeatureRunResult,
)
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntent,
    ReactivityActionIntentResolveRequest,
    ReactivityActionIntentResolveResponse,
)
from aware_reactivity_service_dto.reactivity.bridge_event import (
    ActorReactivityBridgeEvent,
)

REACTIVITY_ACTION_DISPATCH_FEATURE = "reactivity_action_dispatch"


class ReactivityActionDispatchSdk(Protocol):
    def stream_events(
        self,
        *,
        subscriber_id: str,
        event_type_filters: Sequence[str] = (),
        branch_filters: Sequence[UUID] = (),
        projection_hash_filters: Sequence[str] = (),
        object_instance_graph_filters: Sequence[UUID] = (),
        include_replay: bool = True,
        resume_after_event_id: UUID | None = None,
    ) -> AsyncIterator[ActorReactivityBridgeEvent]: ...

    async def resolve_action_intents(
        self,
        request: ReactivityActionIntentResolveRequest,
    ) -> ReactivityActionIntentResolveResponse: ...


ActionIntentDispatcher = Callable[
    [ActorReactivityBridgeEvent, ReactivityActionIntent],
    Awaitable[ActionDispatchBridgeResult],
]
ActionIntentDispatcherFactory = Callable[
    [ExperienceSessionFeatureLease],
    ActionIntentDispatcher,
]
ReactivityActionDispatchSdkFactory = Callable[
    [ExperienceSessionFeatureLease],
    ReactivityActionDispatchSdk,
]


@dataclass(frozen=True, slots=True)
class ExperienceReactivityActionDispatchConfig:
    subscriber_id: str
    event_type_filters: tuple[str, ...] = ()
    action_type_filters: tuple[str, ...] = ()
    branch_filters: tuple[UUID, ...] = ()
    projection_hash_filters: tuple[str, ...] = ()
    object_instance_graph_filters: tuple[UUID, ...] = ()
    include_replay: bool = True
    resume_after_event_id: UUID | None = None
    max_events: int | None = None


@dataclass(frozen=True, slots=True)
class ExperienceReactivityActionDispatchHealth:
    status: str
    subscriber_id: str
    event_count: int = 0
    intent_count: int = 0
    claimed_count: int = 0
    replay_skipped_count: int = 0
    fulfilled_count: int = 0
    failed_count: int = 0
    continuation_count: int = 0
    last_event_id: UUID | None = None
    last_action_intent_id: UUID | None = None
    last_result_status: str | None = None
    last_error: str | None = None
    info: str | None = None


async def run_experience_reactivity_action_dispatch_supervisor(
    *,
    sdk: ReactivityActionDispatchSdk,
    dispatch_intent: ActionIntentDispatcher,
    config: ExperienceReactivityActionDispatchConfig,
) -> ExperienceReactivityActionDispatchHealth:
    health = ExperienceReactivityActionDispatchHealth(
        status="running",
        subscriber_id=config.subscriber_id,
        info="Experience Reactivity action dispatch supervisor started.",
    )
    try:
        async for event in sdk.stream_events(
            subscriber_id=config.subscriber_id,
            event_type_filters=config.event_type_filters,
            branch_filters=config.branch_filters,
            projection_hash_filters=config.projection_hash_filters,
            object_instance_graph_filters=config.object_instance_graph_filters,
            include_replay=config.include_replay,
            resume_after_event_id=config.resume_after_event_id,
        ):
            response = await sdk.resolve_action_intents(
                build_action_intent_resolve_request(
                    event=event,
                    subscriber_id=config.subscriber_id,
                    action_type_filters=config.action_type_filters,
                )
            )
            if not response.accepted:
                raise RuntimeError(
                    response.error or "reactivity_action_intent_resolution_rejected"
                )
            health = _with_event(
                health, event=event, intent_count=len(response.intents)
            )
            for intent in response.intents:
                result = await dispatch_intent(event, intent)
                health = _with_result(health, intent=intent, result=result)
            if (
                config.max_events is not None
                and health.event_count >= config.max_events
            ):
                break
    except Exception as exc:
        return replace(
            health,
            status="failed",
            last_error=str(exc),
            info="Experience Reactivity action dispatch supervisor failed.",
        )
    failed = health.failed_count > 0
    return replace(
        health,
        status="failed" if failed else "completed",
        info=(
            "Experience Reactivity action dispatch supervisor completed with failures."
            if failed
            else "Experience Reactivity action dispatch supervisor completed."
        ),
    )


@dataclass(frozen=True, slots=True)
class ExperienceReactivityActionDispatchFeatureAdapter:
    sdk_for_lease: ReactivityActionDispatchSdkFactory
    dispatch_intent_for_lease: ActionIntentDispatcherFactory
    feature_key: str = REACTIVITY_ACTION_DISPATCH_FEATURE

    async def run(
        self,
        lease: ExperienceSessionFeatureLease,
    ) -> ExperienceSessionFeatureRunResult:
        health = await run_experience_reactivity_action_dispatch_supervisor(
            sdk=self.sdk_for_lease(lease),
            dispatch_intent=self.dispatch_intent_for_lease(lease),
            config=_config_from_lease(lease),
        )
        return ExperienceSessionFeatureRunResult(
            status="failed" if health.status == "failed" else "completed",
            info=health.info,
            last_error=health.last_error,
            health=health,
        )

    async def release(self, lease: ExperienceSessionFeatureLease) -> None:
        return None


def _config_from_lease(
    lease: ExperienceSessionFeatureLease,
) -> ExperienceReactivityActionDispatchConfig:
    scope = lease.session_scope
    config = lease.config
    subscriber_id = config.get("subscriber_id")
    max_events = config.get("max_events")
    resume_after_event_id = config.get("resume_after_event_id")
    object_instance_graph_id = config.get("object_instance_graph_id")
    return ExperienceReactivityActionDispatchConfig(
        subscriber_id=(
            subscriber_id
            if isinstance(subscriber_id, str) and subscriber_id
            else f"experience.action_dispatch.{lease.lease_key}"
        ),
        event_type_filters=_string_tuple(config.get("event_type_filters")),
        action_type_filters=_string_tuple(config.get("action_type_filters")),
        branch_filters=(scope.branch_id,) if scope.branch_id else (),
        projection_hash_filters=(
            (scope.projection_hash,) if scope.projection_hash else ()
        ),
        object_instance_graph_filters=(
            (cast(UUID, object_instance_graph_id),)
            if isinstance(object_instance_graph_id, UUID)
            else ()
        ),
        include_replay=bool(config.get("include_replay", True)),
        resume_after_event_id=(
            cast(UUID, resume_after_event_id)
            if isinstance(resume_after_event_id, UUID)
            else None
        ),
        max_events=max_events if isinstance(max_events, int) else None,
    )


def _with_event(
    health: ExperienceReactivityActionDispatchHealth,
    *,
    event: ActorReactivityBridgeEvent,
    intent_count: int,
) -> ExperienceReactivityActionDispatchHealth:
    return replace(
        health,
        event_count=health.event_count + 1,
        intent_count=health.intent_count + intent_count,
        last_event_id=event.event_id,
    )


def _with_result(
    health: ExperienceReactivityActionDispatchHealth,
    *,
    intent: ReactivityActionIntent,
    result: ActionDispatchBridgeResult,
) -> ExperienceReactivityActionDispatchHealth:
    claimed = result.execution_claim is not None and result.status not in {
        "claim_failed",
        "claim_replay_skipped",
    }
    replay_skipped = result.status == "claim_replay_skipped"
    fulfilled = result.status == "fulfilled"
    failed = result.status in {
        "binding_failed",
        "claim_failed",
        "composition_rejected",
        "continuation_failed",
        "fulfillment_failed",
        "role_denied",
    }
    return replace(
        health,
        claimed_count=health.claimed_count + int(claimed),
        replay_skipped_count=health.replay_skipped_count + int(replay_skipped),
        fulfilled_count=health.fulfilled_count + int(fulfilled),
        failed_count=health.failed_count + int(failed),
        continuation_count=health.continuation_count
        + int(result.program_continuation_activation is not None),
        last_action_intent_id=intent.action_intent_id,
        last_result_status=result.status,
        last_error=result.reason if failed else health.last_error,
    )


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item)


__all__ = [
    "ActionIntentDispatcher",
    "ActionIntentDispatcherFactory",
    "ExperienceReactivityActionDispatchConfig",
    "ExperienceReactivityActionDispatchFeatureAdapter",
    "ExperienceReactivityActionDispatchHealth",
    "REACTIVITY_ACTION_DISPATCH_FEATURE",
    "ReactivityActionDispatchSdk",
    "ReactivityActionDispatchSdkFactory",
    "run_experience_reactivity_action_dispatch_supervisor",
]
