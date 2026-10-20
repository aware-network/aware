"""Real-Git publication canaries. No fixture has issued actor-action authority."""

import gc
import hashlib
import json
import weakref

import pytest

from aware_goal_operational_runtime import extract_goal_phase_native_carrier
from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.phase_acceptance_provenance import OWNER_PROFILE
from aware_goal_operational_runtime.phase_owner_attestation import (
    AUTHORIZATION_SCHEMA, DECISION_SCHEMA, OBLIGATIONS, EVIDENCE_ROLES,
    make_owner_attestation_claim_v2, encode_owner_attestation_v2,
)
from aware_goal_native_fs_adapter.owner_attestation_publication import (
    GitOwnerAttestationPublicationVerifierV2, GitOwnerAttestationPublicationProofV2,
    require_verified_owner_attestation_publication, _ISSUED,
)
from test_native_provider import CUSTOMER_PATH, CUSTOMER_ISSUE_PATH, CUSTOMER_ISSUE_TAG, GOAL, _source, _native_capability, _git

ARTIFACT = "retained/owner-authorization.json"


def _fixture(tmp_path, monkeypatch, *, fault=None, decision=False):
    root, _ = _source(tmp_path, goal_path=CUSTOMER_PATH)
    origin = _git(root, "rev-parse", "HEAD")
    capability = _native_capability(root, monkeypatch)
    verifier = GitOwnerAttestationPublicationVerifierV2(resolver_capability=capability)
    payload = (root / CUSTOMER_PATH).read_bytes()
    _, doc = extract_goal_phase_native_carrier(payload)
    definition = doc.definitions[0]
    common = {
        "coordinate": {"goal_tag": GOAL, "lane_key": "runtime", "phase_key": "first"},
        "definition_ref": definition.definition_ref, "gate_digest": definition.gate.gate_digest,
        "source_epoch": {"provider_binding_ref": verifier.source_binding_ref, "source_revision": origin,
                         "document_ref": doc.document_ref, "goal_sha256": "sha256:" + hashlib.sha256(payload).hexdigest()},
        "profile": OWNER_PROFILE, "owner_actor_ref": "identity:unverified-actor",
        "owner_execution_id": "codex-test", "owner_authority_ref": "owner:unverified-appointment",
        "issued_at": "2026-10-03T01:00:00Z", "action_occurrence_ref": "actor-action-occurrence:" + fingerprint("unissued-action"),
    }
    if fault == "foreign-owner": common["owner_execution_id"] = "codex-foreign"
    if fault == "wrong-target": common["coordinate"]["phase_key"] = "absent"
    if fault == "wrong-gate": common["gate_digest"] = fingerprint("foreign-gate")
    if fault == "wrong-binding": common["source_epoch"]["provider_binding_ref"] = "provider:foreign"
    if fault == "wrong-sha": common["source_epoch"]["goal_sha256"] = fingerprint("foreign-source")
    if fault == "source-restore":
        for data in (payload + b"\n", payload):
            (root / CUSTOMER_PATH).write_bytes(data)
            _git(root, "add", CUSTOMER_PATH)
            _git(root, "commit", "-qm", "Protected Goal changes before publication")
    claim = make_owner_attestation_claim_v2(AUTHORIZATION_SCHEMA, dict(
        common, promise_interpretation="unchanged_gate_attestation",
        obligation_keys=list(OBLIGATIONS), evidence_roles=list(EVIDENCE_ROLES),
    ))
    if decision:
        inventory = [{"evidence_ref": "evidence:" + role, "role": role,
                      "content_identity": {"content_ref": "object:unverified:" + role, "sha256": fingerprint(role), "byte_count": 12},
                      "source_epoch": {"provider_binding_ref": "object:unverified", "source_revision": "object:historical"},
                      "publication_authority_ref": "publication:unverified"} for role in EVIDENCE_ROLES]
        claim = make_owner_attestation_claim_v2(DECISION_SCHEMA, dict(
            common, authorization_ref=claim.reference, verdict="accept", evidence_inventory=inventory,
            obligations=[{"key": key, "attestation": "met", "evidence_refs": ["evidence:implementation"]} for key in OBLIGATIONS],
            limitations=[],
        ))
    issue = root / CUSTOMER_ISSUE_PATH
    issue.parent.mkdir(parents=True)
    scope = [ARTIFACT, CUSTOMER_ISSUE_PATH]
    if fault == "wrong-scope": scope.append("other.txt")
    issue.write_text(
        f"# Issue\n- Tag: {CUSTOMER_ISSUE_TAG}\n- Status: {'Closed' if fault == 'closed-issue' else 'In Progress'}\n"
        f"- Owner: codex-test\n- Goal: {'goal/2026-09-26/foreign' if fault == 'wrong-issue-goal' else GOAL}\n\n"
        "## Ownership Scope\n" + "".join(f"- `{p}`\n" for p in scope) + "\n## Updates\n"
    )
    _git(root, "add", CUSTOMER_ISSUE_PATH)
    _git(root, "commit", "-qm", "Admit governing Issue")
    artifact = root / ARTIFACT
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(encode_owner_attestation_v2(claim))
    if fault == "preexisting":
        _git(root, "add", ARTIFACT)
        _git(root, "commit", "-qm", "Earlier artifact, not the claimed publication")
        artifact.write_bytes(artifact.read_bytes() + b"\n")
    issue.write_text(issue.read_text() + "- Exact artifact publication.\n")
    if fault == "postimage-repair":
        before = issue.read_text().replace("codex-test", "codex-foreign")
        issue.write_text(before)
        _git(root, "add", CUSTOMER_ISSUE_PATH)
        _git(root, "commit", "-qm", "Foreign parent Issue")
        issue.write_text(before.replace("codex-foreign", "codex-test") + "- Repair in postimage.\n")
    paths = sorted((ARTIFACT, CUSTOMER_ISSUE_PATH))
    if fault == "extra-path":
        (root / "extra.txt").write_text("outside effect")
        paths.append("extra.txt")
    _git(root, "add", *paths)
    message = "Publish retained claim"
    if fault != "missing-receipt":
        message += f"\n\nIssue-Tag: {CUSTOMER_ISSUE_TAG}\nIssue-Path: {CUSTOMER_ISSUE_PATH}\nOwner: codex-test\nOwned-Paths: {','.join(sorted((ARTIFACT, CUSTOMER_ISSUE_PATH)))}"
    _git(root, "commit", "-qm", message)
    commit = _git(root, "rev-parse", "HEAD")
    kwargs = dict(goal_path=CUSTOMER_PATH, artifact_path=ARTIFACT, publication_commit=commit,
                  repository_commit_receipt_ref="repository-commit:" + commit, issue_path=CUSTOMER_ISSUE_PATH, expected_claim=claim)
    return root, verifier, kwargs


