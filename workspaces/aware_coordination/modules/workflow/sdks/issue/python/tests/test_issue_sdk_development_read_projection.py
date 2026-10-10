from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from aware_issue_sdk import (
    ClassifiedValueV1,
    build_issue_development_read_projection_v2,
    normalize_issue_activity_kind_v1,
    normalize_issue_lifecycle_v1,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "contracts/development_read_projection/v2/issue-development-read-projection-v2-fixtures.json"
)


def test_immutable_v2_fixtures_are_byte_exact() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert fixture["schema_ref"] == (
        "aware.coordination.issue-development-read-projection.v2.fixtures"
    )
    assert fixture["fixture_version"] == 1
    for case in fixture["cases"]:
        projection = build_issue_development_read_projection_v2(**case["input"])
        assert projection.model_dump(mode="json") == case["expected_projection"]


def test_unavailable_latest_time_never_falls_back_to_observation() -> None:
    projection = build_issue_development_read_projection_v2(
        content_text=(
            "# Issue: No clock\n\n"
            "- Status: In Progress\n\n"
            "## Updates (append-only)\n"
            "- Continued without a declared time.\n"
        ),
        source_path="docs/issues/2026/08/20/no-clock.md",
        source_observed_at="2026-08-20T07:00:00Z",
    )

    assert projection.latest_activity.activity_at is None
    assert projection.latest_activity.time_authority == "unavailable"
    assert projection.source.observed_at == "2026-08-20T07:00:00Z"
    assert projection.identity.lifecycle.value == "in_progress"


def test_closed_vocabularies_preserve_raw_alias_and_unknown_values() -> None:
    alias = normalize_issue_lifecycle_v1("Inprogress")
    unknown = normalize_issue_lifecycle_v1("Awaiting Product")
    kind_alias = normalize_issue_activity_kind_v1("implementation-ready")

    assert alias.model_dump() == {
        "value": "in_progress",
        "raw_value": "Inprogress",
        "classification": "normalized_alias",
    }
    assert unknown.model_dump() == {
        "value": "unknown",
        "raw_value": "Awaiting Product",
        "classification": "unknown",
    }
    assert kind_alias.model_dump() == {
        "value": "implementation_ready",
        "raw_value": "implementation-ready",
        "classification": "normalized_alias",
    }


def test_projection_is_frozen_and_rejects_untrusted_coordinates() -> None:
    projection = build_issue_development_read_projection_v2(
        content_text="# Issue: Frozen\n",
        source_path="docs/issues/2026/08/20/frozen.md",
        source_observed_at="2026-08-20T07:00:00Z",
    )

    with pytest.raises(ValidationError):
        projection.projection_revision = "changed"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        ClassifiedValueV1.model_validate(
            {"value": "open", "classification": "declared", "extra": True}
        )
    with pytest.raises(ValueError, match=r"canonical.*relative"):
        build_issue_development_read_projection_v2(
            content_text="# Issue: Escape\n",
            source_path="../escape.md",
            source_observed_at="2026-08-20T07:00:00Z",
        )
    with pytest.raises(ValueError, match="explicit timezone"):
        build_issue_development_read_projection_v2(
            content_text="# Issue: Naive\n",
            source_path="docs/issues/naive.md",
            source_observed_at="2026-08-20T07:00:00",
        )


def test_resolution_closes_occurrences_and_later_direction_is_new() -> None:
    projection = build_issue_development_read_projection_v2(
        content_text=(
            "# Issue: Occurrences\n\n"
            "- Status: Blocked\n\n"
            "## Updates (append-only)\n"
            "- 2026-08-20T01:00:00Z — Waiting for evidence. "
            "(activity_kind: `blocked`)\n"
            "- 2026-08-20T01:05:00Z — Evidence arrived. "
            "(activity_kind: `resolved`)\n"
            "- 2026-08-20T01:10:00Z — Luis corrected the boundary. "
            "(activity_kind: `human_direction`)\n"
        ),
        source_path="docs/issues/2026/08/20/occurrences.md",
        source_observed_at="2026-08-20T01:11:00Z",
    )

    first, second = projection.attention_candidates
    assert first.resolved_at == "2026-08-20T01:05:00Z"
    assert first.resolved_by_activity_ref == projection.activities[1].activity_ref
    assert second.kind == "human_direction"
    assert second.resolved_by_activity_ref is None
