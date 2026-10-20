"""Real provider canaries. Git writes are confined to pytest-owned repositories."""
from __future__ import annotations

import gc
import hashlib
import subprocess
from copy import copy, deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
from aware_goal_operational_runtime import (
    GoalLanePhaseGate, attach_goal_phase_native_carrier, extract_goal_phase_native_carrier,
    GoalPhaseDependency, GoalDependencyRelation,
    GoalPhaseOperationJournalEntryV1, GoalPhaseOperationJournalV1,
)
from aware_goal_operational_runtime.phase_runtime_checks_review import (
    EVIDENCE_SCHEMA, GATE_CONTRACT, INVARIANTS, PROFILE, PROOF, PUBLICATION, REQUEST, REVIEW,
    RuntimeChecksVerifiedInputV2, canonical_json, digest, endpoints_coord, make_runtime_checks_artifact,
    evaluate_runtime_checks_review_v2, decode_runtime_checks_evaluation,
    RuntimeChecksEvaluationV2, require_runtime_checks_evaluation, _EVALUATIONS,
)
from aware_goal_native_fs_adapter.runtime_checks_review import GitRuntimeChecksReviewAuthorityVerifier, _ISSUED
from aware_goal_native_fs_adapter.native_lane_evidence import GitNativeLaneEvidenceVerifier, _ISSUED as _SNAPSHOT_ISSUED
from aware_goal_operational_runtime.phase_native_lane_evidence import (
    GoalNativeLaneQualifiedGateV2, require_qualified_native_lane_evidence,
    require_native_lane_evidence_for_document, decode_goal_native_lane_evidence_snapshot,
)
from test_native_lane_authority import _publication, FOUNDATION_WORK_PATH, FOUNDATION_WORK_TAG
from test_native_provider import _git, _native_capability, CUSTOMER_PATH, GOAL

REQUEST_PATH = "proof/request.json"
PROOF_PATH = "proof/checks.json"
REVIEW_PATH = "proof/review.json"
REQUEST_ISSUE = "work/issues/2026/09/26/fb-2026-09-26-request.md"
REVIEW_ISSUE = "work/issues/2026/09/26/fb-2026-09-26-review.md"
FOREIGN_ISSUE = "work/issues/2026/09/26/fb-2026-09-26-foreign.md"
SOURCES = ["runtime/a.py", "runtime/b.py"]
OUTPUTS = ["proof/tests.txt", "proof/canary.txt", "proof/static.txt"]


def _bytes(root, name, data):
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)


def _issue(root, name, owner, scope):
    tag = "fb/2026-09-26/" + Path(name).stem.removeprefix("fb-2026-09-26-")
    _bytes(root, name, (f"# Proof authority\n\n- Tag: {tag}\n- Owner: {owner}\n- Status: In Progress\n\n## Ownership Scope\n" + "".join(f"- `{p}`\n" for p in scope) + "\n## Updates\n").encode())


def _effect(root, issue, paths):
    paths = list(paths)  # The real operational writer preserves explicit operand order.
    owner = next(x.removeprefix("- Owner: ") for x in (root / issue).read_text().splitlines() if x.startswith("- Owner: "))
    tag = next(x.removeprefix("- Tag: ") for x in (root / issue).read_text().splitlines() if x.startswith("- Tag: "))
    _git(root, "add", *paths)
    _git(root, "commit", "-qm", "Governed proof\n\n" + f"Issue-Tag: {tag}\nIssue-Path: {issue}\nOwner: {owner}\nOwned-Paths: {','.join(paths)}")
    return _git(root, "rev-parse", "HEAD")


def _file(root, revision, name):
    content = subprocess.check_output(["git", "show", f"{revision}:{name}"], cwd=root)
    return {"path": name, "blob_ref": _git(root, "rev-parse", f"{revision}:{name}"),
        "sha256": "sha256:" + hashlib.sha256(content).hexdigest()}


def _binding(verifier, root, artifact, artifact_path, issue_path, write_paths):
    parent = _git(root, "rev-parse", "HEAD")
    issue = verifier._source._issue(parent, issue_path)
    _bytes(root, artifact_path, canonical_json(artifact.to_wire()).encode())
    (root / issue_path).write_text((root / issue_path).read_text() + "- Proof publication.\n")
    commit = _effect(root, issue_path, write_paths)
    ref = artifact.to_wire()[{REQUEST: "request_ref", PROOF: "proof_ref", REVIEW: "review_ref"}[artifact.to_wire()["schema_id"]]]
    return make_runtime_checks_artifact(PUBLICATION, {
        "artifact_schema_id": artifact.to_wire()["schema_id"], "artifact_ref": ref,
        "artifact_path": artifact_path, "artifact_blob_ref": _git(root, "rev-parse", f"{commit}:{artifact_path}"),
        "repository_revision_ref": commit, "repository_commit_receipt_ref": "repository-commit:" + commit,
        "governing_issue_path": issue_path, "governing_issue_blob_ref": _git(root, "rev-parse", f"{commit}:{issue_path}"),
        "owner_execution_id": issue["owner"], "status": issue["status"], "scope": list(issue["scope"]), "scope_digest": issue["scope_digest"],
    })


def _journal_entry(doc, definition, *, label, approval=None):
    def ref(domain):
        return domain + ":sha256:" + hashlib.sha256((domain + label).encode()).hexdigest()
    return GoalPhaseOperationJournalEntryV1(
        operation_kind="approve_pursuit", decision="approve" if approval is None else "revoke",
        coordinate=definition.coordinate, gate_digest=definition.gate.gate_digest,
        source_preimage_ref=doc.document_ref, actor_ref="human:review-fixture",
        action_occurrence_ref=ref("actor-action"), policy_ref=ref("goal-policy"),
        policy_digest="sha256:" + "6" * 64, idempotency_key=label,
        delta_ref=ref("goal-phase-delta"), event_ref=ref("goal-phase-event"),
        approval_entry_ref=None if approval is None else approval.entry_ref,
    )


