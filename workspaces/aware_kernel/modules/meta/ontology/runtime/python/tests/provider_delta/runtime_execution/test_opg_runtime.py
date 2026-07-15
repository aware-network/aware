from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from aware_meta.graph.projection.deltas.typed_operations import (
    object_instance_graph_create_typed_operation,
    object_projection_graph_constructor_create_typed_operation,
    object_projection_graph_edge_create_typed_operation,
    object_projection_graph_relationship_create_typed_operation,
)
from aware_meta.materialization.deltas.execution import (
    _provider_delta_oig_commit_receipt,
)
from aware_meta.materialization.deltas.ontology_execution.service import (
    build_provider_delta_ontology_execution_plan,
)

from ..fixtures import provider_delta_uuid
from .fixtures import (
    ProviderDeltaRuntimeExecutionContext,
    build_provider_delta_runtime_execution_context,
)


async def _commit_opg_operations(
    *,
    ctx: ProviderDeltaRuntimeExecutionContext,
    typed_operation_plan: dict[str, object],
) -> dict[str, object]:
    ontology_execution_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )
    assert ontology_execution_plan["status"] == "ontology_execution_plan_ready"
    return await _provider_delta_oig_commit_receipt(
        request=ctx.request,
        baseline_dirty_preflight=ctx.baseline_dirty_preflight,
        provider_delta_mutation_plan={},
        provider_delta_ontology_execution_plan=ontology_execution_plan,
        provider_delta_execute_flag_preflight={
            "status": "execute_flag_preflight_ready",
        },
    )


@pytest.mark.asyncio
async def test_meta_provider_delta_executes_opg_runtime_member_intents(
    tmp_path: Path,
) -> None:
    ctx = build_provider_delta_runtime_execution_context(
        workspace_root=tmp_path,
        key="opg-runtime-members",
    )
    opg_id = str(provider_delta_uuid("opg-runtime-exec-opg"))
    opg_semantic_key = "ocg:aware_demo/projection:Runtime"
    typed_operation_plan: dict[str, object] = {
        "status": "typed_operation_plan_ready",
        "typed_operations": tuple(
            operation.evidence_payload()
            for operation in (
                object_projection_graph_edge_create_typed_operation(
                    semantic_key=f"{opg_semantic_key}/edge:room_devices",
                    object_projection_graph_semantic_key=opg_semantic_key,
                    object_projection_graph_id=opg_id,
                    object_projection_graph_edge_id=str(
                        provider_delta_uuid("opg-runtime-exec-edge")
                    ),
                    class_config_relationship_id=str(
                        provider_delta_uuid("opg-runtime-exec-relationship")
                    ),
                    source_refs=("aware/runtime/model.aware",),
                ),
                object_projection_graph_constructor_create_typed_operation(
                    semantic_key=f"{opg_semantic_key}/constructor:Room",
                    object_projection_graph_semantic_key=opg_semantic_key,
                    object_projection_graph_id=opg_id,
                    object_projection_graph_constructor_id=str(
                        provider_delta_uuid("opg-runtime-exec-constructor")
                    ),
                    root_node_id=str(provider_delta_uuid("opg-runtime-exec-root-node")),
                    function_constructor_id=str(
                        provider_delta_uuid("opg-runtime-exec-function-constructor")
                    ),
                    source_refs=("aware/runtime/model.aware",),
                ),
                object_projection_graph_relationship_create_typed_operation(
                    semantic_key=f"{opg_semantic_key}/relationship:portal",
                    object_projection_graph_semantic_key=opg_semantic_key,
                    object_projection_graph_id=opg_id,
                    object_projection_graph_relationship_id=str(
                        provider_delta_uuid("opg-runtime-exec-relationship-edge")
                    ),
                    target_object_projection_graph_id=str(
                        provider_delta_uuid("opg-runtime-exec-target-opg")
                    ),
                    class_config_relationship_id=str(
                        provider_delta_uuid("opg-runtime-exec-relationship")
                    ),
                    source_object_projection_graph_node_id=str(
                        provider_delta_uuid("opg-runtime-exec-source-node")
                    ),
                    target_object_projection_graph_node_id=str(
                        provider_delta_uuid("opg-runtime-exec-target-node")
                    ),
                    source_refs=("aware/runtime/model.aware",),
                ),
                object_instance_graph_create_typed_operation(
                    semantic_key=f"{opg_semantic_key}/object_instance_graph:Runtime",
                    object_projection_graph_semantic_key=opg_semantic_key,
                    object_projection_graph_id=opg_id,
                    object_instance_graph_id=str(
                        provider_delta_uuid("opg-runtime-exec-oig")
                    ),
                    key="runtime",
                    root_class_config_id=str(
                        provider_delta_uuid("opg-runtime-exec-root-class")
                    ),
                    root_source_object_id=str(
                        provider_delta_uuid("opg-runtime-exec-root-source")
                    ),
                    name="Runtime",
                    source_refs=("aware/runtime/model.aware",),
                    hash="sha256:runtime-exec-oig",
                ),
            )
        ),
        "semantic_object_anchors": (),
    }

    receipt = await _commit_opg_operations(
        ctx=ctx,
        typed_operation_plan=typed_operation_plan,
    )

    assert receipt["status"] == "execute_flag_commit_applied"
    invocation_receipt = cast(
        dict[str, object],
        receipt["ontology_function_call_execution_receipt"],
    )
    assert invocation_receipt["status"] == "ontology_function_call_execution_applied"
    assert invocation_receipt["applied_invocation_count"] == 4
    assert len(ctx.runtime.requests) == 4
    assert [request.function_id for request in ctx.runtime.requests] == [
        provider_delta_uuid("ObjectProjectionGraph.create_edge.function"),
        provider_delta_uuid("ObjectProjectionGraph.create_constructor.function"),
        provider_delta_uuid("ObjectProjectionGraph.create_relationship.function"),
        provider_delta_uuid(
            "ObjectProjectionGraph.create_object_instance_graph.function"
        ),
    ]
    assert [str(request.target_object_id) for request in ctx.runtime.requests] == [
        opg_id,
        opg_id,
        opg_id,
        opg_id,
    ]
