"""Maintainer byte accounting and real installer replay; no domain policy logic."""

import hashlib
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASELINE = "763f5fea33964f115445e7191d726d7e10d6305c"
LAYOUT_SHA = "d9c176996bcc615730af2b1d1efc18897f82691db4d4692c3e988b31b47689c4"
PACKET_SHA = "578b25b0d68bed3546ac54fbfeb426062415e6b519df0a7829172e33a8340c2e"
PAYLOAD_SHA = "52d2d443ea8d7b2a5cf4533d78460f1f3c9c62a6bd65ee9a853e15bb07e694d0"


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
        self.assertEqual(self.delivery["preserved_agent_contract"], "1.2.1")

    def test_all_456_reviewed_paths_are_exact(self):
        changes = self.layout["changed_files"]
        self.assertEqual(len(changes), 456)
        self.assertEqual(sum(r["before_sha256"] is None for r in changes.values()), 454)
        for name, record in changes.items():
            with self.subTest(name=name):
                path = ROOT / name
                self.assertFalse(path.is_symlink())
                self.assertEqual(sha(path.read_bytes()), record["sha256"])
                self.assertEqual(path.stat().st_size, record["bytes"])

    def test_two_readme_preimages_and_postimages(self):
        existing = {
            name: r
            for name, r in self.layout["changed_files"].items()
            if r["before_sha256"] is not None
        }
        self.assertEqual(set(existing), {"README.md", "workspaces/README.md"})
        for name, record in existing.items():
            body = subprocess.check_output(
                ["git", "-C", str(ROOT), "show", BASELINE + ":" + name]
            )
            self.assertEqual(sha(body), record["before_sha256"])
            self.assertEqual(sha((ROOT / name).read_bytes()), record["sha256"])

    def test_1452_untouched_baseline_files_and_git_modes(self):
        entries = subprocess.check_output(
            ["git", "-C", str(ROOT), "ls-tree", "-r", BASELINE], text=True
        ).splitlines()
        kept = 0
        for entry in entries:
            attributes, name = entry.split("\t", 1)
            mode, kind, blob = attributes.split()
            self.assertEqual(
                bool((ROOT / name).stat().st_mode & 0o111), mode == "100755", name
            )
            if name in self.layout["changed_files"]:
                continue
            self.assertEqual(kind, "blob")
            path = ROOT / name
            self.assertFalse(path.is_symlink())
            body = subprocess.check_output(
                ["git", "-C", str(ROOT), "cat-file", "blob", blob]
            )
            self.assertEqual(path.read_bytes(), body, name)
            # Git retains executable state, not complete local POSIX permissions.
            self.assertEqual(bool(path.stat().st_mode & 0o111), mode == "100755", name)
            kept += 1
        self.assertEqual(kept, 1452)

    def test_all_449_packet_members_and_source_snapshot(self):
        mapping = self.delivery["packet_member_map"]
        self.assertEqual(len(mapping), 449)
        sources = []
        for original, record in mapping.items():
            path = ROOT / record["path"]
            self.assertFalse(path.is_symlink())
            self.assertEqual(sha(path.read_bytes()), record["sha256"], original)
            self.assertEqual(path.stat().st_size, record["bytes"], original)
            if original.startswith("source/workspaces/"):
                sources.append(record["path"])
        self.assertEqual(len(sources), 151)
        self.assertTrue(
            all(
                p.startswith("workspaces/previews/specification-cli022-reader-v1/")
                for p in sources
            )
        )
        self.assertFalse(any("/ontology/" in p or "/services/" in p for p in sources))

    def test_exact_archives_installer_and_existing_verifier(self):
        self.assertEqual(
            sha(
                (
                    HERE
                    / "distribution/aware-specification-cli022-source-notice-review-v1.tar.gz"
                ).read_bytes()
            ),
            PACKET_SHA,
        )
        self.assertEqual(
            sha(
                (
                    HERE / "packet/payload/specification-cli022-reader-v1.tar.gz"
                ).read_bytes()
            ),
            PAYLOAD_SHA,
        )
        self.assertEqual(
            sha((HERE / "install.py").read_bytes()),
            "645bd18c1301c9c5856b227c6c2bacd7624dc9d2475a296e83b0dfa5fe32ea68",
        )
        self.assertEqual(
            sha((ROOT / "protocols/install.py").read_bytes()),
            "032febe109cf145c65f5edaf14403fc58e7b4e93397535d0327e5ce1a65c6ca9",
        )

    def test_notice_counts_and_predecessor_selection(self):
        notices = json.loads((HERE / "packet/NOTICE-BINDINGS.json").read_bytes())
        self.assertEqual(len(notices["wheel_legal_copies"]), 45)
        self.assertEqual(len(notices["inherited_notices"]), 236)
        self.assertEqual(self.delivery["preserved_selected_protocol_cli"], "0.3.1")
        self.assertEqual(self.delivery["proposed_protocol_cli"], "0.3.1")
        selection = (ROOT / "protocols/specification/LOCAL-SELECTION.md").read_text()
        # This table is the preserved historical 0.3.0 selection. The current
        # standalone entrance is recorded in the unchanged SPEC README.
        self.assertIn("| Protocol CLI | `aware-protocol` 0.3.0 |", selection)
        self.assertIn("1.3.0 remains unallocated", selection)
        current = (ROOT / "protocols/specification/README.md").read_text()
        self.assertIn("**aware-protocol 0.3.1 / aware-spec 0.2.0**", current)
        self.assertIn("previews/admit-runtime-v1/README.md", current)

    def test_links_and_unselected_presentation(self):
        names = [
            HERE / "README.md",
            HERE / "LOCAL-INTEGRATION.md",
            ROOT / "workspaces/previews/specification-cli022-reader-v1/README.md",
        ]
        for path in names:
            for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if not link.startswith(("https:", "http:", "#")):
                    self.assertTrue((path.parent / link).is_file(), (str(path), link))
        text = (HERE / "README.md").read_text()
        for required in (
            "not published or selected",
            "Never overlay",
            "unallocated",
            "authoring/import",
            "every-write",
            "1.3.0 remains unallocated",
        ):
            self.assertIn(required, text)
        self.assertIn(
            "Prepared SPEC reader successor", (ROOT / "README.md").read_text()
        )

    def test_exact_delta_and_no_extra_integrated_paths(self):
        expected = (
            set(self.layout["changed_files"])
            | {
                str((HERE / name).relative_to(ROOT))
                for name in (
                    "layout-review.json",
                    "LOCAL-INTEGRATION.md",
                    "test_local_integration.py",
                )
            }
            | {
                "docs/issues/2026/10/06/fb-2026-10-06-specification-cli022-local-integration-v1.md"
            }
        )
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
        self.assertEqual(len(expected), 460)

    def test_actual_integrated_offline_installer(self):
        scratch = Path(os.environ["AWARE_CLI022_INTEGRATION_REPLAY_ROOT"])
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
            "--chdir",
            "/mnt",
            "/usr/bin/env",
            "-i",
            "PATH=/usr/bin:/bin",
            f"HOME={scratch}",
            f"TMPDIR={scratch}",
            "LANG=C.UTF-8",
        ]
        arguments = [
            "/usr/bin/python3.12",
            "protocols/specification/previews/cli022-reader-v1/install.py",
            "--python-executable",
            "/usr/bin/python3.12",
            "--venv",
            str(target),
        ]
        result = subprocess.run(
            prefix + arguments, capture_output=True, text=True, check=False
        )
        (scratch / "installation.stdout").write_text(result.stdout)
        (scratch / "installation.stderr").write_text(result.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout.splitlines()[-1])
        self.assertEqual(receipt["status"], "installed")
        self.assertEqual(receipt["packet_sha256"], PACKET_SHA)
        self.assertEqual(receipt["payload_sha256"], PAYLOAD_SHA)
        for name in ("aware-protocol", "aware-spec"):
            r = subprocess.run(
                prefix + [str(target / "bin" / name), "--help"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
        audit_code = "import importlib.metadata as m,json; ds=[d for d in m.distributions() if d.metadata['Name']!='pip']; print(json.dumps({'packages':{d.metadata['Name']:d.version for d in ds},'direct_urls':[d.metadata['Name'] for d in ds if d.read_text('direct_url.json')]}))"
        audit = subprocess.run(
            prefix + [str(target / "bin/python"), "-I", "-c", audit_code],
            capture_output=True,
            text=True,
            check=True,
        )
        value = json.loads(audit.stdout)
        self.assertEqual(len(value["packages"]), 27)
        self.assertEqual(value["packages"]["aware-protocol-cli"], "0.3.1")
        self.assertEqual(value["packages"]["aware-specification-cli"], "0.2.2")
        self.assertEqual(value["packages"]["aware-command-runtime"], "0.1.1")
        self.assertEqual(value["direct_urls"], [])
        check = subprocess.run(
            prefix + [str(target / "bin/python"), "-I", "-m", "pip", "check"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(check.returncode, 0, check.stderr)
        refused = subprocess.run(
            prefix + arguments, capture_output=True, text=True, check=False
        )
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
                },
                sort_keys=True,
            )
            + "\n"
        )


if __name__ == "__main__":
    unittest.main()
