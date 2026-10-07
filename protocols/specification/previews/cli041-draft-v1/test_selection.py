"""Selection accounting; reuse the exact accepted installer, not domain logic."""

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
BASELINE = "05600f38fa343adc882d8581168728713ee1caa9"
CHANGED = {
    "README.md",
    "workspaces/README.md",
    "protocols/specification/README.md",
    "protocols/specification/previews/cli041-draft-v1/README.md",
    "workspaces/previews/specification-cli041-draft-v1/README.md",
}
NEW = {
    "protocols/specification/previews/cli041-draft-v1/SELECTION.md",
    "protocols/specification/previews/cli041-draft-v1/test_selection.py",
    "docs/issues/2026/10/07/fb-2026-10-07-specification-cli041-selection-v1.md",
}
REPLAY_SHA = "659267a464e445895976d0d613a369dc56ef878b25120704e86e7d1b35e028e5"


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
        self.assertEqual(len(names), 2373)
        self.assertTrue(CHANGED.issubset(names))
        self.assertEqual(len(names - CHANGED), 2368)

    def test_exact_eight_path_delta(self):
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
        self.assertEqual(len(CHANGED | NEW), 8)

    def test_all_four_packet_maps_and_archives(self):
        for directory, count, digest in (
            (
                ROOT / "protocols/specification",
                429,
                "865c57be501818dc380c9019a0fc710658d67242375a080b563258d6365a97a0",
            ),
            (
                ROOT / "protocols/specification/previews/admit-runtime-v1",
                439,
                "e5d7bf16e7bf4d5cfd91faa3c85c9697feac4a5d9c709c84ea9ef71948dc387f",
            ),
            (
                ROOT / "protocols/specification/previews/cli022-reader-v1",
                449,
                "578b25b0d68bed3546ac54fbfeb426062415e6b519df0a7829172e33a8340c2e",
            ),
            (
                HERE,
                446,
                "b78a45f66ef89ea081d61cd77a37be9d5ccebbfe10b2df60fa577fab53ad0934",
            ),
        ):
            mapping = json.loads((directory / "delivery.json").read_bytes())
            self.assertEqual(mapping["packet_sha256"], digest)
            self.assertEqual(len(mapping["packet_member_map"]), count)
            for row in mapping["packet_member_map"].values():
                path = ROOT / row["path"]
                self.assertFalse(path.is_symlink())
                self.assertEqual(
                    (sha(path.read_bytes()), path.stat().st_size),
                    (row["sha256"], row["bytes"]),
                )
            archives = list((directory / "distribution").glob("*.tar.gz"))
            self.assertEqual(len(archives), 1)
            self.assertEqual(sha(archives[0].read_bytes()), digest)

    def test_local_selection_and_separate_roles_are_explicit(self):
        record = (HERE / "SELECTION.md").read_text()
        for phrase in (
            "selected locally; not publicly delivered",
            "0.4.1",
            "0.3.1",
            "0.6.1",
            "26 packages",
            "27 packages",
            "1.3.0 remains unallocated",
            "No push",
            "Historical customer command sequences remain drafts",
            "known publication",
            "approved-iteration authoring",
            "every-write",
            "continuous",
        ):
            self.assertIn(phrase, record)
        self.assertIn(
            "Locally selected SPEC CLI041 draft successor",
            (ROOT / "README.md").read_text(),
        )
        current = (ROOT / "protocols/specification/README.md").read_text()
        self.assertIn("only aware-spec", current)
        self.assertIn("published CLI022 installation", current)
        self.assertIn("**aware-protocol 0.3.1 / aware-spec 0.2.2**", current)
        entrance = (HERE / "README.md").read_text()
        self.assertIn("independent selection review pending", entrance)
        self.assertIn("Never overlay", entrance)
        self.assertIn("../cli022-reader-v1/README.md", entrance)

    def test_selected_document_links_resolve(self):
        for name in sorted(CHANGED | {str((HERE / "SELECTION.md").relative_to(ROOT))}):
            path = ROOT / name
            for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if not link.startswith(("https:", "http:", "#")):
                    self.assertTrue((path.parent / link).is_file(), (name, link))

    def test_historical_receipt_and_replay_remain_exact(self):
        self.assertEqual(
            sha((HERE / "test_local_integration.py").read_bytes()), REPLAY_SHA
        )
        layout = json.loads((HERE / "layout-review.json").read_bytes())
        self.assertFalse(layout["publication_authorized"])
        self.assertFalse(layout["public_selection_authorized"])
        mapping = json.loads((HERE / "delivery.json").read_bytes())
        self.assertIn("instruction_freeze", mapping["nonclaims"])
        notices = json.loads((HERE / "packet/NOTICE-BINDINGS.json").read_bytes())
        self.assertEqual(len(notices["wheel_legal_copies"]), 43)
        self.assertEqual(len(notices["inherited_notices"]), 236)
        self.assertEqual(
            sha((HERE / "install.py").read_bytes()),
            "03f7fed6f410cc803ce6b0b95bc59371cc4499531f5f5d09df2fdd6faf68909b",
        )

    def test_fresh_offline_accepted_installer_replay(self):
        path = HERE / "test_local_integration.py"
        self.assertEqual(sha(path.read_bytes()), REPLAY_SHA)
        spec = importlib.util.spec_from_file_location("accepted_cli041_replay", path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        case = module.LocalIntegrationTests("test_actual_integrated_offline_installer")
        case.test_actual_integrated_offline_installer()


if __name__ == "__main__":
    unittest.main()
