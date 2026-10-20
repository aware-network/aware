from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from aware_goal_operational_runtime import (
    GoalDependencyEvidence,
    GoalDependencyEvidenceKind,
    GoalRowResolutionOutcome,
    GoalRowSourceObservation,
    dependency_definition_digest,
    evaluate_goal_dependency,
)
from aware_goal_sdk import (
    compose_goal_dependency_view,
    decode_goal_dependency_view,
)
from aware_goal_service_view_compat.dependency_projection import project_goal_dependencies
from aware_goal_service_view_compat.landscape_projection import project_goal_landscape

EVALUATOR_REF = "goal-dependency-evaluator:view-contract-v1"
FIXTURE = Path(__file__).parent / "fixtures" / "goal_dependency_view_contract_v1.json"


def test_dependency_view_root_import_is_neutral_in_fresh_process() -> None:
    script = """
import importlib.abc
import sys

blocked = (
    'aware_goals', 'aware_goal_service_dto', 'aware_content_service_dto',
    'aware_goal_service_api', 'aware_experience', 'aware_service',
)
class Blocker(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if any(fullname == root or fullname.startswith(root + '.') for root in blocked):
            raise AssertionError('forbidden import: ' + fullname)
        return None
sys.meta_path.insert(0, Blocker())
from aware_goal_sdk import compose_goal_dependency_view, GoalDependencyViewContractV1
import aware_goal_sdk.dependency_view
assert compose_goal_dependency_view is aware_goal_sdk.dependency_view.compose_goal_dependency_view
assert GoalDependencyViewContractV1 is aware_goal_sdk.dependency_view.GoalDependencyViewContractV1
assert 'aware_goal_service_view_compat.landscape_projection' not in sys.modules
assert not any(any(name == root or name.startswith(root + '.') for root in blocked)
               for name in sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


def _document() -> str:
    rows = "\n".join(
        f"| {index + 1} | work-{index} | [ ] | Planned | Gate {index} | TBD:work-{index} | Unassigned | TBD |"
        for index in range(5)
    )
    declarations = [
        {
            "dependency_key": f"dependency-{index}",
            "dependent_lane_key": "delivery",
            "dependent_row_key": f"work-{index}",
            "prerequisite_goal_tag": (
                "goal/example" if index == 0 else "goal/external"
            ),
            "prerequisite_lane_key": ("foundation" if index == 0 else "review"),
            "prerequisite_row_key": ("ready" if index == 0 else f"accept-{index}"),
            "relation": "requires_acceptance",
            "reason": f"Acceptance gate {index} is required",
            "evidence_refs": [],
        }
        for index in range(5)
    ]
    return f"""# Goal: Example
- Tag: `goal/example`
- Status: Active

## Lane Sequences

### `delivery`

| Step | Key | Tick | Status | Gate | Issue | Owner | Receipt |
| ---: | --- | --- | --- | --- | --- | --- | --- |
{rows}

### `foundation`

| Step | Key | Tick | Status | Gate | Issue | Owner | Receipt |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | ready | [x] | Closed | Foundation accepted | TBD:ready | Unassigned | receipt:ready |

## Dependencies

