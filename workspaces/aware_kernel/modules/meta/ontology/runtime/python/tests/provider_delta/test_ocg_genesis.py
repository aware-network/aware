from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast

from aware_meta.attribute.config.deltas.ontology_execution import (
    ATTRIBUTE_CREATE_INVOCATION_ORDER,
)
from aware_meta.class_.config.deltas.ontology_execution import (
    CLASS_CREATE_CLASS_INVOCATION_ORDER,
    CLASS_CREATE_NODE_INVOCATION_ORDER,
)
from aware_meta.graph.config.deltas.ontology_execution import (
    GRAPH_BUILD_INVOCATION_ORDER,
)
from aware_meta.graph.package.deltas.ontology_execution import (
    PACKAGE_ATTACH_GRAPH_INVOCATION_ORDER,
    PACKAGE_BUILD_INVOCATION_ORDER,
)
from aware_meta.graph.projection.deltas.ontology_execution import (
    OPG_CREATE_NODE_INVOCATION_ORDER,
    OPG_CREATE_ROOT_INVOCATION_ORDER,
)
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.materialization.deltas.capability_matrix import (
    EXECUTABLE_VIA_ONTOLOGY_FUNCTION,
)
from aware_meta.materialization.deltas.ocg_genesis import (
    OCG_GENESIS_CONTRACT_VERSION,
    MetaOcgGenesisSpec,
    ocg_genesis_preflight,
    ocg_genesis_typed_operation_plan,
)
from aware_meta.materialization.deltas.semantic_scope_closure import (
    build_meta_ocg_semantic_scope_closure,
)
from aware_meta_ontology.class_.class_config import ClassConfig

from .fixtures import provider_delta_uuid


def test_ocg_genesis_typed_operation_plan_names_package_root_and_members() -> None:
    plan = ocg_genesis_typed_operation_plan(spec=_genesis_spec())
    operations = cast(Sequence[Mapping[str, object]], plan["typed_operations"])
    provider_operation_types = {
        str(operation["provider_operation_type"]) for operation in operations
    }
    required_functions = cast(
        tuple[str, ...],
        plan["required_ontology_functions"],
    )

    assert plan["contract_version"] == OCG_GENESIS_CONTRACT_VERSION
    assert plan["status"] == "typed_operation_plan_ready"
    assert plan["typed_operation_count"] == 7
    assert plan["semantic_scope_closure_consumed"] is True
    assert plan["semantic_scope_closure_ready"] is True
    assert plan["semantic_scope_closure_status"] == ("semantic_scope_closure_ready")
    assert plan["semantic_scope_closure_blockers"] == ()
    assert plan["builder_fallback_used"] is False
    assert plan["would_use_builder"] is False
    assert provider_operation_types == {
        "meta_ocg.object_config_graph_package.create",
        "meta_ocg.object_config_graph.create",
        "meta_ocg.object_config_graph_package.update",
        "meta_ocg.class.create",
        "meta_ocg.attribute.create",
        "meta_ocg.object_projection_graph.create",
        "meta_ocg.object_projection_graph_node.create",
    }
    assert required_functions == (
        "ObjectConfigGraphPackage.build",
        "ObjectConfigGraph.build",
        "ObjectConfigGraphPackage.attach_object_config_graph",
        "ObjectConfigGraph.create_node",
        "ObjectConfigGraphNode.create_class",
        "ClassConfig.create_primitive_attribute_config",
        "ObjectProjectionGraph.build_via_object_config_graph",
        "ObjectProjectionGraph.create_node",
    )


