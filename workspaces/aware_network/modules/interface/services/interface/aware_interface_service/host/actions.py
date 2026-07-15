from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Protocol
from uuid import UUID, uuid4

from aware_experience_service_api import AwareExperienceServiceApiClient
from aware_experience_sdk import build_experience_sdk_client
from aware_interface import InterfaceResolvedPaneDescriptor, InterfaceRuntimeState
from aware_interface.lifecycle.models import InterfaceAttentionFocusTargetState
from aware_interface_sdk.transport import InterfaceTransportSession

from aware_interface_service.local_runtime import InterfaceLocalRuntimeController
from aware_interface_service.host.capabilities import (
    hosted_services as hosted_services_capability_mod,
)
from aware_interface_service.host.capabilities.interface_admission import (
    INTERFACE_ADMISSION_ACTION_KEYS,
)
from aware_interface_service.host import (
    interface_admission_actions as interface_admission_actions_mod,
)
from aware_interface_service.models import (
    InterfaceHostServiceLocalNodeRuntimeState,
    InterfaceHostServiceLocalServiceHostState,
    InterfaceHostServiceOperationState,
    InterfaceHostServiceOperationTargetState,
    InterfaceHostServiceState,
)


_API_ACTION_KEY_PREFIX = "api:"
_SDK_ACTION_KEY_PREFIX = "sdk:"


@dataclass(frozen=True, slots=True)
class InterfaceActionTarget:
    action_key: str | None = None
    action_kind: str | None = None
    operation_ref: str | None = None
    sdk_operation_id: str | None = None
    pane_config_sdk_operation_id: str | None = None
    endpoint_ref: str | None = None
    view_invocation_action_config_id: str | None = None
    api_capability_endpoint_id: str | None = None
    pane_config_api_capability_endpoint_id: str | None = None

    @property
    def normalized_action_kind(self) -> str | None:
        return _normalized_action_kind(self.action_kind)

    def effective_action_key(self, fallback: str) -> str:
        if (
            self.action_key is not None
            and not self.action_key.startswith(_API_ACTION_KEY_PREFIX)
            and not self.action_key.startswith(_SDK_ACTION_KEY_PREFIX)
        ):
            return self.action_key
        action_kind = self.normalized_action_kind
        if action_kind == "sdk_operation" and self.operation_ref is not None:
            return f"{_SDK_ACTION_KEY_PREFIX}{self.operation_ref}"
        if action_kind == "api_endpoint" and self.endpoint_ref is not None:
            return f"{_API_ACTION_KEY_PREFIX}{self.endpoint_ref}"
        return self.action_key or fallback

    def invocation_context_payload(self) -> dict[str, object]:
        return _drop_none(
            {
                "action_key": self.action_key,
                "action_kind": self.normalized_action_kind or self.action_kind,
                "operation_ref": self.operation_ref,
                "sdk_operation_id": self.sdk_operation_id,
                "pane_config_sdk_operation_id": self.pane_config_sdk_operation_id,
                "endpoint_ref": self.endpoint_ref,
                "view_invocation_action_config_id": self.view_invocation_action_config_id,
                "api_capability_endpoint_id": self.api_capability_endpoint_id,
                "pane_config_api_capability_endpoint_id": self.pane_config_api_capability_endpoint_id,
            }
        )


@dataclass(frozen=True, slots=True)
class MountedPaneActionRef:
    action_key: str
    pane_ref: str
    window_key: str
    layout_key: str
    section_key: str
    pane_kind: str
    state_source_kind: str
    action_family: str
    layout_section_id: UUID | None = None
    section_focus_scope_id: UUID | None = None
    focus_scope_id: UUID | None = None
    focus_id: UUID | None = None
    branch_id: UUID | None = None
    focus_target: InterfaceAttentionFocusTargetState | None = None
    pane_config_id: UUID | None = None
    pane_package_id: UUID | None = None
    pane_package_name: str | None = None
    object_projection_graph_observable_id: UUID | None = None
    projection_experience_view_id: UUID | None = None
    projection_experience_view_instance_id: UUID | None = None
    view_invocation_action_config_id: UUID | None = None
    view_ref: str | None = None
    projection_view_key: str | None = None
    state_model_id: UUID | None = None
    state_provider_ref: str | None = None
    state_provider_kind: str | None = None
    state_projection_hash: str | None = None
    api_endpoint_ref: str | None = None
    sdk_operation_ref: str | None = None
    action_target: InterfaceActionTarget | None = None

    @property
    def is_api_endpoint(self) -> bool:
        return self.action_family == "api_endpoint"

    @property
    def is_sdk_operation(self) -> bool:
        return self.action_family == "sdk_operation"

    @property
    def is_experience_view_invocation(self) -> bool:
        return (
            self.projection_experience_view_instance_id is not None
            and self.view_invocation_action_config_id is not None
        )

    @property
    def is_interface_admission(self) -> bool:
        return self.action_family == "interface_admission"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _resolve_tail_line_count(payload: dict[str, object] | None) -> int:
    if payload is None:
        return 200
    raw = payload.get("line_count")
    if raw is None:
        return 200
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise RuntimeError(
            "tail_local_node_runtime_logs payload.line_count must be an integer."
        )
    return max(1, raw)


def _resolve_required_token(payload: dict[str, object] | None) -> str:
    if payload is None:
        raise RuntimeError("submit_token payload.token is required.")
    raw = payload.get("token")
    if not isinstance(raw, str) or not raw.strip():
        raise RuntimeError("submit_token payload.token must be a non-empty string.")
    return raw.strip()


