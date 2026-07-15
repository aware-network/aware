from __future__ import annotations

from dataclasses import dataclass

from aware_meta.graph.instance.commit.perf_trace import commit_perf_span
from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphAppendReadyChangeAssembler,
    MetaGraphArgumentBinder,
    MetaGraphHandlerExecutionRequest,
    MetaGraphHandlerExecutionResult,
    MetaGraphImplementationDispatcher,
    MetaGraphMutationBoundaryValidator,
    MetaGraphMutationRecorder,
    MetaGraphPreStateMaterializer,
)


class MetaGraphHandlerExecutionNotReadyError(RuntimeError):
    """Raised when the phase executor reaches an intentionally unwired phase."""


@dataclass(frozen=True, slots=True)
class MetaGraphPhaseHandlerExecutor:
    """Run the Meta-owned executor phases that are production-ready."""

    pre_state_materializer: MetaGraphPreStateMaterializer
    argument_binder: MetaGraphArgumentBinder
    implementation_dispatcher: MetaGraphImplementationDispatcher | None = None
    mutation_recorder: MetaGraphMutationRecorder | None = None
    mutation_boundary_validator: MetaGraphMutationBoundaryValidator | None = None
    append_ready_change_assembler: MetaGraphAppendReadyChangeAssembler | None = None

    async def execute_function(
        self,
        request: MetaGraphHandlerExecutionRequest,
    ) -> MetaGraphHandlerExecutionResult:
        metadata = _handler_execution_trace_metadata(request)
        with commit_perf_span(
            phase="handler_execution.materialize_pre_state",
            category="meta.runtime.handler_execution",
            metadata=metadata,
        ):
            pre_state = await self.pre_state_materializer.materialize_pre_state(
                request
            )
        with commit_perf_span(
            phase="handler_execution.bind_arguments",
            category="meta.runtime.handler_execution",
            metadata=metadata,
        ):
            bound_arguments = await self.argument_binder.bind_arguments(
                request,
                pre_state,
            )
        if self.implementation_dispatcher is not None:
            with commit_perf_span(
                phase="handler_execution.dispatch_implementation",
                category="meta.runtime.handler_execution",
                metadata=metadata,
            ):
                dispatch_result = (
                    await self.implementation_dispatcher.dispatch_implementation(
                        request,
                        pre_state,
                        bound_arguments,
                    )
                )
            if self.mutation_recorder is None:
                raise MetaGraphHandlerExecutionNotReadyError(
                    "MetaGraphPhaseHandlerExecutor reached mutation recording, "
                    "but no Meta mutation recorder is wired yet. "
                    f"function_call_id={request.staged_call.function_call.id} "
                    "function_id="
                    f"{request.staged_call.resolved_target.function_config.id} "
                    f"dispatch_success={dispatch_result.success} "
                    f"dispatch_time_ms={dispatch_result.execution_time_ms}"
                )
            with commit_perf_span(
                phase="handler_execution.record_mutations",
                category="meta.runtime.handler_execution",
                metadata=metadata,
            ):
                mutation_set = await self.mutation_recorder.record_mutations(
                    request,
                    pre_state,
                    dispatch_result,
                )
            if self.mutation_boundary_validator is not None:
                with commit_perf_span(
                    phase="handler_execution.validate_mutation_boundary",
                    category="meta.runtime.handler_execution",
                    metadata=metadata,
                ):
                    boundary_validation = (
                        await self.mutation_boundary_validator.validate_mutations(
                            request,
                            mutation_set,
                        )
                    )
                if self.append_ready_change_assembler is None:
                    raise MetaGraphHandlerExecutionNotReadyError(
                        "MetaGraphPhaseHandlerExecutor reached append-ready "
                        "change assembly, but no Meta append assembler is wired yet. "
                        f"function_call_id={request.staged_call.function_call.id} "
                        "function_id="
                        f"{request.staged_call.resolved_target.function_config.id} "
                        f"boundary_status={boundary_validation.status.value} "
                        "violation_message="
                        f"{boundary_validation.violation_message}"
                    )
                append_ready_change_assembler = self.append_ready_change_assembler
                with commit_perf_span(
                    phase="handler_execution.assemble_append_ready_changes",
                    category="meta.runtime.handler_execution",
                    metadata=metadata,
                ):
                    append_ready = (
                        await append_ready_change_assembler.assemble_append_ready_changes(
                            request,
                            mutation_set,
                            boundary_validation,
                        )
                    )
                with commit_perf_span(
                    phase="handler_execution.build_execution_result",
                    category="meta.runtime.handler_execution",
                    metadata=metadata,
                ):
                    return MetaGraphHandlerExecutionResult(
                        success=dispatch_result.success,
                        payload=dispatch_result.payload,
                        error_message=dispatch_result.error_message,
                        execution_time_ms=dispatch_result.execution_time_ms,
                        graph_hash_pre=append_ready.graph_hash_pre,
                        graph_hash_post=append_ready.graph_hash_post,
                        root_object_id=append_ready.root_object_id,
                        root_class_instance_identity_id=(
                            append_ready.root_class_instance_identity_id
                        ),
                        before_oig=append_ready.before_oig,
                        changes=append_ready.changes,
                        append_ready_changes=append_ready,
                        materialization_cache_prime_snapshot=(
                            append_ready.materialization_cache_prime_snapshot
                        ),
                    )
            raise MetaGraphHandlerExecutionNotReadyError(
                "MetaGraphPhaseHandlerExecutor reached mutation boundary "
                "validation, but no Meta boundary validator is wired yet. "
                f"function_call_id={request.staged_call.function_call.id} "
                "function_id="
                f"{request.staged_call.resolved_target.function_config.id} "
                f"mutation_change_count={len(mutation_set.changes)} "
                f"graph_hash_pre={mutation_set.graph_hash_pre} "
                f"graph_hash_post={mutation_set.graph_hash_post}"
            )
        raise MetaGraphHandlerExecutionNotReadyError(
            "MetaGraphPhaseHandlerExecutor reached implementation dispatch, "
            "but no Meta implementation dispatcher is wired yet. "
            f"function_call_id={request.staged_call.function_call.id} "
            f"function_id={request.staged_call.resolved_target.function_config.id} "
            f"implementation_kind={request.execution_plan.implementation.kind.value} "
            f"positional_arg_count={len(bound_arguments.positional)} "
            f"keyword_arg_count={len(bound_arguments.keyword)}"
        )


def _handler_execution_trace_metadata(
    request: MetaGraphHandlerExecutionRequest,
) -> dict[str, object]:
    implementation = request.execution_plan.implementation
    return {
        "call_target": request.request.call_target.value,
        "domain_projection_hash": request.request.domain_projection_hash,
        "function_call_id": request.staged_call.function_call.id,
        "function_id": implementation.function_config.id,
        "implementation_kind": implementation.kind.value,
        "operation_label": request.staged_call.resolved_target.operation_label,
    }


__all__ = [
    "MetaGraphHandlerExecutionNotReadyError",
    "MetaGraphPhaseHandlerExecutor",
]
