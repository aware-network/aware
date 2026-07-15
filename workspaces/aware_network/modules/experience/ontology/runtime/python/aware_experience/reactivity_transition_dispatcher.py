from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol
from uuid import UUID

from aware_experience.section_graph_binding.api_models import (
    ApplyExperienceViewEventTransitionRequest,
    ApplyExperienceViewEventTransitionResponse,
    ExperienceSectionGraphBindingActivationScope,
)
from aware_experience.section_graph_binding.service import apply_view_event_transition
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntent,
    ReactivityActionIntentResolveRequest,
    ReactivityActionIntentResolveResponse,
)
from aware_reactivity_service_dto.reactivity.bridge_event import (
    ActorReactivityBridgeEvent,
)

DispatchStatus = Literal["applied", "skipped", "failed"]


class ReactivityTransitionSdk(Protocol):
    async def resolve_action_intents(
        self,
        request: ReactivityActionIntentResolveRequest,
    ) -> ReactivityActionIntentResolveResponse: ...

    def stream_events(
        self,
        *,
        subscriber_id: str,
        event_type_filters: Sequence[str] = (),
        environment_id_filters: Sequence[UUID] = (),
        branch_filters: Sequence[UUID] = (),
        projection_hash_filters: Sequence[str] = (),
        object_instance_graph_filters: Sequence[UUID] = (),
        include_replay: bool = True,
        resume_after_event_id: UUID | None = None,
    ) -> AsyncIterator[ActorReactivityBridgeEvent]: ...


class ExperienceViewTransitionApplier(Protocol):
    async def __call__(
        self,
        *,
        request: ApplyExperienceViewEventTransitionRequest,
        host_context: Any,
    ) -> ApplyExperienceViewEventTransitionResponse: ...


@dataclass(frozen=True, slots=True)
class ExperienceReactivityViewTransition:
    experience_name: str
    transition_key: str
    event_type: str
    target_view_ref: str
    target_binding_key: str
    profile_key: str | None = None
    source_view_ref: str | None = None
    action_type: str | None = None
    target_section_key: str | None = None
    target_graph_identity_ref: str | None = None
    activation_scope: ExperienceSectionGraphBindingActivationScope | None = None
    rationale: str | None = None
    section_title: str | None = None
    section_description: str | None = None
    focus_scope_title: str | None = None
    focus_scope_description: str | None = None


@dataclass(frozen=True, slots=True)
class ExperienceReactivityViewTransitionDispatch:
    status: DispatchStatus
    event_id: UUID
    event_type: str
    transition_key: str | None = None
    action_intent_id: UUID | None = None
    action_type: str | None = None
    reason: str | None = None
    response: ApplyExperienceViewEventTransitionResponse | None = None
    error: str | None = None


async def dispatch_reactivity_view_transition_with_sdk(
    *,
    sdk: ReactivityTransitionSdk,
    event: ActorReactivityBridgeEvent,
    transitions: Sequence[ExperienceReactivityViewTransition],
    host_context: Any,
    subscriber_id: str = "experience.transition",
    apply_transition: ExperienceViewTransitionApplier = apply_view_event_transition,
) -> tuple[ExperienceReactivityViewTransitionDispatch, ...]:
    event_transitions = _transitions_for_event(event=event, transitions=transitions)
    if not event_transitions:
        return (
            _skipped(
                event=event,
                reason="no_matching_event_transition",
            ),
        )

    action_type_filters = _action_type_filters(transitions=event_transitions)
    action_intents: tuple[ReactivityActionIntent, ...] = ()
    if action_type_filters:
        response = await sdk.resolve_action_intents(
            build_action_intent_resolve_request(
                event=event,
                subscriber_id=subscriber_id,
                action_type_filters=action_type_filters,
            )
        )
        if response.accepted is False:
            return (
                _skipped(
                    event=event,
                    reason=response.error or "action_intent_resolution_rejected",
                ),
            )
        action_intents = tuple(response.intents or ())

    return await dispatch_reactivity_view_transition(
        event=event,
        transitions=event_transitions,
        host_context=host_context,
        action_intents=action_intents,
        apply_transition=apply_transition,
    )