def _host_restart_reason(payload: dict[str, object] | None) -> str:
    if payload is not None:
        raw = payload.get("reason")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return "Interface Host restart requested through Interface recovery action."


def _host_restart_evidence(
    payload: dict[str, object] | None,
) -> dict[str, object]:
    evidence: dict[str, object] = {
        "interface_action": "interface.host.restart_host",
        "source": "interface_service_host_action",
    }
    if payload is None:
        return evidence
    raw_evidence = payload.get("evidence")
    if isinstance(raw_evidence, dict):
        evidence["request_evidence"] = {
            str(key): value for key, value in raw_evidence.items()
        }
    payload_without_evidence = {
        str(key): value for key, value in payload.items() if key != "evidence"
    }
    if payload_without_evidence:
        evidence["payload"] = payload_without_evidence
    return evidence


def _primary_pane_ref(pane: InterfaceResolvedPaneDescriptor) -> str:
    window_key = pane.window_key.strip()
    layout_key = pane.layout_key.strip()
    section_key = pane.section_key.strip()
    if window_key and layout_key and section_key:
        return f"{window_key}/{layout_key}/{section_key}"
    return section_key or pane.pane_kind.strip() or "unknown"


def _pane_aliases(pane: InterfaceResolvedPaneDescriptor) -> tuple[str, ...]:
    values = (
        _primary_pane_ref(pane),
        pane.section_key.strip(),
        pane.pane_kind.strip(),
        (pane.pane_package_name or "").strip(),
    )
    aliases: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value:
            continue
        normalized = value.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        aliases.append(value)
    return tuple(aliases)


def _pane_matches_ref(pane: InterfaceResolvedPaneDescriptor, pane_ref: str) -> bool:
    normalized_ref = pane_ref.strip().casefold()
    return any(alias.casefold() == normalized_ref for alias in _pane_aliases(pane))


def _action_family(action_key: str) -> str:
    if action_key.startswith(_API_ACTION_KEY_PREFIX):
        return "api_endpoint"
    if action_key.startswith(_SDK_ACTION_KEY_PREFIX):
        return "sdk_operation"
    if action_key in INTERFACE_ADMISSION_ACTION_KEYS:
        return "interface_admission"
    return "host_compatibility"


def _api_endpoint_ref(action_key: str) -> str | None:
    if not action_key.startswith(_API_ACTION_KEY_PREFIX):
        return None
    endpoint_ref = action_key[len(_API_ACTION_KEY_PREFIX) :].strip()
    return endpoint_ref or None


def _sdk_operation_ref(action_key: str) -> str | None:
    if not action_key.startswith(_SDK_ACTION_KEY_PREFIX):
        return None
    operation_ref = action_key[len(_SDK_ACTION_KEY_PREFIX) :].strip()
    return operation_ref or None


def _trimmed_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _as_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return None


def _normalized_action_kind(action_kind: str | None) -> str | None:
    normalized = (action_kind or "").strip().casefold()
    if normalized in {"sdk", "sdk_operation"}:
        return "sdk_operation"
    if normalized in {
        "api",
        "api_endpoint",
        "api_capability_endpoint",
        "capability_endpoint",
    }:
        return "api_endpoint"
    if normalized in {"host", "host_compatibility"}:
        return "host_compatibility"
    return None


def interface_action_target_from_request_payload(
    request_payload: dict[str, object],
) -> InterfaceActionTarget | None:
    action_kind = _trimmed_string(request_payload.get("action_kind"))
    operation_ref = _trimmed_string(request_payload.get("operation_ref"))
    sdk_operation_id = _trimmed_string(request_payload.get("sdk_operation_id"))
    pane_config_sdk_operation_id = _trimmed_string(
        request_payload.get("pane_config_sdk_operation_id")
    )
    endpoint_ref = _trimmed_string(request_payload.get("endpoint_ref"))
    view_invocation_action_config_id = _trimmed_string(
        request_payload.get("view_invocation_action_config_id")
    )
    api_capability_endpoint_id = _trimmed_string(
        request_payload.get("api_capability_endpoint_id")
    )
    pane_config_api_capability_endpoint_id = _trimmed_string(
        request_payload.get("pane_config_api_capability_endpoint_id")
    )
    has_target_identity = any(
        value is not None
        for value in (
            action_kind,
            operation_ref,
            sdk_operation_id,
            pane_config_sdk_operation_id,
            endpoint_ref,
            view_invocation_action_config_id,
            api_capability_endpoint_id,
            pane_config_api_capability_endpoint_id,
        )
    )
    if not has_target_identity:
        return None
    return InterfaceActionTarget(
        action_key=_trimmed_string(request_payload.get("action_key")),
        action_kind=action_kind,
        operation_ref=operation_ref,
        sdk_operation_id=sdk_operation_id,
        pane_config_sdk_operation_id=pane_config_sdk_operation_id,
        endpoint_ref=endpoint_ref,
        view_invocation_action_config_id=view_invocation_action_config_id,
        api_capability_endpoint_id=api_capability_endpoint_id,
        pane_config_api_capability_endpoint_id=pane_config_api_capability_endpoint_id,
    )


