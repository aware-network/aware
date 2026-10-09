"""Real owning publication followed by SDK return-boundary refusal."""

from dataclasses import replace

import pytest
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_issue_sdk import (
    IssueCloseRequest,
    IssueCommitWorkspaceRequest,
    IssueProviderResultError,
    IssueSdkOperationClient,
)
from test_provider import (
    ISSUE_REF,
    _digest,
    _git,
    _mutation_kwargs,
    _publication_repository,
    _publish_implementation,
)


class ReturnedFailure:
    def __init__(self, provider, method, mode):
        self.provider, self.method, self.mode = provider, method, mode
        self.calls = 0
        self.published = None

    def __getattr__(self, name):
        if name != self.method:
            return getattr(self.provider, name)

        def invoke(operation_request):
            self.calls += 1
            self.published = getattr(self.provider, name)(operation_request)
            if self.mode == "raise":
                error = ValueError("late provider result failure")
                error.provider_result = self.published
                raise error
            if name == "close_issue":
                return replace(self.published, operation_ref="issue_sdk.block_issue")
            return replace(self.published, issue_ref="fb/2026-10-08/foreign")

        return invoke


@pytest.mark.parametrize("mode", ["foreign", "raise"])
@pytest.mark.parametrize("method", ["commit_workspace", "close_issue"])
def test_real_publication_is_preserved_after_return_validation_failure(
    tmp_path, mode, method
):
    repository, target = _publication_repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    provider = FilesystemIssueOperationProvider(repository_root=repository)
    if method == "close_issue":
        issue.write_text(
            issue.read_text().replace(
                "- `src/example.py`",
                "- `src/example.py`\n- `docs/issues/2026/09/20/fb-2026-09-20-example.md`",
            )
        )
        implementation = _publish_implementation(
            repository=repository, issue=issue, client=IssueSdkOperationClient(provider)
        )
        operation_request = IssueCloseRequest(
            **_mutation_kwargs(issue, intent="close-return-failure"),
            resolution="Test complete",
            verified_by=("test:proof",),
            publication_receipt_ref=implementation,
        )
    else:
        operation_request = IssueCommitWorkspaceRequest(
            issue_ref=ISSUE_REF,
            expected_issue_source_sha256=_digest(issue),
            target_paths=("src/example.py",),
            message="real SDK boundary proof",
            actor_ref="codex-example",
            actor_evidence_ref="evidence:boundary",
            dry_run=False,
        )
    foreign = repository / "foreign.txt"
    foreign.write_text("foreign staged bytes\n")
    _git(repository, "add", "foreign.txt")
    foreign.write_text("foreign working bytes\n")
    original_index = _git(repository, "ls-files", "--stage", "foreign.txt")
    before_head = _git(repository, "rev-parse", "HEAD")
    wrapped = ReturnedFailure(provider, method, mode)
    with pytest.raises(IssueProviderResultError) as failed:
        getattr(IssueSdkOperationClient(wrapped), method)(operation_request)

    after_head = _git(repository, "rev-parse", "HEAD")
    assert after_head != before_head
    assert (
        _git(repository, "rev-list", "--count", f"{before_head}..{after_head}") == "1"
    )
    assert wrapped.calls == 1
    assert failed.value.effect == "unknown"
    assert failed.value.failure.phase == ("provider" if mode == "raise" else "result")
    report = failed.value.to_wire()["provider_result"]
    receipt_field = (
        "closeout_publication_receipt_ref"
        if method == "close_issue"
        else "publication_receipt_ref"
    )
    assert report[receipt_field] == "git:" + after_head
    if method == "commit_workspace":
        assert report["reference_update"] == "cas_applied"
    else:
        assert "reference_update" not in report  # The owner does not return this field.
    assert report["shared_index_projection"] == "applied"
    assert report["index_reconciliation_pending"] is False
    assert failed.value.to_wire()["issue_ref"] == ISSUE_REF
    assert report["issue_ref"] == (
        ISSUE_REF
        if mode == "raise" or method == "close_issue"
        else "fb/2026-10-08/foreign"
    )
    if mode == "foreign" and method == "close_issue":
        assert report["operation_ref"] == "issue_sdk.block_issue"
    if method == "close_issue":
        assert "- Status: Closed" in issue.read_text()
        assert (
            _git(repository, "show", f"HEAD:{issue.relative_to(repository).as_posix()}")
            == issue.read_text().strip()
        )
    else:
        assert _git(repository, "show", "HEAD:src/example.py") == "after"
    assert target.read_text() == "after\n"
    assert _git(repository, "ls-files", "--stage", "foreign.txt") == original_index
    assert foreign.read_text() == "foreign working bytes\n"
