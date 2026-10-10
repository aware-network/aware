"""One Workspace-owned neutral semantic materialization operation."""

from __future__ import annotations

import json
import time
from collections.abc import Awaitable, Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from threading import RLock
from typing import Never, Protocol, Self, cast
from weakref import WeakKeyDictionary

from aware_code_semantic_contract_runtime import (
    CodeSemanticRequiredResultProduct,
    ContentDigest,
    ExecutionCompletion,
    ExecutionPublicationSnapshot,
    SemanticBody,
    SemanticContractInvocation,
    SemanticContractRuntime,
    SemanticValueCoordinate,
    TypedEmptyCoordinate,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.selected_provider import (
    AdmittedSemanticProviderRegistration,
    SelectedProviderInvocationClosure,
    execute_selected_provider,
    issue_selected_provider_execution,
)

from .materialization_membership_catalog import _source_identity
from .materialization_session import (
    WorkspaceMaterializationSessionAppendRequest,
    WorkspaceMaterializationSessionAppendRequestV3,
    WorkspaceMaterializationSessionAppendResult,
    WorkspaceMaterializationSessionAuthorityGrade,
    WorkspaceMaterializationSessionBaselineGrade,
    WorkspaceMaterializationSessionJournal,
    WorkspaceMaterializationSessionSourceEvidenceV3,
    _WorkspaceMaterializationSessionAppendResultV2,
    admit_workspace_materialization_session_append,
)
from .semantic_dependency_graph import (
    WorkspaceSemanticMaterializationGraphPlanResult,
    WorkspaceSemanticMaterializationNodeExecutionBinding,
)
from .semantic_materialization_publication import (
    WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
    WorkspaceSemanticMaterializationPublication,
    WorkspaceSemanticMaterializationPublicationReceiptV3,
    WorkspaceSemanticMaterializationPublisher,
    WorkspaceSemanticMaterializationRequest,
    WorkspaceSemanticMaterializationRequestV3,
    admit_workspace_semantic_materialization,
)
from .source_admission import (
    WorkspaceOwnerDefinedSourceAdmission,
    WorkspaceOwnerDefinedSourceAdmissionRuntime,
    WorkspaceOwnerDefinedSourceInspection,
    WorkspaceV3OwnerDefinedSourceAdmissionRuntime,
)

WORKSPACE_MATERIALIZE_OPERATION_REQUEST = (
    "aware.workspace.semantic-materialize-operation-request.v2"
)
WORKSPACE_MATERIALIZE_EXECUTION_INPUT_CLOSURE = (
    "aware.workspace.materialize-execution-input-closure.v1"
)
WORKSPACE_MATERIALIZE_EXECUTION_PLAN = (
    "aware.workspace.semantic-materialize-execution-plan.v1"
)
WORKSPACE_MATERIALIZE_OPERATION_NON_CLAIMS = (
    "canonical_commit",
    "canonical_replica",
    "checkout_apply",
    "generated_product_activation",
    "oig_commit",
    "workspace_revision",
)
WORKSPACE_MATERIALIZE_OPERATION_STAGE_ORDER = (
    "plan",
    "execution",
    "publication",
    "fanout",
)

_DIGEST_PREFIX = "sha256:"


class WorkspaceMaterializeOperationError(RuntimeError):
    """The neutral operation contract or one of its stages failed."""


class WorkspaceMaterializeOperationStageError(WorkspaceMaterializeOperationError):
    """A named operation stage failed without issuing a complete result."""

    def __init__(
        self,
        stage: str,
        cause: Exception,
        *,
        stage_timings_ns: tuple[tuple[str, int], ...],
        total_ns: int,
    ) -> None:
        self.stage = _token(stage, "stage")
        if self.stage not in WORKSPACE_MATERIALIZE_OPERATION_STAGE_ORDER:
            raise WorkspaceMaterializeOperationError(
                "operation failure stage is unsupported"
            )
        if type(stage_timings_ns) is not tuple or not stage_timings_ns:
            raise TypeError("operation failure stage timings must be a nonempty tuple")
        expected_prefix = WORKSPACE_MATERIALIZE_OPERATION_STAGE_ORDER[
            : WORKSPACE_MATERIALIZE_OPERATION_STAGE_ORDER.index(self.stage) + 1
        ]
        names: list[str] = []
        for item in stage_timings_ns:
            if (
                type(item) is not tuple
                or len(item) != 2
                or type(item[0]) is not str
                or type(item[1]) is not int
            ):
                raise TypeError("operation failure stage timing must be exact")
            names.append(_token(item[0], "stage_timing_name"))
            _nonnegative(item[1], "stage_timing_ns")
        if tuple(names) != expected_prefix:
            raise WorkspaceMaterializeOperationError(
                "operation failure stage timings are not an exact prefix"
            )
        _nonnegative(total_ns, "total_ns")
        if total_ns < sum(value for _, value in stage_timings_ns):
            raise WorkspaceMaterializeOperationError(
                "operation failure total is shorter than its stage timings"
            )
        self.cause = cause
        self.failure_code = f"{self.stage}_failed"
        self.stage_timings_ns = stage_timings_ns
        self.total_ns = total_ns
        super().__init__(f"Workspace materialize stage {stage} failed: {cause}")


class WorkspaceMaterializeOperationAuthority(Protocol):
    @property
    def operation_ref(self) -> str: ...

    @property
    def operation_digest(self) -> str: ...

    @property
    def authority_grade(self) -> WorkspaceMaterializationSessionAuthorityGrade: ...

    def admits(self, request: WorkspaceMaterializeOperationRequest) -> bool: ...

    def permitted_package_refs_for(
        self, request: WorkspaceMaterializeOperationRequest
    ) -> tuple[str, ...]: ...


class WorkspaceMaterializeExecutionInputCompositionAuthority(Protocol):
    """Workspace host authority over one exact neutral Code input closure."""

    @property
    def authority_grade(self) -> WorkspaceMaterializationSessionAuthorityGrade: ...

    def admits_composition(
        self,
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
        plan_resolver_ref: str,
        plan_resolver_digest: str,
        execution_input_closure_digest: str,
    ) -> bool: ...


class WorkspaceMaterializeExecutionPlanResolver(Protocol):
    @property
    def implementation_ref(self) -> str: ...

    @property
    def implementation_digest(self) -> str: ...

    @property
    def profile_ref(self) -> str: ...

    @property
    def profile_digest(self) -> str: ...

    def resolve(
        self, admission: WorkspaceMaterializeOperationAdmission
    ) -> Awaitable[WorkspaceMaterializeExecutionPlan]: ...


class WorkspaceGraphNodeExecutionPlanResolver(
    WorkspaceMaterializeExecutionPlanResolver, Protocol
):
    """Resolve graph inputs while retaining the original command-owned node use.

    The use stays with the Workspace resolver. Semantic owners receive detached
    Code inputs, never this nominal source and execution lifetime.
    """

    def resolve_graph_node(
        self,
        admission: WorkspaceMaterializeOperationAdmission,
        *,
        node_use: object,
    ) -> Awaitable[WorkspaceMaterializeExecutionPlan]: ...


def derive_workspace_materialize_execution_input_closure_digest(
    input_bodies: tuple[SemanticBody, ...],
) -> str:
    """Derive portable identity for one exact ordered neutral Code input closure."""

    if type(input_bodies) is not tuple:
        raise TypeError("execution input bodies must be an exact tuple")
    coordinate_wires: list[dict[str, object]] = []
    ordering_keys: list[bytes] = []
    for body in input_bodies:
        if type(body) is not SemanticBody:
            raise TypeError("execution input body must be exact SemanticBody")
        body.__post_init__()
        coordinate = body.coordinate
        wire = cast(dict[str, object], coordinate.to_wire())
        ordering_key = canonical_json_bytes(wire)
        coordinate_wires.append(wire)
        ordering_keys.append(ordering_key)
    if len(set(ordering_keys)) != len(ordering_keys):
        raise WorkspaceMaterializeOperationError(
            "execution input coordinates must be unique"
        )
    if tuple(ordering_keys) != tuple(sorted(ordering_keys)):
        raise WorkspaceMaterializeOperationError(
            "execution input bodies must be in canonical coordinate order"
        )
    return _semantic_digest(
        WORKSPACE_MATERIALIZE_EXECUTION_INPUT_CLOSURE,
        {"coordinates": coordinate_wires},
    )


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializeOperationRequest:
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
    package_kind: str
    manifest_digest: str
    source_authority_ref: str
    source_authority_digest: str
    operation_ref: str
    operation_digest: str
    profile_ref: str
    profile_digest: str
    plan_resolver_ref: str
    plan_resolver_digest: str
    execution_input_closure_digest: str
    expected_materialization_head_revision: int
    expected_session_head_revision: int
    expected_session_cursor: int
    expected_predecessor_event_digest: str | None
    request_digest: str
    contract: str = WORKSPACE_MATERIALIZE_OPERATION_REQUEST
    non_claims: tuple[str, ...] = WORKSPACE_MATERIALIZE_OPERATION_NON_CLAIMS

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_MATERIALIZE_OPERATION_REQUEST:
            raise WorkspaceMaterializeOperationError(
                "operation request contract differs"
            )
        if tuple(self.non_claims) != WORKSPACE_MATERIALIZE_OPERATION_NON_CLAIMS:
            raise WorkspaceMaterializeOperationError(
                "operation request non-claims differ"
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
            "operation_ref",
            "profile_ref",
            "plan_resolver_ref",
        ):
            _token(getattr(self, field), field)
        for field in (
            "branch_baseline_digest",
            "manifest_digest",
            "source_authority_digest",
            "operation_digest",
            "profile_digest",
            "plan_resolver_digest",
            "execution_input_closure_digest",
        ):
            _digest(getattr(self, field), field)
        try:
            WorkspaceMaterializationSessionBaselineGrade(self.branch_baseline_grade)
        except ValueError as error:
            raise WorkspaceMaterializeOperationError(
                "branch baseline grade unsupported"
            ) from error
        _nonnegative(
            self.expected_materialization_head_revision,
            "expected_materialization_head_revision",
        )
        _nonnegative(
            self.expected_session_head_revision,
            "expected_session_head_revision",
        )
        _nonnegative(self.expected_session_cursor, "expected_session_cursor")
        if self.expected_predecessor_event_digest is None:
            if (
                self.expected_session_head_revision != 0
                or self.expected_session_cursor != 0
            ):
                raise WorkspaceMaterializeOperationError(
                    "only genesis session request may omit predecessor"
                )
        else:
            _digest(
                self.expected_predecessor_event_digest,
                "expected_predecessor_event_digest",
            )
            if (
                self.expected_session_head_revision == 0
                or self.expected_session_cursor == 0
            ):
                raise WorkspaceMaterializeOperationError(
                    "session successor requires revision, cursor and predecessor"
                )
        if self.request_digest != _semantic_digest(self.contract, self._payload()):
            raise WorkspaceMaterializeOperationError(
                "operation request digest mismatched"
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
        package_kind: str,
        manifest_digest: str,
        source_authority_ref: str,
        source_authority_digest: str,
        operation_ref: str,
        operation_digest: str,
        profile_ref: str,
        profile_digest: str,
        plan_resolver_ref: str,
        plan_resolver_digest: str,
        execution_input_closure_digest: str,
        expected_materialization_head_revision: int,
        expected_session_head_revision: int,
        expected_session_cursor: int,
        expected_predecessor_event_digest: str | None,
    ) -> WorkspaceMaterializeOperationRequest:
        values: dict[str, object] = {
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
            "package_kind": package_kind,
            "manifest_digest": manifest_digest,
            "source_authority_ref": source_authority_ref,
            "source_authority_digest": source_authority_digest,
            "operation_ref": operation_ref,
            "operation_digest": operation_digest,
            "profile_ref": profile_ref,
            "profile_digest": profile_digest,
            "plan_resolver_ref": plan_resolver_ref,
            "plan_resolver_digest": plan_resolver_digest,
            "execution_input_closure_digest": execution_input_closure_digest,
            "expected_materialization_head_revision": (
                expected_materialization_head_revision
            ),
            "expected_session_head_revision": expected_session_head_revision,
            "expected_session_cursor": expected_session_cursor,
            "expected_predecessor_event_digest": (expected_predecessor_event_digest),
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
            package_kind=package_kind,
            manifest_digest=manifest_digest,
            source_authority_ref=source_authority_ref,
            source_authority_digest=source_authority_digest,
            operation_ref=operation_ref,
            operation_digest=operation_digest,
            profile_ref=profile_ref,
            profile_digest=profile_digest,
            plan_resolver_ref=plan_resolver_ref,
            plan_resolver_digest=plan_resolver_digest,
            execution_input_closure_digest=execution_input_closure_digest,
            expected_materialization_head_revision=(
                expected_materialization_head_revision
            ),
            expected_session_head_revision=expected_session_head_revision,
            expected_session_cursor=expected_session_cursor,
            expected_predecessor_event_digest=expected_predecessor_event_digest,
            request_digest=_semantic_digest(
                WORKSPACE_MATERIALIZE_OPERATION_REQUEST, values
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
                "package_kind",
                "manifest_digest",
                "source_authority_ref",
                "source_authority_digest",
                "operation_ref",
                "operation_digest",
                "profile_ref",
                "profile_digest",
                "plan_resolver_ref",
                "plan_resolver_digest",
                "execution_input_closure_digest",
                "expected_materialization_head_revision",
                "expected_session_head_revision",
                "expected_session_cursor",
                "expected_predecessor_event_digest",
            )
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            **self._payload(),
            "request_digest": self.request_digest,
            "non_claims": list(self.non_claims),
        }

    def to_json_bytes(self) -> bytes:
        self.__post_init__()
        return canonical_json_bytes(self.to_dict())

    @classmethod
    def from_json_bytes(cls, value: bytes) -> WorkspaceMaterializeOperationRequest:
        payload = _decode_object(value, set(cls.__dataclass_fields__))
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
            package_kind=_string(payload["package_kind"]),
            manifest_digest=_string(payload["manifest_digest"]),
            source_authority_ref=_string(payload["source_authority_ref"]),
            source_authority_digest=_string(payload["source_authority_digest"]),
            operation_ref=_string(payload["operation_ref"]),
            operation_digest=_string(payload["operation_digest"]),
            profile_ref=_string(payload["profile_ref"]),
            profile_digest=_string(payload["profile_digest"]),
            plan_resolver_ref=_string(payload["plan_resolver_ref"]),
            plan_resolver_digest=_string(payload["plan_resolver_digest"]),
            execution_input_closure_digest=_string(
                payload["execution_input_closure_digest"]
            ),
            expected_materialization_head_revision=_integer(
                payload["expected_materialization_head_revision"]
            ),
            expected_session_head_revision=_integer(
                payload["expected_session_head_revision"]
            ),
            expected_session_cursor=_integer(payload["expected_session_cursor"]),
            expected_predecessor_event_digest=_optional_string(
                payload["expected_predecessor_event_digest"]
            ),
            request_digest=_string(payload["request_digest"]),
            contract=_string(payload["contract"]),
            non_claims=tuple(_string(item) for item in _list(payload["non_claims"])),
        )
        if result.to_json_bytes() != value:
            raise WorkspaceMaterializeOperationError(
                "operation request is not canonical JSON"
            )
        return result


