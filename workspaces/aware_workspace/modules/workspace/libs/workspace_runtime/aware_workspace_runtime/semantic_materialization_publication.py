"""Workspace-owned publication over one neutral Code execution completion.

The module adds operational Workspace authority to exact Code-produced bytes.
It does not execute providers, apply generated deltas, create a Workspace
revision, or issue graph/canonical authority.
"""

from __future__ import annotations

import inspect
import json
import os
import tempfile
import time
import unicodedata
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Never, Protocol, cast

from aware_code_package_delta_contract import (
    CodePackageDelta,
    CodePackageDeltaContractError,
    CodePackageOutputState,
    derive_code_package_output_state,
)
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    ContractViolation,
    ExecutionCompletion,
    ExecutionPublicationSnapshot,
    SemanticBody,
    SemanticContractInvocation,
    SemanticContractProviderDeclaration,
    SemanticContractRef,
    SemanticContractResult,
    SemanticContractRuntime,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
    TerminalStatus,
    TypedEmptyCoordinate,
    canonical_json_bytes,
    decode_invocation,
    decode_result,
)
from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    CatalogPairEpochExpectation,
)
from aware_code_semantic_contract_runtime.retained_admission_interfaces import (
    RetainedSemanticAdmissionExpectation,
)
from aware_local_service_runtime import (
    JsonObject,
    LocalOperationalNamespaceSnapshot,
    LocalOperationalStateConflict,
    LocalOperationalStateStore,
)

