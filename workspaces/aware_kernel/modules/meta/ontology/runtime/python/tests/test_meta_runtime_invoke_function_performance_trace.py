from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_meta.graph.instance.commit.contract import CommitActionDescriptor
from aware_meta.graph.instance.commit.perf_trace import (
    CommitPerfTraceRecorder,
    active_commit_perf_trace,
)
from aware_meta.runtime.commit.required_reactions import (
    RuntimeCommitReactionContext,
    RuntimeCommitReactionReceipt,
)
from aware_meta.runtime.invocation_commit_actions import MetaInvocationCommitAction
from aware_meta.runtime.invocation_commits import append_invocation_domain_commit
from aware_meta.runtime.invocation_reactions import (
    run_invocation_required_commit_reactions,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)


@dataclass(frozen=True)
class _RecordedCommitCall:
    branch_id: UUID
    projection_hash: str
    commit_action: CommitActionDescriptor | None


class _TraceLaneCommitter:
    def __init__(self) -> None:
        self.calls: list[_RecordedCommitCall] = []
        self.appended_commit = ObjectInstanceGraphCommit.model_construct(id=uuid4())

    async def commit(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        object_projection_graph_identity_id: UUID | None = None,
        object_instance_graph_identity_id: UUID,
        object_instance_graph_id: UUID,
        before_oig: ObjectInstanceGraph,
        root_object_id: UUID | None,
        changes: list[ObjectInstanceGraphChange],
        graph_hash_pre: str,
        graph_hash_post: str,
        author_id: UUID,
        commit_action: CommitActionDescriptor | None,
    ) -> ObjectInstanceGraphCommit:
        self.calls.append(
            _RecordedCommitCall(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_action=commit_action,
            )
        )
        return self.appended_commit

    def last_commit_perf_profile_snapshot(self) -> dict[str, int]:
        return {"append_ms": 7}


class _TraceReactionRunner:
    def __init__(self) -> None:
        self.contexts: list[RuntimeCommitReactionContext] = []

    async def __call__(
        self,
        context: RuntimeCommitReactionContext,
    ) -> tuple[RuntimeCommitReactionReceipt, ...]:
        self.contexts.append(context)
        return ()


@pytest.mark.asyncio
async def test_invocation_domain_commit_append_emits_child_trace_spans() -> None:
    committer = _TraceLaneCommitter()
    action = MetaInvocationCommitAction(
        operation_label="Meta.test",
        call_target="instance",
        function_id=uuid4(),
        object_id=uuid4(),
        class_instance_identity_id=uuid4(),
    )
    recorder = CommitPerfTraceRecorder(default_category="meta.runtime.invoke_function")

    with active_commit_perf_trace(recorder):
        result = await append_invocation_domain_commit(
            branch_id=uuid4(),
            projection_hash="sha256:test",
            object_projection_graph_identity_id=uuid4(),
            object_instance_graph_identity_id=uuid4(),
            object_instance_graph_id=uuid4(),
            before_oig=ObjectInstanceGraph.model_construct(id=uuid4()),
            root_object_id=uuid4(),
            changes=[],
            graph_hash_pre="sha256:pre",
            graph_hash_post="sha256:post",
            author_id=uuid4(),
            action=action,
            committer=committer,
        )

    assert result.commit is committer.appended_commit
    assert result.perf_profile == {"append_ms": 7}
    assert len(committer.calls) == 1
    assert committer.calls[0].commit_action is not None
    phases = {event.phase for event in recorder.snapshot()}
    assert {
        "runtime.invoke_function.domain_commit.resolve_committer",
        "runtime.invoke_function.domain_commit.invoke_committer",
        "runtime.invoke_function.domain_commit.perf_profile_snapshot",
    }.issubset(phases)


@pytest.mark.asyncio
async def test_invocation_required_reactions_emit_guard_and_runner_spans() -> None:
    runner = _TraceReactionRunner()
    action = MetaInvocationCommitAction(
        operation_label="Meta.test",
        call_target="instance",
        function_id=uuid4(),
        object_id=uuid4(),
        class_instance_identity_id=uuid4(),
    )
    domain_commit = ObjectInstanceGraphCommit.model_construct(id=uuid4())
    recorder = CommitPerfTraceRecorder(default_category="meta.runtime.invoke_function")

    with active_commit_perf_trace(recorder):
        receipts = await run_invocation_required_commit_reactions(
            index=cast(Any, object()),
            actor_id=uuid4(),
            domain_branch_id=uuid4(),
            domain_projection_hash="sha256:test",
            domain_commit=domain_commit,
            action=action,
            perf_ms={},
            runner=runner,
        )

    assert receipts == ()
    assert len(runner.contexts) == 1
    assert runner.contexts[0].domain_commit is domain_commit
    phases = {event.phase for event in recorder.snapshot()}
    assert {
        "runtime.invoke_function.required_commit_reactions.resolve_source_identity",
        "runtime.invoke_function.required_commit_reactions.set_mutation_owner",
        "runtime.invoke_function.required_commit_reactions.runner",
        "runtime.invoke_function.required_commit_reactions.reset_mutation_owner",
    }.issubset(phases)
