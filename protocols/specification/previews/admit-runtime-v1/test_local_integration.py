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
BASELINE = "0b8710e7c0afb71df8f73685fc22f0632f74d722"
LAYOUT_SHA = "0d84be1c9eca5cc7d9f4104d24ba4810f48668b8dac0ffa32965c07a5cee2b3a"
PACKET_SHA = "e5d7bf16e7bf4d5cfd91faa3c85c9697feac4a5d9c709c84ea9ef71948dc387f"
PAYLOAD_SHA = "3fc5c8e5d48e8bc843b6721ac3a57be20da32e488d8b39b8f7d7b618cd5d777e"


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

    def test_all_446_reviewed_paths_are_exact(self):
        changes = self.layout["changed_files"]
        self.assertEqual(len(changes), 446)
        self.assertEqual(sum(r["before_sha256"] is None for r in changes.values()), 444)
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

    def test_998_untouched_baseline_files_and_git_modes(self):
        entries = subprocess.check_output(
            ["git", "-C", str(ROOT), "ls-tree", "-r", BASELINE], text=True
        ).splitlines()
        kept = 0
        for entry in entries:
            attributes, name = entry.split("\t", 1)
            if name in self.layout["changed_files"]:
                continue
            mode, kind, blob = attributes.split()
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
        self.assertEqual(kept, 998)

    def test_all_439_packet_members_and_source_snapshot(self):
        mapping = self.delivery["packet_member_map"]
        self.assertEqual(len(mapping), 439)
        sources = []
        for original, record in mapping.items():
            path = ROOT / record["path"]
            self.assertFalse(path.is_symlink())
            self.assertEqual(sha(path.read_bytes()), record["sha256"], original)
            self.assertEqual(path.stat().st_size, record["bytes"], original)
            if original.startswith("source/workspaces/"):
                sources.append(record["path"])
        self.assertEqual(len(sources), 145)
        self.assertTrue(
            all(
                p.startswith("workspaces/previews/specification-admit-runtime-v1/")
                for p in sources
            )
        )
        self.assertFalse(any("/ontology/" in p or "/services/" in p for p in sources))

    def test_exact_archives_installer_and_existing_verifier(self):
        self.assertEqual(
            sha(
                (
                    HERE
                    / "distribution/aware-protocol-admit-source-notice-review-v1.tar.gz"
                ).read_bytes()
            ),
            PACKET_SHA,
        )
        self.assertEqual(
            sha(
                (HERE / "packet/payload/protocol-admit-runtime-v1.tar.gz").read_bytes()
            ),
            PAYLOAD_SHA,
        )
        self.assertEqual(
            sha((HERE / "install.py").read_bytes()),
            "6e7aa02f0108d80cca7fdead77ed498bf7337fc0baccaccce3a73ddc29ab9f86",
        )
        self.assertEqual(
            sha((ROOT / "protocols/install.py").read_bytes()),
            "032febe109cf145c65f5edaf14403fc58e7b4e93397535d0327e5ce1a65c6ca9",
        )

    def test_notice_counts_and_predecessor_selection(self):
        notices = json.loads((HERE / "packet/NOTICE-BINDINGS.json").read_bytes())
        self.assertEqual(len(notices["wheel_legal_copies"]), 45)
        self.assertEqual(len(notices["inherited_notices"]), 236)
        self.assertEqual(self.delivery["preserved_selected_protocol_cli"], "0.3.0")
        self.assertEqual(self.delivery["proposed_protocol_cli"], "0.3.1")
        selection = (ROOT / "protocols/specification/LOCAL-SELECTION.md").read_text()
        self.assertIn("| Protocol CLI | `aware-protocol` 0.3.0 |", selection)
        self.assertIn("1.3.0 remains unallocated", selection)

    def test_links_and_unselected_presentation(self):
        names = [
            HERE / "README.md",
            HERE / "LOCAL-INTEGRATION.md",
            ROOT / "workspaces/previews/specification-admit-runtime-v1/README.md",
        ]
        for path in names:
            for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if not link.startswith(("https:", "http:", "#")):
                    self.assertTrue((path.parent / link).is_file(), (str(path), link))
        text = (HERE / "README.md").read_text()
        for required in (
            "not published or selected",
            "Never overlay",
            "unfrozen",
            "authoring/import",
            "every-write",
            "1.3.0 remains unallocated",
        ):
            self.assertIn(required, text)
        self.assertIn(
            "Prepared admit-runtime successor", (ROOT / "README.md").read_text()
        )

    def test_actual_integrated_offline_installer(self):
        scratch = Path(os.environ["AWARE_ADMIT_INTEGRATION_REPLAY_ROOT"])
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
            "protocols/specification/previews/admit-runtime-v1/install.py",
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
        self.assertEqual(value["packages"]["aware-specification-cli"], "0.2.0")
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
