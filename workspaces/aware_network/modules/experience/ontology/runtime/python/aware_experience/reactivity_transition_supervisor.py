from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

from aware_experience.reactivity_transition_dispatcher import (
    ExperienceReactivityViewTransitionDispatch,
    ExperienceViewTransitionApplier,
    ReactivityTransitionSdk,
    stream_reactivity_view_transition_dispatches,
)
from aware_experience.reactivity_transition_specs import (
    ExperienceReactivityViewTransitionSpecResolution,
)
from aware_experience.section_graph_binding.service import apply_view_event_transition

SupervisorStatus = Literal["starting", "running", "completed", "failed"]
SupervisorEventKind = Literal["started", "dispatch", "completed", "failed"]
TransitionSpecLoader = Callable[
    [],
    Awaitable[ExperienceReactivityViewTransitionSpecResolution],
]


@dataclass(frozen=True, slots=True)
class ExperienceReactivityTransitionSupervisorConfig:
    experience_name: str
    profile_key: str | None = None
    subscriber_id: str = "experience.transition"
    environment_id_filters: tuple[UUID, ...] = ()
    branch_filters: tuple[UUID, ...] = ()
    projection_hash_filters: tuple[str, ...] = ()
    object_instance_graph_filters: tuple[UUID, ...] = ()
    include_replay: bool = True
    resume_after_event_id: UUID | None = None
    max_events: int | None = None


@dataclass(frozen=True, slots=True)
class ExperienceReactivityTransitionSupervisorHealth:
    status: SupervisorStatus
    experience_name: str
    profile_key: str | None
    subscriber_id: str
    catalog_revision: str | None = None
    transition_count: int = 0
    dispatch_count: int = 0
    applied_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    last_event_id: UUID | None = None
    last_event_type: str | None = None
    last_transition_key: str | None = None
    last_error: str | None = None
    info: str | None = None


@dataclass(frozen=True, slots=True)
class ExperienceReactivityTransitionSupervisorEvent:
    kind: SupervisorEventKind
    health: ExperienceReactivityTransitionSupervisorHealth
    dispatch: ExperienceReactivityViewTransitionDispatch | None = None


@dataclass(frozen=True, slots=True)
class ExperienceReactivityTransitionSupervisorRun:
    health: ExperienceReactivityTransitionSupervisorHealth
    events: tuple[ExperienceReactivityTransitionSupervisorEvent, ...]


async def stream_experience_reactivity_transition_supervisor(
    *,
    sdk: ReactivityTransitionSdk,
    host_context: Any,
    load_specs: TransitionSpecLoader,
    config: ExperienceReactivityTransitionSupervisorConfig,
    apply_transition: ExperienceViewTransitionApplier = apply_view_event_transition,
) -> AsyncIterator[ExperienceReactivityTransitionSupervisorEvent]:
    try:
        spec_resolution = await load_specs()
        health = ExperienceReactivityTransitionSupervisorHealth(
            status="running",
            experience_name=spec_resolution.experience_name,
            profile_key=spec_resolution.profile_key,
            subscriber_id=config.subscriber_id,
            catalog_revision=spec_resolution.catalog_revision,
            transition_count=len(spec_resolution.transitions),
            info="Experience Reactivity transition supervisor started.",
        )
        yield ExperienceReactivityTransitionSupervisorEvent(
            kind="started",
            health=health,
        )
        if not spec_resolution.transitions:
            yield ExperienceReactivityTransitionSupervisorEvent(
                kind="completed",
                health=_complete_health(
                    health,
                    info="No Experience Reactivity view transitions are configured.",
                ),
            )
            return

        async for dispatch in stream_reactivity_view_transition_dispatches(
            sdk=sdk,
            transitions=spec_resolution.transitions,
            host_context=host_context,
            subscriber_id=config.subscriber_id,
            environment_id_filters=config.environment_id_filters,
            branch_filters=config.branch_filters,
            projection_hash_filters=config.projection_hash_filters,
            object_instance_graph_filters=config.object_instance_graph_filters,
            include_replay=config.include_replay,
            resume_after_event_id=config.resume_after_event_id,
            max_events=config.max_events,
            apply_transition=apply_transition,
        ):
            health = _health_after_dispatch(health, dispatch=dispatch)
            yield ExperienceReactivityTransitionSupervisorEvent(
                kind="dispatch",
                health=health,
                dispatch=dispatch,
            )

        yield ExperienceReactivityTransitionSupervisorEvent(
            kind="completed",
            health=_complete_health(
                health,
                info="Experience Reactivity transition supervisor completed.",
            ),
        )
    except Exception as exc:
        yield ExperienceReactivityTransitionSupervisorEvent(
            kind="failed",
            health=ExperienceReactivityTransitionSupervisorHealth(
                status="failed",
                experience_name=config.experience_name,
                profile_key=config.profile_key,
                subscriber_id=config.subscriber_id,
                last_error=str(exc),
                info="Experience Reactivity transition supervisor failed.",
            ),
        )


