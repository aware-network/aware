from __future__ import annotations

import pytest
from aware_goal_operational_runtime.dependencies import GoalDependencyRelation
from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.phase_contracts import (
    GoalLanePhase,
    GoalLanePhaseGate,
    GoalLanePhaseGateObservation,
    GoalLanePhaseGateOutcome,
    GoalLanePhaseState,
    GoalPhaseCoordinate,
    GoalPhaseDependency,
)
from aware_goal_operational_runtime.phase_frontier import goal_phase_dependency_digest
from aware_goal_operational_runtime.phase_migrated_gate_evaluation import (
    EVALUATOR_PROFILE,
    DefinitionQualificationEvidenceV1,
    DependencyAcceptanceEvidenceV1,
    DependencyBindingV1,
    DependencyState,
    EvaluationResult,
    EvidenceBundleV1,
    ImplementationCloseoutEvidenceV1,
    ImplementationPublicationEvidenceV1,
    IndependentAcceptanceEvidenceV1,
    IssueAuthorityV1,
    MigratedPhaseGateEvaluationError,
    QualificationAcceptanceV1,
    QualificationProposalV1,
    ReasonCode,
    SourceCurrentness,
    SourceEpochV1,
    VerifiedMigratedPhaseGateAuthoritySourcesV1,
    VerifiedMigratedPhaseGateAuthorityV1,
    _seal_migrated_phase_gate_authority_sources,
    decode_evidence_bundle,
    decode_migrated_phase_gate_evaluation,
    decode_qualification_acceptance,
    decode_qualification_proposal,
    evaluate_migrated_phase_gate,
    verify_migrated_phase_gate_authority,
)

COORDINATE = GoalPhaseCoordinate(
    goal_tag="goal/2026-09-10/actorworld-v0",
    lane_key="runtime-authority-retreat",
    phase_key="r3-environment-authority-retreat",
)
PREREQUISITE = GoalPhaseCoordinate(
    goal_tag="goal/2026-09-10/actorworld-v0",
    lane_key="experience-identity-participation",
    phase_key="i2-experience-participation",
)


def _epoch(
    key: str, currentness: SourceCurrentness = SourceCurrentness.EQUAL
) -> SourceEpochV1:
    return SourceEpochV1(
        repository_ref="repository:aware-dev",
        source_commit=f"commit:{key}",
        observed_head="commit:head",
        path=f"authority/{key}.json",
        blob=f"blob:{key}",
        currentness=currentness,
        protected_paths=(f"authority/{key}.json",),
    )


def _issue(path: str, owner: str, status: str = "In Progress") -> IssueAuthorityV1:
    return IssueAuthorityV1(
        issue_path=path,
        issue_blob=f"blob:{path}",
        owner_execution_id=owner,
        status=status,
        scope_digest=f"scope:{path}",
    )


