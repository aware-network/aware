from __future__ import annotations

import copy
from dataclasses import dataclass, replace
from unittest.mock import patch
from weakref import WeakKeyDictionary

import pytest
import pytest_asyncio
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
)
from aware_workspace_runtime import WorkspaceSemanticMaterializationGraphCoordinator
from aware_workspace_runtime.materialization_graph_coordinator import _execution_state
from aware_workspace_runtime.revision_preparation import prepare_workspace_revision
from aware_workspace_runtime.revision_preparation_admission import (
    WorkspaceRevisionPreparationAdmissionError,
    WorkspaceRevisionPreparationContextCapability,
    admit_completed_workspace_materialization_graph_execution,
)
from aware_workspace_runtime.revision_preparation_contracts import (
    WorkspaceRevisionPackageMembershipTransitionAuthority,
    WorkspaceRevisionPackageMembershipTransitionSet,
    WorkspaceRevisionPinSlot,
    WorkspaceRevisionPredecessorAdmission,
    WorkspaceRevisionPreparedPackagePin,
    WorkspaceRevisionSelectionScopeAdmission,
    WorkspaceRevisionSourceClosure,
    WorkspaceRevisionSourceClosureAdmission,
    WorkspaceRevisionSourcePackageEntry,
    WorkspaceRevisionState,
)
from test_materialization_graph_coordinator import _executed_fixture, _fixture


def _digest(label: str) -> str:
    return ContentDigest.of_bytes(label.encode()).value


@dataclass(slots=True)
class _PreparedFixture:
    owner: object
    execution: object
    plan: object
    graph_reader: object
    graph_result: object
    operation_digest: str
    predecessor: object
    predecessor_state: object | None
    predecessor_source_closure: object | None
    source_closure: object
    source_admission: object
    selection: object
    transitions: object
    context_capability: object
    graph_admission: object
    graph_capability: object


@dataclass(frozen=True, slots=True)
class _TestPreparationContext:
    owner: object
    operation_authority_digest: str
    workspace_ref: str
    branch_ref: str
    predecessor: object
    predecessor_wire: bytes
    predecessor_state: object | None
    predecessor_state_wire: bytes | None
    predecessor_source_closure: object | None
    predecessor_source_closure_wire: bytes | None
    source_closure: object
    source_closure_wire: bytes
    source_admission: object
    source_admission_wire: bytes
    selection: object
    selection_wire: bytes
    transitions: object
    transitions_wire: bytes


_TEST_CONTEXTS: WeakKeyDictionary[object, _TestPreparationContext] = (
    WeakKeyDictionary()
)


def _canonical_body(value: object | None) -> bytes | None:
    if value is None:
        return None
    canonical = getattr(value, "canonical_bytes", None)
    if not callable(canonical):
        raise TypeError("test authority must expose canonical bytes")
    body = canonical()
    if type(body) is not bytes:
        raise TypeError("test authority canonical body must be exact bytes")
    return body


def _issue_test_revision_preparation_context(
    *,
    owner: object,
    operation_authority_digest: str,
    workspace_ref: str,
    branch_ref: str,
    predecessor: object,
    predecessor_state: object | None,
    predecessor_source_closure: object | None,
    source_closure: object,
    source_admission: object,
    selection: object,
    transitions: object,
) -> WorkspaceRevisionPreparationContextCapability:
    if (
        getattr(selection, "scope", None) == "partial_workspace_update"
        and predecessor_source_closure is None
    ):
        raise WorkspaceRevisionPreparationAdmissionError(
            "partial source closure requires a positive predecessor"
        )
    capability = object.__new__(WorkspaceRevisionPreparationContextCapability)
    _TEST_CONTEXTS[capability] = _TestPreparationContext(
        owner=owner,
        operation_authority_digest=operation_authority_digest,
        workspace_ref=workspace_ref,
        branch_ref=branch_ref,
        predecessor=predecessor,
        predecessor_wire=_canonical_body(predecessor) or b"",
        predecessor_state=predecessor_state,
        predecessor_state_wire=_canonical_body(predecessor_state),
        predecessor_source_closure=predecessor_source_closure,
        predecessor_source_closure_wire=_canonical_body(predecessor_source_closure),
        source_closure=source_closure,
        source_closure_wire=_canonical_body(source_closure) or b"",
        source_admission=source_admission,
        source_admission_wire=_canonical_body(source_admission) or b"",
        selection=selection,
        selection_wire=_canonical_body(selection) or b"",
        transitions=transitions,
        transitions_wire=_canonical_body(transitions) or b"",
    )
    return capability


