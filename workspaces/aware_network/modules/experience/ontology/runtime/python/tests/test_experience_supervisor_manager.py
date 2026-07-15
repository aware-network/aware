from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from aware_experience.supervisor import (
    ExperienceSessionFeatureLease,
    ExperienceSessionFeatureRunResult,
    ExperienceSessionScope,
    ExperienceSupervisorManager,
    REACTIVITY_TRANSITION_DISPATCH_FEATURE,
    build_experience_session_feature_lease_key,
)


class _BlockingFeatureAdapter:
    feature_key = REACTIVITY_TRANSITION_DISPATCH_FEATURE

    def __init__(self) -> None:
        self.calls: list[ExperienceSessionFeatureLease] = []
        self.release_calls: list[ExperienceSessionFeatureLease] = []
        self.release_events: dict[str, asyncio.Event] = {}

    async def run(
        self,
        lease: ExperienceSessionFeatureLease,
    ) -> ExperienceSessionFeatureRunResult:
        self.calls.append(lease)
        release_event = asyncio.Event()
        self.release_events[lease.lease_key] = release_event
        await release_event.wait()
        return ExperienceSessionFeatureRunResult(
            status="completed",
            info=f"completed {lease.lease_key}",
        )

    async def release(self, lease: ExperienceSessionFeatureLease) -> None:
        self.release_calls.append(lease)
        event = self.release_events.get(lease.lease_key)
        if event is not None:
            event.set()


class _FailingFeatureAdapter(_BlockingFeatureAdapter):
    async def run(
        self,
        lease: ExperienceSessionFeatureLease,
    ) -> ExperienceSessionFeatureRunResult:
        self.calls.append(lease)
        if lease.session_scope.profile_key == "bad":
            raise RuntimeError("session feature failed")
        release_event = asyncio.Event()
        self.release_events[lease.lease_key] = release_event
        await release_event.wait()
        return ExperienceSessionFeatureRunResult(status="completed")


def _scope(*, profile_key: str = "os.default") -> ExperienceSessionScope:
    return ExperienceSessionScope(
        experience_name="aware_control_identity",
        profile_key=profile_key,
        environment_id=uuid4(),
        environment_session_id=uuid4(),
        actor_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="projection.hash",
        workspace_session_id=f"workspace-session-{profile_key}",
    )


@pytest.mark.asyncio
async def test_supervisor_manager_ensures_feature_idempotently_and_releases_only_target() -> (
    None
):
    adapter = _BlockingFeatureAdapter()
    manager = ExperienceSupervisorManager(
        feature_adapters={REACTIVITY_TRANSITION_DISPATCH_FEATURE: adapter},
    )
    first_scope = _scope(profile_key="one")
    second_scope = _scope(profile_key="two")

    first = await manager.ensure_feature(
        session_scope=first_scope,
        feature_key=REACTIVITY_TRANSITION_DISPATCH_FEATURE,
    )
    duplicate = await manager.ensure_feature(
        session_scope=first_scope,
        feature_key=REACTIVITY_TRANSITION_DISPATCH_FEATURE,
    )
    second = await manager.ensure_feature(
        session_scope=second_scope,
        feature_key=REACTIVITY_TRANSITION_DISPATCH_FEATURE,
    )
    await asyncio.sleep(0)

    assert first.lease_key == duplicate.lease_key
    assert first.revision == duplicate.revision
    assert second.lease_key != first.lease_key
    assert len(adapter.calls) == 2

    released = await manager.release_feature(
        session_scope=first_scope,
        feature_key=REACTIVITY_TRANSITION_DISPATCH_FEATURE,
    )
    assert released is not None
    assert released.desired_state == "disabled"
    assert released.worker_status == "released"

    second_snapshot = await manager.get_feature_snapshot(
        session_scope=second_scope,
        feature_key=REACTIVITY_TRANSITION_DISPATCH_FEATURE,
    )
    assert second_snapshot is not None
    assert second_snapshot.desired_state == "enabled"
    assert second_snapshot.worker_status == "running"

    snapshot = await manager.get_snapshot()
    assert snapshot.session_count == 2
    assert snapshot.feature_lease_count == 2
    assert snapshot.status == "running"

    await manager.release_feature(
        session_scope=second_scope,
        feature_key=REACTIVITY_TRANSITION_DISPATCH_FEATURE,
    )


@pytest.mark.asyncio
async def test_supervisor_manager_marks_only_failed_session_feature_unhealthy() -> None:
    adapter = _FailingFeatureAdapter()
    manager = ExperienceSupervisorManager(
        feature_adapters={REACTIVITY_TRANSITION_DISPATCH_FEATURE: adapter},
    )
    good_scope = _scope(profile_key="good")
    bad_scope = _scope(profile_key="bad")

    await manager.ensure_feature(
        session_scope=good_scope,
        feature_key=REACTIVITY_TRANSITION_DISPATCH_FEATURE,
    )
    await manager.ensure_feature(
        session_scope=bad_scope,
        feature_key=REACTIVITY_TRANSITION_DISPATCH_FEATURE,
    )
    await asyncio.sleep(0)

    snapshot = await manager.get_snapshot()
    assert snapshot.status == "degraded"

    good = await manager.get_feature_snapshot(
        session_scope=good_scope,
        feature_key=REACTIVITY_TRANSITION_DISPATCH_FEATURE,
    )
    bad = await manager.get_feature_snapshot(
        session_scope=bad_scope,
        feature_key=REACTIVITY_TRANSITION_DISPATCH_FEATURE,
    )
    assert good is not None
    assert good.worker_status == "running"
    assert bad is not None
    assert bad.worker_status == "failed"
    assert bad.last_error == "session feature failed"

    await manager.release_feature(
        session_scope=good_scope,
        feature_key=REACTIVITY_TRANSITION_DISPATCH_FEATURE,
    )


def test_supervisor_lease_key_includes_environment_session_id() -> None:
    environment_id = uuid4()
    actor_id = uuid4()
    process_id = uuid4()
    thread_id = uuid4()
    branch_id = uuid4()
    base = {
        "experience_name": "aware_control_identity",
        "profile_key": "os.default",
        "environment_id": environment_id,
        "actor_id": actor_id,
        "process_id": process_id,
        "thread_id": thread_id,
        "branch_id": branch_id,
        "projection_hash": "projection.hash",
        "workspace_session_id": "workspace-session",
    }
    first = ExperienceSessionScope(
        **base,
        environment_session_id=uuid4(),
    )
    second = ExperienceSessionScope(
        **base,
        environment_session_id=uuid4(),
    )

    assert build_experience_session_feature_lease_key(
        session_scope=first,
        feature_key=REACTIVITY_TRANSITION_DISPATCH_FEATURE,
    ) != build_experience_session_feature_lease_key(
        session_scope=second,
        feature_key=REACTIVITY_TRANSITION_DISPATCH_FEATURE,
    )
