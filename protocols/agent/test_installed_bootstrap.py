"""Installed contract/setup proofs. Raw Git is disposable fixture setup only."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

CLI = Path(sys.executable).parent / "aware"
PUBLIC = Path(__file__).resolve().parents[2]


def run(root, *arguments, success=True):
    result = subprocess.run([str(CLI), *arguments], cwd=root, text=True, capture_output=True)
    if result.returncode != (0 if success else 2):
        raise AssertionError((result.returncode, result.stdout, result.stderr))
    return json.loads(result.stdout or result.stderr)


def snapshot(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file() and not p.is_symlink() and ".git" not in p.relative_to(root).parts}


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="aware-bootstrap-proof-")
        self.root = Path(self.temporary.name) / "customer"
        self.root.mkdir()
        for arguments in [["init", "-q", "-b", "main"], ["config", "user.name", "Fixture"], ["config", "user.email", "fixture@example.invalid"]]:
            subprocess.run(["git", *arguments], cwd=self.root, check=True, capture_output=True)
        (self.root / "result.txt").write_text("seed\n")
        subprocess.run(["git", "add", "--", "result.txt"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "test-only seed"], cwd=self.root, check=True)

    def tearDown(self):
        self.temporary.cleanup()

    def init(self, *args, success=True):
        return run(self.root, "init", "--repository-root", str(self.root), *args, success=success)

    def test_installed_contract_matches_authored_templates(self):
        result = run(self.root, "contract")
        source = PUBLIC / "protocols/contracts/agent-fs/v1.1.0"
        authored = json.loads((source / "contract.json").read_bytes())
        self.assertEqual(result["contract_ref"], "aware.agent.fs.v1")
        self.assertEqual(result["version"], "1.1.0")
        self.assertEqual(result["actor_authentication"], "unavailable")
        for target, relative in authored["files"].items():
            self.assertEqual(result["template_sha256"][target], hashlib.sha256((source / relative).read_bytes()).hexdigest())

    def test_contract_observation_does_not_write_customer_files(self):
        before = snapshot(self.root)
        run(self.root, "contract")
        self.assertEqual(before, snapshot(self.root))

    def test_complete_missing_scaffold_and_hashes(self):
        result = self.init()
        self.assertEqual(len(result["created"]), 12)
        self.assertFalse(result["manual_integration_required"])
        provenance = json.loads((self.root / ".aware/agent-bootstrap.json").read_bytes())
        self.assertEqual(provenance["contract_ref"], "aware.agent.fs.v1")
        self.assertEqual(provenance["version"], "1.1.0")
        for target, expected in provenance["rendered_sha256"].items():
            self.assertEqual(hashlib.sha256((self.root / target).read_bytes()).hexdigest(), expected)
        text = (self.root / "AGENTS.md").read_text()
        self.assertIn(str(CLI.resolve()), text)
        self.assertIn("## 8. Close or hand off explicitly", text)
        self.assertNotIn("{{", text)

    def test_existing_agents_preserved_without_implicit_link(self):
        original = b"# Customer rules\nNo unrelated edits.\n"
        (self.root / "AGENTS.md").write_bytes(original)
        result = self.init()
        self.assertEqual((self.root / "AGENTS.md").read_bytes(), original)
        self.assertTrue(result["manual_integration_required"])
        self.assertFalse(result["linked_existing_agents"])

    def test_explicit_link_preserves_original_instructions(self):
        original = b"# Customer policy\r\nPreserve these exact bytes.\r\n"
        (self.root / "AGENTS.md").write_bytes(original)
        result = self.init("--link-existing-agents")
        text = (self.root / "AGENTS.md").read_bytes()
        self.assertTrue(text.startswith(original))
        self.assertIn(b"<!-- aware-agent-contract:start -->", text)
        self.assertTrue(result["linked_existing_agents"])
        self.assertFalse(result["manual_integration_required"])

    def test_existing_documentation_is_not_overwritten(self):
        path = self.root / "docs/alignment/CURRENT.md"
        path.parent.mkdir(parents=True)
        original = b"Customer-approved existing context.\n"
        path.write_bytes(original)
        result = self.init()
        self.assertEqual(path.read_bytes(), original)
        self.assertIn("docs/alignment/CURRENT.md", result["preserved"])
        self.assertTrue(result["manual_integration_required"])

    def test_outside_agents_symlink_refuses_before_setup_writes(self):
        outside = Path(self.temporary.name) / "outside.md"
        outside.write_text("Must survive.\n")
        (self.root / "AGENTS.md").symlink_to(outside)
        before = snapshot(self.root)
        result = self.init("--link-existing-agents", success=False)
        self.assertIn("bootstrap_target_unresolvable", json.dumps(result))
        self.assertEqual(before, snapshot(self.root))
        self.assertEqual(outside.read_text(), "Must survive.\n")

    def test_outside_documentation_parent_refuses_before_setup_writes(self):
        outside = Path(self.temporary.name) / "outside-docs"
        outside.mkdir()
        (self.root / "docs").symlink_to(outside, target_is_directory=True)
        before = snapshot(self.root)
        self.init(success=False)
        self.assertEqual(before, snapshot(self.root))
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlink_loop_refuses_before_setup_writes(self):
        (self.root / ".aware").symlink_to(".aware")
        before = snapshot(self.root)
        result = self.init(success=False)
        self.assertIn("unresolvable", json.dumps(result))
        self.assertEqual(before, snapshot(self.root))

    def test_existing_managed_link_requires_explicit_upgrade(self):
        (self.root / "AGENTS.md").write_text("<!-- aware-agent-contract:start -->\nPrevious customer link.\n")
        before = snapshot(self.root)
        result = self.init("--link-existing-agents", success=False)
        self.assertIn("requires_reviewed_upgrade", json.dumps(result))
        self.assertEqual(before, snapshot(self.root))

    def test_partial_prior_setup_is_not_silently_replaced(self):
        path = self.root / ".aware/agent-bootstrap.json"
        path.parent.mkdir()
        path.write_text('{"version":"customer-old"}\n')
        before = snapshot(self.root)
        self.init(success=False)
        self.assertEqual(before, snapshot(self.root))

    def test_repeated_init_never_upgrades_or_rewrites(self):
        self.init()
        before = snapshot(self.root)
        self.init(success=False)
        self.assertEqual(before, snapshot(self.root))

    def test_all_rendered_contract_links_resolve(self):
        result = self.init()
        for name in result["created"]:
            if not name.endswith(".md"):
                continue
            path = self.root / name
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if "://" not in target and not target.startswith("#"):
                    self.assertTrue((path.parent / target.split("#")[0]).exists(), (name, target))

    def test_declared_profile_matches_real_protocol_admission(self):
        self.init()
        from aware_protocol_fs_adapter import admit_protocol_manifest
        admitted = admit_protocol_manifest(repository_root=self.root, manifest_path=self.root / "aware.protocol.toml")
        self.assertIsNotNone(admitted.filesystem_profile)
        self.assertEqual(admitted.diagnostics, ())

    def test_rendered_shell_is_syntax_safe_for_quoted_command(self):
        from aware_agent_cli.setup import render_document, template_inputs
        _, templates = template_inputs()
        rendered = render_document(templates["AGENTS.md"], "/tmp/customer space/'quoted$/bin/aware").decode()
        block = re.search(r"```sh\n(.*?)```", rendered, re.S).group(1)
        subprocess.run(["bash", "-n"], input=block, text=True, check=True)
        self.assertNotIn("{{", rendered)


if __name__ == "__main__":
    unittest.main()