def _dependency_authority(
    state: DependencyState,
) -> tuple[GoalPhaseDependency, dict[str, object]]:
    gate = GoalLanePhaseGate(
        gate_key="i2-acceptance",
        promise="Accept I2.",
        gate_contract_ref="contract:i2-v1",
        evidence_schema_ref="evidence:i2-v1",
    )
    outcome = {
        DependencyState.SATISFIED: GoalLanePhaseGateOutcome.SATISFIED,
        DependencyState.PENDING: GoalLanePhaseGateOutcome.SATISFIED,
        DependencyState.STALE: GoalLanePhaseGateOutcome.STALE,
        DependencyState.REJECTED: GoalLanePhaseGateOutcome.REJECTED,
    }.get(state)
    observations = ()
    if outcome is not None:
        observations = (
            GoalLanePhaseGateObservation(
                observation_ref=f"gate-observation:i2:{outcome.value}",
                gate_digest=gate.gate_digest,
                outcome=outcome,
                evaluator_ref="evaluator:canonical",
                evidence_refs=("evidence:i2",)
                if outcome
                in {
                    GoalLanePhaseGateOutcome.SATISFIED,
                    GoalLanePhaseGateOutcome.REJECTED,
                }
                else (),
                source_revision_refs=("commit:prerequisite",),
                evaluated_at="2026-09-22T00:00:00Z",
                currentness_ref="currentness:i2",
            ),
        )
    prerequisite = GoalLanePhase(
        coordinate=PREREQUISITE,
        title="I2",
        ordinal=2,
        intent="Accept participation.",
        state=(
            GoalLanePhaseState.ACCEPTED
            if state is DependencyState.SATISFIED
            else GoalLanePhaseState.ACTIVE
        ),
        gate=gate,
        gate_observations=observations,
        last_receipt_ref=(
            "goal-phase-acceptance:sha256:" + "a" * 64
            if state is DependencyState.SATISFIED
            else None
        ),
    )
    dependency = GoalPhaseDependency(
        owner_goal_tag=COORDINATE.goal_tag,
        dependency_key="i2-requires-acceptance",
        dependent=COORDINATE,
        prerequisite=PREREQUISITE,
        required_gate_digest=gate.gate_digest,
        relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
        reason="I2 acceptance is required.",
    )
    authority: dict[str, object] = {
        "declaration": dependency,
        "availability": (
            "not_evaluated"
            if state is DependencyState.NOT_EVALUATED
            else "unresolved"
            if state is DependencyState.UNRESOLVED
            else "resolved"
        ),
        "dependent_source_revision_ref": "commit:dependent",
        "prerequisite_source_revision_ref": "commit:prerequisite",
        "prerequisite_phase": prerequisite,
        "evaluator_ref": "evaluator:canonical",
        "currentness_ref": "currentness:dependency",
        "authority_ref": "goal-phase-bootstrap-acceptance-authority:receipt",
        "evidence_schema_id": DependencyAcceptanceEvidenceV1.schema_id,
    }
    return dependency, authority