def _proof_chain(tmp_path, monkeypatch, *, fault=None, verdict="accepted", check_fault=None,
    seed_journal=None, extra_operational_phase=False, publication_holder=None, consumer_relation=None):
    root, receipt, _ = _publication(tmp_path, monkeypatch, work=True, separate_work_issue=True,
        runtime_checks=publication_holder is not None, consumer_relation=consumer_relation)
    if publication_holder is not None:
        publication_holder.append(receipt)
    prefix, doc = extract_goal_phase_native_carrier((root / CUSTOMER_PATH).read_bytes())
    definition = next(d for d in doc.definitions if d.coordinate.lane_key == "foundation")
    gate = GoalLanePhaseGate(gate_key="runtime-checks", promise="Exact opt-in runtime checks.", gate_contract_ref=GATE_CONTRACT,
        evidence_schema_ref=EVIDENCE_SCHEMA, invariant_refs=INVARIANTS)
    definition = replace(definition, gate=gate)
    doc = replace(doc, definitions=tuple(definition if d.coordinate == definition.coordinate else d for d in doc.definitions),
        operational_bundle=replace(doc.operational_bundle, phases=tuple(replace(p, gate=gate) if p.coordinate == definition.coordinate else p for p in doc.operational_bundle.phases)))
    if extra_operational_phase:
        later = next(d for d in doc.definitions if d.coordinate.phase_key == "later")
        first = next(p for p in doc.operational_bundle.phases if p.coordinate.lane_key == "runtime")
        doc = replace(doc, operational_bundle=replace(doc.operational_bundle, phases=(*doc.operational_bundle.phases,
            replace(first, coordinate=later.coordinate, title=later.title, intent=later.intent,
                ordinal=later.ordinal, gate=later.gate))))
    if fault in {"incoming", "outgoing"}:
        other = next(d for d in doc.definitions if d.coordinate != definition.coordinate)
        dependent, prerequisite = (definition, other) if fault == "incoming" else (other, definition)
        edge = GoalPhaseDependency(owner_goal_tag=GOAL, dependency_key="complete-incident-edge", dependent=dependent.coordinate,
            prerequisite=prerequisite.coordinate, relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE, required_gate_digest=prerequisite.gate.gate_digest, reason="Actual incident edge")
        doc = replace(doc, operational_bundle=replace(doc.operational_bundle, dependencies=(edge,)))
    if seed_journal is not None:
        seed = definition if seed_journal == "selected" else next(
            d for d in doc.definitions if d.coordinate != definition.coordinate)
        doc = replace(doc, operation_journal_profile="v1", phase_operation_journal=GoalPhaseOperationJournalV1(
            entries=(_journal_entry(doc, seed, label="seed-approval"),)))
    _bytes(root, CUSTOMER_PATH, attach_goal_phase_native_carrier(prefix, doc))
    scope = [*SOURCES, FOUNDATION_WORK_PATH, PROOF_PATH, *OUTPUTS]
    _issue(root, FOUNDATION_WORK_PATH, "codex-test", scope)
    _issue(root, REQUEST_ISSUE, "codex-test", [REQUEST_PATH, REQUEST_ISSUE])
    _issue(root, REVIEW_ISSUE, "codex-reviewer" if fault != "self-review" else "codex-test", [REVIEW_PATH, REVIEW_ISSUE])
    _issue(root, FOREIGN_ISSUE, "codex-test", SOURCES)
    if fault == "parent-status-repair":
        (root / FOUNDATION_WORK_PATH).write_text((root / FOUNDATION_WORK_PATH).read_text().replace("In Progress", "Closed"))
    if fault == "parent-owner-repair":
        (root / FOUNDATION_WORK_PATH).write_text((root / FOUNDATION_WORK_PATH).read_text().replace("codex-test", "codex-foreign"))
    if fault == "parent-scope-repair":
        (root / FOUNDATION_WORK_PATH).write_text((root / FOUNDATION_WORK_PATH).read_text().replace("- `runtime/b.py`\n", ""))
    _git(root, "add", CUSTOMER_PATH, FOUNDATION_WORK_PATH, REQUEST_ISSUE, REVIEW_ISSUE, FOREIGN_ISSUE)
    _git(root, "commit", "-qm", "Admit exact opt-in Gate and proof authorities")
    if fault == "pre-source-future-proof-blob-restore":
        original = (root / FOUNDATION_WORK_PATH).read_bytes()
        # The later authentic proof publication will append these exact bytes.
        _bytes(root, FOUNDATION_WORK_PATH, original + b"- Proof publication.\n")
        _git(root, "add", FOUNDATION_WORK_PATH)
        _git(root, "commit", "-qm", "Ungoverned early future-proof content")
        _bytes(root, FOUNDATION_WORK_PATH, original)
        _git(root, "add", FOUNDATION_WORK_PATH)
        _git(root, "commit", "-qm", "Restore Work Issue before implementation")
    parent = _git(root, "rev-parse", "HEAD")
    verifier = GitRuntimeChecksReviewAuthorityVerifier(resolver_capability=_native_capability(root, monkeypatch))
    impl_issue_path = FOREIGN_ISSUE if fault == "foreign-issue" else FOUNDATION_WORK_PATH
    impl_issue = verifier._source._issue(parent, impl_issue_path)
    _bytes(root, SOURCES[0], b"FIRST = 1\n")
    _bytes(root, SOURCES[1], b"SECOND = 2\n")
    changed = list(SOURCES)
    if fault is not None and fault.startswith("parent-"):
        _issue(root, FOUNDATION_WORK_PATH, "codex-test", scope)
        changed.append(FOUNDATION_WORK_PATH)
    implementation = _effect(root, impl_issue_path, changed)
    source_revision = implementation
    if fault == "pre-source-owner-restore":
        original = (root / FOUNDATION_WORK_PATH).read_bytes()
        _bytes(root, FOUNDATION_WORK_PATH, original.replace(b"codex-test", b"codex-foreign"))
        _git(root, "add", FOUNDATION_WORK_PATH)
        _git(root, "commit", "-qm", "Foreign selected Work owner")
        _bytes(root, FOUNDATION_WORK_PATH, original)
        _git(root, "add", FOUNDATION_WORK_PATH)
        _git(root, "commit", "-qm", "Restore selected Work owner")
        source_revision = _git(root, "rev-parse", "HEAD")
    work = next(p.work_associations[0] for p in doc.operational_bundle.phases if p.coordinate == definition.coordinate)
    impl = {"repository_revision_ref": implementation, "repository_parent_ref": parent,
        "repository_commit_receipt_ref": "repository-commit:" + implementation,
        "selected_work_binding": {"coordinate": endpoints_coord(definition.coordinate), "association_ref": work.association_ref,
            "receipt_ref": work.receipt_ref, "issue_ref": work.issue_ref, "role": "implementation", "disposition": "current"},
        "governing_issue_path": impl_issue_path, "governing_issue_tag": impl_issue["tag"],
        "governing_issue_blob_ref": impl_issue["blob_oid"], "owner_execution_id": "codex-test", "status": "in_progress",
        "scope": scope if fault == "parent-scope-repair" else list(impl_issue["scope"]),
        "scope_digest": digest({"ownership_scope": scope}) if fault == "parent-scope-repair" else impl_issue["scope_digest"],
        "changed_paths": sorted(changed), "changed_paths_ref": "goal-runtime-checks-changed-paths:" + digest(sorted(changed))}
    inventory = [_file(verifier._source._root, source_revision, name) for name in sorted(changed if fault != "omit-path" else changed[:1])]
    if fault == "source-blob-substitution":
        inventory[0]["blob_ref"] = "a" * 40
    source_ref = "goal-runtime-checks-source-scope:" + digest(inventory)
    request = make_runtime_checks_artifact(REQUEST, {"goal_path": CUSTOMER_PATH, "goal_tag": GOAL,
        "coordinate": endpoints_coord(definition.coordinate), "source_document_ref": doc.document_ref,
        "source_revision_ref": source_revision, "definition_ref": definition.definition_ref, "gate_digest": gate.gate_digest,
        "evaluator_profile": PROFILE, "implementation_publication": impl, "source_scope": inventory,
        "source_scope_ref": source_ref, "incoming_declarations": [], "requested_by_execution_id": "codex-test", "issued_at": "2026-10-01T12:00:00Z"})
    request_pub = _binding(verifier, root, request, REQUEST_PATH, REQUEST_ISSUE, [REQUEST_PATH, REQUEST_ISSUE])
    checks = []
    for key, output_path in zip(("package-tests", "runtime-canary", "static-checks"), OUTPUTS):
        _bytes(root, output_path, b"Verified output\n")
        record = {"key": key, "source_scope_ref": source_ref, "command_argv": ["proof-command", "exact argument with spaces"],
            "output": {"path": output_path, "blob_ref": _git(root, "hash-object", output_path),
                "sha256": "sha256:" + hashlib.sha256((root / output_path).read_bytes()).hexdigest()}, "exit_code": 0}
        record.update({"passed_count": 4, "failed_count": 0, "skipped_count": 0} if key == "package-tests" else
            {"error_count": 0, "warning_count": 0} if key == "static-checks" else {"result": "passed"})
        if check_fault is not None and check_fault[0] == key:
            record[check_fault[1]] = check_fault[2]
        checks.append(record)
    proof = make_runtime_checks_artifact(PROOF, {"request_ref": request.to_wire()["request_ref"],
        "request_publication_ref": request_pub.to_wire()["publication_ref"], "coordinate": endpoints_coord(definition.coordinate),
        "definition_ref": definition.definition_ref, "gate_digest": gate.gate_digest, "evaluator_profile": PROFILE,
        "source_scope_ref": source_ref, "publisher_execution_id": "codex-test", "checks": checks, "issued_at": "2026-10-01T12:01:00Z"})
    if fault == "inherited-output":
        _effect(root, FOUNDATION_WORK_PATH, OUTPUTS)
    proof_effect = [PROOF_PATH, FOUNDATION_WORK_PATH, *OUTPUTS] if fault != "inherited-output" else [PROOF_PATH, FOUNDATION_WORK_PATH]
    proof_pub = _binding(verifier, root, proof, PROOF_PATH, FOUNDATION_WORK_PATH, proof_effect)
    review = make_runtime_checks_artifact(REVIEW, {"request_ref": request.to_wire()["request_ref"],
        "request_publication_ref": request_pub.to_wire()["publication_ref"], "proof_ref": proof.to_wire()["proof_ref"],
        "proof_publication_ref": proof_pub.to_wire()["publication_ref"], "coordinate": endpoints_coord(definition.coordinate),
        "definition_ref": definition.definition_ref, "gate_digest": gate.gate_digest, "evaluator_profile": PROFILE,
        "source_scope_ref": source_ref, "reviewed_changed_paths_ref": impl["changed_paths_ref"] if fault != "wrong-reviewed-paths" else "goal-runtime-checks-changed-paths:" + digest(SOURCES[:1]),
        "reviewer_execution_id": "codex-test" if fault == "self-review" else "codex-foreign" if fault == "foreign-reviewer" else "codex-reviewer",
        "verdict": verdict, "issued_at": "2026-10-01T12:02:00Z"})
    review_pub = _binding(verifier, root, review, REVIEW_PATH, REVIEW_ISSUE, [REVIEW_PATH, REVIEW_ISSUE])
    return root, verifier, {"request_publication": request_pub, "proof_publication": proof_pub, "review_publication": review_pub}


