"""Exact a6 selection/alignment; historical bytes and neutral source unchanged."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "43826e50ab29c8c27c01c80da960018dfc9fee6f"


def previous(path):
    return subprocess.check_output(["git", "show", BASELINE + ":" + path], cwd=ROOT)


class PromotionTests(unittest.TestCase):
    def test_selected_candidate_and_preserved_a5(self):
        selected = (ROOT / "protocols/agent/release.json").read_bytes()
        self.assertEqual(selected, (ROOT / "protocols/agent/release-a6-candidate.json").read_bytes())
        self.assertEqual(hashlib.sha256(selected).hexdigest(), "1f33866867c3385d817776b9afa179751ab669ca280ddab76e8d2080f7b0a08b")
        self.assertEqual((ROOT / "protocols/agent/release-a5.json").read_bytes(), previous("protocols/agent/release.json"))
        self.assertEqual((ROOT / "protocols/agent/release-a5-candidate.json").read_bytes(), previous("protocols/agent/release-a5-candidate.json"))

    def test_payload_catalogs_and_workspace_sources_unchanged(self):
        paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASELINE, "--",
                                         "workspaces", "protocols/contracts/agent-fs", "protocols/agent/distribution",
                                         "protocols/distributions", "protocols/agent/build_bundle.py"], cwd=ROOT, text=True).splitlines()
        for path in paths:
            self.assertEqual((ROOT / path).read_bytes(), previous(path), path)

    def test_contract_labels_and_bootstrap_match_selected_candidate(self):
        bootstrap = json.loads((ROOT / ".aware/agent-bootstrap.json").read_bytes())
        selected = json.loads((ROOT / "protocols/agent/release.json").read_bytes())
        self.assertEqual(selected["agent_contract"], {"ref": bootstrap["contract_ref"], "version": bootstrap["version"]})
        self.assertEqual(bootstrap["version"], "1.2.1")
        self.assertIn("**1.2.1**", (ROOT / "AGENTS.md").read_text())
        self.assertIn("`aware.agent.fs.v1` / 1.2.1.", (ROOT / "docs/agents/README.md").read_text())
        source = ROOT / "protocols/contracts/agent-fs/v1.2.1"
        metadata = json.loads((source / "contract.json").read_bytes())
        for name, relative in metadata["files"].items():
            self.assertEqual(bootstrap["template_sha256"][name], hashlib.sha256((source / relative).read_bytes()).hexdigest())
        for name, digest in bootstrap["rendered_sha256"].items():
            if name == "docs/alignment/CURRENT.md":
                self.assertEqual(digest, hashlib.sha256((source / name).read_bytes()).hexdigest())
                self.assertIn("approved authored amendment", (ROOT / name).read_text())
            else:
                self.assertEqual(digest, hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), name)

    def test_readme_only_projection_preserves_other_105_outputs(self):
        receipt = json.loads((ROOT / "protocols/publication/receipt.json").read_bytes())
        before = json.loads(previous("protocols/publication/receipt.json"))
        self.assertEqual(len(receipt["outputs"]), 106)
        self.assertEqual({k: v for k, v in receipt["outputs"].items() if k != "README.md"},
                         {k: v for k, v in before["outputs"].items() if k != "README.md"})
        self.assertEqual(receipt["generator_sha256"], before["generator_sha256"])
        self.assertEqual((ROOT / "README.md").read_bytes(), (ROOT / "protocols/publication/README.md.in").read_bytes())

    def test_active_instructions_disclose_versions_statuses_and_limits(self):
        for name in ["README.md", "protocols/agent/README.md", "protocols/agent/VERIFICATION.md", "docs/alignment/CURRENT.md"]:
            self.assertIn("0.1.0a6", (ROOT / name).read_text(), name)
        for name in ["protocols/agent/README.md", "protocols/contracts/README.md", "protocols/agent/AGENTS.md"]:
            self.assertIn("1.2.1", (ROOT / name).read_text(), name)
        issue = (ROOT / "docs/issues/PROTOCOL.md").read_text()
        for term in ["issue_day_index:pending", "feed:unavailable", "shared_index_projection", "no operation that evaluates or checks"]:
            self.assertIn(term, issue)
        self.assertIn("task-test interpreter", (ROOT / "protocols/agent/AGENTS.md").read_text())
        self.assertIn("No push", (ROOT / "protocols/publication/A6-PROMOTION.md").read_text())

    def test_quickstart_shell_syntax_and_document_links(self):
        quickstart = (ROOT / "protocols/agent/quickstart.md").read_text()
        blocks = re.findall(r"```sh\n(.*?)```", quickstart, re.S)
        self.assertEqual(len(blocks), 6)
        for block in blocks:
            subprocess.run(["bash", "-n"], input=block, text=True, check=True)
        for name in ["AGENTS.md", "docs/agents/README.md", "protocols/contracts/README.md", "protocols/agent/README.md", "protocols/agent/quickstart.md", "docs/alignment/CURRENT.md"]:
            path = ROOT / name
            for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if "://" not in link and not link.startswith("#"):
                    self.assertTrue((path.parent / link.split("#")[0]).exists(), (name, link))


if __name__ == "__main__":
    unittest.main()
