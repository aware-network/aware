"""Exact local a12 delivery selection with retained reads, not public release."""

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path
from types import FunctionType

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "68f83a514446ac93eefd9c00ccb62c0f9d10f895"
RELEASE = "releases/canonical-reference-fs-v1"
ISSUE = "docs/issues/2026/10/19/fb-2026-10-19-canonical-reference-local-selection-v0.md"
SCOPE = {
    ISSUE,
    "README.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/SELECTED.json",
    RELEASE + "/README.md",
    RELEASE + "/LOCAL-SELECTION.md",
    RELEASE + "/test_local_selection.py",
}
LAYOUT_SHA = "72585c989e6f1438a3ad093fe9a09de841f868728c676582569a69f97cdf4862"
INDEX_SHA = "19497ad59946415d7edc737381735e9f666ec74884275d4d3ec7688924c38113"
ENVELOPE_SHA = "afca86cad0fe96c40250819a37b3ab7284236b30d12db919e6596c2aae6a9d30"
PAYLOAD_SHA = "8c804765c0aae2ee8ffe72768158867eab29dae93c669ec6c259421103eaf0e8"
ROOT_OLD = """Agent **0.2.0a12** is prepared and unselected; instructions remain draft.
The proposed installer targets this candidate, not the currently selected a11.
See [reference navigation](protocols/workspace/REFERENCE-NAVIGATION.md) and
[qualification bounds](releases/canonical-reference-fs-v1/REVIEW-STATUS.md). Existing useful-task and
implementation/draft branches remain unchanged. Workspace stdin/focus does not
automate Issue guards. Integration, selection, freeze and publication are separate."""
ROOT_NEW = """Agent **0.2.0a12** is selected locally; public delivery is not yet authorized.
Instructions remain draft. Use this reviewed checkout, not unchanged public main.
The [delivery pointer](releases/SELECTED.json) binds the complete envelope;
[local selection](releases/canonical-reference-fs-v1/LOCAL-SELECTION.md) records
the limits. Existing useful-task and implementation/draft branches are unchanged.
Workspace stdin/focus does not automate Issue guards. Instruction freeze and
publication remain separate; do not overlay installations or migrate contributor commands."""


