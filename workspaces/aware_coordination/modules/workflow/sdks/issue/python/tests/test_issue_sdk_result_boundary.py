from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest
from aware_issue_runtime import parse_issue_projection
from aware_issue_sdk import (
    IssueAppendEvidenceRequest,
    IssueAppendUpdateRequest,
    IssueBindScopePathsRequest,
    IssueBlockRequest,
    IssueCloseRequest,
    IssueCommitWorkspaceError,
    IssueCommitWorkspaceRequest,
    IssueCommitWorkspaceResult,
    IssueEnsureSnapshotRequest,
    IssueMutationError,
    IssueMutationOutcome,
    IssueMutationResult,
    IssueOperationContractError,
    IssueProviderResultError,
    IssuePublicationOutcome,
    IssueReadProjectionResolveError,
    IssueReadProjectionResolveOutcome,
    IssueReadProjectionResolveRequest,
    IssueReadProjectionResolveResult,
    IssueResumeRequest,
    IssueSdkOperationClient,
    IssueSetOwnerRequest,
    IssueStartProgressRequest,
)

ISSUE = "fb/2026-10-08/boundary"
OTHER = "fb/2026-10-08/foreign"
COMMON = {
    "issue_ref": ISSUE,
    "expected_source_sha256": "sha256:" + "a" * 64,
    "client_intent_id": "test",
    "actor_ref": "codex-test",
    "actor_evidence_ref": "evidence:test",
}
CASES = (
    ("resolve_read_projection", IssueReadProjectionResolveRequest(ISSUE)),
    (
        "ensure_issue_snapshot",
        IssueEnsureSnapshotRequest(
            ISSUE, "test", "P1", "codex-test", "evidence:test", "test"
        ),
    ),
    ("start_issue_progress", IssueStartProgressRequest(**COMMON)),
    ("block_issue", IssueBlockRequest(**COMMON)),
    ("resume_issue", IssueResumeRequest(**COMMON)),
    ("set_issue_owner", IssueSetOwnerRequest(**COMMON, new_owner_ref="codex-next")),
    (
        "bind_issue_scope_paths",
        IssueBindScopePathsRequest(**COMMON, scope_paths=("src/a.py",)),
    ),
    ("append_issue_update", IssueAppendUpdateRequest(**COMMON, message="test")),
    ("append_issue_evidence", IssueAppendEvidenceRequest(**COMMON, path="evidence:x")),
    (
        "close_issue",
        IssueCloseRequest(
            **COMMON,
            resolution="test",
            verified_by=("test",),
            publication_receipt_ref="git:" + "a" * 40,
        ),
    ),
    (
        "commit_workspace",
        IssueCommitWorkspaceRequest(
            ISSUE,
            "sha256:" + "a" * 64,
            ("src/a.py",),
            "test",
            "codex-test",
            "evidence:test",
            False,
        ),
    ),
)


def result_for(method, request):
    if method == "resolve_read_projection":
        return IssueReadProjectionResolveResult(
            IssueReadProjectionResolveOutcome.ABSENT,
            ISSUE,
            "test.provider",
            "test-provider",
            "1.0.0",
        )
    if method == "commit_workspace":
        return IssueCommitWorkspaceResult(
            IssuePublicationOutcome.APPLIED,
            ISSUE,
            ("src/a.py",),
            "test.provider",
            "test-provider",
            "1.0.0",
            "test.operator",
            "isolated_index_atomic_ref_v1",
            "a" * 40,
            "cas_applied",
            shared_index_projection="failed",
            shared_index_projection_error="test",
            index_reconciliation_pending=True,
        )
    return IssueMutationResult(
        request.operation_ref,
        IssueMutationOutcome.STALE,
        ISSUE,
        "test.provider",
        "test-provider",
        "1.0.0",
    )


class Provider:
    def __init__(self, result):
        self.result = result
        self.calls = 0
        self.lookups = 0

    def __getattr__(self, name):
        self.lookups += 1

        def call(request):
            self.calls += 1
            if isinstance(self.result, BaseException):
                raise self.result
            return self.result

        return call