WORKSPACE_SEMANTIC_MATERIALIZATION_ADMISSION = (
    "aware.workspace.semantic-materialization-admission.v1"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_REQUEST = (
    "aware.workspace.semantic-materialization-request.v1"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD = (
    "aware.workspace.semantic-materialization-head.v1"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_RECEIPT = (
    "aware.workspace.semantic-materialization-publication-receipt.v1"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_REQUEST_V3 = (
    "aware.workspace.semantic-materialization-request.v3"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V3 = (
    "aware.workspace.semantic-materialization-head.v3"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4 = (
    "aware.workspace.semantic-materialization-head.v4"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_OUTPUT_STATE_BINDING_V4 = (
    "aware.workspace.semantic-materialization-output-state-binding.v4"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_RECEIPT_V3 = (
    "aware.workspace.semantic-materialization-publication-receipt.v3"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_RECEIPT_V4 = (
    "aware.workspace.semantic-materialization-publication-receipt.v4"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_REREAD_EVIDENCE_V3 = (
    "aware.workspace.semantic-materialization-head-reread-evidence.v3"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_REREAD_EVIDENCE_V4 = (
    "aware.workspace.semantic-materialization-head-reread-evidence.v4"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_AUTHORITY_GRADE = "workspace_authorized"
WORKSPACE_SEMANTIC_MATERIALIZATION_RESULT_WIRE = (
    "aware.code.semantic-contract-result.wire.v1"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_NON_CLAIMS = (
    "canonical_commit",
    "canonical_replica",
    "code_package_delta_applied",
    "generated_product_activation",
    "oig_commit",
    "workspace_revision",
)
DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE = (
    "workspace.semantic-materialization-head.v1"
)

_DIGEST_PREFIX = "sha256:"
_ADMISSION_CONSTRUCTION = object()


class WorkspaceSemanticMaterializationPublicationError(RuntimeError):
    """Raised when publication input, staging, or reread is not exact."""


class WorkspaceSemanticMaterializationPublicationConflict(
    WorkspaceSemanticMaterializationPublicationError
):
    """Raised when the expected package head is stale or mismatched."""


class WorkspaceSemanticMaterializationOperationAuthority(Protocol):
    """Workspace operation capability; a portable request cannot replace it."""

    @property
    def operation_ref(self) -> str: ...

    @property
    def operation_digest(self) -> str: ...

    def admits(self, request: WorkspaceSemanticMaterializationRequest) -> bool: ...


class WorkspaceSemanticMaterializationBodyStore(Protocol):
    """Immutable body staging port owned by the Workspace host."""

    def store_body(self, body_ref: str, canonical_body: bytes) -> None: ...

    def store_bodies(self, bodies: tuple[tuple[str, bytes], ...]) -> None: ...

    def read_body(self, body_ref: str) -> bytes | None: ...


class DirectoryWorkspaceSemanticMaterializationBodyStore:
    """Durable content-addressed terminal-body store with atomic publication."""

    def __init__(self, state_root: Path, *, repository_binding_ref: str) -> None:
        if not isinstance(state_root, Path) or not state_root.is_absolute():
            raise ValueError("semantic body state_root must be an absolute Path")
        binding = _token(repository_binding_ref, "repository_binding_ref")
        binding_digest = ContentDigest.of_bytes(binding.encode("utf-8")).value[7:]
        self._body_root = (
            state_root.resolve()
            / "semantic_materialization"
            / binding_digest
            / "bodies"
        )
        self._body_root.mkdir(parents=True, exist_ok=True)
        if self._body_root.is_symlink():
            raise ValueError("semantic body root cannot be a symlink")
        self._lock = RLock()

    @property
    def body_root(self) -> Path:
        return self._body_root

    def store_body(self, body_ref: str, canonical_body: bytes) -> None:
        self.store_bodies(((body_ref, canonical_body),))

    def store_bodies(self, bodies: tuple[tuple[str, bytes], ...]) -> None:
        if type(bodies) is not tuple:
            raise TypeError("semantic body batch must be an exact tuple")
        prepared: dict[str, tuple[Path, bytes]] = {}
        for index, pair in enumerate(bodies):
            if type(pair) is not tuple or len(pair) != 2:
                raise TypeError(f"semantic body batch item {index} must be a pair")
            body_ref, canonical_body = pair
            if type(canonical_body) is not bytes:
                raise TypeError("semantic body must be exact bytes")
            digest = _digest_from_body_ref(body_ref)
            if ContentDigest.of_bytes(canonical_body).value != digest:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "semantic body bytes differ from body ref"
                )
            existing = prepared.get(body_ref)
            if existing is not None and existing[1] != canonical_body:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "semantic body batch identity collision"
                )
            prepared[body_ref] = (self._body_path(digest), canonical_body)
        with self._lock:
            changed_directories: set[Path] = set()
            for target, canonical_body in prepared.values():
                if target.is_symlink():
                    raise WorkspaceSemanticMaterializationPublicationError(
                        "semantic body target cannot be a symlink"
                    )
                try:
                    existing_body = target.read_bytes()
                except FileNotFoundError:
                    existing_body = None
                if existing_body is not None:
                    if existing_body != canonical_body:
                        raise WorkspaceSemanticMaterializationPublicationError(
                            "semantic body identity collision"
                        )
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                descriptor, temporary_name = tempfile.mkstemp(
                    prefix=".semantic-body-", dir=target.parent
                )
                temporary = Path(temporary_name)
                try:
                    with os.fdopen(descriptor, "wb") as stream:
                        stream.write(canonical_body)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temporary, target)
                    changed_directories.add(target.parent)
                finally:
                    temporary.unlink(missing_ok=True)
            for directory in sorted(changed_directories):
                directory_descriptor = os.open(directory, os.O_RDONLY)
                try:
                    os.fsync(directory_descriptor)
                finally:
                    os.close(directory_descriptor)

    def read_body(self, body_ref: str) -> bytes | None:
        digest = _digest_from_body_ref(body_ref)
        target = self._body_path(digest)
        with self._lock:
            if target.is_symlink():
                raise WorkspaceSemanticMaterializationPublicationError(
                    "semantic body target cannot be a symlink"
                )
            try:
                body = target.read_bytes()
            except FileNotFoundError:
                return None
        if ContentDigest.of_bytes(body).value != digest:
            raise WorkspaceSemanticMaterializationPublicationError(
                "durable semantic body digest mismatched"
            )
        return body

    def _body_path(self, digest: str) -> Path:
        hexadecimal = _digest(digest, "body digest")[7:]
        return self._body_root / (hexadecimal + ".body")


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationRequest:
    """Portable Workspace request bound to source authority and one Code call."""

    package_ref: str
    package_kind: str
    manifest_digest: str
    source_authority_ref: str
    source_authority_digest: str
    operation_ref: str
    operation_digest: str
    profile_ref: str
    profile_digest: str
    invocation_digest: str
    request_digest: str
    contract: str = WORKSPACE_SEMANTIC_MATERIALIZATION_REQUEST
    authority_grade: str = "portable_input"

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_SEMANTIC_MATERIALIZATION_REQUEST:
            raise WorkspaceSemanticMaterializationPublicationError(
                "semantic materialization request contract unsupported"
            )
        if self.authority_grade != "portable_input":
            raise WorkspaceSemanticMaterializationPublicationError(
                "semantic materialization request authority grade unsupported"
            )
        for field in (
            "package_ref",
            "package_kind",
            "source_authority_ref",
            "operation_ref",
            "profile_ref",
        ):
            object.__setattr__(self, field, _token(getattr(self, field), field))
        for field in (
            "manifest_digest",
            "source_authority_digest",
            "operation_digest",
            "profile_digest",
            "invocation_digest",
        ):
            object.__setattr__(self, field, _digest(getattr(self, field), field))
        expected = _semantic_digest(self.contract, self._payload())
        if self.request_digest != expected:
            raise WorkspaceSemanticMaterializationPublicationError(
                "semantic materialization request digest mismatched"
            )

    @classmethod
    def create(
        cls,
        *,
        package_ref: str,
        package_kind: str,
        manifest_digest: str,
        source_authority_ref: str,
        source_authority_digest: str,
        operation_ref: str,
        operation_digest: str,
        profile_ref: str,
        profile_digest: str,
        invocation_digest: str,
    ) -> WorkspaceSemanticMaterializationRequest:
        values = {
            "package_ref": package_ref,
            "package_kind": package_kind,
            "manifest_digest": manifest_digest,
            "source_authority_ref": source_authority_ref,
            "source_authority_digest": source_authority_digest,
            "operation_ref": operation_ref,
            "operation_digest": operation_digest,
            "profile_ref": profile_ref,
            "profile_digest": profile_digest,
            "invocation_digest": invocation_digest,
        }
        return cls(
            **values,
            request_digest=_semantic_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_REQUEST, values
            ),
        )

    @property
    def request_ref(self) -> str:
        return (
            "cas://workspace-semantic-materialization/request/"
            + self.request_digest.removeprefix(_DIGEST_PREFIX)
        )

    def _payload(self) -> dict[str, object]:
        return {
            "package_ref": self.package_ref,
            "package_kind": self.package_kind,
            "manifest_digest": self.manifest_digest,
            "source_authority_ref": self.source_authority_ref,
            "source_authority_digest": self.source_authority_digest,
            "operation_ref": self.operation_ref,
            "operation_digest": self.operation_digest,
            "profile_ref": self.profile_ref,
            "profile_digest": self.profile_digest,
            "invocation_digest": self.invocation_digest,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_grade": self.authority_grade,
            **self._payload(),
            "request_digest": self.request_digest,
        }

    def to_json_bytes(self) -> bytes:
        self.__post_init__()
        return canonical_json_bytes(self.to_dict())

    @classmethod
    def from_json_bytes(cls, value: bytes) -> WorkspaceSemanticMaterializationRequest:
        if type(value) is not bytes:
            raise TypeError("semantic materialization request bytes must be exact")
        try:
            payload = json.loads(value)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise WorkspaceSemanticMaterializationPublicationError(
                "semantic materialization request JSON is invalid"
            ) from error
        exact = _object(
            payload,
            {
                "contract",
                "authority_grade",
                "package_ref",
                "package_kind",
                "manifest_digest",
                "source_authority_ref",
                "source_authority_digest",
                "operation_ref",
                "operation_digest",
                "profile_ref",
                "profile_digest",
                "invocation_digest",
                "request_digest",
            },
            "semantic materialization request",
        )
        result = cls(
            package_ref=_string(exact["package_ref"], "package_ref"),
            package_kind=_string(exact["package_kind"], "package_kind"),
            manifest_digest=_string(exact["manifest_digest"], "manifest_digest"),
            source_authority_ref=_string(
                exact["source_authority_ref"], "source_authority_ref"
            ),
            source_authority_digest=_string(
                exact["source_authority_digest"], "source_authority_digest"
            ),
            operation_ref=_string(exact["operation_ref"], "operation_ref"),
            operation_digest=_string(exact["operation_digest"], "operation_digest"),
            profile_ref=_string(exact["profile_ref"], "profile_ref"),
            profile_digest=_string(exact["profile_digest"], "profile_digest"),
            invocation_digest=_string(exact["invocation_digest"], "invocation_digest"),
            request_digest=_string(exact["request_digest"], "request_digest"),
            contract=_string(exact["contract"], "contract"),
            authority_grade=_string(exact["authority_grade"], "authority_grade"),
        )
        if result.to_json_bytes() != value:
            raise WorkspaceSemanticMaterializationPublicationError(
                "semantic materialization request is not canonical JSON"
            )
        return result


class WorkspaceSemanticMaterializationAdmission:
    """Nonserializable join of portable composition and Workspace operation."""

    __slots__ = (
        "_authority_grade",
        "_manifest_digest",
        "_operation_digest",
        "_operation_ref",
        "_package_kind",
        "_package_ref",
        "_request_digest",
        "_request_ref",
        "_source_authority_digest",
        "_source_authority_ref",
    )

    def __init__(
        self,
        construction_token: object,
        *,
        package_ref: str,
        package_kind: str,
        manifest_digest: str,
        source_authority_ref: str,
        source_authority_digest: str,
        request_ref: str,
        request_digest: str,
        operation_ref: str,
        operation_digest: str,
    ) -> None:
        if construction_token is not _ADMISSION_CONSTRUCTION:
            raise TypeError("semantic materialization admission is runtime-issued only")
        self._package_ref = _token(package_ref, "package_ref")
        self._package_kind = _token(package_kind, "package_kind")
        self._manifest_digest = _digest(manifest_digest, "manifest_digest")
        self._source_authority_ref = _token(
            source_authority_ref, "source_authority_ref"
        )
        self._source_authority_digest = _digest(
            source_authority_digest, "source_authority_digest"
        )
        self._request_ref = _token(request_ref, "request_ref")
        self._request_digest = _digest(request_digest, "request_digest")
        self._operation_ref = _token(operation_ref, "operation_ref")
        self._operation_digest = _digest(operation_digest, "operation_digest")
        self._authority_grade = WORKSPACE_SEMANTIC_MATERIALIZATION_AUTHORITY_GRADE

    @property
    def package_ref(self) -> str:
        return self._package_ref

    @property
    def package_kind(self) -> str:
        return self._package_kind

    @property
    def manifest_digest(self) -> str:
        return self._manifest_digest

    @property
    def source_authority_ref(self) -> str:
        return self._source_authority_ref

    @property
    def source_authority_digest(self) -> str:
        return self._source_authority_digest

    @property
    def request_ref(self) -> str:
        return self._request_ref

    @property
    def request_digest(self) -> str:
        return self._request_digest

    @property
    def operation_ref(self) -> str:
        return self._operation_ref

    @property
    def operation_digest(self) -> str:
        return self._operation_digest

    @property
    def authority_grade(self) -> str:
        return self._authority_grade

    def _assert_intact(self) -> None:
        _token(self._package_ref, "package_ref")
        _token(self._package_kind, "package_kind")
        _digest(self._manifest_digest, "manifest_digest")
        _token(self._source_authority_ref, "source_authority_ref")
        _digest(self._source_authority_digest, "source_authority_digest")
        _token(self._request_ref, "request_ref")
        _digest(self._request_digest, "request_digest")
        if self._request_ref != (
            "cas://workspace-semantic-materialization/request/"
            + self._request_digest.removeprefix(_DIGEST_PREFIX)
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "semantic materialization admission request ref was restamped"
            )
        _token(self._operation_ref, "operation_ref")
        _digest(self._operation_digest, "operation_digest")
        if self._authority_grade != WORKSPACE_SEMANTIC_MATERIALIZATION_AUTHORITY_GRADE:
            raise WorkspaceSemanticMaterializationPublicationError(
                "semantic materialization admission was restamped"
            )

    def __reduce__(self) -> Never:
        raise TypeError("semantic materialization admission is not serializable")


def admit_workspace_semantic_materialization(
    *,
    request: WorkspaceSemanticMaterializationRequest,
    operation_authority: WorkspaceSemanticMaterializationOperationAuthority,
) -> WorkspaceSemanticMaterializationAdmission:
    """Join one portable request to its resident Workspace operation."""

    if type(request) is not WorkspaceSemanticMaterializationRequest:
        raise TypeError("request must be exact Workspace materialization request")
    request.__post_init__()
    operation_ref = _token(operation_authority.operation_ref, "operation_ref")
    operation_digest = _digest(operation_authority.operation_digest, "operation_digest")
    if (
        request.operation_ref != operation_ref
        or request.operation_digest != operation_digest
    ):
        raise WorkspaceSemanticMaterializationPublicationError(
            "operation authority differs from materialization request"
        )
    admitted = operation_authority.admits(request)
    if type(admitted) is not bool or not admitted:
        raise WorkspaceSemanticMaterializationPublicationError(
            "Workspace operation did not admit semantic materialization request"
        )
    return WorkspaceSemanticMaterializationAdmission(
        _ADMISSION_CONSTRUCTION,
        package_ref=request.package_ref,
        package_kind=request.package_kind,
        manifest_digest=request.manifest_digest,
        source_authority_ref=request.source_authority_ref,
        source_authority_digest=request.source_authority_digest,
        request_ref=request.request_ref,
        request_digest=request.request_digest,
        operation_ref=operation_ref,
        operation_digest=operation_digest,
    )


@dataclass(frozen=True, slots=True, order=True)
class WorkspacePublishedSemanticCoordinate:
    role: str
    contract_key: str
    contract_version: str
    contract_schema_digest: str
    value_ref: str
    body_digest: str
    size_bytes: int

    def __post_init__(self) -> None:
        for field in ("role", "contract_key", "contract_version", "value_ref"):
            object.__setattr__(self, field, _token(getattr(self, field), field))
        object.__setattr__(
            self,
            "contract_schema_digest",
            _digest(self.contract_schema_digest, "contract_schema_digest"),
        )
        object.__setattr__(
            self, "body_digest", _digest(self.body_digest, "body_digest")
        )
        _nonnegative_int(self.size_bytes, "size_bytes")

    @classmethod
    def from_code(
        cls, value: SemanticValueCoordinate
    ) -> WorkspacePublishedSemanticCoordinate:
        if type(value) is not SemanticValueCoordinate:
            raise TypeError("semantic coordinate must be exact Code value")
        value.to_wire()
        return cls(
            role=value.role,
            contract_key=value.contract.key,
            contract_version=value.contract.version,
            contract_schema_digest=value.contract.schema_digest.value,
            value_ref=value.value_ref,
            body_digest=value.digest.value,
            size_bytes=value.size_bytes,
        )

    @classmethod
    def from_dict(cls, value: object) -> WorkspacePublishedSemanticCoordinate:
        payload = _object(
            value,
            {
                "role",
                "contract_key",
                "contract_version",
                "contract_schema_digest",
                "value_ref",
                "body_digest",
                "size_bytes",
            },
            "semantic coordinate",
        )
        return cls(
            role=_string(payload["role"], "role"),
            contract_key=_string(payload["contract_key"], "contract_key"),
            contract_version=_string(payload["contract_version"], "contract_version"),
            contract_schema_digest=_string(
                payload["contract_schema_digest"], "contract_schema_digest"
            ),
            value_ref=_string(payload["value_ref"], "value_ref"),
            body_digest=_string(payload["body_digest"], "body_digest"),
            size_bytes=_integer(payload["size_bytes"], "size_bytes"),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "contract_key": self.contract_key,
            "contract_version": self.contract_version,
            "contract_schema_digest": self.contract_schema_digest,
            "value_ref": self.value_ref,
            "body_digest": self.body_digest,
            "size_bytes": self.size_bytes,
        }

    def to_code_wire(self) -> dict[str, object]:
        return {
            "contract": {
                "key": self.contract_key,
                "schema_digest": self.contract_schema_digest,
                "version": self.contract_version,
            },
            "digest": self.body_digest,
            "role": self.role,
            "size_bytes": self.size_bytes,
            "value_ref": self.value_ref,
        }


@dataclass(frozen=True, slots=True, order=True)
class WorkspaceStagedSemanticBody:
    coordinate: WorkspacePublishedSemanticCoordinate
    body_ref: str

    def __post_init__(self) -> None:
        if type(self.coordinate) is not WorkspacePublishedSemanticCoordinate:
            raise TypeError("staged coordinate must be exact Workspace value")
        self.coordinate.__post_init__()
        object.__setattr__(self, "body_ref", _token(self.body_ref, "body_ref"))
        if self.body_ref != _body_ref(self.coordinate.body_digest):
            raise WorkspaceSemanticMaterializationPublicationError(
                "semantic body ref differs from content digest"
            )

    @classmethod
    def from_code(cls, value: SemanticValueCoordinate) -> WorkspaceStagedSemanticBody:
        coordinate = WorkspacePublishedSemanticCoordinate.from_code(value)
        return cls(coordinate, _body_ref(coordinate.body_digest))

    @classmethod
    def from_dict(cls, value: object) -> WorkspaceStagedSemanticBody:
        payload = _object(value, {"coordinate", "body_ref"}, "staged body")
        return cls(
            WorkspacePublishedSemanticCoordinate.from_dict(payload["coordinate"]),
            _string(payload["body_ref"], "body_ref"),
        )

    def to_dict(self) -> dict[str, object]:
        return {"coordinate": self.coordinate.to_dict(), "body_ref": self.body_ref}


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationHead:
    package_ref: str
    package_kind: str
    manifest_digest: str
    source_authority_ref: str
    source_authority_digest: str
    request_ref: str
    request_digest: str
    operation_ref: str
    operation_digest: str
    invocation_digest: str
    profile_digest: str
    terminal_status: str
    result_digest: str
    result_body_ref: str
    result_body_digest: str
    result_body_size_bytes: int
    candidate: WorkspacePublishedSemanticCoordinate
    transition_digest: str | None
    effect_digest: str
    outputs: tuple[WorkspacePublishedSemanticCoordinate, ...]
    semantic_bodies: tuple[WorkspaceStagedSemanticBody, ...]
    output_activation: str
    head_digest: str
    contract: str = WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD
    authority_grade: str = WORKSPACE_SEMANTIC_MATERIALIZATION_AUTHORITY_GRADE
    non_claims: tuple[str, ...] = WORKSPACE_SEMANTIC_MATERIALIZATION_NON_CLAIMS

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD:
            raise WorkspaceSemanticMaterializationPublicationError(
                "semantic materialization head contract unsupported"
            )
        if self.authority_grade != WORKSPACE_SEMANTIC_MATERIALIZATION_AUTHORITY_GRADE:
            raise WorkspaceSemanticMaterializationPublicationError(
                "semantic materialization head authority grade unsupported"
            )
        if tuple(self.non_claims) != WORKSPACE_SEMANTIC_MATERIALIZATION_NON_CLAIMS:
            raise WorkspaceSemanticMaterializationPublicationError(
                "semantic materialization head non-claims differ"
            )
        for field in (
            "package_ref",
            "package_kind",
            "source_authority_ref",
            "request_ref",
            "operation_ref",
            "terminal_status",
            "result_body_ref",
            "output_activation",
        ):
            object.__setattr__(self, field, _token(getattr(self, field), field))
        for field in (
            "manifest_digest",
            "source_authority_digest",
            "request_digest",
            "operation_digest",
            "invocation_digest",
            "profile_digest",
            "result_digest",
            "result_body_digest",
            "effect_digest",
        ):
            object.__setattr__(self, field, _digest(getattr(self, field), field))
        if self.transition_digest is not None:
            object.__setattr__(
                self,
                "transition_digest",
                _digest(self.transition_digest, "transition_digest"),
            )
        _nonnegative_int(self.result_body_size_bytes, "result_body_size_bytes")
        if type(self.candidate) is not WorkspacePublishedSemanticCoordinate:
            raise TypeError("head candidate must be exact Workspace coordinate")
        outputs = _exact_tuple(
            self.outputs, WorkspacePublishedSemanticCoordinate, "outputs"
        )
        bodies = _exact_tuple(
            self.semantic_bodies, WorkspaceStagedSemanticBody, "semantic_bodies"
        )
        if outputs != tuple(sorted(set(outputs))):
            raise WorkspaceSemanticMaterializationPublicationError(
                "head outputs must be unique and ordered"
            )
        if bodies != tuple(sorted(set(bodies))):
            raise WorkspaceSemanticMaterializationPublicationError(
                "head semantic bodies must be unique and ordered"
            )
        if self.output_activation not in {"not_requested", "staged_not_applied"}:
            raise WorkspaceSemanticMaterializationPublicationError(
                "head output activation unsupported"
            )
        if self.output_activation == "not_requested" and outputs:
            raise WorkspaceSemanticMaterializationPublicationError(
                "head outputs require staged activation posture"
            )
        if self.output_activation == "staged_not_applied" and not outputs:
            raise WorkspaceSemanticMaterializationPublicationError(
                "staged activation requires outputs"
            )
        expected = _semantic_digest(self.contract, self._payload())
        if self.head_digest != expected:
            raise WorkspaceSemanticMaterializationPublicationError(
                "semantic materialization head digest mismatched"
            )

    @classmethod
    def create(
        cls,
        *,
        admission: WorkspaceSemanticMaterializationAdmission,
        invocation: SemanticContractInvocation,
        result: SemanticContractResult,
        result_digest: str,
        transition_digest: str | None,
        effect_digest: str,
        result_body_ref: str,
        result_body_digest: str,
        result_body_size_bytes: int,
        candidate: WorkspacePublishedSemanticCoordinate,
        semantic_bodies: tuple[WorkspaceStagedSemanticBody, ...],
    ) -> WorkspaceSemanticMaterializationHead:
        if result.effect is None:
            raise WorkspaceSemanticMaterializationPublicationError(
                "successful result lacks prepared effect"
            )
        outputs = tuple(
            sorted(
                WorkspacePublishedSemanticCoordinate.from_code(item.output)
                for item in result.outputs
            )
        )
        ordered_bodies = tuple(sorted(semantic_bodies))
        output_activation = "staged_not_applied" if outputs else "not_requested"
        values: dict[str, object] = {
            "package_ref": admission.package_ref,
            "package_kind": admission.package_kind,
            "manifest_digest": admission.manifest_digest,
            "source_authority_ref": admission.source_authority_ref,
            "source_authority_digest": admission.source_authority_digest,
            "request_ref": admission.request_ref,
            "request_digest": admission.request_digest,
            "operation_ref": admission.operation_ref,
            "operation_digest": admission.operation_digest,
            "invocation_digest": invocation.digest.value,
            "profile_digest": invocation.profile_digest.value,
            "terminal_status": result.status.value,
            "result_digest": result_digest,
            "result_body_ref": result_body_ref,
            "result_body_digest": result_body_digest,
            "result_body_size_bytes": result_body_size_bytes,
            "candidate": candidate,
            "transition_digest": transition_digest,
            "effect_digest": effect_digest,
            "outputs": outputs,
            "semantic_bodies": ordered_bodies,
            "output_activation": output_activation,
        }
        payload = _head_payload(values)
        return cls(
            package_ref=admission.package_ref,
            package_kind=admission.package_kind,
            manifest_digest=admission.manifest_digest,
            source_authority_ref=admission.source_authority_ref,
            source_authority_digest=admission.source_authority_digest,
            request_ref=admission.request_ref,
            request_digest=admission.request_digest,
            operation_ref=admission.operation_ref,
            operation_digest=admission.operation_digest,
            invocation_digest=invocation.digest.value,
            profile_digest=invocation.profile_digest.value,
            terminal_status=result.status.value,
            result_digest=result_digest,
            result_body_ref=result_body_ref,
            result_body_digest=result_body_digest,
            result_body_size_bytes=result_body_size_bytes,
            candidate=candidate,
            transition_digest=transition_digest,
            effect_digest=effect_digest,
            outputs=outputs,
            semantic_bodies=ordered_bodies,
            output_activation=output_activation,
            head_digest=_semantic_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD, payload
            ),
        )

    def _payload(self) -> dict[str, object]:
        return _head_payload(
            {
                "package_ref": self.package_ref,
                "package_kind": self.package_kind,
                "manifest_digest": self.manifest_digest,
                "source_authority_ref": self.source_authority_ref,
                "source_authority_digest": self.source_authority_digest,
                "request_ref": self.request_ref,
                "request_digest": self.request_digest,
                "operation_ref": self.operation_ref,
                "operation_digest": self.operation_digest,
                "invocation_digest": self.invocation_digest,
                "profile_digest": self.profile_digest,
                "terminal_status": self.terminal_status,
                "result_digest": self.result_digest,
                "result_body_ref": self.result_body_ref,
                "result_body_digest": self.result_body_digest,
                "result_body_size_bytes": self.result_body_size_bytes,
                "candidate": self.candidate,
                "transition_digest": self.transition_digest,
                "effect_digest": self.effect_digest,
                "outputs": self.outputs,
                "semantic_bodies": self.semantic_bodies,
                "output_activation": self.output_activation,
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
    def from_dict(cls, value: object) -> WorkspaceSemanticMaterializationHead:
        payload = _object(
            value,
            {
                "contract",
                "authority_grade",
                "package_ref",
                "package_kind",
                "manifest_digest",
                "source_authority_ref",
                "source_authority_digest",
                "request_ref",
                "request_digest",
                "operation_ref",
                "operation_digest",
                "invocation_digest",
                "profile_digest",
                "terminal_status",
                "result_digest",
                "result_body_ref",
                "result_body_digest",
                "result_body_size_bytes",
                "candidate",
                "transition_digest",
                "effect_digest",
                "outputs",
                "semantic_bodies",
                "output_activation",
                "head_digest",
                "non_claims",
            },
            "semantic materialization head",
        )
        return cls(
            package_ref=_string(payload["package_ref"], "package_ref"),
            package_kind=_string(payload["package_kind"], "package_kind"),
            manifest_digest=_string(payload["manifest_digest"], "manifest_digest"),
            source_authority_ref=_string(
                payload["source_authority_ref"], "source_authority_ref"
            ),
            source_authority_digest=_string(
                payload["source_authority_digest"], "source_authority_digest"
            ),
            request_ref=_string(payload["request_ref"], "request_ref"),
            request_digest=_string(payload["request_digest"], "request_digest"),
            operation_ref=_string(payload["operation_ref"], "operation_ref"),
            operation_digest=_string(payload["operation_digest"], "operation_digest"),
            invocation_digest=_string(
                payload["invocation_digest"], "invocation_digest"
            ),
            profile_digest=_string(payload["profile_digest"], "profile_digest"),
            terminal_status=_string(payload["terminal_status"], "terminal_status"),
            result_digest=_string(payload["result_digest"], "result_digest"),
            result_body_ref=_string(payload["result_body_ref"], "result_body_ref"),
            result_body_digest=_string(
                payload["result_body_digest"], "result_body_digest"
            ),
            result_body_size_bytes=_integer(
                payload["result_body_size_bytes"], "result_body_size_bytes"
            ),
            candidate=WorkspacePublishedSemanticCoordinate.from_dict(
                payload["candidate"]
            ),
            transition_digest=_optional_string(
                payload["transition_digest"], "transition_digest"
            ),
            effect_digest=_string(payload["effect_digest"], "effect_digest"),
            outputs=tuple(
                WorkspacePublishedSemanticCoordinate.from_dict(item)
                for item in _list(payload["outputs"], "outputs")
            ),
            semantic_bodies=tuple(
                WorkspaceStagedSemanticBody.from_dict(item)
                for item in _list(payload["semantic_bodies"], "semantic_bodies")
            ),
            output_activation=_string(
                payload["output_activation"], "output_activation"
            ),
            head_digest=_string(payload["head_digest"], "head_digest"),
            contract=_string(payload["contract"], "contract"),
            authority_grade=_string(payload["authority_grade"], "authority_grade"),
            non_claims=tuple(
                _string(item, "non_claim")
                for item in _list(payload["non_claims"], "non_claims")
            ),
        )


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationPublicationReceipt:
    head: WorkspaceSemanticMaterializationHead
    observed_result_digest: str
    observed_result_body_ref: str
    observed_result_body_digest: str
    observed_semantic_bodies: tuple[WorkspaceStagedSemanticBody, ...]
    prior_head_revision: int
    head_revision: int
    head_advanced: bool
    receipt_digest: str
    contract: str = WORKSPACE_SEMANTIC_MATERIALIZATION_RECEIPT

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_SEMANTIC_MATERIALIZATION_RECEIPT:
            raise WorkspaceSemanticMaterializationPublicationError(
                "publication receipt contract unsupported"
            )
        if type(self.head) is not WorkspaceSemanticMaterializationHead:
            raise TypeError("receipt head must be exact Workspace head")
        self.head.__post_init__()
        for field in ("observed_result_digest", "observed_result_body_digest"):
            object.__setattr__(self, field, _digest(getattr(self, field), field))
        object.__setattr__(
            self,
            "observed_result_body_ref",
            _token(self.observed_result_body_ref, "observed_result_body_ref"),
        )
        bodies = _exact_tuple(
            self.observed_semantic_bodies,
            WorkspaceStagedSemanticBody,
            "observed_semantic_bodies",
        )
        if bodies != tuple(sorted(set(bodies))):
            raise WorkspaceSemanticMaterializationPublicationError(
                "receipt semantic bodies must be unique and ordered"
            )
        _nonnegative_int(self.prior_head_revision, "prior_head_revision")
        _nonnegative_int(self.head_revision, "head_revision")
        if type(self.head_advanced) is not bool:
            raise TypeError("head_advanced must be exact bool")
        if self.head_advanced:
            if self.head_revision != self.prior_head_revision + 1:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "advanced receipt revision is not contiguous"
                )
        elif self.head_revision != self.prior_head_revision:
            raise WorkspaceSemanticMaterializationPublicationError(
                "current receipt changed the head revision"
            )
        expected = _semantic_digest(self.contract, self._payload())
        if self.receipt_digest != expected:
            raise WorkspaceSemanticMaterializationPublicationError(
                "publication receipt digest mismatched"
            )

    @classmethod
    def create(
        cls,
        *,
        head: WorkspaceSemanticMaterializationHead,
        observed_result_digest: str,
        observed_result_body_ref: str,
        observed_result_body_digest: str,
        observed_semantic_bodies: tuple[WorkspaceStagedSemanticBody, ...],
        prior_head_revision: int,
        head_revision: int,
        head_advanced: bool,
    ) -> WorkspaceSemanticMaterializationPublicationReceipt:
        ordered_bodies = tuple(sorted(observed_semantic_bodies))
        values: dict[str, object] = {
            "head": head,
            "observed_result_digest": observed_result_digest,
            "observed_result_body_ref": observed_result_body_ref,
            "observed_result_body_digest": observed_result_body_digest,
            "observed_semantic_bodies": ordered_bodies,
            "prior_head_revision": prior_head_revision,
            "head_revision": head_revision,
            "head_advanced": head_advanced,
        }
        payload = _receipt_payload(values)
        return cls(
            head=head,
            observed_result_digest=observed_result_digest,
            observed_result_body_ref=observed_result_body_ref,
            observed_result_body_digest=observed_result_body_digest,
            observed_semantic_bodies=ordered_bodies,
            prior_head_revision=prior_head_revision,
            head_revision=head_revision,
            head_advanced=head_advanced,
            receipt_digest=_semantic_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_RECEIPT, payload
            ),
        )

    def _payload(self) -> dict[str, object]:
        return _receipt_payload(
            {
                "head": self.head,
                "observed_result_digest": self.observed_result_digest,
                "observed_result_body_ref": self.observed_result_body_ref,
                "observed_result_body_digest": self.observed_result_body_digest,
                "observed_semantic_bodies": self.observed_semantic_bodies,
                "prior_head_revision": self.prior_head_revision,
                "head_revision": self.head_revision,
                "head_advanced": self.head_advanced,
            }
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            **self._payload(),
            "receipt_digest": self.receipt_digest,
        }


def _v2_exact(value: object, expected: type[object], field: str) -> object:
    if type(value) is not expected:
        raise TypeError(f"{field} must be exact {expected.__name__}")
    return value


def _v2_content_digest(value: object, field: str) -> ContentDigest:
    return cast(ContentDigest, _v2_exact(value, ContentDigest, field))


def _v2_digest(contract: str, payload: object) -> ContentDigest:
    return ContentDigest.of_bytes(
        canonical_json_bytes({"contract": contract, "value": payload})
    )


_TRUSTED_V2_JSON_ENCODER = json.JSONEncoder(
    ensure_ascii=False,
    allow_nan=False,
    sort_keys=True,
    separators=(",", ":"),
)


def _trusted_v2_json_bytes(value: object) -> bytes:
    """Encode a module-built exact wire after its public inputs were admitted."""

    return _TRUSTED_V2_JSON_ENCODER.encode(value).encode("utf-8")


def _v2_wire_digest(value: object, field: str) -> ContentDigest:
    del field
    return ContentDigest.of_bytes(
        canonical_json_bytes(cast(_V2PortableWire, value).to_wire())
    )


class _V2PortableWire(Protocol):
    def to_wire(self) -> dict[str, object]: ...


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationRequestV3:
    package: SemanticPackageCoordinate
    result_coordinate: SemanticValueCoordinate
    source_identity_digest: ContentDigest
    code_intent_digest: ContentDigest
    code_match_digest: ContentDigest
    planning_input_digest: ContentDigest
    execution_input_closure_digest: ContentDigest
    operation_result_digest: ContentDigest
    expected_head_revision: int
    request_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        package: SemanticPackageCoordinate,
        result_coordinate: SemanticValueCoordinate,
        source_identity_digest: ContentDigest,
        code_intent_digest: ContentDigest,
        code_match_digest: ContentDigest,
        planning_input_digest: ContentDigest,
        execution_input_closure_digest: ContentDigest,
        operation_result_digest: ContentDigest,
        expected_head_revision: int,
    ) -> WorkspaceSemanticMaterializationRequestV3:
        values = {
            "package": package,
            "result_coordinate": result_coordinate,
            "source_identity_digest": source_identity_digest,
            "code_intent_digest": code_intent_digest,
            "code_match_digest": code_match_digest,
            "planning_input_digest": planning_input_digest,
            "execution_input_closure_digest": execution_input_closure_digest,
            "operation_result_digest": operation_result_digest,
            "expected_head_revision": expected_head_revision,
        }
        payload = _publication_request_v2_payload(values)
        return cls(
            **values,
            request_digest=_v2_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_REQUEST_V3, payload
            ),
        )

    def __post_init__(self) -> None:
        payload = _publication_request_v2_payload(
            {
                name: getattr(self, name)
                for name in (
                    "package",
                    "result_coordinate",
                    "source_identity_digest",
                    "code_intent_digest",
                    "code_match_digest",
                    "planning_input_digest",
                    "execution_input_closure_digest",
                    "operation_result_digest",
                    "expected_head_revision",
                )
            }
        )
        if _v2_content_digest(
            self.request_digest, "request_v2.request_digest"
        ) != _v2_digest(WORKSPACE_SEMANTIC_MATERIALIZATION_REQUEST_V3, payload):
            raise WorkspaceSemanticMaterializationPublicationError(
                "publication request V2 digest mismatched"
            )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_REQUEST_V3,
            **_publication_request_v2_payload(
                {
                    name: getattr(self, name)
                    for name in (
                        "package",
                        "result_coordinate",
                        "source_identity_digest",
                        "code_intent_digest",
                        "code_match_digest",
                        "planning_input_digest",
                        "execution_input_closure_digest",
                        "operation_result_digest",
                        "expected_head_revision",
                    )
                }
            ),
            "request_digest": self.request_digest.to_wire(),
        }


def _publication_request_v2_payload(values: dict[str, object]) -> dict[str, object]:
    package = cast(
        SemanticPackageCoordinate,
        _v2_exact(values["package"], SemanticPackageCoordinate, "request_v2.package"),
    )
    coordinate = cast(
        SemanticValueCoordinate,
        _v2_exact(
            values["result_coordinate"],
            SemanticValueCoordinate,
            "request_v2.result_coordinate",
        ),
    )
    package.__post_init__()
    coordinate.__post_init__()
    return {
        "code_intent_digest": _v2_content_digest(
            values["code_intent_digest"], "request_v2.code_intent_digest"
        ).to_wire(),
        "code_match_digest": _v2_content_digest(
            values["code_match_digest"], "request_v2.code_match_digest"
        ).to_wire(),
        "planning_input_digest": _v2_content_digest(
            values["planning_input_digest"], "request_v2.planning_input_digest"
        ).to_wire(),
        "execution_input_closure_digest": _v2_content_digest(
            values["execution_input_closure_digest"],
            "request_v2.execution_input_closure_digest",
        ).to_wire(),
        "expected_head_revision": _nonnegative_int(
            values["expected_head_revision"], "request_v2.expected_head_revision"
        ),
        "operation_result_digest": _v2_content_digest(
            values["operation_result_digest"], "request_v2.operation_result_digest"
        ).to_wire(),
        "package": package.to_wire(),
        "result_coordinate": coordinate.to_wire(),
        "source_identity_digest": _v2_content_digest(
            values["source_identity_digest"], "request_v2.source_identity_digest"
        ).to_wire(),
    }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationHeadV3:
    request: WorkspaceSemanticMaterializationRequestV3
    package: SemanticPackageCoordinate
    result_coordinate: SemanticValueCoordinate
    source_identity_digest: ContentDigest
    code_intent_digest: ContentDigest
    code_match_digest: ContentDigest
    planning_input_digest: ContentDigest
    execution_input_closure_digest: ContentDigest
    operation_result_digest: ContentDigest
    head_digest: ContentDigest

    @classmethod
    def create(
        cls, *, request: WorkspaceSemanticMaterializationRequestV3
    ) -> WorkspaceSemanticMaterializationHeadV3:
        admitted = cast(
            WorkspaceSemanticMaterializationRequestV3,
            _v2_exact(
                request, WorkspaceSemanticMaterializationRequestV3, "head_v2.request"
            ),
        )
        admitted.__post_init__()
        values = {
            "request": admitted,
            "package": admitted.package,
            "result_coordinate": admitted.result_coordinate,
            "source_identity_digest": admitted.source_identity_digest,
            "code_intent_digest": admitted.code_intent_digest,
            "code_match_digest": admitted.code_match_digest,
            "planning_input_digest": admitted.planning_input_digest,
            "execution_input_closure_digest": admitted.execution_input_closure_digest,
            "operation_result_digest": admitted.operation_result_digest,
        }
        payload = _publication_head_v2_payload(values)
        return cls(
            **values,
            head_digest=_v2_digest(WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V3, payload),
        )

    def __post_init__(self) -> None:
        values = {
            name: getattr(self, name)
            for name in (
                "request",
                "package",
                "result_coordinate",
                "source_identity_digest",
                "code_intent_digest",
                "code_match_digest",
                "planning_input_digest",
                "execution_input_closure_digest",
                "operation_result_digest",
            )
        }
        payload = _publication_head_v2_payload(values)
        if _v2_content_digest(self.head_digest, "head_v2.head_digest") != _v2_digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V3, payload
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "publication head V2 digest mismatched"
            )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V3,
            **_publication_head_v2_payload(
                {
                    name: getattr(self, name)
                    for name in (
                        "request",
                        "package",
                        "result_coordinate",
                        "source_identity_digest",
                        "code_intent_digest",
                        "code_match_digest",
                        "planning_input_digest",
                        "execution_input_closure_digest",
                        "operation_result_digest",
                    )
                }
            ),
            "head_digest": self.head_digest.to_wire(),
        }


def _publication_head_v2_payload(values: dict[str, object]) -> dict[str, object]:
    request = cast(
        WorkspaceSemanticMaterializationRequestV3,
        _v2_exact(
            values["request"],
            WorkspaceSemanticMaterializationRequestV3,
            "head_v2.request",
        ),
    )
    package = cast(
        SemanticPackageCoordinate,
        _v2_exact(values["package"], SemanticPackageCoordinate, "head_v2.package"),
    )
    coordinate = cast(
        SemanticValueCoordinate,
        _v2_exact(
            values["result_coordinate"],
            SemanticValueCoordinate,
            "head_v2.result_coordinate",
        ),
    )
    request.__post_init__()
    package.__post_init__()
    coordinate.__post_init__()
    duplicated = (
        canonical_json_bytes(package.to_wire())
        == canonical_json_bytes(request.package.to_wire())
        and canonical_json_bytes(coordinate.to_wire())
        == canonical_json_bytes(request.result_coordinate.to_wire())
        and values["source_identity_digest"] == request.source_identity_digest
        and values["code_intent_digest"] == request.code_intent_digest
        and values["code_match_digest"] == request.code_match_digest
        and values["planning_input_digest"] == request.planning_input_digest
        and values["execution_input_closure_digest"]
        == request.execution_input_closure_digest
        and values["operation_result_digest"] == request.operation_result_digest
    )
    if not duplicated:
        raise WorkspaceSemanticMaterializationPublicationError(
            "publication head V2 differs from exact request"
        )
    return {
        "code_intent_digest": request.code_intent_digest.to_wire(),
        "code_match_digest": request.code_match_digest.to_wire(),
        "planning_input_digest": request.planning_input_digest.to_wire(),
        "execution_input_closure_digest": request.execution_input_closure_digest.to_wire(),
        "operation_result_digest": request.operation_result_digest.to_wire(),
        "package": package.to_wire(),
        "request": request.to_wire(),
        "result_coordinate": coordinate.to_wire(),
        "source_identity_digest": request.source_identity_digest.to_wire(),
    }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationOutputStateBindingV4:
    """One retained output state bound to an exact selected Code output."""

    output_coordinate: SemanticValueCoordinate
    output_state_name: str
    prior_state_body_ref: str
    prior_state_body_digest: ContentDigest
    prior_state_body_size: int
    prior_state_digest: ContentDigest
    state_body_ref: str
    state_body_digest: ContentDigest
    state_body_size: int
    state_digest: ContentDigest

    def __post_init__(self) -> None:
        coordinate = cast(
            SemanticValueCoordinate,
            _v2_exact(
                self.output_coordinate,
                SemanticValueCoordinate,
                "output binding coordinate",
            ),
        )
        coordinate.__post_init__()
        _token(self.output_state_name, "output_state_name")
        prior_body_digest = _v2_content_digest(
            self.prior_state_body_digest, "output binding prior body digest"
        )
        if self.prior_state_body_ref != _body_ref(prior_body_digest.value):
            raise WorkspaceSemanticMaterializationPublicationError(
                "output binding prior body ref differs from digest"
            )
        if (
            _nonnegative_int(
                self.prior_state_body_size, "output binding prior body size"
            )
            == 0
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "output binding prior body must be nonempty"
            )
        _v2_content_digest(self.prior_state_digest, "output binding prior state digest")
        body_digest = _v2_content_digest(
            self.state_body_digest, "output binding body digest"
        )
        if self.state_body_ref != _body_ref(body_digest.value):
            raise WorkspaceSemanticMaterializationPublicationError(
                "output binding body ref differs from digest"
            )
        if _nonnegative_int(self.state_body_size, "output binding body size") == 0:
            raise WorkspaceSemanticMaterializationPublicationError(
                "output binding body must be nonempty"
            )
        _v2_content_digest(self.state_digest, "output binding state digest")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_OUTPUT_STATE_BINDING_V4,
            "output_coordinate": self.output_coordinate.to_wire(),
            "output_state_name": self.output_state_name,
            "prior_state_body_ref": self.prior_state_body_ref,
            "prior_state_body_digest": self.prior_state_body_digest.to_wire(),
            "prior_state_body_size": self.prior_state_body_size,
            "prior_state_digest": self.prior_state_digest.to_wire(),
            "state_body_ref": self.state_body_ref,
            "state_body_digest": self.state_body_digest.to_wire(),
            "state_body_size": self.state_body_size,
            "state_digest": self.state_digest.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationPackageOccurrenceV4:
    """Stable source occurrence recorded with a state-bound package head.

    This detached value must be derived from the original Workspace source
    admission. It is not an issuer, membership proof, or source-currentness
    handle.
    """

    repository_ref: str
    workspace_ref: str
    module_ref: str
    package_id: str
    package_root: str
    manifest_relative_path: str

    def __post_init__(self) -> None:
        for field in (
            "repository_ref", "workspace_ref", "module_ref", "package_id",
            "package_root", "manifest_relative_path",
        ):
            value = getattr(self, field)
            if type(value) is not str or not value or value.strip() != value:
                raise WorkspaceSemanticMaterializationPublicationError(
                    f"package occurrence {field} must be exact nonempty text"
                )

    def to_wire(self) -> dict[str, str]:
        self.__post_init__()
        return {
            "repository_ref": self.repository_ref,
            "workspace_ref": self.workspace_ref,
            "module_ref": self.module_ref,
            "package_id": self.package_id,
            "package_root": self.package_root,
            "manifest_relative_path": self.manifest_relative_path,
        }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationHeadV4:
    """The V3 result and selected output state in one package-head value."""

    base_head: WorkspaceSemanticMaterializationHeadV3
    package_occurrence: WorkspaceMaterializationPackageOccurrenceV4
    predecessor_head_digest: ContentDigest | None
    operation_ref: str
    operation_digest: ContentDigest
    output_state_bindings: tuple[
        WorkspaceSemanticMaterializationOutputStateBindingV4, ...
    ]
    head_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        request: WorkspaceSemanticMaterializationRequestV3,
        package_occurrence: WorkspaceMaterializationPackageOccurrenceV4,
        predecessor_head_digest: ContentDigest | None = None,
        operation_ref: str,
        operation_digest: ContentDigest,
        output_state_bindings: tuple[
            WorkspaceSemanticMaterializationOutputStateBindingV4, ...
        ],
    ) -> WorkspaceSemanticMaterializationHeadV4:
        base_head = WorkspaceSemanticMaterializationHeadV3.create(request=request)
        payload = cls._payload(
            base_head=base_head,
            package_occurrence=package_occurrence,
            predecessor_head_digest=predecessor_head_digest,
            operation_ref=operation_ref,
            operation_digest=operation_digest,
            output_state_bindings=output_state_bindings,
        )
        return cls(
            base_head=base_head,
            package_occurrence=package_occurrence,
            predecessor_head_digest=predecessor_head_digest,
            operation_ref=operation_ref,
            operation_digest=operation_digest,
            output_state_bindings=output_state_bindings,
            head_digest=_v2_digest(WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4, payload),
        )

    @staticmethod
    def _payload(
        *,
        base_head: WorkspaceSemanticMaterializationHeadV3,
        package_occurrence: WorkspaceMaterializationPackageOccurrenceV4,
        predecessor_head_digest: ContentDigest | None,
        operation_ref: str,
        operation_digest: ContentDigest,
        output_state_bindings: tuple[
            WorkspaceSemanticMaterializationOutputStateBindingV4, ...
        ],
    ) -> dict[str, object]:
        base = cast(
            WorkspaceSemanticMaterializationHeadV3,
            _v2_exact(
                base_head, WorkspaceSemanticMaterializationHeadV3, "head V4 base"
            ),
        )
        base.__post_init__()
        if type(package_occurrence) is not WorkspaceMaterializationPackageOccurrenceV4:
            raise TypeError("exact Workspace package occurrence required")
        package_occurrence.__post_init__()
        if base.request.expected_head_revision == 0:
            if predecessor_head_digest is not None:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "V4 genesis cannot claim a predecessor head digest"
                )
        else:
            _v2_content_digest(
                predecessor_head_digest, "V4 predecessor head digest"
            )
        ref = _token(operation_ref, "head V4 operation ref")
        digest = _v2_content_digest(operation_digest, "head V4 operation digest")
        if (
            type(output_state_bindings) is not tuple
            or not output_state_bindings
            or any(
                type(item) is not WorkspaceSemanticMaterializationOutputStateBindingV4
                for item in output_state_bindings
            )
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "head V4 requires exact nonempty output bindings"
            )
        roles = tuple(item.output_coordinate.role for item in output_state_bindings)
        if roles != tuple(sorted(set(roles), key=str.encode)):
            raise WorkspaceSemanticMaterializationPublicationError(
                "head V4 output bindings must be ordered and role-unique"
            )
        return {
            "base_head": base.to_wire(),
            "package_occurrence": package_occurrence.to_wire(),
            "predecessor_head_digest": (
                None if predecessor_head_digest is None
                else predecessor_head_digest.to_wire()
            ),
            "operation_ref": ref,
            "operation_digest": digest.to_wire(),
            "output_state_bindings": [item.to_wire() for item in output_state_bindings],
        }

    def __post_init__(self) -> None:
        payload = self._payload(
            base_head=self.base_head,
            package_occurrence=self.package_occurrence,
            predecessor_head_digest=self.predecessor_head_digest,
            operation_ref=self.operation_ref,
            operation_digest=self.operation_digest,
            output_state_bindings=self.output_state_bindings,
        )
        if _v2_content_digest(self.head_digest, "head V4 digest") != _v2_digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4, payload
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "head V4 digest differs"
            )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4,
            **self._payload(
                base_head=self.base_head,
                package_occurrence=self.package_occurrence,
                predecessor_head_digest=self.predecessor_head_digest,
                operation_ref=self.operation_ref,
                operation_digest=self.operation_digest,
                output_state_bindings=self.output_state_bindings,
            ),
            "head_digest": self.head_digest.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationPublicationReceiptV4:
    """Detached evidence for one V4 package-head CAS, never its authority."""

    request: WorkspaceSemanticMaterializationRequestV3
    head: WorkspaceSemanticMaterializationHeadV4
    prior_head_revision: int
    head_revision: int
    head_advanced: bool
    canonical_head_wire_digest: ContentDigest
    receipt_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        request: WorkspaceSemanticMaterializationRequestV3,
        head: WorkspaceSemanticMaterializationHeadV4,
        prior_head_revision: int,
        head_revision: int,
        head_advanced: bool,
    ) -> WorkspaceSemanticMaterializationPublicationReceiptV4:
        values = {
            "request": request,
            "head": head,
            "prior_head_revision": prior_head_revision,
            "head_revision": head_revision,
            "head_advanced": head_advanced,
            "canonical_head_wire_digest": ContentDigest.of_bytes(
                canonical_json_bytes(head.to_wire())
            ),
        }
        payload = cls._payload(values)
        return cls(
            **values,
            receipt_digest=_v2_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_RECEIPT_V4, payload
            ),
        )

    @staticmethod
    def _payload(values: dict[str, object]) -> dict[str, object]:
        request = cast(
            WorkspaceSemanticMaterializationRequestV3,
            _v2_exact(
                values["request"],
                WorkspaceSemanticMaterializationRequestV3,
                "receipt V4 request",
            ),
        )
        head = cast(
            WorkspaceSemanticMaterializationHeadV4,
            _v2_exact(
                values["head"],
                WorkspaceSemanticMaterializationHeadV4,
                "receipt V4 head",
            ),
        )
        request.__post_init__()
        head.__post_init__()
        if canonical_json_bytes(head.base_head.request.to_wire()) != canonical_json_bytes(
            request.to_wire()
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "publication receipt V4 request differs from head"
            )
        prior = _nonnegative_int(values["prior_head_revision"], "receipt V4 prior")
        revision = _nonnegative_int(values["head_revision"], "receipt V4 revision")
        advanced = values["head_advanced"]
        if type(advanced) is not bool:
            raise TypeError("receipt V4 head_advanced must be exact bool")
        if (advanced and revision != prior + 1) or (not advanced and revision != prior):
            raise WorkspaceSemanticMaterializationPublicationError(
                "publication receipt V4 revision is not contiguous"
            )
        wire_digest = _v2_content_digest(
            values["canonical_head_wire_digest"], "receipt V4 head wire digest"
        )
        if wire_digest != ContentDigest.of_bytes(canonical_json_bytes(head.to_wire())):
            raise WorkspaceSemanticMaterializationPublicationError(
                "publication receipt V4 head wire digest differs"
            )
        return {
            "request": request.to_wire(),
            "head": head.to_wire(),
            "prior_head_revision": prior,
            "head_revision": revision,
            "head_advanced": advanced,
            "canonical_head_wire_digest": wire_digest.to_wire(),
        }

    def __post_init__(self) -> None:
        payload = self._payload(
            {
                name: getattr(self, name)
                for name in (
                    "request",
                    "head",
                    "prior_head_revision",
                    "head_revision",
                    "head_advanced",
                    "canonical_head_wire_digest",
                )
            }
        )
        if _v2_content_digest(self.receipt_digest, "receipt V4 digest") != _v2_digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_RECEIPT_V4, payload
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "publication receipt V4 digest differs"
            )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_RECEIPT_V4,
            **self._payload(
                {
                    name: getattr(self, name)
                    for name in (
                        "request",
                        "head",
                        "prior_head_revision",
                        "head_revision",
                        "head_advanced",
                        "canonical_head_wire_digest",
                    )
                }
            ),
            "receipt_digest": self.receipt_digest.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationHeadRereadEvidenceV4:
    """Detached observation of the actual V4 head and its stored revision."""

    observation_role: str
    materialization_head_revision: int
    head: WorkspaceSemanticMaterializationHeadV4
    materialization_head_digest: ContentDigest
    canonical_head_wire_digest: ContentDigest
    reread_evidence_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        observation_role: str,
        materialization_head_revision: int,
        head: WorkspaceSemanticMaterializationHeadV4,
    ) -> WorkspaceSemanticMaterializationHeadRereadEvidenceV4:
        values = {
            "observation_role": observation_role,
            "materialization_head_revision": materialization_head_revision,
            "head": head,
            "materialization_head_digest": head.head_digest,
            "canonical_head_wire_digest": ContentDigest.of_bytes(
                canonical_json_bytes(head.to_wire())
            ),
        }
        payload = cls._payload(values)
        return cls(
            **values,
            reread_evidence_digest=_v2_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_REREAD_EVIDENCE_V4,
                payload,
            ),
        )

    @staticmethod
    def _payload(values: dict[str, object]) -> dict[str, object]:
        role = _token(values["observation_role"], "head reread V4 role")
        if role not in {
            "dependency_h1",
            "dependency_h2",
            "package_result",
            "package_reuse",
        }:
            raise WorkspaceSemanticMaterializationPublicationError(
                "head reread V4 observation role unsupported"
            )
        revision = _nonnegative_int(
            values["materialization_head_revision"], "head reread V4 revision"
        )
        head = cast(
            WorkspaceSemanticMaterializationHeadV4,
            _v2_exact(
                values["head"],
                WorkspaceSemanticMaterializationHeadV4,
                "head reread V4 head",
            ),
        )
        head.__post_init__()
        digest = _v2_content_digest(
            values["materialization_head_digest"], "head reread V4 head digest"
        )
        wire_digest = _v2_content_digest(
            values["canonical_head_wire_digest"], "head reread V4 wire digest"
        )
        if digest != head.head_digest or wire_digest != ContentDigest.of_bytes(
            canonical_json_bytes(head.to_wire())
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "head reread V4 differs from actual head"
            )
        return {
            "observation_role": role,
            "materialization_head_revision": revision,
            "head": head.to_wire(),
            "materialization_head_digest": digest.to_wire(),
            "canonical_head_wire_digest": wire_digest.to_wire(),
        }

    def __post_init__(self) -> None:
        payload = self._payload(
            {
                name: getattr(self, name)
                for name in (
                    "observation_role",
                    "materialization_head_revision",
                    "head",
                    "materialization_head_digest",
                    "canonical_head_wire_digest",
                )
            }
        )
        if _v2_content_digest(
            self.reread_evidence_digest, "head reread V4 evidence digest"
        ) != _v2_digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_REREAD_EVIDENCE_V4, payload
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "head reread V4 evidence digest differs"
            )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_REREAD_EVIDENCE_V4,
            **self._payload(
                {
                    name: getattr(self, name)
                    for name in (
                        "observation_role",
                        "materialization_head_revision",
                        "head",
                        "materialization_head_digest",
                        "canonical_head_wire_digest",
                    )
                }
            ),
            "reread_evidence_digest": self.reread_evidence_digest.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationPublicationReceiptV3:
    request: WorkspaceSemanticMaterializationRequestV3
    head: WorkspaceSemanticMaterializationHeadV3
    prior_head_revision: int
    head_revision: int
    head_advanced: bool
    canonical_head_wire_digest: ContentDigest
    receipt_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        request: WorkspaceSemanticMaterializationRequestV3,
        head: WorkspaceSemanticMaterializationHeadV3,
        prior_head_revision: int,
        head_revision: int,
        head_advanced: bool,
    ) -> WorkspaceSemanticMaterializationPublicationReceiptV3:
        exact_request = cast(
            WorkspaceSemanticMaterializationRequestV3,
            _v2_exact(
                request,
                WorkspaceSemanticMaterializationRequestV3,
                "receipt_v2.request",
            ),
        )
        exact_head = cast(
            WorkspaceSemanticMaterializationHeadV3,
            _v2_exact(head, WorkspaceSemanticMaterializationHeadV3, "receipt_v2.head"),
        )
        values = {
            "request": exact_request,
            "head": exact_head,
            "prior_head_revision": prior_head_revision,
            "head_revision": head_revision,
            "head_advanced": head_advanced,
            "canonical_head_wire_digest": _v2_wire_digest(
                exact_head, "receipt_v2.head"
            ),
        }
        payload = _publication_receipt_v2_payload(values)
        return cls(
            **values,
            receipt_digest=_v2_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_RECEIPT_V3, payload
            ),
        )

    def __post_init__(self) -> None:
        values = {
            name: getattr(self, name)
            for name in (
                "request",
                "head",
                "prior_head_revision",
                "head_revision",
                "head_advanced",
                "canonical_head_wire_digest",
            )
        }
        payload = _publication_receipt_v2_payload(values)
        if _v2_content_digest(
            self.receipt_digest, "receipt_v2.receipt_digest"
        ) != _v2_digest(WORKSPACE_SEMANTIC_MATERIALIZATION_RECEIPT_V3, payload):
            raise WorkspaceSemanticMaterializationPublicationError(
                "publication receipt V2 digest mismatched"
            )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_RECEIPT_V3,
            **_publication_receipt_v2_payload(
                {
                    name: getattr(self, name)
                    for name in (
                        "request",
                        "head",
                        "prior_head_revision",
                        "head_revision",
                        "head_advanced",
                        "canonical_head_wire_digest",
                    )
                }
            ),
            "receipt_digest": self.receipt_digest.to_wire(),
        }


