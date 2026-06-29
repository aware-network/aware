from __future__ import annotations

from collections.abc import Sequence
from types import SimpleNamespace
from typing import cast

from aware_meta.materialization.deltas.capability_matrix import (
    BLOCKED_MISSING_ONTOLOGY_FUNCTION,
    EXECUTABLE_VIA_ONTOLOGY_FUNCTION,
    build_provider_delta_functioncall_capability_matrix,
)
from aware_meta.materialization.deltas.ontology_execution import (
    build_provider_delta_ontology_execution_plan,
)
from aware_meta.materialization.deltas.ontology_execution.handlers.attribute import (
    ATTRIBUTE_CONFIG_UPDATE_PRIMITIVE_FUNCTION_REF,
    CLASS_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF,
    FUNCTION_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF,
)
from aware_meta.materialization.deltas.ontology_execution.handlers.attribute_membership import (
    CLASS_CONFIG_ATTRIBUTE_CONFIG_UPDATE_CONFIG_FUNCTION_REF,
    FUNCTION_CONFIG_ATTRIBUTE_CONFIG_UPDATE_CONFIG_FUNCTION_REF,
)
from aware_meta.materialization.deltas.typed_operations import (
    _provider_delta_typed_operation_plan,
)
from aware_meta.materialization.semantic_function_call_resolution import (
    META_CLASS_CONFIG_CREATE_PRIMITIVE_ATTRIBUTE_FUNCTION_REF,
    META_FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_FUNCTION_REF,
)

from .fixtures import provider_delta_uuid


