from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from typing import cast
from uuid import UUID

from aware_meta.enum.config.deltas.ontology_execution import (
    ENUM_CONFIG_CREATE_ENUM_OPTION_FUNCTION_REF,
    ENUM_CONFIG_DELETE_ENUM_OPTION_FUNCTION_REF,
    ENUM_CONFIG_UPDATE_CONFIG_FUNCTION_REF,
    ENUM_OPTION_UPDATE_CONFIG_FUNCTION_REF,
    OBJECT_CONFIG_GRAPH_NODE_CREATE_ENUM_FUNCTION_REF,
    plan_enum_operation,
)
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.materialization.deltas.capability_matrix import (
    EXECUTABLE_VIA_ONTOLOGY_FUNCTION,
    build_provider_delta_functioncall_capability_matrix,
)
from aware_meta.materialization.deltas.ontology_execution.contracts import (
    OntologyExecutionPlanningContext,
    OntologyTypedOperation,
)
from aware_meta.materialization.deltas.ontology_execution.invocation import (
    _invocation_projection_hash_for_instance_intent,
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
from aware_meta.materialization.semantic_function_call_resolution import (
    META_OCG_CREATE_NODE_FUNCTION_REF,
    META_OCG_DELETE_NODE_FUNCTION_REF,
)
from aware_meta.graph.config.stable_ids import (
    stable_enum_config_id,
    stable_object_config_graph_node_id,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)

from .fixtures import provider_delta_uuid


def test_enum_create_existing_graph_plans_feature_owned_function_calls() -> None:
    graph_semantic_key = "ocg:aware_demo"
    enum_semantic_key = f"{graph_semantic_key}/node:aware_demo.home.RoomState"
    graph_id = str(provider_delta_uuid("existing-graph-enum-create-graph"))
    node_id = str(provider_delta_uuid("existing-graph-enum-create-node"))
    enum_config_id = str(provider_delta_uuid("existing-graph-enum-create-enum"))
    dirty_diff = _semantic_dirty_diff(
        entries=(
            _existing_graph_dirty_entry(
                graph_semantic_key=graph_semantic_key,
                graph_id=graph_id,
            ),
            _enum_create_dirty_entry(
                graph_semantic_key=graph_semantic_key,
                enum_semantic_key=enum_semantic_key,
                node_id=node_id,
                enum_config_id=enum_config_id,
                values=("ready", "offline"),
                semantic_scope_closure=_enum_scope_closure(
                    enum_fqn="aware_demo.home.RoomState",
                    enum_name="RoomState",
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
    current = _mapping(operations[0]["current"])
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])
    create_node_intent, create_enum_intent = intents

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert typed_plan["typed_operation_count"] == 1
    assert operations[0]["operation_key"] == (
        f"meta_ocg.enum.create:{enum_semantic_key}"
    )
    assert operations[0]["provider_operation_type"] == "meta_ocg.enum.create"
    assert operations[0]["operation_family"] == "create"
    assert current["enum_fqn"] == "aware_demo.home.RoomState"
    assert current["name"] == "RoomState"
    assert current["values"] == ("ready", "offline")
    assert current["semantic_scope_closure_consumed"] is True
    assert current["semantic_scope_closure_ready"] is True
    assert current["semantic_scope_closure_blockers"] == ()

    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["invocation_intent_count"] == 2
    assert create_node_intent["function_ref"] == META_OCG_CREATE_NODE_FUNCTION_REF
    assert create_node_intent["target_object_id"] == graph_id
    assert create_node_intent["receiver_semantic_key"] == graph_semantic_key
    assert create_node_intent["expected_result_object_id"] == node_id
    assert create_node_intent["kwargs"] == {
        "type": "enum",
        "node_key": "aware_demo.home.RoomState",
    }
    assert create_enum_intent["function_ref"] == (
        OBJECT_CONFIG_GRAPH_NODE_CREATE_ENUM_FUNCTION_REF
    )
    assert create_enum_intent["target_object_id"] == node_id
    assert create_enum_intent["receiver_semantic_key"] == enum_semantic_key
    assert create_enum_intent["expected_result_object_id"] == enum_config_id
    assert create_enum_intent["kwargs"] == {
        "enum_fqn": "aware_demo.home.RoomState",
        "name": "RoomState",
        "description": "Home room lifecycle state.",
        "values": ["ready", "offline"],
    }

    assert capability_matrix["status"] == "functioncall_capability_matrix_ready"
    assert capability_matrix["coverage_status"] == "all_operations_executable"
    assert capability_matrix["execution_policy"] == "ontology_function_call_only"
    assert capability_matrix["execution_allowed"] is True
    assert capability_matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }


def test_enum_create_existing_graph_derives_missing_target_identity() -> None:
    graph_semantic_key = "ocg:aware_demo"
    enum_semantic_key = f"{graph_semantic_key}/node:aware_demo.home.RoomState"
    graph_id = str(provider_delta_uuid("existing-graph-enum-create-derived-graph"))
    expected_node_id = str(
        stable_object_config_graph_node_id(
            object_config_graph_id=UUID(graph_id),
            type=ObjectConfigGraphNodeType.enum.value,
            node_key="aware_demo.home.RoomState",
        )
    )
    expected_enum_config_id = str(
        stable_enum_config_id(
            object_config_graph_node_id=UUID(expected_node_id),
            enum_fqn="aware_demo.home.RoomState",
        )
    )
    graph_operation = OntologyTypedOperation(
        operation_key="meta_ocg.object_config_graph.noop:aware_demo",
        operation_family="noop",
        provider_operation_type="meta_ocg.object_config_graph.noop",
        semantic_key=graph_semantic_key,
        ontology_subject_kind="object_config_graph",
        baseline={"object": {"object_id": graph_id}},
        current={"payload": {"object_id": graph_id}},
    )
    create_current = {
        "graph_semantic_key": graph_semantic_key,
        "node_key": "aware_demo.home.RoomState",
        "enum_fqn": "aware_demo.home.RoomState",
        "name": "RoomState",
        "values": ("ready", "offline"),
    }
    operation = OntologyTypedOperation(
        operation_key=f"meta_ocg.enum.create:{enum_semantic_key}",
        operation_family="create",
        provider_operation_type="meta_ocg.enum.create",
        semantic_key=enum_semantic_key,
        ontology_subject_kind="enum",
        baseline={"object": {}},
        current={**create_current, "payload": create_current},
        source_refs=("aware/home/model.aware",),
    )
    result = plan_enum_operation(
        operation=operation,
        context=OntologyExecutionPlanningContext(
            operation_by_semantic_key={graph_semantic_key: graph_operation},
        ),
    )
    create_node_intent, create_enum_intent = result.invocation_intents

    assert result.status == "ontology_operation_handler_ready"
    assert create_node_intent.expected_result_object_id == expected_node_id
    assert create_enum_intent.target_object_id == expected_node_id
    assert create_enum_intent.expected_result_object_id == expected_enum_config_id


def test_enum_delete_existing_graph_plans_graph_owned_delete_function_call() -> None:
    graph_semantic_key = "ocg:aware_demo"
    enum_semantic_key = f"{graph_semantic_key}/node:aware_demo.home.RoomState"
    graph_id = str(provider_delta_uuid("existing-graph-enum-delete-graph"))
    node_id = str(provider_delta_uuid("existing-graph-enum-delete-node"))
    enum_config_id = str(provider_delta_uuid("existing-graph-enum-delete-enum"))
    dirty_diff = _semantic_dirty_diff(
        entries=(
            _existing_graph_dirty_entry(
                graph_semantic_key=graph_semantic_key,
                graph_id=graph_id,
            ),
            _enum_delete_dirty_entry(
                graph_semantic_key=graph_semantic_key,
                enum_semantic_key=enum_semantic_key,
                node_id=node_id,
                enum_config_id=enum_config_id,
                semantic_scope_closure=_enum_scope_closure(
                    enum_fqn="aware_demo.home.RoomState",
                    enum_name="RoomState",
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
    current = _mapping(operations[0]["current"])
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])
    [delete_node_intent] = intents

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert typed_plan["typed_operation_count"] == 1
    assert operations[0]["operation_key"] == (
        f"meta_ocg.enum.delete:{enum_semantic_key}"
    )
    assert operations[0]["provider_operation_type"] == "meta_ocg.enum.delete"
    assert operations[0]["semantic_subject_type"] == "aware_meta.ObjectConfigGraph"
    assert operations[0]["operation_family"] == "delete"
    assert current["enum_fqn"] == "aware_demo.home.RoomState"
    assert current["name"] == "RoomState"
    assert current["enum_config_id"] == enum_config_id
    assert current["object_config_graph_node_id"] == node_id

    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["invocation_intent_count"] == 1
    assert delete_node_intent["function_ref"] == META_OCG_DELETE_NODE_FUNCTION_REF
    assert delete_node_intent["target_object_id"] == graph_id
    assert delete_node_intent["receiver_semantic_key"] == graph_semantic_key
    assert delete_node_intent["expected_result_object_id"] == node_id
    assert delete_node_intent["commit_required"] is True
    assert delete_node_intent["kwargs"] == {
        "type": "enum",
        "node_key": "aware_demo.home.RoomState",
        "object_config_graph_node_id": node_id,
    }

    assert capability_matrix["status"] == "functioncall_capability_matrix_ready"
    assert capability_matrix["coverage_status"] == "all_operations_executable"
    assert capability_matrix["execution_policy"] == "ontology_function_call_only"
    assert capability_matrix["execution_allowed"] is True
    assert capability_matrix["capability_status_counts"] == {
        EXECUTABLE_VIA_ONTOLOGY_FUNCTION: 1,
    }


def test_enum_delete_ontology_execution_coalesces_child_option_deletes() -> None:
    graph_semantic_key = "ocg:aware_demo"
    enum_semantic_key = f"{graph_semantic_key}/node:aware_demo.home.RoomState"
    graph_id = str(provider_delta_uuid("enum-delete-coalesce-graph"))
    node_id = str(provider_delta_uuid("enum-delete-coalesce-node"))
    enum_config_id = str(provider_delta_uuid("enum-delete-coalesce-enum"))
    option_id = str(provider_delta_uuid("enum-delete-coalesce-option"))
    dirty_diff = _semantic_dirty_diff(
        entries=(
            _existing_graph_dirty_entry(
                graph_semantic_key=graph_semantic_key,
                graph_id=graph_id,
            ),
            _enum_delete_dirty_entry(
                graph_semantic_key=graph_semantic_key,
                enum_semantic_key=enum_semantic_key,
                node_id=node_id,
                enum_config_id=enum_config_id,
                semantic_scope_closure=_enum_scope_closure(
                    enum_fqn="aware_demo.home.RoomState",
                    enum_name="RoomState",
                ),
            ),
            _enum_option_delete_dirty_entry(
                graph_semantic_key=graph_semantic_key,
                enum_semantic_key=enum_semantic_key,
                option_semantic_key=f"{enum_semantic_key}/option:ready",
                enum_config_id=enum_config_id,
                enum_option_id=option_id,
                value="ready",
                semantic_scope_closure=_enum_scope_closure(
                    enum_fqn="aware_demo.home.RoomState",
                    enum_name="RoomState",
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
    operations = cast(Sequence[Mapping[str, object]], typed_plan["typed_operations"])
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])

    assert [operation["provider_operation_type"] for operation in operations] == [
        "meta_ocg.enum.delete",
        "meta_ocg.enum_option.delete",
    ]
    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["operation_handler_result_count"] == 1
    assert ontology_plan["invocation_intent_count"] == 1
    assert intents[0]["function_ref"] == META_OCG_DELETE_NODE_FUNCTION_REF
    assert intents[0]["target_object_id"] == graph_id
    assert intents[0]["expected_result_object_id"] == node_id
    assert intents[0]["kwargs"] == {
        "type": "enum",
        "node_key": "aware_demo.home.RoomState",
        "object_config_graph_node_id": node_id,
    }


def test_enum_create_existing_graph_blocks_on_scope_closure_mismatch() -> None:
    graph_semantic_key = "ocg:aware_demo"
    enum_semantic_key = f"{graph_semantic_key}/node:aware_demo.home.RoomState"

    typed_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=_semantic_dirty_diff(
            entries=(
                _enum_create_dirty_entry(
                    graph_semantic_key=graph_semantic_key,
                    enum_semantic_key=enum_semantic_key,
                    node_id=str(provider_delta_uuid("enum-scope-block-node")),
                    enum_config_id=str(provider_delta_uuid("enum-scope-block-enum")),
                    values=("ready",),
                    semantic_scope_closure=_enum_scope_closure(
                        enum_fqn="aware_demo.home.OtherState",
                        enum_name="OtherState",
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
    assert "semantic_scope_closure_missing_enum_fqn:aware_demo.home.RoomState" in (
        blockers
    )
    assert typed_plan["reason"] == (
        "semantic_scope_closure_missing_enum_fqn:aware_demo.home.RoomState"
    )
    assert blocked_operations[0]["blocked"] is True
    assert blocked_current["semantic_scope_closure_consumed"] is True
    assert blocked_current["semantic_scope_closure_ready"] is False


def test_enum_update_existing_graph_plans_update_config_function_call() -> None:
    graph_semantic_key = "ocg:aware_demo"
    enum_semantic_key = f"{graph_semantic_key}/node:aware_demo.home.RoomState"
    enum_config_id = str(provider_delta_uuid("existing-graph-enum-update-enum"))

    typed_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=_semantic_dirty_diff(
            entries=(
                _enum_update_dirty_entry(
                    graph_semantic_key=graph_semantic_key,
                    enum_semantic_key=enum_semantic_key,
                    enum_config_id=enum_config_id,
                    description="Home room lifecycle state contract.",
                    semantic_scope_closure=_enum_scope_closure(
                        enum_fqn="aware_demo.home.RoomState",
                        enum_name="RoomState",
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
    operations = cast(Sequence[Mapping[str, object]], typed_plan["typed_operations"])
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert operations[0]["provider_operation_type"] == "meta_ocg.enum.update"
    assert operations[0]["operation_family"] == "update"
    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["invocation_intent_count"] == 1
    assert intents[0]["function_ref"] == ENUM_CONFIG_UPDATE_CONFIG_FUNCTION_REF
    assert intents[0]["target_object_id"] == enum_config_id
    assert intents[0]["kwargs"] == {
        "description": "Home room lifecycle state contract.",
    }


def test_enum_update_blocks_identity_drift() -> None:
    graph_semantic_key = "ocg:aware_demo"
    enum_semantic_key = f"{graph_semantic_key}/node:aware_demo.home.RoomState"
    enum_config_id = str(provider_delta_uuid("existing-graph-enum-update-drift"))

    typed_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=_semantic_dirty_diff(
            entries=(
                _enum_update_dirty_entry(
                    graph_semantic_key=graph_semantic_key,
                    enum_semantic_key=enum_semantic_key,
                    enum_config_id=enum_config_id,
                    enum_fqn="aware_demo.home.OtherState",
                    name="OtherState",
                    description="Drifted identity.",
                    semantic_scope_closure=_enum_scope_closure(
                        enum_fqn="aware_demo.home.OtherState",
                        enum_name="OtherState",
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
    handler_results = cast(
        Sequence[Mapping[str, object]],
        ontology_plan["operation_handler_results"],
    )
    blockers = cast(tuple[str, ...], handler_results[0]["blockers"])

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert ontology_plan["status"] == "ontology_execution_plan_blocked"
    assert "enum_update_enum_fqn_identity_changed" in blockers
    assert "enum_update_name_identity_changed" in blockers


def test_enum_option_create_update_and_delete_plan_function_calls() -> None:
    graph_semantic_key = "ocg:aware_demo"
    enum_semantic_key = f"{graph_semantic_key}/node:aware_demo.home.RoomState"
    option_semantic_key = f"{enum_semantic_key}/option:ready"
    enum_config_id = str(provider_delta_uuid("enum-option-parent"))
    enum_option_id = str(provider_delta_uuid("enum-option-ready"))
    delete_option_id = str(provider_delta_uuid("enum-option-archived"))

    typed_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=_semantic_dirty_diff(
            entries=(
                _enum_option_create_dirty_entry(
                    graph_semantic_key=graph_semantic_key,
                    enum_semantic_key=enum_semantic_key,
                    option_semantic_key=option_semantic_key,
                    enum_config_id=enum_config_id,
                    enum_option_id=enum_option_id,
                    label="Ready",
                    description="Ready for automation.",
                    position=0,
                    semantic_scope_closure=_enum_scope_closure(
                        enum_fqn="aware_demo.home.RoomState",
                        enum_name="RoomState",
                    ),
                ),
                _enum_option_update_dirty_entry(
                    graph_semantic_key=graph_semantic_key,
                    enum_semantic_key=enum_semantic_key,
                    option_semantic_key=f"{enum_semantic_key}/option:offline",
                    enum_config_id=enum_config_id,
                    enum_option_id=str(provider_delta_uuid("enum-option-offline")),
                    value="offline",
                    label="Offline",
                    description="Offline state.",
                    position=1,
                    semantic_scope_closure=_enum_scope_closure(
                        enum_fqn="aware_demo.home.RoomState",
                        enum_name="RoomState",
                    ),
                ),
                _enum_option_delete_dirty_entry(
                    graph_semantic_key=graph_semantic_key,
                    enum_semantic_key=enum_semantic_key,
                    option_semantic_key=f"{enum_semantic_key}/option:archived",
                    enum_config_id=enum_config_id,
                    enum_option_id=delete_option_id,
                    value="archived",
                    semantic_scope_closure=_enum_scope_closure(
                        enum_fqn="aware_demo.home.RoomState",
                        enum_name="RoomState",
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
    operations = cast(Sequence[Mapping[str, object]], typed_plan["typed_operations"])
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert typed_plan["typed_operation_count"] == 3
    assert [operation["provider_operation_type"] for operation in operations] == [
        "meta_ocg.enum_option.create",
        "meta_ocg.enum_option.update",
        "meta_ocg.enum_option.delete",
    ]
    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert [intent["function_ref"] for intent in intents] == [
        ENUM_CONFIG_CREATE_ENUM_OPTION_FUNCTION_REF,
        ENUM_OPTION_UPDATE_CONFIG_FUNCTION_REF,
        ENUM_CONFIG_DELETE_ENUM_OPTION_FUNCTION_REF,
    ]
    assert intents[0]["target_object_id"] == enum_config_id
    assert intents[0]["expected_result_object_id"] == enum_option_id
    assert intents[0]["target_projection_name"] == "ObjectConfigGraph"
    assert intents[0]["result_projection_name"] == "ObjectConfigGraph"
    assert intents[0]["kwargs"] == {
        "value": "ready",
        "label": "Ready",
        "description": "Ready for automation.",
        "position": 0,
    }
    assert intents[1]["kwargs"] == {
        "label": "Offline",
        "description": "Offline state.",
        "position": 1,
    }
    assert intents[2]["target_object_id"] == enum_config_id
    assert intents[2]["expected_result_object_id"] == delete_option_id
    assert intents[2]["target_projection_name"] == "ObjectConfigGraph"
    assert intents[2]["kwargs"] == {
        "value": "archived",
        "enum_option_id": delete_option_id,
    }


def test_enum_option_delete_uses_source_id_for_function_argument() -> None:
    graph_semantic_key = "ocg:aware_demo"
    enum_semantic_key = f"{graph_semantic_key}/node:aware_demo.home.RoomState"
    enum_config_receiver_id = str(
        provider_delta_uuid("enum-delete-enum-config-receiver")
    )
    enum_option_source_id = str(provider_delta_uuid("enum-delete-option-source"))
    enum_option_receiver_id = str(provider_delta_uuid("enum-delete-option-receiver"))
    delete_entry = _enum_option_delete_dirty_entry(
        graph_semantic_key=graph_semantic_key,
        enum_semantic_key=enum_semantic_key,
        option_semantic_key=f"{enum_semantic_key}/option:archived",
        enum_config_id=enum_config_receiver_id,
        enum_option_id=enum_option_receiver_id,
        value="archived",
        semantic_scope_closure=_enum_scope_closure(
            enum_fqn="aware_demo.home.RoomState",
            enum_name="RoomState",
        ),
    )
    delete_entry["semantic_source_object_id"] = enum_option_source_id
    payload = delete_entry["payload"]
    assert isinstance(payload, dict)
    payload["semantic_source_object_id"] = enum_option_source_id
    baseline_object = delete_entry["baseline_object"]
    assert isinstance(baseline_object, dict)
    baseline_object["semantic_source_object_id"] = enum_option_source_id
    baseline_object["enum_option_id"] = enum_option_source_id
    baseline_object["entity_id"] = enum_option_source_id
    dirty_diff = _semantic_dirty_diff(entries=(delete_entry,))

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
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])

    assert len(intents) == 1
    assert intents[0]["target_object_id"] == enum_config_receiver_id
    assert intents[0]["expected_result_object_id"] == enum_option_source_id
    assert intents[0]["kwargs"] == {
        "value": "archived",
        "enum_option_id": enum_option_source_id,
    }


def test_enum_option_delete_explicit_projection_overrides_object_inference() -> None:
    target_object_id = UUID(str(provider_delta_uuid("enum-delete-target-object")))
    index = SimpleNamespace(
        opg_by_hash={
            "ocg-hash": SimpleNamespace(
                id="opg:ocg",
                name="ObjectConfigGraph",
                projection_hash="ocg-hash",
            ),
            "narrow-hash": SimpleNamespace(
                id="opg:narrow",
                name="EnumOption",
                projection_hash="narrow-hash",
            ),
        },
    )

    projection_hash = _invocation_projection_hash_for_instance_intent(
        index=cast(object, index),
        intent={"target_projection_name": "ObjectConfigGraph"},
        target_object_id=target_object_id,
        default_projection_hash="default-hash",
        projection_hash_by_object_id={target_object_id: "narrow-hash"},
    )

    assert projection_hash == "narrow-hash"


def _semantic_dirty_diff(
    *,
    entries: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    return {
        "status": "semantic_dirty_diff_ready",
        "reason": "meta_ocg_dirty_diff_ready",
        "available": True,
        "blocked": False,
        "current_delta_fingerprint": "sha256:enum-create-existing-graph",
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


def _enum_create_dirty_entry(
    *,
    graph_semantic_key: str,
    enum_semantic_key: str,
    node_id: str,
    enum_config_id: str,
    values: tuple[str, ...],
    semantic_scope_closure: Mapping[str, object] | None = None,
) -> dict[str, object]:
    entry: dict[str, object] = {
        "entry_kind": "meta_ocg_semantic_dirty_entry",
        "entry_key": f"dirty:runtime_delta:1:{enum_semantic_key}",
        "semantic_key": enum_semantic_key,
        "source_delta_key": f"aware_meta.runtime_delta:{enum_semantic_key}",
        "source_refs": ("aware/home/model.aware",),
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "enum",
        "dirty_operation": "enum_create",
        "baseline_compare_status": "baseline_object_missing",
        "baseline_compare_operation": "create",
        "baseline_object_matched": False,
        "baseline_object_id": None,
        "baseline_object_kind": None,
        "graph_semantic_key": graph_semantic_key,
        "node_id": node_id,
        "node_key": "aware_demo.home.RoomState",
        "node_type": "enum",
        "entity_id": enum_config_id,
        "entity_name": "RoomState",
        "enum_fqn": "aware_demo.home.RoomState",
        "name": "RoomState",
        "description": "Home room lifecycle state.",
        "values": values,
        "payload": {
            "graph_semantic_key": graph_semantic_key,
            "node_id": node_id,
            "node_key": "aware_demo.home.RoomState",
            "node_type": "enum",
            "entity_id": enum_config_id,
            "entity_name": "RoomState",
            "enum_fqn": "aware_demo.home.RoomState",
            "description": "Home room lifecycle state.",
            "values": values,
        },
    }
    if semantic_scope_closure is not None:
        entry["semantic_scope_closure"] = dict(semantic_scope_closure)
    return entry


def _enum_update_dirty_entry(
    *,
    graph_semantic_key: str,
    enum_semantic_key: str,
    enum_config_id: str,
    enum_fqn: str = "aware_demo.home.RoomState",
    name: str = "RoomState",
    description: str | None,
    semantic_scope_closure: Mapping[str, object] | None = None,
) -> dict[str, object]:
    entry: dict[str, object] = {
        "entry_kind": "meta_ocg_semantic_dirty_entry",
        "entry_key": f"dirty:runtime_delta:1:{enum_semantic_key}",
        "semantic_key": enum_semantic_key,
        "source_delta_key": f"aware_meta.runtime_delta:{enum_semantic_key}",
        "source_refs": ("aware/home/model.aware",),
        "semantic_subject_type": "aware_meta.EnumConfig",
        "ontology_subject_kind": "enum",
        "dirty_operation": "enum_update",
        "baseline_compare_status": "baseline_object_changed",
        "baseline_compare_operation": "update",
        "baseline_object_matched": True,
        "baseline_object_id": enum_config_id,
        "baseline_object_kind": "enum",
        "graph_semantic_key": graph_semantic_key,
        "entity_id": enum_config_id,
        "entity_name": name,
        "enum_fqn": enum_fqn,
        "name": name,
        "description": description,
        "payload": {
            "graph_semantic_key": graph_semantic_key,
            "entity_id": enum_config_id,
            "entity_name": name,
            "enum_fqn": enum_fqn,
            "name": name,
            "description": description,
        },
        "baseline_object": {
            "semantic_key": enum_semantic_key,
            "object_kind": "enum",
            "entity_id": enum_config_id,
            "enum_fqn": "aware_demo.home.RoomState",
            "name": "RoomState",
            "description": "Home room lifecycle state.",
        },
    }
    if semantic_scope_closure is not None:
        entry["semantic_scope_closure"] = dict(semantic_scope_closure)
    return entry


def _enum_delete_dirty_entry(
    *,
    graph_semantic_key: str,
    enum_semantic_key: str,
    node_id: str,
    enum_config_id: str,
    semantic_scope_closure: Mapping[str, object] | None = None,
) -> dict[str, object]:
    entry: dict[str, object] = {
        "entry_kind": "meta_ocg_semantic_dirty_entry",
        "entry_key": f"dirty:runtime_delta:1:{enum_semantic_key}",
        "semantic_key": enum_semantic_key,
        "source_delta_key": f"aware_meta.runtime_delta:{enum_semantic_key}",
        "source_refs": ("aware/home/model.aware",),
        "semantic_subject_type": "aware_meta.EnumConfig",
        "ontology_subject_kind": "enum",
        "dirty_operation": "enum_delete",
        "baseline_compare_status": "baseline_object_deleted",
        "baseline_compare_operation": "delete",
        "baseline_object_matched": True,
        "baseline_object_id": enum_config_id,
        "baseline_object_kind": "enum",
        "graph_semantic_key": graph_semantic_key,
        "entity_id": enum_config_id,
        "entity_name": "RoomState",
        "enum_fqn": "aware_demo.home.RoomState",
        "name": "RoomState",
        "object_config_graph_node_id": node_id,
        "node_id": node_id,
        "node_key": "aware_demo.home.RoomState",
        "payload": {
            "graph_semantic_key": graph_semantic_key,
            "entity_id": enum_config_id,
            "entity_name": "RoomState",
            "enum_fqn": "aware_demo.home.RoomState",
            "name": "RoomState",
            "object_config_graph_node_id": node_id,
            "node_id": node_id,
            "node_key": "aware_demo.home.RoomState",
        },
        "baseline_object": {
            "semantic_key": enum_semantic_key,
            "object_kind": "enum",
            "graph_semantic_key": graph_semantic_key,
            "entity_id": enum_config_id,
            "enum_config_id": enum_config_id,
            "enum_fqn": "aware_demo.home.RoomState",
            "name": "RoomState",
            "object_config_graph_node_id": node_id,
            "node_id": node_id,
            "node_key": "aware_demo.home.RoomState",
        },
    }
    if semantic_scope_closure is not None:
        entry["semantic_scope_closure"] = dict(semantic_scope_closure)
    return entry


def _enum_option_create_dirty_entry(
    *,
    graph_semantic_key: str,
    enum_semantic_key: str,
    option_semantic_key: str,
    enum_config_id: str,
    enum_option_id: str,
    label: str | None,
    description: str | None,
    position: int,
    semantic_scope_closure: Mapping[str, object] | None = None,
) -> dict[str, object]:
    entry: dict[str, object] = {
        "entry_kind": "meta_ocg_semantic_dirty_entry",
        "entry_key": f"dirty:runtime_delta:1:{option_semantic_key}",
        "semantic_key": option_semantic_key,
        "source_delta_key": f"aware_meta.runtime_delta:{option_semantic_key}",
        "source_refs": ("aware/home/model.aware",),
        "semantic_subject_type": "aware_meta.EnumOption",
        "ontology_subject_kind": "enum_option",
        "dirty_operation": "enum_option_create",
        "baseline_compare_status": "baseline_object_missing",
        "baseline_compare_operation": "create",
        "baseline_object_matched": False,
        "baseline_object_id": None,
        "baseline_object_kind": None,
        "graph_semantic_key": graph_semantic_key,
        "enum_semantic_key": enum_semantic_key,
        "parent_semantic_key": enum_semantic_key,
        "enum_fqn": "aware_demo.home.RoomState",
        "enum_config_id": enum_config_id,
        "entity_id": enum_option_id,
        "enum_option_id": enum_option_id,
        "value": "ready",
        "label": label,
        "description": description,
        "position": position,
        "payload": {
            "graph_semantic_key": graph_semantic_key,
            "enum_semantic_key": enum_semantic_key,
            "parent_semantic_key": enum_semantic_key,
            "enum_fqn": "aware_demo.home.RoomState",
            "enum_config_id": enum_config_id,
            "entity_id": enum_option_id,
            "enum_option_id": enum_option_id,
            "value": "ready",
            "label": label,
            "description": description,
            "position": position,
        },
    }
    if semantic_scope_closure is not None:
        entry["semantic_scope_closure"] = dict(semantic_scope_closure)
    return entry


def _enum_option_update_dirty_entry(
    *,
    graph_semantic_key: str,
    enum_semantic_key: str,
    option_semantic_key: str,
    enum_config_id: str,
    enum_option_id: str,
    value: str,
    label: str | None,
    description: str | None,
    position: int,
    semantic_scope_closure: Mapping[str, object] | None = None,
) -> dict[str, object]:
    entry: dict[str, object] = {
        "entry_kind": "meta_ocg_semantic_dirty_entry",
        "entry_key": f"dirty:runtime_delta:2:{option_semantic_key}",
        "semantic_key": option_semantic_key,
        "source_delta_key": f"aware_meta.runtime_delta:{option_semantic_key}",
        "source_refs": ("aware/home/model.aware",),
        "semantic_subject_type": "aware_meta.EnumOption",
        "ontology_subject_kind": "enum_option",
        "dirty_operation": "enum_option_update",
        "baseline_compare_status": "baseline_object_changed",
        "baseline_compare_operation": "update",
        "baseline_object_matched": True,
        "baseline_object_id": enum_option_id,
        "baseline_object_kind": "enum_option",
        "graph_semantic_key": graph_semantic_key,
        "enum_semantic_key": enum_semantic_key,
        "parent_semantic_key": enum_semantic_key,
        "enum_fqn": "aware_demo.home.RoomState",
        "enum_config_id": enum_config_id,
        "entity_id": enum_option_id,
        "enum_option_id": enum_option_id,
        "value": value,
        "label": label,
        "description": description,
        "position": position,
        "payload": {
            "graph_semantic_key": graph_semantic_key,
            "enum_semantic_key": enum_semantic_key,
            "parent_semantic_key": enum_semantic_key,
            "enum_fqn": "aware_demo.home.RoomState",
            "enum_config_id": enum_config_id,
            "entity_id": enum_option_id,
            "enum_option_id": enum_option_id,
            "value": value,
            "label": label,
            "description": description,
            "position": position,
        },
        "baseline_object": {
            "semantic_key": option_semantic_key,
            "object_kind": "enum_option",
            "enum_config_id": enum_config_id,
            "entity_id": enum_option_id,
            "enum_option_id": enum_option_id,
            "value": value,
            "label": None,
            "description": None,
            "position": 0,
        },
    }
    if semantic_scope_closure is not None:
        entry["semantic_scope_closure"] = dict(semantic_scope_closure)
    return entry


def _enum_option_delete_dirty_entry(
    *,
    graph_semantic_key: str,
    enum_semantic_key: str,
    option_semantic_key: str,
    enum_config_id: str,
    enum_option_id: str,
    value: str,
    semantic_scope_closure: Mapping[str, object] | None = None,
) -> dict[str, object]:
    entry: dict[str, object] = {
        "entry_kind": "meta_ocg_semantic_dirty_entry",
        "entry_key": f"dirty:runtime_delta:3:{option_semantic_key}",
        "semantic_key": option_semantic_key,
        "source_delta_key": f"aware_meta.runtime_delta:{option_semantic_key}",
        "source_refs": ("aware/home/model.aware",),
        "semantic_subject_type": "aware_meta.EnumOption",
        "ontology_subject_kind": "enum_option",
        "dirty_operation": "enum_option_delete",
        "baseline_compare_status": "baseline_object_removed",
        "baseline_compare_operation": "delete",
        "baseline_object_matched": True,
        "baseline_object_id": enum_option_id,
        "baseline_object_kind": "enum_option",
        "graph_semantic_key": graph_semantic_key,
        "enum_semantic_key": enum_semantic_key,
        "parent_semantic_key": enum_semantic_key,
        "enum_fqn": "aware_demo.home.RoomState",
        "enum_config_id": enum_config_id,
        "entity_id": enum_option_id,
        "enum_option_id": enum_option_id,
        "value": value,
        "payload": {
            "graph_semantic_key": graph_semantic_key,
            "enum_semantic_key": enum_semantic_key,
            "parent_semantic_key": enum_semantic_key,
            "enum_fqn": "aware_demo.home.RoomState",
            "enum_config_id": enum_config_id,
            "entity_id": enum_option_id,
            "enum_option_id": enum_option_id,
            "value": value,
        },
        "baseline_object": {
            "semantic_key": option_semantic_key,
            "object_kind": "enum_option",
            "enum_config_id": enum_config_id,
            "entity_id": enum_option_id,
            "enum_option_id": enum_option_id,
            "value": value,
            "label": None,
            "description": None,
            "position": 2,
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


def _enum_scope_closure(
    *,
    enum_fqn: str,
    enum_name: str,
) -> Mapping[str, object]:
    enum_config = EnumConfig(
        id=provider_delta_uuid(f"enum-scope-closure:{enum_fqn}"),
        enum_fqn=enum_fqn,
        name=enum_name,
    )
    return build_meta_ocg_semantic_scope_closure(
        package_fqn_prefix="aware_demo",
        namespace_by_code_id={
            provider_delta_uuid("enum-scope-closure-code"): NamespacePath(
                package="aware_demo",
                namespace="home",
            ),
        },
        enum_configs=(enum_config,),
    ).evidence_payload()


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, Mapping)
    return dict(cast(Mapping[str, object], value))