def test_real_provider_satisfied_and_exact_decode_without_source_effect(tmp_path, monkeypatch):
    root, verifier, claims = _proof_chain(tmp_path, monkeypatch)
    head = _git(root, "rev-parse", "HEAD")
    status = _git(root, "status", "--porcelain")
    qualified = verifier.verify(**claims)
    result = evaluate_runtime_checks_review_v2(qualified)
    wire = result.to_wire()
    assert wire["result"] == "satisfied" and wire["reasons"] == []
    assert wire["gate_observation"]["source_revision_refs"] == [head]
    assert wire["source_verification"]["original_source_revision_ref"] != head
    assert len(wire["authority_publications"]) == 3
    assert decode_runtime_checks_evaluation(wire, qualified=qualified).to_wire() == result.to_wire()
    assert require_runtime_checks_evaluation(result) is result
    assert _git(root, "rev-parse", "HEAD") == head and _git(root, "status", "--porcelain") == status


@pytest.mark.parametrize("fault,reason", [("foreign-issue", "implementation_work_issue_mismatch"),
    ("parent-status-repair", "parent_authority"), ("parent-owner-repair", "parent_authority"),
    ("parent-scope-repair", "parent_authority"), ("self-review", "not_independent"),
    ("incoming", "dependency_profile_unsupported"), ("omit-path", "implementation_path_omitted"),
    ("pre-source-owner-restore", "issue_history_unqualified"), ("foreign-reviewer", "not_independent"),
    ("wrong-reviewed-paths", "cross_role_mismatch"), ("source-blob-substitution", "source_scope_binding"),
    ("inherited-output", "publication_effect")])
def test_authentic_but_foreign_or_incomplete_authority_refuses_before_evaluation(tmp_path, monkeypatch, fault, reason):
    _, verifier, claims = _proof_chain(tmp_path, monkeypatch, fault=fault)
    with pytest.raises(ValueError, match=reason):
        verifier.verify(**claims)


@pytest.mark.parametrize("verdict,check_fault,result,reason", [
    ("rejected", None, "rejected", "independent_review_rejected"),
    ("unavailable", None, "unavailable", "independent_review_unavailable"),
    ("accepted", ("package-tests", "failed_count", 1), "rejected", "package_tests_failed"),
    ("accepted", ("package-tests", "skipped_count", 1), "unavailable", "package_tests_incomplete"),
    ("accepted", ("static-checks", "warning_count", 1), "rejected", "static_checks_failed"),
    ("accepted", ("runtime-canary", "result", "unavailable"), "unavailable", "runtime_canary_unavailable"),
])
def test_real_provider_negative_reviews_and_checks_are_evaluable(tmp_path, monkeypatch, verdict, check_fault, result, reason):
    _, verifier, claims = _proof_chain(tmp_path, monkeypatch, verdict=verdict, check_fault=check_fault)
    wire = evaluate_runtime_checks_review_v2(verifier.verify(**claims)).to_wire()
    assert wire["result"] == result and reason in wire["reasons"]


@pytest.mark.parametrize("name,reason", [(SOURCES[0], "source_scope_stale"), (SOURCES[1], "source_scope_stale"),
    (OUTPUTS[2], "proof_publication_stale"), (REVIEW_ISSUE, "independent_review_stale"), (FOUNDATION_WORK_PATH, "proof_publication_stale")])
def test_later_protected_touch_and_restore_remain_stale(tmp_path, monkeypatch, name, reason):
    root, verifier, claims = _proof_chain(tmp_path, monkeypatch)
    original = (root / name).read_bytes()
    _bytes(root, name, original + b"\nLater change\n")
    _git(root, "add", name)
    _git(root, "commit", "-qm", "Protected path evolves")
    _bytes(root, name, original)
    _git(root, "add", name)
    _git(root, "commit", "-qm", "Identical restore")
    wire = evaluate_runtime_checks_review_v2(verifier.verify(**claims)).to_wire()
    assert wire["result"] == "stale" and reason in wire["reasons"]
    assert wire["source_verification"]["scope_currentness"] == "stale"


def test_actual_witness_mutation_copy_transport_and_lifetime(tmp_path, monkeypatch):
    _, verifier, claims = _proof_chain(tmp_path, monkeypatch)
    gc.collect()
    before = len(_ISSUED)
    qualified = verifier.verify(**claims)
    wire = evaluate_runtime_checks_review_v2(qualified).to_wire()
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        evaluate_runtime_checks_review_v2(copy(qualified))
    clone = RuntimeChecksVerifiedInputV2(qualified.canonical_body, qualified.source_evidence)
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        evaluate_runtime_checks_review_v2(clone)
    forged = deepcopy(wire)
    forged["result"] = "rejected"
    forged["evaluation_ref"] = "goal-runtime-checks-evaluation:" + digest({k: v for k, v in forged.items() if k != "evaluation_ref"})
    with pytest.raises(ValueError, match="differs_from_authority"):
        decode_runtime_checks_evaluation(forged, qualified=qualified)
    value = qualified.to_wire()
    value["proof"]["checks"][0]["failed_count"] = 1
    object.__setattr__(qualified, "canonical_body", canonical_json(value))
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        evaluate_runtime_checks_review_v2(qualified)
    del clone, qualified
    gc.collect()
    assert len(_ISSUED) == before


def test_issued_evaluation_mutation_reconstruction_and_lifetime(tmp_path, monkeypatch):
    _, verifier, claims = _proof_chain(tmp_path, monkeypatch)
    gc.collect()
    before = len(_EVALUATIONS)
    result = evaluate_runtime_checks_review_v2(verifier.verify(**claims))
    clone = RuntimeChecksEvaluationV2(result.canonical_body)
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        require_runtime_checks_evaluation(clone)
    value = result.to_wire()
    value["result"] = "rejected"
    value["evaluation_ref"] = "goal-runtime-checks-evaluation:" + digest({k: v for k, v in value.items() if k != "evaluation_ref"})
    object.__setattr__(result, "canonical_body", canonical_json(value))
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        require_runtime_checks_evaluation(result)
    del result, clone
    gc.collect()
    assert len(_EVALUATIONS) == before


def test_terminal_io_head_advance_issues_no_witness(tmp_path, monkeypatch):
    root, verifier, claims = _proof_chain(tmp_path, monkeypatch)
    original = verifier._target
    count = 0
    def racing(name):
        nonlocal count
        original(name)
        if name == SOURCES[1]:
            count += 1
        if name == SOURCES[1] and count == 2:  # This is the terminal recheck, not initial I/O.
            _bytes(root, "unrelated.txt", b"Concurrent epoch\n")
            _git(root, "add", "unrelated.txt")
            _git(root, "commit", "-qm", "HEAD advances during target verification")
    monkeypatch.setattr(verifier, "_target", racing)
    before = len(_ISSUED)
    with pytest.raises(ValueError, match="repository_head_advanced"):
        verifier.verify(**claims)
    assert len(_ISSUED) == before


@pytest.mark.parametrize("name", [PROOF_PATH, OUTPUTS[0], SOURCES[1]])
def test_leaf_symlink_never_issues_verified_authority(tmp_path, monkeypatch, name):
    root, verifier, claims = _proof_chain(tmp_path, monkeypatch)
    outside = tmp_path / "outside.txt"
    outside.write_bytes((root / name).read_bytes())
    (root / name).unlink()
    (root / name).symlink_to(outside)
    with pytest.raises(ValueError, match="target_unresolvable"):
        verifier.verify(**claims)


def test_unrelated_head_advance_requires_fresh_source_verification(tmp_path, monkeypatch):
    root, verifier, claims = _proof_chain(tmp_path, monkeypatch)
    initial = evaluate_runtime_checks_review_v2(verifier.verify(**claims)).to_wire()
    _bytes(root, "unrelated.txt", b"Independent lane work\n")
    _git(root, "add", "unrelated.txt")
    _git(root, "commit", "-qm", "Unrelated HEAD advancement")
    fresh = evaluate_runtime_checks_review_v2(verifier.verify(**claims)).to_wire()
    assert fresh["result"] == "satisfied"
    assert initial["currentness_ref"] != fresh["currentness_ref"]
    assert initial["source_verification"]["original_source_revision_ref"] == fresh["source_verification"]["original_source_revision_ref"]
    assert fresh["gate_observation"]["source_revision_refs"] == [_git(root, "rev-parse", "HEAD")]


