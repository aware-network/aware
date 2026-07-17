# pyright: reportMissingImports=false

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any, Protocol, TypeVar, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_attention_ontology.focus.focus import Focus
from aware_attention_ontology.focus.focus_scope import FocusScope
from aware_attention_ontology.layout.layout_section import LayoutSection
from aware_attention_ontology.section.section import Section
from aware_attention_ontology.section.section_focus_scope import SectionFocusScope
from aware_attention_ontology.session.attention_session import AttentionSession
from aware_attention_ontology.stable_ids import (
    stable_attention_session_id,
    stable_attention_session_layout_id,
    stable_attention_session_section_id,
    stable_focus_id,
    stable_attention_layout_topology_transition_id,
    stable_attention_layout_transition_id,
    stable_layout_config_section_config_id,
    stable_layout_id,
    stable_layout_section_id,
    stable_section_id,
)
from aware_attention_service_dto.attention.section.service_operation import (
    ActivateAttentionSectionObservableRequest,
)
from aware_attention_service_dto.attention.section.service_operation import (
    ActivateAttentionSectionObservableResponse,
)
from aware_attention_service_dto.attention.section.models import (
    AttentionFocusScopeCommitPin,
)
from aware_attention_service_dto.attention.section.models import (
    AttentionSectionFocusTarget,
)
from aware_attention_service_dto.attention.section.models import (
    AttentionSectionSnapshot,
)
from aware_attention_service_dto.attention.section.models import (
    AttentionEnvironmentRuntimeTarget,
)
from aware_attention_service_dto.attention.section.models import (
    AttentionRuntimeMountLayoutRequest,
)
from aware_attention_service_dto.attention.section.models import (
    AttentionRuntimeMountSectionRequest,
)
from aware_attention_service_dto.attention.section.models import (
    AttentionRuntimeLayoutSectionState,
)
from aware_attention_service_dto.attention.section.models import (
    AttentionRuntimeMountSnapshot,
)
from aware_attention_service_dto.attention.section.models import (
    AttentionRuntimeMountSnapshotEvent,
)
from aware_attention_service_dto.attention.section.service_operation import (
    GetAttentionFocusScopeCommitsRequest,
)
from aware_attention_service_dto.attention.section.service_operation import (
    GetAttentionFocusScopeCommitsResponse,
)
from aware_attention_service_dto.attention.section.service_operation import (
    GetAttentionSectionStateRequest,
)
from aware_attention_service_dto.attention.section.service_operation import (
    GetAttentionSectionStateResponse,
)
from aware_attention_service_dto.attention.section.service_operation import (
    GetAttentionRuntimeMountRequest,
)
from aware_attention_service_dto.attention.section.service_operation import (
    GetAttentionRuntimeMountResponse,
)
from aware_attention_service_dto.attention.section.service_operation import (
    WatchAttentionRuntimeMountRequest,
)
from aware_attention_service_dto.attention.section.service_operation import (
    WatchAttentionRuntimeMountResponse,
)
from aware_attention_service_dto.attention.session.models import (
    AttentionFocusTransitionPin,
)
from aware_attention_service_dto.attention.session.models import (
    AttentionLayoutTopologyTransitionPin,
)
from aware_attention_service_dto.attention.session.models import (
    AttentionLayoutTopologyTransitionSectionState,
)
from aware_attention_service_dto.attention.session.models import (
    AttentionLayoutTransitionPin,
)
from aware_attention_service_dto.attention.session.models import (
    AttentionLayoutTransitionSectionState,
)
from aware_attention_service_dto.attention.session.models import (
    AttentionSessionLayoutPin,
)
from aware_attention_service_dto.attention.session.models import (
    AttentionSessionPin,
)
from aware_attention_service_dto.attention.session.models import (
    AttentionSessionSectionPin,
)
from aware_attention_service_dto.attention.session.models import (
    AttentionTransitionValidationResult,
)
from aware_attention_service_dto.attention.session.service_operation import (
    ApplyAttentionSessionLayoutTopologyTransitionRequest,
)
from aware_attention_service_dto.attention.session.service_operation import (
    ApplyAttentionSessionLayoutTopologyTransitionResponse,
)
from aware_attention_service_dto.attention.session.service_operation import (
    ApplyAttentionSessionLayoutTransitionRequest,
)
from aware_attention_service_dto.attention.session.service_operation import (
    ApplyAttentionSessionLayoutTransitionResponse,
)
from aware_attention_service_dto.attention.session.service_operation import (
    DescribeAttentionSessionRequest,
)
from aware_attention_service_dto.attention.session.service_operation import (
    DescribeAttentionSessionResponse,
)
from aware_attention_service_dto.attention.session.service_operation import (
    MountAttentionSessionLayoutRequest,
    MountAttentionSessionLayoutResponse,
    MountAttentionSessionSectionRequest,
    MountAttentionSessionSectionResponse,
    StartAttentionSessionRequest,
    StartAttentionSessionResponse,
)
from aware_attention_service_dto.attention.session.service_operation import (
    DescribeAttentionTransitionRequest,
)
from aware_attention_service_dto.attention.session.service_operation import (
    DescribeAttentionTransitionResponse,
)
from aware_attention_service_dto.attention.session.service_operation import (
    ListAttentionTransitionsRequest,
)
from aware_attention_service_dto.attention.session.service_operation import (
    ListAttentionTransitionsResponse,
)
from aware_attention_service_dto.attention.session.service_operation import (
    ValidateAttentionTransitionRequest,
)
from aware_attention_service_dto.attention.session.service_operation import (
    ValidateAttentionTransitionResponse,
)
from aware_code.types import JsonArray, JsonObject
from aware_environment_sdk import (
    EnvironmentCommitReceiptSdkClient,
    EnvironmentSdkCommitReceiptSource,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_root_model
from aware_environment_service_dto.environment.environment import (
    EnvironmentOperationContext,
    LaneCommitReceiptNotification,
)
from aware_identity_service_dto.session.session import SessionDescribeRequest
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionRequest as InvokeFunctionRequest,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionResponse as InvokeFunctionResponse,
)
from aware_meta_service_dto.graph.instance.function_call_target import (
    MetaGraphFunctionCallTarget as InvokeFunctionCallTarget,
)
from aware_orm.models.orm_model import ORMModel
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
from aware_utils.logging import logger
from pydantic import BaseModel

from .environment_fanout import (
    AttentionEnvironmentFanoutFocusConsumer,
    AttentionEnvironmentFocusAttachOutcome,
    AttentionEnvironmentFocusBinding,
    AttentionEnvironmentFocusResolver,
    AttentionEnvironmentFocusRoute,
)

CanonicalActivateAttentionSectionObservableRequest = (
    ActivateAttentionSectionObservableRequest
)
CanonicalGetAttentionFocusScopeCommitsRequest = GetAttentionFocusScopeCommitsRequest
CanonicalGetAttentionRuntimeMountRequest = GetAttentionRuntimeMountRequest
CanonicalGetAttentionSectionStateRequest = GetAttentionSectionStateRequest
CanonicalWatchAttentionRuntimeMountRequest = WatchAttentionRuntimeMountRequest
CanonicalApplyAttentionSessionLayoutTopologyTransitionRequest = (
    ApplyAttentionSessionLayoutTopologyTransitionRequest
)
CanonicalApplyAttentionSessionLayoutTransitionRequest = (
    ApplyAttentionSessionLayoutTransitionRequest
)
CanonicalDescribeAttentionSessionRequest = DescribeAttentionSessionRequest
CanonicalMountAttentionSessionLayoutRequest = MountAttentionSessionLayoutRequest
CanonicalMountAttentionSessionSectionRequest = MountAttentionSessionSectionRequest
CanonicalStartAttentionSessionRequest = StartAttentionSessionRequest
CanonicalDescribeAttentionTransitionRequest = DescribeAttentionTransitionRequest
CanonicalListAttentionTransitionsRequest = ListAttentionTransitionsRequest
CanonicalValidateAttentionTransitionRequest = ValidateAttentionTransitionRequest
ServiceAttentionFocusScopeCommitPin = AttentionFocusScopeCommitPin
ServiceAttentionRuntimeMountSnapshotEvent = AttentionRuntimeMountSnapshotEvent
ServiceAttentionRuntimeMountSnapshot = AttentionRuntimeMountSnapshot
ServiceAttentionSectionSnapshot = AttentionSectionSnapshot
ServiceAttentionFocusTransitionPin = AttentionFocusTransitionPin
ServiceAttentionLayoutTopologyTransitionPin = AttentionLayoutTopologyTransitionPin
ServiceAttentionLayoutTopologyTransitionSectionState = (
    AttentionLayoutTopologyTransitionSectionState
)
ServiceAttentionLayoutTransitionPin = AttentionLayoutTransitionPin
ServiceAttentionLayoutTransitionSectionState = AttentionLayoutTransitionSectionState
ServiceAttentionSessionLayoutPin = AttentionSessionLayoutPin
ServiceAttentionSessionPin = AttentionSessionPin
ServiceAttentionSessionSectionPin = AttentionSessionSectionPin
ServiceAttentionTransitionValidationResult = AttentionTransitionValidationResult

_TModel = TypeVar("_TModel", bound=ORMModel)


def build_aware_attention_service_protocol_handler(
    *, identity_api_client: Any | None = None
) -> object:
    return _AwareAttentionServiceProtocolHandler(
        identity_api_client=identity_api_client,
    )


_runtime_mount_revision_value = 0
_runtime_mount_event: asyncio.Event = asyncio.Event()
_FOCUS_SCOPE_PROJECTION_NAME = "FocusScope"
_RUNTIME_MOUNT_WATCH_SUBSCRIBER_ID = "aware_attention.runtime_mount.environment_fanout"
_IDENTITY_SERVICE_API_PACKAGE_NAME = "identity-service-api"


class _CommitReceiptStreamSource(Protocol):
    def stream_commit_receipts(
        self,
        *,
        subscriber_id: str,
    ) -> AsyncIterator[LaneCommitReceiptNotification]: ...


class _ReplicaQueryModel(Protocol):
    @classmethod
    async def many(cls, **eq_fields: object) -> list[Any]: ...

    @classmethod
    async def by_id(cls, row_id: UUID) -> Any | None: ...


@dataclass(frozen=True, slots=True)
class _AttentionRuntimeContext:
    graph_gateway: ServiceGraphGateway
    runtime_index: MetaGraphRuntimeIndex
    section_opg_id: UUID
    section_projection_hash: str
    section_class_config_id: UUID
    section_focus_scope_class_config_id: UUID
    focus_opg_id: UUID
    focus_projection_hash: str
    focus_class_config_id: UUID
    focus_scope_opg_id: UUID
    focus_scope_projection_hash: str
    focus_scope_class_config_id: UUID
    layout_projection_hash: str
    attention_session_projection_hash: str
    attention_session_opg_id: UUID
    attention_session_build_function_id: UUID
    attention_session_mount_layout_function_id: UUID
    attention_session_layout_attach_section_function_id: UUID
    section_build_function_id: UUID
    section_add_focus_scope_function_id: UUID
    section_set_active_focus_scope_function_id: UUID
    focus_build_function_id: UUID
    focus_scope_set_focus_function_id: UUID
    focus_scope_build_function_id: UUID
    focus_scope_set_observable_function_id: UUID
    focus_scope_ensure_commit_function_id: UUID
    attention_session_layout_apply_transition_function_id: UUID
    attention_session_layout_apply_topology_transition_function_id: UUID


def _reset_runtime_mount_watch_state() -> None:
    global _runtime_mount_revision_value, _runtime_mount_event
    _runtime_mount_revision_value = 0
    _runtime_mount_event = asyncio.Event()


def _runtime_mount_revision() -> int:
    return _runtime_mount_revision_value


def _notify_runtime_mount_changed() -> None:
    global _runtime_mount_revision_value, _runtime_mount_event
    event = _runtime_mount_event
    _runtime_mount_revision_value += 1
    event.set()
    _runtime_mount_event = asyncio.Event()


async def _wait_for_runtime_mount_change(
    *,
    after_revision: int,
) -> bool:
    if _runtime_mount_revision_value != after_revision:
        return True
    event = _runtime_mount_event
    if _runtime_mount_revision_value != after_revision:
        return True
    await event.wait()
    return _runtime_mount_revision_value != after_revision


@asynccontextmanager
async def _runtime_mount_receipt_subscription(
    *,
    host_context: ServiceApiHostContext,
) -> AsyncIterator[None]:
    source = host_context.environment_commit_receipt_source
    lane_keys: set[tuple[UUID, str]] = set()
    for subscription in host_context.lane_subscriptions:
        projection_hash = (subscription.projection_hash or "").strip()
        if not projection_hash:
            continue
        lane_keys.add((subscription.branch_id, projection_hash))
    task: asyncio.Task[None] | None = None
    if source is not None and lane_keys:
        task = asyncio.create_task(
            _watch_runtime_mount_environment_receipts(
                source=cast(_CommitReceiptStreamSource, source),
                lane_keys=frozenset(lane_keys),
            ),
            name="attention-runtime-mount-environment-fanout-watch",
        )
        await asyncio.sleep(0)
    try:
        yield
    finally:
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            return
        except Exception as exc:
            logger.warning(
                "Attention runtime mount Environment fanout watch stopped: %s",
                exc,
            )


async def _watch_runtime_mount_environment_receipts(
    *,
    source: _CommitReceiptStreamSource,
    lane_keys: frozenset[tuple[UUID, str]],
) -> None:
    stream = source.stream_commit_receipts(
        subscriber_id=_RUNTIME_MOUNT_WATCH_SUBSCRIBER_ID,
    )
    try:
        async for receipt in stream:
            if _runtime_mount_receipt_matches_lanes(
                receipt=receipt,
                lane_keys=lane_keys,
            ):
                _notify_runtime_mount_changed()
    finally:
        aclose = cast(Any, getattr(stream, "aclose", None))
        if callable(aclose):
            await cast(Awaitable[object], aclose())


def _runtime_mount_receipt_matches_lanes(
    *,
    receipt: LaneCommitReceiptNotification,
    lane_keys: frozenset[tuple[UUID, str]],
) -> bool:
    projection_hash = (receipt.projection_hash or "").strip()
    if not projection_hash:
        return False
    return (receipt.branch_id, projection_hash) in lane_keys


class _AttentionProtocolSupport:
    def __init__(self, *, identity_api_client: Any | None = None) -> None:
        self.identity_api_client = identity_api_client

    def host_context(self) -> ServiceApiHostContext:
        host_context = current_service_api_host_context()
        if host_context is None:
            raise RuntimeError(
                "Attention service protocol requires an active Service API host context."
            )
        return host_context

    async def runtime_context(self) -> _AttentionRuntimeContext:
        host_context = self.host_context()
        if host_context.graph_gateway is None:
            raise RuntimeError(
                "Attention service protocol requires a Service graph gateway."
            )
        graph_gateway = host_context.graph_gateway
        runtime_index = self._coerce_runtime_index(
            await self._resolve_graph_context(
                host_context=host_context,
                graph_gateway=graph_gateway,
            )
        )
        return _resolve_attention_runtime_context(
            runtime_index=runtime_index,
            graph_gateway=graph_gateway,
        )

    def identity_session_api_client(self) -> Any:
        if self.identity_api_client is not None:
            return self.identity_api_client
        host_context = self.host_context()
        invoker = build_service_api_client_for_api_package(
            host_context.service_api_dependency_routes,
            api_package_name=_IDENTITY_SERVICE_API_PACKAGE_NAME,
            actor_id=host_context.operation_context.actor_id,
            invocation_context=(
                dict(host_context.invocation_context)
                if host_context.invocation_context is not None
                else None
            ),
        )
        if invoker is None:
            raise RuntimeError(
                "AttentionSession start requires the Identity service API route."
            )
        from aware_identity_service_api import AwareIdentityServiceApiClient

        return AwareIdentityServiceApiClient(invoker)

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
            return await cast(Awaitable[object], resolve_graph_context())
        raise RuntimeError(
            "Attention service protocol requires a Service graph context."
        )

    @staticmethod
    def _coerce_runtime_index(graph_context: object) -> MetaGraphRuntimeIndex:
        return cast(
            MetaGraphRuntimeIndex,
            getattr(graph_context, "index", graph_context),
        )


class _AttentionGetSectionStateCapabilityHandler:
    def __init__(self, *, support: _AttentionProtocolSupport) -> None:
        self._support = support

    async def get_section_state(
        self,
        request: GetAttentionSectionStateRequest,
    ) -> GetAttentionSectionStateResponse:
        runtime_context = await self._support.runtime_context()
        host_context = self._support.host_context()
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalGetAttentionSectionStateRequest,
        )
        snapshot = await _get_section_state(
            runtime_context=runtime_context,
            operation_context=host_context.operation_context,
            request=canonical_request,
        )
        return GetAttentionSectionStateResponse(
            snapshot=_convert_model(
                snapshot, model_cls=ServiceAttentionSectionSnapshot
            ),
        )


class _AttentionGetRuntimeMountCapabilityHandler:
    def __init__(self, *, support: _AttentionProtocolSupport) -> None:
        self._support = support

    async def get_runtime_mount(
        self,
        request: GetAttentionRuntimeMountRequest,
    ) -> GetAttentionRuntimeMountResponse:
        runtime_context = await self._support.runtime_context()
        host_context = self._support.host_context()
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalGetAttentionRuntimeMountRequest,
        )
        runtime_mount = await _get_runtime_mount(
            runtime_context=runtime_context,
            operation_context=host_context.operation_context,
            request=canonical_request,
        )
        return GetAttentionRuntimeMountResponse(
            runtime_mount=_convert_model(
                runtime_mount,
                model_cls=ServiceAttentionRuntimeMountSnapshot,
            ),
        )


