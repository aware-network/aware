from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable, Mapping
from datetime import datetime, timezone
import hashlib
from importlib import import_module
import json
from typing import Any, Protocol, cast

from pydantic import BaseModel

from aware_experience_service.session_context_service import (
    EnvironmentSessionContextApiClient,
    IdentityExperienceSessionApiClient,
)
from aware_experience_service.session_view_frame_service import (
    ResolveExperienceSessionViewFrameRequestSpec,
    resolve_experience_session_view_frame,
)
from aware_experience_service_dto.experience.session_view_frame.models import (
    ExperienceSessionViewFrame,
)
from aware_experience_service_dto.experience.view_state.models import (
    ExperienceViewStateEvent,
    ExperienceViewStateProviderProvenance,
    ExperienceViewStateSnapshot,
)
from aware_experience_service_dto.experience.view_state.service_operation import (
    WatchExperienceViewStateRequest,
    WatchExperienceViewStateResponse,
)
from aware_service_runtime.api_ingress.host_context import ServiceApiHostContext
from aware_service_runtime.local_service_host_api_client import (
    build_service_api_client_for_api_package,
    build_service_api_client_for_route,
)
from aware_service_runtime.view_provider_routes import (
    ServiceViewProviderRouteDescriptor,
    resolve_service_view_provider_route,
)


class ExperienceViewStateApiInvoker(Protocol):
    async def invoke_api_endpoint_raw(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: BaseModel | Mapping[str, Any],
        timeout_s: float | None = None,
    ) -> object: ...


ViewStateProviderCallable = Callable[..., object]
_SESSION_VIEW_FRAME_REQUIRED_ERROR = (
    "Experience view-state watch requires session_view_frame_request."
)


class ExperienceViewStateBackend(Protocol):
    async def resolve_view_state(
        self,
        *,
        request: WatchExperienceViewStateRequest,
        host_context: ServiceApiHostContext,
    ) -> ExperienceViewStateSnapshot: ...

    def stream_view_state(
        self,
        *,
        request: WatchExperienceViewStateRequest,
        host_context: ServiceApiHostContext,
    ) -> AsyncIterator[ExperienceViewStateEvent]: ...


