from __future__ import annotations

from typing import TYPE_CHECKING

from aware_meta.graph.instance.commit.perf_trace import commit_perf_span
from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphExecutionPlan,
    MetaGraphRuntimeIndex,
    MetaGraphStagedFunctionCall,
)
from aware_meta.runtime.handler_executor.index import MetaGraphRuntimeIndexView

if TYPE_CHECKING:
    from aware_meta.runtime.invocation_engine import MetaGraphInvokeFunctionInput


def build_meta_graph_execution_plan(
    *,
    index: MetaGraphRuntimeIndex,
    request: "MetaGraphInvokeFunctionInput",
    staged_call: MetaGraphStagedFunctionCall,
    index_view: MetaGraphRuntimeIndexView | None = None,
) -> MetaGraphExecutionPlan:
    metadata = {
        "function_id": str(staged_call.resolved_target.function_config.id),
        "object_projection_graph_id": str(
            staged_call.lane_scope.object_projection_graph_id
        ),
    }
    with commit_perf_span(
        phase="handler_execution.execution_plan.resolve_index_view",
        category="meta.runtime.handler_execution",
        metadata=metadata,
    ):
        if index_view is not None and index_view.index is not index:
            raise ValueError(
                "MetaGraphRuntimeIndexView belongs to a different runtime index object"
            )
        view = (
            index_view
            if index_view is not None
            else MetaGraphRuntimeIndexView(index=index)
        )
    with commit_perf_span(
        phase="handler_execution.execution_plan.resolve_opg",
        category="meta.runtime.handler_execution",
        metadata=metadata,
    ):
        opg = index.opg_by_id.get(staged_call.lane_scope.object_projection_graph_id)
    if opg is None:
        raise ValueError(
            f"ObjectProjectionGraph not found in Meta graph index for execution plan: {staged_call.lane_scope.object_projection_graph_id}"
        )

    with commit_perf_span(
        phase="handler_execution.execution_plan.resolve_implementation",
        category="meta.runtime.handler_execution",
        metadata=metadata,
    ):
        implementation = view.resolve_implementation_descriptor(
            staged_call.resolved_target.function_config.id
        )
    with commit_perf_span(
        phase="handler_execution.execution_plan.function_targets",
        category="meta.runtime.handler_execution",
        metadata=metadata,
    ):
        function_targets_by_id = view.function_targets_by_id
    with commit_perf_span(
        phase="handler_execution.execution_plan.implementation_descriptors",
        category="meta.runtime.handler_execution",
        metadata=metadata,
    ):
        implementation_descriptors_by_id = view.implementation_descriptors_by_id
    with commit_perf_span(
        phase="handler_execution.execution_plan.function_input_edges_by_id",
        category="meta.runtime.handler_execution",
        metadata=metadata,
    ):
        function_input_edges_by_id = view.function_input_edges_by_id
    with commit_perf_span(
        phase=(
            "handler_execution.execution_plan." "function_input_edges_by_function_id"
        ),
        category="meta.runtime.handler_execution",
        metadata=metadata,
    ):
        function_input_edges_by_function_id = view.function_input_edges_by_function_id
    with commit_perf_span(
        phase=(
            "handler_execution.execution_plan."
            "function_input_edges_by_attribute_config_id"
        ),
        category="meta.runtime.handler_execution",
        metadata=metadata,
    ):
        function_input_edges_by_attribute_config_id = (
            view.function_input_edges_by_attribute_config_id
        )
    with commit_perf_span(
        phase="handler_execution.execution_plan.orm_change_translation_index_cache",
        category="meta.runtime.handler_execution",
        metadata=metadata,
    ):
        orm_change_translation_index_cache = view.orm_change_translation_index_cache(
            object_config_graph=index.ocg,
            class_configs_by_id=index.class_configs_by_id,
            relationships_by_id=index.relationships_by_id,
        )
    with commit_perf_span(
        phase="handler_execution.execution_plan.construct_plan",
        category="meta.runtime.handler_execution",
        metadata=metadata,
    ):
        oig_model_construction_plan_cache = view.oig_model_construction_plan_cache(
            index=index
        )
        return MetaGraphExecutionPlan(
            index=index,
            staged_call=staged_call,
            implementation=implementation,
            object_projection_graph=opg,
            target_object_id=request.target_object_id,
            expected_graph_hash_pre=request.expected_graph_hash_pre,
            expected_head_commit_id=request.expected_head_commit_id,
            function_targets_by_id=function_targets_by_id,
            implementation_descriptors_by_id=implementation_descriptors_by_id,
            function_input_edges_by_id=function_input_edges_by_id,
            function_input_edges_by_function_id=function_input_edges_by_function_id,
            function_input_edges_by_attribute_config_id=(
                function_input_edges_by_attribute_config_id
            ),
            orm_change_translation_index_cache=orm_change_translation_index_cache,
            oig_model_construction_plan_cache=oig_model_construction_plan_cache,
        )


__all__ = ["build_meta_graph_execution_plan"]
