from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest
import aware_goal_operational_runtime.phase_native_operational_bootstrap as bootstrap_runtime

from aware_goal_operational_runtime import (
    CommittedIssueAuthorityEvidenceV1,
    GoalCoordinatorAuthorityV1,
    GoalCoordinatorAcceptancePublicationV1,
    GoalBootstrapPublicationIssueAuthorityV1,
    GoalLanePhase,
    GoalLanePhaseDefinitionV1,
    GoalLanePhaseGate,
    GoalLanePhaseState,
    GoalPhaseBootstrapClassification,
    GoalPhaseBootstrapCoordinatorAcceptanceV1,
    GoalPhaseBootstrapEntryV1,
    GoalPhaseBootstrapEvidenceBundleV1,
    GoalPhaseBootstrapRepositoryEvidenceV1,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
    GoalPhaseExecutionAuthorityTransitionV1,
    GoalPhaseHoldAuthorityEvidenceV1,
    GoalPhaseNativeDocumentV1,
    GoalPhaseNativeDocumentV2,
    GoalPhaseNativeOperationalBootstrapError,
    GoalPhaseNativeOperationalBootstrapProposalV1,
    VerifiedGoalCoordinatorAcceptanceV1,
    decode_goal_phase_native_operational_bootstrap_proposal,
    encode_goal_phase_native_operational_bootstrap_proposal,
    issue_goal_phase_native_operational_bootstrap_publication_receipt,
    observe_goal_phase_native_operational_bootstrap_currentness,
    plan_goal_phase_native_operational_bootstrap,
    verify_goal_coordinator_acceptance,
    verify_goal_phase_bootstrap_repository_evidence,
    verify_committed_issue_authority_evidence,
    verify_goal_phase_hold_authority,
)

GOAL = "goal/2026-09-21/bootstrap-test-v0"
REV = "1" * 40


def _definition(key: str = "m1") -> GoalLanePhaseDefinitionV1:
    return GoalLanePhaseDefinitionV1(
        coordinate=GoalPhaseCoordinate(goal_tag=GOAL, lane_key="runtime", phase_key=key),
        ordinal=1,
        title="Bootstrap",
        intent="Retire legacy execution honestly.",
        gate=GoalLanePhaseGate(
            gate_key="accepted",
            promise="Independent acceptance is published.",
            gate_contract_ref="aware.goal.gate/accepted-v1",
            evidence_schema_ref="aware.goal.evidence/accepted-v1",
        ),
    )


def _phase(definition: GoalLanePhaseDefinitionV1) -> GoalLanePhase:
    return GoalLanePhase(
        coordinate=definition.coordinate,
        title=definition.title or "",
        ordinal=definition.ordinal,
        intent=definition.intent or "",
        state=GoalLanePhaseState.PLANNED,
        gate=definition.gate,
    )


def _document(*, phase: GoalLanePhase | None = None) -> GoalPhaseNativeDocumentV1:
    definition = _definition()
    compatibility = b"# Goal\n"
    return GoalPhaseNativeDocumentV1(
        goal_tag=GOAL,
        compatibility_projection_sha256="sha256:" + hashlib.sha256(compatibility).hexdigest(),
        compatibility_projection_byte_count=len(compatibility),
        definitions=(definition,),
        operational_bundle=GoalPhaseContractBundleV1(phases=(() if phase is None else (phase,)), dependencies=()),
        unresolved_dependencies=(),
        source_refs=("repository:path:docs/goals/test.md",),
    )


