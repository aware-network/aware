"""Issue-owned publication values, codecs and original-owner SDK ports.

No Workspace import: the supplying runtime maps the scalar owner coordinates.
Successful decoding does not authenticate a binding or grant work authority.
The original runtime supplies the process-local admission/consumption handles.
"""

from __future__ import annotations

import json
import types
import unicodedata
from dataclasses import dataclass, fields
from typing import Literal, get_args, get_origin, get_type_hints
from weakref import WeakKeyDictionary

IssueRepositoryPublicationEnrollmentRequestPurpose = Literal[
    "repository_publication", "issue_closeout_publication", "index_reconciliation"
]


def evaluate_repository_source_scope(**request):
    """Descriptive Issue policy through its owner, never an admission handle."""
    from aware_issue_operational_runtime.source_scope_policy import (
        evaluate_issue_source_scope,
    )

    decision = evaluate_issue_source_scope(**request)
    return (
        decision.refusal.value if decision.refusal is not None else None,
        decision.offending_path,
    )


def repository_source_scope_covers_path(*, path, scope_paths):
    from aware_issue_operational_runtime.source_scope_policy import (
        issue_scope_covers_path,
    )

    return issue_scope_covers_path(path=path, scope_paths=scope_paths)


@dataclass(frozen=True, slots=True)
class IssueRepositoryPublicationBinding:
    workspace_binding_ref: str
    attempt_ref: str
    repository_ref: str
    publication_reference: str
    expected_head: str | None
    target_paths: tuple[str, ...]
    postimages_digest: str
    message_digest: str
    workspace_provider_generation: str
    workspace_provider_ref: str
    execution_id: str


@dataclass(frozen=True, slots=True)
class IssueRepositoryPublicationRequest:
    issue_ref: str
    expected_issue_source_sha256: str
    binding: IssueRepositoryPublicationBinding


@dataclass(frozen=True, slots=True)
class IssueRepositoryPublicationEnrollmentRequest:
    binding: IssueRepositoryPublicationBinding
    consumer_ref: str
    purpose: IssueRepositoryPublicationEnrollmentRequestPurpose


@dataclass(frozen=True, slots=True)
class IssueRepositoryPublicationConsumeRequest:
    workspace_binding_ref: str
    attempt_ref: str
    workspace_provider_ref: str
    workspace_provider_generation: str
    execution_id: str
    consumer_ref: str
    purpose: Literal[
        "repository_publication", "issue_closeout_publication", "index_reconciliation"
    ]


@dataclass(frozen=True, slots=True)
class IssueRepositoryFileIdentity:
    device: int
    inode: int


