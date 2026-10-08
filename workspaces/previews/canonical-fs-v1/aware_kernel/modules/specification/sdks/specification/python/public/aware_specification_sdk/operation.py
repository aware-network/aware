"""Canonical neutral operations; provider selection is explicit, never inferred."""

from dataclasses import dataclass, replace
from typing import Protocol

from aware_specification_runtime import (
    SpecificationDefinition,
    SpecificationIterationIdentity,
    SpecificationSnapshot,
)
from aware_specification_runtime.values import sha256_ref, token

from .draft_cleanup import (
    SpecificationDraftCleanupEvidence,
    require_cleanup_extension,
    snapshot_draft_cleanup,
)
from .draft_evidence import (
    SpecificationDraftEvidence,
    SpecificationDraftEvidenceReader,
    snapshot_draft_evidence,
)

SPECIFICATION_OBSERVE_OPERATION_REF = "specification_sdk.observe"
SPECIFICATION_OBSERVE_PROVIDER_OPERATION_REF = "specification.source.observe"
SPECIFICATION_DRAFT_CREATE_OPERATION_REF = "specification_sdk.create_draft"
SPECIFICATION_DRAFT_CREATE_PROVIDER_OPERATION_REF = "specification.draft.create"


class SpecificationOperationError(ValueError):
    def __init__(
        self,
        code: str,
        *,
        effect: str = "none",
        evidence: SpecificationDraftEvidence | None = None,
        evidence_diagnostics: tuple[str, ...] = (),
        cleanup_evidence: SpecificationDraftCleanupEvidence | None = None,
    ) -> None:
        token(code, "operation_error_code")
        if type(effect) is not str or effect not in {"none", "published", "unknown"}:
            raise ValueError("invalid_operation_effect")
        if type(evidence_diagnostics) is not tuple:
            raise ValueError("invalid_evidence_diagnostics")
        for diagnostic in evidence_diagnostics:
            token(diagnostic, "evidence_diagnostic")
        self.code = code
        self.effect = effect
        self.evidence = None if evidence is None else snapshot_draft_evidence(evidence)
        self.evidence_diagnostics = evidence_diagnostics
        self.cleanup_evidence = (
            None
            if cleanup_evidence is None
            else snapshot_draft_cleanup(cleanup_evidence)
        )
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class SpecificationObserveRequest:
    expected_source_digest: str | None = None

    def __post_init__(self) -> None:
        if type(self) is not SpecificationObserveRequest:
            raise SpecificationOperationError("invalid_observe_request")
        if self.expected_source_digest is not None:
            sha256_ref(self.expected_source_digest, "expected_source_digest")


@dataclass(frozen=True, slots=True)
class SpecificationObservation:
    snapshot: SpecificationSnapshot
    source_digest: str
    provider_ref: str
    authority_mode: str
    observation_grade: str
    source_context_digest: str
    iterations: tuple[SpecificationIterationIdentity, ...]

    def __post_init__(self) -> None:
        if type(self) is not SpecificationObservation:
            raise SpecificationOperationError("invalid_observation")
        if type(self.snapshot) is not SpecificationSnapshot:
            raise SpecificationOperationError("invalid_observation")
        self.snapshot.__post_init__()
        for name in ("source_digest", "source_context_digest"):
            sha256_ref(getattr(self, name), name)
        token(self.provider_ref, "provider_ref")
        if (
            type(self.authority_mode) is not str
            or type(self.observation_grade) is not str
        ):
            raise SpecificationOperationError("invalid_observation")
        if (
            self.authority_mode != "filesystem"
            or self.observation_grade != "local_structural_observation"
        ):
            raise SpecificationOperationError("unsupported_observation_profile")
        if type(self.iterations) is not tuple or any(
            type(v) is not SpecificationIterationIdentity for v in self.iterations
        ):
            raise SpecificationOperationError("invalid_observation")
        expected = tuple(
            SpecificationIterationIdentity(
                f"specification:{d.key}/phase:{p.phase_key}", i
            )
            for d in self.snapshot.definitions
            for p in d.phases
            for i in p.iterations
        )
        for value in self.iterations:
            value.__post_init__()
        if self.iterations != expected:
            raise SpecificationOperationError("iteration_closure_mismatch")


