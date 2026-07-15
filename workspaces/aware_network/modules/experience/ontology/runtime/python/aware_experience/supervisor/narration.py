from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from dataclasses import dataclass, field
import inspect
from typing import Protocol, cast
from uuid import UUID

from aware_environment_service_dto.environment.environment import (
    LaneCommitReceiptNotification,
)
from aware_experience.supervisor.manager import (
    ExperienceSessionFeatureLease,
    ExperienceSessionFeatureRunResult,
)


EXPERIENCE_SESSION_NARRATOR_FEATURE = "experience_session_narrator"


class ExperienceSessionNarrationReceiptSource(Protocol):
    def stream_commit_receipts(
        self,
        *,
        subscriber_id: str,
        resume_after_commit_id: UUID | None = None,
    ) -> AsyncIterator[LaneCommitReceiptNotification]: ...


class ExperienceSessionNarrationCommitReader(Protocol):
    async def get_object_instance_graph_commit(
        self,
        *,
        commit_id: UUID,
        actor_id: UUID | None = None,
        environment_id: UUID | None = None,
        process_id: UUID | None = None,
        thread_id: UUID | None = None,
        branch_id: UUID | None = None,
        projection_hash: str | None = None,
    ) -> object: ...


class ExperienceSessionNarrationEventSink(Protocol):
    def publish_session_narration_event(
        self,
        event: "ExperienceSessionNarrationEvent",
    ) -> Awaitable[None] | None: ...


ExperienceSessionNarrationSemanticsBuilder = Callable[
    [ExperienceSessionFeatureLease, LaneCommitReceiptNotification, object],
    Mapping[str, object] | Awaitable[Mapping[str, object]],
]


@dataclass(frozen=True, slots=True)
class ExperienceSessionNarrationEvent:
    lease_key: str
    feature_key: str
    experience_name: str
    branch_id: UUID
    projection_hash: str
    commit_id: UUID
    narration_lines: tuple[str, ...] = ()
    profile_key: str | None = None
    environment_id: UUID | None = None
    actor_id: UUID | None = None
    process_id: UUID | None = None
    thread_id: UUID | None = None
    projection_experience_graph_identity_id: UUID | None = None
    object_projection_graph_identity_id: UUID | None = None
    object_instance_graph_identity_id: UUID | None = None
    object_instance_graph_branch_id: UUID | None = None
    object_instance_graph_commit_id: UUID | None = None
    graph_hash_post: str | None = None
    operation_label: str | None = None
    semantics: Mapping[str, object] = field(default_factory=dict)
    evidence: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExperienceSessionNarratorHealth:
    status: str
    event_count: int = 0
    last_commit_id: UUID | None = None
    last_error: str | None = None


@dataclass(slots=True)
class ExperienceSessionNarrationEventBuffer:
    events: list[ExperienceSessionNarrationEvent] = field(default_factory=list)

    def publish_session_narration_event(
        self,
        event: ExperienceSessionNarrationEvent,
    ) -> None:
        self.events.append(event)

    def recent_events(
        self,
        *,
        lease_key: str | None = None,
        after_commit_id: UUID | None = None,
        limit: int | None = None,
    ) -> tuple[ExperienceSessionNarrationEvent, ...]:
        events = tuple(
            event
            for event in self.events
            if (lease_key is None or event.lease_key == lease_key)
            and (after_commit_id is None or event.commit_id.int > after_commit_id.int)
        )
        if limit is not None and limit > 0:
            return events[-limit:]
        return events


