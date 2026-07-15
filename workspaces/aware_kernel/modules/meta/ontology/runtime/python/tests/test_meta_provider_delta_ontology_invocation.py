from __future__ import annotations

from types import SimpleNamespace
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_code.types import JsonArray
from aware_meta.graph.instance.commit.perf_trace import (
    CommitPerfTraceRecorder,
    active_commit_perf_trace,
    commit_perf_span,
    summarize_commit_perf_events,
)
from aware_meta.materialization.deltas.ontology_execution.invocation import (
    execute_ontology_invocation_intents,
)
from aware_meta.runtime.commit_groups import (
    MetaInvocationCommitGroupEntry,
    build_meta_invocation_commit_group_evidence,
)
from aware_meta.runtime.invocation_engine import (
    MetaGraphCommitReceipt,
    MetaGraphInvokeFunctionInput,
)


class _RecordingRuntime:
    def __init__(self) -> None:
        self.requests: list[MetaGraphInvokeFunctionInput] = []

    async def invoke_function(
        self,
        request: MetaGraphInvokeFunctionInput,
    ) -> MetaGraphCommitReceipt:
        self.requests.append(request)
        request_count = len(self.requests)
        graph_hash_pre = request.expected_graph_hash_pre or "sha256:test:pre"
        graph_hash_post = f"sha256:test:post:{request_count}"
        commit_id = _test_uuid(f"commit:{request_count}")
        object_instance_graph_commit_id = _test_uuid(f"oig-commit:{request_count}")
        with commit_perf_span(
            phase="runtime.invoke_function.handler_execute_function",
            category="meta.runtime.invoke_function",
            metadata={"request_count": request_count},
        ):
            pass
        with commit_perf_span(
            phase="runtime.invoke_function.append_domain_commit",
            category="meta.runtime.invoke_function",
            metadata={"request_count": request_count},
        ):
            pass
        with commit_perf_span(
            phase="runtime.invoke_function.append_invocation_domain_commit",
            category="meta.runtime.invoke_function",
            metadata={"request_count": request_count},
        ):
            pass
        with commit_perf_span(
            phase="runtime.invoke_function.required_commit_reactions",
            category="meta.runtime.invoke_function",
            metadata={"request_count": request_count},
        ):
            pass
        return MetaGraphCommitReceipt(
            status="succeeded",
            actor_id=request.actor_id,
            domain_branch_id=request.domain_branch_id,
            domain_projection_hash=request.domain_projection_hash,
            payload={"request_count": request_count},
            error=None,
            logs=(),
            execution_time_ms=1,
            root_object_id=request.target_object_id,
            graph_hash_pre=graph_hash_pre,
            graph_hash_post=graph_hash_post,
            changes=JsonArray([]),
            function_call_id=_test_uuid(f"function-call:{request_count}"),
            function_call_response_id=_test_uuid(
                f"function-call-response:{request_count}"
            ),
            commit_id=commit_id,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
            commit_group=build_meta_invocation_commit_group_evidence(
                commit_group_id=f"test-commit-group:{request_count}",
                entries=(
                    MetaInvocationCommitGroupEntry(
                        role="domain_commit",
                        branch_id=request.domain_branch_id or _test_uuid("branch"),
                        projection_hash=(
                            request.domain_projection_hash or "sha256:test:projection"
                        ),
                        commit_id=commit_id,
                        object_instance_graph_commit_id=(
                            object_instance_graph_commit_id
                        ),
                    ),
                ),
            ),
        )


