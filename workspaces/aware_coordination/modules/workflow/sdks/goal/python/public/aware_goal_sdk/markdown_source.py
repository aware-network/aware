from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast


class GoalMarkdownImportError(ValueError):
    pass


class GoalMarkdownAdmissionError(GoalMarkdownImportError):
    """Strict Goal-record refusal with stable diagnostics."""

    def __init__(self, diagnostics: Sequence[str]) -> None:
        self.diagnostics: tuple[str, ...] = tuple(diagnostics)
        super().__init__("; ".join(self.diagnostics))


@dataclass(frozen=True, slots=True)
class GoalMarkdownLaneSeed:
    lane_key: str
    role_key: str | None = None
    role_label: str | None = None
    owner_execution_id: str | None = None
    status_token: str = "planned"
    current_issue_tag: str | None = None
    since_snapshot: str | None = None
    last_receipt_ref: str | None = None
    scope: str | None = None

    def to_json(self) -> dict[str, object]:
        return _dataclass_payload(self)


@dataclass(frozen=True, slots=True)
class GoalMarkdownLaneIssueSeed:
    lane_key: str
    row_key: str
    gate: str
    row_number: int = 0
    sync_time_snapshot: str | None = None
    issue_ref: str | None = None
    planned_issue_tag: str | None = None
    tick_token: str = "planned"
    status_snapshot: str = "Planned"
    owner_execution_id: str | None = None
    receipt_ref: str | None = None

    def to_json(self) -> dict[str, object]:
        return _dataclass_payload(self)


@dataclass(frozen=True, slots=True)
class GoalMarkdownImportPlan:
    goal_tag: str
    title: str
    priority_level_token: str = "medium"
    status_snapshot: str = "proposed"
    source_path: str | None = None
    source_sha256: str | None = None
    lanes: tuple[GoalMarkdownLaneSeed, ...] = ()
    lane_issues: tuple[GoalMarkdownLaneIssueSeed, ...] = ()

    def to_json(self) -> dict[str, object]:
        return {
            "goal_tag": self.goal_tag,
            "title": self.title,
            "priority_level_token": self.priority_level_token,
            "status_snapshot": self.status_snapshot,
            "source_path": self.source_path,
            "source_sha256": self.source_sha256,
            "lanes": [lane.to_json() for lane in self.lanes],
            "lane_issues": [issue.to_json() for issue in self.lane_issues],
        }


def load_goal_markdown_import_plan(path: str | Path) -> GoalMarkdownImportPlan:
    source_path = Path(path)
    markdown = source_path.read_text(encoding="utf-8")
    return parse_goal_markdown_import_plan(
        markdown,
        source_path=source_path.as_posix(),
    )


def parse_goal_markdown_import_plan(
    markdown: str,
    *,
    source_path: str | None = None,
) -> GoalMarkdownImportPlan:
    metadata = _goal_metadata(markdown, source_path=source_path)
    tables = _markdown_tables(markdown)
    lanes = _lane_seeds(tables)
    lane_issues = _lane_issue_seeds(tables)
    lanes = _merge_missing_lanes(lanes=lanes, lane_issues=lane_issues)
    return GoalMarkdownImportPlan(
        goal_tag=metadata["tag"],
        title=metadata["title"],
        priority_level_token=metadata["priority"],
        status_snapshot=metadata["status"],
        source_path=source_path,
        source_sha256=hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        lanes=lanes,
        lane_issues=lane_issues,
    )


def declared_goal_refs(markdown: str) -> tuple[str, ...]:
    """Return explicitly authored Goal tags without path inference."""

    return tuple(
        tag for tag in _goal_tag_declarations(markdown) if tag is not None
    )