class RouteBackedExperienceViewStateBackend:
    def __init__(
        self,
        *,
        api_invokers_by_package: (
            Mapping[str, ExperienceViewStateApiInvoker] | None
        ) = None,
        provider_callables: Mapping[str, ViewStateProviderCallable] | None = None,
    ) -> None:
        self._api_invokers_by_package = {
            key.strip().casefold(): value
            for key, value in (api_invokers_by_package or {}).items()
            if key.strip()
        }
        self._provider_callables = {
            key.strip(): value
            for key, value in (provider_callables or {}).items()
            if key.strip()
        }

    async def resolve_view_state(
        self,
        *,
        request: WatchExperienceViewStateRequest,
        host_context: ServiceApiHostContext,
    ) -> ExperienceViewStateSnapshot:
        provider_context, provider_route = _provider_context_with_route_defaults(
            request=request,
            host_context=host_context,
        )
        api_view_ref = _required_api_view_ref(
            request=request,
            provider_context=provider_context,
        )
        api_package_name = _context_text(provider_context, "api_package_name")
        endpoint_ref = _context_text(provider_context, "endpoint_ref")
        discriminant = _context_text(provider_context, "discriminant") or endpoint_ref
        request_payload = _context_mapping(provider_context, "request_payload")
        if request_payload is None:
            request_payload = {}
        provider_ref = _context_text(provider_context, "provider_ref")
        if endpoint_ref is None:
            if provider_ref is None:
                raise RuntimeError(
                    "Experience route-backed view-state provider requires "
                    "provider_context.provider_ref when no transport "
                    "endpoint_ref is present: " + f"api_view_ref={api_view_ref!r}"
                )
            response = None
            response_payload = (
                _context_mapping(
                    provider_context,
                    "response_payload",
                )
                or {}
            )
        else:
            if api_package_name is None:
                raise RuntimeError(
                    "Experience route-backed view-state provider transport "
                    "requires provider_context.api_package_name when "
                    "endpoint_ref is present."
                )
            invoker = self._api_invoker(
                api_package_name=api_package_name,
                host_context=host_context,
                provider_route=provider_route,
            )
            response = await invoker.invoke_api_endpoint_raw(
                endpoint_ref=endpoint_ref,
                discriminant=discriminant or endpoint_ref,
                request_payload=request_payload,
                timeout_s=_context_float(provider_context, "timeout_s"),
            )
            response_payload = _response_payload(response)
        raw_state = (
            _provider_state(
                provider_ref=provider_ref,
                provider_callables=self._provider_callables,
                provider_input=_provider_input(
                    request=request,
                    api_view_ref=api_view_ref,
                    endpoint_ref=endpoint_ref,
                    api_package_name=api_package_name,
                    response_payload=response_payload,
                    provider_context=provider_context,
                ),
            )
            if provider_ref is not None
            else response_payload
        )
        state_payload, state_model_ref = _validated_state_payload(
            raw_state=raw_state,
            view_ref=_context_text(provider_context, "view_ref"),
            projection_view_key=_context_text(
                provider_context,
                "projection_view_key",
            ),
            provider_context=provider_context,
        )
        status = _state_status(
            state_payload=state_payload,
            response=response,
            response_payload=response_payload,
        )
        return ExperienceViewStateSnapshot(
            experience_name=request.experience_name,
            view_ref=_required_context_text(
                provider_context,
                "view_ref",
            ),
            projection_view_key=(
                _context_text(provider_context, "projection_view_key")
                or _optional_payload_text(state_payload, "VIEW_KEY")
            ),
            projection_experience_view_id=_context_uuid(
                provider_context,
                "projection_experience_view_id",
            ),
            projection_experience_view_instance_id=(
                request.projection_experience_view_instance_id
            ),
            state_model_ref=(
                state_model_ref
                or _context_text(provider_context, "state_model_ref")
                or _optional_payload_text(state_payload, "STATE_MODEL_REF")
            ),
            provider=ExperienceViewStateProviderProvenance(
                provider_kind=(
                    _context_text(provider_context, "provider_kind")
                    or "service_operation"
                ),
                provider_ref=provider_ref,
                service_name=_context_text(provider_context, "service_name"),
                api_view_ref=api_view_ref,
                api_view_id=_context_uuid(provider_context, "api_view_id"),
                endpoint_ref=endpoint_ref,
                discriminant=discriminant,
                service_operation_config_api_view_id=_context_uuid(
                    provider_context,
                    "service_operation_config_api_view_id",
                ),
                evidence=_provider_evidence(
                    api_package_name=api_package_name,
                    api_view_ref=api_view_ref,
                    provider_route=provider_route,
                ),
            ),
            status=status,
            state=state_payload,
            observed_at=_utc_now_iso(),
            provenance={
                "source": "route_backed_experience_view_state_backend",
                "api_package_name": api_package_name,
                "api_view_ref": api_view_ref,
                "endpoint_ref": endpoint_ref,
                "discriminant": discriminant,
                "response_status": _response_status(response),
            },
        )

    def _api_invoker(
        self,
        *,
        api_package_name: str,
        host_context: ServiceApiHostContext,
        provider_route: ServiceViewProviderRouteDescriptor | None = None,
    ) -> ExperienceViewStateApiInvoker:
        configured = self._api_invokers_by_package.get(
            api_package_name.strip().casefold()
        )
        if configured is not None:
            return configured
        if provider_route is not None:
            return cast(
                ExperienceViewStateApiInvoker,
                build_service_api_client_for_route(
                    provider_route.api_route,
                    actor_id=host_context.operation_context.actor_id,
                    invocation_context={
                        "source": "experience.view_state.watch",
                        "experience_service": host_context.service_name,
                    },
                ),
            )
        invoker = build_service_api_client_for_api_package(
            host_context.service_api_dependency_routes,
            api_package_name=api_package_name,
            consumer_service_package_id=host_context.service_package_id,
            consumer_service_package_name=host_context.service_package_name,
            actor_id=host_context.operation_context.actor_id,
            invocation_context={
                "source": "experience.view_state.watch",
                "experience_service": host_context.service_name,
            },
        )
        if invoker is None:
            raise RuntimeError(
                "Experience view-state provider route is unavailable: "
                + f"api_package_name={api_package_name!r}"
            )
        return cast(ExperienceViewStateApiInvoker, invoker)


