"""Strict contextual codecs for Workspace semantic dependency graph evidence."""

from __future__ import annotations

import json
from typing import Protocol, cast

from aware_code_semantic_contract_runtime import (
    ContentDigest,
    ContractViolation,
)

from .semantic_dependency_graph import (
    WorkspaceDependencyTargetResolution,
    WorkspaceFulfilledDependencyProductV3,
    WorkspaceSemanticMaterializationFailureEvidenceEntryV2,
    WorkspaceSemanticMaterializationGraph,
    WorkspaceSemanticMaterializationGraphExecutionBinding,
    WorkspaceSemanticMaterializationGraphPlanResult,
    WorkspaceSemanticMaterializationGraphResultV3,
    WorkspaceSemanticMaterializationLocalRootAssociation,
    WorkspaceSemanticMaterializationNodeExecutionBinding,
    WorkspaceSemanticMaterializationNodeResultEvidenceV3,
    WorkspaceSemanticMaterializationTerminalEvidenceContextV3,
    WorkspaceSemanticMaterializationTerminalFailureV3,
)
from .semantic_materialization_publication import (
    WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
)

_MAX_WIRE_BYTES = 8_000_000


class _WireValue(Protocol):
    def __post_init__(self) -> None: ...

    def to_wire(self) -> object: ...


def encode_workspace_dependency_target_resolution(
    value: WorkspaceDependencyTargetResolution,
) -> bytes:
    return _encode_exact(value, WorkspaceDependencyTargetResolution, "target")


def encode_workspace_semantic_materialization_node_execution_binding(
    value: WorkspaceSemanticMaterializationNodeExecutionBinding,
    *,
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
) -> bytes:
    if type(value) is not WorkspaceSemanticMaterializationNodeExecutionBinding:
        raise TypeError("node execution binding must be exact")
    if type(plan_result) is not WorkspaceSemanticMaterializationGraphPlanResult:
        raise TypeError("node execution binding plan result must be exact")
    plan_result.__post_init__()
    expected = WorkspaceSemanticMaterializationNodeExecutionBinding.create(
        graph=plan_result.graph,
        node_digest=value.node_digest,
        package=value.package,
        package_entry=value.package_entry,
        code_intent=value.code_intent,
        workspace_admitted_intent=value.workspace_admitted_intent,
        planning_context=value.planning_context,
        code_match=value.code_match,
        code_match_admission=value.code_match_admission,
        dependency_demand_set=value.dependency_demand_set,
        planning_input_digest=value.planning_input_digest,
        planning_demand_closure=value.planning_demand_closure,
        incoming_target_resolutions=value.incoming_target_resolutions,
        required_result_products=value.required_result_products,
    )
    if expected.binding_digest != value.binding_digest:
        raise ContractViolation("node execution binding differs from context")
    retained = tuple(
        item
        for item in plan_result.graph_execution_binding.ordered_node_bindings
        if item.node_digest == expected.node_digest
    )
    if len(retained) != 1:
        raise ContractViolation("node execution binding is absent from plan context")
    expected_wire = _encode_admitted_wire(expected.to_wire())
    retained_wire = _encode_admitted_wire(retained[0].to_wire())
    if expected_wire != retained_wire:
        raise ContractViolation("node execution binding differs from plan context")
    return retained_wire


def decode_workspace_semantic_materialization_node_execution_binding(
    wire: bytes,
    *,
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
    expected: WorkspaceSemanticMaterializationNodeExecutionBinding,
) -> WorkspaceSemanticMaterializationNodeExecutionBinding:
    if type(expected) is not WorkspaceSemanticMaterializationNodeExecutionBinding:
        raise TypeError("node execution binding expected value must be exact")
    if (
        encode_workspace_semantic_materialization_node_execution_binding(
            expected, plan_result=plan_result
        )
        != wire
    ):
        raise ContractViolation("node execution binding wire is not canonical")
    return expected