def test_meta_provider_delta_attribute_create_ontology_execution_plan_ready() -> None:
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    function_semantic_key = "ocg:aware_demo/node:aware_demo.functions.Sync"
    class_attribute_semantic_key = f"{class_semantic_key}/attribute:name"
    function_attribute_semantic_key = f"{function_semantic_key}/attribute:payload"
    class_config_id = provider_delta_uuid("ontology-exec-attribute-class-owner")
    function_config_id = provider_delta_uuid("ontology-exec-attribute-function-owner")
    class_attribute_id = provider_delta_uuid("ontology-exec-attribute-class-name")
    function_attribute_id = provider_delta_uuid(
        "ontology-exec-attribute-function-payload"
    )

    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 2,
        "semantic_object_anchors": (
            {
                "operation_key": (
                    f"meta_ocg_provider_delta:anchor:class:{class_semantic_key}"
                ),
                "operation_family": "anchor",
                "provider_operation_type": "meta_ocg.class.anchor",
                "semantic_key": class_semantic_key,
                "ontology_subject_kind": "class",
                "baseline": {},
                "current": {
                    "semantic_key": class_semantic_key,
                    "object_kind": "class",
                    "node_type": "class",
                    "entity_id": str(class_config_id),
                    "entity_name": "Room",
                },
            },
            {
                "operation_key": (
                    "meta_ocg_provider_delta:anchor:function:"
                    f"{function_semantic_key}"
                ),
                "operation_family": "anchor",
                "provider_operation_type": "meta_ocg.function.anchor",
                "semantic_key": function_semantic_key,
                "ontology_subject_kind": "function",
                "baseline": {},
                "current": {
                    "semantic_key": function_semantic_key,
                    "object_kind": "function",
                    "node_type": "function",
                    "entity_id": str(function_config_id),
                    "entity_name": "Sync",
                },
            },
        ),
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:create:attribute:"
                    f"{class_attribute_semantic_key}"
                ),
                "operation_family": "create",
                "provider_operation_type": "meta_ocg.attribute.create",
                "semantic_key": class_attribute_semantic_key,
                "semantic_subject_type": "aware_meta.AttributeConfig",
                "ontology_subject_kind": "attribute",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {},
                "current": {
                    "semantic_key": class_attribute_semantic_key,
                    "object_kind": "attribute",
                    "entity_id": str(class_attribute_id),
                    "owner_semantic_key": class_semantic_key,
                    "attribute_name": "name",
                    "attribute_signature": {
                        "name": "name",
                        "position": 0,
                        "description": "Human-readable room name.",
                        "is_required": True,
                        "is_public": True,
                        "type_descriptor": {
                            "kind": "primitive",
                            "primitive_base_type": "string",
                        },
                    },
                },
            },
            {
                "operation_key": (
                    "meta_ocg_provider_delta:create:attribute:"
                    f"{function_attribute_semantic_key}"
                ),
                "operation_family": "create",
                "provider_operation_type": "meta_ocg.attribute.create",
                "semantic_key": function_attribute_semantic_key,
                "semantic_subject_type": "aware_meta.AttributeConfig",
                "ontology_subject_kind": "attribute",
                "source_refs": ("aware/home/functions/sync.aware",),
                "baseline": {},
                "current": {
                    "semantic_key": function_attribute_semantic_key,
                    "object_kind": "attribute",
                    "entity_id": str(function_attribute_id),
                    "owner_semantic_key": function_semantic_key,
                    "attribute_name": "payload",
                    "attribute_signature": {
                        "name": "payload",
                        "position": 0,
                        "function_attribute_type": "input",
                        "is_identity_key": True,
                        "is_required": True,
                        "is_public": True,
                        "type_descriptor": {
                            "kind": "primitive",
                            "primitive_base_type": "string",
                        },
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
    assert plan["invocation_intent_count"] == 2
    assert plan["blockers"] == ()
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    class_intent, function_intent = intents
    assert class_intent["owner_class_name"] == "ClassConfig"
    assert class_intent["function_ref"] == (
        META_CLASS_CONFIG_CREATE_PRIMITIVE_ATTRIBUTE_FUNCTION_REF
    )
    assert class_intent["target_object_id"] == str(class_config_id)
    assert class_intent["expected_result_object_id"] == str(class_attribute_id)
    class_kwargs = cast(dict[str, object], class_intent["kwargs"])
    assert class_kwargs["name"] == "name"
    assert class_kwargs["description"] == "Human-readable room name."
    assert class_kwargs["primitive_base_type"] == "string"
    assert class_kwargs["is_required"] is True
    assert class_kwargs["position"] == 0
    assert "type" not in class_kwargs

    assert function_intent["owner_class_name"] == "FunctionConfig"
    assert function_intent["function_ref"] == (
        META_FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_FUNCTION_REF
    )
    assert function_intent["target_object_id"] == str(function_config_id)
    assert function_intent["expected_result_object_id"] == str(function_attribute_id)
    function_kwargs = cast(dict[str, object], function_intent["kwargs"])
    assert function_kwargs["name"] == "payload"
    assert function_kwargs["primitive_base_type"] == "string"
    assert function_kwargs["type"] == "input"
    assert function_kwargs["is_identity_key"] is True

    assert matrix["status"] == "functioncall_capability_matrix_ready"
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["execution_policy"] == "ontology_function_call_only"
    assert matrix["execution_allowed"] is True
    assert matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 2,
    }


def test_meta_provider_delta_attribute_update_ontology_execution_plan_ready() -> None:
    attribute_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room/attribute:name"
    )
    attribute_config_id = provider_delta_uuid("capability-baseline-attribute")
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:attribute:"
                    f"{attribute_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.attribute.update",
                "semantic_key": attribute_semantic_key,
                "semantic_subject_type": "aware_meta.AttributeConfig",
                "ontology_subject_kind": "attribute",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(attribute_config_id),
                    "object_kind": "attribute",
                },
                "current": {
                    "semantic_key": attribute_semantic_key,
                    "object_kind": "attribute",
                    "owner_semantic_key": (
                        "ocg:aware_demo/node:aware_demo.default.home.Room"
                    ),
                    "attribute_name": "name",
                    "attribute_signature": {
                        "name": "name",
                        "is_required": True,
                        "is_public": True,
                        "exclude_serialization": True,
                        "type_descriptor": {
                            "kind": "primitive",
                            "primitive_base_type": "string",
                        },
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
        "meta_ocg_attribute_update_function_call_ready"
    )
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    intent = intents[0]
    assert intent["owner_class_name"] == "AttributeConfig"
    assert intent["function_name"] == "update_primitive"
    assert intent["function_ref"] == ATTRIBUTE_CONFIG_UPDATE_PRIMITIVE_FUNCTION_REF
    assert intent["target_object_id"] == str(attribute_config_id)
    assert intent["expected_result_object_id"] == str(attribute_config_id)
    kwargs = cast(dict[str, object], intent["kwargs"])
    assert kwargs["primitive_base_type"] == "string"
    assert kwargs["is_required"] is True
    assert kwargs["exclude_serialization"] is True
    assert "name" not in kwargs
    assert "position" not in kwargs
    assert matrix["status"] == "functioncall_capability_matrix_ready"
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["execution_allowed"] is True
    assert matrix["missing_ontology_function_operation_count"] == 0
    assert matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }
    executable = cast(
        Sequence[dict[str, object]],
        matrix["capability_entries"],
    )
    assert executable[0]["capability_status"] == (EXECUTABLE_VIA_ONTOLOGY_FUNCTION)
    assert executable[0]["provider_operation_type"] == ("meta_ocg.attribute.update")
    assert executable[0]["function_refs"] == (
        ATTRIBUTE_CONFIG_UPDATE_PRIMITIVE_FUNCTION_REF,
    )


def test_meta_provider_delta_attribute_update_accepts_lane_receiver_object_id() -> None:
    attribute_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room/attribute:name"
    )
    attribute_config_id = provider_delta_uuid("capability-lane-receiver-attribute")
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:attribute:"
                    f"{attribute_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.attribute.update",
                "semantic_key": attribute_semantic_key,
                "semantic_subject_type": "aware_meta.AttributeConfig",
                "ontology_subject_kind": "attribute",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_kind": "attribute",
                },
                "current": {
                    "semantic_key": attribute_semantic_key,
                    "object_kind": "attribute",
                    "owner_semantic_key": (
                        "ocg:aware_demo/node:aware_demo.default.home.Room"
                    ),
                    "attribute_name": "name",
                    "receiver_object_id": str(attribute_config_id),
                    "semantic_apply_receiver_object_id": str(attribute_config_id),
                    "attribute_signature": {
                        "name": "name",
                        "is_required": True,
                        "type_descriptor": {
                            "kind": "primitive",
                            "primitive_base_type": "string",
                        },
                    },
                },
            },
        ),
    }

    plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )

    assert plan["status"] == "ontology_execution_plan_ready"
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    [intent] = intents
    assert intent["function_name"] == "update_primitive"
    assert intent["target_object_id"] == str(attribute_config_id)
    assert intent["expected_result_object_id"] == str(attribute_config_id)


