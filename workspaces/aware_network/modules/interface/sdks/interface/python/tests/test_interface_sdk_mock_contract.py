from __future__ import annotations

import asyncio
import os
import subprocess
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import pytest

from aware_interface_sdk import InterfaceSdkClient

_REPO_ROOT = Path(__file__).resolve().parents[8]


@dataclass(frozen=True, slots=True)
class _MockHostProcess:
    process: subprocess.Popen[str]
    socket_path: Path


@pytest.mark.asyncio
async def test_interface_sdk_consumes_mock_identity_admission_host(
    tmp_path: Path,
) -> None:
    with _mock_host_process(tmp_path) as host:
        client = InterfaceSdkClient.from_local_control(socket_path=host.socket_path)

        ping = await client.ping()
        assert ping.service == "aware_interface_service"
        assert ping.protocol_version == 1
        assert ping.default_endpoint == "mock://identity_admission"

        surface = await client.ensure_surface(
            namespace="sdk-mock-contract",
            host_label="sdk-mock-contract-host",
        )
        assert surface.status_payload()["runtime_available"] is True
        assert surface.panes_payload()["pane_count"] == 1

        pane = surface.resolve_pane("identity_admission")
        assert pane.pane_ref == "main/coordination_center/orchestration"
        assert "sdk:identity_sdk.admit_identity" in pane.surface_affordance_keys

        runtime = surface.host_state.runtime
        assert runtime is not None
        assert len(runtime.dynamic_pane_render_specs) == 1
        assert (
            runtime.dynamic_pane_render_specs[0].payload["pane_kind"]
            == "identity_admission"
        )
        assert runtime.materialized_pane_states[0].state["status"] == "ready"

        response = await client.invoke_pane_action(
            namespace="sdk-mock-contract",
            pane_ref="identity_admission",
            action_ref="sdk:identity_sdk.admit_identity",
            payload={
                "profile": {
                    "display_name": "SDK Contract",
                    "public_handle": "@sdk-contract",
                    "bio": "AX-ready contract smoke",
                }
            },
        )
        state = response.host_state.runtime.materialized_pane_states[0].state
        assert state["status"] == "admitted"
        assert state["display_name"] == "SDK Contract"
        assert state["public_handle"] == "@sdk-contract"

        follow = client.follow_states(
            namespace="sdk-mock-contract",
            poll_interval_ms=25,
        )
        try:
            followed = await asyncio.wait_for(anext(follow), timeout=5)
        finally:
            await follow.aclose()
        assert followed.runtime is not None
        assert (
            followed.runtime.materialized_pane_states[0].state["display_name"]
            == "SDK Contract"
        )


@contextmanager
def _mock_host_process(tmp_path: Path) -> Iterator[_MockHostProcess]:
    socket_path = tmp_path / "interface-mock.sock"
    state_home = tmp_path / "interface-mock-state"
    env = dict(os.environ)
    env["AWARE_INTERFACE_CONTROL_SOCKET"] = str(socket_path)
    env["AWARE_INTERFACE_MOCK_STATE_HOME"] = str(state_home)
    env["AWARE_INTERFACE_MOCK_REPOSITORY_ROOT"] = str(_REPO_ROOT)
    process = subprocess.Popen(
        [
            "uv",
            "run",
            "--project",
            "workspaces/aware_network/modules/interface/libs/interface_mock/python",
            "aware-interface-mock-service",
        ],
        cwd=_REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        _wait_for_socket(socket_path=socket_path, process=process)
        yield _MockHostProcess(process=process, socket_path=socket_path)
    finally:
        _stop_process(process)


def _wait_for_socket(
    *,
    socket_path: Path,
    process: subprocess.Popen[str],
    timeout_s: float = 15.0,
) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate(timeout=1)
            raise AssertionError(
                "Interface mock host exited before socket was ready.\n"
                f"stdout:\n{stdout}\nstderr:\n{stderr}"
            )
        if socket_path.exists():
            return
        time.sleep(0.05)
    raise AssertionError(f"Interface mock host socket was not ready: {socket_path}")


def _stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)