@dataclass(frozen=True, slots=True)
class _ExecutionInputAdmissionState:
    package_ref: str
    package_kind: str
    manifest_digest: str
    source_authority_ref: str
    source_authority_digest: str
    operation_ref: str
    operation_digest: str
    profile_ref: str
    profile_digest: str
    plan_resolver_ref: str
    plan_resolver_digest: str
    execution_input_closure_digest: str
    authority_grade: WorkspaceMaterializationSessionAuthorityGrade


_EXECUTION_INPUT_ADMISSIONS: WeakKeyDictionary[
    WorkspaceMaterializeExecutionInputCompositionAdmission,
    _ExecutionInputAdmissionState,
] = WeakKeyDictionary()
_EXECUTION_INPUT_ADMISSIONS_LOCK = RLock()


class WorkspaceMaterializeExecutionInputCompositionAdmission:
    """Workspace-issued nominal authority for one exact Code input closure."""

    def __new__(
        cls,
    ) -> Self:
        raise TypeError("execution input admission is Workspace-constructed only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("execution input admission is sealed")

    @property
    def execution_input_closure_digest(self) -> str:
        return _execution_input_admission_state(self).execution_input_closure_digest

    @property
    def authority_grade(self) -> WorkspaceMaterializationSessionAuthorityGrade:
        return _execution_input_admission_state(self).authority_grade

    def _assert_intact(self) -> None:
        state = _execution_input_admission_state(self)
        for field in (
            "package_ref",
            "package_kind",
            "source_authority_ref",
            "operation_ref",
            "profile_ref",
            "plan_resolver_ref",
        ):
            _token(getattr(state, field), field)
        for field in (
            "manifest_digest",
            "source_authority_digest",
            "operation_digest",
            "profile_digest",
            "plan_resolver_digest",
            "execution_input_closure_digest",
        ):
            _digest(getattr(state, field), field)
        if (
            type(state.authority_grade)
            is not WorkspaceMaterializationSessionAuthorityGrade
        ):
            raise WorkspaceMaterializeOperationError(
                "execution input authority grade differs"
            )

    def __reduce__(self) -> Never:
        raise TypeError("execution input admission is not serializable")


def admit_workspace_materialize_execution_input_composition(
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
    plan_resolver_ref: str,
    plan_resolver_digest: str,
    input_bodies: tuple[SemanticBody, ...],
    composition_authority: WorkspaceMaterializeExecutionInputCompositionAuthority,
) -> WorkspaceMaterializeExecutionInputCompositionAdmission:
    values = {
        "package_ref": _token(package_ref, "package_ref"),
        "package_kind": _token(package_kind, "package_kind"),
        "manifest_digest": _digest(manifest_digest, "manifest_digest"),
        "source_authority_ref": _token(source_authority_ref, "source_authority_ref"),
        "source_authority_digest": _digest(
            source_authority_digest, "source_authority_digest"
        ),
        "operation_ref": _token(operation_ref, "operation_ref"),
        "operation_digest": _digest(operation_digest, "operation_digest"),
        "profile_ref": _token(profile_ref, "profile_ref"),
        "profile_digest": _digest(profile_digest, "profile_digest"),
        "plan_resolver_ref": _token(plan_resolver_ref, "plan_resolver_ref"),
        "plan_resolver_digest": _digest(plan_resolver_digest, "plan_resolver_digest"),
        "execution_input_closure_digest": (
            derive_workspace_materialize_execution_input_closure_digest(input_bodies)
        ),
    }
    grade = composition_authority.authority_grade
    if type(grade) is not WorkspaceMaterializationSessionAuthorityGrade:
        raise WorkspaceMaterializeOperationError(
            "execution input authority grade is not nominal"
        )
    admitted = composition_authority.admits_composition(**values)
    if type(admitted) is not bool or not admitted:
        raise WorkspaceMaterializeOperationError(
            "Workspace execution input composition was not admitted"
        )
    admission = object.__new__(WorkspaceMaterializeExecutionInputCompositionAdmission)
    with _EXECUTION_INPUT_ADMISSIONS_LOCK:
        _EXECUTION_INPUT_ADMISSIONS[admission] = _ExecutionInputAdmissionState(
            **values,
            authority_grade=grade,
        )
    return admission


def _execution_input_admission_state(
    admission: WorkspaceMaterializeExecutionInputCompositionAdmission,
) -> _ExecutionInputAdmissionState:
    if type(admission) is not WorkspaceMaterializeExecutionInputCompositionAdmission:
        raise TypeError("execution input admission must be exact")
    with _EXECUTION_INPUT_ADMISSIONS_LOCK:
        state = _EXECUTION_INPUT_ADMISSIONS.get(admission)
    if state is None:
        raise WorkspaceMaterializeOperationError(
            "execution input admission is not registered"
        )
    return state


@dataclass(frozen=True, slots=True)
class _AdmissionState:
    request: WorkspaceMaterializeOperationRequest
    authority_grade: WorkspaceMaterializationSessionAuthorityGrade
    permitted_package_refs: tuple[str, ...]
    execution_input_admission: WorkspaceMaterializeExecutionInputCompositionAdmission


_ADMISSIONS: WeakKeyDictionary[
    WorkspaceMaterializeOperationAdmission, _AdmissionState
] = WeakKeyDictionary()
_ADMISSIONS_LOCK = RLock()


class WorkspaceMaterializeOperationAdmission:
    """Runtime-issued, nonserializable operation authority."""

    def __new__(cls) -> WorkspaceMaterializeOperationAdmission:  # noqa: PYI034
        raise TypeError("materialize operation admission is Workspace-constructed only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("materialize operation admission is sealed")

    @property
    def request(self) -> WorkspaceMaterializeOperationRequest:
        return _admission_state(self).request

    @property
    def authority_grade(self) -> WorkspaceMaterializationSessionAuthorityGrade:
        return _admission_state(self).authority_grade

    @property
    def permitted_package_refs(self) -> tuple[str, ...]:
        return _admission_state(self).permitted_package_refs

    @property
    def execution_input_admission(
        self,
    ) -> WorkspaceMaterializeExecutionInputCompositionAdmission:
        return _admission_state(self).execution_input_admission

    def _assert_intact(self) -> None:
        state = _admission_state(self)
        state.request.__post_init__()
        if (
            type(state.authority_grade)
            is not WorkspaceMaterializationSessionAuthorityGrade
        ):
            raise WorkspaceMaterializeOperationError(
                "operation authority grade differs"
            )
        if state.permitted_package_refs != tuple(
            sorted(set(state.permitted_package_refs))
        ):
            raise WorkspaceMaterializeOperationError(
                "operation permitted packages differ"
            )
        state.execution_input_admission._assert_intact()
        execution_input = _execution_input_admission_state(
            state.execution_input_admission
        )
        if (
            execution_input.authority_grade is not state.authority_grade
            or execution_input.package_ref != state.request.package_ref
            or execution_input.package_kind != state.request.package_kind
            or execution_input.manifest_digest != state.request.manifest_digest
            or execution_input.source_authority_ref
            != state.request.source_authority_ref
            or execution_input.source_authority_digest
            != state.request.source_authority_digest
            or execution_input.operation_ref != state.request.operation_ref
            or execution_input.operation_digest != state.request.operation_digest
            or execution_input.profile_ref != state.request.profile_ref
            or execution_input.profile_digest != state.request.profile_digest
            or execution_input.plan_resolver_ref != state.request.plan_resolver_ref
            or execution_input.plan_resolver_digest
            != state.request.plan_resolver_digest
            or execution_input.execution_input_closure_digest
            != state.request.execution_input_closure_digest
        ):
            raise WorkspaceMaterializeOperationError(
                "execution input admission differs from operation"
            )

    def __reduce__(self) -> Never:
        raise TypeError("materialize operation admission is not serializable")


def admit_workspace_materialize_operation(
    *,
    request: WorkspaceMaterializeOperationRequest,
    operation_authority: WorkspaceMaterializeOperationAuthority,
    execution_input_admission: (WorkspaceMaterializeExecutionInputCompositionAdmission),
) -> WorkspaceMaterializeOperationAdmission:
    if type(request) is not WorkspaceMaterializeOperationRequest:
        raise TypeError("request must be exact materialize operation request")
    request.__post_init__()
    if (
        _token(operation_authority.operation_ref, "operation_ref")
        != request.operation_ref
        or _digest(operation_authority.operation_digest, "operation_digest")
        != request.operation_digest
    ):
        raise WorkspaceMaterializeOperationError(
            "operation authority differs from request"
        )
    grade = operation_authority.authority_grade
    if type(grade) is not WorkspaceMaterializationSessionAuthorityGrade:
        raise WorkspaceMaterializeOperationError("authority grade is not nominal")
    execution_input_state = _execution_input_admission_state(execution_input_admission)
    execution_input_admission._assert_intact()
    if (
        execution_input_state.authority_grade is not grade
        or execution_input_state.package_ref != request.package_ref
        or execution_input_state.package_kind != request.package_kind
        or execution_input_state.manifest_digest != request.manifest_digest
        or execution_input_state.source_authority_ref != request.source_authority_ref
        or execution_input_state.source_authority_digest
        != request.source_authority_digest
        or execution_input_state.operation_ref != request.operation_ref
        or execution_input_state.operation_digest != request.operation_digest
        or execution_input_state.profile_ref != request.profile_ref
        or execution_input_state.profile_digest != request.profile_digest
        or execution_input_state.plan_resolver_ref != request.plan_resolver_ref
        or execution_input_state.plan_resolver_digest != request.plan_resolver_digest
        or execution_input_state.execution_input_closure_digest
        != request.execution_input_closure_digest
    ):
        raise WorkspaceMaterializeOperationError(
            "execution input admission differs from request"
        )
    admitted = operation_authority.admits(request)
    if type(admitted) is not bool or not admitted:
        raise WorkspaceMaterializeOperationError(
            "Workspace operation did not admit request"
        )
    permitted = operation_authority.permitted_package_refs_for(request)
    if type(permitted) is not tuple:
        raise TypeError("permitted packages must be an exact tuple")
    normalized = tuple(
        sorted({_token(item, "permitted_package_ref") for item in permitted})
    )
    if normalized != permitted or request.package_ref not in normalized:
        raise WorkspaceMaterializeOperationError(
            "permitted packages are noncanonical or omit target"
        )
    admission = object.__new__(WorkspaceMaterializeOperationAdmission)
    with _ADMISSIONS_LOCK:
        _ADMISSIONS[admission] = _AdmissionState(
            request,
            grade,
            normalized,
            execution_input_admission,
        )
    return admission


def _admission_state(
    admission: WorkspaceMaterializeOperationAdmission,
) -> _AdmissionState:
    if type(admission) is not WorkspaceMaterializeOperationAdmission:
        raise TypeError("admission must be exact materialize operation admission")
    with _ADMISSIONS_LOCK:
        state = _ADMISSIONS.get(admission)
    if state is None:
        raise WorkspaceMaterializeOperationError(
            "materialize operation admission is not registered"
        )
    return state


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializeExecutionPlan:
    source_authority_ref: str
    source_authority_digest: str
    operation_ref: str
    operation_digest: str
    package_ref: str
    package_kind: str
    manifest_digest: str
    profile_ref: str
    profile_digest: str
    invocation: SemanticContractInvocation
    input_bodies: tuple[SemanticBody, ...]
    predecessor_body: SemanticBody | None
    plan_digest: str
    contract: str = WORKSPACE_MATERIALIZE_EXECUTION_PLAN

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_MATERIALIZE_EXECUTION_PLAN:
            raise WorkspaceMaterializeOperationError("execution plan contract differs")
        for field in (
            "source_authority_ref",
            "operation_ref",
            "package_ref",
            "package_kind",
            "profile_ref",
        ):
            _token(getattr(self, field), field)
        for field in (
            "source_authority_digest",
            "operation_digest",
            "manifest_digest",
            "profile_digest",
        ):
            _digest(getattr(self, field), field)
        if type(self.invocation) is not SemanticContractInvocation:
            raise TypeError("execution plan invocation must be exact")
        self.invocation.__post_init__()
        if type(self.input_bodies) is not tuple or any(
            type(item) is not SemanticBody for item in self.input_bodies
        ):
            raise TypeError("execution plan input bodies must be exact")
        for item in self.input_bodies:
            item.__post_init__()
        ordered = tuple(
            sorted(
                self.input_bodies,
                key=lambda item: canonical_json_bytes(item.coordinate.to_wire()),
            )
        )
        if self.input_bodies != ordered or len(
            {item.coordinate for item in self.input_bodies}
        ) != len(self.input_bodies):
            raise WorkspaceMaterializeOperationError(
                "execution plan input bodies are not canonical"
            )
        if {item.coordinate for item in self.input_bodies} != set(
            self.invocation.inputs
        ):
            raise WorkspaceMaterializeOperationError(
                "execution plan bodies differ from invocation inputs"
            )
        if type(self.invocation.predecessor) is TypedEmptyCoordinate:
            if self.predecessor_body is not None:
                raise WorkspaceMaterializeOperationError(
                    "typed-empty plan cannot carry predecessor body"
                )
        else:
            if type(self.predecessor_body) is not SemanticBody:
                raise WorkspaceMaterializeOperationError(
                    "successor plan requires predecessor body"
                )
            self.predecessor_body.__post_init__()
            if self.predecessor_body.coordinate != self.invocation.predecessor:
                raise WorkspaceMaterializeOperationError(
                    "execution plan predecessor body differs"
                )
        if (
            self.invocation.target_package.package_ref != self.package_ref
            or self.invocation.target_package.package_kind != self.package_kind
            or self.invocation.target_package.manifest_digest.value
            != self.manifest_digest
            or self.invocation.profile_ref != self.profile_ref
            or self.invocation.profile_digest.value != self.profile_digest
        ):
            raise WorkspaceMaterializeOperationError(
                "execution plan invocation differs from package/profile"
            )
        if self.plan_digest != _semantic_digest(self.contract, self._payload()):
            raise WorkspaceMaterializeOperationError("execution plan digest mismatched")

    @classmethod
    def create(
        cls,
        *,
        source_authority_ref: str,
        source_authority_digest: str,
        operation_ref: str,
        operation_digest: str,
        invocation: SemanticContractInvocation,
        input_bodies: tuple[SemanticBody, ...],
        predecessor_body: SemanticBody | None = None,
    ) -> WorkspaceMaterializeExecutionPlan:
        ordered = tuple(
            sorted(
                input_bodies,
                key=lambda item: canonical_json_bytes(item.coordinate.to_wire()),
            )
        )
        values: dict[str, object] = {
            "source_authority_ref": source_authority_ref,
            "source_authority_digest": source_authority_digest,
            "operation_ref": operation_ref,
            "operation_digest": operation_digest,
            "package_ref": invocation.target_package.package_ref,
            "package_kind": invocation.target_package.package_kind,
            "manifest_digest": invocation.target_package.manifest_digest.value,
            "profile_ref": invocation.profile_ref,
            "profile_digest": invocation.profile_digest.value,
            "invocation": invocation,
            "input_bodies": ordered,
            "predecessor_body": predecessor_body,
        }
        return cls(
            source_authority_ref=source_authority_ref,
            source_authority_digest=source_authority_digest,
            operation_ref=operation_ref,
            operation_digest=operation_digest,
            package_ref=invocation.target_package.package_ref,
            package_kind=invocation.target_package.package_kind,
            manifest_digest=invocation.target_package.manifest_digest.value,
            profile_ref=invocation.profile_ref,
            profile_digest=invocation.profile_digest.value,
            invocation=invocation,
            input_bodies=ordered,
            predecessor_body=predecessor_body,
            plan_digest=_semantic_digest(
                WORKSPACE_MATERIALIZE_EXECUTION_PLAN, _plan_payload(values)
            ),
        )

    def _payload(self) -> dict[str, object]:
        return _plan_payload(
            {
                "source_authority_ref": self.source_authority_ref,
                "source_authority_digest": self.source_authority_digest,
                "operation_ref": self.operation_ref,
                "operation_digest": self.operation_digest,
                "package_ref": self.package_ref,
                "package_kind": self.package_kind,
                "manifest_digest": self.manifest_digest,
                "profile_ref": self.profile_ref,
                "profile_digest": self.profile_digest,
                "invocation": self.invocation,
                "input_bodies": self.input_bodies,
                "predecessor_body": self.predecessor_body,
            }
        )


class WorkspaceMaterializeGraphNodeUse(Protocol):
    """Original command-owned node use retained across selected execution."""

    def bind_execution_plan(self, plan: WorkspaceMaterializeExecutionPlan) -> None: ...

    def validate(self) -> None: ...


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializeOperationMetrics:
    plan_ns: int
    execution_ns: int
    publication_ns: int
    fanout_ns: int
    total_ns: int

    def __post_init__(self) -> None:
        for field in self.__dataclass_fields__:
            _nonnegative(getattr(self, field), field)


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializeOperationResult:
    request_digest: str
    plan_digest: str
    result_digest: str
    publication: WorkspaceSemanticMaterializationPublication
    fanout: WorkspaceMaterializationSessionAppendResult
    metrics: WorkspaceMaterializeOperationMetrics

    def __post_init__(self) -> None:
        for field in ("request_digest", "plan_digest", "result_digest"):
            _digest(getattr(self, field), field)
        if type(self.publication) is not WorkspaceSemanticMaterializationPublication:
            raise TypeError("operation publication must be exact")
        if type(self.fanout) is not WorkspaceMaterializationSessionAppendResult:
            raise TypeError("operation fanout must be exact")
        if type(self.metrics) is not WorkspaceMaterializeOperationMetrics:
            raise TypeError("operation metrics must be exact")
        if (
            self.result_digest != self.publication.receipt.head.result_digest
            or self.fanout.event.publication_receipt_digest
            != self.publication.receipt.receipt_digest
        ):
            raise WorkspaceMaterializeOperationError(
                "operation result stages are not contiguous"
            )


@dataclass(frozen=True, slots=True)
class _WorkspaceMaterializeGraphOperationResultV2:
    operation_result_digest: ContentDigest
    publication_receipt: WorkspaceSemanticMaterializationPublicationReceiptV3
    package_head_reread_evidence: WorkspaceSemanticMaterializationHeadRereadEvidenceV3
    session_source_evidence: WorkspaceMaterializationSessionSourceEvidenceV3
    session_append_result: _WorkspaceMaterializationSessionAppendResultV2


@dataclass(slots=True)
class _GraphNodeAdmissionState:
    graph_execution_admission: object
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult
    node_binding: WorkspaceSemanticMaterializationNodeExecutionBinding
    execution_input_closure_digest: ContentDigest
    operation: WorkspaceMaterializeOperation
    operation_admission: WorkspaceMaterializeOperationAdmission
    session_append_fence_rereader: Callable[[], None]
    owner: object
    live: bool = True


_GRAPH_NODE_ADMISSIONS: WeakKeyDictionary[
    AdmittedWorkspaceSemanticMaterializationGraphNodeExecution,
    _GraphNodeAdmissionState,
] = WeakKeyDictionary()
_GRAPH_NODE_ADMISSIONS_LOCK = RLock()


class AdmittedWorkspaceSemanticMaterializationGraphNodeExecution:
    """Process-local authority joining one graph node to one existing operation."""

    __slots__ = ("__weakref__",)

    def __new__(cls) -> AdmittedWorkspaceSemanticMaterializationGraphNodeExecution:  # noqa: PYI034
        raise TypeError("graph-node execution admission is Workspace-constructed only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("graph-node execution admission is sealed")

    def __copy__(self) -> Never:
        raise TypeError("graph-node execution admission is not copyable")

    def __deepcopy__(self, memo: object) -> Never:
        del memo
        raise TypeError("graph-node execution admission is not copyable")

    def __reduce__(self) -> Never:
        raise TypeError("graph-node execution admission is not serializable")


def _admit_workspace_semantic_materialization_graph_node_execution(
    *,
    graph_execution_admission: object,
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
    node_binding: WorkspaceSemanticMaterializationNodeExecutionBinding,
    execution_input_closure_digest: ContentDigest,
    operation: WorkspaceMaterializeOperation,
    operation_admission: WorkspaceMaterializeOperationAdmission,
    session_append_fence_rereader: Callable[[], None],
    owner: object,
) -> AdmittedWorkspaceSemanticMaterializationGraphNodeExecution:
    if type(plan_result) is not WorkspaceSemanticMaterializationGraphPlanResult:
        raise TypeError("graph-node plan result must be exact")
    if type(node_binding) is not WorkspaceSemanticMaterializationNodeExecutionBinding:
        raise TypeError("graph-node binding must be exact")
    if type(execution_input_closure_digest) is not ContentDigest:
        raise TypeError("graph-node execution-input closure must be exact")
    if type(operation) is not WorkspaceMaterializeOperation:
        raise TypeError("graph-node operation must be exact")
    if type(operation_admission) is not WorkspaceMaterializeOperationAdmission:
        raise TypeError("graph-node operation admission must be exact")
    if not callable(session_append_fence_rereader):
        raise TypeError("graph-node session-append fence rereader must be callable")
    request = operation_admission.request
    if (
        not any(
            item is node_binding
            for item in plan_result.graph_execution_binding.ordered_node_bindings
        )
        or request.package_ref != node_binding.package.package_ref
        or request.package_kind != node_binding.package.package_kind
        or request.manifest_digest != node_binding.package.manifest_digest.value
        or request.source_authority_ref
        != node_binding.package_entry.source_authority_ref
        or request.source_authority_digest
        != node_binding.package_entry.source_authority_digest.value
        or request.execution_input_closure_digest
        != execution_input_closure_digest.value
    ):
        raise WorkspaceMaterializeOperationError(
            "graph-node operation differs from exact execution binding"
        )
    admission = object.__new__(
        AdmittedWorkspaceSemanticMaterializationGraphNodeExecution
    )
    with _GRAPH_NODE_ADMISSIONS_LOCK:
        _GRAPH_NODE_ADMISSIONS[admission] = _GraphNodeAdmissionState(
            graph_execution_admission=graph_execution_admission,
            plan_result=plan_result,
            node_binding=node_binding,
            execution_input_closure_digest=execution_input_closure_digest,
            operation=operation,
            operation_admission=operation_admission,
            session_append_fence_rereader=session_append_fence_rereader,
            owner=owner,
        )
    return admission


def _graph_node_admission_state(
    admission: AdmittedWorkspaceSemanticMaterializationGraphNodeExecution,
) -> _GraphNodeAdmissionState:
    if (
        type(admission)
        is not AdmittedWorkspaceSemanticMaterializationGraphNodeExecution
    ):
        raise TypeError("graph-node execution admission must be exact")
    with _GRAPH_NODE_ADMISSIONS_LOCK:
        state = _GRAPH_NODE_ADMISSIONS.get(admission)
    if state is None or not state.live:
        raise WorkspaceMaterializeOperationError(
            "graph-node execution admission is absent or revoked"
        )
    return state


def _validate_graph_node_owner_source(
    node_admission: AdmittedWorkspaceSemanticMaterializationGraphNodeExecution,
    *,
    source_runtime: (
        WorkspaceOwnerDefinedSourceAdmissionRuntime
        | WorkspaceV3OwnerDefinedSourceAdmissionRuntime
    ),
    source_admission: WorkspaceOwnerDefinedSourceAdmission,
) -> None:
    """Revalidate source-to-node correspondence without issuing owner authority.

    The installed host must retain and supply both original handles. Matching
    two independently supplied handles is not an operation/attempt admission.
    """

    state = _graph_node_admission_state(node_admission)
    if type(source_runtime) not in (
        WorkspaceOwnerDefinedSourceAdmissionRuntime,
        WorkspaceV3OwnerDefinedSourceAdmissionRuntime,
    ):
        raise TypeError("exact Workspace source runtime required")
    if type(source_admission) is not WorkspaceOwnerDefinedSourceAdmission:
        raise TypeError("exact Workspace source admission required")
    operation_admission = state.operation_admission
    operation_admission._assert_intact()
    request = operation_admission.request
    state.operation._assert_composition_current(request)
    inspection = source_runtime.inspect(source_admission)
    if type(inspection) is not WorkspaceOwnerDefinedSourceInspection:
        raise TypeError("exact Workspace source inspection required")
    binding = state.node_binding
    entry = binding.package_entry
    authority = inspection.authority_result_coordinate
    if (
        inspection.repository_ref != entry.repository_ref
        or inspection.workspace_ref != entry.workspace_ref
        or inspection.module_ref != entry.module_ref
        or inspection.package != binding.package
        or inspection.package_kind != binding.package.package_kind
        or inspection.manifest_contract != entry.manifest_contract
        or inspection.manifest_relative_path != entry.manifest_relative_path
        or inspection.profile_ref
        != binding.code_match.selected_binding.profile_declaration.profile_ref
        or authority.role != "package_authority"
        or authority.value_ref != entry.source_authority_ref
        or authority.digest != entry.source_authority_digest
        or request.source_authority_ref != authority.value_ref
        or request.source_authority_digest != authority.digest.value
        or _source_identity(
            {
                "package": inspection.package,
                "manifest_contract": inspection.manifest_contract,
                "manifest_relative_path": inspection.manifest_relative_path,
                "source_authority_ref": authority.value_ref,
                "source_authority_digest": authority.digest,
            }
        )
        != entry.source_identity_digest
    ):
        raise WorkspaceMaterializeOperationError(
            "original owner source differs from graph node"
        )
    _graph_node_admission_state(node_admission)


def _revoke_workspace_semantic_materialization_graph_node_execution(
    admission: AdmittedWorkspaceSemanticMaterializationGraphNodeExecution,
) -> None:
    state = _graph_node_admission_state(admission)
    with _GRAPH_NODE_ADMISSIONS_LOCK:
        state.live = False


class _ChildPublicationAuthority:
    def __init__(self, request: WorkspaceSemanticMaterializationRequest) -> None:
        self.operation_ref = request.operation_ref
        self.operation_digest = request.operation_digest
        self._request_digest = request.request_digest

    def admits(self, request: WorkspaceSemanticMaterializationRequest) -> bool:
        return request.request_digest == self._request_digest


class _ChildSessionAuthority:
    def __init__(
        self,
        request: WorkspaceMaterializationSessionAppendRequest,
        state: _AdmissionState,
    ) -> None:
        self.operation_ref = request.operation_ref
        self.operation_digest = request.operation_digest
        self.authority_grade = state.authority_grade
        self._request_digest = request.request_digest
        self._permitted = state.permitted_package_refs

    def admits(self, request: WorkspaceMaterializationSessionAppendRequest) -> bool:
        return request.request_digest == self._request_digest

    def permitted_package_refs_for(
        self, request: WorkspaceMaterializationSessionAppendRequest
    ) -> tuple[str, ...]:
        if request.request_digest != self._request_digest:
            return ()
        return self._permitted


class WorkspaceMaterializeOperation:
    """Execute, publish and fan out one admitted neutral materialization."""

    def __init__(
        self,
        *,
        runtime: SemanticContractRuntime,
        plan_resolver: WorkspaceMaterializeExecutionPlanResolver,
        publisher: WorkspaceSemanticMaterializationPublisher,
        session_journal: WorkspaceMaterializationSessionJournal,
        graph_product_registration: AdmittedSemanticProviderRegistration | None = None,
        graph_node_use: Callable[
            [AdmittedWorkspaceSemanticMaterializationGraphNodeExecution],
            AbstractContextManager[WorkspaceMaterializeGraphNodeUse],
        ] | None = None,
    ) -> None:
        if type(runtime) is not SemanticContractRuntime:
            raise TypeError("operation runtime must be exact SemanticContractRuntime")
        if type(publisher) is not WorkspaceSemanticMaterializationPublisher:
            raise TypeError("operation publisher must be exact Workspace publisher")
        if type(session_journal) is not WorkspaceMaterializationSessionJournal:
            raise TypeError("operation session journal must be exact Workspace journal")
        if (graph_product_registration is None) != (graph_node_use is None):
            raise TypeError("graph product registration and node use must be paired")
        if (
            graph_product_registration is not None
            and type(graph_product_registration) is not AdmittedSemanticProviderRegistration
        ):
            raise TypeError("exact selected graph product registration required")
        if graph_node_use is not None and not callable(graph_node_use):
            raise TypeError("graph node use entrance must be callable")
        self._runtime = runtime
        self._graph_product_registration = graph_product_registration
        self._graph_node_use = graph_node_use
        self._plan_resolver = plan_resolver
        self._publisher = publisher
        self._session_journal = session_journal
        self._resolver_ref = _token(
            plan_resolver.implementation_ref, "plan_resolver_ref"
        )
        self._resolver_digest = _digest(
            plan_resolver.implementation_digest, "plan_resolver_digest"
        )
        self._profile_ref = _token(plan_resolver.profile_ref, "profile_ref")
        self._profile_digest = _digest(plan_resolver.profile_digest, "profile_digest")
        if (
            runtime.profile.profile_ref != self._profile_ref
            or runtime.profile.digest.value != self._profile_digest
        ):
            raise WorkspaceMaterializeOperationError(
                "resolver profile differs from Code runtime"
            )

    async def execute(
        self, admission: WorkspaceMaterializeOperationAdmission
    ) -> WorkspaceMaterializeOperationResult:
        started = time.perf_counter_ns()
        plan_started = time.perf_counter_ns()
        try:
            state = _admission_state(admission)
            admission._assert_intact()
            request = state.request
            self._assert_composition_current(request)
            plan = await self._plan_resolver.resolve(admission)
            if type(plan) is not WorkspaceMaterializeExecutionPlan:
                raise TypeError("resolver returned a foreign execution plan")
            plan.__post_init__()
            self._validate_plan(request, plan)
            resolved_execution_input_closure_digest = (
                derive_workspace_materialize_execution_input_closure_digest(
                    plan.input_bodies
                )
            )
            admitted_execution_input = _execution_input_admission_state(
                state.execution_input_admission
            )
            if (
                resolved_execution_input_closure_digest
                != admitted_execution_input.execution_input_closure_digest
                or resolved_execution_input_closure_digest
                != request.execution_input_closure_digest
            ):
                raise WorkspaceMaterializeOperationError(
                    "resolved execution input closure differs from admission"
                )
        except Exception as error:
            plan_ns = time.perf_counter_ns() - plan_started
            raise WorkspaceMaterializeOperationStageError(
                "plan",
                error,
                stage_timings_ns=(("plan", plan_ns),),
                total_ns=time.perf_counter_ns() - started,
            ) from error
        plan_ns = time.perf_counter_ns() - plan_started

        execution_started = time.perf_counter_ns()
        try:
            completion = await self._runtime.execute(
                plan.invocation,
                plan.input_bodies,
                predecessor_body=plan.predecessor_body,
            )
        except Exception as error:
            execution_ns = time.perf_counter_ns() - execution_started
            raise WorkspaceMaterializeOperationStageError(
                "execution",
                error,
                stage_timings_ns=(
                    ("plan", plan_ns),
                    ("execution", execution_ns),
                ),
                total_ns=time.perf_counter_ns() - started,
            ) from error
        execution_ns = time.perf_counter_ns() - execution_started

        publication_started = time.perf_counter_ns()
        try:
            publication_request = WorkspaceSemanticMaterializationRequest.create(
                package_ref=request.package_ref,
                package_kind=request.package_kind,
                manifest_digest=request.manifest_digest,
                source_authority_ref=request.source_authority_ref,
                source_authority_digest=request.source_authority_digest,
                operation_ref=request.operation_ref,
                operation_digest=request.operation_digest,
                profile_ref=request.profile_ref,
                profile_digest=request.profile_digest,
                invocation_digest=plan.invocation.digest.value,
            )
            publication_admission = admit_workspace_semantic_materialization(
                request=publication_request,
                operation_authority=_ChildPublicationAuthority(publication_request),
            )
            publication = self._publisher.publish(
                admission=publication_admission,
                invocation=plan.invocation,
                completion=completion,
                expected_head_revision=(request.expected_materialization_head_revision),
            )
        except Exception as error:
            publication_ns = time.perf_counter_ns() - publication_started
            raise WorkspaceMaterializeOperationStageError(
                "publication",
                error,
                stage_timings_ns=(
                    ("plan", plan_ns),
                    ("execution", execution_ns),
                    ("publication", publication_ns),
                ),
                total_ns=time.perf_counter_ns() - started,
            ) from error
        publication_ns = time.perf_counter_ns() - publication_started

        fanout_started = time.perf_counter_ns()
        try:
            session_request = WorkspaceMaterializationSessionAppendRequest.create(
                workspace_session_ref=request.workspace_session_ref,
                epoch=request.epoch,
                participant_ref=request.participant_ref,
                actor_ref=request.actor_ref,
                workflow_session_ref=request.workflow_session_ref,
                materialization_attempt_ref=request.materialization_attempt_ref,
                branch_baseline_ref=request.branch_baseline_ref,
                branch_baseline_digest=request.branch_baseline_digest,
                branch_baseline_grade=request.branch_baseline_grade,
                package_ref=request.package_ref,
                profile_digest=request.profile_digest,
                source_authority_ref=request.source_authority_ref,
                source_authority_digest=request.source_authority_digest,
                publication_receipt_digest=publication.receipt.receipt_digest,
                expected_session_head_revision=request.expected_session_head_revision,
                expected_cursor=request.expected_session_cursor,
                expected_predecessor_event_digest=(
                    request.expected_predecessor_event_digest
                ),
                operation_ref=request.operation_ref,
                operation_digest=request.operation_digest,
            )
            session_admission = admit_workspace_materialization_session_append(
                request=session_request,
                operation_authority=_ChildSessionAuthority(session_request, state),
            )
            fanout = self._session_journal.append(
                admission=session_admission,
                publication=publication.receipt,
            )
        except Exception as error:
            fanout_ns = time.perf_counter_ns() - fanout_started
            raise WorkspaceMaterializeOperationStageError(
                "fanout",
                error,
                stage_timings_ns=(
                    ("plan", plan_ns),
                    ("execution", execution_ns),
                    ("publication", publication_ns),
                    ("fanout", fanout_ns),
                ),
                total_ns=time.perf_counter_ns() - started,
            ) from error
        fanout_ns = time.perf_counter_ns() - fanout_started
        return WorkspaceMaterializeOperationResult(
            request_digest=request.request_digest,
            plan_digest=plan.plan_digest,
            result_digest=publication.receipt.head.result_digest,
            publication=publication,
            fanout=fanout,
            metrics=WorkspaceMaterializeOperationMetrics(
                plan_ns=plan_ns,
                execution_ns=execution_ns,
                publication_ns=publication_ns,
                fanout_ns=fanout_ns,
                total_ns=time.perf_counter_ns() - started,
            ),
        )

    async def _execute_graph_v2(
        self,
        admission: AdmittedWorkspaceSemanticMaterializationGraphNodeExecution,
    ) -> _WorkspaceMaterializeGraphOperationResultV2:
        """Execute the existing operation behind one exact graph-node authority.

        This entrance is deliberately private and is not used by the mounted V1
        operation. 07F-D may expose it only through a managed host admission.
        """

        graph_state = _graph_node_admission_state(admission)
        if graph_state.operation is not self:
            raise WorkspaceMaterializeOperationError(
                "graph-node admission belongs to another operation"
            )
        operation_admission = graph_state.operation_admission
        state = _admission_state(operation_admission)
        operation_admission._assert_intact()
        request = state.request
        self._assert_composition_current(request)
        binding = graph_state.node_binding
        if len(binding.required_result_products) != 1:
            raise WorkspaceMaterializeOperationError(
                "graph-node execution requires exactly one result product"
            )
        registration = self._graph_product_registration
        node_use = self._graph_node_use
        if registration is None or node_use is None:
            raise WorkspaceMaterializeOperationError(
                "tracked graph-product execution unavailable"
            )
        with node_use(admission) as use:
            # Input production may await semantic owners. Keep the original
            # command/source node use alive across that await, not only across
            # the selected Code call that consumes the resulting bodies.
            resolve_graph_node = getattr(
                self._plan_resolver, "resolve_graph_node", None
            )
            if not callable(resolve_graph_node):
                raise WorkspaceMaterializeOperationError(
                    "graph-node-bound input resolver unavailable"
                )
            graph_resolve = cast(
                Callable[..., Awaitable[WorkspaceMaterializeExecutionPlan]],
                resolve_graph_node,
            )
            plan = await graph_resolve(operation_admission, node_use=use)
            if type(plan) is not WorkspaceMaterializeExecutionPlan:
                raise TypeError("resolver returned a foreign execution plan")
            plan.__post_init__()
            self._validate_plan(request, plan)
            closure = derive_workspace_materialize_execution_input_closure_digest(
                plan.input_bodies
            )
            if (
                closure != request.execution_input_closure_digest
                or closure != graph_state.execution_input_closure_digest.value
            ):
                raise WorkspaceMaterializeOperationError(
                    "graph-node resolved closure differs from admission"
                )
            use.bind_execution_plan(plan)
            semantic_input = SelectedProviderInvocationClosure(
                plan.invocation, plan.input_bodies, plan.predecessor_body
            )
            execution = issue_selected_provider_execution(
                self._runtime,
                registration,
                semantic_input,
                operation_context=use,
            )
            completion = execute_selected_provider(self._runtime, execution)
            if type(completion) is not ExecutionCompletion:
                raise WorkspaceMaterializeOperationError(
                    "selected graph product lacks runtime-owned completion"
                )
            use.validate()
            snapshot = self._runtime.snapshot_completion(completion)
            result_coordinate = _select_graph_result_coordinate(
                required_products=binding.required_result_products,
                snapshot=snapshot,
            )
            publication_request = WorkspaceSemanticMaterializationRequestV3.create(
                package=binding.package,
                result_coordinate=result_coordinate,
                source_identity_digest=binding.package_entry.source_identity_digest,
                code_intent_digest=binding.code_intent.intent_digest,
                code_match_digest=binding.code_match.match_digest,
                planning_input_digest=binding.planning_input_digest,
                execution_input_closure_digest=graph_state.execution_input_closure_digest,
                operation_result_digest=snapshot.result_digest,
                expected_head_revision=request.expected_materialization_head_revision,
            )
            publication_receipt, package_head = self._publisher._publish_graph_v2(
                request=publication_request,
                snapshot=snapshot,
                invocation=plan.invocation,
            )
            try:
                use.validate()
            except BaseException as error:
                raise WorkspaceMaterializeOperationError(
                    "graph_source_reconciliation_required"
                ) from error
            source = WorkspaceMaterializationSessionSourceEvidenceV3.create(
                disposition="executed",
                head_reread_evidence=package_head,
                publication_receipt=publication_receipt,
            )
            append_request = WorkspaceMaterializationSessionAppendRequestV3.create(
                workspace_session_ref=request.workspace_session_ref,
                epoch=request.epoch,
                participant_ref=request.participant_ref,
                actor_ref=request.actor_ref,
                workflow_session_ref=request.workflow_session_ref,
                materialization_attempt_ref=request.materialization_attempt_ref,
                branch_baseline_ref=request.branch_baseline_ref,
                branch_baseline_digest=ContentDigest(request.branch_baseline_digest),
                branch_baseline_grade=request.branch_baseline_grade,
                package_ref=request.package_ref,
                operation_ref=request.operation_ref,
                operation_digest=ContentDigest(request.operation_digest),
                source_evidence=source,
                expected_session_head_revision=request.expected_session_head_revision,
                expected_cursor=request.expected_session_cursor,
                expected_predecessor_event_digest=(
                    None
                    if request.expected_predecessor_event_digest is None
                    else ContentDigest(request.expected_predecessor_event_digest)
                ),
            )
            graph_state.session_append_fence_rereader()
            append_result = self._session_journal._append_graph_v2(
                request=append_request
            )
            try:
                use.validate()
            except BaseException as error:
                raise WorkspaceMaterializeOperationError(
                    "graph_source_reconciliation_required"
                ) from error
            return _WorkspaceMaterializeGraphOperationResultV2(
                operation_result_digest=snapshot.result_digest,
                publication_receipt=publication_receipt,
                package_head_reread_evidence=package_head,
                session_source_evidence=source,
                session_append_result=append_result,
            )

    def _assert_composition_current(
        self, request: WorkspaceMaterializeOperationRequest
    ) -> None:
        if (
            _token(self._plan_resolver.implementation_ref, "plan_resolver_ref")
            != self._resolver_ref
            or _digest(
                self._plan_resolver.implementation_digest,
                "plan_resolver_digest",
            )
            != self._resolver_digest
            or _token(self._plan_resolver.profile_ref, "profile_ref")
            != self._profile_ref
            or _digest(self._plan_resolver.profile_digest, "profile_digest")
            != self._profile_digest
            or request.plan_resolver_ref != self._resolver_ref
            or request.plan_resolver_digest != self._resolver_digest
            or request.profile_ref != self._profile_ref
            or request.profile_digest != self._profile_digest
        ):
            raise WorkspaceMaterializeOperationError(
                "materialize operation composition was substituted"
            )

    @staticmethod
    def _validate_plan(
        request: WorkspaceMaterializeOperationRequest,
        plan: WorkspaceMaterializeExecutionPlan,
    ) -> None:
        if (
            plan.source_authority_ref != request.source_authority_ref
            or plan.source_authority_digest != request.source_authority_digest
            or plan.operation_ref != request.operation_ref
            or plan.operation_digest != request.operation_digest
            or plan.package_ref != request.package_ref
            or plan.package_kind != request.package_kind
            or plan.manifest_digest != request.manifest_digest
            or plan.profile_ref != request.profile_ref
            or plan.profile_digest != request.profile_digest
        ):
            raise WorkspaceMaterializeOperationError(
                "execution plan differs from admitted operation"
            )


def _select_graph_result_coordinate(
    *,
    required_products: tuple[CodeSemanticRequiredResultProduct, ...],
    snapshot: ExecutionPublicationSnapshot,
) -> SemanticValueCoordinate:
    """Select the sole exact graph-demanded product from Code-owned evidence."""

    if type(required_products) is not tuple:
        raise TypeError("graph required products must be an exact tuple")
    for product in required_products:
        if type(product) is not CodeSemanticRequiredResultProduct:
            raise TypeError("graph required product must be exact")
        product.__post_init__()
    if len(required_products) != 1:
        raise WorkspaceMaterializeOperationError(
            "graph-node operation requires one exact result product"
        )
    if type(snapshot) is not ExecutionPublicationSnapshot:
        raise TypeError("graph publication snapshot must be exact")
    snapshot.__post_init__()
    result = snapshot.result
    required_product = required_products[0]
    produced_coordinates = tuple(
        coordinate
        for coordinate in (
            result.current_result,
            None if result.transition is None else result.transition.result,
            None if result.effect is None else result.effect.effect_body,
            *(output.output for output in result.outputs),
        )
        if coordinate is not None
    )
    matching_coordinates = tuple(
        coordinate
        for coordinate in produced_coordinates
        if coordinate.role == required_product.role
        and coordinate.contract == required_product.contract
    )
    if len(matching_coordinates) != 1:
        raise WorkspaceMaterializeOperationError(
            "graph-node operation did not produce one exact required product"
        )
    selected = matching_coordinates[0]
    snapshot.body_for(selected)
    return selected


def _plan_payload(values: dict[str, object]) -> dict[str, object]:
    invocation = cast(SemanticContractInvocation, values["invocation"])
    bodies = cast(tuple[SemanticBody, ...], values["input_bodies"])
    predecessor = cast(SemanticBody | None, values["predecessor_body"])
    return {
        "source_authority_ref": values["source_authority_ref"],
        "source_authority_digest": values["source_authority_digest"],
        "operation_ref": values["operation_ref"],
        "operation_digest": values["operation_digest"],
        "package_ref": values["package_ref"],
        "package_kind": values["package_kind"],
        "manifest_digest": values["manifest_digest"],
        "profile_ref": values["profile_ref"],
        "profile_digest": values["profile_digest"],
        "invocation": invocation.to_wire(),
        "input_bodies": [item.coordinate.to_wire() for item in bodies],
        "predecessor_body": (
            None if predecessor is None else predecessor.coordinate.to_wire()
        ),
    }


def _decode_object(value: bytes, fields: set[str]) -> dict[str, object]:
    if type(value) is not bytes:
        raise TypeError("operation wire must be exact bytes")
    try:
        payload = json.loads(value)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WorkspaceMaterializeOperationError(
            "operation wire is invalid JSON"
        ) from error
    if (
        type(payload) is not dict
        or set(payload) != fields
        or any(type(key) is not str for key in payload)
    ):
        raise WorkspaceMaterializeOperationError("operation wire fields differ")
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
        raise WorkspaceMaterializeOperationError(f"{field} must be a nonempty token")
    return value


def _digest(value: object, field: str) -> str:
    item = _token(value, field)
    if len(item) != 71 or not item.startswith(_DIGEST_PREFIX) or item != item.lower():
        raise WorkspaceMaterializeOperationError(f"{field} must be lowercase SHA-256")
    try:
        int(item[7:], 16)
    except ValueError as error:
        raise WorkspaceMaterializeOperationError(
            f"{field} must be lowercase SHA-256"
        ) from error
    return item


def _nonnegative(value: object, field: str) -> int:
    if type(value) is not int or value < 0:
        raise WorkspaceMaterializeOperationError(
            f"{field} must be a nonnegative integer"
        )
    return value


def _string(value: object) -> str:
    if type(value) is not str:
        raise WorkspaceMaterializeOperationError("operation wire string type differs")
    return value


def _integer(value: object) -> int:
    if type(value) is not int:
        raise WorkspaceMaterializeOperationError("operation wire integer type differs")
    return value


def _optional_string(value: object) -> str | None:
    return None if value is None else _string(value)


def _list(value: object) -> list[object]:
    if type(value) is not list:
        raise WorkspaceMaterializeOperationError("operation wire list type differs")
    return cast(list[object], value)


__all__ = [
    "WORKSPACE_MATERIALIZE_EXECUTION_INPUT_CLOSURE",
    "WORKSPACE_MATERIALIZE_EXECUTION_PLAN",
    "WORKSPACE_MATERIALIZE_OPERATION_NON_CLAIMS",
    "WORKSPACE_MATERIALIZE_OPERATION_REQUEST",
    "WORKSPACE_MATERIALIZE_OPERATION_STAGE_ORDER",
    "AdmittedWorkspaceSemanticMaterializationGraphNodeExecution",
    "WorkspaceMaterializeExecutionInputCompositionAdmission",
    "WorkspaceMaterializeExecutionInputCompositionAuthority",
    "WorkspaceMaterializeExecutionPlan",
    "WorkspaceMaterializeExecutionPlanResolver",
    "WorkspaceMaterializeOperation",
    "WorkspaceMaterializeOperationAdmission",
    "WorkspaceMaterializeOperationAuthority",
    "WorkspaceMaterializeOperationError",
    "WorkspaceMaterializeOperationMetrics",
    "WorkspaceMaterializeOperationRequest",
    "WorkspaceMaterializeOperationResult",
    "WorkspaceMaterializeOperationStageError",
    "admit_workspace_materialize_execution_input_composition",
    "admit_workspace_materialize_operation",
    "derive_workspace_materialize_execution_input_closure_digest",
]
