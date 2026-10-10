"""Authored repository-preparation values; none is an authority handle."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

RepositoryPreparationOutcome = Literal["created", "existing", "planned", "refused"]
RepositoryPreparationEffectState = Literal["none", "applied", "unknown"]
RepositoryPreparationCleanupState = Literal[
    "not_attempted", "completed", "incomplete", "unknown"
]


@dataclass(frozen=True, slots=True)
class RepositoryPrepareRequest:
    repository_root: str
    create_if_missing: bool = False
    dry_run: bool = False


@dataclass(frozen=True, slots=True)
class RepositoryPreparationEffect:
    path: str
    kind: str
    state: RepositoryPreparationEffectState
    durability_confirmed: bool
    before_sha256: str | None = None
    after_sha256: str | None = None
    after_device: int | None = None
    after_inode: int | None = None
    mode: int | None = None


@dataclass(frozen=True, slots=True)
class RepositoryPreparationPlanObservation:
    request: RepositoryPrepareRequest
    plan_ref: str
    plan_sha256: str
    execution_id: str
    phase: str
    ordered_effect_paths: tuple[str, ...]
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RepositoryPrepareResult:
    contract: str = field(default="aware.repository.prepare-result.v1", kw_only=True)
    operation_ref: str = field(
        default="repository_sdk.prepare_repository", kw_only=True
    )
    request: RepositoryPrepareRequest
    outcome: RepositoryPreparationOutcome
    repository_root: str
    head: str | None
    diagnostics: tuple[str, ...]
    execution_id: str
    attempt_ref: str | None
    authority_mode: str = field(default="filesystem", kw_only=True)
    effects: tuple[RepositoryPreparationEffect, ...]
    cleanup_state: RepositoryPreparationCleanupState
    ledger_complete: bool
    provider_invoked: bool
    authorizes_retry: bool = False


@dataclass(frozen=True, slots=True)
class RepositoryPreparationErrorEvidence:
    contract: str = field(default="aware.repository.prepare-error.v1", kw_only=True)
    operation_ref: str = field(
        default="repository_sdk.prepare_repository", kw_only=True
    )
    request: RepositoryPrepareRequest
    code: str
    phase: str
    execution_id: str
    attempt_ref: str | None
    effects: tuple[RepositoryPreparationEffect, ...]
    cleanup_state: RepositoryPreparationCleanupState
    ledger_complete: bool
    provider_invoked: bool
    reported_result: object | None
    evidence_grade: str = field(default="unvalidated_provider_report", kw_only=True)
    diagnostics: tuple[str, ...]
    authorizes_retry: bool = False


class RepositoryPreparationError(RuntimeError):
    def __init__(self, *, evidence: RepositoryPreparationErrorEvidence):
        self.evidence = evidence
        super().__init__(evidence.code)
