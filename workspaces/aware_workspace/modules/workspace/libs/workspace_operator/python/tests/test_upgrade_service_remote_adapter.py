from __future__ import annotations

from uuid import UUID

import pytest

from aware_workspace_operator.bridge.adapters.upgrade_service_remote import (
    CompilerUpgradeRemoteAdapter,
)
from aware_workspace_operator.bridge.models import CompilerOperationResult


@pytest.mark.asyncio
async def test_upgrade_remote_adapter_extracts_nested_upgrade_result() -> None:
    previous = UUID("11111111-1111-1111-1111-111111111111")
    current = UUID("22222222-2222-2222-2222-222222222222")

    async def _request_fn(payload: dict[str, object]) -> dict[str, object]:
        assert payload["service"] == "compiler"
        assert payload["operation"] == "apply_upgrade"
        return {
            "environment_operation": {
                "response": {
                    "service_operation": {
                        "service": "compiler",
                        "operation": "apply_upgrade",
                        "upgrade_result": {
                            "previous_head_commit_id": str(previous),
                            "current_head_commit_id": str(current),
                            "lane_head_advanced": True,
                            "preflight_status": "ok",
                            "preflight_relationship": "up_to_date",
                            "preflight_integrity_ok": True,
                        },
                    }
                }
            }
        }

    adapter = CompilerUpgradeRemoteAdapter(request_fn=_request_fn)
    result = await adapter.apply_compiler_delta(
        compiler_result=CompilerOperationResult(
            operation="apply_code_package_delta",
            session_id=UUID("33333333-3333-3333-3333-333333333333"),
            repo_root="/tmp/repo",
            lane="main",
            language_id="aware",
            update_id=5,
            object_config_graph_delta={"node_deltas": [{"change": "update"}]},
        )
    )

    assert result.previous_head_commit_id == previous
    assert result.current_head_commit_id == current
    assert result.lane_head_advanced is True
    assert result.preflight_status == "ok"
    assert result.preflight_relationship == "up_to_date"
    assert result.preflight_integrity_ok is True


@pytest.mark.asyncio
async def test_upgrade_remote_adapter_normalizes_alias_fields() -> None:
    current = UUID("44444444-4444-4444-4444-444444444444")

    async def _request_fn(payload: dict[str, object]) -> dict[str, object]:
        assert payload["operation"] == "apply_upgrade"
        return {
            "upgrade": {
                "current_commit_id": str(current),
                "status": "ok",
                "relationship": "up_to_date",
                "integrity_ok": True,
                "lane_head_advanced": True,
            }
        }

    adapter = CompilerUpgradeRemoteAdapter(request_fn=_request_fn)
    result = await adapter.apply_compiler_delta(
        compiler_result=CompilerOperationResult(
            operation="apply_code_package_delta",
            object_config_graph_delta={"node_deltas": [{"change": "update"}]},
        )
    )

    assert result.current_head_commit_id == current
    assert result.preflight_status == "ok"
    assert result.preflight_relationship == "up_to_date"
    assert result.preflight_integrity_ok is True
    assert result.lane_head_advanced is True
