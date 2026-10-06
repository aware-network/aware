"""Local selection accounting; reuse the accepted real installer, not domain logic."""

import hashlib
import importlib.util
import json
import re
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASELINE = "d23d8d7c8e11"
CHANGED = {
    "README.md",
    "workspaces/README.md",
    "protocols/specification/README.md",
    "protocols/specification/previews/admit-runtime-v1/README.md",
}
NEW = {
    "protocols/specification/previews/admit-runtime-v1/SELECTION.md",
    "protocols/specification/previews/admit-runtime-v1/test_selection.py",
    "docs/issues/2026/10/06/fb-2026-10-06-specification-admit-runtime-selection-v1.md",
}


class SelectionTests(unittest.TestCase):
    def test_every_other_baseline_file_and_git_mode_is_preserved(self):
        rows = subprocess.check_output(
            ["git", "-C", str(ROOT), "ls-tree", "-r", BASELINE], text=True
        ).splitlines()
        for row in rows:
            attrs, name = row.split("\t", 1)
            mode, kind, blob = attrs.split()
            self.assertEqual(kind, "blob")
            path = ROOT / name
            self.assertFalse(path.is_symlink(), name)
            self.assertEqual(bool(path.stat().st_mode & 0o111), mode == "100755", name)
            if name not in CHANGED:
                body = subprocess.check_output(
                    ["git", "-C", str(ROOT), "cat-file", "blob", blob]
                )
                self.assertEqual(path.read_bytes(), body, name)
        self.assertTrue(CHANGED.issubset({row.split("\t", 1)[1] for row in rows}))

    def test_only_the_declared_selection_paths_are_dirty(self):
        # This check also works after the scoped implementation is committed.
        changed = set(
            subprocess.check_output(
                ["git", "-C", str(ROOT), "diff", "--name-only", BASELINE], text=True
            ).splitlines()
        )
        untracked = set(
            subprocess.check_output(
                ["git", "-C", str(ROOT), "ls-files", "--others", "--exclude-standard"],
                text=True,
            ).splitlines()
        )
        self.assertEqual(changed | untracked, CHANGED | NEW)

    def test_both_exact_packet_mappings_and_distributions(self):
        for directory, count, digest in (
            (
                ROOT / "protocols/specification",
                429,
                "865c57be501818dc380c9019a0fc710658d67242375a080b563258d6365a97a0",
            ),
            (
                HERE,
                439,
                "e5d7bf16e7bf4d5cfd91faa3c85c9697feac4a5d9c709c84ea9ef71948dc387f",
            ),
        ):
            value = json.loads((directory / "delivery.json").read_bytes())
            self.assertEqual(value["packet_sha256"], digest)
            self.assertEqual(len(value["packet_member_map"]), count)
            for record in value["packet_member_map"].values():
                path = ROOT / record["path"]
                self.assertFalse(path.is_symlink())
                body = path.read_bytes()
                self.assertEqual(len(body), record["bytes"])
                self.assertEqual(hashlib.sha256(body).hexdigest(), record["sha256"])
            archives = list((directory / "distribution").glob("*.tar.gz"))
            self.assertEqual(len(archives), 1)
            self.assertEqual(
                hashlib.sha256(archives[0].read_bytes()).hexdigest(), digest
            )

    def test_selection_axes_and_limits_are_explicit(self):
        text = (HERE / "SELECTION.md").read_text()
        for value in (
            "selected locally",
            "not publicly delivered",
            "0.3.1",
            "0.2.0",
            "27 packages",
            "1.3.0 remains unallocated",
            "authoring/import",
            "historical drafts",
            "No push",
        ):
            self.assertIn(value, text)
        self.assertIn(
            "Locally selected admit-runtime successor",
            (ROOT / "README.md").read_text(),
        )
        self.assertIn(
            "published predecessor", (HERE.parents[1] / "README.md").read_text()
        )
        self.assertIn("independent selection review", (HERE / "README.md").read_text())

    def test_selected_document_links_resolve(self):
        for path in (
            ROOT / "README.md",
            ROOT / "workspaces/README.md",
            HERE.parents[1] / "README.md",
            HERE / "README.md",
            HERE / "SELECTION.md",
        ):
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if not target.startswith(("https:", "http:", "#")):
                    self.assertTrue((path.parent / target).is_file(), (path, target))

    def test_original_layout_receipt_remains_historical(self):
        value = json.loads((HERE / "layout-review.json").read_bytes())
        self.assertFalse(value["publication_authorized"])
        self.assertFalse(value["public_selection_authorized"])
        notices = json.loads((HERE / "packet/NOTICE-BINDINGS.json").read_bytes())
        self.assertEqual(len(notices["wheel_legal_copies"]), 45)
        self.assertEqual(len(notices["inherited_notices"]), 236)

    def test_actual_accepted_installer_with_fresh_offline_environment(self):
        spec = importlib.util.spec_from_file_location(
            "accepted_admit_installer_replay", HERE / "test_local_integration.py"
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        case = module.LocalIntegrationTests("test_actual_integrated_offline_installer")
        case.test_actual_integrated_offline_installer()


if __name__ == "__main__":
    unittest.main()