def encode_workspace_semantic_materialization_graph_execution_binding(
    value: WorkspaceSemanticMaterializationGraphExecutionBinding,
    *,
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
) -> bytes:
    if type(value) is not WorkspaceSemanticMaterializationGraphExecutionBinding:
        raise TypeError("graph execution binding must be exact")
    if type(plan_result) is not WorkspaceSemanticMaterializationGraphPlanResult:
        raise TypeError("graph execution binding plan result must be exact")
    plan_result.__post_init__()
    expected = WorkspaceSemanticMaterializationGraphExecutionBinding.create(
        graph=plan_result.graph,
        ordered_node_bindings=value.ordered_node_bindings,
    )
    if expected.binding_digest != value.binding_digest:
        raise ContractViolation("graph execution binding differs from context")
    expected_wire = _encode_admitted_wire(expected.to_wire())
    retained_wire = _encode_admitted_wire(plan_result.graph_execution_binding.to_wire())
    if expected_wire != retained_wire:
        raise ContractViolation("graph execution binding differs from plan context")
    return retained_wire


def decode_workspace_semantic_materialization_graph_execution_binding(
    wire: bytes,
    *,
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
    expected: WorkspaceSemanticMaterializationGraphExecutionBinding,
) -> WorkspaceSemanticMaterializationGraphExecutionBinding:
    if type(expected) is not WorkspaceSemanticMaterializationGraphExecutionBinding:
        raise TypeError("graph execution binding expected value must be exact")
    if (
        encode_workspace_semantic_materialization_graph_execution_binding(
            expected, plan_result=plan_result
        )
        != wire
    ):
        raise ContractViolation("graph execution binding wire is not canonical")
    return expected


def encode_workspace_semantic_materialization_graph_plan_result(
    value: WorkspaceSemanticMaterializationGraphPlanResult,
) -> bytes:
    if type(value) is not WorkspaceSemanticMaterializationGraphPlanResult:
        raise TypeError("graph plan result must be exact")
    expected = WorkspaceSemanticMaterializationGraphPlanResult.create(
        selection_resolution=value.selection_resolution,
        graph=value.graph,
        graph_plan_admission=value.graph_plan_admission,
        graph_execution_binding=value.graph_execution_binding,
        timing_entries=value.timing_entries,
        counter_entries=value.counter_entries,
    )
    if expected.planning_result_digest != value.planning_result_digest:
        raise ContractViolation("graph plan result differs from context")
    return _encode_admitted_wire(expected.to_wire())


def decode_workspace_semantic_materialization_graph_plan_result(
    wire: bytes,
    *,
    expected: WorkspaceSemanticMaterializationGraphPlanResult,
) -> WorkspaceSemanticMaterializationGraphPlanResult:
    if type(expected) is not WorkspaceSemanticMaterializationGraphPlanResult:
        raise TypeError("graph plan result expected value must be exact")
    if encode_workspace_semantic_materialization_graph_plan_result(expected) != wire:
        raise ContractViolation("graph plan result wire is not canonical")
    return expected


def decode_workspace_dependency_target_resolution(
    wire: bytes,
    *,
    expected: WorkspaceDependencyTargetResolution,
) -> WorkspaceDependencyTargetResolution:
    if type(expected) is not WorkspaceDependencyTargetResolution:
        raise TypeError("target expected value must be exact")
    return _canonical_result(wire, expected, "target")


def encode_workspace_semantic_materialization_head_reread_evidence_v2(
    value: WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
) -> bytes:
    return _encode_exact(
        value,
        WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
        "head_reread_v2",
    )


def decode_workspace_semantic_materialization_head_reread_evidence_v2(
    wire: bytes,
    *,
    expected: WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
) -> WorkspaceSemanticMaterializationHeadRereadEvidenceV3:
    if type(expected) is not WorkspaceSemanticMaterializationHeadRereadEvidenceV3:
        raise TypeError("head reread V2 expected value must be exact")
    if (
        encode_workspace_semantic_materialization_head_reread_evidence_v2(expected)
        != wire
    ):
        raise ContractViolation("head reread V2 wire is not canonical")
    return expected


