"""Maintainer byte/layout and installed activation checks, not customer workflow."""

import ast
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
BASELINE = "0e1af47a417df143681125e467930aedf4157cd2"
LAYOUT_SHA = "4a9688c47105934c72783cea59574f2a78975b030581c15b9c19f9f7b47f5c8c"
PACKET_SHA = "49fd470e4aadf564ec40131f1bffbe95d0f8d65cf0946e60db07dfd88c09531d"
PAYLOAD_SHA = "db23274dcc05c3923c9f7ba33f6bf0d1cbda3717aa120d44ee74ef4d35297b11"
ISSUE_PATH = (
    "docs/issues/2026/10/09/fb-2026-10-09-canonical-agent-local-integration-v0.md"
)


def sha(body):
    return hashlib.sha256(body).hexdigest()


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.layout = json.loads((HERE / "layout-review.json").read_bytes())
        self.delivery = json.loads((HERE / "delivery.json").read_bytes())

    def test_accepted_receipt_and_original_selection_owner(self):
        self.assertEqual(sha((HERE / "layout-review.json").read_bytes()), LAYOUT_SHA)
        self.assertEqual(self.layout["baseline_revision"], BASELINE)
        self.assertFalse(self.layout["publication_authorized"])
        self.assertFalse(self.layout["public_selection_authorized"])
        self.assertEqual(self.delivery["supported_interfaces"], ["aware"])
        self.assertEqual(
            (self.delivery["packages"], self.delivery["aware_packages"]), (32, 19)
        )
        self.assertEqual(
            self.delivery["selection_owner"],
            "Workspace portable_protocols; no layout selection",
        )

    def test_all_reviewed_postimages(self):
        self.assertEqual(len(self.layout["changed_files"]), 881)
        self.assertEqual(
            sum(
                row["before_sha256"] is None
                for row in self.layout["changed_files"].values()
            ),
            879,
        )
        for name, row in self.layout["changed_files"].items():
            with self.subTest(name=name):
                path = ROOT / name
                self.assertFalse(path.is_symlink())
                self.assertEqual(
                    (sha(path.read_bytes()), path.stat().st_size),
                    (row["sha256"], row["bytes"]),
                )

    def test_all_baseline_bytes_and_git_modes(self):
        raw = subprocess.check_output(["git", "-C", str(ROOT), "archive", BASELINE])
        kept = total = 0
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            for member in archive.getmembers():
                if not member.isfile():
                    continue
                total += 1
                path = ROOT / member.name
                self.assertFalse(path.is_symlink())
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
        self.assertEqual((total, kept), (3250, 3248))
        self.assertEqual(
            {
                n
                for n, row in self.layout["changed_files"].items()
                if row["before_sha256"] is not None
            },
            {"README.md", "workspaces/README.md"},
        )

    def test_exact_local_integration_scope(self):
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
        self.assertEqual(len(expected), 885)

    def test_packet_source_legal_and_notice_mapping(self):
        self.assertEqual(len(self.delivery["packet_member_map"]), 871)
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
        self.assertEqual(len(sources), 549)
        self.assertTrue(
            all(
                p.startswith("workspaces/previews/canonical-agent-fs-v1/")
                for p in sources
            )
        )
        notices = json.loads((HERE / "packet/NOTICE-BINDINGS.json").read_bytes())
        self.assertEqual(notices["candidate_archive_sha256"], PAYLOAD_SHA)
        self.assertEqual(len(notices["wheel_legal_copies"]), 51)
        self.assertEqual(len(notices["inherited_notice_inputs"]), 236)
        self.assertEqual(len(notices["new_notice_inputs"]), 23)
        self.assertEqual(
            sha(
                (
                    HERE / "distribution/canonical-agent-source-notice-review-v1.tar.gz"
                ).read_bytes()
            ),
            PACKET_SHA,
        )
        self.assertEqual(
            sha(
                (
                    HERE
                    / "packet/payload/aware-canonical-neutral-fs-internal-v1.tar.gz"
                ).read_bytes()
            ),
            PAYLOAD_SHA,
        )

    def test_existing_selections_and_bootstrap(self):
        agent = json.loads((ROOT / "protocols/agent/release.json").read_bytes())
        self.assertEqual(agent["version"], "0.1.0a6")
        self.assertEqual(agent["agent_contract"]["version"], "1.2.1")
        self.assertIn("unselected", (HERE / "README.md").read_text())
        # The full baseline test binds every predecessor selection/installer and
        # root bootstrap byte. This new preview is not selected by those files.
        self.assertNotIn("canonical-agent-fs-v1", (ROOT / "AGENTS.md").read_text())
        for phrase in (
            "No `aware init`",
            "automatic guard discovery",
            "prepared inputs",
            "Instructions remain draft",
            "not distribution packages",
        ):
            self.assertIn(phrase, (HERE / "README.md").read_text())

    def test_local_markdown_links(self):
        for path in (
            HERE / "README.md",
            HERE / "WORKFLOW.md",
            HERE / "LOCAL-INTEGRATION.md",
            ROOT / "workspaces/previews/canonical-agent-fs-v1/README.md",
        ):
            for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if not link.startswith(("https:", "http:", "#")):
                    self.assertTrue((path.parent / link).is_file(), (str(path), link))

    def test_retained_installer_policy(self):
        original = ast.parse(
            (
                ROOT / "protocols/specification/previews/admit-runtime-v1/install.py"
            ).read_bytes()
        )
        current = ast.parse((HERE / "install.py").read_bytes())

        class Coordinate(ast.NodeTransformer):
            def visit_Constant(self, node):
                if (
                    node.value
                    == "payload/aware-canonical-neutral-fs-internal-v1.tar.gz"
                ):
                    node.value = "payload/protocol-admit-runtime-v1.tar.gz"
                return node

        for name in ("new_target", "load_verifier", "clean_environment", "main"):
            before = next(
                n
                for n in original.body
                if isinstance(n, ast.FunctionDef) and n.name == name
            )
            after = next(
                n
                for n in current.body
                if isinstance(n, ast.FunctionDef) and n.name == name
            )
            self.assertEqual(ast.dump(before), ast.dump(Coordinate().visit(after)))

    def test_fresh_offline_integrated_installation(self):
        scratch = Path(os.environ["AWARE_AGENT_INTEGRATION_REPLAY_ROOT"])
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

        def successful(args):
            result = run(args)
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout

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
        self.assertEqual(
            (result["packet_sha256"], result["payload_sha256"]),
            (PACKET_SHA, PAYLOAD_SHA),
        )
        successful([str(target / "bin/aware"), "--help"])
        parity = 0
        for family, cli, leaves in (
            (
                "issue",
                "aware-issue-cli",
                (
                    "ensure-snapshot",
                    "resolve-read-projection",
                    "start-progress",
                    "bind-scope",
                    "commit-workspace",
                    "close",
                ),
            ),
            ("protocol", "aware-protocol", ("admit", "setup-specification")),
            ("spec", "aware-spec", ("create-draft", "observe", "iteration-identity")),
        ):
            successful([str(target / "bin/aware"), family, "--help"])
            for leaf in leaves:
                mounted = successful(
                    [str(target / "bin/aware"), family, leaf, "--help"]
                )
                original = successful(
                    [str(target / "bin" / cli), leaf, "--help"]
                ).replace(cli, "aware " + family)
                self.assertEqual(
                    mounted.split("\n\n", 1)[0].split(),
                    original.split("\n\n", 1)[0].split(),
                )
                self.assertEqual(
                    mounted.split("options:", 1)[1].split(),
                    original.split("options:", 1)[1].split(),
                )
                parity += 1
        packages = json.loads(
            successful(
                [
                    str(target / "bin/python"),
                    "-I",
                    "-c",
                    "import json,importlib.metadata as m; ds=[d for d in m.distributions() if d.metadata['Name']!='pip']; assert not any(d.read_text('direct_url.json') for d in ds); print(json.dumps({d.metadata['Name']:d.version for d in ds},sort_keys=True))",
                ]
            )
        )
        self.assertEqual(len(packages), 32)
        with tarfile.open(
            HERE / "packet/payload/aware-canonical-neutral-fs-internal-v1.tar.gz"
        ) as archive:
            member = next(
                m
                for m in archive.getmembers()
                if m.isfile() and m.name.endswith("/manifest.json")
            )
            manifest = json.loads(archive.extractfile(member).read())

        def normalized(name):
            return name.lower().replace("_", "-")

        self.assertEqual(
            {normalized(n): v for n, v in packages.items()},
            {normalized(r["name"]): r["version"] for r in manifest["wheels"]},
        )
        successful([str(target / "bin/python"), "-I", "-m", "pip", "check"])
        reused = run(command)
        self.assertEqual(reused.returncode, 2)
        self.assertIn("installation_target_must_be_new", reused.stderr)
        self.assertEqual(scratch.stat().st_mode & 0o777, 0o700)
        (scratch / "installed-receipt.json").write_text(
            json.dumps(
                {
                    "packages": packages,
                    "interfaces": ["aware"],
                    "original_leaf_usage_option_parity": parity,
                    "packet_sha256": PACKET_SHA,
                    "payload_sha256": PAYLOAD_SHA,
                    "checkout_hidden": True,
                    "network_disabled": True,
                    "environment_cleared": True,
                    "no_editable_or_direct_urls": True,
                    "reuse_refusal": reused.returncode,
                    "parent_mode": "0700",
                    "customer_domain_operations_replayed": False,
                },
                sort_keys=True,
                indent=2,
            )
            + "\n"
        )


if __name__ == "__main__":
    unittest.main()
