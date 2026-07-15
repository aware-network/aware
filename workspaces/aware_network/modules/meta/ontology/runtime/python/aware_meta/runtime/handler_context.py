from __future__ import annotations

from aware_meta.runtime.handler_executor.execution_context import (
    MetaGraphHandlerContext,
    MetaGraphHandlerExecutionContext,
    current_meta_graph_handler_execution_context,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.invocation_engine import MetaGraphInvokeFunctionCallable
from aware_meta_ontology.function.function_call import FunctionCall
from aware_orm.session.session import Session


def current_handler_execution_context() -> MetaGraphHandlerExecutionContext:
    """Return the active Meta-owned handler execution context."""

    return current_meta_graph_handler_execution_context()


def current_handler_context() -> MetaGraphHandlerContext:
    return current_handler_execution_context().ctx


def current_handler_session() -> Session:
    return current_handler_execution_context().session


def current_handler_index() -> MetaGraphRuntimeIndex:
    return current_handler_execution_context().index


def current_handler_invoke_function() -> MetaGraphInvokeFunctionCallable | None:
    return current_handler_execution_context().invoke_function


def current_function_call(*, consumer: str | None = None) -> FunctionCall:
    _ = consumer
    return current_handler_execution_context().function_call


__all__ = [
    "current_function_call",
    "current_handler_context",
    "current_handler_execution_context",
    "current_handler_index",
    "current_handler_invoke_function",
    "current_handler_session",
]