class _AggregateRecordingRuntime(_RecordingRuntime):
    def __init__(self) -> None:
        super().__init__()
        self.aggregate_requests: list[tuple[MetaGraphInvokeFunctionInput, ...]] = []

    async def invoke_function_aggregate(
        self,
        requests: tuple[MetaGraphInvokeFunctionInput, ...],
    ) -> tuple[MetaGraphCommitReceipt, ...]:
        self.aggregate_requests.append(requests)
        receipts: list[MetaGraphCommitReceipt] = []
        graph_hash_pre = "sha256:test:aggregate:pre"
        for request_count, request in enumerate(requests, start=1):
            graph_hash_post = f"sha256:test:aggregate:post:{request_count}"
            commit_id = _test_uuid(f"aggregate-commit:{request_count}")
            object_instance_graph_commit_id = _test_uuid(
                f"aggregate-oig-commit:{request_count}"
            )
            with commit_perf_span(
                phase="runtime.invoke_function.aggregate_commit",
                category="meta.runtime.invoke_function",
                metadata={"request_count": request_count},
            ):
                pass
            receipts.append(
                MetaGraphCommitReceipt(
                    status="succeeded",
                    actor_id=request.actor_id,
                    domain_branch_id=request.domain_branch_id,
                    domain_projection_hash=request.domain_projection_hash,
                    payload={"request_count": request_count},
                    error=None,
                    logs=(),
                    execution_time_ms=1,
                    root_object_id=request.target_object_id,
                    graph_hash_pre=graph_hash_pre,
                    graph_hash_post=graph_hash_post,
                    changes=JsonArray([]),
                    function_call_id=_test_uuid(
                        f"aggregate-function-call:{request_count}"
                    ),
                    function_call_response_id=_test_uuid(
                        f"aggregate-function-call-response:{request_count}"
                    ),
                    commit_id=commit_id,
                    object_instance_graph_commit_id=object_instance_graph_commit_id,
                    commit_group=build_meta_invocation_commit_group_evidence(
                        commit_group_id=f"test-aggregate-commit-group:{request_count}",
                        entries=(
                            MetaInvocationCommitGroupEntry(
                                role="domain_commit",
                                branch_id=(
                                    request.domain_branch_id or _test_uuid("branch")
                                ),
                                projection_hash=(
                                    request.domain_projection_hash
                                    or "sha256:test:projection"
                                ),
                                commit_id=commit_id,
                                object_instance_graph_commit_id=(
                                    object_instance_graph_commit_id
                                ),
                            ),
                        ),
                    ),
                )
            )
            graph_hash_pre = graph_hash_post
        return tuple(receipts)


class _AggregateIndependentAppendRuntime(_AggregateRecordingRuntime):
    async def invoke_function_aggregate(
        self,
        requests: tuple[MetaGraphInvokeFunctionInput, ...],
    ) -> dict[str, object]:
        receipts = await super().invoke_function_aggregate(requests)
        return {
            "commit_receipts": receipts,
            "aggregate_commit_execution": {
                "status": "not_implemented",
                "backend_status": "invoked",
                "backend_invoked": True,
                "executor": "test.invoke_function_aggregate",
                "request_count": len(requests),
                "receipt_count": len(receipts),
                "durable_transaction_status": "not_implemented",
                "durability_policy": "independent_append",
                "invocation_lane_committer_batch_api_available": True,
                "aggregate_batch_append_used": False,
                "aggregate_uncommitted_session_state_status": "not_implemented",
                "blockers": (
                    "aggregate_commit_not_implemented",
                    "aggregate_commit_durable_transaction_not_implemented",
                    "aggregate_commit_uncommitted_session_state_not_implemented",
                ),
            },
        }


