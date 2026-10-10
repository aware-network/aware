"""Neutral typed fixtures prove carriage/validation, never authorization."""

from dataclasses import FrozenInstanceError, replace

import pytest
from aware_specification_sdk import (
    SPECIFICATION_DRAFT_CLEANUP_PROFILE,
    SpecificationDraftCleanupEvidence,
    SpecificationDraftCleanupInvocation,
    SpecificationDraftCleanupLedger,
    SpecificationDraftCleanupRequest,
    SpecificationDraftIssueCleanup,
    SpecificationDraftPhysicalCleanup,
    SpecificationDraftPhysicalEffect,
    SpecificationOperationError,
)
from aware_specification_sdk.draft_cleanup import (
    require_cleanup_extension,
    snapshot_draft_cleanup,
)

SHA = "sha256:" + "1" * 64


def request(**changes):
    return replace(
        SpecificationDraftCleanupRequest(
            "issue:one",
            SHA,
            "config/aware.protocol.toml",
            SHA,
            "plans/demo",
            "plans/scratch",
            (("a", b"exact bytes"),),
            "intent:one",
            "client:one",
            "protocol_specification_draft_v1",
            "specification_draft_package_v1",
            SHA,
            ("plans/scratch", "plans/demo"),
        ),
        **changes,
    )


def ledger(**changes):
    return replace(
        SpecificationDraftCleanupLedger("none", (), (), (), False, True), **changes
    )


def effect():
    return SpecificationDraftPhysicalEffect(
        "plans/demo",
        "package_publication",
        "applied",
        None,
        None,
        None,
        None,
        None,
        False,
    )


def value(**changes):
    issue = SpecificationDraftIssueCleanup(
        request(), None, "unknown", "unknown", None, "unknown", "caller", None
    )
    physical = SpecificationDraftPhysicalCleanup(
        "/original/root",
        "plans/demo",
        "plans/scratch",
        False,
        "not_attempted",
        ledger(ledger_complete=None),
    )
    invocation = SpecificationDraftCleanupInvocation("unknown", "not_invoked", ())
    return replace(
        SpecificationDraftCleanupEvidence(
            SPECIFICATION_DRAFT_CLEANUP_PROFILE,
            "attempt:one",
            "not_entered",
            issue,
            physical,
            invocation,
            invocation,
            None,
            "unknown",
            (),
        ),
        **changes,
    )


def test_detaches_every_nested_value_and_preserves_missing_fields():
    original = value()
    copy = snapshot_draft_cleanup(original)
    assert copy == original and copy is not original
    assert copy.issue_disposition is not original.issue_disposition
    assert copy.issue_disposition.request is not original.issue_disposition.request
    assert (
        copy.physical_observation.evidence is not original.physical_observation.evidence
    )
    assert copy.issue_disposition.execution_ref is None
    assert copy.issue_disposition.physical_cleanup_attempted is None
    assert copy.physical_observation.evidence.ledger_complete is None
    assert copy.issue_disposition.request.ordered_members == (("a", b"exact bytes"),)
    assert copy.physical_observation.root_locator == "/original/root"
    with pytest.raises(FrozenInstanceError):
        copy.context_state = "entered"


def test_error_keyword_is_additive_and_detached():
    source = value()
    error = SpecificationOperationError(
        "primary", effect="unknown", cleanup_evidence=source
    )
    assert error.cleanup_evidence == source and error.cleanup_evidence is not source
    assert error.evidence is None and error.effect == "unknown"
    assert SpecificationOperationError("legacy").cleanup_evidence is None


@pytest.mark.parametrize(
    "changes",
    [
        {"profile": "future"},
        {"attempt_ref": ""},
        {"context_state": "success"},
        {"issue_disposition": object()},
        {"physical_observation": object()},
        {"physical_invocation": object()},
        {"protocol_invocation": object()},
        {"protocol_owner_attempted": False},
        {"protocol_owner_attempted": True},
        {"protocol_owner_outcome": "completed"},
        {"cleanup_diagnostics": []},
        {"cleanup_diagnostics": (None,)},
    ],
)
def test_malformed_and_unqualified_completion_refuse(changes):
    with pytest.raises((ValueError, TypeError)):
        value(**changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"ordered_members": []},
        {"ordered_members": (("a", bytearray(b"a")),)},
        {"ordered_members": (("b", b"b"), ("a", b"a"))},
        {"manifest_locator": "../a"},
        {"expected_issue_sha256": "bad"},
        {"ordered_effect_paths": []},
        {"candidate_sha256": "bad"},
    ],
)
def test_request_rejects_mutable_or_malformed_values(changes):
    with pytest.raises(ValueError):
        request(**changes)


