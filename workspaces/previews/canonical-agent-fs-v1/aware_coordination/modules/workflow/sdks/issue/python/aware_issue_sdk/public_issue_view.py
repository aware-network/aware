"""A public reading of one Issue, lowered from its development read projection.

The Issue SDK owns what an Issue says. This lowers the canonical
`IssueReadProjectionV2` into a view state a reader can be shown — its title,
lifecycle, priority, problem, goal, acceptance, resolution, activity and
attention — and withholds what identifies people or storage: owner and actor
ids, repository paths, raw Markdown, commands, references and receipts, which
leave only as counts. It parses nothing itself.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from aware_issue_sdk.development_read_projection import (
    build_issue_development_read_projection_v2,
)

ISSUE_VIEW_STATE_SCHEMA = "aware.workflow.issue.view_state.v1"

# An execution identity written into prose (`codex-<uuid>`): it names a
# session, so it reads as one.
_EXECUTION_ID = re.compile(
    r"\b([a-z][a-z_]*)-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"
)


def _said(text: str | None) -> str | None:
    """Text as a reader may see it: execution identities read as sessions."""

    return None if text is None else _EXECUTION_ID.sub(r"\1 session", text)


def issue_view_key(repository_path: str) -> str:
    """An opaque, stable key for the Issue at [repository_path].

    It names the Issue without saying where it is stored, so a Goal can refer
    to an Issue and a reader can resolve its view without the path leaving.
    """

    normalized = repository_path.strip().lstrip("./")
    return "issue:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def public_issue_view_state(
    content_text: str,
    *,
    repository_path: str,
    observed_at: str,
) -> dict[str, Any]:
    """The Issue at [repository_path] as a reader may see it."""

    reading = build_issue_development_read_projection_v2(
        content_text=content_text,
        source_path=repository_path,
        source_observed_at=observed_at,
    )
    identity = reading.identity
    acceptance = [
        {"text": _said(item.text), "checked": bool(item.checked)}
        for item in reading.acceptance_items
    ]
    activities = [
        {
            "sequence": activity.sequence,
            "headline": _said(activity.headline),
            "detail": _said(activity.detail),
            "kind": activity.semantic_kind.value,
            "at": activity.activity_at,
            "time_authority": activity.time_authority,
            "outcome": activity.outcome,
        }
        for activity in reading.activities
    ]
    return {
        "schema_version": ISSUE_VIEW_STATE_SCHEMA,
        "key": issue_view_key(repository_path),
        "title": _said(identity.title),
        "lifecycle": identity.lifecycle.value,
        "status": identity.lifecycle.raw_value or identity.lifecycle.value,
        "priority": identity.priority,
        "problem": [_said(item.text) for item in reading.problem_items],
        "goal": [_said(item.text) for item in reading.goal_items],
        "acceptance": acceptance,
        "resolution": _said(reading.resolution),
        "activities": activities,
        "attention": [
            {
                "kind": candidate.kind,
                "raised_at": candidate.raised_at,
                "resolved_at": candidate.resolved_at,
            }
            for candidate in reading.attention_candidates
        ],
        "latest_activity": {
            "at": reading.latest_activity.activity_at,
            "time_authority": reading.latest_activity.time_authority,
        },
        "evidence_count": len(reading.evidence_refs),
        "scope_count": len(identity.ownership_scope),
    }


def issue_view_summary(view: dict[str, Any]) -> dict[str, Any]:
    """What a map needs of an Issue view: status, priority, checks and when
    its activity was recorded — derived from the view, never re-read."""

    acceptance = view.get("acceptance") or []
    return {
        "key": view["key"],
        "title": view.get("title"),
        "status": view.get("status"),
        "priority": view.get("priority"),
        "checks": (
            {
                "done": sum(1 for item in acceptance if item["checked"]),
                "total": len(acceptance),
            }
            if acceptance
            else None
        ),
        "update_times": sorted(
            activity["at"] for activity in view.get("activities") or [] if activity["at"]
        ),
    }


__all__ = [
    "ISSUE_VIEW_STATE_SCHEMA",
    "issue_view_key",
    "issue_view_summary",
    "public_issue_view_state",
]