def _verify_test_revision_preparation_context(*, stage: str, **values: object) -> None:
    capability = values["capability"]
    record = _TEST_CONTEXTS.get(capability)
    predecessor = values["predecessor"]
    if (
        record is None
        or record.owner is not values["owner"]
        or record.operation_authority_digest != values["operation_authority_digest"]
        or record.workspace_ref != values["workspace_ref"]
        or record.branch_ref != values["branch_ref"]
        or record.predecessor is not predecessor
        or record.predecessor_state is not values["predecessor_state"]
        or record.predecessor_source_closure
        is not values["predecessor_source_closure"]
        or record.predecessor_wire != _canonical_body(predecessor)
        or record.predecessor_state_wire
        != _canonical_body(values["predecessor_state"])
        or record.predecessor_source_closure_wire
        != _canonical_body(values["predecessor_source_closure"])
    ):
        raise WorkspaceRevisionPreparationAdmissionError(
            "revision preparation predecessor context differs"
        )
    if stage == "predecessor":
        return
    if (
        record.source_closure is not values["source_closure"]
        or record.source_admission is not values["source_admission"]
        or record.transitions is not values["transitions"]
        or record.source_closure_wire != _canonical_body(values["source_closure"])
        or record.source_admission_wire
        != _canonical_body(values["source_admission"])
        or record.transitions_wire != _canonical_body(values["transitions"])
    ):
        raise WorkspaceRevisionPreparationAdmissionError(
            "revision preparation source context differs"
        )
    if stage == "source":
        return
    if (
        stage != "selection"
        or record.selection is not values["selection"]
        or record.selection_wire != _canonical_body(values["selection"])
    ):
        raise WorkspaceRevisionPreparationAdmissionError(
            "revision preparation selection context differs"
        )


