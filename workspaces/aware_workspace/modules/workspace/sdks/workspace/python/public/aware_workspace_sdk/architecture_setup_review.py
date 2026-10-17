"""Explicitly selected, SDK-carried two-review Workspace setup workflow."""

from __future__ import annotations

import importlib
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aware_issue_sdk.operation import IssueMutationError, IssueMutationResult

from .architecture_setup_review_values import (
    ReviewedSetupApplyInputs,
    ReviewedSetupScopeInputs,
    ReviewPurpose,
    SetupApplyDecision,
    SetupCommandOutcome,
    SetupConciseResult,
    SetupEvidenceRead,
    SetupEvidenceRef,
    SetupReviewClientCleanup,
    SetupReviewError,
    SetupReviewFailure,
    SetupReviewRead,
    SetupReviewRequest,
    SetupScopeCompletion,
    SetupScopeContinuation,
    SetupScopeDecision,
    SetupTarget,
    SetupUnknownScopeOutcome,
)

_TOKEN = object()


def concise_result(value: SetupReviewRead | SetupCommandOutcome) -> SetupConciseResult:
    """Owner projection; retained references never imply unobserved publication."""
    from .architecture_setup_review_codec import review_value_to_json

    if type(value) is SetupReviewRead:
        result = SetupConciseResult(
            "preview_completed",
            value.reference,
            "scope_review"
            if value.record.scope_outcome_ref is None
            else "apply_review",
            "captured",
            value.private_observation.ledger_complete,
            (),
            False,
        )
    elif type(value) is SetupCommandOutcome:
        if (
            value.reference is None
            or value.retention.status != "published"
            or not value.retention.ledger_complete
        ):
            raise ValueError("complete_retained_capture_required_for_concise_output")
        result = SetupConciseResult(
            value.product_status,
            value.reference,
            "none",
            value.retention.status,
            value.retention.ledger_complete,
            value.diagnostics,
            False,
        )
    else:
        raise TypeError("original_review_or_command_outcome_required")
    if len(review_value_to_json(result).encode("utf-8")) > 16_384:
        raise ValueError("concise_result_budget_exceeded")
    return result


class WorkspaceSetupReviewClient:
    """Own one explicit private root; release it after completing the workflow."""

    def __init__(self, runtime, token):
        if token is not _TOKEN:
            raise TypeError("select_review_provider_explicitly")
        self._runtime = runtime

    @classmethod
    def filesystem(
        cls,
        *,
        repository_root: Path,
        evidence_root: Path,
        execution_id: str,
        authority_manifest_locator: str,
    ) -> WorkspaceSetupReviewClient:
        fs = importlib.import_module(
            "aware_workspace_fs_adapter.architecture_setup_review"
        )
        runtime = importlib.import_module(
            "aware_workspace_runtime.architecture_setup_review"
        )
        return cls(
            runtime.WorkspaceSetupReviewRuntime(
                repository_root=repository_root,
                evidence_root=evidence_root,
                execution_id=execution_id,
                authority_manifest_locator=authority_manifest_locator,
                storage_factory=fs.FilesystemSetupReview,
            ),
            _TOKEN,
        )

    def preview_review(
        self,
        request: SetupReviewRequest,
        *,
        scope_continuation: SetupScopeContinuation | None = None,
    ) -> SetupReviewRead:
        return self._runtime.preview_review(
            request, scope_continuation=scope_continuation
        )

    def read_review(
        self,
        reference: SetupEvidenceRef,
        *,
        expected_target: SetupTarget,
        purpose: ReviewPurpose,
    ) -> SetupReviewRead:
        return self._runtime.read_review(
            reference, expected_target=expected_target, purpose=purpose
        )

    def record_review_decision(
        self,
        reference: SetupEvidenceRef,
        *,
        decision: SetupScopeDecision | SetupApplyDecision,
    ) -> ReviewedSetupScopeInputs | ReviewedSetupApplyInputs:
        return self._runtime.record_review_decision(reference, decision=decision)

    def record_scope_outcome(
        self,
        scope_inputs: ReviewedSetupScopeInputs,
        *,
        outcome: IssueMutationResult | IssueMutationError | SetupUnknownScopeOutcome,
    ) -> SetupScopeCompletion:
        return self._runtime.record_scope_outcome(scope_inputs, outcome=outcome)

    def apply_reviewed(
        self, inputs: ReviewedSetupApplyInputs, *, client_intent_id: str
    ) -> SetupCommandOutcome:
        return self._runtime.apply_reviewed(inputs, client_intent_id=client_intent_id)

    def read_evidence(
        self, reference: SetupEvidenceRef, *, expected_target: SetupTarget
    ) -> SetupEvidenceRead:
        return self._runtime.read_evidence(reference, expected_target=expected_target)

    def release_client(self) -> SetupReviewClientCleanup:
        return self._runtime.release_client()

    def __enter__(self):
        return self

    def __exit__(self, _kind, error, _traceback):
        try:
            cleanup = self.release_client()
        except BaseException as cleanup_error:
            if error is None:
                raise
            cleanup = getattr(getattr(cleanup_error, "failure", None), "cleanup", None)
            BaseException.__setattr__(
                error, "setup_review_cleanup_failure", cleanup_error
            )
        if error is not None:
            BaseException.__setattr__(error, "setup_review_client_cleanup", cleanup)
            prefix = (
                error.failure
                if type(error) is SetupReviewError
                else getattr(error, "setup_review_failure", None)
            )
            if type(prefix) is SetupReviewFailure:
                prefix = replace(prefix, cleanup=cleanup)
                if type(error) is SetupReviewError:
                    error.failure = prefix
                else:
                    BaseException.__setattr__(error, "setup_review_failure", prefix)
        return False
