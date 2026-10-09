"""Git delivery accounting; reuse accepted artifacts and the genuine installer."""

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
BASELINE = "9dd6daf559fcef9e9eba252ad1ff2ef6fc005fd0"
REMOTE_PREDECESSOR = "0e1af47a417df143681125e467930aedf4157cd2"
CHANGED = {
    "README.md",
    "workspaces/README.md",
    "protocols/collaboration/previews/canonical-agent-fs-v1/README.md",
    "protocols/collaboration/previews/canonical-agent-fs-v1/SELECTION.md",
    "workspaces/previews/canonical-agent-fs-v1/README.md",
}
NEW = {
    "protocols/collaboration/previews/canonical-agent-fs-v1/PUBLICATION.md",
    "protocols/collaboration/previews/canonical-agent-fs-v1/test_publication.py",
    "docs/issues/2026/10/09/fb-2026-10-09-canonical-agent-git-publication-v0.md",
}

path = HERE / "test_selection.py"
assert hashlib.sha256(path.read_bytes()).hexdigest() == (
    "fae0b97023172ebf10e3514fb68e58753c0eaf2c4ad8eb6eff9b023070d9f5e9"
)
spec = importlib.util.spec_from_file_location("accepted_agent_selection", path)
assert spec is not None and spec.loader is not None
accepted = importlib.util.module_from_spec(spec)
spec.loader.exec_module(accepted)


class PublicationTests(accepted.SelectionTests):
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
        self.assertEqual((len(names), len(names - CHANGED)), (4136, 4131))

    def test_exact_seven_path_delta(self):
        # Inherited method name is historical; this delivery has eight paths.
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

    def test_selection_keeps_preparation_and_owner_boundaries(self):
        record = (HERE / "PUBLICATION.md").read_text()
        for phrase in (
            "Luis explicitly authorized",
            "non-force",
            "32-package",
            "0.2.0a1",
            "0.8.0",
            "0.3.4",
            "0.4.2",
            "sole software",
            "already prepared",
            "no `aware init`",
            "guard discovery",
            "Instructions remain draft",
            "never automatically retry known",
            "not every-write",
            "hostile-process isolation",
        ):
            self.assertIn(phrase, record)
        entrance = (HERE / "README.md").read_text()
        self.assertIn("Selected Git preview", entrance)
        self.assertIn("No `aware init`", entrance)
        self.assertIn("Never overlay", entrance)
        self.assertIn("Instructions remain draft", entrance)
        self.assertIn(
            "Available now: unified filesystem collaboration preview",
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
                "docs/issues/2026/10/09/fb-2026-10-09-canonical-agent-local-integration-v0.md",
                "docs/issues/2026/10/09/fb-2026-10-09-canonical-agent-local-selection-v0.md",
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
        self.assertEqual(len(actual), 888)
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
        self.assertEqual(int(count), 8)
