from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from aware_interface.host_capabilities import InterfaceHostPaneContribution
from aware_interface import InterfaceRuntimeState, InterfaceNavigationContextLayoutTargetState
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
)
from aware_interface_service.models import (
    InterfaceHostServiceAllowedAction,
    InterfaceHostServiceControlPlaneProfilesState,
    InterfaceHostServiceControlPlaneWorkspaceState,
    InterfaceHostServiceCurrentScreen,
    InterfaceHostServiceLaneSyncState,
    InterfaceHostServiceLocalNodeRuntimeState,
    InterfaceHostServiceLocalServiceHostState,
    InterfaceHostServiceOperationState,
)


OPERATOR_LOCAL_BOOTSTRAP_PROFILE_ID = "operator.local_bootstrap"
CONSUMER_REMOTE_ADMISSION_PROFILE_ID = "consumer.remote_admission"
CONTROL_PLANE_PROFILE_IDS = (
    OPERATOR_LOCAL_BOOTSTRAP_PROFILE_ID,
    CONSUMER_REMOTE_ADMISSION_PROFILE_ID,
)


def normalize_control_plane_profile_id(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def active_control_plane_profile_id(value: str | None) -> str:
    normalized = normalize_control_plane_profile_id(value)
    if normalized in CONTROL_PLANE_PROFILE_IDS:
        return normalized
    return OPERATOR_LOCAL_BOOTSTRAP_PROFILE_ID


def operator_profile_active(value: str | None) -> bool:
    return active_control_plane_profile_id(value) == OPERATOR_LOCAL_BOOTSTRAP_PROFILE_ID


def consumer_profile_active(value: str | None) -> bool:
    return (
        active_control_plane_profile_id(value) == CONSUMER_REMOTE_ADMISSION_PROFILE_ID
    )


def normalize_selected_step_id(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


@dataclass(frozen=True, slots=True)
class InterfaceHostProductInputs:
    endpoint: str | None
    namespace: str
    active_profile_id: str
    selected_step_id: str | None
    selected_step_explicit: bool
    authenticated: bool
    interface_admitted: bool
    transport_bound: bool
    local_service_host: InterfaceHostServiceLocalServiceHostState | None
    local_node_runtime: InterfaceHostServiceLocalNodeRuntimeState | None
    identity_admission_summary: str | None
    identity_admission_error: str | None
    identity_admission_detail_lines: tuple[str, ...]
    identity_admission_recent_activity: tuple[str, ...]
    identity_admission_updated_at: str | None


@dataclass(frozen=True, slots=True)
class InterfaceHostProductState:
    current_screen: InterfaceHostServiceCurrentScreen | None
    pane_contributions: tuple[InterfaceHostPaneContribution, ...]
    allowed_actions: tuple[InterfaceHostServiceAllowedAction, ...]
    current_operation: InterfaceHostServiceOperationState | None
    control_plane_profiles: InterfaceHostServiceControlPlaneProfilesState
    control_plane_workspace: InterfaceHostServiceControlPlaneWorkspaceState | None
    selected_step_id: str | None


@dataclass(frozen=True, slots=True)
class InterfaceHostLayoutInputs:
    runtime_state: InterfaceRuntimeState
    endpoint: str | None
    namespace: str
    active_profile_id: str
    current_screen: InterfaceHostServiceCurrentScreen | None
    pane_contributions: tuple[InterfaceHostPaneContribution, ...]
    allowed_actions: tuple[InterfaceHostServiceAllowedAction, ...]
    current_operation: InterfaceHostServiceOperationState | None
    control_plane_workspace: InterfaceHostServiceControlPlaneWorkspaceState | None
    local_service_host: InterfaceHostServiceLocalServiceHostState | None
    local_node_runtime: InterfaceHostServiceLocalNodeRuntimeState | None
    lane_sync: InterfaceHostServiceLaneSyncState | None
    interface_config_bundle: InterfaceConfigBundle | None
    bundle_window_layout_enabled: bool
    bundle_window_key: str | None
    bundle_layout_config_id: UUID | None
    bundle_layout_key: str | None
    bundle_focus_section_key: str | None
    bundle_focus_observable_id: UUID | None
    navigation_context_layout_target: InterfaceNavigationContextLayoutTargetState | None


__all__ = [
    "CONSUMER_REMOTE_ADMISSION_PROFILE_ID",
    "CONTROL_PLANE_PROFILE_IDS",
    "InterfaceHostLayoutInputs",
    "InterfaceHostProductInputs",
    "InterfaceHostProductState",
    "OPERATOR_LOCAL_BOOTSTRAP_PROFILE_ID",
    "active_control_plane_profile_id",
    "consumer_profile_active",
    "normalize_control_plane_profile_id",
    "normalize_selected_step_id",
    "operator_profile_active",
]