@dataclass(frozen=True, slots=True)
class IssueRepositoryPublicationPhysicalEffect:
    effect_ref: str
    subject_ref: str
    kind: Literal[
        "repository_reference_update",
        "shared_index_projection",
        "transaction_index_write",
        "transaction_index_cleanup",
        "recovery_record_write",
        "recovery_record_cleanup",
        "descriptor_release",
        "source_compensation",
    ]
    state: Literal["not_attempted", "applied", "failed", "unknown"]
    before_ref: str | None
    after_ref: str | None
    before_digest: str | None
    after_digest: str | None
    before_identity: IssueRepositoryFileIdentity | None
    after_identity: IssueRepositoryFileIdentity | None
    mode: int | None
    durability_confirmed: bool | None
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IssueRepositoryPublicationLockReleaseObservation:
    binding_ref: str
    attempt_ref: str
    provider_ref: str
    provider_generation: str
    transaction_ref: str
    release_observation_ref: str
    repository_lock_release: Literal[
        "not_acquired", "confirmed_released", "not_released", "unknown"
    ]
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IssueRepositoryPublicationEffectObservation:
    binding: IssueRepositoryPublicationBinding
    workspace_observation_ref: str
    work_admission_receipt_ref: str
    publication_receipt_ref: str | None
    publication_state: Literal["not_published", "published", "unknown"]
    expected_head: str | None
    candidate_commit: str | None
    commit_hash: str | None
    updated_reference: str | None
    reference_update: Literal["not_run", "cas_applied", "cas_failed", "unknown"]
    index_projection: Literal["not_run", "applied", "pending", "failed", "unknown"]
    cleanup_state: Literal["not_attempted", "completed", "incomplete", "unknown"]
    lock_release: IssueRepositoryPublicationLockReleaseObservation | None
    admission_completion: Literal["not_attempted", "completed", "pending", "unknown"]
    transaction_mode: str
    shared_index_unchanged: bool | None
    index_reconciliation_pending: bool | None
    effects: tuple[IssueRepositoryPublicationPhysicalEffect, ...]
    ledger_complete: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IssueRepositoryPublicationAdmissionObservation:
    issue_ref: str
    expected_issue_source_sha256: str
    provider_ref: str
    provider_generation: str
    execution_id: str
    observation_ref: str
    attempt_ref: str
    binding: IssueRepositoryPublicationBinding
    admission_receipt_ref: str
    enrollment_receipt_ref: str | None
    work_admission_receipt_ref: str | None
    consumer_ref: str | None
    purpose: Literal[
        "repository_publication", "issue_closeout_publication", "index_reconciliation"
    ]
    phase: str
    consumption_state: Literal["not_consumed", "consumed", "unknown"]
    completion_state: Literal["not_attempted", "completed", "pending", "unknown"]
    publication: IssueRepositoryPublicationEffectObservation | None
    ledger_complete: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IssuePublicationCleanupObservation:
    issue_ref: str | None
    provider_ref: str
    provider_generation: str
    execution_id: str
    observation_ref: str
    attempt_ref: str
    admission_receipt_ref: str | None
    resource_ownership: Literal["not_acquired", "owned", "released", "unknown"]
    cleanup_state: Literal["not_attempted", "completed", "incomplete", "unknown"]
    publication: IssueRepositoryPublicationEffectObservation | None
    source_observation: IssueCloseoutSourceObservation | None
    ledger_complete: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IssueCloseoutSourceObservation:
    issue_ref: str
    provider_ref: str
    provider_generation: str
    execution_id: str
    observation_ref: str
    attempt_ref: str
    close_admission_receipt_ref: str
    source_path: str
    source_change_state: Literal["not_attempted", "applied", "failed", "unknown"]
    source_sha256_before: str | None
    source_sha256_after: str | None
    source_identity_before: IssueRepositoryFileIdentity | None
    source_identity_after: IssueRepositoryFileIdentity | None
    source_mode_before: int | None
    source_mode_after: int | None
    durability_confirmed: bool | None
    cleanup_state: Literal["not_attempted", "completed", "incomplete", "unknown"]
    ledger_complete: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IssueCloseoutObservation:
    issue_ref: str
    provider_ref: str
    provider_generation: str
    execution_id: str
    observation_ref: str
    attempt_ref: str
    close_admission_receipt_ref: str
    implementation_publication_receipt_ref: str
    closeout_publication_receipt_ref: str | None
    source_observation: IssueCloseoutSourceObservation | None
    publication_admission: IssueRepositoryPublicationAdmissionObservation | None
    completion_state: Literal["not_attempted", "completed", "pending", "unknown"]
    ledger_complete: bool
    diagnostics: tuple[str, ...]


class IssuePublicationValueError(ValueError):
    """Malformed value; no provider was selected or invoked."""


_VALUE_TYPES = (
    IssueRepositoryPublicationBinding,
    IssueRepositoryPublicationRequest,
    IssueRepositoryPublicationEnrollmentRequest,
    IssueRepositoryPublicationConsumeRequest,
    IssueRepositoryFileIdentity,
    IssueRepositoryPublicationPhysicalEffect,
    IssueRepositoryPublicationLockReleaseObservation,
    IssueRepositoryPublicationEffectObservation,
    IssueRepositoryPublicationAdmissionObservation,
    IssuePublicationCleanupObservation,
    IssueCloseoutSourceObservation,
    IssueCloseoutObservation,
)