def test_ocg_genesis_blocks_typed_operations_when_scope_closure_misses_class() -> None:
    spec = _genesis_spec()
    plan = ocg_genesis_typed_operation_plan(
        spec=spec,
        semantic_scope_closure=_scope_closure_for_class_fqn(
            class_fqn="aware_demo.Other",
            class_name="Other",
        ),
    )

    assert plan["status"] == "typed_operation_plan_blocked"
    assert plan["reason"] == "meta_ocg_semantic_scope_closure_blocked"
    assert plan["typed_operation_count"] == 0
    assert plan["typed_operations"] == ()
    assert plan["semantic_scope_closure_consumed"] is False
    assert plan["semantic_scope_closure_ready"] is False
    assert plan["semantic_scope_closure_status"] == ("semantic_scope_closure_ready")
    assert plan["semantic_scope_closure_blockers"] == (
        "semantic_scope_closure_missing_class_fqn:aware_demo.Room",
    )
    assert plan["blockers"] == (
        "semantic_scope_closure_missing_class_fqn:aware_demo.Room",
    )
    assert plan["builder_fallback_used"] is False
    assert plan["would_use_builder"] is False


def test_ocg_genesis_preflight_blocks_before_execution_when_scope_is_blocked() -> None:
    spec = _genesis_spec()
    preflight = ocg_genesis_preflight(
        spec=spec,
        semantic_scope_closure=_scope_closure_for_class_fqn(
            class_fqn="aware_demo.Other",
            class_name="Other",
        ),
    )
    typed_plan = cast(Mapping[str, object], preflight["typed_operation_plan"])

    assert preflight["status"] == "ocg_genesis_blocked"
    assert preflight["reason"] == (
        "meta_ocg_package_genesis_typed_operation_plan_blocked"
    )
    assert preflight["execution_allowed"] is False
    assert preflight["typed_operation_count"] == 0
    assert preflight["ontology_invocation_intent_count"] == 0
    assert preflight["ontology_execution_plan"] is None
    assert preflight["functioncall_capability_matrix"] is None
    assert preflight["blockers"] == (
        "semantic_scope_closure_missing_class_fqn:aware_demo.Room",
    )
    assert typed_plan["status"] == "typed_operation_plan_blocked"


def test_ocg_genesis_preflight_is_fully_executable_via_functioncalls() -> None:
    preflight = ocg_genesis_preflight(spec=_genesis_spec())
    ontology_plan = cast(
        Mapping[str, object],
        preflight["ontology_execution_plan"],
    )
    capability_matrix = cast(
        Mapping[str, object],
        preflight["functioncall_capability_matrix"],
    )
    handler_reason_counts = cast(
        dict[str, int],
        ontology_plan["handler_reason_counts"],
    )
    capability_status_counts = cast(
        dict[str, int],
        capability_matrix["capability_status_counts"],
    )

    assert preflight["status"] == "ocg_genesis_executable"
    assert preflight["reason"] == ("meta_ocg_package_genesis_functioncalls_ready")
    assert preflight["execution_allowed"] is True
    typed_operation_plan = cast(
        Mapping[str, object],
        preflight["typed_operation_plan"],
    )
    assert typed_operation_plan["semantic_scope_closure_consumed"] is True
    assert preflight["builder_fallback_used"] is False
    assert preflight["would_use_builder"] is False
    assert preflight["did_execute"] is False
    assert preflight["did_persist"] is False
    assert preflight["typed_operation_count"] == 7
    assert preflight["ontology_invocation_intent_count"] == 8
    assert preflight["executable_operation_count"] == 7
    assert preflight["non_executable_operation_count"] == 0
    assert preflight["blocker_count"] == 0
    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["invocation_intent_count"] == 8
    assert ontology_plan["operation_handler_result_count"] == 7
    assert handler_reason_counts == {
        "meta_ocg_attribute_create_function_call_ready": 1,
        "meta_ocg_class_create_function_call_ready": 1,
        "meta_ocg_graph_create_function_call_ready": 1,
        "meta_opg_create_function_call_ready": 1,
        "meta_opg_node_create_function_call_ready": 1,
        "meta_ocg_package_attach_graph_function_call_ready": 1,
        "meta_ocg_package_create_function_call_ready": 1,
    }
    assert capability_status_counts == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 7,
    }
    assert ontology_plan["blockers"] == ()
    assert preflight["blockers"] == ()


