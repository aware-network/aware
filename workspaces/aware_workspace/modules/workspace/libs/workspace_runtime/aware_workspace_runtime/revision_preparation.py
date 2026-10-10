"""Pure zero-write Workspace revision-state and candidate preparation."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from typing import cast

from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticContractRef,
    canonical_json_bytes,
)

from .revision_preparation_admission import (
    WorkspaceMaterializationGraphExecutionAdmissionCapability,
    WorkspaceRevisionPreparationAdmissionError,
    WorkspaceRevisionPreparationContextCapability,
    _verify_workspace_revision_preparation_context_stage,
    verify_workspace_materialization_graph_execution_admission,
)
from .revision_preparation_contracts import (
    WorkspaceMaterializationGraphExecutionAdmission,
    WorkspaceRevisionCandidate,
    WorkspaceRevisionCandidatePredecessor,
    WorkspaceRevisionPackageMembershipTransitionSet,
    WorkspaceRevisionPredecessorAdmission,
    WorkspaceRevisionPreparationEvidence,
    WorkspaceRevisionPreparedPackagePin,
    WorkspaceRevisionSelectionScopeAdmission,
    WorkspaceRevisionSourceClosure,
    WorkspaceRevisionSourceClosureAdmission,
    WorkspaceRevisionSourcePackageEntry,
    WorkspaceRevisionState,
)
from .semantic_dependency_graph import (
    WorkspaceSemanticMaterializationGraphPlanResult,
    WorkspaceSemanticMaterializationGraphResultV3,
)


@dataclass(frozen=True, slots=True)
class WorkspaceRevisionPreparationResult:
    """Nonportable return from one contextual zero-write preparation."""

    state: WorkspaceRevisionState | None
    candidate: WorkspaceRevisionCandidate | None
    evidence: WorkspaceRevisionPreparationEvidence

    def __post_init__(self) -> None:
        if type(self.evidence) is not WorkspaceRevisionPreparationEvidence:
            raise TypeError("preparation result evidence must be exact")
        self.evidence.canonical_bytes()
        if self.evidence.outcome == "candidate_prepared":
            if (
                type(self.state) is not WorkspaceRevisionState
                or type(self.candidate) is not WorkspaceRevisionCandidate
                or self.state.state_digest != self.evidence.derived_state_digest
                or self.candidate.candidate_digest != self.evidence.candidate_digest
                or self.candidate.state is not self.state
            ):
                raise WorkspaceRevisionPreparationAdmissionError(
                    "candidate preparation result is incomplete"
                )
        elif self.evidence.outcome == "revision_unchanged":
            if (
                type(self.state) is not WorkspaceRevisionState
                or self.candidate is not None
                or self.state.state_digest != self.evidence.derived_state_digest
            ):
                raise WorkspaceRevisionPreparationAdmissionError(
                    "unchanged preparation result is incomplete"
                )
        elif self.state is not None or self.candidate is not None:
            raise WorkspaceRevisionPreparationAdmissionError(
                "refused preparation cannot carry state or candidate"
            )


def _merge_workspace_revision_source_overlay(
    *,
    predecessor_entries: tuple[WorkspaceRevisionSourcePackageEntry, ...],
    replacements: tuple[WorkspaceRevisionSourcePackageEntry, ...],
    removed_lineages: frozenset[str],
) -> tuple[tuple[WorkspaceRevisionSourcePackageEntry, ...], int]:
    """Return one canonical linear source overlay and its exact visit count."""

    if type(predecessor_entries) is not tuple or type(replacements) is not tuple:
        raise TypeError("source overlay inputs must be exact tuples")
    if type(removed_lineages) is not frozenset:
        raise TypeError("removed source lineages must be exact frozenset")
    for collection, label in (
        (predecessor_entries, "predecessor"),
        (replacements, "replacement"),
    ):
        if any(
            type(item) is not WorkspaceRevisionSourcePackageEntry for item in collection
        ):
            raise TypeError(f"{label} source entry must be exact")
        keys = tuple(item.package_lineage_ref.encode() for item in collection)
        if any(left >= right for left, right in pairwise(keys)):
            raise WorkspaceRevisionPreparationAdmissionError(
                f"{label} source entries must be uniquely ordered"
            )
    replacement_lineages = {item.package_lineage_ref for item in replacements}
    excluded_lineages = replacement_lineages | removed_lineages
    left_index = 0
    right_index = 0
    members_visited = 0
    merged: list[WorkspaceRevisionSourcePackageEntry] = []
    while left_index < len(predecessor_entries) or right_index < len(replacements):
        if (
            left_index < len(predecessor_entries)
            and predecessor_entries[left_index].package_lineage_ref
            in excluded_lineages
        ):
            left_index += 1
            members_visited += 1
            continue
        if right_index == len(replacements):
            merged.append(predecessor_entries[left_index])
            left_index += 1
            members_visited += 1
            continue
        if left_index == len(predecessor_entries):
            merged.append(replacements[right_index])
            right_index += 1
            members_visited += 1
            continue
        left = predecessor_entries[left_index]
        right = replacements[right_index]
        left_key = left.package_lineage_ref.encode()
        right_key = right.package_lineage_ref.encode()
        if left_key < right_key:
            merged.append(left)
            left_index += 1
            members_visited += 1
        elif right_key < left_key:
            merged.append(right)
            right_index += 1
            members_visited += 1
        else:
            raise WorkspaceRevisionPreparationAdmissionError(
                "retained and replacement source entries collide"
            )
    return tuple(merged), members_visited


def _merge_prepared_pin_overlay(
    *,
    predecessor_pins: tuple[WorkspaceRevisionPreparedPackagePin, ...],
    replacements: tuple[WorkspaceRevisionPreparedPackagePin, ...],
    selected_lineages: frozenset[str],
    removed_lineages: frozenset[str],
) -> tuple[tuple[WorkspaceRevisionPreparedPackagePin, ...], int]:
    """Return one canonical linear merge and its exact member-visit count."""

    if type(predecessor_pins) is not tuple or type(replacements) is not tuple:
        raise TypeError("pin overlay inputs must be exact tuples")
    if (
        type(selected_lineages) is not frozenset
        or type(removed_lineages) is not frozenset
    ):
        raise TypeError("pin overlay lineage sets must be exact frozensets")
    for collection, label in (
        (predecessor_pins, "predecessor"),
        (replacements, "replacement"),
    ):
        if any(
            type(item) is not WorkspaceRevisionPreparedPackagePin
            for item in collection
        ):
            raise TypeError(f"{label} prepared pin must be exact")
        keys = tuple(item.slot.ordering_key() for item in collection)
        if any(left >= right for left, right in pairwise(keys)):
            raise WorkspaceRevisionPreparationAdmissionError(
                f"{label} prepared pins must be uniquely ordered"
            )
    excluded_lineages = selected_lineages | removed_lineages
    left_index = 0
    right_index = 0
    members_visited = 0
    merged: list[WorkspaceRevisionPreparedPackagePin] = []
    while left_index < len(predecessor_pins) or right_index < len(replacements):
        if (
            left_index < len(predecessor_pins)
            and predecessor_pins[left_index].slot.package_lineage_ref
            in excluded_lineages
        ):
            left_index += 1
            members_visited += 1
            continue
        if right_index == len(replacements):
            merged.append(predecessor_pins[left_index])
            left_index += 1
            members_visited += 1
            continue
        if left_index == len(predecessor_pins):
            merged.append(replacements[right_index])
            right_index += 1
            members_visited += 1
            continue
        left = predecessor_pins[left_index]
        right = replacements[right_index]
        left_key = left.slot.ordering_key()
        right_key = right.slot.ordering_key()
        if left_key < right_key:
            merged.append(left)
            left_index += 1
            members_visited += 1
        elif right_key < left_key:
            merged.append(right)
            right_index += 1
            members_visited += 1
        else:
            raise WorkspaceRevisionPreparationAdmissionError(
                "retained and selected pins collide"
            )
    return tuple(merged), members_visited


def _slot_lookup_key(
    lineage: str, role: str, contract: SemanticContractRef
) -> tuple[str, str, str, str, str]:
    return (
        lineage,
        role,
        contract.key,
        contract.version,
        contract.schema_digest.value,
    )


def _refusal(
    *,
    code: str,
    operation_authority_digest: str,
    workspace_ref: str,
    branch_ref: str,
    selection_scope: str,
    transitions: WorkspaceRevisionPackageMembershipTransitionSet,
    plan_wire: bytes,
    result_wire: bytes,
    result: WorkspaceSemanticMaterializationGraphResultV3,
    predecessor_digest: str | None = None,
    source_digest: str | None = None,
    selection_digest: str | None = None,
    graph_admission: WorkspaceMaterializationGraphExecutionAdmission | None = None,
) -> WorkspaceRevisionPreparationResult:
    evidence = WorkspaceRevisionPreparationEvidence.create(
        outcome="preparation_refused",
        operation_authority_digest=operation_authority_digest,
        workspace_ref=workspace_ref,
        branch_ref=branch_ref,
        predecessor_admission_digest=predecessor_digest,
        source_closure_admission_digest=source_digest,
        selection_scope=selection_scope,
        selection_scope_admission_digest=selection_digest,
        graph_execution_admission_digest=(
            None if graph_admission is None else graph_admission.admission_digest
        ),
        execution_provenance_lifecycle=(
            None
            if graph_admission is None
            else graph_admission.execution_provenance_lifecycle
        ),
        plan_body_sha256=ContentDigest.of_bytes(plan_wire).value,
        plan_body_size_bytes=len(plan_wire),
        graph_result_body_sha256=ContentDigest.of_bytes(result_wire).value,
        graph_result_body_size_bytes=len(result_wire),
        graph_result_digest=result.result_digest.value,
        package_membership_transition_set_digest=transitions.set_digest,
        derived_state_digest=None,
        candidate_digest=None,
        refusal_code=code,
        provider_execution_count=0,
        external_read_count=0,
        external_write_count=0,
        ontology_call_count=0,
        meta_oig_call_count=0,
    )
    return WorkspaceRevisionPreparationResult(None, None, evidence)


def prepare_workspace_revision(
    *,
    owner: object,
    operation_authority_digest: str,
    workspace_ref: str,
    branch_ref: str,
    context_capability: WorkspaceRevisionPreparationContextCapability,
    predecessor: WorkspaceRevisionPredecessorAdmission,
    predecessor_state: WorkspaceRevisionState | None,
    predecessor_source_closure: WorkspaceRevisionSourceClosure | None,
    source_closure: WorkspaceRevisionSourceClosure,
    source_admission: WorkspaceRevisionSourceClosureAdmission,
    selection: WorkspaceRevisionSelectionScopeAdmission,
    transitions: WorkspaceRevisionPackageMembershipTransitionSet,
    graph_execution: object,
    graph_admission_capability: WorkspaceMaterializationGraphExecutionAdmissionCapability,
    graph_admission: WorkspaceMaterializationGraphExecutionAdmission,
    plan: WorkspaceSemanticMaterializationGraphPlanResult,
    graph_result: WorkspaceSemanticMaterializationGraphResultV3,
) -> WorkspaceRevisionPreparationResult:
    """Prepare one exact revision candidate without reads, writes or execution."""

    exact_types = (
        (predecessor, WorkspaceRevisionPredecessorAdmission, "predecessor"),
        (source_closure, WorkspaceRevisionSourceClosure, "source_closure"),
        (source_admission, WorkspaceRevisionSourceClosureAdmission, "source_admission"),
        (selection, WorkspaceRevisionSelectionScopeAdmission, "selection"),
        (transitions, WorkspaceRevisionPackageMembershipTransitionSet, "transitions"),
        (
            graph_admission,
            WorkspaceMaterializationGraphExecutionAdmission,
            "graph_admission",
        ),
        (plan, WorkspaceSemanticMaterializationGraphPlanResult, "plan"),
        (graph_result, WorkspaceSemanticMaterializationGraphResultV3, "graph_result"),
    )
    for value, expected, path in exact_types:
        if type(value) is not expected:
            raise TypeError(f"{path} must be exact {expected.__name__}")
    if (
        predecessor_state is not None
        and type(predecessor_state) is not WorkspaceRevisionState
    ):
        raise TypeError(
            "predecessor_state must be exact WorkspaceRevisionState or null"
        )
    plan_wire = canonical_json_bytes(plan.to_wire())
    result_wire = canonical_json_bytes(graph_result.to_wire())

    if (
        predecessor.operation_authority_digest != operation_authority_digest
        or predecessor.workspace_ref != workspace_ref
        or predecessor.branch_ref != branch_ref
    ):
        return _refusal(
            code="operation_currentness_mismatch",
            operation_authority_digest=operation_authority_digest,
            workspace_ref=workspace_ref,
            branch_ref=branch_ref,
            selection_scope=selection.scope,
            transitions=transitions,
            plan_wire=plan_wire,
            result_wire=result_wire,
            result=graph_result,
        )

    def verify_context_stage(stage: str) -> None:
        _verify_workspace_revision_preparation_context_stage(
            stage=stage,
            capability=context_capability,
            owner=owner,
            operation_authority_digest=operation_authority_digest,
            workspace_ref=workspace_ref,
            branch_ref=branch_ref,
            predecessor=predecessor,
            predecessor_state=predecessor_state,
            predecessor_source_closure=predecessor_source_closure,
            source_closure=source_closure,
            source_admission=source_admission,
            selection=selection,
            transitions=transitions,
        )

    try:
        verify_context_stage("predecessor")
    except (TypeError, WorkspaceRevisionPreparationAdmissionError):
        return _refusal(
            code="predecessor_authority_unavailable",
            operation_authority_digest=operation_authority_digest,
            workspace_ref=workspace_ref,
            branch_ref=branch_ref,
            selection_scope=selection.scope,
            transitions=transitions,
            plan_wire=plan_wire,
            result_wire=result_wire,
            result=graph_result,
        )
    try:
        verify_context_stage("source")
    except (TypeError, WorkspaceRevisionPreparationAdmissionError):
        return _refusal(
            code="source_closure_not_admitted",
            operation_authority_digest=operation_authority_digest,
            workspace_ref=workspace_ref,
            branch_ref=branch_ref,
            selection_scope=selection.scope,
            transitions=transitions,
            plan_wire=plan_wire,
            result_wire=result_wire,
            result=graph_result,
            predecessor_digest=predecessor.admission_digest,
        )
    try:
        verify_context_stage("selection")
    except (TypeError, WorkspaceRevisionPreparationAdmissionError):
        return _refusal(
            code="selection_scope_not_admitted",
            operation_authority_digest=operation_authority_digest,
            workspace_ref=workspace_ref,
            branch_ref=branch_ref,
            selection_scope=selection.scope,
            transitions=transitions,
            plan_wire=plan_wire,
            result_wire=result_wire,
            result=graph_result,
            predecessor_digest=predecessor.admission_digest,
            source_digest=source_admission.admission_digest,
        )
    try:
        verify_workspace_materialization_graph_execution_admission(
            capability=graph_admission_capability,
            admission=graph_admission,
            execution=graph_execution,
            owner=owner,
            plan=plan,
            result=graph_result,
        )
    except (TypeError, WorkspaceRevisionPreparationAdmissionError):
        return _refusal(
            code="graph_execution_provenance_unavailable",
            operation_authority_digest=operation_authority_digest,
            workspace_ref=workspace_ref,
            branch_ref=branch_ref,
            selection_scope=selection.scope,
            transitions=transitions,
            plan_wire=plan_wire,
            result_wire=result_wire,
            result=graph_result,
            predecessor_digest=predecessor.admission_digest,
            source_digest=source_admission.admission_digest,
            selection_digest=selection.admission_digest,
        )
    if graph_result.status != "succeeded":
        return _refusal(
            code="graph_not_succeeded",
            operation_authority_digest=operation_authority_digest,
            workspace_ref=workspace_ref,
            branch_ref=branch_ref,
            selection_scope=selection.scope,
            transitions=transitions,
            plan_wire=plan_wire,
            result_wire=result_wire,
            result=graph_result,
            graph_admission=graph_admission,
            predecessor_digest=predecessor.admission_digest,
            source_digest=source_admission.admission_digest,
            selection_digest=selection.admission_digest,
        )
    if (
        graph_admission.operation_authority_digest != operation_authority_digest
        or selection.graph_digest != plan.graph.graph_digest.value
        or graph_result.graph_digest != plan.graph.graph_digest
    ):
        return _refusal(
            code="graph_coverage_mismatch",
            operation_authority_digest=operation_authority_digest,
            workspace_ref=workspace_ref,
            branch_ref=branch_ref,
            selection_scope=selection.scope,
            transitions=transitions,
            plan_wire=plan_wire,
            result_wire=result_wire,
            result=graph_result,
            graph_admission=graph_admission,
            predecessor_digest=predecessor.admission_digest,
            source_digest=source_admission.admission_digest,
            selection_digest=selection.admission_digest,
        )

    entries_by_lineage = {
        item.package_lineage_ref: item for item in source_closure.ordered_packages
    }
    entries_by_package_ref: dict[str, list[WorkspaceRevisionSourcePackageEntry]] = {}
    for item in source_closure.ordered_packages:
        entries_by_package_ref.setdefault(item.current_package_ref, []).append(item)
    for transition in transitions.ordered_authorities:
        entry = entries_by_lineage.get(transition.package_lineage_ref)
        if (
            transition.operation_authority_digest != operation_authority_digest
            or transition.workspace_ref != workspace_ref
            or (
                transition.disposition == "present"
                and (
                    entry is None
                    or entry.source_after_state_authority_digest
                    != transition.current_source_after_state_authority_digest
                )
            )
            or (transition.disposition == "removed" and entry is not None)
        ):
            return _refusal(
                code="package_membership_transition_invalid",
                operation_authority_digest=operation_authority_digest,
                workspace_ref=workspace_ref,
                branch_ref=branch_ref,
                selection_scope=selection.scope,
                transitions=transitions,
                plan_wire=plan_wire,
                result_wire=result_wire,
                result=graph_result,
                graph_admission=graph_admission,
                predecessor_digest=predecessor.admission_digest,
                source_digest=source_admission.admission_digest,
                selection_digest=selection.admission_digest,
            )

    bindings = plan.graph_execution_binding.ordered_node_bindings
    results_by_node = {
        item.node_digest: item for item in graph_result.ordered_node_results
    }
    if len(results_by_node) != len(graph_result.ordered_node_results) or {
        item.node_digest for item in bindings
    } != set(results_by_node):
        return _refusal(
            code="graph_coverage_mismatch",
            operation_authority_digest=operation_authority_digest,
            workspace_ref=workspace_ref,
            branch_ref=branch_ref,
            selection_scope=selection.scope,
            transitions=transitions,
            plan_wire=plan_wire,
            result_wire=result_wire,
            result=graph_result,
            graph_admission=graph_admission,
            predecessor_digest=predecessor.admission_digest,
            source_digest=source_admission.admission_digest,
            selection_digest=selection.admission_digest,
        )

    slots = selection.ordered_selected_slots
    slots_by_key = {
        _slot_lookup_key(
            slot.package_lineage_ref, slot.result_role, slot.semantic_contract
        ): slot
        for slot in slots
    }
    if len(slots_by_key) != len(slots):
        return _refusal(
            code="pin_slot_collision",
            operation_authority_digest=operation_authority_digest,
            workspace_ref=workspace_ref,
            branch_ref=branch_ref,
            selection_scope=selection.scope,
            transitions=transitions,
            plan_wire=plan_wire,
            result_wire=result_wire,
            result=graph_result,
            graph_admission=graph_admission,
            predecessor_digest=predecessor.admission_digest,
            source_digest=source_admission.admission_digest,
            selection_digest=selection.admission_digest,
        )
    used_slots: set[str] = set()
    derived_by_slot: dict[str, WorkspaceRevisionPreparedPackagePin] = {}
    for binding in bindings:
        result = results_by_node[binding.node_digest]
        package_entries = entries_by_package_ref.get(binding.package.package_ref, [])
        if len(package_entries) != 1:
            return _refusal(
                code="source_result_mismatch",
                operation_authority_digest=operation_authority_digest,
                workspace_ref=workspace_ref,
                branch_ref=branch_ref,
                selection_scope=selection.scope,
                transitions=transitions,
                plan_wire=plan_wire,
                result_wire=result_wire,
                result=graph_result,
                graph_admission=graph_admission,
                predecessor_digest=predecessor.admission_digest,
                source_digest=source_admission.admission_digest,
                selection_digest=selection.admission_digest,
            )
        source_entry = package_entries[0]
        slot = slots_by_key.get(
            _slot_lookup_key(
                source_entry.package_lineage_ref,
                result.result_coordinate.role,
                result.result_coordinate.contract,
            )
        )
        if slot is None:
            return _refusal(
                code="graph_coverage_mismatch",
                operation_authority_digest=operation_authority_digest,
                workspace_ref=workspace_ref,
                branch_ref=branch_ref,
                selection_scope=selection.scope,
                transitions=transitions,
                plan_wire=plan_wire,
                result_wire=result_wire,
                result=graph_result,
                graph_admission=graph_admission,
                predecessor_digest=predecessor.admission_digest,
                source_digest=source_admission.admission_digest,
                selection_digest=selection.admission_digest,
            )
        if slot.slot_digest in used_slots:
            return _refusal(
                code="pin_slot_collision",
                operation_authority_digest=operation_authority_digest,
                workspace_ref=workspace_ref,
                branch_ref=branch_ref,
                selection_scope=selection.scope,
                transitions=transitions,
                plan_wire=plan_wire,
                result_wire=result_wire,
                result=graph_result,
                graph_admission=graph_admission,
                predecessor_digest=predecessor.admission_digest,
                source_digest=source_admission.admission_digest,
                selection_digest=selection.admission_digest,
            )
        used_slots.add(slot.slot_digest)
        if (
            binding.package_entry.source_identity_digest.value
            != source_entry.source_package_identity_digest
        ):
            return _refusal(
                code="source_result_mismatch",
                operation_authority_digest=operation_authority_digest,
                workspace_ref=workspace_ref,
                branch_ref=branch_ref,
                selection_scope=selection.scope,
                transitions=transitions,
                plan_wire=plan_wire,
                result_wire=result_wire,
                result=graph_result,
                graph_admission=graph_admission,
                predecessor_digest=predecessor.admission_digest,
                source_digest=source_admission.admission_digest,
                selection_digest=selection.admission_digest,
            )
        try:
            derived_by_slot[slot.slot_digest] = (
                WorkspaceRevisionPreparedPackagePin.create(
                    slot=slot,
                    semantic_package=binding.package,
                    source_package_identity_digest=(
                        source_entry.source_package_identity_digest
                    ),
                    source_after_state_authority_digest=(
                        source_entry.source_after_state_authority_digest
                    ),
                    code_intent_digest=binding.code_intent.intent_digest.value,
                    code_match_digest=binding.code_match.match_digest.value,
                    execution_input_closure_digest=(
                        result.execution_input_closure_digest.value
                    ),
                    result_coordinate=result.result_coordinate,
                    package_head_revision=result.result_head_revision,
                    package_head_digest=result.result_head_digest.value,
                    package_head_body_sha256=(
                        result.package_head_reread_evidence.canonical_head_wire_digest.value
                    ),
                )
            )
        except (TypeError, ValueError, WorkspaceRevisionPreparationAdmissionError):
            return _refusal(
                code="pin_derivation_invalid",
                operation_authority_digest=operation_authority_digest,
                workspace_ref=workspace_ref,
                branch_ref=branch_ref,
                selection_scope=selection.scope,
                transitions=transitions,
                plan_wire=plan_wire,
                result_wire=result_wire,
                result=graph_result,
                graph_admission=graph_admission,
                predecessor_digest=predecessor.admission_digest,
                source_digest=source_admission.admission_digest,
                selection_digest=selection.admission_digest,
            )
    if used_slots != {slot.slot_digest for slot in slots}:
        return _refusal(
            code="graph_coverage_mismatch",
            operation_authority_digest=operation_authority_digest,
            workspace_ref=workspace_ref,
            branch_ref=branch_ref,
            selection_scope=selection.scope,
            transitions=transitions,
            plan_wire=plan_wire,
            result_wire=result_wire,
            result=graph_result,
            graph_admission=graph_admission,
            predecessor_digest=predecessor.admission_digest,
            source_digest=source_admission.admission_digest,
            selection_digest=selection.admission_digest,
        )

    derived = [derived_by_slot[slot.slot_digest] for slot in slots]
    removed = {
        item.package_lineage_ref
        for item in transitions.ordered_authorities
        if item.disposition == "removed"
    }
    selected_lineages = {slot.package_lineage_ref for slot in slots}
    if selection.scope == "complete_workspace_profile":
        final_pins = list(derived)
    else:
        if predecessor_state is None:
            return _refusal(
                code="predecessor_authority_unavailable",
                operation_authority_digest=operation_authority_digest,
                workspace_ref=workspace_ref,
                branch_ref=branch_ref,
                selection_scope=selection.scope,
                transitions=transitions,
                plan_wire=plan_wire,
                result_wire=result_wire,
                result=graph_result,
                graph_admission=graph_admission,
                predecessor_digest=predecessor.admission_digest,
                source_digest=source_admission.admission_digest,
                selection_digest=selection.admission_digest,
            )
        try:
            final_pins = list(
                _merge_prepared_pin_overlay(
                    predecessor_pins=predecessor_state.ordered_package_pins,
                    replacements=tuple(derived),
                    selected_lineages=frozenset(selected_lineages),
                    removed_lineages=frozenset(removed),
                )[0]
            )
        except WorkspaceRevisionPreparationAdmissionError:
            return _refusal(
                code="pin_slot_collision",
                operation_authority_digest=operation_authority_digest,
                workspace_ref=workspace_ref,
                branch_ref=branch_ref,
                selection_scope=selection.scope,
                transitions=transitions,
                plan_wire=plan_wire,
                result_wire=result_wire,
                result=graph_result,
                graph_admission=graph_admission,
                predecessor_digest=predecessor.admission_digest,
                source_digest=source_admission.admission_digest,
                selection_digest=selection.admission_digest,
            )
    try:
        for pin in final_pins:
            entry = entries_by_lineage.get(pin.slot.package_lineage_ref)
            if (
                entry is None
                or pin.source_package_identity_digest
                != entry.source_package_identity_digest
                or pin.source_after_state_authority_digest
                != entry.source_after_state_authority_digest
                or pin.semantic_package.package_ref != entry.current_package_ref
            ):
                return _refusal(
                    code="source_result_mismatch",
                    operation_authority_digest=operation_authority_digest,
                    workspace_ref=workspace_ref,
                    branch_ref=branch_ref,
                    selection_scope=selection.scope,
                    transitions=transitions,
                    plan_wire=plan_wire,
                    result_wire=result_wire,
                    result=graph_result,
                    graph_admission=graph_admission,
                    predecessor_digest=predecessor.admission_digest,
                    source_digest=source_admission.admission_digest,
                    selection_digest=selection.admission_digest,
                )
        state = WorkspaceRevisionState.create(
            workspace_ref=workspace_ref,
            source_closure_digest=source_closure.closure_digest,
            ordered_package_pins=tuple(final_pins),
        )
    except (TypeError, ValueError, WorkspaceRevisionPreparationAdmissionError):
        return _refusal(
            code="state_derivation_invalid",
            operation_authority_digest=operation_authority_digest,
            workspace_ref=workspace_ref,
            branch_ref=branch_ref,
            selection_scope=selection.scope,
            transitions=transitions,
            plan_wire=plan_wire,
            result_wire=result_wire,
            result=graph_result,
            graph_admission=graph_admission,
            predecessor_digest=predecessor.admission_digest,
            source_digest=source_admission.admission_digest,
            selection_digest=selection.admission_digest,
        )

    unchanged = (
        predecessor_state is not None
        and state.canonical_bytes() == predecessor_state.canonical_bytes()
    )
    candidate = None
    if not unchanged:
        predecessor_value = (
            WorkspaceRevisionCandidatePredecessor.genesis(
                cast(str, predecessor.revision_nonmembership_digest)
            )
            if predecessor.disposition == "genesis"
            else WorkspaceRevisionCandidatePredecessor.revision(
                workspace_revision_ref=cast(
                    str, predecessor.predecessor_workspace_revision_ref
                ),
                workspace_revision_digest=cast(
                    str, predecessor.predecessor_workspace_revision_digest
                ),
                state_digest=cast(str, predecessor.predecessor_state_digest),
            )
        )
        candidate = WorkspaceRevisionCandidate.create(
            state=state, predecessor=predecessor_value
        )
    evidence = WorkspaceRevisionPreparationEvidence.create(
        outcome="revision_unchanged" if unchanged else "candidate_prepared",
        operation_authority_digest=operation_authority_digest,
        workspace_ref=workspace_ref,
        branch_ref=branch_ref,
        predecessor_admission_digest=predecessor.admission_digest,
        source_closure_admission_digest=source_admission.admission_digest,
        selection_scope=selection.scope,
        selection_scope_admission_digest=selection.admission_digest,
        graph_execution_admission_digest=graph_admission.admission_digest,
        execution_provenance_lifecycle=graph_admission.execution_provenance_lifecycle,
        plan_body_sha256=ContentDigest.of_bytes(plan_wire).value,
        plan_body_size_bytes=len(plan_wire),
        graph_result_body_sha256=ContentDigest.of_bytes(result_wire).value,
        graph_result_body_size_bytes=len(result_wire),
        graph_result_digest=graph_result.result_digest.value,
        package_membership_transition_set_digest=transitions.set_digest,
        derived_state_digest=state.state_digest,
        candidate_digest=None if candidate is None else candidate.candidate_digest,
        refusal_code=None,
        provider_execution_count=0,
        external_read_count=0,
        external_write_count=0,
        ontology_call_count=0,
        meta_oig_call_count=0,
    )
    return WorkspaceRevisionPreparationResult(state, candidate, evidence)


__all__ = ["WorkspaceRevisionPreparationResult", "prepare_workspace_revision"]
