#!/usr/bin/env python3
"""Serialize test-only sample input with the installed neutral codec; no writer claim."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from aware_goal_operational_runtime import (
    GoalLanePhase, GoalLanePhaseDefinitionV1, GoalLanePhaseGate, GoalLanePhaseState,
    GoalPhaseContractBundleV1, GoalPhaseCoordinate, GoalPhaseExecutionAuthorityV1,
    GoalPhaseNativeDocumentV2,
)
from aware_goal_sdk import attach_goal_phase_native_document


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    goal_path = "protocols/examples/read-only/goals/2026/10/05/goal-2026-10-05-reader-demo.md"
    goal_tag = "goal/2026-10-05/reader-demo"
    prefix = (
        "# Goal: Synthetic reader demo\n\n"
        "This is test input, not customer authority or an approval.\n\n"
        "- Slug: `reader-demo`\n- Tag: `goal/2026-10-05/reader-demo`\n"
        "- Status: `Active`\n- Priority: `P2`\n- Owner: `demo-fixture`\n\n"
        "## Lane Map\n\n"
        "| Lane | Role | Owner | Status | Current Issue | Since | Last Receipt | Scope |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
        "| `demo` | Sample | `demo-fixture` | Ready | `TBD:read` | Pending | Pending | Read-only |\n\n"
        "## Forward Plan By Lane\n\n| Lane | Next Issue | Gate |\n| --- | --- | --- |\n"
        "| `demo` | `TBD:read` | Observe the fixture without changing it. |\n\n"
        "## Lane Sequences\n\n### `demo`\n\n"
        "| Step | Key | Time | Tick | Issue | Gate | Status | Owner | Receipt |\n"
        "| ---: | --- | --- | --- | --- | --- | --- | --- | --- |\n"
        "| 1 | `read` | Pending | `[ ]` | `TBD:read` | Observe the fixture without changing it. | Planned | `demo-fixture` | Pending |\n\n"
        "## Integrated Updates (append-only)\n\n"
    ).encode()
    gate = GoalLanePhaseGate(gate_key="read", promise="Observe the fixture without changing it.",
                             gate_contract_ref="example:read-contract", evidence_schema_ref="example:read-evidence")
    coordinate = GoalPhaseCoordinate(goal_tag, "demo", "read")
    definition = GoalLanePhaseDefinitionV1(coordinate=coordinate, ordinal=1,
                                          title="Read", intent="Demonstrate read-only observations.", gate=gate)
    phase = GoalLanePhase(coordinate=coordinate, title="Read", ordinal=1,
                         intent=definition.intent, state=GoalLanePhaseState.ACTIVE, gate=gate)
    document = GoalPhaseNativeDocumentV2(
        goal_tag=goal_tag, compatibility_projection_sha256="sha256:" + hashlib.sha256(prefix).hexdigest(),
        compatibility_projection_byte_count=len(prefix), definitions=(definition,),
        operational_bundle=GoalPhaseContractBundleV1(phases=(phase,), dependencies=()),
        unresolved_dependencies=(),
        source_refs=("repository-path:" + goal_path,),
        execution_authority=GoalPhaseExecutionAuthorityV1(
            source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
            parity_ref="goal-phase-native-compatibility-parity:sha256:" + "1" * 64,
            proposal_aggregate_ref="goal-phase-native-operational-bootstrap-proposal:sha256:" + "2" * 64,
            coordinator_acceptance_ref="goal-phase-native-operational-bootstrap-coordinator-acceptance:sha256:" + "3" * 64,
        ),
    )
    target = root / goal_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(attach_goal_phase_native_document(prefix, document))
    receipt = {"purpose": "synthetic read-only fixture; no real approval or customer authority",
               "generator": "protocols/publication/build_demo_fixture.py",
               "goal_path": goal_path, "goal_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
               "serialization": "installed aware-goal-sdk 0.3.0 neutral codec"}
    (root / "protocols/examples/read-only/fixture.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
