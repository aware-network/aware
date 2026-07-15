from __future__ import annotations

from dataclasses import dataclass, replace
import re

from aware_interface import (
    InterfaceHostCapabilityAction,
    InterfaceHostCapabilityOperation,
    InterfaceHostCapabilityScreen,
    InterfaceHostCapabilitySnapshot,
    InterfaceHostCapabilityTarget,
    InterfaceHostCapabilityTraceEntry,
)
from aware_interface_service.models import (
    InterfaceHostServiceLocalNodeRuntimeState,
    InterfaceHostServiceLocalServiceHostState,
    InterfaceHostServiceOperationTargetState,
)


@dataclass(frozen=True, slots=True)
class _ParsedCapabilityTraceEntry:
    step_id: str | None
    entry: InterfaceHostCapabilityTraceEntry


def preview_lines(lines: tuple[str, ...], *, max_lines: int = 8) -> tuple[str, ...]:
    if len(lines) <= max_lines:
        return lines
    return lines[-max_lines:]


def resolve_current_node_target(
    node_runtime: InterfaceHostServiceLocalNodeRuntimeState,
) -> InterfaceHostServiceOperationTargetState | None:
    if not node_runtime.target_statuses:
        return None
    if node_runtime.active_target_id is not None:
        for item in node_runtime.target_statuses:
            if item.target_id == node_runtime.active_target_id:
                return item
    for item in node_runtime.target_statuses:
        if item.error:
            return item
    for item in node_runtime.target_statuses:
        if not (item.is_active and item.is_healthy):
            return item
    return node_runtime.target_statuses[-1]


def build_local_node_gate_message(
    node_runtime: InterfaceHostServiceLocalNodeRuntimeState,
) -> str:
    current_target = resolve_current_node_target(node_runtime)
    if current_target is not None:
        target_detail = current_target.error or current_target.summary
        if target_detail:
            return f"{current_target.display_name}: {target_detail}"
    return (
        node_runtime.error
        or node_runtime.summary
        or "Local Service host is ready. Start the local Node runtime to continue."
    )


def _phase_label(token: str) -> str:
    normalized = token.strip().replace("_", " ").replace("-", " ")
    if not normalized:
        return "Unknown"
    return " ".join(part.capitalize() for part in normalized.split())


def _step_status(target: InterfaceHostServiceOperationTargetState) -> str:
    if target.error:
        return "blocked"
    if target.is_active and target.is_healthy:
        return "ready"
    phase = target.phase.strip().lower()
    if phase in {"ready", "running", "starting_bundle", "starting_targets", "preparing_bundle"}:
        return "running"
    if target.summary or phase not in {"", "idle"}:
        return "waiting"
    return "idle"


def _parse_control_plane_trace_entry(
    raw: str,
    *,
    step_titles: dict[str, str],
) -> _ParsedCapabilityTraceEntry:
    trimmed = raw.strip()
    if not trimmed:
        return _ParsedCapabilityTraceEntry(
            step_id=None,
            entry=InterfaceHostCapabilityTraceEntry(
                source_key="interface",
                source_label="Interface",
                message="No detail reported yet.",
            ),
        )

    bracket_match = re.match(r"^\[([^\]]+)\]\s*(.*)$", trimmed)
    source_key = "interface"
    message = trimmed
    if bracket_match is not None:
        source_key = bracket_match.group(1).strip().lower()
        message = bracket_match.group(2).strip()

    step_label: str | None = None
    docker_step_match = re.match(r"^(#\d+)\s+(.*)$", message)
    if docker_step_match is not None:
        step_label = docker_step_match.group(1).strip()
        message = docker_step_match.group(2).strip()

    phase_match = re.search(r"\bphase=([a-zA-Z0-9_-]+)\b", message)
    if phase_match is not None and not step_label:
        step_label = _phase_label(phase_match.group(1))

    source_label = step_titles.get(source_key)
    if source_label is None:
        source_label = {
            "bundle": "Bundle",
            "environment": "Environment",
            "postgres": "Postgres",
            "node": "Node",
        }.get(source_key, _phase_label(source_key))

    return _ParsedCapabilityTraceEntry(
        step_id=source_key if source_key in step_titles else None,
        entry=InterfaceHostCapabilityTraceEntry(
            source_key=source_key,
            source_label=source_label,
            message=message,
            step_label=step_label,
        ),
    )


def _fallback_trace_entries_for_target(
    target: InterfaceHostServiceOperationTargetState,
) -> tuple[InterfaceHostCapabilityTraceEntry, ...]:
    lines = tuple(line.strip() for line in target.detail_lines if line.strip())
    if lines:
        return tuple(
            InterfaceHostCapabilityTraceEntry(
                source_key=target.target_id,
                source_label=target.display_name,
                message=line,
            )
            for line in preview_lines(lines, max_lines=4)
        )
    message = (
        target.error
        or target.summary
        or ("Ready." if target.is_active and target.is_healthy else "No trace activity reported yet.")
    )
    return (
        InterfaceHostCapabilityTraceEntry(
            source_key=target.target_id,
            source_label=target.display_name,
            message=message,
        ),
    )


