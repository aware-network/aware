from __future__ import annotations

import re
from uuid import UUID

from aware_attention_ontology.stable_ids import (
    stable_layout_config_id,
    stable_layout_config_section_config_id,
)
from aware_interface.lifecycle.models import (
    InterfaceWindowLayoutSectionState,
    InterfaceWindowLayoutState,
)
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
    InterfaceWindowConfigBundle,
    InterfaceWindowConfigLayoutBundle,
)

_DEFAULT_ENTRY_CONTROL_PLANE_VIEW_ID = "entry.control-plane"
_BOOTSTRAP_LAYOUT_KEY = "bootstrap.control-plane"


def resolve_bootstrap_window_layout_state(
    *,
    active: bool,
    projection_view_id: str | None,
    has_target_statuses: bool,
    has_logs: bool,
    resolved_at: str | None = None,
) -> InterfaceWindowLayoutState | None:
    if not active:
        return None

    resolved_view_id = str(
        projection_view_id or _DEFAULT_ENTRY_CONTROL_PLANE_VIEW_ID
    ).strip() or _DEFAULT_ENTRY_CONTROL_PLANE_VIEW_ID
    layout_config_id = stable_layout_config_id(key=_BOOTSTRAP_LAYOUT_KEY)

    return InterfaceWindowLayoutState(
        source_kind="interface_bootstrap",
        window_key="bootstrap",
        layout_config_id=layout_config_id,
        layout_key=_BOOTSTRAP_LAYOUT_KEY,
        title="Bootstrap Control Plane",
        description=(
            "Interface-owned bootstrap layout before canonical workspace "
            "materialization is live."
        ),
        frame_mode="grid",
        version_hash="interface-bootstrap-control-plane-v1",
        resolved_at=resolved_at,
        stale=False,
        sections=(
            InterfaceWindowLayoutSectionState(
                section_key="overview",
                layout_config_section_config_id=stable_layout_config_section_config_id(
                    layout_config_id=layout_config_id,
                    section_key="overview",
                ),
                title="Setup Overview",
                description="Bootstrap owner and runtime summary.",
                order=0,
                flex=1.0,
                is_visible=True,
                projection_view_id=resolved_view_id,
                pane_key="setup_overview",
            ),
            InterfaceWindowLayoutSectionState(
                section_key="actions",
                layout_config_section_config_id=stable_layout_config_section_config_id(
                    layout_config_id=layout_config_id,
                    section_key="actions",
                ),
                title="Action Center",
                description="Available next actions for the current bootstrap phase.",
                order=1,
                flex=1.0,
                is_visible=True,
                projection_view_id=resolved_view_id,
                pane_key="action_center",
            ),
            InterfaceWindowLayoutSectionState(
                section_key="targets",
                layout_config_section_config_id=stable_layout_config_section_config_id(
                    layout_config_id=layout_config_id,
                    section_key="targets",
                ),
                title="Bootstrap Targets",
                description="Target-level runtime readiness and blockers.",
                order=2,
                flex=1.0,
                is_visible=has_target_statuses,
                projection_view_id=resolved_view_id,
                pane_key="bootstrap_targets",
            ),
            InterfaceWindowLayoutSectionState(
                section_key="activity",
                layout_config_section_config_id=stable_layout_config_section_config_id(
                    layout_config_id=layout_config_id,
                    section_key="activity",
                ),
                title="Current Activity",
                description="Current pressure point and recent progress feed.",
                order=3,
                flex=1.0,
                is_visible=True,
                projection_view_id=resolved_view_id,
                pane_key="current_activity",
            ),
            InterfaceWindowLayoutSectionState(
                section_key="context",
                layout_config_section_config_id=stable_layout_config_section_config_id(
                    layout_config_id=layout_config_id,
                    section_key="context",
                ),
                title="Runtime Context",
                description="Current endpoint, view, and layout context.",
                order=4,
                flex=1.0,
                is_visible=True,
                projection_view_id=resolved_view_id,
                pane_key="runtime_context",
            ),
            InterfaceWindowLayoutSectionState(
                section_key="logs",
                layout_config_section_config_id=stable_layout_config_section_config_id(
                    layout_config_id=layout_config_id,
                    section_key="logs",
                ),
                title="Technical Logs",
                description="Expanded technical trace feed for the active bootstrap rail.",
                order=5,
                flex=1.0,
                is_visible=has_logs,
                projection_view_id=resolved_view_id,
                pane_key="technical_logs",
            ),
        ),
    )


