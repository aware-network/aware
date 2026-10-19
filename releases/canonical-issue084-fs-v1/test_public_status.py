"""Current delivery wording over original conservation and negative controls."""

import hashlib
import importlib.util
import os
from pathlib import Path

ROOT = Path(
    os.environ.get("AWARE_STATUS_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-issue084-fs-v1"
BASELINE = "813ab2e82f7ff0fa24403c6889bf82e2c8b121fb"
HISTORICAL_SHA = "42bd4086fbff0f08034cd88c45057b19e39079e95978a0541a63f0d20946e6f3"
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
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/canonical-issue084-fs-v1/README.md",
    "protocols/specification/README.md",
    "protocols/FIRST-USEFUL-TASK.md",
}
ISSUE = "docs/issues/2026/10/19/fb-2026-10-19-canonical-issue084-public-status-v0.md"
SCOPE = CURRENT | {
    ISSUE,
    "releases/SELECTED.json",
    "releases/canonical-issue084-fs-v1/PUBLIC-INSTRUCTIONS.json",
    "releases/canonical-issue084-fs-v1/PUBLIC-STATUS.md",
    "releases/canonical-issue084-fs-v1/test_public_status.py",
}

path = ROOT / "releases/canonical-a14-fs-v1/test_public_status.py"
if (
    path.is_symlink()
    or hashlib.sha256(path.read_bytes()).hexdigest()
    != "a500496873cf5a82fcf11f47c743a4213c2988a03d39e25436a058f1f52f5585"
):
    raise ValueError("original_status_or_freeze_helper_required")
spec = importlib.util.spec_from_file_location("issue084_original_status", path)
assert spec and spec.loader
owner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(owner)


def freeze():
    module = owner.load(
        RELEASE / "test_instruction_freeze.py",
        "cbfb140c23ae5036702f89e009227a6a2553dad15fa74a91658be8d6532c91af",
    )
    # The corrected receiver wraps a14's original helper instead of exporting
    # it. Delegate to that same immutable original for the inherited checks.
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
        {20: 21},
    )
    test_exact_scope_unaffected_bytes_modes_and_issue = bind(
        owner.PublicStatus.test_exact_scope_unaffected_bytes_modes_and_issue,
        {(1829, 1833, 1816): (1871, 1875, 1856)},
    )
    test_pointer_no_new_authority_and_whole_envelope = bind(
        owner.PublicStatus.test_pointer_no_new_authority_and_whole_envelope,
        {
            "canonical-a14-fs-v1/PUBLIC-INSTRUCTIONS.json": "canonical-issue084-fs-v1/PUBLIC-INSTRUCTIONS.json",
            "canonical-a14-source-notice-review-v1.tar.gz": "canonical-issue084-source-notice-review-v1.tar.gz",
            "050ed63545dd1d63c795285609e15dbdaa054c28788c9e5993e8a1871f356ea6": "d1326d1465a5bfbaf13293ce09e3b1a763e5ae98371f04f750fb4b81e76ebcee",
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
                "not a new evaluation of CLI 0.8.4",
            )
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
                "releases/canonical-issue084-fs-v1/PUBLIC-STATUS.md",
            )
        },
    )

    def test_historical_a14_sections_keep_their_explicit_pin(self):
        freeze().Instructions.test_historical_a14_pin_survives_current_status_replacement(
            self
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
