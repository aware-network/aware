from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from time import perf_counter
from typing import Any, cast
from uuid import UUID, uuid4

from aware_code.types import JsonArray
from aware_history_ontology.stable_ids import stable_lane_id
from aware_meta.graph.instance.apply import (
    apply_object_instance_graph_body_draft,
    apply_object_instance_graph_changes,
)
from aware_meta.graph.instance.commit.body_codec import OigCommitBodyDraft
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.graph.instance.commit.fs_backend import (
    grouped_durable_write_transaction,
)
from aware_meta.graph.instance.commit.perf_trace import (
    CommitPerfTraceRecorder,
    active_commit_perf_trace,
    commit_perf_span,
    current_commit_perf_trace,
    summarize_commit_perf_events,
)
from aware_meta.runtime.handler_executor import (
    MetaGraphCommitIndex,
    MetaGraphExecutionPlan,
    MetaGraphHandlerExecutionRequest,
    MetaGraphHandlerExecutionResult,
    MetaGraphHandlerExecutor,
    MetaGraphImplementationPolicy,
    MetaGraphInvocationLaneScope,
    MetaGraphResolvedFunctionTarget,
    MetaGraphRuntimeIndex,
    MetaGraphRuntimeIndexView,
    MetaGraphStagedFunctionCall,
    MetaGraphPreStateProviderResult,
    build_meta_graph_pre_state,
    build_meta_graph_execution_plan,
    build_meta_graph_function_target_index,
)
from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphMaterializationCachePrimeSnapshot,
)
from aware_meta.runtime.commit_groups import (
    MetaInvocationCommitGroupEvidence,
    MetaInvocationCommitGroupEntry,
    build_meta_invocation_commit_group_evidence,
)
from aware_meta.runtime.invocation_commit_actions import MetaInvocationCommitAction
from aware_meta.runtime.invocation_commits import (
    InvocationDomainCommitAppendResult,
    InvocationLaneCommitter,
    append_invocation_domain_commit,
    append_invocation_domain_commit_batch,
    build_invocation_lane_commit_batch_request,
)
from aware_meta.runtime.invocation_engine import (
    MetaGraphCallTarget,
    MetaGraphCommitReceipt,
    MetaGraphInvokeFunctionInput,
)
from aware_meta.runtime.invocation_helpers import (
    jsonify_invocation_payload,
    link_function_call_response_commit,
)
from aware_meta.runtime.invocation_reactions import (
    InvocationRequiredReactionBatchItem,
    InvocationRequiredReactionRunner,
    run_invocation_required_commit_reactions,
    run_invocation_required_commit_reactions_batch,
)
from aware_meta.runtime.commit.required_reactions import RuntimeCommitReactionReceipt
from aware_meta.runtime.commit.identity_lane import (
    ObjectInstanceGraphIdentityLaneHeadEnsureResult,
    ensure_object_instance_graph_identity_lane_head,
    resolve_object_instance_graph_identity_lane_context,
)
from aware_meta_ontology.function.function_call import FunctionCall
from aware_meta_ontology.function.function_call_response import FunctionCallResponse
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_identity import (
    ObjectProjectionGraphIdentity,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.stable_ids import (
    stable_class_instance_identity_id,
    stable_function_call_id,
    stable_function_call_response_id,
    stable_object_config_graph_identity_id,
    stable_object_instance_graph_commit_id,
    stable_object_instance_graph_branch_id,
    stable_object_instance_graph_id,
    stable_object_instance_graph_identity_id,
    stable_object_instance_graph_lane_id,
    stable_object_projection_graph_identity_id,
)
from aware_utils.logging import logger


_SLOW_META_INVOCATION_COMMIT_THRESHOLD_MS = 1000
_SLOW_META_INVOCATION_TRACE_THRESHOLD_MS = 1000


@dataclass(frozen=True)
class MetaGraphStagedHandlerResult:
    staged_call: MetaGraphStagedFunctionCall
    request: MetaGraphInvokeFunctionInput
    execution_result: MetaGraphHandlerExecutionResult
    function_call_response: FunctionCallResponse


@dataclass(frozen=True)
class MetaGraphStagedCommitAction:
    staged_result: MetaGraphStagedHandlerResult
    action: MetaInvocationCommitAction


@dataclass(frozen=True)
class MetaGraphDomainCommitAppendRequest:
    staged_action: MetaGraphStagedCommitAction
    before_oig: ObjectInstanceGraph
    changes: tuple[ObjectInstanceGraphChange, ...]
    graph_hash_pre: str
    graph_hash_post: str
    body_draft: OigCommitBodyDraft | None = None
    root_object_id: UUID | None = None
    root_class_instance_identity_id: UUID | None = None
    materialization_cache_prime_snapshot: (
        MetaGraphMaterializationCachePrimeSnapshot | None
    ) = None


@dataclass(frozen=True)
class MetaGraphAggregateStagedPreState:
    before_oig: ObjectInstanceGraph
    graph_hash_pre: str
    root_object_id: UUID | None = None
    root_class_instance_identity_id: UUID | None = None


@dataclass(frozen=True)
class MetaGraphAppendedDomainCommit:
    append_request: MetaGraphDomainCommitAppendRequest
    append_result: InvocationDomainCommitAppendResult
    reaction_receipts: tuple[RuntimeCommitReactionReceipt, ...]
    identity_lane_head_ensure_result: (
        ObjectInstanceGraphIdentityLaneHeadEnsureResult | None
    ) = None
    required_reaction_batch_status: str | None = None


class MetaGraphCommitInvocationNotReadyError(RuntimeError):
    """Raised until the canonical Meta commit backend owns the full call path."""


class MetaGraphCommitInvocationBackend:
    """Canonical Meta-owned FunctionCall -> FunctionCallResponse -> OIG commit backend."""

    def __init__(
        self,
        *,
        handler_executor: MetaGraphHandlerExecutor | None = None,
        lane_committer: InvocationLaneCommitter | None = None,
        required_reaction_runner: InvocationRequiredReactionRunner | None = None,
        implementation_policy: MetaGraphImplementationPolicy | None = None,
    ) -> None:
        self._handler_executor = handler_executor
        self._lane_committer = lane_committer
        self._required_reaction_runner = required_reaction_runner
        self._implementation_policy = (
            implementation_policy or MetaGraphImplementationPolicy()
        )
        self._runtime_index_views: dict[int, MetaGraphRuntimeIndexView] = {}

    async def invoke_function(
        self, request: MetaGraphInvokeFunctionInput
    ) -> MetaGraphCommitReceipt:
        if current_commit_perf_trace() is not None:
            return await self._invoke_function_with_active_trace(request)

        recorder = CommitPerfTraceRecorder(
            default_category="meta.runtime.invoke_function"
        )
        started_at = perf_counter()
        with active_commit_perf_trace(recorder):
            receipt = await self._invoke_function_with_active_trace(request)
        duration_ms = max((perf_counter() - started_at) * 1000, 0.0)
        trace_summary = _log_slow_invocation_trace(
            request=request,
            receipt=receipt,
            duration_ms=duration_ms,
            events=recorder.snapshot_json(),
        )
        if trace_summary:
            receipt = replace(
                receipt,
                perf_trace_duration_ms=round(duration_ms, 3),
                perf_trace_summary=trace_summary,
            )
        return receipt

    async def invoke_function_aggregate(
        self,
        requests: Sequence[MetaGraphInvokeFunctionInput],
    ) -> Mapping[str, object]:
        request_tuple = tuple(requests)
        if current_commit_perf_trace() is not None:
            return await self._invoke_function_aggregate_with_active_trace(
                request_tuple,
            )

        recorder = CommitPerfTraceRecorder(
            default_category="meta.runtime.invoke_function"
        )
        with active_commit_perf_trace(recorder):
            return await self._invoke_function_aggregate_with_active_trace(
                request_tuple,
            )

    async def _invoke_function_aggregate_with_active_trace(
        self,
        requests: tuple[MetaGraphInvokeFunctionInput, ...],
    ) -> Mapping[str, object]:
        metadata = {
            "request_count": len(requests),
            "executor": "MetaGraphCommitInvocationBackend.invoke_function_aggregate",
        }
        receipts: list[MetaGraphCommitReceipt] = []
        with commit_perf_span(
            phase="runtime.invoke_function.aggregate.prepare",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            request_tuple = tuple(requests)
            staged_batch_blockers = _aggregate_staged_batch_preflight_blockers(
                requests=request_tuple,
                lane_committer=self._lane_committer,
            )
        if not staged_batch_blockers:
            with commit_perf_span(
                phase="runtime.invoke_function.aggregate.staged_batch",
                category="meta.runtime.invoke_function",
                metadata=metadata,
            ):
                return await self._invoke_function_aggregate_staged_batch(
                    request_tuple,
                    metadata=metadata,
                )
        expected_graph_hash_pre_by_lane: dict[tuple[UUID, str], str] = {}
        expected_head_commit_id_by_lane: dict[tuple[UUID, str], UUID] = {}
        for request_index, request in enumerate(request_tuple):
            invoke_request = _request_with_aggregate_lane_head(
                request=request,
                expected_graph_hash_pre_by_lane=expected_graph_hash_pre_by_lane,
                expected_head_commit_id_by_lane=expected_head_commit_id_by_lane,
            )
            with commit_perf_span(
                phase="runtime.invoke_function.aggregate.invoke_function",
                category="meta.runtime.invoke_function",
                metadata={
                    **metadata,
                    **_invoke_request_trace_metadata(invoke_request),
                    "request_index": request_index,
                },
            ):
                receipt = await self._invoke_function_with_active_trace(invoke_request)
                receipts.append(receipt)
            _record_aggregate_lane_head(
                receipt=receipt,
                expected_graph_hash_pre_by_lane=expected_graph_hash_pre_by_lane,
                expected_head_commit_id_by_lane=expected_head_commit_id_by_lane,
            )
        return {
            "commit_receipts": tuple(receipts),
            "aggregate_commit_execution": _aggregate_commit_execution_payload(
                receipts=tuple(receipts),
                request_count=len(request_tuple),
                lane_committer=self._lane_committer,
                staged_batch_blockers=staged_batch_blockers,
            ),
        }

    async def _invoke_function_aggregate_staged_batch(
        self,
        requests: tuple[MetaGraphInvokeFunctionInput, ...],
        *,
        metadata: Mapping[str, object],
    ) -> Mapping[str, object]:
        staged_actions: list[MetaGraphStagedCommitAction] = []
        staged_pre_state: MetaGraphAggregateStagedPreState | None = None
        for request_index, request in enumerate(requests):
            invoke_request = request
            if staged_pre_state is not None:
                invoke_request = replace(
                    request,
                    expected_graph_hash_pre=staged_pre_state.graph_hash_pre,
                    expected_head_commit_id=None,
                )
            with commit_perf_span(
                phase="runtime.invoke_function.aggregate.invoke_function",
                category="meta.runtime.invoke_function",
                metadata={
                    **metadata,
                    **_invoke_request_trace_metadata(invoke_request),
                    "request_index": request_index,
                    "aggregate_staged_batch": True,
                },
            ):
                pass
            with commit_perf_span(
                phase="runtime.invoke_function.stage_function_call",
                category="meta.runtime.invoke_function",
                metadata={
                    **metadata,
                    **_invoke_request_trace_metadata(invoke_request),
                    "request_index": request_index,
                    "aggregate_staged_batch": True,
                },
            ):
                staged_call = self.stage_function_call(invoke_request)
            call_metadata = {
                **metadata,
                **_invoke_staged_call_trace_metadata(
                    request=invoke_request,
                    staged_call=staged_call,
                ),
                "request_index": request_index,
                "aggregate_staged_batch": True,
            }
            with commit_perf_span(
                phase="runtime.invoke_function.execute_staged_function_call",
                category="meta.runtime.invoke_function",
                metadata=call_metadata,
            ):
                staged_result = await self.execute_staged_function_call(
                    request=invoke_request,
                    staged_call=staged_call,
                    staged_pre_state=staged_pre_state,
                )
            with commit_perf_span(
                phase="runtime.invoke_function.stage_commit_action",
                category="meta.runtime.invoke_function",
                metadata=call_metadata,
            ):
                staged_action = self.stage_commit_action(staged_result)
            staged_actions.append(staged_action)
            if request_index < len(requests) - 1:
                with commit_perf_span(
                    phase=(
                        "runtime.invoke_function.aggregate." "build_staged_pre_state"
                    ),
                    category="meta.runtime.invoke_function",
                    metadata=call_metadata,
                ):
                    append_request = self.build_domain_commit_append_request(
                        staged_action
                    )
                    staged_pre_state = (
                        self._aggregate_staged_pre_state_from_append_request(
                            append_request=append_request,
                        )
                    )

        with commit_perf_span(
            phase="runtime.invoke_function.append_domain_commit",
            category="meta.runtime.invoke_function",
            metadata={**metadata, "aggregate_staged_batch": True},
        ):
            with grouped_durable_write_transaction() as durable_transaction:
                appended_commits = await self.append_domain_commits_batch(
                    tuple(staged_actions)
                )
            durable_transaction_stats = durable_transaction.stats_snapshot()
        _record_aggregate_grouped_durable_transaction_metrics(
            stats=durable_transaction_stats,
            metadata=metadata,
        )
        with commit_perf_span(
            phase="runtime.invoke_function.build_commit_receipt",
            category="meta.runtime.invoke_function",
            metadata={**metadata, "aggregate_staged_batch": True},
        ):
            receipts = tuple(
                self.build_commit_receipt(appended_commit)
                for appended_commit in appended_commits
            )
        return {
            "commit_receipts": receipts,
            "aggregate_commit_execution": _aggregate_commit_execution_payload(
                receipts=receipts,
                request_count=len(requests),
                lane_committer=self._lane_committer,
                aggregate_batch_append_used=True,
                aggregate_required_reaction_batch_status=(
                    _aggregate_required_reaction_batch_status(appended_commits)
                ),
                durable_transaction_stats=durable_transaction_stats,
            ),
        }

    async def _invoke_function_with_active_trace(
        self, request: MetaGraphInvokeFunctionInput
    ) -> MetaGraphCommitReceipt:
        with commit_perf_span(
            phase="runtime.invoke_function.stage_function_call",
            category="meta.runtime.invoke_function",
            metadata=_invoke_request_trace_metadata(request),
        ):
            staged_call = self.stage_function_call(request)
        metadata = _invoke_staged_call_trace_metadata(
            request=request,
            staged_call=staged_call,
        )
        with commit_perf_span(
            phase="runtime.invoke_function.execute_staged_function_call",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            staged_result = await self.execute_staged_function_call(
                request=request,
                staged_call=staged_call,
            )
        with commit_perf_span(
            phase="runtime.invoke_function.stage_commit_action",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            staged_action = self.stage_commit_action(staged_result)
        with commit_perf_span(
            phase="runtime.invoke_function.append_domain_commit",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            appended_commit = await self.append_domain_commit(staged_action)
        with commit_perf_span(
            phase="runtime.invoke_function.build_commit_receipt",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            return self.build_commit_receipt(appended_commit)

    async def execute_staged_function_call(
        self,
        *,
        request: MetaGraphInvokeFunctionInput,
        staged_call: MetaGraphStagedFunctionCall,
        staged_pre_state: MetaGraphAggregateStagedPreState | None = None,
    ) -> MetaGraphStagedHandlerResult:
        if self._handler_executor is None:
            raise MetaGraphCommitInvocationNotReadyError(
                "MetaGraphCommitInvocationBackend is the canonical Meta-owned "
                "FunctionCall -> FunctionCallResponse -> OIG Commit backend. "
                "It staged FunctionCall, but handler execution is not wired yet. "
                f"Resolved function target={staged_call.resolved_target.operation_label} "
                f"function_id={staged_call.resolved_target.function_config.id} "
                f"function_call_id={staged_call.function_call.id}."
            )

        metadata = _invoke_staged_call_trace_metadata(
            request=request,
            staged_call=staged_call,
        )
        with commit_perf_span(
            phase="runtime.invoke_function.build_execution_plan",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            execution_plan = self.build_execution_plan(
                request=request,
                staged_call=staged_call,
            )
        with commit_perf_span(
            phase="runtime.invoke_function.handler_execute_function",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            handler_request = MetaGraphHandlerExecutionRequest(
                request=request,
                staged_call=staged_call,
                execution_plan=execution_plan,
                invoke_function=self.invoke_function,
            )
            if staged_pre_state is not None:
                with commit_perf_span(
                    phase=(
                        "runtime.invoke_function." "build_staged_pre_state_override"
                    ),
                    category="meta.runtime.invoke_function",
                    metadata=metadata,
                ):
                    handler_request = replace(
                        handler_request,
                        pre_state_override=build_meta_graph_pre_state(
                            request=handler_request,
                            snapshot=MetaGraphPreStateProviderResult(
                                before_oig=staged_pre_state.before_oig,
                                graph_hash_pre=staged_pre_state.graph_hash_pre,
                                head_commit_id=None,
                                root_object_id=staged_pre_state.root_object_id,
                                root_class_instance_identity_id=(
                                    staged_pre_state.root_class_instance_identity_id
                                ),
                            ),
                        ),
                    )
            execution_result = await self._handler_executor.execute_function(
                handler_request
            )
        with commit_perf_span(
            phase="runtime.invoke_function.stage_function_call_response",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            function_call_response = self.stage_function_call_response(
                function_call=staged_call.function_call,
                success=execution_result.success,
                error_message=execution_result.error_message,
                execution_time_ms=execution_result.execution_time_ms,
                graph_hash_post=execution_result.graph_hash_post,
                root_class_instance_identity_id=(
                    execution_result.root_class_instance_identity_id
                ),
            )
        return MetaGraphStagedHandlerResult(
            staged_call=staged_call,
            request=request,
            execution_result=execution_result,
            function_call_response=function_call_response,
        )

    def build_execution_plan(
        self,
        *,
        request: MetaGraphInvokeFunctionInput,
        staged_call: MetaGraphStagedFunctionCall,
    ) -> MetaGraphExecutionPlan:
        index = cast(MetaGraphRuntimeIndex, request.index)
        return build_meta_graph_execution_plan(
            index=index,
            request=request,
            staged_call=staged_call,
            index_view=self._runtime_index_view(index),
        )

    def stage_commit_action(
        self,
        staged_result: MetaGraphStagedHandlerResult,
    ) -> MetaGraphStagedCommitAction:
        request = staged_result.request
        staged_call = staged_result.staged_call
        execution_result = staged_result.execution_result
        call_target = request.call_target.value
        object_id = request.target_object_id
        class_instance_identity_id = (
            staged_call.function_call.target_class_instance_identity_id
        )
        if request.call_target is MetaGraphCallTarget.opg_constructor:
            object_id = execution_result.root_object_id
            class_instance_identity_id = (
                execution_result.root_class_instance_identity_id
            )
        elif class_instance_identity_id is None:
            class_instance_identity_id = (
                execution_result.root_class_instance_identity_id
            )

        action = MetaInvocationCommitAction(
            operation_label=staged_call.resolved_target.operation_label,
            call_target=call_target,
            function_id=staged_call.resolved_target.function_config.id,
            object_id=object_id,
            class_instance_identity_id=class_instance_identity_id,
        )
        return MetaGraphStagedCommitAction(
            staged_result=staged_result,
            action=action,
        )

    async def append_domain_commit(
        self,
        staged_action: MetaGraphStagedCommitAction,
    ) -> MetaGraphAppendedDomainCommit:
        metadata = _invoke_staged_call_trace_metadata(
            request=staged_action.staged_result.request,
            staged_call=staged_action.staged_result.staged_call,
        )
        with commit_perf_span(
            phase="runtime.invoke_function.build_domain_commit_append_request",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            append_request = self.build_domain_commit_append_request(staged_action)
        staged_result = staged_action.staged_result
        lane_scope = staged_result.staged_call.lane_scope
        execution_result = staged_result.execution_result
        ensure_perf_ms: dict[str, int] = {}
        identity_lane_head_ensure_result = None
        with commit_perf_span(
            phase="runtime.invoke_function.ensure_identity_lane_head",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            identity_lane_head_ensure_result = await self._ensure_object_instance_graph_identity_lane_head_for_domain_commit(
                staged_action=staged_action,
                perf_ms=ensure_perf_ms,
            )
        with commit_perf_span(
            phase="runtime.invoke_function.append_invocation_domain_commit",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            append_result = await append_invocation_domain_commit(
                branch_id=lane_scope.domain_branch_id,
                projection_hash=lane_scope.domain_projection_hash,
                object_projection_graph_identity_id=(
                    lane_scope.object_projection_graph_identity_id
                ),
                object_instance_graph_identity_id=(
                    lane_scope.object_instance_graph_identity_id
                ),
                object_instance_graph_id=lane_scope.object_instance_graph_id,
                before_oig=append_request.before_oig,
                root_object_id=(
                    execution_result.root_object_id or append_request.root_object_id
                ),
                changes=list(append_request.changes),
                body_draft=append_request.body_draft,
                graph_hash_pre=append_request.graph_hash_pre,
                graph_hash_post=append_request.graph_hash_post,
                author_id=staged_result.request.actor_id,
                action=staged_action.action,
                committer=self._lane_committer,
            )
        with commit_perf_span(
            phase="runtime.invoke_function.prime_domain_materialization_cache",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            self._prime_domain_materialization_cache(
                staged_action=staged_action,
                append_request=append_request,
                append_result=append_result,
            )
        if ensure_perf_ms:
            append_result = InvocationDomainCommitAppendResult(
                commit=append_result.commit,
                perf_profile={
                    **ensure_perf_ms,
                    **append_result.perf_profile,
                },
            )
        with commit_perf_span(
            phase="runtime.invoke_function.link_function_call_response_commit",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            link_function_call_response_commit(
                response=staged_result.function_call_response,
                oig_commit=append_result.commit,
            )
        with commit_perf_span(
            phase="runtime.invoke_function.required_commit_reactions",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            reaction_receipts = await self.run_required_commit_reactions(
                staged_action=staged_action,
                append_result=append_result,
            )
        perf_profile = append_result.perf_profile
        if (
            max(perf_profile.values(), default=0)
            >= _SLOW_META_INVOCATION_COMMIT_THRESHOLD_MS
        ):
            logger.info(
                "Meta invocation commit slow path "
                "operation_label=%s branch_id=%s projection_hash=%s commit_id=%s "
                "object_instance_graph_commit_id=%s perf_ms=%s",
                staged_action.action.operation_label,
                lane_scope.domain_branch_id,
                lane_scope.domain_projection_hash,
                (
                    append_result.commit.commit.id
                    if append_result.commit is not None
                    else None
                ),
                append_result.commit.id if append_result.commit is not None else None,
                perf_profile,
            )
        return MetaGraphAppendedDomainCommit(
            append_request=append_request,
            append_result=append_result,
            reaction_receipts=reaction_receipts,
            identity_lane_head_ensure_result=identity_lane_head_ensure_result,
        )

    async def append_domain_commits_batch(
        self,
        staged_actions: tuple[MetaGraphStagedCommitAction, ...],
    ) -> tuple[MetaGraphAppendedDomainCommit, ...]:
        if not staged_actions:
            return ()
        append_requests: list[MetaGraphDomainCommitAppendRequest] = []
        for staged_action in staged_actions:
            metadata = _invoke_staged_call_trace_metadata(
                request=staged_action.staged_result.request,
                staged_call=staged_action.staged_result.staged_call,
            )
            with commit_perf_span(
                phase="runtime.invoke_function.build_domain_commit_append_request",
                category="meta.runtime.invoke_function",
                metadata={**metadata, "aggregate_staged_batch": True},
            ):
                append_requests.append(
                    self.build_domain_commit_append_request(staged_action)
                )

        first_request = append_requests[0]
        first_staged_action = first_request.staged_action
        first_staged_result = first_staged_action.staged_result
        lane_scope = first_staged_result.staged_call.lane_scope
        metadata = {
            **_invoke_staged_call_trace_metadata(
                request=first_staged_result.request,
                staged_call=first_staged_result.staged_call,
            ),
            "aggregate_staged_batch": True,
            "batch_request_count": len(append_requests),
        }
        ensure_perf_ms: dict[str, int] = {}
        identity_lane_head_ensure_result = None
        with commit_perf_span(
            phase="runtime.invoke_function.ensure_identity_lane_head",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            identity_lane_head_ensure_result = await self._ensure_object_instance_graph_identity_lane_head_for_domain_commit(
                staged_action=first_staged_action,
                perf_ms=ensure_perf_ms,
            )

        with commit_perf_span(
            phase="runtime.invoke_function.append_invocation_domain_commit",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            append_results = await append_invocation_domain_commit_batch(
                branch_id=lane_scope.domain_branch_id,
                projection_hash=lane_scope.domain_projection_hash,
                requests=tuple(
                    build_invocation_lane_commit_batch_request(
                        object_projection_graph_identity_id=(
                            request.staged_action.staged_result.staged_call.lane_scope.object_projection_graph_identity_id
                        ),
                        object_instance_graph_identity_id=(
                            request.staged_action.staged_result.staged_call.lane_scope.object_instance_graph_identity_id
                        ),
                        object_instance_graph_id=(
                            request.staged_action.staged_result.staged_call.lane_scope.object_instance_graph_id
                        ),
                        before_oig=request.before_oig,
                        root_object_id=(
                            request.staged_action.staged_result.execution_result.root_object_id
                            or request.root_object_id
                        ),
                        changes=request.changes,
                        body_draft=request.body_draft,
                        graph_hash_pre=request.graph_hash_pre,
                        graph_hash_post=request.graph_hash_post,
                        author_id=request.staged_action.staged_result.request.actor_id,
                        action=request.staged_action.action,
                    )
                    for request in append_requests
                ),
                committer=self._lane_committer,
            )

        appended_commits: list[MetaGraphAppendedDomainCommit] = []
        for index, (append_request, append_result) in enumerate(
            zip(append_requests, append_results, strict=True)
        ):
            staged_action = append_request.staged_action
            staged_result = staged_action.staged_result
            item_metadata = {
                **_invoke_staged_call_trace_metadata(
                    request=staged_result.request,
                    staged_call=staged_result.staged_call,
                ),
                "aggregate_staged_batch": True,
                "batch_request_index": index,
            }
            with commit_perf_span(
                phase="runtime.invoke_function.prime_domain_materialization_cache",
                category="meta.runtime.invoke_function",
                metadata=item_metadata,
            ):
                self._prime_domain_materialization_cache(
                    staged_action=staged_action,
                    append_request=append_request,
                    append_result=append_result,
                )
            if index == 0 and ensure_perf_ms:
                append_result = InvocationDomainCommitAppendResult(
                    commit=append_result.commit,
                    perf_profile={
                        **ensure_perf_ms,
                        **append_result.perf_profile,
                    },
                )
            with commit_perf_span(
                phase="runtime.invoke_function.link_function_call_response_commit",
                category="meta.runtime.invoke_function",
                metadata=item_metadata,
            ):
                link_function_call_response_commit(
                    response=staged_result.function_call_response,
                    oig_commit=append_result.commit,
                )
            appended_commit = MetaGraphAppendedDomainCommit(
                append_request=append_request,
                append_result=append_result,
                reaction_receipts=(),
                identity_lane_head_ensure_result=(
                    identity_lane_head_ensure_result if index == 0 else None
                ),
            )
            self._log_slow_domain_commit(staged_action, append_result)
            appended_commits.append(appended_commit)

        if self._required_reaction_runner is None:
            with commit_perf_span(
                phase="runtime.invoke_function.required_commit_reactions_batch",
                category="meta.runtime.invoke_function",
                metadata=metadata,
            ):
                reaction_receipts_by_commit = (
                    await self.run_required_commit_reactions_batch(
                        appended_commits=tuple(appended_commits),
                    )
                )
            appended_commits = [
                replace(
                    appended_commit,
                    reaction_receipts=reaction_receipts,
                    required_reaction_batch_status="succeeded",
                )
                for appended_commit, reaction_receipts in zip(
                    appended_commits,
                    reaction_receipts_by_commit,
                    strict=True,
                )
            ]
        else:
            fallback_appended_commits: list[MetaGraphAppendedDomainCommit] = []
            for index, appended_commit in enumerate(appended_commits):
                append_request = appended_commit.append_request
                staged_action = append_request.staged_action
                staged_result = staged_action.staged_result
                item_metadata = {
                    **_invoke_staged_call_trace_metadata(
                        request=staged_result.request,
                        staged_call=staged_result.staged_call,
                    ),
                    "aggregate_staged_batch": True,
                    "batch_request_index": index,
                    "required_reaction_batch_status": "fallback_independent",
                }
                with commit_perf_span(
                    phase="runtime.invoke_function.required_commit_reactions",
                    category="meta.runtime.invoke_function",
                    metadata=item_metadata,
                ):
                    reaction_receipts = await self.run_required_commit_reactions(
                        staged_action=staged_action,
                        append_result=appended_commit.append_result,
                    )
                fallback_appended_commits.append(
                    replace(
                        appended_commit,
                        reaction_receipts=reaction_receipts,
                        required_reaction_batch_status="fallback_independent",
                    )
                )
            appended_commits = fallback_appended_commits
        return tuple(appended_commits)

    def _aggregate_staged_pre_state_from_append_request(
        self,
        *,
        append_request: MetaGraphDomainCommitAppendRequest,
    ) -> MetaGraphAggregateStagedPreState:
        staged_action = append_request.staged_action
        staged_result = staged_action.staged_result
        snapshot = _validated_cache_prime_snapshot(
            staged_action=staged_action,
            append_request=append_request,
        )
        if snapshot is not None:
            post_oig = snapshot.post_oig
        else:
            index = cast(MetaGraphRuntimeIndex, staged_result.request.index)
            post_oig = append_request.before_oig.model_copy(deep=True)
            if append_request.body_draft is not None:
                apply_object_instance_graph_body_draft(
                    graph=post_oig,
                    body_draft=append_request.body_draft,
                    attribute_configs_by_id=index.attribute_configs_by_id,
                    class_configs_by_id=index.class_configs_by_id,
                )
            else:
                apply_object_instance_graph_changes(
                    graph=post_oig,
                    changes=append_request.changes,
                    attribute_configs_by_id=index.attribute_configs_by_id,
                    class_configs_by_id=index.class_configs_by_id,
                )
        post_oig.hash = append_request.graph_hash_post
        return MetaGraphAggregateStagedPreState(
            before_oig=post_oig,
            graph_hash_pre=append_request.graph_hash_post,
            root_object_id=(
                staged_result.execution_result.root_object_id
                or append_request.root_object_id
            ),
            root_class_instance_identity_id=(
                staged_result.execution_result.root_class_instance_identity_id
                or append_request.root_class_instance_identity_id
            ),
        )

    def _log_slow_domain_commit(
        self,
        staged_action: MetaGraphStagedCommitAction,
        append_result: InvocationDomainCommitAppendResult,
    ) -> None:
        perf_profile = append_result.perf_profile
        if (
            max(perf_profile.values(), default=0)
            < _SLOW_META_INVOCATION_COMMIT_THRESHOLD_MS
        ):
            return
        lane_scope = staged_action.staged_result.staged_call.lane_scope
        logger.info(
            "Meta invocation commit slow path "
            "operation_label=%s branch_id=%s projection_hash=%s commit_id=%s "
            "object_instance_graph_commit_id=%s perf_ms=%s",
            staged_action.action.operation_label,
            lane_scope.domain_branch_id,
            lane_scope.domain_projection_hash,
            (
                append_result.commit.commit.id
                if append_result.commit is not None
                else None
            ),
            append_result.commit.id if append_result.commit is not None else None,
            perf_profile,
        )

    def _prime_domain_materialization_cache(
        self,
        *,
        staged_action: MetaGraphStagedCommitAction,
        append_request: MetaGraphDomainCommitAppendRequest,
        append_result: InvocationDomainCommitAppendResult,
    ) -> None:
        domain_commit = append_result.commit
        if domain_commit is None:
            return

        staged_result = staged_action.staged_result
        lane_scope = staged_result.staged_call.lane_scope
        index = cast(MetaGraphRuntimeIndex, staged_result.request.index)
        metadata = {
            **_invoke_staged_call_trace_metadata(
                request=staged_result.request,
                staged_call=staged_result.staged_call,
            ),
            "branch_id": lane_scope.domain_branch_id,
            "projection_hash": lane_scope.domain_projection_hash,
            "commit_id": domain_commit.commit.id,
            "object_instance_graph_id": lane_scope.object_instance_graph_id,
            "change_count": len(append_request.changes),
        }
        with commit_perf_span(
            phase=(
                "runtime.invoke_function.prime_domain_materialization_cache."
                "resolve_opg"
            ),
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            opg = index.opg_by_hash.get(lane_scope.domain_projection_hash)
        if opg is None:
            return

        try:
            snapshot = _validated_cache_prime_snapshot(
                staged_action=staged_action,
                append_request=append_request,
            )
            if snapshot is not None:
                with commit_perf_span(
                    phase=(
                        "runtime.invoke_function.prime_domain_materialization_cache."
                        "use_post_oig_snapshot"
                    ),
                    category="meta.runtime.invoke_function",
                    metadata=metadata,
                ):
                    post_oig = snapshot.post_oig
            else:
                with commit_perf_span(
                    phase=(
                        "runtime.invoke_function.prime_domain_materialization_cache."
                        "copy_before_oig"
                    ),
                    category="meta.runtime.invoke_function",
                    metadata=metadata,
                ):
                    post_oig = append_request.before_oig.model_copy(deep=True)
                with commit_perf_span(
                    phase=(
                        "runtime.invoke_function.prime_domain_materialization_cache."
                        "apply_changes"
                    ),
                    category="meta.runtime.invoke_function",
                    metadata=metadata,
                ):
                    if append_request.body_draft is not None:
                        apply_object_instance_graph_body_draft(
                            graph=post_oig,
                            body_draft=append_request.body_draft,
                            attribute_configs_by_id=index.attribute_configs_by_id,
                            class_configs_by_id=index.class_configs_by_id,
                        )
                    else:
                        apply_object_instance_graph_changes(
                            graph=post_oig,
                            changes=append_request.changes,
                            attribute_configs_by_id=index.attribute_configs_by_id,
                            class_configs_by_id=index.class_configs_by_id,
                        )
            with commit_perf_span(
                phase=(
                    "runtime.invoke_function.prime_domain_materialization_cache."
                    "assign_hash"
                ),
                category="meta.runtime.invoke_function",
                metadata=metadata,
            ):
                post_oig.hash = append_request.graph_hash_post
            with commit_perf_span(
                phase=(
                    "runtime.invoke_function.prime_domain_materialization_cache."
                    "prime_cache"
                ),
                category="meta.runtime.invoke_function",
                metadata=metadata,
            ):
                CachedLaneMaterializer().prime(
                    branch_id=lane_scope.domain_branch_id,
                    opg=opg,
                    commit_id=domain_commit.commit.id,
                    oig_id=lane_scope.object_instance_graph_id,
                    graph=post_oig,
                )
        except Exception as exc:
            logger.warning(
                "Meta domain materialization cache prime skipped "
                "operation_label=%s branch_id=%s projection_hash=%s commit_id=%s "
                "reason=%s",
                staged_action.action.operation_label,
                lane_scope.domain_branch_id,
                lane_scope.domain_projection_hash,
                domain_commit.commit.id,
                exc,
            )

    async def _ensure_object_instance_graph_identity_lane_head_for_domain_commit(
        self,
        *,
        staged_action: MetaGraphStagedCommitAction,
        perf_ms: dict[str, int],
    ) -> ObjectInstanceGraphIdentityLaneHeadEnsureResult | None:
        staged_result = staged_action.staged_result
        lane_scope = staged_result.staged_call.lane_scope
        if not hasattr(staged_result.request.index.ocg, "object_projection_graphs"):
            return None
        oigi_ctx = resolve_object_instance_graph_identity_lane_context(
            index=staged_result.request.index,
        )
        if oigi_ctx is None:
            return None
        if lane_scope.domain_projection_hash == oigi_ctx.projection_hash:
            return None
        return await ensure_object_instance_graph_identity_lane_head(
            index=staged_result.request.index,
            index_view=self._runtime_index_view(
                cast(MetaGraphCommitIndex, staged_result.request.index)
            ),
            object_instance_graph_id=lane_scope.object_instance_graph_id,
            domain_projection_hash=lane_scope.domain_projection_hash,
            author_id=staged_result.request.actor_id,
            label=staged_action.action.operation_label,
            perf_ms=perf_ms,
            perf_metric_prefix="domain_commit_oigi_lane_ensure",
        )

    async def run_required_commit_reactions(
        self,
        *,
        staged_action: MetaGraphStagedCommitAction,
        append_result: InvocationDomainCommitAppendResult,
    ) -> tuple[RuntimeCommitReactionReceipt, ...]:
        domain_commit = append_result.commit
        if domain_commit is None:
            return ()

        staged_result = staged_action.staged_result
        lane_scope = staged_result.staged_call.lane_scope
        reaction_runner = self._required_reaction_runner
        if reaction_runner is None:
            return await run_invocation_required_commit_reactions(
                index=staged_result.request.index,
                index_view=self._runtime_index_view(
                    cast(MetaGraphCommitIndex, staged_result.request.index)
                ),
                actor_id=staged_result.request.actor_id,
                domain_branch_id=lane_scope.domain_branch_id,
                domain_projection_hash=lane_scope.domain_projection_hash,
                domain_commit=domain_commit,
                action=staged_action.action,
                perf_ms=append_result.perf_profile,
            )

        return await run_invocation_required_commit_reactions(
            index=staged_result.request.index,
            index_view=self._runtime_index_view(
                cast(MetaGraphCommitIndex, staged_result.request.index)
            ),
            actor_id=staged_result.request.actor_id,
            domain_branch_id=lane_scope.domain_branch_id,
            domain_projection_hash=lane_scope.domain_projection_hash,
            domain_commit=domain_commit,
            action=staged_action.action,
            perf_ms=append_result.perf_profile,
            runner=reaction_runner,
        )

    async def run_required_commit_reactions_batch(
        self,
        *,
        appended_commits: tuple[MetaGraphAppendedDomainCommit, ...],
    ) -> tuple[tuple[RuntimeCommitReactionReceipt, ...], ...]:
        items: list[InvocationRequiredReactionBatchItem] = []
        item_positions: list[int] = []
        receipts_by_position: list[tuple[RuntimeCommitReactionReceipt, ...]] = [
            () for _ in appended_commits
        ]
        for index, appended_commit in enumerate(appended_commits):
            domain_commit = appended_commit.append_result.commit
            if domain_commit is None:
                continue
            staged_action = appended_commit.append_request.staged_action
            staged_result = staged_action.staged_result
            lane_scope = staged_result.staged_call.lane_scope
            items.append(
                InvocationRequiredReactionBatchItem(
                    index=staged_result.request.index,
                    index_view=self._runtime_index_view(
                        cast(MetaGraphCommitIndex, staged_result.request.index)
                    ),
                    actor_id=staged_result.request.actor_id,
                    domain_branch_id=lane_scope.domain_branch_id,
                    domain_projection_hash=lane_scope.domain_projection_hash,
                    domain_commit=domain_commit,
                    action=staged_action.action,
                    perf_ms=appended_commit.append_result.perf_profile,
                )
            )
            item_positions.append(index)
        if not items:
            return tuple(receipts_by_position)

        batch_receipts = await run_invocation_required_commit_reactions_batch(
            items=tuple(items),
        )
        for position, receipts in zip(item_positions, batch_receipts, strict=True):
            receipts_by_position[position] = receipts
        return tuple(receipts_by_position)

    def build_domain_commit_append_request(
        self,
        staged_action: MetaGraphStagedCommitAction,
    ) -> MetaGraphDomainCommitAppendRequest:
        staged_result = staged_action.staged_result
        execution_result = staged_result.execution_result
        append_ready = execution_result.append_ready_changes
        if append_ready is not None:
            if append_ready.execution_plan.staged_call is not staged_result.staged_call:
                raise ValueError(
                    "Meta append-ready changes were built for a different "
                    "staged FunctionCall."
                )
            return MetaGraphDomainCommitAppendRequest(
                staged_action=staged_action,
                before_oig=append_ready.before_oig,
                changes=append_ready.changes,
                body_draft=append_ready.body_draft,
                graph_hash_pre=append_ready.graph_hash_pre,
                graph_hash_post=append_ready.graph_hash_post,
                root_object_id=append_ready.root_object_id,
                root_class_instance_identity_id=(
                    append_ready.root_class_instance_identity_id
                ),
                materialization_cache_prime_snapshot=(
                    append_ready.materialization_cache_prime_snapshot
                ),
            )

        before_oig = execution_result.before_oig
        if before_oig is None:
            raise self._commit_append_not_ready(
                staged_action=staged_action,
                missing_field="before_oig",
            )

        graph_hash_pre = (
            execution_result.graph_hash_pre
            or staged_result.staged_call.function_call.graph_hash_pre
        )
        if not graph_hash_pre:
            raise self._commit_append_not_ready(
                staged_action=staged_action,
                missing_field="graph_hash_pre",
            )
        graph_hash_post = execution_result.graph_hash_post
        if not graph_hash_post:
            raise self._commit_append_not_ready(
                staged_action=staged_action,
                missing_field="graph_hash_post",
            )

        return MetaGraphDomainCommitAppendRequest(
            staged_action=staged_action,
            before_oig=before_oig,
            changes=execution_result.changes,
            body_draft=execution_result.body_draft,
            graph_hash_pre=graph_hash_pre,
            graph_hash_post=graph_hash_post,
            root_object_id=execution_result.root_object_id,
            root_class_instance_identity_id=(
                execution_result.root_class_instance_identity_id
            ),
            materialization_cache_prime_snapshot=(
                execution_result.materialization_cache_prime_snapshot
            ),
        )

    def build_commit_receipt(
        self,
        appended_commit: MetaGraphAppendedDomainCommit,
    ) -> MetaGraphCommitReceipt:
        append_request = appended_commit.append_request
        staged_action = append_request.staged_action
        staged_result = staged_action.staged_result
        execution_result = staged_result.execution_result
        response = staged_result.function_call_response
        domain_commit = appended_commit.append_result.commit
        commit_id = None
        object_instance_graph_commit_id = None
        graph_hash_pre = append_request.graph_hash_pre
        graph_hash_post = append_request.graph_hash_post
        root_object_id = (
            execution_result.root_object_id or append_request.root_object_id
        )
        if domain_commit is not None:
            commit_id = domain_commit.commit.id
            object_instance_graph_commit_id = stable_object_instance_graph_commit_id(
                object_instance_graph_identity_id=(
                    domain_commit.object_instance_graph_identity_id
                ),
                commit_id=commit_id,
            )
            graph_hash_pre = domain_commit.graph_hash_pre
            graph_hash_post = domain_commit.graph_hash_post
            root_object_id = domain_commit.root_source_object_id

        return MetaGraphCommitReceipt(
            status="succeeded" if execution_result.success else "failed",
            actor_id=staged_result.request.actor_id,
            domain_branch_id=staged_result.staged_call.lane_scope.domain_branch_id,
            domain_projection_hash=(
                staged_result.staged_call.lane_scope.domain_projection_hash
            ),
            payload=execution_result.payload,
            error=execution_result.error_message,
            execution_time_ms=execution_result.execution_time_ms,
            root_object_id=root_object_id,
            graph_hash_pre=graph_hash_pre,
            graph_hash_post=graph_hash_post,
            changes=_changes_json_array(append_request.changes),
            function_call_id=staged_result.staged_call.function_call.id,
            function_call_response_id=response.id,
            commit_id=commit_id,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
            commit_action=staged_action.action,
            logs=_reaction_logs(appended_commit.reaction_receipts),
            commit_group=_commit_group_evidence(appended_commit),
        )

    def _commit_append_not_ready(
        self,
        *,
        staged_action: MetaGraphStagedCommitAction,
        missing_field: str,
    ) -> MetaGraphCommitInvocationNotReadyError:
        staged_result = staged_action.staged_result
        staged_call = staged_result.staged_call
        response = staged_result.function_call_response
        return MetaGraphCommitInvocationNotReadyError(
            "MetaGraphCommitInvocationBackend is the canonical Meta-owned "
            "FunctionCall -> FunctionCallResponse -> OIG Commit backend, but "
            f"OIG commit append requires handler result {missing_field}. "
            f"Resolved function target={staged_call.resolved_target.operation_label} "
            f"function_id={staged_call.resolved_target.function_config.id} "
            f"function_call_id={staged_call.function_call.id} "
            f"function_call_response_id={response.id} "
            f"commit_action={staged_action.action.operation_label}."
        )

    def resolve_function_target(
        self,
        request: MetaGraphInvokeFunctionInput,
    ) -> MetaGraphResolvedFunctionTarget:
        return self._runtime_index_view(
            cast(MetaGraphCommitIndex, request.index)
        ).resolve_function_target(request.function_id)

    def stage_function_call(
        self,
        request: MetaGraphInvokeFunctionInput,
    ) -> MetaGraphStagedFunctionCall:
        resolved_target = self.resolve_function_target(request)
        index = cast(MetaGraphCommitIndex, request.index)
        lane_scope = resolve_meta_graph_invocation_lane_scope(
            index=index,
            request=request,
        )
        call_key = request.call_key or uuid4()
        target_class_instance_identity_id = None
        if request.target_object_id is not None:
            target_class_instance_identity_id = stable_class_instance_identity_id(
                object_instance_graph_identity_id=(
                    lane_scope.object_instance_graph_identity_id
                ),
                class_instance_id=request.target_object_id,
            )

        function_call = FunctionCall(
            id=stable_function_call_id(
                object_instance_graph_lane_id=lane_scope.object_instance_graph_lane_id,
                function_config_id=resolved_target.function_config.id,
                call_key=call_key,
            ),
            object_instance_graph_lane_id=lane_scope.object_instance_graph_lane_id,
            call_key=call_key,
            function_config=resolved_target.function_config,
            function_config_id=resolved_target.function_config.id,
            target_class_instance_identity_id=target_class_instance_identity_id,
            base_commit_id=None,
            graph_hash_pre=request.expected_graph_hash_pre,
        )
        return MetaGraphStagedFunctionCall(
            resolved_target=resolved_target,
            lane_scope=lane_scope,
            function_call=function_call,
        )

    def stage_function_call_response(
        self,
        *,
        function_call: FunctionCall,
        success: bool,
        error_message: str | None = None,
        execution_time_ms: int = 0,
        graph_hash_post: str | None = None,
        root_class_instance_identity_id: UUID | None = None,
    ) -> FunctionCallResponse:
        function_call_id = function_call.id
        if function_call_id is None:
            raise RuntimeError(
                "MetaGraphCommitInvocationBackend cannot stage response without "
                "FunctionCall.id"
            )
        response = FunctionCallResponse(
            id=stable_function_call_response_id(function_call_id=function_call_id),
            function_call_id=function_call_id,
            success=success,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
            graph_hash_post=graph_hash_post,
            root_class_instance_identity_id=root_class_instance_identity_id,
        )
        function_call.function_call_response = response
        return response

    def _runtime_index_view(
        self,
        index: MetaGraphCommitIndex,
    ) -> MetaGraphRuntimeIndexView:
        cache_key = id(index)
        index_view = self._runtime_index_views.get(cache_key)
        if index_view is None:
            index_view = MetaGraphRuntimeIndexView(
                index=index,
                implementation_policy=self._implementation_policy,
            )
            self._runtime_index_views[cache_key] = index_view
        return index_view


def _invoke_request_trace_metadata(
    request: MetaGraphInvokeFunctionInput,
) -> dict[str, object]:
    return {
        "call_target": request.call_target.value,
        "domain_projection_hash": request.domain_projection_hash,
        "function_id": request.function_id,
    }


def _aggregate_commit_execution_payload(
    *,
    receipts: tuple[MetaGraphCommitReceipt, ...],
    request_count: int,
    lane_committer: InvocationLaneCommitter | None,
    aggregate_batch_append_used: bool = False,
    aggregate_required_reaction_batch_status: str | None = None,
    durable_transaction_stats: Mapping[str, object] | None = None,
    staged_batch_blockers: tuple[str, ...] = (),
) -> dict[str, object]:
    role_counts: Counter[str] = Counter()
    durability_policies: set[str] = set()
    for receipt in receipts:
        commit_group = receipt.commit_group
        if commit_group is None:
            continue
        role_counts.update(commit_group.role_counts)
        if commit_group.durability_policy:
            durability_policies.add(commit_group.durability_policy)
    batch_api_available = _invocation_lane_committer_batch_api_available(lane_committer)
    durable_transaction_write_count = _mapping_int(
        durable_transaction_stats,
        "write_count",
    )
    durable_transaction_status = (
        "implemented"
        if aggregate_batch_append_used and durable_transaction_write_count > 0
        else "not_implemented"
    )
    if aggregate_batch_append_used:
        required_reaction_batch_status = (
            aggregate_required_reaction_batch_status or "not_attempted"
        )
        required_reaction_batch_succeeded = (
            required_reaction_batch_status == "succeeded"
        )
        status = (
            "succeeded"
            if (
                durable_transaction_status == "implemented"
                and required_reaction_batch_succeeded
            )
            else "partial"
        )
        if durable_transaction_status == "implemented":
            durability_policy = (
                "aggregate_grouped_durable_transaction_required_reactions_batch"
                if required_reaction_batch_succeeded
                else "aggregate_grouped_durable_transaction_required_reactions_independent"
            )
        else:
            durability_policy = (
                "domain_batch_append_required_reactions_batch"
                if required_reaction_batch_succeeded
                else "domain_batch_append_required_reactions_independent"
            )
        aggregate_uncommitted_session_state_status = "implemented"
        aggregate_domain_batch_append_status = "succeeded"
        blockers = []
        if durable_transaction_status != "implemented":
            blockers.append("aggregate_commit_durable_transaction_not_implemented")
        if not required_reaction_batch_succeeded:
            blockers.append("aggregate_commit_required_reaction_batch_not_implemented")
    else:
        status = "not_implemented"
        durability_policy = "independent_append"
        aggregate_uncommitted_session_state_status = "not_implemented"
        aggregate_domain_batch_append_status = "not_attempted"
        required_reaction_batch_status = "not_attempted"
        blockers = [
            "aggregate_commit_not_implemented",
            "aggregate_commit_durable_transaction_not_implemented",
        ]
    if staged_batch_blockers:
        blockers.extend(staged_batch_blockers)
    elif not aggregate_batch_append_used:
        if batch_api_available:
            blockers.append(
                "aggregate_commit_uncommitted_session_state_not_implemented"
            )
        else:
            blockers.append("invocation_lane_committer_batch_api_unavailable")
    return {
        "status": status,
        "backend_status": "invoked",
        "backend_invoked": True,
        "executor": "MetaGraphCommitInvocationBackend.invoke_function_aggregate",
        "request_count": request_count,
        "receipt_count": len(receipts),
        "durable_transaction_status": durable_transaction_status,
        "durable_transaction_write_count": durable_transaction_write_count,
        "durable_transaction_syncfs_count": _mapping_int(
            durable_transaction_stats,
            "syncfs_count",
        ),
        "durable_transaction_file_fsync_count": _mapping_int(
            durable_transaction_stats,
            "file_fsync_count",
        ),
        "durable_transaction_directory_fsync_count": _mapping_int(
            durable_transaction_stats,
            "directory_fsync_count",
        ),
        "durable_transaction_storage_status": (
            _optional_text(
                durable_transaction_stats.get("status")
                if isinstance(durable_transaction_stats, Mapping)
                else None
            )
        ),
        "durability_policy": durability_policy,
        "observed_durability_policies": tuple(sorted(durability_policies)),
        "observed_role_counts": dict(sorted(role_counts.items())),
        "invocation_lane_committer_batch_api_available": batch_api_available,
        "aggregate_batch_append_used": aggregate_batch_append_used,
        "aggregate_uncommitted_session_state_status": (
            aggregate_uncommitted_session_state_status
        ),
        "aggregate_domain_batch_append_status": aggregate_domain_batch_append_status,
        "aggregate_required_reaction_batch_status": (required_reaction_batch_status),
        "aggregate_batch_append_blockers": tuple(staged_batch_blockers),
        "blockers": tuple(dict.fromkeys(blockers)),
    }


def _record_aggregate_grouped_durable_transaction_metrics(
    *,
    stats: Mapping[str, object],
    metadata: Mapping[str, object],
) -> None:
    write_count = _mapping_int(stats, "write_count")
    if write_count <= 0:
        return
    phase_metadata = {
        **metadata,
        "transaction_write_count": write_count,
        "transaction_status": _optional_text(stats.get("status")) or "unknown",
    }
    with commit_perf_span(
        phase="runtime.invoke_function.aggregate.grouped_durable_transaction_committed",
        category="meta.runtime.invoke_function",
        metadata=phase_metadata,
    ):
        pass
    for _index in range(write_count):
        with commit_perf_span(
            phase="runtime.invoke_function.aggregate.grouped_durable_transaction_write",
            category="meta.runtime.invoke_function",
            metadata=phase_metadata,
        ):
            pass
    for _index in range(_mapping_int(stats, "syncfs_count")):
        with commit_perf_span(
            phase="runtime.invoke_function.aggregate.grouped_durable_transaction_syncfs",
            category="meta.runtime.invoke_function",
            metadata=phase_metadata,
        ):
            pass
    for _index in range(_mapping_int(stats, "file_fsync_count")):
        with commit_perf_span(
            phase="runtime.invoke_function.aggregate.grouped_durable_transaction_file_fsync",
            category="meta.runtime.invoke_function",
            metadata=phase_metadata,
        ):
            pass


def _mapping_int(values: Mapping[str, object] | None, key: str) -> int:
    if not isinstance(values, Mapping):
        return 0
    try:
        return max(int(cast(Any, values.get(key, 0))), 0)
    except Exception:
        return 0


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _aggregate_required_reaction_batch_status(
    appended_commits: tuple[MetaGraphAppendedDomainCommit, ...],
) -> str | None:
    statuses = {
        appended_commit.required_reaction_batch_status
        for appended_commit in appended_commits
        if appended_commit.required_reaction_batch_status is not None
    }
    if not statuses:
        return None
    if statuses == {"succeeded"}:
        return "succeeded"
    if "fallback_independent" in statuses:
        return "fallback_independent"
    return sorted(statuses)[0]


def _invocation_lane_committer_batch_api_available(
    lane_committer: InvocationLaneCommitter | None,
) -> bool:
    if lane_committer is None:
        return True
    return callable(getattr(lane_committer, "commit_many", None))


def _aggregate_staged_batch_preflight_blockers(
    *,
    requests: tuple[MetaGraphInvokeFunctionInput, ...],
    lane_committer: InvocationLaneCommitter | None,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if len(requests) < 2:
        blockers.append("aggregate_commit_requires_multiple_requests")
    if not _invocation_lane_committer_batch_api_available(lane_committer):
        blockers.append("invocation_lane_committer_batch_api_unavailable")

    lane_keys = tuple(_request_lane_key(request) for request in requests)
    if any(lane_key is None for lane_key in lane_keys):
        blockers.append("aggregate_commit_explicit_lane_required")
    else:
        distinct_lane_keys = {
            lane_key for lane_key in lane_keys if lane_key is not None
        }
        if len(distinct_lane_keys) > 1:
            blockers.append("aggregate_commit_same_lane_required")

    return tuple(dict.fromkeys(blockers))


def _request_with_aggregate_lane_head(
    *,
    request: MetaGraphInvokeFunctionInput,
    expected_graph_hash_pre_by_lane: Mapping[tuple[UUID, str], str],
    expected_head_commit_id_by_lane: Mapping[tuple[UUID, str], UUID],
) -> MetaGraphInvokeFunctionInput:
    lane_key = _request_lane_key(request)
    if lane_key is None:
        return request
    graph_hash_pre = expected_graph_hash_pre_by_lane.get(lane_key)
    head_commit_id = expected_head_commit_id_by_lane.get(lane_key)
    if graph_hash_pre is None and head_commit_id is None:
        return request
    return replace(
        request,
        expected_graph_hash_pre=graph_hash_pre or request.expected_graph_hash_pre,
        expected_head_commit_id=head_commit_id or request.expected_head_commit_id,
    )


def _record_aggregate_lane_head(
    *,
    receipt: MetaGraphCommitReceipt,
    expected_graph_hash_pre_by_lane: dict[tuple[UUID, str], str],
    expected_head_commit_id_by_lane: dict[tuple[UUID, str], UUID],
) -> None:
    branch_id = receipt.domain_branch_id
    projection_hash = receipt.domain_projection_hash
    if branch_id is None or projection_hash is None:
        return
    lane_key = (branch_id, projection_hash)
    if receipt.graph_hash_post:
        expected_graph_hash_pre_by_lane[lane_key] = receipt.graph_hash_post
    if receipt.commit_id is not None:
        expected_head_commit_id_by_lane[lane_key] = receipt.commit_id


def _request_lane_key(
    request: MetaGraphInvokeFunctionInput,
) -> tuple[UUID, str] | None:
    if request.domain_branch_id is None or request.domain_projection_hash is None:
        return None
    return (request.domain_branch_id, request.domain_projection_hash)


def _validated_cache_prime_snapshot(
    *,
    staged_action: MetaGraphStagedCommitAction,
    append_request: MetaGraphDomainCommitAppendRequest,
) -> MetaGraphMaterializationCachePrimeSnapshot | None:
    snapshot = append_request.materialization_cache_prime_snapshot
    if snapshot is None:
        return None
    execution_result = getattr(staged_action.staged_result, "execution_result", None)
    append_ready = (
        getattr(execution_result, "append_ready_changes", None)
        if execution_result is not None
        else None
    )
    if (
        append_ready is not None
        and snapshot.execution_plan is not append_ready.execution_plan
    ):
        return None
    if snapshot.post_oig.id != append_request.before_oig.id:
        return None
    if snapshot.graph_hash_post != append_request.graph_hash_post:
        return None
    return snapshot


def _invoke_staged_call_trace_metadata(
    *,
    request: MetaGraphInvokeFunctionInput,
    staged_call: MetaGraphStagedFunctionCall,
) -> dict[str, object]:
    return {
        **_invoke_request_trace_metadata(request),
        "function_call_id": staged_call.function_call.id,
        "operation_label": staged_call.resolved_target.operation_label,
    }


def resolve_meta_graph_invocation_lane_scope(
    *,
    index: MetaGraphCommitIndex,
    request: MetaGraphInvokeFunctionInput,
) -> MetaGraphInvocationLaneScope:
    domain_branch_id = request.domain_branch_id
    if domain_branch_id is None:
        raise ValueError(
            "MetaGraphCommitInvocationBackend requires domain_branch_id before "
            "FunctionCall staging."
        )

    opg, projection_hash = _resolve_projection(index=index, request=request)
    object_projection_graph_identity_id = (
        resolve_meta_graph_object_projection_graph_identity_id(
            index=index,
            opg=opg,
        )
    )
    object_instance_graph_id = (
        request.domain_object_instance_graph_id
        or stable_object_instance_graph_id(
            object_projection_graph_id=opg.id,
            key=str(domain_branch_id),
        )
    )
    object_instance_graph_identity_id = (
        request.domain_object_instance_graph_identity_id
        or stable_object_instance_graph_identity_id(
            object_projection_graph_identity_id=object_projection_graph_identity_id,
            object_instance_graph_id=object_instance_graph_id,
        )
    )
    object_instance_graph_branch_id = stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        branch_id=domain_branch_id,
    )
    lane_id = stable_lane_id(
        branch_id=domain_branch_id,
        lane_hash=projection_hash,
    )
    object_instance_graph_lane_id = stable_object_instance_graph_lane_id(
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        lane_id=lane_id,
    )

    return MetaGraphInvocationLaneScope(
        domain_branch_id=domain_branch_id,
        domain_projection_hash=projection_hash,
        object_projection_graph_id=opg.id,
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        lane_id=lane_id,
        object_instance_graph_lane_id=object_instance_graph_lane_id,
    )


def _resolve_projection(
    *,
    index: MetaGraphCommitIndex,
    request: MetaGraphInvokeFunctionInput,
) -> tuple[ObjectProjectionGraph, str]:
    if request.domain_projection_hash is not None:
        projection_hash = request.domain_projection_hash
        opg = index.opg_by_hash.get(projection_hash)
        if opg is None:
            raise ValueError(
                "ObjectProjectionGraph not found in runtime index for projection_hash: "
                f"{projection_hash}"
            )
        return opg, projection_hash

    if request.object_projection_graph_id is not None:
        opg = index.opg_by_id.get(request.object_projection_graph_id)
        if opg is None:
            raise ValueError(
                "ObjectProjectionGraph not found in runtime index for id: "
                f"{request.object_projection_graph_id}"
            )
        return opg, opg.projection_hash

    raise ValueError(
        "MetaGraphCommitInvocationBackend requires domain_projection_hash or "
        "object_projection_graph_id before FunctionCall staging."
    )


def resolve_meta_graph_object_projection_graph_identity_id(
    *,
    index: MetaGraphCommitIndex,
    opg: ObjectProjectionGraph,
) -> UUID:
    ocg_key = (index.ocg.fqn_prefix or "").strip() or (index.ocg.name or "").strip()
    if not ocg_key:
        raise ValueError(
            "ObjectConfigGraph must provide fqn_prefix or name before "
            "FunctionCall staging."
        )

    ocgi_id = stable_object_config_graph_identity_id(key=ocg_key)
    opgi_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=ocgi_id,
        object_projection_graph_id=opg.id,
    )
    ocgi = index.ocg.object_config_graph_identity
    if ocgi is None:
        return opgi_id

    existing_identities = tuple(ocgi.object_projection_graph_identities)
    source_identity = _resolve_source_object_projection_graph_identity(
        existing_identities=existing_identities,
        object_config_graph_identity_id=ocgi.id,
        object_projection_graph_id=opg.id,
    )
    if source_identity is not None:
        return source_identity.id

    for existing in existing_identities:
        if existing.id == opgi_id:
            return existing.id
    return opgi_id


def _resolve_source_object_projection_graph_identity(
    *,
    existing_identities: tuple[ObjectProjectionGraphIdentity, ...],
    object_config_graph_identity_id: UUID,
    object_projection_graph_id: UUID,
) -> ObjectProjectionGraphIdentity | None:
    for existing in existing_identities:
        if existing.object_projection_graph_id != object_projection_graph_id:
            continue
        existing_ocgi_id = existing.object_config_graph_identity_id
        if existing_ocgi_id == object_config_graph_identity_id:
            continue
        expected_existing_id = stable_object_projection_graph_identity_id(
            object_config_graph_identity_id=existing_ocgi_id,
            object_projection_graph_id=object_projection_graph_id,
        )
        if existing.id == expected_existing_id:
            return existing
    return None


_resolve_object_projection_graph_identity_id = (
    resolve_meta_graph_object_projection_graph_identity_id
)


def _changes_json_array(
    changes: tuple[ObjectInstanceGraphChange, ...],
) -> JsonArray:
    return JsonArray([jsonify_invocation_payload(change) for change in changes])


def _commit_group_evidence(
    appended_commit: MetaGraphAppendedDomainCommit,
) -> MetaInvocationCommitGroupEvidence | None:
    entries: list[MetaInvocationCommitGroupEntry] = []
    ensure_result = appended_commit.identity_lane_head_ensure_result
    if (
        ensure_result is not None
        and ensure_result.status == "created"
        and ensure_result.commit_id is not None
        and ensure_result.object_instance_graph_commit_id is not None
    ):
        entries.append(
            MetaInvocationCommitGroupEntry(
                role="identity_lane_head_commit",
                branch_id=ensure_result.branch_id,
                projection_hash=ensure_result.projection_hash,
                commit_id=ensure_result.commit_id,
                object_instance_graph_commit_id=(
                    ensure_result.object_instance_graph_commit_id
                ),
                object_instance_graph_identity_id=(
                    ensure_result.object_instance_graph_identity_id
                ),
                object_instance_graph_id=ensure_result.object_instance_graph_id,
                operation_label="ObjectInstanceGraphIdentity.create",
            )
        )

    staged_action = appended_commit.append_request.staged_action
    lane_scope = staged_action.staged_result.staged_call.lane_scope
    domain_commit = appended_commit.append_result.commit
    if domain_commit is not None:
        entries.append(
            MetaInvocationCommitGroupEntry(
                role="domain_commit",
                branch_id=lane_scope.domain_branch_id,
                projection_hash=lane_scope.domain_projection_hash,
                commit_id=domain_commit.commit.id,
                object_instance_graph_commit_id=domain_commit.id,
                object_instance_graph_identity_id=(
                    domain_commit.object_instance_graph_identity_id
                ),
                object_instance_graph_id=domain_commit.object_instance_graph_id,
                operation_label=staged_action.action.operation_label,
            )
        )

    for receipt in appended_commit.reaction_receipts:
        entries.extend(receipt.commit_group_entries)

    commit_group_id = _commit_group_id(appended_commit)
    return build_meta_invocation_commit_group_evidence(
        commit_group_id=commit_group_id,
        entries=tuple(entries),
    )


def _commit_group_id(appended_commit: MetaGraphAppendedDomainCommit) -> str:
    domain_commit = appended_commit.append_result.commit
    if domain_commit is not None:
        return f"meta-invocation:{domain_commit.commit.id}"
    staged_call = appended_commit.append_request.staged_action.staged_result.staged_call
    return f"meta-invocation:function-call:{staged_call.function_call.id}"


def _reaction_logs(
    receipts: tuple[RuntimeCommitReactionReceipt, ...],
) -> tuple[str, ...]:
    return tuple(
        f"{receipt.provider_key}.{receipt.reaction_key}:{receipt.status}"
        for receipt in receipts
    )


def _log_slow_invocation_trace(
    *,
    request: MetaGraphInvokeFunctionInput,
    receipt: MetaGraphCommitReceipt,
    duration_ms: float,
    events: tuple[Mapping[str, object], ...],
) -> dict[str, dict[str, float | int]] | None:
    if duration_ms < _SLOW_META_INVOCATION_TRACE_THRESHOLD_MS:
        return None
    trace_summary = summarize_commit_perf_events(events)
    if not trace_summary:
        return None
    operation_label = (
        receipt.commit_action.operation_label
        if receipt.commit_action is not None
        else None
    )
    logger.info(
        "Meta invocation slow path operation_label=%s function_id=%s "
        "function_call_id=%s commit_id=%s object_instance_graph_commit_id=%s "
        "duration_ms=%.3f trace_summary=%s",
        operation_label,
        request.function_id,
        receipt.function_call_id,
        receipt.commit_id,
        receipt.object_instance_graph_commit_id,
        duration_ms,
        trace_summary,
    )
    return trace_summary


__all__ = [
    "build_meta_graph_function_target_index",
    "MetaGraphAppendedDomainCommit",
    "MetaGraphCommitInvocationBackend",
    "MetaGraphCommitInvocationNotReadyError",
    "MetaGraphDomainCommitAppendRequest",
    "MetaGraphHandlerExecutionRequest",
    "MetaGraphHandlerExecutionResult",
    "MetaGraphHandlerExecutor",
    "MetaGraphInvocationLaneScope",
    "MetaGraphResolvedFunctionTarget",
    "MetaGraphStagedCommitAction",
    "MetaGraphStagedFunctionCall",
    "MetaGraphStagedHandlerResult",
    "resolve_meta_graph_invocation_lane_scope",
    "resolve_meta_graph_object_projection_graph_identity_id",
]
