import pytest
from aware_issue_operational_runtime import (
    IssueSourceScopeRefusal,
    evaluate_issue_source_scope,
    issue_scope_covers_path,
)


@pytest.mark.parametrize(
    "status", ["In Progress", "in_progress", "IN-PROGRESS", "  in   progress  "]
)
def test_existing_in_progress_spellings(status):
    result = evaluate_issue_source_scope(
        issue_owner="codex-owner",
        issue_status=status,
        scope_paths=("owned",),
        actor_ref="codex-owner",
        effect_paths=("owned/a", "owned/b/c"),
    )
    assert result.allowed


@pytest.mark.parametrize("status", ["Open", "Blocked", "Closed", "", "inprogress"])
def test_other_lifecycles_refuse(status):
    result = evaluate_issue_source_scope(
        issue_owner="codex-owner",
        issue_status=status,
        scope_paths=("owned",),
        actor_ref="codex-owner",
        effect_paths=("owned/a",),
    )
    assert result.refusal is IssueSourceScopeRefusal.STATUS_INVALID


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("owned", True),
        ("owned/a", True),
        ("owned/a/b", True),
        ("ownedness/a", False),
        ("other/owned", False),
        ("own", False),
    ],
)
def test_scope_uses_component_delimited_prefix(path, expected):
    assert issue_scope_covers_path(path=path, scope_paths=("owned",)) is expected


def test_refusal_precedence_matches_existing_publication():
    assert (
        evaluate_issue_source_scope(
            issue_owner="foreign",
            issue_status="Closed",
            scope_paths=(),
            actor_ref="codex-owner",
            effect_paths=("foreign",),
        ).refusal
        is IssueSourceScopeRefusal.OWNER_MISMATCH
    )
    result = evaluate_issue_source_scope(
        issue_owner="codex-owner",
        issue_status="In Progress",
        scope_paths=("owned",),
        actor_ref="codex-owner",
        effect_paths=("owned/a", "first", "second"),
    )
    assert result.refusal is IssueSourceScopeRefusal.OUT_OF_SCOPE
    assert result.offending_path == "first"


def test_empty_effects_preserve_policy_but_do_not_admit_an_operation():
    assert evaluate_issue_source_scope(
        issue_owner="codex-owner",
        issue_status="In Progress",
        scope_paths=(),
        actor_ref="codex-owner",
        effect_paths=(),
    ).allowed