def _values(
    *,
    dependency_state: DependencyState = DependencyState.SATISFIED,
    reviewer: str = "codex-reviewer",
    review_owner: str = "codex-reviewer",
    implementation_owner: str = "codex-implementer",
    review_verdict: str = "accepted",
    dependency_currentness: SourceCurrentness = SourceCurrentness.EQUAL,
    implementation_gate_digest: str = "sha256:gate",
    review_changed_path_digest: str | None = None,
):
    dependency_declaration, _ = _dependency_authority(dependency_state)
    definition = DefinitionQualificationEvidenceV1(
        role="definition_qualification",
        role_key="definition_qualification",
        source_epoch=_epoch("definition"),
        m13_publication_receipt_ref="goal-m13-publication:receipt",
        reconciliation_receipt_ref="goal-reconciliation:receipt",
        goal_path="docs/goals/actorworld.md",
        goal_tag=COORDINATE.goal_tag,
        coordinate=COORDINATE,
        before_document_ref="goal-document:before",
        after_document_ref="goal-document:after",
        before_definition_ref="goal-definition:before",
        after_definition_ref="goal-definition:after",
        proposal_publication_ref="goal-proposal-publication:m13",
        acceptance_publication_ref="goal-acceptance-publication:m13",
        publication_commit="commit:m13",
        goal_blob="blob:goal",
        repository_commit_receipt_ref="repository-commit:commit:m13",
    )
    implementation_issue = _issue("docs/issues/implementation.md", implementation_owner)
    implementation = ImplementationPublicationEvidenceV1(
        role="implementation_publication",
        role_key="implementation_publication",
        source_epoch=_epoch("implementation"),
        coordinate=COORDINATE,
        definition_ref="goal-definition:after",
        gate_digest=implementation_gate_digest,
        issue_authority=implementation_issue,
        parent_commit="commit:parent",
        implementation_commit="commit:implementation",
        changed_paths=("runtime.py",),
        tree_entry_oids=("blob:runtime",),
        repository_commit_receipt_ref="repository-commit:implementation",
    )
    review = IndependentAcceptanceEvidenceV1(
        role="independent_acceptance",
        role_key="independent_acceptance",
        source_epoch=_epoch("review"),
        verdict=review_verdict,
        reviewer_execution_id=reviewer,
        reviewed_implementation_commit="commit:implementation",
        changed_path_digest=fingerprint(
            {"changed_paths": ["runtime.py"], "tree_entry_oids": ["blob:runtime"]}
        )
        if review_changed_path_digest is None
        else review_changed_path_digest,
        coordinate=COORDINATE,
        definition_ref="goal-definition:after",
        gate_digest="sha256:gate",
        validation_evidence_refs=("proof:tests",),
        review_issue_authority=_issue("docs/issues/review.md", review_owner),
        artifact_path="docs/reviews/verdict.json",
        artifact_blob="blob:verdict",
        publication_commit="commit:review",
        repository_commit_receipt_ref="repository-commit:review",
    )
    closeout = ImplementationCloseoutEvidenceV1(
        role="implementation_closeout",
        role_key="implementation_closeout",
        source_epoch=_epoch("closeout"),
        issue_path=implementation_issue.issue_path,
        owner_execution_id=implementation_issue.owner_execution_id,
        scope_digest=implementation_issue.scope_digest,
        before_issue_blob=implementation_issue.issue_blob,
        after_issue_blob="blob:implementation-closed",
        implementation_commit="commit:implementation",
        independent_verdict_ref=review.evidence_ref,
        closeout_commit="commit:closeout",
        repository_commit_receipt_ref="repository-commit:closeout",
    )
    dependency = DependencyAcceptanceEvidenceV1(
        role="dependency:i2-requires-acceptance",
        role_key="i2-requires-acceptance",
        source_epoch=_epoch("dependency", dependency_currentness),
        dependency_key="i2-requires-acceptance",
        dependency_digest=goal_phase_dependency_digest(dependency_declaration),
        relation="requires_acceptance",
        dependent=COORDINATE,
        prerequisite=PREREQUISITE,
        dependent_source_revision_ref="commit:dependent",
        prerequisite_source_revision_ref="commit:prerequisite",
        required_gate_digest=dependency_declaration.required_gate_digest,
        state=dependency_state,
        authority_ref="goal-phase-bootstrap-acceptance-authority:receipt",
    )
    entries = tuple(
        sorted(
            (definition, dependency, implementation, review, closeout),
            key=lambda item: (item.role, item.role_key),
        )
    )
    bundle = EvidenceBundleV1(entries=entries)
    roles = tuple(sorted(item.role for item in entries))
    proposal = QualificationProposalV1(
        proposal_ref="goal-migrated-phase-proposal:one",
        goal_path="docs/goals/actorworld.md",
        goal_tag=COORDINATE.goal_tag,
        coordinate=COORDINATE,
        document_ref="goal-document:after",
        source_revision_ref="commit:head",
        definition_ref="goal-definition:after",
        gate_digest="sha256:gate",
        evaluator_profile=EVALUATOR_PROFILE,
        dependency_bindings=(
            DependencyBindingV1(
                dependency_key="i2-requires-acceptance",
                dependency_digest=goal_phase_dependency_digest(dependency_declaration),
            ),
        ),
        evidence_role_keys=roles,
    )
    acceptance = QualificationAcceptanceV1(
        acceptance_ref="goal-migrated-phase-acceptance:one",
        proposal_ref=proposal.proposal_ref,
        accepting_execution_id="codex-coordinator",
        acceptance_issue_authority=_issue(
            "docs/issues/acceptance.md", "codex-coordinator"
        ),
        coordinator_authority_ref="goal-coordinator-authority:one",
        coordinator_current=True,
        decision="authorize_evaluation",
        evidence_bundle_ref=bundle.bundle_ref,
    )
    return proposal, acceptance, bundle


