from __future__ import annotations

from collections.abc import Callable, Sequence
from types import SimpleNamespace
from typing import cast

from aware_meta.materialization.deltas.capability_matrix import (
    EXECUTABLE_VIA_ONTOLOGY_FUNCTION,
    build_provider_delta_functioncall_capability_matrix,
)
from aware_meta.materialization.deltas.ontology_execution import (
    build_provider_delta_ontology_execution_plan as _build_provider_delta_ontology_execution_plan,
)
from aware_meta.function.impl.deltas.ontology_execution import (
    FUNCTION_IMPL_CREATE_INSTRUCTION_REF,
    FUNCTION_IMPL_INSTRUCTION_ATTACH_SET_REF,
    FUNCTION_IMPL_INSTRUCTION_CREATE_VALUE_SOURCE_REF,
    FUNCTION_IMPL_INSTRUCTION_SET_UPDATE_ASSIGNMENT_REF,
    FUNCTION_IMPL_REMOVE_INSTRUCTION_REF,
    FUNCTION_IMPL_VALUE_SOURCE_UPDATE_FUNCTION_INPUT_REF,
)
from aware_meta.function.impl.deltas.typed_operations import (
    normalize_function_impl_body_source_meaning_provider_delta_operation,
)
from aware_meta_ontology.stable_ids import stable_function_impl_instruction_id

from .fixtures import provider_delta_uuid


build_provider_delta_ontology_execution_plan = cast(
    Callable[..., dict[str, object]],
    _build_provider_delta_ontology_execution_plan,
)


def test_meta_provider_delta_function_impl_normalization_splits_receiver_and_source_ids() -> (
    None
):
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
    function_semantic_key = f"{class_semantic_key}.rename"
    function_impl_semantic_key = f"{function_semantic_key}/function_impl:default"
    receiver_function_impl_id = provider_delta_uuid(
        "ontology-exec-function-impl-oig-receiver"
    )
    source_function_impl_id = provider_delta_uuid(
        "ontology-exec-function-impl-semantic-source"
    )
    target_edge_id = provider_delta_uuid("ontology-exec-source-split-target-edge")
    source_input_id = provider_delta_uuid("ontology-exec-source-split-source-input")
    expected_instruction_id = stable_function_impl_instruction_id(
        function_impl_id=source_function_impl_id,
        type="set",
        sequence=0,
    )
    receiver_derived_instruction_id = stable_function_impl_instruction_id(
        function_impl_id=receiver_function_impl_id,
        type="set",
        sequence=0,
    )

    normalization = normalize_function_impl_body_source_meaning_provider_delta_operation(
        operation={
            "operation_key": "op:function_impl:source-split",
            "semantic_key": function_impl_semantic_key,
            "source_refs": ("aware/home/tv_channel.aware",),
            "before_payload": {
                "class_name": "TvChannel",
                "function_name": "rename",
                "function_impl_key": "default",
                "function_impl_signature": {
                    "instruction_count": 0,
                    "instruction_summaries": (),
                    "instructions": (),
                },
            },
            "after_payload": {
                "class_name": "TvChannel",
                "function_name": "rename",
                "function_impl_key": "default",
                "function_impl_signature": {
                    "instruction_count": 1,
                    "instruction_summaries": ("set name = display_name",),
                    "instructions": (
                        {
                            "type": "set",
                            "sequence": 0,
                            "set": {
                                "target_attribute_name": "name",
                                "target_class_config_attribute_config_id": (
                                    str(target_edge_id)
                                ),
                                "value_source": {
                                    "key": "display_name",
                                    "kind": "function_input_ref",
                                    "source_function_config_attribute_config_id": (
                                        str(source_input_id)
                                    ),
                                    "source_function_input_name": "display_name",
                                },
                            },
                        },
                    ),
                },
            },
        },
        function_impl_object_id=str(receiver_function_impl_id),
        function_impl_source_object_id=str(source_function_impl_id),
    )

    assert normalization.ready is True
    payload = normalization.evidence_payload()
    typed_operation = cast(
        dict[str, object],
        payload["provider_delta_typed_operation"],
    )
    current = cast(dict[str, object], typed_operation["current"])
    assert current["entity_id"] == str(receiver_function_impl_id)
    assert current["function_impl_id"] == str(source_function_impl_id)
    assert current["semantic_apply_receiver_object_id"] == (
        str(receiver_function_impl_id)
    )
    signature = cast(dict[str, object], current["function_impl_signature"])
    instructions = cast(Sequence[dict[str, object]], signature["instructions"])
    assert instructions[0]["function_impl_instruction_id"] == (
        str(expected_instruction_id)
    )
    assert instructions[0]["function_impl_instruction_id"] != (
        str(receiver_derived_instruction_id)
    )

    plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(
            context={"aware_meta.graph_runtime_context": object()},
        ),
        provider_delta_typed_operation_plan=payload[
            "provider_delta_typed_operation_plan"
        ],
    )

    assert plan["status"] == "ontology_execution_plan_ready"
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    assert intents[0]["function_ref"] == FUNCTION_IMPL_CREATE_INSTRUCTION_REF
    assert intents[0]["target_object_id"] == str(receiver_function_impl_id)
    assert intents[0]["expected_result_object_id"] == str(expected_instruction_id)
    assert intents[1]["target_object_id"] == str(expected_instruction_id)


