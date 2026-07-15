from __future__ import annotations

from aware_interface import (
    InterfaceHostCapabilityOperation,
    InterfaceHostCapabilityTarget,
)
from aware_interface.host_capabilities import (
    InterfaceHostCapabilityAction,
    InterfaceHostCapabilitySnapshot,
    InterfaceHostPaneContribution,
)
from aware_interface_service.host.capabilities.identity import (
    CONTROL_IDENTITY_ADMISSION_SCREEN_KEY,
    build_identity_capability_snapshot,
)
from aware_interface_service.host.capabilities.interface_admission import (
    INTERFACE_ADMISSION_SCREEN_KEY,
    build_interface_admission_capability_snapshot,
)
from aware_interface_service.host.capabilities.local_runtime import (
    build_local_node_runtime_capability_snapshot,
    build_local_service_host_capability_snapshot,
)
from aware_interface_service.host.state import (
    CONSUMER_REMOTE_ADMISSION_PROFILE_ID,
    OPERATOR_LOCAL_BOOTSTRAP_PROFILE_ID,
    InterfaceHostProductInputs,
    InterfaceHostProductState,
    active_control_plane_profile_id,
    consumer_profile_active,
    normalize_selected_step_id,
)
from aware_interface_service.models import (
    InterfaceHostServiceAllowedAction,
    InterfaceHostServiceControlPlaneOrchestrationStep,
    InterfaceHostServiceControlPlaneProfileState,
    InterfaceHostServiceControlPlaneProfilesState,
    InterfaceHostServiceControlPlaneTraceEntry,
    InterfaceHostServiceControlPlaneTraceGroup,
    InterfaceHostServiceControlPlaneWorkspaceState,
    InterfaceHostServiceCurrentScreen,
    InterfaceHostServiceOperationState,
    InterfaceHostServiceOperationTargetState,
)


def _preview_trace_entries(
    entries: tuple[InterfaceHostServiceControlPlaneTraceEntry, ...],
    *,
    max_entries: int = 4,
) -> tuple[InterfaceHostServiceControlPlaneTraceEntry, ...]:
    if len(entries) <= max_entries:
        return entries
    return entries[-max_entries:]


def _fallback_trace_entries_for_target(
    target: InterfaceHostCapabilityTarget,
) -> tuple[InterfaceHostServiceControlPlaneTraceEntry, ...]:
    lines = tuple(line.strip() for line in target.detail_lines if line.strip())
    if lines:
        return tuple(
            InterfaceHostServiceControlPlaneTraceEntry(
                step_id=target.target_id,
                source_key=target.target_id,
                source_label=target.display_name,
                message=line,
            )
            for line in lines[-4:]
        )
    message = (
        target.error
        or target.summary
        or (
            "Ready."
            if target.is_active and target.is_healthy
            else "No trace activity reported yet."
        )
    )
    return (
        InterfaceHostServiceControlPlaneTraceEntry(
            step_id=target.target_id,
            source_key=target.target_id,
            source_label=target.display_name,
            message=message,
        ),
    )


def _current_screen_from_capability(
    *,
    screen_key: str,
    source_kind: str,
    screen_kind: str,
    title: str | None,
    message: str | None,
    projection_view_id: str | None,
    pane_key: str | None,
) -> InterfaceHostServiceCurrentScreen:
    return InterfaceHostServiceCurrentScreen(
        screen_kind=screen_kind,
        screen_key=screen_key,
        source_kind=source_kind,
        title=title,
        message=message,
        projection_view_id=projection_view_id,
        pane_key=pane_key,
    )


def _allowed_action_from_capability(
    action_key: str,
    *,
    label: str,
    enabled: bool,
    reason: str | None,
    payload_schema_hint: str | None,
) -> InterfaceHostServiceAllowedAction:
    return InterfaceHostServiceAllowedAction(
        action_key=action_key,
        label=label,
        enabled=enabled,
        reason=reason,
        payload_schema_hint=payload_schema_hint,
    )


def _normalized_pane_key(value: str | None, *, fallback: str) -> str:
    normalized = (value or "").strip()
    if normalized:
        return normalized
    return fallback