@pytest.mark.asyncio
async def test_ontology_invocation_emits_per_intent_trace_spans() -> None:
    runtime = _RecordingRuntime()
    recorder = CommitPerfTraceRecorder(default_category="meta.provider_delta")
    projection_hash = "sha256:test:projection"
    target_object_id = _test_uuid("target-object")

    with active_commit_perf_trace(recorder):
        receipt = await execute_ontology_invocation_intents(
            runtime=runtime,
            graph_runtime_context=SimpleNamespace(index=_runtime_index()),
            actor_id=_test_uuid("actor"),
            branch_id=_test_uuid("branch"),
            projection_hash=projection_hash,
            invocation_intents=(
                {
                    "intent_key": "rename",
                    "operation_key": "meta.test.rename",
                    "semantic_key": "ocg:test/node:Room/function:rename",
                    "invocation_order": 1,
                    "invocation_mode": "instance",
                    "owner_class_name": "Room",
                    "function_name": "rename",
                    "target_object_id": str(target_object_id),
                    "kwargs": {"display_name": "Kitchen"},
                    "commit_required": True,
                },
            ),
        )

    trace_summary = summarize_commit_perf_events(recorder.snapshot_json())
    event_metadata = {
        str(event.get("phase")): event.get("metadata")
        for event in recorder.snapshot_json()
    }

    assert receipt["status"] == "ontology_function_call_execution_applied"
    assert receipt["applied_invocation_count"] == 1
    assert receipt["function_call_count"] == 1
    assert receipt["single_commit_candidate"] is False
    assert receipt["batch_blocker_reasons"] == ("function_call_count_lt_2",)
    assert receipt["aggregate_invocation_receipt_status"] == (
        "aggregate_invocation_receipt_blocked"
    )
    aggregate_receipt = receipt["aggregate_invocation_receipt"]
    assert aggregate_receipt["available"] is False
    assert aggregate_receipt["blockers"] == ("function_call_count_lt_2",)
    assert aggregate_receipt["aggregate_commit_required_mode"] == "not_applicable"
    assert aggregate_receipt["aggregate_commit_backend_available"] is False
    assert aggregate_receipt["aggregate_commit_blockers"] == (
        "function_call_count_lt_2",
    )
    assert receipt["function_call_commit_core_ms"] >= 0
    assert receipt["handler_execute_ms"] >= 0
    assert receipt["append_domain_commit_ms"] >= 0
    assert receipt["append_domain_excluding_required_reactions_ms"] >= 0
    assert receipt["append_invocation_domain_commit_ms"] >= 0
    assert receipt["required_commit_reactions_ms"] >= 0
    assert len(runtime.requests) == 1
    assert runtime.requests[0].target_object_id == target_object_id
    assert runtime.requests[0].domain_projection_hash == projection_hash
    invocation_receipts = receipt["invocation_receipts"]
    assert isinstance(invocation_receipts, tuple)
    assert len(invocation_receipts) == 1
    invocation_receipt = invocation_receipts[0]
    assert invocation_receipt["invoke_function_duration_ms"] >= 0
    assert "runtime.invoke_function.handler_execute_function" in (
        invocation_receipt["invoke_function_core_phase_ms"]
    )
    assert set(trace_summary) >= {
        "ontology_invocation.input_for_intent",
        "ontology_invocation.invoke_function",
        "ontology_invocation.receipt_payload",
        "ontology_invocation.head_tracking",
    }
    assert trace_summary["ontology_invocation.invoke_function"]["count"] == 1
    assert event_metadata["ontology_invocation.invoke_function"] == {
        "function_name": "rename",
        "intent_key": "rename",
        "invocation_index": 0,
        "invocation_mode": "instance",
        "operation_key": "meta.test.rename",
        "owner_class_name": "Room",
        "semantic_key": "ocg:test/node:Room/function:rename",
    }