def _publication_receipt_v2_payload(values: dict[str, object]) -> dict[str, object]:
    request = cast(
        WorkspaceSemanticMaterializationRequestV3,
        _v2_exact(
            values["request"],
            WorkspaceSemanticMaterializationRequestV3,
            "receipt_v2.request",
        ),
    )
    head = cast(
        WorkspaceSemanticMaterializationHeadV3,
        _v2_exact(
            values["head"], WorkspaceSemanticMaterializationHeadV3, "receipt_v2.head"
        ),
    )
    request.__post_init__()
    head.__post_init__()
    if canonical_json_bytes(head.request.to_wire()) != canonical_json_bytes(
        request.to_wire()
    ):
        raise WorkspaceSemanticMaterializationPublicationError(
            "publication receipt V2 request differs from head"
        )
    prior = _nonnegative_int(
        values["prior_head_revision"], "receipt_v2.prior_head_revision"
    )
    revision = _nonnegative_int(values["head_revision"], "receipt_v2.head_revision")
    advanced = values["head_advanced"]
    if type(advanced) is not bool:
        raise TypeError("receipt_v2.head_advanced must be exact bool")
    if (advanced and revision != prior + 1) or (not advanced and revision != prior):
        raise WorkspaceSemanticMaterializationPublicationError(
            "publication receipt V2 revision is not contiguous"
        )
    wire_digest = _v2_content_digest(
        values["canonical_head_wire_digest"], "receipt_v2.canonical_head_wire_digest"
    )
    if wire_digest != _v2_wire_digest(head, "receipt_v2.head"):
        raise WorkspaceSemanticMaterializationPublicationError(
            "publication receipt V2 head wire digest differs"
        )
    return {
        "canonical_head_wire_digest": wire_digest.to_wire(),
        "head": head.to_wire(),
        "head_advanced": advanced,
        "head_revision": revision,
        "prior_head_revision": prior,
        "request": request.to_wire(),
    }


