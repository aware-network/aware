from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from aware_service_runtime.manifest.spec import AwareServiceCompilationMode
from aware_service_ontology.service.service_package import ServicePackage

from .builder import (
    ServiceActivationPlan,
    ServiceActivationPlanArtifact,
    ServiceCompilePlan,
    ServiceCompilePlanArtifact,
    build_service_activation_plan,
    build_service_compile_plan,
    emit_service_activation_plan_artifact,
    emit_service_compile_plan_artifact,
)
from .workspace import (
    ServiceWorkspace,
    ServiceWorkspaceSnapshot,
    build_service_workspace_snapshot_from_package,
)


@dataclass(frozen=True, slots=True)
class ServiceCompileResult:
    snapshot: ServiceWorkspaceSnapshot
    compile_plan: ServiceCompilePlan | None = None
    compile_plan_artifact: ServiceCompilePlanArtifact | None = None
    activation_plan: ServiceActivationPlan | None = None
    activation_plan_artifact: ServiceActivationPlanArtifact | None = None


def compile_service_workspace(
    *,
    toml_path: str | Path,
    repo_root: str | Path | None = None,
    emit_compile_plan: bool = False,
) -> ServiceCompileResult:
    workspace = ServiceWorkspace.from_toml(toml_path=toml_path, repo_root=repo_root)
    snapshot = workspace.build_snapshot()
    if (
        snapshot.spec.build.compilation_mode
        != AwareServiceCompilationMode.service_ontology
    ):
        return ServiceCompileResult(snapshot=snapshot)

    package_name = (snapshot.spec.service.package_name or "").strip()
    if not package_name:
        raise ValueError(
            "Service package_name must be non-empty for ontology-mode compilation"
        )

    compile_plan = build_service_compile_plan(snapshot=snapshot)
    compile_plan_artifact: ServiceCompilePlanArtifact | None = None
    activation_plan: ServiceActivationPlan | None = None
    activation_plan_artifact: ServiceActivationPlanArtifact | None = None

    if emit_compile_plan:
        runtime_package_dir = (
            snapshot.repo_root / ".aware" / "service" / "runtime" / package_name
        ).resolve()
        compile_plan_artifact = emit_service_compile_plan_artifact(
            plan=compile_plan,
            runtime_package_dir=runtime_package_dir,
            repo_root=snapshot.repo_root,
        )
        activation_plan = build_service_activation_plan(
            snapshot=snapshot,
            compile_plan_artifact=compile_plan_artifact,
        )
        activation_plan_artifact = _emit_activation_intent_unless_committed_lock_exists(
            activation_plan=activation_plan,
            runtime_package_dir=runtime_package_dir,
            repo_root=snapshot.repo_root,
        )

    return ServiceCompileResult(
        snapshot=snapshot,
        compile_plan=compile_plan,
        compile_plan_artifact=compile_plan_artifact,
        activation_plan=activation_plan,
        activation_plan_artifact=activation_plan_artifact,
    )


def compile_committed_service_package_workspace(
    *,
    service_package: ServicePackage,
    materialized_workspace_root: str | Path,
    emit_compile_plan: bool = False,
) -> ServiceCompileResult:
    snapshot = build_service_workspace_snapshot_from_package(
        service_package=service_package,
        materialized_workspace_root=materialized_workspace_root,
    )
    if (
        snapshot.spec.build.compilation_mode
        != AwareServiceCompilationMode.service_ontology
    ):
        return ServiceCompileResult(snapshot=snapshot)

    package_name = (snapshot.spec.service.package_name or "").strip()
    if not package_name:
        raise ValueError(
            "Service package_name must be non-empty for ontology-mode compilation"
        )

    compile_plan = build_service_compile_plan(snapshot=snapshot)
    compile_plan_artifact: ServiceCompilePlanArtifact | None = None
    activation_plan: ServiceActivationPlan | None = None
    activation_plan_artifact: ServiceActivationPlanArtifact | None = None

    if emit_compile_plan:
        runtime_package_dir = (
            snapshot.repo_root / ".aware" / "service" / "runtime" / package_name
        ).resolve()
        compile_plan_artifact = emit_service_compile_plan_artifact(
            plan=compile_plan,
            runtime_package_dir=runtime_package_dir,
            repo_root=snapshot.repo_root,
        )
        activation_plan = build_service_activation_plan(
            snapshot=snapshot,
            compile_plan_artifact=compile_plan_artifact,
        )
        activation_plan_artifact = _emit_activation_intent_unless_committed_lock_exists(
            activation_plan=activation_plan,
            runtime_package_dir=runtime_package_dir,
            repo_root=snapshot.repo_root,
        )

    return ServiceCompileResult(
        snapshot=snapshot,
        compile_plan=compile_plan,
        compile_plan_artifact=compile_plan_artifact,
        activation_plan=activation_plan,
        activation_plan_artifact=activation_plan_artifact,
    )


def _emit_activation_intent_unless_committed_lock_exists(
    *,
    activation_plan: ServiceActivationPlan,
    runtime_package_dir: Path,
    repo_root: Path,
) -> ServiceActivationPlanArtifact:
    artifact_path = (runtime_package_dir / "service.activation_plan.json").resolve()
    if not artifact_path.is_file():
        return emit_service_activation_plan_artifact(
            plan=activation_plan,
            runtime_package_dir=runtime_package_dir,
            repo_root=repo_root,
        )
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return ServiceActivationPlanArtifact(
        path=artifact_path,
        relpath=artifact_path.relative_to(repo_root.resolve()).as_posix(),
        hash_sha256=sha256(canonical).hexdigest(),
    )


__all__ = [
    "ServiceCompileResult",
    "compile_committed_service_package_workspace",
    "compile_service_workspace",
]
