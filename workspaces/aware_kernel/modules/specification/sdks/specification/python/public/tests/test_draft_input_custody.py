"""Neutral custody carriage/history; no owner authorization or imports."""

from dataclasses import FrozenInstanceError, fields, replace

import pytest
from aware_specification_sdk import (
    SpecificationDraftCleanupEvidence as Evidence,
)
from aware_specification_sdk import (
    SpecificationDraftCleanupInvocation as Invocation,
)
from aware_specification_sdk import (
    SpecificationDraftCleanupLedger as Ledger,
)
from aware_specification_sdk import (
    SpecificationDraftInputCustodyObservation as Custody,
)
from aware_specification_sdk import (
    SpecificationDraftInputResourceObservation as Resource,
)
from aware_specification_sdk import (
    SpecificationOperationError,
)
from aware_specification_sdk.draft_cleanup import (
    require_cleanup_extension,
    snapshot_draft_cleanup,
)


def sample():
    physical = Resource(
        "acquired",
        "admission",
        "completed",
        "returned",
        True,
        "completed",
        ("original",),
    )
    protocol = Resource(
        "acquired", "admission", "completed", "returned", None, "unknown", ()
    )
    custody = Custody(
        "custody:attempt",
        "intent",
        "codex-execution",
        "released",
        "/repo",
        "aware.protocol.toml",
        "sha256:" + "1" * 64,
        "specs/widget",
        "specs/.scratch",
        physical,
        protocol,
        Ledger("published", (), (), (), False, True),
        (),
        "context:original",
    )
    return Evidence(
        "specification.draft.cleanup-evidence.v1",
        "custody:attempt",
        "closed",
        None,
        None,
        Invocation("context", "returned", ()),
        Invocation("context", "returned", ()),
        None,
        "unknown",
        (),
        custody,
    )


def test_detached_exact_shapes_and_error_reconstruction():
    value = sample()
    snapshot = snapshot_draft_cleanup(value)
    assert snapshot == value and snapshot.input_custody is not value.input_custody
    assert snapshot.input_custody.physical is not value.input_custody.physical
    assert [f.name for f in fields(snapshot.input_custody)] == [
        "attempt_ref",
        "client_intent_id",
        "execution_ref",
        "custody_state",
        "root_locator",
        "manifest_locator",
        "manifest_sha256",
        "target_locator",
        "scratch_locator",
        "physical",
        "protocol",
        "physical_evidence",
        "diagnostics",
        "context_ref",
    ]
    error = SpecificationOperationError(
        "original", effect="unknown", cleanup_evidence=value
    )
    assert error.cleanup_evidence == value
    with pytest.raises(FrozenInstanceError):
        snapshot.input_custody.context_ref = "replacement"


@pytest.mark.parametrize(
    "field,bad",
    [
        ("acquisition", "unknown"),
        ("responsibility", "caller"),
        ("transfer", "not_attempted"),
        ("release_invocation", "not_invoked"),
        ("owner_cleanup_attempted", False),
        ("owner_cleanup_outcome", "not_attempted"),
        ("diagnostics", ()),
    ],
)
def test_resource_history_cannot_regress(field, bad):
    previous = sample()
    current = replace(
        previous,
        input_custody=replace(
            previous.input_custody,
            physical=replace(previous.input_custody.physical, **{field: bad}),
        ),
    )
    with pytest.raises(ValueError):
        require_cleanup_extension(previous, current)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("attempt_ref", "other"),
        ("client_intent_id", "other"),
        ("context_ref", "other"),
        ("execution_ref", None),
        ("manifest_locator", None),
        ("physical_evidence", None),
        ("custody_state", "reserved"),
        ("custody_state", "unknown"),
    ],
)
def test_correlation_and_effect_history_cannot_disappear(field, bad):
    previous = sample()
    with pytest.raises(ValueError):
        current = replace(
            previous, input_custody=replace(previous.input_custody, **{field: bad})
        )
        require_cleanup_extension(previous, current)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("attempt_ref", None),
        ("client_intent_id", None),
        ("manifest_locator", "../escape"),
        ("root_locator", "relative"),
        ("root_locator", "/repo/../other"),
        ("context_ref", "e\u0301"),
        ("context_ref", "bad\u0085"),
        ("physical", object()),
        ("protocol", object()),
        ("physical_evidence", object()),
    ],
)
def test_malformed_or_noncanonical_nested_values_refuse(field, bad):
    with pytest.raises((AttributeError, TypeError, ValueError)):
        replace(sample().input_custody, **{field: bad})