def admit_goal_markdown_import_plan(
    markdown: str,
    *,
    expected_goal_ref: str,
    source_path: str,
) -> GoalMarkdownImportPlan:
    """Strictly admit one canonical Markdown Goal before view lowering.

    The compatibility parser remains permissive for migration/import use. This
    entrance rejects every structural repair that parser would otherwise make.
    """

    diagnostics: list[str] = []
    expected = expected_goal_ref.strip()
    if expected != expected_goal_ref or re.fullmatch(
        r"goal/\d{4}-\d{2}-\d{2}/[a-z0-9]+(?:-[a-z0-9]+)*",
        expected,
    ) is None:
        diagnostics.append("goal_ref_invalid")

    tag_declarations = _goal_tag_declarations(markdown)
    if not tag_declarations or tag_declarations[0] is None:
        diagnostics.append("goal_identity_missing")
    if len(tag_declarations) > 1:
        diagnostics.append("goal_identity_duplicate")
    elif (
        tag_declarations
        and tag_declarations[0] is not None
        and tag_declarations[0] != expected
    ):
        diagnostics.append("goal_identity_mismatch")

    path_ref = _goal_tag_from_path(source_path)
    if path_ref is None:
        diagnostics.append("goal_source_path_noncanonical")
    elif path_ref != expected:
        diagnostics.append("goal_source_path_identity_mismatch")

    try:
        tables = _markdown_tables(markdown)
    except GoalMarkdownImportError as error:
        diagnostics.append(f"goal_structure_malformed:{error}")
        tables = ()
    diagnostics.extend(_strict_structure_diagnostics(tables))
    if diagnostics:
        raise GoalMarkdownAdmissionError(diagnostics)

    plan = parse_goal_markdown_import_plan(markdown, source_path=source_path)
    if plan.goal_tag != expected:
        raise GoalMarkdownAdmissionError(("goal_identity_mismatch",))
    return plan


def _goal_tag_declarations(markdown: str) -> list[str | None]:
    tags: list[str | None] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- ") or ":" not in stripped:
            continue
        key, value = stripped[2:].split(":", 1)
        if _column_key(key) != "tag":
            continue
        tags.append(_value_or_none(value))
    return tags


def _strict_structure_diagnostics(
    tables: Sequence[_MarkdownTable],
) -> tuple[str, ...]:
    diagnostics: list[str] = []
    lane_tables = [
        table for table in tables if _section_key(table.section) == "lane_map"
    ]
    if len(lane_tables) > 1:
        diagnostics.append("goal_lane_map_duplicate")
    lane_keys: list[str] = []
    for table in lane_tables:
        for row in table.rows:
            lane_key = row.get("lane")
            if lane_key is None:
                diagnostics.append("goal_lane_key_missing")
            else:
                lane_keys.append(lane_key)
    if len(lane_keys) != len(set(lane_keys)):
        diagnostics.append("goal_lane_key_duplicate")

    seen_rows: set[tuple[str, str]] = set()
    next_step_by_lane: dict[str, int] = {}
    for table in tables:
        section_key = _section_key(table.section)
        if section_key not in {"issue_matrix", "lane_issues", "lane_sequences"}:
            continue
        for row in table.rows:
            lane_key = row.get("lane") or table.heading
            if not lane_key:
                diagnostics.append("goal_lane_issue_lane_missing")
                continue
            if lane_key not in lane_keys:
                diagnostics.append(f"goal_lane_issue_lane_unmapped:{lane_key}")
            row_key = row.get("key")
            if not row_key:
                diagnostics.append(f"goal_lane_issue_key_missing:{lane_key}")
            elif (lane_key, row_key) in seen_rows:
                diagnostics.append(f"goal_lane_issue_key_duplicate:{lane_key}:{row_key}")
            else:
                seen_rows.add((lane_key, row_key))
            if row.get("gate") is None:
                diagnostics.append(
                    f"goal_lane_issue_gate_missing:{lane_key}:{row_key or 'unknown'}"
                )
            if section_key == "lane_sequences":
                step, _ = _row_identity(row.get("step"))
                if step <= 0:
                    diagnostics.append(
                        f"goal_lane_issue_step_missing:{lane_key}:{row_key or 'unknown'}"
                    )
                else:
                    expected_step = next_step_by_lane.get(lane_key, 0) + 1
                    if step != expected_step:
                        diagnostics.append(
                            f"goal_lane_issue_step_noncontiguous:{lane_key}:"
                            + f"{row_key or 'unknown'}:expected_{expected_step}:actual_{step}"
                        )
                    next_step_by_lane[lane_key] = step
    return tuple(diagnostics)


def _goal_metadata(
    markdown: str,
    *,
    source_path: str | None,
) -> dict[str, str]:
    title = None
    tag = None
    status = None
    priority = None
    for line in markdown.splitlines():
        stripped = line.strip()
        if title is None and stripped.startswith("# Goal:"):
            title = _clean_cell(stripped.removeprefix("# Goal:"))
            continue
        if not stripped.startswith("- ") or ":" not in stripped:
            continue
        key, value = stripped[2:].split(":", 1)
        normalized_key = _column_key(key)
        if normalized_key == "tag":
            tag = _value_or_none(value)
        elif normalized_key == "status":
            status = _value_or_none(value)
        elif normalized_key == "priority":
            priority = _value_or_none(value)

    if title is None:
        raise GoalMarkdownImportError("Goal Markdown import requires '# Goal: ...'.")
    if tag is None:
        tag = _goal_tag_from_path(source_path)
    if tag is None:
        raise GoalMarkdownImportError("Goal Markdown import requires '- Tag: ...'.")
    return {
        "title": title,
        "tag": tag,
        "status": status or "proposed",
        "priority": priority or "medium",
    }


