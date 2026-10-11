"""Exact local Issue083 selection; no release or unassisted-onboarding claim."""

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "releases/canonical-issue083-fs-v1"
BASELINE = "fa39296925943787c11039930fe0ad0635b1d7fb"
ORIGINAL_TEST_SHA = "9df5f18e60d2b5ad567d8317b66ab5e2f95043501162edc0bec994ba6486ba61"
ISSUE = "docs/issues/2026/10/11/fb-2026-10-11-canonical-issue083-local-selection-v0.md"
SCOPE = {
    "README.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/SELECTED.json",
    "releases/canonical-issue083-fs-v1/README.md",
    "releases/canonical-issue083-fs-v1/LOCAL-SELECTION.md",
    "releases/canonical-issue083-fs-v1/test_local_selection.py",
    ISSUE,
}


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def sha(body):
    return hashlib.sha256(body).hexdigest()


def original_test():
    path = RELEASE / "test_local_integration.py"
    if path.is_symlink() or sha(path.read_bytes()) != ORIGINAL_TEST_SHA:
        raise ValueError("original_installer_proof_changed")
    spec = importlib.util.spec_from_file_location("issue083_installation_proof", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Selection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {}
        for entry in git("ls-tree", "-r", "-z", BASELINE).split(b"\0"):
            if entry:
                meta, name = entry.split(b"\t", 1)
                mode, kind, oid = meta.split()
                assert kind == b"blob" and mode in (b"100644", b"100755")
                cls.rows[name.decode()] = (mode, oid)
        cls.record = json.loads((ROOT / "releases/SELECTED.json").read_bytes())

    def test_exact_scope_and_all_baseline_bytes_modes(self):
        actual = set()
        for parent, dirs, files in os.walk(ROOT):
            dirs[:] = [name for name in dirs if name != ".git"]
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
        self.assertEqual(len(self.rows), 1152)
        self.assertEqual(len(actual), 1155)
        self.assertEqual(len(set(self.rows) - SCOPE), 1147)

    def test_delivery_pointer_is_not_another_selector_or_authority(self):
        record = self.record
        self.assertEqual(record["selection_kind"], "local_delivery_selection")
        self.assertEqual(record["release"], "canonical-issue083-fs-v1")
        self.assertEqual(record["baseline_revision"], BASELINE)
        self.assertEqual(record["canonical_profile"], "portable_protocols")
        self.assertNotIn("packages", record)
        self.assertNotIn("instruction_record", record)
        self.assertEqual(record["instruction_status"], "draft")
        self.assertEqual(record["selection_review"], "pending")
        self.assertEqual(
            record["commands"],
            ["aware init", "aware issue", "aware protocol", "aware spec"],
        )
        for name in (
            "public_delivery_authorized",
            "contributor_selection_changed",
            "domain_matrix_replayed",
            "unassisted_onboarding_proven",
            "detached_wheels_accepted",
        ):
            self.assertFalse(record[name])
        self.assertTrue(record["whole_envelope_required"])
        issue = (ROOT / ISSUE).read_text()
        section = issue.split("## Ownership Scope", 1)[1].split("##", 1)[0]
        self.assertEqual(
            {
                line.strip()[3:-1]
                for line in section.splitlines()
                if line.strip().startswith("- `")
            },
            SCOPE,
        )

    def test_artifact_source_notice_and_installer_bindings(self):
        for digest, location in (
            ("envelope_sha256", ROOT / "releases" / self.record["envelope"]),
            ("source_index_sha256", ROOT / "releases" / self.record["source_index"]),
        ):
            self.assertEqual(sha(location.read_bytes()), self.record[digest])
        self.assertEqual(
            self.record["envelope_sha256"],
            "a41782559bc3a2d9e02ceacc5bf458f0a77e53940b1b3bdcc8fabca6c15b53ea",
        )
        self.assertEqual(
            self.record["payload_sha256"],
            "0fb3d491b4b99578b06be99894b945d27834d49ad855029de227792ade4f16f4",
        )
        index = json.loads((RELEASE / "SOURCE-INDEX.json").read_bytes())
        self.assertEqual(index["source_revision"], self.record["source_revision"])
        self.assertEqual(
            index["source_revision"], "1f17292b223a1b9054623b4d93589a2cab029bf9"
        )
        self.assertEqual(index["canonical_profile"], "portable_protocols")
        self.assertEqual(len(index["files"]), 1043)
        self.assertEqual(
            len(json.loads((RELEASE / "CONTENT-AUDIT.json").read_bytes())["findings"]),
            12,
        )
        inventory = json.loads((RELEASE / "NOTICE-BINDINGS.json").read_bytes())[
            "aware_package_legal_inventory"
        ]
        self.assertEqual(
            sum(not row["detected_legal_file_paths"] for row in inventory), 6
        )
        for name in (
            "protocols/install.py",
            "workspaces/README.md",
            "protocols/WORKFLOW.md",
            "protocols/issues/FIRST-ISSUE.md",
            "protocols/repository/README.md",
            "releases/canonical-issue083-fs-v1/CONTENT-AUDIT.json",
            "releases/canonical-issue083-fs-v1/NOTICE-BINDINGS.json",
            "releases/canonical-issue083-fs-v1/DELIVERY-MAP.json",
        ):
            self.assertEqual(
                (ROOT / name).read_bytes(), git("show", BASELINE + ":" + name), name
            )

    def test_contributor_and_predecessor_remain_exact(self):
        for name in self.rows:
            if name in {
                "AGENTS.md",
                "CONTRIBUTING.md",
                "aware.protocol.toml",
            } or name.startswith(
                (
                    ".aware/",
                    "docs/agents/",
                    "protocols/contracts/",
                    "releases/canonical-initializer-fs-v1/",
                )
            ):
                self.assertEqual(
                    (ROOT / name).read_bytes(), git("show", BASELINE + ":" + name), name
                )
        self.assertIn("1.2.1", (ROOT / "AGENTS.md").read_text())
        predecessor = json.loads(git("show", BASELINE + ":releases/SELECTED.json"))
        self.assertEqual(predecessor["release"], "canonical-initializer-fs-v1")
        self.assertTrue((ROOT / "releases" / predecessor["envelope"]).is_file())

    def test_only_local_status_changes_in_root_commands(self):
        before = git("show", BASELINE + ":README.md").decode()
        expected = before.replace(
            "This is a prepared, unselected Issue083 successor layout. Instructions remain\n"
            "draft; it is not a claim that public main already delivers this software.\n"
            "The unchanged [delivery pointer](releases/SELECTED.json) still names the retained\n"
            "initializer predecessor. Selection, instruction freeze and publication follow\n"
            "separate review. Do not overlay either installation or migrate contributor tools.",
            "The reviewed Issue083 successor is selected locally; public delivery is not yet\n"
            "authorized. Instructions remain draft. Use this reviewed checkout, not unchanged\n"
            "public main. The [delivery pointer](releases/SELECTED.json) binds its exact whole\n"
            "envelope; [local selection](releases/canonical-issue083-fs-v1/LOCAL-SELECTION.md)\n"
            "records the review boundaries. Do not overlay installations or migrate contributor\n"
            "tools. Instruction freeze and publication remain separately governed.",
        ).replace(
            "From this prepared checkout root:", "From this reviewed checkout root:"
        )
        self.assertEqual((ROOT / "README.md").read_text(), expected)
        self.assertIn(
            "not frozen or publicly delivered",
            (ROOT / "docs/alignment/CURRENT.md").read_text(),
        )
        self.assertIn("six", (RELEASE / "LOCAL-SELECTION.md").read_text().lower())
        self.assertIn(
            "public delivery is not yet authorized", (RELEASE / "README.md").read_text()
        )

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

    def test_fresh_offline_hidden_install_and_refusals(self):
        original_test().Integration.test_fresh_offline_hidden_install_and_refusals(self)


if __name__ == "__main__":
    unittest.main()