def test_unknown_and_absent_extension_remain_non_authorizing():
    value = sample()
    legacy = replace(value, input_custody=None)
    assert snapshot_draft_cleanup(legacy).input_custody is None
    require_cleanup_extension(legacy, value)
    with pytest.raises(ValueError):
        require_cleanup_extension(value, legacy)
    current = replace(
        value,
        input_custody=replace(
            value.input_custody,
            physical_evidence=replace(
                value.input_custody.physical_evidence, residual_scratch_paths=()
            ),
        ),
    )
    require_cleanup_extension(value, current)


@pytest.mark.parametrize("observer_failure", [False, True])
def test_sdk_primary_refusal_preserves_correlated_detached_custody(observer_failure):
    from aware_specification_sdk import SpecificationSdkClient
    from test_draft_evidence import Provider, Reader, evidence, request

    cleanup = sample()
    cleanup = replace(
        cleanup,
        attempt_ref="attempt:one",
        input_custody=replace(
            cleanup.input_custody,
            attempt_ref="attempt:one",
            client_intent_id="client-intent:one",
            execution_ref="execution:one",
            manifest_sha256="sha256:" + "1" * 64,
            target_locator="plans/demo",
            scratch_locator="plans/.aware-spec-draft-" + "a" * 32,
        ),
    )

    class OriginalReader(Reader):
        def observe_draft_cleanup(self):
            if observer_failure:
                raise RuntimeError("original cleanup lookup unavailable")
            return cleanup

    reader = OriginalReader(evidence())
    primary = SpecificationOperationError(
        "original_primary", effect="unknown", cleanup_evidence=cleanup
    )
    with pytest.raises(SpecificationOperationError, match="original_primary") as caught:
        SpecificationSdkClient(
            Provider(reader, failure=primary), draft_evidence_reader=reader
        ).create_draft(request())
    assert caught.value.cleanup_evidence == cleanup
    assert caught.value.cleanup_evidence.input_custody is not cleanup.input_custody
    assert caught.value.evidence.package_outcome == "published"
    assert caught.value.effect == "unknown"


@pytest.mark.parametrize(
    "field,bad",
    [
        ("client_intent_id", "other"),
        ("execution_ref", "other"),
        ("manifest_sha256", "sha256:" + "2" * 64),
        ("target_locator", "plans/other"),
        ("scratch_locator", "plans/other-scratch"),
    ],
)
def test_sdk_custody_mismatch_cannot_replace_original_publication(field, bad):
    from aware_specification_sdk import SpecificationSdkClient
    from test_draft_evidence import Provider, Reader, evidence, request

    cleanup = sample()
    cleanup = replace(
        cleanup,
        attempt_ref="attempt:one",
        input_custody=replace(
            cleanup.input_custody,
            attempt_ref="attempt:one",
            client_intent_id="client-intent:one",
            execution_ref="execution:one",
            manifest_sha256="sha256:" + "1" * 64,
            target_locator="plans/demo",
            scratch_locator="plans/.aware-spec-draft-" + "a" * 32,
        ),
    )
    cleanup = replace(
        cleanup, input_custody=replace(cleanup.input_custody, **{field: bad})
    )

    class OriginalReader(Reader):
        def observe_draft_cleanup(self):
            return cleanup

    reader = OriginalReader(evidence())
    primary = SpecificationOperationError("original_primary", effect="unknown")
    with pytest.raises(SpecificationOperationError, match="original_primary") as caught:
        SpecificationSdkClient(
            Provider(reader, failure=primary), draft_evidence_reader=reader
        ).create_draft(request())
    assert caught.value.cleanup_evidence is None
    assert "draft_cleanup_evidence_invalid" in caught.value.evidence_diagnostics
    assert caught.value.evidence.package_outcome == "published"
