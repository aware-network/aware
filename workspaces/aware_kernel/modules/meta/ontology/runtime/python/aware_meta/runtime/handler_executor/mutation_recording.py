from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol

from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphExecutionSessionDelta,
    MetaGraphHandlerDispatchResult,
    MetaGraphHandlerExecutionRequest,
    MetaGraphMutationSet,
    MetaGraphPreState,
)


class MetaGraphMutationRecordingError(RuntimeError):
    """Raised when Meta cannot safely record handler mutations."""


class MetaGraphMutationRecordingNotReadyError(MetaGraphMutationRecordingError):
    """Raised when no Meta mutation source is wired."""


class MetaGraphMutationSource(Protocol):
    async def collect_mutations(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        dispatch_result: MetaGraphHandlerDispatchResult,
    ) -> MetaGraphMutationSet: ...


@dataclass(frozen=True, slots=True)
class MetaGraphSessionDeltaMutationSource:
    """Collect mutations from the typed execution-session delta."""

    async def collect_mutations(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        dispatch_result: MetaGraphHandlerDispatchResult,
    ) -> MetaGraphMutationSet:
        session_delta = dispatch_result.session_delta
        if session_delta is None:
            raise MetaGraphMutationRecordingNotReadyError(
                "Meta dispatch result does not include execution-session delta "
                "evidence for mutation recording. "
                f"function_call_id={request.staged_call.function_call.id} "
                "function_id="
                f"{request.staged_call.resolved_target.function_config.id}"
            )
        return build_meta_graph_mutation_set_from_session_delta(
            request=request,
            pre_state=pre_state,
            dispatch_result=dispatch_result,
            session_delta=session_delta,
        )


@dataclass(frozen=True, slots=True)
class MetaGraphMutationRecorderPhase:
    """Collect implementation mutations from a Meta-owned session delta source."""

    mutation_source: MetaGraphMutationSource | None = None

    async def record_mutations(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        dispatch_result: MetaGraphHandlerDispatchResult,
    ) -> MetaGraphMutationSet:
        _validate_recording_inputs(
            request=request,
            pre_state=pre_state,
            dispatch_result=dispatch_result,
        )
        if self.mutation_source is None:
            function_config = request.execution_plan.implementation.function_config
            raise MetaGraphMutationRecordingNotReadyError(
                "Meta mutation source is not wired. "
                f"function_call_id={request.staged_call.function_call.id} "
                f"function_id={function_config.id} "
                f"dispatch_success={dispatch_result.success}"
            )
        mutation_set = await self.mutation_source.collect_mutations(
            request,
            pre_state,
            dispatch_result,
        )
        return build_meta_graph_mutation_set(
            request=request,
            pre_state=pre_state,
            dispatch_result=dispatch_result,
            mutation_set=mutation_set,
        )


def build_meta_graph_mutation_set_from_session_delta(
    *,
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
    dispatch_result: MetaGraphHandlerDispatchResult,
    session_delta: MetaGraphExecutionSessionDelta,
) -> MetaGraphMutationSet:
    _validate_recording_inputs(
        request=request,
        pre_state=pre_state,
        dispatch_result=dispatch_result,
    )
    execution_plan = request.execution_plan
    if session_delta.execution_plan is not execution_plan:
        raise MetaGraphMutationRecordingError(
            "Meta execution-session delta belongs to a different execution plan."
        )
    if session_delta.before_oig is not pre_state.before_oig:
        raise MetaGraphMutationRecordingError(
            "Meta execution-session delta references a different pre-state OIG."
        )
    if not session_delta.graph_hash_post:
        raise MetaGraphMutationRecordingError(
            "Meta execution-session delta requires graph_hash_post authority."
        )
    return build_meta_graph_mutation_set(
        request=request,
        pre_state=pre_state,
        dispatch_result=dispatch_result,
        mutation_set=MetaGraphMutationSet(
            execution_plan=execution_plan,
            before_oig=session_delta.before_oig,
            changes=session_delta.changes,
            graph_hash_pre=session_delta.graph_hash_pre,
            graph_hash_post=session_delta.graph_hash_post,
            root_object_id=session_delta.root_object_id,
            root_class_instance_identity_id=(
                session_delta.root_class_instance_identity_id
            ),
            target_class_instance_id=session_delta.target_class_instance_id,
            constructed_class_instance_ids=(
                session_delta.constructed_class_instance_ids
            ),
        ),
    )


def build_meta_graph_mutation_set(
    *,
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
    dispatch_result: MetaGraphHandlerDispatchResult,
    mutation_set: MetaGraphMutationSet,
) -> MetaGraphMutationSet:
    _validate_recording_inputs(
        request=request,
        pre_state=pre_state,
        dispatch_result=dispatch_result,
    )
    execution_plan = request.execution_plan
    if mutation_set.execution_plan is not execution_plan:
        raise MetaGraphMutationRecordingError(
            "Meta mutation source returned mutations for a different "
            "execution plan."
        )
    if mutation_set.before_oig is not pre_state.before_oig:
        raise MetaGraphMutationRecordingError(
            "Meta mutation source returned mutations for a different "
            "pre-state OIG."
        )
    if (
        mutation_set.graph_hash_pre is not None
        and mutation_set.graph_hash_pre != pre_state.graph_hash_pre
    ):
        raise MetaGraphMutationRecordingError(
            "Meta mutation source returned a graph_hash_pre mismatch."
        )
    return replace(
        mutation_set,
        graph_hash_pre=pre_state.graph_hash_pre,
        root_object_id=mutation_set.root_object_id or pre_state.root_object_id,
        root_class_instance_identity_id=(
            mutation_set.root_class_instance_identity_id
            or pre_state.root_class_instance_identity_id
        ),
        target_class_instance_id=(
            mutation_set.target_class_instance_id or pre_state.target_object_id
        ),
    )


def _validate_recording_inputs(
    *,
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
    dispatch_result: MetaGraphHandlerDispatchResult,
) -> None:
    execution_plan = request.execution_plan
    if pre_state.execution_plan is not execution_plan:
        raise MetaGraphMutationRecordingError(
            "Meta mutation recording requires pre-state from the same "
            "execution plan."
        )
    if dispatch_result.execution_plan is not execution_plan:
        raise MetaGraphMutationRecordingError(
            "Meta mutation recording requires dispatch output from the same "
            "execution plan."
        )


__all__ = [
    "build_meta_graph_mutation_set_from_session_delta",
    "build_meta_graph_mutation_set",
    "MetaGraphMutationRecorderPhase",
    "MetaGraphMutationRecordingError",
    "MetaGraphMutationRecordingNotReadyError",
    "MetaGraphSessionDeltaMutationSource",
    "MetaGraphMutationSource",
]