def test_meta_provider_delta_attribute_delete_ontology_execution_plan_ready() -> None:
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    function_semantic_key = f"{class_semantic_key}.rename"
    class_attribute_semantic_key = f"{class_semantic_key}/attribute:state"
    function_attribute_semantic_key = f"{function_semantic_key}/attribute:payload"
    class_config_id = provider_delta_uuid("ontology-exec-delete-attribute-class-owner")
    function_config_id = provider_delta_uuid(
        "ontology-exec-delete-attribute-function-owner"
    )
    class_attribute_id = provider_delta_uuid(
        "ontology-exec-delete-attribute-class-state"
    )
    function_attribute_id = provider_delta_uuid(
        "ontology-exec-delete-attribute-function-payload"
    )
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 2,
        "semantic_object_anchors": (
            {
                "operation_key": (
                    f"meta_ocg_provider_delta:anchor:class:{class_semantic_key}"
                ),
                "operation_family": "anchor",
                "provider_operation_type": "meta_ocg.class.anchor",
                "semantic_key": class_semantic_key,
                "ontology_subject_kind": "class",
                "baseline": {"object_id": str(class_config_id)},
                "current": {
                    "semantic_key": class_semantic_key,
                    "object_kind": "class",
                    "node_type": "class",
                    "entity_id": str(class_config_id),
                    "entity_name": "Room",
                },
            },
            {
                "operation_key": (
                    "meta_ocg_provider_delta:anchor:function:"
                    f"{function_semantic_key}"
                ),
                "operation_family": "anchor",
                "provider_operation_type": "meta_ocg.function.anchor",
                "semantic_key": function_semantic_key,
                "ontology_subject_kind": "function",
                "baseline": {"object_id": str(function_config_id)},
                "current": {
                    "semantic_key": function_semantic_key,
                    "object_kind": "function",
                    "node_type": "function",
                    "entity_id": str(function_config_id),
                    "entity_name": "rename",
                },
            },
        ),
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:delete:attribute:"
                    f"{class_attribute_semantic_key}"
                ),
                "operation_family": "delete",
                "provider_operation_type": "meta_ocg.attribute.delete",
                "semantic_key": class_attribute_semantic_key,
                "semantic_subject_type": "aware_meta.AttributeConfig",
                "ontology_subject_kind": "attribute",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(class_attribute_id),
                    "object_kind": "attribute",
                    "object": {
                        "owner_semantic_key": class_semantic_key,
                        "attribute_name": "state",
                    },
                },
                "current": {
                    "semantic_key": class_attribute_semantic_key,
                    "object_kind": "attribute",
                    "owner_semantic_key": class_semantic_key,
                    "attribute_name": "state",
                },
            },
            {
                "operation_key": (
                    "meta_ocg_provider_delta:delete:attribute:"
                    f"{function_attribute_semantic_key}"
                ),
                "operation_family": "delete",
                "provider_operation_type": "meta_ocg.attribute.delete",
                "semantic_key": function_attribute_semantic_key,
                "semantic_subject_type": "aware_meta.AttributeConfig",
                "ontology_subject_kind": "attribute",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(function_attribute_id),
                    "object_kind": "attribute",
                    "object": {
                        "owner_semantic_key": function_semantic_key,
                        "attribute_name": "payload",
                        "function_attribute_type": "output",
                    },
                },
                "current": {
                    "semantic_key": function_attribute_semantic_key,
                    "object_kind": "attribute",
                    "owner_semantic_key": function_semantic_key,
                    "attribute_name": "payload",
                    "attribute_signature": {
                        "name": "payload",
                        "function_attribute_type": "output",
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
    assert plan["invocation_intent_count"] == 2
    handler_results = cast(
        Sequence[dict[str, object]],
        plan["operation_handler_results"],
    )
    assert {result["reason"] for result in handler_results} == {
        "meta_ocg_attribute_delete_function_call_ready",
    }
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    class_intent, function_intent = intents
    assert class_intent["owner_class_name"] == "ClassConfig"
    assert class_intent["function_name"] == "remove_attribute_config"
    assert class_intent["function_ref"] == (
        CLASS_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF
    )
    assert class_intent["target_object_id"] == str(class_config_id)
    assert class_intent["expected_result_object_id"] == str(class_attribute_id)
    class_kwargs = cast(dict[str, object], class_intent["kwargs"])
    assert class_kwargs == {
        "name": "state",
        "attribute_config_id": str(class_attribute_id),
    }

    assert function_intent["owner_class_name"] == "FunctionConfig"
    assert function_intent["function_name"] == "remove_attribute_config"
    assert function_intent["function_ref"] == (
        FUNCTION_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF
    )
    assert function_intent["target_object_id"] == str(function_config_id)
    assert function_intent["expected_result_object_id"] == str(function_attribute_id)
    function_kwargs = cast(dict[str, object], function_intent["kwargs"])
    assert function_kwargs == {
        "name": "payload",
        "type": "output",
        "attribute_config_id": str(function_attribute_id),
    }
    assert matrix["status"] == "functioncall_capability_matrix_ready"
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["execution_policy"] == "ontology_function_call_only"
    assert matrix["execution_allowed"] is True
    assert matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 2,
    }


def test_meta_provider_delta_attribute_membership_update_ontology_execution_plan_ready() -> (
    None
):
    class_attribute_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room/attribute:name"
    )
    class_membership_semantic_key = (
        f"{class_attribute_semantic_key}/membership:class_config"
    )
    function_attribute_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room.rename"
        "/attribute:input:name"
    )
    function_membership_semantic_key = (
        f"{function_attribute_semantic_key}/membership:function_config"
    )
    class_config_id = provider_delta_uuid("ontology-exec-class-attribute-class")
    class_attribute_config_id = provider_delta_uuid(
        "ontology-exec-class-attribute-attribute"
    )
    class_edge_id = provider_delta_uuid("ontology-exec-class-attribute-edge")
    function_config_id = provider_delta_uuid(
        "ontology-exec-function-attribute-function"
    )
    function_attribute_config_id = provider_delta_uuid(
        "ontology-exec-function-attribute-attribute"
    )
    function_edge_id = provider_delta_uuid("ontology-exec-function-attribute-edge")
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 2,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:attribute_membership:"
                    f"{class_membership_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": ("meta_ocg.attribute_membership.update"),
                "semantic_key": class_membership_semantic_key,
                "semantic_subject_type": ("aware_meta.ClassConfigAttributeConfig"),
                "ontology_subject_kind": "attribute_membership",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(class_edge_id),
                    "object_kind": "attribute_membership",
                    "object": {
                        "class_config_attribute_config_id": str(class_edge_id),
                        "class_config_id": str(class_config_id),
                        "attribute_config_id": str(class_attribute_config_id),
                        "attribute_membership_signature": {
                            "owner_kind": "class",
                            "class_config_id": str(class_config_id),
                            "attribute_config_id": str(class_attribute_config_id),
                            "position": 0,
                            "is_identity_key": False,
                        },
                    },
                },
                "current": {
                    "semantic_key": class_membership_semantic_key,
                    "object_kind": "attribute_membership",
                    "class_config_attribute_config_id": str(class_edge_id),
                    "class_config_id": str(class_config_id),
                    "attribute_config_id": str(class_attribute_config_id),
                    "attribute_membership_owner_kind": "class",
                    "attribute_membership_signature": {
                        "owner_kind": "class",
                        "class_config_id": str(class_config_id),
                        "attribute_config_id": str(class_attribute_config_id),
                        "position": 4,
                        "is_identity_key": True,
                    },
                },
            },
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:attribute_membership:"
                    f"{function_membership_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": ("meta_ocg.attribute_membership.update"),
                "semantic_key": function_membership_semantic_key,
                "semantic_subject_type": ("aware_meta.FunctionConfigAttributeConfig"),
                "ontology_subject_kind": "attribute_membership",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(function_edge_id),
                    "object_kind": "attribute_membership",
                    "object": {
                        "function_config_attribute_config_id": str(function_edge_id),
                        "function_config_id": str(function_config_id),
                        "attribute_config_id": str(function_attribute_config_id),
                        "attribute_membership_signature": {
                            "owner_kind": "function",
                            "function_config_id": str(function_config_id),
                            "attribute_config_id": str(function_attribute_config_id),
                            "name": "name",
                            "type": "input",
                            "position": 0,
                            "is_identity_key": False,
                            "identity_key_origin": "standalone",
                        },
                    },
                },
                "current": {
                    "semantic_key": function_membership_semantic_key,
                    "object_kind": "attribute_membership",
                    "function_config_attribute_config_id": str(function_edge_id),
                    "function_config_id": str(function_config_id),
                    "attribute_config_id": str(function_attribute_config_id),
                    "function_attribute_type": "input",
                    "attribute_membership_owner_kind": "function",
                    "attribute_membership_signature": {
                        "owner_kind": "function",
                        "function_config_id": str(function_config_id),
                        "attribute_config_id": str(function_attribute_config_id),
                        "name": "name",
                        "type": "input",
                        "position": 2,
                        "is_identity_key": True,
                        "identity_key_origin": "propagated_parent",
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
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    assert len(intents) == 2
    class_intent = intents[0]
    assert class_intent["owner_class_name"] == "ClassConfigAttributeConfig"
    assert class_intent["function_name"] == "update_config"
    assert class_intent["function_ref"] == (
        CLASS_CONFIG_ATTRIBUTE_CONFIG_UPDATE_CONFIG_FUNCTION_REF
    )
    assert class_intent["target_object_id"] == str(class_edge_id)
    assert class_intent["kwargs"] == {
        "position": 4,
        "is_identity_key": True,
    }
    function_intent = intents[1]
    assert function_intent["owner_class_name"] == "FunctionConfigAttributeConfig"
    assert function_intent["function_name"] == "update_config"
    assert function_intent["function_ref"] == (
        FUNCTION_CONFIG_ATTRIBUTE_CONFIG_UPDATE_CONFIG_FUNCTION_REF
    )
    assert function_intent["target_object_id"] == str(function_edge_id)
    assert function_intent["kwargs"] == {
        "position": 2,
        "is_identity_key": True,
        "identity_key_origin": "propagated_parent",
    }
    assert matrix["status"] == "functioncall_capability_matrix_ready"
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["execution_policy"] == "ontology_function_call_only"
    assert matrix["execution_allowed"] is True
    assert matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 2,
    }


def test_meta_provider_delta_attribute_membership_update_uses_executable_receiver() -> (
    None
):
    membership_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room"
        "/attribute:name/membership:class_config"
    )
    semantic_edge_id = provider_delta_uuid(
        "ontology-exec-class-attribute-membership-semantic-edge"
    )
    executable_edge_id = provider_delta_uuid(
        "ontology-exec-class-attribute-membership-executable-edge"
    )
    class_config_id = provider_delta_uuid(
        "ontology-exec-class-attribute-membership-class"
    )
    attribute_config_id = provider_delta_uuid(
        "ontology-exec-class-attribute-membership-attribute"
    )
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:attribute_membership:"
                    f"{membership_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.attribute_membership.update",
                "semantic_key": membership_semantic_key,
                "semantic_subject_type": "aware_meta.ClassConfigAttributeConfig",
                "ontology_subject_kind": "attribute_membership",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(semantic_edge_id),
                    "object_kind": "attribute_membership",
                    "object": {
                        "class_config_attribute_config_id": str(semantic_edge_id),
                        "class_config_id": str(class_config_id),
                        "attribute_config_id": str(attribute_config_id),
                        "attribute_membership_signature": {
                            "owner_kind": "class",
                            "class_config_id": str(class_config_id),
                            "attribute_config_id": str(attribute_config_id),
                            "position": 0,
                            "is_identity_key": False,
                        },
                    },
                },
                "current": {
                    "semantic_key": membership_semantic_key,
                    "object_kind": "attribute_membership",
                    "class_config_attribute_config_id": str(semantic_edge_id),
                    "semantic_apply_receiver_object_id": str(executable_edge_id),
                    "executable_object_id": str(executable_edge_id),
                    "class_config_id": str(class_config_id),
                    "attribute_config_id": str(attribute_config_id),
                    "attribute_membership_owner_kind": "class",
                    "attribute_membership_signature": {
                        "owner_kind": "class",
                        "class_config_id": str(class_config_id),
                        "attribute_config_id": str(attribute_config_id),
                        "position": 0,
                        "is_identity_key": True,
                    },
                },
            },
        ),
    }

    plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )

    assert plan["status"] == "ontology_execution_plan_ready"
    intent = cast(Sequence[dict[str, object]], plan["invocation_intents"])[0]
    assert intent["target_object_id"] == str(executable_edge_id)
    assert intent["expected_result_object_id"] == str(executable_edge_id)
    assert intent["semantic_key"] == membership_semantic_key
    assert intent["receiver_semantic_key"] == membership_semantic_key
    assert intent["kwargs"] == {
        "position": 0,
        "is_identity_key": True,
    }