def test_meta_provider_delta_function_impl_body_resolution_uses_source_edge_ids() -> (
    None
):
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
    function_semantic_key = f"{class_semantic_key}.rename"
    function_impl_semantic_key = f"{function_semantic_key}/function_impl:default"
    receiver_function_impl_id = provider_delta_uuid(
        "ontology-exec-function-impl-edge-receiver"
    )
    source_function_impl_id = provider_delta_uuid(
        "ontology-exec-function-impl-edge-source"
    )
    target_edge_receiver_id = provider_delta_uuid(
        "ontology-exec-function-impl-target-edge-receiver"
    )
    target_edge_source_id = provider_delta_uuid(
        "ontology-exec-function-impl-target-edge-source"
    )
    source_input_receiver_id = provider_delta_uuid(
        "ontology-exec-function-impl-input-edge-receiver"
    )
    source_input_source_id = provider_delta_uuid(
        "ontology-exec-function-impl-input-edge-source"
    )

    normalization = normalize_function_impl_body_source_meaning_provider_delta_operation(
        operation={
            "operation_key": "op:function_impl:source-edge-split",
            "semantic_key": function_impl_semantic_key,
            "source_refs": ("aware/home/tv_channel.aware",),
            "before_payload": {
                "class_name": "TvChannel",
                "function_name": "rename",
                "function_impl_key": "default",
                "body_text": None,
            },
            "after_payload": {
                "class_name": "TvChannel",
                "function_name": "rename",
                "function_impl_key": "default",
                "body_text": "{\n    set name = display_name\n}\n",
            },
        },
        function_impl_object_id=str(receiver_function_impl_id),
        function_impl_source_object_id=str(source_function_impl_id),
        current_semantic_object_ids={
            "meta.class_attribute_edge:TvChannel.name": str(
                target_edge_receiver_id
            ),
            "meta.function_input_edge:TvChannel.rename.display_name": str(
                source_input_receiver_id
            ),
        },
        current_semantic_source_object_ids={
            "meta.class_attribute_edge:TvChannel.name": str(target_edge_source_id),
            "meta.function_input_edge:TvChannel.rename.display_name": str(
                source_input_source_id
            ),
        },
    )

    assert normalization.ready is True
    payload = normalization.evidence_payload()
    typed_operation = cast(
        dict[str, object],
        payload["provider_delta_typed_operation"],
    )
    current = cast(dict[str, object], typed_operation["current"])
    signature = cast(dict[str, object], current["function_impl_signature"])
    instructions = cast(Sequence[dict[str, object]], signature["instructions"])
    set_payload = cast(dict[str, object], instructions[0]["set"])
    assert set_payload["target_class_config_attribute_config_id"] == (
        str(target_edge_source_id)
    )
    value_source = cast(dict[str, object], set_payload["value_source"])
    assert value_source["source_function_config_attribute_config_id"] == (
        str(source_input_source_id)
    )
    assert value_source["source_function_config_attribute_config_id"] != (
        str(source_input_receiver_id)
    )