@pytest.mark.asyncio
async def test_ontology_invocation_marks_same_projection_multi_intent_candidate() -> (
    None
):
    runtime = _RecordingRuntime()
    projection_hash = "sha256:test:projection"
    first_target_object_id = _test_uuid("first-target-object")
    second_target_object_id = _test_uuid("second-target-object")
    recorder = CommitPerfTraceRecorder(default_category="meta.provider_delta")

    with active_commit_perf_trace(recorder):
        receipt = await execute_ontology_invocation_intents(
            runtime=runtime,
            graph_runtime_context=SimpleNamespace(index=_runtime_index()),
            actor_id=_test_uuid("actor"),
            branch_id=_test_uuid("branch"),
            projection_hash=projection_hash,
            invocation_intents=(
                {
                    "intent_key": "rename-second",
                    "operation_key": "meta.test.rename",
                    "semantic_key": "ocg:test/node:Room/function:rename-second",
                    "invocation_order": 2,
                    "invocation_mode": "instance",
                    "owner_class_name": "Room",
                    "function_name": "rename",
                    "target_object_id": str(second_target_object_id),
                    "kwargs": {"display_name": "Pantry"},
                    "commit_required": True,
                },
                {
                    "intent_key": "rename-first",
                    "operation_key": "meta.test.rename",
                    "semantic_key": "ocg:test/node:Room/function:rename-first",
                    "invocation_order": 1,
                    "invocation_mode": "instance",
                    "owner_class_name": "Room",
                    "function_name": "rename",
                    "target_object_id": str(first_target_object_id),
                    "kwargs": {"display_name": "Kitchen"},
                    "commit_required": True,
                },
            ),
        )

    assert receipt["status"] == "ontology_function_call_execution_applied"
    assert receipt["function_call_count"] == 2
    assert receipt["applied_invocation_count"] == 2
    assert receipt["single_commit_candidate"] is True
    assert receipt["batch_blocker_reasons"] == ()
    assert receipt["aggregate_invocation_receipt_status"] == (
        "aggregate_invocation_receipt_ready"
    )
    assert receipt["aggregate_invocation_receipt_available"] is True
    aggregate_receipt = receipt["aggregate_invocation_receipt"]
    assert aggregate_receipt["function_call_count"] == 2
    assert aggregate_receipt["commit_count"] == 2
    assert aggregate_receipt["aggregate_receipt_implemented"] is True
    assert aggregate_receipt["aggregate_commit_implemented"] is False
    assert aggregate_receipt["aggregate_commit_required_mode"] == "single_domain_commit"
    assert aggregate_receipt["aggregate_commit_backend_available"] is False
    assert aggregate_receipt["aggregate_commit_blockers"] == (
        "aggregate_commit_not_implemented",
        "aggregate_commit_single_domain_backend_unavailable",
    )
    assert aggregate_receipt["current_durability_policy"] == ("independent_append",)
    aggregate_commit_group = aggregate_receipt["commit_group_summary"]
    assert aggregate_commit_group["group_count"] == 2
    assert aggregate_commit_group["role_counts"] == {"domain_commit": 2}
    assert aggregate_commit_group["domain_lane_count"] == 1
    assert receipt["batch_candidate_projection_hash"] == projection_hash
    assert receipt["function_call_commit_core_ms"] >= 0
    assert receipt["estimated_batch_savings_ms"] >= 0
    assert len(runtime.requests) == 2
    assert runtime.requests[0].target_object_id == first_target_object_id
    assert runtime.requests[1].target_object_id == second_target_object_id
    assert runtime.requests[1].expected_graph_hash_pre == "sha256:test:post:1"
    invocation_receipts = receipt["invocation_receipts"]
    assert isinstance(invocation_receipts, tuple)
    assert invocation_receipts[0]["graph_hash_post"] == "sha256:test:post:1"
    assert invocation_receipts[1]["graph_hash_pre"] == "sha256:test:post:1"
    assert all(
        "runtime.invoke_function.append_domain_commit"
        in invocation_receipt["invoke_function_core_phase_ms"]
        for invocation_receipt in invocation_receipts
    )


@pytest.mark.asyncio
async def test_ontology_invocation_uses_available_aggregate_executor() -> None:
    runtime = _AggregateRecordingRuntime()
    projection_hash = "sha256:test:projection"
    first_target_object_id = _test_uuid("aggregate-first-target-object")
    second_target_object_id = _test_uuid("aggregate-second-target-object")

    receipt = await execute_ontology_invocation_intents(
        runtime=runtime,
        graph_runtime_context=SimpleNamespace(index=_runtime_index()),
        actor_id=_test_uuid("actor"),
        branch_id=_test_uuid("branch"),
        projection_hash=projection_hash,
        invocation_intents=(
            {
                "intent_key": "rename-first",
                "operation_key": "meta.test.rename",
                "semantic_key": "ocg:test/node:Room/function:rename-first",
                "invocation_order": 1,
                "invocation_mode": "instance",
                "owner_class_name": "Room",
                "function_name": "rename",
                "target_object_id": str(first_target_object_id),
                "kwargs": {"display_name": "Kitchen"},
                "commit_required": True,
            },
            {
                "intent_key": "rename-second",
                "operation_key": "meta.test.rename",
                "semantic_key": "ocg:test/node:Room/function:rename-second",
                "invocation_order": 2,
                "invocation_mode": "instance",
                "owner_class_name": "Room",
                "function_name": "rename",
                "target_object_id": str(second_target_object_id),
                "kwargs": {"display_name": "Pantry"},
                "commit_required": True,
            },
        ),
    )

    assert receipt["status"] == "ontology_function_call_execution_applied"
    assert (
        receipt["reason"]
        == "meta_ocg_ontology_function_call_aggregate_execution_applied"
    )
    assert runtime.requests == []
    assert len(runtime.aggregate_requests) == 1
    assert len(runtime.aggregate_requests[0]) == 2
    aggregate_execution = receipt["aggregate_commit_execution"]
    assert aggregate_execution["status"] == "succeeded"
    assert aggregate_execution["executor"] == "invoke_function_aggregate"
    aggregate_receipt = receipt["aggregate_invocation_receipt"]
    assert aggregate_receipt["aggregate_commit_implemented"] is True
    assert aggregate_receipt["aggregate_commit_status"] == "succeeded"
    assert aggregate_receipt["aggregate_commit_backend_available"] is True
    assert aggregate_receipt["aggregate_commit_blockers"] == ()
    assert aggregate_receipt["aggregate_commit_required_mode"] == "single_domain_commit"
    assert receipt["function_call_count"] == 2
    assert receipt["function_call_commit_core_ms"] >= 0


