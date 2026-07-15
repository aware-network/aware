from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from types import SimpleNamespace
from typing import cast
from uuid import UUID, uuid4

import pytest

from aware_code.types import JsonObject, JsonValue
from aware_history_ontology.commit.commit import Commit
from aware_meta.graph.instance.commit.perf_trace import (
    CommitPerfTraceRecorder,
    active_commit_perf_trace,
    summarize_commit_perf_events,
)
from aware_meta.runtime import graph_commit_invocation_backend as backend_module
from aware_meta.runtime.commit.required_reactions import (
    RuntimeCommitReactionContext,
    RuntimeCommitReactionReceipt,
)
from aware_meta.runtime.commit.identity_lane import (
    ObjectInstanceGraphIdentityLaneHeadEnsureResult,
)
from aware_meta.runtime.commit_groups import (
    META_INVOCATION_COMMIT_GROUP_DURABILITY_POLICY,
    MetaInvocationCommitGroupEntry,
)
from aware_meta.runtime.graph_commit_invocation_backend import (
    MetaGraphCommitInvocationBackend,
)
from aware_meta.runtime.handler_executor import (
    MetaGraphHandlerExecutionRequest,
    MetaGraphHandlerExecutionResult,
    MetaGraphRuntimeIndex,
)
from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphMaterializationCachePrimeSnapshot,
)
from aware_meta.runtime.invocation_engine import (
    MetaGraphCommitReceipt,
    MetaGraphInvokeFunctionInput,
)
from aware_meta.materialization.deltas.ontology_execution.invocation import (
    _commit_receipt_payload,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id


@pytest.mark.asyncio
async def test_meta_commit_backend_auto_logs_slow_invocation_trace(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        backend_module,
        "_SLOW_META_INVOCATION_TRACE_THRESHOLD_MS",
        0,
    )
    caplog.set_level(logging.INFO)
    case = _append_case()

    receipt = await case.backend.invoke_function(case.request)

    assert receipt.status == "succeeded"
    assert receipt.perf_trace_duration_ms is not None
    assert receipt.perf_trace_duration_ms >= 0
    assert receipt.perf_trace_summary is not None
    assert set(receipt.perf_trace_summary) >= {
        "runtime.invoke_function.handler_execute_function",
        "runtime.invoke_function.append_domain_commit",
        "runtime.invoke_function.build_commit_receipt",
    }
    messages = [record.getMessage() for record in caplog.records]
    slow_messages = [
        message
        for message in messages
        if message.startswith("Meta invocation slow path")
    ]
    assert len(slow_messages) == 1
    slow_message = slow_messages[0]
    assert "operation_label=mutate" in slow_message
    assert "runtime.invoke_function.handler_execute_function" in slow_message
    assert "runtime.invoke_function.append_domain_commit" in slow_message
    assert "runtime.invoke_function.build_commit_receipt" in slow_message


@pytest.mark.asyncio
async def test_meta_commit_backend_preserves_external_perf_trace_recorder(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        backend_module,
        "_SLOW_META_INVOCATION_TRACE_THRESHOLD_MS",
        0,
    )
    caplog.set_level(logging.INFO)
    case = _append_case()
    recorder = CommitPerfTraceRecorder(default_category="meta.runtime.invoke_function")

    with active_commit_perf_trace(recorder):
        receipt = await case.backend.invoke_function(case.request)

    assert receipt.status == "succeeded"
    assert receipt.perf_trace_duration_ms is None
    assert receipt.perf_trace_summary is None
    assert not [
        record
        for record in caplog.records
        if record.getMessage().startswith("Meta invocation slow path")
    ]
    trace_summary = summarize_commit_perf_events(recorder.snapshot_json())
    assert set(trace_summary) >= {
        "runtime.invoke_function.stage_function_call",
        "runtime.invoke_function.execute_staged_function_call",
        "runtime.invoke_function.handler_execute_function",
        "runtime.invoke_function.append_domain_commit",
        "runtime.invoke_function.build_commit_receipt",
    }


@pytest.mark.asyncio
async def test_meta_commit_backend_records_invocation_commit_group(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    identity_commit_id = uuid4()
    identity_oig_commit_id = uuid4()
    identity_oig_id = uuid4()
    history_commit_id = uuid4()
    history_oig_commit_id = uuid4()
    history_oig_id = uuid4()
    oigi_projection_hash = "sha256:test:oigi"
    case = _append_case(oigi_projection_hash=oigi_projection_hash)

    async def _ensure_oigi_head(
        **kwargs: object,
    ) -> ObjectInstanceGraphIdentityLaneHeadEnsureResult:
        object_instance_graph_id = kwargs["object_instance_graph_id"]
        assert isinstance(object_instance_graph_id, UUID)
        return ObjectInstanceGraphIdentityLaneHeadEnsureResult(
            status="created",
            branch_id=object_instance_graph_id,
            projection_hash=oigi_projection_hash,
            object_instance_graph_identity_id=identity_oig_id,
            object_instance_graph_id=identity_oig_id,
            commit_id=identity_commit_id,
            object_instance_graph_commit_id=identity_oig_commit_id,
        )

    async def _reaction_runner(
        context: RuntimeCommitReactionContext,
    ) -> tuple[RuntimeCommitReactionReceipt, ...]:
        assert context.index_view is not None
        assert context.index_view.index is context.index
        domain_commit = context.domain_commit
        assert domain_commit is not None
        return (
            RuntimeCommitReactionReceipt(
                provider_key="aware_meta",
                reaction_key="object_instance_graph_identity.history_upsert",
                status="succeeded",
                commit_group_entries=(
                    MetaInvocationCommitGroupEntry(
                        role="oigi_history_commit",
                        branch_id=domain_commit.object_instance_graph_id,
                        projection_hash=oigi_projection_hash,
                        commit_id=history_commit_id,
                        object_instance_graph_commit_id=history_oig_commit_id,
                        object_instance_graph_identity_id=history_oig_id,
                        object_instance_graph_id=history_oig_id,
                        operation_label=(
                            "ObjectInstanceGraphIdentity."
                            "upsert_history_from_lane_head"
                        ),
                        provider_key="aware_meta",
                        reaction_key=("object_instance_graph_identity.history_upsert"),
                    ),
                ),
            ),
        )

    monkeypatch.setattr(
        backend_module,
        "ensure_object_instance_graph_identity_lane_head",
        _ensure_oigi_head,
    )
    backend = MetaGraphCommitInvocationBackend(
        handler_executor=case.backend._handler_executor,  # noqa: SLF001
        lane_committer=case.backend._lane_committer,  # noqa: SLF001
        required_reaction_runner=_reaction_runner,
    )

    receipt = await backend.invoke_function(case.request)

    assert receipt.commit_group is not None
    assert (
        receipt.commit_group.commit_group_id == f"meta-invocation:{receipt.commit_id}"
    )
    assert receipt.commit_group.durability_policy == (
        META_INVOCATION_COMMIT_GROUP_DURABILITY_POLICY
    )
    assert receipt.commit_group.role_counts == {
        "identity_lane_head_commit": 1,
        "domain_commit": 1,
        "oigi_history_commit": 1,
    }
    payload = receipt.commit_group.evidence_payload()
    assert payload["entry_count"] == 3
    assert payload["durability_policy"] == "independent_append"
    entries = cast(list[dict[str, object]], payload["entries"])
    assert [entry["role"] for entry in entries] == [
        "identity_lane_head_commit",
        "domain_commit",
        "oigi_history_commit",
    ]
    provider_payload = _commit_receipt_payload(
        intent={"intent_key": "test.intent"},
        commit_receipt=receipt,
    )
    assert provider_payload["commit_group"] == payload
    assert receipt.logs == (
        "aware_meta.object_instance_graph_identity.history_upsert:succeeded",
    )


@pytest.mark.asyncio
async def test_meta_commit_backend_aggregate_uses_staged_same_lane_batch_append() -> (
    None
):
    case = _append_case(
        handler_result_factory=_aggregate_snapshot_result_factory(uuid4()),
    )
    second_request = replace(case.request, call_key=uuid4())

    result = await case.backend.invoke_function_aggregate(
        (
            case.request,
            second_request,
        )
    )

    receipts = cast(tuple[object, ...], result["commit_receipts"])
    assert len(receipts) == 2
    assert all(
        isinstance(receipt, MetaGraphCommitReceipt) and receipt.status == "succeeded"
        for receipt in receipts
    )
    aggregate_execution = cast(
        dict[str, object],
        result["aggregate_commit_execution"],
    )
    assert aggregate_execution["status"] == "partial"
    assert aggregate_execution["backend_status"] == "invoked"
    assert aggregate_execution["backend_invoked"] is True
    assert aggregate_execution["executor"] == (
        "MetaGraphCommitInvocationBackend.invoke_function_aggregate"
    )
    assert aggregate_execution["request_count"] == 2
    assert aggregate_execution["receipt_count"] == 2
    assert aggregate_execution["durable_transaction_status"] == "not_implemented"
    assert aggregate_execution["durability_policy"] == (
        "domain_batch_append_required_reactions_independent"
    )
    assert aggregate_execution["observed_role_counts"] == {"domain_commit": 2}
    assert aggregate_execution["observed_durability_policies"] == (
        "independent_append",
    )
    assert aggregate_execution["invocation_lane_committer_batch_api_available"] is True
    assert aggregate_execution["aggregate_batch_append_used"] is True
    assert (
        aggregate_execution["aggregate_uncommitted_session_state_status"]
        == "implemented"
    )
    assert aggregate_execution["aggregate_domain_batch_append_status"] == "succeeded"
    assert (
        aggregate_execution["aggregate_required_reaction_batch_status"]
        == "fallback_independent"
    )
    handler_executor = cast(
        _RecordingMetaGraphHandlerExecutor,
        case.backend._handler_executor,  # noqa: SLF001
    )
    assert handler_executor.calls[1].request.expected_graph_hash_pre == (
        cast(MetaGraphCommitReceipt, receipts[0]).graph_hash_post
    )
    assert handler_executor.calls[1].request.expected_head_commit_id is None
    assert handler_executor.calls[1].pre_state_override is not None
    lane_committer = cast(
        _RecordingInvocationLaneCommitter,
        case.backend._lane_committer,  # noqa: SLF001
    )
    assert lane_committer.commit_calls == []
    assert len(lane_committer.commit_many_calls) == 1
    batch_requests = cast(
        tuple[object, ...],
        lane_committer.commit_many_calls[0]["requests"],
    )
    assert len(batch_requests) == 2
    assert getattr(batch_requests[1], "graph_hash_pre") == (
        cast(MetaGraphCommitReceipt, receipts[0]).graph_hash_post
    )
    assert aggregate_execution["blockers"] == (
        "aggregate_commit_durable_transaction_not_implemented",
        "aggregate_commit_required_reaction_batch_not_implemented",
    )


@pytest.mark.asyncio
async def test_meta_commit_backend_aggregate_marks_required_reaction_batch_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[object, ...]] = []

    async def _batch_reactions(
        *,
        items: tuple[object, ...],
    ) -> tuple[tuple[RuntimeCommitReactionReceipt, ...], ...]:
        calls.append(items)
        return tuple(
            (
                RuntimeCommitReactionReceipt(
                    provider_key="aware_meta",
                    reaction_key="object_instance_graph_identity.history_upsert",
                    status="succeeded",
                ),
            )
            for _ in items
        )

    monkeypatch.setattr(
        backend_module,
        "run_invocation_required_commit_reactions_batch",
        _batch_reactions,
    )
    case = _append_case(
        handler_result_factory=_aggregate_snapshot_result_factory(uuid4()),
        required_reaction_runner=False,
    )
    second_request = replace(case.request, call_key=uuid4())

    result = await case.backend.invoke_function_aggregate(
        (
            case.request,
            second_request,
        )
    )

    assert len(calls) == 1
    assert len(calls[0]) == 2
    aggregate_execution = cast(
        dict[str, object],
        result["aggregate_commit_execution"],
    )
    assert (
        aggregate_execution["aggregate_required_reaction_batch_status"] == "succeeded"
    )
    assert aggregate_execution["durability_policy"] == (
        "domain_batch_append_required_reactions_batch"
    )
    assert aggregate_execution["blockers"] == (
        "aggregate_commit_durable_transaction_not_implemented",
    )


@pytest.mark.asyncio
async def test_meta_commit_backend_aggregate_reports_missing_committer_batch_api() -> (
    None
):
    case = _append_case(committer_batch_api=False)

    result = await case.backend.invoke_function_aggregate(
        (
            case.request,
            case.request,
        )
    )

    aggregate_execution = cast(
        dict[str, object],
        result["aggregate_commit_execution"],
    )
    assert aggregate_execution["invocation_lane_committer_batch_api_available"] is False
    assert aggregate_execution["aggregate_batch_append_used"] is False
    assert aggregate_execution["blockers"] == (
        "aggregate_commit_not_implemented",
        "aggregate_commit_durable_transaction_not_implemented",
        "invocation_lane_committer_batch_api_unavailable",
    )


@dataclass(frozen=True)
class _AppendCase:
    backend: MetaGraphCommitInvocationBackend
    request: MetaGraphInvokeFunctionInput


def _append_case(
    *,
    oigi_projection_hash: str | None = None,
    committer_batch_api: bool = True,
    required_reaction_runner: bool = True,
    handler_result_factory: (
        Callable[
            [MetaGraphHandlerExecutionRequest, int], MetaGraphHandlerExecutionResult
        ]
        | None
    ) = None,
) -> _AppendCase:
    function_id = uuid4()
    branch_id = uuid4()
    projection_hash = "sha256:test:domain"
    root_object_id = uuid4()
    index = _meta_commit_index(
        function_config=FunctionConfig(
            id=function_id,
            owner_key="aware.tests",
            name="mutate",
        ),
        projection_hash=projection_hash,
        opg_id=uuid4(),
        oigi_projection_hash=oigi_projection_hash,
    )
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, cast(object, index)),
        actor_id=uuid4(),
        function_id=function_id,
        domain_branch_id=branch_id,
        domain_projection_hash=projection_hash,
        call_key=uuid4(),
        expected_graph_hash_pre="sha256:test:pre",
    )
    staged_call = MetaGraphCommitInvocationBackend().stage_function_call(request)
    lane_scope = staged_call.lane_scope
    before_oig = ObjectInstanceGraph.model_construct(
        id=lane_scope.object_instance_graph_id
    )
    domain_commit_id = uuid4()
    domain_commit = ObjectInstanceGraphCommit.model_construct(
        id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=(
                lane_scope.object_instance_graph_identity_id
            ),
            commit_id=domain_commit_id,
        ),
        commit=Commit.model_construct(id=domain_commit_id),
        object_instance_graph_identity_id=(
            lane_scope.object_instance_graph_identity_id
        ),
        object_instance_graph_id=lane_scope.object_instance_graph_id,
        root_source_object_id=root_object_id,
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
        object_instance_graph_changes=[],
    )
    committer_class = (
        _RecordingInvocationLaneCommitter
        if committer_batch_api
        else _RecordingInvocationLaneCommitterWithoutBatch
    )
    backend = MetaGraphCommitInvocationBackend(
        handler_executor=_RecordingMetaGraphHandlerExecutor(
            result=(
                None
                if handler_result_factory is not None
                else MetaGraphHandlerExecutionResult(
                    success=True,
                    payload=cast(JsonValue, JsonObject({"ok": True})),
                    execution_time_ms=3,
                    graph_hash_pre="sha256:test:pre",
                    graph_hash_post="sha256:test:post",
                    root_object_id=root_object_id,
                    before_oig=before_oig,
                )
            ),
            result_factory=handler_result_factory,
        ),
        lane_committer=committer_class(commit=domain_commit),
        required_reaction_runner=(
            _RecordingRequiredReactionRunner().run if required_reaction_runner else None
        ),
    )
    return _AppendCase(backend=backend, request=request)