@dataclass(frozen=True, slots=True)
class ExperienceSessionNarratorFeatureAdapter:
    receipt_source_for_lease: Callable[
        [ExperienceSessionFeatureLease],
        ExperienceSessionNarrationReceiptSource | None,
    ]
    commit_reader_for_lease: Callable[
        [ExperienceSessionFeatureLease],
        ExperienceSessionNarrationCommitReader | None,
    ]
    semantic_payload_for_commit: ExperienceSessionNarrationSemanticsBuilder | None = (
        None
    )
    event_sink: ExperienceSessionNarrationEventSink | None = None
    feature_key: str = EXPERIENCE_SESSION_NARRATOR_FEATURE

    async def run(
        self,
        lease: ExperienceSessionFeatureLease,
    ) -> ExperienceSessionFeatureRunResult:
        scope = lease.session_scope
        if scope.branch_id is None or not (scope.projection_hash or "").strip():
            return _failed_result(
                "Experience session narrator requires branch_id and projection_hash."
            )

        source = self.receipt_source_for_lease(lease)
        if source is None:
            return _failed_result(
                "Experience session narrator requires Environment commit fanout."
            )
        commit_reader = self.commit_reader_for_lease(lease)
        if commit_reader is None:
            return _failed_result(
                "Experience session narrator requires Environment commit readback."
            )

        event_count = 0
        last_commit_id: UUID | None = None
        try:
            async for receipt in source.stream_commit_receipts(
                subscriber_id=_subscriber_id(lease),
                resume_after_commit_id=_resume_after_commit_id(lease),
            ):
                if not _matches_lease_lane(lease=lease, receipt=receipt):
                    continue
                commit_payload = await commit_reader.get_object_instance_graph_commit(
                    commit_id=receipt.commit_id,
                    actor_id=scope.actor_id,
                    environment_id=scope.environment_id,
                    process_id=scope.process_id,
                    thread_id=scope.thread_id,
                    branch_id=scope.branch_id,
                    projection_hash=scope.projection_hash,
                )
                semantics = await _build_semantics(
                    builder=self.semantic_payload_for_commit,
                    lease=lease,
                    receipt=receipt,
                    commit_payload=commit_payload,
                )
                event = _event_from_receipt(
                    lease=lease,
                    receipt=receipt,
                    semantics=semantics,
                )
                await _publish_event(sink=self.event_sink, event=event)
                event_count += 1
                last_commit_id = receipt.commit_id
                max_events = _max_events(lease)
                if max_events is not None and event_count >= max_events:
                    break
        except Exception as exc:
            return ExperienceSessionFeatureRunResult(
                status="failed",
                info="Experience session narrator failed.",
                last_error=str(exc),
                health=ExperienceSessionNarratorHealth(
                    status="failed",
                    event_count=event_count,
                    last_commit_id=last_commit_id,
                    last_error=str(exc),
                ),
            )

        return ExperienceSessionFeatureRunResult(
            status="completed",
            info=f"Experience session narrator processed {event_count} commit(s).",
            health=ExperienceSessionNarratorHealth(
                status="completed",
                event_count=event_count,
                last_commit_id=last_commit_id,
            ),
        )

    async def release(self, lease: ExperienceSessionFeatureLease) -> None:
        _ = lease
        return None


def _failed_result(error: str) -> ExperienceSessionFeatureRunResult:
    return ExperienceSessionFeatureRunResult(
        status="failed",
        info="Experience session narrator is not configured.",
        last_error=error,
        health=ExperienceSessionNarratorHealth(status="failed", last_error=error),
    )


def _matches_lease_lane(
    *,
    lease: ExperienceSessionFeatureLease,
    receipt: LaneCommitReceiptNotification,
) -> bool:
    scope = lease.session_scope
    return (
        receipt.branch_id == scope.branch_id
        and (receipt.projection_hash or "").strip()
        == (scope.projection_hash or "").strip()
    )


async def _build_semantics(
    *,
    builder: ExperienceSessionNarrationSemanticsBuilder | None,
    lease: ExperienceSessionFeatureLease,
    receipt: LaneCommitReceiptNotification,
    commit_payload: object,
) -> Mapping[str, object]:
    if builder is None:
        return {}
    result = builder(lease, receipt, commit_payload)
    if inspect.isawaitable(result):
        return cast(Mapping[str, object], await result)
    return result


def _event_from_receipt(
    *,
    lease: ExperienceSessionFeatureLease,
    receipt: LaneCommitReceiptNotification,
    semantics: Mapping[str, object],
) -> ExperienceSessionNarrationEvent:
    scope = lease.session_scope
    handoff_scope = _handoff_scope(lease)
    return ExperienceSessionNarrationEvent(
        lease_key=lease.lease_key,
        feature_key=lease.feature_key,
        experience_name=scope.experience_name,
        profile_key=scope.profile_key,
        environment_id=receipt.environment_id or scope.environment_id,
        actor_id=receipt.actor_id or scope.actor_id,
        process_id=receipt.process_id or scope.process_id,
        thread_id=receipt.thread_id or scope.thread_id,
        branch_id=receipt.branch_id,
        projection_hash=receipt.projection_hash,
        commit_id=receipt.commit_id,
        projection_experience_graph_identity_id=_uuid_from_mapping(
            handoff_scope,
            "projection_experience_graph_identity_id",
        ),
        object_projection_graph_identity_id=(
            receipt.object_projection_graph_identity_id
            or _uuid_from_mapping(handoff_scope, "object_projection_graph_identity_id")
        ),
        object_instance_graph_identity_id=receipt.object_instance_graph_identity_id,
        object_instance_graph_branch_id=(
            receipt.object_instance_graph_branch_id
            or _uuid_from_mapping(handoff_scope, "object_instance_graph_branch_id")
        ),
        object_instance_graph_commit_id=receipt.object_instance_graph_commit_id,
        graph_hash_post=receipt.graph_hash_post,
        operation_label=receipt.operation_label,
        narration_lines=_narration_lines(semantics),
        semantics=dict(semantics),
        evidence={
            "source": "experience_session_narrator",
            "handoff_scope": dict(handoff_scope),
        },
    )


