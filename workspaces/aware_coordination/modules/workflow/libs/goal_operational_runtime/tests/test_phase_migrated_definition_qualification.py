from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest
from aware_goal_operational_runtime import (
    GoalCoordinatorAuthorityV1,
    GoalCoordinatorDelegationPublicationV1,
    GoalDefinitionQualificationIssueAuthorityV1,
    GoalLanePhaseDefinitionV1,
    GoalLanePhaseGate,
    GoalOwnerCoordinatorAuthorityPublicationV1,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
    GoalPhaseDefinitionQualificationAcceptancePublicationV1,
    GoalPhaseDefinitionQualificationAcceptanceV1,
    GoalPhaseDefinitionQualificationProposalPublicationV1,
    GoalPhaseDefinitionQualificationProposalV1,
    GoalPhaseExecutionAuthorityV1,
    GoalPhaseMigratedDefinitionQualificationError,
    GoalPhaseNativeDocumentV2,
    decode_goal_phase_definition_qualification_acceptance,
    decode_goal_phase_definition_qualification_acceptance_publication,
    decode_goal_phase_definition_qualification_proposal,
    decode_goal_phase_definition_qualification_proposal_publication,
    decode_goal_phase_migrated_definition_qualification_publication_receipt,
    encode_goal_phase_definition_qualification_acceptance,
    encode_goal_phase_definition_qualification_acceptance_publication,
    encode_goal_phase_definition_qualification_proposal,
    encode_goal_phase_definition_qualification_proposal_publication,
    encode_goal_phase_migrated_definition_qualification_publication_receipt,
    issue_goal_phase_migrated_definition_qualification_publication_receipt,
    plan_goal_phase_migrated_definition_qualification,
)

GOAL = "goal/2026-09-10/actorworld-ux-ax-runtime-convergence-v0"
REV = "1" * 40


def _gate() -> GoalLanePhaseGate:
    return GoalLanePhaseGate(
        gate_key="accepted",
        promise="Independent acceptance is published.",
        gate_contract_ref="aware.goal.gate/accepted-v1",
        evidence_schema_ref="aware.goal.evidence/accepted-v1",
    )


def _document() -> GoalPhaseNativeDocumentV2:
    compatibility = b"# ActorWorld\n"
    definition = GoalLanePhaseDefinitionV1(
        coordinate=GoalPhaseCoordinate(
            goal_tag=GOAL,
            lane_key="runtime-authority-retreat",
            phase_key="r3-environment-experience-retreat",
        ),
        ordinal=3,
        gate=_gate(),
    )
    return GoalPhaseNativeDocumentV2(
        goal_tag=GOAL,
        compatibility_projection_sha256=(
            "sha256:" + hashlib.sha256(compatibility).hexdigest()
        ),
        compatibility_projection_byte_count=len(compatibility),
        definitions=(definition,),
        operational_bundle=GoalPhaseContractBundleV1(phases=(), dependencies=()),
        unresolved_dependencies=(),
        source_refs=("repository:path:docs/goals/actorworld.md",),
        execution_authority=GoalPhaseExecutionAuthorityV1(
            source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
            parity_ref="goal-phase-native-compatibility-parity:sha256:" + "2" * 64,
            proposal_aggregate_ref=(
                "goal-phase-native-operational-bootstrap-proposal:sha256:"
                + "3" * 64
            ),
            coordinator_acceptance_ref=(
                "goal-phase-native-operational-bootstrap-coordinator-acceptance:sha256:"
                + "4" * 64
            ),
        ),
    )


