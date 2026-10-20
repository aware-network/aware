from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from typing import cast

import pytest
from aware_goal_operational_runtime import (
    GoalDependencyRelation,
    GoalGlobalDirectionAuthorityV1,
    GoalLaneDirectionAuthorityV1,
    GoalLanePhase,
    GoalLanePhaseDefinitionV1,
    GoalLanePhaseGate,
    GoalLanePhaseState,
    GoalLanePhaseWork,
    GoalLanePhaseWorkDisposition,
    GoalLanePhaseWorkRole,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
    GoalPhaseDependency,
    GoalPhaseExecutionAuthorityV1,
    GoalPhaseNativeAdvancementDisposition,
    GoalPhaseNativeCompatibilityRelation,
    GoalPhaseNativeDocumentV2,
    GoalPhaseNativeDocumentV3,
    GoalPhaseOperationJournalEntryV1,
    GoalPhaseOperationJournalV1,
    GoalPhaseNativeRetainedCurrentness,
    GoalPhaseNativeScopeDescriptorV1,
    GoalPhaseNativeScopeError,
    GoalPhaseNativeScopeProfile,
    GoalPhaseNativeScopeProjectionV1,
    GoalPhaseNativeScopeRelation,
    GoalPhaseNativeScopeSourceEpochV1,
    GoalPhaseProjectionRevisionV1,
    GoalPhaseSourceBindingV1,
    GoalPhaseUnresolvedDependencyV1,
    assess_goal_phase_native_scope_advancement,
    admit_goal_phase_native_scope_delta,
    apply_goal_phase_mutation_to_native_document,
    bind_goal_phase_publication,
    decode_goal_phase_native_scope_advancement,
    decode_goal_phase_native_scope_projection,
    encode_goal_phase_native_scope_advancement,
    encode_goal_phase_native_scope_projection,
    issue_goal_phase_publication_receipt,
    plan_goal_phase_same_gate_successor,
    project_goal_phase_native_scope,
    reconcile_goal_phase_projection,
    verify_goal_phase_native_scope_source_epoch,
    verify_goal_phase_projection_currentness,
)

GOAL = "goal/2026-09-10/actorworld"
_OLD_COMMIT = b"tree " + b"0" * 40 + b"\n\nold\n"
OLD = hashlib.sha1(
    b"commit " + str(len(_OLD_COMMIT)).encode() + b"\0" + _OLD_COMMIT,
    usedforsecurity=False,
).hexdigest()
_NEW_COMMIT = b"tree " + b"0" * 40 + b"\nparent " + OLD.encode() + b"\n\nnew\n"
NEW = hashlib.sha1(
    b"commit " + str(len(_NEW_COMMIT)).encode() + b"\0" + _NEW_COMMIT,
    usedforsecurity=False,
).hexdigest()


def _gate(key: str) -> GoalLanePhaseGate:
    return GoalLanePhaseGate(
        gate_key=key,
        promise=f"Accept {key}.",
        gate_contract_ref=f"contract:{key}",
        evidence_schema_ref=f"evidence:{key}",
    )


G2 = GoalPhaseCoordinate(GOAL, "goal-ontology", "g2")
R3 = GoalPhaseCoordinate(GOAL, "runtime-retreat", "r3")
G2_GATE = _gate("g2")
R3_GATE = _gate("r3")


def _execution() -> GoalPhaseExecutionAuthorityV1:
    digest = "sha256:" + "a" * 64
    return GoalPhaseExecutionAuthorityV1(
        source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
        parity_ref="goal-phase-native-compatibility-parity:" + digest,
        proposal_aggregate_ref=(
            "goal-phase-native-operational-bootstrap-proposal:" + digest
        ),
        coordinator_acceptance_ref=(
            "goal-phase-native-operational-bootstrap-coordinator-acceptance:" + digest
        ),
    )


def _document(*, operational_r3: bool = False) -> GoalPhaseNativeDocumentV2:
    phases = ()
    if operational_r3:
        phases = (
            GoalLanePhase(
                coordinate=R3,
                title="Environment inhabitation",
                ordinal=1,
                intent="Admit Environment honestly.",
                state=GoalLanePhaseState.ACTIVE,
                gate=R3_GATE,
            ),
        )
    return GoalPhaseNativeDocumentV2(
        goal_tag=GOAL,
        compatibility_projection_sha256="sha256:" + "b" * 64,
        compatibility_projection_byte_count=100,
        definitions=(
            GoalLanePhaseDefinitionV1(
                coordinate=G2,
                ordinal=1,
                title="Goal Ontology",
                intent="Persist Goal authority.",
                gate=G2_GATE,
            ),
            GoalLanePhaseDefinitionV1(
                coordinate=R3,
                ordinal=1,
                title="Environment inhabitation",
                intent="Admit Environment honestly.",
                gate=R3_GATE,
            ),
        ),
        operational_bundle=GoalPhaseContractBundleV1(phases, ()),
        unresolved_dependencies=(),
        source_refs=("repository-path:docs/goals/actorworld.md",),
        execution_authority=_execution(),
    )