def _validated_head_v2_wire(
    head: WorkspaceSemanticMaterializationHeadV3,
) -> dict[str, object]:
    """Wire one already freshly validated V2 head without recursive re-entry."""

    def digest_wire(value: ContentDigest) -> str:
        return value.value

    def contract_wire(value: SemanticContractRef) -> dict[str, object]:
        return {
            "key": value.key,
            "schema_digest": digest_wire(value.schema_digest),
            "version": value.version,
        }

    def package_wire(value: SemanticPackageCoordinate) -> dict[str, object]:
        return {
            "manifest_digest": digest_wire(value.manifest_digest),
            "package_kind": value.package_kind,
            "package_ref": value.package_ref,
        }

    def coordinate_wire(value: SemanticValueCoordinate) -> dict[str, object]:
        return {
            "contract": contract_wire(value.contract),
            "digest": digest_wire(value.digest),
            "role": value.role,
            "size_bytes": value.size_bytes,
            "value_ref": value.value_ref,
        }

    request = head.request
    request_wire = {
        "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_REQUEST_V3,
        "code_intent_digest": digest_wire(request.code_intent_digest),
        "code_match_digest": digest_wire(request.code_match_digest),
        "planning_input_digest": digest_wire(request.planning_input_digest),
        "execution_input_closure_digest": digest_wire(
            request.execution_input_closure_digest
        ),
        "expected_head_revision": request.expected_head_revision,
        "operation_result_digest": digest_wire(request.operation_result_digest),
        "package": package_wire(request.package),
        "request_digest": digest_wire(request.request_digest),
        "result_coordinate": coordinate_wire(request.result_coordinate),
        "source_identity_digest": digest_wire(request.source_identity_digest),
    }
    return {
        "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V3,
        "code_intent_digest": digest_wire(head.code_intent_digest),
        "code_match_digest": digest_wire(head.code_match_digest),
        "planning_input_digest": digest_wire(head.planning_input_digest),
        "execution_input_closure_digest": digest_wire(
            head.execution_input_closure_digest
        ),
        "head_digest": digest_wire(head.head_digest),
        "operation_result_digest": digest_wire(head.operation_result_digest),
        "package": package_wire(head.package),
        "request": request_wire,
        "result_coordinate": coordinate_wire(head.result_coordinate),
        "source_identity_digest": digest_wire(head.source_identity_digest),
    }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationHeadRereadEvidenceV3:
    observation_role: str
    materialization_head_revision: int
    head: WorkspaceSemanticMaterializationHeadV3
    package: SemanticPackageCoordinate
    result_coordinate: SemanticValueCoordinate
    source_identity_digest: ContentDigest
    code_intent_digest: ContentDigest
    code_match_digest: ContentDigest
    planning_input_digest: ContentDigest
    execution_input_closure_digest: ContentDigest
    materialization_head_digest: ContentDigest
    canonical_head_wire_digest: ContentDigest
    reread_evidence_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        observation_role: str,
        materialization_head_revision: int,
        head: WorkspaceSemanticMaterializationHeadV3,
    ) -> WorkspaceSemanticMaterializationHeadRereadEvidenceV3:
        exact_head = cast(
            WorkspaceSemanticMaterializationHeadV3,
            _v2_exact(
                head, WorkspaceSemanticMaterializationHeadV3, "head_reread_v2.head"
            ),
        )
        exact_head.__post_init__()
        role = _token(observation_role, "head_reread_v2.observation_role")
        if role not in {
            "dependency_h1",
            "dependency_h2",
            "package_result",
            "package_reuse",
        }:
            raise WorkspaceSemanticMaterializationPublicationError(
                "head reread V2 observation role unsupported"
            )
        revision = _nonnegative_int(
            materialization_head_revision,
            "head_reread_v2.materialization_head_revision",
        )
        canonical_head_wire_digest = ContentDigest.of_bytes(
            canonical_json_bytes(_validated_head_v2_wire(exact_head))
        )
        values = {
            "observation_role": role,
            "materialization_head_revision": revision,
            "head": exact_head,
            "package": exact_head.package,
            "result_coordinate": exact_head.result_coordinate,
            "source_identity_digest": exact_head.source_identity_digest,
            "code_intent_digest": exact_head.code_intent_digest,
            "code_match_digest": exact_head.code_match_digest,
            "planning_input_digest": exact_head.planning_input_digest,
            "execution_input_closure_digest": exact_head.execution_input_closure_digest,
            "materialization_head_digest": exact_head.head_digest,
            "canonical_head_wire_digest": canonical_head_wire_digest,
        }
        payload = {
            "canonical_head_wire_digest": canonical_head_wire_digest.to_wire(),
            "code_intent_digest": exact_head.code_intent_digest.to_wire(),
            "code_match_digest": exact_head.code_match_digest.to_wire(),
            "planning_input_digest": exact_head.planning_input_digest.to_wire(),
            "execution_input_closure_digest": exact_head.execution_input_closure_digest.to_wire(),
            "head": _validated_head_v2_wire(exact_head),
            "materialization_head_digest": exact_head.head_digest.to_wire(),
            "materialization_head_revision": revision,
            "observation_role": role,
            "package": exact_head.package.to_wire(),
            "result_coordinate": exact_head.result_coordinate.to_wire(),
            "source_identity_digest": exact_head.source_identity_digest.to_wire(),
        }
        return cls(
            **values,
            reread_evidence_digest=_v2_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_REREAD_EVIDENCE_V3, payload
            ),
        )

    def __post_init__(self) -> None:
        values = {
            name: getattr(self, name)
            for name in (
                "observation_role",
                "materialization_head_revision",
                "head",
                "package",
                "result_coordinate",
                "source_identity_digest",
                "code_intent_digest",
                "code_match_digest",
                "planning_input_digest",
                "execution_input_closure_digest",
                "materialization_head_digest",
                "canonical_head_wire_digest",
            )
        }
        payload = _head_reread_v2_payload(values)
        if _v2_content_digest(
            self.reread_evidence_digest, "head_reread_v2.reread_evidence_digest"
        ) != _v2_digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_REREAD_EVIDENCE_V3, payload
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "head reread V2 digest mismatched"
            )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_REREAD_EVIDENCE_V3,
            **_head_reread_v2_payload(
                {
                    name: getattr(self, name)
                    for name in (
                        "observation_role",
                        "materialization_head_revision",
                        "head",
                        "package",
                        "result_coordinate",
                        "source_identity_digest",
                        "code_intent_digest",
                        "code_match_digest",
                        "planning_input_digest",
                        "execution_input_closure_digest",
                        "materialization_head_digest",
                        "canonical_head_wire_digest",
                    )
                }
            ),
            "reread_evidence_digest": self.reread_evidence_digest.to_wire(),
        }


def _create_head_reread_v2_from_validated_head(
    *,
    observation_role: str,
    materialization_head_revision: int,
    head: WorkspaceSemanticMaterializationHeadV3,
) -> WorkspaceSemanticMaterializationHeadRereadEvidenceV3:
    """Derive evidence from a head freshly authenticated by the resident reader."""

    role = _token(observation_role, "head_reread_v2.observation_role")
    if role not in {
        "dependency_h1",
        "dependency_h2",
        "package_result",
        "package_reuse",
    }:
        raise WorkspaceSemanticMaterializationPublicationError(
            "head reread V2 observation role unsupported"
        )
    revision = _nonnegative_int(
        materialization_head_revision,
        "head_reread_v2.materialization_head_revision",
    )
    head_wire = _validated_head_v2_wire(head)
    canonical_head_wire_digest = ContentDigest.of_bytes(
        _trusted_v2_json_bytes(head_wire)
    )
    values = {
        "observation_role": role,
        "materialization_head_revision": revision,
        "head": head,
        "package": head.package,
        "result_coordinate": head.result_coordinate,
        "source_identity_digest": head.source_identity_digest,
        "code_intent_digest": head.code_intent_digest,
        "code_match_digest": head.code_match_digest,
        "planning_input_digest": head.planning_input_digest,
        "execution_input_closure_digest": head.execution_input_closure_digest,
        "materialization_head_digest": head.head_digest,
        "canonical_head_wire_digest": canonical_head_wire_digest,
    }
    payload = {
        "canonical_head_wire_digest": canonical_head_wire_digest.to_wire(),
        "code_intent_digest": head.code_intent_digest.to_wire(),
        "code_match_digest": head.code_match_digest.to_wire(),
        "planning_input_digest": head.planning_input_digest.to_wire(),
        "execution_input_closure_digest": head.execution_input_closure_digest.to_wire(),
        "head": head_wire,
        "materialization_head_digest": head.head_digest.to_wire(),
        "materialization_head_revision": revision,
        "observation_role": role,
        "package": head.package.to_wire(),
        "result_coordinate": head.result_coordinate.to_wire(),
        "source_identity_digest": head.source_identity_digest.to_wire(),
    }
    result = object.__new__(WorkspaceSemanticMaterializationHeadRereadEvidenceV3)
    for name, value in values.items():
        object.__setattr__(result, name, value)
    object.__setattr__(
        result,
        "reread_evidence_digest",
        ContentDigest.of_bytes(
            _trusted_v2_json_bytes(
                {
                    "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_REREAD_EVIDENCE_V3,
                    "value": payload,
                }
            )
        ),
    )
    return result


def _head_reread_v2_payload(values: dict[str, object]) -> dict[str, object]:
    role = _token(values["observation_role"], "head_reread_v2.observation_role")
    if role not in {
        "dependency_h1",
        "dependency_h2",
        "package_result",
        "package_reuse",
    }:
        raise WorkspaceSemanticMaterializationPublicationError(
            "head reread V2 observation role unsupported"
        )
    head = cast(
        WorkspaceSemanticMaterializationHeadV3,
        _v2_exact(
            values["head"],
            WorkspaceSemanticMaterializationHeadV3,
            "head_reread_v2.head",
        ),
    )
    package = cast(
        SemanticPackageCoordinate,
        _v2_exact(
            values["package"], SemanticPackageCoordinate, "head_reread_v2.package"
        ),
    )
    coordinate = cast(
        SemanticValueCoordinate,
        _v2_exact(
            values["result_coordinate"],
            SemanticValueCoordinate,
            "head_reread_v2.result_coordinate",
        ),
    )
    head.__post_init__()
    package.__post_init__()
    coordinate.__post_init__()
    duplicated = (
        canonical_json_bytes(package.to_wire())
        == canonical_json_bytes(head.package.to_wire())
        and canonical_json_bytes(coordinate.to_wire())
        == canonical_json_bytes(head.result_coordinate.to_wire())
        and values["source_identity_digest"] == head.source_identity_digest
        and values["code_intent_digest"] == head.code_intent_digest
        and values["code_match_digest"] == head.code_match_digest
        and values["planning_input_digest"] == head.planning_input_digest
        and values["execution_input_closure_digest"]
        == head.execution_input_closure_digest
        and values["materialization_head_digest"] == head.head_digest
        and values["canonical_head_wire_digest"]
        == _v2_wire_digest(head, "head_reread_v2.head")
    )
    if not duplicated:
        raise WorkspaceSemanticMaterializationPublicationError(
            "head reread V2 differs from exact publication head"
        )
    return {
        "canonical_head_wire_digest": cast(
            ContentDigest, values["canonical_head_wire_digest"]
        ).to_wire(),
        "code_intent_digest": head.code_intent_digest.to_wire(),
        "code_match_digest": head.code_match_digest.to_wire(),
        "planning_input_digest": head.planning_input_digest.to_wire(),
        "execution_input_closure_digest": head.execution_input_closure_digest.to_wire(),
        "head": head.to_wire(),
        "materialization_head_digest": head.head_digest.to_wire(),
        "materialization_head_revision": _nonnegative_int(
            values["materialization_head_revision"],
            "head_reread_v2.materialization_head_revision",
        ),
        "observation_role": role,
        "package": package.to_wire(),
        "result_coordinate": coordinate.to_wire(),
        "source_identity_digest": head.source_identity_digest.to_wire(),
    }


def _encode_v2_exact(value: object, expected: type[object], field: str) -> bytes:
    exact = _v2_exact(value, expected, field)
    return canonical_json_bytes(cast(_V2PortableWire, exact).to_wire())


def _decode_v2_expected(
    wire: bytes, expected_value: object, expected_type: type[object], field: str
) -> object:
    if type(wire) is not bytes:
        raise TypeError(f"{field} wire must be exact bytes")
    if _encode_v2_exact(expected_value, expected_type, field) != wire:
        raise WorkspaceSemanticMaterializationPublicationError(
            f"{field} wire is not canonical for expected context"
        )
    return expected_value


def encode_workspace_semantic_materialization_request_v2(
    value: WorkspaceSemanticMaterializationRequestV3,
) -> bytes:
    return _encode_v2_exact(
        value, WorkspaceSemanticMaterializationRequestV3, "request_v2"
    )


def decode_workspace_semantic_materialization_request_v2(
    wire: bytes, *, expected: WorkspaceSemanticMaterializationRequestV3
) -> WorkspaceSemanticMaterializationRequestV3:
    return cast(
        WorkspaceSemanticMaterializationRequestV3,
        _decode_v2_expected(
            wire, expected, WorkspaceSemanticMaterializationRequestV3, "request_v2"
        ),
    )


def encode_workspace_semantic_materialization_head_v2(
    value: WorkspaceSemanticMaterializationHeadV3,
) -> bytes:
    return _encode_v2_exact(value, WorkspaceSemanticMaterializationHeadV3, "head_v2")


def decode_workspace_semantic_materialization_head_v2(
    wire: bytes, *, expected: WorkspaceSemanticMaterializationHeadV3
) -> WorkspaceSemanticMaterializationHeadV3:
    return cast(
        WorkspaceSemanticMaterializationHeadV3,
        _decode_v2_expected(
            wire, expected, WorkspaceSemanticMaterializationHeadV3, "head_v2"
        ),
    )


def encode_workspace_semantic_materialization_publication_receipt_v2(
    value: WorkspaceSemanticMaterializationPublicationReceiptV3,
) -> bytes:
    return _encode_v2_exact(
        value, WorkspaceSemanticMaterializationPublicationReceiptV3, "receipt_v2"
    )


def decode_workspace_semantic_materialization_publication_receipt_v2(
    wire: bytes, *, expected: WorkspaceSemanticMaterializationPublicationReceiptV3
) -> WorkspaceSemanticMaterializationPublicationReceiptV3:
    return cast(
        WorkspaceSemanticMaterializationPublicationReceiptV3,
        _decode_v2_expected(
            wire,
            expected,
            WorkspaceSemanticMaterializationPublicationReceiptV3,
            "receipt_v2",
        ),
    )


def encode_workspace_semantic_materialization_head_reread_evidence_v2(
    value: WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
) -> bytes:
    return _encode_v2_exact(
        value, WorkspaceSemanticMaterializationHeadRereadEvidenceV3, "head_reread_v2"
    )


def decode_workspace_semantic_materialization_head_reread_evidence_v2(
    wire: bytes, *, expected: WorkspaceSemanticMaterializationHeadRereadEvidenceV3
) -> WorkspaceSemanticMaterializationHeadRereadEvidenceV3:
    return cast(
        WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
        _decode_v2_expected(
            wire,
            expected,
            WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
            "head_reread_v2",
        ),
    )


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationPublicationMetrics:
    validation_ns: int
    staging_ns: int
    head_derivation_ns: int
    cas_ns: int
    reread_ns: int
    receipt_ns: int
    total_ns: int
    body_write_count: int
    body_write_bytes: int
    body_reread_count: int
    body_reread_bytes: int
    head_cas_count: int
    head_reread_count: int

    def __post_init__(self) -> None:
        for field in self.__dataclass_fields__:
            _nonnegative_int(getattr(self, field), field)


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationPublication:
    receipt: WorkspaceSemanticMaterializationPublicationReceipt
    metrics: WorkspaceSemanticMaterializationPublicationMetrics

    def __post_init__(self) -> None:
        if type(self.receipt) is not WorkspaceSemanticMaterializationPublicationReceipt:
            raise TypeError("publication receipt must be exact Workspace receipt")
        if type(self.metrics) is not WorkspaceSemanticMaterializationPublicationMetrics:
            raise TypeError("publication metrics must be exact Workspace metrics")


