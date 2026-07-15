from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class InterfaceHostCapabilityAction:
    action_key: str
    label: str
    enabled: bool = True
    reason: str | None = None
    payload_schema_hint: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceHostCapabilityTraceEntry:
    source_key: str
    source_label: str
    message: str
    step_label: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceHostCapabilityTarget:
    target_id: str
    display_name: str
    kind: str | None = None
    phase: str = "idle"
    status: str = "idle"
    is_active: bool = False
    is_healthy: bool = False
    summary: str | None = None
    error: str | None = None
    current: bool = False
    detail_lines: tuple[str, ...] = ()
    trace_preview: tuple[InterfaceHostCapabilityTraceEntry, ...] = ()


@dataclass(frozen=True, slots=True)
class InterfaceHostCapabilityOperation:
    capability_id: str
    title: str | None = None
    status: str = "idle"
    phase: str | None = None
    current_target_id: str | None = None
    current_target_title: str | None = None
    summary: str | None = None
    error: str | None = None
    running: bool = False
    retryable: bool = False
    updated_at: str | None = None
    recent_activity: tuple[str, ...] = ()
    targets: tuple[InterfaceHostCapabilityTarget, ...] = ()


@dataclass(frozen=True, slots=True)
class InterfaceHostCapabilityScreen:
    screen_key: str
    source_kind: str
    screen_kind: str = "gate"
    title: str | None = None
    message: str | None = None
    projection_view_id: str | None = None
    pane_key: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceHostPaneContribution:
    pane_key: str
    pane_kind: str
    section_key: str
    title: str | None = None
    summary: str | None = None
    status: str | None = None
    readiness_reason: str | None = None
    narrative_key: str | None = None
    action_keys: tuple[str, ...] = ()
    machine_payload: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InterfaceHostCapabilitySnapshot:
    capability_id: str
    kind: str
    screen: InterfaceHostCapabilityScreen | None = None
    actions: tuple[InterfaceHostCapabilityAction, ...] = ()
    operation: InterfaceHostCapabilityOperation | None = None
    pane_contributions: tuple[InterfaceHostPaneContribution, ...] = ()
    warnings: tuple[str, ...] = ()


class InterfaceHostCapabilityConsumer(Protocol):
    def build_snapshot(self) -> InterfaceHostCapabilitySnapshot | None:
        ...


__all__ = [
    "InterfaceHostCapabilityAction",
    "InterfaceHostCapabilityConsumer",
    "InterfaceHostCapabilityOperation",
    "InterfaceHostCapabilityScreen",
    "InterfaceHostCapabilitySnapshot",
    "InterfaceHostCapabilityTarget",
    "InterfaceHostCapabilityTraceEntry",
    "InterfaceHostPaneContribution",
]