class _AttentionGetFocusScopeCommitsCapabilityHandler:
    def __init__(self, *, support: _AttentionProtocolSupport) -> None:
        self._support = support

    async def get_focus_scope_commits(
        self,
        request: GetAttentionFocusScopeCommitsRequest,
    ) -> GetAttentionFocusScopeCommitsResponse:
        runtime_context = await self._support.runtime_context()
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalGetAttentionFocusScopeCommitsRequest,
        )
        return await _get_focus_scope_commits(
            runtime_context=runtime_context,
            request=canonical_request,
        )


class _AttentionWatchRuntimeMountCapabilityHandler:
    def __init__(self, *, support: _AttentionProtocolSupport) -> None:
        self._support = support

    async def watch_runtime_mount(
        self,
        request: WatchAttentionRuntimeMountRequest,
    ) -> WatchAttentionRuntimeMountResponse:
        runtime_context = await self._support.runtime_context()
        host_context = self._support.host_context()
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalWatchAttentionRuntimeMountRequest,
        )
        runtime_mount = await _get_runtime_mount(
            runtime_context=runtime_context,
            operation_context=host_context.operation_context,
            request=_runtime_mount_request_from_watch_request(canonical_request),
        )
        return WatchAttentionRuntimeMountResponse(
            runtime_mount=_convert_model(
                runtime_mount,
                model_cls=ServiceAttentionRuntimeMountSnapshot,
            ),
        )

    async def stream_watch_runtime_mount(
        self,
        request: WatchAttentionRuntimeMountRequest,
    ) -> AsyncIterator[ServiceAttentionRuntimeMountSnapshotEvent]:
        runtime_context = await self._support.runtime_context()
        host_context = self._support.host_context()
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalWatchAttentionRuntimeMountRequest,
        )
        runtime_mount_request = _runtime_mount_request_from_watch_request(
            canonical_request
        )
        last_signature: str | None = None

        async with _runtime_mount_receipt_subscription(host_context=host_context):
            while True:
                baseline_revision = _runtime_mount_revision()
                runtime_mount = await _get_runtime_mount(
                    runtime_context=runtime_context,
                    operation_context=host_context.operation_context,
                    request=runtime_mount_request,
                )
                signature = _runtime_mount_signature(runtime_mount)
                if signature != last_signature:
                    yield ServiceAttentionRuntimeMountSnapshotEvent(
                        runtime_mount=_convert_model(
                            runtime_mount,
                            model_cls=ServiceAttentionRuntimeMountSnapshot,
                        )
                    )
                    last_signature = signature
                if _runtime_mount_revision() != baseline_revision:
                    continue
                await _wait_for_runtime_mount_change(
                    after_revision=baseline_revision,
                )


class _AttentionStartSessionCapabilityHandler:
    def __init__(self, *, support: _AttentionProtocolSupport) -> None:
        self._support = support

    async def start_attention_session(
        self,
        request: StartAttentionSessionRequest,
    ) -> StartAttentionSessionResponse:
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalStartAttentionSessionRequest,
        )
        identity_client = self._support.identity_session_api_client()
        identity_result = (
            await identity_client.identity.describe_session.describe_session(
                SessionDescribeRequest(
                    session_id=canonical_request.identity_session_id,
                )
            )
        )
        identity_session = identity_result.session
        if identity_session is None:
            raise RuntimeError(
                "AttentionSession start requires a committed Identity Session."
            )
        if identity_session.session_id != canonical_request.identity_session_id:
            raise RuntimeError("AttentionSession Identity Session authority mismatch.")

        status = canonical_request.status.strip().lower()
        if status not in {"active", "suspended", "closed"}:
            raise ValueError(
                f"Unsupported AttentionSession status: {canonical_request.status!r}."
            )
        attention_session_id = stable_attention_session_id(
            identity_session_id=canonical_request.identity_session_id,
        )
        runtime_context = await self._support.runtime_context()
        host_context = self._support.host_context()
        result = await _invoke_constructor(
            runtime_context=runtime_context,
            operation_context=host_context.operation_context,
            branch_id=attention_session_id,
            projection_hash=runtime_context.attention_session_projection_hash,
            object_projection_graph_id=runtime_context.attention_session_opg_id,
            function_id=runtime_context.attention_session_build_function_id,
            kwargs={
                "identity_session_id": canonical_request.identity_session_id,
                "key": canonical_request.key,
                "title": canonical_request.title,
                "description": canonical_request.description,
                "purpose": canonical_request.purpose,
                "status": status,
                "source_kind": canonical_request.source_kind,
                "source_ref": canonical_request.source_ref,
                "metadata_json": canonical_request.metadata_json or {},
            },
        )
        return StartAttentionSessionResponse(
            request_id=canonical_request.request_id,
            attention_session_id=attention_session_id,
            identity_session_id=canonical_request.identity_session_id,
            status=status,
            domain_commit_id=result.domain_commit_id,
            object_instance_graph_commit_id=(result.object_instance_graph_commit_id),
            graph_hash_post=_normalize_optional_text(result.graph_hash_post),
        )


class _AttentionMountSessionLayoutCapabilityHandler:
    def __init__(self, *, support: _AttentionProtocolSupport) -> None:
        self._support = support

    async def mount_attention_session_layout(
        self,
        request: MountAttentionSessionLayoutRequest,
    ) -> MountAttentionSessionLayoutResponse:
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalMountAttentionSessionLayoutRequest,
        )
        if canonical_request.order < 0:
            raise ValueError("Attention session layout order must be non-negative.")
        runtime_context = await self._support.runtime_context()
        if (
            await _load_attention_session_lane_snapshot(
                runtime_context=runtime_context,
                attention_session_id=canonical_request.attention_session_id,
            )
            is None
        ):
            raise RuntimeError(
                "Attention layout mount requires a committed AttentionSession."
            )
        host_context = self._support.host_context()
        result = await _invoke_instance(
            runtime_context=runtime_context,
            operation_context=host_context.operation_context,
            branch_id=canonical_request.attention_session_id,
            projection_hash=runtime_context.attention_session_projection_hash,
            object_id=canonical_request.attention_session_id,
            function_id=runtime_context.attention_session_mount_layout_function_id,
            kwargs={
                "layout_id": canonical_request.layout_id,
                "layout_config_id": canonical_request.layout_config_id,
                "key": canonical_request.key,
                "order": canonical_request.order,
                "is_active": canonical_request.is_active,
            },
        )
        return MountAttentionSessionLayoutResponse(
            request_id=canonical_request.request_id,
            attention_session_id=canonical_request.attention_session_id,
            attention_session_layout_id=stable_attention_session_layout_id(
                attention_session_id=canonical_request.attention_session_id,
                layout_id=canonical_request.layout_id,
            ),
            layout_id=canonical_request.layout_id,
            domain_commit_id=result.domain_commit_id,
            object_instance_graph_commit_id=(result.object_instance_graph_commit_id),
            graph_hash_post=_normalize_optional_text(result.graph_hash_post),
        )


class _AttentionMountSessionSectionCapabilityHandler:
    def __init__(self, *, support: _AttentionProtocolSupport) -> None:
        self._support = support

    async def mount_attention_session_section(
        self,
        request: MountAttentionSessionSectionRequest,
    ) -> MountAttentionSessionSectionResponse:
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalMountAttentionSessionSectionRequest,
        )
        if canonical_request.order < 0:
            raise ValueError("Attention session section order must be non-negative.")
        runtime_context = await self._support.runtime_context()
        snapshot = await _load_attention_session_lane_snapshot(
            runtime_context=runtime_context,
            attention_session_id=canonical_request.attention_session_id,
        )
        if snapshot is None:
            raise RuntimeError(
                "Attention section mount requires a committed AttentionSession."
            )
        if (
            _select_runtime_session_layout(
                session=snapshot.session,
                attention_session_layout_id=(
                    canonical_request.attention_session_layout_id
                ),
            )
            is None
        ):
            raise RuntimeError(
                "Attention section mount requires a layout on the target "
                "AttentionSession lane."
            )
        host_context = self._support.host_context()
        result = await _invoke_instance(
            runtime_context=runtime_context,
            operation_context=host_context.operation_context,
            branch_id=canonical_request.attention_session_id,
            projection_hash=runtime_context.attention_session_projection_hash,
            object_id=canonical_request.attention_session_layout_id,
            function_id=(
                runtime_context.attention_session_layout_attach_section_function_id
            ),
            kwargs={
                "layout_section_id": canonical_request.layout_section_id,
                "section_id": canonical_request.section_id,
                "section_key": canonical_request.section_key,
                "order": canonical_request.order,
                "is_active": canonical_request.is_active,
            },
        )
        return MountAttentionSessionSectionResponse(
            request_id=canonical_request.request_id,
            attention_session_id=canonical_request.attention_session_id,
            attention_session_layout_id=(canonical_request.attention_session_layout_id),
            attention_session_section_id=stable_attention_session_section_id(
                attention_session_layout_id=(
                    canonical_request.attention_session_layout_id
                ),
                layout_section_id=canonical_request.layout_section_id,
                section_id=canonical_request.section_id,
            ),
            layout_section_id=canonical_request.layout_section_id,
            section_id=canonical_request.section_id,
            domain_commit_id=result.domain_commit_id,
            object_instance_graph_commit_id=(result.object_instance_graph_commit_id),
            graph_hash_post=_normalize_optional_text(result.graph_hash_post),
        )


class _AttentionDescribeSessionCapabilityHandler:
    def __init__(self, *, support: _AttentionProtocolSupport) -> None:
        self._support = support

    async def describe_attention_session(
        self,
        request: DescribeAttentionSessionRequest,
    ) -> DescribeAttentionSessionResponse:
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalDescribeAttentionSessionRequest,
        )
        response = await _describe_attention_session(request=canonical_request)
        if response.session is None:
            return response
        runtime_context = await self._support.runtime_context()
        lane_snapshot = await _load_attention_session_lane_snapshot(
            runtime_context=runtime_context,
            attention_session_id=response.session.attention_session_id,
        )
        if lane_snapshot is None:
            return response
        active_layout = _select_runtime_session_layout(
            session=lane_snapshot.session,
            attention_session_layout_id=(
                response.active_layout.attention_session_layout_id
                if response.active_layout is not None
                else None
            ),
        )
        response.active_layout_transition = _active_layout_transition_pin(
            layout=active_layout,
            head=lane_snapshot.head,
        )
        response.active_layout_topology_transition = (
            _active_layout_topology_transition_pin(
                layout=active_layout,
                head=lane_snapshot.head,
            )
        )
        return response


class _AttentionApplySessionLayoutTransitionCapabilityHandler:
    def __init__(self, *, support: _AttentionProtocolSupport) -> None:
        self._support = support

    async def apply_session_layout_transition(
        self,
        request: ApplyAttentionSessionLayoutTransitionRequest,
    ) -> ApplyAttentionSessionLayoutTransitionResponse:
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalApplyAttentionSessionLayoutTransitionRequest,
        )
        runtime_context = await self._support.runtime_context()
        host_context = self._support.host_context()
        return await _apply_session_layout_transition(
            runtime_context=runtime_context,
            operation_context=host_context.operation_context,
            request=canonical_request,
        )


class _AttentionApplySessionLayoutTopologyTransitionCapabilityHandler:
    def __init__(self, *, support: _AttentionProtocolSupport) -> None:
        self._support = support

    async def apply_session_layout_topology_transition(
        self,
        request: ApplyAttentionSessionLayoutTopologyTransitionRequest,
    ) -> ApplyAttentionSessionLayoutTopologyTransitionResponse:
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalApplyAttentionSessionLayoutTopologyTransitionRequest,
        )
        runtime_context = await self._support.runtime_context()
        host_context = self._support.host_context()
        return await _apply_session_layout_topology_transition(
            runtime_context=runtime_context,
            operation_context=host_context.operation_context,
            request=canonical_request,
        )


class _AttentionDescribeTransitionCapabilityHandler:
    def __init__(self, *, support: _AttentionProtocolSupport) -> None:
        self._support = support

    async def describe_attention_transition(
        self,
        request: DescribeAttentionTransitionRequest,
    ) -> DescribeAttentionTransitionResponse:
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalDescribeAttentionTransitionRequest,
        )
        return await _describe_attention_transition(request=canonical_request)


class _AttentionListTransitionsCapabilityHandler:
    def __init__(self, *, support: _AttentionProtocolSupport) -> None:
        self._support = support

    async def list_attention_transitions(
        self,
        request: ListAttentionTransitionsRequest,
    ) -> ListAttentionTransitionsResponse:
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalListAttentionTransitionsRequest,
        )
        return await _list_attention_transitions(request=canonical_request)


class _AttentionValidateTransitionCapabilityHandler:
    def __init__(self, *, support: _AttentionProtocolSupport) -> None:
        self._support = support

    async def validate_attention_transition(
        self,
        request: ValidateAttentionTransitionRequest,
    ) -> ValidateAttentionTransitionResponse:
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalValidateAttentionTransitionRequest,
        )
        validation = await _validate_attention_transition(request=canonical_request)
        return ValidateAttentionTransitionResponse(
            validation=_convert_model(
                validation,
                model_cls=ServiceAttentionTransitionValidationResult,
            ),
        )


class _AttentionActivateSectionObservableCapabilityHandler:
    def __init__(self, *, support: _AttentionProtocolSupport) -> None:
        self._support = support

    async def activate_section_observable(
        self,
        request: ActivateAttentionSectionObservableRequest,
    ) -> ActivateAttentionSectionObservableResponse:
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalActivateAttentionSectionObservableRequest,
        )
        runtime_context = await self._support.runtime_context()
        host_context = self._support.host_context()
        snapshot = await _activate_section_observable(
            runtime_context=runtime_context,
            operation_context=host_context.operation_context,
            request=canonical_request,
        )
        return ActivateAttentionSectionObservableResponse(
            snapshot=_convert_model(
                snapshot, model_cls=ServiceAttentionSectionSnapshot
            ),
        )


@dataclass(frozen=True, slots=True)
class _AttentionProtocolActivationAuthority:
    handler: _AttentionActivateSectionObservableCapabilityHandler

    async def activate_section_observable(
        self,
        request: ActivateAttentionSectionObservableRequest,
    ) -> AttentionSectionSnapshot:
        response = await self.handler.activate_section_observable(request)
        return response.snapshot

    async def ensure_focus_scope_commit(
        self,
        *,
        focus_scope_id: UUID,
        focus_id: UUID,
        object_instance_graph_commit_id: UUID,
    ) -> None:
        runtime_context = await self.handler._support.runtime_context()
        host_context = self.handler._support.host_context()
        await _ensure_focus_scope_commit(
            runtime_context=runtime_context,
            operation_context=host_context.operation_context,
            focus_scope_id=focus_scope_id,
            focus_id=focus_id,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
        )


class _AttentionApiServiceProtocolHandler:
    def __init__(self, *, support: _AttentionProtocolSupport) -> None:
        self.activate_section_observable = (
            _AttentionActivateSectionObservableCapabilityHandler(support=support)
        )
        self.get_section_state = _AttentionGetSectionStateCapabilityHandler(
            support=support
        )
        self.get_focus_scope_commits = _AttentionGetFocusScopeCommitsCapabilityHandler(
            support=support
        )
        self.start_attention_session = _AttentionStartSessionCapabilityHandler(
            support=support
        )
        self.mount_attention_session_layout = (
            _AttentionMountSessionLayoutCapabilityHandler(support=support)
        )
        self.mount_attention_session_section = (
            _AttentionMountSessionSectionCapabilityHandler(support=support)
        )
        self.describe_attention_session = _AttentionDescribeSessionCapabilityHandler(
            support=support
        )
        self.apply_session_layout_transition = (
            _AttentionApplySessionLayoutTransitionCapabilityHandler(support=support)
        )
        self.apply_session_layout_topology_transition = (
            _AttentionApplySessionLayoutTopologyTransitionCapabilityHandler(
                support=support
            )
        )
        self.describe_attention_transition = (
            _AttentionDescribeTransitionCapabilityHandler(support=support)
        )
        self.list_attention_transitions = _AttentionListTransitionsCapabilityHandler(
            support=support
        )
        self.validate_attention_transition = (
            _AttentionValidateTransitionCapabilityHandler(support=support)
        )
        self.get_runtime_mount = _AttentionGetRuntimeMountCapabilityHandler(
            support=support
        )
        self.watch_runtime_mount = _AttentionWatchRuntimeMountCapabilityHandler(
            support=support
        )


