from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID, uuid4

from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceActionResponse,
    InterfaceInvokeApiResponse,
    InterfaceStopResponse,
    InterfaceStatusResponse,
    NamespaceEnsureResponse,
    NamespaceListResponse,
    PingResponse,
)
from aware_interface_service_dto.comms.models.hosted_interface_namespace import (
    HostedInterfaceNamespace,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceBackendState,
    InterfaceCurrentScreen,
    InterfaceHostState,
    InterfaceRuntimeState,
    InterfaceTransportState,
)
from aware_interface_sdk import InterfaceSdkClient
from aware_sdk import cli
from aware_sdk.commands import identity as identity_command


def test_identity_status_reports_hidden_sdk_boundary(capsys) -> None:
    exit_code = cli.main(["identity", "status", "--namespace", "luis"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["identity"]["ready"] is True
    assert payload["identity"]["namespace"] == "luis"
    assert payload["api_boundary"]["sdk_package"] == "aware-identity-sdk"
    assert (
        payload["api_boundary"]["generated_api_package"] == "aware_identity_service_api"
    )
    assert payload["api_boundary"]["transport"] == "interface-api-ingress"
    assert payload["api_boundary"]["agent_process_thread_owner"] == "agent-service"


def test_admit_human_routes_identity_sdk_through_interface_api(
    monkeypatch,
    capsys,
) -> None:
    observed: dict[str, Any] = {}
    actor_id = uuid4()
    identity_id = uuid4()
    identity_profile_id = uuid4()

    monkeypatch.setattr(
        identity_command,
        "_build_interface_client",
        lambda args: InterfaceSdkClient(
            control_client=_FakeIdentityInterfaceControlClient(
                observed=observed,
                actor_id=actor_id,
                response_payload={
                    "identity_id": str(identity_id),
                    "actor_id": str(actor_id),
                    "identity_profile_id": str(identity_profile_id),
                    "public_handle": "luis",
                    "info": "identity admission completed via signup_via_profile",
                },
            )
        ),
    )

    exit_code = cli.main(
        [
            "identity",
            "admit-human",
            "--namespace",
            "luis",
            "--public-key",
            "public-key",
            "--display-name",
            "Luis",
            "--public-handle",
            "luis",
            "--bio",
            "workspace owner",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["identity"]["identity_id"] == str(identity_id)
    assert payload["identity"]["actor_id"] == str(actor_id)
    assert payload["identity"]["identity_profile_id"] == str(identity_profile_id)
    assert payload["identity"]["identity_type"] == "human"
    assert payload["gate"]["status"] == "crossed"
    assert payload["gate"]["crossed"] is True
    assert payload["api_boundary"]["service_imports_allowed"] is False
    assert observed["ensure_namespace"] == {
        "namespace": "luis",
        "auth_token": None,
        "endpoint": None,
        "host_label": None,
        "environment_config_id": None,
        "interface_package_id": None,
        "interface_package_name": None,
    }
    assert observed["invoke_api"]["endpoint_ref"] == (
        "identity.signup_via_profile.signup_via_profile"
    )
    request_payload = observed["invoke_api"]["request_payload"]
    assert request_payload["public_key"] == "public-key"
    assert request_payload["source"] == "aware_sdk.identity"
    profile_payload = request_payload["create_profile_request"]
    assert profile_payload["display_name"] == "Luis"
    assert profile_payload["public_handle"] == "luis"
    assert profile_payload["identity_type"] == "human"
    assert profile_payload["bio"] == "workspace owner"


def test_admit_agent_keeps_process_thread_out_of_identity_command(
    monkeypatch,
    capsys,
) -> None:
    observed: dict[str, Any] = {}
    actor_id = uuid4()

    monkeypatch.setattr(
        identity_command,
        "_build_interface_client",
        lambda args: InterfaceSdkClient(
            control_client=_FakeIdentityInterfaceControlClient(
                observed=observed,
                actor_id=actor_id,
                response_payload={
                    "identity_id": str(uuid4()),
                    "actor_id": str(actor_id),
                    "identity_profile_id": str(uuid4()),
                    "public_handle": "build-agent",
                },
            )
        ),
    )

    exit_code = cli.main(
        [
            "identity",
            "admit-agent",
            "--namespace",
            "codex",
            "--public-key",
            "agent-public-key",
            "--display-name",
            "Build Agent",
            "--public-handle",
            "build-agent",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["identity"]["identity_type"] == "agent"
    assert payload["api_boundary"]["agent_process_thread_owner"] == "agent-service"
    request_payload = observed["invoke_api"]["request_payload"]
    assert request_payload["create_profile_request"]["identity_type"] == "agent"
    assert "agent_process_thread_id" not in captured.out


def test_admit_human_reports_missing_local_interface_adapter(
    monkeypatch,
    capsys,
) -> None:
    def _missing_local_control(*args: object, **kwargs: object) -> InterfaceSdkClient:
        _ = args, kwargs
        raise ModuleNotFoundError(
            "No module named 'aware_interface_control'",
            name="aware_interface_control",
        )

    monkeypatch.setattr(
        InterfaceSdkClient,
        "from_local_control",
        classmethod(_missing_local_control),
    )

    exit_code = cli.main(
        [
            "identity",
            "admit-human",
            "--namespace",
            "luis",
            "--public-key",
            "public-key",
            "--display-name",
            "Luis",
            "--public-handle",
            "luis",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    payload = json.loads(captured.out)
    assert payload["namespace"] == "luis"
    assert payload["command"] == "identity"
    assert payload["ready"] is False
    assert payload["operation"] == "interface_client_bootstrap"
    assert payload["reason"] == "local_adapter_not_installed"


def test_cli_info_lists_identity_as_hidden_transitional_diagnostic(capsys) -> None:
    exit_code = cli.main(["info"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["public_contract"]["transitional_diagnostics"] == {
        "commands": ["hub", "identity", "sdk", "actions", "run"],
        "status": "hidden-bootstrap-diagnostic-only",
    }


class _FakeIdentityInterfaceControlClient:
    def __init__(
        self,
        *,
        observed: dict[str, Any],
        actor_id: UUID,
        response_payload: dict[str, object],
    ) -> None:
        self._observed = observed
        self._actor_id = actor_id
        self._response_payload = response_payload

    async def ping(self) -> PingResponse:
        return PingResponse(request_id=uuid4(), service="aware_interface_service")

    async def list_namespaces(self) -> NamespaceListResponse:
        return NamespaceListResponse(
            request_id=uuid4(),
            namespaces=[
                HostedInterfaceNamespace(
                    namespace="luis",
                    host_label="interface-luis",
                    started=True,
                )
            ],
        )

    async def ensure_namespace(
        self,
        *,
        namespace: str,
        auth_token: str | None = None,
        endpoint: str | None = None,
        host_label: str | None = None,
        environment_config_id: UUID | None = None,
        interface_package_id: UUID | None = None,
        interface_package_name: str | None = None,
    ) -> NamespaceEnsureResponse:
        self._observed["ensure_namespace"] = {
            "namespace": namespace,
            "auth_token": auth_token,
            "endpoint": endpoint,
            "host_label": host_label,
            "environment_config_id": environment_config_id,
            "interface_package_id": interface_package_id,
            "interface_package_name": interface_package_name,
        }
        return NamespaceEnsureResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=_host_state(namespace=namespace, actor_id=self._actor_id),
        )

    async def select_step(self, *, namespace: str, step_id: str | None) -> object:
        return {"namespace": namespace, "step_id": step_id}

    async def request_window_layout(
        self,
        *,
        namespace: str,
        interface_package_id: UUID | None = None,
        interface_package_name: str | None = None,
        window_key: str | None = None,
        layout_config_id: UUID | None = None,
        layout_key: str | None = None,
        section_key: str | None = None,
        observable_id: UUID | None = None,
        representation_id: UUID | None = None,
        requested_by_service: str | None = None,
        requested_by_operation: str | None = None,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> object:
        return {
            "namespace": namespace,
            "interface_package_id": interface_package_id,
            "interface_package_name": interface_package_name,
            "window_key": window_key,
            "layout_config_id": layout_config_id,
            "layout_key": layout_key,
            "section_key": section_key,
            "observable_id": observable_id,
            "representation_id": representation_id,
            "requested_by_service": requested_by_service,
            "requested_by_operation": requested_by_operation,
            "reason": reason,
            "idempotency_key": idempotency_key,
        }

    async def status(self, *, namespace: str) -> InterfaceStatusResponse:
        return InterfaceStatusResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=_host_state(namespace=namespace, actor_id=self._actor_id),
        )

    async def stop(self, *, namespace: str) -> InterfaceStopResponse:
        return InterfaceStopResponse(
            request_id=uuid4(),
            namespace=namespace,
            hosted_namespace=HostedInterfaceNamespace(
                namespace=namespace,
                host_label=f"interface-{namespace}",
                started=False,
            ),
        )

    async def invoke_api(self, **kwargs: Any) -> InterfaceInvokeApiResponse:
        self._observed["invoke_api"] = kwargs
        return InterfaceInvokeApiResponse(
            request_id=uuid4(),
            namespace=str(kwargs["namespace"]),
            endpoint_ref=str(kwargs["endpoint_ref"]),
            discriminant=str(kwargs["discriminant"]),
            service_status="succeeded",
            response_payload=self._response_payload,
        )

    async def action(self, **kwargs: Any) -> InterfaceActionResponse:
        namespace = str(kwargs["namespace"])
        return InterfaceActionResponse(
            request_id=uuid4(),
            namespace=namespace,
            action_key=str(kwargs["action_key"]),
            host_state=_host_state(namespace=namespace, actor_id=self._actor_id),
        )

    async def follow(
        self,
        *,
        namespace: str,
        poll_interval_ms: int = 1000,
    ) -> AsyncIterator[InterfaceHostState]:
        _ = poll_interval_ms
        yield _host_state(namespace=namespace, actor_id=self._actor_id)


def _host_state(*, namespace: str, actor_id: UUID) -> InterfaceHostState:
    return InterfaceHostState(
        host_label=f"interface-{namespace}",
        namespace=namespace,
        endpoint="https://interface.example",
        started=True,
        current_screen=InterfaceCurrentScreen(
            screen_kind="identity",
            screen_key="identity",
            source_kind="pane",
            title="Identity",
        ),
        transport=InterfaceTransportState(
            available=True,
            registered=True,
            authenticated=True,
            actor_id=actor_id,
            interface_id=uuid4(),
            interface_session_id=uuid4(),
            session_label=f"interface-{namespace}",
            capabilities=["interface.invoke_api"],
        ),
        runtime=InterfaceRuntimeState(
            backend=InterfaceBackendState(
                available=True,
                database_exists=True,
                opg_count=1,
                projection_bundle_available=True,
                projection_plan_count=1,
                table_count=2,
            ),
            resolved_panes=[],
        ),
    )
