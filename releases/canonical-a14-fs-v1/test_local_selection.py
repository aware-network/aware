"""A14 local delivery pointer through original derivation and conservation tests."""

import hashlib
import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path
from types import FunctionType

ROOT = Path(
    os.environ.get("AWARE_A14_SELECTION_ROOT", Path(__file__).resolve().parents[2])
)
BASELINE = "de2b739d4dc04381e4e93225d0373cf5d7edfe31"
RELEASE = "releases/canonical-a14-fs-v1"
ISSUE = "docs/issues/2026/10/19/fb-2026-10-19-canonical-a14-local-selection-v0.md"
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
LAYOUT_SHA = "55d18f86bed814658e2e6994eb0d726595f05851483fec95a0a023e67f9ba919"
INDEX_SHA = "3d43a253a59418256c78880fa817ab3eed762f4c1511eca61ba402996477109b"
ENVELOPE_SHA = "050ed63545dd1d63c795285609e15dbdaa054c28788c9e5993e8a1871f356ea6"
PAYLOAD_SHA = "4d1bf3b5ab43e904d463ba307840cf681889339d7197b089083add866d692c58"
ROOT_OLD = """## Prepared a14 resource summaries

Agent **0.2.0a14** is prepared and unselected; this guidance remains draft.
The proposed installer targets a14, not the delivered a12 selection.
[Resource summaries](protocols/workspace/RESOURCE-RELEASES.md) distinguish
reported resource closes from incomplete ledgers and historical unknowns.
The [qualification bounds](releases/canonical-a14-fs-v1/REVIEW-STATUS.md) keep optional Goal and
positive create-first execution unqualified. Existing useful customer work,
optional SPEC, both reviews and manual Issue guards remain the current rail."""
ROOT_NEW = """## Locally selected a14 resource summaries

Agent **0.2.0a14** is selected locally; public delivery is not yet authorized.
Instructions remain draft. Use this reviewed checkout, not unchanged public main.
The [delivery pointer](releases/SELECTED.json) binds the complete envelope;
[local selection](releases/canonical-a14-fs-v1/LOCAL-SELECTION.md) records its limits.
[Resource summaries](protocols/workspace/RESOURCE-RELEASES.md) distinguish reported
closes from ledger completeness and historical unknowns. Optional Goal and positive
create-first remain unqualified; useful work, optional SPEC, both explicit reviews
and manual Issue guards remain. Do not overlay installations or change contributor
commands. Instruction freeze and publication are separate."""


def sha(body):
    return hashlib.sha256(body).hexdigest()


def load(path, digest, name):
    if path.is_symlink() or sha(path.read_bytes()) != digest:
        raise ValueError("original_selection_reader_required")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bind(function, replacements):
    code = function.__code__
    if not all(
        any(type(c) is type(k) and c == k for c in code.co_consts) for k in replacements
    ):
        raise ValueError("original_receiving_constant_required")
    result = FunctionType(
        code.replace(
            co_consts=tuple(
                next(
                    (
                        v
                        for k, v in replacements.items()
                        if type(c) is type(k) and c == k
                    ),
                    c,
                )
                for c in code.co_consts
            )
        ),
        function.__globals__,
        function.__name__,
        function.__defaults__,
        function.__closure__,
    )
    assert result.__code__.co_code == code.co_code
    return result


def derive_delivery_record(root):
    original = load(
        root / "releases/canonical-init-summary-fs-v1/test_local_selection.py",
        "04b19daa657fcb45fc7865db0cfaab77249f79177c5c553c4bc83e3d34827ba2",
        "a14_original_delivery_derivation",
    )
    original.BASELINE = BASELINE
    return bind(
        original.derive_delivery_record,
        {
            "canonical-init-summary-fs-v1": "canonical-a14-fs-v1",
            "canonical-init-summary-source-notice-review-v1.tar.gz": "canonical-a14-source-notice-review-v1.tar.gz",
            "a5006a828cf465ddd50eb219476e08292558b82dccc8d5a5838eb72a1755e6a6": LAYOUT_SHA,
            "3bfb00f7950169a6bf916f38dc1a81536b0e4a5f243ce97c79302946a64bc164": INDEX_SHA,
            "73f5038b365dcc7f193b7ebd71b77145d12fe2386311be75dcffd9afadd25df9": ENVELOPE_SHA,
            "d133ae36d78648b0f1c77652b7ab56ded7b2180620e0c023eccf9da4c2cc88e0": PAYLOAD_SHA,
        },
    )(root)


owner = load(
    ROOT / "releases/canonical-reference-fs-v1/test_local_selection.py",
    "9ce41afb1349011f1c5de234e7a01d4f174bda094059ee0c50dd573b9e23200a",
    "a14_original_selection_accounting",
)
for name in (
    "ROOT",
    "BASELINE",
    "RELEASE",
    "ISSUE",
    "SCOPE",
    "LAYOUT_SHA",
    "INDEX_SHA",
    "ENVELOPE_SHA",
    "PAYLOAD_SHA",
    "ROOT_OLD",
    "ROOT_NEW",
    "derive_delivery_record",
):
    setattr(owner, name, globals()[name])


class Selection(owner.Selection):
    test_exact_scope_and_conservation = bind(
        owner.Selection.test_exact_scope_and_conservation,
        {
            (1749, 1752, 1744): (1822, 1825, 1817),
        },
    )
    test_predecessor_contributor_installer_and_guides_preserved = bind(
        owner.Selection.test_predecessor_contributor_installer_and_guides_preserved,
        {
            (
                ".aware/",
                "docs/agents/",
                "protocols/",
                "releases/canonical-init-summary-fs-v1/",
            ): (
                ".aware/",
                "docs/agents/",
                "protocols/",
                "releases/canonical-reference-fs-v1/",
            ),
            "canonical-init-summary-fs-v1": "canonical-reference-fs-v1",
        },
    )
    test_retained_installation_reads = bind(
        owner.Selection.test_retained_installation_reads,
        {
            "e43c4a7d786930d2e88888a554d81028e6e1f4560f7220225661356e0820a7ee": "725ed1b5b681efdc7a6a944e96ceae6df074a8494fa065c7fd20f43b9a6b831c",
        },
    )

    def test_artifacts_software_and_legal_unchanged(self):
        bind(
            owner.Selection.test_artifacts_software_and_legal_unchanged,
            {
                1342: 1372,
                "canonical-reference-source-notice-review-v1.tar.gz": "canonical-a14-source-notice-review-v1.tar.gz",
            },
        )(self)
        index = json.loads((ROOT / RELEASE / "SOURCE-INDEX.json").read_bytes())
        mapping = json.loads((ROOT / RELEASE / "SOURCE-MAP.json").read_bytes())
        rows = [r for r in index["files"] if "metadata_overlay" in r]
        self.assertEqual(len(rows), 3)
        for row in rows:
            overlay = row["metadata_overlay"]
            self.assertEqual(mapping[row["path"]]["metadata_overlay"], overlay)
            self.assertEqual(
                sha((ROOT / RELEASE / overlay["original_attached_path"]).read_bytes()),
                overlay["original_sha256"],
            )


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--delivery-record":
        print(
            json.dumps(
                derive_delivery_record(Path(sys.argv[2])), sort_keys=True, indent=2
            )
        )
    else:
        unittest.main()