```json
{json.dumps(declarations, indent=2)}
```
"""


def _source_observations(dependency, *, resolved: bool = True):
    dependent = GoalRowSourceObservation(
        dependency.dependent,
        GoalRowResolutionOutcome.RESOLVED,
        source_revision_ref="goal-revision:dependent-7",
    )
    prerequisite = (
        GoalRowSourceObservation(
            dependency.prerequisite,
            GoalRowResolutionOutcome.RESOLVED,
            source_revision_ref="goal-revision:prerequisite-4",
            gate_digest="sha256:gate-current",
        )
        if resolved
        else GoalRowSourceObservation(
            dependency.prerequisite,
            GoalRowResolutionOutcome.UNRESOLVED,
        )
    )
    return dependent, prerequisite


def _acceptance_evidence(dependency, *, gate_digest: str = "sha256:gate-current"):
    return GoalDependencyEvidence(
        owner_goal_tag=dependency.owner_goal_tag,
        dependency_key=dependency.dependency_key,
        dependency_digest=dependency_definition_digest(dependency),
        prerequisite=dependency.prerequisite,
        dependent_source_revision_ref="goal-revision:dependent-7",
        prerequisite_source_revision_ref="goal-revision:prerequisite-4",
        prerequisite_gate_digest=gate_digest,
        kind=GoalDependencyEvidenceKind.ACCEPTANCE,
        evidence_ref=f"goal-gate-evidence:{dependency.dependency_key}",
        qualification_ref="evidence-qualification:accepted",
    )


def _evaluate(dependency, *, evidence=(), resolved: bool = True):
    dependent, prerequisite = _source_observations(dependency, resolved=resolved)
    return evaluate_goal_dependency(
        dependency,
        dependent=dependent,
        prerequisite=prerequisite,
        evidence=tuple(evidence),
        evaluator_ref=EVALUATOR_REF,
    )


def contract_wire() -> dict[str, object]:
    document = _document()
    projection = project_goal_dependencies(document)
    dependencies = projection.dependencies
    observations = {
        dependencies[1].dependency_key: _evaluate(dependencies[1]).to_wire(),
        dependencies[2].dependency_key: _evaluate(
            dependencies[2],
            evidence=(_acceptance_evidence(dependencies[2]),),
        ).to_wire(),
        dependencies[3].dependency_key: _evaluate(
            dependencies[3],
            evidence=(
                _acceptance_evidence(
                    dependencies[3], gate_digest="sha256:gate-previous"
                ),
            ),
        ).to_wire(),
        dependencies[4].dependency_key: _evaluate(
            dependencies[4], resolved=False
        ).to_wire(),
    }
    landscape = project_goal_landscape(
        document,
        source_path="docs/goals/example.md",
        observations=observations,
    )
    return compose_goal_dependency_view(landscape).to_wire()


def test_contract_matches_shared_five_state_fixture_and_round_trips() -> None:
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
    wire = contract_wire()

    assert decode_goal_dependency_view(wire).to_wire() == wire
    assert wire["schema_id"] == expected["schema_id"]
    assert [item["presentation_state"] for item in wire["dependencies"]] == (
        expected["presentation_states"]
    )
    assert wire["lane_relationships"] == expected["lane_relationships"]
    assert wire["cross_goal_relationships"] == expected["cross_goal_relationships"]


def test_lane_and_cross_goal_relationships_are_lossless_summaries() -> None:
    wire = contract_wire()

    assert wire["lane_relationships"] == [
        {
            "prerequisite_goal_tag": "goal/example",
            "prerequisite_lane_key": "foundation",
            "dependent_goal_tag": "goal/example",
            "dependent_lane_key": "delivery",
            "dependency_keys": ["dependency-0"],
        },
        {
            "prerequisite_goal_tag": "goal/external",
            "prerequisite_lane_key": "review",
            "dependent_goal_tag": "goal/example",
            "dependent_lane_key": "delivery",
            "dependency_keys": [
                "dependency-1",
                "dependency-2",
                "dependency-3",
                "dependency-4",
            ],
        },
    ]
    assert wire["cross_goal_relationships"] == [
        {
            "prerequisite_goal_tag": "goal/external",
            "dependent_goal_tag": "goal/example",
            "dependency_keys": [
                "dependency-1",
                "dependency-2",
                "dependency-3",
                "dependency-4",
            ],
        }
    ]
    carried = {
        key
        for relationship in wire["lane_relationships"]
        for key in relationship["dependency_keys"]
    }
    assert carried == {f"dependency-{index}" for index in range(5)}


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        (lambda wire: wire.update(extra="authority"), "unknown=.*extra"),
        (
            lambda wire: wire.update(effect_profile="dispatch_authorizing"),
            "effect_profile",
        ),
        (
            lambda wire: wire["dependencies"][0].update(presentation_state="pending"),
            "presentation_state",
        ),
        (
            lambda wire: wire["dependencies"][1]["operational_observation"].update(
                dependency_digest="sha256:different"
            ),
            "dependency_digest",
        ),
        (
            lambda wire: wire["lane_relationships"][0]["dependency_keys"].append(
                "fabricated"
            ),
            "lane_relationships",
        ),
    ),
)
def test_decoder_rejects_reconstruction_or_authority_drift(mutation, message) -> None:
    wire = deepcopy(contract_wire())
    mutation(wire)

    with pytest.raises((TypeError, ValueError), match=message):
        decode_goal_dependency_view(wire)


def test_duplicate_dependency_identity_fails_closed() -> None:
    wire = deepcopy(contract_wire())
    wire["dependencies"].append(deepcopy(wire["dependencies"][0]))

    with pytest.raises(ValueError, match="duplicate GoalDependency"):
        decode_goal_dependency_view(wire)
