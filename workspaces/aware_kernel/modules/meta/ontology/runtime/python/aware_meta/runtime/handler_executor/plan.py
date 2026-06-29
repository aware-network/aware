from __future__ import annotations

from typing import TYPE_CHECKING

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
    view = index_view if index_view is not None else MetaGraphRuntimeIndexView(index=index)
    opg = index.opg_by_id.get(staged_call.lane_scope.object_projection_graph_id)
    if opg is None:
        raise ValueError(
            "ObjectProjectionGraph not found in Meta graph index for execution plan: "
            f"{staged_call.lane_scope.object_projection_graph_id}"
        )

    implementation = view.resolve_implementation_descriptor(
        staged_call.resolved_target.function_config.id
    )
    return MetaGraphExecutionPlan(
        index=index,
        staged_call=staged_call,
        implementation=implementation,
        object_projection_graph=opg,
        target_object_id=request.target_object_id,
        expected_graph_hash_pre=request.expected_graph_hash_pre,
        expected_head_commit_id=request.expected_head_commit_id,
        function_targets_by_id=view.function_targets_by_id,
        implementation_descriptors_by_id=view.implementation_descriptors_by_id,
        function_input_edges_by_id=view.function_input_edges_by_id,
        function_input_edges_by_function_id=view.function_input_edges_by_function_id,
        function_input_edges_by_attribute_config_id=(
            view.function_input_edges_by_attribute_config_id
        ),
    )


__all__ = ["build_meta_graph_execution_plan"]