async def _prepared_fixture(
    node_count: int = 2,
    *,
    executed: bool = False,
    predecessor_state: WorkspaceRevisionState | None = None,
    predecessor_source_closure: WorkspaceRevisionSourceClosure | None = None,
    scope: str = "complete_workspace_profile",
) -> _PreparedFixture:
    if executed:
        plan, graph_reader, owner, execution, _metrics = await _executed_fixture(
            node_count
        )
    else:
        plan, graph_reader, owner, execution = await _fixture(node_count)
    graph_result = await WorkspaceSemanticMaterializationGraphCoordinator().execute(
        execution, owner=owner
    )
    graph_admission, graph_capability = (
        admit_completed_workspace_materialization_graph_execution(
            execution=execution,
            owner=owner,
            result=graph_result,
        )
    )
    operation_digest = _execution_state(execution).operation_digest.value
    entries: list[WorkspaceRevisionSourcePackageEntry] = []
    transitions: list[WorkspaceRevisionPackageMembershipTransitionAuthority] = []
    slots: list[WorkspaceRevisionPinSlot] = []
    results_by_node = {
        item.node_digest: item for item in graph_result.ordered_node_results
    }
    predecessor_entries = (
        {}
        if predecessor_source_closure is None
        else {
            item.package_lineage_ref: item
            for item in predecessor_source_closure.ordered_packages
        }
    )
    for index, binding in enumerate(
        plan.graph_execution_binding.ordered_node_bindings, start=1
    ):
        lineage = f"workspace-package-lineage:00000000-0000-4000-8000-{index:012d}"
        after_state = _digest(f"after-state:{index}")
        entry = WorkspaceRevisionSourcePackageEntry.create(
            package_lineage_ref=lineage,
            source_package_identity_digest=(
                binding.package_entry.source_identity_digest.value
            ),
            current_package_ref=binding.package.package_ref,
            source_after_state_authority_digest=after_state,
            source_after_state_body_sha256=_digest(f"after-state-body:{index}"),
        )
        entries.append(entry)
        transitions.append(
            WorkspaceRevisionPackageMembershipTransitionAuthority.create(
                disposition="present",
                workspace_ref="workspace:test",
                operation_authority_digest=operation_digest,
                package_lineage_ref=lineage,
                predecessor_membership_digest=(
                    None
                    if lineage not in predecessor_entries
                    else predecessor_entries[lineage].entry_digest
                ),
                current_membership_proof_digest=_digest(f"membership:{index}"),
                current_nonmembership_proof_digest=None,
                current_source_after_state_authority_digest=after_state,
            )
        )
        node_result = results_by_node[binding.node_digest]
        slots.append(
            WorkspaceRevisionPinSlot.create(
                package_lineage_ref=lineage,
                result_role=node_result.result_coordinate.role,
                semantic_contract=node_result.result_coordinate.contract,
            )
        )
    entries.sort(key=lambda item: item.package_lineage_ref.encode())
    transitions.sort(
        key=lambda item: (item.package_lineage_ref.encode(), item.disposition.encode())
    )
    slots.sort(key=lambda item: item.ordering_key())
    source_closure = WorkspaceRevisionSourceClosure.create(
        workspace_ref="workspace:test", ordered_packages=tuple(entries)
    )
    transition_set = WorkspaceRevisionPackageMembershipTransitionSet.create(
        ordered_authorities=tuple(transitions)
    )
    if predecessor_state is None:
        predecessor = WorkspaceRevisionPredecessorAdmission.create(
            disposition="genesis",
            operation_authority_digest=operation_digest,
            workspace_ref="workspace:test",
            branch_ref="workspace-branch:test",
            observed_branch_head_ref=None,
            observed_branch_head_digest=None,
            revision_nonmembership_digest=_digest("revision-nonmembership"),
            predecessor_workspace_revision_ref=None,
            predecessor_workspace_revision_digest=None,
            predecessor_state_digest=None,
            predecessor_source_closure_digest=None,
        )
    else:
        predecessor = WorkspaceRevisionPredecessorAdmission.create(
            disposition="revision",
            operation_authority_digest=operation_digest,
            workspace_ref="workspace:test",
            branch_ref="workspace-branch:test",
            observed_branch_head_ref="workspace-revision:previous",
            observed_branch_head_digest=_digest("branch-head"),
            revision_nonmembership_digest=None,
            predecessor_workspace_revision_ref="workspace-revision:previous",
            predecessor_workspace_revision_digest=_digest("workspace-revision"),
            predecessor_state_digest=predecessor_state.state_digest,
            predecessor_source_closure_digest=(
                predecessor_source_closure.closure_digest
            ),
        )
    selection = WorkspaceRevisionSelectionScopeAdmission.create(
        scope=scope,
        operation_authority_digest=operation_digest,
        workspace_ref="workspace:test",
        graph_digest=plan.graph.graph_digest.value,
        ordered_selected_slots=tuple(slots),
        current_membership_catalog_root_digest=_digest("membership-root"),
        complete_profile_proof_digest=(
            _digest("complete-profile")
            if scope == "complete_workspace_profile"
            else None
        ),
    )
    source_admission = WorkspaceRevisionSourceClosureAdmission.create(
        disposition="admitted",
        operation_authority_digest=operation_digest,
        workspace_ref="workspace:test",
        predecessor_source_closure_digest=(
            None
            if predecessor_source_closure is None
            else predecessor_source_closure.closure_digest
        ),
        selection_scope=selection.scope,
        selection_scope_admission_digest=selection.admission_digest,
        package_membership_transition_set_digest=transition_set.set_digest,
        source_closure_digest=source_closure.closure_digest,
    )
    context_capability = _issue_test_revision_preparation_context(
        owner=owner,
        operation_authority_digest=operation_digest,
        workspace_ref="workspace:test",
        branch_ref="workspace-branch:test",
        predecessor=predecessor,
        predecessor_state=predecessor_state,
        predecessor_source_closure=predecessor_source_closure,
        source_closure=source_closure,
        source_admission=source_admission,
        selection=selection,
        transitions=transition_set,
    )
    return _PreparedFixture(
        owner=owner,
        execution=execution,
        plan=plan,
        graph_reader=graph_reader,
        graph_result=graph_result,
        operation_digest=operation_digest,
        predecessor=predecessor,
        predecessor_state=predecessor_state,
        predecessor_source_closure=predecessor_source_closure,
        source_closure=source_closure,
        source_admission=source_admission,
        selection=selection,
        transitions=transition_set,
        context_capability=context_capability,
        graph_admission=graph_admission,
        graph_capability=graph_capability,
    )


