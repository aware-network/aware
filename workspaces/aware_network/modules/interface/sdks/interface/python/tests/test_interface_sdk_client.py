from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest
from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt,
    EnvironmentNavigationCommitReceipt,
    EnvironmentNavigationContextView,
    EnvironmentSessionJoinReceipt,
    EnvironmentSessionView,
)
from aware_experience_service_dto.experience.actor_admission.models import (
    ExperienceActorConfigAdmissionReceipt,
)
from aware_interface_service_dto.comms.models.hosted_interface_namespace import (
    HostedInterfaceNamespace,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceAdmitEnvironmentActorResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceApplyAttentionLayoutTransitionResponse,
    InterfaceApplyAttentionLayoutTopologyTransitionResponse,
    InterfaceAttentionLayoutTransitionSectionIntent,
    InterfaceAttentionLayoutTopologyTransitionSectionIntent,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceJoinEnvironmentSessionResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceEnterEnvironmentResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceEnterAppScreenResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceResolveExperienceLensResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceActionResponse,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceAllowedAction,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceBackendState,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceCurrentScreen,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceEnvironmentAdmissionState,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceEnvironmentNavigationState,
    InterfaceEnvironmentSessionState,
    InterfaceExperienceLensState,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceAppScreenState,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceExperienceSessionNarrationEventState,
    InterfaceExperienceSessionNarrationState,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceHostState,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceInvokeApiResponse,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceLocalNodeRuntimeState,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceLocalServiceHostState,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceRequestWindowLayoutResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceSelectProfileResponse,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceResolvedPaneDescriptor,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceResolvedView,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceRuntimeState,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceStatusResponse,
)
from aware_interface_service_dto.comms.models.control_plane import InterfaceStopResponse
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceTransportState,
)
from aware_interface_service_dto.comms.models.control_plane import (
    NamespaceEnsureResponse,
)
from aware_interface_service_dto.comms.models.control_plane import NamespaceListResponse
from aware_interface_service_dto.comms.models.control_plane import PingResponse
from aware_interface_sdk import (
    InterfaceExperienceSessionNarrationSnapshot,
    InterfaceHostUnavailableError,
    InterfaceSdkClient,
    InterfaceSurfaceSnapshot,
)

_HUB_ENDPOINT_ID = UUID("22222222-2222-4222-8222-222222222222")
_INTERFACE_ADMISSION_ACTION_KEYS = [
    "interface_admission.create_interface",
    "interface_admission.select_interface",
    "interface_admission.request_pairing",
    "interface_admission.resume_interface",
]


def test_from_local_service_host_uses_runtime_auth_actor_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, object] = {}
    service_client = object()
    actor_id = uuid4()
    monkeypatch.setenv("AWARE_INTERFACE_AUTH_ACTOR_ID", str(actor_id))

    def _fake_build_local_interface_service_host_api_client(**kwargs: object) -> object:
        observed.update(kwargs)
        return service_client

    monkeypatch.setattr(
        "aware_interface_service.local_host.build_local_interface_service_host_api_client",
        _fake_build_local_interface_service_host_api_client,
    )

    client = InterfaceSdkClient.from_local_service_host(
        socket_path=tmp_path / "interface-service.sock",
        state_home=tmp_path / "state",
    )

    assert client.service_client is service_client
    assert observed["actor_id"] == actor_id
    assert observed["socket_path"] == (tmp_path / "interface-service.sock").resolve()
    assert client.socket_path == (tmp_path / "interface-service.sock").resolve()
    assert client.state_home == (tmp_path / "state").resolve()
    assert observed["invocation_context"] == {
        "actor_context": {
            "status": "ready",
            "kind": "agent_operator",
            "source": "interface_sdk.local_host.runtime_auth",
            "actor_id": str(actor_id),
        }
    }


def test_from_local_service_host_synthesizes_local_operator_actor_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, object] = {}
    service_client = object()
    socket_path = tmp_path / "interface-service.sock"
    state_home = tmp_path / "state"
    for env_name in (
        "AWARE_INTERFACE_AUTH_ACTOR_ID",
        "AWARE_NODE_RUNTIME_AUTH_ACTOR_ID",
        "AWARE_RUNTIME_AUTH_ACTOR_ID",
    ):
        monkeypatch.delenv(env_name, raising=False)

    def _fake_build_local_interface_service_host_api_client(**kwargs: object) -> object:
        observed.update(kwargs)
        return service_client

    monkeypatch.setattr(
        "aware_interface_service.local_host.build_local_interface_service_host_api_client",
        _fake_build_local_interface_service_host_api_client,
    )

    client = InterfaceSdkClient.from_local_service_host(
        socket_path=socket_path,
        state_home=state_home,
    )

    expected_actor_id = uuid5(
        NAMESPACE_URL,
        "aware:interface-sdk-local-host:local-operator:"
        f"{state_home.resolve().as_posix()}",
    )
    assert client.service_client is service_client
    assert observed["actor_id"] == expected_actor_id
    assert observed["invocation_context"] == {
        "actor_context": {
            "status": "ready",
            "kind": "agent_operator",
            "source": "interface_sdk.local_host.local_operator",
            "actor_id": str(expected_actor_id),
        }
    }


def test_from_local_service_host_uses_service_host_socket_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, object] = {}
    service_client = object()
    socket_path = tmp_path / "node-run" / "service" / "aware-service-host.sock"
    state_home = tmp_path / "node-run" / "interface" / "state"
    monkeypatch.setenv("AWARE_INTERFACE_SERVICE_HOST_SOCKET_PATH", str(socket_path))
    monkeypatch.setenv("AWARE_INTERFACE_SERVICE_STATE_HOME", str(state_home))

    def _fake_build_local_interface_service_host_api_client(**kwargs: object) -> object:
        observed.update(kwargs)
        return service_client

    monkeypatch.setattr(
        "aware_interface_service.local_host.build_local_interface_service_host_api_client",
        _fake_build_local_interface_service_host_api_client,
    )

    client = InterfaceSdkClient.from_local_service_host()

    assert client.service_client is service_client
    assert observed["socket_path"] == socket_path.resolve()
    assert client.socket_path == socket_path.resolve()
    assert client.state_home == state_home.resolve()


@pytest.mark.asyncio
async def test_interface_sdk_projects_hub_pane_surface() -> None:
    client = InterfaceSdkClient(control_client=_FakeInterfaceControlClient())

    surface = await client.status_surface(namespace="luis")

    assert surface.status_payload()["pane_count"] == 1
    assert surface.status_payload()["pane_api_capability_endpoint_count"] == 0
    assert surface.render_payload()["panes"][0]["pane_kind"] == "hub_code_package"
    assert surface.panes_payload()["panes"][0]["pane_ref"] == "home/main/hub"
    assert surface.panes_payload()["panes"][0]["aliases"] == [
        "hub",
        "hub_code_package",
        "aware-hub-code-package-pane",
    ]
    assert surface.panes_payload()["panes"][0]["api_capability_endpoint_ids"] == []


@pytest.mark.asyncio
async def test_interface_status_surface_projects_generated_experience_session_narration() -> (
    None
):
    commit_id = uuid4()
    branch_id = uuid4()
    actor_id = uuid4()
    client = InterfaceSdkClient(
        control_client=_NarratingInterfaceControlClient(
            commit_id=commit_id,
            branch_id=branch_id,
            actor_id=actor_id,
        )
    )

    surface = await client.status_surface(namespace="luis")
    narration = surface.experience_session_narration

    assert isinstance(surface.host_state, InterfaceHostState)
    assert isinstance(
        surface.host_state.experience_session_narration,
        InterfaceExperienceSessionNarrationState,
    )
    assert isinstance(narration, InterfaceExperienceSessionNarrationSnapshot)
    assert narration.active is True
    assert narration.feature_key == "experience_session_narrator"
    assert narration.experience_name == "my_home"
    assert narration.actor_id == actor_id
    assert narration.event_count == 1
    assert narration.last_commit_id == commit_id
    assert narration.events[0].commit_id == commit_id
    assert narration.events[0].branch_id == branch_id
    assert narration.events[0].text == "my_home lane status changed"
    assert narration.events[0].semantics == {"class_name": "Task"}
    assert narration.events_after_commit(commit_id) == ()


def test_interface_surface_without_materialized_narration_is_inactive() -> None:
    surface = InterfaceSurfaceSnapshot(
        namespace="luis",
        host_state=SimpleNamespace(experience_session_narration=None),
    )

    narration = surface.experience_session_narration

    assert narration.status == "inactive"
    assert narration.events == ()