def _pane_contributions_from_capability(
    snapshot: InterfaceHostCapabilitySnapshot,
) -> tuple[InterfaceHostPaneContribution, ...]:
    if snapshot.pane_contributions:
        return snapshot.pane_contributions
    screen = snapshot.screen
    if screen is None:
        return ()
    pane_key = _normalized_pane_key(
        screen.pane_key,
        fallback=screen.screen_key,
    )
    operation = snapshot.operation
    status = operation.status if operation is not None else None
    readiness_reason = (
        operation.error
        if operation is not None and operation.error is not None
        else screen.message
    )
    return (
        InterfaceHostPaneContribution(
            pane_key=pane_key,
            pane_kind=pane_key,
            section_key=pane_key,
            title=screen.title,
            summary=screen.message,
            status=status,
            readiness_reason=readiness_reason,
            narrative_key=f"bootstrap.{pane_key}",
            action_keys=tuple(action.action_key for action in snapshot.actions),
            machine_payload={
                "capability_id": snapshot.capability_id,
                "capability_kind": snapshot.kind,
                "screen_key": screen.screen_key,
                "source_kind": screen.source_kind,
            },
        ),
    )


def _dedupe_pane_contributions(
    contributions: tuple[InterfaceHostPaneContribution, ...],
) -> tuple[InterfaceHostPaneContribution, ...]:
    seen: set[tuple[str, str]] = set()
    deduped: list[InterfaceHostPaneContribution] = []
    for contribution in contributions:
        key = (
            contribution.section_key.strip().casefold(),
            contribution.pane_key.strip().casefold(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(contribution)
    return tuple(deduped)


def _allowed_actions_from_contributions(
    *,
    contributions: tuple[InterfaceHostPaneContribution, ...],
    snapshots: tuple[InterfaceHostCapabilitySnapshot, ...],
) -> tuple[InterfaceHostServiceAllowedAction, ...]:
    action_keys = {
        action_key
        for contribution in contributions
        for action_key in contribution.action_keys
    }
    actions_by_key: dict[str, InterfaceHostCapabilityAction] = {}
    for snapshot in snapshots:
        for action in snapshot.actions:
            if (
                action.action_key in action_keys
                and action.action_key not in actions_by_key
            ):
                actions_by_key[action.action_key] = action
    return tuple(
        _allowed_action_from_capability(
            action.action_key,
            label=action.label,
            enabled=action.enabled,
            reason=action.reason,
            payload_schema_hint=action.payload_schema_hint,
        )
        for action in actions_by_key.values()
    )


def _allowed_actions_from_snapshot(
    snapshot: InterfaceHostCapabilitySnapshot | None,
) -> tuple[InterfaceHostServiceAllowedAction, ...]:
    if snapshot is None:
        return ()
    return tuple(
        _allowed_action_from_capability(
            action.action_key,
            label=action.label,
            enabled=action.enabled,
            reason=action.reason,
            payload_schema_hint=action.payload_schema_hint,
        )
        for action in snapshot.actions
    )


def _merge_allowed_actions(
    *action_sets: tuple[InterfaceHostServiceAllowedAction, ...],
) -> tuple[InterfaceHostServiceAllowedAction, ...]:
    merged: list[InterfaceHostServiceAllowedAction] = []
    seen: set[str] = set()
    for action_set in action_sets:
        for action in action_set:
            if action.action_key in seen:
                continue
            seen.add(action.action_key)
            merged.append(action)
    return tuple(merged)


def _operation_target_from_capability(
    target: InterfaceHostCapabilityTarget,
) -> InterfaceHostServiceOperationTargetState:
    return InterfaceHostServiceOperationTargetState(
        target_id=target.target_id,
        display_name=target.display_name,
        kind=target.kind,
        phase=target.phase,
        is_active=target.is_active,
        is_healthy=target.is_healthy,
        summary=target.summary,
        error=target.error,
        detail_lines=target.detail_lines,
    )


def _operation_from_capability(
    operation: InterfaceHostCapabilityOperation,
) -> InterfaceHostServiceOperationState:
    return InterfaceHostServiceOperationState(
        operation_key=operation.capability_id,
        title=operation.title,
        status=operation.status,
        phase=operation.phase,
        current_target_id=operation.current_target_id,
        current_target_title=operation.current_target_title,
        summary=operation.summary,
        error=operation.error,
        running=operation.running,
        retryable=operation.retryable,
        updated_at=operation.updated_at,
        recent_activity=operation.recent_activity,
        target_statuses=tuple(
            _operation_target_from_capability(target) for target in operation.targets
        ),
    )


def derive_control_plane_profiles_state(
    *,
    active_profile_id: str,
    current_screen: InterfaceHostServiceCurrentScreen | None,
) -> InterfaceHostServiceControlPlaneProfilesState:
    resolved_profile_id = active_control_plane_profile_id(active_profile_id)
    current_gate_key = current_screen.screen_key if current_screen is not None else None
    profiles = (
        InterfaceHostServiceControlPlaneProfileState(
            profile_id=OPERATOR_LOCAL_BOOTSTRAP_PROFILE_ID,
            title="Operator Bootstrap",
            kind="operator",
            summary="Bootstrap and repair local node capability rails from the Interface control plane.",
            selected=resolved_profile_id == OPERATOR_LOCAL_BOOTSTRAP_PROFILE_ID,
            gate_keys=(
                "local_service_host_gate",
                "local_node_runtime_gate",
                CONTROL_IDENTITY_ADMISSION_SCREEN_KEY,
            ),
            current_gate_key=(
                current_gate_key
                if resolved_profile_id == OPERATOR_LOCAL_BOOTSTRAP_PROFILE_ID
                else None
            ),
        ),
        InterfaceHostServiceControlPlaneProfileState(
            profile_id=CONSUMER_REMOTE_ADMISSION_PROFILE_ID,
            title="Consumer Admission",
            kind="consumer",
            summary=(
                "Attach to remote Identity, Economy, and API capability rails "
                "without local bootstrap being a hard prerequisite."
            ),
            selected=resolved_profile_id == CONSUMER_REMOTE_ADMISSION_PROFILE_ID,
            gate_keys=(
                INTERFACE_ADMISSION_SCREEN_KEY,
                CONTROL_IDENTITY_ADMISSION_SCREEN_KEY,
            ),
            current_gate_key=(
                current_gate_key
                if resolved_profile_id == CONSUMER_REMOTE_ADMISSION_PROFILE_ID
                and current_gate_key
                in {
                    INTERFACE_ADMISSION_SCREEN_KEY,
                    CONTROL_IDENTITY_ADMISSION_SCREEN_KEY,
                }
                else None
            ),
        ),
    )
    return InterfaceHostServiceControlPlaneProfilesState(
        active_profile_id=resolved_profile_id,
        profiles=profiles,
    )


def derive_control_plane_workspace(
    *,
    operation: InterfaceHostCapabilityOperation | None,
    selected_step_id: str | None,
    selected_step_explicit: bool,
) -> tuple[InterfaceHostServiceControlPlaneWorkspaceState | None, str | None]:
    if operation is None or not operation.targets:
        return None, None

    step_titles = {item.target_id: item.display_name for item in operation.targets}
    current_step_id = operation.current_target_id
    requested_selection = normalize_selected_step_id(selected_step_id)
    fallback_selected = (
        current_step_id or requested_selection or operation.targets[0].target_id
    )
    if selected_step_explicit and requested_selection in step_titles:
        resolved_selected_step_id = requested_selection
    else:
        resolved_selected_step_id = (
            fallback_selected
            if fallback_selected in step_titles
            else operation.targets[0].target_id
        )

    groups: list[InterfaceHostServiceControlPlaneTraceGroup] = []
    steps: list[InterfaceHostServiceControlPlaneOrchestrationStep] = []
    for target in operation.targets:
        entries = tuple(
            InterfaceHostServiceControlPlaneTraceEntry(
                step_id=target.target_id,
                source_key=trace.source_key,
                source_label=trace.source_label,
                message=trace.message,
                step_label=trace.step_label,
            )
            for trace in target.trace_preview
        )
        if not entries:
            entries = _fallback_trace_entries_for_target(target)
        preview = _preview_trace_entries(entries)
        groups.append(
            InterfaceHostServiceControlPlaneTraceGroup(
                step_id=target.target_id,
                step_title=target.display_name,
                status=target.status,
                current=target.target_id == current_step_id,
                selected=target.target_id == resolved_selected_step_id,
                entries=preview,
            )
        )
        steps.append(
            InterfaceHostServiceControlPlaneOrchestrationStep(
                step_id=target.target_id,
                title=target.display_name,
                kind=target.kind,
                status=target.status,
                phase=target.phase,
                summary=target.error or target.summary,
                current=target.target_id == current_step_id,
                selected=target.target_id == resolved_selected_step_id,
                trace_preview=preview,
            )
        )

    return (
        InterfaceHostServiceControlPlaneWorkspaceState(
            selected_step_id=resolved_selected_step_id,
            current_step_id=current_step_id,
            orchestration_steps=tuple(steps),
            grouped_trace_preview=tuple(groups),
        ),
        resolved_selected_step_id,
    )


def compose_host_product(
    inputs: InterfaceHostProductInputs,
) -> InterfaceHostProductState:
    service_host_snapshot = build_local_service_host_capability_snapshot(
        operator_profile_active=active_control_plane_profile_id(
            inputs.active_profile_id
        )
        == OPERATOR_LOCAL_BOOTSTRAP_PROFILE_ID,
        local_service_host=inputs.local_service_host,
    )
    local_node_snapshot = build_local_node_runtime_capability_snapshot(
        operator_profile_active=active_control_plane_profile_id(
            inputs.active_profile_id
        )
        == OPERATOR_LOCAL_BOOTSTRAP_PROFILE_ID,
        local_service_host=inputs.local_service_host,
        local_node_runtime=inputs.local_node_runtime,
    )
    is_consumer_profile_active = consumer_profile_active(inputs.active_profile_id)
    interface_admission_snapshot = build_interface_admission_capability_snapshot(
        consumer_profile_active=is_consumer_profile_active,
        authenticated=inputs.authenticated,
        interface_admitted=inputs.interface_admitted,
        transport_bound=inputs.transport_bound,
    )
    identity_snapshot = build_identity_capability_snapshot(
        consumer_profile_active=(
            is_consumer_profile_active and interface_admission_snapshot is None
        ),
        authenticated=inputs.authenticated,
        transport_bound=inputs.transport_bound,
        local_service_host=inputs.local_service_host,
        local_node_runtime=inputs.local_node_runtime,
        admission_summary=inputs.identity_admission_summary,
        admission_error=inputs.identity_admission_error,
        admission_detail_lines=inputs.identity_admission_detail_lines,
        admission_recent_activity=inputs.identity_admission_recent_activity,
        admission_updated_at=inputs.identity_admission_updated_at,
    )
    screen_precedence = tuple(
        snapshot
        for snapshot in (
            service_host_snapshot,
            local_node_snapshot,
            interface_admission_snapshot,
            identity_snapshot,
        )
        if snapshot is not None
    )
    operation_precedence = tuple(
        snapshot
        for snapshot in (
            identity_snapshot,
            local_node_snapshot,
            service_host_snapshot,
        )
        if snapshot is not None
    )
    screen_snapshot = next(
        (item for item in screen_precedence if item.screen is not None),
        None,
    )
    action_snapshot = screen_snapshot or next(
        (item for item in screen_precedence if item.actions),
        None,
    )
    operation_snapshot = next(
        (item.operation for item in operation_precedence if item.operation is not None),
        None,
    )
    pane_contributions = _dedupe_pane_contributions(
        tuple(
            contribution
            for snapshot in ((screen_snapshot,) if screen_snapshot is not None else ())
            for contribution in _pane_contributions_from_capability(snapshot)
        )
    )
    current_screen = (
        _current_screen_from_capability(
            screen_key=screen_snapshot.screen.screen_key,
            source_kind=screen_snapshot.screen.source_kind,
            screen_kind=screen_snapshot.screen.screen_kind,
            title=screen_snapshot.screen.title,
            message=screen_snapshot.screen.message,
            projection_view_id=screen_snapshot.screen.projection_view_id,
            pane_key=screen_snapshot.screen.pane_key,
        )
        if screen_snapshot is not None and screen_snapshot.screen is not None
        else None
    )
    allowed_actions = _allowed_actions_from_contributions(
        contributions=pane_contributions,
        snapshots=screen_precedence,
    ) or (
        tuple(
            _allowed_action_from_capability(
                action.action_key,
                label=action.label,
                enabled=action.enabled,
                reason=action.reason,
                payload_schema_hint=action.payload_schema_hint,
            )
            for action in action_snapshot.actions
        )
        if action_snapshot is not None
        else ()
    )
    allowed_actions = _merge_allowed_actions(
        allowed_actions,
        _allowed_actions_from_snapshot(interface_admission_snapshot),
    )
    control_plane_workspace, resolved_selected_step_id = derive_control_plane_workspace(
        operation=operation_snapshot,
        selected_step_id=inputs.selected_step_id,
        selected_step_explicit=inputs.selected_step_explicit,
    )
    return InterfaceHostProductState(
        current_screen=current_screen,
        pane_contributions=pane_contributions,
        allowed_actions=allowed_actions,
        current_operation=(
            _operation_from_capability(operation_snapshot)
            if operation_snapshot is not None
            else None
        ),
        control_plane_profiles=derive_control_plane_profiles_state(
            active_profile_id=inputs.active_profile_id,
            current_screen=current_screen,
        ),
        control_plane_workspace=control_plane_workspace,
        selected_step_id=resolved_selected_step_id,
    )


__all__ = [
    "compose_host_product",
    "derive_control_plane_profiles_state",
    "derive_control_plane_workspace",
]
