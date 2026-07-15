from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import inspect
from uuid import UUID, uuid4

import pytest

from aware_environment_sdk import EnvironmentSdkCommitReceiptSource
from aware_environment_service_dto.environment.environment import (
    LaneCommitReceiptNotification,
)
from aware_meta.graph.instance.commit.contract import LaneHeadCommitReceipt
from aware_meta.receipts.lane_commit_receipt_bus import (
    LaneCommitReceiptBus as MetaLaneCommitReceiptBus,
)
from aware_meta.receipts.lane_head_receipt_relay import (
    LaneHeadReceiptRelay,
)


class _FakeEnvironmentSdkClient:
    def __init__(self) -> None:
        self.registered_count = 0
        self.unsubscribe_count = 0
        self.subscription_filters: list[tuple[UUID | None, str | None]] = []
        self._watchers: list[
            Callable[
                [LaneCommitReceiptNotification],
                Awaitable[None] | None,
            ]
        ] = []
        self._subscribed = asyncio.Event()

    async def ensure_interface_session_registered(self) -> None:
        self.registered_count += 1

    def subscribe_lane_commit_receipts(
        self,
        *,
        watcher: Callable[
            [LaneCommitReceiptNotification],
            Awaitable[None] | None,
        ],
        branch_id: UUID | None = None,
        projection_hash: str | None = None,
    ) -> Callable[[], None]:
        self.subscription_filters.append((branch_id, projection_hash))
        self._watchers.append(watcher)
        self._subscribed.set()

        def _unsubscribe() -> None:
            self.unsubscribe_count += 1
            if watcher in self._watchers:
                self._watchers.remove(watcher)

        return _unsubscribe

    async def wait_subscribed(self) -> None:
        await self._subscribed.wait()

    async def emit(self, receipt: LaneCommitReceiptNotification) -> None:
        for watcher in tuple(self._watchers):
            result = watcher(receipt)
            if inspect.isawaitable(result):
                await result


@pytest.mark.asyncio
async def test_environment_sdk_source_streams_required_oig_commit_receipts() -> None:
    branch_id = uuid4()
    object_projection_graph_id = uuid4()
    object_projection_graph_identity_id = uuid4()
    object_instance_graph_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    object_instance_graph_branch_id = uuid4()
    receipt = LaneCommitReceiptNotification(
        actor_id=uuid4(),
        environment_id=uuid4(),
        branch_id=branch_id,
        projection_hash="sha256:test",
        commit_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
        object_projection_graph_id=object_projection_graph_id,
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
    )
    client = _FakeEnvironmentSdkClient()
    source = EnvironmentSdkCommitReceiptSource(client=client)

    async def _collect_one() -> LaneCommitReceiptNotification:
        stream = source.stream_commit_receipts(subscriber_id="identity.test")
        try:
            return await anext(stream)
        finally:
            await stream.aclose()

    task = asyncio.create_task(_collect_one())
    await asyncio.wait_for(client.wait_subscribed(), timeout=1.0)
    await client.emit(receipt)

    delivered = await asyncio.wait_for(task, timeout=1.0)
    assert delivered == receipt
    assert delivered.object_projection_graph_id == object_projection_graph_id
    assert (
        delivered.object_projection_graph_identity_id
        == object_projection_graph_identity_id
    )
    assert delivered.object_instance_graph_id == object_instance_graph_id
    assert (
        delivered.object_instance_graph_identity_id == object_instance_graph_identity_id
    )
    assert delivered.object_instance_graph_branch_id == object_instance_graph_branch_id
    assert client.registered_count == 1
    assert client.unsubscribe_count == 1
    assert client.subscription_filters == [(None, None)]


@pytest.mark.asyncio
async def test_environment_sdk_source_filters_until_resume_commit() -> None:
    branch_id = uuid4()
    projection_hash = "sha256:test"
    skipped = LaneCommitReceiptNotification(
        actor_id=uuid4(),
        environment_id=uuid4(),
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
    )
    resume = LaneCommitReceiptNotification(
        actor_id=uuid4(),
        environment_id=uuid4(),
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
    )
    emitted = LaneCommitReceiptNotification(
        actor_id=uuid4(),
        environment_id=uuid4(),
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
    )
    other_lane = LaneCommitReceiptNotification(
        actor_id=uuid4(),
        environment_id=uuid4(),
        branch_id=uuid4(),
        projection_hash=projection_hash,
        commit_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
    )
    client = _FakeEnvironmentSdkClient()
    source = EnvironmentSdkCommitReceiptSource(
        client=client,
        branch_id=branch_id,
        projection_hash=projection_hash,
    )

    async def _collect_one() -> LaneCommitReceiptNotification:
        stream = source.stream_commit_receipts(
            subscriber_id="identity.test",
            resume_after_commit_id=resume.commit_id,
        )
        try:
            return await anext(stream)
        finally:
            await stream.aclose()

    task = asyncio.create_task(_collect_one())
    await asyncio.wait_for(client.wait_subscribed(), timeout=1.0)
    await client.emit(skipped)
    await client.emit(other_lane)
    await client.emit(resume)
    await client.emit(emitted)

    assert await asyncio.wait_for(task, timeout=1.0) == emitted
    assert client.subscription_filters == [(branch_id, projection_hash)]


def test_lane_head_receipt_relay_dispatches_enriched_identity_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bus = MetaLaneCommitReceiptBus()
    monkeypatch.setattr(MetaLaneCommitReceiptBus, "_instance", bus)
    dispatched: list[LaneCommitReceiptNotification] = []
    unsubscribe = bus.subscribe_all(watcher=dispatched.append)

    object_projection_graph_id = uuid4()
    object_projection_graph_identity_id = uuid4()
    object_instance_graph_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    object_instance_graph_branch_id = uuid4()
    branch_id = uuid4()
    projection_hash = "sha256:test"
    relay = LaneHeadReceiptRelay()

    try:
        relay._on_lane_head_receipt(
            LaneHeadCommitReceipt(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=uuid4(),
                created_at_unix_ms=1,
                graph_hash_post="a" * 64,
                object_instance_graph_id=object_instance_graph_id,
                object_instance_graph_commit_id=uuid4(),
                object_projection_graph_id=object_projection_graph_id,
                object_projection_graph_identity_id=object_projection_graph_identity_id,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_instance_graph_branch_id=object_instance_graph_branch_id,
                root_object_id=uuid4(),
            )
        )
    finally:
        unsubscribe()

    assert len(dispatched) == 1
    notification = dispatched[0]
    assert notification.branch_id == branch_id
    assert notification.projection_hash == projection_hash
    assert notification.object_projection_graph_id == object_projection_graph_id
    assert (
        notification.object_projection_graph_identity_id
        == object_projection_graph_identity_id
    )
    assert notification.object_instance_graph_id == object_instance_graph_id
    assert (
        notification.object_instance_graph_identity_id
        == object_instance_graph_identity_id
    )
    assert (
        notification.object_instance_graph_branch_id == object_instance_graph_branch_id
    )
