"""Optional saved-evidence provider over the original cleanup-qualified reader."""

from __future__ import annotations

from dataclasses import asdict, fields, replace
from importlib import import_module, metadata
from inspect import Parameter, signature
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from aware_specification_sdk.saved_receipt import (
    SPECIFICATION_SAVED_RECEIPT_SOURCE_LIMIT,
    SpecificationSavedReceiptCleanup,
    SpecificationSavedReceiptError,
    SpecificationSavedReceiptErrorEvidence,
    SpecificationSavedReceiptEvidenceGrade,
    SpecificationSavedReceiptReadCleanup,
    SpecificationSavedReceiptRequest,
    SpecificationSavedReceiptResult,
    SpecificationSavedReceiptSource,
    SpecificationSavedReceiptValueError,
    present_saved_draft_capture,
)


def _reader() -> ModuleType:
    owner = import_module("aware_file_system.confined_mutation")
    expected = {
        "ConfinedFileReadCleanup": {
            "outcome",
            "acquired_count",
            "release_attempted_count",
            "closed_count",
            "diagnostics",
        },
        "ConfinedFileObservation": {
            "path",
            "outcome",
            "exists",
            "content_digest",
            "size_bytes",
            "content",
            "error_code",
        },
        "ConfinedFileObservationWithCleanup": {
            "observation",
            "root_locator",
            "path",
            "cleanup",
            "observation_grade",
            "confinement_profile",
        },
    }
    for name, names in expected.items():
        if {item.name for item in fields(getattr(owner, name))} != names:
            raise ValueError("receipt_reader_value_incompatible")
    if not issubclass(owner.ConfinedFileObservationError, Exception):
        raise TypeError("receipt_reader_error_incompatible")
    if {item.value for item in owner.ConfinedObservationOutcome} != {
        "observed",
        "denied",
        "failed",
    }:
        raise ValueError("receipt_reader_outcome_incompatible")
    parameters = signature(owner.observe_confined_file_with_cleanup).parameters
    if set(parameters) != {"root", "path", "maximum_bytes"} or any(
        item.kind is not Parameter.KEYWORD_ONLY for item in parameters.values()
    ):
        raise ValueError("receipt_reader_port_incompatible")
    return owner


def _refusal(
    request: SpecificationSavedReceiptRequest,
    code: str,
    *,
    cleanup: SpecificationSavedReceiptReadCleanup | None = None,
    source: SpecificationSavedReceiptSource | None = None,
    diagnostics: tuple[str, ...] = (),
) -> SpecificationSavedReceiptError:
    outcome = (
        SpecificationSavedReceiptCleanup.NOT_ACQUIRED
        if cleanup is None
        else cleanup.outcome
    )
    return SpecificationSavedReceiptError(
        SpecificationSavedReceiptErrorEvidence(
            code,
            "Saved receipt presentation refused; no operation replay or retry is authorized.",
            request=request,
            provider_invoked=True,
            cleanup=outcome,
            effect="unknown" if outcome == "unknown" else "none",
            observed_source=source,
            diagnostics=diagnostics,
            evidence_grade=SpecificationSavedReceiptEvidenceGrade.PROVIDER_OBSERVATION,
        )
    )


def _unvalidated(
    request: SpecificationSavedReceiptRequest, value: object
) -> SpecificationSavedReceiptError:
    # Keep only bounded, transportable data from the rejected lower report.
    # A report is never reclassified as a verified source or confirmed cleanup.
    report = None
    faults = ()
    try:
        name = (
            (type(value).__module__ + "." + type(value).__name__)
            .encode("utf-8")[:1024]
            .decode("utf-8", errors="ignore")
        )
    except BaseException:  # noqa: BLE001 - reporting cannot erase the original lower failure
        name = "unavailable"
    try:
        if type(value) is dict:
            report = value
        else:
            report = asdict(cast(Any, value))
        evidence = SpecificationSavedReceiptErrorEvidence(
            "receipt_reader_report_invalid",
            "Original reader report is unvalidated; cleanup remains unknown.",
            request=request,
            provider_invoked=True,
            cleanup=SpecificationSavedReceiptCleanup.UNKNOWN,
            effect="unknown",
            reported_result=report,
            reported_result_type=name,
            evidence_grade=SpecificationSavedReceiptEvidenceGrade.UNVALIDATED_PROVIDER_REPORT,
        )
    except BaseException:  # noqa: BLE001 - raw bytes or invalid reports may not have bounded JSON transport
        faults = ("reader_report_not_transportable",)
        evidence = SpecificationSavedReceiptErrorEvidence(
            "receipt_reader_report_invalid",
            "Original reader report is unvalidated; cleanup remains unknown.",
            request=request,
            provider_invoked=True,
            cleanup=SpecificationSavedReceiptCleanup.UNKNOWN,
            effect="unknown",
            reported_result_type=name,
            report_diagnostics=faults,
            evidence_grade=SpecificationSavedReceiptEvidenceGrade.UNVALIDATED_PROVIDER_REPORT,
        )
    return SpecificationSavedReceiptError(evidence)


def _cleanup(owner: ModuleType, value: Any) -> SpecificationSavedReceiptReadCleanup:
    if type(value) is not owner.ConfinedFileReadCleanup:
        raise TypeError("original_read_cleanup_required")
    checked = replace(value)
    return SpecificationSavedReceiptReadCleanup(
        checked.outcome,
        checked.acquired_count,
        checked.release_attempted_count,
        checked.closed_count,
        checked.diagnostics,
    )


