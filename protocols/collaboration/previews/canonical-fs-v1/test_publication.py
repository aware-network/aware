"""Git delivery accounting; reuse accepted bytes and the actual installer."""

import hashlib
import importlib.util
import io
import json
import re
import subprocess
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASELINE = "151f001ea6def6430cd1ea7e4d26324936540d97"
REMOTE_PREDECESSOR = "095b9c5cad57e8d4183533f385c7cf568caeb277"
CHANGED = {
    "README.md",
    "workspaces/README.md",
    "protocols/collaboration/previews/canonical-fs-v1/README.md",
    "protocols/collaboration/previews/canonical-fs-v1/SELECTION.md",
    "workspaces/previews/canonical-fs-v1/README.md",
}
NEW = {
    "protocols/collaboration/previews/canonical-fs-v1/PUBLICATION.md",
    "protocols/collaboration/previews/canonical-fs-v1/test_publication.py",
    "docs/issues/2026/10/08/fb-2026-10-08-canonical-neutral-git-publication-v1.md",
}

path = HERE / "test_selection.py"
assert hashlib.sha256(path.read_bytes()).hexdigest() == (
    "053513bb2702a28884b6266ae392e445957f9338cdd830e64c6bcdf8b1621e60"
)
spec = importlib.util.spec_from_file_location("accepted_canonical_selection", path)
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
        self.assertEqual(len(names), 3247)
        self.assertTrue(CHANGED.issubset(names))
        self.assertEqual(len(names - CHANGED), 3242)

    def test_exact_seven_path_delta(self):
        # Inherited name is historical; delivery has eight paths.
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
        self.assertEqual(len(CHANGED | NEW), 8)

    def test_local_selection_preserves_owners_and_preparation_limits(self):
        record = (HERE / "PUBLICATION.md").read_text()
        for phrase in (
            "Luis explicitly authorized",
            "non-force",
            "31-package",
            "0.7.1",
            "0.3.2",
            "0.4.2",
            "sole software",
            "not a unified aware",
            "already prepared",
            "Instructions remain draft",
            "contract 1.3.0 remains unallocated",
            "never automatically retry known publication",
            "not every-write",
            "not",
            "continuous",
        ):
            self.assertIn(phrase, record)
        entrance = (HERE / "README.md").read_text()
        self.assertIn("Selected standalone Git preview", entrance)
        self.assertIn("no aware init", entrance)
        self.assertIn("Never overlay", entrance)
        self.assertIn("Instructions remain draft", entrance)
        self.assertIn(
            "Available now: canonical filesystem collaboration preview",
            (ROOT / "README.md").read_text(),
        )
        historical = (HERE / "SELECTION.md").read_text()
        self.assertIn("Historical checkpoint", historical)
        self.assertIn("not publicly delivered at that checkpoint", historical)
        self.assertFalse((ROOT / "protocols/collaboration/selection.json").exists())
        agent = json.loads((ROOT / "protocols/agent/release.json").read_bytes())
        self.assertEqual(agent["version"], "0.1.0a6")
        self.assertEqual(agent["agent_contract"]["version"], "1.2.1")

    def test_selected_document_links_resolve(self):
        for name in sorted(
            CHANGED | {str((HERE / "PUBLICATION.md").relative_to(ROOT))}
        ):
            path = ROOT / name
            for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if not link.startswith(("https:", "http:", "#")):
                    self.assertTrue((path.parent / link).is_file(), (name, link))

    def test_accepted_outgoing_predecessor_scope(self):
        subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "merge-base",
                "--is-ancestor",
                REMOTE_PREDECESSOR,
                BASELINE,
            ],
            check=True,
        )
        layout = json.loads((HERE / "layout-review.json").read_bytes())
        expected = (
            set(layout["changed_files"])
            | {
                str((HERE / filename).relative_to(ROOT))
                for filename in (
                    "layout-review.json",
                    "LOCAL-INTEGRATION.md",
                    "test_local_integration.py",
                    "SELECTION.md",
                    "test_selection.py",
                )
            }
            | {
                "docs/issues/2026/10/08/fb-2026-10-08-canonical-neutral-local-integration-v1.md",
                "docs/issues/2026/10/08/fb-2026-10-08-canonical-neutral-local-selection-v1.md",
            }
        )
        actual = set(
            subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(ROOT),
                    "diff",
                    REMOTE_PREDECESSOR,
                    BASELINE,
                    "--name-only",
                ],
                text=True,
            ).splitlines()
        )
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 870)
        count = subprocess.check_output(
            [
                "git",
                "-C",
                str(ROOT),
                "rev-list",
                "--count",
                f"{REMOTE_PREDECESSOR}..{BASELINE}",
            ],
            text=True,
        )
        self.assertEqual(int(count), 9)
