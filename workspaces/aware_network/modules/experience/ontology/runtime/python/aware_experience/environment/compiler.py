from __future__ import annotations

import re
from pathlib import Path

from aware_experience.compiler.models import (
    ExperienceEnvironmentEventActionOwnership,
    ExperienceEnvironmentEventNodeScopeOwnership,
    ExperienceEnvironmentEventOwnership,
    ExperienceEnvironmentOwnership,
    ExperienceEnvironmentProgramOwnership,
)

_ENV_HEADER_RE = re.compile(
    r"\benvironment\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{",
    re.DOTALL,
)
_EXPERIENCE_STMT_RE = re.compile(r"\bexperience\s+([A-Za-z_][A-Za-z0-9_\.]*)\s*;?")
_PROGRAM_STMT_RE = re.compile(
    r"\bprogram\s+([A-Za-z_][A-Za-z0-9_\.]*)\s+([A-Za-z_][A-Za-z0-9_\.]*)\s*;?",
)
_EVENT_STMT_RE = re.compile(r"\bevent\s+([A-Za-z_][A-Za-z0-9_\.]*)\s*\{", re.DOTALL)
_ACTION_STMT_RE = re.compile(r"\baction\s+([A-Za-z_][A-Za-z0-9_\.]*)")
_NODE_SCOPE_STMT_RE = re.compile(
    r"^\s*(?://\s*@aware\s+)?node_scope\s+([A-Za-z_][A-Za-z0-9_\.]*)\s*;?\s*$",
    re.MULTILINE,
)


def load_environment_ownership_from_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
) -> tuple[ExperienceEnvironmentOwnership, ...]:
    environments_by_name: dict[str, ExperienceEnvironmentOwnership] = {}
    for relpath in source_files:
        source_path = (package_root / relpath).resolve()
        _assert_within(
            base=package_root, candidate=source_path, label="environment source"
        )
        text = source_path.read_text(encoding="utf-8")
        source_rel = relpath.as_posix()
        for name, body in _iter_environment_blocks(source_text=text):
            env_name = _normalize_symbol(name)
            if not env_name:
                continue
            if env_name in environments_by_name:
                raise ValueError(
                    f"Duplicate environment declaration {env_name!r} across experience sources"
                )

            experiences = tuple(
                sorted(
                    {
                        _normalize_symbol(raw)
                        for raw in _EXPERIENCE_STMT_RE.findall(body)
                        if _normalize_symbol(raw)
                    }
                )
            )
            programs = tuple(
                sorted(
                    (
                        ExperienceEnvironmentProgramOwnership(
                            program_config=(m.group(1) or "").strip(),
                            program_impl=(m.group(2) or "").strip(),
                        )
                        for m in _PROGRAM_STMT_RE.finditer(body)
                        if (m.group(1) or "").strip() and (m.group(2) or "").strip()
                    ),
                    key=lambda item: (item.program_config, item.program_impl),
                )
            )

            events: list[ExperienceEnvironmentEventOwnership] = []
            for event_symbol, event_body in _iter_event_blocks(body):
                actions: list[ExperienceEnvironmentEventActionOwnership] = []
                for action_symbol in _iter_action_symbols(event_body):
                    actions.append(
                        ExperienceEnvironmentEventActionOwnership(action=action_symbol)
                    )
                actions.sort(key=lambda item: item.action)
                node_scopes = tuple(
                    ExperienceEnvironmentEventNodeScopeOwnership(node_ref=node_ref)
                    for node_ref in _iter_node_scope_refs(event_body)
                )
                events.append(
                    ExperienceEnvironmentEventOwnership(
                        event=event_symbol,
                        actions=tuple(actions),
                        node_scopes=node_scopes,
                    )
                )
            events.sort(key=lambda item: item.event)

            environments_by_name[env_name] = ExperienceEnvironmentOwnership(
                name=env_name,
                source_path=source_rel,
                experiences=experiences,
                programs=programs,
                events=tuple(events),
            )

    return tuple(
        sorted(
            environments_by_name.values(),
            key=lambda item: (item.name, item.source_path),
        )
    )


