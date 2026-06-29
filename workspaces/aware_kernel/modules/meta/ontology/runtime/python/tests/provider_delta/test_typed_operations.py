from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from aware_meta.materialization.deltas.typed_operations import (
    _provider_delta_typed_operation_plan,
)

from .fixtures import provider_delta_uuid


def test_meta_provider_delta_function_impl_typed_operation_uses_noop_function_anchor() -> (
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

    assert typed_operation_plan["status"] == "typed_operation_plan_ready"
    assert typed_operation_plan["typed_operation_count"] == 1
    assert typed_operation_plan["semantic_object_anchor_count"] == 2
    assert typed_operation_plan["operation_family_counts"] == {"update": 1}
    assert typed_operation_plan["operation_type_counts"] == {
        "meta_ocg.function_impl.update": 1,
    }
    operations = cast(
        Sequence[dict[str, object]],
        typed_operation_plan["typed_operations"],
    )
    operation = operations[0]
    assert operation["semantic_key"] == function_impl_semantic_key
    assert operation["ontology_subject_kind"] == "function_impl"
    assert operation["provider_operation_type"] == "meta_ocg.function_impl.update"

    anchors = cast(
        Sequence[dict[str, object]],
        typed_operation_plan["semantic_object_anchors"],
    )
    anchor_by_key = {anchor["semantic_key"]: anchor for anchor in anchors}
    assert set(anchor_by_key) == {
        function_semantic_key,
        function_impl_semantic_key,
    }
    function_anchor = anchor_by_key[function_semantic_key]
    assert function_anchor["operation_family"] == "anchor"
    assert function_anchor["provider_operation_type"] == "meta_ocg.function.anchor"
    assert function_anchor["ontology_subject_kind"] == "function"
    function_current = function_anchor["current"]
    assert isinstance(function_current, dict)
    assert function_current["entity_id"] == str(function_config_id)

    function_impl_anchor = anchor_by_key[function_impl_semantic_key]
    assert function_impl_anchor["provider_operation_type"] == (
        "meta_ocg.function_impl.anchor"
    )
    function_impl_current = function_impl_anchor["current"]
    assert isinstance(function_impl_current, dict)
    assert function_impl_current["entity_id"] == str(function_impl_id)


def test_meta_provider_delta_class_create_typed_operation_carries_class_identity() -> (
    None
):
    graph_semantic_key = "ocg:aware_demo"
    class_semantic_key = f"{graph_semantic_key}/node:aware_demo.default.home.Scene"
    graph_id = provider_delta_uuid("typed-operation-class-create-graph")
    node_id = provider_delta_uuid("typed-operation-class-create-node")
    class_config_id = provider_delta_uuid("typed-operation-class-create-config")

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
                    "entry_key": f"dirty:graph:{graph_semantic_key}",
                    "dirty_operation": "object_config_graph_noop",
                    "baseline_compare_operation": "noop",
                    "baseline_compare_status": "baseline_object_unchanged",
                    "semantic_key": graph_semantic_key,
                    "semantic_subject_type": "aware_meta.ObjectConfigGraph",
                    "ontology_subject_kind": "object_config_graph",
                    "source_refs": ("aware/home/model.aware",),
                    "baseline_object_id": str(graph_id),
                    "baseline_object_kind": "object_config_graph",
                    "payload": {
                        "fqn_prefix": "aware_demo",
                    },
                    "baseline_object": {
                        "object_id": str(graph_id),
                        "object_kind": "object_config_graph",
                    },
                },
                {
                    "entry_key": f"dirty:class:{class_semantic_key}",
                    "dirty_operation": "class_create",
                    "baseline_compare_operation": "create",
                    "baseline_compare_status": "baseline_object_missing",
                    "semantic_key": class_semantic_key,
                    "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
                    "ontology_subject_kind": "class",
                    "source_refs": ("aware/home/model.aware",),
                    "graph_semantic_key": graph_semantic_key,
                    "node_id": str(node_id),
                    "node_key": "aware_demo.default.home.Scene",
                    "node_type": "class",
                    "entity_id": str(class_config_id),
                    "entity_name": "Scene",
                    "class_fqn": "aware_demo.default.home.Scene",
                    "description": "A semantic scene inside the home.",
                    "identity_mode": "standalone",
                    "payload": {
                        "graph_semantic_key": graph_semantic_key,
                        "node_id": str(node_id),
                        "node_key": "aware_demo.default.home.Scene",
                        "node_type": "class",
                        "entity_id": str(class_config_id),
                        "entity_name": "Scene",
                        "class_fqn": "aware_demo.default.home.Scene",
                        "description": "A semantic scene inside the home.",
                        "identity_mode": "standalone",
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
    assert typed_operation_plan["semantic_object_anchor_count"] == 2
    assert typed_operation_plan["operation_type_counts"] == {
        "meta_ocg.class.create": 1,
    }
    operations = cast(
        Sequence[dict[str, object]],
        typed_operation_plan["typed_operations"],
    )
    operation = operations[0]
    assert operation["ontology_subject_kind"] == "class"
    current = cast(dict[str, object], operation["current"])
    assert current["graph_semantic_key"] == graph_semantic_key
    assert current["object_config_graph_node_id"] == str(node_id)
    assert current["class_config_id"] == str(class_config_id)
    assert current["class_fqn"] == "aware_demo.default.home.Scene"
    assert current["name"] == "Scene"
    assert current["description"] == "A semantic scene inside the home."
    assert current["identity_mode"] == "standalone"

    anchors = cast(
        Sequence[dict[str, object]],
        typed_operation_plan["semantic_object_anchors"],
    )
    anchor_by_key = {anchor["semantic_key"]: anchor for anchor in anchors}
    graph_anchor = anchor_by_key[graph_semantic_key]
    assert graph_anchor["operation_family"] == "anchor"
    assert graph_anchor["provider_operation_type"] == (
        "meta_ocg.object_config_graph.anchor"
    )
    graph_baseline = cast(dict[str, object], graph_anchor["baseline"])
    assert graph_baseline["object_id"] == str(graph_id)


def test_meta_provider_delta_function_update_splits_membership_typed_operation() -> (
    None
):
    function_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room.rename"
    membership_semantic_key = f"{function_semantic_key}/membership:class_config"
    function_config_id = provider_delta_uuid(
        "typed-operation-function-membership-function"
    )
    class_config_id = provider_delta_uuid("typed-operation-function-membership-class")
    edge_id = provider_delta_uuid("typed-operation-function-membership-edge")
    scalar_signature = {
        "owner_key": "aware_demo.default.home.Room",
        "name": "rename",
        "kind": "instance",
        "description": "Rename a room.",
        "verb": "rename",
        "is_async": False,
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
                    "entry_key": f"dirty:function:{function_semantic_key}",
                    "dirty_operation": "function_update",
                    "baseline_compare_operation": "update",
                    "baseline_compare_status": "baseline_object_matched",
                    "semantic_key": function_semantic_key,
                    "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
                    "ontology_subject_kind": "function",
                    "source_refs": ("aware/home/room.aware",),
                    "baseline_object_id": str(function_config_id),
                    "baseline_object_kind": "function",
                    "entity_id": str(function_config_id),
                    "entity_name": "rename",
                    "parent_semantic_key": (
                        "ocg:aware_demo/node:aware_demo.default.home.Room"
                    ),
                    "function_name": "rename",
                    "class_config_id": str(class_config_id),
                    "class_config_function_config_id": str(edge_id),
                    "function_config_id": str(function_config_id),
                    "function_membership_semantic_key": (membership_semantic_key),
                    "function_signature": scalar_signature,
                    "function_membership_signature": {
                        "class_config_id": str(class_config_id),
                        "function_config_id": str(function_config_id),
                        "is_public": False,
                        "is_constructor": True,
                        "position": 2,
                    },
                    "baseline_object": {
                        "object_id": str(function_config_id),
                        "object_kind": "function",
                        "class_config_function_config_id": str(edge_id),
                        "class_config_id": str(class_config_id),
                        "function_config_id": str(function_config_id),
                        "function_signature": scalar_signature,
                        "function_membership_signature": {
                            "class_config_id": str(class_config_id),
                            "function_config_id": str(function_config_id),
                            "is_public": True,
                            "is_constructor": False,
                            "position": 0,
                        },
                    },
                    "payload": {
                        "entity_id": str(function_config_id),
                        "function_signature": scalar_signature,
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
        "meta_ocg.function_membership.update": 1,
    }
    operations = cast(
        Sequence[dict[str, object]],
        typed_operation_plan["typed_operations"],
    )
    operation = operations[0]
    assert operation["ontology_subject_kind"] == "function_membership"
    assert operation["semantic_key"] == membership_semantic_key
    baseline = cast(dict[str, object], operation["baseline"])
    assert baseline["object_id"] == str(edge_id)
    current = cast(dict[str, object], operation["current"])
    assert current["class_config_function_config_id"] == str(edge_id)
    assert current["function_membership_signature"] == {
        "class_config_id": str(class_config_id),
        "function_config_id": str(function_config_id),
        "is_public": False,
        "is_constructor": True,
        "position": 2,
    }


def test_meta_provider_delta_function_update_scalar_only_skips_membership_noop() -> (
    None
):
    function_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room.rename"
    function_config_id = provider_delta_uuid(
        "typed-operation-function-scalar-only-function"
    )
    class_config_id = provider_delta_uuid("typed-operation-function-scalar-only-class")
    edge_id = provider_delta_uuid("typed-operation-function-scalar-only-edge")
    baseline_signature = {
        "owner_key": "aware_demo.default.home.Room",
        "name": "rename",
        "kind": "instance",
        "description": "Rename a room.",
        "verb": None,
        "is_async": False,
    }
    current_signature = {
        **baseline_signature,
        "description": "Rename a room and update assistant-facing context.",
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
                    "entry_key": f"dirty:function:{function_semantic_key}",
                    "dirty_operation": "function_update",
                    "baseline_compare_operation": "update",
                    "baseline_compare_status": "baseline_object_matched",
                    "semantic_key": function_semantic_key,
                    "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
                    "ontology_subject_kind": "function",
                    "source_refs": ("aware/home/room.aware",),
                    "baseline_object_id": str(function_config_id),
                    "baseline_object_kind": "function",
                    "entity_id": str(function_config_id),
                    "entity_name": "rename",
                    "parent_semantic_key": (
                        "ocg:aware_demo/node:aware_demo.default.home.Room"
                    ),
                    "function_name": "rename",
                    "class_config_id": str(class_config_id),
                    "class_config_function_config_id": str(edge_id),
                    "function_config_id": str(function_config_id),
                    "function_signature": current_signature,
                    "function_membership_signature": {
                        "class_config_id": str(class_config_id),
                        "function_config_id": str(function_config_id),
                        "is_public": True,
                        "is_constructor": False,
                        "position": 0,
                    },
                    "baseline_object": {
                        "object_id": str(function_config_id),
                        "object_kind": "function",
                        "class_config_function_config_id": str(edge_id),
                        "function_signature": baseline_signature,
                        "function_membership_signature": {},
                    },
                    "payload": {
                        "entity_id": str(function_config_id),
                        "function_signature": current_signature,
                        "function_membership_signature": {
                            "class_config_id": str(class_config_id),
                            "function_config_id": str(function_config_id),
                            "is_public": True,
                            "is_constructor": False,
                            "position": 0,
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
        "meta_ocg.function.update": 1,
    }
    operations = cast(
        Sequence[dict[str, object]],
        typed_operation_plan["typed_operations"],
    )
    operation = operations[0]
    assert operation["ontology_subject_kind"] == "function"
    assert operation["semantic_key"] == function_semantic_key
    current = cast(dict[str, object], operation["current"])
    assert current["function_config_id"] == str(function_config_id)
    assert current["function_membership_signature"] == {
        "class_config_id": str(class_config_id),
        "function_config_id": str(function_config_id),
        "is_public": True,
        "is_constructor": False,
        "position": 0,
    }


def test_meta_provider_delta_attribute_update_splits_class_membership_typed_operation() -> (
    None
):
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    attribute_semantic_key = f"{class_semantic_key}/attribute:name"
    membership_semantic_key = f"{attribute_semantic_key}/membership:class_config"
    class_config_id = provider_delta_uuid("typed-operation-class-attribute-class")
    attribute_config_id = provider_delta_uuid(
        "typed-operation-class-attribute-attribute"
    )
    edge_id = provider_delta_uuid("typed-operation-class-attribute-edge")
    scalar_signature = {
        "name": "name",
        "description": "Room name.",
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
                    "entity_name": "name",
                    "parent_semantic_key": class_semantic_key,
                    "attribute_name": "name",
                    "class_config_id": str(class_config_id),
                    "class_config_attribute_config_id": str(edge_id),
                    "attribute_config_id": str(attribute_config_id),
                    "attribute_membership_semantic_key": (membership_semantic_key),
                    "attribute_membership_owner_kind": "class",
                    "attribute_signature": scalar_signature,
                    "attribute_membership_signature": {
                        "owner_kind": "class",
                        "class_config_id": str(class_config_id),
                        "attribute_config_id": str(attribute_config_id),
                        "position": 3,
                        "is_identity_key": True,
                    },
                    "baseline_object": {
                        "object_id": str(attribute_config_id),
                        "object_kind": "attribute",
                        "class_config_attribute_config_id": str(edge_id),
                        "class_config_id": str(class_config_id),
                        "attribute_config_id": str(attribute_config_id),
                        "attribute_signature": scalar_signature,
                        "attribute_membership_signature": {
                            "owner_kind": "class",
                            "class_config_id": str(class_config_id),
                            "attribute_config_id": str(attribute_config_id),
                            "position": 0,
                            "is_identity_key": False,
                        },
                    },
                    "payload": {
                        "entity_id": str(attribute_config_id),
                        "attribute_signature": scalar_signature,
                        "attribute_membership_signature": {
                            "owner_kind": "class",
                            "class_config_id": str(class_config_id),
                            "attribute_config_id": str(attribute_config_id),
                            "position": 3,
                            "is_identity_key": True,
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
    operation = operations[0]
    assert operation["ontology_subject_kind"] == "attribute_membership"
    assert operation["semantic_key"] == membership_semantic_key
    assert operation["semantic_subject_type"] == (
        "aware_meta.ClassConfigAttributeConfig"
    )
    baseline = cast(dict[str, object], operation["baseline"])
    assert baseline["object_id"] == str(edge_id)
    current = cast(dict[str, object], operation["current"])
    assert current["class_config_attribute_config_id"] == str(edge_id)
    assert current["attribute_membership_signature"] == {
        "owner_kind": "class",
        "class_config_id": str(class_config_id),
        "attribute_config_id": str(attribute_config_id),
        "position": 3,
        "is_identity_key": True,
    }
