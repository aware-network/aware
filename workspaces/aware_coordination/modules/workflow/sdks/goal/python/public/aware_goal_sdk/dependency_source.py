"""Neutral decoding of authored Goal dependency declarations.

This module owns syntax and exact source identity, not satisfaction, Gate
observation, eligibility, or currentness decisions.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import cast

from aware_goal_operational_runtime.dependencies import (
    GoalDependency, GoalDependencyRelation, validate_dependency_set,
)

from .markdown_source import GoalMarkdownImportPlan, parse_goal_markdown_import_plan


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _declarations(markdown: str) -> list[dict[str, object]]:
    # Track fences so headings in examples cannot become declarations.
    sections: list[list[str]] = []
    active: list[str] | None = None
    fence: str | None = None
    for line in markdown.splitlines():
        stripped = line.strip()
        marker = re.match(r"^(`{3,}|~{3,})", stripped)
        if fence is None and stripped.startswith("## "):
            active = None
            if stripped == "## Dependencies":
                active = []
                sections.append(active)
            continue
        if active is not None:
            active.append(line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and stripped == token:
                fence = None
    if not sections:
        return []
    if len(sections) != 1:
        raise ValueError("exactly one Dependencies section is allowed")
    body = "\n".join(sections[0]).strip()
    match = re.fullmatch(r"```json\s*\n(.*?)\n```", body, flags=re.DOTALL)
    if not match:
        raise ValueError("Dependencies must contain exactly one fenced json array")
    result = cast(object, json.loads(match.group(1), object_pairs_hook=_unique_object))
    if type(result) is not list:
        raise ValueError("Dependencies must be an array of objects")
    rows: list[dict[str, object]] = []
    for row in cast(list[object], result):
        if type(row) is not dict:
            raise ValueError("Dependencies must be an array of objects")
        rows.append(cast(dict[str, object], row))
    return rows


@dataclass(frozen=True)
class GoalDependencySourceV1:
    plan: GoalMarkdownImportPlan
    dependencies: tuple[GoalDependency, ...]
    known_rows: frozenset[tuple[str, str]]
    source_sha256: str
    source_path: str | None


def parse_goal_dependency_source(
    markdown: str, *, source_path: str | None = None
) -> GoalDependencySourceV1:
    plan = parse_goal_markdown_import_plan(markdown, source_path=source_path)
    dependencies: list[GoalDependency] = []
    for row in _declarations(markdown):
        values = dict(row)
        if "owner_goal_tag" in values:
            raise ValueError("owner_goal_tag is supplied by the containing Goal")
        refs = values.pop("evidence_refs", [])
        if not isinstance(refs, list):
            raise ValueError("evidence_refs must be a JSON array")
        relation = GoalDependencyRelation(values.pop("relation"))
        # Preserve the historical constructor's validation order and diagnostics.
        # The casts narrow only static types; untrusted JSON values remain unchanged.
        dependencies.append(GoalDependency(
            owner_goal_tag=plan.goal_tag,
            relation=relation,
            evidence_refs=cast(tuple[str, ...], tuple(cast(list[object], refs))),
            **cast(dict[str, str], values),
        ))
    typed = tuple(dependencies)
    validate_dependency_set(typed)
    return GoalDependencySourceV1(
        plan=plan,
        dependencies=typed,
        known_rows=frozenset((row.lane_key, row.row_key) for row in plan.lane_issues),
        source_sha256=plan.source_sha256 or "",
        source_path=source_path,
    )


__all__ = ["GoalDependencySourceV1", "parse_goal_dependency_source"]
