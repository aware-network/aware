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
RELEASE = ROOT / "releases/canonical-initializer-fs-v1"
BASELINE = "e519fffda47ea66a9ff69b874b3919702765cca2"
ENVELOPE_SHA = "5f0edebe568d1cfd8a06a33e6122cd4e0d3dd68f764058b1aa098456cc2df13c"
PAYLOAD_SHA = "2d812c489485ee187cf45fca012fffdfda5fcdf93d60495a02b843f94e4a8b68"
SOURCE_SHA = "69b4581f7ceef335fc9eb28f5e507198a638be56ab761e662ae60d195a8edfd1"
ORIGINAL_TEST_SHA = "ceee1bd44d454ff0eee6d63a5953ef832cbc57e2ec50e3e23410282ee6288b2b"
INSTRUCTIONS = {
    "README.md",
    "protocols/README.md",
    "protocols/COHERENCE.md",
    "protocols/INITIALIZATION.md",
    "protocols/WORKFLOW.md",
    "protocols/issues/README.md",
    "protocols/repository/README.md",
    "protocols/specification/README.md",
    "protocols/example-draft-input.py",
    "releases/README.md",
    "releases/canonical-initializer-fs-v1/README.md",
}
SCOPE = {
    "README.md",
    "protocols/WORKFLOW.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/SELECTED.json",
    "releases/canonical-initializer-fs-v1/README.md",
    "releases/canonical-initializer-fs-v1/INSTRUCTIONS.json",
    "releases/canonical-initializer-fs-v1/INSTRUCTION-FREEZE.md",
    "releases/canonical-initializer-fs-v1/test_instruction_freeze.py",
    "docs/issues/2026/10/11/fb-2026-10-11-canonical-initializer-instruction-freeze-v0.md",
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
                    RELEASE / "canonical-initializer-source-notice-review-v1.tar.gz"
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
        self.assertIn("fresh Protocol admission", workflow)
        self.assertIn("no silent guard refresh", workflow.lower())
        self.assertIn("not a manifest-byte currentness substitute", workflow)
        self.assertIn("absolute input paths", workflow)
        self.assertIn("Six", workflow)

    def test_local_links_and_install_blocks_are_valid(self):
        for name in INSTRUCTIONS:
            if name.endswith(".md"):
                text = (ROOT / name).read_text()
                for link in re.findall(r"\]\(([^)]+)\)", text):
                    if "://" not in link and not link.startswith("#"):
                        self.assertTrue(
                            (ROOT / name)
                            .parent.joinpath(link.split("#", 1)[0])
                            .exists(),
                            (name, link),
                        )
                for block in re.findall(r"```(?:sh|bash)\n(.*?)```", text, re.DOTALL):
                    result = subprocess.run(
                        ["/bin/bash", "-n"],
                        input=block,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 0, (name, result.stderr))

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