def encode_workspace_fulfilled_dependency_product_v2(
    value: WorkspaceFulfilledDependencyProductV3,
    *,
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
) -> bytes:
    if type(value) is not WorkspaceFulfilledDependencyProductV3:
        raise TypeError("fulfilled product V2 must be exact")
    expected = WorkspaceFulfilledDependencyProductV3.create(
        plan_result=plan_result,
        consumer_node_digest=value.consumer_node_digest,
        target_node_digest=value.target_node_digest,
        target_resolution=value.target_resolution,
        head_h1=value.head_h1_reread_evidence,
        head_h2=value.head_h2_reread_evidence,
        consumed_body_coordinate=value.consumed_body_coordinate,
    )
    if _encode_admitted_wire(expected.to_wire()) != _encode_admitted_wire(
        value.to_wire()
    ):
        raise ContractViolation("fulfilled product V2 differs from context")
    return _encode_admitted_wire(expected.to_wire())


def decode_workspace_fulfilled_dependency_product_v2(
    wire: bytes,
    *,
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
    expected: WorkspaceFulfilledDependencyProductV3,
) -> WorkspaceFulfilledDependencyProductV3:
    if type(expected) is not WorkspaceFulfilledDependencyProductV3:
        raise TypeError("fulfilled product V2 expected value must be exact")
    if (
        encode_workspace_fulfilled_dependency_product_v2(
            expected,
            plan_result=plan_result,
        )
        != wire
    ):
        raise ContractViolation("fulfilled product V2 wire is not canonical")
    return expected


def encode_workspace_semantic_materialization_failure_evidence_entry_v2(
    value: WorkspaceSemanticMaterializationFailureEvidenceEntryV2,
) -> bytes:
    return _encode_exact(
        value,
        WorkspaceSemanticMaterializationFailureEvidenceEntryV2,
        "failure_entry_v2",
    )


def decode_workspace_semantic_materialization_failure_evidence_entry_v2(
    wire: bytes,
    *,
    expected: WorkspaceSemanticMaterializationFailureEvidenceEntryV2,
) -> WorkspaceSemanticMaterializationFailureEvidenceEntryV2:
    if type(expected) is not WorkspaceSemanticMaterializationFailureEvidenceEntryV2:
        raise TypeError("failure entry V2 expected value must be exact")
    if (
        encode_workspace_semantic_materialization_failure_evidence_entry_v2(expected)
        != wire
    ):
        raise ContractViolation("failure entry V2 wire is not canonical")
    return expected


def encode_workspace_semantic_materialization_terminal_failure_v2(
    value: WorkspaceSemanticMaterializationTerminalFailureV3,
    *,
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
    evidence_context: WorkspaceSemanticMaterializationTerminalEvidenceContextV3,
) -> bytes:
    if type(value) is not WorkspaceSemanticMaterializationTerminalFailureV3:
        raise TypeError("terminal failure V2 must be exact")
    if (
        type(evidence_context)
        is not WorkspaceSemanticMaterializationTerminalEvidenceContextV3
    ):
        raise TypeError("terminal failure V2 evidence context must be exact")
    expected = WorkspaceSemanticMaterializationTerminalFailureV3.create(
        plan_result=plan_result,
        terminal_node_digest=value.terminal_node_digest,
        terminal_stage=value.terminal_stage,
        failure_code=value.failure_code,
        ordered_completed_fulfilled_products=value.ordered_completed_fulfilled_products,
        evidence_context=evidence_context,
    )
    if _encode_admitted_wire(expected.to_wire()) != _encode_admitted_wire(
        value.to_wire()
    ):
        raise ContractViolation("terminal failure V2 differs from context")
    return _encode_admitted_wire(expected.to_wire())


def decode_workspace_semantic_materialization_terminal_failure_v2(
    wire: bytes,
    *,
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
    expected: WorkspaceSemanticMaterializationTerminalFailureV3,
    evidence_context: WorkspaceSemanticMaterializationTerminalEvidenceContextV3,
) -> WorkspaceSemanticMaterializationTerminalFailureV3:
    if type(expected) is not WorkspaceSemanticMaterializationTerminalFailureV3:
        raise TypeError("terminal failure V2 expected value must be exact")
    if (
        encode_workspace_semantic_materialization_terminal_failure_v2(
            expected,
            plan_result=plan_result,
            evidence_context=evidence_context,
        )
        != wire
    ):
        raise ContractViolation("terminal failure V2 wire is not canonical")
    return expected


