"""The authored-source parser must not pull the legacy Service/View graph."""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Mapping, Sequence

import pytest

import aware_goal_service_view_compat.markdown_import as legacy_markdown_import
from aware_goal_sdk.dependency_source import parse_goal_dependency_source
from aware_goal_service_view_compat.dependency_projection import project_goal_dependencies
from aware_goal_service_view_compat.markdown_import import (
    GoalMarkdownImportPlan as LegacyImportPlan,
    goal_home_view_state_from_markdown_import_plan,
)
from aware_goal_sdk.markdown_source import (
    GoalMarkdownAdmissionError,
    GoalMarkdownImportPlan,
    admit_goal_markdown_import_plan,
    parse_goal_markdown_import_plan,
)


GOAL_REF = "goal/2026-09-27/neutral-source-v0"
SOURCE_PATH = "docs/goals/2026/09/27/goal-2026-09-27-neutral-source-v0.md"
SOURCE = f"""# Goal: Neutral source

- Tag: `{GOAL_REF}`
- Status: Active

## Lane Map

| Lane | Role | Owner | Status | Current Issue | Since | Last Receipt | Scope |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `delivery` | Delivery | Unassigned | Active | TBD | TBD | TBD | Neutral |

## Lane Sequences

### `delivery`

| Step | Key | Time | Tick | Issue | Gate | Status | Owner | Receipt |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `deliver` | TBD | `[ ]` | `TBD:deliver` | Review | Planned | Unassigned | TBD |
"""
DEPENDENCY_DECLARATION = {
    "dependency_key": "deliver-requires-external",
    "dependent_lane_key": "delivery",
    "dependent_row_key": "deliver",
    "prerequisite_goal_tag": "goal/2026-09-27/external-v0",
    "prerequisite_lane_key": "review",
    "prerequisite_row_key": "accept",
    "relation": "requires_acceptance",
    "reason": "External review is required.",
}


def _with_dependencies(rows: Sequence[Mapping[str, object]]) -> str:
    return SOURCE + "\n## Dependencies\n\n```json\n" + json.dumps(rows) + "\n```\n"


def test_source_parser_is_same_type_and_value_as_legacy_import() -> None:
    plan = admit_goal_markdown_import_plan(
        SOURCE, expected_goal_ref=GOAL_REF, source_path=SOURCE_PATH
    )
    assert GoalMarkdownImportPlan is LegacyImportPlan
    assert (
        GoalMarkdownAdmissionError
        is legacy_markdown_import.__dict__["GoalMarkdownAdmissionError"]
    )
    assert plan.goal_tag == GOAL_REF
    assert plan.lane_issues[0].row_key == "deliver"
    assert goal_home_view_state_from_markdown_import_plan(plan).tag == GOAL_REF


def test_native_source_retains_issue_locations_before_provider_admission() -> None:
    issue_path = "docs/issues/2026/09/27/fb-2026-09-27-current-work.md"
    source = SOURCE.replace("| Active | TBD |", f"| Active | {issue_path} |")
    source = source.replace("`TBD:deliver`", f"`{issue_path}`")
    legacy = parse_goal_markdown_import_plan(source, source_path=SOURCE_PATH)
    assert legacy.lanes[0].current_issue_tag == "fb/2026-09-27/current-work"
    assert legacy.lane_issues[0].planned_issue_tag == "fb/2026-09-27/current-work"
    native = parse_goal_markdown_import_plan(
        source, source_path=SOURCE_PATH, preserve_issue_locations=True,
    )
    assert native.lanes[0].current_issue_tag == issue_path
    assert native.lane_issues[0].planned_issue_tag == issue_path


def test_dependency_source_preserves_declaration_without_evaluating_it() -> None:
    source = _with_dependencies([DEPENDENCY_DECLARATION])
    parsed = parse_goal_dependency_source(source, source_path=SOURCE_PATH)
    assert parsed.plan.goal_tag == GOAL_REF
    assert parsed.known_rows == {("delivery", "deliver")}
    assert (
        parsed.dependencies[0].to_wire()["dependency_key"]
        == DEPENDENCY_DECLARATION["dependency_key"]
    )
    assert not hasattr(parsed, "satisfaction")


