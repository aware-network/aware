from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from uuid import UUID

from aware_interface.lifecycle.models import (
    InterfaceRuntimeFocusState,
    InterfaceResolvedPaneActionTarget,
    InterfaceResolvedPaneDescriptor,
    InterfaceResolvedSectionStateAddress,
    InterfaceWindowLayoutSectionState,
    InterfaceWindowLayoutState,
)
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
)


@dataclass(frozen=True, slots=True)
class _BundlePaneMount:
    pane_config_id: UUID
    pane_package_id: UUID | None
    pane_package_name: str | None
    pane_kind: str
    object_projection_graph_observable_id: UUID | None
    projection_experience_graph_identity_id: UUID | None
    object_projection_graph_identity_id: UUID | None
    section_graph_binding_key: str | None
    projection_experience_view_id: UUID | None
    state_model_id: UUID | None
    view_ref: str
    projection_view_key: str | None
    title: str | None
    summary: str | None
    narrative_key: str | None
    projection_view_id: str | None
    view_action_keys: tuple[str, ...]
    view_action_targets: tuple[InterfaceResolvedPaneActionTarget, ...]


_SECTION_SOURCE_KINDS_THAT_OVERRIDE_BUNDLE_VIEW_STATE = {
    "allowed_actions",
    "control_plane_workspace",
    "current_operation",
    "current_screen",
    "host_pane_contribution",
    "local_node_runtime_logs",
}