@pytest_asyncio.fixture(scope="module")
async def reused_fixture() -> _PreparedFixture:
    return await _prepared_fixture(2)


def _prepare(fixture: _PreparedFixture, **changes: object):  # type: ignore[no-untyped-def]
    values = {
        "owner": fixture.owner,
        "operation_authority_digest": fixture.operation_digest,
        "workspace_ref": "workspace:test",
        "branch_ref": "workspace-branch:test",
        "context_capability": fixture.context_capability,
        "predecessor": fixture.predecessor,
        "predecessor_state": fixture.predecessor_state,
        "predecessor_source_closure": fixture.predecessor_source_closure,
        "source_closure": fixture.source_closure,
        "source_admission": fixture.source_admission,
        "selection": fixture.selection,
        "transitions": fixture.transitions,
        "graph_execution": fixture.execution,
        "graph_admission_capability": fixture.graph_capability,
        "graph_admission": fixture.graph_admission,
        "plan": fixture.plan,
        "graph_result": fixture.graph_result,
    }
    values.update(changes)
    with patch(
        "aware_workspace_runtime.revision_preparation."
        "_verify_workspace_revision_preparation_context_stage",
        _verify_test_revision_preparation_context,
    ):
        return prepare_workspace_revision(**values)  # type: ignore[arg-type]


def _source_entry_for_pin(
    pin: WorkspaceRevisionPreparedPackagePin,
    *,
    after_state: str,
) -> WorkspaceRevisionSourcePackageEntry:
    return WorkspaceRevisionSourcePackageEntry.create(
        package_lineage_ref=pin.slot.package_lineage_ref,
        source_package_identity_digest=pin.source_package_identity_digest,
        current_package_ref=pin.semantic_package.package_ref,
        source_after_state_authority_digest=after_state,
        source_after_state_body_sha256=_digest(f"body:{after_state}"),
    )


def _clone_pin(
    pin: WorkspaceRevisionPreparedPackagePin,
    *,
    lineage: str,
    marker: str,
    package_ref: str | None = None,
    source_package_identity_digest: str | None = None,
) -> WorkspaceRevisionPreparedPackagePin:
    slot = WorkspaceRevisionPinSlot.create(
        package_lineage_ref=lineage,
        result_role=pin.slot.result_role,
        semantic_contract=pin.slot.semantic_contract,
    )
    package = SemanticPackageCoordinate(
        package_ref=package_ref or pin.semantic_package.package_ref,
        package_kind=pin.semantic_package.package_kind,
        manifest_digest=ContentDigest(_digest(f"manifest:{marker}")),
    )
    coordinate = SemanticValueCoordinate(
        role=pin.result_coordinate.role,
        contract=pin.result_coordinate.contract,
        value_ref=f"value:{marker}",
        digest=ContentDigest(_digest(f"value:{marker}")),
        size_bytes=len(marker.encode()),
    )
    return WorkspaceRevisionPreparedPackagePin.create(
        slot=slot,
        semantic_package=package,
        source_package_identity_digest=(
            source_package_identity_digest or pin.source_package_identity_digest
        ),
        source_after_state_authority_digest=_digest(f"after:{marker}"),
        code_intent_digest=pin.code_intent_digest,
        code_match_digest=pin.code_match_digest,
        execution_input_closure_digest=pin.execution_input_closure_digest,
        result_coordinate=coordinate,
        package_head_revision=pin.package_head_revision,
        package_head_digest=_digest(f"head:{marker}"),
        package_head_body_sha256=_digest(f"head-body:{marker}"),
    )