@pytest.mark.asyncio
async def test_interface_sdk_admits_environment_actor_before_experience() -> None:
    control_client = _FakeInterfaceControlClient()
    client = InterfaceSdkClient(control_client=control_client)
    environment_profile_id = uuid4()
    actor_config_id = uuid4()
    class_instance_identity_id = uuid4()
    role_config_id = uuid4()

    response = await client.admit_environment_actor(
        namespace="luis",
        environment_profile_id=environment_profile_id,
        actor_config_id=actor_config_id,
        class_instance_identity_id=class_instance_identity_id,
        requested_role_config_ids=[role_config_id],
        requested_role_config_names=["aware.environment.member"],
        reason="join shared environment",
        evidence={"source": "sdk-test"},
    )

    assert response.environment_admission is not None
    assert response.environment_admission.status == "admitted"
    assert response.environment_admission.accepted is True
    assert response.environment_admission.environment_profile_id == (
        environment_profile_id
    )
    assert response.environment_admission.actor_config_id == actor_config_id
    assert response.environment_admission.class_instance_identity_id == (
        class_instance_identity_id
    )
    assert response.environment_admission.requested_role_config_ids == [role_config_id]
    assert response.environment_admission.requested_role_config_names == [
        "aware.environment.member"
    ]
    assert response.environment_admission_receipt is not None
    assert response.environment_admission_receipt.environment_profile_id == (
        environment_profile_id
    )
    assert control_client.requests[-1] == {
        "operation": "interface_admit_environment_actor",
        "namespace": "luis",
        "environment_profile_id": environment_profile_id,
        "actor_config_id": actor_config_id,
        "class_instance_identity_id": class_instance_identity_id,
        "requested_role_config_ids": [role_config_id],
        "requested_role_config_names": ["aware.environment.member"],
        "reason": "join shared environment",
        "evidence": {"source": "sdk-test"},
    }

    surface = InterfaceSurfaceSnapshot(
        namespace=response.namespace,
        host_state=response.host_state,
    )
    admission_payload = surface.status_payload()["environment_admission"]
    assert isinstance(admission_payload, dict)
    assert admission_payload["status"] == "admitted"
    assert admission_payload["source_kind"] == "environment_sdk_actor_admission"
    receipt_payload = surface.status_payload()["environment_admission_receipt"]
    assert isinstance(receipt_payload, dict)
    assert receipt_payload["environment_profile_id"] == str(environment_profile_id)
    assert surface.status_payload()["environment_navigation"] is None


@pytest.mark.asyncio
async def test_interface_sdk_joins_environment_session_with_default_navigation_context() -> (
    None
):
    control_client = _FakeInterfaceControlClient()
    client = InterfaceSdkClient(control_client=control_client)
    environment_id = uuid4()
    environment_profile_id = uuid4()
    actor_config_id = uuid4()
    class_instance_identity_id = uuid4()
    admission = await client.admit_environment_actor(
        namespace="luis",
        environment_id=environment_id,
        environment_profile_id=environment_profile_id,
        actor_config_id=actor_config_id,
        class_instance_identity_id=class_instance_identity_id,
        requested_role_config_names=["aware.environment.member"],
        reason="join shared environment",
        evidence={"source": "sdk-test"},
    )
    assert admission.environment_admission_receipt is not None

    environment_session_id = uuid4()
    response = await client.join_environment_session(
        namespace="luis",
        environment_session_id=environment_session_id,
        environment_admission_receipt=admission.environment_admission_receipt,
        reason="join coordination thread",
        evidence={"source": "sdk-test"},
    )

    assert response.environment_session is not None
    assert response.environment_session.environment_session_id == environment_session_id
    assert response.environment_session_join_receipt is not None
    assert response.environment_session_join_receipt.environment_session_id == (
        environment_session_id
    )
    assert response.environment_navigation_context is not None
    assert response.default_navigation_receipt is not None
    assert response.environment_session_state is not None
    assert response.environment_session_state.environment_session_id == (
        environment_session_id
    )
    assert response.environment_navigation_state is not None
    assert response.environment_navigation_state.environment_session_id == (
        environment_session_id
    )
    assert control_client.requests[-1] == {
        "operation": "interface_join_environment_session",
        "namespace": "luis",
        "environment_session_id": environment_session_id,
        "environment_profile_id": None,
        "environment_admission_receipt": admission.environment_admission_receipt,
        "reason": "join coordination thread",
        "evidence": {"source": "sdk-test"},
    }

    surface = InterfaceSurfaceSnapshot(
        namespace=response.namespace,
        host_state=response.host_state,
    )
    assert response.host_state.environment_session is not None
    assert response.host_state.environment_session.status == "joined"
    assert surface.status_payload()["environment_navigation"][
        "environment_session_id"
    ] == str(environment_session_id)


@pytest.mark.asyncio
async def test_interface_sdk_enters_environment_with_default_navigation_context() -> (
    None
):
    control_client = _FakeInterfaceControlClient()
    client = InterfaceSdkClient(control_client=control_client)
    environment_id = uuid4()
    environment_profile_id = uuid4()
    actor_config_id = uuid4()
    class_instance_identity_id = uuid4()
    environment_session_config_id = uuid4()

    response = await client.enter_environment(
        namespace="luis",
        environment_id=environment_id,
        environment_profile_id=environment_profile_id,
        actor_config_id=actor_config_id,
        class_instance_identity_id=class_instance_identity_id,
        environment_session_config_id=environment_session_config_id,
        session_key="luis:coordination",
        title="Coordination",
        reason="enter coordination",
        evidence={"source": "sdk-test"},
    )

    assert response.environment_session is not None
    assert response.environment_session.environment_id == environment_id
    assert response.environment_session.environment_profile_id == (
        environment_profile_id
    )
    assert response.environment_session.session_key == "luis:coordination"
    assert response.environment_session_join_receipt is not None
    assert response.environment_navigation_context is not None
    assert response.default_navigation_receipt is not None
    assert response.environment_session_state is not None
    assert response.environment_navigation_state is not None
    assert control_client.requests[-1] == {
        "operation": "interface_enter_environment",
        "namespace": "luis",
        "environment_id": environment_id,
        "environment_profile_id": environment_profile_id,
        "actor_config_id": actor_config_id,
        "class_instance_identity_id": class_instance_identity_id,
        "object_instance_graph_branch_key": "all",
        "object_instance_graph_branch_id": None,
        "requested_role_config_ids": [],
        "requested_role_config_names": [],
        "environment_admission_receipt": None,
        "environment_session_id": None,
        "environment_session_config_id": environment_session_config_id,
        "session_key": "luis:coordination",
        "title": "Coordination",
        "description": None,
        "purpose": None,
        "source_kind": None,
        "source_ref": None,
        "reason": "enter coordination",
        "evidence": {"source": "sdk-test"},
    }


@pytest.mark.asyncio
async def test_interface_sdk_enters_app_screen_from_committed_coordinates() -> None:
    control_client = _FakeInterfaceControlClient()
    client = InterfaceSdkClient(control_client=control_client)
    app_package_id = uuid4()
    app_package_branch_id = uuid4()
    app_package_commit_id = uuid4()
    screen_id = uuid4()

    response = await client.enter_app_screen(
        namespace="luis",
        app_package_id=app_package_id,
        app_package_branch_id=app_package_branch_id,
        app_package_object_instance_graph_commit_id=app_package_commit_id,
        app_config_screen_config_id=screen_id,
        reason="enter Home",
        evidence={"source": "sdk-test"},
    )

    assert response.app_screen is not None
    assert response.app_screen.accepted is True
    assert control_client.requests[-1] == {
        "operation": "interface_enter_app_screen",
        "namespace": "luis",
        "app_package_id": app_package_id,
        "app_package_branch_id": app_package_branch_id,
        "app_package_object_instance_graph_commit_id": app_package_commit_id,
        "app_config_screen_config_id": screen_id,
        "reason": "enter Home",
        "evidence": {"source": "sdk-test"},
    }
    assert "environment_id" not in control_client.requests[-1]
    assert "experience_name" not in control_client.requests[-1]
    assert "layout_binding_key" not in control_client.requests[-1]


@pytest.mark.asyncio
async def test_interface_sdk_resolves_experience_lens_with_session_evidence() -> None:
    control_client = _FakeInterfaceControlClient()
    client = InterfaceSdkClient(control_client=control_client)
    environment_id = uuid4()
    environment_profile_id = uuid4()
    actor_id = _host_state("luis").transport.actor_id
    environment_session_id = uuid4()
    navigation_context_id = uuid4()
    experience_session_config_id = uuid4()
    environment_session_join = EnvironmentSessionJoinReceipt(
        accepted=True,
        status="joined",
        actor_id=actor_id,
        environment_id=environment_id,
        environment_profile_id=environment_profile_id,
        environment_session_id=environment_session_id,
        environment_session_key="luis:coordination",
        evidence={"source": "sdk-test"},
    )
    environment_navigation_context = EnvironmentNavigationContextView(
        environment_navigation_context_id=navigation_context_id,
        environment_session_id=environment_session_id,
        environment_id=environment_id,
        key="main",
        status="active",
        root_object_id=uuid4(),
        evidence={"source": "sdk-test"},
    )
    experience_actor_admission = ExperienceActorConfigAdmissionReceipt(
        accepted=True,
        status="admitted",
        experience_name="aware_conversations",
        actor_id=actor_id,
        actor_config_id=uuid4(),
        class_instance_identity_id=uuid4(),
        evidence={"source": "sdk-test"},
    )

    response = await client.resolve_experience_lens(
        namespace="luis",
        environment_session_join_receipt=environment_session_join,
        environment_navigation_context=environment_navigation_context,
        experience_actor_admission=experience_actor_admission,
        experience_identity_session_config_id=experience_session_config_id,
        reason="open conversation lens",
        evidence={"source": "sdk-test"},
    )

    assert response.experience_lens is not None
    assert response.experience_lens.status == "resolved"
    assert response.environment_session is not None
    assert response.environment_session.environment_session_id == environment_session_id
    assert response.environment_navigation is not None
    assert (
        response.environment_navigation.environment_navigation_context_id
        == navigation_context_id
    )
    assert control_client.requests[-1] == {
        "operation": "interface_resolve_experience_lens",
        "namespace": "luis",
        "environment_session_join_receipt": environment_session_join,
        "environment_navigation_context": environment_navigation_context,
        "experience_actor_admission": experience_actor_admission,
        "experience_identity_session_config_id": experience_session_config_id,
        "reason": "open conversation lens",
        "evidence": {"source": "sdk-test"},
    }