def _refuse(path: str, reason: str):
    raise IssuePublicationValueError(f"{path}: {reason}")


def _paths(value: tuple[str, ...], path: str) -> None:
    if value != tuple(sorted(set(value))):
        _refuse(path, "paths must be unique and sorted")
    for item in value:
        if (
            not item
            or item.startswith("/")
            or "\\" in item
            or any(part in ("", ".", "..") for part in item.split("/"))
            or unicodedata.normalize("NFC", item) != item
            or any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in item)
        ):
            _refuse(path, "noncanonical repository path")


def _record(annotation: type, value: object, path: str, *, decode: bool):
    definitions = fields(annotation)
    if decode:
        if type(value) is not dict or set(value) != {
            field.name for field in definitions
        }:
            _refuse(path, "expected exactly the authored fields")
        source = value
    else:
        if type(value) is not annotation:
            _refuse(path, "expected the original SDK value type")
        source = {field.name: getattr(value, field.name) for field in definitions}
    hints = get_type_hints(annotation)
    result = {
        field.name: _convert(
            hints[field.name], source[field.name], f"{path}.{field.name}", decode=decode
        )
        for field in definitions
    }
    if "target_paths" in result:
        _paths(tuple(result["target_paths"]), path + ".target_paths")
    if "source_path" in result:
        _paths((result["source_path"],), path + ".source_path")
    return annotation(**result) if decode else result


def _convert(annotation: object, value: object, path: str, *, decode: bool):
    origin, arguments = get_origin(annotation), get_args(annotation)
    if origin is types.UnionType:
        if value is None and type(None) in arguments:
            return None
        return _convert(
            next(item for item in arguments if item is not type(None)),
            value,
            path,
            decode=decode,
        )
    if annotation in (str, int, bool):
        if type(value) is not annotation:
            _refuse(path, "incorrect primitive type")
        if annotation is str:
            try:
                value.encode("utf-8")
            except UnicodeError:
                _refuse(path, "string is not UTF-8 encodable")
        return value
    if origin is Literal:
        if type(value) is not str or value not in arguments:
            _refuse(path, "unrecognized authored enum value")
        return value
    if origin is tuple:
        if type(value) is not (list if decode else tuple):
            _refuse(path, "incorrect ordered collection type")
        items = [
            _convert(arguments[0], item, f"{path}[{index}]", decode=decode)
            for index, item in enumerate(value)
        ]
        return tuple(items) if decode else items
    if any(annotation is item for item in _VALUE_TYPES):
        return _record(annotation, value, path, decode=decode)
    _refuse(path, "unsupported value type")


def repository_publication_value_to_payload(value: object) -> dict[str, object]:
    if not any(type(value) is item for item in _VALUE_TYPES):
        _refuse("value", "not an Issue publication value; handles cannot be encoded")
    return _record(type(value), value, "value", decode=False)


def repository_publication_value_from_payload[T](
    value_type: type[T], payload: object
) -> T:
    if not any(value_type is item for item in _VALUE_TYPES):
        _refuse(
            "value_type", "not an Issue publication value; handles cannot be decoded"
        )
    return _record(value_type, payload, "value", decode=True)


def _json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            _refuse("json", "duplicate field")
        result[key] = value
    return result


def _json_number(value: str):
    _refuse("json", "floating-point or nonfinite numbers are not authored values")


def repository_publication_value_to_json(value: object) -> str:
    return json.dumps(
        repository_publication_value_to_payload(value),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    )


def repository_publication_value_from_json[T](value_type: type[T], source: str) -> T:
    if type(source) is not str:
        _refuse("json", "expected text")
    try:
        payload = json.loads(
            source,
            object_pairs_hook=_json_object,
            parse_constant=_json_number,
            parse_float=_json_number,
        )
    except (ValueError, RecursionError) as error:
        if isinstance(error, IssuePublicationValueError):
            raise
        raise IssuePublicationValueError("json: malformed input") from error
    return repository_publication_value_from_payload(value_type, payload)