def _aggregate_snapshot_result_factory(
    root_object_id: UUID,
) -> Callable[[MetaGraphHandlerExecutionRequest, int], MetaGraphHandlerExecutionResult]:
    def _result(
        request: MetaGraphHandlerExecutionRequest,
        index: int,
    ) -> MetaGraphHandlerExecutionResult:
        before_oig = (
            request.pre_state_override.before_oig
            if request.pre_state_override is not None
            else ObjectInstanceGraph.model_construct(
                id=request.staged_call.lane_scope.object_instance_graph_id,
                hash=request.execution_plan.expected_graph_hash_pre,
            )
        )
        graph_hash_pre = (
            request.execution_plan.expected_graph_hash_pre
            or before_oig.hash
            or "sha256:test:pre"
        )
        graph_hash_post = f"sha256:test:post:{index}"
        post_oig = ObjectInstanceGraph.model_construct(
            id=before_oig.id,
            hash=graph_hash_post,
        )
        return MetaGraphHandlerExecutionResult(
            success=True,
            payload=cast(JsonValue, JsonObject({"ok": True, "index": index})),
            execution_time_ms=3,
            graph_hash_pre=graph_hash_pre,
            graph_hash_post=graph_hash_post,
            root_object_id=root_object_id,
            before_oig=before_oig,
            materialization_cache_prime_snapshot=(
                MetaGraphMaterializationCachePrimeSnapshot(
                    execution_plan=request.execution_plan,
                    post_oig=post_oig,
                    graph_hash_post=graph_hash_post,
                )
            ),
        )

    return _result