@pytest.mark.asyncio
async def test_interface_sdk_projects_bootstrap_host_pane_surface() -> None:
    client = InterfaceSdkClient(control_client=_BootstrapInterfaceControlClient())

    surface = await client.ensure_surface(namespace="codex")
    payload = surface.panes_payload()

    assert payload["pane_count"] == 1
    assert payload["pane_api_capability_endpoint_count"] == 0
    assert (
        payload["panes"][0]["pane_ref"]
        == "bootstrap/bootstrap.panes/identity_auth_gate"
    )
    assert payload["panes"][0]["aliases"] == ["identity_auth_gate"]
    assert payload["panes"][0]["pane_kind"] == "identity_auth_gate"
    assert payload["panes"][0]["state_source_kind"] == "host_pane_contribution"
    assert payload["panes"][0]["state_projection_hash"] == (
        "section:bootstrap.panes:identity_auth_gate"
    )
    assert payload["panes"][0]["narrative_key"] == "bootstrap.panes.identity_auth_gate"
    assert payload["panes"][0]["surface_affordance_keys"] == ["signup_via_profile"]
    assert surface.status_payload()["runtime_available"] is True
    assert surface.status_payload()["pane_count"] == 1


@pytest.mark.asyncio
async def test_interface_sdk_exposes_actorless_interface_admission_state() -> None:
    interface_id = UUID("44444444-4444-4444-8444-444444444444")
    interface_session_id = UUID("55555555-5555-4555-8555-555555555555")
    client = InterfaceSdkClient(
        control_client=_ActorlessInterfaceAdmissionControlClient(
            interface_id=interface_id,
            interface_session_id=interface_session_id,
        )
    )

    surface = await client.ensure_surface(namespace="codex")
    payload = surface.status_payload()

    assert payload["connected"] is True
    assert payload["interface"] == {
        "registered": True,
        "admitted": True,
        "interface_id": str(interface_id),
        "interface_session_id": str(interface_session_id),
        "session_label": "interface-codex",
        "capabilities": ["interface.api"],
    }
    assert payload["actor"]["authenticated"] is False
    assert payload["actor"]["actor_id"] is None
    assert payload["surface_affordance_count"] == 4
    assert [
        item["action_key"]
        for item in surface.surface_affordances_payload()["affordances"]
    ] == _INTERFACE_ADMISSION_ACTION_KEYS


@pytest.mark.asyncio
async def test_interface_sdk_projects_local_service_host_gate_surface() -> None:
    client = InterfaceSdkClient(
        control_client=_LocalRuntimeGateInterfaceControlClient(
            gate="local_service_host_gate"
        )
    )

    surface = await client.ensure_surface(namespace="codex")
    payload = surface.panes_payload()

    assert payload["pane_count"] == 1
    assert payload["pane_api_capability_endpoint_count"] == 0
    assert payload["panes"][0]["pane_ref"] == (
        "bootstrap/bootstrap.panes/local_service_host_gate"
    )
    assert payload["panes"][0]["aliases"] == ["local_service_host_gate"]
    assert payload["panes"][0]["pane_kind"] == "local_service_host_gate"
    assert payload["panes"][0]["state_source_kind"] == "host_pane_contribution"
    assert payload["panes"][0]["state_projection_hash"] == (
        "section:bootstrap.panes:local_service_host_gate"
    )
    assert payload["panes"][0]["narrative_key"] == (
        "bootstrap.panes.local_service_host_gate"
    )
    assert payload["panes"][0]["surface_affordance_keys"] == [
        "ensure_local_service_host",
        "restart_local_service_host",
    ]
    capabilities = surface.capabilities_payload()
    assert capabilities["local_service_host"]["managed"] is True
    assert capabilities["local_service_host"]["ready"] is False
    assert capabilities["local_node_runtime"] is None
    assert surface.status_payload()["warnings"] == ["local_service_host_required"]


def test_interface_sdk_prefers_current_gate_over_stale_runtime_panes() -> None:
    host_state = _aware_control_host_state("codex").model_copy(
        update={
            "current_screen": InterfaceCurrentScreen(
                screen_kind="gate",
                screen_key="local_service_host_gate",
                source_kind="gate",
                title="Local Service Host Required",
                message="Local Service host socket was not found.",
                pane_key="local_service_host_gate",
            ),
            "allowed_actions": [
                InterfaceAllowedAction(
                    action_key="ensure_local_service_host",
                    label="Ensure Local Service Host",
                ),
                InterfaceAllowedAction(
                    action_key="restart_local_service_host",
                    label="Restart Local Service Host",
                ),
            ],
            "warnings": ["local_service_host_required"],
        }
    )
    surface = InterfaceSurfaceSnapshot(namespace="codex", host_state=host_state)

    payload = surface.panes_payload()

    assert payload["pane_count"] == 1
    assert payload["panes"][0]["pane_ref"] == (
        "bootstrap/bootstrap.panes/local_service_host_gate"
    )
    assert payload["panes"][0]["aliases"] == ["local_service_host_gate"]
    assert payload["panes"][0]["surface_affordance_keys"] == [
        "ensure_local_service_host",
        "restart_local_service_host",
    ]
    assert surface.resolve_pane("local_service_host_gate").pane_ref == (
        "bootstrap/bootstrap.panes/local_service_host_gate"
    )


@pytest.mark.asyncio
async def test_interface_sdk_rejects_hub_pane_capability_without_endpoint_ids() -> None:
    control_client = _FakeInterfaceControlClient()
    client = InterfaceSdkClient(control_client=control_client)

    with pytest.raises(ValueError, match="is not exposed by pane"):
        await client.invoke_pane_capability(
            namespace="luis",
            pane_ref="hub",
            capability_ref="1",
            request_payload={"package_name": "aware-home"},
        )

    assert control_client.requests == [
        {"operation": "namespace_ensure", "namespace": "luis"},
    ]


@pytest.mark.asyncio
async def test_interface_sdk_invokes_api_endpoint_without_control_client_reachthrough() -> (
    None
):
    control_client = _FakeInterfaceControlClient()
    client = InterfaceSdkClient(control_client=control_client)

    response = await client.invoke_api_endpoint(
        namespace="luis",
        endpoint_ref=str(_HUB_ENDPOINT_ID),
        discriminant="hub.package.resolve",
        request_payload={"package_name": "aware-home"},
    )

    assert response.endpoint_ref == str(_HUB_ENDPOINT_ID)
    assert response.discriminant == "hub.package.resolve"
    assert response.service_status == "ok"
    assert control_client.requests == [
        {
            "operation": "interface_invoke_api",
            "namespace": "luis",
            "endpoint_ref": str(_HUB_ENDPOINT_ID),
            "discriminant": "hub.package.resolve",
            "request_payload": {"package_name": "aware-home"},
        },
    ]


@pytest.mark.asyncio
async def test_interface_sdk_rejects_unmounted_hub_capability_before_invoke() -> None:
    control_client = _FakeInterfaceControlClient()
    client = InterfaceSdkClient(control_client=control_client)

    with pytest.raises(ValueError, match="is not exposed by pane"):
        await client.invoke_pane_capability(
            namespace="luis",
            pane_ref="hub",
            capability_ref="33333333-3333-4333-8333-333333333333",
        )

    assert control_client.requests == [
        {"operation": "namespace_ensure", "namespace": "luis"},
    ]


@pytest.mark.asyncio
async def test_interface_sdk_invokes_bootstrap_pane_action() -> None:
    control_client = _BootstrapInterfaceControlClient()
    client = InterfaceSdkClient(control_client=control_client)

    response = await client.invoke_pane_action(
        namespace="codex",
        pane_ref="identity_auth_gate",
        action_ref="signup_via_profile",
        payload={"public_key": "ed25519:test"},
    )

    assert response.action_key == "signup_via_profile"
    assert response.pane_ref == "bootstrap/bootstrap.panes/identity_auth_gate"
    assert control_client.requests == [
        {"operation": "namespace_ensure", "namespace": "codex"},
        {
            "operation": "interface_action",
            "namespace": "codex",
            "pane_ref": "bootstrap/bootstrap.panes/identity_auth_gate",
            "action_key": "signup_via_profile",
            "payload": {"public_key": "ed25519:test"},
        },
    ]


@pytest.mark.asyncio
async def test_interface_sdk_invokes_local_runtime_gate_actions() -> None:
    control_client = _LocalRuntimeGateInterfaceControlClient(
        gate="local_service_host_gate"
    )
    client = InterfaceSdkClient(control_client=control_client)

    service_response = await client.invoke_pane_action(
        namespace="codex",
        pane_ref="local_service_host_gate",
        action_ref="ensure_local_service_host",
    )
    assert service_response.action_key == "ensure_local_service_host"
    assert service_response.pane_ref == (
        "bootstrap/bootstrap.panes/local_service_host_gate"
    )

    control_client = _LocalRuntimeGateInterfaceControlClient(
        gate="local_node_runtime_gate"
    )
    client = InterfaceSdkClient(control_client=control_client)

    node_response = await client.invoke_pane_action(
        namespace="codex",
        pane_ref="local_node_runtime_gate",
        action_ref="ensure_local_node_runtime_started",
    )
    assert node_response.action_key == "ensure_local_node_runtime_started"
    assert node_response.pane_ref == "bootstrap/bootstrap.panes/local_node_runtime_gate"
    assert control_client.requests == [
        {"operation": "namespace_ensure", "namespace": "codex"},
        {
            "operation": "interface_action",
            "namespace": "codex",
            "pane_ref": "bootstrap/bootstrap.panes/local_node_runtime_gate",
            "action_key": "ensure_local_node_runtime_started",
            "payload": {},
        },
    ]


