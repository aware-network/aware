from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from aware_interface import (
    InterfaceMaterializedPaneState,
    InterfaceResolvedPaneDescriptor,
    InterfaceRuntimeState,
)


@dataclass(frozen=True, slots=True)
class InterfaceSharedAttentionTarget:
    environment_session_id: str
    environment_navigation_context_id: str | None = None
    environment_session_thread_id: str | None = None
    environment_session_attention_session_id: str | None = None
    thread_id: str | None = None
    thread_layout_id: str | None = None
    branch_id: str | None = None
    projection_hash: str | None = None
    attention_session_id: str | None = None
    active_attention_focus_transition_id: str | None = None

    def shared_key(self) -> tuple[str | None, ...]:
        return (
            self.environment_session_id,
            self.environment_navigation_context_id,
            self.thread_id,
            self.thread_layout_id,
            self.projection_hash,
            self.attention_session_id,
            self.active_attention_focus_transition_id,
        )


@dataclass(frozen=True, slots=True)
class InterfaceSharedSessionDemoParticipant:
    actor_id: str
    pane_state_key: str
    view_ref: str | None = None
    projection_view_key: str | None = None
    window_key: str | None = None
    layout_key: str | None = None
    section_key: str | None = None
    pane_kind: str | None = None
    action_keys: tuple[str, ...] = ()
    session_view_frame_digest: str | None = None
    target: InterfaceSharedAttentionTarget | None = None


@dataclass(frozen=True, slots=True)
class InterfaceSharedSessionDemoReadiness:
    status: str
    participant_count: int = 0
    participants: tuple[InterfaceSharedSessionDemoParticipant, ...] = ()
    shared_target: InterfaceSharedAttentionTarget | None = None
    blockers: tuple[str, ...] = ()
    evidence: dict[str, object] | None = None

    @property
    def ready(self) -> bool:
        return self.status == "ready"


def resolve_shared_session_demo_readiness(
    *,
    runtime_states: Sequence[InterfaceRuntimeState],
    required_participant_count: int = 2,
    required_view_actions: Mapping[str, Iterable[str]] | None = None,
) -> InterfaceSharedSessionDemoReadiness:
    participants: list[InterfaceSharedSessionDemoParticipant] = []
    blockers: list[str] = []
    for runtime_state in runtime_states:
        panes_by_key = {
            _pane_state_key_for_descriptor(pane): pane
            for pane in runtime_state.resolved_panes
        }
        for pane_state in runtime_state.materialized_pane_states:
            participant = _participant_from_pane_state(
                pane_state=pane_state,
                pane=panes_by_key.get(pane_state.pane_state_key),
                blockers=blockers,
            )
            if participant is not None:
                participants.append(participant)

    unique_participants = _unique_participants_by_actor(participants)
    shared_target = _shared_target(unique_participants, blockers)
    _validate_required_views(
        participants=unique_participants,
        required_view_actions=required_view_actions or {},
        blockers=blockers,
    )
    if len(unique_participants) < required_participant_count:
        blockers.append("participant_count_below_required")

    status = "ready"
    if blockers:
        status = (
            "blocked" if any("mismatch" in item for item in blockers) else "waiting"
        )
    return InterfaceSharedSessionDemoReadiness(
        status=status,
        participant_count=len(unique_participants),
        participants=tuple(unique_participants),
        shared_target=shared_target,
        blockers=tuple(dict.fromkeys(blockers)),
        evidence={
            "source_kind": "interface_shared_session_demo_readiness",
            "runtime_state_count": len(runtime_states),
            "materialized_participant_count": len(participants),
            "required_participant_count": required_participant_count,
        },
    )


def _participant_from_pane_state(
    *,
    pane_state: InterfaceMaterializedPaneState,
    pane: InterfaceResolvedPaneDescriptor | None,
    blockers: list[str],
) -> InterfaceSharedSessionDemoParticipant | None:
    provenance = _mapping(pane_state.provenance)
    frame = _mapping(provenance.get("session_view_frame"))
    if not frame:
        blockers.append("session_view_frame_provenance_required")
        return None
    session_scope = _mapping(frame.get("session_scope"))
    actor_id = _text(session_scope.get("actor_id"))
    if actor_id is None:
        blockers.append("participant_actor_id_required")
        return None
    target = _target_from_frame(frame=frame, provenance=provenance, blockers=blockers)
    return InterfaceSharedSessionDemoParticipant(
        actor_id=actor_id,
        pane_state_key=pane_state.pane_state_key,
        view_ref=_text(session_scope.get("view_ref"))
        or _text(provenance.get("view_ref")),
        projection_view_key=(
            _text(session_scope.get("projection_view_key"))
            or _text(provenance.get("projection_view_key"))
        ),
        window_key=_text(session_scope.get("window_key")) or pane_state.window_key,
        layout_key=_text(session_scope.get("layout_key")) or pane_state.layout_key,
        section_key=_text(session_scope.get("section_key")) or pane_state.section_key,
        pane_kind=pane_state.pane_kind,
        action_keys=tuple(pane.action_keys) if pane is not None else (),
        session_view_frame_digest=_text(provenance.get("session_view_frame_digest")),
        target=target,
    )


