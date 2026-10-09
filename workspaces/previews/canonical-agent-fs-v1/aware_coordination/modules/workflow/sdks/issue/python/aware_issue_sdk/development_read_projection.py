"""Development read facets over the canonical Issue runtime projection."""

from __future__ import annotations

from typing import ClassVar, Literal

from aware_issue_runtime import (
    ISSUE_DEVELOPMENT_READ_PROJECTION_V2_SCHEMA,
    IssueReadProjection,
    build_issue_development_read_payload_v2,
    issue_development_read_payload_v2_from_runtime,
    normalize_issue_activity_kind_payload_v1,
    normalize_issue_lifecycle_payload_v1,
)
from pydantic import BaseModel, ConfigDict

Classification = Literal["declared", "normalized_alias", "inferred", "unknown"]
TimeAuthority = Literal[
    "commit_receipt",
    "issue_service",
    "source_declared",
    "source_observed",
    "unavailable",
]

class _FrozenProjection(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")


class ClassifiedValueV1(_FrozenProjection):
    value: str
    raw_value: str | None = None
    classification: Classification


class IssueDevelopmentIdentityV2(_FrozenProjection):
    issue_ref: str
    title: str
    slug: str | None = None
    tag: str | None = None
    lifecycle: ClassifiedValueV1
    priority: str | None = None
    owner_execution_id: str | None = None
    goal_ref: str | None = None
    source_description: str | None = None
    ownership_scope: tuple[str, ...] = ()


class IssueDevelopmentListItemV2(_FrozenProjection):
    sequence: int
    text: str
    checked: bool | None = None
    raw_markdown: str | None = None


class IssueDevelopmentReferenceV2(_FrozenProjection):
    kind: Literal["commit_sha", "repository_path"]
    value: str


class IssueDevelopmentActivityV2(_FrozenProjection):
    activity_ref: str
    sequence: int
    message: str
    raw_markdown: str
    headline: str
    detail: str | None = None
    actor_execution_id: str | None = None
    outcome: str | None = None
    command: str | None = None
    exit_code: int | None = None
    structural_change_kind: Literal["update_appended"] = "update_appended"
    semantic_kind: ClassifiedValueV1
    activity_at: str | None = None
    time_authority: TimeAuthority
    references: tuple[IssueDevelopmentReferenceV2, ...] = ()


class IssueDevelopmentAttentionCandidateV2(_FrozenProjection):
    candidate_ref: str
    kind: Literal["blocked", "human_direction"]
    source_activity_ref: str
    raised_at: str | None = None
    time_authority: TimeAuthority
    classification: Classification
    resolved_at: str | None = None
    resolved_by_activity_ref: str | None = None


class IssueDevelopmentAdditionalSectionV2(_FrozenProjection):
    sequence: int
    heading: str
    raw_lines: tuple[str, ...] = ()


class IssueDevelopmentSourceV2(_FrozenProjection):
    path: str
    digest: str
    raw_markdown: str
    observed_at: str
    observation_time_authority: Literal["source_observed"] = "source_observed"


class IssueDevelopmentLatestActivityV2(_FrozenProjection):
    sequence: int | None = None
    activity_ref: str | None = None
    activity_at: str | None = None
    time_authority: TimeAuthority = "unavailable"


class IssueDevelopmentReadProjectionV2(_FrozenProjection):
    schema_ref: Literal["aware.coordination.issue-development-read-projection.v2"] = (
        ISSUE_DEVELOPMENT_READ_PROJECTION_V2_SCHEMA
    )
    projection_revision: str
    identity: IssueDevelopmentIdentityV2
    problem_items: tuple[IssueDevelopmentListItemV2, ...] = ()
    goal_items: tuple[IssueDevelopmentListItemV2, ...] = ()
    acceptance_items: tuple[IssueDevelopmentListItemV2, ...] = ()
    activities: tuple[IssueDevelopmentActivityV2, ...] = ()
    attention_candidates: tuple[IssueDevelopmentAttentionCandidateV2, ...] = ()
    evidence_refs: tuple[IssueDevelopmentListItemV2, ...] = ()
    resolution: str | None = None
    additional_sections: tuple[IssueDevelopmentAdditionalSectionV2, ...] = ()
    source: IssueDevelopmentSourceV2
    latest_activity: IssueDevelopmentLatestActivityV2
    canonical_receipt_coordinates: tuple[str, ...] = ()


def build_issue_development_read_projection_v2(
    *,
    content_text: str,
    source_path: str,
    source_observed_at: str,
) -> IssueDevelopmentReadProjectionV2:
    """Adapt the Issue runtime projection; never implement another parser."""

    return IssueDevelopmentReadProjectionV2.model_validate(
        build_issue_development_read_payload_v2(
            content_text=content_text,
            source_path=source_path,
            source_observed_at=source_observed_at,
        )
    )


def issue_development_read_projection_v2_from_runtime(
    projection: IssueReadProjection,
    *,
    raw_lifecycle: str | None,
) -> IssueDevelopmentReadProjectionV2:
    """Add Development reading facets to one Issue runtime projection."""

    return IssueDevelopmentReadProjectionV2.model_validate(
        issue_development_read_payload_v2_from_runtime(
            projection,
            raw_lifecycle=raw_lifecycle,
        )
    )


def normalize_issue_lifecycle_v1(raw_value: str | None) -> ClassifiedValueV1:
    """Normalize lifecycle while preserving authored vocabulary provenance."""

    return ClassifiedValueV1.model_validate(
        normalize_issue_lifecycle_payload_v1(raw_value)
    )


def normalize_issue_activity_kind_v1(raw_value: str) -> ClassifiedValueV1:
    """Normalize an explicitly declared activity kind through the V1 table."""

    return ClassifiedValueV1.model_validate(
        normalize_issue_activity_kind_payload_v1(raw_value)
    )


__all__ = [
    "ISSUE_DEVELOPMENT_READ_PROJECTION_V2_SCHEMA",
    "ClassifiedValueV1",
    "IssueDevelopmentActivityV2",
    "IssueDevelopmentAdditionalSectionV2",
    "IssueDevelopmentAttentionCandidateV2",
    "IssueDevelopmentIdentityV2",
    "IssueDevelopmentLatestActivityV2",
    "IssueDevelopmentListItemV2",
    "IssueDevelopmentReadProjectionV2",
    "IssueDevelopmentReferenceV2",
    "IssueDevelopmentSourceV2",
    "build_issue_development_read_projection_v2",
    "issue_development_read_projection_v2_from_runtime",
    "normalize_issue_activity_kind_v1",
    "normalize_issue_lifecycle_v1",
]
