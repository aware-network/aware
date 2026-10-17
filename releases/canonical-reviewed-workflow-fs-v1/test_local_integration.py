"""Maintainer proof of exact reviewed-workflow integration; not unassisted evaluation."""

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "releases/canonical-reviewed-workflow-fs-v1"
PREDECESSOR = ROOT / "releases/canonical-workspace-a1-fs-v1"
BASELINE = "001457643287a15c9b1e6b379f58c09cecc9def2"
LAYOUT_SHA = "bef22ce66bf6c218e2c89a828ed9750d9dba5fea7737f085e6310b813931d221"
ENVELOPE_SHA = "03eb59691cfa1aa1e01e95a7c2727eb3d093ac28e5bd26ae7073416bb61f01b2"
PAYLOAD_SHA = "899b2ef4beabf074fbdf7ea5980d4eaea1967ef4318b3ebc772814ee84b54727"
ISSUE = "docs/issues/2026/10/17/fb-2026-10-17-canonical-reviewed-workflow-public-integration-v0.md"
EXTRAS = {
    ISSUE,
    *[
        "releases/canonical-reviewed-workflow-fs-v1/" + name
        for name in (
            "LAYOUT-REVIEW.json",
            "LOCAL-INTEGRATION.md",
            "test_local_integration.py",
        )
    ],
}


def sha(body):
    return hashlib.sha256(body).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


class Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layout = json.loads((RELEASE / "LAYOUT-REVIEW.json").read_bytes())

    def test_accepted_layout_and_exact_file_set(self):
        self.assertEqual(sha((RELEASE / "LAYOUT-REVIEW.json").read_bytes()), LAYOUT_SHA)
        actual = set()
        for parent, directories, files in os.walk(ROOT):
            directories[:] = [name for name in directories if name != ".git"]
            for name in files:
                path = Path(parent) / name
                self.assertFalse(path.is_symlink())
                actual.add(str(path.relative_to(ROOT)))
        self.assertEqual(actual, set(self.layout["files"]) | EXTRAS)
        self.assertEqual(len(self.layout["files"]), 1581)
        for name, row in self.layout["files"].items():
            path = ROOT / name
            self.assertEqual(sha(path.read_bytes()), row["sha256"], name)
            self.assertEqual(path.stat().st_size, row["bytes"], name)
            self.assertEqual(
                bool(path.stat().st_mode & 0o111),
                bool(int(row["mode"], 8) & 0o111),
                name,
            )

    def test_exact_scope_and_preserved_baseline(self):
        baseline = set(
            git("ls-tree", "-r", "--name-only", BASELINE).decode().splitlines()
        )
        self.assertEqual(baseline, set(self.layout["baseline_dispositions"]))
        self.assertEqual(len(self.layout["changed_files"]), 127)
        self.assertEqual(len(set(self.layout["changed_files"]) | EXTRAS), 131)
        self.assertFalse(
            any(
                row["after_sha256"] is None
                for row in self.layout["changed_files"].values()
            )
        )
        before_modes = dict(
            line.split("\t", 1)[::-1]
            for line in git("ls-tree", "-r", BASELINE).decode().splitlines()
        )
        for name, row in self.layout["baseline_dispositions"].items():
            if row["disposition"] == "preserved":
                self.assertEqual(
                    (ROOT / name).read_bytes(), git("show", BASELINE + ":" + name), name
                )
            self.assertEqual(
                bool((ROOT / name).stat().st_mode & 0o111),
                before_modes[name].startswith("100755"),
                name,
            )
        self.assertFalse(self.layout["selected"])
        self.assertFalse(self.layout["instructions_frozen"])
        self.assertFalse(self.layout["publication_authorized"])

    def test_issue_scope_and_contributor_selection(self):
        issue = (ROOT / ISSUE).read_text()
        scope = issue.split("## Ownership Scope", 1)[1].split("##", 1)[0]
        actual = {
            line.strip()[3:-1]
            for line in scope.splitlines()
            if line.strip().startswith("- `")
        }
        self.assertEqual(actual, set(self.layout["changed_files"]) | EXTRAS)
        for name in (
            "AGENTS.md",
            "CONTRIBUTING.md",
            "aware.protocol.toml",
            "releases/SELECTED.json",
        ):
            self.assertEqual(
                (ROOT / name).read_bytes(), git("show", BASELINE + ":" + name)
            )
        for name, row in self.layout["baseline_dispositions"].items():
            if name.startswith(
                (
                    ".aware/",
                    "docs/agents/",
                    "protocols/contracts/",
                    "releases/canonical-",
                )
            ):
                self.assertEqual(sha((ROOT / name).read_bytes()), row["sha256"])

    def test_one_profile_source_tree(self):
        index = json.loads((RELEASE / "SOURCE-INDEX.json").read_bytes())
        mapping = json.loads((RELEASE / "SOURCE-MAP.json").read_bytes())
        self.assertEqual(index["canonical_profile"], "portable_protocols")
        self.assertEqual(len(index["files"]), 1329)
        self.assertEqual(len(mapping), 1329)
        for name, row in mapping.items():
            self.assertEqual(
                sha((ROOT / row["path"]).read_bytes()), row["sha256"], name
            )
        self.assertEqual(len(list(ROOT.glob("workspaces/**/pyproject.toml"))), 28)
        self.assertFalse((ROOT / "workspaces/previews").exists())
        self.assertFalse((ROOT / "protocols/collaboration/previews").exists())

    def test_whole_envelope_and_unsuppressed_findings(self):
        spec = importlib.util.spec_from_file_location(
            "target_fit_verifier", RELEASE / "archive_verifier.py"
        )
        assert spec and spec.loader
        verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier)
        archive = RELEASE / "canonical-reviewed-workflow-source-notice-review-v1.tar.gz"
        self.assertEqual(sha(archive.read_bytes()), ENVELOPE_SHA)
        _, members = verifier.verified_archive(archive.read_bytes(), ENVELOPE_SHA)
        delivery = json.loads((RELEASE / "DELIVERY-MAP.json").read_bytes())
        self.assertEqual(set(delivery), set(members))
        self.assertEqual(len(members), 1788)
        for name, row in delivery.items():
            self.assertEqual(sha(members[name]), row["sha256"], name)
        for name in (
            "LICENSE",
            "NOTICE",
            "SOURCE-INDEX.json",
            "NOTICE-BINDINGS.json",
            "CONTENT-AUDIT.json",
        ):
            self.assertEqual((RELEASE / name).read_bytes(), members[name])
        self.assertEqual(len(json.loads(members["CONTENT-AUDIT.json"])["findings"]), 12)
        self.assertEqual(
            len(json.loads(members["NOTICE-BINDINGS.json"])["detached_wheel_gaps"]),
            6,
        )

    def test_reference_guard_and_closeout_guidance(self):
        readme = (ROOT / "README.md").read_text()
        self.assertIn("not two admitted", readme)
        self.assertIn("fb/YYYY-MM-DD/lowercase-hyphenated-slug", readme)
        self.assertIn("not an atomic transaction", readme)
        self.assertIn("unselected", readme)
        workflow = (ROOT / "protocols/WORKFLOW.md").read_text()
        self.assertIn("the complete shape is", workflow)
        self.assertIn(
            "not Issue eligibility", (ROOT / "protocols/WORKFLOW.md").read_text()
        )
        self.assertTrue(self.layout["source_is_composite"])
        self.assertTrue(self.layout["whole_envelope_required"])
        self.assertEqual(
            self.layout["workspace_mount_profile"],
            "bounded-reviewed-repository-manifest-a1",
        )
        self.assertFalse(self.layout["a2_admitted"])
        self.assertFalse(self.layout["tree_completion_admitted"])
        self.assertFalse(self.layout["unassisted_onboarding_proven"])
        self.assertIn("does not admit an Issue", readme)
        self.assertIn("not unassisted onboarding", readme)
        guide = (ROOT / "protocols/workspace/REVIEWED-SETUP.md").read_text()
        self.assertIn("--accept-reviewed-effect-scope", guide)
        self.assertIn("--accept-reviewed-final-files", guide)
        self.assertIn("detached-wheel legal gaps", (RELEASE / "README.md").read_text())
        self.assertIn(
            "live publication capability",
            (ROOT / "protocols/repository/README.md").read_text(),
        )

    def test_installer_only_coordinate_changes(self):
        import ast

        before = git("show", BASELINE + ":protocols/install.py").decode()
        after = (ROOT / "protocols/install.py").read_text()
        for new, old in {
            ENVELOPE_SHA: "de8740f8e2fd84be257704407e43ffc9a687d23f219becae3f992798519e739a",
            PAYLOAD_SHA: "a62e7f96d93c233302824ef6820d96b944867ef2338a121000976ea8a3ca1fe5",
            "canonical-reviewed-workflow-source-notice-review-v1.tar.gz": "canonical-workspace-a1-source-notice-review-v1.tar.gz",
            "canonical-reviewed-workflow-fs-v1": "canonical-workspace-a1-fs-v1",
        }.items():
            after = after.replace(new, old)
        self.assertEqual(ast.dump(ast.parse(after)), ast.dump(ast.parse(before)))

    def test_fresh_offline_hidden_install_and_refusals(self):
        scratch = Path(os.environ["AWARE_INITIALIZER_INTEGRATION_REPLAY_ROOT"])
        self.assertTrue(scratch.is_dir() and not scratch.is_symlink())
        self.assertEqual(scratch.stat().st_mode & 0o777, 0o700)
        target = scratch / "env"
        self.assertFalse(target.exists() or target.is_symlink())
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
            "--ro-bind",
            str(ROOT),
            "/mnt",
            "--clearenv",
            "--setenv",
            "PATH",
            "/usr/bin:/bin",
            "--setenv",
            "LANG",
            "C.UTF-8",
            "--setenv",
            "TMPDIR",
            str(scratch),
            "--chdir",
            "/mnt",
            "--",
        ]
        commands = []

        def run(args, expected=0):
            result = subprocess.run(
                prefix + args, capture_output=True, text=True, timeout=180, check=False
            )
            commands.append(
                {
                    "argv": args,
                    "exit": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )
            (scratch / "commands.json").write_text(
                json.dumps(commands, indent=2) + "\n"
            )
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            return result

        command = [
            "/usr/bin/python3.12",
            "protocols/install.py",
            "--python-executable",
            "/usr/bin/python3.12",
            "--venv",
            str(target),
        ]
        receipt = json.loads(run(command).stdout.splitlines()[-1])
        self.assertEqual(receipt["packet_sha256"], ENVELOPE_SHA)
        self.assertEqual(receipt["payload_sha256"], PAYLOAD_SHA)
        retained = Path(receipt["retained_source_and_notices"])
        for name in ("LICENSE", "NOTICE", "source/THIRD_PARTY_NOTICES.md"):
            self.assertTrue((retained / name).is_file())
        for args in (
            ["--help"],
            ["init", "--help"],
            ["issue", "--help"],
            ["protocol", "--help"],
            ["spec", "--help"],
            ["spec", "prepare-draft", "--help"],
            ["spec", "present-receipt", "--help"],
            ["workspace", "--help"],
            ["workspace", "review", "--help"],
            ["workspace", "setup", "--help"],
            ["workspace", "setup", "repository", "--help"],
            ["workspace", "setup", "workspace", "--help"],
            ["workspace", "setup", "module", "--help"],
            ["workspace", "setup", "python-package", "--help"],
            ["workspace", "setup", "align", "--help"],
        ):
            run([str(target / "bin/aware"), *args])
        refused = json.loads(
            run(
                [
                    str(target / "bin/aware"),
                    "init",
                    "--repo-root",
                    str(scratch / "missing-identity"),
                    "--create-repository",
                ],
                2,
            ).stdout
        )
        self.assertEqual(refused["effect"], "none")
        self.assertFalse((scratch / "missing-identity").exists())
        versions = json.loads(
            run(
                [
                    str(target / "bin/python"),
                    "-I",
                    "-c",
                    "import importlib.metadata as m,json; ds=[d for d in m.distributions() if d.metadata['Name']!='pip']; assert not any(d.read_text('direct_url.json') for d in ds); print(json.dumps({d.metadata['Name']:d.version for d in ds}))",
                ]
            ).stdout
        )
        path = RELEASE / "archive_verifier.py"
        spec = importlib.util.spec_from_file_location(
            "installed_envelope_verifier", path
        )
        assert spec and spec.loader
        verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier)
        _, outer = verifier.verified_archive(
            (
                RELEASE / "canonical-reviewed-workflow-source-notice-review-v1.tar.gz"
            ).read_bytes(),
            ENVELOPE_SHA,
        )
        _, inner = verifier.verified_archive(
            outer["payload/aware-canonical-neutral-fs-internal-v1.tar.gz"], PAYLOAD_SHA
        )
        normalize = lambda name: re.sub(r"[-_.]+", "-", name).lower()
        self.assertEqual(
            {normalize(k): v for k, v in versions.items()},
            {
                normalize(row["name"]): row["version"]
                for row in json.loads(inner["consumer-lock.json"])["packages"]
            },
        )
        self.assertEqual(len(versions), 42)
        run([str(target / "bin/python"), "-I", "-m", "pip", "check"])
        self.assertIn("installation_target_must_be_new", run(command, 2).stderr)
        self.assertEqual(scratch.stat().st_mode & 0o777, 0o700)
        (scratch / "installed-receipt.json").write_text(
            json.dumps(
                {
                    "installation": receipt,
                    "versions": versions,
                    "missing_harness_effect": refused["effect"],
                    "domain_matrix_replayed": False,
                    "governed_a1_replayed": False,
                    "unassisted_U": False,
                },
                indent=2,
            )
            + "\n"
        )


if __name__ == "__main__":
    unittest.main()