async def dispatch_reactivity_view_transition(
    *,
    event: ActorReactivityBridgeEvent,
    transitions: Sequence[ExperienceReactivityViewTransition],
    host_context: Any,
    action_intents: Sequence[ReactivityActionIntent] = (),
    apply_transition: ExperienceViewTransitionApplier = apply_view_event_transition,
) -> tuple[ExperienceReactivityViewTransitionDispatch, ...]:
    event_transitions = _transitions_for_event(event=event, transitions=transitions)
    if not event_transitions:
        return (_skipped(event=event, reason="no_matching_event_transition"),)

    results: list[ExperienceReactivityViewTransitionDispatch] = []
    event_only_transitions = [
        transition
        for transition in event_transitions
        if _optional_text(transition.action_type) is None
    ]
    for transition in event_only_transitions:
        results.append(
            await _apply_transition(
                event=event,
                transition=transition,
                host_context=host_context,
                action_intent=None,
                apply_transition=apply_transition,
            )
        )

    action_transitions = [
        transition
        for transition in event_transitions
        if _optional_text(transition.action_type) is not None
    ]
    if action_transitions:
        matching_intents = _matching_action_intents(
            event=event, action_intents=action_intents
        )
        for intent in matching_intents:
            for transition in action_transitions:
                if _optional_text(transition.action_type) != _optional_text(
                    intent.action_type
                ):
                    continue
                results.append(
                    await _apply_transition(
                        event=event,
                        transition=transition,
                        host_context=host_context,
                        action_intent=intent,
                        apply_transition=apply_transition,
                    )
                )

    if results:
        return tuple(results)
    return (_skipped(event=event, reason="no_matching_action_transition"),)


async def stream_reactivity_view_transition_dispatches(
    *,
    sdk: ReactivityTransitionSdk,
    transitions: Sequence[ExperienceReactivityViewTransition],
    host_context: Any,
    subscriber_id: str = "experience.transition",
    environment_id_filters: Sequence[UUID] = (),
    branch_filters: Sequence[UUID] = (),
    projection_hash_filters: Sequence[str] = (),
    object_instance_graph_filters: Sequence[UUID] = (),
    include_replay: bool = True,
    resume_after_event_id: UUID | None = None,
    max_events: int | None = None,
    apply_transition: ExperienceViewTransitionApplier = apply_view_event_transition,
) -> AsyncIterator[ExperienceReactivityViewTransitionDispatch]:
    event_count = 0
    async for event in sdk.stream_events(
        subscriber_id=subscriber_id,
        event_type_filters=_event_type_filters(transitions=transitions),
        environment_id_filters=environment_id_filters,
        branch_filters=branch_filters,
        projection_hash_filters=projection_hash_filters,
        object_instance_graph_filters=object_instance_graph_filters,
        include_replay=include_replay,
        resume_after_event_id=resume_after_event_id,
    ):
        for result in await dispatch_reactivity_view_transition_with_sdk(
            sdk=sdk,
            event=event,
            transitions=transitions,
            host_context=host_context,
            subscriber_id=subscriber_id,
            apply_transition=apply_transition,
        ):
            yield result
        event_count += 1
        if max_events is not None and event_count >= max_events:
            return


def build_action_intent_resolve_request(
    *,
    event: ActorReactivityBridgeEvent,
    subscriber_id: str,
    action_type_filters: Sequence[str] = (),
) -> ReactivityActionIntentResolveRequest:
    return ReactivityActionIntentResolveRequest(
        subscriber_id=subscriber_id,
        event_id=event.event_id,
        event_config_id=event.event_config_id,
        activation_id=event.activation_id,
        event_type=event.event_type,
        source=event.source,
        created_at_unix_ms=event.created_at_unix_ms,
        branch_id=event.branch_id,
        projection_hash=event.projection_hash,
        commit_id=event.commit_id,
        event_config_condition_config_id=event.event_config_condition_config_id,
        root_object_id=event.root_object_id,
        object_instance_graph_id=event.object_instance_graph_id,
        object_instance_graph_commit_id=event.object_instance_graph_commit_id,
        object_instance_graph_branch_id=event.branch_id,
        graph_hash_post=event.graph_hash_post,
        action_type_filters=list(action_type_filters),
    )


def _transitions_for_event(
    *,
    event: ActorReactivityBridgeEvent,
    transitions: Sequence[ExperienceReactivityViewTransition],
) -> tuple[ExperienceReactivityViewTransition, ...]:
    event_type = _required_text(event.event_type, label="event.event_type")
    return tuple(
        transition
        for transition in transitions
        if _required_text(transition.event_type, label="transition.event_type")
        == event_type
    )


async def _apply_transition(
    *,
    event: ActorReactivityBridgeEvent,
    transition: ExperienceReactivityViewTransition,
    host_context: Any,
    action_intent: ReactivityActionIntent | None,
    apply_transition: ExperienceViewTransitionApplier,
) -> ExperienceReactivityViewTransitionDispatch:
    action_intent_id = (
        action_intent.action_intent_id if action_intent is not None else None
    )
    action_type = (
        _optional_text(action_intent.action_type)
        if action_intent is not None
        else _optional_text(transition.action_type)
    )
    try:
        response = await apply_transition(
            request=_apply_request(
                event=event,
                transition=transition,
                action_intent=action_intent,
            ),
            host_context=host_context,
        )
    except Exception as exc:
        return ExperienceReactivityViewTransitionDispatch(
            status="failed",
            event_id=event.event_id,
            event_type=event.event_type,
            transition_key=transition.transition_key,
            action_intent_id=action_intent_id,
            action_type=action_type,
            reason="apply_transition_failed",
            error=str(exc),
        )
    return ExperienceReactivityViewTransitionDispatch(
        status="applied",
        event_id=event.event_id,
        event_type=event.event_type,
        transition_key=transition.transition_key,
        action_intent_id=action_intent_id,
        action_type=action_type,
        response=response,
    )