def _global(revision: str, *, status: str = "active") -> GoalGlobalDirectionAuthorityV1:
    return GoalGlobalDirectionAuthorityV1(
        goal_tag=GOAL,
        lifecycle_status=status,
        owner_ref="codex-owner",
        governance_authority_refs=("goal-governance:accepted",),
        hold_state="clear",
        hold_authority_refs=(),
        execution_authority_ref=_execution().authority_ref,
        compatibility_guard_ref="goal-compatibility-guard:stable",
        source_revision_ref=revision,
        projector_ref="goal-compatibility-direction-projector:v1",
        projection_receipt_ref=f"goal-direction-projection:{revision}",
    )


def _lanes(
    revision: str, *, g2_state: str = "active"
) -> tuple[GoalLaneDirectionAuthorityV1, ...]:
    return (
        GoalLaneDirectionAuthorityV1(
            goal_tag=GOAL,
            lane_key="goal-ontology",
            role="Goal authority",
            owner_ref="codex-g2",
            operational_state=g2_state,
            state_detail=None,
            blocker_authority_refs=(),
            current_issue_ref=None,
                current_issue_authority_ref=None,
                compatibility_guard_ref="goal-lane-compatibility-guard:g2",
            source_revision_ref=revision,
            projector_ref="goal-compatibility-direction-projector:v1",
            projection_receipt_ref=f"goal-lane-projection:g2:{revision}",
        ),
        GoalLaneDirectionAuthorityV1(
            goal_tag=GOAL,
            lane_key="runtime-retreat",
            role="Runtime authority",
            owner_ref="codex-r3",
            operational_state="active",
            state_detail=None,
            blocker_authority_refs=(),
            current_issue_ref=None,
                current_issue_authority_ref=None,
                compatibility_guard_ref="goal-lane-compatibility-guard:r3",
            source_revision_ref=revision,
            projector_ref="goal-compatibility-direction-projector:v1",
            projection_receipt_ref=f"goal-lane-projection:r3:{revision}",
        ),
    )


def _source(revision: str, marker: str) -> GoalPhaseSourceBindingV1:
    return GoalPhaseSourceBindingV1(
        repository_revision_ref=revision,
        goal_sha256="sha256:" + marker * 64,
        goal_blob_oid=marker * 40,
    )


def _descriptor(
    profile: GoalPhaseNativeScopeProfile,
) -> GoalPhaseNativeScopeDescriptorV1:
    return GoalPhaseNativeScopeDescriptorV1(
        root=G2,
        profile=profile,
        consumer_authority_ref="goal-phase-pursuit:g2",
        projector_ref="goal-phase-native-scope-projector:v1",
    )


def _project(
    document: GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3,
    revision: str,
    *,
    profile: GoalPhaseNativeScopeProfile = GoalPhaseNativeScopeProfile.PHASE_DIRECTION,
    status: str = "active",
    g2_state: str = "active",
):
    return project_goal_phase_native_scope(
        document=document,
        descriptor=_descriptor(profile),
        goal_authority=_global(revision, status=status),
        lane_authorities=_lanes(revision, g2_state=g2_state),
    )


def _advance(
    before: GoalPhaseNativeScopeProjectionV1,
    after: GoalPhaseNativeScopeProjectionV1,
):
    return assess_goal_phase_native_scope_advancement(
        previous=before,
        candidate=after,
        source_epoch=_epoch("descendant"),
    )


def _epoch(relation: str) -> GoalPhaseNativeScopeSourceEpochV1:
    previous = _source(OLD, "1")
    candidate = _source(NEW, "2")
    goal_path = "docs/goals/actorworld.md"
    return verify_goal_phase_native_scope_source_epoch(
        goal_path=goal_path,
        previous_source=previous,
        candidate_source=candidate,
        repository_resolver=lambda path, old, new: {
            "observed_head_ref": NEW,
            "lineage": relation,
            "previous_source": previous.to_wire(),
            "candidate_source": candidate.to_wire(),
            "compatibility_relation": GoalPhaseNativeCompatibilityRelation.EXACT.value,
        },
    )