async def run_experience_reactivity_transition_supervisor(
    *,
    sdk: ReactivityTransitionSdk,
    host_context: Any,
    load_specs: TransitionSpecLoader,
    config: ExperienceReactivityTransitionSupervisorConfig,
    apply_transition: ExperienceViewTransitionApplier = apply_view_event_transition,
) -> ExperienceReactivityTransitionSupervisorRun:
    events = [
        event
        async for event in stream_experience_reactivity_transition_supervisor(
            sdk=sdk,
            host_context=host_context,
            load_specs=load_specs,
            config=config,
            apply_transition=apply_transition,
        )
    ]
    if not events:
        raise RuntimeError("Experience Reactivity transition supervisor emitted no events.")
    return ExperienceReactivityTransitionSupervisorRun(
        health=events[-1].health,
        events=tuple(events),
    )


def _health_after_dispatch(
    health: ExperienceReactivityTransitionSupervisorHealth,
    *,
    dispatch: ExperienceReactivityViewTransitionDispatch,
) -> ExperienceReactivityTransitionSupervisorHealth:
    applied = 1 if dispatch.status == "applied" else 0
    skipped = 1 if dispatch.status == "skipped" else 0
    failed = 1 if dispatch.status == "failed" else 0
    return ExperienceReactivityTransitionSupervisorHealth(
        status="running",
        experience_name=health.experience_name,
        profile_key=health.profile_key,
        subscriber_id=health.subscriber_id,
        catalog_revision=health.catalog_revision,
        transition_count=health.transition_count,
        dispatch_count=health.dispatch_count + 1,
        applied_count=health.applied_count + applied,
        skipped_count=health.skipped_count + skipped,
        failed_count=health.failed_count + failed,
        last_event_id=dispatch.event_id,
        last_event_type=dispatch.event_type,
        last_transition_key=dispatch.transition_key,
        last_error=dispatch.error or health.last_error,
        info=dispatch.reason or dispatch.status,
    )


def _complete_health(
    health: ExperienceReactivityTransitionSupervisorHealth,
    *,
    info: str,
) -> ExperienceReactivityTransitionSupervisorHealth:
    return ExperienceReactivityTransitionSupervisorHealth(
        status="completed",
        experience_name=health.experience_name,
        profile_key=health.profile_key,
        subscriber_id=health.subscriber_id,
        catalog_revision=health.catalog_revision,
        transition_count=health.transition_count,
        dispatch_count=health.dispatch_count,
        applied_count=health.applied_count,
        skipped_count=health.skipped_count,
        failed_count=health.failed_count,
        last_event_id=health.last_event_id,
        last_event_type=health.last_event_type,
        last_transition_key=health.last_transition_key,
        last_error=health.last_error,
        info=info,
    )


__all__ = [
    "ExperienceReactivityTransitionSupervisorConfig",
    "ExperienceReactivityTransitionSupervisorEvent",
    "ExperienceReactivityTransitionSupervisorHealth",
    "ExperienceReactivityTransitionSupervisorRun",
    "TransitionSpecLoader",
    "run_experience_reactivity_transition_supervisor",
    "stream_experience_reactivity_transition_supervisor",
]