def _markdown_tables(markdown: str) -> tuple[_MarkdownTable, ...]:
    lines = markdown.splitlines()
    tables: list[_MarkdownTable] = []
    section = ""
    heading = ""
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith("## "):
            section = _clean_cell(stripped.removeprefix("## "))
            heading = ""
            index += 1
            continue
        if stripped.startswith("### "):
            heading = _clean_cell(stripped.removeprefix("### "))
            index += 1
            continue
        if _is_table_start(lines, index):
            table_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index])
                index += 1
            tables.append(_parse_table(table_lines, section=section, heading=heading))
            continue
        index += 1
    return tuple(tables)


def _lane_seeds(tables: Sequence[_MarkdownTable]) -> tuple[GoalMarkdownLaneSeed, ...]:
    lane_table = next(
        (table for table in tables if _section_key(table.section) == "lane_map"),
        None,
    )
    if lane_table is None:
        return ()
    seeds: list[GoalMarkdownLaneSeed] = []
    for row in lane_table.rows:
        lane_key = row.get("lane")
        if lane_key is None:
            continue
        seeds.append(
            GoalMarkdownLaneSeed(
                lane_key=lane_key,
                role_label=row.get("role"),
                owner_execution_id=row.get("owner"),
                status_token=row.get("status") or "planned",
                current_issue_tag=_issue_tag(row.get("current_issue")),
                since_snapshot=row.get("since"),
                last_receipt_ref=row.get("last_receipt"),
                scope=row.get("scope"),
            )
        )
    return tuple(seeds)


def _lane_issue_seeds(
    tables: Sequence[_MarkdownTable],
) -> tuple[GoalMarkdownLaneIssueSeed, ...]:
    seeds: list[GoalMarkdownLaneIssueSeed] = []
    next_step_by_lane: dict[str, int] = {}
    for table in tables:
        section_key = _section_key(table.section)
        if section_key not in {"issue_matrix", "lane_issues", "lane_sequences"}:
            continue
        for row in table.rows:
            lane_key = row.get("lane") or table.heading
            if not lane_key:
                continue
            parsed_step, row_label = _row_identity(row.get("step") or row.get("row"))
            if section_key == "lane_sequences" and parsed_step > 0:
                row_number = parsed_step
            else:
                row_number = next_step_by_lane.get(lane_key, 0) + 1
            next_step_by_lane[lane_key] = max(
                next_step_by_lane.get(lane_key, 0),
                row_number,
            )
            issue_ref = row.get("issue")
            row_key = row.get("key") or row_label or _row_key_from_issue_ref(issue_ref)
            if not row_key:
                row_key = f"row-{row_number}" if row_number > 0 else "lane-issue"
            seeds.append(
                GoalMarkdownLaneIssueSeed(
                    lane_key=lane_key,
                    row_key=row_key,
                    row_number=row_number,
                    sync_time_snapshot=row.get("time"),
                    issue_ref=issue_ref,
                    planned_issue_tag=_issue_tag(issue_ref),
                    gate=row.get("gate") or "TBD",
                    tick_token=row.get("tick") or "planned",
                    status_snapshot=row.get("status") or "Planned",
                    owner_execution_id=row.get("owner"),
                    receipt_ref=row.get("receipt"),
                )
            )
    return tuple(seeds)


def _merge_missing_lanes(
    *,
    lanes: Sequence[GoalMarkdownLaneSeed],
    lane_issues: Sequence[GoalMarkdownLaneIssueSeed],
) -> tuple[GoalMarkdownLaneSeed, ...]:
    existing = {lane.lane_key for lane in lanes}
    merged = list(lanes)
    for issue in lane_issues:
        if issue.lane_key in existing:
            continue
        merged.append(GoalMarkdownLaneSeed(lane_key=issue.lane_key))
        existing.add(issue.lane_key)
    return tuple(merged)


@dataclass(frozen=True, slots=True)
class _MarkdownTable:
    section: str
    heading: str
    headers: tuple[str, ...]
    rows: tuple[dict[str, str], ...]


