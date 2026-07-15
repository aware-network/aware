"""Meta-owned execution context for generated language handlers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID

from aware_meta.graph.projection.portal_index import ObjectProjectionGraphPortalIndex
from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphHandlerExecutionRequest,
    MetaGraphRuntimeIndex,
)
from aware_meta.runtime.invocation_engine import (
    MetaGraphInvokeFunctionCallable,
)
from aware_meta_ontology.function.function_call import FunctionCall
from aware_orm.session.session import Session


@dataclass(frozen=True, slots=True)
class MetaGraphHandlerContext:
    requester_id: UUID
    domain_oigb_id: UUID | None = None
    domain_object_instance_graph_id: UUID | None = None
    domain_object_instance_graph_identity_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None
    portal_index: ObjectProjectionGraphPortalIndex | None = None


@dataclass(frozen=True, slots=True)
class MetaGraphHandlerExecutionContext:
    session: Session
    ctx: MetaGraphHandlerContext
    function_call: FunctionCall
    index: MetaGraphRuntimeIndex
    request: MetaGraphHandlerExecutionRequest | None = None
    invoke_function: MetaGraphInvokeFunctionCallable | None = None


_CURRENT: ContextVar[MetaGraphHandlerExecutionContext | None] = ContextVar(
    "aware_meta_graph_handler_execution_context",
    default=None,
)


def build_meta_graph_handler_execution_context(
    *,
    request: MetaGraphHandlerExecutionRequest,
) -> MetaGraphHandlerExecutionContext:
    lane_scope = request.staged_call.lane_scope
    session = Session(branch_id=lane_scope.domain_branch_id, skip_db=True)
    return MetaGraphHandlerExecutionContext(
        session=session,
        ctx=MetaGraphHandlerContext(
            requester_id=request.request.actor_id,
            domain_oigb_id=lane_scope.object_instance_graph_branch_id,
            domain_object_instance_graph_id=lane_scope.object_instance_graph_id,
            domain_object_instance_graph_identity_id=(
                lane_scope.object_instance_graph_identity_id
            ),
            branch_id=lane_scope.domain_branch_id,
            projection_hash=lane_scope.domain_projection_hash,
            portal_index=request.execution_plan.index.portal_index,
        ),
        function_call=request.staged_call.function_call,
        index=request.execution_plan.index,
        request=request,
        invoke_function=request.invoke_function,
    )


@contextmanager
def scoped_meta_graph_handler_execution_context(
    context: MetaGraphHandlerExecutionContext,
) -> Iterator[None]:
    token = _CURRENT.set(context)
    try:
        yield
    finally:
        _CURRENT.reset(token)


def current_meta_graph_handler_execution_context_or_none() -> (
    MetaGraphHandlerExecutionContext | None
):
    return _CURRENT.get()


def current_meta_graph_handler_execution_context() -> MetaGraphHandlerExecutionContext:
    value = current_meta_graph_handler_execution_context_or_none()
    if value is None:
        raise RuntimeError("No Meta graph handler execution context is set")
    return value


__all__ = [
    "MetaGraphHandlerContext",
    "MetaGraphHandlerExecutionContext",
    "build_meta_graph_handler_execution_context",
    "current_meta_graph_handler_execution_context",
    "current_meta_graph_handler_execution_context_or_none",
    "scoped_meta_graph_handler_execution_context",
]