@pytest.mark.asyncio
async def test_interface_sdk_invokes_aware_control_hub_selector_mounted_api_action() -> (
    None
):
    control_client = _AwareControlInterfaceControlClient()
    client = InterfaceSdkClient(control_client=control_client)

    response = await client.invoke_pane_action(
        namespace="codex",
        pane_ref="hub_package_selector",
        action_ref="api:hub.code_package.search",
        payload={"query": "aware-control", "limit": 5},
    )

    assert response.action_key == "api:hub.code_package.search"
    assert response.pane_ref == "main/coordination_center/primary"
    assert control_client.requests == [
        {"operation": "namespace_ensure", "namespace": "codex"},
        {
            "operation": "interface_action",
            "namespace": "codex",
            "pane_ref": "main/coordination_center/primary",
            "action_key": "api:hub.code_package.search",
            "payload": {"query": "aware-control", "limit": 5},
        },
    ]


@pytest.mark.asyncio
async def test_interface_sdk_requests_window_layout_through_control_client() -> None:
    control_client = _FakeInterfaceControlClient()
    client = InterfaceSdkClient(control_client=control_client)
    interface_package_id = UUID("11111111-1111-4111-8111-111111111111")
    layout_config_id = UUID("33333333-3333-4333-8333-333333333333")
    observable_id = UUID("44444444-4444-4444-8444-444444444444")

    response = await client.request_window_layout(
        namespace="codex",
        interface_package_id=interface_package_id,
        interface_package_name="aware-workspace-interface",
        window_key="main",
        layout_config_id=layout_config_id,
        layout_key="ide_workbench",
        section_key="primary",
        observable_id=observable_id,
        requested_by_service="conversation",
        requested_by_operation="select_attention",
        reason="issue-selected-from-feed",
        idempotency_key="conversation:issue-feed-select",
    )

    assert response.operation == "interface_request_window_layout"
    assert response.namespace == "codex"
    assert response.layout_key == "ide_workbench"
    assert response.section_key == "primary"
    assert response.observable_id == observable_id
    assert control_client.requests == [
        {
            "operation": "interface_request_window_layout",
            "namespace": "codex",
            "interface_package_id": interface_package_id,
            "interface_package_name": "aware-workspace-interface",
            "window_key": "main",
            "layout_config_id": layout_config_id,
            "layout_key": "ide_workbench",
            "section_key": "primary",
            "observable_id": observable_id,
            "representation_id": None,
            "requested_by_service": "conversation",
            "requested_by_operation": "select_attention",
            "reason": "issue-selected-from-feed",
            "idempotency_key": "conversation:issue-feed-select",
        }
    ]


@pytest.mark.asyncio
async def test_interface_sdk_applies_one_attention_layout_transition() -> None:
    control_client = _FakeInterfaceControlClient()
    client = InterfaceSdkClient(control_client=control_client)
    previous_transition_id = UUID("99999999-9999-4999-8999-999999999999")
    topology_transition_id = UUID("88888888-8888-4888-8888-888888888888")
    section_id = UUID("11111111-1111-4111-8111-111111111111")
    sections = [
        InterfaceAttentionLayoutTransitionSectionIntent(
            layout_config_section_config_id=section_id,
            order=0,
            weight_micros=1_000_000,
        )
    ]

    response = await client.apply_attention_layout_transition(
        namespace="codex",
        client_intent_id="drag-1",
        expected_previous_layout_transition_id=previous_transition_id,
        topology_transition_id=topology_transition_id,
        section_states=sections,
    )

    assert response.outcome == "committed"
    assert control_client.requests == [
        {
            "operation": "interface_apply_attention_layout_transition",
            "namespace": "codex",
            "client_intent_id": "drag-1",
            "expected_previous_layout_transition_id": previous_transition_id,
            "topology_transition_id": topology_transition_id,
            "section_states": sections,
        }
    ]


@pytest.mark.asyncio
async def test_interface_sdk_applies_one_attention_layout_topology_transition() -> None:
    control_client = _FakeInterfaceControlClient()
    client = InterfaceSdkClient(control_client=control_client)
    previous_topology_transition_id = UUID("99999999-9999-4999-8999-999999999999")
    section_id = UUID("11111111-1111-4111-8111-111111111111")
    sections = [
        InterfaceAttentionLayoutTopologyTransitionSectionIntent(
            layout_config_section_config_id=section_id,
            order=0,
        )
    ]

    response = await client.apply_attention_layout_topology_transition(
        namespace="codex",
        client_intent_id="topology-1",
        expected_previous_topology_transition_id=(previous_topology_transition_id),
        section_states=sections,
    )

    assert response.outcome == "committed"
    assert control_client.requests == [
        {
            "operation": "interface_apply_attention_layout_topology_transition",
            "namespace": "codex",
            "client_intent_id": "topology-1",
            "expected_previous_topology_transition_id": (
                previous_topology_transition_id
            ),
            "section_states": sections,
        }
    ]


@pytest.mark.asyncio
async def test_interface_sdk_ensure_surface_forwards_interface_package() -> None:
    control_client = _FakeInterfaceControlClient()
    client = InterfaceSdkClient(control_client=control_client)
    interface_package_id = UUID("11111111-1111-4111-8111-111111111111")

    await client.ensure_surface(
        namespace="codex",
        interface_package_id=interface_package_id,
        interface_package_name="aware-control-interface",
    )

    assert control_client.requests == [
        {
            "operation": "namespace_ensure",
            "namespace": "codex",
            "interface_package_id": interface_package_id,
            "interface_package_name": "aware-control-interface",
        }
    ]


@pytest.mark.asyncio
async def test_interface_sdk_rejects_action_not_exposed_by_pane() -> None:
    control_client = _BootstrapInterfaceControlClient()
    client = InterfaceSdkClient(control_client=control_client)

    with pytest.raises(ValueError, match="is not exposed by pane"):
        await client.invoke_pane_action(
            namespace="codex",
            pane_ref="identity_auth_gate",
            action_ref="submit_token",
        )

    assert control_client.requests == [
        {"operation": "namespace_ensure", "namespace": "codex"},
    ]


@pytest.mark.asyncio
async def test_interface_sdk_reports_unavailable_host_readiness_payload() -> None:
    socket_path = Path("/tmp/missing-interface-control.sock")
    client = InterfaceSdkClient(
        control_client=_UnavailableInterfaceControlClient(),
        socket_path=socket_path,
    )

    with pytest.raises(InterfaceHostUnavailableError) as exc_info:
        await client.status_surface(namespace="codex")

    payload = exc_info.value.readiness_payload(
        namespace="codex",
        command="status",
    )
    assert payload["ready"] is False
    assert payload["status"] == "interface_host_unavailable"
    assert payload["product_boundary"] == "interface-renderer"
    assert payload["operation"] == "interface_status"
    assert payload["reason"] == "socket_not_found"
    assert payload["socket_path"] == str(socket_path)


@pytest.mark.asyncio
async def test_interface_sdk_select_profile_dispatches_through_interface_control() -> (
    None
):
    control_client = _FakeInterfaceControlClient()
    client = InterfaceSdkClient(control_client=control_client)

    response = await client.select_profile(
        namespace="codex",
        profile_id="operator.local_bootstrap",
    )

    assert response.namespace == "codex"
    assert response.profile_id == "operator.local_bootstrap"
    assert control_client.requests[-1] == {
        "operation": "interface_select_profile",
        "namespace": "codex",
        "profile_id": "operator.local_bootstrap",
    }


def _namespace_ensure_record(
    namespace: str,
    *,
    interface_package_id: UUID | None = None,
    interface_package_name: str | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "operation": "namespace_ensure",
        "namespace": namespace,
    }
    if interface_package_id is not None:
        record["interface_package_id"] = interface_package_id
    if interface_package_name is not None:
        record["interface_package_name"] = interface_package_name
    return record