def test_source_correlation_does_not_normalize_absolute_root():
    physical = replace(value().physical_observation, root_locator="/original//root")
    assert (
        value(physical_observation=physical).physical_observation.root_locator
        == "/original//root"
    )
    with pytest.raises(ValueError, match="source_mismatch"):
        value(physical_observation=replace(physical, target_path="plans/other"))
    with pytest.raises(ValueError, match="completeness"):
        replace(physical, evidence=ledger())


@pytest.mark.parametrize(
    "mutation",
    [
        "attempt",
        "request",
        "effects",
        "publication",
        "diagnostics",
        "invocation",
        "issue_attempted",
        "physical_attempted",
    ],
)
def test_known_history_cannot_regress(mutation):
    before = value()
    before = replace(
        before,
        issue_disposition=replace(
            before.issue_disposition,
            physical_claim="claimed",
            physical_cleanup_attempted=True,
            evidence=ledger(package_outcome="published", effects=(effect(),)),
        ),
        cleanup_diagnostics=("prior",),
        physical_observation=replace(before.physical_observation, attempted=True),
        physical_invocation=SpecificationDraftCleanupInvocation(
            "context", "returned", ()
        ),
    )
    after = before
    if mutation == "attempt":
        after = replace(after, attempt_ref="attempt:other")
    if mutation == "request":
        after = replace(
            after,
            issue_disposition=replace(
                after.issue_disposition, request=request(client_intent_id="other")
            ),
        )
    if mutation == "effects":
        after = replace(
            after,
            issue_disposition=replace(
                after.issue_disposition,
                evidence=replace(after.issue_disposition.evidence, effects=()),
            ),
        )
    if mutation == "publication":
        after = replace(
            after,
            issue_disposition=replace(
                after.issue_disposition,
                evidence=replace(
                    after.issue_disposition.evidence, package_outcome="none"
                ),
            ),
        )
    if mutation == "diagnostics":
        after = replace(after, cleanup_diagnostics=())
    if mutation == "invocation":
        after = replace(
            after,
            physical_invocation=SpecificationDraftCleanupInvocation(
                "context", "not_invoked", ()
            ),
        )
    if mutation == "issue_attempted":
        after = replace(
            after,
            issue_disposition=replace(
                after.issue_disposition, physical_cleanup_attempted=False
            ),
        )
    if mutation == "physical_attempted":
        after = replace(
            after,
            physical_observation=replace(after.physical_observation, attempted=False),
        )
    with pytest.raises(ValueError):
        require_cleanup_extension(before, after)


def test_history_extension_and_cleanup_residue_shrink_are_legal():
    original = value()
    old = replace(
        original,
        issue_disposition=replace(
            original.issue_disposition,
            evidence=ledger(
                effects=(effect(),), residual_scratch_paths=("plans/scratch/a",)
            ),
        ),
    )
    new = replace(
        old,
        issue_disposition=replace(
            old.issue_disposition,
            evidence=replace(
                old.issue_disposition.evidence,
                effects=(effect(), effect()),
                residual_scratch_paths=(),
            ),
        ),
    )
    require_cleanup_extension(old, new)


@pytest.mark.parametrize("unavailable", [False, True])
@pytest.mark.parametrize("malformed_error", [False, True])
def test_sdk_reconstruction_preserves_carrier_with_available_or_failed_ledger(
    unavailable,
    malformed_error,
):
    # Reuse existing neutral typed fixtures, not physical or policy doubles.
    from aware_specification_sdk import SpecificationSdkClient
    from test_draft_evidence import Provider, Reader, evidence
    from test_draft_evidence import request as draft_request

    cleanup = value(
        attempt_ref="attempt:one", issue_disposition=None, physical_observation=None
    )

    class OwnerReader(Reader):
        def observe_draft_cleanup(self):
            return cleanup

        def observe_draft_evidence(self):
            if unavailable and self.calls:
                raise OSError("ledger unavailable")
            return super().observe_draft_evidence()

    reader = OwnerReader(evidence())
    primary = SpecificationOperationError(
        "original_primary", effect="unknown", cleanup_evidence=cleanup
    )
    if malformed_error:
        primary.code = None
    provider = Provider(
        reader,
        failure=primary,
    )
    expected = "draft_provider_error_invalid" if malformed_error else "original_primary"
    with pytest.raises(SpecificationOperationError, match=expected) as caught:
        SpecificationSdkClient(provider, draft_evidence_reader=reader).create_draft(
            draft_request()
        )
    assert caught.value.cleanup_evidence == cleanup
    assert caught.value.cleanup_evidence is not cleanup
    assert caught.value.effect == "unknown"