async def _publish_event(
    *,
    sink: ExperienceSessionNarrationEventSink | None,
    event: ExperienceSessionNarrationEvent,
) -> None:
    if sink is None:
        return
    result = sink.publish_session_narration_event(event)
    if inspect.isawaitable(result):
        await result


def _handoff_scope(lease: ExperienceSessionFeatureLease) -> Mapping[str, object]:
    value = lease.config.get("handoff_scope")
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    return {}


def _narration_lines(semantics: Mapping[str, object]) -> tuple[str, ...]:
    lines = semantics.get("narration_lines")
    if not isinstance(lines, (list, tuple)):
        return ()
    return tuple(str(line) for line in lines if str(line).strip())


def _subscriber_id(lease: ExperienceSessionFeatureLease) -> str:
    value = lease.config.get("subscriber_id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return f"experience.narrator.{lease.lease_key}"


def _resume_after_commit_id(lease: ExperienceSessionFeatureLease) -> UUID | None:
    return _uuid_value(lease.config.get("resume_after_commit_id"))


def _max_events(lease: ExperienceSessionFeatureLease) -> int | None:
    value = lease.config.get("max_events")
    if isinstance(value, int) and value > 0:
        return value
    return None


def _uuid_from_mapping(mapping: Mapping[str, object], key: str) -> UUID | None:
    return _uuid_value(mapping.get(key))


def _uuid_value(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return UUID(value)
        except ValueError:
            return None
    return None


def experience_session_narration_event_payload(
    event: ExperienceSessionNarrationEvent,
) -> dict[str, object]:
    return {
        "lease_key": event.lease_key,
        "feature_key": event.feature_key,
        "experience_name": event.experience_name,
        "profile_key": event.profile_key,
        "environment_id": _uuid_text(event.environment_id),
        "actor_id": _uuid_text(event.actor_id),
        "process_id": _uuid_text(event.process_id),
        "thread_id": _uuid_text(event.thread_id),
        "branch_id": str(event.branch_id),
        "projection_hash": event.projection_hash,
        "commit_id": str(event.commit_id),
        "projection_experience_graph_identity_id": _uuid_text(
            event.projection_experience_graph_identity_id
        ),
        "object_projection_graph_identity_id": _uuid_text(
            event.object_projection_graph_identity_id
        ),
        "object_instance_graph_identity_id": _uuid_text(
            event.object_instance_graph_identity_id
        ),
        "object_instance_graph_branch_id": _uuid_text(
            event.object_instance_graph_branch_id
        ),
        "object_instance_graph_commit_id": _uuid_text(
            event.object_instance_graph_commit_id
        ),
        "graph_hash_post": event.graph_hash_post,
        "operation_label": event.operation_label,
        "narration_lines": list(event.narration_lines),
        "semantics": dict(event.semantics),
        "evidence": dict(event.evidence),
    }


def _uuid_text(value: UUID | None) -> str | None:
    return str(value) if value is not None else None


__all__ = [
    "EXPERIENCE_SESSION_NARRATOR_FEATURE",
    "ExperienceSessionNarrationCommitReader",
    "ExperienceSessionNarrationEvent",
    "ExperienceSessionNarrationEventBuffer",
    "ExperienceSessionNarrationEventSink",
    "ExperienceSessionNarrationReceiptSource",
    "ExperienceSessionNarrationSemanticsBuilder",
    "ExperienceSessionNarratorFeatureAdapter",
    "ExperienceSessionNarratorHealth",
    "experience_session_narration_event_payload",
]
