from __future__ import annotations

from typing import cast

import pytest

from aware_network.node_deploy.models import (
    NodeDeployLogTail,
    NodeDeployRuntimeSnapshot,
    build_log_event,
)
from aware_network.node_deploy.supervisor import DefaultNodeDeploySupervisor
from aware_network.node_deploy.dto import (
    DescribeNodeRuntimeRequest,
    EnsureNodeRuntimeStartedRequest,
    NodeDeployRuntimePhase,
    NodeDeployTarget,
    StreamNodeRuntimeEventsResponse,
    StreamNodeRuntimeEventsRequest,
    TailNodeRuntimeLogsResponse,
    TailNodeRuntimeLogsRequest,
)


class RecordingEventSink:
    def __init__(self) -> None:
        self.events = []

    async def publish_event(self, *, event) -> None:
        self.events.append(event)


class StubNodeDeployBackend:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []
        self.snapshot = NodeDeployRuntimeSnapshot(
            target=NodeDeployTarget(
                target_key="default",
                node_base_url="http://127.0.0.1:8000",
                node_websocket_path="/interface/network_node",
            ),
            phase=NodeDeployRuntimePhase.ready,
            backend_kind="repo-dev",
            is_active=True,
            is_healthy=True,
            summary="ready",
        )

    async def describe_runtime(self, *, request: DescribeNodeRuntimeRequest):
        self.calls.append(("describe_runtime", request))
        return self.snapshot

    async def ensure_runtime_started(
        self,
        *,
        request: EnsureNodeRuntimeStartedRequest,
        event_sink=None,
    ):
        self.calls.append(("ensure_runtime_started", request))
        if event_sink is not None:
            await event_sink.publish_event(
                event=build_log_event(
                    log_line="booted",
                    runtime_status=self.snapshot,
                    actor_id=request.actor_id,
                    operation=request.operation,
                )
            )
        return self.snapshot

    async def restart_runtime(self, *, request, event_sink=None):
        self.calls.append(("restart_runtime", request))
        return self.snapshot

    async def stop_runtime(self, *, request, event_sink=None):
        self.calls.append(("stop_runtime", request))
        return self.snapshot

    async def tail_runtime_logs(self, *, request: TailNodeRuntimeLogsRequest):
        self.calls.append(("tail_runtime_logs", request))
        return NodeDeployLogTail(
            log_lines=("line-1", "line-2"),
            runtime_status=self.snapshot,
        )

    async def stream_runtime_events(self, *, request, event_sink):
        self.calls.append(("stream_runtime_events", request))
        await event_sink.publish_event(
            event=build_log_event(
                log_line="progress",
                runtime_status=self.snapshot,
                actor_id=request.actor_id,
                operation=request.operation,
            )
        )
        return self.snapshot


@pytest.mark.asyncio
async def test_supervisor_handles_ensure_started_request() -> None:
    backend = StubNodeDeployBackend()
    sink = RecordingEventSink()
    supervisor = DefaultNodeDeploySupervisor(backend=backend)

    response = await supervisor.handle_request(
        request=EnsureNodeRuntimeStartedRequest(wait_for_ready=True),
        event_sink=sink,
    )

    assert response.status == "succeeded"
    assert response.runtime_status is not None
    assert response.runtime_status.phase == NodeDeployRuntimePhase.ready
    assert backend.calls[0][0] == "ensure_runtime_started"
    assert len(sink.events) == 1
    assert sink.events[0].kind == "runtime_log"


@pytest.mark.asyncio
async def test_supervisor_handles_log_tail_request() -> None:
    backend = StubNodeDeployBackend()
    supervisor = DefaultNodeDeploySupervisor(backend=backend)

    response = await supervisor.handle_request(
        request=TailNodeRuntimeLogsRequest(line_count=2),
    )
    response = cast(TailNodeRuntimeLogsResponse, response)

    assert response.status == "succeeded"
    assert response.log_lines == ["line-1", "line-2"]
    assert response.runtime_status is not None
    assert response.runtime_status.backend_kind == "repo-dev"


@pytest.mark.asyncio
async def test_supervisor_requires_event_sink_for_stream_request() -> None:
    backend = StubNodeDeployBackend()
    supervisor = DefaultNodeDeploySupervisor(backend=backend)

    response = await supervisor.handle_request(
        request=StreamNodeRuntimeEventsRequest(include_history=True),
    )
    response = cast(StreamNodeRuntimeEventsResponse, response)

    assert response.status == "failed"
    assert response.error == "stream_node_runtime_events requires an event sink"
    assert response.stream_open is False


@pytest.mark.asyncio
async def test_supervisor_stream_request_forwards_events() -> None:
    backend = StubNodeDeployBackend()
    sink = RecordingEventSink()
    supervisor = DefaultNodeDeploySupervisor(backend=backend)

    response = await supervisor.handle_request(
        request=StreamNodeRuntimeEventsRequest(include_history=True),
        event_sink=sink,
    )
    response = cast(StreamNodeRuntimeEventsResponse, response)

    assert response.status == "succeeded"
    assert response.stream_open is True
    assert [event.kind for event in sink.events] == ["runtime_log"]
