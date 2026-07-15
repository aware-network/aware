from __future__ import annotations
import asyncio
from contextlib import suppress
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast
from uuid import UUID, uuid4

from aware_api_service_dto.comms.models.api import (
    ApiRequestStatus,
    ApiStreamLifecycle,
)
from aware_code.types import JsonObject
from aware_comms import DuplexIpcEndpoint
from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt,
    EnvironmentNavigationContextView,
    EnvironmentSessionJoinReceipt,
)
from aware_experience_service_dto.experience.actor_admission.models import (
    ExperienceActorConfigAdmissionReceipt,
)
from aware_experience_service_api import AwareExperienceServiceApiClient
from aware_interface import (
    InterfaceBackendState,
    InterfaceMaterializedPaneState,
    InterfaceRuntimeCoordinator,
    InterfaceRuntimePaneRenderSpecState,
    InterfaceRuntimeSectionRepresentationState,
    InterfaceRuntimeFocusState,
    InterfaceResolvedPaneDescriptor,
    InterfaceResolvedSectionStateAddress,
    InterfaceResolvedView,
    InterfaceRuntimeState,
    InterfaceRuntimeWindowState,
    InterfaceRuntimeWindowNavigationContextState,
    InterfaceNavigationContextLayoutTargetState,
    InterfaceWindowLayoutState,
    load_workspace_interface_config_bundle,
)
from aware_interface.host_capabilities import InterfaceHostPaneContribution
from aware_interface.host_runtime import InterfaceHostRuntimeSyncAssets
from aware_interface.stable_ids import (
    stable_interface_environment_id,
    stable_interface_window_id,
    stable_interface_window_navigation_context_id,
    stable_window_id,
)
from aware_interface.session_port import FocusScopeLane, SectionFocusScopeLane
from aware_interface_sdk.transport import InterfaceTransportSession
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
)
from aware_service_service_dto.comms.models.service import (
    RequestStatus,
    ServiceOperationResponse,
    StreamLifecycle,
)
from aware_service_runtime.contracts import ServiceHostApiIngressRequest
from aware_service_runtime.duplex_client import ServiceHostDuplexClient
from aware_utils.logging import logger

from aware_interface_service.host.product import (
    compose_host_product as _compose_host_product,
    derive_control_plane_profiles_state as _derive_host_control_plane_profiles_state,
)
from aware_interface_service.host.state import (
    InterfaceHostLayoutInputs,
    InterfaceHostProductInputs,
    consumer_profile_active as _consumer_profile_active_value,
)
from aware_interface_service.models import (
    InterfaceAppScreenEntryResult,
    InterfaceAppScreenState,
    InterfaceEnvironmentAdmissionState,
    InterfaceEnvironmentEntryResult,
    InterfaceEnvironmentNavigationSelectResult,
    InterfaceEnvironmentNavigationState,
    InterfaceEnvironmentSessionJoinResult,
    InterfaceEnvironmentSessionState,
    InterfaceExperienceSessionActorContext,
    InterfaceExperienceLensState,
    InterfaceHostServiceAllowedAction,
    InterfaceHostAttentionLayoutTransitionResult,
    InterfaceHostAttentionLayoutTopologyTransitionResult,
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
    InterfaceHostServiceWorkspaceDiscoveryState,
    InterfaceHostServiceWorkspaceSemanticSourceState,
)

if TYPE_CHECKING:
    from aware_interface_service.local_runtime import InterfaceLocalRuntimeController


class _LazyModule:
    def __init__(self, module_name: str) -> None:
        self._module_name = module_name
        self._module: object | None = None

    def __getattr__(self, name: str) -> object:
        module = self._module
        if module is None:
            module = import_module(self._module_name)
            self._module = module
        return getattr(module, name)


hosted_services_capability_mod = _LazyModule(
    "aware_interface_service.host.capabilities.hosted_services"
)
app_screen_capability_mod = _LazyModule(
    "aware_interface_service.host.capabilities.app_screen"
)
local_runtime_capability_mod = _LazyModule(
    "aware_interface_service.host.capabilities.local_runtime"
)
attention_capability_mod = _LazyModule(
    "aware_interface_service.host.capabilities.attention"
)
environment_admission_capability_mod = _LazyModule(
    "aware_interface_service.host.capabilities.environment_admission"
)
environment_entry_capability_mod = _LazyModule(
    "aware_interface_service.host.capabilities.environment_entry"
)
environment_navigation_capability_mod = _LazyModule(
    "aware_interface_service.host.capabilities.environment_navigation"
)
environment_session_capability_mod = _LazyModule(
    "aware_interface_service.host.capabilities.environment_session"
)
experience_capability_mod = _LazyModule(
    "aware_interface_service.host.capabilities.experience"
)
experience_lens_capability_mod = _LazyModule(
    "aware_interface_service.host.capabilities.experience_lens"
)
experience_session_capability_mod = _LazyModule(
    "aware_interface_service.host.capabilities.experience_session"
)
host_actions_mod = _LazyModule("aware_interface_service.host.actions")
host_control_plane_mod = _LazyModule("aware_interface_service.host.control_plane")
host_layout_mod = _LazyModule("aware_interface_service.host.layout")
host_lane_sync_mod = _LazyModule("aware_interface_service.host.lane_sync")
host_status_mod = _LazyModule("aware_interface_service.host.status")
host_view_state_subscription_mod = _LazyModule(
    "aware_interface_service.host.view_state_subscription"
)


class _InterfaceCoordinatorProtocol(Protocol):
    async def snapshot(self) -> InterfaceRuntimeState: ...

    async def ensure_boot_interface_graph(self) -> UUID: ...

    async def resolve_projection_hash(self, *, opg_name: str) -> str: ...

    async def resolve_focus_scope_lane(
        self, *, window_key: str
    ) -> "FocusScopeLane": ...

    async def resolve_section_focus_scope_lane(
        self,
        *,
        window_key: str,
        layout_key: str,
        section_key: str,
    ) -> "SectionFocusScopeLane": ...

    def build_lane_sync_service(
        self,
        *,
        include_commit_payload: bool = True,
    ) -> "InterfaceLaneSyncService": ...


if TYPE_CHECKING:
    from aware_interface import InterfaceLaneSyncService


class _InterfaceHostRuntimeProtocol(Protocol):
    def load_sync_assets(
        self,
        *,
        projection_hash: str,
    ) -> InterfaceHostRuntimeSyncAssets: ...

    async def load_pane_render_spec_runtime_states(
        self,
        *,
        interface_config_bundle: InterfaceConfigBundle | None = None,
    ) -> tuple[InterfaceRuntimePaneRenderSpecState, ...]: ...


def _normalize_status_token(value: object) -> str:
    return str(getattr(value, "value", value) or "").strip()


def _request_status_from_api_status(status: object) -> RequestStatus:
    token = _normalize_status_token(status)
    if token == ApiRequestStatus.succeeded.value:
        return RequestStatus.succeeded
    if token == ApiRequestStatus.pending.value:
        return RequestStatus.pending
    return RequestStatus.failed


def _stream_lifecycle_from_api_lifecycle(
    lifecycle: object,
) -> StreamLifecycle:
    token = _normalize_status_token(lifecycle)
    if token == ApiStreamLifecycle.started.value:
        return StreamLifecycle.started
    if token == ApiStreamLifecycle.closed.value:
        return StreamLifecycle.closed
    return StreamLifecycle.auto_close


