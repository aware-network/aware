"""Git delivery accounting; reuse accepted byte and real installer checks."""

import hashlib
import importlib.util
import io
import re
import subprocess
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASELINE = "60f9aecf0f5245121ae59cfd8fb7eecfd3db0b44"
CHANGED = {
    "README.md",
    "workspaces/README.md",
    "protocols/specification/README.md",
    "workspaces/previews/specification-cli041-draft-v1/README.md",
    "protocols/specification/previews/cli041-draft-v1/README.md",
    "protocols/specification/previews/cli041-draft-v1/SELECTION.md",
}
NEW = {
    "protocols/specification/previews/cli041-draft-v1/PUBLICATION.md",
    "protocols/specification/previews/cli041-draft-v1/test_publication.py",
    "docs/issues/2026/10/07/fb-2026-10-07-specification-cli041-git-publication-v1.md",
}

path = HERE / "test_selection.py"
assert hashlib.sha256(path.read_bytes()).hexdigest() == (
    "cb569e016cba74d8565eb41170ef33200e490c6e2f8bd82ad7de9385c406667c"
)
spec = importlib.util.spec_from_file_location("accepted_cli041_selection_replay", path)
assert spec is not None and spec.loader is not None
accepted = importlib.util.module_from_spec(spec)
spec.loader.exec_module(accepted)


class PublicationTests(accepted.SelectionTests):
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
        self.assertEqual(len(names), 2376)
        self.assertTrue(CHANGED.issubset(names))
        self.assertEqual(len(names - CHANGED), 2370)

    def test_exact_eight_path_delta(self):
        # Inherited method name is historical; this publication has nine paths.
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
        self.assertEqual(len(CHANGED | NEW), 9)

    def test_local_selection_and_separate_roles_are_explicit(self):
        record = (HERE / "PUBLICATION.md").read_text()
        for phrase in (
            "Luis explicitly authorized",
            "non-force",
            "26 packages",
            "0.4.1",
            "0.6.1",
            "1.3.0 remains unallocated",
            "historical unfrozen drafts",
            "not every-write",
            "not continuous",
            "672-case",
            "approved-iteration authoring",
        ):
            self.assertIn(phrase, record)
        root = (ROOT / "README.md").read_text()
        self.assertIn("Available now: governed SPEC draft preview", root)
        self.assertIn("26-package installation", root)
        self.assertIn("CLI022 remains the separately installed", root)
        overview = (ROOT / "protocols/specification/README.md").read_text()
        self.assertIn("Selected standalone Git governed draft preview", overview)
        self.assertIn("**aware-protocol 0.3.1 / aware-spec 0.2.2**", overview)
        self.assertIn(
            "selected standalone Git preview", (HERE / "README.md").read_text()
        )
        historical = (HERE / "SELECTION.md").read_text()
        self.assertIn("Historical checkpoint", historical)
        self.assertIn("not publicly delivered at that checkpoint", historical)

    def test_publication_links_resolve(self):
        for name in sorted(
            CHANGED | {str((HERE / "PUBLICATION.md").relative_to(ROOT))}
        ):
            path = ROOT / name
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if not target.startswith(("https:", "http:", "#")):
                    self.assertTrue((path.parent / target).is_file(), (name, target))