def _proposal(document: GoalPhaseNativeDocumentV1, *, classification: GoalPhaseBootstrapClassification, desired: GoalLanePhase | None) -> GoalPhaseNativeOperationalBootstrapProposalV1:
    definition = document.definitions[0]
    return GoalPhaseNativeOperationalBootstrapProposalV1(
        goal_tag=GOAL,
        source_document_ref=document.document_ref,
        source_goal_sha256="sha256:" + "2" * 64,
        source_repository_revision_ref=REV,
        requested_execution_authority_transition=GoalPhaseExecutionAuthorityTransitionV1(
            source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
            parity_ref="goal-phase-native-compatibility-parity:sha256:" + "3" * 64,
        ),
        evidence_bundle=GoalPhaseBootstrapEvidenceBundleV1(),
        entries=(GoalPhaseBootstrapEntryV1(
            coordinate=definition.coordinate,
            definition_ref=definition.definition_ref,
            gate_digest=definition.gate.gate_digest,
            classification=classification,
            evidence_keys=(),
            desired_phase=desired,
        ),),
    )


def _acceptance_and_verification(proposal: GoalPhaseNativeOperationalBootstrapProposalV1):
    authority = GoalCoordinatorAuthorityV1(
        goal_tag=GOAL,
        goal_doc_path="docs/goals/test.md",
        authority_profile="committed_goal_owner_v1",
        coordinator_execution_id="codex-test",
        source_repository_revision_ref=REV,
        source_goal_sha256=proposal.source_goal_sha256,
        source_goal_blob_oid="6" * 40,
        authority_source_ref="goal-owner-snapshot:sha256:" + "7" * 64,
        authority_repository_path="docs/goals/test.md",
        authority_repository_revision_ref=REV,
        authority_blob_oid="6" * 40,
        currentness_ref="goal-coordinator-authority-currentness:sha256:" + "8" * 64,
    )
    acceptance = GoalPhaseBootstrapCoordinatorAcceptanceV1(
        proposal_aggregate_ref=proposal.aggregate_ref,
        goal_tag=GOAL,
        source_document_ref=proposal.source_document_ref,
        source_goal_sha256=proposal.source_goal_sha256,
        source_repository_revision_ref=REV,
        coordinator_execution_id="codex-test",
        coordinator_authority_ref=authority.authority_ref,
        accepted_at="2026-09-21T13:00:00Z",
        evidence_refs=(),
    )
    issue = GoalBootstrapPublicationIssueAuthorityV1(
        issue_ref="docs/issues/test.md",
        owner_execution_id="codex-publisher",
        goal_doc_path="docs/goals/test.md",
        repository_revision_ref=REV,
        issue_blob_oid="9" * 40,
        scope_digest="sha256:" + "a" * 64,
    )
    acceptance_publication = GoalCoordinatorAcceptancePublicationV1(
        proposal_aggregate_ref=proposal.aggregate_ref,
        coordinator_acceptance_ref=acceptance.receipt_ref,
        coordinator_execution_id="codex-test",
        acceptance_path="docs/reports/acceptance.json",
        acceptance_commit_ref=REV,
        acceptance_blob_oid="c" * 40,
        issuance_issue_ref=issue.issue_ref,
        issuance_issue_blob_oid=issue.issue_blob_oid,
        repository_commit_receipt_ref=f"repository-commit:{REV}",
        published_at="2026-09-21T13:01:00Z",
    )
    verified = verify_goal_coordinator_acceptance(
        acceptance,
        acceptance_publication,
        proposal,
        authority,
        issue,
        lambda source, head: {"goal_tag": GOAL, "goal_sha256": proposal.source_goal_sha256, "lineage": "equal"},
        lambda ref, head: {
            "goal_tag": authority.goal_tag,
            "goal_doc_path": authority.goal_doc_path,
            "coordinator_execution_id": "codex-test",
            "authority_source_ref": authority.authority_source_ref,
            "authority_repository_path": authority.authority_repository_path,
            "authority_repository_revision_ref": authority.authority_repository_revision_ref,
            "authority_blob_oid": authority.authority_blob_oid,
            "revocation_state": "clear",
            "currentness_ref": authority.currentness_ref,
        },
        lambda ref, head: {
            "proposal_aggregate_ref": proposal.aggregate_ref,
            "coordinator_acceptance_ref": acceptance.receipt_ref,
            "coordinator_execution_id": "codex-test",
            "acceptance_path": acceptance_publication.acceptance_path,
            "acceptance_commit_ref": acceptance_publication.acceptance_commit_ref,
            "acceptance_blob_oid": acceptance_publication.acceptance_blob_oid,
            "issuance_issue_ref": acceptance_publication.issuance_issue_ref,
            "issuance_issue_blob_oid": acceptance_publication.issuance_issue_blob_oid,
            "repository_commit_receipt_ref": acceptance_publication.repository_commit_receipt_ref,
        },
        lambda issue_ref, head: {
            "issue_ref": issue.issue_ref,
            "owner_execution_id": issue.owner_execution_id,
            "goal_doc_path": issue.goal_doc_path,
            "authority_repository_revision_ref": issue.repository_revision_ref,
            "observed_repository_revision_ref": head,
            "issue_blob_oid": issue.issue_blob_oid,
            "scope_digest": issue.scope_digest,
            "status": issue.status,
        },
        REV,
    )
    return acceptance, verified