@pytest.mark.parametrize("mutation", ["type", "missing", "mismatch"])
def test_sdk_post_publication_result_fault_preserves_cleanup(mutation):
    from aware_specification_sdk import SpecificationSdkClient
    from test_draft_evidence import Provider, Reader, evidence
    from test_draft_evidence import request as draft_request

    cleanup = value(issue_disposition=None, physical_observation=None)

    class OwnerReader(Reader):
        def observe_draft_cleanup(self):
            return cleanup

    def corrupt(result):
        if mutation == "type":
            return object()
        if mutation == "missing":
            object.__delattr__(result, "created_paths")
            return result
        return replace(result, authoring_intent_ref="other")

    reader = OwnerReader(evidence())
    with pytest.raises(SpecificationOperationError) as caught:
        SpecificationSdkClient(
            Provider(reader, transform=corrupt), draft_evidence_reader=reader
        ).create_draft(draft_request())
    assert caught.value.effect == "unknown"
    assert caught.value.evidence.package_outcome == "published"
    assert caught.value.cleanup_evidence == cleanup


@pytest.mark.parametrize("foreign_observer", [False, True])
def test_sdk_foreign_cleanup_never_substitutes_original_history(foreign_observer):
    from aware_specification_sdk import SpecificationSdkClient
    from test_draft_evidence import Provider, Reader, evidence
    from test_draft_evidence import request as draft_request

    original = value(issue_disposition=None, physical_observation=None)
    foreign = replace(original, attempt_ref="attempt:foreign")

    class OwnerReader(Reader):
        def observe_draft_cleanup(self):
            return foreign if foreign_observer else original

    reader = OwnerReader(evidence())
    provider = Provider(
        reader, failure=SpecificationOperationError("primary", cleanup_evidence=foreign)
    )
    with pytest.raises(SpecificationOperationError) as caught:
        SpecificationSdkClient(provider, draft_evidence_reader=reader).create_draft(
            draft_request()
        )
    assert caught.value.code == "primary"
    assert caught.value.effect == "unknown"
    assert caught.value.cleanup_evidence == (None if foreign_observer else original)
    assert "draft_cleanup_evidence_invalid" in caught.value.evidence_diagnostics


@pytest.mark.parametrize(
    "stage", ["lookup", "invocation", "validation", "returned_validation"]
)
@pytest.mark.parametrize("secondary", [RuntimeError, KeyboardInterrupt])
def test_secondary_cleanup_failure_preserves_primary_and_publication(
    monkeypatch, stage, secondary
):
    from aware_specification_sdk import SpecificationSdkClient, operation
    from test_draft_evidence import Provider, Reader, evidence
    from test_draft_evidence import request as draft_request

    cleanup = value(issue_disposition=None, physical_observation=None)
    observed = replace(cleanup)
    validate = operation.snapshot_draft_cleanup

    def validate_observation(candidate):
        if stage == "validation" and candidate is observed:
            raise secondary("secondary validation failure")
        if stage == "returned_validation" and candidate is primary_cleanup:
            raise secondary("secondary returned validation failure")
        return validate(candidate)

    class OwnerReader(Reader):
        @property
        def observe_draft_cleanup(self):
            if stage == "lookup":
                raise secondary("secondary lookup failure")
            return self.cleanup_observation

        def cleanup_observation(self):
            if stage == "invocation":
                raise secondary("secondary invocation failure")
            return observed

    primary = SpecificationOperationError("original_primary", cleanup_evidence=cleanup)
    primary_cleanup = primary.cleanup_evidence
    monkeypatch.setattr(operation, "snapshot_draft_cleanup", validate_observation)
    reader = OwnerReader(evidence())
    with pytest.raises(SpecificationOperationError) as caught:
        SpecificationSdkClient(
            Provider(reader, failure=primary), draft_evidence_reader=reader
        ).create_draft(draft_request())
    assert caught.value.code == "original_primary"
    assert caught.value.effect == "unknown"
    assert caught.value.evidence.package_outcome == "published"
    assert caught.value.cleanup_evidence == cleanup
    assert caught.value.__cause__ is primary
    expected = (
        "draft_cleanup_evidence_invalid"
        if stage == "returned_validation"
        else "draft_cleanup_observation_unavailable"
    )
    assert expected in caught.value.evidence_diagnostics