class _FakeInterfaceControlClient:
    def __init__(self) -> None:
        self.requests: list[dict[str, object]] = []

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
        _ = auth_token, endpoint, host_label, environment_config_id
        self.requests.append(
            _namespace_ensure_record(
                namespace,
                interface_package_id=interface_package_id,
                interface_package_name=interface_package_name,
            )
        )
        return NamespaceEnsureResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=_host_state(namespace),
        )

    async def select_step(self, *, namespace: str, step_id: str | None) -> object:
        return {"namespace": namespace, "step_id": step_id}

    async def select_profile(
        self,
        *,
        namespace: str,
        profile_id: str,
    ) -> InterfaceSelectProfileResponse:
        self.requests.append(
            {
                "operation": "interface_select_profile",
                "namespace": namespace,
                "profile_id": profile_id,
            }
        )
        return InterfaceSelectProfileResponse(
            request_id=uuid4(),
            namespace=namespace,
            profile_id=profile_id,
            host_state=_host_state(namespace),
        )

    async def status(self, *, namespace: str) -> InterfaceStatusResponse:
        self.requests.append({"operation": "interface_status", "namespace": namespace})
        return InterfaceStatusResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=_host_state(namespace),
        )

    async def admit_environment_actor(
        self,
        *,
        namespace: str,
        environment_id: UUID | None = None,
        environment_profile_id: UUID,
        actor_config_id: UUID,
        class_instance_identity_id: UUID,
        object_instance_graph_branch_key: str = "all",
        object_instance_graph_branch_id: UUID | None = None,
        requested_role_config_ids: list[UUID] | None = None,
        requested_role_config_names: list[str] | None = None,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> InterfaceAdmitEnvironmentActorResponse:
        _ = (
            environment_id,
            object_instance_graph_branch_key,
            object_instance_graph_branch_id,
        )
        requested_role_ids = list(requested_role_config_ids or ())
        requested_role_names = list(requested_role_config_names or ())
        self.requests.append(
            {
                "operation": "interface_admit_environment_actor",
                "namespace": namespace,
                "environment_profile_id": environment_profile_id,
                "actor_config_id": actor_config_id,
                "class_instance_identity_id": class_instance_identity_id,
                "requested_role_config_ids": requested_role_ids,
                "requested_role_config_names": requested_role_names,
                "reason": reason,
                "evidence": dict(evidence or {}),
            }
        )
        host_state = _host_state(namespace)
        resolved_environment_id = environment_id or uuid4()
        environment_admission = InterfaceEnvironmentAdmissionState(
            status="admitted",
            source_kind="environment_sdk_actor_admission",
            accepted=True,
            actor_id=host_state.transport.actor_id,
            environment_id=resolved_environment_id,
            environment_profile_id=environment_profile_id,
            actor_config_id=actor_config_id,
            class_instance_identity_id=class_instance_identity_id,
            requested_role_config_ids=requested_role_ids,
            requested_role_config_names=requested_role_names,
            binding_count=1,
            evidence={"source": "fake-control-client"},
        )
        environment_admission_receipt = EnvironmentActorAdmissionReceipt(
            accepted=True,
            status="admitted",
            actor_id=host_state.transport.actor_id,
            environment_id=resolved_environment_id,
            environment_profile_id=environment_profile_id,
            actor_config_id=actor_config_id,
            class_instance_identity_id=class_instance_identity_id,
            requested_role_config_ids=requested_role_ids,
            requested_role_config_names=requested_role_names,
            evidence={"source": "fake-control-client"},
        )
        return InterfaceAdmitEnvironmentActorResponse(
            request_id=uuid4(),
            namespace=namespace,
            environment_admission=environment_admission,
            environment_admission_receipt=environment_admission_receipt,
            host_state=host_state.model_copy(
                update={
                    "environment_admission": environment_admission,
                    "environment_admission_receipt": environment_admission_receipt,
                },
            ),
        )

    async def join_environment_session(
        self,
        *,
        namespace: str,
        environment_session_id: UUID,
        environment_profile_id: UUID | None = None,
        environment_admission_receipt: EnvironmentActorAdmissionReceipt | None = None,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> InterfaceJoinEnvironmentSessionResponse:
        self.requests.append(
            {
                "operation": "interface_join_environment_session",
                "namespace": namespace,
                "environment_session_id": environment_session_id,
                "environment_profile_id": environment_profile_id,
                "environment_admission_receipt": environment_admission_receipt,
                "reason": reason,
                "evidence": dict(evidence or {}),
            }
        )
        host_state = _host_state(namespace)
        resolved_environment_id = (
            environment_admission_receipt.environment_id
            if environment_admission_receipt is not None
            else uuid4()
        )
        resolved_profile_id = (
            environment_admission_receipt.environment_profile_id
            if environment_admission_receipt is not None
            else (environment_profile_id or uuid4())
        )
        actor_id = (
            environment_admission_receipt.actor_id
            if environment_admission_receipt is not None
            else host_state.transport.actor_id
        )
        navigation_context_id = uuid4()
        process_id = uuid4()
        thread_id = uuid4()
        environment_session = EnvironmentSessionView(
            environment_session_id=environment_session_id,
            environment_id=resolved_environment_id,
            environment_profile_id=resolved_profile_id,
            session_key="luis:coordination",
            title="Coordination",
            status="active",
            evidence={"source": "fake-control-client"},
        )
        environment_session_join_receipt = EnvironmentSessionJoinReceipt(
            accepted=True,
            status="joined",
            actor_id=actor_id,
            environment_id=resolved_environment_id,
            environment_profile_id=resolved_profile_id,
            environment_session_id=environment_session_id,
            environment_session_key=environment_session.session_key,
            evidence={"source": "fake-control-client"},
        )
        environment_navigation_context = EnvironmentNavigationContextView(
            environment_navigation_context_id=navigation_context_id,
            environment_session_id=environment_session_id,
            environment_id=resolved_environment_id,
            key="main",
            title="Main",
            status="active",
            selected_process_id=process_id,
            selected_thread_id=thread_id,
            root_object_id=uuid4(),
            evidence={"source": "fake-control-client"},
        )
        default_navigation_receipt = EnvironmentNavigationCommitReceipt(
            accepted=True,
            status="selected",
            actor_id=actor_id,
            environment_id=resolved_environment_id,
            environment_session_id=environment_session_id,
            environment_navigation_context_id=navigation_context_id,
            key=environment_navigation_context.key,
            is_default=True,
            selected_process_id=process_id,
            selected_thread_id=thread_id,
            root_object_id=environment_navigation_context.root_object_id,
            evidence={"source": "fake-control-client"},
        )
        environment_session_state = InterfaceEnvironmentSessionState(
            status=environment_session_join_receipt.status,
            accepted=environment_session_join_receipt.accepted,
            actor_id=actor_id,
            environment_id=resolved_environment_id,
            environment_profile_id=resolved_profile_id,
            environment_session_id=environment_session_id,
            environment_session_key=environment_session.session_key,
            evidence={"source": "fake-control-client"},
        )
        environment_navigation_state = InterfaceEnvironmentNavigationState(
            status=environment_navigation_context.status,
            accepted=True,
            actor_id=actor_id,
            environment_id=resolved_environment_id,
            environment_session_id=environment_session_id,
            environment_navigation_context_id=navigation_context_id,
            key=environment_navigation_context.key,
            process_id=process_id,
            thread_id=thread_id,
            root_object_id=environment_navigation_context.root_object_id,
            evidence={"source": "fake-control-client"},
        )
        host_state = host_state.model_copy(
            update={
                "environment_session": environment_session_state,
                "environment_session_join_receipt": (environment_session_join_receipt),
                "environment_navigation": environment_navigation_state,
            },
        )
        return InterfaceJoinEnvironmentSessionResponse(
            request_id=uuid4(),
            namespace=namespace,
            environment_session=environment_session,
            environment_session_join_receipt=environment_session_join_receipt,
            environment_navigation_context=environment_navigation_context,
            default_navigation_receipt=default_navigation_receipt,
            environment_session_state=environment_session_state,
            environment_navigation_state=environment_navigation_state,
            host_state=host_state,
        )

    async def enter_environment(
        self,
        *,
        namespace: str,
        environment_id: UUID | None = None,
        environment_profile_id: UUID | None = None,
        actor_config_id: UUID | None = None,
        class_instance_identity_id: UUID | None = None,
        object_instance_graph_branch_key: str = "all",
        object_instance_graph_branch_id: UUID | None = None,
        requested_role_config_ids: list[UUID] | None = None,
        requested_role_config_names: list[str] | None = None,
        environment_admission_receipt: EnvironmentActorAdmissionReceipt | None = None,
        environment_session_id: UUID | None = None,
        environment_session_config_id: UUID | None = None,
        session_key: str | None = None,
        title: str | None = None,
        description: str | None = None,
        purpose: str | None = None,
        source_kind: str | None = None,
        source_ref: str | None = None,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> InterfaceEnterEnvironmentResponse:
        requested_role_ids = list(requested_role_config_ids or ())
        requested_role_names = list(requested_role_config_names or ())
        self.requests.append(
            {
                "operation": "interface_enter_environment",
                "namespace": namespace,
                "environment_id": environment_id,
                "environment_profile_id": environment_profile_id,
                "actor_config_id": actor_config_id,
                "class_instance_identity_id": class_instance_identity_id,
                "object_instance_graph_branch_key": object_instance_graph_branch_key,
                "object_instance_graph_branch_id": object_instance_graph_branch_id,
                "requested_role_config_ids": requested_role_ids,
                "requested_role_config_names": requested_role_names,
                "environment_admission_receipt": environment_admission_receipt,
                "environment_session_id": environment_session_id,
                "environment_session_config_id": environment_session_config_id,
                "session_key": session_key,
                "title": title,
                "description": description,
                "purpose": purpose,
                "source_kind": source_kind,
                "source_ref": source_ref,
                "reason": reason,
                "evidence": dict(evidence or {}),
            }
        )
        host_state = _host_state(namespace)
        resolved_environment_id = (
            environment_admission_receipt.environment_id
            if environment_admission_receipt is not None
            else (environment_id or uuid4())
        )
        resolved_profile_id = (
            environment_admission_receipt.environment_profile_id
            if environment_admission_receipt is not None
            else (environment_profile_id or uuid4())
        )
        actor_id = (
            environment_admission_receipt.actor_id
            if environment_admission_receipt is not None
            else host_state.transport.actor_id
        )
        resolved_session_id = environment_session_id or uuid4()
        resolved_session_key = session_key or "luis:coordination"
        navigation_context_id = uuid4()
        process_id = uuid4()
        thread_id = uuid4()
        environment_admission = InterfaceEnvironmentAdmissionState(
            status="admitted",
            source_kind="environment_sdk_actor_admission",
            accepted=True,
            actor_id=actor_id,
            environment_id=resolved_environment_id,
            environment_profile_id=resolved_profile_id,
            actor_config_id=actor_config_id,
            class_instance_identity_id=class_instance_identity_id,
            requested_role_config_ids=requested_role_ids,
            requested_role_config_names=requested_role_names,
            binding_count=1,
            evidence={"source": "fake-control-client"},
        )
        resolved_admission_receipt = environment_admission_receipt or (
            EnvironmentActorAdmissionReceipt(
                accepted=True,
                status="admitted",
                actor_id=actor_id,
                environment_id=resolved_environment_id,
                environment_profile_id=resolved_profile_id,
                actor_config_id=actor_config_id,
                class_instance_identity_id=class_instance_identity_id,
                requested_role_config_ids=requested_role_ids,
                requested_role_config_names=requested_role_names,
                evidence={"source": "fake-control-client"},
            )
        )
        environment_session = EnvironmentSessionView(
            environment_session_id=resolved_session_id,
            environment_id=resolved_environment_id,
            environment_profile_id=resolved_profile_id,
            session_key=resolved_session_key,
            title=title or "Coordination",
            status="active",
            evidence={"source": "fake-control-client"},
        )
        environment_session_join_receipt = EnvironmentSessionJoinReceipt(
            accepted=True,
            status="joined",
            actor_id=actor_id,
            environment_id=resolved_environment_id,
            environment_profile_id=resolved_profile_id,
            environment_session_id=resolved_session_id,
            environment_session_key=environment_session.session_key,
            evidence={"source": "fake-control-client"},
        )
        environment_navigation_context = EnvironmentNavigationContextView(
            environment_navigation_context_id=navigation_context_id,
            environment_session_id=resolved_session_id,
            environment_id=resolved_environment_id,
            key="main",
            title="Main",
            status="active",
            selected_process_id=process_id,
            selected_thread_id=thread_id,
            root_object_id=uuid4(),
            evidence={"source": "fake-control-client"},
        )
        default_navigation_receipt = EnvironmentNavigationCommitReceipt(
            accepted=True,
            status="selected",
            actor_id=actor_id,
            environment_id=resolved_environment_id,
            environment_session_id=resolved_session_id,
            environment_navigation_context_id=navigation_context_id,
            key=environment_navigation_context.key,
            is_default=True,
            selected_process_id=process_id,
            selected_thread_id=thread_id,
            root_object_id=environment_navigation_context.root_object_id,
            evidence={"source": "fake-control-client"},
        )
        environment_session_state = InterfaceEnvironmentSessionState(
            status=environment_session_join_receipt.status,
            accepted=environment_session_join_receipt.accepted,
            actor_id=actor_id,
            environment_id=resolved_environment_id,
            environment_profile_id=resolved_profile_id,
            environment_session_id=resolved_session_id,
            environment_session_key=environment_session.session_key,
            evidence={"source": "fake-control-client"},
        )
        environment_navigation_state = InterfaceEnvironmentNavigationState(
            status=environment_navigation_context.status,
            accepted=True,
            actor_id=actor_id,
            environment_id=resolved_environment_id,
            environment_session_id=resolved_session_id,
            environment_navigation_context_id=navigation_context_id,
            key=environment_navigation_context.key,
            process_id=process_id,
            thread_id=thread_id,
            root_object_id=environment_navigation_context.root_object_id,
            evidence={"source": "fake-control-client"},
        )
        host_state = host_state.model_copy(
            update={
                "environment_admission": environment_admission,
                "environment_admission_receipt": resolved_admission_receipt,
                "environment_session": environment_session_state,
                "environment_session_join_receipt": (environment_session_join_receipt),
                "environment_navigation": environment_navigation_state,
            },
        )
        return InterfaceEnterEnvironmentResponse(
            request_id=uuid4(),
            namespace=namespace,
            environment_admission=environment_admission,
            environment_admission_receipt=resolved_admission_receipt,
            environment_session=environment_session,
            environment_session_join_receipt=environment_session_join_receipt,
            environment_navigation_context=environment_navigation_context,
            default_navigation_receipt=default_navigation_receipt,
            environment_session_state=environment_session_state,
            environment_navigation_state=environment_navigation_state,
            host_state=host_state,
        )

    async def resolve_experience_lens(
        self,
        *,
        namespace: str,
        environment_session_join_receipt: object | None = None,
        environment_navigation_context: object | None = None,
        experience_actor_admission: object | None = None,
        experience_identity_session_config_id: UUID | None = None,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> InterfaceResolveExperienceLensResponse:
        self.requests.append(
            {
                "operation": "interface_resolve_experience_lens",
                "namespace": namespace,
                "environment_session_join_receipt": environment_session_join_receipt,
                "environment_navigation_context": environment_navigation_context,
                "experience_actor_admission": experience_actor_admission,
                "experience_identity_session_config_id": (
                    experience_identity_session_config_id
                ),
                "reason": reason,
                "evidence": dict(evidence or {}),
            }
        )
        session_join = (
            environment_session_join_receipt
            if isinstance(
                environment_session_join_receipt,
                EnvironmentSessionJoinReceipt,
            )
            else None
        )
        navigation = (
            environment_navigation_context
            if isinstance(
                environment_navigation_context,
                EnvironmentNavigationContextView,
            )
            else None
        )
        host_state = _host_state(namespace)
        environment_session = (
            InterfaceEnvironmentSessionState(
                status=session_join.status,
                accepted=session_join.accepted,
                actor_id=session_join.actor_id,
                environment_id=session_join.environment_id,
                environment_profile_id=session_join.environment_profile_id,
                environment_session_id=session_join.environment_session_id,
                environment_session_key=session_join.environment_session_key,
                evidence={"source": "fake-control-client"},
            )
            if session_join is not None
            else None
        )
        environment_navigation = (
            InterfaceEnvironmentNavigationState(
                status=navigation.status,
                accepted=navigation.status == "active",
                actor_id=session_join.actor_id if session_join is not None else None,
                environment_id=navigation.environment_id,
                environment_session_id=navigation.environment_session_id,
                environment_navigation_context_id=(
                    navigation.environment_navigation_context_id
                ),
                key=navigation.key,
                root_object_id=navigation.root_object_id,
                evidence={"source": "fake-control-client"},
            )
            if navigation is not None
            else None
        )
        experience_lens = InterfaceExperienceLensState(
            status="resolved",
            accepted=True,
            actor_id=session_join.actor_id if session_join is not None else None,
            environment_id=(
                navigation.environment_id
                if navigation is not None
                else (session_join.environment_id if session_join is not None else None)
            ),
            environment_session_id=(
                session_join.environment_session_id
                if session_join is not None
                else None
            ),
            environment_navigation_context_id=(
                navigation.environment_navigation_context_id
                if navigation is not None
                else None
            ),
            experience_name=(
                experience_actor_admission.experience_name
                if isinstance(
                    experience_actor_admission,
                    ExperienceActorConfigAdmissionReceipt,
                )
                else None
            ),
            view_ref="aware_conversations.chat.home.v1",
            section_key="conversation",
            action_count=0,
            evidence={"source": "fake-control-client"},
        )
        host_state = host_state.model_copy(
            update={
                "environment_session": environment_session,
                "environment_session_join_receipt": session_join,
                "environment_navigation": environment_navigation,
                "experience_lens": experience_lens,
            },
        )
        return InterfaceResolveExperienceLensResponse(
            request_id=uuid4(),
            namespace=namespace,
            environment_session=environment_session,
            environment_navigation=environment_navigation,
            experience_lens=experience_lens,
            host_state=host_state,
        )

    async def enter_app_screen(
        self,
        *,
        namespace: str,
        app_package_id: UUID,
        app_package_branch_id: UUID,
        app_package_object_instance_graph_commit_id: UUID,
        app_config_screen_config_id: UUID,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> InterfaceEnterAppScreenResponse:
        self.requests.append(
            {
                "operation": "interface_enter_app_screen",
                "namespace": namespace,
                "app_package_id": app_package_id,
                "app_package_branch_id": app_package_branch_id,
                "app_package_object_instance_graph_commit_id": (
                    app_package_object_instance_graph_commit_id
                ),
                "app_config_screen_config_id": app_config_screen_config_id,
                "reason": reason,
                "evidence": dict(evidence or {}),
            }
        )
        app_screen = InterfaceAppScreenState(
            status="resolved",
            accepted=True,
            app_package_id=app_package_id,
            app_package_branch_id=app_package_branch_id,
            app_package_object_instance_graph_commit_id=(
                app_package_object_instance_graph_commit_id
            ),
            app_config_screen_config_id=app_config_screen_config_id,
            screen_key="home",
            experience_name="home_story",
            layout_binding_key="configuration_map",
        )
        host_state = _host_state(namespace).model_copy(
            update={"app_screen": app_screen},
        )
        return InterfaceEnterAppScreenResponse(
            request_id=uuid4(),
            namespace=namespace,
            app_screen=app_screen,
            host_state=host_state,
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
    ) -> InterfaceRequestWindowLayoutResponse:
        self.requests.append(
            {
                "operation": "interface_request_window_layout",
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
        )
        return InterfaceRequestWindowLayoutResponse(
            request_id=uuid4(),
            namespace=namespace,
            interface_package_id=interface_package_id,
            interface_package_name=interface_package_name,
            window_key=window_key,
            layout_config_id=layout_config_id,
            layout_key=layout_key,
            section_key=section_key,
            observable_id=observable_id,
            representation_id=representation_id,
            requested_by_service=requested_by_service,
            requested_by_operation=requested_by_operation,
            reason=reason,
            idempotency_key=idempotency_key,
            host_state=_host_state(namespace),
        )

    async def apply_attention_layout_transition(
        self,
        *,
        namespace: str,
        client_intent_id: str,
        expected_previous_layout_transition_id: UUID | None,
        topology_transition_id: UUID | None,
        section_states: list[InterfaceAttentionLayoutTransitionSectionIntent],
    ) -> InterfaceApplyAttentionLayoutTransitionResponse:
        self.requests.append(
            {
                "operation": "interface_apply_attention_layout_transition",
                "namespace": namespace,
                "client_intent_id": client_intent_id,
                "expected_previous_layout_transition_id": (
                    expected_previous_layout_transition_id
                ),
                "topology_transition_id": topology_transition_id,
                "section_states": section_states,
            }
        )
        return InterfaceApplyAttentionLayoutTransitionResponse(
            request_id=uuid4(),
            namespace=namespace,
            outcome="committed",
            active_layout_transition_id=uuid4(),
            object_instance_graph_commit_id=uuid4(),
            graph_hash_post="sha256:layout",
            host_state=_host_state(namespace),
        )

    async def apply_attention_layout_topology_transition(
        self,
        *,
        namespace: str,
        client_intent_id: str,
        expected_previous_topology_transition_id: UUID | None,
        section_states: list[InterfaceAttentionLayoutTopologyTransitionSectionIntent],
    ) -> InterfaceApplyAttentionLayoutTopologyTransitionResponse:
        self.requests.append(
            {
                "operation": ("interface_apply_attention_layout_topology_transition"),
                "namespace": namespace,
                "client_intent_id": client_intent_id,
                "expected_previous_topology_transition_id": (
                    expected_previous_topology_transition_id
                ),
                "section_states": section_states,
            }
        )
        return InterfaceApplyAttentionLayoutTopologyTransitionResponse(
            request_id=uuid4(),
            namespace=namespace,
            outcome="committed",
            active_topology_transition_id=uuid4(),
            object_instance_graph_commit_id=uuid4(),
            graph_hash_post="sha256:topology",
            host_state=_host_state(namespace),
        )

    async def invoke_api(self, **kwargs: Any) -> InterfaceInvokeApiResponse:
        self.requests.append(
            {
                "operation": "interface_invoke_api",
                "namespace": str(kwargs["namespace"]),
                "endpoint_ref": str(kwargs["endpoint_ref"]),
                "discriminant": str(kwargs["discriminant"]),
                "request_payload": dict(kwargs.get("request_payload") or {}),
            }
        )
        return InterfaceInvokeApiResponse(
            request_id=uuid4(),
            namespace=str(kwargs["namespace"]),
            endpoint_ref=str(kwargs["endpoint_ref"]),
            discriminant=str(kwargs["discriminant"]),
            service_status="ok",
            response_payload={
                "resolved": True,
                "request_payload": dict(kwargs.get("request_payload") or {}),
            },
        )

    async def action(
        self,
        *,
        namespace: str,
        pane_ref: str | None = None,
        action_key: str,
        payload: dict[str, object] | None = None,
    ) -> InterfaceActionResponse:
        self.requests.append(
            {
                "operation": "interface_action",
                "namespace": namespace,
                "pane_ref": pane_ref,
                "action_key": action_key,
                "payload": dict(payload or {}),
            }
        )
        return InterfaceActionResponse(
            request_id=uuid4(),
            namespace=namespace,
            pane_ref=pane_ref,
            action_key=action_key,
            host_state=_host_state(namespace),
        )

    async def follow(
        self,
        *,
        namespace: str,
        poll_interval_ms: int = 1000,
    ) -> AsyncIterator[InterfaceHostState]:
        _ = poll_interval_ms
        yield _host_state(namespace)


class _NarratingInterfaceControlClient(_FakeInterfaceControlClient):
    def __init__(
        self,
        *,
        commit_id: UUID,
        branch_id: UUID,
        actor_id: UUID,
    ) -> None:
        super().__init__()
        self.commit_id = commit_id
        self.branch_id = branch_id
        self.actor_id = actor_id

    async def status(self, *, namespace: str) -> InterfaceStatusResponse:
        self.requests.append({"operation": "interface_status", "namespace": namespace})
        return InterfaceStatusResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=_host_state_with_narration(
                namespace,
                commit_id=self.commit_id,
                branch_id=self.branch_id,
                actor_id=self.actor_id,
            ),
        )


class _UnavailableInterfaceControlClient(_FakeInterfaceControlClient):
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
        _ = (
            namespace,
            auth_token,
            endpoint,
            host_label,
            environment_config_id,
            interface_package_id,
            interface_package_name,
        )
        raise FileNotFoundError("No such file or directory")

    async def status(self, *, namespace: str) -> InterfaceStatusResponse:
        _ = namespace
        raise FileNotFoundError("No such file or directory")


class _BootstrapInterfaceControlClient(_FakeInterfaceControlClient):
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
        _ = auth_token, endpoint, host_label, environment_config_id
        self.requests.append(
            _namespace_ensure_record(
                namespace,
                interface_package_id=interface_package_id,
                interface_package_name=interface_package_name,
            )
        )
        return NamespaceEnsureResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=_bootstrap_host_state(namespace),
        )

    async def status(self, *, namespace: str) -> InterfaceStatusResponse:
        self.requests.append({"operation": "interface_status", "namespace": namespace})
        return InterfaceStatusResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=_bootstrap_host_state(namespace),
        )


class _ActorlessInterfaceAdmissionControlClient(_FakeInterfaceControlClient):
    def __init__(
        self,
        *,
        interface_id: UUID,
        interface_session_id: UUID,
    ) -> None:
        super().__init__()
        self.interface_id = interface_id
        self.interface_session_id = interface_session_id

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
        _ = auth_token, endpoint, host_label, environment_config_id
        self.requests.append(
            _namespace_ensure_record(
                namespace,
                interface_package_id=interface_package_id,
                interface_package_name=interface_package_name,
            )
        )
        return NamespaceEnsureResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=InterfaceHostState(
                host_label=f"interface-{namespace}",
                namespace=namespace,
                endpoint="mock://interface",
                started=True,
                transport=InterfaceTransportState(
                    available=True,
                    registered=True,
                    authenticated=False,
                    actor_id=None,
                    interface_id=self.interface_id,
                    interface_session_id=self.interface_session_id,
                    session_label=f"interface-{namespace}",
                    capabilities=["interface.api"],
                ),
                allowed_actions=[
                    InterfaceAllowedAction(
                        action_key=action_key,
                        label=action_key.removeprefix("interface_admission.").replace(
                            "_", " "
                        ),
                        enabled=False,
                        payload_schema_hint="{interface_id?: uuid}",
                    )
                    for action_key in _INTERFACE_ADMISSION_ACTION_KEYS
                ],
            ),
        )


class _LocalRuntimeGateInterfaceControlClient(_FakeInterfaceControlClient):
    def __init__(self, *, gate: str) -> None:
        super().__init__()
        self._gate = gate

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
        _ = auth_token, endpoint, host_label, environment_config_id
        self.requests.append(
            _namespace_ensure_record(
                namespace,
                interface_package_id=interface_package_id,
                interface_package_name=interface_package_name,
            )
        )
        return NamespaceEnsureResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=_local_runtime_gate_host_state(namespace, gate=self._gate),
        )

    async def status(self, *, namespace: str) -> InterfaceStatusResponse:
        self.requests.append({"operation": "interface_status", "namespace": namespace})
        return InterfaceStatusResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=_local_runtime_gate_host_state(namespace, gate=self._gate),
        )

    async def action(
        self,
        *,
        namespace: str,
        pane_ref: str | None = None,
        action_key: str,
        payload: dict[str, object] | None = None,
    ) -> InterfaceActionResponse:
        self.requests.append(
            {
                "operation": "interface_action",
                "namespace": namespace,
                "pane_ref": pane_ref,
                "action_key": action_key,
                "payload": dict(payload or {}),
            }
        )
        node_ready = action_key == "ensure_local_node_runtime_started"
        return InterfaceActionResponse(
            request_id=uuid4(),
            namespace=namespace,
            pane_ref=pane_ref,
            action_key=action_key,
            host_state=_local_runtime_gate_host_state(
                namespace,
                gate=self._gate,
                node_ready=node_ready,
            ),
        )


