from __future__ import annotations

from collections.abc import Sequence
from types import SimpleNamespace
from typing import cast

from aware_meta.materialization.deltas.capability_matrix import (
    EXECUTABLE_VIA_ONTOLOGY_FUNCTION,
    build_provider_delta_functioncall_capability_matrix,
)
from aware_meta.materialization.deltas.ontology_execution.service import (
    build_provider_delta_ontology_execution_plan,
)
from aware_meta.function.config.deltas.ontology_execution import (
    CLASS_CONFIG_REMOVE_FUNCTION_CONFIG_FUNCTION_REF,
    FUNCTION_CONFIG_CREATE_INVOCATION_FUNCTION_REF,
    FUNCTION_CONFIG_UPDATE_CONFIG_FUNCTION_REF,
)

from .fixtures import provider_delta_uuid


def test_meta_provider_delta_function_update_ontology_execution_plan_ready() -> None:
    function_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room.rename"
    generic_object_id = provider_delta_uuid(
        "ontology-exec-update-function-generic-object"
    )
    function_config_id = provider_delta_uuid("ontology-exec-update-function")
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:function:"
                    f"{function_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.function.update",
                "semantic_key": function_semantic_key,
                "semantic_subject_type": "aware_meta.FunctionConfig",
                "ontology_subject_kind": "function",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(generic_object_id),
                    "object_kind": "function",
                    "object": {
                        "object_id": str(generic_object_id),
                        "payload": {
                            "entity_id": str(function_config_id),
                            "function_config_id": str(function_config_id),
                            "owner_key": "aware_demo.default.home.Room",
                            "name": "rename",
                            "kind": "instance",
                        },
                        "owner_key": "aware_demo.default.home.Room",
                        "name": "rename",
                        "kind": "instance",
                    },
                },
                "current": {
                    "semantic_key": function_semantic_key,
                    "object_kind": "function",
                    "object_id": str(generic_object_id),
                    "entity_id": str(function_config_id),
                    "function_config_id": str(function_config_id),
                    "entity_name": "rename",
                    "function_name": "rename",
                    "payload": {
                        "verb": "upsert",
                    },
                    "function_signature": {
                        "owner_key": "aware_demo.default.home.Room",
                        "name": "rename",
                        "kind": "instance",
                        "description": "Rename a room.",
                        "verb": "rename",
                        "is_async": True,
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
        "meta_ocg_function_update_function_call_ready"
    )
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    intent = intents[0]
    assert intent["owner_class_name"] == "FunctionConfig"
    assert intent["function_name"] == "update_config"
    assert intent["function_ref"] == FUNCTION_CONFIG_UPDATE_CONFIG_FUNCTION_REF
    assert intent["target_object_id"] == str(function_config_id)
    assert intent["receiver_semantic_key"] == function_semantic_key
    assert intent["expected_result_object_id"] == str(function_config_id)
    assert intent["kwargs"] == {
        "description": "Rename a room.",
        "verb": "rename",
        "is_async": True,
    }
    assert matrix["status"] == "functioncall_capability_matrix_ready"
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["execution_policy"] == "ontology_function_call_only"
    assert matrix["execution_allowed"] is True
    assert matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }


def test_meta_provider_delta_function_update_blocks_identity_change() -> None:
    function_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room.rename"
    function_config_id = provider_delta_uuid("ontology-exec-update-function-identity")
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:function:"
                    f"{function_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.function.update",
                "semantic_key": function_semantic_key,
                "semantic_subject_type": "aware_meta.FunctionConfig",
                "ontology_subject_kind": "function",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(function_config_id),
                    "object_kind": "function",
                    "object": {
                        "owner_key": "aware_demo.default.home.Room",
                        "name": "rename",
                        "kind": "instance",
                    },
                },
                "current": {
                    "function_signature": {
                        "owner_key": "aware_demo.default.home.Device",
                        "name": "rename_device",
                        "kind": "static",
                        "description": "Rename a device.",
                        "verb": "rename",
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
        "function_identity_change_requires_replacement:owner_key",
        "function_identity_change_requires_replacement:name",
        "function_identity_change_requires_replacement:kind",
    }
    handler_results = cast(
        Sequence[dict[str, object]],
        plan["operation_handler_results"],
    )
    assert handler_results[0]["reason"] == (
        "meta_ocg_function_update_requires_existing_function_config"
    )
    assert matrix["coverage_status"] == "all_operations_blocked"
    assert matrix["capability_status_counts"] == {
        "unsupported": 1,
    }


def test_meta_provider_delta_function_delete_ontology_execution_plan_ready() -> None:
    function_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room.rename"
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    class_config_id = provider_delta_uuid("ontology-exec-delete-function-class")
    function_config_id = provider_delta_uuid("ontology-exec-delete-function")
    executable_class_instance_id = provider_delta_uuid(
        "ontology-exec-delete-function-class-instance"
    )
    executable_function_instance_id = provider_delta_uuid(
        "ontology-exec-delete-function-instance"
    )
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": f"meta_ocg.function.delete:{function_semantic_key}",
                "operation_family": "delete",
                "provider_operation_type": "meta_ocg.function.delete",
                "semantic_key": function_semantic_key,
                "semantic_subject_type": "aware_meta.FunctionConfig",
                "ontology_subject_kind": "function",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(executable_function_instance_id),
                    "semantic_source_object_id": str(function_config_id),
                    "object_kind": "function",
                    "object": {
                        "object_id": str(executable_function_instance_id),
                        "semantic_source_object_id": str(function_config_id),
                        "function_config_id": str(function_config_id),
                        "owner_semantic_key": class_semantic_key,
                        "class_config_id": str(executable_class_instance_id),
                        "owner_key": "aware_demo.default.home.Room",
                        "name": "rename",
                        "kind": "instance",
                        "function_signature": {
                            "owner_key": "aware_demo.default.home.Room",
                            "name": "rename",
                            "kind": "instance",
                        },
                        "function_membership_signature": {
                            "class_config_id": str(class_config_id),
                            "function_config_id": str(function_config_id),
                        },
                    },
                },
                "current": {
                    "semantic_key": function_semantic_key,
                    "object_kind": "function",
                    "owner_semantic_key": class_semantic_key,
                    "class_config_id": str(executable_class_instance_id),
                    "function_config_id": str(executable_function_instance_id),
                    "semantic_source_object_id": str(function_config_id),
                    "entity_id": str(executable_function_instance_id),
                    "function_name": "rename",
                    "owner_key": "aware_demo.default.home.Room",
                    "function_signature": {
                        "owner_key": "aware_demo.default.home.Room",
                        "name": "rename",
                        "kind": "instance",
                    },
                    "function_membership_signature": {
                        "class_config_id": str(class_config_id),
                        "function_config_id": str(function_config_id),
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
        "meta_ocg_function_delete_function_call_ready"
    )
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    intent = intents[0]
    assert intent["owner_class_name"] == "ClassConfig"
    assert intent["function_name"] == "remove_function_config"
    assert intent["function_ref"] == CLASS_CONFIG_REMOVE_FUNCTION_CONFIG_FUNCTION_REF
    assert intent["target_object_id"] == str(executable_class_instance_id)
    assert intent["receiver_semantic_key"] == class_semantic_key
    assert intent["expected_result_object_id"] == str(function_config_id)
    assert intent["commit_required"] is True
    assert intent["kwargs"] == {
        "name": "rename",
        "function_config_id": str(function_config_id),
    }
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }


def test_meta_provider_delta_function_invocation_create_ontology_execution_plan_ready() -> (
    None
):
    function_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room.rename"
    invocation_semantic_key = f"{function_semantic_key}/invocation:0"
    function_config_id = provider_delta_uuid("ontology-exec-function-invocation-owner")
    invocation_id = provider_delta_uuid("ontology-exec-function-invocation-object")
    target_function_config_id = provider_delta_uuid(
        "ontology-exec-function-invocation-target"
    )
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg.function_invocation.create:" f"{invocation_semantic_key}"
                ),
                "operation_family": "create",
                "provider_operation_type": ("meta_ocg.function_invocation.create"),
                "semantic_key": invocation_semantic_key,
                "semantic_subject_type": "aware_meta.FunctionConfigInvocation",
                "ontology_subject_kind": "function_invocation",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {},
                "current": {
                    "semantic_key": invocation_semantic_key,
                    "object_kind": "function_invocation",
                    "function_semantic_key": function_semantic_key,
                    "entity_id": str(invocation_id),
                    "function_config_invocation_id": str(invocation_id),
                    "function_config_id": str(function_config_id),
                    "position": 0,
                    "kind": "call",
                    "target_function_config_id": str(target_function_config_id),
                    "relationship_fingerprint": "owner",
                    "root_kind": "owner",
                    "function_invocation_signature": {
                        "function_config_id": str(function_config_id),
                        "position": 0,
                        "kind": "call",
                        "target_function_config_id": str(target_function_config_id),
                        "relationship_fingerprint": "owner",
                        "root_kind": "owner",
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
        "meta_ocg_function_invocation_create_function_call_ready"
    )
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    intent = intents[0]
    assert intent["owner_class_name"] == "FunctionConfig"
    assert intent["function_name"] == "create_invocation"
    assert intent["function_ref"] == FUNCTION_CONFIG_CREATE_INVOCATION_FUNCTION_REF
    assert intent["target_object_id"] == str(function_config_id)
    assert intent["receiver_semantic_key"] == function_semantic_key
    assert intent["result_semantic_key"] == invocation_semantic_key
    assert intent["expected_result_object_id"] == str(invocation_id)
    assert intent["kwargs"] == {
        "position": 0,
        "kind": "call",
        "target_function_config_id": str(target_function_config_id),
        "relationship_fingerprint": "owner",
        "class_config_relationship_id": None,
        "root_invocation_id": None,
        "root_kind": "owner",
        "capture_name": None,
    }
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["execution_policy"] == "ontology_function_call_only"
    assert matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }


def test_meta_provider_delta_function_invocation_create_blocks_invalid_relationship_fingerprint() -> (
    None
):
    function_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room.rename"
    function_config_id = provider_delta_uuid(
        "ontology-exec-function-invocation-owner-invalid"
    )
    target_function_config_id = provider_delta_uuid(
        "ontology-exec-function-invocation-target-invalid"
    )
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg.function_invocation.create:"
                    f"{function_semantic_key}/invocation:invalid"
                ),
                "operation_family": "create",
                "provider_operation_type": ("meta_ocg.function_invocation.create"),
                "semantic_key": f"{function_semantic_key}/invocation:invalid",
                "semantic_subject_type": "aware_meta.FunctionConfigInvocation",
                "ontology_subject_kind": "function_invocation",
                "baseline": {},
                "current": {
                    "function_semantic_key": function_semantic_key,
                    "function_config_id": str(function_config_id),
                    "position": 1,
                    "kind": "construct",
                    "target_function_config_id": str(target_function_config_id),
                    "relationship_fingerprint": "not-owner",
                },
            },
        ),
    }

    plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )

    assert plan["status"] == "ontology_execution_plan_blocked"
    assert plan["reason"] == "meta_ocg_ontology_execution_plan_blocked"
    assert plan["blockers"] == (
        "function_invocation_relationship_fingerprint_requires_relationship_id",
    )
    handler_results = cast(
        Sequence[dict[str, object]],
        plan["operation_handler_results"],
    )
    assert handler_results[0]["reason"] == (
        "meta_ocg_function_invocation_create_requires_parent_and_target"
    )