class WorkspaceSemanticMaterializationPublisher:
    """Stage exact Code output and advance one direct Workspace package head."""

    def __init__(
        self,
        *,
        state_store: LocalOperationalStateStore,
        body_store: WorkspaceSemanticMaterializationBodyStore,
        runtime: SemanticContractRuntime | None = None,
        state_namespace: str = DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
    ) -> None:
        if runtime is not None and type(runtime) is not SemanticContractRuntime:
            raise TypeError("runtime must be exact Code semantic runtime or absent")
        self._runtime = runtime
        self._state_store = state_store
        self._body_store = body_store
        self._state_namespace = _token(state_namespace, "state_namespace")
        self._lineage_entrances: dict[str, tuple[object, Any]] = {}
        for name in ("read_namespace_snapshot", "validate_namespace_snapshot"):
            method = getattr(state_store, name, None)
            if method is None:
                self._lineage_entrances.clear()
                break
            descriptor = inspect.getattr_static(state_store, name)
            if (
                not inspect.ismethod(method)
                or method.__self__ is not state_store
                or method.__func__ is not descriptor
            ):
                raise TypeError("original package-head namespace entrance required")
            self._lineage_entrances[name] = descriptor, method

    def _lineage_call(self, name: str, *args: object) -> Any:
        entrance = self._lineage_entrances.get(name)
        if entrance is None:
            raise WorkspaceSemanticMaterializationPublicationError(
                "original package-head namespace entrance unavailable"
            )
        descriptor, method = entrance
        if inspect.getattr_static(self._state_store, name) is not descriptor:
            raise WorkspaceSemanticMaterializationPublicationError(
                "package-head namespace entrance substituted"
            )
        result = method(*args)
        if inspect.getattr_static(self._state_store, name) is not descriptor:
            raise WorkspaceSemanticMaterializationPublicationError(
                "package-head namespace entrance substituted"
            )
        return result

    def _observe_v4_occurrence_absence(
        self,
        package: SemanticPackageCoordinate,
        occurrence: WorkspaceMaterializationPackageOccurrenceV4,
    ) -> LocalOperationalNamespaceSnapshot:
        """Inspect the original package-head namespace without issuing genesis.

        A last-value store cannot reconstruct an overwritten or deleted head.
        Such records, and heads predating occurrence binding, therefore refuse
        a negative claim. Historical non-Workspace continuity is a separate
        required admission before an empty SDK output state can be used.
        """

        snapshot = self._lineage_call("read_namespace_snapshot", self._state_namespace)
        self._validate_v4_occurrence_absence(snapshot, package, occurrence)
        return snapshot

    def _validate_v4_occurrence_absence(
        self,
        snapshot: LocalOperationalNamespaceSnapshot,
        package: SemanticPackageCoordinate,
        occurrence: WorkspaceMaterializationPackageOccurrenceV4,
    ) -> None:
        if type(snapshot) is not LocalOperationalNamespaceSnapshot:
            raise TypeError("original package-head namespace snapshot required")
        if type(package) is not SemanticPackageCoordinate:
            raise TypeError("exact selected package coordinate required")
        package.__post_init__()
        if type(occurrence) is not WorkspaceMaterializationPackageOccurrenceV4:
            raise TypeError("exact package occurrence required")
        occurrence.__post_init__()
        if snapshot.namespace != self._state_namespace:
            raise WorkspaceSemanticMaterializationPublicationError(
                "package-head namespace differs from original publisher"
            )
        self._lineage_call("validate_namespace_snapshot", snapshot)
        for record in snapshot.records:
            if record.deleted or record.value is None or record.revision != 1:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "package-head lineage history is unavailable"
                )
            if (
                _stored_publication_contract(record.value)
                != WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4
            ):
                raise WorkspaceSemanticMaterializationPublicationError(
                    "package-head occurrence history is unavailable"
                )
            head = _stored_publication_head_v4(record.value)
            if head.base_head.package.package_ref != record.key:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "package-head key differs from retained head"
                )
            if head.package_occurrence == occurrence:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "package-head lineage already exists"
                )
            if record.key == package.package_ref:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "selected package head already exists"
                )
        self._lineage_call("validate_namespace_snapshot", snapshot)

    def read_head(
        self, package_ref: str
    ) -> tuple[int, WorkspaceSemanticMaterializationHead] | None:
        record = self._state_store.read(
            self._state_namespace, _token(package_ref, "package_ref")
        )
        if record is None or record.value is None:
            return None
        if (
            _stored_publication_contract(record.value)
            != WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "stored publication head contract unsupported"
            )
        head = WorkspaceSemanticMaterializationHead.from_dict(
            _thaw_state_json(record.value)
        )
        if head.package_ref != package_ref:
            raise WorkspaceSemanticMaterializationPublicationError(
                "stored head package differs from state key"
            )
        return record.revision, head

    def _read_graph_v2_head(
        self,
        package_ref: str,
        *,
        observation_role: str,
        _retained_read: Callable[..., Any] | None = None,
    ) -> WorkspaceSemanticMaterializationHeadRereadEvidenceV3 | None:
        """Read one detached V2 head for the dormant graph coordinator.

        This is deliberately not part of the package export surface. 07F-C3
        will place the positive entrance behind the admitted graph execution
        capability; C2 only proves the resident persistence primitive.
        """

        package_key = _token(package_ref, "package_ref")
        record = (
            self._state_store.read(self._state_namespace, package_key)
            if _retained_read is None
            else _retained_read(2, self._state_namespace, package_key)
        )
        if record is None or record.value is None:
            return None
        head = _stored_publication_head_v2(record.value)
        if head.package.package_ref != package_ref:
            raise WorkspaceSemanticMaterializationPublicationError(
                "stored V2 head package differs from state key"
            )
        return _create_head_reread_v2_from_validated_head(
            observation_role=observation_role,
            materialization_head_revision=record.revision,
            head=head,
        )

    def _read_graph_v5_head_data(
        self,
        occurrence: object,
        *,
        expected_output_roles: tuple[str, ...],
    ) -> tuple[bytes, bytes | None] | None:
        """Read historical V5 record/HEAD bytes without approval or currentness.

        Fresh selected operation and original installed store/owner checks are
        required separately before predecessor or dependency admission. Missing
        data is not typed-empty genesis. V3/V4 readers/writers are unchanged.
        """
        from .package_occurrence_lineage import read_head_data

        try:
            return read_head_data(
                self, occurrence, expected_output_roles=expected_output_roles,
            )
        finally:
            # Held Workspace rejection frames do not own another store alias.
            del self, occurrence

    def _read_graph_v4_head(
        self,
        package_ref: str,
        *,
        _retained_read: Callable[..., Any] | None = None,
    ) -> tuple[int, WorkspaceSemanticMaterializationHeadV4] | None:
        """Read the stored state-bound head; this detached value grants no use."""

        package_key = _token(package_ref, "package_ref")
        record = (
            self._state_store.read(self._state_namespace, package_key)
            if _retained_read is None
            else _retained_read(2, self._state_namespace, package_key)
        )
        if record is None or record.value is None:
            return None
        head = _stored_publication_head_v4(record.value)
        if head.base_head.package.package_ref != package_ref:
            raise WorkspaceSemanticMaterializationPublicationError(
                "stored V4 head package differs from state key"
            )
        return record.revision, head

    def _read_graph_v4_head_evidence(
        self,
        package_ref: str,
        *,
        observation_role: str,
        _retained_read: Callable[..., Any] | None = None,
    ) -> WorkspaceSemanticMaterializationHeadRereadEvidenceV4 | None:
        """Reread one state-bound head and every retained transition body.

        The two head reads bound a sequential observation interval. They are
        detached evidence, not a fence or a substitute for parent exclusion.
        """

        first = (
            self._read_graph_v4_head(package_ref)
            if _retained_read is None
            else _retained_read(6, package_ref)
        )
        if first is None:
            return None
        revision, head = first
        for binding in head.output_state_bindings:
            if _retained_read is None:
                self._read_graph_v4_output_state(
                    head, output_role=binding.output_coordinate.role
                )
            else:
                _retained_read(7, head, output_role=binding.output_coordinate.role)
        final = (
            self._read_graph_v4_head(package_ref)
            if _retained_read is None
            else _retained_read(6, package_ref)
        )
        if final != first:
            raise WorkspaceSemanticMaterializationPublicationError(
                "state-bound package head changed during reread"
            )
        return WorkspaceSemanticMaterializationHeadRereadEvidenceV4.create(
            observation_role=observation_role,
            materialization_head_revision=revision,
            head=head,
        )

    def _read_graph_package_head_evidence(
        self,
        package_ref: str,
        *,
        observation_role: str,
        _retained_read: Callable[..., Any] | None = None,
    ) -> (
        WorkspaceSemanticMaterializationHeadRereadEvidenceV3
        | WorkspaceSemanticMaterializationHeadRereadEvidenceV4
        | None
    ):
        """Read one existing graph head without erasing its wire version.

        The version check is only routing. Each owning reader performs its own
        fresh validation; a replacement between the reads refuses.

        Fulfillment supplies its captured original dispatcher as an internal
        read context. Every nested HEAD/body/store call preserves that context;
        this path never looks up the next reader after I/O. Other callers retain
        their existing read behavior. The context grants no store authority.
        """

        package_key = _token(package_ref, "package_ref")
        record = (
            self._state_store.read(self._state_namespace, package_key)
            if _retained_read is None
            else _retained_read(2, self._state_namespace, package_key)
        )
        if record is None or record.value is None:
            return None
        contract = _stored_publication_contract(record.value)
        if contract == WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V3:
            observed = (
                self._read_graph_v2_head(package_key, observation_role=observation_role)
                if _retained_read is None
                else _retained_read(4, package_key, observation_role=observation_role)
            )
        elif contract == WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4:
            observed = (
                self._read_graph_v4_head_evidence(
                    package_key, observation_role=observation_role
                )
                if _retained_read is None
                else _retained_read(5, package_key, observation_role=observation_role)
            )
        else:
            raise WorkspaceSemanticMaterializationPublicationError(
                "stored graph package head contract unsupported"
            )
        if observed is None or observed.materialization_head_revision != record.revision:
            raise WorkspaceSemanticMaterializationPublicationError(
                "graph package head changed during versioned read"
            )
        return observed

    def _publish_graph_v2(
        self,
        *,
        request: WorkspaceSemanticMaterializationRequestV3,
        snapshot: ExecutionPublicationSnapshot,
        invocation: SemanticContractInvocation,
    ) -> tuple[
        WorkspaceSemanticMaterializationPublicationReceiptV3,
        WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
    ]:
        """Persist one dormant graph V2 head in the existing package slot."""

        if type(request) is not WorkspaceSemanticMaterializationRequestV3:
            raise TypeError("graph publication request must be exact V2 request")
        if type(snapshot) is not ExecutionPublicationSnapshot:
            raise TypeError("graph publication snapshot must be exact Code snapshot")
        if type(invocation) is not SemanticContractInvocation:
            raise TypeError(
                "graph publication invocation must be exact Code invocation"
            )
        request.__post_init__()
        snapshot.__post_init__()
        invocation.__post_init__()
        if invocation.digest != snapshot.invocation_digest:
            raise WorkspaceSemanticMaterializationPublicationError(
                "graph publication invocation differs from Code snapshot"
            )
        if request.operation_result_digest != snapshot.result_digest:
            raise WorkspaceSemanticMaterializationPublicationError(
                "graph publication operation result differs from Code snapshot"
            )
        snapshot.body_for(request.result_coordinate)
        self._stage_graph_v2_snapshot(snapshot, invocation=invocation)
        target = WorkspaceSemanticMaterializationHeadV3.create(request=request)
        record = self._state_store.read(
            self._state_namespace, request.package.package_ref
        )
        actual_revision = 0 if record is None else record.revision
        current_v2: WorkspaceSemanticMaterializationHeadV3 | None = None
        if record is not None and record.value is not None:
            contract = _stored_publication_contract(record.value)
            if contract == WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD:
                # Strictly authenticate the historical predecessor. Its body is
                # never returned from the graph entrance or reissued as V2.
                predecessor = WorkspaceSemanticMaterializationHead.from_dict(
                    _thaw_state_json(record.value)
                )
                if predecessor.package_ref != request.package.package_ref:
                    raise WorkspaceSemanticMaterializationPublicationError(
                        "stored V1 predecessor package differs from state key"
                    )
            elif contract == WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V3:
                current_v2 = _stored_publication_head_v2(record.value)
                if current_v2.package.package_ref != request.package.package_ref:
                    raise WorkspaceSemanticMaterializationPublicationError(
                        "stored V2 predecessor package differs from state key"
                    )
            else:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "stored publication head contract unsupported"
                )

        exact_retry = (
            current_v2 is not None
            and current_v2 == target
            and actual_revision == request.expected_head_revision + 1
        )
        if exact_retry:
            head_revision = actual_revision
            advanced = True
        else:
            if actual_revision != request.expected_head_revision:
                raise WorkspaceSemanticMaterializationPublicationConflict(
                    "graph V2 expected package head revision is stale"
                )
            try:
                advanced_record = self._state_store.compare_and_set(
                    self._state_namespace,
                    request.package.package_ref,
                    expected_revision=request.expected_head_revision,
                    value=cast(JsonObject, target.to_wire()),
                )
            except LocalOperationalStateConflict as error:
                raise WorkspaceSemanticMaterializationPublicationConflict(
                    "graph V2 package head CAS lost"
                ) from error
            head_revision = advanced_record.revision
            advanced = True

        reread = self._read_graph_v2_head(
            request.package.package_ref, observation_role="package_result"
        )
        if (
            reread is None
            or reread.materialization_head_revision != head_revision
            or canonical_json_bytes(reread.head.to_wire())
            != canonical_json_bytes(target.to_wire())
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "graph V2 committed package head reread differs"
            )
        receipt = WorkspaceSemanticMaterializationPublicationReceiptV3.create(
            request=request,
            head=target,
            prior_head_revision=request.expected_head_revision,
            head_revision=head_revision,
            head_advanced=advanced,
        )
        return receipt, reread

    def _stage_graph_v2_snapshot(
        self,
        snapshot: ExecutionPublicationSnapshot,
        *,
        invocation: SemanticContractInvocation,
    ) -> None:
        """Stage and reread one complete detached Code publication snapshot."""

        if type(snapshot) is not ExecutionPublicationSnapshot:
            raise TypeError("graph publication snapshot must be exact Code snapshot")
        if type(invocation) is not SemanticContractInvocation:
            raise TypeError(
                "graph publication invocation must be exact Code invocation"
            )
        snapshot.__post_init__()
        invocation.__post_init__()
        if invocation.digest != snapshot.invocation_digest:
            raise WorkspaceSemanticMaterializationPublicationError(
                "Code invocation differs from detached snapshot"
            )
        try:
            result_text = snapshot.result_wire.decode("utf-8")
        except UnicodeDecodeError as error:
            raise WorkspaceSemanticMaterializationPublicationError(
                "Code result wire is not UTF-8"
            ) from error
        root = json.loads(result_text)
        if type(root) is not dict or "digest" not in root:
            raise WorkspaceSemanticMaterializationPublicationError(
                "Code result wire lacks its top-level digest"
            )
        digest = root.pop("digest", None)
        if digest != snapshot.result_digest.value:
            raise WorkspaceSemanticMaterializationPublicationError(
                "Code result wire digest differs from snapshot"
            )
        result_body = canonical_json_bytes(root)
        if ContentDigest.of_bytes(result_body) != snapshot.result_digest:
            raise WorkspaceSemanticMaterializationPublicationError(
                "digest-stripped Code result body identity differs"
            )

        invocation_root = invocation.to_wire()
        invocation_digest = invocation_root.pop("digest", None)
        if invocation_digest != snapshot.invocation_digest.value:
            raise WorkspaceSemanticMaterializationPublicationError(
                "Code invocation wire digest differs from snapshot"
            )
        invocation_body = canonical_json_bytes(invocation_root)
        if ContentDigest.of_bytes(invocation_body) != snapshot.invocation_digest:
            raise WorkspaceSemanticMaterializationPublicationError(
                "digest-stripped Code invocation body identity differs"
            )

        staged = tuple(
            (
                _body_ref(body.coordinate.digest.value),
                body.canonical_body,
            )
            for body in snapshot.bodies
        ) + (
            (_body_ref(snapshot.invocation_digest.value), invocation_body),
            (_body_ref(snapshot.result_digest.value), result_body),
        )
        if len({body_ref for body_ref, _body in staged}) != len(staged):
            raise WorkspaceSemanticMaterializationPublicationError(
                "graph publication body refs are not unique"
            )
        self._body_store.store_bodies(staged)
        for body_ref, expected in staged:
            observed = self._body_store.read_body(body_ref)
            if type(observed) is not bytes or observed != expected:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "graph publication staged body reread differs"
                )

    def _read_graph_v2_operation_result(
        self,
        head: WorkspaceSemanticMaterializationHeadV3,
        *,
        declaration: SemanticContractProviderDeclaration,
    ) -> tuple[SemanticContractResult, SemanticContractInvocation]:
        """Reconstruct one strict Code result from its digest-stripped CAS body."""

        if type(head) is not WorkspaceSemanticMaterializationHeadV3:
            raise TypeError("graph operation-result head must be exact V3 head")
        if type(declaration) is not SemanticContractProviderDeclaration:
            raise TypeError(
                "graph operation-result declaration must be exact Code value"
            )
        head.__post_init__()
        declaration.__post_init__()
        body_ref = _body_ref(head.operation_result_digest.value)
        body = self._body_store.read_body(body_ref)
        if type(body) is not bytes:
            raise WorkspaceSemanticMaterializationPublicationError(
                "graph operation-result body is absent"
            )
        if ContentDigest.of_bytes(body) != head.operation_result_digest:
            raise WorkspaceSemanticMaterializationPublicationError(
                "graph operation-result body digest differs from head"
            )
        try:
            root = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise WorkspaceSemanticMaterializationPublicationError(
                "graph operation-result body is not strict JSON"
            ) from error
        if (
            type(root) is not dict
            or "digest" in root
            or canonical_json_bytes(root) != body
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "graph operation-result body is not canonical digest-free JSON"
            )
        invocation_digest = root.get("invocation_digest")
        if type(invocation_digest) is not str:
            raise WorkspaceSemanticMaterializationPublicationError(
                "graph operation-result invocation digest is absent"
            )
        try:
            exact_invocation_digest = ContentDigest(invocation_digest)
        except (TypeError, ValueError) as error:
            raise WorkspaceSemanticMaterializationPublicationError(
                "graph operation-result invocation digest is invalid"
            ) from error
        invocation_body = self._body_store.read_body(
            _body_ref(exact_invocation_digest.value)
        )
        if (
            type(invocation_body) is not bytes
            or ContentDigest.of_bytes(invocation_body) != exact_invocation_digest
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "graph operation-result invocation body differs"
            )
        try:
            invocation_root = json.loads(invocation_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise WorkspaceSemanticMaterializationPublicationError(
                "graph invocation body is not strict JSON"
            ) from error
        if (
            type(invocation_root) is not dict
            or "digest" in invocation_root
            or canonical_json_bytes(invocation_root) != invocation_body
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "graph invocation body is not canonical digest-free JSON"
            )
        invocation_wire = canonical_json_bytes(
            {**invocation_root, "digest": exact_invocation_digest.value}
        )
        try:
            invocation = decode_invocation(invocation_wire.decode("utf-8"))
        except (ContractViolation, TypeError, ValueError) as error:
            raise WorkspaceSemanticMaterializationPublicationError(
                "reconstructed graph invocation is invalid"
            ) from error
        if invocation.digest != exact_invocation_digest:
            raise WorkspaceSemanticMaterializationPublicationError(
                "reconstructed graph invocation digest differs"
            )
        full_wire = canonical_json_bytes(
            {**root, "digest": head.operation_result_digest.value}
        )
        try:
            result = decode_result(full_wire.decode("utf-8"), declaration, invocation)
        except (ContractViolation, TypeError, ValueError) as error:
            raise WorkspaceSemanticMaterializationPublicationError(
                "reconstructed graph operation result is invalid"
            ) from error
        if result.digest != head.operation_result_digest:
            raise WorkspaceSemanticMaterializationPublicationError(
                "reconstructed graph operation result digest differs"
            )
        return result, invocation

    def _read_graph_v2_body(
        self,
        coordinate: SemanticValueCoordinate,
        *,
        _retained_read: Callable[..., Any] | None = None,
    ) -> SemanticBody:
        """Reread one exact content-addressed body referenced by V2 evidence."""

        if type(coordinate) is not SemanticValueCoordinate:
            raise TypeError("graph semantic body coordinate must be exact")
        coordinate.__post_init__()
        body_ref = _body_ref(coordinate.digest.value)
        body = (
            self._body_store.read_body(body_ref)
            if _retained_read is None
            else _retained_read(3, body_ref)
        )
        if type(body) is not bytes:
            raise WorkspaceSemanticMaterializationPublicationError(
                "graph semantic body is absent"
            )
        if (
            ContentDigest.of_bytes(body) != coordinate.digest
            or len(body) != coordinate.size_bytes
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "graph semantic body differs from its coordinate"
            )
        return SemanticBody(coordinate, body)

    def _read_graph_v4_output_state(
        self,
        head: WorkspaceSemanticMaterializationHeadV4,
        *,
        output_role: str,
        _retained_read: Callable[..., Any] | None = None,
    ) -> CodePackageOutputState:
        """Recheck retained Code delta/state bytes; grant no predecessor authority."""

        if type(head) is not WorkspaceSemanticMaterializationHeadV4:
            raise TypeError("exact state-bound package head required")
        head.__post_init__()
        role = _token(output_role, "output_role")
        matches = tuple(
            item for item in head.output_state_bindings
            if item.output_coordinate.role == role
        )
        if len(matches) != 1:
            raise WorkspaceSemanticMaterializationPublicationError(
                "state-bound output role is unavailable"
            )
        binding = matches[0]

        def read_state_body(body_ref: str, digest: ContentDigest, size: int) -> bytes:
            body = (
                self._body_store.read_body(body_ref)
                if _retained_read is None
                else _retained_read(3, body_ref)
            )
            if (
                type(body) is not bytes
                or ContentDigest.of_bytes(body) != digest
                or len(body) != size
            ):
                raise WorkspaceSemanticMaterializationPublicationError(
                    "state-bound output body is missing or changed"
                )
            return body

        prior_body = read_state_body(
            binding.prior_state_body_ref,
            binding.prior_state_body_digest,
            binding.prior_state_body_size,
        )
        state_body = read_state_body(
            binding.state_body_ref,
            binding.state_body_digest,
            binding.state_body_size,
        )
        delta_body = (
            self._read_graph_v2_body(binding.output_coordinate)
            if _retained_read is None
            else _retained_read(1, binding.output_coordinate)
        ).canonical_body
        try:
            prior = CodePackageOutputState.from_json_bytes(prior_body)
            state = CodePackageOutputState.from_json_bytes(state_body)
            delta = CodePackageDelta.from_json_bytes(delta_body)
            derived = derive_code_package_output_state(prior, delta)
        except (CodePackageDeltaContractError, TypeError, ValueError) as error:
            raise WorkspaceSemanticMaterializationPublicationError(
                "state-bound Code output transition is invalid"
            ) from error
        if (
            prior.state_digest != binding.prior_state_digest.value
            or state.state_digest != binding.state_digest.value
            or prior.package_name != binding.output_state_name
            or state.package_name != binding.output_state_name
            or derived != state
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "state-bound Code output transition differs"
            )
        return state

    def _read_graph_v4_current_output_state(
        self,
        *,
        package: SemanticPackageCoordinate,
        expected_head_revision: int,
        expected_head_digest: ContentDigest,
        declaration: SemanticContractProviderDeclaration,
        output_role: str,
        output_state_name: str,
    ) -> CodePackageOutputState:
        """Reread the exact current Code result and state; issue no admission.

        The caller owns the original operation, package-occurrence and source
        validators. This shared read only verifies their expected head against
        retained Code result and output-state bodies across one read interval.
        """

        if type(package) is not SemanticPackageCoordinate:
            raise TypeError("exact selected package coordinate required")
        package.__post_init__()
        _nonnegative_int(expected_head_revision, "expected_head_revision")
        _v2_content_digest(expected_head_digest, "expected_head_digest")
        if type(declaration) is not SemanticContractProviderDeclaration:
            raise TypeError("original selected Code declaration required")
        declaration.__post_init__()
        role = _token(output_role, "output_role")
        name = _token(output_state_name, "output_state_name")
        current = self._read_graph_v4_head(package.package_ref)
        if current is None:
            raise WorkspaceSemanticMaterializationPublicationError(
                "state-bound current head is unavailable"
            )
        revision, head = current
        if (
            revision != expected_head_revision
            or head.head_digest != expected_head_digest
            or head.base_head.package != package
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "state-bound head differs from original admission"
            )
        result, invocation = self._read_graph_v2_operation_result(
            head.base_head, declaration=declaration
        )
        selected = tuple(
            binding.output_coordinate
            for binding in head.output_state_bindings
            if binding.output_coordinate.role == role
        )
        if (
            invocation.target_package != package
            or result.status is not TerminalStatus.DELTA
            or len(selected) != 1
            or sum(item.output == selected[0] for item in result.outputs) != 1
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "state-bound output differs from selected Code result"
            )
        state = self._read_graph_v4_output_state(head, output_role=role)
        if self._read_graph_v4_head(package.package_ref) != current:
            raise WorkspaceSemanticMaterializationPublicationError(
                "state-bound head changed during output-state read"
            )
        if state.package_name != name:
            raise WorkspaceSemanticMaterializationPublicationError(
                "state-bound output name differs"
            )
        return state

    def _prepare_graph_v4_output_successor(
        self,
        *,
        request: WorkspaceSemanticMaterializationRequestV3,
        package_occurrence: WorkspaceMaterializationPackageOccurrenceV4,
        predecessor_head_digest: ContentDigest | None = None,
        snapshot: ExecutionPublicationSnapshot,
        invocation: SemanticContractInvocation,
        operation_ref: str,
        operation_digest: ContentDigest,
        output_role: str,
        prior_output_state: CodePackageOutputState,
    ) -> tuple[WorkspaceSemanticMaterializationHeadV4, bytes, bytes]:
        """Derive a data-only V4 candidate; original admission must precede CAS."""

        if type(request) is not WorkspaceSemanticMaterializationRequestV3:
            raise TypeError("exact graph publication request required")
        if type(package_occurrence) is not WorkspaceMaterializationPackageOccurrenceV4:
            raise TypeError("exact Workspace package occurrence required")
        package_occurrence.__post_init__()
        if type(snapshot) is not ExecutionPublicationSnapshot:
            raise TypeError("exact Code publication snapshot required")
        if type(invocation) is not SemanticContractInvocation:
            raise TypeError("exact Code invocation required")
        if type(prior_output_state) is not CodePackageOutputState:
            raise TypeError("exact prior Code output state required")
        request.__post_init__()
        snapshot.__post_init__()
        invocation.__post_init__()
        prior_output_state.__post_init__()
        if (
            request.package != invocation.target_package
            or snapshot.invocation_digest != invocation.digest
            or snapshot.profile_digest != invocation.profile_digest
            or snapshot.result_digest != request.operation_result_digest
            or snapshot.result_digest != snapshot.result.digest
            or snapshot.result_wire != canonical_json_bytes(snapshot.result.to_wire())
            or snapshot.result.status is not TerminalStatus.DELTA
            or snapshot.result.transition is None
            or snapshot.result.transition.result != request.result_coordinate
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "V4 successor differs from selected Code execution"
            )
        role = _token(output_role, "output_role")
        selected = tuple(
            item.output for item in snapshot.result.outputs
            if item.output.role == role
        )
        if len(selected) != 1:
            raise WorkspaceSemanticMaterializationPublicationError(
                "V4 successor requires one selected Code output"
            )
        try:
            delta = CodePackageDelta.from_json_bytes(
                snapshot.body_for(selected[0]).canonical_body
            )
            successor = derive_code_package_output_state(prior_output_state, delta)
        except (
            ContractViolation,
            CodePackageDeltaContractError,
            TypeError,
            ValueError,
        ) as error:
            raise WorkspaceSemanticMaterializationPublicationError(
                "V4 successor Code delta is invalid"
            ) from error
        prior_body = prior_output_state.to_json_bytes()
        state_body = successor.to_json_bytes()
        prior_digest = ContentDigest.of_bytes(prior_body)
        state_digest = ContentDigest.of_bytes(state_body)
        binding = WorkspaceSemanticMaterializationOutputStateBindingV4(
            output_coordinate=selected[0],
            output_state_name=successor.package_name,
            prior_state_body_ref=_body_ref(prior_digest.value),
            prior_state_body_digest=prior_digest,
            prior_state_body_size=len(prior_body),
            prior_state_digest=ContentDigest(prior_output_state.state_digest),
            state_body_ref=_body_ref(state_digest.value),
            state_body_digest=state_digest,
            state_body_size=len(state_body),
            state_digest=ContentDigest(successor.state_digest),
        )
        head = WorkspaceSemanticMaterializationHeadV4.create(
            request=request,
            package_occurrence=package_occurrence,
            predecessor_head_digest=predecessor_head_digest,
            operation_ref=operation_ref,
            operation_digest=operation_digest,
            output_state_bindings=(binding,),
        )
        return head, prior_body, state_body

    def _publish_graph_v4_existing_successor(
        self,
        *,
        request: WorkspaceSemanticMaterializationRequestV3,
        snapshot: ExecutionPublicationSnapshot,
        invocation: SemanticContractInvocation,
        package_occurrence: WorkspaceMaterializationPackageOccurrenceV4,
        expected_prior_head_digest: ContentDigest,
        prior_output_state: CodePackageOutputState,
        operation_ref: str,
        operation_digest: ContentDigest,
        output_role: str,
    ) -> tuple[
        WorkspaceSemanticMaterializationPublicationReceiptV4,
        WorkspaceSemanticMaterializationHeadRereadEvidenceV4,
    ]:
        """Commit one state-bound successor in the existing package-head slot.

        This private store primitive does not admit a graph node or genesis.
        Its caller must retain the original node/source use across this call.
        All result and state bodies are reread before the single head CAS.
        """

        if type(request) is not WorkspaceSemanticMaterializationRequestV3:
            raise TypeError("exact V4 graph request required")
        if type(expected_prior_head_digest) is not ContentDigest:
            raise TypeError("exact original predecessor digest required")
        request.__post_init__()
        expected_prior_head_digest.__post_init__()
        if request.expected_head_revision < 1:
            raise WorkspaceSemanticMaterializationPublicationError(
                "V4 genesis requires separate lineage and historical admission"
            )
        if type(package_occurrence) is not WorkspaceMaterializationPackageOccurrenceV4:
            raise TypeError("exact V4 package occurrence required")
        package_occurrence.__post_init__()
        if type(prior_output_state) is not CodePackageOutputState:
            raise TypeError("exact prior output state required")
        prior_output_state.__post_init__()

        target, prior_body, state_body = self._prepare_graph_v4_output_successor(
            request=request,
            package_occurrence=package_occurrence,
            predecessor_head_digest=expected_prior_head_digest,
            snapshot=snapshot,
            invocation=invocation,
            operation_ref=operation_ref,
            operation_digest=operation_digest,
            output_role=output_role,
            prior_output_state=prior_output_state,
        )
        predecessor = self._read_graph_v4_head_evidence(
            request.package.package_ref, observation_role="package_reuse"
        )
        exact_retry = (
            predecessor is not None
            and predecessor.materialization_head_revision
            == request.expected_head_revision + 1
            and predecessor.head == target
            and target.predecessor_head_digest == expected_prior_head_digest
        )
        if not exact_retry and (
            predecessor is None
            or predecessor.materialization_head_revision
            != request.expected_head_revision
            or predecessor.materialization_head_digest
            != expected_prior_head_digest
            or predecessor.head.base_head.package != request.package
            or predecessor.head.package_occurrence != package_occurrence
            or invocation.predecessor
            != predecessor.head.base_head.result_coordinate
            or self._read_graph_v4_output_state(
                predecessor.head, output_role=output_role
            ) != prior_output_state
        ):
            raise WorkspaceSemanticMaterializationPublicationConflict(
                "V4 graph predecessor differs from original observation"
            )
        self._stage_graph_v2_snapshot(snapshot, invocation=invocation)
        state_bodies = {
            _body_ref(ContentDigest.of_bytes(body).value): body
            for body in (prior_body, state_body)
        }
        self._body_store.store_bodies(tuple(state_bodies.items()))
        for body_ref, body in state_bodies.items():
            if self._body_store.read_body(body_ref) != body:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "V4 output state staged body reread differs"
                )

        current = self._read_graph_v4_head_evidence(
            request.package.package_ref, observation_role="package_reuse"
        )
        if exact_retry and (
            current is not None
            and current.materialization_head_revision
            == request.expected_head_revision + 1
            and current.head == target
        ):
            head_revision = current.materialization_head_revision
        else:
            if (
                current is None
                or current.materialization_head_revision
                != request.expected_head_revision
                or current.materialization_head_digest
                != expected_prior_head_digest
                or predecessor is None
                or current.head != predecessor.head
                or self._read_graph_v4_output_state(
                    current.head, output_role=output_role
                ) != prior_output_state
            ):
                raise WorkspaceSemanticMaterializationPublicationConflict(
                    "V4 graph predecessor changed before CAS"
                )
            try:
                advanced = self._state_store.compare_and_set(
                    self._state_namespace,
                    request.package.package_ref,
                    expected_revision=request.expected_head_revision,
                    value=cast(JsonObject, target.to_wire()),
                )
            except LocalOperationalStateConflict as error:
                raise WorkspaceSemanticMaterializationPublicationConflict(
                    "V4 graph package-head CAS lost"
                ) from error
            head_revision = advanced.revision

        reread = self._read_graph_v4_head_evidence(
            request.package.package_ref, observation_role="package_result"
        )
        if (
            reread is None
            or reread.materialization_head_revision != head_revision
            or reread.head != target
            or self._read_graph_v4_output_state(
                reread.head, output_role=output_role
            ).state_digest
            != target.output_state_bindings[0].state_digest.value
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "V4 graph committed head or output state reread differs"
            )
        receipt = WorkspaceSemanticMaterializationPublicationReceiptV4.create(
            request=request,
            head=target,
            prior_head_revision=(
                head_revision if exact_retry else request.expected_head_revision
            ),
            head_revision=head_revision,
            head_advanced=not exact_retry,
        )
        return receipt, reread

    def publish(
        self,
        *,
        admission: WorkspaceSemanticMaterializationAdmission,
        invocation: SemanticContractInvocation,
        completion: ExecutionCompletion,
        expected_head_revision: int,
    ) -> WorkspaceSemanticMaterializationPublication:
        started = time.perf_counter_ns()
        validation_started = started
        if type(admission) is not WorkspaceSemanticMaterializationAdmission:
            raise TypeError("admission must be exact Workspace admission")
        admission._assert_intact()
        if type(invocation) is not SemanticContractInvocation:
            raise TypeError("invocation must be exact Code invocation")
        invocation.__post_init__()
        _nonnegative_int(expected_head_revision, "expected_head_revision")
        if self._runtime is None:
            raise WorkspaceSemanticMaterializationPublicationError(
                "direct publication requires its original Code runtime"
            )
        try:
            snapshot = self._runtime.snapshot_completion(completion)
        except (AttributeError, ContractViolation, TypeError) as error:
            raise WorkspaceSemanticMaterializationPublicationError(
                "Code runtime does not own execution completion"
            ) from error
        if (
            snapshot.invocation_digest != invocation.digest
            or snapshot.profile_digest != invocation.profile_digest
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "execution completion differs from exact invocation/profile"
            )
        if admission.request_digest != _semantic_digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_REQUEST,
            {
                "package_ref": admission.package_ref,
                "package_kind": admission.package_kind,
                "manifest_digest": admission.manifest_digest,
                "source_authority_ref": admission.source_authority_ref,
                "source_authority_digest": admission.source_authority_digest,
                "operation_ref": admission.operation_ref,
                "operation_digest": admission.operation_digest,
                "profile_ref": invocation.profile_ref,
                "profile_digest": invocation.profile_digest.value,
                "invocation_digest": invocation.digest.value,
            },
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "Workspace admission differs from exact Code invocation"
            )
        if (
            invocation.target_package.package_ref != admission.package_ref
            or invocation.target_package.package_kind != admission.package_kind
            or invocation.target_package.manifest_digest.value
            != admission.manifest_digest
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "Code target package differs from Workspace admission"
            )
        result = snapshot.result
        if result.status not in {TerminalStatus.CURRENT, TerminalStatus.DELTA}:
            raise WorkspaceSemanticMaterializationPublicationError(
                "non-success Code completion cannot be published"
            )
        current = self.read_head(admission.package_ref)
        actual_revision = 0 if current is None else current[0]
        possible_exact_retry = (
            result.status is TerminalStatus.DELTA
            and actual_revision == expected_head_revision + 1
        )
        if actual_revision != expected_head_revision and not possible_exact_retry:
            raise WorkspaceSemanticMaterializationPublicationConflict(
                f"expected head revision {expected_head_revision}, found {actual_revision}"
            )
        if actual_revision == expected_head_revision and current is None:
            if type(invocation.predecessor) is not TypedEmptyCoordinate:
                raise WorkspaceSemanticMaterializationPublicationConflict(
                    "genesis publication requires typed-empty predecessor"
                )
            if result.status is TerminalStatus.CURRENT:
                raise WorkspaceSemanticMaterializationPublicationConflict(
                    "current result requires an existing Workspace head"
                )
        elif actual_revision == expected_head_revision:
            assert current is not None
            predecessor = invocation.predecessor
            if type(predecessor) is not SemanticValueCoordinate:
                raise WorkspaceSemanticMaterializationPublicationConflict(
                    "successor publication requires exact semantic predecessor"
                )
            if canonical_json_bytes(predecessor.to_wire()) != canonical_json_bytes(
                current[1].candidate.to_code_wire()
            ):
                raise WorkspaceSemanticMaterializationPublicationConflict(
                    "Code predecessor differs from current Workspace head"
                )
        if result.status is TerminalStatus.CURRENT:
            candidate_value = result.current_result
        else:
            if result.transition is None:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "delta result lacks transition"
                )
            candidate_value = result.transition.result
        if type(candidate_value) is not SemanticValueCoordinate:
            raise WorkspaceSemanticMaterializationPublicationError(
                "successful result lacks exact candidate coordinate"
            )
        candidate = WorkspacePublishedSemanticCoordinate.from_code(candidate_value)
        if (
            result.status is TerminalStatus.CURRENT
            and current is not None
            and candidate != current[1].candidate
        ):
            raise WorkspaceSemanticMaterializationPublicationConflict(
                "current result candidate differs from Workspace head"
            )
        validation_ns = time.perf_counter_ns() - validation_started

        staging_started = time.perf_counter_ns()
        semantic_coordinates = _terminal_body_coordinates(result)
        snapshot_bodies = {
            item.coordinate: item.canonical_body for item in snapshot.bodies
        }
        staged: list[WorkspaceStagedSemanticBody] = []
        staged_writes: list[tuple[str, bytes]] = []
        body_write_bytes = 0
        for coordinate in semantic_coordinates:
            try:
                body = snapshot_bodies[coordinate]
            except KeyError as error:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "completion snapshot lacks terminal semantic body"
                ) from error
            staged_body = WorkspaceStagedSemanticBody.from_code(coordinate)
            staged.append(staged_body)
            staged_writes.append((staged_body.body_ref, body))
            body_write_bytes += len(body)
        result_wire = snapshot.result_wire
        result_body_digest = ContentDigest.of_bytes(result_wire).value
        result_body_ref = _body_ref(result_body_digest)
        staged_writes.append((result_body_ref, result_wire))
        self._body_store.store_bodies(tuple(staged_writes))
        body_write_bytes += len(result_wire)
        for staged_body, coordinate in zip(staged, semantic_coordinates, strict=True):
            observed = self._body_store.read_body(staged_body.body_ref)
            expected = snapshot_bodies[coordinate]
            if type(observed) is not bytes or observed != expected:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "staged semantic body reread differs"
                )
        observed_result_wire = self._body_store.read_body(result_body_ref)
        if (
            type(observed_result_wire) is not bytes
            or observed_result_wire != result_wire
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "staged result envelope reread differs"
            )
        staging_ns = time.perf_counter_ns() - staging_started
        staged_tuple = tuple(sorted(staged))

        head_derivation_started = time.perf_counter_ns()
        cas_ns = 0
        head_cas_count = 0
        if result.status is TerminalStatus.CURRENT:
            assert current is not None
            head_revision, head = current
            head_advanced = False
        else:
            head = WorkspaceSemanticMaterializationHead.create(
                admission=admission,
                invocation=invocation,
                result=result,
                result_digest=snapshot.result_digest.value,
                transition_digest=(
                    snapshot.transition_digest.value
                    if snapshot.transition_digest is not None
                    else None
                ),
                effect_digest=snapshot.effect_digest.value,
                result_body_ref=result_body_ref,
                result_body_digest=result_body_digest,
                result_body_size_bytes=len(result_wire),
                candidate=candidate,
                semantic_bodies=staged_tuple,
            )
            if possible_exact_retry:
                assert current is not None
                if current[1] != head:
                    raise WorkspaceSemanticMaterializationPublicationConflict(
                        "advanced Workspace head differs from exact retry"
                    )
                head_revision = current[0]
                head_advanced = True
            else:
                cas_started = time.perf_counter_ns()
                try:
                    record = self._state_store.compare_and_set(
                        self._state_namespace,
                        admission.package_ref,
                        expected_revision=expected_head_revision,
                        value=cast(JsonObject, head.to_dict()),
                    )
                except LocalOperationalStateConflict as error:
                    raise WorkspaceSemanticMaterializationPublicationConflict(
                        "Workspace package head CAS lost"
                    ) from error
                cas_ns = time.perf_counter_ns() - cas_started
                head_cas_count = 1
                head_revision = record.revision
                head_advanced = True
        head_derivation_ns = time.perf_counter_ns() - head_derivation_started - cas_ns

        reread_started = time.perf_counter_ns()
        reread = self.read_head(admission.package_ref)
        if reread is None or reread[0] != head_revision or reread[1] != head:
            raise WorkspaceSemanticMaterializationPublicationError(
                "Workspace package head committed reread differs"
            )
        reread_ns = time.perf_counter_ns() - reread_started
        receipt_started = time.perf_counter_ns()
        receipt = WorkspaceSemanticMaterializationPublicationReceipt.create(
            head=head,
            observed_result_digest=snapshot.result_digest.value,
            observed_result_body_ref=result_body_ref,
            observed_result_body_digest=result_body_digest,
            observed_semantic_bodies=staged_tuple,
            prior_head_revision=expected_head_revision,
            head_revision=head_revision,
            head_advanced=head_advanced,
        )
        receipt_ns = time.perf_counter_ns() - receipt_started
        metrics = WorkspaceSemanticMaterializationPublicationMetrics(
            validation_ns=validation_ns,
            staging_ns=staging_ns,
            head_derivation_ns=head_derivation_ns,
            cas_ns=cas_ns,
            reread_ns=reread_ns,
            receipt_ns=receipt_ns,
            total_ns=time.perf_counter_ns() - started,
            body_write_count=len(staged_tuple) + 1,
            body_write_bytes=body_write_bytes,
            body_reread_count=len(staged_tuple) + 1,
            body_reread_bytes=body_write_bytes,
            head_cas_count=head_cas_count,
            head_reread_count=1,
        )
        return WorkspaceSemanticMaterializationPublication(receipt, metrics)


