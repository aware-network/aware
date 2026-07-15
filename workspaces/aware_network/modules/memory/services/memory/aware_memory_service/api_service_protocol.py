# pyright: reportMissingImports=false

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol, cast
from uuid import UUID

from aware_attention_service_api import AwareAttentionServiceApiClient
from aware_attention_service_dto.attention.session.service_operation import (
    ValidateAttentionTransitionRequest,
)
from aware_code.types import JsonArray, JsonObject
from aware_environment_service_dto.environment.environment import (
    EnvironmentOperationContext,
    InvokeFunctionCallTarget,
    InvokeFunctionRequest,
    InvokeFunctionResponse,
)
from aware_identity_service_api import AwareIdentityServiceApiClient
from aware_identity_service_dto.session.session import (
    ActorSessionsListRequest,
    SessionDescribeRequest,
    SessionMembersListRequest,
)
from aware_memory_ontology.stable_ids import (
    stable_memory_working_id,
    stable_memory_working_event_meaning_id,
    stable_memory_working_item_id,
)
from aware_memory_service_dto.memory.working.models import (
    AttentionTransitionValidationEvidence,
    MemoryActorContextEvidence,
    MemoryActorContextEvent,
    MemoryActorContextFrame,
    MemoryActorContextFrameEvent,
    MemoryActorContextFrameItem,
    MemoryActorContextSnapshot,
    MemoryEventActionProvenanceEvidence,
    MemoryResolvedEventMeaningEvidence,
    MemoryResolvedEventMeaningPin,
    MemoryWorkingCommitReceipt,
    MemoryWorkingFact,
    MemoryWorkingItemEvidence,
    MemoryWorkingItemPin,
    MemoryWorkingPin,
)
from aware_memory_service_dto.memory.working.service_operation import (
    DescribeMemoryWorkingRequest,
    DescribeMemoryWorkingResponse,
    EnsureMemoryWorkingRequest,
    EnsureMemoryWorkingResponse,
    ListMemoryWorkingItemsRequest,
    ListMemoryWorkingItemsResponse,
    RememberAttentionTransitionRequest,
    RememberAttentionTransitionResponse,
    RememberContentRequest,
    RememberContentResponse,
    RememberEventRequest,
    RememberEventResponse,
    RecordResolvedEventMeaningRequest,
    RecordResolvedEventMeaningResponse,
    ResolveActorMemoryContextRequest,
    ResolveActorMemoryContextFrameRequest,
    ResolveActorMemoryContextFrameResponse,
    ResolveActorMemoryContextResponse,
    ResolveMemoryContextRequest,
    ResolveMemoryContextResponse,
    ValidateMemoryWorkingItemRequest,
    ValidateMemoryWorkingItemResponse,
    WatchActorMemoryContextRequest,
    WatchActorMemoryContextFrameRequest,
    WatchActorMemoryContextFrameResponse,
    WatchActorMemoryContextResponse,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_service_runtime.api_ingress.host_context import (
    ServiceApiHostContext,
    current_service_api_host_context,
)
from aware_service_runtime.api_ingress.ontology_replica_orm_context import (
    current_service_ontology_replica_orm_session,
)
from aware_service_runtime.contracts import (
    ServiceGraphGateway,
    ServiceOperationContext,
)
from aware_service_runtime.local_service_host_api_client import (
    build_service_api_client_for_api_package,
)

_ATTENTION_SERVICE_API_PACKAGE_NAME = "attention-service-api"
_IDENTITY_SERVICE_API_PACKAGE_NAME = "identity-service-api"
_MEMORY_WORKING_PROJECTION_NAME = "MemoryWorking"
_MEMORY_WORKING_CLASS_FQN = "aware_memory_ontology.memory.memory_working.MemoryWorking"
_MEMORY_WORKING_EVENT_FRAME_CLASS_FQN = (
    "aware_memory_ontology.memory.memory_working_event_frame.MemoryWorkingEventFrame"
)
_EVENT_ACTION_PROVENANCE_FIELD_NAMES = (
    "event_config_id",
    "event_activation_id",
    "event_type",
    "event_source",
    "event_status",
    "commit_branch_id",
    "commit_projection_hash",
    "commit_id",
    "object_instance_graph_id",
    "object_instance_graph_commit_id",
    "actor_subscription_id",
    "action_intent_id",
    "intent_key",
    "action_config_id",
    "action_execution_id",
    "action_execution_key",
    "api_call_key",
    "action_binding_id",
    "action_experience_id",
    "environment_profile_id",
    "environment_event_id",
    "invocation_config_id",
    "endpoint_id",
)
_REQUIRED_EVENT_ACTION_PROVENANCE_FIELDS = (
    "commit_id",
    "actor_subscription_id",
    "action_intent_id",
    "intent_key",
    "action_config_id",
    "action_execution_id",
    "api_call_key",
    "action_binding_id",
    "action_experience_id",
    "environment_profile_id",
    "environment_event_id",
    "invocation_config_id",
    "endpoint_id",
)
_RESOLVED_EVENT_MEANING_RESOLVER_FIELD_NAMES = (
    "resolver_status",
    "resolver_endpoint_ref",
    "resolver_discriminant",
    "resolver_program_impl_instruction_intent_id",
    "resolver_action_config_id",
    "resolver_api_capability_endpoint_id",
    "resolver_api_call_id",
    "resolver_api_call_key",
    "resolver_request_model_id",
    "resolver_api_call_outcome_id",
    "resolver_response_model_id",
    "resolver_response_class_config_id",
    "resolver_service_operation_id",
    "resolver_service_operation_config_id",
    "resolver_service_operation_commit_id",
    "resolver_service_operation_head_commit_id",
    "resolver_service_operation_branch_id",
    "resolver_service_operation_projection_hash",
    "resolver_api_call_outcome_commit_id",
    "resolver_api_call_outcome_head_commit_id",
    "resolver_api_call_outcome_branch_id",
    "resolver_api_call_outcome_projection_hash",
)


class MemoryAttentionTransitionValidator(Protocol):
    async def validate_attention_transition(
        self,
        request: RememberAttentionTransitionRequest,
        *,
        host_context: ServiceApiHostContext,
        actor_id: UUID | None,
    ) -> AttentionTransitionValidationEvidence: ...


class MemoryActorContextValidator(Protocol):
    async def validate_actor_context(
        self,
        request: ResolveActorMemoryContextRequest,
        *,
        host_context: ServiceApiHostContext,
        actor_id: UUID | None,
    ) -> MemoryActorContextEvidence: ...


@dataclass(frozen=True, slots=True)
class _MemoryRuntimeContext:
    graph_gateway: ServiceGraphGateway
    runtime_index: MetaGraphRuntimeIndex
    memory_working_opg_id: UUID
    memory_working_projection_hash: str
    memory_working_class_config_id: UUID
    memory_working_build_function_id: UUID
    memory_working_add_attention_item_function_id: UUID
    memory_working_add_content_item_function_id: UUID
    memory_working_add_event_item_function_id: UUID
    memory_working_event_frame_record_resolved_meaning_function_id: UUID


@dataclass(frozen=True, slots=True)
class _MemoryReplicaModels:
    memory_working: type[Any]
    memory_working_item: type[Any]
    memory_working_content_frame: type[Any]
    memory_working_event_frame: type[Any]
    memory_working_event_meaning: type[Any]
    memory_working_tool_frame: type[Any]


@dataclass(frozen=True, slots=True)
class _MemoryWorkingChange:
    memory_working_id: UUID
    memory_working_item_id: UUID | None
    commit_id: UUID | None
    sequence: int
    fact_kind: str | None = None


@dataclass(frozen=True, slots=True)
class _MemoryActorContextStreamUpdate:
    snapshot: MemoryActorContextSnapshot
    change: _MemoryWorkingChange | None = None


class _MemoryWorkingCommitFanout:
    def __init__(self) -> None:
        self._condition = asyncio.Condition()
        self._sequence = 0
        self._latest_by_memory_working_id: dict[UUID, _MemoryWorkingChange] = {}

    def latest_sequence(self, memory_working_id: UUID) -> int:
        change = self._latest_by_memory_working_id.get(memory_working_id)
        return 0 if change is None else change.sequence

    async def publish(
        self,
        *,
        memory_working_id: UUID,
        memory_working_item_id: UUID | None,
        commit_id: UUID | None,
        fact_kind: str | None = None,
    ) -> None:
        async with self._condition:
            self._sequence += 1
            self._latest_by_memory_working_id[memory_working_id] = _MemoryWorkingChange(
                memory_working_id=memory_working_id,
                memory_working_item_id=memory_working_item_id,
                commit_id=commit_id,
                sequence=self._sequence,
                fact_kind=fact_kind,
            )
            self._condition.notify_all()

    async def wait_for_change(
        self,
        *,
        memory_working_id: UUID,
        after_sequence: int,
    ) -> _MemoryWorkingChange:
        def _has_change() -> bool:
            change = self._latest_by_memory_working_id.get(memory_working_id)
            return change is not None and change.sequence > after_sequence

        async with self._condition:
            await self._condition.wait_for(_has_change)
            return self._latest_by_memory_working_id[memory_working_id]


def build_aware_memory_service_protocol_handler(
    *,
    attention_validator: MemoryAttentionTransitionValidator | None = None,
    actor_context_validator: MemoryActorContextValidator | None = None,
) -> object:
    return _AwareMemoryServiceProtocolHandler(
        attention_validator=attention_validator,
        actor_context_validator=actor_context_validator,
    )


class _MemoryProtocolSupport:
    def host_context(self) -> ServiceApiHostContext:
        host_context = current_service_api_host_context()
        if host_context is None:
            raise RuntimeError(
                "Memory service protocol requires an active Service API host context."
            )
        return host_context

    def operation_context(self) -> ServiceOperationContext:
        return self.host_context().operation_context

    async def runtime_context(self) -> _MemoryRuntimeContext:
        host_context = self.host_context()
        if host_context.graph_gateway is None:
            raise RuntimeError(
                "Memory service protocol requires a Service graph gateway."
            )
        graph_gateway = host_context.graph_gateway
        runtime_index = self._coerce_runtime_index(
            await self._resolve_graph_context(
                host_context=host_context,
                graph_gateway=graph_gateway,
            )
        )
        return _resolve_memory_runtime_context(
            runtime_index=runtime_index,
            graph_gateway=graph_gateway,
        )

    async def _resolve_graph_context(
        self,
        *,
        host_context: ServiceApiHostContext,
        graph_gateway: object,
    ) -> object:
        if host_context.materialization is not None:
            return host_context.materialization.graph_context
        if host_context.graph_context_provider is not None:
            return await host_context.graph_context_provider.resolve_graph_context()
        resolve_graph_context = getattr(graph_gateway, "resolve_graph_context", None)
        if callable(resolve_graph_context):
            return await resolve_graph_context()
        raise RuntimeError("Memory service protocol requires a Service graph context.")

    @staticmethod
    def _coerce_runtime_index(graph_context: object) -> MetaGraphRuntimeIndex:
        return cast(
            MetaGraphRuntimeIndex,
            getattr(graph_context, "index", graph_context),
        )


class _MemoryEnsureWorkingCapabilityHandler:
    def __init__(self, *, support: _MemoryProtocolSupport) -> None:
        self._support = support

    async def ensure_memory_working(
        self,
        request: EnsureMemoryWorkingRequest,
    ) -> EnsureMemoryWorkingResponse:
        operation_context = self._support.operation_context()
        actor_id = _resolve_actor_id(request.actor_id, operation_context)
        key = _normalize_key(request.key)
        memory_working_id = stable_memory_working_id(actor_id=actor_id, key=key)
        existing = await _load_memory_working_by_id(memory_working_id)
        if existing is not None:
            return EnsureMemoryWorkingResponse(
                request_id=request.request_id,
                memory_working=await _memory_working_pin(existing),
                receipt=None,
            )

        runtime_context = await self._support.runtime_context()
        response = await _invoke_constructor(
            runtime_context=runtime_context,
            operation_context=operation_context,
            branch_id=memory_working_id,
            projection_hash=runtime_context.memory_working_projection_hash,
            object_projection_graph_id=runtime_context.memory_working_opg_id,
            function_id=runtime_context.memory_working_build_function_id,
            kwargs={"actor_id": actor_id, "key": key},
        )
        pin = MemoryWorkingPin(
            memory_working_id=memory_working_id,
            actor_id=actor_id,
            key=key,
            item_count=0,
        )
        return EnsureMemoryWorkingResponse(
            request_id=request.request_id,
            memory_working=pin,
            receipt=_memory_working_receipt(
                response=response,
                memory_working_id=memory_working_id,
                memory_working_item_id=None,
            ),
        )


class _MemoryDescribeWorkingCapabilityHandler:
    async def describe_memory_working(
        self,
        request: DescribeMemoryWorkingRequest,
    ) -> DescribeMemoryWorkingResponse:
        memory_working = await _load_memory_working_for_request(
            memory_working_id=request.memory_working_id,
            actor_id=request.actor_id,
            key=request.key,
        )
        if memory_working is None:
            return DescribeMemoryWorkingResponse(
                request_id=request.request_id,
                exists=False,
                memory_working=None,
            )
        return DescribeMemoryWorkingResponse(
            request_id=request.request_id,
            exists=True,
            memory_working=await _memory_working_pin(memory_working),
        )


class _MemoryListWorkingItemsCapabilityHandler:
    async def list_memory_working_items(
        self,
        request: ListMemoryWorkingItemsRequest,
    ) -> ListMemoryWorkingItemsResponse:
        memory_working = await _load_memory_working_for_request(
            memory_working_id=request.memory_working_id,
            actor_id=request.actor_id,
            key=request.key,
        )
        if memory_working is None:
            return ListMemoryWorkingItemsResponse(
                request_id=request.request_id,
                memory_working=None,
                items=[],
            )
        items = await _memory_working_items_for_id(
            _row_id(memory_working),
            kind=request.kind,
            limit=request.limit,
        )
        return ListMemoryWorkingItemsResponse(
            request_id=request.request_id,
            memory_working=await _memory_working_pin(memory_working, items=items),
            items=[await _memory_working_item_pin(item) for item in items],
        )


class _MemoryValidateWorkingItemCapabilityHandler:
    def __init__(
        self,
        *,
        support: _MemoryProtocolSupport,
        attention_validator: MemoryAttentionTransitionValidator,
    ) -> None:
        self._support = support
        self._attention_validator = attention_validator

    async def validate_memory_working_item(
        self,
        request: ValidateMemoryWorkingItemRequest,
    ) -> ValidateMemoryWorkingItemResponse:
        item = await _load_memory_working_item_by_id(request.memory_working_item_id)
        if item is None:
            return ValidateMemoryWorkingItemResponse(
                request_id=request.request_id,
                success=False,
                error="memory_working_item_missing",
                evidence=None,
            )
        evidence = await _memory_working_item_evidence(
            item=await _memory_working_item_pin(item),
            request=request,
            support=self._support,
            attention_validator=self._attention_validator,
        )
        return ValidateMemoryWorkingItemResponse(
            request_id=request.request_id,
            evidence=evidence,
        )


class _MemoryResolveContextCapabilityHandler:
    def __init__(
        self,
        *,
        support: _MemoryProtocolSupport,
        attention_validator: MemoryAttentionTransitionValidator,
    ) -> None:
        self._support = support
        self._attention_validator = attention_validator

    async def resolve_memory_context(
        self,
        request: ResolveMemoryContextRequest,
    ) -> ResolveMemoryContextResponse:
        return await _resolve_memory_context_response(
            request=request,
            support=self._support,
            attention_validator=self._attention_validator,
        )


class _MemoryResolveActorContextCapabilityHandler:
    def __init__(
        self,
        *,
        support: _MemoryProtocolSupport,
        attention_validator: MemoryAttentionTransitionValidator,
        actor_context_validator: MemoryActorContextValidator,
    ) -> None:
        self._support = support
        self._attention_validator = attention_validator
        self._actor_context_validator = actor_context_validator

    async def resolve_actor_memory_context(
        self,
        request: ResolveActorMemoryContextRequest,
    ) -> ResolveActorMemoryContextResponse:
        return await _resolve_actor_memory_context_response(
            request=request,
            support=self._support,
            attention_validator=self._attention_validator,
            actor_context_validator=self._actor_context_validator,
        )


class _MemoryWatchActorContextCapabilityHandler:
    def __init__(
        self,
        *,
        support: _MemoryProtocolSupport,
        commit_fanout: _MemoryWorkingCommitFanout,
        attention_validator: MemoryAttentionTransitionValidator,
        actor_context_validator: MemoryActorContextValidator,
    ) -> None:
        self._support = support
        self._commit_fanout = commit_fanout
        self._attention_validator = attention_validator
        self._actor_context_validator = actor_context_validator

    async def watch_actor_memory_context(
        self,
        request: WatchActorMemoryContextRequest,
    ) -> WatchActorMemoryContextResponse:
        snapshot, changed = await _build_actor_memory_context_snapshot(
            request=request,
            support=self._support,
            attention_validator=self._attention_validator,
            actor_context_validator=self._actor_context_validator,
            known_cursor=request.known_cursor,
            known_digest=request.known_digest,
            sequence=0,
        )
        return WatchActorMemoryContextResponse(
            request_id=request.request_id,
            success=snapshot.actor_context.usable,
            error=None if snapshot.actor_context.usable else "actor_context_unusable",
            snapshot=snapshot,
            changed=changed,
        )

    async def stream_watch_actor_memory_context(
        self,
        request: WatchActorMemoryContextRequest,
    ):
        async for update in _stream_actor_memory_context_snapshots(
            request=request,
            support=self._support,
            commit_fanout=self._commit_fanout,
            attention_validator=self._attention_validator,
            actor_context_validator=self._actor_context_validator,
        ):
            yield MemoryActorContextEvent(snapshot=update.snapshot)


class _MemoryResolveActorContextFrameCapabilityHandler:
    def __init__(
        self,
        *,
        support: _MemoryProtocolSupport,
        attention_validator: MemoryAttentionTransitionValidator,
        actor_context_validator: MemoryActorContextValidator,
    ) -> None:
        self._support = support
        self._attention_validator = attention_validator
        self._actor_context_validator = actor_context_validator

    async def resolve_actor_memory_context_frame(
        self,
        request: ResolveActorMemoryContextFrameRequest,
    ) -> ResolveActorMemoryContextFrameResponse:
        snapshot, changed = await _build_actor_memory_context_snapshot(
            request=_watch_actor_memory_context_request_from_frame_request(request),
            support=self._support,
            attention_validator=self._attention_validator,
            actor_context_validator=self._actor_context_validator,
            known_cursor=None,
            known_digest=None,
            sequence=0,
        )
        return ResolveActorMemoryContextFrameResponse(
            request_id=request.request_id,
            success=snapshot.actor_context.usable,
            error=None if snapshot.actor_context.usable else "actor_context_unusable",
            frame=_memory_actor_context_frame_from_snapshot(snapshot),
            changed=changed,
        )


class _MemoryWatchActorContextFrameCapabilityHandler:
    def __init__(
        self,
        *,
        support: _MemoryProtocolSupport,
        commit_fanout: _MemoryWorkingCommitFanout,
        attention_validator: MemoryAttentionTransitionValidator,
        actor_context_validator: MemoryActorContextValidator,
    ) -> None:
        self._support = support
        self._commit_fanout = commit_fanout
        self._attention_validator = attention_validator
        self._actor_context_validator = actor_context_validator

    async def watch_actor_memory_context_frame(
        self,
        request: WatchActorMemoryContextFrameRequest,
    ) -> WatchActorMemoryContextFrameResponse:
        snapshot, changed = await _build_actor_memory_context_snapshot(
            request=_watch_actor_memory_context_request_from_frame_request(request),
            support=self._support,
            attention_validator=self._attention_validator,
            actor_context_validator=self._actor_context_validator,
            known_cursor=request.known_cursor,
            known_digest=request.known_digest,
            sequence=0,
        )
        return WatchActorMemoryContextFrameResponse(
            request_id=request.request_id,
            success=snapshot.actor_context.usable,
            error=None if snapshot.actor_context.usable else "actor_context_unusable",
            frame=_memory_actor_context_frame_from_snapshot(snapshot),
            changed=changed,
        )

    async def stream_watch_actor_memory_context_frame(
        self,
        request: WatchActorMemoryContextFrameRequest,
    ):
        watch_request = _watch_actor_memory_context_request_from_frame_request(request)
        async for update in _stream_actor_memory_context_snapshots(
            request=watch_request,
            support=self._support,
            commit_fanout=self._commit_fanout,
            attention_validator=self._attention_validator,
            actor_context_validator=self._actor_context_validator,
        ):
            yield MemoryActorContextFrameEvent(
                frame=_memory_actor_context_frame_from_snapshot(update.snapshot),
                fact=_memory_working_fact_from_stream_update(update),
            )


class _MemoryRememberAttentionTransitionCapabilityHandler:
    def __init__(
        self,
        *,
        support: _MemoryProtocolSupport,
        commit_fanout: _MemoryWorkingCommitFanout,
        attention_validator: MemoryAttentionTransitionValidator,
    ) -> None:
        self._support = support
        self._commit_fanout = commit_fanout
        self._attention_validator = attention_validator

    async def remember_attention_transition(
        self,
        request: RememberAttentionTransitionRequest,
    ) -> RememberAttentionTransitionResponse:
        host_context = self._support.host_context()
        operation_context = host_context.operation_context
        validation = await self._attention_validator.validate_attention_transition(
            request,
            host_context=host_context,
            actor_id=operation_context.actor_id,
        )
        if not validation.valid:
            memory_working_id, actor_id, key = await _resolve_target_memory_working(
                request.memory_working_id,
                request.actor_id,
                request.key,
                operation_context,
            )
            return RememberAttentionTransitionResponse(
                request_id=request.request_id,
                success=False,
                error="attention_transition_validation_failed",
                memory_working=await _memory_working_pin_or_stub(
                    memory_working_id=memory_working_id,
                    actor_id=actor_id,
                    key=key,
                ),
                item=None,
                attention_validation=validation,
                receipt=None,
            )

        memory_working, receipt = await _ensure_memory_working_for_write(
            support=self._support,
            memory_working_id=request.memory_working_id,
            actor_id=request.actor_id,
            key=request.key,
        )
        next_position = await _next_item_position(_row_id(memory_working))
        item_id = stable_memory_working_item_id(
            memory_working_id=_row_id(memory_working),
            kind="attention",
            position=next_position,
        )
        runtime_context = await self._support.runtime_context()
        write_response = await _invoke_instance(
            runtime_context=runtime_context,
            operation_context=operation_context,
            branch_id=_row_id(memory_working),
            projection_hash=runtime_context.memory_working_projection_hash,
            object_id=_row_id(memory_working),
            function_id=(runtime_context.memory_working_add_attention_item_function_id),
            kwargs={
                "attention_focus_transition_id": request.attention_focus_transition_id,
                "rationale": request.rationale,
                "summary": request.summary,
            },
        )
        item = await _load_memory_working_item_by_id(item_id)
        commit_receipt = _memory_working_receipt(
            response=write_response,
            memory_working_id=_row_id(memory_working),
            memory_working_item_id=item_id,
            prior_receipt=receipt,
        )
        await self._commit_fanout.publish(
            memory_working_id=_row_id(memory_working),
            memory_working_item_id=item_id,
            commit_id=commit_receipt.commit_id,
        )
        return RememberAttentionTransitionResponse(
            request_id=request.request_id,
            memory_working=await _memory_working_pin(memory_working),
            item=(
                await _memory_working_item_pin(item)
                if item is not None
                else _memory_working_item_stub(
                    memory_working_id=_row_id(memory_working),
                    memory_working_item_id=item_id,
                    kind="attention",
                    position=next_position,
                    attention_focus_transition_id=(
                        request.attention_focus_transition_id
                    ),
                    rationale=request.rationale,
                    summary=request.summary,
                )
            ),
            attention_validation=validation,
            receipt=commit_receipt,
        )


class _MemoryRememberContentCapabilityHandler:
    def __init__(
        self,
        *,
        support: _MemoryProtocolSupport,
        commit_fanout: _MemoryWorkingCommitFanout,
    ) -> None:
        self._support = support
        self._commit_fanout = commit_fanout

    async def remember_content(
        self,
        request: RememberContentRequest,
    ) -> RememberContentResponse:
        memory_working, ensure_receipt = await _ensure_memory_working_for_write(
            support=self._support,
            memory_working_id=request.memory_working_id,
            actor_id=request.actor_id,
            key=request.key,
        )
        operation_context = self._support.operation_context()
        next_position = await _next_item_position(_row_id(memory_working))
        item_id = stable_memory_working_item_id(
            memory_working_id=_row_id(memory_working),
            kind="content",
            position=next_position,
        )
        runtime_context = await self._support.runtime_context()
        response = await _invoke_instance(
            runtime_context=runtime_context,
            operation_context=operation_context,
            branch_id=_row_id(memory_working),
            projection_hash=runtime_context.memory_working_projection_hash,
            object_id=_row_id(memory_working),
            function_id=runtime_context.memory_working_add_content_item_function_id,
            kwargs={
                "content_id": request.content_id,
                "rationale": request.rationale,
                "summary": request.summary,
            },
        )
        item = await _load_memory_working_item_by_id(item_id)
        commit_receipt = _memory_working_receipt(
            response=response,
            memory_working_id=_row_id(memory_working),
            memory_working_item_id=item_id,
            prior_receipt=ensure_receipt,
        )
        await self._commit_fanout.publish(
            memory_working_id=_row_id(memory_working),
            memory_working_item_id=item_id,
            commit_id=commit_receipt.commit_id,
        )
        return RememberContentResponse(
            request_id=request.request_id,
            memory_working=await _memory_working_pin(memory_working),
            item=(
                await _memory_working_item_pin(item)
                if item is not None
                else _memory_working_item_stub(
                    memory_working_id=_row_id(memory_working),
                    memory_working_item_id=item_id,
                    kind="content",
                    position=next_position,
                    content_id=request.content_id,
                    rationale=request.rationale,
                    summary=request.summary,
                )
            ),
            receipt=commit_receipt,
        )


class _MemoryRememberEventCapabilityHandler:
    def __init__(
        self,
        *,
        support: _MemoryProtocolSupport,
        commit_fanout: _MemoryWorkingCommitFanout,
    ) -> None:
        self._support = support
        self._commit_fanout = commit_fanout

    async def remember_event(
        self,
        request: RememberEventRequest,
    ) -> RememberEventResponse:
        operation_context = self._support.operation_context()
        event_action_provenance = _event_action_provenance_evidence_from_request(
            request,
            operation_context=operation_context,
        )
        if (
            event_action_provenance.validation_status != "source_unverified"
            and not event_action_provenance.usable
        ):
            memory_working = await _memory_working_pin_for_failed_write(
                memory_working_id=request.memory_working_id,
                actor_id=request.actor_id,
                key=request.key,
                operation_context=operation_context,
            )
            return RememberEventResponse(
                request_id=request.request_id,
                success=False,
                error=event_action_provenance.validation_status,
                memory_working=memory_working,
                memory_working_item_id=None,
                item=None,
                event_action_provenance=event_action_provenance,
                receipt=None,
            )

        memory_working, ensure_receipt = await _ensure_memory_working_for_write(
            support=self._support,
            memory_working_id=request.memory_working_id,
            actor_id=request.actor_id,
            key=request.key,
        )
        next_position = await _next_item_position(_row_id(memory_working))
        item_id = stable_memory_working_item_id(
            memory_working_id=_row_id(memory_working),
            kind="event",
            position=next_position,
        )
        runtime_context = await self._support.runtime_context()
        response = await _invoke_instance(
            runtime_context=runtime_context,
            operation_context=operation_context,
            branch_id=_row_id(memory_working),
            projection_hash=runtime_context.memory_working_projection_hash,
            object_id=_row_id(memory_working),
            function_id=runtime_context.memory_working_add_event_item_function_id,
            kwargs={
                "event_id": request.event_id,
                **_event_action_provenance_kwargs_from_request(request),
                "rationale": request.rationale,
                "summary": request.summary,
            },
        )
        item = await _load_memory_working_item_by_id(item_id)
        commit_receipt = _memory_working_receipt(
            response=response,
            memory_working_id=_row_id(memory_working),
            memory_working_item_id=item_id,
            prior_receipt=ensure_receipt,
        )
        await self._commit_fanout.publish(
            memory_working_id=_row_id(memory_working),
            memory_working_item_id=item_id,
            commit_id=commit_receipt.commit_id,
            fact_kind="event_remembered",
        )
        item_pin = (
            await _memory_working_item_pin(item)
            if item is not None
            else _memory_working_item_stub(
                memory_working_id=_row_id(memory_working),
                memory_working_item_id=item_id,
                kind="event",
                position=next_position,
                event_id=request.event_id,
                **_event_action_provenance_kwargs_from_request(request),
                rationale=request.rationale,
                summary=request.summary,
            )
        )
        if item_pin.memory_working_item_id != item_id:
            raise RuntimeError("memory_remember_event_item_identity_mismatch")
        return RememberEventResponse(
            request_id=request.request_id,
            memory_working=await _memory_working_pin(memory_working),
            memory_working_item_id=item_id,
            item=item_pin,
            event_action_provenance=event_action_provenance,
            receipt=commit_receipt,
        )


class _MemoryRecordResolvedEventMeaningCapabilityHandler:
    def __init__(
        self,
        *,
        support: _MemoryProtocolSupport,
        commit_fanout: _MemoryWorkingCommitFanout,
    ) -> None:
        self._support = support
        self._commit_fanout = commit_fanout

    async def record_resolved_event_meaning(
        self,
        request: RecordResolvedEventMeaningRequest,
    ) -> RecordResolvedEventMeaningResponse:
        operation_context = self._support.operation_context()
        item = await _load_memory_working_item_by_id(request.memory_working_item_id)
        if item is None:
            return _resolved_event_meaning_failure_response(
                request=request,
                status="memory_working_item_missing",
            )

        item_pin = await _memory_working_item_pin(item)
        memory_working = await _load_memory_working_by_id(item_pin.memory_working_id)
        if memory_working is None:
            return _resolved_event_meaning_failure_response(
                request=request,
                status="memory_working_missing",
                item=item_pin,
            )

        memory_working_pin = await _memory_working_pin(memory_working)
        actor_id = operation_context.actor_id or request.actor_id
        if (
            actor_id is None
            or memory_working_pin.actor_id != actor_id
            or (
                request.actor_id is not None
                and operation_context.actor_id is not None
                and request.actor_id != operation_context.actor_id
            )
        ):
            return _resolved_event_meaning_failure_response(
                request=request,
                status="actor_id_mismatch",
                memory_working=memory_working_pin,
                item=item_pin,
            )
        if item_pin.kind != "event" or item_pin.event_frame_id is None:
            return _resolved_event_meaning_failure_response(
                request=request,
                status="memory_working_item_not_event",
                memory_working=memory_working_pin,
                item=item_pin,
            )
        if item_pin.event_id != request.resolved_meaning.event_id:
            return _resolved_event_meaning_failure_response(
                request=request,
                status="event_id_mismatch",
                memory_working=memory_working_pin,
                item=item_pin,
            )

        source_provenance = _event_action_provenance_evidence_from_item(
            item_pin,
            actor_id=actor_id,
        )
        if not source_provenance.usable:
            return _resolved_event_meaning_failure_response(
                request=request,
                status="remembered_event_source_unverified",
                memory_working=memory_working_pin,
                item=item_pin,
                reasons=list(source_provenance.failure_reasons),
            )

        validation_error = _resolved_event_meaning_request_error(request)
        if validation_error is not None:
            return _resolved_event_meaning_failure_response(
                request=request,
                status=validation_error,
                memory_working=memory_working_pin,
                item=item_pin,
            )

        existing = item_pin.resolved_event_meaning
        if existing is not None:
            if _resolved_event_meaning_matches_request(existing, request):
                return RecordResolvedEventMeaningResponse(
                    request_id=request.request_id,
                    memory_working=memory_working_pin,
                    item=item_pin,
                    resolved_event_meaning=_resolved_event_meaning_evidence(existing),
                    receipt=None,
                )
            return _resolved_event_meaning_failure_response(
                request=request,
                status="resolved_event_meaning_conflict",
                memory_working=memory_working_pin,
                item=item_pin,
                meaning=existing,
            )

        runtime_context = await self._support.runtime_context()
        response = await _invoke_instance(
            runtime_context=runtime_context,
            operation_context=operation_context,
            branch_id=item_pin.memory_working_id,
            projection_hash=runtime_context.memory_working_projection_hash,
            object_id=item_pin.event_frame_id,
            function_id=(
                runtime_context.memory_working_event_frame_record_resolved_meaning_function_id
            ),
            kwargs=_resolved_event_meaning_invocation_kwargs(request),
        )
        meaning = _resolved_event_meaning_pin_from_request(
            request=request,
            memory_working_event_frame_id=item_pin.event_frame_id,
            resolved_at=datetime.now(timezone.utc),
        )
        item_pin = item_pin.model_copy(update={"resolved_event_meaning": meaning})
        receipt = _memory_working_receipt(
            response=response,
            memory_working_id=item_pin.memory_working_id,
            memory_working_item_id=item_pin.memory_working_item_id,
        )
        await self._commit_fanout.publish(
            memory_working_id=item_pin.memory_working_id,
            memory_working_item_id=item_pin.memory_working_item_id,
            commit_id=receipt.commit_id,
            fact_kind="event_meaning_resolved",
        )
        return RecordResolvedEventMeaningResponse(
            request_id=request.request_id,
            memory_working=memory_working_pin,
            item=item_pin,
            resolved_event_meaning=_resolved_event_meaning_evidence(meaning),
            receipt=receipt,
        )


class _MemoryApiServiceProtocolHandler:
    def __init__(
        self,
        *,
        attention_validator: MemoryAttentionTransitionValidator,
        actor_context_validator: MemoryActorContextValidator,
    ) -> None:
        support = _MemoryProtocolSupport()
        commit_fanout = _MemoryWorkingCommitFanout()
        self.ensure_memory_working = _MemoryEnsureWorkingCapabilityHandler(
            support=support,
        )
        self.describe_memory_working = _MemoryDescribeWorkingCapabilityHandler()
        self.list_memory_working_items = _MemoryListWorkingItemsCapabilityHandler()
        self.validate_memory_working_item = _MemoryValidateWorkingItemCapabilityHandler(
            support=support,
            attention_validator=attention_validator,
        )
        self.resolve_memory_context = _MemoryResolveContextCapabilityHandler(
            support=support,
            attention_validator=attention_validator,
        )
        self.resolve_actor_memory_context = _MemoryResolveActorContextCapabilityHandler(
            support=support,
            attention_validator=attention_validator,
            actor_context_validator=actor_context_validator,
        )
        self.watch_actor_memory_context = _MemoryWatchActorContextCapabilityHandler(
            support=support,
            commit_fanout=commit_fanout,
            attention_validator=attention_validator,
            actor_context_validator=actor_context_validator,
        )
        self.resolve_actor_memory_context_frame = (
            _MemoryResolveActorContextFrameCapabilityHandler(
                support=support,
                attention_validator=attention_validator,
                actor_context_validator=actor_context_validator,
            )
        )
        self.watch_actor_memory_context_frame = (
            _MemoryWatchActorContextFrameCapabilityHandler(
                support=support,
                commit_fanout=commit_fanout,
                attention_validator=attention_validator,
                actor_context_validator=actor_context_validator,
            )
        )
        self.remember_attention_transition = (
            _MemoryRememberAttentionTransitionCapabilityHandler(
                support=support,
                commit_fanout=commit_fanout,
                attention_validator=attention_validator,
            )
        )
        self.remember_content = _MemoryRememberContentCapabilityHandler(
            support=support,
            commit_fanout=commit_fanout,
        )
        self.remember_event = _MemoryRememberEventCapabilityHandler(
            support=support,
            commit_fanout=commit_fanout,
        )
        self.record_resolved_event_meaning = (
            _MemoryRecordResolvedEventMeaningCapabilityHandler(
                support=support,
                commit_fanout=commit_fanout,
            )
        )


class _AwareMemoryServiceProtocolHandler:
    def __init__(
        self,
        *,
        attention_validator: MemoryAttentionTransitionValidator | None = None,
        actor_context_validator: MemoryActorContextValidator | None = None,
    ) -> None:
        self.memory = _MemoryApiServiceProtocolHandler(
            attention_validator=(
                attention_validator or _ServiceRouteAttentionTransitionValidator()
            ),
            actor_context_validator=(
                actor_context_validator or _ServiceRouteActorContextValidator()
            ),
        )


class _ServiceRouteAttentionTransitionValidator:
    async def validate_attention_transition(
        self,
        request: RememberAttentionTransitionRequest,
        *,
        host_context: ServiceApiHostContext,
        actor_id: UUID | None,
    ) -> AttentionTransitionValidationEvidence:
        invoker = build_service_api_client_for_api_package(
            host_context.service_api_dependency_routes,
            api_package_name=_ATTENTION_SERVICE_API_PACKAGE_NAME,
            actor_id=actor_id,
            invocation_context=_host_invocation_context_payload(host_context),
        )
        if invoker is None:
            return AttentionTransitionValidationEvidence(
                exists=False,
                valid=False,
                failure_reasons=["attention_service_route_missing"],
                attention_focus_transition_id=request.attention_focus_transition_id,
            )
        client = AwareAttentionServiceApiClient(invoker)
        try:
            response = await client.attention.validate_attention_transition.validate_attention_transition(
                ValidateAttentionTransitionRequest(
                    request_id=request.request_id,
                    attention_focus_transition_id=request.attention_focus_transition_id,
                    expected_identity_session_id=request.expected_identity_session_id,
                    expected_attention_session_id=request.expected_attention_session_id,
                    expected_attention_session_section_id=(
                        request.expected_attention_session_section_id
                    ),
                    expected_focus_scope_id=request.expected_focus_scope_id,
                    expected_object_instance_graph_commit_id=(
                        request.expected_object_instance_graph_commit_id
                    ),
                    expected_projection_hash=request.expected_projection_hash,
                )
            )
        except Exception as exc:  # pragma: no cover - defensive fail-closed path
            return AttentionTransitionValidationEvidence(
                exists=False,
                valid=False,
                failure_reasons=[
                    f"attention_validation_error:{type(exc).__name__}",
                ],
                attention_focus_transition_id=request.attention_focus_transition_id,
            )
        return _attention_validation_evidence(response.validation)


class _ServiceRouteActorContextValidator:
    async def validate_actor_context(
        self,
        request: ResolveActorMemoryContextRequest,
        *,
        host_context: ServiceApiHostContext,
        actor_id: UUID | None,
    ) -> MemoryActorContextEvidence:
        resolved_actor_id = request.actor_id or actor_id
        if resolved_actor_id is None:
            return _actor_context_failure(
                request=request,
                actor_id=None,
                status="actor_id_missing",
                reasons=["actor_id_missing"],
            )
        if not request.validate_identity:
            return _actor_context_failure(
                request=request,
                actor_id=resolved_actor_id,
                status="not_validated",
                reasons=["identity_validation_not_requested"],
            )

        invoker = build_service_api_client_for_api_package(
            host_context.service_api_dependency_routes,
            api_package_name=_IDENTITY_SERVICE_API_PACKAGE_NAME,
            actor_id=resolved_actor_id,
            invocation_context=_host_invocation_context_payload(host_context),
        )
        if invoker is None:
            return _actor_context_failure(
                request=request,
                actor_id=resolved_actor_id,
                status="identity_service_route_missing",
                reasons=["identity_service_route_missing"],
            )

        client = AwareIdentityServiceApiClient(invoker)
        try:
            session = await _resolve_identity_session_for_actor_context(
                client=client,
                request=request,
                actor_id=resolved_actor_id,
            )
            if session is None:
                return _actor_context_failure(
                    request=request,
                    actor_id=resolved_actor_id,
                    status="identity_session_missing",
                    reasons=["identity_session_missing"],
                )
            session_id = cast(UUID, getattr(session, "session_id"))
            session_status = cast(str | None, getattr(session, "status", None))
            if not _status_is_active(session_status):
                return _actor_context_failure(
                    request=request,
                    actor_id=resolved_actor_id,
                    identity_session_id=session_id,
                    identity_session_exists=True,
                    identity_session_status=session_status,
                    status="identity_session_inactive",
                    reasons=["identity_session_inactive"],
                )
            parent_session_id = cast(
                UUID | None,
                getattr(session, "parent_session_id", None),
            )
            if (
                request.parent_identity_session_id is not None
                and parent_session_id != request.parent_identity_session_id
            ):
                return _actor_context_failure(
                    request=request,
                    actor_id=resolved_actor_id,
                    identity_session_id=session_id,
                    parent_identity_session_id=parent_session_id,
                    identity_session_exists=True,
                    identity_session_status=session_status,
                    status="identity_session_parent_mismatch",
                    reasons=["identity_session_parent_mismatch"],
                )
            members = (
                await client.identity.list_session_members.list_session_members(
                    SessionMembersListRequest(
                        request_id=request.request_id,
                        session_id=session_id,
                        status="active",
                        include_inactive=False,
                    )
                )
            ).members
        except _ActorContextResolutionError as exc:
            return _actor_context_failure(
                request=request,
                actor_id=resolved_actor_id,
                identity_session_id=exc.identity_session_id,
                actor_sessions_considered=exc.actor_sessions_considered,
                status=exc.status,
                reasons=[exc.status],
            )
        except Exception as exc:  # pragma: no cover - defensive fail-closed path
            return _actor_context_failure(
                request=request,
                actor_id=resolved_actor_id,
                status="identity_validation_error",
                reasons=[f"identity_validation_error:{type(exc).__name__}"],
            )

        actor_members = [
            member
            for member in members
            if getattr(member, "actor_id", None) == resolved_actor_id
            and _status_is_active(getattr(member, "status", None))
        ]
        if not actor_members:
            return _actor_context_failure(
                request=request,
                actor_id=resolved_actor_id,
                identity_session_id=session_id,
                parent_identity_session_id=parent_session_id,
                identity_session_exists=True,
                identity_session_status=session_status,
                status="actor_session_member_missing",
                reasons=["actor_session_member_missing"],
            )
        member = _sort_identity_rows(actor_members, id_attr="session_member_id")[0]
        member_status = cast(str | None, getattr(member, "status", None))
        return MemoryActorContextEvidence(
            actor_id=resolved_actor_id,
            identity_session_id=session_id,
            parent_identity_session_id=parent_session_id,
            attention_session_id=request.expected_attention_session_id,
            identity_session_exists=True,
            identity_session_status=session_status,
            actor_session_member_id=cast(UUID, getattr(member, "session_member_id")),
            actor_session_member_status=member_status,
            actor_session_member_active=True,
            actor_sessions_considered=1,
            validation_status="valid",
            valid=True,
            usable=True,
            failure_reasons=[],
        )


def _attention_validation_evidence(
    validation: object,
) -> AttentionTransitionValidationEvidence:
    transition = getattr(validation, "transition", None)
    return AttentionTransitionValidationEvidence(
        exists=bool(getattr(validation, "exists", False)),
        valid=bool(getattr(validation, "valid", False)),
        failure_reasons=list(getattr(validation, "failure_reasons", []) or []),
        attention_focus_transition_id=cast(
            UUID | None,
            getattr(transition, "attention_focus_transition_id", None),
        ),
        identity_session_id=cast(
            UUID | None,
            getattr(transition, "identity_session_id", None),
        ),
        attention_session_id=cast(
            UUID | None,
            getattr(transition, "attention_session_id", None),
        ),
        attention_session_section_id=cast(
            UUID | None,
            getattr(transition, "attention_session_section_id", None),
        ),
        focus_scope_id=cast(UUID | None, getattr(transition, "focus_scope_id", None)),
        object_instance_graph_commit_id=cast(
            UUID | None,
            getattr(transition, "object_instance_graph_commit_id", None),
        ),
        projection_hash=cast(str | None, getattr(transition, "projection_hash", None)),
    )


async def _resolve_actor_memory_context_response(
    *,
    request: ResolveActorMemoryContextRequest,
    support: _MemoryProtocolSupport,
    attention_validator: MemoryAttentionTransitionValidator,
    actor_context_validator: MemoryActorContextValidator,
) -> ResolveActorMemoryContextResponse:
    host_context = support.host_context()
    actor_context = await actor_context_validator.validate_actor_context(
        request,
        host_context=host_context,
        actor_id=host_context.operation_context.actor_id,
    )
    if not actor_context.usable:
        return ResolveActorMemoryContextResponse(
            request_id=request.request_id,
            success=False,
            error="actor_context_validation_failed",
            actor_context=actor_context,
            exists=False,
            memory_working=None,
            items=[],
        )

    memory_context = await _resolve_memory_context_response(
        request=ResolveMemoryContextRequest(
            request_id=request.request_id,
            actor_id=actor_context.actor_id,
            key=request.key,
            kind=request.kind,
            limit=request.limit,
            expected_identity_session_id=actor_context.identity_session_id,
            expected_attention_session_id=actor_context.attention_session_id,
            expected_attention_session_section_id=(
                request.expected_attention_session_section_id
            ),
            expected_focus_scope_id=request.expected_focus_scope_id,
            expected_object_instance_graph_commit_id=(
                request.expected_object_instance_graph_commit_id
            ),
            expected_projection_hash=request.expected_projection_hash,
            validate_sources=request.validate_sources,
            include_unusable=request.include_unusable,
        ),
        support=support,
        attention_validator=attention_validator,
    )
    return ResolveActorMemoryContextResponse(
        request_id=request.request_id,
        success=memory_context.success,
        info=memory_context.info,
        error=memory_context.error,
        actor_context=actor_context,
        exists=memory_context.exists,
        memory_working=memory_context.memory_working,
        items=memory_context.items,
        usable_item_count=memory_context.usable_item_count,
        unresolved_item_count=memory_context.unresolved_item_count,
    )


async def _build_actor_memory_context_snapshot(
    *,
    request: WatchActorMemoryContextRequest,
    support: _MemoryProtocolSupport,
    attention_validator: MemoryAttentionTransitionValidator,
    actor_context_validator: MemoryActorContextValidator,
    known_cursor: str | None,
    known_digest: str | None,
    sequence: int,
) -> tuple[MemoryActorContextSnapshot, bool]:
    resolved = await _resolve_actor_memory_context_response(
        request=_actor_memory_context_request_from_watch(request),
        support=support,
        attention_validator=attention_validator,
        actor_context_validator=actor_context_validator,
    )
    base_snapshot = MemoryActorContextSnapshot(
        actor_context=resolved.actor_context,
        exists=resolved.exists,
        memory_working=resolved.memory_working,
        items=resolved.items,
        usable_item_count=resolved.usable_item_count,
        unresolved_item_count=resolved.unresolved_item_count,
        sequence=sequence,
    )
    digest = _memory_actor_context_digest(base_snapshot)
    cursor = _memory_actor_context_cursor(base_snapshot, digest=digest)
    changed = not (
        (known_digest is not None and known_digest == digest)
        or (known_cursor is not None and known_cursor == cursor)
    )
    snapshot = MemoryActorContextSnapshot(
        actor_context=resolved.actor_context,
        exists=resolved.exists,
        memory_working=resolved.memory_working,
        items=resolved.items,
        usable_item_count=resolved.usable_item_count,
        unresolved_item_count=resolved.unresolved_item_count,
        cursor=cursor,
        digest=digest,
        sequence=sequence,
        change_reason=_memory_actor_context_change_reason(
            known_cursor=known_cursor,
            known_digest=known_digest,
            changed=changed,
        ),
        observed_at=_utc_now_text(),
    )
    return snapshot, changed


async def _stream_actor_memory_context_snapshots(
    *,
    request: WatchActorMemoryContextRequest,
    support: _MemoryProtocolSupport,
    commit_fanout: _MemoryWorkingCommitFanout,
    attention_validator: MemoryAttentionTransitionValidator,
    actor_context_validator: MemoryActorContextValidator,
):
    last_digest = request.known_digest
    last_cursor = request.known_cursor
    sequence = 0
    target_memory_working_id = _watch_target_memory_working_id_from_request(
        request=request,
        operation_context=support.operation_context(),
    )
    after_sequence = (
        commit_fanout.latest_sequence(target_memory_working_id)
        if target_memory_working_id is not None
        else 0
    )

    snapshot, _ = await _build_actor_memory_context_snapshot(
        request=request,
        support=support,
        attention_validator=attention_validator,
        actor_context_validator=actor_context_validator,
        known_cursor=last_cursor,
        known_digest=last_digest,
        sequence=sequence,
    )
    yield _MemoryActorContextStreamUpdate(snapshot=snapshot)
    last_digest = snapshot.digest
    last_cursor = snapshot.cursor
    sequence += 1

    if target_memory_working_id is None:
        target_memory_working_id = _watch_target_memory_working_id_from_snapshot(
            request=request,
            snapshot=snapshot,
        )
    if target_memory_working_id is None:
        return

    while True:
        change = await commit_fanout.wait_for_change(
            memory_working_id=target_memory_working_id,
            after_sequence=after_sequence,
        )
        after_sequence = change.sequence
        snapshot, changed = await _build_actor_memory_context_snapshot(
            request=request,
            support=support,
            attention_validator=attention_validator,
            actor_context_validator=actor_context_validator,
            known_cursor=last_cursor,
            known_digest=last_digest,
            sequence=sequence,
        )
        if not changed:
            continue
        snapshot = _memory_actor_context_snapshot_with_change_reason(
            snapshot,
            change_reason="memory_commit",
        )
        yield _MemoryActorContextStreamUpdate(snapshot=snapshot, change=change)
        last_digest = snapshot.digest
        last_cursor = snapshot.cursor
        sequence += 1


def _memory_working_fact_from_stream_update(
    update: _MemoryActorContextStreamUpdate,
) -> MemoryWorkingFact | None:
    change = update.change
    if (
        change is None
        or change.fact_kind not in {"event_remembered", "event_meaning_resolved"}
        or change.memory_working_item_id is None
        or change.commit_id is None
    ):
        return None

    snapshot = update.snapshot
    memory_working = snapshot.memory_working
    if (
        memory_working is None
        or memory_working.memory_working_id != change.memory_working_id
    ):
        return None
    evidence = next(
        (
            item
            for item in snapshot.items
            if item.item.memory_working_item_id == change.memory_working_item_id
        ),
        None,
    )
    if evidence is None or evidence.item.kind != "event":
        return None
    item = evidence.item
    if item.event_id is None:
        return None

    resolved_event_meaning_id: UUID | None = None
    validation_status = evidence.validation_status
    usable = evidence.usable
    if change.fact_kind == "event_remembered":
        provenance = evidence.event_action_provenance
        if provenance is not None:
            validation_status = provenance.validation_status
            usable = provenance.usable
    else:
        resolved = evidence.resolved_event_meaning
        meaning = resolved.meaning if resolved is not None else None
        if meaning is None:
            return None
        resolved_event_meaning_id = meaning.memory_working_event_meaning_id
        validation_status = resolved.validation_status
        usable = resolved.usable

    return MemoryWorkingFact(
        kind=change.fact_kind,
        actor_id=memory_working.actor_id,
        memory_working_id=memory_working.memory_working_id,
        memory_working_item_id=item.memory_working_item_id,
        event_id=item.event_id,
        resolved_event_meaning_id=resolved_event_meaning_id,
        source_actor_subscription_id=item.actor_subscription_id,
        memory_commit_id=change.commit_id,
        validation_status=validation_status,
        usable=usable,
    )


def _actor_memory_context_request_from_watch(
    request: WatchActorMemoryContextRequest,
) -> ResolveActorMemoryContextRequest:
    return ResolveActorMemoryContextRequest(
        request_id=request.request_id,
        actor_id=request.actor_id,
        key=request.key,
        kind=request.kind,
        limit=request.limit,
        identity_session_id=request.identity_session_id,
        parent_identity_session_id=request.parent_identity_session_id,
        expected_attention_session_id=request.expected_attention_session_id,
        expected_attention_session_section_id=(
            request.expected_attention_session_section_id
        ),
        expected_focus_scope_id=request.expected_focus_scope_id,
        expected_object_instance_graph_commit_id=(
            request.expected_object_instance_graph_commit_id
        ),
        expected_projection_hash=request.expected_projection_hash,
        validate_identity=request.validate_identity,
        validate_sources=request.validate_sources,
        include_unusable=request.include_unusable,
    )


def _watch_actor_memory_context_request_from_frame_request(
    request: (
        ResolveActorMemoryContextFrameRequest | WatchActorMemoryContextFrameRequest
    ),
) -> WatchActorMemoryContextRequest:
    return WatchActorMemoryContextRequest(
        request_id=request.request_id,
        actor_id=request.actor_id,
        key=request.key,
        kind=request.kind,
        limit=request.limit,
        identity_session_id=request.identity_session_id,
        parent_identity_session_id=request.parent_identity_session_id,
        expected_attention_session_id=request.expected_attention_session_id,
        expected_attention_session_section_id=(
            request.expected_attention_session_section_id
        ),
        expected_focus_scope_id=request.expected_focus_scope_id,
        expected_object_instance_graph_commit_id=(
            request.expected_object_instance_graph_commit_id
        ),
        expected_projection_hash=request.expected_projection_hash,
        validate_identity=request.validate_identity,
        validate_sources=request.validate_sources,
        include_unusable=request.include_unusable,
        known_cursor=cast(str | None, getattr(request, "known_cursor", None)),
        known_digest=cast(str | None, getattr(request, "known_digest", None)),
    )


def _memory_actor_context_frame_from_snapshot(
    snapshot: MemoryActorContextSnapshot,
) -> MemoryActorContextFrame:
    frame_items = [
        _memory_actor_context_frame_item_from_evidence(item) for item in snapshot.items
    ]
    usable_items = [item for item in frame_items if item.usable]
    unresolved_items = [item for item in frame_items if not item.usable]
    return MemoryActorContextFrame(
        actor_context=snapshot.actor_context,
        exists=snapshot.exists,
        memory_working=snapshot.memory_working,
        usable_items=usable_items,
        unresolved_items=unresolved_items,
        usable_item_count=snapshot.usable_item_count,
        unresolved_item_count=snapshot.unresolved_item_count,
        cursor=snapshot.cursor,
        digest=snapshot.digest,
        sequence=snapshot.sequence,
        change_reason=snapshot.change_reason,
        observed_at=snapshot.observed_at,
    )


def _memory_actor_context_frame_item_from_evidence(
    evidence: MemoryWorkingItemEvidence,
) -> MemoryActorContextFrameItem:
    item = evidence.item
    source_kind, source_id = _memory_actor_context_frame_item_source(item)
    meaning_evidence = evidence.resolved_event_meaning
    resolved_meaning = (
        meaning_evidence.meaning
        if meaning_evidence is not None and meaning_evidence.usable
        else None
    )
    fallback_text = _memory_actor_context_frame_item_text(
        item=item,
        source_kind=source_kind,
        source_id=source_id,
    )
    return MemoryActorContextFrameItem(
        memory_working_item_id=item.memory_working_item_id,
        kind=item.kind,
        position=item.position,
        text=(resolved_meaning.meaning_text if resolved_meaning else fallback_text),
        text_source=(
            "resolved_event_meaning"
            if resolved_meaning is not None
            else _memory_actor_context_frame_item_text_source(
                item=item,
                source_kind=source_kind,
                source_id=source_id,
            )
        ),
        meaning_status=(
            meaning_evidence.validation_status
            if meaning_evidence is not None
            else ("not_resolved" if item.kind == "event" else "not_applicable")
        ),
        resolved_event_meaning_id=(
            resolved_meaning.memory_working_event_meaning_id
            if resolved_meaning is not None
            else None
        ),
        source_kind=source_kind,
        source_id=source_id,
        validation_status=evidence.validation_status,
        usable=evidence.usable,
        failure_reasons=evidence.failure_reasons,
    )


def _memory_actor_context_frame_item_source(
    item: MemoryWorkingItemPin,
) -> tuple[str | None, UUID | None]:
    if item.attention_focus_transition_id is not None:
        return "attention_focus_transition", item.attention_focus_transition_id
    if item.content_id is not None:
        return "content", item.content_id
    if item.event_id is not None:
        return "event", item.event_id
    if item.tool_call_id is not None:
        return "tool_call", item.tool_call_id
    if item.tool_response_id is not None:
        return "tool_response", item.tool_response_id
    if item.object_instance_graph_branch_id is not None:
        return "object_instance_graph_branch", item.object_instance_graph_branch_id
    return item.kind, None


def _memory_actor_context_frame_item_text(
    *,
    item: MemoryWorkingItemPin,
    source_kind: str | None,
    source_id: UUID | None,
) -> str | None:
    if item.summary:
        return item.summary
    if item.rationale:
        return item.rationale
    if source_kind is not None and source_id is not None:
        return f"{source_kind}:{source_id}"
    return None


def _memory_actor_context_frame_item_text_source(
    *,
    item: MemoryWorkingItemPin,
    source_kind: str | None,
    source_id: UUID | None,
) -> str | None:
    if item.summary:
        return "summary"
    if item.rationale:
        return "rationale"
    if source_kind is not None and source_id is not None:
        return "source_reference"
    return None


def _memory_actor_context_cursor(
    snapshot: MemoryActorContextSnapshot,
    *,
    digest: str,
) -> str:
    memory_working = snapshot.memory_working
    if memory_working is not None:
        latest_item_id = memory_working.latest_item_id
        return (
            f"memory:{memory_working.memory_working_id}:"
            f"items:{memory_working.item_count}:"
            f"latest:{latest_item_id or 'none'}:"
            f"state:{digest}"
        )
    actor_id = snapshot.actor_context.actor_id
    if actor_id is not None:
        return f"actor:{actor_id}:memory:none:state:{digest}"
    return f"actor:none:memory:none:state:{digest}"


def _memory_actor_context_digest(snapshot: MemoryActorContextSnapshot) -> str:
    payload = snapshot.model_dump(
        mode="json",
        exclude={
            "cursor",
            "digest",
            "sequence",
            "change_reason",
            "observed_at",
        },
    )
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _memory_actor_context_change_reason(
    *,
    known_cursor: str | None,
    known_digest: str | None,
    changed: bool,
) -> str:
    if known_cursor is None and known_digest is None:
        return "initial"
    if changed:
        return "changed"
    return "unchanged"


def _memory_actor_context_snapshot_with_change_reason(
    snapshot: MemoryActorContextSnapshot,
    *,
    change_reason: str,
) -> MemoryActorContextSnapshot:
    return MemoryActorContextSnapshot(
        actor_context=snapshot.actor_context,
        exists=snapshot.exists,
        memory_working=snapshot.memory_working,
        items=snapshot.items,
        usable_item_count=snapshot.usable_item_count,
        unresolved_item_count=snapshot.unresolved_item_count,
        cursor=snapshot.cursor,
        digest=snapshot.digest,
        sequence=snapshot.sequence,
        change_reason=change_reason,
        observed_at=snapshot.observed_at,
    )


def _watch_target_memory_working_id_from_request(
    *,
    request: WatchActorMemoryContextRequest,
    operation_context: ServiceOperationContext,
) -> UUID | None:
    actor_id = request.actor_id or operation_context.actor_id
    if actor_id is None:
        return None
    return stable_memory_working_id(
        actor_id=actor_id,
        key=_normalize_key(request.key),
    )


def _watch_target_memory_working_id_from_snapshot(
    *,
    request: WatchActorMemoryContextRequest,
    snapshot: MemoryActorContextSnapshot,
) -> UUID | None:
    if snapshot.memory_working is not None:
        return snapshot.memory_working.memory_working_id
    actor_id = snapshot.actor_context.actor_id or request.actor_id
    if actor_id is None:
        return None
    return stable_memory_working_id(
        actor_id=actor_id,
        key=_normalize_key(request.key),
    )


def _utc_now_text() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


async def _resolve_memory_context_response(
    *,
    request: ResolveMemoryContextRequest,
    support: _MemoryProtocolSupport,
    attention_validator: MemoryAttentionTransitionValidator,
) -> ResolveMemoryContextResponse:
    memory_working = await _load_memory_working_for_request(
        memory_working_id=request.memory_working_id,
        actor_id=request.actor_id,
        key=request.key,
    )
    if memory_working is None:
        return ResolveMemoryContextResponse(
            request_id=request.request_id,
            exists=False,
            memory_working=None,
            items=[],
        )
    items = await _memory_working_items_for_id(
        _row_id(memory_working),
        kind=request.kind,
        limit=request.limit,
    )
    evidence_items = [
        await _memory_working_item_evidence(
            item=await _memory_working_item_pin(item),
            request=request,
            support=support,
            attention_validator=attention_validator,
        )
        for item in items
    ]
    if not request.include_unusable:
        evidence_items = [item for item in evidence_items if item.usable]
    return ResolveMemoryContextResponse(
        request_id=request.request_id,
        exists=True,
        memory_working=await _memory_working_pin(memory_working, items=items),
        items=evidence_items,
        usable_item_count=sum(1 for item in evidence_items if item.usable),
        unresolved_item_count=sum(1 for item in evidence_items if not item.usable),
    )


class _ActorContextResolutionError(Exception):
    def __init__(
        self,
        *,
        status: str,
        identity_session_id: UUID | None = None,
        actor_sessions_considered: int = 0,
    ) -> None:
        super().__init__(status)
        self.status = status
        self.identity_session_id = identity_session_id
        self.actor_sessions_considered = actor_sessions_considered


async def _resolve_identity_session_for_actor_context(
    *,
    client: AwareIdentityServiceApiClient,
    request: ResolveActorMemoryContextRequest,
    actor_id: UUID,
) -> object | None:
    if request.identity_session_id is not None:
        return (
            await client.identity.describe_session.describe_session(
                SessionDescribeRequest(
                    request_id=request.request_id,
                    session_id=request.identity_session_id,
                )
            )
        ).session

    result = await client.identity.list_actor_sessions.list_actor_sessions(
        ActorSessionsListRequest(
            request_id=request.request_id,
            actor_id=actor_id,
            parent_session_id=request.parent_identity_session_id,
            status="active",
            include_inactive=False,
        )
    )
    sessions = [
        session
        for session in _sort_identity_rows(result.sessions, id_attr="session_id")
        if _status_is_active(getattr(session, "status", None))
    ]
    if not sessions:
        raise _ActorContextResolutionError(
            status="identity_actor_session_missing",
            actor_sessions_considered=0,
        )
    if len(sessions) != 1:
        raise _ActorContextResolutionError(
            status="identity_session_ambiguous",
            actor_sessions_considered=len(sessions),
        )
    return sessions[0]


def _actor_context_failure(
    *,
    request: ResolveActorMemoryContextRequest,
    actor_id: UUID | None,
    status: str,
    reasons: list[str],
    identity_session_id: UUID | None = None,
    parent_identity_session_id: UUID | None = None,
    identity_session_exists: bool = False,
    identity_session_status: str | None = None,
    actor_sessions_considered: int = 0,
) -> MemoryActorContextEvidence:
    return MemoryActorContextEvidence(
        actor_id=actor_id,
        identity_session_id=identity_session_id or request.identity_session_id,
        parent_identity_session_id=(
            parent_identity_session_id or request.parent_identity_session_id
        ),
        attention_session_id=request.expected_attention_session_id,
        identity_session_exists=identity_session_exists,
        identity_session_status=identity_session_status,
        actor_sessions_considered=actor_sessions_considered,
        validation_status=status,
        valid=False,
        usable=False,
        failure_reasons=reasons,
    )


def _status_is_active(status: object) -> bool:
    return str(status or "active").strip().casefold() == "active"


def _sort_identity_rows(rows: list[object], *, id_attr: str) -> list[object]:
    return sorted(
        rows,
        key=lambda row: (
            str(getattr(row, "key", "") or ""),
            str(getattr(row, id_attr, "") or ""),
        ),
    )


async def _ensure_memory_working_for_write(
    *,
    support: _MemoryProtocolSupport,
    memory_working_id: UUID | None,
    actor_id: UUID | None,
    key: str,
) -> tuple[object, MemoryWorkingCommitReceipt | None]:
    operation_context = support.operation_context()
    target_id, target_actor_id, target_key = await _resolve_target_memory_working(
        memory_working_id,
        actor_id,
        key,
        operation_context,
    )
    existing = await _load_memory_working_by_id(target_id)
    if existing is not None:
        return existing, None

    runtime_context = await support.runtime_context()
    response = await _invoke_constructor(
        runtime_context=runtime_context,
        operation_context=operation_context,
        branch_id=target_id,
        projection_hash=runtime_context.memory_working_projection_hash,
        object_projection_graph_id=runtime_context.memory_working_opg_id,
        function_id=runtime_context.memory_working_build_function_id,
        kwargs={"actor_id": target_actor_id, "key": target_key},
    )
    row = _MemoryWorkingStub(
        id=target_id,
        actor_id=target_actor_id,
        key=target_key,
        content_chain_id=None,
    )
    return row, _memory_working_receipt(
        response=response,
        memory_working_id=target_id,
        memory_working_item_id=None,
    )


async def _resolve_target_memory_working(
    memory_working_id: UUID | None,
    actor_id: UUID | None,
    key: str,
    operation_context: ServiceOperationContext,
) -> tuple[UUID, UUID, str]:
    if memory_working_id is not None:
        existing = await _load_memory_working_by_id(memory_working_id)
        if existing is not None:
            return (
                memory_working_id,
                cast(UUID, getattr(existing, "actor_id")),
                _normalize_key(cast(str, getattr(existing, "key", key))),
            )
    resolved_actor_id = _resolve_actor_id(actor_id, operation_context)
    resolved_key = _normalize_key(key)
    return (
        memory_working_id
        or stable_memory_working_id(actor_id=resolved_actor_id, key=resolved_key),
        resolved_actor_id,
        resolved_key,
    )


def _resolve_actor_id(
    actor_id: UUID | None,
    operation_context: ServiceOperationContext,
) -> UUID:
    if actor_id is not None:
        return actor_id
    if operation_context.actor_id is not None:
        return operation_context.actor_id
    raise ValueError(
        "Memory working operations require actor_id or operation context actor_id."
    )


async def _load_memory_working_for_request(
    *,
    memory_working_id: UUID | None,
    actor_id: UUID | None,
    key: str,
) -> object | None:
    if memory_working_id is not None:
        return await _load_memory_working_by_id(memory_working_id)
    if actor_id is None:
        return None
    models = _memory_replica_models_or_none()
    if models is None:
        return None
    matches = list(
        await models.memory_working.many(
            actor_id=actor_id,
            key=_normalize_key(key),
        )
    )
    return _sort_memory_working(matches)[0] if matches else None


async def _load_memory_working_by_id(memory_working_id: UUID) -> object | None:
    models = _memory_replica_models_or_none()
    if models is None:
        return None
    return await models.memory_working.by_id(memory_working_id)


async def _load_memory_working_item_by_id(item_id: UUID) -> object | None:
    models = _memory_replica_models_or_none()
    if models is None:
        return None
    return await models.memory_working_item.by_id(item_id)


async def _memory_working_items_for_id(
    memory_working_id: UUID,
    *,
    kind: str | None = None,
    limit: int | None = None,
) -> list[object]:
    models = _memory_replica_models_or_none()
    if models is None:
        return []
    if kind is None:
        items = list(
            await models.memory_working_item.many(memory_working_id=memory_working_id)
        )
    else:
        items = list(
            await models.memory_working_item.many(
                memory_working_id=memory_working_id,
                kind=_normalize_kind(kind),
            )
        )
    sorted_items = _sort_items(items)
    if limit is None:
        return sorted_items
    return sorted_items[: max(0, int(limit))]


async def _next_item_position(memory_working_id: UUID) -> int:
    items = await _memory_working_items_for_id(memory_working_id)
    if not items:
        return 0
    return max(int(getattr(item, "position", 0) or 0) for item in items) + 1


async def _memory_working_pin(
    memory_working: object,
    *,
    items: list[object] | None = None,
) -> MemoryWorkingPin:
    item_rows = items
    if item_rows is None:
        item_rows = await _memory_working_items_for_id(_row_id(memory_working))
    latest = item_rows[-1] if item_rows else None
    return MemoryWorkingPin(
        memory_working_id=_row_id(memory_working),
        actor_id=cast(UUID, getattr(memory_working, "actor_id")),
        key=_normalize_key(cast(str, getattr(memory_working, "key", "default"))),
        content_chain_id=cast(
            UUID | None, getattr(memory_working, "content_chain_id", None)
        ),
        item_count=len(item_rows),
        latest_item_id=_row_id(latest) if latest is not None else None,
    )


async def _memory_working_pin_or_stub(
    *,
    memory_working_id: UUID,
    actor_id: UUID,
    key: str,
) -> MemoryWorkingPin:
    memory_working = await _load_memory_working_by_id(memory_working_id)
    if memory_working is not None:
        return await _memory_working_pin(memory_working)
    return MemoryWorkingPin(
        memory_working_id=memory_working_id,
        actor_id=actor_id,
        key=_normalize_key(key),
    )


async def _memory_working_pin_for_failed_write(
    *,
    memory_working_id: UUID | None,
    actor_id: UUID | None,
    key: str,
    operation_context: ServiceOperationContext,
) -> MemoryWorkingPin:
    if memory_working_id is not None:
        existing = await _load_memory_working_by_id(memory_working_id)
        if existing is not None:
            return await _memory_working_pin(existing)
    target_actor_id = operation_context.actor_id or actor_id
    if target_actor_id is None:
        raise ValueError(
            "Memory working operations require actor_id or operation context actor_id."
        )
    target_key = _normalize_key(key)
    return MemoryWorkingPin(
        memory_working_id=(
            memory_working_id
            or stable_memory_working_id(actor_id=target_actor_id, key=target_key)
        ),
        actor_id=target_actor_id,
        key=target_key,
    )


async def _memory_working_item_pin(item: object) -> MemoryWorkingItemPin:
    event_frame = await _frame_by_id_or_item("event", item)
    resolved_event_meaning = await _resolved_event_meaning_for_event_frame(event_frame)
    content_frame = await _frame_by_id_or_item("content", item)
    tool_frame = await _frame_by_id_or_item("tool", item)
    return MemoryWorkingItemPin(
        memory_working_item_id=_row_id(item),
        memory_working_id=cast(UUID, getattr(item, "memory_working_id")),
        kind=_normalize_kind(getattr(item, "kind")),
        position=int(getattr(item, "position", 0) or 0),
        created_at=getattr(item, "created_at", None),
        event_frame_id=_row_id(event_frame) if event_frame is not None else None,
        event_id=(
            cast(UUID, getattr(event_frame, "event_id"))
            if event_frame is not None
            else None
        ),
        event_config_id=_event_frame_uuid(event_frame, "event_config_id"),
        event_activation_id=_event_frame_uuid(event_frame, "event_activation_id"),
        event_type=_event_frame_str(event_frame, "event_type"),
        event_source=_event_frame_str(event_frame, "event_source"),
        event_status=_event_frame_str(event_frame, "event_status"),
        commit_branch_id=_event_frame_uuid(event_frame, "commit_branch_id"),
        commit_projection_hash=_event_frame_str(event_frame, "commit_projection_hash"),
        commit_id=_event_frame_uuid(event_frame, "commit_id"),
        object_instance_graph_id=_event_frame_uuid(
            event_frame,
            "object_instance_graph_id",
        ),
        object_instance_graph_commit_id=_event_frame_uuid(
            event_frame,
            "object_instance_graph_commit_id",
        ),
        action_intent_id=_event_frame_uuid(event_frame, "action_intent_id"),
        intent_key=_event_frame_str(event_frame, "intent_key"),
        action_config_id=_event_frame_uuid(event_frame, "action_config_id"),
        action_execution_id=_event_frame_uuid(event_frame, "action_execution_id"),
        action_execution_key=_event_frame_str(event_frame, "action_execution_key"),
        api_call_key=_event_frame_uuid(event_frame, "api_call_key"),
        action_binding_id=_event_frame_uuid(event_frame, "action_binding_id"),
        action_experience_id=_event_frame_uuid(event_frame, "action_experience_id"),
        environment_profile_id=_event_frame_uuid(
            event_frame,
            "environment_profile_id",
        ),
        environment_event_id=_event_frame_uuid(event_frame, "environment_event_id"),
        invocation_config_id=_event_frame_uuid(event_frame, "invocation_config_id"),
        endpoint_id=_event_frame_uuid(event_frame, "endpoint_id"),
        actor_subscription_id=_event_frame_uuid(
            event_frame,
            "actor_subscription_id",
        ),
        resolved_event_meaning=(
            _resolved_event_meaning_pin_from_row(
                resolved_event_meaning,
                memory_working_item_id=_row_id(item),
                event_id=cast(UUID, getattr(event_frame, "event_id")),
            )
            if resolved_event_meaning is not None and event_frame is not None
            else None
        ),
        content_frame_id=_row_id(content_frame) if content_frame is not None else None,
        content_id=(
            cast(UUID, getattr(content_frame, "content_id"))
            if content_frame is not None
            else None
        ),
        tool_frame_id=_row_id(tool_frame) if tool_frame is not None else None,
        tool_call_id=(
            cast(UUID, getattr(tool_frame, "tool_call_id"))
            if tool_frame is not None
            else None
        ),
        tool_response_id=(
            cast(UUID | None, getattr(tool_frame, "tool_response_id", None))
            if tool_frame is not None
            else None
        ),
        object_instance_graph_branch_id=(
            cast(
                UUID | None,
                getattr(tool_frame, "object_instance_graph_branch_id", None),
            )
            if tool_frame is not None
            else None
        ),
        projection_hash=(
            cast(str | None, getattr(tool_frame, "projection_hash", None))
            if tool_frame is not None
            else None
        ),
        attention_focus_transition_id=cast(
            UUID | None,
            getattr(item, "attention_transition_id", None),
        ),
        rationale=cast(str | None, getattr(item, "rationale", None)),
        summary=cast(str | None, getattr(item, "summary", None)),
    )


def _event_frame_uuid(event_frame: object | None, field_name: str) -> UUID | None:
    if event_frame is None:
        return None
    return cast(UUID | None, getattr(event_frame, field_name, None))


def _event_frame_str(event_frame: object | None, field_name: str) -> str | None:
    if event_frame is None:
        return None
    return cast(str | None, getattr(event_frame, field_name, None))


async def _resolved_event_meaning_for_event_frame(
    event_frame: object | None,
) -> object | None:
    if event_frame is None:
        return None
    relationship = getattr(event_frame, "resolved_meaning", None)
    if relationship is not None:
        return relationship
    models = _memory_replica_models_or_none()
    if models is None:
        return None
    matches = list(
        await models.memory_working_event_meaning.many(
            memory_working_event_frame_id=_row_id(event_frame)
        )
    )
    if len(matches) > 1:
        raise RuntimeError(
            "Memory event frame has multiple resolved meanings despite unique contract"
        )
    return matches[0] if matches else None


def _resolved_event_meaning_pin_from_row(
    row: object,
    *,
    memory_working_item_id: UUID,
    event_id: UUID,
) -> MemoryResolvedEventMeaningPin:
    return MemoryResolvedEventMeaningPin(
        memory_working_event_meaning_id=_row_id(row),
        memory_working_event_frame_id=cast(
            UUID, getattr(row, "memory_working_event_frame_id")
        ),
        memory_working_item_id=memory_working_item_id,
        event_id=event_id,
        meaning_text=cast(str, getattr(row, "meaning_text")),
        provider_reference=cast(str | None, getattr(row, "provider_reference", None)),
        resolved_at=cast(datetime | None, getattr(row, "resolved_at", None)),
        **{
            field_name: getattr(row, field_name)
            for field_name in _RESOLVED_EVENT_MEANING_RESOLVER_FIELD_NAMES
        },
    )


def _resolved_event_meaning_pin_from_request(
    *,
    request: RecordResolvedEventMeaningRequest,
    memory_working_event_frame_id: UUID,
    resolved_at: datetime,
) -> MemoryResolvedEventMeaningPin:
    result = request.resolved_meaning
    return MemoryResolvedEventMeaningPin(
        memory_working_event_meaning_id=stable_memory_working_event_meaning_id(
            memory_working_event_frame_id=memory_working_event_frame_id,
            resolver_api_call_outcome_id=request.resolver_api_call_outcome_id,
        ),
        memory_working_event_frame_id=memory_working_event_frame_id,
        memory_working_item_id=request.memory_working_item_id,
        event_id=result.event_id,
        meaning_text=result.meaning_text.strip(),
        provider_reference=(
            result.provider_reference.strip() if result.provider_reference else None
        ),
        resolved_at=resolved_at,
        resolver_status="succeeded",
        resolver_endpoint_ref=request.resolver_endpoint_ref.strip(),
        resolver_discriminant=request.resolver_discriminant.strip(),
        **{
            field_name: getattr(request, field_name)
            for field_name in _RESOLVED_EVENT_MEANING_RESOLVER_FIELD_NAMES
            if field_name
            not in {
                "resolver_status",
                "resolver_endpoint_ref",
                "resolver_discriminant",
            }
        },
    )


def _resolved_event_meaning_invocation_kwargs(
    request: RecordResolvedEventMeaningRequest,
) -> dict[str, object]:
    return {
        "meaning_text": request.resolved_meaning.meaning_text,
        "provider_reference": request.resolved_meaning.provider_reference,
        **{
            field_name: getattr(request, field_name)
            for field_name in _RESOLVED_EVENT_MEANING_RESOLVER_FIELD_NAMES
        },
    }


def _resolved_event_meaning_request_error(
    request: RecordResolvedEventMeaningRequest,
) -> str | None:
    if not request.resolved_meaning.meaning_text.strip():
        return "resolved_event_meaning_text_missing"
    if request.resolver_status.strip().casefold() != "succeeded":
        return "resolver_not_succeeded"
    required_text = (
        request.resolver_endpoint_ref,
        request.resolver_discriminant,
        request.resolver_service_operation_projection_hash,
        request.resolver_api_call_outcome_projection_hash,
    )
    if any(not value.strip() for value in required_text):
        return "resolver_terminal_evidence_incomplete"
    return None


def _resolved_event_meaning_matches_request(
    existing: MemoryResolvedEventMeaningPin,
    request: RecordResolvedEventMeaningRequest,
) -> bool:
    expected = _resolved_event_meaning_pin_from_request(
        request=request,
        memory_working_event_frame_id=existing.memory_working_event_frame_id,
        resolved_at=existing.resolved_at or datetime.min.replace(tzinfo=timezone.utc),
    )
    return existing.model_dump(exclude={"resolved_at"}) == expected.model_dump(
        exclude={"resolved_at"}
    )


def _resolved_event_meaning_evidence(
    meaning: MemoryResolvedEventMeaningPin | None,
) -> MemoryResolvedEventMeaningEvidence:
    if meaning is None:
        return MemoryResolvedEventMeaningEvidence(
            validation_status="not_resolved",
            valid=False,
            usable=False,
            failure_reasons=["resolved_event_meaning_missing"],
        )
    reasons: list[str] = []
    if not meaning.meaning_text.strip():
        reasons.append("meaning_text_missing")
    if meaning.resolver_status.strip().casefold() != "succeeded":
        reasons.append("resolver_not_succeeded")
    if (
        meaning.memory_working_event_meaning_id
        != stable_memory_working_event_meaning_id(
            memory_working_event_frame_id=meaning.memory_working_event_frame_id,
            resolver_api_call_outcome_id=meaning.resolver_api_call_outcome_id,
        )
    ):
        reasons.append("meaning_identity_invalid")
    valid = not reasons
    return MemoryResolvedEventMeaningEvidence(
        validation_status="resolved" if valid else "resolved_meaning_invalid",
        valid=valid,
        usable=valid,
        failure_reasons=reasons,
        meaning=meaning,
    )


def _resolved_event_meaning_failure_response(
    *,
    request: RecordResolvedEventMeaningRequest,
    status: str,
    memory_working: MemoryWorkingPin | None = None,
    item: MemoryWorkingItemPin | None = None,
    meaning: MemoryResolvedEventMeaningPin | None = None,
    reasons: list[str] | None = None,
) -> RecordResolvedEventMeaningResponse:
    return RecordResolvedEventMeaningResponse(
        request_id=request.request_id,
        success=False,
        error=status,
        memory_working=memory_working,
        item=item,
        resolved_event_meaning=MemoryResolvedEventMeaningEvidence(
            validation_status=status,
            valid=False,
            usable=False,
            failure_reasons=reasons or [status],
            meaning=meaning,
        ),
        receipt=None,
    )


def _event_action_provenance_kwargs_from_request(
    request: RememberEventRequest,
) -> dict[str, object]:
    return {
        field_name: getattr(request, field_name)
        for field_name in _EVENT_ACTION_PROVENANCE_FIELD_NAMES
    }


def _event_action_provenance_kwargs_from_item(
    item: MemoryWorkingItemPin,
) -> dict[str, object]:
    return {
        field_name: getattr(item, field_name)
        for field_name in _EVENT_ACTION_PROVENANCE_FIELD_NAMES
    }


def _event_action_provenance_supplied(values: dict[str, object]) -> bool:
    return any(_provenance_value_present(value) for value in values.values())


def _provenance_value_present(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _event_action_provenance_evidence_from_request(
    request: RememberEventRequest,
    *,
    operation_context: ServiceOperationContext,
) -> MemoryEventActionProvenanceEvidence:
    actor_id = request.actor_id or operation_context.actor_id
    values = _event_action_provenance_kwargs_from_request(request)
    supplied = _event_action_provenance_supplied(values)
    reasons: list[str] = []
    if (
        request.actor_id is not None
        and operation_context.actor_id is not None
        and request.actor_id != operation_context.actor_id
    ):
        reasons.append("actor_id_operation_context_mismatch")
    if supplied:
        missing = [
            field_name
            for field_name in _REQUIRED_EVENT_ACTION_PROVENANCE_FIELDS
            if not _provenance_value_present(values.get(field_name))
        ]
        reasons.extend(f"missing:{field_name}" for field_name in missing)

    if reasons:
        return _event_action_provenance_evidence(
            event_id=request.event_id,
            actor_id=actor_id,
            values=values,
            validation_status=(
                "actor_id_mismatch"
                if "actor_id_operation_context_mismatch" in reasons
                else "event_action_provenance_incomplete"
            ),
            valid=False,
            usable=False,
            failure_reasons=reasons,
        )
    if not supplied:
        return _event_action_provenance_evidence(
            event_id=request.event_id,
            actor_id=actor_id,
            values=values,
            validation_status="source_unverified",
            valid=False,
            usable=False,
            failure_reasons=["event_action_provenance_not_supplied"],
        )
    return _event_action_provenance_evidence(
        event_id=request.event_id,
        actor_id=actor_id,
        values=values,
        validation_status="action_dispatch_verified",
        valid=True,
        usable=True,
        failure_reasons=[],
    )


def _event_action_provenance_evidence_from_item(
    item: MemoryWorkingItemPin,
    *,
    actor_id: UUID | None = None,
) -> MemoryEventActionProvenanceEvidence:
    values = _event_action_provenance_kwargs_from_item(item)
    supplied = _event_action_provenance_supplied(values)
    missing = [
        field_name
        for field_name in _REQUIRED_EVENT_ACTION_PROVENANCE_FIELDS
        if not _provenance_value_present(values.get(field_name))
    ]
    if not supplied:
        return _event_action_provenance_evidence(
            event_id=item.event_id,
            actor_id=actor_id,
            values=values,
            validation_status="source_unverified",
            valid=False,
            usable=False,
            failure_reasons=["event_action_provenance_not_supplied"],
        )
    if missing:
        return _event_action_provenance_evidence(
            event_id=item.event_id,
            actor_id=actor_id,
            values=values,
            validation_status="event_action_provenance_incomplete",
            valid=False,
            usable=False,
            failure_reasons=[f"missing:{field_name}" for field_name in missing],
        )
    return _event_action_provenance_evidence(
        event_id=item.event_id,
        actor_id=actor_id,
        values=values,
        validation_status="action_dispatch_verified",
        valid=True,
        usable=True,
        failure_reasons=[],
    )


def _event_action_provenance_evidence(
    *,
    event_id: UUID | None,
    actor_id: UUID | None,
    values: dict[str, object],
    validation_status: str,
    valid: bool,
    usable: bool,
    failure_reasons: list[str],
) -> MemoryEventActionProvenanceEvidence:
    return MemoryEventActionProvenanceEvidence(
        validation_status=validation_status,
        valid=valid,
        usable=usable,
        failure_reasons=failure_reasons,
        event_id=event_id,
        actor_id=actor_id,
        event_config_id=cast(UUID | None, values.get("event_config_id")),
        event_activation_id=cast(UUID | None, values.get("event_activation_id")),
        event_type=cast(str | None, values.get("event_type")),
        event_source=cast(str | None, values.get("event_source")),
        event_status=cast(str | None, values.get("event_status")),
        commit_branch_id=cast(UUID | None, values.get("commit_branch_id")),
        commit_projection_hash=cast(str | None, values.get("commit_projection_hash")),
        commit_id=cast(UUID | None, values.get("commit_id")),
        object_instance_graph_id=cast(
            UUID | None,
            values.get("object_instance_graph_id"),
        ),
        object_instance_graph_commit_id=cast(
            UUID | None,
            values.get("object_instance_graph_commit_id"),
        ),
        actor_subscription_id=cast(
            UUID | None,
            values.get("actor_subscription_id"),
        ),
        action_intent_id=cast(UUID | None, values.get("action_intent_id")),
        intent_key=cast(str | None, values.get("intent_key")),
        action_config_id=cast(UUID | None, values.get("action_config_id")),
        action_execution_id=cast(UUID | None, values.get("action_execution_id")),
        action_execution_key=cast(str | None, values.get("action_execution_key")),
        api_call_key=cast(UUID | None, values.get("api_call_key")),
        action_binding_id=cast(UUID | None, values.get("action_binding_id")),
        action_experience_id=cast(UUID | None, values.get("action_experience_id")),
        environment_profile_id=cast(
            UUID | None,
            values.get("environment_profile_id"),
        ),
        environment_event_id=cast(UUID | None, values.get("environment_event_id")),
        invocation_config_id=cast(UUID | None, values.get("invocation_config_id")),
        endpoint_id=cast(UUID | None, values.get("endpoint_id")),
    )


async def _memory_working_item_evidence(
    *,
    item: MemoryWorkingItemPin,
    request: object,
    support: _MemoryProtocolSupport,
    attention_validator: MemoryAttentionTransitionValidator,
) -> MemoryWorkingItemEvidence:
    if not bool(getattr(request, "validate_sources", True)):
        return MemoryWorkingItemEvidence(
            item=item,
            validation_status="not_validated",
            valid=False,
            usable=False,
            failure_reasons=["source_validation_not_requested"],
        )

    if item.kind == "attention":
        return await _attention_item_evidence(
            item=item,
            request=request,
            support=support,
            attention_validator=attention_validator,
        )
    if item.kind == "content":
        return _unverified_item_evidence(
            item=item,
            reason=(
                "content_source_validation_not_available"
                if item.content_id is not None
                else "content_source_missing"
            ),
        )
    if item.kind == "event":
        provenance = _event_action_provenance_evidence_from_item(item)
        meaning = _resolved_event_meaning_evidence(item.resolved_event_meaning)
        return MemoryWorkingItemEvidence(
            item=item,
            validation_status=provenance.validation_status,
            valid=provenance.valid,
            usable=provenance.usable,
            failure_reasons=list(provenance.failure_reasons or []),
            event_action_provenance=provenance,
            resolved_event_meaning=meaning,
        )
    if item.kind == "tool":
        return _unverified_item_evidence(
            item=item,
            reason=(
                "actor_action_validation_not_available"
                if item.tool_call_id is not None
                else "tool_source_missing"
            ),
        )
    return MemoryWorkingItemEvidence(
        item=item,
        validation_status="unsupported_memory_kind",
        valid=False,
        usable=False,
        failure_reasons=[f"unsupported_memory_kind:{item.kind}"],
    )


async def _attention_item_evidence(
    *,
    item: MemoryWorkingItemPin,
    request: object,
    support: _MemoryProtocolSupport,
    attention_validator: MemoryAttentionTransitionValidator,
) -> MemoryWorkingItemEvidence:
    if item.attention_focus_transition_id is None:
        return MemoryWorkingItemEvidence(
            item=item,
            validation_status="attention_transition_missing",
            valid=False,
            usable=False,
            failure_reasons=["attention_transition_missing"],
        )
    try:
        validation = await attention_validator.validate_attention_transition(
            RememberAttentionTransitionRequest(
                request_id=getattr(request, "request_id", None),
                memory_working_id=item.memory_working_id,
                attention_focus_transition_id=item.attention_focus_transition_id,
                expected_identity_session_id=getattr(
                    request,
                    "expected_identity_session_id",
                    None,
                ),
                expected_attention_session_id=getattr(
                    request,
                    "expected_attention_session_id",
                    None,
                ),
                expected_attention_session_section_id=getattr(
                    request,
                    "expected_attention_session_section_id",
                    None,
                ),
                expected_focus_scope_id=getattr(
                    request,
                    "expected_focus_scope_id",
                    None,
                ),
                expected_object_instance_graph_commit_id=getattr(
                    request,
                    "expected_object_instance_graph_commit_id",
                    None,
                ),
                expected_projection_hash=getattr(
                    request,
                    "expected_projection_hash",
                    None,
                ),
            ),
            host_context=support.host_context(),
            actor_id=support.operation_context().actor_id,
        )
    except Exception as exc:  # pragma: no cover - defensive fail-closed path
        validation = AttentionTransitionValidationEvidence(
            exists=False,
            valid=False,
            failure_reasons=[f"attention_validation_error:{type(exc).__name__}"],
            attention_focus_transition_id=item.attention_focus_transition_id,
        )
    return MemoryWorkingItemEvidence(
        item=item,
        validation_status=(
            "valid" if validation.valid else "attention_transition_invalid"
        ),
        valid=validation.valid,
        usable=validation.valid,
        failure_reasons=list(validation.failure_reasons or []),
        attention_validation=validation,
    )


def _unverified_item_evidence(
    *,
    item: MemoryWorkingItemPin,
    reason: str,
) -> MemoryWorkingItemEvidence:
    return MemoryWorkingItemEvidence(
        item=item,
        validation_status="source_unverified",
        valid=False,
        usable=False,
        failure_reasons=[reason],
    )


async def _frame_by_id_or_item(kind: str, item: object) -> object | None:
    relationship = getattr(item, f"{kind}_frame", None)
    if relationship is not None:
        return relationship
    models = _memory_replica_models_or_none()
    if models is None:
        return None
    model = {
        "content": models.memory_working_content_frame,
        "event": models.memory_working_event_frame,
        "tool": models.memory_working_tool_frame,
    }[kind]
    matches = list(await model.many(memory_working_item_id=_row_id(item)))
    return matches[0] if matches else None


def _memory_working_item_stub(
    *,
    memory_working_id: UUID,
    memory_working_item_id: UUID,
    kind: str,
    position: int,
    event_id: UUID | None = None,
    event_config_id: UUID | None = None,
    event_activation_id: UUID | None = None,
    event_type: str | None = None,
    event_source: str | None = None,
    event_status: str | None = None,
    commit_branch_id: UUID | None = None,
    commit_projection_hash: str | None = None,
    commit_id: UUID | None = None,
    object_instance_graph_id: UUID | None = None,
    object_instance_graph_commit_id: UUID | None = None,
    actor_subscription_id: UUID | None = None,
    action_intent_id: UUID | None = None,
    intent_key: str | None = None,
    action_config_id: UUID | None = None,
    action_execution_id: UUID | None = None,
    action_execution_key: str | None = None,
    api_call_key: UUID | None = None,
    action_binding_id: UUID | None = None,
    action_experience_id: UUID | None = None,
    environment_profile_id: UUID | None = None,
    environment_event_id: UUID | None = None,
    invocation_config_id: UUID | None = None,
    endpoint_id: UUID | None = None,
    content_id: UUID | None = None,
    attention_focus_transition_id: UUID | None = None,
    rationale: str | None = None,
    summary: str | None = None,
) -> MemoryWorkingItemPin:
    return MemoryWorkingItemPin(
        memory_working_item_id=memory_working_item_id,
        memory_working_id=memory_working_id,
        kind=kind,
        position=position,
        event_id=event_id,
        event_config_id=event_config_id,
        event_activation_id=event_activation_id,
        event_type=event_type,
        event_source=event_source,
        event_status=event_status,
        commit_branch_id=commit_branch_id,
        commit_projection_hash=commit_projection_hash,
        commit_id=commit_id,
        object_instance_graph_id=object_instance_graph_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        actor_subscription_id=actor_subscription_id,
        action_intent_id=action_intent_id,
        intent_key=intent_key,
        action_config_id=action_config_id,
        action_execution_id=action_execution_id,
        action_execution_key=action_execution_key,
        api_call_key=api_call_key,
        action_binding_id=action_binding_id,
        action_experience_id=action_experience_id,
        environment_profile_id=environment_profile_id,
        environment_event_id=environment_event_id,
        invocation_config_id=invocation_config_id,
        endpoint_id=endpoint_id,
        content_id=content_id,
        attention_focus_transition_id=attention_focus_transition_id,
        rationale=rationale,
        summary=summary,
    )


def _memory_replica_models_or_none() -> _MemoryReplicaModels | None:
    if current_service_ontology_replica_orm_session() is None:
        return None
    return _memory_replica_models()


def _memory_replica_models() -> _MemoryReplicaModels:
    try:
        from aware_memory_ontology_orm_models.memory.memory_working import (
            MemoryWorking as MemoryWorkingOrmModel,
        )
        from aware_memory_ontology_orm_models.memory.memory_working_content_frame import (
            MemoryWorkingContentFrame as MemoryWorkingContentFrameOrmModel,
        )
        from aware_memory_ontology_orm_models.memory.memory_working_event_frame import (
            MemoryWorkingEventFrame as MemoryWorkingEventFrameOrmModel,
        )
        from aware_memory_ontology_orm_models.memory.memory_working_event_meaning import (
            MemoryWorkingEventMeaning as MemoryWorkingEventMeaningOrmModel,
        )
        from aware_memory_ontology_orm_models.memory.memory_working_item import (
            MemoryWorkingItem as MemoryWorkingItemOrmModel,
        )
        from aware_memory_ontology_orm_models.memory.memory_working_tool_frame import (
            MemoryWorkingToolFrame as MemoryWorkingToolFrameOrmModel,
        )
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Memory service ontology replica reads require the generated Memory "
            "ontology ORM model package to be importable. ServiceHost startup "
            "must expose the required ontology ORM package closure."
        ) from exc
    return _MemoryReplicaModels(
        memory_working=MemoryWorkingOrmModel,
        memory_working_item=MemoryWorkingItemOrmModel,
        memory_working_content_frame=MemoryWorkingContentFrameOrmModel,
        memory_working_event_frame=MemoryWorkingEventFrameOrmModel,
        memory_working_event_meaning=MemoryWorkingEventMeaningOrmModel,
        memory_working_tool_frame=MemoryWorkingToolFrameOrmModel,
    )


async def _invoke_constructor(
    *,
    runtime_context: _MemoryRuntimeContext,
    operation_context: ServiceOperationContext,
    branch_id: UUID,
    projection_hash: str,
    object_projection_graph_id: UUID,
    function_id: UUID,
    kwargs: dict[str, object],
) -> InvokeFunctionResponse:
    environment_context = _require_environment_operation_context()
    response = await runtime_context.graph_gateway.invoke_function(
        request=InvokeFunctionRequest(
            actor_id=operation_context.actor_id,
            environment_id=environment_context.environment_id,
            process_id=environment_context.process_id,
            thread_id=environment_context.thread_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            call_target=InvokeFunctionCallTarget.opg_constructor,
            object_projection_graph_id=object_projection_graph_id,
            function_id=function_id,
            args=cast(JsonArray, []),
            kwargs=cast(JsonObject, kwargs),
            expected_graph_hash_pre=None,
            expected_head_commit_id=None,
            commit=True,
            publish=False,
        ),
        graph_context=runtime_context.runtime_index,
    )
    _ensure_invoke_succeeded(response=response)
    return response


async def _invoke_instance(
    *,
    runtime_context: _MemoryRuntimeContext,
    operation_context: ServiceOperationContext,
    branch_id: UUID,
    projection_hash: str,
    object_id: UUID,
    function_id: UUID,
    kwargs: dict[str, object],
) -> InvokeFunctionResponse:
    environment_context = _require_environment_operation_context()
    response = await runtime_context.graph_gateway.invoke_function(
        request=InvokeFunctionRequest(
            actor_id=operation_context.actor_id,
            environment_id=environment_context.environment_id,
            process_id=environment_context.process_id,
            thread_id=environment_context.thread_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            call_target=InvokeFunctionCallTarget.instance,
            object_id=object_id,
            object_projection_graph_id=None,
            function_id=function_id,
            args=cast(JsonArray, []),
            kwargs=cast(JsonObject, kwargs),
            expected_graph_hash_pre=None,
            expected_head_commit_id=None,
            commit=True,
            publish=False,
        ),
        graph_context=runtime_context.runtime_index,
    )
    _ensure_invoke_succeeded(response=response)
    return response


def _require_environment_operation_context() -> EnvironmentOperationContext:
    host_context = current_service_api_host_context()
    if host_context is None or host_context.environment_context is None:
        raise RuntimeError(
            "Memory graph mutation requires an EnvironmentOperationContext "
            "on the active Service API host context."
        )
    return host_context.environment_context


def _ensure_invoke_succeeded(*, response: InvokeFunctionResponse) -> None:
    if (response.status or "").strip().lower() == "succeeded":
        return
    raise RuntimeError(
        "Memory ontology invocation failed: "
        f"status={response.status!r} error={response.error!r}"
    )


def _memory_working_receipt(
    *,
    response: InvokeFunctionResponse,
    memory_working_id: UUID,
    memory_working_item_id: UUID | None,
    prior_receipt: MemoryWorkingCommitReceipt | None = None,
) -> MemoryWorkingCommitReceipt:
    info = None
    if prior_receipt is not None and prior_receipt.commit_id is not None:
        info = f"ensure_commit_id={prior_receipt.commit_id}"
    return MemoryWorkingCommitReceipt(
        memory_working_id=memory_working_id,
        memory_working_item_id=memory_working_item_id,
        branch_id=response.branch_id,
        projection_hash=response.projection_hash,
        commit_id=response.commit_id or response.object_instance_graph_commit_id,
        status=response.status,
        info=info,
    )


def _resolve_memory_runtime_context(
    *,
    runtime_index: MetaGraphRuntimeIndex,
    graph_gateway: ServiceGraphGateway,
) -> _MemoryRuntimeContext:
    memory_working_opg = _require_named_projection(
        runtime_index=runtime_index,
        name=_MEMORY_WORKING_PROJECTION_NAME,
    )
    memory_working_class = _require_class_config(
        runtime_index=runtime_index,
        class_fqn=_MEMORY_WORKING_CLASS_FQN,
    )
    memory_working_event_frame_class = _require_class_config(
        runtime_index=runtime_index,
        class_fqn=_MEMORY_WORKING_EVENT_FRAME_CLASS_FQN,
    )
    return _MemoryRuntimeContext(
        graph_gateway=graph_gateway,
        runtime_index=runtime_index,
        memory_working_opg_id=memory_working_opg.id,
        memory_working_projection_hash=_require_projection_hash(
            memory_working_opg,
            label=_MEMORY_WORKING_PROJECTION_NAME,
        ),
        memory_working_class_config_id=memory_working_class.id,
        memory_working_build_function_id=_require_function_id(
            memory_working_class,
            name="build",
        ),
        memory_working_add_attention_item_function_id=_require_function_id(
            memory_working_class,
            name="add_attention_item",
        ),
        memory_working_add_content_item_function_id=_require_function_id(
            memory_working_class,
            name="add_content_item",
        ),
        memory_working_add_event_item_function_id=_require_function_id(
            memory_working_class,
            name="add_event_item",
        ),
        memory_working_event_frame_record_resolved_meaning_function_id=(
            _require_function_id(
                memory_working_event_frame_class,
                name="record_resolved_meaning",
            )
        ),
    )


def _projection_lookup_key(value: object) -> str:
    text = str(value or "").strip().casefold()
    return "".join(char for char in text if char.isalnum())


def _require_named_projection(
    *,
    runtime_index: MetaGraphRuntimeIndex,
    name: str,
) -> Any:
    requested = str(name or "").strip()
    exact_matches = [
        candidate
        for candidate in getattr(
            getattr(runtime_index, "ocg", None),
            "object_projection_graphs",
            [],
        )
        or []
        if (getattr(candidate, "name", "") or "").strip() == requested
    ]
    matches = exact_matches
    if not matches:
        requested_key = _projection_lookup_key(requested)
        matches = [
            candidate
            for candidate in getattr(
                getattr(runtime_index, "ocg", None),
                "object_projection_graphs",
                [],
            )
            or []
            if _projection_lookup_key(getattr(candidate, "name", "")) == requested_key
        ]
    if not matches:
        raise ValueError(f"Memory projection `{name}` is missing from runtime index.")
    if len(matches) != 1:
        raise ValueError(
            f"Memory projection `{name}` is ambiguous in runtime index: "
            f"expected 1, found {len(matches)}"
        )
    return matches[0]


def _require_class_config(
    *,
    runtime_index: MetaGraphRuntimeIndex,
    class_fqn: str,
) -> Any:
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
            and "memory" in str(getattr(class_config, "class_fqn", "") or "")
        ]
    if not matches:
        raise ValueError(
            f"Memory class config `{class_fqn}` is missing from runtime index."
        )
    if len(matches) != 1:
        raise ValueError(
            f"Memory class config `{class_fqn}` is ambiguous in runtime index: "
            f"expected 1, found {len(matches)}"
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
    class_fqn = str(getattr(class_config, "fqn", "") or "")
    if not function_ids:
        raise ValueError(
            f"Memory function `{class_fqn}.{name}` is missing from runtime index."
        )
    if len(function_ids) != 1:
        raise ValueError(
            f"Memory function `{class_fqn}.{name}` is ambiguous in runtime index: "
            f"expected 1, found {len(function_ids)}"
        )
    return function_ids[0]


def _require_projection_hash(candidate: object, *, label: str) -> str:
    projection_hash = str(getattr(candidate, "projection_hash", "") or "").strip()
    if not projection_hash:
        raise ValueError(
            f"Memory projection `{label}` could not resolve projection hash from runtime index."
        )
    return projection_hash


def _host_invocation_context_payload(
    host_context: ServiceApiHostContext,
) -> JsonObject | None:
    if host_context.invocation_context is None:
        return None
    return cast(JsonObject, dict(host_context.invocation_context))


def _sort_memory_working(rows: list[object]) -> list[object]:
    return sorted(
        rows,
        key=lambda row: (
            str(getattr(row, "key", "") or ""),
            str(_row_id(row)),
        ),
    )


def _sort_items(items: list[object]) -> list[object]:
    return sorted(
        items,
        key=lambda item: (
            int(getattr(item, "position", 0) or 0),
            str(_row_id(item)),
        ),
    )


def _normalize_key(value: str | None) -> str:
    return (value or "").strip().casefold() or "default"


def _normalize_kind(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw or "").strip().casefold()


def _row_id(row: object) -> UUID:
    return cast(UUID, getattr(row, "id"))


@dataclass(frozen=True, slots=True)
class _MemoryWorkingStub:
    id: UUID
    actor_id: UUID
    key: str
    content_chain_id: UUID | None = None


__all__ = [
    "MemoryAttentionTransitionValidator",
    "build_aware_memory_service_protocol_handler",
]