def _authorities(document: GoalPhaseNativeDocumentV2):
    definition = document.definitions[0]
    proposal = GoalPhaseDefinitionQualificationProposalV1(
        goal_path="docs/goals/actorworld.md",
        goal_tag=GOAL,
        source_document_ref=document.document_ref,
        source_repository_revision=REV,
        coordinate=definition.coordinate,
        ordinal=definition.ordinal,
        gate_digest=definition.gate.gate_digest,
        before_definition_ref=definition.definition_ref,
        title="Environment and Experience authority retreat",
        intent="Retire compatibility-only authority after accepted convergence.",
        evidence_refs=("evidence:r3-design-acceptance",),
        issuer_execution_id="codex-r3",
        proposed_at="2026-09-22T03:00:00Z",
    )
    proposal_payload = encode_goal_phase_definition_qualification_proposal(proposal)
    proposal_issue = GoalDefinitionQualificationIssueAuthorityV1(
        issue_path="docs/issues/r3-proposal.md",
        issue_blob="5" * 40,
        owner_execution_id="codex-r3",
        status="In Progress",
        scope_digest="sha256:" + "6" * 64,
    )
    proposal_publication = GoalPhaseDefinitionQualificationProposalPublicationV1(
        proposal=proposal,
        artifact_path="docs/reports/r3-proposal.json",
        publication_commit="7" * 40,
        artifact_blob="8" * 40,
        repository_commit_receipt_ref="repository-commit:" + "7" * 40,
        issue_authority=proposal_issue,
        artifact_payload_digest="sha256:" + hashlib.sha256(proposal_payload).hexdigest(),
    )
    coordinator = GoalCoordinatorAuthorityV1(
        goal_tag=GOAL,
        goal_doc_path=proposal.goal_path,
        authority_profile="committed_goal_owner_v1",
        coordinator_execution_id="codex-goal-owner",
        source_repository_revision_ref=REV,
        source_goal_sha256="sha256:" + "9" * 64,
        source_goal_blob_oid="a" * 40,
        authority_source_ref="goal-owner-authority-intent:sha256:" + "b" * 64,
        authority_repository_path=proposal.goal_path,
        authority_repository_revision_ref=REV,
        authority_blob_oid="a" * 40,
        currentness_ref="goal-coordinator-authority-currentness:sha256:" + "c" * 64,
    )
    delegation = GoalCoordinatorDelegationPublicationV1(
        authority=coordinator,
        publication=GoalOwnerCoordinatorAuthorityPublicationV1(
            goal_tag=GOAL,
            goal_doc_path=proposal.goal_path,
            goal_owner_execution_id="codex-goal-owner",
            coordinator_execution_id="codex-goal-owner",
            coordinator_authority_ref=coordinator.authority_ref,
            authority_source_ref=coordinator.authority_source_ref,
            authority_declaration_path="docs/governance/coordinator.json",
            authority_declaration_commit_ref="d" * 40,
            authority_declaration_blob_oid="e" * 40,
            issuance_issue_ref="docs/issues/coordinator-authority.md",
            issuance_issue_blob_oid="f" * 40,
            repository_commit_receipt_ref="repository-commit:" + "d" * 40,
            published_at="2026-09-22T03:05:00Z",
        ),
    )
    acceptance = GoalPhaseDefinitionQualificationAcceptanceV1(
        proposal_publication_authority_ref=proposal_publication.authority_ref,
        goal_path=proposal.goal_path,
        goal_tag=GOAL,
        source_document_ref=document.document_ref,
        source_repository_revision=REV,
        coordinator_authority_ref=delegation.authority_ref,
        accepting_execution_id="codex-goal-owner",
        publication_issue_path="docs/issues/r3-acceptance.md",
        accepted_at="2026-09-22T03:10:00Z",
    )
    acceptance_issue = GoalDefinitionQualificationIssueAuthorityV1(
        issue_path=acceptance.publication_issue_path,
        issue_blob="d" * 40,
        owner_execution_id="codex-goal-owner",
        status="In Progress",
        scope_digest="sha256:" + "e" * 64,
    )
    acceptance_publication = GoalPhaseDefinitionQualificationAcceptancePublicationV1(
        acceptance=acceptance,
        artifact_path="docs/reports/r3-acceptance.json",
        publication_commit="f" * 40,
        artifact_blob="0" * 40,
        repository_commit_receipt_ref="repository-commit:" + "f" * 40,
        issue_authority=acceptance_issue,
        proposal_publication=proposal_publication,
        delegation=delegation,
    )
    return proposal_publication, acceptance_publication


def test_qualification_replaces_only_incomplete_definition() -> None:
    document = _document()
    proposal, acceptance = _authorities(document)
    plan = plan_goal_phase_migrated_definition_qualification(
        source_document=document,
        proposal_publication=proposal,
        acceptance_publication=acceptance,
    )
    assert plan.after_document.definitions[0].title == proposal.proposal.title
    assert plan.after_document.definitions[0].intent == proposal.proposal.intent
    assert plan.after_document.operational_bundle == document.operational_bundle
    assert plan.after_document.source_refs == document.source_refs
    assert plan.after_document.execution_authority == document.execution_authority


def test_portable_semantic_artifacts_round_trip_strictly() -> None:
    document = _document()
    proposal_publication, acceptance_publication = _authorities(document)
    proposal = proposal_publication.proposal
    acceptance = acceptance_publication.acceptance
    assert decode_goal_phase_definition_qualification_proposal(
        encode_goal_phase_definition_qualification_proposal(proposal)
    ) == proposal
    assert decode_goal_phase_definition_qualification_acceptance(
        encode_goal_phase_definition_qualification_acceptance(acceptance)
    ) == acceptance
    assert decode_goal_phase_definition_qualification_proposal_publication(
        encode_goal_phase_definition_qualification_proposal_publication(
            proposal_publication
        )
    ) == proposal_publication
    assert decode_goal_phase_definition_qualification_acceptance_publication(
        encode_goal_phase_definition_qualification_acceptance_publication(
            acceptance_publication
        )
    ) == acceptance_publication


