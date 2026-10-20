"""Public-safe native Phase facts: what a public Goal reader may see."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from aware_goal_operational_runtime import (
    GoalLanePhase,
    GoalLanePhaseDefinitionV1,
    GoalLanePhaseGate,
    GoalLanePhaseState,
    GoalLanePhaseWork,
    GoalLanePhaseWorkDisposition,
    GoalLanePhaseWorkRole,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
    GoalPhaseNativeDocumentV1,
)
from aware_goal_sdk.native_phase_markdown import attach_goal_phase_native_document
from aware_goal_sdk.native_phase_public_facts import (
    native_phase_key,
    native_phase_public_facts,
)

_TAG = "goal/2026-09-22/public-facts-v0"
_SOURCE = """# Goal: Public facts

- Tag: `goal/2026-09-22/public-facts-v0`

## Lane Sequences

### runtime

| Step | Key | Tick | Status | Gate | Issue | Owner | Receipt |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | m1 | [x] | Closed | Reviewed | TBD:m1 | TBD | This issue |
""".encode()


def _coordinate(phase_key: str) -> GoalPhaseCoordinate:
    return GoalPhaseCoordinate(goal_tag=_TAG, lane_key="runtime", phase_key=phase_key)


def _gate() -> GoalLanePhaseGate:
    return GoalLanePhaseGate(
        gate_key="reviewed",
        promise="Independent review accepts the host.",
        gate_contract_ref="aware.goal.gate/reviewed-v1",
        evidence_schema_ref="aware.goal.gate-evidence/reviewed-v1",
    )


def _goal(tmp_path: Path) -> bytes:
    issues = tmp_path / "docs" / "issues"
    issues.mkdir(parents=True)
    (issues / "implementation.md").write_text(
        "# Issue: Host implementation\n\n- Status: In Progress\n- Priority: P0\n\n"
        "## Acceptance Checklist\n- [x] One\n- [ ] Two\n\n"
        "## Updates (append-only)\n"
        "- 2026-09-21T12:00:00Z | codex-private | Private text.\n"
        "- 2026-09-21T11:00:00Z — Opened.\n",
        encoding="utf-8",
    )
    active = GoalLanePhase(
        coordinate=_coordinate("m2"),
        title="Native host",
        ordinal=2,
        intent="Host the Goal natively.",
        state=GoalLanePhaseState.ACTIVE,
        gate=_gate(),
        work_associations=(
            GoalLanePhaseWork(
                association_ref="phase-work:review:1",
                issue_ref="docs/issues/missing-review.md",
                role=GoalLanePhaseWorkRole.REVIEW,
                disposition=GoalLanePhaseWorkDisposition.RETIRED,
                admitted_at="2026-09-21T10:00:00Z",
                retired_at="2026-09-21T11:00:00Z",
                receipt_ref="receipt:phase-work:review",
            ),
            GoalLanePhaseWork(
                association_ref="phase-work:implementation:1",
                issue_ref="docs/issues/implementation.md",
                role=GoalLanePhaseWorkRole.IMPLEMENTATION,
                disposition=GoalLanePhaseWorkDisposition.CURRENT,
                admitted_at="2026-09-21T11:00:00Z",
                receipt_ref="receipt:phase-work:implementation",
            ),
        ),
    )
    document = GoalPhaseNativeDocumentV1(
        goal_tag=_TAG,
        compatibility_projection_sha256="sha256:"
        + hashlib.sha256(_SOURCE).hexdigest(),
        compatibility_projection_byte_count=len(_SOURCE),
        definitions=(
            GoalLanePhaseDefinitionV1(
                coordinate=_coordinate("m1"), ordinal=1, gate=_gate()
            ),
            GoalLanePhaseDefinitionV1(
                coordinate=_coordinate("m2"),
                ordinal=2,
                gate=_gate(),
                title="Native host",
                intent="Host the Goal natively.",
            ),
        ),
        operational_bundle=GoalPhaseContractBundleV1(
            phases=(active,), dependencies=()
        ),
        unresolved_dependencies=(),
        source_refs=("repository:path:docs/goals/test.md",),
    )
    return attach_goal_phase_native_document(_SOURCE, document)


def test_definitions_and_operational_phase_are_lowered(tmp_path: Path) -> None:
    facts = native_phase_public_facts(_goal(tmp_path), repo_root=tmp_path)

    assert facts["availability"] == "available"
    phases = facts["phases"]
    # A definition without operational facts claims no state.
    defined = phases[native_phase_key("runtime", "m1")]
    assert defined["ordinal"] == 1
    assert defined["title"] is None
    assert defined["operational"] is None

    active = phases[native_phase_key("runtime", "m2")]
    assert active["title"] == "Native host"
    assert active["gate"] == "Independent review accepts the host."
    operational = active["operational"]
    assert operational["state"] == "active"
    # No observation is `not_evaluated`, never `pending`.
    assert operational["gate_observation"] == {"outcome": "not_evaluated"}
    assert operational["work"] == [
        {
            "title": "missing review",
            "role": "review",
            "disposition": "retired",
            "admitted_at": "2026-09-21T10:00:00Z",
            "retired_at": "2026-09-21T11:00:00Z",
        },
        {
            "title": "Host implementation",
            "role": "implementation",
            "disposition": "current",
            "admitted_at": "2026-09-21T11:00:00Z",
        },
    ]


def test_references_and_receipts_never_leave(tmp_path: Path) -> None:
    encoded = json.dumps(native_phase_public_facts(_goal(tmp_path), repo_root=tmp_path))

    for private in (
        "docs/issues",
        "codex-private",
        "Private text",
        "receipt:",
        "phase-work:",
        "aware.goal.gate/",
        "sha256:",
    ):
        assert private not in encoded


def test_absent_or_tampered_blocks_yield_no_facts(tmp_path: Path) -> None:
    assert native_phase_public_facts(_SOURCE, repo_root=tmp_path) == {
        "schema_version": "aware.goal.native-phase-public-facts.v1",
        "availability": "no_native_block",
        "phases": {},
    }
    tampered = _goal(tmp_path).replace(b"Native host", b"Other host", 1)
    assert (
        native_phase_public_facts(tampered, repo_root=tmp_path)["availability"]
        == "invalid_native_block"
    )


def test_work_names_its_issue_only_through_the_composers_key(tmp_path: Path) -> None:
    refs: list[str] = []

    def key(issue_ref: str) -> str:
        refs.append(issue_ref)
        return f"issue:{len(refs)}"

    facts = native_phase_public_facts(
        _goal(tmp_path), repo_root=tmp_path, issue_key=key
    )
    work = facts["phases"][native_phase_key("runtime", "m2")]["operational"]["work"]
    assert [item["issue_key"] for item in work] == ["issue:1", "issue:2"]
    # The composer saw the refs; the facts carry only the keys.
    assert refs == ["docs/issues/missing-review.md", "docs/issues/implementation.md"]
    assert "docs/issues" not in json.dumps(facts)