def _apply_request(
    *,
    event: ActorReactivityBridgeEvent,
    transition: ExperienceReactivityViewTransition,
    action_intent: ReactivityActionIntent | None,
) -> ApplyExperienceViewEventTransitionRequest:
    return ApplyExperienceViewEventTransitionRequest(
        request_id=event.event_id,
        experience_name=_required_text(
            transition.experience_name,
            label="transition.experience_name",
        ),
        profile_key=_optional_text(transition.profile_key),
        transition_key=_required_text(
            transition.transition_key,
            label="transition.transition_key",
        ),
        source_view_ref=_optional_text(transition.source_view_ref),
        event_id=event.event_id,
        event_type=event.event_type,
        action_intent_id=(
            action_intent.action_intent_id if action_intent is not None else None
        ),
        action_type=(
            _optional_text(action_intent.action_type)
            if action_intent is not None
            else _optional_text(transition.action_type)
        ),
        activation_scope=_activation_scope_for_event(
            event=event,
            transition=transition,
            action_intent=action_intent,
        ),
        rationale=_optional_text(transition.rationale),
        section_title=_optional_text(transition.section_title),
        section_description=_optional_text(transition.section_description),
        focus_scope_title=_optional_text(transition.focus_scope_title),
        focus_scope_description=_optional_text(transition.focus_scope_description),
    )


def _activation_scope_for_event(
    *,
    event: ActorReactivityBridgeEvent,
    transition: ExperienceReactivityViewTransition,
    action_intent: ReactivityActionIntent | None,
) -> ExperienceSectionGraphBindingActivationScope:
    scope = transition.activation_scope
    if scope is None:
        return ExperienceSectionGraphBindingActivationScope(
            branch_id=(
                action_intent.object_instance_graph_branch_id
                if action_intent is not None
                and action_intent.object_instance_graph_branch_id is not None
                else event.branch_id
            ),
            state_projection_hash=event.projection_hash,
            focus_scope_id=(
                action_intent.focus_scope_id if action_intent is not None else None
            ),
            focus_id=action_intent.focus_id if action_intent is not None else None,
        )

    updates: dict[str, object] = {}
    if scope.branch_id is None:
        updates["branch_id"] = (
            action_intent.object_instance_graph_branch_id
            if action_intent is not None
            and action_intent.object_instance_graph_branch_id is not None
            else event.branch_id
        )
    if scope.state_projection_hash is None:
        updates["state_projection_hash"] = event.projection_hash
    if action_intent is not None and scope.focus_scope_id is None:
        updates["focus_scope_id"] = action_intent.focus_scope_id
    if action_intent is not None and scope.focus_id is None:
        updates["focus_id"] = action_intent.focus_id
    if not updates:
        return scope
    return scope.model_copy(update=updates)


def _matching_action_intents(
    *,
    event: ActorReactivityBridgeEvent,
    action_intents: Sequence[ReactivityActionIntent],
) -> tuple[ReactivityActionIntent, ...]:
    return tuple(
        intent
        for intent in action_intents
        if intent.event_id == event.event_id and intent.event_type == event.event_type
    )


def _event_type_filters(
    *,
    transitions: Sequence[ExperienceReactivityViewTransition],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                _required_text(transition.event_type, label="transition.event_type")
                for transition in transitions
            },
            key=str.casefold,
        )
    )


def _action_type_filters(
    *,
    transitions: Sequence[ExperienceReactivityViewTransition],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                action_type
                for transition in transitions
                for action_type in [_optional_text(transition.action_type)]
                if action_type is not None
            },
            key=str.casefold,
        )
    )


def _skipped(
    *,
    event: ActorReactivityBridgeEvent,
    reason: str,
) -> ExperienceReactivityViewTransitionDispatch:
    return ExperienceReactivityViewTransitionDispatch(
        status="skipped",
        event_id=event.event_id,
        event_type=event.event_type,
        reason=reason,
    )


def _required_text(value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} is required")
    return normalized


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


__all__ = [
    "ExperienceReactivityViewTransition",
    "ExperienceReactivityViewTransitionDispatch",
    "ExperienceViewTransitionApplier",
    "ReactivityTransitionSdk",
    "build_action_intent_resolve_request",
    "dispatch_reactivity_view_transition",
    "dispatch_reactivity_view_transition_with_sdk",
    "stream_reactivity_view_transition_dispatches",
]
