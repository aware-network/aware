from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from typing import cast

from aware_meta.fqn_resolver import NamespacePath
from aware_meta.function.config.deltas.ontology_execution import (
    FUNCTION_CONFIG_UPDATE_CONFIG_FUNCTION_REF,
)
from aware_meta.materialization.deltas.capability_matrix import (
    EXECUTABLE_VIA_ONTOLOGY_FUNCTION,
    build_provider_delta_functioncall_capability_matrix,
)
from aware_meta.materialization.deltas.ontology_execution.service import (
    build_provider_delta_ontology_execution_plan,
)
from aware_meta.materialization.deltas.semantic_scope_closure import (
    build_meta_ocg_semantic_scope_closure,
)
from aware_meta.materialization.deltas.typed_operations import (
    _provider_delta_typed_operation_plan,
)
from aware_meta_ontology.class_.class_config import ClassConfig

from .fixtures import provider_delta_uuid


def test_function_update_consumes_owner_class_scope_closure() -> None:
    function_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room/function:rename"
    )
    function_config_id = str(provider_delta_uuid("function-update-scope-function"))
    typed_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=_semantic_dirty_diff(
            entries=(
                _function_update_dirty_entry(
                    function_semantic_key=function_semantic_key,
                    function_config_id=function_config_id,
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
    ontology_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_plan,
    )
    capability_matrix = build_provider_delta_functioncall_capability_matrix(
        provider_delta_typed_operation_plan=typed_plan,
        provider_delta_ontology_execution_plan=ontology_plan,
    )
    operations = cast(Sequence[Mapping[str, object]], typed_plan["typed_operations"])
    operation = operations[0]
    current = _mapping(operation["current"])
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])
    intent = intents[0]

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert typed_plan["typed_operation_count"] == 1
    assert typed_plan["typed_operation_entry_blockers"] == ()
    assert operation["operation_key"] == (
        f"meta_ocg.function.update:{function_semantic_key}"
    )
    assert operation["provider_operation_type"] == "meta_ocg.function.update"
    assert current["semantic_subject_type"] == "aware_meta.FunctionConfig"
    assert current["owner_semantic_key"] == (
        "ocg:aware_demo/node:aware_demo.default.home.Room"
    )
    assert current["owner_key"] == "aware_demo.default.home.Room"
    assert current["function_config_id"] == function_config_id
    assert current["function_name"] == "rename"
    assert current["semantic_scope_closure_consumed"] is True
    assert current["semantic_scope_closure_ready"] is True
    assert current["semantic_scope_closure_blockers"] == ()

    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert intent["function_ref"] == FUNCTION_CONFIG_UPDATE_CONFIG_FUNCTION_REF
    assert intent["target_object_id"] == function_config_id
    assert intent["receiver_semantic_key"] == function_semantic_key
    assert intent["expected_result_object_id"] == function_config_id
    assert intent["kwargs"] == {
        "description": "Rename a room with assistant context.",
        "verb": "rename",
        "is_async": True,
    }
    assert capability_matrix["status"] == "functioncall_capability_matrix_ready"
    assert capability_matrix["coverage_status"] == "all_operations_executable"
    assert capability_matrix["execution_allowed"] is True
    assert capability_matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }


def test_function_update_blocks_on_owner_class_scope_closure_mismatch() -> None:
    function_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room/function:rename"
    )
    typed_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=_semantic_dirty_diff(
            entries=(
                _function_update_dirty_entry(
                    function_semantic_key=function_semantic_key,
                    function_config_id=str(
                        provider_delta_uuid("function-update-scope-block")
                    ),
                    semantic_scope_closure=_class_scope_closure(
                        class_fqn="aware_demo.default.home.Device",
                        class_name="Device",
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
    assert "semantic_scope_closure_missing_class_fqn:aware_demo.default.home.Room" in (
        blockers
    )
    assert typed_plan["reason"] == (
        "semantic_scope_closure_missing_class_fqn:aware_demo.default.home.Room"
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
        "current_delta_fingerprint": "sha256:function-update-scope-closure",
        "baseline_index_compare_available": True,
        "baseline_index_compare_status": "baseline_index_compared",
        "baseline_index_compare_reason": (
            "meta_ocg_dirty_diff_compared_against_baseline_semantic_object_index"
        ),
        "semantic_dirty_entries": entries,
    }


def _function_update_dirty_entry(
    *,
    function_semantic_key: str,
    function_config_id: str,
    semantic_scope_closure: Mapping[str, object],
) -> dict[str, object]:
    owner_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
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
        "description": "Rename a room with assistant context.",
        "verb": "rename",
        "is_async": True,
    }
    return {
        "entry_key": f"dirty:function:{function_semantic_key}",
        "dirty_operation": "function_update",
        "baseline_compare_operation": "update",
        "baseline_compare_status": "baseline_object_matched",
        "semantic_key": function_semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "function",
        "source_refs": ("aware/home/model.aware",),
        "baseline_object_id": function_config_id,
        "baseline_object_kind": "function",
        "baseline_object": {
            "object_id": function_config_id,
            "object_kind": "function",
            "function_config_id": function_config_id,
            "function_signature": baseline_signature,
        },
        "entity_id": function_config_id,
        "entity_name": "rename",
        "function_config_id": function_config_id,
        "function_name": "rename",
        "parent_semantic_key": owner_semantic_key,
        "owner_semantic_key": owner_semantic_key,
        "function_signature": current_signature,
        "payload": {
            "entity_id": function_config_id,
            "function_config_id": function_config_id,
            "function_signature": current_signature,
        },
        "semantic_scope_closure": dict(semantic_scope_closure),
    }


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
        id=provider_delta_uuid(f"function-update-scope-closure:{class_fqn}"),
        class_fqn=class_fqn,
        name=class_name,
    )
    return build_meta_ocg_semantic_scope_closure(
        package_fqn_prefix="aware_demo",
        namespace_by_code_id={
            provider_delta_uuid("function-update-scope-closure-code"): (
                NamespacePath(
                    package="aware_demo",
                    namespace="home",
                )
            ),
        },
        class_configs=(class_config,),
    ).evidence_payload()


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, Mapping)
    return dict(cast(Mapping[str, object], value))
