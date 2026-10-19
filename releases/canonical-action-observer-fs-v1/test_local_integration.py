"""Current observer provenance over original accounting and retained-read methods.

Metadata-only source-map assertions are explicitly superseded by twelve-overlay
and supplemental-declaration assertions; original whole-source checks remain.
"""

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "releases/canonical-action-observer-fs-v1"
BASELINE = "dbdc57d0523082e51f0c830b47ddb523c45de26c"
LAYOUT_SHA = "190f2184d1649687b9af0deb1d22b154778545f6831cc051902b723d3d114b4e"
ENVELOPE_SHA = "a21ef71179c055fa87e4ffde7ede35b87246deceb4a4d1039c6b7fa17e23292f"
PAYLOAD_SHA = "a2e468dfdcdd8c6b9a6d8187f3eded2db2465c3ddf15ee44309beb1cf9c97533"
ISSUE = "docs/issues/2026/10/20/fb-2026-10-20-canonical-action-observer-public-integration-v0.md"
EXTRAS = {
    ISSUE,
    *[
        str(RELEASE.relative_to(ROOT)) + "/" + n
        for n in (
            "LAYOUT-REVIEW.json",
            "LOCAL-INTEGRATION.md",
            "test_local_integration.py",
        )
    ],
}

path = ROOT / "releases/canonical-issue084-fs-v1/test_local_integration.py"
if (
    path.is_symlink()
    or hashlib.sha256(path.read_bytes()).hexdigest()
    != "9d99f4c8ddab23cfaface4c635d502c2bf463a78ffd72fe064b2b79b7a851640"
):
    raise ValueError("original_issue084_accounting_required")
spec = importlib.util.spec_from_file_location("observer_original_accounting", path)
owner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(owner)
for name in (
    "ROOT",
    "RELEASE",
    "BASELINE",
    "LAYOUT_SHA",
    "ENVELOPE_SHA",
    "PAYLOAD_SHA",
    "ISSUE",
    "EXTRAS",
):
    for module in (owner, owner.owner, owner.owner.owner):
        setattr(module, name, globals()[name])
bind = owner.owner.bind


class Integration(owner.Integration):
    test_exact_postimages_and_modes = bind(
        owner.Integration.test_exact_postimages_and_modes, {1860: 1935}
    )
    test_baseline_and_exact_scope = bind(
        owner.Integration.test_baseline_and_exact_scope, {38: 84, 42: 88}
    )
    test_whole_envelope_and_raw_findings = bind(
        owner.Integration.test_whole_envelope_and_raw_findings,
        {
            1837: 1867,
            "canonical-issue084-source-notice-review-v1.tar.gz": "canonical-action-observer-source-notice-review-v1.tar.gz",
        },
    )
    test_installer_four_coordinates_only = bind(
        owner.Integration.test_installer_four_coordinates_only,
        {
            "050ed63545dd1d63c795285609e15dbdaa054c28788c9e5993e8a1871f356ea6": "d1326d1465a5bfbaf13293ce09e3b1a763e5ae98371f04f750fb4b81e76ebcee",
            "4d1bf3b5ab43e904d463ba307840cf681889339d7197b089083add866d692c58": "f5e65fefa12ac6a778bf39e7efdffacf3a8a8b1fb261a6332a9656388ab94b5a",
            "canonical-issue084-source-notice-review-v1.tar.gz": "canonical-action-observer-source-notice-review-v1.tar.gz",
            "canonical-a14-source-notice-review-v1.tar.gz": "canonical-issue084-source-notice-review-v1.tar.gz",
            "canonical-issue084-fs-v1": "canonical-action-observer-fs-v1",
            "canonical-a14-fs-v1": "canonical-issue084-fs-v1",
        },
    )

    def test_complete_source_map(self):
        # Original reference method checks every mapped source body, profile and
        # absence of a second previews tree. Keep that code intact apart from count.
        bind(owner.owner.owner.Integration.test_complete_source_map, {1342: 1394})(self)
        index = json.loads((RELEASE / "SOURCE-INDEX.json").read_bytes())
        mapping = json.loads((RELEASE / "SOURCE-MAP.json").read_bytes())
        supplemental = json.loads(
            (RELEASE / "SUPPLEMENTAL-SOURCE-MAP.json").read_bytes()
        )
        overlays = json.loads(
            (RELEASE / "source-bindings/observer-overlays.json").read_bytes()
        )["overlays"]
        self.assertEqual(len(overlays), 12)
        self.assertEqual(len(supplemental), 2)
        self.assertEqual(sum(r["before_exists"] for r in overlays), 11)
        self.assertEqual(
            sum(r["metadata_overlay_revision"] is not None for r in overlays), 3
        )
        for row in index["files"]:
            if "source_overlay" in row:
                self.assertEqual(
                    mapping[row["path"]]["source_overlay"], row["source_overlay"]
                )
        for row in overlays:
            target = supplemental.get(row["path"]) or mapping[row["path"]]
            self.assertEqual(
                hashlib.sha256((ROOT / target["path"]).read_bytes()).hexdigest(),
                row["after_sha256"],
            )
            if row["path"] in supplemental:
                self.assertFalse(target["selector_member"])
            if row["before_exists"]:
                self.assertEqual(
                    hashlib.sha256(
                        (RELEASE / row["before_attached_path"]).read_bytes()
                    ).hexdigest(),
                    row["before_sha256"],
                )
            else:
                self.assertIsNone(row["before_attached_path"])
                self.assertIsNone(row["before_sha256"])
