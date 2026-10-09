"""Workspace experience/bootstrap rails for Aware."""

from importlib import import_module

# Avoid importing bridge/quality/bootstrap rails for a command that only needs
# commit models and functions.  Keep the public package exports intact through
# PEP 562 lazy attribute resolution.
_EXPORT_MODULES = {
    "BridgeEvidenceEvent": ".bridge.models",
    "CompilerOperationResult": ".bridge.models",
    "UpgradeExecutionResult": ".bridge.models",
    "WorkspaceBridgeCycleRequest": ".bridge.models",
    "WorkspaceBridgeCycleResult": ".bridge.models",
    "CompilerSessionPort": ".bridge.interfaces",
    "EvidencePort": ".bridge.interfaces",
    "UpgradePort": ".bridge.interfaces",
    "WorkspaceDeltaPort": ".bridge.interfaces",
    "WorkspaceBridgeOrchestrator": ".bridge.orchestrator",
    "print_workspace_commit_result": ".commit",
    "run_workspace_authorized_commit": ".commit",
    "run_workspace_commit": ".commit",
    "run_workspace_content_commit": ".commit",
    "verify_repository_commit_receipt": ".commit",
    "ResidentCommitAdmissionEvidence": ".models",
    "WorkspaceAuthorizedCommitOptions": ".models",
    "WorkspaceBootstrapOptions": ".models",
    "WorkspaceCommitIssueMetadata": ".models",
    "WorkspaceCommitOptions": ".models",
    "WorkspaceCommitOutcome": ".models",
    "WorkspaceContentCommitOptions": ".models",
    "WorkspaceSuppliedPathContent": ".models",
    "WorkspaceModuleCreateOptions": ".models",
    "WorkspaceModuleCreateReport": ".models",
    "WorkspaceQualityOptions": ".models",
    "WorkspaceQualityOutcome": ".models",
    "resolve_repo_root": ".pipeline.utils",
    "print_workspace_quality_result": ".quality",
    "run_workspace_quality_gates": ".quality",
}

_LAZY_EXPORTS = {
    "SkillPackExportResult": ".bootstrap",
    "SkillPackExporter": ".bootstrap",
    "WorkspaceBootstrapOutcome": ".bootstrap",
    "WorkspaceModuleCreateOutcome": ".bootstrap",
    "print_workspace_bootstrap_result": ".bootstrap",
    "print_workspace_module_create_result": ".bootstrap",
    "run_workspace_bootstrap": ".bootstrap",
    "run_workspace_module_create": ".bootstrap",
}


def __getattr__(name: str):  # type: ignore[no-untyped-def]
    module_name = _EXPORT_MODULES.get(name)
    if module_name is not None:
        module = import_module(module_name, package=__name__)
        value = getattr(module, name)
        globals()[name] = value
        return value

    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(
            f"module 'aware_workspace_operator' has no attribute {name!r}"
        )
    module = import_module(module_name, package=__name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


__all__ = [
    "BridgeEvidenceEvent",
    "CompilerOperationResult",
    "CompilerSessionPort",
    "EvidencePort",
    "ResidentCommitAdmissionEvidence",
    "SkillPackExportResult",
    "SkillPackExporter",
    "UpgradeExecutionResult",
    "UpgradePort",
    "WorkspaceAuthorizedCommitOptions",
    "WorkspaceBootstrapOptions",
    "WorkspaceBootstrapOutcome",
    "WorkspaceBridgeCycleRequest",
    "WorkspaceBridgeCycleResult",
    "WorkspaceBridgeOrchestrator",
    "WorkspaceCommitIssueMetadata",
    "WorkspaceCommitOptions",
    "WorkspaceCommitOutcome",
    "WorkspaceContentCommitOptions",
    "WorkspaceDeltaPort",
    "WorkspaceModuleCreateOptions",
    "WorkspaceModuleCreateOutcome",
    "WorkspaceModuleCreateReport",
    "WorkspaceQualityOptions",
    "WorkspaceQualityOutcome",
    "WorkspaceSuppliedPathContent",
    "print_workspace_bootstrap_result",
    "print_workspace_commit_result",
    "print_workspace_module_create_result",
    "print_workspace_quality_result",
    "resolve_repo_root",
    "run_workspace_authorized_commit",
    "run_workspace_bootstrap",
    "run_workspace_commit",
    "run_workspace_content_commit",
    "run_workspace_module_create",
    "run_workspace_quality_gates",
    "verify_repository_commit_receipt",
]
