from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from typing import cast

from aware_meta.graph.projection.deltas.ontology_execution import (
    OBJECT_CONFIG_GRAPH_CREATE_PROJECTION_DECLARATION_FUNCTION_REF,
    OBJECT_PROJECTION_GRAPH_CREATE_CONSTRUCTOR_FUNCTION_REF,
    OBJECT_PROJECTION_GRAPH_CREATE_EDGE_FUNCTION_REF,
    OBJECT_PROJECTION_GRAPH_CREATE_OBJECT_INSTANCE_GRAPH_FUNCTION_REF,
    OBJECT_PROJECTION_GRAPH_CREATE_RELATIONSHIP_FUNCTION_REF,
    OBJECT_PROJECTION_GRAPH_DECLARATION_CREATE_BINDING_FUNCTION_REF,
    OPG_CREATE_CONSTRUCTOR_INVOCATION_ORDER,
    OPG_CREATE_EDGE_INVOCATION_ORDER,
    OPG_CREATE_OBJECT_INSTANCE_GRAPH_INVOCATION_ORDER,
    OPG_CREATE_PROJECTION_BINDING_INVOCATION_ORDER,
    OPG_CREATE_PROJECTION_DECLARATION_INVOCATION_ORDER,
    OPG_CREATE_RELATIONSHIP_INVOCATION_ORDER,
)
from aware_meta.graph.projection.deltas.typed_operations import (
    object_instance_graph_create_typed_operation,
    object_projection_graph_binding_create_typed_operation,
    object_projection_graph_constructor_create_typed_operation,
    object_projection_graph_create_typed_operation,
    object_projection_graph_declaration_create_typed_operation,
    object_projection_graph_edge_create_typed_operation,
    object_projection_graph_relationship_create_typed_operation,
)
from aware_meta.materialization.deltas.ontology_execution.service import (
    build_provider_delta_ontology_execution_plan,
)

from .fixtures import provider_delta_uuid


