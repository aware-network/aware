"""New-directory installed proofs; no raw Git seed commit or copied admission rule."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("workflow_helpers", Path(__file__).with_name("test_installed_workflow.py"))
flow = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(flow)
CLI = Path(sys.executable).parent / "aware"


class RepositorySetupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="aware-installed-genesis-")
        self.parent = Path(self.temporary.name)
        self.root = self.parent / "customer"

    def tearDown(self):
        self.temporary.cleanup()

    def invoke(self, *args, success=True):
        return flow.invoke(self.parent, *args, success=success)

    def init(self, *args, success=True):
        return self.invoke("init", "--repository-root", str(self.root), *args, success=success)

    def test_missing_repository_returns_actionable_refusal_without_writes(self):
        result = self.init(success=False)
        self.assertEqual(result["outcome"], "refused")
        self.assertIn("git_repository_required", result["diagnostics"])
        self.assertFalse(self.root.exists())

    def test_explicit_creation_then_first_real_issue_commit_close_and_recovery(self):
        initialized = self.init("--create-repository")
        self.assertEqual(initialized["repository_preparation"]["outcome"], "created")
        self.assertIsNone(initialized["repository_preparation"]["head"])
        self.assertNotEqual(subprocess.run(["git", "-C", str(self.root), "rev-parse", "--verify", "HEAD"], capture_output=True).returncode, 0)
        self.assertEqual(flow.git(self.root, "remote"), "")
        # Explicit fixture/customer author preparation, not an identity invented by Aware.
        flow.git(self.root, "config", "user.name", "Customer Fixture")
        flow.git(self.root, "config", "user.email", "customer@example.invalid")
        (self.root / "src").mkdir()
        (self.root / "src/result.py").write_text("value = 42\n")
        (self.root / "unrelated.txt").write_text("Preserve unrelated first-repository work.\n")
        flow.git(self.root, "add", "--", "unrelated.txt")  # staged-work fault injection only
        staged = flow.git(self.root, "show", ":unrelated.txt")
        paths = [*initialized["created"], "src/result.py", flow.ISSUE]
        args = ["issue", "open", "--repository-root", str(self.root), "--issue-ref", flow.REF,
                "--title", "First customer result", "--client-intent-id", "new-repository-open",
                "--problem", "A new repository needs its first governed contribution.",
                "--objective", "Publish the exact approved first contribution.",
                "--acceptance", "Preserve foreign staging and use the shared commit owner.",
                "--actor-ref", flow.ACTOR, "--actor-evidence-ref", "fixture:" + flow.ACTOR]
        for path in paths:
            args.extend(["--scope-path", path])
        self.assertEqual(self.invoke(*args)["outcome"], "opened")
        flow.mutation(self.root, "append-update", "--message", "Customer outcome: value=42; verification executed in this installed test.")

        def publish(dry=False):
            observed = flow.invoke(self.root, "issue", "resolve-read-projection", "--repository-root", str(self.root), "--issue-ref", flow.REF)
            args = ["repository", "commit", "--repository-root", str(self.root), "--issue-ref", flow.REF,
                    "--expected-issue-source-sha256", observed["projection"]["source"]["digest"],
                    "--actor-ref", flow.ACTOR, "--actor-evidence-ref", "fixture:" + flow.ACTOR,
                    "--message", "First scoped customer publication"]
            for path in paths:
                args.extend(["--path", path])
            if dry:
                args.append("--dry-run")
            return self.invoke(*args)

        self.assertEqual(publish(True)["outcome"], "planned")
        published = publish()
        self.assertEqual(published["outcome"], "applied")
        first = published["commit_hash"]
        self.assertEqual(flow.git(self.root, "rev-list", "--count", first), "1")
        self.assertEqual(set(flow.git(self.root, "ls-tree", "-r", "--name-only", first).splitlines()), set(paths))
        self.assertEqual(flow.git(self.root, "show", ":unrelated.txt"), staged)
        closed = flow.mutation(self.root, "close", "--resolution", "First real customer result delivered",
                               "--verified-by", "Installed test confirms value=42 and one root commit",
                               "--publication-receipt-ref", published["publication_receipt_ref"])
        self.assertEqual(closed["outcome"], "applied")
        # Separate process reads only durable records; this is installed proof, not external R acceptance.
        recovered = subprocess.run([str(CLI), "issue", "resolve-read-projection", "--repository-root", str(self.root),
                                    "--issue-ref", flow.REF], cwd=self.parent, capture_output=True, text=True,
                                   env={"PATH": "/usr/bin:/bin", "HOME": str(self.parent), "LANG": "C.UTF-8"}, check=True)
        projection = json.loads(recovered.stdout)["projection"]
        self.assertEqual(projection["identity"]["status"], "closed")
        self.assertEqual(projection["identity"]["owner_ref"], flow.ACTOR)
        self.assertEqual((self.root / "unrelated.txt").read_text(), "Preserve unrelated first-repository work.\n")

    def test_prepare_dry_run_writes_nothing(self):
        result = self.invoke("repository", "create", "--repository-root", str(self.root), "--dry-run")
        self.assertEqual(result["outcome"], "planned")
        self.assertFalse(self.root.exists())

    def test_create_then_init_on_unborn_existing_root(self):
        self.assertEqual(self.invoke("repository", "create", "--repository-root", str(self.root))["outcome"], "created")
        head = (self.root / ".git/HEAD").read_bytes()
        result = self.init()
        self.assertEqual(result["repository_preparation"]["outcome"], "existing")
        self.assertIsNone(result["repository_preparation"]["head"])
        self.assertEqual((self.root / ".git/HEAD").read_bytes(), head)

    def test_nonempty_non_git_target_preserved(self):
        self.root.mkdir()
        (self.root / "customer.txt").write_bytes(b"customer preimage")
        result = self.init("--create-repository", success=False)
        self.assertIn("repository_creation_requires_empty_target", result["diagnostics"])
        self.assertEqual((self.root / "customer.txt").read_bytes(), b"customer preimage")
        self.assertFalse((self.root / ".git").exists())

    def test_nested_creation_refuses_without_mutating_parent_repository(self):
        self.invoke("repository", "create", "--repository-root", str(self.parent))
        before = (self.parent / ".git/HEAD").read_bytes()
        result = self.init("--create-repository", success=False)
        self.assertIn("nested_repository_creation_refused", result["diagnostics"])
        self.assertEqual((self.parent / ".git/HEAD").read_bytes(), before)
        self.assertFalse(self.root.exists())

    def test_symlink_root_refuses_without_target_changes(self):
        target = self.parent / "real"
        target.mkdir()
        self.root.symlink_to(target, target_is_directory=True)
        result = self.init("--create-repository", success=False)
        self.assertIn("repository_symlink_path_refused", result["diagnostics"])
        self.assertEqual(list(target.iterdir()), [])

    def test_file_root_returns_typed_refusal(self):
        self.root.write_bytes(b"preserved")
        result = self.init("--create-repository", success=False)
        self.assertIn("repository_directory_required", result["diagnostics"])
        self.assertEqual(self.root.read_bytes(), b"preserved")

    def test_provider_does_not_import_ambient_git_target(self):
        outside = self.parent / "other"
        self.invoke("repository", "create", "--repository-root", str(outside))
        environment = dict(os.environ, GIT_DIR=str(outside / ".git"), GIT_WORK_TREE=str(outside))
        result = subprocess.run([str(CLI), "init", "--repository-root", str(self.root)], env=environment,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("git_repository_required", json.loads(result.stderr)["diagnostics"])
        self.assertFalse(self.root.exists())

    def test_sdk_rejects_untyped_requests_and_results(self):
        from aware_repository_sdk import RepositorySdkOperationClient, RepositoryPrepareRequest
        class Forged:
            def prepare_repository(self, request):
                return {"outcome": "created"}
        client = RepositorySdkOperationClient(provider=Forged())
        with self.assertRaises(TypeError):
            client.prepare_repository({"repository_root": str(self.root)})
        with self.assertRaises(TypeError):
            client.prepare_repository(RepositoryPrepareRequest(str(self.root)))


if __name__ == "__main__":
    unittest.main()