@pytest.mark.parametrize("holder", ["physical_invocation", "protocol_invocation"])
def test_invoked_history_cannot_return_to_not_invoked(holder):
    before = replace(
        value(),
        **{holder: SpecificationDraftCleanupInvocation("context", "invoked", ())},
    )
    after = replace(
        before,
        **{holder: SpecificationDraftCleanupInvocation("context", "not_invoked", ())},
    )
    with pytest.raises(ValueError, match="invocation_regressed"):
        require_cleanup_extension(before, after)


@pytest.mark.parametrize("holder", ["physical_invocation", "protocol_invocation"])
@pytest.mark.parametrize("mutation", ["responsibility", "diagnostics"])
def test_invoked_holder_and_diagnostics_cannot_regress(holder, mutation):
    before = replace(
        value(),
        **{
            holder: SpecificationDraftCleanupInvocation(
                "context", "invoked", ("original_fault",)
            )
        },
    )
    current = getattr(before, holder)
    if mutation == "responsibility":
        current = replace(current, responsibility="unknown")
    else:
        current = replace(current, diagnostics=())
    with pytest.raises(ValueError, match="invocation_regressed"):
        require_cleanup_extension(before, replace(before, **{holder: current}))


@pytest.mark.parametrize("holder", ["issue_disposition", "physical_observation"])
@pytest.mark.parametrize(
    ("old_outcome", "new_outcome"),
    [
        ("completed", "not_attempted"),
        ("completed", "unknown"),
        ("completed", "incomplete"),
        ("incomplete", "not_attempted"),
        ("incomplete", "unknown"),
        ("unknown", "not_attempted"),
    ],
)
def test_observed_cleanup_outcome_cannot_regress(holder, old_outcome, new_outcome):
    before = value()
    original = getattr(before, holder)
    outcome_key = (
        "physical_cleanup_outcome" if holder == "issue_disposition" else "outcome"
    )
    attempted_key = (
        "physical_cleanup_attempted" if holder == "issue_disposition" else "attempted"
    )
    before = replace(
        before,
        **{
            holder: replace(original, **{outcome_key: old_outcome, attempted_key: True})
        },
    )
    after = replace(
        before,
        **{holder: replace(getattr(before, holder), **{outcome_key: new_outcome})},
    )
    with pytest.raises(ValueError, match="outcome_regressed"):
        require_cleanup_extension(before, after)


@pytest.mark.parametrize("holder", ["physical_invocation", "protocol_invocation"])
@pytest.mark.parametrize(
    ("before", "after"),
    [("not_invoked", "invoked"), ("invoked", "returned"), ("invoked", "raised")],
)
def test_lawful_invocation_progress_remains_available(holder, before, after):
    original = replace(
        value(), **{holder: SpecificationDraftCleanupInvocation("context", before, ())}
    )
    current = replace(
        original, **{holder: SpecificationDraftCleanupInvocation("context", after, ())}
    )
    require_cleanup_extension(original, current)


@pytest.mark.parametrize("holder", ["issue_disposition", "physical_observation"])
@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("not_attempted", "unknown"),
        ("unknown", "completed"),
        ("unknown", "incomplete"),
        ("incomplete", "completed"),
    ],
)
def test_lawful_cleanup_outcome_progress_remains_available(holder, before, after):
    original = value()
    outcome_key = (
        "physical_cleanup_outcome" if holder == "issue_disposition" else "outcome"
    )
    attempted_key = (
        "physical_cleanup_attempted" if holder == "issue_disposition" else "attempted"
    )
    original = replace(
        original,
        **{
            holder: replace(
                getattr(original, holder),
                **{outcome_key: before, attempted_key: before != "not_attempted"},
            )
        },
    )
    current = replace(
        original,
        **{
            holder: replace(
                getattr(original, holder), **{outcome_key: after, attempted_key: True}
            )
        },
    )
    require_cleanup_extension(original, current)


@pytest.mark.parametrize("holder", ["issue_disposition", "physical_observation"])
def test_pre_attempt_unknown_can_become_observed_not_attempted(holder):
    original = value()
    outcome_key = (
        "physical_cleanup_outcome" if holder == "issue_disposition" else "outcome"
    )
    original = replace(
        original,
        **{holder: replace(getattr(original, holder), **{outcome_key: "unknown"})},
    )
    current = replace(
        original,
        **{
            holder: replace(getattr(original, holder), **{outcome_key: "not_attempted"})
        },
    )
    require_cleanup_extension(original, current)
