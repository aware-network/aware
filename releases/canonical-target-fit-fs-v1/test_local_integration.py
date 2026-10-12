"""Maintainer proof of exact target-fit integration; not unassisted evaluation."""

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "releases/canonical-target-fit-fs-v1"
PREDECESSOR = ROOT / "releases/canonical-draft-preparation-fs-v1"
BASELINE = "9bcd6ec319fe56df786a2306968ab7df45369135"
LAYOUT_SHA = "fb2a5d53a399b41cef7da8d475ec37c23c484f903abcd4bae1d24750464bd62d"
ENVELOPE_SHA = "4823b609938c7d748bfc113ae2a54d7af697e6ca88e698716f538b3460f6b79e"
PAYLOAD_SHA = "e789f1016795098c094162c99766497700da10b182b36911daa8aa2e7c56b7fe"
ISSUE = (
    "docs/issues/2026/10/12/fb-2026-10-12-canonical-target-fit-public-integration-v0.md"
)
EXTRAS = {
    ISSUE,
    *[
        "releases/canonical-target-fit-fs-v1/" + name
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
        self.assertEqual(len(self.layout["files"]), 1332)
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
        self.assertEqual(len(self.layout["changed_files"]), 169)
        self.assertEqual(len(set(self.layout["changed_files"]) | EXTRAS), 173)
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
        self.assertEqual(len(index["files"]), 1157)
        self.assertEqual(len(mapping), 1157)
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
        archive = RELEASE / "canonical-target-fit-source-notice-review-v1.tar.gz"
        self.assertEqual(sha(archive.read_bytes()), ENVELOPE_SHA)
        _, members = verifier.verified_archive(archive.read_bytes(), ENVELOPE_SHA)
        delivery = json.loads((RELEASE / "DELIVERY-MAP.json").read_bytes())
        self.assertEqual(set(delivery), set(members))
        self.assertEqual(len(members), 1496)
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
            sum(
                not row["detected_legal_file_paths"]
                for row in json.loads(members["NOTICE-BINDINGS.json"])[
                    "aware_package_legal_inventory"
                ]
            ),
            6,
        )

    def test_reference_guard_and_closeout_guidance(self):
        readme = (ROOT / "README.md").read_text()
        self.assertIn("not two admitted", readme)
        self.assertIn("fb/YYYY-MM-DD/lowercase-hyphenated-slug", readme)
        self.assertIn("not atomic", readme)
        self.assertIn("unselected", readme)
        self.assertIn("expected shape", readme)
        self.assertIn("not Issue eligibility", readme)
        self.assertFalse(self.layout["workspace_agent_mount_admitted"])
        self.assertIn("detached wheels", (RELEASE / "README.md").read_text())
        self.assertIn(
            "live publication capability",
            (ROOT / "protocols/repository/README.md").read_text(),
        )

    def test_installer_only_coordinate_changes(self):
        import ast

        before = git("show", BASELINE + ":protocols/install.py").decode()
        after = (ROOT / "protocols/install.py").read_text()
        for new, old in {
            ENVELOPE_SHA: "3e1fab9a79c19476ece55a1f0d62aa7784e911d52a01d32b65655617bacdb9f8",
            PAYLOAD_SHA: "f2ef55bd871ee054e2f707189537ea533c46d013e8fdbc676a830f9968b94513",
            "canonical-target-fit-source-notice-review-v1.tar.gz": "canonical-draft-preparation-source-notice-review-v1.tar.gz",
            "canonical-target-fit-fs-v1": "canonical-draft-preparation-fs-v1",
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
        ):
            run([str(target / "bin/aware"), *args])
        run([str(target / "bin/aware"), "workspace", "--help"], 2)
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
                RELEASE / "canonical-target-fit-source-notice-review-v1.tar.gz"
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
                },
                indent=2,
            )
            + "\n"
        )


if __name__ == "__main__":
    unittest.main()
