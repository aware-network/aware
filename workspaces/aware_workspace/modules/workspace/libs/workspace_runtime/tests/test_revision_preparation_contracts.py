from __future__ import annotations

from pathlib import Path

import pytest
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticContractRef,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
)
from aware_workspace_runtime.revision_preparation_contracts import (
    WorkspaceMaterializationGraphExecutionAdmission,
    WorkspaceRevisionCandidate,
    WorkspaceRevisionCandidatePredecessor,
    WorkspaceRevisionPackageMembershipTransitionAuthority,
    WorkspaceRevisionPackageMembershipTransitionSet,
    WorkspaceRevisionPinSlot,
    WorkspaceRevisionPredecessorAdmission,
    WorkspaceRevisionPreparationEvidence,
    WorkspaceRevisionPreparedPackagePin,
    WorkspaceRevisionSelectionScopeAdmission,
    WorkspaceRevisionSourceClosure,
    WorkspaceRevisionSourceClosureAdmission,
    WorkspaceRevisionSourcePackageEntry,
    WorkspaceRevisionState,
)


def _digest(label: str) -> str:
    return ContentDigest.of_bytes(label.encode()).value


def _portable_fixture() -> dict[str, object]:
    operation = _digest("operation")
    workspace_ref = "workspace:test"
    lineage = "workspace-package-lineage:00000000-0000-4000-8000-000000000001"
    contract = SemanticContractRef(
        key="aware.test.result",
        version="1",
        schema_digest=ContentDigest(_digest("contract")),
    )
    slot = WorkspaceRevisionPinSlot.create(
        package_lineage_ref=lineage,
        result_role="result",
        semantic_contract=contract,
    )
    source_entry = WorkspaceRevisionSourcePackageEntry.create(
        package_lineage_ref=lineage,
        source_package_identity_digest=_digest("source-identity"),
        current_package_ref="package:test@1.0.0",
        source_after_state_authority_digest=_digest("source-after-state"),
        source_after_state_body_sha256=_digest("source-after-state-body"),
    )
    source_closure = WorkspaceRevisionSourceClosure.create(
        workspace_ref=workspace_ref,
        ordered_packages=(source_entry,),
    )
    transition = WorkspaceRevisionPackageMembershipTransitionAuthority.create(
        disposition="present",
        workspace_ref=workspace_ref,
        operation_authority_digest=operation,
        package_lineage_ref=lineage,
        predecessor_membership_digest=None,
        current_membership_proof_digest=_digest("membership"),
        current_nonmembership_proof_digest=None,
        current_source_after_state_authority_digest=(
            source_entry.source_after_state_authority_digest
        ),
    )
    transitions = WorkspaceRevisionPackageMembershipTransitionSet.create(
        ordered_authorities=(transition,)
    )
    predecessor = WorkspaceRevisionPredecessorAdmission.create(
        disposition="genesis",
        operation_authority_digest=operation,
        workspace_ref=workspace_ref,
        branch_ref="workspace-branch:test",
        observed_branch_head_ref=None,
        observed_branch_head_digest=None,
        revision_nonmembership_digest=_digest("revision-nonmembership"),
        predecessor_workspace_revision_ref=None,
        predecessor_workspace_revision_digest=None,
        predecessor_state_digest=None,
        predecessor_source_closure_digest=None,
    )
    selection = WorkspaceRevisionSelectionScopeAdmission.create(
        scope="complete_workspace_profile",
        operation_authority_digest=operation,
        workspace_ref=workspace_ref,
        graph_digest=_digest("graph"),
        ordered_selected_slots=(slot,),
        current_membership_catalog_root_digest=_digest("membership-root"),
        complete_profile_proof_digest=_digest("complete-profile"),
    )
    source_admission = WorkspaceRevisionSourceClosureAdmission.create(
        disposition="admitted",
        operation_authority_digest=operation,
        workspace_ref=workspace_ref,
        predecessor_source_closure_digest=None,
        selection_scope=selection.scope,
        selection_scope_admission_digest=selection.admission_digest,
        package_membership_transition_set_digest=transitions.set_digest,
        source_closure_digest=source_closure.closure_digest,
    )
    pin = WorkspaceRevisionPreparedPackagePin.create(
        slot=slot,
        semantic_package=SemanticPackageCoordinate(
            package_ref=source_entry.current_package_ref,
            package_kind="ontology",
            manifest_digest=ContentDigest(_digest("manifest")),
        ),
        source_package_identity_digest=source_entry.source_package_identity_digest,
        source_after_state_authority_digest=(
            source_entry.source_after_state_authority_digest
        ),
        code_intent_digest=_digest("intent"),
        code_match_digest=_digest("match"),
        execution_input_closure_digest=_digest("execution-input"),
        result_coordinate=SemanticValueCoordinate(
            role=slot.result_role,
            contract=contract,
            value_ref="value:test",
            digest=ContentDigest(_digest("value")),
            size_bytes=4,
        ),
        package_head_revision=1,
        package_head_digest=_digest("package-head"),
        package_head_body_sha256=_digest("package-head-body"),
    )
    state = WorkspaceRevisionState.create(
        workspace_ref=workspace_ref,
        source_closure_digest=source_closure.closure_digest,
        ordered_package_pins=(pin,),
    )
    candidate = WorkspaceRevisionCandidate.create(
        state=state,
        predecessor=WorkspaceRevisionCandidatePredecessor.genesis(
            predecessor.revision_nonmembership_digest  # type: ignore[arg-type]
        ),
    )
    graph_admission = WorkspaceMaterializationGraphExecutionAdmission.create(
        disposition="admitted",
        operation_authority_digest=operation,
        execution_provenance_lifecycle="same_process_execution",
        plan_body_sha256=_digest("plan-body"),
        plan_body_size_bytes=100,
        graph_result_body_sha256=_digest("graph-result-body"),
        graph_result_body_size_bytes=200,
        graph_result_digest=_digest("graph-result"),
    )
    evidence_arguments = {
        "operation_authority_digest": operation,
        "workspace_ref": workspace_ref,
        "branch_ref": predecessor.branch_ref,
        "predecessor_admission_digest": predecessor.admission_digest,
        "source_closure_admission_digest": source_admission.admission_digest,
        "selection_scope": selection.scope,
        "selection_scope_admission_digest": selection.admission_digest,
        "graph_execution_admission_digest": graph_admission.admission_digest,
        "execution_provenance_lifecycle": "same_process_execution",
        "plan_body_sha256": graph_admission.plan_body_sha256,
        "plan_body_size_bytes": graph_admission.plan_body_size_bytes,
        "graph_result_body_sha256": graph_admission.graph_result_body_sha256,
        "graph_result_body_size_bytes": graph_admission.graph_result_body_size_bytes,
        "graph_result_digest": graph_admission.graph_result_digest,
        "package_membership_transition_set_digest": transitions.set_digest,
        "provider_execution_count": 0,
        "external_read_count": 0,
        "external_write_count": 0,
        "ontology_call_count": 0,
        "meta_oig_call_count": 0,
    }
    candidate_evidence = WorkspaceRevisionPreparationEvidence.create(
        outcome="candidate_prepared",
        derived_state_digest=state.state_digest,
        candidate_digest=candidate.candidate_digest,
        refusal_code=None,
        **evidence_arguments,
    )
    unchanged_evidence = WorkspaceRevisionPreparationEvidence.create(
        outcome="revision_unchanged",
        derived_state_digest=state.state_digest,
        candidate_digest=None,
        refusal_code=None,
        **evidence_arguments,
    )
    refused_evidence = WorkspaceRevisionPreparationEvidence.create(
        outcome="preparation_refused",
        derived_state_digest=None,
        candidate_digest=None,
        refusal_code="graph_execution_provenance_unavailable",
        graph_execution_admission_digest=None,
        execution_provenance_lifecycle=None,
        **{
            key: value
            for key, value in evidence_arguments.items()
            if key
            not in (
                "graph_execution_admission_digest",
                "execution_provenance_lifecycle",
            )
        },
    )
    return locals()


