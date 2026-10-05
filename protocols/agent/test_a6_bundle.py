"""Separate a6 candidate accounting; live a5 and domain owner bytes preserved."""
import hashlib
import json
from pathlib import Path
import unittest

from test_bundle import BundleTests

ROOT = Path(__file__).resolve().parent


class A6BundleTests(BundleTests):
    release_name = "release-a6-candidate.json"

    def test_live_selection_and_exact_one_wheel_correction(self):
        current = json.loads((ROOT / "release-a5.json").read_bytes())
        self.assertEqual(current["version"], "0.1.0a5")
        self.assertEqual(hashlib.sha256((ROOT / "release-a5.json").read_bytes()).hexdigest(),
                         "dea4c561c37f557dbb9012838522f4e96d076b323e220e164eba7e24c3442bc0")
        self.assertEqual(current["archive_sha256"], "0e6a2c98a0d8c691b7078ab48194363971d547689514b5c8fa3a3d2f7ccc9184")
        self.assertEqual(self.release["version"], "0.1.0a6")
        self.assertEqual(self.release["agent_contract"]["version"], "1.2.1")
        self.assertEqual((ROOT / "release.json").read_bytes(), (ROOT / self.release_name).read_bytes())
        before = {r["filename"]: r["sha256"] for r in current["wheels"]}
        after = {r["filename"]: r["sha256"] for r in self.release["wheels"]}
        unchanged = {n for n in before.keys() & after.keys() if before[n] == after[n]}
        self.assertEqual(len(unchanged), 21)
        self.assertEqual(before.keys() - after.keys(), {"aware_agent_cli-0.1.0a5-py3-none-any.whl"})
        self.assertEqual(after.keys() - before.keys(), {"aware_agent_cli-0.1.0a6-py3-none-any.whl"})

    def test_exact_binding_and_unchanged_domain_owner_sources(self):
        binding = json.loads((ROOT / "feedback-a6-candidate-binding.json").read_bytes())
        self.assertEqual(binding["archive_sha256"], self.release["archive_sha256"])
        self.assertEqual(binding["release_sha256"], hashlib.sha256((ROOT / self.release_name).read_bytes()).hexdigest())
        self.assertFalse(binding["domain_implementation_changed"])
        self.assertEqual(binding["source_provenance_sha256"], hashlib.sha256(self.files["source-provenance.json"]).hexdigest())
        for row in binding["owner_files"]:
            module = row["package"].replace("-", "_")
            relative = row["path"].split("/" + module + "/", 1)[1]
            data = self.files["source/" + module + "/" + module + "/" + relative]
            self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256"])

    def test_semantic_labels_and_client_only_version_literal(self):
        prefix = "source/aware_agent_cli/aware_agent_cli/"
        metadata = json.loads(self.files[prefix + "templates/agent-fs-v1/contract.json"])
        version = metadata["version"]
        self.assertIn(("**" + version + "**").encode(), self.files[prefix + "templates/agent-fs-v1/AGENTS.md.in"])
        self.assertIn(("`aware.agent.fs.v1` / " + version + ".").encode(), self.files[prefix + "templates/agent-fs-v1/docs/agents/README.md"])
        old = json.loads((ROOT / "release-a5.json").read_bytes())
        _, prior = __import__("test_bundle").VERIFIER.verified_archive((ROOT / old["archive"]).read_bytes(), old["archive_sha256"])
        self.assertEqual(self.files[prefix + "main.py"], prior[prefix + "main.py"].replace(b"aware-agent-cli 0.1.0a5", b"aware-agent-cli 0.1.0a6"))
        for name, data in prior.items():
            if name.startswith(prefix) and "/templates/" not in name and not name.endswith("/main.py"):
                self.assertEqual(self.files[name], data, name)


if __name__ == "__main__":
    unittest.main()
