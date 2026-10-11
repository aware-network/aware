"""Maintainer instruction checks over the original installer and installed CLI."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(
    os.environ.get("AWARE_FREEZE_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-issue083-fs-v1"
BASELINE = "5d35a566b0d7e565e3c7b33cb7e6d5632ffdcee8"
FREEZE_CHECKPOINT = "f654b30bea29db00c0042c2caefe0cae0261ab3b"
ENVELOPE_SHA = "a41782559bc3a2d9e02ceacc5bf458f0a77e53940b1b3bdcc8fabca6c15b53ea"
PAYLOAD_SHA = "0fb3d491b4b99578b06be99894b945d27834d49ad855029de227792ade4f16f4"
SOURCE_SHA = "3ae51d3c2a8238adb31335f2b2941a30495066d81f048ef8848b593249025fb0"
ORIGINAL_TEST_SHA = "9df5f18e60d2b5ad567d8317b66ab5e2f95043501162edc0bec994ba6486ba61"
INSTRUCTIONS = {
    "README.md",
    "protocols/README.md",
    "protocols/COHERENCE.md",
    "protocols/INITIALIZATION.md",
    "protocols/WORKFLOW.md",
    "protocols/issues/README.md",
    "protocols/issues/FIRST-ISSUE.md",
    "protocols/repository/README.md",
    "protocols/specification/README.md",
    "protocols/example-draft-input.py",
    "releases/README.md",
    "releases/canonical-issue083-fs-v1/README.md",
}
SCOPE = {
    "README.md",
    "protocols/issues/FIRST-ISSUE.md",
    "protocols/WORKFLOW.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/SELECTED.json",
    "releases/canonical-issue083-fs-v1/README.md",
    "releases/canonical-issue083-fs-v1/INSTRUCTIONS.json",
    "releases/canonical-issue083-fs-v1/INSTRUCTION-FREEZE.md",
    "releases/canonical-issue083-fs-v1/test_instruction_freeze.py",
    "docs/issues/2026/10/11/fb-2026-10-11-canonical-issue083-instruction-freeze-v0.md",
}


def sha(body):
    return hashlib.sha256(body).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def verify_instructions(rows, bodies):
    if set(rows) != INSTRUCTIONS or set(bodies) != INSTRUCTIONS:
        raise ValueError("exact_instruction_set_required")
    for name, row in rows.items():
        body = bodies[name]
        if len(body) != row["bytes"] or sha(body) != row["sha256"]:
            raise ValueError("instruction_bytes_changed:" + name)


def original_test():
    path = RELEASE / "test_local_integration.py"
    if sha(path.read_bytes()) != ORIGINAL_TEST_SHA:
        raise ValueError("original_installer_test_changed")
    spec = importlib.util.spec_from_file_location("accepted_installer_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def heading_fragments(text):
    """Resolve ATX headings in these authored Markdown instructions, not code."""
    anchors = set()
    counts = {}
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        heading = re.match(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if heading:
            title = heading.group(1).lower()
            title = re.sub(r"[`*_]", "", title)
            slug = re.sub(r"[^\w\s-]", "", title).replace(" ", "-")
            count = counts.get(slug, 0)
            counts[slug] = count + 1
            anchors.add(slug if not count else f"{slug}-{count}")
    return anchors


def verify_local_link(source, link):
    if "://" in link:
        return
    path, _, fragment = link.partition("#")
    target = source.parent / path if path else source
    if not target.exists():
        raise ValueError("local_link_target_missing:" + link)
    if fragment and fragment not in heading_fragments(target.read_text()):
        raise ValueError("local_link_fragment_missing:" + link)


class Instructions(unittest.TestCase):
    def test_exact_instruction_bytes_and_negative_controls(self):
        record = json.loads((RELEASE / "INSTRUCTIONS.json").read_bytes())
        self.assertEqual(record["baseline_revision"], BASELINE)
        self.assertEqual(record["status"], "frozen_locally_review_pending")
        bodies = {name: (ROOT / name).read_bytes() for name in INSTRUCTIONS}
        verify_instructions(record["files"], bodies)
        changed = dict(bodies)
        changed["protocols/WORKFLOW.md"] += b"\n"
        with self.assertRaisesRegex(ValueError, "instruction_bytes_changed"):
            verify_instructions(record["files"], changed)
        changed.pop("README.md")
        with self.assertRaisesRegex(ValueError, "exact_instruction_set_required"):
            verify_instructions(record["files"], changed)

    def test_exact_scope_and_unaffected_baseline_bytes_modes(self):
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
        self.assertEqual(actual, set(rows) | SCOPE)
        for name, (mode, oid) in rows.items():
            path = ROOT / name
            self.assertFalse(path.is_symlink(), name)
            self.assertEqual(bool(path.stat().st_mode & 0o111), mode == "100755", name)
            if name not in SCOPE:
                self.assertEqual(path.read_bytes(), git("cat-file", "blob", oid), name)

    def test_artifacts_and_sole_package_selector_preserved(self):
        record = json.loads((RELEASE / "INSTRUCTIONS.json").read_bytes())
        self.assertEqual(record["canonical_profile"], "portable_protocols")
        self.assertEqual(record["envelope_sha256"], ENVELOPE_SHA)
        self.assertEqual(record["payload_sha256"], PAYLOAD_SHA)
        self.assertEqual(record["source_index_sha256"], SOURCE_SHA)
        self.assertEqual(sha((RELEASE / "SOURCE-INDEX.json").read_bytes()), SOURCE_SHA)
        self.assertEqual(
            sha(
                (
                    RELEASE / "canonical-issue083-source-notice-review-v1.tar.gz"
                ).read_bytes()
            ),
            ENVELOPE_SHA,
        )
        selected = json.loads((ROOT / "releases/SELECTED.json").read_bytes())
        before = json.loads(git("show", BASELINE + ":releases/SELECTED.json"))
        for key in ("instruction_status", "instruction_record", "selection_review"):
            selected.pop(key, None)
            before.pop(key, None)
        self.assertEqual(selected, before)
        self.assertFalse(selected["public_delivery_authorized"])
        self.assertFalse(selected["detached_wheels_accepted"])
        self.assertFalse(selected["contributor_selection_changed"])
        self.assertNotIn("packages", record)
        self.assertNotIn("packages", selected)

    def test_install_and_init_commands_preserve_supported_boundaries(self):
        root = (ROOT / "README.md").read_text()
        workflow = (ROOT / "protocols/WORKFLOW.md").read_text()
        before = git("show", BASELINE + ":README.md").decode()
        self.assertEqual(
            re.findall(r"```sh\n(.*?)```", root, re.DOTALL),
            re.findall(r"```sh\n(.*?)```", before, re.DOTALL),
        )
        self.assertNotIn("/bin/sh ./install.sh", workflow)
        self.assertNotIn('"$aware_init_env/bin/aware" init', workflow)
        for text in (root, workflow):
            self.assertIn("protocols/install.py", text)
            self.assertIn("--python-executable /usr/bin/python3.12", text)
            self.assertIn("--create-repository --apply --format json", text)
            self.assertIn("pending independent", text)
            self.assertIn("not yet", text)
        self.assertIn("prospective_only", workflow)
        self.assertIn("completion_verified=false", workflow)
        self.assertIn("fresh Protocol admission", " ".join(workflow.split()))
        self.assertIn("no silent guard refresh", workflow.lower())
        self.assertIn("normalized semantic identity", workflow)
        self.assertIn("absolute input paths", workflow)
        self.assertIn("six missing package-local", workflow)
        first = (ROOT / "protocols/issues/FIRST-ISSUE.md").read_text()
        self.assertIn("fb/YYYY-MM-DD/lowercase-hyphenated-slug", first)
        self.assertIn("not an atomic transaction", workflow)
        self.assertIn("live publication capability", workflow)

    def test_local_links_and_install_blocks_are_valid(self):
        for name in INSTRUCTIONS:
            if name.endswith(".md"):
                text = (ROOT / name).read_text()
                for link in re.findall(r"\]\(([^)]+)\)", text):
                    verify_local_link(ROOT / name, link)
                for block in re.findall(r"```(?:sh|bash)\n(.*?)```", text, re.DOTALL):
                    result = subprocess.run(
                        ["/bin/bash", "-n"],
                        input=block,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 0, (name, result.stderr))

    def test_first_issue_fragment_and_single_instruction_pin_correction(self):
        name = "protocols/issues/FIRST-ISSUE.md"
        old_link = "../WORKFLOW.md#spec-and-guard-meanings"
        new_link = "../WORKFLOW.md#guarded-work-and-paired-publication"
        before = git("show", FREEZE_CHECKPOINT + ":" + name).decode()
        after = (ROOT / name).read_text()
        self.assertEqual(after, before.replace(old_link, new_link))
        with self.assertRaisesRegex(ValueError, "local_link_fragment_missing"):
            verify_local_link(ROOT / name, old_link)
        verify_local_link(ROOT / name, new_link)
        # Same-document fragments are checked too; fenced comments are not headings.
        verify_local_link(
            ROOT / "protocols/WORKFLOW.md", "#guarded-work-and-paired-publication"
        )
        with self.assertRaisesRegex(ValueError, "local_link_fragment_missing"):
            verify_local_link(ROOT / "protocols/WORKFLOW.md", "#missing-heading")
        self.assertEqual(
            heading_fragments("# Repeat\n```python\n# Hidden\n```\n# Repeat\n"),
            {"repeat", "repeat-1"},
        )
        previous = json.loads(
            git(
                "show",
                FREEZE_CHECKPOINT
                + ":releases/canonical-issue083-fs-v1/INSTRUCTIONS.json",
            )
        )
        current = json.loads((RELEASE / "INSTRUCTIONS.json").read_bytes())
        row = current["files"].pop(name)
        old_row = previous["files"].pop(name)
        self.assertNotEqual(row, old_row)
        self.assertEqual(current, previous)

    def test_documented_install_guards_refuse_existing_targets(self):
        for name in ("README.md", "protocols/WORKFLOW.md"):
            text = (ROOT / name).read_text()
            block = re.search(r"```(?:sh|bash)\n(.*?)```", text, re.DOTALL).group(1)
            parent_var, env_var = (
                ("aware_parent", "aware_env")
                if name == "README.md"
                else ("aware_init_parent", "aware_init_env")
            )
            for kind in ("absent", "file", "directory", "symlink", "dangling_symlink"):
                with (
                    self.subTest(name=name, kind=kind),
                    tempfile.TemporaryDirectory() as temporary,
                ):
                    parent = Path(temporary)
                    target = parent / "env"
                    if kind == "file":
                        target.touch()
                    elif kind == "directory":
                        target.mkdir()
                    elif kind in {"symlink", "dangling_symlink"}:
                        destination = parent / "destination"
                        if kind == "symlink":
                            destination.mkdir()
                        target.symlink_to(destination)
                    controlled = re.sub(
                        parent_var + r"=.*\n",
                        parent_var + '="' + temporary + '"\n',
                        block,
                        count=1,
                    )
                    controlled, count = re.subn(
                        r"/usr/bin/python3\.12 protocols/install\.py \\\n  --python-executable /usr/bin/python3\.12 --venv \"\$"
                        + env_var
                        + r"\"",
                        "printf 'INSTALLER_REACHED\\n'",
                        controlled,
                    )
                    self.assertEqual(count, 1)
                    controlled = controlled.replace('"$AWARE" --help', ":")
                    result = subprocess.run(
                        ["/bin/bash", "-c", controlled],
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(
                        "INSTALLER_REACHED" in result.stdout,
                        kind == "absent",
                        result.stderr,
                    )
                    self.assertEqual(result.returncode == 0, kind == "absent")

    def test_fresh_offline_install_and_documented_command_help(self):
        original_test().Integration.test_fresh_offline_hidden_install_and_refusals(self)
        scratch = Path(os.environ["AWARE_INITIALIZER_INTEGRATION_REPLAY_ROOT"])
        command = scratch / "env/bin/aware"
        prefix = [
            "/usr/bin/bwrap",
            "--die-with-parent",
            "--unshare-net",
            "--ro-bind",
            "/",
            "/",
            "--dev",
            "/dev",
            "--proc",
            "/proc",
            "--tmpfs",
            "/home",
            "--tmpfs",
            "/root",
            "--tmpfs",
            "/tmp",
            "--bind",
            str(scratch),
            str(scratch),
            "--clearenv",
            "--setenv",
            "PATH",
            "/usr/bin:/bin",
            "--setenv",
            "HOME",
            str(scratch),
            "--setenv",
            "LANG",
            "C.UTF-8",
            "--chdir",
            str(scratch),
            "--",
        ]
        operations = [
            ("init",),
            ("issue", "ensure-snapshot"),
            ("issue", "bind-scope"),
            ("issue", "start-progress"),
            ("issue", "publish-close"),
            ("protocol", "admit"),
            ("protocol", "setup-specification"),
            ("spec", "observe"),
            ("spec", "iteration-identity"),
            ("spec", "create-draft"),
        ]
        for operation in operations:
            result = subprocess.run(
                prefix + [str(command), *operation, "--help"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(
                result.returncode, 0, (operation, result.stdout, result.stderr)
            )
            (scratch / ("help-" + "-".join(operation) + ".txt")).write_text(
                result.stdout
            )
        result = subprocess.run(
            prefix + [str(command), "init", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        for flag in (
            "--repo-root",
            "--create-repository",
            "--apply",
            "--issue-root",
            "--no-agent-contract",
            "--format",
        ):
            self.assertIn(flag, result.stdout)


if __name__ == "__main__":
    unittest.main()