def _bind_partial_context(
    fixture: _PreparedFixture,
    *,
    predecessor_state: WorkspaceRevisionState,
    predecessor_source_closure: WorkspaceRevisionSourceClosure,
    carried_entries: tuple[WorkspaceRevisionSourcePackageEntry, ...],
    removed_lineages: tuple[str, ...],
) -> _PreparedFixture:
    predecessor_by_lineage = {
        item.package_lineage_ref: item
        for item in predecessor_source_closure.ordered_packages
    }
    current_entries = tuple(
        sorted(
            (*fixture.source_closure.ordered_packages, *carried_entries),
            key=lambda item: item.package_lineage_ref.encode(),
        )
    )
    source_closure = WorkspaceRevisionSourceClosure.create(
        workspace_ref="workspace:test", ordered_packages=current_entries
    )
    transitions = [
        WorkspaceRevisionPackageMembershipTransitionAuthority.create(
            disposition="present",
            workspace_ref="workspace:test",
            operation_authority_digest=fixture.operation_digest,
            package_lineage_ref=item.package_lineage_ref,
            predecessor_membership_digest=(
                None
                if item.package_lineage_ref not in predecessor_by_lineage
                else predecessor_by_lineage[item.package_lineage_ref].entry_digest
            ),
            current_membership_proof_digest=item.current_membership_proof_digest,
            current_nonmembership_proof_digest=None,
            current_source_after_state_authority_digest=(
                item.current_source_after_state_authority_digest
            ),
        )
        for item in fixture.transitions.ordered_authorities
    ]
    transitions.extend(
        WorkspaceRevisionPackageMembershipTransitionAuthority.create(
            disposition="removed",
            workspace_ref="workspace:test",
            operation_authority_digest=fixture.operation_digest,
            package_lineage_ref=lineage,
            predecessor_membership_digest=predecessor_by_lineage[lineage].entry_digest,
            current_membership_proof_digest=None,
            current_nonmembership_proof_digest=_digest(f"nonmembership:{lineage}"),
            current_source_after_state_authority_digest=None,
        )
        for lineage in removed_lineages
    )
    transition_set = WorkspaceRevisionPackageMembershipTransitionSet.create(
        ordered_authorities=tuple(
            sorted(
                transitions,
                key=lambda item: (
                    item.package_lineage_ref.encode(),
                    item.disposition.encode(),
                ),
            )
        )
    )
    selection = WorkspaceRevisionSelectionScopeAdmission.create(
        scope="partial_workspace_update",
        operation_authority_digest=fixture.operation_digest,
        workspace_ref="workspace:test",
        graph_digest=fixture.plan.graph.graph_digest.value,
        ordered_selected_slots=fixture.selection.ordered_selected_slots,
        current_membership_catalog_root_digest=(
            fixture.selection.current_membership_catalog_root_digest
        ),
        complete_profile_proof_digest=None,
    )
    predecessor = WorkspaceRevisionPredecessorAdmission.create(
        disposition="revision",
        operation_authority_digest=fixture.operation_digest,
        workspace_ref="workspace:test",
        branch_ref="workspace-branch:test",
        observed_branch_head_ref="workspace-revision:previous",
        observed_branch_head_digest=_digest("partial-branch-head"),
        revision_nonmembership_digest=None,
        predecessor_workspace_revision_ref="workspace-revision:previous",
        predecessor_workspace_revision_digest=_digest("partial-revision"),
        predecessor_state_digest=predecessor_state.state_digest,
        predecessor_source_closure_digest=predecessor_source_closure.closure_digest,
    )
    source_admission = WorkspaceRevisionSourceClosureAdmission.create(
        disposition="admitted",
        operation_authority_digest=fixture.operation_digest,
        workspace_ref="workspace:test",
        predecessor_source_closure_digest=predecessor_source_closure.closure_digest,
        selection_scope=selection.scope,
        selection_scope_admission_digest=selection.admission_digest,
        package_membership_transition_set_digest=transition_set.set_digest,
        source_closure_digest=source_closure.closure_digest,
    )
    context_capability = _issue_test_revision_preparation_context(
        owner=fixture.owner,
        operation_authority_digest=fixture.operation_digest,
        workspace_ref="workspace:test",
        branch_ref="workspace-branch:test",
        predecessor=predecessor,
        predecessor_state=predecessor_state,
        predecessor_source_closure=predecessor_source_closure,
        source_closure=source_closure,
        source_admission=source_admission,
        selection=selection,
        transitions=transition_set,
    )
    return replace(
        fixture,
        predecessor=predecessor,
        predecessor_state=predecessor_state,
        predecessor_source_closure=predecessor_source_closure,
        source_closure=source_closure,
        source_admission=source_admission,
        selection=selection,
        transitions=transition_set,
        context_capability=context_capability,
    )