async def watch_experience_view_state(
    *,
    request: WatchExperienceViewStateRequest,
    host_context: ServiceApiHostContext,
    backend: ExperienceViewStateBackend | None,
    identity_api_client: IdentityExperienceSessionApiClient | None = None,
    environment_api_client: EnvironmentSessionContextApiClient | None = None,
) -> WatchExperienceViewStateResponse:
    snapshot = await _resolve_snapshot(
        request=request,
        host_context=host_context,
        backend=backend,
        sequence=0,
        identity_api_client=identity_api_client,
        environment_api_client=environment_api_client,
    )
    return WatchExperienceViewStateResponse(
        request_id=request.request_id,
        success=_snapshot_success(snapshot),
        error=snapshot.error,
        experience_name=request.experience_name,
        snapshot=snapshot,
        changed=_view_state_changed(
            snapshot=snapshot,
            known_cursor=request.known_cursor,
            known_digest=request.known_digest,
        ),
    )


async def stream_watch_experience_view_state(
    *,
    request: WatchExperienceViewStateRequest,
    host_context: ServiceApiHostContext,
    backend: ExperienceViewStateBackend | None,
    identity_api_client: IdentityExperienceSessionApiClient | None = None,
    environment_api_client: EnvironmentSessionContextApiClient | None = None,
) -> AsyncIterator[ExperienceViewStateEvent]:
    if backend is not None:
        stream_view_state = getattr(backend, "stream_view_state", None)
        if callable(stream_view_state):
            session_view_frame = await _resolve_session_view_frame(
                request=request,
                host_context=host_context,
                identity_api_client=identity_api_client,
                environment_api_client=environment_api_client,
            )
            if session_view_frame is None:
                yield ExperienceViewStateEvent(
                    snapshot=_error_snapshot(
                        request=request,
                        error=_SESSION_VIEW_FRAME_REQUIRED_ERROR,
                        sequence=0,
                    )
                )
                return
            if _session_view_frame_is_blocked(session_view_frame):
                yield ExperienceViewStateEvent(
                    snapshot=_blocked_session_view_frame_snapshot(
                        request=request,
                        session_view_frame=session_view_frame,
                        sequence=0,
                    )
                )
                return
            effective_request = _request_with_session_view_frame_defaults(
                request=request,
                session_view_frame=session_view_frame,
            )
            async for event in stream_view_state(
                request=effective_request,
                host_context=host_context,
            ):
                yield _event_with_snapshot_defaults(
                    event,
                    request=effective_request,
                    session_view_frame=session_view_frame,
                )
            return

    last_signature = request.known_digest or request.known_cursor
    sequence = 0
    poll_interval_s = max(request.poll_interval_ms / 1000.0, 0.25)
    while True:
        snapshot = await _resolve_snapshot(
            request=request,
            host_context=host_context,
            backend=backend,
            sequence=sequence,
            identity_api_client=identity_api_client,
            environment_api_client=environment_api_client,
        )
        signature = snapshot.digest or snapshot.cursor
        if signature != last_signature:
            yield ExperienceViewStateEvent(snapshot=snapshot)
            last_signature = signature
            sequence += 1
        await asyncio.sleep(poll_interval_s)


async def _resolve_snapshot(
    *,
    request: WatchExperienceViewStateRequest,
    host_context: ServiceApiHostContext,
    backend: ExperienceViewStateBackend | None,
    sequence: int,
    identity_api_client: IdentityExperienceSessionApiClient | None = None,
    environment_api_client: EnvironmentSessionContextApiClient | None = None,
) -> ExperienceViewStateSnapshot:
    session_view_frame = await _resolve_session_view_frame(
        request=request,
        host_context=host_context,
        identity_api_client=identity_api_client,
        environment_api_client=environment_api_client,
    )
    if session_view_frame is None:
        return _error_snapshot(
            request=request,
            error=_SESSION_VIEW_FRAME_REQUIRED_ERROR,
            sequence=sequence,
        )
    if _session_view_frame_is_blocked(session_view_frame):
        return _blocked_session_view_frame_snapshot(
            request=request,
            session_view_frame=session_view_frame,
            sequence=sequence,
        )
    effective_request = _request_with_session_view_frame_defaults(
        request=request,
        session_view_frame=session_view_frame,
    )
    if backend is None:
        return _error_snapshot(
            request=effective_request,
            error="Experience view-state watch requires a provider backend.",
            sequence=sequence,
            session_view_frame=session_view_frame,
        )
    try:
        snapshot = await backend.resolve_view_state(
            request=effective_request,
            host_context=host_context,
        )
    except Exception as exc:
        return _error_snapshot(
            request=effective_request,
            error=str(exc),
            sequence=sequence,
            session_view_frame=session_view_frame,
        )
    return _snapshot_with_defaults(
        snapshot,
        request=effective_request,
        sequence=sequence,
        session_view_frame=session_view_frame,
    )


