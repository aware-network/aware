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
RELEASE = ROOT / "releases/canonical-issue083-fs-v1"
BASELINE = "c8f40696a4ee197095fe8045ee4f05034db305b6"
REMOTE_BASELINE = "62701c3d29337ef180bad4776cd58b07ec70decb"
HISTORICAL_SHA = "4acbf0a85cb857d9ea5e5d0f2b93ab27cc04c46e626cd9c1268bd9691f5ee3cc"
FREEZE_TEST_SHA = "d3ec012e62f3ebef4ed58006b41055b6e99c18eea394b61397b388a305c10298"
SCOPE = [
    "README.md",
    "protocols/WORKFLOW.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/SELECTED.json",
    "releases/canonical-issue083-fs-v1/README.md",
    "releases/canonical-issue083-fs-v1/PUBLIC-INSTRUCTIONS.json",
    "releases/canonical-issue083-fs-v1/PUBLICATION.md",
    "releases/canonical-issue083-fs-v1/test_publication.py",
    "docs/issues/2026/10/11/fb-2026-10-11-canonical-issue083-publication-v0.md",
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


def capture_process(args, output, *, cwd=None, env=None):
    """Retain generated proof evidence; never replace an earlier receipt."""
    output = Path(output)
    stdout = output.with_suffix(".stdout")
    stderr = output.with_suffix(".stderr")
    for path in (output, stdout, stderr):
        if path.exists() or path.is_symlink():
            raise ValueError("new_operation_evidence_required")
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, check=False)
    stdout.write_bytes(result.stdout)
    stderr.write_bytes(result.stderr)
    output.write_text(
        json.dumps(
            {
                "command": args,
                "returncode": result.returncode,
                "stdout_sha256": sha(result.stdout),
                "stderr_sha256": sha(result.stderr),
            },
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
    if result.returncode:
        raise RuntimeError("proof_operation_failed; retain " + str(output))
    return result.stdout


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
        accepted_freeze().original_test().Integration.test_whole_envelope_and_unsuppressed_findings(
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
            "canonical-issue083-fs-v1/PUBLIC-INSTRUCTIONS.json",
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
                " ".join(workflow.lower().split())
                if word == "no silent guard refresh"
                else " ".join(workflow.split()),
            )
        self.assertIn("unassisted", (ROOT / "README.md").read_text())

    def test_links_and_shell_syntax(self):
        accepted_freeze().Instructions.test_local_links_and_install_blocks_are_valid(
            self
        )
        for name in (
            "docs/alignment/CURRENT.md",
            "releases/canonical-issue083-fs-v1/PUBLICATION.md",
        ):
            path = ROOT / name
            for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                accepted_freeze().verify_local_link(path, link)

    def test_first_issue_fragment_and_exact_sequence_preserved(self):
        name = "protocols/issues/FIRST-ISSUE.md"
        body = (ROOT / name).read_bytes()
        self.assertEqual(body, git("show", BASELINE + ":" + name))
        self.assertIn(b"../WORKFLOW.md#guarded-work-and-paired-publication", body)
        with self.assertRaisesRegex(ValueError, "local_link_fragment_missing"):
            accepted_freeze().verify_local_link(
                ROOT / name, "../WORKFLOW.md#spec-and-guard-meanings"
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
