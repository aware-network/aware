from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from aware_experience_service_dto.experience.view_state.models import (
    ExperienceViewStateEvent,
    ExperienceViewStateSnapshot,
)
from aware_experience_service_dto.experience.session_view_frame.service_operation import (
    ResolveExperienceSessionViewFrameRequest,
)
from aware_experience_service_dto.experience.view_state.service_operation import (
    WatchExperienceViewStateRequest,
    WatchExperienceViewStateResponse,
)
from aware_interface import (
    InterfaceMaterializedPaneState,
    InterfaceResolvedPaneDescriptor,
    InterfaceRuntimeState,
)


WatchExperienceViewStateCallable = Callable[
    [WatchExperienceViewStateRequest],
    Awaitable[WatchExperienceViewStateResponse],
]


@dataclass(frozen=True, slots=True)
class InterfaceViewStateSubscriptionHydrationResult:
    runtime_state: InterfaceRuntimeState
    hydrated_count: int = 0
    skipped_count: int = 0
    errors: tuple[str, ...] = ()

    @property
    def changed(self) -> bool:
        return self.runtime_state is not None and self.hydrated_count > 0


async def hydrate_experience_view_state_subscriptions(
    *,
    runtime_state: InterfaceRuntimeState,
    watch_experience_view_state: WatchExperienceViewStateCallable,
    provider_contexts_by_pane_state_key: (
        Mapping[str, Mapping[str, object]] | None
    ) = None,
    session_view_frame_requests_by_pane_state_key: (
        Mapping[str, ResolveExperienceSessionViewFrameRequest] | None
    ) = None,
    materialized_at: str | None = None,
) -> InterfaceViewStateSubscriptionHydrationResult:
    contexts = provider_contexts_by_pane_state_key or {}
    frame_requests = session_view_frame_requests_by_pane_state_key or {}
    next_state = runtime_state
    hydrated_count = 0
    skipped_count = 0
    errors: list[str] = []
    for pane in runtime_state.resolved_panes:
        pane_state_key = _pane_state_key_for_descriptor(pane)
        provider_context = contexts.get(pane_state_key)
        if not _pane_supports_experience_view_state_subscription(
            pane=pane,
            provider_context=provider_context,
        ):
            skipped_count += 1
            continue
        session_view_frame_request = frame_requests.get(pane_state_key)
        if session_view_frame_request is None:
            errors.append(f"{pane_state_key}: session_view_frame_request_required")
            skipped_count += 1
            continue
        request = watch_request_for_pane(
            pane=pane,
            session_view_frame_request=session_view_frame_request,
            provider_context=provider_context,
        )
        try:
            response = await watch_experience_view_state(request)
        except Exception as exc:
            errors.append(f"{pane_state_key}: {exc}")
            continue
        next_state = apply_experience_view_state_event(
            runtime_state=next_state,
            event=ExperienceViewStateEvent(snapshot=response.snapshot),
            pane=pane,
            materialized_at=materialized_at,
        )
        hydrated_count += 1
    return InterfaceViewStateSubscriptionHydrationResult(
        runtime_state=next_state,
        hydrated_count=hydrated_count,
        skipped_count=skipped_count,
        errors=tuple(errors),
    )


async def refresh_experience_view_state_subscription(
    *,
    runtime_state: InterfaceRuntimeState,
    pane: InterfaceResolvedPaneDescriptor,
    watch_experience_view_state: WatchExperienceViewStateCallable,
    provider_contexts_by_pane_state_key: (
        Mapping[str, Mapping[str, object]] | None
    ) = None,
    session_view_frame_request: ResolveExperienceSessionViewFrameRequest | None = None,
    refresh_trigger: Mapping[str, object] | None = None,
    materialized_at: str | None = None,
) -> InterfaceViewStateSubscriptionHydrationResult:
    pane_state_key = _pane_state_key_for_descriptor(pane)
    provider_context = (provider_contexts_by_pane_state_key or {}).get(pane_state_key)
    if not _pane_supports_experience_view_state_subscription(
        pane=pane,
        provider_context=provider_context,
    ):
        return InterfaceViewStateSubscriptionHydrationResult(
            runtime_state=runtime_state,
            skipped_count=1,
        )
    if session_view_frame_request is None:
        return InterfaceViewStateSubscriptionHydrationResult(
            runtime_state=runtime_state,
            skipped_count=1,
            errors=(f"{pane_state_key}: session_view_frame_request_required",),
        )
    known_cursor, known_digest = _known_view_state_cursor_for_pane(
        runtime_state=runtime_state,
        pane_state_key=pane_state_key,
    )
    request = watch_request_for_pane(
        pane=pane,
        session_view_frame_request=session_view_frame_request,
        provider_context=_provider_context_with_refresh_trigger(
            provider_context=provider_context,
            refresh_trigger=refresh_trigger,
        ),
        known_cursor=known_cursor,
        known_digest=known_digest,
    )
    try:
        response = await watch_experience_view_state(request)
    except Exception as exc:
        return InterfaceViewStateSubscriptionHydrationResult(
            runtime_state=runtime_state,
            errors=(f"{pane_state_key}: {exc}",),
        )
    next_state = apply_experience_view_state_event(
        runtime_state=runtime_state,
        event=ExperienceViewStateEvent(snapshot=response.snapshot),
        pane=pane,
        materialized_at=materialized_at,
    )
    return InterfaceViewStateSubscriptionHydrationResult(
        runtime_state=next_state,
        hydrated_count=1,
    )


