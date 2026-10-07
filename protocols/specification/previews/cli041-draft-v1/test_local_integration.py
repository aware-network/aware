"""Maintainer accounting and installer replay; no customer authority or policy."""

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
BASELINE = "4c625d810799f277c6ef165b9d9bed04035af23f"
LAYOUT_SHA = "865b3ac8840bf252b989d399d48472c649a7b264a4a631ea322374214546dcc0"
PACKET_SHA = "b78a45f66ef89ea081d61cd77a37be9d5ccebbfe10b2df60fa577fab53ad0934"
PAYLOAD_SHA = "a5dc83d12a79487dbf345481c82b7c6ba894ead77047b5c4e49557a2f7e2aa30"
ISSUE_PATH = (
    "docs/issues/2026/10/07/fb-2026-10-07-specification-cli041-local-integration-v1.md"
)


def sha(body):
    return hashlib.sha256(body).hexdigest()


class LocalIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.layout = json.loads((HERE / "layout-review.json").read_bytes())
        self.delivery = json.loads((HERE / "delivery.json").read_bytes())

    def test_exact_receipt_and_unselected_state(self):
        self.assertEqual(sha((HERE / "layout-review.json").read_bytes()), LAYOUT_SHA)
        self.assertEqual(self.layout["baseline_revision"], BASELINE)
        self.assertFalse(self.layout["publication_authorized"])
        self.assertFalse(self.layout["public_selection_authorized"])
        self.assertEqual(self.delivery["supported_interfaces"], ["aware-spec"])
        self.assertEqual(self.delivery["preserved_agent_contract"], "1.2.1")

    def test_453_reviewed_postimages(self):
        self.assertEqual(len(self.layout["changed_files"]), 453)
        self.assertEqual(
            sum(
                r["before_sha256"] is None
                for r in self.layout["changed_files"].values()
            ),
            451,
        )
        for name, record in self.layout["changed_files"].items():
            with self.subTest(name=name):
                path = ROOT / name
                self.assertFalse(path.is_symlink())
                self.assertEqual(sha(path.read_bytes()), record["sha256"])
                self.assertEqual(path.stat().st_size, record["bytes"])

    def test_baseline_preimages_bytes_and_git_modes(self):
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
                    record = self.layout["changed_files"][member.name]
                    self.assertEqual(sha(body), record["before_sha256"])
                else:
                    self.assertEqual(path.read_bytes(), body, member.name)
                    kept += 1
        self.assertEqual((total, kept), (1918, 1916))
        existing = {
            n
            for n, r in self.layout["changed_files"].items()
            if r["before_sha256"] is not None
        }
        self.assertEqual(existing, {"README.md", "workspaces/README.md"})

    def test_exact_457_path_integration_scope(self):
        extra = {
            str((HERE / n).relative_to(ROOT))
            for n in (
                "layout-review.json",
                "LOCAL-INTEGRATION.md",
                "test_local_integration.py",
            )
        } | {ISSUE_PATH}
        expected = set(self.layout["changed_files"]) | extra
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
        self.assertEqual(len(expected), 457)

    def test_packet_mapping_and_neutral_snapshot(self):
        mapping = self.delivery["packet_member_map"]
        self.assertEqual(len(mapping), 446)
        sources = []
        for original, record in mapping.items():
            path = ROOT / record["path"]
            self.assertFalse(path.is_symlink())
            self.assertEqual(
                (sha(path.read_bytes()), path.stat().st_size),
                (record["sha256"], record["bytes"]),
            )
            if original.startswith("source/workspaces/"):
                sources.append(record["path"])
        self.assertEqual(len(sources), 146)
        self.assertTrue(
            all(
                n.startswith("workspaces/previews/specification-cli041-draft-v1/")
                for n in sources
            )
        )
        self.assertFalse(
            any(
                part in n
                for n in sources
                for part in ("/services/", "/ontology/", "/experience/")
            )
        )

    def test_exact_archives_installer_and_verifier(self):
        for name, digest in {
            "distribution/aware-specification-cli041-source-notice-review-v1.tar.gz": PACKET_SHA,
            "packet/payload/specification-cli041-completion-v1.tar.gz": PAYLOAD_SHA,
            "install.py": "03f7fed6f410cc803ce6b0b95bc59371cc4499531f5f5d09df2fdd6faf68909b",
        }.items():
            self.assertEqual(sha((HERE / name).read_bytes()), digest)
        self.assertEqual(
            sha((ROOT / "protocols/install.py").read_bytes()),
            "032febe109cf145c65f5edaf14403fc58e7b4e93397535d0327e5ce1a65c6ca9",
        )

    def test_notice_account_and_selected_predecessor(self):
        notices = json.loads((HERE / "packet/NOTICE-BINDINGS.json").read_bytes())
        self.assertEqual(len(notices["wheel_legal_copies"]), 43)
        self.assertEqual(len(notices["inherited_notices"]), 236)
        self.assertEqual(self.delivery["preserved_selected_specification_cli"], "0.2.2")
        self.assertEqual(self.delivery["proposed_specification_cli"], "0.4.1")
        current = (ROOT / "protocols/specification/README.md").read_text()
        self.assertIn("**aware-protocol 0.3.1 / aware-spec 0.2.2**", current)
        self.assertIn("previews/cli022-reader-v1/README.md", current)
        agent = json.loads((ROOT / "protocols/agent/release.json").read_bytes())
        self.assertEqual(agent["version"], "0.1.0a6")
        self.assertEqual(agent["agent_contract"]["version"], "1.2.1")

    def test_links_and_draft_boundaries(self):
        for path in (
            HERE / "README.md",
            HERE / "LOCAL-INTEGRATION.md",
            ROOT / "workspaces/previews/specification-cli041-draft-v1/README.md",
        ):
            for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if not link.startswith(("https:", "http:", "#")):
                    self.assertTrue((path.parent / link).is_file(), (str(path), link))
        text = (HERE / "README.md").read_text()
        for phrase in (
            "not published or selected",
            "Never overlay",
            "Only\naware-spec",
            "consumer_completion_verified=true",
            "known published",
            "every-write",
            "Contract1.3.0 remains unallocated",
            "unassisted",
        ):
            self.assertIn(phrase, text)

    def test_actual_integrated_offline_installer(self):
        scratch = Path(os.environ["AWARE_CLI041_INTEGRATION_REPLAY_ROOT"])
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

        args = [
            "/usr/bin/python3.12",
            str(HERE.relative_to(ROOT) / "install.py"),
            "--python-executable",
            "/usr/bin/python3.12",
            "--venv",
            str(target),
        ]
        installed = run(args)
        (scratch / "installation.stdout").write_text(installed.stdout)
        (scratch / "installation.stderr").write_text(installed.stderr)
        self.assertEqual(installed.returncode, 0, installed.stderr)
        receipt = json.loads(installed.stdout.splitlines()[-1])
        self.assertEqual(receipt["status"], "installed")
        self.assertEqual(
            (receipt["packet_sha256"], receipt["payload_sha256"]),
            (PACKET_SHA, PAYLOAD_SHA),
        )
        for command in (
            ["--help"],
            ["create-draft", "--help"],
            ["observe", "--help"],
            ["iteration-identity", "--help"],
        ):
            result = run([str(target / "bin/aware-spec"), *command])
            self.assertEqual(result.returncode, 0, result.stderr)
        for name in ("aware", "aware-protocol"):
            self.assertFalse((target / "bin" / name).exists())
        audit = run(
            [
                str(target / "bin/python"),
                "-I",
                "-c",
                "import importlib.metadata as m,json; ds=[d for d in m.distributions() if d.metadata['Name']!='pip']; print(json.dumps({'packages':{d.metadata['Name']:d.version for d in ds},'direct_urls':[d.metadata['Name'] for d in ds if d.read_text('direct_url.json')]}))",
            ]
        )
        self.assertEqual(audit.returncode, 0, audit.stderr)
        value = json.loads(audit.stdout)
        self.assertEqual(len(value["packages"]), 26)
        self.assertEqual(value["direct_urls"], [])
        for name, version in {
            "aware-specification-cli": "0.4.1",
            "aware-specification-sdk": "0.3.1",
            "aware-specification-fs-sdk-adapter": "0.4.1",
            "aware-protocol-fs-adapter": "0.6.1",
        }.items():
            self.assertEqual(value["packages"][name], version)
        check = run([str(target / "bin/python"), "-I", "-m", "pip", "check"])
        self.assertEqual(check.returncode, 0, check.stderr)
        refused = run(args)
        self.assertEqual(refused.returncode, 2)
        self.assertIn("installation_target_must_be_new", refused.stderr)
        self.assertEqual(scratch.stat().st_mode & 0o777, 0o700)
        (scratch / "installed-receipt.json").write_text(
            json.dumps(
                {
                    "installation": receipt,
                    "audit": value,
                    "dependency_check": check.returncode,
                    "reuse_refusal": refused.returncode,
                    "parent_mode": "0700",
                },
                sort_keys=True,
            )
            + "\n"
        )


if __name__ == "__main__":
    unittest.main()
