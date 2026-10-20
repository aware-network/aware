"""Real-Git provenance and complete-history canaries; no live Goal writes."""

from __future__ import annotations

import gc
import hashlib
import json
from dataclasses import replace
from copy import deepcopy
from pathlib import Path

import pytest
from aware_goal_operational_runtime import (
    GoalNativeLaneAuthorityV1,
    GoalLanePhase,
    GoalLanePhaseState,
    GoalNativeLaneIntroductionPublicationReceiptV1,
    GoalLanePhaseWork,
    GoalLanePhaseWorkDisposition,
    GoalLanePhaseWorkRole,
    GoalDependencyRelation,
    GoalPhaseDependency,
    GoalLanePhaseGateObservation,
    GoalLanePhaseGateOutcome,
    GoalPhaseNativeDocumentV2,
    GoalPhaseNativeDocumentV3,
    GoalPhaseNativeDocumentV4,
    GoalPhaseUnresolvedDependencyV1,
    GoalPhaseOperationJournalEntryV1,
    GoalPhaseOperationJournalV1,
    GoalPhaseCoordinate,
    GoalNativeLaneDirectionAuthorityV1,
    GoalLaneDirectionAuthorityV1,
    decode_goal_phase_eligibility_decision_v2,
    observe_goal_phase_eligibility_v2,
    require_qualified_goal_native_lane_direction,
    decode_goal_native_lane_direction_authority,
    attach_goal_phase_native_carrier as attach_goal_phase_native_document,
    extract_goal_phase_native_carrier as extract_goal_phase_native_document,
)
from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.phase_frontier import goal_phase_dependency_digest
from aware_goal_operational_runtime.phase_native_lane_authority import GoalNativeLaneDirectionEvidenceV1
from aware_goal_operational_runtime.phase_native_lane_hold import (
    GoalNativeLaneHoldDecisionV1, encode_goal_native_lane_hold_block,
)
from aware_goal_operational_runtime.phase_native_lane_evidence import (
    GoalNativeLaneEvidenceIssuerV2, decode_goal_native_lane_evidence_snapshot,
    require_qualified_native_lane_evidence,
)
from aware_goal_native_fs_adapter.native_lane_evidence import (
    GitNativeLaneEvidenceVerifier, _ISSUED as _SNAPSHOT_ISSUED,
)
from aware_goal_native_fs_adapter.native_lane_hold import (
    GitNativeLaneHoldAuthorityVerifier, GitNativeLaneHoldVerificationV1,
    decode_native_lane_hold_verification, require_verified_native_lane_hold,
    _ISSUED as _HOLD_ISSUED,
)
from aware_goal_native_fs_adapter.native_lane_authority import (
    GitNativeLaneDirectionEvidenceV1,
    GitNativeLaneVerificationV1,
    NativeGitLaneAuthorityVerifier,
    _VERIFIED,
    _DIRECTION_ISSUED,
    require_verified_git_native_lane,
)
from aware_goal_native_fs_adapter.compatibility_source import GoalNativeScopeSourceError
from aware_protocol_fs_adapter.native_goal_resolver import NativeGoalResolverError
from aware_goal_sdk.phase_operation import (
    GoalPhaseObserveEligibilityRequestV2, GoalPhaseOperationClient,
    GoalPhaseObserveEligibilityError, decode_goal_phase_observe_eligibility_request_v2,
    decode_goal_phase_observe_eligibility_result_v2,
    issue_goal_phase_operation_result_ref_v2,
)
from aware_goal_native_fs_adapter.phase_operation import NativeGitGoalPhaseOperationProvider

from test_native_provider import (
    CUSTOMER_PATH, CUSTOMER_ISSUE_PATH, CUSTOMER_ISSUE_TAG, GOAL,
    CUSTOMER_EXTERNAL_PATH, EXTERNAL_GOAL, _publish_external_source,
    _git, _native_capability, _publish_customer_issue, _publish_native_only_lane, _source,
)


FOUNDATION_WORK_PATH = "work/issues/2026/09/26/fb-2026-09-26-foundation-implementation.md"
FOUNDATION_WORK_TAG = "fb/2026-09-26/foundation-implementation"


def _change_restore_work_owner(root: Path, path: str) -> None:
    target = root / path
    original = target.read_bytes()
    target.write_bytes(original.replace(b"- Owner: codex-test", b"- Owner: codex-foreign"))
    _git(root, "add", path)
    _git(root, "commit", "-qm", "Foreign owner takes selected Work Issue")
    target.write_bytes(original)
    _git(root, "add", path)
    _git(root, "commit", "-qm", "Restore selected Work Issue byte-exactly")