def _interface_action_target_from_resolved_pane_action(
    *,
    pane: InterfaceResolvedPaneDescriptor,
    action_key: str,
) -> InterfaceActionTarget | None:
    normalized_key = action_key.strip().casefold()
    if not normalized_key:
        return None
    matches = [
        target
        for target in tuple(getattr(pane, "action_targets", ()))
        if getattr(target, "action_key", "").strip().casefold() == normalized_key
    ]
    if not matches:
        return None
    if len(matches) > 1:
        raise RuntimeError(
            "Resolved pane exposes multiple Experience action targets for action_key: "
            + f"pane={_primary_pane_ref(pane)!r} action_key={action_key!r}"
        )
    target = matches[0]
    action_kind = getattr(target, "action_kind", None)
    normalized_kind = _normalized_action_kind(action_kind)
    target_ref = getattr(target, "target_ref", None)
    view_invocation_action_config_id = getattr(
        target,
        "view_invocation_action_config_id",
        None,
    )
    api_capability_endpoint_id = getattr(target, "api_capability_endpoint_id", None)
    sdk_operation_id = getattr(target, "sdk_operation_id", None)
    return InterfaceActionTarget(
        action_key=getattr(target, "action_key", None),
        action_kind=action_kind,
        endpoint_ref=target_ref if normalized_kind == "api_endpoint" else None,
        operation_ref=target_ref if normalized_kind == "sdk_operation" else None,
        view_invocation_action_config_id=(
            str(view_invocation_action_config_id)
            if view_invocation_action_config_id is not None
            else None
        ),
        api_capability_endpoint_id=(
            str(api_capability_endpoint_id)
            if api_capability_endpoint_id is not None
            else None
        ),
        sdk_operation_id=(
            str(sdk_operation_id) if sdk_operation_id is not None else None
        ),
    )


def _pane_action_key_for_target_ref(
    *,
    pane: InterfaceResolvedPaneDescriptor,
    action_kind: str | None,
    target_ref: str | None,
) -> str | None:
    normalized_kind = _normalized_action_kind(action_kind)
    normalized_target_ref = (target_ref or "").strip()
    if normalized_kind is None or not normalized_target_ref:
        return None
    matches = [
        target
        for target in tuple(getattr(pane, "action_targets", ()))
        if _normalized_action_kind(getattr(target, "action_kind", None))
        == normalized_kind
        and getattr(target, "target_ref", "").strip() == normalized_target_ref
    ]
    if not matches:
        return None
    if len(matches) > 1:
        raise RuntimeError(
            "Resolved pane exposes multiple Experience action targets for target_ref: "
            + f"pane={_primary_pane_ref(pane)!r} target_ref={normalized_target_ref!r}"
        )
    return getattr(matches[0], "action_key", None)


def _resolve_effective_pane_action_key(
    *,
    pane: InterfaceResolvedPaneDescriptor,
    requested_action_key: str,
    action_target: InterfaceActionTarget | None,
) -> str:
    effective_action_key = (
        action_target.effective_action_key(requested_action_key)
        if action_target is not None
        else requested_action_key
    )
    pane_action_keys = tuple(getattr(pane, "action_keys", ()))
    if effective_action_key in pane_action_keys:
        return effective_action_key

    if action_target is not None:
        target_ref = action_target.operation_ref or action_target.endpoint_ref
        mapped_action_key = _pane_action_key_for_target_ref(
            pane=pane,
            action_kind=action_target.action_kind,
            target_ref=target_ref,
        )
        if mapped_action_key is not None and mapped_action_key in pane_action_keys:
            return mapped_action_key

    if requested_action_key.startswith(_API_ACTION_KEY_PREFIX):
        mapped_action_key = _pane_action_key_for_target_ref(
            pane=pane,
            action_kind="api_endpoint",
            target_ref=_api_endpoint_ref(requested_action_key),
        )
        if mapped_action_key is not None and mapped_action_key in pane_action_keys:
            return mapped_action_key

    if requested_action_key.startswith(_SDK_ACTION_KEY_PREFIX):
        mapped_action_key = _pane_action_key_for_target_ref(
            pane=pane,
            action_kind="sdk_operation",
            target_ref=_sdk_operation_ref(requested_action_key),
        )
        if mapped_action_key is not None and mapped_action_key in pane_action_keys:
            return mapped_action_key

    return effective_action_key


