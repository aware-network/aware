"""Port interfaces for workspace-environment bridge orchestration."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from aware_workspace_operator.bridge.models import (
    BridgeEvidenceEvent,
    CompilerOperationResult,
    UpgradeExecutionResult,
)


@runtime_checkable
class WorkspaceDeltaPort(Protocol):
    """Normalize/validate CodePackageDelta payloads before compiler submission."""

    async def normalize_code_package_delta(
        self, *, code_package_delta: dict[str, Any]
    ) -> dict[str, Any]: ...


@runtime_checkable
class CompilerSessionPort(Protocol):
    """Compiler session lifecycle + delta operations."""

    async def open_session(
        self,
        *,
        repo_root: str,
        lane: str,
        language_id: str,
        focus_uri: str | None = None,
        session_id: UUID | None = None,
    ) -> CompilerOperationResult: ...

    async def apply_code_package_delta(
        self,
        *,
        session_id: UUID,
        code_package_delta: dict[str, Any],
        focus_uri: str | None = None,
    ) -> CompilerOperationResult: ...

    async def get_object_config_graph_delta(
        self,
        *,
        session_id: UUID,
        update_id: int | None = None,
        focus_uri: str | None = None,
    ) -> CompilerOperationResult: ...

    async def close_session(
        self,
        *,
        session_id: UUID,
        repo_root: str | None = None,
        lane: str | None = None,
        language_id: str | None = None,
        focus_uri: str | None = None,
    ) -> CompilerOperationResult: ...


@runtime_checkable
class UpgradePort(Protocol):
    """Apply compiler delta rails and return lane/preflight status."""

    async def apply_compiler_delta(
        self, *, compiler_result: CompilerOperationResult
    ) -> UpgradeExecutionResult: ...


@runtime_checkable
class EvidencePort(Protocol):
    """Append-only bridge evidence sink."""

    async def record(self, *, event: BridgeEvidenceEvent) -> None: ...


__all__ = [
    "CompilerSessionPort",
    "EvidencePort",
    "UpgradePort",
    "WorkspaceDeltaPort",
]
