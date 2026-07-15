from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
import os
from pathlib import Path
import signal
from time import monotonic
from typing import Protocol, cast
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import NAMESPACE_URL, UUID, uuid5

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
from aware_network.node_deploy.backends.base import NodeDeployBackend
from aware_network.node_deploy.contracts import NodeDeployEventSink
from aware_network.node_deploy.errors import NodeDeploySupervisorError
from aware_network.node_deploy.models import (
    NodeDeployLogTail,
    NodeDeployRuntimeSnapshot,
    NodeDeployTargetStatusSnapshot,
    build_log_event,
    build_status_event,
    build_terminal_event,
    utc_now_iso,
)

_MANIFEST_VERSION = "aware.workspace_deployment.operator_run.v1"
_NODE_RUN_MANIFEST_VERSION = "aware.node.run_manifest.v1"
_STATUS_RECEIPT_VERSION = "aware.node_deploy.operator_run.status.v1"
_BACKEND_KIND = "operator-run"
_DEFAULT_NODE_WEBSOCKET_PATH = "/interface/network_node"
_DEFAULT_READY_TIMEOUT_S = 600.0
_DEFAULT_HEALTH_TIMEOUT_S = 0.5
_PROCESS_STOP_TIMEOUT_S = 10.0


class OperatorRunProcessManager(Protocol):
    async def launch(
        self,
        *,
        command_file_path: Path,
        cwd: Path,
    ) -> int: ...

    def is_running(self, *, pid: int) -> bool: ...

    async def stop(
        self,
        *,
        pid: int,
        force: bool,
        timeout_s: float,
    ) -> None: ...


class OperatorRunHealthProbe(Protocol):
    def __call__(
        self,
        *,
        node: "OperatorRunNode",
        timeout_s: float,
    ) -> bool: ...


@dataclass(frozen=True, slots=True)
class OperatorRunNode:
    manifest_path: Path
    run_dir: Path
    node_package: str
    command_file_path: Path
    env_file_path: Path
    log_path: Path
    host: str
    port: int
    command: str | None = None
    boot_kernel: bool = False
    node_id: UUID | None = None
    node_info_path: Path | None = None
    deployment_payload_path: Path | None = None
    node_host_root: Path | None = None
    python_project_path: Path | None = None
    python_execution_closure_manifest_path: Path | None = None
    environment_service_port: int | None = None
    environment_api_endpoint: str | None = None
    node_base_url_override: str | None = None
    node_websocket_path_override: str | None = None
    runtime_config_status: str | None = None
    runtime_config_missing: tuple[str, ...] = ()

    @property
    def target_id(self) -> UUID:
        if self.node_id is not None:
            return self.node_id
        return uuid5(
            NAMESPACE_URL,
            f"aware-operator-run:{self.manifest_path}:{self.node_package}",
        )

    @property
    def node_base_url(self) -> str:
        if self.node_base_url_override:
            return self.node_base_url_override
        info = _read_node_info(path=self.node_info_path)
        value = info.get("http_base_url")
        if isinstance(value, str) and value.strip():
            return value.strip()
        return f"http://{self.host}:{self.port}"

    @property
    def node_websocket_path(self) -> str:
        if self.node_websocket_path_override:
            return self.node_websocket_path_override
        info = _read_node_info(path=self.node_info_path)
        value = info.get("ws_interface_to_node_path")
        if isinstance(value, str) and value.strip():
            return value.strip()
        return _DEFAULT_NODE_WEBSOCKET_PATH

    def to_target(self) -> NodeDeployTarget:
        return NodeDeployTarget(
            target_id=self.target_id,
            target_key=self.node_package,
            display_name=self.node_package,
            node_base_url=self.node_base_url,
            node_websocket_path=self.node_websocket_path,
        )


@dataclass(frozen=True, slots=True)
class _OperatorRunManifest:
    manifest_path: Path
    run_dir: Path
    nodes: tuple[OperatorRunNode, ...]


@dataclass(frozen=True, slots=True)
class _NodeRuntimeState:
    node: OperatorRunNode
    pid: int | None
    phase: NodeDeployRuntimePhase
    is_active: bool
    is_healthy: bool
    summary: str
    error: str | None = None
    status_receipt: Mapping[str, object] | None = None