def _meta_commit_index(
    *,
    function_config: object,
    projection_hash: str,
    opg_id: UUID,
    oigi_projection_hash: str | None = None,
) -> SimpleNamespace:
    opg = SimpleNamespace(
        id=opg_id,
        name="Domain",
        projection_hash=projection_hash,
    )
    object_projection_graphs = []
    if oigi_projection_hash is not None:
        object_projection_graphs.append(
            SimpleNamespace(
                id=uuid4(),
                name="ObjectInstanceGraphIdentity",
                projection_hash=oigi_projection_hash,
            )
        )
    return SimpleNamespace(
        ocg=SimpleNamespace(
            name="Aware Tests",
            fqn_prefix="aware.tests",
            object_config_graph_identity=None,
            object_projection_graphs=object_projection_graphs,
            object_config_graph_nodes=[
                SimpleNamespace(
                    type=ObjectConfigGraphNodeType.function,
                    function_config=function_config,
                )
            ],
        ),
        class_configs_by_id={},
        attribute_configs_by_id={},
        relationships_by_id={},
        portal_index=SimpleNamespace(),
        opg_by_hash={projection_hash: opg},
        opg_by_id={opg_id: opg},
    )


class _RecordingMetaGraphHandlerExecutor:
    def __init__(
        self,
        *,
        result: MetaGraphHandlerExecutionResult | None = None,
        result_factory: (
            Callable[
                [MetaGraphHandlerExecutionRequest, int], MetaGraphHandlerExecutionResult
            ]
            | None
        ) = None,
    ) -> None:
        self.result = result
        self.result_factory = result_factory
        self.calls: list[MetaGraphHandlerExecutionRequest] = []

    async def execute_function(
        self,
        request: MetaGraphHandlerExecutionRequest,
    ) -> MetaGraphHandlerExecutionResult:
        index = len(self.calls)
        self.calls.append(request)
        if self.result_factory is not None:
            return self.result_factory(request, index)
        if self.result is None:
            raise AssertionError("Recording handler requires result or result_factory")
        return self.result


