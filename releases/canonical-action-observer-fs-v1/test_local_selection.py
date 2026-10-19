"""Original selection derivation/conservation with exact observer coordinates."""

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(
    os.environ.get("AWARE_OBSERVER_SELECTION_ROOT", Path(__file__).resolve().parents[2])
)
BASELINE = "c1e68962fe776851686f4a1476e74a0a09846c99"
RELEASE = "releases/canonical-action-observer-fs-v1"
ISSUE = "docs/issues/2026/10/20/fb-2026-10-20-canonical-action-observer-local-selection-v0.md"
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
LAYOUT_SHA = "190f2184d1649687b9af0deb1d22b154778545f6831cc051902b723d3d114b4e"
INDEX_SHA = "903ed0e0b39f29bf2614e73f25f97250eb62eb917d80ee6a00ad18063a515063"
ENVELOPE_SHA = "a21ef71179c055fa87e4ffde7ede35b87246deceb4a4d1039c6b7fa17e23292f"
PAYLOAD_SHA = "a2e468dfdcdd8c6b9a6d8187f3eded2db2465c3ddf15ee44309beb1cf9c97533"
ROOT_OLD = """## Prepared historical action observation

Agent **0.2.0a15** is prepared and unselected; instructions remain draft.
[Historical action observation](protocols/workspace/ACTION-OBSERVATION.md)
validates original retained intent without proving completion or authorizing
retry. The proposed installer targets this successor, not the delivered a14
software. Useful work, optional SPEC and both explicit review decisions stay."""
ROOT_NEW = """## Locally selected historical action observation

Agent **0.2.0a15** is selected locally; public delivery is not yet authorized.
Instructions remain draft. Use this reviewed checkout, not unchanged public main.
The [delivery pointer](releases/SELECTED.json) binds the complete envelope;
[local selection](releases/canonical-action-observer-fs-v1/LOCAL-SELECTION.md) records its limits.
[Historical action observation](protocols/workspace/ACTION-OBSERVATION.md)
validates original intent, not completion, current admission or retry authority.
Useful work, optional SPEC and both explicit review decisions stay unchanged.
Instruction freeze and publication are separate; no automatic refresh or retry."""

path = ROOT / "releases/canonical-issue084-fs-v1/test_local_selection.py"
if (
    path.is_symlink()
    or hashlib.sha256(path.read_bytes()).hexdigest()
    != "68d257b9b9ee63d01fcfe2f04620df508bcbbe63e608014c6d9c43669e9424e7"
):
    raise ValueError("original_issue084_selection_reader_required")
spec = importlib.util.spec_from_file_location("observer_original_selection", path)
owner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(owner)
bind = owner.owner.bind


def derive_delivery_record(root):
    original = owner.owner.load(
        root / "releases/canonical-init-summary-fs-v1/test_local_selection.py",
        "04b19daa657fcb45fc7865db0cfaab77249f79177c5c553c4bc83e3d34827ba2",
        "observer_original_derivation",
    )
    original.BASELINE = BASELINE
    return bind(
        original.derive_delivery_record,
        {
            "canonical-init-summary-fs-v1": "canonical-action-observer-fs-v1",
            "canonical-init-summary-source-notice-review-v1.tar.gz": "canonical-action-observer-source-notice-review-v1.tar.gz",
            "a5006a828cf465ddd50eb219476e08292558b82dccc8d5a5838eb72a1755e6a6": LAYOUT_SHA,
            "3bfb00f7950169a6bf916f38dc1a81536b0e4a5f243ce97c79302946a64bc164": INDEX_SHA,
            "73f5038b365dcc7f193b7ebd71b77145d12fe2386311be75dcffd9afadd25df9": ENVELOPE_SHA,
            "d133ae36d78648b0f1c77652b7ab56ded7b2180620e0c023eccf9da4c2cc88e0": PAYLOAD_SHA,
        },
    )(root)


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
):
    for module in (owner, owner.owner, owner.owner.owner):
        setattr(module, name, globals()[name])
owner.owner.owner.derive_delivery_record = derive_delivery_record


class Selection(owner.Selection):
    test_exact_scope_and_conservation = bind(
        owner.Selection.test_exact_scope_and_conservation,
        {(1864, 1867, 1859): (1939, 1942, 1934)},
    )
    test_predecessor_contributor_installer_and_guides_preserved = bind(
        owner.Selection.test_predecessor_contributor_installer_and_guides_preserved,
        {
            (
                ".aware/",
                "docs/agents/",
                "protocols/",
                "releases/canonical-a14-fs-v1/",
            ): (
                ".aware/",
                "docs/agents/",
                "protocols/",
                "releases/canonical-issue084-fs-v1/",
            ),
            "canonical-a14-fs-v1": "canonical-issue084-fs-v1",
        },
    )
    test_retained_installation_reads = bind(
        owner.Selection.test_retained_installation_reads,
        {
            "9d99f4c8ddab23cfaface4c635d502c2bf463a78ffd72fe064b2b79b7a851640": "a306b52dde771bafda7cd65021c79311c7df8260e024786e2710cd243f36e68b",
        },
    )

    def test_artifacts_software_and_legal_unchanged(self):
        bind(
            owner.owner.owner.Selection.test_artifacts_software_and_legal_unchanged,
            {
                1342: 1394,
                "canonical-reference-source-notice-review-v1.tar.gz": "canonical-action-observer-source-notice-review-v1.tar.gz",
            },
        )(self)
        mapping = json.loads((ROOT / RELEASE / "SOURCE-MAP.json").read_bytes())
        supplemental = json.loads(
            (ROOT / RELEASE / "SUPPLEMENTAL-SOURCE-MAP.json").read_bytes()
        )
        overlays = json.loads(
            (ROOT / RELEASE / "source-bindings/observer-overlays.json").read_bytes()
        )["overlays"]
        self.assertEqual(len(overlays), 12)
        self.assertEqual(len(supplemental), 2)
        for row in overlays:
            target = supplemental.get(row["path"]) or mapping[row["path"]]
            self.assertEqual(
                hashlib.sha256((ROOT / target["path"]).read_bytes()).hexdigest(),
                row["after_sha256"],
            )
            if row["before_exists"]:
                self.assertEqual(
                    hashlib.sha256(
                        (ROOT / RELEASE / row["before_attached_path"]).read_bytes()
                    ).hexdigest(),
                    row["before_sha256"],
                )
            else:
                self.assertIsNone(row["before_attached_path"])


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--delivery-record":
        print(
            json.dumps(
                derive_delivery_record(Path(sys.argv[2])), sort_keys=True, indent=2
            )
        )
    else:
        import unittest

        unittest.main()