class _AwareControlInterfaceControlClient(_FakeInterfaceControlClient):
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
        _ = auth_token, endpoint, host_label, environment_config_id
        self.requests.append(
            _namespace_ensure_record(
                namespace,
                interface_package_id=interface_package_id,
                interface_package_name=interface_package_name,
            )
        )
        return NamespaceEnsureResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=_aware_control_host_state(namespace),
        )

    async def status(self, *, namespace: str) -> InterfaceStatusResponse:
        self.requests.append({"operation": "interface_status", "namespace": namespace})
        return InterfaceStatusResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=_aware_control_host_state(namespace),
        )

    async def action(
        self,
        *,
        namespace: str,
        pane_ref: str | None = None,
        action_key: str,
        payload: dict[str, object] | None = None,
    ) -> InterfaceActionResponse:
        self.requests.append(
            {
                "operation": "interface_action",
                "namespace": namespace,
                "pane_ref": pane_ref,
                "action_key": action_key,
                "payload": dict(payload or {}),
            }
        )
        return InterfaceActionResponse(
            request_id=uuid4(),
            namespace=namespace,
            pane_ref=pane_ref,
            action_key=action_key,
            host_state=_aware_control_host_state(namespace),
        )


def _host_state(namespace: str) -> InterfaceHostState:
    return InterfaceHostState(
        host_label=f"interface-{namespace}",
        namespace=namespace,
        endpoint="https://interface.example",
        started=True,
        current_screen=InterfaceCurrentScreen(
            screen_kind="hub",
            screen_key="code_packages",
            source_kind="pane",
            title="Hub Code Packages",
            pane_key="hub",
        ),
        transport=InterfaceTransportState(
            available=True,
            registered=True,
            authenticated=True,
            actor_id=uuid4(),
            interface_id=uuid4(),
            interface_session_id=uuid4(),
            session_label=f"interface-{namespace}",
            capabilities=["interface.api"],
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
            resolved_panes=[
                InterfaceResolvedPaneDescriptor(
                    window_key="home",
                    layout_key="main",
                    section_key="hub",
                    pane_kind="hub_code_package",
                    pane_package_name="aware-hub-code-package-pane",
                    title="Hub",
                    summary="Resolve CodePackage artifacts",
                    state_source_kind="api",
                )
            ],
        ),
    )


