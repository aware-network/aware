from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol
from uuid import UUID

from aware_interface import (
    InterfaceResolvedSectionStateAddress,
    InterfaceRuntimeSectionRepresentationState,
    InterfaceRuntimeState,
)
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
    InterfaceWindowConfigLayoutBundle,
)

import aware_interface_service.host.layout as host_layout_mod
from aware_interface_service.host.state import (
    CONTROL_PLANE_PROFILE_IDS,
    normalize_control_plane_profile_id,
    normalize_selected_step_id,
)
from aware_interface_service.models import (
    InterfaceHostServiceControlPlaneWorkspaceState,
    InterfaceHostServiceSelectedSemanticPackageState,
    InterfaceHostServiceState,
    InterfaceHostServiceWorkspaceDiscoveryState,
    InterfaceHostServiceWorkspaceSemanticSourceState,
)

if TYPE_CHECKING:
    from aware_interface_sdk.transport import InterfaceTransportSession


@dataclass(frozen=True, slots=True)
class ResolvedRuntimeFocusSelection:
    layout_config_id: UUID | None
    layout_key: str | None
    section_key: str | None
    observable_id: UUID | None
    representation_id: UUID | None = None


def _normalize_optional_uuid(value: UUID | str | None) -> UUID | None:
    if value is None or isinstance(value, UUID):
        return value
    normalized = str(value).strip()
    if not normalized:
        return None
    return UUID(normalized)


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _layout_request_idempotency_fingerprint(
    *,
    interface_package_id: UUID | str | None,
    interface_package_name: str | None,
    window_key: str | None,
    layout_config_id: UUID | str | None,
    layout_key: str | None,
    section_key: str | None,
    observable_id: UUID | str | None,
    representation_id: UUID | str | None,
) -> str:
    payload = {
        "interface_package_id": (
            str(interface_package_id) if interface_package_id is not None else None
        ),
        "interface_package_name": _normalize_optional_text(interface_package_name),
        "window_key": _normalize_optional_text(window_key),
        "layout_config_id": (
            str(layout_config_id) if layout_config_id is not None else None
        ),
        "layout_key": _normalize_optional_text(layout_key),
        "section_key": _normalize_optional_text(section_key),
        "observable_id": str(observable_id) if observable_id is not None else None,
        "representation_id": (
            str(representation_id) if representation_id is not None else None
        ),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _available_bundle_layouts(
    *,
    interface_config_bundle: InterfaceConfigBundle | None,
    bundle_window_key: str | None,
) -> tuple[InterfaceWindowConfigLayoutBundle, ...]:
    if interface_config_bundle is None:
        return ()
    window_key = bundle_window_key or "main"
    for window in interface_config_bundle.window_configs:
        if window.key != window_key:
            continue
        layouts = tuple(
            layout
            for layout in window.layout_configs
            if layout.key.strip()
        )
        if layouts:
            return layouts
    return ()


def _validate_request_interface_package(
    *,
    interface_config_bundle: InterfaceConfigBundle,
    interface_package_id: UUID | str | None,
    interface_package_name: str | None,
) -> None:
    normalized_package_id = _normalize_optional_uuid(interface_package_id)
    if (
        normalized_package_id is not None
        and normalized_package_id != interface_config_bundle.interface_package_id
    ):
        raise RuntimeError(
            "Interface window-layout request targeted interface package id "
            f"{normalized_package_id}, but the host is running "
            f"{interface_config_bundle.interface_package_id}."
        )
    normalized_package_name = _normalize_optional_text(interface_package_name)
    if (
        normalized_package_name is not None
        and normalized_package_name.casefold()
        != interface_config_bundle.interface_package_name.casefold()
    ):
        raise RuntimeError(
            "Interface window-layout request targeted interface package "
            f"{normalized_package_name!r}, but the host is running "
            f"{interface_config_bundle.interface_package_name!r}."
        )


def _resolve_request_window_key(
    *,
    interface_config_bundle: InterfaceConfigBundle,
    bundle_window_key: str | None,
    window_key: str | None,
) -> str:
    requested_window_key = (
        _normalize_optional_text(window_key)
        or _normalize_optional_text(bundle_window_key)
        or "main"
    )
    available_by_key = {
        window.key.strip().casefold(): window.key
        for window in interface_config_bundle.window_configs
        if window.key.strip()
    }
    resolved_window_key = available_by_key.get(requested_window_key.casefold())
    if resolved_window_key is None:
        available = ", ".join(sorted(available_by_key.values())) or "<none>"
        raise RuntimeError(
            f"Unknown interface window: {requested_window_key}. "
            f"Available windows: {available}"
        )
    return resolved_window_key


def _normalize_optional_section_key(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _resolve_runtime_focus_selection_from_representation_id(
    runtime: InterfaceHostControlPlaneRuntime,
    *,
    representation_id: UUID,
) -> ResolvedRuntimeFocusSelection | None:
    runtime_state = runtime.state().runtime
    if runtime_state is None:
        return None
    representation = next(
        (
            item
            for item in runtime_state.section_representations
            if item.representation_id == representation_id
        ),
        None,
    )
    if representation is None:
        return None
    return ResolvedRuntimeFocusSelection(
        layout_config_id=representation.layout_config_id,
        layout_key=representation.layout_key,
        section_key=representation.section_key,
        observable_id=representation.observable_id,
        representation_id=representation.representation_id,
    )


def normalize_runtime_focus_selection(
    *,
    layout_config_id: UUID | str | None,
    layout_key: str | None,
    section_key: str | None,
    observable_id: UUID | str | None,
    interface_config_bundle: InterfaceConfigBundle | None,
    bundle_window_key: str | None,
) -> ResolvedRuntimeFocusSelection:
    normalized_layout_config_id = _normalize_optional_uuid(layout_config_id)
    normalized = layout_key.strip() if isinstance(layout_key, str) else None
    normalized_layout_key = normalized or None
    normalized_section_key = _normalize_optional_section_key(section_key)
    normalized_observable_id = _normalize_optional_uuid(observable_id)
    if (
        normalized_layout_config_id is None
        and normalized_layout_key is None
        and normalized_section_key is None
        and normalized_observable_id is None
    ):
        return ResolvedRuntimeFocusSelection(
            layout_config_id=None,
            layout_key=None,
            section_key=None,
            observable_id=None,
        )
    available_layouts = _available_bundle_layouts(
        interface_config_bundle=interface_config_bundle,
        bundle_window_key=bundle_window_key,
    )
    available_focus_targets = host_layout_mod.derive_runtime_focus_targets(
        interface_config_bundle=interface_config_bundle,
        window_key=bundle_window_key,
    )
    if not available_layouts:
        return ResolvedRuntimeFocusSelection(
            layout_config_id=normalized_layout_config_id,
            layout_key=normalized_layout_key,
            section_key=normalized_section_key,
            observable_id=normalized_observable_id,
        )
    available_by_id = {
        layout.layout_config_id: layout for layout in available_layouts
    }
    available_by_key = {
        layout.key: layout for layout in available_layouts
    }
    selected_layout: InterfaceWindowConfigLayoutBundle | None = None
    if normalized_layout_config_id is not None:
        selected_layout = available_by_id.get(normalized_layout_config_id)
        if selected_layout is None:
            available = ", ".join(
                str(item.layout_config_id) for item in available_layouts
            ) or "<none>"
            raise RuntimeError(
                f"Unknown runtime layout config id: {normalized_layout_config_id}. "
                f"Available layout ids: {available}"
            )
    elif normalized_layout_key is not None:
        selected_layout = available_by_key.get(normalized_layout_key)
        if selected_layout is None:
            available = ", ".join(sorted(available_by_key)) or "<none>"
            raise RuntimeError(
                f"Unknown runtime layout: {layout_key}. "
                f"Available layouts: {available}"
            )
    elif normalized_section_key is not None:
        matching_layouts = tuple(
            layout
            for layout in available_layouts
            if any(
                section.key.strip().casefold()
                == normalized_section_key.casefold()
                for section in layout.sections
            )
        )
        if not matching_layouts:
            available_sections = ", ".join(
                sorted(
                    {
                        section.key
                        for layout in available_layouts
                        for section in layout.sections
                    }
                )
            ) or "<none>"
            raise RuntimeError(
                f"Unknown runtime focus section: {section_key}. "
                f"Available sections: {available_sections}"
            )
        if len(matching_layouts) > 1:
            available_layout_keys = ", ".join(item.key for item in matching_layouts)
            raise RuntimeError(
                f"Runtime focus section {section_key!r} is ambiguous across layouts: "
                f"{available_layout_keys}. Provide a layout identity."
            )
        selected_layout = matching_layouts[0] if matching_layouts else None
    else:
        selected_layout = None
    if selected_layout is None:
        return ResolvedRuntimeFocusSelection(
            layout_config_id=normalized_layout_config_id,
            layout_key=normalized_layout_key,
            section_key=normalized_section_key,
            observable_id=normalized_observable_id,
        )
    normalized_layout_config_id = selected_layout.layout_config_id
    normalized_layout_key = selected_layout.key
    layout_focus_targets = tuple(
        item
        for item in available_focus_targets
        if item.layout_config_id == selected_layout.layout_config_id
        or item.layout_key.strip().casefold() == selected_layout.key.strip().casefold()
    )
    if normalized_observable_id is not None:
        focus_target = next(
            (
                item
                for item in layout_focus_targets
                if item.observable_id == normalized_observable_id
                and (
                    normalized_section_key is None
                    or (
                        item.section_key is not None
                        and item.section_key.strip().casefold()
                        == normalized_section_key.casefold()
                    )
                )
            ),
            None,
        )
        if focus_target is None:
            available = ", ".join(
                sorted(
                    str(item.observable_id)
                    for item in layout_focus_targets
                    if item.observable_id is not None
                )
            ) or "<none>"
            raise RuntimeError(
                f"Unknown runtime focus observable {normalized_observable_id} for layout "
                f"{selected_layout.key!r}. Available observables: {available}"
            )
        normalized_section_key = focus_target.section_key
        normalized_observable_id = focus_target.observable_id
    elif normalized_section_key is not None:
        matched_section = next(
            (
                section
                for section in selected_layout.sections
                if section.key.strip().casefold() == normalized_section_key.casefold()
            ),
            None,
        )
        if matched_section is None:
            available = ", ".join(section.key for section in selected_layout.sections) or "<none>"
            raise RuntimeError(
                f"Unknown runtime focus section {section_key!r} for layout "
                f"{selected_layout.key!r}. Available sections: {available}"
            )
        normalized_section_key = matched_section.key
    else:
        focus_target = next(
            iter(layout_focus_targets),
            None,
        )
        normalized_section_key = focus_target.section_key if focus_target is not None else None
        normalized_observable_id = focus_target.observable_id if focus_target is not None else None
    return ResolvedRuntimeFocusSelection(
        layout_config_id=normalized_layout_config_id,
        layout_key=normalized_layout_key,
        section_key=normalized_section_key,
        observable_id=normalized_observable_id,
    )


class InterfaceHostControlPlaneRuntime(Protocol):
    repository_root: Path
    interface_config_bundle: InterfaceConfigBundle | None
    transport_session: "InterfaceTransportSession | None"
    bundle_window_layout_enabled: bool
    bundle_window_key: str | None
    bundle_layout_config_id: UUID | None
    bundle_layout_key: str | None
    bundle_focus_section_key: str | None
    bundle_focus_observable_id: UUID | None
    _active_profile_id: str
    _selected_step_id: str | None
    _selected_step_explicit: bool
    _selected_workspace_root: Path | None
    _joined_workspace_root: Path | None
    _selected_semantic_package_selector: str | None
    _selected_semantic_package_selector_explicit: bool
    _selected_semantic_package: InterfaceHostServiceSelectedSemanticPackageState | None
    _selected_workspace_semantic_source: (
        InterfaceHostServiceWorkspaceSemanticSourceState | None
    )
    _interface_window_layout_request_idempotency: dict[str, str]
    _workspace_registry: object | None
    _workspace_discovery: InterfaceHostServiceWorkspaceDiscoveryState | None
    _control_plane_workspace: InterfaceHostServiceControlPlaneWorkspaceState | None
    _attached_namespace_counts_by_workspace: dict[str, int]

    def state(self) -> InterfaceHostServiceState:
        ...

    def activate_interface_config_bundle_for_request(
        self,
        *,
        interface_package_id: UUID | str | None = None,
        interface_package_name: str | None = None,
    ) -> InterfaceConfigBundle | None:
        ...

    async def _refresh_host_surface(self) -> None:
        ...

    async def _refresh_host_surface_from_cached_state(self) -> None:
        ...

    async def _refresh_hosted_service_status(self) -> None:
        ...

    async def _refresh_workspace_entry_state(self) -> None:
        ...


async def apply_workspace_session(
    runtime: InterfaceHostControlPlaneRuntime,
    *,
    selected_workspace_root: Path | None,
    joined_workspace_root: Path | None,
    selected_runtime_focus_section_key: str | None = None,
    selected_runtime_focus_observable_id: UUID | str | None = None,
    attached_namespace_counts_by_workspace: dict[str, int] | None = None,
) -> InterfaceHostServiceState:
    runtime._selected_workspace_root = (
        selected_workspace_root.expanduser().resolve()
        if selected_workspace_root is not None
        else None
    )
    runtime._joined_workspace_root = (
        joined_workspace_root.expanduser().resolve()
        if joined_workspace_root is not None
        else None
    )
    try:
        selection = normalize_runtime_focus_selection(
            layout_config_id=None,
            layout_key=None,
            section_key=selected_runtime_focus_section_key,
            observable_id=selected_runtime_focus_observable_id,
            interface_config_bundle=runtime.interface_config_bundle,
            bundle_window_key=runtime.bundle_window_key,
        )
        runtime.bundle_layout_config_id = selection.layout_config_id
        runtime.bundle_layout_key = selection.layout_key
        runtime.bundle_focus_section_key = selection.section_key
        runtime.bundle_focus_observable_id = selection.observable_id
    except RuntimeError:
        runtime.bundle_layout_config_id = None
        runtime.bundle_layout_key = None
        runtime.bundle_focus_section_key = None
        runtime.bundle_focus_observable_id = None
    runtime._attached_namespace_counts_by_workspace = dict(
        attached_namespace_counts_by_workspace or {}
    )
    await runtime._refresh_host_surface()
    return runtime.state()


async def select_control_plane_step(
    runtime: InterfaceHostControlPlaneRuntime,
    *,
    step_id: str | None,
) -> InterfaceHostServiceState:
    normalized = normalize_selected_step_id(step_id)
    if runtime._control_plane_workspace is None:
        await runtime._refresh_host_surface()
    workspace = runtime._control_plane_workspace
    valid_step_ids = (
        {item.step_id for item in workspace.orchestration_steps}
        if workspace is not None
        else set()
    )
    if normalized is not None and normalized not in valid_step_ids:
        available = ", ".join(sorted(valid_step_ids)) or "<none>"
        raise RuntimeError(
            f"Unknown control-plane step: {normalized}. Available steps: {available}"
        )
    runtime._selected_step_id = normalized
    runtime._selected_step_explicit = normalized is not None
    await runtime._refresh_host_surface()
    return runtime.state()


async def select_control_plane_profile(
    runtime: InterfaceHostControlPlaneRuntime,
    *,
    profile_id: str,
) -> InterfaceHostServiceState:
    normalized = normalize_control_plane_profile_id(profile_id)
    if normalized not in CONTROL_PLANE_PROFILE_IDS:
        available = ", ".join(CONTROL_PLANE_PROFILE_IDS)
        raise RuntimeError(
            f"Unknown control-plane profile: {profile_id}. Available profiles: {available}"
        )
    runtime._active_profile_id = normalized
    runtime._selected_step_id = None
    runtime._selected_step_explicit = False
    await runtime._refresh_hosted_service_status()
    await runtime._refresh_host_surface()
    return runtime.state()


async def select_control_plane_workspace(
    runtime: InterfaceHostControlPlaneRuntime,
    *,
    workspace_root: str,
) -> InterfaceHostServiceState:
    _ = workspace_root
    raise RuntimeError(
        "Workspace selection is not a generic InterfaceHost control-plane action. "
        "Mount a Workspace interface/pane package and invoke its declared API or SDK operation."
    )


async def select_control_plane_semantic_package(
    runtime: InterfaceHostControlPlaneRuntime,
    *,
    selector_key: str | None,
) -> InterfaceHostServiceState:
    _ = selector_key
    raise RuntimeError(
        "Workspace semantic-package selection is not a generic InterfaceHost "
        "control-plane action. Mount a Workspace interface/pane package and invoke "
        "its declared API or SDK operation."
    )


async def select_control_plane_runtime_layout(
    runtime: InterfaceHostControlPlaneRuntime,
    *,
    layout_config_id: UUID | str | None,
) -> InterfaceHostServiceState:
    if not runtime.bundle_window_layout_enabled or runtime.interface_config_bundle is None:
        raise RuntimeError(
            "Interface Host does not have a bundle-backed runtime layout to select."
        )
    selection = normalize_runtime_focus_selection(
        layout_config_id=layout_config_id,
        layout_key=None,
        section_key=None,
        observable_id=None,
        interface_config_bundle=runtime.interface_config_bundle,
        bundle_window_key=runtime.bundle_window_key,
    )
    return await _apply_resolved_runtime_focus_selection(
        runtime,
        selection=selection,
    )


async def _apply_resolved_runtime_focus_selection(
    runtime: InterfaceHostControlPlaneRuntime,
    *,
    selection: ResolvedRuntimeFocusSelection,
) -> InterfaceHostServiceState:
    runtime.bundle_layout_config_id = selection.layout_config_id
    runtime.bundle_layout_key = selection.layout_key
    runtime.bundle_focus_section_key = selection.section_key
    runtime.bundle_focus_observable_id = selection.observable_id
    activated_via_experience = False
    try:
        import aware_interface_service.host.capabilities.experience as experience_capability_mod

        runtime_state = runtime.state().runtime
        representation = _runtime_representation_for_selection(
            runtime_state=runtime_state,
            selection=selection,
        )
        activation = await experience_capability_mod.activate_experience_section_graph_binding_for_runtime_focus(
            transport_session=runtime.transport_session,
            interface_config_bundle=runtime.interface_config_bundle,
            navigation_context_layout_target=(
                runtime_state.navigation_context_layout_target
                if runtime_state is not None
                else None
            ),
            section_state_addresses=_runtime_section_state_addresses(runtime_state),
            window_key=runtime.bundle_window_key,
            layout_key=selection.layout_key,
            section_key=selection.section_key,
            observable_id=selection.observable_id,
            representation=representation,
        )
        activated_via_experience = activation is not None
    except Exception:
        activated_via_experience = False
    if not activated_via_experience:
        try:
            import aware_interface_service.host.capabilities.attention as attention_capability_mod

            await attention_capability_mod.activate_attention_observable_for_runtime_focus(
                transport_session=runtime.transport_session,
                interface_config_bundle=runtime.interface_config_bundle,
                bundle_window_key=runtime.bundle_window_key,
                layout_config_id=selection.layout_config_id,
                layout_key=selection.layout_key,
                section_key=selection.section_key,
                observable_id=selection.observable_id,
            )
        except Exception:
            pass
    await runtime._refresh_host_surface_from_cached_state()
    return runtime.state()


def _runtime_representation_for_selection(
    *,
    runtime_state: InterfaceRuntimeState | None,
    selection: ResolvedRuntimeFocusSelection,
) -> InterfaceRuntimeSectionRepresentationState | None:
    if runtime_state is None:
        return None
    if selection.representation_id is not None:
        return next(
            (
                item
                for item in runtime_state.section_representations
                if item.representation_id == selection.representation_id
            ),
            None,
        )
    return next(
        (
            item
            for item in runtime_state.section_representations
            if (
                selection.section_key is None
                or item.section_key.strip().casefold()
                == selection.section_key.strip().casefold()
            )
            and (
                selection.observable_id is None
                or item.observable_id == selection.observable_id
            )
            and (
                selection.layout_config_id is None
                or item.layout_config_id == selection.layout_config_id
            )
        ),
        None,
    )


def _runtime_section_state_addresses(
    runtime_state: InterfaceRuntimeState | None,
) -> dict[str, InterfaceResolvedSectionStateAddress]:
    if runtime_state is None:
        return {}
    addresses: dict[str, InterfaceResolvedSectionStateAddress] = {}
    for pane in runtime_state.resolved_panes:
        if pane.section_key in addresses:
            continue
        addresses[pane.section_key] = InterfaceResolvedSectionStateAddress(
            section_key=pane.section_key,
            layout_section_id=pane.layout_section_id,
            section_focus_scope_id=pane.section_focus_scope_id,
            focus_scope_id=pane.focus_scope_id,
            focus_id=pane.focus_id,
            observable_id=pane.object_projection_graph_observable_id,
            branch_id=pane.branch_id,
            state_projection_hash=pane.state_projection_hash,
            focus_target=pane.focus_target,
        )
    return addresses


async def activate_control_plane_runtime_focus(
    runtime: InterfaceHostControlPlaneRuntime,
    *,
    representation_id: UUID | str | None = None,
    layout_config_id: UUID | str | None = None,
    layout_key: str | None = None,
    section_key: str | None = None,
    observable_id: UUID | str | None = None,
) -> InterfaceHostServiceState:
    if not runtime.bundle_window_layout_enabled or runtime.interface_config_bundle is None:
        raise RuntimeError(
            "Interface Host does not have a bundle-backed runtime layout to select."
        )
    normalized_representation_id = _normalize_optional_uuid(representation_id)
    if normalized_representation_id is None:
        raise RuntimeError(
            "Bundle-backed runtime focus activation requires a compiled representation id. "
            "Use select_control_plane_runtime_layout(...) for layout-only switches."
        )
    selection = _resolve_runtime_focus_selection_from_representation_id(
        runtime,
        representation_id=normalized_representation_id,
    )
    if selection is None:
        await runtime._refresh_host_surface_from_cached_state()
        selection = _resolve_runtime_focus_selection_from_representation_id(
            runtime,
            representation_id=normalized_representation_id,
        )
    if selection is None:
        runtime_state = runtime.state().runtime
        available = ", ".join(
            sorted(
                str(item.representation_id)
                for item in (
                    runtime_state.section_representations
                    if runtime_state is not None
                    else ()
                )
            )
        ) or "<none>"
        raise RuntimeError(
            f"Unknown runtime representation id: {normalized_representation_id}. "
            f"Available representation ids: {available}"
        )
    return await _apply_resolved_runtime_focus_selection(
        runtime,
        selection=selection,
    )


async def request_interface_window_layout(
    runtime: InterfaceHostControlPlaneRuntime,
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
    _ = requested_by_service, requested_by_operation, reason
    normalized_idempotency_key = _normalize_optional_text(idempotency_key)
    request_fingerprint = _layout_request_idempotency_fingerprint(
        interface_package_id=interface_package_id,
        interface_package_name=interface_package_name,
        window_key=window_key,
        layout_config_id=layout_config_id,
        layout_key=layout_key,
        section_key=section_key,
        observable_id=observable_id,
        representation_id=representation_id,
    )
    if normalized_idempotency_key is not None:
        previous_fingerprint = runtime._interface_window_layout_request_idempotency.get(
            normalized_idempotency_key
        )
        if previous_fingerprint == request_fingerprint:
            return runtime.state()
        if previous_fingerprint is not None:
            raise RuntimeError(
                "Interface window-layout request idempotency key was already used "
                "for a different target: "
                + normalized_idempotency_key
            )
    interface_config_bundle = runtime.activate_interface_config_bundle_for_request(
        interface_package_id=interface_package_id,
        interface_package_name=interface_package_name,
    )
    if not runtime.bundle_window_layout_enabled or interface_config_bundle is None:
        raise RuntimeError(
            "Interface Host does not have a bundle-backed runtime layout to select."
        )
    _validate_request_interface_package(
        interface_config_bundle=interface_config_bundle,
        interface_package_id=interface_package_id,
        interface_package_name=interface_package_name,
    )
    resolved_window_key = _resolve_request_window_key(
        interface_config_bundle=interface_config_bundle,
        bundle_window_key=runtime.bundle_window_key,
        window_key=window_key,
    )
    previous_window_key = runtime.bundle_window_key
    runtime.bundle_window_key = resolved_window_key
    normalized_representation_id = _normalize_optional_uuid(representation_id)
    try:
        if normalized_representation_id is not None:
            selection = _resolve_runtime_focus_selection_from_representation_id(
                runtime,
                representation_id=normalized_representation_id,
            )
            if selection is None:
                await runtime._refresh_host_surface_from_cached_state()
                selection = _resolve_runtime_focus_selection_from_representation_id(
                    runtime,
                    representation_id=normalized_representation_id,
                )
            if selection is None:
                runtime_state = runtime.state().runtime
                available = ", ".join(
                    sorted(
                        str(item.representation_id)
                        for item in (
                            runtime_state.section_representations
                            if runtime_state is not None
                            else ()
                        )
                    )
                ) or "<none>"
                raise RuntimeError(
                    f"Unknown runtime representation id: {normalized_representation_id}. "
                    f"Available representation ids: {available}"
                )
        else:
            selection = normalize_runtime_focus_selection(
                layout_config_id=layout_config_id,
                layout_key=layout_key,
                section_key=section_key,
                observable_id=observable_id,
                interface_config_bundle=interface_config_bundle,
                bundle_window_key=resolved_window_key,
            )
        state = await _apply_resolved_runtime_focus_selection(
            runtime,
            selection=selection,
        )
        if normalized_idempotency_key is not None:
            runtime._interface_window_layout_request_idempotency[
                normalized_idempotency_key
            ] = request_fingerprint
        return state
    except Exception:
        runtime.bundle_window_key = previous_window_key
        raise


__all__ = [
    "activate_control_plane_runtime_focus",
    "InterfaceHostControlPlaneRuntime",
    "ResolvedRuntimeFocusSelection",
    "apply_workspace_session",
    "normalize_runtime_focus_selection",
    "request_interface_window_layout",
    "select_control_plane_profile",
    "select_control_plane_runtime_layout",
    "select_control_plane_semantic_package",
    "select_control_plane_step",
    "select_control_plane_workspace",
]