def _event_with_snapshot_defaults(
    event: ExperienceViewStateEvent,
    *,
    request: WatchExperienceViewStateRequest,
    session_view_frame: ExperienceSessionViewFrame | None,
) -> ExperienceViewStateEvent:
    snapshot = event.snapshot
    return event.model_copy(
        update={
            "snapshot": _snapshot_with_defaults(
                snapshot,
                request=request,
                sequence=snapshot.sequence,
                session_view_frame=session_view_frame,
            )
        }
    )


def _snapshot_with_defaults(
    snapshot: ExperienceViewStateSnapshot,
    *,
    request: WatchExperienceViewStateRequest,
    sequence: int,
    session_view_frame: ExperienceSessionViewFrame | None,
) -> ExperienceViewStateSnapshot:
    update: dict[str, object] = {}
    if not snapshot.experience_name:
        update["experience_name"] = request.experience_name
    if session_view_frame is not None:
        session_view_frame_digest = _session_view_frame_digest(session_view_frame)
        if snapshot.session_view_frame is None:
            update["session_view_frame"] = session_view_frame
        if snapshot.session_view_frame_digest != session_view_frame_digest:
            update["session_view_frame_digest"] = session_view_frame_digest
        if not snapshot.change_reason or snapshot.change_reason == "initial":
            update["change_reason"] = "frame_state_resolved"
    if snapshot.sequence == 0 and sequence:
        update["sequence"] = sequence
    if not snapshot.observed_at:
        update["observed_at"] = _utc_now_iso()
    if update:
        snapshot = snapshot.model_copy(update=update)
    return _snapshot_with_digest(snapshot)


def _snapshot_with_digest(
    snapshot: ExperienceViewStateSnapshot,
) -> ExperienceViewStateSnapshot:
    session_view_frame_digest = snapshot.session_view_frame_digest or (
        _session_view_frame_digest(snapshot.session_view_frame)
        if snapshot.session_view_frame is not None
        else None
    )
    digest = snapshot.digest or _stable_digest(
        {
            "experience_name": snapshot.experience_name,
            "view_ref": snapshot.view_ref,
            "projection_view_key": snapshot.projection_view_key,
            "session_view_frame_digest": session_view_frame_digest,
            "state_model_ref": snapshot.state_model_ref,
            "provider": _model_payload(snapshot.provider),
            "status": snapshot.status,
            "state": dict(snapshot.state),
            "change_reason": snapshot.change_reason,
            "provenance": dict(snapshot.provenance),
            "error": snapshot.error,
        }
    )
    cursor = snapshot.cursor or f"experience-view-state:{digest}"
    if snapshot.digest == digest and snapshot.cursor == cursor:
        if snapshot.session_view_frame_digest == session_view_frame_digest:
            return snapshot
    return snapshot.model_copy(
        update={
            "digest": digest,
            "cursor": cursor,
            "session_view_frame_digest": session_view_frame_digest,
        }
    )


def _error_snapshot(
    *,
    request: WatchExperienceViewStateRequest,
    error: str,
    sequence: int,
    session_view_frame: ExperienceSessionViewFrame | None = None,
) -> ExperienceViewStateSnapshot:
    return _snapshot_with_digest(
        ExperienceViewStateSnapshot(
            experience_name=request.experience_name,
            view_ref=_context_text(request.provider_context, "view_ref") or "unknown",
            projection_experience_view_instance_id=(
                request.projection_experience_view_instance_id
            ),
            session_view_frame=session_view_frame,
            session_view_frame_digest=(
                _session_view_frame_digest(session_view_frame)
                if session_view_frame is not None
                else None
            ),
            status="error",
            state={},
            change_reason="error",
            sequence=sequence,
            observed_at=_utc_now_iso(),
            provenance={
                "source": "aware_experience_service.view_state_watch",
                "provider_context": dict(request.provider_context),
            },
            error=error,
        )
    )


