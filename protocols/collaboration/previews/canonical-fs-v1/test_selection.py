"""Local artifact selection accounting; reuse the accepted actual installer."""

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
BASELINE = "51e51b2d01d442f32468af230efdc5b673ee099a"
CHANGED = {
    "README.md",
    "workspaces/README.md",
    "protocols/collaboration/previews/canonical-fs-v1/README.md",
    "workspaces/previews/canonical-fs-v1/README.md",
}
NEW = {
    "protocols/collaboration/previews/canonical-fs-v1/SELECTION.md",
    "protocols/collaboration/previews/canonical-fs-v1/test_selection.py",
    "docs/issues/2026/10/08/fb-2026-10-08-canonical-neutral-local-selection-v1.md",
}
REPLAY_SHA = "cf976c21839ec3c808eb299a3448bb491f049f7dde74f06032d636d289eafef6"
ENVELOPE_SHA = "d135c339b7c14d28d2df1ed7c4335fad71e3d5e163c3ede70f3cef692c679f75"
PAYLOAD_SHA = "6225a71ca27450170ec3b1d55336191d52fc5346c7739fff73141febb4877fb1"


def sha(body):
    return hashlib.sha256(body).hexdigest()


class SelectionTests(unittest.TestCase):
    def test_baseline_bytes_and_git_executable_modes(self):
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
        self.assertEqual(len(names), 3244)
        self.assertTrue(CHANGED.issubset(names))
        self.assertEqual(len(names - CHANGED), 3240)

    def test_exact_seven_path_delta(self):
        changes = set(
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
        self.assertEqual(changes | untracked, CHANGED | NEW)
        self.assertEqual(len(CHANGED | NEW), 7)

    def test_exact_envelope_map_payload_and_manifests(self):
        delivery = json.loads((HERE / "delivery.json").read_bytes())
        self.assertEqual(len(delivery["packet_member_map"]), 853)
        for original, row in delivery["packet_member_map"].items():
            path = ROOT / row["path"]
            self.assertFalse(path.is_symlink(), original)
            self.assertEqual(
                (sha(path.read_bytes()), path.stat().st_size),
                (row["sha256"], row["bytes"]),
                original,
            )
        for filename, expected, manifest_digest in (
            (
                "distribution/canonical-neutral-source-notice-review-v1.tar.gz",
                ENVELOPE_SHA,
                "ec085ed07459401a2953d787f6c1eb187fb2a443d1974bb8af97ac1536e56c16",
            ),
            (
                "packet/payload/aware-canonical-neutral-fs-internal-v1.tar.gz",
                PAYLOAD_SHA,
                "badd5543520602437350a1af940c6e9825dbe8562de225a6b05e46ce543ec05a",
            ),
        ):
            path = HERE / filename
            self.assertEqual(sha(path.read_bytes()), expected)
            with tarfile.open(path) as archive:
                manifests = [
                    m
                    for m in archive.getmembers()
                    if m.isfile()
                    and (
                        m.name == "manifest.json"
                        or m.name.count("/") == 1
                        and m.name.endswith("/manifest.json")
                    )
                ]
                self.assertEqual(len(manifests), 1)
                self.assertEqual(
                    sha(archive.extractfile(manifests[0]).read()), manifest_digest
                )

    def test_local_selection_preserves_owners_and_preparation_limits(self):
        record = (HERE / "SELECTION.md").read_text()
        for phrase in (
            "Selected locally; not publicly delivered",
            "Independent selection review pending",
            "sole software",
            "18 Aware packages",
            "533 committed source",
            "31 packages",
            "0.7.1",
            "0.3.2",
            "0.4.2",
            "no supported repository/profile initializer",
            "Contract 1.3.0 remains unallocated",
            "Instructions remain draft",
            "never automatically retry",
            "every-write detection",
            "continuous confinement",
            "No push is authorized",
        ):
            self.assertIn(phrase, record)
        entrance = (HERE / "README.md").read_text()
        for phrase in (
            "Selected locally; not publicly delivered",
            "Instructions remain draft",
            "already prepared",
            "no aware init",
            "three family commands",
            "Never overlay",
            "not distribution packages",
        ):
            self.assertIn(phrase, entrance)
        self.assertIn(
            "Locally selected canonical filesystem composition",
            (ROOT / "README.md").read_text(),
        )
        self.assertFalse((ROOT / "protocols/collaboration/selection.json").exists())
        agent = json.loads((ROOT / "protocols/agent/release.json").read_bytes())
        self.assertEqual(agent["version"], "0.1.0a6")
        self.assertEqual(agent["agent_contract"]["version"], "1.2.1")

    def test_selected_document_links_resolve(self):
        for name in sorted(CHANGED | {str((HERE / "SELECTION.md").relative_to(ROOT))}):
            path = ROOT / name
            for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if not link.startswith(("https:", "http:", "#")):
                    self.assertTrue((path.parent / link).is_file(), (name, link))

    def test_historical_receipts_replay_and_legal_bytes_remain_exact(self):
        self.assertEqual(
            sha((HERE / "test_local_integration.py").read_bytes()), REPLAY_SHA
        )
        layout = json.loads((HERE / "layout-review.json").read_bytes())
        self.assertFalse(layout["publication_authorized"])
        self.assertFalse(layout["public_selection_authorized"])
        self.assertEqual(
            sha((HERE / "layout-review.json").read_bytes()),
            "01c9b62cbd7589aad845ee5010337c4ca2a4a9306525a0479067d334bb0f4da7",
        )
        notices = json.loads((HERE / "packet/NOTICE-BINDINGS.json").read_bytes())
        self.assertEqual(len(notices["wheel_legal_copies"]), 49)
        self.assertEqual(len(notices["inherited_notice_inputs"]), 236)
        self.assertEqual(len(notices["new_notice_inputs"]), 23)
        self.assertEqual(
            sha((HERE / "install.py").read_bytes()),
            "2777f66da40a39709cc843685dc84fe4f49eb23cdfece380ebf2c411d253aaf5",
        )

    def test_fresh_offline_accepted_installer_replay(self):
        path = HERE / "test_local_integration.py"
        self.assertEqual(sha(path.read_bytes()), REPLAY_SHA)
        spec = importlib.util.spec_from_file_location("accepted_canonical_replay", path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        case = module.LocalIntegrationTests(
            "test_fresh_offline_integrated_installation"
        )
        case.test_fresh_offline_integrated_installation()


if __name__ == "__main__":
    unittest.main()
