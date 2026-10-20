from __future__ import annotations

import pytest
from aware_goal_service_view_compat.markdown_import import (
    GoalMarkdownAdmissionError,
    admit_goal_markdown_import_plan,
    goal_home_view_state_from_markdown_import_plan,
    parse_goal_markdown_import_plan,
)

GOAL_REF = "goal/2026-09-20/example"
SOURCE_PATH = "docs/goals/2026/09/20/goal-2026-09-20-example.md"


def _markdown(*, tag: str | None = GOAL_REF, key: str = "implementation") -> str:
    tag_line = "" if tag is None else f"- Tag: `{tag}`\n"
    return f"""# Goal: Example

{tag_line}- Status: Active
- Priority: P1

## Lane Map

| Lane | Role | Owner | Status | Current Issue | Since | Last Receipt | Scope |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `delivery` | Delivery | Unassigned | Active | TBD | TBD | TBD | Example |

## Lane Sequences

### `delivery`

| Step | Key | Time | Tick | Issue | Gate | Status | Owner | Receipt |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `{key}` | TBD | `[ ]` | `TBD:implementation` | Ship it | Planned | Unassigned | TBD |
"""


def test_strict_admission_accepts_explicit_canonical_identity() -> None:
    plan = admit_goal_markdown_import_plan(
        _markdown(),
        expected_goal_ref=GOAL_REF,
        source_path=SOURCE_PATH,
    )

    view = goal_home_view_state_from_markdown_import_plan(plan)
    assert view.tag == GOAL_REF
    assert view.provenance["source_kind"] == "markdown_seed"
    assert view.provenance["service_resolved"] is False


@pytest.mark.parametrize(
    ("markdown", "diagnostic"),
    [
        (_markdown(tag=None), "goal_identity_missing"),
        (_markdown(tag="goal/2026-09-20/other"), "goal_identity_mismatch"),
        (_markdown(key=""), "goal_lane_issue_key_missing:delivery"),
        (_markdown().replace("| Ship it |", "|  |"), "goal_lane_issue_gate_missing"),
    ],
)
def test_strict_admission_rejects_compatibility_repairs(
    markdown: str, diagnostic: str
) -> None:
    with pytest.raises(GoalMarkdownAdmissionError) as raised:
        admit_goal_markdown_import_plan(
            markdown,
            expected_goal_ref=GOAL_REF,
            source_path=SOURCE_PATH,
        )

    assert any(item.startswith(diagnostic) for item in raised.value.diagnostics)


def test_nonstructural_edit_preserves_correlation_but_changes_snapshot_ids() -> None:
    before = admit_goal_markdown_import_plan(
        _markdown(), expected_goal_ref=GOAL_REF, source_path=SOURCE_PATH
    )
    after = admit_goal_markdown_import_plan(
        _markdown() + "\nA nonstructural note.\n",
        expected_goal_ref=GOAL_REF,
        source_path=SOURCE_PATH,
    )
    before_view = goal_home_view_state_from_markdown_import_plan(before)
    after_view = goal_home_view_state_from_markdown_import_plan(after)

    assert before_view.tag == after_view.tag == GOAL_REF
    assert before_view.lanes[0].lane_key == after_view.lanes[0].lane_key == "delivery"
    assert before_view.lanes[0].issues[0].row_key == "implementation"
    assert after_view.lanes[0].issues[0].row_key == "implementation"
    assert before.source_sha256 != after.source_sha256
    assert before_view.goal_id != after_view.goal_id
    assert before_view.lanes[0].goal_lane_id != after_view.lanes[0].goal_lane_id


def test_noncontiguous_step_is_importable_but_not_canonical_authority() -> None:
    markdown = _markdown().replace("| 1 | `implementation`", "| 2 | `implementation`")

    assert parse_goal_markdown_import_plan(markdown, source_path=SOURCE_PATH).goal_tag == GOAL_REF
    with pytest.raises(GoalMarkdownAdmissionError) as raised:
        admit_goal_markdown_import_plan(
            markdown, expected_goal_ref=GOAL_REF, source_path=SOURCE_PATH
        )

    assert raised.value.diagnostics == (
        "goal_lane_issue_step_noncontiguous:delivery:implementation:expected_1:actual_2",
    )