__all__ = (
    "IssueCloseoutObservation",
    "IssueCloseoutSourceObservation",
    "IssuePublicationCleanupObservation",
    "IssuePublicationValueError",
    "IssueRepositoryFileIdentity",
    "IssueRepositoryPublicationAdmissionObservation",
    "IssueRepositoryPublicationBinding",
    "IssueRepositoryPublicationConsumeRequest",
    "IssueRepositoryPublicationEffectObservation",
    "IssueRepositoryPublicationEnrollmentRequest",
    "IssueRepositoryPublicationLockReleaseObservation",
    "IssueRepositoryPublicationPhysicalEffect",
    "IssueRepositoryPublicationRequest",
    "evaluate_repository_source_scope",
    "repository_publication_value_from_json",
    "repository_publication_value_from_payload",
    "repository_publication_value_to_json",
    "repository_publication_value_to_payload",
    "repository_source_scope_covers_path",
)


@dataclass(frozen=True, slots=True)
class IssueRepositoryOperationResult:
    """Immutable presentation of existing owner values, never an authority handle.

    The original owner codecs supply the payload. This carrier preserves their
    complete fields instead of projecting them into the success-only v1 DTO.
    """

    payload_json: str

    def __post_init__(self):
        if type(self.payload_json) is not str:
            raise TypeError("Repository result JSON required")
        payload = self.to_wire()
        if (
            type(payload) is not dict
            or payload.get("contract") != "aware.issue.repository-operation.v2"
            or payload.get("operation_ref")
            not in {"issue_sdk.commit_workspace", "issue_sdk.close_issue"}
            or type(payload.get("issue_ref")) is not str
            or payload.get("outcome")
            not in {"planned", "completed", "incomplete", "refused"}
        ):
            raise ValueError("Repository result presentation invalid")

    def to_wire(self):
        return json.loads(
            self.payload_json,
            object_pairs_hook=_json_object,
            parse_constant=_json_number,
            parse_float=_json_number,
        )

    @property
    def outcome(self):
        return self.to_wire()["outcome"]


class IssueRepositoryPublicationRefusal(ValueError):
    """Owner refusal; retained observation is evidence, never a replay permit."""

    def __init__(
        self,
        code,
        *,
        observation=None,
        workspace_observation=None,
        workspace_result=None,
        cleanup_observations=(),
        diagnostics=(),
        consumer_result=None,
    ):
        self.code = code
        self.observation = observation
        self.workspace_observation = workspace_observation
        self.workspace_result = workspace_result
        self.cleanup_observations = tuple(cleanup_observations)
        self.diagnostics = tuple(diagnostics)
        self.consumer_result = consumer_result
        self.result_validation_complete = False
        self.consumer_result_validation = (
            "unvalidated" if consumer_result is not None else "unavailable"
        )
        super().__init__(code)


_PUBLICATION_OWNERS = WeakKeyDictionary()
_PUBLICATION_CLIENT_PROVIDERS = WeakKeyDictionary()


class _PublicationHandle:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use the original Issue repository publication provider")

    def __copy__(self):
        raise TypeError("Issue publication handles cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Issue publication handles cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Issue publication handles cannot be serialized")

    @property
    def phase(self):
        return _publication_owner(self)._handle_phase(self)


class IssueRepositoryPublicationAdmission(_PublicationHandle):
    __slots__ = ()


class IssueRepositoryPublicationEnrollment(_PublicationHandle):
    __slots__ = ()


class IssueRepositoryPublicationLease(_PublicationHandle):
    __slots__ = ()

    @property
    def receipt_ref(self):
        return _publication_owner(self)._lease_receipt(self)


class IssueCloseAdmission(_PublicationHandle):
    __slots__ = ()


def _publication_owner(handle):
    if type(handle) not in (
        IssueRepositoryPublicationAdmission,
        IssueRepositoryPublicationEnrollment,
        IssueRepositoryPublicationLease,
        IssueCloseAdmission,
    ):
        raise IssueRepositoryPublicationRefusal(
            "issue_publication_original_handle_required"
        )
    owner = _PUBLICATION_OWNERS.get(handle)
    if owner is None:
        raise IssueRepositoryPublicationRefusal("issue_publication_handle_not_issued")
    return owner