def resolve_bundle_backed_pane_descriptors(
    *,
    window_layout: InterfaceWindowLayoutState | None,
    interface_config_bundle: InterfaceConfigBundle | None,
    active_focus: InterfaceRuntimeFocusState | None = None,
    projection_view_id_fallback: str | None,
    section_state_addresses: dict[str, InterfaceResolvedSectionStateAddress] | None,
    default_pane_kind: Callable[[InterfaceWindowLayoutSectionState], str],
    state_source_kind_for_section: Callable[[str], str],
    summary_for_section: Callable[[str, str | None], str | None],
    action_keys_for_section: Callable[[str], tuple[str, ...]],
) -> tuple[InterfaceResolvedPaneDescriptor, ...]:
    if window_layout is None:
        return ()

    mounts_by_section_config_id = _bundle_mounts_by_section_config_id(
        interface_config_bundle
    )
    descriptors: list[InterfaceResolvedPaneDescriptor] = []
    for section in window_layout.sections:
        if not section.is_visible:
            continue
        section_state_address = (
            section_state_addresses.get(section.section_key)
            if section_state_addresses is not None
            else None
        )
        focus_target = (
            section_state_address.focus_target
            if section_state_address is not None
            else None
        )
        target_projection_experience_graph_identity_id = (
            focus_target.projection_experience_graph_identity_id
            if focus_target is not None
            else None
        )
        target_object_projection_graph_identity_id = (
            focus_target.object_projection_graph_identity_id
            if focus_target is not None
            else None
        )
        bundle_mounts = (
            mounts_by_section_config_id.get(section.layout_config_section_config_id)
            if section.layout_config_section_config_id is not None
            else ()
        )
        active_observable_id = (
            active_focus.observable_id if active_focus is not None else None
        )
        bundle_mount = _select_bundle_mount_for_section(
            section_key=section.section_key,
            bundle_mounts=bundle_mounts or (),
            active_observable_id=active_observable_id,
        )
        if bundle_mount is None:
            projection_view_id = (
                section.projection_view_id or projection_view_id_fallback
            )
            section_summary = summary_for_section(
                section.section_key, projection_view_id
            )
            descriptors.append(
                InterfaceResolvedPaneDescriptor(
                    window_key=window_layout.window_key,
                    layout_key=window_layout.layout_key,
                    section_key=section.section_key,
                    layout_config_section_config_id=section.layout_config_section_config_id,
                    layout_section_id=(
                        section_state_address.layout_section_id
                        if section_state_address is not None
                        else None
                    ),
                    section_focus_scope_id=(
                        section_state_address.section_focus_scope_id
                        if section_state_address is not None
                        else None
                    ),
                    focus_scope_id=(
                        section_state_address.focus_scope_id
                        if section_state_address is not None
                        else None
                    ),
                    branch_id=(
                        section_state_address.branch_id
                        if section_state_address is not None
                        else None
                    ),
                    focus_id=(
                        section_state_address.focus_id
                        if section_state_address is not None
                        else None
                    ),
                    focus_target=focus_target,
                    pane_kind=default_pane_kind(section),
                    pane_config_id=None,
                    pane_package_id=None,
                    pane_package_name=None,
                    object_projection_graph_observable_id=None,
                    projection_experience_graph_identity_id=(
                        target_projection_experience_graph_identity_id
                    ),
                    object_projection_graph_identity_id=(
                        target_object_projection_graph_identity_id
                    ),
                    section_graph_binding_key=None,
                    projection_experience_view_id=None,
                    projection_view_id=projection_view_id,
                    view_ref=None,
                    projection_view_key=None,
                    state_model_id=None,
                    title=section.title,
                    summary=section_summary,
                    narrative_key=f"{window_layout.layout_key}.{section.section_key}",
                    state_source_kind=state_source_kind_for_section(
                        section.section_key
                    ),
                    state_projection_hash=(
                        section_state_address.state_projection_hash
                        if section_state_address is not None
                        else None
                    ),
                    action_keys=action_keys_for_section(section.section_key),
                )
            )
            continue

        projection_view_id = (
            bundle_mount.projection_view_id
            if bundle_mount.projection_view_id is not None
            else section.projection_view_id or projection_view_id_fallback
        )
        section_summary = summary_for_section(section.section_key, projection_view_id)
        section_source_kind = state_source_kind_for_section(section.section_key)
        descriptors.append(
            InterfaceResolvedPaneDescriptor(
                window_key=window_layout.window_key,
                layout_key=window_layout.layout_key,
                section_key=section.section_key,
                layout_config_section_config_id=section.layout_config_section_config_id,
                layout_section_id=(
                    section_state_address.layout_section_id
                    if section_state_address is not None
                    else None
                ),
                section_focus_scope_id=(
                    section_state_address.section_focus_scope_id
                    if section_state_address is not None
                    else None
                ),
                focus_scope_id=(
                    section_state_address.focus_scope_id
                    if section_state_address is not None
                    else None
                ),
                branch_id=(
                    section_state_address.branch_id
                    if section_state_address is not None
                    else None
                ),
                focus_id=(
                    section_state_address.focus_id
                    if section_state_address is not None
                    else None
                ),
                focus_target=focus_target,
                pane_kind=bundle_mount.pane_kind,
                pane_config_id=bundle_mount.pane_config_id,
                pane_package_id=bundle_mount.pane_package_id,
                pane_package_name=bundle_mount.pane_package_name,
                object_projection_graph_observable_id=bundle_mount.object_projection_graph_observable_id,
                projection_experience_graph_identity_id=(
                    bundle_mount.projection_experience_graph_identity_id
                    or target_projection_experience_graph_identity_id
                ),
                object_projection_graph_identity_id=(
                    bundle_mount.object_projection_graph_identity_id
                    or target_object_projection_graph_identity_id
                ),
                section_graph_binding_key=bundle_mount.section_graph_binding_key,
                projection_experience_view_id=bundle_mount.projection_experience_view_id,
                projection_view_id=projection_view_id,
                view_ref=bundle_mount.view_ref,
                projection_view_key=bundle_mount.projection_view_key,
                state_model_id=bundle_mount.state_model_id,
                title=section.title or bundle_mount.title,
                summary=section_summary or bundle_mount.summary,
                narrative_key=(
                    bundle_mount.narrative_key
                    or f"{window_layout.layout_key}.{section.section_key}"
                ),
                state_source_kind=_bundle_mount_state_source_kind(
                    bundle_mount=bundle_mount,
                    section_source_kind=section_source_kind,
                ),
                state_projection_hash=(
                    section_state_address.state_projection_hash
                    if section_state_address is not None
                    else None
                ),
                action_keys=_dedupe_action_keys(
                    (
                        *action_keys_for_section(section.section_key),
                        *bundle_mount.view_action_keys,
                    )
                ),
                action_targets=bundle_mount.view_action_targets,
            )
        )
    return tuple(descriptors)


