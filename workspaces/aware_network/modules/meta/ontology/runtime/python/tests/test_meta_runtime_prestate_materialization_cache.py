from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_code.types import JsonArray, JsonObject
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.instance.commit import materialization_cache as cache_module
from aware_meta.graph.instance.commit.perf_trace import (
    CommitPerfTraceRecorder,
    active_commit_perf_trace,
    summarize_commit_perf_events,
)
from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphExecutionPlan,
    MetaGraphFunctionImplementationDescriptor,
    MetaGraphImplementationKind,
    MetaGraphResolvedFunctionTarget,
    MetaGraphRuntimeIndex,
    MetaGraphStagedFunctionCall,
)
from aware_meta.runtime.handler_executor.pre_state import (
    MetaGraphOigMaterializerPreStateProvider,
)
from aware_meta.runtime.invocation_engine import (
    MetaGraphCallTarget,
    MetaGraphInvokeFunctionInput,
)
from aware_meta.runtime.graph_commit_invocation_backend import (
    resolve_meta_graph_invocation_lane_scope,
)
from aware_meta_ontology.function.function_call import FunctionCall
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)


@pytest.mark.asyncio
async def test_cached_lane_materializer_trace_reports_primed_hit() -> None:
    branch_id = uuid4()
    commit_id = uuid4()
    oig_id = uuid4()
    projection_hash = f"sha256:test:runtime-prestate-cache:{uuid4()}"
    graph = _make_graph(oig_id=oig_id, graph_hash="sha256:test:cached")
    fake_materializer = _FakeMaterializer(snapshot=(graph, {"state": "loaded"}))
    materializer = cache_module.CachedLaneMaterializer(
        materializer=cast(Any, fake_materializer),
        cache=cache_module.SharedMaterializationCache(max_entries=8),
    )
    opg = ObjectProjectionGraph.model_construct(
        id=uuid4(),
        projection_hash=projection_hash,
    )
    materializer.prime(
        branch_id=branch_id,
        opg=opg,
        commit_id=commit_id,
        oig_id=oig_id,
        graph=graph,
        indexes={"instance_map": {}, "classcfg_map": {}},
    )

    recorder = CommitPerfTraceRecorder(default_category="meta.test")
    with active_commit_perf_trace(recorder):
        cached_graph, _indexes = await materializer.get(
            branch_id=branch_id,
            ocg=_object_config_graph(),
            opg=opg,
            commit_id=commit_id,
            oig_id=oig_id,
        )

    assert cached_graph is graph
    assert fake_materializer.get_call_count == 0
    trace_summary = summarize_commit_perf_events(recorder.snapshot_json())
    assert trace_summary["oig_materialization_cache.get"]["count"] == 1
    assert trace_summary["oig_materialization_cache.hit"]["count"] == 1
    assert "oig_materialization_cache.miss" not in trace_summary


@pytest.mark.asyncio
async def test_pre_state_provider_uses_cached_lane_materializer() -> None:
    expected_head_commit_id = uuid4()
    graph_hash = "sha256:test:pre-state-cache-provider"
    handler_request = _handler_request(
        graph_hash=graph_hash,
        expected_head_commit_id=expected_head_commit_id,
    )
    before_oig = _make_graph(
        oig_id=handler_request.staged_call.lane_scope.object_instance_graph_id,
        graph_hash=graph_hash,
    )
    lane_materializer = _RecordingLaneMaterializer(
        snapshot=(before_oig, {"state": "cached"}),
    )
    provider = MetaGraphOigMaterializerPreStateProvider(
        materializer=cast(Any, _UnusedRawMaterializer()),
        lane_materializer=cast(Any, lane_materializer),
    )

    snapshot = await provider.read_pre_state(handler_request)

    plan = handler_request.execution_plan
    lane_scope = handler_request.staged_call.lane_scope
    assert snapshot.before_oig is before_oig
    assert snapshot.graph_hash_pre == graph_hash
    assert snapshot.head_commit_id == expected_head_commit_id
    assert lane_materializer.get_call_count == 1
    call = lane_materializer.calls[0]
    assert call.branch_id == lane_scope.domain_branch_id
    assert call.ocg is plan.index.ocg
    assert call.opg is plan.object_projection_graph
    assert call.commit_id == expected_head_commit_id
    assert call.oig_id == lane_scope.object_instance_graph_id
    assert call.attribute_configs_by_id is plan.index.attribute_configs_by_id
    assert call.class_configs_by_id is plan.index.class_configs_by_id


@dataclass(frozen=True, slots=True)
class _MaterializerGetCall:
    branch_id: UUID
    ocg: ObjectConfigGraph
    opg: ObjectProjectionGraph
    commit_id: UUID | None
    oig_id: UUID | None
    attribute_configs_by_id: object
    class_configs_by_id: object


