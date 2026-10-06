from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

ISSUE_PROJECTION_SCHEMA_VERSION = "aware.issue.read-projection.v1"


class IssueTimeAuthority(StrEnum):
    COMMIT_RECEIPT = "commit_receipt"
    ISSUE_SERVICE = "issue_service"
    SOURCE_DECLARED = "source_declared"
    SOURCE_OBSERVED = "source_observed"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class IssueSourceHeader:
    field: str
    value: str


@dataclass(frozen=True, slots=True)
class IssueSourceSection:
    heading: str
    lines: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IssueSourceDocument:
    title: str
    headers: tuple[IssueSourceHeader, ...]
    sections: tuple[IssueSourceSection, ...]

    def header(self, field: str) -> str | None:
        for header in self.headers:
            if header.field.casefold() == field.casefold():
                return header.value
        return None

    def matching_sections(self, heading: str) -> tuple[IssueSourceSection, ...]:
        return tuple(
            section
            for section in self.sections
            if section.heading.casefold() == heading.casefold()
        )


@dataclass(frozen=True, slots=True)
class IssueAcceptanceProjection:
    sequence: int
    text: str
    checked: bool
    raw_line: str

    def to_payload(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "text": self.text,
            "checked": self.checked,
            "raw_line": self.raw_line,
        }


@dataclass(frozen=True, slots=True)
class IssueActivityProjection:
    ref: str
    sequence: int
    message: str
    raw_text: str
    actor_ref: str | None
    activity_at: str | None
    time_authority: IssueTimeAuthority
    outcome: str | None = None
    command: str | None = None
    command_exit_code: int | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "ref": self.ref,
            "sequence": self.sequence,
            "message": self.message,
            "raw_text": self.raw_text,
            "actor_ref": self.actor_ref,
            "activity_at": self.activity_at,
            "time_authority": self.time_authority.value,
            "outcome": self.outcome,
            "command": self.command,
            "command_exit_code": self.command_exit_code,
        }


@dataclass(frozen=True, slots=True)
class IssueEvidenceProjection:
    sequence: int
    kind: str
    reference: str
    raw_line: str

    def to_payload(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "kind": self.kind,
            "reference": self.reference,
            "raw_line": self.raw_line,
        }


@dataclass(frozen=True, slots=True)
class IssueAdditionalSectionProjection:
    heading: str
    lines: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {"heading": self.heading, "lines": list(self.lines)}


@dataclass(frozen=True, slots=True)
class IssueReadProjection:
    schema_version: str
    issue_ref: str
    source_path: str
    source_digest: str
    raw_markdown: str
    title: str
    slug: str | None
    tag: str | None
    status: str
    priority: str | None
    owner_ref: str | None
    goal_ref: str | None
    captured: str | None
    source_description: str | None
    ownership_scope: tuple[str, ...]
    problem_items: tuple[str, ...]
    goal_items: tuple[str, ...]
    acceptance_items: tuple[IssueAcceptanceProjection, ...]
    activities: tuple[IssueActivityProjection, ...]
    evidence: tuple[IssueEvidenceProjection, ...]
    resolution: str | None
    additional_sections: tuple[IssueAdditionalSectionProjection, ...]
    observed_at: str | None = None
    observation_time_authority: IssueTimeAuthority = IssueTimeAuthority.UNAVAILABLE
    lane_head_commit_id: str | None = None
    function_call_id: str | None = None

    @property
    def projection_revision(self) -> str:
        return self.source_digest

    def to_payload(self, *, include_raw_markdown: bool = True) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "issue_ref": self.issue_ref,
            "identity": {
                "title": self.title,
                "slug": self.slug,
                "tag": self.tag,
                "status": self.status,
                "priority": self.priority,
                "owner_ref": self.owner_ref,
                "goal_ref": self.goal_ref,
                "captured": self.captured,
                "source_description": self.source_description,
            },
            "content": {
                "problem_items": list(self.problem_items),
                "goal_items": list(self.goal_items),
                "acceptance_items": [
                    item.to_payload() for item in self.acceptance_items
                ],
                "ownership_scope": list(self.ownership_scope),
            },
            "activity": [item.to_payload() for item in self.activities],
            "evidence": [item.to_payload() for item in self.evidence],
            "resolution": self.resolution,
            "additional_sections": [
                section.to_payload() for section in self.additional_sections
            ],
            "source": {
                "path": self.source_path,
                "digest": self.source_digest,
                "raw_markdown": self.raw_markdown if include_raw_markdown else None,
                "observed_at": self.observed_at,
                "time_authority": self.observation_time_authority.value,
            },
            "revision": {
                "projection_revision": self.projection_revision,
                "lane_head_commit_id": self.lane_head_commit_id,
                "function_call_id": self.function_call_id,
            },
        }