def _terminal_body_coordinates(
    result: SemanticContractResult,
) -> tuple[SemanticValueCoordinate, ...]:
    effect = result.effect
    if effect is None:
        raise WorkspaceSemanticMaterializationPublicationError(
            "successful result lacks prepared effect"
        )
    values: list[SemanticValueCoordinate] = [effect.effect_body]
    if result.current_result is not None:
        values.append(result.current_result)
    if result.transition is not None:
        values.extend((result.transition.result, result.transition.transition_body))
    values.extend(effect.renderer_inputs)
    values.extend(item.output for item in result.outputs)
    unique = {canonical_json_bytes(item.to_wire()): item for item in values}
    return tuple(unique[key] for key in sorted(unique))


def _stored_publication_contract(value: JsonObject) -> str:
    root = _v2_wire_mapping(_thaw_state_json(value), "stored publication head")
    contract = root.get("contract")
    if type(contract) is not str:
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication head contract must be exact string"
        )
    return contract


def _stored_publication_head_v2(
    value: JsonObject,
) -> WorkspaceSemanticMaterializationHeadV3:
    root = _v2_wire_mapping(_thaw_state_json(value), "stored publication head V2")
    head = _parse_publication_head_v2_wire(root)
    if canonical_json_bytes(root) != encode_workspace_semantic_materialization_head_v2(
        head
    ):
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication head V2 is not canonical"
        )
    return head


def _stored_publication_head_v4(
    value: JsonObject,
) -> WorkspaceSemanticMaterializationHeadV4:
    root = _v2_wire_mapping(_thaw_state_json(value), "stored publication head V4")
    head = _parse_publication_head_v4_wire(root)
    if canonical_json_bytes(root) != canonical_json_bytes(head.to_wire()):
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication head V4 is not canonical"
        )
    return head


def _v2_wire_mapping(value: object, field: str) -> dict[str, object]:
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise WorkspaceSemanticMaterializationPublicationError(
            f"{field} must be exact string-keyed object"
        )
    return cast(dict[str, object], value)


def _v2_wire_keys(value: object, expected: set[str], field: str) -> dict[str, object]:
    root = _v2_wire_mapping(value, field)
    if set(root) != expected:
        raise WorkspaceSemanticMaterializationPublicationError(f"{field} fields differ")
    return root


def _parse_v2_digest_wire(value: object, field: str) -> ContentDigest:
    try:
        return ContentDigest.of_wire(value, field)
    except (ContractViolation, TypeError, ValueError) as error:
        raise WorkspaceSemanticMaterializationPublicationError(
            f"{field} digest differs"
        ) from error


def _parse_v2_package_wire(value: object, field: str) -> SemanticPackageCoordinate:
    root = _v2_wire_keys(
        value, {"manifest_digest", "package_kind", "package_ref"}, field
    )
    try:
        result = SemanticPackageCoordinate(
            package_ref=_string(root["package_ref"], f"{field}.package_ref"),
            package_kind=_string(root["package_kind"], f"{field}.package_kind"),
            manifest_digest=_parse_v2_digest_wire(
                root["manifest_digest"], f"{field}.manifest_digest"
            ),
        )
    except (ContractViolation, TypeError, ValueError) as error:
        raise WorkspaceSemanticMaterializationPublicationError(
            f"{field} package differs"
        ) from error
    if canonical_json_bytes(result.to_wire()) != canonical_json_bytes(root):
        raise WorkspaceSemanticMaterializationPublicationError(
            f"{field} package is not canonical"
        )
    return result


def _parse_v2_contract_wire(value: object, field: str) -> SemanticContractRef:
    root = _v2_wire_keys(value, {"key", "schema_digest", "version"}, field)
    try:
        result = SemanticContractRef(
            key=_string(root["key"], f"{field}.key"),
            version=_string(root["version"], f"{field}.version"),
            schema_digest=_parse_v2_digest_wire(
                root["schema_digest"], f"{field}.schema_digest"
            ),
        )
    except (ContractViolation, TypeError, ValueError) as error:
        raise WorkspaceSemanticMaterializationPublicationError(
            f"{field} contract differs"
        ) from error
    if canonical_json_bytes(result.to_wire()) != canonical_json_bytes(root):
        raise WorkspaceSemanticMaterializationPublicationError(
            f"{field} contract is not canonical"
        )
    return result