def test_definition_only_bootstrap_produces_strict_v2_without_inventing_phase() -> None:
    source = _document()
    proposal = _proposal(source, classification=GoalPhaseBootstrapClassification.DEFINITION_ONLY_HISTORICAL, desired=None)
    decoded = decode_goal_phase_native_operational_bootstrap_proposal(encode_goal_phase_native_operational_bootstrap_proposal(proposal))
    acceptance, verified = _acceptance_and_verification(decoded)
    plan = plan_goal_phase_native_operational_bootstrap(source_document=source, proposal=decoded, coordinator_acceptance=acceptance, verified_coordinator_acceptance=verified, verified_evidence=())
    assert isinstance(plan.target_document, GoalPhaseNativeDocumentV2)
    assert plan.target_document.operational_bundle.phases == ()
    assert plan.target_document.execution_authority.legacy_execution_disposition == "retired"


def test_existing_operational_phase_must_be_retained_exactly() -> None:
    definition = _definition()
    phase = _phase(definition)
    source = _document(phase=phase)
    proposal = _proposal(source, classification=GoalPhaseBootstrapClassification.DEFINITION_ONLY_HISTORICAL, desired=None)
    acceptance, verified = _acceptance_and_verification(proposal)
    with pytest.raises(GoalPhaseNativeOperationalBootstrapError, match="already_operational"):
        plan_goal_phase_native_operational_bootstrap(source_document=source, proposal=proposal, coordinator_acceptance=acceptance, verified_coordinator_acceptance=verified, verified_evidence=())


def test_existing_operational_phase_round_trips_losslessly() -> None:
    definition = _definition()
    phase = _phase(definition)
    source = _document(phase=phase)
    proposal = _proposal(source, classification=GoalPhaseBootstrapClassification.ALREADY_OPERATIONAL, desired=phase)
    acceptance, verified = _acceptance_and_verification(proposal)
    plan = plan_goal_phase_native_operational_bootstrap(source_document=source, proposal=proposal, coordinator_acceptance=acceptance, verified_coordinator_acceptance=verified, verified_evidence=())
    assert plan.target_document.operational_bundle.phases == (phase,)


