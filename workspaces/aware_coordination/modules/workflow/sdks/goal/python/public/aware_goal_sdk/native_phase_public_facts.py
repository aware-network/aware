"""Public-safe facts from a Goal's native Lane/Phase authority block.

A Goal document may carry a native Phase block beside its legacy rows. This
reads it through the strict extractor, so a block that is absent, stale or not
byte-bound to its Markdown yields no facts rather than wrong ones, and lowers
each Phase to the facts a public Goal reader may see:

- the definition: ordinal, title, intent and Gate promise;
- where the Phase is operational: its native state, its current Gate
  observation (or ``not_evaluated`` when none exists), and its work — each
  Issue's title, role, disposition and admission/retirement times.

Issue paths, receipts, evaluator and evidence references, digests and
association identities stay behind. Nothing here derives state, eligibility or
acceptance: every value is the native document's own.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

from .native_phase_markdown import (
    START_MARKER,
    GoalPhaseNativeMarkdownError,
    extract_goal_phase_native_document,
)

NATIVE_PHASE_PUBLIC_FACTS_SCHEMA = "aware.goal.native-phase-public-facts.v1"

_ISSUE_TITLE = re.compile(r"^#\s*Issue:\s*(.+?)\s*$", re.MULTILINE)


def native_phase_key(lane_key: str, phase_key: str) -> str:
    """The key facts are listed under: one Phase coordinate within a Goal."""

    return f"{lane_key}::{phase_key}"


def native_phase_public_facts(
    goal_markdown: bytes,
    *,
    repo_root: Path,
    issue_key: Callable[[str], str | None] | None = None,
) -> dict[str, object]:
    """Public-safe native Phase facts for one Goal document.

    ``availability`` is ``available``, ``no_native_block`` or
    ``invalid_native_block``; only ``available`` carries phases.

    Each Work association names its Issue only through [issue_key], supplied
    by whoever composes the reading: the Goal refers to an Issue without
    reading it, and never says where it is stored.
    """

    if START_MARKER not in goal_markdown:
        return _unavailable("no_native_block")
    try:
        _, document = extract_goal_phase_native_document(goal_markdown)
    except (GoalPhaseNativeMarkdownError, ValueError):
        return _unavailable("invalid_native_block")

    operational = {
        native_phase_key(phase.coordinate.lane_key, phase.coordinate.phase_key): phase
        for phase in document.operational_bundle.phases
    }
    phases: dict[str, object] = {}
    for definition in document.definitions:
        key = native_phase_key(
            definition.coordinate.lane_key,
            definition.coordinate.phase_key,
        )
        phase = operational.get(key)
        phases[key] = {
            "lane_key": definition.coordinate.lane_key,
            "phase_key": definition.coordinate.phase_key,
            "ordinal": definition.ordinal,
            "title": definition.title or (phase.title if phase else None),
            "intent": definition.intent or (phase.intent if phase else None),
            "gate": definition.gate.promise,
            "operational": (
                _operational(phase, repo_root, issue_key) if phase else None
            ),
        }
    return {
        "schema_version": NATIVE_PHASE_PUBLIC_FACTS_SCHEMA,
        "availability": "available",
        "phases": phases,
    }


def _operational(
    phase,
    repo_root: Path,
    issue_key: Callable[[str], str | None] | None,
) -> dict[str, object]:
    current = [
        observation
        for observation in phase.gate_observations
        if observation.outcome.value != "stale"
    ]
    # Absence of an observation is `not_evaluated`, never `pending`.
    observation = (
        {
            "outcome": current[0].outcome.value,
            "evaluated_at": current[0].evaluated_at,
        }
        if current
        else {"outcome": "not_evaluated"}
    )
    return {
        "state": phase.state.value,
        "gate_observation": observation,
        "work": [
            {
                "title": _issue_title(repo_root, work.issue_ref),
                "role": work.role.value,
                "disposition": work.disposition.value,
                "admitted_at": work.admitted_at,
                **({"retired_at": work.retired_at} if work.retired_at else {}),
                **(
                    {"issue_key": key}
                    if issue_key is not None
                    and (key := issue_key(work.issue_ref)) is not None
                    else {}
                ),
            }
            for work in phase.work_associations
        ],
    }


def _issue_title(repo_root: Path, issue_ref: str) -> str:
    """The Issue's own title, or its file name when the title is unreadable."""

    path = (repo_root / issue_ref).resolve()
    try:
        path.relative_to(repo_root.resolve())
        match = _ISSUE_TITLE.search(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        match = None
    if match:
        return match.group(1)
    stem = Path(issue_ref).stem
    return re.sub(r"^fb-\d{4}-\d{2}-\d{2}-", "", stem).replace("-", " ")


def _unavailable(reason: str) -> dict[str, object]:
    return {
        "schema_version": NATIVE_PHASE_PUBLIC_FACTS_SCHEMA,
        "availability": reason,
        "phases": {},
    }
