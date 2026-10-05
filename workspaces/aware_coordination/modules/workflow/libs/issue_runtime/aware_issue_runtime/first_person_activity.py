"""Issue-authoritative first-person Activity projection."""

from __future__ import annotations

import base64
import binascii
import json
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import cast

from .contracts import IssueReadProjection
from .development import issue_development_read_payload_v2_from_runtime
from .parser import parse_issue_source
from .pulse import build_repository_pulse_payload_v1

FIRST_PERSON_ISSUE_ACTIVITY_SCHEMA_V1 = (
    "aware.coordination.first-person-issue-activity.v1"
)

_CURSOR_PREFIX = "first-person-issue-activity-v1."
_TRUSTED_ACTIVITY_TIME_AUTHORITIES = frozenset(
    {"commit_receipt", "issue_service", "source_declared"}
)


def build_first_person_issue_activity_payload_v1(
    *,
    projections: Iterable[IssueReadProjection],
    owner_execution_id: str,
    repository_revision: str,
    observed_at: str,
    issue_epoch: str,
    issue_cursor: int,
    resolved_goal_refs: Iterable[str] = (),
    since_at: str | None = None,
    until_at: str | None = None,
    after_cursor: str | None = None,
    limit: int = 100,
) -> dict[str, object]:
    """Project one admitted execution's Issue work and recent occurrences."""

    normalized_owner = _required_trimmed(owner_execution_id, "owner_execution_id")
    normalized_revision = _required_trimmed(repository_revision, "repository_revision")
    all_projections = tuple(projections)
    owned = tuple(
        projection
        for projection in all_projections
        if projection.owner_ref == normalized_owner
    )
    repository_cursor = None
    if after_cursor is not None:
        cursor_payload = _decode_cursor(after_cursor)
        if cursor_payload["owner_execution_id"] != normalized_owner:
            raise ValueError(
                "First-person Issue Activity cursor belongs to another subject."
            )
        if cursor_payload["repository_revision"] != normalized_revision:
            raise ValueError(
                "First-person Issue Activity cursor is stale for this repository revision."
            )
        repository_cursor = cast(str, cursor_payload["repository_pulse_cursor"])

    pulse = build_repository_pulse_payload_v1(
        projections=owned,
        repository_revision=normalized_revision,
        observed_at=observed_at,
        issue_epoch=issue_epoch,
        issue_cursor=issue_cursor,
        resolved_goal_refs=resolved_goal_refs,
        since_at=since_at,
        until_at=until_at,
        after_cursor=repository_cursor,
        limit=limit,
    )
    pulse_query = cast(dict[str, object], pulse["query"])
    pulse_cursor = pulse["next_cursor"]
    next_cursor = (
        None
        if pulse_cursor is None
        else _encode_cursor(
            {
                "owner_execution_id": normalized_owner,
                "repository_revision": normalized_revision,
                "repository_pulse_cursor": cast(str, pulse_cursor),
            }
        )
    )
    work_items = [_owned_work_item(projection) for projection in owned]
    work_items.sort(key=_work_item_order, reverse=True)
    diagnostics = dict(cast(dict[str, object], pulse["diagnostics"]))
    diagnostics["owned_issue_count"] = len(work_items)
    diagnostics["repository_issue_count"] = len(all_projections)
    return {
        "schema_ref": FIRST_PERSON_ISSUE_ACTIVITY_SCHEMA_V1,
        "authority_kind": pulse["authority_kind"],
        "owner_execution_id": normalized_owner,
        "repository_revision": normalized_revision,
        "observed_at": pulse["observed_at"],
        "issue_epoch": pulse["issue_epoch"],
        "issue_cursor": pulse["issue_cursor"],
        "query": {
            "since_at": pulse_query["since_at"],
            "until_at": pulse_query["until_at"],
            "after_cursor": after_cursor,
            "limit": pulse_query["limit"],
        },
        "work_items": work_items,
        "occurrences": pulse["items"],
        "next_cursor": next_cursor,
        "truncated": pulse["truncated"],
        "diagnostics": diagnostics,
    }


def _owned_work_item(projection: IssueReadProjection) -> dict[str, object]:
    development = issue_development_read_payload_v2_from_runtime(
        projection,
        raw_lifecycle=parse_issue_source(projection.raw_markdown).header("Status"),
    )
    identity = cast(dict[str, object], development["identity"])
    lifecycle = cast(dict[str, object], identity["lifecycle"])
    activities = cast(list[dict[str, object]], development["activities"])
    latest = cast(dict[str, object], development["latest_activity"])
    ordering = _latest_trusted_activity(activities)
    return {
        "issue_ref": identity["issue_ref"],
        "issue_projection_revision": projection.projection_revision,
        "issue_title": identity["title"],
        "lifecycle": lifecycle,
        "priority": identity.get("priority"),
        "owner_execution_id": identity.get("owner_execution_id"),
        "goal_ref": identity.get("goal_ref"),
        "relationship": "owned_by_current_execution",
        "latest_activity": latest,
        "ordering_activity": (
            {
                "activity_ref": ordering["activity_ref"],
                "activity_at": ordering["activity_at"],
                "time_authority": ordering["time_authority"],
            }
            if ordering is not None
            else {
                "activity_ref": None,
                "activity_at": None,
                "time_authority": "unavailable",
            }
        ),
        "source_path": projection.source_path,
    }


def _latest_trusted_activity(
    activities: list[dict[str, object]],
) -> dict[str, object] | None:
    trusted = [
        item
        for item in activities
        if isinstance(item.get("activity_at"), str)
        and item.get("time_authority") in _TRUSTED_ACTIVITY_TIME_AUTHORITIES
    ]
    if not trusted:
        return None
    return max(
        trusted,
        key=lambda item: (
            _parse_absolute_time(cast(str, item["activity_at"])),
            cast(str, item["activity_ref"]),
        ),
    )


def _work_item_order(item: dict[str, object]) -> tuple[int, datetime, str]:
    ordering = cast(dict[str, object], item["ordering_activity"])
    activity_at = ordering.get("activity_at")
    if isinstance(activity_at, str):
        return (1, _parse_absolute_time(activity_at), cast(str, item["issue_ref"]))
    return (0, datetime.min.replace(tzinfo=UTC), cast(str, item["issue_ref"]))


def _encode_cursor(payload: dict[str, str]) -> str:
    encoded = base64.urlsafe_b64encode(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    return _CURSOR_PREFIX + encoded.rstrip("=")


def _decode_cursor(value: str) -> dict[str, object]:
    if not isinstance(value, str) or not value.startswith(_CURSOR_PREFIX):
        raise ValueError("First-person Issue Activity cursor is invalid.")
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
        raise ValueError("First-person Issue Activity cursor is invalid.") from error
    expected = {
        "owner_execution_id",
        "repository_revision",
        "repository_pulse_cursor",
    }
    if not isinstance(payload, dict) or set(payload) != expected:
        raise ValueError("First-person Issue Activity cursor fields are invalid.")
    for field in expected:
        _required_trimmed(payload.get(field), f"cursor {field}")
    return cast(dict[str, object], payload)


def _required_trimmed(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"First-person Issue Activity {field} is invalid.")
    return value


def _parse_absolute_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.strip())
    if parsed.tzinfo is None:
        raise ValueError("First-person Issue Activity time requires a timezone.")
    return parsed.astimezone(UTC)


__all__ = [
    "FIRST_PERSON_ISSUE_ACTIVITY_SCHEMA_V1",
    "build_first_person_issue_activity_payload_v1",
]
