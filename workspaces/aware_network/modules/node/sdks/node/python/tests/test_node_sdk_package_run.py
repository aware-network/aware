from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from aware_node_sdk import (
    AwareNodeSdk,
    NodePackageRunClient,
    NodePackageRunPrepareLocalRequest,
)


class _Backend:
    def __init__(self, plan: object) -> None:
        self.plan = plan
        self.requests: list[NodePackageRunPrepareLocalRequest] = []

    def prepare_local_node_package_run(
        self,
        request: NodePackageRunPrepareLocalRequest,
    ) -> object:
        self.requests.append(request)
        return self.plan


def test_package_run_facade_normalizes_backend_plan() -> None:
    plan = SimpleNamespace(
        run_dir=Path("/tmp/run"),
        node_run_manifest_path=Path("/tmp/run/node-run-manifest.json"),
        node_operator_pid_path=Path("/tmp/run/node-deploy/pids/kernel.pid"),
        node_log_path=Path("/tmp/run/logs/node.log"),
        node_host="127.0.0.1",
        node_port=8911,
    )
    plan.to_payload = lambda: {
        "node_package": "kernel-environment-node",
        "node_run_manifest_path": plan.node_run_manifest_path.as_posix(),
        "node_operator_pid_path": plan.node_operator_pid_path.as_posix(),
        "node_log_path": plan.node_log_path.as_posix(),
        "node_host": plan.node_host,
        "node_port": plan.node_port,
    }
    backend = _Backend(plan)
    client = NodePackageRunClient(backend=backend)
    request = NodePackageRunPrepareLocalRequest(
        repo_root=Path("/repo"),
        node_toml_path=Path("nodes/kernel_environment_host/aware.node.toml"),
        run_dir=Path("/tmp/run"),
        service_toml_paths=(Path("services/environment/aware.service.toml"),),
        remote_service_api_provider_refs_json='[{"provider_node_id":"node"}]',
        interface_package_names_by_target={"aware_workspace": "aware-control"},
        auth_token="token",
        issue_runtime_auth_token=False,
        require_live_runtime=False,
    )

    result = client.prepare_local_node_package_run(request)

    assert backend.requests == [request]
    assert (
        backend.requests[0].remote_service_api_provider_refs_json
        == '[{"provider_node_id":"node"}]'
    )
    assert result.run_dir == Path("/tmp/run")
    assert result.node_run_manifest_path == Path("/tmp/run/node-run-manifest.json")
    assert result.node_operator_pid_path == Path("/tmp/run/node-deploy/pids/kernel.pid")
    assert result.node_log_path == Path("/tmp/run/logs/node.log")
    assert result.node_host == "127.0.0.1"
    assert result.node_port == 8911
    assert result.to_payload()["node_package"] == "kernel-environment-node"


def test_aware_node_sdk_exposes_package_run_facade() -> None:
    sdk = AwareNodeSdk(api_client=object())  # type: ignore[arg-type]

    assert isinstance(sdk.package_run, NodePackageRunClient)


def test_package_run_facade_rejects_backend_without_payload() -> None:
    client = NodePackageRunClient(backend=_Backend(object()))

    with pytest.raises(TypeError, match="to_payload"):
        client.prepare_local_node_package_run(
            NodePackageRunPrepareLocalRequest(
                repo_root=Path("/repo"),
                node_toml_path=Path("aware.node.toml"),
                run_dir=Path("/tmp/run"),
            )
        )