def _parse_table(
    table_lines: Sequence[str],
    *,
    section: str,
    heading: str,
) -> _MarkdownTable:
    headers = tuple(_column_key(cell) for cell in _split_table_row(table_lines[0]))
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = _split_table_row(line)
        row: dict[str, str] = {}
        for index, header in enumerate(headers):
            if index >= len(cells):
                continue
            value = _value_or_none(cells[index])
            if value is not None:
                row[header] = value
        if row:
            rows.append(row)
    return _MarkdownTable(
        section=section,
        heading=heading,
        headers=headers,
        rows=tuple(rows),
    )


def _is_table_start(lines: Sequence[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    if not lines[index].strip().startswith("|"):
        return False
    separator = lines[index + 1].strip()
    return separator.startswith("|") and "---" in separator


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in stripped:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            current.append(char)
            continue
        if char == "|":
            cells.append(_clean_cell("".join(current)))
            current = []
            continue
        current.append(char)
    cells.append(_clean_cell("".join(current)))
    return cells


def _row_identity(value: str | None) -> tuple[int, str | None]:
    text = _value_or_none(value)
    if text is None:
        return 0, None
    match = re.match(r"^(?P<number>\d+)(?:[.)]\s*(?P<label>.+))?$", text)
    if match is None:
        return 0, _slug_key(text)
    label = match.group("label")
    return int(match.group("number")), _slug_key(label) if label else None


def _row_key_from_issue_ref(issue_ref: str | None) -> str | None:
    text = _value_or_none(issue_ref)
    if text is None:
        return None
    if text.startswith("TBD:"):
        return _slug_key(text.removeprefix("TBD:"))
    name = Path(text).name
    if name.endswith(".md"):
        name = name[:-3]
    name = re.sub(r"^fb-\d{4}-\d{2}-\d{2}-", "", name)
    return _slug_key(name)


def _issue_tag(value: str | None) -> str | None:
    text = _value_or_none(value)
    if text is None:
        return None
    if text.startswith("TBD:") or text.startswith("fb/"):
        return text
    match = re.search(
        r"docs/issues/(\d{4})/(\d{2})/(\d{2})/(fb-\d{4}-\d{2}-\d{2}-.+?)\.md$", text
    )
    if match is None:
        return text
    year, month, day, filename = match.groups()
    slug = re.sub(r"^fb-\d{4}-\d{2}-\d{2}-", "", filename)
    return f"fb/{year}-{month}-{day}/{slug}"


def _goal_tag_from_path(source_path: str | None) -> str | None:
    if source_path is None:
        return None
    match = re.search(
        r"docs/goals/(\d{4})/(\d{2})/(\d{2})/goal-\d{4}-\d{2}-\d{2}-(.+?)\.md$",
        source_path,
    )
    if match is None:
        return None
    year, month, day, slug = match.groups()
    return f"goal/{year}-{month}-{day}/{slug}"


def _column_key(value: str) -> str:
    text = _clean_cell(value).lower()
    text = text.replace("/", " ")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _section_key(value: str) -> str:
    return _column_key(value)


def _clean_cell(value: object | None) -> str:
    text = "" if value is None else str(value).strip()
    text = re.sub(r"^\[(?P<label>.*?)\]\((?P<target>.*?)\)$", r"\g<target>", text)
    if len(text) >= 2 and text.startswith("`") and text.endswith("`"):
        text = text[1:-1].strip()
    return text.replace("\\|", "|").strip()


def _value_or_none(value: object | None) -> str | None:
    text = _clean_cell(value)
    if not text or text in {"-", "None", "`None`"}:
        return None
    return text


def _slug_key(value: str | None) -> str | None:
    text = _value_or_none(value)
    if text is None:
        return None
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return text or None


def _dataclass_payload(
    value: GoalMarkdownLaneSeed | GoalMarkdownLaneIssueSeed,
) -> dict[str, object]:
    payload = cast(dict[str, object], asdict(value))
    return {key: item for key, item in payload.items() if item is not None}


__all__ = [
    "GoalMarkdownAdmissionError",
    "GoalMarkdownImportError",
    "GoalMarkdownImportPlan",
    "GoalMarkdownLaneIssueSeed",
    "GoalMarkdownLaneSeed",
    "admit_goal_markdown_import_plan",
    "declared_goal_refs",
    "load_goal_markdown_import_plan",
    "parse_goal_markdown_import_plan",
]