def _publication(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, extra_path=False, foreign_owner=False, no_receipt=False, work=False, separate_work_issue=False, incident_direction=None, external=False, unresolved=False, external_goal_path=CUSTOMER_EXTERNAL_PATH, hold=None, hold_fault=None, runtime_checks=False, consumer_relation=None, journal=False, incident_operational=False):
    root, _ = _source(tmp_path, goal_path=CUSTOMER_PATH, v3=journal)
    _publish_native_only_lane(root)
    _publish_customer_issue(root)
    if external:
        _publish_external_source(root, goal_path=external_goal_path)
        compatibility, source = extract_goal_phase_native_document((root / external_goal_path).read_bytes())
        definition = source.definitions[0]
        phases = (GoalLanePhase(coordinate=definition.coordinate, ordinal=definition.ordinal,
            title=definition.title, intent=definition.intent, gate=definition.gate,
            state=GoalLanePhaseState.PLANNED),) if incident_operational else ()
        source = replace(source, operational_bundle=replace(source.operational_bundle, phases=phases))
        if journal and incident_operational:
            source = _append_journal_claim(source, definition.coordinate)
        if external_goal_path != CUSTOMER_EXTERNAL_PATH:
            # An independently templated date directory lets the external
            # parent change without also changing the dependent Goal's path.
            tag = "goal/2026-09-27/eligibility-external"
            compatibility = compatibility.replace(EXTERNAL_GOAL.encode(), tag.encode())
            source = replace(source, goal_tag=tag, definitions=tuple(
                replace(d, coordinate=replace(d.coordinate, goal_tag=tag)) for d in source.definitions
            ), compatibility_projection_sha256="sha256:" + hashlib.sha256(compatibility).hexdigest(),
                compatibility_projection_byte_count=len(compatibility))
        (root / external_goal_path).write_bytes(attach_goal_phase_native_document(compatibility, source))
        _git(root, "add", external_goal_path)
        _git(root, "commit", "-qm", "Retain external definition without operational evidence")
    if incident_direction is not None:
        compatibility, source = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
        foundation = next(d for d in source.definitions if d.coordinate.lane_key == "foundation")
        other = next(d for d in source.definitions if d.coordinate.phase_key == "later")
        if external:
            _, external_doc = extract_goal_phase_native_document((root / external_goal_path).read_bytes())
            other = external_doc.definitions[0]
        elif incident_operational:
            endpoint = GoalLanePhase(coordinate=other.coordinate, ordinal=other.ordinal,
                title=other.title, intent=other.intent, gate=other.gate,
                state=GoalLanePhaseState.PLANNED)
            source = replace(source, operational_bundle=replace(source.operational_bundle,
                phases=(*source.operational_bundle.phases, endpoint)))
        dependent, prerequisite = (foundation, other) if incident_direction == "incoming" else (other, foundation)
        edge = GoalPhaseDependency(
            owner_goal_tag=GOAL, dependency_key="qualified-edge-required",
            dependent=dependent.coordinate, prerequisite=prerequisite.coordinate,
            relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
            required_gate_digest=prerequisite.gate.gate_digest, reason="Authored edge",
        )
        source = replace(source, operational_bundle=replace(source.operational_bundle, dependencies=(edge,)))
        (root / CUSTOMER_PATH).write_bytes(attach_goal_phase_native_document(compatibility, source))
        _git(root, "add", CUSTOMER_PATH)
        _git(root, "commit", "-qm", "Authored dependency before lane introduction")
    if unresolved:
        compatibility, source = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
        foundation = next(d for d in source.definitions if d.coordinate.lane_key == "foundation")
        source = replace(source, unresolved_dependencies=(GoalPhaseUnresolvedDependencyV1(
            owner_goal_tag=GOAL, dependency_key="unresolved-foundation-edge",
            dependent=foundation.coordinate,
            prerequisite=GoalPhaseCoordinate("goal/2026-09-26/unavailable", "runtime", "later"),
            relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
            reason="Required Gate has not been resolved",
        ),))
        (root / CUSTOMER_PATH).write_bytes(attach_goal_phase_native_document(compatibility, source))
        _git(root, "add", CUSTOMER_PATH)
        _git(root, "commit", "-qm", "Preserve typed unresolved declaration")
    if work:
        if separate_work_issue:
            (root / FOUNDATION_WORK_PATH).write_text(
                (root / CUSTOMER_ISSUE_PATH).read_text().replace(CUSTOMER_ISSUE_TAG, FOUNDATION_WORK_TAG)
            )
            _git(root, "add", FOUNDATION_WORK_PATH)
            _git(root, "commit", "-qm", "Publish distinct implementation Work Issue")
        compatibility, before = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
        association = GoalLanePhaseWork(
            association_ref="goal-phase-work:foundation",
            issue_ref=FOUNDATION_WORK_TAG if separate_work_issue else CUSTOMER_ISSUE_TAG,
            role=GoalLanePhaseWorkRole.IMPLEMENTATION,
            disposition=GoalLanePhaseWorkDisposition.CURRENT,
            admitted_at="2026-09-26T12:00:00Z", receipt_ref="goal-phase-work-admission:foundation",
        )
        before = replace(before, operational_bundle=replace(before.operational_bundle,
            phases=tuple(replace(p, work_associations=(association,)) if p.coordinate.lane_key == "foundation" else p for p in before.operational_bundle.phases),
        ))
        (root / CUSTOMER_PATH).write_bytes(attach_goal_phase_native_document(compatibility, before))
        _git(root, "add", CUSTOMER_PATH)
        _git(root, "commit", "-qm", "Prior native Phase Work admission")
    if foreign_owner:
        path = root / CUSTOMER_ISSUE_PATH
        path.write_text(path.read_text().replace("codex-test", "codex-foreign"))
        _git(root, "add", CUSTOMER_ISSUE_PATH)
        _git(root, "commit", "-qm", "Foreign owner")
    if hold_fault == "unqualified_gate":
        compatibility, before = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
        phases = tuple(replace(p, gate_observations=(GoalLanePhaseGateObservation(
            observation_ref="gate-observation:unverified", gate_digest=p.gate.gate_digest,
            outcome=GoalLanePhaseGateOutcome.SATISFIED, evaluator_ref="evaluator:unverified",
            evidence_refs=("evidence:unverified",), source_revision_refs=(_git(root, "rev-parse", "HEAD"),),
            evaluated_at="2026-09-26T12:00:00Z", currentness_ref="currentness:unverified",
        ),)) if p.coordinate.lane_key == "foundation" else p for p in before.operational_bundle.phases)
        before = replace(before, operational_bundle=replace(before.operational_bundle, phases=phases))
        (root / CUSTOMER_PATH).write_bytes(attach_goal_phase_native_document(compatibility, before))
        _git(root, "add", CUSTOMER_PATH)
        _git(root, "commit", "-qm", "Preserve a supplied observation without an admitted evaluator")
    decision = None
    if hold is not None:
        issue_path = root / CUSTOMER_ISSUE_PATH
        issue_path.write_text(issue_path.read_text() + f"- `{CUSTOMER_ISSUE_PATH}`\n")
        _git(root, "add", CUSTOMER_ISSUE_PATH)
        _git(root, "commit", "-qm", "Admit Issue path for typed decision publication")
        source_revision = _git(root, "rev-parse", "HEAD")
        _, source_document = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
        decision = GoalNativeLaneHoldDecisionV1(
            goal_tag=GOAL, lane_key="foreign" if hold_fault == "foreign_lane" else "foundation",
            source_document_ref=source_document.document_ref,
            source_revision_ref=source_revision, owner_profile="provider_execution_v1",
            owner_ref="codex-test", target_state=hold, state_detail="Explicit steward hold",
            current_work_association_ref="goal-phase-work:foundation" if work else None,
            issued_at="2026-09-26T12:05:00Z", governing_issue_tag=CUSTOMER_ISSUE_TAG,
        )
        work_path = FOUNDATION_WORK_PATH if separate_work_issue else CUSTOMER_ISSUE_PATH
        if hold_fault == "work_change_restore_before_decision":
            _change_restore_work_owner(root, work_path)
        evidence = "Unissued hold reference" if hold_fault == "token_only" else encode_goal_native_lane_hold_block(decision)
        issue_path.write_text(issue_path.read_text() + "\n## Hold decision evidence\n\n" + evidence + "\n")
        _git(root, "add", CUSTOMER_ISSUE_PATH)
        message = "Publish typed Goal-owner hold decision"
        if hold_fault != "no_decision_receipt":
            message += (
                f"\n\nIssue-Tag: {CUSTOMER_ISSUE_TAG}\nIssue-Path: {CUSTOMER_ISSUE_PATH}"
                f"\nOwner: {'codex-foreign' if hold_fault == 'foreign_issuer' else 'codex-test'}\nOwned-Paths: {CUSTOMER_ISSUE_PATH}"
            )
        if hold_fault == "extra_decision_path":
            (root / "extra-decision.txt").write_text("Not a one-Issue decision effect")
            _git(root, "add", "extra-decision.txt")
        _git(root, "commit", "-qm", message)
        if hold_fault == "work_change_restore_after_decision":
            _change_restore_work_owner(root, work_path)
        if hold_fault == "inherited_decision":
            issue_path.write_text(issue_path.read_text() + "\nInherited decision in a later Issue update\n")
            _git(root, "add", CUSTOMER_ISSUE_PATH)
            _git(root, "commit", "-qm", message)
        if hold_fault == "source_change_restore":
            original = (root / CUSTOMER_PATH).read_bytes()
            (root / CUSTOMER_PATH).write_bytes(original + b"\nUnknown source delta\n")
            _git(root, "add", CUSTOMER_PATH)
            _git(root, "commit", "-qm", "Touch the protected source")
            (root / CUSTOMER_PATH).write_bytes(original)
            _git(root, "add", CUSTOMER_PATH)
            _git(root, "commit", "-qm", "Restore byte-identical source")
    if runtime_checks:
        from aware_goal_operational_runtime import GoalLanePhaseGate
        from aware_goal_operational_runtime.phase_runtime_checks_review import GATE_CONTRACT, EVIDENCE_SCHEMA, INVARIANTS
        compatibility, source = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
        definition = next(d for d in source.definitions if d.coordinate.lane_key == "foundation")
        gate = GoalLanePhaseGate(gate_key="runtime-checks", promise="Exact opt-in runtime checks.",
            gate_contract_ref=GATE_CONTRACT, evidence_schema_ref=EVIDENCE_SCHEMA, invariant_refs=INVARIANTS)
        source = replace(source, definitions=tuple(replace(d, gate=gate) if d.coordinate == definition.coordinate else d for d in source.definitions),
            operational_bundle=replace(source.operational_bundle, phases=tuple(replace(p, gate=gate) if p.coordinate == definition.coordinate else p for p in source.operational_bundle.phases)))
        if consumer_relation is not None:
            definition = next(d for d in source.definitions if d.coordinate.lane_key == "foundation")
            consumer = replace(definition, coordinate=replace(definition.coordinate, phase_key="consumer"), ordinal=2)
            phase = next(p for p in source.operational_bundle.phases if p.coordinate == definition.coordinate)
            edge = GoalPhaseDependency(owner_goal_tag=GOAL, dependency_key="consumer-needs-foundation",
                dependent=consumer.coordinate, prerequisite=definition.coordinate,
                relation=consumer_relation, required_gate_digest=gate.gate_digest, reason="Exact qualified Gate dependency")
            source = replace(source, definitions=(*source.definitions, consumer),
                operational_bundle=replace(source.operational_bundle,
                    phases=(*source.operational_bundle.phases, replace(phase, coordinate=consumer.coordinate,
                        ordinal=2, state=GoalLanePhaseState.PLANNED, work_associations=())),
                    dependencies=(*source.operational_bundle.dependencies, edge)))
        (root / CUSTOMER_PATH).write_bytes(attach_goal_phase_native_document(compatibility, source))
        scope = ["runtime/a.py", "runtime/b.py", FOUNDATION_WORK_PATH, "proof/checks.json",
            "proof/tests.txt", "proof/canary.txt", "proof/static.txt"]
        (root / FOUNDATION_WORK_PATH).write_text(
            f"# Proof authority\n\n- Tag: {FOUNDATION_WORK_TAG}\n- Owner: codex-test\n- Status: In Progress\n\n## Ownership Scope\n"
            + "".join(f"- `{p}`\n" for p in scope) + "\n## Updates\n")
        _git(root, "add", CUSTOMER_PATH, FOUNDATION_WORK_PATH)
        _git(root, "commit", "-qm", "Qualify Gate and exact Work scope before introduction")
    parent = _git(root, "rev-parse", "HEAD")
    before_bytes = (root / CUSTOMER_PATH).read_bytes()
    compatibility, before = extract_goal_phase_native_document(before_bytes)
    lane = GoalNativeLaneAuthorityV1(
        goal_tag=GOAL, lane_key="foundation", role="Foundation",
        owner_profile="provider_execution_v1", owner_ref="codex-test",
        operational_state="active" if decision is None else decision.target_state,
        state_detail=None if decision is None else decision.state_detail,
        hold_authority_refs=() if decision is None else (decision.decision_ref,),
        current_work_association_ref="goal-phase-work:foundation" if work else None,
    )
    after = GoalPhaseNativeDocumentV4(
        goal_tag=before.goal_tag,
        compatibility_projection_sha256=before.compatibility_projection_sha256,
        compatibility_projection_byte_count=before.compatibility_projection_byte_count,
        definitions=before.definitions, operational_bundle=before.operational_bundle,
        unresolved_dependencies=before.unresolved_dependencies, source_refs=before.source_refs,
        execution_authority=before.execution_authority,
        native_lane_authorities=(lane,), operation_journal_profile="v1" if journal else "none",
        phase_operation_journal=before.phase_operation_journal if journal else None,
    )
    after_bytes = attach_goal_phase_native_document(compatibility, after)
    (root / CUSTOMER_PATH).write_bytes(after_bytes)
    _git(root, "add", CUSTOMER_PATH)
    if extra_path:
        (root / "extra.txt").write_text("out of scope")
        _git(root, "add", "extra.txt")
    message = "Introduce native lane"
    if not no_receipt:
        message += (
            f"\n\nIssue-Tag: {CUSTOMER_ISSUE_TAG}\nIssue-Path: {CUSTOMER_ISSUE_PATH}"
            f"\nOwner: {'codex-foreign' if foreign_owner else 'codex-test'}\nOwned-Paths: {CUSTOMER_PATH}"
        )
    _git(root, "commit", "-qm", message)
    commit = _git(root, "rev-parse", "HEAD")
    receipt = GoalNativeLaneIntroductionPublicationReceiptV1(
        goal_tag=GOAL, lane_key="foundation", lane_authority_ref=lane.lane_authority_ref,
        goal_path=CUSTOMER_PATH, before_document_ref=before.document_ref,
        after_document_ref=after.document_ref,
        before_goal_sha256="sha256:" + hashlib.sha256(before_bytes).hexdigest(),
        after_goal_sha256="sha256:" + hashlib.sha256(after_bytes).hexdigest(),
        before_goal_blob_oid=_git(root, "rev-parse", f"{parent}:{CUSTOMER_PATH}"),
        after_goal_blob_oid=_git(root, "rev-parse", f"{commit}:{CUSTOMER_PATH}"),
        repository_parent_ref=parent, repository_commit_ref=commit,
        repository_commit_receipt_ref="repository-commit:" + commit,
        publication_issue_path=CUSTOMER_ISSUE_PATH,
        publication_issue_blob_oid=_git(root, "rev-parse", f"{parent}:{CUSTOMER_ISSUE_PATH}"),
        publication_issue_owner_execution_id="codex-foreign" if foreign_owner else "codex-test",
        publication_issue_status="in_progress",
        publication_issue_scope_digest=fingerprint({"ownership_scope": [CUSTOMER_PATH] + ([] if decision is None else [CUSTOMER_ISSUE_PATH])}),
    )
    capability = _native_capability(root, monkeypatch)
    return root, receipt, NativeGitLaneAuthorityVerifier(resolver_capability=capability)


