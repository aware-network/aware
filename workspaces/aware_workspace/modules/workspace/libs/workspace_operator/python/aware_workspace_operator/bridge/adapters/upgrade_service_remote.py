"""Remote upgrade adapter over service-operation payloads."""

from __future__ import annotations

from typing import Any

from aware_workspace_operator.bridge.interfaces import UpgradePort
from aware_workspace_operator.bridge.models import (
    CompilerOperationResult,
    UpgradeExecutionResult,
)

from .compiler_service_remote import CompilerServiceRequestFn


class CompilerUpgradeRemoteAdapter(UpgradePort):
    """Bridge adapter that applies compiler deltas through service-operation APIs."""

    def __init__(
        self,
        *,
        request_fn: CompilerServiceRequestFn,
        operation: str = "apply_upgrade",
    ) -> None:
        self._request_fn = request_fn
        self._operation = operation

    async def apply_compiler_delta(
        self, *, compiler_result: CompilerOperationResult
    ) -> UpgradeExecutionResult:
        payload = {
            "service": "compiler",
            "operation": self._operation,
            "session_id": (
                str(compiler_result.session_id)
                if compiler_result.session_id is not None
                else None
            ),
            "repo_root": compiler_result.repo_root,
            "lane": compiler_result.lane,
            "language_id": compiler_result.language_id,
            "focus_uri": compiler_result.focus_uri,
            "update_id": compiler_result.update_id,
            "object_config_graph_delta": compiler_result.object_config_graph_delta,
        }
        response = await self._request_fn(payload)
        upgrade_payload = _extract_upgrade_payload(response=response)
        if upgrade_payload is None:
            raise ValueError(
                "Upgrade service response did not include an upgrade_result payload."
            )
        return UpgradeExecutionResult.model_validate(
            _normalize_upgrade_payload(payload=upgrade_payload)
        )


def _extract_upgrade_payload(*, response: dict[str, Any]) -> dict[str, Any] | None:
    if _is_upgrade_payload(response):
        return response

    for key in ("upgrade_result", "upgrade"):
        nested = response.get(key)
        if _is_upgrade_payload(nested):
            return nested

    for key in ("service_operation", "response", "environment_operation"):
        nested = response.get(key)
        if isinstance(nested, dict):
            payload = _extract_upgrade_payload(response=nested)
            if payload is not None:
                return payload

    return None


def _is_upgrade_payload(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    keys = {
        "previous_head_commit_id",
        "current_head_commit_id",
        "lane_head_advanced",
        "preflight_status",
        "preflight_relationship",
        "preflight_integrity_ok",
        "status",
        "relationship",
        "integrity_ok",
        "head_commit_id",
    }
    return any(k in value for k in keys)


def _normalize_upgrade_payload(*, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "previous_head_commit_id": payload.get("previous_head_commit_id")
        or payload.get("previous_commit_id"),
        "current_head_commit_id": payload.get("current_head_commit_id")
        or payload.get("head_commit_id")
        or payload.get("current_commit_id"),
        "lane_head_advanced": bool(payload.get("lane_head_advanced", False)),
        "preflight_status": payload.get("preflight_status")
        or payload.get("status")
        or "not_run",
        "preflight_relationship": payload.get("preflight_relationship")
        or payload.get("relationship"),
        "preflight_integrity_ok": (
            payload.get("preflight_integrity_ok")
            if "preflight_integrity_ok" in payload
            else payload.get("integrity_ok")
        ),
    }


__all__ = ["CompilerUpgradeRemoteAdapter"]
