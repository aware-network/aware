"""Neutral structural Project content; decoding NEVER establishes authority.

Namespace, branch, caller, source epoch and actionable target joins belong to
the independently issued outer observation. No such fields are minted here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, cast
import unicodedata

from aware_goal_operational_runtime.identity import normalize_goal_tag

CONTENT_SCHEMA = "aware.workflow.project.goals.content.v1"
SOURCE_SCHEMA = "aware.project.context.v1"
PRIORITIES = frozenset({"critical", "high", "low", "medium", "urgent"})
STATUSES = frozenset({"archived", "cancelled", "finished_failed", "finished_succeeded",
                      "initializing", "paused", "queued", "running"})
OUTCOMES = frozenset({"available", "unselected", "absent", "denied", "unavailable",
                     "ambiguous", "stale"})
MEMBER_AVAILABILITY = frozenset({"available", "unavailable", "ambiguous", "stale"})
REASONS = {"absent": "project_absent", "denied": "access_denied",
           "unavailable": "source_unavailable", "ambiguous": "source_ambiguous",
           "stale": "source_stale"}
MAX_MEMBERS = 256
MAX_RECORD_BYTES = 256 * 1024


def text(value: object, field: str, limit: int) -> str:
    if (type(value) is not str or not value.strip() or len(value) > limit
            or any(unicodedata.category(c) in {"Cc", "Cs"} for c in value)):
        raise ValueError(f"invalid {field}")
    return value


def project_key(value: object) -> str:
    key = text(value, "project_key", 128)
    if unicodedata.normalize("NFC", key) != key:
        raise ValueError("project_key must already be NFC")
    return key


def goal_tag(value: object) -> str:
    _ = text(value, "goal_tag", MAX_RECORD_BYTES)
    if type(value) is not str or normalize_goal_tag(value) != value:
        raise ValueError("Goal tag must be exact owner-canonical text")
    return value


def choice(value: object, allowed: frozenset[str], field: str) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"invalid {field}")
    return value


def strict_object(value: object, fields: set[str], label: str) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{label} requires exactly {sorted(fields)}")
    raw = cast(dict[object, object], value)
    if set(raw) != fields:
        raise ValueError(f"{label} requires exactly {sorted(fields)}")
    return cast(dict[str, object], raw)


def bounded_array(value: object, field: str) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{field} must be a bounded array")
    items = cast(list[object], value)
    if len(items) > MAX_MEMBERS:
        raise ValueError(f"{field} exceeds member budget")
    return items


@dataclass(frozen=True, slots=True)
class ProjectMetadataV1:
    project_key: str
    title: str
    priority_level: str
    status: str

    def __post_init__(self) -> None:
        _ = project_key(self.project_key)
        _ = text(self.title, "title", 512)
        _ = choice(self.priority_level, PRIORITIES, "priority_level")
        _ = choice(self.status, STATUSES, "status")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {"project_key": self.project_key, "title": self.title,
                "priority_level": self.priority_level, "status": self.status}

    @classmethod
    def from_wire(cls, value: object) -> ProjectMetadataV1:
        v = strict_object(value, {"project_key", "title", "priority_level", "status"}, "Project metadata")
        return cls(project_key(v["project_key"]), text(v["title"], "title", 512),
                   choice(v["priority_level"], PRIORITIES, "priority_level"),
                   choice(v["status"], STATUSES, "status"))


@dataclass(frozen=True, slots=True)
class ProjectContextRecordV1:
    project: ProjectMetadataV1
    goal_tags: tuple[str, ...]
    schema_id: ClassVar[str] = SOURCE_SCHEMA

    def __post_init__(self) -> None:
        if type(self.project) is not ProjectMetadataV1:
            raise ValueError("exact Project metadata required")
        self.project.__post_init__()
        if type(self.goal_tags) is not tuple or len(self.goal_tags) > MAX_MEMBERS:
            raise ValueError("bounded immutable goal_tags required")
        for tag in self.goal_tags:
            _ = goal_tag(tag)
        if len(set(self.goal_tags)) != len(self.goal_tags):
            raise ValueError("duplicate Goal membership")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {"schema_id": SOURCE_SCHEMA, **self.project.to_wire(), "goal_tags": list(self.goal_tags)}

    @classmethod
    def from_wire(cls, value: object) -> ProjectContextRecordV1:
        v = strict_object(value, {"schema_id", "project_key", "title", "priority_level", "status", "goal_tags"}, "Project source")
        if v["schema_id"] != SOURCE_SCHEMA or type(v["schema_id"]) is not str:
            raise ValueError("unsupported Project source schema")
        tags = bounded_array(v["goal_tags"], "goal_tags")
        metadata = ProjectMetadataV1.from_wire({key: v[key] for key in
                                               ("project_key", "title", "priority_level", "status")})
        return cls(metadata, tuple(goal_tag(tag) for tag in tags))


@dataclass(frozen=True, slots=True)
class ProjectGoalLabelV1:
    goal_tag: str
    title: str | None
    availability: str

    def __post_init__(self) -> None:
        _ = goal_tag(self.goal_tag)
        _ = choice(self.availability, MEMBER_AVAILABILITY, "availability")
        if self.title is not None:
            _ = text(self.title, "Goal title", 512)
        if self.availability == "available" and self.title is None:
            raise ValueError("available member needs an independently disclosed title")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {"goal_tag": self.goal_tag, "title": self.title, "availability": self.availability}

    @classmethod
    def from_wire(cls, value: object) -> ProjectGoalLabelV1:
        v = strict_object(value, {"goal_tag", "title", "availability"}, "Goal label")
        title = None if v["title"] is None else text(v["title"], "Goal title", 512)
        return cls(goal_tag(v["goal_tag"]), title, choice(v["availability"], MEMBER_AVAILABILITY, "availability"))


@dataclass(frozen=True, slots=True)
class ProjectGoalsContentV1:
    outcome: str
    reason_code: str | None
    project: ProjectMetadataV1 | None
    coverage: str | None
    goals: tuple[ProjectGoalLabelV1, ...]
    schema_id: ClassVar[str] = CONTENT_SCHEMA

    def __post_init__(self) -> None:
        _ = choice(self.outcome, OUTCOMES, "outcome")
        if type(self.goals) is not tuple or len(self.goals) > MAX_MEMBERS:
            raise ValueError("bounded immutable goals required")
        for member in self.goals:
            if type(member) is not ProjectGoalLabelV1:
                raise ValueError("exact Goal label required")
            member.__post_init__()
        tags = tuple(member.goal_tag for member in self.goals)
        if len(set(tags)) != len(tags):
            raise ValueError("duplicate Goal labels")
        if self.project is not None:
            if type(self.project) is not ProjectMetadataV1:
                raise ValueError("exact Project metadata required")
            self.project.__post_init__()
        if self.outcome in {"available", "stale"}:
            if self.project is None:
                raise ValueError("displayed content requires Project metadata")
            _ = choice(self.coverage, frozenset({"complete", "filtered"}), "coverage")
        elif self.project is not None or self.coverage is not None or self.goals:
            raise ValueError("non-disclosing outcome carries Project data")
        if self.outcome in {"available", "unselected"}:
            if self.reason_code is not None:
                raise ValueError("unexpected reason_code")
        elif self.reason_code != REASONS[self.outcome] or type(self.reason_code) is not str:
            raise ValueError("reason_code contradicts outcome")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {"schema_id": CONTENT_SCHEMA, "outcome": self.outcome,
                "reason_code": self.reason_code,
                "project": None if self.project is None else self.project.to_wire(),
                "coverage": self.coverage, "goals": [m.to_wire() for m in self.goals]}

    @classmethod
    def from_wire(cls, value: object) -> ProjectGoalsContentV1:
        v = strict_object(value, {"schema_id", "outcome", "reason_code", "project", "coverage", "goals"}, "Project content")
        if v["schema_id"] != CONTENT_SCHEMA or type(v["schema_id"]) is not str:
            raise ValueError("unsupported Project content schema")
        members = bounded_array(v["goals"], "goals")
        outcome = choice(v["outcome"], OUTCOMES, "outcome")
        reason = None if v["reason_code"] is None else choice(
            v["reason_code"], frozenset(REASONS.values()), "reason_code")
        coverage = None if v["coverage"] is None else choice(
            v["coverage"], frozenset({"complete", "filtered"}), "coverage")
        # Reconstruct detached values only; no source/target authority is issued.
        return cls(outcome, reason,
                   None if v["project"] is None else ProjectMetadataV1.from_wire(v["project"]),
                   coverage, tuple(ProjectGoalLabelV1.from_wire(m) for m in members))
