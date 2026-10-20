"""Original selection derivation/conservation, exact expanded coordinates."""

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(
    os.environ.get(
        "AWARE_PROJECT_GOAL_SELECTION_ROOT", Path(__file__).resolve().parents[2]
    )
)
BASELINE = "0ecaece70f15a1187abcb1de03f96f26bbb590e0"
RELEASE = "releases/canonical-project-goal-fs-v1"
ISSUE = "docs/issues/2026/10/20/fb-2026-10-20-project-goal-local-selection-v0.md"
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
LAYOUT_SHA = "be96c99f0ccebee211cbcaf2f8b01f9dcbc466c0dc5cc4aa6c92974d0f427ad5"
INDEX_SHA = "b2fa5ff4b46366d20ddc086aa66b5ee05dcf27fff0ea02a4d324ef00aef3ca51"
ENVELOPE_SHA = "edaab985f57541928effb038c825fa3af6ec6afbffda45249099a64bf1120898"
PAYLOAD_SHA = "f5b5062aeefec2db2ce660e533342ef9b0df59b9ef7a1b02661d467239da4522"
ROOT_OLD = """# Aware

Draft instructions for prepared, unselected Agent a16; not public availability.

Coherent work between agents in your Git repository.

Aware helps an agent make a bounded change and leave evidence another execution
can review and lawfully continue. Issues coordinate the work; a Specification
draft is optional when the task needs shared intent. The agent still implements
and tests the customer's change. Aware is not a sandbox or an application
correctness checker, and coherence is not a promise of faster agents.

## Complete something useful

Start with a small customer-approved outcome: a bug fix, a read-only tool or a
tested improvement to an owned repository. Follow
[your first useful task](protocols/FIRST-USEFUL-TASK.md). A starter
[JSON-checker task](protocols/tasks/JSON-CHECKER.md) gives explicit acceptance
criteria, not a prewritten implementation or mandatory task.

Today's path is **Issue → optional SPEC → bounded work → verification → local
publication and closeout**. A generated manifest is setup, not completion of the
customer's application. Optional prepared Project/Goal direction is a separate fresh-repository branch.
Language/Meta elevation remains parallel; neither is a prerequisite for this path.

## Prepared optional Project/Goal and original-intent presentation

Agent **0.2.0a16** / Issue CLI **0.8.4**, 49 payload distributions, is prepared
and unselected. Instructions are draft, not public availability. Start with
[useful customer code](protocols/FIRST-USEFUL-TASK.md); Issue-first and optional
SPEC remain independent. For a fresh repository only, see the separate
[optional Project/Goal branch](protocols/PROJECT-GOAL.md). It creates direction,
not work authority, and does not provide Goal-to-Issue, decomposition or RUN.

The delivered predecessor is Agent a15 at
`5af88a6b95b928811022e5cd0255e4bb5c77bd87`; local wording baseline is
`3f70fcf57e56708a1e1f8c0b52a10e2eb812da6d`. This private proposal does not replace that published evidence.
The proposed installer targets this successor and retains its entire envelope.
Selection, instruction freeze, publication and new client trials are separate."""
ROOT_NEW = """# Aware

Draft instructions for locally selected Agent a16; public delivery is not yet authorized.

Coherent work between agents in your Git repository.

Aware helps an agent make a bounded change and leave evidence another execution
can review and lawfully continue. Issues coordinate the work; a Specification
draft is optional when the task needs shared intent. The agent still implements
and tests the customer's change. Aware is not a sandbox or an application
correctness checker, and coherence is not a promise of faster agents.

## Complete something useful

Start with a small customer-approved outcome: a bug fix, a read-only tool or a
tested improvement to an owned repository. Follow
[your first useful task](protocols/FIRST-USEFUL-TASK.md). A starter
[JSON-checker task](protocols/tasks/JSON-CHECKER.md) gives explicit acceptance
criteria, not a prewritten implementation or mandatory task.

Today's path is **Issue → optional SPEC → bounded work → verification → local
publication and closeout**. A generated manifest is setup, not completion of the
customer's application. Optional locally selected Project/Goal direction is a separate fresh-repository branch.
Language/Meta elevation remains parallel; neither is a prerequisite for this path.

## Locally selected optional Project/Goal and original-intent presentation

Agent **0.2.0a16** / Issue CLI **0.8.4**, 49 payload distributions, is selected locally;
public delivery is not yet authorized. Instructions remain draft. Start with
[useful customer code](protocols/FIRST-USEFUL-TASK.md); Issue-first and optional
SPEC remain independent. For a fresh repository only, see the separate
[optional Project/Goal branch](protocols/PROJECT-GOAL.md). It creates direction,
not work authority, and does not provide Goal-to-Issue, decomposition or RUN.

The delivered predecessor is Agent a15 at
`5af88a6b95b928811022e5cd0255e4bb5c77bd87`; local wording baseline is
`3f70fcf57e56708a1e1f8c0b52a10e2eb812da6d`. This private proposal does not replace that published evidence.
The proposed installer targets this successor and retains its entire envelope.
The [delivery pointer](releases/SELECTED.json) binds the complete envelope;
[local selection](releases/canonical-project-goal-fs-v1/LOCAL-SELECTION.md) records its limits.
Instruction freeze, publication and new client trials remain separate."""

