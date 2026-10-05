"""Provider-neutral contracts for canonical Issue SDK operations."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar, Protocol, cast

from aware_issue_runtime import ISSUE_PROJECTION_SCHEMA_VERSION, IssueReadProjection

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


@dataclass(frozen=True, slots=True)
class IssueAppendUpdateRequest(IssueMutationRequest):
    message: str = ""
    outcome: str = "info"
    operation_ref: ClassVar[str] = ISSUE_APPEND_UPDATE_OPERATION_REF

    def __post_init__(self) -> None:
        IssueMutationRequest.__post_init__(self)
        object.__setattr__(self, "message", _text(self.message, "message"))
        object.__setattr__(self, "outcome", _text(self.outcome, "outcome"))


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


@dataclass(frozen=True, slots=True)
class IssueSdkOperationClient:
    """Canonical Issue operation client with an explicit authority provider."""

    provider: IssueOperationProvider

    def resolve_read_projection(
        self,
        request: IssueReadProjectionResolveRequest,
    ) -> IssueReadProjectionResolveResult:
        return self.provider.resolve_read_projection(request)

    def ensure_issue_snapshot(
        self, request: IssueEnsureSnapshotRequest
    ) -> IssueMutationResult:
        return self.provider.ensure_issue_snapshot(request)

    def start_issue_progress(
        self, request: IssueStartProgressRequest
    ) -> IssueMutationResult:
        return self.provider.start_issue_progress(request)

    def block_issue(self, request: IssueBlockRequest) -> IssueMutationResult:
        return self.provider.block_issue(request)

    def resume_issue(self, request: IssueResumeRequest) -> IssueMutationResult:
        return self.provider.resume_issue(request)

    def set_issue_owner(self, request: IssueSetOwnerRequest) -> IssueMutationResult:
        return self.provider.set_issue_owner(request)

    def bind_issue_scope_paths(
        self, request: IssueBindScopePathsRequest
    ) -> IssueMutationResult:
        return self.provider.bind_issue_scope_paths(request)

    def append_issue_update(
        self, request: IssueAppendUpdateRequest
    ) -> IssueMutationResult:
        return self.provider.append_issue_update(request)

    def append_issue_evidence(
        self, request: IssueAppendEvidenceRequest
    ) -> IssueMutationResult:
        return self.provider.append_issue_evidence(request)

    def close_issue(self, request: IssueCloseRequest) -> IssueMutationResult:
        return self.provider.close_issue(request)

    def commit_workspace(
        self, request: IssueCommitWorkspaceRequest
    ) -> IssueCommitWorkspaceResult:
        return self.provider.commit_workspace(request)


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
    "IssueCommitWorkspaceRequest",
    "IssueCommitWorkspaceResult",
    "IssueEnsureSnapshotRequest",
    "IssueMutationOutcome",
    "IssueMutationRequest",
    "IssueMutationResult",
    "IssueOperationContractError",
    "IssueOperationProvider",
    "IssuePublicationOutcome",
    "IssueReadProjectionResolveOutcome",
    "IssueReadProjectionResolveRequest",
    "IssueReadProjectionResolveResult",
    "IssueResumeRequest",
    "IssueSdkOperationClient",
    "IssueSetOwnerRequest",
    "IssueStartProgressRequest",
]