class _AwareAttentionServiceProtocolHandler:
    def __init__(self, *, identity_api_client: Any | None = None) -> None:
        support = _AttentionProtocolSupport(
            identity_api_client=identity_api_client,
        )
        self._support = support
        self.attention = _AttentionApiServiceProtocolHandler(support=support)
        self._environment_fanout_task: (
            asyncio.Task[tuple[AttentionEnvironmentFocusAttachOutcome, ...]] | None
        ) = None

    async def start_service_host(
        self,
        *,
        environment_api_client: EnvironmentCommitReceiptSdkClient | None = None,
        environment_focus_binding: AttentionEnvironmentFocusBinding | None = None,
    ) -> None:
        if environment_api_client is None:
            logger.warning(
                "Attention service hosted without Environment receipt fanout "
                "client; focus attachment from Environment commits is inactive."
            )
            return
        if environment_focus_binding is None:
            logger.info(
                "Attention Environment fanout using committed focus resolver; "
                "no static section/observable focus binding was supplied."
            )
        task = self._environment_fanout_task
        if task is not None and not task.done():
            return
        consumer = AttentionEnvironmentFanoutFocusConsumer(
            source=EnvironmentSdkCommitReceiptSource(client=environment_api_client),
            authority=_AttentionProtocolActivationAuthority(
                handler=self.attention.activate_section_observable,
            ),
            binding=environment_focus_binding,
            resolver=(
                None
                if environment_focus_binding is not None
                else _AttentionCommittedFocusResolver(support=self._support)
            ),
        )
        self._environment_fanout_task = asyncio.create_task(
            consumer.run(),
            name="attention-servicehost-environment-fanout-focus",
        )
        self._environment_fanout_task.add_done_callback(
            self._on_environment_fanout_done
        )

    async def close_service_host(self) -> None:
        task = self._environment_fanout_task
        self._environment_fanout_task = None
        if task is None or task.done():
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            return
        except Exception as exc:
            logger.warning("Attention Environment fanout close failed: %s", exc)

    def _on_environment_fanout_done(
        self,
        task: asyncio.Task[tuple[AttentionEnvironmentFocusAttachOutcome, ...]],
    ) -> None:
        if task.cancelled():
            return
        try:
            task.result()
        except Exception as exc:
            logger.warning("Attention Environment fanout stopped: %s", exc)


@dataclass(frozen=True, slots=True)
class _AttentionCommittedFocusResolver(AttentionEnvironmentFocusResolver):
    support: _AttentionProtocolSupport

    async def resolve_focus_routes(
        self,
        *,
        receipt: LaneCommitReceiptNotification,
    ) -> tuple[AttentionEnvironmentFocusRoute, ...]:
        runtime_context = await self.support.runtime_context()
        return await _resolve_environment_receipt_focus_routes_from_replica(
            runtime_context=runtime_context,
            receipt=receipt,
        )


def _resolve_attention_runtime_context(
    *,
    runtime_index: MetaGraphRuntimeIndex,
    graph_gateway: ServiceGraphGateway,
) -> _AttentionRuntimeContext:
    section_opg = _require_named_projection(runtime_index=runtime_index, name="Section")
    focus_opg = _require_named_projection(runtime_index=runtime_index, name="Focus")
    focus_scope_opg = _require_named_projection(
        runtime_index=runtime_index,
        name=_FOCUS_SCOPE_PROJECTION_NAME,
    )
    layout_opg = _require_named_projection(
        runtime_index=runtime_index,
        name="Layout",
    )
    attention_session_opg = _require_named_projection(
        runtime_index=runtime_index,
        name="AttentionSession",
    )
    section_class = _require_class_config(
        runtime_index=runtime_index,
        class_fqn="aware_attention_ontology.section.section.Section",
    )
    focus_class = _require_class_config(
        runtime_index=runtime_index,
        class_fqn="aware_attention_ontology.focus.focus.Focus",
    )
    focus_scope_class = _require_class_config(
        runtime_index=runtime_index,
        class_fqn="aware_attention_ontology.focus.focus_scope.FocusScope",
    )
    section_focus_scope_class = _require_class_config(
        runtime_index=runtime_index,
        class_fqn="aware_attention_ontology.section.section_focus_scope.SectionFocusScope",
    )
    attention_session_class = _require_class_config(
        runtime_index=runtime_index,
        class_fqn=(
            "aware_attention_ontology.session.attention_session.AttentionSession"
        ),
    )
    attention_session_layout_class = _require_class_config(
        runtime_index=runtime_index,
        class_fqn=(
            "aware_attention_ontology.session.attention_session_layout."
            "AttentionSessionLayout"
        ),
    )
    return _AttentionRuntimeContext(
        graph_gateway=graph_gateway,
        runtime_index=runtime_index,
        section_opg_id=section_opg.id,
        section_projection_hash=_require_projection_hash(section_opg, label="Section"),
        section_class_config_id=section_class.id,
        section_focus_scope_class_config_id=section_focus_scope_class.id,
        focus_opg_id=focus_opg.id,
        focus_projection_hash=_require_projection_hash(focus_opg, label="Focus"),
        focus_class_config_id=focus_class.id,
        focus_scope_opg_id=focus_scope_opg.id,
        focus_scope_projection_hash=_require_projection_hash(
            focus_scope_opg,
            label=_FOCUS_SCOPE_PROJECTION_NAME,
        ),
        focus_scope_class_config_id=focus_scope_class.id,
        layout_projection_hash=_require_projection_hash(
            layout_opg,
            label="Layout",
        ),
        attention_session_projection_hash=_require_projection_hash(
            attention_session_opg,
            label="AttentionSession",
        ),
        attention_session_opg_id=attention_session_opg.id,
        attention_session_build_function_id=_require_function_id(
            attention_session_class,
            name="build",
        ),
        attention_session_mount_layout_function_id=_require_function_id(
            attention_session_class,
            name="mount_layout",
        ),
        attention_session_layout_attach_section_function_id=_require_function_id(
            attention_session_layout_class,
            name="attach_section",
        ),
        section_build_function_id=_require_function_id(section_class, name="build"),
        section_add_focus_scope_function_id=_require_function_id(
            section_class,
            name="add_focus_scope",
        ),
        section_set_active_focus_scope_function_id=_require_function_id(
            section_class,
            name="set_active_focus_scope",
        ),
        focus_build_function_id=_require_function_id(focus_class, name="build"),
        focus_scope_set_focus_function_id=_require_function_id(
            focus_scope_class,
            name="set_focus",
        ),
        focus_scope_build_function_id=_require_function_id(
            focus_scope_class,
            name="build",
        ),
        focus_scope_set_observable_function_id=_require_function_id(
            focus_scope_class,
            name="set_observable",
        ),
        focus_scope_ensure_commit_function_id=_require_function_id(
            focus_scope_class,
            name="ensure_commit",
        ),
        attention_session_layout_apply_transition_function_id=_require_function_id(
            attention_session_layout_class,
            name="apply_layout_transition",
        ),
        attention_session_layout_apply_topology_transition_function_id=(
            _require_function_id(
                attention_session_layout_class,
                name="apply_topology_transition",
            )
        ),
    )


def _runtime_mount_signature(runtime_mount: object) -> str:
    payload = runtime_mount
    if isinstance(runtime_mount, BaseModel):
        payload = runtime_mount.model_dump(mode="json", exclude_none=True)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _runtime_mount_request_from_watch_request(
    request: CanonicalWatchAttentionRuntimeMountRequest,
) -> CanonicalGetAttentionRuntimeMountRequest:
    return CanonicalGetAttentionRuntimeMountRequest(
        window_key=request.window_key,
        environment_target=request.environment_target,
        attention_session_id=request.attention_session_id,
        preferred_layout_config_id=request.preferred_layout_config_id,
        preferred_layout_key=request.preferred_layout_key,
        preferred_section_key=request.preferred_section_key,
        preferred_observable_id=request.preferred_observable_id,
        layouts=request.layouts,
    )


async def _activate_section_observable(
    *,
    runtime_context: _AttentionRuntimeContext,
    operation_context: ServiceOperationContext,
    request: CanonicalActivateAttentionSectionObservableRequest,
) -> AttentionSectionSnapshot:
    section_key = request.section_key.strip()
    if not section_key:
        raise ValueError("section_key is required")
    section_id = stable_section_id(key=section_key)
    section_title = (request.section_title or "").strip() or _labelize_key(section_key)
    focus_scope_title = (
        request.focus_scope_title or ""
    ).strip() or f"{section_title} focus"
    focus_scope_description = _normalize_optional_text(request.focus_scope_description)

    current_snapshot = await _read_section_snapshot(
        runtime_context=runtime_context,
        section_key=section_key,
    )
    if not current_snapshot.exists:
        await _invoke_constructor(
            runtime_context=runtime_context,
            operation_context=operation_context,
            branch_id=section_id,
            projection_hash=runtime_context.section_projection_hash,
            object_projection_graph_id=runtime_context.section_opg_id,
            function_id=runtime_context.section_build_function_id,
            kwargs={
                "key": section_key,
                "title": section_title,
                "description": _normalize_optional_text(request.section_description),
            },
        )

    refreshed_snapshot = await _read_section_snapshot(
        runtime_context=runtime_context,
        section_key=section_key,
    )
    scoped_focus_scope_id = _activation_scope_focus_scope_id(request.activation_scope)
    focus_scope_id = (
        scoped_focus_scope_id
        or refreshed_snapshot.focus_scope_id
        or _service_focus_scope_id_for_section(section_id=section_id)
    )
    if refreshed_snapshot.focus_scope_id != focus_scope_id:
        existing_focus_scope = await _load_focus_scope(
            runtime_context=runtime_context,
            focus_scope_id=focus_scope_id,
        )
        if existing_focus_scope is None:
            await _invoke_constructor(
                runtime_context=runtime_context,
                operation_context=operation_context,
                branch_id=focus_scope_id,
                projection_hash=runtime_context.focus_scope_projection_hash,
                object_projection_graph_id=runtime_context.focus_scope_opg_id,
                function_id=runtime_context.focus_scope_build_function_id,
                kwargs={
                    "title": focus_scope_title,
                    "description": focus_scope_description,
                    "expires_at": None,
                    "is_active": True,
                    "last_accessed": _utc_now_iso(),
                },
            )
        await _invoke_instance(
            runtime_context=runtime_context,
            operation_context=operation_context,
            branch_id=section_id,
            projection_hash=runtime_context.section_projection_hash,
            object_id=section_id,
            function_id=runtime_context.section_add_focus_scope_function_id,
            kwargs={
                "focus_scope_id": focus_scope_id,
                "title": focus_scope_title,
                "description": focus_scope_description,
            },
        )
        await _invoke_instance(
            runtime_context=runtime_context,
            operation_context=operation_context,
            branch_id=section_id,
            projection_hash=runtime_context.section_projection_hash,
            object_id=section_id,
            function_id=runtime_context.section_set_active_focus_scope_function_id,
            kwargs={"focus_scope_id": focus_scope_id},
        )
    await _invoke_instance(
        runtime_context=runtime_context,
        operation_context=operation_context,
        branch_id=focus_scope_id,
        projection_hash=runtime_context.focus_scope_projection_hash,
        object_id=focus_scope_id,
        function_id=runtime_context.focus_scope_set_observable_function_id,
        kwargs={
            "observable_id": request.observable_id,
            "rationale": _normalize_optional_text(request.rationale),
        },
    )
    await _ensure_focus_target(
        runtime_context=runtime_context,
        operation_context=operation_context,
        focus_scope_id=focus_scope_id,
        focus_target=_activation_scope_focus_target(request.activation_scope),
        rationale=_normalize_optional_text(request.rationale),
    )
    _notify_runtime_mount_changed()
    return await _read_section_snapshot(
        runtime_context=runtime_context,
        section_key=section_key,
    )


async def _get_section_state(
    *,
    runtime_context: _AttentionRuntimeContext,
    operation_context: ServiceOperationContext,
    request: CanonicalGetAttentionSectionStateRequest,
) -> AttentionSectionSnapshot:
    snapshot = await _read_section_snapshot(
        runtime_context=runtime_context,
        section_key=request.section_key,
    )
    if snapshot.observable_id is not None or request.default_observable_id is None:
        return snapshot
    return await _activate_section_observable(
        runtime_context=runtime_context,
        operation_context=operation_context,
        request=CanonicalActivateAttentionSectionObservableRequest(
            section_key=request.section_key,
            observable_id=request.default_observable_id,
            rationale=(
                _normalize_optional_text(request.default_rationale)
                or "attention_default_section_observable"
            ),
        ),
    )


async def _get_focus_scope_commits(
    *,
    runtime_context: _AttentionRuntimeContext,
    request: CanonicalGetAttentionFocusScopeCommitsRequest,
) -> GetAttentionFocusScopeCommitsResponse:
    limit = request.limit
    if limit is not None and limit < 0:
        raise ValueError("limit must be greater than or equal to 0")

    focus_scope = await _load_focus_scope(
        runtime_context=runtime_context,
        focus_scope_id=request.focus_scope_id,
    )
    if focus_scope is None:
        return GetAttentionFocusScopeCommitsResponse(
            focus_scope_id=request.focus_scope_id,
            exists=False,
            commits=[],
        )

    commits: list[AttentionFocusScopeCommitPin] = []
    for focus_scope_commit in focus_scope.commits:
        pin = _focus_scope_commit_pin(focus_scope_commit)
        if request.focus_id is not None and pin.focus_id != request.focus_id:
            continue
        if (
            request.object_instance_graph_commit_id is not None
            and pin.object_instance_graph_commit_id
            != request.object_instance_graph_commit_id
        ):
            continue
        commits.append(pin)
        if limit is not None and len(commits) >= limit:
            break

    return GetAttentionFocusScopeCommitsResponse(
        focus_scope_id=request.focus_scope_id,
        exists=True,
        commits=commits,
    )


@dataclass(frozen=True, slots=True)
class _AttentionSessionLaneSnapshot:
    session: AttentionSession
    head: JsonObject


async def _load_attention_session_lane_snapshot(
    *,
    runtime_context: _AttentionRuntimeContext,
    attention_session_id: UUID,
) -> _AttentionSessionLaneSnapshot | None:
    loaded = await _load_projection_root_model_with_head(
        runtime_context=runtime_context,
        branch_id=attention_session_id,
        projection_hash=runtime_context.attention_session_projection_hash,
        root_id=attention_session_id,
        model_type=AttentionSession,
    )
    if loaded is None:
        return None
    session, head = loaded
    return _AttentionSessionLaneSnapshot(session=session, head=head)


def _select_runtime_session_layout(
    *,
    session: AttentionSession,
    attention_session_layout_id: UUID | None = None,
    layout_id: UUID | None = None,
    layout_config_id: UUID | None = None,
    layout_key: str | None = None,
) -> Any | None:
    layouts = list(session.layouts)
    if attention_session_layout_id is not None:
        return next(
            (
                layout
                for layout in layouts
                if _row_id(layout) == attention_session_layout_id
            ),
            None,
        )
    if layout_id is not None:
        matches = [
            layout
            for layout in layouts
            if getattr(layout, "layout_id", None) == layout_id
        ]
        if len(matches) == 1:
            return matches[0]
    if layout_config_id is not None:
        matches = [
            layout
            for layout in layouts
            if getattr(layout, "layout_config_id", None) == layout_config_id
        ]
        if len(matches) == 1:
            return matches[0]
    normalized_layout_key = _normalize_optional_text(layout_key)
    if normalized_layout_key is not None:
        matches = [
            layout
            for layout in layouts
            if _normalize_optional_text(getattr(layout, "key", None))
            == normalized_layout_key
        ]
        if len(matches) == 1:
            return matches[0]
    active_layout = getattr(session, "active_layout", None)
    if active_layout is not None:
        return active_layout
    active_layout_id = getattr(session, "active_layout_id", None)
    if active_layout_id is not None:
        for layout in layouts:
            if _row_id(layout) == active_layout_id:
                return layout
    active_layouts = [
        layout for layout in layouts if bool(getattr(layout, "is_active", False))
    ]
    if len(active_layouts) == 1:
        return active_layouts[0]
    return layouts[0] if len(layouts) == 1 else None


def _active_layout_topology_transition(layout: Any | None) -> Any | None:
    if layout is None:
        return None
    active_transition = getattr(layout, "active_topology_transition", None)
    if active_transition is not None:
        return active_transition
    active_transition_id = getattr(layout, "active_topology_transition_id", None)
    if active_transition_id is None:
        return None
    return next(
        (
            transition
            for transition in getattr(layout, "topology_transitions", []) or []
            if _row_id(transition) == active_transition_id
        ),
        None,
    )


def _active_layout_topology_transition_pin(
    *,
    layout: Any | None,
    head: JsonObject,
) -> AttentionLayoutTopologyTransitionPin | None:
    transition = _active_layout_topology_transition(layout)
    if transition is None or layout is None:
        return None
    return _runtime_layout_topology_transition_pin(
        layout=layout,
        transition=transition,
        head=head,
    )


