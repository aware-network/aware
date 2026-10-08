from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from aware_issue_runtime import (
    IssueTimeAuthority,
    build_repository_pulse_payload_v1,
    parse_issue_projection,
)

_ROOT = Path(__file__).resolve().parents[7]
_FIXTURE = (
    _ROOT
    / "workspaces/aware_coordination/modules/workflow/sdks/issue/python/contracts"
    / "repository_pulse/v1/repository-pulse-v1-fixtures.json"
)


def test_runtime_payload_matches_the_sealed_repository_pulse_v1_fixture() -> None:
    fixture = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    for case in fixture["cases"]:
        projections = [
            parse_issue_projection(
                text=source["content_text"],
                source_path=source["source_path"],
                observed_at=case["input"]["observed_at"],
            )
            for source in case["input"]["sources"]
        ]
        assert (
            build_repository_pulse_payload_v1(
                projections=projections,
                repository_revision=case["input"]["repository_revision"],
                observed_at=case["input"]["observed_at"],
                issue_epoch=case["input"]["issue_epoch"],
                issue_cursor=case["input"]["issue_cursor"],
                resolved_goal_refs=case["input"]["resolved_goal_refs"],
                limit=case["input"]["limit"],
            )
            == case["expected_projection"]
        )


def test_cursor_is_exact_stale_safe_and_preserves_the_original_window() -> None:
    projections = (
        _projection("alpha", "2026-08-21T05:00:00Z"),
        _projection("beta", "2026-08-21T04:00:00Z"),
    )
    first = build_repository_pulse_payload_v1(
        projections=projections,
        repository_revision="sha256:" + "a" * 64,
        observed_at="2026-08-21T06:00:00Z",
        issue_epoch="issue-epoch",
        issue_cursor=1,
        limit=1,
    )
    cursor = first["next_cursor"]
    assert isinstance(cursor, str)
    second = build_repository_pulse_payload_v1(
        projections=projections,
        repository_revision="sha256:" + "a" * 64,
        observed_at="2026-08-21T08:00:00Z",
        issue_epoch="issue-epoch",
        issue_cursor=1,
        after_cursor=cursor,
        limit=1,
    )
    assert second["query"] == {
        "since_at": "2026-08-20T18:00:00Z",
        "until_at": "2026-08-21T06:00:00Z",
        "after_cursor": cursor,
        "limit": 1,
    }
    assert [item["activity_ref"] for item in second["items"]] == [
        "fb/2026-08-21/beta#update-1"
    ]
    with pytest.raises(ValueError, match="stale"):
        build_repository_pulse_payload_v1(
            projections=projections,
            repository_revision="sha256:" + "b" * 64,
            observed_at="2026-08-21T06:00:00Z",
            issue_epoch="issue-epoch",
            issue_cursor=2,
            after_cursor=cursor,
            limit=1,
        )


def test_unavailable_and_observation_only_time_never_enter_pulse() -> None:
    unavailable = _projection("unavailable", None)
    trusted = _projection("trusted", "2026-08-21T05:00:00Z")
    observed_activity = replace(
        trusted.activities[0],
        ref="fb/2026-08-21/observed#update-1",
        time_authority=IssueTimeAuthority.SOURCE_OBSERVED,
    )
    observed = replace(
        trusted,
        issue_ref="fb/2026-08-21/observed",
        source_path="docs/issues/2026/08/21/fb-2026-08-21-observed.md",
        activities=(observed_activity,),
    )
    payload = build_repository_pulse_payload_v1(
        projections=(unavailable, observed, trusted),
        repository_revision="sha256:" + "a" * 64,
        observed_at="2026-08-21T06:00:00Z",
        issue_epoch="issue-epoch",
        issue_cursor=1,
    )
    assert [item["issue_ref"] for item in payload["items"]] == ["fb/2026-08-21/trusted"]
    assert payload["diagnostics"]["unavailable_time_activities"] == 1
    assert payload["diagnostics"]["untrusted_time_activities"] == 1


def test_duplicate_historical_activity_identity_is_an_integrity_diagnostic() -> None:
    first = _projection("first", "2026-08-21T05:00:00Z")
    second = _projection("second", "2026-08-21T04:00:00Z")
    second_activity = replace(second.activities[0], ref=first.activities[0].ref)
    second = replace(second, activities=(second_activity,))
    payload = build_repository_pulse_payload_v1(
        projections=(first, second),
        repository_revision="sha256:" + "a" * 64,
        observed_at="2026-08-21T06:00:00Z",
        issue_epoch="issue-epoch",
        issue_cursor=1,
    )
    assert payload["items"] == []
    assert payload["diagnostics"]["identity_conflict_activities"] == 2


def _projection(slug: str, activity_at: str | None):
    activity = (
        "- activity without authoritative time (recorder: `codex-test`)"
        if activity_at is None
        else f"- {activity_at} — opened (recorder: `codex-test`)"
    )
    text = f"""# Issue: {slug.title()}

- Slug: `{slug}`
- Tag: `fb/2026-08-21/{slug}`
- Status: In Progress
- Priority: P0

## Goal
1. Prove Pulse.

## Acceptance Checklist
- [ ] complete

## Updates (append-only)
{activity}
"""
    return parse_issue_projection(
        text=text,
        source_path=f"docs/issues/2026/08/21/fb-2026-08-21-{slug}.md",
        observed_at="2026-08-21T06:00:00Z",
    )
