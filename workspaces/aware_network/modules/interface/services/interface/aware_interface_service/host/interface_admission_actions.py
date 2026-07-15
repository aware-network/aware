from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID, uuid4

from aware_identity_ontology.stable_ids import (
    stable_actor_id,
    stable_identity_id,
)
from aware_interface_service.host.capabilities.interface_admission import (
    ACCEPT_PAIRING_ACTION_KEY,
    CREATE_INTERFACE_ACTION_KEY,
    REQUEST_PAIRING_ACTION_KEY,
    RESUME_INTERFACE_ACTION_KEY,
    SELECT_INTERFACE_ACTION_KEY,
)
from aware_interface_service.models import (
    InterfaceHostServiceOperationState,
    InterfaceHostServiceOperationTargetState,
    InterfaceHostServiceState,
)


_DEFERRED_ACTION_REASONS = {
    SELECT_INTERFACE_ACTION_KEY: (
        "Interface selection needs the canonical Interface list/read model."
    ),
    REQUEST_PAIRING_ACTION_KEY: (
        "Pairing-code creation needs the canonical pairing challenge service."
    ),
    ACCEPT_PAIRING_ACTION_KEY: (
        "Pairing acceptance needs the canonical InterfaceSession commit service."
    ),
    RESUME_INTERFACE_ACTION_KEY: (
        "Interface resume needs the canonical InterfaceSession lookup service."
    ),
}


class InterfaceAdmissionActionRuntime(Protocol):
    namespace: str
    host_label: str
    _interface_admitted: bool
    _committed_interface_id: UUID | None
    _interface_system_actor_id: UUID | None
    _interface_system_identity_id: UUID | None
    _current_operation: InterfaceHostServiceOperationState | None

    def state(self) -> InterfaceHostServiceState: ...

    async def _refresh_hosted_service_status(self) -> None: ...

    async def _refresh_host_surface(self) -> None: ...

    async def _ensure_boot_interface_graph_for_admission(self) -> UUID: ...

    async def _ensure_interface_system_actor_for_admission(
        self,
        *,
        interface_id: UUID,
    ) -> tuple[UUID, UUID]: ...

    def _notify_state_changed(self) -> None: ...


_BOOT_PROGRAM_REF = "aware_control:EnsureBootInterfaceGraph"
_BOOT_PROGRAM_CONFIG = "EnsureBootInterfaceGraphConfig"
_BOOT_PENDING_REASON = "runtime_coordinator_unavailable"
_INTERFACE_SYSTEM_IDENTITY_TYPE = "system"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _payload_string(payload: dict[str, object], key: str) -> str | None:
    raw = payload.get(key)
    if not isinstance(raw, str):
        return None
    value = raw.strip()
    return value or None


def stable_interface_system_actor_ids(
    *,
    interface_id: UUID,
) -> tuple[UUID, UUID]:
    """Return the canonical system Identity/Actor ids for an Interface.

    The Identity rail owns actual actor creation. Interface bootstrap records the
    deterministic target so pre-operator actions have a provenance subject before
    human Identity admission binds an operator Actor.
    """

    identity_id = stable_identity_id(
        public_key=f"interface:{interface_id}",
        type=_INTERFACE_SYSTEM_IDENTITY_TYPE,
    )
    actor_id = stable_actor_id(identity_id=identity_id, key="default")
    return identity_id, actor_id


def _operation_state(
    *,
    action_key: str,
    interface_id: UUID,
    interface_label: str,
    status: str,
    phase: str,
    target_phase: str,
    summary: str,
    error: str | None,
    retryable: bool,
    target_healthy: bool,
    detail_lines: tuple[str, ...],
) -> InterfaceHostServiceOperationState:
    return InterfaceHostServiceOperationState(
        operation_key=action_key,
        title="Interface Admission",
        status=status,
        phase=phase,
        current_target_id=str(interface_id),
        current_target_title=interface_label,
        summary=summary,
        error=error,
        running=False,
        retryable=retryable,
        updated_at=_utc_now_iso(),
        recent_activity=(
            f"[interface] {summary}",
            f"[interface] interface_id={interface_id}",
        ),
        target_statuses=(
            InterfaceHostServiceOperationTargetState(
                target_id=str(interface_id),
                display_name=interface_label,
                kind="interface",
                phase=target_phase,
                is_active=True,
                is_healthy=target_healthy,
                summary=summary,
                error=error,
                detail_lines=detail_lines,
            ),
        ),
    )


async def invoke_interface_admission_action(
    runtime: InterfaceAdmissionActionRuntime,
    *,
    action_key: str,
    payload: dict[str, object] | None = None,
) -> InterfaceHostServiceState:
    request_payload = payload or {}
    if action_key == CREATE_INTERFACE_ACTION_KEY:
        return await _create_interface(runtime, payload=request_payload)
    reason = _DEFERRED_ACTION_REASONS.get(
        action_key,
        f"Unsupported Interface Admission action: {action_key}",
    )
    raise RuntimeError(reason)


