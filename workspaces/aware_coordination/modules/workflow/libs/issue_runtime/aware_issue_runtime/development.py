"""Generated-free Development facets over canonical Issue projections."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from pathlib import PurePosixPath

from .contracts import IssueActivityProjection, IssueReadProjection, IssueTimeAuthority
from .parser import parse_issue_projection, parse_issue_source

ISSUE_DEVELOPMENT_READ_PROJECTION_V2_SCHEMA = (
    "aware.coordination.issue-development-read-projection.v2"
)

_DECLARED_LIFECYCLES = frozenset({"open", "in_progress", "blocked", "closed"})
_LIFECYCLE_ALIASES = {
    "inprogress": "in_progress",
    "resolved": "closed",
    "completed": "closed",
    "rejected": "closed",
}
_DECLARED_ACTIVITY_KINDS = frozenset(
    {
        "opened",
        "claimed",
        "progress",
        "implementation",
        "implementation_ready",
        "commit",
        "proof",
        "blocked",
        "human_direction",
        "resolved",
    }
)
_ACTIVITY_KIND_ALIASES = {
    "claim": "claimed",
    "update": "progress",
    "implementation-ready": "implementation_ready",
    "validation": "proof",
    "verified": "proof",
    "blocker": "blocked",
    "closed": "resolved",
}
_DECLARED_KIND = re.compile(
    r"(?:activity_kind\s*=\s*`?(?P<assignment>[a-z][a-z0-9_-]*)`?"
    + r"|\(activity(?:_kind)?:\s*`?(?P<suffix>[a-z][a-z0-9_-]*)`?\))",
    re.IGNORECASE,
)
_COMMIT_SHA = re.compile(r"(?<![0-9a-f])(?P<sha>[0-9a-f]{40})(?![0-9a-f])")
_BACKTICK = re.compile(r"`(?P<value>[^`]+)`")


def build_issue_development_read_payload_v2(
    *,
    content_text: str,
    source_path: str,
    source_observed_at: str,
) -> dict[str, object]:
    """Parse only through Issue runtime, then add deterministic Dev facets."""

    observed_at = _normalize_absolute_time(source_observed_at)
    projection = parse_issue_projection(
        text=content_text,
        source_path=source_path,
        observed_at=observed_at,
    )
    raw_lifecycle = parse_issue_source(content_text).header("Status")
    return issue_development_read_payload_v2_from_runtime(
        projection,
        raw_lifecycle=raw_lifecycle,
    )


def issue_development_read_payload_v2_from_runtime(
    projection: IssueReadProjection,
    *,
    raw_lifecycle: str | None,
) -> dict[str, object]:
    """Return the dependency-free wire payload used by SDK and Local Service."""

    if projection.observation_time_authority is not IssueTimeAuthority.SOURCE_OBSERVED:
        raise ValueError("Development V2 requires explicit source observation time.")
    if projection.observed_at is None:
        raise ValueError("Development V2 requires source observed_at.")
    observed_at = _normalize_absolute_time(projection.observed_at)
    activities = [_activity(item) for item in projection.activities]
    latest = activities[-1] if activities else None
    return {
        "schema_ref": ISSUE_DEVELOPMENT_READ_PROJECTION_V2_SCHEMA,
        "projection_revision": projection.projection_revision,
        "identity": {
            "issue_ref": projection.issue_ref,
            "title": projection.title,
            "slug": projection.slug,
            "tag": projection.tag,
            "lifecycle": normalize_issue_lifecycle_payload_v1(raw_lifecycle),
            "priority": projection.priority,
            "owner_execution_id": projection.owner_ref,
            "goal_ref": projection.goal_ref,
            "source_description": projection.source_description,
            "ownership_scope": list(projection.ownership_scope),
        },
        "problem_items": [
            {"sequence": index, "text": text, "checked": None, "raw_markdown": None}
            for index, text in enumerate(projection.problem_items, start=1)
        ],
        "goal_items": [
            {"sequence": index, "text": text, "checked": None, "raw_markdown": None}
            for index, text in enumerate(projection.goal_items, start=1)
        ],
        "acceptance_items": [
            {
                "sequence": item.sequence,
                "text": item.text,
                "checked": item.checked,
                "raw_markdown": item.raw_line,
            }
            for item in projection.acceptance_items
        ],
        "activities": activities,
        "attention_candidates": _attention_candidates(activities),
        "evidence_refs": [
            {
                "sequence": item.sequence,
                "text": item.reference,
                "checked": None,
                "raw_markdown": item.raw_line,
            }
            for item in projection.evidence
        ],
        "resolution": projection.resolution,
        "additional_sections": [
            {
                "sequence": index,
                "heading": section.heading,
                "raw_lines": list(section.lines),
            }
            for index, section in enumerate(projection.additional_sections, start=1)
        ],
        "source": {
            "path": projection.source_path,
            "digest": projection.source_digest,
            "raw_markdown": projection.raw_markdown,
            "observed_at": observed_at,
            "observation_time_authority": "source_observed",
        },
        "latest_activity": {
            "sequence": None if latest is None else latest["sequence"],
            "activity_ref": None if latest is None else latest["activity_ref"],
            "activity_at": None if latest is None else latest["activity_at"],
            "time_authority": (
                "unavailable" if latest is None else latest["time_authority"]
            ),
        },
        "canonical_receipt_coordinates": [
            value
            for value in (
                projection.lane_head_commit_id,
                projection.function_call_id,
            )
            if value is not None
        ],
    }


def normalize_issue_lifecycle_payload_v1(
    raw_value: str | None,
) -> dict[str, object]:
    if raw_value is None or not raw_value.strip():
        return {"value": "unknown", "raw_value": None, "classification": "unknown"}
    normalized_raw = raw_value.strip().strip("`").strip()
    token = _token(normalized_raw)
    if token in _DECLARED_LIFECYCLES:
        classification = "declared"
        value = token
    elif token in _LIFECYCLE_ALIASES:
        classification = "normalized_alias"
        value = _LIFECYCLE_ALIASES[token]
    else:
        classification = "unknown"
        value = "unknown"
    return {
        "value": value,
        "raw_value": normalized_raw,
        "classification": classification,
    }


def normalize_issue_activity_kind_payload_v1(raw_value: str) -> dict[str, object]:
    token = "_".join(raw_value.strip().casefold().split())
    if token in _DECLARED_ACTIVITY_KINDS:
        classification = "declared"
        value = token
    elif token in _ACTIVITY_KIND_ALIASES:
        classification = "normalized_alias"
        value = _ACTIVITY_KIND_ALIASES[token]
    else:
        classification = "unknown"
        value = "unknown"
    return {
        "value": value,
        "raw_value": raw_value or None,
        "classification": classification,
    }


def _activity(activity: IssueActivityProjection) -> dict[str, object]:
    semantic_body = activity.message
    declared_match = _DECLARED_KIND.search(semantic_body)
    if declared_match:
        raw_kind = declared_match.group("assignment") or declared_match.group("suffix")
        if raw_kind is None:  # pragma: no cover - regex groups are exhaustive
            raise ValueError("Declared activity kind is missing")
        semantic_kind = normalize_issue_activity_kind_payload_v1(raw_kind)
        semantic_body = _DECLARED_KIND.sub("", semantic_body).strip()
    else:
        semantic_kind = _infer_activity_kind(semantic_body)
    headline, detail = _headline_detail(semantic_body)
    return {
        "activity_ref": activity.ref,
        "sequence": activity.sequence,
        "message": activity.raw_text,
        "raw_markdown": f"- {activity.raw_text}",
        "headline": headline,
        "detail": detail,
        "actor_execution_id": activity.actor_ref,
        "outcome": activity.outcome,
        "command": activity.command,
        "exit_code": activity.command_exit_code,
        "structural_change_kind": "update_appended",
        "semantic_kind": semantic_kind,
        "activity_at": (
            _normalize_absolute_time(activity.activity_at)
            if activity.activity_at is not None
            else None
        ),
        "time_authority": activity.time_authority.value,
        "references": _references(activity.raw_text),
    }


def _infer_activity_kind(text: str) -> dict[str, object]:
    value = text.casefold()
    inferred: str | None = None
    if re.search(
        r"\bluis\b.{0,80}\b(approved|corrected|directed|transferred|asked)\b",
        value,
    ):
        inferred = "human_direction"
    elif re.search(r"\b(blocked|blocker)\b", value):
        inferred = "blocked"
    elif value.startswith(("closed ", "resolved ")):
        inferred = "resolved"
    elif value.startswith("opened "):
        inferred = "opened"
    elif value.startswith("claimed "):
        inferred = "claimed"
    elif "implementation-ready" in value or "implementation ready" in value:
        inferred = "implementation_ready"
    elif "canonical implementation" in value or re.search(r"\bcommit(?:ted)?\b", value):
        inferred = "commit"
    elif re.search(r"\b(proof|proved|verified|tests? passed)\b", value):
        inferred = "proof"
    elif re.search(r"\b(implemented|implementation)\b", value):
        inferred = "implementation"
    return {
        "value": inferred or "unknown",
        "raw_value": None,
        "classification": "inferred" if inferred is not None else "unknown",
    }


def _attention_candidates(
    activities: list[dict[str, object]],
) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    unresolved: list[int] = []
    for activity in activities:
        semantic_kind = activity["semantic_kind"]
        if not isinstance(semantic_kind, dict):  # pragma: no cover - internal invariant
            raise TypeError("Activity semantic kind is invalid")
        kind = semantic_kind["value"]
        if kind in {"blocked", "human_direction"}:
            candidate_kind = "blocked" if kind == "blocked" else "human_direction"
            activity_ref = str(activity["activity_ref"])
            candidates.append(
                {
                    "candidate_ref": _stable_ref("attention", activity_ref, str(kind)),
                    "kind": candidate_kind,
                    "source_activity_ref": activity_ref,
                    "raised_at": activity["activity_at"],
                    "time_authority": activity["time_authority"],
                    "classification": semantic_kind["classification"],
                    "resolved_at": None,
                    "resolved_by_activity_ref": None,
                }
            )
            unresolved.append(len(candidates) - 1)
        elif kind == "resolved":
            for index in unresolved:
                candidates[index] = {
                    **candidates[index],
                    "resolved_at": activity["activity_at"],
                    "resolved_by_activity_ref": activity["activity_ref"],
                }
            unresolved.clear()
    return candidates


def _headline_detail(text: str) -> tuple[str, str | None]:
    compact = " ".join(part.strip() for part in text.splitlines() if part.strip())
    if not compact:
        return "Activity recorded", None
    match = re.search(r"(?<=[.!?])\s+", compact)
    if match is None:
        return compact, None
    headline = compact[: match.start()].strip()
    detail = compact[match.end() :].strip()
    return headline, detail or None


def _references(text: str) -> list[dict[str, str]]:
    found: list[tuple[str, str]] = []
    for match in _COMMIT_SHA.finditer(text.casefold()):
        found.append(("commit_sha", match.group("sha")))
    for match in _BACKTICK.finditer(text):
        value = match.group("value").strip()
        if _repository_path(value):
            found.append(("repository_path", value))
    return [{"kind": kind, "value": value} for kind, value in dict.fromkeys(found)]


def _repository_path(value: str) -> bool:
    if "/" not in value or value.startswith(("http://", "https://", "/")):
        return False
    path = PurePosixPath(value)
    return ".." not in path.parts and not any(char.isspace() for char in value)


def _normalize_absolute_time(value: str) -> str:
    parsed = datetime.fromisoformat(value.strip())
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must carry an explicit timezone.")
    normalized = parsed.astimezone(UTC).isoformat(timespec="seconds")
    return normalized.replace("+00:00", "Z")


def _token(value: str) -> str:
    return "_".join(value.strip().casefold().replace("-", " ").split())


def _stable_ref(prefix: str, *parts: str) -> str:
    payload = "\x1f".join(parts).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(payload).hexdigest()}"


__all__ = [
    "ISSUE_DEVELOPMENT_READ_PROJECTION_V2_SCHEMA",
    "build_issue_development_read_payload_v2",
    "issue_development_read_payload_v2_from_runtime",
    "normalize_issue_activity_kind_payload_v1",
    "normalize_issue_lifecycle_payload_v1",
]
