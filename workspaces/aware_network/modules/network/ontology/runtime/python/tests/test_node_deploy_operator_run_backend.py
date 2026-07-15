from __future__ import annotations

import json
from pathlib import Path

import pytest

from aware_network.node_deploy.backends.operator_run import (
    OperatorRunNode,
    OperatorRunNodeDeployBackend,
)
from aware_network.node_deploy.dto import (
    DescribeNodeRuntimeRequest,
    EnsureNodeRuntimeStartedRequest,
    NodeDeployRuntimePhase,
    NodeDeployTarget,
    RestartNodeRuntimeRequest,
    StopNodeRuntimeRequest,
    StreamNodeRuntimeEventsRequest,
    TailNodeRuntimeLogsRequest,
)
from aware_network.node_deploy.errors import NodeDeploySupervisorError


class FakeProcessManager:
    def __init__(self) -> None:
        self.next_pid = 4200
        self.running: set[int] = set()
        self.launches: list[tuple[Path, Path, int]] = []
        self.stops: list[tuple[int, bool]] = []

    async def launch(
        self,
        *,
        command_file_path: Path,
        cwd: Path,
    ) -> int:
        pid = self.next_pid
        self.next_pid += 1
        self.running.add(pid)
        self.launches.append((command_file_path, cwd, pid))
        return pid

    def is_running(self, *, pid: int) -> bool:
        return pid in self.running

    async def stop(
        self,
        *,
        pid: int,
        force: bool,
        timeout_s: float,
    ) -> None:
        _ = timeout_s
        self.stops.append((pid, force))
        self.running.discard(pid)


class FakeHealthProbe:
    def __init__(self, *, ready: bool = False) -> None:
        self.ready = ready
        self.calls: list[OperatorRunNode] = []

    def __call__(self, *, node: OperatorRunNode, timeout_s: float) -> bool:
        _ = timeout_s
        self.calls.append(node)
        return self.ready


class RecordingEventSink:
    def __init__(self) -> None:
        self.events = []

    async def publish_event(self, *, event) -> None:  # noqa: ANN001
        self.events.append(event)


@pytest.mark.asyncio
async def test_operator_run_backend_starts_node_and_writes_receipts(
    tmp_path: Path,
) -> None:
    manifest_path = _write_operator_run_manifest(tmp_path=tmp_path)
    process_manager = FakeProcessManager()
    health_probe = FakeHealthProbe(ready=False)
    backend = OperatorRunNodeDeployBackend(
        manifest_path=manifest_path,
        process_manager=process_manager,
        health_probe=health_probe,
    )
    sink = RecordingEventSink()

    snapshot = await backend.ensure_runtime_started(
        request=EnsureNodeRuntimeStartedRequest(wait_for_ready=False),
        event_sink=sink,
    )

    command_path = tmp_path / "commands" / "kernel-node.sh"
    assert snapshot.phase == NodeDeployRuntimePhase.waiting_node
    assert snapshot.backend_kind == "operator-run"
    assert snapshot.is_active is True
    assert snapshot.is_healthy is False
    assert snapshot.target is not None
    assert snapshot.target.target_key == "kernel-node"
    assert snapshot.node_base_url == "http://127.0.0.1:8911"
    assert process_manager.launches == [(command_path, tmp_path, 4200)]
    assert len(sink.events) == 1
    assert sink.events[0].kind == "runtime_status"

    pid_path = tmp_path / "node-deploy" / "pids" / "kernel-node.pid"
    status_path = tmp_path / "node-deploy" / "status" / "kernel-node.json"
    assert pid_path.read_text(encoding="utf-8") == "4200\n"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    assert status["version"] == "aware.node_deploy.operator_run.status.v1"
    assert status["status"] == "running"
    assert status["pid"] == 4200
    assert status["command_file_path"] == command_path.as_posix()

    log_path = tmp_path / "logs" / "kernel-node.log"
    log_path.write_text("first\nsecond\n", encoding="utf-8")

    tail = await backend.tail_runtime_logs(request=TailNodeRuntimeLogsRequest(line_count=1))

    assert tail.log_lines == ("second",)
    assert tail.runtime_status is not None
    assert tail.runtime_status.recent_log_lines[-1] == "second"


