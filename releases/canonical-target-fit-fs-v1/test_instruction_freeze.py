"""Pin target-fit guidance; reuse accepted installer proofs, not domain policy."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(
    os.environ.get("AWARE_FREEZE_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-target-fit-fs-v1"
BASELINE = "8bb81cb2a543992448cfe8b55b5b1f4eab07fb71"
ENVELOPE_SHA = "4823b609938c7d748bfc113ae2a54d7af697e6ca88e698716f538b3460f6b79e"
PAYLOAD_SHA = "e789f1016795098c094162c99766497700da10b182b36911daa8aa2e7c56b7fe"
SOURCE_SHA = "51a300ca6e27b8d3d8001fe7fa8d8a4799caa2e102274fa099b0a979df2d3aec"
ORIGINAL_TEST_SHA = "eb10650c02099e6547488bcb9b1939ef74cb9161de39699ddf2a97345cbd0fbc"
HELPER_SHA = "3bd2808fbec5be1f6f850e98050440ede14539987bd55115022c560253002495"
INSTRUCTIONS = {
    "README.md",
    "protocols/README.md",
    "protocols/COHERENCE.md",
    "protocols/INITIALIZATION.md",
    "protocols/WORKFLOW.md",
    "protocols/issues/README.md",
    "protocols/issues/FIRST-ISSUE.md",
    "protocols/repository/README.md",
    "protocols/specification/README.md",
    "protocols/example-draft-input.py",
    "releases/README.md",
    "releases/canonical-target-fit-fs-v1/README.md",
}
SCOPE = {
    "README.md",
    "protocols/WORKFLOW.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/SELECTED.json",
    "releases/canonical-target-fit-fs-v1/README.md",
    "releases/canonical-target-fit-fs-v1/INSTRUCTIONS.json",
    "releases/canonical-target-fit-fs-v1/INSTRUCTION-FREEZE.md",
    "releases/canonical-target-fit-fs-v1/test_instruction_freeze.py",
    "docs/issues/2026/10/12/fb-2026-10-12-canonical-target-fit-instruction-freeze-v0.md",
}


def sha(body):
    return hashlib.sha256(body).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def helper():
    """Fresh retained proof instance; only immutable delivery coordinates change."""
    path = (
        ROOT / "releases/canonical-draft-preparation-fs-v1/test_instruction_freeze.py"
    )
    if path.is_symlink() or sha(path.read_bytes()) != HELPER_SHA:
        raise ValueError("retained_instruction_helper_changed")
    spec = importlib.util.spec_from_file_location("retained_instruction_proof", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT, module.RELEASE = ROOT, RELEASE
    module.ORIGINAL_TEST_SHA = ORIGINAL_TEST_SHA
    module.INSTRUCTIONS = INSTRUCTIONS
    return module


def derive_instruction_record(root):
    """Return byte pins only; no writes, package selection or operation authority."""
    release = root / "releases/canonical-target-fit-fs-v1"
    for name, digest in (
        ("SOURCE-INDEX.json", SOURCE_SHA),
        ("canonical-target-fit-source-notice-review-v1.tar.gz", ENVELOPE_SHA),
    ):
        path = release / name
        if path.is_symlink() or sha(path.read_bytes()) != digest:
            raise ValueError("accepted_delivery_artifacts_required")
    rows = {}
    for name in sorted(INSTRUCTIONS):
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("regular_instruction_file_required:" + name)
        body = path.read_bytes()
        rows[name] = {"bytes": len(body), "sha256": sha(body)}
    return {
        "record_kind": "candidate_instruction_byte_pins",
        "status": "frozen_locally_review_pending",
        "baseline_revision": BASELINE,
        "canonical_profile": "portable_protocols",
        "package_selection_owner": "Workspace authored profile; this record is not a package catalog",
        "envelope_sha256": ENVELOPE_SHA,
        "payload_sha256": PAYLOAD_SHA,
        "source_index_sha256": SOURCE_SHA,
        "public_delivery_authorized": False,
        "whole_envelope_required": True,
        "detached_wheels_accepted": False,
        "unassisted_onboarding_proven": False,
        "workspace_agent_mount_admitted": False,
        "files": rows,
    }


class Instructions(unittest.TestCase):
    def test_exact_instruction_bytes_and_negative_controls(self):
        record = json.loads((RELEASE / "INSTRUCTIONS.json").read_bytes())
        self.assertEqual(record, derive_instruction_record(ROOT))
        bodies = {name: (ROOT / name).read_bytes() for name in INSTRUCTIONS}
        proof = helper()
        proof.verify_instructions(record["files"], bodies)
        changed = dict(bodies)
        changed["protocols/WORKFLOW.md"] += b"\n"
        with self.assertRaisesRegex(ValueError, "instruction_bytes_changed"):
            proof.verify_instructions(record["files"], changed)
        changed.pop("README.md")
        with self.assertRaisesRegex(ValueError, "exact_instruction_set_required"):
            proof.verify_instructions(record["files"], changed)

    def test_exact_scope_and_unaffected_baseline_bytes_modes(self):
        rows = {}
        for line in git("ls-tree", "-r", BASELINE).decode().splitlines():
            meta, name = line.split("\t")
            mode, kind, oid = meta.split()
            self.assertEqual(kind, "blob")
            rows[name] = (mode, oid)
        actual = {
            str(p.relative_to(ROOT))
            for p in ROOT.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(ROOT).parts
        }
        self.assertEqual(actual, set(rows) | SCOPE)
        changed = actual - set(rows)
        for name, (mode, oid) in rows.items():
            path = ROOT / name
            self.assertFalse(path.is_symlink(), name)
            self.assertEqual(bool(path.stat().st_mode & 0o111), mode == "100755", name)
            before = git("cat-file", "blob", oid)
            if path.read_bytes() != before:
                changed.add(name)
            if name not in SCOPE:
                self.assertEqual(path.read_bytes(), before, name)
        self.assertEqual(changed, SCOPE)
        self.assertEqual(len(rows), 1339)
        self.assertEqual(len(actual), 1343)
        self.assertEqual(len(set(rows) - SCOPE), 1333)

    def test_artifacts_and_sole_package_selector_preserved(self):
        selected = json.loads((ROOT / "releases/SELECTED.json").read_bytes())
        before = json.loads(git("show", BASELINE + ":releases/SELECTED.json"))
        self.assertEqual(
            selected["instruction_status"], "frozen_locally_review_pending"
        )
        self.assertEqual(selected["selection_review"], "accepted_locally")
        self.assertEqual(
            selected["instruction_record"],
            "canonical-target-fit-fs-v1/INSTRUCTIONS.json",
        )
        for key in ("instruction_status", "instruction_record", "selection_review"):
            selected.pop(key, None)
            before.pop(key, None)
        self.assertEqual(selected, before)
        self.assertEqual(selected["canonical_profile"], "portable_protocols")
        self.assertFalse(selected["public_delivery_authorized"])
        self.assertFalse(selected["detached_wheels_accepted"])
        self.assertFalse(selected["workspace_agent_mount_admitted"])
        self.assertFalse(selected["unassisted_onboarding_proven"])
        self.assertNotIn("packages", selected)
        self.assertNotIn("packages", derive_instruction_record(ROOT))
        original = helper().original_test()
        original.Integration.test_whole_envelope_and_unsuppressed_findings(self)

    def test_supported_commands_and_target_fit_boundaries(self):
        root = (ROOT / "README.md").read_text()
        workflow = (ROOT / "protocols/WORKFLOW.md").read_text()
        before = git("show", BASELINE + ":README.md").decode()
        self.assertEqual(
            re.findall(r"```sh\n(.*?)```", root, re.DOTALL),
            re.findall(r"```sh\n(.*?)```", before, re.DOTALL),
        )
        self.assertNotIn("/bin/sh ./install.sh", workflow)
        for text in (root, workflow):
            self.assertIn("protocols/install.py", text)
            self.assertIn("--python-executable /usr/bin/python3.12", text)
            self.assertIn("pending independent", text)
            self.assertIn("not yet", text)
            self.assertIn("whole", text.lower())
            self.assertIn("docs/specs/json-checker/aware.spec.toml", text)
            self.assertIn("docs/specs/aware.spec.toml", text)
        for phrase in (
            "prospective_only",
            "completion_verified=false",
            "fresh Protocol admission",
            "never silent guard refresh",
            "normalized semantic identity",
            "absolute input paths",
            "six missing package-local",
            "not an atomic transaction",
            "live publication capability",
            "no draft-input custody",
            "preserve every remaining argument and reviewed guard",
            "no subsequent Issue/input observation",
            "not Issue eligibility",
            "aware workspace",
        ):
            self.assertIn(phrase, " ".join(workflow.split()))
        old_blocks = re.findall(
            r"```bash\n(.*?)```",
            git("show", BASELINE + ":protocols/WORKFLOW.md").decode(),
            re.DOTALL,
        )
        new_blocks = re.findall(r"```bash\n(.*?)```", workflow, re.DOTALL)
        self.assertEqual(
            new_blocks[1:],
            [
                block.replace(
                    "Set the absolute path of this expanded envelope",
                    "Set the exact retained_source_and_notices directory",
                )
                for block in old_blocks[1:]
            ],
        )
        self.assertEqual(
            (ROOT / "protocols/issues/FIRST-ISSUE.md").read_bytes(),
            git("show", BASELINE + ":protocols/issues/FIRST-ISSUE.md"),
        )

    def test_local_links_and_install_blocks_are_valid(self):
        helper().Instructions.test_local_links_and_install_blocks_are_valid(self)

    def test_documented_install_guards_refuse_existing_targets(self):
        helper().Instructions.test_documented_install_guards_refuse_existing_targets(
            self
        )

    def test_fresh_offline_install_and_documented_command_help(self):
        helper().Instructions.test_fresh_offline_install_and_documented_command_help(
            self
        )


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--instruction-record":
        print(json.dumps(derive_instruction_record(Path(sys.argv[2])), indent=2))
    else:
        unittest.main()