def _blocked_session_view_frame_snapshot(
    *,
    request: WatchExperienceViewStateRequest,
    session_view_frame: ExperienceSessionViewFrame,
    sequence: int,
) -> ExperienceViewStateSnapshot:
    blockers = _session_view_frame_blockers(session_view_frame)
    error = (
        session_view_frame.error
        or (blockers[0] if blockers else None)
        or "experience_session_view_frame_blocked"
    )
    lens = session_view_frame.lens
    return _snapshot_with_digest(
        ExperienceViewStateSnapshot(
            experience_name=request.experience_name,
            view_ref=(
                getattr(lens, "view_ref", None)
                or _context_text(request.provider_context, "view_ref")
                or "unknown"
            ),
            projection_view_key=(
                getattr(lens, "projection_view_key", None)
                or _context_text(request.provider_context, "projection_view_key")
            ),
            projection_experience_view_instance_id=(
                request.projection_experience_view_instance_id
            ),
            session_view_frame=session_view_frame,
            session_view_frame_digest=_session_view_frame_digest(session_view_frame),
            status="blocked",
            state={},
            change_reason="session_view_frame_blocked",
            sequence=sequence,
            observed_at=_utc_now_iso(),
            provenance={
                "source": "aware_experience_service.view_state_watch",
                "blocked_boundary": "session_view_frame",
                "session_view_frame_status": session_view_frame.status,
                "session_view_frame_blockers": blockers,
                "provider_context": dict(request.provider_context),
            },
            error=error,
        )
    )


def _snapshot_success(snapshot: ExperienceViewStateSnapshot) -> bool:
    return snapshot.status.strip().casefold() not in {"blocked", "error"}


def _view_state_changed(
    *,
    snapshot: ExperienceViewStateSnapshot,
    known_cursor: str | None,
    known_digest: str | None,
) -> bool:
    normalized_cursor = (known_cursor or "").strip()
    normalized_digest = (known_digest or "").strip()
    if normalized_cursor and normalized_cursor == snapshot.cursor:
        return False
    if normalized_digest and normalized_digest == snapshot.digest:
        return False
    return True


async def _resolve_session_view_frame(
    *,
    request: WatchExperienceViewStateRequest,
    host_context: ServiceApiHostContext,
    identity_api_client: IdentityExperienceSessionApiClient | None,
    environment_api_client: EnvironmentSessionContextApiClient | None,
) -> ExperienceSessionViewFrame | None:
    session_view_frame_request = getattr(request, "session_view_frame_request", None)
    if session_view_frame_request is None:
        return None
    response = await resolve_experience_session_view_frame(
        request=_session_view_frame_request_spec(session_view_frame_request),
        host_context=host_context,
        identity_api_client=identity_api_client,
        environment_api_client=environment_api_client,
    )
    return ExperienceSessionViewFrame.model_validate(
        response.frame.model_dump(mode="json", exclude_none=True)
    )


def _session_view_frame_is_blocked(
    session_view_frame: ExperienceSessionViewFrame,
) -> bool:
    status = session_view_frame.status.strip().casefold()
    return (
        not session_view_frame.accepted
        or status in {"blocked", "error", "failed", "unavailable"}
        or bool(_session_view_frame_blockers(session_view_frame))
    )


def _session_view_frame_blockers(
    session_view_frame: ExperienceSessionViewFrame,
) -> list[str]:
    blockers: list[str] = []
    blockers.extend(session_view_frame.blockers)
    lens = session_view_frame.lens
    if lens is not None:
        blockers.extend(getattr(lens, "blockers", []) or [])
    return _dedupe_text(blockers)