@pytest.mark.asyncio
async def test_operator_run_backend_starts_from_node_run_manifest(
    tmp_path: Path,
) -> None:
    manifest_path = _write_node_run_manifest(tmp_path=tmp_path)
    process_manager = FakeProcessManager()
    backend = OperatorRunNodeDeployBackend(
        manifest_path=manifest_path,
        process_manager=process_manager,
        health_probe=FakeHealthProbe(ready=False),
    )

    snapshot = await backend.ensure_runtime_started(
        request=EnsureNodeRuntimeStartedRequest(wait_for_ready=False),
    )

    command_path = tmp_path / "commands" / "kernel-node.sh"
    assert snapshot.phase == NodeDeployRuntimePhase.waiting_node
    assert snapshot.backend_kind == "operator-run"
    assert snapshot.target is not None
    assert snapshot.target.target_key == "kernel-node"
    assert snapshot.node_base_url == "http://node.local:8917"
    assert snapshot.node_websocket_path == "/node/ws"
    assert snapshot.target.node_base_url == "http://node.local:8917"
    assert snapshot.target.node_websocket_path == "/node/ws"
    assert process_manager.launches == [(command_path, tmp_path, 4200)]


@pytest.mark.asyncio
async def test_operator_run_backend_describes_ready_and_streams_history(
    tmp_path: Path,
) -> None:
    manifest_path = _write_operator_run_manifest(tmp_path=tmp_path)
    process_manager = FakeProcessManager()
    health_probe = FakeHealthProbe(ready=True)
    backend = OperatorRunNodeDeployBackend(
        manifest_path=manifest_path,
        process_manager=process_manager,
        health_probe=health_probe,
    )
    await backend.ensure_runtime_started(
        request=EnsureNodeRuntimeStartedRequest(wait_for_ready=False),
    )
    (tmp_path / "logs" / "kernel-node.log").write_text(
        "booting\nready\n",
        encoding="utf-8",
    )

    snapshot = await backend.describe_runtime(request=DescribeNodeRuntimeRequest())
    sink = RecordingEventSink()
    stream_snapshot = await backend.stream_runtime_events(
        request=StreamNodeRuntimeEventsRequest(include_history=True),
        event_sink=sink,
    )

    assert snapshot.phase == NodeDeployRuntimePhase.ready
    assert snapshot.is_healthy is True
    assert stream_snapshot.phase == NodeDeployRuntimePhase.ready
    assert [event.kind for event in sink.events] == [
        "runtime_status",
        "runtime_log",
        "runtime_log",
    ]
    assert sink.events[-1].log_line == "ready"


@pytest.mark.asyncio
async def test_operator_run_backend_stops_and_restarts_node(
    tmp_path: Path,
) -> None:
    manifest_path = _write_operator_run_manifest(tmp_path=tmp_path)
    process_manager = FakeProcessManager()
    backend = OperatorRunNodeDeployBackend(
        manifest_path=manifest_path,
        process_manager=process_manager,
        health_probe=FakeHealthProbe(ready=False),
    )
    await backend.ensure_runtime_started(
        request=EnsureNodeRuntimeStartedRequest(wait_for_ready=False),
    )

    stopped = await backend.stop_runtime(request=StopNodeRuntimeRequest(force=False))

    assert stopped.phase == NodeDeployRuntimePhase.idle
    assert process_manager.stops == [(4200, False)]
    assert not (tmp_path / "node-deploy" / "pids" / "kernel-node.pid").exists()
    status = json.loads((tmp_path / "node-deploy" / "status" / "kernel-node.json").read_text(encoding="utf-8"))
    assert status["status"] == "stopped"

    await backend.ensure_runtime_started(
        request=EnsureNodeRuntimeStartedRequest(wait_for_ready=False),
    )
    restarted = await backend.restart_runtime(request=RestartNodeRuntimeRequest(wait_for_ready=False))

    assert restarted.phase == NodeDeployRuntimePhase.waiting_node
    assert process_manager.launches[-1][2] == 4202
    assert process_manager.stops[-1] == (4201, True)