def _runtime_layout_topology_transition_pin(
    *,
    layout: Any,
    transition: Any,
    head: JsonObject,
    object_instance_graph_commit_id: UUID | None = None,
    graph_hash_post: str | None = None,
) -> AttentionLayoutTopologyTransitionPin:
    session_sections = {
        _row_id(section): section for section in getattr(layout, "sections", []) or []
    }
    section_states: list[AttentionLayoutTopologyTransitionSectionState] = []
    for state in sorted(
        getattr(transition, "section_states", []) or [],
        key=lambda item: (int(getattr(item, "order", 0) or 0), str(_row_id(item))),
    ):
        attention_session_section_id = cast(
            UUID | None,
            getattr(state, "attention_session_section_id", None),
        )
        if attention_session_section_id is None:
            raise RuntimeError(
                "Committed Attention layout topology state is missing "
                "attention_session_section_id."
            )
        session_section = session_sections.get(attention_session_section_id)
        section_states.append(
            ServiceAttentionLayoutTopologyTransitionSectionState(
                attention_layout_topology_transition_section_id=_row_id(state),
                attention_layout_topology_transition_id=_row_id(transition),
                attention_session_section_id=attention_session_section_id,
                layout_section_id=(
                    cast(
                        UUID | None, getattr(session_section, "layout_section_id", None)
                    )
                    if session_section is not None
                    else None
                ),
                section_id=(
                    cast(UUID | None, getattr(session_section, "section_id", None))
                    if session_section is not None
                    else None
                ),
                section_key=(
                    _normalize_optional_text(
                        getattr(session_section, "section_key", None)
                    )
                    if session_section is not None
                    else None
                ),
                order=int(getattr(state, "order", 0) or 0),
            )
        )
    return ServiceAttentionLayoutTopologyTransitionPin(
        attention_layout_topology_transition_id=_row_id(transition),
        attention_session_layout_id=_row_id(layout),
        previous_topology_transition_id=cast(
            UUID | None,
            getattr(transition, "previous_topology_transition_id", None),
        ),
        client_intent_id=str(getattr(transition, "client_intent_id")),
        sequence=int(getattr(transition, "sequence", 0) or 0),
        transition_kind=str(getattr(transition, "transition_kind", "topology")),
        source_kind=_normalize_optional_text(getattr(transition, "source_kind", None)),
        source_ref=_normalize_optional_text(getattr(transition, "source_ref", None)),
        metadata_json=_metadata_json(transition),
        object_instance_graph_commit_id=(
            object_instance_graph_commit_id
            if object_instance_graph_commit_id is not None
            else _head_uuid(head, "object_instance_graph_commit_id")
        ),
        graph_hash_post=(
            graph_hash_post
            if graph_hash_post is not None
            else _normalize_optional_text(cast(str | None, head.get("graph_hash_post")))
        ),
        section_states=section_states,
    )


def _active_layout_transition(layout: Any | None) -> Any | None:
    if layout is None:
        return None
    active_transition = getattr(layout, "active_layout_transition", None)
    if active_transition is not None:
        return active_transition
    active_transition_id = getattr(layout, "active_layout_transition_id", None)
    if active_transition_id is None:
        return None
    return next(
        (
            transition
            for transition in getattr(layout, "layout_transitions", []) or []
            if _row_id(transition) == active_transition_id
        ),
        None,
    )


def _active_layout_transition_pin(
    *,
    layout: Any | None,
    head: JsonObject,
) -> AttentionLayoutTransitionPin | None:
    transition = _active_layout_transition(layout)
    if transition is None or layout is None:
        return None
    return _runtime_layout_transition_pin(
        layout=layout,
        transition=transition,
        head=head,
    )


def _runtime_layout_transition_pin(
    *,
    layout: Any,
    transition: Any,
    head: JsonObject,
    object_instance_graph_commit_id: UUID | None = None,
    graph_hash_post: str | None = None,
) -> AttentionLayoutTransitionPin:
    session_sections = {
        _row_id(section): section for section in getattr(layout, "sections", []) or []
    }
    section_states: list[AttentionLayoutTransitionSectionState] = []
    for state in sorted(
        getattr(transition, "section_states", []) or [],
        key=lambda item: (int(getattr(item, "order", 0) or 0), str(_row_id(item))),
    ):
        attention_session_section_id = cast(
            UUID | None,
            getattr(state, "attention_session_section_id", None),
        )
        if attention_session_section_id is None:
            raise RuntimeError(
                "Committed Attention layout transition state is missing "
                "attention_session_section_id."
            )
        session_section = session_sections.get(attention_session_section_id)
        section_states.append(
            ServiceAttentionLayoutTransitionSectionState(
                attention_layout_transition_section_id=_row_id(state),
                attention_layout_transition_id=_row_id(transition),
                attention_session_section_id=attention_session_section_id,
                layout_section_id=(
                    cast(
                        UUID | None, getattr(session_section, "layout_section_id", None)
                    )
                    if session_section is not None
                    else None
                ),
                section_id=(
                    cast(UUID | None, getattr(session_section, "section_id", None))
                    if session_section is not None
                    else None
                ),
                section_key=(
                    _normalize_optional_text(
                        getattr(session_section, "section_key", None)
                    )
                    if session_section is not None
                    else None
                ),
                order=int(getattr(state, "order", 0) or 0),
                weight_micros=int(getattr(state, "weight_micros", 0) or 0),
                is_visible=bool(getattr(state, "is_visible", True)),
                is_collapsed=bool(getattr(state, "is_collapsed", False)),
            )
        )
    return ServiceAttentionLayoutTransitionPin(
        attention_layout_transition_id=_row_id(transition),
        attention_session_layout_id=_row_id(layout),
        previous_transition_id=cast(
            UUID | None,
            getattr(transition, "previous_transition_id", None),
        ),
        topology_transition_id=cast(
            UUID | None,
            getattr(transition, "topology_transition_id", None),
        ),
        client_intent_id=str(getattr(transition, "client_intent_id")),
        sequence=int(getattr(transition, "sequence", 0) or 0),
        transition_kind=str(getattr(transition, "transition_kind", "layout")),
        source_kind=_normalize_optional_text(getattr(transition, "source_kind", None)),
        source_ref=_normalize_optional_text(getattr(transition, "source_ref", None)),
        metadata_json=_metadata_json(transition),
        object_instance_graph_commit_id=(
            object_instance_graph_commit_id
            if object_instance_graph_commit_id is not None
            else _head_uuid(head, "object_instance_graph_commit_id")
        ),
        graph_hash_post=(
            graph_hash_post
            if graph_hash_post is not None
            else _normalize_optional_text(cast(str | None, head.get("graph_hash_post")))
        ),
        section_states=section_states,
    )


def _head_uuid(head: JsonObject, field_name: str) -> UUID | None:
    raw = head.get(field_name)
    if raw is None:
        return None
    return raw if isinstance(raw, UUID) else UUID(str(raw))


@dataclass(frozen=True, slots=True)
class _AttentionSessionReplicaModels:
    session: type[Any]
    layout: type[Any]
    section: type[Any]
    transition: type[Any]
    layout_transition: type[Any] | None = None
    layout_transition_section: type[Any] | None = None


@dataclass(frozen=True, slots=True)
class _AttentionTransitionChain:
    transition: Any
    section: Any | None
    layout: Any | None
    session: Any | None


def _attention_session_replica_available() -> bool:
    return current_service_ontology_replica_orm_session() is not None


def _attention_session_replica_models() -> _AttentionSessionReplicaModels:
    try:
        from aware_attention_ontology_orm_models.session.attention_layout_transition import (
            AttentionLayoutTransition as AttentionLayoutTransitionOrmModel,
        )
        from aware_attention_ontology_orm_models.session.attention_layout_transition_section import (
            AttentionLayoutTransitionSection as AttentionLayoutTransitionSectionOrmModel,
        )
        from aware_attention_ontology_orm_models.session.attention_focus_transition import (
            AttentionFocusTransition as AttentionFocusTransitionOrmModel,
        )
        from aware_attention_ontology_orm_models.session.attention_session import (
            AttentionSession as AttentionSessionOrmModel,
        )
        from aware_attention_ontology_orm_models.session.attention_session_layout import (
            AttentionSessionLayout as AttentionSessionLayoutOrmModel,
        )
        from aware_attention_ontology_orm_models.session.attention_session_section import (
            AttentionSessionSection as AttentionSessionSectionOrmModel,
        )
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Attention session transition reads require the generated Attention "
            "ontology ORM model package to be importable. ServiceHost startup "
            "must expose the required ontology ORM package closure."
        ) from exc

    return _AttentionSessionReplicaModels(
        session=AttentionSessionOrmModel,
        layout=AttentionSessionLayoutOrmModel,
        section=AttentionSessionSectionOrmModel,
        transition=AttentionFocusTransitionOrmModel,
        layout_transition=AttentionLayoutTransitionOrmModel,
        layout_transition_section=AttentionLayoutTransitionSectionOrmModel,
    )


async def _describe_attention_session(
    *,
    request: CanonicalDescribeAttentionSessionRequest,
) -> DescribeAttentionSessionResponse:
    if request.attention_session_id is None and request.identity_session_id is None:
        raise ValueError("attention_session_id or identity_session_id is required.")
    if not _attention_session_replica_available():
        return DescribeAttentionSessionResponse(
            request_id=_request_id(request),
            session=None,
            layouts=[],
            info="missing_attention_ontology_replica",
        )

    models = _attention_session_replica_models()
    session = await _load_attention_session_for_request(
        models=models,
        attention_session_id=request.attention_session_id,
        identity_session_id=request.identity_session_id,
    )
    if session is None:
        return DescribeAttentionSessionResponse(
            request_id=_request_id(request),
            session=None,
            layouts=[],
            info="attention_session_not_found",
        )

    layouts = _sort_layouts(
        await models.layout.many(attention_session_id=_row_id(session))
    )
    active_layout = _select_active_layout(session=session, layouts=layouts)
    active_section = (
        await _select_active_section(models=models, layout=active_layout)
        if active_layout is not None
        else None
    )
    active_transition = (
        await _select_active_transition(models=models, section=active_section)
        if active_section is not None
        else None
    )

    return DescribeAttentionSessionResponse(
        request_id=_request_id(request),
        session=_attention_session_pin(session),
        layouts=[_attention_session_layout_pin(layout) for layout in layouts],
        active_layout=(
            _attention_session_layout_pin(active_layout)
            if active_layout is not None
            else None
        ),
        active_section=(
            _attention_session_section_pin(active_section)
            if active_section is not None
            else None
        ),
        active_transition=(
            await _attention_transition_pin_for_transition(
                models=models,
                transition=active_transition,
            )
            if active_transition is not None
            else None
        ),
    )


async def _apply_session_layout_topology_transition(
    *,
    runtime_context: _AttentionRuntimeContext,
    operation_context: ServiceOperationContext,
    request: CanonicalApplyAttentionSessionLayoutTopologyTransitionRequest,
) -> ApplyAttentionSessionLayoutTopologyTransitionResponse:
    normalized_intent_id = (request.client_intent_id or "").strip().casefold()
    if not normalized_intent_id:
        raise ValueError("client_intent_id is required")
    if not request.section_states:
        raise ValueError(
            "section_states must contain the complete active topology vector"
        )

    initial = await _load_attention_session_lane_snapshot(
        runtime_context=runtime_context,
        attention_session_id=request.attention_session_id,
    )
    if initial is None:
        raise ValueError(
            "AttentionSession lane not found: "
            f"attention_session_id={request.attention_session_id}"
        )
    layout = _select_runtime_session_layout(
        session=initial.session,
        attention_session_layout_id=request.attention_session_layout_id,
    )
    if layout is None:
        raise ValueError(
            "AttentionSessionLayout is not mounted by the requested AttentionSession: "
            f"attention_session_layout_id={request.attention_session_layout_id}"
        )

    latest_before = _active_layout_topology_transition_pin(
        layout=layout,
        head=initial.head,
    )
    latest_before_id = (
        latest_before.attention_layout_topology_transition_id
        if latest_before is not None
        else None
    )
    is_active_intent_retry = (
        latest_before is not None
        and latest_before.client_intent_id.strip().casefold() == normalized_intent_id
    )
    if (
        not is_active_intent_retry
        and request.expected_previous_topology_transition_id != latest_before_id
    ):
        return _layout_topology_transition_conflict_response(
            request=request,
            reason="stale_previous_topology_transition",
            latest_transition=latest_before,
        )

    section_states_json = JsonObject(
        {
            "sections": [
                {
                    "attention_session_section_id": str(
                        state.attention_session_section_id
                    ),
                    "order": state.order,
                }
                for state in request.section_states
            ]
        }
    )
    invoke_response = await _invoke_instance(
        runtime_context=runtime_context,
        operation_context=operation_context,
        branch_id=request.attention_session_id,
        projection_hash=runtime_context.attention_session_projection_hash,
        object_id=request.attention_session_layout_id,
        function_id=(
            runtime_context.attention_session_layout_apply_topology_transition_function_id
        ),
        kwargs={
            "client_intent_id": normalized_intent_id,
            "section_states_json": section_states_json,
            "expected_previous_topology_transition_id": (
                request.expected_previous_topology_transition_id
            ),
            "transition_kind": request.transition_kind,
            "source_kind": request.source_kind,
            "source_ref": request.source_ref,
            "metadata_json": JsonObject(request.metadata_json or {}),
        },
        expected_graph_hash_pre=_normalize_optional_text(
            cast(str | None, initial.head.get("graph_hash_post"))
        ),
        expected_head_commit_id=_head_uuid(initial.head, "commit_id"),
        ensure_succeeded=False,
    )
    if (invoke_response.status or "").strip().casefold() != "succeeded":
        if _is_layout_topology_transition_conflict_error(invoke_response.error):
            latest = await _latest_layout_topology_transition_pin(
                runtime_context=runtime_context,
                attention_session_id=request.attention_session_id,
                attention_session_layout_id=request.attention_session_layout_id,
            )
            return _layout_topology_transition_conflict_response(
                request=request,
                reason=_layout_topology_transition_conflict_reason(
                    invoke_response.error
                ),
                latest_transition=latest,
                detail=invoke_response.error,
            )
        _ensure_invoke_succeeded(response=invoke_response)

    refreshed = await _load_attention_session_lane_snapshot(
        runtime_context=runtime_context,
        attention_session_id=request.attention_session_id,
    )
    if refreshed is None:
        raise RuntimeError("Committed AttentionSession lane could not be read back")
    refreshed_layout = _select_runtime_session_layout(
        session=refreshed.session,
        attention_session_layout_id=request.attention_session_layout_id,
    )
    if refreshed_layout is None:
        raise RuntimeError("Committed AttentionSessionLayout could not be read back")
    transition_id = stable_attention_layout_topology_transition_id(
        attention_session_layout_id=request.attention_session_layout_id,
        client_intent_id=normalized_intent_id,
    )
    committed_transition = next(
        (
            transition
            for transition in refreshed_layout.topology_transitions
            if _row_id(transition) == transition_id
        ),
        None,
    )
    if committed_transition is None:
        raise RuntimeError(
            "Attention layout topology transition invocation succeeded but the "
            f"committed transition was not readable: transition_id={transition_id}"
        )
    outcome = "idempotent" if invoke_response.domain_commit_id is None else "committed"
    transition_pin = _runtime_layout_topology_transition_pin(
        layout=refreshed_layout,
        transition=committed_transition,
        head=refreshed.head,
        object_instance_graph_commit_id=invoke_response.object_instance_graph_commit_id,
        graph_hash_post=_normalize_optional_text(invoke_response.graph_hash_post),
    )
    latest_transition = _active_layout_topology_transition_pin(
        layout=refreshed_layout,
        head=refreshed.head,
    )
    if outcome == "committed":
        _notify_runtime_mount_changed()
    return ApplyAttentionSessionLayoutTopologyTransitionResponse(
        request_id=_request_id(request),
        success=True,
        outcome=outcome,
        transition=transition_pin,
        latest_transition=latest_transition,
    )


async def _latest_layout_topology_transition_pin(
    *,
    runtime_context: _AttentionRuntimeContext,
    attention_session_id: UUID,
    attention_session_layout_id: UUID,
) -> AttentionLayoutTopologyTransitionPin | None:
    snapshot = await _load_attention_session_lane_snapshot(
        runtime_context=runtime_context,
        attention_session_id=attention_session_id,
    )
    if snapshot is None:
        return None
    layout = _select_runtime_session_layout(
        session=snapshot.session,
        attention_session_layout_id=attention_session_layout_id,
    )
    return _active_layout_topology_transition_pin(layout=layout, head=snapshot.head)


def _layout_topology_transition_conflict_response(
    *,
    request: CanonicalApplyAttentionSessionLayoutTopologyTransitionRequest,
    reason: str,
    latest_transition: AttentionLayoutTopologyTransitionPin | None,
    detail: str | None = None,
) -> ApplyAttentionSessionLayoutTopologyTransitionResponse:
    return ApplyAttentionSessionLayoutTopologyTransitionResponse(
        request_id=_request_id(request),
        success=False,
        info="layout_topology_transition_conflict",
        error=detail or reason,
        outcome="conflict",
        conflict_reason=reason,
        transition=None,
        latest_transition=latest_transition,
    )


def _is_layout_topology_transition_conflict_error(error: str | None) -> bool:
    normalized = (error or "").casefold()
    return any(
        token in normalized
        for token in (
            "stale expected previous topology transition id",
            "client_intent_id collides",
            "client_intent_id already identifies",
            "expected_head_commit_id",
            "expected head commit",
            "expected_graph_hash_pre",
            "graph hash pre",
            "pre-state graph hash mismatch",
            "head changed",
            "head mismatch",
            "pre-state head commit mismatch",
        )
    )


def _layout_topology_transition_conflict_reason(error: str | None) -> str:
    normalized = (error or "").casefold()
    if "client_intent_id" in normalized:
        return "client_intent_collision"
    if "stale expected previous topology transition id" in normalized:
        return "stale_previous_topology_transition"
    return "lane_head_changed"


