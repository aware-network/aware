"""Maintainer byte accounting of local integration; no domain enforcement logic."""

import hashlib
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASELINE = "8a7c1658df9937959e92f6c8096d6b1dadbba121"
PACKET_SHA = "865c57be501818dc380c9019a0fc710658d67242375a080b563258d6365a97a0"
PAYLOAD_SHA = "955e423c82e431f9565e1b2351a6686855246b585d9890281bc73e8401d52eac"
SNAPSHOT = "workspaces/previews/specification-setup-read-v1"


def sha(body):
    return hashlib.sha256(body).hexdigest()


class DeliveryIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.value = json.loads((HERE / "delivery.json").read_bytes())

    def test_exact_packet_and_payload(self):
        self.assertEqual(
            sha(
                (
                    HERE / "distribution/aware-specification-fs-review-packet-v1.tar.gz"
                ).read_bytes()
            ),
            PACKET_SHA,
        )
        self.assertEqual(
            sha(
                (
                    HERE / "packet/payload/specification-setup-read-v3.tar.gz"
                ).read_bytes()
            ),
            PAYLOAD_SHA,
        )
        self.assertEqual(self.value["packet_sha256"], PACKET_SHA)

    def test_all_429_packet_members_preserved(self):
        mapping = self.value["packet_member_map"]
        self.assertEqual(len(mapping), 429)
        for original, record in mapping.items():
            with self.subTest(original=original):
                path = ROOT / record["path"]
                self.assertFalse(path.is_symlink())
                body = path.read_bytes()
                self.assertEqual(sha(body), record["sha256"])
                self.assertEqual(len(body), record["bytes"])

    def test_neutral_source_is_a_separate_exact_snapshot(self):
        rows = [
            item
            for name, item in self.value["packet_member_map"].items()
            if name.startswith("source/workspaces/")
        ]
        self.assertEqual(len(rows), 137)
        self.assertTrue(all(item["path"].startswith(SNAPSHOT + "/") for item in rows))
        self.assertFalse(
            any(
                "/ontology/" in item["path"] or "/services/" in item["path"]
                for item in rows
            )
        )

    def test_all_notice_bindings_preserved(self):
        notices = json.loads((HERE / "packet/NOTICE-BINDINGS.json").read_bytes())
        self.assertEqual(len(notices["wheel_legal_copies"]), 43)
        self.assertEqual(len(notices["inherited_notices"]), 236)

    def test_retained_installer_and_verifier_bytes(self):
        self.assertEqual(
            sha((HERE / "install.py").read_bytes()),
            "9dd4ec867e9521fd19b22a5ef126fb464754c6e1ae9763554589c22963a729b1",
        )
        self.assertEqual(
            sha((ROOT / "protocols/install.py").read_bytes()),
            "032febe109cf145c65f5edaf14403fc58e7b4e93397535d0327e5ce1a65c6ca9",
        )

    def test_all_559_untouched_baseline_files_preserved(self):
        paths = subprocess.check_output(
            ["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", BASELINE],
            text=True,
        ).splitlines()
        unchanged = [
            path for path in paths if path not in {"README.md", "workspaces/README.md"}
        ]
        self.assertEqual(len(unchanged), 559)
        for name in unchanged:
            original = subprocess.check_output(
                ["git", "-C", str(ROOT), "show", BASELINE + ":" + name]
            )
            self.assertEqual((ROOT / name).read_bytes(), original, name)

    def test_two_reviewed_readme_updates_are_exact(self):
        self.assertEqual(
            sha((ROOT / "README.md").read_bytes()),
            "37024352b0ed6136ec170c2e1bce18fe67a1ecf8845be906a58164d08d09270a",
        )
        self.assertEqual(
            sha((ROOT / "workspaces/README.md").read_bytes()),
            "b69cdb806a550d56ece19450d0607a9a10116916ef3217ccff67a2936c90d773",
        )

    def test_local_links_and_selection_do_not_claim_publication(self):
        for name in (
            "README.md",
            "LOCAL-SELECTION.md",
            "packet/README.md",
            "packet/instructions/specification-consumer-bootstrap-addendum-v1.md",
            "packet/instructions/specification-setup-customer-sequence-v1.md",
        ):
            path = HERE / name
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if not target.startswith(("http:", "https:", "#")):
                    self.assertTrue((path.parent / target).is_file(), (name, target))
        selection = (HERE / "LOCAL-SELECTION.md").read_text()
        for required in (
            "not publicly",
            "1.3.0 remains unallocated",
            "remain **drafts**",
            "explicit publication authorization",
        ):
            self.assertIn(required, selection)
        self.assertEqual(self.value["preserved_agent_contract"], "1.2.1")

    def test_actual_integrated_installer_offline(self):
        # Explicit maintainer replay target, retained for independent inspection.
        scratch = Path(os.environ["AWARE_SPEC_INSTALL_REPLAY_ROOT"])
        self.assertTrue(scratch.is_dir())
        self.assertEqual(scratch.stat().st_mode & 0o777, 0o700)
        target = scratch / "env"
        self.assertFalse(target.exists())
        prefix = [
            "/usr/bin/bwrap",
            "--die-with-parent",
            "--unshare-net",
            "--ro-bind",
            "/",
            "/",
            "--dev",
            "/dev",
            "--ro-bind",
            str(ROOT),
            "/mnt",
            "--tmpfs",
            os.environ["AWARE_SPEC_PRODUCER_ROOT"],
            "--tmpfs",
            os.environ["AWARE_SPEC_PUBLIC_PRODUCER_PARENT"],
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
            "protocols/specification/install.py",
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
            activated = subprocess.run(
                prefix + [str(target / "bin" / name), "--help"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(activated.returncode, 0, activated.stderr)
        audit = subprocess.run(
            prefix
            + [
                str(target / "bin/python"),
                "-I",
                "-c",
                "import importlib.metadata as m,json; ds=[d for d in m.distributions() if d.metadata['Name']!='pip']; print(json.dumps({'packages':{d.metadata['Name']:d.version for d in ds},'direct_urls':[d.metadata['Name'] for d in ds if d.read_text('direct_url.json')]}))",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        audited = json.loads(audit.stdout)
        self.assertEqual(len(audited["packages"]), 26)
        self.assertEqual(audited["direct_urls"], [])
        rejected = subprocess.run(
            prefix + arguments, capture_output=True, text=True, check=False
        )
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("installation_target_must_be_new", rejected.stderr)
        self.assertEqual(scratch.stat().st_mode & 0o777, 0o700)
        (scratch / "installed-receipt.json").write_text(
            json.dumps(
                {
                    "installation": receipt,
                    "audit": audited,
                    "interfaces": ["aware-protocol", "aware-spec"],
                    "existing_environment_refusal": rejected.returncode,
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    unittest.main()
