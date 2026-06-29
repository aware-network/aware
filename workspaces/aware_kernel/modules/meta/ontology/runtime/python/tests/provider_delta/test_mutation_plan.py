from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from aware_meta.materialization.deltas.service import _provider_delta_mutation_plan
from aware_meta.materialization.deltas.typed_operations import (
    _provider_delta_typed_operation_plan,
)

from .fixtures import provider_delta_uuid


def test_meta_provider_delta_function_impl_mutation_plan_uses_noop_function_anchor() -> (
    None
):
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    function_semantic_key = f"{class_semantic_key}.rename"
    function_impl_semantic_key = f"{function_semantic_key}/function_impl:default"
    function_config_id = provider_delta_uuid("function-impl-anchor-function-config")
    function_impl_id = provider_delta_uuid("function-impl-anchor-function-impl")

    typed_operation_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_ready",
            "reason": "meta_ocg_dirty_diff_ready",
            "available": True,
            "blocked": False,
            "baseline_index_compare_available": True,
            "baseline_index_compare_status": "baseline_index_compared",
            "baseline_index_compare_reason": ("meta_ocg_baseline_index_compared"),
            "semantic_dirty_entries": (
                {
                    "entry_key": f"dirty:function:{function_semantic_key}",
                    "dirty_operation": "function_noop",
                    "baseline_compare_operation": "noop",
                    "baseline_compare_status": "baseline_object_unchanged",
                    "semantic_key": function_semantic_key,
                    "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
                    "ontology_subject_kind": "function",
                    "source_refs": ("home/model.aware",),
                    "baseline_object_id": "baseline-function",
                    "baseline_object_kind": "function",
                    "entity_id": str(function_config_id),
                    "entity_name": "rename",
                    "graph_semantic_key": "ocg:aware_demo",
                    "node_key": "aware_demo.default.home.Room.rename",
                    "node_type": "function",
                    "parent_semantic_key": class_semantic_key,
                    "function_name": "rename",
                    "function_signature": {
                        "description": "Rename the room.",
                    },
                    "payload": {
                        "entity_id": str(function_config_id),
                        "entity_name": "rename",
                        "graph_semantic_key": "ocg:aware_demo",
                        "node_key": "aware_demo.default.home.Room.rename",
                        "node_type": "function",
                    },
                },
                {
                    "entry_key": f"dirty:function-impl:{function_impl_semantic_key}",
                    "dirty_operation": "function_impl_update",
                    "baseline_compare_operation": "update",
                    "baseline_compare_status": "baseline_object_matched",
                    "semantic_key": function_impl_semantic_key,
                    "semantic_subject_type": "aware_meta.FunctionImpl",
                    "ontology_subject_kind": "function_impl",
                    "source_refs": ("home/model.aware",),
                    "baseline_object_id": "baseline-function-impl",
                    "baseline_object_kind": "function_impl",
                    "entity_id": str(function_impl_id),
                    "entity_name": "default",
                    "owner_semantic_key": class_semantic_key,
                    "parent_semantic_key": function_semantic_key,
                    "function_semantic_key": function_semantic_key,
                    "function_name": "rename",
                    "function_impl_key": "default",
                    "function_impl_kind": "instruction_body",
                    "function_impl_signature": {
                        "instruction_count": 1,
                        "instruction_summaries": ("set name = new_name",),
                    },
                    "payload": {
                        "entity_id": str(function_impl_id),
                        "entity_name": "default",
                        "function_semantic_key": function_semantic_key,
                        "function_name": "rename",
                        "function_impl_key": "default",
                        "function_impl_kind": "instruction_body",
                        "function_impl_signature": {
                            "instruction_count": 1,
                            "instruction_summaries": ("set name = new_name",),
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

    mutation_plan = _provider_delta_mutation_plan(
        provider_delta_typed_operation_plan=typed_operation_plan,
    )

    assert mutation_plan["status"] == "mutation_plan_ready"
    assert mutation_plan["semantic_object_anchor_count"] == 2
    mutation_steps = {
        step["semantic_key"]: step
        for step in cast(Sequence[dict[str, object]], mutation_plan["mutation_steps"])
    }
    function_impl_step = mutation_steps[function_impl_semantic_key]
    assert function_impl_step["receiver_semantic_key"] == function_semantic_key
    assert function_impl_step["receiver_object_id"] == str(function_config_id)
    assert function_impl_step["receiver_entity_kind"] == "function_config"
    assert function_impl_step["dependencies"] == ()
    assert _descriptor_tree_payload_keys(mutation_plan) == ()


def test_meta_provider_delta_function_impl_mutation_plan_is_head_move_ready() -> None:
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    function_semantic_key = f"{class_semantic_key}.rename"
    function_impl_semantic_key = f"{function_semantic_key}/function_impl:default"
    function_config_id = provider_delta_uuid("function-impl-mutation-function-config")
    function_impl_id = provider_delta_uuid("function-impl-mutation-function-impl")

    mutation_plan = _provider_delta_mutation_plan(
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
            "blocked": False,
            "typed_operation_count": 3,
            "typed_operations": (
                {
                    "operation_key": "meta_ocg_provider_delta:update:graph:aware_demo",
                    "operation_family": "update",
                    "provider_operation_type": "meta_ocg.object_config_graph.update",
                    "semantic_key": "ocg:aware_demo",
                    "semantic_subject_type": "aware_meta.ObjectConfigGraph",
                    "ontology_subject_kind": "object_config_graph",
                    "source_refs": ("home/model.aware",),
                    "current": {
                        "semantic_key": "ocg:aware_demo",
                        "object_kind": "object_config_graph",
                        "graph_semantic_key": "ocg:aware_demo",
                        "entity_name": "aware_demo",
                    },
                    "baseline": {"object_id": "baseline-graph"},
                    "ocg_operation": {
                        "operation": "ensure_object_config_graph",
                        "arguments": {
                            "name": "aware_demo",
                            "fqn_prefix": "aware_demo",
                            "language": "aware",
                        },
                    },
                },
                {
                    "operation_key": (
                        "meta_ocg_provider_delta:update:function:"
                        f"{function_semantic_key}"
                    ),
                    "operation_family": "update",
                    "provider_operation_type": "meta_ocg.function.update",
                    "semantic_key": function_semantic_key,
                    "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
                    "ontology_subject_kind": "function",
                    "source_refs": ("home/model.aware",),
                    "current": {
                        "semantic_key": function_semantic_key,
                        "object_kind": "function",
                        "graph_semantic_key": "ocg:aware_demo",
                        "node_key": "aware_demo.default.home.Room.rename",
                        "entity_id": str(function_config_id),
                        "entity_name": "rename",
                        "function_name": "rename",
                    },
                    "baseline": {"object_id": "baseline-function"},
                    "ocg_operation": {
                        "operation": "ensure_object_config_graph_node",
                        "receiver_semantic_key": "ocg:aware_demo",
                        "arguments": {
                            "graph_semantic_key": "ocg:aware_demo",
                            "node_key": "aware_demo.default.home.Room.rename",
                            "node_type": "function",
                            "entity_id": str(function_config_id),
                            "entity_name": "rename",
                        },
                    },
                },
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
                    "source_refs": ("home/model.aware",),
                    "current": {
                        "semantic_key": function_impl_semantic_key,
                        "object_kind": "function_impl",
                        "entity_id": str(function_impl_id),
                        "entity_name": "default",
                        "owner_semantic_key": class_semantic_key,
                        "function_semantic_key": function_semantic_key,
                        "function_name": "rename",
                        "function_impl_key": "default",
                        "function_impl_kind": "instruction_body",
                        "function_impl_signature": {
                            "instruction_count": 1,
                            "instruction_summaries": ("set name = new_name",),
                        },
                    },
                    "baseline": {"object_id": "baseline-function-impl"},
                    "ocg_operation": {
                        "operation": "ensure_function_impl",
                        "receiver_semantic_key": function_semantic_key,
                        "arguments": {
                            "function_semantic_key": function_semantic_key,
                            "function_name": "rename",
                            "function_impl_key": "default",
                            "function_impl_kind": "instruction_body",
                            "function_impl_signature": {
                                "instruction_count": 1,
                                "instruction_summaries": ("set name = new_name",),
                            },
                        },
                    },
                },
            ),
        }
    )

    assert mutation_plan["status"] == "mutation_plan_ready"
    mutation_steps = {
        step["semantic_key"]: step
        for step in cast(Sequence[dict[str, object]], mutation_plan["mutation_steps"])
    }
    function_impl_step = mutation_steps[function_impl_semantic_key]
    assert function_impl_step["function_ref"] == (
        "aware_meta_ontology.function.function_config."
        "FunctionConfig.create_function_impl"
    )
    assert function_impl_step["receiver_semantic_key"] == function_semantic_key
    assert function_impl_step["receiver_object_id"] == str(function_config_id)
    assert function_impl_step["receiver_entity_kind"] == "function_config"
    assert function_impl_step["function_impl_key"] == "default"
    assert _descriptor_tree_payload_keys(mutation_plan) == ()


def _descriptor_tree_payload_keys(payload: dict[str, object]) -> tuple[str, ...]:
    return tuple(sorted(key for key in payload if "descriptor_tree" in key))
