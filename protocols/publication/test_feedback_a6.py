"""Version-semantic regressions and preserved a5 bytes, not new domain logic."""
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("feedback_projection", ROOT / "protocols/publication/prepare_feedback_a6.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CONTRACT = ROOT / "protocols/contracts/agent-fs/v1.2.1"


def consistent_labels(assets):
    version = json.loads(assets["contract.json"])["version"]
    return (f"**{version}**".encode() in assets["AGENTS.md.in"]
            and f"`aware.agent.fs.v1` / {version}.".encode() in assets["docs/agents/README.md"])


class FeedbackTests(unittest.TestCase):
    def assets(self, source):
        metadata = json.loads((source / "contract.json").read_bytes())
        return {p: (source / p).read_bytes() for p in ["contract.json", *metadata["files"].values()]}

    def test_actual_a5_mismatch_is_not_equal_hash_acceptance(self):
        old = self.assets(ROOT / "protocols/contracts/agent-fs/v1.2.0")
        self.assertFalse(consistent_labels(old))
        self.assertTrue(consistent_labels(MODULE.corrected_assets(old)))

    def test_new_authored_and_packaged_contracts_agree_semantically(self):
        authored = self.assets(CONTRACT)
        packaged = self.assets(ROOT / (MODULE.PROJECT + "aware_agent_cli/templates/agent-fs-v1"))
        self.assertEqual(authored, packaged)
        self.assertTrue(consistent_labels(authored))
        corrupted = dict(packaged, **{"docs/agents/README.md": b"`aware.agent.fs.v1` / 1.1.0.\n"})
        self.assertFalse(consistent_labels(corrupted))

    def test_old_contract_and_a5_record_remain_byte_identical(self):
        self.assertEqual((ROOT / "protocols/agent/release-a5.json").read_bytes(), MODULE.committed("protocols/agent/release.json"))
        paths = [
                 "protocols/agent/release-a5-candidate.json", "protocols/agent/issue-a5-candidate-binding.json",
                 "protocols/agent/distribution/aware-agent-fs-0.1.0a5-linux_x86_64-py312.tar.gz"]
        paths.extend("protocols/contracts/agent-fs/v1.2.0/" + p for p in self.assets(ROOT / "protocols/contracts/agent-fs/v1.2.0"))
        for path in paths:
            self.assertEqual((ROOT / path).read_bytes(), MODULE.committed(path), path)

    def test_existing_version_refuses_before_other_writes(self):
        paths = [ROOT / "protocols/agent/source-provenance.json", CONTRACT / "contract.json"]
        before = [p.read_bytes() for p in paths]
        result = subprocess.run(["/usr/bin/python3.12", "-B", str(ROOT / "protocols/publication/prepare_feedback_a6.py")], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("contract_version_coordinate_exists", result.stderr)
        self.assertEqual(before, [p.read_bytes() for p in paths])

    def test_source_version_preconditions(self):
        old = self.assets(ROOT / "protocols/contracts/agent-fs/v1.2.0")
        for path, value in [("contract.json", b'{"version":"other"}'), ("AGENTS.md.in", b"other"), ("docs/agents/README.md", b"other")]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                MODULE.corrected_assets(dict(old, **{path: value}))

    def test_status_acceptance_and_interpreter_guidance_are_explicit(self):
        issue = (CONTRACT / "docs/issues/PROTOCOL.md").read_text()
        for term in ["issue_day_index:pending", "feed:unavailable", "shared_index_projection", "index_reconciliation_pending", "no operation that evaluates or checks"]:
            self.assertIn(term, issue)
        evaluation = (ROOT / "protocols/evaluations/README.md").read_text()
        for term in ["sys.executable", "sys.version", '"$task_python" -m unittest', "Missing historical evidence stays unknown"]:
            self.assertIn(term, evaluation)


if __name__ == "__main__":
    unittest.main()
