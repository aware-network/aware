from __future__ import annotations

import asyncio
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from collections.abc import Mapping
from typing import Protocol, cast
from uuid import UUID, uuid4

from aware_code.types import JsonArray, JsonValue

from aware_service_service_dto.comms.models.service import (
    RequestStatus,
    ServiceOperationRequest,
    ServiceOperationResponse,
    StreamLifecycle,
)
from pydantic import model_validator

from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.contract import CommitActionDescriptor
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.instance.diff import diff_object_instance_graph_changes
from aware_meta.graph.instance.root import resolve_root_source_object_id

from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph

from aware_meta_service_dto.runtime.temporal_mutation_service_operation import (
    TemporalMutationDiagnostic,
    TemporalMutationServiceOperation,
)
from aware_meta_service.temporal_mutation_admission import (
    DenyAllTemporalMutationAdmissionPolicy,
    TemporalMutationAdmissionPolicy,
    TemporalMutationAdmissionRequest,
)
from aware_service_runtime.temporal_mutation_error_codes import (
    TEMPORAL_MUTATION_SERVICE_ERROR_CODE_DEFINITIONS,
    TemporalMutationServiceErrorCode,
)
from aware_service_runtime.error_codes import (
    ErrorCodeRegistry,
    RegisteredErrorCodeDefinition,
)

from aware_utils.logging import logger

_SYSTEM_ACTOR_ID = UUID(int=0)
_TEMPORAL_MUTATION_ERROR_REGISTRY = ErrorCodeRegistry(
    definitions=TEMPORAL_MUTATION_SERVICE_ERROR_CODE_DEFINITIONS,
)
_TEMPORAL_MUTATION_ERROR_DEFINITIONS_BY_CODE = {
    definition.code: definition
    for definition in _TEMPORAL_MUTATION_ERROR_REGISTRY.definitions
}


class _TemporalMutationGraphContextGateway(Protocol):
    async def resolve_graph_context(self) -> object: ...


class _TemporalMutationMetaTemporalGraphRoute(Protocol):
    async def invoke_temporal_function(self, **kwargs: object) -> object: ...