def test_r3_changes_graph_but_preserves_g2_direction() -> None:
    before_document = _document()
    after_document = _document(operational_r3=True)
    g2 = _advance(_project(before_document, OLD), _project(after_document, NEW))
    assert g2.scope_relation is GoalPhaseNativeScopeRelation.UNCHANGED
    assert g2.retained_scope_currentness is GoalPhaseNativeRetainedCurrentness.CURRENT
    assert g2.disposition is GoalPhaseNativeAdvancementDisposition.REOBSERVED_UNCHANGED

    graph = _advance(
        _project(before_document, OLD, profile=GoalPhaseNativeScopeProfile.GOAL_GRAPH),
        _project(after_document, NEW, profile=GoalPhaseNativeScopeProfile.GOAL_GRAPH),
    )
    assert graph.scope_relation is GoalPhaseNativeScopeRelation.CHANGED
    assert (
        graph.disposition
        is GoalPhaseNativeAdvancementDisposition.ADMITTED_DELTA_REQUIRED
    )


def test_v3_journal_changes_only_its_phase_lane_and_graph_scope() -> None:
    before = _document(operational_r3=True)
    entry = GoalPhaseOperationJournalEntryV1(
        operation_kind="approve_pursuit", decision="approve",
        coordinate=R3, gate_digest=R3_GATE.gate_digest,
        source_preimage_ref=before.document_ref,
        actor_ref="identity:reviewer",
        action_occurrence_ref="actor-action-occurrence:sha256:" + "1" * 64,
        policy_ref="goal-phase-approval-policy:sha256:" + "2" * 64,
        policy_digest="sha256:" + "3" * 64,
        idempotency_key="r3-approval", delta_ref="goal-phase-delta:sha256:" + "4" * 64,
        event_ref="goal-phase-event:sha256:" + "5" * 64,
    )
    after = GoalPhaseNativeDocumentV3(
        goal_tag=before.goal_tag,
        compatibility_projection_sha256=before.compatibility_projection_sha256,
        compatibility_projection_byte_count=before.compatibility_projection_byte_count,
        definitions=before.definitions,
        operational_bundle=before.operational_bundle,
        unresolved_dependencies=before.unresolved_dependencies,
        source_refs=before.source_refs,
        execution_authority=before.execution_authority,
        phase_operation_journal=GoalPhaseOperationJournalV1((entry,)),
    )
    g2 = _advance(_project(before, OLD), _project(after, NEW))
    assert g2.scope_relation is GoalPhaseNativeScopeRelation.UNCHANGED
    assert g2.disposition is GoalPhaseNativeAdvancementDisposition.REOBSERVED_UNCHANGED

    r3_descriptor = GoalPhaseNativeScopeDescriptorV1(
        root=R3, profile=GoalPhaseNativeScopeProfile.PHASE_DIRECTION,
        consumer_authority_ref="goal-phase-pursuit:r3",
        projector_ref="goal-phase-native-scope-projector:v1",
    )
    r3_before = project_goal_phase_native_scope(
        document=before, descriptor=r3_descriptor,
        goal_authority=_global(OLD), lane_authorities=_lanes(OLD),
    )
    r3_after = project_goal_phase_native_scope(
        document=after, descriptor=r3_descriptor,
        goal_authority=_global(NEW), lane_authorities=_lanes(NEW),
    )
    r3 = _advance(r3_before, r3_after)
    assert r3.scope_relation is GoalPhaseNativeScopeRelation.CHANGED
    assert r3.disposition is GoalPhaseNativeAdvancementDisposition.ADMITTED_DELTA_REQUIRED
    assert any(change.kind == "phase-operation-journal" for change in r3.changes)

    graph = _advance(
        _project(before, OLD, profile=GoalPhaseNativeScopeProfile.GOAL_GRAPH),
        _project(after, NEW, profile=GoalPhaseNativeScopeProfile.GOAL_GRAPH),
    )
    assert graph.scope_relation is GoalPhaseNativeScopeRelation.CHANGED