def _host_state_with_narration(
    namespace: str,
    *,
    commit_id: UUID,
    branch_id: UUID,
    actor_id: UUID,
) -> InterfaceHostState:
    return _host_state(namespace).model_copy(
        update={
            "experience_session_narration": InterfaceExperienceSessionNarrationState(
                status="active",
                feature_key="experience_session_narrator",
                experience_name="my_home",
                view_ref="my_home.lane",
                actor_id=actor_id,
                event_count=1,
                last_commit_id=commit_id,
                events=[
                    InterfaceExperienceSessionNarrationEventState(
                        commit_id=commit_id,
                        branch_id=branch_id,
                        projection_hash="projection:lane",
                        narration_lines=["my_home lane status changed"],
                        operation_label="Task.status = done",
                        semantics={"class_name": "Task"},
                    )
                ],
                evidence={"provider": "generated_interface_dto"},
            )
        }
    )


def _aware_control_host_state(namespace: str) -> InterfaceHostState:
    return InterfaceHostState(
        host_label=f"interface-{namespace}",
        namespace=namespace,
        endpoint="http://127.0.0.1:9000",
        started=True,
        current_screen=InterfaceCurrentScreen(
            screen_kind="control",
            screen_key="aware_control",
            source_kind="pane",
            title="Aware Control",
            pane_key="hub_package_selector",
        ),
        transport=InterfaceTransportState(
            available=True,
            registered=True,
            authenticated=True,
            actor_id=uuid4(),
            interface_id=uuid4(),
            interface_session_id=uuid4(),
            session_label=f"interface-{namespace}",
            capabilities=["interface.actions"],
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
            resolved_view=InterfaceResolvedView(
                experience_key="aware_hub",
                projection_view_id="home.channel_heads.v1",
                interface_package_name="aware-control-interface",
            ),
            resolved_panes=[
                InterfaceResolvedPaneDescriptor(
                    window_key="main",
                    layout_key="coordination_center",
                    section_key="primary",
                    pane_kind="hub_package_selector",
                    pane_package_name="aware-hub-package-selector-pane",
                    title="Hub Discovery",
                    summary="Resolve CodePackage artifacts",
                    state_source_kind="api",
                    action_keys=["api:hub.code_package.search"],
                )
            ],
        ),
    )


