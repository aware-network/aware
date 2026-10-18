"""Maintainer receiving: exact documentation delta and original retained reads."""

import hashlib
import importlib.util
import json
import os
import posixpath
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(
    os.environ.get("IMPLEMENTATION_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-init-summary-fs-v1"
ORIGINAL_RECEIVER_SHA = (
    "ad3e35eab434e9062afbb3294d478646c2debe37fbd4ff2368a35ee8489f9a68"
)


def sha(body):
    return hashlib.sha256(body).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def record():
    return json.loads((RELEASE / "IMPLEMENTATION-INTEGRATION.json").read_bytes())


class Integration(unittest.TestCase):
    def test_exact_accepted_postimages_and_receiver(self):
        value = record()
        self.assertEqual(len(value["accepted_postimages"]), 7)
        for name, row in value["accepted_postimages"].items():
            path = ROOT / name
            self.assertFalse(path.is_symlink(), name)
            self.assertEqual(sha(path.read_bytes()), row["after_sha256"], name)
            self.assertEqual(path.stat().st_size, row["bytes"], name)
        self.assertEqual(sha(Path(__file__).read_bytes()), value["receiver_sha256"])

    def test_exact_scope_unaffected_bytes_and_all_git_modes(self):
        value = record()
        original = {}
        for line in (
            git("ls-tree", "-r", value["baseline_revision"]).decode().splitlines()
        ):
            meta, name = line.split("\t")
            mode, kind, oid = meta.split()
            self.assertEqual(kind, "blob")
            original[name] = (mode, oid)
        actual = {
            str(p.relative_to(ROOT))
            for p in ROOT.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(ROOT).parts
        }
        self.assertEqual(len(original), value["baseline_file_count"])
        self.assertEqual(actual, set(original) | set(value["scope_paths"]))
        self.assertEqual(len(actual), value["expected_file_count_after_implementation"])
        changed = actual - set(original)
        for name, (mode, oid) in original.items():
            path = ROOT / name
            self.assertFalse(path.is_symlink(), name)
            self.assertEqual(bool(path.stat().st_mode & 0o111), mode == "100755", name)
            before = git("cat-file", "blob", oid)
            if path.read_bytes() != before:
                changed.add(name)
            if name not in value["scope_paths"]:
                self.assertEqual(path.read_bytes(), before, name)
        for name in actual - set(original):
            self.assertFalse((ROOT / name).is_symlink(), name)
            self.assertFalse((ROOT / name).stat().st_mode & 0o111, name)
        self.assertEqual(changed, set(value["scope_paths"]))
        self.assertEqual(len(changed), 11)

    def test_original_protected_carriage_and_selection(self):
        for name, row in record()["protected_inputs"].items():
            self.assertEqual(sha((ROOT / name).read_bytes()), row["sha256"], name)
        selected = json.loads((ROOT / "releases/SELECTED.json").read_bytes())
        before = json.loads(
            git("show", record()["baseline_revision"] + ":releases/SELECTED.json")
        )
        selected.pop("instruction_status")
        before.pop("instruction_status")
        self.assertEqual(selected, before)

    def test_eighteen_pins_and_rejection_controls(self):
        value = json.loads((RELEASE / "PUBLIC-INSTRUCTIONS.json").read_bytes())
        self.assertEqual(len(value["files"]), 18)
        for name, row in value["files"].items():
            body = (ROOT / name).read_bytes()
            self.assertEqual({"bytes": len(body), "sha256": sha(body)}, row)
            self.assertNotEqual(sha(body + b"\n"), row["sha256"])
        self.assertFalse(value["instruction_alignment_publication_authorized"])
        self.assertFalse(record()["push_authorized"])
        self.assertFalse(record()["independent_integration_acceptance"])

    def test_original_draft_and_other_shell_blocks_preserved(self):
        pattern = rb"```(?:bash|sh)\n(.*?)```"
        name = "protocols/issues/FIRST-ISSUE.md"
        before = re.findall(
            pattern, git("show", record()["baseline_revision"] + ":" + name), re.DOTALL
        )
        after = re.findall(pattern, (ROOT / name).read_bytes(), re.DOTALL)
        self.assertEqual(after[: len(before)], before)
        self.assertEqual(len(after) - len(before), 4)
        for name in ("README.md", "protocols/INIT.md", "protocols/WORKFLOW.md"):
            self.assertEqual(
                re.findall(
                    pattern,
                    git("show", record()["baseline_revision"] + ":" + name),
                    re.DOTALL,
                ),
                re.findall(pattern, (ROOT / name).read_bytes(), re.DOTALL),
            )

    def test_authored_links_and_fragments(self):
        for name in record()["accepted_postimages"]:
            if not name.endswith(".md"):
                continue
            for target in re.findall(r"\]\(([^)]+)\)", (ROOT / name).read_text()):
                if target.startswith("https://"):
                    continue
                path, _, fragment = target.partition("#")
                resolved = (
                    ROOT
                    / posixpath.normpath(posixpath.join(posixpath.dirname(name), path))
                    if path
                    else ROOT / name
                )
                self.assertTrue(resolved.is_file(), (name, target))
                if fragment:
                    headings = re.findall(
                        r"^#+ (.+)$", resolved.read_text(), re.MULTILINE
                    )
                    self.assertIn(
                        fragment,
                        {
                            re.sub(r"[^\w\- ]", "", text.lower()).replace(" ", "-")
                            for text in headings
                        },
                    )

    def test_checkpoint_not_authority_customer_proof_or_a12_requirement(self):
        value = record()
        self.assertRegex(
            value["admitted_issue_source_sha256"], r"^sha256:[0-9a-f]{64}$"
        )
        self.assertFalse(value["new_build_or_installation"])
        self.assertIn(
            "no new installation, customer evaluation, a12 requirement",
            value["qualification"],
        )
        wire = json.dumps(value)
        for fragment in ("/tmp/", "/home/", "/root/"):
            self.assertNotIn(fragment, wire)

    def test_retained_installation_reads(self):
        path = RELEASE / "test_local_integration.py"
        self.assertEqual(sha(path.read_bytes()), ORIGINAL_RECEIVER_SHA)
        spec = importlib.util.spec_from_file_location(
            "original_init_integration_reads", path
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.retained_installation_reads(self)


if __name__ == "__main__":
    unittest.main()