@pytest.mark.asyncio
async def test_ontology_invocation_reports_independent_append_aggregate_backend() -> (
    None
):
    runtime = _AggregateIndependentAppendRuntime()
    projection_hash = "sha256:test:projection"

    receipt = await execute_ontology_invocation_intents(
        runtime=runtime,
        graph_runtime_context=SimpleNamespace(index=_runtime_index()),
        actor_id=_test_uuid("actor"),
        branch_id=_test_uuid("branch"),
        projection_hash=projection_hash,
        invocation_intents=(
            {
                "intent_key": "rename-first",
                "operation_key": "meta.test.rename",
                "semantic_key": "ocg:test/node:Room/function:rename-first",
                "invocation_order": 1,
                "invocation_mode": "instance",
                "owner_class_name": "Room",
                "function_name": "rename",
                "target_object_id": str(_test_uuid("independent-first-target")),
                "kwargs": {"display_name": "Kitchen"},
                "commit_required": True,
            },
            {
                "intent_key": "rename-second",
                "operation_key": "meta.test.rename",
                "semantic_key": "ocg:test/node:Room/function:rename-second",
                "invocation_order": 2,
                "invocation_mode": "instance",
                "owner_class_name": "Room",
                "function_name": "rename",
                "target_object_id": str(_test_uuid("independent-second-target")),
                "kwargs": {"display_name": "Pantry"},
                "commit_required": True,
            },
        ),
    )

    assert receipt["status"] == "ontology_function_call_execution_applied"
    aggregate_execution = receipt["aggregate_commit_execution"]
    assert aggregate_execution["status"] == "not_implemented"
    assert aggregate_execution["backend_status"] == "invoked"
    aggregate_receipt = receipt["aggregate_invocation_receipt"]
    assert aggregate_receipt["aggregate_commit_implemented"] is False
    assert aggregate_receipt["aggregate_commit_status"] == "not_implemented"
    assert aggregate_receipt["aggregate_commit_backend_available"] is True
    assert aggregate_receipt["aggregate_commit_backend_invoked"] is True
    assert aggregate_receipt["aggregate_commit_execution_status"] == "not_implemented"
    assert aggregate_receipt["aggregate_commit_durable_transaction_status"] == (
        "not_implemented"
    )
    assert aggregate_receipt["aggregate_commit_blockers"] == (
        "aggregate_commit_not_implemented",
        "aggregate_commit_durable_transaction_not_implemented",
        "aggregate_commit_uncommitted_session_state_not_implemented",
    )
    assert len(runtime.aggregate_requests) == 1
    assert runtime.requests == []


def _runtime_index() -> object:
    function_id = _test_uuid("function")
    function_link_id = _test_uuid("function-link")
    class_config = SimpleNamespace(
        id=_test_uuid("class"),
        name="Room",
        class_fqn="aware.test.Room",
        class_config_function_configs=(
            SimpleNamespace(
                id=function_link_id,
                function_config_id=function_id,
                function_config=SimpleNamespace(
                    id=function_id,
                    name="rename",
                ),
            ),
        ),
    )
    return SimpleNamespace(
        class_configs_by_id={class_config.id: class_config},
        opg_by_id={},
        opg_by_hash={},
    )


def _test_uuid(key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"aware:test:ontology-invocation-trace:{key}")
