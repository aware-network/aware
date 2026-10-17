"""Pin refusal-successor guidance; reuse accepted installer proofs, not domain policy."""

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
RELEASE = ROOT / "releases/canonical-refusal-successor-fs-v1"
BASELINE = "af25f6f6e3a2586bb05e7d6c893f7f9a2a4612d3"
ENVELOPE_SHA = "e96946272b7812e833d41370ec5bfbba722f2f6f91720f994abcf9f407c975f7"
PAYLOAD_SHA = "34c3c9d16d5bec1aba75add5ce03e55d32b25c828da78e878288b19453d6a51c"
SOURCE_SHA = "9b6dcbc7b5a6f05a9ef6ab207de79f3788ca4fe92f03c8857a1a27b4d815ee34"
ORIGINAL_TEST_SHA = "b2c47206babe628074d04728c25149faebf28d116eb7d86a8920c96bc7b47fc1"
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
    "workspaces/aware_kernel/modules/specification/sdks/specification/python/cli/examples/prepare_draft_input.py",
    "protocols/workspace/README.md",
    "protocols/workspace/REVIEWED-SETUP.md",
    "releases/README.md",
    "releases/canonical-refusal-successor-fs-v1/README.md",
}
SCOPE = {
    "README.md",
    "protocols/WORKFLOW.md",
    "protocols/specification/README.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/SELECTED.json",
    "releases/canonical-refusal-successor-fs-v1/README.md",
    "releases/canonical-refusal-successor-fs-v1/INSTRUCTIONS.json",
    "releases/canonical-refusal-successor-fs-v1/INSTRUCTION-FREEZE.md",
    "releases/canonical-refusal-successor-fs-v1/test_instruction_freeze.py",
    "docs/issues/2026/10/18/fb-2026-10-18-canonical-refusal-successor-instruction-freeze-v0.md",
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
    release = root / "releases/canonical-refusal-successor-fs-v1"
    for name, digest in (
        ("SOURCE-INDEX.json", SOURCE_SHA),
        ("canonical-refusal-successor-source-notice-review-v1.tar.gz", ENVELOPE_SHA),
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
        "catalog_revision": json.loads((release / "SOURCE-INDEX.json").read_bytes())[
            "catalog_revision"
        ],
        "source_is_composite": True,
        "package_selection_owner": "Workspace authored profile; this record is not a package catalog",
        "envelope_sha256": ENVELOPE_SHA,
        "payload_sha256": PAYLOAD_SHA,
        "source_index_sha256": SOURCE_SHA,
        "public_delivery_authorized": False,
        "whole_envelope_required": True,
        "detached_wheels_accepted": False,
        "unassisted_onboarding_proven": False,
        "workspace_agent_mount_admitted": True,
        "workspace_mount_profile": "bounded-reviewed-repository-manifest-a1",
        "init_supplies_configuration_not_admission": True,
        "a2_admitted": False,
        "tree_completion_admitted": False,
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
        self.assertEqual(len(rows), 1634)
        self.assertEqual(len(actual), 1638)
        self.assertEqual(len(set(rows) - SCOPE), 1627)

    def test_artifacts_and_sole_package_selector_preserved(self):
        selected = json.loads((ROOT / "releases/SELECTED.json").read_bytes())
        before = json.loads(git("show", BASELINE + ":releases/SELECTED.json"))
        self.assertEqual(
            selected["instruction_status"], "frozen_locally_review_pending"
        )
        self.assertEqual(selected["selection_review"], "accepted_locally")
        self.assertEqual(
            selected["instruction_record"],
            "canonical-refusal-successor-fs-v1/INSTRUCTIONS.json",
        )
        for key in ("instruction_status", "instruction_record", "selection_review"):
            selected.pop(key, None)
            before.pop(key, None)
        self.assertEqual(selected, before)
        self.assertEqual(selected["canonical_profile"], "portable_protocols")
        self.assertFalse(selected["public_delivery_authorized"])
        self.assertFalse(selected["detached_wheels_accepted"])
        self.assertTrue(selected["workspace_agent_mount_admitted"])
        self.assertTrue(selected["init_supplies_configuration_not_admission"])
        self.assertEqual(
            selected["workspace_mount_profile"],
            "bounded-reviewed-repository-manifest-a1",
        )
        self.assertFalse(selected["a2_admitted"])
        self.assertFalse(selected["tree_completion_admitted"])
        self.assertFalse(selected["unassisted_onboarding_proven"])
        self.assertNotIn("packages", selected)
        self.assertNotIn("packages", derive_instruction_record(ROOT))
        original = helper().original_test()
        original.Integration.test_whole_envelope_and_unsuppressed_findings(self)

    def test_supported_commands_and_target_fit_boundaries(self):
        root = (ROOT / "README.md").read_text()
        workflow = (ROOT / "protocols/WORKFLOW.md").read_text()
        for name in ("README.md", "protocols/WORKFLOW.md"):
            before = git("show", BASELINE + ":" + name).decode()
            current = (ROOT / name).read_text()
            self.assertEqual(
                re.findall(r"```(?:sh|bash)\n(.*?)```", current, re.DOTALL),
                re.findall(r"```(?:sh|bash)\n(.*?)```", before, re.DOTALL),
            )
            self.assertIn("protocols/install.py", current)
            self.assertIn("--python-executable /usr/bin/python3.12", current)
            self.assertIn("pending independent", current)
            self.assertIn("not yet", current)
            self.assertIn("whole", current.lower())
        for phrase in (
            "prospective_only",
            "completion_verified=false",
            "fresh Protocol admission",
            "never silent guard refresh",
            "normalized semantic identity",
            "absolute input paths",
            "not an atomic transaction",
            "live publication capability",
            "no draft-input custody",
            "preserve every remaining argument and reviewed guard",
            "no subsequent Issue/input observation",
            "not Issue eligibility",
            "docs/specs/json-checker/aware.spec.toml",
            "docs/specs/aware.spec.toml",
        ):
            self.assertIn(phrase, " ".join(workflow.split()))
        for phrase in (
            "does not admit an Issue",
            "not two admitted owner plans",
            "Original release uncertainty",
            "not unassisted onboarding",
            "Clean stale Issue/authority refusals exit 2",
            "Spent-reference incompleteness remains 3",
            "interruptions remain 130",
        ):
            self.assertIn(phrase, " ".join(root.split()))
        guide = (ROOT / "protocols/workspace/REVIEWED-SETUP.md").read_bytes()
        self.assertEqual(
            guide, git("show", BASELINE + ":protocols/workspace/REVIEWED-SETUP.md")
        )
        for flag in ("--accept-reviewed-effect-scope", "--accept-reviewed-final-files"):
            self.assertIn(flag, guide.decode())
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
