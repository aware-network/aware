from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib

from .builder import (
    AttentionCompilePlan,
    AttentionCompilePlanArtifact,
    build_attention_compile_plan_from_layout_ownership,
    build_attention_compile_plan_from_anchor,
    emit_attention_compile_plan_artifact,
)
from .parser import load_attention_layout_ownership_from_sources
from .workspace import AttentionWorkspace, AttentionWorkspaceSnapshot


@dataclass(frozen=True, slots=True)
class AttentionCompileResult:
    snapshot: AttentionWorkspaceSnapshot | None
    anchor_path: Path | None
    package_name: str
    source_files: tuple[str, ...]
    compile_plan: AttentionCompilePlan
    compile_plan_artifact: AttentionCompilePlanArtifact | None = None


def compile_attention_anchor_workspace(
    *,
    anchor_path: str | Path,
    repo_root: str | Path | None = None,
    package_name: str | None = None,
    emit_compile_plan: bool = False,
    frame_mode: str = "vertical",
) -> AttentionCompileResult:
    resolved_anchor_path = Path(anchor_path).resolve()
    if not resolved_anchor_path.is_file():
        raise FileNotFoundError(f"Attention anchor path does not exist: {resolved_anchor_path}")

    resolved_repo_root = (
        Path(repo_root).resolve()
        if repo_root is not None
        else _find_repo_root(start=resolved_anchor_path.parent)
    )
    resolved_package_name = (package_name or resolved_anchor_path.parents[1].name).strip()
    source_relpath = _render_relpath(path=resolved_anchor_path, repo_root=resolved_repo_root)

    anchor_payload = tomllib.loads(resolved_anchor_path.read_text(encoding="utf-8"))
    compile_plan = build_attention_compile_plan_from_anchor(
        anchor_payload=anchor_payload,
        package_name=resolved_package_name,
        source_files=(source_relpath,),
        frame_mode=frame_mode,
    )
    compile_plan_artifact: AttentionCompilePlanArtifact | None = None
    if emit_compile_plan:
        runtime_package_dir = (
            resolved_repo_root / ".aware" / "attention" / "runtime" / resolved_package_name
        ).resolve()
        compile_plan_artifact = emit_attention_compile_plan_artifact(
            plan=compile_plan,
            runtime_package_dir=runtime_package_dir,
            repo_root=resolved_repo_root,
        )

    return AttentionCompileResult(
        snapshot=None,
        anchor_path=resolved_anchor_path,
        package_name=resolved_package_name,
        source_files=(source_relpath,),
        compile_plan=compile_plan,
        compile_plan_artifact=compile_plan_artifact,
    )


def resolve_attention_runtime_package_dir(*, snapshot: AttentionWorkspaceSnapshot) -> Path:
    package_name = (snapshot.spec.attention.package_name or "").strip()
    if not package_name:
        raise ValueError("Attention package_name must be non-empty for runtime artifact persistence")
    return (snapshot.repo_root / ".aware" / "attention" / "runtime" / package_name).resolve()


def compile_attention_workspace(
    *,
    toml_path: str | Path,
    repo_root: str | Path | None = None,
    emit_compile_plan: bool = False,
    frame_mode: str | None = None,
) -> AttentionCompileResult:
    workspace = AttentionWorkspace.from_toml(toml_path=toml_path, repo_root=repo_root)
    snapshot = workspace.build_snapshot()
    resolved_frame_mode = (frame_mode or snapshot.spec.build.frame_mode).strip()
    source_files = tuple(
        _render_relpath(path=(snapshot.package_root / path), repo_root=snapshot.repo_root)
        for path in snapshot.source_files
    )
    ownership = load_attention_layout_ownership_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
    )
    if ownership.layouts:
        compile_plan = build_attention_compile_plan_from_layout_ownership(
            layout_ownership=ownership.layouts,
            package_name=snapshot.spec.attention.package_name,
            source_files=source_files,
            frame_mode=resolved_frame_mode,
        )
    else:
        if snapshot.anchor_path is None:
            raise ValueError(
                "Attention workspace must declare authored layout topology or a legacy anchor_path"
            )
        anchor_payload = tomllib.loads(snapshot.anchor_path.read_text(encoding="utf-8"))
        compile_plan = build_attention_compile_plan_from_anchor(
            anchor_payload=anchor_payload,
            package_name=snapshot.spec.attention.package_name,
            source_files=source_files,
            frame_mode=resolved_frame_mode,
        )
    compile_plan_artifact: AttentionCompilePlanArtifact | None = None
    if emit_compile_plan:
        runtime_package_dir = resolve_attention_runtime_package_dir(snapshot=snapshot)
        compile_plan_artifact = emit_attention_compile_plan_artifact(
            plan=compile_plan,
            runtime_package_dir=runtime_package_dir,
            repo_root=snapshot.repo_root,
        )

    return AttentionCompileResult(
        snapshot=snapshot,
        anchor_path=snapshot.anchor_path,
        package_name=snapshot.spec.attention.package_name,
        source_files=source_files,
        compile_plan=compile_plan,
        compile_plan_artifact=compile_plan_artifact,
    )


def _render_relpath(*, path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _find_repo_root(*, start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    while current.parent != current:
        if (current / "aware.environment.toml").exists():
            return current
        current = current.parent
    if (current / "aware.environment.toml").exists():
        return current
    return (start or Path.cwd()).resolve()


__all__ = [
    "AttentionCompileResult",
    "compile_attention_anchor_workspace",
    "compile_attention_workspace",
    "resolve_attention_runtime_package_dir",
]
