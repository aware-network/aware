from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol
from uuid import UUID

from aware_code.types import JsonArray, JsonObject, JsonValue
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.invocation_commit_actions import MetaInvocationCommitAction


class MetaGraphCallTarget(Enum):
    """Function-call target variants owned by the Meta runtime boundary."""

    instance = "instance"
    opg_constructor = "opg_constructor"


@dataclass(frozen=True)
class MetaGraphInvokeFunctionInput:
    """Meta-owned function invocation input.

    Environment runtime execution context is intentionally not a first-class
    field here. It belongs to orchestration adapters, not Meta graph commit
    validity.
    """

    index: MetaGraphRuntimeIndex
    actor_id: UUID
    function_id: UUID
    domain_branch_id: UUID | None = None
    domain_projection_hash: str | None = None
    domain_object_instance_graph_id: UUID | None = None
    domain_object_instance_graph_identity_id: UUID | None = None
    call_key: UUID | None = None
    call_target: MetaGraphCallTarget = MetaGraphCallTarget.instance
    target_object_id: UUID | None = None
    object_projection_graph_id: UUID | None = None
    args: JsonArray = field(default_factory=JsonArray)
    kwargs: JsonObject = field(default_factory=JsonObject)
    expected_graph_hash_pre: str | None = None
    expected_head_commit_id: UUID | None = None
    commit: bool = True
    publish: bool = False


@dataclass(frozen=True)
class MetaGraphCommitReceipt:
    """Meta-owned receipt for function invocation over graph commit truth."""

    status: str
    actor_id: UUID | None
    domain_branch_id: UUID | None
    domain_projection_hash: str | None
    payload: JsonValue | None
    error: str | None
    logs: Sequence[str]
    execution_time_ms: int | None
    root_object_id: UUID | None
    graph_hash_pre: str | None
    graph_hash_post: str | None
    changes: JsonArray
    function_call_id: UUID | None
    function_call_response_id: UUID | None
    commit_id: UUID | None
    object_instance_graph_commit_id: UUID | None
    commit_action: MetaInvocationCommitAction | None = None


class MetaGraphInvocationBackend(Protocol):
    async def invoke_function(
        self, request: MetaGraphInvokeFunctionInput
    ) -> MetaGraphCommitReceipt: ...


MetaGraphInvokeFunctionCallable = Callable[
    [MetaGraphInvokeFunctionInput],
    Awaitable[MetaGraphCommitReceipt],
]


class MetaGraphInvocationEngine:
    """Meta-owned function invocation engine.

    The engine owns the Meta request/receipt authority and requires an explicit
    invocation backend. Compatibility callers must name the legacy backend
    directly instead of relying on a hidden fallback.
    """

    def __init__(
        self,
        *,
        backend: MetaGraphInvocationBackend,
    ) -> None:
        self._backend = backend

    async def invoke_function(
        self, request: MetaGraphInvokeFunctionInput
    ) -> MetaGraphCommitReceipt:
        return await self._backend.invoke_function(request)


__all__ = [
    "MetaGraphCallTarget",
    "MetaGraphCommitReceipt",
    "MetaGraphInvocationBackend",
    "MetaGraphInvocationEngine",
    "MetaGraphInvokeFunctionCallable",
    "MetaGraphInvokeFunctionInput",
]
