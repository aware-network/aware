"""Provider-neutral contracts for canonical Issue SDK operations."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import StrEnum
from types import UnionType
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Protocol,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    override,
)

from aware_issue_runtime import ISSUE_PROJECTION_SCHEMA_VERSION, IssueReadProjection

if TYPE_CHECKING:
    from .repository_publication import (
        IssueRepositoryOperationResult,
        IssueRepositoryPublicationClient,
    )
    from .specification_iteration import (
        IssueSpecificationIterationBindingObservation,
        IssueSpecificationIterationBindingObserveRequest,
    )

ISSUE_RESOLVE_READ_PROJECTION_OPERATION_REF = "issue_sdk.resolve_issue_read_projection"
ISSUE_RESOLVE_READ_PROJECTION_PROVIDER_OPERATION_REF = (
    "workflow.issue.read_projection.resolve"
)
ISSUE_READ_PROJECTION_RESOLVE_REQUEST_CONTRACT = (
    "aware.issue.read-projection-resolve-request.v1"
)
ISSUE_READ_PROJECTION_RESOLVE_RESULT_CONTRACT = (
    "aware.issue.read-projection-resolve-result.v1"
)
ISSUE_MUTATION_RESULT_CONTRACT = "aware.issue.mutation-result.v1"

ISSUE_ENSURE_SNAPSHOT_OPERATION_REF = "issue_sdk.ensure_issue_snapshot"
ISSUE_START_PROGRESS_OPERATION_REF = "issue_sdk.start_issue_progress"
ISSUE_BLOCK_OPERATION_REF = "issue_sdk.block_issue"
ISSUE_RESUME_OPERATION_REF = "issue_sdk.resume_issue"
ISSUE_SET_OWNER_OPERATION_REF = "issue_sdk.set_issue_owner"
ISSUE_BIND_SCOPE_OPERATION_REF = "issue_sdk.bind_issue_scope_paths"
ISSUE_APPEND_UPDATE_OPERATION_REF = "issue_sdk.append_issue_update"
ISSUE_APPEND_EVIDENCE_OPERATION_REF = "issue_sdk.append_issue_evidence"
ISSUE_CLOSE_OPERATION_REF = "issue_sdk.close_issue"
ISSUE_COMMIT_WORKSPACE_OPERATION_REF = "issue_sdk.commit_workspace"

ISSUE_ENSURE_SNAPSHOT_PROVIDER_OPERATION_REF = "workflow.issue.snapshot.ensure"
ISSUE_START_PROGRESS_PROVIDER_OPERATION_REF = "workflow.issue.lifecycle.start"
ISSUE_BLOCK_PROVIDER_OPERATION_REF = "workflow.issue.lifecycle.block"
ISSUE_RESUME_PROVIDER_OPERATION_REF = "workflow.issue.lifecycle.resume"
ISSUE_SET_OWNER_PROVIDER_OPERATION_REF = "workflow.issue.owner.set"
ISSUE_BIND_SCOPE_PROVIDER_OPERATION_REF = "workflow.issue.scope.bind"
ISSUE_APPEND_UPDATE_PROVIDER_OPERATION_REF = "workflow.issue.update.append"
ISSUE_APPEND_EVIDENCE_PROVIDER_OPERATION_REF = "workflow.issue.evidence.append"
ISSUE_CLOSE_PROVIDER_OPERATION_REF = "workflow.issue.lifecycle.close"
ISSUE_COMMIT_WORKSPACE_PROVIDER_OPERATION_REF = "workflow.issue.workspace.commit"
ISSUE_COMMIT_WORKSPACE_RESULT_CONTRACT = "aware.issue.workspace-commit-result.v1"


class IssueOperationContractError(ValueError):
    """Raised when a canonical Issue operation value is malformed."""


@dataclass(frozen=True, slots=True)
class IssueProviderReport:
    """Detached bounded data, explicitly not an admitted provider result."""

    payload_json: str | None
    capture_diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.payload_json is not None:
            if type(self.payload_json) is not str or len(self.payload_json) > 65536:
                raise IssueOperationContractError("provider_report_invalid")
            if type(json.loads(self.payload_json)) is not dict:
                raise IssueOperationContractError("provider_report_invalid")
        if type(self.capture_diagnostics) is not tuple or any(
            type(value) is not str for value in self.capture_diagnostics
        ):
            raise IssueOperationContractError("capture_diagnostics_invalid")

    def to_wire(self) -> dict[str, object] | None:
        return None if self.payload_json is None else json.loads(self.payload_json)


@dataclass(frozen=True, slots=True)
class IssueOperationFailure:
    """Failure value; distinct from both its exception and effect authority."""

    code: str
    phase: str
    operation_ref: str
    issue_ref: str | None
    provider_invoked: bool
    effect: str
    provider_result: IssueProviderReport
    contract: ClassVar[str] = "aware.issue.operation-failure.v1"

    def __post_init__(self) -> None:
        for value in (self.code, self.operation_ref):
            if type(value) is not str or not value or value.strip() != value:
                raise IssueOperationContractError("operation_failure_invalid")
        if self.issue_ref is not None and type(self.issue_ref) is not str:
            raise IssueOperationContractError("operation_failure_invalid")
        if (
            type(self.provider_invoked) is not bool
            or type(self.phase) is not str
            or type(self.effect) is not str
            or self.phase not in {"request", "provider", "result"}
        ):
            raise IssueOperationContractError("operation_failure_invalid")
        if self.provider_invoked != (self.phase != "request") or self.effect != (
            "unknown" if self.provider_invoked else "none"
        ):
            raise IssueOperationContractError("operation_failure_invalid")
        if type(self.provider_result) is not IssueProviderReport:
            raise IssueOperationContractError("operation_failure_invalid")
        self.provider_result.__post_init__()

    def to_wire(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "code": self.code,
            "phase": self.phase,
            "operation_ref": self.operation_ref,
            "issue_ref": self.issue_ref,
            "provider_invoked": self.provider_invoked,
            "effect": self.effect,
            "provider_result": self.provider_result.to_wire(),
            "provider_report_grade": "unvalidated_provider_report",
            "capture_diagnostics": list(self.provider_result.capture_diagnostics),
        }


@dataclass(frozen=True, slots=True)
class IssueReadProjectionResolveError(IssueOperationFailure):
    contract: ClassVar[str] = "aware.issue.read-projection-resolve-error.v1"


@dataclass(frozen=True, slots=True)
class IssueMutationError(IssueOperationFailure):
    contract: ClassVar[str] = "aware.issue.mutation-error.v1"


@dataclass(frozen=True, slots=True)
class IssueCommitWorkspaceError(IssueOperationFailure):
    contract: ClassVar[str] = "aware.issue.workspace-commit-error.v1"


class IssueProviderResultError(IssueOperationContractError):
    """Compatibility ValueError carrier; original value never auto-serialized."""

    def __init__(self, failure: IssueOperationFailure, *, provider_result: object):
        if type(failure) not in {
            IssueReadProjectionResolveError,
            IssueMutationError,
            IssueCommitWorkspaceError,
        }:
            raise IssueOperationContractError("operation_failure_value_required")
        failure.__post_init__()
        self.failure: IssueOperationFailure = failure
        self.provider_result: object = provider_result
        self.effect: str = failure.effect
        super().__init__(failure.code)

    def to_wire(self) -> dict[str, object]:
        return self.failure.to_wire()


class IssueReadProjectionResolveOutcome(StrEnum):
    FOUND = "found"
    ABSENT = "absent"
    MALFORMED = "malformed"
    UNSUPPORTED_PROFILE = "unsupported_profile"
    AUTHORITY_UNAVAILABLE = "authority_unavailable"


class IssueMutationOutcome(StrEnum):
    APPLIED = "applied"
    IDEMPOTENT = "idempotent"
    ABSENT = "absent"
    STALE = "stale"
    CONFLICT = "conflict"
    INVALID = "invalid"
    UNAUTHORIZED = "unauthorized"
    BLOCKED = "blocked"
    MALFORMED = "malformed"
    UNSUPPORTED_PROFILE = "unsupported_profile"
    AUTHORITY_UNAVAILABLE = "authority_unavailable"


class IssuePublicationOutcome(StrEnum):
    PLANNED = "planned"
    APPLIED = "applied"
    STALE = "stale"
    UNAUTHORIZED = "unauthorized"
    OUT_OF_SCOPE = "out_of_scope"
    CONFLICT = "conflict"
    INVALID = "invalid"
    AUTHORITY_UNAVAILABLE = "authority_unavailable"


def _text(value: object, field_name: str) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise IssueOperationContractError(
            f"{field_name} must be non-empty trimmed text"
        )
    return value


def _text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise IssueOperationContractError(f"{field_name} must be an iterable of text")
    result = tuple(value)
    if any(type(item) is not str or not item for item in result):
        raise IssueOperationContractError(f"{field_name} must contain non-empty text")
    return cast(tuple[str, ...], result)


def _optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _text(value, field_name)


def _authored_items(value: object, field_name: str) -> tuple[str, ...]:
    """Freeze plain single-line authored items, not Markdown authority sections."""
    result = _text_tuple(value, field_name)
    for item in result:
        _text(item, field_name)
        if len(item.splitlines()) != 1 or any(
            ord(character) < 32 or ord(character) == 127 for character in item
        ):
            raise IssueOperationContractError(
                f"{field_name} must contain single-line text"
            )
    return result


def _sha256(value: object, field_name: str) -> str:
    result = _text(value, field_name)
    if len(result) != 71 or not result.startswith("sha256:"):
        raise IssueOperationContractError(f"{field_name} must be a sha256 digest")
    try:
        bytes.fromhex(result.removeprefix("sha256:"))
    except ValueError as error:
        raise IssueOperationContractError(
            f"{field_name} must be a sha256 digest"
        ) from error
    return result


def _git_hash(value: object) -> str:
    result = _text(value, "commit_hash")
    if len(result) not in {40, 64}:
        raise IssueOperationContractError("commit_hash must be a Git object id")
    try:
        bytes.fromhex(result)
    except ValueError as error:
        raise IssueOperationContractError(
            "commit_hash must be a Git object id"
        ) from error
    return result


@dataclass(frozen=True, slots=True)
class IssueReadProjectionResolveRequest:
    issue_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "issue_ref", _text(self.issue_ref, "issue_ref"))

    def to_wire(self) -> dict[str, object]:
        return {
            "contract": ISSUE_READ_PROJECTION_RESOLVE_REQUEST_CONTRACT,
            "issue_ref": self.issue_ref,
        }


@dataclass(frozen=True, slots=True)
class IssueReadProjectionResolveResult:
    outcome: IssueReadProjectionResolveOutcome
    issue_ref: str
    provider_ref: str
    provider_distribution: str
    provider_version: str
    projection: IssueReadProjection | None = None
    evidence: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()
    operation_ref: str = ISSUE_RESOLVE_READ_PROJECTION_OPERATION_REF
    projection_ref: str = ISSUE_PROJECTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if type(self.outcome) is not IssueReadProjectionResolveOutcome:
            raise IssueOperationContractError(
                "outcome must be IssueReadProjectionResolveOutcome"
            )
        if self.operation_ref != ISSUE_RESOLVE_READ_PROJECTION_OPERATION_REF:
            raise IssueOperationContractError(
                "operation_ref must identify issue_sdk.resolve_issue_read_projection"
            )
        if self.projection_ref != ISSUE_PROJECTION_SCHEMA_VERSION:
            raise IssueOperationContractError(
                "projection_ref must identify the established Issue read projection"
            )
        for field_name in (
            "issue_ref",
            "provider_ref",
            "provider_distribution",
            "provider_version",
        ):
            object.__setattr__(
                self, field_name, _text(getattr(self, field_name), field_name)
            )
        object.__setattr__(self, "evidence", _text_tuple(self.evidence, "evidence"))
        object.__setattr__(
            self, "diagnostics", _text_tuple(self.diagnostics, "diagnostics")
        )
        if self.outcome is IssueReadProjectionResolveOutcome.FOUND:
            if type(self.projection) is not IssueReadProjection:
                raise IssueOperationContractError(
                    "found outcome requires an Issue read projection"
                )
            if self.projection.issue_ref != self.issue_ref:
                raise IssueOperationContractError(
                    "found Issue projection identity must match issue_ref"
                )
        elif self.projection is not None:
            raise IssueOperationContractError(
                "non-found Issue result must not carry a projection"
            )

    def to_wire(self) -> dict[str, object]:
        return {
            "contract": ISSUE_READ_PROJECTION_RESOLVE_RESULT_CONTRACT,
            "operation_ref": self.operation_ref,
            "outcome": self.outcome.value,
            "issue_ref": self.issue_ref,
            "projection_ref": self.projection_ref,
            "projection": (
                self.projection.to_payload(include_raw_markdown=False)
                if self.projection is not None
                else None
            ),
            "provider_ref": self.provider_ref,
            "provider_distribution": self.provider_distribution,
            "provider_version": self.provider_version,
            "evidence": list(self.evidence),
            "diagnostics": list(self.diagnostics),
        }


@dataclass(frozen=True, slots=True)
class IssueMutationRequest:
    issue_ref: str
    expected_source_sha256: str
    client_intent_id: str
    actor_ref: str
    actor_evidence_ref: str
    operation_ref: ClassVar[str] = "issue_sdk.mutation"

    def __post_init__(self) -> None:
        for field_name in (
            "issue_ref",
            "client_intent_id",
            "actor_ref",
            "actor_evidence_ref",
        ):
            object.__setattr__(
                self, field_name, _text(getattr(self, field_name), field_name)
            )
        object.__setattr__(
            self,
            "expected_source_sha256",
            _sha256(self.expected_source_sha256, "expected_source_sha256"),
        )

    def _wire(self, **values: object) -> dict[str, object]:
        return {
            "operation_ref": self.operation_ref,
            "issue_ref": self.issue_ref,
            "expected_source_sha256": self.expected_source_sha256,
            "client_intent_id": self.client_intent_id,
            "actor_ref": self.actor_ref,
            "actor_evidence_ref": self.actor_evidence_ref,
            **values,
        }

    def to_wire(self) -> dict[str, object]:
        """Serialize request data only; this never admits an operation."""
        return self._wire()


@dataclass(frozen=True, slots=True)
class IssueEnsureSnapshotRequest:
    issue_ref: str
    title: str
    priority: str
    actor_ref: str
    actor_evidence_ref: str
    client_intent_id: str
    owner_ref: str | None = None
    goal_ref: str = "TBD"
    source_description: str = "issue_sdk.ensure_issue_snapshot"
    expected_source_sha256: str | None = None
    problem_items: tuple[str, ...] = ()
    objective_items: tuple[str, ...] = ()
    acceptance_items: tuple[str, ...] = ()
    operation_ref: ClassVar[str] = ISSUE_ENSURE_SNAPSHOT_OPERATION_REF

    def __post_init__(self) -> None:
        for field_name in (
            "issue_ref",
            "title",
            "priority",
            "actor_ref",
            "actor_evidence_ref",
            "client_intent_id",
            "goal_ref",
            "source_description",
        ):
            object.__setattr__(
                self, field_name, _text(getattr(self, field_name), field_name)
            )
        object.__setattr__(
            self, "owner_ref", _optional_text(self.owner_ref, "owner_ref")
        )
        if self.expected_source_sha256 is not None:
            object.__setattr__(
                self,
                "expected_source_sha256",
                _sha256(self.expected_source_sha256, "expected_source_sha256"),
            )
        for field_name in ("problem_items", "objective_items", "acceptance_items"):
            object.__setattr__(
                self, field_name, _authored_items(getattr(self, field_name), field_name)
            )

    def to_wire(self) -> dict[str, object]:
        return {
            "operation_ref": self.operation_ref,
            "issue_ref": self.issue_ref,
            "title": self.title,
            "priority": self.priority,
            "actor_ref": self.actor_ref,
            "actor_evidence_ref": self.actor_evidence_ref,
            "client_intent_id": self.client_intent_id,
            "owner_ref": self.owner_ref,
            "goal_ref": self.goal_ref,
            "source_description": self.source_description,
            "expected_source_sha256": self.expected_source_sha256,
            "problem_items": list(self.problem_items),
            "objective_items": list(self.objective_items),
            "acceptance_items": list(self.acceptance_items),
        }


@dataclass(frozen=True, slots=True)
class IssueStartProgressRequest(IssueMutationRequest):
    operation_ref: ClassVar[str] = ISSUE_START_PROGRESS_OPERATION_REF


@dataclass(frozen=True, slots=True)
class IssueBlockRequest(IssueMutationRequest):
    operation_ref: ClassVar[str] = ISSUE_BLOCK_OPERATION_REF


@dataclass(frozen=True, slots=True)
class IssueResumeRequest(IssueMutationRequest):
    operation_ref: ClassVar[str] = ISSUE_RESUME_OPERATION_REF


@dataclass(frozen=True, slots=True)
class IssueSetOwnerRequest(IssueMutationRequest):
    new_owner_ref: str = ""
    operation_ref: ClassVar[str] = ISSUE_SET_OWNER_OPERATION_REF

    def __post_init__(self) -> None:
        IssueMutationRequest.__post_init__(self)
        object.__setattr__(
            self,
            "new_owner_ref",
            _text(self.new_owner_ref, "new_owner_ref"),
        )

    @override
    def to_wire(self) -> dict[str, object]:
        return self._wire(new_owner_ref=self.new_owner_ref)


@dataclass(frozen=True, slots=True)
class IssueCloseRequest(IssueMutationRequest):
    resolution: str = ""
    verified_by: tuple[str, ...] = ()
    publication_receipt_ref: str = ""
    operation_ref: ClassVar[str] = ISSUE_CLOSE_OPERATION_REF

    def __post_init__(self) -> None:
        IssueMutationRequest.__post_init__(self)
        object.__setattr__(self, "resolution", _text(self.resolution, "resolution"))
        verified_by = _text_tuple(self.verified_by, "verified_by")
        if not verified_by:
            raise IssueOperationContractError("verified_by must not be empty")
        object.__setattr__(self, "verified_by", verified_by)
        object.__setattr__(
            self,
            "publication_receipt_ref",
            _text(self.publication_receipt_ref, "publication_receipt_ref"),
        )

    @override
    def to_wire(self) -> dict[str, object]:
        return self._wire(
            resolution=self.resolution,
            verified_by=list(self.verified_by),
            publication_receipt_ref=self.publication_receipt_ref,
        )


@dataclass(frozen=True, slots=True)
class IssueBindScopePathsRequest(IssueMutationRequest):
    scope_paths: tuple[str, ...] = ()
    operation_ref: ClassVar[str] = ISSUE_BIND_SCOPE_OPERATION_REF

    def __post_init__(self) -> None:
        IssueMutationRequest.__post_init__(self)
        scope_paths = _text_tuple(self.scope_paths, "scope_paths")
        if len(scope_paths) != len(set(scope_paths)):
            raise IssueOperationContractError("scope_paths must be unique")
        object.__setattr__(self, "scope_paths", tuple(sorted(scope_paths)))

    @override
    def to_wire(self) -> dict[str, object]:
        return self._wire(scope_paths=list(self.scope_paths))


@dataclass(frozen=True, slots=True)
class IssueAppendUpdateRequest(IssueMutationRequest):
    message: str = ""
    outcome: str = "info"
    operation_ref: ClassVar[str] = ISSUE_APPEND_UPDATE_OPERATION_REF

    def __post_init__(self) -> None:
        IssueMutationRequest.__post_init__(self)
        object.__setattr__(self, "message", _text(self.message, "message"))
        object.__setattr__(self, "outcome", _text(self.outcome, "outcome"))

    @override
    def to_wire(self) -> dict[str, object]:
        return self._wire(message=self.message, outcome=self.outcome)


@dataclass(frozen=True, slots=True)
class IssueAppendEvidenceRequest(IssueMutationRequest):
    path: str = ""
    description: str | None = None
    operation_ref: ClassVar[str] = ISSUE_APPEND_EVIDENCE_OPERATION_REF

    def __post_init__(self) -> None:
        IssueMutationRequest.__post_init__(self)
        object.__setattr__(self, "path", _text(self.path, "path"))
        object.__setattr__(
            self,
            "description",
            _optional_text(self.description, "description"),
        )

    @override
    def to_wire(self) -> dict[str, object]:
        return self._wire(path=self.path, description=self.description)


@dataclass(frozen=True, slots=True)
class IssueCommitWorkspaceRequest:
    issue_ref: str
    expected_issue_source_sha256: str
    target_paths: tuple[str, ...]
    message: str
    actor_ref: str
    actor_evidence_ref: str
    dry_run: bool
    operation_ref: ClassVar[str] = ISSUE_COMMIT_WORKSPACE_OPERATION_REF

    def __post_init__(self) -> None:
        for field_name in (
            "issue_ref",
            "message",
            "actor_ref",
            "actor_evidence_ref",
        ):
            object.__setattr__(
                self, field_name, _text(getattr(self, field_name), field_name)
            )
        object.__setattr__(
            self,
            "expected_issue_source_sha256",
            _sha256(
                self.expected_issue_source_sha256,
                "expected_issue_source_sha256",
            ),
        )
        target_paths = _text_tuple(self.target_paths, "target_paths")
        if not target_paths:
            raise IssueOperationContractError("target_paths must not be empty")
        if len(target_paths) != len(set(target_paths)):
            raise IssueOperationContractError("target_paths must be unique")
        object.__setattr__(self, "target_paths", tuple(sorted(target_paths)))
        if type(self.dry_run) is not bool:
            raise IssueOperationContractError("dry_run must be bool")

    def to_wire(self) -> dict[str, object]:
        return {
            "operation_ref": self.operation_ref,
            "issue_ref": self.issue_ref,
            "expected_issue_source_sha256": self.expected_issue_source_sha256,
            "target_paths": list(self.target_paths),
            "message": self.message,
            "actor_ref": self.actor_ref,
            "actor_evidence_ref": self.actor_evidence_ref,
            "dry_run": self.dry_run,
        }


@dataclass(frozen=True, slots=True)
class IssueMutationResult:
    operation_ref: str
    outcome: IssueMutationOutcome
    issue_ref: str
    provider_ref: str
    provider_distribution: str
    provider_version: str
    source_sha256_before: str | None = None
    source_sha256_after: str | None = None
    closeout_publication_receipt_ref: str | None = None
    projection: IssueReadProjection | None = None
    evidence: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()
    shared_index_projection: str | None = None
    shared_index_projection_error: str | None = None
    index_reconciliation_pending: bool | None = None

    def __post_init__(self) -> None:
        if type(self.outcome) is not IssueMutationOutcome:
            raise IssueOperationContractError("outcome must be IssueMutationOutcome")
        for field_name in (
            "operation_ref",
            "issue_ref",
            "provider_ref",
            "provider_distribution",
            "provider_version",
        ):
            object.__setattr__(
                self, field_name, _text(getattr(self, field_name), field_name)
            )
        for field_name in ("source_sha256_before", "source_sha256_after"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _sha256(value, field_name))
        if self.closeout_publication_receipt_ref is not None:
            if self.outcome is not IssueMutationOutcome.APPLIED:
                raise IssueOperationContractError(
                    "only an applied mutation may carry a closeout publication receipt"
                )
            object.__setattr__(
                self,
                "closeout_publication_receipt_ref",
                _text(
                    self.closeout_publication_receipt_ref,
                    "closeout_publication_receipt_ref",
                ),
            )
        if (
            any(
                value is not None
                for value in (
                    self.shared_index_projection,
                    self.shared_index_projection_error,
                    self.index_reconciliation_pending,
                )
            )
            and self.closeout_publication_receipt_ref is None
        ):
            raise IssueOperationContractError(
                "index result requires a closeout publication receipt"
            )
        if self.shared_index_projection is not None and (
            type(self.shared_index_projection) is not str
            or self.shared_index_projection not in {"not_run", "applied", "failed"}
        ):
            raise IssueOperationContractError("invalid shared_index_projection")
        if (
            self.index_reconciliation_pending is not None
            and type(self.index_reconciliation_pending) is not bool
        ):
            raise IssueOperationContractError(
                "index_reconciliation_pending must be bool or null"
            )
        if self.shared_index_projection_error is not None:
            object.__setattr__(
                self,
                "shared_index_projection_error",
                _text(
                    self.shared_index_projection_error, "shared_index_projection_error"
                ),
            )
        object.__setattr__(self, "evidence", _text_tuple(self.evidence, "evidence"))
        object.__setattr__(
            self, "diagnostics", _text_tuple(self.diagnostics, "diagnostics")
        )
        if self.outcome in {
            IssueMutationOutcome.APPLIED,
            IssueMutationOutcome.IDEMPOTENT,
        }:
            if type(self.projection) is not IssueReadProjection:
                raise IssueOperationContractError(
                    "successful mutation requires an Issue read projection"
                )
            if self.projection.issue_ref != self.issue_ref:
                raise IssueOperationContractError(
                    "mutation projection identity must match issue_ref"
                )
        elif self.projection is not None:
            raise IssueOperationContractError(
                "refused mutation must not carry an Issue projection"
            )

    def to_wire(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "contract": ISSUE_MUTATION_RESULT_CONTRACT,
            "operation_ref": self.operation_ref,
            "outcome": self.outcome.value,
            "issue_ref": self.issue_ref,
            "projection_ref": ISSUE_PROJECTION_SCHEMA_VERSION,
            "projection": (
                self.projection.to_payload(include_raw_markdown=False)
                if self.projection is not None
                else None
            ),
            "provider_ref": self.provider_ref,
            "provider_distribution": self.provider_distribution,
            "provider_version": self.provider_version,
            "source_sha256_before": self.source_sha256_before,
            "source_sha256_after": self.source_sha256_after,
            "closeout_publication_receipt_ref": (self.closeout_publication_receipt_ref),
            "evidence": list(self.evidence),
            "diagnostics": list(self.diagnostics),
        }
        if self.closeout_publication_receipt_ref is not None:
            payload.update(
                shared_index_projection=self.shared_index_projection,
                shared_index_projection_error=self.shared_index_projection_error,
                index_reconciliation_pending=self.index_reconciliation_pending,
            )
        return payload


@dataclass(frozen=True, slots=True)
class IssueCommitWorkspaceResult:
    outcome: IssuePublicationOutcome
    issue_ref: str
    target_paths: tuple[str, ...]
    provider_ref: str
    provider_distribution: str
    provider_version: str
    operator_ref: str
    transaction_mode: str
    commit_hash: str | None = None
    reference_update: str = "not_run"
    evidence: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()
    operation_ref: str = ISSUE_COMMIT_WORKSPACE_OPERATION_REF
    shared_index_projection: str | None = None
    shared_index_projection_error: str | None = None
    index_reconciliation_pending: bool | None = None

    def __post_init__(self) -> None:
        if type(self.outcome) is not IssuePublicationOutcome:
            raise IssueOperationContractError("outcome must be IssuePublicationOutcome")
        if self.operation_ref != ISSUE_COMMIT_WORKSPACE_OPERATION_REF:
            raise IssueOperationContractError(
                "operation_ref must identify issue_sdk.commit_workspace"
            )
        if self.shared_index_projection is not None and (
            type(self.shared_index_projection) is not str
            or self.shared_index_projection not in {"not_run", "applied", "failed"}
        ):
            raise IssueOperationContractError("invalid shared_index_projection")
        if (
            self.index_reconciliation_pending is not None
            and type(self.index_reconciliation_pending) is not bool
        ):
            raise IssueOperationContractError(
                "index_reconciliation_pending must be bool or null"
            )
        if self.shared_index_projection_error is not None:
            object.__setattr__(
                self,
                "shared_index_projection_error",
                _text(
                    self.shared_index_projection_error, "shared_index_projection_error"
                ),
            )
        for field_name in (
            "issue_ref",
            "provider_ref",
            "provider_distribution",
            "provider_version",
            "operator_ref",
            "transaction_mode",
            "reference_update",
        ):
            object.__setattr__(
                self, field_name, _text(getattr(self, field_name), field_name)
            )
        object.__setattr__(
            self, "target_paths", _text_tuple(self.target_paths, "target_paths")
        )
        object.__setattr__(self, "evidence", _text_tuple(self.evidence, "evidence"))
        object.__setattr__(
            self, "diagnostics", _text_tuple(self.diagnostics, "diagnostics")
        )
        if self.outcome is IssuePublicationOutcome.APPLIED:
            object.__setattr__(self, "commit_hash", _git_hash(self.commit_hash))
        elif self.commit_hash is not None:
            raise IssueOperationContractError(
                "only applied publication may carry commit_hash"
            )

    @property
    def publication_receipt_ref(self) -> str | None:
        return None if self.commit_hash is None else f"git:{self.commit_hash}"

    def to_wire(self) -> dict[str, object]:
        return {
            "contract": ISSUE_COMMIT_WORKSPACE_RESULT_CONTRACT,
            "operation_ref": self.operation_ref,
            "outcome": self.outcome.value,
            "issue_ref": self.issue_ref,
            "target_paths": list(self.target_paths),
            "provider_ref": self.provider_ref,
            "provider_distribution": self.provider_distribution,
            "provider_version": self.provider_version,
            "operator_ref": self.operator_ref,
            "transaction_mode": self.transaction_mode,
            "commit_hash": self.commit_hash,
            "publication_receipt_ref": self.publication_receipt_ref,
            "shared_index_projection": self.shared_index_projection,
            "shared_index_projection_error": self.shared_index_projection_error,
            "index_reconciliation_pending": self.index_reconciliation_pending,
            "reference_update": self.reference_update,
            "evidence": list(self.evidence),
            "diagnostics": list(self.diagnostics),
        }


class IssueReadProjectionResolveProvider(Protocol):
    def resolve_read_projection(
        self,
        request: IssueReadProjectionResolveRequest,
    ) -> IssueReadProjectionResolveResult: ...


class IssueOperationProvider(IssueReadProjectionResolveProvider, Protocol):
    def ensure_issue_snapshot(
        self, request: IssueEnsureSnapshotRequest
    ) -> IssueMutationResult: ...

    def start_issue_progress(
        self, request: IssueStartProgressRequest
    ) -> IssueMutationResult: ...

    def block_issue(self, request: IssueBlockRequest) -> IssueMutationResult: ...

    def resume_issue(self, request: IssueResumeRequest) -> IssueMutationResult: ...

    def set_issue_owner(self, request: IssueSetOwnerRequest) -> IssueMutationResult: ...

    def bind_issue_scope_paths(
        self, request: IssueBindScopePathsRequest
    ) -> IssueMutationResult: ...

    def append_issue_update(
        self, request: IssueAppendUpdateRequest
    ) -> IssueMutationResult: ...

    def append_issue_evidence(
        self, request: IssueAppendEvidenceRequest
    ) -> IssueMutationResult: ...

    def close_issue(self, request: IssueCloseRequest) -> IssueMutationResult: ...

    def commit_workspace(
        self, request: IssueCommitWorkspaceRequest
    ) -> IssueCommitWorkspaceResult: ...


type _RequestValue = (
    IssueReadProjectionResolveRequest
    | IssueEnsureSnapshotRequest
    | IssueStartProgressRequest
    | IssueBlockRequest
    | IssueResumeRequest
    | IssueSetOwnerRequest
    | IssueBindScopePathsRequest
    | IssueAppendUpdateRequest
    | IssueAppendEvidenceRequest
    | IssueCloseRequest
    | IssueCommitWorkspaceRequest
)
type _ResultValue = (
    IssueReadProjectionResolveResult | IssueMutationResult | IssueCommitWorkspaceResult
)


def _check_shape(value: object, expected: object, depth: int = 0) -> None:
    """Check declared Python value shapes, not lifecycle or authority policy."""
    if depth > 32:
        raise IssueOperationContractError("operation_value_depth_invalid")
    origin = get_origin(expected)
    if origin is UnionType:
        for choice in get_args(expected):
            try:
                _check_shape(value, choice, depth + 1)
                return
            except IssueOperationContractError:
                pass
        raise IssueOperationContractError("operation_value_type_invalid")
    if origin is tuple:
        if type(value) is not tuple:
            raise IssueOperationContractError("operation_value_type_invalid")
        arguments = get_args(expected)
        if len(arguments) == 2 and arguments[1] is Ellipsis:
            for item in value:
                _check_shape(item, arguments[0], depth + 1)
        else:
            if len(value) != len(arguments):
                raise IssueOperationContractError("operation_value_type_invalid")
            for item, item_type in zip(value, arguments, strict=True):
                _check_shape(item, item_type, depth + 1)
        return
    if not isinstance(expected, type) or type(value) is not expected:
        raise IssueOperationContractError("operation_value_type_invalid")
    if isinstance(expected, type) and is_dataclass(expected):
        hints = get_type_hints(expected)
        for field in fields(expected):
            _check_shape(
                object.__getattribute__(value, field.name), hints[field.name], depth + 1
            )
        if expected is IssueReadProjection:
            projection = cast(IssueReadProjection, value)
            if projection.schema_version != ISSUE_PROJECTION_SCHEMA_VERSION:
                raise IssueOperationContractError("projection_contract_invalid")
            _sha256(projection.source_digest, "projection_source_digest")


_REPORT_FIELDS = (
    "operation_ref",
    "issue_ref",
    "outcome",
    "commit_hash",
    "publication_receipt_ref",
    "closeout_publication_receipt_ref",
    "operator_ref",
    "transaction_mode",
    "reference_update",
    "shared_index_projection",
    "shared_index_projection_error",
    "index_reconciliation_pending",
    "source_sha256_before",
    "source_sha256_after",
    "target_paths",
    "provider_ref",
    "provider_distribution",
    "provider_version",
    "projection_ref",
    "effect",
    "evidence",
    "diagnostics",
)


def _report_json_value(value: object, depth: int = 0) -> object:
    if depth > 4:
        raise ValueError("report_value_depth")
    if type(value) in {
        IssueMutationOutcome,
        IssuePublicationOutcome,
        IssueReadProjectionResolveOutcome,
    }:
        return cast(
            IssueMutationOutcome
            | IssuePublicationOutcome
            | IssueReadProjectionResolveOutcome,
            value,
        ).value
    if value is None or type(value) in {bool, int}:
        return value
    if type(value) is str and len(value) <= 8192:
        return value
    if type(value) in {tuple, list}:
        sequence = cast(tuple[object, ...] | list[object], value)
        if len(sequence) <= 128:
            return [_report_json_value(item, depth + 1) for item in sequence]
    raise ValueError("report_value_unavailable")


def _capture_report(value: object) -> IssueProviderReport:
    """No arbitrary to_wire/property/repr calls, raw Markdown or unknown keys."""
    captured: dict[str, object] = {}
    diagnostics: list[str] = []
    known = type(value) in {
        IssueReadProjectionResolveResult,
        IssueMutationResult,
        IssueCommitWorkspaceResult,
    }
    if not known and type(value) is not dict:
        return IssueProviderReport(
            None,
            () if value is None else ("provider_report_unavailable:unsupported_value",),
        )
    data: dict[str, object] = {}
    if known:
        names = {
            field.name
            for field in fields(
                cast(
                    IssueReadProjectionResolveResult
                    | IssueMutationResult
                    | IssueCommitWorkspaceResult,
                    value,
                )
            )
        }
    else:
        # Copy only exact string keys without hashing/comparing foreign keys.
        for index, (key, item) in enumerate(
            dict.items(cast(dict[object, object], value))
        ):
            if index >= 4096:
                diagnostics.append("provider_report_key_budget")
                break
            if type(key) is str and key in _REPORT_FIELDS:
                data[key] = item
        names = set(data)
    used = 2
    for name in _REPORT_FIELDS:
        if name not in names and not (
            known
            and type(value) is IssueCommitWorkspaceResult
            and name == "publication_receipt_ref"
        ):
            continue
        try:
            if name == "publication_receipt_ref" and known:
                commit = object.__getattribute__(value, "commit_hash")
                if commit is not None and type(commit) is not str:
                    raise ValueError("report_value_unavailable")
                raw = None if commit is None else f"git:{commit}"
            else:
                raw = object.__getattribute__(value, name) if known else data[name]
            safe = _report_json_value(raw)
            encoded = json.dumps({name: safe}, sort_keys=True, allow_nan=False)
            if used + len(encoded) > 32768:
                raise ValueError("report_value_budget")
            captured[name] = safe
            used += len(encoded)
        except BaseException:  # noqa: BLE001 — evidence capture cannot mask the original failure
            # Capturing evidence cannot erase the original failure or result.
            diagnostics.append(f"provider_report_field_unavailable:{name}")
    if known and "projection" in names:
        diagnostics.append("provider_projection_not_exported")
    return IssueProviderReport(
        json.dumps(captured, sort_keys=True, separators=(",", ":")),
        tuple(diagnostics),
    )


def _provider_error_value(error: BaseException) -> object:
    # Use BaseException's own storage descriptor, never a subclass property.
    values = BaseException.__dict__["__dict__"].__get__(error, BaseException)
    return values.get("provider_result", error) if type(values) is dict else error


def _boundary_error(
    error_type: type[IssueOperationFailure],
    code: str,
    phase: str,
    operation_ref: str,
    request: object,
    value: object,
) -> IssueProviderResultError:
    issue_ref = None
    if is_dataclass(type(request)):
        # Callers only supply the exact, previously checked request here.
        try:
            candidate = object.__getattribute__(request, "issue_ref")
        except AttributeError:
            candidate = None
        if type(candidate) is str:
            issue_ref = candidate
    return IssueProviderResultError(
        error_type(
            code=code,
            phase=phase,
            operation_ref=operation_ref,
            issue_ref=issue_ref,
            provider_invoked=phase != "request",
            effect="none" if phase == "request" else "unknown",
            provider_result=_capture_report(value),
        ),
        provider_result=value,
    )


def _invoke_operation[Request: _RequestValue, Result: _ResultValue](
    request: object,
    request_type: type[Request],
    result_type: type[Result],
    operation_ref: str,
    error_type: type[IssueOperationFailure],
    call: Callable[[Request], object],
) -> Result:
    try:
        _check_shape(request, request_type)
        admitted_request = cast(Request, request)
        checked = replace(admitted_request)
        if checked != request:
            raise IssueOperationContractError("request_normalization_mismatch")
    except (TypeError, ValueError, AttributeError, RecursionError) as error:
        original = request if type(request) is request_type else None
        raise _boundary_error(
            error_type, "request_invalid", "request", operation_ref, original, None
        ) from error
    admitted_request = cast(Request, request)
    try:
        result = call(admitted_request)
    except BaseException as error:
        code = (
            "provider_invocation_failed"
            if isinstance(error, Exception)
            else "provider_invocation_interrupted"
        )
        raise _boundary_error(
            error_type,
            code,
            "provider",
            operation_ref,
            admitted_request,
            _provider_error_value(error),
        ) from error
    try:
        _check_shape(result, result_type)
        accepted_result = cast(Result, result)
        checked_result = replace(accepted_result)
        if checked_result != result:
            raise IssueOperationContractError("result_normalization_mismatch")
        if (
            accepted_result.operation_ref != operation_ref
            or accepted_result.issue_ref != admitted_request.issue_ref
        ):
            raise IssueOperationContractError("result_identity_mismatch")
        if result_type is IssueCommitWorkspaceResult:
            publication = cast(IssueCommitWorkspaceResult, accepted_result)
            publication_request = cast(IssueCommitWorkspaceRequest, admitted_request)
            if (
                len(set(publication.target_paths)) != len(publication.target_paths)
                or tuple(sorted(publication.target_paths))
                != publication_request.target_paths
            ):
                raise IssueOperationContractError("publication_paths_mismatch")
            if (
                (
                    publication_request.dry_run
                    and publication.outcome is IssuePublicationOutcome.APPLIED
                )
                or (
                    not publication_request.dry_run
                    and publication.outcome is IssuePublicationOutcome.PLANNED
                )
                or (
                    publication.outcome is IssuePublicationOutcome.APPLIED
                    and publication.reference_update == "cas_failed"
                )
            ):
                raise IssueOperationContractError("publication_outcome_mismatch")
    except BaseException as error:
        raise _boundary_error(
            error_type,
            "provider_result_invalid",
            "result",
            operation_ref,
            admitted_request,
            result,
        ) from error
    return cast(Result, result)


@dataclass(frozen=True, slots=True)
class IssueSdkOperationClient:
    """Canonical Issue operation client with an explicit authority provider."""

    provider: IssueOperationProvider
    repository_client: IssueRepositoryPublicationClient | None = None

    def observe_specification_iteration_binding(
        self, request: IssueSpecificationIterationBindingObserveRequest
    ) -> IssueSpecificationIterationBindingObservation:
        from .specification_iteration import observe_pairing

        return observe_pairing(self.provider, request)

    def resolve_read_projection(
        self,
        request: IssueReadProjectionResolveRequest,
    ) -> IssueReadProjectionResolveResult:
        return _invoke_operation(
            request,
            IssueReadProjectionResolveRequest,
            IssueReadProjectionResolveResult,
            ISSUE_RESOLVE_READ_PROJECTION_OPERATION_REF,
            IssueReadProjectionResolveError,
            lambda value: self.provider.resolve_read_projection(value),
        )

    def ensure_issue_snapshot(
        self, request: IssueEnsureSnapshotRequest
    ) -> IssueMutationResult:
        return _invoke_operation(
            request,
            IssueEnsureSnapshotRequest,
            IssueMutationResult,
            ISSUE_ENSURE_SNAPSHOT_OPERATION_REF,
            IssueMutationError,
            lambda value: self.provider.ensure_issue_snapshot(value),
        )

    def start_issue_progress(
        self, request: IssueStartProgressRequest
    ) -> IssueMutationResult:
        return _invoke_operation(
            request,
            IssueStartProgressRequest,
            IssueMutationResult,
            ISSUE_START_PROGRESS_OPERATION_REF,
            IssueMutationError,
            lambda value: self.provider.start_issue_progress(value),
        )

    def block_issue(self, request: IssueBlockRequest) -> IssueMutationResult:
        return _invoke_operation(
            request,
            IssueBlockRequest,
            IssueMutationResult,
            ISSUE_BLOCK_OPERATION_REF,
            IssueMutationError,
            lambda value: self.provider.block_issue(value),
        )

    def resume_issue(self, request: IssueResumeRequest) -> IssueMutationResult:
        return _invoke_operation(
            request,
            IssueResumeRequest,
            IssueMutationResult,
            ISSUE_RESUME_OPERATION_REF,
            IssueMutationError,
            lambda value: self.provider.resume_issue(value),
        )

    def set_issue_owner(self, request: IssueSetOwnerRequest) -> IssueMutationResult:
        return _invoke_operation(
            request,
            IssueSetOwnerRequest,
            IssueMutationResult,
            ISSUE_SET_OWNER_OPERATION_REF,
            IssueMutationError,
            lambda value: self.provider.set_issue_owner(value),
        )

    def bind_issue_scope_paths(
        self, request: IssueBindScopePathsRequest
    ) -> IssueMutationResult:
        return _invoke_operation(
            request,
            IssueBindScopePathsRequest,
            IssueMutationResult,
            ISSUE_BIND_SCOPE_OPERATION_REF,
            IssueMutationError,
            lambda value: self.provider.bind_issue_scope_paths(value),
        )

    def append_issue_update(
        self, request: IssueAppendUpdateRequest
    ) -> IssueMutationResult:
        return _invoke_operation(
            request,
            IssueAppendUpdateRequest,
            IssueMutationResult,
            ISSUE_APPEND_UPDATE_OPERATION_REF,
            IssueMutationError,
            lambda value: self.provider.append_issue_update(value),
        )

    def append_issue_evidence(
        self, request: IssueAppendEvidenceRequest
    ) -> IssueMutationResult:
        return _invoke_operation(
            request,
            IssueAppendEvidenceRequest,
            IssueMutationResult,
            ISSUE_APPEND_EVIDENCE_OPERATION_REF,
            IssueMutationError,
            lambda value: self.provider.append_issue_evidence(value),
        )

    def close_issue(
        self, request: IssueCloseRequest
    ) -> IssueMutationResult | IssueRepositoryOperationResult:
        if self.repository_client is not None:
            from .repository_publication import IssueRepositoryPublicationClient

            if type(self.repository_client) is not IssueRepositoryPublicationClient:
                raise TypeError("Original Issue repository SDK client required")
            return self.repository_client.close_issue_result(request)
        return _invoke_operation(
            request,
            IssueCloseRequest,
            IssueMutationResult,
            ISSUE_CLOSE_OPERATION_REF,
            IssueMutationError,
            lambda value: self.provider.close_issue(value),
        )

    def commit_workspace(
        self, request: IssueCommitWorkspaceRequest
    ) -> IssueCommitWorkspaceResult | IssueRepositoryOperationResult:
        if self.repository_client is not None:
            from .repository_publication import IssueRepositoryPublicationClient

            if type(self.repository_client) is not IssueRepositoryPublicationClient:
                raise TypeError("Original Issue repository SDK client required")
            return self.repository_client.commit_workspace_result(request)
        return _invoke_operation(
            request,
            IssueCommitWorkspaceRequest,
            IssueCommitWorkspaceResult,
            ISSUE_COMMIT_WORKSPACE_OPERATION_REF,
            IssueCommitWorkspaceError,
            lambda value: self.provider.commit_workspace(value),
        )


__all__ = [
    "ISSUE_APPEND_EVIDENCE_OPERATION_REF",
    "ISSUE_APPEND_EVIDENCE_PROVIDER_OPERATION_REF",
    "ISSUE_APPEND_UPDATE_OPERATION_REF",
    "ISSUE_APPEND_UPDATE_PROVIDER_OPERATION_REF",
    "ISSUE_BIND_SCOPE_OPERATION_REF",
    "ISSUE_BIND_SCOPE_PROVIDER_OPERATION_REF",
    "ISSUE_BLOCK_OPERATION_REF",
    "ISSUE_BLOCK_PROVIDER_OPERATION_REF",
    "ISSUE_CLOSE_OPERATION_REF",
    "ISSUE_CLOSE_PROVIDER_OPERATION_REF",
    "ISSUE_COMMIT_WORKSPACE_OPERATION_REF",
    "ISSUE_COMMIT_WORKSPACE_PROVIDER_OPERATION_REF",
    "ISSUE_COMMIT_WORKSPACE_RESULT_CONTRACT",
    "ISSUE_ENSURE_SNAPSHOT_OPERATION_REF",
    "ISSUE_ENSURE_SNAPSHOT_PROVIDER_OPERATION_REF",
    "ISSUE_MUTATION_RESULT_CONTRACT",
    "ISSUE_READ_PROJECTION_RESOLVE_REQUEST_CONTRACT",
    "ISSUE_READ_PROJECTION_RESOLVE_RESULT_CONTRACT",
    "ISSUE_RESOLVE_READ_PROJECTION_OPERATION_REF",
    "ISSUE_RESOLVE_READ_PROJECTION_PROVIDER_OPERATION_REF",
    "ISSUE_RESUME_OPERATION_REF",
    "ISSUE_RESUME_PROVIDER_OPERATION_REF",
    "ISSUE_SET_OWNER_OPERATION_REF",
    "ISSUE_SET_OWNER_PROVIDER_OPERATION_REF",
    "ISSUE_START_PROGRESS_OPERATION_REF",
    "ISSUE_START_PROGRESS_PROVIDER_OPERATION_REF",
    "IssueAppendEvidenceRequest",
    "IssueAppendUpdateRequest",
    "IssueBindScopePathsRequest",
    "IssueBlockRequest",
    "IssueCloseRequest",
    "IssueCommitWorkspaceError",
    "IssueCommitWorkspaceRequest",
    "IssueCommitWorkspaceResult",
    "IssueEnsureSnapshotRequest",
    "IssueMutationError",
    "IssueMutationOutcome",
    "IssueMutationRequest",
    "IssueMutationResult",
    "IssueOperationContractError",
    "IssueOperationFailure",
    "IssueOperationProvider",
    "IssueProviderReport",
    "IssueProviderResultError",
    "IssuePublicationOutcome",
    "IssueReadProjectionResolveError",
    "IssueReadProjectionResolveOutcome",
    "IssueReadProjectionResolveRequest",
    "IssueReadProjectionResolveResult",
    "IssueResumeRequest",
    "IssueSdkOperationClient",
    "IssueSetOwnerRequest",
    "IssueStartProgressRequest",
]
