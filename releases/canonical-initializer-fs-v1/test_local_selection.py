"""Exact local delivery selection; original installed proof reused unchanged."""

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "releases/canonical-initializer-fs-v1"
BASELINE = "d669df7da01970a12b782663eefa8682d97bbf32"
ORIGINAL_TEST_SHA = "ceee1bd44d454ff0eee6d63a5953ef832cbc57e2ec50e3e23410282ee6288b2b"
SCOPE = {
    "README.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/canonical-initializer-fs-v1/README.md",
    "releases/SELECTED.json",
    "releases/canonical-initializer-fs-v1/LOCAL-SELECTION.md",
    "releases/canonical-initializer-fs-v1/test_local_selection.py",
    "docs/issues/2026/10/10/fb-2026-10-10-canonical-initializer-local-selection-v0.md",
}


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def original_test():
    path = RELEASE / "test_local_integration.py"
    if (
        path.is_symlink()
        or hashlib.sha256(path.read_bytes()).hexdigest() != ORIGINAL_TEST_SHA
    ):
        raise ValueError("original_installer_proof_changed")
    spec = importlib.util.spec_from_file_location("original_integration", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Selection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {}
        raw = git("ls-tree", "-r", "-z", BASELINE)
        for entry in raw.split(b"\0"):
            if entry:
                meta, name = entry.split(b"\t", 1)
                mode, kind, oid = meta.split()
                assert kind == b"blob" and mode in (b"100644", b"100755")
                cls.rows[name.decode()] = (mode, oid)
        cls.record = json.loads((ROOT / "releases/SELECTED.json").read_bytes())

    def test_exact_scope_and_all_baseline_bytes_modes(self):
        actual = set()
        for parent, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d != ".git"]
            for name in files:
                path = Path(parent) / name
                self.assertFalse(path.is_symlink())
                actual.add(str(path.relative_to(ROOT)))
        self.assertEqual(actual, set(self.rows) | SCOPE)
        raw = subprocess.check_output(
            ["git", "-C", str(ROOT), "cat-file", "--batch"],
            input=b"".join(oid + b"\n" for mode, oid in self.rows.values()),
        )
        offset, changed = 0, set()
        for name, (mode, oid) in self.rows.items():
            end = raw.index(b"\n", offset)
            found, kind, count = raw[offset:end].split()
            start, size = end + 1, int(count)
            self.assertEqual(found, oid)
            self.assertEqual(kind, b"blob")
            self.assertEqual(raw[start + size], 10)
            body = raw[start : start + size]
            offset = start + size + 1
            path = ROOT / name
            self.assertEqual(bool(path.stat().st_mode & 0o111), mode == b"100755", name)
            if path.read_bytes() != body:
                changed.add(name)
                self.assertIn(name, SCOPE)
        self.assertEqual(offset, len(raw))
        self.assertEqual(changed | (actual - set(self.rows)), SCOPE)
        self.assertEqual(len(self.rows), 1091)

    def test_delivery_record_is_not_package_selection_or_authority(self):
        record = self.record
        self.assertEqual(record["selection_kind"], "local_delivery_selection")
        self.assertEqual(record["baseline_revision"], BASELINE)
        self.assertEqual(record["canonical_profile"], "portable_protocols")
        self.assertNotIn("packages", record)
        self.assertEqual(record["instruction_status"], "draft")
        self.assertEqual(record["selection_review"], "pending")
        self.assertEqual(
            record["commands"],
            ["aware init", "aware issue", "aware protocol", "aware spec"],
        )
        for flag in (
            "public_delivery_authorized",
            "contributor_selection_changed",
            "domain_matrix_replayed",
            "unassisted_onboarding_proven",
            "detached_wheels_accepted",
        ):
            self.assertFalse(record[flag])
        self.assertTrue(record["whole_envelope_required"])

    def test_exact_artifact_source_notice_and_installer_bindings(self):
        for field, location in (
            ("envelope_sha256", ROOT / "releases" / self.record["envelope"]),
            ("source_index_sha256", ROOT / "releases" / self.record["source_index"]),
        ):
            self.assertEqual(
                hashlib.sha256(location.read_bytes()).hexdigest(), self.record[field]
            )
        self.assertEqual(
            self.record["envelope_sha256"],
            "5f0edebe568d1cfd8a06a33e6122cd4e0d3dd68f764058b1aa098456cc2df13c",
        )
        self.assertEqual(
            self.record["payload_sha256"],
            "2d812c489485ee187cf45fca012fffdfda5fcdf93d60495a02b843f94e4a8b68",
        )
        for name in (
            "protocols/install.py",
            "docs/HISTORY.md",
            "releases/canonical-initializer-fs-v1/CONTENT-AUDIT.json",
            "releases/canonical-initializer-fs-v1/NOTICE-BINDINGS.json",
            "releases/canonical-initializer-fs-v1/DELIVERY-MAP.json",
        ):
            self.assertEqual(
                (ROOT / name).read_bytes(), git("show", BASELINE + ":" + name), name
            )
        self.assertEqual(
            len(json.loads((RELEASE / "SOURCE-INDEX.json").read_bytes())["files"]), 1023
        )
        self.assertEqual(
            len(json.loads((RELEASE / "CONTENT-AUDIT.json").read_bytes())["findings"]),
            12,
        )

    def test_contributor_bootstrap_and_every_baseline_git_mode_preserved(self):
        for name in self.rows:
            if name in {
                "AGENTS.md",
                "aware.protocol.toml",
                "CONTRIBUTING.md",
            } or name.startswith(
                (".aware/", "docs/agents/", "protocols/contracts/agent-fs/v1.2.1/")
            ):
                self.assertEqual(
                    (ROOT / name).read_bytes(), git("show", BASELINE + ":" + name), name
                )
        self.assertIn("1.2.1", (ROOT / "AGENTS.md").read_text())

    def test_only_status_wording_changes_in_customer_root_commands(self):
        before = git("show", BASELINE + ":README.md").decode()
        expected = before.replace(
            "This is a prepared, unpublished initializer layout. Instructions remain draft.\nUse them against this review tree, not as a claim that unchanged public main\nalready contains this installation.",
            "This initializer distribution is selected locally; public delivery is not yet\nauthorized. Instructions remain draft. Use this reviewed checkout, not unchanged\npublic main. See the [exact local selection](releases/canonical-initializer-fs-v1/LOCAL-SELECTION.md).",
        ).replace(
            "From the prepared checkout root:", "From this reviewed checkout root:"
        )
        self.assertEqual((ROOT / "README.md").read_text(), expected)
        self.assertIn(
            "not frozen or publicly delivered",
            (ROOT / "docs/alignment/CURRENT.md").read_text(),
        )
        self.assertIn("six", (RELEASE / "LOCAL-SELECTION.md").read_text().lower())

    def test_authored_markdown_links_resolve(self):
        for name in SCOPE:
            if name.endswith(".md") and not name.startswith("docs/issues/"):
                for link in re.findall(r"\]\(([^)]+)\)", (ROOT / name).read_text()):
                    if "://" not in link and not link.startswith("#"):
                        self.assertTrue(
                            (ROOT / name)
                            .parent.joinpath(link.split("#", 1)[0])
                            .exists(),
                            (name, link),
                        )

    test_fresh_offline_hidden_install_and_refusals = (
        original_test().Integration.test_fresh_offline_hidden_install_and_refusals
    )


if __name__ == "__main__":
    unittest.main()
