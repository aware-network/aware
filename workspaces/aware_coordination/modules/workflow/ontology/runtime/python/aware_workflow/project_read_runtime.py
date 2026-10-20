"""Pure Project membership interpretation; all inputs/results are detached data.

Original providers must qualify source, policy and Goal-reading facts before
calling this reducer for a real View. This module does not verify or issue
those authorities. It performs no I/O, creates no identity/branch/target, and
defines no additional public wire. Existing Project content is the result.
"""

from __future__ import annotations

from dataclasses import dataclass

from .project_read_contract import (
    MAX_MEMBERS,
    OUTCOMES,
    REASONS,
    ProjectContextRecordV1,
    ProjectGoalLabelV1,
    ProjectGoalsContentV1,
    ProjectMetadataV1,
    choice,
    goal_tag,
)

_DISCLOSURES = frozenset({"disclosed", "denied", "unavailable"})


@dataclass(frozen=True, slots=True)
class ProjectGoalReadDisposition:
    """Internal domain facts, not a caller permit or an issued Goal reading.

    ``unavailable`` means disclosure authority is unknown/unavailable, not
    denial. A disclosed member with no reading stays visible as unavailable.
    Denied/unknown members cannot carry a title or Goal reading.
    """

    goal_tag: str
    disclosure: str
    reading: ProjectGoalLabelV1 | None

    def __post_init__(self) -> None:
        _ = goal_tag(self.goal_tag)
        _ = choice(self.disclosure, _DISCLOSURES, "disclosure")
        if self.reading is not None:
            if type(self.reading) is not ProjectGoalLabelV1:
                raise ValueError("exact Goal label required")
            self.reading.__post_init__()
            if self.reading.goal_tag != self.goal_tag:
                raise ValueError("Goal reading belongs to a different member")
            if self.disclosure != "disclosed":
                raise ValueError("undisclosed member cannot carry a Goal reading")


@dataclass(frozen=True, slots=True)
class ProjectReadInput:
    """Internal complete domain input; constructible values confer no authority.

    Available/stale inputs carry exactly one disposition per authored member.
    Other outcomes are non-disclosing and carry no record or member facts.
    """

    outcome: str
    record: ProjectContextRecordV1 | None
    members: tuple[ProjectGoalReadDisposition, ...]

    def __post_init__(self) -> None:
        _ = choice(self.outcome, OUTCOMES, "outcome")
        if type(self.members) is not tuple or len(self.members) > MAX_MEMBERS:
            raise ValueError("bounded immutable member dispositions required")
        for member in self.members:
            if type(member) is not ProjectGoalReadDisposition:
                raise ValueError("exact member disposition required")
            member.__post_init__()
        if self.outcome not in {"available", "stale"}:
            if self.record is not None or self.members:
                raise ValueError("non-disclosing input carries Project data")
            return
        if type(self.record) is not ProjectContextRecordV1:
            raise ValueError("displayed reading requires exact Project record")
        self.record.__post_init__()
        keys = tuple(member.goal_tag for member in self.members)
        if len(set(keys)) != len(keys):
            raise ValueError("duplicate member disposition")
        if set(keys) != set(self.record.goal_tags):
            raise ValueError("member dispositions must equal complete authored membership")


def read_project_goals(reading: ProjectReadInput) -> ProjectGoalsContentV1:
    """Reduce complete domain facts without source or authorization inference.

    Revalidate at consumption and return independent nested values. Unknown
    disclosure refuses a public list as unavailable; it is not filtered away
    as if denial had been established. Stale Project content cannot label a
    member current/available, while other member gaps remain explicit.
    """
    if type(reading) is not ProjectReadInput:
        raise ValueError("exact Project read input required")
    reading.__post_init__()
    if reading.outcome not in {"available", "stale"}:
        return ProjectGoalsContentV1(
            reading.outcome, REASONS.get(reading.outcome), None, None, ()
        )
    # The consumption invariant above requires the record for these outcomes.
    record = reading.record
    if record is None:
        raise ValueError("displayed reading requires Project record")
    if any(member.disclosure == "unavailable" for member in reading.members):
        return ProjectGoalsContentV1("unavailable", REASONS["unavailable"], None, None, ())

    by_key = {member.goal_tag: member for member in reading.members}
    result: list[ProjectGoalLabelV1] = []
    for tag in record.goal_tags:
        member = by_key[tag]
        if member.disclosure == "denied":
            continue
        if member.reading is None:
            result.append(ProjectGoalLabelV1(tag, None, "unavailable"))
            continue
        label = ProjectGoalLabelV1.from_wire(member.reading.to_wire())
        if reading.outcome == "stale" and label.availability == "available":
            label = ProjectGoalLabelV1(label.goal_tag, label.title, "stale")
        result.append(label)
    return ProjectGoalsContentV1(
        outcome=reading.outcome,
        reason_code=REASONS.get(reading.outcome),
        project=ProjectMetadataV1.from_wire(record.project.to_wire()),
        coverage="filtered" if any(m.disclosure == "denied" for m in reading.members) else "complete",
        goals=tuple(result),
    )
