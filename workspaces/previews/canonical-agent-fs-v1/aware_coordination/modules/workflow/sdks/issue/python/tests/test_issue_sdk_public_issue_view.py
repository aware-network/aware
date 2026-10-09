"""The public reading of an Issue: what a reader sees, what never leaves."""

from __future__ import annotations

import json

from aware_issue_sdk.public_issue_view import (
    issue_view_key,
    issue_view_summary,
    public_issue_view_state,
)

_ISSUE = """# Issue: Host implementation

- Slug: host-implementation-v0
- Tag: fb/2026-09-21/host-implementation-v0
- Status: Closed
- Owner: codex-private-owner
- Priority: P0
- Goal: goal/2026-09-10/example-v0

## Ownership Scope
- `docs/issues/2026/09/21/fb-2026-09-21-host-implementation-v0.md`
- `workspaces/secret/path.dart`

## Problem
The host is not native yet.

## Acceptance Checklist
- [x] One
- [ ] Two

## Updates (append-only)
- 2026-09-21T11:00:00Z | codex-private-actor | Opened the issue.
- 2026-09-21T12:00:00Z | codex-private-actor | Closed after commit `abc1234` in `workspaces/secret/path.dart`.
- 2026-09-21T13:00:00Z | codex-private-actor | Reviewed by codex-01a0c62a-621c-7060-9b65-3f1dc73850a3.
"""

_PATH = "docs/issues/2026/09/21/fb-2026-09-21-host-implementation-v0.md"


def _view():
    return public_issue_view_state(
        _ISSUE, repository_path=_PATH, observed_at="2026-09-24T00:00:00Z"
    )


def test_a_reader_sees_what_the_issue_says() -> None:
    view = _view()
    assert view["schema_version"] == "aware.workflow.issue.view_state.v1"
    assert view["title"] == "Host implementation"
    assert view["status"] == "Closed"
    assert view["priority"] == "P0"
    assert view["problem"] == ["The host is not native yet."]
    assert view["acceptance"] == [
        {"text": "One", "checked": True},
        {"text": "Two", "checked": False},
    ]
    assert [activity["at"] for activity in view["activities"]] == [
        "2026-09-21T11:00:00Z",
        "2026-09-21T12:00:00Z",
        "2026-09-21T13:00:00Z",
    ]
    # An execution identity in prose reads as a session.
    assert view["activities"][2]["headline"] == "Reviewed by codex session."
    assert view["scope_count"] == 2


def test_people_and_storage_never_leave() -> None:
    encoded = json.dumps(_view())
    for private in ("codex-private-owner", "codex-private-actor", "01a0c62a", _PATH, "fb-2026"):
        assert private not in encoded


def test_the_key_names_the_issue_without_its_path() -> None:
    key = issue_view_key(_PATH)
    assert key == issue_view_key("./" + _PATH)
    assert key.startswith("issue:") and "docs" not in key
    assert _view()["key"] == key


def test_a_summary_derives_from_the_view() -> None:
    summary = issue_view_summary(_view())
    assert summary["status"] == "Closed"
    assert summary["checks"] == {"done": 1, "total": 2}
    assert summary["update_times"] == [
        "2026-09-21T11:00:00Z",
        "2026-09-21T12:00:00Z",
        "2026-09-21T13:00:00Z",
    ]
