"""Receive accepted onboarding documents and pin guidance, not runtime authority."""

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
    os.environ.get("AWARE_ONBOARDING_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-workspace-a1-fs-v1"
BASELINE = "0b1e027ef3a3fba8d8c6a124adb7bc027030898e"
STATUS_SHA = "79fe4455d1720912c98255574f7063dea788d6086867d295441243085c283db8"
PROOF_SHA = "06d244e5eb489ef8410687c51028dcf03a1b91872e330af94b7c437f11aad86a"
GUIDE = "protocols/workspace/FIRST-SETUP.md"
ACCEPTED = {
    "protocols/WORKFLOW.md": "6469aac7b905392df2ab81e63ef8d7ba8d3c3cad17486b3753ceab318f93b060",
    "protocols/issues/FIRST-ISSUE.md": "6a006c9bdc86fdbc4baf618de9db799b804c8486b760f92d9a0221fd79f12873",
    "protocols/workspace/README.md": "d7e3c8845a418c9286c393e6d9c1abe116511c583c9a26c3f9a4c3b83eb0bd22",
    GUIDE: "42155f5b152a4ccb0c7a2a09a9a5e73beeb60d08bb89de1b8c6139615e372067",
}
SCOPE = {
    "protocols/WORKFLOW.md",
    "protocols/issues/FIRST-ISSUE.md",
    "protocols/workspace/README.md",
    "protocols/workspace/FIRST-SETUP.md",
    "README.md",
    "releases/canonical-workspace-a1-fs-v1/README.md",
    "releases/SELECTED.json",
    "releases/canonical-workspace-a1-fs-v1/ONBOARDING-INSTRUCTIONS.json",
    "releases/canonical-workspace-a1-fs-v1/ONBOARDING-INTEGRATION.md",
    "releases/canonical-workspace-a1-fs-v1/test_onboarding_integration.py",
    "docs/issues/2026/10/16/fb-2026-10-16-canonical-workspace-a1-onboarding-integration-v0.md",
}


def sha(body):
    return hashlib.sha256(body).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def retained():
    path = RELEASE / "test_public_status.py"
    if sha(path.read_bytes()) != PROOF_SHA:
        raise ValueError("accepted_status_proof_changed")
    spec = importlib.util.spec_from_file_location("retained_a1_status", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def successor_record():
    historical = (RELEASE / "PUBLIC-INSTRUCTIONS.json").read_bytes()
    if sha(historical) != STATUS_SHA:
        raise ValueError("historical_status_record_changed")
    record = json.loads(historical)
    names = set(record["files"]) | {GUIDE}
    if len(names) != 14:
        raise ValueError("fourteen_instruction_paths_required")
    record.update(
        status="onboarding_integration_review_pending",
        baseline_revision=BASELINE,
        previous_instruction_sha256=STATUS_SHA,
        onboarding_instruction_publication_authorized=False,
        accepted_preparation_revision="a01eb13020c66cd2dc4dcff2bc95ae22b3eb4311",
        accepted_document_sha256=ACCEPTED,
        software_changed=False,
    )
    record["files"] = {
        name: {"bytes": len(body), "sha256": sha(body)}
        for name, body in ((name, (ROOT / name).read_bytes()) for name in sorted(names))
    }
    return record


class Onboarding(unittest.TestCase):
    def test_four_accepted_postimages_exact(self):
        for name, digest in ACCEPTED.items():
            path = ROOT / name
            self.assertFalse(path.is_symlink(), name)
            self.assertEqual(sha(path.read_bytes()), digest, name)
            self.assertTrue(path.is_file(), name)
            self.assertFalse(path.stat().st_mode & 0o111, name)

    def test_fourteen_pins_and_history_preserved(self):
        record = json.loads((RELEASE / "ONBOARDING-INSTRUCTIONS.json").read_bytes())
        self.assertEqual(record, successor_record())
        for name in (
            "INSTRUCTIONS.json",
            "PUBLIC-INSTRUCTIONS.json",
            "INSTRUCTION-FREEZE.md",
            "PUBLIC-STATUS.md",
        ):
            self.assertEqual(
                (RELEASE / name).read_bytes(),
                git(
                    "show", BASELINE + ":releases/canonical-workspace-a1-fs-v1/" + name
                ),
            )
        helper = retained().accepted_freeze().helper()
        helper.INSTRUCTIONS = set(record["files"])
        bodies = {name: (ROOT / name).read_bytes() for name in record["files"]}
        helper.verify_instructions(record["files"], bodies)
        changed = dict(bodies)
        changed[GUIDE] += b"\n"
        with self.assertRaisesRegex(ValueError, "instruction_bytes_changed"):
            helper.verify_instructions(record["files"], changed)
        changed.pop(GUIDE)
        with self.assertRaisesRegex(ValueError, "exact_instruction_set_required"):
            helper.verify_instructions(record["files"], changed)

    def test_exact_scope_unaffected_bytes_and_modes(self):
        rows = {}
        for line in git("ls-tree", "-r", BASELINE).decode().splitlines():
            metadata, name = line.split("\t")
            mode, kind, oid = metadata.split()
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
        self.assertEqual(len(rows), 1512)
        self.assertEqual(len(actual), 1517)
        self.assertEqual(len(set(rows) - SCOPE), 1506)

    def test_delivery_pointer_and_complete_carriage(self):
        before = json.loads(git("show", BASELINE + ":releases/SELECTED.json"))
        current = json.loads((ROOT / "releases/SELECTED.json").read_bytes())
        self.assertEqual(
            current["instruction_record"],
            "canonical-workspace-a1-fs-v1/ONBOARDING-INSTRUCTIONS.json",
        )
        self.assertEqual(
            current["instruction_status"], "onboarding_integration_review_pending"
        )
        self.assertFalse(current["onboarding_instruction_publication_authorized"])
        for name in (
            "instruction_record",
            "instruction_status",
            "onboarding_instruction_publication_authorized",
        ):
            current.pop(name, None)
            before.pop(name, None)
        self.assertEqual(current, before)
        self.assertEqual(current["canonical_profile"], "portable_protocols")
        self.assertFalse(current["unassisted_onboarding_proven"])
        self.assertTrue(current["whole_envelope_required"])
        self.assertTrue(current["a1_prepared_owner_inputs_required"])
        self.assertFalse(current["a2_admitted"])
        self.assertFalse(current["tree_c_completion_admitted"])
        retained().accepted_freeze().helper().original_test().Integration.test_whole_envelope_and_unsuppressed_findings(
            self
        )

    def test_operation_blocks_and_bounded_guidance(self):
        record = successor_record()
        for name in set(record["files"]) - {GUIDE}:
            before = git("show", BASELINE + ":" + name)
            current = (ROOT / name).read_bytes()
            blocks = lambda body: re.findall(
                rb"```(?:sh|bash|python)\n(.*?)```", body, re.DOTALL
            )
            if name.endswith(".py"):
                self.assertEqual(current, before, name)
            else:
                self.assertEqual(blocks(current), blocks(before), name)
        guide = (ROOT / GUIDE).read_text()
        self.assertEqual(len(re.findall(r"```bash\n(.*?)\n```", guide, re.DOTALL)), 4)
        for phrase in (
            "a1_reviewed_scope",
            "a1_reviewed_files",
            "primary_path, *step.auxiliary_paths",
            "binding.file_transitions",
            "Stop here.",
            "Stop again.",
            "No automatic refresh",
            "This example does not commit/close",
        ):
            self.assertIn(phrase, guide)
        result = subprocess.run(
            ["bash", "-n"],
            input="\n".join(re.findall(r"```bash\n(.*?)\n```", guide, re.DOTALL)),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_links_and_local_review_boundary(self):
        freeze = retained().accepted_freeze()
        freeze.Instructions.test_local_links_and_install_blocks_are_valid(self)
        helper = freeze.helper()
        for name in (
            *ACCEPTED,
            "releases/canonical-workspace-a1-fs-v1/README.md",
            "releases/canonical-workspace-a1-fs-v1/ONBOARDING-INTEGRATION.md",
        ):
            source = ROOT / name
            for link in re.findall(r"\]\(([^)]+)\)", source.read_text()):
                helper.verify_local_link(source, link)
        root = (ROOT / "README.md").read_text()
        self.assertIn("ONBOARDING-INSTRUCTIONS.json", root)
        self.assertIn("ONBOARDING-INTEGRATION.md", root)
        self.assertIn("separate review and delivery status", root)
        self.assertIn("example creates only", root)

    def test_original_install_guards(self):
        retained().PublicStatus.test_original_executable_install_guards(self)

    def test_fresh_offline_install_and_original_help(self):
        retained().PublicStatus.test_fresh_offline_install_and_eleven_help_entrances(
            self
        )


if __name__ == "__main__":
    if "--print-instruction-record" in sys.argv:
        print(json.dumps(successor_record(), indent=2) + "\n", end="")
    else:
        unittest.main()