def test_ocg_genesis_preflight_orders_root_and_member_intents() -> None:
    preflight = ocg_genesis_preflight(spec=_genesis_spec())
    ontology_plan = cast(
        Mapping[str, object],
        preflight["ontology_execution_plan"],
    )
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])

    assert [
        (
            intent["invocation_order"],
            intent["owner_class_name"],
            intent["function_name"],
            intent["target_object_id"],
            intent.get("target_projection_name"),
            intent.get("result_projection_name"),
            intent.get("commit_required"),
        )
        for intent in intents
    ] == [
        (
            PACKAGE_BUILD_INVOCATION_ORDER,
            "ObjectConfigGraphPackage",
            "build",
            None,
            None,
            "ObjectConfigGraphPackage",
            False,
        ),
        (
            GRAPH_BUILD_INVOCATION_ORDER,
            "ObjectConfigGraph",
            "build",
            None,
            None,
            "ObjectConfigGraph",
            False,
        ),
        (
            PACKAGE_ATTACH_GRAPH_INVOCATION_ORDER,
            "ObjectConfigGraphPackage",
            "attach_object_config_graph",
            str(provider_delta_uuid("ocg-genesis-package")),
            "ObjectConfigGraphPackage",
            None,
            False,
        ),
        (
            CLASS_CREATE_NODE_INVOCATION_ORDER,
            "ObjectConfigGraph",
            "create_node",
            str(provider_delta_uuid("ocg-genesis-graph")),
            None,
            None,
            False,
        ),
        (
            CLASS_CREATE_CLASS_INVOCATION_ORDER,
            "ObjectConfigGraphNode",
            "create_class",
            str(provider_delta_uuid("ocg-genesis-node")),
            None,
            None,
            False,
        ),
        (
            ATTRIBUTE_CREATE_INVOCATION_ORDER,
            "ClassConfig",
            "create_primitive_attribute_config",
            str(provider_delta_uuid("ocg-genesis-class")),
            None,
            None,
            False,
        ),
        (
            OPG_CREATE_ROOT_INVOCATION_ORDER,
            "ObjectProjectionGraph",
            "build_via_object_config_graph",
            None,
            None,
            "ObjectProjectionGraph",
            True,
        ),
        (
            OPG_CREATE_NODE_INVOCATION_ORDER,
            "ObjectProjectionGraph",
            "create_node",
            str(provider_delta_uuid("ocg-genesis-opg")),
            "ObjectProjectionGraph",
            None,
            True,
        ),
    ]


def _genesis_spec() -> MetaOcgGenesisSpec:
    return MetaOcgGenesisSpec(
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
        source_ref="aware/home/model.aware",
        package_id=str(provider_delta_uuid("ocg-genesis-package")),
        object_config_graph_id=str(provider_delta_uuid("ocg-genesis-graph")),
        object_config_graph_node_id=str(provider_delta_uuid("ocg-genesis-node")),
        class_config_id=str(provider_delta_uuid("ocg-genesis-class")),
        attribute_config_id=str(provider_delta_uuid("ocg-genesis-attribute")),
        object_projection_graph_id=str(provider_delta_uuid("ocg-genesis-opg")),
        object_projection_graph_node_id=str(
            provider_delta_uuid("ocg-genesis-opg-node")
        ),
        class_name="Room",
        attribute_name="name",
        graph_hash="sha256:ocg-genesis",
        layout_hash="sha256:layout",
        projection_name="Demo",
        projection_hash="sha256:opg-genesis",
        package_title="Demo ontology",
        package_description="Demo package.",
        class_description="Room in a demo home.",
        attribute_description="Human-readable room name.",
    )


def _scope_closure_for_class_fqn(
    *,
    class_fqn: str,
    class_name: str,
) -> Mapping[str, object]:
    class_config = ClassConfig(
        id=provider_delta_uuid(f"scope-closure-class:{class_fqn}"),
        class_fqn=class_fqn,
        name=class_name,
    )
    return build_meta_ocg_semantic_scope_closure(
        package_fqn_prefix="aware_demo",
        namespace_by_code_id={
            provider_delta_uuid("ocg-genesis-scope-code"): NamespacePath(
                package="aware_demo",
                namespace="default",
            ),
        },
        class_configs=(class_config,),
    ).evidence_payload()