def test_meta_provider_delta_function_impl_ontology_execution_plan_ready() -> None:
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
    function_semantic_key = f"{class_semantic_key}.rename"
    function_impl_semantic_key = f"{function_semantic_key}/function_impl:default"
    function_impl_id = provider_delta_uuid("ontology-exec-function-impl")
    current_function_impl_id = provider_delta_uuid(
        "ontology-exec-current-function-impl"
    )
    target_edge_id = provider_delta_uuid("ontology-exec-target-edge")
    source_input_id = provider_delta_uuid("ontology-exec-source-input")

    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:function_impl:"
                    f"{function_impl_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.function_impl.update",
                "semantic_key": function_impl_semantic_key,
                "semantic_subject_type": "aware_meta.FunctionImpl",
                "ontology_subject_kind": "function_impl",
                "source_refs": ("aware/home/tv_channel.aware",),
                "baseline": {
                    "object_id": str(function_impl_id),
                    "object": {
                        "function_impl_signature": {
                            "instruction_count": 0,
                            "instruction_summaries": (),
                            "instructions": (),
                        },
                    },
                },
                "current": {
                    "semantic_key": function_impl_semantic_key,
                    "object_kind": "function_impl",
                    "entity_id": str(current_function_impl_id),
                    "function_semantic_key": function_semantic_key,
                    "function_name": "rename",
                    "function_impl_key": "default",
                    "function_impl_kind": "instruction_body",
                    "function_impl_signature": {
                        "instruction_count": 1,
                        "instruction_summaries": ("set name = display_name",),
                        "instructions": (
                            {
                                "type": "set",
                                "sequence": 0,
                                "set": {
                                    "target_attribute_name": "name",
                                    "target_class_config_attribute_config_id": (
                                        str(target_edge_id)
                                    ),
                                    "value_source": {
                                        "key": "display_name",
                                        "kind": "function_input",
                                        "source_function_config_attribute_config_id": (
                                            str(source_input_id)
                                        ),
                                        "source_function_input_name": ("display_name"),
                                    },
                                },
                            },
                        ),
                    },
                },
            },
        ),
    }
    plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(
            context={"aware_meta.graph_runtime_context": object()},
        ),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )

    assert plan["status"] == "ontology_execution_plan_ready"
    assert plan["reason"] == "meta_ocg_ontology_execution_plan_ready"
    assert plan["operation_handler_result_count"] == 1
    assert plan["invocation_intent_count"] == 3
    assert plan["blockers"] == ()
    runtime_preflight = cast(
        dict[str, object],
        plan["invocation_runtime_preflight"],
    )
    assert runtime_preflight["graph_runtime_context_available"] is True
    assert runtime_preflight["runtime_available"] is False
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    assert [intent["invocation_mode"] for intent in intents] == [
        "instance",
        "instance",
        "instance",
    ]
    assert [intent["function_ref"] for intent in intents] == [
        FUNCTION_IMPL_CREATE_INSTRUCTION_REF,
        FUNCTION_IMPL_INSTRUCTION_CREATE_VALUE_SOURCE_REF,
        FUNCTION_IMPL_INSTRUCTION_ATTACH_SET_REF,
    ]
    assert intents[0]["target_object_id"] == str(function_impl_id)
    assert intents[0]["target_object_id"] != str(current_function_impl_id)
    create_instruction_kwargs = cast(dict[str, object], intents[0]["kwargs"])
    assert create_instruction_kwargs == {"type": "set", "sequence": 0}
    value_source_kwargs = cast(dict[str, object], intents[1]["kwargs"])
    assert value_source_kwargs["key"] == "display_name"
    assert value_source_kwargs["source_function_config_attribute_config_id"] == (
        str(source_input_id)
    )
    assert "function_impl_instruction_id" not in value_source_kwargs
    assert intents[1]["target_object_id"] == intents[0]["expected_result_object_id"]
    attach_set_kwargs = cast(dict[str, object], intents[2]["kwargs"])
    assert attach_set_kwargs["target_class_config_attribute_config_id"] == (
        str(target_edge_id)
    )
    assert attach_set_kwargs["value_source_id"] == (
        intents[1]["expected_result_object_id"]
    )
    matrix = build_provider_delta_functioncall_capability_matrix(
        provider_delta_typed_operation_plan=typed_operation_plan,
        provider_delta_ontology_execution_plan=plan,
    )
    assert matrix["status"] == "functioncall_capability_matrix_ready"
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["execution_policy"] == "ontology_function_call_only"
    assert matrix["execution_allowed"] is True
    assert matrix["non_executable_operation_count"] == 0
    assert matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }
    capability_entries = cast(
        Sequence[dict[str, object]],
        matrix["capability_entries"],
    )
    assert capability_entries[0]["capability_status"] == (
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION
    )
    assert capability_entries[0]["function_refs"] == (
        FUNCTION_IMPL_CREATE_INSTRUCTION_REF,
        FUNCTION_IMPL_INSTRUCTION_CREATE_VALUE_SOURCE_REF,
        FUNCTION_IMPL_INSTRUCTION_ATTACH_SET_REF,
    )


