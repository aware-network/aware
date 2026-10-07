"""Issue-authoritative cross-Issue activity projection for Repository Pulse."""

from __future__ import annotations

import base64
import binascii
import json
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import cast

from .contracts import IssueReadProjection
from .development import issue_development_read_payload_v2_from_runtime
from .parser import parse_issue_source

REPOSITORY_PULSE_SCHEMA_V1 = "aware.coordination.repository-pulse.v1"
REPOSITORY_PULSE_ACTIVITY_SCHEMA_V1 = "aware.coordination.repository-pulse-activity.v1"

_DEFAULT_WINDOW = timedelta(hours=12)
_DEFAULT_LIMIT = 100
_MAX_LIMIT = 500
_CURSOR_PREFIX = "repository-pulse-v1."
_TRUSTED_ACTIVITY_TIME_AUTHORITIES = frozenset(
    {"commit_receipt", "issue_service", "source_declared"}
)


def build_repository_pulse_payload_v1(
    *,
    projections: Iterable[IssueReadProjection],
    repository_revision: str,
    observed_at: str,
    issue_epoch: str,
    issue_cursor: int,
    resolved_goal_refs: Iterable[str] = (),
    since_at: str | None = None,
    until_at: str | None = None,
    after_cursor: str | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> dict[str, object]:
    """Build one stale-safe, time-bounded page over authoritative Issue activity."""

    if not repository_revision:
        raise ValueError("Repository Pulse requires repository_revision.")
    if not issue_epoch:
        raise ValueError("Repository Pulse requires issue_epoch.")
    if (
        not isinstance(issue_cursor, int)
        or isinstance(issue_cursor, bool)
        or issue_cursor < 0
    ):
        raise ValueError("Repository Pulse issue_cursor is invalid.")
    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= _MAX_LIMIT
    ):
        raise ValueError(f"Repository Pulse limit must be between 1 and {_MAX_LIMIT}.")

    normalized_observed_at = _normalize_absolute_time(observed_at)
    normalized_since_at, normalized_until_at = repository_pulse_window_v1(
        repository_revision=repository_revision,
        observed_at=normalized_observed_at,
        since_at=since_at,
        until_at=until_at,
        after_cursor=after_cursor,
    )
    cursor_payload = None if after_cursor is None else _decode_cursor(after_cursor)

    since = _parse_absolute_time(normalized_since_at)
    until = _parse_absolute_time(normalized_until_at)
    if since > until:
        raise ValueError("Repository Pulse since_at cannot be after until_at.")

    goal_refs = frozenset(resolved_goal_refs)
    rows: list[tuple[datetime, str, dict[str, object]]] = []
    issue_count = 0
    activity_count = 0
    trusted_timed_count = 0
    unavailable_time_count = 0
    untrusted_time_count = 0
    activity_ref_counts: dict[str, int] = {}

    for projection in projections:
        issue_count += 1
        development = issue_development_read_payload_v2_from_runtime(
            projection,
            raw_lifecycle=parse_issue_source(projection.raw_markdown).header("Status"),
        )
        identity = cast(dict[str, object], development["identity"])
        lifecycle = cast(dict[str, object], identity["lifecycle"])
        source = cast(dict[str, object], development["source"])
        for raw_activity in cast(list[dict[str, object]], development["activities"]):
            activity_count += 1
            activity_ref = _required_text(raw_activity, "activity_ref")
            activity_ref_counts[activity_ref] = (
                activity_ref_counts.get(activity_ref, 0) + 1
            )
            activity_at = raw_activity.get("activity_at")
            time_authority = _required_text(raw_activity, "time_authority")
            if activity_at is None or time_authority == "unavailable":
                unavailable_time_count += 1
                continue
            if not isinstance(activity_at, str):
                raise TypeError("Repository Pulse activity_at is invalid.")
            if time_authority not in _TRUSTED_ACTIVITY_TIME_AUTHORITIES:
                untrusted_time_count += 1
                continue
            normalized_activity_at = _normalize_absolute_time(activity_at)
            activity_time = _parse_absolute_time(normalized_activity_at)
            trusted_timed_count += 1
            if not since <= activity_time <= until:
                continue
            goal_ref = identity.get("goal_ref")
            goal_resolution = (
                "unavailable"
                if goal_ref is None
                else "resolved"
                if isinstance(goal_ref, str) and goal_ref in goal_refs
                else "unresolved"
            )
            row = {
                "schema_ref": REPOSITORY_PULSE_ACTIVITY_SCHEMA_V1,
                "activity_ref": activity_ref,
                "issue_ref": _required_text(identity, "issue_ref"),
                "issue_projection_revision": projection.projection_revision,
                "issue_title": _required_text(identity, "title"),
                "lifecycle": lifecycle,
                "priority": identity.get("priority"),
                "owner_execution_id": identity.get("owner_execution_id"),
                "goal_ref": goal_ref,
                "goal_resolution": goal_resolution,
                "sequence": raw_activity["sequence"],
                "headline": _required_text(raw_activity, "headline"),
                "actor_execution_id": raw_activity.get("actor_execution_id"),
                "activity_at": normalized_activity_at,
                "time_authority": time_authority,
                "semantic_kind": raw_activity["semantic_kind"],
                "references": raw_activity["references"],
                "outcome": raw_activity.get("outcome"),
                "source_path": _required_text(source, "path"),
                "source_observed_at": _required_text(source, "observed_at"),
            }
            rows.append((activity_time, activity_ref, row))

    conflicting_refs = {
        activity_ref for activity_ref, count in activity_ref_counts.items() if count > 1
    }
    identity_conflict_count = sum(activity_ref_counts[ref] for ref in conflicting_refs)
    if conflicting_refs:
        rows = [row for row in rows if row[1] not in conflicting_refs]
    rows.sort(key=lambda value: (value[0], value[1]), reverse=True)
    start = 0
    if cursor_payload is not None:
        cursor_identity = (
            _parse_absolute_time(_cursor_text(cursor_payload, "activity_at")),
            _cursor_text(cursor_payload, "activity_ref"),
        )
        for index, (activity_time, activity_ref, _) in enumerate(rows):
            if (activity_time, activity_ref) == cursor_identity:
                start = index + 1
                break
        else:
            raise ValueError(
                "Repository Pulse cursor activity is absent from this revision."
            )

    selected = rows[start : start + limit]
    has_more = start + len(selected) < len(rows)
    next_cursor = None
    if has_more and selected:
        last_time, last_ref, _ = selected[-1]
        next_cursor = _encode_cursor(
            {
                "repository_revision": repository_revision,
                "since_at": normalized_since_at,
                "until_at": normalized_until_at,
                "activity_at": _format_absolute_time(last_time),
                "activity_ref": last_ref,
            }
        )

    return {
        "schema_ref": REPOSITORY_PULSE_SCHEMA_V1,
        "authority_kind": "local_uncommitted",
        "repository_revision": repository_revision,
        "observed_at": normalized_observed_at,
        "issue_epoch": issue_epoch,
        "issue_cursor": issue_cursor,
        "query": {
            "since_at": normalized_since_at,
            "until_at": normalized_until_at,
            "after_cursor": after_cursor,
            "limit": limit,
        },
        "diagnostics": {
            "issues_considered": issue_count,
            "activities_considered": activity_count,
            "trusted_timed_activities": trusted_timed_count,
            "unavailable_time_activities": unavailable_time_count,
            "untrusted_time_activities": untrusted_time_count,
            "identity_conflict_activities": identity_conflict_count,
            "window_activities": len(rows),
        },
        "items": [row for _, _, row in selected],
        "next_cursor": next_cursor,
        "truncated": has_more,
    }