def _mounted_pane_action_ref(
    *,
    pane: InterfaceResolvedPaneDescriptor,
    action_key: str,
    action_target: InterfaceActionTarget | None = None,
) -> MountedPaneActionRef:
    pane_action_target = _interface_action_target_from_resolved_pane_action(
        pane=pane,
        action_key=action_key,
    )
    resolved_action_target = action_target
    if resolved_action_target is None:
        resolved_action_target = pane_action_target
    elif pane_action_target is not None:
        resolved_action_target = _merge_action_target_with_pane_target(
            requested=resolved_action_target,
            pane_target=pane_action_target,
        )
    action_family = (
        resolved_action_target.normalized_action_kind
        if resolved_action_target is not None
        and resolved_action_target.normalized_action_kind is not None
        else _action_family(action_key)
    )
    return MountedPaneActionRef(
        action_key=action_key,
        pane_ref=_primary_pane_ref(pane),
        window_key=pane.window_key,
        layout_key=pane.layout_key,
        section_key=pane.section_key,
        pane_kind=pane.pane_kind,
        state_source_kind=pane.state_source_kind,
        action_family=action_family,
        layout_section_id=pane.layout_section_id,
        section_focus_scope_id=pane.section_focus_scope_id,
        focus_scope_id=pane.focus_scope_id,
        focus_id=pane.focus_id,
        branch_id=pane.branch_id,
        focus_target=pane.focus_target,
        pane_config_id=pane.pane_config_id,
        pane_package_id=pane.pane_package_id,
        pane_package_name=pane.pane_package_name,
        object_projection_graph_observable_id=pane.object_projection_graph_observable_id,
        projection_experience_view_id=pane.projection_experience_view_id,
        projection_experience_view_instance_id=getattr(
            pane,
            "projection_experience_view_instance_id",
            None,
        ),
        view_invocation_action_config_id=(
            _as_uuid(resolved_action_target.view_invocation_action_config_id)
            if resolved_action_target is not None
            else None
        ),
        view_ref=pane.view_ref,
        projection_view_key=pane.projection_view_key,
        state_model_id=pane.state_model_id,
        state_provider_ref=pane.state_provider_ref,
        state_provider_kind=pane.state_provider_kind,
        state_projection_hash=pane.state_projection_hash,
        api_endpoint_ref=(
            resolved_action_target.endpoint_ref
            if resolved_action_target is not None
            and resolved_action_target.endpoint_ref is not None
            else _api_endpoint_ref(action_key)
        ),
        sdk_operation_ref=(
            resolved_action_target.operation_ref
            if resolved_action_target is not None
            and resolved_action_target.operation_ref is not None
            else _sdk_operation_ref(action_key)
        ),
        action_target=resolved_action_target,
    )


def _merge_action_target_with_pane_target(
    *,
    requested: InterfaceActionTarget,
    pane_target: InterfaceActionTarget,
) -> InterfaceActionTarget:
    return InterfaceActionTarget(
        action_key=requested.action_key or pane_target.action_key,
        action_kind=requested.action_kind or pane_target.action_kind,
        operation_ref=requested.operation_ref or pane_target.operation_ref,
        sdk_operation_id=requested.sdk_operation_id or pane_target.sdk_operation_id,
        pane_config_sdk_operation_id=(
            requested.pane_config_sdk_operation_id
            or pane_target.pane_config_sdk_operation_id
        ),
        endpoint_ref=requested.endpoint_ref or pane_target.endpoint_ref,
        view_invocation_action_config_id=(
            requested.view_invocation_action_config_id
            or pane_target.view_invocation_action_config_id
        ),
        api_capability_endpoint_id=(
            requested.api_capability_endpoint_id
            or pane_target.api_capability_endpoint_id
        ),
        pane_config_api_capability_endpoint_id=(
            requested.pane_config_api_capability_endpoint_id
            or pane_target.pane_config_api_capability_endpoint_id
        ),
    )


def _drop_none(payload: dict[str, object | None]) -> dict[str, object]:
    return {key: value for key, value in payload.items() if value is not None}


def _experience_name_from_view_ref(view_ref: str | None) -> str | None:
    normalized = (view_ref or "").strip()
    if not normalized:
        return None
    experience_name = normalized.split(".", 1)[0].strip()
    return experience_name or None


