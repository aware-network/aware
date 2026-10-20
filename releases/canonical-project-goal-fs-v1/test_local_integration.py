"""Original whole-source accounting and retained reads with finite receiving."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "releases/canonical-project-goal-fs-v1"
BASELINE = "3f70fcf57e56708a1e1f8c0b52a10e2eb812da6d"
LAYOUT_SHA = "be96c99f0ccebee211cbcaf2f8b01f9dcbc466c0dc5cc4aa6c92974d0f427ad5"
ENVELOPE_SHA = "edaab985f57541928effb038c825fa3af6ec6afbffda45249099a64bf1120898"
PAYLOAD_SHA = "f5b5062aeefec2db2ce660e533342ef9b0df59b9ef7a1b02661d467239da4522"
ISSUE = "docs/issues/2026/10/20/fb-2026-10-20-project-goal-public-integration-v0.md"
EXTRAS = {
    ISSUE,
    *[
        str(RELEASE.relative_to(ROOT)) + "/" + name
        for name in (
            "LAYOUT-REVIEW.json",
            "LOCAL-INTEGRATION.md",
            "test_local_integration.py",
        )
    ],
}

# Reuse the pinned existing finite test binder and original reference methods.
import hashlib
import importlib.util

path = ROOT / "releases/canonical-a14-fs-v1/test_local_integration.py"
if (
    path.is_symlink()
    or hashlib.sha256(path.read_bytes()).hexdigest()
    != "725ed1b5b681efdc7a6a944e96ceae6df074a8494fa065c7fd20f43b9a6b831c"
):
    raise ValueError("original_accounting_binder_required")
spec = importlib.util.spec_from_file_location("goal_original_accounting", path)
assert spec and spec.loader
binder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binder)
owner = binder.owner
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
    setattr(owner, name, globals()[name])
bind = binder.bind


class Integration(owner.Integration):
    test_exact_postimages_and_modes = bind(
        owner.Integration.test_exact_postimages_and_modes, {1745: 2293}
    )
    test_baseline_and_exact_scope = bind(
        owner.Integration.test_baseline_and_exact_scope, {37: 368, 41: 372}
    )
    test_whole_envelope_and_raw_findings = bind(
        owner.Integration.test_whole_envelope_and_raw_findings,
        {
            1801: 2185,
            12: 13,
            6: 9,
            "canonical-reference-source-notice-review-v1.tar.gz": "canonical-project-goal-source-notice-review-v1.tar.gz",
        },
    )
    test_installer_four_coordinates_only = bind(
        owner.Integration.test_installer_four_coordinates_only,
        {
            "73f5038b365dcc7f193b7ebd71b77145d12fe2386311be75dcffd9afadd25df9": "a21ef71179c055fa87e4ffde7ede35b87246deceb4a4d1039c6b7fa17e23292f",
            "d133ae36d78648b0f1c77652b7ab56ded7b2180620e0c023eccf9da4c2cc88e0": "a2e468dfdcdd8c6b9a6d8187f3eded2db2465c3ddf15ee44309beb1cf9c97533",
            "canonical-reference-source-notice-review-v1.tar.gz": "canonical-project-goal-source-notice-review-v1.tar.gz",
            "canonical-init-summary-source-notice-review-v1.tar.gz": "canonical-action-observer-source-notice-review-v1.tar.gz",
            "canonical-reference-fs-v1": "canonical-project-goal-fs-v1",
            "canonical-init-summary-fs-v1": "canonical-action-observer-fs-v1",
        },
    )

    def test_complete_source_map(self):
        bind(owner.Integration.test_complete_source_map, {1342: 1698})(self)
        index = json.loads((RELEASE / "SOURCE-INDEX.json").read_bytes())
        mapping = json.loads((RELEASE / "SOURCE-MAP.json").read_bytes())
        overlays = json.loads(
            (RELEASE / "source-bindings/composite-overlays.json").read_bytes()
        )["overlays"]
        self.assertEqual(len(overlays), 22)
        for row in index["files"]:
            if "source_overlay" in row:
                self.assertEqual(
                    mapping[row["path"]]["source_overlay"], row["source_overlay"]
                )
        for row in overlays:
            self.assertEqual(
                hashlib.sha256(
                    (ROOT / mapping[row["path"]]["path"]).read_bytes()
                ).hexdigest(),
                row["after_sha256"],
            )
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
        # Every borrowed/declaration body is part of the full source index above;
        # these exact sidecars retain why it is carried without another selector.
        for name, key, count in (
            ("borrowed-modules.json", "modules", 16),
            ("workspace-declarations.json", "files", 17),
        ):
            rows = json.loads((RELEASE / "source-bindings" / name).read_bytes())[key]
            self.assertEqual(len(rows), count)
            for row in rows:
                self.assertEqual(mapping[row["path"]]["sha256"], row["sha256"])

    def test_original_retained_installation_reads(self):
        path = ROOT / "releases/canonical-init-summary-fs-v1/test_local_integration.py"
        module = binder.load(
            path,
            "ad3e35eab434e9062afbb3294d478646c2debe37fbd4ff2368a35ee8489f9a68",
            "goal_retained_reader",
        )
        module.PAYLOAD_SHA = PAYLOAD_SHA
        original = module.retained_installation_reads
        qualified = bind(
            original,
            {
                42: 49,
                153: 156,
                "build/environment": "proof/environment",
                "build/receipt.json": "proof/receipt.json",
                "build/installed-account.json": "proof/installed-account.json",
                "build/installed-origins.json": "proof/installed-origins.json",
            },
        )
        self.assertEqual(qualified.__code__.co_code, original.__code__.co_code)
        self.assertEqual(qualified.__code__.co_names, original.__code__.co_names)
        qualified(self)