def watch_request_for_pane(
    *,
    pane: InterfaceResolvedPaneDescriptor,
    session_view_frame_request: ResolveExperienceSessionViewFrameRequest,
    provider_context: Mapping[str, object] | None = None,
    known_cursor: str | None = None,
    known_digest: str | None = None,
) -> WatchExperienceViewStateRequest:
    scope = session_view_frame_request.session_scope
    return WatchExperienceViewStateRequest(
        experience_name=scope.experience_name,
        session_view_frame_request=session_view_frame_request,
        projection_experience_view_instance_id=(
            pane.projection_experience_view_instance_id
        ),
        provider_context=_pane_provider_context(
            pane=pane,
            extra_context=provider_context,
        ),
        known_cursor=known_cursor,
        known_digest=known_digest,
    )


def pane_for_mounted_action_ref(
    *,
    runtime_state: InterfaceRuntimeState,
    mounted_action_ref: object,
) -> InterfaceResolvedPaneDescriptor | None:
    view_instance_id = getattr(
        mounted_action_ref,
        "projection_experience_view_instance_id",
        None,
    )
    view_ref = _optional_text(getattr(mounted_action_ref, "view_ref", None))
    pane_config_id = getattr(mounted_action_ref, "pane_config_id", None)
    for pane in runtime_state.resolved_panes:
        if (
            view_instance_id is not None
            and pane.projection_experience_view_instance_id == view_instance_id
        ):
            return pane
    for pane in runtime_state.resolved_panes:
        if view_ref is not None and pane.view_ref != view_ref:
            continue
        if pane_config_id is not None and pane.pane_config_id == pane_config_id:
            return pane
        if _pane_matches_action_ref(pane=pane, mounted_action_ref=mounted_action_ref):
            return pane
    return None


def materialized_pane_state_from_experience_view_state(
    *,
    pane: InterfaceResolvedPaneDescriptor,
    snapshot: ExperienceViewStateSnapshot,
    materialized_at: str | None = None,
) -> InterfaceMaterializedPaneState:
    provenance = _view_state_provenance(pane=pane, snapshot=snapshot)
    return InterfaceMaterializedPaneState(
        pane_state_key=_pane_state_key_for_descriptor(pane),
        window_key=pane.window_key,
        layout_key=pane.layout_key,
        section_key=pane.section_key,
        pane_kind=pane.pane_kind,
        pane_config_id=pane.pane_config_id,
        pane_package_id=pane.pane_package_id,
        focus_scope_id=pane.focus_scope_id,
        branch_id=pane.branch_id,
        projection_experience_view_id=(
            snapshot.projection_experience_view_id or pane.projection_experience_view_id
        ),
        projection_view_id=pane.projection_view_id,
        state_model_id=snapshot.state_model_id or pane.state_model_id,
        projection_hash=pane.state_projection_hash,
        status=snapshot.status,
        head_commit_id=_optional_text(snapshot.provenance.get("head_commit_id")),
        graph_hash_post=_optional_text(snapshot.provenance.get("graph_hash_post")),
        materialized_at=materialized_at or snapshot.observed_at or _utc_now_iso(),
        state=dict(snapshot.state),
        provenance=provenance,
        error=snapshot.error,
    )