class OperatorRunNodeDeployBackend(NodeDeployBackend):
    """NodeDeploy backend over a prepared WorkspaceDeployment operator run."""

    def __init__(
        self,
        *,
        manifest_path: Path,
        default_node_package: str | None = None,
        process_manager: OperatorRunProcessManager | None = None,
        health_probe: OperatorRunHealthProbe | None = None,
        ready_timeout_s: float = _DEFAULT_READY_TIMEOUT_S,
        health_probe_timeout_s: float = _DEFAULT_HEALTH_TIMEOUT_S,
    ) -> None:
        self._manifest_path = manifest_path.expanduser().resolve()
        self._default_node_package = _clean_text(default_node_package)
        self._process_manager = process_manager or _DefaultOperatorRunProcessManager()
        self._health_probe = health_probe or _default_health_probe
        self._ready_timeout_s = ready_timeout_s
        self._health_probe_timeout_s = health_probe_timeout_s

    async def describe_runtime(
        self,
        *,
        request: DescribeNodeRuntimeRequest,
    ) -> NodeDeployRuntimeSnapshot:
        manifest = self._load_manifest()
        node = self._select_node(manifest=manifest, request=request)
        return self._build_snapshot(manifest=manifest, selected_node=node)

    async def ensure_runtime_started(
        self,
        *,
        request: EnsureNodeRuntimeStartedRequest,
        event_sink: NodeDeployEventSink | None = None,
    ) -> NodeDeployRuntimeSnapshot:
        manifest = self._load_manifest()
        node = self._select_node(manifest=manifest, request=request)
        current = self._inspect_node(node=node)
        if current.is_active:
            snapshot = self._build_snapshot(
                manifest=manifest,
                selected_node=node,
                selected_state=current,
            )
            if event_sink is not None:
                await event_sink.publish_event(
                    event=build_status_event(
                        runtime_status=snapshot,
                        actor_id=request.actor_id,
                        operation=request.operation,
                        message=current.summary,
                    )
                )
            if request.wait_for_ready and not current.is_healthy:
                return await self._wait_for_ready(
                    manifest=manifest,
                    node=node,
                    request=request,
                    event_sink=event_sink,
                )
            return snapshot

        self._preflight_node(node=node)
        node.log_path.parent.mkdir(parents=True, exist_ok=True)
        pid = await self._process_manager.launch(
            command_file_path=node.command_file_path,
            cwd=manifest.run_dir,
        )
        self._write_pid(node=node, pid=pid)
        self._write_status(
            node=node,
            pid=pid,
            phase=NodeDeployRuntimePhase.waiting_node,
            status="running",
            summary="Operator-run node command started.",
        )
        state = self._inspect_node(node=node)
        snapshot = self._build_snapshot(
            manifest=manifest,
            selected_node=node,
            selected_state=state,
        )
        if event_sink is not None:
            await event_sink.publish_event(
                event=build_status_event(
                    runtime_status=snapshot,
                    actor_id=request.actor_id,
                    operation=request.operation,
                    message="Operator-run node command started.",
                )
            )
        if request.wait_for_ready:
            return await self._wait_for_ready(
                manifest=manifest,
                node=node,
                request=request,
                event_sink=event_sink,
            )
        return snapshot

    async def restart_runtime(
        self,
        *,
        request: RestartNodeRuntimeRequest,
        event_sink: NodeDeployEventSink | None = None,
    ) -> NodeDeployRuntimeSnapshot:
        manifest = self._load_manifest()
        node = self._select_node(manifest=manifest, request=request)
        await self._stop_node(node=node, force=True)
        ensure_request = EnsureNodeRuntimeStartedRequest(
            actor_id=request.actor_id,
            target=request.target,
            wait_for_ready=request.wait_for_ready,
        )
        snapshot = await self.ensure_runtime_started(
            request=ensure_request,
            event_sink=event_sink,
        )
        if event_sink is not None:
            await event_sink.publish_event(
                event=build_terminal_event(
                    terminal_status="succeeded",
                    runtime_status=snapshot,
                    actor_id=request.actor_id,
                    operation=request.operation,
                    message="Operator-run node restarted.",
                )
            )
        return snapshot

    async def stop_runtime(
        self,
        *,
        request: StopNodeRuntimeRequest,
        event_sink: NodeDeployEventSink | None = None,
    ) -> NodeDeployRuntimeSnapshot:
        manifest = self._load_manifest()
        node = self._select_node(manifest=manifest, request=request)
        await self._stop_node(node=node, force=request.force)
        snapshot = self._build_snapshot(manifest=manifest, selected_node=node)
        if event_sink is not None:
            await event_sink.publish_event(
                event=build_terminal_event(
                    terminal_status="succeeded",
                    runtime_status=snapshot,
                    actor_id=request.actor_id,
                    operation=request.operation,
                    message="Operator-run node stopped.",
                )
            )
        return snapshot

    async def tail_runtime_logs(
        self,
        *,
        request: TailNodeRuntimeLogsRequest,
    ) -> NodeDeployLogTail:
        manifest = self._load_manifest()
        node = self._select_node(manifest=manifest, request=request)
        lines = _tail_file(
            path=node.log_path,
            line_count=max(1, request.line_count),
        )
        snapshot = self._build_snapshot(manifest=manifest, selected_node=node)
        return NodeDeployLogTail(
            log_lines=lines,
            runtime_status=snapshot.with_log_lines(lines),
        )

    async def stream_runtime_events(
        self,
        *,
        request: StreamNodeRuntimeEventsRequest,
        event_sink: NodeDeployEventSink,
    ) -> NodeDeployRuntimeSnapshot:
        manifest = self._load_manifest()
        node = self._select_node(manifest=manifest, request=request)
        snapshot = self._build_snapshot(manifest=manifest, selected_node=node)
        if request.include_history:
            await event_sink.publish_event(
                event=build_status_event(
                    runtime_status=snapshot,
                    actor_id=request.actor_id,
                    operation=request.operation,
                    message=snapshot.summary,
                )
            )
            for line in _tail_file(path=node.log_path, line_count=20):
                await event_sink.publish_event(
                    event=build_log_event(
                        log_line=line,
                        runtime_status=snapshot,
                        actor_id=request.actor_id,
                        operation=request.operation,
                    )
                )
        return snapshot

    def _load_manifest(self) -> _OperatorRunManifest:
        payload = _load_json_object(path=self._manifest_path)
        version = payload.get("version")
        if version == _NODE_RUN_MANIFEST_VERSION:
            return _operator_run_manifest_from_node_run_manifest_payload(
                payload=payload,
                manifest_path=self._manifest_path,
            )
        if version != _MANIFEST_VERSION:
            raise NodeDeploySupervisorError(
                "Unsupported operator-run manifest version "
                f"{version!r}; expected {_MANIFEST_VERSION!r} or "
                f"{_NODE_RUN_MANIFEST_VERSION!r}."
            )
        run_dir = _optional_path(
            payload.get("run_dir"),
            base_dir=self._manifest_path.parent,
        )
        if run_dir is None:
            run_dir = self._manifest_path.parent
        nodes = tuple(
            _node_from_payload(
                raw_node=raw_node,
                manifest_path=self._manifest_path,
                run_dir=run_dir,
            )
            for raw_node in _manifest_nodes(payload=payload)
        )
        if not nodes:
            raise NodeDeploySupervisorError("Operator-run manifest contains no nodes.")
        return _OperatorRunManifest(
            manifest_path=self._manifest_path,
            run_dir=run_dir,
            nodes=nodes,
        )

    def _select_node(
        self,
        *,
        manifest: _OperatorRunManifest,
        request,
    ) -> OperatorRunNode:
        target_key = _clean_text(request.target.target_key if request.target else None)
        if target_key is None:
            target_key = self._default_node_package
        if target_key is not None:
            for node in manifest.nodes:
                if node.node_package == target_key:
                    return node
            raise NodeDeploySupervisorError(
                "Unknown operator-run node target "
                f"{target_key!r}. Available nodes: "
                f"{_available_nodes(manifest.nodes)}"
            )

        target_id = request.target.target_id if request.target else None
        if target_id is not None:
            for node in manifest.nodes:
                if node.target_id == target_id:
                    return node
            raise NodeDeploySupervisorError(
                "Unknown operator-run node target id "
                f"{target_id}. Available nodes: "
                f"{_available_nodes(manifest.nodes)}"
            )

        if len(manifest.nodes) == 1:
            return manifest.nodes[0]
        raise NodeDeploySupervisorError(
            "Operator-run manifest contains multiple nodes; pass "
            "target.target_key or configure a default node package. "
            f"Available nodes: {_available_nodes(manifest.nodes)}"
        )

    def _preflight_node(self, *, node: OperatorRunNode) -> None:
        issues = []
        if not node.command_file_path.is_file():
            issues.append(f"command_file_path missing: {node.command_file_path}")
        if not node.env_file_path.is_file():
            issues.append(f"env_file_path missing: {node.env_file_path}")
        if node.deployment_payload_path is not None and not node.deployment_payload_path.exists():
            issues.append("deployment_payload_path missing: " f"{node.deployment_payload_path}")
        if node.python_project_path is not None and not node.python_project_path.exists():
            issues.append(f"python_project_path missing: {node.python_project_path}")
        if (
            node.python_execution_closure_manifest_path is not None
            and not node.python_execution_closure_manifest_path.is_file()
        ):
            issues.append(
                "python_execution_closure_manifest_path missing: " f"{node.python_execution_closure_manifest_path}"
            )
        if issues:
            snapshot = self._failed_snapshot(
                node=node,
                message="; ".join(issues),
            )
            raise NodeDeploySupervisorError(
                "Operator-run node preflight failed: " + "; ".join(issues),
                runtime_status=snapshot,
            )

    def _inspect_node(self, *, node: OperatorRunNode) -> _NodeRuntimeState:
        receipt = self._read_status(node=node)
        pid = self._read_pid(node=node)
        if pid is None:
            pid = _int_value(receipt.get("pid") if receipt else None)
        is_active = self._process_manager.is_running(pid=pid) if pid is not None else False
        is_healthy = (
            self._health_probe(
                node=node,
                timeout_s=self._health_probe_timeout_s,
            )
            if is_active
            else False
        )
        if is_healthy:
            return _NodeRuntimeState(
                node=node,
                pid=pid,
                phase=NodeDeployRuntimePhase.ready,
                is_active=True,
                is_healthy=True,
                summary="Operator-run node is ready.",
                status_receipt=receipt,
            )
        if is_active:
            return _NodeRuntimeState(
                node=node,
                pid=pid,
                phase=NodeDeployRuntimePhase.waiting_node,
                is_active=True,
                is_healthy=False,
                summary=("Operator-run node process is active; health is not ready."),
                status_receipt=receipt,
            )
        if pid is not None and _receipt_status(receipt) in {
            "running",
            "ready",
            "starting",
        }:
            return _NodeRuntimeState(
                node=node,
                pid=pid,
                phase=NodeDeployRuntimePhase.failed,
                is_active=False,
                is_healthy=False,
                summary="Operator-run node process is not running.",
                error=f"Stale pid receipt: {pid}",
                status_receipt=receipt,
            )
        status = _receipt_status(receipt)
        summary = "Operator-run node is stopped." if status == "stopped" else "Operator-run node has not been started."
        return _NodeRuntimeState(
            node=node,
            pid=pid,
            phase=NodeDeployRuntimePhase.idle,
            is_active=False,
            is_healthy=False,
            summary=summary,
            status_receipt=receipt,
        )

    def _build_snapshot(
        self,
        *,
        manifest: _OperatorRunManifest,
        selected_node: OperatorRunNode,
        selected_state: _NodeRuntimeState | None = None,
    ) -> NodeDeployRuntimeSnapshot:
        states = {
            node.node_package: (
                selected_state
                if selected_state is not None and node.node_package == selected_node.node_package
                else self._inspect_node(node=node)
            )
            for node in manifest.nodes
        }
        state = states[selected_node.node_package]
        log_lines = _tail_file(path=selected_node.log_path, line_count=20)
        active_target_id = (
            selected_node.node_package
            if state.phase
            in {
                NodeDeployRuntimePhase.ready,
                NodeDeployRuntimePhase.waiting_node,
            }
            else None
        )
        return NodeDeployRuntimeSnapshot(
            phase=state.phase,
            target=selected_node.to_target(),
            active_target_id=active_target_id,
            backend_kind=_BACKEND_KIND,
            is_active=state.is_active,
            is_healthy=state.is_healthy,
            node_base_url=selected_node.node_base_url,
            node_websocket_path=selected_node.node_websocket_path,
            summary=state.summary,
            error=state.error,
            updated_at=utc_now_iso(),
            recent_log_lines=log_lines,
            target_statuses=tuple(
                _target_status_for_state(
                    state=item,
                    selected=(item.node.node_package == selected_node.node_package),
                    pid_file_path=self._pid_file_path(node=item.node),
                    status_file_path=self._status_file_path(node=item.node),
                )
                for item in states.values()
            ),
        )

    def _failed_snapshot(
        self,
        *,
        node: OperatorRunNode,
        message: str,
    ) -> NodeDeployRuntimeSnapshot:
        return NodeDeployRuntimeSnapshot(
            phase=NodeDeployRuntimePhase.failed,
            target=node.to_target(),
            backend_kind=_BACKEND_KIND,
            is_active=False,
            is_healthy=False,
            node_base_url=node.node_base_url,
            node_websocket_path=node.node_websocket_path,
            summary="Operator-run node preflight failed.",
            error=message,
            updated_at=utc_now_iso(),
            target_statuses=(
                NodeDeployTargetStatusSnapshot(
                    target_id=node.node_package,
                    display_name=node.node_package,
                    kind="node",
                    endpoint=node.node_base_url,
                    phase=NodeDeployRuntimePhase.failed.value,
                    is_active=False,
                    is_healthy=False,
                    summary="Preflight failed.",
                    error=message,
                    detail_lines=_node_detail_lines(
                        node=node,
                        pid=None,
                        pid_file_path=self._pid_file_path(node=node),
                        status_file_path=self._status_file_path(node=node),
                    ),
                ),
            ),
        )

    async def _wait_for_ready(
        self,
        *,
        manifest: _OperatorRunManifest,
        node: OperatorRunNode,
        request: EnsureNodeRuntimeStartedRequest,
        event_sink: NodeDeployEventSink | None,
    ) -> NodeDeployRuntimeSnapshot:
        deadline = monotonic() + self._ready_timeout_s
        while monotonic() <= deadline:
            state = self._inspect_node(node=node)
            snapshot = self._build_snapshot(
                manifest=manifest,
                selected_node=node,
                selected_state=state,
            )
            if state.is_healthy:
                self._write_status(
                    node=node,
                    pid=state.pid,
                    phase=NodeDeployRuntimePhase.ready,
                    status="ready",
                    summary="Operator-run node is ready.",
                )
                if event_sink is not None:
                    await event_sink.publish_event(
                        event=build_status_event(
                            runtime_status=snapshot,
                            actor_id=request.actor_id,
                            operation=request.operation,
                            message="Operator-run node is ready.",
                        )
                    )
                return snapshot
            if state.phase is NodeDeployRuntimePhase.failed:
                self._write_status(
                    node=node,
                    pid=state.pid,
                    phase=NodeDeployRuntimePhase.failed,
                    status="failed",
                    summary=state.summary,
                    error=state.error,
                )
                raise NodeDeploySupervisorError(
                    state.error or state.summary,
                    runtime_status=snapshot,
                )
            await asyncio.sleep(0.25)

        snapshot = self._build_snapshot(manifest=manifest, selected_node=node)
        raise NodeDeploySupervisorError(
            "Operator-run node did not become ready before timeout.",
            runtime_status=snapshot,
        )

    async def _stop_node(self, *, node: OperatorRunNode, force: bool) -> None:
        state = self._inspect_node(node=node)
        if state.pid is not None and state.is_active:
            await self._process_manager.stop(
                pid=state.pid,
                force=force,
                timeout_s=_PROCESS_STOP_TIMEOUT_S,
            )
        self._remove_pid(node=node)
        self._write_status(
            node=node,
            pid=state.pid,
            phase=NodeDeployRuntimePhase.idle,
            status="stopped",
            summary="Operator-run node stopped.",
        )

    def _pid_file_path(self, *, node: OperatorRunNode) -> Path:
        return node.run_dir / "node-deploy" / "pids" / f"{_receipt_name(node.node_package)}.pid"

    def _status_file_path(self, *, node: OperatorRunNode) -> Path:
        return node.run_dir / "node-deploy" / "status" / f"{_receipt_name(node.node_package)}.json"

    def _read_pid(self, *, node: OperatorRunNode) -> int | None:
        path = self._pid_file_path(node=node)
        try:
            return int(path.read_text(encoding="utf-8").strip())
        except (FileNotFoundError, ValueError):
            return None

    def _write_pid(self, *, node: OperatorRunNode, pid: int) -> None:
        path = self._pid_file_path(node=node)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{pid}\n", encoding="utf-8")

    def _remove_pid(self, *, node: OperatorRunNode) -> None:
        try:
            self._pid_file_path(node=node).unlink()
        except FileNotFoundError:
            return

    def _read_status(
        self,
        *,
        node: OperatorRunNode,
    ) -> Mapping[str, object] | None:
        path = self._status_file_path(node=node)
        try:
            return _load_json_object(path=path)
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            return None

    def _write_status(
        self,
        *,
        node: OperatorRunNode,
        pid: int | None,
        phase: NodeDeployRuntimePhase,
        status: str,
        summary: str,
        error: str | None = None,
    ) -> None:
        path = self._status_file_path(node=node)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": _STATUS_RECEIPT_VERSION,
            "node_package": node.node_package,
            "manifest_path": node.manifest_path.as_posix(),
            "run_dir": node.run_dir.as_posix(),
            "pid": pid,
            "phase": phase.value,
            "status": status,
            "summary": summary,
            "error": error,
            "command_file_path": node.command_file_path.as_posix(),
            "env_file_path": node.env_file_path.as_posix(),
            "log_path": node.log_path.as_posix(),
            "node_base_url": node.node_base_url,
            "node_websocket_path": node.node_websocket_path,
            "updated_at": utc_now_iso(),
        }
        previous = self._read_status(node=node)
        if previous and previous.get("started_at") and status != "running":
            payload["started_at"] = previous["started_at"]
        elif status in {"running", "ready"}:
            payload["started_at"] = previous.get("started_at") if previous else None
            if payload["started_at"] is None:
                payload["started_at"] = payload["updated_at"]
        if status == "stopped":
            payload["stopped_at"] = payload["updated_at"]
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


