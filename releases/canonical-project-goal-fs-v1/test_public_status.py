"""Current-delivery pins over original conservation and retained-read owners."""

import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path

ROOT = Path(
    os.environ.get("AWARE_STATUS_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-project-goal-fs-v1"
BASELINE = "704b5943931fcac23bcc748a574e112d20884017"
HISTORICAL_SHA = "8c5266131f0a176373fe17fc1d35967d8e3e8644ef3f056cd8e456716284833d"
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
    "protocols/PROJECT-GOAL.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/canonical-project-goal-fs-v1/README.md",
    "protocols/specification/README.md",
    "protocols/FIRST-USEFUL-TASK.md",
}
ISSUE = "docs/issues/2026/10/20/fb-2026-10-20-project-goal-public-status-v0.md"
SCOPE = CURRENT | {
    ISSUE,
    "releases/SELECTED.json",
    *[
        "releases/canonical-project-goal-fs-v1/" + name
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
    raise ValueError("original_status_owner_required")
spec = importlib.util.spec_from_file_location("project_goal_original_status", path)
assert spec and spec.loader
owner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(owner)


def freeze():
    module = owner.load(
        RELEASE / "test_instruction_freeze.py",
        "4201267a77f405be3609f1716eca05a7f823dada2c3ce7526bb85deb5bac03f5",
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
bind = freeze().binder.bind


class PublicStatus(owner.PublicStatus):
    test_exact_pins_historical_bytes_and_negative_controls = bind(
        owner.PublicStatus.test_exact_pins_historical_bytes_and_negative_controls,
        {20: 24},
    )
    test_exact_scope_unaffected_bytes_modes_and_issue = bind(
        owner.PublicStatus.test_exact_scope_unaffected_bytes_modes_and_issue,
        {(1829, 1833, 1816): (2304, 2308, 2286)},
    )
    test_pointer_no_new_authority_and_whole_envelope = bind(
        owner.PublicStatus.test_pointer_no_new_authority_and_whole_envelope,
        {
            "canonical-a14-fs-v1/PUBLIC-INSTRUCTIONS.json": "canonical-project-goal-fs-v1/PUBLIC-INSTRUCTIONS.json",
            "canonical-a14-source-notice-review-v1.tar.gz": "canonical-project-goal-source-notice-review-v1.tar.gz",
            "050ed63545dd1d63c795285609e15dbdaa054c28788c9e5993e8a1871f356ea6": "edaab985f57541928effb038c825fa3af6ec6afbffda45249099a64bf1120898",
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
                "releases/canonical-project-goal-fs-v1/PUBLIC-STATUS.md",
            )
        },
    )

    def test_command_blocks_and_evaluation_limits(self):
        record = json.loads((RELEASE / "PUBLIC-INSTRUCTIONS.json").read_bytes())
        for name in record["files"]:
            before = owner.git("show", BASELINE + ":" + name)
            body = (ROOT / name).read_bytes()
            if name.endswith((".py", ".json")):
                self.assertEqual(body, before, name)
            else:
                blocks = lambda b: re.findall(
                    rb"```(?:sh|bash|python)\n(.*?)```", b, re.DOTALL
                )
                self.assertEqual(blocks(body), blocks(before), name)
        task = (ROOT / "protocols/FIRST-USEFUL-TASK.md").read_text()
        for phrase in (
            "379cd5dcbe26c256be82c760b73fc100fdfc0fc6",
            "faed3f46668a3ec111d8fbf4cf1d5a287d5e1b89",
            "not a new evaluation of a16",
        ):
            self.assertIn(phrase, task)
        status = (RELEASE / "PUBLIC-STATUS.md").read_text()
        for phrase in (
            "manual Issue guards",
            "not a new U/V/R",
            "not a live remote-status assertion",
            "Whole-envelope delivery remains required",
            "No additional public push",
            "unknowns",
            "not a clean matrix PASS",
            "not a clean single34-case replay",
        ):
            self.assertIn(phrase, status)

    def test_direction_observation_and_explicit_historical_pins(self):
        for name, heading in (
            ("README.md", "## Historical a14 predecessor resource summaries"),
            ("protocols/WORKFLOW.md", "## Historical a14 predecessor summaries"),
        ):
            section = (
                (ROOT / name).read_text().split(heading, 1)[1].split("\n## ", 1)[0]
            )
            self.assertIn("08a598fdeb8f960bf30fb8e85229e820286e67be", section)
        for name in CURRENT:
            self.assertNotIn("exact revision above", (ROOT / name).read_text(), name)
        goal = " ".join((ROOT / "protocols/PROJECT-GOAL.md").read_text().split())
        for phrase in (
            "not work authority",
            "fs_v4",
            "Git",
            "not a clean matrix PASS",
            "not a clean single 34-case replay",
        ):
            self.assertIn(phrase, goal)
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


if __name__ == "__main__":
    import unittest

    unittest.main()