def _sources(
    values, *, authority_state: DependencyState | None = None
) -> VerifiedMigratedPhaseGateAuthoritySourcesV1:
    proposal, acceptance, bundle = values
    records = {item.evidence_ref: item.to_wire() for item in bundle.entries}
    epochs = {
        (
            item.source_epoch.repository_ref,
            item.source_epoch.source_commit,
            item.source_epoch.observed_head,
            item.source_epoch.path,
        ): item.source_epoch.to_wire()
        for item in bundle.entries
    }
    dependency_item = next(
        item
        for item in bundle.entries
        if isinstance(item, DependencyAcceptanceEvidenceV1)
    )
    _, dependency_authority = _dependency_authority(
        dependency_item.state if authority_state is None else authority_state
    )
    sources = _seal_migrated_phase_gate_authority_sources(
        proposal_wire=proposal.to_wire(),
        acceptance_wire=acceptance.to_wire(),
        evidence_wires=records,
        source_epoch_wires=epochs,
        role_currentness={
            item.evidence_ref: item.source_epoch.currentness.value
            for item in bundle.entries
        },
        coordinator_wire={
            "goal_tag": proposal.goal_tag,
            "execution_id": acceptance.accepting_execution_id,
            "current": acceptance.coordinator_current,
            "authority_ref": acceptance.coordinator_authority_ref,
        },
        dependency_authorities={"i2-requires-acceptance": dependency_authority},
    )
    return sources


def _verify(
    values, *, authority_state: DependencyState | None = None
) -> VerifiedMigratedPhaseGateAuthorityV1:
    proposal, acceptance, bundle = values
    return verify_migrated_phase_gate_authority(
        proposal,
        acceptance,
        bundle,
        authority_sources=_sources(values, authority_state=authority_state),
    )


def _evaluate(values):
    return evaluate_migrated_phase_gate(_verify(values))


def test_current_satisfied_bundle_derives_observations() -> None:
    proposal, acceptance, bundle = _values()
    assert decode_qualification_proposal(proposal.to_wire()) == proposal
    assert decode_qualification_acceptance(acceptance.to_wire()) == acceptance
    assert decode_evidence_bundle(bundle.to_wire()) == bundle
    evaluation = _evaluate((proposal, acceptance, bundle))
    assert decode_migrated_phase_gate_evaluation(evaluation.to_wire()) == evaluation
    assert evaluation.result is EvaluationResult.SATISFIED
    assert evaluation.reasons == ()
    assert evaluation.gate_observation_ref is not None
    assert len(evaluation.dependency_observation_refs) == 1
    assert evaluation.dependency_observation_refs[0].startswith(
        "goal-phase-dependency-observation:"
    )


@pytest.mark.parametrize(
    ("state", "expected", "code"),
    [
        (
            DependencyState.PENDING,
            EvaluationResult.REJECTED,
            ReasonCode.DEPENDENCY_PENDING,
        ),
        (
            DependencyState.REJECTED,
            EvaluationResult.REJECTED,
            ReasonCode.DEPENDENCY_REJECTED,
        ),
        (DependencyState.STALE, EvaluationResult.STALE, ReasonCode.DEPENDENCY_STALE),
        (
            DependencyState.UNRESOLVED,
            EvaluationResult.UNAVAILABLE,
            ReasonCode.DEPENDENCY_UNRESOLVED,
        ),
        (
            DependencyState.NOT_EVALUATED,
            EvaluationResult.UNAVAILABLE,
            ReasonCode.DEPENDENCY_NOT_EVALUATED,
        ),
    ],
)
def test_dependency_reduction_is_total(state, expected, code) -> None:
    evaluation = _evaluate(_values(dependency_state=state))
    assert evaluation.result is expected
    assert code in {reason.code for reason in evaluation.reasons}
    assert evaluation.gate_observation_ref is None


def test_rejected_precedes_stale() -> None:
    evaluation = _evaluate(
        _values(
            dependency_state=DependencyState.PENDING,
            dependency_currentness=SourceCurrentness.STALE,
        )
    )
    assert evaluation.result is EvaluationResult.REJECTED


def test_foreign_reviewer_substitution_fails_before_evaluation() -> None:
    with pytest.raises(MigratedPhaseGateEvaluationError, match="foreign reviewer"):
        _evaluate(_values(reviewer="codex-foreign", review_owner="codex-reviewer"))