@pytest.mark.parametrize(
    "name",
    (
        "slot",
        "pin",
        "transition",
        "transitions",
        "predecessor",
        "selection",
        "source_entry",
        "source_closure",
        "source_admission",
        "state",
        "candidate",
        "graph_admission",
        "candidate_evidence",
        "unchanged_evidence",
        "refused_evidence",
    ),
)
def test_portable_values_round_trip_exactly(name: str) -> None:
    value = _portable_fixture()[name]
    decoded = type(value).from_canonical_bytes(value.canonical_bytes())
    assert decoded.canonical_bytes() == value.canonical_bytes()


def test_mutated_issued_value_cannot_be_serialized() -> None:
    slot = _portable_fixture()["slot"]
    assert isinstance(slot, WorkspaceRevisionPinSlot)
    object.__setattr__(slot, "result_role", "other")
    with pytest.raises(ValueError, match="issued state"):
        slot.canonical_bytes()


def test_pin_result_role_and_contract_must_match_its_stable_slot() -> None:
    fixture = _portable_fixture()
    pin = fixture["pin"]
    assert isinstance(pin, WorkspaceRevisionPreparedPackagePin)
    values = {
        field: getattr(pin, field)
        for field in pin.__dataclass_fields__
        if field != "pin_digest"
    }
    values["result_coordinate"] = SemanticValueCoordinate(
        role="other",
        contract=pin.result_coordinate.contract,
        value_ref=pin.result_coordinate.value_ref,
        digest=pin.result_coordinate.digest,
        size_bytes=pin.result_coordinate.size_bytes,
    )
    with pytest.raises(ValueError, match="stable slot"):
        WorkspaceRevisionPreparedPackagePin.create(**values)