def test_later_same_lane_change_and_restore_refuses_not_relabels(tmp_path, monkeypatch):
    root, verifier, claims = _proof_chain(tmp_path, monkeypatch)
    original = (root / CUSTOMER_PATH).read_bytes()
    prefix, doc = extract_goal_phase_native_carrier(original)
    lane = replace(doc.native_lane_authorities[0], role="Different authority")
    _bytes(root, CUSTOMER_PATH, attach_goal_phase_native_carrier(prefix, replace(doc, native_lane_authorities=(lane,))))
    _git(root, "add", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Relevant semantic delta")
    _bytes(root, CUSTOMER_PATH, original)
    _git(root, "add", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Identical restore does not erase semantic history")
    with pytest.raises(ValueError, match="semantic_scope_changed"):
        verifier.verify(**claims)


def test_inherited_artifact_receipt_commit_relabel_refuses(tmp_path, monkeypatch):
    root, verifier, claims = _proof_chain(tmp_path, monkeypatch)
    _bytes(root, "unrelated.txt", b"Receipt relabel\n")
    _git(root, "add", "unrelated.txt")
    _git(root, "commit", "-qm", "Not an artifact publication")
    commit = _git(root, "rev-parse", "HEAD")
    claim = claims["review_publication"].to_wire()
    issue = verifier._source._issue(_git(root, "rev-parse", "HEAD^"), REVIEW_ISSUE)
    claim.update(repository_revision_ref=commit, repository_commit_receipt_ref="repository-commit:" + commit,
        governing_issue_blob_ref=issue["blob_oid"])
    claims["review_publication"] = make_runtime_checks_artifact(PUBLICATION, {k: v for k, v in claim.items() if k not in {"schema_id", "publication_ref"}})
    with pytest.raises(ValueError, match="publication_effect"):
        verifier.verify(**claims)


def test_parent_symlink_and_terminal_replacement_refuse(tmp_path, monkeypatch):
    root, verifier, claims = _proof_chain(tmp_path, monkeypatch)
    outside = tmp_path / "external-proof"
    (root / "proof").rename(outside)
    (root / "proof").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="target_unresolvable"):
        verifier.verify(**claims)


def test_terminal_leaf_replacement_after_initial_resolution_refuses(tmp_path, monkeypatch):
    root, verifier, claims = _proof_chain(tmp_path, monkeypatch)
    original = verifier._target
    count = 0
    outside = tmp_path / "external-source.py"
    outside.write_bytes((root / SOURCES[1]).read_bytes())
    def racing(name):
        nonlocal count
        if name == SOURCES[1]:
            count += 1
            if count == 2:
                (root / name).unlink()
                (root / name).symlink_to(outside)
        original(name)
    monkeypatch.setattr(verifier, "_target", racing)
    before = len(_ISSUED)
    with pytest.raises(ValueError, match="target_unresolvable"):
        verifier.verify(**claims)
    assert len(_ISSUED) == before


def test_real_rejected_stale_unavailable_precedence_preserves_all_reasons(tmp_path, monkeypatch):
    root, verifier, claims = _proof_chain(tmp_path, monkeypatch, verdict="unavailable", check_fault=("package-tests", "failed_count", 1))
    _bytes(root, SOURCES[1], b"SECOND = 3\n")
    _git(root, "add", SOURCES[1])
    _git(root, "commit", "-qm", "Qualified proof becomes stale")
    wire = evaluate_runtime_checks_review_v2(verifier.verify(**claims)).to_wire()
    assert wire["result"] == "rejected"
    assert wire["reasons"] == ["independent_review_unavailable", "package_tests_failed", "source_scope_stale"]


def test_proof_issue_closeout_is_stale_not_an_exempt_transition(tmp_path, monkeypatch):
    root, verifier, claims = _proof_chain(tmp_path, monkeypatch)
    target = root / FOUNDATION_WORK_PATH
    target.write_text(target.read_text().replace("In Progress", "Closed"))
    _git(root, "add", FOUNDATION_WORK_PATH)
    _git(root, "commit", "-qm", "Proof Issue closeout")
    wire = evaluate_runtime_checks_review_v2(verifier.verify(**claims)).to_wire()
    assert wire["result"] == "stale" and "proof_publication_stale" in wire["reasons"]


def test_outgoing_incident_legacy_lane_authority_is_not_elided(tmp_path, monkeypatch):
    root, verifier, claims = _proof_chain(tmp_path, monkeypatch, fault="outgoing")
    assert evaluate_runtime_checks_review_v2(verifier.verify(**claims)).to_wire()["result"] == "satisfied"
    prefix, doc = extract_goal_phase_native_carrier((root / CUSTOMER_PATH).read_bytes())
    changed = prefix.replace(b"| Runtime |", b"| Changed runtime |")
    assert changed != prefix
    doc = replace(doc, compatibility_projection_sha256="sha256:" + hashlib.sha256(changed).hexdigest(),
        compatibility_projection_byte_count=len(changed))
    _bytes(root, CUSTOMER_PATH, attach_goal_phase_native_carrier(changed, doc))
    _git(root, "add", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Change incident containing-lane authority")
    with pytest.raises(ValueError, match="semantic_scope_changed"):
        verifier.verify(**claims)


def _commit_journal_entry(root, *, lane_key, decision, phase_key=None):
    prefix, doc = extract_goal_phase_native_carrier((root / CUSTOMER_PATH).read_bytes())
    definition = next(d for d in doc.definitions if d.coordinate.lane_key == lane_key
        and (phase_key is None or d.coordinate.phase_key == phase_key))
    entries = () if doc.phase_operation_journal is None else doc.phase_operation_journal.entries
    approval = next((e for e in reversed(entries) if e.coordinate == definition.coordinate
        and e.decision == "approve"), None) if decision == "revoke" else None
    if decision == "revoke":
        assert approval is not None
    entry = _journal_entry(doc, definition, label="later-" + decision, approval=approval)
    successor = replace(doc, operation_journal_profile="v1",
        phase_operation_journal=GoalPhaseOperationJournalV1(entries=(*entries, entry)))
    _bytes(root, CUSTOMER_PATH, attach_goal_phase_native_carrier(prefix, successor))
    _git(root, "add", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Publish fixture journal " + decision)
    return doc, successor


@pytest.mark.parametrize("decision", ["approve", "revoke"])
def test_same_phase_journal_change_refuses_before_fresh_gate_observation(tmp_path, monkeypatch, decision):
    root, verifier, claims = _proof_chain(tmp_path, monkeypatch,
        seed_journal="selected" if decision == "revoke" else "unrelated")
    assert evaluate_runtime_checks_review_v2(verifier.verify(**claims)).to_wire()["result"] == "satisfied"
    _commit_journal_entry(root, lane_key="foundation", decision=decision)
    before = len(_ISSUED)
    with pytest.raises(ValueError, match="semantic_scope_changed"):
        verifier.verify(**claims)
    assert len(_ISSUED) == before


@pytest.mark.parametrize("incident", [False, True])
def test_scoped_journal_change_and_identical_restore_refuses(tmp_path, monkeypatch, incident):
    root, verifier, claims = _proof_chain(tmp_path, monkeypatch,
        fault="outgoing" if incident else None, seed_journal="selected" if incident else "unrelated")
    original = (root / CUSTOMER_PATH).read_bytes()
    _commit_journal_entry(root, lane_key="runtime" if incident else "foundation", decision="approve")
    _bytes(root, CUSTOMER_PATH, original)
    _git(root, "add", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Restore identical preapproval carrier")
    assert (root / CUSTOMER_PATH).read_bytes() == original
    with pytest.raises(ValueError, match="semantic_scope_changed"):
        verifier.verify(**claims)


@pytest.mark.parametrize("decision", ["approve", "revoke"])
def test_incident_endpoint_journal_change_refuses(tmp_path, monkeypatch, decision):
    root, verifier, claims = _proof_chain(tmp_path, monkeypatch, fault="outgoing",
        seed_journal="unrelated" if decision == "revoke" else "selected")
    assert evaluate_runtime_checks_review_v2(verifier.verify(**claims)).to_wire()["result"] == "satisfied"
    _, doc = extract_goal_phase_native_carrier((root / CUSTOMER_PATH).read_bytes())
    endpoint = doc.operational_bundle.dependencies[0].dependent
    _commit_journal_entry(root, lane_key=endpoint.lane_key, phase_key=endpoint.phase_key, decision=decision)
    with pytest.raises(ValueError, match="semantic_scope_changed"):
        verifier.verify(**claims)


@pytest.mark.parametrize("incident", [False, True])
def test_unrelated_journal_append_preserves_scope_and_fresh_observation(tmp_path, monkeypatch, incident):
    root, verifier, claims = _proof_chain(tmp_path, monkeypatch,
        fault="outgoing" if incident else None, seed_journal="selected", extra_operational_phase=incident)
    prior = evaluate_runtime_checks_review_v2(verifier.verify(**claims)).to_wire()
    _, document = extract_goal_phase_native_carrier((root / CUSTOMER_PATH).read_bytes())
    endpoint = document.operational_bundle.dependencies[0].dependent if incident else None
    unrelated = next(d.coordinate for d in document.definitions if d.coordinate.lane_key == "runtime"
        and d.coordinate != endpoint)
    before, after = _commit_journal_entry(root, lane_key="runtime", phase_key=unrelated.phase_key, decision="approve")
    assert before.phase_operation_journal.journal_ref != after.phase_operation_journal.journal_ref
    wire = evaluate_runtime_checks_review_v2(verifier.verify(**claims)).to_wire()
    assert wire["result"] == "satisfied" and wire["reasons"] == []
    assert wire["gate_observation"]["source_revision_refs"] == [_git(root, "rev-parse", "HEAD")]
    assert wire["gate_observation"]["source_revision_refs"] != prior["gate_observation"]["source_revision_refs"]


def test_journal_profile_introduction_is_not_an_unrelated_entry_only_change(tmp_path, monkeypatch):
    root, verifier, claims = _proof_chain(tmp_path, monkeypatch)
    before, after = _commit_journal_entry(root, lane_key="runtime", decision="approve")
    assert before.operation_journal_profile == "none" and after.operation_journal_profile == "v1"
    with pytest.raises(ValueError, match="semantic_scope_changed"):
        verifier.verify(**claims)


@pytest.mark.parametrize("verdict,check_fault,touch,expected", [
    ("accepted", None, False, "satisfied"),
    ("rejected", None, False, "rejected"),
    ("unavailable", None, False, "unavailable"),
    ("accepted", ("runtime-canary", "result", "unavailable"), False, "unavailable"),
    ("accepted", None, True, "stale"),
    ("rejected", None, True, "rejected"),
])
def test_evaluator_snapshot_preserves_complete_issued_result(tmp_path, monkeypatch, verdict, check_fault, touch, expected):
    root, _, claims = _proof_chain(tmp_path, monkeypatch, verdict=verdict, check_fault=check_fault)
    if touch:
        _bytes(root, SOURCES[1], b"SECOND = 3\n")
        _git(root, "add", SOURCES[1])
        _git(root, "commit", "-qm", "Later source path becomes stale")
    head, status = _git(root, "rev-parse", "HEAD"), _git(root, "status", "--porcelain")
    provider = GitNativeLaneEvidenceVerifier(resolver_capability=_native_capability(root, monkeypatch))
    snapshot = require_qualified_native_lane_evidence(provider.qualify_runtime_checks(**claims))
    _, document = extract_goal_phase_native_carrier((root / CUSTOMER_PATH).read_bytes())
    assert require_native_lane_evidence_for_document(snapshot, document=document, lane_key="foundation") is snapshot
    record = snapshot.gate_observations[0].to_wire()
    assert set(record) == {"coordinate", "evaluator_profile", "evaluation", "gate_observation"}
    assert record["evaluation"]["result"] == expected
    assert record["gate_observation"] == record["evaluation"]["gate_observation"]
    assert record["gate_observation"]["outcome"] == ("unresolved" if expected == "unavailable" else expected)
    assert record["gate_observation"]["source_revision_refs"] == [head]
    assert snapshot.gate_observations[0].evaluator_input.to_wire()["request"]["source_revision_ref"] != head
    assert snapshot.authority_inventory[0]["authority"] == snapshot.gate_observations[0].evaluator_input.to_wire()
    assert decode_goal_native_lane_evidence_snapshot(snapshot.to_wire(), qualified=snapshot) is snapshot
    assert _git(root, "rev-parse", "HEAD") == head and _git(root, "status", "--porcelain") == status


@pytest.mark.parametrize("mutation", ["clone", "input", "output", "record", "inventory", "epoch"])
def test_actually_issued_gate_snapshot_mutation_refuses(tmp_path, monkeypatch, mutation):
    root, _, claims = _proof_chain(tmp_path, monkeypatch)
    provider = GitNativeLaneEvidenceVerifier(resolver_capability=_native_capability(root, monkeypatch))
    snapshot = provider.qualify_runtime_checks(**claims)
    gate = snapshot.gate_observations[0]
    if mutation == "clone":
        snapshot = replace(snapshot)
    elif mutation in {"input", "output"}:
        value = gate.evaluator_input if mutation == "input" else gate.evaluation
        body = value.to_wire()
        body["evaluated_at"] = "2026-10-01T12:04:00Z"
        object.__setattr__(value, "canonical_body", canonical_json(body))
    elif mutation == "record":
        object.__setattr__(snapshot, "gate_observations", ({"outcome": "satisfied"},))
    elif mutation == "inventory":
        snapshot.authority_inventory[0]["authority"]["request"]["implementation_publication"]["owner_execution_id"] = "codex-foreign"
    else:
        object.__setattr__(snapshot, "source_revision_ref", "a" * 40)
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        require_qualified_native_lane_evidence(snapshot)


def test_two_valid_evaluator_graphs_cannot_be_cross_paired(tmp_path, monkeypatch):
    root, _, claims = _proof_chain(tmp_path, monkeypatch)
    provider = GitNativeLaneEvidenceVerifier(resolver_capability=_native_capability(root, monkeypatch))
    first = provider.qualify_runtime_checks(**claims)
    _bytes(root, SOURCES[1], b"SECOND = 3\n")
    _git(root, "add", SOURCES[1])
    _git(root, "commit", "-qm", "Advance second source")
    second = provider.qualify_runtime_checks(**claims)
    with pytest.raises(ValueError, match="differs_from_authority"):
        GoalNativeLaneQualifiedGateV2(first.gate_observations[0].evaluator_input, second.gate_observations[0].evaluation)


def test_gate_snapshot_transport_redigestion_and_old_epoch_refuse(tmp_path, monkeypatch):
    root, _, claims = _proof_chain(tmp_path, monkeypatch)
    provider = GitNativeLaneEvidenceVerifier(resolver_capability=_native_capability(root, monkeypatch))
    old = provider.qualify_runtime_checks(**claims)
    wire = deepcopy(old.to_wire())
    wire["gate_observations"][0]["gate_observation"]["outcome"] = "rejected"
    wire["snapshot_ref"] = "goal-native-lane-evidence:" + digest({k: v for k, v in wire.items() if k != "snapshot_ref"})
    with pytest.raises(ValueError, match="transport_differs"):
        decode_goal_native_lane_evidence_snapshot(wire, qualified=old)
    _bytes(root, "unrelated.txt", b"Unrelated epoch advance\n")
    _git(root, "add", "unrelated.txt")
    _git(root, "commit", "-qm", "Unrelated fresh epoch")
    fresh = provider.qualify_runtime_checks(**claims)
    assert fresh.gate_observations[0].evaluation.to_wire()["result"] == "satisfied"
    assert fresh.gate_observations[0].evaluator_input.to_wire()["request"] == old.gate_observations[0].evaluator_input.to_wire()["request"]
    with pytest.raises(ValueError, match="transport_differs"):
        decode_goal_native_lane_evidence_snapshot(old.to_wire(), qualified=fresh)


@pytest.mark.parametrize("fault,reason", [("foreign-issue", "implementation_work_issue_mismatch"),
    ("incoming", "dependency_profile_unsupported"), ("foreign-reviewer", "reviewer_not_independent")])
def test_gate_snapshot_entrance_reverifies_publication_authority(tmp_path, monkeypatch, fault, reason):
    root, _, claims = _proof_chain(tmp_path, monkeypatch, fault=fault)
    provider = GitNativeLaneEvidenceVerifier(resolver_capability=_native_capability(root, monkeypatch))
    before = len(_SNAPSHOT_ISSUED)
    with pytest.raises(ValueError, match=reason):
        provider.qualify_runtime_checks(**claims)
    assert len(_SNAPSHOT_ISSUED) == before


def test_gate_snapshot_terminal_head_check_follows_all_new_join_io(tmp_path, monkeypatch):
    from aware_goal_native_fs_adapter import native_lane_evidence as module
    root, _, claims = _proof_chain(tmp_path, monkeypatch)
    provider = GitNativeLaneEvidenceVerifier(resolver_capability=_native_capability(root, monkeypatch))
    evaluating = False
    evaluate = module.evaluate_runtime_checks_review_v2
    target = provider._checks._target
    def mark(value):
        nonlocal evaluating
        result = evaluate(value)
        evaluating = True
        return result
    def advance(path):
        nonlocal evaluating
        result = target(path)
        if evaluating:
            evaluating = False
            _bytes(root, SOURCES[1], b"SECOND = 4\n")
            _git(root, "add", SOURCES[1])
            _git(root, "commit", "-qm", "Concurrent commit at final intake target check")
        return result
    monkeypatch.setattr(module, "evaluate_runtime_checks_review_v2", mark)
    monkeypatch.setattr(provider._checks, "_target", advance)
    before = len(_SNAPSHOT_ISSUED)
    with pytest.raises(ValueError, match="repository_head_advanced"):
        provider.qualify_runtime_checks(**claims)
    assert len(_SNAPSHOT_ISSUED) == before


def test_gate_snapshot_terminal_target_replacement_refuses(tmp_path, monkeypatch):
    from aware_goal_native_fs_adapter import native_lane_evidence as module
    root, _, claims = _proof_chain(tmp_path, monkeypatch)
    provider = GitNativeLaneEvidenceVerifier(resolver_capability=_native_capability(root, monkeypatch))
    replacing = False
    evaluate = module.evaluate_runtime_checks_review_v2
    target = provider._checks._target
    outside = tmp_path / "foreign-output.txt"
    outside.write_bytes(b"Unrelated external file\n")
    def mark(value):
        nonlocal replacing
        result = evaluate(value)
        replacing = True
        return result
    def replace_target(path):
        if replacing and path == OUTPUTS[0]:
            local = root / path
            local.rename(root / "retained-original-output.txt")
            local.symlink_to(outside)
        return target(path)
    monkeypatch.setattr(module, "evaluate_runtime_checks_review_v2", mark)
    monkeypatch.setattr(provider._checks, "_target", replace_target)
    before = len(_SNAPSHOT_ISSUED)
    with pytest.raises(ValueError, match="unsafe|unresolvable"):
        provider.qualify_runtime_checks(**claims)
    assert len(_SNAPSHOT_ISSUED) == before
    assert outside.read_bytes() == b"Unrelated external file\n"


def test_gate_snapshot_claims_cannot_substitute_forged_publication_or_constructed_result(tmp_path, monkeypatch):
    root, _, claims = _proof_chain(tmp_path, monkeypatch)
    provider = GitNativeLaneEvidenceVerifier(resolver_capability=_native_capability(root, monkeypatch))
    valid = provider.qualify_runtime_checks(**claims)
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        GoalNativeLaneQualifiedGateV2(valid.gate_observations[0].evaluator_input,
            RuntimeChecksEvaluationV2(valid.gate_observations[0].evaluation.canonical_body))
    body = claims["proof_publication"].to_wire()
    forged = make_runtime_checks_artifact(PUBLICATION,
        {k: ("a" * 40 if k == "artifact_blob_ref" else v) for k, v in body.items() if k not in {"schema_id", "publication_ref"}})
    before = len(_SNAPSHOT_ISSUED)
    with pytest.raises(ValueError):
        provider.qualify_runtime_checks(**{**claims, "proof_publication": forged})
    assert len(_SNAPSHOT_ISSUED) == before
    with pytest.raises(TypeError):
        provider.qualify_runtime_checks(evaluation=valid.gate_observations[0].evaluation)


def test_gate_snapshot_registry_has_output_lifetime(tmp_path, monkeypatch):
    root, _, claims = _proof_chain(tmp_path, monkeypatch)
    provider = GitNativeLaneEvidenceVerifier(resolver_capability=_native_capability(root, monkeypatch))
    gc.collect()
    before = len(_SNAPSHOT_ISSUED)
    snapshot = provider.qualify_runtime_checks(**claims)
    assert len(_SNAPSHOT_ISSUED) == before + 1
    del snapshot
    gc.collect()
    assert len(_SNAPSHOT_ISSUED) == before


def _direction_chain(tmp_path, monkeypatch, **kwargs):
    from aware_goal_native_fs_adapter.native_lane_authority import NativeGitLaneAuthorityVerifier
    receipts = []
    root, _, claims = _proof_chain(tmp_path, monkeypatch, publication_holder=receipts, **kwargs)
    provider = NativeGitLaneAuthorityVerifier(resolver_capability=_native_capability(root, monkeypatch))
    return root, provider, receipts[0], claims


def _eligibility(direction, phase_key):
    from aware_goal_operational_runtime import observe_goal_phase_eligibility_v2
    definition = next(d for d in direction.document.definitions if d.coordinate.lane_key == "foundation" and d.coordinate.phase_key == phase_key)
    return observe_goal_phase_eligibility_v2(document=direction.document, coordinate=definition.coordinate,
        expected_gate_digest=definition.gate.gate_digest, global_authority=direction.global_authority,
        lane_authority=direction, source_revision_ref=direction.global_authority.source_revision_ref)


def test_gate_direction_composition_preserves_carrier_and_lifecycle(tmp_path, monkeypatch):
    root, provider, receipt, claims = _direction_chain(tmp_path, monkeypatch)
    before = (root / CUSTOMER_PATH).read_bytes()
    head = _git(root, "rev-parse", "HEAD")
    status = _git(root, "status", "--porcelain")
    direction = provider.qualify_runtime_checks_direction(receipt, **claims)
    assert direction.evidence_snapshot.gate_observations[0].evaluation.to_wire()["result"] == "satisfied"
    selected = next(p for p in direction.document.operational_bundle.phases if p.coordinate.lane_key == "foundation")
    assert selected.state.value == "active" and selected.gate_observations == ()
    assert _eligibility(direction, selected.coordinate.phase_key).decision.eligibility == "eligible"
    assert (root / CUSTOMER_PATH).read_bytes() == before and _git(root, "rev-parse", "HEAD") == head
    assert _git(root, "status", "--porcelain") == status


@pytest.mark.parametrize("verdict,touch", [("accepted", False), ("rejected", False),
    ("unavailable", False), ("accepted", True)])
def test_portable_v2_gate_intake_preserves_issued_decision_and_negative_results(tmp_path, monkeypatch, verdict, touch):
    from test_native_lane_authority import _operation_request_v2
    from aware_goal_native_fs_adapter.phase_operation import NativeGitGoalPhaseOperationProvider
    from aware_goal_sdk.phase_operation import GoalPhaseOperationClient
    import aware_goal_native_fs_adapter.phase_operation as operation_module
    root, provider, receipt, claims = _direction_chain(tmp_path, monkeypatch,
        verdict=verdict, consumer_relation=GoalDependencyRelation.REQUIRES_COMPLETION)
    if touch:
        (root / "runtime/b.py").write_text("# Later implementation advance\n")
        _git(root, "add", "runtime/b.py")
        _git(root, "commit", "-qm", "Advance a protected runtime path")
    request = _operation_request_v2(root, receipt, claims=claims, phase_key="consumer")
    # Capture the real reducer output after concrete verification. Separate
    # verifier calls legitimately have distinct evaluation-time authority refs.
    canonical = []
    reducer = operation_module.observe_goal_phase_eligibility_v2
    def record(**inputs):
        result = reducer(**inputs)
        canonical.append(result.to_wire())
        return result
    monkeypatch.setattr(operation_module, "observe_goal_phase_eligibility_v2", record)
    before = (_git(root, "rev-parse", "HEAD"), _git(root, "write-tree"), _git(root, "status", "--porcelain"))
    actual = GoalPhaseOperationClient(NativeGitGoalPhaseOperationProvider(_native_capability(root, monkeypatch))).observe_eligibility_v2(request)
    direction = provider.qualify_runtime_checks_direction(receipt, **claims)
    assert actual["decision"] == canonical[0]
    assert actual["decision"]["dependency_gate"] == _eligibility(direction, "consumer").to_wire()["dependency_gate"]
    assert actual["decision"]["eligibility"] == ("eligible" if verdict == "accepted" and not touch else "held")
    assert (_git(root, "rev-parse", "HEAD"), _git(root, "write-tree"), _git(root, "status", "--porcelain")) == before


@pytest.mark.parametrize("fault", ["foreign-issue", "parent-status-repair", "self-review", "wrong-reviewed-paths", "inherited-output"])
def test_portable_v2_gate_locator_does_not_bypass_concrete_authority(tmp_path, monkeypatch, fault):
    from test_native_lane_authority import _operation_request_v2
    from aware_goal_native_fs_adapter.phase_operation import NativeGitGoalPhaseOperationProvider
    from aware_goal_sdk.phase_operation import GoalPhaseOperationClient, GoalPhaseObserveEligibilityError
    root, _, receipt, claims = _direction_chain(tmp_path, monkeypatch, fault=fault)
    request = _operation_request_v2(root, receipt, claims=claims)
    with pytest.raises(GoalPhaseObserveEligibilityError):
        GoalPhaseOperationClient(NativeGitGoalPhaseOperationProvider(_native_capability(root, monkeypatch))).observe_eligibility_v2(request)


@pytest.mark.parametrize("verdict,check_fault,result,partition", [
    ("accepted", None, "eligible", "satisfied"),
    ("rejected", None, "held", "rejected"),
    ("accepted", ("package-tests", "failed_count", 1), "held", "rejected"),
    ("unavailable", None, "held", "unresolved"),
])
def test_gate_direction_uses_neutral_dependency_results(tmp_path, monkeypatch, verdict, check_fault, result, partition):
    root, provider, receipt, claims = _direction_chain(tmp_path, monkeypatch,
        consumer_relation=GoalDependencyRelation.REQUIRES_COMPLETION, verdict=verdict, check_fault=check_fault)
    direction = provider.qualify_runtime_checks_direction(receipt, **claims)
    decision = _eligibility(direction, "consumer").decision
    assert decision.eligibility == result and decision.observation_coverage == "complete"
    assert getattr(decision.dependency_gate, partition + "_keys") == ("consumer-needs-foundation",)


def test_gate_direction_satisfaction_does_not_authorize_acceptance_dependency(tmp_path, monkeypatch):
    _, provider, receipt, claims = _direction_chain(tmp_path, monkeypatch,
        consumer_relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE)
    direction = provider.qualify_runtime_checks_direction(receipt, **claims)
    with pytest.raises(ValueError, match="acceptance_profile_unsupported"):
        _eligibility(direction, "consumer")


@pytest.mark.parametrize("path", [*SOURCES, *OUTPUTS, REVIEW_PATH])
def test_gate_direction_keeps_authenticated_stale_result(tmp_path, monkeypatch, path):
    root, provider, receipt, claims = _direction_chain(tmp_path, monkeypatch,
        consumer_relation=GoalDependencyRelation.REQUIRES_COMPLETION)
    (root / path).write_bytes((root / path).read_bytes() + b"\n")
    _git(root, "add", path)
    _git(root, "commit", "-qm", "Later evidence advance")
    direction = provider.qualify_runtime_checks_direction(receipt, **claims)
    assert direction.evidence_snapshot.gate_observations[0].evaluation.to_wire()["result"] == "stale"
    decision = _eligibility(direction, "consumer").decision
    assert decision.eligibility == "held" and decision.observation_coverage == "complete"
    assert decision.dependency_gate.stale_keys == ("consumer-needs-foundation",)


def test_gate_direction_without_issued_effect_join_still_refuses(tmp_path, monkeypatch):
    _, provider, receipt, _ = _direction_chain(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="scope_not_current"):
        provider.qualify_direction(receipt)


@pytest.mark.parametrize("restore", [False, True])
def test_gate_direction_refuses_unaccounted_work_issue_history(tmp_path, monkeypatch, restore):
    root, provider, receipt, claims = _direction_chain(tmp_path, monkeypatch)
    original = (root / FOUNDATION_WORK_PATH).read_bytes()
    _bytes(root, FOUNDATION_WORK_PATH, original + b"- Unaccounted Issue update.\n")
    _git(root, "add", FOUNDATION_WORK_PATH)
    _git(root, "commit", "-qm", "Unknown Work Issue effect")
    if restore:
        _bytes(root, FOUNDATION_WORK_PATH, original)
        _git(root, "add", FOUNDATION_WORK_PATH)
        _git(root, "commit", "-qm", "Restore exact Work Issue bytes")
    with pytest.raises(ValueError, match="issue_effect_unqualified"):
        provider.qualify_runtime_checks_direction(receipt, **claims)


def test_gate_direction_reobserves_unrelated_advance_without_relabeling_origin(tmp_path, monkeypatch):
    root, provider, receipt, claims = _direction_chain(tmp_path, monkeypatch)
    previous = provider.qualify_runtime_checks_direction(receipt, **claims)
    _bytes(root, "unrelated.txt", b"Unrelated source")
    _git(root, "add", "unrelated.txt")
    _git(root, "commit", "-qm", "Unrelated repository advancement")
    current = provider.qualify_runtime_checks_direction(receipt, **claims)
    assert current.global_authority.source_revision_ref == _git(root, "rev-parse", "HEAD")
    assert current.scope_currentness_ref != previous.scope_currentness_ref
    a = previous.evidence_snapshot.gate_observations[0].evaluator_input.to_wire()["source_verification"]
    b = current.evidence_snapshot.gate_observations[0].evaluator_input.to_wire()["source_verification"]
    assert a["original_source_revision_ref"] == b["original_source_revision_ref"]
    assert _eligibility(current, next(p.coordinate.phase_key for p in current.document.operational_bundle.phases if p.coordinate.lane_key == "foundation")).decision.eligibility == "eligible"


def test_gate_direction_preserves_unrelated_lane_independence(tmp_path, monkeypatch):
    root, provider, receipt, claims = _direction_chain(tmp_path, monkeypatch)
    old = provider.qualify_runtime_checks_direction(receipt, **claims)
    prefix, doc = extract_goal_phase_native_carrier((root / CUSTOMER_PATH).read_bytes())
    doc = replace(doc, definitions=tuple(replace(d, title="Unrelated updated title") if d.coordinate.phase_key == "later" else d for d in doc.definitions))
    _bytes(root, CUSTOMER_PATH, attach_goal_phase_native_carrier(prefix, doc))
    _git(root, "add", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Unrelated lane definition update")
    current = provider.qualify_runtime_checks_direction(receipt, **claims)
    assert current.document.document_ref != old.document.document_ref
    assert current.semantic_closure_ref == old.semantic_closure_ref
    assert current.evidence_snapshot.gate_observations[0].evaluation.to_wire()["result"] == "satisfied"


@pytest.mark.parametrize("mutation", ["snapshot", "evaluation", "issue", "document"])
def test_gate_direction_rejects_postissuance_mutation(tmp_path, monkeypatch, mutation):
    from aware_goal_operational_runtime import require_qualified_goal_native_lane_direction
    _, provider, receipt, claims = _direction_chain(tmp_path, monkeypatch)
    direction = provider.qualify_runtime_checks_direction(receipt, **claims)
    if mutation == "snapshot":
        object.__setattr__(direction.evidence_snapshot, "source_revision_ref", receipt.repository_commit_ref)
    elif mutation == "evaluation":
        result = direction.evidence_snapshot.gate_observations[0].evaluation
        wire = result.to_wire()
        wire["result"] = "rejected"
        object.__setattr__(result, "canonical_body", canonical_json(wire))
    elif mutation == "issue":
        next(iter(direction.issue_authorities.values()))["blob_oid"] = "0" * 40
    else:
        object.__setattr__(direction.document, "source_refs", ("forged:source",))
    with pytest.raises(ValueError):
        require_qualified_goal_native_lane_direction(direction)


@pytest.mark.parametrize("race", ["head", "target"])
def test_gate_direction_terminal_io_precedes_last_head_and_seal(tmp_path, monkeypatch, race):
    from aware_goal_native_fs_adapter.native_lane_authority import _DIRECTION_ISSUED
    root, provider, receipt, claims = _direction_chain(tmp_path, monkeypatch)
    before = len(_DIRECTION_ISSUED)
    original = provider._recheck_evidence_targets
    calls = []
    def replace_after_checks(snapshot, paths):
        original(snapshot, paths)
        calls.append(True)
        if len(calls) != 2:
            return
        if race == "head":
            _bytes(root, "unrelated.txt", b"Race")
            _git(root, "add", "unrelated.txt")
            _git(root, "commit", "-qm", "HEAD advances during terminal I/O")
        else:
            (root / SOURCES[0]).unlink()
            (root / SOURCES[0]).symlink_to(tmp_path / "external-source")
            original(snapshot, paths)
    monkeypatch.setattr(provider, "_recheck_evidence_targets", replace_after_checks)
    with pytest.raises(ValueError, match="repository_head_advanced|target_unresolvable"):
        provider.qualify_runtime_checks_direction(receipt, **claims)
    assert len(_DIRECTION_ISSUED) <= before


@pytest.mark.parametrize("change", ["definition", "work", "journal", "incident"])
def test_gate_direction_rejects_relevant_change_and_restore(tmp_path, monkeypatch, change):
    root, provider, receipt, claims = _direction_chain(tmp_path, monkeypatch,
        consumer_relation=GoalDependencyRelation.REQUIRES_COMPLETION)
    original = (root / CUSTOMER_PATH).read_bytes()
    prefix, doc = extract_goal_phase_native_carrier(original)
    definition = next(d for d in doc.definitions if d.coordinate.lane_key == "foundation" and d.coordinate.phase_key != "consumer")
    if change == "definition":
        doc = replace(doc, definitions=tuple(replace(d, title="Different authority") if d.coordinate == definition.coordinate else d for d in doc.definitions),
            operational_bundle=replace(doc.operational_bundle, phases=tuple(replace(p, title="Different authority") if p.coordinate == definition.coordinate else p for p in doc.operational_bundle.phases)))
    elif change == "work":
        doc = replace(doc, operational_bundle=replace(doc.operational_bundle, phases=tuple(
            replace(p, work_associations=tuple(replace(w, admitted_at="2026-09-26T12:01:00Z") for w in p.work_associations))
            if p.coordinate == definition.coordinate else p for p in doc.operational_bundle.phases)))
    elif change == "journal":
        doc = replace(doc, operation_journal_profile="v1", phase_operation_journal=GoalPhaseOperationJournalV1(
            entries=(_journal_entry(doc, definition, label="new-approval"),)))
    else:
        doc = replace(doc, operational_bundle=replace(doc.operational_bundle, dependencies=tuple(replace(d, reason="Changed incident authority") for d in doc.operational_bundle.dependencies)))
    _bytes(root, CUSTOMER_PATH, attach_goal_phase_native_carrier(prefix, doc))
    _git(root, "add", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Relevant authority changes")
    _bytes(root, CUSTOMER_PATH, original)
    _git(root, "add", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Restore exact Goal")
    with pytest.raises(ValueError):
        provider.qualify_runtime_checks_direction(receipt, **claims)


def test_gate_direction_portable_decoders_recompute_and_refuse_tampering(tmp_path, monkeypatch):
    from aware_goal_operational_runtime import decode_goal_phase_eligibility_decision_v2, decode_goal_native_lane_direction_authority
    _, provider, receipt, claims = _direction_chain(tmp_path, monkeypatch,
        consumer_relation=GoalDependencyRelation.REQUIRES_COMPLETION)
    direction = provider.qualify_runtime_checks_direction(receipt, **claims)
    assert decode_goal_native_lane_direction_authority(direction.to_wire(), qualified=direction) is direction
    decision = _eligibility(direction, "consumer")
    definition = next(d for d in direction.document.definitions if d.coordinate.phase_key == "consumer")
    inputs = dict(document=direction.document, coordinate=definition.coordinate,
        expected_gate_digest=definition.gate.gate_digest, global_authority=direction.global_authority,
        lane_authority=direction, source_revision_ref=direction.global_authority.source_revision_ref)
    assert decode_goal_phase_eligibility_decision_v2(decision.to_wire(), **inputs) == decision
    wire = decision.to_wire()
    wire["eligibility"] = "held"
    wire["decision_ref"] = "goal-phase-eligibility-decision:" + digest({k:v for k,v in wire.items() if k != "decision_ref"})
    with pytest.raises(ValueError):
        decode_goal_phase_eligibility_decision_v2(wire, **inputs)


def test_gate_direction_copied_issuance_and_caller_snapshots_refuse(tmp_path, monkeypatch):
    from aware_goal_operational_runtime import require_qualified_goal_native_lane_direction
    _, provider, receipt, claims = _direction_chain(tmp_path, monkeypatch)
    direction = provider.qualify_runtime_checks_direction(receipt, **claims)
    with pytest.raises(ValueError):
        require_qualified_goal_native_lane_direction(copy(direction))
    with pytest.raises(TypeError):
        provider.qualify_runtime_checks_direction(receipt, evidence_snapshot=direction.evidence_snapshot)
    foreign = claims["review_publication"].to_wire()
    foreign["owner_execution_id"] = "codex-foreign"
    claims["review_publication"] = make_runtime_checks_artifact(PUBLICATION, {k:v for k,v in foreign.items() if k not in {"schema_id", "publication_ref"}})
    with pytest.raises(ValueError):
        provider.qualify_runtime_checks_direction(receipt, **claims)


def test_gate_direction_registry_follows_output_lifetime(tmp_path, monkeypatch):
    from aware_goal_native_fs_adapter.native_lane_authority import _DIRECTION_ISSUED
    _, provider, receipt, claims = _direction_chain(tmp_path, monkeypatch)
    gc.collect()
    before = len(_DIRECTION_ISSUED)
    direction = provider.qualify_runtime_checks_direction(receipt, **claims)
    assert len(_DIRECTION_ISSUED) == before + 1
    del direction
    gc.collect()
    assert len(_DIRECTION_ISSUED) == before


def test_gate_direction_refuses_pre_source_future_publication_blob_replay(tmp_path, monkeypatch):
    from aware_goal_native_fs_adapter.native_lane_authority import _DIRECTION_ISSUED, _VERIFIED
    root, provider, receipt, claims = _direction_chain(tmp_path, monkeypatch,
        fault="pre-source-future-proof-blob-restore")
    # The evaluator's legitimate source starts after the restore. Its standalone
    # result is current; lane continuity must independently check the earlier gap.
    checker = GitRuntimeChecksReviewAuthorityVerifier(resolver_capability=_native_capability(root, monkeypatch))
    assert evaluate_runtime_checks_review_v2(checker.verify(**claims)).to_wire()["result"] == "satisfied"
    proof = claims["proof_publication"].to_wire()
    future_blob = proof["governing_issue_blob_ref"]
    edges = provider._history_edges(receipt.repository_commit_ref, proof["repository_revision_ref"])
    early = next(child for _, child in edges if provider._git("show", "-s", "--format=%s", child).strip() == b"Ungoverned early future-proof content")
    assert _git(root, "rev-parse", f"{early}:{FOUNDATION_WORK_PATH}") == future_blob
    before = (len(_DIRECTION_ISSUED), len(_VERIFIED))
    with pytest.raises(ValueError, match="issue_effect_unqualified"):
        provider.qualify_runtime_checks_direction(receipt, **claims)
    assert len(_DIRECTION_ISSUED) <= before[0] and len(_VERIFIED) <= before[1]


def test_gate_direction_binds_actual_authorized_issue_effect_epoch(tmp_path, monkeypatch):
    from aware_goal_operational_runtime.phase_native_lane_evidence import require_native_lane_gate_issue_effect
    from aware_goal_native_fs_adapter.native_lane_authority import require_verified_git_native_lane
    _, provider, receipt, claims = _direction_chain(tmp_path, monkeypatch)
    direction = provider.qualify_runtime_checks_direction(receipt, **claims)
    verification = provider._verify(receipt, direction.evidence_snapshot)
    proof = claims["proof_publication"].to_wire()
    assert len(verification.qualified_issue_effects) == 1
    path, parent, commit, before, after, authority = verification.qualified_issue_effects[0]
    assert path == FOUNDATION_WORK_PATH
    assert commit == proof["repository_revision_ref"] and provider._parents(commit) == (parent,)
    assert after == proof["governing_issue_blob_ref"] and before != after
    assert authority == proof["publication_ref"]
    assert verification.to_wire()["qualified_issue_effects"] == [list(verification.qualified_issue_effects[0])]
    for wrong_parent, wrong_commit in ((receipt.repository_commit_ref, commit), (parent, receipt.repository_commit_ref)):
        with pytest.raises(ValueError, match="issue_effect_unqualified"):
            require_native_lane_gate_issue_effect(direction.evidence_snapshot, issue_path=path,
                parent_ref=wrong_parent, commit_ref=wrong_commit, before_blob_ref=before, after_blob_ref=after)
    object.__setattr__(verification, "qualified_issue_effects", ())
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        require_verified_git_native_lane(verification)


def test_gate_direction_refuses_ungoverned_issue_mode_change(tmp_path, monkeypatch):
    root, provider, receipt, claims = _direction_chain(tmp_path, monkeypatch)
    (root / FOUNDATION_WORK_PATH).chmod(0o755)
    _git(root, "add", FOUNDATION_WORK_PATH)
    _git(root, "commit", "-qm", "Ungoverned Issue mode effect with identical blob")
    with pytest.raises(ValueError, match="issue_effect_unqualified"):
        provider.qualify_runtime_checks_direction(receipt, **claims)
