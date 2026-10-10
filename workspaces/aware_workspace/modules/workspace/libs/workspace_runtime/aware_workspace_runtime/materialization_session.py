"""Durable ordered WorkspaceSession evidence over published semantic results."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from threading import RLock
from typing import Never, Protocol, cast
from weakref import WeakKeyDictionary

from aware_code_semantic_contract_runtime import ContentDigest, canonical_json_bytes
from aware_local_service_runtime import (
    JsonObject,
    LocalOperationalStateConflict,
    LocalOperationalStateStore,
)

from .semantic_materialization_publication import (
    WorkspacePublishedSemanticCoordinate,
    WorkspaceSemanticMaterializationHead,
    WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
    WorkspaceSemanticMaterializationPublicationReceipt,
    WorkspaceSemanticMaterializationPublicationReceiptV3,
    _parse_head_reread_evidence_v2_wire,
    _parse_publication_receipt_v2_wire,
)

WORKSPACE_MATERIALIZATION_SESSION_APPEND_REQUEST = (
    "aware.workspace.materialization-session-append-request.v1"
)
WORKSPACE_MATERIALIZATION_SESSION_EVENT = (
    "aware.workspace.materialization-session-event.v1"
)
WORKSPACE_MATERIALIZATION_SESSION_HEAD = (
    "aware.workspace.materialization-session-head.v1"
)
WORKSPACE_MATERIALIZATION_SESSION_FANOUT_RECEIPT = (
    "aware.workspace.materialization-session-fanout-receipt.v1"
)
WORKSPACE_MATERIALIZATION_SESSION_SNAPSHOT = (
    "aware.workspace.materialization-session-snapshot.v1"
)
WORKSPACE_MATERIALIZATION_SESSION_SOURCE_EVIDENCE_V3 = (
    "aware.workspace.materialization-session-source-evidence.v3"
)
WORKSPACE_MATERIALIZATION_SESSION_APPEND_REQUEST_V3 = (
    "aware.workspace.materialization-session-append-request.v3"
)
WORKSPACE_MATERIALIZATION_SESSION_EVENT_V3 = (
    "aware.workspace.materialization-session-event.v3"
)
WORKSPACE_MATERIALIZATION_SESSION_HEAD_V2 = (
    "aware.workspace.materialization-session-head.v2"
)
WORKSPACE_MATERIALIZATION_SESSION_EVENT_REREAD_EVIDENCE_V3 = (
    "aware.workspace.materialization-session-event-reread-evidence.v3"
)
WORKSPACE_MATERIALIZATION_SESSION_FANOUT_RECEIPT_V3 = (
    "aware.workspace.materialization-session-fanout-receipt.v3"
)
WORKSPACE_MATERIALIZATION_SESSION_EVENT_NAMESPACE = (
    "workspace.materialization-session-event.v1"
)
WORKSPACE_MATERIALIZATION_SESSION_HEAD_NAMESPACE = (
    "workspace.materialization-session-head.v1"
)
WORKSPACE_MATERIALIZATION_SESSION_NON_CLAIMS = (
    "canonical_commit",
    "canonical_replica",
    "checkout_apply",
    "oig_commit",
    "workspace_branch_head",
    "workspace_revision",
)

_DIGEST_PREFIX = "sha256:"


class WorkspaceMaterializationSessionError(RuntimeError):
    """Session evidence is malformed, unavailable, or not admitted."""


class WorkspaceMaterializationSessionConflict(WorkspaceMaterializationSessionError):
    """Expected session state is stale or a content identity collided."""


class WorkspaceMaterializationSessionAuthorityGrade(StrEnum):
    LOCAL_OPERATIONAL = "local_operational"
    WORKSPACE_AUTHORIZED_SHARED = "workspace_authorized_shared"


class WorkspaceMaterializationSessionBaselineGrade(StrEnum):
    SOURCE_HEAD_LOCAL_OPERATIONAL = "source_head_local_operational"
    WORKSPACE_REVISION_COMMITTED = "workspace_revision_committed"


class WorkspaceMaterializationSessionGapReason(StrEnum):
    EPOCH_MISMATCH = "epoch_mismatch"
    CURSOR_AHEAD = "cursor_ahead"
    RETENTION_EXCEEDED = "retention_exceeded"


class WorkspaceMaterializationSessionOperationAuthority(Protocol):
    @property
    def operation_ref(self) -> str: ...

    @property
    def operation_digest(self) -> str: ...

    @property
    def authority_grade(self) -> WorkspaceMaterializationSessionAuthorityGrade: ...

    def admits(self, request: WorkspaceMaterializationSessionAppendRequest) -> bool: ...

    def permitted_package_refs_for(
        self, request: WorkspaceMaterializationSessionAppendRequest
    ) -> tuple[str, ...]: ...


WorkspaceMaterializationSessionPackageHeadResolver = Callable[
    [str], tuple[int, WorkspaceSemanticMaterializationHead] | None
]


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationSessionAppendRequest:
    workspace_session_ref: str
    epoch: str
    participant_ref: str
    actor_ref: str
    workflow_session_ref: str
    materialization_attempt_ref: str
    branch_baseline_ref: str
    branch_baseline_digest: str
    branch_baseline_grade: str
    package_ref: str
    profile_digest: str
    source_authority_ref: str
    source_authority_digest: str
    publication_receipt_digest: str
    expected_session_head_revision: int
    expected_cursor: int
    expected_predecessor_event_digest: str | None
    operation_ref: str
    operation_digest: str
    request_digest: str
    contract: str = WORKSPACE_MATERIALIZATION_SESSION_APPEND_REQUEST

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_MATERIALIZATION_SESSION_APPEND_REQUEST:
            raise WorkspaceMaterializationSessionError(
                "append request contract differs"
            )
        for field in (
            "workspace_session_ref",
            "epoch",
            "participant_ref",
            "actor_ref",
            "workflow_session_ref",
            "materialization_attempt_ref",
            "branch_baseline_ref",
            "package_ref",
            "source_authority_ref",
            "operation_ref",
        ):
            _token(getattr(self, field), field)
        for field in (
            "branch_baseline_digest",
            "profile_digest",
            "source_authority_digest",
            "publication_receipt_digest",
            "operation_digest",
        ):
            _digest(getattr(self, field), field)
        try:
            WorkspaceMaterializationSessionBaselineGrade(self.branch_baseline_grade)
        except ValueError as error:
            raise WorkspaceMaterializationSessionError(
                "branch baseline grade unsupported"
            ) from error
        _nonnegative(
            self.expected_session_head_revision, "expected_session_head_revision"
        )
        _nonnegative(self.expected_cursor, "expected_cursor")
        if self.expected_predecessor_event_digest is None:
            if self.expected_cursor != 0 or self.expected_session_head_revision != 0:
                raise WorkspaceMaterializationSessionError(
                    "only genesis may omit predecessor event"
                )
        else:
            _digest(
                self.expected_predecessor_event_digest,
                "expected_predecessor_event_digest",
            )
            if self.expected_cursor == 0 or self.expected_session_head_revision == 0:
                raise WorkspaceMaterializationSessionError(
                    "successor requires positive expected cursor and revision"
                )
        if self.request_digest != _semantic_digest(self.contract, self._payload()):
            raise WorkspaceMaterializationSessionError(
                "append request digest mismatched"
            )

    @classmethod
    def create(
        cls,
        *,
        workspace_session_ref: str,
        epoch: str,
        participant_ref: str,
        actor_ref: str,
        workflow_session_ref: str,
        materialization_attempt_ref: str,
        branch_baseline_ref: str,
        branch_baseline_digest: str,
        branch_baseline_grade: str,
        package_ref: str,
        profile_digest: str,
        source_authority_ref: str,
        source_authority_digest: str,
        publication_receipt_digest: str,
        expected_session_head_revision: int,
        expected_cursor: int,
        expected_predecessor_event_digest: str | None,
        operation_ref: str,
        operation_digest: str,
    ) -> WorkspaceMaterializationSessionAppendRequest:
        payload: dict[str, object] = {
            "workspace_session_ref": workspace_session_ref,
            "epoch": epoch,
            "participant_ref": participant_ref,
            "actor_ref": actor_ref,
            "workflow_session_ref": workflow_session_ref,
            "materialization_attempt_ref": materialization_attempt_ref,
            "branch_baseline_ref": branch_baseline_ref,
            "branch_baseline_digest": branch_baseline_digest,
            "branch_baseline_grade": branch_baseline_grade,
            "package_ref": package_ref,
            "profile_digest": profile_digest,
            "source_authority_ref": source_authority_ref,
            "source_authority_digest": source_authority_digest,
            "publication_receipt_digest": publication_receipt_digest,
            "expected_session_head_revision": expected_session_head_revision,
            "expected_cursor": expected_cursor,
            "expected_predecessor_event_digest": expected_predecessor_event_digest,
            "operation_ref": operation_ref,
            "operation_digest": operation_digest,
        }
        return cls(
            workspace_session_ref=workspace_session_ref,
            epoch=epoch,
            participant_ref=participant_ref,
            actor_ref=actor_ref,
            workflow_session_ref=workflow_session_ref,
            materialization_attempt_ref=materialization_attempt_ref,
            branch_baseline_ref=branch_baseline_ref,
            branch_baseline_digest=branch_baseline_digest,
            branch_baseline_grade=branch_baseline_grade,
            package_ref=package_ref,
            profile_digest=profile_digest,
            source_authority_ref=source_authority_ref,
            source_authority_digest=source_authority_digest,
            publication_receipt_digest=publication_receipt_digest,
            expected_session_head_revision=expected_session_head_revision,
            expected_cursor=expected_cursor,
            expected_predecessor_event_digest=expected_predecessor_event_digest,
            operation_ref=operation_ref,
            operation_digest=operation_digest,
            request_digest=_semantic_digest(
                WORKSPACE_MATERIALIZATION_SESSION_APPEND_REQUEST, payload
            ),
        )

    def _payload(self) -> dict[str, object]:
        return {
            field: getattr(self, field)
            for field in (
                "workspace_session_ref",
                "epoch",
                "participant_ref",
                "actor_ref",
                "workflow_session_ref",
                "materialization_attempt_ref",
                "branch_baseline_ref",
                "branch_baseline_digest",
                "branch_baseline_grade",
                "package_ref",
                "profile_digest",
                "source_authority_ref",
                "source_authority_digest",
                "publication_receipt_digest",
                "expected_session_head_revision",
                "expected_cursor",
                "expected_predecessor_event_digest",
                "operation_ref",
                "operation_digest",
            )
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
        cls, value: bytes
    ) -> WorkspaceMaterializationSessionAppendRequest:
        payload = _decode_json_object(value, set(cls.__dataclass_fields__))
        result = cls(
            workspace_session_ref=_string(payload["workspace_session_ref"]),
            epoch=_string(payload["epoch"]),
            participant_ref=_string(payload["participant_ref"]),
            actor_ref=_string(payload["actor_ref"]),
            workflow_session_ref=_string(payload["workflow_session_ref"]),
            materialization_attempt_ref=_string(payload["materialization_attempt_ref"]),
            branch_baseline_ref=_string(payload["branch_baseline_ref"]),
            branch_baseline_digest=_string(payload["branch_baseline_digest"]),
            branch_baseline_grade=_string(payload["branch_baseline_grade"]),
            package_ref=_string(payload["package_ref"]),
            profile_digest=_string(payload["profile_digest"]),
            source_authority_ref=_string(payload["source_authority_ref"]),
            source_authority_digest=_string(payload["source_authority_digest"]),
            publication_receipt_digest=_string(payload["publication_receipt_digest"]),
            expected_session_head_revision=_integer(
                payload["expected_session_head_revision"]
            ),
            expected_cursor=_integer(payload["expected_cursor"]),
            expected_predecessor_event_digest=_optional_string(
                payload["expected_predecessor_event_digest"]
            ),
            operation_ref=_string(payload["operation_ref"]),
            operation_digest=_string(payload["operation_digest"]),
            request_digest=_string(payload["request_digest"]),
            contract=_string(payload["contract"]),
        )
        if result.to_json_bytes() != value:
            raise WorkspaceMaterializationSessionError(
                "append request is not canonical JSON"
            )
        return result


@dataclass(frozen=True, slots=True)
class _AdmissionState:
    request: WorkspaceMaterializationSessionAppendRequest
    authority_grade: WorkspaceMaterializationSessionAuthorityGrade
    permitted_package_refs: tuple[str, ...]


_ADMISSIONS: WeakKeyDictionary[
    WorkspaceMaterializationSessionAdmission, _AdmissionState
] = WeakKeyDictionary()
_ADMISSIONS_LOCK = RLock()


class WorkspaceMaterializationSessionAdmission:
    """Runtime-issued, nonserializable session operation admission."""

    def __new__(cls) -> WorkspaceMaterializationSessionAdmission:  # noqa: PYI034
        raise TypeError("session admission is Workspace-constructed only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("session admission is sealed")

    @property
    def request(self) -> WorkspaceMaterializationSessionAppendRequest:
        return _admission_state(self).request

    @property
    def authority_grade(self) -> WorkspaceMaterializationSessionAuthorityGrade:
        return _admission_state(self).authority_grade

    @property
    def permitted_package_refs(self) -> tuple[str, ...]:
        return _admission_state(self).permitted_package_refs

    def _assert_intact(self) -> None:
        state = _admission_state(self)
        state.request.__post_init__()
        if (
            type(state.authority_grade)
            is not WorkspaceMaterializationSessionAuthorityGrade
        ):
            raise WorkspaceMaterializationSessionError(
                "session authority grade differs"
            )
        if state.permitted_package_refs != tuple(
            sorted(set(state.permitted_package_refs))
        ):
            raise WorkspaceMaterializationSessionError(
                "session permitted packages are not canonical"
            )

    def __reduce__(self) -> Never:
        raise TypeError("session admission is not serializable")


def admit_workspace_materialization_session_append(
    *,
    request: WorkspaceMaterializationSessionAppendRequest,
    operation_authority: WorkspaceMaterializationSessionOperationAuthority,
) -> WorkspaceMaterializationSessionAdmission:
    if type(request) is not WorkspaceMaterializationSessionAppendRequest:
        raise TypeError("request must be exact session append request")
    request.__post_init__()
    if (
        _token(operation_authority.operation_ref, "operation_ref")
        != request.operation_ref
        or _digest(operation_authority.operation_digest, "operation_digest")
        != request.operation_digest
    ):
        raise WorkspaceMaterializationSessionError(
            "operation authority differs from append request"
        )
    grade = operation_authority.authority_grade
    if type(grade) is not WorkspaceMaterializationSessionAuthorityGrade:
        raise WorkspaceMaterializationSessionError("authority grade is not nominal")
    admitted = operation_authority.admits(request)
    if type(admitted) is not bool or not admitted:
        raise WorkspaceMaterializationSessionError(
            "Workspace operation did not admit session append"
        )
    permitted = operation_authority.permitted_package_refs_for(request)
    if type(permitted) is not tuple:
        raise TypeError("permitted package refs must be an exact tuple")
    normalized = tuple(
        sorted({_token(item, "permitted_package_ref") for item in permitted})
    )
    if normalized != permitted or request.package_ref not in normalized:
        raise WorkspaceMaterializationSessionError(
            "permitted package refs are not canonical or omit target"
        )
    admission = object.__new__(WorkspaceMaterializationSessionAdmission)
    with _ADMISSIONS_LOCK:
        _ADMISSIONS[admission] = _AdmissionState(request, grade, normalized)
    return admission


def _admission_state(
    admission: WorkspaceMaterializationSessionAdmission,
) -> _AdmissionState:
    if type(admission) is not WorkspaceMaterializationSessionAdmission:
        raise TypeError("admission must be exact session admission")
    with _ADMISSIONS_LOCK:
        state = _ADMISSIONS.get(admission)
    if state is None:
        raise WorkspaceMaterializationSessionError(
            "session admission is not registered by this runtime"
        )
    return state


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationSessionEvent:
    workspace_session_ref: str
    epoch: str
    authority_grade: str
    participant_ref: str
    actor_ref: str
    workflow_session_ref: str
    materialization_attempt_ref: str
    branch_baseline_ref: str
    branch_baseline_digest: str
    branch_baseline_grade: str
    cursor: int
    predecessor_event_digest: str | None
    package_ref: str
    package_kind: str
    manifest_digest: str
    profile_digest: str
    source_authority_ref: str
    source_authority_digest: str
    publication_receipt_digest: str
    materialization_head_revision: int
    materialization_head_digest: str
    result_digest: str
    result_body_ref: str
    result_body_digest: str
    outputs: tuple[WorkspacePublishedSemanticCoordinate, ...]
    event_digest: str
    contract: str = WORKSPACE_MATERIALIZATION_SESSION_EVENT
    non_claims: tuple[str, ...] = WORKSPACE_MATERIALIZATION_SESSION_NON_CLAIMS

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_MATERIALIZATION_SESSION_EVENT:
            raise WorkspaceMaterializationSessionError("session event contract differs")
        if tuple(self.non_claims) != WORKSPACE_MATERIALIZATION_SESSION_NON_CLAIMS:
            raise WorkspaceMaterializationSessionError(
                "session event non-claims differ"
            )
        for field in (
            "workspace_session_ref",
            "epoch",
            "participant_ref",
            "actor_ref",
            "workflow_session_ref",
            "materialization_attempt_ref",
            "branch_baseline_ref",
            "package_ref",
            "package_kind",
            "source_authority_ref",
            "result_body_ref",
        ):
            _token(getattr(self, field), field)
        try:
            WorkspaceMaterializationSessionAuthorityGrade(self.authority_grade)
            WorkspaceMaterializationSessionBaselineGrade(self.branch_baseline_grade)
        except ValueError as error:
            raise WorkspaceMaterializationSessionError(
                "session event authority grade unsupported"
            ) from error
        for field in (
            "branch_baseline_digest",
            "manifest_digest",
            "profile_digest",
            "source_authority_digest",
            "publication_receipt_digest",
            "materialization_head_digest",
            "result_digest",
            "result_body_digest",
        ):
            _digest(getattr(self, field), field)
        _positive(self.cursor, "cursor")
        _positive(self.materialization_head_revision, "materialization_head_revision")
        if self.cursor == 1:
            if self.predecessor_event_digest is not None:
                raise WorkspaceMaterializationSessionError(
                    "genesis event cannot have predecessor"
                )
        else:
            _digest(self.predecessor_event_digest, "predecessor_event_digest")
        if type(self.outputs) is not tuple or any(
            type(item) is not WorkspacePublishedSemanticCoordinate
            for item in self.outputs
        ):
            raise TypeError("session event outputs must be exact coordinates")
        for item in self.outputs:
            item.__post_init__()
        if self.outputs != tuple(sorted(set(self.outputs))):
            raise WorkspaceMaterializationSessionError(
                "session event outputs are not canonical"
            )
        if self.event_digest != _semantic_digest(self.contract, self._payload()):
            raise WorkspaceMaterializationSessionError(
                "session event digest mismatched"
            )

    @classmethod
    def create(
        cls,
        *,
        admission: WorkspaceMaterializationSessionAdmission,
        publication: WorkspaceSemanticMaterializationPublicationReceipt,
    ) -> WorkspaceMaterializationSessionEvent:
        state = _admission_state(admission)
        request = state.request
        head = publication.head
        values: dict[str, object] = {
            "workspace_session_ref": request.workspace_session_ref,
            "epoch": request.epoch,
            "authority_grade": state.authority_grade.value,
            "participant_ref": request.participant_ref,
            "actor_ref": request.actor_ref,
            "workflow_session_ref": request.workflow_session_ref,
            "materialization_attempt_ref": request.materialization_attempt_ref,
            "branch_baseline_ref": request.branch_baseline_ref,
            "branch_baseline_digest": request.branch_baseline_digest,
            "branch_baseline_grade": request.branch_baseline_grade,
            "cursor": request.expected_cursor + 1,
            "predecessor_event_digest": request.expected_predecessor_event_digest,
            "package_ref": head.package_ref,
            "package_kind": head.package_kind,
            "manifest_digest": head.manifest_digest,
            "profile_digest": head.profile_digest,
            "source_authority_ref": head.source_authority_ref,
            "source_authority_digest": head.source_authority_digest,
            "publication_receipt_digest": publication.receipt_digest,
            "materialization_head_revision": publication.head_revision,
            "materialization_head_digest": head.head_digest,
            "result_digest": head.result_digest,
            "result_body_ref": head.result_body_ref,
            "result_body_digest": head.result_body_digest,
            "outputs": head.outputs,
        }
        return cls(
            workspace_session_ref=request.workspace_session_ref,
            epoch=request.epoch,
            authority_grade=state.authority_grade.value,
            participant_ref=request.participant_ref,
            actor_ref=request.actor_ref,
            workflow_session_ref=request.workflow_session_ref,
            materialization_attempt_ref=request.materialization_attempt_ref,
            branch_baseline_ref=request.branch_baseline_ref,
            branch_baseline_digest=request.branch_baseline_digest,
            branch_baseline_grade=request.branch_baseline_grade,
            cursor=request.expected_cursor + 1,
            predecessor_event_digest=request.expected_predecessor_event_digest,
            package_ref=head.package_ref,
            package_kind=head.package_kind,
            manifest_digest=head.manifest_digest,
            profile_digest=head.profile_digest,
            source_authority_ref=head.source_authority_ref,
            source_authority_digest=head.source_authority_digest,
            publication_receipt_digest=publication.receipt_digest,
            materialization_head_revision=publication.head_revision,
            materialization_head_digest=head.head_digest,
            result_digest=head.result_digest,
            result_body_ref=head.result_body_ref,
            result_body_digest=head.result_body_digest,
            outputs=head.outputs,
            event_digest=_semantic_digest(
                WORKSPACE_MATERIALIZATION_SESSION_EVENT,
                _event_payload(values),
            ),
        )

    def _payload(self) -> dict[str, object]:
        return _event_payload({field: getattr(self, field) for field in _EVENT_FIELDS})

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            **self._payload(),
            "event_digest": self.event_digest,
            "non_claims": list(self.non_claims),
        }

    def to_json_bytes(self) -> bytes:
        self.__post_init__()
        return canonical_json_bytes(self.to_dict())

    @classmethod
    def from_json_bytes(cls, value: bytes) -> WorkspaceMaterializationSessionEvent:
        payload = _decode_json_object(
            value, set(_EVENT_FIELDS) | {"contract", "event_digest", "non_claims"}
        )
        result = cls(
            workspace_session_ref=_string(payload["workspace_session_ref"]),
            epoch=_string(payload["epoch"]),
            authority_grade=_string(payload["authority_grade"]),
            participant_ref=_string(payload["participant_ref"]),
            actor_ref=_string(payload["actor_ref"]),
            workflow_session_ref=_string(payload["workflow_session_ref"]),
            materialization_attempt_ref=_string(payload["materialization_attempt_ref"]),
            branch_baseline_ref=_string(payload["branch_baseline_ref"]),
            branch_baseline_digest=_string(payload["branch_baseline_digest"]),
            branch_baseline_grade=_string(payload["branch_baseline_grade"]),
            cursor=_integer(payload["cursor"]),
            predecessor_event_digest=_optional_string(
                payload["predecessor_event_digest"]
            ),
            package_ref=_string(payload["package_ref"]),
            package_kind=_string(payload["package_kind"]),
            manifest_digest=_string(payload["manifest_digest"]),
            profile_digest=_string(payload["profile_digest"]),
            source_authority_ref=_string(payload["source_authority_ref"]),
            source_authority_digest=_string(payload["source_authority_digest"]),
            publication_receipt_digest=_string(payload["publication_receipt_digest"]),
            materialization_head_revision=_integer(
                payload["materialization_head_revision"]
            ),
            materialization_head_digest=_string(payload["materialization_head_digest"]),
            result_digest=_string(payload["result_digest"]),
            result_body_ref=_string(payload["result_body_ref"]),
            result_body_digest=_string(payload["result_body_digest"]),
            outputs=tuple(
                WorkspacePublishedSemanticCoordinate.from_dict(item)
                for item in _list(payload["outputs"])
            ),
            event_digest=_string(payload["event_digest"]),
            contract=_string(payload["contract"]),
            non_claims=tuple(_string(item) for item in _list(payload["non_claims"])),
        )
        if result.to_json_bytes() != value:
            raise WorkspaceMaterializationSessionError(
                "session event is not canonical JSON"
            )
        return result


_EVENT_FIELDS = (
    "workspace_session_ref",
    "epoch",
    "authority_grade",
    "participant_ref",
    "actor_ref",
    "workflow_session_ref",
    "materialization_attempt_ref",
    "branch_baseline_ref",
    "branch_baseline_digest",
    "branch_baseline_grade",
    "cursor",
    "predecessor_event_digest",
    "package_ref",
    "package_kind",
    "manifest_digest",
    "profile_digest",
    "source_authority_ref",
    "source_authority_digest",
    "publication_receipt_digest",
    "materialization_head_revision",
    "materialization_head_digest",
    "result_digest",
    "result_body_ref",
    "result_body_digest",
    "outputs",
)


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationSessionHead:
    workspace_session_ref: str
    epoch: str
    authority_grade: str
    cursor: int
    event_digest: str
    head_digest: str
    contract: str = WORKSPACE_MATERIALIZATION_SESSION_HEAD
    non_claims: tuple[str, ...] = WORKSPACE_MATERIALIZATION_SESSION_NON_CLAIMS

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_MATERIALIZATION_SESSION_HEAD:
            raise WorkspaceMaterializationSessionError("session head contract differs")
        if tuple(self.non_claims) != WORKSPACE_MATERIALIZATION_SESSION_NON_CLAIMS:
            raise WorkspaceMaterializationSessionError("session head non-claims differ")
        _token(self.workspace_session_ref, "workspace_session_ref")
        _token(self.epoch, "epoch")
        try:
            WorkspaceMaterializationSessionAuthorityGrade(self.authority_grade)
        except ValueError as error:
            raise WorkspaceMaterializationSessionError(
                "session head authority grade unsupported"
            ) from error
        _positive(self.cursor, "cursor")
        _digest(self.event_digest, "event_digest")
        if self.head_digest != _semantic_digest(self.contract, self._payload()):
            raise WorkspaceMaterializationSessionError("session head digest mismatched")

    @classmethod
    def from_event(
        cls, event: WorkspaceMaterializationSessionEvent
    ) -> WorkspaceMaterializationSessionHead:
        values = {
            "workspace_session_ref": event.workspace_session_ref,
            "epoch": event.epoch,
            "authority_grade": event.authority_grade,
            "cursor": event.cursor,
            "event_digest": event.event_digest,
        }
        return cls(
            workspace_session_ref=event.workspace_session_ref,
            epoch=event.epoch,
            authority_grade=event.authority_grade,
            cursor=event.cursor,
            event_digest=event.event_digest,
            head_digest=_semantic_digest(
                WORKSPACE_MATERIALIZATION_SESSION_HEAD, values
            ),
        )

    def _payload(self) -> dict[str, object]:
        return {
            "workspace_session_ref": self.workspace_session_ref,
            "epoch": self.epoch,
            "authority_grade": self.authority_grade,
            "cursor": self.cursor,
            "event_digest": self.event_digest,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            **self._payload(),
            "head_digest": self.head_digest,
            "non_claims": list(self.non_claims),
        }

    def to_json_bytes(self) -> bytes:
        self.__post_init__()
        return canonical_json_bytes(self.to_dict())

    @classmethod
    def from_json_bytes(cls, value: bytes) -> WorkspaceMaterializationSessionHead:
        payload = _decode_json_object(value, set(cls.__dataclass_fields__))
        result = cls(
            workspace_session_ref=_string(payload["workspace_session_ref"]),
            epoch=_string(payload["epoch"]),
            authority_grade=_string(payload["authority_grade"]),
            cursor=_integer(payload["cursor"]),
            event_digest=_string(payload["event_digest"]),
            head_digest=_string(payload["head_digest"]),
            contract=_string(payload["contract"]),
            non_claims=tuple(_string(item) for item in _list(payload["non_claims"])),
        )
        if result.to_json_bytes() != value:
            raise WorkspaceMaterializationSessionError(
                "session head is not canonical JSON"
            )
        return result


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationSessionFanoutReceipt:
    request_digest: str
    event_digest: str
    head_digest: str
    prior_head_revision: int
    head_revision: int
    head_advanced: bool
    receipt_digest: str
    contract: str = WORKSPACE_MATERIALIZATION_SESSION_FANOUT_RECEIPT

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_MATERIALIZATION_SESSION_FANOUT_RECEIPT:
            raise WorkspaceMaterializationSessionError(
                "fanout receipt contract differs"
            )
        for field in ("request_digest", "event_digest", "head_digest"):
            _digest(getattr(self, field), field)
        _nonnegative(self.prior_head_revision, "prior_head_revision")
        _positive(self.head_revision, "head_revision")
        if type(self.head_advanced) is not bool:
            raise TypeError("head_advanced must be exact bool")
        if self.head_advanced:
            if self.head_revision != self.prior_head_revision + 1:
                raise WorkspaceMaterializationSessionError(
                    "advanced fanout revision is not contiguous"
                )
        elif self.head_revision != self.prior_head_revision:
            raise WorkspaceMaterializationSessionError(
                "current fanout receipt changed revision"
            )
        if self.receipt_digest != _semantic_digest(self.contract, self._payload()):
            raise WorkspaceMaterializationSessionError(
                "fanout receipt digest mismatched"
            )

    @classmethod
    def create(
        cls,
        *,
        request_digest: str,
        event_digest: str,
        head_digest: str,
        prior_head_revision: int,
        head_revision: int,
        head_advanced: bool,
    ) -> WorkspaceMaterializationSessionFanoutReceipt:
        values = {
            "request_digest": request_digest,
            "event_digest": event_digest,
            "head_digest": head_digest,
            "prior_head_revision": prior_head_revision,
            "head_revision": head_revision,
            "head_advanced": head_advanced,
        }
        return cls(
            request_digest=request_digest,
            event_digest=event_digest,
            head_digest=head_digest,
            prior_head_revision=prior_head_revision,
            head_revision=head_revision,
            head_advanced=head_advanced,
            receipt_digest=_semantic_digest(
                WORKSPACE_MATERIALIZATION_SESSION_FANOUT_RECEIPT, values
            ),
        )

    def _payload(self) -> dict[str, object]:
        return {
            "request_digest": self.request_digest,
            "event_digest": self.event_digest,
            "head_digest": self.head_digest,
            "prior_head_revision": self.prior_head_revision,
            "head_revision": self.head_revision,
            "head_advanced": self.head_advanced,
        }


def _session_v2_exact(value: object, expected: type[object], field: str) -> object:
    if type(value) is not expected:
        raise TypeError(f"{field} must be exact {expected.__name__}")
    return value


def _session_v2_content_digest(value: object, field: str) -> ContentDigest:
    return cast(ContentDigest, _session_v2_exact(value, ContentDigest, field))


def _session_v2_digest(contract: str, payload: object) -> ContentDigest:
    return ContentDigest.of_bytes(
        canonical_json_bytes({"contract": contract, "value": payload})
    )


def _session_v2_wire_digest(value: object, field: str) -> ContentDigest:
    del field
    return ContentDigest.of_bytes(
        canonical_json_bytes(cast(_SessionV2PortableWire, value).to_wire())
    )


class _SessionV2PortableWire(Protocol):
    def to_wire(self) -> dict[str, object]: ...


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationSessionSourceEvidenceV3:
    disposition: str
    head_reread_evidence: WorkspaceSemanticMaterializationHeadRereadEvidenceV3
    publication_receipt: WorkspaceSemanticMaterializationPublicationReceiptV3 | None
    publication_receipt_digest: ContentDigest | None
    source_evidence_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        disposition: str,
        head_reread_evidence: WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
        publication_receipt: WorkspaceSemanticMaterializationPublicationReceiptV3
        | None,
    ) -> WorkspaceMaterializationSessionSourceEvidenceV3:
        receipt_digest = (
            None
            if publication_receipt is None
            else publication_receipt.receipt_digest
            if type(publication_receipt)
            is WorkspaceSemanticMaterializationPublicationReceiptV3
            else None
        )
        values = {
            "disposition": disposition,
            "head_reread_evidence": head_reread_evidence,
            "publication_receipt": publication_receipt,
            "publication_receipt_digest": receipt_digest,
        }
        payload = _session_source_v2_payload(values)
        return cls(
            **values,
            source_evidence_digest=_session_v2_digest(
                WORKSPACE_MATERIALIZATION_SESSION_SOURCE_EVIDENCE_V3, payload
            ),
        )

    def __post_init__(self) -> None:
        values = {
            name: getattr(self, name)
            for name in (
                "disposition",
                "head_reread_evidence",
                "publication_receipt",
                "publication_receipt_digest",
            )
        }
        payload = _session_source_v2_payload(values)
        if _session_v2_content_digest(
            self.source_evidence_digest, "session_source_v2.source_evidence_digest"
        ) != _session_v2_digest(
            WORKSPACE_MATERIALIZATION_SESSION_SOURCE_EVIDENCE_V3, payload
        ):
            raise WorkspaceMaterializationSessionError(
                "session source V2 digest mismatched"
            )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_MATERIALIZATION_SESSION_SOURCE_EVIDENCE_V3,
            **_session_source_v2_payload(
                {
                    name: getattr(self, name)
                    for name in (
                        "disposition",
                        "head_reread_evidence",
                        "publication_receipt",
                        "publication_receipt_digest",
                    )
                }
            ),
            "source_evidence_digest": self.source_evidence_digest.to_wire(),
        }


def _session_source_v2_payload(values: dict[str, object]) -> dict[str, object]:
    disposition = _token(values["disposition"], "session_source_v2.disposition")
    if disposition not in {"executed", "reused"}:
        raise WorkspaceMaterializationSessionError(
            "session source V2 disposition unsupported"
        )
    head = cast(
        WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
        _session_v2_exact(
            values["head_reread_evidence"],
            WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
            "session_source_v2.head_reread_evidence",
        ),
    )
    head.__post_init__()
    receipt_value = values["publication_receipt"]
    if (
        receipt_value is not None
        and type(receipt_value)
        is not WorkspaceSemanticMaterializationPublicationReceiptV3
    ):
        raise TypeError("session source V2 publication receipt must be exact or null")
    receipt = cast(
        WorkspaceSemanticMaterializationPublicationReceiptV3 | None, receipt_value
    )
    if receipt is not None:
        receipt.__post_init__()
    digest_value = values["publication_receipt_digest"]
    if digest_value is not None and type(digest_value) is not ContentDigest:
        raise TypeError("session source V2 receipt digest must be exact or null")
    receipt_digest = cast(ContentDigest | None, digest_value)
    if disposition == "executed":
        if (
            head.observation_role != "package_result"
            or receipt is None
            or receipt_digest != receipt.receipt_digest
            or receipt.head_revision != head.materialization_head_revision
            or receipt.canonical_head_wire_digest != head.canonical_head_wire_digest
        ):
            raise WorkspaceMaterializationSessionError(
                "executed session source V2 lacks exact publication evidence"
            )
    elif (
        head.observation_role != "package_reuse"
        or receipt is not None
        or receipt_digest is not None
    ):
        raise WorkspaceMaterializationSessionError(
            "reused session source V2 carries publication evidence"
        )
    return {
        "disposition": disposition,
        "head_reread_evidence_digest": head.reread_evidence_digest.to_wire(),
        "publication_receipt_digest": (
            None if receipt_digest is None else receipt_digest.to_wire()
        ),
    }


def _create_graph_v2_session_source_evidence(
    *,
    disposition: str,
    head_reread_evidence: WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
    publication_receipt: WorkspaceSemanticMaterializationPublicationReceiptV3 | None,
) -> WorkspaceMaterializationSessionSourceEvidenceV3:
    """Bind a coordinator-authenticated head without repeating its full wire proof."""

    if (
        type(head_reread_evidence)
        is not WorkspaceSemanticMaterializationHeadRereadEvidenceV3
    ):
        raise TypeError("graph V2 source head evidence must be exact")
    if (
        publication_receipt is not None
        and type(publication_receipt)
        is not WorkspaceSemanticMaterializationPublicationReceiptV3
    ):
        raise TypeError("graph V2 publication receipt must be exact or null")
    if disposition == "reused":
        if (
            head_reread_evidence.observation_role != "package_reuse"
            or publication_receipt is not None
        ):
            raise WorkspaceMaterializationSessionError(
                "reused graph V2 source differs from its admitted head"
            )
        receipt_digest = None
    elif disposition == "executed":
        if (
            head_reread_evidence.observation_role != "package_result"
            or publication_receipt is None
            or publication_receipt.head_revision
            != head_reread_evidence.materialization_head_revision
            or publication_receipt.canonical_head_wire_digest
            != head_reread_evidence.canonical_head_wire_digest
        ):
            raise WorkspaceMaterializationSessionError(
                "executed graph V2 source differs from its publication"
            )
        receipt_digest = publication_receipt.receipt_digest
    else:
        raise WorkspaceMaterializationSessionError(
            "graph V2 source disposition unsupported"
        )
    payload = {
        "disposition": disposition,
        "head_reread_evidence_digest": head_reread_evidence.reread_evidence_digest.value,
        "publication_receipt_digest": (
            None if receipt_digest is None else receipt_digest.value
        ),
    }
    result = object.__new__(WorkspaceMaterializationSessionSourceEvidenceV3)
    object.__setattr__(result, "disposition", disposition)
    object.__setattr__(result, "head_reread_evidence", head_reread_evidence)
    object.__setattr__(result, "publication_receipt", publication_receipt)
    object.__setattr__(result, "publication_receipt_digest", receipt_digest)
    object.__setattr__(
        result,
        "source_evidence_digest",
        _session_v2_digest(
            WORKSPACE_MATERIALIZATION_SESSION_SOURCE_EVIDENCE_V3, payload
        ),
    )
    return result


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationSessionAppendRequestV3:
    workspace_session_ref: str
    epoch: str
    participant_ref: str
    actor_ref: str
    workflow_session_ref: str
    materialization_attempt_ref: str
    branch_baseline_ref: str
    branch_baseline_digest: ContentDigest
    branch_baseline_grade: str
    package_ref: str
    operation_ref: str
    operation_digest: ContentDigest
    source_evidence: WorkspaceMaterializationSessionSourceEvidenceV3
    expected_session_head_revision: int
    expected_cursor: int
    expected_predecessor_event_digest: ContentDigest | None
    request_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        workspace_session_ref: str,
        epoch: str,
        participant_ref: str,
        actor_ref: str,
        workflow_session_ref: str,
        materialization_attempt_ref: str,
        branch_baseline_ref: str,
        branch_baseline_digest: ContentDigest,
        branch_baseline_grade: str,
        package_ref: str,
        operation_ref: str,
        operation_digest: ContentDigest,
        source_evidence: WorkspaceMaterializationSessionSourceEvidenceV3,
        expected_session_head_revision: int,
        expected_cursor: int,
        expected_predecessor_event_digest: ContentDigest | None,
    ) -> WorkspaceMaterializationSessionAppendRequestV3:
        values = {
            "workspace_session_ref": workspace_session_ref,
            "epoch": epoch,
            "participant_ref": participant_ref,
            "actor_ref": actor_ref,
            "workflow_session_ref": workflow_session_ref,
            "materialization_attempt_ref": materialization_attempt_ref,
            "branch_baseline_ref": branch_baseline_ref,
            "branch_baseline_digest": branch_baseline_digest,
            "branch_baseline_grade": branch_baseline_grade,
            "package_ref": package_ref,
            "operation_ref": operation_ref,
            "operation_digest": operation_digest,
            "source_evidence": source_evidence,
            "expected_session_head_revision": expected_session_head_revision,
            "expected_cursor": expected_cursor,
            "expected_predecessor_event_digest": expected_predecessor_event_digest,
        }
        payload = _session_append_request_v2_payload(values)
        return cls(
            workspace_session_ref=workspace_session_ref,
            epoch=epoch,
            participant_ref=participant_ref,
            actor_ref=actor_ref,
            workflow_session_ref=workflow_session_ref,
            materialization_attempt_ref=materialization_attempt_ref,
            branch_baseline_ref=branch_baseline_ref,
            branch_baseline_digest=branch_baseline_digest,
            branch_baseline_grade=branch_baseline_grade,
            package_ref=package_ref,
            operation_ref=operation_ref,
            operation_digest=operation_digest,
            source_evidence=source_evidence,
            expected_session_head_revision=expected_session_head_revision,
            expected_cursor=expected_cursor,
            expected_predecessor_event_digest=expected_predecessor_event_digest,
            request_digest=_session_v2_digest(
                WORKSPACE_MATERIALIZATION_SESSION_APPEND_REQUEST_V3, payload
            ),
        )

    def __post_init__(self) -> None:
        values = {
            name: getattr(self, name)
            for name in self.__dataclass_fields__
            if name != "request_digest"
        }
        payload = _session_append_request_v2_payload(values)
        if _session_v2_content_digest(
            self.request_digest, "session_append_v2.request_digest"
        ) != _session_v2_digest(
            WORKSPACE_MATERIALIZATION_SESSION_APPEND_REQUEST_V3, payload
        ):
            raise WorkspaceMaterializationSessionError(
                "session append request V2 digest mismatched"
            )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_MATERIALIZATION_SESSION_APPEND_REQUEST_V3,
            **_session_append_request_v2_payload(
                {
                    name: getattr(self, name)
                    for name in self.__dataclass_fields__
                    if name != "request_digest"
                }
            ),
            "request_digest": self.request_digest.to_wire(),
        }


def _session_append_request_v2_payload(values: dict[str, object]) -> dict[str, object]:
    token_fields = (
        "workspace_session_ref",
        "epoch",
        "participant_ref",
        "actor_ref",
        "workflow_session_ref",
        "materialization_attempt_ref",
        "branch_baseline_ref",
        "branch_baseline_grade",
        "package_ref",
        "operation_ref",
    )
    tokens = {
        name: _token(values[name], f"session_append_v2.{name}") for name in token_fields
    }
    source = cast(
        WorkspaceMaterializationSessionSourceEvidenceV3,
        _session_v2_exact(
            values["source_evidence"],
            WorkspaceMaterializationSessionSourceEvidenceV3,
            "session_append_v2.source_evidence",
        ),
    )
    source.__post_init__()
    expected_revision = _nonnegative(
        values["expected_session_head_revision"],
        "session_append_v2.expected_session_head_revision",
    )
    expected_cursor = _nonnegative(
        values["expected_cursor"], "session_append_v2.expected_cursor"
    )
    predecessor_value = values["expected_predecessor_event_digest"]
    if predecessor_value is not None and type(predecessor_value) is not ContentDigest:
        raise TypeError("session append V2 predecessor must be exact digest or null")
    predecessor = cast(ContentDigest | None, predecessor_value)
    if (predecessor is None) != (expected_revision == 0 and expected_cursor == 0):
        raise WorkspaceMaterializationSessionError(
            "session append V2 predecessor/revision/cursor differ"
        )
    return {
        **tokens,
        "branch_baseline_digest": _session_v2_content_digest(
            values["branch_baseline_digest"], "session_append_v2.branch_baseline_digest"
        ).to_wire(),
        "expected_cursor": expected_cursor,
        "expected_predecessor_event_digest": None
        if predecessor is None
        else predecessor.to_wire(),
        "expected_session_head_revision": expected_revision,
        "operation_digest": _session_v2_content_digest(
            values["operation_digest"], "session_append_v2.operation_digest"
        ).to_wire(),
        "source_evidence_digest": source.source_evidence_digest.to_wire(),
    }


def _create_graph_v2_session_append_request(
    *,
    workspace_session_ref: str,
    epoch: str,
    participant_ref: str,
    actor_ref: str,
    workflow_session_ref: str,
    materialization_attempt_ref: str,
    branch_baseline_ref: str,
    branch_baseline_digest: ContentDigest,
    branch_baseline_grade: str,
    package_ref: str,
    operation_ref: str,
    operation_digest: ContentDigest,
    source_evidence: WorkspaceMaterializationSessionSourceEvidenceV3,
    expected_session_head_revision: int,
    expected_cursor: int,
    expected_predecessor_event_digest: ContentDigest | None,
) -> WorkspaceMaterializationSessionAppendRequestV3:
    """Create a dormant V2 request from one already admitted graph state."""

    token_values = {
        name: _token(value, f"session_append_v2.{name}")
        for name, value in {
            "workspace_session_ref": workspace_session_ref,
            "epoch": epoch,
            "participant_ref": participant_ref,
            "actor_ref": actor_ref,
            "workflow_session_ref": workflow_session_ref,
            "materialization_attempt_ref": materialization_attempt_ref,
            "branch_baseline_ref": branch_baseline_ref,
            "branch_baseline_grade": branch_baseline_grade,
            "package_ref": package_ref,
            "operation_ref": operation_ref,
        }.items()
    }
    if type(branch_baseline_digest) is not ContentDigest:
        raise TypeError("graph V2 baseline digest must be exact")
    if type(operation_digest) is not ContentDigest:
        raise TypeError("graph V2 operation digest must be exact")
    if type(source_evidence) is not WorkspaceMaterializationSessionSourceEvidenceV3:
        raise TypeError("graph V2 source evidence must be exact")
    revision = _nonnegative(
        expected_session_head_revision,
        "session_append_v2.expected_session_head_revision",
    )
    cursor = _nonnegative(expected_cursor, "session_append_v2.expected_cursor")
    if (
        expected_predecessor_event_digest is not None
        and type(expected_predecessor_event_digest) is not ContentDigest
    ):
        raise TypeError("graph V2 predecessor must be exact or null")
    if (expected_predecessor_event_digest is None) != (revision == 0 and cursor == 0):
        raise WorkspaceMaterializationSessionError(
            "graph V2 predecessor/revision/cursor differ"
        )
    values: dict[str, object] = {
        **token_values,
        "branch_baseline_digest": branch_baseline_digest,
        "operation_digest": operation_digest,
        "source_evidence": source_evidence,
        "expected_session_head_revision": revision,
        "expected_cursor": cursor,
        "expected_predecessor_event_digest": expected_predecessor_event_digest,
    }
    payload = {
        **token_values,
        "branch_baseline_digest": branch_baseline_digest.value,
        "expected_cursor": cursor,
        "expected_predecessor_event_digest": (
            None
            if expected_predecessor_event_digest is None
            else expected_predecessor_event_digest.value
        ),
        "expected_session_head_revision": revision,
        "operation_digest": operation_digest.value,
        "source_evidence_digest": source_evidence.source_evidence_digest.value,
    }
    result = object.__new__(WorkspaceMaterializationSessionAppendRequestV3)
    for name, value in values.items():
        object.__setattr__(result, name, value)
    object.__setattr__(
        result,
        "request_digest",
        _session_v2_digest(
            WORKSPACE_MATERIALIZATION_SESSION_APPEND_REQUEST_V3, payload
        ),
    )
    return result


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationSessionEventV3:
    append_request: WorkspaceMaterializationSessionAppendRequestV3
    workspace_session_ref: str
    epoch: str
    cursor: int
    predecessor_event_digest: ContentDigest | None
    package_ref: str
    disposition: str
    source_evidence: WorkspaceMaterializationSessionSourceEvidenceV3
    head_reread_evidence_digest: ContentDigest
    publication_receipt_digest: ContentDigest | None
    event_digest: ContentDigest

    @classmethod
    def create(
        cls, *, append_request: WorkspaceMaterializationSessionAppendRequestV3
    ) -> WorkspaceMaterializationSessionEventV3:
        request = cast(
            WorkspaceMaterializationSessionAppendRequestV3,
            _session_v2_exact(
                append_request,
                WorkspaceMaterializationSessionAppendRequestV3,
                "session_event_v2.append_request",
            ),
        )
        request.__post_init__()
        source = request.source_evidence
        values = {
            "append_request": request,
            "workspace_session_ref": request.workspace_session_ref,
            "epoch": request.epoch,
            "cursor": request.expected_cursor + 1,
            "predecessor_event_digest": request.expected_predecessor_event_digest,
            "package_ref": request.package_ref,
            "disposition": source.disposition,
            "source_evidence": source,
            "head_reread_evidence_digest": source.head_reread_evidence.reread_evidence_digest,
            "publication_receipt_digest": source.publication_receipt_digest,
        }
        payload = _session_event_v2_payload(values)
        return cls(
            **values,
            event_digest=_session_v2_digest(
                WORKSPACE_MATERIALIZATION_SESSION_EVENT_V3, payload
            ),
        )

    def __post_init__(self) -> None:
        values = {
            name: getattr(self, name)
            for name in self.__dataclass_fields__
            if name != "event_digest"
        }
        payload = _session_event_v2_payload(values)
        if _session_v2_content_digest(
            self.event_digest, "session_event_v2.event_digest"
        ) != _session_v2_digest(WORKSPACE_MATERIALIZATION_SESSION_EVENT_V3, payload):
            raise WorkspaceMaterializationSessionError(
                "session event V2 digest mismatched"
            )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_MATERIALIZATION_SESSION_EVENT_V3,
            **_session_event_v2_payload(
                {
                    name: getattr(self, name)
                    for name in self.__dataclass_fields__
                    if name != "event_digest"
                }
            ),
            "event_digest": self.event_digest.to_wire(),
        }


def _session_event_v2_payload(values: dict[str, object]) -> dict[str, object]:
    request = cast(
        WorkspaceMaterializationSessionAppendRequestV3,
        _session_v2_exact(
            values["append_request"],
            WorkspaceMaterializationSessionAppendRequestV3,
            "session_event_v2.append_request",
        ),
    )
    source = cast(
        WorkspaceMaterializationSessionSourceEvidenceV3,
        _session_v2_exact(
            values["source_evidence"],
            WorkspaceMaterializationSessionSourceEvidenceV3,
            "session_event_v2.source_evidence",
        ),
    )
    request.__post_init__()
    source.__post_init__()
    predecessor_value = values["predecessor_event_digest"]
    if predecessor_value is not None and type(predecessor_value) is not ContentDigest:
        raise TypeError("session event V2 predecessor must be exact digest or null")
    predecessor = cast(ContentDigest | None, predecessor_value)
    receipt_value = values["publication_receipt_digest"]
    if receipt_value is not None and type(receipt_value) is not ContentDigest:
        raise TypeError(
            "session event V2 publication receipt must be exact digest or null"
        )
    receipt = cast(ContentDigest | None, receipt_value)
    if (
        values["workspace_session_ref"] != request.workspace_session_ref
        or values["epoch"] != request.epoch
        or values["cursor"] != request.expected_cursor + 1
        or predecessor != request.expected_predecessor_event_digest
        or values["package_ref"] != request.package_ref
        or values["disposition"] != source.disposition
        or source.source_evidence_digest
        != request.source_evidence.source_evidence_digest
        or values["head_reread_evidence_digest"]
        != source.head_reread_evidence.reread_evidence_digest
        or receipt != source.publication_receipt_digest
    ):
        raise WorkspaceMaterializationSessionError(
            "session event V2 differs from exact append request/source"
        )
    return {
        "append_request_digest": request.request_digest.to_wire(),
        "disposition": source.disposition,
        "epoch": request.epoch,
        "head_reread_evidence_digest": source.head_reread_evidence.reread_evidence_digest.to_wire(),
        "package_ref": request.package_ref,
        "predecessor_event_digest": None
        if predecessor is None
        else predecessor.to_wire(),
        "publication_receipt_digest": None if receipt is None else receipt.to_wire(),
        "source_evidence_digest": source.source_evidence_digest.to_wire(),
        "workspace_session_ref": request.workspace_session_ref,
        "cursor": request.expected_cursor + 1,
    }


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationSessionHeadV2:
    workspace_session_ref: str
    epoch: str
    cursor: int
    event_digest: ContentDigest
    head_digest: ContentDigest

    @classmethod
    def from_event(
        cls, event: WorkspaceMaterializationSessionEventV3
    ) -> WorkspaceMaterializationSessionHeadV2:
        exact = cast(
            WorkspaceMaterializationSessionEventV3,
            _session_v2_exact(
                event, WorkspaceMaterializationSessionEventV3, "session_head_v2.event"
            ),
        )
        exact.__post_init__()
        values = {
            "workspace_session_ref": exact.workspace_session_ref,
            "epoch": exact.epoch,
            "cursor": exact.cursor,
            "event_digest": exact.event_digest,
        }
        return cls(
            **values,
            head_digest=_session_v2_digest(
                WORKSPACE_MATERIALIZATION_SESSION_HEAD_V2,
                _session_head_v2_payload(values),
            ),
        )

    def __post_init__(self) -> None:
        values = {
            name: getattr(self, name)
            for name in ("workspace_session_ref", "epoch", "cursor", "event_digest")
        }
        payload = _session_head_v2_payload(values)
        if _session_v2_content_digest(
            self.head_digest, "session_head_v2.head_digest"
        ) != _session_v2_digest(WORKSPACE_MATERIALIZATION_SESSION_HEAD_V2, payload):
            raise WorkspaceMaterializationSessionError(
                "session head V2 digest mismatched"
            )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_MATERIALIZATION_SESSION_HEAD_V2,
            **_session_head_v2_payload(
                {
                    name: getattr(self, name)
                    for name in (
                        "workspace_session_ref",
                        "epoch",
                        "cursor",
                        "event_digest",
                    )
                }
            ),
            "head_digest": self.head_digest.to_wire(),
        }


def _session_head_v2_payload(values: dict[str, object]) -> dict[str, object]:
    return {
        "cursor": _positive(values["cursor"], "session_head_v2.cursor"),
        "epoch": _token(values["epoch"], "session_head_v2.epoch"),
        "event_digest": _session_v2_content_digest(
            values["event_digest"], "session_head_v2.event_digest"
        ).to_wire(),
        "workspace_session_ref": _token(
            values["workspace_session_ref"], "session_head_v2.workspace_session_ref"
        ),
    }


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationSessionEventRereadEvidenceV3:
    workspace_session_ref: str
    session_head_revision: int
    event: WorkspaceMaterializationSessionEventV3
    session_head: WorkspaceMaterializationSessionHeadV2
    canonical_event_wire_digest: ContentDigest
    canonical_session_head_wire_digest: ContentDigest
    reread_evidence_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        session_head_revision: int,
        event: WorkspaceMaterializationSessionEventV3,
        session_head: WorkspaceMaterializationSessionHeadV2,
    ) -> WorkspaceMaterializationSessionEventRereadEvidenceV3:
        exact_event = cast(
            WorkspaceMaterializationSessionEventV3,
            _session_v2_exact(
                event,
                WorkspaceMaterializationSessionEventV3,
                "event_reread_v2.event",
            ),
        )
        exact_head = cast(
            WorkspaceMaterializationSessionHeadV2,
            _session_v2_exact(
                session_head,
                WorkspaceMaterializationSessionHeadV2,
                "event_reread_v2.session_head",
            ),
        )
        values = {
            "workspace_session_ref": exact_event.workspace_session_ref,
            "session_head_revision": session_head_revision,
            "event": exact_event,
            "session_head": exact_head,
            "canonical_event_wire_digest": _session_v2_wire_digest(
                exact_event, "event_reread_v2.event"
            ),
            "canonical_session_head_wire_digest": _session_v2_wire_digest(
                exact_head, "event_reread_v2.session_head"
            ),
        }
        payload = _session_event_reread_v2_payload(values)
        return cls(
            **values,
            reread_evidence_digest=_session_v2_digest(
                WORKSPACE_MATERIALIZATION_SESSION_EVENT_REREAD_EVIDENCE_V3, payload
            ),
        )

    def __post_init__(self) -> None:
        values = {
            name: getattr(self, name)
            for name in self.__dataclass_fields__
            if name != "reread_evidence_digest"
        }
        payload = _session_event_reread_v2_payload(values)
        if _session_v2_content_digest(
            self.reread_evidence_digest, "event_reread_v2.reread_evidence_digest"
        ) != _session_v2_digest(
            WORKSPACE_MATERIALIZATION_SESSION_EVENT_REREAD_EVIDENCE_V3, payload
        ):
            raise WorkspaceMaterializationSessionError(
                "session event reread V2 digest mismatched"
            )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_MATERIALIZATION_SESSION_EVENT_REREAD_EVIDENCE_V3,
            **_session_event_reread_v2_payload(
                {
                    name: getattr(self, name)
                    for name in self.__dataclass_fields__
                    if name != "reread_evidence_digest"
                }
            ),
            "reread_evidence_digest": self.reread_evidence_digest.to_wire(),
        }


def _session_event_reread_v2_payload(values: dict[str, object]) -> dict[str, object]:
    event = cast(
        WorkspaceMaterializationSessionEventV3,
        _session_v2_exact(
            values["event"],
            WorkspaceMaterializationSessionEventV3,
            "event_reread_v2.event",
        ),
    )
    head = cast(
        WorkspaceMaterializationSessionHeadV2,
        _session_v2_exact(
            values["session_head"],
            WorkspaceMaterializationSessionHeadV2,
            "event_reread_v2.session_head",
        ),
    )
    event.__post_init__()
    head.__post_init__()
    if (
        values["workspace_session_ref"] != event.workspace_session_ref
        or head.workspace_session_ref != event.workspace_session_ref
        or head.epoch != event.epoch
        or head.cursor != event.cursor
        or head.event_digest != event.event_digest
        or values["canonical_event_wire_digest"]
        != _session_v2_wire_digest(event, "event_reread_v2.event")
        or values["canonical_session_head_wire_digest"]
        != _session_v2_wire_digest(head, "event_reread_v2.session_head")
    ):
        raise WorkspaceMaterializationSessionError(
            "session event reread V2 differs from exact event/head"
        )
    return {
        "canonical_event_wire_digest": cast(
            ContentDigest, values["canonical_event_wire_digest"]
        ).to_wire(),
        "canonical_session_head_wire_digest": cast(
            ContentDigest, values["canonical_session_head_wire_digest"]
        ).to_wire(),
        "event_digest": event.event_digest.to_wire(),
        "session_head_digest": head.head_digest.to_wire(),
        "session_head_revision": _positive(
            values["session_head_revision"], "event_reread_v2.session_head_revision"
        ),
        "workspace_session_ref": event.workspace_session_ref,
    }


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationSessionFanoutReceiptV3:
    append_request: WorkspaceMaterializationSessionAppendRequestV3
    event_reread_evidence: WorkspaceMaterializationSessionEventRereadEvidenceV3
    prior_head_revision: int
    head_revision: int
    head_advanced: bool
    receipt_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        append_request: WorkspaceMaterializationSessionAppendRequestV3,
        event_reread_evidence: WorkspaceMaterializationSessionEventRereadEvidenceV3,
        prior_head_revision: int,
        head_revision: int,
        head_advanced: bool,
    ) -> WorkspaceMaterializationSessionFanoutReceiptV3:
        values = {
            "append_request": append_request,
            "event_reread_evidence": event_reread_evidence,
            "prior_head_revision": prior_head_revision,
            "head_revision": head_revision,
            "head_advanced": head_advanced,
        }
        payload = _session_fanout_receipt_v2_payload(values)
        return cls(
            **values,
            receipt_digest=_session_v2_digest(
                WORKSPACE_MATERIALIZATION_SESSION_FANOUT_RECEIPT_V3, payload
            ),
        )

    def __post_init__(self) -> None:
        values = {
            name: getattr(self, name)
            for name in self.__dataclass_fields__
            if name != "receipt_digest"
        }
        payload = _session_fanout_receipt_v2_payload(values)
        if _session_v2_content_digest(
            self.receipt_digest, "session_fanout_v2.receipt_digest"
        ) != _session_v2_digest(
            WORKSPACE_MATERIALIZATION_SESSION_FANOUT_RECEIPT_V3, payload
        ):
            raise WorkspaceMaterializationSessionError(
                "session fanout receipt V2 digest mismatched"
            )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_MATERIALIZATION_SESSION_FANOUT_RECEIPT_V3,
            **_session_fanout_receipt_v2_payload(
                {
                    name: getattr(self, name)
                    for name in self.__dataclass_fields__
                    if name != "receipt_digest"
                }
            ),
            "receipt_digest": self.receipt_digest.to_wire(),
        }


def _session_fanout_receipt_v2_payload(values: dict[str, object]) -> dict[str, object]:
    request = cast(
        WorkspaceMaterializationSessionAppendRequestV3,
        _session_v2_exact(
            values["append_request"],
            WorkspaceMaterializationSessionAppendRequestV3,
            "session_fanout_v2.append_request",
        ),
    )
    event_reread = cast(
        WorkspaceMaterializationSessionEventRereadEvidenceV3,
        _session_v2_exact(
            values["event_reread_evidence"],
            WorkspaceMaterializationSessionEventRereadEvidenceV3,
            "session_fanout_v2.event_reread_evidence",
        ),
    )
    request.__post_init__()
    event_reread.__post_init__()
    event = event_reread.event
    if event.append_request.request_digest != request.request_digest:
        raise WorkspaceMaterializationSessionError(
            "session fanout V2 request differs from positive event"
        )
    prior = _nonnegative(
        values["prior_head_revision"], "session_fanout_v2.prior_head_revision"
    )
    revision = _positive(values["head_revision"], "session_fanout_v2.head_revision")
    advanced = values["head_advanced"]
    if type(advanced) is not bool:
        raise TypeError("session fanout V2 head_advanced must be exact bool")
    if (advanced and revision != prior + 1) or (not advanced and revision != prior):
        raise WorkspaceMaterializationSessionError(
            "session fanout V2 revision is not contiguous"
        )
    if event_reread.session_head_revision != revision:
        raise WorkspaceMaterializationSessionError(
            "session fanout V2 reread revision differs"
        )
    return {
        "append_request_digest": request.request_digest.to_wire(),
        "event_reread_evidence_digest": (event_reread.reread_evidence_digest.to_wire()),
        "head_advanced": advanced,
        "head_revision": revision,
        "prior_head_revision": prior,
    }


def _encode_session_v2(value: object, expected: type[object], field: str) -> bytes:
    exact = _session_v2_exact(value, expected, field)
    return canonical_json_bytes(cast(_SessionV2PortableWire, exact).to_wire())


def _decode_session_v2(
    wire: bytes, *, expected: object, expected_type: type[object], field: str
) -> object:
    if type(wire) is not bytes:
        raise TypeError(f"{field} wire must be exact bytes")
    if _encode_session_v2(expected, expected_type, field) != wire:
        raise WorkspaceMaterializationSessionError(
            f"{field} wire is not canonical for expected context"
        )
    return expected


def encode_workspace_materialization_session_source_evidence_v2(
    value: WorkspaceMaterializationSessionSourceEvidenceV3,
) -> bytes:
    return _encode_session_v2(
        value, WorkspaceMaterializationSessionSourceEvidenceV3, "session_source_v2"
    )


def decode_workspace_materialization_session_source_evidence_v2(
    wire: bytes, *, expected: WorkspaceMaterializationSessionSourceEvidenceV3
) -> WorkspaceMaterializationSessionSourceEvidenceV3:
    return cast(
        WorkspaceMaterializationSessionSourceEvidenceV3,
        _decode_session_v2(
            wire,
            expected=expected,
            expected_type=WorkspaceMaterializationSessionSourceEvidenceV3,
            field="session_source_v2",
        ),
    )


def encode_workspace_materialization_session_append_request_v2(
    value: WorkspaceMaterializationSessionAppendRequestV3,
) -> bytes:
    return _encode_session_v2(
        value, WorkspaceMaterializationSessionAppendRequestV3, "session_append_v2"
    )


def decode_workspace_materialization_session_append_request_v2(
    wire: bytes, *, expected: WorkspaceMaterializationSessionAppendRequestV3
) -> WorkspaceMaterializationSessionAppendRequestV3:
    return cast(
        WorkspaceMaterializationSessionAppendRequestV3,
        _decode_session_v2(
            wire,
            expected=expected,
            expected_type=WorkspaceMaterializationSessionAppendRequestV3,
            field="session_append_v2",
        ),
    )


def encode_workspace_materialization_session_event_v2(
    value: WorkspaceMaterializationSessionEventV3,
) -> bytes:
    return _encode_session_v2(
        value, WorkspaceMaterializationSessionEventV3, "session_event_v2"
    )


def decode_workspace_materialization_session_event_v2(
    wire: bytes, *, expected: WorkspaceMaterializationSessionEventV3
) -> WorkspaceMaterializationSessionEventV3:
    return cast(
        WorkspaceMaterializationSessionEventV3,
        _decode_session_v2(
            wire,
            expected=expected,
            expected_type=WorkspaceMaterializationSessionEventV3,
            field="session_event_v2",
        ),
    )


def encode_workspace_materialization_session_event_reread_evidence_v2(
    value: WorkspaceMaterializationSessionEventRereadEvidenceV3,
) -> bytes:
    return _encode_session_v2(
        value,
        WorkspaceMaterializationSessionEventRereadEvidenceV3,
        "session_event_reread_v2",
    )


def decode_workspace_materialization_session_event_reread_evidence_v2(
    wire: bytes, *, expected: WorkspaceMaterializationSessionEventRereadEvidenceV3
) -> WorkspaceMaterializationSessionEventRereadEvidenceV3:
    return cast(
        WorkspaceMaterializationSessionEventRereadEvidenceV3,
        _decode_session_v2(
            wire,
            expected=expected,
            expected_type=WorkspaceMaterializationSessionEventRereadEvidenceV3,
            field="session_event_reread_v2",
        ),
    )


def encode_workspace_materialization_session_fanout_receipt_v2(
    value: WorkspaceMaterializationSessionFanoutReceiptV3,
) -> bytes:
    return _encode_session_v2(
        value, WorkspaceMaterializationSessionFanoutReceiptV3, "session_fanout_v2"
    )


def decode_workspace_materialization_session_fanout_receipt_v2(
    wire: bytes, *, expected: WorkspaceMaterializationSessionFanoutReceiptV3
) -> WorkspaceMaterializationSessionFanoutReceiptV3:
    return cast(
        WorkspaceMaterializationSessionFanoutReceiptV3,
        _decode_session_v2(
            wire,
            expected=expected,
            expected_type=WorkspaceMaterializationSessionFanoutReceiptV3,
            field="session_fanout_v2",
        ),
    )


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationSessionAppendMetrics:
    validation_ns: int
    event_stage_ns: int
    head_cas_ns: int
    reread_ns: int
    receipt_ns: int
    total_ns: int
    event_state_cas_count: int
    event_state_reuse_count: int
    head_state_cas_count: int
    event_state_read_count: int
    head_state_read_count: int
    event_wire_bytes: int

    def __post_init__(self) -> None:
        for field in self.__dataclass_fields__:
            _nonnegative(getattr(self, field), field)


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationSessionAppendResult:
    event: WorkspaceMaterializationSessionEvent
    head: WorkspaceMaterializationSessionHead
    receipt: WorkspaceMaterializationSessionFanoutReceipt
    metrics: WorkspaceMaterializationSessionAppendMetrics


@dataclass(frozen=True, slots=True)
class _WorkspaceMaterializationSessionAppendResultV2:
    event: WorkspaceMaterializationSessionEventV3
    head: WorkspaceMaterializationSessionHeadV2
    reread_evidence: WorkspaceMaterializationSessionEventRereadEvidenceV3
    receipt: WorkspaceMaterializationSessionFanoutReceiptV3
    metrics: WorkspaceMaterializationSessionAppendMetrics


@dataclass(frozen=True, slots=True, order=True)
class WorkspaceMaterializationSessionPackageHead:
    package_ref: str
    head_revision: int
    head_digest: str
    result_digest: str
    result_body_ref: str
    result_body_digest: str
    outputs: tuple[WorkspacePublishedSemanticCoordinate, ...]

    def __post_init__(self) -> None:
        _token(self.package_ref, "package_ref")
        _positive(self.head_revision, "head_revision")
        for field in ("head_digest", "result_digest", "result_body_digest"):
            _digest(getattr(self, field), field)
        _token(self.result_body_ref, "result_body_ref")
        if type(self.outputs) is not tuple or any(
            type(item) is not WorkspacePublishedSemanticCoordinate
            for item in self.outputs
        ):
            raise TypeError("snapshot outputs must be exact coordinates")

    @classmethod
    def from_head(
        cls, revision: int, head: WorkspaceSemanticMaterializationHead
    ) -> WorkspaceMaterializationSessionPackageHead:
        if type(head) is not WorkspaceSemanticMaterializationHead:
            raise TypeError("package head must be exact Workspace head")
        head.__post_init__()
        return cls(
            package_ref=head.package_ref,
            head_revision=revision,
            head_digest=head.head_digest,
            result_digest=head.result_digest,
            result_body_ref=head.result_body_ref,
            result_body_digest=head.result_body_digest,
            outputs=head.outputs,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "package_ref": self.package_ref,
            "head_revision": self.head_revision,
            "head_digest": self.head_digest,
            "result_digest": self.result_digest,
            "result_body_ref": self.result_body_ref,
            "result_body_digest": self.result_body_digest,
            "outputs": [item.to_dict() for item in self.outputs],
        }


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationSessionSnapshot:
    workspace_session_ref: str
    epoch: str
    authority_grade: str
    participant_ref: str
    presented_cursor: int
    current_cursor: int
    event_head_digest: str | None
    package_heads: tuple[WorkspaceMaterializationSessionPackageHead, ...]
    snapshot_digest: str
    contract: str = WORKSPACE_MATERIALIZATION_SESSION_SNAPSHOT

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_MATERIALIZATION_SESSION_SNAPSHOT:
            raise WorkspaceMaterializationSessionError("snapshot contract differs")
        for field in ("workspace_session_ref", "epoch", "participant_ref"):
            _token(getattr(self, field), field)
        WorkspaceMaterializationSessionAuthorityGrade(self.authority_grade)
        _nonnegative(self.presented_cursor, "presented_cursor")
        _nonnegative(self.current_cursor, "current_cursor")
        if self.event_head_digest is None:
            if self.current_cursor != 0:
                raise WorkspaceMaterializationSessionError(
                    "nonempty snapshot requires event head"
                )
        else:
            _digest(self.event_head_digest, "event_head_digest")
        if type(self.package_heads) is not tuple or any(
            type(item) is not WorkspaceMaterializationSessionPackageHead
            for item in self.package_heads
        ):
            raise TypeError("snapshot package heads must be exact")
        if self.package_heads != tuple(sorted(set(self.package_heads))):
            raise WorkspaceMaterializationSessionError(
                "snapshot package heads are not canonical"
            )
        if self.snapshot_digest != _semantic_digest(self.contract, self._payload()):
            raise WorkspaceMaterializationSessionError("snapshot digest mismatched")

    @classmethod
    def create(
        cls,
        *,
        admission: WorkspaceMaterializationSessionAdmission,
        presented_cursor: int,
        head: WorkspaceMaterializationSessionHead | None,
        package_heads: tuple[WorkspaceMaterializationSessionPackageHead, ...],
    ) -> WorkspaceMaterializationSessionSnapshot:
        state = _admission_state(admission)
        values: dict[str, object] = {
            "workspace_session_ref": state.request.workspace_session_ref,
            "epoch": state.request.epoch,
            "authority_grade": state.authority_grade.value,
            "participant_ref": state.request.participant_ref,
            "presented_cursor": presented_cursor,
            "current_cursor": 0 if head is None else head.cursor,
            "event_head_digest": None if head is None else head.event_digest,
            "package_heads": tuple(sorted(package_heads)),
        }
        return cls(
            workspace_session_ref=state.request.workspace_session_ref,
            epoch=state.request.epoch,
            authority_grade=state.authority_grade.value,
            participant_ref=state.request.participant_ref,
            presented_cursor=presented_cursor,
            current_cursor=0 if head is None else head.cursor,
            event_head_digest=None if head is None else head.event_digest,
            package_heads=tuple(sorted(package_heads)),
            snapshot_digest=_semantic_digest(
                WORKSPACE_MATERIALIZATION_SESSION_SNAPSHOT,
                _snapshot_payload(values),
            ),
        )

    def _payload(self) -> dict[str, object]:
        return _snapshot_payload(
            {
                "workspace_session_ref": self.workspace_session_ref,
                "epoch": self.epoch,
                "authority_grade": self.authority_grade,
                "participant_ref": self.participant_ref,
                "presented_cursor": self.presented_cursor,
                "current_cursor": self.current_cursor,
                "event_head_digest": self.event_head_digest,
                "package_heads": self.package_heads,
            }
        )


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationSessionReadMetrics:
    total_ns: int
    head_state_read_count: int
    event_state_read_count: int
    package_head_read_count: int
    returned_event_count: int
    requested_package_count: int

    def __post_init__(self) -> None:
        for field in self.__dataclass_fields__:
            _nonnegative(getattr(self, field), field)


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationSessionGap:
    reason: WorkspaceMaterializationSessionGapReason
    requested_epoch: str | None
    requested_after_cursor: int
    reset_snapshot: WorkspaceMaterializationSessionSnapshot


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationSessionReplay:
    snapshot: WorkspaceMaterializationSessionSnapshot
    events: tuple[WorkspaceMaterializationSessionEvent, ...]
    gap: WorkspaceMaterializationSessionGap | None
    metrics: WorkspaceMaterializationSessionReadMetrics


class WorkspaceMaterializationSessionJournal:
    """O(1) durable append and bounded predecessor-chain replay."""

    def __init__(
        self,
        *,
        state_store: LocalOperationalStateStore,
        package_head_resolver: WorkspaceMaterializationSessionPackageHeadResolver,
        replay_limit: int = 128,
        snapshot_package_limit: int = 64,
        event_namespace: str = WORKSPACE_MATERIALIZATION_SESSION_EVENT_NAMESPACE,
        head_namespace: str = WORKSPACE_MATERIALIZATION_SESSION_HEAD_NAMESPACE,
    ) -> None:
        if type(replay_limit) is not int or replay_limit <= 0:
            raise ValueError("session replay limit must be positive")
        if type(snapshot_package_limit) is not int or snapshot_package_limit <= 0:
            raise ValueError("snapshot package limit must be positive")
        self._state_store = state_store
        self._package_head_resolver = package_head_resolver
        self._replay_limit = replay_limit
        self._snapshot_package_limit = snapshot_package_limit
        self._event_namespace = _token(event_namespace, "event_namespace")
        self._head_namespace = _token(head_namespace, "head_namespace")

    def read_head(
        self, workspace_session_ref: str
    ) -> tuple[int, WorkspaceMaterializationSessionHead] | None:
        record = self._state_store.read(
            self._head_namespace, _token(workspace_session_ref, "workspace_session_ref")
        )
        if record is None or record.value is None:
            return None
        return record.revision, WorkspaceMaterializationSessionHead.from_json_bytes(
            _stored_wire(record.value, "session head")
        )

    def _read_graph_v2_head(
        self, workspace_session_ref: str
    ) -> tuple[int, WorkspaceMaterializationSessionHeadV2] | None:
        observed = self._read_graph_resume_head(workspace_session_ref)
        if observed is None:
            return None
        revision, head = observed
        if type(head) is not WorkspaceMaterializationSessionHeadV2:
            raise WorkspaceMaterializationSessionError(
                "stored session head is not graph V2"
            )
        return revision, head

    def _read_graph_resume_head(
        self, workspace_session_ref: str
    ) -> (
        tuple[
            int,
            WorkspaceMaterializationSessionHead | WorkspaceMaterializationSessionHeadV2,
        ]
        | None
    ):
        """Read the exact V1/V2 head at a dormant graph recovery boundary."""

        record = self._state_store.read(
            self._head_namespace, _token(workspace_session_ref, "workspace_session_ref")
        )
        if record is None or record.value is None:
            return None
        wire = _stored_wire(record.value, "session head")
        contract = _wire_contract(wire, "session head")
        if contract == WORKSPACE_MATERIALIZATION_SESSION_HEAD:
            head: (
                WorkspaceMaterializationSessionHead
                | WorkspaceMaterializationSessionHeadV2
            ) = WorkspaceMaterializationSessionHead.from_json_bytes(wire)
        elif contract == WORKSPACE_MATERIALIZATION_SESSION_HEAD_V2:
            head = _parse_session_head_v2_wire(wire)
        else:
            raise WorkspaceMaterializationSessionError(
                "stored session head contract unsupported"
            )
        if head.workspace_session_ref != workspace_session_ref:
            raise WorkspaceMaterializationSessionError(
                "stored session head differs from state key"
            )
        return record.revision, head

    def _reread_graph_v2_event(
        self, event_digest: ContentDigest
    ) -> WorkspaceMaterializationSessionEventV3 | None:
        """Freshly authenticate one immutable dormant V2 event by its digest."""

        if type(event_digest) is not ContentDigest:
            raise TypeError("graph V2 event digest must be exact")
        record = self._state_store.read(self._event_namespace, event_digest.value)
        if record is None or record.value is None:
            return None
        event = _parse_graph_v2_event_wrapper(record.value)
        if event.event_digest != event_digest:
            raise WorkspaceMaterializationSessionError(
                "stored graph V2 event differs from its state key"
            )
        return event

    def _append_graph_v2(
        self,
        *,
        request: WorkspaceMaterializationSessionAppendRequestV3,
    ) -> _WorkspaceMaterializationSessionAppendResultV2:
        """Persist one dormant graph V2 event through the existing journal."""

        started = time.perf_counter_ns()
        validation_started = started
        if type(request) is not WorkspaceMaterializationSessionAppendRequestV3:
            raise TypeError("graph session append request must be exact V2 request")
        request.__post_init__()
        event = WorkspaceMaterializationSessionEventV3.create(append_request=request)
        target_head = WorkspaceMaterializationSessionHeadV2.from_event(event)
        record = self._state_store.read(
            self._head_namespace, request.workspace_session_ref
        )
        actual_revision = 0 if record is None else record.revision
        current_v1: WorkspaceMaterializationSessionHead | None = None
        current_v2: WorkspaceMaterializationSessionHeadV2 | None = None
        if record is not None and record.value is not None:
            wire = _stored_wire(record.value, "session head")
            contract = _wire_contract(wire, "session head")
            if contract == WORKSPACE_MATERIALIZATION_SESSION_HEAD:
                current_v1 = WorkspaceMaterializationSessionHead.from_json_bytes(wire)
            elif contract == WORKSPACE_MATERIALIZATION_SESSION_HEAD_V2:
                current_v2 = _parse_session_head_v2_wire(wire)
            else:
                raise WorkspaceMaterializationSessionError(
                    "stored session head contract unsupported"
                )

        exact_retry = (
            current_v2 is not None
            and canonical_json_bytes(current_v2.to_wire())
            == canonical_json_bytes(target_head.to_wire())
            and actual_revision == request.expected_session_head_revision + 1
        )
        if not exact_retry:
            if actual_revision != request.expected_session_head_revision:
                raise WorkspaceMaterializationSessionConflict(
                    "graph V2 expected session head revision is stale"
                )
            if current_v1 is not None:
                if (
                    current_v1.workspace_session_ref != request.workspace_session_ref
                    or current_v1.epoch != request.epoch
                    or current_v1.cursor != request.expected_cursor
                    or request.expected_predecessor_event_digest
                    != ContentDigest(current_v1.event_digest)
                ):
                    raise WorkspaceMaterializationSessionConflict(
                        "graph V2 V1 predecessor differs"
                    )
            elif current_v2 is not None:
                if (
                    current_v2.workspace_session_ref != request.workspace_session_ref
                    or current_v2.epoch != request.epoch
                    or current_v2.cursor != request.expected_cursor
                    or request.expected_predecessor_event_digest
                    != current_v2.event_digest
                ):
                    raise WorkspaceMaterializationSessionConflict(
                        "graph V2 predecessor differs"
                    )
            elif (
                request.expected_cursor != 0
                or request.expected_predecessor_event_digest is not None
            ):
                raise WorkspaceMaterializationSessionConflict(
                    "graph V2 genesis predecessor differs"
                )
        validation_ns = time.perf_counter_ns() - validation_started

        stage_started = time.perf_counter_ns()
        event_wire = encode_workspace_materialization_session_event_v2(event)
        event_wrapper = _graph_v2_event_wrapper(event)
        existing_event = self._state_store.read(
            self._event_namespace, event.event_digest.value
        )
        event_state_cas_count = 0
        event_state_reuse_count = 0
        if existing_event is None:
            try:
                self._state_store.compare_and_set(
                    self._event_namespace,
                    event.event_digest.value,
                    expected_revision=0,
                    value=event_wrapper,
                )
            except LocalOperationalStateConflict as error:
                raise WorkspaceMaterializationSessionConflict(
                    "graph V2 session event stage CAS lost"
                ) from error
            event_state_cas_count = 1
        elif existing_event.value is None or canonical_json_bytes(
            _thaw_session_json(existing_event.value)
        ) != canonical_json_bytes(event_wrapper):
            raise WorkspaceMaterializationSessionConflict(
                "graph V2 session event digest collided with different context"
            )
        else:
            event_state_reuse_count = 1
        event_stage_ns = time.perf_counter_ns() - stage_started

        head_cas_started = time.perf_counter_ns()
        if exact_retry:
            head_revision = actual_revision
            prior_head_revision = request.expected_session_head_revision
            head_advanced = True
            head_state_cas_count = 0
        else:
            try:
                advanced_record = self._state_store.compare_and_set(
                    self._head_namespace,
                    request.workspace_session_ref,
                    expected_revision=request.expected_session_head_revision,
                    value=_wire_wrapper(canonical_json_bytes(target_head.to_wire())),
                )
            except LocalOperationalStateConflict as error:
                raise WorkspaceMaterializationSessionConflict(
                    "graph V2 session head CAS lost"
                ) from error
            head_revision = advanced_record.revision
            prior_head_revision = request.expected_session_head_revision
            head_advanced = True
            head_state_cas_count = 1
        head_cas_ns = time.perf_counter_ns() - head_cas_started

        reread_started = time.perf_counter_ns()
        event_record = self._state_store.read(
            self._event_namespace, event.event_digest.value
        )
        head_record = self._read_graph_v2_head(request.workspace_session_ref)
        if event_record is None or event_record.value is None:
            raise WorkspaceMaterializationSessionError(
                "graph V2 session event reread is absent"
            )
        observed_event = _parse_graph_v2_event_wrapper(event_record.value)
        if (
            head_record is None
            or head_record[0] != head_revision
            or encode_workspace_materialization_session_event_v2(observed_event)
            != event_wire
            or canonical_json_bytes(head_record[1].to_wire())
            != canonical_json_bytes(target_head.to_wire())
        ):
            raise WorkspaceMaterializationSessionError(
                "graph V2 session event/head reread differs"
            )
        reread = WorkspaceMaterializationSessionEventRereadEvidenceV3.create(
            session_head_revision=head_revision,
            event=observed_event,
            session_head=head_record[1],
        )
        reread_ns = time.perf_counter_ns() - reread_started
        receipt_started = time.perf_counter_ns()
        receipt = WorkspaceMaterializationSessionFanoutReceiptV3.create(
            append_request=request,
            event_reread_evidence=reread,
            prior_head_revision=prior_head_revision,
            head_revision=head_revision,
            head_advanced=head_advanced,
        )
        receipt_ns = time.perf_counter_ns() - receipt_started
        return _WorkspaceMaterializationSessionAppendResultV2(
            event=observed_event,
            head=head_record[1],
            reread_evidence=reread,
            receipt=receipt,
            metrics=WorkspaceMaterializationSessionAppendMetrics(
                validation_ns=validation_ns,
                event_stage_ns=event_stage_ns,
                head_cas_ns=head_cas_ns,
                reread_ns=reread_ns,
                receipt_ns=receipt_ns,
                total_ns=time.perf_counter_ns() - started,
                event_state_cas_count=event_state_cas_count,
                event_state_reuse_count=event_state_reuse_count,
                head_state_cas_count=head_state_cas_count,
                event_state_read_count=2,
                head_state_read_count=2,
                event_wire_bytes=len(event_wire),
            ),
        )

    def _replay_graph_v2_events(
        self,
        *,
        workspace_session_ref: str,
        epoch: str,
        after_cursor: int,
    ) -> tuple[
        WorkspaceMaterializationSessionEvent | WorkspaceMaterializationSessionEventV3,
        ...,
    ]:
        """Strictly replay mixed V1→V2 history for the dormant graph reader."""

        session_ref = _token(workspace_session_ref, "workspace_session_ref")
        expected_epoch = _token(epoch, "epoch")
        _nonnegative(after_cursor, "after_cursor")
        record = self._state_store.read(self._head_namespace, session_ref)
        if record is None or record.value is None:
            return ()
        head_wire = _stored_wire(record.value, "session head")
        head_contract = _wire_contract(head_wire, "session head")
        if head_contract == WORKSPACE_MATERIALIZATION_SESSION_HEAD:
            head_v1 = WorkspaceMaterializationSessionHead.from_json_bytes(head_wire)
            head_session_ref = head_v1.workspace_session_ref
            head_epoch = head_v1.epoch
            cursor = head_v1.cursor
            digest: str | None = head_v1.event_digest
        elif head_contract == WORKSPACE_MATERIALIZATION_SESSION_HEAD_V2:
            head_v2 = _parse_session_head_v2_wire(head_wire)
            head_session_ref = head_v2.workspace_session_ref
            head_epoch = head_v2.epoch
            cursor = head_v2.cursor
            digest = head_v2.event_digest.value
        else:
            raise WorkspaceMaterializationSessionError(
                "session replay head contract unsupported"
            )
        if head_session_ref != session_ref or head_epoch != expected_epoch:
            raise WorkspaceMaterializationSessionError(
                "session replay head coordinate differs"
            )
        if after_cursor > cursor or cursor - after_cursor > self._replay_limit:
            raise WorkspaceMaterializationSessionError(
                "session replay cursor is outside the bounded history"
            )
        events: list[
            WorkspaceMaterializationSessionEvent
            | WorkspaceMaterializationSessionEventV3
        ] = []
        while cursor > after_cursor:
            if digest is None:
                raise WorkspaceMaterializationSessionError(
                    "session replay chain ended before cursor"
                )
            event_record = self._state_store.read(self._event_namespace, digest)
            if event_record is None or event_record.value is None:
                raise WorkspaceMaterializationSessionError(
                    "session replay event body is unavailable"
                )
            wrapper = _session_wire_mapping(event_record.value, "session event wrapper")
            if set(wrapper) == {"wire", "wire_digest"}:
                event_v1 = WorkspaceMaterializationSessionEvent.from_json_bytes(
                    _stored_wire(event_record.value, "session event")
                )
                event: (
                    WorkspaceMaterializationSessionEvent
                    | WorkspaceMaterializationSessionEventV3
                ) = event_v1
                event_digest = event_v1.event_digest
                predecessor = event_v1.predecessor_event_digest
            elif set(wrapper) == {"context", "wire", "wire_digest"}:
                event_v2 = _parse_graph_v2_event_wrapper(event_record.value)
                event = event_v2
                event_digest = event_v2.event_digest.value
                predecessor = (
                    None
                    if event_v2.predecessor_event_digest is None
                    else event_v2.predecessor_event_digest.value
                )
            else:
                raise WorkspaceMaterializationSessionError(
                    "session replay event wrapper fields differ"
                )
            if (
                event_digest != digest
                or event.workspace_session_ref != session_ref
                or event.epoch != expected_epoch
                or event.cursor != cursor
            ):
                raise WorkspaceMaterializationSessionError(
                    "session replay event chain is not contiguous"
                )
            events.append(event)
            digest = predecessor
            cursor -= 1
        return tuple(reversed(events))

    def append(
        self,
        *,
        admission: WorkspaceMaterializationSessionAdmission,
        publication: WorkspaceSemanticMaterializationPublicationReceipt,
    ) -> WorkspaceMaterializationSessionAppendResult:
        started = time.perf_counter_ns()
        validation_started = started
        state = _admission_state(admission)
        admission._assert_intact()
        request = state.request
        if type(publication) is not WorkspaceSemanticMaterializationPublicationReceipt:
            raise TypeError("publication must be exact Workspace receipt")
        publication.__post_init__()
        head = publication.head
        if (
            publication.receipt_digest != request.publication_receipt_digest
            or head.package_ref != request.package_ref
            or head.profile_digest != request.profile_digest
            or head.source_authority_ref != request.source_authority_ref
            or head.source_authority_digest != request.source_authority_digest
        ):
            raise WorkspaceMaterializationSessionError(
                "publication differs from admitted session append"
            )
        # This preflight is version fencing, not a new currentness claim. A
        # historical V1 receipt may still be appended in session order, but a
        # resolver that observes a V2 package slot fails before event staging.
        observed_package = self._package_head_resolver(head.package_ref)
        if observed_package is not None:
            _, observed_head = observed_package
            if type(observed_head) is not WorkspaceSemanticMaterializationHead:
                raise WorkspaceMaterializationSessionConflict(
                    "mounted V1 append observed a non-V1 package head"
                )
        current = self.read_head(request.workspace_session_ref)
        actual_revision = 0 if current is None else current[0]
        actual_head = None if current is None else current[1]
        event = WorkspaceMaterializationSessionEvent.create(
            admission=admission, publication=publication
        )
        target_head = WorkspaceMaterializationSessionHead.from_event(event)
        exact_retry = (
            actual_head == target_head
            and actual_revision == request.expected_session_head_revision + 1
        )
        if not exact_retry:
            if actual_revision != request.expected_session_head_revision:
                raise WorkspaceMaterializationSessionConflict(
                    "expected session head revision is stale"
                )
            if current is None:
                if request.expected_cursor != 0:
                    raise WorkspaceMaterializationSessionConflict(
                        "genesis expected cursor differs"
                    )
            elif (
                actual_head is None
                or actual_head.epoch != request.epoch
                or actual_head.authority_grade != state.authority_grade.value
                or actual_head.cursor != request.expected_cursor
                or actual_head.event_digest != request.expected_predecessor_event_digest
            ):
                raise WorkspaceMaterializationSessionConflict(
                    "session cursor or predecessor differs"
                )
        validation_ns = time.perf_counter_ns() - validation_started

        stage_started = time.perf_counter_ns()
        event_wire = event.to_json_bytes()
        event_wrapper = _wire_wrapper(event_wire)
        existing_event = self._state_store.read(
            self._event_namespace, event.event_digest
        )
        event_state_read_count = 1
        event_state_cas_count = 0
        event_state_reuse_count = 0
        if existing_event is None:
            try:
                self._state_store.compare_and_set(
                    self._event_namespace,
                    event.event_digest,
                    expected_revision=0,
                    value=event_wrapper,
                )
            except LocalOperationalStateConflict as error:
                raise WorkspaceMaterializationSessionConflict(
                    "session event stage CAS lost"
                ) from error
            event_state_cas_count = 1
        else:
            if (
                existing_event.value is None
                or _stored_wire(existing_event.value, "session event") != event_wire
            ):
                raise WorkspaceMaterializationSessionConflict(
                    "session event digest collided with different wire"
                )
            event_state_reuse_count = 1
        event_stage_ns = time.perf_counter_ns() - stage_started

        head_cas_started = time.perf_counter_ns()
        head_state_cas_count = 0
        if exact_retry:
            assert current is not None
            head_revision = current[0]
            head_advanced = False
            prior_head_revision = head_revision
        else:
            try:
                record = self._state_store.compare_and_set(
                    self._head_namespace,
                    request.workspace_session_ref,
                    expected_revision=request.expected_session_head_revision,
                    value=_wire_wrapper(target_head.to_json_bytes()),
                )
            except LocalOperationalStateConflict as error:
                raise WorkspaceMaterializationSessionConflict(
                    "session head CAS lost"
                ) from error
            head_revision = record.revision
            prior_head_revision = request.expected_session_head_revision
            head_advanced = True
            head_state_cas_count = 1
        head_cas_ns = time.perf_counter_ns() - head_cas_started

        reread_started = time.perf_counter_ns()
        event_reread = self._state_store.read(self._event_namespace, event.event_digest)
        head_reread = self.read_head(request.workspace_session_ref)
        if (
            event_reread is None
            or event_reread.value is None
            or _stored_wire(event_reread.value, "session event") != event_wire
            or head_reread is None
            or head_reread[0] != head_revision
            or head_reread[1] != target_head
        ):
            raise WorkspaceMaterializationSessionError(
                "session event/head reread differs"
            )
        reread_ns = time.perf_counter_ns() - reread_started

        receipt_started = time.perf_counter_ns()
        receipt = WorkspaceMaterializationSessionFanoutReceipt.create(
            request_digest=request.request_digest,
            event_digest=event.event_digest,
            head_digest=target_head.head_digest,
            prior_head_revision=prior_head_revision,
            head_revision=head_revision,
            head_advanced=head_advanced,
        )
        receipt_ns = time.perf_counter_ns() - receipt_started
        return WorkspaceMaterializationSessionAppendResult(
            event=event,
            head=target_head,
            receipt=receipt,
            metrics=WorkspaceMaterializationSessionAppendMetrics(
                validation_ns=validation_ns,
                event_stage_ns=event_stage_ns,
                head_cas_ns=head_cas_ns,
                reread_ns=reread_ns,
                receipt_ns=receipt_ns,
                total_ns=time.perf_counter_ns() - started,
                event_state_cas_count=event_state_cas_count,
                event_state_reuse_count=event_state_reuse_count,
                head_state_cas_count=head_state_cas_count,
                event_state_read_count=event_state_read_count + 1,
                head_state_read_count=2,
                event_wire_bytes=len(event_wire),
            ),
        )

    def replay(
        self,
        *,
        admission: WorkspaceMaterializationSessionAdmission,
        requested_epoch: str | None,
        after_cursor: int,
        package_refs: tuple[str, ...],
    ) -> WorkspaceMaterializationSessionReplay:
        started = time.perf_counter_ns()
        state = _admission_state(admission)
        admission._assert_intact()
        _nonnegative(after_cursor, "after_cursor")
        if requested_epoch is not None:
            _token(requested_epoch, "requested_epoch")
        normalized_packages = _package_page(
            package_refs,
            permitted=state.permitted_package_refs,
            maximum=self._snapshot_package_limit,
        )
        current = self.read_head(state.request.workspace_session_ref)
        package_heads: list[WorkspaceMaterializationSessionPackageHead] = []
        for package_ref in normalized_packages:
            resolved = self._package_head_resolver(package_ref)
            if resolved is not None:
                package_heads.append(
                    WorkspaceMaterializationSessionPackageHead.from_head(*resolved)
                )
        head = None if current is None else current[1]
        snapshot = WorkspaceMaterializationSessionSnapshot.create(
            admission=admission,
            presented_cursor=after_cursor,
            head=head,
            package_heads=tuple(package_heads),
        )
        current_cursor = 0 if head is None else head.cursor
        reason: WorkspaceMaterializationSessionGapReason | None = None
        if requested_epoch is not None and requested_epoch != state.request.epoch:
            reason = WorkspaceMaterializationSessionGapReason.EPOCH_MISMATCH
        elif after_cursor > current_cursor:
            reason = WorkspaceMaterializationSessionGapReason.CURSOR_AHEAD
        elif current_cursor - after_cursor > self._replay_limit:
            reason = WorkspaceMaterializationSessionGapReason.RETENTION_EXCEEDED
        if reason is not None:
            metrics = WorkspaceMaterializationSessionReadMetrics(
                total_ns=time.perf_counter_ns() - started,
                head_state_read_count=1,
                event_state_read_count=0,
                package_head_read_count=len(normalized_packages),
                returned_event_count=0,
                requested_package_count=len(normalized_packages),
            )
            return WorkspaceMaterializationSessionReplay(
                snapshot=snapshot,
                events=(),
                gap=WorkspaceMaterializationSessionGap(
                    reason=reason,
                    requested_epoch=requested_epoch,
                    requested_after_cursor=after_cursor,
                    reset_snapshot=snapshot,
                ),
                metrics=metrics,
            )
        events: list[WorkspaceMaterializationSessionEvent] = []
        event_reads = 0
        digest = None if head is None else head.event_digest
        cursor = current_cursor
        while cursor > after_cursor:
            if digest is None:
                raise WorkspaceMaterializationSessionError(
                    "session event chain ended before cursor"
                )
            record = self._state_store.read(self._event_namespace, digest)
            event_reads += 1
            if record is None or record.value is None:
                raise WorkspaceMaterializationSessionError(
                    "session event chain body is unavailable"
                )
            event = WorkspaceMaterializationSessionEvent.from_json_bytes(
                _stored_wire(record.value, "session event")
            )
            if (
                event.event_digest != digest
                or event.workspace_session_ref != state.request.workspace_session_ref
                or event.epoch != state.request.epoch
                or event.cursor != cursor
            ):
                raise WorkspaceMaterializationSessionError(
                    "session event chain is not contiguous"
                )
            events.append(event)
            digest = event.predecessor_event_digest
            cursor -= 1
        ordered = tuple(reversed(events))
        metrics = WorkspaceMaterializationSessionReadMetrics(
            total_ns=time.perf_counter_ns() - started,
            head_state_read_count=1,
            event_state_read_count=event_reads,
            package_head_read_count=len(normalized_packages),
            returned_event_count=len(ordered),
            requested_package_count=len(normalized_packages),
        )
        return WorkspaceMaterializationSessionReplay(
            snapshot=snapshot,
            events=ordered,
            gap=None,
            metrics=metrics,
        )


def _event_payload(values: dict[str, object]) -> dict[str, object]:
    result = {field: values[field] for field in _EVENT_FIELDS}
    result["outputs"] = [
        item.to_dict()
        for item in cast(
            tuple[WorkspacePublishedSemanticCoordinate, ...], values["outputs"]
        )
    ]
    return result


def _snapshot_payload(values: dict[str, object]) -> dict[str, object]:
    return {
        "workspace_session_ref": values["workspace_session_ref"],
        "epoch": values["epoch"],
        "authority_grade": values["authority_grade"],
        "participant_ref": values["participant_ref"],
        "presented_cursor": values["presented_cursor"],
        "current_cursor": values["current_cursor"],
        "event_head_digest": values["event_head_digest"],
        "package_heads": [
            item.to_dict()
            for item in cast(
                tuple[WorkspaceMaterializationSessionPackageHead, ...],
                values["package_heads"],
            )
        ],
    }


def _wire_wrapper(wire: bytes) -> JsonObject:
    if type(wire) is not bytes:
        raise TypeError("canonical wire must be exact bytes")
    return cast(
        JsonObject,
        {
            "wire": wire.decode("utf-8"),
            "wire_digest": ContentDigest.of_bytes(wire).value,
        },
    )


def _graph_v2_event_wrapper(
    event: WorkspaceMaterializationSessionEventV3,
) -> JsonObject:
    if type(event) is not WorkspaceMaterializationSessionEventV3:
        raise TypeError("graph V2 event must be exact")
    event.__post_init__()
    source = event.source_evidence
    publication = source.publication_receipt
    return cast(
        JsonObject,
        {
            "context": {
                "append_request": event.append_request.to_wire(),
                "head_reread_evidence": source.head_reread_evidence.to_wire(),
                "publication_receipt": (
                    None if publication is None else publication.to_wire()
                ),
                "source_evidence": source.to_wire(),
            },
            "wire": encode_workspace_materialization_session_event_v2(event).decode(
                "utf-8"
            ),
            "wire_digest": ContentDigest.of_bytes(
                encode_workspace_materialization_session_event_v2(event)
            ).value,
        },
    )


def _parse_graph_v2_event_wrapper(
    value: JsonObject,
) -> WorkspaceMaterializationSessionEventV3:
    root = _session_wire_keys(
        _thaw_session_json(value), {"context", "wire", "wire_digest"}, "event"
    )
    wire_text = root["wire"]
    wire_digest = root["wire_digest"]
    if type(wire_text) is not str or type(wire_digest) is not str:
        raise WorkspaceMaterializationSessionError(
            "graph V2 event wrapper types differ"
        )
    wire = wire_text.encode("utf-8")
    if ContentDigest.of_bytes(wire).value != wire_digest:
        raise WorkspaceMaterializationSessionError(
            "graph V2 event wrapper digest differs"
        )
    context = _session_wire_keys(
        root["context"],
        {
            "append_request",
            "head_reread_evidence",
            "publication_receipt",
            "source_evidence",
        },
        "event.context",
    )
    head_evidence = _parse_head_reread_evidence_v2_wire(context["head_reread_evidence"])
    publication_value = context["publication_receipt"]
    publication = (
        None
        if publication_value is None
        else _parse_publication_receipt_v2_wire(publication_value)
    )
    source = WorkspaceMaterializationSessionSourceEvidenceV3.create(
        disposition=_session_wire_token(
            _session_wire_mapping(context["source_evidence"], "source").get(
                "disposition"
            ),
            "source.disposition",
        ),
        head_reread_evidence=head_evidence,
        publication_receipt=publication,
    )
    if canonical_json_bytes(source.to_wire()) != canonical_json_bytes(
        _thaw_session_json(context["source_evidence"])
    ):
        raise WorkspaceMaterializationSessionError(
            "stored graph V2 source evidence differs from fresh derivation"
        )
    append = _parse_session_append_request_v2_wire(
        context["append_request"], source=source
    )
    event = WorkspaceMaterializationSessionEventV3.create(append_request=append)
    if encode_workspace_materialization_session_event_v2(event) != wire:
        raise WorkspaceMaterializationSessionError(
            "stored graph V2 event differs from fresh derivation"
        )
    return event


def _parse_session_append_request_v2_wire(
    value: object,
    *,
    source: WorkspaceMaterializationSessionSourceEvidenceV3,
) -> WorkspaceMaterializationSessionAppendRequestV3:
    field = "stored session append request V2"
    root = _session_wire_keys(
        value,
        {
            "actor_ref",
            "branch_baseline_digest",
            "branch_baseline_grade",
            "branch_baseline_ref",
            "contract",
            "epoch",
            "expected_cursor",
            "expected_predecessor_event_digest",
            "expected_session_head_revision",
            "materialization_attempt_ref",
            "operation_digest",
            "operation_ref",
            "package_ref",
            "participant_ref",
            "request_digest",
            "source_evidence_digest",
            "workflow_session_ref",
            "workspace_session_ref",
        },
        field,
    )
    if root["contract"] != WORKSPACE_MATERIALIZATION_SESSION_APPEND_REQUEST_V3:
        raise WorkspaceMaterializationSessionError(
            "stored session append request V2 contract differs"
        )
    predecessor_value = root["expected_predecessor_event_digest"]
    predecessor = (
        None
        if predecessor_value is None
        else _session_wire_digest(predecessor_value, f"{field}.predecessor")
    )
    request = WorkspaceMaterializationSessionAppendRequestV3.create(
        workspace_session_ref=_session_wire_token(
            root["workspace_session_ref"], f"{field}.workspace_session_ref"
        ),
        epoch=_session_wire_token(root["epoch"], f"{field}.epoch"),
        participant_ref=_session_wire_token(
            root["participant_ref"], f"{field}.participant_ref"
        ),
        actor_ref=_session_wire_token(root["actor_ref"], f"{field}.actor_ref"),
        workflow_session_ref=_session_wire_token(
            root["workflow_session_ref"], f"{field}.workflow_session_ref"
        ),
        materialization_attempt_ref=_session_wire_token(
            root["materialization_attempt_ref"],
            f"{field}.materialization_attempt_ref",
        ),
        branch_baseline_ref=_session_wire_token(
            root["branch_baseline_ref"], f"{field}.branch_baseline_ref"
        ),
        branch_baseline_digest=_session_wire_digest(
            root["branch_baseline_digest"], f"{field}.branch_baseline_digest"
        ),
        branch_baseline_grade=_session_wire_token(
            root["branch_baseline_grade"], f"{field}.branch_baseline_grade"
        ),
        package_ref=_session_wire_token(root["package_ref"], f"{field}.package_ref"),
        operation_ref=_session_wire_token(
            root["operation_ref"], f"{field}.operation_ref"
        ),
        operation_digest=_session_wire_digest(
            root["operation_digest"], f"{field}.operation_digest"
        ),
        source_evidence=source,
        expected_session_head_revision=_nonnegative(
            root["expected_session_head_revision"],
            f"{field}.expected_session_head_revision",
        ),
        expected_cursor=_nonnegative(
            root["expected_cursor"], f"{field}.expected_cursor"
        ),
        expected_predecessor_event_digest=predecessor,
    )
    if canonical_json_bytes(request.to_wire()) != canonical_json_bytes(root):
        raise WorkspaceMaterializationSessionError(
            "stored session append request V2 differs from fresh derivation"
        )
    return request


def _parse_session_head_v2_wire(
    wire: bytes,
) -> WorkspaceMaterializationSessionHeadV2:
    root = _canonical_session_wire_root(wire, "session head V2")
    if root.get("contract") != WORKSPACE_MATERIALIZATION_SESSION_HEAD_V2:
        raise WorkspaceMaterializationSessionError(
            "stored session head V2 contract differs"
        )
    root = _session_wire_keys(
        root,
        {
            "contract",
            "cursor",
            "epoch",
            "event_digest",
            "head_digest",
            "workspace_session_ref",
        },
        "session head V2",
    )
    values = {
        "workspace_session_ref": _session_wire_token(
            root["workspace_session_ref"], "session head V2.workspace_session_ref"
        ),
        "epoch": _session_wire_token(root["epoch"], "session head V2.epoch"),
        "cursor": _positive(root["cursor"], "session head V2.cursor"),
        "event_digest": _session_wire_digest(
            root["event_digest"], "session head V2.event_digest"
        ),
    }
    head = WorkspaceMaterializationSessionHeadV2(
        **values,
        head_digest=_session_wire_digest(
            root["head_digest"], "session head V2.head_digest"
        ),
    )
    if canonical_json_bytes(head.to_wire()) != wire:
        raise WorkspaceMaterializationSessionError(
            "stored session head V2 differs from fresh validation"
        )
    return head


def _wire_contract(wire: bytes, field: str) -> str:
    root = _canonical_session_wire_root(wire, field)
    return _session_wire_token(root.get("contract"), f"{field}.contract")


def _canonical_session_wire_root(wire: bytes, field: str) -> dict[str, object]:
    if type(wire) is not bytes:
        raise TypeError(f"{field} wire must be exact bytes")
    try:
        value = json.loads(wire)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WorkspaceMaterializationSessionError(
            f"{field} wire is not JSON"
        ) from error
    root = _session_wire_mapping(value, field)
    if canonical_json_bytes(root) != wire:
        raise WorkspaceMaterializationSessionError(f"{field} wire is not canonical")
    return root


def _session_wire_mapping(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, Mapping) or any(type(key) is not str for key in value):
        raise WorkspaceMaterializationSessionError(
            f"{field} must be exact string-keyed object"
        )
    return {cast(str, key): item for key, item in value.items()}


def _thaw_session_json(value: object) -> object:
    if value is None or type(value) in {str, bool, int, float}:
        return value
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise WorkspaceMaterializationSessionError(
                "stored session state contains non-string key"
            )
        return {cast(str, key): _thaw_session_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_thaw_session_json(item) for item in value]
    raise WorkspaceMaterializationSessionError(
        "stored session state contains unsupported value"
    )


def _session_wire_keys(
    value: object, expected: set[str], field: str
) -> dict[str, object]:
    root = _session_wire_mapping(value, field)
    if set(root) != expected:
        raise WorkspaceMaterializationSessionError(f"{field} fields differ")
    return root


def _session_wire_token(value: object, field: str) -> str:
    if type(value) is not str:
        raise WorkspaceMaterializationSessionError(f"{field} must be exact string")
    return _token(value, field)


def _session_wire_digest(value: object, field: str) -> ContentDigest:
    try:
        return ContentDigest.of_wire(value, field)
    except (TypeError, ValueError) as error:
        raise WorkspaceMaterializationSessionError(f"{field} digest differs") from error


def _stored_wire(value: JsonObject, label: str) -> bytes:
    if not isinstance(value, dict) or set(value) != {"wire", "wire_digest"}:
        raise WorkspaceMaterializationSessionError(f"{label} wrapper differs")
    wire_text = value["wire"]
    digest = value["wire_digest"]
    if type(wire_text) is not str or type(digest) is not str:
        raise WorkspaceMaterializationSessionError(f"{label} wrapper types differ")
    wire = wire_text.encode("utf-8")
    if ContentDigest.of_bytes(wire).value != digest:
        raise WorkspaceMaterializationSessionError(f"{label} wrapper digest differs")
    return wire


def _package_page(
    values: tuple[str, ...], *, permitted: tuple[str, ...], maximum: int
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise TypeError("package refs must be an exact tuple")
    normalized = tuple(sorted({_token(item, "package_ref") for item in values}))
    if normalized != values:
        raise WorkspaceMaterializationSessionError(
            "snapshot package refs are not canonical"
        )
    if len(values) > maximum:
        raise WorkspaceMaterializationSessionError(
            "snapshot package page exceeds limit"
        )
    if any(item not in permitted for item in values):
        raise WorkspaceMaterializationSessionError(
            "snapshot package ref is not admitted"
        )
    return values


def _decode_json_object(value: bytes, fields: set[str]) -> dict[str, object]:
    if type(value) is not bytes:
        raise TypeError("wire must be exact bytes")
    try:
        payload = json.loads(value)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WorkspaceMaterializationSessionError("wire is invalid JSON") from error
    if (
        type(payload) is not dict
        or set(payload) != fields
        or any(type(key) is not str for key in payload)
    ):
        raise WorkspaceMaterializationSessionError("wire fields differ")
    return cast(dict[str, object], payload)


def _semantic_digest(contract: str, payload: object) -> str:
    return ContentDigest.of_bytes(
        canonical_json_bytes({"contract": contract, "value": payload})
    ).value


def _token(value: object, field: str) -> str:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or any(character.isspace() for character in value)
    ):
        raise WorkspaceMaterializationSessionError(f"{field} must be a nonempty token")
    return value


def _digest(value: object, field: str) -> str:
    item = _token(value, field)
    if len(item) != 71 or not item.startswith(_DIGEST_PREFIX) or item != item.lower():
        raise WorkspaceMaterializationSessionError(f"{field} must be lowercase SHA-256")
    try:
        int(item[7:], 16)
    except ValueError as error:
        raise WorkspaceMaterializationSessionError(
            f"{field} must be lowercase SHA-256"
        ) from error
    return item


def _nonnegative(value: object, field: str) -> int:
    if type(value) is not int or value < 0:
        raise WorkspaceMaterializationSessionError(
            f"{field} must be a nonnegative integer"
        )
    return value


def _positive(value: object, field: str) -> int:
    result = _nonnegative(value, field)
    if result == 0:
        raise WorkspaceMaterializationSessionError(f"{field} must be positive")
    return result


def _string(value: object) -> str:
    if type(value) is not str:
        raise WorkspaceMaterializationSessionError("wire string type differs")
    return value


def _integer(value: object) -> int:
    if type(value) is not int:
        raise WorkspaceMaterializationSessionError("wire integer type differs")
    return value


def _optional_string(value: object) -> str | None:
    return None if value is None else _string(value)


def _list(value: object) -> list[object]:
    if type(value) is not list:
        raise WorkspaceMaterializationSessionError("wire list type differs")
    return cast(list[object], value)


__all__ = [
    "WORKSPACE_MATERIALIZATION_SESSION_APPEND_REQUEST",
    "WORKSPACE_MATERIALIZATION_SESSION_APPEND_REQUEST_V3",
    "WORKSPACE_MATERIALIZATION_SESSION_EVENT",
    "WORKSPACE_MATERIALIZATION_SESSION_EVENT_REREAD_EVIDENCE_V3",
    "WORKSPACE_MATERIALIZATION_SESSION_EVENT_V3",
    "WORKSPACE_MATERIALIZATION_SESSION_FANOUT_RECEIPT",
    "WORKSPACE_MATERIALIZATION_SESSION_FANOUT_RECEIPT_V3",
    "WORKSPACE_MATERIALIZATION_SESSION_HEAD",
    "WORKSPACE_MATERIALIZATION_SESSION_HEAD_V2",
    "WORKSPACE_MATERIALIZATION_SESSION_SOURCE_EVIDENCE_V3",
    "WORKSPACE_MATERIALIZATION_SESSION_SNAPSHOT",
    "WorkspaceMaterializationSessionAdmission",
    "WorkspaceMaterializationSessionAppendMetrics",
    "WorkspaceMaterializationSessionAppendRequest",
    "WorkspaceMaterializationSessionAppendRequestV3",
    "WorkspaceMaterializationSessionAppendResult",
    "WorkspaceMaterializationSessionAuthorityGrade",
    "WorkspaceMaterializationSessionBaselineGrade",
    "WorkspaceMaterializationSessionConflict",
    "WorkspaceMaterializationSessionError",
    "WorkspaceMaterializationSessionEvent",
    "WorkspaceMaterializationSessionEventRereadEvidenceV3",
    "WorkspaceMaterializationSessionEventV3",
    "WorkspaceMaterializationSessionFanoutReceipt",
    "WorkspaceMaterializationSessionFanoutReceiptV3",
    "WorkspaceMaterializationSessionGap",
    "WorkspaceMaterializationSessionGapReason",
    "WorkspaceMaterializationSessionHead",
    "WorkspaceMaterializationSessionHeadV2",
    "WorkspaceMaterializationSessionJournal",
    "WorkspaceMaterializationSessionOperationAuthority",
    "WorkspaceMaterializationSessionPackageHead",
    "WorkspaceMaterializationSessionPackageHeadResolver",
    "WorkspaceMaterializationSessionReadMetrics",
    "WorkspaceMaterializationSessionReplay",
    "WorkspaceMaterializationSessionSnapshot",
    "WorkspaceMaterializationSessionSourceEvidenceV3",
    "admit_workspace_materialization_session_append",
    "decode_workspace_materialization_session_append_request_v2",
    "decode_workspace_materialization_session_event_reread_evidence_v2",
    "decode_workspace_materialization_session_event_v2",
    "decode_workspace_materialization_session_fanout_receipt_v2",
    "decode_workspace_materialization_session_source_evidence_v2",
    "encode_workspace_materialization_session_append_request_v2",
    "encode_workspace_materialization_session_event_reread_evidence_v2",
    "encode_workspace_materialization_session_event_v2",
    "encode_workspace_materialization_session_fanout_receipt_v2",
    "encode_workspace_materialization_session_source_evidence_v2",
]
