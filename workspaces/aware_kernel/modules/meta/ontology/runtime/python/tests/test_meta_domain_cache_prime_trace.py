from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
    SharedMaterializationCache,
)
from aware_meta.graph.instance.commit.perf_trace import (
    CommitPerfTraceRecorder,
    active_commit_perf_trace,
)
from aware_meta.runtime.graph_commit_invocation_backend import (
    MetaGraphCommitInvocationBackend,
    MetaGraphDomainCommitAppendRequest,
)
import aware_meta.runtime.graph_commit_invocation_backend as invocation_backend
from aware_meta.runtime.handler_executor.append_ready import (
    build_meta_graph_append_ready_changes,
)
from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphMutationBoundaryStatus,
    MetaGraphMutationBoundaryValidation,
    MetaGraphMutationSet,
    MetaGraphMaterializationCachePrimeSnapshot,
)
from aware_meta.runtime.invocation_commits import InvocationDomainCommitAppendResult
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)


def test_domain_cache_prime_emits_reconstruction_child_spans(monkeypatch: Any) -> None:
    projection_hash = "sha256:test:projection"
    commit_id = uuid4()
    oig_id = uuid4()
    before_oig = ObjectInstanceGraph.model_construct(
        id=oig_id,
        hash="sha256:test:pre",
        class_instances=[],
        class_instance_relationships=[],
    )
    staged_action = _staged_action(
        projection_hash=projection_hash,
        oig_id=oig_id,
    )
    append_request = MetaGraphDomainCommitAppendRequest(
        staged_action=staged_action,
        before_oig=before_oig,
        changes=(),
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
    )
    append_result = InvocationDomainCommitAppendResult(
        commit=ObjectInstanceGraphCommit.model_construct(
            id=uuid4(),
            commit=SimpleNamespace(id=commit_id),
            commit_id=commit_id,
        ),
        perf_profile={},
    )
    primed: list[ObjectInstanceGraph] = []

    class _FakeCachedLaneMaterializer:
        def prime(self, **kwargs: Any) -> None:
            primed.append(kwargs["graph"])

    monkeypatch.setattr(
        invocation_backend,
        "CachedLaneMaterializer",
        _FakeCachedLaneMaterializer,
    )
    recorder = CommitPerfTraceRecorder(default_category="meta.runtime.invoke_function")

    with active_commit_perf_trace(recorder):
        MetaGraphCommitInvocationBackend()._prime_domain_materialization_cache(
            staged_action=staged_action,
            append_request=append_request,
            append_result=append_result,
        )

    phases = {event.phase for event in recorder.snapshot()}
    assert {
        "runtime.invoke_function.prime_domain_materialization_cache.resolve_opg",
        "runtime.invoke_function.prime_domain_materialization_cache.copy_before_oig",
        "runtime.invoke_function.prime_domain_materialization_cache.apply_changes",
        "runtime.invoke_function.prime_domain_materialization_cache.assign_hash",
        "runtime.invoke_function.prime_domain_materialization_cache.prime_cache",
    }.issubset(phases)
    assert len(primed) == 1
    assert primed[0] is not before_oig
    assert primed[0].hash == "sha256:test:post"


def test_domain_cache_prime_uses_valid_post_oig_snapshot(monkeypatch: Any) -> None:
    projection_hash = "sha256:test:projection"
    commit_id = uuid4()
    oig_id = uuid4()
    before_oig = ObjectInstanceGraph.model_construct(
        id=oig_id,
        hash="sha256:test:pre",
        class_instances=[],
        class_instance_relationships=[],
    )
    post_oig = before_oig.model_copy(deep=True)
    staged_action = _staged_action(
        projection_hash=projection_hash,
        oig_id=oig_id,
    )
    append_request = MetaGraphDomainCommitAppendRequest(
        staged_action=staged_action,
        before_oig=before_oig,
        changes=(),
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
        materialization_cache_prime_snapshot=(
            MetaGraphMaterializationCachePrimeSnapshot(
                execution_plan=cast(Any, SimpleNamespace()),
                post_oig=post_oig,
                graph_hash_post="sha256:test:post",
            )
        ),
    )
    append_result = InvocationDomainCommitAppendResult(
        commit=ObjectInstanceGraphCommit.model_construct(
            id=uuid4(),
            commit=SimpleNamespace(id=commit_id),
            commit_id=commit_id,
        ),
        perf_profile={},
    )
    primed: list[ObjectInstanceGraph] = []

    class _FakeCachedLaneMaterializer:
        def prime(self, **kwargs: Any) -> None:
            primed.append(kwargs["graph"])

    monkeypatch.setattr(
        invocation_backend,
        "CachedLaneMaterializer",
        _FakeCachedLaneMaterializer,
    )
    recorder = CommitPerfTraceRecorder(default_category="meta.runtime.invoke_function")

    with active_commit_perf_trace(recorder):
        MetaGraphCommitInvocationBackend()._prime_domain_materialization_cache(
            staged_action=staged_action,
            append_request=append_request,
            append_result=append_result,
        )

    phases = {event.phase for event in recorder.snapshot()}
    assert (
        "runtime.invoke_function.prime_domain_materialization_cache."
        "use_post_oig_snapshot"
    ) in phases
    assert (
        "runtime.invoke_function.prime_domain_materialization_cache.copy_before_oig"
        not in phases
    )
    assert (
        "runtime.invoke_function.prime_domain_materialization_cache.apply_changes"
        not in phases
    )
    assert primed == [post_oig]
    assert post_oig.hash == "sha256:test:post"


