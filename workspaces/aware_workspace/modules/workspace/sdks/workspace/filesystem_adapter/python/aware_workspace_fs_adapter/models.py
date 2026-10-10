"""Original Git writer models; Operator retains aliases, not duplicate types."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field


class BaseStrictModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


class WorkspaceCommitIssueMetadata(BaseStrictModel):
    issue_tag: str
    issue_owner: str
    issue_status: str
    ownership_scope: tuple[str, ...] = ()


class WorkspaceCommitOptions(BaseStrictModel):
    repo_root: Path
    issue_path: str
    target_paths: tuple[str, ...]
    message: str
    owner_id: str | None = None
    dry_run: bool = False
    allow_empty: bool = False
    issue_metadata: WorkspaceCommitIssueMetadata | None = None
    expected_issue_source_sha256: str | None = None
    reconcile_commit: str | None = None


class WorkspaceAuthorizedPathState(BaseStrictModel):
    """Exact Workspace-authorized repository state admitted for commit."""

    path: str
    expected_exists: bool
    expected_content_digest: str | None = None


class WorkspaceSuppliedPathContent(BaseStrictModel):
    """Exact repository postimage supplied independently of the worktree."""

    path: str
    expected_head_blob_oid: str | None
    content_text: str
    file_mode: Literal["100644", "100755"] = "100644"


class WorkspaceContentCommitOptions(BaseStrictModel):
    """Issue-authorized exact-content branch-ref CAS publication."""

    repo_root: Path
    issue_path: str
    path_contents: tuple[WorkspaceSuppliedPathContent, ...]
    message: str
    owner_id: str | None = None
    expected_head: str
    expected_repository_ref: str
    expected_issue_blob_oid: str | None = None
    semantic_intent_digest: str
    idempotency_ref: str
    dry_run: bool = False


class ResidentCommitAdmissionEvidence(BaseStrictModel):
    """Server-authoritative accountability retained with one repository commit."""

    generation_owner_ref: str
    repository_operation_ref: str
    actor_ref: str
    agent_ref: str | None = None
    human_sponsor_ref: str | None = None
    dev_session_ref: str
    work_context_ref: str
    issue_revision_ref: str
    workspace_session_ref: str
    source_effect_policy: str
    workspace_mutation_receipt_digests: tuple[str, ...] = ()
    provider_source_admission_digests: tuple[str, ...] = ()


class WorkspaceAuthorizedCommitOptions(BaseStrictModel):
    repo_root: Path
    target_paths: tuple[str, ...]
    message: str
    owner_id: str | None = None
    dry_run: bool = False
    allow_empty: bool = False
    idempotency_ref: str | None = None
    authorized_path_states: tuple[WorkspaceAuthorizedPathState, ...] = ()
    resident_admission_evidence: ResidentCommitAdmissionEvidence | None = None


class WorkspaceCommitReport(BaseStrictModel):
    repo_root: str
    issue_path: str | None = None
    issue_tag: str | None = None
    issue_owner: str | None = None
    issue_status: str | None = None
    committed_issue_blob_oid: str | None = None
    owner_id: str | None = None
    ownership_scope: list[str] = Field(default_factory=list)
    requested_paths: list[str] = Field(default_factory=list)
    staged_paths: list[str] = Field(default_factory=list)
    commit_message: str | None = None
    commit_hash: str | None = None
    idempotency_ref: str | None = None
    request_fingerprint: str | None = None
    idempotent_replay: bool = False
    repository_write_preflight: Literal["not_run", "passed", "failed"] = "not_run"
    index_restored: bool | None = None
    transaction_mode: Literal[
        "not_run", "shared_index_snapshot_v0", "isolated_index_atomic_ref_v1"
    ] = "not_run"
    expected_head: str | None = None
    candidate_commit: str | None = None
    updated_reference: str | None = None
    reference_update: Literal["not_run", "cas_applied", "cas_failed"] = "not_run"
    shared_index_unchanged: bool | None = None
    shared_index_projection: Literal["not_run", "applied", "failed"] = "not_run"
    shared_index_projection_error: str | None = None
    index_reconciliation_pending: bool = False
    repository_admission_ref: str | None = None
    repository_admission_evidence_digest: str | None = None
    dry_run: bool = False
    command_log: list[list[str]] = Field(default_factory=list)
    status: Literal["ok", "failed", "planned"]
    error: str | None = None


class WorkspaceCommitOutcome(BaseStrictModel):
    report: WorkspaceCommitReport
    exit_code: int

    @property
    def payload(self) -> dict[str, object]:
        return self.report.model_dump(mode="json")
