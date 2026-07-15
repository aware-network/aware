from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Iterable
from uuid import UUID

from aware_network.node_deploy.dto import (
    NodeDeployOperationEvent,
    NodeDeployRuntimeLogEvent,
    NodeDeployRuntimePhase,
    NodeDeployRuntimeStatus,
    NodeDeployRuntimeStatusEvent,
    NodeDeployRuntimeTerminalEvent,
    NodeDeployTargetStatus,
    NodeDeployTarget,
)

DEFAULT_RECENT_LOG_LIMIT = 50


def utc_now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True, slots=True)
class NodeDeployTargetStatusSnapshot:
    target_id: str
    display_name: str
    kind: str | None = None
    endpoint: str | None = None
    phase: str = "idle"
    is_active: bool = False
    is_healthy: bool = False
    summary: str | None = None
    error: str | None = None
    detail_lines: tuple[str, ...] = ()

    def to_api_model(self) -> NodeDeployTargetStatus:
        return NodeDeployTargetStatus(
            target_id=self.target_id,
            display_name=self.display_name,
            kind=self.kind,
            endpoint=self.endpoint,
            phase=self.phase,
            is_active=self.is_active,
            is_healthy=self.is_healthy,
            summary=self.summary,
            error=self.error,
            detail_lines=list(self.detail_lines),
        )


@dataclass(frozen=True, slots=True)
class NodeDeployRuntimeSnapshot:
    """Host-neutral view of the current node-deploy runtime state."""

    phase: NodeDeployRuntimePhase = NodeDeployRuntimePhase.idle
    target: NodeDeployTarget | None = None
    active_target_id: str | None = None
    backend_kind: str | None = None
    is_active: bool = False
    is_healthy: bool = False
    node_base_url: str | None = None
    node_websocket_path: str | None = None
    summary: str | None = None
    error: str | None = None
    updated_at: str | None = None
    recent_log_lines: tuple[str, ...] = ()
    target_statuses: tuple[NodeDeployTargetStatusSnapshot, ...] = ()

    def with_log_lines(
        self,
        log_lines: Iterable[str],
        *,
        limit: int = DEFAULT_RECENT_LOG_LIMIT,
    ) -> NodeDeployRuntimeSnapshot:
        normalized = tuple(line for line in log_lines if line)
        merged = (*self.recent_log_lines, *normalized)
        return replace(
            self,
            recent_log_lines=merged[-limit:],
            updated_at=utc_now_iso(),
        )

    def to_api_model(self) -> NodeDeployRuntimeStatus:
        return NodeDeployRuntimeStatus(
            target=self.target,
            phase=self.phase,
            active_target_id=self.active_target_id,
            backend_kind=self.backend_kind,
            is_active=self.is_active,
            is_healthy=self.is_healthy,
            node_base_url=self.node_base_url,
            node_websocket_path=self.node_websocket_path,
            summary=self.summary,
            error=self.error,
            updated_at=self.updated_at or utc_now_iso(),
            recent_log_lines=list(self.recent_log_lines),
            target_statuses=[item.to_api_model() for item in self.target_statuses],
        )


@dataclass(frozen=True, slots=True)
class NodeDeployLogTail:
    """Host-neutral log tail payload returned by deploy backends."""

    log_lines: tuple[str, ...] = ()
    runtime_status: NodeDeployRuntimeSnapshot | None = None


def build_status_event(
    *,
    runtime_status: NodeDeployRuntimeSnapshot,
    actor_id: UUID | None = None,
    operation: str | None = None,
    message: str | None = None,
    timestamp: str | None = None,
) -> NodeDeployOperationEvent:
    return NodeDeployRuntimeStatusEvent(
        actor_id=actor_id,
        operation=operation,
        runtime_status=runtime_status.to_api_model(),
        message=message,
        timestamp=timestamp or utc_now_iso(),
    )


def build_log_event(
    *,
    log_line: str,
    runtime_status: NodeDeployRuntimeSnapshot | None = None,
    actor_id: UUID | None = None,
    operation: str | None = None,
    message: str | None = None,
    timestamp: str | None = None,
) -> NodeDeployOperationEvent:
    return NodeDeployRuntimeLogEvent(
        actor_id=actor_id,
        operation=operation,
        runtime_status=runtime_status.to_api_model() if runtime_status else None,
        message=message,
        timestamp=timestamp or utc_now_iso(),
        log_line=log_line,
    )


def build_terminal_event(
    *,
    terminal_status: str,
    runtime_status: NodeDeployRuntimeSnapshot | None = None,
    actor_id: UUID | None = None,
    operation: str | None = None,
    message: str | None = None,
    timestamp: str | None = None,
) -> NodeDeployOperationEvent:
    return NodeDeployRuntimeTerminalEvent(
        actor_id=actor_id,
        operation=operation,
        runtime_status=runtime_status.to_api_model() if runtime_status else None,
        message=message,
        timestamp=timestamp or utc_now_iso(),
        terminal_status=terminal_status,
    )