@dataclass(frozen=True, slots=True)
class SpecificationDraftRequest:
    definition: SpecificationDefinition
    author_ref: str
    authoring_intent_ref: str

    def __post_init__(self) -> None:
        if (
            type(self) is not SpecificationDraftRequest
            or type(self.definition) is not SpecificationDefinition
        ):
            raise SpecificationOperationError("invalid_draft_request")
        self.definition.__post_init__()
        token(self.author_ref, "author_ref")
        token(self.authoring_intent_ref, "authoring_intent_ref")
        if any(p.iterations for p in self.definition.phases):
            raise SpecificationOperationError("iteration_approval_writer_unavailable")
        if (
            not self.definition.invariants
            or not self.definition.phases
            or not self.definition.description
        ):
            raise SpecificationOperationError("incomplete_draft_meaning")
        if any(not p.description for p in self.definition.phases):
            raise SpecificationOperationError("incomplete_draft_meaning")
        SpecificationSnapshot((self.definition,))


@dataclass(frozen=True, slots=True)
class SpecificationDraftResult:
    observation: SpecificationObservation
    created_paths: tuple[str, ...]
    authoring_intent_ref: str
    evidence: SpecificationDraftEvidence | None = None

    def __post_init__(self) -> None:
        if (
            type(self) is not SpecificationDraftResult
            or type(self.observation) is not SpecificationObservation
        ):
            raise SpecificationOperationError("invalid_draft_result")
        self.observation.__post_init__()
        token(self.authoring_intent_ref, "authoring_intent_ref")
        if self.evidence is not None:
            object.__setattr__(self, "evidence", snapshot_draft_evidence(self.evidence))
        if (
            type(self.created_paths) is not tuple
            or not self.created_paths
            or any(type(v) is not str for v in self.created_paths)
        ):
            raise SpecificationOperationError("invalid_draft_result")
        if self.created_paths != tuple(sorted(set(self.created_paths))):
            raise SpecificationOperationError("invalid_draft_result")
        for path in self.created_paths:
            token(path, "created_path")
            if (
                path.startswith("/")
                or "\\" in path
                or any(part in {"", ".", ".."} for part in path.split("/"))
            ):
                raise SpecificationOperationError("invalid_draft_result")


class SpecificationOperationProvider(Protocol):
    def observe(
        self, request: SpecificationObserveRequest
    ) -> SpecificationObservation: ...
    def create_draft(
        self, request: SpecificationDraftRequest
    ) -> SpecificationDraftResult: ...