def test_public_reused_graph_prepares_exact_zero_write_candidate(
    reused_fixture: _PreparedFixture,
) -> None:
    result = _prepare(reused_fixture)
    assert result.evidence.outcome == "candidate_prepared"
    assert result.state is not None
    assert result.candidate is not None
    assert len(result.state.ordered_package_pins) == 2
    assert {
        item.outcome for item in reused_fixture.graph_result.ordered_node_results
    } == {"reused"}
    assert (
        result.evidence.provider_execution_count,
        result.evidence.external_read_count,
        result.evidence.external_write_count,
        result.evidence.ontology_call_count,
        result.evidence.meta_oig_call_count,
    ) == (0, 0, 0, 0, 0)


@pytest.mark.asyncio
async def test_public_executed_graph_prepares_the_same_authority_shape() -> None:
    fixture = await _prepared_fixture(1, executed=True)
    result = _prepare(fixture)
    assert result.evidence.outcome == "candidate_prepared"
    assert result.state is not None
    assert len(result.state.ordered_package_pins) == 1
    assert fixture.graph_result.ordered_node_results[0].outcome == "executed"


@pytest.mark.asyncio
async def test_partial_replacement_with_identical_state_is_unchanged() -> None:
    genesis_fixture = await _prepared_fixture()
    genesis = _prepare(genesis_fixture)
    assert genesis.state is not None
    revision_fixture = await _prepared_fixture(
        predecessor_state=genesis.state,
        predecessor_source_closure=genesis_fixture.source_closure,
        scope="partial_workspace_update",
    )
    result = _prepare(revision_fixture)
    assert result.evidence.outcome == "revision_unchanged"
    assert result.state is not None
    assert result.state.canonical_bytes() == genesis.state.canonical_bytes()
    assert result.candidate is None


