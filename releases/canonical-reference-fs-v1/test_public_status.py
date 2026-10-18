"""A12 delivered-software status; original pin/status guards and retained reads."""

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
    os.environ.get("AWARE_STATUS_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-reference-fs-v1"
BASELINE = "f372cf75aaa228f059ab12e4095cec598e998541"
HISTORICAL_SHA = "3d1d836a501600cb5014f0cfe3d02baf8e4be835369c3dd7a0ab2032720b7188"
SCOPE = {
    "README.md",
    "protocols/WORKFLOW.md",
    "protocols/INIT.md",
    "protocols/workspace/README.md",
    "protocols/workspace/REVIEWED-SETUP.md",
    "protocols/workspace/REFERENCE-NAVIGATION.md",
    "protocols/specification/README.md",
    "protocols/FIRST-USEFUL-TASK.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/SELECTED.json",
    "releases/canonical-reference-fs-v1/README.md",
    "releases/canonical-reference-fs-v1/PUBLIC-INSTRUCTIONS.json",
    "releases/canonical-reference-fs-v1/PUBLIC-STATUS.md",
    "releases/canonical-reference-fs-v1/test_public_status.py",
    "docs/issues/2026/10/19/fb-2026-10-19-canonical-reference-public-status-v0.md",
}
CURRENT = {
    "README.md",
    "protocols/WORKFLOW.md",
    "protocols/INIT.md",
    "protocols/workspace/README.md",
    "protocols/workspace/REVIEWED-SETUP.md",
    "protocols/workspace/REFERENCE-NAVIGATION.md",
    "protocols/specification/README.md",
    "protocols/FIRST-USEFUL-TASK.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/canonical-reference-fs-v1/README.md",
}


def sha(body):
    return hashlib.sha256(body).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def load(path, digest):
    if path.is_symlink() or sha(path.read_bytes()) != digest:
        raise ValueError("original_status_or_freeze_helper_required")
    spec = importlib.util.spec_from_file_location("reference_status_original", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def original():
    module = load(
        ROOT / "releases/canonical-human-evidence-fs-v1/test_public_status.py",
        "e2f8455da2fc84d80d5999c4bfec1c8e6689088998406fb932664bbde5fb186a",
    )
    module.ROOT, module.RELEASE, module.BASELINE = ROOT, RELEASE, BASELINE
    module.HISTORICAL_SHA = HISTORICAL_SHA
    return module


def accepted_freeze():
    return load(
        RELEASE / "test_instruction_freeze.py",
        "d95407f9d0164d7f600996c0a81986eae6f14bd50c64e7f8f04d90bccde475b1",
    )


def successor_record():
    return original().successor_record()


class PublicStatus(unittest.TestCase):
    def test_historical_bytes_and_successor_pins(self):
        self.assertEqual(
            sha((RELEASE / "INSTRUCTIONS.json").read_bytes()), HISTORICAL_SHA
        )
        self.assertEqual(
            (RELEASE / "INSTRUCTIONS.json").read_bytes(),
            git(
                "show",
                BASELINE + ":releases/canonical-reference-fs-v1/INSTRUCTIONS.json",
            ),
        )
        record = json.loads((RELEASE / "PUBLIC-INSTRUCTIONS.json").read_bytes())
        self.assertEqual(record, successor_record())
        self.assertEqual(len(record["files"]), 19)
        proof = accepted_freeze().original().helper()
        bodies = {name: (ROOT / name).read_bytes() for name in record["files"]}
        proof.verify_instructions(record["files"], bodies)
        bodies["README.md"] += b"\n"
        with self.assertRaisesRegex(ValueError, "instruction_bytes_changed"):
            proof.verify_instructions(record["files"], bodies)
        bodies.pop("protocols/workspace/REFERENCE-NAVIGATION.md")
        with self.assertRaisesRegex(ValueError, "exact_instruction_set_required"):
            proof.verify_instructions(record["files"], bodies)

    def test_exact_scope_modes_and_unaffected_bytes(self):
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
            (len(rows), len(actual), len(set(rows) - SCOPE)), (1756, 1760, 1744)
        )
        issue = (
            ROOT
            / "docs/issues/2026/10/19/fb-2026-10-19-canonical-reference-public-status-v0.md"
        ).read_text()
        section = issue.split("## Ownership Scope", 1)[1].split("##", 1)[0]
        self.assertEqual(
            {
                x.strip()[3:-1]
                for x in section.splitlines()
                if x.strip().startswith("- `")
            },
            SCOPE,
        )

    def test_pointer_artifacts_and_no_new_authority(self):
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
            "canonical-reference-fs-v1/PUBLIC-INSTRUCTIONS.json",
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
        source = accepted_freeze().load(
            RELEASE / "test_local_integration.py",
            "e43c4a7d786930d2e88888a554d81028e6e1f4560f7220225661356e0820a7ee",
        )
        source.Integration.test_whole_envelope_and_raw_findings(self)

    def test_command_blocks_example_and_evaluation_limits(self):
        record = json.loads((RELEASE / "PUBLIC-INSTRUCTIONS.json").read_bytes())
        for name in record["files"]:
            before = git("show", BASELINE + ":" + name)
            body = (ROOT / name).read_bytes()
            if name.endswith((".py", ".json")):
                self.assertEqual(body, before, name)
            else:
                self.assertEqual(
                    re.findall(rb"```(?:sh|bash|python)\n(.*?)```", body, re.DOTALL),
                    re.findall(rb"```(?:sh|bash|python)\n(.*?)```", before, re.DOTALL),
                    name,
                )
        workflow = " ".join((ROOT / "protocols/WORKFLOW.md").read_text().split())
        for phrase in (
            "prospective_only",
            "completion_verified=false",
            "fresh Protocol admission",
            "not an atomic transaction",
            "not Issue eligibility",
        ):
            self.assertIn(phrase, workflow)
        navigation = (ROOT / "protocols/workspace/REFERENCE-NAVIGATION.md").read_text()
        self.assertIn("--reference-from-stdin", navigation)
        self.assertIn("does not automate Issue guard extraction", navigation)
        setup = (ROOT / "protocols/workspace/REVIEWED-SETUP.md").read_text()
        self.assertEqual(
            setup.split("## Inputs and configuration", 1)[1],
            git("show", BASELINE + ":protocols/workspace/REVIEWED-SETUP.md")
            .decode()
            .split("## Inputs and configuration", 1)[1],
        )
        task = (ROOT / "protocols/FIRST-USEFUL-TASK.md").read_text()
        self.assertIn("379cd5dcbe26c256be82c760b73fc100fdfc0fc6", task)
        self.assertIn("not a new evaluation", task)
        status = (RELEASE / "PUBLIC-STATUS.md").read_text()
        self.assertIn("not a new U/V/R", status)

    def test_status_missing_revision_and_stale_wording_controls(self):
        owner = original()
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
                with (
                    self.subTest(name=name, stale=stale),
                    self.assertRaisesRegex(ValueError, "stale_delivery_status"),
                ):
                    owner.verify_delivery_status(text + "\n" + stale)
        record = successor_record()
        self.assertTrue(record["public_delivery_authorized"])
        self.assertFalse(record["instruction_alignment_publication_authorized"])
        self.assertFalse(record["unassisted_onboarding_proven"])
        status = (RELEASE / "PUBLIC-STATUS.md").read_text()
        for phrase in (
            "not a live remote-status assertion",
            "not live remote state or",
            "Whole-envelope delivery remains required",
            "independent status-alignment review remains next",
            "No additional public push or U/V/R execution",
        ):
            self.assertIn(phrase, status)

    def test_links_and_shell_syntax(self):
        freeze = accepted_freeze()
        freeze.Instructions.test_local_links_and_shell_syntax(self)
        for name in (
            "docs/alignment/CURRENT.md",
            "releases/canonical-reference-fs-v1/PUBLIC-STATUS.md",
        ):
            for link in re.findall(r"\]\(([^)]+)\)", (ROOT / name).read_text()):
                freeze.original().helper().verify_local_link(ROOT / name, link)

    def test_original_existing_target_refusals(self):
        accepted_freeze().Instructions.test_documented_existing_target_refusals(self)

    def test_retained_readonly_versions_help_and_origins(self):
        accepted_freeze().Instructions.test_retained_installation_help_and_origins(self)


if __name__ == "__main__":
    if "--print-instruction-record" in sys.argv:
        print(json.dumps(successor_record(), sort_keys=True, indent=2))
    else:
        unittest.main()
