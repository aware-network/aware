from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from typing import cast

from aware_meta.materialization.deltas.capability_matrix import (
    EXECUTABLE_VIA_ONTOLOGY_FUNCTION,
    UNSUPPORTED,
    build_provider_delta_functioncall_capability_matrix,
)
from aware_meta.materialization.deltas.ontology_execution.service import (
    build_provider_delta_ontology_execution_plan,
)
from aware_meta.class_.config.deltas.ontology_execution import (
    CLASS_CONFIG_UPDATE_CONFIG_FUNCTION_REF,
    OBJECT_CONFIG_GRAPH_NODE_CREATE_CLASS_FUNCTION_REF,
)
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.materialization.deltas.semantic_scope_closure import (
    build_meta_ocg_semantic_scope_closure,
)
from aware_meta.materialization.deltas.typed_operations import (
    _provider_delta_typed_operation_plan,
)
from aware_meta.materialization.semantic_function_call_resolution import (
    META_OCG_CREATE_NODE_FUNCTION_REF,
    META_OCG_DELETE_NODE_FUNCTION_REF,
)
from aware_meta_ontology.class_.class_config import ClassConfig

from .fixtures import provider_delta_uuid


def test_meta_provider_delta_class_create_ontology_execution_plan_ready() -> None:
    graph_semantic_key = "ocg:aware_demo"
    class_semantic_key = f"{graph_semantic_key}/node:aware_demo.default.home.Scene"
    graph_id = provider_delta_uuid("ontology-exec-class-create-graph")
    node_id = provider_delta_uuid("ontology-exec-class-create-node")
    class_config_id = provider_delta_uuid("ontology-exec-class-create-config")
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "semantic_object_anchors": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:anchor:object_config_graph:"
                    f"{graph_semantic_key}"
                ),
                "operation_family": "anchor",
                "provider_operation_type": "meta_ocg.object_config_graph.anchor",
                "semantic_key": graph_semantic_key,
                "ontology_subject_kind": "object_config_graph",
                "baseline": {
                    "object_id": str(graph_id),
                    "object_kind": "object_config_graph",
                },
                "current": {
                    "semantic_key": graph_semantic_key,
                    "object_kind": "object_config_graph",
                    "payload": {
                        "fqn_prefix": "aware_demo",
                    },
                },
            },
        ),
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:create:class:" f"{class_semantic_key}"
                ),
                "operation_family": "create",
                "provider_operation_type": "meta_ocg.class.create",
                "semantic_key": class_semantic_key,
                "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
                "ontology_subject_kind": "class",
                "source_refs": ("aware/home/model.aware",),
                "baseline": {},
                "current": {
                    "semantic_key": class_semantic_key,
                    "object_kind": "class",
                    "graph_semantic_key": graph_semantic_key,
                    "node_id": str(node_id),
                    "node_key": "aware_demo.default.home.Scene",
                    "node_type": "class",
                    "entity_id": str(class_config_id),
                    "entity_name": "Scene",
                    "class_fqn": "aware_demo.default.home.Scene",
                    "description": "A semantic scene inside the home.",
                    "is_base": True,
                    "is_edge": False,
                    "value_mode": "graph_ref",
                    "payload": {
                        "graph_semantic_key": graph_semantic_key,
                        "node_id": str(node_id),
                        "node_key": "aware_demo.default.home.Scene",
                        "node_type": "class",
                        "entity_id": str(class_config_id),
                        "entity_name": "Scene",
                        "class_fqn": "aware_demo.default.home.Scene",
                        "description": "A semantic scene inside the home.",
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
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    create_node_intent, create_class_intent = intents
    assert create_node_intent["owner_class_name"] == "ObjectConfigGraph"
    assert create_node_intent["function_name"] == "create_node"
    assert create_node_intent["function_ref"] == META_OCG_CREATE_NODE_FUNCTION_REF
    assert create_node_intent["target_object_id"] == str(graph_id)
    assert create_node_intent["receiver_semantic_key"] == graph_semantic_key
    assert create_node_intent["expected_result_object_id"] == str(node_id)
    create_node_kwargs = cast(dict[str, object], create_node_intent["kwargs"])
    assert create_node_kwargs == {
        "type": "class",
        "node_key": "aware_demo.default.home.Scene",
    }

    assert create_class_intent["owner_class_name"] == "ObjectConfigGraphNode"
    assert create_class_intent["function_name"] == "create_class"
    assert create_class_intent["function_ref"] == (
        OBJECT_CONFIG_GRAPH_NODE_CREATE_CLASS_FUNCTION_REF
    )
    assert create_class_intent["target_object_id"] == str(node_id)
    assert create_class_intent["receiver_semantic_key"] == class_semantic_key
    assert create_class_intent["expected_result_object_id"] == str(class_config_id)
    create_class_kwargs = cast(dict[str, object], create_class_intent["kwargs"])
    assert create_class_kwargs["class_fqn"] == "aware_demo.default.home.Scene"
    assert create_class_kwargs["name"] == "Scene"
    assert create_class_kwargs["description"] == "A semantic scene inside the home."
    assert create_class_kwargs["is_base"] is True
    assert create_class_kwargs["is_edge"] is False
    assert create_class_kwargs["value_mode"] == "graph_ref"

    assert matrix["status"] == "functioncall_capability_matrix_ready"
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["execution_policy"] == "ontology_function_call_only"
    assert matrix["execution_allowed"] is True
    assert matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }
    entries = cast(Sequence[dict[str, object]], matrix["capability_entries"])
    assert entries[0]["function_refs"] == (
        META_OCG_CREATE_NODE_FUNCTION_REF,
        OBJECT_CONFIG_GRAPH_NODE_CREATE_CLASS_FUNCTION_REF,
    )


def test_meta_provider_delta_class_create_coalesces_description_update() -> None:
    graph_semantic_key = "ocg:aware_demo"
    class_semantic_key = f"{graph_semantic_key}/node:aware_demo.default.home.Scene"
    graph_id = provider_delta_uuid("ontology-exec-class-create-coalesce-graph")
    node_id = provider_delta_uuid("ontology-exec-class-create-coalesce-node")
    class_config_id = provider_delta_uuid("ontology-exec-class-create-coalesce-config")
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 2,
        "semantic_object_anchors": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:anchor:object_config_graph:"
                    f"{graph_semantic_key}"
                ),
                "operation_family": "anchor",
                "provider_operation_type": "meta_ocg.object_config_graph.anchor",
                "semantic_key": graph_semantic_key,
                "ontology_subject_kind": "object_config_graph",
                "baseline": {"object_id": str(graph_id)},
                "current": {"payload": {"object_id": str(graph_id)}},
            },
        ),
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:create:class:" f"{class_semantic_key}"
                ),
                "operation_family": "create",
                "provider_operation_type": "meta_ocg.class.create",
                "semantic_key": class_semantic_key,
                "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
                "ontology_subject_kind": "class",
                "source_refs": ("aware/home/model.aware",),
                "baseline": {},
                "current": {
                    "semantic_key": class_semantic_key,
                    "object_kind": "class",
                    "graph_semantic_key": graph_semantic_key,
                    "node_id": str(node_id),
                    "node_key": "aware_demo.default.home.Scene",
                    "node_type": "class",
                    "entity_id": str(class_config_id),
                    "entity_name": "Scene",
                    "class_fqn": "aware_demo.default.home.Scene",
                    "description": "A semantic scene inside the home.",
                    "payload": {
                        "graph_semantic_key": graph_semantic_key,
                        "node_id": str(node_id),
                        "node_key": "aware_demo.default.home.Scene",
                        "entity_id": str(class_config_id),
                        "entity_name": "Scene",
                        "class_fqn": "aware_demo.default.home.Scene",
                        "description": "A semantic scene inside the home.",
                    },
                },
            },
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:class:"
                    f"{class_semantic_key}:description"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.class.update",
                "semantic_key": class_semantic_key,
                "semantic_subject_type": "aware_meta.ClassConfig",
                "ontology_subject_kind": "class",
                "source_refs": ("aware/home/model.aware",),
                "baseline": {"object": {"description": None}},
                "current": {
                    "semantic_key": class_semantic_key,
                    "object_kind": "class",
                    "class_fqn": "aware_demo.default.home.Scene",
                    "entity_name": "Scene",
                    "description": "A semantic scene inside the home.",
                    "payload": {
                        "class_fqn": "aware_demo.default.home.Scene",
                        "entity_name": "Scene",
                        "description": "A semantic scene inside the home.",
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
    assert plan["blockers"] == ()
    assert plan["operation_handler_result_count"] == 1
    assert plan["invocation_intent_count"] == 2
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    assert [intent["function_name"] for intent in intents] == [
        "create_node",
        "create_class",
    ]


def test_meta_provider_delta_class_delete_uses_graph_delete_node_function() -> None:
    graph_semantic_key = "ocg:aware_demo"
    class_semantic_key = f"{graph_semantic_key}/node:aware_demo.default.home.Scene"
    graph_id = provider_delta_uuid("ontology-exec-class-delete-graph")
    node_id = provider_delta_uuid("ontology-exec-class-delete-node")
    class_config_id = provider_delta_uuid("ontology-exec-class-delete-config")
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "semantic_object_anchors": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:anchor:object_config_graph:"
                    f"{graph_semantic_key}"
                ),
                "operation_family": "anchor",
                "provider_operation_type": "meta_ocg.object_config_graph.anchor",
                "semantic_key": graph_semantic_key,
                "ontology_subject_kind": "object_config_graph",
                "baseline": {"object_id": str(graph_id)},
                "current": {"payload": {"object_id": str(graph_id)}},
            },
        ),
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:delete:class:" f"{class_semantic_key}"
                ),
                "operation_family": "delete",
                "provider_operation_type": "meta_ocg.class.delete",
                "semantic_key": class_semantic_key,
                "semantic_subject_type": "aware_meta.ObjectConfigGraph",
                "ontology_subject_kind": "class",
                "source_refs": ("aware/home/model.aware",),
                "baseline": {
                    "object": {
                        "graph_semantic_key": graph_semantic_key,
                        "object_config_graph_node_id": str(node_id),
                        "node_id": str(node_id),
                        "node_key": "aware_demo.default.home.Scene",
                        "class_config_id": str(class_config_id),
                        "entity_id": str(class_config_id),
                        "class_fqn": "aware_demo.default.home.Scene",
                        "name": "Scene",
                    },
                },
                "current": {
                    "semantic_key": class_semantic_key,
                    "object_kind": "class",
                    "graph_semantic_key": graph_semantic_key,
                    "object_config_graph_node_id": str(node_id),
                    "node_id": str(node_id),
                    "node_key": "aware_demo.default.home.Scene",
                    "class_config_id": str(class_config_id),
                    "entity_id": str(class_config_id),
                    "class_fqn": "aware_demo.default.home.Scene",
                    "name": "Scene",
                    "payload": {
                        "graph_semantic_key": graph_semantic_key,
                        "object_config_graph_node_id": str(node_id),
                        "node_key": "aware_demo.default.home.Scene",
                        "class_config_id": str(class_config_id),
                        "class_fqn": "aware_demo.default.home.Scene",
                        "name": "Scene",
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
    assert plan["blockers"] == ()
    assert plan["operation_handler_result_count"] == 1
    assert plan["invocation_intent_count"] == 1
    intents = cast(Sequence[dict[str, object]], plan["invocation_intents"])
    [delete_node_intent] = intents
    assert delete_node_intent["owner_class_name"] == "ObjectConfigGraph"
    assert delete_node_intent["function_name"] == "delete_node"
    assert delete_node_intent["function_ref"] == META_OCG_DELETE_NODE_FUNCTION_REF
    assert delete_node_intent["target_object_id"] == str(graph_id)
    assert delete_node_intent["receiver_semantic_key"] == graph_semantic_key
    assert delete_node_intent["expected_result_object_id"] == str(node_id)
    assert delete_node_intent["commit_required"] is True
    assert delete_node_intent["target_projection_name"] == "ObjectConfigGraph"
    assert delete_node_intent["result_projection_name"] == "ObjectConfigGraph"
    delete_node_kwargs = cast(dict[str, object], delete_node_intent["kwargs"])
    assert delete_node_kwargs == {
        "type": "class",
        "node_key": "aware_demo.default.home.Scene",
        "object_config_graph_node_id": str(node_id),
    }
    assert matrix["status"] == "functioncall_capability_matrix_ready"
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["execution_allowed"] is True
    entries = cast(Sequence[dict[str, object]], matrix["capability_entries"])
    assert entries[0]["function_refs"] == (META_OCG_DELETE_NODE_FUNCTION_REF,)


def test_meta_provider_delta_class_update_uses_update_config_function() -> None:
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    node_id = provider_delta_uuid("ontology-exec-class-update-node")
    class_config_id = provider_delta_uuid("ontology-exec-class-update-config")
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:class:" f"{class_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.class.update",
                "semantic_key": class_semantic_key,
                "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
                "ontology_subject_kind": "class",
                "source_refs": ("aware/home/model.aware",),
                "baseline": {
                    "object_id": str(node_id),
                    "object_kind": "class",
                    "object": {
                        "object_id": str(node_id),
                        "payload": {
                            "entity_id": str(class_config_id),
                            "node_id": str(node_id),
                            "class_fqn": "aware_demo.default.home.Room",
                            "name": "Room",
                        },
                    },
                },
                "current": {
                    "semantic_key": class_semantic_key,
                    "object_kind": "class",
                    "object_id": str(node_id),
                    "entity_id": str(class_config_id),
                    "entity_name": "Room",
                    "class_fqn": "aware_demo.default.home.Room",
                    "description": "A renamed home room.",
                    "is_base": False,
                    "is_edge": True,
                    "value_mode": "inline_value",
                    "identity_mode": "standalone",
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
    handler_results = cast(
        Sequence[dict[str, object]],
        plan["operation_handler_results"],
    )
    assert handler_results[0]["handler_key"] == (
        "class.object_config_graph_node_function_calls"
    )
    assert handler_results[0]["reason"] == "meta_ocg_class_update_function_call_ready"
    intents = cast(
        Sequence[dict[str, object]], handler_results[0]["invocation_intents"]
    )
    assert len(intents) == 1
    intent = intents[0]
    assert intent["owner_class_name"] == "ClassConfig"
    assert intent["function_name"] == "update_config"
    assert intent["function_ref"] == CLASS_CONFIG_UPDATE_CONFIG_FUNCTION_REF
    assert intent["target_object_id"] == str(class_config_id)
    assert intent["receiver_semantic_key"] == class_semantic_key
    assert intent["expected_result_object_id"] == str(class_config_id)
    kwargs = cast(dict[str, object], intent["kwargs"])
    assert kwargs == {
        "description": "A renamed home room.",
        "is_base": False,
        "is_edge": True,
        "value_mode": "inline_value",
        "identity_mode": "standalone",
    }
    assert matrix["status"] == "functioncall_capability_matrix_ready"
    assert matrix["coverage_status"] == "all_operations_executable"
    assert matrix["execution_allowed"] is True
    assert matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }


def test_meta_provider_delta_class_update_consumes_scope_closure_evidence() -> None:
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    class_config_id = provider_delta_uuid("class-update-scope-config")
    typed_operation_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=_semantic_dirty_diff(
            entries=(
                _class_update_dirty_entry(
                    class_semantic_key=class_semantic_key,
                    class_config_id=str(class_config_id),
                    semantic_scope_closure=_class_scope_closure(
                        class_fqn="aware_demo.default.home.Room",
                        class_name="Room",
                    ),
                ),
            ),
        ),
        provider_delta_head_move_plan=_ready_head_move_plan(),
        semantic_change_payloads=(),
        function_call_plans=(),
    )
    operations = cast(
        Sequence[Mapping[str, object]],
        typed_operation_plan["typed_operations"],
    )
    operation = operations[0]
    current = cast(Mapping[str, object], operation["current"])

    assert typed_operation_plan["status"] == "typed_operation_plan_ready"
    assert typed_operation_plan["typed_operation_count"] == 1
    assert typed_operation_plan["typed_operation_entry_blockers"] == ()
    assert operation["operation_key"] == (f"meta_ocg.class.update:{class_semantic_key}")
    assert current["semantic_scope_closure_consumed"] is True
    assert current["semantic_scope_closure_ready"] is True
    assert current["semantic_scope_closure_blockers"] == ()

    ontology_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )

    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])
    assert intents[0]["function_ref"] == CLASS_CONFIG_UPDATE_CONFIG_FUNCTION_REF
    assert intents[0]["target_object_id"] == str(class_config_id)


