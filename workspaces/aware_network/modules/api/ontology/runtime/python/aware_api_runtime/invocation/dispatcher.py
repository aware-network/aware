from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ContextManager, Protocol
from uuid import UUID

from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import MetaGraphRuntimeIndex

from .resolution import (
    ApiInvocationIR,
    ApiInvocationSourceCommit,
    ResolvedApiInvocationEnvelope,
    build_resolved_api_invocation_envelope,
)

if TYPE_CHECKING:
    from .materialization.call import ApiCallMaterializationResult


class _MetaRuntimeLaneProtocol(Protocol):
    @property
    def last_commit_id(self) -> UUID | None: ...

    @property
    def last_head_commit_id(self) -> UUID | None: ...

    def activate(
        self,
        *,
        commit: bool = True,
        publish: bool = False,
    ) -> ContextManager[object]: ...


class ApiInvocationRuntimeProtocol(Protocol):
    def bind(
        self,
        *,
        projection: str,
        branch_id: UUID,
        actor_id: UUID | None = None,
    ) -> _MetaRuntimeLaneProtocol: ...


@dataclass(frozen=True, slots=True)
class ApiInvocationDispatchResult:
    ir: ApiInvocationIR
    materialized_call: ApiCallMaterializationResult
    envelope: ResolvedApiInvocationEnvelope


async def dispatch_api_invocation(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    source_lane: MaterializationLaneContext,
    target_lane: MaterializationLaneContext,
    ir: ApiInvocationIR,
    source_commit: ApiInvocationSourceCommit | None = None,
    call_key: UUID | None = None,
    commit: bool = True,
    publish: bool = False,
    receipt_projection_backend: str | None = None,
) -> ApiInvocationDispatchResult:
    """Materialize one API invocation and return its commit-backed handoff."""
    materialized_call = await _materialize_api_call(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        source_lane=source_lane,
        target_lane=target_lane,
        ir=ir,
        source_commit=source_commit,
        call_key=call_key,
        commit=commit,
        publish=publish,
        receipt_projection_backend=receipt_projection_backend,
    )
    envelope = build_resolved_api_invocation_envelope(
        ir=ir,
        materialized_call=materialized_call.binding,
    )
    return ApiInvocationDispatchResult(
        ir=ir,
        materialized_call=materialized_call,
        envelope=envelope,
    )


async def _materialize_api_call(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    source_lane: MaterializationLaneContext,
    target_lane: MaterializationLaneContext,
    ir: ApiInvocationIR,
    source_commit: ApiInvocationSourceCommit | None,
    call_key: UUID | None,
    commit: bool,
    publish: bool,
    receipt_projection_backend: str | None,
) -> ApiCallMaterializationResult:
    from .materialization.call import materialize_api_call

    return await materialize_api_call(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        source_lane=source_lane,
        target_lane=target_lane,
        ir=ir,
        source_commit=source_commit,
        call_key=call_key,
        commit=commit,
        publish=publish,
        receipt_projection_backend=receipt_projection_backend,
    )


__all__ = [
    "ApiInvocationDispatchResult",
    "ApiInvocationRuntimeProtocol",
    "dispatch_api_invocation",
]