def test_proposal_decoder_rejects_boolean_ordinal_and_recomputed_aggregate() -> None:
    source = _document(phase=_phase(_definition()))
    proposal = _proposal(source, classification=GoalPhaseBootstrapClassification.ALREADY_OPERATIONAL, desired=source.operational_bundle.phases[0])
    wire = json.loads(encode_goal_phase_native_operational_bootstrap_proposal(proposal))
    wire["entries"][0]["desired_phase"]["ordinal"] = True
    wire.pop("aggregate_ref")
    wire["aggregate_ref"] = "goal-phase-native-operational-bootstrap-proposal:sha256:" + hashlib.sha256(json.dumps(wire, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    with pytest.raises((GoalPhaseNativeOperationalBootstrapError, ValueError, TypeError)):
        decode_goal_phase_native_operational_bootstrap_proposal(json.dumps(wire, sort_keys=True, separators=(",", ":")).encode())


def test_coordinator_authority_is_goal_scoped_and_not_issue_ownership() -> None:
    authority = GoalCoordinatorAuthorityV1(
        goal_tag=GOAL,
        goal_doc_path="docs/goals/test.md",
        authority_profile="committed_goal_owner_v1",
        coordinator_execution_id="codex-coordinator",
        source_repository_revision_ref=REV,
        source_goal_sha256="sha256:" + "2" * 64,
        source_goal_blob_oid="6" * 40,
        authority_source_ref="goal-owner-snapshot:sha256:" + "7" * 64,
        authority_repository_path="docs/goals/test.md",
        authority_repository_revision_ref=REV,
        authority_blob_oid="6" * 40,
        currentness_ref="goal-coordinator-authority-currentness:sha256:" + "8" * 64,
    )
    assert authority.coordinator_execution_id == "codex-coordinator"
    with pytest.raises(GoalPhaseNativeOperationalBootstrapError, match="revoked"):
        GoalCoordinatorAuthorityV1(
            goal_tag=GOAL, goal_doc_path="docs/goals/test.md", authority_profile="committed_goal_owner_v1", coordinator_execution_id="codex-coordinator", source_repository_revision_ref=REV, source_goal_sha256="sha256:" + "2" * 64, source_goal_blob_oid="6" * 40, authority_source_ref="goal-owner-snapshot:sha256:" + "7" * 64, authority_repository_path="docs/goals/test.md", authority_repository_revision_ref=REV, authority_blob_oid="6" * 40, currentness_ref="goal-coordinator-authority-currentness:sha256:" + "8" * 64, revocation_state="revoked",
        )
    with pytest.raises(GoalPhaseNativeOperationalBootstrapError, match="delegation"):
        GoalCoordinatorAuthorityV1(
            goal_tag=GOAL, goal_doc_path="docs/goals/test.md",
            authority_profile="repository_published_delegation_v1",
            coordinator_execution_id="codex-coordinator",
            source_repository_revision_ref=REV,
            source_goal_sha256="sha256:" + "2" * 64,
            source_goal_blob_oid="6" * 40,
            authority_source_ref="goal-coordinator-delegation:sha256:" + "7" * 64,
            authority_repository_path="docs/reports/delegation.json",
            authority_repository_revision_ref=REV,
            authority_blob_oid="6" * 40,
            currentness_ref="goal-coordinator-authority-currentness:sha256:" + "8" * 64,
        )


def test_plan_and_publication_receipt_reject_postconstruction_forgery() -> None:
    source = _document()
    proposal = _proposal(source, classification=GoalPhaseBootstrapClassification.DEFINITION_ONLY_HISTORICAL, desired=None)
    acceptance, verified = _acceptance_and_verification(proposal)
    plan = plan_goal_phase_native_operational_bootstrap(source_document=source, proposal=proposal, coordinator_acceptance=acceptance, verified_coordinator_acceptance=verified, verified_evidence=())
    forged_target = replace(plan.target_document, source_refs=("repository:path:forged",))
    object.__setattr__(plan, "target_document", forged_target)
    with pytest.raises(GoalPhaseNativeOperationalBootstrapError, match="not canonical"):
        issue_goal_phase_native_operational_bootstrap_publication_receipt(
            plan=plan,
            repository_commit_ref="b" * 40,
            repository_commit_receipt_ref="repository-commit:" + "b" * 40,
            changed_path="docs/goals/test.md",
        )


def test_planner_rejects_forged_verifier_output_and_mutated_proposal() -> None:
    source = _document()
    proposal = _proposal(
        source,
        classification=GoalPhaseBootstrapClassification.DEFINITION_ONLY_HISTORICAL,
        desired=None,
    )
    acceptance, verified = _acceptance_and_verification(proposal)
    forged = object.__new__(VerifiedGoalCoordinatorAcceptanceV1)
    object.__setattr__(forged, "acceptance_ref", acceptance.receipt_ref)
    object.__setattr__(forged, "proposal_aggregate_ref", proposal.aggregate_ref)
    object.__setattr__(forged, "publication_head", REV)
    object.__setattr__(forged, "coordinator_authority_ref", "goal-coordinator-authority:sha256:" + "1" * 64)
    object.__setattr__(forged, "publication_issue_ref", "docs/issues/test.md")
    object.__setattr__(forged, "verification_ref", "goal-phase-bootstrap-coordinator-verification:sha256:" + "2" * 64)
    with pytest.raises(GoalPhaseNativeOperationalBootstrapError, match="sealed"):
        plan_goal_phase_native_operational_bootstrap(
            source_document=source,
            proposal=proposal,
            coordinator_acceptance=acceptance,
            verified_coordinator_acceptance=forged,
            verified_evidence=(),
        )

    fresh_proposal = _proposal(
        source,
        classification=GoalPhaseBootstrapClassification.DEFINITION_ONLY_HISTORICAL,
        desired=None,
    )
    fresh_acceptance, sealed = _acceptance_and_verification(fresh_proposal)
    object.__setattr__(sealed, "publication_head", "e" * 40)
    verification_body = {
        "acceptance_ref": sealed.acceptance_ref,
        "acceptance_publication_ref": sealed.coordinator_acceptance_publication_ref,
        "authority_ref": sealed.coordinator_authority_ref,
        "issue_ref": sealed.publication_issue_ref,
        "issue_authority_digest": sealed.publication_issue_authority_digest,
        "publication_head": sealed.publication_head,
    }
    forged_ref = "goal-phase-bootstrap-coordinator-verification:sha256:" + hashlib.sha256(
        json.dumps(
            verification_body,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    object.__setattr__(sealed, "verification_ref", forged_ref)
    with pytest.raises(GoalPhaseNativeOperationalBootstrapError, match="mutated"):
        plan_goal_phase_native_operational_bootstrap(
            source_document=source,
            proposal=fresh_proposal,
            coordinator_acceptance=fresh_acceptance,
            verified_coordinator_acceptance=sealed,
            verified_evidence=(),
        )

    object.__setattr__(proposal, "source_goal_sha256", "sha256:" + "f" * 64)
    with pytest.raises(GoalPhaseNativeOperationalBootstrapError):
        plan_goal_phase_native_operational_bootstrap(
            source_document=source,
            proposal=proposal,
            coordinator_acceptance=acceptance,
            verified_coordinator_acceptance=verified,
            verified_evidence=(),
        )


def test_publication_currentness_separates_receipt_from_later_observation() -> None:
    source = _document()
    proposal = _proposal(source, classification=GoalPhaseBootstrapClassification.DEFINITION_ONLY_HISTORICAL, desired=None)
    acceptance, verified = _acceptance_and_verification(proposal)
    plan = plan_goal_phase_native_operational_bootstrap(source_document=source, proposal=proposal, coordinator_acceptance=acceptance, verified_coordinator_acceptance=verified, verified_evidence=())
    receipt = issue_goal_phase_native_operational_bootstrap_publication_receipt(
        plan=plan,
        repository_commit_ref="b" * 40,
        repository_commit_receipt_ref="repository-commit:" + "b" * 40,
        changed_path="docs/goals/test.md",
    )
    def evidence(observed: str, changed: tuple[str, ...] = ()) -> GoalPhaseBootstrapRepositoryEvidenceV1:
        return verify_goal_phase_bootstrap_repository_evidence(
            publication_revision_ref="b" * 40,
            observed_revision_ref=observed,
            protected_paths=("docs/goals/test.md", "docs/issues/test.md"),
            repository_resolver=lambda publication, current, paths: {
                "lineage": "equal" if current == publication else "descendant",
                "changed_paths": list(changed),
            },
        )

    exact = observe_goal_phase_native_operational_bootstrap_currentness(
        publication_receipt=receipt, repository_evidence=evidence("b" * 40)
    )
    advanced = observe_goal_phase_native_operational_bootstrap_currentness(
        publication_receipt=receipt, repository_evidence=evidence("c" * 40)
    )
    stale = observe_goal_phase_native_operational_bootstrap_currentness(
        publication_receipt=receipt,
        repository_evidence=evidence("c" * 40, ("docs/goals/test.md",)),
    )
    tampered = evidence("c" * 40)
    object.__setattr__(tampered, "changed_paths", ("docs/goals/test.md",))
    tampered.__post_init__()
    with pytest.raises(GoalPhaseNativeOperationalBootstrapError, match="mutated"):
        observe_goal_phase_native_operational_bootstrap_currentness(
            publication_receipt=receipt,
            repository_evidence=tampered,
        )
    assert (exact.status, exact.projection_currentness) == ("current", "exact")
    assert (advanced.status, advanced.replay_disposition) == ("current", "reobserved_unchanged")
    assert (stale.status, stale.replay_disposition) == ("stale", "refuse")


def test_mutated_valid_evidence_verifier_output_is_rejected() -> None:
    coordinate = _definition().coordinate
    evidence = CommittedIssueAuthorityEvidenceV1(
        evidence_key="issue-authority",
        phase_coordinate=coordinate,
        issue_ref="docs/issues/active.md",
        repository_revision_ref=REV,
        issue_blob_oid="a" * 40,
        expected_owner_execution_id="codex-worker",
        expected_scope_digest="sha256:" + "b" * 64,
        phase_association_ref="goal-phase-work:sha256:" + "c" * 64,
        work_role="implementation",
        authority_admitted_at="2026-09-21T12:00:00Z",
    )
    verified = verify_committed_issue_authority_evidence(
        evidence,
        lambda issue_ref, revision: {
            "blob_oid": evidence.issue_blob_oid,
            "status": evidence.expected_status,
            "owner_execution_id": evidence.expected_owner_execution_id,
            "scope_digest": evidence.expected_scope_digest,
            "phase_association_ref": evidence.phase_association_ref,
        },
        REV,
    )
    object.__setattr__(
        verified,
        "evidence_ref",
        "goal-phase-bootstrap-issue-authority:sha256:" + "d" * 64,
    )
    object.__setattr__(
        verified,
        "verification_ref",
        "goal-phase-bootstrap-evidence-verification:sha256:"
        + hashlib.sha256(
            json.dumps(
                {"evidence_ref": verified.evidence_ref},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest(),
    )
    hold = GoalPhaseHoldAuthorityEvidenceV1(
        evidence_key="hold-authority",
        phase_coordinate=coordinate,
        current_issue_evidence_key=evidence.evidence_key,
        hold_receipt_ref="goal-phase-hold:sha256:" + "1" * 64,
        publication_receipt_ref="goal-publication:sha256:" + "2" * 64,
        repository_commit_ref=REV,
        source_currentness_ref="goal-currentness:sha256:" + "3" * 64,
    )
    with pytest.raises(GoalPhaseNativeOperationalBootstrapError, match="mutated"):
        verify_goal_phase_hold_authority(hold, verified, lambda commit: {})


def test_verifier_registration_is_strictly_lifetime_bounded() -> None:
    retained = [
        verify_goal_phase_bootstrap_repository_evidence(
            publication_revision_ref="a" * 40,
            observed_revision_ref="a" * 40,
            protected_paths=(f"docs/goals/test-{ordinal}.md",),
            repository_resolver=lambda publication, observed, paths: {
                "lineage": "equal",
                "changed_paths": [],
            },
        )
        for ordinal in range(bootstrap_runtime._VERIFICATION_REGISTRY_LIMIT + 1)
    ]
    assert len(bootstrap_runtime._VERIFICATION_REGISTRY) == (
        bootstrap_runtime._VERIFICATION_REGISTRY_LIMIT
    )
    assert retained[0].verifier_token not in bootstrap_runtime._VERIFICATION_REGISTRY
    assert retained[-1].verifier_token in bootstrap_runtime._VERIFICATION_REGISTRY
