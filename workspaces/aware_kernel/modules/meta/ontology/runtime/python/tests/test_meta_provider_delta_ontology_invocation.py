from __future__ import annotations

from types import SimpleNamespace
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_code.types import JsonArray
from aware_meta.graph.instance.commit.perf_trace import (
    CommitPerfTraceRecorder,
    active_commit_perf_trace,
    summarize_commit_perf_events,
)
from aware_meta.materialization.deltas.ontology_execution.invocation import (
    execute_ontology_invocation_intents,
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
        return MetaGraphCommitReceipt(
            status="succeeded",
            actor_id=request.actor_id,
            domain_branch_id=request.domain_branch_id,
            domain_projection_hash=request.domain_projection_hash,
            payload={"request_count": len(self.requests)},
            error=None,
            logs=(),
            execution_time_ms=1,
            root_object_id=request.target_object_id,
            graph_hash_pre="sha256:test:pre",
            graph_hash_post="sha256:test:post",
            changes=JsonArray([]),
            function_call_id=_test_uuid("function-call"),
            function_call_response_id=_test_uuid("function-call-response"),
            commit_id=_test_uuid("commit"),
            object_instance_graph_commit_id=_test_uuid("oig-commit"),
        )


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
    assert len(runtime.requests) == 1
    assert runtime.requests[0].target_object_id == target_object_id
    assert runtime.requests[0].domain_projection_hash == projection_hash
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