async def _create_interface(
    runtime: InterfaceAdmissionActionRuntime,
    *,
    payload: dict[str, object],
) -> InterfaceHostServiceState:
    display_name = (
        _payload_string(payload, "display_name") or f"{runtime.host_label} Interface"
    )
    idempotency_key = _payload_string(payload, "idempotency_key")
    window_config_id = _payload_string(payload, "window_config_id")

    interface_id = runtime._committed_interface_id or uuid4()
    status = "pending"
    phase = "admitted_boot_pending"
    target_phase = "boot_pending"
    target_healthy = False
    retryable = True
    error: str | None = None
    summary = f"Interface admitted for {runtime.namespace}; boot graph is pending."
    boot_detail_lines: tuple[str, ...] = (
        "boot_status=pending",
        f"boot_program_ref={_BOOT_PROGRAM_REF}",
        f"boot_program_config={_BOOT_PROGRAM_CONFIG}",
        f"boot_reason={_BOOT_PENDING_REASON}",
    )

    try:
        interface_id = await runtime._ensure_boot_interface_graph_for_admission()
    except AttributeError:
        runtime._committed_interface_id = interface_id
    except RuntimeError as exc:
        if str(exc) == _BOOT_PENDING_REASON:
            runtime._committed_interface_id = interface_id
        else:
            runtime._committed_interface_id = interface_id
            status = "failed"
            phase = "admitted_boot_failed"
            target_phase = "boot_failed"
            error = str(exc)
            summary = (
                f"Interface admitted for {runtime.namespace}; " "boot graph failed."
            )
            boot_detail_lines = (
                "boot_status=failed",
                f"boot_program_ref={_BOOT_PROGRAM_REF}",
                f"boot_program_config={_BOOT_PROGRAM_CONFIG}",
                f"boot_error={error}",
            )
    except Exception as exc:  # pragma: no cover - defensive host boundary.
        runtime._committed_interface_id = interface_id
        status = "failed"
        phase = "admitted_boot_failed"
        target_phase = "boot_failed"
        error = str(exc)
        summary = f"Interface admitted for {runtime.namespace}; boot graph failed."
        boot_detail_lines = (
            "boot_status=failed",
            f"boot_program_ref={_BOOT_PROGRAM_REF}",
            f"boot_program_config={_BOOT_PROGRAM_CONFIG}",
            f"boot_error={error}",
        )
    else:
        runtime._committed_interface_id = interface_id
        status = "succeeded"
        phase = "admitted_boot_committed"
        target_phase = "boot_committed"
        target_healthy = True
        retryable = False
        summary = (
            f"Interface admitted and boot graph committed for {runtime.namespace}."
        )
        boot_detail_lines = (
            "boot_status=committed",
            f"boot_program_ref={_BOOT_PROGRAM_REF}",
            f"boot_program_config={_BOOT_PROGRAM_CONFIG}",
        )

    try:
        (
            interface_system_identity_id,
            interface_system_actor_id,
        ) = await runtime._ensure_interface_system_actor_for_admission(
            interface_id=interface_id,
        )
    except AttributeError:
        (
            interface_system_identity_id,
            interface_system_actor_id,
        ) = stable_interface_system_actor_ids(interface_id=interface_id)
        runtime._interface_system_identity_id = interface_system_identity_id
        runtime._interface_system_actor_id = interface_system_actor_id

    runtime._interface_admitted = True

    detail_lines = (
        f"interface_id={interface_id}",
        f"interface_system_identity_id={interface_system_identity_id}",
        f"interface_system_actor_id={interface_system_actor_id}",
        f"namespace={runtime.namespace}",
        f"host_label={runtime.host_label}",
        "identity_authenticated=false",
    )
    optional_lines = tuple(
        line
        for line in (
            f"window_config_id={window_config_id}" if window_config_id else None,
            f"idempotency_key={idempotency_key}" if idempotency_key else None,
        )
        if line is not None
    )
    detail_lines = detail_lines + boot_detail_lines + optional_lines

    await runtime._refresh_hosted_service_status()
    await runtime._refresh_host_surface()
    runtime._current_operation = _operation_state(
        action_key=CREATE_INTERFACE_ACTION_KEY,
        interface_id=interface_id,
        interface_label=display_name,
        status=status,
        phase=phase,
        target_phase=target_phase,
        summary=summary,
        error=error,
        retryable=retryable,
        target_healthy=target_healthy,
        detail_lines=detail_lines,
    )
    runtime._notify_state_changed()
    return runtime.state()


__all__ = ["invoke_interface_admission_action"]
