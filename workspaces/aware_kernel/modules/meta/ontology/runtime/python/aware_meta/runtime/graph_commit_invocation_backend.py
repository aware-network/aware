from __future__ import annotations

from dataclasses import dataclass
from typing import cast
from uuid import UUID, uuid4

from aware_code.types import JsonArray
from aware_history_ontology.stable_ids import stable_lane_id
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
    build_meta_graph_execution_plan,
    build_meta_graph_function_target_index,
)
from aware_meta.runtime.invocation_commit_actions import MetaInvocationCommitAction
from aware_meta.runtime.invocation_commits import (
    InvocationDomainCommitAppendResult,
    InvocationLaneCommitter,
    append_invocation_domain_commit,
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
    InvocationRequiredReactionRunner,
    run_invocation_required_commit_reactions,
)
from aware_meta.runtime.commit.required_reactions import RuntimeCommitReactionReceipt
from aware_meta.runtime.commit.identity_lane import (
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
    root_object_id: UUID | None = None
    root_class_instance_identity_id: UUID | None = None


@dataclass(frozen=True)
class MetaGraphAppendedDomainCommit:
    append_request: MetaGraphDomainCommitAppendRequest
    append_result: InvocationDomainCommitAppendResult
    reaction_receipts: tuple[RuntimeCommitReactionReceipt, ...]


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
        staged_call = self.stage_function_call(request)
        staged_result = await self.execute_staged_function_call(
            request=request,
            staged_call=staged_call,
        )
        staged_action = self.stage_commit_action(staged_result)
        appended_commit = await self.append_domain_commit(staged_action)
        return self.build_commit_receipt(appended_commit)

    async def execute_staged_function_call(
        self,
        *,
        request: MetaGraphInvokeFunctionInput,
        staged_call: MetaGraphStagedFunctionCall,
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

        execution_plan = self.build_execution_plan(
            request=request,
            staged_call=staged_call,
        )
        execution_result = await self._handler_executor.execute_function(
            MetaGraphHandlerExecutionRequest(
                request=request,
                staged_call=staged_call,
                execution_plan=execution_plan,
                invoke_function=self.invoke_function,
            )
        )
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
        append_request = self.build_domain_commit_append_request(staged_action)
        staged_result = staged_action.staged_result
        lane_scope = staged_result.staged_call.lane_scope
        execution_result = staged_result.execution_result
        ensure_perf_ms: dict[str, int] = {}
        await self._ensure_object_instance_graph_identity_lane_head_for_domain_commit(
            staged_action=staged_action,
            perf_ms=ensure_perf_ms,
        )
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
            graph_hash_pre=append_request.graph_hash_pre,
            graph_hash_post=append_request.graph_hash_post,
            author_id=staged_result.request.actor_id,
            action=staged_action.action,
            committer=self._lane_committer,
        )
        if ensure_perf_ms:
            append_result = InvocationDomainCommitAppendResult(
                commit=append_result.commit,
                perf_profile={
                    **ensure_perf_ms,
                    **append_result.perf_profile,
                },
            )
        link_function_call_response_commit(
            response=staged_result.function_call_response,
            oig_commit=append_result.commit,
        )
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
        )

    async def _ensure_object_instance_graph_identity_lane_head_for_domain_commit(
        self,
        *,
        staged_action: MetaGraphStagedCommitAction,
        perf_ms: dict[str, int],
    ) -> None:
        staged_result = staged_action.staged_result
        lane_scope = staged_result.staged_call.lane_scope
        if not hasattr(staged_result.request.index.ocg, "object_projection_graphs"):
            return
        oigi_ctx = resolve_object_instance_graph_identity_lane_context(
            index=staged_result.request.index,
        )
        if oigi_ctx is None:
            return
        if lane_scope.domain_projection_hash == oigi_ctx.projection_hash:
            return
        await ensure_object_instance_graph_identity_lane_head(
            index=staged_result.request.index,
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
                actor_id=staged_result.request.actor_id,
                domain_branch_id=lane_scope.domain_branch_id,
                domain_projection_hash=lane_scope.domain_projection_hash,
                domain_commit=domain_commit,
                action=staged_action.action,
                perf_ms=append_result.perf_profile,
            )

        return await run_invocation_required_commit_reactions(
            index=staged_result.request.index,
            actor_id=staged_result.request.actor_id,
            domain_branch_id=lane_scope.domain_branch_id,
            domain_projection_hash=lane_scope.domain_projection_hash,
            domain_commit=domain_commit,
            action=staged_action.action,
            perf_ms=append_result.perf_profile,
            runner=reaction_runner,
        )

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
                graph_hash_pre=append_ready.graph_hash_pre,
                graph_hash_post=append_ready.graph_hash_post,
                root_object_id=append_ready.root_object_id,
                root_class_instance_identity_id=(
                    append_ready.root_class_instance_identity_id
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
            graph_hash_pre=graph_hash_pre,
            graph_hash_post=graph_hash_post,
            root_object_id=execution_result.root_object_id,
            root_class_instance_identity_id=(
                execution_result.root_class_instance_identity_id
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


def _reaction_logs(
    receipts: tuple[RuntimeCommitReactionReceipt, ...],
) -> tuple[str, ...]:
    return tuple(
        f"{receipt.provider_key}.{receipt.reaction_key}:{receipt.status}"
        for receipt in receipts
    )


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
