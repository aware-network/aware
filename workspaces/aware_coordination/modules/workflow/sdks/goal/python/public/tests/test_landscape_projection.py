from dataclasses import replace

import pytest

from aware_goal_service_view_compat.landscape_projection import project_goal_landscape
from aware_goal_operational_runtime.dependency_evaluation import (
    GoalRowSourceObservation, GoalRowResolutionOutcome,
    GoalDependencyEvidence, GoalDependencyEvidenceKind,
    dependency_definition_digest, evaluate_goal_dependency,
)
from test_dependency_projection import declaration, document


@pytest.mark.parametrize('state', ['not_evaluated', 'pending', 'satisfied', 'stale', 'unresolved'])
def test_five_cases_preserve_runtime_payload(state):
    source = document([declaration()])
    dependency = project_goal_landscape(source).projection.dependencies[0]
    dependent = GoalRowSourceObservation(dependency.dependent, GoalRowResolutionOutcome.RESOLVED, source_revision_ref='rev:d')
    prerequisite = GoalRowSourceObservation(dependency.prerequisite, GoalRowResolutionOutcome.RESOLVED, source_revision_ref='rev:p', gate_digest='digest:g')
    evidence = GoalDependencyEvidence(
        owner_goal_tag=dependency.owner_goal_tag, dependency_key=dependency.dependency_key,
        dependency_digest=dependency_definition_digest(dependency), prerequisite=dependency.prerequisite,
        dependent_source_revision_ref='rev:d', prerequisite_source_revision_ref='rev:p',
        prerequisite_gate_digest='digest:g', kind=GoalDependencyEvidenceKind.ACCEPTANCE,
        evidence_ref='evidence:1', qualification_ref='qualification:1',
    )
    if state == 'stale':
        evidence = replace(evidence, prerequisite_source_revision_ref='rev:old')
    if state == 'unresolved':
        prerequisite = GoalRowSourceObservation(dependency.prerequisite, GoalRowResolutionOutcome.UNRESOLVED)
    raw = None if state == 'not_evaluated' else evaluate_goal_dependency(
        dependency, dependent=dependent, prerequisite=prerequisite,
        evidence=(evidence,) if state in ('satisfied', 'stale') else (), evaluator_ref='evaluator:test',
    ).to_wire()
    result = project_goal_landscape(source, observations={dependency.dependency_key: raw}).to_json()
    entry = result['dependencies'][0]
    assert entry['operational_observation'] == raw
    if raw is not None:
        assert raw['satisfaction'] == state
    assert entry['declaration_digest'] == dependency_definition_digest(dependency)
    assert entry['document_presence']['prerequisite'] == 'external_unresolved'
    assert result['currentness_evidence'] is None
    assert 'satisfaction' not in entry


def test_rejects_unknown_and_authorizing_payloads():
    source = document([declaration()])
    with pytest.raises(ValueError):
        project_goal_landscape(source, observations={'invented': None})
    with pytest.raises(ValueError):
        project_goal_landscape(source, observations={'shipping-review': {'effect_profile': 'dispatch'}})
