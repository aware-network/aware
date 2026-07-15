from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aware_skill.manifest import AwareSkillCompilationMode

from .builder import (
    SkillCompilePlan,
    SkillCompilePlanArtifact,
    build_skill_compile_plan,
    emit_skill_compile_plan_artifact,
)
from .workspace import SkillWorkspace, SkillWorkspaceSnapshot


@dataclass(frozen=True, slots=True)
class SkillCompileResult:
    snapshot: SkillWorkspaceSnapshot
    compile_plan: SkillCompilePlan | None = None
    compile_plan_artifact: SkillCompilePlanArtifact | None = None


def compile_skill_workspace(
    *,
    toml_path: str | Path,
    repo_root: str | Path | None = None,
    emit_compile_plan: bool = False,
) -> SkillCompileResult:
    workspace = SkillWorkspace.from_toml(toml_path=toml_path, repo_root=repo_root)
    snapshot = workspace.build_snapshot()
    if snapshot.spec.build.compilation_mode != AwareSkillCompilationMode.skill_ontology:
        return SkillCompileResult(snapshot=snapshot)

    package_name = (snapshot.spec.skill.package_name or "").strip()
    if not package_name:
        raise ValueError("Skill package_name must be non-empty for ontology-mode compilation")

    compile_plan = build_skill_compile_plan(snapshot=snapshot)
    compile_plan_artifact: SkillCompilePlanArtifact | None = None
    if emit_compile_plan:
        runtime_package_dir = (snapshot.repo_root / ".aware" / "skill" / "runtime" / package_name).resolve()
        compile_plan_artifact = emit_skill_compile_plan_artifact(
            plan=compile_plan,
            runtime_package_dir=runtime_package_dir,
            repo_root=snapshot.repo_root,
        )

    return SkillCompileResult(
        snapshot=snapshot,
        compile_plan=compile_plan,
        compile_plan_artifact=compile_plan_artifact,
    )


__all__ = [
    "SkillCompileResult",
    "compile_skill_workspace",
]
