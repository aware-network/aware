"""A12 current guidance pins and retained reads; no installation or authority."""

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path
from types import FunctionType

ROOT = Path(
    os.environ.get("AWARE_FREEZE_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-reference-fs-v1"
BASELINE = "bff896efd1839eef5d0bd207a2ab93637e8bba45"
ENVELOPE_SHA = "afca86cad0fe96c40250819a37b3ab7284236b30d12db919e6596c2aae6a9d30"
PAYLOAD_SHA = "8c804765c0aae2ee8ffe72768158867eab29dae93c669ec6c259421103eaf0e8"
SOURCE_SHA = "19497ad59946415d7edc737381735e9f666ec74884275d4d3ec7688924c38113"
ISSUE = (
    "docs/issues/2026/10/19/fb-2026-10-19-canonical-reference-instruction-freeze-v0.md"
)
INSTRUCTIONS = {
    "README.md",
    "protocols/README.md",
    "protocols/COHERENCE.md",
    "protocols/INITIALIZATION.md",
    "protocols/INIT.md",
    "protocols/WORKFLOW.md",
    "protocols/issues/README.md",
    "protocols/issues/FIRST-ISSUE.md",
    "protocols/repository/README.md",
    "protocols/specification/README.md",
    "protocols/workspace/README.md",
    "protocols/workspace/REVIEWED-SETUP.md",
    "protocols/workspace/REFERENCE-NAVIGATION.md",
    "protocols/FIRST-USEFUL-TASK.md",
    "protocols/tasks/JSON-CHECKER.md",
    "protocols/EVIDENCE-MAP.json",
    "workspaces/aware_kernel/modules/specification/sdks/specification/python/cli/examples/prepare_draft_input.py",
    "releases/README.md",
    "releases/canonical-reference-fs-v1/README.md",
}
SCOPE = {
    ISSUE,
    "README.md",
    "protocols/WORKFLOW.md",
    "protocols/INIT.md",
    "protocols/workspace/README.md",
    "protocols/workspace/REVIEWED-SETUP.md",
    "protocols/workspace/REFERENCE-NAVIGATION.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/SELECTED.json",
    "releases/canonical-reference-fs-v1/README.md",
    "releases/canonical-reference-fs-v1/INSTRUCTIONS.json",
    "releases/canonical-reference-fs-v1/INSTRUCTION-FREEZE.md",
    "releases/canonical-reference-fs-v1/test_instruction_freeze.py",
}


def sha(body):
    return hashlib.sha256(body).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def load(path, digest):
    if path.is_symlink() or sha(path.read_bytes()) != digest:
        raise ValueError("original_instruction_helper_required")
    spec = importlib.util.spec_from_file_location("reference_original_freeze", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def original():
    module = load(
        ROOT / "releases/canonical-init-summary-fs-v1/test_instruction_freeze.py",
        "4b7e470c217a0eeba87c7a02850e214c97060660858e35414131d19c74edcebc",
    )
    module.ROOT, module.RELEASE, module.BASELINE = ROOT, RELEASE, BASELINE
    module.ENVELOPE_SHA, module.PAYLOAD_SHA, module.SOURCE_SHA = (
        ENVELOPE_SHA,
        PAYLOAD_SHA,
        SOURCE_SHA,
    )
    module.INSTRUCTIONS = INSTRUCTIONS
    return module


def derive_instruction_record(root):
    module = original()
    function = module.derive_instruction_record
    replacements = {
        "releases/canonical-init-summary-fs-v1": "releases/canonical-reference-fs-v1",
        "canonical-init-summary-source-notice-review-v1.tar.gz": "canonical-reference-source-notice-review-v1.tar.gz",
    }
    if not set(replacements).issubset(function.__code__.co_consts):
        raise ValueError("original_instruction_coordinates_required")
    bound = FunctionType(
        function.__code__.replace(
            co_consts=tuple(
                replacements.get(c, c) if isinstance(c, str) else c
                for c in function.__code__.co_consts
            )
        ),
        function.__globals__,
    )
    assert bound.__code__.co_code == function.__code__.co_code
    return bound(root)


class Instructions(unittest.TestCase):
    def test_exact_pins_and_original_negative_controls(self):
        record = json.loads((RELEASE / "INSTRUCTIONS.json").read_bytes())
        self.assertEqual(record, derive_instruction_record(ROOT))
        self.assertEqual(len(record["files"]), 19)
        proof = original().helper()
        bodies = {name: (ROOT / name).read_bytes() for name in INSTRUCTIONS}
        proof.verify_instructions(record["files"], bodies)
        changed = dict(bodies)
        changed["protocols/workspace/REFERENCE-NAVIGATION.md"] += b"\n"
        with self.assertRaisesRegex(ValueError, "instruction_bytes_changed"):
            proof.verify_instructions(record["files"], changed)
        changed.pop("README.md")
        with self.assertRaisesRegex(ValueError, "exact_instruction_set_required"):
            proof.verify_instructions(record["files"], changed)

    def test_exact_scope_conservation_and_issue_guard_boundary(self):
        rows = {}
        for line in git("ls-tree", "-r", BASELINE).decode().splitlines():
            meta, name = line.split("\t", 1)
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
        self.assertEqual(
            (len(rows), len(actual), len(set(rows) - SCOPE)), (1752, 1756, 1742)
        )
        section = (
            (ROOT / ISSUE)
            .read_text()
            .split("## Ownership Scope", 1)[1]
            .split("##", 1)[0]
        )
        self.assertEqual(
            {
                line.strip()[3:-1]
                for line in section.splitlines()
                if line.strip().startswith("- `")
            },
            SCOPE,
        )

    def test_artifacts_pointer_and_historical_records_preserved(self):
        current = json.loads((ROOT / "releases/SELECTED.json").read_bytes())
        before = json.loads(git("show", BASELINE + ":releases/SELECTED.json"))
        self.assertEqual(current["instruction_status"], "frozen_locally_review_pending")
        self.assertEqual(current["selection_review"], "accepted_locally")
        self.assertEqual(
            current["instruction_record"], "canonical-reference-fs-v1/INSTRUCTIONS.json"
        )
        for key in ("instruction_status", "instruction_record", "selection_review"):
            current.pop(key, None)
            before.pop(key, None)
        self.assertEqual(current, before)
        self.assertFalse(current["public_delivery_authorized"])
        self.assertNotIn("packages", current)
        source = load(
            RELEASE / "test_local_integration.py",
            "e43c4a7d786930d2e88888a554d81028e6e1f4560f7220225661356e0820a7ee",
        )
        source.Integration.test_whole_envelope_and_raw_findings(self)
        for key in (
            "activation_included_in_this_delivery",
            "tooling_activation_performed",
            "a2_admitted",
            "tree_completion_admitted",
        ):
            self.assertFalse(derive_instruction_record(ROOT)[key])

    def test_current_guidance_and_unchanged_command_blocks(self):
        for name in INSTRUCTIONS:
            if name.endswith(".md"):
                before = git("show", BASELINE + ":" + name).decode()
                after = (ROOT / name).read_text()
                self.assertEqual(
                    re.findall(r"```(?:sh|bash)\n(.*?)```", before, re.DOTALL),
                    re.findall(r"```(?:sh|bash)\n(.*?)```", after, re.DOTALL),
                    name,
                )
        for name in (
            "README.md",
            "protocols/WORKFLOW.md",
            "protocols/INIT.md",
            "protocols/workspace/README.md",
            "protocols/workspace/REVIEWED-SETUP.md",
            "protocols/workspace/REFERENCE-NAVIGATION.md",
            "docs/alignment/CURRENT.md",
            "releases/README.md",
            "releases/canonical-reference-fs-v1/README.md",
        ):
            text = " ".join((ROOT / name).read_text().split())
            self.assertIn("frozen locally pending independent", text, name)
            self.assertIn("public delivery is not yet authorized", text, name)
            self.assertNotIn("prepared, unselected", text, name)
            self.assertNotIn("Instructions remain draft", text, name)
        guide = (ROOT / "protocols/workspace/REFERENCE-NAVIGATION.md").read_text()
        self.assertIn("--reference-from-stdin", guide)
        self.assertIn(
            "no current-use authority", " ".join(guide.replace("**", "").split())
        )
        self.assertIn("does not automate Issue guard extraction", guide)
        workflow = " ".join((ROOT / "protocols/WORKFLOW.md").read_text().split())
        for phrase in (
            "prospective_only",
            "completion_verified=false",
            "fresh Protocol admission",
            "not Issue eligibility",
            "not an atomic transaction",
        ):
            self.assertIn(phrase, workflow)
        setup = (ROOT / "protocols/workspace/REVIEWED-SETUP.md").read_text()
        for flag in ("--accept-reviewed-effect-scope", "--accept-reviewed-final-files"):
            self.assertIn(flag, setup)
        for name in (
            "protocols/FIRST-USEFUL-TASK.md",
            "protocols/tasks/JSON-CHECKER.md",
            "protocols/issues/FIRST-ISSUE.md",
            "protocols/EVIDENCE-MAP.json",
        ):
            self.assertEqual(
                (ROOT / name).read_bytes(), git("show", BASELINE + ":" + name)
            )

    def test_local_links_and_shell_syntax(self):
        original().helper().Instructions.test_local_links_and_install_blocks_are_valid(
            self
        )

    def test_documented_existing_target_refusals(self):
        original().helper().Instructions.test_documented_install_guards_refuse_existing_targets(
            self
        )

    def test_retained_installation_help_and_origins(self):
        source = load(
            RELEASE / "test_local_integration.py",
            "e43c4a7d786930d2e88888a554d81028e6e1f4560f7220225661356e0820a7ee",
        )
        source.Integration.test_original_retained_installation_reads(self)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--instruction-record":
        print(
            json.dumps(
                derive_instruction_record(Path(sys.argv[2])), sort_keys=True, indent=2
            )
        )
    else:
        unittest.main()