def _parse_v2_coordinate_wire(value: object, field: str) -> SemanticValueCoordinate:
    root = _v2_wire_keys(
        value,
        {"contract", "digest", "role", "size_bytes", "value_ref"},
        field,
    )
    try:
        result = SemanticValueCoordinate(
            role=_string(root["role"], f"{field}.role"),
            contract=_parse_v2_contract_wire(root["contract"], f"{field}.contract"),
            value_ref=_string(root["value_ref"], f"{field}.value_ref"),
            digest=_parse_v2_digest_wire(root["digest"], f"{field}.digest"),
            size_bytes=_nonnegative_int(root["size_bytes"], f"{field}.size_bytes"),
        )
    except (ContractViolation, TypeError, ValueError) as error:
        raise WorkspaceSemanticMaterializationPublicationError(
            f"{field} coordinate differs"
        ) from error
    if canonical_json_bytes(result.to_wire()) != canonical_json_bytes(root):
        raise WorkspaceSemanticMaterializationPublicationError(
            f"{field} coordinate is not canonical"
        )
    return result


def _parse_publication_request_v2_wire(
    value: object,
) -> WorkspaceSemanticMaterializationRequestV3:
    field = "stored publication request V2"
    root = _v2_wire_keys(
        value,
        {
            "code_intent_digest",
            "code_match_digest",
            "planning_input_digest",
            "contract",
            "execution_input_closure_digest",
            "expected_head_revision",
            "operation_result_digest",
            "package",
            "request_digest",
            "result_coordinate",
            "source_identity_digest",
        },
        field,
    )
    if root["contract"] != WORKSPACE_SEMANTIC_MATERIALIZATION_REQUEST_V3:
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication request V2 contract differs"
        )
    result = WorkspaceSemanticMaterializationRequestV3.create(
        package=_parse_v2_package_wire(root["package"], f"{field}.package"),
        result_coordinate=_parse_v2_coordinate_wire(
            root["result_coordinate"], f"{field}.result_coordinate"
        ),
        source_identity_digest=_parse_v2_digest_wire(
            root["source_identity_digest"], f"{field}.source_identity_digest"
        ),
        code_intent_digest=_parse_v2_digest_wire(
            root["code_intent_digest"], f"{field}.code_intent_digest"
        ),
        code_match_digest=_parse_v2_digest_wire(
            root["code_match_digest"], f"{field}.code_match_digest"
        ),
        planning_input_digest=_parse_v2_digest_wire(
            root["planning_input_digest"], f"{field}.planning_input_digest"
        ),
        execution_input_closure_digest=_parse_v2_digest_wire(
            root["execution_input_closure_digest"],
            f"{field}.execution_input_closure_digest",
        ),
        operation_result_digest=_parse_v2_digest_wire(
            root["operation_result_digest"], f"{field}.operation_result_digest"
        ),
        expected_head_revision=_nonnegative_int(
            root["expected_head_revision"], f"{field}.expected_head_revision"
        ),
    )
    if _parse_v2_digest_wire(
        root["request_digest"], f"{field}.request_digest"
    ) != result.request_digest or canonical_json_bytes(
        root
    ) != encode_workspace_semantic_materialization_request_v2(result):
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication request V2 differs from fresh derivation"
        )
    return result


def _parse_publication_head_v2_wire(
    value: object,
) -> WorkspaceSemanticMaterializationHeadV3:
    field = "stored publication head V2"
    root = _v2_wire_keys(
        value,
        {
            "code_intent_digest",
            "code_match_digest",
            "planning_input_digest",
            "contract",
            "execution_input_closure_digest",
            "head_digest",
            "operation_result_digest",
            "package",
            "request",
            "result_coordinate",
            "source_identity_digest",
        },
        field,
    )
    if root["contract"] != WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V3:
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication head V2 contract differs"
        )
    request = _parse_publication_request_v2_wire(root["request"])
    result = WorkspaceSemanticMaterializationHeadV3.create(request=request)
    if _parse_v2_digest_wire(
        root["head_digest"], f"{field}.head_digest"
    ) != result.head_digest or canonical_json_bytes(
        root
    ) != encode_workspace_semantic_materialization_head_v2(result):
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication head V2 differs from fresh derivation"
        )
    return result


def _parse_publication_output_state_binding_v4_wire(
    value: object, field: str
) -> WorkspaceSemanticMaterializationOutputStateBindingV4:
    root = _v2_wire_keys(
        value,
        {
            "contract",
            "output_coordinate",
            "output_state_name",
            "prior_state_body_ref",
            "prior_state_body_digest",
            "prior_state_body_size",
            "prior_state_digest",
            "state_body_ref",
            "state_body_digest",
            "state_body_size",
            "state_digest",
        },
        field,
    )
    if root["contract"] != WORKSPACE_SEMANTIC_MATERIALIZATION_OUTPUT_STATE_BINDING_V4:
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored output binding V4 contract differs"
        )
    result = WorkspaceSemanticMaterializationOutputStateBindingV4(
        output_coordinate=_parse_v2_coordinate_wire(
            root["output_coordinate"], f"{field}.output_coordinate"
        ),
        output_state_name=_string(
            root["output_state_name"], f"{field}.output_state_name"
        ),
        prior_state_body_ref=_string(
            root["prior_state_body_ref"], f"{field}.prior_state_body_ref"
        ),
        prior_state_body_digest=_parse_v2_digest_wire(
            root["prior_state_body_digest"], f"{field}.prior_state_body_digest"
        ),
        prior_state_body_size=_nonnegative_int(
            root["prior_state_body_size"], f"{field}.prior_state_body_size"
        ),
        prior_state_digest=_parse_v2_digest_wire(
            root["prior_state_digest"], f"{field}.prior_state_digest"
        ),
        state_body_ref=_string(root["state_body_ref"], f"{field}.state_body_ref"),
        state_body_digest=_parse_v2_digest_wire(
            root["state_body_digest"], f"{field}.state_body_digest"
        ),
        state_body_size=_nonnegative_int(
            root["state_body_size"], f"{field}.state_body_size"
        ),
        state_digest=_parse_v2_digest_wire(
            root["state_digest"], f"{field}.state_digest"
        ),
    )
    if canonical_json_bytes(root) != canonical_json_bytes(result.to_wire()):
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored output binding V4 differs from fresh derivation"
        )
    return result


def _parse_publication_occurrence_v4_wire(
    value: object,
) -> WorkspaceMaterializationPackageOccurrenceV4:
    field = "stored publication package occurrence V4"
    fields = {
        "repository_ref", "workspace_ref", "module_ref", "package_id",
        "package_root", "manifest_relative_path",
    }
    root = _v2_wire_keys(value, fields, field)
    return WorkspaceMaterializationPackageOccurrenceV4(
        **{name: _string(root[name], f"{field}.{name}") for name in fields}
    )


def _parse_publication_head_v4_wire(
    value: object,
) -> WorkspaceSemanticMaterializationHeadV4:
    field = "stored publication head V4"
    root = _v2_wire_keys(
        value,
        {
            "base_head",
            "contract",
            "head_digest",
            "operation_digest",
            "operation_ref",
            "output_state_bindings",
            "package_occurrence",
            "predecessor_head_digest",
        },
        field,
    )
    if root["contract"] != WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4:
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication head V4 contract differs"
        )
    base = _parse_publication_head_v2_wire(root["base_head"])
    bindings_wire = root["output_state_bindings"]
    if type(bindings_wire) is not list:
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication head V4 bindings must be exact list"
        )
    bindings = tuple(
        _parse_publication_output_state_binding_v4_wire(
            item, f"{field}.binding[{index}]"
        )
        for index, item in enumerate(bindings_wire)
    )
    result = WorkspaceSemanticMaterializationHeadV4.create(
        request=base.request,
        package_occurrence=_parse_publication_occurrence_v4_wire(
            root["package_occurrence"]
        ),
        predecessor_head_digest=(
            None if root["predecessor_head_digest"] is None
            else _parse_v2_digest_wire(
                root["predecessor_head_digest"],
                f"{field}.predecessor_head_digest",
            )
        ),
        operation_ref=_string(root["operation_ref"], f"{field}.operation_ref"),
        operation_digest=_parse_v2_digest_wire(
            root["operation_digest"], f"{field}.operation_digest"
        ),
        output_state_bindings=bindings,
    )
    if (
        _parse_v2_digest_wire(root["head_digest"], f"{field}.head_digest")
        != result.head_digest
        or canonical_json_bytes(root) != canonical_json_bytes(result.to_wire())
    ):
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication head V4 differs from fresh derivation"
        )
    return result


def _parse_publication_receipt_v2_wire(
    value: object,
) -> WorkspaceSemanticMaterializationPublicationReceiptV3:
    field = "stored publication receipt V2"
    root = _v2_wire_keys(
        value,
        {
            "canonical_head_wire_digest",
            "contract",
            "head",
            "head_advanced",
            "head_revision",
            "prior_head_revision",
            "receipt_digest",
            "request",
        },
        field,
    )
    if root["contract"] != WORKSPACE_SEMANTIC_MATERIALIZATION_RECEIPT_V3:
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication receipt V2 contract differs"
        )
    request = _parse_publication_request_v2_wire(root["request"])
    head = _parse_publication_head_v2_wire(root["head"])
    advanced = root["head_advanced"]
    if type(advanced) is not bool:
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication receipt V2 advancement must be exact bool"
        )
    result = WorkspaceSemanticMaterializationPublicationReceiptV3.create(
        request=request,
        head=head,
        prior_head_revision=_nonnegative_int(
            root["prior_head_revision"], f"{field}.prior_head_revision"
        ),
        head_revision=_nonnegative_int(root["head_revision"], f"{field}.head_revision"),
        head_advanced=advanced,
    )
    if canonical_json_bytes(
        root
    ) != encode_workspace_semantic_materialization_publication_receipt_v2(result):
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication receipt V2 differs from fresh derivation"
        )
    return result


def _parse_publication_receipt_v4_wire(
    value: object,
) -> WorkspaceSemanticMaterializationPublicationReceiptV4:
    field = "stored publication receipt V4"
    root = _v2_wire_keys(
        value,
        {
            "canonical_head_wire_digest",
            "contract",
            "head",
            "head_advanced",
            "head_revision",
            "prior_head_revision",
            "receipt_digest",
            "request",
        },
        field,
    )
    if root["contract"] != WORKSPACE_SEMANTIC_MATERIALIZATION_RECEIPT_V4:
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication receipt V4 contract differs"
        )
    advanced = root["head_advanced"]
    if type(advanced) is not bool:
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication receipt V4 advancement must be exact bool"
        )
    result = WorkspaceSemanticMaterializationPublicationReceiptV4.create(
        request=_parse_publication_request_v2_wire(root["request"]),
        head=_parse_publication_head_v4_wire(root["head"]),
        prior_head_revision=_nonnegative_int(
            root["prior_head_revision"], f"{field}.prior_head_revision"
        ),
        head_revision=_nonnegative_int(
            root["head_revision"], f"{field}.head_revision"
        ),
        head_advanced=advanced,
    )
    if canonical_json_bytes(root) != canonical_json_bytes(result.to_wire()):
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication receipt V4 differs from fresh derivation"
        )
    return result


def _parse_head_reread_evidence_v4_wire(
    value: object,
) -> WorkspaceSemanticMaterializationHeadRereadEvidenceV4:
    field = "stored publication head reread V4"
    root = _v2_wire_keys(
        value,
        {
            "canonical_head_wire_digest",
            "contract",
            "head",
            "materialization_head_digest",
            "materialization_head_revision",
            "observation_role",
            "reread_evidence_digest",
        },
        field,
    )
    if root["contract"] != WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_REREAD_EVIDENCE_V4:
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication head reread V4 contract differs"
        )
    result = WorkspaceSemanticMaterializationHeadRereadEvidenceV4.create(
        observation_role=_string(root["observation_role"], f"{field}.observation_role"),
        materialization_head_revision=_nonnegative_int(
            root["materialization_head_revision"],
            f"{field}.materialization_head_revision",
        ),
        head=_parse_publication_head_v4_wire(root["head"]),
    )
    if canonical_json_bytes(root) != canonical_json_bytes(result.to_wire()):
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication head reread V4 differs from fresh derivation"
        )
    return result


def _parse_head_reread_evidence_v2_wire(
    value: object,
) -> WorkspaceSemanticMaterializationHeadRereadEvidenceV3:
    field = "stored publication head reread V2"
    root = _v2_wire_keys(
        value,
        {
            "canonical_head_wire_digest",
            "code_intent_digest",
            "code_match_digest",
            "planning_input_digest",
            "contract",
            "execution_input_closure_digest",
            "head",
            "materialization_head_digest",
            "materialization_head_revision",
            "observation_role",
            "package",
            "reread_evidence_digest",
            "result_coordinate",
            "source_identity_digest",
        },
        field,
    )
    if root["contract"] != WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_REREAD_EVIDENCE_V3:
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication head reread V2 contract differs"
        )
    head = _parse_publication_head_v2_wire(root["head"])
    result = WorkspaceSemanticMaterializationHeadRereadEvidenceV3.create(
        observation_role=_string(root["observation_role"], f"{field}.observation_role"),
        materialization_head_revision=_nonnegative_int(
            root["materialization_head_revision"],
            f"{field}.materialization_head_revision",
        ),
        head=head,
    )
    if canonical_json_bytes(
        root
    ) != encode_workspace_semantic_materialization_head_reread_evidence_v2(result):
        raise WorkspaceSemanticMaterializationPublicationError(
            "stored publication head reread V2 differs from fresh derivation"
        )
    return result


def _head_payload(values: dict[str, object]) -> dict[str, object]:
    candidate = cast(WorkspacePublishedSemanticCoordinate, values["candidate"])
    outputs = cast(tuple[WorkspacePublishedSemanticCoordinate, ...], values["outputs"])
    bodies = cast(tuple[WorkspaceStagedSemanticBody, ...], values["semantic_bodies"])
    return {
        "package_ref": values["package_ref"],
        "package_kind": values["package_kind"],
        "manifest_digest": values["manifest_digest"],
        "source_authority_ref": values["source_authority_ref"],
        "source_authority_digest": values["source_authority_digest"],
        "request_ref": values["request_ref"],
        "request_digest": values["request_digest"],
        "operation_ref": values["operation_ref"],
        "operation_digest": values["operation_digest"],
        "invocation_digest": values["invocation_digest"],
        "profile_digest": values["profile_digest"],
        "terminal_status": values["terminal_status"],
        "result_digest": values["result_digest"],
        "result_body_ref": values["result_body_ref"],
        "result_body_digest": values["result_body_digest"],
        "result_body_size_bytes": values["result_body_size_bytes"],
        "candidate": candidate.to_dict(),
        "transition_digest": values["transition_digest"],
        "effect_digest": values["effect_digest"],
        "outputs": [item.to_dict() for item in outputs],
        "semantic_bodies": [item.to_dict() for item in bodies],
        "output_activation": values["output_activation"],
    }


def _receipt_payload(values: dict[str, object]) -> dict[str, object]:
    head = cast(WorkspaceSemanticMaterializationHead, values["head"])
    bodies = cast(
        tuple[WorkspaceStagedSemanticBody, ...],
        values["observed_semantic_bodies"],
    )
    return {
        "head": head.to_dict(),
        "observed_result_digest": values["observed_result_digest"],
        "observed_result_body_ref": values["observed_result_body_ref"],
        "observed_result_body_digest": values["observed_result_body_digest"],
        "observed_semantic_bodies": [item.to_dict() for item in bodies],
        "prior_head_revision": values["prior_head_revision"],
        "head_revision": values["head_revision"],
        "head_advanced": values["head_advanced"],
    }


class WorkspaceAuthorityPredecessorAdmission:
    """Nominal operation-bound handle; portable equality grants no authority."""

    __slots__ = ()

    def __new__(cls):
        raise TypeError("authority predecessor admissions are runtime-issued")

    def __reduce__(self):
        raise TypeError("authority predecessor admissions cannot be serialized")


@dataclass(frozen=True, slots=True)
class WorkspaceAuthorityPredecessorEvidence:
    disposition: str
    predecessor: TypedEmptyCoordinate | SemanticValueCoordinate
    predecessor_body: SemanticBody | None
    materialization_head_revision: int
    materialization_head_digest: ContentDigest | None

    def __post_init__(self) -> None:
        if self.disposition not in {"genesis", "current"}:
            raise WorkspaceSemanticMaterializationPublicationError(
                "authority predecessor disposition unsupported"
            )
        _nonnegative_int(
            self.materialization_head_revision,
            "authority_predecessor.materialization_head_revision",
        )
        if self.disposition == "genesis":
            if (
                type(self.predecessor) is not TypedEmptyCoordinate
                or self.predecessor_body is not None
                or self.materialization_head_revision != 0
                or self.materialization_head_digest is not None
            ):
                raise WorkspaceSemanticMaterializationPublicationError(
                    "genesis predecessor evidence differs"
                )
            self.predecessor.__post_init__()
            return
        if (
            type(self.predecessor) is not SemanticValueCoordinate
            or type(self.predecessor_body) is not SemanticBody
            or type(self.materialization_head_digest) is not ContentDigest
            or self.materialization_head_revision < 1
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "current predecessor evidence differs"
            )
        self.predecessor.__post_init__()
        self.predecessor_body.__post_init__()
        self.materialization_head_digest.__post_init__()
        if self.predecessor_body.coordinate != self.predecessor:
            raise WorkspaceSemanticMaterializationPublicationError(
                "predecessor body coordinate differs"
            )


@dataclass(frozen=True, slots=True)
class _WorkspaceAuthorityPredecessorRecord:
    authority_context: object
    authority_expected: RetainedSemanticAdmissionExpectation
    execution_identity: object
    result_contract: SemanticContractRef
    evidence: WorkspaceAuthorityPredecessorEvidence