def test_implementer_self_review_fails_before_evaluation() -> None:
    with pytest.raises(MigratedPhaseGateEvaluationError, match="self-review"):
        _evaluate(
            _values(
                reviewer="codex-implementer",
                review_owner="codex-implementer",
                implementation_owner="codex-implementer",
            )
        )


def test_sealed_authority_cannot_be_mutated_after_verification() -> None:
    verified = _verify(_values())
    object.__setattr__(verified, "coordinator_current", False)
    with pytest.raises(MigratedPhaseGateEvaluationError, match="forged or mutated"):
        evaluate_migrated_phase_gate(verified)


def test_public_verifier_rejects_caller_constructed_authority_sources() -> None:
    proposal, acceptance, bundle = _values()
    forged = object.__new__(VerifiedMigratedPhaseGateAuthoritySourcesV1)
    with pytest.raises(MigratedPhaseGateEvaluationError, match="not sealed"):
        verify_migrated_phase_gate_authority(
            proposal,
            acceptance,
            bundle,
            authority_sources=forged,
        )


def test_seal_binds_complete_prerequisite_observation_semantics() -> None:
    values = _values()
    sources = _sources(values)
    authority = sources.dependency_authorities["i2-requires-acceptance"]
    prerequisite = authority["prerequisite_phase"]
    assert type(prerequisite) is GoalLanePhase
    observation = prerequisite.gate_observations[0]
    object.__setattr__(observation, "currentness_ref", "currentness:forged")
    proposal, acceptance, bundle = values
    with pytest.raises(MigratedPhaseGateEvaluationError, match="forged or mutated"):
        verify_migrated_phase_gate_authority(
            proposal, acceptance, bundle, authority_sources=sources
        )


def test_caller_authored_dependency_outcome_cannot_override_evaluator() -> None:
    with pytest.raises(
        MigratedPhaseGateEvaluationError, match="differs from canonical evaluation"
    ):
        _verify(
            _values(dependency_state=DependencyState.SATISFIED),
            authority_state=DependencyState.PENDING,
        )


def test_cross_role_gate_mismatch_fails_before_evaluation() -> None:
    with pytest.raises(
        MigratedPhaseGateEvaluationError,
        match="implementation publication differs from proposal",
    ):
        _verify(_values(implementation_gate_digest="sha256:foreign-gate"))


def test_review_changed_paths_must_match_implementation_publication() -> None:
    with pytest.raises(
        MigratedPhaseGateEvaluationError, match="changed-path digest differs"
    ):
        _verify(_values(review_changed_path_digest="sha256:foreign-paths"))


def test_post_construction_mutation_fails_revalidation() -> None:
    proposal, acceptance, bundle = _values()
    review = next(
        item for item in bundle.entries if type(item) is IndependentAcceptanceEvidenceV1
    )
    object.__setattr__(review, "reviewer_execution_id", "codex-forged")
    with pytest.raises(MigratedPhaseGateEvaluationError):
        _evaluate((proposal, acceptance, bundle))


def test_strict_decoders_reject_unknown_fields_and_boolean_substitution() -> None:
    proposal, acceptance, bundle = _values()
    proposal_wire = proposal.to_wire()
    proposal_wire["unknown"] = "value"
    with pytest.raises(MigratedPhaseGateEvaluationError, match="fields"):
        decode_qualification_proposal(proposal_wire)
    proposal_wire = proposal.to_wire()
    proposal_wire["proposal_ref"] = "goal-migrated-phase-proposal:forged"
    with pytest.raises(MigratedPhaseGateEvaluationError, match="proposal ref"):
        decode_qualification_proposal(proposal_wire)
    acceptance_wire = acceptance.to_wire()
    acceptance_wire["coordinator_current"] = 1
    with pytest.raises(TypeError, match="exact bool"):
        decode_qualification_acceptance(acceptance_wire)
    bundle_wire = bundle.to_wire()
    bundle_wire["bundle_ref"] = "goal-migrated-phase-evidence-bundle:forged"
    with pytest.raises(MigratedPhaseGateEvaluationError, match="bundle ref"):
        decode_evidence_bundle(bundle_wire)
