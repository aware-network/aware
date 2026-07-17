from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import TYPE_CHECKING, Callable
from uuid import UUID

from aware_interface import (
    InterfaceRuntimeFocusState,
    InterfaceRuntimeSectionRepresentationState,
    InterfaceRuntimeFocusTarget,
    InterfaceRuntimeLayoutState,
    InterfaceResolvedPaneDescriptor,
    InterfaceResolvedSectionStateAddress,
    InterfaceNavigationContextLayoutTargetState,
    InterfaceWindowLayoutSectionState,
    InterfaceWindowLayoutState,
    resolve_bootstrap_window_layout_state,
    resolve_bundle_backed_pane_descriptors,
)
from aware_attention_ontology.stable_ids import (
    stable_layout_config_id,
    stable_layout_config_section_config_id,
)
from aware_interface.host_capabilities import InterfaceHostPaneContribution
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
    InterfaceWindowConfigBundle,
    InterfaceWindowConfigLayoutBundle,
    InterfaceWindowLayoutSectionBundle,
)
from aware_interface.lifecycle.window_layout import (
    resolve_bundle_window_layout_state,
)
from aware_interface_service.host.state import (
    InterfaceHostLayoutInputs,
    operator_profile_active,
)
from aware_interface_service.host.capabilities.identity import (
    CONTROL_IDENTITY_ADMISSION_SCREEN_KEY,
)
from aware_interface_service.models import (
    InterfaceHostServiceCurrentScreen,
    InterfaceHostServiceLaneSyncState,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from aware_interface.session_port import SectionFocusScopeLane


def _resolved_pane_kind(section_key: str, pane_key: str | None) -> str:
    normalized_pane_key = (pane_key or "").strip()
    if normalized_pane_key:
        return normalized_pane_key
    normalized_section_key = section_key.strip()
    return normalized_section_key or "unknown"


def _contribution_by_section_key(
    inputs: InterfaceHostLayoutInputs,
) -> dict[str, InterfaceHostPaneContribution]:
    return {
        contribution.section_key.strip().casefold(): contribution
        for contribution in inputs.pane_contributions
        if contribution.section_key.strip()
    }


def _pane_contribution_for_section(
    *,
    inputs: InterfaceHostLayoutInputs,
    section_key: str,
) -> InterfaceHostPaneContribution | None:
    normalized_section_key = section_key.strip().casefold()
    return _contribution_by_section_key(inputs).get(normalized_section_key)


def _current_screen_prefers_pane_contributions(
    current_screen: InterfaceHostServiceCurrentScreen | None,
) -> bool:
    return (
        current_screen is not None
        and current_screen.screen_key.strip().casefold() == "interface_admission"
    )


def _contribution_backed_window_layout(
    *,
    inputs: InterfaceHostLayoutInputs,
    projection_view_id: str | None,
    resolved_at: str | None,
) -> InterfaceWindowLayoutState | None:
    if not inputs.pane_contributions:
        return None
    layout_key = "bootstrap.panes"
    layout_config_id = stable_layout_config_id(key=layout_key)
    sections: list[InterfaceWindowLayoutSectionState] = []
    seen_sections: set[str] = set()
    for order, contribution in enumerate(inputs.pane_contributions):
        normalized_section = contribution.section_key.strip()
        if not normalized_section:
            continue
        section_key = normalized_section
        section_dedupe_key = section_key.casefold()
        if section_dedupe_key in seen_sections:
            continue
        seen_sections.add(section_dedupe_key)
        sections.append(
            InterfaceWindowLayoutSectionState(
                section_key=section_key,
                layout_config_section_config_id=stable_layout_config_section_config_id(
                    layout_config_id=layout_config_id,
                    section_key=section_key,
                ),
                title=contribution.title,
                description=contribution.readiness_reason or contribution.summary,
                order=order,
                flex=1.0,
                is_visible=True,
                projection_view_id=projection_view_id,
                pane_key=contribution.pane_key,
            )
        )
    if not sections:
        return None
    return InterfaceWindowLayoutState(
        source_kind="interface_bootstrap_pane_contributions",
        window_key="bootstrap",
        layout_config_id=layout_config_id,
        layout_key=layout_key,
        title="Bootstrap Panes",
        description=(
            "Interface-hosted bootstrap panes resolved before a full Interface "
            "package is mounted."
        ),
        frame_mode="grid" if len(sections) > 1 else "vertical",
        version_hash="interface-bootstrap-pane-contributions-v1",
        resolved_at=resolved_at,
        stale=False,
        sections=tuple(sections),
    )


def build_runtime_window_layout(
    *,
    inputs: InterfaceHostLayoutInputs,
    resolved_at: str,
) -> InterfaceWindowLayoutState | None:
    current_screen = inputs.current_screen
    resolved_view = inputs.runtime_state.resolved_view
    bootstrap_active = (
        (
            operator_profile_active(inputs.active_profile_id)
            and (
                inputs.local_service_host is not None
                and inputs.local_service_host.managed
            )
        )
        or (
            operator_profile_active(inputs.active_profile_id)
            and (
                inputs.local_node_runtime is not None
                and inputs.local_node_runtime.managed
            )
        )
        or (
            current_screen is not None
            and current_screen.screen_key
            in {
                "workspace_selection_gate",
                "workspace_start_gate",
                "workspace_join_gate",
                "local_service_host_gate",
                "local_node_runtime_gate",
                CONTROL_IDENTITY_ADMISSION_SCREEN_KEY,
            }
        )
        or bool(inputs.allowed_actions)
    )
    projection_view_id = (
        current_screen.projection_view_id
        if current_screen is not None and current_screen.projection_view_id
        else resolved_view.projection_view_id if resolved_view is not None else None
    )
    has_target_statuses = bool(
        operator_profile_active(inputs.active_profile_id)
        and inputs.local_node_runtime is not None
        and inputs.local_node_runtime.target_statuses
    )
    has_logs = bool(
        operator_profile_active(inputs.active_profile_id)
        and inputs.local_node_runtime is not None
        and inputs.local_node_runtime.recent_log_lines
    )
    contribution_layout_preferred = _current_screen_prefers_pane_contributions(
        current_screen
    ) and bool(inputs.pane_contributions)
    window_layout = (
        _contribution_backed_window_layout(
            inputs=inputs,
            projection_view_id=projection_view_id,
            resolved_at=resolved_at,
        )
        if contribution_layout_preferred
        else None
    )
    if window_layout is None:
        window_layout = (
            resolve_bundle_window_layout_state(
                interface_config_bundle=inputs.interface_config_bundle,
                preferred_window_key=(
                    inputs.navigation_context_layout_target.window_key
                    if inputs.navigation_context_layout_target is not None
                    and inputs.navigation_context_layout_target.window_key
                    else inputs.bundle_window_key
                ),
                preferred_layout_config_id=(
                    inputs.navigation_context_layout_target.layout_config_id
                    if inputs.navigation_context_layout_target is not None
                    and inputs.navigation_context_layout_target.layout_config_id
                    is not None
                    else inputs.bundle_layout_config_id
                ),
                preferred_layout_key=(
                    inputs.navigation_context_layout_target.layout_key
                    if inputs.navigation_context_layout_target is not None
                    and inputs.navigation_context_layout_target.layout_key
                    else inputs.bundle_layout_key
                ),
                resolved_at=resolved_at,
            )
            if inputs.bundle_window_layout_enabled
            else None
        )
    if (
        window_layout is not None
        and inputs.navigation_context_layout_target is not None
        and (
            inputs.navigation_context_layout_target.layout_config_id is not None
            or inputs.navigation_context_layout_target.layout_key
        )
    ):
        window_layout = replace(
            window_layout,
            source_kind="environment_navigation_context_layout_target",
        )
    if window_layout is None:
        window_layout = _contribution_backed_window_layout(
            inputs=inputs,
            projection_view_id=projection_view_id,
            resolved_at=resolved_at,
        )
    if window_layout is None:
        window_layout = resolve_bootstrap_window_layout_state(
            active=bootstrap_active,
            projection_view_id=projection_view_id,
            has_target_statuses=has_target_statuses,
            has_logs=has_logs,
            resolved_at=resolved_at,
        )
    return window_layout


def apply_runtime_layout_sections(
    *,
    window_layout: InterfaceWindowLayoutState,
    runtime_sections: tuple[InterfaceWindowLayoutSectionState, ...],
) -> InterfaceWindowLayoutState:
    if not runtime_sections:
        return window_layout
    base_by_section_config_id = {
        section.layout_config_section_config_id: section
        for section in window_layout.sections
        if section.layout_config_section_config_id is not None
    }
    base_by_layout_section_id = {
        section.layout_section_id: section
        for section in window_layout.sections
        if section.layout_section_id is not None
    }
    base_by_key = {
        section.section_key.strip().casefold(): section
        for section in window_layout.sections
        if section.section_key.strip()
    }
    sections: list[InterfaceWindowLayoutSectionState] = []
    for runtime_section in sorted(
        runtime_sections,
        key=lambda item: (item.order, item.section_key.strip().casefold()),
    ):
        normalized_key = runtime_section.section_key.strip()
        if not normalized_key:
            continue
        if runtime_section.layout_config_section_config_id is not None:
            base = base_by_section_config_id.get(
                runtime_section.layout_config_section_config_id
            )
        elif runtime_section.layout_section_id is not None:
            base = base_by_layout_section_id.get(runtime_section.layout_section_id)
        else:
            # Compatibility only for legacy/runtime rows that carry no graph id.
            base = base_by_key.get(normalized_key.casefold())
        sections.append(
            InterfaceWindowLayoutSectionState(
                section_key=normalized_key,
                layout_config_section_config_id=(
                    runtime_section.layout_config_section_config_id
                    if runtime_section.layout_config_section_config_id is not None
                    else (
                        base.layout_config_section_config_id
                        if base is not None
                        else None
                    )
                ),
                layout_section_id=runtime_section.layout_section_id,
                attention_session_section_id=(
                    runtime_section.attention_session_section_id
                ),
                title=runtime_section.title
                or (base.title if base is not None else None),
                description=(
                    runtime_section.description
                    or (base.description if base is not None else None)
                ),
                order=runtime_section.order,
                flex=runtime_section.flex,
                weight_micros=runtime_section.weight_micros,
                is_visible=runtime_section.is_visible,
                is_collapsed=runtime_section.is_collapsed,
                projection_view_id=(
                    base.projection_view_id if base is not None else None
                ),
                pane_key=base.pane_key if base is not None else None,
            )
        )
    if not sections:
        return window_layout
    return replace(
        window_layout,
        source_kind="attention_runtime_mount",
        sections=tuple(sections),
    )


def _resolve_window_bundle(
    *,
    interface_config_bundle: InterfaceConfigBundle | None,
    window_key: str | None,
) -> InterfaceWindowConfigBundle | None:
    if interface_config_bundle is None:
        return None
    preferred_window_key = (window_key or "").strip().casefold()
    if preferred_window_key:
        matching_window = next(
            (
                item
                for item in interface_config_bundle.window_configs
                if item.key.strip().casefold() == preferred_window_key
            ),
            None,
        )
        if matching_window is not None:
            return matching_window
    return next(iter(interface_config_bundle.window_configs), None)


def _resolve_layout_bundle(
    *,
    window_bundle: InterfaceWindowConfigBundle | None,
    layout_config_id: UUID | None,
    layout_key: str | None,
) -> InterfaceWindowConfigLayoutBundle | None:
    if window_bundle is None:
        return None
    if layout_config_id is not None:
        matching_layout = next(
            (
                item
                for item in window_bundle.layout_configs
                if item.layout_config_id == layout_config_id
            ),
            None,
        )
        if matching_layout is not None:
            return matching_layout
    normalized_layout_key = (layout_key or "").strip().casefold()
    if normalized_layout_key:
        matching_layout = next(
            (
                item
                for item in window_bundle.layout_configs
                if item.key.strip().casefold() == normalized_layout_key
            ),
            None,
        )
        if matching_layout is not None:
            return matching_layout
    return next(iter(window_bundle.layout_configs), None)


def derive_runtime_layout_states(
    *,
    interface_config_bundle: InterfaceConfigBundle | None,
    window_layout: InterfaceWindowLayoutState | None,
    active_focus: InterfaceRuntimeFocusState | None,
) -> tuple[InterfaceRuntimeLayoutState, ...]:
    if interface_config_bundle is None or window_layout is None:
        return ()
    window_bundle = _resolve_window_bundle(
        interface_config_bundle=interface_config_bundle,
        window_key=window_layout.window_key,
    )
    if window_bundle is None:
        return ()
    active_layout_config_id = (
        active_focus.layout_config_id
        if active_focus is not None and active_focus.layout_config_id is not None
        else window_layout.layout_config_id
    )
    return tuple(
        InterfaceRuntimeLayoutState(
            layout_config_id=layout.layout_config_id,
            layout_key=layout.key,
            label=_labelize_layout_key(layout.key),
            is_active=layout.layout_config_id == active_layout_config_id,
        )
        for layout in window_bundle.layout_configs
    )


def derive_runtime_focus_targets(
    *,
    interface_config_bundle,
    window_key: str | None,
) -> tuple[InterfaceRuntimeFocusTarget, ...]:
    window_bundle = _resolve_window_bundle(
        interface_config_bundle=interface_config_bundle,
        window_key=window_key,
    )
    if window_bundle is None:
        return ()

    observable_focus_targets = _derive_observable_focus_targets(
        interface_config_bundle=interface_config_bundle,
        window_bundle=window_bundle,
    )
    if observable_focus_targets:
        return observable_focus_targets

    focus_targets: list[InterfaceRuntimeFocusTarget] = []
    for layout in window_bundle.layout_configs:
        focus_targets.extend(_focus_targets_for_layout(layout))
    return tuple(focus_targets)


def derive_runtime_section_representations(
    *,
    interface_config_bundle: InterfaceConfigBundle | None,
    window_layout: InterfaceWindowLayoutState | None,
    active_focus: InterfaceRuntimeFocusState | None,
    navigation_context_layout_target: (
        InterfaceNavigationContextLayoutTargetState | None
    ) = None,
) -> tuple[InterfaceRuntimeSectionRepresentationState, ...]:
    if interface_config_bundle is None or window_layout is None:
        return ()
    window_bundle = _resolve_window_bundle(
        interface_config_bundle=interface_config_bundle,
        window_key=window_layout.window_key,
    )
    layout_bundle = _resolve_layout_bundle(
        window_bundle=window_bundle,
        layout_config_id=window_layout.layout_config_id,
        layout_key=window_layout.layout_key,
    )
    if window_bundle is None or layout_bundle is None:
        return ()

    section_order: dict[UUID, int] = {}
    visible_sections: dict[UUID, InterfaceWindowLayoutSectionBundle] = {}
    for order, section in enumerate(layout_bundle.sections):
        if not any(
            mounted_section.section_key.strip().casefold()
            == section.key.strip().casefold()
            for mounted_section in window_layout.sections
        ):
            continue
        section_order[section.layout_config_section_config_id] = order
        visible_sections[section.layout_config_section_config_id] = section
    if not visible_sections:
        return ()

    ordered_representations: list[
        tuple[int, int, InterfaceRuntimeSectionRepresentationState]
    ] = []
    encounter_order = 0
    for pane_config in interface_config_bundle.pane_configs:
        for projection_view in pane_config.projection_experience_views:
            observable_id = projection_view.object_projection_graph_observable_id
            if observable_id is None:
                continue
            for mount in projection_view.section_mounts:
                section_bundle = visible_sections.get(
                    mount.layout_config_section_config_id
                )
                if section_bundle is None:
                    continue
                thread_section_mapping = _thread_layout_section_mapping(
                    navigation_context_layout_target=navigation_context_layout_target,
                    section_key=section_bundle.key,
                    observable_id=observable_id,
                    view_ref=projection_view.view_ref,
                )
                ordered_representations.append(
                    (
                        section_order[mount.layout_config_section_config_id],
                        encounter_order,
                        InterfaceRuntimeSectionRepresentationState(
                            representation_id=pane_config.pane_config_id,
                            window_key=window_layout.window_key,
                            layout_config_id=layout_bundle.layout_config_id,
                            layout_key=layout_bundle.key,
                            section_key=section_bundle.key,
                            layout_config_section_config_id=mount.layout_config_section_config_id,
                            pane_name=pane_config.name,
                            pane_kind=pane_config.pane_kind,
                            label=_runtime_section_representation_label(
                                projection_view.view_ref
                            ),
                            observable_id=observable_id,
                            projection_experience_graph_identity_id=getattr(
                                projection_view,
                                "projection_experience_graph_identity_id",
                                None,
                            ),
                            object_projection_graph_identity_id=getattr(
                                projection_view,
                                "object_projection_graph_identity_id",
                                None,
                            ),
                            section_graph_binding_key=(
                                getattr(
                                    projection_view,
                                    "section_graph_binding_key",
                                    None,
                                )
                                or _mapping_optional_text(
                                    thread_section_mapping,
                                    "section_graph_binding_key",
                                )
                            ),
                            view_ref=(
                                _mapping_optional_text(
                                    thread_section_mapping,
                                    "view_ref",
                                )
                                or projection_view.view_ref
                            ),
                            projection_view_key=getattr(
                                projection_view,
                                "projection_view_key",
                                None,
                            ),
                            is_active=_runtime_focus_matches_representation(
                                active_focus=active_focus,
                                layout_config_id=layout_bundle.layout_config_id,
                                layout_key=layout_bundle.key,
                                section_key=section_bundle.key,
                                observable_id=observable_id,
                            ),
                        ),
                    )
                )
                encounter_order += 1
    ordered_representations.sort(key=lambda item: (item[0], item[1], item[2]))
    return tuple(item[2] for item in ordered_representations)


def _derive_observable_focus_targets(
    *,
    interface_config_bundle: InterfaceConfigBundle | None,
    window_bundle: InterfaceWindowConfigBundle,
) -> tuple[InterfaceRuntimeFocusTarget, ...]:
    if interface_config_bundle is None:
        return ()

    section_scoped_targets: list[tuple[int, str, InterfaceRuntimeFocusTarget]] = []
    for layout in window_bundle.layout_configs:
        section_targets = _observable_focus_targets_for_layout(
            interface_config_bundle=interface_config_bundle,
            layout=layout,
        )
        if not section_targets:
            continue
        for order, label_key, target in section_targets:
            section_scoped_targets.append((order, label_key, target))
    if not section_scoped_targets:
        return ()
    section_scoped_targets.sort(key=lambda item: (item[0], item[1]))
    return tuple(item[2] for item in section_scoped_targets)


def _observable_focus_targets_for_layout(
    *,
    interface_config_bundle: InterfaceConfigBundle,
    layout: InterfaceWindowConfigLayoutBundle,
) -> tuple[tuple[int, str, InterfaceRuntimeFocusTarget], ...]:
    section_index = {
        section.layout_config_section_config_id: order
        for order, section in enumerate(layout.sections)
    }
    section_by_id = {
        section.layout_config_section_config_id: section for section in layout.sections
    }
    candidates_by_section: dict[
        UUID, dict[UUID, tuple[int, str, InterfaceRuntimeFocusTarget]]
    ] = {}
    for pane_config in interface_config_bundle.pane_configs:
        for projection_view in pane_config.projection_experience_views:
            observable_id = projection_view.object_projection_graph_observable_id
            if observable_id is None:
                continue
            for mount in projection_view.section_mounts:
                if mount.layout_config_section_config_id not in section_by_id:
                    continue
                section = section_by_id[mount.layout_config_section_config_id]
                section_candidates = candidates_by_section.setdefault(
                    mount.layout_config_section_config_id,
                    {},
                )
                order = section_index[mount.layout_config_section_config_id]
                label = pane_config.name or _labelize_layout_key(section.key)
                candidate = InterfaceRuntimeFocusTarget(
                    layout_config_id=layout.layout_config_id,
                    layout_key=layout.key,
                    label=label,
                    section_key=section.key,
                    layout_config_section_config_id=mount.layout_config_section_config_id,
                    observable_id=observable_id,
                    view_ref=projection_view.view_ref,
                    projection_view_key=projection_view.projection_view_key,
                )
                existing = section_candidates.get(observable_id)
                candidate_tuple = (label.casefold(), candidate)
                if existing is None or candidate_tuple[:1] < existing[:1]:
                    section_candidates[observable_id] = candidate_tuple

    targets: list[tuple[int, str, InterfaceRuntimeFocusTarget]] = []
    for section_config_id, candidates in candidates_by_section.items():
        if len(candidates) <= 1:
            continue
        order = section_index[section_config_id]
        ordered_candidates = sorted(candidates.values(), key=lambda item: item[0])
        for candidate_order, (label_key, candidate) in enumerate(ordered_candidates):
            targets.append((order * 100 + candidate_order, label_key, candidate))
    return tuple(targets)


def _labelize_layout_key(layout_key: str) -> str:
    parts = [
        part.strip() for part in layout_key.replace("-", "_").split("_") if part.strip()
    ]
    if not parts:
        return "Layout"
    return " ".join(part[0].upper() + part[1:] for part in parts)


def _observable_key_from_view_ref(view_ref: str) -> str:
    parts = [segment.strip() for segment in view_ref.split(".") if segment.strip()]
    if len(parts) >= 2:
        return parts[1]
    if parts:
        return parts[-1]
    return view_ref


def _humanize_runtime_label(value: str) -> str:
    normalized = value.replace("-", "_").strip()
    if not normalized:
        return "View"
    return " ".join(part.capitalize() for part in normalized.split("_") if part.strip())


def _runtime_section_representation_label(view_ref: str) -> str:
    return _humanize_runtime_label(_observable_key_from_view_ref(view_ref))


def _runtime_focus_matches_representation(
    *,
    active_focus: InterfaceRuntimeFocusState | None,
    layout_config_id: UUID | None,
    layout_key: str,
    section_key: str,
    observable_id: UUID,
) -> bool:
    if active_focus is None:
        return False
    layout_matches = (
        active_focus.layout_config_id == layout_config_id
        if layout_config_id is not None
        else (active_focus.layout_key or "").strip().casefold()
        == layout_key.strip().casefold()
    )
    if not layout_matches:
        return False
    return (
        active_focus.section_key or ""
    ).strip().casefold() == section_key.strip().casefold() and active_focus.observable_id == observable_id


def _focus_targets_for_layout(
    layout: InterfaceWindowConfigLayoutBundle,
) -> tuple[InterfaceRuntimeFocusTarget, ...]:
    if not layout.sections:
        return ()
    return tuple(
        InterfaceRuntimeFocusTarget(
            layout_config_id=layout.layout_config_id,
            layout_key=layout.key,
            label=_labelize_layout_key(section.key),
            section_key=section.key,
            layout_config_section_config_id=section.layout_config_section_config_id,
        )
        for section in layout.sections
    )


def preferred_runtime_focus_section(
    *,
    window_layout: InterfaceWindowLayoutState | None,
    focus_targets: tuple[InterfaceRuntimeFocusTarget, ...],
) -> str | None:
    if window_layout is None:
        return None
    for target in focus_targets:
        if target.section_key is None:
            continue
        if target.layout_config_id == window_layout.layout_config_id or (
            target.layout_key.strip().casefold()
            == window_layout.layout_key.strip().casefold()
        ):
            return target.section_key
    return None


def _layout_section_config_id(
    *,
    sections: (
        tuple[InterfaceWindowLayoutSectionBundle, ...]
        | list[InterfaceWindowLayoutSectionBundle]
    ),
    section_key: str,
) -> UUID | None:
    normalized_section_key = section_key.strip().casefold()
    for section in sections:
        if section.key.strip().casefold() == normalized_section_key:
            return section.layout_config_section_config_id
    return None


def resolved_pane_state_source_kind(section_key: str) -> str:
    return {
        "overview": "current_screen",
        "actions": "allowed_actions",
        "targets": "control_plane_workspace",
        "activity": "current_operation",
        "context": "resolved_view",
        "logs": "local_node_runtime_logs",
    }.get(section_key, "section_focus_scope_lane")


def resolved_pane_state_source_kind_for_inputs(
    *,
    section_key: str,
    inputs: InterfaceHostLayoutInputs,
) -> str:
    contribution = _pane_contribution_for_section(
        inputs=inputs,
        section_key=section_key,
    )
    if contribution is not None:
        return "host_pane_contribution"
    return resolved_pane_state_source_kind(section_key)


def resolved_pane_action_keys(
    *,
    section_key: str,
    inputs: InterfaceHostLayoutInputs,
) -> tuple[str, ...]:
    contribution = _pane_contribution_for_section(
        inputs=inputs,
        section_key=section_key,
    )
    if contribution is not None:
        return contribution.action_keys
    if section_key != "actions":
        return ()
    return tuple(action.action_key for action in inputs.allowed_actions)


def resolved_pane_summary(
    *,
    section_key: str,
    projection_view_id: str | None,
    inputs: InterfaceHostLayoutInputs,
) -> str | None:
    contribution = _pane_contribution_for_section(
        inputs=inputs,
        section_key=section_key,
    )
    if contribution is not None:
        return contribution.summary
    current_screen_message = (
        inputs.current_screen.message if inputs.current_screen is not None else None
    )
    if section_key == "overview":
        if current_screen_message:
            return current_screen_message
        return (
            inputs.current_operation.summary
            if inputs.current_operation is not None
            else None
        )
    if section_key == "actions":
        count = len(inputs.allowed_actions)
        if count:
            noun = "action" if count == 1 else "actions"
            return f"{count} {noun} available."
        return current_screen_message
    if section_key == "targets":
        workspace = inputs.control_plane_workspace
        if workspace is not None:
            selected = next(
                (step for step in workspace.orchestration_steps if step.selected),
                None,
            )
            current = next(
                (step for step in workspace.orchestration_steps if step.current),
                None,
            )
            active = selected or current
            if active is not None:
                return active.summary or active.title
            count = len(workspace.orchestration_steps)
            if count:
                noun = "step" if count == 1 else "steps"
                return f"{count} orchestration {noun} tracked."
        return (
            inputs.current_operation.current_target_title
            if inputs.current_operation is not None
            else None
        )
    if section_key == "activity":
        if (
            inputs.current_operation is not None
            and inputs.current_operation.recent_activity
        ):
            return inputs.current_operation.recent_activity[-1]
        if inputs.current_operation is not None:
            return inputs.current_operation.summary
        return current_screen_message
    if section_key == "context":
        endpoint = (inputs.endpoint or "").strip()
        projection = (projection_view_id or "").strip()
        if endpoint and projection:
            return f"{endpoint} · {projection}"
        if endpoint:
            return endpoint
        if projection:
            return projection
        return inputs.namespace
    if section_key == "logs":
        log_lines = (
            inputs.local_node_runtime.recent_log_lines
            if inputs.local_node_runtime is not None
            else ()
        )
        count = len(log_lines)
        if count:
            noun = "line" if count == 1 else "lines"
            return f"{count} recent log {noun} available."
        return "No recent logs yet."
    return None


def resolved_pane_kind_for_section(
    *,
    section: InterfaceWindowLayoutSectionState,
    inputs: InterfaceHostLayoutInputs,
) -> str:
    contribution = _pane_contribution_for_section(
        inputs=inputs,
        section_key=section.section_key,
    )
    if contribution is not None:
        return contribution.pane_kind
    return _resolved_pane_kind(
        section.section_key,
        section.pane_key,
    )


def derive_resolved_pane_descriptors(
    *,
    inputs: InterfaceHostLayoutInputs,
    window_layout: InterfaceWindowLayoutState,
    active_focus: InterfaceRuntimeFocusState | None,
    section_state_addresses: (
        dict[str, InterfaceResolvedSectionStateAddress] | None
    ) = None,
) -> tuple[InterfaceResolvedPaneDescriptor, ...]:
    projection_view_id_fallback = (
        inputs.runtime_state.resolved_view.projection_view_id
        if inputs.runtime_state.resolved_view is not None
        else None
    )
    panes = resolve_bundle_backed_pane_descriptors(
        window_layout=window_layout,
        interface_config_bundle=inputs.interface_config_bundle,
        active_focus=active_focus,
        projection_view_id_fallback=projection_view_id_fallback,
        section_state_addresses=section_state_addresses,
        default_pane_kind=lambda section: resolved_pane_kind_for_section(
            section=section,
            inputs=inputs,
        ),
        state_source_kind_for_section=lambda section_key: resolved_pane_state_source_kind_for_inputs(
            section_key=section_key,
            inputs=inputs,
        ),
        summary_for_section=lambda section_key, projection_view_id: resolved_pane_summary(
            section_key=section_key,
            projection_view_id=projection_view_id,
            inputs=inputs,
        ),
        action_keys_for_section=lambda section_key: resolved_pane_action_keys(
            section_key=section_key,
            inputs=inputs,
        ),
    )
    return tuple(
        _pane_with_thread_layout_section_mapping(
            pane=pane,
            navigation_context_layout_target=inputs.navigation_context_layout_target,
        )
        for pane in panes
    )


def _pane_with_thread_layout_section_mapping(
    *,
    pane: InterfaceResolvedPaneDescriptor,
    navigation_context_layout_target: (
        InterfaceNavigationContextLayoutTargetState | None
    ),
) -> InterfaceResolvedPaneDescriptor:
    if pane.object_projection_graph_observable_id is None:
        return pane
    mapping = _thread_layout_section_mapping(
        navigation_context_layout_target=navigation_context_layout_target,
        section_key=pane.section_key,
        observable_id=pane.object_projection_graph_observable_id,
        view_ref=pane.view_ref,
    )
    section_graph_binding_key = (
        pane.section_graph_binding_key
        or _mapping_optional_text(
            mapping,
            "section_graph_binding_key",
        )
    )
    view_ref = pane.view_ref or _mapping_optional_text(mapping, "view_ref")
    if (
        section_graph_binding_key == pane.section_graph_binding_key
        and view_ref == pane.view_ref
    ):
        return pane
    return replace(
        pane,
        section_graph_binding_key=section_graph_binding_key,
        view_ref=view_ref,
    )


def _thread_layout_section_mapping(
    *,
    navigation_context_layout_target: (
        InterfaceNavigationContextLayoutTargetState | None
    ),
    section_key: str,
    observable_id: UUID,
    view_ref: str | None,
) -> dict[str, object] | None:
    if navigation_context_layout_target is None:
        return None
    evidence = (
        navigation_context_layout_target.evidence
        if isinstance(navigation_context_layout_target.evidence, Mapping)
        else {}
    )
    for mapping in evidence.get("sections", ()) or ():
        if not isinstance(mapping, Mapping):
            continue
        mapped_section_key = _mapping_optional_text(mapping, "section_key")
        if mapped_section_key is not None and not _text_matches(
            mapped_section_key,
            section_key,
        ):
            continue
        mapped_observable_id = _mapping_uuid(mapping, "observable_id")
        if mapped_observable_id is not None and mapped_observable_id != observable_id:
            continue
        mapped_view_ref = _mapping_optional_text(mapping, "view_ref")
        if (
            view_ref is not None
            and mapped_view_ref is not None
            and not _text_matches(mapped_view_ref, view_ref)
        ):
            continue
        return dict(mapping)
    return None


def _mapping_optional_text(
    mapping: Mapping[str, object] | None,
    key: str,
) -> str | None:
    if mapping is None:
        return None
    value = mapping.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _mapping_uuid(
    mapping: Mapping[str, object] | None,
    key: str,
) -> UUID | None:
    value = mapping.get(key) if mapping is not None else None
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (AttributeError, TypeError, ValueError):
        return None


def _text_matches(left: object, right: object) -> bool:
    left_text = str(left).strip().casefold()
    right_text = str(right).strip().casefold()
    return bool(left_text) and bool(right_text) and left_text == right_text


def resolve_active_runtime_focus(
    *,
    window_layout: InterfaceWindowLayoutState | None,
    focus_targets: tuple[InterfaceRuntimeFocusTarget, ...],
    section_state_addresses: (
        dict[str, InterfaceResolvedSectionStateAddress] | None
    ) = None,
    preferred_section_key: str | None = None,
    preferred_observable_id: UUID | None = None,
) -> InterfaceRuntimeFocusState | None:
    if window_layout is None:
        return None
    layout_focus_targets = tuple(
        item
        for item in focus_targets
        if item.layout_config_id == window_layout.layout_config_id
        or item.layout_key.casefold() == window_layout.layout_key.casefold()
    )
    target = next(
        (
            item
            for item in layout_focus_targets
            if preferred_observable_id is not None
            and item.observable_id == preferred_observable_id
            and (
                preferred_section_key is None
                or (
                    item.section_key is not None
                    and item.section_key.strip().casefold()
                    == preferred_section_key.strip().casefold()
                )
            )
        ),
        None,
    ) or next(iter(layout_focus_targets), None)
    section_key = preferred_section_key or (
        target.section_key if target is not None else None
    )
    section = None
    if section_key is not None:
        section = next(
            (
                item
                for item in window_layout.sections
                if item.section_key.strip().casefold() == section_key.strip().casefold()
            ),
            None,
        )
        if section is None:
            section_key = None
    address = (
        section_state_addresses.get(section_key)
        if section_key is not None and section_state_addresses is not None
        else None
    )
    if target is None and section is None and address is None:
        return InterfaceRuntimeFocusState(
            layout_config_id=window_layout.layout_config_id,
            layout_key=window_layout.layout_key,
        )
    return InterfaceRuntimeFocusState(
        layout_config_id=window_layout.layout_config_id,
        layout_key=window_layout.layout_key,
        section_key=section_key,
        layout_config_section_config_id=(
            section.layout_config_section_config_id
            if section is not None
            else target.layout_config_section_config_id if target is not None else None
        ),
        layout_section_id=address.layout_section_id if address is not None else None,
        section_focus_scope_id=(
            address.section_focus_scope_id if address is not None else None
        ),
        focus_scope_id=address.focus_scope_id if address is not None else None,
        focus_id=address.focus_id if address is not None else None,
        observable_id=(
            address.observable_id
            if address is not None and address.observable_id is not None
            else target.observable_id if target is not None else None
        ),
        focus_target=address.focus_target if address is not None else None,
    )


def attention_owned_runtime_focus(
    *,
    window_layout: InterfaceWindowLayoutState | None,
    section_state_addresses: dict[str, InterfaceResolvedSectionStateAddress] | None,
    active_section_key: str | None,
    active_observable_id: UUID | None,
) -> InterfaceRuntimeFocusState | None:
    if window_layout is None:
        return None
    normalized_section_key = (
        active_section_key.strip().casefold()
        if active_section_key is not None and active_section_key.strip()
        else None
    )
    section = (
        next(
            (
                item
                for item in window_layout.sections
                if normalized_section_key is not None
                and item.section_key.strip().casefold() == normalized_section_key
            ),
            None,
        )
        if normalized_section_key is not None
        else None
    )
    section_key = section.section_key if section is not None else None
    address = (
        section_state_addresses.get(section_key)
        if section_key is not None and section_state_addresses is not None
        else None
    )
    if section is None and address is None and active_observable_id is None:
        return InterfaceRuntimeFocusState(
            layout_config_id=window_layout.layout_config_id,
            layout_key=window_layout.layout_key,
        )
    return InterfaceRuntimeFocusState(
        layout_config_id=window_layout.layout_config_id,
        layout_key=window_layout.layout_key,
        section_key=section_key,
        layout_config_section_config_id=(
            section.layout_config_section_config_id if section is not None else None
        ),
        layout_section_id=address.layout_section_id if address is not None else None,
        section_focus_scope_id=(
            address.section_focus_scope_id if address is not None else None
        ),
        focus_scope_id=address.focus_scope_id if address is not None else None,
        focus_id=address.focus_id if address is not None else None,
        observable_id=(
            address.observable_id
            if address is not None and address.observable_id is not None
            else active_observable_id
        ),
        focus_target=address.focus_target if address is not None else None,
    )


def _uuid_or_none(value: UUID | str | None) -> UUID | None:
    if value is None or isinstance(value, UUID):
        return value
    normalized = str(value).strip()
    if not normalized:
        return None
    return UUID(normalized)


def fallback_section_state_addresses(
    *,
    window_layout: InterfaceWindowLayoutState,
    current_screen: InterfaceHostServiceCurrentScreen | None,
    lane_sync_state: InterfaceHostServiceLaneSyncState | None,
    section_keys: frozenset[str] | None = None,
) -> dict[str, InterfaceResolvedSectionStateAddress]:
    focus_scope_id = (
        current_screen.focus_scope_id
        if current_screen is not None and current_screen.focus_scope_id is not None
        else _uuid_or_none(
            lane_sync_state.lane_id if lane_sync_state is not None else None
        )
    )
    branch_id = (
        current_screen.branch_id
        if current_screen is not None and current_screen.branch_id is not None
        else lane_sync_state.branch_id if lane_sync_state is not None else None
    )
    focus_id = (
        current_screen.focus_id
        if current_screen is not None and current_screen.focus_id is not None
        else None
    )
    state_projection_hash = (
        lane_sync_state.projection_hash if lane_sync_state is not None else None
    )
    if (
        focus_scope_id is None
        and focus_id is None
        and branch_id is None
        and (state_projection_hash is None or not state_projection_hash.strip())
    ):
        return {}
    return {
        section.section_key: InterfaceResolvedSectionStateAddress(
            section_key=section.section_key,
            focus_scope_id=focus_scope_id,
            focus_id=focus_id,
            branch_id=branch_id,
            state_projection_hash=state_projection_hash,
        )
        for section in window_layout.sections
        if section.is_visible
        and (section_keys is None or section.section_key in section_keys)
    }


def merge_section_state_addresses(
    *,
    base: Mapping[str, InterfaceResolvedSectionStateAddress] | None,
    overlay: Mapping[str, InterfaceResolvedSectionStateAddress] | None,
) -> dict[str, InterfaceResolvedSectionStateAddress]:
    addresses = dict(base or {})
    for section_key, overlay_address in (overlay or {}).items():
        current = addresses.get(section_key)
        if current is None:
            addresses[section_key] = overlay_address
            continue
        overlay_projection_hash = (
            overlay_address.state_projection_hash.strip()
            if overlay_address.state_projection_hash is not None
            else ""
        )
        base_projection_hash = (
            current.state_projection_hash.strip()
            if current.state_projection_hash is not None
            else ""
        )
        addresses[section_key] = InterfaceResolvedSectionStateAddress(
            section_key=overlay_address.section_key,
            layout_section_id=(
                current.layout_section_id
                if current.layout_section_id is not None
                else overlay_address.layout_section_id
            ),
            section_focus_scope_id=(
                overlay_address.section_focus_scope_id
                if overlay_address.section_focus_scope_id is not None
                else current.section_focus_scope_id
            ),
            focus_scope_id=(
                overlay_address.focus_scope_id
                if overlay_address.focus_scope_id is not None
                else current.focus_scope_id
            ),
            focus_id=(
                overlay_address.focus_id
                if overlay_address.focus_id is not None
                else current.focus_id
            ),
            observable_id=(
                overlay_address.observable_id
                if overlay_address.observable_id is not None
                else current.observable_id
            ),
            branch_id=(
                current.branch_id
                if current.branch_id is not None
                else overlay_address.branch_id
            ),
            state_projection_hash=(
                base_projection_hash
                or overlay_projection_hash
                or current.state_projection_hash
                or overlay_address.state_projection_hash
            ),
            focus_target=(
                overlay_address.focus_target
                if overlay_address.focus_target is not None
                else current.focus_target
            ),
        )
    return addresses


async def resolve_section_state_addresses(
    *,
    window_layout: InterfaceWindowLayoutState,
    current_screen: InterfaceHostServiceCurrentScreen | None,
    lane_sync_state: InterfaceHostServiceLaneSyncState | None,
    section_keys: frozenset[str] | None = None,
    section_lane_resolver: (
        Callable[
            [str, str, str],
            "Awaitable[SectionFocusScopeLane]",
        ]
        | None
    ) = None,
) -> dict[str, InterfaceResolvedSectionStateAddress]:
    addresses = fallback_section_state_addresses(
        window_layout=window_layout,
        current_screen=current_screen,
        lane_sync_state=lane_sync_state,
        section_keys=section_keys,
    )
    if section_lane_resolver is None:
        return addresses
    for section in window_layout.sections:
        if not section.is_visible or (
            section_keys is not None and section.section_key not in section_keys
        ):
            continue
        try:
            lane = await section_lane_resolver(
                window_layout.window_key,
                window_layout.layout_key,
                section.section_key,
            )
        except Exception:
            continue
        addresses[section.section_key] = InterfaceResolvedSectionStateAddress(
            section_key=section.section_key,
            layout_section_id=lane.layout_section_id,
            section_focus_scope_id=lane.section_focus_scope_id,
            focus_scope_id=lane.focus_scope_id,
            branch_id=lane.branch_id,
            state_projection_hash=lane.projection_hash,
        )
    return addresses


__all__ = [
    "build_runtime_window_layout",
    "attention_owned_runtime_focus",
    "derive_runtime_focus_targets",
    "derive_runtime_layout_states",
    "derive_resolved_pane_descriptors",
    "fallback_section_state_addresses",
    "merge_section_state_addresses",
    "preferred_runtime_focus_section",
    "resolve_active_runtime_focus",
    "resolved_pane_action_keys",
    "resolved_pane_state_source_kind",
    "resolved_pane_summary",
    "resolve_section_state_addresses",
]