@pytest.mark.parametrize("method,operation_request", CASES)
def test_valid_values_preserve_result_identity_and_single_call(
    method, operation_request
):
    result = result_for(method, operation_request)
    provider = Provider(result)
    assert (
        getattr(IssueSdkOperationClient(provider), method)(operation_request) is result
    )
    assert provider.calls == 1


@pytest.mark.parametrize("method,operation_request", CASES)
def test_invalid_request_precedes_even_provider_method_lookup(
    method, operation_request
):
    provider = Provider(result_for(method, operation_request))
    with pytest.raises(IssueProviderResultError) as failed:
        getattr(IssueSdkOperationClient(provider), method)({"issue_ref": ISSUE})
    assert isinstance(failed.value, IssueOperationContractError)
    assert failed.value.failure.phase == "request"
    assert failed.value.effect == "none"
    assert failed.value.failure.provider_invoked is False
    assert provider.calls == provider.lookups == 0


@pytest.mark.parametrize("method,operation_request", CASES)
@pytest.mark.parametrize("foreign", [False, True])
def test_untyped_and_foreign_issue_results_refuse(method, operation_request, foreign):
    result = (
        replace(result_for(method, operation_request), issue_ref=OTHER)
        if foreign
        else {"outcome": "pretend_success", "raw_markdown": "do not export this"}
    )
    provider = Provider(result)
    with pytest.raises(IssueProviderResultError) as failed:
        getattr(IssueSdkOperationClient(provider), method)(operation_request)
    error = failed.value
    assert error.provider_result is result
    assert error.effect == "unknown"
    assert error.failure.issue_ref == ISSUE
    assert error.failure.provider_invoked is True
    assert error.failure.phase == "result"
    payload = error.to_wire()
    assert payload["provider_report_grade"] == "unvalidated_provider_report"
    assert "raw_markdown" not in str(payload)
    if foreign:
        assert payload["provider_result"]["issue_ref"] == OTHER
    assert provider.calls == 1


def test_wrong_mutation_operation_is_not_accepted():
    method, request = CASES[7]
    result = replace(result_for(method, request), operation_ref="issue_sdk.block_issue")
    with pytest.raises(IssueProviderResultError):
        IssueSdkOperationClient(Provider(result)).append_issue_update(request)


@pytest.mark.parametrize(
    "mutation", ["paths", "duplicate_paths", "preview", "planned", "cas_failed"]
)
def test_publication_correlation_keeps_original_receipt(mutation):
    method, request = CASES[-1]
    result = result_for(method, request)
    if mutation == "paths":
        result = replace(result, target_paths=("src/foreign.py",))
    elif mutation == "duplicate_paths":
        result = replace(result, target_paths=("src/a.py", "src/a.py"))
    elif mutation == "preview":
        request = replace(request, dry_run=True)
    elif mutation == "planned":
        result = replace(
            result, outcome=IssuePublicationOutcome.PLANNED, commit_hash=None
        )
    else:
        result = replace(result, reference_update="cas_failed")
    with pytest.raises(IssueProviderResultError) as failed:
        IssueSdkOperationClient(Provider(result)).commit_workspace(request)
    payload = failed.value.to_wire()["provider_result"]
    assert failed.value.provider_result is result
    assert payload["commit_hash"] == result.commit_hash
    assert payload["reference_update"] == result.reference_update
    assert payload["transaction_mode"] == result.transaction_mode
    assert payload["index_reconciliation_pending"] is True


@pytest.mark.parametrize(
    "exception", [ValueError, RuntimeError, KeyboardInterrupt, SystemExit]
)
def test_provider_failure_preserves_cause_and_detached_evidence(exception):
    method, request = CASES[-1]
    result = result_for(method, request)
    original = exception("not exported")
    original.provider_result = result
    provider = Provider(original)
    with pytest.raises(IssueProviderResultError) as failed:
        IssueSdkOperationClient(provider).commit_workspace(request)
    assert failed.value.__cause__ is original
    assert failed.value.provider_result is result
    assert failed.value.failure.phase == "provider"
    assert failed.value.effect == "unknown"
    snapshot = failed.value.to_wire()
    object.__setattr__(result, "commit_hash", "b" * 40)
    assert failed.value.to_wire() == snapshot
    assert provider.calls == 1


