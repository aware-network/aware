from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from uuid import UUID, uuid4

import pytest

from aware_environment_service_dto.environment.environment import (
    LaneCommitReceiptNotification,
)
from aware_experience.supervisor import (
    EXPERIENCE_SESSION_NARRATOR_FEATURE,
    ExperienceSessionFeatureLease,
    ExperienceSessionNarrationEventBuffer,
    ExperienceSessionNarratorFeatureAdapter,
    ExperienceSessionScope,
)


class _ReceiptSource:
    def __init__(self, receipts: tuple[LaneCommitReceiptNotification, ...]) -> None:
        self.receipts = receipts
        self.calls: list[dict[str, object]] = []

    async def stream_commit_receipts(
        self,
        *,
        subscriber_id: str,
        resume_after_commit_id: UUID | None = None,
    ) -> AsyncIterator[LaneCommitReceiptNotification]:
        self.calls.append(
            {
                "subscriber_id": subscriber_id,
                "resume_after_commit_id": resume_after_commit_id,
            }
        )
        for receipt in self.receipts:
            yield receipt


class _CommitReader:
    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.calls: list[dict[str, object]] = []

    async def get_object_instance_graph_commit(self, **kwargs: object) -> object:
        self.calls.append(dict(kwargs))
        return self.payload


@pytest.mark.asyncio
async def test_experience_session_narrator_publishes_semantic_commit_event() -> None:
    branch_id = uuid4()
    projection_hash = "sha256:experience-session-narrator"
    commit_id = uuid4()
    actor_id = uuid4()
    environment_id = uuid4()
    process_id = uuid4()
    thread_id = uuid4()
    projection_experience_graph_identity_id = uuid4()
    object_projection_graph_identity_id = uuid4()
    object_instance_graph_branch_id = uuid4()
    object_instance_graph_commit_id = uuid4()
    receipt = LaneCommitReceiptNotification(
        actor_id=actor_id,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        graph_hash_post="graph-after",
        operation_label="Task.update_status",
    )
    source = _ReceiptSource((receipt,))
    reader = _CommitReader(payload={"commit": {"id": str(commit_id)}})
    sink = ExperienceSessionNarrationEventBuffer()

    async def _semantics(
        lease: ExperienceSessionFeatureLease,
        received_receipt: LaneCommitReceiptNotification,
        commit_payload: object,
    ) -> Mapping[str, object]:
        assert lease.feature_key == EXPERIENCE_SESSION_NARRATOR_FEATURE
        assert received_receipt is receipt
        assert commit_payload == {"commit": {"id": str(commit_id)}}
        return {
            "descriptor_count": 1,
            "narration_lines": ['Task.status = "done"'],
        }

    lease = ExperienceSessionFeatureLease(
        lease_key="lease-1",
        session_scope=ExperienceSessionScope(
            experience_name="my_home",
            profile_key="default",
            environment_id=environment_id,
            actor_id=actor_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
        ),
        feature_key=EXPERIENCE_SESSION_NARRATOR_FEATURE,
        config={
            "max_events": 1,
            "handoff_scope": {
                "projection_experience_graph_identity_id": str(
                    projection_experience_graph_identity_id
                ),
                "object_projection_graph_identity_id": str(
                    object_projection_graph_identity_id
                ),
                "object_instance_graph_branch_id": str(object_instance_graph_branch_id),
            },
        },
    )
    adapter = ExperienceSessionNarratorFeatureAdapter(
        receipt_source_for_lease=lambda _: source,
        commit_reader_for_lease=lambda _: reader,
        semantic_payload_for_commit=_semantics,
        event_sink=sink,
    )

    result = await adapter.run(lease)

    assert result.status == "completed"
    assert result.health is not None
    assert getattr(result.health, "event_count") == 1
    assert source.calls == [
        {
            "subscriber_id": "experience.narrator.lease-1",
            "resume_after_commit_id": None,
        }
    ]
    assert reader.calls == [
        {
            "commit_id": commit_id,
            "actor_id": actor_id,
            "environment_id": environment_id,
            "process_id": process_id,
            "thread_id": thread_id,
            "branch_id": branch_id,
            "projection_hash": projection_hash,
        }
    ]
    assert len(sink.events) == 1
    event = sink.events[0]
    assert event.experience_name == "my_home"
    assert event.branch_id == branch_id
    assert event.projection_hash == projection_hash
    assert event.commit_id == commit_id
    assert event.object_instance_graph_commit_id == object_instance_graph_commit_id
    assert event.projection_experience_graph_identity_id == (
        projection_experience_graph_identity_id
    )
    assert (
        event.object_projection_graph_identity_id == object_projection_graph_identity_id
    )
    assert event.object_instance_graph_branch_id == object_instance_graph_branch_id
    assert event.narration_lines == ('Task.status = "done"',)
    assert dict(event.semantics)["descriptor_count"] == 1


@pytest.mark.asyncio
async def test_experience_session_narrator_fails_without_lane_scope() -> None:
    adapter = ExperienceSessionNarratorFeatureAdapter(
        receipt_source_for_lease=lambda _: None,
        commit_reader_for_lease=lambda _: None,
    )
    lease = ExperienceSessionFeatureLease(
        lease_key="lease-1",
        session_scope=ExperienceSessionScope(
            experience_name="my_home",
            projection_hash="sha256:missing-branch",
        ),
        feature_key=EXPERIENCE_SESSION_NARRATOR_FEATURE,
    )

    result = await adapter.run(lease)

    assert result.status == "failed"
    assert result.last_error == (
        "Experience session narrator requires branch_id and projection_hash."
    )