def resolve_bundle_window_layout_state(
    *,
    interface_config_bundle: InterfaceConfigBundle | None,
    preferred_window_key: str | None = None,
    preferred_layout_config_id: UUID | None = None,
    preferred_layout_key: str | None = None,
    resolved_at: str | None = None,
) -> InterfaceWindowLayoutState | None:
    if interface_config_bundle is None:
        return None

    window_config = _select_window_config(
        interface_config_bundle=interface_config_bundle,
        preferred_window_key=preferred_window_key,
    )
    if window_config is None:
        return None

    layout_config = _select_layout_config(
        window_config=window_config,
        preferred_layout_config_id=preferred_layout_config_id,
        preferred_layout_key=preferred_layout_key,
    )
    if layout_config is None:
        return None

    description = window_config.description
    if description is None:
        description = (
            "Layout resolved from canonical Interface bundle truth."
        )

    return InterfaceWindowLayoutState(
        source_kind="interface_bundle",
        window_key=window_config.key,
        layout_config_id=layout_config.layout_config_id,
        layout_key=layout_config.key,
        title=_title_from_key(layout_config.key),
        description=description,
        frame_mode="grid" if len(layout_config.sections) > 1 else "vertical",
        version_hash=(
            f"{interface_config_bundle.interface_config_id}:"
            f"{window_config.window_config_id}:{layout_config.layout_config_id}"
        ),
        resolved_at=resolved_at,
        stale=False,
        sections=tuple(
            InterfaceWindowLayoutSectionState(
                section_key=section.key,
                layout_config_section_config_id=section.layout_config_section_config_id,
                title=_title_from_key(section.key),
                order=index,
                flex=1.0,
                is_visible=True,
            )
            for index, section in enumerate(layout_config.sections)
        ),
    )


def _select_window_config(
    *,
    interface_config_bundle: InterfaceConfigBundle,
    preferred_window_key: str | None,
) -> InterfaceWindowConfigBundle | None:
    if not interface_config_bundle.window_configs:
        return None
    normalized_window_key = (preferred_window_key or "").strip().casefold()
    if normalized_window_key:
        for window_config in interface_config_bundle.window_configs:
            if window_config.key.casefold() == normalized_window_key:
                return window_config
    return interface_config_bundle.window_configs[0]


def _select_layout_config(
    *,
    window_config: InterfaceWindowConfigBundle,
    preferred_layout_config_id: UUID | None = None,
    preferred_layout_key: str | None,
) -> InterfaceWindowConfigLayoutBundle | None:
    if not window_config.layout_configs:
        return None
    if preferred_layout_config_id is not None:
        for layout_config in window_config.layout_configs:
            if layout_config.layout_config_id == preferred_layout_config_id:
                return layout_config
    normalized_layout_key = (preferred_layout_key or "").strip().casefold()
    if normalized_layout_key:
        for layout_config in window_config.layout_configs:
            if layout_config.key.casefold() == normalized_layout_key:
                return layout_config
    for layout_config in window_config.layout_configs:
        if layout_config.is_default:
            return layout_config
    return window_config.layout_configs[0]


def _title_from_key(value: str) -> str:
    normalized = re.sub(r"[_\\-]+", " ", value.strip()).strip()
    if not normalized:
        return "Untitled"
    return " ".join(part.capitalize() for part in normalized.split())


__all__ = [
    "resolve_bundle_window_layout_state",
    "resolve_bootstrap_window_layout_state",
]