async def _apply_session_layout_transition(
    *,
    runtime_context: _AttentionRuntimeContext,
    operation_context: ServiceOperationContext,
    request: CanonicalApplyAttentionSessionLayoutTransitionRequest,
) -> ApplyAttentionSessionLayoutTransitionResponse:
    normalized_intent_id = (request.client_intent_id or "").strip().casefold()
    if not normalized_intent_id:
        raise ValueError("client_intent_id is required")
    if not request.section_states:
        raise ValueError(
            "section_states must contain the complete mounted section vector"
        )

    initial = await _load_attention_session_lane_snapshot(
        runtime_context=runtime_context,
        attention_session_id=request.attention_session_id,
    )
    if initial is None:
        raise ValueError(
            "AttentionSession lane not found: "
            f"attention_session_id={request.attention_session_id}"
        )
    layout = _select_runtime_session_layout(
        session=initial.session,
        attention_session_layout_id=request.attention_session_layout_id,
    )
    if layout is None:
        raise ValueError(
            "AttentionSessionLayout is not mounted by the requested AttentionSession: "
            f"attention_session_layout_id={request.attention_session_layout_id}"
        )

    latest_topology_before = _active_layout_topology_transition_pin(
        layout=layout,
        head=initial.head,
    )
    latest_topology_before_id = (
        latest_topology_before.attention_layout_topology_transition_id
        if latest_topology_before is not None
        else None
    )
    if request.topology_transition_id != latest_topology_before_id:
        return _layout_transition_conflict_response(
            request=request,
            reason="stale_topology_transition",
            latest_transition=_active_layout_transition_pin(
                layout=layout,
                head=initial.head,
            ),
            latest_topology_transition=latest_topology_before,
        )

    latest_before = _active_layout_transition_pin(
        layout=layout,
        head=initial.head,
    )
    latest_before_id = (
        latest_before.attention_layout_transition_id
        if latest_before is not None
        else None
    )
    is_active_intent_retry = (
        latest_before is not None
        and latest_before.client_intent_id.strip().casefold() == normalized_intent_id
    )
    if (
        not is_active_intent_retry
        and request.expected_previous_layout_transition_id != latest_before_id
    ):
        return _layout_transition_conflict_response(
            request=request,
            reason="stale_previous_transition",
            latest_transition=latest_before,
            latest_topology_transition=latest_topology_before,
        )

    section_states_json = JsonObject(
        {
            "sections": [
                {
                    "attention_session_section_id": str(
                        state.attention_session_section_id
                    ),
                    "order": state.order,
                    "weight_micros": state.weight_micros,
                    "is_visible": state.is_visible,
                    "is_collapsed": state.is_collapsed,
                }
                for state in request.section_states
            ]
        }
    )
    invoke_response = await _invoke_instance(
        runtime_context=runtime_context,
        operation_context=operation_context,
        branch_id=request.attention_session_id,
        projection_hash=runtime_context.attention_session_projection_hash,
        object_id=request.attention_session_layout_id,
        function_id=(
            runtime_context.attention_session_layout_apply_transition_function_id
        ),
        kwargs={
            "client_intent_id": normalized_intent_id,
            "section_states_json": section_states_json,
            "expected_previous_layout_transition_id": (
                request.expected_previous_layout_transition_id
            ),
            "topology_transition_id": request.topology_transition_id,
            "transition_kind": request.transition_kind,
            "source_kind": request.source_kind,
            "source_ref": request.source_ref,
            "metadata_json": JsonObject(request.metadata_json or {}),
        },
        expected_graph_hash_pre=_normalize_optional_text(
            cast(str | None, initial.head.get("graph_hash_post"))
        ),
        expected_head_commit_id=_head_uuid(initial.head, "commit_id"),
        ensure_succeeded=False,
    )
    if (invoke_response.status or "").strip().casefold() != "succeeded":
        if _is_layout_transition_conflict_error(invoke_response.error):
            latest = await _latest_layout_transition_pin(
                runtime_context=runtime_context,
                attention_session_id=request.attention_session_id,
                attention_session_layout_id=request.attention_session_layout_id,
            )
            latest_topology = await _latest_layout_topology_transition_pin(
                runtime_context=runtime_context,
                attention_session_id=request.attention_session_id,
                attention_session_layout_id=request.attention_session_layout_id,
            )
            return _layout_transition_conflict_response(
                request=request,
                reason=_layout_transition_conflict_reason(invoke_response.error),
                latest_transition=latest,
                latest_topology_transition=latest_topology,
                detail=invoke_response.error,
            )
        _ensure_invoke_succeeded(response=invoke_response)

    refreshed = await _load_attention_session_lane_snapshot(
        runtime_context=runtime_context,
        attention_session_id=request.attention_session_id,
    )
    if refreshed is None:
        raise RuntimeError("Committed AttentionSession lane could not be read back")
    refreshed_layout = _select_runtime_session_layout(
        session=refreshed.session,
        attention_session_layout_id=request.attention_session_layout_id,
    )
    if refreshed_layout is None:
        raise RuntimeError("Committed AttentionSessionLayout could not be read back")
    transition_id = stable_attention_layout_transition_id(
        attention_session_layout_id=request.attention_session_layout_id,
        client_intent_id=normalized_intent_id,
    )
    committed_transition = next(
        (
            transition
            for transition in refreshed_layout.layout_transitions
            if _row_id(transition) == transition_id
        ),
        None,
    )
    if committed_transition is None:
        raise RuntimeError(
            "Attention layout transition invocation succeeded but the committed "
            f"transition was not readable: transition_id={transition_id}"
        )
    outcome = "idempotent" if invoke_response.domain_commit_id is None else "committed"
    transition_pin = _runtime_layout_transition_pin(
        layout=refreshed_layout,
        transition=committed_transition,
        head=refreshed.head,
        object_instance_graph_commit_id=invoke_response.object_instance_graph_commit_id,
        graph_hash_post=_normalize_optional_text(invoke_response.graph_hash_post),
    )
    latest_transition = _active_layout_transition_pin(
        layout=refreshed_layout,
        head=refreshed.head,
    )
    latest_topology_transition = _active_layout_topology_transition_pin(
        layout=refreshed_layout,
        head=refreshed.head,
    )
    if outcome == "committed":
        _notify_runtime_mount_changed()
    return ApplyAttentionSessionLayoutTransitionResponse(
        request_id=_request_id(request),
        success=True,
        outcome=outcome,
        transition=transition_pin,
        latest_transition=latest_transition,
        latest_topology_transition=latest_topology_transition,
    )


async def _latest_layout_transition_pin(
    *,
    runtime_context: _AttentionRuntimeContext,
    attention_session_id: UUID,
    attention_session_layout_id: UUID,
) -> AttentionLayoutTransitionPin | None:
    snapshot = await _load_attention_session_lane_snapshot(
        runtime_context=runtime_context,
        attention_session_id=attention_session_id,
    )
    if snapshot is None:
        return None
    layout = _select_runtime_session_layout(
        session=snapshot.session,
        attention_session_layout_id=attention_session_layout_id,
    )
    return _active_layout_transition_pin(layout=layout, head=snapshot.head)


def _layout_transition_conflict_response(
    *,
    request: CanonicalApplyAttentionSessionLayoutTransitionRequest,
    reason: str,
    latest_transition: AttentionLayoutTransitionPin | None,
    latest_topology_transition: AttentionLayoutTopologyTransitionPin | None = None,
    detail: str | None = None,
) -> ApplyAttentionSessionLayoutTransitionResponse:
    return ApplyAttentionSessionLayoutTransitionResponse(
        request_id=_request_id(request),
        success=False,
        info="layout_transition_conflict",
        error=detail or reason,
        outcome="conflict",
        conflict_reason=reason,
        transition=None,
        latest_transition=latest_transition,
        latest_topology_transition=latest_topology_transition,
    )


def _is_layout_transition_conflict_error(error: str | None) -> bool:
    normalized = (error or "").casefold()
    return any(
        token in normalized
        for token in (
            "stale expected previous transition id",
            "topology_transition_id must exactly pin the active topology",
            "client_intent_id collides",
            "client_intent_id already identifies",
            "expected_head_commit_id",
            "expected head commit",
            "expected_graph_hash_pre",
            "graph hash pre",
            "pre-state graph hash mismatch",
            "head changed",
            "head mismatch",
            "pre-state head commit mismatch",
        )
    )


def _layout_transition_conflict_reason(error: str | None) -> str:
    normalized = (error or "").casefold()
    if "client_intent_id" in normalized:
        return "client_intent_collision"
    if "topology_transition_id must exactly pin" in normalized:
        return "stale_topology_transition"
    if "stale expected previous transition id" in normalized:
        return "stale_previous_transition"
    return "lane_head_changed"


async def _describe_attention_transition(
    *,
    request: CanonicalDescribeAttentionTransitionRequest,
) -> DescribeAttentionTransitionResponse:
    if not _attention_session_replica_available():
        return DescribeAttentionTransitionResponse(
            request_id=_request_id(request),
            exists=False,
            transition=None,
            info="missing_attention_ontology_replica",
        )

    models = _attention_session_replica_models()
    transition = await models.transition.by_id(request.attention_focus_transition_id)
    if transition is None:
        return DescribeAttentionTransitionResponse(
            request_id=_request_id(request),
            exists=False,
            transition=None,
            info="attention_transition_not_found",
        )
    return DescribeAttentionTransitionResponse(
        request_id=_request_id(request),
        exists=True,
        transition=await _attention_transition_pin_for_transition(
            models=models,
            transition=transition,
        ),
    )


async def _list_attention_transitions(
    *,
    request: CanonicalListAttentionTransitionsRequest,
) -> ListAttentionTransitionsResponse:
    if request.limit is not None and request.limit < 0:
        raise ValueError("limit must be greater than or equal to 0")
    if not _attention_session_replica_available():
        return ListAttentionTransitionsResponse(
            request_id=_request_id(request),
            transitions=[],
            info="missing_attention_ontology_replica",
        )

    models = _attention_session_replica_models()
    transitions = await _transition_candidates(models=models, request=request)
    pins: list[AttentionFocusTransitionPin] = []
    for transition in _sort_transitions(transitions):
        pin = await _attention_transition_pin_for_transition(
            models=models,
            transition=transition,
        )
        if not _transition_pin_matches_request(pin=pin, request=request):
            continue
        pins.append(pin)
        if request.limit is not None and len(pins) >= request.limit:
            break
    return ListAttentionTransitionsResponse(
        request_id=_request_id(request),
        transitions=pins,
    )


async def _validate_attention_transition(
    *,
    request: CanonicalValidateAttentionTransitionRequest,
) -> AttentionTransitionValidationResult:
    if not _attention_session_replica_available():
        return AttentionTransitionValidationResult(
            exists=False,
            valid=False,
            failure_reasons=["missing_attention_ontology_replica"],
            transition=None,
        )

    models = _attention_session_replica_models()
    transition = await models.transition.by_id(request.attention_focus_transition_id)
    if transition is None:
        return AttentionTransitionValidationResult(
            exists=False,
            valid=False,
            failure_reasons=["attention_transition_not_found"],
            transition=None,
        )

    pin = await _attention_transition_pin_for_transition(
        models=models,
        transition=transition,
    )
    failure_reasons = _transition_validation_failures(
        pin=pin,
        request=request,
    )
    return AttentionTransitionValidationResult(
        exists=True,
        valid=not failure_reasons,
        failure_reasons=failure_reasons,
        transition=pin,
    )


async def _load_attention_session_for_request(
    *,
    models: _AttentionSessionReplicaModels,
    attention_session_id: UUID | None,
    identity_session_id: UUID | None,
) -> Any | None:
    if attention_session_id is not None:
        session = await models.session.by_id(attention_session_id)
        if (
            session is not None
            and identity_session_id is not None
            and getattr(session, "identity_session_id", None) != identity_session_id
        ):
            return None
        return session
    sessions = await models.session.many(identity_session_id=identity_session_id)
    return _sort_sessions(sessions)[0] if sessions else None


async def _transition_candidates(
    *,
    models: _AttentionSessionReplicaModels,
    request: CanonicalListAttentionTransitionsRequest,
) -> list[Any]:
    if (
        request.attention_session_id is not None
        or request.identity_session_id is not None
    ):
        sessions = await _matching_attention_sessions(models=models, request=request)
        transitions: list[Any] = []
        for session in sessions:
            for layout in await models.layout.many(
                attention_session_id=_row_id(session)
            ):
                for section in await models.section.many(
                    attention_session_layout_id=_row_id(layout)
                ):
                    if (
                        request.attention_session_section_id is not None
                        and _row_id(section) != request.attention_session_section_id
                    ):
                        continue
                    if _normalize_optional_text(
                        request.section_key
                    ) is not None and _normalize_optional_text(
                        getattr(section, "section_key", None)
                    ) != _normalize_optional_text(
                        request.section_key
                    ):
                        continue
                    transitions.extend(
                        await models.transition.many(
                            attention_session_section_id=_row_id(section)
                        )
                    )
        return transitions

    if request.attention_session_section_id is not None:
        return list(
            await models.transition.many(
                attention_session_section_id=request.attention_session_section_id
            )
        )

    if _normalize_optional_text(request.section_key) is not None:
        transitions: list[Any] = []
        for section in await models.section.many(section_key=request.section_key):
            transitions.extend(
                await models.transition.many(
                    attention_session_section_id=_row_id(section)
                )
            )
        return transitions

    if request.focus_scope_id is not None:
        return list(await models.transition.many(focus_scope_id=request.focus_scope_id))

    if _normalize_optional_text(request.transition_kind) is not None:
        return list(
            await models.transition.many(
                transition_kind=_normalize_optional_text(request.transition_kind)
            )
        )

    return list(await models.transition.many())


async def _matching_attention_sessions(
    *,
    models: _AttentionSessionReplicaModels,
    request: CanonicalListAttentionTransitionsRequest,
) -> list[Any]:
    if request.attention_session_id is not None:
        session = await models.session.by_id(request.attention_session_id)
        if session is None:
            return []
        if (
            request.identity_session_id is not None
            and getattr(session, "identity_session_id", None)
            != request.identity_session_id
        ):
            return []
        return [session]
    return _sort_sessions(
        await models.session.many(identity_session_id=request.identity_session_id)
    )


async def _attention_transition_pin_for_transition(
    *,
    models: _AttentionSessionReplicaModels,
    transition: Any,
) -> AttentionFocusTransitionPin:
    chain = await _load_transition_chain(models=models, transition=transition)
    return _attention_transition_pin(chain)


async def _load_transition_chain(
    *,
    models: _AttentionSessionReplicaModels,
    transition: Any,
) -> _AttentionTransitionChain:
    section = await models.section.by_id(
        getattr(transition, "attention_session_section_id", None)
    )
    layout = (
        await models.layout.by_id(getattr(section, "attention_session_layout_id", None))
        if section is not None
        else None
    )
    session = (
        await models.session.by_id(getattr(layout, "attention_session_id", None))
        if layout is not None
        else None
    )
    return _AttentionTransitionChain(
        transition=transition,
        section=section,
        layout=layout,
        session=session,
    )


async def _select_active_section(
    *,
    models: _AttentionSessionReplicaModels,
    layout: Any,
) -> Any | None:
    active_section_id = getattr(layout, "active_section_id", None)
    if active_section_id is not None:
        active_section = await models.section.by_id(active_section_id)
        if active_section is not None:
            return active_section
    sections = _sort_sections(
        await models.section.many(attention_session_layout_id=_row_id(layout))
    )
    for section in sections:
        if bool(getattr(section, "is_active", False)):
            return section
    return sections[0] if sections else None


async def _select_active_transition(
    *,
    models: _AttentionSessionReplicaModels,
    section: Any,
) -> Any | None:
    active_transition_id = getattr(section, "active_transition_id", None)
    if active_transition_id is not None:
        active_transition = await models.transition.by_id(active_transition_id)
        if active_transition is not None:
            return active_transition
    transitions = _sort_transitions(
        await models.transition.many(attention_session_section_id=_row_id(section))
    )
    return transitions[-1] if transitions else None


def _select_active_layout(*, session: Any, layouts: list[Any]) -> Any | None:
    active_layout_id = getattr(session, "active_layout_id", None)
    if active_layout_id is not None:
        for layout in layouts:
            if _row_id(layout) == active_layout_id:
                return layout
    for layout in layouts:
        if bool(getattr(layout, "is_active", False)):
            return layout
    return layouts[0] if layouts else None


def _attention_session_pin(session: Any) -> AttentionSessionPin:
    return AttentionSessionPin(
        attention_session_id=_row_id(session),
        identity_session_id=cast(UUID, getattr(session, "identity_session_id")),
        active_layout_id=cast(UUID | None, getattr(session, "active_layout_id", None)),
        key=cast(str | None, getattr(session, "key", None)),
        title=cast(str | None, getattr(session, "title", None)),
        description=cast(str | None, getattr(session, "description", None)),
        purpose=cast(str | None, getattr(session, "purpose", None)),
        status=cast(str, getattr(session, "status", "active")),
        source_kind=cast(str | None, getattr(session, "source_kind", None)),
        source_ref=cast(str | None, getattr(session, "source_ref", None)),
        metadata_json=_metadata_json(session),
    )