def test_cached_lane_materializer_prime_emits_index_and_store_spans() -> None:
    recorder = CommitPerfTraceRecorder(default_category="meta.oig.materialization_cache")
    materializer = CachedLaneMaterializer(
        materializer=cast(Any, _FakeOIGMaterializer()),
        cache=SharedMaterializationCache(max_entries=64),
    )

    with active_commit_perf_trace(recorder):
        materializer.prime(
            branch_id=uuid4(),
            opg=ObjectProjectionGraph.model_construct(
                id=uuid4(),
                projection_hash="sha256:test:projection",
            ),
            commit_id=uuid4(),
            oig_id=uuid4(),
            graph=ObjectInstanceGraph.model_construct(
                id=uuid4(),
                class_instances=[],
                class_instance_relationships=[],
            ),
        )

    phases = {event.phase for event in recorder.snapshot()}
    assert {
        "oig_materialization_cache.prime.build_indexes",
        "oig_materialization_cache.prime.store",
    }.issubset(phases)


def test_append_ready_preserves_valid_cache_prime_snapshot() -> None:
    execution_plan = cast(Any, SimpleNamespace())
    before_oig = ObjectInstanceGraph.model_construct(
        id=uuid4(),
        class_instances=[],
        class_instance_relationships=[],
    )
    post_oig = before_oig.model_copy(deep=True)
    snapshot = MetaGraphMaterializationCachePrimeSnapshot(
        execution_plan=execution_plan,
        post_oig=post_oig,
        graph_hash_post="sha256:test:post",
    )
    mutation_set = MetaGraphMutationSet(
        execution_plan=execution_plan,
        before_oig=before_oig,
        changes=(),
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
        materialization_cache_prime_snapshot=snapshot,
    )

    append_ready = build_meta_graph_append_ready_changes(
        request=cast(Any, SimpleNamespace(execution_plan=execution_plan)),
        mutation_set=mutation_set,
        boundary_validation=MetaGraphMutationBoundaryValidation(
            execution_plan=execution_plan,
            mutation_set=mutation_set,
            status=MetaGraphMutationBoundaryStatus.accepted,
        ),
    )

    assert append_ready.materialization_cache_prime_snapshot is snapshot


def _staged_action(
    *,
    projection_hash: str,
    oig_id: object,
) -> Any:
    lane_scope = SimpleNamespace(
        domain_branch_id=uuid4(),
        domain_projection_hash=projection_hash,
        object_instance_graph_id=oig_id,
    )
    staged_call = SimpleNamespace(
        lane_scope=lane_scope,
        function_call=SimpleNamespace(id=uuid4()),
        resolved_target=SimpleNamespace(operation_label="ClassConfig.remove_attribute"),
    )
    request = SimpleNamespace(
        call_target=SimpleNamespace(value="instance"),
        domain_projection_hash=projection_hash,
        function_id=uuid4(),
        index=SimpleNamespace(
            opg_by_hash={
                projection_hash: ObjectProjectionGraph.model_construct(
                    id=uuid4(),
                    projection_hash=projection_hash,
                ),
            },
            attribute_configs_by_id={},
            class_configs_by_id={},
        ),
    )
    return SimpleNamespace(
        staged_result=SimpleNamespace(
            request=request,
            staged_call=staged_call,
        ),
        action=SimpleNamespace(operation_label="ClassConfig.remove_attribute"),
    )


class _FakeOIGMaterializer:
    def indexes_from_graph(self, graph: ObjectInstanceGraph) -> dict[str, object]:
        return {"class_instance_count": len(graph.class_instances)}