@pytest.mark.parametrize("decision", [False, True])
def test_real_publication_does_not_authenticate_claimed_actor_action_or_evidence(tmp_path, monkeypatch, decision):
    root, verifier, kwargs = _fixture(tmp_path, monkeypatch, decision=decision)
    before = (root / CUSTOMER_PATH).read_bytes()
    proof = verifier.verify(**kwargs)
    assert require_verified_owner_attestation_publication(proof) is proof
    wire = proof.to_wire()
    assert wire["observed_head"] == _git(root, "rev-parse", "HEAD")
    assert wire["claim"] == kwargs["expected_claim"].to_wire()
    assert wire["verified_goal_owner_execution_id"] == "codex-test"
    for key in ("actor_identity_authority", "action_issuance_authority", "owner_appointment_authority", "evidence_issuance_authority"):
        assert wire[key] == "unavailable"
    assert not hasattr(proof, "verifier_token") and not hasattr(proof, "outcome")
    assert (root / CUSTOMER_PATH).read_bytes() == before


@pytest.mark.parametrize("fault", ["foreign-owner", "wrong-target", "wrong-gate", "wrong-binding", "wrong-sha",
                                   "closed-issue", "wrong-scope", "wrong-issue-goal", "extra-path", "missing-receipt",
                                   "preexisting", "postimage-repair", "source-restore"])
def test_real_publication_faults_refuse(tmp_path, monkeypatch, fault):
    _, verifier, kwargs = _fixture(tmp_path, monkeypatch, fault=fault)
    with pytest.raises(ValueError): verifier.verify(**kwargs)


@pytest.mark.parametrize("path", [CUSTOMER_PATH, CUSTOMER_ISSUE_PATH, ARTIFACT])
def test_changed_then_restored_protected_history_refuses(tmp_path, monkeypatch, path):
    root, verifier, kwargs = _fixture(tmp_path, monkeypatch)
    target = root / path
    original = target.read_bytes()
    for data in (original + b"\n", original):
        target.write_bytes(data)
        _git(root, "add", path)
        _git(root, "commit", "-qm", "Protected change and restore")
    with pytest.raises(ValueError, match="protected_history_changed"): verifier.verify(**kwargs)


