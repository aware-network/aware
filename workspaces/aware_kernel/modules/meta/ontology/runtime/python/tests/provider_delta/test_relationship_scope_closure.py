from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from typing import cast

from aware_meta.class_.config.relationship.deltas.ontology_execution import (
    CLASS_CONFIG_CREATE_RELATIONSHIP_FUNCTION_REF,
    CLASS_CONFIG_REMOVE_RELATIONSHIP_CONFIG_FUNCTION_REF,
)
from aware_meta.fqn_resolver import NamespacePath
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


def test_relationship_create_consumes_source_and_target_scope_closure() -> None:
    relationship_semantic_key = _relationship_semantic_key()
    source_class_config_id = str(provider_delta_uuid("relationship-scope-source"))
    target_class_config_id = str(provider_delta_uuid("relationship-scope-target"))
    relationship_config_id = str(provider_delta_uuid("relationship-scope-create"))
    typed_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=_semantic_dirty_diff(
            entries=(
                _relationship_create_dirty_entry(
                    relationship_semantic_key=relationship_semantic_key,
                    source_class_config_id=source_class_config_id,
                    target_class_config_id=target_class_config_id,
                    relationship_config_id=relationship_config_id,
                    semantic_scope_closure=_class_scope_closure(
                        ("aware_demo.default.home.Device", "Device"),
                        ("aware_demo.default.home.Room", "Room"),
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
    operation = _only_mapping(typed_plan["typed_operations"])
    current = _mapping(operation["current"])
    intent = _only_mapping(ontology_plan["invocation_intents"])

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert typed_plan["typed_operation_count"] == 1
    assert typed_plan["typed_operation_entry_blockers"] == ()
    assert operation["operation_key"] == (
        f"meta_ocg.relationship.create:{relationship_semantic_key}"
    )
    assert operation["provider_operation_type"] == "meta_ocg.relationship.create"
    assert current["semantic_subject_type"] == ("aware_meta.ClassConfigRelationship")
    assert current["source_class_semantic_key"] == (
        "ocg:aware_demo/node:aware_demo.default.home.Room"
    )
    assert current["source_class_fqn"] == "aware_demo.default.home.Room"
    assert current["target_class_fqn"] == "aware_demo.default.home.Device"
    assert current["source_class_config_id"] == source_class_config_id
    assert current["target_class_config_id"] == target_class_config_id
    assert current["relationship_config_id"] == relationship_config_id
    assert current["semantic_scope_closure_consumed"] is True
    assert current["semantic_scope_closure_ready"] is True
    assert current["semantic_scope_closure_blockers"] == ()
    assert len(cast(Sequence[object], current["semantic_scope_closure_gates"])) == 2

    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert intent["function_ref"] == CLASS_CONFIG_CREATE_RELATIONSHIP_FUNCTION_REF
    assert intent["target_object_id"] == source_class_config_id
    assert intent["receiver_semantic_key"] == (
        "ocg:aware_demo/node:aware_demo.default.home.Room"
    )
    assert intent["expected_result_object_id"] == relationship_config_id
    assert capability_matrix["status"] == "functioncall_capability_matrix_ready"
    assert capability_matrix["coverage_status"] == "all_operations_executable"
    assert capability_matrix["execution_allowed"] is True
    assert capability_matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }


def test_relationship_update_blocks_on_source_class_scope_closure_mismatch() -> None:
    relationship_semantic_key = _relationship_semantic_key()
    relationship_config_id = str(provider_delta_uuid("relationship-scope-update-block"))
    typed_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=_semantic_dirty_diff(
            entries=(
                _relationship_update_dirty_entry(
                    relationship_semantic_key=relationship_semantic_key,
                    relationship_config_id=relationship_config_id,
                    semantic_scope_closure=_class_scope_closure(
                        ("aware_demo.default.home.Device", "Device"),
                    ),
                ),
            ),
        ),
        provider_delta_head_move_plan=_ready_head_move_plan(),
        semantic_change_payloads=(),
        function_call_plans=(),
    )
    blockers = cast(tuple[str, ...], typed_plan["typed_operation_entry_blockers"])
    blocked_operation = _operation_by_key(
        typed_plan["blocked_operations"],
        operation_key=f"meta_ocg.relationship.update:{relationship_semantic_key}",
    )
    blocked_current = _mapping(blocked_operation["current"])

    assert typed_plan["status"] == "typed_operation_plan_blocked"
    assert typed_plan["typed_operation_count"] == 0
    assert "semantic_scope_closure_missing_class_fqn:aware_demo.default.home.Room" in (
        blockers
    )
    assert typed_plan["reason"] == (
        "semantic_scope_closure_missing_class_fqn:aware_demo.default.home.Room"
    )
    assert blocked_operation["operation_key"] == (
        f"meta_ocg.relationship.update:{relationship_semantic_key}"
    )
    assert blocked_operation["blocked"] is True
    assert blocked_current["semantic_scope_closure_consumed"] is True
    assert blocked_current["semantic_scope_closure_ready"] is False


def test_relationship_delete_consumes_source_scope_closure() -> None:
    source_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    relationship_semantic_key = f"{source_semantic_key}/relationship:room_devices"
    source_class_config_id = str(
        provider_delta_uuid("relationship-scope-delete-source")
    )
    relationship_config_id = str(
        provider_delta_uuid("relationship-scope-delete-relationship")
    )
    typed_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=_semantic_dirty_diff(
            entries=(
                _relationship_delete_dirty_entry(
                    relationship_semantic_key=relationship_semantic_key,
                    source_class_config_id=source_class_config_id,
                    relationship_config_id=relationship_config_id,
                    semantic_scope_closure=_class_scope_closure(
                        ("aware_demo.default.home.Room", "Room"),
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
    operation = _only_mapping(typed_plan["typed_operations"])
    current = _mapping(operation["current"])
    intent = _only_mapping(ontology_plan["invocation_intents"])

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert operation["operation_key"] == (
        f"meta_ocg.relationship.delete:{relationship_semantic_key}"
    )
    assert current["semantic_scope_closure_consumed"] is True
    assert current["semantic_scope_closure_ready"] is True
    assert len(cast(Sequence[object], current["semantic_scope_closure_gates"])) == 1
    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert (
        intent["function_ref"] == CLASS_CONFIG_REMOVE_RELATIONSHIP_CONFIG_FUNCTION_REF
    )
    assert intent["target_object_id"] == source_class_config_id
    assert intent["expected_result_object_id"] == relationship_config_id


def _relationship_semantic_key() -> str:
    return (
        "ocg:aware_demo/node:aware_demo.default.home.Room:room_devices:"
        "one_to_many:aware_demo.default.home.Device"
    )


def _semantic_dirty_diff(
    *,
    entries: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    return {
        "status": "semantic_dirty_diff_ready",
        "reason": "meta_ocg_dirty_diff_ready",
        "available": True,
        "blocked": False,
        "current_delta_fingerprint": "sha256:relationship-scope-closure",
        "baseline_index_compare_available": True,
        "baseline_index_compare_status": "baseline_index_compared",
        "baseline_index_compare_reason": (
            "meta_ocg_dirty_diff_compared_against_baseline_semantic_object_index"
        ),
        "semantic_dirty_entries": entries,
    }


def _relationship_create_dirty_entry(
    *,
    relationship_semantic_key: str,
    source_class_config_id: str,
    target_class_config_id: str,
    relationship_config_id: str,
    semantic_scope_closure: Mapping[str, object],
) -> dict[str, object]:
    return {
        "entry_key": f"dirty:relationship:{relationship_semantic_key}",
        "dirty_operation": "relationship_create",
        "baseline_compare_operation": "create",
        "baseline_compare_status": "baseline_object_missing",
        "semantic_key": relationship_semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "relationship",
        "source_refs": ("aware/home/model.aware",),
        "entity_id": relationship_config_id,
        "relationship_key": "room_devices",
        "relationship_type": "one_to_many",
        "source_class_config_id": source_class_config_id,
        "target_class_config_id": target_class_config_id,
        "relationship_signature": {
            "target_class_config_id": target_class_config_id,
            "relationship_key": "room_devices",
            "relationship_type": "one_to_many",
            "identity_rail": "containment",
            "forward_required": True,
            "forward_loading_strategy": "eager",
            "reverse_loading_strategy": "lazy",
        },
        "semantic_scope_closure": dict(semantic_scope_closure),
    }


def _relationship_update_dirty_entry(
    *,
    relationship_semantic_key: str,
    relationship_config_id: str,
    semantic_scope_closure: Mapping[str, object],
) -> dict[str, object]:
    target_class_config_id = str(
        provider_delta_uuid("relationship-scope-update-target")
    )
    return {
        "entry_key": f"dirty:relationship:{relationship_semantic_key}",
        "dirty_operation": "relationship_update",
        "baseline_compare_operation": "update",
        "baseline_compare_status": "baseline_object_matched",
        "semantic_key": relationship_semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "relationship",
        "source_refs": ("aware/home/model.aware",),
        "baseline_object_id": relationship_config_id,
        "baseline_object_kind": "relationship",
        "baseline_object": {
            "object_id": relationship_config_id,
            "object_kind": "relationship",
            "entity_id": relationship_config_id,
            "relationship_key": "room_devices",
            "relationship_signature": {
                "target_class_config_id": target_class_config_id,
                "relationship_key": "room_devices",
                "relationship_type": "one_to_many",
            },
        },
        "entity_id": relationship_config_id,
        "relationship_key": "room_devices",
        "relationship_type": "one_to_one",
        "relationship_signature": {
            "target_class_config_id": target_class_config_id,
            "relationship_key": "room_devices",
            "relationship_type": "one_to_one",
            "forward_loading_strategy": "eager",
        },
        "semantic_scope_closure": dict(semantic_scope_closure),
    }


def _relationship_delete_dirty_entry(
    *,
    relationship_semantic_key: str,
    source_class_config_id: str,
    relationship_config_id: str,
    semantic_scope_closure: Mapping[str, object],
) -> dict[str, object]:
    return {
        "entry_key": f"dirty:relationship:{relationship_semantic_key}",
        "dirty_operation": "relationship_delete",
        "baseline_compare_operation": "delete",
        "baseline_compare_status": "baseline_object_stale",
        "semantic_key": relationship_semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "relationship",
        "source_refs": ("aware/home/model.aware",),
        "source_class_config_id": source_class_config_id,
        "baseline_object_id": relationship_config_id,
        "baseline_object_kind": "relationship",
        "baseline_object": {
            "object_id": relationship_config_id,
            "object_kind": "relationship",
            "entity_id": relationship_config_id,
            "relationship_key": "room_devices",
        },
        "relationship_key": "room_devices",
        "semantic_scope_closure": dict(semantic_scope_closure),
    }


def _ready_head_move_plan() -> dict[str, object]:
    return {
        "status": "head_move_plan_ready",
        "reason": "provider_delta_head_move_plan_ready",
        "blocked": False,
    }


def _class_scope_closure(
    *class_specs: tuple[str, str],
) -> Mapping[str, object]:
    return build_meta_ocg_semantic_scope_closure(
        package_fqn_prefix="aware_demo",
        namespace_by_code_id={
            provider_delta_uuid("relationship-scope-closure-code"): NamespacePath(
                package="aware_demo",
                namespace="home",
            ),
        },
        class_configs=tuple(
            ClassConfig(
                id=provider_delta_uuid(f"relationship-scope-closure:{class_fqn}"),
                class_fqn=class_fqn,
                name=class_name,
            )
            for class_fqn, class_name in class_specs
        ),
    ).evidence_payload()


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, Mapping)
    return dict(cast(Mapping[str, object], value))


def _only_mapping(value: object) -> dict[str, object]:
    assert isinstance(value, Sequence)
    assert len(value) == 1
    return _mapping(value[0])


def _operation_by_key(
    value: object,
    *,
    operation_key: str,
) -> dict[str, object]:
    assert isinstance(value, Sequence)
    for item in value:
        operation = _mapping(item)
        if operation.get("operation_key") == operation_key:
            return operation
    raise AssertionError(f"operation not found: {operation_key}")
