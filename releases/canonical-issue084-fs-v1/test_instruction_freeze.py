"""Exact current pins over original instruction checks and retained reads."""

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(
    os.environ.get("AWARE_FREEZE_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-issue084-fs-v1"
BASELINE = "3398791f531c0bbf0f2978fee7a0f52510de2826"
ENVELOPE_SHA = "d1326d1465a5bfbaf13293ce09e3b1a763e5ae98371f04f750fb4b81e76ebcee"
PAYLOAD_SHA = "f5e65fefa12ac6a778bf39e7efdffacf3a8a8b1fb261a6332a9656388ab94b5a"
SOURCE_SHA = "6c532eb4ace4df423f0f0a666742900a2ebc65919475523d4ff175dcb2d6673d"
ISSUE = (
    "docs/issues/2026/10/19/fb-2026-10-19-canonical-issue084-instruction-freeze-v0.md"
)
CURRENT = (
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
)
SCOPE = {
    ISSUE,
    *CURRENT,
    "releases/SELECTED.json",
    "releases/canonical-issue084-fs-v1/INSTRUCTIONS.json",
    "releases/canonical-issue084-fs-v1/INSTRUCTION-FREEZE.md",
    "releases/canonical-issue084-fs-v1/test_instruction_freeze.py",
}
path = ROOT / "releases/canonical-a14-fs-v1/test_instruction_freeze.py"
if (
    path.is_symlink()
    or hashlib.sha256(path.read_bytes()).hexdigest()
    != "0d16ba7dde8d85c089d4b64142742ed0ffba348c0b1371fd449abd40fce8801b"
):
    raise ValueError("original_instruction_helper_required")
spec = importlib.util.spec_from_file_location(
    "issue084_original_instruction_checks", path
)
assert spec and spec.loader
owner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(owner)
OLD_CURRENT = owner.CURRENT
INSTRUCTIONS = (owner.INSTRUCTIONS - {"releases/canonical-a14-fs-v1/README.md"}) | {
    "releases/canonical-issue084-fs-v1/README.md",
    "protocols/issues/OBSERVATION-INPUT.md",
}
ORIGINAL_DERIVE = owner.derive_instruction_record


def derive_instruction_record(root):
    return owner.bind(
        ORIGINAL_DERIVE,
        {
            "releases/canonical-a14-fs-v1": "releases/canonical-issue084-fs-v1",
            "canonical-a14-source-notice-review-v1.tar.gz": "canonical-issue084-source-notice-review-v1.tar.gz",
        },
    )(root)


for name in (
    "ROOT",
    "RELEASE",
    "BASELINE",
    "ENVELOPE_SHA",
    "PAYLOAD_SHA",
    "SOURCE_SHA",
    "ISSUE",
    "INSTRUCTIONS",
    "SCOPE",
    "CURRENT",
):
    setattr(owner, name, globals()[name])
    setattr(owner.owner, name, globals()[name])
owner.owner.derive_instruction_record = derive_instruction_record


class Instructions(owner.Instructions):
    def test_historical_a14_pin_survives_current_status_replacement(self):
        historical_pin = "08a598fdeb8f960bf30fb8e85229e820286e67be"

        def assert_historical_section(body, heading):
            self.assertEqual(body.count(heading), 1)
            section = body.split(heading, 1)[1].split("\n## ", 1)[0]
            self.assertIn(historical_pin, section)
            self.assertIn("predecessor", section.lower())
            self.assertNotIn("exact revision above", section)
            self.assertNotIn("Current a14", section)

        for path, heading, old_heading in (
            (
                "README.md",
                "## Historical a14 predecessor resource summaries",
                "## Delivered a14 resource summaries",
            ),
            (
                "protocols/WORKFLOW.md",
                "## Historical a14 predecessor summaries",
                "## Delivered a14 summaries",
            ),
        ):
            body = (ROOT / path).read_text()
            assert_historical_section(body, heading)
            # Other historical occurrences elsewhere must not hide a missing
            # pin in this section after the current introduction is replaced.
            prefix, section = body.split(heading, 1)
            with self.assertRaises(AssertionError):
                assert_historical_section(
                    prefix + heading + section.replace(historical_pin, ""), heading
                )
            before = owner.owner.git("show", BASELINE + ":" + path).decode()
            old_section = before.split(old_heading, 1)[1].split("\n## ", 1)[0]
            self.assertIn("exact revision above", old_section)
            self.assertNotIn(historical_pin, old_section)
            with self.assertRaises(AssertionError):
                assert_historical_section(heading + old_section, heading)

    test_exact_pins_and_original_negative_controls = owner.bind(
        owner.Instructions.test_exact_pins_and_original_negative_controls, {20: 21}
    )
    test_exact_scope_conservation_and_issue_guard_boundary = owner.bind(
        owner.Instructions.test_exact_scope_conservation_and_issue_guard_boundary,
        {(1825, 1829, 1814): (1867, 1871, 1854)},
    )
    test_artifacts_pointer_and_historical_records_preserved = owner.bind(
        owner.Instructions.test_artifacts_pointer_and_historical_records_preserved,
        {
            "canonical-a14-fs-v1/INSTRUCTIONS.json": "canonical-issue084-fs-v1/INSTRUCTIONS.json",
            "725ed1b5b681efdc7a6a944e96ceae6df074a8494fa065c7fd20f43b9a6b831c": "9d99f4c8ddab23cfaface4c635d502c2bf463a78ffd72fe064b2b79b7a851640",
        },
    )
    test_current_guidance_and_unchanged_command_blocks = owner.bind(
        owner.Instructions.test_current_guidance_and_unchanged_command_blocks,
        {OLD_CURRENT: CURRENT},
    )
    test_retained_installation_help_and_origins = owner.bind(
        owner.Instructions.test_retained_installation_help_and_origins,
        {
            "725ed1b5b681efdc7a6a944e96ceae6df074a8494fa065c7fd20f43b9a6b831c": "9d99f4c8ddab23cfaface4c635d502c2bf463a78ffd72fe064b2b79b7a851640",
        },
    )


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--instruction-record":
        print(
            json.dumps(
                derive_instruction_record(Path(sys.argv[2])), sort_keys=True, indent=2
            )
        )
    else:
        import unittest

        unittest.main()
