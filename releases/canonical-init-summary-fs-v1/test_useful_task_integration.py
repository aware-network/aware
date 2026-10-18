"""Maintainer checks for documentation integration; no installer or workflow replay."""

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
    os.environ.get("USEFUL_TASK_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-init-summary-fs-v1"
RECORD = RELEASE / "USEFUL-TASK-INTEGRATION.json"
ORIGINAL_RECEIVER_SHA = (
    "ad3e35eab434e9062afbb3294d478646c2debe37fbd4ff2368a35ee8489f9a68"
)


def sha(body):
    return hashlib.sha256(body).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def record():
    return json.loads(RECORD.read_bytes())


class Integration(unittest.TestCase):
    def test_exact_accepted_postimages_and_receiver(self):
        value = record()
        self.assertEqual(len(value["accepted_postimages"]), 14)
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
        self.assertEqual(actual, set(original) | set(value["scope_paths"]))
        self.assertEqual(len(actual), 1718)
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
        self.assertEqual(changed, set(value["scope_paths"]))
        self.assertEqual(len(changed), 18)

    def test_original_protected_carriage_and_history(self):
        for name, row in record()["protected_inputs"].items():
            self.assertEqual(sha((ROOT / name).read_bytes()), row["sha256"], name)
        selected = json.loads((ROOT / "releases/SELECTED.json").read_bytes())
        before = json.loads(
            git("show", record()["baseline_revision"] + ":releases/SELECTED.json")
        )
        for key in (
            "published_revision",
            "public_delivery_authorized",
            "instruction_status",
            "instruction_record",
            "instruction_alignment_publication_authorized",
        ):
            selected.pop(key, None)
            before.pop(key, None)
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

    def test_original_shell_blocks_and_reading_order(self):
        for name in ("README.md", "protocols/INIT.md", "protocols/WORKFLOW.md"):
            before = git("show", record()["baseline_revision"] + ":" + name)
            after = (ROOT / name).read_bytes()
            self.assertEqual(
                re.findall(rb"```(?:bash|sh)\n(.*?)```", before, re.DOTALL),
                re.findall(rb"```(?:bash|sh)\n(.*?)```", after, re.DOTALL),
            )
        text = (ROOT / "README.md").read_text()
        self.assertLess(
            text.index("## Complete something useful"),
            text.index("## Start with the shipped software"),
        )
        self.assertLess(
            text.index("## Start with the shipped software"),
            text.index("## Inspect the evidence"),
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
                    anchors = {
                        re.sub(r"[^\w\- ]", "", text.lower()).replace(" ", "-")
                        for text in headings
                    }
                    self.assertIn(fragment, anchors)

    def test_scope_checkpoint_is_not_current_authority_or_customer_evaluation(self):
        value = record()
        self.assertEqual(len(value["scope_paths"]), 18)
        self.assertRegex(
            value["admitted_issue_source_sha256"], r"^sha256:[0-9a-f]{64}$"
        )
        self.assertFalse(value["new_build_or_installation"])
        task = (ROOT / "protocols/tasks/JSON-CHECKER.md").read_text()
        self.assertIn("not an implementation or an evaluated customer success", task)
        self.assertIn("not claimed clean", task)

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
