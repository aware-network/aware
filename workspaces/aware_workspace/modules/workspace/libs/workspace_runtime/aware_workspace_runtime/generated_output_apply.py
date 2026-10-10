"""Workspace-owned application of one admitted CodePackageDelta output.

The checkout is a recoverable mirror. Exact file effects occur through the
FileSystem descriptor-confined CAS primitive; a Workspace output head advances
only after the complete desired state is reread. No product activation,
WorkspaceRevision, graph commit, or canonical authority is issued here.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from threading import RLock
from typing import Never, Protocol, TextIO, cast, final
from weakref import WeakKeyDictionary

from aware_code_package_delta_contract import (
    CODE_PACKAGE_DELTA_CONTRACT,
    CodePackageDelta,
    CodePackageDeltaContractError,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
    CodePackageOutputState,
    derive_code_package_output_state,
)
from aware_code_semantic_contract_runtime import ContentDigest, canonical_json_bytes
from aware_file_system import (
    ConfinedFileMutationRequest,
    ConfinedFileMutationResult,
    ConfinedFileObservation,
    ConfinedMutationKind,
    ConfinedMutationOutcome,
    ConfinedObservationOutcome,
    mutate_confined_file,
    observe_confined_file,
)
from aware_local_service_runtime import (
    JsonObject,
    LocalOperationalStateConflict,
    LocalOperationalStateStore,
)

from .semantic_materialization_publication import (
    WorkspacePublishedSemanticCoordinate,
    WorkspaceSemanticMaterializationBodyStore,
    WorkspaceSemanticMaterializationHead,
)

WORKSPACE_GENERATED_OUTPUT_APPLY_REQUEST = (
    "aware.workspace.generated-output-apply-request.v1"
)
WORKSPACE_GENERATED_OUTPUT_HEAD = "aware.workspace.generated-output-head.v1"
WORKSPACE_GENERATED_OUTPUT_RECEIPT = (
    "aware.workspace.generated-output-apply-receipt.v1"
)
WORKSPACE_GENERATED_OUTPUT_AUTHORITY_GRADE = "workspace_authorized_mirror"
WORKSPACE_GENERATED_OUTPUT_NON_CLAIMS = (
    "canonical_commit",
    "canonical_replica",
    "generated_product_activation",
    "oig_commit",
    "workspace_revision",
)
DEFAULT_GENERATED_OUTPUT_STATE_NAMESPACE = "workspace.generated-output-head.v1"

_DIGEST_PREFIX = "sha256:"


@dataclass(frozen=True, slots=True)
class _WorkspaceGeneratedOutputApplyAdmissionState:
    request: WorkspaceGeneratedOutputApplyRequest
    checkout_root: Path


_ADMISSIONS: WeakKeyDictionary[
    WorkspaceGeneratedOutputApplyAdmission,
    _WorkspaceGeneratedOutputApplyAdmissionState,
] = WeakKeyDictionary()
_ADMISSIONS_LOCK = RLock()


class WorkspaceGeneratedOutputApplyError(RuntimeError):
    """Raised when apply authority or exact stored evidence is malformed."""


class WorkspaceGeneratedOutputApplyAuthority(Protocol):
    @property
    def operation_ref(self) -> str: ...

    @property
    def operation_digest(self) -> str: ...

    def admits(self, request: WorkspaceGeneratedOutputApplyRequest) -> bool: ...

    def checkout_root_for(
        self, request: WorkspaceGeneratedOutputApplyRequest
    ) -> Path: ...


class WorkspaceGeneratedOutputObserveFile(Protocol):
    def __call__(self, *, root: Path, path: str) -> ConfinedFileObservation: ...


class WorkspaceGeneratedOutputMutateFile(Protocol):
    def __call__(
        self, *, root: Path, request: ConfinedFileMutationRequest
    ) -> ConfinedFileMutationResult: ...


class WorkspaceGeneratedOutputApplyLease(Protocol):
    """Host-owned exclusive effect-window lease for one checkout/package."""

    def acquire(self, request: WorkspaceGeneratedOutputApplyRequest) -> bool: ...

    def release(self, request: WorkspaceGeneratedOutputApplyRequest) -> None: ...


class FileWorkspaceGeneratedOutputApplyLease:
    """Cross-process advisory effect-window lease below a host state root."""

    def __init__(self, state_root: Path) -> None:
        if not isinstance(state_root, Path) or not state_root.is_absolute():
            raise ValueError("generated output lease state root must be absolute")
        if state_root.is_symlink() or not state_root.is_dir():
            raise ValueError(
                "generated output lease state root must be an existing direct directory"
            )
        self._lease_root = (
            state_root.resolve(strict=True) / "generated_output_apply" / "leases"
        )
        self._lease_root.mkdir(parents=True, mode=0o700, exist_ok=True)
        if self._lease_root.is_symlink():
            raise ValueError("generated output lease directory cannot be a symlink")
        self._streams: dict[str, TextIO] = {}
        self._lock = RLock()

    def acquire(self, request: WorkspaceGeneratedOutputApplyRequest) -> bool:
        if type(request) is not WorkspaceGeneratedOutputApplyRequest:
            raise TypeError("lease request must be exact Workspace apply request")
        request.__post_init__()
        key = _lease_key(request)
        with self._lock:
            if key in self._streams:
                return False
            target = self._lease_root / (key + ".lock")
            if target.is_symlink():
                raise WorkspaceGeneratedOutputApplyError(
                    "generated output lease target cannot be a symlink"
                )
            flags = os.O_RDWR | os.O_CREAT
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            try:
                descriptor = os.open(target, flags, 0o600)
            except OSError as error:
                raise WorkspaceGeneratedOutputApplyError(
                    "generated output lease target could not be opened safely"
                ) from error
            stream = os.fdopen(descriptor, "r+", encoding="utf-8")
            try:
                _lock_nonblocking(stream)
            except OSError:
                stream.close()
                return False
            try:
                stream.seek(0)
                stream.truncate()
                stream.write(
                    json.dumps(
                        {
                            "acquired_at": datetime.now(UTC).isoformat(),
                            "checkout_binding_ref": request.checkout_binding_ref,
                            "package_ref": request.package_ref,
                            "pid": os.getpid(),
                            "request_digest": request.request_digest,
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    + "\n"
                )
                stream.flush()
                os.fsync(stream.fileno())
            except Exception:
                _unlock(stream)
                stream.close()
                raise
            self._streams[key] = stream
            return True

    def release(self, request: WorkspaceGeneratedOutputApplyRequest) -> None:
        if type(request) is not WorkspaceGeneratedOutputApplyRequest:
            raise TypeError("lease request must be exact Workspace apply request")
        request.__post_init__()
        key = _lease_key(request)
        with self._lock:
            stream = self._streams.pop(key, None)
        if stream is None:
            raise WorkspaceGeneratedOutputApplyError(
                "generated output apply lease is not held"
            )
        try:
            _unlock(stream)
        finally:
            stream.close()


@dataclass(frozen=True, slots=True)
class WorkspaceGeneratedOutputApplyRequest:
    package_ref: str
    output_package_name: str
    checkout_binding_ref: str
    checkout_binding_digest: str
    materialization_head_digest: str
    materialization_head_revision: int
    output_body_digest: str
    expected_output_head_revision: int
    operation_ref: str
    operation_digest: str
    request_digest: str
    contract: str = WORKSPACE_GENERATED_OUTPUT_APPLY_REQUEST

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_GENERATED_OUTPUT_APPLY_REQUEST:
            raise WorkspaceGeneratedOutputApplyError("apply request contract differs")
        for field in (
            "package_ref",
            "output_package_name",
            "checkout_binding_ref",
            "operation_ref",
        ):
            _token(getattr(self, field), field)
        for field in (
            "checkout_binding_digest",
            "materialization_head_digest",
            "output_body_digest",
            "operation_digest",
        ):
            _digest(getattr(self, field), field)
        _nonnegative(self.materialization_head_revision, "materialization_head_revision")
        _nonnegative(
            self.expected_output_head_revision, "expected_output_head_revision"
        )
        if self.materialization_head_revision == 0:
            raise WorkspaceGeneratedOutputApplyError(
                "materialization head revision must be positive"
            )
        if self.request_digest != _semantic_digest(self.contract, self._payload()):
            raise WorkspaceGeneratedOutputApplyError("apply request digest mismatched")

    @classmethod
    def create(
        cls,
        *,
        package_ref: str,
        output_package_name: str,
        checkout_binding_ref: str,
        checkout_binding_digest: str,
        materialization_head_digest: str,
        materialization_head_revision: int,
        output_body_digest: str,
        expected_output_head_revision: int,
        operation_ref: str,
        operation_digest: str,
    ) -> WorkspaceGeneratedOutputApplyRequest:
        values: dict[str, object] = {
            "package_ref": package_ref,
            "output_package_name": output_package_name,
            "checkout_binding_ref": checkout_binding_ref,
            "checkout_binding_digest": checkout_binding_digest,
            "materialization_head_digest": materialization_head_digest,
            "materialization_head_revision": materialization_head_revision,
            "output_body_digest": output_body_digest,
            "expected_output_head_revision": expected_output_head_revision,
            "operation_ref": operation_ref,
            "operation_digest": operation_digest,
        }
        return cls(
            package_ref=package_ref,
            output_package_name=output_package_name,
            checkout_binding_ref=checkout_binding_ref,
            checkout_binding_digest=checkout_binding_digest,
            materialization_head_digest=materialization_head_digest,
            materialization_head_revision=materialization_head_revision,
            output_body_digest=output_body_digest,
            expected_output_head_revision=expected_output_head_revision,
            operation_ref=operation_ref,
            operation_digest=operation_digest,
            request_digest=_semantic_digest(
                WORKSPACE_GENERATED_OUTPUT_APPLY_REQUEST, values
            ),
        )

    @property
    def request_ref(self) -> str:
        return "cas://workspace-generated-output/request/" + self.request_digest[7:]

    def _payload(self) -> dict[str, object]:
        return {
            "package_ref": self.package_ref,
            "output_package_name": self.output_package_name,
            "checkout_binding_ref": self.checkout_binding_ref,
            "checkout_binding_digest": self.checkout_binding_digest,
            "materialization_head_digest": self.materialization_head_digest,
            "materialization_head_revision": self.materialization_head_revision,
            "output_body_digest": self.output_body_digest,
            "expected_output_head_revision": self.expected_output_head_revision,
            "operation_ref": self.operation_ref,
            "operation_digest": self.operation_digest,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            **self._payload(),
            "request_digest": self.request_digest,
        }

    def to_json_bytes(self) -> bytes:
        self.__post_init__()
        return canonical_json_bytes(self.to_dict())

    @classmethod
    def from_json_bytes(
        cls, body: bytes
    ) -> WorkspaceGeneratedOutputApplyRequest:
        if type(body) is not bytes:
            raise TypeError("apply request body must be exact bytes")
        try:
            raw = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise WorkspaceGeneratedOutputApplyError(
                "apply request JSON is invalid"
            ) from error
        value = _object(
            raw,
            {
                "contract",
                "package_ref",
                "output_package_name",
                "checkout_binding_ref",
                "checkout_binding_digest",
                "materialization_head_digest",
                "materialization_head_revision",
                "output_body_digest",
                "expected_output_head_revision",
                "operation_ref",
                "operation_digest",
                "request_digest",
            },
            "apply request",
        )
        result = cls(
            package_ref=_string(value["package_ref"], "package_ref"),
            output_package_name=_string(
                value["output_package_name"], "output_package_name"
            ),
            checkout_binding_ref=_string(
                value["checkout_binding_ref"], "checkout_binding_ref"
            ),
            checkout_binding_digest=_string(
                value["checkout_binding_digest"], "checkout_binding_digest"
            ),
            materialization_head_digest=_string(
                value["materialization_head_digest"],
                "materialization_head_digest",
            ),
            materialization_head_revision=_integer(
                value["materialization_head_revision"],
                "materialization_head_revision",
            ),
            output_body_digest=_string(
                value["output_body_digest"], "output_body_digest"
            ),
            expected_output_head_revision=_integer(
                value["expected_output_head_revision"],
                "expected_output_head_revision",
            ),
            operation_ref=_string(value["operation_ref"], "operation_ref"),
            operation_digest=_string(
                value["operation_digest"], "operation_digest"
            ),
            request_digest=_string(value["request_digest"], "request_digest"),
            contract=_string(value["contract"], "contract"),
        )
        if result.to_json_bytes() != body:
            raise WorkspaceGeneratedOutputApplyError(
                "apply request body is not canonical"
            )
        return result


@final
class WorkspaceGeneratedOutputApplyAdmission:
    """Sealed, invocation-local join of operation authority and checkout root."""

    def __new__(cls) -> WorkspaceGeneratedOutputApplyAdmission:
        raise TypeError("apply admission is Workspace-constructed only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("apply admission is sealed")

    @property
    def request(self) -> WorkspaceGeneratedOutputApplyRequest:
        return _admission_state(self).request

    @property
    def checkout_root(self) -> Path:
        return _admission_state(self).checkout_root

    def _assert_intact(self) -> None:
        state = _admission_state(self)
        state.request.__post_init__()
        if (
            not isinstance(state.checkout_root, Path)
            or not state.checkout_root.is_absolute()
            or not state.checkout_root.is_dir()
            or state.checkout_root.is_symlink()
        ):
            raise WorkspaceGeneratedOutputApplyError(
                "admitted checkout root is no longer an exact directory"
            )

    def __reduce__(self) -> Never:
        raise TypeError("apply admission is not serializable")


def admit_workspace_generated_output_apply(
    *,
    request: WorkspaceGeneratedOutputApplyRequest,
    operation_authority: WorkspaceGeneratedOutputApplyAuthority,
) -> WorkspaceGeneratedOutputApplyAdmission:
    if type(request) is not WorkspaceGeneratedOutputApplyRequest:
        raise TypeError("request must be exact Workspace apply request")
    request.__post_init__()
    if (
        _token(operation_authority.operation_ref, "operation_ref")
        != request.operation_ref
        or _digest(operation_authority.operation_digest, "operation_digest")
        != request.operation_digest
    ):
        raise WorkspaceGeneratedOutputApplyError(
            "operation authority differs from apply request"
        )
    admitted = operation_authority.admits(request)
    if type(admitted) is not bool or not admitted:
        raise WorkspaceGeneratedOutputApplyError(
            "Workspace operation did not admit generated output apply"
        )
    checkout_root = operation_authority.checkout_root_for(request)
    if not isinstance(checkout_root, Path) or not checkout_root.is_absolute():
        raise WorkspaceGeneratedOutputApplyError(
            "Workspace operation returned no absolute checkout root"
        )
    if checkout_root.is_symlink() or not checkout_root.is_dir():
        raise WorkspaceGeneratedOutputApplyError(
            "Workspace operation checkout root is not an existing direct directory"
        )
    resolved_root = checkout_root.resolve(strict=True)
    admission = object.__new__(WorkspaceGeneratedOutputApplyAdmission)
    with _ADMISSIONS_LOCK:
        _ADMISSIONS[admission] = _WorkspaceGeneratedOutputApplyAdmissionState(
            request=request,
            checkout_root=resolved_root,
        )
    return admission


def _admission_state(
    admission: WorkspaceGeneratedOutputApplyAdmission,
) -> _WorkspaceGeneratedOutputApplyAdmissionState:
    if type(admission) is not WorkspaceGeneratedOutputApplyAdmission:
        raise TypeError("admission must be exact Workspace apply admission")
    with _ADMISSIONS_LOCK:
        state = _ADMISSIONS.get(admission)
    if state is None:
        raise WorkspaceGeneratedOutputApplyError(
            "apply admission is not registered by this Workspace runtime"
        )
    return state


@dataclass(frozen=True, slots=True)
class WorkspaceGeneratedOutputHead:
    package_ref: str
    output_package_name: str
    checkout_binding_ref: str
    checkout_binding_digest: str
    materialization_head_digest: str
    materialization_head_revision: int
    output_coordinate: WorkspacePublishedSemanticCoordinate
    output_state_body_ref: str
    output_state_body_digest: str
    output_state_size_bytes: int
    output_state_digest: str
    applied_path_count: int
    absent_paths: tuple[str, ...]
    mirror_state: str
    head_digest: str
    contract: str = WORKSPACE_GENERATED_OUTPUT_HEAD
    authority_grade: str = WORKSPACE_GENERATED_OUTPUT_AUTHORITY_GRADE
    non_claims: tuple[str, ...] = WORKSPACE_GENERATED_OUTPUT_NON_CLAIMS

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_GENERATED_OUTPUT_HEAD:
            raise WorkspaceGeneratedOutputApplyError("output head contract differs")
        if self.authority_grade != WORKSPACE_GENERATED_OUTPUT_AUTHORITY_GRADE:
            raise WorkspaceGeneratedOutputApplyError("output head authority differs")
        if tuple(self.non_claims) != WORKSPACE_GENERATED_OUTPUT_NON_CLAIMS:
            raise WorkspaceGeneratedOutputApplyError("output head non-claims differ")
        for field in (
            "package_ref",
            "output_package_name",
            "checkout_binding_ref",
            "output_state_body_ref",
        ):
            _token(getattr(self, field), field)
        for field in (
            "checkout_binding_digest",
            "materialization_head_digest",
            "output_state_body_digest",
            "output_state_digest",
        ):
            _digest(getattr(self, field), field)
        _positive(self.materialization_head_revision, "materialization_head_revision")
        _nonnegative(self.output_state_size_bytes, "output_state_size_bytes")
        _nonnegative(self.applied_path_count, "applied_path_count")
        if type(self.absent_paths) is not tuple:
            raise TypeError("output head absent_paths must be an exact tuple")
        for path in self.absent_paths:
            _relative_path(path)
        if tuple(sorted(set(self.absent_paths))) != self.absent_paths:
            raise WorkspaceGeneratedOutputApplyError(
                "output head absent paths are not canonical"
            )
        if type(self.output_coordinate) is not WorkspacePublishedSemanticCoordinate:
            raise TypeError("output coordinate must be exact Workspace coordinate")
        self.output_coordinate.__post_init__()
        if self.mirror_state != "applied_reread":
            raise WorkspaceGeneratedOutputApplyError("output mirror state differs")
        if self.output_state_body_ref != _body_ref(self.output_state_body_digest):
            raise WorkspaceGeneratedOutputApplyError("output state body ref differs")
        if self.head_digest != _semantic_digest(self.contract, self._payload()):
            raise WorkspaceGeneratedOutputApplyError("output head digest mismatched")

    @classmethod
    def create(
        cls,
        *,
        request: WorkspaceGeneratedOutputApplyRequest,
        output_coordinate: WorkspacePublishedSemanticCoordinate,
        output_state_body_ref: str,
        output_state_body_digest: str,
        output_state_size_bytes: int,
        output_state: CodePackageOutputState,
        absent_paths: tuple[str, ...],
    ) -> WorkspaceGeneratedOutputHead:
        values: dict[str, object] = {
            "package_ref": request.package_ref,
            "output_package_name": request.output_package_name,
            "checkout_binding_ref": request.checkout_binding_ref,
            "checkout_binding_digest": request.checkout_binding_digest,
            "materialization_head_digest": request.materialization_head_digest,
            "materialization_head_revision": request.materialization_head_revision,
            "output_coordinate": output_coordinate,
            "output_state_body_ref": output_state_body_ref,
            "output_state_body_digest": output_state_body_digest,
            "output_state_size_bytes": output_state_size_bytes,
            "output_state_digest": output_state.state_digest,
            "applied_path_count": len(output_state.paths),
            "absent_paths": list(absent_paths),
            "mirror_state": "applied_reread",
        }
        return cls(
            package_ref=request.package_ref,
            output_package_name=request.output_package_name,
            checkout_binding_ref=request.checkout_binding_ref,
            checkout_binding_digest=request.checkout_binding_digest,
            materialization_head_digest=request.materialization_head_digest,
            materialization_head_revision=request.materialization_head_revision,
            output_coordinate=output_coordinate,
            output_state_body_ref=output_state_body_ref,
            output_state_body_digest=output_state_body_digest,
            output_state_size_bytes=output_state_size_bytes,
            output_state_digest=output_state.state_digest,
            applied_path_count=len(output_state.paths),
            absent_paths=absent_paths,
            mirror_state="applied_reread",
            head_digest=_semantic_digest(
                WORKSPACE_GENERATED_OUTPUT_HEAD, _head_payload(values)
            ),
        )

    def _payload(self) -> dict[str, object]:
        return _head_payload(
            {
                "package_ref": self.package_ref,
                "output_package_name": self.output_package_name,
                "checkout_binding_ref": self.checkout_binding_ref,
                "checkout_binding_digest": self.checkout_binding_digest,
                "materialization_head_digest": self.materialization_head_digest,
                "materialization_head_revision": self.materialization_head_revision,
                "output_coordinate": self.output_coordinate,
                "output_state_body_ref": self.output_state_body_ref,
                "output_state_body_digest": self.output_state_body_digest,
                "output_state_size_bytes": self.output_state_size_bytes,
                "output_state_digest": self.output_state_digest,
                "applied_path_count": self.applied_path_count,
                "absent_paths": list(self.absent_paths),
                "mirror_state": self.mirror_state,
            }
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_grade": self.authority_grade,
            **self._payload(),
            "head_digest": self.head_digest,
            "non_claims": list(self.non_claims),
        }

    @classmethod
    def from_dict(cls, raw: object) -> WorkspaceGeneratedOutputHead:
        value = _object(
            raw,
            {
                "contract",
                "authority_grade",
                "package_ref",
                "output_package_name",
                "checkout_binding_ref",
                "checkout_binding_digest",
                "materialization_head_digest",
                "materialization_head_revision",
                "output_coordinate",
                "output_state_body_ref",
                "output_state_body_digest",
                "output_state_size_bytes",
                "output_state_digest",
                "applied_path_count",
                "absent_paths",
                "mirror_state",
                "head_digest",
                "non_claims",
            },
            "output head",
        )
        return cls(
            package_ref=_string(value["package_ref"], "package_ref"),
            output_package_name=_string(
                value["output_package_name"], "output_package_name"
            ),
            checkout_binding_ref=_string(
                value["checkout_binding_ref"], "checkout_binding_ref"
            ),
            checkout_binding_digest=_string(
                value["checkout_binding_digest"], "checkout_binding_digest"
            ),
            materialization_head_digest=_string(
                value["materialization_head_digest"],
                "materialization_head_digest",
            ),
            materialization_head_revision=_integer(
                value["materialization_head_revision"],
                "materialization_head_revision",
            ),
            output_coordinate=WorkspacePublishedSemanticCoordinate.from_dict(
                value["output_coordinate"]
            ),
            output_state_body_ref=_string(
                value["output_state_body_ref"], "output_state_body_ref"
            ),
            output_state_body_digest=_string(
                value["output_state_body_digest"], "output_state_body_digest"
            ),
            output_state_size_bytes=_integer(
                value["output_state_size_bytes"], "output_state_size_bytes"
            ),
            output_state_digest=_string(
                value["output_state_digest"], "output_state_digest"
            ),
            applied_path_count=_integer(
                value["applied_path_count"], "applied_path_count"
            ),
            absent_paths=tuple(
                _string(item, "absent_path")
                for item in _list(value["absent_paths"], "absent_paths")
            ),
            mirror_state=_string(value["mirror_state"], "mirror_state"),
            head_digest=_string(value["head_digest"], "head_digest"),
            contract=_string(value["contract"], "contract"),
            authority_grade=_string(
                value["authority_grade"], "authority_grade"
            ),
            non_claims=tuple(
                _string(item, "non_claim")
                for item in _list(value["non_claims"], "non_claims")
            ),
        )


@dataclass(frozen=True, slots=True)
class WorkspaceGeneratedOutputApplyReceipt:
    head: WorkspaceGeneratedOutputHead
    prior_head_revision: int
    head_revision: int
    head_advanced: bool
    mutation_count: int
    recovered_current_count: int
    reread_count: int
    receipt_digest: str
    contract: str = WORKSPACE_GENERATED_OUTPUT_RECEIPT

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_GENERATED_OUTPUT_RECEIPT:
            raise WorkspaceGeneratedOutputApplyError("apply receipt contract differs")
        if type(self.head) is not WorkspaceGeneratedOutputHead:
            raise TypeError("apply receipt head must be exact Workspace head")
        self.head.__post_init__()
        for field in (
            "prior_head_revision",
            "head_revision",
            "mutation_count",
            "recovered_current_count",
            "reread_count",
        ):
            _nonnegative(getattr(self, field), field)
        if type(self.head_advanced) is not bool:
            raise TypeError("head_advanced must be exact bool")
        if self.head_advanced:
            if self.head_revision != self.prior_head_revision + 1:
                raise WorkspaceGeneratedOutputApplyError(
                    "apply receipt head revision is not contiguous"
                )
        elif self.head_revision != self.prior_head_revision:
            raise WorkspaceGeneratedOutputApplyError(
                "current apply receipt changed head revision"
            )
        if self.receipt_digest != _semantic_digest(self.contract, self._payload()):
            raise WorkspaceGeneratedOutputApplyError("apply receipt digest mismatched")

    @classmethod
    def create(
        cls,
        *,
        head: WorkspaceGeneratedOutputHead,
        prior_head_revision: int,
        head_revision: int,
        head_advanced: bool,
        mutation_count: int,
        recovered_current_count: int,
        reread_count: int,
    ) -> WorkspaceGeneratedOutputApplyReceipt:
        values: dict[str, object] = {
            "head": head,
            "prior_head_revision": prior_head_revision,
            "head_revision": head_revision,
            "head_advanced": head_advanced,
            "mutation_count": mutation_count,
            "recovered_current_count": recovered_current_count,
            "reread_count": reread_count,
        }
        return cls(
            head=head,
            prior_head_revision=prior_head_revision,
            head_revision=head_revision,
            head_advanced=head_advanced,
            mutation_count=mutation_count,
            recovered_current_count=recovered_current_count,
            reread_count=reread_count,
            receipt_digest=_semantic_digest(
                WORKSPACE_GENERATED_OUTPUT_RECEIPT, _receipt_payload(values)
            ),
        )

    def _payload(self) -> dict[str, object]:
        return _receipt_payload(
            {
                "head": self.head,
                "prior_head_revision": self.prior_head_revision,
                "head_revision": self.head_revision,
                "head_advanced": self.head_advanced,
                "mutation_count": self.mutation_count,
                "recovered_current_count": self.recovered_current_count,
                "reread_count": self.reread_count,
            }
        )


@dataclass(frozen=True, slots=True)
class WorkspaceGeneratedOutputApplyMetrics:
    validation_ns: int
    preflight_ns: int
    mutation_ns: int
    reread_ns: int
    staging_ns: int
    head_cas_ns: int
    head_reread_ns: int
    total_ns: int
    preflight_count: int
    mutation_count: int
    recovered_current_count: int
    reread_count: int
    bytes_written: int
    bytes_deleted: int
    head_cas_count: int
    head_reread_count: int
    lease_acquire_ns: int
    lease_acquire_count: int
    lease_release_count: int

    def __post_init__(self) -> None:
        for field in self.__dataclass_fields__:
            _nonnegative(getattr(self, field), field)


@dataclass(frozen=True, slots=True)
class WorkspaceGeneratedOutputApplyResult:
    status: str
    receipt: WorkspaceGeneratedOutputApplyReceipt | None
    metrics: WorkspaceGeneratedOutputApplyMetrics
    conflict_path: str | None = None
    error_code: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"applied", "current", "conflicted", "failed"}:
            raise WorkspaceGeneratedOutputApplyError("apply result status differs")
        if type(self.metrics) is not WorkspaceGeneratedOutputApplyMetrics:
            raise TypeError("apply result metrics must be exact metrics")
        if self.status in {"applied", "current"}:
            if self.receipt is None or self.conflict_path or self.error_code:
                raise WorkspaceGeneratedOutputApplyError(
                    "successful apply result fields differ"
                )
        elif self.receipt is not None or self.error_code is None:
            raise WorkspaceGeneratedOutputApplyError(
                "unsuccessful apply result fields differ"
            )


class WorkspaceGeneratedOutputApplier:
    """Apply one exact output delta and publish a reread-backed mirror head."""

    def __init__(
        self,
        *,
        state_store: LocalOperationalStateStore,
        body_store: WorkspaceSemanticMaterializationBodyStore,
        apply_lease: WorkspaceGeneratedOutputApplyLease,
        state_namespace: str = DEFAULT_GENERATED_OUTPUT_STATE_NAMESPACE,
        observe_file: WorkspaceGeneratedOutputObserveFile = observe_confined_file,
        mutate_file: WorkspaceGeneratedOutputMutateFile = mutate_confined_file,
    ) -> None:
        self._state_store = state_store
        self._body_store = body_store
        self._apply_lease = apply_lease
        self._state_namespace = _token(state_namespace, "state_namespace")
        self._observe_file = observe_file
        self._mutate_file = mutate_file

    def read_head(
        self, *, package_ref: str, checkout_binding_ref: str
    ) -> tuple[int, WorkspaceGeneratedOutputHead] | None:
        key = _state_key(package_ref, checkout_binding_ref)
        record = self._state_store.read(self._state_namespace, key)
        if record is None or record.value is None:
            return None
        head = WorkspaceGeneratedOutputHead.from_dict(_thaw(record.value))
        if (
            head.package_ref != package_ref
            or head.checkout_binding_ref != checkout_binding_ref
        ):
            raise WorkspaceGeneratedOutputApplyError(
                "stored output head differs from state key"
            )
        return record.revision, head

    def apply(
        self,
        *,
        admission: WorkspaceGeneratedOutputApplyAdmission,
        materialization: tuple[int, WorkspaceSemanticMaterializationHead],
    ) -> WorkspaceGeneratedOutputApplyResult:
        started = time.perf_counter_ns()
        if type(admission) is not WorkspaceGeneratedOutputApplyAdmission:
            raise TypeError("admission must be exact Workspace apply admission")
        admission._assert_intact()
        request = admission.request
        lease_started = time.perf_counter_ns()
        acquired = self._apply_lease.acquire(request)
        lease_acquire_ns = time.perf_counter_ns() - lease_started
        if type(acquired) is not bool:
            raise WorkspaceGeneratedOutputApplyError(
                "generated output lease returned a non-boolean result"
            )
        if not acquired:
            result = self._terminal_failure(
                started=started,
                validation_ns=0,
                status="conflicted",
                error_code="generated_output_apply_lease_unavailable",
            )
            return _with_lease_metrics(
                result,
                started=started,
                lease_acquire_ns=lease_acquire_ns,
                acquired=False,
                released=False,
            )
        try:
            result = self._apply_locked(
                admission=admission,
                materialization=materialization,
            )
        finally:
            self._apply_lease.release(request)
        return _with_lease_metrics(
            result,
            started=started,
            lease_acquire_ns=lease_acquire_ns,
            acquired=True,
            released=True,
        )

    def _apply_locked(
        self,
        *,
        admission: WorkspaceGeneratedOutputApplyAdmission,
        materialization: tuple[int, WorkspaceSemanticMaterializationHead],
    ) -> WorkspaceGeneratedOutputApplyResult:
        started = time.perf_counter_ns()
        validation_started = started
        if type(admission) is not WorkspaceGeneratedOutputApplyAdmission:
            raise TypeError("admission must be exact Workspace apply admission")
        admission._assert_intact()
        request = admission.request
        root = admission.checkout_root
        if type(materialization) is not tuple or len(materialization) != 2:
            raise TypeError("materialization must be an exact revision/head pair")
        materialization_revision, materialization_head = materialization
        _positive(materialization_revision, "materialization_head_revision")
        if type(materialization_head) is not WorkspaceSemanticMaterializationHead:
            raise TypeError("materialization head must be exact Workspace head")
        materialization_head.__post_init__()
        if (
            materialization_revision != request.materialization_head_revision
            or materialization_head.package_ref != request.package_ref
            or materialization_head.head_digest
            != request.materialization_head_digest
        ):
            raise WorkspaceGeneratedOutputApplyError(
                "materialization head differs from apply admission"
            )
        output = _selected_delta_output(materialization_head, request)
        body_ref = _body_ref(output.body_digest)
        delta_body = self._body_store.read_body(body_ref)
        if type(delta_body) is not bytes:
            raise WorkspaceGeneratedOutputApplyError("staged output body is absent")
        if (
            ContentDigest.of_bytes(delta_body).value != output.body_digest
            or len(delta_body) != output.size_bytes
        ):
            raise WorkspaceGeneratedOutputApplyError(
                "staged output body differs from coordinate"
            )
        try:
            delta = CodePackageDelta.from_json_bytes(delta_body)
        except CodePackageDeltaContractError as error:
            raise WorkspaceGeneratedOutputApplyError(
                "staged output is not an exact CodePackageDelta"
            ) from error
        if delta.package_name != request.output_package_name:
            raise WorkspaceGeneratedOutputApplyError(
                "CodePackageDelta package differs from apply admission"
            )
        current = self.read_head(
            package_ref=request.package_ref,
            checkout_binding_ref=request.checkout_binding_ref,
        )
        if current is not None and (
            current[1].checkout_binding_digest != request.checkout_binding_digest
            or current[1].output_package_name != request.output_package_name
        ):
            raise WorkspaceGeneratedOutputApplyError(
                "current output head differs from admitted checkout/package"
            )
        actual_revision = 0 if current is None else current[0]
        if actual_revision != request.expected_output_head_revision:
            return self._terminal_failure(
                started=started,
                validation_ns=time.perf_counter_ns() - validation_started,
                status="conflicted",
                error_code="expected_output_head_revision_mismatch",
            )
        prior_state = self._prior_state(current, delta.package_name)
        if current is not None and (
            current[1].materialization_head_digest
            == request.materialization_head_digest
            and current[1].output_coordinate == output
        ):
            return self._complete_current(
                started=started,
                validation_started=validation_started,
                request=request,
                current=current,
                output_state=prior_state,
                root=root,
            )
        try:
            desired_state = derive_code_package_output_state(prior_state, delta)
        except CodePackageDeltaContractError as error:
            raise WorkspaceGeneratedOutputApplyError(
                "CodePackageDelta differs from current output state"
            ) from error
        absent_paths = _advance_absent_paths(
            () if current is None else current[1].absent_paths,
            delta,
        )
        validation_ns = time.perf_counter_ns() - validation_started

        preflight_started = time.perf_counter_ns()
        pending: list[CodePackageDeltaPath] = []
        recovered = 0
        for movement in delta.paths:
            observation = self._observe(root=root, path=movement.relative_path)
            disposition = _preflight_disposition(movement, observation)
            if disposition == "desired":
                recovered += 1
            elif disposition == "prior":
                pending.append(movement)
            else:
                return self._terminal_failure(
                    started=started,
                    validation_ns=validation_ns,
                    preflight_ns=time.perf_counter_ns() - preflight_started,
                    preflight_count=len(delta.paths),
                    recovered_current_count=recovered,
                    status=(
                        "conflicted"
                        if observation.outcome
                        is ConfinedObservationOutcome.OBSERVED
                        else "failed"
                    ),
                    conflict_path=movement.relative_path,
                    error_code=observation.error_code or "output_preflight_mismatch",
                )
        preflight_ns = time.perf_counter_ns() - preflight_started

        mutation_started = time.perf_counter_ns()
        mutation_count = 0
        bytes_written = 0
        bytes_deleted = 0
        for movement in pending:
            mutation_request = _mutation_request(movement)
            result = self._mutate_file(root=root, request=mutation_request)
            _validate_mutation_result(mutation_request, result)
            if result.outcome is not ConfinedMutationOutcome.APPLIED:
                return self._terminal_failure(
                    started=started,
                    validation_ns=validation_ns,
                    preflight_ns=preflight_ns,
                    mutation_ns=time.perf_counter_ns() - mutation_started,
                    preflight_count=len(delta.paths),
                    mutation_count=mutation_count,
                    recovered_current_count=recovered,
                    bytes_written=bytes_written,
                    bytes_deleted=bytes_deleted,
                    status=(
                        "conflicted"
                        if result.outcome is ConfinedMutationOutcome.CONFLICT
                        else "failed"
                    ),
                    conflict_path=movement.relative_path,
                    error_code=result.error_code or "output_mutation_failed",
                )
            mutation_count += 1
            bytes_written += result.after_size_bytes or 0
            if not result.after_exists:
                bytes_deleted += result.before_size_bytes or 0
        mutation_ns = time.perf_counter_ns() - mutation_started

        reread_started = time.perf_counter_ns()
        mismatch = self._reread_desired_state(
            root=root,
            output_state=desired_state,
            absent_paths=absent_paths,
        )
        reread_ns = time.perf_counter_ns() - reread_started
        if mismatch is not None:
            return self._terminal_failure(
                started=started,
                validation_ns=validation_ns,
                preflight_ns=preflight_ns,
                mutation_ns=mutation_ns,
                reread_ns=reread_ns,
                preflight_count=len(delta.paths),
                mutation_count=mutation_count,
                recovered_current_count=recovered,
                reread_count=len(desired_state.paths) + len(absent_paths),
                bytes_written=bytes_written,
                bytes_deleted=bytes_deleted,
                status="conflicted",
                conflict_path=mismatch,
                error_code="output_reread_mismatch",
            )
        return self._publish_head(
            started=started,
            validation_ns=validation_ns,
            preflight_ns=preflight_ns,
            mutation_ns=mutation_ns,
            reread_ns=reread_ns,
            request=request,
            output=output,
            output_state=desired_state,
            absent_paths=absent_paths,
            mutation_count=mutation_count,
            recovered_current_count=recovered,
            bytes_written=bytes_written,
            bytes_deleted=bytes_deleted,
        )

    def _prior_state(
        self,
        current: tuple[int, WorkspaceGeneratedOutputHead] | None,
        package_name: str,
    ) -> CodePackageOutputState:
        if current is None:
            return CodePackageOutputState.empty(package_name)
        body = self._body_store.read_body(current[1].output_state_body_ref)
        if type(body) is not bytes:
            raise WorkspaceGeneratedOutputApplyError(
                "current output state body is absent"
            )
        if ContentDigest.of_bytes(body).value != current[1].output_state_body_digest:
            raise WorkspaceGeneratedOutputApplyError(
                "current output state body digest differs"
            )
        try:
            state = CodePackageOutputState.from_json_bytes(body)
        except CodePackageDeltaContractError as error:
            raise WorkspaceGeneratedOutputApplyError(
                "current output state body is invalid"
            ) from error
        if (
            state.package_name != package_name
            or state.state_digest != current[1].output_state_digest
            or set(item.relative_path for item in state.paths)
            & set(current[1].absent_paths)
        ):
            raise WorkspaceGeneratedOutputApplyError(
                "current output state differs from output head"
            )
        return state

    def _complete_current(
        self,
        *,
        started: int,
        validation_started: int,
        request: WorkspaceGeneratedOutputApplyRequest,
        current: tuple[int, WorkspaceGeneratedOutputHead],
        output_state: CodePackageOutputState,
        root: Path,
    ) -> WorkspaceGeneratedOutputApplyResult:
        validation_ns = time.perf_counter_ns() - validation_started
        reread_started = time.perf_counter_ns()
        mismatch = self._reread_desired_state(
            root=root,
            output_state=output_state,
            absent_paths=current[1].absent_paths,
        )
        reread_ns = time.perf_counter_ns() - reread_started
        if mismatch is not None:
            return self._terminal_failure(
                started=started,
                validation_ns=validation_ns,
                reread_ns=reread_ns,
                reread_count=len(output_state.paths) + len(current[1].absent_paths),
                status="conflicted",
                conflict_path=mismatch,
                error_code="current_output_reread_mismatch",
            )
        head_revision, head = current
        head_reread_started = time.perf_counter_ns()
        reread = self.read_head(
            package_ref=request.package_ref,
            checkout_binding_ref=request.checkout_binding_ref,
        )
        head_reread_ns = time.perf_counter_ns() - head_reread_started
        if reread != current:
            raise WorkspaceGeneratedOutputApplyError("current output head moved")
        receipt = WorkspaceGeneratedOutputApplyReceipt.create(
            head=head,
            prior_head_revision=head_revision,
            head_revision=head_revision,
            head_advanced=False,
            mutation_count=0,
            recovered_current_count=(
                len(output_state.paths) + len(head.absent_paths)
            ),
            reread_count=len(output_state.paths) + len(head.absent_paths),
        )
        metrics = WorkspaceGeneratedOutputApplyMetrics(
            validation_ns=validation_ns,
            preflight_ns=0,
            mutation_ns=0,
            reread_ns=reread_ns,
            staging_ns=0,
            head_cas_ns=0,
            head_reread_ns=head_reread_ns,
            total_ns=time.perf_counter_ns() - started,
            preflight_count=0,
            mutation_count=0,
            recovered_current_count=(
                len(output_state.paths) + len(head.absent_paths)
            ),
            reread_count=len(output_state.paths) + len(head.absent_paths),
            bytes_written=0,
            bytes_deleted=0,
            head_cas_count=0,
            head_reread_count=1,
            lease_acquire_ns=0,
            lease_acquire_count=0,
            lease_release_count=0,
        )
        return WorkspaceGeneratedOutputApplyResult("current", receipt, metrics)

    def _publish_head(
        self,
        *,
        started: int,
        validation_ns: int,
        preflight_ns: int,
        mutation_ns: int,
        reread_ns: int,
        request: WorkspaceGeneratedOutputApplyRequest,
        output: WorkspacePublishedSemanticCoordinate,
        output_state: CodePackageOutputState,
        absent_paths: tuple[str, ...],
        mutation_count: int,
        recovered_current_count: int,
        bytes_written: int,
        bytes_deleted: int,
    ) -> WorkspaceGeneratedOutputApplyResult:
        staging_started = time.perf_counter_ns()
        state_body = output_state.to_json_bytes()
        state_body_digest = ContentDigest.of_bytes(state_body).value
        state_body_ref = _body_ref(state_body_digest)
        self._body_store.store_bodies(((state_body_ref, state_body),))
        observed = self._body_store.read_body(state_body_ref)
        if type(observed) is not bytes or observed != state_body:
            raise WorkspaceGeneratedOutputApplyError(
                "staged output state reread differs"
            )
        head = WorkspaceGeneratedOutputHead.create(
            request=request,
            output_coordinate=output,
            output_state_body_ref=state_body_ref,
            output_state_body_digest=state_body_digest,
            output_state_size_bytes=len(state_body),
            output_state=output_state,
            absent_paths=absent_paths,
        )
        staging_ns = time.perf_counter_ns() - staging_started
        state_key = _state_key(request.package_ref, request.checkout_binding_ref)
        cas_started = time.perf_counter_ns()
        try:
            record = self._state_store.compare_and_set(
                self._state_namespace,
                state_key,
                expected_revision=request.expected_output_head_revision,
                value=cast(JsonObject, head.to_dict()),
            )
        except LocalOperationalStateConflict:
            return self._terminal_failure(
                started=started,
                validation_ns=validation_ns,
                preflight_ns=preflight_ns,
                mutation_ns=mutation_ns,
                reread_ns=reread_ns,
                staging_ns=staging_ns,
                head_cas_ns=time.perf_counter_ns() - cas_started,
                preflight_count=mutation_count + recovered_current_count,
                mutation_count=mutation_count,
                recovered_current_count=recovered_current_count,
                reread_count=len(output_state.paths) + len(absent_paths),
                bytes_written=bytes_written,
                bytes_deleted=bytes_deleted,
                status="conflicted",
                error_code="output_head_cas_lost",
            )
        head_cas_ns = time.perf_counter_ns() - cas_started
        head_reread_started = time.perf_counter_ns()
        reread = self.read_head(
            package_ref=request.package_ref,
            checkout_binding_ref=request.checkout_binding_ref,
        )
        head_reread_ns = time.perf_counter_ns() - head_reread_started
        if reread != (record.revision, head):
            raise WorkspaceGeneratedOutputApplyError("output head reread differs")
        receipt = WorkspaceGeneratedOutputApplyReceipt.create(
            head=head,
            prior_head_revision=request.expected_output_head_revision,
            head_revision=record.revision,
            head_advanced=True,
            mutation_count=mutation_count,
            recovered_current_count=recovered_current_count,
            reread_count=len(output_state.paths) + len(absent_paths),
        )
        metrics = WorkspaceGeneratedOutputApplyMetrics(
            validation_ns=validation_ns,
            preflight_ns=preflight_ns,
            mutation_ns=mutation_ns,
            reread_ns=reread_ns,
            staging_ns=staging_ns,
            head_cas_ns=head_cas_ns,
            head_reread_ns=head_reread_ns,
            total_ns=time.perf_counter_ns() - started,
            preflight_count=mutation_count + recovered_current_count,
            mutation_count=mutation_count,
            recovered_current_count=recovered_current_count,
            reread_count=len(output_state.paths) + len(absent_paths),
            bytes_written=bytes_written,
            bytes_deleted=bytes_deleted,
            head_cas_count=1,
            head_reread_count=1,
            lease_acquire_ns=0,
            lease_acquire_count=0,
            lease_release_count=0,
        )
        return WorkspaceGeneratedOutputApplyResult("applied", receipt, metrics)

    def _reread_desired_state(
        self,
        *,
        root: Path,
        output_state: CodePackageOutputState,
        absent_paths: tuple[str, ...],
    ) -> str | None:
        desired = {item.relative_path: item for item in output_state.paths}
        for path, state in desired.items():
            observed = self._observe(root=root, path=path)
            if (
                observed.outcome is not ConfinedObservationOutcome.OBSERVED
                or not observed.exists
                or observed.content_digest != state.content_hash
                or observed.size_bytes != state.size_bytes
            ):
                return path
        for path in absent_paths:
            observed = self._observe(root=root, path=path)
            if (
                observed.outcome is not ConfinedObservationOutcome.OBSERVED
                or observed.exists
            ):
                return path
        return None

    def _observe(self, *, root: Path, path: str) -> ConfinedFileObservation:
        observed = self._observe_file(root=root, path=path)
        if type(observed) is not ConfinedFileObservation:
            raise WorkspaceGeneratedOutputApplyError(
                "generated output observer returned a foreign value"
            )
        observed.__post_init__()
        if observed.path != path:
            raise WorkspaceGeneratedOutputApplyError(
                "generated output observation path differs"
            )
        return observed

    def _terminal_failure(
        self,
        *,
        started: int,
        validation_ns: int,
        status: str,
        error_code: str,
        preflight_ns: int = 0,
        mutation_ns: int = 0,
        reread_ns: int = 0,
        staging_ns: int = 0,
        head_cas_ns: int = 0,
        preflight_count: int = 0,
        mutation_count: int = 0,
        recovered_current_count: int = 0,
        reread_count: int = 0,
        bytes_written: int = 0,
        bytes_deleted: int = 0,
        conflict_path: str | None = None,
    ) -> WorkspaceGeneratedOutputApplyResult:
        metrics = WorkspaceGeneratedOutputApplyMetrics(
            validation_ns=validation_ns,
            preflight_ns=preflight_ns,
            mutation_ns=mutation_ns,
            reread_ns=reread_ns,
            staging_ns=staging_ns,
            head_cas_ns=head_cas_ns,
            head_reread_ns=0,
            total_ns=time.perf_counter_ns() - started,
            preflight_count=preflight_count,
            mutation_count=mutation_count,
            recovered_current_count=recovered_current_count,
            reread_count=reread_count,
            bytes_written=bytes_written,
            bytes_deleted=bytes_deleted,
            head_cas_count=0,
            head_reread_count=0,
            lease_acquire_ns=0,
            lease_acquire_count=0,
            lease_release_count=0,
        )
        return WorkspaceGeneratedOutputApplyResult(
            status, None, metrics, conflict_path, error_code
        )


def _selected_delta_output(
    head: WorkspaceSemanticMaterializationHead,
    request: WorkspaceGeneratedOutputApplyRequest,
) -> WorkspacePublishedSemanticCoordinate:
    matches = tuple(
        item
        for item in head.outputs
        if item.contract_key == CODE_PACKAGE_DELTA_CONTRACT
        and item.body_digest == request.output_body_digest
    )
    if len(matches) != 1:
        raise WorkspaceGeneratedOutputApplyError(
            "materialization head has no unique admitted CodePackageDelta output"
        )
    output = matches[0]
    staged = tuple(
        item
        for item in head.semantic_bodies
        if item.coordinate == output and item.body_ref == _body_ref(output.body_digest)
    )
    if len(staged) != 1:
        raise WorkspaceGeneratedOutputApplyError(
            "CodePackageDelta output lacks exact staged body evidence"
        )
    return output


def _with_lease_metrics(
    result: WorkspaceGeneratedOutputApplyResult,
    *,
    started: int,
    lease_acquire_ns: int,
    acquired: bool,
    released: bool,
) -> WorkspaceGeneratedOutputApplyResult:
    metrics = replace(
        result.metrics,
        total_ns=time.perf_counter_ns() - started,
        lease_acquire_ns=lease_acquire_ns,
        lease_acquire_count=1 if acquired else 0,
        lease_release_count=1 if released else 0,
    )
    return replace(result, metrics=metrics)


def _preflight_disposition(
    movement: CodePackageDeltaPath,
    observation: ConfinedFileObservation,
) -> str:
    if observation.outcome is not ConfinedObservationOutcome.OBSERVED:
        return "failed"
    if movement.kind is CodePackageDeltaKind.create:
        if not observation.exists:
            return "prior"
        return (
            "desired"
            if observation.content_digest == movement.after_hash
            else "conflict"
        )
    if movement.kind is CodePackageDeltaKind.update:
        if observation.exists and observation.content_digest == movement.after_hash:
            return "desired"
        if observation.exists and observation.content_digest == movement.before_hash:
            return "prior"
        return "conflict"
    if not observation.exists:
        return "desired"
    return (
        "prior" if observation.content_digest == movement.before_hash else "conflict"
    )


def _mutation_request(movement: CodePackageDeltaPath) -> ConfinedFileMutationRequest:
    kind = {
        CodePackageDeltaKind.create: ConfinedMutationKind.CREATE,
        CodePackageDeltaKind.update: ConfinedMutationKind.UPDATE,
        CodePackageDeltaKind.delete: ConfinedMutationKind.DELETE,
    }[movement.kind]
    content = (
        movement.content_text.encode("utf-8")
        if movement.content_text is not None
        else None
    )
    return ConfinedFileMutationRequest(
        kind=kind,
        path=movement.relative_path,
        expected_exists=movement.kind is not CodePackageDeltaKind.create,
        expected_content_digest=movement.before_hash,
        content=content,
    )


def _validate_mutation_result(
    request: ConfinedFileMutationRequest,
    result: ConfinedFileMutationResult,
) -> None:
    if type(result) is not ConfinedFileMutationResult:
        raise WorkspaceGeneratedOutputApplyError(
            "generated output mutator returned a foreign value"
        )
    if result.kind is not request.kind or result.path != request.path:
        raise WorkspaceGeneratedOutputApplyError(
            "generated output mutation result differs from request"
        )
    if type(result.outcome) is not ConfinedMutationOutcome:
        raise WorkspaceGeneratedOutputApplyError(
            "generated output mutation outcome is foreign"
        )
    if result.outcome is not ConfinedMutationOutcome.APPLIED:
        return
    if (
        not result.before_exists
        or result.before_content_digest != request.expected_content_digest
    ) and request.expected_exists:
        raise WorkspaceGeneratedOutputApplyError(
            "applied mutation prior evidence differs from request"
        )
    if not request.expected_exists and result.before_exists:
        raise WorkspaceGeneratedOutputApplyError(
            "applied create reported an existing prior"
        )
    if request.kind is ConfinedMutationKind.DELETE:
        if result.after_exists or any(
            value is not None
            for value in (
                result.after_content_digest,
                result.after_size_bytes,
                result.after_content,
            )
        ):
            raise WorkspaceGeneratedOutputApplyError(
                "applied delete result retains output evidence"
            )
        return
    expected_content = request.content
    if (
        expected_content is None
        or not result.after_exists
        or result.after_content_digest
        != ContentDigest.of_bytes(expected_content).value
        or result.after_size_bytes != len(expected_content)
        or result.after_content != expected_content
    ):
        raise WorkspaceGeneratedOutputApplyError(
            "applied mutation result differs from desired bytes"
        )
def _advance_absent_paths(
    prior_absent_paths: tuple[str, ...],
    delta: CodePackageDelta,
) -> tuple[str, ...]:
    absent = set(prior_absent_paths)
    for movement in delta.paths:
        if movement.kind is CodePackageDeltaKind.delete:
            absent.add(movement.relative_path)
        else:
            absent.discard(movement.relative_path)
    return tuple(sorted(absent))


def _head_payload(values: dict[str, object]) -> dict[str, object]:
    output = cast(
        WorkspacePublishedSemanticCoordinate, values["output_coordinate"]
    )
    return {
        "package_ref": values["package_ref"],
        "output_package_name": values["output_package_name"],
        "checkout_binding_ref": values["checkout_binding_ref"],
        "checkout_binding_digest": values["checkout_binding_digest"],
        "materialization_head_digest": values["materialization_head_digest"],
        "materialization_head_revision": values["materialization_head_revision"],
        "output_coordinate": output.to_dict(),
        "output_state_body_ref": values["output_state_body_ref"],
        "output_state_body_digest": values["output_state_body_digest"],
        "output_state_size_bytes": values["output_state_size_bytes"],
        "output_state_digest": values["output_state_digest"],
        "applied_path_count": values["applied_path_count"],
        "absent_paths": values["absent_paths"],
        "mirror_state": values["mirror_state"],
    }


def _receipt_payload(values: dict[str, object]) -> dict[str, object]:
    head = cast(WorkspaceGeneratedOutputHead, values["head"])
    return {
        "head": head.to_dict(),
        "prior_head_revision": values["prior_head_revision"],
        "head_revision": values["head_revision"],
        "head_advanced": values["head_advanced"],
        "mutation_count": values["mutation_count"],
        "recovered_current_count": values["recovered_current_count"],
        "reread_count": values["reread_count"],
    }


def _state_key(package_ref: str, checkout_binding_ref: str) -> str:
    return _semantic_digest(
        "aware.workspace.generated-output-state-key.v1",
        {
            "package_ref": _token(package_ref, "package_ref"),
            "checkout_binding_ref": _token(
                checkout_binding_ref, "checkout_binding_ref"
            ),
        },
    )


def _lease_key(request: WorkspaceGeneratedOutputApplyRequest) -> str:
    return _semantic_digest(
        "aware.workspace.generated-output-apply-lease-key.v1",
        {
            "checkout_binding_digest": request.checkout_binding_digest,
            "checkout_binding_ref": request.checkout_binding_ref,
            "package_ref": request.package_ref,
        },
    )[7:]


def _lock_nonblocking(stream: TextIO) -> None:
    if os.name == "nt":
        import msvcrt

        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        return
    import fcntl

    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock(stream: TextIO) -> None:
    if os.name == "nt":
        import msvcrt

        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _body_ref(digest: str) -> str:
    return "cas://workspace-semantic-materialization/body/" + _digest(
        digest, "body digest"
    )[7:]


def _semantic_digest(contract: str, value: object) -> str:
    return ContentDigest.of_bytes(
        canonical_json_bytes({"contract": contract, "value": value})
    ).value


def _token(value: object, field: str) -> str:
    if type(value) is not str or not value or value != value.strip() or "\x00" in value:
        raise WorkspaceGeneratedOutputApplyError(f"{field} must be normalized text")
    return value


def _relative_path(value: object) -> str:
    text = _token(value, "relative path")
    parsed = PurePosixPath(text)
    if (
        parsed.is_absolute()
        or text != parsed.as_posix()
        or any(part in {"", ".", ".."} for part in parsed.parts)
    ):
        raise WorkspaceGeneratedOutputApplyError(
            "relative path must be normalized and confined"
        )
    return text


def _digest(value: object, field: str) -> str:
    text = _token(value, field)
    if (
        not text.startswith(_DIGEST_PREFIX)
        or len(text) != 71
        or any(character not in "0123456789abcdef" for character in text[7:])
    ):
        raise WorkspaceGeneratedOutputApplyError(f"{field} must be SHA-256")
    return text


def _nonnegative(value: object, field: str) -> int:
    if type(value) is not int or value < 0:
        raise WorkspaceGeneratedOutputApplyError(f"{field} must be nonnegative")
    return value


def _positive(value: object, field: str) -> int:
    if _nonnegative(value, field) == 0:
        raise WorkspaceGeneratedOutputApplyError(f"{field} must be positive")
    return cast(int, value)


def _object(value: object, fields: set[str], path: str) -> dict[str, object]:
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise WorkspaceGeneratedOutputApplyError(f"{path} must be an object")
    result = cast(dict[str, object], value)
    if set(result) != fields:
        raise WorkspaceGeneratedOutputApplyError(f"{path} fields differ")
    return result


def _string(value: object, field: str) -> str:
    if type(value) is not str:
        raise WorkspaceGeneratedOutputApplyError(f"{field} must be text")
    return value


def _integer(value: object, field: str) -> int:
    if type(value) is not int:
        raise WorkspaceGeneratedOutputApplyError(f"{field} must be an integer")
    return value


def _list(value: object, field: str) -> list[object]:
    if type(value) is not list:
        raise WorkspaceGeneratedOutputApplyError(f"{field} must be an array")
    return cast(list[object], value)


def _thaw(value: object) -> object:
    if value is None or type(value) in (str, bool, int, float):
        return value
    if isinstance(value, (list, tuple)):
        return [_thaw(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _thaw(item) for key, item in value.items()}
    raise WorkspaceGeneratedOutputApplyError(
        "operational output state contains a non-JSON value"
    )


__all__ = [
    "DEFAULT_GENERATED_OUTPUT_STATE_NAMESPACE",
    "FileWorkspaceGeneratedOutputApplyLease",
    "WORKSPACE_GENERATED_OUTPUT_APPLY_REQUEST",
    "WORKSPACE_GENERATED_OUTPUT_AUTHORITY_GRADE",
    "WORKSPACE_GENERATED_OUTPUT_HEAD",
    "WORKSPACE_GENERATED_OUTPUT_NON_CLAIMS",
    "WORKSPACE_GENERATED_OUTPUT_RECEIPT",
    "WorkspaceGeneratedOutputApplier",
    "WorkspaceGeneratedOutputApplyAdmission",
    "WorkspaceGeneratedOutputApplyAuthority",
    "WorkspaceGeneratedOutputApplyLease",
    "WorkspaceGeneratedOutputApplyError",
    "WorkspaceGeneratedOutputApplyMetrics",
    "WorkspaceGeneratedOutputApplyReceipt",
    "WorkspaceGeneratedOutputApplyRequest",
    "WorkspaceGeneratedOutputApplyResult",
    "WorkspaceGeneratedOutputHead",
    "WorkspaceGeneratedOutputMutateFile",
    "WorkspaceGeneratedOutputObserveFile",
    "admit_workspace_generated_output_apply",
]