def _iter_environment_blocks(*, source_text: str) -> tuple[tuple[str, str], ...]:
    rows: list[tuple[str, str]] = []
    cursor = 0
    while True:
        match = _ENV_HEADER_RE.search(source_text, cursor)
        if match is None:
            break
        name = (match.group(1) or "").strip()
        body_start = match.end()
        body_end = _find_matching_brace(source_text=source_text, start=body_start - 1)
        body = source_text[body_start:body_end].strip()
        rows.append((name, body))
        cursor = body_end + 1
    return tuple(rows)


def _iter_event_blocks(environment_body: str) -> tuple[tuple[str, str], ...]:
    rows: list[tuple[str, str]] = []
    cursor = 0
    while True:
        match = _EVENT_STMT_RE.search(environment_body, cursor)
        if match is None:
            break
        event_symbol = _normalize_reference((match.group(1) or "").strip())
        body_start = match.end()
        body_end = _find_matching_brace(
            source_text=environment_body,
            start=body_start - 1,
        )
        body = environment_body[body_start:body_end].strip()
        if event_symbol:
            rows.append((event_symbol, body))
        cursor = body_end + 1
    return tuple(rows)


def _iter_action_symbols(event_body: str) -> tuple[str, ...]:
    rows: list[str] = []
    cursor = 0
    while True:
        match = _ACTION_STMT_RE.search(event_body, cursor)
        if match is None:
            break
        action_symbol = _normalize_reference((match.group(1) or "").strip())
        if action_symbol:
            rows.append(action_symbol)
        cursor = match.end()
    return tuple(rows)


def _iter_node_scope_refs(event_body: str) -> tuple[str, ...]:
    rows: list[str] = []
    seen: set[str] = set()
    for match in _NODE_SCOPE_STMT_RE.finditer(event_body):
        node_ref = _normalize_reference((match.group(1) or "").strip())
        if not node_ref:
            continue
        node_ref_key = node_ref.casefold()
        if node_ref_key in seen:
            raise ValueError(f"Duplicate event node_scope {node_ref!r}")
        seen.add(node_ref_key)
        rows.append(node_ref)
    return tuple(rows)


def _find_matching_brace(*, source_text: str, start: int) -> int:
    if start < 0 or start >= len(source_text) or source_text[start] != "{":
        raise ValueError(
            "Invalid environment block start while parsing environment declarations"
        )

    depth = 0
    idx = start
    in_single = False
    in_double = False
    in_triple = False
    while idx < len(source_text):
        token = source_text[idx]
        nxt = source_text[idx : idx + 3]

        if in_triple:
            if nxt == '"""':
                in_triple = False
                idx += 3
                continue
            idx += 1
            continue
        if in_single:
            if token == "'" and source_text[idx - 1] != "\\":
                in_single = False
            idx += 1
            continue
        if in_double:
            if token == '"' and source_text[idx - 1] != "\\":
                in_double = False
            idx += 1
            continue

        if nxt == '"""':
            in_triple = True
            idx += 3
            continue
        if token == "'":
            in_single = True
            idx += 1
            continue
        if token == '"':
            in_double = True
            idx += 1
            continue
        if token == "{":
            depth += 1
        elif token == "}":
            depth -= 1
            if depth == 0:
                return idx
        idx += 1

    raise ValueError(
        "Unclosed environment block while parsing environment declarations"
    )


def _normalize_symbol(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.strip()


def _normalize_reference(raw: str) -> str:
    return (raw or "").strip()


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if (
        candidate_resolved == base_resolved
        or base_resolved in candidate_resolved.parents
    ):
        return
    raise ValueError(
        f"{label} resolved outside package boundary: base={base_resolved} candidate={candidate_resolved}"
    )


__all__ = [
    "load_environment_ownership_from_sources",
]