def test_opg_runtime_members_plan_projection_member_function_calls() -> None:
    opg_id = str(provider_delta_uuid("opg-runtime-opg"))
    opg_semantic_key = "ocg:aware_demo/projection:Runtime"
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "typed_operations": tuple(
            operation.evidence_payload()
            for operation in (
                object_projection_graph_create_typed_operation(
                    semantic_key=opg_semantic_key,
                    graph_semantic_key="ocg:aware_demo",
                    object_config_graph_id=str(
                        provider_delta_uuid("opg-runtime-graph")
                    ),
                    object_projection_graph_id=opg_id,
                    name="Runtime",
                    projection_hash="sha256:opg-runtime",
                    source_refs=("aware/runtime/model.aware",),
                ),
                object_projection_graph_edge_create_typed_operation(
                    semantic_key=f"{opg_semantic_key}/edge:room_devices",
                    object_projection_graph_semantic_key=opg_semantic_key,
                    object_projection_graph_id=opg_id,
                    object_projection_graph_edge_id=str(
                        provider_delta_uuid("opg-runtime-edge")
                    ),
                    class_config_relationship_id=str(
                        provider_delta_uuid("opg-runtime-class-relationship")
                    ),
                    source_refs=("aware/runtime/model.aware",),
                    multiplicity="one",
                    depth_limit=2,
                ),
                object_projection_graph_constructor_create_typed_operation(
                    semantic_key=f"{opg_semantic_key}/constructor:Room",
                    object_projection_graph_semantic_key=opg_semantic_key,
                    object_projection_graph_id=opg_id,
                    object_projection_graph_constructor_id=str(
                        provider_delta_uuid("opg-runtime-constructor")
                    ),
                    root_node_id=str(provider_delta_uuid("opg-runtime-root-node")),
                    function_constructor_id=str(
                        provider_delta_uuid("opg-runtime-function-constructor")
                    ),
                    source_refs=("aware/runtime/model.aware",),
                ),
                object_projection_graph_relationship_create_typed_operation(
                    semantic_key=f"{opg_semantic_key}/relationship:portal",
                    object_projection_graph_semantic_key=opg_semantic_key,
                    object_projection_graph_id=opg_id,
                    object_projection_graph_relationship_id=str(
                        provider_delta_uuid("opg-runtime-relationship")
                    ),
                    target_object_projection_graph_id=str(
                        provider_delta_uuid("opg-runtime-target-opg")
                    ),
                    class_config_relationship_id=str(
                        provider_delta_uuid("opg-runtime-class-relationship")
                    ),
                    source_object_projection_graph_node_id=str(
                        provider_delta_uuid("opg-runtime-source-node")
                    ),
                    target_object_projection_graph_node_id=str(
                        provider_delta_uuid("opg-runtime-target-node")
                    ),
                    source_refs=("aware/runtime/model.aware",),
                ),
                object_instance_graph_create_typed_operation(
                    semantic_key=f"{opg_semantic_key}/object_instance_graph:Runtime",
                    object_projection_graph_semantic_key=opg_semantic_key,
                    object_projection_graph_id=opg_id,
                    object_instance_graph_id=str(
                        provider_delta_uuid("opg-runtime-oig")
                    ),
                    key="runtime",
                    root_class_config_id=str(
                        provider_delta_uuid("opg-runtime-root-class")
                    ),
                    root_source_object_id=str(
                        provider_delta_uuid("opg-runtime-root-source")
                    ),
                    name="Runtime",
                    source_refs=("aware/runtime/model.aware",),
                    description="Runtime OIG.",
                    hash="sha256:runtime-oig",
                ),
            )
        ),
        "semantic_object_anchors": (),
    }

    plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )
    intents = cast(Sequence[Mapping[str, object]], plan["invocation_intents"])
    member_intents = intents[1:]

    assert plan["status"] == "ontology_execution_plan_ready"
    assert plan["invocation_intent_count"] == 5
    assert [
        (
            intent["invocation_order"],
            intent["owner_class_name"],
            intent["function_name"],
            intent["function_ref"],
            intent["target_object_id"],
            intent["target_projection_name"],
            intent["commit_required"],
        )
        for intent in member_intents
    ] == [
        (
            OPG_CREATE_EDGE_INVOCATION_ORDER,
            "ObjectProjectionGraph",
            "create_edge",
            OBJECT_PROJECTION_GRAPH_CREATE_EDGE_FUNCTION_REF,
            opg_id,
            "ObjectProjectionGraph",
            True,
        ),
        (
            OPG_CREATE_CONSTRUCTOR_INVOCATION_ORDER,
            "ObjectProjectionGraph",
            "create_constructor",
            OBJECT_PROJECTION_GRAPH_CREATE_CONSTRUCTOR_FUNCTION_REF,
            opg_id,
            "ObjectProjectionGraph",
            True,
        ),
        (
            OPG_CREATE_RELATIONSHIP_INVOCATION_ORDER,
            "ObjectProjectionGraph",
            "create_relationship",
            OBJECT_PROJECTION_GRAPH_CREATE_RELATIONSHIP_FUNCTION_REF,
            opg_id,
            "ObjectProjectionGraph",
            True,
        ),
        (
            OPG_CREATE_OBJECT_INSTANCE_GRAPH_INVOCATION_ORDER,
            "ObjectProjectionGraph",
            "create_object_instance_graph",
            OBJECT_PROJECTION_GRAPH_CREATE_OBJECT_INSTANCE_GRAPH_FUNCTION_REF,
            opg_id,
            "ObjectProjectionGraph",
            True,
        ),
    ]
    edge_kwargs = cast(dict[str, object], member_intents[0]["kwargs"])
    oig_kwargs = cast(dict[str, object], member_intents[3]["kwargs"])
    assert edge_kwargs["multiplicity"] == "one"
    assert edge_kwargs["depth_limit"] == 2
    assert oig_kwargs == {
        "key": "runtime",
        "root_class_config_id": str(provider_delta_uuid("opg-runtime-root-class")),
        "root_source_object_id": str(provider_delta_uuid("opg-runtime-root-source")),
        "name": "Runtime",
        "description": "Runtime OIG.",
        "hash": "sha256:runtime-oig",
    }