@pytest.mark.asyncio
async def test_partial_update_replaces_adds_removes_and_carries_by_lineage() -> None:
    current_fixture = await _prepared_fixture(2, executed=True)
    current = _prepare(current_fixture)
    assert current.state is not None
    first, second = current.state.ordered_package_pins
    first_lineage = first.slot.package_lineage_ref
    carry_lineage = "workspace-package-lineage:00000000-0000-4000-8000-000000000003"
    removed_lineage = "workspace-package-lineage:00000000-0000-4000-8000-000000000004"
    prior_first = _clone_pin(
        first,
        lineage=first_lineage,
        marker="prior-first",
        package_ref="aware.sdk.demo0000@0.9.0",
    )
    carried = _clone_pin(
        first,
        lineage=carry_lineage,
        marker="carried",
        package_ref="aware.sdk.carried@1.0.0",
        source_package_identity_digest=_digest("source:carried"),
    )
    removed = _clone_pin(
        first,
        lineage=removed_lineage,
        marker="removed",
        package_ref="aware.sdk.removed@1.0.0",
        source_package_identity_digest=_digest("source:removed"),
    )
    predecessor_entries = tuple(
        sorted(
            (
                _source_entry_for_pin(
                    prior_first,
                    after_state=prior_first.source_after_state_authority_digest,
                ),
                _source_entry_for_pin(
                    carried,
                    after_state=carried.source_after_state_authority_digest,
                ),
                _source_entry_for_pin(
                    removed,
                    after_state=removed.source_after_state_authority_digest,
                ),
            ),
            key=lambda item: item.package_lineage_ref.encode(),
        )
    )
    predecessor_source = WorkspaceRevisionSourceClosure.create(
        workspace_ref="workspace:test", ordered_packages=predecessor_entries
    )
    predecessor_state = WorkspaceRevisionState.create(
        workspace_ref="workspace:test",
        source_closure_digest=predecessor_source.closure_digest,
        ordered_package_pins=tuple(
            sorted(
                (prior_first, carried, removed),
                key=lambda item: item.slot.ordering_key(),
            )
        ),
    )
    partial_fixture = _bind_partial_context(
        current_fixture,
        predecessor_state=predecessor_state,
        predecessor_source_closure=predecessor_source,
        carried_entries=(predecessor_entries[1],),
        removed_lineages=(removed_lineage,),
    )
    result = _prepare(partial_fixture)
    assert result.evidence.outcome == "candidate_prepared"
    assert result.state is not None
    assert result.candidate is not None
    pins_by_lineage = {
        pin.slot.package_lineage_ref: pin for pin in result.state.ordered_package_pins
    }
    assert set(pins_by_lineage) == {
        first_lineage,
        second.slot.package_lineage_ref,
        carry_lineage,
    }
    assert pins_by_lineage[first_lineage].semantic_package.package_ref == (
        first.semantic_package.package_ref
    )
    assert pins_by_lineage[carry_lineage].canonical_bytes() == carried.canonical_bytes()
    assert removed_lineage not in pins_by_lineage
    assert result.candidate.predecessor.kind == "revision"
    assert (
        result.evidence.provider_execution_count,
        result.evidence.external_read_count,
        result.evidence.external_write_count,
        result.evidence.ontology_call_count,
        result.evidence.meta_oig_call_count,
    ) == (0, 0, 0, 0, 0)


def test_operation_substitution_has_first_refusal_and_retains_no_prefix(
    reused_fixture: _PreparedFixture,
) -> None:
    result = _prepare(
        reused_fixture, operation_authority_digest=_digest("foreign-operation")
    )
    assert result.evidence.refusal_code == "operation_currentness_mismatch"
    assert result.evidence.predecessor_admission_digest is None
    assert result.evidence.source_closure_admission_digest is None
    assert result.evidence.selection_scope_admission_digest is None
    assert result.evidence.graph_execution_admission_digest is None


def test_foreign_owner_refuses_before_graph_provenance(
    reused_fixture: _PreparedFixture,
) -> None:
    result = _prepare(reused_fixture, owner=object())
    assert result.evidence.refusal_code == "predecessor_authority_unavailable"
    assert result.evidence.predecessor_admission_digest is None


def test_structural_predecessor_copy_retains_no_admission_prefix(
    reused_fixture: _PreparedFixture,
) -> None:
    copied_predecessor = WorkspaceRevisionPredecessorAdmission.from_canonical_bytes(
        reused_fixture.predecessor.canonical_bytes()
    )
    result = _prepare(reused_fixture, predecessor=copied_predecessor)
    assert result.evidence.refusal_code == "predecessor_authority_unavailable"
    assert result.evidence.predecessor_admission_digest is None


