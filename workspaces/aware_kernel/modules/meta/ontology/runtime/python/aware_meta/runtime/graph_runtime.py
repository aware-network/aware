from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from aware_meta.runtime.graph_context import MetaGraphRuntimeContext
from aware_meta.runtime.invocation_engine import (
    MetaGraphCallTarget,
    MetaGraphCommitReceipt,
    MetaGraphInvocationBackend,
    MetaGraphInvocationEngine,
    MetaGraphInvokeFunctionInput,
)

if TYPE_CHECKING:
    from aware_meta.runtime.graph_lane import MetaGraphBoundRuntimeLane


class MetaGraphRuntime:
    """Local Meta graph runtime authority facade.

    The facade delegates to an explicit Meta invocation engine or backend. A
    caller that still needs the legacy invoker must inject the compatibility
    backend by name.
    """

    def __init__(
        self,
        *,
        backend: MetaGraphInvocationBackend | None = None,
        invocation_engine: MetaGraphInvocationEngine | None = None,
        context: MetaGraphRuntimeContext | None = None,
    ) -> None:
        if invocation_engine is not None and backend is not None:
            raise ValueError(
                "invocation_engine cannot be combined with backend"
            )
        if invocation_engine is None and backend is None:
            raise ValueError("MetaGraphRuntime requires backend or invocation_engine")
        if invocation_engine is not None:
            self._invocation_engine = invocation_engine
        else:
            assert backend is not None
            self._invocation_engine = MetaGraphInvocationEngine(backend=backend)
        self._context = context

    @property
    def context(self) -> MetaGraphRuntimeContext | None:
        return self._context

    async def invoke_function(
        self, request: MetaGraphInvokeFunctionInput
    ) -> MetaGraphCommitReceipt:
        return await self._invocation_engine.invoke_function(request)

    def bind(
        self,
        *,
        projection: str,
        branch_id: UUID,
        actor_id: UUID | None = None,
        context: MetaGraphRuntimeContext | None = None,
    ) -> MetaGraphBoundRuntimeLane:
        from aware_meta.runtime.graph_lane import bind_meta_graph_runtime_lane

        runtime_context = context or self._context
        if runtime_context is None:
            raise ValueError(
                "MetaGraphRuntime.bind requires a MetaGraphRuntimeContext."
            )
        return bind_meta_graph_runtime_lane(
            runtime=self,
            context=runtime_context,
            projection=projection,
            branch_id=branch_id,
            actor_id=actor_id,
        )


__all__ = [
    "MetaGraphCallTarget",
    "MetaGraphCommitReceipt",
    "MetaGraphInvocationBackend",
    "MetaGraphInvocationEngine",
    "MetaGraphInvokeFunctionInput",
    "MetaGraphRuntime",
]