@pytest.mark.parametrize(
    ("change", "expected_type", "expected_message"),
    [
        ({"evidence_refs": None}, ValueError, "evidence_refs must be a JSON array"),
        ({"evidence_refs": 7}, ValueError, "evidence_refs must be a JSON array"),
        ({"evidence_refs": [7]}, ValueError, "evidence_refs must be non-empty text"),
        (
            {"evidence_refs": ["proof:one", "proof:one"]},
            ValueError,
            "evidence_refs must contain unique values",
        ),
        ({"dependent_lane_key": 7}, ValueError, "dependent_lane_key must be non-empty text"),
        ({"reason": None}, ValueError, "reason must be non-empty text"),
        (
            {"relation": "not-a-relation"},
            ValueError,
            "'not-a-relation' is not a valid GoalDependencyRelation",
        ),
        (
            {"unexpected": "value"},
            TypeError,
            "GoalDependency.__init__() got an unexpected keyword argument 'unexpected'",
        ),
        (
            {"owner_goal_tag": GOAL_REF},
            ValueError,
            "owner_goal_tag is supplied by the containing Goal",
        ),
    ],
)
def test_dependency_diagnostics_match_legacy_projection(
    change: dict[str, object], expected_type: type[Exception], expected_message: str
) -> None:
    document = _with_dependencies([dict(DEPENDENCY_DECLARATION, **change)])
    for decode in (parse_goal_dependency_source, project_goal_dependencies):
        with pytest.raises(expected_type) as raised:
            _ = decode(document, source_path=SOURCE_PATH)
        assert str(raised.value) == expected_message


def test_missing_dependency_field_keeps_constructor_diagnostic() -> None:
    declaration = dict(DEPENDENCY_DECLARATION)
    del declaration["dependency_key"]
    with pytest.raises(TypeError) as raised:
        _ = parse_goal_dependency_source(
            _with_dependencies([declaration]), source_path=SOURCE_PATH
        )
    assert str(raised.value) == (
        "GoalDependency.__init__() missing 1 required positional argument: "
        "'dependency_key'"
    )


@pytest.mark.parametrize(
    "bad_source",
    [
        SOURCE.replace("- Tag: `" + GOAL_REF + "`", "- Tag: `goal/other`")
        + "\n- Tag: `" + GOAL_REF + "`\n",
        SOURCE + "\n## Dependencies\n\n```json\n[{\"relation\":\"requires_acceptance\",\"relation\":\"requires_completion\"}]\n```\n",
    ],
)
def test_neutral_source_refuses_duplicate_authority(bad_source: str) -> None:
    if "## Dependencies" in bad_source:
        with pytest.raises(ValueError, match="duplicate JSON field"):
            _ = parse_goal_dependency_source(bad_source, source_path=SOURCE_PATH)
    else:
        with pytest.raises(GoalMarkdownAdmissionError, match="goal_identity_duplicate"):
            _ = admit_goal_markdown_import_plan(
                bad_source, expected_goal_ref=GOAL_REF, source_path=SOURCE_PATH
            )


def test_neutral_import_graph_excludes_generated_and_service_packages() -> None:
    script = """
import importlib.abc
import sys

blocked = ('aware_goal_service_dto', 'aware_content_service_dto',
           'aware_goals', 'aware_experience', 'aware_service')
class Blocker(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if any(fullname == root or fullname.startswith(root + '.') for root in blocked):
            raise AssertionError('forbidden import: ' + fullname)
        return None
sys.meta_path.insert(0, Blocker())
import aware_goal_sdk.markdown_source
import aware_goal_sdk.dependency_source
import aware_goal_sdk.phase_markdown_projection
import aware_goal_sdk.native_phase_markdown
assert not any(any(name == root or name.startswith(root + '.') for root in blocked)
               for name in sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