def test_meta_provider_delta_function_impl_ontology_execution_blocks_replacement_without_baseline_instruction_index() -> (
    None
):
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
    function_semantic_key = f"{class_semantic_key}.rename"
    function_impl_semantic_key = f"{function_semantic_key}/function_impl:default"
    function_impl_id = provider_delta_uuid("ontology-exec-replacement-function-impl")

    plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
            "typed_operation_count": 1,
            "typed_operations": (
                {
                    "operation_key": (
                        "meta_ocg_provider_delta:update:function_impl:"
                        f"{function_impl_semantic_key}"
                    ),
                    "operation_family": "update",
                    "provider_operation_type": "meta_ocg.function_impl.update",
                    "semantic_key": function_impl_semantic_key,
                    "ontology_subject_kind": "function_impl",
                    "baseline": {
                        "object_id": str(function_impl_id),
                        "object": {
                            "function_impl_signature": {
                                "instruction_count": 1,
                                "instructions": (),
                            },
                        },
                    },
                    "current": {
                        "entity_id": str(function_impl_id),
                        "function_impl_signature": {
                            "instructions": ({"type": "set", "sequence": 0},),
                        },
                    },
                },
            ),
        },
    )

    assert plan["status"] == "ontology_execution_plan_blocked"
    assert plan["reason"] == "meta_ocg_ontology_execution_plan_blocked"
    assert plan["invocation_intent_count"] == 0
    assert plan["blockers"] == ("function_impl_baseline_instruction_index_unavailable",)
    handler_results = cast(
        Sequence[dict[str, object]],
        plan["operation_handler_results"],
    )
    assert handler_results[0]["reason"] == (
        "meta_ocg_function_impl_replacement_requires_baseline_instruction_index"
    )


