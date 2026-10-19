"""Observer instruction byte pins over original guards and retained reads."""

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(
    os.environ.get("AWARE_FREEZE_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-action-observer-fs-v1"
BASELINE = "0d62c3164b9b91eac98d7e8a9bcddfa5612eabe8"
ENVELOPE_SHA = "a21ef71179c055fa87e4ffde7ede35b87246deceb4a4d1039c6b7fa17e23292f"
PAYLOAD_SHA = "a2e468dfdcdd8c6b9a6d8187f3eded2db2465c3ddf15ee44309beb1cf9c97533"
SOURCE_SHA = "903ed0e0b39f29bf2614e73f25f97250eb62eb917d80ee6a00ad18063a515063"
ISSUE = "docs/issues/2026/10/20/fb-2026-10-20-canonical-action-observer-instruction-freeze-v0.md"
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
    "protocols/workspace/ACTION-OBSERVATION.md",
    "protocols/EXISTING-REPOSITORY.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/canonical-action-observer-fs-v1/README.md",
)
SCOPE = {
    ISSUE,
    *CURRENT,
    "releases/SELECTED.json",
    *[
        "releases/canonical-action-observer-fs-v1/" + n
        for n in (
            "INSTRUCTIONS.json",
            "INSTRUCTION-FREEZE.md",
            "test_instruction_freeze.py",
        )
    ],
}
path = ROOT / "releases/canonical-a14-fs-v1/test_instruction_freeze.py"
if (
    path.is_symlink()
    or hashlib.sha256(path.read_bytes()).hexdigest()
    != "0d16ba7dde8d85c089d4b64142742ed0ffba348c0b1371fd449abd40fce8801b"
):
    raise ValueError("original_instruction_helper_required")
spec = importlib.util.spec_from_file_location(
    "observer_original_instruction_checks", path
)
assert spec and spec.loader
owner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(owner)
OLD_CURRENT = owner.CURRENT
INSTRUCTIONS = (owner.INSTRUCTIONS - {"releases/canonical-a14-fs-v1/README.md"}) | {
    "releases/canonical-action-observer-fs-v1/README.md",
    "protocols/issues/OBSERVATION-INPUT.md",
    "protocols/workspace/ACTION-OBSERVATION.md",
    "protocols/EXISTING-REPOSITORY.md",
}
ORIGINAL_DERIVE = owner.derive_instruction_record


def derive_instruction_record(root):
    return owner.bind(
        ORIGINAL_DERIVE,
        {
            "releases/canonical-a14-fs-v1": "releases/canonical-action-observer-fs-v1",
            "canonical-a14-source-notice-review-v1.tar.gz": "canonical-action-observer-source-notice-review-v1.tar.gz",
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
    test_exact_pins_and_original_negative_controls = owner.bind(
        owner.Instructions.test_exact_pins_and_original_negative_controls, {20: 23}
    )
    test_exact_scope_conservation_and_issue_guard_boundary = owner.bind(
        owner.Instructions.test_exact_scope_conservation_and_issue_guard_boundary,
        {(1825, 1829, 1814): (1942, 1946, 1927)},
    )
    test_artifacts_pointer_and_historical_records_preserved = owner.bind(
        owner.Instructions.test_artifacts_pointer_and_historical_records_preserved,
        {
            "canonical-a14-fs-v1/INSTRUCTIONS.json": "canonical-action-observer-fs-v1/INSTRUCTIONS.json",
            "725ed1b5b681efdc7a6a944e96ceae6df074a8494fa065c7fd20f43b9a6b831c": "a306b52dde771bafda7cd65021c79311c7df8260e024786e2710cd243f36e68b",
        },
    )
    test_current_guidance_and_unchanged_command_blocks = owner.bind(
        owner.Instructions.test_current_guidance_and_unchanged_command_blocks,
        {OLD_CURRENT: CURRENT},
    )
    test_retained_installation_help_and_origins = owner.bind(
        owner.Instructions.test_retained_installation_help_and_origins,
        {
            "725ed1b5b681efdc7a6a944e96ceae6df074a8494fa065c7fd20f43b9a6b831c": "a306b52dde771bafda7cd65021c79311c7df8260e024786e2710cd243f36e68b",
        },
    )

    def test_current_observer_limits_and_explicit_predecessor_pins(self):
        def verify(path, body):
            text = " ".join(body.split())
            self.assertIn("Agent **0.2.0a15**", text, path)
            self.assertIn("frozen locally pending independent review", text, path)
            self.assertIn("public delivery is not yet authorized", text, path)
            self.assertNotIn("exact revision above", text, path)
            self.assertNotIn("prepared, unselected Agent", text, path)
            self.assertNotIn("Prepared/unselected instructions are draft", text, path)

        for name in CURRENT:
            body = (ROOT / name).read_text()
            verify(name, body)
            for changed in (
                body.replace("0.2.0a15", "0.2.0a14"),
                body.replace("public delivery is not yet authorized", "available now"),
                body + "\nUse the exact revision above.\n",
            ):
                with self.assertRaises(AssertionError):
                    verify(name, changed)
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
            section = (
                (ROOT / name).read_text().split(heading, 1)[1].split("\n## ", 1)[0]
            )
            self.assertIn(pin, section)
            self.assertIn("predecessor", section.lower())
        guide = " ".join(
            (ROOT / "protocols/workspace/ACTION-OBSERVATION.md").read_text().split()
        )
        for phrase in (
            "not establish whether",
            "no current admission",
            "permission to retry",
            "unknown remains unknown",
            "incomplete retention",
        ):
            self.assertIn(phrase, guide)
        adoption = " ".join(
            (ROOT / "protocols/EXISTING-REPOSITORY.md").read_text().split()
        )
        for phrase in (
            "docs/issues",
            "default, not a required",
            "not a migration command",
            "not a published or unassisted",
        ):
            self.assertIn(phrase, adoption)


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
