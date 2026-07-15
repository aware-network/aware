from __future__ import annotations

from pathlib import Path
from typing import Protocol
from uuid import UUID

from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt,
    EnvironmentSessionJoinReceipt,
)
from aware_interface import InterfaceRuntimeState
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
)
from aware_interface_sdk.transport import (
    InterfaceTransportBindingState,
    InterfaceTransportSession,
)

from aware_interface_service.host.product import (
    derive_control_plane_profiles_state as _derive_host_control_plane_profiles_state,
)
from aware_interface_service.host.capabilities.interface_admission import (
    INTERFACE_ADMISSION_SCREEN_KEY,
)
from aware_interface_service.host.capabilities.identity import (
    CONTROL_IDENTITY_ADMISSION_SCREEN_KEY,
)
from aware_interface_service.host.state import (
    OPERATOR_LOCAL_BOOTSTRAP_PROFILE_ID,
    active_control_plane_profile_id,
)
from aware_interface_service.models import (
    InterfaceAppScreenState,
    InterfaceEnvironmentAdmissionState,
    InterfaceEnvironmentNavigationState,
    InterfaceEnvironmentSessionState,
    InterfaceExperienceLensState,
    InterfaceHostServiceAllowedAction,
    InterfaceHostServiceControlPlaneProfilesState,
    InterfaceHostServiceControlPlaneWorkspaceState,
    InterfaceHostServiceCurrentScreen,
    InterfaceHostServiceExperienceSessionHandoffState,
    InterfaceHostServiceExperienceSessionNarrationState,
    InterfaceHostServiceHostedServicesState,
    InterfaceHostServiceLaneSyncState,
    InterfaceHostServiceLocalNodeRuntimeState,
    InterfaceHostServiceLocalServiceHostState,
    InterfaceHostServiceOperationState,
    InterfaceHostServiceRecoveryCapabilityState,
    InterfaceHostServiceRendererCapabilitiesState,
    InterfaceHostServiceSelectedSemanticPackageState,
    InterfaceHostServiceSelectedWorkspaceState,
    InterfaceHostServiceState,
    InterfaceHostServiceTransportState,
    InterfaceHostServiceWorkspaceDiscoveryState,
)


class InterfaceHostStatusRuntime(Protocol):
    host_label: str
    repository_root: Path
    state_home: Path | None
    namespace: str
    endpoint: str | None
    environment_id: UUID | None
    environment_config_id: UUID | None
    transport_session: InterfaceTransportSession | None
    coordinator: object | None
    host_runtime: object | None
    _started: bool
    _authenticated: bool
    _interface_system_actor_id: UUID | None
    _interface_system_identity_id: UUID | None
    _runtime_state: InterfaceRuntimeState | None
    interface_config_bundle: InterfaceConfigBundle | None
    _lane_sync_state: InterfaceHostServiceLaneSyncState | None
    _environment_admission_state: InterfaceEnvironmentAdmissionState | None
    _environment_session_state: InterfaceEnvironmentSessionState | None
    _environment_navigation_state: InterfaceEnvironmentNavigationState | None
    _environment_admission_receipt: EnvironmentActorAdmissionReceipt | None
    _environment_session_join_receipt: EnvironmentSessionJoinReceipt | None
    _experience_lens_state: InterfaceExperienceLensState | None
    _app_screen_state: InterfaceAppScreenState | None
    _renderer_capabilities: InterfaceHostServiceRendererCapabilitiesState | None
    _local_service_host: InterfaceHostServiceLocalServiceHostState | None
    _local_node_runtime: InterfaceHostServiceLocalNodeRuntimeState | None
    _hosted_services: InterfaceHostServiceHostedServicesState | None
    _active_profile_id: str
    _control_plane_profiles: InterfaceHostServiceControlPlaneProfilesState | None
    _control_plane_workspace: InterfaceHostServiceControlPlaneWorkspaceState | None
    _workspace_discovery: InterfaceHostServiceWorkspaceDiscoveryState | None
    _selected_workspace: InterfaceHostServiceSelectedWorkspaceState | None
    _selected_semantic_package: InterfaceHostServiceSelectedSemanticPackageState | None
    _current_screen: InterfaceHostServiceCurrentScreen | None
    _current_operation: InterfaceHostServiceOperationState | None
    _allowed_actions: tuple[InterfaceHostServiceAllowedAction, ...]
    _recovery_capabilities: tuple[InterfaceHostServiceRecoveryCapabilityState, ...]
    _experience_session_handoff_state: (
        InterfaceHostServiceExperienceSessionHandoffState | None
    )
    _experience_session_narration_state: (
        InterfaceHostServiceExperienceSessionNarrationState | None
    )