def test_meta_provider_delta_attribute_membership_update_blocks_identity_change() -> (
    None
):
    membership_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room.rename"
        "/attribute:input:name/membership:function_config"
    )
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:attribute_membership:"
                    f"{membership_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": ("meta_ocg.attribute_membership.update"),
                "semantic_key": membership_semantic_key,
                "semantic_subject_type": ("aware_meta.FunctionConfigAttributeConfig"),
                "ontology_subject_kind": "attribute_membership",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(
                        provider_delta_uuid("ontology-exec-attribute-membership-edge")
                    ),
                    "object_kind": "attribute_membership",
                    "object": {
                        "function_config_id": str(
                            provider_delta_uuid(
                                "ontology-exec-attribute-membership-baseline-function"
                            )
                        ),
                        "attribute_config_id": str(
                            provider_delta_uuid(
                                "ontology-exec-attribute-membership-baseline-attribute"
                            )
                        ),
                        "attribute_membership_signature": {
                            "name": "name",
                            "type": "input",
                        },
                    },
                },
                "current": {
                    "function_config_id": str(
                        provider_delta_uuid(
                            "ontology-exec-attribute-membership-current-function"
                        )
                    ),
                    "attribute_config_id": str(
                        provider_delta_uuid(
                            "ontology-exec-attribute-membership-current-attribute"
                        )
                    ),
                    "attribute_membership_owner_kind": "function",
                    "attribute_membership_signature": {
                        "name": "new_name",
                        "type": "output",
                        "position": 0,
                        "is_identity_key": False,
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
        (
            "attribute_membership_identity_change_requires_replacement:"
            "function_config_id"
        ),
        (
            "attribute_membership_identity_change_requires_replacement:"
            "attribute_config_id"
        ),
        "attribute_membership_identity_change_requires_replacement:name",
        "attribute_membership_identity_change_requires_replacement:type",
        "unsupported_attribute_replacement_descriptor_kind:unknown",
    }
    handler_results = cast(
        Sequence[dict[str, object]],
        plan["operation_handler_results"],
    )
    assert handler_results[0]["reason"] == (
        "meta_ocg_attribute_membership_replacement_blocked"
    )
    assert matrix["coverage_status"] == "all_operations_blocked"
    assert matrix["capability_status_counts"] == {
        "unsupported": 1,
    }


def test_meta_provider_delta_attribute_update_marks_function_membership_identity_replacement() -> (
    None
):
    function_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room.rename"
    attribute_semantic_key = f"{function_semantic_key}/attribute:input:name"
    membership_semantic_key = f"{attribute_semantic_key}/membership:function_config"
    function_config_id = provider_delta_uuid(
        "typed-operation-function-attribute-replacement-function"
    )
    attribute_config_id = provider_delta_uuid(
        "typed-operation-function-attribute-replacement-attribute"
    )
    edge_id = provider_delta_uuid("typed-operation-function-attribute-replacement-edge")
    current_scalar_signature = {
        "name": "display_name",
        "description": "New display name.",
        "default_value": None,
        "is_primary": False,
        "is_public": True,
        "is_required": True,
        "is_unique": False,
        "is_virtual": False,
        "exclude_serialization": False,
        "type_descriptor": {
            "kind": "primitive",
            "primitive_base_type": "string",
        },
    }
    baseline_scalar_signature = {
        **current_scalar_signature,
        "name": "name",
        "description": "Name.",
    }
    typed_operation_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_ready",
            "reason": "meta_ocg_dirty_diff_ready",
            "available": True,
            "blocked": False,
            "baseline_index_compare_available": True,
            "baseline_index_compare_status": "baseline_index_compared",
            "semantic_dirty_entries": (
                {
                    "entry_key": f"dirty:attribute:{attribute_semantic_key}",
                    "dirty_operation": "attribute_update",
                    "baseline_compare_operation": "update",
                    "baseline_compare_status": "baseline_object_matched",
                    "semantic_key": attribute_semantic_key,
                    "semantic_subject_type": "aware_meta.AttributeConfig",
                    "ontology_subject_kind": "attribute",
                    "source_refs": ("aware/home/room.aware",),
                    "baseline_object_id": str(attribute_config_id),
                    "baseline_object_kind": "attribute",
                    "entity_id": str(attribute_config_id),
                    "entity_name": "display_name",
                    "parent_semantic_key": function_semantic_key,
                    "attribute_name": "display_name",
                    "function_config_id": str(function_config_id),
                    "function_config_attribute_config_id": str(edge_id),
                    "attribute_config_id": str(attribute_config_id),
                    "function_attribute_type": "output",
                    "attribute_membership_semantic_key": (membership_semantic_key),
                    "attribute_membership_owner_kind": "function",
                    "attribute_signature": current_scalar_signature,
                    "attribute_membership_signature": {
                        "owner_kind": "function",
                        "function_config_id": str(function_config_id),
                        "attribute_config_id": str(attribute_config_id),
                        "name": "display_name",
                        "type": "output",
                        "position": 1,
                        "is_identity_key": False,
                        "identity_key_origin": "standalone",
                    },
                    "baseline_object": {
                        "object_id": str(attribute_config_id),
                        "object_kind": "attribute",
                        "function_config_attribute_config_id": str(edge_id),
                        "function_config_id": str(function_config_id),
                        "attribute_config_id": str(attribute_config_id),
                        "function_attribute_type": "input",
                        "attribute_signature": baseline_scalar_signature,
                        "attribute_membership_signature": {
                            "owner_kind": "function",
                            "function_config_id": str(function_config_id),
                            "attribute_config_id": str(attribute_config_id),
                            "name": "name",
                            "type": "input",
                            "position": 1,
                            "is_identity_key": False,
                            "identity_key_origin": "standalone",
                        },
                    },
                    "payload": {
                        "entity_id": str(attribute_config_id),
                        "attribute_signature": current_scalar_signature,
                        "attribute_membership_signature": {
                            "owner_kind": "function",
                            "function_config_id": str(function_config_id),
                            "attribute_config_id": str(attribute_config_id),
                            "name": "display_name",
                            "type": "output",
                            "position": 1,
                            "is_identity_key": False,
                            "identity_key_origin": "standalone",
                        },
                    },
                },
            ),
        },
        provider_delta_head_move_plan={
            "status": "head_move_plan_ready",
            "reason": "workspace_provider_delta_head_move_plan_ready",
            "blocked": False,
        },
        semantic_change_payloads=(),
        function_call_plans=(),
    )

    assert typed_operation_plan["status"] == "typed_operation_plan_ready"
    assert typed_operation_plan["typed_operation_count"] == 1
    assert typed_operation_plan["operation_type_counts"] == {
        "meta_ocg.attribute_membership.update": 1,
    }
    operations = cast(
        Sequence[dict[str, object]],
        typed_operation_plan["typed_operations"],
    )
    membership_operation = next(
        operation
        for operation in operations
        if operation["ontology_subject_kind"] == "attribute_membership"
    )
    current = cast(dict[str, object], membership_operation["current"])
    assert current["attribute_membership_replacement_required"] is True
    assert current["attribute_membership_changed_fields"] == ("name", "type")
    assert current["attribute_membership_mutable_update_fields"] == ()
    assert current["attribute_membership_identity_replacement_fields"] == (
        "name",
        "type",
    )

    execution_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )
    matrix = build_provider_delta_functioncall_capability_matrix(
        provider_delta_typed_operation_plan=typed_operation_plan,
        provider_delta_ontology_execution_plan=execution_plan,
    )

    assert execution_plan["status"] == "ontology_execution_plan_ready"
    assert execution_plan["blockers"] == ()
    assert execution_plan["invocation_intent_count"] == 2
    handler_results = cast(
        Sequence[dict[str, object]],
        execution_plan["operation_handler_results"],
    )
    membership_result = next(
        result
        for result in handler_results
        if result["semantic_key"] == membership_semantic_key
    )
    assert membership_result["reason"] == (
        "meta_ocg_attribute_membership_replacement_function_call_ready"
    )
    intents = cast(Sequence[dict[str, object]], execution_plan["invocation_intents"])
    assert intents[0]["function_ref"] == (
        FUNCTION_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF
    )
    assert intents[0]["function_name"] == "remove_attribute_config"
    assert intents[0]["target_object_id"] == str(function_config_id)
    assert intents[0]["kwargs"] == {
        "name": "name",
        "type": "input",
        "attribute_config_id": str(attribute_config_id),
    }
    assert intents[1]["function_ref"] == (
        META_FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_FUNCTION_REF
    )
    assert intents[1]["function_name"] == "add_primitive_attribute_config"
    assert intents[1]["target_object_id"] == str(function_config_id)
    assert intents[1]["expected_result_object_id"] == str(attribute_config_id)
    assert intents[1]["kwargs"] == {
        "name": "display_name",
        "description": "New display name.",
        "default_value": None,
        "is_primary": False,
        "is_public": True,
        "is_required": True,
        "is_unique": False,
        "is_virtual": False,
        "position": 1,
        "type": "output",
        "is_identity_key": False,
        "primitive_base_type": "string",
    }
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }


def test_meta_provider_delta_class_attribute_membership_update_plans_identity_replacement() -> (
    None
):
    attribute_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room/attribute:name"
    )
    membership_semantic_key = f"{attribute_semantic_key}/membership:class_config"
    baseline_attribute_config_id = provider_delta_uuid(
        "ontology-exec-class-attribute-replacement-baseline-attribute"
    )
    current_attribute_config_id = provider_delta_uuid(
        "ontology-exec-class-attribute-replacement-current-attribute"
    )
    class_config_id = provider_delta_uuid(
        "ontology-exec-class-attribute-replacement-class"
    )
    edge_id = provider_delta_uuid("ontology-exec-class-attribute-replacement-edge")
    baseline_attribute_signature = {
        "name": "name",
        "description": "Room name.",
        "default_value": None,
        "is_primary": False,
        "is_public": True,
        "is_required": True,
        "is_unique": False,
        "is_virtual": False,
        "type_descriptor": {
            "kind": "primitive",
            "primitive_base_type": "string",
        },
    }
    current_attribute_signature = {
        **baseline_attribute_signature,
        "description": "Display name.",
    }
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:attribute_membership:"
                    f"{membership_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": ("meta_ocg.attribute_membership.update"),
                "semantic_key": membership_semantic_key,
                "semantic_subject_type": ("aware_meta.ClassConfigAttributeConfig"),
                "ontology_subject_kind": "attribute_membership",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(edge_id),
                    "object_kind": "attribute_membership",
                    "object": {
                        "class_config_attribute_config_id": str(edge_id),
                        "class_config_id": str(class_config_id),
                        "attribute_config_id": str(baseline_attribute_config_id),
                        "attribute_name": "name",
                        "attribute_signature": baseline_attribute_signature,
                    },
                },
                "current": {
                    "class_config_attribute_config_id": str(edge_id),
                    "class_config_id": str(class_config_id),
                    "attribute_config_id": str(current_attribute_config_id),
                    "attribute_name": "name",
                    "attribute_membership_owner_kind": "class",
                    "payload": {
                        "attribute_signature": current_attribute_signature,
                    },
                    "attribute_membership_signature": {
                        "owner_kind": "class",
                        "class_config_id": str(class_config_id),
                        "attribute_config_id": str(current_attribute_config_id),
                        "position": 0,
                        "is_identity_key": True,
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
    assert plan["invocation_intent_count"] == 2
    handler_results = cast(
        Sequence[dict[str, object]],
        plan["operation_handler_results"],
    )
    assert handler_results[0]["reason"] == (
        "meta_ocg_attribute_membership_replacement_function_call_ready"
    )
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    assert intents[0]["function_ref"] == (
        CLASS_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF
    )
    assert intents[0]["function_name"] == "remove_attribute_config"
    assert intents[0]["target_object_id"] == str(class_config_id)
    assert intents[0]["kwargs"] == {
        "name": "name",
        "attribute_config_id": str(baseline_attribute_config_id),
    }
    assert intents[1]["function_ref"] == (
        META_CLASS_CONFIG_CREATE_PRIMITIVE_ATTRIBUTE_FUNCTION_REF
    )
    assert intents[1]["function_name"] == "create_primitive_attribute_config"
    assert intents[1]["target_object_id"] == str(class_config_id)
    assert intents[1]["expected_result_object_id"] == str(current_attribute_config_id)
    assert intents[1]["kwargs"] == {
        "name": "name",
        "description": "Display name.",
        "default_value": None,
        "is_primary": False,
        "is_public": True,
        "is_required": True,
        "is_unique": False,
        "is_virtual": False,
        "position": 0,
        "primitive_base_type": "string",
    }
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }


def test_meta_provider_delta_attribute_replacement_blocks_unsupported_collection_descriptor() -> (
    None
):
    attribute_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room/attribute:devices"
    )
    membership_semantic_key = f"{attribute_semantic_key}/membership:class_config"
    baseline_attribute_config_id = provider_delta_uuid(
        "ontology-exec-attribute-replacement-collection-baseline-attribute"
    )
    current_attribute_config_id = provider_delta_uuid(
        "ontology-exec-attribute-replacement-collection-current-attribute"
    )
    class_config_id = provider_delta_uuid(
        "ontology-exec-attribute-replacement-collection-class"
    )
    edge_id = provider_delta_uuid("ontology-exec-attribute-replacement-collection-edge")
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:attribute_membership:"
                    f"{membership_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": ("meta_ocg.attribute_membership.update"),
                "semantic_key": membership_semantic_key,
                "semantic_subject_type": ("aware_meta.ClassConfigAttributeConfig"),
                "ontology_subject_kind": "attribute_membership",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(edge_id),
                    "object_kind": "attribute_membership",
                    "object": {
                        "class_config_attribute_config_id": str(edge_id),
                        "class_config_id": str(class_config_id),
                        "attribute_config_id": str(baseline_attribute_config_id),
                        "attribute_name": "devices",
                        "attribute_signature": {
                            "name": "devices",
                            "type_descriptor": {
                                "kind": "primitive",
                                "primitive_base_type": "string",
                            },
                        },
                    },
                },
                "current": {
                    "class_config_attribute_config_id": str(edge_id),
                    "class_config_id": str(class_config_id),
                    "attribute_config_id": str(current_attribute_config_id),
                    "attribute_name": "devices",
                    "attribute_membership_owner_kind": "class",
                    "payload": {
                        "attribute_signature": {
                            "name": "devices",
                            "type_descriptor": {"kind": "collection"},
                        },
                    },
                    "attribute_membership_signature": {
                        "owner_kind": "class",
                        "class_config_id": str(class_config_id),
                        "attribute_config_id": str(current_attribute_config_id),
                    },
                },
            },
        ),
    }

    plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )

    assert plan["status"] == "ontology_execution_plan_blocked"
    assert set(cast(Sequence[str], plan["blockers"])) == {
        (
            "attribute_membership_identity_change_requires_replacement:"
            "attribute_config_id"
        ),
        "attribute_replacement_collection_ontology_function_missing",
    }
    handler_results = cast(
        Sequence[dict[str, object]],
        plan["operation_handler_results"],
    )
    assert handler_results[0]["reason"] == (
        "meta_ocg_attribute_membership_replacement_blocked"
    )


