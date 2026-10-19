"""Finite Issue CLI 0.8.4 coordinates over original accounting/retained reads."""

import hashlib
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "releases/canonical-issue084-fs-v1"
BASELINE = "54252d539ded2ad35b33720ad58d1b9be4e5fb6e"
LAYOUT_SHA = "d22712a18b175971d4064231ee1a277770a3804c1f803bd398015f30409aaa09"
ENVELOPE_SHA = "d1326d1465a5bfbaf13293ce09e3b1a763e5ae98371f04f750fb4b81e76ebcee"
PAYLOAD_SHA = "f5e65fefa12ac6a778bf39e7efdffacf3a8a8b1fb261a6332a9656388ab94b5a"
ISSUE = (
    "docs/issues/2026/10/19/fb-2026-10-19-canonical-issue084-public-integration-v0.md"
)
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

path = ROOT / "releases/canonical-a14-fs-v1/test_local_integration.py"
if (
    path.is_symlink()
    or hashlib.sha256(path.read_bytes()).hexdigest()
    != "725ed1b5b681efdc7a6a944e96ceae6df074a8494fa065c7fd20f43b9a6b831c"
):
    raise ValueError("original_overlay_accounting_tests_required")
spec = importlib.util.spec_from_file_location(
    "issue084_original_integration_tests", path
)
assert spec and spec.loader
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
    setattr(owner, name, globals()[name])
    setattr(owner.owner, name, globals()[name])


class Integration(owner.Integration):
    test_exact_postimages_and_modes = owner.bind(
        owner.Integration.test_exact_postimages_and_modes, {1818: 1860}
    )
    test_baseline_and_exact_scope = owner.bind(
        owner.Integration.test_baseline_and_exact_scope, {97: 38, 101: 42}
    )
    test_complete_source_map = owner.bind(
        owner.Integration.test_complete_source_map, {1372: 1374}
    )
    test_whole_envelope_and_raw_findings = owner.bind(
        owner.Integration.test_whole_envelope_and_raw_findings,
        {
            1835: 1837,
            "canonical-a14-source-notice-review-v1.tar.gz": "canonical-issue084-source-notice-review-v1.tar.gz",
        },
    )
    test_installer_four_coordinates_only = owner.bind(
        owner.Integration.test_installer_four_coordinates_only,
        {
            "afca86cad0fe96c40250819a37b3ab7284236b30d12db919e6596c2aae6a9d30": "050ed63545dd1d63c795285609e15dbdaa054c28788c9e5993e8a1871f356ea6",
            "8c804765c0aae2ee8ffe72768158867eab29dae93c669ec6c259421103eaf0e8": "4d1bf3b5ab43e904d463ba307840cf681889339d7197b089083add866d692c58",
            "canonical-a14-source-notice-review-v1.tar.gz": "canonical-issue084-source-notice-review-v1.tar.gz",
            "canonical-reference-source-notice-review-v1.tar.gz": "canonical-a14-source-notice-review-v1.tar.gz",
            "canonical-a14-fs-v1": "canonical-issue084-fs-v1",
            "canonical-reference-fs-v1": "canonical-a14-fs-v1",
        },
    )
    test_original_retained_installation_reads = owner.bind(
        owner.Integration.test_original_retained_installation_reads, {155: 156}
    )