def encode_workspace_semantic_materialization_node_result_evidence_v2(
    value: WorkspaceSemanticMaterializationNodeResultEvidenceV3,
    *,
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
) -> bytes:
    if type(value) is not WorkspaceSemanticMaterializationNodeResultEvidenceV3:
        raise TypeError("node result evidence V2 must be exact")
    expected = WorkspaceSemanticMaterializationNodeResultEvidenceV3.create(
        plan_result=plan_result,
        node_digest=value.node_digest,
        outcome=value.outcome,
        execution_input_closure_digest=value.execution_input_closure_digest,
        ordered_fulfilled_products=value.ordered_fulfilled_products,
        package_head_reread_evidence=value.package_head_reread_evidence,
        publication_receipt=value.publication_receipt,
        session_source_evidence=value.session_source_evidence,
        session_event_reread_evidence=value.session_event_reread_evidence,
        session_fanout_receipt=value.session_fanout_receipt,
    )
    if _encode_admitted_wire(expected.to_wire()) != _encode_admitted_wire(
        value.to_wire()
    ):
        raise ContractViolation("node result evidence V2 differs from context")
    return _encode_admitted_wire(expected.to_wire())


def decode_workspace_semantic_materialization_node_result_evidence_v2(
    wire: bytes,
    *,
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
    expected: WorkspaceSemanticMaterializationNodeResultEvidenceV3,
) -> WorkspaceSemanticMaterializationNodeResultEvidenceV3:
    if type(expected) is not WorkspaceSemanticMaterializationNodeResultEvidenceV3:
        raise TypeError("node result evidence V2 expected value must be exact")
    if (
        encode_workspace_semantic_materialization_node_result_evidence_v2(
            expected, plan_result=plan_result
        )
        != wire
    ):
        raise ContractViolation("node result evidence V2 wire is not canonical")
    return expected


def encode_workspace_semantic_materialization_graph_result_v2(
    value: WorkspaceSemanticMaterializationGraphResultV3,
    *,
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
) -> bytes:
    if type(value) is not WorkspaceSemanticMaterializationGraphResultV3:
        raise TypeError("graph result V2 must be exact")
    expected = WorkspaceSemanticMaterializationGraphResultV3.create(
        plan_result=plan_result,
        status=value.status,
        ordered_node_results=value.ordered_node_results,
        terminal_failure=value.terminal_failure,
        ordered_fulfilled_products=value.ordered_fulfilled_products,
        counter_entries=value.counter_entries,
    )
    if _encode_admitted_wire(expected.to_wire()) != _encode_admitted_wire(
        value.to_wire()
    ):
        raise ContractViolation("graph result V2 differs from context")
    return _encode_admitted_wire(expected.to_wire())


def decode_workspace_semantic_materialization_graph_result_v2(
    wire: bytes,
    *,
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
    expected: WorkspaceSemanticMaterializationGraphResultV3,
) -> WorkspaceSemanticMaterializationGraphResultV3:
    if type(expected) is not WorkspaceSemanticMaterializationGraphResultV3:
        raise TypeError("graph result V2 expected value must be exact")
    if (
        encode_workspace_semantic_materialization_graph_result_v2(
            expected, plan_result=plan_result
        )
        != wire
    ):
        raise ContractViolation("graph result V2 wire is not canonical")
    return expected


def encode_workspace_semantic_materialization_graph(
    value: WorkspaceSemanticMaterializationGraph,
    *,
    local_root_associations: tuple[
        WorkspaceSemanticMaterializationLocalRootAssociation, ...
    ],
) -> bytes:
    if type(value) is not WorkspaceSemanticMaterializationGraph:
        raise TypeError("graph must be exact")
    value.validate_local_root_context(local_root_associations)
    return _encode_admitted_wire(value.to_wire())


def decode_workspace_semantic_materialization_graph(
    wire: bytes,
    *,
    expected: WorkspaceSemanticMaterializationGraph,
    local_root_associations: tuple[
        WorkspaceSemanticMaterializationLocalRootAssociation, ...
    ],
) -> WorkspaceSemanticMaterializationGraph:
    if type(expected) is not WorkspaceSemanticMaterializationGraph:
        raise TypeError("graph expected value must be exact")
    if (
        encode_workspace_semantic_materialization_graph(
            expected, local_root_associations=local_root_associations
        )
        != wire
    ):
        raise ContractViolation("graph wire is not canonical")
    return expected


