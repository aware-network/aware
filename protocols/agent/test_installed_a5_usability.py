"""Real installed customer entrance; no copied Issue or publication decisions."""

import importlib.metadata
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import test_installed_workflow as flow

BINDING = json.loads(Path(os.environ["AWARE_REPAIR_BINDING"]).read_bytes())


class InstalledA5Usability(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="aware-a5-usability-")
        self.parent = Path(self.temporary.name)
        self.root = self.parent / "customer"
        self.initialized = flow.invoke(
            self.parent,
            "init",
            "--repository-root",
            str(self.root),
            "--create-repository",
        )
        flow.git(self.root, "config", "user.name", "Fixture")
        flow.git(self.root, "config", "user.email", "fixture@example.invalid")

    def tearDown(self):
        self.temporary.cleanup()

    def arguments(self, *extra):
        return [
            "issue",
            "open",
            "--repository-root",
            str(self.root),
            "--issue-ref",
            flow.REF,
            "--title",
            "Durable approved work",
            "--client-intent-id",
            "a5-open",
            "--actor-ref",
            flow.ACTOR,
            "--actor-evidence-ref",
            "fixture:" + flow.ACTOR,
            "--problem",
            "The request must survive execution replacement.",
            "--objective",
            "Deliver the approved bounded result.",
            "--acceptance",
            "Preserve unrelated files and every publication warning.",
            *extra,
        ]

    def observe(self, *extra):
        return flow.invoke(
            self.root,
            "issue",
            "resolve-read-projection",
            "--repository-root",
            str(self.root),
            "--issue-ref",
            flow.REF,
            *extra,
        )

    def test_version_and_installed_shared_summary_identity(self):
        self.assertEqual(importlib.metadata.version("aware-agent-cli"), BINDING["version"])
        result = flow.invoke(self.root, "contract")
        self.assertEqual(result["version"], BINDING["consumer_contract"]["version"])
        import aware_agent_cli.main as entrance
        from aware_issue_cli.summary import summarize_result

        self.assertIs(entrance.summarize_result, summarize_result)

    def test_typed_content_summary_commit_and_close_preserve_customer_work(self):
        paths = [*self.initialized["created"], flow.ISSUE, "result.txt"]
        arguments = self.arguments("--format", "summary")
        for path in paths:
            arguments.extend(["--scope-path", path])
        opened = flow.invoke(self.root, *arguments)
        self.assertEqual(opened["outcome"], "opened")
        self.assertFalse(opened["atomic"])
        self.assertEqual(len(opened["receipts"]), 3)
        content = self.observe()["projection"]["content"]
        self.assertEqual(
            content["problem_items"],
            ["The request must survive execution replacement."],
        )
        self.assertEqual(
            content["goal_items"], ["Deliver the approved bounded result."]
        )
        self.assertEqual(
            content["acceptance_items"][0]["text"],
            "Preserve unrelated files and every publication warning.",
        )
        self.assertFalse(content["acceptance_items"][0]["checked"])
        (self.root / "result.txt").write_text("Delivered.\n")
        (self.root / "unrelated.txt").write_text("Preserve.\n")
        digest = self.observe()["projection"]["source"]["digest"]
        commit = [
            "repository",
            "commit",
            "--repository-root",
            str(self.root),
            "--issue-ref",
            flow.REF,
            "--expected-issue-source-sha256",
            digest,
            "--actor-ref",
            flow.ACTOR,
            "--actor-evidence-ref",
            "fixture:" + flow.ACTOR,
            "--message",
            "Deliver approved work",
            "--format",
            "summary",
        ]
        for path in paths:
            commit.extend(["--path", path])
        planned = flow.invoke(self.root, *commit, "--dry-run")
        self.assertEqual(planned["reference_update"], "not_run")
        applied = flow.invoke(self.root, *commit)
        self.assertEqual(applied["reference_update"], "cas_applied")
        self.assertEqual(applied["transaction_mode"], "isolated_index_atomic_ref_v1")
        self.assertIsNotNone(applied["operator_ref"])
        self.assertEqual(applied["index_result"]["shared_index_projection"], "applied")
        closed = flow.mutation(
            self.root,
            "close",
            "--resolution",
            "Delivered scoped work.",
            "--verified-by",
            "Installed fixture checks passed.",
            "--publication-receipt-ref",
            applied["publication_receipt_ref"],
            "--format",
            "summary",
        )
        self.assertEqual(closed["identity"]["status"], "closed")
        self.assertEqual(closed["index_result"]["shared_index_projection"], "applied")
        self.assertFalse(closed["index_result"]["index_reconciliation_pending"])
        self.assertFalse(closed["acceptance"][0]["checked"])
        self.assertEqual((self.root / "unrelated.txt").read_text(), "Preserve.\n")
        self.assertEqual(flow.git(self.root, "status", "--porcelain", "--", *paths), "")

    def test_missing_content_refuses_without_creation(self):
        arguments = self.arguments("--scope-path", "result.txt")
        index = arguments.index("--acceptance")
        del arguments[index : index + 2]
        result = subprocess.run(
            [str(flow.CLI), *arguments],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--acceptance", result.stderr)
        self.assertFalse((self.root / flow.ISSUE).exists())

    def test_invalid_content_refuses_before_issue_creation(self):
        result = flow.invoke(
            self.root,
            *self.arguments(
                "--scope-path", "result.txt", "--problem", "first\n## Owner"
            ),
            success=False,
        )
        self.assertEqual(result["outcome"], "error")
        self.assertFalse((self.root / flow.ISSUE).exists())

    def test_existing_issue_summary_refusal_preserves_record(self):
        arguments = self.arguments("--scope-path", "result.txt")
        flow.invoke(self.root, *arguments)
        before = (self.root / flow.ISSUE).read_bytes()
        result = flow.invoke(
            self.root, *arguments, "--format", "summary", success=False
        )
        self.assertEqual(result["diagnostics"], ["open_requires_absent_issue"])
        self.assertEqual(result["observation"]["identity"]["status"], "in_progress")
        self.assertEqual((self.root / flow.ISSUE).read_bytes(), before)

    def test_incomplete_scope_preserves_actual_creation_receipt(self):
        result = flow.invoke(
            self.root,
            *self.arguments("--scope-path", "../outside", "--format", "summary"),
            success=False,
        )
        self.assertEqual(result["outcome"], "incomplete")
        self.assertFalse(result["atomic"])
        self.assertEqual(len(result["receipts"]), 1)
        self.assertEqual(result["receipts"][0]["outcome"], "applied")
        observed = self.observe()
        self.assertEqual(observed["projection"]["identity"]["status"], "open")
        self.assertEqual(
            result["receipts"][0]["source_sha256_after"],
            observed["projection"]["source"]["digest"],
        )
        self.assertFalse((self.parent / "outside").exists())

    def test_summary_refusal_uses_actual_scope_owner(self):
        flow.invoke(self.root, *self.arguments("--scope-path", "result.txt"))
        (self.root / "other.txt").write_text("Not owned.\n")
        before = (self.root / flow.ISSUE).read_bytes()
        digest = self.observe()["projection"]["source"]["digest"]
        result = flow.invoke(
            self.root,
            "repository",
            "commit",
            "--repository-root",
            str(self.root),
            "--issue-ref",
            flow.REF,
            "--expected-issue-source-sha256",
            digest,
            "--actor-ref",
            flow.ACTOR,
            "--actor-evidence-ref",
            "fixture:" + flow.ACTOR,
            "--message",
            "Must refuse",
            "--path",
            "other.txt",
            "--format",
            "summary",
            success=False,
        )
        self.assertEqual(result["outcome"], "out_of_scope")
        self.assertEqual(result["reference_update"], "not_run")
        self.assertIsNotNone(result["operator_ref"])
        self.assertIsNone(result["publication_receipt_ref"])
        self.assertEqual((self.root / flow.ISSUE).read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
