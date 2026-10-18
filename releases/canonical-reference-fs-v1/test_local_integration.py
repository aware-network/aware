"""Maintainer exact-layout accounting and original retained reads, not installation."""

import ast
import hashlib
import importlib.util
import json
import os
import subprocess
import unittest
from pathlib import Path
from types import FunctionType

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "releases/canonical-reference-fs-v1"
BASELINE = "055ce1d3528325e05b8bb872f7d6da5340a7dffa"
LAYOUT_SHA = "72585c989e6f1438a3ad093fe9a09de841f868728c676582569a69f97cdf4862"
ENVELOPE_SHA = "afca86cad0fe96c40250819a37b3ab7284236b30d12db919e6596c2aae6a9d30"
PAYLOAD_SHA = "8c804765c0aae2ee8ffe72768158867eab29dae93c669ec6c259421103eaf0e8"
ISSUE = (
    "docs/issues/2026/10/19/fb-2026-10-19-canonical-reference-public-integration-v0.md"
)
EXTRAS = {
    ISSUE,
    *[
        str(RELEASE.relative_to(ROOT)) + "/" + n
        for n in (
            "LAYOUT-REVIEW.json",
            "LOCAL-INTEGRATION.md",
            "test_local_integration.py",
        )
    ],
}


def sha(body):
    return hashlib.sha256(body).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


class Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layout = json.loads((RELEASE / "LAYOUT-REVIEW.json").read_bytes())

    def test_exact_postimages_and_modes(self):
        self.assertEqual(sha((RELEASE / "LAYOUT-REVIEW.json").read_bytes()), LAYOUT_SHA)
        actual = set()
        for parent, directories, files in os.walk(ROOT):
            directories[:] = [n for n in directories if n != ".git"]
            for name in files:
                path = Path(parent) / name
                self.assertFalse(path.is_symlink())
                actual.add(str(path.relative_to(ROOT)))
        self.assertEqual(actual, set(self.layout["files"]) | EXTRAS)
        self.assertEqual(len(self.layout["files"]), 1745)
        for name, row in self.layout["files"].items():
            path = ROOT / name
            self.assertEqual(sha(path.read_bytes()), row["sha256"], name)
            self.assertEqual(path.stat().st_size, row["bytes"], name)
            self.assertEqual(
                bool(path.stat().st_mode & 0o111),
                bool(int(row["mode"], 8) & 0o111),
                name,
            )

    def test_baseline_and_exact_scope(self):
        before = set(
            git("ls-tree", "-r", "--name-only", BASELINE).decode().splitlines()
        )
        self.assertEqual(before, set(self.layout["baseline_dispositions"]))
        self.assertEqual(len(self.layout["changed_files"]), 37)
        self.assertEqual(len(set(self.layout["changed_files"]) | EXTRAS), 41)
        modes = {
            line.split("\t", 1)[1]: line.split()[0]
            for line in git("ls-tree", "-r", BASELINE).decode().splitlines()
        }
        for name, row in self.layout["baseline_dispositions"].items():
            if row["disposition"] == "preserved":
                self.assertEqual(
                    (ROOT / name).read_bytes(), git("show", BASELINE + ":" + name), name
                )
            self.assertEqual(
                bool((ROOT / name).stat().st_mode & 0o111),
                modes[name] == "100755",
                name,
            )
        self.assertTrue(
            all(row["after_sha256"] for row in self.layout["changed_files"].values())
        )

    def test_issue_and_contributor_governance(self):
        scope = (
            (ROOT / ISSUE)
            .read_text()
            .split("## Ownership Scope", 1)[1]
            .split("##", 1)[0]
        )
        actual = {
            line.strip()[3:-1]
            for line in scope.splitlines()
            if line.strip().startswith("- `")
        }
        self.assertEqual(actual, set(self.layout["changed_files"]) | EXTRAS)
        for name in (
            "AGENTS.md",
            "CONTRIBUTING.md",
            "aware.protocol.toml",
            "releases/SELECTED.json",
        ):
            self.assertEqual(
                (ROOT / name).read_bytes(), git("show", BASELINE + ":" + name)
            )
        for key in ("selected", "instructions_frozen", "publication_authorized"):
            self.assertFalse(self.layout[key])

    def test_complete_source_map(self):
        index = json.loads((RELEASE / "SOURCE-INDEX.json").read_bytes())
        mapping = json.loads((RELEASE / "SOURCE-MAP.json").read_bytes())
        self.assertEqual(index["canonical_profile"], "portable_protocols")
        self.assertEqual(len(index["files"]), 1342)
        self.assertEqual(len(mapping), 1342)
        for name, row in mapping.items():
            self.assertEqual(
                sha((ROOT / row["path"]).read_bytes()), row["sha256"], name
            )
        self.assertFalse((ROOT / "workspaces/previews").exists())

    def test_whole_envelope_and_raw_findings(self):
        spec = importlib.util.spec_from_file_location(
            "reference_verifier", RELEASE / "archive_verifier.py"
        )
        assert spec and spec.loader
        verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier)
        archive = RELEASE / "canonical-reference-source-notice-review-v1.tar.gz"
        _, members = verifier.verified_archive(archive.read_bytes(), ENVELOPE_SHA)
        self.assertEqual(len(members), 1801)
        delivery = json.loads((RELEASE / "DELIVERY-MAP.json").read_bytes())
        self.assertEqual(set(delivery), set(members))
        for name, row in delivery.items():
            self.assertEqual(sha(members[name]), row["sha256"], name)
        for name in (
            "LICENSE",
            "NOTICE",
            "SOURCE-INDEX.json",
            "NOTICE-BINDINGS.json",
            "CONTENT-AUDIT.json",
        ):
            self.assertEqual((RELEASE / name).read_bytes(), members[name])
        audit = json.loads(members["CONTENT-AUDIT.json"])
        self.assertEqual(len(audit["findings"]), 12)
        self.assertEqual(audit["clearance"], "not_granted")
        self.assertEqual(
            len(json.loads(members["NOTICE-BINDINGS.json"])["detached_wheel_gaps"]), 6
        )

    def test_installer_four_coordinates_only(self):
        before = git("show", BASELINE + ":protocols/install.py").decode()
        after = (ROOT / "protocols/install.py").read_text()
        for new, old in {
            ENVELOPE_SHA: "73f5038b365dcc7f193b7ebd71b77145d12fe2386311be75dcffd9afadd25df9",
            PAYLOAD_SHA: "d133ae36d78648b0f1c77652b7ab56ded7b2180620e0c023eccf9da4c2cc88e0",
            "canonical-reference-source-notice-review-v1.tar.gz": "canonical-init-summary-source-notice-review-v1.tar.gz",
            "canonical-reference-fs-v1": "canonical-init-summary-fs-v1",
        }.items():
            after = after.replace(new, old)
        self.assertEqual(ast.dump(ast.parse(after)), ast.dump(ast.parse(before)))

    def test_useful_task_and_historical_read_boundaries(self):
        for name in (
            "protocols/tasks/JSON-CHECKER.md",
            "protocols/issues/FIRST-ISSUE.md",
        ):
            self.assertEqual(
                (ROOT / name).read_bytes(), git("show", BASELINE + ":" + name)
            )
        guide = (ROOT / "protocols/workspace/REFERENCE-NAVIGATION.md").read_text()
        self.assertIn("--reference-from-stdin", guide)
        self.assertIn("--focus", guide)
        self.assertIn("Issue", guide)
        self.assertTrue(self.layout["whole_envelope_required"])
        self.assertFalse(self.layout["a2_admitted"])
        self.assertFalse(self.layout["tree_completion_admitted"])

    def test_original_retained_installation_reads(self):
        path = ROOT / "releases/canonical-init-summary-fs-v1/test_local_integration.py"
        self.assertEqual(
            sha(path.read_bytes()),
            "ad3e35eab434e9062afbb3294d478646c2debe37fbd4ff2368a35ee8489f9a68",
        )
        spec = importlib.util.spec_from_file_location("reference_retained_reader", path)
        assert spec and spec.loader
        original = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(original)
        original.PAYLOAD_SHA = PAYLOAD_SHA
        function = original.retained_installation_reads
        constants = function.__code__.co_consts
        self.assertEqual(sum(type(c) is int and c == 153 for c in constants), 1)
        bound = FunctionType(
            function.__code__.replace(
                co_consts=tuple(
                    154 if type(c) is int and c == 153 else c for c in constants
                )
            ),
            function.__globals__,
        )
        self.assertEqual(bound.__code__.co_code, function.__code__.co_code)
        bound(self)


if __name__ == "__main__":
    unittest.main()
