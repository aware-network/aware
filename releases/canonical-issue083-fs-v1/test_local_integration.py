"""Maintainer proof of exact Issue083 integration; not unassisted evaluation."""

import hashlib
import importlib.util
import json
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "releases/canonical-issue083-fs-v1"
PREDECESSOR = ROOT / "releases/canonical-initializer-fs-v1"
BASELINE = "da3ac15a5585a42c53cfc00ccaaa890416392f63"
LAYOUT_SHA = "6fef470c1c99c92cdb602aa7fd6f92c1017b366ba10189ea80c0d30faedf36ed"
ENVELOPE_SHA = "a41782559bc3a2d9e02ceacc5bf458f0a77e53940b1b3bdcc8fabca6c15b53ea"
PAYLOAD_SHA = "0fb3d491b4b99578b06be99894b945d27834d49ad855029de227792ade4f16f4"
ORIGINAL_TEST_SHA = "ceee1bd44d454ff0eee6d63a5953ef832cbc57e2ec50e3e23410282ee6288b2b"
ISSUE = (
    "docs/issues/2026/10/11/fb-2026-10-11-canonical-issue083-public-integration-v0.md"
)
EXTRAS = {
    ISSUE,
    *[
        "releases/canonical-issue083-fs-v1/" + name
        for name in (
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


def original_installer_proof():
    path = PREDECESSOR / "test_local_integration.py"
    if path.is_symlink() or sha(path.read_bytes()) != ORIGINAL_TEST_SHA:
        raise ValueError("original_installer_proof_changed")
    spec = importlib.util.spec_from_file_location("original_integration_proof", path)
    assert spec and spec.loader
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)
    owner.ROOT, owner.RELEASE = ROOT, RELEASE
    owner.ENVELOPE_SHA, owner.PAYLOAD_SHA = ENVELOPE_SHA, PAYLOAD_SHA
    # The original installer smoke uses a filename literal; its verifier and
    # run/check assertions stay unchanged. Supply the successor archive through
    # an explicit retained alias in private scratch, not a public artifact rename.
    return owner


class Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layout = json.loads((RELEASE / "LAYOUT-REVIEW.json").read_bytes())

    def test_accepted_layout_and_exact_file_set(self):
        self.assertEqual(sha((RELEASE / "LAYOUT-REVIEW.json").read_bytes()), LAYOUT_SHA)
        actual = set()
        for parent, directories, files in os.walk(ROOT):
            directories[:] = [name for name in directories if name != ".git"]
            for name in files:
                path = Path(parent) / name
                self.assertFalse(path.is_symlink())
                actual.add(str(path.relative_to(ROOT)))
        self.assertEqual(actual, set(self.layout["files"]) | EXTRAS)
        self.assertEqual(len(self.layout["files"]), 1148)
        for name, row in self.layout["files"].items():
            path = ROOT / name
            self.assertEqual(sha(path.read_bytes()), row["sha256"], name)
            self.assertEqual(path.stat().st_size, row["bytes"], name)
            self.assertEqual(
                bool(path.stat().st_mode & 0o111),
                bool(int(row["mode"], 8) & 0o111),
                name,
            )

    def test_exact_scope_and_preserved_baseline(self):
        baseline = set(
            git("ls-tree", "-r", "--name-only", BASELINE).decode().splitlines()
        )
        self.assertEqual(baseline, set(self.layout["baseline_dispositions"]))
        self.assertEqual(len(self.layout["changed_files"]), 68)
        self.assertEqual(len(set(self.layout["changed_files"]) | EXTRAS), 72)
        self.assertFalse(
            any(
                row["after_sha256"] is None
                for row in self.layout["changed_files"].values()
            )
        )
        before_modes = dict(
            line.split("\t", 1)[::-1]
            for line in git("ls-tree", "-r", BASELINE).decode().splitlines()
        )
        for name, row in self.layout["baseline_dispositions"].items():
            if row["disposition"] == "preserved":
                self.assertEqual(
                    (ROOT / name).read_bytes(), git("show", BASELINE + ":" + name), name
                )
            self.assertEqual(
                bool((ROOT / name).stat().st_mode & 0o111),
                before_modes[name].startswith("100755"),
                name,
            )
        self.assertFalse(self.layout["selected"])
        self.assertFalse(self.layout["instructions_frozen"])
        self.assertFalse(self.layout["publication_authorized"])

    def test_issue_scope_and_contributor_selection(self):
        issue = (ROOT / ISSUE).read_text()
        scope = issue.split("## Ownership Scope", 1)[1].split("##", 1)[0]
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
        for name, row in self.layout["baseline_dispositions"].items():
            if name.startswith(
                (
                    ".aware/",
                    "docs/agents/",
                    "protocols/contracts/",
                    "releases/canonical-initializer-fs-v1/",
                )
            ):
                self.assertEqual(sha((ROOT / name).read_bytes()), row["sha256"])

    def test_one_profile_source_tree(self):
        index = json.loads((RELEASE / "SOURCE-INDEX.json").read_bytes())
        mapping = json.loads((RELEASE / "SOURCE-MAP.json").read_bytes())
        self.assertEqual(index["canonical_profile"], "portable_protocols")
        self.assertEqual(len(index["files"]), 1043)
        self.assertEqual(len(mapping), 1043)
        for name, row in mapping.items():
            self.assertEqual(
                sha((ROOT / row["path"]).read_bytes()), row["sha256"], name
            )
        self.assertEqual(len(list(ROOT.glob("workspaces/**/pyproject.toml"))), 26)
        self.assertFalse((ROOT / "workspaces/previews").exists())
        self.assertFalse((ROOT / "protocols/collaboration/previews").exists())

    def test_whole_envelope_and_unsuppressed_findings(self):
        spec = importlib.util.spec_from_file_location(
            "issue083_verifier", RELEASE / "archive_verifier.py"
        )
        assert spec and spec.loader
        verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier)
        archive = RELEASE / "canonical-issue083-source-notice-review-v1.tar.gz"
        self.assertEqual(sha(archive.read_bytes()), ENVELOPE_SHA)
        _, members = verifier.verified_archive(archive.read_bytes(), ENVELOPE_SHA)
        delivery = json.loads((RELEASE / "DELIVERY-MAP.json").read_bytes())
        self.assertEqual(set(delivery), set(members))
        self.assertEqual(len(members), 1378)
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
        self.assertEqual(len(json.loads(members["CONTENT-AUDIT.json"])["findings"]), 12)
        self.assertEqual(
            sum(
                not row["detected_legal_file_paths"]
                for row in json.loads(members["NOTICE-BINDINGS.json"])[
                    "aware_package_legal_inventory"
                ]
            ),
            6,
        )

    def test_reference_guard_and_closeout_guidance(self):
        readme = (ROOT / "README.md").read_text()
        self.assertIn("not two admitted", readme)
        self.assertIn("fb/YYYY-MM-DD/lowercase-hyphenated-slug", readme)
        self.assertIn("not atomic", readme)
        self.assertIn("unselected", readme)
        self.assertIn("detached wheels", (RELEASE / "README.md").read_text())
        self.assertIn(
            "live publication capability",
            (ROOT / "protocols/repository/README.md").read_text(),
        )

    def test_installer_only_coordinate_changes(self):
        import ast

        before = git("show", BASELINE + ":protocols/install.py").decode()
        after = (ROOT / "protocols/install.py").read_text()
        for new, old in {
            ENVELOPE_SHA: "5f0edebe568d1cfd8a06a33e6122cd4e0d3dd68f764058b1aa098456cc2df13c",
            PAYLOAD_SHA: "2d812c489485ee187cf45fca012fffdfda5fcdf93d60495a02b843f94e4a8b68",
            "canonical-issue083-source-notice-review-v1.tar.gz": "canonical-initializer-source-notice-review-v1.tar.gz",
            "canonical-issue083-fs-v1": "canonical-initializer-fs-v1",
        }.items():
            after = after.replace(new, old)
        self.assertEqual(ast.dump(ast.parse(after)), ast.dump(ast.parse(before)))

    def test_fresh_offline_hidden_install_and_refusals(self):
        # Reuse the unchanged proof with a private filename view, rather than
        # copy its installer logic or normalize accepted public attachments.
        owner = original_installer_proof()
        scratch = Path(os.environ["AWARE_INITIALIZER_INTEGRATION_REPLAY_ROOT"])
        view = scratch / "release-view"
        view.mkdir(mode=0o700)
        for name in ("archive_verifier.py",):
            (view / name).write_bytes((RELEASE / name).read_bytes())
        (view / "canonical-initializer-source-notice-review-v1.tar.gz").write_bytes(
            (RELEASE / "canonical-issue083-source-notice-review-v1.tar.gz").read_bytes()
        )
        owner.RELEASE = view
        owner.Integration.test_fresh_offline_hidden_install_and_refusals(self)


if __name__ == "__main__":
    unittest.main()
