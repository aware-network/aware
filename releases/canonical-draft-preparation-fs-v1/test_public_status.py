"""Status-only delivery guidance checks reuse the accepted installation proof."""

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
    os.environ.get("AWARE_STATUS_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-draft-preparation-fs-v1"
BASELINE = "2b0194bcde2643f04886e309d08587cde71dfd24"
HISTORICAL_SHA = "fa8fc5d11cb2413d0459734eae3ff566bbd64f1373ca0a5a1ba6418681b24593"
FREEZE_TEST_SHA = "3bd2808fbec5be1f6f850e98050440ede14539987bd55115022c560253002495"
SCOPE = {
    "README.md",
    "protocols/WORKFLOW.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/SELECTED.json",
    "releases/canonical-draft-preparation-fs-v1/README.md",
    "releases/canonical-draft-preparation-fs-v1/PUBLIC-INSTRUCTIONS.json",
    "releases/canonical-draft-preparation-fs-v1/PUBLIC-STATUS.md",
    "releases/canonical-draft-preparation-fs-v1/test_public_status.py",
    "docs/issues/2026/10/11/fb-2026-10-11-canonical-draft-preparation-public-status-v0.md",
}


def sha(body):
    return hashlib.sha256(body).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def accepted_freeze():
    path = RELEASE / "test_instruction_freeze.py"
    if sha(path.read_bytes()) != FREEZE_TEST_SHA:
        raise ValueError("accepted_freeze_proof_changed")
    spec = importlib.util.spec_from_file_location("accepted_draft_freeze", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def successor_record():
    """Print-only pin derivation; never writes instructions or selects packages."""
    historical = (RELEASE / "INSTRUCTIONS.json").read_bytes()
    if sha(historical) != HISTORICAL_SHA:
        raise ValueError("historical_instruction_record_changed")
    record = json.loads(historical)
    record.update(
        status="status_alignment_review_pending",
        baseline_revision=BASELINE,
        published_software_revision=BASELINE,
        historical_instruction_sha256=HISTORICAL_SHA,
        public_delivery_authorized=True,
        instruction_alignment_publication_authorized=False,
    )
    record["files"] = {
        name: {"bytes": len(body), "sha256": sha(body)}
        for name, body in (
            (name, (ROOT / name).read_bytes()) for name in record["files"]
        )
    }
    return record


def verify_delivery_status(text):
    normalized = " ".join(text.lower().split())
    if BASELINE not in text:
        raise ValueError("published_revision_missing")
    for stale in (
        "public delivery is not yet authorized",
        "not publicly delivered",
        "unchanged public main",
        "frozen locally pending independent",
    ):
        if stale in normalized:
            raise ValueError("stale_delivery_status:" + stale)


class PublicStatus(unittest.TestCase):
    def test_historical_record_and_exact_successor_pins(self):
        self.assertEqual(
            (RELEASE / "INSTRUCTIONS.json").read_bytes(),
            git(
                "show",
                BASELINE
                + ":releases/canonical-draft-preparation-fs-v1/INSTRUCTIONS.json",
            ),
        )
        record = json.loads((RELEASE / "PUBLIC-INSTRUCTIONS.json").read_bytes())
        self.assertEqual(record, successor_record())
        freeze = accepted_freeze()
        bodies = {name: (ROOT / name).read_bytes() for name in record["files"]}
        freeze.verify_instructions(record["files"], bodies)
        bodies["README.md"] += b"\n"
        with self.assertRaisesRegex(ValueError, "instruction_bytes_changed"):
            freeze.verify_instructions(record["files"], bodies)

    def test_exact_scope_unaffected_bytes_and_modes(self):
        baseline = {}
        for line in git("ls-tree", "-r", BASELINE).decode().splitlines():
            meta, name = line.split("\t")
            mode, kind, oid = meta.split()
            self.assertEqual(kind, "blob")
            baseline[name] = (mode, oid)
        actual = {
            str(path.relative_to(ROOT))
            for path in ROOT.rglob("*")
            if path.is_file() and ".git" not in path.relative_to(ROOT).parts
        }
        self.assertEqual(actual, set(baseline) | SCOPE)
        changed = actual - set(baseline)
        for name, (mode, oid) in baseline.items():
            path = ROOT / name
            self.assertFalse(path.is_symlink(), name)
            self.assertEqual(bool(path.stat().st_mode & 0o111), mode == "100755", name)
            original = git("cat-file", "blob", oid)
            if path.read_bytes() != original:
                changed.add(name)
            if name not in SCOPE:
                self.assertEqual(path.read_bytes(), original, name)
        self.assertEqual(changed, SCOPE)
        self.assertEqual(len(baseline), 1208)
        self.assertEqual(len(actual), 1212)
        self.assertEqual(len(set(baseline) - SCOPE), 1202)

    def test_unchanged_candidate_carriage_and_sole_selector(self):
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
            "canonical-draft-preparation-fs-v1/PUBLIC-INSTRUCTIONS.json",
        )
        for key in (
            "selection_kind",
            "instruction_status",
            "instruction_record",
            "public_delivery_authorized",
            "published_revision",
            "instruction_alignment_publication_authorized",
        ):
            current.pop(key, None)
            before.pop(key, None)
        self.assertEqual(current, before)
        self.assertEqual(current["canonical_profile"], "portable_protocols")
        self.assertFalse(current["detached_wheels_accepted"])
        self.assertFalse(current["contributor_selection_changed"])
        self.assertFalse(current["unassisted_onboarding_proven"])
        self.assertNotIn("packages", current)
        freeze = accepted_freeze()
        freeze.original_test().Integration.test_whole_envelope_and_unsuppressed_findings(
            self
        )

    def test_operation_blocks_and_example_are_unchanged(self):
        record = json.loads((RELEASE / "PUBLIC-INSTRUCTIONS.json").read_bytes())
        for name in record["files"]:
            before = git("show", BASELINE + ":" + name)
            current = (ROOT / name).read_bytes()
            if name.endswith(".py"):
                self.assertEqual(current, before, name)
            else:
                blocks = lambda body: re.findall(
                    rb"```(?:sh|bash|python)\n(.*?)```", body, re.DOTALL
                )
                self.assertEqual(blocks(current), blocks(before), name)
        workflow = (ROOT / "protocols/WORKFLOW.md").read_text()
        for phrase in (
            "prospective_only",
            "completion_verified=false",
            "fresh Protocol admission",
            "absolute input paths",
            "never silent guard refresh",
            "not an atomic transaction",
            "live publication capability",
            "no draft-input custody",
            "preserve every remaining argument and reviewed guard",
        ):
            self.assertIn(phrase, " ".join(workflow.split()))
        self.assertIn("unassisted", (ROOT / "README.md").read_text())

    def test_status_matches_observed_delivery_without_new_authority(self):
        for name in (
            "README.md",
            "protocols/WORKFLOW.md",
            "docs/alignment/CURRENT.md",
            "releases/README.md",
            "releases/canonical-draft-preparation-fs-v1/README.md",
        ):
            text = (ROOT / name).read_text()
            verify_delivery_status(text)
            original = git("show", BASELINE + ":" + name).decode()
            with self.assertRaisesRegex(ValueError, "stale_delivery_status"):
                verify_delivery_status(original + "\n" + BASELINE)
            with self.assertRaisesRegex(ValueError, "published_revision_missing"):
                verify_delivery_status(text.replace(BASELINE, "unknown_revision"))
        record = json.loads((RELEASE / "PUBLIC-INSTRUCTIONS.json").read_bytes())
        self.assertFalse(record["instruction_alignment_publication_authorized"])
        self.assertFalse(record["unassisted_onboarding_proven"])
        ledger = (RELEASE / "PUBLIC-STATUS.md").read_text()
        self.assertIn("independent status-alignment review remains next", ledger)
        self.assertIn("No additional public push or U/V/R execution", ledger)
        self.assertIn("Whole-envelope delivery remains required", ledger)

    def test_links_fragments_and_shell_syntax(self):
        freeze = accepted_freeze()
        freeze.Instructions.test_local_links_and_install_blocks_are_valid(self)
        for name in (
            "docs/alignment/CURRENT.md",
            "releases/canonical-draft-preparation-fs-v1/PUBLIC-STATUS.md",
        ):
            source = ROOT / name
            for link in re.findall(r"\]\(([^)]+)\)", source.read_text()):
                freeze.verify_local_link(source, link)

    def test_original_executable_install_guards(self):
        accepted_freeze().Instructions.test_documented_install_guards_refuse_existing_targets(
            self
        )

    def test_fresh_offline_install_and_eleven_help_entrances(self):
        accepted_freeze().Instructions.test_fresh_offline_install_and_documented_command_help(
            self
        )


if __name__ == "__main__":
    if "--print-instruction-record" in sys.argv:
        print(json.dumps(successor_record(), indent=2) + "\n", end="")
    else:
        unittest.main()