def _attention_session_layout_pin(layout: Any) -> AttentionSessionLayoutPin:
    return AttentionSessionLayoutPin(
        attention_session_layout_id=_row_id(layout),
        attention_session_id=cast(UUID, getattr(layout, "attention_session_id")),
        layout_id=cast(UUID, getattr(layout, "layout_id")),
        layout_config_id=cast(UUID | None, getattr(layout, "layout_config_id", None)),
        active_section_id=cast(UUID | None, getattr(layout, "active_section_id", None)),
        active_layout_transition_id=cast(
            UUID | None,
            getattr(layout, "active_layout_transition_id", None),
        ),
        active_topology_transition_id=cast(
            UUID | None,
            getattr(layout, "active_topology_transition_id", None),
        ),
        key=cast(str | None, getattr(layout, "key", None)),
        order=int(getattr(layout, "order", 0) or 0),
        is_active=bool(getattr(layout, "is_active", True)),
    )


def _attention_session_section_pin(section: Any) -> AttentionSessionSectionPin:
    return AttentionSessionSectionPin(
        attention_session_section_id=_row_id(section),
        attention_session_layout_id=cast(
            UUID, getattr(section, "attention_session_layout_id")
        ),
        layout_section_id=cast(UUID, getattr(section, "layout_section_id")),
        section_id=cast(UUID, getattr(section, "section_id")),
        active_transition_id=cast(
            UUID | None, getattr(section, "active_transition_id", None)
        ),
        section_key=cast(str | None, getattr(section, "section_key", None)),
        order=int(getattr(section, "order", 0) or 0),
        is_active=bool(getattr(section, "is_active", True)),
    )


def _attention_transition_pin(
    chain: _AttentionTransitionChain,
) -> AttentionFocusTransitionPin:
    transition = chain.transition
    section = chain.section
    layout = chain.layout
    session = chain.session
    return AttentionFocusTransitionPin(
        attention_focus_transition_id=_row_id(transition),
        attention_session_section_id=cast(
            UUID,
            getattr(transition, "attention_session_section_id"),
        ),
        attention_session_layout_id=(
            cast(UUID, getattr(section, "attention_session_layout_id"))
            if section is not None
            else None
        ),
        attention_session_id=(
            cast(UUID, getattr(layout, "attention_session_id"))
            if layout is not None
            else None
        ),
        identity_session_id=(
            cast(UUID, getattr(session, "identity_session_id"))
            if session is not None
            else None
        ),
        layout_section_id=(
            cast(UUID, getattr(section, "layout_section_id"))
            if section is not None
            else None
        ),
        section_id=(
            cast(UUID, getattr(section, "section_id")) if section is not None else None
        ),
        section_key=(
            cast(str | None, getattr(section, "section_key", None))
            if section is not None
            else None
        ),
        layout_id=(
            cast(UUID, getattr(layout, "layout_id")) if layout is not None else None
        ),
        layout_config_id=(
            cast(UUID | None, getattr(layout, "layout_config_id", None))
            if layout is not None
            else None
        ),
        previous_transition_id=cast(
            UUID | None,
            getattr(transition, "previous_transition_id", None),
        ),
        focus_scope_id=cast(UUID, getattr(transition, "focus_scope_id")),
        focus_id=cast(UUID | None, getattr(transition, "focus_id", None)),
        observable_id=cast(UUID | None, getattr(transition, "observable_id", None)),
        object_projection_graph_identity_id=cast(
            UUID | None,
            getattr(transition, "object_projection_graph_identity_id", None),
        ),
        object_instance_graph_branch_id=cast(
            UUID | None,
            getattr(transition, "object_instance_graph_branch_id", None),
        ),
        object_instance_graph_commit_id=cast(
            UUID | None,
            getattr(transition, "object_instance_graph_commit_id", None),
        ),
        transition_key=cast(str, getattr(transition, "transition_key")),
        sequence=int(getattr(transition, "sequence", 0) or 0),
        projection_hash=cast(str | None, getattr(transition, "projection_hash", None)),
        transition_kind=cast(str, getattr(transition, "transition_kind", "focus")),
        rationale=cast(str | None, getattr(transition, "rationale", None)),
        source_kind=cast(str | None, getattr(transition, "source_kind", None)),
        source_ref=cast(str | None, getattr(transition, "source_ref", None)),
        metadata_json=_metadata_json(transition),
    )


def _transition_pin_matches_request(
    *,
    pin: AttentionFocusTransitionPin,
    request: CanonicalListAttentionTransitionsRequest,
) -> bool:
    if (
        request.focus_scope_id is not None
        and pin.focus_scope_id != request.focus_scope_id
    ):
        return False
    if _normalize_optional_text(
        request.transition_kind
    ) is not None and _normalize_optional_text(
        pin.transition_kind
    ) != _normalize_optional_text(
        request.transition_kind
    ):
        return False
    return True


def _transition_validation_failures(
    *,
    pin: AttentionFocusTransitionPin,
    request: CanonicalValidateAttentionTransitionRequest,
) -> list[str]:
    failures: list[str] = []
    if (
        request.expected_identity_session_id is not None
        and pin.identity_session_id != request.expected_identity_session_id
    ):
        failures.append("identity_session_mismatch")
    if (
        request.expected_attention_session_id is not None
        and pin.attention_session_id != request.expected_attention_session_id
    ):
        failures.append("attention_session_mismatch")
    if (
        request.expected_attention_session_section_id is not None
        and pin.attention_session_section_id
        != request.expected_attention_session_section_id
    ):
        failures.append("attention_session_section_mismatch")
    if (
        request.expected_focus_scope_id is not None
        and pin.focus_scope_id != request.expected_focus_scope_id
    ):
        failures.append("focus_scope_mismatch")
    if (
        request.expected_object_instance_graph_commit_id is not None
        and pin.object_instance_graph_commit_id
        != request.expected_object_instance_graph_commit_id
    ):
        failures.append("object_instance_graph_commit_mismatch")
    if _normalize_optional_text(
        request.expected_projection_hash
    ) is not None and _normalize_optional_text(
        pin.projection_hash
    ) != _normalize_optional_text(
        request.expected_projection_hash
    ):
        failures.append("projection_hash_mismatch")
    if pin.attention_session_id is None:
        failures.append("attention_session_chain_missing")
    if pin.identity_session_id is None:
        failures.append("identity_session_chain_missing")
    return failures


def _sort_sessions(sessions: list[Any]) -> list[Any]:
    return sorted(
        sessions,
        key=lambda session: (
            str(getattr(session, "key", "") or ""),
            str(_row_id(session)),
        ),
    )


def _sort_layouts(layouts: list[Any]) -> list[Any]:
    return sorted(
        layouts,
        key=lambda layout: (
            int(getattr(layout, "order", 0) or 0),
            str(getattr(layout, "key", "") or ""),
            str(_row_id(layout)),
        ),
    )


def _sort_sections(sections: list[Any]) -> list[Any]:
    return sorted(
        sections,
        key=lambda section: (
            int(getattr(section, "order", 0) or 0),
            str(getattr(section, "section_key", "") or ""),
            str(_row_id(section)),
        ),
    )


def _sort_transitions(transitions: list[Any]) -> list[Any]:
    return sorted(
        transitions,
        key=lambda transition: (
            int(getattr(transition, "sequence", 0) or 0),
            str(getattr(transition, "transition_key", "") or ""),
            str(_row_id(transition)),
        ),
    )


def _metadata_json(row: Any) -> JsonObject:
    value = getattr(row, "metadata_json", None)
    if value is None:
        return JsonObject()
    if isinstance(value, JsonObject):
        return value
    return JsonObject(value)


def _row_id(row: Any) -> UUID:
    return cast(UUID, getattr(row, "id"))


async def _get_runtime_mount(
    *,
    runtime_context: _AttentionRuntimeContext,
    operation_context: ServiceOperationContext,
    request: CanonicalGetAttentionRuntimeMountRequest,
) -> AttentionRuntimeMountSnapshot:
    environment_target = _normalize_environment_runtime_target(
        request.environment_target
    )
    selected_layout = _select_runtime_mount_layout(
        request=request,
    )
    if selected_layout is None:
        _validate_environment_runtime_target_layout(
            environment_target=environment_target,
            selected_layout=None,
        )
        return AttentionRuntimeMountSnapshot(
            window_key=_normalize_optional_text(request.window_key),
            environment_target=environment_target,
            attention_session_id=request.attention_session_id,
            attention_session_layout_id=None,
            layout_config_id=None,
            layout_id=None,
            layout_key=None,
            active_section_key=None,
            active_observable_id=None,
            admitted_layout_sections=[],
            layout_sections=[],
            section_snapshots=[],
        )
    _validate_environment_runtime_target_layout(
        environment_target=environment_target,
        selected_layout=selected_layout,
    )
    layout_id = _runtime_mount_layout_id(
        environment_target=environment_target,
        selected_layout=selected_layout,
    )
    layout_config_id = (
        selected_layout.layout_config_id
        if selected_layout.layout_config_id is not None
        else (
            environment_target.layout_config_id
            if environment_target is not None
            else None
        )
    )
    layout_sections = await _get_runtime_mount_layout_sections(
        runtime_context=runtime_context,
        environment_target=environment_target,
        selected_layout=selected_layout,
        layout_id=layout_id,
        layout_config_id=layout_config_id,
    )
    attention_session_layout_id: UUID | None = None
    active_layout_transition: AttentionLayoutTransitionPin | None = None
    active_layout_topology_transition: AttentionLayoutTopologyTransitionPin | None = (
        None
    )
    admitted_layout_sections = list(layout_sections)
    if request.attention_session_id is not None:
        session_snapshot = await _load_attention_session_lane_snapshot(
            runtime_context=runtime_context,
            attention_session_id=request.attention_session_id,
        )
        if session_snapshot is None:
            raise ValueError(
                "Attention runtime mount session lane not found: "
                f"attention_session_id={request.attention_session_id}"
            )
        session_layout = _select_runtime_session_layout(
            session=session_snapshot.session,
            layout_id=layout_id,
            layout_config_id=layout_config_id,
            layout_key=selected_layout.layout_key,
        )
        if session_layout is None:
            raise ValueError(
                "Attention runtime mount could not match the selected layout to "
                f"AttentionSession {request.attention_session_id}."
            )
        attention_session_layout_id = _row_id(session_layout)
        layout_sections = _bind_runtime_session_sections(
            layout_sections=layout_sections,
            session_layout=session_layout,
        )
        admitted_layout_sections = list(layout_sections)
        active_layout_transition = _active_layout_transition_pin(
            layout=session_layout,
            head=session_snapshot.head,
        )
        active_layout_topology_transition = _active_layout_topology_transition_pin(
            layout=session_layout,
            head=session_snapshot.head,
        )
        if active_layout_topology_transition is not None:
            layout_sections = _overlay_runtime_layout_topology_transition(
                layout_sections=layout_sections,
                transition=active_layout_topology_transition,
            )
        if active_layout_transition is not None:
            active_topology_id = (
                active_layout_topology_transition.attention_layout_topology_transition_id
                if active_layout_topology_transition is not None
                else None
            )
            if active_layout_transition.topology_transition_id != active_topology_id:
                raise RuntimeError(
                    "AttentionSession active geometry transition does not pin the "
                    "active topology transition."
                )
            layout_sections = _overlay_runtime_layout_transition(
                layout_sections=layout_sections,
                transition=active_layout_transition,
            )
    section_snapshots: list[AttentionSectionSnapshot] = []
    mounted_section_keys = {state.section_key for state in layout_sections}
    for section_request in selected_layout.sections:
        if section_request.section_key not in mounted_section_keys:
            continue
        section_snapshots.append(
            await _get_section_state(
                runtime_context=runtime_context,
                operation_context=operation_context,
                request=CanonicalGetAttentionSectionStateRequest(
                    section_key=section_request.section_key,
                    default_observable_id=section_request.default_observable_id,
                    default_rationale=section_request.default_rationale,
                ),
            )
        )
    active_snapshot = _select_active_runtime_mount_snapshot(
        section_snapshots=tuple(section_snapshots),
        preferred_section_key=_normalize_optional_text(request.preferred_section_key),
        preferred_observable_id=request.preferred_observable_id,
    )
    return AttentionRuntimeMountSnapshot(
        window_key=_normalize_optional_text(request.window_key),
        environment_target=environment_target,
        attention_session_id=request.attention_session_id,
        attention_session_layout_id=attention_session_layout_id,
        layout_config_id=layout_config_id,
        layout_id=layout_id,
        layout_key=_normalize_optional_text(selected_layout.layout_key),
        active_section_key=(
            active_snapshot.section_key if active_snapshot is not None else None
        ),
        active_observable_id=(
            active_snapshot.observable_id if active_snapshot is not None else None
        ),
        active_layout_transition=active_layout_transition,
        active_layout_topology_transition=active_layout_topology_transition,
        admitted_layout_sections=admitted_layout_sections,
        layout_sections=layout_sections,
        section_snapshots=section_snapshots,
    )


def _bind_runtime_session_sections(
    *,
    layout_sections: list[AttentionRuntimeLayoutSectionState],
    session_layout: object,
) -> list[AttentionRuntimeLayoutSectionState]:
    """Attach authoritative mounted session-section ids before any transition."""

    runtime_by_layout_section_id = {
        state.layout_section_id: state
        for state in layout_sections
        if state.layout_section_id is not None
    }
    session_by_layout_section_id = {
        getattr(section, "layout_section_id", None): section
        for section in (getattr(session_layout, "sections", None) or [])
        if getattr(section, "layout_section_id", None) is not None
    }
    if (
        len(runtime_by_layout_section_id) != len(layout_sections)
        or len(session_by_layout_section_id)
        != len(getattr(session_layout, "sections", None) or [])
        or set(runtime_by_layout_section_id) != set(session_by_layout_section_id)
    ):
        raise ValueError(
            "AttentionSession mounted section membership does not match the "
            "selected runtime mount layout_section ids."
        )
    return sorted(
        (
            runtime_state.model_copy(
                update={
                    "attention_session_section_id": _row_id(
                        session_by_layout_section_id[layout_section_id]
                    )
                }
            )
            for layout_section_id, runtime_state in runtime_by_layout_section_id.items()
        ),
        key=lambda item: (item.order, item.section_key),
    )


def _overlay_runtime_layout_transition(
    *,
    layout_sections: list[AttentionRuntimeLayoutSectionState],
    transition: AttentionLayoutTransitionPin,
) -> list[AttentionRuntimeLayoutSectionState]:
    runtime_by_layout_section_id = {
        state.layout_section_id: state
        for state in layout_sections
        if state.layout_section_id is not None
    }
    transition_by_layout_section_id = {
        state.layout_section_id: state
        for state in transition.section_states
        if state.layout_section_id is not None
    }
    if (
        len(runtime_by_layout_section_id) != len(layout_sections)
        or len(transition_by_layout_section_id) != len(transition.section_states)
        or set(runtime_by_layout_section_id) != set(transition_by_layout_section_id)
    ):
        raise ValueError(
            "AttentionSession layout transition section membership does not match "
            "the selected runtime mount layout_section ids."
        )
    overlaid: list[AttentionRuntimeLayoutSectionState] = []
    for layout_section_id, runtime_state in runtime_by_layout_section_id.items():
        transition_state = transition_by_layout_section_id[layout_section_id]
        overlaid.append(
            runtime_state.model_copy(
                update={
                    "source_kind": "attention_session_layout_transition",
                    "attention_session_section_id": (
                        transition_state.attention_session_section_id
                    ),
                    "order": transition_state.order,
                    "flex": (
                        transition_state.weight_micros / 1_000_000.0
                        if transition_state.is_visible
                        and not transition_state.is_collapsed
                        else 0.0
                    ),
                    "weight_micros": transition_state.weight_micros,
                    "is_visible": transition_state.is_visible,
                    "is_collapsed": transition_state.is_collapsed,
                }
            )
        )
    return sorted(overlaid, key=lambda item: (item.order, item.section_key))


def _overlay_runtime_layout_topology_transition(
    *,
    layout_sections: list[AttentionRuntimeLayoutSectionState],
    transition: AttentionLayoutTopologyTransitionPin,
) -> list[AttentionRuntimeLayoutSectionState]:
    runtime_by_session_section_id = {
        state.attention_session_section_id: state
        for state in layout_sections
        if state.attention_session_section_id is not None
    }
    topology_by_session_section_id = {
        state.attention_session_section_id: state for state in transition.section_states
    }
    if (
        len(runtime_by_session_section_id) != len(layout_sections)
        or len(topology_by_session_section_id) != len(transition.section_states)
        or not topology_by_session_section_id
        or not set(topology_by_session_section_id).issubset(
            runtime_by_session_section_id
        )
    ):
        raise ValueError(
            "AttentionSession topology transition membership is not a non-empty "
            "subset of the admitted runtime mount section anchors."
        )
    mounted: list[AttentionRuntimeLayoutSectionState] = []
    for session_section_id, topology_state in topology_by_session_section_id.items():
        runtime_state = runtime_by_session_section_id[session_section_id]
        mounted.append(
            runtime_state.model_copy(
                update={
                    "source_kind": "attention_session_layout_topology_transition",
                    "order": topology_state.order,
                    "weight_micros": None,
                    "is_visible": True,
                    "is_collapsed": False,
                }
            )
        )
    return sorted(mounted, key=lambda item: (item.order, item.section_key))