def _publish_goal(root: Path, document=None, compatibility=None):
    old_compatibility, old_document = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
    compatibility = old_compatibility if compatibility is None else compatibility
    document = old_document if document is None else document
    document = replace(document,
        compatibility_projection_sha256="sha256:" + hashlib.sha256(compatibility).hexdigest(),
        compatibility_projection_byte_count=len(compatibility),
    )
    (root / CUSTOMER_PATH).write_bytes(attach_goal_phase_native_document(compatibility, document))
    _git(root, "add", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Advance Goal")


def test_authenticate_current_customer_root_publication(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch)
    result = require_verified_git_native_lane(verifier.verify(receipt))
    assert (result.status, result.projection_currentness, result.replay_disposition) == ("current", "exact", "exact")
    assert result.observed_head == _git(root, "rev-parse", "HEAD")
    assert result.origin_closure_ref == result.current_closure_ref
    assert result.protected_paths == (CUSTOMER_PATH,)


def _eligibility_inputs(qualified):
    phase = next(p for p in qualified.document.operational_bundle.phases
        if p.coordinate.lane_key == qualified.lane_key)
    return dict(document=qualified.document, coordinate=phase.coordinate,
        expected_gate_digest=phase.gate.gate_digest, global_authority=qualified.global_authority,
        lane_authority=qualified, source_revision_ref=qualified.global_authority.source_revision_ref)


def _operation_request_v2(root, receipt, *, claims=None, phase_key="native-first"):
    locator = root / "proof/lane-publication.json"
    locator.parent.mkdir(exist_ok=True)
    locator.write_text(json.dumps(receipt.to_wire()))
    files = ["proof/lane-publication.json"]
    gate_locator = None
    if claims is not None:
        gate_locator = "repository-path:proof/gate-publications.json"
        (root / "proof/gate-publications.json").write_text(json.dumps({k: v.to_wire() for k, v in claims.items()}))
        files.append("proof/gate-publications.json")
    _git(root, "add", *files)
    _git(root, "commit", "-qm", "Retain untrusted publication locator claims")
    _, document = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
    definition = next(d for d in document.definitions if d.coordinate.lane_key == "foundation"
        and d.coordinate.phase_key == phase_key)
    return GoalPhaseObserveEligibilityRequestV2(
        source_locator_ref="repository-path:" + CUSTOMER_PATH,
        goal_tag=document.goal_tag, lane_key="foundation", phase_key=phase_key,
        expected_goal_sha256="sha256:" + hashlib.sha256((root / CUSTOMER_PATH).read_bytes()).hexdigest(),
        expected_native_document_ref=document.document_ref, expected_gate_digest=definition.gate.gate_digest,
        lane_authority_locator_ref="repository-path:proof/lane-publication.json",
        gate_authority_locator_ref=gate_locator,
    )


@pytest.mark.parametrize("mode", ["absence", "work", "incoming", "external", "unresolved", "held", "blocked"])
def test_portable_v2_operation_matches_qualified_neutral_decision_without_effect(tmp_path, monkeypatch, mode):
    kwargs = {"work": mode == "work"}
    if mode in {"incoming", "external"}:
        kwargs.update(incident_direction="incoming", external=mode == "external")
    if mode == "unresolved":
        kwargs["unresolved"] = True
    if mode in {"held", "blocked"}:
        kwargs["hold"] = mode
    root, receipt, verifier = _publication(tmp_path, monkeypatch, **kwargs)
    request = _operation_request_v2(root, receipt)
    assert decode_goal_phase_observe_eligibility_request_v2(request.to_wire()) == request
    before = (_git(root, "rev-parse", "HEAD"), _git(root, "write-tree"),
        _git(root, "status", "--porcelain"), (root / CUSTOMER_PATH).read_bytes())
    provider = NativeGitGoalPhaseOperationProvider(_native_capability(root, monkeypatch))
    result = GoalPhaseOperationClient(provider).observe_eligibility_v2(request)
    expected = observe_goal_phase_eligibility_v2(**_eligibility_inputs(verifier.qualify_direction(receipt))).to_wire()
    assert result["decision"] == expected
    assert result["source_revision_ref"] == before[0]
    assert result["event_effect"] == result["dispatch_effect"] == "none"
    assert decode_goal_phase_observe_eligibility_result_v2(result, request=request) == result
    assert (_git(root, "rev-parse", "HEAD"), _git(root, "write-tree"),
        _git(root, "status", "--porcelain"), (root / CUSTOMER_PATH).read_bytes()) == before


@pytest.mark.parametrize("fault", ["unknown_profile_running", "eligible_stale"])
def test_redigested_fake_provider_cannot_contradict_genuine_v2_decision(tmp_path, monkeypatch, fault):
    root, receipt, _ = _publication(tmp_path, monkeypatch)
    request = _operation_request_v2(root, receipt)
    provider = NativeGitGoalPhaseOperationProvider(_native_capability(root, monkeypatch))
    genuine = GoalPhaseOperationClient(provider).observe_eligibility_v2(request)
    forged = deepcopy(genuine)
    decision = forged["decision"]
    if fault == "unknown_profile_running":
        decision.update(lane_authority_profile="unknown", eligibility="running")
    else:
        decision["dependency_gate"].update(
            state="stale", incoming_count=1, dependency_keys=["stale-input"], stale=["stale-input"])
        decision["observation_coverage"] = "complete"
        assert decision["eligibility"] == "eligible"
    decision["decision_ref"] = "goal-phase-eligibility-decision:" + fingerprint(
        {key: value for key, value in decision.items() if key != "decision_ref"})
    forged["result_ref"] = issue_goal_phase_operation_result_ref_v2(
        {key: value for key, value in forged.items() if key != "result_ref"})

    class FakeProvider:
        def observe_eligibility_v2(self, request):
            return forged

    before = (_git(root, "rev-parse", "HEAD"), _git(root, "write-tree"),
        _git(root, "status", "--porcelain"), (root / CUSTOMER_PATH).read_bytes())
    with pytest.raises(GoalPhaseObserveEligibilityError):
        GoalPhaseOperationClient(FakeProvider()).observe_eligibility_v2(request)
    assert GoalPhaseOperationClient(provider).observe_eligibility_v2(request) == genuine
    assert (_git(root, "rev-parse", "HEAD"), _git(root, "write-tree"),
        _git(root, "status", "--porcelain"), (root / CUSTOMER_PATH).read_bytes()) == before


@pytest.mark.parametrize("fault", ["foreign", "redigested", "missing", "uncommitted", "symlink", "parent_symlink", "duplicate_json"])
def test_portable_v2_operation_cannot_seal_locator_claims_as_authority(tmp_path, monkeypatch, fault):
    root, receipt, _ = _publication(tmp_path, monkeypatch)
    request = _operation_request_v2(root, receipt)
    locator = root / "proof/lane-publication.json"
    if fault == "foreign":
        request = replace(request, lane_key="runtime", phase_key="first")
    elif fault == "missing":
        request = replace(request, lane_authority_locator_ref="repository-path:proof/missing.json")
    elif fault == "uncommitted":
        (root / "proof/new.json").write_text(locator.read_text())
        request = replace(request, lane_authority_locator_ref="repository-path:proof/new.json")
    elif fault in {"symlink", "parent_symlink"}:
        external = tmp_path / "external"
        external.mkdir()
        (external / locator.name).write_text(locator.read_text())
        if fault == "symlink":
            locator.unlink()
            locator.symlink_to(external / locator.name)
        else:
            (root / "proof").rename(root / "retained-proof")
            (root / "proof").symlink_to(external, target_is_directory=True)
    else:
        if fault == "redigested":
            forged = replace(receipt, publication_issue_owner_execution_id="codex-foreign")
            locator.write_text(json.dumps(forged.to_wire()))
        else:
            text = locator.read_text()
            locator.write_text(text[:-1] + ',"goal_tag":"' + receipt.goal_tag + '"}')
        _git(root, "add", "proof/lane-publication.json")
        _git(root, "commit", "-qm", "Commit fabricated locator, not publication authority")
    before = _git(root, "rev-parse", "HEAD")
    with pytest.raises(GoalPhaseObserveEligibilityError):
        GoalPhaseOperationClient(NativeGitGoalPhaseOperationProvider(_native_capability(root, monkeypatch))).observe_eligibility_v2(request)
    assert _git(root, "rev-parse", "HEAD") == before


def test_portable_v2_operation_reobserves_fresh_epoch_and_refuses_lane_restore(tmp_path, monkeypatch):
    root, receipt, _ = _publication(tmp_path, monkeypatch)
    request = _operation_request_v2(root, receipt)
    client = GoalPhaseOperationClient(NativeGitGoalPhaseOperationProvider(_native_capability(root, monkeypatch)))
    previous = client.observe_eligibility_v2(request)
    (root / "unrelated.txt").write_text("Unrelated epoch\n")
    _git(root, "add", "unrelated.txt")
    _git(root, "commit", "-qm", "Advance unrelated source")
    current = client.observe_eligibility_v2(request)
    assert current["source_revision_ref"] != previous["source_revision_ref"]
    assert current["decision"]["eligibility"] == "eligible"
    assert current["decision"]["scope_currentness_ref"] != previous["decision"]["scope_currentness_ref"]
    _, original = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
    _publish_goal(root, replace(original, native_lane_authorities=(replace(original.native_lane_authorities[0], owner_ref="codex-foreign"),)))
    _publish_goal(root, original)
    with pytest.raises(GoalPhaseObserveEligibilityError, match="native_lane_scope_not_current"):
        client.observe_eligibility_v2(request)


def test_portable_v2_operation_terminal_locator_io_precedes_final_head(tmp_path, monkeypatch):
    root, receipt, _ = _publication(tmp_path, monkeypatch)
    request = _operation_request_v2(root, receipt)
    provider = NativeGitGoalPhaseOperationProvider(_native_capability(root, monkeypatch))
    resolve = provider._resolve_authority_target
    calls = 0
    def interleave(path):
        nonlocal calls
        resolve(path)
        calls += 1
        if calls == 2:
            (root / "concurrent.txt").write_text("Advance during terminal resolution\n")
            _git(root, "add", "concurrent.txt")
            _git(root, "commit", "-qm", "Concurrent terminal source advance")
    monkeypatch.setattr(provider, "_resolve_authority_target", interleave)
    with pytest.raises(GoalPhaseObserveEligibilityError, match="repository_head_advanced"):
        GoalPhaseOperationClient(provider).observe_eligibility_v2(request)


@pytest.mark.parametrize("target", ["locator", "goal", "work", "external"])
def test_portable_v2_operation_terminal_replacement_refuses_after_qualification(tmp_path, monkeypatch, target):
    kwargs = {"work": target == "work", "separate_work_issue": target == "work"}
    if target == "external":
        kwargs.update(incident_direction="incoming", external=True)
    root, receipt, _ = _publication(tmp_path, monkeypatch, **kwargs)
    request = _operation_request_v2(root, receipt)
    path = {"locator": "proof/lane-publication.json", "goal": CUSTOMER_PATH,
        "work": FOUNDATION_WORK_PATH, "external": CUSTOMER_EXTERNAL_PATH}[target]
    original = NativeGitLaneAuthorityVerifier.qualify_direction
    def replace_after(self, receipt):
        value = original(self, receipt)
        file = root / path
        outside = tmp_path / "outside-target"
        outside.write_bytes(file.read_bytes())
        file.unlink()
        file.symlink_to(outside)
        return value
    monkeypatch.setattr(NativeGitLaneAuthorityVerifier, "qualify_direction", replace_after)
    with pytest.raises(GoalPhaseObserveEligibilityError):
        GoalPhaseOperationClient(NativeGitGoalPhaseOperationProvider(_native_capability(root, monkeypatch))).observe_eligibility_v2(request)


@pytest.mark.parametrize("work", [False, True])
def test_qualified_native_direction_enters_one_neutral_v2_decision(tmp_path, monkeypatch, work):
    root, receipt, verifier = _publication(tmp_path, monkeypatch, work=work)
    qualified = require_qualified_goal_native_lane_direction(verifier.qualify_direction(receipt))
    args = _eligibility_inputs(qualified)
    result = observe_goal_phase_eligibility_v2(**args)
    assert result.decision.eligibility == "eligible"
    assert result.lane_authority_profile == "native_carrier_v1"
    assert result.decision.lane_authority_ref == qualified.authority_ref
    assert result.source_revision_ref == _git(root, "rev-parse", "HEAD")
    assert result.scope_currentness_ref.startswith("goal-git-native-lane-verification:sha256:")
    assert "compatibility_guard_ref" not in qualified.to_wire()
    assert decode_goal_native_lane_direction_authority(qualified.to_wire(), qualified=qualified) is qualified
    assert result.to_wire()["effect_profile"] == "read_only_non_authorizing"
    assert decode_goal_phase_eligibility_decision_v2(result.to_wire(), **args) == result


@pytest.mark.parametrize("external", [False, True])
def test_native_v2_missing_dependency_evidence_stays_not_evaluated(tmp_path, monkeypatch, external):
    _, receipt, verifier = _publication(tmp_path, monkeypatch, incident_direction="incoming", external=external)
    qualified = verifier.qualify_direction(receipt)
    result = observe_goal_phase_eligibility_v2(**_eligibility_inputs(qualified))
    assert result.decision.eligibility == "held"
    assert result.decision.dependency_gate.not_evaluated_keys == ("qualified-edge-required",)
    assert result.decision.observation_coverage == "none"
    assert result.decision.reasons == ("frontier_ineligible",)


def test_native_v2_unresolved_dependency_stays_explicit(tmp_path, monkeypatch):
    _, receipt, verifier = _publication(tmp_path, monkeypatch, unresolved=True)
    result = observe_goal_phase_eligibility_v2(**_eligibility_inputs(verifier.qualify_direction(receipt)))
    assert result.decision.eligibility == "held"
    assert result.decision.unresolved_dependency_keys == ("unresolved-foundation-edge",)
    assert "unresolved_incoming_dependency" in result.decision.reasons


@pytest.mark.parametrize("mutation", ["clone", "new", "global", "document", "issue", "source"])
def test_qualified_native_direction_refuses_forged_or_mutated_inputs(tmp_path, monkeypatch, mutation):
    _, receipt, verifier = _publication(tmp_path, monkeypatch, work=True)
    qualified = verifier.qualify_direction(receipt)
    args = _eligibility_inputs(qualified)
    if mutation == "clone":
        args["lane_authority"] = replace(qualified)
    elif mutation == "new":
        args["lane_authority"] = object.__new__(GoalNativeLaneDirectionAuthorityV1)
    elif mutation == "global":
        object.__setattr__(qualified.global_authority, "lifecycle_status", "completed")
    elif mutation == "document":
        object.__setattr__(qualified.document, "source_refs", ("forged:replacement",))
    elif mutation == "issue":
        qualified.issue_authorities[CUSTOMER_ISSUE_TAG]["status"] = "closed"
    else:
        object.__setattr__(qualified, "source_blob_ref", "object-source:substitution")
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        observe_goal_phase_eligibility_v2(**args)


def test_native_v2_refuses_separately_substituted_document_or_goal_authority(tmp_path, monkeypatch):
    _, receipt, verifier = _publication(tmp_path, monkeypatch)
    qualified = verifier.qualify_direction(receipt)
    args = _eligibility_inputs(qualified)
    for substitutions in (
        {"document": replace(qualified.document, source_refs=("caller:substitution",))},
        {"global_authority": replace(qualified.global_authority, lifecycle_status="completed")},
        {"prerequisite_sources": {}},
    ):
        with pytest.raises(ValueError, match="source_mismatch|must_not_be_substituted"):
            observe_goal_phase_eligibility_v2(**{**args, **substitutions})


def test_echo_verifier_and_copied_issuance_witness_cannot_qualify(tmp_path, monkeypatch):
    class EchoEvidence(GoalNativeLaneDirectionEvidenceV1):
        def require_direction(self, value):
            return None
    _, receipt, verifier = _publication(tmp_path, monkeypatch)
    valid = verifier.qualify_direction(receipt)
    for evidence in (EchoEvidence(), replace(valid.source_evidence), GitNativeLaneDirectionEvidenceV1(valid.scope_currentness_ref)):
        forged = replace(valid, source_evidence=evidence)
        with pytest.raises(ValueError, match="unissued_or_mutated"):
            observe_goal_phase_eligibility_v2(**_eligibility_inputs(forged))


@pytest.mark.parametrize("mutation", ["source", "issue", "unknown"])
def test_native_direction_wire_cannot_self_authorize_redigested_substitution(tmp_path, monkeypatch, mutation):
    _, receipt, verifier = _publication(tmp_path, monkeypatch, work=True)
    qualified = verifier.qualify_direction(receipt)
    wire = qualified.to_wire()
    if mutation == "source":
        wire["source_blob_ref"] = "object-source:another"
    elif mutation == "issue":
        wire["current_issue_authorities"][0]["owner"] = "codex-foreign"
    else:
        wire["ignored_field"] = True
    wire.pop("authority_ref")
    wire["authority_ref"] = "goal-native-lane-direction:" + fingerprint(wire)
    with pytest.raises(ValueError, match="wire_differs_from_authority"):
        decode_goal_native_lane_direction_authority(wire, qualified=qualified)
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        decode_goal_native_lane_direction_authority(wire, qualified=replace(qualified))


def test_complete_nested_prerequisite_semantics_are_bound_by_provider(tmp_path, monkeypatch):
    _, receipt, verifier = _publication(tmp_path, monkeypatch, incident_direction="incoming", external=True)
    valid = verifier.qualify_direction(receipt)
    source = valid.dependency_sources[EXTERNAL_GOAL]
    # Preserve the old source/doc references while changing nested semantics.
    object.__setattr__(source.document.definitions[0].gate, "promise", "Forged prerequisite")
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        observe_goal_phase_eligibility_v2(**_eligibility_inputs(valid))


@pytest.mark.parametrize("mutation", ["eligibility", "scope", "boolean", "unknown", "profile"])
def test_native_v2_decoder_recomputes_even_redigested_transport(tmp_path, monkeypatch, mutation):
    _, receipt, verifier = _publication(tmp_path, monkeypatch)
    args = _eligibility_inputs(verifier.qualify_direction(receipt))
    wire = deepcopy(observe_goal_phase_eligibility_v2(**args).to_wire())
    if mutation == "eligibility":
        wire["eligibility"] = "held"
    elif mutation == "scope":
        wire["scope_currentness_ref"] = "currentness:caller-authored"
    elif mutation == "boolean":
        wire["dependency_gate"]["incoming_count"] = False
    elif mutation == "unknown":
        wire["future_authority"] = "ignored?"
    else:
        wire["lane_authority_profile"] = "markdown_compat_v1"
    wire.pop("decision_ref")
    wire["decision_ref"] = "goal-phase-eligibility-decision:" + fingerprint(wire)
    with pytest.raises(ValueError, match="differs from qualified authority"):
        decode_goal_phase_eligibility_decision_v2(wire, **args)


def test_native_v2_cannot_fabricate_markdown_provenance(tmp_path, monkeypatch):
    _, receipt, verifier = _publication(tmp_path, monkeypatch)
    qualified = verifier.qualify_direction(receipt)
    fake = GoalLaneDirectionAuthorityV1(
        goal_tag=qualified.document.goal_tag, lane_key=qualified.lane_key,
        role="Foundation", owner_ref="codex-test", operational_state="active",
        state_detail=None, blocker_authority_refs=(), current_issue_ref=None,
        current_issue_authority_ref=None, compatibility_guard_ref="fabricated:guard",
        source_revision_ref=qualified.global_authority.source_revision_ref,
        projector_ref="fabricated:projector", projection_receipt_ref="fabricated:receipt",
    )
    with pytest.raises(ValueError, match="requires_native_provenance"):
        observe_goal_phase_eligibility_v2(**{**_eligibility_inputs(qualified), "lane_authority": fake})


def test_native_direction_qualification_refuses_changed_and_restored_scope(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch)
    _, document = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
    _publish_goal(root, replace(document, native_lane_authorities=(replace(document.native_lane_authorities[0], role="Changed"),)))
    _publish_goal(root, document)
    with pytest.raises(ValueError, match="scope_not_current"):
        verifier.qualify_direction(receipt)


def test_native_v2_reobserves_unrelated_lane_advance_without_rebinding_old_proof(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch)
    original = verifier.qualify_direction(receipt)
    _, document = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
    definitions = tuple(replace(d, title="Unrelated future definition") if d.coordinate.phase_key == "later" else d
        for d in document.definitions)
    _publish_goal(root, replace(document, definitions=definitions))
    advanced = verifier.qualify_direction(receipt)
    assert original.semantic_closure_ref == advanced.semantic_closure_ref
    assert original.document.document_ref != advanced.document.document_ref
    decision = observe_goal_phase_eligibility_v2(**_eligibility_inputs(advanced))
    assert decision.decision.eligibility == "eligible"
    assert decision.source_revision_ref == _git(root, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match="authority_source_mismatch"):
        observe_goal_phase_eligibility_v2(**{**_eligibility_inputs(original), "source_revision_ref": decision.source_revision_ref})


def test_native_direction_registry_follows_output_lifetime(tmp_path, monkeypatch):
    _, receipt, verifier = _publication(tmp_path, monkeypatch)
    gc.collect()
    count = len(_DIRECTION_ISSUED)
    qualified = verifier.qualify_direction(receipt)
    assert len(_DIRECTION_ISSUED) == count + 1
    del qualified
    gc.collect()
    assert len(_DIRECTION_ISSUED) == count


def test_head_advance_after_provenance_before_direction_handoff_refuses(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch)
    read = verifier._snapshot
    calls = 0
    count = len(_DIRECTION_ISSUED)
    def interleave(revision, path):
        nonlocal calls
        result = read(revision, path)
        calls += 1
        # verify reads before, after, current and current closure. The next
        # snapshot is the joined direction handoff, after verification issuance.
        if calls == 6:
            _, document = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
            _publish_goal(root, replace(document, native_lane_authorities=(replace(document.native_lane_authorities[0], role="Concurrent"),)))
        return result
    monkeypatch.setattr(verifier, "_snapshot", interleave)
    with pytest.raises(ValueError, match="repository_head_advanced"):
        verifier.qualify_direction(receipt)
    assert calls >= 6
    assert len(_DIRECTION_ISSUED) == count


@pytest.mark.parametrize("kw, reason", [
    ({"foreign_owner": True}, "goal_owner_issue_mismatch"),
    ({"no_receipt": True}, "issue_receipt_absent"),
    ({"extra_path": True}, "not_one_goal_path"),
])
def test_refuse_unauthorized_publication(tmp_path, monkeypatch, kw, reason):
    _, receipt, verifier = _publication(tmp_path, monkeypatch, **kw)
    with pytest.raises(ValueError, match=reason):
        verifier.verify(receipt)


@pytest.mark.parametrize("field, value", [
    ("before_goal_sha256", "sha256:" + "0" * 64),
    ("publication_issue_blob_oid", "0" * 40),
    ("publication_issue_scope_digest", "sha256:" + "0" * 64),
    ("lane_authority_ref", "goal-native-lane-authority:sha256:" + "0" * 64),
])
def test_redigested_false_receipt_refuses(tmp_path, monkeypatch, field, value):
    _, receipt, verifier = _publication(tmp_path, monkeypatch)
    with pytest.raises(ValueError):
        verifier.verify(replace(receipt, **{field: value}))


def test_relabel_inherited_blob_as_publication_refuses(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch)
    (root / "note.txt").write_text("unrelated")
    _git(root, "add", "note.txt")
    _git(root, "commit", "-qm", "Unrelated")
    head = _git(root, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match="not_one_goal_path"):
        verifier.verify(replace(receipt,
            repository_parent_ref=receipt.repository_commit_ref,
            repository_commit_ref=head, repository_commit_receipt_ref="repository-commit:" + head,
        ))


def test_unrelated_lane_change_preserves_native_scope(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch)
    compatibility, document = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
    definitions = tuple(
        replace(d, title="Other lane changed") if d.coordinate.lane_key == "runtime" else d
        for d in document.definitions
    )
    # Only definition-only runtime Phase changes, not its existing operational Phase.
    definitions = tuple(
        replace(d, title="Later changed") if d.coordinate.phase_key == "later" else old
        for d, old in zip(definitions, document.definitions, strict=True)
    )
    _publish_goal(root, replace(document, definitions=definitions), compatibility)
    result = verifier.verify(receipt)
    assert (result.status, result.replay_disposition) == ("current", "reobserved_unchanged")
    assert len(result.history_edges) == 1


def test_changed_and_restored_lane_is_stale(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch)
    _, original = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
    changed = replace(original, native_lane_authorities=(replace(original.native_lane_authorities[0], role="Changed"),))
    _publish_goal(root, changed)
    _publish_goal(root, original)
    result = verifier.verify(receipt)
    assert result.origin_closure_ref == result.current_closure_ref
    assert (result.status, result.replay_disposition) == ("stale", "admitted_delta_required")
    assert len(result.history_edges) == 2


def _append_journal_claim(document, coordinate, *, decision="approve"):
    # Structural fixture only, never a trusted action or policy issuer.
    definition = next(d for d in document.definitions if d.coordinate == coordinate)
    prior_journal = getattr(document, "phase_operation_journal", None)
    entries = () if prior_journal is None else prior_journal.entries
    approval = next((entry.entry_ref for entry in reversed(entries)
        if entry.coordinate == coordinate and entry.decision == "approve"), None)
    marker = str(len(entries) + 2) * 64
    entry = GoalPhaseOperationJournalEntryV1(
        operation_kind="approve_pursuit", decision=decision, coordinate=coordinate,
        gate_digest=definition.gate.gate_digest, source_preimage_ref=document.document_ref,
        actor_ref="identity:structural-fixture", action_occurrence_ref="actor-action-occurrence:sha256:" + marker,
        policy_ref="goal-phase-approval-policy:sha256:" + "2" * 64,
        policy_digest="sha256:" + "3" * 64, idempotency_key=f"claim-{len(entries)}",
        delta_ref="goal-phase-delta:sha256:" + marker, event_ref="goal-phase-event:sha256:" + marker,
        approval_entry_ref=approval if decision == "revoke" else None,
    )
    journal = GoalPhaseOperationJournalV1((*entries, entry))
    if type(document) is GoalPhaseNativeDocumentV4:
        return replace(document, operation_journal_profile="v1", phase_operation_journal=journal)
    if type(document) is GoalPhaseNativeDocumentV3:
        return replace(document, phase_operation_journal=journal)
    assert type(document) is GoalPhaseNativeDocumentV2
    return GoalPhaseNativeDocumentV3(
        goal_tag=document.goal_tag,
        compatibility_projection_sha256=document.compatibility_projection_sha256,
        compatibility_projection_byte_count=document.compatibility_projection_byte_count,
        definitions=document.definitions, operational_bundle=document.operational_bundle,
        unresolved_dependencies=document.unresolved_dependencies, source_refs=document.source_refs,
        execution_authority=document.execution_authority, phase_operation_journal=journal,
    )


@pytest.mark.parametrize("target", ["same_lane", "incident_endpoint", "unrelated"])
@pytest.mark.parametrize("decision", ["approve", "revoke", "restore"])
def test_native_lane_currentness_binds_scoped_journal_history(tmp_path, monkeypatch, target, decision):
    root, receipt, verifier = _publication(tmp_path, monkeypatch,
        incident_direction="incoming", journal=True, incident_operational=True)
    original_bytes = (root / CUSTOMER_PATH).read_bytes()
    _, original = extract_goal_phase_native_document(original_bytes)
    coordinate = next(d.coordinate for d in original.definitions if (
        d.coordinate.lane_key == "foundation" if target == "same_lane"
        else d.coordinate.phase_key == ("later" if target == "incident_endpoint" else "first")
    ))
    # The initial journal approves runtime/first. Revoke it for the unrelated
    # control, preserving the profile and all incident authority exactly.
    if target == "unrelated":
        changed = _append_journal_claim(original, coordinate, decision="revoke")
    else:
        changed = _append_journal_claim(original, coordinate)
    _publish_goal(root, changed)
    if decision == "revoke" and target != "unrelated":
        _publish_goal(root, _append_journal_claim(changed, coordinate, decision="revoke"))
    elif decision == "restore":
        _publish_goal(root, original)
        assert (root / CUSTOMER_PATH).read_bytes() == original_bytes
    before = (_git(root, "rev-parse", "HEAD"), _git(root, "write-tree"), _git(root, "status", "--porcelain"))
    verified = verifier.verify(receipt)
    assert (verified.status, verified.replay_disposition) == (
        ("current", "reobserved_unchanged") if target == "unrelated"
        else ("stale", "admitted_delta_required"))
    if target != "unrelated":
        with pytest.raises(ValueError, match="native_lane_scope_not_current"):
            verifier.qualify_direction(receipt)
    assert (_git(root, "rev-parse", "HEAD"), _git(root, "write-tree"), _git(root, "status", "--porcelain")) == before


def test_journal_profile_change_is_not_unrelated_entry_advancement(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch)
    _, original = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
    coordinate = next(d.coordinate for d in original.definitions if d.coordinate.phase_key == "first")
    _publish_goal(root, _append_journal_claim(original, coordinate))
    assert verifier.verify(receipt).status == "stale"


@pytest.mark.parametrize("decision", ["approve", "revoke", "restore"])
def test_cross_goal_endpoint_journal_history_is_relevant(tmp_path, monkeypatch, decision):
    root, receipt, verifier = _publication(tmp_path, monkeypatch,
        incident_direction="incoming", external=True, journal=True, incident_operational=True)
    compatibility, original = extract_goal_phase_native_document((root / CUSTOMER_EXTERNAL_PATH).read_bytes())
    coordinate = original.definitions[0].coordinate
    changed = _append_journal_claim(original, coordinate, decision="revoke")
    def publish(document):
        (root / CUSTOMER_EXTERNAL_PATH).write_bytes(attach_goal_phase_native_document(compatibility, document))
        _git(root, "add", CUSTOMER_EXTERNAL_PATH)
        _git(root, "commit", "-qm", "Change prerequisite journal authority")
    publish(changed)
    if decision == "approve":
        publish(_append_journal_claim(changed, coordinate))
    elif decision == "restore":
        publish(original)
    before = (_git(root, "rev-parse", "HEAD"), _git(root, "write-tree"), _git(root, "status", "--porcelain"))
    verified = verifier.verify(receipt)
    assert (verified.status, verified.replay_disposition) == ("stale", "admitted_delta_required")
    with pytest.raises(ValueError, match="native_lane_scope_not_current"):
        verifier.qualify_direction(receipt)
    assert (_git(root, "rev-parse", "HEAD"), _git(root, "write-tree"), _git(root, "status", "--porcelain")) == before


def test_unknown_compatibility_is_ambiguous(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch)
    compatibility, _ = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
    _publish_goal(root, compatibility=b"Unknown text\n" + compatibility)
    result = verifier.verify(receipt)
    assert (result.status, result.replay_disposition) == ("ambiguous", "refuse")
    assert "compatibility_unknown" in result.reasons


@pytest.mark.parametrize("change", ["owner", "lifecycle"])
def test_goal_global_change_is_relevant(tmp_path, monkeypatch, change):
    root, receipt, verifier = _publication(tmp_path, monkeypatch)
    compatibility, _ = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
    altered = compatibility.replace(b"Owner: `codex-test`", b"Owner: `codex-successor`") if change == "owner" else compatibility.replace(b"Status: `Active`", b"Status: `Completed`")
    _publish_goal(root, compatibility=altered)
    assert verifier.verify(receipt).status == "stale"


def test_side_branch_identical_source_not_current(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch)
    final = (root / CUSTOMER_PATH).read_bytes()
    _git(root, "checkout", "-qb", "sibling", receipt.repository_parent_ref)
    (root / CUSTOMER_PATH).write_bytes(final)
    _git(root, "add", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Same tree on sibling")
    result = verifier.verify(receipt)
    assert (result.status, result.replay_disposition) == ("ambiguous", "refuse")


def test_merge_side_branch_change_and_restore_is_examined(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch)
    _git(root, "branch", "main-proof")
    _git(root, "checkout", "-qb", "side-proof")
    _, original = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
    changed = replace(original, native_lane_authorities=(replace(original.native_lane_authorities[0], role="Changed"),))
    _publish_goal(root, changed)
    _publish_goal(root, original)
    _git(root, "checkout", "-q", "main-proof")
    (root / "unrelated.txt").write_text("main")
    _git(root, "add", "unrelated.txt")
    _git(root, "commit", "-qm", "Main advance")
    _git(root, "merge", "--no-ff", "-qm", "Join", "side-proof")
    result = verifier.verify(receipt)
    assert result.status == "stale"
    assert len(result.history_edges) == 5


def test_verifier_output_mutation_and_constructed_copy_refuse(tmp_path, monkeypatch):
    _, receipt, verifier = _publication(tmp_path, monkeypatch)
    valid = verifier.verify(receipt)
    copied = replace(valid)
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        require_verified_git_native_lane(copied)
    object.__setattr__(valid, "observed_head", "0" * 40)
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        require_verified_git_native_lane(valid)


def test_verifier_registry_is_lifetime_bounded(tmp_path, monkeypatch):
    _, receipt, verifier = _publication(tmp_path, monkeypatch)
    gc.collect()
    count = len(_VERIFIED)
    result = verifier.verify(receipt)
    assert isinstance(result, GitNativeLaneVerificationV1)
    assert len(_VERIFIED) == count + 1
    del result
    gc.collect()
    assert len(_VERIFIED) == count


def test_selected_work_issue_is_observed_and_protected(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch, work=True)
    origin = verifier.verify(receipt)
    assert origin.status == "current"
    assert CUSTOMER_ISSUE_PATH in origin.protected_paths
    path = root / CUSTOMER_ISSUE_PATH
    original = path.read_text()
    path.write_text(original + "\n## Updates\n- Later authority touch\n")
    _git(root, "add", CUSTOMER_ISSUE_PATH)
    _git(root, "commit", "-qm", "Touch current Issue")
    path.write_text(original)
    _git(root, "add", CUSTOMER_ISSUE_PATH)
    _git(root, "commit", "-qm", "Restore current Issue")
    result = verifier.verify(receipt)
    assert result.status == "stale"
    assert result.origin_closure_ref == result.current_closure_ref
    assert len(result.history_edges) == 2


@pytest.mark.parametrize("replacement", ["- Status: Closed", "- Owner: codex-foreign"])
def test_selected_work_foreign_or_closed_issue_refuses(tmp_path, monkeypatch, replacement):
    root, receipt, verifier = _publication(tmp_path, monkeypatch, work=True)
    path = root / CUSTOMER_ISSUE_PATH
    before = "- Status: In Progress" if "Status" in replacement else "- Owner: codex-test"
    path.write_text(path.read_text().replace(before, replacement))
    _git(root, "add", CUSTOMER_ISSUE_PATH)
    _git(root, "commit", "-qm", "Change current Issue authority")
    with pytest.raises(ValueError, match="current_work_issue_disagreement"):
        verifier.verify(receipt)


def test_native_lane_record_cannot_overlap_markdown_lane(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch)
    _, document = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
    extra = replace(document.native_lane_authorities[0], lane_key="runtime")
    _publish_goal(root, replace(document, native_lane_authorities=(*document.native_lane_authorities, extra)))
    with pytest.raises(GoalNativeScopeSourceError, match="overlap"):
        verifier.verify(receipt)


def test_head_advancement_during_verification_refuses(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch)
    original = verifier._closure
    def advance(revision, published, evidence_snapshot=None):
        result = original(revision, published, evidence_snapshot)
        if _git(root, "rev-parse", "HEAD") == receipt.repository_commit_ref:
            (root / "advance.txt").write_text("advance")
            _git(root, "add", "advance.txt")
            _git(root, "commit", "-qm", "Concurrent advance")
        return result
    monkeypatch.setattr(verifier, "_closure", advance)
    with pytest.raises(ValueError, match="repository_head_advanced"):
        verifier.verify(receipt)


@pytest.mark.parametrize("direction", ["incoming", "outgoing"])
def test_new_incident_dependency_is_relevant_scope_change(tmp_path, monkeypatch, direction):
    root, receipt, verifier = _publication(tmp_path, monkeypatch)
    _, document = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
    foundation = next(d for d in document.definitions if d.coordinate.lane_key == "foundation")
    other = next(d for d in document.definitions if d.coordinate.phase_key == "later")
    dependent, prerequisite = (foundation, other) if direction == "incoming" else (other, foundation)
    dependency = GoalPhaseDependency(
        owner_goal_tag=GOAL, dependency_key="qualified-edge-required",
        dependent=dependent.coordinate, prerequisite=prerequisite.coordinate,
        relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
        required_gate_digest=prerequisite.gate.gate_digest, reason="Authored edge",
    )
    _publish_goal(root, replace(document, operational_bundle=replace(document.operational_bundle, dependencies=(dependency,))))
    result = verifier.verify(receipt)
    assert (result.status, result.replay_disposition) == ("stale", "admitted_delta_required")
    assert "lane_scope_changed" in result.reasons


@pytest.mark.parametrize("direction", ["incoming", "outgoing"])
def test_complete_incident_snapshot_preserves_missing_observation(tmp_path, monkeypatch, direction):
    _, receipt, verifier = _publication(tmp_path, monkeypatch, incident_direction=direction)
    result = require_verified_git_native_lane(verifier.verify(receipt))
    assert result.status == "current"
    closure, _, _ = verifier._closure(result.observed_head, receipt)
    assert len(closure["incident_dependencies"]) == 1
    entry = closure["incident_dependencies"][0]
    assert entry["declaration"]["dependency_key"] == "qualified-edge-required"
    assert entry["observation_profile"] == "not_evaluated"
    assert entry["observation"] is None
    assert len(result.dependency_source_epochs) == 1


def test_cross_goal_source_is_independently_read_and_protected(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch, incident_direction="incoming", external=True)
    result = require_verified_git_native_lane(verifier.verify(receipt))
    assert result.status == "current"
    assert CUSTOMER_EXTERNAL_PATH in result.protected_paths
    assert {epoch[1] for epoch in result.dependency_source_epochs} == {GOAL, EXTERNAL_GOAL}
    original = (root / CUSTOMER_EXTERNAL_PATH).read_bytes()
    compatibility, source = extract_goal_phase_native_document(original)
    changed = replace(source, definitions=(replace(source.definitions[0], intent="Changed prerequisite direction"),))
    (root / CUSTOMER_EXTERNAL_PATH).write_bytes(attach_goal_phase_native_document(compatibility, changed))
    _git(root, "add", CUSTOMER_EXTERNAL_PATH)
    _git(root, "commit", "-qm", "External prerequisite change")
    (root / CUSTOMER_EXTERNAL_PATH).write_bytes(original)
    _git(root, "add", CUSTOMER_EXTERNAL_PATH)
    _git(root, "commit", "-qm", "Restore external prerequisite")
    result = verifier.verify(receipt)
    assert result.status == "stale"
    assert result.origin_closure_ref == result.current_closure_ref
    assert len(result.history_edges) == 2


def test_external_whole_document_advance_does_not_invalidate_unchanged_endpoint(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch, incident_direction="incoming", external=True)
    compatibility, source = extract_goal_phase_native_document((root / CUSTOMER_EXTERNAL_PATH).read_bytes())
    extra = replace(source.definitions[0], coordinate=replace(source.definitions[0].coordinate, phase_key="unrelated"), ordinal=3)
    source = replace(source, definitions=(*source.definitions, extra))
    (root / CUSTOMER_EXTERNAL_PATH).write_bytes(attach_goal_phase_native_document(compatibility, source))
    _git(root, "add", CUSTOMER_EXTERNAL_PATH)
    _git(root, "commit", "-qm", "External unrelated definition change")
    result = require_verified_git_native_lane(verifier.verify(receipt))
    assert (result.status, result.replay_disposition) == ("current", "reobserved_unchanged")
    assert len({epoch[0] for epoch in result.dependency_source_epochs}) == 2


def test_missing_external_goal_is_not_current_or_not_evaluated(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch, incident_direction="incoming", external=True)
    _git(root, "rm", CUSTOMER_EXTERNAL_PATH)
    _git(root, "commit", "-qm", "Remove prerequisite source")
    with pytest.raises(ValueError, match="goal_source_unavailable"):
        verifier.verify(receipt)


def test_unqualified_supplied_gate_is_not_downgraded_to_absent(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch, incident_direction="incoming", external=True)
    # The retained publisher deliberately contains a caller-shaped historical
    # Gate token; it is committed but not independently qualified.
    _publish_external_source(root, goal_path=CUSTOMER_EXTERNAL_PATH)
    with pytest.raises(ValueError, match="gate_authority_unavailable"):
        verifier.verify(receipt)


def test_dependency_epoch_mutation_cannot_reseal_verified_result(tmp_path, monkeypatch):
    _, receipt, verifier = _publication(tmp_path, monkeypatch, incident_direction="incoming")
    result = verifier.verify(receipt)
    object.__setattr__(result, "dependency_source_epochs", ())
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        require_verified_git_native_lane(result)


def test_typed_unresolved_declaration_stays_explicit(tmp_path, monkeypatch):
    _, receipt, verifier = _publication(tmp_path, monkeypatch, unresolved=True)
    result = require_verified_git_native_lane(verifier.verify(receipt))
    closure, _, _ = verifier._closure(result.observed_head, receipt)
    assert result.status == "current"
    assert result.dependency_source_epochs == ()
    assert closure["incident_dependencies"][0]["observation_profile"] == "unresolved"
    assert closure["incident_dependencies"][0]["observation"] is None


def test_duplicate_external_goal_authority_refuses(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch, incident_direction="incoming", external=True)
    copy = "customer/objectives/2026/09/26/goal-2026-09-26-copied-external.md"
    (root / copy).write_bytes((root / CUSTOMER_EXTERNAL_PATH).read_bytes())
    _git(root, "add", copy)
    _git(root, "commit", "-qm", "Copied foreign authority carrier")
    with pytest.raises(ValueError, match="goal_source_ambiguous"):
        verifier.verify(receipt)


def test_required_gate_is_bound_to_verified_external_definition(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch, incident_direction="incoming", external=True)
    _, source = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
    wrong = replace(source.operational_bundle.dependencies[0], required_gate_digest="sha256:" + "0" * 64)
    _publish_goal(root, replace(source, operational_bundle=replace(source.operational_bundle, dependencies=(wrong,))))
    with pytest.raises(ValueError, match="required_gate_mismatch"):
        verifier.verify(receipt)


def test_external_unknown_compatibility_delta_is_ambiguous_not_stale(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch, incident_direction="incoming", external=True)
    compatibility, source = extract_goal_phase_native_document((root / CUSTOMER_EXTERNAL_PATH).read_bytes())
    compatibility = b"Unknown external authority text\n" + compatibility
    source = replace(source,
        compatibility_projection_sha256="sha256:" + hashlib.sha256(compatibility).hexdigest(),
        compatibility_projection_byte_count=len(compatibility))
    (root / CUSTOMER_EXTERNAL_PATH).write_bytes(attach_goal_phase_native_document(compatibility, source))
    _git(root, "add", CUSTOMER_EXTERNAL_PATH)
    _git(root, "commit", "-qm", "Unknown prerequisite compatibility delta")
    result = verifier.verify(receipt)
    assert (result.status, result.replay_disposition) == ("ambiguous", "refuse")
    assert "compatibility_unknown" in result.reasons


_ISOLATED_EXTERNAL_PATH = "customer/objectives/2026/09/27/goal-2026-09-27-eligibility-external.md"


def _replace_external_target(root: Path, tmp_path: Path, variant: str) -> None:
    """Change only a disposable fixture target; committed bytes stay exact."""
    target = root / _ISOLATED_EXTERNAL_PATH
    if variant == "leaf":
        outside = tmp_path / "outside-external.md"
        target.rename(outside)
        target.symlink_to(outside)
    elif variant == "parent":
        outside = tmp_path / "outside-goal-directory"
        target.parent.rename(outside)
        target.parent.symlink_to(outside, target_is_directory=True)
    else:
        raise AssertionError("unsupported target replacement")


@pytest.mark.parametrize("variant", ["leaf", "parent"])
def test_external_concrete_target_is_resolved_before_source_use(tmp_path, monkeypatch, variant):
    root, receipt, verifier = _publication(tmp_path, monkeypatch,
        incident_direction="incoming", external=True, external_goal_path=_ISOLATED_EXTERNAL_PATH)
    head = _git(root, "rev-parse", "HEAD")
    _replace_external_target(root, tmp_path, variant)
    assert (root / CUSTOMER_PATH).is_file() and not (root / CUSTOMER_PATH).is_symlink()
    with pytest.raises(NativeGoalResolverError, match="native_goal_target_unresolvable"):
        verifier.verify(receipt)
    assert _git(root, "rev-parse", "HEAD") == head


@pytest.mark.parametrize("variant", ["leaf", "parent"])
def test_external_target_replaced_after_discovery_refuses_before_read(tmp_path, monkeypatch, variant):
    root, receipt, verifier = _publication(tmp_path, monkeypatch,
        incident_direction="incoming", external=True, external_goal_path=_ISOLATED_EXTERNAL_PATH)
    discover, read = verifier._goal_path, verifier._regular_file
    replaced = False
    reads_after_replacement: list[str] = []
    def discover_then_replace(revision, goal_tag):
        nonlocal replaced
        path = discover(revision, goal_tag)
        if not replaced:
            _replace_external_target(root, tmp_path, variant)
            replaced = True
        return path
    def count_reads(revision, path):
        if replaced:
            reads_after_replacement.append(path)
        return read(revision, path)
    monkeypatch.setattr(verifier, "_goal_path", discover_then_replace)
    monkeypatch.setattr(verifier, "_regular_file", count_reads)
    with pytest.raises(NativeGoalResolverError, match="native_goal_target_unresolvable"):
        verifier.verify(receipt)
    assert replaced and reads_after_replacement == []


@pytest.mark.parametrize("variant", ["leaf", "parent"])
def test_terminal_external_target_replacement_cannot_mint_verification(tmp_path, monkeypatch, variant):
    root, receipt, verifier = _publication(tmp_path, monkeypatch,
        incident_direction="incoming", external=True, external_goal_path=_ISOLATED_EXTERNAL_PATH)
    observe_commit = verifier._commit
    head_reads = 0
    count_before = len(_VERIFIED)
    def replace_at_terminal_head(value):
        nonlocal head_reads
        commit = observe_commit(value)
        if value == "HEAD":
            head_reads += 1
            if head_reads == 2:
                _replace_external_target(root, tmp_path, variant)
        return commit
    monkeypatch.setattr(verifier, "_commit", replace_at_terminal_head)
    with pytest.raises(NativeGoalResolverError, match="native_goal_target_unresolvable"):
        verifier.verify(receipt)
    assert head_reads == 2
    assert len(_VERIFIED) == count_before


@pytest.mark.parametrize("target", ["dependent", "prerequisite"])
def test_head_advance_during_terminal_target_resolution_cannot_issue(tmp_path, monkeypatch, target):
    root, receipt, verifier = _publication(tmp_path, monkeypatch,
        incident_direction="incoming", external=True, external_goal_path=_ISOLATED_EXTERNAL_PATH)
    observed_head = _git(root, "rev-parse", "HEAD")
    observe_commit = verifier._commit
    resolver_type = type(verifier._capability)
    resolve_target = resolver_type.resolve_goal_path
    head_reads = 0
    advanced = False
    count_before = len(_VERIFIED)
    trigger_path = CUSTOMER_PATH if target == "dependent" else _ISOLATED_EXTERNAL_PATH

    def count_head_observations(value):
        nonlocal head_reads
        if value == "HEAD":
            head_reads += 1
        return observe_commit(value)

    def resolve_then_publish(capability, path):
        nonlocal advanced
        location = resolve_target(capability, path)
        if head_reads == 2 and path == trigger_path and not advanced:
            _, document = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
            record = replace(document.native_lane_authorities[0], role="Concurrent semantic change")
            _publish_goal(root, replace(document, native_lane_authorities=(record,)))
            advanced = True
        return location

    monkeypatch.setattr(verifier, "_commit", count_head_observations)
    monkeypatch.setattr(resolver_type, "resolve_goal_path", resolve_then_publish)
    with pytest.raises(ValueError, match="repository_head_advanced"):
        verifier.verify(receipt)
    assert advanced and head_reads == 3
    assert _git(root, "rev-parse", "HEAD") != observed_head
    assert len(_VERIFIED) == count_before


def test_held_lane_requires_separate_qualified_hold_intake(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch)
    _, document = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
    held = replace(document.native_lane_authorities[0],
        operational_state="held", state_detail="Explicitly held",
        hold_authority_refs=("goal-lane-hold:sha256:" + "a" * 64,),
    )
    _publish_goal(root, replace(document, native_lane_authorities=(held,)))
    with pytest.raises(ValueError, match="hold_authority_unavailable"):
        verifier.verify(receipt)


@pytest.mark.parametrize("state", ["held", "blocked"])
@pytest.mark.parametrize("work", [False, True])
def test_real_git_goal_owner_hold_issuance_is_a_proof_not_eligibility(tmp_path, monkeypatch, state, work):
    root, receipt, direction = _publication(tmp_path, monkeypatch, hold=state, work=work)
    verifier = GitNativeLaneHoldAuthorityVerifier(resolver_capability=_native_capability(root, monkeypatch))
    verified = require_verified_native_lane_hold(verifier.verify(receipt))
    assert type(verified) is GitNativeLaneHoldVerificationV1
    assert verified.decision.target_state == state
    assert verified.observed_head == _git(root, "rev-parse", "HEAD")
    assert verified.decision_issue_authority["owner"] == "codex-test"
    assert verified.source_goal_blob_oid == receipt.before_goal_blob_oid
    assert verified.source_goal_sha256 == receipt.before_goal_sha256
    assert set(verified.protected_paths) == {CUSTOMER_PATH, CUSTOMER_ISSUE_PATH}
    assert (verified.selected_work_issue_authority is not None) == work
    assert (verified.selected_work_issue_source_authority is not None) == work
    assert verified.selected_work_issue_permitted_effect_receipt_refs == (
        ("repository-commit:" + verified.decision_commit_ref,) if work else ()
    )
    assert verified.to_wire()["effect_profile"] == "read_only_non_authorizing"
    assert decode_native_lane_hold_verification(verified.to_wire(), qualified=verified) is verified
    # The primitive is non-authorizing; the fresh joined entrance separately
    # qualifies its complete snapshot before the neutral reducer sees a hold.
    qualified = direction.qualify_direction(receipt)
    snapshot = require_qualified_native_lane_evidence(qualified.evidence_snapshot)
    assert qualified.to_wire()["schema_id"] == "aware.goal.native-lane-direction-authority.v2"
    assert direction.verify(receipt).to_wire()["schema_id"] == "aware.goal.git-native-lane-verification.v2"
    assert snapshot.holds[0].issuance_authority == verified.to_wire()
    decision = observe_goal_phase_eligibility_v2(**_eligibility_inputs(qualified))
    assert decision.decision.eligibility == "held"
    assert decision.decision.reasons == ("lane_not_open",)
    assert decode_goal_phase_eligibility_decision_v2(decision.to_wire(), **_eligibility_inputs(qualified)) == decision
    assert decode_goal_native_lane_evidence_snapshot(snapshot.to_wire(), qualified=snapshot) is snapshot


@pytest.mark.parametrize("separate_work_issue", [False, True])
def test_hold_binds_selected_work_source_and_only_authenticated_decision_effect(tmp_path, monkeypatch, separate_work_issue):
    root, receipt, direction = _publication(
        tmp_path, monkeypatch, hold="held", work=True, separate_work_issue=separate_work_issue,
    )
    verifier = GitNativeLaneHoldAuthorityVerifier(resolver_capability=_native_capability(root, monkeypatch))
    verified = verifier.verify(receipt)
    path = FOUNDATION_WORK_PATH if separate_work_issue else CUSTOMER_ISSUE_PATH
    source = verified.selected_work_issue_source_authority
    current = verified.selected_work_issue_authority
    assert source is not None and current is not None
    assert source["path"] == current["path"] == path
    assert source["blob_oid"] == _git(root, "rev-parse", f"{verified.decision.source_revision_ref}:{path}")
    assert current["blob_oid"] == _git(root, "rev-parse", f"{verified.observed_head}:{path}")
    assert source["owner"] == current["owner"] == "codex-test"
    assert source["status"] == current["status"] == "in_progress"
    assert source["scope_digest"] == current["scope_digest"]
    if separate_work_issue:
        assert source == current
        assert verified.selected_work_issue_permitted_effect_receipt_refs == ()
    else:
        assert source["blob_oid"] != current["blob_oid"]
        assert current == verified.decision_issue_authority
        assert verified.selected_work_issue_permitted_effect_receipt_refs == ("repository-commit:" + verified.decision_commit_ref,)
    assert set(verified.protected_paths) == {CUSTOMER_PATH, CUSTOMER_ISSUE_PATH, path}
    assert decode_native_lane_hold_verification(verified.to_wire(), qualified=verified) is verified
    result = observe_goal_phase_eligibility_v2(**_eligibility_inputs(direction.qualify_direction(receipt)))
    assert result.decision.eligibility == "held"
    assert result.decision.reasons == ("lane_not_open",)


@pytest.mark.parametrize("separate_work_issue", [False, True])
@pytest.mark.parametrize("fault", ["work_change_restore_before_decision", "work_change_restore_after_decision"])
def test_hold_protects_selected_work_issue_from_source_through_introduction(tmp_path, monkeypatch, separate_work_issue, fault):
    root, receipt, _ = _publication(
        tmp_path, monkeypatch, hold="held", work=True,
        separate_work_issue=separate_work_issue, hold_fault=fault,
    )
    verifier = GitNativeLaneHoldAuthorityVerifier(resolver_capability=_native_capability(root, monkeypatch))
    count = len(_HOLD_ISSUED)
    reason = "goal_owner_issuance_invalid" if not separate_work_issue and fault == "work_change_restore_after_decision" else "protected_history_changed"
    with pytest.raises(ValueError, match=reason):
        verifier.verify(receipt)
    assert len(_HOLD_ISSUED) == count


def test_hold_distinct_work_issue_change_restore_after_introduction_refuses(tmp_path, monkeypatch):
    root, receipt, _ = _publication(tmp_path, monkeypatch, hold="held", work=True, separate_work_issue=True)
    _change_restore_work_owner(root, FOUNDATION_WORK_PATH)
    verifier = GitNativeLaneHoldAuthorityVerifier(resolver_capability=_native_capability(root, monkeypatch))
    count = len(_HOLD_ISSUED)
    with pytest.raises(ValueError, match="protected_history_changed"):
        verifier.verify(receipt)
    assert len(_HOLD_ISSUED) == count


@pytest.mark.parametrize("fault,reason", [
    ("token_only", "issue_block_ambiguous"),
    ("foreign_lane", "decision_carrier_mismatch"),
    ("no_decision_receipt", "issue_receipt_absent"),
    ("foreign_issuer", "issue_receipt_mismatch"),
    ("extra_decision_path", "decision_effect_invalid"),
    ("inherited_decision", "decision_inherited_or_replaced"),
    ("source_change_restore", "protected_history_changed"),
])
def test_hold_decision_requires_actual_authorized_publication(tmp_path, monkeypatch, fault, reason):
    root, receipt, _ = _publication(tmp_path, monkeypatch, hold="held", hold_fault=fault)
    verifier = GitNativeLaneHoldAuthorityVerifier(resolver_capability=_native_capability(root, monkeypatch))
    count = len(_HOLD_ISSUED)
    with pytest.raises(ValueError, match=reason):
        verifier.verify(receipt)
    assert len(_HOLD_ISSUED) == count


@pytest.mark.parametrize("path", [CUSTOMER_PATH, CUSTOMER_ISSUE_PATH])
def test_hold_protected_history_detects_issue_or_goal_change_restore(tmp_path, monkeypatch, path):
    root, receipt, _ = _publication(tmp_path, monkeypatch, hold="held")
    verifier = GitNativeLaneHoldAuthorityVerifier(resolver_capability=_native_capability(root, monkeypatch))
    original = (root / path).read_bytes()
    (root / path).write_bytes(original + b"\nChanged authority\n")
    _git(root, "add", path)
    _git(root, "commit", "-qm", "Change protected authority")
    (root / path).write_bytes(original)
    _git(root, "add", path)
    _git(root, "commit", "-qm", "Restore protected authority")
    with pytest.raises(ValueError, match="protected_history_changed"):
        verifier.verify(receipt)


def test_hold_release_is_not_an_implicit_supported_transition(tmp_path, monkeypatch):
    root, receipt, _ = _publication(tmp_path, monkeypatch, hold="held")
    _, document = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
    released = replace(document.native_lane_authorities[0],
        operational_state="active", state_detail=None, hold_authority_refs=(),
    )
    _publish_goal(root, replace(document, native_lane_authorities=(released,)))
    with pytest.raises(ValueError, match="protected_history_changed"):
        GitNativeLaneHoldAuthorityVerifier(resolver_capability=_native_capability(root, monkeypatch)).verify(receipt)


@pytest.mark.parametrize("path", [CUSTOMER_PATH, CUSTOMER_ISSUE_PATH])
def test_hold_proof_requires_concrete_goal_and_issue_target_containment(tmp_path, monkeypatch, path):
    root, receipt, _ = _publication(tmp_path, monkeypatch, hold="held")
    verifier = GitNativeLaneHoldAuthorityVerifier(resolver_capability=_native_capability(root, monkeypatch))
    target = root / path
    outside = tmp_path / "outside-source.md"
    outside.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(outside)
    count = len(_HOLD_ISSUED)
    expected_error = NativeGoalResolverError if path == CUSTOMER_PATH else GoalNativeScopeSourceError
    with pytest.raises(expected_error):
        verifier.verify(receipt)
    assert len(_HOLD_ISSUED) == count


def test_hold_unrelated_advance_is_reobserved_at_real_head(tmp_path, monkeypatch):
    root, receipt, _ = _publication(tmp_path, monkeypatch, hold="held")
    verifier = GitNativeLaneHoldAuthorityVerifier(resolver_capability=_native_capability(root, monkeypatch))
    earlier = verifier.verify(receipt)
    (root / "unrelated.txt").write_text("No Goal or Issue touch")
    _git(root, "add", "unrelated.txt")
    _git(root, "commit", "-qm", "Unrelated advance")
    fresh = verifier.verify(receipt)
    assert earlier.decision == fresh.decision
    assert earlier.observed_head != fresh.observed_head
    assert fresh.observed_head == _git(root, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match="transport_differs"):
        decode_native_lane_hold_verification(earlier.to_wire(), qualified=fresh)


@pytest.mark.parametrize("mutation", ["copy", "construct", "decision", "issue", "work_source", "permitted_effect", "head"])
def test_actually_issued_hold_verification_cannot_be_copied_or_mutated(tmp_path, monkeypatch, mutation):
    root, receipt, _ = _publication(tmp_path, monkeypatch, hold="held", work=True)
    verifier = GitNativeLaneHoldAuthorityVerifier(resolver_capability=_native_capability(root, monkeypatch))
    verified = verifier.verify(receipt)
    if mutation == "copy":
        verified = deepcopy(verified)
    elif mutation == "construct":
        verified = replace(verified)
    elif mutation == "decision":
        changed = replace(verified.decision, state_detail="Newly digested counterfeit decision")
        object.__setattr__(verified, "decision", changed)
    elif mutation == "issue":
        verified.decision_issue_authority["owner"] = "codex-foreign"
    elif mutation == "work_source":
        verified.selected_work_issue_source_authority["blob_oid"] = "a" * 40
    elif mutation == "permitted_effect":
        object.__setattr__(verified, "selected_work_issue_permitted_effect_receipt_refs", ())
    else:
        object.__setattr__(verified, "observed_head", "a" * 40)
    # to_wire recomputes the ref; the retained issued fingerprint still refuses.
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        require_verified_native_lane_hold(verified)
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        decode_native_lane_hold_verification(verified.to_wire(), qualified=verified)


def test_hold_transport_redigestion_cannot_replace_issued_authority(tmp_path, monkeypatch):
    root, receipt, _ = _publication(tmp_path, monkeypatch, hold="held")
    verified = GitNativeLaneHoldAuthorityVerifier(resolver_capability=_native_capability(root, monkeypatch)).verify(receipt)
    payload = deepcopy(verified.to_wire())
    payload["decision"]["state_detail"] = "Different hold"
    payload["verification_ref"] = "goal-git-native-lane-hold-verification:" + fingerprint({k: v for k, v in payload.items() if k != "verification_ref"})
    with pytest.raises(ValueError, match="transport_differs"):
        decode_native_lane_hold_verification(payload, qualified=verified)


@pytest.mark.parametrize("work", [False, True])
def test_hold_terminal_head_check_follows_concrete_target_checks(tmp_path, monkeypatch, work):
    root, receipt, _ = _publication(tmp_path, monkeypatch, hold="held", work=work, separate_work_issue=work)
    capability = _native_capability(root, monkeypatch)
    verifier = GitNativeLaneHoldAuthorityVerifier(resolver_capability=capability)
    unchanged = verifier._unchanged
    armed = False
    advanced = False
    def guard(*args):
        nonlocal armed
        unchanged(*args)
        armed = args[0] == receipt.repository_commit_ref
    resolver_type = type(capability)
    resolve = resolver_type.resolve_goal_path
    def target(*args):
        nonlocal advanced
        location = resolve(*args)
        if armed and not advanced:
            (root / "concurrent.txt").write_text("Concurrent repository effect")
            _git(root, "add", "concurrent.txt")
            _git(root, "commit", "-qm", "Advance during terminal provider I/O")
            advanced = True
        return location
    monkeypatch.setattr(verifier, "_unchanged", guard)
    monkeypatch.setattr(resolver_type, "resolve_goal_path", target)
    count = len(_HOLD_ISSUED)
    with pytest.raises(ValueError, match="repository_head_advanced"):
        verifier.verify(receipt)
    assert advanced and len(_HOLD_ISSUED) == count


def test_hold_issuance_registration_has_output_lifetime(tmp_path, monkeypatch):
    root, receipt, _ = _publication(tmp_path, monkeypatch, hold="held")
    verifier = GitNativeLaneHoldAuthorityVerifier(resolver_capability=_native_capability(root, monkeypatch))
    gc.collect()
    initial = len(_HOLD_ISSUED)
    verified = verifier.verify(receipt)
    assert len(_HOLD_ISSUED) == initial + 1
    del verified
    gc.collect()
    assert len(_HOLD_ISSUED) == initial


@pytest.mark.parametrize("direction,external", [("incoming", False), ("incoming", True), ("outgoing", False)])
def test_joined_hold_snapshot_binds_complete_incident_inventory(tmp_path, monkeypatch, external, direction):
    root, receipt, provider = _publication(tmp_path, monkeypatch, hold="held", work=True,
        separate_work_issue=True, incident_direction=direction, external=external, unresolved=True)
    qualified = provider.qualify_direction(receipt)
    snapshot = qualified.evidence_snapshot
    assert snapshot.source_revision_ref == _git(root, "rev-parse", "HEAD")
    assert snapshot.gate_observations == ()
    assert [pair[0] for pair in snapshot.incident_declarations] == ["qualified-edge-required", "unresolved-foundation-edge"]
    assert snapshot.incident_declarations[0][1] == goal_phase_dependency_digest(qualified.document.operational_bundle.dependencies[0])
    paths = {item["path"] if "path" in item else item["authority"].get("path") for item in snapshot.authority_inventory}
    assert {CUSTOMER_PATH, CUSTOMER_ISSUE_PATH, FOUNDATION_WORK_PATH} <= paths
    if external:
        assert CUSTOMER_EXTERNAL_PATH in paths
    result = observe_goal_phase_eligibility_v2(**_eligibility_inputs(qualified))
    assert result.decision.eligibility == "held"
    assert "lane_not_open" in result.decision.reasons
    assert result.decision.observation_coverage == "none"
    if direction == "incoming":
        assert result.decision.dependency_gate.not_evaluated_keys == ("qualified-edge-required",)


@pytest.mark.parametrize("mutation", ["clone", "echo", "source", "decision", "issuance", "inventory", "gate", "incident"])
def test_actually_issued_evidence_snapshot_mutation_refuses_before_eligibility(tmp_path, monkeypatch, mutation):
    _, receipt, provider = _publication(tmp_path, monkeypatch, hold="held", work=True,
        separate_work_issue=True, incident_direction="incoming")
    qualified = provider.qualify_direction(receipt)
    snapshot = qualified.evidence_snapshot
    if mutation == "clone":
        snapshot = replace(snapshot)
        object.__setattr__(qualified, "evidence_snapshot", snapshot)
    elif mutation == "echo":
        class EchoIssuer(GoalNativeLaneEvidenceIssuerV2):
            def require_snapshot(self, value):
                return None
        object.__setattr__(snapshot, "source_evidence", EchoIssuer())
    elif mutation == "source":
        object.__setattr__(snapshot, "source_revision_ref", "a" * 40)
    elif mutation == "decision":
        object.__setattr__(snapshot.holds[0].decision, "state_detail", "Counterfeit reason")
    elif mutation == "issuance":
        snapshot.holds[0].issuance_authority["selected_work_issue_source_authority"]["owner"] = "codex-foreign"
    elif mutation == "inventory":
        object.__setattr__(snapshot, "authority_inventory", snapshot.authority_inventory[:1])
    elif mutation == "gate":
        object.__setattr__(snapshot, "gate_observations", ({"outcome": "satisfied"},))
    else:
        object.__setattr__(snapshot, "incident_declarations", ())
    # Invalid typed Gate records refuse even transport serialization; all other
    # mutations still demonstrate that re-digestion cannot replace issuance.
    if mutation == "gate":
        with pytest.raises(ValueError, match="gate_authority_unavailable"):
            _ = snapshot.to_wire()
    else:
        _ = snapshot.to_wire()
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        require_qualified_native_lane_evidence(snapshot)
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        observe_goal_phase_eligibility_v2(**_eligibility_inputs(qualified))


@pytest.mark.parametrize("mutation", ["unknown", "source", "inventory", "decision", "effect", "type"])
def test_evidence_snapshot_transport_redigestion_cannot_replace_authority(tmp_path, monkeypatch, mutation):
    root, receipt, _ = _publication(tmp_path, monkeypatch, hold="held")
    snapshot = GitNativeLaneEvidenceVerifier(resolver_capability=_native_capability(root, monkeypatch)).qualify(receipt)
    payload = deepcopy(snapshot.to_wire())
    if mutation == "unknown":
        payload["eligible"] = True
    elif mutation == "source":
        payload["source_revision_ref"] = "a" * 40
    elif mutation == "inventory":
        payload["authority_inventory"] = []
    elif mutation == "decision":
        payload["holds"][0]["decision"]["state_detail"] = "Counterfeit reason"
    elif mutation == "effect":
        payload["event_effect"] = "issued"
    else:
        payload["holds"][0]["issuance_authority"]["source_goal_sha256"] = False
    payload["snapshot_ref"] = "goal-native-lane-evidence:" + fingerprint({k: v for k, v in payload.items() if k != "snapshot_ref"})
    with pytest.raises(ValueError, match="transport_differs"):
        decode_goal_native_lane_evidence_snapshot(payload, qualified=snapshot)


@pytest.mark.parametrize("fault", ["token_only", "foreign_lane", "no_decision_receipt", "foreign_issuer",
    "extra_decision_path", "inherited_decision", "source_change_restore", "work_change_restore_after_decision", "unqualified_gate"])
def test_joined_hold_entrance_issues_no_snapshot_for_unqualified_authority(tmp_path, monkeypatch, fault):
    root, receipt, provider = _publication(tmp_path, monkeypatch, hold="held", work=True,
        separate_work_issue=True, hold_fault=fault)
    gc.collect()
    count = len(_SNAPSHOT_ISSUED)
    reason = {
        "token_only": "issue_block_ambiguous", "foreign_lane": "decision_carrier_mismatch",
        "no_decision_receipt": "issue_receipt_absent", "foreign_issuer": "issue_receipt_mismatch",
        "extra_decision_path": "decision_effect_invalid", "inherited_decision": "decision_inherited_or_replaced",
        "source_change_restore": "protected_history_changed", "work_change_restore_after_decision": "protected_history_changed",
        "unqualified_gate": "native_lane_gate_authority_unavailable",
    }[fault]
    with pytest.raises(ValueError, match=reason):
        provider.qualify_direction(receipt)
    assert len(_SNAPSHOT_ISSUED) == count


def test_joined_hold_snapshot_reobserves_unrelated_head_without_relabeling_decision(tmp_path, monkeypatch):
    root, receipt, provider = _publication(tmp_path, monkeypatch, hold="held")
    old = provider.qualify_direction(receipt)
    (root / "unrelated.txt").write_text("No source authority changed")
    _git(root, "add", "unrelated.txt")
    _git(root, "commit", "-qm", "Unrelated HEAD advance")
    fresh = provider.qualify_direction(receipt)
    assert fresh.semantic_closure_ref == old.semantic_closure_ref
    assert fresh.evidence_snapshot.holds[0].decision == old.evidence_snapshot.holds[0].decision
    assert fresh.evidence_snapshot.source_revision_ref != old.evidence_snapshot.source_revision_ref
    assert fresh.evidence_snapshot.holds[0].evidence_source_revision_ref == old.evidence_snapshot.holds[0].evidence_source_revision_ref
    assert fresh.evidence_snapshot.to_wire()["snapshot_ref"] != old.evidence_snapshot.to_wire()["snapshot_ref"]
    with pytest.raises(ValueError, match="transport_differs"):
        decode_goal_native_lane_evidence_snapshot(old.evidence_snapshot.to_wire(), qualified=fresh.evidence_snapshot)
    assert observe_goal_phase_eligibility_v2(**_eligibility_inputs(fresh)).decision.eligibility == "held"


def test_joined_hold_snapshot_registration_has_output_lifetime(tmp_path, monkeypatch):
    root, receipt, _ = _publication(tmp_path, monkeypatch, hold="held")
    verifier = GitNativeLaneEvidenceVerifier(resolver_capability=_native_capability(root, monkeypatch))
    gc.collect()
    count = len(_SNAPSHOT_ISSUED)
    snapshot = verifier.qualify(receipt)
    assert len(_SNAPSHOT_ISSUED) == count + 1
    del snapshot
    gc.collect()
    assert len(_SNAPSHOT_ISSUED) == count


def test_snapshot_terminal_head_check_follows_external_target_resolution(tmp_path, monkeypatch):
    root, receipt, _ = _publication(tmp_path, monkeypatch, hold="held", incident_direction="incoming", external=True)
    capability = _native_capability(root, monkeypatch)
    verifier = GitNativeLaneEvidenceVerifier(resolver_capability=capability)
    source = verifier._holds._source
    dependencies = source._dependency_sources
    armed = False
    advanced = False
    def restore(*args):
        nonlocal armed
        result = dependencies(*args)
        armed = True
        return result
    resolve = type(capability).resolve_goal_path
    def target(self, path):
        nonlocal advanced
        location = resolve(self, path)
        if armed and not advanced and path == CUSTOMER_EXTERNAL_PATH:
            (root / "concurrent.txt").write_text("Advance during terminal external I/O")
            _git(root, "add", "concurrent.txt")
            _git(root, "commit", "-qm", "Concurrent HEAD advance")
            advanced = True
        return location
    monkeypatch.setattr(source, "_dependency_sources", restore)
    monkeypatch.setattr(type(capability), "resolve_goal_path", target)
    count = len(_SNAPSHOT_ISSUED)
    with pytest.raises(ValueError, match="repository_head_advanced"):
        verifier.qualify(receipt)
    assert advanced and len(_SNAPSHOT_ISSUED) == count


@pytest.mark.parametrize("parent", [False, True])
def test_snapshot_rechecks_external_target_after_source_restoration(tmp_path, monkeypatch, parent):
    path = "customer/objectives/2026/09/27/goal-2026-09-27-eligibility-external.md"
    root, receipt, _ = _publication(tmp_path, monkeypatch, hold="held", incident_direction="incoming",
        external=True, external_goal_path=path)
    verifier = GitNativeLaneEvidenceVerifier(resolver_capability=_native_capability(root, monkeypatch))
    source = verifier._holds._source
    restore = source._dependency_sources
    def replace_target(*args):
        result = restore(*args)
        target = root / path
        outside = tmp_path / "outside-external-source"
        if parent:
            target.parent.rename(outside)
            target.parent.symlink_to(outside, target_is_directory=True)
        else:
            outside.write_bytes(target.read_bytes())
            target.unlink()
            target.symlink_to(outside)
        return result
    monkeypatch.setattr(source, "_dependency_sources", replace_target)
    count = len(_SNAPSHOT_ISSUED)
    with pytest.raises(NativeGoalResolverError):
        verifier.qualify(receipt)
    assert len(_SNAPSHOT_ISSUED) == count


@pytest.mark.parametrize("restore", [False, True])
def test_held_lane_still_checks_external_semantic_history(tmp_path, monkeypatch, restore):
    root, receipt, provider = _publication(tmp_path, monkeypatch, hold="held", incident_direction="incoming", external=True)
    old_bytes = (root / CUSTOMER_EXTERNAL_PATH).read_bytes()
    compatibility, external = extract_goal_phase_native_document(old_bytes)
    changed = replace(external, definitions=tuple(replace(d, title="Changed prerequisite direction") for d in external.definitions))
    (root / CUSTOMER_EXTERNAL_PATH).write_bytes(attach_goal_phase_native_document(compatibility, changed))
    _git(root, "add", CUSTOMER_EXTERNAL_PATH)
    _git(root, "commit", "-qm", "Change incident external direction")
    if restore:
        (root / CUSTOMER_EXTERNAL_PATH).write_bytes(old_bytes)
        _git(root, "add", CUSTOMER_EXTERNAL_PATH)
        _git(root, "commit", "-qm", "Restore exact external direction")
    result = provider.verify(receipt)
    assert (result.status, result.replay_disposition) == ("stale", "admitted_delta_required")
    with pytest.raises(ValueError, match="native_lane_scope_not_current"):
        provider.qualify_direction(receipt)


def test_absence_wire_schemas_and_fields_remain_exact(tmp_path, monkeypatch):
    _, receipt, provider = _publication(tmp_path, monkeypatch)
    verification = provider.verify(receipt).to_wire()
    direction = provider.qualify_direction(receipt).to_wire()
    assert verification["schema_id"] == "aware.goal.git-native-lane-verification.v1"
    assert "evidence_snapshot_ref" not in verification
    assert direction["schema_id"] == "aware.goal.native-lane-direction-authority.v1"
    assert "evidence_snapshot" not in direction


def test_branch_forked_before_introduction_is_not_qualified(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch)
    _git(root, "branch", "introduced-main")
    _git(root, "checkout", "-qb", "old-fork", receipt.repository_parent_ref)
    (root / "unrelated.txt").write_text("older side branch")
    _git(root, "add", "unrelated.txt")
    _git(root, "commit", "-qm", "Pre-introduction branch")
    _git(root, "checkout", "-q", "introduced-main")
    _git(root, "merge", "--no-ff", "-qm", "Join old fork", "old-fork")
    with pytest.raises(ValueError, match="history_unqualified_branch"):
        verifier.verify(receipt)


def test_gate_observation_requires_qualified_evidence_currentness(tmp_path, monkeypatch):
    root, receipt, verifier = _publication(tmp_path, monkeypatch)
    _, document = extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
    phases = tuple(
        replace(p, gate_observations=(GoalLanePhaseGateObservation(
            observation_ref="gate-observation:unverified", gate_digest=p.gate.gate_digest,
            outcome=GoalLanePhaseGateOutcome.SATISFIED, evaluator_ref="evaluator:unverified",
            evidence_refs=("evidence:unverified",), source_revision_refs=(receipt.repository_commit_ref,),
            evaluated_at="2026-09-26T12:00:00Z", currentness_ref="currentness:unverified",
        ),)) if p.coordinate.lane_key == "foundation" else p
        for p in document.operational_bundle.phases
    )
    _publish_goal(root, replace(document, operational_bundle=replace(document.operational_bundle, phases=phases)))
    with pytest.raises(ValueError, match="gate_authority_unavailable"):
        verifier.verify(receipt)
