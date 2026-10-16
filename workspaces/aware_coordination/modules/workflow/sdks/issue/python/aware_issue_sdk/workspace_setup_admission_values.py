"""Issue-owned A1 data. Decoding never issues an admission or consumption."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from aware_workspace_sdk.architecture_setup_admission_values import (
    WorkspaceAuthorizedSetupResult,
    WorkspaceSetupFileObservation,
    WorkspaceSetupPlanBinding,
    WorkspaceSetupPrimaryFailure,
    WorkspaceSetupResourceEvidence,
)

ActorMetadataGrade = Literal["declared_metadata_v1"]

AuthorityGrade = Literal["filesystem_harness_observed_v1"]

ClientReleaseOutcome = Literal["not_attempted", "confirmed", "failed", "unknown"]

Ownership = Literal["owned", "borrowed", "released", "unknown"]

Phase = Literal[
    "preparing",
    "prepared",
    "admitted",
    "enrolled",
    "spent",
    "executing",
    "completed",
    "retired",
]

Purpose = Literal["workspace_setup_a1_v1"]


@dataclass(frozen=True, slots=True)
class IssueWorkspaceSetupAdmissionRefusalEvidence:
    code: str
    cause_type: str | None
    binding: IssueWorkspaceSetupBinding | None
    observation: IssueWorkspaceSetupObservation | None
    workspace_result: WorkspaceAuthorizedSetupResult | None
    cleanup: IssueWorkspaceSetupCleanup | None
    primary_failure: WorkspaceSetupPrimaryFailure
    ledger_complete: bool
    client_cleanup: IssueWorkspaceSetupClientCleanup | None


@dataclass(frozen=True, slots=True)
class IssueWorkspaceSetupBinding:
    issue_provider_ref: str
    issue_provider_generation: str
    execution_ref: str
    issue_ref: str
    issue_source_sha256: str
    authority_manifest_locator: str
    authority_manifest_sha256: str
    client_intent_id: str
    workspace_binding: WorkspaceSetupPlanBinding
    effect_paths: tuple[str, ...]
    authority_grade: AuthorityGrade
    actor_metadata_grade: ActorMetadataGrade


@dataclass(frozen=True, slots=True)
class IssueWorkspaceSetupCleanup:
    binding: IssueWorkspaceSetupBinding | None
    ownership: Ownership
    attempted: bool
    outcome: ClientReleaseOutcome
    diagnostics: tuple[str, ...]
    ledger_complete: bool
    resources: tuple[WorkspaceSetupResourceEvidence, ...]
    primary_failure: WorkspaceSetupPrimaryFailure


@dataclass(frozen=True, slots=True)
class IssueWorkspaceSetupClientCleanup:
    provider_ref: str | None
    provider_generation: str | None
    client_ref: str | None
    resources: tuple[WorkspaceSetupResourceEvidence, ...]
    attempted: bool
    outcome: ClientReleaseOutcome
    primary_failure: WorkspaceSetupPrimaryFailure
    diagnostics: tuple[str, ...]
    ledger_complete: bool


@dataclass(frozen=True, slots=True)
class IssueWorkspaceSetupObservation:
    binding: IssueWorkspaceSetupBinding | None
    phase: Phase
    consumption_ref: str | None
    verified_effect_ordinal: int | None
    diagnostics: tuple[str, ...]
    ledger_complete: bool
    resources: tuple[WorkspaceSetupResourceEvidence, ...]
    primary_failure: WorkspaceSetupPrimaryFailure


@dataclass(frozen=True, slots=True)
class IssueWorkspaceSetupRequest:
    issue_ref: str
    expected_issue_source_sha256: str
    actor_ref: str | None
    actor_evidence_ref: str | None
    client_intent_id: str
    purpose: Purpose
    expected_authority_manifest_sha256: str


@dataclass(frozen=True, slots=True)
class IssueWorkspaceSetupSourcesObservation:
    issue_ref: str
    authority_manifest_locator: str
    issue_source: WorkspaceSetupFileObservation
    authority_manifest_source: WorkspaceSetupFileObservation
    execution_ref: str
    authority_grade: AuthorityGrade
    actor_metadata_grade: ActorMetadataGrade
    primary_failure: WorkspaceSetupPrimaryFailure
    ledger_complete: bool


ISSUE_SETUP_VALUE_TYPES = (
    IssueWorkspaceSetupAdmissionRefusalEvidence,
    IssueWorkspaceSetupBinding,
    IssueWorkspaceSetupCleanup,
    IssueWorkspaceSetupClientCleanup,
    IssueWorkspaceSetupObservation,
    IssueWorkspaceSetupRequest,
    IssueWorkspaceSetupSourcesObservation,
)
ISSUE_SETUP_WIRE_IDS = {
    IssueWorkspaceSetupAdmissionRefusalEvidence: "aware.issue.workspace-setup-a1-refusal-evidence.v1",
    IssueWorkspaceSetupBinding: "aware.issue.setup-a1-issue-workspace-setup-binding.v1",
    IssueWorkspaceSetupCleanup: "aware.issue.workspace-setup-a1-cleanup.v1",
    IssueWorkspaceSetupClientCleanup: "aware.issue.workspace-setup-a1-client-cleanup.v1",
    IssueWorkspaceSetupObservation: "aware.issue.workspace-setup-a1-observation.v1",
    IssueWorkspaceSetupRequest: "aware.issue.setup-a1-issue-workspace-setup-request.v1",
    IssueWorkspaceSetupSourcesObservation: "aware.issue.workspace-setup-a1-sources-observation.v1",
}
ISSUE_SETUP_FIELD_TYPES = {
    IssueWorkspaceSetupAdmissionRefusalEvidence: (
        ("code", "Code"),
        ("cause_type", "Nullable[Code]"),
        ("binding", "Nullable[IssueWorkspaceSetupBinding]"),
        ("observation", "Nullable[IssueWorkspaceSetupObservation]"),
        ("workspace_result", "Nullable[WorkspaceAuthorizedSetupResult]"),
        ("cleanup", "Nullable[IssueWorkspaceSetupCleanup]"),
        ("primary_failure", "WorkspaceSetupPrimaryFailure"),
        ("ledger_complete", "Bool"),
        ("client_cleanup", "Nullable[IssueWorkspaceSetupClientCleanup]"),
    ),
    IssueWorkspaceSetupBinding: (
        ("issue_provider_ref", "Ref"),
        ("issue_provider_generation", "Ref"),
        ("execution_ref", "Ref"),
        ("issue_ref", "RelativePath"),
        ("issue_source_sha256", "Digest"),
        ("authority_manifest_locator", "RelativePath"),
        ("authority_manifest_sha256", "Digest"),
        ("client_intent_id", "Ref"),
        ("workspace_binding", "WorkspaceSetupPlanBinding"),
        ("effect_paths", "Array[RelativePath]"),
        ("authority_grade", "AuthorityGrade"),
        ("actor_metadata_grade", "ActorMetadataGrade"),
    ),
    IssueWorkspaceSetupCleanup: (
        ("binding", "Nullable[IssueWorkspaceSetupBinding]"),
        ("ownership", "Ownership"),
        ("attempted", "Bool"),
        ("outcome", "ClientReleaseOutcome"),
        ("diagnostics", "Array[Diagnostic]"),
        ("ledger_complete", "Bool"),
        ("resources", "Array[WorkspaceSetupResourceEvidence]"),
        ("primary_failure", "WorkspaceSetupPrimaryFailure"),
    ),
    IssueWorkspaceSetupClientCleanup: (
        ("provider_ref", "Nullable[Ref]"),
        ("provider_generation", "Nullable[Ref]"),
        ("client_ref", "Nullable[Ref]"),
        ("resources", "Array[WorkspaceSetupResourceEvidence]"),
        ("attempted", "Bool"),
        ("outcome", "ClientReleaseOutcome"),
        ("primary_failure", "WorkspaceSetupPrimaryFailure"),
        ("diagnostics", "Array[Diagnostic]"),
        ("ledger_complete", "Bool"),
    ),
    IssueWorkspaceSetupObservation: (
        ("binding", "Nullable[IssueWorkspaceSetupBinding]"),
        ("phase", "Phase"),
        ("consumption_ref", "Nullable[Ref]"),
        ("verified_effect_ordinal", "Nullable[U64]"),
        ("diagnostics", "Array[Diagnostic]"),
        ("ledger_complete", "Bool"),
        ("resources", "Array[WorkspaceSetupResourceEvidence]"),
        ("primary_failure", "WorkspaceSetupPrimaryFailure"),
    ),
    IssueWorkspaceSetupRequest: (
        ("issue_ref", "RelativePath"),
        ("expected_issue_source_sha256", "Digest"),
        ("actor_ref", "Nullable[Ref]"),
        ("actor_evidence_ref", "Nullable[Ref]"),
        ("client_intent_id", "Ref"),
        ("purpose", "Purpose"),
        ("expected_authority_manifest_sha256", "Digest"),
    ),
    IssueWorkspaceSetupSourcesObservation: (
        ("issue_ref", "RelativePath"),
        ("authority_manifest_locator", "RelativePath"),
        ("issue_source", "WorkspaceSetupFileObservation"),
        ("authority_manifest_source", "WorkspaceSetupFileObservation"),
        ("execution_ref", "Ref"),
        ("authority_grade", "AuthorityGrade"),
        ("actor_metadata_grade", "ActorMetadataGrade"),
        ("primary_failure", "WorkspaceSetupPrimaryFailure"),
        ("ledger_complete", "Bool"),
    ),
}
ISSUE_SETUP_ENUMS = {
    "ActorMetadataGrade": ["declared_metadata_v1"],
    "AuthorityGrade": ["filesystem_harness_observed_v1"],
    "ClientReleaseOutcome": ["not_attempted", "confirmed", "failed", "unknown"],
    "Ownership": ["owned", "borrowed", "released", "unknown"],
    "Phase": [
        "preparing",
        "prepared",
        "admitted",
        "enrolled",
        "spent",
        "executing",
        "completed",
        "retired",
    ],
    "Purpose": ["workspace_setup_a1_v1"],
}
