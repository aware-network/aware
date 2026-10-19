"""A14 current status, historical-byte preservation and retained read checks."""

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(
    os.environ.get("AWARE_STATUS_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-a14-fs-v1"
BASELINE = "08a598fdeb8f960bf30fb8e85229e820286e67be"
HISTORICAL_SHA = "de665f59850205b62a1010dc506f9dd8d4932cde562d6cf6ccb40ebd81971bb1"
CURRENT = {
    "README.md",
    "protocols/WORKFLOW.md",
    "protocols/INIT.md",
    "protocols/workspace/README.md",
    "protocols/workspace/REVIEWED-SETUP.md",
    "protocols/workspace/REFERENCE-NAVIGATION.md",
    "protocols/workspace/RESOURCE-RELEASES.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/canonical-a14-fs-v1/README.md",
    "protocols/specification/README.md",
    "protocols/FIRST-USEFUL-TASK.md",
}
ISSUE = "docs/issues/2026/10/19/fb-2026-10-19-canonical-a14-public-status-v0.md"
SCOPE = CURRENT | {
    ISSUE,
    "releases/SELECTED.json",
    "releases/canonical-a14-fs-v1/PUBLIC-INSTRUCTIONS.json",
    "releases/canonical-a14-fs-v1/PUBLIC-STATUS.md",
    "releases/canonical-a14-fs-v1/test_public_status.py",
}


def sha(body):
    return hashlib.sha256(body).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def load(path, digest):
    if path.is_symlink() or sha(path.read_bytes()) != digest:
        raise ValueError("original_status_or_freeze_helper_required")
    spec = importlib.util.spec_from_file_location("a14_status_original", path)
    assert spec and spec.loader
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)
    return owner


def status_owner():
    owner = load(
        ROOT / "releases/canonical-human-evidence-fs-v1/test_public_status.py",
        "e2f8455da2fc84d80d5999c4bfec1c8e6689088998406fb932664bbde5fb186a",
    )
    owner.ROOT, owner.RELEASE, owner.BASELINE = ROOT, RELEASE, BASELINE
    owner.HISTORICAL_SHA = HISTORICAL_SHA
    return owner


def freeze():
    return load(
        RELEASE / "test_instruction_freeze.py",
        "0d16ba7dde8d85c089d4b64142742ed0ffba348c0b1371fd449abd40fce8801b",
    )


class PublicStatus(unittest.TestCase):
    def test_exact_pins_historical_bytes_and_negative_controls(self):
        self.assertEqual(
            sha((RELEASE / "INSTRUCTIONS.json").read_bytes()), HISTORICAL_SHA
        )
        record = json.loads((RELEASE / "PUBLIC-INSTRUCTIONS.json").read_bytes())
        self.assertEqual(record, status_owner().successor_record())
        self.assertEqual(len(record["files"]), 20)
        proof = freeze().original().helper()
        bodies = {name: (ROOT / name).read_bytes() for name in record["files"]}
        proof.verify_instructions(record["files"], bodies)
        bodies["README.md"] += b"\n"
        with self.assertRaisesRegex(ValueError, "instruction_bytes_changed"):
            proof.verify_instructions(record["files"], bodies)
        bodies.pop("protocols/workspace/RESOURCE-RELEASES.md")
        with self.assertRaisesRegex(ValueError, "exact_instruction_set_required"):
            proof.verify_instructions(record["files"], bodies)

    def test_exact_scope_unaffected_bytes_modes_and_issue(self):
        baseline = {}
        for row in git("ls-tree", "-rz", BASELINE).split(b"\0"):
            if not row:
                continue
            meta, name = row.split(b"\t", 1)
            mode, kind, oid = meta.decode().split()
            self.assertEqual(kind, "blob")
            baseline[name.decode()] = (mode, oid)
        actual = {
            str(p.relative_to(ROOT))
            for p in ROOT.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(ROOT).parts
        }
        self.assertEqual(actual, set(baseline) | SCOPE)
        changed = actual - set(baseline)
        for name, (mode, oid) in baseline.items():
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
            (len(baseline), len(actual), len(set(baseline) - SCOPE)), (1829, 1833, 1816)
        )
        section = (
            (ROOT / ISSUE)
            .read_text()
            .split("## Ownership Scope", 1)[1]
            .split("##", 1)[0]
        )
        self.assertEqual(
            set(re.findall(r"^- `([^`]+)`$", section, re.MULTILINE)), SCOPE
        )

    def test_pointer_no_new_authority_and_whole_envelope(self):
        before = json.loads(git("show", BASELINE + ":releases/SELECTED.json"))
        current = json.loads((ROOT / "releases/SELECTED.json").read_bytes())
        self.assertEqual(current["published_revision"], BASELINE)
        self.assertTrue(current["public_delivery_authorized"])
        self.assertFalse(current["instruction_alignment_publication_authorized"])
        self.assertEqual(
            current["instruction_status"], "status_alignment_review_pending"
        )
        self.assertEqual(
            current["instruction_record"],
            "canonical-a14-fs-v1/PUBLIC-INSTRUCTIONS.json",
        )
        for key in (
            "instruction_status",
            "instruction_record",
            "public_delivery_authorized",
            "published_revision",
            "instruction_alignment_publication_authorized",
        ):
            current.pop(key, None)
            before.pop(key, None)
        self.assertEqual(current, before)
        self.assertNotIn("packages", current)
        self.assertTrue(current["whole_envelope_required"])
        self.assertFalse(current["detached_wheels_accepted"])
        self.assertEqual(
            sha(
                (RELEASE / "canonical-a14-source-notice-review-v1.tar.gz").read_bytes()
            ),
            "050ed63545dd1d63c795285609e15dbdaa054c28788c9e5993e8a1871f356ea6",
        )

    def test_command_blocks_and_evaluation_limits(self):
        record = json.loads((RELEASE / "PUBLIC-INSTRUCTIONS.json").read_bytes())
        for name in record["files"]:
            before = git("show", BASELINE + ":" + name)
            body = (ROOT / name).read_bytes()
            if name.endswith((".py", ".json")):
                self.assertEqual(body, before, name)
            else:
                blocks = lambda b: re.findall(
                    rb"```(?:sh|bash|python)\n(.*?)```", b, re.DOTALL
                )
                self.assertEqual(blocks(body), blocks(before), name)
        marker = "## Inputs and configuration"
        self.assertEqual(
            (ROOT / "protocols/workspace/REVIEWED-SETUP.md")
            .read_text()
            .split(marker, 1)[1],
            git("show", BASELINE + ":protocols/workspace/REVIEWED-SETUP.md")
            .decode()
            .split(marker, 1)[1]
            .replace(
                "## Locally frozen a14 release evidence",
                "## Delivered a14 release evidence",
            )
            .replace(
                "The locally frozen [resource-summary guide]",
                "The delivered [resource-summary guide]",
            ),
        )
        task = (ROOT / "protocols/FIRST-USEFUL-TASK.md").read_text()
        for text in (
            "379cd5dcbe26c256be82c760b73fc100fdfc0fc6",
            "faed3f46668a3ec111d8fbf4cf1d5a287d5e1b89",
            "not a new evaluation of a14",
        ):
            self.assertIn(text, task)
        self.assertIn(BASELINE + "/protocols/INIT.md", task)
        status = (RELEASE / "PUBLIC-STATUS.md").read_text()
        for text in (
            "manual Issue guards",
            "not a new U/V/R",
            "positive create-first",
            "Whole-envelope delivery remains required",
            "not a live remote-status assertion",
            "No additional public push",
            "unknowns",
        ):
            self.assertIn(text, status)

    def test_delivery_revision_and_stale_wording_controls(self):
        owner = status_owner()
        for name in CURRENT:
            text = (ROOT / name).read_text()
            owner.verify_delivery_status(text)
            with self.assertRaisesRegex(ValueError, "published_revision_missing"):
                owner.verify_delivery_status(text.replace(BASELINE, "unknown_revision"))
            for stale in (
                "Public delivery is not yet authorized.",
                "Frozen locally pending independent review.",
                "Instructions remain draft.",
                "Use unchanged public main.",
            ):
                with self.assertRaisesRegex(ValueError, "stale_delivery_status"):
                    owner.verify_delivery_status(text + "\n" + stale)

    def test_links_and_shell_syntax(self):
        freeze().Instructions.test_local_links_and_shell_syntax(self)
        for name in (
            "docs/alignment/CURRENT.md",
            "releases/canonical-a14-fs-v1/PUBLIC-STATUS.md",
        ):
            for link in re.findall(r"\]\(([^)]+)\)", (ROOT / name).read_text()):
                freeze().original().helper().verify_local_link(ROOT / name, link)

    def test_original_existing_target_refusals(self):
        freeze().Instructions.test_documented_existing_target_refusals(self)

    def test_retained_installation_help_and_origins(self):
        freeze().Instructions.test_retained_installation_help_and_origins(self)


if __name__ == "__main__":
    unittest.main()
