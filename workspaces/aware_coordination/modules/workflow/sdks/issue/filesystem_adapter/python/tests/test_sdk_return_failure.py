"""Real owning publication followed by SDK return-boundary refusal."""

import json
from dataclasses import replace

import pytest
from aware_issue_sdk import (
    IssueCloseRequest,
    IssueCommitWorkspaceRequest,
)
from aware_issue_sdk.repository_publication import (
    IssueRepositoryOperationResult,
    IssueRepositoryPublicationRefusal,
)
from test_provider import (
    ISSUE_REF,
    _digest,
    _git,
    _mutation_kwargs,
    _publication_client,
    _publication_repository,
    _publish_implementation,
)


class ReturnedFailure:
    def __init__(self, provider, method, mode):
        self.provider, self.method, self.mode = provider, method, mode
        self.original = getattr(provider, method)
        self.calls = 0
        self.published = None

    def __getattr__(self, name):
        if name != self.method:
            return getattr(self.provider, name)

        def invoke(operation_request):
            self.calls += 1
            self.published = self.original(operation_request)
            if self.mode == "untyped":
                return self.published.to_wire()
            if self.mode == "raise":
                error = ValueError("late provider result failure")
                error.provider_result = self.published
                raise error
            if name == "close_issue":
                return replace(self.published, operation_ref="issue_sdk.block_issue")
            if type(self.published) is IssueRepositoryOperationResult:
                payload = self.published.to_wire()
                payload["issue_ref"] = "fb/2026-10-08/foreign"
                return IssueRepositoryOperationResult(json.dumps(payload))
            return replace(self.published, issue_ref="fb/2026-10-08/foreign")

        return invoke


@pytest.mark.parametrize("mode", ["foreign", "raise", "untyped"])
@pytest.mark.parametrize("method", ["commit_workspace", "close_issue"])
def test_real_publication_is_preserved_after_return_validation_failure(
    tmp_path, monkeypatch, mode, method
):
    monkeypatch.setenv("CODEX_THREAD_ID", "example")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    repository, target = _publication_repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    issue.write_text(
        issue.read_text().replace(
            "- `src/example.py`",
            "- `src/example.py`\n- `" + issue.relative_to(repository).as_posix() + "`",
        )
    )
    client = _publication_client(repository)
    if method == "close_issue":
        implementation = _publish_implementation(
            repository=repository, issue=issue, client=client
        )
        request = IssueCloseRequest(
            **_mutation_kwargs(issue, intent="close-return-failure"),
            resolution="Test complete",
            verified_by=("test:proof",),
            publication_receipt_ref=implementation,
        )
    else:
        request = IssueCommitWorkspaceRequest(
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
    index = _git(repository, "ls-files", "--stage", "foreign.txt")
    before = _git(repository, "rev-parse", "HEAD")
    owner = client.repository_client._provider
    wrapped = ReturnedFailure(owner, method + "_result", mode)
    port = getattr(wrapped, method + "_result")
    monkeypatch.setattr(owner, method + "_result", port)
    # The wrapper retains the original callable rather than redispatching the
    # patched owner, so this is exactly one real publication.
    with pytest.raises(IssueRepositoryPublicationRefusal) as failed:
        getattr(client, method)(request)
    after = _git(repository, "rev-parse", "HEAD")
    assert (
        after != before
        and _git(repository, "rev-list", "--count", before + ".." + after) == "1"
    )
    assert wrapped.calls == 1
    retained = failed.value.consumer_result.to_wire()
    assert retained["workspace_result"]["commit_hash"] == after
    assert retained["workspace_result"]["publication_state"] == "published"
    assert len(retained["workspace_result"]["original_writer_report"]) == 32
    assert _git(repository, "ls-files", "--stage", "foreign.txt") == index
    assert foreign.read_text() == "foreign working bytes\n"
    assert target.read_text() == "after\n"
    if method == "close_issue":
        assert "- Status: Closed" in issue.read_text()
        assert (
            retained["issue_observation"]["source_observation"]["source_change_state"]
            == "applied"
        )
