"""Typed models for workspace-operator bootstrap pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

WorkspaceBootstrapMode = Literal["remote-managed", "full-local"]
WorkspaceAutomationPhase = Literal["day-1", "phase-2"]


class BaseStrictModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


class SkillPackExportResultProtocol(Protocol):
    """Protocol for skill-pack exporters used by bootstrap."""

    skill_names: tuple[str, ...]
    created_paths: tuple[Path, ...]
    source_root: Path
    resolved_references: dict[str, dict[str, str]]


class SkillPackExporterProtocol(Protocol):
    """Protocol for skill-pack exporters used by bootstrap."""

    def __call__(
        self,
        *,
        destination_root: Path,
        pack_name: str,
        export_mode: str,
    ) -> SkillPackExportResultProtocol: ...


class WorkspaceBootstrapOptions(BaseStrictModel):
    """Input options for workspace bootstrap orchestration."""

    repo_root: Path
    bootstrap_mode: WorkspaceBootstrapMode = "remote-managed"
    requested_module_ids: tuple[str, ...] = ()
    materialization_mode: Literal["all", "runtime", "none"] = "runtime"
    allow_missing_dependencies: bool = False

    write_environment_file: bool = False
    skip_environment_file: bool = False
    environment_file_relpath: str = "aware.environment.toml"
    environment_handle: str = "external"
    environment_title: str = "Aware External Workspace"

    write_agent_files: bool = True
    skip_agent_files: bool = False
    skill_pack: str = "aware-core"
    skill_export_mode: str = "external"

    write_proof_tests: bool = True
    skip_proof_tests: bool = False

    write_collaboration_scaffold: bool = True
    skip_collaboration_scaffold: bool = False

    write_workspace_scaffold: bool = True
    skip_workspace_scaffold: bool = False

    write_delivery_contracts: bool = True
    skip_delivery_contracts: bool = False

    write_grammar_docs_bundle: bool = True
    skip_grammar_docs_bundle: bool = False

    write_software_rules_bundle: bool = True
    skip_software_rules_bundle: bool = False
    software_template_id: str = "mental-model-v1"
    software_profile_id: str = "external-default-v1"

    write_seed_bundle: bool = True
    skip_seed_bundle: bool = False
    automation_phase: WorkspaceAutomationPhase = "day-1"


class MissingDependency(BaseStrictModel):
    module_id: str
    package_name: str
    dependency_package_name: str
    dependency_aware_toml_path: str


class ModuleBootstrapResult(BaseStrictModel):
    module_id: str
    package_names: list[str] = Field(default_factory=list)
    missing_dependencies: list[MissingDependency] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class DiscoveredPackage(BaseStrictModel):
    package_name: str
    aware_toml_path: str


class DuplicatePackage(BaseStrictModel):
    package_name: str
    kept_aware_toml_path: str
    ignored_aware_toml_paths: list[str] = Field(default_factory=list)


class ScaffoldFileStatus(BaseStrictModel):
    key: str
    path: str
    exists: bool
    created: bool


class EnvironmentFileStatus(BaseStrictModel):
    path: str
    exists: bool
    created: bool
    write_requested: bool


class WorkspaceManifestStatus(BaseStrictModel):
    path: str
    exists: bool
    created: bool
    write_requested: bool


class AgentsMdStatus(BaseStrictModel):
    path: str
    exists: bool
    created: bool


class SkillsStatus(BaseStrictModel):
    root_path: str
    exists: bool
    pack_name: str
    export_mode: str
    source_root: str | None = None
    skill_names: list[str] = Field(default_factory=list)
    resolved_references: dict[str, dict[str, str]] = Field(default_factory=dict)
    readme_path: str
    readme_exists: bool
    primary_skill_path: str | None = None
    primary_skill_exists: bool
    created: bool


class AgentFilesStatus(BaseStrictModel):
    write_requested: bool
    created_paths: list[str] = Field(default_factory=list)
    agents_md: AgentsMdStatus
    skills: SkillsStatus


class ProofTestModuleStatus(BaseStrictModel):
    module_id: str
    path: str
    exists: bool
    created: bool


class ProofTestsStatus(BaseStrictModel):
    write_requested: bool
    created_paths: list[str] = Field(default_factory=list)
    modules: list[ProofTestModuleStatus] = Field(default_factory=list)


class CollaborationScaffoldStatus(BaseStrictModel):
    write_requested: bool
    created_paths: list[str] = Field(default_factory=list)
    files: list[ScaffoldFileStatus] = Field(default_factory=list)
    today_log_path: str


class WorkspaceScaffoldStatus(BaseStrictModel):
    write_requested: bool
    created_paths: list[str] = Field(default_factory=list)
    files: list[ScaffoldFileStatus] = Field(default_factory=list)


class DeliveryContractsStatus(BaseStrictModel):
    write_requested: bool
    created_paths: list[str] = Field(default_factory=list)
    files: list[ScaffoldFileStatus] = Field(default_factory=list)
    contracts_root: str


class GrammarDocsBundleStatus(BaseStrictModel):
    write_requested: bool
    created_paths: list[str] = Field(default_factory=list)
    files: list[ScaffoldFileStatus] = Field(default_factory=list)
    docs_root: str
    source_root: str


class SoftwareRulesBundleStatus(BaseStrictModel):
    write_requested: bool
    created_paths: list[str] = Field(default_factory=list)
    files: list[ScaffoldFileStatus] = Field(default_factory=list)
    docs_root: str
    source_root: str
    template_id: str
    profile_id: str
    strict_unresolved: bool
    unresolved_tokens: list[str] = Field(default_factory=list)
    unresolved_by_file: dict[str, list[str]] = Field(default_factory=dict)


class SeedBundleStatus(BaseStrictModel):
    write_requested: bool
    created_paths: list[str] = Field(default_factory=list)
    files: list[ScaffoldFileStatus] = Field(default_factory=list)
    seeds_root: str
    source_root: str


class WorkspaceModulePackageRegistration(BaseStrictModel):
    module_id: str
    surface: str
    language: str
    manager: str
    distribution_name: str
    import_root: str
    package_root: str
    pyproject_path: str


class WorkspaceRootPyprojectStatus(BaseStrictModel):
    path: str
    exists: bool
    planned_action: Literal["create", "overwrite", "skip"]
    workspace_members: list[str] = Field(default_factory=list)
    workspace_sources: list[str] = Field(default_factory=list)


class WorkspaceModuleCreateOptions(BaseStrictModel):
    repo_root: Path
    module_id: str
    dependencies: tuple[str, ...] = ()
    title: str | None = None
    description: str | None = None
    runtime_handler_modules: tuple[str, ...] = ()
    runtime_project_name: str | None = None
    runtime_import_root: str | None = None
    dry_run: bool = False
    force: bool = False


class WorkspaceModuleCreateReport(BaseStrictModel):
    repo_root: str
    module_root: str
    dry_run: bool
    planned_paths: list[str] = Field(default_factory=list)
    created_paths: list[str] = Field(default_factory=list)
    overwritten_paths: list[str] = Field(default_factory=list)
    package_registrations: list[WorkspaceModulePackageRegistration] = Field(
        default_factory=list
    )
    root_pyproject: WorkspaceRootPyprojectStatus
    next_steps: list[str] = Field(default_factory=list)
    status: Literal["ok"] = "ok"


class WorkspaceModuleCreateOutcome(BaseStrictModel):
    report: WorkspaceModuleCreateReport
    exit_code: int

    @property
    def payload(self) -> dict[str, object]:
        return self.report.model_dump(mode="json")


class WorkspaceQualityOptions(BaseStrictModel):
    repo_root: Path
    target_paths: tuple[str, ...] = ()
    include_languages: tuple[str, ...] = ()
    include_gate_ids: tuple[str, ...] = ()
    run_commands: bool = True
    fail_on_missing_command: bool = True


class WorkspaceQualityCommandResult(BaseStrictModel):
    gate_id: str
    language: str
    description: str
    command: list[str] = Field(default_factory=list)
    target_paths: list[str] = Field(default_factory=list)
    status: Literal["planned", "passed", "failed", "skipped"]
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    reason: str | None = None


class WorkspaceQualityReport(BaseStrictModel):
    repo_root: str
    target_paths: list[str] = Field(default_factory=list)
    detected_languages: list[str] = Field(default_factory=list)
    commands: list[WorkspaceQualityCommandResult] = Field(default_factory=list)
    status: Literal["ok", "failed"]


class WorkspaceQualityOutcome(BaseStrictModel):
    report: WorkspaceQualityReport
    exit_code: int

    @property
    def payload(self) -> dict[str, object]:
        return self.report.model_dump(mode="json")


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


class NextRequiredAction(BaseStrictModel):
    code: str
    track: str
    description: str


class WorkspaceBootstrapReport(BaseStrictModel):
    repo_root: str
    bootstrap_mode: WorkspaceBootstrapMode
    module_ids: list[str] = Field(default_factory=list)
    modules: list[ModuleBootstrapResult] = Field(default_factory=list)
    missing_dependencies: list[MissingDependency] = Field(default_factory=list)
    discovered_packages: list[DiscoveredPackage] = Field(default_factory=list)
    duplicate_packages: list[DuplicatePackage] = Field(default_factory=list)
    workspace_manifest: WorkspaceManifestStatus
    environment_file: EnvironmentFileStatus
    agent_files: AgentFilesStatus
    collaboration_scaffold: CollaborationScaffoldStatus
    proof_tests: ProofTestsStatus
    workspace_scaffold: WorkspaceScaffoldStatus
    delivery_contracts: DeliveryContractsStatus
    grammar_docs_bundle: GrammarDocsBundleStatus
    software_rules_bundle: SoftwareRulesBundleStatus
    seed_bundle: SeedBundleStatus
    next_required_actions: list[NextRequiredAction] = Field(default_factory=list)
    status: Literal["ok", "failed"]


class WorkspaceBootstrapOutcome(BaseStrictModel):
    report: WorkspaceBootstrapReport
    exit_code: int

    @property
    def payload(self) -> dict[str, object]:
        return self.report.model_dump(mode="json")


class WorkspacePreflightState(BaseStrictModel):
    module_ids: list[str] = Field(default_factory=list)
    modules: list[ModuleBootstrapResult] = Field(default_factory=list)
    missing_dependencies: list[MissingDependency] = Field(default_factory=list)
    discovered_packages: list[DiscoveredPackage] = Field(default_factory=list)
    duplicate_packages: list[DuplicatePackage] = Field(default_factory=list)
    has_errors: bool = False


class WorkspaceScaffoldState(BaseStrictModel):
    workspace_manifest: WorkspaceManifestStatus
    environment_file: EnvironmentFileStatus
    agent_files: AgentFilesStatus
    collaboration_scaffold: CollaborationScaffoldStatus
    proof_tests: ProofTestsStatus
    workspace_scaffold: WorkspaceScaffoldStatus
    delivery_contracts: DeliveryContractsStatus
    grammar_docs_bundle: GrammarDocsBundleStatus
    software_rules_bundle: SoftwareRulesBundleStatus
    seed_bundle: SeedBundleStatus


__all__ = [
    "AgentFilesStatus",
    "BaseStrictModel",
    "CollaborationScaffoldStatus",
    "DeliveryContractsStatus",
    "DiscoveredPackage",
    "DuplicatePackage",
    "EnvironmentFileStatus",
    "GrammarDocsBundleStatus",
    "MissingDependency",
    "ModuleBootstrapResult",
    "NextRequiredAction",
    "ProofTestModuleStatus",
    "ProofTestsStatus",
    "ResidentCommitAdmissionEvidence",
    "ScaffoldFileStatus",
    "SeedBundleStatus",
    "SkillPackExportResultProtocol",
    "SkillsStatus",
    "SoftwareRulesBundleStatus",
    "WorkspaceAuthorizedCommitOptions",
    "WorkspaceBootstrapMode",
    "WorkspaceBootstrapOptions",
    "WorkspaceBootstrapOutcome",
    "WorkspaceBootstrapReport",
    "WorkspaceCommitIssueMetadata",
    "WorkspaceCommitOptions",
    "WorkspaceCommitOutcome",
    "WorkspaceCommitReport",
    "WorkspaceContentCommitOptions",
    "WorkspaceManifestStatus",
    "WorkspaceModuleCreateOptions",
    "WorkspaceModuleCreateOutcome",
    "WorkspaceModuleCreateReport",
    "WorkspaceModulePackageRegistration",
    "WorkspacePreflightState",
    "WorkspaceQualityCommandResult",
    "WorkspaceQualityOptions",
    "WorkspaceQualityOutcome",
    "WorkspaceQualityReport",
    "WorkspaceRootPyprojectStatus",
    "WorkspaceScaffoldState",
    "WorkspaceScaffoldStatus",
    "WorkspaceSuppliedPathContent",
]
