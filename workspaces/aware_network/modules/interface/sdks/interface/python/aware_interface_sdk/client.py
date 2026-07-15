from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Mapping
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Protocol, TypeVar, cast
from uuid import UUID

from pydantic import BaseModel

from aware_types import JsonObject
from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt,
    EnvironmentNavigationContextView,
    EnvironmentSessionJoinReceipt,
)
from aware_experience_service_dto.experience.actor_admission.models import (
    ExperienceActorConfigAdmissionReceipt,
)
from aware_interface_service_api import AwareInterfaceServiceApiClient
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceAdmitEnvironmentActorRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceAdmitEnvironmentActorResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceApplyAttentionLayoutTransitionRequest,
    InterfaceApplyAttentionLayoutTransitionResponse,
    InterfaceApplyAttentionLayoutTopologyTransitionRequest,
    InterfaceApplyAttentionLayoutTopologyTransitionResponse,
    InterfaceAttentionLayoutTransitionSectionIntent,
    InterfaceAttentionLayoutTopologyTransitionSectionIntent,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceActionRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceActionResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceFollowRequest,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceHostState,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceInvokeApiRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceInvokeApiResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceJoinEnvironmentSessionRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceJoinEnvironmentSessionResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceExperienceSessionMountRequest,
    InterfaceExperienceSessionMountResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceSessionStartRequest,
    InterfaceSessionStartResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceSessionDescribeRequest,
    InterfaceSessionDescribeResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceEnterEnvironmentRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceEnterEnvironmentResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceEnterAppScreenRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceEnterAppScreenResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceRequestWindowLayoutRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceRequestWindowLayoutResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceResolveExperienceLensRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceResolveExperienceLensResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceSelectStepRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceSelectStepResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceSelectProfileRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceSelectProfileResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceStatusRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceStatusResponse,
)
from aware_interface_service_dto.comms.models.control_plane import InterfaceStopRequest
from aware_interface_service_dto.comms.models.control_plane import InterfaceStopResponse
from aware_interface_service_dto.comms.models.control_plane import (
    NamespaceEnsureRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    NamespaceEnsureResponse,
)
from aware_interface_service_dto.comms.models.control_plane import NamespaceListRequest
from aware_interface_service_dto.comms.models.control_plane import NamespaceListResponse
from aware_interface_service_dto.comms.models.control_plane import PingRequest
from aware_interface_service_dto.comms.models.control_plane import PingResponse

from aware_interface_sdk.models import InterfaceSurfaceSnapshot


JsonPayload = Mapping[str, object] | JsonObject


def _json_object(value: JsonPayload | None = None) -> JsonObject:
    if value is None:
        return JsonObject()
    if isinstance(value, JsonObject):
        return value
    return JsonObject(cast(dict[str, Any], dict(value)))


def _object_payload(value: JsonPayload | None = None) -> dict[str, object]:
    if value is None:
        return {}
    return cast(dict[str, object], dict(value))


def _resolve_local_service_host_path(
    value: str | Path | None,
    *,
    env_names: tuple[str, ...],
) -> Path | None:
    if value is not None:
        return Path(value).expanduser().resolve()
    for env_name in env_names:
        env_value = str(os.environ.get(env_name) or "").strip()
        if env_value:
            return Path(env_value).expanduser().resolve()
    return None


def _local_service_host_invocation_context(
    actor_id: UUID | None,
    *,
    source: str | None = None,
) -> dict[str, object] | None:
    if actor_id is None:
        return None
    return {
        "actor_context": {
            "status": "ready",
            "kind": "agent_operator",
            "source": source or "interface_sdk.local_host.runtime_auth",
            "actor_id": str(actor_id),
        }
    }