def _encode_exact[T: _WireValue](value: object, expected: type[T], path: str) -> bytes:
    if type(value) is not expected:
        raise TypeError(f"{path} must be exact {expected.__name__}")
    admitted = cast(T, value)
    admitted.__post_init__()
    return _encode_admitted_wire(admitted.to_wire())


def _canonical_result[T: _WireValue](wire: bytes, value: T, path: str) -> T:
    if _encode_admitted_wire(value.to_wire()) != wire:
        raise ContractViolation(f"{path} wire is not canonical")
    return value


def _encode_admitted_wire(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _unchecked_value[T](expected: type[T], **fields: object) -> T:
    result = object.__new__(expected)
    for name, value in fields.items():
        object.__setattr__(result, name, value)
    return result


def _decode_object(wire: bytes, keys: set[str], path: str) -> dict[str, object]:
    if type(wire) is not bytes:
        raise TypeError("wire must be exact bytes")
    if not wire or len(wire) > _MAX_WIRE_BYTES:
        raise ContractViolation("wire size unsupported")
    try:
        parsed = json.loads(wire.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractViolation("wire is not JSON") from error
    return _object(parsed, keys, path)


def _object_value(value: object, path: str) -> dict[str, object]:
    if type(value) is not dict:
        raise TypeError(f"{path} must be exact object")
    return cast(dict[str, object], value)


def _object(value: object, keys: set[str], path: str) -> dict[str, object]:
    result = _object_value(value, path)
    if any(type(key) is not str for key in result) or set(result) != keys:
        raise ContractViolation(f"{path} fields differ")
    return result


def _contract(root: dict[str, object], expected: str, path: str) -> None:
    if _text(root["contract"], f"{path}.contract") != expected:
        raise ContractViolation(f"{path} contract unsupported")


def _list(value: object, path: str) -> list[object]:
    if type(value) is not list:
        raise TypeError(f"{path} must be exact list")
    return cast(list[object], value)


def _text(value: object, path: str) -> str:
    if type(value) is not str or not value or any(char.isspace() for char in value):
        raise TypeError(f"{path} must be nonempty token text")
    return value


def _optional_text(value: object, path: str) -> str | None:
    return None if value is None else _text(value, path)


def _integer(value: object, path: str) -> int:
    if type(value) is not int or value < 0:
        raise TypeError(f"{path} must be exact nonnegative integer")
    return value


def _digest(value: object, path: str) -> ContentDigest:
    return ContentDigest.of_wire(value, path)


__all__ = [
    "decode_workspace_dependency_target_resolution",
    "decode_workspace_fulfilled_dependency_product_v2",
    "decode_workspace_semantic_materialization_failure_evidence_entry_v2",
    "decode_workspace_semantic_materialization_graph",
    "decode_workspace_semantic_materialization_graph_execution_binding",
    "decode_workspace_semantic_materialization_graph_plan_result",
    "decode_workspace_semantic_materialization_graph_result_v2",
    "decode_workspace_semantic_materialization_head_reread_evidence_v2",
    "decode_workspace_semantic_materialization_node_execution_binding",
    "decode_workspace_semantic_materialization_node_result_evidence_v2",
    "decode_workspace_semantic_materialization_terminal_failure_v2",
    "encode_workspace_dependency_target_resolution",
    "encode_workspace_fulfilled_dependency_product_v2",
    "encode_workspace_semantic_materialization_failure_evidence_entry_v2",
    "encode_workspace_semantic_materialization_graph",
    "encode_workspace_semantic_materialization_graph_execution_binding",
    "encode_workspace_semantic_materialization_graph_plan_result",
    "encode_workspace_semantic_materialization_graph_result_v2",
    "encode_workspace_semantic_materialization_head_reread_evidence_v2",
    "encode_workspace_semantic_materialization_node_execution_binding",
    "encode_workspace_semantic_materialization_node_result_evidence_v2",
    "encode_workspace_semantic_materialization_terminal_failure_v2",
]
