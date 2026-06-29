from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from typing import cast

from aware_meta.class_.config.deltas.ontology_execution import (
    OBJECT_CONFIG_GRAPH_NODE_CREATE_CLASS_FUNCTION_REF,
)
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.materialization.deltas.capability_matrix import (
    EXECUTABLE_VIA_ONTOLOGY_FUNCTION,
    build_provider_delta_functioncall_capability_matrix,
)
from aware_meta.materialization.deltas.semantic_scope_closure import (
    build_meta_ocg_semantic_scope_closure,
)
from aware_meta.materialization.deltas.ontology_execution.service import (
    build_provider_delta_ontology_execution_plan,
)
from aware_meta.materialization.deltas.typed_operations import (
    _provider_delta_typed_operation_plan,
)
from aware_meta.materialization.semantic_function_call_resolution import (
    META_OCG_CREATE_NODE_FUNCTION_REF,
)
from aware_meta_ontology.class_.class_config import ClassConfig

from .fixtures import provider_delta_uuid


def test_class_create_existing_graph_uses_feature_owned_operation_identity() -> None:
    graph_semantic_key = "ocg:aware_demo"
    class_semantic_key = f"{graph_semantic_key}/node:aware_demo.home.Scene"
    graph_id = str(provider_delta_uuid("existing-graph-class-create-graph"))
    node_id = str(provider_delta_uuid("existing-graph-class-create-node"))
    class_config_id = str(provider_delta_uuid("existing-graph-class-create-class"))
    dirty_diff = _semantic_dirty_diff(
        entries=(
            _existing_graph_dirty_entry(
                graph_semantic_key=graph_semantic_key,
                graph_id=graph_id,
            ),
            _class_create_dirty_entry(
                graph_semantic_key=graph_semantic_key,
                class_semantic_key=class_semantic_key,
                node_id=node_id,
                class_config_id=class_config_id,
            ),
        ),
    )
    head_move_plan = {
        "status": "head_move_plan_ready",
        "reason": "provider_delta_head_move_plan_ready",
        "blocked": False,
    }

    typed_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=dirty_diff,
        provider_delta_head_move_plan=head_move_plan,
        semantic_change_payloads=(),
        function_call_plans=(),
    )
    ontology_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_plan,
    )
    capability_matrix = build_provider_delta_functioncall_capability_matrix(
        provider_delta_typed_operation_plan=typed_plan,
        provider_delta_ontology_execution_plan=ontology_plan,
    )
    operations = cast(Sequence[Mapping[str, object]], typed_plan["typed_operations"])
    anchors = cast(
        Sequence[Mapping[str, object]],
        typed_plan["semantic_object_anchors"],
    )
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])
    create_node_intent, create_class_intent = intents

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert typed_plan["typed_operation_count"] == 1
    assert operations[0]["operation_key"] == (
        f"meta_ocg.class.create:{class_semantic_key}"
    )
    assert "genesis" not in str(operations[0]["operation_key"])
    assert operations[0]["provider_operation_type"] == "meta_ocg.class.create"
    assert operations[0]["operation_family"] == "create"
    assert operations[0]["semantic_key"] == class_semantic_key

    graph_anchor = next(
        anchor for anchor in anchors if anchor["semantic_key"] == graph_semantic_key
    )
    assert graph_anchor["provider_operation_type"] == (
        "meta_ocg.object_config_graph.anchor"
    )
    assert _mapping(graph_anchor["baseline"])["object_id"] == graph_id

    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["invocation_intent_count"] == 2
    assert create_node_intent["function_ref"] == META_OCG_CREATE_NODE_FUNCTION_REF
    assert create_node_intent["target_object_id"] == graph_id
    assert create_node_intent["receiver_semantic_key"] == graph_semantic_key
    assert create_node_intent["expected_result_object_id"] == node_id
    assert create_class_intent["function_ref"] == (
        OBJECT_CONFIG_GRAPH_NODE_CREATE_CLASS_FUNCTION_REF
    )
    assert create_class_intent["target_object_id"] == node_id
    assert create_class_intent["receiver_semantic_key"] == class_semantic_key
    assert create_class_intent["expected_result_object_id"] == class_config_id

    assert capability_matrix["status"] == "functioncall_capability_matrix_ready"
    assert capability_matrix["coverage_status"] == "all_operations_executable"
    assert capability_matrix["execution_policy"] == "ontology_function_call_only"
    assert capability_matrix["execution_allowed"] is True
    assert capability_matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }


def test_class_create_existing_graph_consumes_scope_closure_evidence() -> None:
    graph_semantic_key = "ocg:aware_demo"
    class_semantic_key = f"{graph_semantic_key}/node:aware_demo.home.Scene"
    class_fqn = "aware_demo.home.Scene"
    typed_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=_semantic_dirty_diff(
            entries=(
                _class_create_dirty_entry(
                    graph_semantic_key=graph_semantic_key,
                    class_semantic_key=class_semantic_key,
                    node_id=str(
                        provider_delta_uuid("existing-graph-scope-class-create-node")
                    ),
                    class_config_id=str(
                        provider_delta_uuid("existing-graph-scope-class-create-class")
                    ),
                    semantic_scope_closure=_class_scope_closure(
                        class_fqn=class_fqn,
                        class_name="Scene",
                    ),
                ),
            ),
        ),
        provider_delta_head_move_plan=_ready_head_move_plan(),
        semantic_change_payloads=(),
        function_call_plans=(),
    )
    operations = cast(Sequence[Mapping[str, object]], typed_plan["typed_operations"])
    current = _mapping(operations[0]["current"])

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert typed_plan["typed_operation_count"] == 1
    assert typed_plan["typed_operation_entry_blockers"] == ()
    assert current["semantic_scope_closure_consumed"] is True
    assert current["semantic_scope_closure_ready"] is True
    assert current["semantic_scope_closure_blockers"] == ()
    gate = _mapping(current["semantic_scope_closure_gate"])
    assert gate["status"] == "semantic_scope_closure_gate_ready"
    assert gate["target_fqn"] == class_fqn


def test_class_create_existing_graph_blocks_on_scope_closure_mismatch() -> None:
    graph_semantic_key = "ocg:aware_demo"
    class_semantic_key = f"{graph_semantic_key}/node:aware_demo.home.Scene"

    typed_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=_semantic_dirty_diff(
            entries=(
                _class_create_dirty_entry(
                    graph_semantic_key=graph_semantic_key,
                    class_semantic_key=class_semantic_key,
                    node_id=str(provider_delta_uuid("existing-graph-scope-block-node")),
                    class_config_id=str(
                        provider_delta_uuid("existing-graph-scope-block-class")
                    ),
                    semantic_scope_closure=_class_scope_closure(
                        class_fqn="aware_demo.home.Other",
                        class_name="Other",
                    ),
                ),
            ),
        ),
        provider_delta_head_move_plan=_ready_head_move_plan(),
        semantic_change_payloads=(),
        function_call_plans=(),
    )
    blockers = cast(tuple[str, ...], typed_plan["typed_operation_entry_blockers"])
    blocked_operations = cast(
        Sequence[Mapping[str, object]],
        typed_plan["blocked_operations"],
    )
    blocked_current = _mapping(blocked_operations[0]["current"])

    assert typed_plan["status"] == "typed_operation_plan_blocked"
    assert typed_plan["typed_operation_count"] == 0
    assert cast(int, typed_plan["blocked_operation_count"]) >= 1
    assert "semantic_scope_closure_missing_class_fqn:aware_demo.home.Scene" in (
        blockers
    )
    assert typed_plan["reason"] == (
        "semantic_scope_closure_missing_class_fqn:aware_demo.home.Scene"
    )
    assert blocked_operations[0]["blocked"] is True
    assert blocked_current["semantic_scope_closure_consumed"] is True
    assert blocked_current["semantic_scope_closure_ready"] is False