class _RecordingInvocationLaneCommitter:
    def __init__(self, *, commit: ObjectInstanceGraphCommit | None) -> None:
        self.commit_result = commit
        self.commit_calls: list[dict[str, object]] = []
        self.commit_many_calls: list[dict[str, object]] = []

    async def commit(self, **kwargs: object) -> ObjectInstanceGraphCommit | None:
        self.commit_calls.append(dict(kwargs))
        return self.commit_result

    async def commit_many(
        self, **kwargs: object
    ) -> tuple[ObjectInstanceGraphCommit, ...]:
        self.commit_many_calls.append(dict(kwargs))
        requests = cast(Sequence[object], kwargs.get("requests", ()))
        if self.commit_result is None:
            return ()
        commits: list[ObjectInstanceGraphCommit] = []
        for request in requests:
            commit_id = uuid4()
            object_instance_graph_identity_id = cast(
                UUID,
                getattr(request, "object_instance_graph_identity_id"),
            )
            commits.append(
                ObjectInstanceGraphCommit.model_construct(
                    id=stable_object_instance_graph_commit_id(
                        object_instance_graph_identity_id=(
                            object_instance_graph_identity_id
                        ),
                        commit_id=commit_id,
                    ),
                    commit=Commit.model_construct(id=commit_id),
                    object_instance_graph_identity_id=(
                        object_instance_graph_identity_id
                    ),
                    object_instance_graph_id=getattr(
                        request,
                        "object_instance_graph_id",
                    ),
                    root_source_object_id=getattr(request, "root_object_id"),
                    graph_hash_pre=getattr(request, "graph_hash_pre"),
                    graph_hash_post=getattr(request, "graph_hash_post"),
                    object_instance_graph_changes=list(getattr(request, "changes", ())),
                )
            )
        return tuple(commits)

    def last_commit_perf_profile_snapshot(self) -> dict[str, int]:
        return {"append_ms": 4}


class _RecordingInvocationLaneCommitterWithoutBatch:
    def __init__(self, *, commit: ObjectInstanceGraphCommit | None) -> None:
        self.commit_result = commit

    async def commit(
        self,
        **_: object,
    ) -> ObjectInstanceGraphCommit | None:
        return self.commit_result

    def last_commit_perf_profile_snapshot(self) -> dict[str, int]:
        return {"append_ms": 4}


class _RecordingRequiredReactionRunner:
    async def run(
        self,
        context: RuntimeCommitReactionContext,
    ) -> tuple[RuntimeCommitReactionReceipt, ...]:
        return (
            RuntimeCommitReactionReceipt(
                provider_key="aware_meta",
                reaction_key=(
                    f"test_required_reaction:{context.domain_projection_hash}"
                ),
                status="succeeded",
            ),
        )
