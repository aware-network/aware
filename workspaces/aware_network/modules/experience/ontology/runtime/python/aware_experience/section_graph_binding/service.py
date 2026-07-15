from __future__ import annotations

# pyright: reportMissingImports=false, reportAttributeAccessIssue=false

import asyncio
from collections.abc import Iterator
from dataclasses import dataclass
import json
from typing import Any, cast
from uuid import UUID

from pydantic import BaseModel

from aware_experience.section_graph_binding.api_models import (
    ActivateExperienceLayoutGraphBindingRequest,
    ActivateExperienceLayoutGraphBindingResponse,
    ActivateExperienceSectionGraphBindingRequest,
    ActivateExperienceSectionGraphBindingResponse,
    ApplyExperienceViewEventTransitionRequest,
    ApplyExperienceViewEventTransitionResponse,
    ExperienceLayoutGraphBindingState,
    ExperienceSectionFocusTarget,
    ExperienceSectionGraphBindingActivationScope,
    ExperienceViewInvocationActionApiDispatchReceipt,
    ExperienceViewInvocationActionReceipt,
    ExperienceViewEventTransitionReceipt,
    ExperienceViewEventTransitionTarget,
    ExperienceViewEventTransitionTrigger,
    ExperienceSectionViewResolution,
    ExperienceViewInvocationActionDescriptor,
    ExperienceSectionGraphBindingState,
    ExperienceSectionGraphBindingStateEvent,
    ExperienceSectionGraphBindingStateSnapshot,
    GetExperienceLayoutGraphBindingCatalogRequest,
    GetExperienceLayoutGraphBindingCatalogResponse,
    GetExperienceLayoutGraphBindingStateRequest,
    GetExperienceLayoutGraphBindingStateResponse,
    GetExperienceSectionGraphBindingCatalogRequest,
    GetExperienceSectionGraphBindingCatalogResponse,
    GetExperienceSectionGraphBindingStateRequest,
    GetExperienceSectionGraphBindingStateResponse,
    InvokeExperienceViewInvocationActionRequest,
    InvokeExperienceViewInvocationActionResponse,
    RecordExperienceViewInvocationActionRequest,
    RecordExperienceViewInvocationActionResponse,
    WatchExperienceSectionGraphBindingsRequest,
    WatchExperienceSectionGraphBindingsResponse,
)
from aware_experience.section_graph_binding.catalog import (
    ExperienceLayoutGraphBindingCatalog,
    ExperienceLayoutGraphBindingCatalogEntry,
    ExperienceSectionGraphBindingCatalog,
    ExperienceSectionGraphBindingCatalogEntry,
    ExperienceSectionObservableViewResolution,
    resolve_layout_graph_binding_catalog,
    resolve_section_graph_binding_catalog,
    resolve_section_observable_invocation_actions,
    resolve_section_observable_view_instance,
)
from aware_api_ontology.api.api_view_capability_endpoint import (
    ApiViewCapabilityEndpoint,
)
from aware_environment_service_dto.environment.environment import (
    InvokeFunctionCallTarget,
    InvokeFunctionRequest,
    InvokeFunctionResponse,
)
from aware_experience_ontology.invocation.experience_invocation_action_config import (
    ExperienceInvocationActionConfig,
)
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_experience_ontology.projection.projection_experience_view import (
    ProjectionExperienceView,
)
from aware_experience_ontology.projection.projection_experience_view_instance import (
    ProjectionExperienceViewInstance,
)
from aware_experience_ontology.projection.projection_experience_view_invocation_action_config import (
    ProjectionExperienceViewInvocationActionConfig,
)
from aware_experience.stable_ids import (
    stable_experience_invocation_action_commit_id,
    stable_experience_invocation_action_id,
    stable_projection_experience_view_invocation_action_id,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_orm.session.session import Session
from aware_code.types import JsonArray, JsonObject
from aware_service_runtime.api_ingress.host_context import ServiceApiHostContext
from aware_service_runtime.contracts import ServiceGraphGateway
from aware_service_runtime.local_service_host_api_client import (
    build_service_api_client_for_api_package,
)

_SECTION_GRAPH_BINDING_PROJECTION_NAMES = (
    "ProjectionExperience",
    "ExperienceInvocationActionConfig",
    "ProjectionExperienceGraph",
    "ProjectionExperienceSectionGraphBinding",
)
_VIEW_INVOCATION_ACTION_PROJECTION_NAMES = (
    *_SECTION_GRAPH_BINDING_PROJECTION_NAMES,
    "ExperienceInvocationAction",
)
EXPERIENCE_TRANSITION_SPEC_PROJECTION_NAMES = (
    *_SECTION_GRAPH_BINDING_PROJECTION_NAMES,
    "EnvironmentExperience",
    "EventConfig",
)
_ATTENTION_SERVICE_API_PACKAGE_NAME = "attention-service-api"


@dataclass(frozen=True, slots=True)
class _SectionGraphBindingRuntimeContext:
    host_context: ServiceApiHostContext
    graph_gateway: ServiceGraphGateway
    runtime_index: MetaGraphRuntimeIndex
    branch_id: UUID
    projection_hashes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _ViewEventTransitionTargetResolution:
    transition_key: str
    source_view_ref: str | None
    event_type: str
    action_type: str | None
    target_view_ref: str
    target_binding_key: str
    target_section_key: str | None
    target_graph_identity_ref: str | None
    rationale: str | None
    focus_scope_title: str | None


@dataclass(frozen=True, slots=True)
class _ViewInvocationActionRecordingTarget:
    experience_name: str
    projection_experience_view_instance_id: UUID
    projection_experience_view_id: UUID
    view_invocation_action_config_id: UUID
    experience_invocation_action_config_id: UUID
    api_view_capability_endpoint_id: UUID
    action_key: str
    target_kind: str
    endpoint_ref: str
    sdk_operation_api_view_capability_endpoint_id: UUID | None
    api_capability_endpoint_id: UUID | None
    sdk_operation_id: UUID | None


@dataclass(frozen=True, slots=True)
class _InvocationCommitEventEvidence:
    event_id: UUID
    event_role: str
    description: str


@dataclass(frozen=True, slots=True)
class _InvocationCommitEvidence:
    object_instance_graph_commit_id: UUID
    commit_role: str
    description: str
    event_evidence: tuple[_InvocationCommitEventEvidence, ...] = ()


@dataclass(slots=True)
class _InvocationCommitEvidenceAccumulator:
    object_instance_graph_commit_id: UUID
    commit_role: str
    description: str
    event_evidence: list[_InvocationCommitEventEvidence]
    seen_event_ids: set[UUID]


@dataclass(frozen=True, slots=True)
class _InvocationFunctionTarget:
    function_id: UUID
    projection_hash: str


async def get_section_graph_binding_catalog(
    *,
    request: GetExperienceSectionGraphBindingCatalogRequest,
    host_context: ServiceApiHostContext,
) -> GetExperienceSectionGraphBindingCatalogResponse:
    catalog = await _resolve_catalog(
        host_context=host_context,
        experience_name=request.experience_name,
    )
    entries = catalog.filter_entries(
        section_keys=request.section_keys,
        binding_keys=request.binding_keys,
    )
    return GetExperienceSectionGraphBindingCatalogResponse(
        request_id=request.request_id,
        success=True,
        info="section graph binding catalog resolved",
        experience_name=catalog.experience_name,
        catalog_revision=catalog.catalog_revision,
        bindings=[entry.descriptor for entry in entries],
    )


async def get_layout_graph_binding_catalog(
    *,
    request: GetExperienceLayoutGraphBindingCatalogRequest,
    host_context: ServiceApiHostContext,
) -> GetExperienceLayoutGraphBindingCatalogResponse:
    catalog = await _resolve_layout_catalog(
        host_context=host_context,
        experience_name=request.experience_name,
    )
    entries = catalog.filter_entries(
        layout_binding_keys=request.layout_binding_keys,
    )
    return GetExperienceLayoutGraphBindingCatalogResponse(
        request_id=request.request_id,
        success=True,
        info="layout graph binding catalog resolved",
        experience_name=catalog.experience_name,
        catalog_revision=catalog.catalog_revision,
        bindings=[entry.descriptor for entry in entries],
    )


async def get_section_graph_binding_state(
    *,
    request: GetExperienceSectionGraphBindingStateRequest,
    host_context: ServiceApiHostContext,
) -> GetExperienceSectionGraphBindingStateResponse:
    catalog = await _resolve_catalog(
        host_context=host_context,
        experience_name=request.experience_name,
    )
    entry = _require_catalog_entry(catalog=catalog, binding_key=request.binding_key)
    attention_snapshot = await _read_attention_section_snapshot(
        host_context=host_context,
        section_key=entry.descriptor.section_key,
    )
    section_view = await _try_resolve_section_view_resolution_for_attention_snapshot(
        host_context=host_context,
        experience_name=catalog.experience_name,
        entry=entry,
        attention_snapshot=attention_snapshot,
    )
    state = _state_from_attention_snapshot(
        entry=entry,
        attention_snapshot=attention_snapshot,
        section_view=section_view,
    )
    return GetExperienceSectionGraphBindingStateResponse(
        request_id=request.request_id,
        success=True,
        info="section graph binding state resolved",
        experience_name=catalog.experience_name,
        catalog_revision=catalog.catalog_revision,
        state=state,
    )


async def get_layout_graph_binding_state(
    *,
    request: GetExperienceLayoutGraphBindingStateRequest,
    host_context: ServiceApiHostContext,
) -> GetExperienceLayoutGraphBindingStateResponse:
    catalog = await _resolve_layout_catalog(
        host_context=host_context,
        experience_name=request.experience_name,
    )
    entry = _require_layout_catalog_entry(
        catalog=catalog,
        binding_key=request.layout_binding_key,
    )
    state = await _layout_state_from_catalog_entry(
        host_context=host_context,
        catalog=catalog,
        entry=entry,
    )
    return GetExperienceLayoutGraphBindingStateResponse(
        request_id=request.request_id,
        success=True,
        info="layout graph binding state resolved",
        experience_name=catalog.experience_name,
        catalog_revision=catalog.catalog_revision,
        state=state,
    )


async def activate_section_graph_binding(
    *,
    request: ActivateExperienceSectionGraphBindingRequest,
    host_context: ServiceApiHostContext,
) -> ActivateExperienceSectionGraphBindingResponse:
    catalog = await _resolve_catalog(
        host_context=host_context,
        experience_name=request.experience_name,
    )
    entry = _require_catalog_entry(catalog=catalog, binding_key=request.binding_key)
    _require_activation_scope_matches_entry(
        activation_scope=request.activation_scope,
        entry=entry,
    )
    attention_snapshot, state = await _activate_catalog_entry(
        host_context=host_context,
        catalog=catalog,
        entry=entry,
        activation_scope=request.activation_scope,
        rationale=_normalize_optional_text(request.rationale)
        or f"experience_section_graph_binding:{catalog.experience_name}:{entry.descriptor.binding_key}",
        section_title=_normalize_optional_text(request.section_title),
        section_description=_normalize_optional_text(request.section_description),
        focus_scope_title=_normalize_optional_text(request.focus_scope_title),
        focus_scope_description=_normalize_optional_text(
            request.focus_scope_description
        ),
    )
    _ = attention_snapshot
    return ActivateExperienceSectionGraphBindingResponse(
        request_id=request.request_id,
        success=True,
        info="section graph binding activated",
        experience_name=catalog.experience_name,
        catalog_revision=catalog.catalog_revision,
        state=state,
    )


async def activate_layout_graph_binding(
    *,
    request: ActivateExperienceLayoutGraphBindingRequest,
    host_context: ServiceApiHostContext,
) -> ActivateExperienceLayoutGraphBindingResponse:
    catalog = await _resolve_layout_catalog(
        host_context=host_context,
        experience_name=request.experience_name,
    )
    entry = _require_layout_catalog_entry(
        catalog=catalog,
        binding_key=request.layout_binding_key,
    )
    _require_layout_activation_scope_is_not_section_specific(
        activation_scope=request.activation_scope,
    )
    section_catalog = await _resolve_catalog(
        host_context=host_context,
        experience_name=catalog.experience_name,
    )
    section_states: list[ExperienceSectionGraphBindingState] = []
    for section_entry in entry.section_entries:
        _attention_snapshot, state = await _activate_catalog_entry(
            host_context=host_context,
            catalog=section_catalog,
            entry=section_entry,
            activation_scope=request.activation_scope,
            rationale=_normalize_optional_text(request.rationale)
            or (
                "experience_layout_graph_binding:"
                + f"{catalog.experience_name}:{entry.descriptor.binding_key}:"
                + f"{section_entry.descriptor.binding_key}"
            ),
            section_title=_normalize_optional_text(request.section_title),
            section_description=_normalize_optional_text(request.section_description),
            focus_scope_title=_normalize_optional_text(request.focus_scope_title),
            focus_scope_description=_normalize_optional_text(
                request.focus_scope_description
            ),
        )
        section_states.append(state)
    return ActivateExperienceLayoutGraphBindingResponse(
        request_id=request.request_id,
        success=True,
        info="layout graph binding activated",
        experience_name=catalog.experience_name,
        catalog_revision=catalog.catalog_revision,
        state=ExperienceLayoutGraphBindingState(
            binding=entry.descriptor,
            exists=bool(section_states)
            and all(state.exists for state in section_states),
            section_states=section_states,
        ),
    )


async def apply_view_event_transition(
    *,
    request: ApplyExperienceViewEventTransitionRequest,
    host_context: ServiceApiHostContext,
) -> ApplyExperienceViewEventTransitionResponse:
    transition_key = _normalize_required_text(
        request.transition_key,
        label="transition_key",
    )
    event_type = _normalize_required_text(request.event_type, label="event_type")
    resolved_transition = await _resolve_view_event_transition_target(
        host_context=host_context,
        experience_name=request.experience_name,
        profile_key=_normalize_optional_text(getattr(request, "profile_key", None)),
        transition_key=transition_key,
        event_type=event_type,
        source_view_ref=_normalize_optional_text(request.source_view_ref),
        action_type=_normalize_optional_text(request.action_type),
    )
    catalog = await _resolve_catalog(
        host_context=host_context,
        experience_name=request.experience_name,
    )
    entry = _require_catalog_entry(
        catalog=catalog,
        binding_key=resolved_transition.target_binding_key,
    )
    _require_transition_target_matches_entry(
        target_view_ref=resolved_transition.target_view_ref,
        target_section_key=resolved_transition.target_section_key,
        target_graph_identity_ref=resolved_transition.target_graph_identity_ref,
        entry=entry,
    )
    _require_transition_request_target_hints_match_resolution(
        request=request,
        resolved_transition=resolved_transition,
    )
    _require_activation_scope_matches_entry(
        activation_scope=request.activation_scope,
        entry=entry,
    )
    attention_snapshot, state = await _activate_catalog_entry(
        host_context=host_context,
        catalog=catalog,
        entry=entry,
        activation_scope=request.activation_scope,
        rationale=_normalize_optional_text(request.rationale)
        or resolved_transition.rationale
        or f"experience_view_event_transition:{transition_key}:{event_type}",
        section_title=request.section_title,
        section_description=request.section_description,
        focus_scope_title=request.focus_scope_title
        or resolved_transition.focus_scope_title,
        focus_scope_description=request.focus_scope_description,
    )
    target_section_view = await _resolve_section_view_resolution_for_attention_snapshot(
        host_context=host_context,
        experience_name=catalog.experience_name,
        entry=entry,
        attention_snapshot=attention_snapshot,
    )
    state = _state_from_attention_snapshot(
        entry=entry,
        attention_snapshot=attention_snapshot,
        section_view=target_section_view,
    )
    target = ExperienceViewEventTransitionTarget(
        target_view_ref=resolved_transition.target_view_ref,
        target_binding_key=resolved_transition.target_binding_key,
        target_section_key=resolved_transition.target_section_key,
        target_graph_identity_ref=resolved_transition.target_graph_identity_ref,
        section_view=target_section_view,
    )
    trigger = ExperienceViewEventTransitionTrigger(
        source_view_ref=_normalize_optional_text(request.source_view_ref)
        or resolved_transition.source_view_ref,
        event_id=request.event_id,
        event_type=event_type,
        action_intent_id=request.action_intent_id,
        action_type=_normalize_optional_text(request.action_type),
    )
    receipt = ExperienceViewEventTransitionReceipt(
        transition_key=transition_key,
        experience_name=catalog.experience_name,
        trigger=trigger,
        target=target,
        state=state,
        info=(
            "experience view event transition applied through section graph binding "
            "and section observable view instance "
            f"{target_section_view.projection_experience_section_view_id}"
        ),
    )
    return ApplyExperienceViewEventTransitionResponse(
        request_id=request.request_id,
        success=True,
        info=receipt.info,
        experience_name=catalog.experience_name,
        catalog_revision=catalog.catalog_revision,
        receipt=receipt,
        state=state,
    )


async def record_experience_view_invocation_action(
    *,
    request: RecordExperienceViewInvocationActionRequest,
    host_context: ServiceApiHostContext,
) -> RecordExperienceViewInvocationActionResponse:
    invocation_key = request.invocation_key
    status = _normalize_optional_text(request.status) or "pending"
    runtime_context = await _resolve_runtime_context(
        host_context=host_context,
        experience_name=request.experience_name,
        projection_names=_VIEW_INVOCATION_ACTION_PROJECTION_NAMES,
    )
    session = await _hydrate_section_graph_binding_session(
        runtime_context=runtime_context,
    )
    target = _resolve_view_invocation_action_recording_target(
        session=session,
        experience_name=request.experience_name,
        projection_experience_view_instance_id=(
            request.projection_experience_view_instance_id
        ),
        view_invocation_action_config_id=request.view_invocation_action_config_id,
    )
    receipt = await _record_view_invocation_action_for_target(
        runtime_context=runtime_context,
        target=target,
        invocation_key=invocation_key,
        actor_id=request.actor_id,
        api_call_id=request.api_call_id,
        sdk_operation_call_id=request.sdk_operation_call_id,
        request_ref=_normalize_optional_text(request.request_ref),
        receipt_ref=_normalize_optional_text(request.receipt_ref),
        status=status,
    )
    return RecordExperienceViewInvocationActionResponse(
        request_id=request.request_id,
        success=True,
        info=(
            "experience view invocation action recorded through view instance "
            f"{target.projection_experience_view_instance_id}"
        ),
        experience_name=target.experience_name,
        receipt=receipt,
    )


async def invoke_experience_view_invocation_action(
    *,
    request: InvokeExperienceViewInvocationActionRequest,
    host_context: ServiceApiHostContext,
) -> InvokeExperienceViewInvocationActionResponse:
    runtime_context = await _resolve_runtime_context(
        host_context=host_context,
        experience_name=request.experience_name,
        projection_names=_VIEW_INVOCATION_ACTION_PROJECTION_NAMES,
    )
    session = await _hydrate_section_graph_binding_session(
        runtime_context=runtime_context,
    )
    target = _resolve_view_invocation_action_recording_target(
        session=session,
        experience_name=request.experience_name,
        projection_experience_view_instance_id=(
            request.projection_experience_view_instance_id
        ),
        view_invocation_action_config_id=request.view_invocation_action_config_id,
    )
    endpoint_ref = _api_endpoint_ref_for_view_invocation_target(target=target)
    invoker = _require_view_invocation_action_api_invoker(
        host_context=host_context,
        target=target,
        request=request,
    )
    raw_response = await invoker.invoke_api_endpoint_raw(
        endpoint_ref=endpoint_ref,
        discriminant=endpoint_ref,
        request_payload=cast(JsonObject, dict(request.request_payload or {})),
    )
    api_dispatch_receipt = _require_api_dispatch_receipt(
        receipt=getattr(raw_response, "receipt", None),
        target=target,
    )
    _require_api_dispatch_receipt_matches_target(
        receipt=api_dispatch_receipt,
        target=target,
    )
    status = _normalize_optional_text(getattr(raw_response, "status", None)) or (
        api_dispatch_receipt.status
    )
    receipt = await _record_view_invocation_action_for_target(
        runtime_context=runtime_context,
        target=target,
        invocation_key=request.invocation_key,
        actor_id=request.actor_id,
        api_call_id=api_dispatch_receipt.api_call_id,
        sdk_operation_call_id=None,
        request_ref=(
            _normalize_optional_text(request.request_ref)
            or f"experience:{target.experience_name}:{target.action_key}"
        ),
        receipt_ref=(
            _normalize_optional_text(request.receipt_ref)
            or _api_dispatch_receipt_ref(receipt=api_dispatch_receipt)
        ),
        status=status,
    )
    await _attach_invocation_action_commit_evidence(
        runtime_context=runtime_context,
        experience_invocation_action_id=receipt.experience_invocation_action_id,
        commit_evidence=_api_dispatch_commit_evidence(receipt=api_dispatch_receipt),
        actor_id=request.actor_id,
    )
    succeeded = status.strip().casefold() != "failed"
    return InvokeExperienceViewInvocationActionResponse(
        request_id=request.request_id,
        success=succeeded,
        info=(
            "experience view invocation action invoked through API target "
            f"{endpoint_ref!r} and recorded through view instance "
            f"{target.projection_experience_view_instance_id}"
        ),
        error=getattr(raw_response, "error", None) if not succeeded else None,
        experience_name=target.experience_name,
        receipt=receipt,
        api_dispatch_receipt=api_dispatch_receipt,
        response_payload=_json_value_payload(
            getattr(raw_response, "response_payload", None)
        ),
    )


async def watch_section_graph_bindings(
    *,
    request: WatchExperienceSectionGraphBindingsRequest,
    host_context: ServiceApiHostContext,
) -> WatchExperienceSectionGraphBindingsResponse:
    snapshot = await _build_snapshot(
        host_context=host_context,
        experience_name=request.experience_name,
        section_keys=request.section_keys,
        binding_keys=request.binding_keys,
    )
    return WatchExperienceSectionGraphBindingsResponse(
        request_id=request.request_id,
        success=True,
        info="section graph binding snapshot resolved",
        experience_name=snapshot.experience_name,
        snapshot=snapshot,
    )


async def stream_watch_section_graph_bindings(
    *,
    request: WatchExperienceSectionGraphBindingsRequest,
    host_context: ServiceApiHostContext,
):
    last_signature: str | None = None
    poll_interval_s = max(request.poll_interval_ms / 1000.0, 0.25)

    while True:
        snapshot = await _build_snapshot(
            host_context=host_context,
            experience_name=request.experience_name,
            section_keys=request.section_keys,
            binding_keys=request.binding_keys,
        )
        signature = _snapshot_signature(snapshot)
        if signature != last_signature:
            yield ExperienceSectionGraphBindingStateEvent(snapshot=snapshot)
            last_signature = signature
        await asyncio.sleep(poll_interval_s)


async def _resolve_catalog(
    *,
    host_context: ServiceApiHostContext,
    experience_name: str,
) -> ExperienceSectionGraphBindingCatalog:
    runtime_context = await _resolve_runtime_context(
        host_context=host_context,
        experience_name=experience_name,
    )
    session = await _hydrate_section_graph_binding_session(
        runtime_context=runtime_context
    )
    return resolve_section_graph_binding_catalog(
        session=session,
        experience_name=experience_name,
    )


async def _resolve_layout_catalog(
    *,
    host_context: ServiceApiHostContext,
    experience_name: str,
) -> ExperienceLayoutGraphBindingCatalog:
    runtime_context = await _resolve_runtime_context(
        host_context=host_context,
        experience_name=experience_name,
    )
    session = await _hydrate_section_graph_binding_session(
        runtime_context=runtime_context
    )
    return resolve_layout_graph_binding_catalog(
        session=session,
        experience_name=experience_name,
    )


async def _build_snapshot(
    *,
    host_context: ServiceApiHostContext,
    experience_name: str,
    section_keys: list[str],
    binding_keys: list[str],
) -> ExperienceSectionGraphBindingStateSnapshot:
    catalog = await _resolve_catalog(
        host_context=host_context,
        experience_name=experience_name,
    )
    entries = catalog.filter_entries(
        section_keys=section_keys,
        binding_keys=binding_keys,
    )
    states: list[ExperienceSectionGraphBindingState] = []
    for entry in entries:
        attention_snapshot = await _read_attention_section_snapshot(
            host_context=host_context,
            section_key=entry.descriptor.section_key,
        )
        section_view = (
            await _try_resolve_section_view_resolution_for_attention_snapshot(
                host_context=host_context,
                experience_name=catalog.experience_name,
                entry=entry,
                attention_snapshot=attention_snapshot,
            )
        )
        states.append(
            _state_from_attention_snapshot(
                entry=entry,
                attention_snapshot=attention_snapshot,
                section_view=section_view,
            )
        )
    return ExperienceSectionGraphBindingStateSnapshot(
        experience_name=catalog.experience_name,
        catalog_revision=catalog.catalog_revision,
        states=states,
    )


async def _layout_state_from_catalog_entry(
    *,
    host_context: ServiceApiHostContext,
    catalog: ExperienceLayoutGraphBindingCatalog,
    entry: ExperienceLayoutGraphBindingCatalogEntry,
) -> ExperienceLayoutGraphBindingState:
    states: list[ExperienceSectionGraphBindingState] = []
    for section_entry in entry.section_entries:
        attention_snapshot = await _read_attention_section_snapshot(
            host_context=host_context,
            section_key=section_entry.descriptor.section_key,
        )
        section_view = (
            await _try_resolve_section_view_resolution_for_attention_snapshot(
                host_context=host_context,
                experience_name=catalog.experience_name,
                entry=section_entry,
                attention_snapshot=attention_snapshot,
            )
        )
        states.append(
            _state_from_attention_snapshot(
                entry=section_entry,
                attention_snapshot=attention_snapshot,
                section_view=section_view,
            )
        )
    return ExperienceLayoutGraphBindingState(
        binding=entry.descriptor,
        exists=bool(states) and all(state.exists for state in states),
        section_states=states,
    )


async def _resolve_view_event_transition_target(
    *,
    host_context: ServiceApiHostContext,
    experience_name: str,
    profile_key: str | None,
    transition_key: str,
    event_type: str,
    source_view_ref: str | None,
    action_type: str | None,
) -> _ViewEventTransitionTargetResolution:
    from aware_experience.reactivity_transition_specs import (
        resolve_reactivity_view_transition_specs,
    )

    session = await hydrate_experience_reference_session(
        host_context=host_context,
        experience_name=experience_name,
        projection_names=EXPERIENCE_TRANSITION_SPEC_PROJECTION_NAMES,
    )
    spec_resolution = resolve_reactivity_view_transition_specs(
        session=session,
        experience_name=experience_name,
        profile_key=profile_key,
    )
    matches = tuple(
        transition
        for transition in spec_resolution.transitions
        if _transition_spec_matches_request(
            transition=transition,
            transition_key=transition_key,
            event_type=event_type,
            source_view_ref=source_view_ref,
            action_type=action_type,
        )
    )
    if not matches:
        raise ValueError(
            "No committed EnvironmentExperienceViewEventTransition matches "
            + "apply request: "
            + f"experience_name={experience_name!r} "
            + f"profile_key={profile_key!r} "
            + f"transition_key={transition_key!r} "
            + f"event_type={event_type!r} "
            + f"source_view_ref={source_view_ref!r} "
            + f"action_type={action_type!r}"
        )
    if len(matches) != 1:
        raise ValueError(
            "Ambiguous committed EnvironmentExperienceViewEventTransition "
            + "matches apply request: "
            + f"experience_name={experience_name!r} "
            + f"profile_key={profile_key!r} "
            + f"transition_key={transition_key!r} "
            + f"event_type={event_type!r} "
            + f"matches={len(matches)}"
        )
    transition = matches[0]
    return _ViewEventTransitionTargetResolution(
        transition_key=transition_key,
        source_view_ref=_normalize_optional_text(transition.source_view_ref),
        event_type=event_type,
        action_type=_normalize_optional_text(transition.action_type),
        target_view_ref=_normalize_required_text(
            transition.target_view_ref,
            label="transition.target_view_ref",
        ),
        target_binding_key=_normalize_required_text(
            transition.target_binding_key,
            label="transition.target_binding_key",
        ),
        target_section_key=_normalize_optional_text(transition.target_section_key),
        target_graph_identity_ref=_normalize_optional_text(
            transition.target_graph_identity_ref
        ),
        rationale=_normalize_optional_text(transition.rationale),
        focus_scope_title=_normalize_optional_text(transition.focus_scope_title),
    )


def _transition_spec_matches_request(
    *,
    transition: object,
    transition_key: str,
    event_type: str,
    source_view_ref: str | None,
    action_type: str | None,
) -> bool:
    if (
        _normalize_required_text(
            getattr(transition, "transition_key", None),
            label="transition.transition_key",
        )
        != transition_key
    ):
        return False
    if (
        _normalize_required_text(
            getattr(transition, "event_type", None),
            label="transition.event_type",
        )
        != event_type
    ):
        return False
    transition_source_view_ref = _normalize_optional_text(
        getattr(transition, "source_view_ref", None)
    )
    if source_view_ref is not None and source_view_ref != transition_source_view_ref:
        return False
    transition_action_type = _normalize_optional_text(
        getattr(transition, "action_type", None)
    )
    if transition_action_type is not None and transition_action_type != action_type:
        return False
    return True


def _require_catalog_entry(
    *,
    catalog: ExperienceSectionGraphBindingCatalog,
    binding_key: str,
) -> ExperienceSectionGraphBindingCatalogEntry:
    entry = catalog.entry_for_binding_key(binding_key=binding_key)
    if entry is None:
        raise ValueError(
            "Unknown ProjectionExperienceSectionGraphBinding: "
            + f"experience_name={catalog.experience_name!r} binding_key={binding_key!r}"
        )
    return entry


def _require_layout_catalog_entry(
    *,
    catalog: ExperienceLayoutGraphBindingCatalog,
    binding_key: str,
) -> ExperienceLayoutGraphBindingCatalogEntry:
    entry = catalog.entry_for_binding_key(binding_key=binding_key)
    if entry is None:
        raise ValueError(
            "Unknown ProjectionExperienceLayoutGraphBinding: "
            + f"experience_name={catalog.experience_name!r} binding_key={binding_key!r}"
        )
    return entry


def _state_from_attention_snapshot(
    *,
    entry: ExperienceSectionGraphBindingCatalogEntry,
    attention_snapshot: object,
    section_view: ExperienceSectionViewResolution | None = None,
) -> ExperienceSectionGraphBindingState:
    observable_id = cast(
        UUID | None, getattr(attention_snapshot, "observable_id", None)
    )
    focus_target = _experience_focus_target_from_attention_snapshot(
        entry=entry,
        attention_snapshot=attention_snapshot,
    )
    return ExperienceSectionGraphBindingState(
        binding=entry.descriptor,
        exists=bool(getattr(attention_snapshot, "exists", False)),
        is_active=observable_id == entry.projection_observable_id,
        focus_scope_id=cast(
            UUID | None, getattr(attention_snapshot, "focus_scope_id", None)
        ),
        focus_id=cast(UUID | None, getattr(attention_snapshot, "focus_id", None)),
        projection_observable_id=entry.projection_observable_id,
        projection_experience_graph_identity_id=entry.graph_identity_object_id,
        observable_id=observable_id,
        focus_target=focus_target,
        section_view=section_view,
    )


async def _activate_catalog_entry(
    *,
    host_context: ServiceApiHostContext,
    catalog: ExperienceSectionGraphBindingCatalog,
    entry: ExperienceSectionGraphBindingCatalogEntry,
    activation_scope: ExperienceSectionGraphBindingActivationScope | None,
    rationale: str | None,
    section_title: str | None,
    section_description: str | None,
    focus_scope_title: str | None,
    focus_scope_description: str | None,
) -> tuple[object, ExperienceSectionGraphBindingState]:
    attention_snapshot = await _activate_attention_section_observable(
        host_context=host_context,
        section_key=entry.descriptor.section_key,
        observable_id=entry.projection_observable_id,
        activation_scope=activation_scope,
        rationale=rationale,
        section_title=section_title,
        section_description=section_description,
        focus_scope_title=focus_scope_title,
        focus_scope_description=focus_scope_description,
    )
    section_view = await _try_resolve_section_view_resolution_for_attention_snapshot(
        host_context=host_context,
        experience_name=catalog.experience_name,
        entry=entry,
        attention_snapshot=attention_snapshot,
    )
    state = _state_from_attention_snapshot(
        entry=entry,
        attention_snapshot=attention_snapshot,
        section_view=section_view,
    )
    return attention_snapshot, state


async def _resolve_section_view_instance_for_attention_snapshot(
    *,
    host_context: ServiceApiHostContext,
    experience_name: str,
    entry: ExperienceSectionGraphBindingCatalogEntry,
    attention_snapshot: object,
) -> ExperienceSectionObservableViewResolution:
    resolution, _actions = (
        await _resolve_section_view_instance_and_actions_for_attention_snapshot(
            host_context=host_context,
            experience_name=experience_name,
            entry=entry,
            attention_snapshot=attention_snapshot,
        )
    )
    return resolution


async def _resolve_section_view_resolution_for_attention_snapshot(
    *,
    host_context: ServiceApiHostContext,
    experience_name: str,
    entry: ExperienceSectionGraphBindingCatalogEntry,
    attention_snapshot: object,
) -> ExperienceSectionViewResolution:
    (
        resolution,
        actions,
    ) = await _resolve_section_view_instance_and_actions_for_attention_snapshot(
        host_context=host_context,
        experience_name=experience_name,
        entry=entry,
        attention_snapshot=attention_snapshot,
    )
    return _section_view_resolution_dto(
        resolution=resolution,
        actions=actions,
    )


async def _try_resolve_section_view_resolution_for_attention_snapshot(
    *,
    host_context: ServiceApiHostContext,
    experience_name: str,
    entry: ExperienceSectionGraphBindingCatalogEntry,
    attention_snapshot: object,
) -> ExperienceSectionViewResolution | None:
    section_id = cast(UUID | None, getattr(attention_snapshot, "section_id", None))
    observable_id = cast(
        UUID | None, getattr(attention_snapshot, "observable_id", None)
    )
    if section_id is None or observable_id != entry.projection_observable_id:
        return None
    try:
        return await _resolve_section_view_resolution_for_attention_snapshot(
            host_context=host_context,
            experience_name=experience_name,
            entry=entry,
            attention_snapshot=attention_snapshot,
        )
    except ValueError:
        return None


async def _resolve_section_view_instance_and_actions_for_attention_snapshot(
    *,
    host_context: ServiceApiHostContext,
    experience_name: str,
    entry: ExperienceSectionGraphBindingCatalogEntry,
    attention_snapshot: object,
) -> tuple[ExperienceSectionObservableViewResolution, tuple[object, ...]]:
    section_id = cast(UUID | None, getattr(attention_snapshot, "section_id", None))
    if section_id is None:
        raise ValueError(
            "Attention section snapshot must include section_id for Experience "
            "section observable view resolution."
        )
    observable_id = cast(
        UUID | None, getattr(attention_snapshot, "observable_id", None)
    )
    if observable_id is None:
        raise ValueError(
            "Attention section snapshot must include observable_id for Experience "
            "section observable view resolution: " + f"section_id={section_id}"
        )
    if observable_id != entry.projection_observable_id:
        raise ValueError(
            "Attention section snapshot observable does not match selected "
            "section graph binding: "
            + f"section_id={section_id} "
            + f"snapshot_observable_id={observable_id} "
            + f"binding_observable_id={entry.projection_observable_id}"
        )

    session = await hydrate_experience_reference_session(
        host_context=host_context,
        experience_name=experience_name,
    )
    resolution = resolve_section_observable_view_instance(
        session=session,
        experience_name=experience_name,
        section_id=section_id,
        object_projection_graph_observable_id=observable_id,
    )
    _require_section_view_resolution_matches_entry(
        resolution=resolution,
        entry=entry,
        section_id=section_id,
    )
    actions = resolve_section_observable_invocation_actions(
        session=session,
        experience_name=experience_name,
        section_id=section_id,
        object_projection_graph_observable_id=observable_id,
    )
    return resolution, cast(tuple[object, ...], actions)


def _resolve_view_invocation_action_recording_target(
    *,
    session: Session,
    experience_name: str,
    projection_experience_view_instance_id: UUID,
    view_invocation_action_config_id: UUID,
) -> _ViewInvocationActionRecordingTarget:
    normalized_experience_name = _normalize_required_text(
        experience_name,
        label="experience_name",
    )
    experiences_by_id: dict[UUID, ProjectionExperience] = {}
    views_by_id: dict[UUID, ProjectionExperienceView] = {}
    view_instances_by_id: dict[UUID, ProjectionExperienceViewInstance] = {}
    view_action_configs_by_id: dict[
        UUID, ProjectionExperienceViewInvocationActionConfig
    ] = {}
    experience_action_configs_by_id: dict[UUID, ExperienceInvocationActionConfig] = {}
    api_view_capability_endpoints_by_id: dict[UUID, ApiViewCapabilityEndpoint] = {}

    for obj in session.imap_all_objects():
        if isinstance(obj, ProjectionExperience) and obj.id is not None:
            experiences_by_id[obj.id] = obj
            continue
        if isinstance(obj, ProjectionExperienceView) and obj.id is not None:
            views_by_id[obj.id] = obj
            continue
        if isinstance(obj, ProjectionExperienceViewInstance) and obj.id is not None:
            view_instances_by_id[obj.id] = obj
            continue
        if (
            isinstance(obj, ProjectionExperienceViewInvocationActionConfig)
            and obj.id is not None
        ):
            view_action_configs_by_id[obj.id] = obj
            continue
        if isinstance(obj, ExperienceInvocationActionConfig) and obj.id is not None:
            experience_action_configs_by_id[obj.id] = obj
            continue
        if isinstance(obj, ApiViewCapabilityEndpoint) and obj.id is not None:
            api_view_capability_endpoints_by_id[obj.id] = obj

    view_instance = view_instances_by_id.get(projection_experience_view_instance_id)
    if view_instance is None:
        raise ValueError(
            "Unknown ProjectionExperienceViewInstance for invocation action record: "
            + f"projection_experience_view_instance_id={projection_experience_view_instance_id}"
        )
    view = views_by_id.get(view_instance.projection_experience_view_id)
    if view is None:
        raise ValueError(
            "ProjectionExperienceViewInstance references missing ProjectionExperienceView: "
            + f"projection_experience_view_instance_id={projection_experience_view_instance_id} "
            + f"projection_experience_view_id={view_instance.projection_experience_view_id}"
        )
    experience = experiences_by_id.get(view.projection_experience_id)
    if experience is None:
        raise ValueError(
            "ProjectionExperienceView references missing ProjectionExperience: "
            + f"projection_experience_view_id={view.id} "
            + f"projection_experience_id={view.projection_experience_id}"
        )
    if experience.name.strip().casefold() != normalized_experience_name.casefold():
        raise ValueError(
            "ProjectionExperienceViewInstance does not belong to requested Experience: "
            + f"requested_experience_name={normalized_experience_name!r} "
            + f"resolved_experience_name={experience.name!r} "
            + f"projection_experience_view_instance_id={projection_experience_view_instance_id}"
        )
    view_action_config = view_action_configs_by_id.get(view_invocation_action_config_id)
    if view_action_config is None:
        raise ValueError(
            "Unknown ProjectionExperienceViewInvocationActionConfig for invocation "
            + "action record: "
            + f"view_invocation_action_config_id={view_invocation_action_config_id}"
        )
    if view_action_config.projection_experience_view_id != view.id:
        raise ValueError(
            "ProjectionExperienceViewInvocationActionConfig does not belong to "
            + "the selected view instance view: "
            + f"projection_experience_view_instance_id={projection_experience_view_instance_id} "
            + f"projection_experience_view_id={view.id} "
            + f"view_invocation_action_config_id={view_invocation_action_config_id}"
        )
    experience_action_config_id = (
        view_action_config.experience_invocation_action_config_id
    )
    if experience_action_config_id is None:
        raise ValueError(
            "ProjectionExperienceViewInvocationActionConfig.experience_invocation_action_config_id "
            + "is required: "
            + f"view_invocation_action_config_id={view_invocation_action_config_id}"
        )
    experience_action_config = experience_action_configs_by_id.get(
        experience_action_config_id
    )
    if experience_action_config is None:
        experience_action_config = (
            view_action_config.experience_invocation_action_config
        )
    if experience_action_config is None or experience_action_config.id is None:
        raise ValueError(
            "ProjectionExperienceViewInvocationActionConfig references missing "
            + "ExperienceInvocationActionConfig: "
            + f"view_invocation_action_config_id={view_invocation_action_config_id} "
            + f"experience_invocation_action_config_id={experience_action_config_id}"
        )
    if experience_action_config.id != experience_action_config_id:
        raise ValueError(
            "ProjectionExperienceViewInvocationActionConfig references mismatched "
            + "ExperienceInvocationActionConfig: "
            + f"view_invocation_action_config_id={view_invocation_action_config_id} "
            + f"expected={experience_action_config_id} "
            + f"actual={experience_action_config.id}"
        )
    if experience_action_config.projection_experience_id != experience.id:
        raise ValueError(
            "ExperienceInvocationActionConfig belongs to a different ProjectionExperience: "
            + f"view_invocation_action_config_id={view_invocation_action_config_id} "
            + f"experience_invocation_action_config_id={experience_action_config.id}"
        )
    api_view_capability_endpoint_id = view_action_config.api_view_capability_endpoint_id
    if api_view_capability_endpoint_id is None:
        raise ValueError(
            "ProjectionExperienceViewInvocationActionConfig.api_view_capability_endpoint_id "
            + "is required: "
            + f"view_invocation_action_config_id={view_invocation_action_config_id}"
        )
    api_view_capability_endpoint = api_view_capability_endpoints_by_id.get(
        api_view_capability_endpoint_id
    )
    if api_view_capability_endpoint is None:
        api_view_capability_endpoint = view_action_config.api_view_capability_endpoint
    if api_view_capability_endpoint is None or api_view_capability_endpoint.id is None:
        raise ValueError(
            "ProjectionExperienceViewInvocationActionConfig references missing "
            + "ApiViewCapabilityEndpoint: "
            + f"view_invocation_action_config_id={view_invocation_action_config_id} "
            + f"api_view_capability_endpoint_id={api_view_capability_endpoint_id}"
        )
    if api_view_capability_endpoint.id != api_view_capability_endpoint_id:
        raise ValueError(
            "ProjectionExperienceViewInvocationActionConfig references mismatched "
            + "ApiViewCapabilityEndpoint: "
            + f"view_invocation_action_config_id={view_invocation_action_config_id} "
            + f"expected={api_view_capability_endpoint_id} "
            + f"actual={api_view_capability_endpoint.id}"
        )
    if api_view_capability_endpoint.api_view_id != view.api_view_id:
        raise ValueError(
            "ProjectionExperienceViewInvocationActionConfig ApiViewCapabilityEndpoint "
            + "does not belong to the selected ProjectionExperienceView api_view"
        )
    if (
        experience_action_config.api_capability_endpoint_id is not None
        and experience_action_config.api_capability_endpoint_id
        != api_view_capability_endpoint.api_capability_endpoint_id
    ):
        raise ValueError(
            "ExperienceInvocationActionConfig API endpoint target does not match "
            + "ApiViewCapabilityEndpoint: "
            + f"view_invocation_action_config_id={view_invocation_action_config_id}"
        )
    return _ViewInvocationActionRecordingTarget(
        experience_name=experience.name,
        projection_experience_view_instance_id=projection_experience_view_instance_id,
        projection_experience_view_id=view.id,
        view_invocation_action_config_id=view_invocation_action_config_id,
        experience_invocation_action_config_id=experience_action_config.id,
        api_view_capability_endpoint_id=api_view_capability_endpoint_id,
        action_key=_normalize_required_text(
            view_action_config.action_key,
            label="projection_experience_view_invocation_action_config.action_key",
        ),
        target_kind=_normalize_required_text(
            experience_action_config.target_kind.value,
            label="experience_invocation_action_config.target_kind",
        ),
        endpoint_ref=_normalize_required_text(
            api_view_capability_endpoint.endpoint_ref,
            label="api_view_capability_endpoint.endpoint_ref",
        ),
        sdk_operation_api_view_capability_endpoint_id=(
            view_action_config.sdk_operation_api_view_capability_endpoint_id
        ),
        api_capability_endpoint_id=(
            api_view_capability_endpoint.api_capability_endpoint_id
        ),
        sdk_operation_id=experience_action_config.sdk_operation_id,
    )


async def _record_view_invocation_action_for_target(
    *,
    runtime_context: _SectionGraphBindingRuntimeContext,
    target: _ViewInvocationActionRecordingTarget,
    invocation_key: UUID,
    actor_id: UUID | None,
    api_call_id: UUID | None,
    sdk_operation_call_id: UUID | None,
    request_ref: str | None,
    receipt_ref: str | None,
    status: str,
) -> ExperienceViewInvocationActionReceipt:
    experience_invocation_action_id = stable_experience_invocation_action_id(
        experience_invocation_action_config_id=(
            target.experience_invocation_action_config_id
        ),
        invocation_key=invocation_key,
    )
    projection_experience_view_invocation_action_id = (
        stable_projection_experience_view_invocation_action_id(
            view_invocation_action_config_id=target.view_invocation_action_config_id,
            experience_invocation_action_id=experience_invocation_action_id,
        )
    )
    invoke_response = await _invoke_view_instance_record_action_invocation(
        runtime_context=runtime_context,
        projection_experience_view_instance_id=(
            target.projection_experience_view_instance_id
        ),
        view_invocation_action_config_id=target.view_invocation_action_config_id,
        invocation_key=invocation_key,
        actor_id=actor_id,
        api_call_id=api_call_id,
        sdk_operation_call_id=sdk_operation_call_id,
        request_ref=request_ref,
        receipt_ref=receipt_ref,
        status=status,
    )
    return ExperienceViewInvocationActionReceipt(
        projection_experience_view_instance_id=(
            target.projection_experience_view_instance_id
        ),
        view_invocation_action_config_id=target.view_invocation_action_config_id,
        experience_invocation_action_config_id=(
            target.experience_invocation_action_config_id
        ),
        experience_invocation_action_id=experience_invocation_action_id,
        projection_experience_view_invocation_action_id=(
            projection_experience_view_invocation_action_id
        ),
        invocation_key=invocation_key,
        actor_id=actor_id,
        api_call_id=api_call_id,
        sdk_operation_call_id=sdk_operation_call_id,
        request_ref=request_ref,
        receipt_ref=receipt_ref,
        status=status,
        object_instance_graph_commit_id=invoke_response.object_instance_graph_commit_id,
        commit_id=invoke_response.commit_id,
    )


async def _attach_invocation_action_commit_evidence(
    *,
    runtime_context: _SectionGraphBindingRuntimeContext,
    experience_invocation_action_id: UUID,
    commit_evidence: tuple[_InvocationCommitEvidence, ...],
    actor_id: UUID | None,
) -> None:
    if not commit_evidence:
        return
    invocation_action_projection_hash = _require_projection_hash(
        runtime_index=runtime_context.runtime_index,
        name="ExperienceInvocationAction",
    )
    add_commit_target = _resolve_invocation_function_target(
        runtime_context=runtime_context,
        class_fqn=(
            "aware_experience_ontology.invocation."
            "experience_invocation_action.ExperienceInvocationAction"
        ),
        function_name="add_commit",
        projection_hash=invocation_action_projection_hash,
    )
    add_event_target = (
        _resolve_invocation_function_target(
            runtime_context=runtime_context,
            class_fqn=(
                "aware_experience_ontology.invocation."
                "experience_invocation_action_commit.ExperienceInvocationActionCommit"
            ),
            function_name="add_event",
            projection_hash=invocation_action_projection_hash,
        )
        if any(evidence.event_evidence for evidence in commit_evidence)
        else None
    )
    for evidence in commit_evidence:
        await _invoke_experience_invocation_action_add_commit(
            runtime_context=runtime_context,
            function_target=add_commit_target,
            experience_invocation_action_id=experience_invocation_action_id,
            object_instance_graph_commit_id=evidence.object_instance_graph_commit_id,
            commit_role=evidence.commit_role,
            description=evidence.description,
            actor_id=actor_id,
        )
        if evidence.event_evidence:
            experience_invocation_action_commit_id = (
                stable_experience_invocation_action_commit_id(
                    experience_invocation_action_id=experience_invocation_action_id,
                    object_instance_graph_commit_id=(
                        evidence.object_instance_graph_commit_id
                    ),
                )
            )
            await _attach_invocation_action_commit_event_evidence(
                runtime_context=runtime_context,
                function_target=add_event_target,
                experience_invocation_action_commit_id=(
                    experience_invocation_action_commit_id
                ),
                event_evidence=evidence.event_evidence,
                actor_id=actor_id,
            )


async def _attach_invocation_action_commit_event_evidence(
    *,
    runtime_context: _SectionGraphBindingRuntimeContext,
    function_target: _InvocationFunctionTarget | None,
    experience_invocation_action_commit_id: UUID,
    event_evidence: tuple[_InvocationCommitEventEvidence, ...],
    actor_id: UUID | None,
) -> None:
    if function_target is None:
        raise RuntimeError(
            "Experience invocation action commit event function target is required "
            "when event evidence is present."
        )
    for evidence in event_evidence:
        await _invoke_experience_invocation_action_commit_add_event(
            runtime_context=runtime_context,
            function_target=function_target,
            experience_invocation_action_commit_id=(
                experience_invocation_action_commit_id
            ),
            event_id=evidence.event_id,
            event_role=evidence.event_role,
            description=evidence.description,
            actor_id=actor_id,
        )


def _api_dispatch_commit_evidence(
    *,
    receipt: ExperienceViewInvocationActionApiDispatchReceipt,
) -> tuple[_InvocationCommitEvidence, ...]:
    candidates = (
        (
            receipt.service_operation_commit_id,
            "service_operation",
            "API dispatch service operation commit",
            getattr(receipt, "service_operation_event_ids", ()),
            "API dispatch service operation emitted event",
        ),
        (
            receipt.service_operation_head_commit_id,
            "service_operation_head",
            "API dispatch service operation head commit",
            getattr(receipt, "service_operation_head_event_ids", ()),
            "API dispatch service operation head emitted event",
        ),
        (
            receipt.api_call_outcome_commit_id,
            "api_call_outcome",
            "API dispatch call outcome commit",
            getattr(receipt, "api_call_outcome_event_ids", ()),
            "API dispatch call outcome emitted event",
        ),
        (
            receipt.api_call_outcome_head_commit_id,
            "api_call_outcome_head",
            "API dispatch call outcome head commit",
            getattr(receipt, "api_call_outcome_head_event_ids", ()),
            "API dispatch call outcome head emitted event",
        ),
    )
    evidence_by_commit_id: dict[UUID, _InvocationCommitEvidenceAccumulator] = {}
    commit_order: list[UUID] = []
    for commit_id, commit_role, description, event_ids, event_description in candidates:
        if commit_id is None:
            continue
        accumulator = evidence_by_commit_id.get(commit_id)
        if accumulator is None:
            accumulator = _InvocationCommitEvidenceAccumulator(
                object_instance_graph_commit_id=commit_id,
                commit_role=commit_role,
                description=description,
                event_evidence=[],
                seen_event_ids=set(),
            )
            evidence_by_commit_id[commit_id] = accumulator
            commit_order.append(commit_id)
        for event_id in _iter_api_dispatch_event_ids(event_ids=event_ids):
            if event_id in accumulator.seen_event_ids:
                continue
            accumulator.seen_event_ids.add(event_id)
            accumulator.event_evidence.append(
                _InvocationCommitEventEvidence(
                    event_id=event_id,
                    event_role="emitted",
                    description=event_description,
                )
            )
    ordered_accumulators = (
        evidence_by_commit_id[commit_id] for commit_id in commit_order
    )
    return tuple(
        _InvocationCommitEvidence(
            object_instance_graph_commit_id=accumulator.object_instance_graph_commit_id,
            commit_role=accumulator.commit_role,
            description=accumulator.description,
            event_evidence=tuple(accumulator.event_evidence),
        )
        for accumulator in ordered_accumulators
    )


def _iter_api_dispatch_event_ids(
    *,
    event_ids: object,
) -> Iterator[UUID]:
    if event_ids is None:
        return
    if isinstance(event_ids, UUID):
        yield event_ids
        return
    if isinstance(event_ids, str):
        yield UUID(event_ids)
        return
    try:
        raw_event_ids = iter(cast(Any, event_ids))
    except TypeError:
        yield UUID(str(event_ids))
        return
    for raw_event_id in raw_event_ids:
        yield (
            raw_event_id if isinstance(raw_event_id, UUID) else UUID(str(raw_event_id))
        )


def _api_endpoint_ref_for_view_invocation_target(
    *,
    target: _ViewInvocationActionRecordingTarget,
) -> str:
    if target.api_capability_endpoint_id is None:
        raise ValueError(
            "API-backed ApiViewCapabilityEndpoint requires "
            + "api_capability_endpoint_id: "
            + f"action_key={target.action_key!r} endpoint_ref={target.endpoint_ref!r}"
        )
    parts = _api_endpoint_ref_parts(endpoint_ref=target.endpoint_ref)
    return ".".join(parts)


def _api_endpoint_ref_parts(*, endpoint_ref: str) -> tuple[str, str, str]:
    parts = tuple(part.strip() for part in endpoint_ref.split(".") if part.strip())
    if len(parts) != 3:
        raise ValueError(
            "API-backed ApiViewCapabilityEndpoint.endpoint_ref must use "
            + "`api.capability.endpoint`: "
            + f"endpoint_ref={endpoint_ref!r}"
        )
    return cast(tuple[str, str, str], parts)


def _api_package_name_for_target(
    *, target: _ViewInvocationActionRecordingTarget
) -> str:
    api_name, _capability_name, _endpoint_name = _api_endpoint_ref_parts(
        endpoint_ref=target.endpoint_ref,
    )
    return f"{api_name}-service-api"


def _require_view_invocation_action_api_invoker(
    *,
    host_context: ServiceApiHostContext,
    target: _ViewInvocationActionRecordingTarget,
    request: InvokeExperienceViewInvocationActionRequest,
) -> Any:
    api_package_name = _api_package_name_for_target(target=target)
    client = build_service_api_client_for_api_package(
        host_context.service_api_dependency_routes,
        api_package_name=api_package_name,
        actor_id=request.actor_id or host_context.operation_context.actor_id,
        invocation_context=_view_invocation_context_payload(
            host_context=host_context,
            target=target,
            request=request,
        ),
    )
    if client is None:
        raise RuntimeError(
            "Experience view action API invocation requires a Service API "
            + "dependency route for "
            + f"{api_package_name!r}."
        )
    return client


def _view_invocation_context_payload(
    *,
    host_context: ServiceApiHostContext,
    target: _ViewInvocationActionRecordingTarget,
    request: InvokeExperienceViewInvocationActionRequest,
) -> JsonObject:
    payload: dict[str, object] = {}
    if host_context.invocation_context is not None:
        payload.update(dict(host_context.invocation_context))
    payload["experience_invocation"] = _drop_none(
        {
            "experience_name": target.experience_name,
            "projection_experience_view_instance_id": str(
                target.projection_experience_view_instance_id
            ),
            "view_invocation_action_config_id": str(
                target.view_invocation_action_config_id
            ),
            "experience_invocation_action_config_id": str(
                target.experience_invocation_action_config_id
            ),
            "invocation_key": str(request.invocation_key),
            "action_key": target.action_key,
            "target_kind": target.target_kind,
            "endpoint_ref": target.endpoint_ref,
            "api_view_capability_endpoint_id": str(
                target.api_view_capability_endpoint_id
            ),
            "sdk_operation_api_view_capability_endpoint_id": (
                str(target.sdk_operation_api_view_capability_endpoint_id)
                if target.sdk_operation_api_view_capability_endpoint_id is not None
                else None
            ),
            "api_capability_endpoint_id": (
                str(target.api_capability_endpoint_id)
                if target.api_capability_endpoint_id is not None
                else None
            ),
            "sdk_operation_id": (
                str(target.sdk_operation_id)
                if target.sdk_operation_id is not None
                else None
            ),
        }
    )
    service_role_evidence = _view_invocation_service_actor_role_evidence(
        request=request,
    )
    if service_role_evidence:
        service_context = _mapping_payload(
            payload.get("service_operation_admission_context")
        )
        service_context.setdefault(
            "actor_context",
            _drop_none(
                {
                    "status": "ready",
                    "kind": "experience_service",
                    "source": "aware_experience.view_invocation_action",
                    "actor_id": str(
                        request.actor_id or host_context.operation_context.actor_id
                    ),
                    "evidence": {
                        "source": "aware_experience.section_graph_binding.service",
                        "experience_name": target.experience_name,
                        "action_key": target.action_key,
                    },
                }
            ),
        )
        service_context["service_actor_role_evidence"] = service_role_evidence
        payload["service_operation_admission_context"] = service_context
    return cast(JsonObject, payload)


def _view_invocation_service_actor_role_evidence(
    *,
    request: InvokeExperienceViewInvocationActionRequest,
) -> list[JsonObject]:
    matched_role_config_id = _matched_preflight_role_config_id(
        admission_evidence=request.admission_evidence,
    )
    if matched_role_config_id is None:
        return []
    evidence_items: list[JsonObject] = []
    for binding in request.admitted_actor_role_bindings:
        if binding.role_config_id != matched_role_config_id:
            continue
        evidence_items.append(
            cast(
                JsonObject,
                _drop_none(
                    {
                        "source": "aware_experience.view_invocation_action_admission",
                        "role_config_id": str(binding.role_config_id),
                        "role_config_name": binding.role_config_name,
                        "actor_id": str(binding.actor_id),
                        "actor_role_id": str(binding.actor_role_id),
                        "access_scope": "operation",
                        "scope_kind": "operation",
                        "scope_ref": "default",
                        "class_instance_identity_id": str(
                            binding.class_instance_identity_id
                        ),
                        # Identity RoleAssignmentBinding is an inline value today; the
                        # concrete ActorRole id is the stable binding identity carried
                        # forward for ServiceActorRoleEvidence non-null checks.
                        "role_assignment_binding_id": str(binding.actor_role_id),
                        "granted": True,
                    },
                ),
            ),
        )
    return evidence_items


def _matched_preflight_role_config_id(
    *,
    admission_evidence: JsonObject,
) -> UUID | None:
    preflight = _mapping_payload(
        admission_evidence.get("experience_invocation_action_admission_preflight")
    )
    role_config_id = preflight.get("matched_role_config_id")
    if role_config_id is None:
        return None
    try:
        return (
            role_config_id
            if isinstance(role_config_id, UUID)
            else UUID(str(role_config_id))
        )
    except ValueError:
        return None


def _mapping_payload(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    return {}


def _require_api_dispatch_receipt(
    *,
    receipt: object,
    target: _ViewInvocationActionRecordingTarget,
) -> ExperienceViewInvocationActionApiDispatchReceipt:
    if receipt is None:
        raise RuntimeError(
            "Experience view action API invocation requires Service/API dispatch "
            + "receipt metadata from target API call: "
            + f"action_key={target.action_key!r} endpoint_ref={target.endpoint_ref!r}"
        )
    if isinstance(receipt, ExperienceViewInvocationActionApiDispatchReceipt):
        return receipt
    payload = (
        receipt.model_dump(mode="json", exclude_none=True)
        if isinstance(receipt, BaseModel)
        else dict(cast(dict[str, object], receipt))
    )
    return ExperienceViewInvocationActionApiDispatchReceipt.model_validate(payload)


def _require_api_dispatch_receipt_matches_target(
    *,
    receipt: ExperienceViewInvocationActionApiDispatchReceipt,
    target: _ViewInvocationActionRecordingTarget,
) -> None:
    if receipt.api_capability_endpoint_id is None:
        return
    if receipt.api_capability_endpoint_id == target.api_capability_endpoint_id:
        return
    raise ValueError(
        "Service/API dispatch receipt endpoint does not match committed "
        + "ApiViewCapabilityEndpoint target: "
        + f"endpoint_ref={target.endpoint_ref!r} "
        + f"expected_api_capability_endpoint_id={target.api_capability_endpoint_id} "
        + f"actual_api_capability_endpoint_id={receipt.api_capability_endpoint_id}"
    )


def _api_dispatch_receipt_ref(
    *,
    receipt: ExperienceViewInvocationActionApiDispatchReceipt,
) -> str:
    if receipt.api_call_id is not None:
        return f"api_call:{receipt.api_call_id}"
    if receipt.call_key is not None:
        return f"api_call_key:{receipt.call_key}"
    return f"api_endpoint:{receipt.endpoint_ref}"


def _json_value_payload(value: object) -> object | None:
    if value is None:
        return None
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, list):
        return [_json_value_payload(item) for item in value]
    if isinstance(value, tuple):
        return [_json_value_payload(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _json_value_payload(item)
            for key, item in cast(dict[object, object], value).items()
        }
    return value


def _require_section_view_resolution_matches_entry(
    *,
    resolution: ExperienceSectionObservableViewResolution,
    entry: ExperienceSectionGraphBindingCatalogEntry,
    section_id: UUID,
) -> None:
    if (
        entry.projection_experience_view_id is not None
        and resolution.projection_experience_view_id
        != entry.projection_experience_view_id
    ):
        raise ValueError(
            "Resolved section observable view instance does not match transition "
            "target view config: "
            + f"section_id={section_id} "
            + f"resolved_view_id={resolution.projection_experience_view_id} "
            + f"target_view_id={entry.projection_experience_view_id}"
        )
    if (
        entry.section_graph_binding_id is not None
        and resolution.section_graph_binding_id != entry.section_graph_binding_id
    ):
        raise ValueError(
            "Resolved section observable view instance does not match transition "
            "target section graph binding: "
            + f"section_id={section_id} "
            + f"resolved_section_graph_binding_id={resolution.section_graph_binding_id} "
            + f"target_section_graph_binding_id={entry.section_graph_binding_id}"
        )
    if resolution.view_ref != entry.descriptor.view_ref:
        raise ValueError(
            "Resolved section observable view instance does not match transition "
            "target view ref: "
            + f"resolved_view_ref={resolution.view_ref!r} "
            + f"target_view_ref={entry.descriptor.view_ref!r}"
        )


def _section_view_resolution_dto(
    *,
    resolution: ExperienceSectionObservableViewResolution,
    actions: tuple[object, ...],
) -> ExperienceSectionViewResolution:
    return ExperienceSectionViewResolution(
        projection_experience_id=resolution.projection_experience_id,
        section_id=resolution.section_id,
        object_projection_graph_observable_id=(
            resolution.object_projection_graph_observable_id
        ),
        projection_experience_section_id=resolution.projection_experience_section_id,
        projection_experience_section_view_id=(
            resolution.projection_experience_section_view_id
        ),
        projection_experience_view_instance_id=(
            resolution.projection_experience_view_instance_id
        ),
        projection_experience_view_id=resolution.projection_experience_view_id,
        section_graph_binding_id=resolution.section_graph_binding_id,
        view_ref=resolution.view_ref,
        view_instance_key=resolution.view_instance_key,
        section_key=resolution.section_key,
        status=resolution.status,
        actions=[
            _view_invocation_action_descriptor(action=action) for action in actions
        ],
    )


def _view_invocation_action_descriptor(
    *,
    action: object,
) -> ExperienceViewInvocationActionDescriptor:
    view_invocation_action_config_id = cast(
        UUID | None,
        getattr(action, "view_invocation_action_config_id", None)
        or getattr(action, "id", None),
    )
    experience_invocation_action_config_id = cast(
        UUID | None,
        getattr(action, "experience_invocation_action_config_id", None),
    )
    action_id = view_invocation_action_config_id
    if action_id is None:
        raise ValueError(
            "ProjectionExperienceViewInvocationActionConfig.id is required"
        )
    if view_invocation_action_config_id is None:
        raise ValueError(
            "Experience view invocation action descriptor requires "
            "view_invocation_action_config_id."
        )
    if experience_invocation_action_config_id is None:
        raise ValueError(
            "Experience view invocation action descriptor requires "
            "experience_invocation_action_config_id."
        )
    api_view_capability_endpoint_id = cast(
        UUID | None,
        getattr(action, "api_view_capability_endpoint_id", None),
    )
    if api_view_capability_endpoint_id is None:
        raise ValueError(
            "Experience view invocation action descriptor requires "
            "api_view_capability_endpoint_id."
        )
    return ExperienceViewInvocationActionDescriptor(
        action_id=action_id,
        view_invocation_action_config_id=view_invocation_action_config_id,
        experience_invocation_action_config_id=experience_invocation_action_config_id,
        api_view_capability_endpoint_id=api_view_capability_endpoint_id,
        action_key=_normalize_required_text(
            getattr(action, "action_key", None),
            label="view_invocation_action.action_key",
        ),
        target_kind=_normalize_required_text(
            getattr(action, "target_kind", None),
            label="view_invocation_action.target_kind",
        ),
        endpoint_ref=_normalize_required_text(
            getattr(action, "endpoint_ref", None),
            label="view_invocation_action.endpoint_ref",
        ),
        label=_normalize_optional_text(getattr(action, "label", None)),
        receipt_policy=_normalize_optional_text(
            getattr(action, "receipt_policy", None)
        ),
        confirmation_policy=_normalize_optional_text(
            getattr(action, "confirmation_policy", None)
        ),
        optimistic_policy=_normalize_optional_text(
            getattr(action, "optimistic_policy", None)
        ),
        sdk_operation_api_view_capability_endpoint_id=cast(
            UUID | None,
            getattr(action, "sdk_operation_api_view_capability_endpoint_id", None),
        ),
        api_capability_endpoint_id=cast(
            UUID | None,
            getattr(action, "api_capability_endpoint_id", None),
        ),
        sdk_operation_id=cast(UUID | None, getattr(action, "sdk_operation_id", None)),
    )


async def _resolve_runtime_context(
    *,
    host_context: ServiceApiHostContext,
    experience_name: str,
    projection_names: tuple[str, ...] = _SECTION_GRAPH_BINDING_PROJECTION_NAMES,
) -> _SectionGraphBindingRuntimeContext:
    graph_gateway = host_context.graph_gateway
    if graph_gateway is None:
        raise RuntimeError(
            "Experience section-graph-binding service requires a Service graph gateway."
        )
    branch_id = (
        _experience_reference_branch_id(
            host_context=host_context,
            experience_name=experience_name,
        )
        or host_context.operation_context.branch_id
    )
    if branch_id is None:
        raise ValueError(
            "Experience section-graph-binding service requires branch_id on operation context."
        )
    runtime_index = await _resolve_runtime_index(
        host_context=host_context,
        graph_gateway=graph_gateway,
    )
    projection_hashes = tuple(
        _require_projection_hash(runtime_index=runtime_index, name=name)
        for name in projection_names
    )
    return _SectionGraphBindingRuntimeContext(
        host_context=host_context,
        graph_gateway=graph_gateway,
        runtime_index=runtime_index,
        branch_id=branch_id,
        projection_hashes=projection_hashes,
    )


async def _resolve_runtime_index(
    *,
    host_context: ServiceApiHostContext,
    graph_gateway: object,
) -> MetaGraphRuntimeIndex:
    if host_context.materialization is not None:
        return _coerce_runtime_index(host_context.materialization.graph_context)
    if host_context.graph_context_provider is not None:
        return _coerce_runtime_index(
            await host_context.graph_context_provider.resolve_graph_context()
        )
    resolve_graph_context = getattr(graph_gateway, "resolve_graph_context", None)
    if callable(resolve_graph_context):
        return _coerce_runtime_index(await resolve_graph_context())
    raise RuntimeError(
        "Experience section-graph-binding service requires a Service graph context."
    )


def _coerce_runtime_index(graph_context: object) -> MetaGraphRuntimeIndex:
    return cast(
        MetaGraphRuntimeIndex,
        getattr(graph_context, "index", graph_context),
    )


async def _invoke_view_instance_record_action_invocation(
    *,
    runtime_context: _SectionGraphBindingRuntimeContext,
    projection_experience_view_instance_id: UUID,
    view_invocation_action_config_id: UUID,
    invocation_key: UUID,
    actor_id: UUID | None,
    api_call_id: UUID | None,
    sdk_operation_call_id: UUID | None,
    request_ref: str | None,
    receipt_ref: str | None,
    status: str,
) -> InvokeFunctionResponse:
    class_config = _require_class_config(
        runtime_index=runtime_context.runtime_index,
        class_fqn=(
            "aware_experience_ontology.projection."
            "projection_experience_view_instance.ProjectionExperienceViewInstance"
        ),
    )
    function_id = _require_function_id(
        class_config,
        name="record_action_invocation",
    )
    response = await runtime_context.graph_gateway.invoke_function(
        request=InvokeFunctionRequest(
            actor_id=actor_id
            or runtime_context.host_context.operation_context.actor_id,
            **_environment_invoke_context(host_context=runtime_context.host_context),
            branch_id=runtime_context.branch_id,
            projection_hash=_require_projection_hash(
                runtime_index=runtime_context.runtime_index,
                name="ProjectionExperience",
            ),
            call_target=InvokeFunctionCallTarget.instance,
            object_id=projection_experience_view_instance_id,
            object_projection_graph_id=None,
            function_id=function_id,
            args=cast(JsonArray, []),
            kwargs=cast(
                JsonObject,
                _drop_none(
                    {
                        "view_invocation_action_config_id": view_invocation_action_config_id,
                        "invocation_key": invocation_key,
                        "actor_id": actor_id,
                        "api_call_id": api_call_id,
                        "sdk_operation_call_id": sdk_operation_call_id,
                        "request_ref": request_ref,
                        "receipt_ref": receipt_ref,
                        "status": status,
                    }
                ),
            ),
            expected_graph_hash_pre=None,
            expected_head_commit_id=None,
            commit=True,
            publish=False,
        ),
        graph_context=runtime_context.runtime_index,
    )
    _ensure_invoke_succeeded(
        response=response,
        context="Experience view invocation action record",
    )
    return response


async def _invoke_experience_invocation_action_add_commit(
    *,
    runtime_context: _SectionGraphBindingRuntimeContext,
    function_target: _InvocationFunctionTarget,
    experience_invocation_action_id: UUID,
    object_instance_graph_commit_id: UUID,
    commit_role: str,
    description: str,
    actor_id: UUID | None,
) -> InvokeFunctionResponse:
    response = await runtime_context.graph_gateway.invoke_function(
        request=InvokeFunctionRequest(
            actor_id=actor_id
            or runtime_context.host_context.operation_context.actor_id,
            **_environment_invoke_context(host_context=runtime_context.host_context),
            branch_id=runtime_context.branch_id,
            projection_hash=function_target.projection_hash,
            call_target=InvokeFunctionCallTarget.instance,
            object_id=experience_invocation_action_id,
            object_projection_graph_id=None,
            function_id=function_target.function_id,
            args=cast(JsonArray, []),
            kwargs=cast(
                JsonObject,
                {
                    "object_instance_graph_commit_id": object_instance_graph_commit_id,
                    "commit_role": commit_role,
                    "description": description,
                },
            ),
            expected_graph_hash_pre=None,
            expected_head_commit_id=None,
            commit=True,
            publish=False,
        ),
        graph_context=runtime_context.runtime_index,
    )
    _ensure_invoke_succeeded(
        response=response,
        context="Experience invocation action commit evidence attachment",
    )
    return response


async def _invoke_experience_invocation_action_commit_add_event(
    *,
    runtime_context: _SectionGraphBindingRuntimeContext,
    function_target: _InvocationFunctionTarget,
    experience_invocation_action_commit_id: UUID,
    event_id: UUID,
    event_role: str,
    description: str,
    actor_id: UUID | None,
) -> InvokeFunctionResponse:
    response = await runtime_context.graph_gateway.invoke_function(
        request=InvokeFunctionRequest(
            actor_id=actor_id
            or runtime_context.host_context.operation_context.actor_id,
            **_environment_invoke_context(host_context=runtime_context.host_context),
            branch_id=runtime_context.branch_id,
            projection_hash=function_target.projection_hash,
            call_target=InvokeFunctionCallTarget.instance,
            object_id=experience_invocation_action_commit_id,
            object_projection_graph_id=None,
            function_id=function_target.function_id,
            args=cast(JsonArray, []),
            kwargs=cast(
                JsonObject,
                {
                    "event_id": event_id,
                    "event_role": event_role,
                    "description": description,
                },
            ),
            expected_graph_hash_pre=None,
            expected_head_commit_id=None,
            commit=True,
            publish=False,
        ),
        graph_context=runtime_context.runtime_index,
    )
    _ensure_invoke_succeeded(
        response=response,
        context="Experience invocation action commit event evidence attachment",
    )
    return response


def _resolve_invocation_function_target(
    *,
    runtime_context: _SectionGraphBindingRuntimeContext,
    class_fqn: str,
    function_name: str,
    projection_hash: str,
) -> _InvocationFunctionTarget:
    class_config = _require_class_config(
        runtime_index=runtime_context.runtime_index,
        class_fqn=class_fqn,
    )
    return _InvocationFunctionTarget(
        function_id=_require_function_id(class_config, name=function_name),
        projection_hash=projection_hash,
    )


def _require_class_config(
    *, runtime_index: MetaGraphRuntimeIndex, class_fqn: str
) -> object:
    matches = [
        class_config
        for class_config in getattr(runtime_index, "class_configs_by_id", {}).values()
        if str(
            getattr(class_config, "fqn", None)
            or getattr(class_config, "class_fqn", "")
            or ""
        )
        == class_fqn
    ]
    if not matches:
        class_name = class_fqn.rsplit(".", 1)[-1]
        matches = [
            class_config
            for class_config in getattr(
                runtime_index,
                "class_configs_by_id",
                {},
            ).values()
            if str(getattr(class_config, "name", "") or "") == class_name
            and "experience" in str(getattr(class_config, "class_fqn", "") or "")
        ]
    if not matches:
        class_name = class_fqn.rsplit(".", 1)[-1]
        matches = [
            class_config
            for class_config in getattr(
                runtime_index,
                "class_configs_by_id",
                {},
            ).values()
            if str(getattr(class_config, "name", "") or "") == class_name
        ]
    if not matches:
        raise ValueError(
            f"Experience class config `{class_fqn}` is missing from runtime index."
        )
    if len(matches) != 1:
        raise ValueError(
            f"Experience class config `{class_fqn}` is ambiguous in runtime index: "
            + f"expected 1, found {len(matches)}"
        )
    return matches[0]


def _require_function_id(class_config: object, *, name: str) -> UUID:
    function_ids = [
        function_config.id
        for link in getattr(class_config, "class_config_function_configs", []) or []
        for function_config in [getattr(link, "function_config", None)]
        if function_config is not None
        and (getattr(function_config, "name", "") or "").strip() == name
    ]
    class_fqn = str(
        getattr(class_config, "fqn", None)
        or getattr(class_config, "class_fqn", "")
        or ""
    )
    if not function_ids:
        raise ValueError(
            f"Experience function `{class_fqn}.{name}` is missing from runtime index."
        )
    if len(function_ids) != 1:
        raise ValueError(
            f"Experience function `{class_fqn}.{name}` is ambiguous in runtime index: "
            + f"expected 1, found {len(function_ids)}"
        )
    return function_ids[0]


def _ensure_invoke_succeeded(
    *,
    response: InvokeFunctionResponse,
    context: str,
) -> None:
    if (response.status or "").strip().casefold() == "succeeded":
        return
    raise RuntimeError(f"{context} failed: {response.error or response.status}")


async def hydrate_experience_reference_session(
    *,
    host_context: ServiceApiHostContext,
    experience_name: str,
    projection_names: tuple[str, ...] = _SECTION_GRAPH_BINDING_PROJECTION_NAMES,
) -> Session:
    runtime_context = await _resolve_runtime_context(
        host_context=host_context,
        experience_name=experience_name,
        projection_names=projection_names,
    )
    return await _hydrate_section_graph_binding_session(
        runtime_context=runtime_context,
    )


def _experience_reference_branch_id(
    *,
    host_context: ServiceApiHostContext,
    experience_name: str,
) -> UUID | None:
    normalized = (experience_name or "").strip()
    if not normalized:
        return None
    branch_ids = host_context.experience_reference_branch_ids_by_experience_name
    return branch_ids.get(normalized) or branch_ids.get(normalized.casefold())


async def _hydrate_section_graph_binding_session(
    *,
    runtime_context: _SectionGraphBindingRuntimeContext,
) -> Session:
    session = Session(branch_id=runtime_context.branch_id, skip_db=True)
    for projection_hash in runtime_context.projection_hashes:
        await _hydrate_projection_into_session(
            runtime_context=runtime_context,
            session=session,
            projection_hash=projection_hash,
        )
    return session


async def _hydrate_projection_into_session(
    *,
    runtime_context: _SectionGraphBindingRuntimeContext,
    session: Session,
    projection_hash: str,
) -> None:
    target_head = await FSCommitStore().head(
        branch_id=runtime_context.branch_id,
        projection_hash=projection_hash,
    )
    if target_head is None or not target_head.get("commit_id"):
        return
    opg = runtime_context.runtime_index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"Experience section-graph-binding service could not resolve projection hash {projection_hash!r}."
        )
    target_oig, _ = await CachedLaneMaterializer().get(
        branch_id=runtime_context.branch_id,
        ocg=runtime_context.runtime_index.ocg,
        opg=opg,
        commit_id=UUID(str(target_head["commit_id"])),
        oig_id=(
            UUID(str(target_head["object_instance_graph_id"]))
            if target_head.get("object_instance_graph_id")
            else None
        ),
        attribute_configs_by_id=runtime_context.runtime_index.attribute_configs_by_id,
        class_configs_by_id=runtime_context.runtime_index.class_configs_by_id,
    )
    hydrated_session = reify_oig_session(
        index=runtime_context.runtime_index,
        opg=opg,
        oig=target_oig,
        branch_id=runtime_context.branch_id,
    )
    for obj in hydrated_session.imap_all_objects():
        session.merge(obj)


def _require_projection_hash(*, runtime_index: MetaGraphRuntimeIndex, name: str) -> str:
    matches = [
        candidate
        for candidate in getattr(
            getattr(runtime_index, "ocg", None), "object_projection_graphs", []
        )
        or []
        if (getattr(candidate, "name", "") or "").strip() == name
    ]
    if not matches:
        raise ValueError(
            f"Experience projection `{name}` is missing from runtime index."
        )
    if len(matches) != 1:
        raise ValueError(
            f"Experience projection `{name}` is ambiguous in runtime index: expected 1, found {len(matches)}"
        )
    projection_hash = str(getattr(matches[0], "projection_hash", "") or "").strip()
    if not projection_hash:
        raise ValueError(
            f"Experience projection `{name}` could not resolve projection hash from runtime index."
        )
    return projection_hash


async def _read_attention_section_snapshot(
    *,
    host_context: ServiceApiHostContext,
    section_key: str,
) -> object:
    from aware_attention_service_api import AwareAttentionServiceApiClient
    from aware_attention_service_dto.attention.section.service_operation import (
        GetAttentionSectionStateRequest,
    )

    client = AwareAttentionServiceApiClient(
        _require_attention_service_api_invoker(host_context=host_context)
    )
    response = await client.attention.get_section_state.get_section_state(
        GetAttentionSectionStateRequest(
            section_key=section_key,
        )
    )
    snapshot = getattr(response, "snapshot", None)
    if snapshot is None:
        raise RuntimeError(
            "Attention service get_section_state did not return snapshot for "
            + f"section_key={section_key!r}"
        )
    return snapshot


async def _activate_attention_section_observable(
    *,
    host_context: ServiceApiHostContext,
    section_key: str,
    observable_id: UUID,
    activation_scope: ExperienceSectionGraphBindingActivationScope | None,
    rationale: str | None,
    section_title: str | None,
    section_description: str | None,
    focus_scope_title: str | None,
    focus_scope_description: str | None,
) -> object:
    from aware_attention_service_api import AwareAttentionServiceApiClient
    from aware_attention_service_dto.attention.section.service_operation import (
        ActivateAttentionSectionObservableRequest,
    )

    client = AwareAttentionServiceApiClient(
        _require_attention_service_api_invoker(host_context=host_context)
    )
    response = (
        await client.attention.activate_section_observable.activate_section_observable(
            ActivateAttentionSectionObservableRequest(
                section_key=section_key,
                observable_id=observable_id,
                activation_scope=_attention_activation_scope_from_experience_scope(
                    activation_scope
                ),
                rationale=rationale,
                section_title=section_title,
                section_description=section_description,
                focus_scope_title=focus_scope_title,
                focus_scope_description=focus_scope_description,
            )
        )
    )
    snapshot = getattr(response, "snapshot", None)
    if snapshot is None:
        raise RuntimeError(
            "Attention service activate_section_observable did not return snapshot for "
            + f"section_key={section_key!r}"
        )
    return snapshot


def _require_attention_service_api_invoker(
    *,
    host_context: ServiceApiHostContext,
) -> Any:
    client = build_service_api_client_for_api_package(
        host_context.service_api_dependency_routes,
        api_package_name=_ATTENTION_SERVICE_API_PACKAGE_NAME,
        actor_id=host_context.operation_context.actor_id,
        invocation_context=_host_invocation_context_payload(host_context),
    )
    if client is None:
        raise RuntimeError(
            "Experience section-graph-binding activation requires a Service API "
            "dependency route for attention-service-api."
        )
    return client


def _host_invocation_context_payload(
    host_context: ServiceApiHostContext,
) -> JsonObject | None:
    if host_context.invocation_context is None:
        return None
    return cast(JsonObject, dict(host_context.invocation_context))


def _require_activation_scope_matches_entry(
    *,
    activation_scope: ExperienceSectionGraphBindingActivationScope | None,
    entry: ExperienceSectionGraphBindingCatalogEntry,
) -> None:
    if activation_scope is None:
        return
    scoped_section_key = _normalize_optional_text(activation_scope.section_key)
    if scoped_section_key is None:
        return
    binding_section_key = entry.descriptor.section_key.strip()
    if scoped_section_key == binding_section_key:
        return
    raise ValueError(
        "Experience activation scope section_key does not match the selected "
        + "section graph binding: "
        + f"scope_section_key={scoped_section_key!r} "
        + f"binding_section_key={binding_section_key!r} "
        + f"binding_key={entry.descriptor.binding_key!r}"
    )


def _require_layout_activation_scope_is_not_section_specific(
    *,
    activation_scope: ExperienceSectionGraphBindingActivationScope | None,
) -> None:
    if activation_scope is None:
        return
    section_specific_fields = (
        "section_key",
        "layout_section_id",
        "section_focus_scope_id",
        "focus_scope_id",
        "observable_id",
        "focus_target",
    )
    populated = [
        field_name
        for field_name in section_specific_fields
        if getattr(activation_scope, field_name, None) is not None
    ]
    if populated:
        raise ValueError(
            "Experience layout graph binding activation must not include "
            + "section-specific activation scope fields: "
            + ", ".join(populated)
        )


def _require_transition_target_matches_entry(
    *,
    target_view_ref: str,
    target_section_key: str | None,
    target_graph_identity_ref: str | None,
    entry: ExperienceSectionGraphBindingCatalogEntry,
) -> None:
    descriptor = entry.descriptor
    if target_view_ref != descriptor.view_ref:
        raise ValueError(
            "Experience view event transition target_view_ref does not match "
            + "the selected section graph binding: "
            + f"target_view_ref={target_view_ref!r} "
            + f"binding_view_ref={descriptor.view_ref!r} "
            + f"binding_key={descriptor.binding_key!r}"
        )
    if target_section_key is not None and target_section_key != descriptor.section_key:
        raise ValueError(
            "Experience view event transition target_section_key does not match "
            + "the selected section graph binding: "
            + f"target_section_key={target_section_key!r} "
            + f"binding_section_key={descriptor.section_key!r} "
            + f"binding_key={descriptor.binding_key!r}"
        )
    if (
        target_graph_identity_ref is not None
        and target_graph_identity_ref != descriptor.graph_identity_ref
    ):
        raise ValueError(
            "Experience view event transition target_graph_identity_ref does not "
            + "match the selected section graph binding: "
            + f"target_graph_identity_ref={target_graph_identity_ref!r} "
            + f"binding_graph_identity_ref={descriptor.graph_identity_ref!r} "
            + f"binding_key={descriptor.binding_key!r}"
        )


def _require_transition_request_target_hints_match_resolution(
    *,
    request: ApplyExperienceViewEventTransitionRequest,
    resolved_transition: _ViewEventTransitionTargetResolution,
) -> None:
    target_view_ref = _normalize_optional_text(
        getattr(request, "target_view_ref", None)
    )
    if (
        target_view_ref is not None
        and target_view_ref != resolved_transition.target_view_ref
    ):
        raise ValueError(
            "Experience view event transition target_view_ref hint does not match "
            + "committed transition target: "
            + f"target_view_ref={target_view_ref!r} "
            + f"committed_target_view_ref={resolved_transition.target_view_ref!r} "
            + f"transition_key={resolved_transition.transition_key!r}"
        )
    target_binding_key = _normalize_optional_text(
        getattr(request, "target_binding_key", None)
    )
    if (
        target_binding_key is not None
        and target_binding_key != resolved_transition.target_binding_key
    ):
        raise ValueError(
            "Experience view event transition target_binding_key hint does not "
            + "match committed transition target: "
            + f"target_binding_key={target_binding_key!r} "
            + f"committed_target_binding_key={resolved_transition.target_binding_key!r} "
            + f"transition_key={resolved_transition.transition_key!r}"
        )
    target_section_key = _normalize_optional_text(
        getattr(request, "target_section_key", None)
    )
    if (
        target_section_key is not None
        and target_section_key != resolved_transition.target_section_key
    ):
        raise ValueError(
            "Experience view event transition target_section_key hint does not "
            + "match committed transition target: "
            + f"target_section_key={target_section_key!r} "
            + f"committed_target_section_key={resolved_transition.target_section_key!r} "
            + f"transition_key={resolved_transition.transition_key!r}"
        )
    target_graph_identity_ref = _normalize_optional_text(
        getattr(request, "target_graph_identity_ref", None)
    )
    if (
        target_graph_identity_ref is not None
        and target_graph_identity_ref != resolved_transition.target_graph_identity_ref
    ):
        raise ValueError(
            "Experience view event transition target_graph_identity_ref hint does "
            + "not match committed transition target: "
            + f"target_graph_identity_ref={target_graph_identity_ref!r} "
            + f"committed_target_graph_identity_ref={resolved_transition.target_graph_identity_ref!r} "
            + f"transition_key={resolved_transition.transition_key!r}"
        )


def _attention_activation_scope_from_experience_scope(
    activation_scope: ExperienceSectionGraphBindingActivationScope | None,
) -> Any:
    if activation_scope is None:
        return None
    from aware_attention_service_dto.attention.section.service_operation import (
        AttentionSectionActivationScope,
    )

    payload = activation_scope.model_dump(
        mode="json",
        include={
            "window_key",
            "layout_key",
            "layout_section_id",
            "section_focus_scope_id",
            "focus_scope_id",
            "branch_id",
            "state_projection_hash",
            "focus_target",
        },
        exclude_none=True,
    )
    if not payload:
        return None
    return AttentionSectionActivationScope.model_validate(payload)


def _experience_focus_target_from_attention_snapshot(
    *,
    entry: ExperienceSectionGraphBindingCatalogEntry,
    attention_snapshot: object,
) -> ExperienceSectionFocusTarget | None:
    focus_target = getattr(attention_snapshot, "focus_target", None)
    if focus_target is None:
        return None
    if hasattr(focus_target, "model_dump"):
        payload = focus_target.model_dump(mode="json", exclude_none=True)
    else:
        payload = dict(cast(dict[str, object], focus_target))
    payload["projection_experience_graph_identity_id"] = str(
        entry.graph_identity_object_id
    )
    return ExperienceSectionFocusTarget.model_validate(payload)


def _normalize_optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_required_text(value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} is required")
    return normalized


def _drop_none(values: dict[str, object | None]) -> dict[str, object]:
    return {key: value for key, value in values.items() if value is not None}


def _environment_invoke_context(
    *, host_context: ServiceApiHostContext
) -> dict[str, object]:
    environment_context = host_context.environment_context
    operation_context = host_context.operation_context
    environment_id = (
        getattr(environment_context, "environment_id", None)
        if environment_context is not None
        else getattr(operation_context, "environment_id", None)
    )
    if environment_id is None:
        raise ValueError(
            "Experience section-graph-binding service requires environment_id "
            "on ServiceApiHostContext.environment_context."
        )
    process_id = (
        getattr(environment_context, "process_id", None)
        if environment_context is not None
        else getattr(operation_context, "process_id", None)
    )
    thread_id = (
        getattr(environment_context, "thread_id", None)
        if environment_context is not None
        else getattr(operation_context, "thread_id", None)
    )
    return _drop_none(
        {
            "environment_id": environment_id,
            "process_id": process_id,
            "thread_id": thread_id,
        }
    )


def _snapshot_signature(snapshot: ExperienceSectionGraphBindingStateSnapshot) -> str:
    return json.dumps(
        snapshot.model_dump(mode="json", exclude_none=True),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


__all__ = [
    "EXPERIENCE_TRANSITION_SPEC_PROJECTION_NAMES",
    "apply_view_event_transition",
    "activate_layout_graph_binding",
    "activate_section_graph_binding",
    "get_layout_graph_binding_catalog",
    "get_layout_graph_binding_state",
    "get_section_graph_binding_catalog",
    "get_section_graph_binding_state",
    "hydrate_experience_reference_session",
    "invoke_experience_view_invocation_action",
    "record_experience_view_invocation_action",
    "stream_watch_section_graph_bindings",
    "watch_section_graph_bindings",
]
