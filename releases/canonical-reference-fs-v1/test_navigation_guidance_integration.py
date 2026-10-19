"""Read-only exact navigation integration receiving; no installation/owner calls."""

import hashlib
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(
    os.environ.get("NAVIGATION_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RECORD = "releases/canonical-reference-fs-v1/NAVIGATION-GUIDANCE-INTEGRATION.json"


def sha(body):
    return hashlib.sha256(body).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def record():
    return json.loads((ROOT / RECORD).read_bytes())


class Receiving(unittest.TestCase):
    def test_exact_postimages_and_receiver(self):
        value = record()
        self.assertEqual(len(value["accepted_postimages"]), 3)
        for name, row in value["accepted_postimages"].items():
            body = (ROOT / name).read_bytes()
            self.assertEqual(
                (sha(body), len(body)), (row["after_sha256"], row["bytes"])
            )
        self.assertEqual(sha(Path(__file__).read_bytes()), value["receiver_sha256"])

    def test_exact_scope_and_unaffected_bytes_modes(self):
        value = record()
        baseline = {}
        for line in (
            git("ls-tree", "-r", value["baseline_revision"]).decode().splitlines()
        ):
            metadata, name = line.split("\t", 1)
            mode, kind, oid = metadata.split()
            self.assertEqual(kind, "blob")
            baseline[name] = (mode, oid)
        actual = {
            str(p.relative_to(ROOT))
            for p in ROOT.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(ROOT).parts
        }
        self.assertEqual(len(baseline), value["baseline_file_count"])
        self.assertEqual(len(actual), value["expected_file_count"])
        self.assertEqual(actual, set(baseline) | set(value["scope_paths"]))
        changed = actual - set(baseline)
        for name, (mode, oid) in baseline.items():
            path = ROOT / name
            self.assertFalse(path.is_symlink(), name)
            self.assertEqual(bool(path.stat().st_mode & 0o111), mode == "100755", name)
            old = git("cat-file", "blob", oid)
            if path.read_bytes() != old:
                changed.add(name)
            if name not in value["scope_paths"]:
                self.assertEqual(path.read_bytes(), old, name)
        for name in actual - set(baseline):
            # The original Issue owner creates private mode0600 records.
            # Git records the executable bit, not read/write permission bits.
            self.assertFalse((ROOT / name).is_symlink(), name)
            self.assertFalse((ROOT / name).stat().st_mode & 0o111, name)
        self.assertEqual(changed, set(value["scope_paths"]))

    def test_protected_inputs_and_status_only_pointer(self):
        value = record()
        for name, digest in value["protected_inputs"].items():
            self.assertEqual(sha((ROOT / name).read_bytes()), digest)
        path = "releases/SELECTED.json"
        old = json.loads(git("show", value["baseline_revision"] + ":" + path))
        new = json.loads((ROOT / path).read_bytes())
        new["instruction_status"] = old["instruction_status"]
        self.assertEqual(new, old)

    def test_nineteen_current_pins_and_historical_freeze(self):
        path = ROOT / "releases/canonical-reference-fs-v1/PUBLIC-INSTRUCTIONS.json"
        value = json.loads(path.read_bytes())
        self.assertEqual(len(value["files"]), 19)
        for name, row in value["files"].items():
            body = (ROOT / name).read_bytes()
            self.assertEqual(row, {"bytes": len(body), "sha256": sha(body)})
            self.assertNotEqual(row["sha256"], sha(body + b"\n"))
        self.assertFalse(value["instruction_alignment_publication_authorized"])

    def test_shell_blocks_and_guidance_boundaries(self):
        path = "protocols/FIRST-USEFUL-TASK.md"
        old = git("show", record()["baseline_revision"] + ":" + path)
        body = (ROOT / path).read_bytes()
        self.assertEqual(
            re.findall(rb"```.*?```", old, re.DOTALL),
            re.findall(rb"```.*?```", body, re.DOTALL),
        )
        text = " ".join(body.decode().split())
        self.assertNotIn("proposed parallel successors", text)
        for term in (
            "do not automate Issue guard extraction",
            "no current-use authority",
            "separate scope and final-file review decisions",
            "never automatic guard refresh or mutation retry",
        ):
            self.assertIn(term, text)
        self.assertTrue(
            (ROOT / "protocols/workspace/REFERENCE-NAVIGATION.md").is_file()
        )

    def test_original_issue_scope_and_no_broader_acceptance(self):
        value = record()
        body = (ROOT / value["public_issue_path"]).read_text()
        scope_section = body.split("## Ownership Scope", 1)[1].split("##", 1)[0]
        self.assertEqual(
            set(re.findall(r"^- `([^`]+)`", scope_section, re.MULTILINE)),
            set(value["scope_paths"]),
        )
        self.assertRegex(
            value["admitted_issue_source_sha256"], r"^sha256:[0-9a-f]{64}$"
        )
        self.assertFalse(value["push_authorized"])
        self.assertFalse(value["independent_integration_acceptance"])
        self.assertFalse(value["new_installation"])


if __name__ == "__main__":
    unittest.main()
