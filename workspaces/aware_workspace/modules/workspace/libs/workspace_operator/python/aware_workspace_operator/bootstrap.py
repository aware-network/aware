"""Backward-compatible bootstrap facade over typed workspace pipeline."""

from __future__ import annotations

from aware_workspace_operator.models import (
    SkillPackExporterProtocol,
    SkillPackExportResultProtocol,
    WorkspaceBootstrapOptions,
    WorkspaceBootstrapOutcome,
    WorkspaceCommitOptions,
    WorkspaceCommitOutcome,
    WorkspaceModuleCreateOptions,
    WorkspaceModuleCreateOutcome,
    WorkspaceQualityOptions,
    WorkspaceQualityOutcome,
)
from aware_workspace_operator.commit import (
    print_workspace_commit_result,
    run_workspace_commit,
)
from aware_workspace_operator.module_create import (
    print_workspace_module_create_result,
    run_workspace_module_create,
)
from aware_workspace_operator.pipeline import (
    print_workspace_bootstrap_result,
    resolve_repo_root,
    run_workspace_bootstrap,
)
from aware_workspace_operator.quality import (
    print_workspace_quality_result,
    run_workspace_quality_gates,
)

SkillPackExportResult = SkillPackExportResultProtocol
SkillPackExporter = SkillPackExporterProtocol

__all__ = [
    "SkillPackExportResult",
    "SkillPackExporter",
    "WorkspaceBootstrapOptions",
    "WorkspaceBootstrapOutcome",
    "WorkspaceCommitOptions",
    "WorkspaceCommitOutcome",
    "WorkspaceModuleCreateOptions",
    "WorkspaceModuleCreateOutcome",
    "WorkspaceQualityOptions",
    "WorkspaceQualityOutcome",
    "print_workspace_bootstrap_result",
    "print_workspace_commit_result",
    "print_workspace_module_create_result",
    "print_workspace_quality_result",
    "resolve_repo_root",
    "run_workspace_commit",
    "run_workspace_module_create",
    "run_workspace_quality_gates",
    "run_workspace_bootstrap",
]
