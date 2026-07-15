from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from aware_node.manifest.spec import AwareNodeCompilationMode

from .compiler import NodeOwnership, load_node_ownership_from_sources
from .workspace import NodeWorkspace, NodeWorkspaceSnapshot


@dataclass(frozen=True, slots=True)
class NodeCompilePlan:
    schema_version: int
    package_name: str
    fqn_prefix: str
    source_files: tuple[str, ...]
    node_ownership: NodeOwnership


@dataclass(frozen=True, slots=True)
class NodeCompilePlanArtifact:
    path: Path
    relpath: str
    hash_sha256: str


@dataclass(frozen=True, slots=True)
class NodeCompileResult:
    snapshot: NodeWorkspaceSnapshot
    compile_plan: NodeCompilePlan | None = None
    compile_plan_artifact: NodeCompilePlanArtifact | None = None


def resolve_node_runtime_package_dir(*, snapshot: NodeWorkspaceSnapshot) -> Path:
    package_name = (snapshot.spec.node.package_name or "").strip()
    if not package_name:
        raise ValueError(
            "Node package_name must be non-empty for runtime artifact persistence"
        )
    return (snapshot.repo_root / ".aware" / "node" / "runtime" / package_name).resolve()


def build_node_compile_plan(*, snapshot: NodeWorkspaceSnapshot) -> NodeCompilePlan:
    package_name = (snapshot.spec.node.package_name or "").strip()
    if not package_name:
        raise ValueError(
            "Node package_name must be non-empty for ontology-mode compilation"
        )
    node_ownership = load_node_ownership_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
    )
    return NodeCompilePlan(
        schema_version=3,
        package_name=package_name,
        fqn_prefix=(snapshot.spec.node.fqn_prefix or "").strip(),
        source_files=tuple(path.as_posix() for path in snapshot.source_files),
        node_ownership=node_ownership,
    )


def emit_node_compile_plan_artifact(
    *,
    plan: NodeCompilePlan,
    runtime_package_dir: Path,
    repo_root: Path,
) -> NodeCompilePlanArtifact:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)

    payload = _encode_plan(plan=plan)
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = sha256(canonical).hexdigest()

    artifact_path = (runtime_package_dir / "node.compile_plan.json").resolve()
    _ = artifact_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    relpath = artifact_path.relative_to(repo_root).as_posix()
    return NodeCompilePlanArtifact(
        path=artifact_path,
        relpath=relpath,
        hash_sha256=digest,
    )


def compile_node_workspace(
    *,
    toml_path: str | Path,
    repo_root: str | Path | None = None,
    emit_compile_plan: bool = False,
) -> NodeCompileResult:
    workspace = NodeWorkspace.from_toml(toml_path=toml_path, repo_root=repo_root)
    snapshot = workspace.build_snapshot()
    if snapshot.spec.build.compilation_mode != AwareNodeCompilationMode.node_ontology:
        return NodeCompileResult(snapshot=snapshot)

    compile_plan = build_node_compile_plan(snapshot=snapshot)
    compile_plan_artifact: NodeCompilePlanArtifact | None = None
    if emit_compile_plan:
        runtime_package_dir = resolve_node_runtime_package_dir(snapshot=snapshot)
        compile_plan_artifact = emit_node_compile_plan_artifact(
            plan=compile_plan,
            runtime_package_dir=runtime_package_dir,
            repo_root=snapshot.repo_root,
        )

    return NodeCompileResult(
        snapshot=snapshot,
        compile_plan=compile_plan,
        compile_plan_artifact=compile_plan_artifact,
    )


def _encode_plan(*, plan: NodeCompilePlan) -> dict[str, object]:
    return {
        "schema_version": plan.schema_version,
        "package_name": plan.package_name,
        "fqn_prefix": plan.fqn_prefix,
        "source_files": list(plan.source_files),
        "node_ownership": {
            "name": plan.node_ownership.name,
            "source_path": plan.node_ownership.source_path,
            "included_node_packages": [
                {
                    "included_package_name": include.included_package_name,
                    "include_key": include.include_key,
                    "source_path": include.source_path,
                }
                for include in plan.node_ownership.included_node_packages
            ],
            "environment_targets": [
                {
                    "environment_handle": target.environment_handle,
                    "profile_mounts": [
                        {
                            "profile_key": mount.profile_key,
                            "package_name": mount.package_name,
                            "mount_key": mount.mount_key,
                            "mode": mount.mode,
                            "position": mount.position,
                            "source_path": mount.source_path,
                        }
                        for mount in target.profile_mounts
                    ],
                    "source_path": target.source_path,
                }
                for target in plan.node_ownership.environment_targets
            ],
            "ontology_targets": [
                {
                    "package_name": target.package_name,
                    "source_path": target.source_path,
                }
                for target in plan.node_ownership.ontology_targets
            ],
            "service_targets": [
                {
                    "service_name": target.service_name,
                    "source_path": target.source_path,
                    "code_packages": [
                        {
                            "slot_key": package.slot_key,
                            "package_name": package.package_name,
                            "language": package.language,
                            "source_path": package.source_path,
                        }
                        for package in target.code_packages
                    ],
                }
                for target in plan.node_ownership.service_targets
            ],
            "interface_targets": [
                {
                    "interface_name": target.interface_name,
                    "source_path": target.source_path,
                }
                for target in plan.node_ownership.interface_targets
            ],
        },
    }


__all__ = [
    "NodeCompilePlan",
    "NodeCompilePlanArtifact",
    "NodeCompileResult",
    "build_node_compile_plan",
    "compile_node_workspace",
    "emit_node_compile_plan_artifact",
    "resolve_node_runtime_package_dir",
]