async def _get_runtime_mount_layout_sections(
    *,
    runtime_context: _AttentionRuntimeContext,
    environment_target: AttentionEnvironmentRuntimeTarget | None,
    selected_layout: AttentionRuntimeMountLayoutRequest,
    layout_id: UUID | None,
    layout_config_id: UUID | None,
) -> list[AttentionRuntimeLayoutSectionState]:
    branch_candidates = _runtime_mount_layout_branch_candidates(
        environment_target=environment_target,
        selected_layout=selected_layout,
        layout_id=layout_id,
    )
    states: list[AttentionRuntimeLayoutSectionState] = []
    for index, section_request in enumerate(selected_layout.sections):
        states.append(
            await _get_runtime_mount_layout_section(
                runtime_context=runtime_context,
                branch_candidates=branch_candidates,
                layout_config_id=layout_config_id,
                layout_id=layout_id,
                section_request=section_request,
                index=index,
            )
        )
    return sorted(states, key=lambda item: (item.order, item.section_key))


async def _get_runtime_mount_layout_section(
    *,
    runtime_context: _AttentionRuntimeContext,
    branch_candidates: tuple[UUID, ...],
    layout_config_id: UUID | None,
    layout_id: UUID | None,
    section_request: AttentionRuntimeMountSectionRequest,
    index: int,
) -> AttentionRuntimeLayoutSectionState:
    section_key = _normalize_required_text(
        section_request.section_key,
        label="layout section_key",
    )
    section_id = section_request.section_id or stable_section_id(key=section_key)
    layout_section_id = section_request.layout_section_id
    if layout_section_id is None and layout_id is not None:
        layout_section_id = stable_layout_section_id(
            layout_id=layout_id,
            section_id=section_id,
        )
    layout_config_section_config_id = section_request.layout_config_section_config_id
    if layout_config_section_config_id is None and layout_config_id is not None:
        layout_config_section_config_id = stable_layout_config_section_config_id(
            layout_config_id=layout_config_id,
            section_key=section_key,
        )

    layout_section = None
    if layout_section_id is not None:
        layout_section = await _load_layout_section(
            runtime_context=runtime_context,
            branch_candidates=branch_candidates,
            layout_section_id=layout_section_id,
        )
    section = (
        getattr(layout_section, "section", None) if layout_section is not None else None
    )
    if section is None:
        section = await _load_section(
            runtime_context=runtime_context,
            section_id=section_id,
        )

    graph_layout_section = layout_section is not None
    graph_section_key = _normalize_optional_text(
        getattr(section, "key", None) if section is not None else None
    )
    title = _normalize_optional_text(
        getattr(section, "title", None) if section is not None else None
    ) or _normalize_optional_text(section_request.title)
    description = _normalize_optional_text(
        getattr(section, "description", None) if section is not None else None
    ) or _normalize_optional_text(section_request.description)
    return AttentionRuntimeLayoutSectionState(
        source_kind=(
            "attention_runtime_graph"
            if graph_layout_section
            else "runtime_mount_request"
        ),
        layout_config_id=layout_config_id,
        layout_id=(
            getattr(layout_section, "layout_id", None)
            if layout_section is not None
            else layout_id
        ),
        layout_config_section_config_id=layout_config_section_config_id,
        layout_section_id=layout_section_id,
        section_id=(
            getattr(layout_section, "section_id", None)
            if layout_section is not None
            else section_id
        ),
        section_key=graph_section_key or section_key,
        title=title,
        description=description,
        order=(
            int(layout_section.order)
            if layout_section is not None
            else section_request.order if section_request.order is not None else index
        ),
        flex=(
            float(layout_section.flex)
            if layout_section is not None
            else (
                float(section_request.flex) if section_request.flex is not None else 1.0
            )
        ),
        is_visible=(
            bool(layout_section.is_visible)
            if layout_section is not None
            else (
                bool(section_request.is_visible)
                if section_request.is_visible is not None
                else True
            )
        ),
    )


def _runtime_mount_layout_id(
    *,
    environment_target: AttentionEnvironmentRuntimeTarget | None,
    selected_layout: AttentionRuntimeMountLayoutRequest,
) -> UUID | None:
    if selected_layout.layout_id is not None:
        return selected_layout.layout_id
    layout_key = _normalize_optional_text(selected_layout.layout_key)
    if layout_key is not None:
        return stable_layout_id(key=layout_key)
    if environment_target is not None:
        return environment_target.layout_id
    return None


def _runtime_mount_layout_branch_candidates(
    *,
    environment_target: AttentionEnvironmentRuntimeTarget | None,
    selected_layout: AttentionRuntimeMountLayoutRequest,
    layout_id: UUID | None,
) -> tuple[UUID, ...]:
    candidates = [
        selected_layout.layout_id,
        layout_id,
        environment_target.layout_id if environment_target is not None else None,
        environment_target.thread_layout_id if environment_target is not None else None,
        selected_layout.layout_config_id,
        environment_target.layout_config_id if environment_target is not None else None,
    ]
    unique_candidates: list[UUID] = []
    seen: set[UUID] = set()
    for candidate in candidates:
        if candidate is None or candidate in seen:
            continue
        seen.add(candidate)
        unique_candidates.append(candidate)
    return tuple(unique_candidates)


def _select_runtime_mount_layout(
    *,
    request: CanonicalGetAttentionRuntimeMountRequest,
) -> AttentionRuntimeMountLayoutRequest | None:
    if not request.layouts:
        return None

    if request.preferred_layout_config_id is not None:
        selected = next(
            (
                layout
                for layout in request.layouts
                if layout.layout_config_id == request.preferred_layout_config_id
            ),
            None,
        )
        if selected is not None:
            return selected
        return None

    preferred_layout_key = _normalize_optional_text(request.preferred_layout_key)
    if preferred_layout_key is not None:
        selected = next(
            (
                layout
                for layout in request.layouts
                if layout.layout_key.strip().casefold()
                == preferred_layout_key.casefold()
            ),
            None,
        )
        if selected is not None:
            return selected
        return None

    preferred_section_key = _normalize_optional_text(request.preferred_section_key)
    if preferred_section_key is not None:
        matching_layouts = tuple(
            layout
            for layout in request.layouts
            if any(
                section.section_key.strip().casefold()
                == preferred_section_key.casefold()
                for section in layout.sections
            )
        )
        if len(matching_layouts) == 1:
            return matching_layouts[0]

    if len(request.layouts) == 1:
        return request.layouts[0]
    return None


def _normalize_environment_runtime_target(
    environment_target: AttentionEnvironmentRuntimeTarget | None,
) -> AttentionEnvironmentRuntimeTarget | None:
    if environment_target is None:
        return None
    if environment_target.thread_id is None:
        raise ValueError(
            "Attention runtime mount environment_target requires thread_id."
        )
    if environment_target.thread_layout_id is None:
        raise ValueError(
            "Attention runtime mount environment_target requires thread_layout_id."
        )
    return environment_target


def _validate_environment_runtime_target_layout(
    *,
    environment_target: AttentionEnvironmentRuntimeTarget | None,
    selected_layout: AttentionRuntimeMountLayoutRequest | None,
) -> None:
    if environment_target is None:
        return

    target_layout_config_id = environment_target.layout_config_id
    target_layout_key = _normalize_optional_text(environment_target.layout_key)
    if target_layout_config_id is None and target_layout_key is None:
        return
    if selected_layout is None:
        raise ValueError(
            "Attention runtime mount environment_target did not match a layout request."
        )

    selected_layout_key = _normalize_optional_text(selected_layout.layout_key)
    layout_config_matches = (
        target_layout_config_id is not None
        and selected_layout.layout_config_id == target_layout_config_id
    )
    layout_key_matches = (
        target_layout_key is not None
        and selected_layout_key is not None
        and selected_layout_key.casefold() == target_layout_key.casefold()
    )
    if layout_config_matches or layout_key_matches:
        return
    raise ValueError(
        "Attention runtime mount environment_target did not match the selected layout."
    )


def _select_active_runtime_mount_snapshot(
    *,
    section_snapshots: tuple[AttentionSectionSnapshot, ...],
    preferred_section_key: str | None,
    preferred_observable_id: UUID | None,
) -> AttentionSectionSnapshot | None:
    if not section_snapshots:
        return None

    normalized_section_key = (
        preferred_section_key.strip().casefold()
        if preferred_section_key is not None and preferred_section_key.strip()
        else None
    )
    if preferred_observable_id is not None:
        for snapshot in section_snapshots:
            if snapshot.observable_id != preferred_observable_id:
                continue
            if (
                normalized_section_key is not None
                and snapshot.section_key.strip().casefold() != normalized_section_key
            ):
                continue
            return snapshot

    if normalized_section_key is not None:
        for snapshot in section_snapshots:
            if snapshot.section_key.strip().casefold() == normalized_section_key:
                return snapshot

    for snapshot in section_snapshots:
        if snapshot.observable_id is not None:
            return snapshot
    return None


async def _read_section_snapshot(
    *,
    runtime_context: _AttentionRuntimeContext,
    section_key: str,
) -> AttentionSectionSnapshot:
    normalized_section_key = section_key.strip()
    if not normalized_section_key:
        raise ValueError("section_key is required")
    section_id = stable_section_id(key=normalized_section_key)
    replica_snapshot = await _read_section_snapshot_from_replica_orm(
        runtime_context=runtime_context,
        section_id=section_id,
        section_key=normalized_section_key,
    )
    if replica_snapshot is not None:
        return replica_snapshot
    section = await _load_section(
        runtime_context=runtime_context,
        section_id=section_id,
    )
    if section is None:
        return AttentionSectionSnapshot(
            section_id=section_id,
            section_key=normalized_section_key,
            section_title=None,
            section_description=None,
            exists=False,
            section_focus_scope_id=None,
            focus_scope_id=None,
            focus_scope_title=None,
            focus_scope_description=None,
            focus_id=None,
            observable_id=None,
            is_active=False,
        )
    active_section_focus_scope = _active_section_focus_scope(section=section)
    focus_scope = None
    focus = None
    if active_section_focus_scope is not None:
        focus_scope = await _load_focus_scope(
            runtime_context=runtime_context,
            focus_scope_id=active_section_focus_scope.focus_scope_id,
        )
    if focus_scope is not None and focus_scope.focus_id is not None:
        focus = focus_scope.focus or await _load_focus(
            runtime_context=runtime_context,
            focus_id=focus_scope.focus_id,
        )
    return AttentionSectionSnapshot(
        section_id=section.id,
        section_key=section.key,
        section_title=section.title,
        section_description=section.description,
        exists=True,
        section_focus_scope_id=(
            active_section_focus_scope.id
            if active_section_focus_scope is not None
            else None
        ),
        focus_scope_id=(
            active_section_focus_scope.focus_scope_id
            if active_section_focus_scope is not None
            else None
        ),
        focus_scope_title=(
            focus_scope.title
            if focus_scope is not None
            else (
                active_section_focus_scope.title
                if active_section_focus_scope is not None
                else None
            )
        ),
        focus_scope_description=(
            focus_scope.description
            if focus_scope is not None
            else (
                active_section_focus_scope.description
                if active_section_focus_scope is not None
                else None
            )
        ),
        focus_id=focus_scope.focus_id if focus_scope is not None else None,
        observable_id=focus_scope.observable_id if focus_scope is not None else None,
        focus_target=(
            _focus_target_from_focus(
                focus_scope_id=focus_scope.id,
                focus=focus,
            )
            if focus_scope is not None and focus is not None
            else None
        ),
        is_active=focus_scope.is_active if focus_scope is not None else False,
    )


async def _read_section_snapshot_from_replica_orm(
    *,
    runtime_context: _AttentionRuntimeContext,
    section_id: UUID,
    section_key: str,
) -> AttentionSectionSnapshot | None:
    replica_session = current_service_ontology_replica_orm_session()
    if replica_session is None:
        return None
    _ = replica_session
    try:
        from aware_attention_ontology_orm_models.focus.focus import (
            Focus as FocusOrmModel,
        )
        from aware_attention_ontology_orm_models.focus.focus_scope import (
            FocusScope as FocusScopeOrmModel,
        )
        from aware_attention_ontology_orm_models.section.section import (
            Section as SectionOrmModel,
        )
        from aware_attention_ontology_orm_models.section.section_focus_scope import (
            SectionFocusScope as SectionFocusScopeOrmModel,
        )
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Attention service ontology replica reads require the generated "
            "Attention ontology ORM model package to be importable. ServiceHost "
            "startup must expose the required ontology ORM package closure."
        ) from exc

    section = await SectionOrmModel.by_id(section_id)
    if section is None:
        return AttentionSectionSnapshot(
            section_id=section_id,
            section_key=section_key,
            section_title=None,
            section_description=None,
            exists=False,
            section_focus_scope_id=None,
            focus_scope_id=None,
            focus_scope_title=None,
            focus_scope_description=None,
            focus_id=None,
            observable_id=None,
            focus_target=None,
            is_active=False,
        )

    active_section_focus_scope_id = section.active_focus_scope_id
    section_focus_scope = None
    if active_section_focus_scope_id is not None:
        section_focus_scope = await SectionFocusScopeOrmModel.by_id(
            active_section_focus_scope_id
        )
    if section_focus_scope is None:
        section_focus_scope = await SectionFocusScopeOrmModel.one(section_id=section_id)

    focus_scope_id = (
        section_focus_scope.focus_scope_id if section_focus_scope is not None else None
    )
    focus_scope = None
    if focus_scope_id is not None:
        focus_scope = await FocusScopeOrmModel.by_id(focus_scope_id)
    focus_id = focus_scope.focus_id if focus_scope is not None else None
    focus = None
    if focus_id is not None:
        focus = await FocusOrmModel.by_id(focus_id)

    return AttentionSectionSnapshot(
        section_id=section_id,
        section_key=section.key or section_key,
        section_title=section.title,
        section_description=section.description,
        exists=True,
        section_focus_scope_id=(
            section_focus_scope.id if section_focus_scope is not None else None
        ),
        focus_scope_id=focus_scope_id,
        focus_scope_title=focus_scope.title if focus_scope is not None else None,
        focus_scope_description=(
            focus_scope.description if focus_scope is not None else None
        ),
        focus_id=focus_id,
        observable_id=focus_scope.observable_id if focus_scope is not None else None,
        focus_target=(
            _focus_target_from_focus(
                focus_scope_id=focus_scope_id,
                focus=cast(Focus, cast(object, focus)),
            )
            if focus is not None and focus_scope_id is not None
            else None
        ),
        is_active=focus_scope.is_active if focus_scope is not None else False,
    )


async def _load_section(
    *,
    runtime_context: _AttentionRuntimeContext,
    section_id: UUID,
) -> Section | None:
    return await _load_projection_root_model(
        runtime_context=runtime_context,
        branch_id=section_id,
        projection_hash=runtime_context.section_projection_hash,
        root_id=section_id,
        model_type=Section,
    )


async def _load_layout_section(
    *,
    runtime_context: _AttentionRuntimeContext,
    branch_candidates: tuple[UUID, ...],
    layout_section_id: UUID,
) -> LayoutSection | None:
    for branch_id in branch_candidates:
        layout_section = await _load_projection_root_model(
            runtime_context=runtime_context,
            branch_id=branch_id,
            projection_hash=runtime_context.layout_projection_hash,
            root_id=layout_section_id,
            model_type=LayoutSection,
        )
        if layout_section is not None:
            return layout_section
    return None


async def _load_focus_scope(
    *,
    runtime_context: _AttentionRuntimeContext,
    focus_scope_id: UUID,
) -> FocusScope | None:
    return await _load_projection_root_model(
        runtime_context=runtime_context,
        branch_id=focus_scope_id,
        projection_hash=runtime_context.focus_scope_projection_hash,
        root_id=focus_scope_id,
        model_type=FocusScope,
    )


async def _load_focus(
    *,
    runtime_context: _AttentionRuntimeContext,
    focus_id: UUID,
) -> Focus | None:
    return await _load_projection_root_model(
        runtime_context=runtime_context,
        branch_id=focus_id,
        projection_hash=runtime_context.focus_projection_hash,
        root_id=focus_id,
        model_type=Focus,
    )


async def _resolve_environment_receipt_focus_routes_from_replica(
    *,
    runtime_context: _AttentionRuntimeContext,
    receipt: LaneCommitReceiptNotification,
) -> tuple[AttentionEnvironmentFocusRoute, ...]:
    replica_session = current_service_ontology_replica_orm_session()
    if replica_session is None:
        return ()
    _ = replica_session
    try:
        from aware_attention_ontology_orm_models.focus.focus import (
            Focus as FocusOrmModel,
        )
        from aware_attention_ontology_orm_models.focus.focus_scope import (
            FocusScope as FocusScopeOrmModel,
        )
        from aware_attention_ontology_orm_models.section.section import (
            Section as SectionOrmModel,
        )
        from aware_attention_ontology_orm_models.section.section_focus_scope import (
            SectionFocusScope as SectionFocusScopeOrmModel,
        )
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Attention Environment fanout committed focus resolution requires "
            "the generated Attention ontology ORM model package to be importable. "
            "ServiceHost startup must expose the required ontology ORM package "
            "closure."
        ) from exc

    object_instance_graph_branch_id = receipt.object_instance_graph_branch_id
    object_projection_graph_identity_id = receipt.object_projection_graph_identity_id
    if (
        object_instance_graph_branch_id is None
        and object_projection_graph_identity_id is None
    ):
        return ()

    if object_instance_graph_branch_id is not None:
        focus_candidates = list(
            await FocusOrmModel.many(
                object_instance_graph_branch_id=object_instance_graph_branch_id
            )
        )
    else:
        focus_candidates = list(
            await FocusOrmModel.many(
                object_projection_graph_identity_id=object_projection_graph_identity_id
            )
        )

    routes: list[AttentionEnvironmentFocusRoute] = []
    for focus in focus_candidates:
        if not _focus_matches_environment_receipt(
            focus=focus,
            receipt=receipt,
            ignored_focus_projection_hash=runtime_context.focus_scope_projection_hash,
        ):
            continue
        focus_scope = await FocusScopeOrmModel.by_id(focus.focus_scope_id)
        if focus_scope is None:
            continue
        if not bool(getattr(focus_scope, "is_active", False)):
            continue
        if focus_scope.focus_id != focus.id:
            continue
        section_key = await _resolve_active_section_key_for_focus_scope_from_replica(
            section_model=cast(type[_ReplicaQueryModel], SectionOrmModel),
            section_focus_scope_model=cast(
                type[_ReplicaQueryModel], SectionFocusScopeOrmModel
            ),
            focus_scope_id=focus_scope.id,
        )
        routes.append(
            AttentionEnvironmentFocusRoute(
                section_key=section_key,
                observable_id=focus_scope.observable_id,
                focus_scope_id=focus_scope.id,
                focus_id=focus.id,
                focus_target=_focus_target_from_focus_orm(
                    focus_scope_id=focus_scope.id,
                    focus=focus,
                    projection_hash=receipt.projection_hash,
                ),
            )
        )
    return tuple(routes)


