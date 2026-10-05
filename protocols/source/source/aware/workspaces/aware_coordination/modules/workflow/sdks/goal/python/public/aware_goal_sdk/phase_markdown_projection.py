"""Lossless legacy Goal Markdown to Phase compatibility projection.

This SDK boundary preserves source snapshots without manufacturing native
Phase lifecycle, Gate observations, work admission, or acceptance authority.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from aware_goal_operational_runtime import GoalLanePhaseGate, GoalPhaseCoordinate

from .markdown_source import GoalMarkdownImportPlan, parse_goal_markdown_import_plan

GOAL_PHASE_MARKDOWN_SCHEMA = "aware.goal.phase-markdown-projection.v1"
GOAL_PHASE_MARKDOWN_AUTHORITY_PROFILE = "markdown_legacy_v1"
LEGACY_GATE_CONTRACT_REF = "aware.goal.phase-gate.profile/legacy_text_v1"
LEGACY_GATE_EVIDENCE_SCHEMA_REF = "aware.goal.phase-gate-evidence/unavailable_v1"


class GoalPhaseMarkdownProjectionError(ValueError):
    """Legacy Goal Markdown cannot be projected without losing identity."""


@dataclass(frozen=True, slots=True)
class GoalLegacyPhaseWorkAssociationProjectionV1:
    issue_ref: str | None
    owner_snapshot: str | None
    time_snapshot: str | None
    receipt_snapshot: str | None
    role: None = None
    disposition: None = None
    admitted_at: None = None
    association_profile: str = "legacy_issue_link_v1"

    def __post_init__(self) -> None:
        _optional_snapshot(self.issue_ref, "issue_ref")
        _optional_snapshot(self.owner_snapshot, "owner_snapshot")
        _optional_snapshot(self.time_snapshot, "time_snapshot")
        _optional_snapshot(self.receipt_snapshot, "receipt_snapshot")
        if (
            self.role is not None
            or self.disposition is not None
            or self.admitted_at is not None
        ):
            raise GoalPhaseMarkdownProjectionError(
                "legacy work cannot claim role, disposition, or admission"
            )
        if self.association_profile != "legacy_issue_link_v1":
            raise GoalPhaseMarkdownProjectionError("unsupported association profile")


@dataclass(frozen=True, slots=True)
class GoalLegacyPhaseProjectionV1:
    coordinate: GoalPhaseCoordinate
    ordinal: int
    gate: GoalLanePhaseGate
    legacy_tick_snapshot: str
    legacy_status_snapshot: str
    work_association: GoalLegacyPhaseWorkAssociationProjectionV1
    native_phase_state: None = None
    gate_observation: None = None
    acceptance_receipt_ref: None = None
    compatibility_profile: str = GOAL_PHASE_MARKDOWN_AUTHORITY_PROFILE

    def __post_init__(self) -> None:
        if type(self.coordinate) is not GoalPhaseCoordinate:
            raise TypeError("coordinate must be GoalPhaseCoordinate")
        if type(self.ordinal) is not int or self.ordinal < 1:
            raise GoalPhaseMarkdownProjectionError("ordinal must be positive")
        if type(self.gate) is not GoalLanePhaseGate:
            raise TypeError("gate must be GoalLanePhaseGate")
        if (
            self.gate.gate_key != "legacy-gate"
            or self.gate.gate_contract_ref != LEGACY_GATE_CONTRACT_REF
            or self.gate.evidence_schema_ref != LEGACY_GATE_EVIDENCE_SCHEMA_REF
            or self.gate.invariant_refs
            != (
                "invariant:issue-closure-does-not-accept-phase",
                "invariant:legacy-lifecycle-is-source-snapshot",
            )
            or self.gate.semantic_revision != 1
        ):
            raise GoalPhaseMarkdownProjectionError(
                "legacy Phase Gate differs from compatibility profile"
            )
        _snapshot(self.legacy_tick_snapshot, "legacy_tick_snapshot")
        _snapshot(self.legacy_status_snapshot, "legacy_status_snapshot")
        if (
            type(self.work_association)
            is not GoalLegacyPhaseWorkAssociationProjectionV1
        ):
            raise TypeError(
                "work_association must be GoalLegacyPhaseWorkAssociationProjectionV1"
            )
        if (
            self.native_phase_state is not None
            or self.gate_observation is not None
            or self.acceptance_receipt_ref is not None
        ):
            raise GoalPhaseMarkdownProjectionError(
                "legacy projection cannot claim native Phase authority"
            )
        if self.compatibility_profile != GOAL_PHASE_MARKDOWN_AUTHORITY_PROFILE:
            raise GoalPhaseMarkdownProjectionError("unsupported compatibility profile")

    @property
    def phase_key(self) -> str:
        return self.coordinate.phase_key


@dataclass(frozen=True, slots=True)
class GoalLegacyLaneProjectionV1:
    lane_key: str
    role_snapshot: str | None
    status_snapshot: str
    current_issue_snapshot: str | None
    owner_snapshot: str | None
    since_snapshot: str | None
    receipt_snapshot: str | None
    scope_snapshot: str | None
    phases: tuple[GoalLegacyPhaseProjectionV1, ...]

    def __post_init__(self) -> None:
        _snapshot(self.lane_key, "lane_key")
        _optional_snapshot(self.role_snapshot, "role_snapshot")
        _snapshot(self.status_snapshot, "status_snapshot")
        _optional_snapshot(self.current_issue_snapshot, "current_issue_snapshot")
        _optional_snapshot(self.owner_snapshot, "owner_snapshot")
        _optional_snapshot(self.since_snapshot, "since_snapshot")
        _optional_snapshot(self.receipt_snapshot, "receipt_snapshot")
        _optional_snapshot(self.scope_snapshot, "scope_snapshot")
        if type(self.phases) is not tuple:
            raise TypeError("phases must be exact tuple")
        for phase in self.phases:
            if type(phase) is not GoalLegacyPhaseProjectionV1:
                raise TypeError("phases must contain GoalLegacyPhaseProjectionV1")


@dataclass(frozen=True, slots=True)
class GoalPhaseMarkdownProjectionV1:
    goal_tag: str
    title: str
    status_snapshot: str
    priority_snapshot: str
    source_sha256: str
    source_markdown: str
    source_path: str | None
    lanes: tuple[GoalLegacyLaneProjectionV1, ...]
    schema_id: str = GOAL_PHASE_MARKDOWN_SCHEMA
    authority_profile: str = GOAL_PHASE_MARKDOWN_AUTHORITY_PROFILE

    def __post_init__(self) -> None:
        if self.schema_id != GOAL_PHASE_MARKDOWN_SCHEMA:
            raise GoalPhaseMarkdownProjectionError("unsupported projection schema")
        if self.authority_profile != GOAL_PHASE_MARKDOWN_AUTHORITY_PROFILE:
            raise GoalPhaseMarkdownProjectionError("unsupported authority profile")
        _snapshot(self.goal_tag, "goal_tag")
        if not self.goal_tag.startswith("goal/"):
            raise GoalPhaseMarkdownProjectionError("goal_tag must start with goal/")
        _snapshot(self.title, "title")
        _snapshot(self.status_snapshot, "status_snapshot")
        _snapshot(self.priority_snapshot, "priority_snapshot")
        if type(self.source_markdown) is not str:
            raise TypeError("source_markdown must be exact str")
        _optional_snapshot(self.source_path, "source_path")
        if type(self.lanes) is not tuple:
            raise TypeError("lanes must be exact tuple")
        expected = (
            "sha256:" + hashlib.sha256(self.source_markdown.encode("utf-8")).hexdigest()
        )
        if self.source_sha256 != expected:
            raise GoalPhaseMarkdownProjectionError(
                "source digest does not match Markdown"
            )
        coordinates: set[GoalPhaseCoordinate] = set()
        lane_keys: set[str] = set()
        for lane in self.lanes:
            if type(lane) is not GoalLegacyLaneProjectionV1:
                raise TypeError("lanes must contain GoalLegacyLaneProjectionV1")
            if lane.lane_key in lane_keys:
                raise GoalPhaseMarkdownProjectionError("duplicate legacy lane key")
            lane_keys.add(lane.lane_key)
            for phase in lane.phases:
                if phase.coordinate.lane_key != lane.lane_key:
                    raise GoalPhaseMarkdownProjectionError(
                        "Phase coordinate does not match containing lane"
                    )
                if phase.coordinate in coordinates:
                    raise GoalPhaseMarkdownProjectionError(
                        "duplicate legacy Phase coordinate"
                    )
                coordinates.add(phase.coordinate)
                if phase.coordinate.goal_tag != self.goal_tag:
                    raise GoalPhaseMarkdownProjectionError(
                        "Phase coordinate does not match containing Goal"
                    )
        plan = parse_goal_markdown_import_plan(
            self.source_markdown,
            source_path=self.source_path,
        )
        expected_lanes = _legacy_lanes_from_plan(plan)
        if (
            self.goal_tag != plan.goal_tag
            or self.title != plan.title
            or self.status_snapshot != plan.status_snapshot
            or self.priority_snapshot != plan.priority_level_token
            or self.lanes != expected_lanes
        ):
            raise GoalPhaseMarkdownProjectionError(
                "derived projection does not match bound source Markdown"
            )

    @property
    def phases(self) -> tuple[GoalLegacyPhaseProjectionV1, ...]:
        return tuple(phase for lane in self.lanes for phase in lane.phases)


def load_goal_phase_markdown_projection(
    path: str | Path,
) -> GoalPhaseMarkdownProjectionV1:
    source_path = Path(path)
    source_bytes = source_path.read_bytes()
    return project_goal_phase_markdown(
        source_bytes.decode("utf-8"),
        source_path=source_path.as_posix(),
    )


def project_goal_phase_markdown(
    markdown: str,
    *,
    source_path: str | None = None,
) -> GoalPhaseMarkdownProjectionV1:
    if type(markdown) is not str:
        raise TypeError("markdown must be exact str")
    plan = parse_goal_markdown_import_plan(markdown, source_path=source_path)
    return _projection_from_plan(plan=plan, source_markdown=markdown)


def render_goal_phase_markdown_v1(
    projection: GoalPhaseMarkdownProjectionV1,
) -> str:
    """Return the exact compatibility source, including append-only history."""

    _ = _projection(projection)
    return projection.source_markdown


def render_goal_phase_markdown_v2(
    projection: GoalPhaseMarkdownProjectionV1,
) -> str:
    """Render a deterministic non-authoritative Phase-shaped companion view."""

    projection = _projection(projection)
    lines = [
        f"# Goal Phase Projection: {projection.title}",
        "",
        f"- Tag: `{projection.goal_tag}`",
        f"- Schema: `{projection.schema_id}`",
        f"- Authority Profile: `{projection.authority_profile}`",
        f"- Source SHA-256: `{projection.source_sha256}`",
        "- Native Phase Authority: `unavailable`",
        "",
        "## Lane Phases",
        "",
    ]
    for lane in projection.lanes:
        lines.extend(_render_lane_v2(lane))
    return "\n".join(lines).rstrip() + "\n"


def _projection_from_plan(
    *,
    plan: GoalMarkdownImportPlan,
    source_markdown: str,
) -> GoalPhaseMarkdownProjectionV1:
    lanes = _legacy_lanes_from_plan(plan)
    return GoalPhaseMarkdownProjectionV1(
        goal_tag=plan.goal_tag,
        title=plan.title,
        status_snapshot=plan.status_snapshot,
        priority_snapshot=plan.priority_level_token,
        source_sha256="sha256:" + hashlib.sha256(source_markdown.encode()).hexdigest(),
        source_markdown=source_markdown,
        source_path=plan.source_path,
        lanes=lanes,
    )


def _legacy_lanes_from_plan(
    plan: GoalMarkdownImportPlan,
) -> tuple[GoalLegacyLaneProjectionV1, ...]:
    rows_by_lane: dict[str, list[GoalLegacyPhaseProjectionV1]] = {
        lane.lane_key: [] for lane in plan.lanes
    }
    for row in plan.lane_issues:
        gate = GoalLanePhaseGate(
            gate_key="legacy-gate",
            promise=row.gate,
            gate_contract_ref=LEGACY_GATE_CONTRACT_REF,
            evidence_schema_ref=LEGACY_GATE_EVIDENCE_SCHEMA_REF,
            invariant_refs=(
                "invariant:issue-closure-does-not-accept-phase",
                "invariant:legacy-lifecycle-is-source-snapshot",
            ),
        )
        rows_by_lane.setdefault(row.lane_key, []).append(
            GoalLegacyPhaseProjectionV1(
                coordinate=GoalPhaseCoordinate(
                    goal_tag=plan.goal_tag,
                    lane_key=row.lane_key,
                    phase_key=row.row_key,
                ),
                ordinal=row.row_number,
                gate=gate,
                legacy_tick_snapshot=row.tick_token,
                legacy_status_snapshot=row.status_snapshot,
                work_association=GoalLegacyPhaseWorkAssociationProjectionV1(
                    issue_ref=row.issue_ref or row.planned_issue_tag,
                    owner_snapshot=row.owner_execution_id,
                    time_snapshot=row.sync_time_snapshot,
                    receipt_snapshot=row.receipt_ref,
                ),
            )
        )
    return tuple(
        GoalLegacyLaneProjectionV1(
            lane_key=lane.lane_key,
            role_snapshot=lane.role_label or lane.role_key,
            status_snapshot=lane.status_token,
            current_issue_snapshot=lane.current_issue_tag,
            owner_snapshot=lane.owner_execution_id,
            since_snapshot=lane.since_snapshot,
            receipt_snapshot=lane.last_receipt_ref,
            scope_snapshot=lane.scope,
            phases=tuple(rows_by_lane.get(lane.lane_key, ())),
        )
        for lane in plan.lanes
    )


def _projection(
    value: GoalPhaseMarkdownProjectionV1,
) -> GoalPhaseMarkdownProjectionV1:
    if type(value) is not GoalPhaseMarkdownProjectionV1:
        raise TypeError("projection must be GoalPhaseMarkdownProjectionV1")
    value.__post_init__()
    return value


def _render_lane_v2(lane: GoalLegacyLaneProjectionV1) -> list[str]:
    lines = [
        f"### {_cell(lane.lane_key)}",
        "",
        (
            "| Ordinal | Phase | Legacy Tick | Legacy Status | Gate Profile | "
            + "Gate Digest | Gate | Issue Snapshot | Owner Snapshot | Time Snapshot | "
            + "Receipt Snapshot | Gate Observation | Native Phase State |"
        ),
        "| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for phase in lane.phases:
        work = phase.work_association
        lines.append(
            " | ".join(
                [
                    f"| {_cell(phase.ordinal)}",
                    _cell(phase.phase_key),
                    _cell(phase.legacy_tick_snapshot),
                    _cell(phase.legacy_status_snapshot),
                    _cell(phase.compatibility_profile),
                    _cell(phase.gate.gate_digest),
                    _cell(phase.gate.promise),
                    _cell(work.issue_ref),
                    _cell(work.owner_snapshot),
                    _cell(work.time_snapshot),
                    _cell(work.receipt_snapshot),
                    "not_evaluated",
                    "unavailable |",
                ]
            )
        )
    if not lane.phases:
        lines.append(
            "| - | - | - | - | markdown_legacy_v1 | - | - | - | - | - | - | "
            + "not_evaluated | unavailable |"
        )
    lines.append("")
    return lines


def _cell(value: object | None) -> str:
    if value is None:
        return "-"
    return str(value).replace("|", "\\|").replace("\n", " ")


def _snapshot(value: object, field_name: str) -> None:
    if type(value) is not str or not value:
        raise GoalPhaseMarkdownProjectionError(
            f"{field_name} must be exact non-empty text"
        )


def _optional_snapshot(value: object | None, field_name: str) -> None:
    if value is None:
        return
    _snapshot(value, field_name)


__all__ = [
    "GOAL_PHASE_MARKDOWN_AUTHORITY_PROFILE",
    "GOAL_PHASE_MARKDOWN_SCHEMA",
    "GoalLegacyLaneProjectionV1",
    "GoalLegacyPhaseProjectionV1",
    "GoalLegacyPhaseWorkAssociationProjectionV1",
    "GoalPhaseMarkdownProjectionError",
    "GoalPhaseMarkdownProjectionV1",
    "load_goal_phase_markdown_projection",
    "project_goal_phase_markdown",
    "render_goal_phase_markdown_v1",
    "render_goal_phase_markdown_v2",
]