def transport_state_from_binding(
    *,
    binding: InterfaceTransportBindingState | None,
    authenticated: bool,
    interface_system_actor_id: UUID | None = None,
    interface_system_identity_id: UUID | None = None,
) -> InterfaceHostServiceTransportState:
    if binding is None:
        return InterfaceHostServiceTransportState(
            available=True,
            registered=False,
            authenticated=authenticated,
            interface_system_actor_id=interface_system_actor_id,
            interface_system_identity_id=interface_system_identity_id,
        )
    return InterfaceHostServiceTransportState(
        available=True,
        registered=True,
        authenticated=authenticated,
        actor_id=binding.actor_id,
        interface_id=binding.interface_id,
        interface_system_actor_id=interface_system_actor_id,
        interface_system_identity_id=interface_system_identity_id,
        interface_session_id=binding.interface_session_id,
        session_label=binding.session_label,
        capabilities=binding.capabilities,
        protocol_version=binding.protocol_version,
        last_seen_at=binding.last_seen_at,
        interface_identity_network_node_id=binding.interface_identity_network_node_id,
        interface_session_network_binding_id=binding.interface_session_network_binding_id,
    )


def build_transport_state(
    runtime: InterfaceHostStatusRuntime,
) -> InterfaceHostServiceTransportState:
    if runtime.transport_session is None:
        return InterfaceHostServiceTransportState(
            available=False,
            registered=False,
            authenticated=False,
            interface_system_actor_id=runtime._interface_system_actor_id,
            interface_system_identity_id=runtime._interface_system_identity_id,
        )
    return transport_state_from_binding(
        binding=runtime.transport_session.binding,
        authenticated=runtime._authenticated,
        interface_system_actor_id=runtime._interface_system_actor_id,
        interface_system_identity_id=runtime._interface_system_identity_id,
    )