def test_exact_continue_work_delta_admits_over_stable_background_ambiguity() -> None:
    phase = GoalLanePhase(
        coordinate=G2,
        title="Goal Ontology",
        ordinal=1,
        intent="Persist Goal authority.",
        state=GoalLanePhaseState.ACTIVE,
        gate=G2_GATE,
        work_associations=(
            GoalLanePhaseWork(
                association_ref="phase-work:authority",
                issue_ref="docs/issues/authority.md",
                role=GoalLanePhaseWorkRole.GOVERNANCE,
                disposition=GoalLanePhaseWorkDisposition.CURRENT,
                admitted_at="2026-09-21T00:00:00Z",
                receipt_ref="phase-work-admission:authority",
            ),
        ),
    )
    before_document = replace(
        _document(), operational_bundle=GoalPhaseContractBundleV1((phase,), ())
    )
    before_revision = GoalPhaseProjectionRevisionV1(
        "refs/heads/main", OLD, "1" * 40, "sha256:" + "1" * 64
    )
    plan = plan_goal_phase_same_gate_successor(
        phase=phase,
        expected_binding=bind_goal_phase_publication(
            phase, projection_revision=before_revision
        ),
        expected_current_issue_ref="docs/issues/authority.md",
        successor_issue_ref="docs/issues/implementation.md",
        successor_role=GoalLanePhaseWorkRole.IMPLEMENTATION,
        timestamp="2026-09-21T01:00:00Z",
        evidence_refs=("repository-commit:m9",),
    )
    after_document = apply_goal_phase_mutation_to_native_document(
        document=before_document, plan=plan
    )
    after_revision = GoalPhaseProjectionRevisionV1(
        "refs/heads/main", NEW, "2" * 40, "sha256:" + "2" * 64
    )
    publication = issue_goal_phase_publication_receipt(
        plan=plan,
        after_projection_revision=after_revision,
        repository_commit_receipt_ref="repository-commit:" + NEW,
        changed_path="docs/goals/actorworld.md",
    )
    reconciliation = reconcile_goal_phase_projection(
        publication_receipt=publication, worktree_current=True, index_current=True
    )

    def projection_resolver(_goal_path: str, _commit: str) -> dict[str, object]:
        return {
            "goal_path": "docs/goals/actorworld.md",
            "publication_receipt_ref": publication.receipt_ref,
            "publication_commit_ref": NEW,
            "observed_head_ref": NEW,
            "worktree_sha256": "sha256:" + "2" * 64,
            "index_blob_oid": "2" * 40,
        }

    projection_currentness = verify_goal_phase_projection_currentness(
        publication_receipt=publication,
        repository_resolver=projection_resolver,
    )
    before_lanes = list(_lanes(OLD))
    after_lanes = list(_lanes(NEW))
    for lanes in (before_lanes, after_lanes):
        lanes[0] = replace(
            lanes[0],
            current_issue_ref="docs/issues/unrelated.md",
            current_issue_authority_ref="issue-authority:stable",
        )
    descriptor = _descriptor(GoalPhaseNativeScopeProfile.PHASE_DIRECTION)
    before_scope = project_goal_phase_native_scope(
        document=before_document,
        descriptor=descriptor,
        goal_authority=_global(OLD),
        lane_authorities=tuple(before_lanes),
    )
    after_scope = project_goal_phase_native_scope(
        document=after_document,
        descriptor=descriptor,
        goal_authority=_global(NEW),
        lane_authorities=tuple(after_lanes),
    )
    epoch = _epoch("descendant")
    advancement = assess_goal_phase_native_scope_advancement(
        previous=before_scope, candidate=after_scope, source_epoch=epoch
    )
    assert advancement.scope_relation is GoalPhaseNativeScopeRelation.CHANGED
    admission = admit_goal_phase_native_scope_delta(
        advancement=advancement,
        previous_projection=before_scope,
        candidate_projection=after_scope,
        source_epoch=epoch,
        before_document=before_document,
        after_document=after_document,
        publication_receipt=publication,
        reconciliation_receipt=reconciliation,
        projection_currentness=projection_currentness,
    )
    assert admission.admitted_change.kind == "phase-operational"
    with pytest.raises(GoalPhaseNativeScopeError):
        forged = replace(advancement, changes=())
        admit_goal_phase_native_scope_delta(
            advancement=forged,
            previous_projection=before_scope,
            candidate_projection=after_scope,
            source_epoch=epoch,
            before_document=before_document,
            after_document=after_document,
            publication_receipt=publication,
            reconciliation_receipt=reconciliation,
            projection_currentness=projection_currentness,
        )

    for forged_field, forged_value in (
        ("worktree_sha256", "sha256:" + "3" * 64),
        ("index_blob_oid", "3" * 40),
    ):
        def forged_resolver(
            goal_path: str,
            commit: str,
            *,
            field: str = forged_field,
            value: str = forged_value,
        ) -> dict[str, object]:
            result = projection_resolver(goal_path, commit)
            result[field] = value
            return result

        with pytest.raises(GoalPhaseNativeScopeError):
            verify_goal_phase_projection_currentness(
                publication_receipt=publication,
                repository_resolver=forged_resolver,
            )