def _service_response_from_api_response(
    response: object,
) -> ServiceOperationResponse:
    return ServiceOperationResponse(
        status=_request_status_from_api_status(getattr(response, "status", None)),
        error=getattr(response, "error", None),
        response_payload=getattr(response, "response_payload", None),
        stream_lifecycle=_stream_lifecycle_from_api_lifecycle(
            getattr(response, "stream_lifecycle", None)
        ),
    )


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _optional_uuid(value: object | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return UUID(raw)
    except (TypeError, ValueError):
        return None


def _optional_string(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _pane_state_key_for_descriptor(pane: InterfaceResolvedPaneDescriptor) -> str:
    return ":".join(
        (
            pane.window_key,
            pane.layout_key,
            pane.section_key,
            pane.pane_kind,
            str(pane.pane_config_id or ""),
            pane.state_projection_hash or "",
        )
    )


def _active_runtime_section_representation(
    *,
    active_focus: object,
    section_representations: tuple[InterfaceRuntimeSectionRepresentationState, ...],
) -> InterfaceRuntimeSectionRepresentationState | None:
    section_key = str(getattr(active_focus, "section_key", "") or "").strip()
    observable_id = _optional_uuid(getattr(active_focus, "observable_id", None))
    if not section_key or observable_id is None:
        return None
    candidates = tuple(
        item
        for item in section_representations
        if item.section_key.strip().casefold() == section_key.casefold()
        and item.observable_id == observable_id
    )
    if not candidates:
        focus_target = getattr(active_focus, "focus_target", None)
        object_projection_graph_identity_id = _optional_uuid(
            getattr(focus_target, "object_projection_graph_identity_id", None)
        )
        if object_projection_graph_identity_id is not None:
            candidates = tuple(
                item
                for item in section_representations
                if item.section_key.strip().casefold() == section_key.casefold()
                and item.object_projection_graph_identity_id
                == object_projection_graph_identity_id
            )
    if not candidates:
        return None
    active = next((item for item in candidates if item.is_active), None)
    return active or candidates[0]


def _resolved_section_representation_for_runtime_focus(
    *,
    active_focus: InterfaceRuntimeFocusState | None,
    section_representations: tuple[InterfaceRuntimeSectionRepresentationState, ...],
) -> InterfaceRuntimeSectionRepresentationState | None:
    if active_focus is None or active_focus.observable_id is not None:
        return None
    section_key = str(active_focus.section_key or "").strip().casefold()
    candidates = (
        tuple(
            item
            for item in section_representations
            if item.section_key.strip().casefold() == section_key
        )
        if section_key
        else tuple(section_representations)
    )
    if not candidates:
        return None
    if len(candidates) != 1:
        return None
    return candidates[0]


def _runtime_focus_with_resolved_representation(
    *,
    active_focus: InterfaceRuntimeFocusState | None,
    representation: InterfaceRuntimeSectionRepresentationState | None,
    section_state_addresses: dict[str, InterfaceResolvedSectionStateAddress],
) -> InterfaceRuntimeFocusState | None:
    if active_focus is None or representation is None:
        return active_focus
    if active_focus.observable_id is not None:
        return active_focus
    address = section_state_addresses.get(representation.section_key)
    return replace(
        active_focus,
        layout_config_id=representation.layout_config_id
        or active_focus.layout_config_id,
        layout_key=representation.layout_key or active_focus.layout_key,
        section_key=representation.section_key,
        layout_config_section_config_id=(
            representation.layout_config_section_config_id
            or active_focus.layout_config_section_config_id
        ),
        layout_section_id=(
            address.layout_section_id
            if address is not None and address.layout_section_id is not None
            else active_focus.layout_section_id
        ),
        section_focus_scope_id=(
            address.section_focus_scope_id
            if address is not None and address.section_focus_scope_id is not None
            else active_focus.section_focus_scope_id
        ),
        focus_scope_id=(
            address.focus_scope_id
            if address is not None and address.focus_scope_id is not None
            else active_focus.focus_scope_id
        ),
        focus_id=(
            address.focus_id
            if address is not None and address.focus_id is not None
            else active_focus.focus_id
        ),
        observable_id=representation.observable_id,
        focus_target=(
            address.focus_target
            if address is not None and address.focus_target is not None
            else active_focus.focus_target
        ),
    )


def _experience_section_view_cache_key(
    *,
    section_key: str,
    observable_id: UUID | None,
) -> tuple[str, UUID]:
    if observable_id is None:
        raise RuntimeError("Experience section view cache requires observable_id.")
    return (section_key.strip().casefold(), observable_id)


_API_ACTION_KEY_PREFIX = "api:"
_SDK_ACTION_KEY_PREFIX = "sdk:"
_OPERATOR_LOCAL_BOOTSTRAP_PROFILE_ID = "operator.local_bootstrap"
_CONSUMER_REMOTE_ADMISSION_PROFILE_ID = "consumer.remote_admission"
_INTERFACE_ADMISSION_SCREEN_KEY = "interface_admission"
_DYNAMIC_RENDER_SPEC_WARNING_PREFIX = "dynamic_pane_render_specs_unavailable:"
_EXPERIENCE_VIEW_STATE_SUBSCRIPTION_WARNING_PREFIX = (
    "experience_view_state_subscription_unavailable:"
)


def _resolved_pane_descriptor_key(
    pane: InterfaceResolvedPaneDescriptor,
) -> tuple[str, str, str, str, UUID | None]:
    return (
        pane.window_key,
        pane.layout_key,
        pane.section_key,
        pane.pane_kind,
        pane.pane_config_id,
    )


def _materialized_pane_state_key(
    pane: InterfaceMaterializedPaneState,
) -> tuple[str, str, str, str, UUID | None]:
    return (
        pane.window_key,
        pane.layout_key,
        pane.section_key,
        pane.pane_kind,
        pane.pane_config_id,
    )


def _merge_resolved_pane_descriptors(
    *,
    existing: tuple[InterfaceResolvedPaneDescriptor, ...],
    derived: tuple[InterfaceResolvedPaneDescriptor, ...],
    materialized_pane_states: tuple[InterfaceMaterializedPaneState, ...],
) -> tuple[InterfaceResolvedPaneDescriptor, ...]:
    if not existing:
        return derived
    if not derived:
        return existing
    seen = {_resolved_pane_descriptor_key(pane) for pane in derived}
    materialized_keys = {
        _materialized_pane_state_key(pane) for pane in materialized_pane_states
    }
    merged = list(derived)
    for pane in existing:
        key = _resolved_pane_descriptor_key(pane)
        if key in seen or key not in materialized_keys:
            continue
        merged.append(pane)
        seen.add(key)
    return tuple(merged)


def _merge_pane_declared_allowed_actions(
    *,
    runtime_state: InterfaceRuntimeState | None,
    existing_actions: tuple[InterfaceHostServiceAllowedAction, ...],
) -> tuple[InterfaceHostServiceAllowedAction, ...]:
    if runtime_state is None:
        return tuple(
            action
            for action in existing_actions
            if not action.action_key.startswith(_API_ACTION_KEY_PREFIX)
            and not action.action_key.startswith(_SDK_ACTION_KEY_PREFIX)
        )

    pane_target_action_keys = {
        getattr(target, "action_key", "").strip()
        for pane in runtime_state.resolved_panes
        for target in tuple(getattr(pane, "action_targets", ()))
        if getattr(target, "action_key", "").strip()
    }
    base_actions = tuple(
        action
        for action in existing_actions
        if not action.action_key.startswith(_API_ACTION_KEY_PREFIX)
        and not action.action_key.startswith(_SDK_ACTION_KEY_PREFIX)
        and action.action_key not in pane_target_action_keys
    )

    seen = {action.action_key for action in base_actions}
    mounted_actions: list[InterfaceHostServiceAllowedAction] = []
    for pane in runtime_state.resolved_panes:
        action_targets_by_key = {
            getattr(target, "action_key", "").strip(): target
            for target in tuple(getattr(pane, "action_targets", ()))
            if getattr(target, "action_key", "").strip()
        }
        for action_key in pane.action_keys:
            if action_key.startswith(_API_ACTION_KEY_PREFIX) or action_key.startswith(
                _SDK_ACTION_KEY_PREFIX
            ):
                seen.add(action_key)
                continue
            if action_key in seen:
                continue
            action_target = action_targets_by_key.get(action_key)
            if action_target is not None:
                if (
                    getattr(
                        pane,
                        "projection_experience_view_instance_id",
                        None,
                    )
                    is None
                ):
                    seen.add(action_key)
                    continue
                if (
                    getattr(
                        action_target,
                        "view_invocation_action_config_id",
                        None,
                    )
                    is None
                ):
                    seen.add(action_key)
                    continue
                seen.add(action_key)
                target_ref = getattr(action_target, "target_ref", "") or action_key
                action_kind = getattr(action_target, "action_kind", "") or "view"
                label = getattr(action_target, "label", None) or action_key
                mounted_actions.append(
                    InterfaceHostServiceAllowedAction(
                        action_key=action_key,
                        label=label,
                        enabled=True,
                        reason=(
                            "Mounted pane declares this Experience view "
                            + f"{action_kind} action."
                        ),
                        payload_schema_hint=f"JSON request payload for {target_ref}",
                    )
                )
                continue
    return (*base_actions, *mounted_actions)


def _merge_pane_api_allowed_actions(
    *,
    runtime_state: InterfaceRuntimeState | None,
    existing_actions: tuple[InterfaceHostServiceAllowedAction, ...],
) -> tuple[InterfaceHostServiceAllowedAction, ...]:
    return _merge_pane_declared_allowed_actions(
        runtime_state=runtime_state,
        existing_actions=existing_actions,
    )


def _merge_dynamic_render_spec_warnings(
    *,
    existing: tuple[str, ...],
    dynamic_warnings: tuple[str, ...],
) -> tuple[str, ...]:
    base = tuple(
        warning
        for warning in existing
        if not warning.startswith(_DYNAMIC_RENDER_SPEC_WARNING_PREFIX)
    )
    return (*base, *dynamic_warnings)


def _merge_experience_view_state_subscription_warnings(
    *,
    existing: tuple[str, ...],
    errors: tuple[str, ...],
) -> tuple[str, ...]:
    base = tuple(
        warning
        for warning in existing
        if not warning.startswith(_EXPERIENCE_VIEW_STATE_SUBSCRIPTION_WARNING_PREFIX)
    )
    warnings = tuple(
        f"{_EXPERIENCE_VIEW_STATE_SUBSCRIPTION_WARNING_PREFIX}{error}"
        for error in errors
    )
    return (*base, *warnings)


def _experience_view_action_refresh_trigger(
    *,
    mounted_action_ref: object,
    request_payload: Mapping[str, object],
    response_payload: Mapping[str, object],
) -> dict[str, object]:
    return _json_payload_object(
        {
            "source": "interface.experience.view_action.completion",
            "pane_ref": getattr(mounted_action_ref, "pane_ref", None),
            "action_key": getattr(mounted_action_ref, "action_key", None),
            "view_ref": getattr(mounted_action_ref, "view_ref", None),
            "projection_view_key": getattr(
                mounted_action_ref,
                "projection_view_key",
                None,
            ),
            "projection_experience_view_instance_id": getattr(
                mounted_action_ref,
                "projection_experience_view_instance_id",
                None,
            ),
            "view_invocation_action_config_id": getattr(
                mounted_action_ref,
                "view_invocation_action_config_id",
                None,
            ),
            "request_payload": request_payload,
            "response_payload": response_payload,
        }
    )


def _replace_materialized_pane_state(
    existing: tuple[InterfaceMaterializedPaneState, ...],
    pane_state: InterfaceMaterializedPaneState,
) -> tuple[InterfaceMaterializedPaneState, ...]:
    replaced = False
    next_states: list[InterfaceMaterializedPaneState] = []
    for item in existing:
        if item.pane_state_key == pane_state.pane_state_key:
            next_states.append(pane_state)
            replaced = True
        else:
            next_states.append(item)
    if not replaced:
        next_states.append(pane_state)
    return tuple(next_states)


def _json_payload_object(value: object) -> dict[str, object]:
    if value is None:
        return {}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        value = model_dump(mode="json", exclude_none=True)
    if not isinstance(value, Mapping):
        return {"value": _json_value(value)}
    return {
        str(key): _json_value(item) for key, item in value.items() if item is not None
    }


def _json_value(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return _json_payload_object(model_dump(mode="json", exclude_none=True))
    if isinstance(value, Mapping):
        return _json_payload_object(value)
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return str(value)


def _bundle_matches_request(
    *,
    bundle: InterfaceConfigBundle | None,
    interface_package_id: UUID | str | None,
    interface_package_name: str | None,
) -> bool:
    if bundle is None:
        return False
    if interface_package_id is not None:
        try:
            if UUID(str(interface_package_id)) != bundle.interface_package_id:
                return False
        except Exception:
            return False
    normalized_package_name = (interface_package_name or "").strip()
    if (
        normalized_package_name
        and normalized_package_name.casefold()
        != bundle.interface_package_name.casefold()
    ):
        return False
    return interface_package_id is not None or bool(normalized_package_name)


@dataclass(slots=True)
class InterfaceHostServiceRuntime:
    repository_root: Path
    host_label: str
    state_home: Path | None = None
    namespace: str = "service"
    endpoint: str | None = None
    environment_id: UUID | None = None
    environment_config_id: UUID | None = None
    transport_session: InterfaceTransportSession | None = None
    host_runtime: _InterfaceHostRuntimeProtocol | None = None
    coordinator: InterfaceRuntimeCoordinator | _InterfaceCoordinatorProtocol | None = (
        None
    )
    local_runtime: InterfaceLocalRuntimeController | None = None
    workspace_client_provider: object | None = None
    interface_config_bundle: InterfaceConfigBundle | None = None
    bundle_window_layout_enabled: bool = False
    bundle_window_key: str | None = None
    bundle_layout_config_id: UUID | None = None
    bundle_layout_key: str | None = None
    bundle_focus_section_key: str | None = None
    bundle_focus_observable_id: UUID | None = None
    mock_service_adapter: object | None = None
    experience_session_handoff_provider: (
        experience_session_capability_mod.ExperienceSessionHandoffProvider | None
    ) = None
    app_screen_resolver: app_screen_capability_mod.CommittedAppScreenResolver | None = (
        None
    )
    experience_app_screen_activator: (
        app_screen_capability_mod.ExperienceAppScreenActivator | None
    ) = None
    experience_view_state_provider_contexts: Mapping[
        str,
        Mapping[str, object],
    ] = field(default_factory=dict)
    _started: bool = field(init=False, default=False)
    _authenticated: bool = field(init=False, default=False)
    _interface_admitted: bool = field(init=False, default=False)
    _runtime_state: InterfaceRuntimeState | None = field(init=False, default=None)
    _committed_interface_id: UUID | None = field(init=False, default=None)
    _interface_system_actor_id: UUID | None = field(init=False, default=None)
    _interface_system_identity_id: UUID | None = field(init=False, default=None)
    _lane_sync_state: InterfaceHostServiceLaneSyncState | None = field(
        init=False, default=None
    )
    _renderer_capabilities: InterfaceHostServiceRendererCapabilitiesState | None = (
        field(
            init=False,
            default=None,
        )
    )
    _local_service_host: InterfaceHostServiceLocalServiceHostState | None = field(
        init=False, default=None
    )
    _local_node_runtime: InterfaceHostServiceLocalNodeRuntimeState | None = field(
        init=False, default=None
    )
    _hosted_services: InterfaceHostServiceHostedServicesState | None = field(
        init=False, default=None
    )
    _recovery_capabilities: tuple[InterfaceHostServiceRecoveryCapabilityState, ...] = (
        field(init=False, default=())
    )
    _local_node_log_tail: tuple[str, ...] = field(init=False, default=())
    _active_profile_id: str = field(
        init=False,
        default=_CONSUMER_REMOTE_ADMISSION_PROFILE_ID,
    )
    _workspace_registry: object | None = field(init=False, default=None)
    _workspace_discovery: InterfaceHostServiceWorkspaceDiscoveryState | None = field(
        init=False,
        default=None,
    )
    _selected_workspace_root: Path | None = field(init=False, default=None)
    _joined_workspace_root: Path | None = field(init=False, default=None)
    _attached_namespace_counts_by_workspace: dict[str, int] = field(
        init=False,
        default_factory=dict,
    )
    _selected_workspace: InterfaceHostServiceSelectedWorkspaceState | None = field(
        init=False,
        default=None,
    )
    _selected_workspace_semantic_source_root: Path | None = field(
        init=False,
        default=None,
    )
    _selected_workspace_semantic_source: (
        InterfaceHostServiceWorkspaceSemanticSourceState | None
    ) = field(init=False, default=None)
    _selected_workspace_semantic_source_invocation_id: str | None = field(
        init=False,
        default=None,
    )
    _selected_semantic_package_selector: str | None = field(init=False, default=None)
    _selected_semantic_package_selector_explicit: bool = field(
        init=False, default=False
    )
    _selected_semantic_package: (
        InterfaceHostServiceSelectedSemanticPackageState | None
    ) = field(
        init=False,
        default=None,
    )
    _interface_window_layout_request_idempotency: dict[str, str] = field(
        init=False,
        default_factory=dict,
    )
    _control_plane_profiles: InterfaceHostServiceControlPlaneProfilesState | None = (
        field(
            init=False,
            default=None,
        )
    )
    _selected_step_id: str | None = field(init=False, default=None)
    _selected_step_explicit: bool = field(init=False, default=False)
    _control_plane_workspace: InterfaceHostServiceControlPlaneWorkspaceState | None = (
        field(
            init=False,
            default=None,
        )
    )
    _current_screen: InterfaceHostServiceCurrentScreen | None = field(
        init=False, default=None
    )
    _current_operation: InterfaceHostServiceOperationState | None = field(
        init=False, default=None
    )
    _allowed_actions: tuple[InterfaceHostServiceAllowedAction, ...] = field(
        init=False,
        default=(),
    )
    _pane_contributions: tuple[InterfaceHostPaneContribution, ...] = field(
        init=False,
        default=(),
    )
    _state_revision: int = field(init=False, default=0)
    _state_change_event: asyncio.Event = field(
        init=False, default_factory=asyncio.Event
    )
    _attention_runtime_mount_cache_signature: str | None = field(
        init=False, default=None
    )
    _attention_runtime_mount_cache: (
        attention_capability_mod.AttentionRuntimeMountResolution | None
    ) = field(
        init=False,
        default=None,
    )
    _identity_admission_summary: str | None = field(init=False, default=None)
    _identity_admission_error: str | None = field(init=False, default=None)
    _identity_admission_detail_lines: tuple[str, ...] = field(init=False, default=())
    _identity_admission_recent_activity: tuple[str, ...] = field(init=False, default=())
    _identity_admission_updated_at: str | None = field(init=False, default=None)
    _environment_admission_state: InterfaceEnvironmentAdmissionState | None = field(
        init=False,
        default=None,
    )
    _environment_session_state: InterfaceEnvironmentSessionState | None = field(
        init=False,
        default=None,
    )
    _environment_navigation_state: InterfaceEnvironmentNavigationState | None = field(
        init=False,
        default=None,
    )
    _environment_admission_receipt: EnvironmentActorAdmissionReceipt | None = field(
        init=False,
        default=None,
    )
    _environment_session_join_receipt: EnvironmentSessionJoinReceipt | None = field(
        init=False,
        default=None,
    )
    _environment_navigation_context: EnvironmentNavigationContextView | None = field(
        init=False,
        default=None,
    )
    _experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None = field(
        init=False,
        default=None,
    )
    _experience_identity_session_config_id: UUID | None = field(
        init=False,
        default=None,
    )
    _experience_lens_state: InterfaceExperienceLensState | None = field(
        init=False,
        default=None,
    )
    _app_screen_state: InterfaceAppScreenState | None = field(
        init=False,
        default=None,
    )
    _experience_session_handoff_state: (
        InterfaceHostServiceExperienceSessionHandoffState | None
    ) = field(init=False, default=None)
    _experience_session_narration_state: (
        InterfaceHostServiceExperienceSessionNarrationState | None
    ) = field(init=False, default=None)
    _experience_section_view_activations: dict[
        tuple[str, UUID],
        experience_capability_mod.ExperienceSectionGraphBindingActivationResolution,
    ] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        self.repository_root = self.repository_root.resolve()
        if self.state_home is not None:
            self.state_home = self.state_home.resolve()
        if (
            self.experience_app_screen_activator is None
            and self.transport_session is not None
        ):
            self.experience_app_screen_activator = (
                app_screen_capability_mod.ServiceApiExperienceAppScreenActivator(
                    transport_session=self.transport_session,
                )
            )

    def _product_inputs(self) -> InterfaceHostProductInputs:
        return InterfaceHostProductInputs(
            endpoint=self.endpoint,
            namespace=self.namespace,
            active_profile_id=self._active_profile_id,
            selected_step_id=self._selected_step_id,
            selected_step_explicit=self._selected_step_explicit,
            authenticated=self._authenticated,
            interface_admitted=self._interface_admitted,
            transport_bound=self.transport_session is not None,
            local_service_host=self._local_service_host,
            local_node_runtime=self._local_node_runtime,
            identity_admission_summary=self._identity_admission_summary,
            identity_admission_error=self._identity_admission_error,
            identity_admission_detail_lines=self._identity_admission_detail_lines,
            identity_admission_recent_activity=self._identity_admission_recent_activity,
            identity_admission_updated_at=self._identity_admission_updated_at,
        )

    def _layout_inputs(self) -> InterfaceHostLayoutInputs:
        runtime_state = self._runtime_state
        if runtime_state is None:
            raise RuntimeError(
                "Interface host service runtime is missing runtime state; cannot resolve layout."
            )
        return InterfaceHostLayoutInputs(
            runtime_state=runtime_state,
            endpoint=self.endpoint,
            namespace=self.namespace,
            active_profile_id=self._active_profile_id,
            current_screen=self._current_screen,
            pane_contributions=self._pane_contributions,
            allowed_actions=self._allowed_actions,
            current_operation=self._current_operation,
            control_plane_workspace=self._control_plane_workspace,
            local_service_host=self._local_service_host,
            local_node_runtime=self._local_node_runtime,
            lane_sync=self._lane_sync_state,
            interface_config_bundle=self.interface_config_bundle,
            bundle_window_layout_enabled=self.bundle_window_layout_enabled,
            bundle_window_key=self.bundle_window_key,
            bundle_layout_config_id=self.bundle_layout_config_id,
            bundle_layout_key=self.bundle_layout_key,
            bundle_focus_section_key=self.bundle_focus_section_key,
            bundle_focus_observable_id=self.bundle_focus_observable_id,
            navigation_context_layout_target=runtime_state.navigation_context_layout_target,
        )

    async def _resolve_section_focus_scope_lane_for_layout(
        self,
        window_key: str,
        layout_key: str,
        section_key: str,
    ) -> "SectionFocusScopeLane":
        return await host_lane_sync_mod.resolve_section_focus_scope_lane_for_layout(
            cast(
                host_lane_sync_mod.InterfaceHostLaneSyncRuntime,
                cast(object, self),
            ),
            window_key=window_key,
            layout_key=layout_key,
            section_key=section_key,
        )

    def _section_lane_resolver(
        self,
    ) -> Callable[[str, str, str], Awaitable["SectionFocusScopeLane"]] | None:
        if self.coordinator is None:
            return None
        return self._resolve_section_focus_scope_lane_for_layout

    async def _resolve_host_section_state_addresses(
        self,
        *,
        window_layout: InterfaceWindowLayoutState | None,
        allow_section_lane_resolver: bool = True,
    ) -> dict[str, InterfaceResolvedSectionStateAddress]:
        if window_layout is None:
            return {}
        return await host_layout_mod.resolve_section_state_addresses(
            window_layout=window_layout,
            current_screen=self._current_screen,
            lane_sync_state=self._lane_sync_state,
            section_lane_resolver=(
                self._section_lane_resolver() if allow_section_lane_resolver else None
            ),
        )

    async def start(
        self,
        *,
        token: str | None = None,
        ensure_boot_graph: bool = False,
        authenticated: bool | None = None,
    ) -> InterfaceHostServiceState:
        if self.transport_session is not None:
            if getattr(self.transport_session, "binding", None) is None:
                await self.transport_session.ensure_registered()
            if token is not None:
                login = await self.transport_session.login_with_token(token=token)
                self._authenticated = login.actor_id is not None
            elif authenticated is not None:
                self._authenticated = authenticated
        elif authenticated is not None:
            self._authenticated = authenticated
        if self._authenticated:
            self._interface_admitted = True
        await self._refresh_local_runtime_state()
        if self.coordinator is not None:
            if ensure_boot_graph:
                await self._ensure_boot_interface_graph_for_admission()
            else:
                self._runtime_state = await self.coordinator.snapshot()
        await self._refresh_hosted_service_status()
        await self._refresh_host_surface()
        self._started = True
        return self.state()

    async def _ensure_boot_interface_graph_for_admission(self) -> UUID:
        if self.coordinator is None:
            raise RuntimeError("runtime_coordinator_unavailable")
        interface_id = await self.coordinator.ensure_boot_interface_graph()
        self._committed_interface_id = interface_id
        self._runtime_state = await self.coordinator.snapshot()
        return interface_id

    async def _ensure_interface_system_actor_for_admission(
        self,
        *,
        interface_id: UUID,
    ) -> tuple[UUID, UUID]:
        from aware_interface_service.host.interface_admission_actions import (
            stable_interface_system_actor_ids,
        )

        identity_id, actor_id = stable_interface_system_actor_ids(
            interface_id=interface_id,
        )
        self._interface_system_identity_id = identity_id
        self._interface_system_actor_id = actor_id
        return identity_id, actor_id

    def _operator_actor_context(self) -> InterfaceExperienceSessionActorContext | None:
        if not self._authenticated:
            return None
        binding = self.transport_session.binding if self.transport_session else None
        actor_id = _optional_uuid(getattr(binding, "actor_id", None))
        if actor_id is None:
            return None
        return InterfaceExperienceSessionActorContext(
            actor_id=actor_id,
            actor_kind="agent_operator",
            actor_source="transport_binding",
            interface_id=_optional_uuid(getattr(binding, "interface_id", None)),
            interface_session_id=_optional_uuid(
                getattr(binding, "interface_session_id", None)
            ),
            session_label=_optional_string(getattr(binding, "session_label", None)),
            capabilities=tuple(
                str(item)
                for item in tuple(getattr(binding, "capabilities", ()) or ())
                if str(item).strip()
            ),
        )

    def _interface_bootstrap_actor_context(
        self,
    ) -> InterfaceExperienceSessionActorContext | None:
        actor_id = self._interface_system_actor_id
        if actor_id is None:
            return None
        binding = self.transport_session.binding if self.transport_session else None
        capabilities = tuple(
            str(item)
            for item in tuple(getattr(binding, "capabilities", ()) or ())
            if str(item).strip()
        )
        return InterfaceExperienceSessionActorContext(
            actor_id=actor_id,
            actor_kind="service_actor",
            actor_source="interface_bootstrap",
            interface_id=(
                self._committed_interface_id
                or _optional_uuid(getattr(binding, "interface_id", None))
            ),
            interface_system_identity_id=self._interface_system_identity_id,
            interface_session_id=_optional_uuid(
                getattr(binding, "interface_session_id", None)
            ),
            session_label=_optional_string(getattr(binding, "session_label", None)),
            capabilities=capabilities + ("interface_system_bootstrap",),
        )

    def _resolved_service_actor_context(
        self,
    ) -> InterfaceExperienceSessionActorContext | None:
        return (
            self._operator_actor_context() or self._interface_bootstrap_actor_context()
        )

    async def refresh_runtime_state(self) -> InterfaceHostServiceState:
        await self._refresh_local_runtime_state()
        if self.coordinator is None:
            if not self._authenticated or (
                self.bundle_window_layout_enabled
                and self.interface_config_bundle is not None
            ):
                await self._refresh_hosted_service_status()
                await self._refresh_host_surface()
                return self.state()
            raise RuntimeError(
                "Interface host service runtime is missing a coordinator; cannot refresh runtime state."
            )
        self._runtime_state = await self.coordinator.snapshot()
        await self._refresh_hosted_service_status()
        await self._refresh_host_surface()
        return self.state()

    async def heartbeat(
        self, *, timestamp: str | None = None
    ) -> InterfaceHostServiceState:
        if self.transport_session is None:
            raise RuntimeError(
                "Interface host service runtime is missing a transport session; cannot heartbeat."
            )
        await self.transport_session.heartbeat(timestamp=timestamp)
        return self.state()

    async def enter_app_screen(
        self,
        *,
        app_package_id: UUID,
        app_package_branch_id: UUID,
        app_package_object_instance_graph_commit_id: UUID,
        app_config_screen_config_id: UUID,
        reason: str | None = None,
        evidence: Mapping[str, object] | None = None,
        committed_app_screen_resolver: (
            app_screen_capability_mod.CommittedAppScreenResolver | None
        ) = None,
    ) -> InterfaceAppScreenEntryResult:
        updated_at = _utc_now_iso()
        request_evidence = dict(evidence or {})
        resolver = committed_app_screen_resolver or self.app_screen_resolver
        if resolver is None:
            return self._block_app_screen_entry(
                blocker="committed_app_screen_resolver_unavailable",
                app_package_id=app_package_id,
                app_package_branch_id=app_package_branch_id,
                app_package_object_instance_graph_commit_id=(
                    app_package_object_instance_graph_commit_id
                ),
                app_config_screen_config_id=app_config_screen_config_id,
                reason=reason,
                updated_at=updated_at,
                evidence=request_evidence,
            )

        try:
            resolution = await resolver.resolve(
                app_screen_capability_mod.CommittedAppScreenEntryRequest(
                    app_package_id=app_package_id,
                    app_package_branch_id=app_package_branch_id,
                    app_package_object_instance_graph_commit_id=(
                        app_package_object_instance_graph_commit_id
                    ),
                    app_config_screen_config_id=app_config_screen_config_id,
                )
            )
        except Exception as exc:
            return self._block_app_screen_entry(
                blocker="committed_app_screen_resolution_failed",
                app_package_id=app_package_id,
                app_package_branch_id=app_package_branch_id,
                app_package_object_instance_graph_commit_id=(
                    app_package_object_instance_graph_commit_id
                ),
                app_config_screen_config_id=app_config_screen_config_id,
                reason=reason,
                updated_at=updated_at,
                evidence={**request_evidence, "resolution_error": str(exc)},
            )

        resolved_state = app_screen_capability_mod.app_screen_state_from_resolution(
            resolution=resolution,
            reason=reason,
            updated_at=updated_at,
            evidence=request_evidence,
        )
        activator = self.experience_app_screen_activator
        if activator is None:
            return self._block_resolved_app_screen_entry(
                state=resolved_state,
                blocker="experience_app_screen_activator_unavailable",
            )
        try:
            activation = await activator.activate(
                experience_name=resolution.experience_name,
                layout_binding_key=resolution.layout_binding_key,
                rationale=(
                    reason or f"interface_enter_app_screen:{resolution.screen_key}"
                ),
            )
        except Exception as exc:
            return self._block_resolved_app_screen_entry(
                state=resolved_state,
                blocker="experience_layout_graph_binding_activation_failed",
                evidence={"activation_error": str(exc)},
            )
        if not app_screen_capability_mod.experience_activation_succeeded(activation):
            return self._block_resolved_app_screen_entry(
                state=resolved_state,
                blocker=app_screen_capability_mod.experience_activation_error(
                    activation
                ),
            )

        self._app_screen_state = resolved_state
        self._notify_state_changed()
        return InterfaceAppScreenEntryResult(
            state=self.state(),
            app_screen=resolved_state,
        )

    def _block_app_screen_entry(
        self,
        *,
        blocker: str,
        app_package_id: UUID,
        app_package_branch_id: UUID,
        app_package_object_instance_graph_commit_id: UUID,
        app_config_screen_config_id: UUID,
        reason: str | None,
        updated_at: str,
        evidence: Mapping[str, object] | None = None,
    ) -> InterfaceAppScreenEntryResult:
        state = app_screen_capability_mod.blocked_app_screen_state(
            blocker=blocker,
            app_package_id=app_package_id,
            app_package_branch_id=app_package_branch_id,
            app_package_object_instance_graph_commit_id=(
                app_package_object_instance_graph_commit_id
            ),
            app_config_screen_config_id=app_config_screen_config_id,
            reason=reason,
            updated_at=updated_at,
            evidence=evidence,
        )
        self._app_screen_state = state
        self._notify_state_changed()
        return InterfaceAppScreenEntryResult(state=self.state(), app_screen=state)

    def _block_resolved_app_screen_entry(
        self,
        *,
        state: InterfaceAppScreenState,
        blocker: str,
        evidence: Mapping[str, object] | None = None,
    ) -> InterfaceAppScreenEntryResult:
        blocked = replace(
            state,
            status="blocked",
            accepted=False,
            blockers=(blocker,),
            error=blocker,
            evidence={**state.evidence, **dict(evidence or {})},
        )
        self._app_screen_state = blocked
        self._notify_state_changed()
        return InterfaceAppScreenEntryResult(
            state=self.state(),
            app_screen=blocked,
        )

    async def admit_environment_actor(
        self,
        *,
        environment_profile_id: UUID,
        actor_config_id: UUID,
        class_instance_identity_id: UUID,
        environment_id: UUID | None = None,
        object_instance_graph_branch_key: str = "all",
        object_instance_graph_branch_id: UUID | None = None,
        requested_role_config_ids: Sequence[UUID] = (),
        requested_role_config_names: Sequence[str] = (),
        reason: str | None = None,
        evidence: Mapping[str, object] | None = None,
    ) -> InterfaceHostServiceState:
        admission_port = environment_admission_capability_mod.ServiceApiInterfaceEnvironmentAdmissionPort(
            transport_session=self.transport_session,
            context_environment_id=(environment_id or self.environment_id),
            actor_context=self._resolved_service_actor_context(),
        )
        admission_result = await admission_port.admit_actor(
            environment_profile_id=environment_profile_id,
            actor_config_id=actor_config_id,
            class_instance_identity_id=class_instance_identity_id,
            environment_id=environment_id,
            object_instance_graph_branch_key=object_instance_graph_branch_key,
            object_instance_graph_branch_id=object_instance_graph_branch_id,
            requested_role_config_ids=requested_role_config_ids,
            requested_role_config_names=requested_role_config_names,
            reason=reason,
            evidence=evidence,
        )
        self._environment_admission_state = admission_result.admission_state
        self._environment_admission_receipt = (
            admission_result.environment_admission_receipt
        )
        self._environment_session_state = None
        self._environment_navigation_state = None
        self._environment_session_join_receipt = None
        self._environment_navigation_context = None
        self._experience_actor_admission = None
        self._experience_identity_session_config_id = None
        self._experience_lens_state = None
        self._experience_session_handoff_state = None
        self._experience_session_narration_state = None
        self._notify_state_changed()
        return self.state()

    async def enter_environment(
        self,
        *,
        environment_id: UUID | None = None,
        environment_profile_id: UUID | None = None,
        actor_config_id: UUID | None = None,
        class_instance_identity_id: UUID | None = None,
        object_instance_graph_branch_key: str = "all",
        object_instance_graph_branch_id: UUID | None = None,
        requested_role_config_ids: Sequence[UUID] = (),
        requested_role_config_names: Sequence[str] = (),
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
        evidence: Mapping[str, object] | None = None,
    ) -> InterfaceEnvironmentEntryResult:
        entry_port = (
            environment_entry_capability_mod.ServiceApiInterfaceEnvironmentEntryPort(
                transport_session=self.transport_session,
                context_environment_id=environment_id or self.environment_id,
                actor_context=self._resolved_service_actor_context(),
            )
        )
        entry = await entry_port.enter_environment(
            environment_id=environment_id,
            environment_profile_id=environment_profile_id,
            actor_config_id=actor_config_id,
            class_instance_identity_id=class_instance_identity_id,
            object_instance_graph_branch_key=object_instance_graph_branch_key,
            object_instance_graph_branch_id=object_instance_graph_branch_id,
            requested_role_config_ids=requested_role_config_ids,
            requested_role_config_names=requested_role_config_names,
            environment_admission_receipt=(
                environment_admission_receipt or self._environment_admission_receipt
            ),
            environment_session_id=environment_session_id,
            environment_session_config_id=environment_session_config_id,
            session_key=session_key,
            title=title,
            description=description,
            purpose=purpose,
            source_kind=source_kind,
            source_ref=source_ref,
            reason=reason,
            evidence=evidence,
        )
        if entry.environment_admission_state is not None:
            self._environment_admission_state = entry.environment_admission_state
        if entry.environment_admission_receipt is not None:
            self._environment_admission_receipt = entry.environment_admission_receipt
        self._environment_session_state = entry.environment_session_state
        self._environment_session_join_receipt = entry.environment_session_join_receipt
        self._environment_navigation_state = entry.environment_navigation_state
        self._environment_navigation_context = entry.environment_navigation_context
        self._experience_actor_admission = None
        self._experience_identity_session_config_id = None
        self._experience_lens_state = None
        self._experience_session_handoff_state = None
        self._experience_session_narration_state = None
        await self._refresh_environment_navigation_chrome()
        self._notify_state_changed()
        return environment_entry_capability_mod.result_with_state(
            state=self.state(),
            entry=entry,
        )

    async def join_environment_session(
        self,
        *,
        environment_session_id: UUID,
        environment_profile_id: UUID | None = None,
        environment_admission_receipt: EnvironmentActorAdmissionReceipt | None = None,
        reason: str | None = None,
        evidence: Mapping[str, object] | None = None,
    ) -> InterfaceEnvironmentSessionJoinResult:
        session_port = environment_session_capability_mod.ServiceApiInterfaceEnvironmentSessionPort(
            transport_session=self.transport_session,
            context_environment_id=self.environment_id,
            actor_context=self._resolved_service_actor_context(),
        )
        join = await session_port.join_session(
            environment_session_id=environment_session_id,
            environment_profile_id=environment_profile_id,
            environment_admission_receipt=(
                environment_admission_receipt or self._environment_admission_receipt
            ),
            reason=reason,
            evidence=evidence,
        )
        self._environment_session_state = join.environment_session_state
        self._environment_session_join_receipt = join.environment_session_join_receipt
        self._environment_navigation_state = join.environment_navigation_state
        self._environment_navigation_context = join.environment_navigation_context
        self._experience_actor_admission = None
        self._experience_identity_session_config_id = None
        self._experience_lens_state = None
        self._experience_session_handoff_state = None
        self._experience_session_narration_state = None
        await self._refresh_environment_navigation_chrome()
        self._notify_state_changed()
        return environment_session_capability_mod.result_with_state(
            state=self.state(),
            join=join,
        )

    async def select_environment_navigation_target(
        self,
        *,
        environment_navigation_context_id: UUID | None = None,
        selected_process_id: UUID | None = None,
        selected_thread_id: UUID | None = None,
        reason: str | None = None,
        evidence: Mapping[str, object] | None = None,
    ) -> InterfaceEnvironmentNavigationSelectResult:
        mock_selector = getattr(
            self.mock_service_adapter,
            "select_environment_navigation_target",
            None,
        )
        if callable(mock_selector):
            self._environment_navigation_state = mock_selector(
                environment_navigation_context_id=environment_navigation_context_id,
                selected_process_id=selected_process_id,
                selected_thread_id=selected_thread_id,
                reason=reason,
                evidence=evidence,
            )
            runtime_state = getattr(self.mock_service_adapter, "runtime_state", None)
            if callable(runtime_state):
                self._runtime_state = runtime_state()
            self._experience_lens_state = None
            self._environment_navigation_context = None
            self._experience_actor_admission = None
            self._experience_identity_session_config_id = None
            self._experience_session_handoff_state = None
            self._experience_session_narration_state = None
            self._notify_state_changed()
            return environment_navigation_capability_mod.result_with_state(
                state=self.state(),
                selection=environment_navigation_capability_mod.ServiceApiInterfaceEnvironmentNavigationSelection(
                    environment_navigation_state=self._environment_navigation_state,
                ),
            )

        navigation_port = environment_navigation_capability_mod.ServiceApiInterfaceEnvironmentNavigationPort(
            transport_session=self.transport_session,
            context_environment_id=self.environment_id,
            actor_context=self._resolved_service_actor_context(),
        )
        selection = await navigation_port.select_target(
            environment_session_join_receipt=self._environment_session_join_receipt,
            active_navigation_state=self._environment_navigation_state,
            environment_navigation_context_id=environment_navigation_context_id,
            selected_process_id=selected_process_id,
            selected_thread_id=selected_thread_id,
            reason=reason,
            evidence=evidence,
        )
        if selection.environment_navigation_state is not None:
            self._environment_navigation_state = selection.environment_navigation_state
        self._environment_navigation_context = selection.environment_navigation_context
        self._experience_actor_admission = None
        self._experience_identity_session_config_id = None
        self._experience_lens_state = None
        self._experience_session_handoff_state = None
        self._experience_session_narration_state = None
        await self._refresh_environment_navigation_chrome()
        self._notify_state_changed()
        return environment_navigation_capability_mod.result_with_state(
            state=self.state(),
            selection=selection,
        )

    async def resolve_experience_lens(
        self,
        *,
        environment_session_join_receipt: EnvironmentSessionJoinReceipt | None,
        environment_navigation_context: EnvironmentNavigationContextView | None,
        experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None,
        experience_identity_session_config_id: UUID | None,
        reason: str | None = None,
        evidence: Mapping[str, object] | None = None,
    ) -> InterfaceHostServiceState:
        updated_at = _utc_now_iso()
        actor_context = self._resolved_service_actor_context()
        actor_id = actor_context.actor_id if actor_context is not None else None
        if environment_session_join_receipt is not None:
            self._environment_session_join_receipt = environment_session_join_receipt
            self._environment_session_state = experience_lens_capability_mod.environment_session_state_from_join_receipt(
                receipt=environment_session_join_receipt,
                updated_at=updated_at,
            )
        else:
            self._environment_session_state = None
            self._environment_session_join_receipt = None
        if environment_navigation_context is not None:
            self._environment_navigation_context = environment_navigation_context
            self._environment_navigation_state = experience_lens_capability_mod.environment_navigation_state_from_context(
                context=environment_navigation_context,
                actor_id=actor_id,
                updated_at=updated_at,
            )
        else:
            self._environment_navigation_state = None
            self._environment_navigation_context = None
        self._experience_actor_admission = experience_actor_admission
        self._experience_identity_session_config_id = (
            experience_identity_session_config_id
        )

        blocker = self._experience_lens_preflight_blocker(
            actor_id=actor_id,
            environment_session_join_receipt=environment_session_join_receipt,
            environment_navigation_context=environment_navigation_context,
            experience_actor_admission=experience_actor_admission,
            experience_identity_session_config_id=experience_identity_session_config_id,
        )
        if blocker is not None:
            self._experience_lens_state = (
                experience_lens_capability_mod.experience_lens_state_from_blocker(
                    blocker=blocker,
                    actor_id=actor_id,
                    environment_session=self._environment_session_state,
                    environment_navigation=self._environment_navigation_state,
                    updated_at=updated_at,
                )
            )
            self._notify_state_changed()
            return self.state()

        runtime_state = self._runtime_state
        window_layout = (
            runtime_state.window_layout if runtime_state is not None else None
        )
        active_focus = runtime_state.active_focus if runtime_state is not None else None
        if (
            runtime_state is None
            or window_layout is None
            or active_focus is None
            or self.interface_config_bundle is None
        ):
            self._experience_lens_state = (
                experience_lens_capability_mod.experience_lens_state_from_blocker(
                    blocker="current_runtime_focus_required",
                    actor_id=actor_id,
                    environment_session=self._environment_session_state,
                    environment_navigation=self._environment_navigation_state,
                    updated_at=updated_at,
                )
            )
            self._notify_state_changed()
            return self.state()

        section_representations = tuple(runtime_state.section_representations)
        await self._ensure_experience_session_handoff_for_runtime_focus(
            window_layout=window_layout,
            active_focus=active_focus,
            section_representations=section_representations,
            environment_session_join=environment_session_join_receipt,
            environment_navigation_context=environment_navigation_context,
            experience_actor_admission=experience_actor_admission,
            experience_identity_session_config_id=experience_identity_session_config_id,
            require_explicit_contract=True,
        )
        if (
            self._experience_session_handoff_state is None
            or not self._experience_session_handoff_state.admitted
        ):
            blocker = (
                self._experience_session_handoff_state.error
                if self._experience_session_handoff_state is not None
                and self._experience_session_handoff_state.error
                else "experience_session_handoff_required"
            )
            self._experience_lens_state = (
                experience_lens_capability_mod.experience_lens_state_from_blocker(
                    blocker=blocker,
                    actor_id=actor_id,
                    environment_session=self._environment_session_state,
                    environment_navigation=self._environment_navigation_state,
                    updated_at=updated_at,
                )
            )
            self._notify_state_changed()
            return self.state()

        section_key = getattr(active_focus, "section_key", None)
        observable_id = _optional_uuid(getattr(active_focus, "observable_id", None))
        representation = _active_runtime_section_representation(
            active_focus=cast(Any, active_focus),
            section_representations=section_representations,
        )
        activation = await experience_capability_mod.activate_experience_section_graph_binding_for_runtime_focus(
            transport_session=self.transport_session,
            interface_config_bundle=self.interface_config_bundle,
            navigation_context_layout_target=(
                self._runtime_navigation_context_layout_target()
            ),
            section_state_addresses={},
            window_key=window_layout.window_key,
            layout_key=window_layout.layout_key,
            section_key=str(section_key) if section_key is not None else None,
            observable_id=observable_id,
            representation=representation,
        )
        if activation is None:
            self._experience_lens_state = (
                experience_lens_capability_mod.experience_lens_state_from_blocker(
                    blocker="experience_section_graph_binding_not_resolved",
                    actor_id=actor_id,
                    environment_session=self._environment_session_state,
                    environment_navigation=self._environment_navigation_state,
                    updated_at=updated_at,
                )
            )
            self._notify_state_changed()
            return self.state()

        if actor_id is None:
            self._experience_lens_state = (
                experience_lens_capability_mod.experience_lens_state_from_blocker(
                    blocker="actor_identity_required",
                    actor_id=None,
                    environment_session=self._environment_session_state,
                    environment_navigation=self._environment_navigation_state,
                    updated_at=updated_at,
                )
            )
            self._notify_state_changed()
            return self.state()
        self._experience_lens_state = (
            experience_lens_capability_mod.experience_lens_state_from_activation(
                activation=activation,
                actor_id=actor_id,
                environment_session=cast(
                    InterfaceEnvironmentSessionState,
                    self._environment_session_state,
                ),
                environment_navigation=cast(
                    InterfaceEnvironmentNavigationState,
                    self._environment_navigation_state,
                ),
                view_ref=(
                    getattr(representation, "view_ref", None)
                    if representation is not None
                    else None
                ),
                active_focus=cast(Any, active_focus),
                updated_at=updated_at,
                evidence={
                    "reason": reason,
                    "request_evidence": dict(evidence or {}),
                    "experience_session_handoff": (
                        dict(self._experience_session_handoff_state.evidence)
                        if self._experience_session_handoff_state is not None
                        else {}
                    ),
                },
            )
        )
        self._experience_section_view_activations[
            _experience_section_view_cache_key(
                section_key=activation.section_key,
                observable_id=activation.projection_observable_id,
            )
        ] = activation
        self._notify_state_changed()
        return self.state()

    def _experience_lens_preflight_blocker(
        self,
        *,
        actor_id: UUID | None,
        environment_session_join_receipt: EnvironmentSessionJoinReceipt | None,
        environment_navigation_context: EnvironmentNavigationContextView | None,
        experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None,
        experience_identity_session_config_id: UUID | None,
    ) -> str | None:
        if not self._interface_admitted:
            return "interface_admission_required"
        if actor_id is None:
            return "actor_identity_required"
        admission = self._environment_admission_receipt
        if admission is None:
            return "environment_admission_required"
        if not admission.accepted or admission.status != "admitted":
            return "environment_admission_not_admitted"
        if admission.actor_id != actor_id:
            return "environment_admission_actor_scope_mismatch"
        if environment_session_join_receipt is None:
            return "environment_session_join_required"
        if (
            not environment_session_join_receipt.accepted
            or environment_session_join_receipt.status not in {"joined", "started"}
        ):
            return "environment_session_join_not_accepted"
        if environment_session_join_receipt.actor_id != actor_id:
            return "environment_session_actor_scope_mismatch"
        if environment_session_join_receipt.environment_id != admission.environment_id:
            return "environment_session_environment_scope_mismatch"
        if environment_navigation_context is None:
            return "environment_navigation_context_required"
        if environment_navigation_context.status != "active":
            return "environment_navigation_context_not_active"
        if (
            environment_navigation_context.environment_session_id
            != environment_session_join_receipt.environment_session_id
        ):
            return "environment_navigation_session_scope_mismatch"
        if environment_navigation_context.environment_id != admission.environment_id:
            return "environment_navigation_environment_scope_mismatch"
        if experience_actor_admission is None:
            return "experience_actor_admission_required"
        if (
            not experience_actor_admission.accepted
            or experience_actor_admission.status != "admitted"
        ):
            return "experience_actor_admission_not_admitted"
        if experience_actor_admission.actor_id != actor_id:
            return "experience_actor_admission_actor_scope_mismatch"
        if not experience_actor_admission.bindings:
            return "experience_actor_admission_has_no_role_bindings"
        if experience_identity_session_config_id is None:
            return "experience_identity_session_config_required"
        return None

    async def close(self) -> None:
        if self.transport_session is not None:
            await self.transport_session.close()
        self._started = False
        self._authenticated = False
        self._interface_admitted = False
        self._runtime_state = None
        self._committed_interface_id = None
        self._lane_sync_state = None
        self._environment_admission_state = None
        self._environment_session_state = None
        self._environment_navigation_state = None
        self._environment_admission_receipt = None
        self._environment_session_join_receipt = None
        self._environment_navigation_context = None
        self._experience_actor_admission = None
        self._experience_identity_session_config_id = None
        self._experience_lens_state = None
        self._renderer_capabilities = None
        self._local_service_host = None
        self._local_node_runtime = None
        self._hosted_services = None
        self._local_node_log_tail = ()
        self._active_profile_id = _CONSUMER_REMOTE_ADMISSION_PROFILE_ID
        self._attention_runtime_mount_cache_signature = None
        self._attention_runtime_mount_cache = None
        self.bundle_layout_config_id = None
        self.bundle_layout_key = None
        self.bundle_focus_section_key = None
        self.bundle_focus_observable_id = None
        self._workspace_registry = None
        self._workspace_discovery = None
        self._selected_workspace_root = None
        self._joined_workspace_root = None
        self._attached_namespace_counts_by_workspace = {}
        self._selected_workspace = None
        self._selected_semantic_package_selector = None
        self._selected_semantic_package_selector_explicit = False
        self._selected_semantic_package = None
        self._interface_window_layout_request_idempotency = {}
        self._control_plane_profiles = None
        self._selected_step_id = None
        self._selected_step_explicit = False
        self._control_plane_workspace = None
        self._current_screen = None
        self._current_operation = None
        self._allowed_actions = ()
        self._pane_contributions = ()
        self._identity_admission_summary = None
        self._identity_admission_error = None
        self._identity_admission_detail_lines = ()
        self._identity_admission_recent_activity = ()
        self._identity_admission_updated_at = None
        self._experience_session_handoff_state = None
        self._experience_session_narration_state = None

    async def perform_action(
        self,
        *,
        pane_ref: str | None = None,
        action_key: str,
        action_target: host_actions_mod.InterfaceActionTarget | None = None,
        payload: dict[str, object] | None = None,
    ) -> InterfaceHostServiceState:
        return await host_actions_mod.perform_action(
            self,
            pane_ref=pane_ref,
            action_key=action_key,
            action_target=action_target,
            payload=payload,
        )

    async def invoke_api(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: JsonObject | dict[str, object],
        invocation_context: JsonObject | dict[str, object] | None = None,
    ) -> ServiceOperationResponse:
        mock_invoke_api = (
            getattr(self.mock_service_adapter, "invoke_api", None)
            if self.mock_service_adapter is not None
            else None
        )
        if callable(mock_invoke_api):
            response = await cast(
                Callable[..., Awaitable[ServiceOperationResponse]],
                mock_invoke_api,
            )(
                endpoint_ref=endpoint_ref,
                discriminant=discriminant,
                request_payload=request_payload,
                invocation_context=invocation_context,
            )
            await self._refresh_after_mock_service_adapter_operation()
            return response

        transport_client = (
            getattr(self.transport_session, "client", None)
            if self.transport_session is not None
            else None
        )
        raw_invoke_api = (
            getattr(transport_client, "invoke_api_endpoint_raw", None)
            if transport_client is not None
            else None
        )
        if callable(raw_invoke_api):
            raw_invoke = cast(
                Callable[..., Awaitable[object]],
                raw_invoke_api,
            )
            response = await raw_invoke(
                endpoint_ref=endpoint_ref,
                discriminant=discriminant,
                request_payload=request_payload,
                invocation_context=invocation_context,
                timeout_s=10.0,
            )
            return _service_response_from_api_response(response)
        if self.local_runtime is None:
            raise RuntimeError(
                "Interface host API gateway requires a transport session or local runtime."
            )
        snapshot = await self.local_runtime.ensure_service_host_ready()
        service_host = snapshot.service_host
        if not service_host.managed:
            raise RuntimeError(
                "Interface host API gateway currently supports only locally managed Service host routing."
            )
        if not service_host.ready:
            raise RuntimeError(
                service_host.error
                or "Interface host API gateway could not reach a ready local Service host."
            )
        client = ServiceHostDuplexClient(
            endpoint=DuplexIpcEndpoint.unix_socket(
                socket_path=str(self.local_runtime.resolve_service_host_socket_path())
            )
        )
        return await client.send_api_ingress_request(
            request=ServiceHostApiIngressRequest(
                actor_id=self.state().transport.actor_id,
                endpoint_ref=endpoint_ref,
                discriminant=discriminant,
                request_payload=cast(JsonObject, request_payload),
                invocation_context=(
                    cast(JsonObject, invocation_context)
                    if invocation_context is not None
                    else None
                ),
                network_request_id=uuid4(),
                stream_requested=False,
            ),
            timeout_s=10.0,
        )

    async def invoke_sdk_operation(
        self,
        *,
        operation_ref: str,
        discriminant: str,
        request_payload: JsonObject | dict[str, object],
        pane_ref: str | None = None,
        window_key: str | None = None,
        layout_key: str | None = None,
        section_key: str | None = None,
        pane_config_id: UUID | None = None,
        pane_package_id: UUID | None = None,
        pane_package_name: str | None = None,
        view_ref: str | None = None,
        projection_view_key: str | None = None,
        projection_experience_view_id: UUID | None = None,
        state_model_id: UUID | None = None,
        state_provider_ref: str | None = None,
        state_provider_kind: str | None = None,
        layout_section_id: UUID | None = None,
        section_focus_scope_id: UUID | None = None,
        focus_scope_id: UUID | None = None,
        observable_id: UUID | None = None,
        branch_id: UUID | None = None,
        state_projection_hash: str | None = None,
        invocation_context: JsonObject | dict[str, object] | None = None,
    ) -> ServiceOperationResponse:
        _ = (
            discriminant,
            request_payload,
            pane_ref,
            window_key,
            layout_key,
            section_key,
            pane_config_id,
            pane_package_id,
            pane_package_name,
            view_ref,
            projection_view_key,
            projection_experience_view_id,
            state_model_id,
            state_provider_ref,
            state_provider_kind,
            layout_section_id,
            section_focus_scope_id,
            focus_scope_id,
            observable_id,
            branch_id,
            state_projection_hash,
            invocation_context,
        )
        return ServiceOperationResponse(
            status=RequestStatus.failed,
            error=(
                "Interface host SDK operation dispatch is retired. "
                "Pane operations must invoke Experience view actions; "
                "service/runtime operations must use semantic API/service rails."
            ),
            response_payload={
                "operation_ref": operation_ref,
                "retired_rail": "interface_host_sdk_operation_gateway",
            },
            stream_lifecycle=StreamLifecycle.auto_close,
        )

    async def join_selected_workspace(self) -> InterfaceHostServiceState:
        return await host_actions_mod.join_selected_workspace(self)

    async def ensure_selected_workspace_running(self) -> InterfaceHostServiceState:
        return await host_actions_mod.ensure_selected_workspace_running(self)

    async def leave_selected_workspace(self) -> InterfaceHostServiceState:
        return await host_actions_mod.leave_selected_workspace(self)

    async def recover_selected_workspace(self) -> InterfaceHostServiceState:
        return await host_actions_mod.recover_selected_workspace(self)

    async def stop_selected_workspace(self) -> InterfaceHostServiceState:
        return await host_actions_mod.stop_selected_workspace(self)

    async def report_renderer_capabilities(
        self,
        *,
        renderer_capabilities: InterfaceHostServiceRendererCapabilitiesState,
    ) -> InterfaceHostServiceState:
        self._renderer_capabilities = renderer_capabilities
        self._notify_state_changed()
        return self.state()

    async def apply_workspace_session(
        self,
        *,
        selected_workspace_root: Path | None,
        joined_workspace_root: Path | None,
        selected_runtime_focus_section_key: str | None = None,
        selected_runtime_focus_observable_id: UUID | str | None = None,
        attached_namespace_counts_by_workspace: dict[str, int] | None = None,
    ) -> InterfaceHostServiceState:
        return await host_control_plane_mod.apply_workspace_session(
            self,
            selected_workspace_root=selected_workspace_root,
            joined_workspace_root=joined_workspace_root,
            selected_runtime_focus_section_key=selected_runtime_focus_section_key,
            selected_runtime_focus_observable_id=selected_runtime_focus_observable_id,
            attached_namespace_counts_by_workspace=attached_namespace_counts_by_workspace,
        )

    async def select_control_plane_step(
        self,
        *,
        step_id: str | None,
    ) -> InterfaceHostServiceState:
        return await host_control_plane_mod.select_control_plane_step(
            self,
            step_id=step_id,
        )

    async def select_control_plane_profile(
        self,
        *,
        profile_id: str,
    ) -> InterfaceHostServiceState:
        return await host_control_plane_mod.select_control_plane_profile(
            self,
            profile_id=profile_id,
        )

    async def select_control_plane_workspace(
        self,
        *,
        workspace_root: str,
    ) -> InterfaceHostServiceState:
        return await host_control_plane_mod.select_control_plane_workspace(
            self,
            workspace_root=workspace_root,
        )

    async def select_control_plane_semantic_package(
        self,
        *,
        selector_key: str | None,
    ) -> InterfaceHostServiceState:
        return await host_control_plane_mod.select_control_plane_semantic_package(
            self,
            selector_key=selector_key,
        )

    async def select_control_plane_runtime_layout(
        self,
        *,
        layout_config_id: UUID | str | None = None,
    ) -> InterfaceHostServiceState:
        return await host_control_plane_mod.select_control_plane_runtime_layout(
            self,
            layout_config_id=layout_config_id,
        )

    async def activate_control_plane_runtime_focus(
        self,
        *,
        representation_id: UUID | str | None = None,
        layout_config_id: UUID | str | None = None,
        layout_key: str | None = None,
        section_key: str | None = None,
        observable_id: UUID | str | None = None,
    ) -> InterfaceHostServiceState:
        return await host_control_plane_mod.activate_control_plane_runtime_focus(
            self,
            representation_id=representation_id,
            layout_config_id=layout_config_id,
            layout_key=layout_key,
            section_key=section_key,
            observable_id=observable_id,
        )

    async def request_interface_window_layout(
        self,
        *,
        interface_package_id: UUID | str | None = None,
        interface_package_name: str | None = None,
        window_key: str | None = None,
        layout_config_id: UUID | str | None = None,
        layout_key: str | None = None,
        section_key: str | None = None,
        observable_id: UUID | str | None = None,
        representation_id: UUID | str | None = None,
        requested_by_service: str | None = None,
        requested_by_operation: str | None = None,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> InterfaceHostServiceState:
        return await host_control_plane_mod.request_interface_window_layout(
            self,
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
        )

    async def apply_attention_layout_transition(
        self,
        *,
        client_intent_id: str,
        expected_previous_layout_transition_id: UUID | str | None,
        topology_transition_id: UUID | str | None = None,
        section_states: Sequence[attention_capability_mod.AttentionLayoutIntentSection],
        source_ref: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> InterfaceHostAttentionLayoutTransitionResult:
        runtime_state = self._runtime_state
        interface_config_bundle = self.interface_config_bundle
        if runtime_state is None or interface_config_bundle is None:
            raise RuntimeError(
                "Interface layout transition requires a materialized Host runtime."
            )
        attention_session_id = attention_capability_mod.attention_session_id_from_materialized_session_frames(
            runtime_state.materialized_pane_states
        )
        assert attention_session_id is not None
        environment_target = self._attention_environment_runtime_target()
        runtime_mount = await attention_capability_mod.resolve_runtime_mount_from_attention(
            transport_session=self.transport_session,
            interface_config_bundle=interface_config_bundle,
            bundle_window_key=self._preferred_runtime_mount_window_key(),
            section_state_addresses=await self._resolve_host_section_state_addresses(
                window_layout=runtime_state.window_layout,
                allow_section_lane_resolver=False,
            ),
            environment_target=environment_target,
            attention_session_id=attention_session_id,
            preferred_layout_config_id=self._preferred_runtime_mount_layout_config_id(),
            preferred_section_key=self.bundle_focus_section_key,
            preferred_observable_id=self.bundle_focus_observable_id,
        )
        if runtime_mount.attention_session_layout_id is None:
            raise RuntimeError(
                "Attention runtime mount is missing attention_session_layout_id."
            )
        previous_transition_id = (
            expected_previous_layout_transition_id
            if isinstance(expected_previous_layout_transition_id, UUID)
            else (
                UUID(str(expected_previous_layout_transition_id))
                if expected_previous_layout_transition_id is not None
                else None
            )
        )
        pinned_topology_transition_id = (
            topology_transition_id
            if isinstance(topology_transition_id, UUID)
            else (
                UUID(str(topology_transition_id))
                if topology_transition_id is not None
                else None
            )
        )
        result = await attention_capability_mod.apply_session_layout_intent_through_attention(
            transport_session=self.transport_session,
            runtime_mount=runtime_mount,
            intent=attention_capability_mod.AttentionLayoutIntent(
                attention_session_id=attention_session_id,
                attention_session_layout_id=(runtime_mount.attention_session_layout_id),
                client_intent_id=client_intent_id,
                expected_previous_layout_transition_id=previous_transition_id,
                topology_transition_id=pinned_topology_transition_id,
                section_states=tuple(section_states),
                source_ref=source_ref,
                metadata=metadata or {},
            ),
        )
        refreshed_mount = (
            await attention_capability_mod.resolve_runtime_mount_from_attention(
                transport_session=self.transport_session,
                interface_config_bundle=interface_config_bundle,
                bundle_window_key=self._preferred_runtime_mount_window_key(),
                section_state_addresses=runtime_mount.section_state_addresses,
                environment_target=environment_target,
                attention_session_id=attention_session_id,
                preferred_layout_config_id=(
                    runtime_mount.active_layout_config_id
                    or self._preferred_runtime_mount_layout_config_id()
                ),
                preferred_section_key=self.bundle_focus_section_key,
                preferred_observable_id=self.bundle_focus_observable_id,
            )
        )
        refreshed_request = attention_capability_mod.build_watch_runtime_mount_request(
            interface_config_bundle=interface_config_bundle,
            bundle_window_key=self._preferred_runtime_mount_window_key(),
            environment_target=environment_target,
            attention_session_id=attention_session_id,
            preferred_layout_config_id=refreshed_mount.active_layout_config_id,
            preferred_layout_key=refreshed_mount.active_layout_key,
            preferred_section_key=self.bundle_focus_section_key,
            preferred_observable_id=self.bundle_focus_observable_id,
        )
        self._attention_runtime_mount_cache_signature = (
            attention_capability_mod.runtime_mount_watch_request_signature(
                refreshed_request
            )
        )
        self._attention_runtime_mount_cache = refreshed_mount
        if not await self._apply_streamed_attention_runtime_mount_resolution(
            resolution=refreshed_mount
        ):
            raise RuntimeError(
                "Interface Host could not reconcile the refreshed Attention runtime mount."
            )
        transition = result.reconciliation_transition
        return InterfaceHostAttentionLayoutTransitionResult(
            outcome=result.outcome,
            conflict_reason=result.conflict_reason,
            active_layout_transition_id=(
                transition.attention_layout_transition_id if transition else None
            ),
            active_topology_transition_id=(
                refreshed_mount.active_topology_transition_id
            ),
            object_instance_graph_commit_id=(
                transition.object_instance_graph_commit_id if transition else None
            ),
            graph_hash_post=transition.graph_hash_post if transition else None,
            state=self.state(),
        )

    async def apply_attention_layout_topology_transition(
        self,
        *,
        client_intent_id: str,
        expected_previous_topology_transition_id: UUID | str | None,
        section_states: Sequence[
            attention_capability_mod.AttentionLayoutTopologyIntentSection
        ],
        source_ref: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> InterfaceHostAttentionLayoutTopologyTransitionResult:
        runtime_state = self._runtime_state
        interface_config_bundle = self.interface_config_bundle
        if runtime_state is None or interface_config_bundle is None:
            raise RuntimeError(
                "Interface layout topology transition requires a materialized Host runtime."
            )
        attention_session_id = attention_capability_mod.attention_session_id_from_materialized_session_frames(
            runtime_state.materialized_pane_states
        )
        assert attention_session_id is not None
        environment_target = self._attention_environment_runtime_target()
        runtime_mount = await attention_capability_mod.resolve_runtime_mount_from_attention(
            transport_session=self.transport_session,
            interface_config_bundle=interface_config_bundle,
            bundle_window_key=self._preferred_runtime_mount_window_key(),
            section_state_addresses=await self._resolve_host_section_state_addresses(
                window_layout=runtime_state.window_layout,
                allow_section_lane_resolver=False,
            ),
            environment_target=environment_target,
            attention_session_id=attention_session_id,
            preferred_layout_config_id=self._preferred_runtime_mount_layout_config_id(),
            preferred_section_key=self.bundle_focus_section_key,
            preferred_observable_id=self.bundle_focus_observable_id,
        )
        if runtime_mount.attention_session_layout_id is None:
            raise RuntimeError(
                "Attention runtime mount is missing attention_session_layout_id."
            )
        previous_transition_id = (
            expected_previous_topology_transition_id
            if isinstance(expected_previous_topology_transition_id, UUID)
            else (
                UUID(str(expected_previous_topology_transition_id))
                if expected_previous_topology_transition_id is not None
                else None
            )
        )
        result = await attention_capability_mod.apply_session_layout_topology_intent_through_attention(
            transport_session=self.transport_session,
            runtime_mount=runtime_mount,
            intent=attention_capability_mod.AttentionLayoutTopologyIntent(
                attention_session_id=attention_session_id,
                attention_session_layout_id=runtime_mount.attention_session_layout_id,
                client_intent_id=client_intent_id,
                expected_previous_topology_transition_id=previous_transition_id,
                section_states=tuple(section_states),
                source_ref=source_ref,
                metadata=metadata or {},
            ),
        )
        refreshed_mount = (
            await attention_capability_mod.resolve_runtime_mount_from_attention(
                transport_session=self.transport_session,
                interface_config_bundle=interface_config_bundle,
                bundle_window_key=self._preferred_runtime_mount_window_key(),
                section_state_addresses=runtime_mount.section_state_addresses,
                environment_target=environment_target,
                attention_session_id=attention_session_id,
                preferred_layout_config_id=(
                    runtime_mount.active_layout_config_id
                    or self._preferred_runtime_mount_layout_config_id()
                ),
                preferred_section_key=self.bundle_focus_section_key,
                preferred_observable_id=self.bundle_focus_observable_id,
            )
        )
        refreshed_request = attention_capability_mod.build_watch_runtime_mount_request(
            interface_config_bundle=interface_config_bundle,
            bundle_window_key=self._preferred_runtime_mount_window_key(),
            environment_target=environment_target,
            attention_session_id=attention_session_id,
            preferred_layout_config_id=refreshed_mount.active_layout_config_id,
            preferred_layout_key=refreshed_mount.active_layout_key,
            preferred_section_key=self.bundle_focus_section_key,
            preferred_observable_id=self.bundle_focus_observable_id,
        )
        self._attention_runtime_mount_cache_signature = (
            attention_capability_mod.runtime_mount_watch_request_signature(
                refreshed_request
            )
        )
        self._attention_runtime_mount_cache = refreshed_mount
        if not await self._apply_streamed_attention_runtime_mount_resolution(
            resolution=refreshed_mount
        ):
            raise RuntimeError(
                "Interface Host could not reconcile the refreshed Attention runtime mount."
            )
        transition = result.reconciliation_transition
        return InterfaceHostAttentionLayoutTopologyTransitionResult(
            outcome=result.outcome,
            conflict_reason=result.conflict_reason,
            active_topology_transition_id=(
                transition.attention_layout_topology_transition_id
                if transition
                else None
            ),
            object_instance_graph_commit_id=(
                transition.object_instance_graph_commit_id if transition else None
            ),
            graph_hash_post=transition.graph_hash_post if transition else None,
            state=self.state(),
        )

    def activate_interface_config_bundle_for_request(
        self,
        *,
        interface_package_id: UUID | str | None = None,
        interface_package_name: str | None = None,
    ) -> InterfaceConfigBundle | None:
        if _bundle_matches_request(
            bundle=self.interface_config_bundle,
            interface_package_id=interface_package_id,
            interface_package_name=interface_package_name,
        ):
            return self.interface_config_bundle
        if interface_package_id is None and not (interface_package_name or "").strip():
            return self.interface_config_bundle
        result = load_workspace_interface_config_bundle(
            repository_root=self.repository_root,
            interface_package_id=interface_package_id,
            interface_package_name=interface_package_name,
        )
        if result.bundle is None:
            return self.interface_config_bundle
        if self.interface_config_bundle == result.bundle:
            return self.interface_config_bundle
        self.interface_config_bundle = result.bundle
        self.bundle_window_layout_enabled = True
        self.bundle_window_key = None
        self.bundle_layout_config_id = None
        self.bundle_layout_key = None
        self.bundle_focus_section_key = None
        self.bundle_focus_observable_id = None
        self._attention_runtime_mount_cache_signature = None
        self._attention_runtime_mount_cache = None
        return self.interface_config_bundle

    async def sync_focus_scope_lane_once(
        self,
        *,
        window_key: str = "execution",
        include_commit_payload: bool = True,
        force: bool = False,
    ) -> InterfaceHostServiceState:
        return await host_lane_sync_mod.sync_focus_scope_lane_once(
            cast(
                host_lane_sync_mod.InterfaceHostLaneSyncRuntime,
                cast(object, self),
            ),
            window_key=window_key,
            include_commit_payload=include_commit_payload,
            force=force,
        )

    async def watch_focus_scope_lane(
        self,
        *,
        window_key: str = "execution",
        include_initial: bool = False,
        include_commit_payload: bool = True,
        force: bool = False,
    ) -> None:
        await host_lane_sync_mod.watch_focus_scope_lane(
            cast(
                host_lane_sync_mod.InterfaceHostLaneSyncRuntime,
                cast(object, self),
            ),
            window_key=window_key,
            include_initial=include_initial,
            include_commit_payload=include_commit_payload,
            force=force,
        )

    def _preferred_runtime_mount_layout_config_id(self) -> UUID | None:
        target = self._runtime_navigation_context_layout_target()
        if target is not None and target.layout_config_id is not None:
            return target.layout_config_id
        if self.bundle_layout_config_id is not None:
            return self.bundle_layout_config_id
        if self._runtime_state is not None:
            return self._runtime_state.active_layout_config_id
        return None

    def _preferred_runtime_mount_layout_key(self) -> str | None:
        target = self._runtime_navigation_context_layout_target()
        if target is not None and target.layout_key:
            return target.layout_key
        if self.bundle_layout_key is not None:
            return self.bundle_layout_key
        if (
            self._runtime_state is not None
            and self._runtime_state.window_layout is not None
        ):
            return self._runtime_state.window_layout.layout_key
        return None

    def _preferred_runtime_mount_window_key(self) -> str | None:
        target = self._runtime_navigation_context_layout_target()
        if target is not None and target.window_key:
            return target.window_key
        return self.bundle_window_key

    def _runtime_navigation_context_layout_target(
        self,
    ) -> InterfaceNavigationContextLayoutTargetState | None:
        if self._runtime_state is None:
            return None
        return self._runtime_state.navigation_context_layout_target

    def _attention_environment_runtime_target(
        self,
    ) -> attention_capability_mod.AttentionEnvironmentRuntimeTarget | None:
        return attention_capability_mod.build_attention_environment_runtime_target(
            navigation_context_layout_target=self._runtime_navigation_context_layout_target(),
        )

    def _active_attention_session_id(self) -> UUID | None:
        runtime_state = self._runtime_state
        if runtime_state is None:
            return None
        return attention_capability_mod.attention_session_id_from_materialized_session_frames(
            runtime_state.materialized_pane_states,
            required=False,
        )

    async def watch_attention_runtime_mount(
        self,
        *,
        poll_interval_ms: int = 1000,
        recheck_interval_s: float = 1.0,
    ) -> None:
        if (
            not self.bundle_window_layout_enabled
            or self.interface_config_bundle is None
        ):
            return
        reconnect_interval_s = max(recheck_interval_s, 0.25)
        while True:
            environment_target = self._attention_environment_runtime_target()
            attention_session_id = self._active_attention_session_id()
            request = attention_capability_mod.build_watch_runtime_mount_request(
                interface_config_bundle=self.interface_config_bundle,
                bundle_window_key=self._preferred_runtime_mount_window_key(),
                environment_target=environment_target,
                attention_session_id=attention_session_id,
                preferred_layout_config_id=(
                    self._preferred_runtime_mount_layout_config_id()
                ),
                preferred_layout_key=self._preferred_runtime_mount_layout_key(),
                preferred_section_key=self.bundle_focus_section_key,
                preferred_observable_id=self.bundle_focus_observable_id,
                poll_interval_ms=poll_interval_ms,
            )
            request_signature = (
                attention_capability_mod.runtime_mount_watch_request_signature(request)
            )
            if request is None or request_signature is None:
                await asyncio.sleep(reconnect_interval_s)
                continue
            try:
                section_state_addresses = (
                    await self._resolve_host_section_state_addresses(
                        window_layout=(
                            self._runtime_state.window_layout
                            if self._runtime_state is not None
                            else None
                        ),
                        allow_section_lane_resolver=False,
                    )
                )
                stream = attention_capability_mod.stream_runtime_mount_from_attention(
                    transport_session=self.transport_session,
                    interface_config_bundle=self.interface_config_bundle,
                    bundle_window_key=self._preferred_runtime_mount_window_key(),
                    section_state_addresses=section_state_addresses,
                    environment_target=environment_target,
                    attention_session_id=attention_session_id,
                    preferred_layout_config_id=request.preferred_layout_config_id,
                    preferred_layout_key=request.preferred_layout_key,
                    preferred_section_key=request.preferred_section_key,
                    preferred_observable_id=request.preferred_observable_id,
                    poll_interval_ms=request.poll_interval_ms,
                )
                stream_iter = stream.__aiter__()
                next_event_task: (
                    asyncio.Task[
                        attention_capability_mod.AttentionRuntimeMountResolution
                    ]
                    | None
                ) = None
                try:
                    while True:
                        current_environment_target = (
                            self._attention_environment_runtime_target()
                        )
                        current_signature = attention_capability_mod.runtime_mount_watch_request_signature(
                            attention_capability_mod.build_watch_runtime_mount_request(
                                interface_config_bundle=self.interface_config_bundle,
                                bundle_window_key=(
                                    self._preferred_runtime_mount_window_key()
                                ),
                                environment_target=current_environment_target,
                                attention_session_id=(
                                    self._active_attention_session_id()
                                ),
                                preferred_layout_config_id=(
                                    self._preferred_runtime_mount_layout_config_id()
                                ),
                                preferred_layout_key=(
                                    self._preferred_runtime_mount_layout_key()
                                ),
                                preferred_section_key=self.bundle_focus_section_key,
                                preferred_observable_id=self.bundle_focus_observable_id,
                                poll_interval_ms=poll_interval_ms,
                            )
                        )
                        if current_signature != request_signature:
                            break
                        if next_event_task is None:
                            next_event_task = asyncio.create_task(
                                stream_iter.__anext__()
                            )
                        done, _pending = await asyncio.wait(
                            {next_event_task},
                            timeout=reconnect_interval_s,
                        )
                        if not done:
                            continue
                        try:
                            resolution = next_event_task.result()
                        except StopAsyncIteration:
                            break
                        finally:
                            next_event_task = None
                        layout_changed = (
                            self._runtime_state is None
                            or self._runtime_state.active_layout_config_id
                            != resolution.active_layout_config_id
                        )
                        transition_changed = (
                            self._runtime_state is None
                            or self._runtime_state.window_layout is None
                            or self._runtime_state.window_layout.active_layout_transition_id
                            != resolution.active_layout_transition_id
                        )
                        topology_changed = (
                            self._runtime_state is None
                            or self._runtime_state.window_layout is None
                            or self._runtime_state.window_layout.active_topology_transition_id
                            != resolution.active_topology_transition_id
                        )
                        if (
                            not layout_changed
                            and not transition_changed
                            and not topology_changed
                            and self.bundle_focus_section_key
                            == resolution.active_section_key
                            and self.bundle_focus_observable_id
                            == resolution.active_observable_id
                        ):
                            continue
                        self.bundle_layout_config_id = (
                            resolution.active_layout_config_id
                        )
                        self.bundle_layout_key = resolution.active_layout_key
                        self.bundle_focus_section_key = resolution.active_section_key
                        self.bundle_focus_observable_id = (
                            resolution.active_observable_id
                        )
                        if self._runtime_state is not None:
                            self._runtime_state = replace(
                                self._runtime_state,
                                active_layout_config_id=(
                                    resolution.active_layout_config_id
                                ),
                            )
                        next_environment_target = (
                            self._attention_environment_runtime_target()
                        )
                        next_request_signature = attention_capability_mod.runtime_mount_watch_request_signature(
                            attention_capability_mod.build_watch_runtime_mount_request(
                                interface_config_bundle=self.interface_config_bundle,
                                bundle_window_key=(
                                    self._preferred_runtime_mount_window_key()
                                ),
                                environment_target=next_environment_target,
                                attention_session_id=(
                                    self._active_attention_session_id()
                                ),
                                preferred_layout_config_id=(
                                    self._preferred_runtime_mount_layout_config_id()
                                ),
                                preferred_layout_key=(
                                    self._preferred_runtime_mount_layout_key()
                                ),
                                preferred_section_key=self.bundle_focus_section_key,
                                preferred_observable_id=self.bundle_focus_observable_id,
                                poll_interval_ms=poll_interval_ms,
                            )
                        )
                        if next_request_signature is not None:
                            request_signature = next_request_signature
                            self._attention_runtime_mount_cache_signature = (
                                next_request_signature
                            )
                            self._attention_runtime_mount_cache = resolution
                        if await self._apply_streamed_attention_runtime_mount_resolution(
                            resolution=resolution
                        ):
                            continue
                        await self._refresh_runtime_mount_surface_from_cached_state()
                finally:
                    if next_event_task is not None and not next_event_task.done():
                        next_event_task.cancel()
                        with suppress(asyncio.CancelledError):
                            await next_event_task
                    aclose = getattr(stream_iter, "aclose", None)
                    if callable(aclose):
                        with suppress(Exception):
                            await aclose()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning(
                    "aware_interface_service attention runtime-mount watch failed: %s",
                    exc,
                )
            await asyncio.sleep(reconnect_interval_s)

    def state(self) -> InterfaceHostServiceState:
        return host_status_mod.build_service_state(
            cast(host_status_mod.InterfaceHostStatusRuntime, cast(object, self))
        )

    def state_revision(self) -> int:
        return self._state_revision

    def _sync_pane_api_allowed_actions(self) -> None:
        self._allowed_actions = _merge_pane_api_allowed_actions(
            runtime_state=self._runtime_state,
            existing_actions=self._allowed_actions,
        )

    async def _refresh_environment_navigation_chrome(self) -> None:
        runtime_state = self._runtime_state
        if runtime_state is None:
            return
        materialized_pane_states = runtime_state.materialized_pane_states
        navigator_state = await environment_navigation_capability_mod.environment_navigator_materialized_pane_state(
            transport_session=self.transport_session,
            navigation_state=self._environment_navigation_state,
        )
        if navigator_state is not None:
            materialized_pane_states = _replace_materialized_pane_state(
                materialized_pane_states,
                navigator_state,
            )
        thread_layout_state = await environment_navigation_capability_mod.environment_thread_layout_materialized_pane_state(
            transport_session=self.transport_session,
            navigation_state=self._environment_navigation_state,
        )
        if thread_layout_state is not None:
            materialized_pane_states = _replace_materialized_pane_state(
                materialized_pane_states,
                thread_layout_state,
            )
        if materialized_pane_states == runtime_state.materialized_pane_states:
            return
        self._runtime_state = replace(
            runtime_state,
            materialized_pane_states=materialized_pane_states,
        )

    async def _ensure_experience_session_handoff_for_runtime_focus(
        self,
        *,
        window_layout: InterfaceWindowLayoutState | None,
        active_focus: object,
        section_representations: tuple[
            "InterfaceRuntimeSectionRepresentationState",
            ...,
        ],
        environment_session_join: EnvironmentSessionJoinReceipt | None = None,
        environment_navigation_context: EnvironmentNavigationContextView | None = None,
        experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None = None,
        experience_identity_session_config_id: UUID | None = None,
        require_explicit_contract: bool = False,
    ) -> None:
        if not require_explicit_contract and (
            environment_session_join is None
            or environment_navigation_context is None
            or experience_actor_admission is None
            or experience_identity_session_config_id is None
        ):
            return
        provider = self.experience_session_handoff_provider
        if provider is None:
            provider = experience_session_capability_mod.build_experience_sdk_session_handoff_provider(
                transport_session=self.transport_session,
            )
        if provider is None:
            return
        request = (
            experience_session_capability_mod.build_experience_session_handoff_request(
                namespace=self.namespace,
                authenticated=self._authenticated,
                interface_admitted=self._interface_admitted,
                transport_binding=(
                    self.transport_session.binding if self.transport_session else None
                ),
                actor_context=self._resolved_service_actor_context(),
                runtime_state=self._runtime_state,
                window_layout=window_layout,
                active_focus=cast(Any, active_focus),
                section_representations=section_representations,
                environment_admission=self._environment_admission_receipt,
                environment_session_join=environment_session_join,
                environment_navigation_context=environment_navigation_context,
                experience_actor_admission=experience_actor_admission,
                experience_identity_session_config_id=(
                    experience_identity_session_config_id
                ),
                host_environment_id=self.environment_id,
            )
        )
        if request is None:
            self._experience_session_handoff_state = None
            self._experience_session_narration_state = None
            return
        blocker = experience_session_capability_mod.experience_session_handoff_blocker(
            request
        )
        if blocker is not None:
            self._experience_session_handoff_state = (
                experience_session_capability_mod.handoff_state_from_blocker(
                    request=request,
                    blocker=blocker,
                )
            )
            return
        try:
            result = await provider.ensure_experience_session_handoff(request)
        except Exception as exc:
            self._experience_session_handoff_state = (
                experience_session_capability_mod.handoff_state_from_failure(
                    request=request,
                    error=exc,
                )
            )
            return
        self._experience_session_handoff_state = (
            experience_session_capability_mod.handoff_state_from_result(result)
        )
        if self._experience_session_handoff_state.feature_enabled:
            await self._ensure_experience_session_narration_for_runtime_focus(
                provider=provider,
                window_layout=window_layout,
                active_focus=active_focus,
                section_representations=section_representations,
                environment_session_join=environment_session_join,
                environment_navigation_context=environment_navigation_context,
                experience_actor_admission=experience_actor_admission,
                experience_identity_session_config_id=(
                    experience_identity_session_config_id
                ),
            )
        else:
            self._experience_session_narration_state = None

    async def _ensure_experience_session_narration_for_runtime_focus(
        self,
        *,
        provider: experience_session_capability_mod.ExperienceSessionHandoffProvider,
        window_layout: InterfaceWindowLayoutState | None,
        active_focus: object,
        section_representations: tuple[
            "InterfaceRuntimeSectionRepresentationState",
            ...,
        ],
        environment_session_join: EnvironmentSessionJoinReceipt | None,
        environment_navigation_context: EnvironmentNavigationContextView | None,
        experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None,
        experience_identity_session_config_id: UUID | None,
    ) -> None:
        request = experience_session_capability_mod.build_experience_session_handoff_request(
            namespace=self.namespace,
            authenticated=self._authenticated,
            interface_admitted=self._interface_admitted,
            transport_binding=(
                self.transport_session.binding if self.transport_session else None
            ),
            actor_context=self._resolved_service_actor_context(),
            runtime_state=self._runtime_state,
            window_layout=window_layout,
            active_focus=cast(Any, active_focus),
            section_representations=section_representations,
            environment_admission=self._environment_admission_receipt,
            environment_session_join=environment_session_join,
            environment_navigation_context=environment_navigation_context,
            experience_actor_admission=experience_actor_admission,
            experience_identity_session_config_id=(
                experience_identity_session_config_id
            ),
            host_environment_id=self.environment_id,
            feature_key=(
                experience_session_capability_mod.EXPERIENCE_SESSION_NARRATOR_FEATURE_KEY
            ),
        )
        if request is None:
            self._experience_session_narration_state = None
            return
        blocker = experience_session_capability_mod.experience_session_handoff_blocker(
            request
        )
        if blocker is not None:
            self._experience_session_narration_state = (
                experience_session_capability_mod.narration_state_from_blocker(
                    request=request,
                    blocker=blocker,
                )
            )
            return
        try:
            result = await provider.ensure_experience_session_handoff(request)
            self._experience_session_narration_state = (
                experience_session_capability_mod.narration_state_from_result(result)
            )
            status_reader = getattr(
                provider,
                "get_experience_session_narration",
                None,
            )
            if callable(status_reader):
                self._experience_session_narration_state = await status_reader(request)
        except Exception as exc:
            self._experience_session_narration_state = (
                experience_session_capability_mod.narration_state_from_failure(
                    request=request,
                    error=exc,
                )
            )

    async def _retry_experience_session_handoff_for_current_runtime_focus(
        self,
    ) -> None:
        runtime_state = self._runtime_state
        if runtime_state is None:
            return
        window_layout = runtime_state.window_layout
        active_focus = runtime_state.active_focus
        if window_layout is None or active_focus is None:
            return
        await self._ensure_experience_session_handoff_for_runtime_focus(
            window_layout=window_layout,
            active_focus=active_focus,
            section_representations=tuple(runtime_state.section_representations),
        )

    async def wait_for_state_change(
        self,
        *,
        after_revision: int,
        timeout_s: float,
    ) -> bool:
        if self._state_revision != after_revision:
            return True
        event = self._state_change_event
        if self._state_revision != after_revision:
            return True
        try:
            await asyncio.wait_for(event.wait(), timeout=max(timeout_s, 0.0))
        except asyncio.TimeoutError:
            return self._state_revision != after_revision
        return True

    def _require_selected_workspace(self) -> InterfaceHostServiceSelectedWorkspaceState:
        selected_workspace = self._selected_workspace
        if selected_workspace is None:
            raise RuntimeError("Select a workspace first.")
        return selected_workspace

    async def _refresh_host_surface(self) -> None:
        await self._refresh_host_surface_from_cached_state()

    async def _refresh_after_mock_service_adapter_operation(self) -> None:
        adapter_snapshot = (
            getattr(self.mock_service_adapter, "snapshot", None)
            if self.mock_service_adapter is not None
            else None
        )
        if not callable(adapter_snapshot):
            return
        self._runtime_state = await cast(
            Callable[[], Awaitable[InterfaceRuntimeState]],
            adapter_snapshot,
        )()
        await self._refresh_hosted_service_status()
        await self._refresh_host_surface()

    async def _refresh_host_surface_from_cached_state(self) -> None:
        product = _compose_host_product(self._product_inputs())
        self._selected_step_id = product.selected_step_id
        self._current_screen = product.current_screen
        self._pane_contributions = product.pane_contributions
        self._allowed_actions = product.allowed_actions
        self._current_operation = product.current_operation
        self._control_plane_workspace = product.control_plane_workspace
        self._control_plane_profiles = product.control_plane_profiles
        await self._refresh_runtime_mount_surface_from_cached_state()

    async def _refresh_runtime_mount_surface_from_cached_state(self) -> None:
        await self._refresh_runtime_window_layout()
        await self._hydrate_experience_view_state_subscriptions()
        self._notify_state_changed()

    async def _hydrate_experience_view_state_subscriptions(self) -> None:
        runtime_state = self._runtime_state
        if runtime_state is None or self.transport_session is None:
            return
        client = AwareExperienceServiceApiClient(self.transport_session.client)
        session_view_frame_requests = (
            self._experience_session_view_frame_requests_by_pane_state_key(
                runtime_state=runtime_state,
            )
        )

        async def _watch_experience_view_state(request):  # type: ignore[no-untyped-def]
            return await client.experience.watch_experience_view_state.watch_experience_view_state(
                request
            )

        result = await host_view_state_subscription_mod.hydrate_experience_view_state_subscriptions(
            runtime_state=runtime_state,
            watch_experience_view_state=_watch_experience_view_state,
            provider_contexts_by_pane_state_key=(
                self.experience_view_state_provider_contexts
            ),
            session_view_frame_requests_by_pane_state_key=(session_view_frame_requests),
        )
        next_state = result.runtime_state
        if result.errors:
            next_state = replace(
                next_state,
                warnings=_merge_experience_view_state_subscription_warnings(
                    existing=next_state.warnings,
                    errors=tuple(result.errors),
                ),
            )
        if next_state != runtime_state:
            self._runtime_state = next_state

    async def _refresh_experience_view_state_subscription_after_action(
        self,
        *,
        mounted_action_ref: object,
        request_payload: Mapping[str, object],
        response_payload: Mapping[str, object],
    ) -> bool:
        runtime_state = self._runtime_state
        if runtime_state is None or self.transport_session is None:
            return False
        pane = host_view_state_subscription_mod.pane_for_mounted_action_ref(
            runtime_state=runtime_state,
            mounted_action_ref=mounted_action_ref,
        )
        if pane is None:
            return False
        session_view_frame_request = (
            self._experience_session_view_frame_request_for_pane(
                runtime_state=runtime_state,
                pane=pane,
            )
        )
        client = AwareExperienceServiceApiClient(self.transport_session.client)

        async def _watch_experience_view_state(request):  # type: ignore[no-untyped-def]
            return await client.experience.watch_experience_view_state.watch_experience_view_state(
                request
            )

        result = await host_view_state_subscription_mod.refresh_experience_view_state_subscription(
            runtime_state=runtime_state,
            pane=pane,
            watch_experience_view_state=_watch_experience_view_state,
            provider_contexts_by_pane_state_key=(
                self.experience_view_state_provider_contexts
            ),
            session_view_frame_request=session_view_frame_request,
            refresh_trigger=_experience_view_action_refresh_trigger(
                mounted_action_ref=mounted_action_ref,
                request_payload=request_payload,
                response_payload=response_payload,
            ),
        )
        next_state = result.runtime_state
        if result.errors:
            next_state = replace(
                next_state,
                warnings=_merge_experience_view_state_subscription_warnings(
                    existing=next_state.warnings,
                    errors=tuple(result.errors),
                ),
            )
        if next_state != runtime_state:
            self._runtime_state = next_state
            return True
        return False

    def _experience_session_view_frame_requests_by_pane_state_key(
        self,
        *,
        runtime_state: InterfaceRuntimeState,
    ) -> dict[str, object]:
        requests: dict[str, object] = {}
        for pane in runtime_state.resolved_panes:
            request = self._experience_session_view_frame_request_for_pane(
                runtime_state=runtime_state,
                pane=pane,
            )
            if request is None:
                continue
            requests[_pane_state_key_for_descriptor(pane)] = request
        return requests

    def _experience_session_view_frame_request_for_pane(
        self,
        *,
        runtime_state: InterfaceRuntimeState,
        pane: InterfaceResolvedPaneDescriptor,
    ) -> object | None:
        return experience_session_capability_mod.build_experience_session_view_frame_request_for_pane(
            namespace=self.namespace,
            authenticated=self._authenticated,
            interface_admitted=self._interface_admitted,
            transport_binding=(
                self.transport_session.binding if self.transport_session else None
            ),
            actor_context=self._resolved_service_actor_context(),
            runtime_state=runtime_state,
            pane=pane,
            active_focus=runtime_state.active_focus,
            section_representations=tuple(runtime_state.section_representations),
            environment_admission=self._environment_admission_receipt,
            environment_session_join=self._environment_session_join_receipt,
            environment_navigation_context=self._environment_navigation_context,
            experience_actor_admission=self._experience_actor_admission,
            experience_identity_session_config_id=(
                self._experience_identity_session_config_id
            ),
            host_environment_id=self.environment_id,
        )

    async def _apply_streamed_attention_runtime_mount_resolution(
        self,
        *,
        resolution: attention_capability_mod.AttentionRuntimeMountResolution,
    ) -> bool:
        if self._runtime_state is None or self.interface_config_bundle is None:
            return False
        expected_environment_target = self._attention_environment_runtime_target()
        if expected_environment_target is not None:
            if not attention_capability_mod.environment_runtime_targets_match(
                actual=resolution.environment_target,
                expected=expected_environment_target,
            ):
                return False
        layout_inputs = self._layout_inputs()
        current_window_layout = self._runtime_state.window_layout
        layout_matches = current_window_layout is not None and (
            resolution.active_layout_config_id == current_window_layout.layout_config_id
            if resolution.active_layout_config_id is not None
            else (
                (resolution.active_layout_key or "").strip().casefold()
                == current_window_layout.layout_key.strip().casefold()
            )
        )
        window_layout = current_window_layout
        if not layout_matches:
            resolved_at = _utc_now_iso()
            window_layout = host_layout_mod.build_runtime_window_layout(
                inputs=replace(
                    layout_inputs,
                    bundle_layout_config_id=resolution.active_layout_config_id,
                    bundle_layout_key=resolution.active_layout_key,
                ),
                resolved_at=resolved_at,
            )
        if window_layout is None:
            return False
        window_layout = host_layout_mod.apply_runtime_layout_sections(
            window_layout=window_layout,
            runtime_sections=resolution.window_layout_sections,
        )
        window_layout = attention_capability_mod.pin_window_layout_to_runtime_mount(
            window_layout=window_layout,
            resolution=resolution,
        )
        section_state_addresses = host_layout_mod.merge_section_state_addresses(
            base=await self._resolve_host_section_state_addresses(
                window_layout=window_layout,
                allow_section_lane_resolver=False,
            ),
            overlay=resolution.section_state_addresses,
        )
        active_focus = host_layout_mod.attention_owned_runtime_focus(
            window_layout=window_layout,
            section_state_addresses=section_state_addresses,
            active_section_key=resolution.active_section_key,
            active_observable_id=resolution.active_observable_id,
        )
        self.bundle_focus_section_key = (
            active_focus.section_key if active_focus is not None else None
        )
        self.bundle_focus_observable_id = (
            active_focus.observable_id if active_focus is not None else None
        )
        self.bundle_layout_config_id = (
            active_focus.layout_config_id
            if active_focus is not None and active_focus.layout_config_id is not None
            else window_layout.layout_config_id
        )
        self.bundle_layout_key = (
            active_focus.layout_key
            if active_focus is not None
            else window_layout.layout_key
        )
        section_representations = host_layout_mod.derive_runtime_section_representations(
            interface_config_bundle=self.interface_config_bundle,
            window_layout=window_layout,
            active_focus=active_focus,
            navigation_context_layout_target=self._runtime_navigation_context_layout_target(),
        )
        active_window, windows = await self._resolve_runtime_window_states(
            window_layout=window_layout,
        )
        self._runtime_state = replace(
            self._runtime_state,
            window_layout=window_layout,
            active_window=active_window,
            windows=windows,
            active_layout_config_id=(
                active_focus.layout_config_id
                if active_focus is not None
                else window_layout.layout_config_id
            ),
            layout_states=host_layout_mod.derive_runtime_layout_states(
                interface_config_bundle=self.interface_config_bundle,
                window_layout=window_layout,
                active_focus=active_focus,
            ),
            active_focus=active_focus,
            available_focus_targets=host_layout_mod.derive_runtime_focus_targets(
                interface_config_bundle=self.interface_config_bundle,
                window_key=window_layout.window_key,
            ),
            section_representations=section_representations,
            resolved_panes=host_layout_mod.derive_resolved_pane_descriptors(
                inputs=layout_inputs,
                window_layout=window_layout,
                active_focus=active_focus,
                section_state_addresses=section_state_addresses,
            ),
        )
        await self._ensure_experience_session_handoff_for_runtime_focus(
            window_layout=window_layout,
            active_focus=active_focus,
            section_representations=section_representations,
        )
        self._sync_pane_api_allowed_actions()
        self._notify_state_changed()
        return True

    async def _finalize_host_surface(self) -> None:
        self._control_plane_profiles = _derive_host_control_plane_profiles_state(
            active_profile_id=self._active_profile_id,
            current_screen=self._current_screen,
        )
        await self._refresh_runtime_window_layout()
        self._notify_state_changed()

    def _notify_state_changed(self) -> None:
        event = self._state_change_event
        self._state_revision += 1
        event.set()
        self._state_change_event = asyncio.Event()

    async def _refresh_workspace_entry_state(self) -> None:
        self._workspace_registry = None
        self._workspace_discovery = None
        self._selected_workspace = None
        self._selected_workspace_semantic_source_root = None
        self._selected_workspace_semantic_source = None
        self._selected_workspace_semantic_source_invocation_id = None
        self._selected_semantic_package = None

    def _ensure_bootstrap_runtime_state(self) -> None:
        if self._runtime_state is not None or not self._pane_contributions:
            return
        self._runtime_state = InterfaceRuntimeState(
            backend=InterfaceBackendState(
                available=False,
                manifest_path=None,
                registry_path=None,
                database_path=None,
                database_exists=False,
                environment_id=self.environment_id,
                opg_count=0,
                projection_bundle_available=False,
                projection_plan_count=0,
                table_count=0,
                reason="interface_host_bootstrap_panes",
            ),
            resolved_view=InterfaceResolvedView(
                experience_key="aware.interface.bootstrap",
                projection_view_id="entry.control-plane",
                host_payload={
                    "source_kind": "interface_host_bootstrap_panes",
                    "pane_count": len(self._pane_contributions),
                },
            ),
            warnings=("interface_host_bootstrap_panes",),
        )

    def _interface_admission_gate_active(self) -> bool:
        return (
            self._current_screen is not None
            and self._current_screen.screen_key == _INTERFACE_ADMISSION_SCREEN_KEY
            and bool(self._pane_contributions)
        )

    def _control_entry_session_contract_required(self) -> bool:
        return (
            self._interface_admitted
            and not self._authenticated
            and self._current_screen is not None
            and self._current_screen.screen_key == "control_identity_admission"
        )

    def _runtime_interface_id(self) -> UUID | None:
        if self._committed_interface_id is not None:
            return self._committed_interface_id
        binding = self.transport_session.binding if self.transport_session else None
        if binding is not None:
            return binding.interface_id
        profile = self.transport_session.profile if self.transport_session else None
        return profile.interface_id if profile is not None else None

    async def _resolve_projection_hash(self, *, opg_name: str) -> str | None:
        if self.coordinator is None:
            return None
        try:
            return await self.coordinator.resolve_projection_hash(opg_name=opg_name)
        except Exception:
            return None

    async def _sync_committed_lane_head(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
    ) -> tuple[str | None, dict[str, object]]:
        coordinator = self.coordinator
        host_runtime = self.host_runtime
        if coordinator is None or host_runtime is None:
            return None, {"synced": False, "reason": "coordinator_or_runtime_missing"}
        try:
            sync_service = coordinator.build_lane_sync_service(
                include_commit_payload=True,
            )
            assets = host_runtime.load_sync_assets(projection_hash=projection_hash)
            result = await sync_service.sync_lane_head(
                branch_id=str(branch_id),
                projection_hash=projection_hash,
                lane_id=str(branch_id),
                ocg=assets.ocg,
                opg=assets.opg,
            )
        except Exception as exc:
            return None, {"synced": False, "error": str(exc)}
        return result.head_commit_id, {
            "synced": True,
            "advanced": result.advanced,
            "projected": result.projected,
            "previous_head_commit_id": result.previous_head_commit_id,
            "fetched_commit_ids": list(result.fetched_commit_ids),
        }

    async def _projected_row(
        self,
        *,
        table_name: str,
        branch_id: UUID,
        projection_hash: str,
        object_id: UUID,
    ) -> dict[str, object] | None:
        db = getattr(self.host_runtime, "db", None)
        execute_query = getattr(db, "execute_query", None)
        if not callable(execute_query):
            return None
        query = cast(Callable[..., Awaitable[list[dict[str, object]]]], execute_query)
        rows = await query(
            f"""
            SELECT *
            FROM {table_name}
            WHERE branch_id = $1
              AND projection_hash = $2
              AND id = $3
            LIMIT 1
            """,
            str(branch_id),
            projection_hash,
            str(object_id),
        )
        return rows[0] if rows else None

    async def _resolve_runtime_window_states(
        self,
        *,
        window_layout: InterfaceWindowLayoutState | None,
    ) -> tuple[
        InterfaceRuntimeWindowState | None, tuple[InterfaceRuntimeWindowState, ...]
    ]:
        if window_layout is None:
            return None, ()
        interface_id = self._runtime_interface_id()
        navigation_context_target = self._runtime_navigation_context_layout_target()
        active_navigation_context = InterfaceRuntimeWindowNavigationContextState(
            source_kind="runtime_target",
            environment_navigation_context_id=(
                navigation_context_target.environment_navigation_context_id
                if navigation_context_target is not None
                else None
            ),
            thread_id=(
                navigation_context_target.thread_id
                if navigation_context_target is not None
                else None
            ),
            interface_window_navigation_context_id=(
                navigation_context_target.interface_window_navigation_context_id
                if navigation_context_target is not None
                else None
            ),
            interface_environment_id=(
                navigation_context_target.interface_environment_id
                if navigation_context_target is not None
                else None
            ),
            environment_id=(
                navigation_context_target.environment_id
                if navigation_context_target is not None
                else None
            ),
            process_id=(
                navigation_context_target.process_id
                if navigation_context_target is not None
                else None
            ),
        )
        if interface_id is None:
            fallback = InterfaceRuntimeWindowState(
                source_kind="runtime_synthesized",
                window_key=window_layout.window_key,
                active=True,
                title=window_layout.title,
                active_navigation_context=active_navigation_context,
                active_layout_config_id=window_layout.layout_config_id,
                active_layout_key=window_layout.layout_key,
                active_layout_source_kind=window_layout.source_kind,
                evidence={"reason": "interface_id_unavailable"},
            )
            return fallback, (fallback,)

        window_id = stable_window_id(
            interface_id=interface_id,
            window_key=window_layout.window_key,
        )
        interface_window_id = stable_interface_window_id(
            interface_id=interface_id,
            window_id=window_id,
        )
        interface_projection_hash = await self._resolve_projection_hash(
            opg_name="interface",
        )
        window_projection_hash = await self._resolve_projection_hash(
            opg_name="window",
        )
        interface_head_commit_id: str | None = None
        window_head_commit_id: str | None = None
        interface_sync_evidence: dict[str, object] = {}
        window_sync_evidence: dict[str, object] = {}
        interface_window_row: dict[str, object] | None = None
        window_row: dict[str, object] | None = None
        interface_window_navigation_context_row: dict[str, object] | None = None
        interface_environment_row: dict[str, object] | None = None

        if interface_projection_hash:
            interface_head_commit_id, interface_sync_evidence = (
                await self._sync_committed_lane_head(
                    branch_id=interface_id,
                    projection_hash=interface_projection_hash,
                )
            )
            with suppress(Exception):
                interface_window_row = await self._projected_row(
                    table_name="interface_window",
                    branch_id=interface_id,
                    projection_hash=interface_projection_hash,
                    object_id=interface_window_id,
                )
                active_navigation_context_id = _optional_uuid(
                    interface_window_row.get("active_navigation_context_id")
                    if interface_window_row is not None
                    else None
                )
                if active_navigation_context_id is not None:
                    interface_window_navigation_context_row = await self._projected_row(
                        table_name="interface_window_navigation_context",
                        branch_id=interface_id,
                        projection_hash=interface_projection_hash,
                        object_id=active_navigation_context_id,
                    )
                    interface_environment_id = _optional_uuid(
                        interface_window_navigation_context_row.get(
                            "interface_environment_id"
                        )
                        if interface_window_navigation_context_row is not None
                        else None
                    )
                    if interface_environment_id is not None:
                        interface_environment_row = await self._projected_row(
                            table_name="interface_environment",
                            branch_id=interface_id,
                            projection_hash=interface_projection_hash,
                            object_id=interface_environment_id,
                        )

        if window_projection_hash:
            window_head_commit_id, window_sync_evidence = (
                await self._sync_committed_lane_head(
                    branch_id=window_id,
                    projection_hash=window_projection_hash,
                )
            )
            with suppress(Exception):
                window_row = await self._projected_row(
                    table_name="window_",
                    branch_id=window_id,
                    projection_hash=window_projection_hash,
                    object_id=window_id,
                )

        projected_interface_window_navigation_context_id = _optional_uuid(
            interface_window_row.get("active_navigation_context_id")
            if interface_window_row is not None
            else None
        )
        projected_environment_navigation_context_id = _optional_uuid(
            interface_window_navigation_context_row.get(
                "environment_navigation_context_id"
            )
            if interface_window_navigation_context_row is not None
            else None
        )
        projected_interface_environment_id = _optional_uuid(
            interface_window_navigation_context_row.get("interface_environment_id")
            if interface_window_navigation_context_row is not None
            else None
        )
        projected_environment_id = _optional_uuid(
            interface_environment_row.get("environment_id")
            if interface_environment_row is not None
            else None
        )

        interface_environment_id = (
            projected_interface_environment_id
            or active_navigation_context.interface_environment_id
            or (
                stable_interface_environment_id(
                    interface_id=interface_id,
                    environment_id=active_navigation_context.environment_id,
                )
                if active_navigation_context.environment_id is not None
                else None
            )
        )
        environment_navigation_context_id = (
            projected_environment_navigation_context_id
            or active_navigation_context.environment_navigation_context_id
        )
        thread_id = active_navigation_context.thread_id
        interface_window_navigation_context_id = (
            projected_interface_window_navigation_context_id
            or active_navigation_context.interface_window_navigation_context_id
            or (
                stable_interface_window_navigation_context_id(
                    interface_window_id=interface_window_id,
                    interface_environment_id=interface_environment_id,
                    environment_navigation_context_id=environment_navigation_context_id,
                )
                if interface_environment_id is not None
                and environment_navigation_context_id is not None
                else None
            )
        )
        active_navigation_context = InterfaceRuntimeWindowNavigationContextState(
            source_kind=(
                "committed_oig"
                if interface_window_navigation_context_row is not None
                else active_navigation_context.source_kind
            ),
            environment_navigation_context_id=environment_navigation_context_id,
            thread_id=thread_id,
            interface_window_navigation_context_id=interface_window_navigation_context_id,
            interface_environment_id=interface_environment_id,
            environment_id=projected_environment_id
            or active_navigation_context.environment_id,
            process_id=active_navigation_context.process_id,
            evidence={
                "interface_window_navigation_context_projected": interface_window_navigation_context_row
                is not None,
                "interface_environment_projected": interface_environment_row
                is not None,
            },
        )
        active_layout_id = _optional_uuid(
            window_row.get("active_layout_id") if window_row is not None else None
        )
        committed = interface_window_row is not None and window_row is not None
        partial_commit = bool(
            interface_head_commit_id
            or window_head_commit_id
            or interface_window_row is not None
            or window_row is not None
        )
        source_kind = (
            "committed_oig"
            if committed
            else "committed_oig_incomplete" if partial_commit else "runtime_synthesized"
        )
        window_state = InterfaceRuntimeWindowState(
            source_kind=source_kind,
            window_key=window_layout.window_key,
            active=True,
            interface_id=interface_id,
            interface_window_id=interface_window_id,
            window_id=window_id,
            title=window_layout.title,
            active_navigation_context=active_navigation_context,
            active_layout_id=active_layout_id,
            active_layout_config_id=window_layout.layout_config_id,
            active_layout_key=window_layout.layout_key,
            active_layout_source_kind=(
                "window_oig"
                if active_layout_id is not None
                else window_layout.source_kind
            ),
            interface_projection_hash=interface_projection_hash,
            window_projection_hash=window_projection_hash,
            interface_head_commit_id=interface_head_commit_id,
            window_head_commit_id=window_head_commit_id,
            evidence={
                "interface_lane": interface_sync_evidence,
                "window_lane": window_sync_evidence,
                "interface_window_projected": interface_window_row is not None,
                "window_projected": window_row is not None,
            },
        )
        return window_state, (window_state,)

    async def _refresh_runtime_window_layout(self) -> None:
        self._ensure_bootstrap_runtime_state()
        if self._runtime_state is None:
            return
        interface_admission_gate_active = self._interface_admission_gate_active()
        resolved_view = self._runtime_state.resolved_view
        interface_config_bundle = self.interface_config_bundle
        if interface_config_bundle is not None:
            resolved_view = InterfaceResolvedView(
                experience_key=(
                    resolved_view.experience_key
                    if resolved_view is not None
                    else interface_config_bundle.name
                ),
                interface_package_id=interface_config_bundle.interface_package_id,
                interface_package_name=interface_config_bundle.interface_package_name,
                projection_view_id=(
                    resolved_view.projection_view_id
                    if resolved_view is not None
                    else None
                ),
                host_payload=(
                    dict(resolved_view.host_payload)
                    if resolved_view is not None
                    else {}
                ),
            )
        layout_inputs = self._layout_inputs()
        resolved_at = _utc_now_iso()
        bundle_layout_preview = (
            host_layout_mod.build_runtime_window_layout(
                inputs=layout_inputs,
                resolved_at=resolved_at,
            )
            if not interface_admission_gate_active
            and layout_inputs.bundle_window_layout_enabled
            and interface_config_bundle is not None
            else None
        )
        available_focus_targets = host_layout_mod.derive_runtime_focus_targets(
            interface_config_bundle=interface_config_bundle,
            window_key=(
                self._preferred_runtime_mount_window_key()
                or (
                    bundle_layout_preview.window_key
                    if bundle_layout_preview is not None
                    else None
                )
            ),
        )
        bundle_preferred_section_key = (
            self.bundle_focus_section_key
            or host_layout_mod.preferred_runtime_focus_section(
                window_layout=bundle_layout_preview,
                focus_targets=available_focus_targets,
            )
        )
        bundle_backed_window_layout = bool(
            not interface_admission_gate_active
            and layout_inputs.bundle_window_layout_enabled
            and interface_config_bundle is not None
        )
        section_state_addresses: dict[str, InterfaceResolvedSectionStateAddress] = {}
        attention_runtime_mount = None
        if bundle_backed_window_layout:
            section_state_addresses = await self._resolve_host_section_state_addresses(
                window_layout=bundle_layout_preview,
                allow_section_lane_resolver=False,
            )
            environment_target = self._attention_environment_runtime_target()
            attention_session_id = self._active_attention_session_id()
            runtime_mount_request = (
                attention_capability_mod.build_watch_runtime_mount_request(
                    interface_config_bundle=interface_config_bundle,
                    bundle_window_key=self._preferred_runtime_mount_window_key(),
                    environment_target=environment_target,
                    attention_session_id=attention_session_id,
                    preferred_layout_config_id=(
                        self._preferred_runtime_mount_layout_config_id()
                    ),
                    preferred_layout_key=self._preferred_runtime_mount_layout_key(),
                    preferred_section_key=(
                        bundle_preferred_section_key
                        if bundle_backed_window_layout
                        else None
                    ),
                    preferred_observable_id=(
                        self.bundle_focus_observable_id
                        if bundle_backed_window_layout
                        else None
                    ),
                )
            )
            runtime_mount_request_signature = (
                attention_capability_mod.runtime_mount_watch_request_signature(
                    runtime_mount_request
                )
            )
            attention_runtime_mount = (
                self._attention_runtime_mount_cache
                if (
                    runtime_mount_request_signature is not None
                    and runtime_mount_request_signature
                    == self._attention_runtime_mount_cache_signature
                    and self._attention_runtime_mount_cache is not None
                )
                else await attention_capability_mod.resolve_runtime_mount_from_attention(
                    transport_session=self.transport_session,
                    interface_config_bundle=interface_config_bundle,
                    bundle_window_key=self._preferred_runtime_mount_window_key(),
                    section_state_addresses=section_state_addresses,
                    environment_target=environment_target,
                    attention_session_id=attention_session_id,
                    preferred_layout_config_id=(
                        self._preferred_runtime_mount_layout_config_id()
                    ),
                    preferred_section_key=(
                        bundle_preferred_section_key
                        if bundle_backed_window_layout
                        else None
                    ),
                    preferred_observable_id=(
                        self.bundle_focus_observable_id
                        if bundle_backed_window_layout
                        else None
                    ),
                )
            )
            if runtime_mount_request_signature is not None:
                self._attention_runtime_mount_cache_signature = (
                    runtime_mount_request_signature
                )
                self._attention_runtime_mount_cache = attention_runtime_mount
            section_state_addresses = attention_runtime_mount.section_state_addresses
            window_layout = host_layout_mod.build_runtime_window_layout(
                inputs=replace(
                    layout_inputs,
                    bundle_layout_config_id=attention_runtime_mount.active_layout_config_id,
                    bundle_layout_key=attention_runtime_mount.active_layout_key,
                ),
                resolved_at=resolved_at,
            )
            if window_layout is not None:
                window_layout = host_layout_mod.apply_runtime_layout_sections(
                    window_layout=window_layout,
                    runtime_sections=attention_runtime_mount.window_layout_sections,
                )
                window_layout = (
                    attention_capability_mod.pin_window_layout_to_runtime_mount(
                        window_layout=window_layout,
                        resolution=attention_runtime_mount,
                    )
                )
            section_state_addresses = host_layout_mod.merge_section_state_addresses(
                base=await self._resolve_host_section_state_addresses(
                    window_layout=window_layout,
                    allow_section_lane_resolver=False,
                ),
                overlay=section_state_addresses,
            )
        else:
            window_layout = host_layout_mod.build_runtime_window_layout(
                inputs=layout_inputs,
                resolved_at=resolved_at,
            )
            section_state_addresses = (
                await self._resolve_host_section_state_addresses(
                    window_layout=window_layout,
                )
                if window_layout is not None
                else {}
            )
            if window_layout is not None:
                section_state_addresses = await attention_capability_mod.enrich_section_state_addresses_from_attention(
                    transport_session=self.transport_session,
                    interface_config_bundle=interface_config_bundle,
                    bundle_window_key=window_layout.window_key,
                    window_layout=window_layout,
                    section_state_addresses=section_state_addresses,
                )
        if bundle_backed_window_layout:
            active_focus = host_layout_mod.attention_owned_runtime_focus(
                window_layout=window_layout,
                section_state_addresses=section_state_addresses,
                active_section_key=(
                    attention_runtime_mount.active_section_key
                    if attention_runtime_mount is not None
                    else None
                ),
                active_observable_id=(
                    attention_runtime_mount.active_observable_id
                    if attention_runtime_mount is not None
                    else None
                ),
            )
            section_representations = (
                host_layout_mod.derive_runtime_section_representations(
                    interface_config_bundle=interface_config_bundle,
                    window_layout=window_layout,
                    active_focus=active_focus,
                    navigation_context_layout_target=self._runtime_navigation_context_layout_target(),
                )
                if window_layout is not None
                else ()
            )
            active_focus = _runtime_focus_with_resolved_representation(
                active_focus=active_focus,
                representation=_resolved_section_representation_for_runtime_focus(
                    active_focus=active_focus,
                    section_representations=section_representations,
                ),
                section_state_addresses=section_state_addresses,
            )
            if active_focus is not None:
                activated = (
                    await self._activate_experience_focus_target_for_active_focus(
                        window_layout=window_layout,
                        active_focus=active_focus,
                        section_state_addresses=section_state_addresses,
                    )
                )
                if activated:
                    attention_runtime_mount = await attention_capability_mod.resolve_runtime_mount_from_attention(
                        transport_session=self.transport_session,
                        interface_config_bundle=interface_config_bundle,
                        bundle_window_key=self._preferred_runtime_mount_window_key(),
                        section_state_addresses={},
                        environment_target=self._attention_environment_runtime_target(),
                        attention_session_id=self._active_attention_session_id(),
                        preferred_layout_config_id=(
                            self._preferred_runtime_mount_layout_config_id()
                        ),
                        preferred_section_key=active_focus.section_key,
                        preferred_observable_id=active_focus.observable_id,
                    )
                    section_state_addresses = (
                        attention_runtime_mount.section_state_addresses
                    )
                    window_layout = host_layout_mod.apply_runtime_layout_sections(
                        window_layout=window_layout,
                        runtime_sections=attention_runtime_mount.window_layout_sections,
                    )
                    window_layout = (
                        attention_capability_mod.pin_window_layout_to_runtime_mount(
                            window_layout=window_layout,
                            resolution=attention_runtime_mount,
                        )
                    )
                    active_focus = host_layout_mod.attention_owned_runtime_focus(
                        window_layout=window_layout,
                        section_state_addresses=section_state_addresses,
                        active_section_key=attention_runtime_mount.active_section_key,
                        active_observable_id=(
                            attention_runtime_mount.active_observable_id
                        ),
                    )
                    section_representations = (
                        host_layout_mod.derive_runtime_section_representations(
                            interface_config_bundle=interface_config_bundle,
                            window_layout=window_layout,
                            active_focus=active_focus,
                            navigation_context_layout_target=self._runtime_navigation_context_layout_target(),
                        )
                        if window_layout is not None
                        else ()
                    )
                    active_focus = _runtime_focus_with_resolved_representation(
                        active_focus=active_focus,
                        representation=_resolved_section_representation_for_runtime_focus(
                            active_focus=active_focus,
                            section_representations=section_representations,
                        ),
                        section_state_addresses=section_state_addresses,
                    )
        else:
            active_focus = host_layout_mod.resolve_active_runtime_focus(
                window_layout=window_layout,
                focus_targets=available_focus_targets,
                section_state_addresses=section_state_addresses,
                preferred_section_key=self.bundle_focus_section_key,
                preferred_observable_id=self.bundle_focus_observable_id,
            )
        self.bundle_focus_section_key = (
            active_focus.section_key if active_focus is not None else None
        )
        self.bundle_focus_observable_id = (
            active_focus.observable_id if active_focus is not None else None
        )
        self.bundle_layout_config_id = (
            active_focus.layout_config_id
            if active_focus is not None and active_focus.layout_config_id is not None
            else (window_layout.layout_config_id if window_layout is not None else None)
        )
        self.bundle_layout_key = (
            active_focus.layout_key
            if active_focus is not None
            else (window_layout.layout_key if window_layout is not None else None)
        )
        resolved_panes = (
            host_layout_mod.derive_resolved_pane_descriptors(
                inputs=layout_inputs,
                window_layout=window_layout,
                active_focus=active_focus,
                section_state_addresses=section_state_addresses,
            )
            if window_layout is not None
            else ()
        )
        resolved_panes = self._merge_experience_section_view_action_bindings(
            resolved_panes
        )
        resolved_panes = _merge_resolved_pane_descriptors(
            existing=self._runtime_state.resolved_panes,
            derived=resolved_panes,
            materialized_pane_states=self._runtime_state.materialized_pane_states,
        )
        dynamic_render_specs, dynamic_render_spec_warnings = (
            await self._load_dynamic_pane_render_specs()
        )
        active_window, windows = await self._resolve_runtime_window_states(
            window_layout=window_layout,
        )
        section_representations = (
            host_layout_mod.derive_runtime_section_representations(
                interface_config_bundle=interface_config_bundle,
                window_layout=window_layout,
                active_focus=active_focus,
                navigation_context_layout_target=self._runtime_navigation_context_layout_target(),
            )
            if window_layout is not None
            else ()
        )
        section_representations = self._merge_experience_section_view_representations(
            section_representations
        )
        self._runtime_state = replace(
            self._runtime_state,
            resolved_view=resolved_view,
            window_layout=window_layout,
            active_window=active_window,
            windows=windows,
            active_layout_config_id=(
                active_focus.layout_config_id
                if active_focus is not None
                else (
                    window_layout.layout_config_id
                    if window_layout is not None
                    else None
                )
            ),
            layout_states=(
                host_layout_mod.derive_runtime_layout_states(
                    interface_config_bundle=interface_config_bundle,
                    window_layout=window_layout,
                    active_focus=active_focus,
                )
                if window_layout is not None
                else ()
            ),
            active_focus=active_focus,
            available_focus_targets=available_focus_targets,
            section_representations=section_representations,
            resolved_panes=resolved_panes,
            dynamic_pane_render_specs=dynamic_render_specs,
            warnings=_merge_dynamic_render_spec_warnings(
                existing=self._runtime_state.warnings,
                dynamic_warnings=dynamic_render_spec_warnings,
            ),
        )
        await self._ensure_experience_session_handoff_for_runtime_focus(
            window_layout=window_layout,
            active_focus=active_focus,
            section_representations=section_representations,
            require_explicit_contract=(self._control_entry_session_contract_required()),
        )
        self._sync_pane_api_allowed_actions()

    async def _activate_experience_focus_target_for_active_focus(
        self,
        *,
        window_layout: InterfaceWindowLayoutState | None,
        active_focus: object,
        section_state_addresses: dict[str, InterfaceResolvedSectionStateAddress],
    ) -> bool:
        if window_layout is None or self.interface_config_bundle is None:
            return False
        section_key = getattr(active_focus, "section_key", None)
        observable_id = getattr(active_focus, "observable_id", None)
        if section_key is None or observable_id is None:
            return False
        representations = host_layout_mod.derive_runtime_section_representations(
            interface_config_bundle=self.interface_config_bundle,
            window_layout=window_layout,
            active_focus=cast(Any, active_focus),
            navigation_context_layout_target=self._runtime_navigation_context_layout_target(),
        )
        representation = _active_runtime_section_representation(
            active_focus=active_focus,
            section_representations=representations,
        )
        try:
            activation = await experience_capability_mod.activate_experience_section_graph_binding_for_runtime_focus(
                transport_session=self.transport_session,
                interface_config_bundle=self.interface_config_bundle,
                navigation_context_layout_target=self._runtime_navigation_context_layout_target(),
                section_state_addresses=section_state_addresses,
                window_key=window_layout.window_key,
                layout_key=window_layout.layout_key,
                section_key=str(section_key),
                observable_id=observable_id,
                representation=representation,
            )
        except Exception:
            return False
        if activation is not None:
            for cache_observable_id in dict.fromkeys(
                (activation.projection_observable_id, _optional_uuid(observable_id))
            ):
                if cache_observable_id is None:
                    continue
                self._experience_section_view_activations[
                    _experience_section_view_cache_key(
                        section_key=activation.section_key,
                        observable_id=cache_observable_id,
                    )
                ] = activation
        return activation is not None

    def _merge_experience_section_view_action_bindings(
        self,
        panes: tuple[InterfaceResolvedPaneDescriptor, ...],
    ) -> tuple[InterfaceResolvedPaneDescriptor, ...]:
        if not panes or not self._experience_section_view_activations:
            return panes
        merged: list[InterfaceResolvedPaneDescriptor] = []
        for pane in panes:
            observable_id = pane.object_projection_graph_observable_id
            activation = (
                self._experience_section_view_activations.get(
                    _experience_section_view_cache_key(
                        section_key=pane.section_key,
                        observable_id=observable_id,
                    )
                )
                if observable_id is not None
                else None
            )
            if activation is None:
                merged.append(pane)
                continue
            action_config_ids = {
                action.action_key.strip().casefold(): (
                    action.view_invocation_action_config_id
                )
                for action in activation.view_actions
            }
            action_targets = tuple(
                replace(
                    target,
                    view_invocation_action_config_id=(
                        action_config_ids.get(target.action_key.strip().casefold())
                        or target.view_invocation_action_config_id
                    ),
                )
                for target in pane.action_targets
            )
            merged.append(
                replace(
                    pane,
                    section_graph_binding_key=(
                        pane.section_graph_binding_key or activation.binding_key
                    ),
                    projection_experience_view_instance_id=(
                        activation.projection_experience_view_instance_id
                        or pane.projection_experience_view_instance_id
                    ),
                    action_targets=action_targets,
                )
            )
        return tuple(merged)

    def _merge_experience_section_view_representations(
        self,
        representations: tuple[InterfaceRuntimeSectionRepresentationState, ...],
    ) -> tuple[InterfaceRuntimeSectionRepresentationState, ...]:
        if not representations or not self._experience_section_view_activations:
            return representations
        merged: list[InterfaceRuntimeSectionRepresentationState] = []
        changed = False
        for representation in representations:
            activation = self._experience_section_view_activations.get(
                _experience_section_view_cache_key(
                    section_key=representation.section_key,
                    observable_id=representation.observable_id,
                )
            )
            if activation is None:
                merged.append(representation)
                continue
            updated = replace(
                representation,
                section_graph_binding_key=(
                    representation.section_graph_binding_key or activation.binding_key
                ),
                projection_experience_graph_identity_id=(
                    representation.projection_experience_graph_identity_id
                    or activation.projection_experience_graph_identity_id
                ),
                object_projection_graph_identity_id=(
                    representation.object_projection_graph_identity_id
                    or activation.object_projection_graph_identity_id
                ),
            )
            changed = changed or updated != representation
            merged.append(updated)
        return tuple(merged) if changed else representations

    async def _load_dynamic_pane_render_specs(
        self,
    ) -> tuple[tuple[InterfaceRuntimePaneRenderSpecState, ...], tuple[str, ...]]:
        if (
            self._current_screen is not None
            and self._current_screen.screen_key == _INTERFACE_ADMISSION_SCREEN_KEY
        ):
            return (), ()
        loader = next(
            (
                getattr(source, "load_pane_render_spec_runtime_states", None)
                for source in (self.host_runtime, self.mock_service_adapter)
                if source is not None
                and callable(
                    getattr(source, "load_pane_render_spec_runtime_states", None)
                )
            ),
            None,
        )
        if not callable(loader):
            return (), ()
        load_render_specs = cast(
            Callable[
                ...,
                Awaitable[tuple[InterfaceRuntimePaneRenderSpecState, ...]],
            ],
            loader,
        )
        try:
            return (
                await load_render_specs(
                    interface_config_bundle=self.interface_config_bundle,
                ),
                (),
            )
        except Exception as exc:
            return (), (f"{_DYNAMIC_RENDER_SPEC_WARNING_PREFIX}{exc}",)

    async def _refresh_local_runtime_state(self) -> None:
        if self.local_runtime is None:
            self._local_service_host = None
            self._local_node_runtime = None
            self._local_node_log_tail = ()
            return
        snapshot = await self.local_runtime.snapshot()
        self._apply_local_runtime_snapshot(
            service_host=snapshot.service_host,
            node_runtime=snapshot.node_runtime,
        )

    def _should_query_hosted_service_status(self) -> bool:
        return hosted_services_capability_mod.should_query_hosted_service_status(
            transport_bound=self.transport_session is not None,
            consumer_profile_active=_consumer_profile_active_value(
                self._active_profile_id
            ),
            local_service_host=self._local_service_host,
            local_node_runtime=self._local_node_runtime,
        )

    async def _refresh_hosted_service_status(self) -> None:
        self._recovery_capabilities = (
            await hosted_services_capability_mod.refresh_host_recovery_capabilities(
                transport_session=self.transport_session,
                endpoint=self.endpoint,
            )
        )
        if (
            _consumer_profile_active_value(self._active_profile_id)
            and not self._interface_admitted
        ):
            self._hosted_services = None
            return
        self._hosted_services = (
            await hosted_services_capability_mod.refresh_hosted_service_status(
                transport_session=self.transport_session,
                consumer_profile_active=_consumer_profile_active_value(
                    self._active_profile_id
                ),
                local_service_host=self._local_service_host,
                local_node_runtime=self._local_node_runtime,
            )
        )
        if self._hosted_services is None:
            self._hosted_services = (
                await hosted_services_capability_mod.refresh_local_service_host_status(
                    local_runtime=self.local_runtime,
                    local_service_host=self._local_service_host,
                )
                if self._active_profile_id == _OPERATOR_LOCAL_BOOTSTRAP_PROFILE_ID
                else None
            )

    def _apply_local_runtime_snapshot(
        self,
        *,
        service_host: InterfaceHostServiceLocalServiceHostState,
        node_runtime: InterfaceHostServiceLocalNodeRuntimeState,
    ) -> None:
        (
            self._local_service_host,
            self._local_node_runtime,
            self._local_node_log_tail,
        ) = local_runtime_capability_mod.apply_local_runtime_snapshot(
            service_host=service_host,
            node_runtime=node_runtime,
            local_node_log_tail=self._local_node_log_tail,
        )


def _thread_target_uuid_evidence(
    thread_target: InterfaceNavigationContextLayoutTargetState | None,
    key: str,
) -> UUID | None:
    value = _thread_target_text_evidence(thread_target, key)
    if value is None:
        return None
    try:
        return UUID(value)
    except ValueError:
        return None


def _thread_target_text_evidence(
    thread_target: InterfaceNavigationContextLayoutTargetState | None,
    key: str,
) -> str | None:
    evidence = thread_target.evidence if thread_target is not None else None
    if not isinstance(evidence, Mapping):
        return None
    value = evidence.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "InterfaceHostServiceRuntime",
]
