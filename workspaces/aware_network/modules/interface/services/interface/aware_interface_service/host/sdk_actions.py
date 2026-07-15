from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Protocol
from uuid import UUID

from aware_interface_service.models import (
    InterfaceHostServiceOperationState,
    InterfaceHostServiceOperationTargetState,
    InterfaceHostServiceState,
)


class MountedPaneSdkActionRef(Protocol):
    @property
    def action_key(self) -> str: ...

    @property
    def pane_ref(self) -> str: ...

    @property
    def window_key(self) -> str: ...

    @property
    def layout_key(self) -> str: ...

    @property
    def section_key(self) -> str: ...

    @property
    def pane_kind(self) -> str: ...

    @property
    def state_source_kind(self) -> str: ...

    @property
    def layout_section_id(self) -> UUID | None: ...

    @property
    def section_focus_scope_id(self) -> UUID | None: ...

    @property
    def focus_scope_id(self) -> UUID | None: ...

    @property
    def focus_id(self) -> UUID | None: ...

    @property
    def branch_id(self) -> UUID | None: ...

    @property
    def focus_target(self) -> object | None: ...

    @property
    def pane_config_id(self) -> UUID | None: ...

    @property
    def pane_package_id(self) -> UUID | None: ...

    @property
    def pane_package_name(self) -> str | None: ...

    @property
    def object_projection_graph_observable_id(self) -> UUID | None: ...

    @property
    def projection_experience_view_id(self) -> UUID | None: ...

    @property
    def view_ref(self) -> str | None: ...

    @property
    def projection_view_key(self) -> str | None: ...

    @property
    def state_model_id(self) -> UUID | None: ...

    @property
    def state_provider_ref(self) -> str | None: ...

    @property
    def state_provider_kind(self) -> str | None: ...

    @property
    def state_projection_hash(self) -> str | None: ...

    @property
    def sdk_operation_ref(self) -> str | None: ...


class InterfaceHostSdkActionRuntime(Protocol):
    _current_operation: InterfaceHostServiceOperationState | None

    def state(self) -> InterfaceHostServiceState: ...

    def _notify_state_changed(self) -> None: ...


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


async def invoke_mounted_pane_sdk_action(
    runtime: InterfaceHostSdkActionRuntime,
    *,
    mounted_action_ref: MountedPaneSdkActionRef,
    payload: dict[str, object] | None = None,
) -> InterfaceHostServiceState:
    _record_blocked_mounted_pane_sdk_action_operation(
        runtime,
        mounted_action_ref=mounted_action_ref,
        request_payload=payload or {},
    )
    return runtime.state()


def _drop_none(payload: dict[str, object | None]) -> dict[str, object]:
    return {key: value for key, value in payload.items() if value is not None}


def _experience_name_from_view_ref(view_ref: str | None) -> str | None:
    normalized = (view_ref or "").strip()
    if not normalized:
        return None
    experience_name = normalized.split(".", 1)[0].strip()
    return experience_name or None


