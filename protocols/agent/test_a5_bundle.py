"""Exact a5 candidate accounting, independently of the unchanged a4 selection."""

import hashlib
import json
import unittest
from pathlib import Path

from test_bundle import BundleTests

ROOT = Path(__file__).resolve().parent


class A5BundleTests(BundleTests):
    release_name = "release-a5-candidate.json"

    def test_candidate_is_separate_from_current_release(self):
        current = json.loads((ROOT / "release-a4.json").read_bytes())
        self.assertEqual(current["version"], "0.1.0a4")
        self.assertEqual(
            hashlib.sha256((ROOT / "release-a4.json").read_bytes()).hexdigest(),
            "a3e57d5e430cbc37194b9a16a264961e07e17781493703e8fd4ca5b44415a6c0",
        )
        self.assertEqual(
            current["archive_sha256"],
            "52109f772692071681570e59a161ced33ac6606ff2effdff4fa2094cd4c58cbe",
        )
        self.assertEqual(self.release["version"], "0.1.0a5")
        self.assertEqual(self.release["agent_contract"]["version"], "1.2.0")
        self.assertEqual((ROOT / "release.json").read_bytes(), (ROOT / self.release_name).read_bytes())

    def test_exact_owner_adoption_and_unchanged_dependency_payload(self):
        binding = json.loads((ROOT / "issue-a5-candidate-binding.json").read_bytes())
        self.assertEqual(binding["archive_sha256"], self.release["archive_sha256"])
        for row in binding["owner_files"]:
            module = row["package"].replace("-", "_")
            relative = row["path"].split("/" + module + "/", 1)[1]
            data = self.files["source/" + module + "/" + module + "/" + relative]
            self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256"])
        before = {
            row["filename"]: row["sha256"]
            for row in json.loads((ROOT / "release-a4.json").read_bytes())["wheels"]
        }
        after = {row["filename"]: row["sha256"] for row in self.release["wheels"]}
        unchanged = {
            name for name in before.keys() & after.keys() if before[name] == after[name]
        }
        self.assertEqual(len(unchanged), 18)
        self.assertEqual(len(before.keys() - after.keys()), 4)
        self.assertEqual(len(after.keys() - before.keys()), 4)


if __name__ == "__main__":
    unittest.main()