path = ROOT / "releases/canonical-a14-fs-v1/test_local_selection.py"
if (
    path.is_symlink()
    or hashlib.sha256(path.read_bytes()).hexdigest()
    != "45a4a2b5c913ad8339d4ee78028b2f33cb359c8c9e40603da2f93074e62970f7"
):
    raise ValueError("original_selection_reader_required")
spec = importlib.util.spec_from_file_location("project_goal_selection_binder", path)
assert spec and spec.loader
binder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binder)
owner = binder.owner
bind = binder.bind


def derive_delivery_record(root):
    original = binder.load(
        root / "releases/canonical-init-summary-fs-v1/test_local_selection.py",
        "04b19daa657fcb45fc7865db0cfaab77249f79177c5c553c4bc83e3d34827ba2",
        "project_goal_original_derivation",
    )
    original.BASELINE = BASELINE
    return bind(
        original.derive_delivery_record,
        {
            "canonical-init-summary-fs-v1": "canonical-project-goal-fs-v1",
            "canonical-init-summary-source-notice-review-v1.tar.gz": "canonical-project-goal-source-notice-review-v1.tar.gz",
            "a5006a828cf465ddd50eb219476e08292558b82dccc8d5a5838eb72a1755e6a6": LAYOUT_SHA,
            "3bfb00f7950169a6bf916f38dc1a81536b0e4a5f243ce97c79302946a64bc164": INDEX_SHA,
            "73f5038b365dcc7f193b7ebd71b77145d12fe2386311be75dcffd9afadd25df9": ENVELOPE_SHA,
            "d133ae36d78648b0f1c77652b7ab56ded7b2180620e0c023eccf9da4c2cc88e0": PAYLOAD_SHA,
            "bounded-reviewed-repository-manifest-a1": "Issue_first_independent_optional_fresh_create_first_fs_v4_separate",
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
    "derive_delivery_record",
):
    setattr(owner, name, globals()[name])


class Selection(owner.Selection):
    test_exact_scope_and_conservation = bind(
        owner.Selection.test_exact_scope_and_conservation,
        {(1749, 1752, 1744): (2297, 2300, 2292)},
    )
    test_predecessor_contributor_installer_and_guides_preserved = bind(
        owner.Selection.test_predecessor_contributor_installer_and_guides_preserved,
        {
            (
                ".aware/",
                "docs/agents/",
                "protocols/",
                "releases/canonical-init-summary-fs-v1/",
            ): (
                ".aware/",
                "docs/agents/",
                "protocols/",
                "releases/canonical-action-observer-fs-v1/",
            ),
            "canonical-init-summary-fs-v1": "canonical-action-observer-fs-v1",
        },
    )
    test_retained_installation_reads = bind(
        owner.Selection.test_retained_installation_reads,
        {
            "e43c4a7d786930d2e88888a554d81028e6e1f4560f7220225661356e0820a7ee": "19f9a769b46b4bd79aa47ead87ebc7d846c74f2f89cc2e8ed99a31348dd8dcf7",
        },
    )
    test_artifacts_software_and_legal_unchanged = bind(
        owner.Selection.test_artifacts_software_and_legal_unchanged,
        {
            1342: 1698,
            6: 9,
            (12, "not_granted"): (13, "not_granted"),
            "canonical-reference-source-notice-review-v1.tar.gz": "canonical-project-goal-source-notice-review-v1.tar.gz",
        },
    )


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