class SpecificationSdkClient:
    def __init__(
        self,
        provider: SpecificationOperationProvider,
        *,
        draft_evidence_reader: SpecificationDraftEvidenceReader | None = None,
    ) -> None:
        self._provider = provider
        self._draft_evidence_reader = draft_evidence_reader

    def observe(self, request: SpecificationObserveRequest) -> SpecificationObservation:
        if type(request) is not SpecificationObserveRequest:
            raise SpecificationOperationError("invalid_observe_request")
        request.__post_init__()
        result = self._provider.observe(request)
        if type(result) is not SpecificationObservation:
            raise SpecificationOperationError("invalid_observation")
        try:
            result.__post_init__()
        except SpecificationOperationError:
            raise
        except (AttributeError, TypeError, ValueError) as error:
            raise SpecificationOperationError("invalid_observation") from error
        if (
            request.expected_source_digest is not None
            and result.source_digest != request.expected_source_digest
        ):
            raise SpecificationOperationError("source_changed")
        return result

    def create_draft(
        self, request: SpecificationDraftRequest
    ) -> SpecificationDraftResult:
        if type(request) is not SpecificationDraftRequest:
            raise SpecificationOperationError("invalid_draft_request")
        try:
            request.__post_init__()
        except (AttributeError, TypeError, ValueError) as error:
            raise SpecificationOperationError("invalid_draft_request") from error
        requested_meaning = SpecificationSnapshot((request.definition,)).snapshot_digest
        requested_author = request.author_ref
        requested_intent = request.authoring_intent_ref
        reader = self._draft_evidence_reader
        original = None if reader is None else _read_evidence(reader, None)
        observed: SpecificationDraftEvidence | None
        if (
            original is not None
            and original.authoring_intent_ref != request.authoring_intent_ref
        ):
            raise SpecificationOperationError(
                "draft_evidence_mismatch", evidence=original
            )
        try:
            result = self._provider.create_draft(request)
        except BaseException as error:
            if reader is None:
                raise
            cleanup, cleanup_faults = _carry_cleanup(error, reader, original)
            # Read the original ledger before inspecting any returned error fields.
            try:
                observed = _read_evidence(reader, original)
            except SpecificationOperationError as lookup_error:
                if isinstance(error, SpecificationOperationError):
                    try:
                        token(error.code, "operation_error_code")
                    except (AttributeError, TypeError, ValueError):
                        raise SpecificationOperationError(
                            "draft_provider_error_invalid",
                            effect="unknown",
                            evidence=lookup_error.evidence,
                            evidence_diagnostics=(
                                *lookup_error.evidence_diagnostics,
                                *cleanup_faults,
                            ),
                            cleanup_evidence=cleanup,
                        ) from error
                    raise SpecificationOperationError(
                        error.code,
                        effect="unknown",
                        evidence=lookup_error.evidence,
                        evidence_diagnostics=(
                            *lookup_error.evidence_diagnostics,
                            *cleanup_faults,
                        ),
                        cleanup_evidence=cleanup,
                    ) from error
                raise SpecificationOperationError(
                    lookup_error.code,
                    effect="unknown",
                    evidence=lookup_error.evidence,
                    evidence_diagnostics=(
                        *lookup_error.evidence_diagnostics,
                        *cleanup_faults,
                    ),
                    cleanup_evidence=cleanup,
                ) from error
            if isinstance(error, SpecificationOperationError):
                try:
                    token(error.code, "operation_error_code")
                    if type(error.effect) is not str or error.effect not in {
                        "none",
                        "published",
                        "unknown",
                    }:
                        raise ValueError("invalid_operation_effect")
                    if error.evidence is not None and _correlation(
                        snapshot_draft_evidence(error.evidence)
                    ) != _correlation(observed):
                        raise ValueError("returned_evidence_mismatch")
                    effect = error.effect
                    if cleanup_faults:
                        effect = "unknown"
                    if effect == "none" and observed.package_outcome == "published":
                        effect = "published"
                    elif (
                        effect == "none" and observed.package_outcome == "unknown"
                    ) or (
                        effect == "published"
                        and observed.package_outcome != "published"
                    ):
                        effect = "unknown"
                    refusal = SpecificationOperationError(
                        error.code,
                        effect=effect,
                        evidence=observed,
                        evidence_diagnostics=(
                            *error.evidence_diagnostics,
                            *cleanup_faults,
                        ),
                        cleanup_evidence=cleanup,
                    )
                except (AttributeError, TypeError, ValueError):
                    refusal = SpecificationOperationError(
                        "draft_provider_error_invalid",
                        effect="unknown",
                        evidence=observed,
                        evidence_diagnostics=cleanup_faults,
                        cleanup_evidence=cleanup,
                    )
                raise refusal from error
            raise SpecificationOperationError(
                "draft_provider_failed",
                effect="unknown",
                evidence=observed,
                evidence_diagnostics=cleanup_faults,
                cleanup_evidence=cleanup,
            ) from error
        # Required original retrieval precedes all result/nested-value access.
        try:
            observed = None if reader is None else _read_evidence(reader, original)
        except SpecificationOperationError as error:
            cleanup, faults = _carry_cleanup(error, reader, original)
            raise SpecificationOperationError(
                error.code,
                effect="unknown",
                evidence=error.evidence,
                evidence_diagnostics=(*error.evidence_diagnostics, *faults),
                cleanup_evidence=cleanup,
            ) from error
        if type(result) is not SpecificationDraftResult:
            cleanup, faults = _carry_cleanup(
                ValueError("invalid_draft_result"), reader, original
            )
            raise SpecificationOperationError(
                "invalid_draft_result",
                effect="unknown",
                evidence=observed,
                evidence_diagnostics=faults,
                cleanup_evidence=cleanup,
            )
        try:
            result.__post_init__()
            request.__post_init__()
            if (
                result.observation.snapshot.snapshot_digest != requested_meaning
                or SpecificationSnapshot((request.definition,)).snapshot_digest
                != requested_meaning
                or request.author_ref != requested_author
                or request.authoring_intent_ref != requested_intent
                or result.authoring_intent_ref != requested_intent
            ):
                raise SpecificationOperationError(
                    "draft_result_mismatch", effect="unknown"
                )
            if observed is not None:
                if result.evidence is not None and result.evidence != observed:
                    raise ValueError("returned_evidence_mismatch")
                if (
                    not observed.ledger_complete
                    or not observed.completion_verified
                    or observed.package_outcome != "published"
                    or observed.residual_scratch_paths
                    or observed.cleanup_diagnostics
                    or result.created_paths
                    != tuple(
                        observed.target_locator + "/" + member.relative_path
                        for member in observed.members
                    )
                ):
                    raise ValueError("draft_completion_unverified")
                result = replace(result, evidence=observed)
        except (
            AttributeError,
            TypeError,
            ValueError,
            SpecificationOperationError,
        ) as error:
            cleanup, faults = _carry_cleanup(error, reader, original)
            raise SpecificationOperationError(
                error.code
                if isinstance(error, SpecificationOperationError)
                else "draft_result_invalid",
                effect="unknown",
                evidence=observed,
                evidence_diagnostics=faults,
                cleanup_evidence=cleanup,
            ) from error
        return result