def test_meta_provider_delta_class_update_blocks_on_scope_closure_mismatch() -> None:
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    typed_operation_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=_semantic_dirty_diff(
            entries=(
                _class_update_dirty_entry(
                    class_semantic_key=class_semantic_key,
                    class_config_id=str(
                        provider_delta_uuid("class-update-scope-block-config")
                    ),
                    semantic_scope_closure=_class_scope_closure(
                        class_fqn="aware_demo.default.home.Other",
                        class_name="Other",
                    ),
                ),
            ),
        ),
        provider_delta_head_move_plan=_ready_head_move_plan(),
        semantic_change_payloads=(),
        function_call_plans=(),
    )
    blockers = cast(
        tuple[str, ...],
        typed_operation_plan["typed_operation_entry_blockers"],
    )
    blocked_operations = cast(
        Sequence[Mapping[str, object]],
        typed_operation_plan["blocked_operations"],
    )
    blocked_current = cast(Mapping[str, object], blocked_operations[0]["current"])

    assert typed_operation_plan["status"] == "typed_operation_plan_blocked"
    assert typed_operation_plan["typed_operation_count"] == 0
    assert "semantic_scope_closure_missing_class_fqn:aware_demo.default.home.Room" in (
        blockers
    )
    assert typed_operation_plan["reason"] == (
        "semantic_scope_closure_missing_class_fqn:aware_demo.default.home.Room"
    )
    assert blocked_operations[0]["blocked"] is True
    assert blocked_current["semantic_scope_closure_consumed"] is True
    assert blocked_current["semantic_scope_closure_ready"] is False