def _issue_publication_handle(owner, handle_type):
    from aware_issue_operational_runtime.repository_publication import (
        IssueRepositoryPublicationRuntime,
    )

    if type(owner) is not IssueRepositoryPublicationRuntime or handle_type not in (
        IssueRepositoryPublicationAdmission,
        IssueRepositoryPublicationEnrollment,
        IssueRepositoryPublicationLease,
        IssueCloseAdmission,
    ):
        raise TypeError("Original Issue publication owner and handle type required")
    handle = object.__new__(handle_type)
    _PUBLICATION_OWNERS[handle] = owner
    return handle


class IssueRepositoryPublicationClient:
    """Own-runtime dispatch; values and observations never confer authority."""

    __slots__ = ("__weakref__",)

    def __init__(self, provider):
        from aware_issue_operational_runtime.repository_publication import (
            IssueRepositoryPublicationRuntime,
        )

        if type(provider) is not IssueRepositoryPublicationRuntime:
            raise TypeError("Original Issue repository publication runtime required")
        _PUBLICATION_CLIENT_PROVIDERS[self] = provider

    @property
    def _provider(self):
        provider = _PUBLICATION_CLIENT_PROVIDERS.get(self)
        if provider is None:
            raise IssueRepositoryPublicationRefusal(
                "issue_publication_sdk_client_not_issued"
            )
        return provider

    def admit_repository_publication(self, request: IssueRepositoryPublicationRequest):
        request = self._request(IssueRepositoryPublicationRequest, request)
        return self._provider.admit_repository_publication(request)

    def admit_repository_index_reconciliation(
        self, request: IssueRepositoryPublicationRequest
    ):
        request = self._request(IssueRepositoryPublicationRequest, request)
        return self._provider.admit_repository_index_reconciliation(request)

    def commit_workspace_result(self, request):
        from .operation import IssueCommitWorkspaceRequest

        if type(request) is not IssueCommitWorkspaceRequest:
            raise TypeError("Exact IssueCommitWorkspaceRequest required")
        from dataclasses import replace

        return self._invoke_result(
            replace(request), self._provider.commit_workspace_result
        )

    def close_issue_result(self, request):
        from .operation import IssueCloseRequest

        if type(request) is not IssueCloseRequest:
            raise TypeError("Exact IssueCloseRequest required")
        from dataclasses import replace

        return self._invoke_result(replace(request), self._provider.close_issue_result)

    @staticmethod
    def _invoke_result(request, call):
        try:
            result = call(request)
        except IssueRepositoryPublicationRefusal:
            raise
        except BaseException as error:
            values = BaseException.__dict__["__dict__"].__get__(error, BaseException)
            retained = values.get("provider_result")
            raise IssueRepositoryPublicationRefusal(
                "issue_repository_result_return_unavailable",
                consumer_result=retained
                if type(retained) is IssueRepositoryOperationResult
                else None,
            ) from error
        if type(result) is not IssueRepositoryOperationResult:
            retained = None
            if type(result) is dict:
                try:
                    retained = IssueRepositoryOperationResult(
                        json.dumps(result, allow_nan=False)
                    )
                except (TypeError, ValueError, RecursionError):
                    pass
            raise IssueRepositoryPublicationRefusal(
                "issue_repository_result_type_invalid", consumer_result=retained
            )
        payload = result.to_wire()
        if (
            payload["issue_ref"] != request.issue_ref
            or payload["operation_ref"] != request.operation_ref
        ):
            raise IssueRepositoryPublicationRefusal(
                "issue_repository_result_correlation_mismatch", consumer_result=result
            )
        from aware_issue_operational_runtime.repository_publication import (
            validate_repository_operation_result,
        )

        try:
            validate_repository_operation_result(request, payload)
        except (TypeError, ValueError, KeyError, RecursionError) as error:
            raise IssueRepositoryPublicationRefusal(
                "issue_repository_result_validation_failed",
                consumer_result=result,
                diagnostics=(f"unvalidated_result:{type(error).__name__}:{error}",),
            ) from error
        return result

    def commit_workspace(self, request):
        """Compose original owners; return full Workspace, Issue and cleanup values.

        These are the existing owner projections, not the legacy success-only
        IssueCommitWorkspaceResult or a reconstructed publication receipt.
        """
        from dataclasses import replace

        from .operation import IssueCommitWorkspaceRequest

        if type(request) is not IssueCommitWorkspaceRequest:
            raise TypeError("Exact IssueCommitWorkspaceRequest required")
        return self._provider.commit_workspace(replace(request))

    def close_issue(self, request):
        """Same original providers required; fresh Git facts cannot grant closeout."""
        from dataclasses import replace

        from .operation import IssueCloseRequest

        if type(request) is not IssueCloseRequest:
            raise TypeError("Exact IssueCloseRequest required")
        return self._provider.close_issue(replace(request))

    def prepare_repository_closeout(self, request, attempt_ref: str):
        from .operation import IssueCloseRequest

        if type(request) is not IssueCloseRequest:
            raise TypeError("Exact IssueCloseRequest required")
        # Reconstruct intent data, never reconstruct an admission.
        from dataclasses import replace

        request = replace(request)
        if type(attempt_ref) is not str or not attempt_ref.strip():
            raise ValueError("Nonblank closeout attempt_ref required")
        _convert(str, attempt_ref, "attempt_ref", decode=False)
        return self._provider.prepare_repository_closeout(request, attempt_ref)

    def apply_repository_closeout_source(self, close_admission):
        return self._request(
            IssueCloseoutSourceObservation,
            self._provider.apply_repository_closeout_source(close_admission),
        )

    def bind_closeout_publication(self, close_admission, binding):
        binding = self._request(IssueRepositoryPublicationBinding, binding)
        return self._provider.bind_closeout_publication(close_admission, binding)

    def finish_repository_closeout(self, close_admission, observation):
        observation = self._request(
            IssueRepositoryPublicationEffectObservation, observation
        )
        return self._request(
            IssueCloseoutObservation,
            self._provider.finish_repository_closeout(close_admission, observation),
        )

    def release_repository_closeout(self, close_admission):
        return self._request(
            IssuePublicationCleanupObservation,
            self._provider.release_repository_closeout(close_admission),
        )

    def enroll_repository_publication(
        self, admission, request: IssueRepositoryPublicationEnrollmentRequest
    ):
        request = self._request(IssueRepositoryPublicationEnrollmentRequest, request)
        return self._provider.enroll_repository_publication(admission, request)

    def consume_repository_publication(
        self, enrollment, request: IssueRepositoryPublicationConsumeRequest
    ):
        request = self._request(IssueRepositoryPublicationConsumeRequest, request)
        return self._provider.consume_repository_publication(enrollment, request)

    def finish_repository_publication(
        self, lease, observation: IssueRepositoryPublicationEffectObservation
    ):
        observation = self._request(
            IssueRepositoryPublicationEffectObservation, observation
        )
        return self._provider.finish_repository_publication(lease, observation)

    def observe_repository_publication_admission(self, admission):
        return self._provider.observe_repository_publication_admission(admission)

    def release_repository_publication_admission(self, admission):
        return self._provider.release_repository_publication_admission(admission)

    def release_repository_publication_enrollment(self, enrollment):
        return self._provider.release_repository_publication_enrollment(enrollment)

    @staticmethod
    def _request(expected, request):
        if type(request) is not expected:
            raise TypeError(f"Exact {expected.__name__} required")
        return repository_publication_value_from_payload(
            expected, repository_publication_value_to_payload(request)
        )


__all__ += (
    "IssueCloseAdmission",
    "IssueRepositoryOperationResult",
    "IssueRepositoryPublicationAdmission",
    "IssueRepositoryPublicationClient",
    "IssueRepositoryPublicationEnrollment",
    "IssueRepositoryPublicationLease",
    "IssueRepositoryPublicationRefusal",
)