def test_unrelated_descendant_and_absent_artifact_projection_are_read_only(tmp_path, monkeypatch):
    root, verifier, kwargs = _fixture(tmp_path, monkeypatch)
    (root / "unrelated.txt").write_text("unrelated")
    _git(root, "add", "unrelated.txt")
    _git(root, "commit", "-qm", "Unrelated advancement")
    (root / ARTIFACT).unlink()
    proof = verifier.verify(**kwargs)
    assert proof.to_wire()["observed_head"] == _git(root, "rev-parse", "HEAD")
    assert not (root / ARTIFACT).exists()


def test_stale_goal_worktree_is_not_source_authority_or_repaired(tmp_path, monkeypatch):
    root, verifier, kwargs = _fixture(tmp_path, monkeypatch)
    target = root / CUSTOMER_PATH
    target.write_bytes(b"stale local Goal projection\n")
    proof = verifier.verify(**kwargs)
    assert proof.to_wire()["observed_head"] == _git(root, "rev-parse", "HEAD")
    assert target.read_bytes() == b"stale local Goal projection\n"


@pytest.mark.parametrize("fault", ["receipt", "inherited", "copied-path", "symlink", "parent-symlink"])
def test_coordinate_receipt_and_containment_substitutions_refuse(tmp_path, monkeypatch, fault):
    root, verifier, kwargs = _fixture(tmp_path, monkeypatch)
    if fault == "receipt": kwargs["repository_commit_receipt_ref"] = "repository-commit:" + "a" * 40
    elif fault == "inherited":
        (root / "other.txt").write_text("other")
        _git(root, "add", "other.txt"); _git(root, "commit", "-qm", "Inherited artifact")
        kwargs["publication_commit"] = _git(root, "rev-parse", "HEAD")
        kwargs["repository_commit_receipt_ref"] = "repository-commit:" + kwargs["publication_commit"]
    elif fault == "copied-path": kwargs["artifact_path"] = "copied/authorization.json"
    else:
        outside = tmp_path / "outside"; outside.mkdir()
        target = root / ARTIFACT
        if fault == "symlink":
            target.unlink(); target.symlink_to(outside / "foreign.json")
        else:
            target.unlink(); target.parent.rmdir(); target.parent.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError): verifier.verify(**kwargs)


def test_issued_proof_mutation_forgery_detachment_and_lifetime(tmp_path, monkeypatch):
    _, verifier, kwargs = _fixture(tmp_path, monkeypatch)
    proof = verifier.verify(**kwargs)
    detached = proof.to_wire(); detached["claim"]["owner_actor_ref"] = "identity:foreign"
    assert require_verified_owner_attestation_publication(proof) is proof
    forged = GitOwnerAttestationPublicationProofV2(proof.canonical_body)
    with pytest.raises(ValueError, match="unissued_or_mutated"): require_verified_owner_attestation_publication(forged)
    value = json.loads(proof.canonical_body); value["observed_head"] = "b" * 40
    object.__setattr__(proof, "canonical_body", json.dumps(value, sort_keys=True, separators=(",", ":")))
    with pytest.raises(ValueError, match="unissued_or_mutated"): require_verified_owner_attestation_publication(proof)
    issued = verifier.verify(**kwargs); pointer = weakref.ref(issued); del issued; gc.collect()
    assert pointer() is None
    assert all(k is not None for k in _ISSUED)


def test_terminal_resolution_commit_refuses_before_registration(tmp_path, monkeypatch):
    root, verifier, kwargs = _fixture(tmp_path, monkeypatch)
    original = verifier._artifact_target
    calls = 0
    def interleave(path):
        nonlocal calls
        original(path); calls += 1
        if calls == 2:
            (root / "concurrent.txt").write_text("advance")
            _git(root, "add", "concurrent.txt"); _git(root, "commit", "-qm", "Concurrent terminal commit")
    monkeypatch.setattr(verifier, "_artifact_target", interleave)
    before = len(_ISSUED)
    with pytest.raises(ValueError, match="repository_head_advanced"): verifier.verify(**kwargs)
    assert len(_ISSUED) == before
