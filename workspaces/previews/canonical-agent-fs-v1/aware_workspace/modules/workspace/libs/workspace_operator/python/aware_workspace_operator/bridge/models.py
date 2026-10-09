"""Typed models for workspace-environment bridge orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import Field

from aware_workspace_operator.models import BaseStrictModel


class CompilerOperationResult(BaseStrictModel):
    """Result payload aligned with CompilerServiceOperation fields."""

    operation: str
    session_id: UUID | None = None
    repo_root: str | None = None
    lane: str | None = None
    language_id: str | None = None
    focus_uri: str | None = None
    update_id: int | None = None
    code_package_delta: dict[str, Any] | None = None
    object_config_graph_delta: dict[str, Any] | None = None


class UpgradeExecutionResult(BaseStrictModel):
    """Upgrade/preflight summary produced by UpgradePort implementations."""

    previous_head_commit_id: UUID | None = None
    current_head_commit_id: UUID | None = None
    lane_head_advanced: bool = False
    preflight_status: str = "not_run"
    preflight_relationship: str | None = None
    preflight_integrity_ok: bool | None = None


class BridgeEvidenceEvent(BaseStrictModel):
    """Append-only evidence event captured for bridge execution."""

    timestamp: str
    step: str
    status: str
    details: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def now(
        cls,
        *,
        step: str,
        status: str,
        details: dict[str, Any] | None = None,
    ) -> "BridgeEvidenceEvent":
        return cls(
            timestamp=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            step=step,
            status=status,
            details=details or {},
        )


class WorkspaceBridgeCycleRequest(BaseStrictModel):
    """Single bridge cycle request for remote workspace evolution."""

    repo_root: str
    lane: str = "main"
    language_id: str = "aware"
    focus_uri: str | None = None
    code_package_delta: dict[str, Any]
    close_session: bool = True
    session_id: UUID | None = None


class WorkspaceBridgeCycleResult(BaseStrictModel):
    """Bridge cycle output used for orchestration and evidence summaries."""

    session_id: UUID | None = None
    update_id: int | None = None
    object_config_graph_delta_present: bool = False
    lane_head_advanced: bool = False
    preflight_status: str = "not_run"
    preflight_relationship: str | None = None
    preflight_integrity_ok: bool | None = None
    evidence_count: int = 0


__all__ = [
    "BridgeEvidenceEvent",
    "CompilerOperationResult",
    "UpgradeExecutionResult",
    "WorkspaceBridgeCycleRequest",
    "WorkspaceBridgeCycleResult",
]
