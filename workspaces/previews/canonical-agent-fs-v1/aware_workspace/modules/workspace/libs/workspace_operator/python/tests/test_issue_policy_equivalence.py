import itertools

import aware_workspace_operator.commit as owner
import pytest
from aware_issue_operational_runtime import evaluate_issue_source_scope


@pytest.mark.parametrize(
    ("issue_owner", "status", "paths"),
    list(
        itertools.product(
            ("codex-owner", "foreign"),
            (
                "In Progress",
                "in_progress",
                "IN-PROGRESS",
                " in  progress ",
                "Closed",
                "Open",
            ),
            (
                (),
                ("owned",),
                ("owned/a/b",),
                ("ownedness/a",),
                ("owned/a", "first", "second"),
            ),
        )
    ),
)
def test_publication_preserves_original_decisions_and_diagnostics(
    issue_owner, status, paths
):
    issue = owner._IssueMetadata(
        "issue.md", "issue-tag", issue_owner, status, ("owned",)
    )
    # Frozen legacy behavior as a test oracle only; production owns one policy.
    expected = None
    if issue_owner != "codex-owner":
        expected = f"Issue owner mismatch: issue owner is {issue_owner!r}, command owner is 'codex-owner'."
    elif (
        " ".join(status.strip().lower().replace("_", " ").replace("-", " ").split())
        != "in progress"
    ):
        expected = (
            f"Issue status must be In Progress for commit rail, found: {status!r}."
        )
    else:
        for path in paths:
            if path != "owned" and not path.startswith("owned/"):
                expected = f"Requested path is outside ownership scope: {path} (scope=['owned'])"
                break
    if expected is None:
        owner._validate_issue_and_paths(
            issue=issue, owner_id="codex-owner", requested_paths=paths
        )
    else:
        with pytest.raises(ValueError) as error:
            owner._validate_issue_and_paths(
                issue=issue, owner_id="codex-owner", requested_paths=paths
            )
        assert str(error.value) == expected


def test_publication_calls_original_issue_policy(monkeypatch):
    calls = []

    def observe(**kwargs):
        calls.append(kwargs)
        return evaluate_issue_source_scope(**kwargs)

    monkeypatch.setattr(owner, "evaluate_issue_source_scope", observe)
    issue = owner._IssueMetadata(
        "issue.md", "issue-tag", "codex-owner", "In Progress", ("owned",)
    )
    owner._validate_issue_and_paths(
        issue=issue, owner_id="codex-owner", requested_paths=("owned/a",)
    )
    assert len(calls) == 1
    assert calls[0]["effect_paths"] == ("owned/a",)


def test_authored_dependency_points_to_registered_original_package():
    import tomllib
    from pathlib import Path

    manifest = Path(__file__).parents[1] / "pyproject.toml"
    project = tomllib.loads(manifest.read_text())
    assert (
        "aware-issue-operational-runtime>=0.3.0,<0.4.0"
        in project["project"]["dependencies"]
    )
    target = (
        manifest.parent
        / project["tool"]["uv"]["sources"]["aware-issue-operational-runtime"]["path"]
    ).resolve()
    assert (
        tomllib.loads((target / "pyproject.toml").read_text())["project"]["name"]
        == "aware-issue-operational-runtime"
    )
