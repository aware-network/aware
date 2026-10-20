import json

import pytest

from aware_goal_service_view_compat.dependency_projection import project_goal_dependencies


SOURCE = '''# Goal: Example
- Tag: goal/example
- Status: Active

## Lane Sequences
### delivery
| Step | Key | Tick | Status | Gate | Issue | Owner | Receipt |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ship | [!] | Blocked | Wait for review | TBD:ship | Unassigned | Pending |
'''


def declaration():
    return dict(
        dependency_key="shipping-review", dependent_lane_key="delivery",
        dependent_row_key="ship", prerequisite_goal_tag="goal/external",
        prerequisite_lane_key="review", prerequisite_row_key="accept",
        relation="requires_acceptance", reason="Independent review",
    )


def document(rows):
    return SOURCE + '\n## Dependencies\n\n```json\n' + json.dumps(rows) + '\n```\n'


def test_prose_does_not_create_edges():
    assert project_goal_dependencies(SOURCE).dependencies == ()


def test_external_edge_preserved_and_never_satisfied():
    result = project_goal_dependencies(document([declaration()])).to_json()
    edge = result['dependencies'][0]
    assert edge['dependent_resolution'] == 'present'
    assert edge['prerequisite_resolution'] == 'external_unresolved'
    assert edge['satisfaction'] == 'unknown'
    assert result['source_sha256'] == result['goal_view']['provenance']['source_sha256']


def test_unknown_local_row_remains_visible():
    row = declaration()
    row['prerequisite_goal_tag'] = 'goal/example'
    edge = project_goal_dependencies(document([row])).to_json()['dependencies'][0]
    assert edge['prerequisite_resolution'] == 'unresolved'


def test_invalid_edges_and_syntax_fail_closed():
    for rows in ([declaration(), declaration()], [dict(declaration(), guessed=True)]):
        with pytest.raises((ValueError, TypeError)):
            project_goal_dependencies(document(rows))
    with pytest.raises(ValueError):
        project_goal_dependencies(SOURCE + '\n## Dependencies\nreview then ship')
    with pytest.raises(ValueError):
        project_goal_dependencies(document([]) + '\n## Dependencies\n```json\n[]\n```')


def test_fenced_heading_example_is_not_authority():
    assert project_goal_dependencies(SOURCE + '\n````markdown\n## Dependencies\n```json\n[]\n```\n````').dependencies == ()
