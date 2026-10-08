"""Neutral receipt carriage, not issuance of Protocol cleanup authority."""

from dataclasses import asdict, replace

import pytest
from aware_specification_sdk import SpecificationOperationError
from aware_specification_sdk.draft_cleanup import (
    require_cleanup_extension,
    snapshot_draft_cleanup,
)
from test_draft_input_custody import sample


def completion(attempted, outcome):
    value = sample()
    return replace(
        value,
        input_custody=replace(
            value.input_custody,
            protocol=replace(
                value.input_custody.protocol,
                owner_cleanup_attempted=attempted,
                owner_cleanup_outcome=outcome,
            ),
        ),
        protocol_owner_attempted=attempted,
        protocol_owner_outcome=outcome,
    )


@pytest.mark.parametrize(
    "attempted,outcome",
    [
        (False, "not_attempted"),
        (True, "completed"),
        (True, "incomplete"),
        (True, "unknown"),
    ],
)
def test_exact_correlated_carriage_is_detached_and_non_authorizing(attempted, outcome):
    value = completion(attempted, outcome)
    snapshot = snapshot_draft_cleanup(value)
    assert asdict(snapshot) == asdict(value)
    assert snapshot.input_custody is not value.input_custody
    error = SpecificationOperationError(
        "primary", effect="unknown", cleanup_evidence=value
    )
    assert error.cleanup_evidence == value
    assert error.effect == "unknown"


@pytest.mark.parametrize("nested", [False, True])
def test_historical_unknown_is_not_recomputed_from_nested_completion(nested):
    value = completion(True, "completed")
    historical = replace(
        value,
        input_custody=value.input_custody if nested else None,
        protocol_owner_attempted=None,
        protocol_owner_outcome="unknown",
    )
    assert asdict(snapshot_draft_cleanup(historical)) == asdict(historical)
    assert historical.protocol_owner_attempted is None
    assert historical.protocol_owner_outcome == "unknown"


@pytest.mark.parametrize(
    "field",
    [
        "execution_ref",
        "context_ref",
        "root_locator",
        "manifest_locator",
        "manifest_sha256",
        "target_locator",
        "scratch_locator",
    ],
)
def test_missing_correlation_cannot_support_known_completion(field):
    value = completion(True, "completed")
    with pytest.raises(ValueError):
        replace(value, input_custody=replace(value.input_custody, **{field: None}))


@pytest.mark.parametrize(
    "attempted,outcome",
    [
        (False, "completed"),
        (True, "not_attempted"),
        (None, "completed"),
        (1, "completed"),
    ],
)
def test_unpaired_or_untyped_projection_refuses(attempted, outcome):
    with pytest.raises(ValueError):
        replace(
            completion(True, "completed"),
            protocol_owner_attempted=attempted,
            protocol_owner_outcome=outcome,
        )


def test_data_without_nested_source_evidence_cannot_assert_completion():
    with pytest.raises(ValueError):
        replace(completion(True, "completed"), input_custody=None)


@pytest.mark.parametrize("outcome", ["completed", "incomplete", "unknown"])
def test_typed_but_mismatched_nested_outcome_refuses(outcome):
    other = "unknown" if outcome != "unknown" else "incomplete"
    with pytest.raises(ValueError, match="unqualified_protocol_cleanup_completion"):
        replace(completion(True, outcome), protocol_owner_outcome=other)


@pytest.mark.parametrize("outcome", ["completed", "incomplete", "unknown"])
def test_original_attempt_progress_is_accepted(outcome):
    require_cleanup_extension(
        completion(False, "not_attempted"), completion(True, outcome)
    )


@pytest.mark.parametrize(
    "old,new",
    [
        ("completed", "unknown"),
        ("completed", "incomplete"),
        ("incomplete", "completed"),
        ("unknown", "completed"),
        ("unknown", "incomplete"),
    ],
)
def test_later_disposal_cannot_rewrite_original_outcome(old, new):
    with pytest.raises(ValueError, match="draft_protocol_cleanup_history_regressed"):
        require_cleanup_extension(completion(True, old), completion(True, new))


@pytest.mark.parametrize("outcome", ["completed", "incomplete", "unknown"])
def test_known_original_attempt_cannot_disappear(outcome):
    previous = completion(True, outcome)
    with pytest.raises(ValueError):
        require_cleanup_extension(previous, completion(False, "not_attempted"))
    with pytest.raises(ValueError):
        require_cleanup_extension(
            previous,
            replace(
                previous,
                protocol_owner_attempted=None,
                protocol_owner_outcome="unknown",
            ),
        )


def test_separate_physical_progress_remains_lawful():
    final = completion(True, "completed")
    before = replace(
        final,
        input_custody=replace(
            final.input_custody,
            physical=replace(
                final.input_custody.physical, owner_cleanup_outcome="incomplete"
            ),
        ),
    )
    require_cleanup_extension(before, final)


@pytest.mark.parametrize("observer_failure", [False, True])
def test_sdk_primary_refusal_preserves_original_completion_and_publication(
    observer_failure,
):
    from aware_specification_sdk import SpecificationSdkClient
    from test_draft_evidence import Provider, Reader, evidence, request

    value = completion(True, "incomplete")
    value = replace(
        value,
        attempt_ref="attempt:one",
        input_custody=replace(
            value.input_custody,
            attempt_ref="attempt:one",
            client_intent_id="client-intent:one",
            execution_ref="execution:one",
            target_locator="plans/demo",
            scratch_locator="plans/.aware-spec-draft-" + "a" * 32,
        ),
    )

    class OriginalReader(Reader):
        def observe_draft_cleanup(self):
            if observer_failure:
                raise RuntimeError("original observer unavailable")
            return value

    reader = OriginalReader(evidence())
    primary = SpecificationOperationError(
        "original_primary", effect="unknown", cleanup_evidence=value
    )
    with pytest.raises(SpecificationOperationError, match="original_primary") as caught:
        SpecificationSdkClient(
            Provider(reader, failure=primary), draft_evidence_reader=reader
        ).create_draft(request())
    assert caught.value.cleanup_evidence == value
    assert caught.value.evidence.package_outcome == "published"
    assert caught.value.effect == "unknown"
