"""Test documented first-Issue admission through the unchanged installed command."""

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
    os.environ.get("AWARE_FIRST_ISSUE_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-initializer-fs-v1"
BASELINE = "62701c3d29337ef180bad4776cd58b07ec70decb"
PUBLIC_PINS_SHA = "38fba88d0026c27434229b9017fcdbb8df402ea709038ee598d75febfb50432d"
ORIGINAL_INTEGRATION_SHA = (
    "ceee1bd44d454ff0eee6d63a5953ef832cbc57e2ec50e3e23410282ee6288b2b"
)
SCOPE = [
    "README.md",
    "protocols/WORKFLOW.md",
    "protocols/issues/README.md",
    "protocols/issues/FIRST-ISSUE.md",
    "releases/SELECTED.json",
    "releases/canonical-initializer-fs-v1/FIRST-ISSUE-INSTRUCTIONS.json",
    "releases/canonical-initializer-fs-v1/FIRST-ISSUE-REVIEW.md",
    "releases/canonical-initializer-fs-v1/test_first_issue_onboarding.py",
    "docs/issues/2026/10/11/fb-2026-10-11-first-issue-reference-onboarding-v0.md",
]
REFERENCE = "fb/2026-10-11/json-checker-draft"
RECORD = "docs/issues/2026/10/11/fb-2026-10-11-json-checker-draft.md"
EXPECTED_SCOPE = [RECORD, "aware.protocol.toml", "docs/specs/json-checker"]


def sha(body):
    return hashlib.sha256(body).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def documented_block():
    text = (ROOT / "protocols/issues/FIRST-ISSUE.md").read_text()
    blocks = re.findall(r"```bash\n(.*?)```", text, re.DOTALL)
    if len(blocks) != 1:
        raise ValueError("one_complete_admission_block_required")
    return blocks[0]


def original_integration():
    path = RELEASE / "test_local_integration.py"
    if sha(path.read_bytes()) != ORIGINAL_INTEGRATION_SHA:
        raise ValueError("original_integration_proof_changed")
    spec = importlib.util.spec_from_file_location("retained_integration_proof", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pin_check(rows, bodies):
    if set(rows) != set(bodies):
        raise ValueError("instruction_set_changed")
    for name, row in rows.items():
        if len(bodies[name]) != row["bytes"] or sha(bodies[name]) != row["sha256"]:
            raise ValueError("instruction_bytes_changed:" + name)


class FirstIssue(unittest.TestCase):
    def prefix(self, scratch, identity=True):
        env = Path(os.environ["AWARE_FIRST_ISSUE_INSTALLED_ENV"])
        self.assertTrue((env / "bin/aware").is_file())
        args = [
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
            "--ro-bind",
            str(env),
            str(env),
            "--clearenv",
            "--setenv",
            "PATH",
            "/usr/bin:/bin",
            "--setenv",
            "HOME",
            str(scratch),
            "--setenv",
            "TMPDIR",
            str(scratch),
            "--setenv",
            "LANG",
            "C.UTF-8",
            "--setenv",
            "AWARE",
            str(env / "bin/aware"),
            "--setenv",
            "aware_repo_root",
            str(scratch / "customer"),
            "--chdir",
            str(scratch),
        ]
        if identity:
            supplied = [
                (key, os.environ.get(key, "").strip())
                for key in ("CODEX_THREAD_ID", "CLAUDE_CODE_SESSION_ID")
            ]
            supplied = [(key, value) for key, value in supplied if value]
            self.assertEqual(len(supplied), 1, "genuine_unambiguous_harness_required")
            key, value = supplied[0]
            self.actor = (
                "codex-" if key == "CODEX_THREAD_ID" else "claude_code-"
            ) + value
            args += ["--setenv", key, value]
        return args + ["--"]

    def case(self, name):
        parent = Path(os.environ["AWARE_FIRST_ISSUE_REPLAY_ROOT"])
        self.assertTrue(parent.is_dir() and not parent.is_symlink())
        path = parent / name
        self.assertFalse(path.exists())
        path.mkdir(mode=0o700)
        prefix = self.prefix(path)
        env = Path(os.environ["AWARE_FIRST_ISSUE_INSTALLED_ENV"])
        initialized = subprocess.run(
            prefix
            + [
                str(env / "bin/aware"),
                "init",
                "--repo-root",
                str(path / "customer"),
                "--create-repository",
                "--apply",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        (path / "init.stdout").write_text(initialized.stdout)
        (path / "init.stderr").write_text(initialized.stderr)
        self.assertEqual(
            initialized.returncode, 0, initialized.stdout + initialized.stderr
        )
        init_result = json.loads(initialized.stdout)
        self.assertTrue(init_result["completion_verified"])
        self.assertEqual(init_result["execution_id"], self.actor)
        foreign = path / "customer/FOREIGN.txt"
        foreign.write_bytes(b"foreign work must survive\n")
        foreign.chmod(0o640)
        return path, prefix

    def source_state(self, repository):
        return {
            str(p.relative_to(repository)): (p.read_bytes(), p.stat().st_mode & 0o777)
            for p in repository.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(repository).parts
        }

    def run_document(self, scratch, prefix, body=None):
        result = subprocess.run(
            prefix + ["/bin/bash", "-s"],
            input=body or documented_block(),
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        (scratch / "document.stdout").write_text(result.stdout)
        (scratch / "document.stderr").write_text(result.stderr)
        return result

    def receipts(self, scratch):
        dirs = list(scratch.glob("aware-first-issue.*"))
        self.assertEqual(len(dirs), 1)
        return dirs[0]

    def test_exact_instruction_pins_and_negative_control(self):
        record = json.loads((RELEASE / "FIRST-ISSUE-INSTRUCTIONS.json").read_bytes())
        self.assertEqual(record["baseline_revision"], BASELINE)
        self.assertEqual(record["status"], "first_issue_correction_review_pending")
        self.assertFalse(record["public_delivery_authorized"])
        self.assertFalse(record["runtime_payload_changed"])
        self.assertEqual(record["supersedes_instruction_sha256"], PUBLIC_PINS_SHA)
        self.assertEqual(len(record["files"]), 12)
        bodies = {name: (ROOT / name).read_bytes() for name in record["files"]}
        pin_check(record["files"], bodies)
        bodies["protocols/issues/FIRST-ISSUE.md"] += b"\n"
        with self.assertRaisesRegex(ValueError, "instruction_bytes_changed"):
            pin_check(record["files"], bodies)

    def test_exact_scope_and_unchanged_baseline_bytes_modes(self):
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
            self.assertFalse((ROOT / name).is_symlink())
            self.assertEqual(
                bool((ROOT / name).stat().st_mode & 0o111), mode == "100755", name
            )
            if name not in SCOPE:
                self.assertEqual(
                    (ROOT / name).read_bytes(), git("cat-file", "blob", oid), name
                )

    def test_original_software_carriage_and_selector(self):
        original_integration().Integration.test_whole_envelope_and_every_attachment(
            self
        )
        self.assertEqual(
            sha((RELEASE / "PUBLIC-INSTRUCTIONS.json").read_bytes()), PUBLIC_PINS_SHA
        )
        current = json.loads((ROOT / "releases/SELECTED.json").read_bytes())
        before = json.loads(git("show", BASELINE + ":releases/SELECTED.json"))
        for key in ("instruction_status", "instruction_record"):
            current.pop(key)
            before.pop(key)
        self.assertEqual(current, before)
        self.assertEqual(current["canonical_profile"], "portable_protocols")
        self.assertFalse(current["detached_wheels_accepted"])
        self.assertFalse(current["contributor_selection_changed"])

    def test_reference_guidance_links_and_shell_syntax(self):
        for name in (
            "README.md",
            "protocols/WORKFLOW.md",
            "protocols/issues/README.md",
            "protocols/issues/FIRST-ISSUE.md",
        ):
            text = (ROOT / name).read_text()
            for link in re.findall(r"\]\(([^)]+)\)", text):
                if "://" not in link and not link.startswith("#"):
                    self.assertTrue(
                        (ROOT / name).parent.joinpath(link.split("#", 1)[0]).exists(),
                        (name, link),
                    )
        text = (ROOT / "protocols/issues/FIRST-ISSUE.md").read_text()
        self.assertIn("fb/YYYY-MM-DD/lowercase-hyphenated-slug", text)
        self.assertIn(REFERENCE, text)
        self.assertIn(RECORD, text)
        self.assertIn("not cryptographic authentication", text)
        self.assertIn("does not configure SPEC", text)
        result = subprocess.run(
            ["/bin/bash", "-n"],
            input=documented_block(),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ("README.md", "protocols/WORKFLOW.md"):
            blocks = lambda b: re.findall(rb"```(?:sh|bash)\n(.*?)```", b, re.DOTALL)
            self.assertEqual(
                blocks((ROOT / name).read_bytes()),
                blocks(git("show", BASELINE + ":" + name)),
            )

    def test_documented_admission_through_installed_cli(self):
        scratch, prefix = self.case("admitted")
        repository = scratch / "customer"
        before = self.source_state(repository)
        result = self.run_document(scratch, prefix)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipts = self.receipts(scratch)
        for name in ("create.json", "scope.json", "progress.json"):
            self.assertEqual(
                json.loads((receipts / name).read_bytes())["outcome"], "applied", name
            )
        admitted = json.loads((receipts / "admitted-read.json").read_bytes())
        self.assertEqual(admitted["outcome"], "found")
        projection = admitted["projection"]
        self.assertEqual(projection["identity"]["owner_ref"], self.actor)
        self.assertEqual(projection["identity"]["status"], "in_progress")
        self.assertEqual(
            set(projection["content"]["ownership_scope"]), set(EXPECTED_SCOPE)
        )
        self.assertEqual(projection["source"]["path"], RECORD)
        self.assertEqual(
            projection["source"]["digest"],
            "sha256:" + sha((repository / RECORD).read_bytes()),
        )
        after = self.source_state(repository)
        for name, row in before.items():
            self.assertEqual(after[name], row, name)
        self.assertEqual(set(after) - set(before), {RECORD})
        self.assertFalse((repository / ".git/index").exists())
        head = subprocess.run(
            ["git", "-C", str(repository), "rev-parse", "--verify", "HEAD"],
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(head.returncode, 0)

    def test_path_reference_refuses_without_guessed_retry(self):
        scratch, prefix = self.case("invalid-reference")
        before = self.source_state(scratch / "customer")
        body = documented_block().replace(
            "first_issue_ref='" + REFERENCE + "'", "first_issue_ref='" + RECORD + "'"
        )
        self.assertNotEqual(body, documented_block())
        result = self.run_document(scratch, prefix, body)
        self.assertEqual(result.returncode, 2)
        receipts = self.receipts(scratch)
        refused = json.loads((receipts / "create.json").read_bytes())
        self.assertEqual(refused["outcome"], "malformed")
        self.assertIn("issue_ref_invalid", refused["diagnostics"])
        self.assertEqual(self.source_state(scratch / "customer"), before)
        self.assertEqual({p.name for p in receipts.iterdir()}, {"create.json"})
        self.assertFalse((scratch / "customer/.git/index").exists())

    def test_missing_identity_stops_before_issue_effects(self):
        scratch, _ = self.case("missing-identity")
        before = self.source_state(scratch / "customer")
        result = self.run_document(scratch, self.prefix(scratch, identity=False))
        self.assertEqual(result.returncode, 2)
        self.assertIn("remain read-only", result.stderr)
        self.assertEqual(self.source_state(scratch / "customer"), before)
        self.assertFalse(list(scratch.glob("aware-first-issue.*")))

    def test_stale_guard_refuses_without_refresh_or_effects(self):
        scratch, prefix = self.case("stale-guard")
        result = self.run_document(scratch, prefix)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipts = self.receipts(scratch)
        old = json.loads((receipts / "scope-read.json").read_bytes())["projection"][
            "source"
        ]["digest"]
        current = self.source_state(scratch / "customer")
        env = Path(os.environ["AWARE_FIRST_ISSUE_INSTALLED_ENV"])
        result = subprocess.run(
            prefix
            + [
                str(env / "bin/aware"),
                "issue",
                "start-progress",
                "--repository-root",
                str(scratch / "customer"),
                "--issue-ref",
                REFERENCE,
                "--expected-source-sha256",
                old,
                "--client-intent-id",
                "explicit-stale-probe",
                "--actor-ref",
                self.actor,
                "--actor-evidence-ref",
                "harness:" + self.actor,
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        (scratch / "stale.stdout").write_text(result.stdout)
        (scratch / "stale.stderr").write_text(result.stderr)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.source_state(scratch / "customer"), current)
        refused = json.loads(result.stdout)
        self.assertEqual(refused["outcome"], "stale")
        self.assertEqual(refused["diagnostics"], ["expected_source_sha256_mismatch"])


if __name__ == "__main__":
    unittest.main()
