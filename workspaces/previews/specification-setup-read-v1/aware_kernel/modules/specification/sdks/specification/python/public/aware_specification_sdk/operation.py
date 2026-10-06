"""Canonical neutral operations; provider selection is explicit, never inferred."""

from dataclasses import dataclass
from typing import Protocol

from aware_specification_runtime import (
    SpecificationDefinition,
    SpecificationIterationIdentity,
    SpecificationSnapshot,
)
from aware_specification_runtime.values import sha256_ref, token

SPECIFICATION_OBSERVE_OPERATION_REF = "specification_sdk.observe"
SPECIFICATION_OBSERVE_PROVIDER_OPERATION_REF = "specification.source.observe"
SPECIFICATION_DRAFT_CREATE_OPERATION_REF = "specification_sdk.create_draft"
SPECIFICATION_DRAFT_CREATE_PROVIDER_OPERATION_REF = "specification.draft.create"


class SpecificationOperationError(ValueError):
    def __init__(self, code: str, *, effect: str = "none") -> None:
        self.code = code
        self.effect = effect
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

    def __post_init__(self) -> None:
        if (
            type(self) is not SpecificationDraftResult
            or type(self.observation) is not SpecificationObservation
        ):
            raise SpecificationOperationError("invalid_draft_result")
        self.observation.__post_init__()
        token(self.authoring_intent_ref, "authoring_intent_ref")
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
    def __init__(self, provider: SpecificationOperationProvider) -> None:
        self._provider = provider

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
        request.__post_init__()
        result = self._provider.create_draft(request)
        if type(result) is not SpecificationDraftResult:
            raise SpecificationOperationError("invalid_draft_result", effect="unknown")
        try:
            result.__post_init__()
            if (
                result.observation.snapshot.definitions != (request.definition,)
                or result.authoring_intent_ref != request.authoring_intent_ref
            ):
                raise SpecificationOperationError(
                    "draft_result_mismatch", effect="unknown"
                )
        except (AttributeError, TypeError, ValueError) as error:
            raise SpecificationOperationError(
                "draft_result_invalid", effect="unknown"
            ) from error
        return result