def build_service_state(
    runtime: InterfaceHostStatusRuntime,
) -> InterfaceHostServiceState:
    warnings: list[str] = []
    resolved_profile_id = active_control_plane_profile_id(runtime._active_profile_id)
    if runtime.transport_session is None:
        warnings.append("transport_unbound")
    if runtime.coordinator is None:
        warnings.append("runtime_unbound")
    if runtime.host_runtime is None:
        warnings.append("host_runtime_unbound")
    if (
        resolved_profile_id == OPERATOR_LOCAL_BOOTSTRAP_PROFILE_ID
        and runtime._local_service_host is not None
        and runtime._local_service_host.managed
        and not runtime._local_service_host.ready
    ):
        warnings.append("local_service_host_required")
    if (
        resolved_profile_id == OPERATOR_LOCAL_BOOTSTRAP_PROFILE_ID
        and runtime._local_node_runtime is not None
        and runtime._local_node_runtime.managed
        and runtime._local_service_host is not None
        and runtime._local_service_host.ready
        and not runtime._local_node_runtime.ready
    ):
        warnings.append("local_node_runtime_required")
    if runtime._runtime_state is not None:
        warnings.extend(runtime._runtime_state.warnings)
    if runtime._lane_sync_state is not None and runtime._lane_sync_state.error:
        warnings.append("lane_sync_error")
    if runtime._environment_admission_state is not None:
        if runtime._environment_admission_state.status == "blocked":
            warnings.append("environment_admission_blocked")
        elif runtime._environment_admission_state.status == "error":
            warnings.append("environment_admission_error")
    if runtime._environment_navigation_state is not None:
        if runtime._environment_navigation_state.status == "blocked":
            warnings.append("environment_navigation_blocked")
        elif runtime._environment_navigation_state.status == "error":
            warnings.append("environment_navigation_error")
    if runtime._environment_session_state is not None:
        if runtime._environment_session_state.status == "blocked":
            warnings.append("environment_session_blocked")
        elif runtime._environment_session_state.status == "error":
            warnings.append("environment_session_error")
    if runtime._experience_lens_state is not None:
        if runtime._experience_lens_state.status == "blocked":
            warnings.append("experience_lens_blocked")
        elif runtime._experience_lens_state.status == "error":
            warnings.append("experience_lens_error")
    if (
        runtime._experience_session_handoff_state is not None
        and runtime._experience_session_handoff_state.error
    ):
        warnings.append("experience_session_handoff_error")
    if (
        runtime._experience_session_narration_state is not None
        and runtime._experience_session_narration_state.error
    ):
        warnings.append("experience_session_narration_error")
    if runtime._workspace_discovery is not None and runtime._workspace_discovery.error:
        warnings.append("workspace_discovery_error")
    if (
        runtime._workspace_discovery is not None
        and runtime._workspace_discovery.selection_required
        and runtime._workspace_discovery.candidates
    ):
        warnings.append("workspace_selection_required")
    selected_workspace = runtime._selected_workspace
    lifecycle = selected_workspace.lifecycle if selected_workspace is not None else None
    if lifecycle is not None and not lifecycle.joined:
        warnings.append(
            "workspace_join_required"
            if lifecycle.joinable
            else "workspace_runtime_pending"
        )
    if runtime._current_screen is not None:
        if runtime._current_screen.screen_key == INTERFACE_ADMISSION_SCREEN_KEY:
            warnings.append("interface_admission_required")
        elif (
            runtime._current_screen.screen_key == CONTROL_IDENTITY_ADMISSION_SCREEN_KEY
        ):
            warnings.append("identity_auth_required")
    return InterfaceHostServiceState(
        host_label=runtime.host_label,
        repository_root=runtime.repository_root,
        state_home=runtime.state_home,
        namespace=runtime.namespace,
        endpoint=runtime.endpoint,
        environment_id=runtime.environment_id,
        environment_config_id=runtime.environment_config_id,
        started=runtime._started,
        transport=build_transport_state(runtime),
        renderer_capabilities=runtime._renderer_capabilities,
        local_service_host=runtime._local_service_host,
        local_node_runtime=runtime._local_node_runtime,
        hosted_services=runtime._hosted_services,
        lane_sync=runtime._lane_sync_state,
        environment_admission=runtime._environment_admission_state,
        environment_session=runtime._environment_session_state,
        environment_navigation=runtime._environment_navigation_state,
        environment_admission_receipt=runtime._environment_admission_receipt,
        environment_session_join_receipt=runtime._environment_session_join_receipt,
        experience_lens=runtime._experience_lens_state,
        app_screen=runtime._app_screen_state,
        runtime=runtime._runtime_state,
        interface_config_bundle=runtime.interface_config_bundle,
        control_plane_profiles=(
            runtime._control_plane_profiles
            if runtime._control_plane_profiles is not None
            else _derive_host_control_plane_profiles_state(
                active_profile_id=runtime._active_profile_id,
                current_screen=runtime._current_screen,
            )
        ),
        control_plane_workspace=runtime._control_plane_workspace,
        workspace_discovery=runtime._workspace_discovery,
        selected_workspace=runtime._selected_workspace,
        selected_semantic_package=runtime._selected_semantic_package,
        current_screen=runtime._current_screen,
        current_operation=runtime._current_operation,
        allowed_actions=runtime._allowed_actions,
        recovery_capabilities=runtime._recovery_capabilities,
        experience_session_handoff=runtime._experience_session_handoff_state,
        experience_session_narration=runtime._experience_session_narration_state,
        warnings=tuple(warnings),
    )


__all__ = [
    "InterfaceHostStatusRuntime",
    "build_service_state",
    "build_transport_state",
    "transport_state_from_binding",
]
