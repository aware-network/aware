"""Portable authored codecs never authenticate their own authority."""
from copy import deepcopy

import pytest
from aware_goal_operational_runtime.phase_runtime_checks_review import (
    PROFILE, PROOF, PUBLICATION, RuntimeChecksSourceIssuerV2, RuntimeChecksVerifiedInputV2,
    canonical_json, decode_runtime_checks_artifact, digest, evaluate_runtime_checks_review_v2,
    make_runtime_checks_artifact, strict_json,
)


def _proof():
    scope = "goal-runtime-checks-source-scope:sha256:" + "a" * 64
    checks = []
    for key in ("package-tests", "runtime-canary", "static-checks"):
        check = {"key": key, "source_scope_ref": scope, "command_argv": ["tool", "exact argument"],
            "output": {"path": f"evidence/{key}.txt", "blob_ref": "a" * 40, "sha256": "sha256:" + "b" * 64}, "exit_code": 0}
        check.update({"passed_count": 1, "failed_count": 0, "skipped_count": 0} if key == "package-tests" else
            {"error_count": 0, "warning_count": 0} if key == "static-checks" else {"result": "passed"})
        checks.append(check)
    return make_runtime_checks_artifact(PROOF, {"request_ref": "goal-runtime-checks-review-request:sha256:" + "c" * 64,
        "request_publication_ref": "goal-runtime-checks-authority-publication:sha256:" + "d" * 64,
        "coordinate": {"goal_tag": "goal/2026-10-01/portable", "lane_key": "runtime", "phase_key": "proof"},
        "definition_ref": "goal-phase-definition:sha256:" + "e" * 64, "gate_digest": "sha256:" + "f" * 64,
        "evaluator_profile": PROFILE, "source_scope_ref": scope, "publisher_execution_id": "codex-proof",
        "checks": checks, "issued_at": "2026-10-01T12:00:00Z"})


def _redigest(value):
    return make_runtime_checks_artifact(value["schema_id"], {k: v for k, v in value.items() if k != "proof_ref"})


def test_canonical_portable_codec_returns_independent_trees():
    proof = _proof()
    wire = proof.to_wire()
    assert decode_runtime_checks_artifact(wire) == proof
    wire["checks"][0]["failed_count"] = 1
    assert proof.to_wire()["checks"][0]["failed_count"] == 0


@pytest.mark.parametrize("field", ["exit_code", "passed_count", "failed_count", "skipped_count"])
@pytest.mark.parametrize("value", [True, False, "0", -1, None])
def test_redigested_non_json_integer_counts_refuse(field, value):
    wire = _proof().to_wire()
    wire["checks"][0][field] = value
    with pytest.raises(ValueError, match="wire_integer"):
        _redigest(wire)


@pytest.mark.parametrize("fault", ["extra", "missing", "duplicate", "reorder", "wrong-profile", "wrong-time", "absolute-path", "dot-path", "bad-argv"])
def test_redigested_structurally_noncanonical_proof_refuses(fault):
    wire = _proof().to_wire()
    if fault == "extra": wire["unexpected"] = True
    elif fault == "missing": del wire["checks"][0]["failed_count"]
    elif fault == "duplicate": wire["checks"][1] = deepcopy(wire["checks"][0])
    elif fault == "reorder": wire["checks"].reverse()
    elif fault == "wrong-profile": wire["evaluator_profile"] = "arbitrary-evaluator"
    elif fault == "wrong-time": wire["issued_at"] = "2026-10-01T12:00:00+01:00"
    elif fault == "absolute-path": wire["checks"][0]["output"]["path"] = "/outside/proof.txt"
    elif fault == "dot-path": wire["checks"][0]["output"]["path"] = "evidence/../proof.txt"
    elif fault == "bad-argv": wire["checks"][0]["command_argv"] = [True]
    with pytest.raises((ValueError, TypeError)):
        _redigest(wire)


def test_duplicate_json_keys_and_tampered_artifact_digest_refuse():
    with pytest.raises(ValueError, match="duplicate_json"):
        strict_json('{"schema_id":"one","schema_id":"two"}')
    wire = _proof().to_wire()
    wire["checks"][0]["failed_count"] = 1
    with pytest.raises(ValueError, match="artifact_digest"):
        decode_runtime_checks_artifact(wire)


def test_customer_publication_paths_roundtrip_without_fixed_docs_roots():
    scope = ["customer/proofs/evidence.json", "customer/issues/proof.md"]
    proof = _proof().to_wire()
    publication = make_runtime_checks_artifact(PUBLICATION, {
        "artifact_schema_id": PROOF, "artifact_ref": proof["proof_ref"], "artifact_path": scope[0],
        "artifact_blob_ref": "a" * 40, "repository_revision_ref": "b" * 40,
        "repository_commit_receipt_ref": "repository-commit:" + "b" * 40,
        "governing_issue_path": scope[1], "governing_issue_blob_ref": "c" * 40,
        "owner_execution_id": "codex-proof", "status": "in_progress", "scope": scope,
        "scope_digest": digest({"ownership_scope": scope}),
    })
    assert decode_runtime_checks_artifact(publication.to_wire()) == publication


def test_structural_transport_does_not_impose_git_on_an_object_provider():
    value = _proof().to_wire()
    value["checks"][0]["output"]["blob_ref"] = "source-object:immutable-output"
    proof = _redigest(value)
    assert decode_runtime_checks_artifact(proof.to_wire()) == proof
    # A structural round-trip issues no provider authority.


def test_caller_constructed_input_with_echo_witness_is_not_authority():
    class EchoWitness(RuntimeChecksSourceIssuerV2):
        def require_input(self, value):
            return None
    value = RuntimeChecksVerifiedInputV2(canonical_json({"proof": _proof().to_wire()}), EchoWitness())
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        evaluate_runtime_checks_review_v2(value)