def _target_from_frame(
    *,
    frame: Mapping[str, object],
    provenance: Mapping[str, object],
    blockers: list[str],
) -> InterfaceSharedAttentionTarget | None:
    environment_session_id = _field_text(
        frame=frame,
        provenance=provenance,
        key="environment_session_id",
    )
    attention_session_id = _field_text(
        frame=frame,
        provenance=provenance,
        key="attention_session_id",
    )
    active_transition_id = _field_text(
        frame=frame,
        provenance=provenance,
        key="active_attention_focus_transition_id",
    )
    thread_layout_id = _field_text(
        frame=frame,
        provenance=provenance,
        key="thread_layout_id",
    )
    missing = [
        key
        for key, value in (
            ("environment_session_id", environment_session_id),
            ("attention_session_id", attention_session_id),
            ("active_attention_focus_transition_id", active_transition_id),
            ("thread_layout_id", thread_layout_id),
        )
        if value is None
    ]
    for key in missing:
        blockers.append(f"shared_target_required:{key}")
    if missing:
        return None
    return InterfaceSharedAttentionTarget(
        environment_session_id=environment_session_id or "",
        environment_navigation_context_id=_field_text(
            frame=frame,
            provenance=provenance,
            key="environment_navigation_context_id",
        ),
        environment_session_thread_id=_field_text(
            frame=frame,
            provenance=provenance,
            key="environment_session_thread_id",
        ),
        environment_session_attention_session_id=_field_text(
            frame=frame,
            provenance=provenance,
            key="environment_session_attention_session_id",
        ),
        thread_id=_field_text(frame=frame, provenance=provenance, key="thread_id"),
        thread_layout_id=thread_layout_id,
        branch_id=_field_text(frame=frame, provenance=provenance, key="branch_id"),
        projection_hash=_field_text(
            frame=frame,
            provenance=provenance,
            key="projection_hash",
        ),
        attention_session_id=attention_session_id,
        active_attention_focus_transition_id=active_transition_id,
    )


def _shared_target(
    participants: Sequence[InterfaceSharedSessionDemoParticipant],
    blockers: list[str],
) -> InterfaceSharedAttentionTarget | None:
    targets = [participant.target for participant in participants if participant.target]
    if not targets:
        return None
    first = targets[0]
    if any(target.shared_key() != first.shared_key() for target in targets[1:]):
        blockers.append("shared_attention_target_mismatch")
        return None
    return first


def _validate_required_views(
    *,
    participants: Sequence[InterfaceSharedSessionDemoParticipant],
    required_view_actions: Mapping[str, Iterable[str]],
    blockers: list[str],
) -> None:
    by_view: dict[str, set[str]] = {}
    for participant in participants:
        if participant.view_ref is None:
            continue
        by_view.setdefault(participant.view_ref, set()).update(participant.action_keys)
    for view_ref, action_keys in required_view_actions.items():
        if view_ref not in by_view:
            blockers.append(f"required_view_missing:{view_ref}")
            continue
        for action_key in action_keys:
            if action_key not in by_view[view_ref]:
                blockers.append(f"required_action_missing:{view_ref}:{action_key}")


def _unique_participants_by_actor(
    participants: Sequence[InterfaceSharedSessionDemoParticipant],
) -> tuple[InterfaceSharedSessionDemoParticipant, ...]:
    by_actor: dict[str, InterfaceSharedSessionDemoParticipant] = {}
    for participant in participants:
        by_actor.setdefault(participant.actor_id, participant)
    return tuple(by_actor.values())


def _field_text(
    *,
    frame: Mapping[str, object],
    provenance: Mapping[str, object],
    key: str,
) -> str | None:
    return _text(provenance.get(key)) or _text(frame.get(key))


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _pane_state_key_for_descriptor(pane: InterfaceResolvedPaneDescriptor) -> str:
    return ":".join(
        (
            pane.window_key,
            pane.layout_key,
            pane.section_key,
            pane.pane_kind,
            str(pane.pane_config_id or ""),
            pane.state_projection_hash or "",
        )
    )


__all__ = [
    "InterfaceSharedAttentionTarget",
    "InterfaceSharedSessionDemoParticipant",
    "InterfaceSharedSessionDemoReadiness",
    "resolve_shared_session_demo_readiness",
]
