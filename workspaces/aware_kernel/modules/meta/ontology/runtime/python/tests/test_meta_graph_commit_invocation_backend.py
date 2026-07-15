from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import cast
from uuid import UUID, uuid4

import pytest

from aware_code.types import JsonObject
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
from aware_meta.runtime.graph_commit_invocation_backend import (
    MetaGraphCommitInvocationBackend,
)
from aware_meta.runtime.handler_executor import (
    MetaGraphHandlerExecutionRequest,
    MetaGraphHandlerExecutionResult,
    MetaGraphRuntimeIndex,
)
from aware_meta.runtime.invocation_engine import MetaGraphInvokeFunctionInput
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


class _AppendCase(SimpleNamespace):
    backend: MetaGraphCommitInvocationBackend
    request: MetaGraphInvokeFunctionInput


def _append_case() -> _AppendCase:
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
    )
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, index),
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
    backend = MetaGraphCommitInvocationBackend(
        handler_executor=_RecordingMetaGraphHandlerExecutor(
            result=MetaGraphHandlerExecutionResult(
                success=True,
                payload=JsonObject({"ok": True}),
                execution_time_ms=3,
                graph_hash_pre="sha256:test:pre",
                graph_hash_post="sha256:test:post",
                root_object_id=root_object_id,
                before_oig=before_oig,
            )
        ),
        lane_committer=_RecordingInvocationLaneCommitter(commit=domain_commit),
        required_reaction_runner=_RecordingRequiredReactionRunner().run,
    )
    return _AppendCase(backend=backend, request=request)


def _meta_commit_index(
    *,
    function_config: object,
    projection_hash: str,
    opg_id: UUID,
) -> SimpleNamespace:
    opg = SimpleNamespace(
        id=opg_id,
        name="Domain",
        projection_hash=projection_hash,
    )
    return SimpleNamespace(
        ocg=SimpleNamespace(
            name="Aware Tests",
            fqn_prefix="aware.tests",
            object_config_graph_identity=None,
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
    def __init__(self, *, result: MetaGraphHandlerExecutionResult) -> None:
        self.result = result
        self.calls: list[MetaGraphHandlerExecutionRequest] = []

    async def execute_function(
        self,
        request: MetaGraphHandlerExecutionRequest,
    ) -> MetaGraphHandlerExecutionResult:
        self.calls.append(request)
        return self.result


class _RecordingInvocationLaneCommitter:
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
