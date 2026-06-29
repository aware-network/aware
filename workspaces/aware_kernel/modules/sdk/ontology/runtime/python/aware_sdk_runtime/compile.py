from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aware_sdk_runtime.manifest.spec import AwareSdkCompilationMode

from .builder import (
    SdkCompilePlan,
    SdkCompilePlanArtifact,
    build_sdk_compile_plan,
    emit_sdk_compile_plan_artifact,
)
from .workspace import SdkWorkspace, SdkWorkspaceSnapshot


@dataclass(frozen=True, slots=True)
class SdkCompileResult:
    snapshot: SdkWorkspaceSnapshot
    compile_plan: SdkCompilePlan | None = None
    compile_plan_artifact: SdkCompilePlanArtifact | None = None


def compile_sdk_workspace(
    *,
    toml_path: str | Path,
    repo_root: str | Path | None = None,
    emit_compile_plan: bool = False,
) -> SdkCompileResult:
    workspace = SdkWorkspace.from_toml(toml_path=toml_path, repo_root=repo_root)
    snapshot = workspace.build_snapshot()
    if snapshot.spec.build.compilation_mode != AwareSdkCompilationMode.sdk_ontology:
        return SdkCompileResult(snapshot=snapshot)

    package_name = (snapshot.spec.sdk.package_name or "").strip()
    if not package_name:
        raise ValueError("SDK package_name must be non-empty for ontology-mode compilation")

    compile_plan = build_sdk_compile_plan(snapshot=snapshot)
    compile_plan_artifact: SdkCompilePlanArtifact | None = None
    if emit_compile_plan:
        runtime_package_dir = (snapshot.repo_root / ".aware" / "sdk" / "runtime" / package_name).resolve()
        compile_plan_artifact = emit_sdk_compile_plan_artifact(
            plan=compile_plan,
            runtime_package_dir=runtime_package_dir,
            repo_root=snapshot.repo_root,
        )

    return SdkCompileResult(
        snapshot=snapshot,
        compile_plan=compile_plan,
        compile_plan_artifact=compile_plan_artifact,
    )


__all__ = [
    "SdkCompileResult",
    "compile_sdk_workspace",
]