def sha(body):
    return hashlib.sha256(body).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def load(path, digest):
    if path.is_symlink() or sha(path.read_bytes()) != digest:
        raise ValueError("original_selection_reader_required")
    spec = importlib.util.spec_from_file_location("reference_original_selection", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def derive_delivery_record(root):
    original = load(
        root / "releases/canonical-init-summary-fs-v1/test_local_selection.py",
        "04b19daa657fcb45fc7865db0cfaab77249f79177c5c553c4bc83e3d34827ba2",
    )
    original.BASELINE = BASELINE
    function = original.derive_delivery_record
    replacements = {
        "canonical-init-summary-fs-v1": "canonical-reference-fs-v1",
        "canonical-init-summary-source-notice-review-v1.tar.gz": "canonical-reference-source-notice-review-v1.tar.gz",
        "a5006a828cf465ddd50eb219476e08292558b82dccc8d5a5838eb72a1755e6a6": LAYOUT_SHA,
        "3bfb00f7950169a6bf916f38dc1a81536b0e4a5f243ce97c79302946a64bc164": INDEX_SHA,
        "73f5038b365dcc7f193b7ebd71b77145d12fe2386311be75dcffd9afadd25df9": ENVELOPE_SHA,
        "d133ae36d78648b0f1c77652b7ab56ded7b2180620e0c023eccf9da4c2cc88e0": PAYLOAD_SHA,
    }
    if not set(replacements).issubset(function.__code__.co_consts):
        raise ValueError("original_delivery_constants_required")
    bound = FunctionType(
        function.__code__.replace(
            co_consts=tuple(
                replacements.get(c, c) if isinstance(c, str) else c
                for c in function.__code__.co_consts
            )
        ),
        function.__globals__,
    )
    assert bound.__code__.co_code == function.__code__.co_code
    return bound(root)


class Selection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {}
        for entry in git("ls-tree", "-r", "-z", BASELINE).split(b"\0"):
            if entry:
                meta, name = entry.split(b"\t", 1)
                mode, kind, oid = meta.split()
                assert kind == b"blob" and mode in (b"100644", b"100755")
                cls.rows[name.decode()] = (mode, oid)
        cls.record = json.loads((ROOT / "releases/SELECTED.json").read_bytes())

    def test_exact_scope_and_conservation(self):
        actual = set()
        for parent, dirs, files in os.walk(ROOT):
            dirs[:] = [n for n in dirs if n != ".git"]
            for name in files:
                path = Path(parent) / name
                self.assertFalse(path.is_symlink())
                actual.add(str(path.relative_to(ROOT)))
        self.assertEqual(actual, set(self.rows) | SCOPE)
        raw = subprocess.check_output(
            ["git", "-C", str(ROOT), "cat-file", "--batch"],
            input=b"".join(oid + b"\n" for _, oid in self.rows.values()),
        )
        offset, changed = 0, set()
        for name, (mode, oid) in self.rows.items():
            end = raw.index(b"\n", offset)
            found, kind, size = raw[offset:end].split()
            start, size = end + 1, int(size)
            self.assertEqual((found, kind, raw[start + size]), (oid, b"blob", 10))
            path = ROOT / name
            self.assertEqual(bool(path.stat().st_mode & 0o111), mode == b"100755", name)
            if path.read_bytes() != raw[start : start + size]:
                changed.add(name)
            offset = start + size + 1
        self.assertEqual(offset, len(raw))
        self.assertEqual(changed | (actual - set(self.rows)), SCOPE)
        self.assertEqual(
            (len(self.rows), len(actual), len(set(self.rows) - SCOPE)),
            (1749, 1752, 1744),
        )

    def test_pointer_derivation_and_issue_scope(self):
        self.assertEqual(self.record, derive_delivery_record(ROOT))
        self.assertEqual(self.record["canonical_profile"], "portable_protocols")
        self.assertNotIn("packages", self.record)
        self.assertNotIn("published_revision", self.record)
        for key in (
            "public_delivery_authorized",
            "contributor_selection_changed",
            "domain_matrix_replayed",
            "unassisted_onboarding_proven",
            "detached_wheels_accepted",
            "tooling_activation_performed",
        ):
            self.assertFalse(self.record[key])
        self.assertEqual(self.record["instruction_status"], "draft")
        self.assertEqual(self.record["selection_review"], "pending")
        section = (
            (ROOT / ISSUE)
            .read_text()
            .split("## Ownership Scope", 1)[1]
            .split("##", 1)[0]
        )
        self.assertEqual(
            {
                line.strip()[3:-1]
                for line in section.splitlines()
                if line.strip().startswith("- `")
            },
            SCOPE,
        )

    def test_artifacts_software_and_legal_unchanged(self):
        self.assertEqual(
            sha((ROOT / RELEASE / "SOURCE-INDEX.json").read_bytes()), INDEX_SHA
        )
        self.assertEqual(
            sha(
                (
                    ROOT
                    / RELEASE
                    / "canonical-reference-source-notice-review-v1.tar.gz"
                ).read_bytes()
            ),
            ENVELOPE_SHA,
        )
        self.assertEqual(self.record["payload_sha256"], PAYLOAD_SHA)
        index = json.loads((ROOT / RELEASE / "SOURCE-INDEX.json").read_bytes())
        self.assertEqual(len(index["files"]), 1342)
        self.assertEqual(self.record["catalog_revision"], index["catalog_revision"])
        for name in self.rows:
            if name.startswith(("workspaces/", RELEASE + "/")) and name not in SCOPE:
                self.assertEqual(
                    (ROOT / name).read_bytes(), git("show", BASELINE + ":" + name), name
                )
        self.assertEqual(
            len(
                json.loads((ROOT / RELEASE / "NOTICE-BINDINGS.json").read_bytes())[
                    "detached_wheel_gaps"
                ]
            ),
            6,
        )
        audit = json.loads((ROOT / RELEASE / "CONTENT-AUDIT.json").read_bytes())
        self.assertEqual(
            (len(audit["findings"]), audit["clearance"]), (12, "not_granted")
        )

    def test_predecessor_contributor_installer_and_guides_preserved(self):
        for name in self.rows:
            if name in {
                "AGENTS.md",
                "CONTRIBUTING.md",
                "aware.protocol.toml",
                "protocols/install.py",
            } or name.startswith(
                (
                    ".aware/",
                    "docs/agents/",
                    "protocols/",
                    "releases/canonical-init-summary-fs-v1/",
                )
            ):
                self.assertEqual(
                    (ROOT / name).read_bytes(), git("show", BASELINE + ":" + name), name
                )
        old = json.loads(git("show", BASELINE + ":releases/SELECTED.json"))
        self.assertEqual(old["release"], "canonical-init-summary-fs-v1")
        self.assertTrue((ROOT / "releases" / old["envelope"]).is_file())

    def test_status_only_root_and_explicit_limits(self):
        before = git("show", BASELINE + ":README.md").decode()
        self.assertEqual(before.count(ROOT_OLD), 1)
        self.assertEqual(
            (ROOT / "README.md").read_text(), before.replace(ROOT_OLD, ROOT_NEW)
        )
        for name in (
            "docs/alignment/CURRENT.md",
            "releases/README.md",
            RELEASE + "/README.md",
            RELEASE + "/LOCAL-SELECTION.md",
        ):
            self.assertIn(
                "public delivery is not yet authorized", (ROOT / name).read_text()
            )
        for name in (
            "README.md",
            "protocols/WORKFLOW.md",
            "protocols/workspace/REVIEWED-SETUP.md",
        ):
            before = git("show", BASELINE + ":" + name).decode()
            after = (ROOT / name).read_text()
            self.assertEqual(
                re.findall(r"```(?:sh|bash)[^\n]*\n.*?```", before, re.DOTALL),
                re.findall(r"```(?:sh|bash)[^\n]*\n.*?```", after, re.DOTALL),
            )

    def test_markdown_links_resolve(self):
        for name in SCOPE:
            if name.endswith(".md") and not name.startswith("docs/issues/"):
                for link in re.findall(r"\]\(([^)]+)\)", (ROOT / name).read_text()):
                    if "://" in link or link.startswith("mailto:"):
                        continue
                    location, _, fragment = link.partition("#")
                    target = (
                        (ROOT / name).parent / location if location else ROOT / name
                    )
                    self.assertTrue(target.is_file(), (name, link))
                    if fragment:
                        anchors = {
                            re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-")
                            for h in re.findall(
                                r"^#{1,6}\s+(.+)$", target.read_text(), re.MULTILINE
                            )
                        }
                        self.assertIn(fragment, anchors, (name, link))

    def test_retained_installation_reads(self):
        original = load(
            ROOT / RELEASE / "test_local_integration.py",
            "e43c4a7d786930d2e88888a554d81028e6e1f4560f7220225661356e0820a7ee",
        )
        original.Integration.test_original_retained_installation_reads(self)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--delivery-record":
        print(
            json.dumps(
                derive_delivery_record(Path(sys.argv[2])), sort_keys=True, indent=2
            )
        )
    else:
        unittest.main()
