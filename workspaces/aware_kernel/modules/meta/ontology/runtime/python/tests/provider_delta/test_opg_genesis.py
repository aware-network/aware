from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast

from aware_meta.graph.projection.deltas.ontology_execution import (
    OPG_CREATE_NODE_INVOCATION_ORDER,
    OPG_CREATE_ROOT_INVOCATION_ORDER,
)
from aware_meta.graph.projection.deltas.typed_operations import (
    OBJECT_PROJECTION_GRAPH_CREATE_NODE_FUNCTION,
    OBJECT_PROJECTION_GRAPH_BUILD_FUNCTION,
    object_projection_graph_create_typed_operation,
    object_projection_graph_node_create_typed_operation,
)
from aware_meta.materialization.deltas.ontology_execution.service import (
    build_provider_delta_ontology_execution_plan,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)

from .fixtures import provider_delta_uuid


def test_opg_genesis_operations_plan_projection_root_and_node_calls() -> None:
    operations = _opg_operations()
    plan = {
        "status": "typed_operation_plan_ready",
        "typed_operations": tuple(
            operation.evidence_payload() for operation in operations
        ),
        "semantic_object_anchors": (),
    }

    ontology_plan = build_provider_delta_ontology_execution_plan(
        request=object(),
        provider_delta_typed_operation_plan=plan,
    )
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])

    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["operation_handler_result_count"] == 2
    assert ontology_plan["invocation_intent_count"] == 2
    assert [
        (
            intent["invocation_order"],
            intent["owner_class_name"],
            intent["function_name"],
            intent["target_object_id"],
            intent["result_projection_name"],
            intent["commit_required"],
        )
        for intent in intents
    ] == [
        (
            OPG_CREATE_ROOT_INVOCATION_ORDER,
            "ObjectProjectionGraph",
            "build_via_object_config_graph",
            None,
            "ObjectProjectionGraph",
            True,
        ),
        (
            OPG_CREATE_NODE_INVOCATION_ORDER,
            "ObjectProjectionGraph",
            "create_node",
            str(provider_delta_uuid("opg-genesis-opg")),
            None,
            True,
        ),
    ]


def test_opg_genesis_typed_operations_name_required_functions() -> None:
    opg_operation, node_operation = _opg_operations()

    assert opg_operation.current["required_ontology_function"] == (
        OBJECT_PROJECTION_GRAPH_BUILD_FUNCTION
    )
    assert node_operation.current["required_ontology_function"] == (
        OBJECT_PROJECTION_GRAPH_CREATE_NODE_FUNCTION
    )
    assert opg_operation.provider_operation_type == (
        "meta_ocg.object_projection_graph.create"
    )
    assert node_operation.provider_operation_type == (
        "meta_ocg.object_projection_graph_node.create"
    )
    assert "genesis" not in opg_operation.operation_key
    assert "genesis" not in node_operation.operation_key


def _opg_operations() -> tuple[
    MetaProviderDeltaTypedOperation,
    MetaProviderDeltaTypedOperation,
]:
    graph_semantic_key = "ocg:aware_demo"
    opg_semantic_key = f"{graph_semantic_key}/projection:Demo"
    return (
        object_projection_graph_create_typed_operation(
            semantic_key=opg_semantic_key,
            graph_semantic_key=graph_semantic_key,
            object_config_graph_id=str(provider_delta_uuid("opg-genesis-graph")),
            object_projection_graph_id=str(provider_delta_uuid("opg-genesis-opg")),
            name="Demo",
            projection_hash="sha256:opg-genesis",
            source_refs=("aware/home/model.aware",),
            language="aware",
            description="Demo projection.",
        ),
        object_projection_graph_node_create_typed_operation(
            semantic_key=f"{opg_semantic_key}/node:aware_demo.Room",
            object_projection_graph_semantic_key=opg_semantic_key,
            object_projection_graph_id=str(provider_delta_uuid("opg-genesis-opg")),
            object_projection_graph_node_id=str(
                provider_delta_uuid("opg-genesis-node")
            ),
            class_config_id=str(provider_delta_uuid("opg-genesis-class")),
            source_refs=("aware/home/model.aware",),
            is_root=True,
            required_for_validity=True,
        ),
    )