def test_nested_projection_shape_refuses_without_reparsing_source():
    projection = parse_issue_projection(
        text=f"# Issue: test\n\n- Tag: `{ISSUE}`\n",
        source_path="docs/issues/2026/10/08/test.md",
    )
    result = IssueReadProjectionResolveResult(
        IssueReadProjectionResolveOutcome.FOUND,
        ISSUE,
        "test.provider",
        "test-provider",
        "1.0.0",
        projection,
    )
    object.__setattr__(projection, "ownership_scope", ["src/a.py"])
    with pytest.raises(IssueProviderResultError) as failed:
        IssueSdkOperationClient(Provider(result)).resolve_read_projection(CASES[0][1])
    assert failed.value.provider_result is result
    assert "projection" not in failed.value.to_wire()["provider_result"]


def test_hostile_serialization_hooks_are_not_called():
    class Hostile:
        def to_wire(self):
            raise AssertionError("must not call")

        def __repr__(self):
            raise AssertionError("must not call")

    value = Hostile()
    with pytest.raises(IssueProviderResultError) as failed:
        IssueSdkOperationClient(Provider(value)).commit_workspace(CASES[-1][1])
    assert failed.value.provider_result is value
    assert failed.value.to_wire()["provider_result"] is None


def test_large_evidence_does_not_erase_small_publication_coordinates():
    result = replace(result_for(*CASES[-1]), evidence=("x" * 100000,))
    provider = Provider(replace(result, issue_ref=OTHER))
    with pytest.raises(IssueProviderResultError) as failed:
        IssueSdkOperationClient(provider).commit_workspace(CASES[-1][1])
    payload = failed.value.to_wire()
    assert payload["provider_result"]["publication_receipt_ref"] == "git:" + "a" * 40
    assert (
        "provider_report_field_unavailable:evidence" in payload["capture_diagnostics"]
    )


def test_failure_value_is_not_its_exception_or_a_permit():
    provider = Provider(result_for(*CASES[-1]))
    with pytest.raises(IssueProviderResultError) as failed:
        IssueSdkOperationClient(provider).commit_workspace(
            replace(CASES[-1][1], dry_run=True)
        )
    value = failed.value.failure
    assert type(value) is IssueCommitWorkspaceError
    assert not isinstance(value, BaseException)
    with pytest.raises(FrozenInstanceError):
        value.effect = "published"
    with pytest.raises(IssueOperationContractError):
        replace(value, effect="none")
    assert IssueMutationError.contract == "aware.issue.mutation-error.v1"
    assert (
        IssueReadProjectionResolveError.contract
        == "aware.issue.read-projection-resolve-error.v1"
    )


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("schema_version", "unknown.version"),
        ("source_digest", "not-a-digest"),
        ("activities", ["mutable"]),
    ],
)
def test_projection_contract_corruption_is_a_result_failure(field_name, value):
    projection = parse_issue_projection(
        text=f"# Issue: test\n\n- Tag: `{ISSUE}`\n",
        source_path="docs/issues/2026/10/08/test.md",
    )
    result = IssueReadProjectionResolveResult(
        IssueReadProjectionResolveOutcome.FOUND,
        ISSUE,
        "test.provider",
        "test-provider",
        "1.0.0",
        projection,
    )
    object.__setattr__(projection, field_name, value)
    with pytest.raises(IssueProviderResultError) as failed:
        IssueSdkOperationClient(Provider(result)).resolve_read_projection(CASES[0][1])
    assert failed.value.failure.phase == "result"
    assert failed.value.provider_result is result


def test_provider_exception_property_is_not_called():
    class PropertyError(ValueError):
        @property
        def provider_result(self):
            raise AssertionError("do not execute arbitrary properties")

    original = PropertyError("test")
    with pytest.raises(IssueProviderResultError) as failed:
        IssueSdkOperationClient(Provider(original)).commit_workspace(CASES[-1][1])
    assert failed.value.__cause__ is original
    assert failed.value.provider_result is original
    assert failed.value.to_wire()["provider_result"] is None
