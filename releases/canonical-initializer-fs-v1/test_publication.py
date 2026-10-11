"""Publication checks reuse accepted installer and command proofs, not another rail."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(
    os.environ.get("AWARE_PUBLICATION_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-initializer-fs-v1"
BASELINE = "019dcdc0acb27e49c3569c2ce3e7427777303330"
REMOTE_BASELINE = "f760ac28066191e50ba12d249928c0fd553f79b4"
HISTORICAL_SHA = "cd86d0c8ced285d86acf52410da45784ff3f83aafeab328b2276ae9c4d537c0e"
FREEZE_TEST_SHA = "4fee9711df76721a413dd2ddf85cd6f680bdfc60873f64eb61bccb1182ce0f43"
SCOPE = [
    "README.md",
    "protocols/WORKFLOW.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/SELECTED.json",
    "releases/canonical-initializer-fs-v1/README.md",
    "releases/canonical-initializer-fs-v1/PUBLIC-INSTRUCTIONS.json",
    "releases/canonical-initializer-fs-v1/PUBLICATION.md",
    "releases/canonical-initializer-fs-v1/test_publication.py",
    "docs/issues/2026/10/11/fb-2026-10-11-canonical-initializer-publication-v0.md",
]


def sha(body):
    return hashlib.sha256(body).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def accepted_freeze():
    path = RELEASE / "test_instruction_freeze.py"
    if sha(path.read_bytes()) != FREEZE_TEST_SHA:
        raise ValueError("original_freeze_test_changed")
    spec = importlib.util.spec_from_file_location("accepted_instruction_proof", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Publication(unittest.TestCase):
    def test_instruction_pins_and_historical_record(self):
        historical = (RELEASE / "INSTRUCTIONS.json").read_bytes()
        self.assertEqual(sha(historical), HISTORICAL_SHA)
        record = json.loads((RELEASE / "PUBLIC-INSTRUCTIONS.json").read_bytes())
        self.assertEqual(record["baseline_revision"], BASELINE)
        self.assertEqual(record["status"], "frozen_accepted")
        self.assertEqual(record["historical_instruction_sha256"], HISTORICAL_SHA)
        bodies = {name: (ROOT / name).read_bytes() for name in record["files"]}
        accepted_freeze().verify_instructions(record["files"], bodies)
        changed = dict(bodies)
        changed["README.md"] += b"\n"
        with self.assertRaisesRegex(ValueError, "instruction_bytes_changed"):
            accepted_freeze().verify_instructions(record["files"], changed)

    def test_exact_scope_unaffected_bytes_and_modes(self):
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
        self.assertEqual(actual, set(rows) | set(SCOPE))
        for name, (mode, oid) in rows.items():
            path = ROOT / name
            self.assertFalse(path.is_symlink(), name)
            self.assertEqual(bool(path.stat().st_mode & 0o111), mode == "100755", name)
            if name not in SCOPE:
                self.assertEqual(path.read_bytes(), git("cat-file", "blob", oid), name)
        self.assertEqual(
            git("merge-base", REMOTE_BASELINE, BASELINE).decode().strip(),
            REMOTE_BASELINE,
        )

    def test_accepted_envelope_every_attachment_and_sole_selector(self):
        accepted_freeze().original_test().Integration.test_whole_envelope_and_every_attachment(
            self
        )
        selected = json.loads((ROOT / "releases/SELECTED.json").read_bytes())
        before = json.loads(git("show", BASELINE + ":releases/SELECTED.json"))
        for key in (
            "selection_kind",
            "instruction_status",
            "instruction_record",
            "public_delivery_authorized",
        ):
            selected.pop(key)
            before.pop(key)
        self.assertEqual(selected, before)
        current = json.loads((ROOT / "releases/SELECTED.json").read_bytes())
        self.assertTrue(current["public_delivery_authorized"])
        self.assertFalse(current["detached_wheels_accepted"])
        self.assertFalse(current["contributor_selection_changed"])
        self.assertEqual(current["canonical_profile"], "portable_protocols")
        self.assertEqual(
            current["instruction_record"],
            "canonical-initializer-fs-v1/PUBLIC-INSTRUCTIONS.json",
        )
        self.assertNotIn("packages", current)

    def test_all_commands_and_example_preserved(self):
        record = json.loads((RELEASE / "PUBLIC-INSTRUCTIONS.json").read_bytes())
        for name in record["files"]:
            current = (ROOT / name).read_bytes()
            before = git("show", BASELINE + ":" + name)
            if name.endswith(".py"):
                self.assertEqual(current, before)
            else:
                blocks = lambda b: re.findall(
                    rb"```(?:sh|bash)\n(.*?)```", b, re.DOTALL
                )
                self.assertEqual(blocks(current), blocks(before), name)
        workflow = (ROOT / "protocols/WORKFLOW.md").read_text()
        for word in (
            "prospective_only",
            "completion_verified=false",
            "fresh Protocol admission",
            "absolute input paths",
            "no silent guard refresh",
        ):
            self.assertIn(
                word,
                workflow.lower() if word == "no silent guard refresh" else workflow,
            )
        self.assertIn("unassisted", (ROOT / "README.md").read_text())

    def test_links_and_shell_syntax(self):
        accepted_freeze().Instructions.test_local_links_and_install_blocks_are_valid(
            self
        )
        for name in (
            "docs/alignment/CURRENT.md",
            "releases/canonical-initializer-fs-v1/PUBLICATION.md",
        ):
            path = ROOT / name
            for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if "://" not in link and not link.startswith("#"):
                    self.assertTrue(
                        path.parent.joinpath(link.split("#", 1)[0]).exists(),
                        (name, link),
                    )

    def test_original_executable_install_guards(self):
        accepted_freeze().Instructions.test_documented_install_guards_refuse_existing_targets(
            self
        )

    def test_fresh_offline_hidden_install_and_ten_help_entrances(self):
        accepted_freeze().Instructions.test_fresh_offline_install_and_documented_command_help(
            self
        )


if __name__ == "__main__":
    unittest.main()
