from __future__ import annotations

from uuid import UUID

import pytest

from aware_workspace_operator.bridge.adapters.compiler_service_remote import (
    CompilerServiceRemoteAdapter,
)


@pytest.mark.asyncio
async def test_remote_compiler_adapter_extracts_nested_service_operation() -> None:
    session_id = UUID("11111111-1111-1111-1111-111111111111")

    async def _request_fn(payload: dict[str, object]) -> dict[str, object]:
        assert payload["service"] == "compiler"
        assert payload["operation"] == "open_session"
        return {
            "environment_operation": {
                "response": {
                    "service_operation": {
                        "service": "compiler",
                        "operation": "open_session",
                        "session_id": str(session_id),
                        "repo_root": "/tmp/repo",
                        "lane": "main",
                        "language_id": "aware",
                        "update_id": 1,
                        "code_package_delta": {"operations": []},
                        "object_config_graph_delta": None,
                    }
                }
            }
        }

    adapter = CompilerServiceRemoteAdapter(request_fn=_request_fn)
    result = await adapter.open_session(
        repo_root="/tmp/repo",
        lane="main",
        language_id="aware",
    )
    assert result.operation == "open_session"
    assert result.session_id == session_id
    assert result.update_id == 1
