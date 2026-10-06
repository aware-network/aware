"""Git delivery accounting; reuse accepted byte and real-install checks."""

import importlib.util
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASELINE = "2dc65f0c60a47071280112c364676cd40f3fed01"
CHANGED = {
    "README.md",
    "workspaces/README.md",
    "protocols/specification/README.md",
    "protocols/specification/previews/admit-runtime-v1/README.md",
    "protocols/specification/previews/admit-runtime-v1/SELECTION.md",
}
NEW = {
    "protocols/specification/previews/admit-runtime-v1/PUBLICATION.md",
    "protocols/specification/previews/admit-runtime-v1/test_publication.py",
    "docs/issues/2026/10/06/fb-2026-10-06-specification-admit-runtime-git-publication-v1.md",
}

spec = importlib.util.spec_from_file_location(
    "accepted_selection_replay", HERE / "test_selection.py"
)
assert spec is not None and spec.loader is not None
accepted = importlib.util.module_from_spec(spec)
spec.loader.exec_module(accepted)


class PublicationTests(accepted.SelectionTests):
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

    def test_selection_axes_and_limits_are_explicit(self):
        text = (HERE / "PUBLICATION.md").read_text()
        for required in (
            "Luis explicitly authorized",
            "0.3.1",
            "0.2.0",
            "27 packages",
            "1.3.0 remains unallocated",
            "authoring/import",
            "historical unfrozen drafts",
            "non-force",
            "not every-write",
            "not continuous",
        ):
            self.assertIn(required, text)
        root = (ROOT / "README.md").read_text()
        self.assertIn("27-package closure", root)
        self.assertIn(
            "protocols/specification/previews/admit-runtime-v1/install.py", root
        )
        self.assertNotIn("publication pending", root)
        entrance = (HERE.parents[1] / "README.md").read_text()
        self.assertIn("current Git preview", entrance)
        self.assertIn("Retained published predecessor", entrance)
        self.assertIn(
            "selected standalone Git preview", (HERE / "README.md").read_text()
        )
        historical = (HERE / "SELECTION.md").read_text()
        self.assertIn("Historical checkpoint", historical)
        self.assertIn("not publicly delivered at that checkpoint", historical)

    def test_publication_links_resolve(self):
        path = HERE / "PUBLICATION.md"
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if not target.startswith(("https:", "http:", "#")):
                self.assertTrue((path.parent / target).is_file(), target)