class _RecordingLaneMaterializer:
    def __init__(self, *, snapshot: tuple[ObjectInstanceGraph, dict[str, object]]):
        self._snapshot = snapshot
        self.calls: list[_MaterializerGetCall] = []

    @property
    def get_call_count(self) -> int:
        return len(self.calls)

    async def get(
        self,
        *,
        branch_id: UUID,
        ocg: ObjectConfigGraph,
        opg: ObjectProjectionGraph,
        commit_id: UUID | None,
        oig_id: UUID | None = None,
        attribute_configs_by_id: object = None,
        class_configs_by_id: object = None,
        timings: object = None,
    ) -> tuple[ObjectInstanceGraph, dict[str, object]]:
        _ = timings
        self.calls.append(
            _MaterializerGetCall(
                branch_id=branch_id,
                ocg=ocg,
                opg=opg,
                commit_id=commit_id,
                oig_id=oig_id,
                attribute_configs_by_id=attribute_configs_by_id,
                class_configs_by_id=class_configs_by_id,
            )
        )
        return self._snapshot


class _FakeMaterializer:
    def __init__(self, *, snapshot: tuple[ObjectInstanceGraph, dict[str, object]]):
        self._snapshot = snapshot
        self.get_call_count = 0

    async def get(
        self, **_kwargs: object
    ) -> tuple[ObjectInstanceGraph, dict[str, object]]:
        self.get_call_count += 1
        return self._snapshot

    def indexes_from_graph(self, _graph: ObjectInstanceGraph) -> dict[str, object]:
        return {"instance_map": {}, "classcfg_map": {}}


class _UnusedRawMaterializer:
    async def get(self, **_kwargs: object) -> None:
        raise AssertionError("raw OIGMaterializer.get must not be used")


@dataclass(frozen=True, slots=True)
class _RuntimeIndex:
    ocg: ObjectConfigGraph
    attribute_configs_by_id: dict[UUID, object]
    class_configs_by_id: dict[UUID, object]
    relationships_by_id: dict[UUID, object]
    opg_by_id: dict[UUID, ObjectProjectionGraph]
    opg_by_hash: dict[str, ObjectProjectionGraph]
    portal_index: object | None = None


def _handler_request(
    *,
    graph_hash: str,
    expected_head_commit_id: UUID,
):
    opg = ObjectProjectionGraph.model_construct(
        id=uuid4(),
        projection_hash=f"sha256:test:prestate-opg:{uuid4()}",
    )
    index = _RuntimeIndex(
        ocg=_object_config_graph(),
        attribute_configs_by_id={},
        class_configs_by_id={},
        relationships_by_id={},
        opg_by_id={opg.id: opg},
        opg_by_hash={opg.projection_hash: opg},
    )
    function_config = FunctionConfig.model_construct(
        id=uuid4(),
        owner_key="aware.tests",
        name="mutate",
    )
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, cast(object, index)),
        actor_id=uuid4(),
        function_id=function_config.id,
        domain_branch_id=uuid4(),
        domain_projection_hash=opg.projection_hash,
        args=JsonArray(),
        kwargs=JsonObject(),
        expected_graph_hash_pre=graph_hash,
        expected_head_commit_id=expected_head_commit_id,
        call_target=MetaGraphCallTarget.instance,
    )
    lane_scope = resolve_meta_graph_invocation_lane_scope(
        index=cast(MetaGraphRuntimeIndex, cast(object, index)),
        request=request,
    )
    resolved_target = MetaGraphResolvedFunctionTarget(
        function_config=function_config,
        operation_label="Test.mutate",
    )
    staged_call = MetaGraphStagedFunctionCall(
        resolved_target=resolved_target,
        lane_scope=lane_scope,
        function_call=FunctionCall.model_construct(id=uuid4()),
    )
    execution_plan = MetaGraphExecutionPlan(
        index=cast(MetaGraphRuntimeIndex, cast(object, index)),
        staged_call=staged_call,
        implementation=MetaGraphFunctionImplementationDescriptor(
            kind=MetaGraphImplementationKind.language_handler,
            function_config=function_config,
        ),
        object_projection_graph=opg,
        expected_graph_hash_pre=graph_hash,
        expected_head_commit_id=expected_head_commit_id,
    )
    from aware_meta.runtime.handler_executor.contracts import (
        MetaGraphHandlerExecutionRequest,
    )

    return MetaGraphHandlerExecutionRequest(
        request=request,
        staged_call=staged_call,
        execution_plan=execution_plan,
    )


def _make_graph(*, oig_id: UUID | None = None, graph_hash: str) -> ObjectInstanceGraph:
    return ObjectInstanceGraph.model_construct(
        id=oig_id or uuid4(),
        hash=graph_hash,
        class_instances=[],
        class_instance_relationships=[],
    )


def _object_config_graph() -> ObjectConfigGraph:
    return ObjectConfigGraph.model_construct(
        id=uuid4(),
        name="TestGraph",
        fqn_prefix="aware.tests",
        hash="sha256:test:ocg",
        language=CodeLanguage.aware,
    )