def test_meta_provider_delta_function_impl_ontology_execution_blocks_value_source_kind_replacement() -> (
    None
):
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
    function_semantic_key = f"{class_semantic_key}.rename"
    function_impl_semantic_key = f"{function_semantic_key}/function_impl:default"
    function_impl_id = provider_delta_uuid(
        "ontology-exec-value-source-kind-function-impl"
    )
    target_edge_id = provider_delta_uuid("ontology-exec-value-source-kind-target-edge")
    source_input_id = provider_delta_uuid(
        "ontology-exec-value-source-kind-source-input"
    )

    plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
            "typed_operation_count": 1,
            "typed_operations": (
                {
                    "operation_key": (
                        "meta_ocg_provider_delta:update:function_impl:"
                        f"{function_impl_semantic_key}"
                    ),
                    "operation_family": "update",
                    "provider_operation_type": "meta_ocg.function_impl.update",
                    "semantic_key": function_impl_semantic_key,
                    "ontology_subject_kind": "function_impl",
                    "baseline": {
                        "object_id": str(function_impl_id),
                        "object": {
                            "function_impl_signature": {
                                "instruction_count": 1,
                                "instructions": (
                                    {
                                        "type": "set",
                                        "sequence": 0,
                                        "set": {
                                            "target_class_config_attribute_config_id": (
                                                str(target_edge_id)
                                            ),
                                            "value_source": {
                                                "key": "display_name",
                                                "kind": "literal",
                                            },
                                        },
                                    },
                                ),
                            },
                        },
                    },
                    "current": {
                        "entity_id": str(function_impl_id),
                        "function_impl_signature": {
                            "instruction_count": 1,
                            "instructions": (
                                {
                                    "type": "set",
                                    "sequence": 0,
                                    "set": {
                                        "target_class_config_attribute_config_id": (
                                            str(target_edge_id)
                                        ),
                                        "value_source": {
                                            "key": "display_name",
                                            "kind": "function_input_ref",
                                            "source_function_config_attribute_config_id": (
                                                str(source_input_id)
                                            ),
                                        },
                                    },
                                },
                            ),
                        },
                    },
                },
            ),
        },
    )

    assert plan["status"] == "ontology_execution_plan_blocked"
    assert plan["invocation_intent_count"] == 0
    assert plan["blockers"] == (
        "function_impl_value_source_replacement_requires_specific_update_function:"
        "literal->function_input_ref",
    )