def test_qualification_rejects_complete_or_operational_target() -> None:
    document = _document()
    complete = replace(
        document,
        definitions=(
            replace(document.definitions[0], title="Already", intent="Complete"),
        ),
    )
    proposal, acceptance = _authorities(complete)
    with pytest.raises(GoalPhaseMigratedDefinitionQualificationError, match="complete"):
        _ = plan_goal_phase_migrated_definition_qualification(
            source_document=complete,
            proposal_publication=proposal,
            acceptance_publication=acceptance,
        )


def test_plan_revalidates_mutated_carrier_and_authority() -> None:
    document = _document()
    proposal, acceptance = _authorities(document)
    plan = plan_goal_phase_migrated_definition_qualification(
        source_document=document,
        proposal_publication=proposal,
        acceptance_publication=acceptance,
    )
    object.__setattr__(plan.after_document, "source_refs", ("forged:source",))
    with pytest.raises(GoalPhaseMigratedDefinitionQualificationError, match="outside"):
        plan.__post_init__()


def test_acceptance_must_bind_exact_proposal_publication() -> None:
    document = _document()
    proposal, acceptance = _authorities(document)
    object.__setattr__(acceptance.acceptance, "proposal_publication_authority_ref", "forged:authority")
    with pytest.raises(GoalPhaseMigratedDefinitionQualificationError, match="wrong proposal"):
        _ = plan_goal_phase_migrated_definition_qualification(
            source_document=document,
            proposal_publication=proposal,
            acceptance_publication=acceptance,
        )


def test_publication_receipt_is_strict_and_plan_bound() -> None:
    document = _document()
    proposal, acceptance = _authorities(document)
    plan = plan_goal_phase_migrated_definition_qualification(
        source_document=document,
        proposal_publication=proposal,
        acceptance_publication=acceptance,
    )
    receipt = issue_goal_phase_migrated_definition_qualification_publication_receipt(
        plan=plan,
        publication_issue_authority_ref="goal-publication-issue:sha256:" + "1" * 64,
        repository_parent_ref="2" * 40,
        repository_commit_ref="3" * 40,
        repository_commit_receipt_ref="repository-commit:" + "3" * 40,
        changed_path=proposal.proposal.goal_path,
        reconciliation_disposition="clear",
    )
    assert decode_goal_phase_migrated_definition_qualification_publication_receipt(
        encode_goal_phase_migrated_definition_qualification_publication_receipt(
            receipt
        )
    ) == receipt
    with pytest.raises(GoalPhaseMigratedDefinitionQualificationError, match="Goal path"):
        _ = issue_goal_phase_migrated_definition_qualification_publication_receipt(
            plan=plan,
            publication_issue_authority_ref="goal-publication-issue:sha256:" + "1" * 64,
            repository_parent_ref="2" * 40,
            repository_commit_ref="3" * 40,
            repository_commit_receipt_ref="repository-commit:" + "3" * 40,
            changed_path="docs/goals/other.md",
            reconciliation_disposition="clear",
        )


def test_acceptance_requires_the_authorized_goal_owner_execution() -> None:
    document = _document()
    proposal, accepted = _authorities(document)
    foreign_acceptance = replace(
        accepted.acceptance,
        accepting_execution_id="codex-foreign",
    )
    foreign_issue = replace(
        accepted.issue_authority,
        owner_execution_id="codex-foreign",
    )
    with pytest.raises(
        GoalPhaseMigratedDefinitionQualificationError,
        match="authorized coordinator",
    ):
        _ = GoalPhaseDefinitionQualificationAcceptancePublicationV1(
            acceptance=foreign_acceptance,
            artifact_path=accepted.artifact_path,
            publication_commit=accepted.publication_commit,
            artifact_blob=accepted.artifact_blob,
            repository_commit_receipt_ref=accepted.repository_commit_receipt_ref,
            issue_authority=foreign_issue,
            proposal_publication=proposal,
            delegation=accepted.delegation,
        )


def test_committed_goal_owner_profile_cannot_name_nonowner_coordinator() -> None:
    document = _document()
    _, accepted = _authorities(document)
    authority = replace(
        accepted.delegation.authority,
        coordinator_execution_id="codex-foreign",
    )
    publication = replace(
        accepted.delegation.publication,
        coordinator_execution_id="codex-foreign",
        coordinator_authority_ref=authority.authority_ref,
    )
    with pytest.raises(
        GoalPhaseMigratedDefinitionQualificationError,
        match="cannot delegate",
    ):
        _ = GoalCoordinatorDelegationPublicationV1(
            authority=authority,
            publication=publication,
        )