def test_coherent_outer_and_nested_restamping_cannot_replace_issued_state() -> None:
    fixture = _portable_fixture()
    slot = fixture["slot"]
    pin = fixture["pin"]
    assert isinstance(slot, WorkspaceRevisionPinSlot)
    assert isinstance(pin, WorkspaceRevisionPreparedPackagePin)
    alternate_slot = WorkspaceRevisionPinSlot.create(
        package_lineage_ref=slot.package_lineage_ref,
        result_role="alternate",
        semantic_contract=slot.semantic_contract,
    )
    object.__setattr__(slot, "result_role", alternate_slot.result_role)
    object.__setattr__(slot, "slot_digest", alternate_slot.slot_digest)
    with pytest.raises(ValueError, match="issued state"):
        slot.canonical_bytes()

    alternate_coordinate = SemanticValueCoordinate(
        role=alternate_slot.result_role,
        contract=alternate_slot.semantic_contract,
        value_ref=pin.result_coordinate.value_ref,
        digest=pin.result_coordinate.digest,
        size_bytes=pin.result_coordinate.size_bytes,
    )
    alternate_values = {
        field: getattr(pin, field)
        for field in pin.__dataclass_fields__
        if field != "pin_digest"
    }
    alternate_values["slot"] = alternate_slot
    alternate_values["result_coordinate"] = alternate_coordinate
    alternate_pin = WorkspaceRevisionPreparedPackagePin.create(**alternate_values)
    object.__setattr__(pin, "slot", alternate_slot)
    object.__setattr__(pin, "result_coordinate", alternate_coordinate)
    object.__setattr__(pin, "pin_digest", alternate_pin.pin_digest)
    with pytest.raises(ValueError, match="issued state"):
        pin.canonical_bytes()


def test_exact_nested_tuple_and_canonical_order_are_required() -> None:
    fixture = _portable_fixture()
    transition = fixture["transition"]
    with pytest.raises(TypeError, match="exact tuple"):
        WorkspaceRevisionPackageMembershipTransitionSet.create(
            ordered_authorities=[transition]  # type: ignore[arg-type]
        )
    assert isinstance(transition, WorkspaceRevisionPackageMembershipTransitionAuthority)
    second = WorkspaceRevisionPackageMembershipTransitionAuthority.create(
        disposition=transition.disposition,
        workspace_ref=transition.workspace_ref,
        operation_authority_digest=transition.operation_authority_digest,
        package_lineage_ref=(
            "workspace-package-lineage:00000000-0000-4000-8000-000000000002"
        ),
        predecessor_membership_digest=transition.predecessor_membership_digest,
        current_membership_proof_digest=transition.current_membership_proof_digest,
        current_nonmembership_proof_digest=(
            transition.current_nonmembership_proof_digest
        ),
        current_source_after_state_authority_digest=(
            transition.current_source_after_state_authority_digest
        ),
    )
    with pytest.raises(ValueError):
        WorkspaceRevisionPackageMembershipTransitionSet.create(
            ordered_authorities=(second, transition)
        )


def test_refusal_prefix_matrix_is_exact() -> None:
    fixture = _portable_fixture()
    evidence = fixture["refused_evidence"]
    assert isinstance(evidence, WorkspaceRevisionPreparationEvidence)
    values = {
        field: getattr(evidence, field)
        for field in evidence.__dataclass_fields__
        if field != "evidence_digest"
    }
    values["predecessor_admission_digest"] = None
    with pytest.raises(ValueError, match="admission prefix"):
        WorkspaceRevisionPreparationEvidence.create(**values)