def _focus_matches_environment_receipt(
    *,
    focus: object,
    receipt: LaneCommitReceiptNotification,
    ignored_focus_projection_hash: str | None,
) -> bool:
    if not bool(getattr(focus, "is_active", False)):
        return False
    receipt_branch_id = receipt.object_instance_graph_branch_id
    focus_branch_id = getattr(focus, "object_instance_graph_branch_id", None)
    if receipt_branch_id is not None and focus_branch_id != receipt_branch_id:
        return False
    receipt_opgi_id = receipt.object_projection_graph_identity_id
    focus_opgi_id = getattr(focus, "object_projection_graph_identity_id", None)
    if receipt_opgi_id is not None and focus_opgi_id != receipt_opgi_id:
        return False
    receipt_projection_hash = _normalize_optional_text(receipt.projection_hash)
    focus_projection_hash = _normalize_optional_text(
        getattr(focus, "projection_hash", None)
    )
    ignored_projection_hash = _normalize_optional_text(ignored_focus_projection_hash)
    if focus_projection_hash == ignored_projection_hash:
        focus_projection_hash = None
    if (
        receipt_projection_hash is not None
        and focus_projection_hash is not None
        and receipt_projection_hash != focus_projection_hash
    ):
        return False
    return True


async def _resolve_active_section_key_for_focus_scope_from_replica(
    *,
    section_model: type[_ReplicaQueryModel],
    section_focus_scope_model: type[_ReplicaQueryModel],
    focus_scope_id: UUID,
) -> str | None:
    section_focus_scopes = list(
        await section_focus_scope_model.many(focus_scope_id=focus_scope_id)
    )
    for section_focus_scope in section_focus_scopes:
        section = await section_model.by_id(section_focus_scope.section_id)
        if section is None:
            continue
        active_focus_scope_id = getattr(section, "active_focus_scope_id", None)
        if (
            active_focus_scope_id is None
            or active_focus_scope_id == section_focus_scope.id
        ):
            return cast(str | None, getattr(section, "key", None))
    return None


def _focus_target_from_focus_orm(
    *,
    focus_scope_id: UUID,
    focus: object,
    projection_hash: str | None = None,
) -> AttentionSectionFocusTarget:
    object_instance_graph_branch_id = cast(
        UUID | None,
        getattr(focus, "object_instance_graph_branch_id", None),
    )
    return AttentionSectionFocusTarget(
        kind=(
            "materialized"
            if object_instance_graph_branch_id is not None
            else "constructor"
        ),
        focus_id=cast(UUID, getattr(focus, "id")),
        focus_scope_id=focus_scope_id,
        object_projection_graph_identity_id=cast(
            UUID,
            getattr(focus, "object_projection_graph_identity_id"),
        ),
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        projection_hash=_normalize_optional_text(projection_hash)
        or _normalize_optional_text(getattr(focus, "projection_hash", None)),
        target_type=_normalize_optional_text(getattr(focus, "target_type", None)),
        target_id=cast(UUID | None, getattr(focus, "target_id", None)),
        description=_normalize_optional_text(getattr(focus, "description", None)),
    )


async def _ensure_focus_target(
    *,
    runtime_context: _AttentionRuntimeContext,
    operation_context: ServiceOperationContext,
    focus_scope_id: UUID,
    focus_target: AttentionSectionFocusTarget | None,
    rationale: str | None,
) -> AttentionSectionFocusTarget | None:
    if focus_target is None:
        return None
    if (
        focus_target.focus_scope_id is not None
        and focus_target.focus_scope_id != focus_scope_id
    ):
        raise ValueError(
            "Attention focus target focus_scope_id does not match activation scope: "
            + f"focus_target.focus_scope_id={focus_target.focus_scope_id} "
            + f"activation.focus_scope_id={focus_scope_id}"
        )
    kind = _focus_target_kind(focus_target)
    focus_id = focus_target.focus_id or stable_focus_id(
        object_projection_graph_identity_id=focus_target.object_projection_graph_identity_id,
        focus_scope_id=focus_scope_id,
    )
    await _invoke_constructor(
        runtime_context=runtime_context,
        operation_context=operation_context,
        branch_id=focus_id,
        projection_hash=runtime_context.focus_projection_hash,
        object_projection_graph_id=runtime_context.focus_opg_id,
        function_id=runtime_context.focus_build_function_id,
        kwargs={
            "focus_scope_id": focus_scope_id,
            "object_projection_graph_identity_id": focus_target.object_projection_graph_identity_id,
            "projection_hash": focus_target.projection_hash,
            "object_instance_graph_branch_id": focus_target.object_instance_graph_branch_id,
            "target_type": _normalize_optional_text(focus_target.target_type),
            "target_id": focus_target.target_id,
            "description": _normalize_optional_text(focus_target.description),
            "expires_at": None,
            "is_active": True,
            "last_accessed": _utc_now_iso(),
        },
    )
    await _invoke_instance(
        runtime_context=runtime_context,
        operation_context=operation_context,
        branch_id=focus_scope_id,
        projection_hash=runtime_context.focus_scope_projection_hash,
        object_id=focus_scope_id,
        function_id=runtime_context.focus_scope_set_focus_function_id,
        kwargs={"focus_id": focus_id, "rationale": rationale},
    )
    return AttentionSectionFocusTarget(
        kind=kind,
        focus_id=focus_id,
        focus_scope_id=focus_scope_id,
        object_projection_graph_identity_id=focus_target.object_projection_graph_identity_id,
        object_instance_graph_branch_id=focus_target.object_instance_graph_branch_id,
        projection_hash=focus_target.projection_hash,
        target_type=_normalize_optional_text(focus_target.target_type),
        target_id=focus_target.target_id,
        description=_normalize_optional_text(focus_target.description),
    )


async def _ensure_focus_scope_commit(
    *,
    runtime_context: _AttentionRuntimeContext,
    operation_context: ServiceOperationContext,
    focus_scope_id: UUID,
    focus_id: UUID,
    object_instance_graph_commit_id: UUID,
) -> InvokeFunctionResponse:
    return await _invoke_instance(
        runtime_context=runtime_context,
        operation_context=operation_context,
        branch_id=focus_scope_id,
        projection_hash=runtime_context.focus_scope_projection_hash,
        object_id=focus_scope_id,
        function_id=runtime_context.focus_scope_ensure_commit_function_id,
        kwargs={
            "focus_id": focus_id,
            "object_instance_graph_commit_id": object_instance_graph_commit_id,
        },
    )


def _focus_target_kind(focus_target: AttentionSectionFocusTarget) -> str:
    normalized = (focus_target.kind or "").strip().casefold()
    if focus_target.object_instance_graph_branch_id is not None:
        return "materialized"
    if normalized in ("", "constructor"):
        return "constructor"
    if normalized == "materialized":
        raise ValueError(
            "Attention materialized focus target requires object_instance_graph_branch_id."
        )
    raise ValueError(f"Unsupported Attention focus target kind: {focus_target.kind!r}")


def _focus_target_from_focus(
    *, focus_scope_id: UUID, focus: Focus
) -> AttentionSectionFocusTarget:
    kind = (
        "materialized"
        if focus.object_instance_graph_branch_id is not None
        else "constructor"
    )
    return AttentionSectionFocusTarget(
        kind=kind,
        focus_id=focus.id,
        focus_scope_id=focus_scope_id,
        object_projection_graph_identity_id=focus.object_projection_graph_identity_id,
        object_instance_graph_branch_id=focus.object_instance_graph_branch_id,
        projection_hash=focus.projection_hash,
        target_type=focus.target_type,
        target_id=focus.target_id,
        description=focus.description,
    )


def _focus_scope_commit_pin(focus_scope_commit: object) -> AttentionFocusScopeCommitPin:
    return ServiceAttentionFocusScopeCommitPin(
        focus_scope_commit_id=cast(UUID, getattr(focus_scope_commit, "id")),
        focus_scope_id=cast(UUID, getattr(focus_scope_commit, "focus_scope_id")),
        focus_id=cast(UUID, getattr(focus_scope_commit, "focus_id")),
        object_instance_graph_commit_id=cast(
            UUID,
            getattr(focus_scope_commit, "object_instance_graph_commit_id"),
        ),
    )


def _active_section_focus_scope(*, section: Section) -> SectionFocusScope | None:
    if section.active_focus_scope is not None:
        return section.active_focus_scope
    active_id = section.active_focus_scope_id
    if active_id is not None:
        for item in section.focus_scopes:
            if item.id == active_id:
                return item
    return section.focus_scopes[0] if section.focus_scopes else None


async def _invoke_constructor(
    *,
    runtime_context: _AttentionRuntimeContext,
    operation_context: ServiceOperationContext,
    branch_id: UUID,
    projection_hash: str,
    object_projection_graph_id: UUID,
    function_id: UUID,
    kwargs: dict[str, object],
) -> InvokeFunctionResponse:
    actor_id = _require_graph_actor_id(operation_context)
    response = await runtime_context.graph_gateway.invoke_function(
        request=InvokeFunctionRequest(
            actor_id=actor_id,
            domain_branch_id=branch_id,
            domain_projection_hash=projection_hash,
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
    runtime_context: _AttentionRuntimeContext,
    operation_context: ServiceOperationContext,
    branch_id: UUID,
    projection_hash: str,
    object_id: UUID,
    function_id: UUID,
    kwargs: dict[str, object],
    expected_graph_hash_pre: str | None = None,
    expected_head_commit_id: UUID | None = None,
    ensure_succeeded: bool = True,
) -> InvokeFunctionResponse:
    actor_id = _require_graph_actor_id(operation_context)
    response = await runtime_context.graph_gateway.invoke_function(
        request=InvokeFunctionRequest(
            actor_id=actor_id,
            domain_branch_id=branch_id,
            domain_projection_hash=projection_hash,
            call_target=InvokeFunctionCallTarget.instance,
            target_object_id=object_id,
            object_projection_graph_id=None,
            function_id=function_id,
            args=cast(JsonArray, []),
            kwargs=cast(JsonObject, kwargs),
            expected_graph_hash_pre=expected_graph_hash_pre,
            expected_head_commit_id=expected_head_commit_id,
            commit=True,
            publish=False,
        ),
        graph_context=runtime_context.runtime_index,
    )
    if ensure_succeeded:
        _ensure_invoke_succeeded(response=response)
    return response


def _require_graph_actor_id(operation_context: ServiceOperationContext) -> UUID:
    actor_id = operation_context.actor_id
    if actor_id is not None:
        return actor_id
    environment_context = _require_environment_operation_context()
    if environment_context.actor_id is not None:
        return environment_context.actor_id
    raise RuntimeError(
        "Attention graph mutation requires an actor_id on the service or "
        "Environment operation context."
    )


def _require_environment_operation_context() -> EnvironmentOperationContext:
    host_context = current_service_api_host_context()
    if host_context is None or host_context.environment_context is None:
        raise RuntimeError(
            "Attention graph mutation requires an EnvironmentOperationContext "
            "on the active Service API host context."
        )
    return host_context.environment_context


def _ensure_invoke_succeeded(*, response: InvokeFunctionResponse) -> None:
    if (response.status or "").strip().lower() == "succeeded":
        return
    raise ValueError(
        f"Attention service invoke failed: {response.error or response.status}"
    )


async def _load_projection_root_model(
    *,
    runtime_context: _AttentionRuntimeContext,
    branch_id: UUID,
    projection_hash: str,
    root_id: UUID,
    model_type: type[_TModel],
) -> _TModel | None:
    loaded = await _load_projection_root_model_with_head(
        runtime_context=runtime_context,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_id=root_id,
        model_type=model_type,
    )
    return loaded[0] if loaded is not None else None


async def _load_projection_root_model_with_head(
    *,
    runtime_context: _AttentionRuntimeContext,
    branch_id: UUID,
    projection_hash: str,
    root_id: UUID,
    model_type: type[_TModel],
) -> tuple[_TModel, JsonObject] | None:
    target_head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if target_head is None or not target_head.get("commit_id"):
        return None
    opg = runtime_context.runtime_index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"Attention service could not resolve projection hash {projection_hash!r}."
        )
    target_oig, _ = await CachedLaneMaterializer().get(
        branch_id=branch_id,
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
    model = reify_oig_root_model(
        index=runtime_context.runtime_index,
        opg=opg,
        oig=target_oig,
        model_type=model_type,
        root_id=root_id,
        branch_id=branch_id,
    )
    if model is None:
        return None
    return model, cast(JsonObject, target_head)


def _projection_lookup_key(value: object) -> str:
    text = str(value or "").strip().casefold()
    return "".join(char for char in text if char.isalnum())


def _require_named_projection(
    *, runtime_index: MetaGraphRuntimeIndex, name: str
) -> Any:
    requested = str(name or "").strip()
    exact_matches = [
        candidate
        for candidate in getattr(
            getattr(runtime_index, "ocg", None), "object_projection_graphs", []
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
                getattr(runtime_index, "ocg", None), "object_projection_graphs", []
            )
            or []
            if _projection_lookup_key(getattr(candidate, "name", "")) == requested_key
        ]
    if not matches:
        raise ValueError(
            f"Attention projection `{name}` is missing from runtime index."
        )
    if len(matches) != 1:
        raise ValueError(
            f"Attention projection `{name}` is ambiguous in runtime index: expected 1, found {len(matches)}"
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
                runtime_index, "class_configs_by_id", {}
            ).values()
            if str(getattr(class_config, "name", "") or "") == class_name
            and "attention" in str(getattr(class_config, "class_fqn", "") or "")
        ]
    if not matches:
        class_name = class_fqn.rsplit(".", 1)[-1]
        matches = [
            class_config
            for class_config in getattr(
                runtime_index, "class_configs_by_id", {}
            ).values()
            if str(getattr(class_config, "name", "") or "") == class_name
        ]
    if not matches:
        raise ValueError(
            f"Attention class config `{class_fqn}` is missing from runtime index."
        )
    if len(matches) != 1:
        raise ValueError(
            f"Attention class config `{class_fqn}` is ambiguous in runtime index: expected 1, found {len(matches)}"
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
            f"Attention function `{class_fqn}.{name}` is missing from runtime index."
        )
    if len(function_ids) != 1:
        raise ValueError(
            "Attention function "
            + f"`{class_fqn}.{name}` is ambiguous in runtime index: "
            + f"expected 1, found {len(function_ids)}"
        )
    return function_ids[0]


def _require_projection_hash(candidate: object, *, label: str) -> str:
    projection_hash = str(getattr(candidate, "projection_hash", "") or "").strip()
    if not projection_hash:
        raise ValueError(
            f"Attention projection `{label}` could not resolve projection hash from runtime index."
        )
    return projection_hash


def _service_focus_scope_id_for_section(*, section_id: UUID) -> UUID:
    return uuid5(
        NAMESPACE_URL,
        f"aware:attention:service:focus_scope:{section_id}",
    )


def _activation_scope_focus_scope_id(activation_scope: object | None) -> UUID | None:
    if activation_scope is None:
        return None
    return cast(UUID | None, getattr(activation_scope, "focus_scope_id", None))


def _activation_scope_focus_target(
    activation_scope: object | None,
) -> AttentionSectionFocusTarget | None:
    if activation_scope is None:
        return None
    focus_target = getattr(activation_scope, "focus_target", None)
    if focus_target is None:
        return None
    if isinstance(focus_target, AttentionSectionFocusTarget):
        return focus_target
    return AttentionSectionFocusTarget.model_validate(focus_target)


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_required_text(value: str, *, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} is required")
    return normalized


def _labelize_key(value: str) -> str:
    parts = [
        part.strip() for part in value.replace("-", "_").split("_") if part.strip()
    ]
    if not parts:
        return "Section"
    return " ".join(part[0].upper() + part[1:] for part in parts)


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace(
            "+00:00",
            "Z",
        )
    )


def _convert_model(value: object, *, model_cls: type[BaseModel]) -> Any:
    payload = value
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json", exclude_none=True)
    return model_cls.model_validate(payload)


def _request_id(value: object) -> Any:
    return getattr(value, "request_id", None)


__all__ = [
    "build_aware_attention_service_protocol_handler",
]
