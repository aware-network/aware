from __future__ import annotations

from uuid import UUID

from aware_interface.lifecycle.models import (
    InterfaceBackendState,
    InterfaceGateState,
    InterfaceMaterializedPaneState,
    InterfaceRuntimeFocusState,
    InterfaceRuntimePaneRenderSpecState,
    InterfaceRuntimeSectionRepresentationState,
    InterfaceRuntimeFocusTarget,
    InterfaceRuntimeLayoutState,
    InterfaceRuntimeWindowState,
    InterfaceResolvedPaneDescriptor,
    InterfaceResolvedView,
    InterfaceRuntimeState,
    InterfaceNavigationContextLayoutTargetState,
    InterfaceWindowLayoutState,
)


def compose_interface_runtime_state(
    *,
    backend: InterfaceBackendState,
    gate_state: InterfaceGateState | None = None,
    resolved_view: InterfaceResolvedView | None = None,
    navigation_context_layout_target: InterfaceNavigationContextLayoutTargetState | None = None,
    window_layout: InterfaceWindowLayoutState | None = None,
    active_window: InterfaceRuntimeWindowState | None = None,
    windows: tuple[InterfaceRuntimeWindowState, ...] = (),
    active_layout_config_id: UUID | None = None,
    layout_states: tuple[InterfaceRuntimeLayoutState, ...] = (),
    active_focus: InterfaceRuntimeFocusState | None = None,
    available_focus_targets: tuple[InterfaceRuntimeFocusTarget, ...] = (),
    section_representations: tuple[
        InterfaceRuntimeSectionRepresentationState, ...
    ] = (),
    resolved_panes: tuple[InterfaceResolvedPaneDescriptor, ...] = (),
    materialized_pane_states: tuple[InterfaceMaterializedPaneState, ...] = (),
    dynamic_pane_render_specs: tuple[InterfaceRuntimePaneRenderSpecState, ...] = (),
    warnings: tuple[str, ...] = (),
) -> InterfaceRuntimeState:
    return InterfaceRuntimeState(
        backend=backend,
        gate_state=gate_state,
        resolved_view=resolved_view,
        navigation_context_layout_target=navigation_context_layout_target,
        window_layout=window_layout,
        active_window=active_window,
        windows=windows,
        active_layout_config_id=(
            active_layout_config_id
            if active_layout_config_id is not None
            else (window_layout.layout_config_id if window_layout is not None else None)
        ),
        layout_states=layout_states,
        active_focus=active_focus,
        available_focus_targets=available_focus_targets,
        section_representations=section_representations,
        resolved_panes=resolved_panes,
        materialized_pane_states=materialized_pane_states,
        dynamic_pane_render_specs=dynamic_pane_render_specs,
        warnings=warnings,
    )


__all__ = [
    "compose_interface_runtime_state",
]
