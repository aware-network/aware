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
from aware_meta.class_.config.relationship.deltas.ontology_execution import (
    CLASS_CONFIG_CREATE_RELATIONSHIP_FUNCTION_REF,
    CLASS_CONFIG_RELATIONSHIP_UPDATE_CONFIG_FUNCTION_REF,
    CLASS_CONFIG_REMOVE_RELATIONSHIP_CONFIG_FUNCTION_REF,
)

from .fixtures import provider_delta_uuid


def test_meta_provider_delta_relationship_create_ontology_execution_plan_ready() -> (
    None
):
    source_class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    relationship_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room:room_devices:"
        "one_to_many:aware_demo.default.home.Device"
    )
    source_class_config_id = provider_delta_uuid(
        "ontology-exec-relationship-source-class"
    )
    target_class_config_id = provider_delta_uuid(
        "ontology-exec-relationship-target-class"
    )
    relationship_config_id = provider_delta_uuid("ontology-exec-create-relationship")
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "semantic_object_anchors": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:anchor:class:"
                    f"{source_class_semantic_key}"
                ),
                "operation_family": "anchor",
                "provider_operation_type": "meta_ocg.class.anchor",
                "semantic_key": source_class_semantic_key,
                "ontology_subject_kind": "class",
                "baseline": {"object_id": str(source_class_config_id)},
                "current": {
                    "semantic_key": source_class_semantic_key,
                    "object_kind": "class",
                    "node_type": "class",
                    "entity_id": str(source_class_config_id),
                    "entity_name": "Room",
                },
            },
        ),
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:create:relationship:"
                    f"{relationship_semantic_key}"
                ),
                "operation_family": "create",
                "provider_operation_type": "meta_ocg.relationship.create",
                "semantic_key": relationship_semantic_key,
                "semantic_subject_type": "aware_meta.ClassConfigRelationship",
                "ontology_subject_kind": "relationship",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {},
                "current": {
                    "semantic_key": relationship_semantic_key,
                    "object_kind": "relationship",
                    "entity_id": str(relationship_config_id),
                    "relationship_key": "room_devices",
                    "relationship_type": "one_to_many",
                    "relationship_signature": {
                        "target_class_config_id": str(target_class_config_id),
                        "identity_rail": "containment",
                        "forward_required": True,
                        "forward_loading_strategy": "eager",
                        "reverse_loading_strategy": "lazy",
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
        "meta_ocg_relationship_create_function_call_ready"
    )
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    intent = intents[0]
    assert intent["owner_class_name"] == "ClassConfig"
    assert intent["function_name"] == "create_relationship"
    assert intent["function_ref"] == CLASS_CONFIG_CREATE_RELATIONSHIP_FUNCTION_REF
    assert intent["target_object_id"] == str(source_class_config_id)
    assert intent["receiver_semantic_key"] == source_class_semantic_key
    assert intent["expected_result_object_id"] == str(relationship_config_id)
    kwargs = cast(dict[str, object], intent["kwargs"])
    assert kwargs == {
        "target_class_config_id": str(target_class_config_id),
        "relationship_key": "room_devices",
        "relationship_type": "one_to_many",
        "identity_rail": "containment",
        "forward_required": True,
        "forward_loading_strategy": "eager",
        "reverse_loading_strategy": "lazy",
        "reified_from_relationship_id": None,
        "reified_role": None,
    }
    assert matrix["status"] == "functioncall_capability_matrix_ready"
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["execution_policy"] == "ontology_function_call_only"
    assert matrix["execution_allowed"] is True
    assert matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }


def test_meta_provider_delta_relationship_delete_ontology_execution_plan_ready() -> (
    None
):
    source_class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    relationship_semantic_key = f"{source_class_semantic_key}/relationship:room_devices"
    source_class_config_id = provider_delta_uuid(
        "ontology-exec-delete-relationship-source"
    )
    relationship_config_id = provider_delta_uuid("ontology-exec-delete-relationship")
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "semantic_object_anchors": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:anchor:class:"
                    f"{source_class_semantic_key}"
                ),
                "operation_family": "anchor",
                "provider_operation_type": "meta_ocg.class.anchor",
                "semantic_key": source_class_semantic_key,
                "ontology_subject_kind": "class",
                "baseline": {"object_id": str(source_class_config_id)},
                "current": {
                    "semantic_key": source_class_semantic_key,
                    "object_kind": "class",
                    "node_type": "class",
                    "entity_id": str(source_class_config_id),
                    "entity_name": "Room",
                },
            },
        ),
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:delete:relationship:"
                    f"{relationship_semantic_key}"
                ),
                "operation_family": "delete",
                "provider_operation_type": "meta_ocg.relationship.delete",
                "semantic_key": relationship_semantic_key,
                "semantic_subject_type": "aware_meta.ClassConfigRelationship",
                "ontology_subject_kind": "relationship",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(relationship_config_id),
                    "object_kind": "relationship",
                    "object": {
                        "relationship_key": "room_devices",
                    },
                },
                "current": {},
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
        "meta_ocg_relationship_delete_function_call_ready"
    )
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    intent = intents[0]
    assert intent["owner_class_name"] == "ClassConfig"
    assert intent["function_name"] == "remove_relationship_config"
    assert intent["function_ref"] == (
        CLASS_CONFIG_REMOVE_RELATIONSHIP_CONFIG_FUNCTION_REF
    )
    assert intent["target_object_id"] == str(source_class_config_id)
    assert intent["receiver_semantic_key"] == source_class_semantic_key
    assert intent["expected_result_object_id"] == str(relationship_config_id)
    assert intent["kwargs"] == {
        "relationship_key": "room_devices",
        "relationship_config_id": str(relationship_config_id),
    }
    assert matrix["status"] == "functioncall_capability_matrix_ready"
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["execution_policy"] == "ontology_function_call_only"
    assert matrix["execution_allowed"] is True
    assert matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }


def test_meta_provider_delta_relationship_update_ontology_execution_plan_ready() -> (
    None
):
    relationship_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room:room_devices:"
        "one_to_many:aware_demo.default.home.Device"
    )
    relationship_config_id = provider_delta_uuid("ontology-exec-update-relationship")
    relationship_node_id = provider_delta_uuid("ontology-exec-update-relationship-node")
    target_class_config_id = provider_delta_uuid("ontology-exec-update-target-class")
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:relationship:"
                    f"{relationship_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.relationship.update",
                "semantic_key": relationship_semantic_key,
                "semantic_subject_type": "aware_meta.ClassConfigRelationship",
                "ontology_subject_kind": "relationship",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(relationship_node_id),
                    "object_kind": "relationship",
                    "object": {
                        "entity_id": str(relationship_config_id),
                        "object_id": str(relationship_node_id),
                        "relationship_key": "room_devices",
                        "relationship_signature": {
                            "target_class_config_id": str(target_class_config_id),
                        },
                    },
                },
                "current": {
                    "relationship_key": "room_devices",
                    "relationship_signature": {
                        "target_class_config_id": str(target_class_config_id),
                        "relationship_type": "one_to_one",
                        "identity_rail": "reference",
                        "forward_required": True,
                        "forward_loading_strategy": "eager",
                        "reverse_loading_strategy": "lazy",
                        "reified_role": "source_to_association",
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
        "meta_ocg_relationship_update_function_call_ready"
    )
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    intent = intents[0]
    assert intent["owner_class_name"] == "ClassConfigRelationship"
    assert intent["function_name"] == "update_config"
    assert intent["function_ref"] == (
        CLASS_CONFIG_RELATIONSHIP_UPDATE_CONFIG_FUNCTION_REF
    )
    assert intent["target_object_id"] == str(relationship_config_id)
    assert intent["receiver_semantic_key"] == relationship_semantic_key
    assert intent["expected_result_object_id"] == str(relationship_config_id)
    assert intent["kwargs"] == {
        "relationship_type": "one_to_one",
        "identity_rail": "reference",
        "forward_required": True,
        "forward_loading_strategy": "eager",
        "reverse_loading_strategy": "lazy",
        "reified_from_relationship_id": None,
        "reified_role": "source_to_association",
    }
    assert matrix["status"] == "functioncall_capability_matrix_ready"
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["execution_policy"] == "ontology_function_call_only"
    assert matrix["execution_allowed"] is True
    assert matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }


def test_meta_provider_delta_relationship_update_blocks_identity_change() -> None:
    relationship_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room:room_devices:"
        "one_to_many:aware_demo.default.home.Device"
    )
    baseline_target_class_config_id = provider_delta_uuid(
        "ontology-exec-update-baseline-target-class"
    )
    current_target_class_config_id = provider_delta_uuid(
        "ontology-exec-update-current-target-class"
    )
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:relationship:"
                    f"{relationship_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.relationship.update",
                "semantic_key": relationship_semantic_key,
                "semantic_subject_type": "aware_meta.ClassConfigRelationship",
                "ontology_subject_kind": "relationship",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(
                        provider_delta_uuid(
                            "ontology-exec-update-identity-relationship"
                        )
                    ),
                    "object_kind": "relationship",
                    "object": {
                        "relationship_key": "room_devices",
                        "relationship_signature": {
                            "target_class_config_id": (
                                str(baseline_target_class_config_id)
                            ),
                        },
                    },
                },
                "current": {
                    "relationship_key": "room_doors",
                    "relationship_type": "one_to_many",
                    "relationship_signature": {
                        "target_class_config_id": (str(current_target_class_config_id)),
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
        "relationship_identity_change_requires_replacement:relationship_key",
        ("relationship_identity_change_requires_replacement:" "target_class_config_id"),
    }
    handler_results = cast(
        Sequence[dict[str, object]],
        plan["operation_handler_results"],
    )
    assert handler_results[0]["reason"] == (
        "meta_ocg_relationship_update_requires_existing_relationship"
    )
    assert matrix["coverage_status"] == "all_operations_blocked"
    assert matrix["capability_status_counts"] == {
        "unsupported": 1,
    }
