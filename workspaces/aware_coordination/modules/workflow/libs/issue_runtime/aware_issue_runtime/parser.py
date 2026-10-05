from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import PurePosixPath

from .contracts import (
    ISSUE_PROJECTION_SCHEMA_VERSION,
    IssueAcceptanceProjection,
    IssueActivityProjection,
    IssueAdditionalSectionProjection,
    IssueEvidenceProjection,
    IssueReadProjection,
    IssueSourceDocument,
    IssueSourceHeader,
    IssueSourceSection,
    IssueTimeAuthority,
)

_HEADER_LINE = re.compile(r"^\s*-\s*([^:]+):\s*(.*)$")
_CHECKLIST_LINE = re.compile(r"^\s*-\s*\[([ xX])\]\s*(.*)$")
_LIST_LINE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)(.*)$")
_ACTIVITY_TIME = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))\s+(?:—|-)\s+(?P<body>.*)$"
)
# The piped form the Aware Updates protocol also uses:
# `<timestamp> | <actor> | <message>`.
_ACTIVITY_PIPED = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2}))\s*\|\s*(?P<actor>[^|]+?)\s*\|\s*(?P<body>.*)$"
)
_TRAILER = re.compile(
    r"\s+\((?P<key>recorder|actor|outcome|command|command exit|exit code):\s*`?(?P<value>[^`)]+)`?\)\s*$",
    re.IGNORECASE,
)
_KNOWN_SECTIONS = {
    "ownership scope",
    "problem",
    "goal",
    "acceptance checklist",
    "verified-by",
    "evidence",
    "updates (append-only)",
    "resolution",
}


def parse_issue_source(text: str) -> IssueSourceDocument:
    title = ""
    headers: list[IssueSourceHeader] = []
    sections: list[IssueSourceSection] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not title and stripped.casefold().startswith("# issue:"):
            title = stripped.split(":", 1)[1].strip()
            continue
        if stripped.startswith("## "):
            if current_heading is not None:
                sections.append(
                    IssueSourceSection(current_heading, tuple(current_lines))
                )
            current_heading = stripped[3:].strip()
            current_lines = []
            continue
        if current_heading is None:
            match = _HEADER_LINE.match(raw_line)
            if match:
                headers.append(
                    IssueSourceHeader(
                        field=match.group(1).strip(),
                        value=_normalize_value(match.group(2)),
                    )
                )
                continue
            if raw_line[:1].isspace() and stripped and headers:
                previous = headers[-1]
                continuation = _normalize_value(stripped)
                headers[-1] = IssueSourceHeader(
                    field=previous.field,
                    value=" ".join(
                        fragment
                        for fragment in (previous.value, continuation)
                        if fragment
                    ),
                )
            continue
        current_lines.append(raw_line.rstrip())

    if current_heading is not None:
        sections.append(IssueSourceSection(current_heading, tuple(current_lines)))
    return IssueSourceDocument(title, tuple(headers), tuple(sections))


def parse_issue_projection(
    *,
    text: str,
    source_path: str,
    observed_at: str | None = None,
) -> IssueReadProjection:
    _validate_source_path(source_path)
    document = parse_issue_source(text)
    digest = f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"
    tag = _optional(document.header("Tag"))
    issue_ref = tag or f"local:{source_path}"
    title = document.title or PurePosixPath(source_path).stem
    activities = _activities(document, issue_ref=issue_ref)
    observed = _optional(observed_at)
    if observed is not None and not _valid_datetime(observed):
        raise ValueError("Issue source observation time must be ISO-8601")
    return IssueReadProjection(
        schema_version=ISSUE_PROJECTION_SCHEMA_VERSION,
        issue_ref=issue_ref,
        source_path=source_path,
        source_digest=digest,
        raw_markdown=text,
        title=title,
        slug=_optional(document.header("Slug")),
        tag=tag,
        status=_status(document.header("Status")),
        priority=_optional(document.header("Priority")),
        owner_ref=_owner(document.header("Owner")),
        goal_ref=_optional(document.header("Goal")),
        captured=_optional(document.header("Captured")),
        source_description=_optional(document.header("Source")),
        ownership_scope=_ownership_scope(document),
        problem_items=_section_items(document, "Problem"),
        goal_items=_section_items(document, "Goal"),
        acceptance_items=_acceptance(document),
        activities=activities,
        evidence=_evidence(document),
        resolution=_resolution(document),
        additional_sections=tuple(
            IssueAdditionalSectionProjection(section.heading, section.lines)
            for section in document.sections
            if section.heading.casefold() not in _KNOWN_SECTIONS
        ),
        observed_at=observed,
        observation_time_authority=(
            IssueTimeAuthority.SOURCE_OBSERVED
            if observed is not None
            else IssueTimeAuthority.UNAVAILABLE
        ),
    )