def apply_experience_view_state_event(
    *,
    runtime_state: InterfaceRuntimeState,
    event: ExperienceViewStateEvent,
    pane: InterfaceResolvedPaneDescriptor | None = None,
    materialized_at: str | None = None,
) -> InterfaceRuntimeState:
    resolved_pane = pane or _resolve_pane_for_snapshot(
        runtime_state=runtime_state,
        snapshot=event.snapshot,
    )
    pane_state = materialized_pane_state_from_experience_view_state(
        pane=resolved_pane,
        snapshot=event.snapshot,
        materialized_at=materialized_at,
    )
    return replace(
        runtime_state,
        materialized_pane_states=_replace_materialized_pane_state(
            runtime_state.materialized_pane_states,
            pane_state,
        ),
    )


def _resolve_pane_for_snapshot(
    *,
    runtime_state: InterfaceRuntimeState,
    snapshot: ExperienceViewStateSnapshot,
) -> InterfaceResolvedPaneDescriptor:
    for pane in runtime_state.resolved_panes:
        if _pane_matches_snapshot(pane=pane, snapshot=snapshot):
            return pane
    raise ValueError(
        "Experience view-state event does not match any resolved Interface pane."
    )


def _pane_supports_experience_view_state_subscription(
    *,
    pane: InterfaceResolvedPaneDescriptor,
    provider_context: Mapping[str, object] | None,
) -> bool:
    source_kind = _optional_text(pane.state_source_kind)
    if source_kind == "experience_view_state":
        return True
    provider_kind = _optional_text(pane.state_provider_kind)
    if provider_kind in {"service_operation", "service_endpoint"}:
        return True
    if provider_context is None:
        return False
    return bool(
        _optional_text(provider_context.get("api_package_name"))
        and _optional_text(provider_context.get("endpoint_ref"))
    )


def _pane_matches_snapshot(
    *,
    pane: InterfaceResolvedPaneDescriptor,
    snapshot: ExperienceViewStateSnapshot,
) -> bool:
    if (
        snapshot.projection_experience_view_instance_id is not None
        and pane.projection_experience_view_instance_id
        == snapshot.projection_experience_view_instance_id
    ):
        return True
    if snapshot.view_ref and pane.view_ref == snapshot.view_ref:
        return True
    if (
        snapshot.projection_view_key
        and pane.projection_view_key == snapshot.projection_view_key
    ):
        return True
    return False


def _pane_matches_action_ref(
    *,
    pane: InterfaceResolvedPaneDescriptor,
    mounted_action_ref: object,
) -> bool:
    return (
        pane.window_key == getattr(mounted_action_ref, "window_key", None)
        and pane.layout_key == getattr(mounted_action_ref, "layout_key", None)
        and pane.section_key == getattr(mounted_action_ref, "section_key", None)
        and pane.pane_kind == getattr(mounted_action_ref, "pane_kind", None)
    )


def _pane_provider_context(
    *,
    pane: InterfaceResolvedPaneDescriptor,
    extra_context: Mapping[str, object] | None,
) -> dict[str, object]:
    context: dict[str, object] = {
        "provider_ref": pane.state_provider_ref,
        "provider_kind": pane.state_provider_kind,
        "projection_experience_view_id": _optional_text(
            pane.projection_experience_view_id
        ),
        "projection_experience_view_instance_id": _optional_text(
            pane.projection_experience_view_instance_id
        ),
        "state_model_id": _optional_text(pane.state_model_id),
        "pane_state_key": _pane_state_key_for_descriptor(pane),
        "pane_kind": pane.pane_kind,
    }
    if extra_context is not None:
        context.update(dict(extra_context))
    return {key: value for key, value in context.items() if value is not None}


def _provider_context_with_refresh_trigger(
    *,
    provider_context: Mapping[str, object] | None,
    refresh_trigger: Mapping[str, object] | None,
) -> dict[str, object] | None:
    if provider_context is None and refresh_trigger is None:
        return None
    context = dict(provider_context or {})
    if refresh_trigger is None:
        return context
    trigger_payload = _json_payload_object(refresh_trigger)
    context["refresh_trigger"] = trigger_payload
    provider_input = _json_payload_object(context.get("provider_input"))
    provenance = _json_payload_object(provider_input.get("provenance"))
    provenance["experience_view_action_completion"] = trigger_payload
    provider_input["provenance"] = provenance
    context["provider_input"] = provider_input
    return context