def _correlation(value: SpecificationDraftEvidence) -> tuple[object, ...]:
    return (
        value.profile,
        value.attempt_ref,
        value.issue_ref,
        value.execution_ref,
        value.client_intent_id,
        value.authoring_intent_ref,
        value.protocol_manifest_sha256,
        value.target_locator,
        value.scratch_locator,
        value.members,
    )


def _cleanup_correlates(
    current: SpecificationDraftCleanupEvidence,
    original: SpecificationDraftEvidence,
) -> bool:
    if current.attempt_ref != original.attempt_ref:
        return False
    if current.issue_disposition is not None:
        request = current.issue_disposition.request
        if (
            request.issue_ref,
            request.client_intent_id,
            request.authoring_intent_ref,
            request.expected_manifest_sha256,
            request.target_locator,
            request.scratch_locator,
        ) != (
            original.issue_ref,
            original.client_intent_id,
            original.authoring_intent_ref,
            original.protocol_manifest_sha256,
            original.target_locator,
            original.scratch_locator,
        ):
            return False
    custody = current.input_custody
    if custody is not None:
        for supplied, expected in (
            (custody.client_intent_id, original.client_intent_id),
            (custody.execution_ref, original.execution_ref),
            (custody.manifest_sha256, original.protocol_manifest_sha256),
            (custody.target_locator, original.target_locator),
            (custody.scratch_locator, original.scratch_locator),
        ):
            if supplied is not None and supplied != expected:
                return False
    return True


def _carry_cleanup(
    error: BaseException,
    reader: SpecificationDraftEvidenceReader | None,
    original: SpecificationDraftEvidence | None,
) -> tuple[SpecificationDraftCleanupEvidence | None, tuple[str, ...]]:
    """Preserve neutral knowledge, not authorize a reader or cleanup call."""
    current = None
    faults: list[str] = []
    try:
        # Attribute lookup itself can execute provider code. Isolate lookup,
        # invocation and validation so no secondary failure masks the primary.
        observer = getattr(reader, "observe_draft_cleanup", None)
        if observer is not None:
            if not callable(observer):
                raise TypeError("invalid_draft_cleanup_observer")
            current = snapshot_draft_cleanup(observer())
    except BaseException as secondary:  # noqa: BLE001 - preserve the primary refusal even if cleanup observation is interrupted
        faults.extend(
            (
                "draft_cleanup_observation_unavailable",
                f"draft_cleanup_observation_detail:{type(secondary).__name__}",
            )
        )
    retained = current
    try:
        supplied = getattr(error, "cleanup_evidence", None)
        if supplied is not None:
            supplied = snapshot_draft_cleanup(supplied)
            if current is not None:
                require_cleanup_extension(supplied, current)
            else:
                current = supplied
        if (
            current is not None
            and original is not None
            and not _cleanup_correlates(current, original)
        ):
            raise ValueError("draft_cleanup_source_mismatch")
    except BaseException:  # noqa: BLE001 - optional returned-carrier faults cannot replace the primary refusal
        faults.append("draft_cleanup_evidence_invalid")
        # Returned data cannot replace the original observer's known history.
        current = retained
        if (
            current is not None
            and original is not None
            and not _cleanup_correlates(current, original)
        ):
            current = None
    return current, tuple(faults)


def _read_evidence(
    reader: SpecificationDraftEvidenceReader,
    previous: SpecificationDraftEvidence | None,
) -> SpecificationDraftEvidence:
    try:
        observed = snapshot_draft_evidence(reader.observe_draft_evidence())
        if previous is not None:
            if _correlation(observed) != _correlation(previous):
                raise ValueError("draft_evidence_mismatch")
            # Same-attempt identity cannot authorize erasing observed history.
            if observed.effects[: len(previous.effects)] != previous.effects:
                raise ValueError("draft_evidence_history_mismatch")
            if (
                previous.package_outcome == "published"
                and observed.package_outcome != "published"
            ):
                raise ValueError("draft_evidence_publication_regressed")
        return observed
    except BaseException as error:
        degraded = (
            None
            if previous is None
            else replace(
                previous,
                package_outcome="published"
                if previous.package_outcome == "published"
                else "unknown",
                ledger_complete=False,
                completion_verified=False,
            )
        )
        raise SpecificationOperationError(
            "draft_evidence_unavailable",
            effect="unknown",
            evidence=degraded,
            evidence_diagnostics=("draft_evidence_unavailable",),
        ) from error
