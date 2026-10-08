"""Maintainer byte accounting and installed activation; no customer policy."""

import hashlib
import io
import json
import os
import re
import subprocess
import tarfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASELINE = "095b9c5cad57e8d4183533f385c7cf568caeb277"
LAYOUT_SHA = "01c9b62cbd7589aad845ee5010337c4ca2a4a9306525a0479067d334bb0f4da7"
PACKET_SHA = "d135c339b7c14d28d2df1ed7c4335fad71e3d5e163c3ede70f3cef692c679f75"
PAYLOAD_SHA = "6225a71ca27450170ec3b1d55336191d52fc5346c7739fff73141febb4877fb1"
ISSUE_PATH = (
    "docs/issues/2026/10/08/fb-2026-10-08-canonical-neutral-local-integration-v1.md"
)
INTERFACES = ["aware-issue-cli", "aware-protocol", "aware-spec"]


def sha(body):
    return hashlib.sha256(body).hexdigest()


class LocalIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.layout = json.loads((HERE / "layout-review.json").read_bytes())
        self.delivery = json.loads((HERE / "delivery.json").read_bytes())

    def test_exact_review_receipt_and_unselected_state(self):
        self.assertEqual(sha((HERE / "layout-review.json").read_bytes()), LAYOUT_SHA)
        self.assertEqual(self.layout["baseline_revision"], BASELINE)
        self.assertFalse(self.layout["publication_authorized"])
        self.assertFalse(self.layout["public_selection_authorized"])
        self.assertEqual(self.delivery["supported_interfaces"], INTERFACES)
        self.assertEqual(
            self.delivery["selection_owner"],
            "Workspace portable_protocols; no layout selection",
        )

    def test_all_863_reviewed_postimages(self):
        self.assertEqual(len(self.layout["changed_files"]), 863)
        self.assertEqual(
            sum(
                row["before_sha256"] is None
                for row in self.layout["changed_files"].values()
            ),
            861,
        )
        for name, row in self.layout["changed_files"].items():
            with self.subTest(name=name):
                path = ROOT / name
                self.assertFalse(path.is_symlink())
                self.assertEqual(
                    (sha(path.read_bytes()), path.stat().st_size),
                    (row["sha256"], row["bytes"]),
                )

    def test_baseline_bytes_and_git_modes_preserved(self):
        raw = subprocess.check_output(["git", "-C", str(ROOT), "archive", BASELINE])
        kept = total = 0
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            for member in archive.getmembers():
                if not member.isfile():
                    continue
                total += 1
                path = ROOT / member.name
                self.assertFalse(path.is_symlink())
                # Git retains executable/non-executable mode, not checkout
                # umask permission bits represented by an archive header.
                self.assertEqual(
                    bool(path.stat().st_mode & 0o111), bool(member.mode & 0o111)
                )
                body = archive.extractfile(member).read()
                if member.name in self.layout["changed_files"]:
                    self.assertEqual(
                        sha(body),
                        self.layout["changed_files"][member.name]["before_sha256"],
                    )
                else:
                    self.assertEqual(path.read_bytes(), body, member.name)
                    kept += 1
        self.assertEqual((total, kept), (2379, 2377))
        self.assertEqual(
            {
                name
                for name, row in self.layout["changed_files"].items()
                if row["before_sha256"] is not None
            },
            {"README.md", "workspaces/README.md"},
        )

    def test_exact_867_path_local_integration(self):
        extras = {
            str((HERE / name).relative_to(ROOT))
            for name in (
                "layout-review.json",
                "LOCAL-INTEGRATION.md",
                "test_local_integration.py",
            )
        } | {ISSUE_PATH}
        expected = set(self.layout["changed_files"]) | extras
        changed = set(
            subprocess.check_output(
                ["git", "-C", str(ROOT), "diff", BASELINE, "--name-only"], text=True
            ).splitlines()
        )
        untracked = set(
            subprocess.check_output(
                ["git", "-C", str(ROOT), "ls-files", "--others", "--exclude-standard"],
                text=True,
            ).splitlines()
        )
        self.assertEqual(changed | untracked, expected)
        self.assertEqual(len(expected), 867)

    def test_all_853_packet_member_mappings(self):
        self.assertEqual(len(self.delivery["packet_member_map"]), 853)
        sources = []
        for original, row in self.delivery["packet_member_map"].items():
            path = ROOT / row["path"]
            self.assertFalse(path.is_symlink())
            self.assertEqual(
                (sha(path.read_bytes()), path.stat().st_size),
                (row["sha256"], row["bytes"]),
                original,
            )
            if original.startswith("source/"):
                sources.append(row["path"])
        self.assertEqual(len(sources), 533)
        self.assertTrue(
            all(
                name.startswith("workspaces/previews/canonical-fs-v1/")
                for name in sources
            )
        )
        self.assertFalse(
            any(
                part in name
                for name in sources
                for part in ("/services/", "/ontology/", "/experience/")
            )
        )

    def test_exact_archive_installer_and_verifier(self):
        for name, digest in {
            "distribution/canonical-neutral-source-notice-review-v1.tar.gz": PACKET_SHA,
            "packet/payload/aware-canonical-neutral-fs-internal-v1.tar.gz": PAYLOAD_SHA,
            "install.py": "2777f66da40a39709cc843685dc84fe4f49eb23cdfece380ebf2c411d253aaf5",
            "example-draft-input.py": "775c29cabf3fe662807a489fe5f9b19b9c9a5d45277a81e222e8f58c4fe49552",
        }.items():
            self.assertEqual(sha((HERE / name).read_bytes()), digest)
        self.assertEqual(
            sha((ROOT / "protocols/install.py").read_bytes()),
            "032febe109cf145c65f5edaf14403fc58e7b4e93397535d0327e5ce1a65c6ca9",
        )

    def test_notice_bindings_and_historical_source_boundary(self):
        notices = json.loads((HERE / "packet/NOTICE-BINDINGS.json").read_bytes())
        self.assertEqual(notices["candidate_archive_sha256"], PAYLOAD_SHA)
        self.assertEqual(len(notices["wheel_legal_copies"]), 49)
        self.assertEqual(len(notices["inherited_notice_inputs"]), 236)
        self.assertEqual(len(notices["new_notice_inputs"]), 23)
        source = ROOT / "workspaces/previews/canonical-fs-v1"
        self.assertTrue((source / "original/README.md").is_file())
        self.assertNotEqual(
            (source / "README.md").read_bytes(),
            (source / "original/README.md").read_bytes(),
        )

    def test_existing_selections_and_bootstrap_unchanged(self):
        agent = json.loads((ROOT / "protocols/agent/release.json").read_bytes())
        self.assertEqual(agent["version"], "0.1.0a6")
        self.assertEqual(agent["agent_contract"]["version"], "1.2.1")
        # Baseline byte/mode test verifies every predecessor selection document,
        # installer and root AGENTS.md, not a newly authored selection interpretation.
        self.assertFalse((ROOT / "protocols/collaboration/selection.json").exists())
        self.assertIn("unselected", (HERE / "README.md").read_text())

    def test_whitespace_diagnostic_hashes_raw_stdout(self):
        diagnostic = subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "diff",
                "--check",
                BASELINE,
                "5d3ca0893395caa92a126cc110be8294347052c4",
            ],
            capture_output=True,
            check=False,
        )
        self.assertEqual(diagnostic.returncode, 2)
        self.assertEqual(diagnostic.stderr, b"")
        self.assertEqual(len(diagnostic.stdout), 76907)
        self.assertEqual(diagnostic.stdout.count(b"\r\n"), 199)
        self.assertEqual(
            sha(diagnostic.stdout),
            "24303e1d02dc86827d367fd423097b0886890d2a210bd835013f62c1a2c4c36e",
        )
        rows = [
            row
            for row in diagnostic.stdout.splitlines()
            if b": trailing whitespace." in row or b": new blank line at EOF." in row
        ]
        self.assertEqual(len(rows), 459)
        self.assertEqual(len({row.split(b":", 1)[0] for row in rows}), 21)
        # Reproduce the incorrect text-mode capture without changing any input.
        normalized = diagnostic.stdout.decode().replace("\r\n", "\n").encode()
        self.assertEqual(
            sha(normalized),
            "73f4ca19037cac4cc10c02165f95917a9e7e4799d204bcd52e1ae1dac9bcaa61",
        )
        self.assertNotEqual(sha(normalized), sha(diagnostic.stdout))

    def test_local_links_and_instruction_limits(self):
        for path in (
            HERE / "README.md",
            HERE / "WORKFLOW.md",
            HERE / "LOCAL-INTEGRATION.md",
            ROOT / "workspaces/previews/canonical-fs-v1/README.md",
        ):
            for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if not link.startswith(("https:", "http:", "#")):
                    self.assertTrue((path.parent / link).is_file(), (str(path), link))
        text = (HERE / "README.md").read_text()
        for phrase in (
            "review-only",
            "three family commands",
            "no aware init",
            "already prepared",
            "Never overlay",
            "Instructions remain draft",
            "continuous",
            "not distribution packages",
        ):
            self.assertIn(phrase, text)
        flow = (HERE / "WORKFLOW.md").read_text()
        for phrase in (
            "source_sha256",
            "input_sha256",
            "repository-relative",
            "absolute snapshot",
            "Never automatically retry known publication",
        ):
            self.assertIn(phrase, flow)

    def test_fresh_offline_integrated_installation(self):
        scratch = Path(os.environ["AWARE_CANONICAL_INTEGRATION_REPLAY_ROOT"])
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
            "/tmp",
            "--ro-bind",
            str(ROOT),
            "/mnt",
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
            "TMPDIR",
            str(scratch),
            "--setenv",
            "LANG",
            "C.UTF-8",
            "--chdir",
            "/mnt",
            "--",
        ]

        def run(args):
            return subprocess.run(
                prefix + args, capture_output=True, text=True, timeout=120, check=False
            )

        command = [
            "/usr/bin/python3.12",
            str(HERE.relative_to(ROOT) / "install.py"),
            "--python-executable",
            "/usr/bin/python3.12",
            "--venv",
            str(target),
        ]
        installed = run(command)
        (scratch / "installation.stdout").write_text(installed.stdout)
        (scratch / "installation.stderr").write_text(installed.stderr)
        self.assertEqual(installed.returncode, 0, installed.stderr)
        result = json.loads(installed.stdout.splitlines()[-1])
        self.assertEqual(result["status"], "installed")
        self.assertEqual(
            (result["packet_sha256"], result["payload_sha256"]),
            (PACKET_SHA, PAYLOAD_SHA),
        )
        for cli, commands in {
            "aware-issue-cli": [
                None,
                "ensure-snapshot",
                "resolve-read-projection",
                "start-progress",
                "bind-scope",
                "commit-workspace",
                "close",
            ],
            "aware-protocol": [None, "admit", "setup-specification"],
            "aware-spec": [None, "create-draft", "observe", "iteration-identity"],
        }.items():
            for subcommand in commands:
                activated = run(
                    [
                        str(target / "bin" / cli),
                        *([subcommand] if subcommand else []),
                        "--help",
                    ]
                )
                self.assertEqual(activated.returncode, 0, activated.stderr)
        self.assertFalse((target / "bin/aware").exists())
        metadata = run(
            [
                str(target / "bin/python"),
                "-I",
                "-c",
                "import json,importlib.metadata as m; ds=[d for d in m.distributions() if d.metadata['Name']!='pip']; assert not any(d.read_text('direct_url.json') for d in ds); print(json.dumps({d.metadata['Name']:d.version for d in ds},sort_keys=True))",
            ]
        )
        self.assertEqual(metadata.returncode, 0, metadata.stderr)
        packages = json.loads(metadata.stdout)
        self.assertEqual(len(packages), 31)
        with tarfile.open(
            HERE / "packet/payload/aware-canonical-neutral-fs-internal-v1.tar.gz"
        ) as archive:
            member = next(
                m
                for m in archive.getmembers()
                if m.isfile() and m.name.endswith("/manifest.json")
            )
            manifest = json.loads(archive.extractfile(member).read())
        normalize = lambda name: name.lower().replace("_", "-")
        self.assertEqual(
            {normalize(name): version for name, version in packages.items()},
            {normalize(row["name"]): row["version"] for row in manifest["wheels"]},
        )
        checked = run([str(target / "bin/python"), "-I", "-m", "pip", "check"])
        self.assertEqual(checked.returncode, 0, checked.stderr)
        refused = run(command)
        self.assertEqual(refused.returncode, 2)
        self.assertIn("installation_target_must_be_new", refused.stderr)
        self.assertEqual(scratch.stat().st_mode & 0o777, 0o700)
        (scratch / "installed-receipt.json").write_text(
            json.dumps(
                {
                    "packages": packages,
                    "interfaces": INTERFACES,
                    "packet_sha256": PACKET_SHA,
                    "payload_sha256": PAYLOAD_SHA,
                    "checkout_hidden": True,
                    "network_isolated": True,
                    "environment_cleared": True,
                    "no_editable_or_direct_urls": True,
                    "reuse_refusal": refused.returncode,
                    "parent_mode": "0700",
                    "customer_operations_replayed": False,
                },
                sort_keys=True,
                indent=2,
            )
            + "\n"
        )


if __name__ == "__main__":
    unittest.main()
