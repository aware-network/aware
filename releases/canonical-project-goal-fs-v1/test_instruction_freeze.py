"""Expanded instruction byte pins through original guards and retained reads."""

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(
    os.environ.get("AWARE_FREEZE_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-project-goal-fs-v1"
BASELINE = "bd046af8057cd76a5e83bc4374b9edb2243cfb07"
ENVELOPE_SHA = "edaab985f57541928effb038c825fa3af6ec6afbffda45249099a64bf1120898"
PAYLOAD_SHA = "f5b5062aeefec2db2ce660e533342ef9b0df59b9ef7a1b02661d467239da4522"
SOURCE_SHA = "b2fa5ff4b46366d20ddc086aa66b5ee05dcf27fff0ea02a4d324ef00aef3ca51"
ISSUE = "docs/issues/2026/10/20/fb-2026-10-20-project-goal-instruction-freeze-v0.md"
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
    "protocols/PROJECT-GOAL.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/canonical-project-goal-fs-v1/README.md",
)
SCOPE = {
    ISSUE,
    *CURRENT,
    "releases/SELECTED.json",
    *[
        "releases/canonical-project-goal-fs-v1/" + name
        for name in (
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
spec = importlib.util.spec_from_file_location("project_goal_instruction_binder", path)
assert spec and spec.loader
binder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binder)
owner = binder.owner
INSTRUCTIONS = (binder.INSTRUCTIONS - {"releases/canonical-a14-fs-v1/README.md"}) | {
    "releases/canonical-project-goal-fs-v1/README.md",
    "protocols/issues/OBSERVATION-INPUT.md",
    "protocols/workspace/ACTION-OBSERVATION.md",
    "protocols/EXISTING-REPOSITORY.md",
    "protocols/PROJECT-GOAL.md",
}
ORIGINAL_CURRENT = next(
    c
    for c in owner.Instructions.test_current_guidance_and_unchanged_command_blocks.__code__.co_consts
    if isinstance(c, tuple) and c[:2] == ("README.md", "protocols/WORKFLOW.md")
)


def derive_instruction_record(root):
    return binder.bind(
        binder.original().derive_instruction_record,
        {
            "releases/canonical-init-summary-fs-v1": "releases/canonical-project-goal-fs-v1",
            "canonical-init-summary-source-notice-review-v1.tar.gz": "canonical-project-goal-source-notice-review-v1.tar.gz",
            "bounded-reviewed-repository-manifest-a1": "Issue_first_independent_optional_fresh_create_first_fs_v4_separate",
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
    for module in (binder, owner):
        setattr(module, name, globals()[name])
owner.derive_instruction_record = derive_instruction_record


class Instructions(owner.Instructions):
    test_exact_pins_and_original_negative_controls = binder.bind(
        owner.Instructions.test_exact_pins_and_original_negative_controls, {19: 24}
    )
    test_exact_scope_conservation_and_issue_guard_boundary = binder.bind(
        owner.Instructions.test_exact_scope_conservation_and_issue_guard_boundary,
        {(1752, 1756, 1742): (2300, 2304, 2284)},
    )
    test_artifacts_pointer_and_historical_records_preserved = binder.bind(
        owner.Instructions.test_artifacts_pointer_and_historical_records_preserved,
        {
            "canonical-reference-fs-v1/INSTRUCTIONS.json": "canonical-project-goal-fs-v1/INSTRUCTIONS.json",
            "e43c4a7d786930d2e88888a554d81028e6e1f4560f7220225661356e0820a7ee": "19f9a769b46b4bd79aa47ead87ebc7d846c74f2f89cc2e8ed99a31348dd8dcf7",
        },
    )
    test_current_guidance_and_unchanged_command_blocks = binder.bind(
        owner.Instructions.test_current_guidance_and_unchanged_command_blocks,
        {ORIGINAL_CURRENT: CURRENT},
    )
    test_retained_installation_help_and_origins = binder.bind(
        owner.Instructions.test_retained_installation_help_and_origins,
        {
            "e43c4a7d786930d2e88888a554d81028e6e1f4560f7220225661356e0820a7ee": "19f9a769b46b4bd79aa47ead87ebc7d846c74f2f89cc2e8ed99a31348dd8dcf7",
        },
    )

    def test_current_optional_direction_and_historical_boundaries(self):
        def verify(name, body):
            text = " ".join(body.split())
            for phrase in (
                "Agent **0.2.0a16**",
                "frozen locally pending independent review",
                "public delivery is not yet authorized",
            ):
                self.assertIn(phrase, text, name)
            for phrase in (
                "exact revision above",
                "prepared, unselected Agent",
                "Instructions remain draft",
            ):
                self.assertNotIn(phrase, text, name)

        for name in CURRENT:
            body = (ROOT / name).read_text()
            verify(name, body)
            for changed in (
                body.replace("0.2.0a16", "0.2.0a15"),
                body.replace("public delivery is not yet authorized", "available now"),
                body + "\nUse the exact revision above.\n",
            ):
                with self.assertRaises(AssertionError):
                    verify(name, changed)
        for name, heading in (
            ("README.md", "## Historical a14 predecessor resource summaries"),
            ("protocols/WORKFLOW.md", "## Historical a14 predecessor summaries"),
        ):
            section = (
                (ROOT / name).read_text().split(heading, 1)[1].split("\n## ", 1)[0]
            )
            self.assertIn("08a598fdeb8f960bf30fb8e85229e820286e67be", section)
            self.assertIn("predecessor", section.lower())
        guide = " ".join((ROOT / "protocols/PROJECT-GOAL.md").read_text().split())
        for phrase in (
            "not work authority",
            "fs_v4",
            "Git",
            "not a clean matrix PASS",
            "not a clean single 34-case replay",
        ):
            self.assertIn(phrase, guide)
        observation = " ".join(
            (ROOT / "protocols/workspace/ACTION-OBSERVATION.md").read_text().split()
        )
        for phrase in (
            "exact original second-review",
            "never an apply/outcome reference",
            "not_established",
            "permission to retry",
            "unknown remains unknown",
            "incomplete retention",
        ):
            self.assertIn(phrase, observation)
        record = derive_instruction_record(ROOT)
        pointer = json.loads((ROOT / "releases/SELECTED.json").read_bytes())
        self.assertEqual(
            record["workspace_mount_profile"], pointer["workspace_mount_profile"]
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
