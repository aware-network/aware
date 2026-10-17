"""Exact local target-fit selection; no release or unassisted-onboarding claim."""

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "releases/canonical-reviewed-workflow-fs-v1"
BASELINE = "0cde0ef8f89d5632311e2cca9e85292a0ea73e59"
ORIGINAL_TEST_SHA = "b42c9f74a19a58915656524fd0759a4905d9d403bbc40920549d1e2a04e0ada5"
ISSUE = "docs/issues/2026/10/17/fb-2026-10-17-canonical-reviewed-workflow-local-selection-v0.md"
SCOPE = {
    "README.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/SELECTED.json",
    "releases/canonical-reviewed-workflow-fs-v1/README.md",
    "releases/canonical-reviewed-workflow-fs-v1/LOCAL-SELECTION.md",
    "releases/canonical-reviewed-workflow-fs-v1/test_local_selection.py",
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
    spec = importlib.util.spec_from_file_location("target_fit_installation_proof", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def derive_delivery_record(root):
    """Derive immutable delivery coordinates, never package selection or authority."""
    release_name = "canonical-reviewed-workflow-fs-v1"
    release = root / "releases" / release_name
    layout_body = (release / "LAYOUT-REVIEW.json").read_bytes()
    index_body = (release / "SOURCE-INDEX.json").read_bytes()
    archive_name = "canonical-reviewed-workflow-source-notice-review-v1.tar.gz"
    archive_body = (release / archive_name).read_bytes()
    if (
        sha(layout_body)
        != "bef22ce66bf6c218e2c89a828ed9750d9dba5fea7737f085e6310b813931d221"
        or sha(index_body)
        != "f5a702c49e3e6ec8107e852517b918cb7086f8b3608ae68be22a7490941fcf22"
        or sha(archive_body)
        != "03eb59691cfa1aa1e01e95a7c2727eb3d093ac28e5bd26ae7073416bb61f01b2"
    ):
        raise ValueError("accepted_delivery_artifacts_required")
    layout, index = json.loads(layout_body), json.loads(index_body)
    if (
        layout["catalog_revision"] != index["catalog_revision"]
        or not layout["source_is_composite"]
        or not index["source_is_composite"]
        or index["canonical_profile"] != "portable_protocols"
        or not layout["whole_envelope_required"]
        or layout["payload_sha256"]
        != "899b2ef4beabf074fbdf7ea5980d4eaea1967ef4318b3ebc772814ee84b54727"
    ):
        raise ValueError("accepted_profile_delivery_binding_required")
    return {
        "selection_kind": "local_delivery_selection",
        "release": release_name,
        "canonical_profile": index["canonical_profile"],
        "package_selection_owner": "Workspace authored profile; this record is not a package catalog",
        "baseline_revision": BASELINE,
        "catalog_revision": index["catalog_revision"],
        "source_is_composite": True,
        "envelope": release_name + "/" + archive_name,
        "envelope_sha256": sha(archive_body),
        "payload_sha256": layout["payload_sha256"],
        "source_index": release_name + "/SOURCE-INDEX.json",
        "source_index_sha256": sha(index_body),
        "installer": "protocols/install.py",
        "commands": [
            "aware init",
            "aware issue",
            "aware protocol",
            "aware spec",
            "aware workspace review",
        ],
        "whole_envelope_required": True,
        "detached_wheels_accepted": False,
        "contributor_selection_changed": False,
        "instruction_status": "draft",
        "selection_record": release_name + "/LOCAL-SELECTION.md",
        "selection_review": "pending",
        "public_delivery_authorized": False,
        "domain_matrix_replayed": False,
        "unassisted_onboarding_proven": False,
        "workspace_agent_mount_admitted": True,
        "workspace_mount_profile": "bounded-reviewed-repository-manifest-a1",
        "init_supplies_configuration_not_admission": True,
        "a2_admitted": False,
        "tree_completion_admitted": False,
    }


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
        self.assertEqual(len(self.rows), 1585)
        self.assertEqual(len(actual), 1588)
        self.assertEqual(len(set(self.rows) - SCOPE), 1580)

    def test_delivery_pointer_is_not_another_selector_or_authority(self):
        record = self.record
        self.assertEqual(record, derive_delivery_record(ROOT))
        self.assertEqual(record["selection_kind"], "local_delivery_selection")
        self.assertEqual(record["release"], "canonical-reviewed-workflow-fs-v1")
        self.assertEqual(record["baseline_revision"], BASELINE)
        self.assertEqual(record["canonical_profile"], "portable_protocols")
        self.assertNotIn("packages", record)
        self.assertNotIn("instruction_record", record)
        self.assertEqual(record["instruction_status"], "draft")
        self.assertEqual(record["selection_review"], "pending")
        self.assertEqual(
            record["commands"],
            [
                "aware init",
                "aware issue",
                "aware protocol",
                "aware spec",
                "aware workspace review",
            ],
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
            "03eb59691cfa1aa1e01e95a7c2727eb3d093ac28e5bd26ae7073416bb61f01b2",
        )
        self.assertEqual(
            self.record["payload_sha256"],
            "899b2ef4beabf074fbdf7ea5980d4eaea1967ef4318b3ebc772814ee84b54727",
        )
        index = json.loads((RELEASE / "SOURCE-INDEX.json").read_bytes())
        self.assertEqual(index["catalog_revision"], self.record["catalog_revision"])
        self.assertEqual(
            index["catalog_revision"], "ec4717726c3c7c822fa4fcc5cb7390fce4127f43"
        )
        self.assertTrue(index["source_is_composite"])
        self.assertNotIn("source_revision", self.record)
        self.assertEqual(index["canonical_profile"], "portable_protocols")
        self.assertEqual(len(index["files"]), 1329)
        self.assertEqual(
            len(json.loads((RELEASE / "CONTENT-AUDIT.json").read_bytes())["findings"]),
            12,
        )
        inventory = json.loads((RELEASE / "NOTICE-BINDINGS.json").read_bytes())
        self.assertEqual(len(inventory["detached_wheel_gaps"]), 6)
        for name in (
            "protocols/install.py",
            "workspaces/README.md",
            "protocols/WORKFLOW.md",
            "protocols/issues/FIRST-ISSUE.md",
            "protocols/repository/README.md",
            "releases/canonical-reviewed-workflow-fs-v1/CONTENT-AUDIT.json",
            "releases/canonical-reviewed-workflow-fs-v1/NOTICE-BINDINGS.json",
            "releases/canonical-reviewed-workflow-fs-v1/DELIVERY-MAP.json",
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
                    "releases/canonical-workspace-a1-fs-v1/",
                )
            ):
                self.assertEqual(
                    (ROOT / name).read_bytes(), git("show", BASELINE + ":" + name), name
                )
        self.assertIn("1.2.1", (ROOT / "AGENTS.md").read_text())
        predecessor = json.loads(git("show", BASELINE + ":releases/SELECTED.json"))
        self.assertEqual(predecessor["release"], "canonical-workspace-a1-fs-v1")
        self.assertTrue((ROOT / "releases" / predecessor["envelope"]).is_file())

    def test_only_local_status_changes_in_root_commands(self):
        before = git("show", BASELINE + ":README.md").decode()
        expected = before.replace(
            "This is a **prepared, unselected reviewed-workflow successor**. Instructions\nremain draft. The unchanged [delivery pointer](releases/SELECTED.json) still\nselects the [delivered A1 predecessor](releases/canonical-workspace-a1-fs-v1/README.md).\nThis proposed tree and its installer do not establish public availability of\nthe successor. Integration, selection, instruction freeze and publication remain\nseparate gates. Do not overlay installations or migrate contributor commands.",
            "The accepted reviewed-workflow successor is selected locally; public delivery is\nnot yet authorized. Instructions remain draft. Use this reviewed checkout, not\nunchanged public main. The [delivery pointer](releases/SELECTED.json) binds the\nexact whole envelope; [local selection](releases/canonical-reviewed-workflow-fs-v1/LOCAL-SELECTION.md)\nrecords the review boundaries. Instruction freeze and publication remain separate.\nDo not overlay installations or migrate contributor commands.",
        ).replace(
            "From the root of this prepared checkout:",
            "From the root of this reviewed checkout:",
        )
        self.assertNotEqual(before, expected)
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
                    if "://" in link or link.startswith("mailto:"):
                        continue
                    location, _, fragment = link.partition("#")
                    target = (
                        (ROOT / name).parent / location if location else ROOT / name
                    )
                    self.assertTrue(target.is_file(), (name, link))
                    if fragment:
                        headings = re.findall(
                            r"^#{1,6}\s+(.+)$", target.read_text(), re.MULTILINE
                        )
                        anchors = {
                            re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
                            for heading in headings
                        }
                        self.assertIn(fragment, anchors, (name, link))

    def test_fresh_offline_hidden_install_and_refusals(self):
        original_test().Integration.test_fresh_offline_hidden_install_and_refusals(self)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--delivery-record":
        print(
            json.dumps(
                derive_delivery_record(Path(sys.argv[2])), sort_keys=True, indent=2
            )
        )
    else:
        unittest.main()
