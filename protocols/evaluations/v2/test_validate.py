"""Disposable evidence fixtures, not real customer evaluations."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("evaluation_validator", Path(__file__).with_name("validate.py"))
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
TIME = "2026-10-05T02:24:12Z"


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="aware-evaluation-v2-proof-")
        self.root = Path(self.temporary.name)
        self.manifest = {
            "schema": "aware.client-evaluation.agent-fs.v2", "evaluation_id": "client-evaluation/2026-10-05/fixture",
            "authority": "external-client-evidence-only", "subject": "installation", "status": "blocked",
            "evaluated_at_utc": TIME,
            "inputs": {"source_commit": "1" * 40, "archive_sha256": "sha256:" + "2" * 64, "client_version": "fixture",
                       "brief_sha256": "sha256:" + "3" * 64, "profile": "aware.collaboration.fs_v1",
                       "target": {"starting_state": "empty_directory", "baseline_commit": None,
                                  "protocol_manifest_sha256": None, "approved_outcome": "Prepare a new project", "goal": None}},
            "environment": {"platform": "linux-x86_64", "python": "3.12", "development_checkout_visible": False,
                            "public_consumer_checkout_visible": True, "editable_packages": 0, "pythonpath_set": False, "service_available": False},
            "executions": [{"ref": "fixture-first", "provider": "fixture"}],
            "passes": [{"pass": p, "result": "blocked" if p == "I" else "not_run",
                        "started_at_utc": TIME if p == "I" else None, "ended_at_utc": TIME if p == "I" else None,
                        "execution_refs": ["fixture-first"] if p == "I" else [], "assistance": []} for p in ["I", "U", "V", "R"]],
            "artifact_digests": {}, "non_claims": ["Fixture only; no external acceptance"]}
        self.findings = {"schema": "aware.client-evaluation.agent-fs.findings.v2", "evaluation_id": self.manifest["evaluation_id"],
                         "findings": [{"id": "F-001", "pass": "I", "classification": "unsupported_capability",
                                       "summary": "Setup gap", "expected": "New target", "observed": "Refused",
                                       "evidence_refs": ["interaction:1"], "enforcement_result": "unsupported",
                                       "non_claims": ["Commit behavior not evaluated"]}]}
        self.interactions = [{"schema": "aware.client-evaluation.agent-fs.interaction.v2", "sequence": 1, "pass": "I",
                              "execution_ref": "fixture-first", "observed_at_utc": TIME, "kind": "refusal", "summary": "Unavailable setup"}]
        self.extra = {}

    def tearDown(self):
        self.temporary.cleanup()

    def save(self):
        contents = {"evaluation.md": b"# Sanitized fixture\n", "findings.json": json.dumps(self.findings).encode(),
                    "interactions.jsonl": ("\n".join(json.dumps(i) for i in self.interactions) + "\n").encode(), **self.extra}
        for name, data in contents.items():
            (self.root / name).parent.mkdir(parents=True, exist_ok=True)
            (self.root / name).write_bytes(data)
        self.manifest["artifact_digests"] = {n: "sha256:" + hashlib.sha256(b).hexdigest() for n, b in contents.items()}
        (self.root / "manifest.json").write_text(json.dumps(self.manifest))

    def valid(self):
        self.save()
        return module.validate(self.root)

    def invalid(self, diagnostic):
        self.save()
        with self.assertRaisesRegex(ValueError, diagnostic):
            module.validate(self.root)

    def test_partial_one_execution_no_goal_or_baseline_is_valid(self):
        self.assertEqual(self.valid()["artifacts"], 3)

    def test_issue_only_committed_target_is_valid(self):
        self.manifest["subject"] = "existing_issue"
        self.manifest["inputs"]["target"].update(starting_state="committed_git", baseline_commit="4" * 40)
        self.valid()

    def test_unborn_target_fake_baseline_refused(self):
        self.manifest["inputs"]["target"]["baseline_commit"] = "4" * 40
        self.invalid("fake_baseline")

    def test_goal_subject_without_qualified_input_refused(self):
        self.manifest["subject"] = "goal_readonly"
        self.invalid("qualified_goal")

    def test_unrun_pass_cannot_have_fabricated_time(self):
        self.manifest["passes"][1]["started_at_utc"] = TIME
        self.invalid("unrun_pass")

    def test_recovery_cannot_reuse_prior_execution(self):
        p = self.manifest["passes"][3]
        p.update(result="passed", started_at_utc=TIME, ended_at_utc=TIME, execution_refs=["fixture-first"])
        self.manifest["passes"][1].update(result="passed", started_at_utc=TIME, ended_at_utc=TIME, execution_refs=["fixture-first"])
        self.invalid("fresh_execution")

    def test_recovery_with_distinct_execution_is_valid(self):
        self.manifest["executions"].append({"ref": "fixture-second", "provider": "fixture"})
        self.manifest["passes"][1].update(result="passed", started_at_utc=TIME, ended_at_utc=TIME, execution_refs=["fixture-first"])
        self.manifest["passes"][3].update(result="passed", started_at_utc=TIME, ended_at_utc=TIME, execution_refs=["fixture-second"])
        self.valid()

    def test_digest_tampering_refused(self):
        self.save()
        (self.root / "evaluation.md").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "digest_mismatch"):
            module.validate(self.root)

    def test_unlisted_file_refused(self):
        self.save()
        (self.root / "unlisted.txt").write_bytes(b"x")
        with self.assertRaisesRegex(ValueError, "inventory_mismatch"):
            module.validate(self.root)

    def test_symlink_refused(self):
        self.save()
        (self.root / "link").symlink_to(self.root / "evaluation.md")
        with self.assertRaisesRegex(ValueError, "symlink_refused"):
            module.validate(self.root)

    def test_duplicate_json_key_refused(self):
        with self.assertRaisesRegex(ValueError, "duplicate_json_key"):
            module.decode('{"a":1,"a":2}')

    def test_noncontiguous_interactions_refused(self):
        self.interactions[0]["sequence"] = 2
        self.invalid("not_contiguous")

    def test_unknown_evidence_refused(self):
        self.findings["findings"][0]["evidence_refs"] = ["interaction:99"]
        self.invalid("evidence_unknown")

    def test_enforcement_claim_requires_rejecting_component(self):
        self.findings["findings"][0]["enforcement_result"] = "rejected"
        self.invalid("component_and_diagnostic")

    def test_human_hint_must_be_disclosed(self):
        self.interactions[0]["kind"] = "human_hint"
        self.invalid("hint_not_disclosed")

    def test_pass_order_refused(self):
        self.manifest["passes"].reverse()
        self.invalid("pass_order")


if __name__ == "__main__":
    unittest.main()