def _activities(
    document: IssueSourceDocument, *, issue_ref: str
) -> tuple[IssueActivityProjection, ...]:
    rows: list[IssueActivityProjection] = []
    for section in document.matching_sections("Updates (append-only)"):
        for line in section.lines:
            stripped = line.strip()
            if not stripped.startswith("- "):
                continue
            raw_text = stripped[2:].strip()
            if not raw_text:
                continue
            timestamp: str | None = None
            time_authority = IssueTimeAuthority.UNAVAILABLE
            body = raw_text
            piped_actor: str | None = None
            time_match = _ACTIVITY_TIME.match(body)
            piped = None if time_match else _ACTIVITY_PIPED.match(body)
            if time_match and _valid_datetime(time_match.group("timestamp")):
                timestamp = time_match.group("timestamp")
                body = time_match.group("body").strip()
                time_authority = IssueTimeAuthority.SOURCE_DECLARED
            elif piped and _valid_datetime(piped.group("timestamp")):
                timestamp = piped.group("timestamp")
                piped_actor = piped.group("actor").strip() or None
                body = piped.group("body").strip()
                time_authority = IssueTimeAuthority.SOURCE_DECLARED
            trailers: dict[str, str] = {}
            while trailer := _TRAILER.search(body):
                trailers[trailer.group("key").casefold()] = trailer.group(
                    "value"
                ).strip()
                body = body[: trailer.start()].rstrip()
            exit_value = trailers.get("command exit") or trailers.get("exit code")
            try:
                command_exit_code = None if exit_value is None else int(exit_value)
            except ValueError:
                command_exit_code = None
            sequence = len(rows) + 1
            rows.append(
                IssueActivityProjection(
                    ref=f"{issue_ref}#update-{sequence}",
                    sequence=sequence,
                    message=body,
                    raw_text=raw_text,
                    actor_ref=trailers.get("recorder")
                    or trailers.get("actor")
                    or piped_actor,
                    activity_at=timestamp,
                    time_authority=time_authority,
                    outcome=trailers.get("outcome"),
                    command=trailers.get("command"),
                    command_exit_code=command_exit_code,
                )
            )
    return tuple(rows)


def _acceptance(
    document: IssueSourceDocument,
) -> tuple[IssueAcceptanceProjection, ...]:
    rows: list[IssueAcceptanceProjection] = []
    for section in document.matching_sections("Acceptance Checklist"):
        for line in section.lines:
            match = _CHECKLIST_LINE.match(line)
            if match is None:
                continue
            rows.append(
                IssueAcceptanceProjection(
                    sequence=len(rows) + 1,
                    text=match.group(2).strip(),
                    checked=match.group(1).casefold() == "x",
                    raw_line=line,
                )
            )
    return tuple(rows)


def _evidence(document: IssueSourceDocument) -> tuple[IssueEvidenceProjection, ...]:
    rows: list[IssueEvidenceProjection] = []
    for heading, kind in (("Verified-by", "verified_by"), ("Evidence", "evidence")):
        for section in document.matching_sections(heading):
            for line in section.lines:
                match = _LIST_LINE.match(line)
                if match is None:
                    continue
                reference = _normalize_value(match.group(1))
                if reference:
                    rows.append(
                        IssueEvidenceProjection(
                            sequence=len(rows) + 1,
                            kind=kind,
                            reference=reference,
                            raw_line=line,
                        )
                    )
    return tuple(rows)


def _ownership_scope(document: IssueSourceDocument) -> tuple[str, ...]:
    values: list[str] = []
    inline = document.header("Ownership Scope")
    if inline:
        values.extend(_normalize_value(item) for item in inline.split(","))
    for section in document.matching_sections("Ownership Scope"):
        for line in section.lines:
            match = _LIST_LINE.match(line)
            if match:
                values.append(_normalize_value(match.group(1)))
    return tuple(dict.fromkeys(value for value in values if value))


def _section_items(document: IssueSourceDocument, heading: str) -> tuple[str, ...]:
    """A section's list items; a section written as prose gives its
    paragraphs instead, each joined onto one line."""

    values: list[str] = []
    for section in document.matching_sections(heading):
        items = [
            match.group(1).strip()
            for line in section.lines
            if (match := _LIST_LINE.match(line)) and match.group(1).strip()
        ]
        if items:
            values.extend(items)
            continue
        paragraph: list[str] = []
        for line in [*section.lines, ""]:
            if line.strip():
                paragraph.append(line.strip())
            elif paragraph:
                values.append(" ".join(paragraph))
                paragraph = []
    return tuple(values)


def _resolution(document: IssueSourceDocument) -> str | None:
    lines: list[str] = []
    for section in document.matching_sections("Resolution"):
        lines.extend(section.lines)
    value = "\n".join(lines).strip()
    return value or None


def _status(value: str | None) -> str:
    normalized = _optional(value) or "Open"
    return "_".join(normalized.casefold().replace("-", " ").split())


def _owner(value: str | None) -> str | None:
    normalized = _optional(value)
    if normalized is None or normalized.casefold() == "unassigned":
        return None
    return normalized


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = _normalize_value(value)
    return normalized or None


def _normalize_value(value: str) -> str:
    normalized = value.strip()
    return normalized.strip("`").strip()


def _valid_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def _validate_source_path(source_path: str) -> None:
    if not source_path:
        raise ValueError("Issue source path is required")
    path = PurePosixPath(source_path)
    if (
        path.is_absolute()
        or path.as_posix() != source_path
        or "\\" in source_path
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(
            "Issue source path must be canonical and relative (repository-relative)"
        )