def _invocation_context_for_mounted_sdk_action_ref(
    mounted_action_ref: MountedPaneSdkActionRef,
) -> dict[str, object]:
    surface = _drop_none(
        {
            "pane_ref": mounted_action_ref.pane_ref,
            "window_key": mounted_action_ref.window_key,
            "layout_key": mounted_action_ref.layout_key,
            "section_key": mounted_action_ref.section_key,
            "pane_kind": mounted_action_ref.pane_kind,
            "state_source_kind": mounted_action_ref.state_source_kind,
            "pane_config_id": mounted_action_ref.pane_config_id,
            "pane_package_id": mounted_action_ref.pane_package_id,
            "pane_package_name": mounted_action_ref.pane_package_name,
            "view_ref": mounted_action_ref.view_ref,
            "projection_view_key": mounted_action_ref.projection_view_key,
            "projection_experience_view_id": mounted_action_ref.projection_experience_view_id,
            "state_model_id": mounted_action_ref.state_model_id,
            "state_provider_ref": mounted_action_ref.state_provider_ref,
            "state_provider_kind": mounted_action_ref.state_provider_kind,
        }
    )
    experience_name = _experience_name_from_view_ref(mounted_action_ref.view_ref)
    experience = _drop_none(
        {
            "experience_name": experience_name,
            "experience_ref": experience_name,
            "projection_experience_view_id": mounted_action_ref.projection_experience_view_id,
        }
    )
    attention = _drop_none(
        {
            "layout_section_id": mounted_action_ref.layout_section_id,
            "section_focus_scope_id": mounted_action_ref.section_focus_scope_id,
            "focus_scope_id": mounted_action_ref.focus_scope_id,
            "focus_id": mounted_action_ref.focus_id,
            "observable_id": mounted_action_ref.object_projection_graph_observable_id,
            "branch_id": mounted_action_ref.branch_id,
            "state_projection_hash": mounted_action_ref.state_projection_hash,
            "focus_target": _focus_target_payload(mounted_action_ref.focus_target),
        }
    )
    raw_action_target = getattr(mounted_action_ref, "action_target", None)
    raw_payload = (
        getattr(raw_action_target, "invocation_context_payload", None)
        if raw_action_target is not None
        else None
    )
    action_target = raw_payload() if callable(raw_payload) else None
    return _drop_none(
        {
            "surface": surface or None,
            "experience": experience or None,
            "attention": attention or None,
            "action_target": action_target or None,
        }
    )


def _focus_target_payload(focus_target: object | None) -> dict[str, object] | None:
    if focus_target is None:
        return None
    payload: dict[str, object | None] = {}
    for field_name in (
        "kind",
        "focus_id",
        "focus_scope_id",
        "projection_experience_graph_identity_id",
        "object_projection_graph_identity_id",
        "object_instance_graph_branch_id",
        "projection_hash",
        "target_type",
        "target_id",
        "description",
    ):
        payload[field_name] = getattr(focus_target, field_name, None)
    return _drop_none(payload)


def _record_blocked_mounted_pane_sdk_action_operation(
    runtime: InterfaceHostSdkActionRuntime,
    *,
    mounted_action_ref: MountedPaneSdkActionRef,
    request_payload: dict[str, object],
) -> None:
    operation_ref = mounted_action_ref.sdk_operation_ref or mounted_action_ref.action_key
    summary = "Pane action blocked before direct SDK dispatch."
    error = (
        "Interface pane actions require Experience view invocation provenance; "
        "direct API/SDK dispatch is retired."
    )
    context = _invocation_context_for_mounted_sdk_action_ref(mounted_action_ref)
    if request_payload:
        context = {**context, "request_payload": request_payload}
    runtime._current_operation = InterfaceHostServiceOperationState(
        operation_key="experience_view_invocation_required",
        title=f"Experience view action required: {operation_ref}",
        status="failed",
        phase="blocked",
        current_target_id=operation_ref,
        current_target_title=operation_ref,
        summary=summary,
        error=error,
        running=False,
        retryable=False,
        updated_at=_utc_now_iso(),
        recent_activity=(
            f"{mounted_action_ref.pane_ref} -> {mounted_action_ref.action_key}",
        ),
        target_statuses=(
            InterfaceHostServiceOperationTargetState(
                target_id=operation_ref,
                display_name=operation_ref,
                kind="experience_view_action_required",
                phase="blocked",
                is_active=False,
                is_healthy=False,
                summary=summary,
                error=error,
                detail_lines=_json_detail_lines(context),
            ),
        ),
    )
    runtime._notify_state_changed()


def _json_detail_lines(payload: object | None) -> tuple[str, ...]:
    if payload is None:
        return ()
    try:
        return (json.dumps(payload, sort_keys=True, default=str),)
    except TypeError:
        return (str(payload),)


__all__ = [
    "invoke_mounted_pane_sdk_action",
]