def test_meta_provider_delta_function_impl_ontology_execution_replaces_set_and_appends_instruction() -> (
    None
):
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
    function_semantic_key = f"{class_semantic_key}.rename"
    function_impl_semantic_key = f"{function_semantic_key}/function_impl:default"
    function_impl_id = provider_delta_uuid(
        "ontology-exec-replacement-ready-function-impl"
    )
    name_target_edge_id = provider_delta_uuid("ontology-exec-replacement-name-edge")
    display_target_edge_id = provider_delta_uuid(
        "ontology-exec-replacement-display-edge"
    )
    old_source_input_id = provider_delta_uuid("ontology-exec-replacement-source-input")
    new_source_input_id = provider_delta_uuid(
        "ontology-exec-replacement-new-source-input"
    )

    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:function_impl:"
                    f"{function_impl_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.function_impl.update",
                "semantic_key": function_impl_semantic_key,
                "semantic_subject_type": "aware_meta.FunctionImpl",
                "ontology_subject_kind": "function_impl",
                "source_refs": ("aware/home/tv_channel.aware",),
                "baseline": {
                    "object_id": str(function_impl_id),
                    "object": {
                        "function_impl_signature": {
                            "instruction_count": 1,
                            "instruction_summaries": ("set name = display_name",),
                            "instructions": (
                                {
                                    "type": "set",
                                    "sequence": 0,
                                    "set": {
                                        "target_attribute_name": "name",
                                        "target_class_config_attribute_config_id": (
                                            str(name_target_edge_id)
                                        ),
                                        "value_source": {
                                            "key": "display_name",
                                            "kind": "function_input_ref",
                                            "source_function_config_attribute_config_id": (
                                                str(old_source_input_id)
                                            ),
                                            "source_function_input_name": (
                                                "display_name"
                                            ),
                                        },
                                    },
                                },
                            ),
                        },
                    },
                },
                "current": {
                    "semantic_key": function_impl_semantic_key,
                    "object_kind": "function_impl",
                    "entity_id": str(function_impl_id),
                    "function_semantic_key": function_semantic_key,
                    "function_name": "rename",
                    "function_impl_key": "default",
                    "function_impl_kind": "instruction_body",
                    "function_impl_signature": {
                        "instruction_count": 2,
                        "instruction_summaries": (
                            "set display_label = display_name",
                            "set name = display_name",
                        ),
                        "instructions": (
                            {
                                "type": "set",
                                "sequence": 0,
                                "set": {
                                    "target_attribute_name": "display_label",
                                    "target_class_config_attribute_config_id": (
                                        str(display_target_edge_id)
                                    ),
                                    "value_source": {
                                        "key": "display_name",
                                        "kind": "function_input_ref",
                                        "source_function_config_attribute_config_id": (
                                            str(new_source_input_id)
                                        ),
                                        "source_function_input_name": ("display_name"),
                                    },
                                },
                            },
                            {
                                "type": "set",
                                "sequence": 1,
                                "set": {
                                    "target_attribute_name": "name",
                                    "target_class_config_attribute_config_id": (
                                        str(name_target_edge_id)
                                    ),
                                    "value_source": {
                                        "key": "display_name",
                                        "kind": "function_input_ref",
                                        "source_function_config_attribute_config_id": (
                                            str(new_source_input_id)
                                        ),
                                        "source_function_input_name": ("display_name"),
                                    },
                                },
                            },
                        ),
                    },
                },
            },
        ),
    }
    plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(
            context={"aware_meta.graph_runtime_context": object()},
        ),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )

    assert plan["status"] == "ontology_execution_plan_ready"
    assert plan["reason"] == "meta_ocg_ontology_execution_plan_ready"
    assert plan["invocation_intent_count"] == 5
    assert plan["blockers"] == ()
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    assert [intent["function_ref"] for intent in intents] == [
        FUNCTION_IMPL_VALUE_SOURCE_UPDATE_FUNCTION_INPUT_REF,
        FUNCTION_IMPL_INSTRUCTION_SET_UPDATE_ASSIGNMENT_REF,
        FUNCTION_IMPL_CREATE_INSTRUCTION_REF,
        FUNCTION_IMPL_INSTRUCTION_CREATE_VALUE_SOURCE_REF,
        FUNCTION_IMPL_INSTRUCTION_ATTACH_SET_REF,
    ]
    update_value_source_kwargs = cast(dict[str, object], intents[0]["kwargs"])
    assert update_value_source_kwargs["source_function_config_attribute_config_id"] == (
        str(new_source_input_id)
    )
    update_set_kwargs = cast(dict[str, object], intents[1]["kwargs"])
    assert update_set_kwargs["target_class_config_attribute_config_id"] == (
        str(display_target_edge_id)
    )
    assert intents[0]["owner_class_name"] == "FunctionImplValueSource"
    assert intents[1]["owner_class_name"] == "FunctionImplInstructionSet"
    assert intents[2]["owner_class_name"] == "FunctionImpl"
    assert intents[3]["owner_class_name"] == "FunctionImplInstruction"
    assert intents[4]["owner_class_name"] == "FunctionImplInstruction"

    matrix = build_provider_delta_functioncall_capability_matrix(
        provider_delta_typed_operation_plan=typed_operation_plan,
        provider_delta_ontology_execution_plan=plan,
    )
    assert matrix["status"] == "functioncall_capability_matrix_ready"
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["execution_policy"] == "ontology_function_call_only"
    assert matrix["execution_allowed"] is True
    assert matrix["non_executable_operation_count"] == 0


