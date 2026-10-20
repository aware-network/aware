from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pytest
from _goal_sdk_public_test_paths import (
    AWARE_GOALS_LANGUAGE_ROOT,
    GOAL_SERVICE_DTO_ROOT,
    PUBLIC_SDK_ROOT,
    REPO_ROOT,
    WORKFLOW_MODULE_ROOT,
)

GOAL_OPERATIONAL_RUNTIME_ROOT = (
    WORKFLOW_MODULE_ROOT / "libs" / "goal_operational_runtime"
)

for _path in (
    PUBLIC_SDK_ROOT,
    GOAL_OPERATIONAL_RUNTIME_ROOT,
    GOAL_SERVICE_DTO_ROOT,
    AWARE_GOALS_LANGUAGE_ROOT,
):
    _path_str = str(_path.resolve())
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from aware_goal_sdk import (
    GOAL_PHASE_MARKDOWN_AUTHORITY_PROFILE,
    GoalLegacyPhaseProjectionV1,
    GoalPhaseMarkdownProjectionError,
    load_goal_phase_markdown_projection,
    parse_goal_markdown_import_plan,
    project_goal_phase_markdown,
    render_goal_phase_markdown_v1,
    render_goal_phase_markdown_v2,
)

ACTORWORLD_GOAL = REPO_ROOT / (
    "docs/goals/2026/09/10/goal-2026-09-10-actorworld-ux-ax-runtime-convergence-v0.md"
)
SHARED_GOAL = REPO_ROOT / (
    "docs/goals/2026/09/12/"
    "goal-2026-09-12-goal-operational-shared-work-convergence-v0.md"
)


def test_legacy_closed_row_never_becomes_native_phase_acceptance() -> None:
    markdown = """# Goal: Compatibility proof

- Tag: `goal/compatibility-proof`

## Lane Sequences

### operational-runtime

| Step | Key | Tick | Status | Gate | Issue | Owner | Receipt |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | accepted-looking-row | [x] | Closed | Exact gate text | docs/issues/closed.md | codex-owner | issue-close:abc |
"""
    projection = project_goal_phase_markdown(markdown)
    phase = projection.phases[0]

    assert phase.phase_key == "accepted-looking-row"
    assert phase.coordinate.phase_key == "accepted-looking-row"
    assert phase.legacy_status_snapshot == "Closed"
    assert phase.native_phase_state is None
    assert phase.gate_observation is None
    assert phase.acceptance_receipt_ref is None
    assert phase.work_association.admitted_at is None
    assert phase.work_association.receipt_snapshot == "issue-close:abc"
    assert phase.gate.gate_contract_ref.endswith("legacy_text_v1")
    assert projection.authority_profile == GOAL_PHASE_MARKDOWN_AUTHORITY_PROFILE


def test_v1_is_byte_exact_and_v2_is_deterministic() -> None:
    source_bytes = ACTORWORLD_GOAL.read_bytes()
    source = source_bytes.decode("utf-8")
    projection = load_goal_phase_markdown_projection(ACTORWORLD_GOAL)

    assert render_goal_phase_markdown_v1(projection) == source
    assert render_goal_phase_markdown_v1(projection).encode("utf-8") == source_bytes
    assert render_goal_phase_markdown_v2(projection) == render_goal_phase_markdown_v2(
        projection
    )
    rendered = render_goal_phase_markdown_v2(projection)
    assert "Native Phase Authority: `unavailable`" in rendered
    assert "not_evaluated | unavailable" in rendered


def test_real_goal_canaries_preserve_every_parsed_coordinate() -> None:
    for path in (ACTORWORLD_GOAL, SHARED_GOAL):
        source = path.read_text(encoding="utf-8")
        legacy_plan = parse_goal_markdown_import_plan(
            source, source_path=path.as_posix()
        )
        projection = load_goal_phase_markdown_projection(path)
        coordinates = [
            (phase.coordinate.lane_key, phase.coordinate.phase_key)
            for phase in projection.phases
        ]
        expected_coordinates = [
            (row.lane_key, row.row_key) for row in legacy_plan.lane_issues
        ]
        assert set(coordinates) == set(expected_coordinates)
        assert len(coordinates) == len(expected_coordinates)
        assert len(set(coordinates)) == len(expected_coordinates)
        assert all(phase.ordinal >= 1 for phase in projection.phases)
        assert all(phase.gate_observation is None for phase in projection.phases)


def test_source_digest_changes_with_any_append_only_source_change() -> None:
    source = SHARED_GOAL.read_text(encoding="utf-8")
    before = project_goal_phase_markdown(source)
    after = project_goal_phase_markdown(source + "\n- append-only-probe\n")

    assert before.source_sha256 != after.source_sha256
    assert render_goal_phase_markdown_v1(after).endswith("- append-only-probe\n")


def test_v1_preserves_crlf_bytes_without_universal_newline_rewrite(
    tmp_path: Path,
) -> None:
    payload = (
        b"# Goal: CRLF proof\r\n\r\n"
        b"- Tag: `goal/crlf-proof`\r\n\r\n"
        b"## Lane Sequences\r\n"
    )
    path = tmp_path / "goal.md"
    path.write_bytes(payload)

    projection = load_goal_phase_markdown_projection(path)

    assert render_goal_phase_markdown_v1(projection).encode("utf-8") == payload


def test_legacy_projection_refuses_native_authority_claims() -> None:
    projection = load_goal_phase_markdown_projection(SHARED_GOAL)
    phase = projection.phases[0]

    with pytest.raises(GoalPhaseMarkdownProjectionError, match="native Phase"):
        GoalLegacyPhaseProjectionV1(
            coordinate=phase.coordinate,
            ordinal=phase.ordinal,
            gate=phase.gate,
            legacy_tick_snapshot=phase.legacy_tick_snapshot,
            legacy_status_snapshot=phase.legacy_status_snapshot,
            work_association=phase.work_association,
            native_phase_state="accepted",  # type: ignore[arg-type]
        )


def test_projection_refuses_derived_values_that_do_not_match_source() -> None:
    projection = load_goal_phase_markdown_projection(SHARED_GOAL)
    lane = projection.lanes[0]
    phase = lane.phases[0]
    forged_phase = replace(phase, ordinal=999)

    with pytest.raises(GoalPhaseMarkdownProjectionError, match="bound source"):
        replace(
            projection,
            lanes=(replace(lane, phases=(forged_phase,)), *projection.lanes[1:]),
        )

    native_gate = replace(
        phase.gate,
        gate_contract_ref="native.contract/v1",
    )
    with pytest.raises(GoalPhaseMarkdownProjectionError, match="compatibility profile"):
        replace(phase, gate=native_gate)
