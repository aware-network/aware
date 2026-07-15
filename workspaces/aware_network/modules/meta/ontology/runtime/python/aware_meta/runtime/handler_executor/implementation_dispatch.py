from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphBoundArguments,
    MetaGraphHandlerDispatchResult,
    MetaGraphHandlerExecutionRequest,
    MetaGraphImplementationKind,
    MetaGraphPreState,
)


class MetaGraphImplementationDispatchError(RuntimeError):
    """Raised when implementation dispatch cannot start safely."""


class MetaGraphImplementationDispatchNotReadyError(
    MetaGraphImplementationDispatchError
):
    """Raised when the selected implementation rail is not wired yet."""


class MetaGraphAwareFunctionImplRunner(Protocol):
    async def run_function_impl(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        bound_arguments: MetaGraphBoundArguments,
    ) -> MetaGraphHandlerDispatchResult: ...


class MetaGraphLanguageHandlerRunner(Protocol):
    async def run_language_handler(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        bound_arguments: MetaGraphBoundArguments,
    ) -> MetaGraphHandlerDispatchResult: ...


@dataclass(frozen=True, slots=True)
class MetaGraphImplementationDispatcherPhase:
    """Route Meta execution to the selected implementation rail."""

    aware_function_impl_runner: MetaGraphAwareFunctionImplRunner | None = None
    language_handler_runner: MetaGraphLanguageHandlerRunner | None = None

    async def dispatch_implementation(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        bound_arguments: MetaGraphBoundArguments,
    ) -> MetaGraphHandlerDispatchResult:
        _validate_dispatch_inputs(
            request=request,
            pre_state=pre_state,
            bound_arguments=bound_arguments,
        )
        implementation = request.execution_plan.implementation
        if implementation.kind is MetaGraphImplementationKind.aware_function_impl:
            return await self._dispatch_aware_function_impl(
                request=request,
                pre_state=pre_state,
                bound_arguments=bound_arguments,
            )
        if implementation.kind is MetaGraphImplementationKind.language_handler:
            return await self._dispatch_language_handler(
                request=request,
                pre_state=pre_state,
                bound_arguments=bound_arguments,
            )
        raise MetaGraphImplementationDispatchError(
            "Unsupported Meta implementation kind. "
            f"implementation_kind={implementation.kind.value}"
        )

    async def _dispatch_aware_function_impl(
        self,
        *,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        bound_arguments: MetaGraphBoundArguments,
    ) -> MetaGraphHandlerDispatchResult:
        function_config = request.execution_plan.implementation.function_config
        function_impl = function_config.function_impl
        if function_impl is None:
            raise MetaGraphImplementationDispatchError(
                "Aware FunctionImpl dispatch requires FunctionConfig.function_impl. "
                f"function_call_id={request.staged_call.function_call.id} "
                f"function_id={function_config.id}"
            )
        if self.aware_function_impl_runner is None:
            raise MetaGraphImplementationDispatchNotReadyError(
                "Meta Aware FunctionImpl runner is not wired. "
                f"function_call_id={request.staged_call.function_call.id} "
                f"function_id={function_config.id} "
                f"function_impl_key={function_impl.key} "
                f"function_impl_kind={function_impl.kind.value}"
            )
        return await self.aware_function_impl_runner.run_function_impl(
            request,
            pre_state,
            bound_arguments,
        )

    async def _dispatch_language_handler(
        self,
        *,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        bound_arguments: MetaGraphBoundArguments,
    ) -> MetaGraphHandlerDispatchResult:
        implementation = request.execution_plan.implementation
        function_config = implementation.function_config
        owner_class_name = (
            implementation.owner_class_config.name
            if implementation.owner_class_config is not None
            else "<unbound>"
        )
        if self.language_handler_runner is None:
            raise MetaGraphImplementationDispatchNotReadyError(
                "Meta language handler runner is not wired. "
                f"function_call_id={request.staged_call.function_call.id} "
                f"function_id={function_config.id} "
                f"owner_key={function_config.owner_key} "
                f"function_name={function_config.name} "
                f"owner_class_name={owner_class_name}"
            )
        return await self.language_handler_runner.run_language_handler(
            request,
            pre_state,
            bound_arguments,
        )


def _validate_dispatch_inputs(
    *,
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
    bound_arguments: MetaGraphBoundArguments,
) -> None:
    execution_plan = request.execution_plan
    if pre_state.execution_plan is not execution_plan:
        raise MetaGraphImplementationDispatchError(
            "Meta implementation dispatch requires pre-state from the same "
            "execution plan."
        )
    if bound_arguments.execution_plan is not execution_plan:
        raise MetaGraphImplementationDispatchError(
            "Meta implementation dispatch requires bound arguments from the "
            "same execution plan."
        )


__all__ = [
    "MetaGraphAwareFunctionImplRunner",
    "MetaGraphImplementationDispatchError",
    "MetaGraphImplementationDispatchNotReadyError",
    "MetaGraphImplementationDispatcherPhase",
    "MetaGraphLanguageHandlerRunner",
]
