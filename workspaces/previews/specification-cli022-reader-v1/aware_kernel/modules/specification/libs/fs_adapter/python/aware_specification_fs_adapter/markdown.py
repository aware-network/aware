"""Deterministic Markdown projection parser for Specification FS V1."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


class MarkdownError(ValueError):
    pass


_PREAMBLE_FORBIDDEN = (
    tuple(range(0x20))
    + tuple(range(0x7F, 0xA0))
    + (0xA0, 0x1680)
    + tuple(range(0x2000, 0x200B))
    + (0x2028, 0x2029, 0x202F, 0x205F, 0x3000)
    + tuple(range(0xD800, 0xE000))
)
_FENCE_GLOBAL_FORBIDDEN = (
    tuple(range(0x20))
    + tuple(range(0x7F, 0xA0))
    + (0x2028, 0x2029)
    + tuple(range(0xD800, 0xE000))
)
_FENCE_EDGE_SPACE = (0x20, 0xA0, 0x1680, 0x202F, 0x205F, 0x3000) + tuple(
    range(0x2000, 0x200B)
)

_LIFECYCLE = {
    "specification": frozenset({"draft", "in_progress", "stable", "deprecated"}),
    "invariant": frozenset({"declared", "partial", "enforced", "deprecated"}),
    "phase": frozenset(
        {"planned", "in_progress", "held", "accepted", "complete", "deprecated"}
    ),
    "iteration": frozenset(
        {"planned", "in_progress", "roadblock", "review_ready", "done", "rejected"}
    ),
    "invariant_index": frozenset(),
    "phase_index": frozenset({"draft", "in_progress", "stable", "deprecated"}),
}


@dataclass(frozen=True, slots=True)
class ParsedMarkdown:
    role: str
    title: str
    bodies: dict[str, str | None]
    sections: dict[str, tuple[str, ...]]


def _validate_preamble_value(value: str) -> str:
    if (
        type(value) is not str
        or not value
        or value.startswith(" ")
        or value.endswith(" ")
        or not unicodedata.is_normalized("NFC", value)
        or any(ord(character) in _PREAMBLE_FORBIDDEN for character in value)
    ):
        raise MarkdownError("preamble value is not canonical")
    return value


def _validate_title(value: str) -> str:
    if (
        not value
        or value.strip(" ") != value
        or not unicodedata.is_normalized("NFC", value)
        or any(ord(character) in _PREAMBLE_FORBIDDEN for character in value)
    ):
        raise MarkdownError("Markdown title is not canonical")
    return value


def _semantic_lines(body: str) -> tuple[str, ...]:
    if type(body) is not str or not body.endswith("\n"):
        raise MarkdownError("Markdown source must be exact text ending in LF")
    lines = body[:-1].split("\n")
    semantic = list(lines)
    fence: tuple[str, int] | None = None
    comment = False
    for index, line in enumerate(lines):
        if comment:
            if "<!--" in line:
                raise MarkdownError("nested HTML comment is forbidden")
            semantic[index] = ""
            if "-->" in line:
                comment = False
            continue
        if fence is not None:
            marker, minimum = fence
            stripped = line.lstrip(" ")
            indent = len(line) - len(stripped)
            run = len(stripped) - len(stripped.lstrip(marker))
            if indent <= 3 and run >= minimum and stripped[run:].strip(" ") == "":
                fence = None
            semantic[index] = ""
            continue
        if "<!--" in line:
            before, _, after = line.partition("<!--")
            if "-->" in after:
                _, _, tail = after.partition("-->")
                if "<!--" in tail:
                    raise MarkdownError("nested HTML comment is forbidden")
                semantic[index] = before + tail
            else:
                semantic[index] = before
                comment = True
            continue
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        if indent <= 3 and stripped and stripped[0] in {"`", "~"}:
            marker = stripped[0]
            run = len(stripped) - len(stripped.lstrip(marker))
            if run >= 3:
                suffix = stripped[run:]
                _validate_fence_suffix(marker, suffix)
                fence = (marker, run)
                semantic[index] = ""
    if fence is not None or comment:
        raise MarkdownError("unclosed Markdown fence or comment")
    return tuple(semantic)


def _validate_fence_suffix(marker: str, suffix: str) -> None:
    if suffix == "":
        return
    if not suffix.startswith(" ") or suffix.startswith("  "):
        raise MarkdownError("fence info suffix is invalid")
    info = suffix[1:]
    if (
        not info
        or not unicodedata.is_normalized("NFC", info)
        or ord(info[0]) in _FENCE_EDGE_SPACE
        or ord(info[-1]) in _FENCE_EDGE_SPACE
        or any(ord(character) in _FENCE_GLOBAL_FORBIDDEN for character in info)
        or (marker == "`" and "`" in info)
    ):
        raise MarkdownError("fence info text is invalid")


def _h1(role: str, line: str) -> str:
    patterns = {
        "specification": r"# (.+) — SPEC",
        "invariant": r"# Invariant [0-9]{2,} — (.+)",
        "phase": r"# Phase [0-9]{2,} — (.+)",
        "iteration": r"# Iteration [0-9]{2,} — (.+)",
        "invariant_index": r"# (.+) — Invariants",
        "phase_index": r"# (.+) — PHASES",
    }
    match = re.fullmatch(patterns[role], line)
    if match is None:
        raise MarkdownError("Markdown H1 does not match its role")
    return _validate_title(match.group(1))


def _preamble(role: str, lines: tuple[str, ...]) -> int:
    fields = {
        "specification": (("Status", "Owner"),),
        "invariant": (("Status", "Owner", "Spec"),),
        "phase": (("State", "Owner"),),
        "iteration": (
            ("State", "Owner", "Approval"),
            ("Phase", "Invariants", "Issue", "LOCK"),
        ),
        "invariant_index": (),
        "phase_index": (("Status", "Owner"),),
    }[role]
    cursor = 2
    for group in fields:
        for field_name in group:
            if cursor >= len(lines):
                raise MarkdownError("Markdown preamble is incomplete")
            prefix = f"{field_name}: "
            if not lines[cursor].startswith(prefix):
                raise MarkdownError("Markdown preamble order is invalid")
            value = _validate_preamble_value(lines[cursor][len(prefix) :])
            if field_name in {"Status", "State"}:
                if not (
                    value.startswith("`")
                    and value.endswith("`")
                    and value.count("`") == 2
                ):
                    raise MarkdownError("lifecycle token must be backticked")
                if value[1:-1] not in _LIFECYCLE[role]:
                    raise MarkdownError("lifecycle token is invalid")
            cursor += 1
        if cursor >= len(lines) or lines[cursor] != "":
            raise MarkdownError("preamble group requires one empty line")
        cursor += 1
    return cursor


def _sections(lines: tuple[str, ...], start: int) -> dict[str, tuple[str, ...]]:
    found: dict[str, tuple[str, ...]] = {}
    headings = [
        (index, line[3:])
        for index, line in enumerate(lines[start:], start)
        if line.startswith("## ")
    ]
    for position, (index, name) in enumerate(headings):
        if name in found:
            raise MarkdownError("duplicate semantic heading")
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        content = list(lines[index + 1 : end])
        if not content or content[0] != "":
            raise MarkdownError("H2 requires one empty line")
        content = content[1:]
        if end != len(lines):
            if not content or content[-1] != "":
                raise MarkdownError("section requires one separating empty line")
            content = content[:-1]
        while content and content[-1] == "":
            if end == len(lines):
                raise MarkdownError("terminal empty content is forbidden")
            break
        found[name] = tuple(content)
    return found


def _body(
    sections: dict[str, tuple[str, ...]], name: str, *, required: bool
) -> str | None:
    value = sections.get(name)
    if value is None:
        if required:
            raise MarkdownError(f"required {name} section is missing")
        return None
    if not value or value[0] == "" or value[-1] == "":
        raise MarkdownError(f"{name} body is empty or padded")
    return "\n".join(value)


def parse_markdown(role: str, body: str) -> ParsedMarkdown:
    if type(role) is not str or role not in _LIFECYCLE:
        raise MarkdownError("Markdown role is invalid")
    lines = _semantic_lines(body)
    if len(lines) < 2 or lines[1] != "":
        raise MarkdownError("Markdown H1 requires one empty line")
    title = _h1(role, lines[0])
    start = _preamble(role, lines)
    sections = _sections(lines, start)
    bodies: dict[str, str | None] = {}
    if role == "specification":
        bodies["Goal"] = _body(sections, "Goal", required=False)
    elif role == "invariant":
        bodies["Statement"] = _body(sections, "Statement", required=True)
    elif role == "phase":
        bodies["Gate"] = _body(sections, "Gate", required=True)
        bodies["Goal"] = _body(sections, "Goal", required=False)
    elif role == "iteration":
        bodies["Goal"] = _body(sections, "Goal", required=True)
    return ParsedMarkdown(role, title, bodies, sections)


def table_rows(
    section: tuple[str, ...], header: str, delimiter: str, columns: int
) -> tuple[tuple[str, ...], ...]:
    starts = [index for index, line in enumerate(section) if line == header]
    if len(starts) != 1:
        raise MarkdownError("projection table header must occur exactly once")
    start = starts[0]
    if start + 1 >= len(section) or section[start + 1] != delimiter:
        raise MarkdownError("projection table delimiter is invalid")
    rows: list[tuple[str, ...]] = []
    for line in section[start + 2 :]:
        if not line.startswith("| "):
            break
        if not line.endswith(" |"):
            raise MarkdownError("projection row spacing is invalid")
        cells = tuple(line[2:-2].split(" | "))
        if len(cells) != columns:
            raise MarkdownError("projection row arity is invalid")
        rows.append(cells)
    return tuple(rows)


def bullet_rows(section: tuple[str, ...]) -> tuple[str, ...]:
    rows: list[str] = []
    for line in section:
        if line.startswith("-"):
            match = re.fullmatch(r"- `([^`]+)`", line)
            if match is None:
                raise MarkdownError("projection bullet is invalid")
            rows.append(match.group(1))
    return tuple(rows)


def decode_rationale(value: str) -> str | None:
    result: list[str] = []
    index = 0
    while index < len(value):
        if value[index] != "\\":
            result.append(value[index])
            index += 1
            continue
        if index + 1 >= len(value) or value[index + 1] not in {"\\", "|", "n"}:
            raise MarkdownError("dependency rationale escape is invalid")
        result.append("\n" if value[index + 1] == "n" else value[index + 1])
        index += 2
    decoded = "".join(result)
    return decoded or None