def _assert_authority_change_stales_g2(
    candidate: GoalPhaseNativeScopeProjectionV1, expected_kind: str
) -> None:
    document = _document()
    result = _advance(_project(document, OLD), candidate)
    assert result.retained_scope_currentness is GoalPhaseNativeRetainedCurrentness.STALE
    assert any(item.kind == expected_kind for item in result.changes)


def test_goal_authority_change_stales_g2() -> None:
    document = _document()
    _assert_authority_change_stales_g2(
        _project(document, NEW, status="parked"), "goal-global"
    )


def test_lane_authority_change_stales_g2() -> None:
    document = _document()
    _assert_authority_change_stales_g2(
        _project(document, NEW, g2_state="ready"), "lane-direction"
    )


def test_unproven_lineage_refuses() -> None:
    document = _document()
    result = assess_goal_phase_native_scope_advancement(
        previous=_project(document, OLD),
        candidate=_project(document, NEW),
        source_epoch=_epoch("unproven"),
    )
    assert result.scope_relation is GoalPhaseNativeScopeRelation.AMBIGUOUS
    assert result.disposition is GoalPhaseNativeAdvancementDisposition.REFUSE


def test_caller_cannot_construct_source_epoch_without_verifier() -> None:
    document = _document()
    with pytest.raises(GoalPhaseNativeScopeError, match="independently verified"):
        _ = assess_goal_phase_native_scope_advancement(
            previous=_project(document, OLD),
            candidate=_project(document, NEW),
            source_epoch=GoalPhaseNativeScopeSourceEpochV1(),
        )


def test_mutated_projection_cannot_forge_reobserved_unchanged() -> None:
    document = _document()
    previous = _project(document, OLD)
    candidate = _project(document, NEW, g2_state="ready")
    assert candidate.scope_digest != previous.scope_digest
    assert candidate.components != previous.components
    object.__setattr__(candidate, "scope_digest", previous.scope_digest)
    with pytest.raises(GoalPhaseNativeScopeError, match="scope digest"):
        _ = assess_goal_phase_native_scope_advancement(
            previous=previous,
            candidate=candidate,
            source_epoch=_epoch("descendant"),
        )


def test_mutated_verified_source_epoch_fails_closed() -> None:
    document = _document()
    epoch = _epoch("descendant")
    object.__setattr__(epoch, "observed_head_ref", OLD)
    with pytest.raises(GoalPhaseNativeScopeError):
        _ = assess_goal_phase_native_scope_advancement(
            previous=_project(document, OLD),
            candidate=_project(document, NEW),
            source_epoch=epoch,
        )


def test_dependency_snapshot_represents_not_evaluated_explicitly() -> None:
    document = replace(
        _document(),
        operational_bundle=GoalPhaseContractBundleV1(
            (),
            (
                GoalPhaseDependency(
                    owner_goal_tag=GOAL,
                    dependency_key="g2-requires-r3",
                    dependent=G2,
                    prerequisite=R3,
                    required_gate_digest=R3_GATE.gate_digest,
                    relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
                    reason="G2 requires accepted R3.",
                ),
            ),
        ),
    )
    projection = _project(document, OLD)
    snapshot = next(
        item for item in projection.components if item.kind == "dependency-snapshot"
    )
    assert snapshot.value_digest.startswith("sha256:")
    assert projection.qualification == "qualified"


def test_unresolved_cross_goal_dependency_makes_scope_ambiguous() -> None:
    external = GoalPhaseCoordinate("goal/2026-09-10/external", "runtime", "h5")
    document = replace(
        _document(),
        unresolved_dependencies=(
            GoalPhaseUnresolvedDependencyV1(
                owner_goal_tag=GOAL,
                dependency_key="g2-requires-external-h5",
                dependent=G2,
                prerequisite=external,
                relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
                reason="External H5 Gate is unresolved.",
            ),
        ),
    )
    projection = _project(document, OLD)
    assert projection.qualification == "ambiguous"
    assert projection.ambiguity_reasons == (
        f"external-dependency-currentness-unavailable:{GOAL}:g2-requires-external-h5",
    )


