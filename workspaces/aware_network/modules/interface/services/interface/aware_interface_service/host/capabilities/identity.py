from __future__ import annotations

from aware_interface import (
    InterfaceHostCapabilityOperation,
    InterfaceHostCapabilityScreen,
    InterfaceHostCapabilitySnapshot,
    InterfaceHostCapabilityTarget,
    InterfaceHostCapabilityTraceEntry,
)
from aware_interface_service.models import (
    InterfaceHostServiceLocalNodeRuntimeState,
    InterfaceHostServiceLocalServiceHostState,
)

CONTROL_IDENTITY_ADMISSION_SCREEN_KEY = "control_identity_admission"
CONTROL_IDENTITY_ADMISSION_PANE_KEY = "identity_admission"


def preview_lines(lines: tuple[str, ...], *, max_lines: int = 8) -> tuple[str, ...]:
    if len(lines) <= max_lines:
        return lines
    return lines[-max_lines:]


def identity_gate_active(
    *,
    authenticated: bool,
    consumer_profile_active: bool,
    local_service_host: InterfaceHostServiceLocalServiceHostState | None,
    local_node_runtime: InterfaceHostServiceLocalNodeRuntimeState | None,
) -> bool:
    if authenticated:
        return False
    if consumer_profile_active:
        return True
    if (
        local_service_host is not None
        and local_service_host.managed
        and not local_service_host.ready
    ):
        return False
    if (
        local_node_runtime is not None
        and local_node_runtime.managed
        and (local_node_runtime.available is False or local_node_runtime.ready is False)
    ):
        return False
    return True


def identity_gate_phase(
    *,
    admission_error: str | None,
    admission_updated_at: str | None,
    transport_bound: bool,
) -> str:
    if admission_error is not None:
        return "admission_failed"
    if admission_updated_at is not None:
        return "admission_created"
    if not transport_bound:
        return "transport_required"
    return "awaiting_signup"


def identity_gate_summary(
    *,
    transport_bound: bool,
    admission_summary: str | None,
    admission_error: str | None,
) -> str:
    if admission_error is not None:
        return admission_error
    if admission_summary is not None:
        return admission_summary
    if not transport_bound:
        return "Identity admission requires an Interface transport session bound to a node endpoint."
    return (
        "This Interface namespace is ready locally but is not attached to an actor yet. "
        "Use remote Identity admission to create the canonical actor record."
    )


def identity_gate_message(
    *,
    transport_bound: bool,
    admission_summary: str | None,
    admission_error: str | None,
    admission_updated_at: str | None,
) -> str:
    summary = identity_gate_summary(
        transport_bound=transport_bound,
        admission_summary=admission_summary,
        admission_error=admission_error,
    )
    if admission_updated_at is not None and admission_error is None:
        return f"{summary} Token-backed attach remains a follow-on rail."
    return summary


def identity_detail_lines(
    *,
    transport_bound: bool,
    admission_summary: str | None,
    admission_error: str | None,
    admission_detail_lines: tuple[str, ...],
) -> tuple[str, ...]:
    if admission_detail_lines:
        return admission_detail_lines
    return (
        identity_gate_summary(
            transport_bound=transport_bound,
            admission_summary=admission_summary,
            admission_error=admission_error,
        ),
    )


def identity_trace_preview(
    *,
    transport_bound: bool,
    admission_summary: str | None,
    admission_error: str | None,
    admission_detail_lines: tuple[str, ...],
    admission_recent_activity: tuple[str, ...],
) -> tuple[InterfaceHostCapabilityTraceEntry, ...]:
    lines = admission_recent_activity
    if not lines:
        lines = tuple(
            f"[identity] {line}"
            for line in identity_detail_lines(
                transport_bound=transport_bound,
                admission_summary=admission_summary,
                admission_error=admission_error,
                admission_detail_lines=admission_detail_lines,
            )
        )
    return tuple(
        InterfaceHostCapabilityTraceEntry(
            source_key="identity",
            source_label="Identity",
            message=line.removeprefix("[identity] ").strip(),
        )
        for line in preview_lines(lines, max_lines=8)
    )


def build_identity_capability_snapshot(
    *,
    consumer_profile_active: bool,
    authenticated: bool,
    transport_bound: bool,
    local_service_host: InterfaceHostServiceLocalServiceHostState | None,
    local_node_runtime: InterfaceHostServiceLocalNodeRuntimeState | None,
    admission_summary: str | None,
    admission_error: str | None,
    admission_detail_lines: tuple[str, ...],
    admission_recent_activity: tuple[str, ...],
    admission_updated_at: str | None,
) -> InterfaceHostCapabilitySnapshot | None:
    if not identity_gate_active(
        authenticated=authenticated,
        consumer_profile_active=consumer_profile_active,
        local_service_host=local_service_host,
        local_node_runtime=local_node_runtime,
    ):
        return None

    phase = identity_gate_phase(
        admission_error=admission_error,
        admission_updated_at=admission_updated_at,
        transport_bound=transport_bound,
    )
    summary = identity_gate_summary(
        transport_bound=transport_bound,
        admission_summary=admission_summary,
        admission_error=admission_error,
    )
    trace_preview = identity_trace_preview(
        transport_bound=transport_bound,
        admission_summary=admission_summary,
        admission_error=admission_error,
        admission_detail_lines=admission_detail_lines,
        admission_recent_activity=admission_recent_activity,
    )
    target = InterfaceHostCapabilityTarget(
        target_id="identity",
        display_name="Identity Admission",
        kind="identity",
        phase=phase,
        status="blocked" if admission_error else "waiting",
        is_active=admission_error is None,
        is_healthy=admission_updated_at is not None and admission_error is None,
        summary=summary,
        error=admission_error,
        current=True,
        detail_lines=identity_detail_lines(
            transport_bound=transport_bound,
            admission_summary=admission_summary,
            admission_error=admission_error,
            admission_detail_lines=admission_detail_lines,
        ),
        trace_preview=trace_preview,
    )
    return InterfaceHostCapabilitySnapshot(
        capability_id="identity",
        kind="identity",
        screen=InterfaceHostCapabilityScreen(
            screen_key=CONTROL_IDENTITY_ADMISSION_SCREEN_KEY,
            source_kind="control_resolver",
            screen_kind="resolver",
            title="Identity Admission",
            message=identity_gate_message(
                transport_bound=transport_bound,
                admission_summary=admission_summary,
                admission_error=admission_error,
                admission_updated_at=admission_updated_at,
            ),
            pane_key=CONTROL_IDENTITY_ADMISSION_PANE_KEY,
        ),
        actions=(),
        operation=InterfaceHostCapabilityOperation(
            capability_id="identity_admission",
            title="Identity Admission",
            status="failed" if admission_error else "waiting",
            phase=phase,
            current_target_id=target.target_id,
            current_target_title=target.display_name,
            summary=summary,
            error=admission_error,
            running=False,
            retryable=True,
            updated_at=admission_updated_at,
            recent_activity=admission_recent_activity,
            targets=(target,),
        ),
    )


__all__ = [
    "CONTROL_IDENTITY_ADMISSION_PANE_KEY",
    "CONTROL_IDENTITY_ADMISSION_SCREEN_KEY",
    "build_identity_capability_snapshot",
    "identity_detail_lines",
    "identity_gate_active",
    "identity_gate_message",
    "identity_gate_phase",
    "identity_gate_summary",
    "identity_trace_preview",
]