def _bundle_mounts_by_section_config_id(
    interface_config_bundle: InterfaceConfigBundle | None,
) -> dict[UUID, tuple[_BundlePaneMount, ...]]:
    if interface_config_bundle is None:
        return {}

    mounts_by_section_config_id: dict[UUID, list[_BundlePaneMount]] = {}
    for pane_config in interface_config_bundle.pane_configs:
        for projection_view in pane_config.projection_experience_views:
            view_action_keys = _dedupe_action_keys(
                action.action_key for action in projection_view.invocation_actions
            )
            view_action_targets = tuple(
                InterfaceResolvedPaneActionTarget(
                    action_key=action.action_key,
                    action_kind=action.action_kind,
                    target_ref=action.target_ref,
                    view_invocation_action_config_id=getattr(
                        action,
                        "view_invocation_action_config_id",
                        None,
                    )
                    or getattr(
                        action,
                        "projection_experience_view_invocation_action_id",
                        None,
                    ),
                    label=action.label,
                    receipt_policy=action.receipt_policy,
                )
                for action in projection_view.invocation_actions
            )
            for mount in projection_view.section_mounts:
                mounts = mounts_by_section_config_id.setdefault(
                    mount.layout_config_section_config_id,
                    [],
                )
                mounts.append(
                    _BundlePaneMount(
                        pane_config_id=pane_config.pane_config_id,
                        pane_package_id=pane_config.pane_package_id,
                        pane_package_name=pane_config.pane_package_name,
                        pane_kind=pane_config.pane_kind,
                        object_projection_graph_observable_id=projection_view.object_projection_graph_observable_id,
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
                        section_graph_binding_key=getattr(
                            projection_view,
                            "section_graph_binding_key",
                            None,
                        ),
                        projection_experience_view_id=projection_view.projection_experience_view_id,
                        state_model_id=projection_view.state_model_id,
                        view_ref=projection_view.view_ref,
                        projection_view_key=projection_view.projection_view_key,
                        title=pane_config.name,
                        summary=pane_config.description,
                        narrative_key=pane_config.narrative_key,
                        projection_view_id=str(
                            projection_view.projection_experience_view_id
                        ),
                        view_action_keys=view_action_keys,
                        view_action_targets=view_action_targets,
                    )
                )
    return {
        section_config_id: tuple(mounts)
        for section_config_id, mounts in mounts_by_section_config_id.items()
    }


def _bundle_mount_state_source_kind(
    *,
    bundle_mount: _BundlePaneMount,
    section_source_kind: str,
) -> str:
    normalized_source_kind = (section_source_kind or "").strip()
    if normalized_source_kind in _SECTION_SOURCE_KINDS_THAT_OVERRIDE_BUNDLE_VIEW_STATE:
        return normalized_source_kind
    if bundle_mount.state_model_id is not None and bundle_mount.view_ref.strip():
        return "experience_view_state"
    return normalized_source_kind or "unknown"


def _select_bundle_mount_for_section(
    *,
    section_key: str,
    bundle_mounts: tuple[_BundlePaneMount, ...],
    active_observable_id: UUID | None,
) -> _BundlePaneMount | None:
    if not bundle_mounts:
        return None

    if active_observable_id is not None:
        observable_mounts = tuple(
            mount
            for mount in bundle_mounts
            if mount.object_projection_graph_observable_id == active_observable_id
        )
        if observable_mounts:
            if len(observable_mounts) != 1:
                raise ValueError(
                    "Interface section resolved multiple `observable -> experience view -> pane` "
                    + f"bindings for active observable {active_observable_id} in section {section_key!r}: "
                    + ", ".join(
                        f"{mount.view_ref!r}->{mount.pane_kind!r}"
                        for mount in observable_mounts
                    )
                )
            return observable_mounts[0]

    if len(bundle_mounts) == 1:
        return bundle_mounts[0]

    return None


def _dedupe_action_keys(action_keys: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    deduped: list[str] = []
    for action_key in action_keys:
        normalized = (action_key or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return tuple(deduped)


__all__ = ["resolve_bundle_backed_pane_descriptors"]
