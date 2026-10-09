"""Workspace-environment bridge orchestrator."""

from __future__ import annotations

from aware_workspace_operator.bridge.interfaces import (
    CompilerSessionPort,
    EvidencePort,
    UpgradePort,
    WorkspaceDeltaPort,
)
from aware_workspace_operator.bridge.models import (
    BridgeEvidenceEvent,
    UpgradeExecutionResult,
    WorkspaceBridgeCycleRequest,
    WorkspaceBridgeCycleResult,
)


class WorkspaceBridgeOrchestrator:
    """Execute canonical bridge cycles via decoupled backend ports."""

    def __init__(
        self,
        *,
        workspace_delta_port: WorkspaceDeltaPort,
        compiler_session_port: CompilerSessionPort,
        upgrade_port: UpgradePort,
        evidence_port: EvidencePort,
    ) -> None:
        self._workspace_delta_port = workspace_delta_port
        self._compiler_session_port = compiler_session_port
        self._upgrade_port = upgrade_port
        self._evidence_port = evidence_port

    async def run_cycle(
        self, *, request: WorkspaceBridgeCycleRequest
    ) -> WorkspaceBridgeCycleResult:
        await self._evidence_port.record(
            event=BridgeEvidenceEvent.now(
                step="bridge_cycle_start",
                status="ok",
                details={"repo_root": request.repo_root, "lane": request.lane},
            )
        )

        normalized_delta = (
            await self._workspace_delta_port.normalize_code_package_delta(
                code_package_delta=request.code_package_delta
            )
        )
        await self._evidence_port.record(
            event=BridgeEvidenceEvent.now(
                step="code_package_delta_normalized",
                status="ok",
                details={"operation_count": _delta_operation_count(normalized_delta)},
            )
        )

        session = await self._compiler_session_port.open_session(
            repo_root=request.repo_root,
            lane=request.lane,
            language_id=request.language_id,
            focus_uri=request.focus_uri,
            session_id=request.session_id,
        )
        if session.session_id is None:
            raise ValueError("Compiler session open did not return a session_id.")

        await self._evidence_port.record(
            event=BridgeEvidenceEvent.now(
                step="compiler_session_opened",
                status="ok",
                details={"session_id": str(session.session_id)},
            )
        )

        upgrade = UpgradeExecutionResult()
        try:
            apply_result = await self._compiler_session_port.apply_code_package_delta(
                session_id=session.session_id,
                code_package_delta=normalized_delta,
                focus_uri=request.focus_uri,
            )
            await self._evidence_port.record(
                event=BridgeEvidenceEvent.now(
                    step="compiler_delta_applied",
                    status="ok",
                    details={
                        "update_id": apply_result.update_id,
                        "ocg_delta_present": apply_result.object_config_graph_delta
                        is not None,
                    },
                )
            )

            if apply_result.object_config_graph_delta is not None:
                upgrade = await self._upgrade_port.apply_compiler_delta(
                    compiler_result=apply_result
                )
                await self._evidence_port.record(
                    event=BridgeEvidenceEvent.now(
                        step="upgrade_applied",
                        status="ok",
                        details={
                            "lane_head_advanced": upgrade.lane_head_advanced,
                            "preflight_status": upgrade.preflight_status,
                            "preflight_relationship": upgrade.preflight_relationship,
                        },
                    )
                )
            else:
                await self._evidence_port.record(
                    event=BridgeEvidenceEvent.now(
                        step="upgrade_skipped",
                        status="ok",
                        details={"reason": "no_object_config_graph_delta"},
                    )
                )
        finally:
            if request.close_session:
                await self._compiler_session_port.close_session(
                    session_id=session.session_id,
                    repo_root=request.repo_root,
                    lane=request.lane,
                    language_id=request.language_id,
                    focus_uri=request.focus_uri,
                )
                await self._evidence_port.record(
                    event=BridgeEvidenceEvent.now(
                        step="compiler_session_closed",
                        status="ok",
                        details={"session_id": str(session.session_id)},
                    )
                )

        evidence_count = len(getattr(self._evidence_port, "events", ()))

        return WorkspaceBridgeCycleResult(
            session_id=session.session_id,
            update_id=apply_result.update_id,
            object_config_graph_delta_present=(
                apply_result.object_config_graph_delta is not None
            ),
            lane_head_advanced=upgrade.lane_head_advanced,
            preflight_status=upgrade.preflight_status,
            preflight_relationship=upgrade.preflight_relationship,
            preflight_integrity_ok=upgrade.preflight_integrity_ok,
            evidence_count=evidence_count,
        )


def _delta_operation_count(code_package_delta: dict[str, object]) -> int:
    operations = code_package_delta.get("operations")
    if isinstance(operations, list):
        return len(operations)
    return 0


__all__ = ["WorkspaceBridgeOrchestrator"]