def test_opg_projection_declaration_operations_plan_function_calls() -> None:
    graph_semantic_key = "ocg:aware_demo"
    declaration_semantic_key = f"{graph_semantic_key}/projection_declaration:Runtime"
    graph_id = str(provider_delta_uuid("opg-runtime-declaration-graph"))
    declaration_id = str(provider_delta_uuid("opg-runtime-declaration"))
    binding_id = str(provider_delta_uuid("opg-runtime-declaration-binding"))
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "typed_operations": tuple(
            operation.evidence_payload()
            for operation in (
                object_projection_graph_declaration_create_typed_operation(
                    semantic_key=declaration_semantic_key,
                    graph_semantic_key=graph_semantic_key,
                    object_config_graph_id=graph_id,
                    object_projection_graph_declaration_id=declaration_id,
                    key="aware_demo:Runtime",
                    projection_name="Runtime",
                    source_refs=("aware/runtime/model.aware",),
                    description="Runtime declaration.",
                    is_branchable=True,
                ),
                object_projection_graph_binding_create_typed_operation(
                    semantic_key=f"{declaration_semantic_key}/binding:aware_demo.Room",
                    object_projection_graph_declaration_semantic_key=(
                        declaration_semantic_key
                    ),
                    object_projection_graph_declaration_id=declaration_id,
                    object_projection_graph_binding_id=binding_id,
                    fqn_prefix="aware_demo",
                    namespace="home",
                    class_name="Room",
                    source_refs=("aware/runtime/model.aware",),
                    attribute_name="selected_channel",
                    target_projection_name="Runtime",
                    side="source",
                ),
            )
        ),
        "semantic_object_anchors": (),
    }

    plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )
    intents = cast(Sequence[Mapping[str, object]], plan["invocation_intents"])

    assert plan["status"] == "ontology_execution_plan_ready"
    assert plan["invocation_intent_count"] == 2
    assert [
        (
            intent["invocation_order"],
            intent["owner_class_name"],
            intent["function_name"],
            intent["function_ref"],
            intent["target_object_id"],
            intent["target_projection_name"],
            intent["expected_result_object_id"],
            intent["commit_required"],
        )
        for intent in intents
    ] == [
        (
            OPG_CREATE_PROJECTION_DECLARATION_INVOCATION_ORDER,
            "ObjectConfigGraph",
            "create_object_projection_graph_declaration",
            OBJECT_CONFIG_GRAPH_CREATE_PROJECTION_DECLARATION_FUNCTION_REF,
            graph_id,
            "ObjectConfigGraph",
            declaration_id,
            True,
        ),
        (
            OPG_CREATE_PROJECTION_BINDING_INVOCATION_ORDER,
            "ObjectProjectionGraphDeclaration",
            "create_binding",
            OBJECT_PROJECTION_GRAPH_DECLARATION_CREATE_BINDING_FUNCTION_REF,
            declaration_id,
            "ObjectConfigGraph",
            binding_id,
            True,
        ),
    ]
    declaration_kwargs = cast(dict[str, object], intents[0]["kwargs"])
    binding_kwargs = cast(dict[str, object], intents[1]["kwargs"])
    assert declaration_kwargs == {
        "key": "aware_demo:Runtime",
        "projection_name": "Runtime",
        "label": None,
        "description": "Runtime declaration.",
        "is_branchable": True,
        "object_projection_graph_declaration_id": declaration_id,
    }
    assert binding_kwargs == {
        "fqn_prefix": "aware_demo",
        "namespace": "home",
        "class_name": "Room",
        "attribute_name": "selected_channel",
        "target_projection_name": "Runtime",
        "side": "source",
        "object_projection_graph_binding_id": binding_id,
    }
