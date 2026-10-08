"""Central executor for workspace bootstrap stages."""

from __future__ import annotations

from pathlib import Path

from aware_workspace_operator.models import (
    SkillPackExporterProtocol,
    WorkspaceBootstrapOptions,
    WorkspaceBootstrapOutcome,
    WorkspaceBootstrapReport,
)
from aware_workspace_operator.pipeline.stages.preflight import run_preflight_stage
from aware_workspace_operator.pipeline.stages.reporting import (
    build_report,
    print_workspace_bootstrap_report,
)
from aware_workspace_operator.pipeline.stages.scaffold import run_scaffold_stage
from aware_workspace_operator.pipeline.utils import resolve_repo_root


def run_workspace_bootstrap(
    *,
    options: WorkspaceBootstrapOptions,
    export_skill_pack_fn: SkillPackExporterProtocol | None,
) -> WorkspaceBootstrapOutcome:
    """Run deterministic workspace-bootstrap pipeline with staged execution."""

    repo_root = Path(options.repo_root).resolve()
    repo_root.mkdir(parents=True, exist_ok=True)

    preflight = run_preflight_stage(request=options, repo_root=repo_root)
    scaffold = run_scaffold_stage(
        request=options,
        preflight=preflight,
        repo_root=repo_root,
        export_skill_pack_fn=export_skill_pack_fn,
    )
    report = build_report(
        request=options,
        preflight=preflight,
        scaffold=scaffold,
        repo_root=repo_root.as_posix(),
    )

    return WorkspaceBootstrapOutcome(
        report=report,
        exit_code=2 if report.status == "failed" else 0,
    )


def print_workspace_bootstrap_result(*, payload: dict[str, object]) -> None:
    """Compatibility adapter for CLI callers that still pass dict payloads."""

    report = WorkspaceBootstrapReport.model_validate(payload)
    print_workspace_bootstrap_report(report=report)


__all__ = [
    "print_workspace_bootstrap_result",
    "resolve_repo_root",
    "run_workspace_bootstrap",
]