def repository_pulse_window_v1(
    *,
    repository_revision: str,
    observed_at: str,
    since_at: str | None = None,
    until_at: str | None = None,
    after_cursor: str | None = None,
) -> tuple[str, str]:
    """Resolve the exact activity window shared by hydration and projection."""

    if not repository_revision:
        raise ValueError("Repository Pulse requires repository_revision.")
    normalized_observed_at = _normalize_absolute_time(observed_at)
    cursor_payload = None if after_cursor is None else _decode_cursor(after_cursor)
    if cursor_payload is not None:
        _require_cursor_revision(cursor_payload, repository_revision)
        cursor_since = _cursor_text(cursor_payload, "since_at")
        cursor_until = _cursor_text(cursor_payload, "until_at")
        if since_at is not None and _normalize_absolute_time(since_at) != cursor_since:
            raise ValueError("Repository Pulse cursor does not match since_at.")
        if until_at is not None and _normalize_absolute_time(until_at) != cursor_until:
            raise ValueError("Repository Pulse cursor does not match until_at.")
        normalized_since_at = cursor_since
        normalized_until_at = cursor_until
    else:
        normalized_until_at = _normalize_absolute_time(
            until_at or normalized_observed_at
        )
        normalized_since_at = _normalize_absolute_time(
            since_at
            or (_parse_absolute_time(normalized_until_at) - _DEFAULT_WINDOW).isoformat()
        )
    if _parse_absolute_time(normalized_since_at) > _parse_absolute_time(
        normalized_until_at
    ):
        raise ValueError("Repository Pulse since_at cannot be after until_at.")
    return normalized_since_at, normalized_until_at


def _encode_cursor(payload: dict[str, str]) -> str:
    encoded = base64.urlsafe_b64encode(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    return _CURSOR_PREFIX + encoded.rstrip("=")


def _decode_cursor(value: str) -> dict[str, object]:
    if not isinstance(value, str) or not value.startswith(_CURSOR_PREFIX):
        raise ValueError("Repository Pulse cursor is invalid.")
    encoded = value.removeprefix(_CURSOR_PREFIX)
    try:
        raw = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
        payload = json.loads(raw.decode("utf-8"))
    except (
        binascii.Error,
        UnicodeDecodeError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        raise ValueError("Repository Pulse cursor is invalid.") from error
    expected = {
        "repository_revision",
        "since_at",
        "until_at",
        "activity_at",
        "activity_ref",
    }
    if not isinstance(payload, dict) or set(payload) != expected:
        raise ValueError("Repository Pulse cursor fields are invalid.")
    for field in expected:
        _cursor_text(payload, field)
    return cast(dict[str, object], payload)


def _require_cursor_revision(
    cursor_payload: dict[str, object], repository_revision: str
) -> None:
    if _cursor_text(cursor_payload, "repository_revision") != repository_revision:
        raise ValueError(
            "Repository Pulse cursor is stale for this repository revision."
        )


def _cursor_text(payload: dict[str, object], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Repository Pulse cursor {field} is invalid.")
    return value


def _required_text(payload: dict[str, object], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise TypeError(f"Repository Pulse {field} is invalid.")
    return value


def _parse_absolute_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.strip())
    except ValueError as error:
        raise ValueError("Repository Pulse timestamp is invalid.") from error
    if parsed.tzinfo is None:
        raise ValueError("Repository Pulse timestamp requires an explicit timezone.")
    return parsed.astimezone(UTC)


def _normalize_absolute_time(value: str) -> str:
    return _format_absolute_time(_parse_absolute_time(value))


def _format_absolute_time(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


__all__ = [
    "REPOSITORY_PULSE_ACTIVITY_SCHEMA_V1",
    "REPOSITORY_PULSE_SCHEMA_V1",
    "build_repository_pulse_payload_v1",
    "repository_pulse_window_v1",
]