class InterfaceControlClient(Protocol):
    async def ping(self) -> Any: ...

    async def list_namespaces(self) -> Any: ...

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
    ) -> Any: ...

    async def select_step(
        self,
        *,
        namespace: str,
        step_id: str | None,
    ) -> Any: ...

    async def select_profile(
        self,
        *,
        namespace: str,
        profile_id: str,
    ) -> Any: ...

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
    ) -> Any: ...

    async def apply_attention_layout_transition(
        self,
        *,
        namespace: str,
        client_intent_id: str,
        expected_previous_layout_transition_id: UUID | None,
        topology_transition_id: UUID | None,
        section_states: list[InterfaceAttentionLayoutTransitionSectionIntent],
    ) -> Any: ...

    async def apply_attention_layout_topology_transition(
        self,
        *,
        namespace: str,
        client_intent_id: str,
        expected_previous_topology_transition_id: UUID | None,
        section_states: list[InterfaceAttentionLayoutTopologyTransitionSectionIntent],
    ) -> Any: ...

    async def status(self, *, namespace: str) -> Any: ...

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
    ) -> Any: ...

    async def join_environment_session(
        self,
        *,
        namespace: str,
        environment_session_id: UUID,
        environment_profile_id: UUID | None = None,
        environment_admission_receipt: EnvironmentActorAdmissionReceipt | None = None,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> Any: ...

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
    ) -> Any: ...

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
    ) -> Any: ...

    async def resolve_experience_lens(
        self,
        *,
        namespace: str,
        environment_session_join_receipt: EnvironmentSessionJoinReceipt | None = None,
        environment_navigation_context: EnvironmentNavigationContextView | None = None,
        experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None = None,
        experience_identity_session_config_id: UUID | None = None,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> Any: ...

    async def stop(self, *, namespace: str) -> Any: ...

    async def invoke_api(
        self,
        *,
        namespace: str,
        endpoint_ref: str,
        discriminant: str | None = None,
        request_payload: dict[str, object] | None = None,
    ) -> Any: ...

    async def action(
        self,
        *,
        namespace: str,
        action_key: str,
        pane_ref: str | None = None,
        payload: dict[str, object] | None = None,
    ) -> Any: ...

    def follow(
        self,
        *,
        namespace: str,
        poll_interval_ms: int = 1000,
    ) -> AsyncIterator[Any]: ...


_T = TypeVar("_T")


class InterfaceSdkError(RuntimeError):
    pass


class InterfaceHostUnavailableError(InterfaceSdkError):
    def __init__(
        self,
        *,
        operation: str,
        reason: str,
        details: str,
        socket_path: Path | None = None,
        state_home: Path | None = None,
    ) -> None:
        self.operation = operation
        self.reason = reason
        self.details = details
        self.socket_path = socket_path
        self.state_home = state_home
        super().__init__(f"Interface host unavailable during {operation}: {details}")

    def readiness_payload(
        self,
        *,
        namespace: str,
        command: str,
    ) -> dict[str, object]:
        return {
            "namespace": namespace,
            "command": command,
            "ready": False,
            "status": "interface_host_unavailable",
            "product_boundary": "interface-renderer",
            "canonical_rail": "SDK -> CLI renderer -> Interface -> API -> Services",
            "operation": self.operation,
            "reason": self.reason,
            "message": self.details,
            "socket_path": (
                str(self.socket_path) if self.socket_path is not None else None
            ),
            "state_home": str(self.state_home) if self.state_home is not None else None,
            "next_action": "start_or_provision_interface_host",
            "current_dev_command": "uv run aware-interface-service-host ensure",
        }


class _ControlBackedAwareInterfaceServiceApiClient:
    def __init__(self, *, control_client: InterfaceControlClient) -> None:
        self.interface = _ControlBackedInterfaceApi(control_client=control_client)


class _ControlBackedCapability:
    def __init__(self, api: "_ControlBackedInterfaceApi") -> None:
        self._api = api

    def __getattr__(self, name: str) -> Any:
        return getattr(self._api, f"_{name}")


class _ControlBackedInterfaceApi:
    def __init__(self, *, control_client: InterfaceControlClient) -> None:
        self._control_client = control_client
        capability = _ControlBackedCapability(self)
        self.admit_interface = capability
        self.admit_environment_actor = capability
        self.join_environment_session = capability
        self.enter_environment = capability
        self.enter_app_screen = capability
        self.resolve_experience_lens = capability
        self.get_interface_state = capability
        self.watch_interface_state = capability
        self.perform_interface_action = capability
        self.select_interface_step = capability
        self.select_interface_profile = capability
        self.select_interface_runtime_layout = capability
        self.activate_interface_runtime_focus = capability
        self.request_interface_window_layout = capability
        self.apply_attention_layout_transition = capability
        self.apply_attention_layout_topology_transition = capability
        self.invoke_interface_api = capability
        self.stream_interface_api = capability
        self.report_renderer_capabilities = capability
        self.sync_view_state_cursor = capability
        self.ping_interface_host = capability
        self.list_interface_namespaces = capability
        self.stop_interface_namespace = capability

    async def _ping_interface_host(self, request: PingRequest) -> PingResponse:
        _ = request
        return _coerce_model(await self._control_client.ping(), PingResponse)

    async def _list_interface_namespaces(
        self,
        request: NamespaceListRequest,
    ) -> NamespaceListResponse:
        _ = request
        return _coerce_model(
            await self._control_client.list_namespaces(),
            NamespaceListResponse,
        )

    async def _admit_interface(
        self,
        request: NamespaceEnsureRequest,
    ) -> NamespaceEnsureResponse:
        return _coerce_model(
            await self._control_client.ensure_namespace(
                namespace=request.namespace,
                auth_token=request.auth_token,
                endpoint=request.endpoint,
                host_label=request.host_label,
                environment_config_id=request.environment_config_id,
                interface_package_id=request.interface_package_id,
                interface_package_name=request.interface_package_name,
            ),
            NamespaceEnsureResponse,
        )

    async def _get_interface_state(
        self,
        request: InterfaceStatusRequest,
    ) -> InterfaceStatusResponse:
        return _coerce_model(
            await self._control_client.status(namespace=request.namespace),
            InterfaceStatusResponse,
        )

    async def _apply_attention_layout_transition(
        self,
        request: InterfaceApplyAttentionLayoutTransitionRequest,
    ) -> InterfaceApplyAttentionLayoutTransitionResponse:
        return _coerce_model(
            await self._control_client.apply_attention_layout_transition(
                namespace=request.namespace,
                client_intent_id=request.client_intent_id,
                expected_previous_layout_transition_id=(
                    request.expected_previous_layout_transition_id
                ),
                topology_transition_id=request.topology_transition_id,
                section_states=list(request.section_states),
            ),
            InterfaceApplyAttentionLayoutTransitionResponse,
        )

    async def _apply_attention_layout_topology_transition(
        self,
        request: InterfaceApplyAttentionLayoutTopologyTransitionRequest,
    ) -> InterfaceApplyAttentionLayoutTopologyTransitionResponse:
        return _coerce_model(
            await self._control_client.apply_attention_layout_topology_transition(
                namespace=request.namespace,
                client_intent_id=request.client_intent_id,
                expected_previous_topology_transition_id=(
                    request.expected_previous_topology_transition_id
                ),
                section_states=list(request.section_states),
            ),
            InterfaceApplyAttentionLayoutTopologyTransitionResponse,
        )

    async def _admit_environment_actor(
        self,
        request: InterfaceAdmitEnvironmentActorRequest,
    ) -> InterfaceAdmitEnvironmentActorResponse:
        return _coerce_model(
            await self._control_client.admit_environment_actor(
                namespace=request.namespace,
                environment_id=request.environment_id,
                environment_profile_id=request.environment_profile_id,
                actor_config_id=request.actor_config_id,
                class_instance_identity_id=request.class_instance_identity_id,
                object_instance_graph_branch_key=(
                    request.object_instance_graph_branch_key
                ),
                object_instance_graph_branch_id=(
                    request.object_instance_graph_branch_id
                ),
                requested_role_config_ids=list(request.requested_role_config_ids),
                requested_role_config_names=list(request.requested_role_config_names),
                reason=request.reason,
                evidence=_object_payload(request.evidence),
            ),
            InterfaceAdmitEnvironmentActorResponse,
        )

    async def _join_environment_session(
        self,
        request: InterfaceJoinEnvironmentSessionRequest,
    ) -> InterfaceJoinEnvironmentSessionResponse:
        return _coerce_model(
            await self._control_client.join_environment_session(
                namespace=request.namespace,
                environment_session_id=request.environment_session_id,
                environment_profile_id=request.environment_profile_id,
                environment_admission_receipt=request.environment_admission_receipt,
                reason=request.reason,
                evidence=_object_payload(request.evidence),
            ),
            InterfaceJoinEnvironmentSessionResponse,
        )

    async def _enter_environment(
        self,
        request: InterfaceEnterEnvironmentRequest,
    ) -> InterfaceEnterEnvironmentResponse:
        return _coerce_model(
            await self._control_client.enter_environment(
                namespace=request.namespace,
                environment_id=request.environment_id,
                environment_profile_id=request.environment_profile_id,
                actor_config_id=request.actor_config_id,
                class_instance_identity_id=request.class_instance_identity_id,
                object_instance_graph_branch_key=(
                    request.object_instance_graph_branch_key
                ),
                object_instance_graph_branch_id=(
                    request.object_instance_graph_branch_id
                ),
                requested_role_config_ids=list(request.requested_role_config_ids),
                requested_role_config_names=list(request.requested_role_config_names),
                environment_admission_receipt=request.environment_admission_receipt,
                environment_session_id=request.environment_session_id,
                environment_session_config_id=request.environment_session_config_id,
                session_key=request.session_key,
                title=request.title,
                description=request.description,
                purpose=request.purpose,
                source_kind=request.source_kind,
                source_ref=request.source_ref,
                reason=request.reason,
                evidence=_object_payload(request.evidence),
            ),
            InterfaceEnterEnvironmentResponse,
        )

    async def _enter_app_screen(
        self,
        request: InterfaceEnterAppScreenRequest,
    ) -> InterfaceEnterAppScreenResponse:
        return _coerce_model(
            await self._control_client.enter_app_screen(
                namespace=request.namespace,
                app_package_id=request.app_package_id,
                app_package_branch_id=request.app_package_branch_id,
                app_package_object_instance_graph_commit_id=(
                    request.app_package_object_instance_graph_commit_id
                ),
                app_config_screen_config_id=request.app_config_screen_config_id,
                reason=request.reason,
                evidence=_object_payload(request.evidence),
            ),
            InterfaceEnterAppScreenResponse,
        )

    async def _resolve_experience_lens(
        self,
        request: InterfaceResolveExperienceLensRequest,
    ) -> InterfaceResolveExperienceLensResponse:
        return _coerce_model(
            await self._control_client.resolve_experience_lens(
                namespace=request.namespace,
                environment_session_join_receipt=(
                    request.environment_session_join_receipt
                ),
                environment_navigation_context=(request.environment_navigation_context),
                experience_actor_admission=request.experience_actor_admission,
                experience_identity_session_config_id=(
                    request.experience_identity_session_config_id
                ),
                reason=request.reason,
                evidence=_object_payload(request.evidence),
            ),
            InterfaceResolveExperienceLensResponse,
        )

    async def _stop_interface_namespace(
        self,
        request: InterfaceStopRequest,
    ) -> InterfaceStopResponse:
        return _coerce_model(
            await self._control_client.stop(namespace=request.namespace),
            InterfaceStopResponse,
        )

    async def _select_interface_step(
        self,
        request: InterfaceSelectStepRequest,
    ) -> InterfaceSelectStepResponse:
        return _coerce_model(
            await self._control_client.select_step(
                namespace=request.namespace,
                step_id=request.step_id,
            ),
            InterfaceSelectStepResponse,
        )

    async def _select_interface_profile(
        self,
        request: InterfaceSelectProfileRequest,
    ) -> InterfaceSelectProfileResponse:
        return _coerce_model(
            await self._control_client.select_profile(
                namespace=request.namespace,
                profile_id=request.profile_id,
            ),
            InterfaceSelectProfileResponse,
        )

    async def _request_interface_window_layout(
        self,
        request: InterfaceRequestWindowLayoutRequest,
    ) -> InterfaceRequestWindowLayoutResponse:
        return _coerce_model(
            await self._control_client.request_window_layout(
                namespace=request.namespace,
                interface_package_id=request.interface_package_id,
                interface_package_name=request.interface_package_name,
                window_key=request.window_key,
                layout_config_id=request.layout_config_id,
                layout_key=request.layout_key,
                section_key=request.section_key,
                observable_id=request.observable_id,
                representation_id=request.representation_id,
                requested_by_service=request.requested_by_service,
                requested_by_operation=request.requested_by_operation,
                reason=request.reason,
                idempotency_key=request.idempotency_key,
            ),
            InterfaceRequestWindowLayoutResponse,
        )

    async def _invoke_interface_api(
        self,
        request: InterfaceInvokeApiRequest,
    ) -> InterfaceInvokeApiResponse:
        return _coerce_model(
            await self._control_client.invoke_api(
                namespace=request.namespace,
                endpoint_ref=request.endpoint_ref,
                discriminant=request.discriminant,
                request_payload=_object_payload(request.request_payload),
            ),
            InterfaceInvokeApiResponse,
        )

    async def _perform_interface_action(
        self,
        request: InterfaceActionRequest,
    ) -> InterfaceActionResponse:
        return _coerce_model(
            await self._control_client.action(
                namespace=request.namespace,
                pane_ref=request.pane_ref,
                action_key=request.action_key,
                payload=_object_payload(request.payload),
            ),
            InterfaceActionResponse,
        )

    def _stream_watch_interface_state(
        self,
        request: InterfaceFollowRequest,
    ) -> AsyncIterator[Any]:
        return self._control_client.follow(
            namespace=request.namespace,
            poll_interval_ms=request.poll_interval_ms,
        )


@dataclass(frozen=True, slots=True)
class InterfaceSdkClient:
    control_client: InterfaceControlClient | None = None
    service_client: AwareInterfaceServiceApiClient | Any | None = None
    socket_path: Path | None = None
    state_home: Path | None = None

    def __post_init__(self) -> None:
        if self.service_client is not None:
            return
        if self.control_client is None:
            raise ValueError(
                "InterfaceSdkClient requires a canonical service_client or a "
                "local control_client transport adapter."
            )
        object.__setattr__(
            self,
            "service_client",
            _ControlBackedAwareInterfaceServiceApiClient(
                control_client=self.control_client,
            ),
        )

    @classmethod
    def from_service_api(
        cls,
        service_client: AwareInterfaceServiceApiClient,
    ) -> "InterfaceSdkClient":
        return cls(service_client=service_client)

    @classmethod
    def from_local_service_host(
        cls,
        *,
        socket_path: Path | None = None,
        state_home: Path | None = None,
        request_timeout_s: float = 30.0,
        actor_id: UUID | None = None,
        invocation_context: Mapping[str, object] | None = None,
    ) -> "InterfaceSdkClient":
        from aware_interface_service.local_host import (
            build_local_interface_service_host_api_client,
        )
        from aware_interface_sdk.local_host import (
            resolve_local_service_host_actor_context_identity,
        )

        resolved_socket_path = _resolve_local_service_host_path(
            socket_path,
            env_names=(
                "AWARE_INTERFACE_SERVICE_HOST_SOCKET_PATH",
                "AWARE_INTERFACE_SERVICE_SOCKET_PATH",
            ),
        )
        resolved_state_home = _resolve_local_service_host_path(
            state_home,
            env_names=(
                "AWARE_INTERFACE_SERVICE_STATE_HOME",
                "AWARE_STATE_HOME",
            ),
        )
        if actor_id is not None:
            resolved_actor_id = actor_id
            resolved_actor_source = "interface_sdk.local_host.runtime_auth"
        else:
            resolved_actor_id, resolved_actor_source = (
                resolve_local_service_host_actor_context_identity(
                    socket_path=resolved_socket_path,
                    state_home=resolved_state_home,
                )
            )
        resolved_invocation_context = (
            invocation_context
            if invocation_context is not None
            else _local_service_host_invocation_context(
                resolved_actor_id,
                source=resolved_actor_source,
            )
        )
        return cls(
            service_client=build_local_interface_service_host_api_client(
                socket_path=resolved_socket_path,
                actor_id=resolved_actor_id,
                request_timeout_s=request_timeout_s,
                invocation_context=resolved_invocation_context,
            ),
            socket_path=resolved_socket_path,
            state_home=resolved_state_home,
        )

    @classmethod
    def from_local_control(
        cls,
        *,
        socket_path: Path | None = None,
        state_home: Path | None = None,
    ) -> "InterfaceSdkClient":
        from aware_interface_control import InterfaceControlPlaneClient

        control_client = InterfaceControlPlaneClient(
            socket_path=socket_path,
            state_home=state_home,
        )
        return cls(
            control_client=control_client,
            service_client=_ControlBackedAwareInterfaceServiceApiClient(
                control_client=control_client,
            ),
            socket_path=control_client.socket_path,
            state_home=state_home,
        )

    async def ping(self) -> PingResponse:
        return await self._host_call(
            "ping",
            self._api().ping_interface_host.ping_interface_host(PingRequest()),
        )

    async def list_namespaces(self) -> NamespaceListResponse:
        return await self._host_call(
            "namespace_list",
            self._api().list_interface_namespaces.list_interface_namespaces(
                NamespaceListRequest(),
            ),
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
        return await self._host_call(
            "namespace_ensure",
            self._api().admit_interface.admit_interface(
                NamespaceEnsureRequest(
                    namespace=namespace,
                    auth_token=auth_token,
                    endpoint=endpoint,
                    host_label=host_label,
                    environment_config_id=environment_config_id,
                    interface_package_id=interface_package_id,
                    interface_package_name=interface_package_name,
                )
            ),
        )

    async def status(self, *, namespace: str) -> InterfaceStatusResponse:
        return await self._host_call(
            "interface_status",
            self._api().get_interface_state.get_interface_state(
                InterfaceStatusRequest(namespace=namespace),
            ),
        )

    async def start_interface_session(
        self,
        *,
        interface_id: UUID,
        identity_session_id: UUID,
        name: str,
    ) -> InterfaceSessionStartResponse:
        return await self._host_call(
            "interface_session_start",
            self._api().start_interface_session.start_interface_session(
                InterfaceSessionStartRequest(
                    interface_id=interface_id,
                    identity_session_id=identity_session_id,
                    name=name,
                )
            ),
        )

    async def describe_interface_session(
        self,
        *,
        interface_session_id: UUID,
    ) -> InterfaceSessionDescribeResponse:
        return await self._host_call(
            "interface_session_describe",
            self._api().describe_interface_session.describe_interface_session(
                InterfaceSessionDescribeRequest(
                    interface_session_id=interface_session_id,
                )
            ),
        )

    async def mount_interface_experience_session(
        self,
        *,
        interface_session_id: UUID,
        experience_session_id: UUID,
        status: str = "active",
        metadata_json: JsonPayload | None = None,
    ) -> InterfaceExperienceSessionMountResponse:
        return await self._host_call(
            "interface_experience_session_mount",
            self._api().mount_interface_experience_session.mount_interface_experience_session(
                InterfaceExperienceSessionMountRequest(
                    interface_session_id=interface_session_id,
                    experience_session_id=experience_session_id,
                    status=status,
                    metadata_json=_json_object(metadata_json),
                )
            ),
        )

    async def admit_environment_actor(
        self,
        *,
        namespace: str,
        environment_profile_id: UUID,
        actor_config_id: UUID,
        class_instance_identity_id: UUID,
        environment_id: UUID | None = None,
        object_instance_graph_branch_key: str = "all",
        object_instance_graph_branch_id: UUID | None = None,
        requested_role_config_ids: list[UUID] | None = None,
        requested_role_config_names: list[str] | None = None,
        reason: str | None = None,
        evidence: JsonPayload | None = None,
    ) -> InterfaceAdmitEnvironmentActorResponse:
        return await self._host_call(
            "interface_admit_environment_actor",
            self._api().admit_environment_actor.admit_environment_actor(
                InterfaceAdmitEnvironmentActorRequest(
                    namespace=namespace,
                    environment_id=environment_id,
                    environment_profile_id=environment_profile_id,
                    actor_config_id=actor_config_id,
                    class_instance_identity_id=class_instance_identity_id,
                    object_instance_graph_branch_key=object_instance_graph_branch_key,
                    object_instance_graph_branch_id=object_instance_graph_branch_id,
                    requested_role_config_ids=list(requested_role_config_ids or ()),
                    requested_role_config_names=list(requested_role_config_names or ()),
                    reason=reason,
                    evidence=_json_object(evidence),
                ),
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
        evidence: JsonPayload | None = None,
    ) -> InterfaceJoinEnvironmentSessionResponse:
        request = InterfaceJoinEnvironmentSessionRequest(
            namespace=namespace,
            environment_session_id=environment_session_id,
            environment_profile_id=environment_profile_id,
            environment_admission_receipt=environment_admission_receipt,
            reason=reason,
            evidence=_json_object(evidence),
        )
        api = self._api()
        capability = getattr(api, "join_environment_session", None)
        if capability is not None:
            return await self._host_call(
                "interface_join_environment_session",
                capability.join_environment_session(request),
            )
        raw_client = getattr(api, "_client")
        raw_response = await raw_client.invoke_api_endpoint_raw(
            endpoint_ref="interface.join_environment_session.join_environment_session",
            discriminant="interface.join_environment_session.join_environment_session",
            request_payload=request,
        )
        if str(getattr(raw_response, "status", "")) == "failed":
            raise RuntimeError(
                getattr(raw_response, "error", None)
                or "Interface Environment session join failed"
            )
        return InterfaceJoinEnvironmentSessionResponse.model_validate(
            getattr(raw_response, "response_payload", None)
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
        evidence: JsonPayload | None = None,
    ) -> InterfaceEnterEnvironmentResponse:
        request = InterfaceEnterEnvironmentRequest(
            namespace=namespace,
            environment_id=environment_id,
            environment_profile_id=environment_profile_id,
            actor_config_id=actor_config_id,
            class_instance_identity_id=class_instance_identity_id,
            object_instance_graph_branch_key=object_instance_graph_branch_key,
            object_instance_graph_branch_id=object_instance_graph_branch_id,
            requested_role_config_ids=list(requested_role_config_ids or ()),
            requested_role_config_names=list(requested_role_config_names or ()),
            environment_admission_receipt=environment_admission_receipt,
            environment_session_id=environment_session_id,
            environment_session_config_id=environment_session_config_id,
            session_key=session_key,
            title=title,
            description=description,
            purpose=purpose,
            source_kind=source_kind,
            source_ref=source_ref,
            reason=reason,
            evidence=_json_object(evidence),
        )
        api = self._api()
        capability = getattr(api, "enter_environment", None)
        if capability is not None:
            return await self._host_call(
                "interface_enter_environment",
                capability.enter_environment(request),
            )
        raw_client = getattr(api, "_client")
        raw_response = await raw_client.invoke_api_endpoint_raw(
            endpoint_ref="interface.enter_environment.enter_environment",
            discriminant="interface.enter_environment.enter_environment",
            request_payload=request,
        )
        if str(getattr(raw_response, "status", "")) == "failed":
            raise RuntimeError(
                getattr(raw_response, "error", None)
                or "Interface Environment entry failed"
            )
        return InterfaceEnterEnvironmentResponse.model_validate(
            getattr(raw_response, "response_payload", None)
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
        evidence: JsonPayload | None = None,
    ) -> InterfaceEnterAppScreenResponse:
        request = InterfaceEnterAppScreenRequest(
            namespace=namespace,
            app_package_id=app_package_id,
            app_package_branch_id=app_package_branch_id,
            app_package_object_instance_graph_commit_id=(
                app_package_object_instance_graph_commit_id
            ),
            app_config_screen_config_id=app_config_screen_config_id,
            reason=reason,
            evidence=_json_object(evidence),
        )
        capability = getattr(self._api(), "enter_app_screen", None)
        if capability is None:
            raise RuntimeError(
                "Interface SDK package is missing the generated enter_app_screen capability"
            )
        return await self._host_call(
            "interface_enter_app_screen",
            capability.enter_app_screen(request),
        )

    async def resolve_experience_lens(
        self,
        *,
        namespace: str,
        environment_session_join_receipt: EnvironmentSessionJoinReceipt | None = None,
        environment_navigation_context: EnvironmentNavigationContextView | None = None,
        experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None = None,
        experience_identity_session_config_id: UUID | None = None,
        reason: str | None = None,
        evidence: JsonPayload | None = None,
    ) -> InterfaceResolveExperienceLensResponse:
        return await self._host_call(
            "interface_resolve_experience_lens",
            self._api().resolve_experience_lens.resolve_experience_lens(
                InterfaceResolveExperienceLensRequest(
                    namespace=namespace,
                    environment_session_join_receipt=(environment_session_join_receipt),
                    environment_navigation_context=environment_navigation_context,
                    experience_actor_admission=experience_actor_admission,
                    experience_identity_session_config_id=(
                        experience_identity_session_config_id
                    ),
                    reason=reason,
                    evidence=_json_object(evidence),
                ),
            ),
        )

    async def stop(self, *, namespace: str) -> InterfaceStopResponse:
        return await self._host_call(
            "interface_stop",
            self._api().stop_interface_namespace.stop_interface_namespace(
                InterfaceStopRequest(namespace=namespace),
            ),
        )

    async def select_step(
        self,
        *,
        namespace: str,
        step_id: str | None,
    ) -> Any:
        return await self._host_call(
            "interface_select_step",
            self._api().select_interface_step.select_interface_step(
                InterfaceSelectStepRequest(
                    namespace=namespace,
                    step_id=step_id,
                ),
            ),
        )

    async def select_profile(
        self,
        *,
        namespace: str,
        profile_id: str,
    ) -> InterfaceSelectProfileResponse:
        return await self._host_call(
            "interface_select_profile",
            self._api().select_interface_profile.select_interface_profile(
                InterfaceSelectProfileRequest(
                    namespace=namespace,
                    profile_id=profile_id,
                ),
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
        return await self._host_call(
            "interface_request_window_layout",
            self._api().request_interface_window_layout.request_interface_window_layout(
                InterfaceRequestWindowLayoutRequest(
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
                ),
            ),
        )

    async def apply_attention_layout_transition(
        self,
        *,
        namespace: str,
        client_intent_id: str,
        expected_previous_layout_transition_id: UUID | None,
        topology_transition_id: UUID | None = None,
        section_states: list[InterfaceAttentionLayoutTransitionSectionIntent],
    ) -> InterfaceApplyAttentionLayoutTransitionResponse:
        return await self._host_call(
            "interface_apply_attention_layout_transition",
            self._api().apply_attention_layout_transition.apply_attention_layout_transition(
                InterfaceApplyAttentionLayoutTransitionRequest(
                    namespace=namespace,
                    client_intent_id=client_intent_id,
                    expected_previous_layout_transition_id=(
                        expected_previous_layout_transition_id
                    ),
                    topology_transition_id=topology_transition_id,
                    section_states=section_states,
                ),
            ),
        )

    async def apply_attention_layout_topology_transition(
        self,
        *,
        namespace: str,
        client_intent_id: str,
        expected_previous_topology_transition_id: UUID | None,
        section_states: list[InterfaceAttentionLayoutTopologyTransitionSectionIntent],
    ) -> InterfaceApplyAttentionLayoutTopologyTransitionResponse:
        return await self._host_call(
            "interface_apply_attention_layout_topology_transition",
            self._api().apply_attention_layout_topology_transition.apply_attention_layout_topology_transition(
                InterfaceApplyAttentionLayoutTopologyTransitionRequest(
                    namespace=namespace,
                    client_intent_id=client_intent_id,
                    expected_previous_topology_transition_id=(
                        expected_previous_topology_transition_id
                    ),
                    section_states=section_states,
                ),
            ),
        )

    async def status_surface(self, *, namespace: str) -> InterfaceSurfaceSnapshot:
        status = await self.status(namespace=namespace)
        return InterfaceSurfaceSnapshot(
            namespace=status.namespace,
            host_state=status.host_state,
        )

    async def ensure_surface(
        self,
        *,
        namespace: str,
        auth_token: str | None = None,
        endpoint: str | None = None,
        host_label: str | None = None,
        environment_config_id: UUID | None = None,
        interface_package_id: UUID | None = None,
        interface_package_name: str | None = None,
    ) -> InterfaceSurfaceSnapshot:
        ensured = await self.ensure_namespace(
            namespace=namespace,
            auth_token=auth_token,
            endpoint=endpoint,
            host_label=host_label,
            environment_config_id=environment_config_id,
            interface_package_id=interface_package_id,
            interface_package_name=interface_package_name,
        )
        return InterfaceSurfaceSnapshot(
            namespace=ensured.namespace,
            host_state=ensured.host_state,
        )

    async def invoke_pane_capability(
        self,
        *,
        namespace: str,
        pane_ref: str,
        capability_ref: str,
        discriminant: str | None = None,
        request_payload: JsonPayload | None = None,
        ensure_current_surface: bool = True,
        auth_token: str | None = None,
        endpoint: str | None = None,
        host_label: str | None = None,
        environment_config_id: UUID | None = None,
        interface_package_id: UUID | None = None,
        interface_package_name: str | None = None,
    ) -> InterfaceInvokeApiResponse:
        if ensure_current_surface:
            surface = await self.ensure_surface(
                namespace=namespace,
                auth_token=auth_token,
                endpoint=endpoint,
                host_label=host_label,
                environment_config_id=environment_config_id,
                interface_package_id=interface_package_id,
                interface_package_name=interface_package_name,
            )
        else:
            surface = await self.status_surface(namespace=namespace)
        pane = surface.resolve_pane(pane_ref)
        endpoint_ref = pane.resolve_capability_ref(capability_ref)
        return await self.invoke_api_endpoint(
            namespace=namespace,
            endpoint_ref=endpoint_ref,
            discriminant=discriminant or endpoint_ref,
            request_payload=request_payload,
        )

    async def invoke_api_endpoint(
        self,
        *,
        namespace: str,
        endpoint_ref: str,
        discriminant: str | None = None,
        request_payload: JsonPayload | None = None,
    ) -> InterfaceInvokeApiResponse:
        return await self._host_call(
            "interface_invoke_api",
            self._api().invoke_interface_api.invoke_interface_api(
                InterfaceInvokeApiRequest(
                    namespace=namespace,
                    endpoint_ref=endpoint_ref,
                    discriminant=discriminant or endpoint_ref,
                    request_payload=_json_object(request_payload),
                ),
            ),
        )

    async def invoke_pane_action(
        self,
        *,
        namespace: str,
        pane_ref: str,
        action_ref: str,
        payload: JsonPayload | None = None,
        ensure_current_surface: bool = True,
        auth_token: str | None = None,
        endpoint: str | None = None,
        host_label: str | None = None,
        environment_config_id: UUID | None = None,
        interface_package_id: UUID | None = None,
        interface_package_name: str | None = None,
    ) -> InterfaceActionResponse:
        if ensure_current_surface:
            surface = await self.ensure_surface(
                namespace=namespace,
                auth_token=auth_token,
                endpoint=endpoint,
                host_label=host_label,
                environment_config_id=environment_config_id,
                interface_package_id=interface_package_id,
                interface_package_name=interface_package_name,
            )
        else:
            surface = await self.status_surface(namespace=namespace)
        pane = surface.resolve_pane(pane_ref)
        action_key = pane.resolve_action_ref(action_ref)
        return await self._host_call(
            "interface_action",
            self._api().perform_interface_action.perform_interface_action(
                InterfaceActionRequest(
                    namespace=namespace,
                    pane_ref=pane.pane_ref,
                    action_key=action_key,
                    payload=_json_object(payload),
                ),
            ),
        )

    async def action(
        self,
        *,
        namespace: str,
        action_key: str,
        pane_ref: str | None = None,
        payload: JsonPayload | None = None,
    ) -> InterfaceActionResponse:
        return await self._host_call(
            "interface_action",
            self._api().perform_interface_action.perform_interface_action(
                InterfaceActionRequest(
                    namespace=namespace,
                    pane_ref=pane_ref,
                    action_key=action_key,
                    payload=_json_object(payload),
                ),
            ),
        )

    def follow_states(
        self,
        *,
        namespace: str,
        poll_interval_ms: int = 1000,
    ) -> AsyncIterator[InterfaceHostState]:
        return self._follow_states(
            namespace=namespace,
            poll_interval_ms=poll_interval_ms,
        )

    async def _follow_states(
        self,
        *,
        namespace: str,
        poll_interval_ms: int,
    ) -> AsyncIterator[InterfaceHostState]:
        request = InterfaceFollowRequest(
            namespace=namespace,
            poll_interval_ms=poll_interval_ms,
        )
        async for (
            event
        ) in self._api().watch_interface_state.stream_watch_interface_state(
            request,
        ):
            host_state = getattr(event, "host_state", event)
            yield _coerce_model(host_state, InterfaceHostState)

    def _api(self) -> Any:
        return cast(Any, self.service_client).interface

    async def _host_call(self, operation: str, awaitable: Awaitable[_T]) -> _T:
        try:
            return await awaitable
        except Exception as exc:
            if _is_host_unavailable_error(exc):
                raise InterfaceHostUnavailableError(
                    operation=operation,
                    reason=_host_unavailable_reason(exc),
                    details=str(exc) or type(exc).__name__,
                    socket_path=self._resolved_socket_path(),
                    state_home=self.state_home,
                ) from exc
            raise

    def _resolved_socket_path(self) -> Path | None:
        if self.socket_path is not None:
            return self.socket_path
        socket_path = getattr(self.control_client, "socket_path", None)
        if socket_path is None:
            return None
        if isinstance(socket_path, Path):
            return socket_path
        return Path(str(socket_path))


_ModelT = TypeVar("_ModelT", bound=BaseModel)


def _coerce_model(value: object, model_cls: type[_ModelT]) -> _ModelT:
    if isinstance(value, model_cls):
        return value
    payload = (
        value.model_dump(mode="json", exclude_none=True)
        if isinstance(
            value,
            BaseModel,
        )
        else value
    )
    return model_cls.model_validate(payload)


def _is_host_unavailable_error(exc: Exception) -> bool:
    if isinstance(
        exc,
        (
            FileNotFoundError,
            ConnectionRefusedError,
            ConnectionResetError,
            BrokenPipeError,
            TimeoutError,
        ),
    ):
        return True
    if isinstance(exc, OSError):
        message = str(exc).lower()
        return (
            "no such file or directory" in message
            or "connection refused" in message
            or "connection reset" in message
            or "broken pipe" in message
        )
    if isinstance(exc, RuntimeError):
        return "closed without a response" in str(exc).lower()
    return False


def _host_unavailable_reason(exc: Exception) -> str:
    if isinstance(exc, FileNotFoundError):
        return "socket_not_found"
    if isinstance(exc, ConnectionRefusedError):
        return "connection_refused"
    if isinstance(exc, ConnectionResetError):
        return "connection_reset"
    if isinstance(exc, BrokenPipeError):
        return "broken_pipe"
    if isinstance(exc, TimeoutError):
        return "timeout"
    message = str(exc).lower()
    if "no such file or directory" in message:
        return "socket_not_found"
    if "connection refused" in message:
        return "connection_refused"
    if "closed without a response" in message:
        return "host_closed_without_response"
    return "interface_host_unavailable"


__all__ = [
    "InterfaceControlClient",
    "InterfaceHostUnavailableError",
    "InterfaceSdkClient",
    "InterfaceSdkError",
]