def test_meta_provider_delta_class_update_blocks_identity_change() -> None:
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    class_config_id = provider_delta_uuid("ontology-exec-class-update-identity")
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:class:" f"{class_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.class.update",
                "semantic_key": class_semantic_key,
                "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
                "ontology_subject_kind": "class",
                "source_refs": ("aware/home/model.aware",),
                "baseline": {
                    "object_id": str(class_config_id),
                    "object_kind": "class",
                    "class_fqn": "aware_demo.default.home.Room",
                    "name": "Room",
                },
                "current": {
                    "semantic_key": class_semantic_key,
                    "object_kind": "class",
                    "entity_id": str(class_config_id),
                    "entity_name": "RenamedRoom",
                    "class_fqn": "aware_demo.default.home.RenamedRoom",
                    "name": "RenamedRoom",
                    "description": "A renamed home room.",
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
        "class_identity_change_requires_replacement:class_fqn",
        "class_identity_change_requires_replacement:name",
    )
    handler_results = cast(
        Sequence[dict[str, object]],
        plan["operation_handler_results"],
    )
    assert handler_results[0]["reason"] == (
        "meta_ocg_class_update_requires_replacement"
    )
    assert matrix["coverage_status"] == "all_operations_blocked"
    assert matrix["execution_allowed"] is False
    assert matrix["capability_status_counts"] == {UNSUPPORTED: 1}


def _semantic_dirty_diff(
    *,
    entries: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    return {
        "status": "semantic_dirty_diff_ready",
        "reason": "meta_ocg_dirty_diff_ready",
        "available": True,
        "blocked": False,
        "baseline_index_compare_available": True,
        "baseline_index_compare_status": "baseline_index_compared",
        "semantic_dirty_entries": entries,
    }


def _ready_head_move_plan() -> dict[str, object]:
    return {
        "status": "head_move_plan_ready",
        "reason": "provider_delta_head_move_plan_ready",
        "blocked": False,
    }


def _class_update_dirty_entry(
    *,
    class_semantic_key: str,
    class_config_id: str,
    semantic_scope_closure: Mapping[str, object],
) -> dict[str, object]:
    class_fqn = "aware_demo.default.home.Room"
    return {
        "entry_key": f"dirty:class:{class_semantic_key}",
        "dirty_operation": "class_update",
        "baseline_compare_operation": "update",
        "baseline_compare_status": "baseline_object_matched",
        "semantic_key": class_semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "class",
        "source_refs": ("aware/home/model.aware",),
        "baseline_object_id": class_config_id,
        "baseline_object_kind": "class",
        "baseline_object": {
            "object_id": class_config_id,
            "object_kind": "class",
            "payload": {
                "entity_id": class_config_id,
                "class_fqn": class_fqn,
                "name": "Room",
            },
        },
        "entity_id": class_config_id,
        "entity_name": "Room",
        "class_fqn": class_fqn,
        "description": "An updated home room.",
        "is_base": False,
        "is_edge": True,
        "value_mode": "inline_value",
        "identity_mode": "standalone",
        "semantic_scope_closure": dict(semantic_scope_closure),
    }


def _class_scope_closure(
    *,
    class_fqn: str,
    class_name: str,
) -> Mapping[str, object]:
    class_config = ClassConfig(
        id=provider_delta_uuid(f"class-update-scope-closure:{class_fqn}"),
        class_fqn=class_fqn,
        name=class_name,
    )
    return build_meta_ocg_semantic_scope_closure(
        package_fqn_prefix="aware_demo",
        namespace_by_code_id={
            provider_delta_uuid("class-update-scope-closure-code"): NamespacePath(
                package="aware_demo",
                namespace="home",
            ),
        },
        class_configs=(class_config,),
    ).evidence_payload()