class ServiceOperationTransport(Protocol):
    async def send_service_response(
        self,
        *,
        request: ServiceOperationRequest,
        response: ServiceOperationResponse,
    ) -> None: ...

    async def close_service_stream(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> None: ...

    async def get_graph_gateway(self) -> _TemporalMutationGraphContextGateway: ...

    async def get_meta_temporal_graph_route(
        self,
    ) -> _TemporalMutationMetaTemporalGraphRoute: ...


class TemporalMutationStateStore(Protocol):
    async def record_session_opened(
        self,
        *,
        session_id: UUID,
        branch_id: UUID,
        projection_hash: str,
        environment_id: UUID,
        process_id: UUID,
        thread_id: UUID,
        base_commit_id: UUID,
        base_graph_hash_post: str,
        overlay_graph_hash_post: str | None,
        overlay_oig_json: str | None,
        revision: int,
        status: str,
        writer_actor_id: UUID | None,
        writer_lease_expires_at: datetime | None,
        created_at: datetime,
        last_activity_at: datetime,
        last_apply_at: datetime | None,
        metadata: dict[str, object] | None = None,
    ) -> None: ...

    async def record_frame(
        self,
        *,
        session_id: UUID,
        frame_id: str,
        branch_id: UUID,
        projection_hash: str,
        revision: int,
        actor_id: UUID,
        function_id: UUID | None,
        object_id: UUID | None,
        idempotency_key: str | None,
        request_hash: str | None,
        graph_hash_pre: str | None,
        graph_hash_post: str | None,
        changes: list[object],
        payload: dict[str, object],
        created_at: datetime,
        overlay_graph_hash_post: str | None,
        overlay_oig_json: str | None,
        writer_actor_id: UUID | None,
        writer_lease_expires_at: datetime | None,
    ) -> None: ...

    async def record_session_tombstone(
        self,
        *,
        session_id: UUID,
        tombstone_id: str,
        branch_id: UUID,
        projection_hash: str,
        revision: int,
        operation: str,
        actor_id: UUID | None,
        finalized_commit_id: UUID | None,
        final_graph_hash_post: str | None,
        reason: str | None,
        closed_at: datetime,
        ttl_cleanup_at: datetime | None,
        payload: dict[str, object],
    ) -> None: ...


class ServiceOperationResult(ServiceOperationResponse):
    response_service_operation: TemporalMutationServiceOperation | None = None

    @model_validator(mode="after")
    def _sync_response_payload(self) -> "ServiceOperationResult":
        payload = self.response_payload
        response_service_operation = self.response_service_operation
        if payload is None and response_service_operation is not None:
            self.response_payload = cast(
                JsonValue,
                response_service_operation.model_dump(mode="json"),
            )
            return self
        if payload is not None and response_service_operation is None:
            self.response_service_operation = (
                _parse_temporal_mutation_service_operation(payload)
            )
            return self
        if payload is not None and response_service_operation is not None:
            if payload == response_service_operation.model_dump(mode="json"):
                return self
            raise TypeError(
                "ServiceOperationResult received mismatched response_payload and "
                "response_service_operation values."
            )
        return self


@dataclass(frozen=True, slots=True)
class _TemporalMutationRequestEnvelope:
    request: ServiceOperationRequest
    service_operation: TemporalMutationServiceOperation
    actor_id: UUID | None
    environment_id: UUID
    process_id: UUID
    thread_id: UUID
    branch_id: UUID
    projection_hash: str
    stream_target_id: UUID
    stream_correlation_id: UUID


def _parse_temporal_mutation_service_operation(
    payload: object,
) -> TemporalMutationServiceOperation:
    if isinstance(payload, TemporalMutationServiceOperation):
        return payload
    if isinstance(payload, Mapping):
        return TemporalMutationServiceOperation.model_validate(dict(payload))
    raise TypeError(
        "service operation payload is not a TemporalMutationServiceOperation"
    )


def _request_envelope_from_request(
    request: ServiceOperationRequest,
) -> _TemporalMutationRequestEnvelope:
    if request.service != "temporal_mutation":
        raise TypeError(
            f"Unsupported service for temporal mutation handler: {request.service!r}"
        )
    service_operation = _parse_temporal_mutation_service_operation(request.operation)
    stream_target_id = request.stream_target_id or UUID(int=0)
    stream_correlation_id = request.stream_correlation_id or uuid4()
    normalized_request = request
    if request.stream_target_id is None or request.stream_correlation_id is None:
        normalized_request = request.model_copy(
            update={
                "stream_target_id": stream_target_id,
                "stream_correlation_id": stream_correlation_id,
            }
        )
    return _TemporalMutationRequestEnvelope(
        request=normalized_request,
        service_operation=service_operation,
        actor_id=request.context.actor_id,
        environment_id=request.context.environment_id,
        process_id=request.context.process_id,
        thread_id=request.context.thread_id,
        branch_id=request.context.branch_id,
        projection_hash=request.context.projection_hash,
        stream_target_id=stream_target_id,
        stream_correlation_id=stream_correlation_id,
    )


def _build_temporal_mutation_diagnostic(
    *,
    operation: str,
    error_code: str,
    error: str,
    session_id: UUID | None,
    branch_id: UUID | None,
    projection_hash: str | None,
    revision: int | None,
) -> TemporalMutationDiagnostic:
    definition = _temporal_mutation_error_definition_for(error_code)
    return TemporalMutationDiagnostic(
        code=definition.code,
        severity=definition.default_severity.value,
        summary=error,
        context={
            key: str(value) if isinstance(value, UUID) else value
            for key, value in {
                "service": "temporal_mutation",
                "operation": operation,
                "session_id": session_id,
                "branch_id": branch_id,
                "projection_hash": projection_hash,
                "revision": revision,
            }.items()
            if value is not None
        },
    )


def _temporal_mutation_error_definition_for(
    error_code: str,
) -> RegisteredErrorCodeDefinition:
    normalized = str(error_code or "").strip()
    definition = _TEMPORAL_MUTATION_ERROR_DEFINITIONS_BY_CODE.get(normalized)
    if definition is None:
        raise ValueError(f"Unknown temporal mutation error code: {normalized}")
    return definition


def _resolve_author_id(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        return UUID(value)
    return _SYSTEM_ACTOR_ID


def _is_graph_catalog_like(value: object) -> bool:
    return all(
        hasattr(value, attr)
        for attr in (
            "ocg",
            "opg_by_hash",
            "attribute_configs_by_id",
            "class_configs_by_id",
        )
    )


@dataclass(frozen=True, slots=True)
class _StreamSubscriber:
    node_id: UUID
    network_operation_id: UUID
    env_req: _TemporalMutationRequestEnvelope


@dataclass(frozen=True, slots=True)
class _TemporalFrame:
    revision: int
    actor_id: UUID
    changes: list[JsonValue]
    graph_hash_pre: str | None
    graph_hash_post: str | None
    created_at: datetime


@dataclass(slots=True)
class _TemporalSession:
    session_id: UUID
    branch_id: UUID
    projection_hash: str
    base_commit_id: UUID
    base_graph_hash_post: str
    base_oig: ObjectInstanceGraph
    overlay_oig: ObjectInstanceGraph
    revision: int
    created_at: datetime
    last_activity_at: datetime
    last_apply_at: datetime | None
    writer_actor_id: UUID | None
    writer_lease_expires_at: datetime | None
    frames: list[_TemporalFrame]
    subscribers: list[_StreamSubscriber]
    lock: asyncio.Lock


class TemporalMutationServicePlugin:
    service = "temporal_mutation"

    def __init__(
        self,
        *,
        transport: ServiceOperationTransport,
        session_ttl_seconds: int | None = None,
        max_sessions: int | None = None,
        max_subscribers_per_session: int | None = None,
        max_change_trees_per_apply: int | None = None,
        min_apply_interval_ms: int | None = None,
        max_frames_per_session: int | None = None,
        max_frame_bytes: int | None = None,
        writer_lease_seconds: int | None = None,
        state_store: TemporalMutationStateStore | None = None,
        admission_policy: TemporalMutationAdmissionPolicy | None = None,
    ):
        self._transport = transport
        self._state_store = state_store
        self._admission_policy = (
            admission_policy or DenyAllTemporalMutationAdmissionPolicy()
        )
        self._materializer = OIGMaterializer()
        self._committer = FSLaneCommitter()
        self._sessions: dict[UUID, _TemporalSession] = {}
        self._sessions_by_lane: dict[tuple[UUID, str], UUID] = {}
        self._lock = asyncio.Lock()
        self._session_ttl = timedelta(
            seconds=(
                session_ttl_seconds
                if session_ttl_seconds is not None
                else int(
                    os.getenv("AWARE_TEMPORAL_MUTATION_SESSION_TTL_SECONDS", "1200")
                )
            )
        )
        self._max_sessions = (
            max_sessions
            if max_sessions is not None
            else int(os.getenv("AWARE_TEMPORAL_MUTATION_MAX_SESSIONS", "256"))
        )
        self._max_subscribers_per_session = (
            max_subscribers_per_session
            if max_subscribers_per_session is not None
            else int(
                os.getenv("AWARE_TEMPORAL_MUTATION_MAX_SUBSCRIBERS_PER_SESSION", "64")
            )
        )
        self._max_change_trees_per_apply = (
            max_change_trees_per_apply
            if max_change_trees_per_apply is not None
            else int(
                os.getenv("AWARE_TEMPORAL_MUTATION_MAX_CHANGE_TREES_PER_APPLY", "200")
            )
        )
        self._min_apply_interval_ms = (
            min_apply_interval_ms
            if min_apply_interval_ms is not None
            else int(os.getenv("AWARE_TEMPORAL_MUTATION_MIN_APPLY_INTERVAL_MS", "0"))
        )
        self._max_frames_per_session = (
            max_frames_per_session
            if max_frames_per_session is not None
            else int(
                os.getenv("AWARE_TEMPORAL_MUTATION_MAX_FRAMES_PER_SESSION", "2048")
            )
        )
        self._max_frame_bytes = (
            max_frame_bytes
            if max_frame_bytes is not None
            else int(os.getenv("AWARE_TEMPORAL_MUTATION_MAX_FRAME_BYTES", "0"))
        )
        self._writer_lease = timedelta(
            seconds=(
                writer_lease_seconds
                if writer_lease_seconds is not None
                else int(
                    os.getenv("AWARE_TEMPORAL_MUTATION_WRITER_LEASE_SECONDS", "30")
                )
            )
        )

    async def handle_request(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> ServiceOperationResult:
        env_req = _request_envelope_from_request(request)
        network_operation_id = env_req.stream_correlation_id
        node_id = env_req.stream_target_id
        service_op = env_req.service_operation
        if not isinstance(service_op, TemporalMutationServiceOperation):
            return ServiceOperationResult(
                status=RequestStatus.failed,
                error="service_operation is not a TemporalMutationServiceOperation",
                stream_lifecycle=StreamLifecycle.auto_close,
            )

        await self._evict_expired_sessions()

        op_kind = (service_op.operation or "open_session").strip().lower()
        if op_kind == "open_session":
            return await self._open_session(
                network_operation_id=network_operation_id,
                env_req=env_req,
                node_id=node_id,
                service_op=service_op,
            )
        if op_kind == "subscribe":
            return await self._subscribe(
                network_operation_id=network_operation_id,
                env_req=env_req,
                node_id=node_id,
                service_op=service_op,
            )
        if op_kind == "unsubscribe":
            return await self._unsubscribe(
                network_operation_id=network_operation_id,
                env_req=env_req,
                node_id=node_id,
                service_op=service_op,
            )
        if op_kind == "acquire_writer":
            return await self._acquire_writer(
                network_operation_id=network_operation_id,
                env_req=env_req,
                node_id=node_id,
                service_op=service_op,
            )
        if op_kind == "release_writer":
            return await self._release_writer(
                network_operation_id=network_operation_id,
                env_req=env_req,
                node_id=node_id,
                service_op=service_op,
            )
        if op_kind == "apply":
            return await self._apply(
                network_operation_id=network_operation_id,
                env_req=env_req,
                node_id=node_id,
                service_op=service_op,
            )
        if op_kind == "finalize":
            return await self._finalize(
                network_operation_id=network_operation_id,
                env_req=env_req,
                node_id=node_id,
                service_op=service_op,
            )
        if op_kind == "close":
            return await self._close(
                network_operation_id=network_operation_id,
                env_req=env_req,
                node_id=node_id,
                service_op=service_op,
            )

        return self._failed_result(
            operation=service_op.operation or "unknown",
            error_code=TemporalMutationServiceErrorCode.unsupported_operation.value,
            error=f"Unsupported temporal_mutation operation: {service_op.operation}",
        )

    async def handle_notification(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> None:
        _ = request
        return

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(UTC)

    def _session_payload(self, *, session: _TemporalSession) -> dict[str, object]:
        participant_actor_ids = sorted(
            {
                str(sub.env_req.actor_id)
                for sub in session.subscribers
                if sub.env_req.actor_id is not None
            }
        )
        return {
            "writer_actor_id": (
                str(session.writer_actor_id)
                if session.writer_actor_id is not None
                else None
            ),
            "writer_lease_expires_at": (
                session.writer_lease_expires_at.isoformat()
                if session.writer_lease_expires_at is not None
                else None
            ),
            "writer_lease_enabled": self._writer_lease_enabled(),
            "subscriber_count": len(session.subscribers),
            "participant_actor_ids": participant_actor_ids,
        }

    def _finalize_payload(
        self,
        *,
        session: _TemporalSession,
        actor_id: UUID,
        finalized_commit_id: UUID | None,
        final_graph_hash_post: str | None,
    ) -> dict[str, object]:
        frame_count = len(session.frames)
        first_revision = session.frames[0].revision if session.frames else None
        last_revision = session.frames[-1].revision if session.frames else None
        return {
            **self._session_payload(session=session),
            "temporal_finalize": {
                "source": "temporal_session_finalize",
                "session_id": str(session.session_id),
                "branch_id": str(session.branch_id),
                "projection_hash": session.projection_hash,
                "base_commit_id": str(session.base_commit_id),
                "finalized_commit_id": (
                    str(finalized_commit_id)
                    if finalized_commit_id is not None
                    else None
                ),
                "base_graph_hash_post": session.base_graph_hash_post,
                "final_graph_hash_post": final_graph_hash_post,
                "revision": session.revision,
                "frame_count": frame_count,
                "first_frame_revision": first_revision,
                "last_frame_revision": last_revision,
                "first_frame_id": (
                    self._frame_id(
                        session_id=session.session_id,
                        revision=first_revision,
                    )
                    if first_revision is not None
                    else None
                ),
                "last_frame_id": (
                    self._frame_id(
                        session_id=session.session_id,
                        revision=last_revision,
                    )
                    if last_revision is not None
                    else None
                ),
                "actor_id": str(actor_id),
            },
        }

    def _overlay_oig_json(self, *, session: _TemporalSession) -> str:
        return json.dumps(
            session.overlay_oig.model_dump(mode="json"),
            separators=(",", ":"),
            sort_keys=True,
        )

    @staticmethod
    def _frame_id(*, session_id: UUID, revision: int) -> str:
        return f"{session_id}:{revision:012d}"

    @staticmethod
    def _tombstone_id(*, session_id: UUID, operation: str) -> str:
        return f"{session_id}:{operation.strip().lower() or 'closed'}"

    @staticmethod
    def _request_hash(service_op: TemporalMutationServiceOperation) -> str:
        payload = json.dumps(
            service_op.model_dump(mode="json"),
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _request_idempotency_key(
        env_req: _TemporalMutationRequestEnvelope,
    ) -> str | None:
        value = getattr(env_req.request, "network_request_id", None)
        return str(value) if value is not None else None

    @staticmethod
    def _json_safe_admission_context(
        values: Mapping[str, object],
    ) -> dict[str, object]:
        safe: dict[str, object] = {}
        for key, value in values.items():
            if isinstance(value, UUID):
                safe[key] = str(value)
                continue
            if isinstance(value, datetime):
                safe[key] = value.isoformat()
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                safe[key] = value
                continue
            safe[key] = str(value)
        return safe

    @staticmethod
    def _admission_request(
        *,
        operation: str,
        env_req: _TemporalMutationRequestEnvelope,
        service_op: TemporalMutationServiceOperation,
        session: _TemporalSession | None = None,
        branch_id: UUID | None = None,
        projection_hash: str | None = None,
    ) -> TemporalMutationAdmissionRequest:
        resolved_actor_id = service_op.actor_id or env_req.actor_id
        resolved_branch_id = (
            branch_id
            or (session.branch_id if session is not None else None)
            or service_op.branch_id
            or env_req.branch_id
        )
        resolved_projection_hash = (
            projection_hash
            or (session.projection_hash if session is not None else None)
            or service_op.projection_hash
            or env_req.projection_hash
        )
        return TemporalMutationAdmissionRequest(
            operation=operation,
            actor_id=resolved_actor_id,
            environment_id=env_req.environment_id,
            process_id=env_req.process_id,
            thread_id=env_req.thread_id,
            branch_id=resolved_branch_id,
            projection_hash=resolved_projection_hash,
            session_id=(
                service_op.session_id
                or (session.session_id if session is not None else None)
            ),
            base_commit_id=service_op.base_commit_id,
            revision=service_op.revision,
            expected_revision=service_op.expected_revision,
            from_revision=service_op.from_revision,
            function_id=service_op.function_id,
            object_id=service_op.object_id,
            commit_message=service_op.commit_message,
            session_revision=session.revision if session is not None else None,
            session_base_commit_id=(
                session.base_commit_id if session is not None else None
            ),
            session_writer_actor_id=(
                session.writer_actor_id if session is not None else None
            ),
            writer_lease_expires_at=(
                session.writer_lease_expires_at if session is not None else None
            ),
            subscriber_count=(
                len(session.subscribers) if session is not None else None
            ),
        )

    def _admission_failed_result(
        self,
        *,
        operation: str,
        error: str,
        error_code: str,
        request: TemporalMutationAdmissionRequest,
        session: _TemporalSession | None,
        context: Mapping[str, object] | None = None,
    ) -> ServiceOperationResult:
        payload = {
            "admission": {
                "allowed": False,
                "reason": error,
                "context": self._json_safe_admission_context(context or {}),
            }
        }
        return self._failed_result(
            operation=operation,
            session_id=request.session_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            revision=(
                session.revision
                if session is not None
                else request.session_revision or request.revision
            ),
            error_code=error_code,
            error=error,
            payload=cast(JsonValue, payload),
        )

    async def _ensure_admitted(
        self,
        *,
        operation: str,
        env_req: _TemporalMutationRequestEnvelope,
        service_op: TemporalMutationServiceOperation,
        session: _TemporalSession | None = None,
        branch_id: UUID | None = None,
        projection_hash: str | None = None,
    ) -> ServiceOperationResult | None:
        request = self._admission_request(
            operation=operation,
            env_req=env_req,
            service_op=service_op,
            session=session,
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        try:
            decision = await self._admission_policy.authorize(request)
        except Exception as exc:
            return self._admission_failed_result(
                operation=operation,
                request=request,
                session=session,
                error_code=TemporalMutationServiceErrorCode.admission_denied.value,
                error=f"Temporal mutation admission policy failed: {exc}",
                context={"policy_error": exc},
            )
        if decision.allowed:
            return None
        return self._admission_failed_result(
            operation=operation,
            request=request,
            session=session,
            error_code=decision.error_code,
            error=decision.reason or "Temporal mutation admission denied.",
            context=decision.context,
        )

    async def _persist_session_opened(
        self,
        *,
        env_req: _TemporalMutationRequestEnvelope,
        session: _TemporalSession,
    ) -> ServiceOperationResult | None:
        state_store = self._state_store
        if state_store is None:
            return None
        try:
            await state_store.record_session_opened(
                session_id=session.session_id,
                branch_id=session.branch_id,
                projection_hash=session.projection_hash,
                environment_id=env_req.environment_id,
                process_id=env_req.process_id,
                thread_id=env_req.thread_id,
                base_commit_id=session.base_commit_id,
                base_graph_hash_post=session.base_graph_hash_post,
                overlay_graph_hash_post=session.overlay_oig.hash,
                overlay_oig_json=self._overlay_oig_json(session=session),
                revision=session.revision,
                status="open",
                writer_actor_id=session.writer_actor_id,
                writer_lease_expires_at=session.writer_lease_expires_at,
                created_at=session.created_at,
                last_activity_at=session.last_activity_at,
                last_apply_at=session.last_apply_at,
                metadata=self._session_payload(session=session),
            )
        except Exception as exc:
            return self._failed_result(
                operation="open_session",
                session_id=session.session_id,
                branch_id=session.branch_id,
                projection_hash=session.projection_hash,
                revision=session.revision,
                error_code=TemporalMutationServiceErrorCode.invocation_failed.value,
                error=f"Temporal session durable state write failed: {exc}",
                payload=self._session_payload(session=session),
            )
        return None

    async def _persist_frame(
        self,
        *,
        env_req: _TemporalMutationRequestEnvelope,
        session: _TemporalSession,
        frame_record: _TemporalFrame,
        service_op: TemporalMutationServiceOperation,
        payload: dict[str, object],
    ) -> ServiceOperationResult | None:
        state_store = self._state_store
        if state_store is None:
            return None
        try:
            await state_store.record_frame(
                session_id=session.session_id,
                frame_id=self._frame_id(
                    session_id=session.session_id,
                    revision=frame_record.revision,
                ),
                branch_id=session.branch_id,
                projection_hash=session.projection_hash,
                revision=frame_record.revision,
                actor_id=frame_record.actor_id,
                function_id=service_op.function_id,
                object_id=service_op.object_id,
                idempotency_key=self._request_idempotency_key(env_req),
                request_hash=self._request_hash(service_op),
                graph_hash_pre=frame_record.graph_hash_pre,
                graph_hash_post=frame_record.graph_hash_post,
                changes=list(frame_record.changes),
                payload=payload,
                created_at=frame_record.created_at,
                overlay_graph_hash_post=session.overlay_oig.hash,
                overlay_oig_json=self._overlay_oig_json(session=session),
                writer_actor_id=session.writer_actor_id,
                writer_lease_expires_at=session.writer_lease_expires_at,
            )
        except Exception as exc:
            return self._failed_result(
                operation="apply",
                session_id=session.session_id,
                branch_id=session.branch_id,
                projection_hash=session.projection_hash,
                revision=session.revision,
                error_code=TemporalMutationServiceErrorCode.invocation_failed.value,
                error=f"Temporal frame durable state write failed: {exc}",
                payload=self._session_payload(session=session),
            )
        return None

    async def _persist_tombstone(
        self,
        *,
        session: _TemporalSession,
        operation: str,
        actor_id: UUID | None,
        finalized_commit_id: UUID | None,
        final_graph_hash_post: str | None,
        reason: str | None,
        payload: dict[str, object],
    ) -> None:
        state_store = self._state_store
        if state_store is None:
            return
        try:
            closed_at = self._utcnow()
            await state_store.record_session_tombstone(
                session_id=session.session_id,
                tombstone_id=self._tombstone_id(
                    session_id=session.session_id,
                    operation=operation,
                ),
                branch_id=session.branch_id,
                projection_hash=session.projection_hash,
                revision=session.revision,
                operation=operation,
                actor_id=actor_id,
                finalized_commit_id=finalized_commit_id,
                final_graph_hash_post=final_graph_hash_post,
                reason=reason,
                closed_at=closed_at,
                ttl_cleanup_at=(
                    closed_at + self._session_ttl
                    if self._session_ttl.total_seconds() > 0
                    else None
                ),
                payload=payload,
            )
        except Exception as exc:
            logger.warning(
                "[temporal_mutation] failed to write temporal session tombstone: "
                f"session_id={session.session_id} operation={operation} error={exc}"
            )

    def _writer_lease_enabled(self) -> bool:
        # v0 policy: single-writer lease.
        #
        # Motivation: For collaborative text editing, our current mutation ops are
        # not convergent across concurrent writers (no OT/CRDT). Without a lease,
        # "server-ordered multi-writer" effectively becomes last-write-wins and
        # will surprise users.
        #
        # Future: When we add OT/CRDT (or an equivalent convergent patch model),
        # multi-writer can be enabled by setting:
        #   AWARE_TEMPORAL_MUTATION_WRITER_LEASE_SECONDS=0
        return self._writer_lease.total_seconds() > 0

    def _ensure_writer_lease(
        self,
        *,
        session: _TemporalSession,
        author_id: UUID,
        now: datetime,
        operation: str,
    ) -> ServiceOperationResult | None:
        if not self._writer_lease_enabled():
            return None

        # Expire old leases to allow hand-off.
        if (
            session.writer_actor_id is not None
            and session.writer_lease_expires_at is not None
        ):
            if now >= session.writer_lease_expires_at:
                session.writer_actor_id = None
                session.writer_lease_expires_at = None

        if session.writer_actor_id is None:
            session.writer_actor_id = author_id
            session.writer_lease_expires_at = now + self._writer_lease
            return None

        if session.writer_actor_id != author_id:
            until = session.writer_lease_expires_at
            until_str = until.isoformat() if until is not None else "unknown"
            return self._failed_result(
                operation=operation,
                session_id=session.session_id,
                branch_id=session.branch_id,
                projection_hash=session.projection_hash,
                revision=session.revision,
                error_code=TemporalMutationServiceErrorCode.not_writer.value,
                error=(
                    "Temporal session is single-writer: apply rejected because another actor holds the lease. "
                    f"writer_actor_id={session.writer_actor_id} lease_expires_at={until_str}"
                ),
                payload=self._session_payload(session=session),
            )

        # Refresh lease for the active writer.
        session.writer_lease_expires_at = now + self._writer_lease
        return None

    @staticmethod
    def _failed_result(
        *,
        operation: str,
        error_code: str,
        error: str,
        session_id: UUID | None = None,
        branch_id: UUID | None = None,
        projection_hash: str | None = None,
        revision: int | None = None,
        payload: JsonValue | None = None,
    ) -> ServiceOperationResult:
        diagnostic = _build_temporal_mutation_diagnostic(
            operation=operation,
            error_code=error_code,
            error=error,
            session_id=session_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            revision=revision,
        )
        return ServiceOperationResult(
            status=RequestStatus.failed,
            error=error,
            response_service_operation=TemporalMutationServiceOperation(
                operation=operation,
                session_id=session_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
                revision=revision,
                status="failed",
                error_code=error_code,
                error=error,
                diagnostic=diagnostic,
                payload=payload,
            ),
            stream_lifecycle=StreamLifecycle.auto_close,
        )

    def _json_size_bytes(self, obj: object) -> int:
        # v0 safety: a best-effort cap for websocket payload sizes.
        # Note: this is not a perfect proxy for wire size (encoding + envelope),
        # but it is sufficient to prevent pathological change payloads.
        try:
            return len(
                json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode(
                    "utf-8"
                )
            )
        except Exception:
            # If we can't measure reliably, treat as oversized.
            return 1 << 60

    async def _evict_expired_sessions(self) -> None:
        # v0 safety: temporal sessions are in-memory overlays and are never SSOT.
        # Ensure we don't leak them indefinitely.
        if self._session_ttl.total_seconds() <= 0:
            return

        now = self._utcnow()
        expired: list[tuple[UUID, _TemporalSession]] = []

        async with self._lock:
            for sid, sess in list(self._sessions.items()):
                if sess.lock.locked():
                    continue
                if now - sess.last_activity_at > self._session_ttl:
                    expired.append((sid, sess))

        for sid, sess in expired:
            try:
                logger.info(
                    "[temporal_mutation] evicting expired session: "
                    f"session_id={sid} branch_id={sess.branch_id} projection_hash={sess.projection_hash}"
                )
                await self._persist_tombstone(
                    session=sess,
                    operation="evicted",
                    actor_id=None,
                    finalized_commit_id=None,
                    final_graph_hash_post=sess.overlay_oig.hash,
                    reason="ttl_expired",
                    payload=self._session_payload(session=sess),
                )
                await self._close_session(session_id=sid, session=sess)
            except Exception as exc:
                logger.warning(
                    f"[temporal_mutation] failed to evict expired session {sid}: {exc}"
                )

    @staticmethod
    def _resolve_lane_key(
        *,
        env_req: _TemporalMutationRequestEnvelope,
        service_op: TemporalMutationServiceOperation,
    ) -> tuple[UUID, str]:
        branch_id = service_op.branch_id or env_req.branch_id
        projection_hash = (
            service_op.projection_hash or env_req.projection_hash or ""
        ).strip()
        if branch_id is None:
            raise ValueError("branch_id is required for temporal mutation sessions")
        if not projection_hash:
            raise ValueError(
                "projection_hash is required for temporal mutation sessions"
            )
        return branch_id, projection_hash

    async def _get_opg(self, *, index: object, projection_hash: str):
        opg_by_hash = getattr(index, "opg_by_hash", None)
        if not isinstance(opg_by_hash, Mapping):
            raise ValueError("Graph catalog does not expose opg_by_hash")
        opg = opg_by_hash.get(projection_hash)
        if opg is None:
            raise ValueError(
                f"ObjectProjectionGraph not found for projection_hash={projection_hash}"
            )
        return opg

    async def _broadcast_frame(
        self, *, session: _TemporalSession, frame: TemporalMutationServiceOperation
    ) -> None:
        subscribers = list(session.subscribers)
        failed_ids: set[UUID] = set()
        for sub in subscribers:
            try:
                await self._transport.send_service_response(
                    request=sub.env_req.request,
                    response=ServiceOperationResult(
                        status=RequestStatus.succeeded,
                        response_service_operation=frame,
                        stream_lifecycle=StreamLifecycle.started,
                    ),
                )
            except Exception as exc:
                logger.warning(
                    f"[temporal_mutation] failed to stream frame to subscriber: {exc}"
                )
                failed_ids.add(sub.network_operation_id)

        # Best-effort prune of dead subscribers.
        if failed_ids:
            session.subscribers = [
                s
                for s in session.subscribers
                if s.network_operation_id not in failed_ids
            ]

    async def _close_session_streams(self, *, session: _TemporalSession) -> None:
        subscribers = list(session.subscribers)
        session.subscribers.clear()
        for sub in subscribers:
            try:
                await self._transport.close_service_stream(
                    request=sub.env_req.request,
                )
            except Exception as exc:
                logger.warning(f"[temporal_mutation] failed to close stream: {exc}")

    async def _emit_session_state(self, *, session: _TemporalSession) -> None:
        # Lightweight collaboration “locker” updates: writer/lease changes must be visible
        # to subscribers even when no OIG changes are applied.
        if not session.subscribers:
            return
        try:
            await self._broadcast_frame(
                session=session,
                frame=TemporalMutationServiceOperation(
                    operation="session_state",
                    session_id=session.session_id,
                    branch_id=session.branch_id,
                    projection_hash=session.projection_hash,
                    base_commit_id=session.base_commit_id,
                    revision=session.revision,
                    payload=self._session_payload(session=session),
                    status="succeeded",
                ),
            )
        except Exception as exc:
            logger.warning(
                f"[temporal_mutation] failed to broadcast session_state: {exc}"
            )

    async def _open_session(
        self,
        *,
        network_operation_id: UUID,
        env_req: _TemporalMutationRequestEnvelope,
        node_id: UUID,
        service_op: TemporalMutationServiceOperation,
    ) -> ServiceOperationResult:
        _ = (network_operation_id, node_id)
        branch_id, projection_hash = self._resolve_lane_key(
            env_req=env_req, service_op=service_op
        )
        lane_key = (branch_id, projection_hash)
        now = self._utcnow()

        admission_error = await self._ensure_admitted(
            operation="open_session",
            env_req=env_req,
            service_op=service_op,
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        if admission_error is not None:
            return admission_error

        store = FSCommitStore()
        requested_base_commit_id = service_op.base_commit_id
        if requested_base_commit_id is None:
            head = await store.head(
                branch_id=branch_id, projection_hash=projection_hash
            )
            if head is None or not head.get("commit_id"):
                return self._failed_result(
                    operation="open_session",
                    session_id=service_op.session_id,
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    error_code=TemporalMutationServiceErrorCode.no_head_commit.value,
                    error="Lane has no HEAD commit; cannot open temporal session",
                )
            requested_base_commit_id = UUID(str(head["commit_id"]))

        stale_session: _TemporalSession | None = None
        async with self._lock:
            # Idempotency: reuse an existing lane session when present.
            existing_session_id = self._sessions_by_lane.get(lane_key)
            if existing_session_id is not None:
                existing = self._sessions.get(existing_session_id)
                if existing is not None:
                    # Sessions are overlays on top of a lane base head. If the lane
                    # head advanced (receipt commit), the overlay no longer has a
                    # valid base and must be closed (v0: no rebase/merge).
                    if existing.base_commit_id != requested_base_commit_id:
                        stale_session = existing
                        self._sessions.pop(existing_session_id, None)
                        if self._sessions_by_lane.get(lane_key) == existing_session_id:
                            self._sessions_by_lane.pop(lane_key, None)
                    else:
                        existing.last_activity_at = now
                        return ServiceOperationResult(
                            status=RequestStatus.succeeded,
                            error=None,
                            response_service_operation=TemporalMutationServiceOperation(
                                operation="open_session",
                                session_id=existing.session_id,
                                branch_id=existing.branch_id,
                                projection_hash=existing.projection_hash,
                                base_commit_id=existing.base_commit_id,
                                base_graph_hash_post=existing.base_graph_hash_post,
                                revision=existing.revision,
                                payload=self._session_payload(session=existing),
                                status="succeeded",
                            ),
                            stream_lifecycle=StreamLifecycle.auto_close,
                        )

            session_id = service_op.session_id or uuid4()
            if session_id in self._sessions:
                sess = self._sessions[session_id]
                if (
                    sess.branch_id != branch_id
                    or sess.projection_hash != projection_hash
                ):
                    return self._failed_result(
                        operation="open_session",
                        session_id=session_id,
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        error_code=TemporalMutationServiceErrorCode.session_id_lane_mismatch.value,
                        error="session_id already exists for a different lane",
                    )
                if sess.base_commit_id != requested_base_commit_id:
                    return self._failed_result(
                        operation="open_session",
                        session_id=session_id,
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        error_code=TemporalMutationServiceErrorCode.base_commit_mismatch.value,
                        error=(
                            "Session base_commit_id does not match lane head; "
                            f"session_base_commit_id={sess.base_commit_id} "
                            f"lane_head_commit_id={requested_base_commit_id}"
                        ),
                    )
                sess.last_activity_at = now
                return ServiceOperationResult(
                    status=RequestStatus.succeeded,
                    error=None,
                    response_service_operation=TemporalMutationServiceOperation(
                        operation="open_session",
                        session_id=sess.session_id,
                        branch_id=sess.branch_id,
                        projection_hash=sess.projection_hash,
                        base_commit_id=sess.base_commit_id,
                        base_graph_hash_post=sess.base_graph_hash_post,
                        revision=sess.revision,
                        payload=self._session_payload(session=sess),
                        status="succeeded",
                    ),
                    stream_lifecycle=StreamLifecycle.auto_close,
                )

            # Hard cap: prevent unbounded in-memory session growth.
            if self._max_sessions > 0 and len(self._sessions) >= self._max_sessions:
                return self._failed_result(
                    operation="open_session",
                    session_id=session_id,
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    error_code=TemporalMutationServiceErrorCode.too_many_sessions.value,
                    error="Too many temporal mutation sessions; close an existing session first",
                )

        if stale_session is not None:
            # Best-effort: notify subscribers and close streams so clients can
            # reopen against the new lane head.
            try:
                await self._broadcast_frame(
                    session=stale_session,
                    frame=TemporalMutationServiceOperation(
                        operation="closed",
                        session_id=stale_session.session_id,
                        branch_id=stale_session.branch_id,
                        projection_hash=stale_session.projection_hash,
                        base_commit_id=stale_session.base_commit_id,
                        revision=stale_session.revision,
                        status="failed",
                        error_code=TemporalMutationServiceErrorCode.head_advanced.value,
                        error=(
                            "Lane head advanced while a temporal session was open; "
                            "session closed. Reopen to continue editing."
                        ),
                        diagnostic=_build_temporal_mutation_diagnostic(
                            operation="closed",
                            error_code=TemporalMutationServiceErrorCode.head_advanced.value,
                            error=(
                                "Lane head advanced while a temporal session was open; "
                                "session closed. Reopen to continue editing."
                            ),
                            session_id=stale_session.session_id,
                            branch_id=stale_session.branch_id,
                            projection_hash=stale_session.projection_hash,
                            revision=stale_session.revision,
                        ),
                        payload={
                            **self._session_payload(session=stale_session),
                            "new_base_commit_id": str(requested_base_commit_id),
                        },
                    ),
                )
            except Exception as exc:
                logger.warning(
                    f"[temporal_mutation] failed to broadcast stale session close: {exc}"
                )
            await self._persist_tombstone(
                session=stale_session,
                operation="stale_head_advanced",
                actor_id=None,
                finalized_commit_id=None,
                final_graph_hash_post=stale_session.overlay_oig.hash,
                reason="head_advanced",
                payload={
                    **self._session_payload(session=stale_session),
                    "new_base_commit_id": str(requested_base_commit_id),
                },
            )
            await self._close_session_streams(session=stale_session)

        graph_gateway = await self._transport.get_graph_gateway()
        graph_context = await graph_gateway.resolve_graph_context()
        if not _is_graph_catalog_like(graph_context):
            return self._failed_result(
                operation="open_session",
                session_id=session_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
                error_code=TemporalMutationServiceErrorCode.graph_context_unavailable.value,
                error="Graph context is unavailable for temporal session open.",
            )
        index = graph_context
        opg = await self._get_opg(index=index, projection_hash=projection_hash)

        base_commit_id = requested_base_commit_id

        base_oig, _indexes = await self._materializer.get(
            branch_id=branch_id,
            ocg=index.ocg,
            opg=opg,
            commit_id=base_commit_id,
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
        )
        base_hash_post = base_oig.hash or ""
        if not base_hash_post:
            return self._failed_result(
                operation="open_session",
                session_id=session_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
                error_code=TemporalMutationServiceErrorCode.missing_graph_hash.value,
                error="Materialized base OIG is missing hash",
            )

        now = self._utcnow()
        session = _TemporalSession(
            session_id=session_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            base_commit_id=base_commit_id,
            base_graph_hash_post=base_hash_post,
            base_oig=base_oig,
            overlay_oig=base_oig.model_copy(deep=True),
            revision=0,
            created_at=now,
            last_activity_at=now,
            last_apply_at=None,
            writer_actor_id=None,
            writer_lease_expires_at=None,
            frames=[],
            subscribers=[],
            lock=asyncio.Lock(),
        )

        durability_error = await self._persist_session_opened(
            env_req=env_req,
            session=session,
        )
        if durability_error is not None:
            return durability_error

        async with self._lock:
            self._sessions[session_id] = session
            self._sessions_by_lane[lane_key] = session_id

        return ServiceOperationResult(
            status=RequestStatus.succeeded,
            error=None,
            response_service_operation=TemporalMutationServiceOperation(
                operation="open_session",
                session_id=session.session_id,
                branch_id=session.branch_id,
                projection_hash=session.projection_hash,
                base_commit_id=session.base_commit_id,
                base_graph_hash_post=session.base_graph_hash_post,
                revision=session.revision,
                payload=self._session_payload(session=session),
                status="succeeded",
            ),
            stream_lifecycle=StreamLifecycle.auto_close,
        )

    async def _subscribe(
        self,
        *,
        network_operation_id: UUID,
        env_req: _TemporalMutationRequestEnvelope,
        node_id: UUID,
        service_op: TemporalMutationServiceOperation,
    ) -> ServiceOperationResult:
        session_id = service_op.session_id
        if session_id is None:
            return self._failed_result(
                operation="subscribe",
                error_code=TemporalMutationServiceErrorCode.missing_session_id.value,
                error="TemporalMutationServiceOperation.session_id is required for subscribe",
            )

        async with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            return self._failed_result(
                operation="subscribe",
                session_id=session_id,
                error_code=TemporalMutationServiceErrorCode.session_not_found.value,
                error="Session not found",
            )

        admission_error = await self._ensure_admitted(
            operation="subscribe",
            env_req=env_req,
            service_op=service_op,
            session=session,
        )
        if admission_error is not None:
            return admission_error

        async with session.lock:
            now = self._utcnow()
            session.last_activity_at = now

            # Idempotent per stream correlation id.
            existing = next(
                (
                    s
                    for s in session.subscribers
                    if s.network_operation_id == network_operation_id
                ),
                None,
            )
            if existing is None:
                if (
                    self._max_subscribers_per_session > 0
                    and len(session.subscribers) >= self._max_subscribers_per_session
                ):
                    return self._failed_result(
                        operation="subscribe",
                        session_id=session.session_id,
                        branch_id=session.branch_id,
                        projection_hash=session.projection_hash,
                        revision=session.revision,
                        error_code=TemporalMutationServiceErrorCode.too_many_subscribers.value,
                        error=(
                            "Too many subscribers for session: "
                            f"limit={self._max_subscribers_per_session}"
                        ),
                    )
                session.subscribers.append(
                    _StreamSubscriber(
                        node_id=node_id,
                        network_operation_id=network_operation_id,
                        env_req=env_req,
                    )
                )

            from_revision = service_op.from_revision
            if from_revision is not None and from_revision < 0:
                return self._failed_result(
                    operation="subscribe",
                    session_id=session.session_id,
                    branch_id=session.branch_id,
                    projection_hash=session.projection_hash,
                    revision=session.revision,
                    error_code=TemporalMutationServiceErrorCode.invalid_from_revision.value,
                    error="from_revision must be >= 0",
                )
            if from_revision is not None and from_revision > session.revision:
                return self._failed_result(
                    operation="subscribe",
                    session_id=session.session_id,
                    branch_id=session.branch_id,
                    projection_hash=session.projection_hash,
                    revision=session.revision,
                    error_code=TemporalMutationServiceErrorCode.revision_mismatch.value,
                    error=f"from_revision {from_revision} is ahead of session revision {session.revision}",
                )

            base_relative = from_revision is None
            from_revision = 0 if from_revision is None else int(from_revision)

            changes_payload: list[JsonValue] = []
            if session.revision > from_revision:
                if not base_relative:
                    if not session.frames:
                        return self._failed_result(
                            operation="subscribe",
                            session_id=session.session_id,
                            branch_id=session.branch_id,
                            projection_hash=session.projection_hash,
                            revision=session.revision,
                            error_code=TemporalMutationServiceErrorCode.replay_unavailable.value,
                            error="Session has no replay frames; resubscribe without from_revision",
                        )

                    min_frame_rev = session.frames[0].revision
                    needed_start = from_revision + 1
                    if needed_start < min_frame_rev:
                        return self._failed_result(
                            operation="subscribe",
                            session_id=session.session_id,
                            branch_id=session.branch_id,
                            projection_hash=session.projection_hash,
                            revision=session.revision,
                            error_code=TemporalMutationServiceErrorCode.reconnect_too_old.value,
                            error=(
                                "Requested from_revision is too old for the session replay buffer; "
                                f"from_revision={from_revision} min_available_revision={min_frame_rev}"
                            ),
                        )
                    if session.frames[-1].revision != session.revision:
                        return self._failed_result(
                            operation="subscribe",
                            session_id=session.session_id,
                            branch_id=session.branch_id,
                            projection_hash=session.projection_hash,
                            revision=session.revision,
                            error_code=TemporalMutationServiceErrorCode.replay_incomplete.value,
                            error="Session replay buffer is incomplete; resubscribe without from_revision",
                        )

                    for fr in session.frames:
                        if fr.revision > from_revision:
                            changes_payload.extend(fr.changes)
                else:
                    full_replay = (
                        session.frames
                        and session.frames[0].revision == 1
                        and session.frames[-1].revision == session.revision
                        and len(session.frames) == session.revision
                    )
                    if full_replay:
                        for fr in session.frames:
                            changes_payload.extend(fr.changes)
                    else:
                        changes = diff_object_instance_graph_changes(
                            old=session.base_oig,
                            new=session.overlay_oig,
                            created_at=datetime.now(UTC),
                        )
                        changes_payload = (
                            [
                                c.model_dump(mode="json", exclude_none=True)
                                for c in changes
                            ]
                            if changes
                            else []
                        )

            return ServiceOperationResult(
                status=RequestStatus.succeeded,
                error=None,
                response_service_operation=TemporalMutationServiceOperation(
                    operation="subscribe",
                    session_id=session.session_id,
                    branch_id=session.branch_id,
                    projection_hash=session.projection_hash,
                    base_commit_id=session.base_commit_id,
                    base_graph_hash_post=session.base_graph_hash_post,
                    revision=session.revision,
                    changes=JsonArray(changes_payload),
                    payload=self._session_payload(session=session),
                    status="succeeded",
                ),
                stream_lifecycle=StreamLifecycle.started,
            )

    async def _unsubscribe(
        self,
        *,
        network_operation_id: UUID,
        env_req: _TemporalMutationRequestEnvelope,
        node_id: UUID,
        service_op: TemporalMutationServiceOperation,
    ) -> ServiceOperationResult:
        _ = (network_operation_id, env_req)

        session_id = service_op.session_id
        if session_id is None:
            return self._failed_result(
                operation="unsubscribe",
                error_code=TemporalMutationServiceErrorCode.missing_session_id.value,
                error="TemporalMutationServiceOperation.session_id is required for unsubscribe",
            )

        async with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            return self._failed_result(
                operation="unsubscribe",
                session_id=session_id,
                error_code=TemporalMutationServiceErrorCode.session_not_found.value,
                error="Session not found",
            )

        admission_error = await self._ensure_admitted(
            operation="unsubscribe",
            env_req=env_req,
            service_op=service_op,
            session=session,
        )
        if admission_error is not None:
            return admission_error

        removed: list[_StreamSubscriber] = []
        async with session.lock:
            session.last_activity_at = self._utcnow()
            removed = [s for s in session.subscribers if s.node_id == node_id]
            if removed:
                session.subscribers = [
                    s for s in session.subscribers if s.node_id != node_id
                ]

        for sub in removed:
            try:
                await self._transport.close_service_stream(
                    request=sub.env_req.request,
                )
            except Exception as exc:
                logger.warning(
                    f"[temporal_mutation] failed to close unsubscribed stream: {exc}"
                )

        return ServiceOperationResult(
            status=RequestStatus.succeeded,
            error=None,
            response_service_operation=TemporalMutationServiceOperation(
                operation="unsubscribe",
                session_id=session.session_id,
                branch_id=session.branch_id,
                projection_hash=session.projection_hash,
                revision=session.revision,
                status="succeeded",
            ),
            stream_lifecycle=StreamLifecycle.auto_close,
        )

    async def _acquire_writer(
        self,
        *,
        network_operation_id: UUID,
        env_req: _TemporalMutationRequestEnvelope,
        node_id: UUID,
        service_op: TemporalMutationServiceOperation,
    ) -> ServiceOperationResult:
        _ = (network_operation_id, node_id)
        session_id = service_op.session_id
        if session_id is None:
            return self._failed_result(
                operation="acquire_writer",
                error_code=TemporalMutationServiceErrorCode.missing_session_id.value,
                error="TemporalMutationServiceOperation.session_id is required for acquire_writer",
            )

        async with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            return self._failed_result(
                operation="acquire_writer",
                session_id=session_id,
                error_code=TemporalMutationServiceErrorCode.session_not_found.value,
                error="Session not found",
            )

        admission_error = await self._ensure_admitted(
            operation="acquire_writer",
            env_req=env_req,
            service_op=service_op,
            session=session,
        )
        if admission_error is not None:
            return admission_error

        actor_id = service_op.actor_id or env_req.actor_id
        author_id = _resolve_author_id(actor_id)

        async with session.lock:
            now = self._utcnow()
            session.last_activity_at = now

            lease_error = self._ensure_writer_lease(
                session=session,
                author_id=author_id,
                now=now,
                operation="acquire_writer",
            )
            if lease_error is not None:
                return lease_error

            await self._emit_session_state(session=session)

            return ServiceOperationResult(
                status=RequestStatus.succeeded,
                error=None,
                response_service_operation=TemporalMutationServiceOperation(
                    operation="acquire_writer",
                    session_id=session.session_id,
                    branch_id=session.branch_id,
                    projection_hash=session.projection_hash,
                    base_commit_id=session.base_commit_id,
                    revision=session.revision,
                    actor_id=author_id,
                    payload=self._session_payload(session=session),
                    status="succeeded",
                ),
                stream_lifecycle=StreamLifecycle.auto_close,
            )

    async def _release_writer(
        self,
        *,
        network_operation_id: UUID,
        env_req: _TemporalMutationRequestEnvelope,
        node_id: UUID,
        service_op: TemporalMutationServiceOperation,
    ) -> ServiceOperationResult:
        _ = (network_operation_id, node_id)
        session_id = service_op.session_id
        if session_id is None:
            return self._failed_result(
                operation="release_writer",
                error_code=TemporalMutationServiceErrorCode.missing_session_id.value,
                error="TemporalMutationServiceOperation.session_id is required for release_writer",
            )

        async with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            return self._failed_result(
                operation="release_writer",
                session_id=session_id,
                error_code=TemporalMutationServiceErrorCode.session_not_found.value,
                error="Session not found",
            )

        admission_error = await self._ensure_admitted(
            operation="release_writer",
            env_req=env_req,
            service_op=service_op,
            session=session,
        )
        if admission_error is not None:
            return admission_error

        actor_id = service_op.actor_id or env_req.actor_id
        author_id = _resolve_author_id(actor_id)

        async with session.lock:
            now = self._utcnow()
            session.last_activity_at = now

            if self._writer_lease_enabled():
                # Expire old leases to allow hand-off.
                if (
                    session.writer_actor_id is not None
                    and session.writer_lease_expires_at is not None
                ):
                    if now >= session.writer_lease_expires_at:
                        session.writer_actor_id = None
                        session.writer_lease_expires_at = None

                if (
                    session.writer_actor_id is not None
                    and session.writer_actor_id != author_id
                ):
                    until = session.writer_lease_expires_at
                    until_str = until.isoformat() if until is not None else "unknown"
                    return self._failed_result(
                        operation="release_writer",
                        session_id=session.session_id,
                        branch_id=session.branch_id,
                        projection_hash=session.projection_hash,
                        revision=session.revision,
                        error_code=TemporalMutationServiceErrorCode.not_writer.value,
                        error=(
                            "Temporal session is single-writer: release rejected "
                            "because another actor holds the lease. "
                            f"writer_actor_id={session.writer_actor_id} lease_expires_at={until_str}"
                        ),
                        payload=self._session_payload(session=session),
                    )

                session.writer_actor_id = None
                session.writer_lease_expires_at = None

            await self._emit_session_state(session=session)

            return ServiceOperationResult(
                status=RequestStatus.succeeded,
                error=None,
                response_service_operation=TemporalMutationServiceOperation(
                    operation="release_writer",
                    session_id=session.session_id,
                    branch_id=session.branch_id,
                    projection_hash=session.projection_hash,
                    base_commit_id=session.base_commit_id,
                    revision=session.revision,
                    actor_id=author_id,
                    payload=self._session_payload(session=session),
                    status="succeeded",
                ),
                stream_lifecycle=StreamLifecycle.auto_close,
            )

    async def _apply(
        self,
        *,
        network_operation_id: UUID,
        env_req: _TemporalMutationRequestEnvelope,
        node_id: UUID,
        service_op: TemporalMutationServiceOperation,
    ) -> ServiceOperationResult:
        _ = (network_operation_id, node_id)

        session_id = service_op.session_id
        if session_id is None:
            return self._failed_result(
                operation="apply",
                error_code=TemporalMutationServiceErrorCode.missing_session_id.value,
                error="TemporalMutationServiceOperation.session_id is required for apply",
            )
        if service_op.function_id is None:
            return self._failed_result(
                operation="apply",
                session_id=session_id,
                error_code=TemporalMutationServiceErrorCode.missing_function_id.value,
                error="TemporalMutationServiceOperation.function_id is required for apply",
            )
        if service_op.object_id is None:
            return self._failed_result(
                operation="apply",
                session_id=session_id,
                error_code=TemporalMutationServiceErrorCode.missing_object_id.value,
                error="TemporalMutationServiceOperation.object_id is required for apply",
            )
        if env_req.process_id is None or env_req.thread_id is None:
            return self._failed_result(
                operation="apply",
                session_id=session_id,
                error_code=TemporalMutationServiceErrorCode.missing_attribution.value,
                error="process_id and thread_id are required for temporal apply (execution attribution)",
            )

        async with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            return self._failed_result(
                operation="apply",
                session_id=session_id,
                error_code=TemporalMutationServiceErrorCode.session_not_found.value,
                error="Session not found",
            )

        admission_error = await self._ensure_admitted(
            operation="apply",
            env_req=env_req,
            service_op=service_op,
            session=session,
        )
        if admission_error is not None:
            return admission_error

        actor_id = service_op.actor_id or env_req.actor_id
        author_id = _resolve_author_id(actor_id)

        graph_gateway = await self._transport.get_graph_gateway()
        graph_context = await graph_gateway.resolve_graph_context()
        if not _is_graph_catalog_like(graph_context):
            return self._failed_result(
                operation="apply",
                session_id=session_id,
                error_code=TemporalMutationServiceErrorCode.graph_context_unavailable.value,
                error="Graph context is unavailable for temporal apply.",
            )
        index = graph_context

        temporal_route = await self._transport.get_meta_temporal_graph_route()

        async with session.lock:
            now = self._utcnow()
            session.last_activity_at = now

            expected_rev = service_op.expected_revision
            if expected_rev is not None and expected_rev != session.revision:
                return self._failed_result(
                    operation="apply",
                    session_id=session.session_id,
                    branch_id=session.branch_id,
                    projection_hash=session.projection_hash,
                    revision=session.revision,
                    error_code=TemporalMutationServiceErrorCode.revision_mismatch.value,
                    error=f"Revision mismatch: expected={expected_rev} actual={session.revision}",
                )

            lease_error = self._ensure_writer_lease(
                session=session,
                author_id=author_id,
                now=now,
                operation="apply",
            )
            if lease_error is not None:
                return lease_error

            if (
                self._min_apply_interval_ms > 0
                and session.last_apply_at is not None
                and (now - session.last_apply_at).total_seconds() * 1000
                < self._min_apply_interval_ms
            ):
                delta_ms = int((now - session.last_apply_at).total_seconds() * 1000)
                wait_ms = max(self._min_apply_interval_ms - delta_ms, 0)
                return self._failed_result(
                    operation="apply",
                    session_id=session.session_id,
                    branch_id=session.branch_id,
                    projection_hash=session.projection_hash,
                    revision=session.revision,
                    error_code=TemporalMutationServiceErrorCode.rate_limited.value,
                    error=f"Apply rate limited; retry after {wait_ms}ms",
                )

            before_oig = session.overlay_oig
            expected_hash = before_oig.hash or ""

            try:
                invoke_resp = await temporal_route.invoke_temporal_function(
                    graph_context=index,
                    environment_id=env_req.environment_id,
                    process_id=env_req.process_id,
                    thread_id=env_req.thread_id,
                    actor_id=author_id,
                    domain_branch_id=session.branch_id,
                    domain_projection_hash=session.projection_hash,
                    before_oig=before_oig.model_dump(mode="json"),
                    target_object_id=service_op.object_id,
                    function_id=service_op.function_id,
                    args=list(service_op.args or []),
                    kwargs=dict(service_op.kwargs or {}),
                    expected_graph_hash_pre=expected_hash,
                    expected_head_commit_id=session.base_commit_id,
                )
            except Exception as exc:
                return ServiceOperationResult(
                    status=RequestStatus.failed,
                    error=str(exc),
                    response_service_operation=TemporalMutationServiceOperation(
                        operation="apply",
                        session_id=session.session_id,
                        revision=session.revision,
                        actor_id=author_id,
                        status="failed",
                        error_code=TemporalMutationServiceErrorCode.invocation_failed.value,
                        error=str(exc),
                        diagnostic=_build_temporal_mutation_diagnostic(
                            operation="apply",
                            error_code=TemporalMutationServiceErrorCode.invocation_failed.value,
                            error=str(exc),
                            session_id=session.session_id,
                            branch_id=session.branch_id,
                            projection_hash=session.projection_hash,
                            revision=session.revision,
                        ),
                        payload=self._session_payload(session=session),
                    ),
                    stream_lifecycle=StreamLifecycle.auto_close,
                )
            if invoke_resp.status != "succeeded":
                return ServiceOperationResult(
                    status=RequestStatus.failed,
                    error=invoke_resp.error or "Temporal apply failed",
                    response_service_operation=TemporalMutationServiceOperation(
                        operation="apply",
                        session_id=session.session_id,
                        revision=session.revision,
                        actor_id=author_id,
                        status="failed",
                        error_code=TemporalMutationServiceErrorCode.invocation_failed.value,
                        error=invoke_resp.error,
                        diagnostic=_build_temporal_mutation_diagnostic(
                            operation="apply",
                            error_code=TemporalMutationServiceErrorCode.invocation_failed.value,
                            error=invoke_resp.error
                            or "Temporal apply invocation failed.",
                            session_id=session.session_id,
                            branch_id=session.branch_id,
                            projection_hash=session.projection_hash,
                            revision=session.revision,
                        ),
                        payload=self._session_payload(session=session),
                    ),
                    stream_lifecycle=StreamLifecycle.auto_close,
                )
            after_oig_payload = getattr(invoke_resp, "after_oig", None)
            if after_oig_payload is None:
                return self._failed_result(
                    operation="apply",
                    session_id=session.session_id,
                    branch_id=session.branch_id,
                    projection_hash=session.projection_hash,
                    revision=session.revision,
                    error_code=TemporalMutationServiceErrorCode.invocation_failed.value,
                    error="Temporal apply response did not include after_oig.",
                )
            after_oig = ObjectInstanceGraph.model_validate(after_oig_payload)
            if not after_oig.hash and invoke_resp.graph_hash_post:
                after_oig.hash = invoke_resp.graph_hash_post

            changes = list(invoke_resp.changes or [])
            if (
                self._max_change_trees_per_apply > 0
                and len(changes) > self._max_change_trees_per_apply
            ):
                return self._failed_result(
                    operation="apply",
                    session_id=session.session_id,
                    branch_id=session.branch_id,
                    projection_hash=session.projection_hash,
                    revision=session.revision,
                    error_code=TemporalMutationServiceErrorCode.too_many_changes.value,
                    error=(
                        "Temporal apply produced too many changes: "
                        f"count={len(changes)} limit={self._max_change_trees_per_apply}"
                    ),
                )
            if self._max_frame_bytes > 0:
                size = self._json_size_bytes(changes)
                if size > self._max_frame_bytes:
                    return self._failed_result(
                        operation="apply",
                        session_id=session.session_id,
                        branch_id=session.branch_id,
                        projection_hash=session.projection_hash,
                        revision=session.revision,
                        error_code=TemporalMutationServiceErrorCode.frame_too_large.value,
                        error=(
                            "Temporal apply produced an oversized frame: "
                            f"bytes={size} limit={self._max_frame_bytes}"
                        ),
                    )

            changes_json = JsonArray(changes)
            changes_list = list(changes_json)
            previous_overlay_oig = session.overlay_oig
            previous_revision = session.revision
            previous_last_apply_at = session.last_apply_at
            previous_frames = list(session.frames)
            frame_created_at = self._utcnow()
            session.overlay_oig = after_oig
            session.revision += 1
            session.last_apply_at = frame_created_at
            frame_record = _TemporalFrame(
                revision=session.revision,
                actor_id=author_id,
                changes=changes_list,
                graph_hash_pre=invoke_resp.graph_hash_pre,
                graph_hash_post=invoke_resp.graph_hash_post,
                created_at=frame_created_at,
            )
            session.frames.append(frame_record)
            if (
                self._max_frames_per_session > 0
                and len(session.frames) > self._max_frames_per_session
            ):
                drop = len(session.frames) - self._max_frames_per_session
                del session.frames[0:drop]

            session_payload = self._session_payload(session=session)
            durability_error = await self._persist_frame(
                env_req=env_req,
                session=session,
                frame_record=frame_record,
                service_op=service_op,
                payload=session_payload,
            )
            if durability_error is not None:
                session.overlay_oig = previous_overlay_oig
                session.revision = previous_revision
                session.last_apply_at = previous_last_apply_at
                session.frames = previous_frames
                return durability_error

            frame = TemporalMutationServiceOperation(
                operation="stream_frame",
                session_id=session.session_id,
                branch_id=session.branch_id,
                projection_hash=session.projection_hash,
                base_commit_id=session.base_commit_id,
                revision=session.revision,
                actor_id=author_id,
                changes=changes_json,
                graph_hash_pre=invoke_resp.graph_hash_pre,
                graph_hash_post=invoke_resp.graph_hash_post,
                payload=session_payload,
                status="succeeded",
            )
            await self._broadcast_frame(session=session, frame=frame)

            return ServiceOperationResult(
                status=RequestStatus.succeeded,
                error=None,
                response_service_operation=TemporalMutationServiceOperation(
                    operation="apply",
                    session_id=session.session_id,
                    revision=session.revision,
                    actor_id=author_id,
                    changes=changes_json,
                    graph_hash_pre=invoke_resp.graph_hash_pre,
                    graph_hash_post=invoke_resp.graph_hash_post,
                    payload=session_payload,
                    status="succeeded",
                ),
                stream_lifecycle=StreamLifecycle.auto_close,
            )

    async def _finalize(
        self,
        *,
        network_operation_id: UUID,
        env_req: _TemporalMutationRequestEnvelope,
        node_id: UUID,
        service_op: TemporalMutationServiceOperation,
    ) -> ServiceOperationResult:
        _ = (network_operation_id, node_id)

        session_id = service_op.session_id
        if session_id is None:
            return self._failed_result(
                operation="finalize",
                error_code=TemporalMutationServiceErrorCode.missing_session_id.value,
                error="TemporalMutationServiceOperation.session_id is required for finalize",
            )

        async with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            return self._failed_result(
                operation="finalize",
                session_id=session_id,
                error_code=TemporalMutationServiceErrorCode.session_not_found.value,
                error="Session not found",
            )

        admission_error = await self._ensure_admitted(
            operation="finalize",
            env_req=env_req,
            service_op=service_op,
            session=session,
        )
        if admission_error is not None:
            return admission_error

        actor_id = service_op.actor_id or env_req.actor_id
        author_id = _resolve_author_id(actor_id)

        async with session.lock:
            now = self._utcnow()
            session.last_activity_at = now

            lease_error = self._ensure_writer_lease(
                session=session,
                author_id=author_id,
                now=now,
                operation="finalize",
            )
            if lease_error is not None:
                return lease_error

            # Conflict check: base head must still be the lane head.
            store = FSCommitStore()
            head_commit = await store.head_commit(
                branch_id=session.branch_id, projection_hash=session.projection_hash
            )
            head_commit_id = head_commit.commit.id if head_commit is not None else None
            if head_commit_id != session.base_commit_id:
                return self._failed_result(
                    operation="finalize",
                    session_id=session.session_id,
                    branch_id=session.branch_id,
                    projection_hash=session.projection_hash,
                    revision=session.revision,
                    error_code=TemporalMutationServiceErrorCode.head_conflict.value,
                    error=(
                        "Lane head advanced while session was open (conflict). "
                        f"base_commit_id={session.base_commit_id} lane_head_commit_id={head_commit_id}"
                    ),
                    payload={
                        **self._session_payload(session=session),
                        "lane_head_commit_id": (
                            str(head_commit_id) if head_commit_id is not None else None
                        ),
                    },
                )

            if head_commit is None:
                return self._failed_result(
                    operation="finalize",
                    session_id=session.session_id,
                    branch_id=session.branch_id,
                    projection_hash=session.projection_hash,
                    revision=session.revision,
                    error_code=TemporalMutationServiceErrorCode.no_head_commit.value,
                    error="Lane has no HEAD commit; cannot finalize temporal session",
                )

            changes = diff_object_instance_graph_changes(
                old=session.base_oig,
                new=session.overlay_oig,
                object_instance_graph_identity_id=head_commit.object_instance_graph_identity_id,
                created_at=datetime.now(UTC),
            )

            commit_action = CommitActionDescriptor(
                operation_label="TemporalSession.finalize"
            )
            try:
                commit = await self._committer.commit(
                    branch_id=session.branch_id,
                    projection_hash=session.projection_hash,
                    object_instance_graph_identity_id=head_commit.object_instance_graph_identity_id,
                    object_instance_graph_id=session.base_oig.id,
                    before_oig=session.base_oig,
                    root_object_id=resolve_root_source_object_id(session.overlay_oig),
                    changes=changes,
                    graph_hash_pre=session.base_oig.hash or "",
                    graph_hash_post=session.overlay_oig.hash or "",
                    author_id=author_id,
                    commit_action=commit_action,
                )
            except Exception as exc:
                return self._failed_result(
                    operation="finalize",
                    session_id=session.session_id,
                    branch_id=session.branch_id,
                    projection_hash=session.projection_hash,
                    revision=session.revision,
                    error_code=TemporalMutationServiceErrorCode.invocation_failed.value,
                    error=f"Temporal finalize commit failed: {exc}",
                    payload=self._session_payload(session=session),
                )

            # Notify subscribers (best-effort), then close streams.
            finalized_commit_id = commit.commit.id if commit and commit.commit else None
            final_graph_hash_post = (
                commit.graph_hash_post if commit else session.overlay_oig.hash
            )
            finalize_payload = self._finalize_payload(
                session=session,
                actor_id=author_id,
                finalized_commit_id=finalized_commit_id,
                final_graph_hash_post=final_graph_hash_post,
            )
            final_frame = TemporalMutationServiceOperation(
                operation="finalized",
                session_id=session.session_id,
                branch_id=session.branch_id,
                projection_hash=session.projection_hash,
                base_commit_id=session.base_commit_id,
                revision=session.revision,
                actor_id=author_id,
                commit_id=finalized_commit_id,
                graph_hash_post=final_graph_hash_post,
                payload=finalize_payload,
                status="succeeded",
            )
            await self._broadcast_frame(session=session, frame=final_frame)
            await self._persist_tombstone(
                session=session,
                operation="finalized",
                actor_id=author_id,
                finalized_commit_id=finalized_commit_id,
                final_graph_hash_post=final_graph_hash_post,
                reason=None,
                payload=finalize_payload,
            )

        await self._close_session(session_id=session.session_id, session=session)

        return ServiceOperationResult(
            status=RequestStatus.succeeded,
            error=None,
            response_service_operation=TemporalMutationServiceOperation(
                operation="finalize",
                session_id=session.session_id,
                branch_id=session.branch_id,
                projection_hash=session.projection_hash,
                base_commit_id=session.base_commit_id,
                revision=session.revision,
                actor_id=author_id,
                commit_id=finalized_commit_id,
                graph_hash_post=final_graph_hash_post,
                payload=finalize_payload,
                status="succeeded",
            ),
            stream_lifecycle=StreamLifecycle.auto_close,
        )

    async def _close(
        self,
        *,
        network_operation_id: UUID,
        env_req: _TemporalMutationRequestEnvelope,
        node_id: UUID,
        service_op: TemporalMutationServiceOperation,
    ) -> ServiceOperationResult:
        _ = (network_operation_id, node_id)
        session_id = service_op.session_id
        if session_id is None:
            return self._failed_result(
                operation="close",
                error_code=TemporalMutationServiceErrorCode.missing_session_id.value,
                error="TemporalMutationServiceOperation.session_id is required for close",
            )

        async with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            return self._failed_result(
                operation="close",
                session_id=session_id,
                error_code=TemporalMutationServiceErrorCode.session_not_found.value,
                error="Session not found",
            )

        admission_error = await self._ensure_admitted(
            operation="close",
            env_req=env_req,
            service_op=service_op,
            session=session,
        )
        if admission_error is not None:
            return admission_error

        actor_id = service_op.actor_id or env_req.actor_id
        author_id = _resolve_author_id(actor_id)

        async with session.lock:
            now = self._utcnow()
            session.last_activity_at = now
            lease_error = self._ensure_writer_lease(
                session=session,
                author_id=author_id,
                now=now,
                operation="close",
            )
            if lease_error is not None:
                return lease_error

        await self._persist_tombstone(
            session=session,
            operation="closed",
            actor_id=author_id,
            finalized_commit_id=None,
            final_graph_hash_post=session.overlay_oig.hash,
            reason=None,
            payload=self._session_payload(session=session),
        )
        await self._close_session(session_id=session_id, session=session)
        return ServiceOperationResult(
            status=RequestStatus.succeeded,
            error=None,
            response_service_operation=TemporalMutationServiceOperation(
                operation="close",
                session_id=session_id,
                status="succeeded",
            ),
            stream_lifecycle=StreamLifecycle.auto_close,
        )

    async def _close_session(
        self, *, session_id: UUID, session: _TemporalSession
    ) -> None:
        lane_key = (session.branch_id, session.projection_hash)
        async with self._lock:
            self._sessions.pop(session_id, None)
            existing = self._sessions_by_lane.get(lane_key)
            if existing == session_id:
                self._sessions_by_lane.pop(lane_key, None)

        await self._close_session_streams(session=session)
