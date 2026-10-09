from __future__ import annotations

from dataclasses import replace

import pytest
from aware_issue_runtime import (
    IssueTimeAuthority,
    build_first_person_issue_activity_payload_v1,
    parse_issue_projection,
)

_REVISION = "sha256:" + "a" * 64
_OWNER = "codex-current-thread"


def test_first_person_activity_returns_only_owned_work_and_occurrences() -> None:
    newest = _projection(
        "newest",
        owner=_OWNER,
        activity_at="2026-08-23T05:00:00Z",
    )
    older = _projection(
        "older",
        owner=_OWNER,
        activity_at="2026-08-23T04:00:00Z",
    )
    unrelated = _projection(
        "unrelated",
        owner="codex-other-thread",
        activity_at="2026-08-23T06:00:00Z",
    )

    payload = build_first_person_issue_activity_payload_v1(
        projections=(older, unrelated, newest),
        owner_execution_id=_OWNER,
        repository_revision=_REVISION,
        observed_at="2026-08-23T06:00:00Z",
        issue_epoch="issue-epoch",
        issue_cursor=3,
    )

    assert [item["issue_ref"] for item in payload["work_items"]] == [
        "fb/2026-08-23/newest",
        "fb/2026-08-23/older",
    ]
    assert [item["issue_ref"] for item in payload["occurrences"]] == [
        "fb/2026-08-23/newest",
        "fb/2026-08-23/older",
    ]
    assert payload["diagnostics"]["owned_issue_count"] == 2
    assert payload["diagnostics"]["repository_issue_count"] == 3


def test_work_order_uses_trusted_time_without_relabeling_latest_append() -> None:
    trusted = _projection(
        "trusted-then-unavailable",
        owner=_OWNER,
        activity_at="2026-08-23T05:00:00Z",
    )
    unavailable = replace(
        trusted.activities[0],
        ref="fb/2026-08-23/trusted-then-unavailable#update-2",
        sequence=2,
        activity_at=None,
        time_authority=IssueTimeAuthority.UNAVAILABLE,
    )
    trusted = replace(trusted, activities=(*trusted.activities, unavailable))
    no_time = _projection("no-time", owner=_OWNER, activity_at=None)

    payload = build_first_person_issue_activity_payload_v1(
        projections=(no_time, trusted),
        owner_execution_id=_OWNER,
        repository_revision=_REVISION,
        observed_at="2026-08-23T06:00:00Z",
        issue_epoch="issue-epoch",
        issue_cursor=2,
    )

    first, second = payload["work_items"]
    assert first["issue_ref"] == "fb/2026-08-23/trusted-then-unavailable"
    assert first["latest_activity"]["time_authority"] == "unavailable"
    assert first["ordering_activity"] == {
        "activity_ref": "fb/2026-08-23/trusted-then-unavailable#update-1",
        "activity_at": "2026-08-23T05:00:00Z",
        "time_authority": "source_declared",
    }
    assert second["ordering_activity"]["time_authority"] == "unavailable"


def test_cursor_is_bound_to_subject_and_repository_revision() -> None:
    projections = (
        _projection("newest", owner=_OWNER, activity_at="2026-08-23T05:00:00Z"),
        _projection("older", owner=_OWNER, activity_at="2026-08-23T04:00:00Z"),
    )
    first = build_first_person_issue_activity_payload_v1(
        projections=projections,
        owner_execution_id=_OWNER,
        repository_revision=_REVISION,
        observed_at="2026-08-23T06:00:00Z",
        issue_epoch="issue-epoch",
        issue_cursor=2,
        limit=1,
    )
    cursor = first["next_cursor"]
    assert isinstance(cursor, str)

    second = build_first_person_issue_activity_payload_v1(
        projections=projections,
        owner_execution_id=_OWNER,
        repository_revision=_REVISION,
        observed_at="2026-08-23T08:00:00Z",
        issue_epoch="issue-epoch",
        issue_cursor=2,
        after_cursor=cursor,
        limit=1,
    )
    assert [item["issue_ref"] for item in second["occurrences"]] == [
        "fb/2026-08-23/older"
    ]
    assert second["query"]["until_at"] == "2026-08-23T06:00:00Z"

    with pytest.raises(ValueError, match="another subject"):
        build_first_person_issue_activity_payload_v1(
            projections=projections,
            owner_execution_id="codex-other-thread",
            repository_revision=_REVISION,
            observed_at="2026-08-23T06:00:00Z",
            issue_epoch="issue-epoch",
            issue_cursor=2,
            after_cursor=cursor,
            limit=1,
        )
    with pytest.raises(ValueError, match="stale"):
        build_first_person_issue_activity_payload_v1(
            projections=projections,
            owner_execution_id=_OWNER,
            repository_revision="sha256:" + "b" * 64,
            observed_at="2026-08-23T06:00:00Z",
            issue_epoch="issue-epoch",
            issue_cursor=3,
            after_cursor=cursor,
            limit=1,
        )


def _projection(slug: str, *, owner: str, activity_at: str | None):
    activity = (
        "- update without authoritative time (recorder: `codex-test`)"
        if activity_at is None
        else f"- {activity_at} — update (recorder: `codex-test`)"
    )
    return parse_issue_projection(
        text=f"""# Issue: {slug.title()}

- Slug: {slug}
- Tag: fb/2026-08-23/{slug}
- Status: In Progress
- Owner: {owner}
- Priority: P0

## Goal
1. Prove first-person Activity.

## Acceptance Checklist
- [ ] complete

## Updates (append-only)
{activity}
""",
        source_path=f"docs/issues/2026/08/23/fb-2026-08-23-{slug}.md",
        observed_at="2026-08-23T06:00:00Z",
    )
