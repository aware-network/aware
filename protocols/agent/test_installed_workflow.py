"""Real installed SDK/CLI proof. Git seed setup and fault injection are test-only."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLI = Path(sys.executable).parent / "aware"
ACTOR = "codex-fixture-owner-one"
NEXT_ACTOR = "codex-fixture-owner-two"
REF = "fb/2026-10-05/agent-demo"
ISSUE = "docs/issues/2026/10/05/fb-2026-10-05-agent-demo.md"


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def invoke(root: Path, *args: str, success: bool = True) -> dict:
    environment = {key: value for key, value in os.environ.items() if key in {"PATH", "HOME", "LANG", "LC_ALL", "TMPDIR"}}
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    completed = subprocess.run([str(CLI), *args], cwd=root, env=environment, text=True, capture_output=True)
    expected = 0 if success else 2
    if completed.returncode != expected:
        raise AssertionError((completed.returncode, completed.stdout, completed.stderr, args))
    return json.loads(completed.stdout or completed.stderr)


def mutation(root: Path, command: str, *args: str, actor: str = ACTOR, success: bool = True) -> dict:
    digest = "sha256:" + hashlib.sha256((root / ISSUE).read_bytes()).hexdigest()
    return invoke(root, "issue", command, "--repository-root", str(root), "--issue-ref", REF,
                  "--expected-source-sha256", digest, "--client-intent-id", command + ":" + actor,
                  "--actor-ref", actor, "--actor-evidence-ref", "fixture-harness:" + actor,
                  *args, success=success)


def state(root: Path) -> dict:
    return {"head": git(root, "rev-parse", "HEAD"), "status": git(root, "status", "--porcelain=v1"),
            "index": hashlib.sha256((root / ".git/index").read_bytes()).hexdigest(),
            "files": {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in root.rglob("*") if path.is_file() and ".git" not in path.relative_to(root).parts}}


class InstalledWorkflow(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="aware-agent-customer-proof-")
        self.root = Path(self.temporary.name)
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "config", "user.name", "Aware Fixture")
        git(self.root, "config", "user.email", "fixture@example.invalid")
        (self.root / "src").mkdir()
        (self.root / "src/result.py").write_text("value = 1\n")
        (self.root / "other.txt").write_text("Preserve original.\n")
        # Fixture-only initial history; all tested work/publication uses owners.
        git(self.root, "add", "--", "src/result.py", "other.txt")
        git(self.root, "commit", "-qm", "fixture-only seed")
        invoke(self.root, "init", "--repository-root", str(self.root))

    def tearDown(self):
        self.temporary.cleanup()

    def open(self):
        return invoke(self.root, "issue", "open", "--repository-root", str(self.root), "--issue-ref", REF,
                      "--title", "Deliver bounded result", "--scope-path", "src/result.py", "--client-intent-id", "open-proof",
                      "--actor-ref", ACTOR, "--actor-evidence-ref", "fixture-harness:" + ACTOR)

    def observe(self):
        return invoke(self.root, "issue", "resolve-read-projection", "--repository-root", str(self.root), "--issue-ref", REF)

    def commit(self, *paths: str, dry: bool = False, actor: str = ACTOR, success: bool = True):
        observed = self.observe()
        args = ["repository", "commit", "--repository-root", str(self.root), "--issue-ref", REF,
                "--expected-issue-source-sha256", observed["projection"]["source"]["digest"],
                "--actor-ref", actor, "--actor-evidence-ref", "fixture-harness:" + actor, "--message", "Deliver owned result"]
        for path in paths:
            args += ["--path", path]
        if dry:
            args += ["--dry-run"]
        return invoke(self.root, *args, success=success)

    def test_installation_boundary(self):
        expected = {"aware-agent-cli", "aware-issue-cli", "aware-issue-fs-adapter", "aware-issue-sdk", "aware-issue-runtime",
                    "aware-issue-operational-runtime", "aware-workspace-operator", "aware-protocol-fs-adapter",
                    "aware-protocol-runtime", "aware-protocol-sdk", "jsonschema", "jsonschema-specifications", "attrs",
                    "referencing", "rpds-py", "typing-extensions", "pydantic", "pydantic-core", "annotated-types", "typing-inspection"}
        installed = {distribution.metadata["Name"].lower().replace("_", "-"): distribution for distribution in importlib.metadata.distributions()}
        self.assertTrue(expected <= installed.keys())
        for name in expected:
            self.assertIsNone(installed[name].read_text("direct_url.json"))
        for name in ("aware_workflow", "aware_local_service_runtime", "aware_issue_service_api", "aware_issue_service_dto",
                     "aware_issues", "aware_ontology", "aware_orm", "aware_experience"):
            self.assertIsNone(importlib.util.find_spec(name))
        from aware_issue_fs_adapter import FilesystemIssueOperationProvider
        self.assertTrue(Path(importlib.import_module(FilesystemIssueOperationProvider.__module__).__file__).is_relative_to(Path(sys.prefix)))

    def test_full_workflow_and_verified_close(self):
        self.assertEqual(self.open()["outcome"], "opened")
        observed = self.observe()
        self.assertEqual(observed["projection"]["identity"]["status"], "in_progress")
        (self.root / "src/result.py").write_text("value = 2\n")
        (self.root / "other.txt").write_text("Preserve dirty customer work.\n")
        mutation(self.root, "append-update", "--message", "Actual fixture verification: value equals 2.")
        self.assertEqual(self.commit("src/result.py", ISSUE, dry=True)["outcome"], "planned")
        published = self.commit("src/result.py", ISSUE)
        self.assertEqual(published["outcome"], "applied")
        closed = mutation(self.root, "close", "--resolution", "Bounded result delivered.", "--verified-by", "Installed proof asserts value=2",
                          "--publication-receipt-ref", published["publication_receipt_ref"])
        self.assertEqual(closed["outcome"], "applied")
        self.assertEqual(self.observe()["projection"]["identity"]["status"], "closed")
        self.assertEqual(git(self.root, "show", "HEAD:src/result.py"), "value = 2")
        self.assertEqual(git(self.root, "show", "HEAD:other.txt"), "Preserve original.")
        self.assertEqual((self.root / "other.txt").read_text(), "Preserve dirty customer work.\n")
        self.assertIsNotNone(closed["closeout_publication_receipt_ref"])

    def test_out_of_scope_refused_without_mutation(self):
        self.open()
        (self.root / "other.txt").write_text("Not owned.\n")
        before = state(self.root)
        refused = self.commit("other.txt", success=False)
        self.assertIn("out_of_scope", json.dumps(refused))
        self.assertEqual(state(self.root), before)

    def test_former_owner_cannot_resume_after_durable_handoff(self):
        self.open()
        mutation(self.root, "block")
        mutation(self.root, "set-owner", "--new-owner-ref", NEXT_ACTOR)
        before = state(self.root)
        refused = mutation(self.root, "resume", success=False)
        self.assertIn("issue_owner_mismatch", json.dumps(refused))
        self.assertEqual(state(self.root), before)
        observed = self.observe()
        self.assertEqual(observed["projection"]["identity"]["owner_ref"], NEXT_ACTOR)
        self.assertEqual(mutation(self.root, "resume", actor=NEXT_ACTOR)["outcome"], "applied")

    def test_stale_issue_digest_refused_without_mutation(self):
        self.open()
        stale = "sha256:" + hashlib.sha256((self.root / ISSUE).read_bytes()).hexdigest()
        mutation(self.root, "append-update", "--message", "A newer observation is necessary.")
        before = state(self.root)
        result = invoke(self.root, "issue", "block", "--repository-root", str(self.root), "--issue-ref", REF,
                        "--expected-source-sha256", stale, "--client-intent-id", "stale-block", "--actor-ref", ACTOR,
                        "--actor-evidence-ref", "fixture-harness:" + ACTOR, success=False)
        self.assertIn("expected_source_sha256_mismatch", json.dumps(result))
        self.assertEqual(state(self.root), before)

    def test_unrelated_staged_work_survives(self):
        self.open()
        (self.root / "other.txt").write_text("Staged customer work.\n")
        git(self.root, "add", "--", "other.txt")  # test-only staging fault injection
        (self.root / "src/result.py").write_text("value = 3\n")
        staged = git(self.root, "show", ":other.txt")
        result = self.commit("src/result.py", ISSUE)
        self.assertEqual(result["outcome"], "applied")
        self.assertEqual(git(self.root, "show", ":other.txt"), staged)
        self.assertEqual(git(self.root, "show", "HEAD:other.txt"), "Preserve original.")
        self.assertEqual((self.root / "other.txt").read_text(), "Staged customer work.\n")
        self.assertEqual(git(self.root, "diff", "--cached", "--name-only"), "other.txt")

    def test_close_rejects_forged_publication_receipt(self):
        self.open()
        before = state(self.root)
        result = mutation(self.root, "close", "--resolution", "Must not close", "--verified-by", "No actual publication",
                          "--publication-receipt-ref", "git:" + "0" * 40, success=False)
        self.assertIn("publication_receipt", json.dumps(result))
        self.assertEqual(state(self.root), before)

    def test_initialization_never_overwrites_customer_configuration(self):
        before = state(self.root)
        result = invoke(self.root, "init", "--repository-root", str(self.root), success=False)
        self.assertIn("bootstrap_target_exists", json.dumps(result))
        self.assertEqual(state(self.root), before)


if __name__ == "__main__":
    unittest.main()