class WorkspaceAuthorityPredecessorIssuerRuntime:
    """Issue predecessor/genesis evidence from the existing Workspace head rail."""

    _pid: int
    _lock: RLock
    _closed: bool
    _publisher: WorkspaceSemanticMaterializationPublisher
    _command_runtime: Any
    _command_parent: object
    _catalog_host: Any
    _catalog_epoch: object
    _catalog_expected: CatalogPairEpochExpectation
    _records: dict[
        WorkspaceAuthorityPredecessorAdmission,
        _WorkspaceAuthorityPredecessorRecord,
    ]
    _issued: set[tuple[object, object]]
    _output_reads: dict[
        WorkspaceAuthorityPredecessorAdmission, tuple[str, str, str]
    ]
    _entrances: dict[str, tuple[Any, str, object, Any]]

    def __init__(self, *args, **kwargs):
        raise TypeError("authority predecessor issuer requires fixed composition")

    @classmethod
    def _assemble(
        cls,
        *,
        publisher: WorkspaceSemanticMaterializationPublisher,
        command_runtime: object,
        command_parent: object,
        catalog_host: object,
        catalog_epoch: object,
        catalog_expected: CatalogPairEpochExpectation,
        authority_validator: object,
    ) -> WorkspaceAuthorityPredecessorIssuerRuntime:
        from .command_lifetime import WorkspaceCommandLifetimeRuntime
        from .semantic_catalog_host import WorkspaceSemanticCatalogHost

        if type(publisher) is not WorkspaceSemanticMaterializationPublisher:
            raise TypeError("exact Workspace materialization publisher required")
        if type(command_runtime) is not WorkspaceCommandLifetimeRuntime:
            raise TypeError("exact Workspace command runtime required")
        if type(catalog_host) is not WorkspaceSemanticCatalogHost:
            raise TypeError("exact Workspace catalog host required")
        if type(catalog_expected) is not CatalogPairEpochExpectation:
            raise TypeError("exact Code catalog epoch expectation required")
        result = object.__new__(cls)
        result._pid = os.getpid()
        result._lock = RLock()
        result._closed = False
        result._publisher = publisher
        result._command_runtime = command_runtime
        result._command_parent = command_parent
        result._catalog_host = catalog_host
        result._catalog_epoch = catalog_epoch
        result._catalog_expected = catalog_expected
        result._records = {}
        result._issued = set()
        result._output_reads = {}
        result._entrances = {}
        for key, receiver, name in (
            ("parent", command_runtime, "validate_direct_invocation_parent"),
            ("epoch", catalog_host, "validate_current_catalog_epoch"),
            (
                "authority",
                authority_validator,
                "validate_retained_semantic_operation_context",
            ),
        ):
            descriptor = inspect.getattr_static(receiver, name)
            method = getattr(receiver, name)
            if (
                not inspect.ismethod(method)
                or method.__self__ is not receiver
                or method.__func__ is not descriptor
            ):
                raise TypeError("original authority predecessor entrance required")
            result._entrances[key] = receiver, name, descriptor, method
        result._check_lifetime()
        return result

    def _process(self) -> None:
        if os.getpid() != self._pid:
            raise WorkspaceSemanticMaterializationPublicationError(
                "authority predecessor process changed"
            )

    def _call(self, key: str, *args, **kwargs):
        receiver, name, descriptor, method = self._entrances[key]
        if inspect.getattr_static(receiver, name) is not descriptor:
            raise WorkspaceSemanticMaterializationPublicationError(
                f"authority predecessor {key} entrance substituted"
            )
        result = method(*args, **kwargs)
        if inspect.getattr_static(receiver, name) is not descriptor:
            raise WorkspaceSemanticMaterializationPublicationError(
                f"authority predecessor {key} entrance substituted"
            )
        return result

    def _check_lifetime(self) -> None:
        self._process()
        if self._closed:
            raise WorkspaceSemanticMaterializationPublicationError(
                "authority predecessor issuer closed"
            )
        self._call(
            "parent",
            self._command_parent,
            expected=self._catalog_expected.invocation,
        )
        self._call("epoch", self._catalog_epoch, expected=self._catalog_expected)

    @staticmethod
    def _check_expected(
        authority_expected: RetainedSemanticAdmissionExpectation,
        execution_identity: object,
        result_contract: SemanticContractRef,
    ) -> None:
        if (
            type(authority_expected) is not RetainedSemanticAdmissionExpectation
            or authority_expected.stage != "authority_derivation"
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "exact authority-stage expectation required"
            )
        if execution_identity is None:
            raise WorkspaceSemanticMaterializationPublicationError(
                "fresh authority execution identity required"
            )
        if type(result_contract) is not SemanticContractRef:
            raise TypeError("exact authority result contract required")
        result_contract.__post_init__()

    def _validate_context(self, authority_context, authority_expected) -> None:
        self._check_lifetime()
        if (
            authority_expected.generation_identity
            is not self._catalog_expected.invocation.lifetime_epoch_identity
            or authority_expected.process_id
            != self._catalog_expected.invocation.process_id
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "authority context differs from command/catalog lifetime"
            )
        if (
            self._call("authority", authority_context, expected=authority_expected)
            is not None
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "authority context validator returned a value"
            )
        self._check_lifetime()

    def _observe(self, package, result_contract):
        record = self._publisher._state_store.read(
            self._publisher._state_namespace, package.package_ref
        )
        if record is None or record.value is None:
            return WorkspaceAuthorityPredecessorEvidence(
                "genesis", TypedEmptyCoordinate(result_contract), None, 0, None
            )
        if (
            _stored_publication_contract(record.value)
            == WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4
        ):
            observed = self._publisher._read_graph_v4_head_evidence(
                package.package_ref, observation_role="package_reuse"
            )
            if observed is None:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "current V4 head disappeared"
                )
            observed.__post_init__()
            revision = observed.materialization_head_revision
            head = observed.head
            observed_package = head.base_head.package
            result_coordinate = head.base_head.result_coordinate
            head_digest = observed.materialization_head_digest
        else:
            observed = self._publisher._read_graph_v2_head(
                package.package_ref, observation_role="package_reuse"
            )
            if observed is None:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "current V3 head disappeared"
                )
            observed.__post_init__()
            revision = observed.materialization_head_revision
            observed_package = observed.package
            result_coordinate = observed.result_coordinate
            head_digest = observed.materialization_head_digest
        if observed_package != package:
            raise WorkspaceSemanticMaterializationPublicationError(
                "current predecessor package differs"
            )
        if result_coordinate.contract != result_contract:
            raise WorkspaceSemanticMaterializationPublicationError(
                "current predecessor result contract differs"
            )
        return WorkspaceAuthorityPredecessorEvidence(
            "current",
            result_coordinate,
            self._publisher._read_graph_v2_body(result_coordinate),
            revision,
            head_digest,
        )

    def issue_authority_predecessor(
        self,
        authority_context,
        *,
        authority_expected,
        execution_identity,
        result_contract,
    ):
        self._check_expected(authority_expected, execution_identity, result_contract)
        with self._lock:
            self._validate_context(authority_context, authority_expected)
            key = (authority_expected.operation_identity, execution_identity)
            if key in self._issued:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "authority predecessor issuance replay"
                )
            evidence = self._observe(authority_expected.package, result_contract)
            self._validate_context(authority_context, authority_expected)
            if self._observe(authority_expected.package, result_contract) != evidence:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "authority predecessor changed during issuance"
                )
            admission = object.__new__(WorkspaceAuthorityPredecessorAdmission)
            self._records[admission] = _WorkspaceAuthorityPredecessorRecord(
                authority_context,
                authority_expected,
                execution_identity,
                result_contract,
                evidence,
            )
            self._issued.add(key)
            return admission

    def _record(
        self,
        admission,
        authority_context,
        authority_expected,
        execution_identity,
        result_contract,
    ):
        self._check_expected(authority_expected, execution_identity, result_contract)
        if type(admission) is not WorkspaceAuthorityPredecessorAdmission:
            raise TypeError("exact authority predecessor admission required")
        record = self._records.get(admission)
        if (
            record is None
            or authority_context is not record.authority_context
            or execution_identity is not record.execution_identity
            or authority_expected != record.authority_expected
            or result_contract != record.result_contract
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "authority predecessor admission context differs"
            )
        self._validate_context(authority_context, authority_expected)
        if (
            self._observe(authority_expected.package, result_contract)
            != record.evidence
        ):
            raise WorkspaceSemanticMaterializationPublicationError(
                "authority predecessor is no longer current"
            )
        self._validate_context(authority_context, authority_expected)
        return record

    def read_authority_predecessor(
        self,
        admission,
        *,
        authority_context,
        authority_expected,
        execution_identity,
        result_contract,
    ):
        with self._lock:
            return deepcopy(
                self._record(
                    admission,
                    authority_context,
                    authority_expected,
                    execution_identity,
                    result_contract,
                ).evidence
            )

    def validate_authority_predecessor_admission(
        self,
        admission,
        *,
        authority_context,
        authority_expected,
        execution_identity,
        result_contract,
    ) -> None:
        with self._lock:
            self._record(
                admission,
                authority_context,
                authority_expected,
                execution_identity,
                result_contract,
            )

    def _current_output_state(
        self,
        record: _WorkspaceAuthorityPredecessorRecord,
        *,
        output_role: str,
        output_state_name: str,
    ) -> CodePackageOutputState:
        if record.evidence.disposition != "current":
            raise WorkspaceSemanticMaterializationPublicationError(
                "SDK output genesis requires lineage-negative admission"
            )
        return self._publisher._read_graph_v4_current_output_state(
            package=record.authority_expected.package,
            expected_head_revision=record.evidence.materialization_head_revision,
            expected_head_digest=record.evidence.materialization_head_digest,
            declaration=record.authority_expected.provider_declaration,
            output_role=output_role,
            output_state_name=output_state_name,
        )

    def read_authority_output_state(
        self,
        admission,
        *,
        authority_context,
        authority_expected,
        execution_identity,
        result_contract,
        output_role,
        output_state_name,
    ) -> CodePackageOutputState:
        """Read once through the original authority predecessor admission."""

        role = _token(output_role, "output_role")
        name = _token(output_state_name, "output_state_name")
        with self._lock:
            record = self._record(
                admission,
                authority_context,
                authority_expected,
                execution_identity,
                result_contract,
            )
            if admission in self._output_reads:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "authority output-state read replay"
                )
            state = self._current_output_state(
                record, output_role=role, output_state_name=name
            )
            self._record(
                admission,
                authority_context,
                authority_expected,
                execution_identity,
                result_contract,
            )
            self._output_reads[admission] = role, name, state.state_digest
            return state

    def validate_authority_output_state_admission(
        self,
        admission,
        *,
        authority_context,
        authority_expected,
        execution_identity,
        result_contract,
        output_role,
        output_state_name,
    ) -> None:
        role = _token(output_role, "output_role")
        name = _token(output_state_name, "output_state_name")
        with self._lock:
            record = self._record(
                admission,
                authority_context,
                authority_expected,
                execution_identity,
                result_contract,
            )
            retained = self._output_reads.get(admission)
            if retained is None or retained[:2] != (role, name):
                raise WorkspaceSemanticMaterializationPublicationError(
                    "authority output-state original read differs"
                )
            state = self._current_output_state(
                record, output_role=role, output_state_name=name
            )
            if state.state_digest != retained[2]:
                raise WorkspaceSemanticMaterializationPublicationError(
                    "authority output state changed"
                )
            self._record(
                admission,
                authority_context,
                authority_expected,
                execution_identity,
                result_contract,
            )

    def close(self) -> None:
        self._process()
        with self._lock:
            self._closed = True
            self._records.clear()
            self._issued.clear()
            self._output_reads.clear()


def _semantic_digest(contract: str, payload: object) -> str:
    return ContentDigest.of_bytes(
        canonical_json_bytes({"contract": contract, "value": payload})
    ).value


def _body_ref(digest: str) -> str:
    return "cas://workspace-semantic-materialization/body/" + _digest(
        digest, "body digest"
    ).removeprefix(_DIGEST_PREFIX)


def _digest_from_body_ref(body_ref: str) -> str:
    prefix = "cas://workspace-semantic-materialization/body/"
    value = _token(body_ref, "body_ref")
    if not value.startswith(prefix) or len(value) != len(prefix) + 64:
        raise WorkspaceSemanticMaterializationPublicationError(
            "semantic body ref schema unsupported"
        )
    return _digest(_DIGEST_PREFIX + value.removeprefix(prefix), "body ref digest")


def _token(value: object, field: str) -> str:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or any(character.isspace() for character in value)
    ):
        raise WorkspaceSemanticMaterializationPublicationError(
            f"{field} must be a nonempty token"
        )
    return value


def _digest(value: object, field: str) -> str:
    item = _token(value, field)
    if len(item) != 71 or not item.startswith(_DIGEST_PREFIX) or item != item.lower():
        raise WorkspaceSemanticMaterializationPublicationError(
            f"{field} must be lowercase SHA-256"
        )
    try:
        int(item[7:], 16)
    except ValueError as error:
        raise WorkspaceSemanticMaterializationPublicationError(
            f"{field} must be lowercase SHA-256"
        ) from error
    return item


def _nonnegative_int(value: object, field: str) -> int:
    if type(value) is not int or value < 0:
        raise WorkspaceSemanticMaterializationPublicationError(
            f"{field} must be a nonnegative integer"
        )
    return value


def _object(value: object, fields: set[str], label: str) -> dict[str, object]:
    if type(value) is not dict:
        raise WorkspaceSemanticMaterializationPublicationError(
            f"{label} must be an exact object"
        )
    actual = set(value)
    if actual != fields or any(type(key) is not str for key in value):
        raise WorkspaceSemanticMaterializationPublicationError(
            f"{label} fields differ: missing={sorted(fields - actual)}, "
            f"unknown={sorted(actual - fields)}"
        )
    return cast(dict[str, object], value)


def _list(value: object, field: str) -> list[object]:
    if type(value) is not list:
        raise WorkspaceSemanticMaterializationPublicationError(
            f"{field} must be a list"
        )
    return cast(list[object], value)


def _string(value: object, field: str) -> str:
    if type(value) is not str:
        raise WorkspaceSemanticMaterializationPublicationError(f"{field} must be text")
    return value


def _optional_string(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _string(value, field)


def _integer(value: object, field: str) -> int:
    if type(value) is not int:
        raise WorkspaceSemanticMaterializationPublicationError(
            f"{field} must be integer"
        )
    return value


def _exact_tuple[T](value: object, expected: type[T], field: str) -> tuple[T, ...]:
    if type(value) is not tuple or any(type(item) is not expected for item in value):
        raise TypeError(f"{field} must be an exact tuple of {expected.__name__}")
    return cast(tuple[T, ...], value)


def _thaw_state_json(value: object) -> object:
    """Copy one host-owned immutable JSON record into exact built-in values."""

    if value is None or type(value) in (str, bool, int, float):
        return value
    if isinstance(value, list):
        return [_thaw_state_json(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _thaw_state_json(item) for key, item in value.items()}
    raise WorkspaceSemanticMaterializationPublicationError(
        "operational state contains a non-JSON value"
    )


__all__ = [
    "DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_ADMISSION",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_AUTHORITY_GRADE",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_REREAD_EVIDENCE_V3",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V3",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_NON_CLAIMS",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_RECEIPT",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_RECEIPT_V3",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_REQUEST",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_REQUEST_V3",
    "DirectoryWorkspaceSemanticMaterializationBodyStore",
    "WorkspaceAuthorityPredecessorAdmission",
    "WorkspaceAuthorityPredecessorEvidence",
    "WorkspaceAuthorityPredecessorIssuerRuntime",
    "WorkspacePublishedSemanticCoordinate",
    "WorkspaceSemanticMaterializationAdmission",
    "WorkspaceSemanticMaterializationBodyStore",
    "WorkspaceSemanticMaterializationHead",
    "WorkspaceSemanticMaterializationHeadRereadEvidenceV3",
    "WorkspaceSemanticMaterializationHeadV3",
    "WorkspaceSemanticMaterializationOperationAuthority",
    "WorkspaceSemanticMaterializationPublication",
    "WorkspaceSemanticMaterializationPublicationConflict",
    "WorkspaceSemanticMaterializationPublicationError",
    "WorkspaceSemanticMaterializationPublicationMetrics",
    "WorkspaceSemanticMaterializationPublicationReceipt",
    "WorkspaceSemanticMaterializationPublicationReceiptV3",
    "WorkspaceSemanticMaterializationPublisher",
    "WorkspaceSemanticMaterializationRequest",
    "WorkspaceSemanticMaterializationRequestV3",
    "WorkspaceStagedSemanticBody",
    "admit_workspace_semantic_materialization",
    "decode_workspace_semantic_materialization_head_reread_evidence_v2",
    "decode_workspace_semantic_materialization_head_v2",
    "decode_workspace_semantic_materialization_publication_receipt_v2",
    "decode_workspace_semantic_materialization_request_v2",
    "encode_workspace_semantic_materialization_head_reread_evidence_v2",
    "encode_workspace_semantic_materialization_head_v2",
    "encode_workspace_semantic_materialization_publication_receipt_v2",
    "encode_workspace_semantic_materialization_request_v2",
]


_V5_STATE_NAMESPACE = "workspace.semantic-materialization-occurrence.v5"
_V5_INSTALLATION_CONTRACT = (
    "aware.workspace.semantic-materialization-namespace-installation.v1"
)
_V5_LINEAGE_CONTRACT = "aware.workspace.package-occurrence-lineage.v1"
_V5_OCCURRENCE_KEY_CONTRACT = "aware.workspace.package-occurrence-key.v1"
_V5_MAX_INTEGER = 9_223_372_036_854_775_807
_V5_OCCURRENCE_FIELDS = frozenset(
    (
        "repository_ref",
        "workspace_ref",
        "module_ref",
        "package_id",
        "package_root",
        "manifest_relative_path",
    )
)
_V5_INSTALLATION_FIELDS = frozenset(
    (
        "contract",
        "namespace",
        "store_binding_digest",
        "installation_ref",
        "legacy_namespace_snapshot_digest",
        "installation_digest",
    )
)


def _v5_json(value: object) -> bytes:
    return canonical_json_bytes(value)


def _v5_digest(contract: str, value: object) -> str:
    return _semantic_digest(contract, value)


def _v5_text(value: object, limit: int, *, token: bool = False) -> str:
    if type(value) is not str:
        raise WorkspaceSemanticMaterializationPublicationError("V5 exact text required")
    if not value or len(value) > limit:
        raise WorkspaceSemanticMaterializationPublicationError("V5 text bound")
    try:
        encoded = value.encode("utf-8")
    except UnicodeError as error:
        raise WorkspaceSemanticMaterializationPublicationError("V5 invalid UTF-8 text") from error
    if len(encoded) > limit:
        raise WorkspaceSemanticMaterializationPublicationError("V5 UTF-8 text bound")
    if value.strip() != value or unicodedata.normalize("NFC", value) != value:
        raise WorkspaceSemanticMaterializationPublicationError("V5 canonical nonempty NFC text required")
    if token and any(c.isspace() for c in value):
        raise WorkspaceSemanticMaterializationPublicationError("V5 token or UTF-8 bound")
    return value


def _v5_sha(value: object) -> str:
    text = _v5_text(value, 71, token=True)
    if (
        len(text) != 71
        or text[:7] != "sha256:"
        or any(c not in "0123456789abcdef" for c in text[7:])
    ):
        raise WorkspaceSemanticMaterializationPublicationError("V5 exact lowercase SHA-256 required")
    return text


def _v5_fields(value: object, fields: frozenset[str]) -> dict[str, object]:
    if type(value) is not dict:
        raise WorkspaceSemanticMaterializationPublicationError("V5 exact object required")
    mapping = cast(dict[object, object], value)
    if len(mapping) != len(fields):
        raise WorkspaceSemanticMaterializationPublicationError("V5 exact field count required")
    # Validate key types before set construction, equality or lookup. This
    # operates on detached JSON, never nominal owner/Workspace handles.
    if any(type(key) is not str for key in mapping) or frozenset(mapping) != fields:
        raise WorkspaceSemanticMaterializationPublicationError("V5 exact fields required")
    return cast(dict[str, object], value)


def _v5_no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise WorkspaceSemanticMaterializationPublicationError("V5 duplicate key")
        result[key] = value
    return result


def _v5_decode(body: bytes, limit: int) -> object:
    if type(body) is not bytes or not body or len(body) > limit:
        raise WorkspaceSemanticMaterializationPublicationError("V5 exact bounded bytes required")
    try:
        return json.loads(body.decode("utf-8"), object_pairs_hook=_v5_no_duplicates)
    except (UnicodeError, ValueError, RecursionError) as error:
        raise WorkspaceSemanticMaterializationPublicationError("V5 invalid JSON wire") from error


def _encode_v5_occurrence(value: object) -> bytes:
    fields = _v5_fields(value, _V5_OCCURRENCE_FIELDS)
    detached = {key: _v5_text(item, 512) for key, item in fields.items()}
    body = _v5_json(detached)
    if len(body) > 4096:
        raise WorkspaceSemanticMaterializationPublicationError("V5 occurrence byte bound")
    return body


def _v5_occurrence_key(value: object) -> str:
    # Incarnation, source epoch, name, version and provider are not key fields.
    detached = json.loads(_encode_v5_occurrence(value))
    return _v5_digest(_V5_OCCURRENCE_KEY_CONTRACT, detached)


def _encode_v5_lineage(value: object) -> bytes:
    fields = _v5_fields(value, frozenset(("contract", "occurrence", "incarnation_ref")))
    if _v5_text(fields["contract"], 192, token=True) != _V5_LINEAGE_CONTRACT:
        raise WorkspaceSemanticMaterializationPublicationError("V5 lineage contract")
    body = _v5_json(
        {
            "contract": _V5_LINEAGE_CONTRACT,
            "occurrence": json.loads(_encode_v5_occurrence(fields["occurrence"])),
            "incarnation_ref": _v5_text(fields["incarnation_ref"], 192, token=True),
        }
    )
    if len(body) > 8192:
        raise WorkspaceSemanticMaterializationPublicationError("V5 lineage byte bound")
    return body


def _decode_v5_lineage(body: bytes) -> dict[str, object]:
    value = _v5_decode(body, 8192)
    if _encode_v5_lineage(value) != body:
        raise WorkspaceSemanticMaterializationPublicationError("V5 noncanonical lineage bytes")
    return cast(dict[str, object], value)


def _encode_v5_namespace_installation(value: object) -> bytes:
    fields = _v5_fields(value, _V5_INSTALLATION_FIELDS)
    if _v5_text(fields["contract"], 192, token=True) != _V5_INSTALLATION_CONTRACT:
        raise WorkspaceSemanticMaterializationPublicationError("V5 installation contract")
    if _v5_text(fields["namespace"], 192, token=True) != _V5_STATE_NAMESPACE:
        raise WorkspaceSemanticMaterializationPublicationError("V5 installation namespace")
    payload = {
        "contract": _V5_INSTALLATION_CONTRACT,
        "namespace": _V5_STATE_NAMESPACE,
        "store_binding_digest": _v5_sha(fields["store_binding_digest"]),
        "installation_ref": _v5_text(fields["installation_ref"], 192, token=True),
        "legacy_namespace_snapshot_digest": _v5_sha(
            fields["legacy_namespace_snapshot_digest"]
        ),
    }
    digest = _v5_sha(fields["installation_digest"])
    if digest != _v5_digest(_V5_INSTALLATION_CONTRACT, payload):
        raise WorkspaceSemanticMaterializationPublicationError("V5 installation digest mismatch")
    body = _v5_json({**payload, "installation_digest": digest})
    if len(body) > 16384:
        raise WorkspaceSemanticMaterializationPublicationError("V5 installation byte bound")
    return body


def _decode_v5_namespace_installation(body: bytes) -> dict[str, object]:
    value = _v5_decode(body, 16384)
    if _encode_v5_namespace_installation(value) != body:
        raise WorkspaceSemanticMaterializationPublicationError("V5 noncanonical installation bytes")
    return cast(dict[str, object], value)


def _encode_v5_read_observation(value: object) -> bytes:
    if type(value) is not list:
        raise WorkspaceSemanticMaterializationPublicationError("V5 exact seven-field observation required")
    items = cast(list[object], value)
    if len(items) != 7:
        raise WorkspaceSemanticMaterializationPublicationError("V5 exact seven-field observation required")
    if type(items[0]) is not str or items[0] != "workspace_v5_read_observation_v1":
        raise WorkspaceSemanticMaterializationPublicationError("V5 observation tag")
    if type(items[6]) is not str or items[6] != "predecessor_read":
        raise WorkspaceSemanticMaterializationPublicationError("V5 observation role")
    revision = items[4]
    if type(revision) is not int or not 0 <= revision <= _V5_MAX_INTEGER:
        raise WorkspaceSemanticMaterializationPublicationError("V5 observation exact bounded revision")
    return _v5_json(
        [
            items[0],
            _v5_sha(items[1]),
            _v5_sha(items[2]),
            _v5_sha(items[3]),
            revision,
            _v5_sha(items[5]),
            items[6],
        ]
    )


def _decode_v5_read_observation(body: bytes) -> list[object]:
    value = _v5_decode(body, 1024)
    if _encode_v5_read_observation(value) != body:
        raise WorkspaceSemanticMaterializationPublicationError("V5 noncanonical observation bytes")
    return cast(list[object], value)