def _dedupe_text(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _session_view_frame_request_spec(
    request: object,
) -> ResolveExperienceSessionViewFrameRequestSpec:
    if isinstance(request, ResolveExperienceSessionViewFrameRequestSpec):
        return request
    if isinstance(request, BaseModel):
        payload = request.model_dump(mode="json", exclude_none=True)
    elif isinstance(request, Mapping):
        payload = _json_object_payload(request)
    else:
        payload = _model_payload(request)
    return ResolveExperienceSessionViewFrameRequestSpec.model_validate(payload)


def _request_with_session_view_frame_defaults(
    *,
    request: WatchExperienceViewStateRequest,
    session_view_frame: ExperienceSessionViewFrame | None,
) -> WatchExperienceViewStateRequest:
    if session_view_frame is None or session_view_frame.lens is None:
        return request
    lens = session_view_frame.lens
    provider_context = dict(request.provider_context)
    _set_default(provider_context, "view_ref", lens.view_ref)
    _set_default(provider_context, "projection_view_key", lens.projection_view_key)
    _set_default(provider_context, "section_key", lens.section_key)
    _set_default(
        provider_context,
        "section_graph_binding_key",
        lens.section_graph_binding_key,
    )
    _set_default(provider_context, "binding_key", lens.section_graph_binding_key)
    return request.model_copy(update={"provider_context": provider_context})


def _set_default(
    target: dict[str, object],
    key: str,
    value: object | None,
) -> None:
    if value is None:
        return
    if _context_text(target, key) is None:
        target[key] = value


def _session_view_frame_digest(
    session_view_frame: ExperienceSessionViewFrame,
) -> str:
    return _stable_digest(
        {
            "session_scope": _model_payload(session_view_frame.session_scope),
            "lens": _model_payload(session_view_frame.lens),
            "environment_session_id": session_view_frame.environment_session_id,
            "environment_navigation_context_id": (
                session_view_frame.environment_navigation_context_id
            ),
            "environment_session_thread_id": (
                session_view_frame.environment_session_thread_id
            ),
            "thread_layout_id": session_view_frame.thread_layout_id,
            "attention_session_id": session_view_frame.attention_session_id,
            "active_attention_focus_transition_id": (
                session_view_frame.active_attention_focus_transition_id
            ),
            "transition_count": session_view_frame.transition_count,
            "status": session_view_frame.status,
            "blockers": list(session_view_frame.blockers),
        }
    )


def _provider_context_with_route_defaults(
    *,
    request: WatchExperienceViewStateRequest,
    host_context: ServiceApiHostContext,
) -> tuple[dict[str, object], ServiceViewProviderRouteDescriptor | None]:
    provider_context = dict(request.provider_context)
    if _context_text(provider_context, "api_package_name") and (
        _context_text(provider_context, "api_view_ref")
        or _context_text(provider_context, "view_ref")
    ):
        return provider_context, None
    provider_route = _resolve_host_provider_route(
        request=request,
        provider_context=provider_context,
        host_context=host_context,
    )
    if provider_route is None:
        return provider_context, None
    defaults = provider_route.provider_context()
    defaults.update(provider_context)
    return defaults, provider_route


def _resolve_host_provider_route(
    *,
    request: WatchExperienceViewStateRequest,
    provider_context: Mapping[str, object],
    host_context: ServiceApiHostContext,
) -> ServiceViewProviderRouteDescriptor | None:
    _ = request
    route_view_ref = _context_text(provider_context, "api_view_ref") or _context_text(
        provider_context,
        "view_ref",
    )
    if route_view_ref is None:
        return None
    return resolve_service_view_provider_route(
        routes=host_context.service_view_provider_routes,
        view_ref=route_view_ref,
        service_name=_context_text(provider_context, "service_name"),
    )


def _provider_evidence(
    *,
    api_package_name: str | None,
    api_view_ref: str,
    provider_route: ServiceViewProviderRouteDescriptor | None,
) -> dict[str, object]:
    evidence: dict[str, object] = {
        "api_view_ref": api_view_ref,
        "source": "route_backed_experience_view_state_backend",
        "route_source": (
            "host_context.service_view_provider_routes"
            if provider_route is not None
            else "provider_context"
        ),
    }
    if api_package_name is not None:
        evidence["api_package_name"] = api_package_name
    if provider_route is not None:
        evidence["view_provider_route"] = provider_route.provider_context()
    return evidence


def _stable_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _provider_input(
    *,
    request: WatchExperienceViewStateRequest,
    api_view_ref: str,
    endpoint_ref: str | None,
    api_package_name: str | None,
    response_payload: Mapping[str, object],
    provider_context: Mapping[str, object],
) -> dict[str, object]:
    explicit_provider_input = _context_mapping(provider_context, "provider_input")
    fulfillment = {
        "source_kind": "experience_service_route_backed_provider",
        "api_view_ref": api_view_ref,
        "api_view_id": _context_text(provider_context, "api_view_id"),
        "projection_experience_view_id": _context_text(
            provider_context,
            "projection_experience_view_id",
        ),
        "service_operation_config_api_view_id": _context_text(
            provider_context,
            "service_operation_config_api_view_id",
        ),
        "service_operation_config_id": _context_text(
            provider_context,
            "service_operation_config_id",
        ),
    }
    provider_input: dict[str, object] = {
        "response": response_payload,
        "fulfillment": {
            key: value for key, value in fulfillment.items() if value is not None
        },
        "provenance": {
            "source": "experience.view_state.watch",
            "experience_name": request.experience_name,
            "view_ref": _context_text(provider_context, "view_ref"),
            "api_view_ref": api_view_ref,
            "api_package_name": api_package_name,
            "endpoint_ref": endpoint_ref,
        },
    }
    if explicit_provider_input is not None:
        provider_input.update(explicit_provider_input)
    return provider_input


def _provider_state(
    *,
    provider_ref: str | None,
    provider_callables: Mapping[str, ViewStateProviderCallable],
    provider_input: Mapping[str, object],
) -> object:
    if provider_ref is None:
        return provider_input
    provider = provider_callables.get(provider_ref) or _load_provider(provider_ref)
    return provider(provider_input=provider_input)


def _load_provider(provider_ref: str) -> ViewStateProviderCallable:
    module_name, _, callable_name = provider_ref.rpartition(".")
    if not module_name or not callable_name:
        raise RuntimeError(
            "Experience route-backed view-state provider refs must be import paths: "
            + f"provider_ref={provider_ref!r}"
        )
    module = import_module(module_name)
    provider = getattr(module, callable_name)
    if not callable(provider):
        raise RuntimeError(
            "Loaded Experience route-backed view-state provider is not callable: "
            + f"provider_ref={provider_ref!r}"
        )
    return cast(ViewStateProviderCallable, provider)


def _validated_state_payload(
    *,
    raw_state: object,
    view_ref: str | None,
    projection_view_key: str | None,
    provider_context: Mapping[str, object],
) -> tuple[dict[str, object], str | None]:
    contract = _load_view_model_contract(
        view_ref=view_ref,
        projection_view_key=projection_view_key,
        provider_context=provider_context,
    )
    if contract is None:
        return _json_object_payload(raw_state), None
    model = contract["model"]
    view_state = model.model_validate(raw_state)
    payload = view_state.model_dump(mode="json", exclude_none=True)
    if not isinstance(payload, Mapping):
        raise RuntimeError(
            "Experience view-state provider output did not dump to an object: "
            + f"view_ref={view_ref!r}"
        )
    return _json_object_payload(payload), _context_text(contract, "state_model_ref")


def _load_view_model_contract(
    *,
    view_ref: str | None,
    projection_view_key: str | None,
    provider_context: Mapping[str, object],
) -> Mapping[str, object] | None:
    if view_ref is None:
        return None
    for registry_module_name in _view_model_registry_module_names(
        view_ref=view_ref,
        provider_context=provider_context,
    ):
        try:
            registry_module = import_module(registry_module_name)
        except ModuleNotFoundError as exc:
            if exc.name in {
                registry_module_name,
                registry_module_name.rsplit(".", 1)[0],
            }:
                continue
            raise
        contracts = getattr(registry_module, "VIEW_MODEL_CONTRACTS", None)
        if contracts is None:
            continue
        for contract in contracts:
            contract_view_ref = _object_text(contract, "view_ref")
            contract_view_key = _object_text(contract, "view_key")
            if contract_view_ref != view_ref:
                continue
            if projection_view_key is not None and contract_view_key not in {
                None,
                projection_view_key,
            }:
                raise RuntimeError(
                    "Experience view-state contract view key mismatch: "
                    + f"view_ref={view_ref!r} expected={projection_view_key!r} "
                    + f"actual={contract_view_key!r}"
                )
            model = getattr(contract, "model", None)
            if model is None or not hasattr(model, "model_validate"):
                raise RuntimeError(
                    "Experience view-state registry contract is missing a pydantic model: "
                    + f"view_ref={view_ref!r} registry_module={registry_module_name!r}"
                )
            return {
                "view_ref": contract_view_ref,
                "view_key": contract_view_key,
                "state_model_ref": _object_text(contract, "state_model_ref"),
                "model": model,
                "registry_module": registry_module_name,
            }
    return None


def _view_model_registry_module_names(
    *,
    view_ref: str,
    provider_context: Mapping[str, object],
) -> tuple[str, ...]:
    explicit = _context_text(provider_context, "view_model_registry_module")
    modules: list[str] = []
    if explicit is not None:
        modules.append(explicit)
    experience_name = view_ref.split(".", 1)[0].strip()
    if experience_name:
        modules.append(f"{experience_name}.view_model_registry")
        if experience_name.endswith("_package"):
            modules.append(
                f"{experience_name.removesuffix('_package')}_experience.view_model_registry"
            )
        modules.append(f"{experience_name}_experience.view_model_registry")
    return tuple(dict.fromkeys(modules))


def _response_payload(response: object) -> dict[str, object]:
    status = _response_status(response)
    if status and status.casefold() == "failed":
        raise RuntimeError(
            _context_text(_json_object_payload(response), "error")
            or "Service API view-state provider request failed."
        )
    payload = getattr(response, "response_payload", None)
    return _json_object_payload(payload)


def _response_status(response: object) -> str | None:
    raw_status = getattr(response, "status", None)
    value = getattr(raw_status, "value", raw_status)
    return str(value).strip() if value is not None else None


def _state_status(
    *,
    state_payload: Mapping[str, object],
    response: object,
    response_payload: Mapping[str, object],
) -> str:
    return (
        _context_text(state_payload, "status")
        or _context_text(response_payload, "status")
        or _response_status(response)
        or "ready"
    )


def _required_context_text(
    context: Mapping[str, object],
    key: str,
) -> str:
    value = _context_text(context, key)
    if value is None:
        raise RuntimeError(
            "Experience route-backed view-state provider requires "
            + f"provider_context.{key}."
        )
    return value


def _required_api_view_ref(
    *,
    request: WatchExperienceViewStateRequest,
    provider_context: Mapping[str, object],
) -> str:
    _ = request
    value = _context_text(provider_context, "api_view_ref") or _context_text(
        provider_context,
        "view_ref",
    )
    if value is None:
        raise RuntimeError(
            "Experience route-backed view-state provider requires an ApiView "
            "contract ref through provider_context.api_view_ref or "
            "provider_context.view_ref."
        )
    return value


def _context_text(context: Mapping[str, object], key: str) -> str | None:
    value = context.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _object_text(value: object, attr: str) -> str | None:
    raw = getattr(value, attr, None)
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _context_uuid(context: Mapping[str, object], key: str):
    value = _context_text(context, key)
    if value is None:
        return None
    from uuid import UUID

    return UUID(value)


def _context_float(context: Mapping[str, object], key: str) -> float | None:
    value = context.get(key)
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except ValueError:
        return None


def _context_mapping(
    context: Mapping[str, object],
    key: str,
) -> dict[str, object] | None:
    value = context.get(key)
    if value is None:
        return None
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json", exclude_none=True)
    if not isinstance(value, Mapping):
        raise RuntimeError(f"provider_context.{key} must be an object.")
    return _json_object_payload(value)


def _optional_payload_text(payload: Mapping[str, object], key: str) -> str | None:
    return _context_text(payload, key)


def _json_object_payload(value: object) -> dict[str, object]:
    if value is None:
        return {}
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, Mapping):
        return {
            str(key): _json_value(item)
            for key, item in value.items()
            if item is not None
        }
    raise RuntimeError(
        "Experience view-state provider expected an object payload: "
        + f"payload_type={type(value).__name__}"
    )


def _json_value(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, BaseModel):
        return _json_object_payload(value)
    if isinstance(value, Mapping):
        return _json_object_payload(value)
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return str(value)


def _model_payload(value: object | None) -> object | None:
    if value is None:
        return None
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return cast(object, value)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = [
    "ExperienceViewStateBackend",
    "RouteBackedExperienceViewStateBackend",
    "stream_watch_experience_view_state",
    "watch_experience_view_state",
]
