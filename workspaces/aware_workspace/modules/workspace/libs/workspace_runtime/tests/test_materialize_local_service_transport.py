from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest
from aware_workspace_materialize_transport import (
    WorkspaceMaterializeCommandProposalV2,
    WorkspaceMaterializeCommandSelectorV2,
    WorkspaceMaterializeHostResultV2,
    WorkspaceMaterializeLocalServiceTransport,
    WorkspaceMaterializeTransportContractError,
    empty_workspace_materialize_host_counters_v2,
)
from aware_workspace_materialize_transport.local_service import (
    default_workspace_materialize_transport,
)


def _proposal() -> WorkspaceMaterializeCommandProposalV2:
    return WorkspaceMaterializeCommandProposalV2.create(
        attempt_ref="workspace-materialize-attempt:transport-test",
        participant_checkout_root="/participant/checkout",
        workspace_manifest_name="aware.workspace.toml",
        selectors=(WorkspaceMaterializeCommandSelectorV2("package", "aware.sdk"),),
        plan_only=True,
    )


def _result(
    proposal: WorkspaceMaterializeCommandProposalV2,
) -> WorkspaceMaterializeHostResultV2:
    counters = dict(empty_workspace_materialize_host_counters_v2(proposal))
    counters["authority_preflight_count"] = 1
    return WorkspaceMaterializeHostResultV2.create(
        proposal=proposal,
        outcome="blocked",
        terminal_stage="host_admission",
        host_timing_ns=(("request_decode", 1), ("host_admission", 2)),
        host_total_ns=4,
        host_counters=tuple(counters.items()),
        plan_result_wire=None,
        graph_result_wire=None,
        failure_kind="authority",
        failure_code="graph_host_not_ready",
    )


class _FrameClient:
    def __init__(self, call_result: dict[str, object]) -> None:
        self.call_result = call_result
        self.requests: list[tuple[str, dict[str, object]]] = []
        self.closed = False

    def request(self, operation: str, parameters: dict[str, object]) -> object:
        self.requests.append((operation, parameters))
        if operation == "attach":
            return {"session_token": "session:test"}
        if operation == "call":
            return self.call_result
        if operation == "detach":
            return {"detached": True}
        raise AssertionError(operation)

    def close(self) -> None:
        self.closed = True


def _transport(
    tmp_path: Path, client: _FrameClient
) -> WorkspaceMaterializeLocalServiceTransport:
    route_path = tmp_path / "route.json"
    route_path.write_text(
        json.dumps(
            {
                "endpoints": [
                    {
                        "address": "/tmp/materialize.sock",
                        "endpoint_id": "local-unix",
                        "kind": "unix",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    route_path.chmod(0o600)

    def factory(socket_path: Path, timeout: float) -> _FrameClient:
        assert socket_path == Path("/tmp/materialize.sock")
        assert timeout == 30.0
        return client

    return WorkspaceMaterializeLocalServiceTransport(
        route_path=route_path,
        client_key="workspace-materialize.codex.test",
        admission_evidence={
            "actor_kind": "agent",
            "execution_id": "codex-test",
            "provider_key": "codex",
            "provider_session_id": "test",
        },
        frame_client_factory=factory,
    )


def test_transport_uses_existing_call_envelope_and_exact_idempotency(
    tmp_path: Path,
) -> None:
    proposal = _proposal()
    result = _result(proposal)
    client = _FrameClient(
        {
            "capability_key": "workspace.materialization",
            "operation_key": "materialize",
            "correlation_id": proposal.attempt_ref,
            "status": "succeeded",
            "payload": {
                "result_wire_base64": base64.b64encode(result.to_wire()).decode()
            },
            "failure": None,
            "participant_receipt": None,
        }
    )
    observed = _transport(tmp_path, client).invoke(proposal.to_wire())

    assert observed == result
    assert client.closed is True
    assert [operation for operation, _ in client.requests] == [
        "attach",
        "call",
        "detach",
    ]
    call = client.requests[1][1]
    assert call["capability_key"] == "workspace.materialization"
    assert call["operation_key"] == "materialize"
    assert call["correlation_id"] == proposal.attempt_ref
    assert call["idempotency_key"] == proposal.attempt_ref
    assert call["require_idempotency"] is True
    payload = call["payload"]
    assert isinstance(payload, dict)
    assert base64.b64decode(payload["proposal_wire_base64"]) == proposal.to_wire()


def test_transport_failure_and_base64_poisons_fail_closed_and_close(
    tmp_path: Path,
) -> None:
    proposal = _proposal()
    failed = _FrameClient(
        {
            "correlation_id": proposal.attempt_ref,
            "status": "failed",
            "failure": {"code": "not_ready", "message": "not ready"},
        }
    )
    with pytest.raises(WorkspaceMaterializeTransportContractError, match="not_ready"):
        _transport(tmp_path, failed).invoke(proposal.to_wire())
    assert failed.closed is True

    poisoned = _FrameClient(
        {
            "correlation_id": proposal.attempt_ref,
            "status": "succeeded",
            "payload": {"result_wire_base64": "not base64!"},
        }
    )
    with pytest.raises(WorkspaceMaterializeTransportContractError, match="base64"):
        _transport(tmp_path, poisoned).invoke(proposal.to_wire())
    assert poisoned.closed is True


def test_default_transport_resolves_deployment_not_semantic_provider(
    tmp_path: Path,
) -> None:
    route_path = tmp_path / "route.json"
    route_path.write_text("{}", encoding="utf-8")
    transport = default_workspace_materialize_transport(
        env={
            "CODEX_THREAD_ID": "01test",
            "AWARE_WORKSPACE_LOCAL_SERVICE_ROUTE_PATH": str(route_path),
        }
    )
    assert transport is not None
    assert default_workspace_materialize_transport(env={}) is None
