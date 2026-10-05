"""Candidate-installed proof; Git writes below are fixture/fault injection only."""
from __future__ import annotations

import importlib.metadata
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SUPPORT = Path(os.environ["AWARE_REPAIR_TEST_SUPPORT"])
spec = importlib.util.spec_from_file_location("repair_flow", SUPPORT / "test_installed_workflow.py")
flow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flow)


class InstalledRepositoryRepair(unittest.TestCase):
    def test_installed_owner_bytes_match_candidate_binding(self):
        binding = json.loads(Path(os.environ["AWARE_REPAIR_BINDING"]).read_text())
        modules = {
            "commit.py": "aware_workspace_operator.commit",
            "operation.py": "aware_issue_sdk.operation",
            "provider.py": "aware_issue_fs_adapter.provider",
        }
        for row in binding["owner_files"]:
            origin = Path(importlib.util.find_spec(row.get("module") or modules[Path(row["path"]).name]).origin)
            self.assertTrue(origin.is_relative_to(Path(sys.prefix)))
            self.assertEqual(hashlib.sha256(origin.read_bytes()).hexdigest(), row["sha256"])

    def test_candidate_version_and_no_editable_or_direct_url(self):
        version = json.loads(Path(os.environ["AWARE_REPAIR_BINDING"]).read_text())["version"]
        self.assertEqual(importlib.metadata.version("aware-agent-cli"), version)
        self.assertEqual(subprocess.check_output([str(flow.CLI), "--version"], text=True).strip(), "aware-agent-cli " + version)
        for distribution in importlib.metadata.distributions():
            self.assertIsNone(distribution.read_text("direct_url.json"))

    def exercise(self, initial):
        with tempfile.TemporaryDirectory(prefix="repository-installed-repair-") as raw:
            parent = Path(raw)
            root = parent / "customer"
            initialized = flow.invoke(parent, "init", "--repository-root", str(root), "--create-repository")
            flow.git(root, "config", "user.name", "Customer Fixture")
            flow.git(root, "config", "user.email", "fixture@example.invalid")
            (root / "src").mkdir()
            (root / "src/result.py").write_text("value = 42\n")
            (root / "foreign.txt").write_text("foreign staged\n")
            if initial == "empty":
                flow.git(root, "read-tree", "--empty")
            if initial == "foreign":
                flow.git(root, "add", "--", "foreign.txt")
            if initial == "conflict":
                flow.git(root, "add", "--", "src/result.py")
                (root / "src/result.py").write_text("value = 43\n")
            paths = [*initialized["created"], "src/result.py", flow.ISSUE]
            args = ["issue", "open", "--repository-root", str(root), "--issue-ref", flow.REF,
                    "--title", "Installed repository repair", "--client-intent-id", "repair-open",
                    "--problem", "The initial index must not hide the approved contribution.",
                    "--objective", "Publish and close through the existing repository owner.",
                    "--acceptance", "Preserve foreign staging and retain pending-index warnings.",
                    "--actor-ref", flow.ACTOR, "--actor-evidence-ref", "fixture:" + flow.ACTOR]
            for path in paths:
                args.extend(["--scope-path", path])
            self.assertEqual(flow.invoke(parent, *args)["outcome"], "opened")
            flow.mutation(root, "append-update", "--message", "Fixture goal: prove exact scoped publication and clean closeout.")

            def publish(dry=False):
                observed = flow.invoke(root, "issue", "resolve-read-projection", "--repository-root", str(root), "--issue-ref", flow.REF)
                args = ["repository", "commit", "--repository-root", str(root), "--issue-ref", flow.REF,
                        "--expected-issue-source-sha256", observed["projection"]["source"]["digest"],
                        "--actor-ref", flow.ACTOR, "--actor-evidence-ref", "fixture:" + flow.ACTOR,
                        "--message", "Installed repair publication"]
                for path in paths:
                    args.extend(["--path", path])
                if dry:
                    args.append("--dry-run")
                return flow.invoke(root, *args)

            planned = publish(True)
            self.assertEqual(planned["outcome"], "planned")
            self.assertEqual(planned["shared_index_projection"], "not_run")
            lock = root / ".git/index.lock"
            if initial == "lock":
                lock.write_text("foreign lock\n")
            published = publish()
            self.assertEqual(published["outcome"], "applied")
            pending = initial in {"lock", "conflict"}
            self.assertEqual(published["index_reconciliation_pending"], pending)
            self.assertEqual(published["shared_index_projection"], "failed" if pending else "applied")
            if initial == "lock":
                self.assertEqual(published["shared_index_projection_error"], "shared_index_lock_busy")
                self.assertEqual(lock.read_text(), "foreign lock\n")
                return  # no caller recovery or unsupported debt-recovery claim
            if initial == "conflict":
                self.assertEqual(published["shared_index_projection_error"], "foreign_staged_content_preserved")
                self.assertEqual(flow.git(root, "show", ":src/result.py"), "value = 42")
                return
            self.assertEqual(flow.git(root, "status", "--porcelain", "--", *paths), "")
            self.assertEqual(flow.git(root, "rev-list", "--count", "HEAD"), "1")
            closed = flow.mutation(root, "close", "--resolution", "Installed fixture complete",
                                   "--verified-by", "Candidate-bound installed publication proof",
                                   "--publication-receipt-ref", published["publication_receipt_ref"])
            self.assertEqual(closed["outcome"], "applied")
            self.assertIsNotNone(closed["closeout_publication_receipt_ref"])
            self.assertEqual(flow.git(root, "status", "--porcelain", "--", *paths), "")
            observed = flow.invoke(parent, "issue", "resolve-read-projection", "--repository-root", str(root), "--issue-ref", flow.REF)
            self.assertEqual(observed["projection"]["identity"]["status"], "closed")
            self.assertIn("Closed", flow.git(root, "show", "HEAD:" + flow.ISSUE))
            if initial == "foreign":
                self.assertEqual(flow.git(root, "show", ":foreign.txt"), "foreign staged")
            self.assertEqual((root / "foreign.txt").read_text(), "foreign staged\n")

    def test_absent_index_first_commit_and_closeout(self):
        self.exercise("absent")

    def test_empty_index_first_commit_and_closeout(self):
        self.exercise("empty")

    def test_foreign_staging_first_commit_and_closeout(self):
        self.exercise("foreign")

    def test_owned_conflict_preserves_staging_and_pending(self):
        self.exercise("conflict")

    def test_native_lock_preserves_success_and_pending(self):
        self.exercise("lock")


if __name__ == "__main__":
    program = unittest.main(exit=False)
    if os.environ.get("AWARE_REPAIR_RESULT_PATH"):
        binding = json.loads(Path(os.environ["AWARE_REPAIR_BINDING"]).read_text())
        result = {"archive_sha256": binding["archive_sha256"], "tests_run": program.result.testsRun,
                  "failures": len(program.result.failures), "errors": len(program.result.errors),
                  "skipped": len(program.result.skipped), "success": program.result.wasSuccessful()}
        Path(os.environ["AWARE_REPAIR_RESULT_PATH"]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    raise SystemExit(0 if program.result.wasSuccessful() else 1)