def _target_trace_preview(
    *,
    node_runtime: InterfaceHostServiceLocalNodeRuntimeState,
    target_statuses: tuple[InterfaceHostServiceOperationTargetState, ...],
    current_target_id: str | None,
) -> dict[str, tuple[InterfaceHostCapabilityTraceEntry, ...]]:
    if not target_statuses:
        return {}

    step_titles = {item.target_id: item.display_name for item in target_statuses}
    grouped_entries: dict[str, list[InterfaceHostCapabilityTraceEntry]] = {
        item.target_id: []
        for item in target_statuses
    }
    default_step_id = (
        current_target_id if current_target_id in step_titles else target_statuses[0].target_id
    )
    parsed_entries = tuple(
        _parse_control_plane_trace_entry(line, step_titles=step_titles)
        for line in preview_lines(tuple(node_runtime.recent_log_lines), max_lines=24)
    )
    for parsed in parsed_entries:
        step_id = parsed.step_id if parsed.step_id in step_titles else default_step_id
        if step_id not in grouped_entries:
            continue
        grouped_entries[step_id].append(parsed.entry)

    resolved: dict[str, tuple[InterfaceHostCapabilityTraceEntry, ...]] = {}
    for target in target_statuses:
        entries = tuple(grouped_entries[target.target_id])
        resolved[target.target_id] = (
            entries if entries else _fallback_trace_entries_for_target(target)
        )
    return resolved


def build_local_service_host_capability_snapshot(
    *,
    operator_profile_active: bool,
    local_service_host: InterfaceHostServiceLocalServiceHostState | None,
) -> InterfaceHostCapabilitySnapshot | None:
    if (
        not operator_profile_active
        or local_service_host is None
        or not local_service_host.managed
        or local_service_host.ready
    ):
        return None

    status = (
        "succeeded"
        if local_service_host.ready
        else "failed"
        if local_service_host.error
        else "running"
        if local_service_host.status == "starting"
        else "waiting"
    )
    target = InterfaceHostCapabilityTarget(
        target_id="local_service_host",
        display_name="Local Service Host",
        kind="service_host",
        phase=local_service_host.status,
        status=status,
        is_active=local_service_host.status == "starting",
        is_healthy=local_service_host.ready,
        summary=local_service_host.error or "Service host bootstrap is required.",
        error=local_service_host.error,
        current=True,
        detail_lines=(
            local_service_host.recent_log_lines
            or (
                local_service_host.error
                or f"Local Service host status: {local_service_host.status}.",
            )
        ),
        trace_preview=(
            InterfaceHostCapabilityTraceEntry(
                source_key="local_service_host",
                source_label="Local Service Host",
                message=(
                    local_service_host.recent_log_lines[-1]
                    if local_service_host.recent_log_lines
                    else local_service_host.error
                    or f"Local Service host status: {local_service_host.status}."
                ),
            ),
        ),
    )
    return InterfaceHostCapabilitySnapshot(
        capability_id="local_service_host",
        kind="service_host",
        screen=InterfaceHostCapabilityScreen(
            screen_key="local_service_host_gate",
            source_kind="gate",
            title="Local Service Host Required",
            message=(
                local_service_host.error
                or "Start the local Service host so this Interface can manage localhost services."
            ),
            pane_key="local_service_host_gate",
        ),
        actions=(
            InterfaceHostCapabilityAction(
                action_key="ensure_local_service_host",
                label="Ensure Local Service Host",
                enabled=local_service_host.supported,
                reason=(
                    "Start or reconnect the same-machine Service host used by the local Interface."
                    if local_service_host.supported
                    else "Local Service host bootstrap is not supported on this platform."
                ),
            ),
            InterfaceHostCapabilityAction(
                action_key="restart_local_service_host",
                label="Restart Local Service Host",
                enabled=local_service_host.supported,
                reason=(
                    "Restart the same-machine Service host after upgrades or stale bootstrap state."
                    if local_service_host.supported
                    else "Local Service host bootstrap is not supported on this platform."
                ),
            ),
        ),
        operation=InterfaceHostCapabilityOperation(
            capability_id="local_service_host",
            title="Local Service Host",
            status=status,
            phase=local_service_host.status,
            current_target_id=target.target_id,
            current_target_title=target.display_name,
            summary=target.summary,
            error=target.error,
            running=status == "running",
            retryable=local_service_host.ready is False and local_service_host.supported,
            updated_at=local_service_host.last_checked_at,
            targets=(target,),
        ),
    )


