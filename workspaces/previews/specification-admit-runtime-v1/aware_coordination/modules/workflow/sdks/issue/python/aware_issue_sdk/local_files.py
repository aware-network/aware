"""Local issue Markdown and day-index helpers for SDK-owned filesystem use."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from aware_issue_runtime import parse_issue_source
from pydantic import BaseModel, Field

_DAY_INDEX_ENTRY_PATTERN = re.compile(
    r"^-\s+`(?P<path>[^`]+)`\s+—\s+(?P<status>[A-Z ]+)\s+"
    r"\(owner:\s+`(?P<owner>[^`]+)`\):\s+(?P<summary>.*)$"
)


class IssueHeaderLine(BaseModel):
    field: str
    value: str


class IssueSection(BaseModel):
    heading: str
    lines: list[str] = Field(default_factory=list)


class IssueDocument(BaseModel):
    title: str
    headers: list[IssueHeaderLine] = Field(default_factory=list)
    sections: list[IssueSection] = Field(default_factory=list)


class IssueLifecycleSnapshot(BaseModel):
    title: str
    slug: str | None = None
    tag: str
    status_display: str
    status_token: str
    owner_session_id: str | None = None
    priority: str | None = None
    goal: str | None = None
    source: str | None = None
    ownership_scope: tuple[str, ...] = ()


class FeedLocalAppendReceipt(BaseModel):
    feed_daily_log_path: Path
    appended_line: str


class FeedLocalFileSdk:
    def append_line(
        self,
        *,
        feed_daily_log_path: Path,
        line: str,
    ) -> FeedLocalAppendReceipt:
        append_feed_line(feed_daily_log_path=feed_daily_log_path, line=line)
        return FeedLocalAppendReceipt(
            feed_daily_log_path=feed_daily_log_path,
            appended_line=line,
        )


def now_utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_issue_document(*, issue_doc_path: Path) -> IssueDocument:
    text = issue_doc_path.read_text(encoding="utf-8")
    return parse_issue_document_text(text=text)


def parse_issue_document_text(*, text: str) -> IssueDocument:
    parsed = parse_issue_source(text)
    return IssueDocument(
        title=parsed.title,
        headers=[
            IssueHeaderLine(field=header.field, value=header.value)
            for header in parsed.headers
        ],
        sections=[
            IssueSection(heading=section.heading, lines=list(section.lines))
            for section in parsed.sections
        ],
    )


def render_issue_document(*, document: IssueDocument) -> str:
    rendered: list[str] = [f"# Issue: {document.title}", ""]
    for header in document.headers:
        rendered.append(f"- {header.field}: {header.value}")
    rendered.append("")
    for index, section in enumerate(document.sections):
        rendered.append(f"## {section.heading}")
        rendered.extend(section.lines)
        if index != len(document.sections) - 1:
            rendered.append("")
    rendered.append("")
    return "\n".join(rendered)


def write_issue_document(*, issue_doc_path: Path, document: IssueDocument) -> None:
    issue_doc_path.parent.mkdir(parents=True, exist_ok=True)
    issue_doc_path.write_text(
        render_issue_document(document=document),
        encoding="utf-8",
    )


def snapshot_issue_document(*, document: IssueDocument) -> IssueLifecycleSnapshot:
    status_display = get_header_value(document=document, field="Status") or "Open"
    return IssueLifecycleSnapshot(
        title=document.title,
        slug=get_header_value(document=document, field="Slug"),
        tag=(get_header_value(document=document, field="Tag") or "").strip("`"),
        status_display=status_display,
        status_token=status_display_to_token(status_display),
        owner_session_id=_strip_backticks(
            get_header_value(document=document, field="Owner")
        ),
        priority=get_header_value(document=document, field="Priority"),
        goal=get_header_value(document=document, field="Goal"),
        source=get_header_value(document=document, field="Source"),
        ownership_scope=parse_ownership_scope(document=document),
    )


def build_issue_document(
    *,
    title: str,
    slug: str,
    tag: str,
    status_display: str,
    owner_session_id: str | None,
    priority: str,
    goal: str,
    captured: str,
    recorder: str,
    source: str,
    ownership_scope: tuple[str, ...],
    updates: tuple[str, ...],
    problem_items: tuple[str, ...] = (),
    objective_items: tuple[str, ...] = (),
    acceptance_items: tuple[str, ...] = (),
) -> IssueDocument:
    headers = [
        IssueHeaderLine(field="Slug", value=wrap_backticks(slug)),
        IssueHeaderLine(field="Tag", value=wrap_backticks(tag)),
        IssueHeaderLine(field="Status", value=status_display),
        IssueHeaderLine(
            field="Owner",
            value=wrap_backticks(owner_session_id or "Unassigned"),
        ),
        IssueHeaderLine(field="Priority", value=priority),
        IssueHeaderLine(field="Goal", value=wrap_backticks(goal)),
        IssueHeaderLine(field="Captured", value=captured),
        IssueHeaderLine(field="Recorder", value=wrap_backticks(recorder)),
        IssueHeaderLine(field="Source", value=wrap_backticks(source)),
    ]
    sections = [
        IssueSection(
            heading="Ownership Scope",
            lines=[f"- {wrap_backticks(path)}" for path in ownership_scope]
            or ["- `TBD`"],
        ),
        IssueSection(
            heading="Problem",
            lines=[f"{i}. {text}" for i, text in enumerate(problem_items, 1)]
            or ["1. TBD"],
        ),
        IssueSection(
            heading="Goal",
            lines=[f"{i}. {text}" for i, text in enumerate(objective_items, 1)]
            or ["1. TBD"],
        ),
        IssueSection(
            heading="Acceptance Checklist",
            lines=[f"- [ ] {text}" for text in acceptance_items] or ["- [ ] TBD"],
        ),
        IssueSection(
            heading="Updates (append-only)",
            lines=list(updates),
        ),
    ]
    return IssueDocument(title=title, headers=headers, sections=sections)


def get_header_value(*, document: IssueDocument, field: str) -> str | None:
    for header in document.headers:
        if header.field.casefold() == field.casefold():
            return header.value
    return None


def set_header_value(*, document: IssueDocument, field: str, value: str) -> None:
    for header in document.headers:
        if header.field.casefold() == field.casefold():
            header.value = value
            return
    insert_index = len(document.headers)
    if field.casefold() == "owner":
        for index, header in enumerate(document.headers):
            if header.field.casefold() == "status":
                insert_index = index + 1
                break
    document.headers.insert(insert_index, IssueHeaderLine(field=field, value=value))


def delete_header(*, document: IssueDocument, field: str) -> None:
    document.headers = [
        header
        for header in document.headers
        if header.field.casefold() != field.casefold()
    ]


def parse_ownership_scope(*, document: IssueDocument) -> tuple[str, ...]:
    scope: list[str] = []
    inline_value = get_header_value(document=document, field="Ownership Scope")
    if inline_value:
        for token in inline_value.split(","):
            value = _normalize_header_value(token)
            if value:
                scope.append(value)
    section = get_section(document=document, heading="Ownership Scope")
    if section is not None:
        for line in section.lines:
            stripped = line.strip()
            if stripped.startswith("- "):
                value = _normalize_header_value(stripped[2:])
                if value:
                    scope.append(value)
    return tuple(dict.fromkeys(scope))


def set_ownership_scope(
    *, document: IssueDocument, scope_paths: tuple[str, ...]
) -> None:
    delete_header(document=document, field="Ownership Scope")
    section = upsert_section(document=document, heading="Ownership Scope")
    section.lines = [f"- {wrap_backticks(path)}" for path in scope_paths] or ["- `TBD`"]


def get_section(*, document: IssueDocument, heading: str) -> IssueSection | None:
    for section in document.sections:
        if section.heading.casefold() == heading.casefold():
            return section
    return None


def upsert_section(
    *,
    document: IssueDocument,
    heading: str,
    before_heading: str | None = None,
) -> IssueSection:
    existing = get_section(document=document, heading=heading)
    if existing is not None:
        return existing
    section = IssueSection(heading=heading, lines=[])
    if before_heading is None:
        document.sections.append(section)
        return section
    for index, candidate in enumerate(document.sections):
        if candidate.heading.casefold() == before_heading.casefold():
            document.sections.insert(index, section)
            return section
    document.sections.append(section)
    return section


def append_update_line(*, document: IssueDocument, line: str) -> None:
    updates = upsert_section(document=document, heading="Updates (append-only)")
    updates.lines.append(line)


def set_resolution(*, document: IssueDocument, resolution: str) -> None:
    section = upsert_section(
        document=document,
        heading="Resolution",
        before_heading="Verified-by",
    )
    section.lines = [resolution]


def set_verified_by(*, document: IssueDocument, entries: tuple[str, ...]) -> None:
    section = upsert_section(
        document=document,
        heading="Verified-by",
        before_heading="Updates (append-only)",
    )
    section.lines = [f"- {entry}" for entry in entries]


def upsert_day_index_entry(
    *,
    day_index_path: Path,
    issue_doc_relpath: str,
    status_display: str,
    owner_session_id: str | None,
    priority: str,
    summary: str,
    title: str,
) -> None:
    day_index_path.parent.mkdir(parents=True, exist_ok=True)
    text = day_index_path.read_text(encoding="utf-8") if day_index_path.exists() else ""
    lines = text.splitlines()
    entry_line = (
        f"- `{issue_doc_relpath}` — {status_display_to_day_index(status_display)} "
        f"(owner: `{owner_session_id or 'Unassigned'}`): {summary}"
    )

    for index, line in enumerate(lines):
        match = _DAY_INDEX_ENTRY_PATTERN.match(line)
        if match and match.group("path") == issue_doc_relpath:
            lines[index] = entry_line
            day_index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return

    heading = f"### {priority} — {title}"
    insert_block = [heading, "", entry_line, ""]
    insert_at = len(lines)
    for index, line in enumerate(lines):
        if line.strip().lower() == "## updates (append-only)":
            insert_at = index
            break
    new_lines = lines[:insert_at] + insert_block + lines[insert_at:]
    day_index_path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")


def append_day_index_update(*, day_index_path: Path, line: str) -> None:
    day_index_path.parent.mkdir(parents=True, exist_ok=True)
    text = day_index_path.read_text(encoding="utf-8") if day_index_path.exists() else ""
    lines = text.splitlines()
    insert_at = len(lines)
    for index, candidate in enumerate(lines):
        if candidate.strip().lower() == "## updates (append-only)":
            insert_at = index + 1
            break
    if insert_at == len(lines):
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend(["## Updates (append-only)"])
        insert_at = len(lines)
    lines.insert(insert_at, line)
    day_index_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def append_feed_line(*, feed_daily_log_path: Path, line: str) -> None:
    feed_daily_log_path.parent.mkdir(parents=True, exist_ok=True)
    existing = (
        feed_daily_log_path.read_text(encoding="utf-8").rstrip()
        if feed_daily_log_path.exists()
        else ""
    )
    content = f"{existing}\n{line}\n" if existing else f"{line}\n"
    feed_daily_log_path.write_text(content, encoding="utf-8")


def default_summary(*, snapshot: IssueLifecycleSnapshot) -> str:
    goal = _strip_backticks(snapshot.goal)
    if goal:
        return goal
    return snapshot.title


def status_display_to_day_index(status_display: str) -> str:
    token = status_display_to_token(status_display)
    return token.replace("_", " ").upper()


def status_display_to_token(status_display: str) -> str:
    return "_".join(status_display.strip().lower().replace("-", " ").split())


def status_token_to_display(status_token: str) -> str:
    token = status_display_to_token(status_token)
    if token == "in_progress":
        return "In Progress"
    if token == "open":
        return "Open"
    if token == "blocked":
        return "Blocked"
    if token == "closed":
        return "Closed"
    return token.replace("_", " ").title()


def wrap_backticks(value: str) -> str:
    return f"`{value}`"


def _strip_backticks(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = _normalize_header_value(value)
    if normalized.casefold() == "unassigned":
        return None
    return normalized


def _normalize_header_value(value: str) -> str:
    candidate = value.strip()
    if len(candidate) >= 2 and candidate[0] == "`" and candidate[-1] == "`":
        return candidate[1:-1].strip()
    return candidate


__all__ = [
    "FeedLocalAppendReceipt",
    "FeedLocalFileSdk",
    "IssueDocument",
    "IssueHeaderLine",
    "IssueLifecycleSnapshot",
    "IssueSection",
    "append_day_index_update",
    "append_feed_line",
    "append_update_line",
    "build_issue_document",
    "default_summary",
    "get_header_value",
    "get_section",
    "now_utc_timestamp",
    "parse_issue_document",
    "parse_issue_document_text",
    "render_issue_document",
    "set_header_value",
    "set_ownership_scope",
    "set_resolution",
    "set_verified_by",
    "snapshot_issue_document",
    "status_display_to_day_index",
    "status_display_to_token",
    "status_token_to_display",
    "upsert_day_index_entry",
    "wrap_backticks",
    "write_issue_document",
]