def _source(
    request: SpecificationSavedReceiptRequest,
    observation: Any,
    cleanup: SpecificationSavedReceiptReadCleanup,
) -> SpecificationSavedReceiptSource | None:
    # Reuse the original value's byte/digest validator before promoting source
    # metadata, including retained observations on the lower-error path.
    observation = replace(observation)
    if type(observation.exists) is not bool:
        raise ValueError("original_read_existence_invalid")
    if not observation.exists:
        if any(
            item is not None
            for item in (
                observation.content,
                observation.content_digest,
                observation.size_bytes,
            )
        ):
            raise ValueError("original_read_absence_invalid")
        return None
    if (
        type(observation.content) is not bytes
        or type(observation.size_bytes) is not int
        or (
            observation.size_bytes != len(observation.content)
            or observation.size_bytes > SPECIFICATION_SAVED_RECEIPT_SOURCE_LIMIT
        )
    ):
        raise ValueError("original_read_source_invalid")
    if observation.outcome.value != "observed" or observation.error_code is not None:
        raise ValueError("original_read_source_outcome_invalid")
    return SpecificationSavedReceiptSource(
        request.base_ref,
        request.source_ref,
        observation.content_digest,
        observation.size_bytes,
        cleanup,
    )


class SpecificationFsSavedReceiptProvider:
    """No retained writer, admission, cache or cleanup capability is acquired."""

    def present_draft_receipt(
        self, request: SpecificationSavedReceiptRequest
    ) -> SpecificationSavedReceiptResult:
        try:
            if type(request) is not SpecificationSavedReceiptRequest:
                raise TypeError("original_saved_receipt_request_required")
            original = replace(request)
        except BaseException as error:
            raise SpecificationSavedReceiptError(
                SpecificationSavedReceiptErrorEvidence(
                    "receipt_request_invalid",
                    "Request validation failed before the original reader was invoked.",
                )
            ) from error
        try:
            owner = _reader()
            root = Path(original.base_ref)
        except BaseException as error:
            raise _refusal(
                original,
                "receipt_reader_integration_unavailable",
                diagnostics=("reader_not_invoked",),
            ) from error
        try:
            returned = owner.observe_confined_file_with_cleanup(
                root=root,
                path=original.source_ref,
                maximum_bytes=SPECIFICATION_SAVED_RECEIPT_SOURCE_LIMIT,
            )
        except BaseException as error:
            if type(error) is not owner.ConfinedFileObservationError:
                raise _unvalidated(original, error) from error
            try:
                failure = cast(Any, error)
                cleanup = _cleanup(owner, failure.cleanup)
                if (
                    failure.root_locator is not None
                    and failure.root_locator != original.base_ref
                ) or (failure.path is not None and failure.path != original.source_ref):
                    raise ValueError("receipt_reader_error_uncorrelated")
                observation = failure.observation
                if observation is not None and (
                    type(observation) is not owner.ConfinedFileObservation
                    or observation.path != original.source_ref
                ):
                    raise ValueError("receipt_reader_error_observation_invalid")
                if (
                    observation is not None
                    and observation.exists
                    and (
                        failure.root_locator != original.base_ref
                        or failure.path != original.source_ref
                    )
                ):
                    raise ValueError("receipt_reader_error_source_uncorrelated")
                # Retained bytes must still match their reported digest. If
                # validation fails, the protected boundary below preserves the
                # original lower cause and labels its report unvalidated.
                source = (
                    None
                    if observation is None
                    else _source(original, observation, cleanup)
                )
                refusal = _refusal(
                    original,
                    failure.code,
                    cleanup=cleanup,
                    source=source,
                    diagnostics=cleanup.diagnostics
                    or (
                        "reader_stage:" + failure.stage,
                        "reader_cause:" + failure.cause_kind,
                    ),
                )
            except BaseException:  # noqa: BLE001 - malformed lower errors retain their original cause
                raise _unvalidated(original, error) from error
            raise refusal from error
        try:
            if type(returned) is not owner.ConfinedFileObservationWithCleanup:
                raise TypeError("original_read_result_required")
            checked = replace(
                returned,
                observation=replace(returned.observation),
                cleanup=replace(returned.cleanup),
            )
            if (
                checked.root_locator != original.base_ref
                or checked.path != original.source_ref
            ):
                raise ValueError("receipt_reader_result_uncorrelated")
            cleanup = _cleanup(owner, checked.cleanup)
        except BaseException as error:
            raise _unvalidated(original, returned) from error
        source = None
        try:
            observation = checked.observation
            if observation.outcome is not owner.ConfinedObservationOutcome.OBSERVED:
                raise _refusal(original, observation.error_code, cleanup=cleanup)
            if not observation.exists:
                raise _refusal(original, "receipt_source_absent", cleanup=cleanup)
            source = _source(original, observation, cleanup)
            try:
                version = metadata.version("aware-specification-fs-sdk-adapter")
            except metadata.PackageNotFoundError:
                version = "source"
            return present_saved_draft_capture(
                original,
                observation.content,
                provider_ref="aware_specification_fs_sdk_adapter.saved-receipt.v1",
                provider_distribution="aware-specification-fs-sdk-adapter",
                provider_version=version,
                cleanup=cleanup,
            )
        except SpecificationSavedReceiptError:
            raise
        except BaseException as error:
            raise _refusal(
                original,
                str(error)
                if type(error) is SpecificationSavedReceiptValueError
                else "receipt_presentation_failed",
                cleanup=cleanup,
                source=source,
                diagnostics=("presentation_failed",),
            ) from error