def test_alternate_tagged_variants_round_trip() -> None:
    fixture = _portable_fixture()
    predecessor = fixture["predecessor"]
    selection = fixture["selection"]
    transition = fixture["transition"]
    graph_admission = fixture["graph_admission"]
    assert isinstance(predecessor, WorkspaceRevisionPredecessorAdmission)
    assert isinstance(selection, WorkspaceRevisionSelectionScopeAdmission)
    assert isinstance(transition, WorkspaceRevisionPackageMembershipTransitionAuthority)
    assert isinstance(graph_admission, WorkspaceMaterializationGraphExecutionAdmission)
    revision = WorkspaceRevisionPredecessorAdmission.create(
        disposition="revision",
        operation_authority_digest=predecessor.operation_authority_digest,
        workspace_ref=predecessor.workspace_ref,
        branch_ref=predecessor.branch_ref,
        observed_branch_head_ref="workspace-revision:previous",
        observed_branch_head_digest=_digest("observed-head"),
        revision_nonmembership_digest=None,
        predecessor_workspace_revision_ref="workspace-revision:previous",
        predecessor_workspace_revision_digest=_digest("revision"),
        predecessor_state_digest=_digest("state"),
        predecessor_source_closure_digest=_digest("source-closure"),
    )
    partial = WorkspaceRevisionSelectionScopeAdmission.create(
        scope="partial_workspace_update",
        operation_authority_digest=selection.operation_authority_digest,
        workspace_ref=selection.workspace_ref,
        graph_digest=selection.graph_digest,
        ordered_selected_slots=selection.ordered_selected_slots,
        current_membership_catalog_root_digest=(
            selection.current_membership_catalog_root_digest
        ),
        complete_profile_proof_digest=None,
    )
    removed = WorkspaceRevisionPackageMembershipTransitionAuthority.create(
        disposition="removed",
        workspace_ref=transition.workspace_ref,
        operation_authority_digest=transition.operation_authority_digest,
        package_lineage_ref=transition.package_lineage_ref,
        predecessor_membership_digest=_digest("predecessor-membership"),
        current_membership_proof_digest=None,
        current_nonmembership_proof_digest=_digest("nonmembership"),
        current_source_after_state_authority_digest=None,
    )
    reexecuted = WorkspaceMaterializationGraphExecutionAdmission.create(
        disposition=graph_admission.disposition,
        operation_authority_digest=graph_admission.operation_authority_digest,
        execution_provenance_lifecycle="reexecuted_after_process_loss",
        plan_body_sha256=graph_admission.plan_body_sha256,
        plan_body_size_bytes=graph_admission.plan_body_size_bytes,
        graph_result_body_sha256=graph_admission.graph_result_body_sha256,
        graph_result_body_size_bytes=graph_admission.graph_result_body_size_bytes,
        graph_result_digest=graph_admission.graph_result_digest,
    )
    for value in (revision, partial, removed, reexecuted):
        assert (
            type(value).from_canonical_bytes(value.canonical_bytes()).canonical_bytes()
            == value.canonical_bytes()
        )


@pytest.mark.parametrize(
    ("filename", "name"),
    (
        ("workspace-revision-graph-execution-admission-v1.json", "graph_admission"),
        (
            "workspace-revision-source-closure-admission-v1.json",
            "source_admission",
        ),
        ("workspace-revision-candidate-v1.json", "candidate"),
        ("workspace-revision-unchanged-evidence-v1.json", "unchanged_evidence"),
        ("workspace-revision-refused-evidence-v1.json", "refused_evidence"),
        (
            "workspace-revision-package-membership-transition-set-v1.json",
            "transitions",
        ),
        ("workspace-revision-predecessor-admission-v1.json", "predecessor"),
        ("workspace-revision-selection-scope-admission-v1.json", "selection"),
        ("workspace-revision-source-closure-v1.json", "source_closure"),
        (
            "workspace-revision-candidate-prepared-evidence-v1.json",
            "candidate_evidence",
        ),
    ),
)
def test_frozen_fixture_is_the_exact_canonical_body(filename: str, name: str) -> None:
    expected = _portable_fixture()[name].canonical_bytes()
    fixture = Path(__file__).with_name("fixtures").joinpath(filename).read_bytes()
    assert fixture == expected
    assert fixture[-1:] == b"}"