@pytest.mark.asyncio
async def test_operator_run_backend_requires_target_for_multi_node_manifest(
    tmp_path: Path,
) -> None:
    manifest_path = _write_operator_run_manifest(
        tmp_path=tmp_path,
        nodes=("kernel-env-node", "kernel-services-node"),
    )
    backend = OperatorRunNodeDeployBackend(
        manifest_path=manifest_path,
        process_manager=FakeProcessManager(),
        health_probe=FakeHealthProbe(),
    )

    with pytest.raises(NodeDeploySupervisorError, match="multiple nodes"):
        await backend.describe_runtime(request=DescribeNodeRuntimeRequest())

    snapshot = await backend.describe_runtime(
        request=DescribeNodeRuntimeRequest(target=NodeDeployTarget(target_key="kernel-services-node"))
    )

    assert snapshot.target is not None
    assert snapshot.target.target_key == "kernel-services-node"
    assert [item.target_id for item in snapshot.target_statuses] == [
        "kernel-env-node",
        "kernel-services-node",
    ]


def _write_operator_run_manifest(
    *,
    tmp_path: Path,
    nodes: tuple[str, ...] = ("kernel-node",),
) -> Path:
    (tmp_path / "commands").mkdir()
    (tmp_path / "env").mkdir()
    (tmp_path / "logs").mkdir()
    payload_nodes = []
    for index, node_package in enumerate(nodes):
        port = 8911 + index
        command_path = tmp_path / "commands" / f"{node_package}.sh"
        env_path = tmp_path / "env" / f"{node_package}.env"
        log_path = tmp_path / "logs" / f"{node_package}.log"
        command_path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        env_path.write_text(f"AWARE_NODE_PORT={port}\n", encoding="utf-8")
        log_path.write_text("", encoding="utf-8")
        payload_nodes.append(
            {
                "node_package": node_package,
                "command_file_path": command_path.as_posix(),
                "env_file_path": env_path.as_posix(),
                "log_path": log_path.as_posix(),
                "host": "127.0.0.1",
                "port": port,
                "command": f"bash {command_path.as_posix()}",
                "boot_kernel": index == 0,
            }
        )
    manifest_path = tmp_path / "deployment-run.json"
    manifest_path.write_text(
        json.dumps(
            {
                "version": "aware.workspace_deployment.operator_run.v1",
                "run_dir": tmp_path.as_posix(),
                "manifest_path": manifest_path.as_posix(),
                "nodes": payload_nodes,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _write_node_run_manifest(*, tmp_path: Path) -> Path:
    (tmp_path / "commands").mkdir()
    (tmp_path / "env").mkdir()
    (tmp_path / "logs").mkdir()
    command_path = tmp_path / "commands" / "kernel-node.sh"
    env_path = tmp_path / "env" / "kernel-node.env"
    log_path = tmp_path / "logs" / "kernel-node.log"
    command_path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    env_path.write_text("AWARE_NODE_PORT=8917\n", encoding="utf-8")
    log_path.write_text("", encoding="utf-8")
    manifest_path = tmp_path / "node-run-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "version": "aware.node.run_manifest.v1",
                "node_package": "kernel-node",
                "host": "127.0.0.1",
                "port": 8917,
                "node_base_url": "http://node.local:8917",
                "node_websocket_path": "/node/ws",
                "run_dir": ".",
                "command_file_path": "commands/kernel-node.sh",
                "env_file_path": "env/kernel-node.env",
                "log_path": "logs/kernel-node.log",
                "environment_service_port": 9917,
                "environment_api_endpoint": "http://127.0.0.1:9917",
                "provenance": {
                    "source_kind": "local_manifest",
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest_path
