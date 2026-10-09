"""Local selection accounting; reuse the accepted real installer, not domain policy."""

import hashlib
import importlib.util
import io
import json
import re
import subprocess
import tarfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASELINE = "ec85eccb2a6dce3ff0f611fa7d71337a11a69070"
CHANGED = {
    "README.md",
    "workspaces/README.md",
    "protocols/collaboration/previews/canonical-agent-fs-v1/README.md",
    "workspaces/previews/canonical-agent-fs-v1/README.md",
}
NEW = {
    "protocols/collaboration/previews/canonical-agent-fs-v1/SELECTION.md",
    "protocols/collaboration/previews/canonical-agent-fs-v1/test_selection.py",
    "docs/issues/2026/10/09/fb-2026-10-09-canonical-agent-local-selection-v0.md",
}
REPLAY_SHA = "def144031439726f402903a935d6af76cea751b528605f0b966af8eb40c9232e"
INSTALLER_SHA = "3a9fd6356bcbd33439aeb2ef303da81ba3bc38e96898b4d486a85a501f348a66"
DELIVERY_SHA = "1f6512d61dfd28b8661ae90325f2db90590600ee0f2e3c6bbd3b0a2011dd7c7f"
ENVELOPE_SHA = "49fd470e4aadf564ec40131f1bffbe95d0f8d65cf0946e60db07dfd88c09531d"
PAYLOAD_SHA = "db23274dcc05c3923c9f7ba33f6bf0d1cbda3717aa120d44ee74ef4d35297b11"


def sha(body):
    return hashlib.sha256(body).hexdigest()


class SelectionTests(unittest.TestCase):
    def test_baseline_bytes_and_git_modes(self):
        raw = subprocess.check_output(["git", "-C", str(ROOT), "archive", BASELINE])
        names = set()
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            for member in archive.getmembers():
                if not member.isfile():
                    continue
                names.add(member.name)
                path = ROOT / member.name
                self.assertFalse(path.is_symlink(), member.name)
                self.assertEqual(
                    bool(path.stat().st_mode & 0o111),
                    bool(member.mode & 0o111),
                    member.name,
                )
                if member.name not in CHANGED:
                    self.assertEqual(
                        path.read_bytes(),
                        archive.extractfile(member).read(),
                        member.name,
                    )
        self.assertTrue(CHANGED.issubset(names))
        self.assertEqual((len(names), len(names - CHANGED)), (4133, 4129))

    def test_exact_seven_path_delta(self):
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
        self.assertEqual(changed | untracked, CHANGED | NEW)
        self.assertEqual(len(CHANGED | NEW), 7)

    def test_exact_artifact_source_and_notice_mapping(self):
        delivery = json.loads((HERE / "delivery.json").read_bytes())
        self.assertEqual(sha((HERE / "delivery.json").read_bytes()), DELIVERY_SHA)
        self.assertEqual(delivery["supported_interfaces"], ["aware"])
        self.assertEqual((delivery["packages"], delivery["aware_packages"]), (32, 19))
        self.assertEqual(len(delivery["packet_member_map"]), 871)
        sources = 0
        for original, row in delivery["packet_member_map"].items():
            path = ROOT / row["path"]
            self.assertFalse(path.is_symlink(), original)
            self.assertEqual(
                (sha(path.read_bytes()), path.stat().st_size),
                (row["sha256"], row["bytes"]),
                original,
            )
            sources += original.startswith("source/")
        self.assertEqual(sources, 549)
        notices = json.loads((HERE / "packet/NOTICE-BINDINGS.json").read_bytes())
        self.assertEqual(notices["candidate_archive_sha256"], PAYLOAD_SHA)
        self.assertEqual(len(notices["wheel_legal_copies"]), 51)
        self.assertEqual(len(notices["inherited_notice_inputs"]), 236)
        self.assertEqual(len(notices["new_notice_inputs"]), 23)
        for name, expected in (
            (
                "distribution/canonical-agent-source-notice-review-v1.tar.gz",
                ENVELOPE_SHA,
            ),
            (
                "packet/payload/aware-canonical-neutral-fs-internal-v1.tar.gz",
                PAYLOAD_SHA,
            ),
        ):
            self.assertEqual(sha((HERE / name).read_bytes()), expected)

    def test_selection_keeps_preparation_and_owner_boundaries(self):
        record = (HERE / "SELECTION.md").read_text()
        for phrase in (
            "Selected locally; not publicly delivered",
            "Independent selection review pending",
            "Instructions remain draft",
            "sole software",
            "aware.protocol.toml",
            "0.2.0a1",
            "0.8.0",
            "0.3.4",
            "0.4.2",
            "No `aware init`",
            "guard discovery",
            "No contract version is allocated",
            "never automatically retry known publication",
            "every-write detection",
            "continuous confinement",
            "No push is authorized",
        ):
            self.assertIn(phrase, record)
        entrance = (HERE / "README.md").read_text()
        for phrase in (
            "Selected locally; not publicly delivered",
            "Instructions remain draft",
            "No `aware init`",
            "automatic guard discovery",
            "prepared inputs",
            "Never overlay",
            "not distribution packages",
        ):
            self.assertIn(phrase, entrance)
        self.assertIn(
            "Locally selected unified filesystem collaboration preview",
            (ROOT / "README.md").read_text(),
        )
        agent = json.loads((ROOT / "protocols/agent/release.json").read_bytes())
        self.assertEqual(agent["version"], "0.1.0a6")
        self.assertEqual(agent["agent_contract"]["version"], "1.2.1")
        self.assertFalse((ROOT / "protocols/collaboration/selection.json").exists())
        self.assertNotIn("canonical-agent-fs-v1", (ROOT / "AGENTS.md").read_text())

    def test_selected_document_links_resolve(self):
        for name in sorted(CHANGED | {str((HERE / "SELECTION.md").relative_to(ROOT))}):
            path = ROOT / name
            for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if not link.startswith(("https:", "http:", "#")):
                    self.assertTrue((path.parent / link).is_file(), (name, link))

    def test_historical_receipts_installer_and_replay_are_unchanged(self):
        self.assertEqual(
            sha((HERE / "test_local_integration.py").read_bytes()), REPLAY_SHA
        )
        self.assertEqual(sha((HERE / "install.py").read_bytes()), INSTALLER_SHA)
        layout = json.loads((HERE / "layout-review.json").read_bytes())
        self.assertFalse(layout["publication_authorized"])
        self.assertFalse(layout["public_selection_authorized"])
        self.assertEqual(
            sha((HERE / "layout-review.json").read_bytes()),
            "4a9688c47105934c72783cea59574f2a78975b030581c15b9c19f9f7b47f5c8c",
        )
        self.assertIn(
            "independently accepted", (HERE / "LOCAL-INTEGRATION.md").read_text()
        )

    def test_fresh_offline_accepted_installer(self):
        path = HERE / "test_local_integration.py"
        self.assertEqual(sha(path.read_bytes()), REPLAY_SHA)
        spec = importlib.util.spec_from_file_location(
            "accepted_agent_integration", path
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        case = module.IntegrationTests("test_fresh_offline_integrated_installation")
        case.setUp()
        case.test_fresh_offline_integrated_installation()


if __name__ == "__main__":
    unittest.main()