def test_meta_provider_delta_function_impl_ontology_execution_removes_stale_instruction() -> (
    None
):
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
    function_semantic_key = f"{class_semantic_key}.rename"
    function_impl_semantic_key = f"{function_semantic_key}/function_impl:default"
    function_impl_id = provider_delta_uuid(
        "ontology-exec-stale-instruction-function-impl"
    )
    name_target_edge_id = provider_delta_uuid("ontology-exec-stale-name-edge")
    display_target_edge_id = provider_delta_uuid("ontology-exec-stale-display-edge")
    source_input_id = provider_delta_uuid("ontology-exec-stale-source-input")

    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:function_impl:"
                    f"{function_impl_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.function_impl.update",
                "semantic_key": function_impl_semantic_key,
                "semantic_subject_type": "aware_meta.FunctionImpl",
                "ontology_subject_kind": "function_impl",
                "source_refs": ("aware/home/tv_channel.aware",),
                "baseline": {
                    "object_id": str(function_impl_id),
                    "object": {
                        "function_impl_signature": {
                            "instruction_count": 2,
                            "instruction_summaries": (
                                "set name = display_name",
                                "set display_label = display_name",
                            ),
                            "instructions": (
                                {
                                    "type": "set",
                                    "sequence": 0,
                                    "set": {
                                        "target_class_config_attribute_config_id": (
                                            str(name_target_edge_id)
                                        ),
                                        "value_source": {
                                            "key": "display_name",
                                            "kind": "function_input_ref",
                                            "source_function_config_attribute_config_id": (
                                                str(source_input_id)
                                            ),
                                        },
                                    },
                                },
                                {
                                    "type": "set",
                                    "sequence": 1,
                                    "set": {
                                        "target_class_config_attribute_config_id": (
                                            str(display_target_edge_id)
                                        ),
                                        "value_source": {
                                            "key": "display_name",
                                            "kind": "function_input_ref",
                                            "source_function_config_attribute_config_id": (
                                                str(source_input_id)
                                            ),
                                        },
                                    },
                                },
                            ),
                        },
                    },
                },
                "current": {
                    "semantic_key": function_impl_semantic_key,
                    "object_kind": "function_impl",
                    "entity_id": str(function_impl_id),
                    "function_semantic_key": function_semantic_key,
                    "function_name": "rename",
                    "function_impl_key": "default",
                    "function_impl_kind": "instruction_body",
                    "function_impl_signature": {
                        "instruction_count": 1,
                        "instruction_summaries": ("set name = display_name",),
                        "instructions": (
                            {
                                "type": "set",
                                "sequence": 0,
                                "set": {
                                    "target_class_config_attribute_config_id": (
                                        str(name_target_edge_id)
                                    ),
                                    "value_source": {
                                        "key": "display_name",
                                        "kind": "function_input_ref",
                                        "source_function_config_attribute_config_id": (
                                            str(source_input_id)
                                        ),
                                    },
                                },
                            },
                        ),
                    },
                },
            },
        ),
    }
    plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(
            context={"aware_meta.graph_runtime_context": object()},
        ),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )

    assert plan["status"] == "ontology_execution_plan_ready"
    assert plan["reason"] == "meta_ocg_ontology_execution_plan_ready"
    assert plan["invocation_intent_count"] == 1
    assert plan["blockers"] == ()
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    intent = intents[0]
    assert intent["function_ref"] == FUNCTION_IMPL_REMOVE_INSTRUCTION_REF
    assert intent["owner_class_name"] == "FunctionImpl"
    assert intent["function_name"] == "remove_instruction"
    assert intent["target_object_id"] == str(function_impl_id)
    assert intent["kwargs"] == {"type": "set", "sequence": 1}

    matrix = build_provider_delta_functioncall_capability_matrix(
        provider_delta_typed_operation_plan=typed_operation_plan,
        provider_delta_ontology_execution_plan=plan,
    )
    assert matrix["status"] == "functioncall_capability_matrix_ready"
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["execution_policy"] == "ontology_function_call_only"
    assert matrix["execution_allowed"] is True
    assert matrix["non_executable_operation_count"] == 0


