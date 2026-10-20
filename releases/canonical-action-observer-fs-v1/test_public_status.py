"""Observer delivery wording over original conservation and retained read checks."""

import hashlib
import importlib.util
import os
from pathlib import Path

ROOT = Path(
    os.environ.get("AWARE_STATUS_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-action-observer-fs-v1"
BASELINE = "5af88a6b95b928811022e5cd0255e4bb5c77bd87"
HISTORICAL_SHA = "a7c7433f9a3e2967d7703606e329b8705dda14c200b79b1e0dca5472d8b8168f"
CURRENT = {
    "README.md",
    "protocols/WORKFLOW.md",
    "protocols/INIT.md",
    "protocols/workspace/README.md",
    "protocols/workspace/REVIEWED-SETUP.md",
    "protocols/workspace/REFERENCE-NAVIGATION.md",
    "protocols/workspace/RESOURCE-RELEASES.md",
    "protocols/issues/README.md",
    "protocols/issues/OBSERVATION-INPUT.md",
    "protocols/workspace/ACTION-OBSERVATION.md",
    "protocols/EXISTING-REPOSITORY.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/canonical-action-observer-fs-v1/README.md",
    "protocols/specification/README.md",
    "protocols/FIRST-USEFUL-TASK.md",
}
ISSUE = (
    "docs/issues/2026/10/20/fb-2026-10-20-canonical-action-observer-public-status-v0.md"
)
SCOPE = CURRENT | {
    ISSUE,
    "releases/SELECTED.json",
    *[
        "releases/canonical-action-observer-fs-v1/" + name
        for name in (
            "PUBLIC-INSTRUCTIONS.json",
            "PUBLIC-STATUS.md",
            "test_public_status.py",
        )
    ],
}
path = ROOT / "releases/canonical-a14-fs-v1/test_public_status.py"
if (
    path.is_symlink()
    or hashlib.sha256(path.read_bytes()).hexdigest()
    != "a500496873cf5a82fcf11f47c743a4213c2988a03d39e25436a058f1f52f5585"
):
    raise ValueError("original_status_or_freeze_helper_required")
spec = importlib.util.spec_from_file_location("observer_original_status", path)
assert spec and spec.loader
owner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(owner)


def freeze():
    module = owner.load(
        RELEASE / "test_instruction_freeze.py",
        "ea1e42c03b2fa5786597040c34740b61aef165b84f5f7b65de9fec6182d57d65",
    )
    module.original = module.owner.original
    return module


for name in (
    "ROOT",
    "RELEASE",
    "BASELINE",
    "HISTORICAL_SHA",
    "CURRENT",
    "ISSUE",
    "SCOPE",
    "freeze",
):
    setattr(owner, name, globals()[name])
bind = freeze().owner.bind


class PublicStatus(owner.PublicStatus):
    test_exact_pins_historical_bytes_and_negative_controls = bind(
        owner.PublicStatus.test_exact_pins_historical_bytes_and_negative_controls,
        {20: 23},
    )
    test_exact_scope_unaffected_bytes_modes_and_issue = bind(
        owner.PublicStatus.test_exact_scope_unaffected_bytes_modes_and_issue,
        {(1829, 1833, 1816): (1946, 1950, 1929)},
    )
    test_pointer_no_new_authority_and_whole_envelope = bind(
        owner.PublicStatus.test_pointer_no_new_authority_and_whole_envelope,
        {
            "canonical-a14-fs-v1/PUBLIC-INSTRUCTIONS.json": "canonical-action-observer-fs-v1/PUBLIC-INSTRUCTIONS.json",
            "canonical-a14-source-notice-review-v1.tar.gz": "canonical-action-observer-source-notice-review-v1.tar.gz",
            "050ed63545dd1d63c795285609e15dbdaa054c28788c9e5993e8a1871f356ea6": "a21ef71179c055fa87e4ffde7ede35b87246deceb4a4d1039c6b7fa17e23292f",
        },
    )
    test_command_blocks_and_evaluation_limits = bind(
        owner.PublicStatus.test_command_blocks_and_evaluation_limits,
        {
            (
                "379cd5dcbe26c256be82c760b73fc100fdfc0fc6",
                "faed3f46668a3ec111d8fbf4cf1d5a287d5e1b89",
                "not a new evaluation of a14",
            ): (
                "379cd5dcbe26c256be82c760b73fc100fdfc0fc6",
                "faed3f46668a3ec111d8fbf4cf1d5a287d5e1b89",
                "not a new evaluation of a15",
            ),
        },
    )
    test_links_and_shell_syntax = bind(
        owner.PublicStatus.test_links_and_shell_syntax,
        {
            (
                "docs/alignment/CURRENT.md",
                "releases/canonical-a14-fs-v1/PUBLIC-STATUS.md",
            ): (
                "docs/alignment/CURRENT.md",
                "releases/canonical-action-observer-fs-v1/PUBLIC-STATUS.md",
            ),
        },
    )

    def test_observer_limits_and_historical_pins_remain_explicit(self):
        for name in CURRENT:
            body = (ROOT / name).read_text()
            self.assertNotIn("exact revision above", body, name)
            self.assertIn("Agent **0.2.0a15**", body, name)
        for name, heading, pin in (
            (
                "README.md",
                "## Historical a14 predecessor resource summaries",
                "08a598fdeb8f960bf30fb8e85229e820286e67be",
            ),
            (
                "protocols/WORKFLOW.md",
                "## Historical a14 predecessor summaries",
                "08a598fdeb8f960bf30fb8e85229e820286e67be",
            ),
            (
                "README.md",
                "## Historical Issue observation input",
                "813ab2e82f7ff0fa24403c6889bf82e2c8b121fb",
            ),
        ):
            body = (ROOT / name).read_text().split(heading, 1)[1].split("\n## ", 1)[0]
            self.assertIn(pin, body)
        guide = " ".join(
            (ROOT / "protocols/workspace/ACTION-OBSERVATION.md").read_text().split()
        )
        for phrase in (
            "no current admission",
            "permission to retry",
            "unknown remains unknown",
            "incomplete retention",
            "not establish whether",
        ):
            self.assertIn(phrase, guide)
        status = (RELEASE / "PUBLIC-STATUS.md").read_text()
        for phrase in (
            "historical intent",
            "not completion",
            "not current admission",
            "not retry authority",
            "separate authorization",
        ):
            self.assertIn(phrase, status)
        adoption = " ".join(
            (ROOT / "protocols/EXISTING-REPOSITORY.md").read_text().split()
        )
        self.assertIn("default, not a required", adoption)
        self.assertIn("not a migration command", adoption)


if __name__ == "__main__":
    import unittest

    unittest.main()