def test_meta_provider_delta_collection_attribute_update_stays_blocked() -> None:
    attribute_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room/attribute:doors"
    )
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:attribute:"
                    f"{attribute_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.attribute.update",
                "semantic_key": attribute_semantic_key,
                "semantic_subject_type": "aware_meta.AttributeConfig",
                "ontology_subject_kind": "attribute",
                "baseline": {
                    "object_id": str(
                        provider_delta_uuid("capability-baseline-collection-attribute")
                    ),
                    "object_kind": "attribute",
                },
                "current": {
                    "semantic_key": attribute_semantic_key,
                    "object_kind": "attribute",
                    "attribute_name": "doors",
                    "attribute_signature": {
                        "name": "doors",
                        "type_descriptor": {
                            "kind": "collection",
                            "collection_kind": "list",
                            "child_links": (),
                        },
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
    assert plan["blockers"] == (
        "attribute_collection_update_ontology_function_missing",
    )
    handler_results = cast(
        Sequence[dict[str, object]],
        plan["operation_handler_results"],
    )
    assert handler_results[0]["reason"] == (
        "meta_ocg_attribute_collection_update_requires_ontology_function"
    )
    assert matrix["coverage_status"] == "all_operations_blocked"
    assert matrix["missing_ontology_function_operation_count"] == 1
    assert matrix["capability_status_counts"] == {
        BLOCKED_MISSING_ONTOLOGY_FUNCTION: 1,
    }


def test_meta_provider_delta_collection_attribute_create_stays_blocked() -> None:
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Channel"
    attribute_semantic_key = f"{class_semantic_key}/attribute:remote_control"
    class_config_id = provider_delta_uuid(
        "ontology-exec-collection-attribute-create-class"
    )
    attribute_config_id = provider_delta_uuid(
        "ontology-exec-collection-attribute-create"
    )
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "semantic_object_anchors": (
            {
                "operation_key": (
                    f"meta_ocg_provider_delta:anchor:class:{class_semantic_key}"
                ),
                "operation_family": "anchor",
                "provider_operation_type": "meta_ocg.class.anchor",
                "semantic_key": class_semantic_key,
                "ontology_subject_kind": "class",
                "baseline": {"object_id": str(class_config_id)},
                "current": {
                    "semantic_key": class_semantic_key,
                    "object_kind": "class",
                    "node_type": "class",
                    "entity_id": str(class_config_id),
                    "entity_name": "Channel",
                },
            },
        ),
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:create:attribute:"
                    f"{attribute_semantic_key}"
                ),
                "operation_family": "create",
                "provider_operation_type": "meta_ocg.attribute.create",
                "semantic_key": attribute_semantic_key,
                "semantic_subject_type": "aware_meta.AttributeConfig",
                "ontology_subject_kind": "attribute",
                "baseline": {},
                "current": {
                    "semantic_key": attribute_semantic_key,
                    "object_kind": "attribute",
                    "entity_id": str(attribute_config_id),
                    "owner_semantic_key": class_semantic_key,
                    "attribute_name": "remote_control",
                    "attribute_signature": {
                        "name": "remote_control",
                        "type_descriptor": {
                            "kind": "collection",
                            "collection_kind": "list",
                            "child_links": (),
                        },
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
    assert plan["blockers"] == ("attribute_collection_ontology_function_missing",)
    handler_results = cast(
        Sequence[dict[str, object]],
        plan["operation_handler_results"],
    )
    assert handler_results[0]["reason"] == (
        "meta_ocg_attribute_collection_create_requires_ontology_function"
    )
    assert matrix["coverage_status"] == "all_operations_blocked"
    assert matrix["missing_ontology_function_operation_count"] == 1
    assert matrix["capability_status_counts"] == {
        BLOCKED_MISSING_ONTOLOGY_FUNCTION: 1,
    }
