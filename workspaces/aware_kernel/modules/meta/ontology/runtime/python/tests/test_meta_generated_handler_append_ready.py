from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest

from aware_meta.graph.instance.commit.perf_trace import (
    CommitPerfTraceRecorder,
    active_commit_perf_trace,
    summarize_commit_perf_events,
)
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_meta.runtime.handler_executor.contracts import MetaGraphPreState
from aware_meta.runtime.handler_executor.session import (
    MetaGraphExecutionSessionDeltaBuilder,
    MetaGraphExecutionSessionDeltaError,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph


def test_constructor_post_oig_delta_hashes_handler_post_oig_directly() -> None:
    root_object_id = uuid4()
    handler_request = _handler_request(is_constructor=True)
    pre_state = _pre_state(handler_request=handler_request)
    post_oig = _post_oig_with_root(
        before_oig=pre_state.before_oig,
        class_config_id=_class_config_id(handler_request=handler_request),
        root_object_id=root_object_id,
    )
    expected_post_hash = compute_hash(post_oig, index=build_index(post_oig))
    recorder = CommitPerfTraceRecorder(
        default_category="meta.runtime.handler_execution",
    )

    with active_commit_perf_trace(recorder):
        session_delta = MetaGraphExecutionSessionDeltaBuilder().build_delta_from_post_oig(
            request=handler_request,
            pre_state=pre_state,
            post_oig=post_oig,
            expected_graph_hash_post=expected_post_hash,
            root_object_id=root_object_id,
        )

    assert session_delta.before_oig is pre_state.before_oig
    assert session_delta.graph_hash_pre == pre_state.graph_hash_pre
    assert session_delta.graph_hash_post == expected_post_hash
    assert session_delta.root_object_id == root_object_id
    assert len(session_delta.changes) == 1
    assert session_delta.materialization_cache_prime_snapshot is not None
    assert session_delta.materialization_cache_prime_snapshot.post_oig is post_oig
    assert (
        session_delta.materialization_cache_prime_snapshot.graph_hash_post
        == expected_post_hash
    )
    trace_summary = summarize_commit_perf_events(recorder.snapshot_json())
    assert "handler_execution.session_delta.diff_post_oig" in trace_summary
    assert "handler_execution.session_delta.constructor_post_oig_hash" in trace_summary
    assert (
        "handler_execution.session_delta.apply_scoped_changes_for_hash"
        not in trace_summary
    )


def test_non_constructor_post_oig_delta_hashes_directly_when_scope_keeps_all() -> None:
    root_object_id = uuid4()
    handler_request = _handler_request(is_constructor=False)
    pre_state = _pre_state(handler_request=handler_request)
    post_oig = _post_oig_with_root(
        before_oig=pre_state.before_oig,
        class_config_id=_class_config_id(handler_request=handler_request),
        root_object_id=root_object_id,
    )
    expected_post_hash = compute_hash(post_oig, index=build_index(post_oig))
    recorder = CommitPerfTraceRecorder(
        default_category="meta.runtime.handler_execution",
    )

    with active_commit_perf_trace(recorder):
        session_delta = MetaGraphExecutionSessionDeltaBuilder().build_delta_from_post_oig(
            request=handler_request,
            pre_state=pre_state,
            post_oig=post_oig,
            expected_graph_hash_post=expected_post_hash,
            root_object_id=root_object_id,
        )

    assert session_delta.graph_hash_post == expected_post_hash
    assert session_delta.materialization_cache_prime_snapshot is not None
    assert session_delta.materialization_cache_prime_snapshot.post_oig is post_oig
    assert (
        session_delta.materialization_cache_prime_snapshot.graph_hash_post
        == expected_post_hash
    )
    trace_summary = summarize_commit_perf_events(recorder.snapshot_json())
    assert "handler_execution.session_delta.diff_post_oig" in trace_summary
    assert (
        "handler_execution.session_delta.scoped_post_oig_hash_direct"
        in trace_summary
    )
    assert (
        "handler_execution.session_delta.apply_scoped_changes_for_hash"
        not in trace_summary
    )
    assert (
        "handler_execution.session_delta.constructor_post_oig_hash"
        not in trace_summary
    )


def test_non_constructor_post_oig_delta_keeps_filtered_scoped_apply_path() -> None:
    handler_request = _handler_request(is_constructor=False)
    class_config_id = _class_config_id(handler_request=handler_request)
    target_object_id = uuid4()
    unrelated_object_id = uuid4()
    target_instance = _class_instance(
        graph_id=handler_request.staged_call.lane_scope.object_instance_graph_id,
        class_config_id=class_config_id,
        object_id=target_object_id,
    )
    unrelated_instance = _class_instance(
        graph_id=handler_request.staged_call.lane_scope.object_instance_graph_id,
        class_config_id=class_config_id,
        object_id=unrelated_object_id,
    )
    before_oig = ObjectInstanceGraph.model_construct(
        id=handler_request.staged_call.lane_scope.object_instance_graph_id,
        hash="sha256:test:pre",
        class_instances=[target_instance],
        class_instance_relationships=[],
    )
    pre_state = _pre_state(
        handler_request=handler_request,
        before_oig=before_oig,
        target_object_id=target_object_id,
    )
    post_oig = before_oig.model_copy(deep=True)
    post_oig.class_instances = [target_instance, unrelated_instance]
    expected_scoped_hash = compute_hash(before_oig, index=build_index(before_oig))
    recorder = CommitPerfTraceRecorder(
        default_category="meta.runtime.handler_execution",
    )

    with active_commit_perf_trace(recorder):
        session_delta = MetaGraphExecutionSessionDeltaBuilder().build_delta_from_post_oig(
            request=handler_request,
            pre_state=pre_state,
            post_oig=post_oig,
            expected_graph_hash_post=expected_scoped_hash,
        )

    assert session_delta.graph_hash_post == expected_scoped_hash
    assert session_delta.changes == ()
    assert session_delta.materialization_cache_prime_snapshot is not None
    assert session_delta.materialization_cache_prime_snapshot.post_oig is not post_oig
    assert (
        session_delta.materialization_cache_prime_snapshot.post_oig.id
        == pre_state.before_oig.id
    )
    assert (
        session_delta.materialization_cache_prime_snapshot.graph_hash_post
        == expected_scoped_hash
    )
    trace_summary = summarize_commit_perf_events(recorder.snapshot_json())
    assert (
        "handler_execution.session_delta.apply_scoped_changes_for_hash"
        in trace_summary
    )
    assert "handler_execution.session_delta.hash_scoped_post_oig" in trace_summary
    assert (
        "handler_execution.session_delta.scoped_post_oig_hash_direct"
        not in trace_summary
    )


def test_constructor_post_oig_delta_still_rejects_hash_mismatch() -> None:
    root_object_id = uuid4()
    handler_request = _handler_request(is_constructor=True)
    pre_state = _pre_state(handler_request=handler_request)
    post_oig = _post_oig_with_root(
        before_oig=pre_state.before_oig,
        class_config_id=_class_config_id(handler_request=handler_request),
        root_object_id=root_object_id,
    )

    with pytest.raises(MetaGraphExecutionSessionDeltaError, match="post hash"):
        MetaGraphExecutionSessionDeltaBuilder().build_delta_from_post_oig(
            request=handler_request,
            pre_state=pre_state,
            post_oig=post_oig,
            expected_graph_hash_post="sha256:test:wrong",
            root_object_id=root_object_id,
        )


def _handler_request(*, is_constructor: bool) -> Any:
    function_config = SimpleNamespace(id=uuid4(), name="create", owner_key="aware.test")
    implementation = SimpleNamespace(
        function_config=function_config,
        is_constructor=is_constructor,
    )
    class_config_id = uuid4()
    execution_plan = SimpleNamespace(
        implementation=implementation,
        index=SimpleNamespace(
            attribute_configs_by_id={},
            class_configs_by_id={
                class_config_id: ClassConfig.model_construct(
                    id=class_config_id,
                    class_fqn="aware.test.Root",
                    name="Root",
                    class_config_attribute_configs=[],
                ),
            },
        ),
    )
    lane_scope = SimpleNamespace(
        object_instance_graph_identity_id=uuid4(),
        object_instance_graph_id=uuid4(),
    )
    return SimpleNamespace(
        execution_plan=execution_plan,
        staged_call=SimpleNamespace(
            lane_scope=lane_scope,
            function_call=SimpleNamespace(id=uuid4()),
            resolved_target=SimpleNamespace(operation_label="Test.create"),
        ),
        request=SimpleNamespace(
            call_target=SimpleNamespace(value="opg_constructor"),
            domain_projection_hash="sha256:test:projection",
        ),
    )


def _pre_state(
    *,
    handler_request: Any,
    before_oig: ObjectInstanceGraph | None = None,
    target_object_id: UUID | None = None,
) -> MetaGraphPreState:
    if before_oig is None:
        before_oig = ObjectInstanceGraph.model_construct(
            id=handler_request.staged_call.lane_scope.object_instance_graph_id,
            hash="sha256:test:pre",
            class_instances=[],
            class_instance_relationships=[],
        )
    return MetaGraphPreState(
        execution_plan=handler_request.execution_plan,
        before_oig=before_oig,
        graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
    )


def _post_oig_with_root(
    *,
    before_oig: ObjectInstanceGraph,
    class_config_id: UUID,
    root_object_id: UUID,
) -> ObjectInstanceGraph:
    root_class_instance = _class_instance(
        graph_id=before_oig.id,
        class_config_id=class_config_id,
        object_id=root_object_id,
    )
    post_oig = before_oig.model_copy(deep=True)
    post_oig.root_class_instance_id = root_class_instance.id
    post_oig.root_class_instance = root_class_instance
    post_oig.class_instances = [root_class_instance]
    return post_oig


def _class_config_id(*, handler_request: Any) -> UUID:
    return next(iter(handler_request.execution_plan.index.class_configs_by_id))


def _class_instance(
    *,
    graph_id: UUID,
    class_config_id: UUID,
    object_id: UUID,
) -> ClassInstance:
    return ClassInstance.model_construct(
        id=object_id,
        object_instance_graph_id=graph_id,
        class_config_id=class_config_id,
        source_object_id=object_id,
        class_instance_attributes=[],
    )