def build_local_node_runtime_capability_snapshot(
    *,
    operator_profile_active: bool,
    local_service_host: InterfaceHostServiceLocalServiceHostState | None,
    local_node_runtime: InterfaceHostServiceLocalNodeRuntimeState | None,
) -> InterfaceHostCapabilitySnapshot | None:
    if (
        not operator_profile_active
        or local_service_host is None
        or not local_service_host.ready
        or local_node_runtime is None
        or not local_node_runtime.managed
    ):
        return None

    current_target = resolve_current_node_target(local_node_runtime)
    status = "idle"
    if local_node_runtime.ready:
        status = "succeeded"
    elif local_node_runtime.error:
        status = "failed"
    elif local_node_runtime.available or local_node_runtime.phase != "idle":
        status = "running"

    trace_preview = _target_trace_preview(
        node_runtime=local_node_runtime,
        target_statuses=local_node_runtime.target_statuses,
        current_target_id=current_target.target_id if current_target is not None else None,
    )
    targets = tuple(
        InterfaceHostCapabilityTarget(
            target_id=target.target_id,
            display_name=target.display_name,
            kind=target.kind,
            phase=target.phase,
            status=_step_status(target),
            is_active=target.is_active,
            is_healthy=target.is_healthy,
            summary=target.summary,
            error=target.error,
            current=target.target_id == (current_target.target_id if current_target is not None else None),
            detail_lines=target.detail_lines,
            trace_preview=trace_preview.get(target.target_id, ()),
        )
        for target in local_node_runtime.target_statuses
    )
    screen = None
    actions: tuple[InterfaceHostCapabilityAction, ...] = ()
    if local_node_runtime.available is False or local_node_runtime.ready is False:
        screen = InterfaceHostCapabilityScreen(
            screen_key="local_node_runtime_gate",
            source_kind="gate",
            title="Local Node Required",
            message=build_local_node_gate_message(local_node_runtime),
            pane_key="local_node_runtime_gate",
        )
        actions = (
            InterfaceHostCapabilityAction(
                action_key="ensure_local_node_runtime_started",
                label="Start Local Node",
                reason="Ask the Interface daemon to start the local Node runtime through node_deploy.",
            ),
            InterfaceHostCapabilityAction(
                action_key="restart_local_service_host",
                label="Restart Local Service",
                reason="Restart the local Service host when localhost bootstrap state is stale or upgraded.",
            ),
            InterfaceHostCapabilityAction(
                action_key="tail_local_node_runtime_logs",
                label="Tail Local Node Logs",
                reason="Fetch the latest local node bootstrap logs through the Interface daemon.",
                payload_schema_hint="object",
            ),
        )
    return InterfaceHostCapabilitySnapshot(
        capability_id="local_node_runtime",
        kind="local_node_runtime",
        screen=screen,
        actions=actions,
        operation=InterfaceHostCapabilityOperation(
            capability_id="local_node_runtime",
            title="Local Node Runtime",
            status=status,
            phase=local_node_runtime.phase,
            current_target_id=current_target.target_id if current_target is not None else None,
            current_target_title=current_target.display_name if current_target is not None else None,
            summary=local_node_runtime.summary or (
                current_target.summary if current_target is not None else None
            ),
            error=local_node_runtime.error or (
                current_target.error if current_target is not None else None
            ),
            running=status == "running",
            retryable=local_node_runtime.ready is False,
            updated_at=local_node_runtime.updated_at,
            recent_activity=local_node_runtime.recent_log_lines,
            targets=targets,
        ),
    )


def merge_local_node_log_tail(
    *,
    node_runtime: InterfaceHostServiceLocalNodeRuntimeState,
    local_node_log_tail: tuple[str, ...],
) -> tuple[InterfaceHostServiceLocalNodeRuntimeState, tuple[str, ...]]:
    if not node_runtime.managed:
        return node_runtime, ()
    if node_runtime.recent_log_lines:
        return node_runtime, node_runtime.recent_log_lines
    if node_runtime.ready:
        return node_runtime, ()
    if local_node_log_tail:
        return replace(
            node_runtime,
            recent_log_lines=local_node_log_tail,
        ), local_node_log_tail
    return node_runtime, local_node_log_tail


def apply_local_runtime_snapshot(
    *,
    service_host: InterfaceHostServiceLocalServiceHostState,
    node_runtime: InterfaceHostServiceLocalNodeRuntimeState,
    local_node_log_tail: tuple[str, ...],
) -> tuple[
    InterfaceHostServiceLocalServiceHostState,
    InterfaceHostServiceLocalNodeRuntimeState,
    tuple[str, ...],
]:
    if not service_host.ready:
        return service_host, node_runtime, ()
    merged_node_runtime, merged_tail = merge_local_node_log_tail(
        node_runtime=node_runtime,
        local_node_log_tail=local_node_log_tail,
    )
    return service_host, merged_node_runtime, merged_tail


__all__ = [
    "apply_local_runtime_snapshot",
    "build_local_node_gate_message",
    "build_local_node_runtime_capability_snapshot",
    "build_local_service_host_capability_snapshot",
    "merge_local_node_log_tail",
    "preview_lines",
    "resolve_current_node_target",
]