def test_meta_provider_delta_function_impl_sequence_identity_reorder_stale_semantics() -> (
    None
):
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
    function_semantic_key = f"{class_semantic_key}.rename"
    function_impl_semantic_key = f"{function_semantic_key}/function_impl:default"
    function_impl_id = provider_delta_uuid(
        "ontology-exec-sequence-identity-function-impl"
    )
    name_target_edge_id = provider_delta_uuid(
        "ontology-exec-sequence-identity-name-edge"
    )
    display_target_edge_id = provider_delta_uuid(
        "ontology-exec-sequence-identity-display-edge"
    )
    source_input_id = provider_delta_uuid(
        "ontology-exec-sequence-identity-source-input"
    )

    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:function_impl:"
                    f"{function_impl_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.function_impl.update",
                "semantic_key": function_impl_semantic_key,
                "semantic_subject_type": "aware_meta.FunctionImpl",
                "ontology_subject_kind": "function_impl",
                "source_refs": ("aware/home/tv_channel.aware",),
                "baseline": {
                    "object_id": str(function_impl_id),
                    "object": {
                        "function_impl_signature": {
                            "instruction_count": 2,
                            "instruction_summaries": (
                                "set display_label = display_name",
                                "set name = display_name",
                            ),
                            "instructions": (
                                {
                                    "type": "set",
                                    "sequence": 0,
                                    "set": {
                                        "target_class_config_attribute_config_id": (
                                            str(display_target_edge_id)
                                        ),
                                        "value_source": {
                                            "key": "display_name",
                                            "kind": "function_input_ref",
                                            "source_function_config_attribute_config_id": (
                                                str(source_input_id)
                                            ),
                                        },
                                    },
                                },
                                {
                                    "type": "set",
                                    "sequence": 1,
                                    "set": {
                                        "target_class_config_attribute_config_id": (
                                            str(name_target_edge_id)
                                        ),
                                        "value_source": {
                                            "key": "display_name",
                                            "kind": "function_input_ref",
                                            "source_function_config_attribute_config_id": (
                                                str(source_input_id)
                                            ),
                                        },
                                    },
                                },
                            ),
                        },
                    },
                },
                "current": {
                    "semantic_key": function_impl_semantic_key,
                    "object_kind": "function_impl",
                    "entity_id": str(function_impl_id),
                    "function_semantic_key": function_semantic_key,
                    "function_name": "rename",
                    "function_impl_key": "default",
                    "function_impl_kind": "instruction_body",
                    "function_impl_signature": {
                        "instruction_count": 1,
                        "instruction_summaries": ("set name = display_name",),
                        "instructions": (
                            {
                                "type": "set",
                                "sequence": 0,
                                "set": {
                                    "target_class_config_attribute_config_id": (
                                        str(name_target_edge_id)
                                    ),
                                    "value_source": {
                                        "key": "display_name",
                                        "kind": "function_input_ref",
                                        "source_function_config_attribute_config_id": (
                                            str(source_input_id)
                                        ),
                                    },
                                },
                            },
                        ),
                    },
                },
            },
        ),
    }
    plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(
            context={"aware_meta.graph_runtime_context": object()},
        ),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )

    assert plan["status"] == "ontology_execution_plan_ready"
    assert plan["reason"] == "meta_ocg_ontology_execution_plan_ready"
    assert plan["invocation_intent_count"] == 2
    assert plan["blockers"] == ()
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    assert [intent["function_ref"] for intent in intents] == [
        FUNCTION_IMPL_REMOVE_INSTRUCTION_REF,
        FUNCTION_IMPL_INSTRUCTION_SET_UPDATE_ASSIGNMENT_REF,
    ]
    assert [intent["reason"] for intent in intents] == [
        "function_impl_instruction_identity_type_sequence_stale_remove_ready",
        "function_impl_instruction_identity_type_sequence_set_update_ready",
    ]
    assert intents[0]["target_object_id"] == str(function_impl_id)
    assert intents[0]["kwargs"] == {"type": "set", "sequence": 1}
    assert intents[1]["owner_class_name"] == "FunctionImplInstructionSet"
    assert intents[1]["receiver_semantic_key"] == (
        f"{function_impl_semantic_key}/instruction:0/set"
    )
    update_set_kwargs = cast(dict[str, object], intents[1]["kwargs"])
    assert update_set_kwargs["target_class_config_attribute_config_id"] == (
        str(name_target_edge_id)
    )

    matrix = build_provider_delta_functioncall_capability_matrix(
        provider_delta_typed_operation_plan=typed_operation_plan,
        provider_delta_ontology_execution_plan=plan,
    )
    assert matrix["status"] == "functioncall_capability_matrix_ready"
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["execution_policy"] == "ontology_function_call_only"
    assert matrix["execution_allowed"] is True
    assert matrix["non_executable_operation_count"] == 0