class _DefaultOperatorRunProcessManager:
    def __init__(self) -> None:
        self._processes: dict[int, asyncio.subprocess.Process] = {}

    async def launch(
        self,
        *,
        command_file_path: Path,
        cwd: Path,
    ) -> int:
        process = await asyncio.create_subprocess_exec(
            "bash",
            command_file_path.as_posix(),
            cwd=cwd.as_posix(),
            start_new_session=True,
        )
        self._processes[process.pid] = process
        return process.pid

    def is_running(self, *, pid: int) -> bool:
        process = self._processes.get(pid)
        if process is not None:
            return process.returncode is None
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    async def stop(
        self,
        *,
        pid: int,
        force: bool,
        timeout_s: float,
    ) -> None:
        signal_value = signal.SIGKILL if force else signal.SIGTERM
        try:
            os.killpg(pid, signal_value)
        except ProcessLookupError:
            try:
                os.kill(pid, signal_value)
            except ProcessLookupError:
                return
        process = self._processes.get(pid)
        if process is not None:
            try:
                await asyncio.wait_for(process.wait(), timeout=timeout_s)
            except asyncio.TimeoutError:
                if not force:
                    try:
                        os.killpg(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        return
                    await asyncio.wait_for(process.wait(), timeout=timeout_s)
            finally:
                self._processes.pop(pid, None)
            return

        deadline = monotonic() + timeout_s
        while monotonic() < deadline:
            if not self.is_running(pid=pid):
                return
            await asyncio.sleep(0.1)
        if not force:
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                return


def _node_from_payload(
    *,
    raw_node: Mapping[str, object],
    manifest_path: Path,
    run_dir: Path,
) -> OperatorRunNode:
    node_package = _required_text(raw_node.get("node_package"), "node_package")
    return OperatorRunNode(
        manifest_path=manifest_path,
        run_dir=run_dir,
        node_package=node_package,
        command_file_path=_required_path(
            raw_node,
            "command_file_path",
            base_dir=run_dir,
        ),
        env_file_path=_required_path(
            raw_node,
            "env_file_path",
            base_dir=run_dir,
        ),
        log_path=_required_path(raw_node, "log_path", base_dir=run_dir),
        host=_required_text(raw_node.get("host"), "host"),
        port=_required_int(raw_node.get("port"), "port"),
        command=_optional_text(raw_node.get("command")),
        boot_kernel=_bool_value(raw_node.get("boot_kernel")),
        node_id=_optional_uuid(raw_node.get("node_id")),
        node_info_path=_optional_path(
            raw_node.get("node_info_path"),
            base_dir=run_dir,
        ),
        deployment_payload_path=_optional_path(
            raw_node.get("deployment_payload_path"),
            base_dir=run_dir,
        ),
        node_host_root=_optional_path(
            raw_node.get("node_host_root"),
            base_dir=run_dir,
        ),
        python_project_path=_optional_path(
            raw_node.get("python_project_path"),
            base_dir=run_dir,
        ),
        python_execution_closure_manifest_path=_optional_path(
            raw_node.get("python_execution_closure_manifest_path"),
            base_dir=run_dir,
        ),
        environment_service_port=_optional_int(raw_node.get("environment_service_port")),
        environment_api_endpoint=_optional_text(raw_node.get("environment_api_endpoint")),
        node_base_url_override=_optional_text(raw_node.get("node_base_url")),
        node_websocket_path_override=_optional_text(raw_node.get("node_websocket_path")),
        runtime_config_status=_optional_text(raw_node.get("runtime_config_status")),
        runtime_config_missing=tuple(
            str(item).strip() for item in _list_value(raw_node.get("runtime_config_missing")) if str(item).strip()
        ),
    )


def _operator_run_manifest_from_node_run_manifest_payload(
    *,
    payload: Mapping[str, object],
    manifest_path: Path,
) -> _OperatorRunManifest:
    run_dir = _optional_path(
        payload.get("run_dir"),
        base_dir=manifest_path.parent,
    )
    if run_dir is None:
        raise ValueError("NodeRunManifest field 'run_dir' is required.")
    node = _node_from_payload(
        raw_node=_node_payload_from_node_run_manifest(
            payload=payload,
            manifest_path=manifest_path,
        ),
        manifest_path=manifest_path,
        run_dir=run_dir,
    )
    return _OperatorRunManifest(
        manifest_path=manifest_path,
        run_dir=run_dir,
        nodes=(node,),
    )


def _node_payload_from_node_run_manifest(
    *,
    payload: Mapping[str, object],
    manifest_path: Path,
) -> Mapping[str, object]:
    base_dir = manifest_path.parent
    provenance = payload.get("provenance")
    provenance_payload = cast(Mapping[str, object], provenance) if isinstance(provenance, Mapping) else {}
    deployment_payload_path = payload.get("deployment_payload_path")
    if deployment_payload_path is None:
        deployment_payload_path = provenance_payload.get("deployment_payload_path")
    return {
        "node_package": payload.get("node_package"),
        "command_file_path": _node_run_manifest_path_text(
            payload.get("command_file_path"),
            base_dir=base_dir,
        ),
        "env_file_path": _node_run_manifest_path_text(
            payload.get("env_file_path"),
            base_dir=base_dir,
        ),
        "log_path": _node_run_manifest_path_text(
            payload.get("log_path"),
            base_dir=base_dir,
        ),
        "host": payload.get("host"),
        "port": payload.get("port"),
        "command": payload.get("command"),
        "boot_kernel": True,
        "node_id": payload.get("node_id"),
        "deployment_payload_path": _node_run_manifest_path_text(
            deployment_payload_path,
            base_dir=base_dir,
        ),
        "node_host_root": _node_run_manifest_path_text(
            payload.get("node_host_root"),
            base_dir=base_dir,
        ),
        "python_project_path": _node_run_manifest_path_text(
            payload.get("python_project_path"),
            base_dir=base_dir,
        ),
        "python_execution_closure_manifest_path": _node_run_manifest_path_text(
            payload.get("python_execution_closure_manifest_path"),
            base_dir=base_dir,
        ),
        "environment_service_port": payload.get("environment_service_port"),
        "environment_api_endpoint": payload.get("environment_api_endpoint"),
        "node_base_url": payload.get("node_base_url"),
        "node_websocket_path": payload.get("node_websocket_path"),
    }


def _node_run_manifest_path_text(
    value: object,
    *,
    base_dir: Path,
) -> str | None:
    text = _optional_text(value)
    if text is None:
        return None
    return _resolve_path(value=text, base_dir=base_dir).as_posix()


def _target_status_for_state(
    *,
    state: _NodeRuntimeState,
    selected: bool,
    pid_file_path: Path,
    status_file_path: Path,
) -> NodeDeployTargetStatusSnapshot:
    return NodeDeployTargetStatusSnapshot(
        target_id=state.node.node_package,
        display_name=state.node.node_package,
        kind="node",
        endpoint=state.node.node_base_url,
        phase=state.phase.value,
        is_active=state.is_active,
        is_healthy=state.is_healthy,
        summary=state.summary,
        error=state.error,
        detail_lines=_node_detail_lines(
            node=state.node,
            pid=state.pid,
            selected=selected,
            pid_file_path=pid_file_path,
            status_file_path=status_file_path,
        ),
    )


def _node_detail_lines(
    *,
    node: OperatorRunNode,
    pid: int | None,
    pid_file_path: Path,
    status_file_path: Path,
    selected: bool = True,
) -> tuple[str, ...]:
    lines = [
        f"Operator run manifest: {node.manifest_path.as_posix()}",
        f"Run dir: {node.run_dir.as_posix()}",
        f"Node package: {node.node_package}",
        f"Selected: {str(selected).lower()}",
        f"Command file: {node.command_file_path.as_posix()}",
        f"Env file: {node.env_file_path.as_posix()}",
        f"Log file: {node.log_path.as_posix()}",
        f"PID file: {pid_file_path.as_posix()}",
        f"Status file: {status_file_path.as_posix()}",
    ]
    if node.command:
        lines.append(f"Command: {node.command}")
    if pid is not None:
        lines.append(f"PID: {pid}")
    if node.deployment_payload_path is not None:
        lines.append(f"Deployment payload: {node.deployment_payload_path.as_posix()}")
    if node.node_host_root is not None:
        lines.append(f"Node host root: {node.node_host_root.as_posix()}")
    if node.python_project_path is not None:
        lines.append(f"Python project: {node.python_project_path.as_posix()}")
    if node.python_execution_closure_manifest_path is not None:
        lines.append("Python execution closure manifest: " f"{node.python_execution_closure_manifest_path.as_posix()}")
    if node.node_info_path is not None:
        lines.append(f"Node info: {node.node_info_path.as_posix()}")
    if node.boot_kernel:
        lines.append("Boot kernel: true")
    if node.environment_service_port is not None:
        lines.append(f"Environment service port: {node.environment_service_port}")
    if node.environment_api_endpoint:
        lines.append(f"Environment API endpoint: {node.environment_api_endpoint}")
    if node.runtime_config_status:
        lines.append(f"Runtime config status: {node.runtime_config_status}")
    if node.runtime_config_missing:
        lines.append("Missing runtime config: " + ", ".join(node.runtime_config_missing))
    return tuple(lines)


def _load_json_object(*, path: Path) -> Mapping[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected JSON object at {path}")
    return cast(Mapping[str, object], payload)


def _manifest_nodes(
    *,
    payload: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    raw_nodes = payload.get("nodes")
    if raw_nodes is None:
        return ()
    if not isinstance(raw_nodes, Sequence) or isinstance(
        raw_nodes,
        (str, bytes),
    ):
        raise ValueError("Operator-run manifest nodes must be a list.")
    nodes: list[Mapping[str, object]] = []
    for raw_node in raw_nodes:
        if not isinstance(raw_node, Mapping):
            raise ValueError("Operator-run manifest node entries must be objects.")
        nodes.append(cast(Mapping[str, object], raw_node))
    return tuple(nodes)


def _read_node_info(*, path: Path | None) -> Mapping[str, object]:
    if path is None:
        return {}
    try:
        return _load_json_object(path=path)
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        return {}


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Operator-run manifest field {field_name!r} is required.")
    return value.strip()


def _required_int(value: object, field_name: str) -> int:
    result = _int_value(value)
    if result is None:
        raise ValueError(f"Operator-run manifest field {field_name!r} must be an integer.")
    return result


def _required_path(
    payload: Mapping[str, object],
    field_name: str,
    *,
    base_dir: Path,
) -> Path:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Operator-run manifest field {field_name!r} is required.")
    return _resolve_path(value=value, base_dir=base_dir)


def _optional_path(value: object, *, base_dir: Path) -> Path | None:
    text = _optional_text(value)
    if text is None:
        return None
    return _resolve_path(value=text, base_dir=base_dir)


def _resolve_path(*, value: str, base_dir: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return _clean_text(value)


def _clean_text(value: str | None) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def _optional_int(value: object) -> int | None:
    return _int_value(value)


def _int_value(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _optional_uuid(value: object) -> UUID | None:
    text = _optional_text(value)
    if text is None:
        return None
    try:
        return UUID(text)
    except ValueError:
        return None


def _list_value(value: object) -> tuple[object, ...]:
    if value is None:
        return ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(value)
    return ()


def _receipt_status(receipt: Mapping[str, object] | None) -> str | None:
    if receipt is None:
        return None
    value = receipt.get("status")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _receipt_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_." else "_" for char in value)


def _available_nodes(nodes: Sequence[OperatorRunNode]) -> str:
    return ", ".join(sorted(node.node_package for node in nodes)) or "<none>"


def _tail_file(*, path: Path, line_count: int) -> tuple[str, ...]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return ()
    return tuple(line for line in lines[-line_count:] if line)


def _default_health_probe(
    *,
    node: OperatorRunNode,
    timeout_s: float,
) -> bool:
    request = Request(f"{node.node_base_url.rstrip('/')}/health", method="GET")
    try:
        with urlopen(request, timeout=timeout_s) as response:
            return 200 <= int(response.status) < 500
    except (OSError, URLError, TimeoutError):
        return False


__all__ = [
    "OperatorRunHealthProbe",
    "OperatorRunNode",
    "OperatorRunNodeDeployBackend",
    "OperatorRunProcessManager",
]
