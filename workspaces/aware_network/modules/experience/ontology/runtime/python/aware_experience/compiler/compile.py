from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aware_experience.compiler.workspace import (
    ExperienceWorkspace,
    ExperienceWorkspaceSnapshot,
)


@dataclass(frozen=True, slots=True)
class ExperienceCompileResult:
    snapshot: ExperienceWorkspaceSnapshot


def compile_experience_workspace(
    *,
    toml_path: str | Path,
    repo_root: str | Path | None = None,
) -> ExperienceCompileResult:
    workspace = ExperienceWorkspace.from_toml(toml_path=toml_path, repo_root=repo_root)
    snapshot = workspace.build_snapshot()

    return ExperienceCompileResult(snapshot=snapshot)


__all__ = [
    "ExperienceCompileResult",
    "compile_experience_workspace",
]