def _bootstrap_host_state(namespace: str) -> InterfaceHostState:
    return InterfaceHostState(
        host_label=f"interface-{namespace}",
        namespace=namespace,
        endpoint="http://127.0.0.1:9000",
        started=True,
        current_screen=InterfaceCurrentScreen(
            screen_kind="gate",
            screen_key="identity_auth_gate",
            source_kind="gate",
            title="Identity/Auth Required",
            message=(
                "Identity admission requires an Interface transport session bound "
                "to a node endpoint."
            ),
            pane_key="identity_auth_gate",
        ),
        transport=InterfaceTransportState(
            available=False,
            registered=False,
            authenticated=False,
            capabilities=[],
        ),
        runtime=InterfaceRuntimeState(
            backend=InterfaceBackendState(
                available=False,
                database_exists=False,
                opg_count=0,
                projection_bundle_available=False,
                projection_plan_count=0,
                table_count=0,
                reason="interface_host_bootstrap_panes",
            ),
            resolved_view=InterfaceResolvedView(
                experience_key="aware.interface.bootstrap",
                projection_view_id="entry.control-plane",
            ),
            resolved_panes=[
                InterfaceResolvedPaneDescriptor(
                    window_key="bootstrap",
                    layout_key="bootstrap.panes",
                    section_key="identity_auth_gate",
                    pane_kind="identity_auth_gate",
                    title="Identity/Auth Required",
                    summary=(
                        "Identity admission requires an Interface transport "
                        "session bound to a node endpoint."
                    ),
                    narrative_key="bootstrap.panes.identity_auth_gate",
                    state_source_kind="host_pane_contribution",
                    state_projection_hash="section:bootstrap.panes:identity_auth_gate",
                    action_keys=["signup_via_profile"],
                )
            ],
            warnings=["interface_host_bootstrap_panes"],
        ),
        warnings=["identity_auth_required"],
    )


def _local_runtime_gate_host_state(
    namespace: str,
    *,
    gate: str,
    node_ready: bool = False,
) -> InterfaceHostState:
    if gate == "local_service_host_gate":
        action_keys = ["ensure_local_service_host", "restart_local_service_host"]
        title = "Local Service Host Required"
        summary = "Service host bootstrap is required."
        message = "Service host bootstrap is required."
        service_host_ready = False
    elif gate == "local_node_runtime_gate":
        action_keys = [
            "ensure_local_node_runtime_started",
            "restart_local_service_host",
            "tail_local_node_runtime_logs",
        ]
        title = "Local Node Runtime Required"
        summary = "Postgres: database bootstrap pending"
        message = "Postgres: database bootstrap pending"
        service_host_ready = True
    else:
        raise AssertionError(f"Unsupported local runtime gate fixture: {gate}")

    return InterfaceHostState(
        host_label=f"interface-{namespace}",
        namespace=namespace,
        endpoint="http://127.0.0.1:9000",
        started=True,
        current_screen=InterfaceCurrentScreen(
            screen_kind="gate",
            screen_key=gate,
            source_kind="gate",
            title=title,
            message=message,
            pane_key=gate,
        ),
        transport=InterfaceTransportState(
            available=False,
            registered=False,
            authenticated=False,
            capabilities=[],
        ),
        local_service_host=InterfaceLocalServiceHostState(
            managed=True,
            supported=True,
            available=service_host_ready,
            ready=service_host_ready,
            status="ready" if service_host_ready else "absent",
            socket_path="/tmp/aware-service-host.sock",
            capabilities=["service.host"],
        ),
        local_node_runtime=(
            InterfaceLocalNodeRuntimeState(
                managed=True,
                available=service_host_ready,
                ready=node_ready,
                phase="ready" if node_ready else "start_db",
                active_target_id="postgres",
                target_key="postgres",
                display_name="Postgres",
                backend_kind="postgres",
                is_active=service_host_ready and not node_ready,
                is_healthy=node_ready,
                summary="Node runtime ready." if node_ready else summary,
            )
            if gate == "local_node_runtime_gate"
            else None
        ),
        runtime=InterfaceRuntimeState(
            backend=InterfaceBackendState(
                available=False,
                database_exists=False,
                opg_count=0,
                projection_bundle_available=False,
                projection_plan_count=0,
                table_count=0,
                reason="interface_host_bootstrap_panes",
            ),
            resolved_view=InterfaceResolvedView(
                experience_key="aware.interface.bootstrap",
                projection_view_id="entry.control-plane",
            ),
            resolved_panes=[
                InterfaceResolvedPaneDescriptor(
                    window_key="bootstrap",
                    layout_key="bootstrap.panes",
                    section_key=gate,
                    pane_kind=gate,
                    title=title,
                    summary=summary,
                    narrative_key=f"bootstrap.panes.{gate}",
                    state_source_kind="host_pane_contribution",
                    state_projection_hash=f"section:bootstrap.panes:{gate}",
                    action_keys=action_keys,
                )
            ],
            warnings=["interface_host_bootstrap_panes"],
        ),
        allowed_actions=[
            InterfaceAllowedAction(action_key=action_key, label=action_key)
            for action_key in action_keys
        ],
        warnings=[
            (
                "local_node_runtime_required"
                if gate == "local_node_runtime_gate"
                else "local_service_host_required"
            )
        ],
    )
