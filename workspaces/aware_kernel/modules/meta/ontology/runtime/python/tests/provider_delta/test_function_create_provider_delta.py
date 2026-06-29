from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from typing import cast

from aware_meta.fqn_resolver import NamespacePath
from aware_meta.function.config.deltas.ontology_execution import (
    CLASS_CONFIG_CREATE_FUNCTION_CONFIG_FUNCTION_REF,
    CLASS_CONFIG_REMOVE_FUNCTION_CONFIG_FUNCTION_REF,
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


def test_function_create_uses_owner_class_anchor_and_scope_closure() -> None:
    class_semantic_key = "ocg:aware_demo/node:aware_demo.home.Room"
    function_semantic_key = f"{class_semantic_key}/function:create_scene"
    class_config_id = str(provider_delta_uuid("function-create-owner-class"))
    function_config_id = str(provider_delta_uuid("function-create-function"))
    dirty_diff = _semantic_dirty_diff(
        entries=(
            _class_anchor_dirty_entry(
                class_semantic_key=class_semantic_key,
                class_config_id=class_config_id,
            ),
            _function_create_dirty_entry(
                class_semantic_key=class_semantic_key,
                function_semantic_key=function_semantic_key,
                function_config_id=function_config_id,
                semantic_scope_closure=_class_scope_closure(
                    class_fqn="aware_demo.home.Room",
                    class_name="Room",
                ),
            ),
        ),
    )

    typed_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=dirty_diff,
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
    assert operation["operation_key"] == (
        f"meta_ocg.function.create:{function_semantic_key}"
    )
    assert operation["provider_operation_type"] == "meta_ocg.function.create"
    assert operation["operation_family"] == "create"
    assert current["owner_semantic_key"] == class_semantic_key
    assert current["function_config_id"] == function_config_id
    assert current["function_name"] == "create_scene"
    assert current["owner_key"] == "aware_demo.home.Room"
    assert current["semantic_scope_closure_consumed"] is True
    assert current["semantic_scope_closure_ready"] is True
    assert current["semantic_scope_closure_blockers"] == ()

    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["invocation_intent_count"] == 1
    assert intent["owner_class_name"] == "ClassConfig"
    assert intent["function_name"] == "create_function_config"
    assert intent["function_ref"] == CLASS_CONFIG_CREATE_FUNCTION_CONFIG_FUNCTION_REF
    assert intent["target_object_id"] == class_config_id
    assert intent["receiver_semantic_key"] == class_semantic_key
    assert intent["expected_result_object_id"] == function_config_id
    assert intent["kwargs"] == {
        "name": "create_scene",
        "description": "Create a scene.",
        "verb": "create",
        "is_async": True,
        "kind": "constructor",
        "is_public": True,
        "is_constructor": True,
        "position": 1,
    }

    assert capability_matrix["status"] == "functioncall_capability_matrix_ready"
    assert capability_matrix["coverage_status"] == "all_operations_executable"
    assert capability_matrix["execution_policy"] == "ontology_function_call_only"
    assert capability_matrix["execution_allowed"] is True
    assert capability_matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }


def test_function_create_blocks_on_owner_scope_closure_mismatch() -> None:
    class_semantic_key = "ocg:aware_demo/node:aware_demo.home.Room"
    function_semantic_key = f"{class_semantic_key}/function:create_scene"

    typed_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=_semantic_dirty_diff(
            entries=(
                _function_create_dirty_entry(
                    class_semantic_key=class_semantic_key,
                    function_semantic_key=function_semantic_key,
                    function_config_id=str(
                        provider_delta_uuid("function-create-scope-block")
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
    assert "semantic_scope_closure_missing_class_fqn:aware_demo.home.Room" in (blockers)
    assert typed_plan["reason"] == (
        "semantic_scope_closure_missing_class_fqn:aware_demo.home.Room"
    )
    assert blocked_operations[0]["blocked"] is True
    assert blocked_current["semantic_scope_closure_consumed"] is True
    assert blocked_current["semantic_scope_closure_ready"] is False


def test_function_delete_uses_owner_class_remove_function_config() -> None:
    class_semantic_key = "ocg:aware_demo/node:aware_demo.home.Room"
    function_semantic_key = f"{class_semantic_key}/function:create_scene"
    class_config_id = str(provider_delta_uuid("function-delete-owner-class"))
    function_config_id = str(provider_delta_uuid("function-delete-function"))
    dirty_diff = _semantic_dirty_diff(
        entries=(
            _class_anchor_dirty_entry(
                class_semantic_key=class_semantic_key,
                class_config_id=class_config_id,
            ),
            _function_delete_dirty_entry(
                class_semantic_key=class_semantic_key,
                function_semantic_key=function_semantic_key,
                class_config_id=class_config_id,
                function_config_id=function_config_id,
            ),
        ),
    )

    typed_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=dirty_diff,
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
    ocg_operation = _mapping(operation["ocg_operation"])
    ocg_arguments = _mapping(ocg_operation["arguments"])
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])
    intent = intents[0]

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert typed_plan["typed_operation_count"] == 1
    assert operation["operation_key"] == (
        f"meta_ocg.function.delete:{function_semantic_key}"
    )
    assert operation["provider_operation_type"] == "meta_ocg.function.delete"
    assert operation["operation_family"] == "delete"
    assert current["owner_semantic_key"] == class_semantic_key
    assert current["class_config_id"] == class_config_id
    assert current["function_config_id"] == function_config_id
    assert current["function_name"] == "create_scene"
    assert ocg_operation["operation"] == "delete_function_config"
    assert ocg_arguments["semantic_key"] == function_semantic_key
    assert ocg_arguments["function_config_id"] == function_config_id
    assert ocg_arguments["class_config_id"] == class_config_id

    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["invocation_intent_count"] == 1
    assert intent["owner_class_name"] == "ClassConfig"
    assert intent["function_name"] == "remove_function_config"
    assert intent["function_ref"] == CLASS_CONFIG_REMOVE_FUNCTION_CONFIG_FUNCTION_REF
    assert intent["target_object_id"] == class_config_id
    assert intent["receiver_semantic_key"] == class_semantic_key
    assert intent["expected_result_object_id"] == function_config_id
    assert intent["kwargs"] == {
        "name": "create_scene",
        "function_config_id": function_config_id,
    }

    assert capability_matrix["status"] == "functioncall_capability_matrix_ready"
    assert capability_matrix["coverage_status"] == "all_operations_executable"
    assert capability_matrix["execution_policy"] == "ontology_function_call_only"
    assert capability_matrix["execution_allowed"] is True
    assert capability_matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }


def _semantic_dirty_diff(
    *,
    entries: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    return {
        "status": "semantic_dirty_diff_ready",
        "reason": "meta_ocg_dirty_diff_ready",
        "available": True,
        "blocked": False,
        "current_delta_fingerprint": "sha256:function-create-existing-graph",
        "baseline_index_compare_available": True,
        "baseline_index_compare_status": "baseline_index_compared",
        "baseline_index_compare_reason": (
            "meta_ocg_dirty_diff_compared_against_baseline_semantic_object_index"
        ),
        "semantic_dirty_entries": entries,
    }


def _class_anchor_dirty_entry(
    *,
    class_semantic_key: str,
    class_config_id: str,
) -> dict[str, object]:
    return {
        "entry_kind": "meta_ocg_semantic_dirty_entry",
        "entry_key": f"dirty:runtime_delta:0:{class_semantic_key}",
        "semantic_key": class_semantic_key,
        "source_delta_key": f"aware_meta.runtime_delta:{class_semantic_key}",
        "source_refs": ("aware/home/model.aware",),
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "class",
        "dirty_operation": "class_noop",
        "baseline_compare_status": "baseline_object_unchanged",
        "baseline_compare_operation": "noop",
        "baseline_object_matched": True,
        "baseline_object_id": class_config_id,
        "baseline_object_kind": "class",
        "payload": {
            "semantic_key": class_semantic_key,
            "object_kind": "class",
            "entity_id": class_config_id,
            "class_config_id": class_config_id,
            "class_fqn": "aware_demo.home.Room",
            "name": "Room",
        },
        "baseline_object": {
            "semantic_key": class_semantic_key,
            "object_kind": "class",
            "object_id": class_config_id,
            "entity_id": class_config_id,
            "class_config_id": class_config_id,
            "class_fqn": "aware_demo.home.Room",
            "name": "Room",
        },
    }


def _function_create_dirty_entry(
    *,
    class_semantic_key: str,
    function_semantic_key: str,
    function_config_id: str,
    semantic_scope_closure: Mapping[str, object] | None = None,
) -> dict[str, object]:
    entry: dict[str, object] = {
        "entry_kind": "meta_ocg_semantic_dirty_entry",
        "entry_key": f"dirty:runtime_delta:1:{function_semantic_key}",
        "semantic_key": function_semantic_key,
        "source_delta_key": f"aware_meta.runtime_delta:{function_semantic_key}",
        "source_refs": ("aware/home/model.aware",),
        "semantic_subject_type": "aware_meta.FunctionConfig",
        "ontology_subject_kind": "function",
        "dirty_operation": "function_create",
        "baseline_compare_status": "baseline_object_missing",
        "baseline_compare_operation": "create",
        "baseline_object_matched": False,
        "baseline_object_id": None,
        "baseline_object_kind": None,
        "owner_semantic_key": class_semantic_key,
        "owner_key": "aware_demo.home.Room",
        "entity_id": function_config_id,
        "function_config_id": function_config_id,
        "entity_name": "create_scene",
        "function_name": "create_scene",
        "description": "Create a scene.",
        "verb": "create",
        "is_async": True,
        "kind": "constructor",
        "is_public": True,
        "is_constructor": True,
        "position": 1,
        "payload": {
            "owner_semantic_key": class_semantic_key,
            "owner_key": "aware_demo.home.Room",
            "entity_id": function_config_id,
            "function_config_id": function_config_id,
            "entity_name": "create_scene",
            "function_name": "create_scene",
            "description": "Create a scene.",
            "verb": "create",
            "is_async": True,
            "kind": "constructor",
            "is_public": True,
            "is_constructor": True,
            "position": 1,
        },
    }
    if semantic_scope_closure is not None:
        entry["semantic_scope_closure"] = dict(semantic_scope_closure)
    return entry


def _function_delete_dirty_entry(
    *,
    class_semantic_key: str,
    function_semantic_key: str,
    class_config_id: str,
    function_config_id: str,
) -> dict[str, object]:
    return {
        "entry_kind": "meta_ocg_semantic_dirty_entry",
        "entry_key": f"dirty:runtime_delta:1:{function_semantic_key}",
        "semantic_key": function_semantic_key,
        "source_delta_key": f"aware_meta.runtime_delta:{function_semantic_key}",
        "source_refs": ("aware/home/model.aware",),
        "semantic_subject_type": "aware_meta.FunctionConfig",
        "ontology_subject_kind": "function",
        "dirty_operation": "function_delete",
        "baseline_compare_status": "baseline_object_deleted",
        "baseline_compare_operation": "delete",
        "baseline_object_matched": True,
        "baseline_object_id": function_config_id,
        "baseline_object_kind": "function",
        "owner_semantic_key": class_semantic_key,
        "owner_key": "aware_demo.home.Room",
        "class_config_id": class_config_id,
        "entity_id": function_config_id,
        "function_config_id": function_config_id,
        "entity_name": "create_scene",
        "function_name": "create_scene",
        "kind": "constructor",
        "baseline_object": {
            "object_id": function_config_id,
            "object_kind": "function",
            "owner_semantic_key": class_semantic_key,
            "owner_key": "aware_demo.home.Room",
            "class_config_id": class_config_id,
            "entity_id": function_config_id,
            "function_config_id": function_config_id,
            "name": "create_scene",
            "function_name": "create_scene",
            "kind": "constructor",
            "function_signature": {
                "owner_key": "aware_demo.home.Room",
                "name": "create_scene",
                "kind": "constructor",
            },
            "function_membership_signature": {
                "class_config_id": class_config_id,
                "function_config_id": function_config_id,
            },
        },
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
        id=provider_delta_uuid(f"function-create-scope-closure:{class_fqn}"),
        class_fqn=class_fqn,
        name=class_name,
    )
    return build_meta_ocg_semantic_scope_closure(
        package_fqn_prefix="aware_demo",
        namespace_by_code_id={
            provider_delta_uuid("function-create-scope-closure-code"): NamespacePath(
                package="aware_demo",
                namespace="home",
            ),
        },
        class_configs=(class_config,),
    ).evidence_payload()


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, Mapping)
    return dict(cast(Mapping[str, object], value))