def _view_state_provenance(
    *,
    pane: InterfaceResolvedPaneDescriptor,
    snapshot: ExperienceViewStateSnapshot,
) -> dict[str, object]:
    provenance: dict[str, object] = {
        "source_kind": "experience_view_state_subscription",
        "experience_name": snapshot.experience_name,
        "view_ref": snapshot.view_ref,
        "projection_view_key": snapshot.projection_view_key,
        "state_model_ref": snapshot.state_model_ref,
        "cursor": snapshot.cursor,
        "digest": snapshot.digest,
        "session_view_frame_digest": snapshot.session_view_frame_digest,
        "change_reason": snapshot.change_reason,
        "sequence": snapshot.sequence,
        "observed_at": snapshot.observed_at,
        "pane_view_ref": pane.view_ref,
        "pane_projection_view_key": pane.projection_view_key,
        "pane_state_provider_ref": pane.state_provider_ref,
        "pane_state_provider_kind": pane.state_provider_kind,
    }
    if snapshot.projection_experience_view_instance_id is not None:
        provenance["projection_experience_view_instance_id"] = str(
            snapshot.projection_experience_view_instance_id
        )
    frame = snapshot.session_view_frame
    if frame is not None:
        provenance["session_view_frame"] = _json_payload_object(frame)
        if frame.lens is not None:
            provenance["session_view_frame_lens"] = _json_payload_object(frame.lens)
        for key in (
            "environment_session_id",
            "environment_navigation_context_id",
            "environment_session_thread_id",
            "environment_session_attention_session_id",
            "attention_session_id",
            "active_attention_focus_transition_id",
            "thread_layout_id",
        ):
            value = getattr(frame, key, None)
            if value is not None:
                provenance[key] = str(value)
    if snapshot.provider is not None:
        provenance["provider"] = _json_payload(snapshot.provider)
    if snapshot.provenance:
        provenance["experience_provenance"] = dict(snapshot.provenance)
    return {key: value for key, value in provenance.items() if value is not None}


def _pane_state_key_for_descriptor(pane: InterfaceResolvedPaneDescriptor) -> str:
    return ":".join(
        (
            pane.window_key,
            pane.layout_key,
            pane.section_key,
            pane.pane_kind,
            str(pane.pane_config_id or ""),
            pane.state_projection_hash or "",
        )
    )


def _replace_materialized_pane_state(
    existing: tuple[InterfaceMaterializedPaneState, ...],
    pane_state: InterfaceMaterializedPaneState,
) -> tuple[InterfaceMaterializedPaneState, ...]:
    replaced = False
    next_states: list[InterfaceMaterializedPaneState] = []
    for item in existing:
        if item.pane_state_key == pane_state.pane_state_key:
            next_states.append(pane_state)
            replaced = True
        else:
            next_states.append(item)
    if not replaced:
        next_states.append(pane_state)
    return tuple(next_states)


def _known_view_state_cursor_for_pane(
    *,
    runtime_state: InterfaceRuntimeState,
    pane_state_key: str,
) -> tuple[str | None, str | None]:
    for state in runtime_state.materialized_pane_states:
        if state.pane_state_key != pane_state_key:
            continue
        provenance = state.provenance or {}
        return (
            _optional_text(provenance.get("cursor")),
            _optional_text(provenance.get("digest")),
        )
    return None, None


def _json_payload_object(value: object) -> dict[str, object]:
    if value is None:
        return {}
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json", exclude_none=True)
    if not isinstance(value, Mapping):
        return {"value": _json_value(value)}
    return {
        str(key): _json_value(item) for key, item in value.items() if item is not None
    }


def _json_payload(value: BaseModel | dict[str, object]) -> dict[str, object]:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=True)
    return dict(value)


def _json_value(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, BaseModel):
        return _json_payload_object(value)
    if isinstance(value, Mapping):
        return _json_payload_object(value)
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return str(value)


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _required_text(value: Any, label: str) -> str:
    text = _optional_text(value)
    if text is None:
        raise RuntimeError(f"{label} is required.")
    return text


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = [
    "InterfaceViewStateSubscriptionHydrationResult",
    "apply_experience_view_state_event",
    "hydrate_experience_view_state_subscriptions",
    "materialized_pane_state_from_experience_view_state",
    "pane_for_mounted_action_ref",
    "refresh_experience_view_state_subscription",
    "watch_request_for_pane",
]