def test_authority_bound_decoders_recompute_canonical_payloads() -> None:
    document = _document()
    projection = _project(document, OLD)
    assert (
        decode_goal_phase_native_scope_projection(
            encode_goal_phase_native_scope_projection(projection),
            document=document,
            descriptor=_descriptor(GoalPhaseNativeScopeProfile.PHASE_DIRECTION),
            goal_authority=_global(OLD),
            lane_authorities=_lanes(OLD),
        )
        == projection
    )
    mutated = cast(
        dict[str, object],
        json.loads(encode_goal_phase_native_scope_projection(projection)),
    )
    components = cast(list[dict[str, object]], mutated["components"])
    components[0]["value_digest"] = "sha256:" + "0" * 64
    with pytest.raises(GoalPhaseNativeScopeError):
        _ = decode_goal_phase_native_scope_projection(
            json.dumps(mutated, sort_keys=True, separators=(",", ":")).encode(),
            document=document,
            descriptor=_descriptor(GoalPhaseNativeScopeProfile.PHASE_DIRECTION),
            goal_authority=_global(OLD),
            lane_authorities=_lanes(OLD),
        )

    advancement = _advance(projection, _project(document, NEW))
    assert (
        decode_goal_phase_native_scope_advancement(
            encode_goal_phase_native_scope_advancement(advancement),
            previous_document=document,
            candidate_document=document,
            descriptor=_descriptor(GoalPhaseNativeScopeProfile.PHASE_DIRECTION),
            previous_goal_authority=_global(OLD),
            candidate_goal_authority=_global(NEW),
            previous_lane_authorities=_lanes(OLD),
            candidate_lane_authorities=_lanes(NEW),
            source_epoch=_epoch("descendant"),
        )
        == advancement
    )
    with pytest.raises(GoalPhaseNativeScopeError, match="reference"):
        _ = replace(
            projection, projection_ref="goal-phase-native-scope-projection:forged"
        )
    with pytest.raises(GoalPhaseNativeScopeError, match="reference"):
        _ = replace(
            advancement,
            advancement_ref="goal-phase-native-scope-advancement:forged",
        )


def test_lane_current_issue_must_match_native_current_work() -> None:
    lane = replace(
        _lanes(OLD)[0],
        current_issue_ref="docs/issues/work.md",
        current_issue_authority_ref="issue-authority:work",
    )
    projection = project_goal_phase_native_scope(
        document=_document(),
        descriptor=_descriptor(GoalPhaseNativeScopeProfile.PHASE_DIRECTION),
        goal_authority=_global(OLD),
        lane_authorities=(lane, _lanes(OLD)[1]),
    )
    assert projection.qualification == "ambiguous"
    assert projection.ambiguity_reasons == (
        "lane-current-issue-disagrees-with-native-phase-work",
    )


def test_unrelated_lane_ambiguity_does_not_poison_phase_scope() -> None:
    ambiguous_r3 = replace(
        _lanes(OLD)[1],
        qualification="ambiguous",
        ambiguity_reasons=("lane-current-issue-status-disagreement",),
    )
    phase = project_goal_phase_native_scope(
        document=_document(),
        descriptor=_descriptor(GoalPhaseNativeScopeProfile.PHASE_DIRECTION),
        goal_authority=_global(OLD),
        lane_authorities=(_lanes(OLD)[0], ambiguous_r3),
    )
    assert phase.qualification == "qualified"

    graph = project_goal_phase_native_scope(
        document=_document(),
        descriptor=_descriptor(GoalPhaseNativeScopeProfile.GOAL_GRAPH),
        goal_authority=_global(OLD),
        lane_authorities=(_lanes(OLD)[0], ambiguous_r3),
    )
    assert graph.qualification == "ambiguous"


def test_compound_blocker_detail_is_semantic_and_requires_authority() -> None:
    with pytest.raises(GoalPhaseNativeScopeError, match="detail and authority"):
        _ = GoalLaneDirectionAuthorityV1(
            goal_tag=GOAL,
            lane_key="goal-ontology",
            role="Goal authority",
            owner_ref="codex-g2",
            operational_state="blocked",
            state_detail="waits for Workspace",
            blocker_authority_refs=(),
            current_issue_ref=None,
                current_issue_authority_ref=None,
                compatibility_guard_ref="goal-lane-compatibility-guard:g2",
            source_revision_ref=OLD,
            projector_ref="goal-compatibility-direction-projector:v1",
            projection_receipt_ref="goal-lane-projection:g2",
        )