def _semantic_dirty_diff(
    *,
    entries: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    return {
        "status": "semantic_dirty_diff_ready",
        "reason": "meta_ocg_dirty_diff_ready",
        "available": True,
        "blocked": False,
        "current_delta_fingerprint": "sha256:class-create-existing-graph",
        "baseline_index_compare_available": True,
        "baseline_index_compare_status": "baseline_index_compared",
        "baseline_index_compare_reason": (
            "meta_ocg_dirty_diff_compared_against_baseline_semantic_object_index"
        ),
        "semantic_dirty_entries": entries,
    }


def _existing_graph_dirty_entry(
    *,
    graph_semantic_key: str,
    graph_id: str,
) -> dict[str, object]:
    return {
        "entry_kind": "meta_ocg_semantic_dirty_entry",
        "entry_key": f"dirty:runtime_delta:0:{graph_semantic_key}",
        "semantic_key": graph_semantic_key,
        "source_delta_key": f"aware_meta.runtime_delta:{graph_semantic_key}",
        "source_refs": ("aware/home/model.aware",),
        "semantic_subject_type": "aware_meta.ObjectConfigGraph",
        "ontology_subject_kind": "object_config_graph",
        "dirty_operation": "object_config_graph_noop",
        "baseline_compare_status": "baseline_object_unchanged",
        "baseline_compare_operation": "noop",
        "baseline_object_matched": True,
        "baseline_object_id": graph_id,
        "baseline_object_kind": "object_config_graph",
        "payload": {
            "semantic_key": graph_semantic_key,
            "object_kind": "object_config_graph",
            "fqn_prefix": "aware_demo",
        },
        "baseline_object": {
            "semantic_key": graph_semantic_key,
            "object_kind": "object_config_graph",
            "object_id": graph_id,
            "fqn_prefix": "aware_demo",
        },
    }


def _class_create_dirty_entry(
    *,
    graph_semantic_key: str,
    class_semantic_key: str,
    node_id: str,
    class_config_id: str,
    semantic_scope_closure: Mapping[str, object] | None = None,
) -> dict[str, object]:
    entry: dict[str, object] = {
        "entry_kind": "meta_ocg_semantic_dirty_entry",
        "entry_key": f"dirty:runtime_delta:1:{class_semantic_key}",
        "semantic_key": class_semantic_key,
        "source_delta_key": f"aware_meta.runtime_delta:{class_semantic_key}",
        "source_refs": ("aware/home/scene.aware",),
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "class",
        "dirty_operation": "class_create",
        "baseline_compare_status": "baseline_object_missing",
        "baseline_compare_operation": "create",
        "baseline_object_matched": False,
        "baseline_object_id": None,
        "baseline_object_kind": None,
        "graph_semantic_key": graph_semantic_key,
        "node_id": node_id,
        "node_key": "aware_demo.home.Scene",
        "node_type": "class",
        "entity_id": class_config_id,
        "entity_name": "Scene",
        "class_fqn": "aware_demo.home.Scene",
        "name": "Scene",
        "description": "A semantic scene inside the home.",
        "is_base": True,
        "is_edge": False,
        "value_mode": "graph_ref",
        "payload": {
            "graph_semantic_key": graph_semantic_key,
            "node_id": node_id,
            "node_key": "aware_demo.home.Scene",
            "node_type": "class",
            "entity_id": class_config_id,
            "entity_name": "Scene",
            "class_fqn": "aware_demo.home.Scene",
            "description": "A semantic scene inside the home.",
            "is_base": True,
            "is_edge": False,
            "value_mode": "graph_ref",
        },
    }
    if semantic_scope_closure is not None:
        entry["semantic_scope_closure"] = dict(semantic_scope_closure)
    return entry


def _ready_head_move_plan() -> dict[str, object]:
    return {
        "status": "head_move_plan_ready",
        "reason": "provider_delta_head_move_plan_ready",
        "blocked": False,
    }


def _class_scope_closure(
    *,
    class_fqn: str,
    class_name: str,
) -> Mapping[str, object]:
    class_config = ClassConfig(
        id=provider_delta_uuid(f"class-scope-closure:{class_fqn}"),
        class_fqn=class_fqn,
        name=class_name,
    )
    return build_meta_ocg_semantic_scope_closure(
        package_fqn_prefix="aware_demo",
        namespace_by_code_id={
            provider_delta_uuid("class-scope-closure-code"): NamespacePath(
                package="aware_demo",
                namespace="home",
            ),
        },
        class_configs=(class_config,),
    ).evidence_payload()


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, Mapping)
    return dict(cast(Mapping[str, object], value))