def test_partial_context_cannot_be_issued_from_genesis(
    reused_fixture: _PreparedFixture,
) -> None:
    selection = WorkspaceRevisionSelectionScopeAdmission.create(
        scope="partial_workspace_update",
        operation_authority_digest=reused_fixture.operation_digest,
        workspace_ref="workspace:test",
        graph_digest=reused_fixture.plan.graph.graph_digest.value,
        ordered_selected_slots=reused_fixture.selection.ordered_selected_slots,
        current_membership_catalog_root_digest=(
            reused_fixture.selection.current_membership_catalog_root_digest
        ),
        complete_profile_proof_digest=None,
    )
    source_admission = WorkspaceRevisionSourceClosureAdmission.create(
        disposition="admitted",
        operation_authority_digest=reused_fixture.operation_digest,
        workspace_ref="workspace:test",
        predecessor_source_closure_digest=None,
        selection_scope=selection.scope,
        selection_scope_admission_digest=selection.admission_digest,
        package_membership_transition_set_digest=reused_fixture.transitions.set_digest,
        source_closure_digest=reused_fixture.source_closure.closure_digest,
    )
    with pytest.raises(
        WorkspaceRevisionPreparationAdmissionError,
        match="partial source closure requires a positive predecessor",
    ):
        _issue_test_revision_preparation_context(
            owner=reused_fixture.owner,
            operation_authority_digest=reused_fixture.operation_digest,
            workspace_ref="workspace:test",
            branch_ref="workspace-branch:test",
            predecessor=reused_fixture.predecessor,
            predecessor_state=None,
            predecessor_source_closure=None,
            source_closure=reused_fixture.source_closure,
            source_admission=source_admission,
            selection=selection,
            transitions=reused_fixture.transitions,
        )


def test_structural_source_copy_cannot_acquire_contextual_authority(
    reused_fixture: _PreparedFixture,
) -> None:
    copied_source = WorkspaceRevisionSourceClosure.from_canonical_bytes(
        reused_fixture.source_closure.canonical_bytes()
    )
    result = _prepare(reused_fixture, source_closure=copied_source)
    assert result.evidence.refusal_code == "source_closure_not_admitted"
    assert result.evidence.predecessor_admission_digest == (
        reused_fixture.predecessor.admission_digest
    )
    assert result.evidence.source_closure_admission_digest is None
    assert result.evidence.selection_scope_admission_digest is None
    assert result.evidence.graph_execution_admission_digest is None


def test_structural_graph_admission_copy_cannot_acquire_provenance(
    reused_fixture: _PreparedFixture,
) -> None:
    copied_admission = type(reused_fixture.graph_admission).from_canonical_bytes(
        reused_fixture.graph_admission.canonical_bytes()
    )
    result = _prepare(reused_fixture, graph_admission=copied_admission)
    assert result.evidence.refusal_code == "graph_execution_provenance_unavailable"
    assert result.evidence.predecessor_admission_digest == (
        reused_fixture.predecessor.admission_digest
    )
    assert result.evidence.source_closure_admission_digest == (
        reused_fixture.source_admission.admission_digest
    )
    assert result.evidence.selection_scope_admission_digest == (
        reused_fixture.selection.admission_digest
    )
    assert result.evidence.graph_execution_admission_digest is None


def test_structural_selection_copy_retains_only_preceding_admissions(
    reused_fixture: _PreparedFixture,
) -> None:
    copied_selection = WorkspaceRevisionSelectionScopeAdmission.from_canonical_bytes(
        reused_fixture.selection.canonical_bytes()
    )
    result = _prepare(reused_fixture, selection=copied_selection)
    assert result.evidence.refusal_code == "selection_scope_not_admitted"
    assert result.evidence.predecessor_admission_digest == (
        reused_fixture.predecessor.admission_digest
    )
    assert result.evidence.source_closure_admission_digest == (
        reused_fixture.source_admission.admission_digest
    )
    assert result.evidence.selection_scope_admission_digest is None


def test_equal_looking_plan_and_result_copies_cannot_reuse_graph_provenance(
    reused_fixture: _PreparedFixture,
) -> None:
    for field in ("plan", "graph_result"):
        copied = copy.deepcopy(getattr(reused_fixture, field))
        result = _prepare(reused_fixture, **{field: copied})
        assert result.evidence.refusal_code == (
            "graph_execution_provenance_unavailable"
        )
        assert result.evidence.graph_execution_admission_digest is None