def invocation_context_for_mounted_action_ref(
    mounted_action_ref: MountedPaneActionRef,
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
    action_target = (
        mounted_action_ref.action_target.invocation_context_payload()
        if mounted_action_ref.action_target is not None
        else None
    )
    return _drop_none(
        {
            "surface": surface or None,
            "experience": experience or None,
            "attention": attention or None,
            "action_target": action_target or None,
        }
    )


def _focus_target_payload(
    focus_target: InterfaceAttentionFocusTargetState | None,
) -> dict[str, object] | None:
    if focus_target is None:
        return None
    return _drop_none(
        {
            "kind": focus_target.kind,
            "focus_id": focus_target.focus_id,
            "focus_scope_id": focus_target.focus_scope_id,
            "projection_experience_graph_identity_id": (
                focus_target.projection_experience_graph_identity_id
            ),
            "object_projection_graph_identity_id": (
                focus_target.object_projection_graph_identity_id
            ),
            "object_instance_graph_branch_id": (
                focus_target.object_instance_graph_branch_id
            ),
            "projection_hash": focus_target.projection_hash,
            "target_type": focus_target.target_type,
            "target_id": focus_target.target_id,
            "description": focus_target.description,
        }
    )


def resolve_mounted_pane_action_ref(
    *,
    runtime_state: InterfaceRuntimeState,
    pane_ref: str | None,
    action_key: str,
    action_target: InterfaceActionTarget | None = None,
) -> MountedPaneActionRef:
    panes = tuple(runtime_state.resolved_panes)
    normalized_pane_ref = (pane_ref or "").strip()
    if normalized_pane_ref:
        matching_panes = [
            pane for pane in panes if _pane_matches_ref(pane, normalized_pane_ref)
        ]
        if not matching_panes:
            raise RuntimeError(
                f"Pane {normalized_pane_ref!r} is not mounted in the current Interface surface."
            )
        if len(matching_panes) > 1:
            refs = ", ".join(_primary_pane_ref(pane) for pane in matching_panes)
            raise RuntimeError(
                f"Pane ref {normalized_pane_ref!r} is ambiguous; use one of: {refs}."
            )
        pane = matching_panes[0]
        effective_action_key = _resolve_effective_pane_action_key(
            pane=pane,
            requested_action_key=action_key,
            action_target=action_target,
        )
        if effective_action_key not in tuple(getattr(pane, "action_keys", ())):
            raise RuntimeError(
                f"Action {effective_action_key!r} is not exposed by pane {_primary_pane_ref(pane)!r}."
            )
        return _mounted_pane_action_ref(
            pane=pane,
            action_key=effective_action_key,
            action_target=action_target,
        )

    action_panes = [
        pane
        for pane in panes
        if _resolve_effective_pane_action_key(
            pane=pane,
            requested_action_key=action_key,
            action_target=action_target,
        )
        in tuple(getattr(pane, "action_keys", ()))
    ]
    if not action_panes:
        effective_action_key = (
            action_target.effective_action_key(action_key)
            if action_target is not None
            else action_key
        )
        raise RuntimeError(
            f"Action {effective_action_key!r} is not exposed by any mounted Interface pane."
        )
    if len(action_panes) > 1:
        effective_action_key = (
            action_target.effective_action_key(action_key)
            if action_target is not None
            else action_key
        )
        refs = ", ".join(_primary_pane_ref(pane) for pane in action_panes)
        raise RuntimeError(
            f"Action {effective_action_key!r} is exposed by multiple panes; provide pane_ref. "
            f"Candidates: {refs}."
        )
    effective_action_key = _resolve_effective_pane_action_key(
        pane=action_panes[0],
        requested_action_key=action_key,
        action_target=action_target,
    )
    return _mounted_pane_action_ref(
        pane=action_panes[0],
        action_key=effective_action_key,
        action_target=action_target,
    )


def _require_pane_exposes_action(
    runtime: "InterfaceHostActionRuntime",
    *,
    pane_ref: str | None,
    action_key: str,
    action_target: InterfaceActionTarget | None = None,
) -> MountedPaneActionRef:
    host_state = runtime.state()
    runtime_state = host_state.runtime
    if runtime_state is None:
        raise RuntimeError(
            "Interface action dispatch requires a resolved Interface runtime surface."
        )
    return resolve_mounted_pane_action_ref(
        runtime_state=runtime_state,
        pane_ref=pane_ref,
        action_key=action_key,
        action_target=action_target,
    )


class InterfaceHostActionRuntime(Protocol):
    local_runtime: InterfaceLocalRuntimeController | None
    transport_session: InterfaceTransportSession | None
    endpoint: str | None
    _authenticated: bool
    _interface_admitted: bool
    _committed_interface_id: UUID | None
    _local_service_host: InterfaceHostServiceLocalServiceHostState | None
    _local_node_runtime: InterfaceHostServiceLocalNodeRuntimeState | None
    _current_operation: InterfaceHostServiceOperationState | None

    def state(self) -> InterfaceHostServiceState: ...

    async def _refresh_host_surface(self) -> None: ...

    async def _refresh_hosted_service_status(self) -> None: ...

    def _notify_state_changed(self) -> None: ...

    def _apply_local_runtime_snapshot(
        self,
        *,
        service_host: InterfaceHostServiceLocalServiceHostState,
        node_runtime: InterfaceHostServiceLocalNodeRuntimeState,
    ) -> None: ...


async def perform_action(
    runtime: InterfaceHostActionRuntime,
    *,
    pane_ref: str | None = None,
    action_key: str,
    action_target: InterfaceActionTarget | None = None,
    payload: dict[str, object] | None = None,
) -> InterfaceHostServiceState:
    try:
        mounted_action_ref = _require_pane_exposes_action(
            runtime,
            pane_ref=pane_ref,
            action_key=action_key,
            action_target=action_target,
        )
    except RuntimeError:
        if _host_state_allows_action(runtime, action_key=action_key):
            host_surface_state = await _perform_host_surface_action(
                runtime,
                action_key=action_key,
                payload=payload,
            )
            if host_surface_state is not None:
                return host_surface_state
        raise
    if mounted_action_ref.is_experience_view_invocation:
        return await invoke_mounted_pane_experience_view_action(
            runtime,
            mounted_action_ref=mounted_action_ref,
            payload=payload,
        )
    if mounted_action_ref.is_interface_admission:
        return await interface_admission_actions_mod.invoke_interface_admission_action(
            runtime,
            action_key=mounted_action_ref.action_key,
            payload=payload,
        )
    if action_key == "ensure_local_service_host":
        return await ensure_local_service_host(runtime)
    if action_key == "restart_local_service_host":
        return await restart_local_service_host(runtime)
    if action_key == "interface.host.refresh_status":
        return await refresh_host_status(runtime)
    if action_key == "interface.host.restart_host":
        return await restart_host(runtime, payload=payload)
    if action_key == "ensure_local_node_runtime_started":
        return await ensure_local_node_runtime_started(runtime)
    if action_key == "tail_local_node_runtime_logs":
        return await tail_local_node_runtime_logs(
            runtime,
            line_count=_resolve_tail_line_count(payload),
        )
    if action_key == "submit_token":
        return await submit_token(runtime, payload=payload)
    if mounted_action_ref.is_api_endpoint or mounted_action_ref.is_sdk_operation:
        return _record_blocked_direct_pane_action(
            runtime,
            mounted_action_ref=mounted_action_ref,
        )
    raise RuntimeError(f"Unsupported interface action: {action_key}")


def _host_state_allows_action(
    runtime: InterfaceHostActionRuntime,
    *,
    action_key: str,
) -> bool:
    host_state = runtime.state()
    for action in host_state.allowed_actions or ():
        if action.action_key != action_key:
            continue
        return getattr(action, "enabled", True) is not False
    for capability in host_state.recovery_capabilities or ():
        if capability.action_key != action_key:
            continue
        return getattr(capability, "enabled", True) is not False
    return False


async def _perform_host_surface_action(
    runtime: InterfaceHostActionRuntime,
    *,
    action_key: str,
    payload: dict[str, object] | None,
) -> InterfaceHostServiceState | None:
    if action_key in INTERFACE_ADMISSION_ACTION_KEYS:
        return await interface_admission_actions_mod.invoke_interface_admission_action(
            runtime,
            action_key=action_key,
            payload=payload,
        )
    if action_key == "ensure_local_service_host":
        return await ensure_local_service_host(runtime)
    if action_key == "restart_local_service_host":
        return await restart_local_service_host(runtime)
    if action_key == "interface.host.refresh_status":
        return await refresh_host_status(runtime)
    if action_key == "interface.host.restart_host":
        return await restart_host(runtime, payload=payload)
    if action_key == "ensure_local_node_runtime_started":
        return await ensure_local_node_runtime_started(runtime)
    if action_key == "tail_local_node_runtime_logs":
        return await tail_local_node_runtime_logs(
            runtime,
            line_count=_resolve_tail_line_count(payload),
        )
    if action_key == "submit_token":
        return await submit_token(runtime, payload=payload)
    return None


async def invoke_mounted_pane_experience_view_action(
    runtime: InterfaceHostActionRuntime,
    *,
    mounted_action_ref: MountedPaneActionRef,
    payload: dict[str, object] | None = None,
) -> InterfaceHostServiceState:
    experience_name = _experience_name_from_view_ref(mounted_action_ref.view_ref)
    view_instance_id = mounted_action_ref.projection_experience_view_instance_id
    action_config_id = mounted_action_ref.view_invocation_action_config_id
    if experience_name is None or view_instance_id is None or action_config_id is None:
        raise RuntimeError(
            "Mounted pane action is missing Experience view invocation provenance."
        )

    request_payload = payload or {}
    try:
        sdk = _experience_sdk_for_runtime(runtime)
        response = await sdk.invoke_view_invocation_action(
            experience_name=experience_name,
            projection_experience_view_instance_id=view_instance_id,
            view_invocation_action_config_id=action_config_id,
            invocation_key=uuid4(),
            actor_id=_runtime_actor_id(runtime),
            request_payload=request_payload,
            request_ref=f"interface:{mounted_action_ref.pane_ref}:{mounted_action_ref.action_key}",
            receipt_ref="interface.experience.view_action.invoke",
        )
    except Exception as exc:
        _record_mounted_pane_experience_view_action_operation(
            runtime,
            mounted_action_ref=mounted_action_ref,
            status="failed",
            summary="Experience view action invocation failed.",
            error=str(exc),
            response_payload=None,
        )
        return runtime.state()

    succeeded = bool(getattr(response, "success", False))
    response_payload = _experience_view_action_response_payload(response)
    if succeeded:
        refresh_after_mock_operation = getattr(
            runtime,
            "_refresh_after_mock_service_adapter_operation",
            None,
        )
        if callable(refresh_after_mock_operation):
            await refresh_after_mock_operation()
        refresh_view_state_subscription = getattr(
            runtime,
            "_refresh_experience_view_state_subscription_after_action",
            None,
        )
        if callable(refresh_view_state_subscription):
            await refresh_view_state_subscription(
                mounted_action_ref=mounted_action_ref,
                request_payload=request_payload,
                response_payload=response_payload,
            )
    _record_mounted_pane_experience_view_action_operation(
        runtime,
        mounted_action_ref=mounted_action_ref,
        status="succeeded" if succeeded else "failed",
        summary=(
            "Experience view action invocation completed."
            if succeeded
            else "Experience view action invocation failed."
        ),
        error=getattr(response, "error", None),
        response_payload=response_payload,
    )
    return runtime.state()


def _experience_sdk_for_runtime(runtime: InterfaceHostActionRuntime):
    transport_session = getattr(runtime, "transport_session", None)
    transport_client = (
        getattr(transport_session, "client", None)
        if transport_session is not None
        else None
    )
    if transport_client is None:
        raise RuntimeError(
            "Interface host cannot invoke Experience view actions because no Experience API transport is bound."
        )
    return build_experience_sdk_client(
        AwareExperienceServiceApiClient(transport_client)
    )


def _runtime_actor_id(runtime: InterfaceHostActionRuntime) -> UUID | None:
    actor_context_resolver = getattr(runtime, "_resolved_service_actor_context", None)
    if callable(actor_context_resolver):
        actor_context = actor_context_resolver()
        actor_id = getattr(actor_context, "actor_id", None)
        if isinstance(actor_id, UUID):
            return actor_id
    try:
        return runtime.state().transport.actor_id
    except AttributeError:
        return None


def _experience_view_action_response_payload(response: object) -> dict[str, object]:
    return _drop_none(
        {
            "response_payload": getattr(response, "response_payload", None),
            "receipt": _model_payload(getattr(response, "receipt", None)),
            "api_dispatch_receipt": _model_payload(
                getattr(response, "api_dispatch_receipt", None)
            ),
        }
    )


def _model_payload(value: object | None) -> object | None:
    if value is None:
        return None
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json")
    return value


def _record_mounted_pane_experience_view_action_operation(
    runtime: InterfaceHostActionRuntime,
    *,
    mounted_action_ref: MountedPaneActionRef,
    status: str,
    summary: str,
    error: str | None,
    response_payload: object | None,
) -> None:
    target_ref = (
        mounted_action_ref.sdk_operation_ref
        or mounted_action_ref.api_endpoint_ref
        or mounted_action_ref.action_key
    )
    runtime._current_operation = InterfaceHostServiceOperationState(
        operation_key="experience_view_invocation_action",
        title=f"Experience view action: {target_ref}",
        status=status,
        phase="completed" if status == "succeeded" else "failed",
        current_target_id=target_ref,
        current_target_title=target_ref,
        summary=summary,
        error=error,
        running=False,
        retryable=status != "succeeded",
        updated_at=_utc_now_iso(),
        recent_activity=(
            f"{mounted_action_ref.pane_ref} -> {mounted_action_ref.action_key}",
        ),
        target_statuses=(
            InterfaceHostServiceOperationTargetState(
                target_id=target_ref,
                display_name=target_ref,
                kind="experience_view_action",
                phase="completed" if status == "succeeded" else "failed",
                is_active=True,
                is_healthy=status == "succeeded",
                summary=summary,
                error=error,
                detail_lines=_json_detail_lines(response_payload),
            ),
        ),
    )
    runtime._notify_state_changed()


def _record_blocked_direct_pane_action(
    runtime: InterfaceHostActionRuntime,
    *,
    mounted_action_ref: MountedPaneActionRef,
) -> InterfaceHostServiceState:
    target_ref = (
        mounted_action_ref.api_endpoint_ref
        or mounted_action_ref.sdk_operation_ref
        or mounted_action_ref.action_key
    )
    error = (
        "Interface pane actions require Experience view invocation provenance; "
        "direct API/SDK dispatch is retired."
    )
    runtime._current_operation = InterfaceHostServiceOperationState(
        operation_key="experience_view_invocation_required",
        title=f"Experience view action required: {target_ref}",
        status="failed",
        phase="blocked",
        current_target_id=target_ref,
        current_target_title=target_ref,
        summary="Pane action blocked before direct API/SDK dispatch.",
        error=error,
        running=False,
        retryable=True,
        updated_at=_utc_now_iso(),
        recent_activity=(
            f"{mounted_action_ref.pane_ref} -> {mounted_action_ref.action_key}",
        ),
        target_statuses=(
            InterfaceHostServiceOperationTargetState(
                target_id=target_ref,
                display_name=target_ref,
                kind="experience_view_action_required",
                phase="blocked",
                is_active=True,
                is_healthy=False,
                summary="Direct Interface API/SDK pane dispatch is retired.",
                error=error,
                detail_lines=_json_detail_lines(
                    invocation_context_for_mounted_action_ref(mounted_action_ref)
                ),
            ),
        ),
    )
    runtime._notify_state_changed()
    return runtime.state()


def _json_detail_lines(payload: object | None) -> tuple[str, ...]:
    if payload is None:
        return ()
    try:
        return (json.dumps(payload, sort_keys=True, default=str),)
    except TypeError:
        return (str(payload),)


def _workspace_control_action_error() -> RuntimeError:
    return RuntimeError(
        "Workspace lifecycle actions are not generic InterfaceHost actions. "
        "Mount a Workspace interface/pane package and dispatch its declared "
        "Experience view action."
    )


async def join_selected_workspace(
    runtime: InterfaceHostActionRuntime,
) -> InterfaceHostServiceState:
    _ = runtime
    raise _workspace_control_action_error()


async def leave_selected_workspace(
    runtime: InterfaceHostActionRuntime,
) -> InterfaceHostServiceState:
    _ = runtime
    raise _workspace_control_action_error()


async def ensure_selected_workspace_running(
    runtime: InterfaceHostActionRuntime,
) -> InterfaceHostServiceState:
    _ = runtime
    raise _workspace_control_action_error()


async def recover_selected_workspace(
    runtime: InterfaceHostActionRuntime,
) -> InterfaceHostServiceState:
    _ = runtime
    raise _workspace_control_action_error()


async def stop_selected_workspace(
    runtime: InterfaceHostActionRuntime,
) -> InterfaceHostServiceState:
    _ = runtime
    raise _workspace_control_action_error()


async def ensure_local_service_host(
    runtime: InterfaceHostActionRuntime,
) -> InterfaceHostServiceState:
    await _ensure_local_service_host(runtime)
    return runtime.state()


async def restart_local_service_host(
    runtime: InterfaceHostActionRuntime,
) -> InterfaceHostServiceState:
    await _restart_local_service_host(runtime)
    return runtime.state()


async def refresh_host_status(
    runtime: InterfaceHostActionRuntime,
) -> InterfaceHostServiceState:
    await runtime._refresh_hosted_service_status()
    await runtime._refresh_host_surface()
    return runtime.state()


async def restart_host(
    runtime: InterfaceHostActionRuntime,
    *,
    payload: dict[str, object] | None,
) -> InterfaceHostServiceState:
    await _restart_host(runtime, payload=payload)
    return runtime.state()


async def ensure_local_node_runtime_started(
    runtime: InterfaceHostActionRuntime,
) -> InterfaceHostServiceState:
    await _ensure_local_node_runtime_started(runtime)
    return runtime.state()


async def restart_local_node_runtime(
    runtime: InterfaceHostActionRuntime,
) -> InterfaceHostServiceState:
    await _restart_local_node_runtime(runtime)
    return runtime.state()


async def tail_local_node_runtime_logs(
    runtime: InterfaceHostActionRuntime,
    *,
    line_count: int,
) -> InterfaceHostServiceState:
    await _tail_local_node_runtime_logs(runtime, line_count=line_count)
    return runtime.state()


async def submit_token(
    runtime: InterfaceHostActionRuntime,
    *,
    payload: dict[str, object] | None,
) -> InterfaceHostServiceState:
    await _submit_token(runtime, payload=payload)
    return runtime.state()


async def _ensure_local_service_host(
    runtime: InterfaceHostActionRuntime,
) -> None:
    if runtime.local_runtime is None:
        raise RuntimeError(
            "Interface host service runtime is not configured for local host management."
        )
    snapshot = await runtime.local_runtime.ensure_service_host_ready()
    runtime._apply_local_runtime_snapshot(
        service_host=snapshot.service_host,
        node_runtime=snapshot.node_runtime,
    )
    await runtime._refresh_hosted_service_status()
    await runtime._refresh_host_surface()


async def _restart_local_service_host(
    runtime: InterfaceHostActionRuntime,
) -> None:
    if runtime.local_runtime is None:
        raise RuntimeError(
            "Interface host service runtime is not configured for local host management."
        )
    snapshot = await runtime.local_runtime.restart_service_host()
    runtime._apply_local_runtime_snapshot(
        service_host=snapshot.service_host,
        node_runtime=snapshot.node_runtime,
    )
    await runtime._refresh_hosted_service_status()
    await runtime._refresh_host_surface()


async def _restart_host(
    runtime: InterfaceHostActionRuntime,
    *,
    payload: dict[str, object] | None,
) -> None:
    await hosted_services_capability_mod.restart_hosted_interface_runtime(
        transport_session=runtime.transport_session,
        endpoint=runtime.endpoint,
        reason=_host_restart_reason(payload),
        evidence=_host_restart_evidence(payload),
    )
    await runtime._refresh_hosted_service_status()
    await runtime._refresh_host_surface()


async def _ensure_local_node_runtime_started(
    runtime: InterfaceHostActionRuntime,
) -> None:
    if runtime.local_runtime is None:
        raise RuntimeError(
            "Interface host service runtime is not configured for local node management."
        )
    async for snapshot in runtime.local_runtime.stream_node_runtime_start():
        runtime._apply_local_runtime_snapshot(
            service_host=snapshot.service_host,
            node_runtime=snapshot.node_runtime,
        )
        await runtime._refresh_hosted_service_status()
        await runtime._refresh_host_surface()


async def _restart_local_node_runtime(
    runtime: InterfaceHostActionRuntime,
) -> None:
    if runtime.local_runtime is None:
        raise RuntimeError(
            "Interface host service runtime is not configured for local node management."
        )
    snapshot = await runtime.local_runtime.restart_node_runtime()
    runtime._apply_local_runtime_snapshot(
        service_host=snapshot.service_host,
        node_runtime=snapshot.node_runtime,
    )
    await runtime._refresh_hosted_service_status()
    await runtime._refresh_host_surface()


async def _stop_local_node_runtime(
    runtime: InterfaceHostActionRuntime,
) -> None:
    if runtime.local_runtime is None:
        raise RuntimeError(
            "Interface host service runtime is not configured for local node management."
        )
    snapshot = await runtime.local_runtime.stop_node_runtime()
    runtime._apply_local_runtime_snapshot(
        service_host=snapshot.service_host,
        node_runtime=snapshot.node_runtime,
    )
    await runtime._refresh_hosted_service_status()
    await runtime._refresh_host_surface()


async def _tail_local_node_runtime_logs(
    runtime: InterfaceHostActionRuntime,
    *,
    line_count: int,
) -> None:
    if runtime.local_runtime is None:
        raise RuntimeError(
            "Interface host service runtime is not configured for local node management."
        )
    snapshot = await runtime.local_runtime.tail_node_runtime_logs(line_count=line_count)
    runtime._apply_local_runtime_snapshot(
        service_host=snapshot.service_host,
        node_runtime=snapshot.node_runtime,
    )
    await runtime._refresh_hosted_service_status()
    await runtime._refresh_host_surface()


async def _submit_token(
    runtime: InterfaceHostActionRuntime,
    *,
    payload: dict[str, object] | None,
) -> None:
    transport_session = runtime.transport_session
    if transport_session is None:
        raise RuntimeError(
            "Interface host service runtime is missing a transport session; cannot submit auth token."
        )
    token = _resolve_required_token(payload)
    login = await transport_session.login_with_token(token=token)
    runtime._authenticated = login.actor_id is not None
    await runtime._refresh_hosted_service_status()
    await runtime._refresh_host_surface()


__all__ = [
    "InterfaceHostActionRuntime",
    "MountedPaneActionRef",
    "ensure_local_node_runtime_started",
    "ensure_local_service_host",
    "ensure_selected_workspace_running",
    "join_selected_workspace",
    "leave_selected_workspace",
    "perform_action",
    "recover_selected_workspace",
    "refresh_host_status",
    "restart_host",
    "restart_local_node_runtime",
    "restart_local_service_host",
    "resolve_mounted_pane_action_ref",
    "stop_selected_workspace",
    "submit_token",
    "tail_local_node_runtime_logs",
]
