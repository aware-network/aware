from __future__ import annotations

from collections.abc import Sequence
from types import SimpleNamespace
from typing import cast

from aware_meta.materialization.deltas.capability_matrix import (
    EXECUTABLE_VIA_ONTOLOGY_FUNCTION,
    build_provider_delta_functioncall_capability_matrix,
)
from aware_meta.materialization.deltas.ontology_execution import (
    build_provider_delta_ontology_execution_plan,
)
from aware_meta.function.config.deltas.membership_ontology_execution import (
    CLASS_CONFIG_FUNCTION_CONFIG_UPDATE_CONFIG_FUNCTION_REF,
)

from .fixtures import provider_delta_uuid


def test_meta_provider_delta_function_membership_update_ontology_execution_plan_ready() -> (
    None
):
    function_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room.rename"
    membership_semantic_key = f"{function_semantic_key}/membership:class_config"
    function_config_id = provider_delta_uuid(
        "ontology-exec-function-membership-function"
    )
    class_config_id = provider_delta_uuid("ontology-exec-function-membership-class")
    edge_id = provider_delta_uuid("ontology-exec-function-membership-edge")
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:function_membership:"
                    f"{membership_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.function_membership.update",
                "semantic_key": membership_semantic_key,
                "semantic_subject_type": "aware_meta.ClassConfigFunctionConfig",
                "ontology_subject_kind": "function_membership",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(edge_id),
                    "object_kind": "function_membership",
                    "object": {
                        "class_config_function_config_id": str(edge_id),
                        "class_config_id": str(class_config_id),
                        "function_config_id": str(function_config_id),
                        "function_membership_signature": {
                            "class_config_id": str(class_config_id),
                            "function_config_id": str(function_config_id),
                            "is_public": True,
                            "is_constructor": False,
                            "position": 0,
                        },
                    },
                },
                "current": {
                    "semantic_key": membership_semantic_key,
                    "object_kind": "function_membership",
                    "class_config_function_config_id": str(edge_id),
                    "class_config_id": str(class_config_id),
                    "function_config_id": str(function_config_id),
                    "function_semantic_key": function_semantic_key,
                    "function_membership_signature": {
                        "class_config_id": str(class_config_id),
                        "function_config_id": str(function_config_id),
                        "is_public": False,
                        "is_constructor": True,
                        "position": 2,
                    },
                },
            },
        ),
    }

    plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )
    matrix = build_provider_delta_functioncall_capability_matrix(
        provider_delta_typed_operation_plan=typed_operation_plan,
        provider_delta_ontology_execution_plan=plan,
    )

    assert plan["status"] == "ontology_execution_plan_ready"
    assert plan["reason"] == "meta_ocg_ontology_execution_plan_ready"
    assert plan["blockers"] == ()
    assert plan["invocation_intent_count"] == 1
    handler_results = cast(
        Sequence[dict[str, object]],
        plan["operation_handler_results"],
    )
    assert handler_results[0]["reason"] == (
        "meta_ocg_function_membership_update_function_call_ready"
    )
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    intent = intents[0]
    assert intent["owner_class_name"] == "ClassConfigFunctionConfig"
    assert intent["function_name"] == "update_config"
    assert intent["function_ref"] == (
        CLASS_CONFIG_FUNCTION_CONFIG_UPDATE_CONFIG_FUNCTION_REF
    )
    assert intent["target_object_id"] == str(edge_id)
    assert intent["receiver_semantic_key"] == membership_semantic_key
    assert intent["expected_result_object_id"] == str(edge_id)
    assert intent["kwargs"] == {
        "is_public": False,
        "is_constructor": True,
        "position": 2,
    }
    assert matrix["status"] == "functioncall_capability_matrix_ready"
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["execution_policy"] == "ontology_function_call_only"
    assert matrix["execution_allowed"] is True
    assert matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }


def test_meta_provider_delta_function_membership_update_blocks_identity_change() -> (
    None
):
    membership_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room.rename"
        "/membership:class_config"
    )
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:function_membership:"
                    f"{membership_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.function_membership.update",
                "semantic_key": membership_semantic_key,
                "semantic_subject_type": "aware_meta.ClassConfigFunctionConfig",
                "ontology_subject_kind": "function_membership",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(
                        provider_delta_uuid("ontology-exec-membership-identity-edge")
                    ),
                    "object_kind": "function_membership",
                    "object": {
                        "class_config_id": str(
                            provider_delta_uuid(
                                "ontology-exec-membership-baseline-class"
                            )
                        ),
                        "function_config_id": str(
                            provider_delta_uuid(
                                "ontology-exec-membership-baseline-function"
                            )
                        ),
                    },
                },
                "current": {
                    "class_config_id": str(
                        provider_delta_uuid("ontology-exec-membership-current-class")
                    ),
                    "function_config_id": str(
                        provider_delta_uuid("ontology-exec-membership-current-function")
                    ),
                    "function_membership_signature": {
                        "is_public": True,
                        "is_constructor": False,
                        "position": 0,
                    },
                },
            },
        ),
    }

    plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )
    matrix = build_provider_delta_functioncall_capability_matrix(
        provider_delta_typed_operation_plan=typed_operation_plan,
        provider_delta_ontology_execution_plan=plan,
    )

    assert plan["status"] == "ontology_execution_plan_blocked"
    assert plan["reason"] == "meta_ocg_ontology_execution_plan_blocked"
    blockers = cast(Sequence[str], plan["blockers"])
    assert set(blockers) == {
        ("function_membership_identity_change_requires_replacement:" "class_config_id"),
        (
            "function_membership_identity_change_requires_replacement:"
            "function_config_id"
        ),
    }
    handler_results = cast(
        Sequence[dict[str, object]],
        plan["operation_handler_results"],
    )
    assert handler_results[0]["reason"] == (
        "meta_ocg_function_membership_update_requires_existing_edge"
    )
    assert matrix["coverage_status"] == "all_operations_blocked"
    assert matrix["capability_status_counts"] == {
        "unsupported": 1,
    }
