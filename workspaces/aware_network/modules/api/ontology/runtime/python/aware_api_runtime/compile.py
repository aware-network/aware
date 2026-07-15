from __future__ import annotations

import asyncio
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Literal
from uuid import NAMESPACE_URL, uuid5

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.runtime import (
    build_meta_graph_runtime_for_aware_package_manifests,
    find_meta_graph_projection_hash_by_name,
)
from aware_meta.runtime.graph_context import (
    resolve_meta_runtime_package_manifest_closure_for_package_names,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_utils.logging import logger

from aware_api_runtime.manifest.spec import (
    AwareApiCompilationMode,
    AwareApiTomlBuildSpec,
    AwareApiTomlPackageSpec,
    AwareApiTomlSpec,
    AwareApiTomlTargetsSpec,
)

from .ir import (
    APICompilePlan,
    APICompilePlanArtifact,
    APIRuntimeArtifacts,
    build_api_compile_plan,
    decode_api_compile_plan_payload,
)
from .packages.materialization import (
    ApiDtoPackageMaterializationResult,
    ApiPublicPackageMaterializationResult,
    ApiServiceProtocolMaterializationResult,
    materialize_api_dto_packages,
    materialize_api_public_package,
    materialize_api_service_protocol,
    refresh_api_public_package_from_runtime_artifacts,
    refresh_api_service_protocol_from_runtime_artifacts,
)
from .dependencies.runtime_resolution import (
    canonicalize_api_accessible_dependency_graphs,
    collect_api_dependency_class_config_ids_from_graphs,
    resolve_api_runtime_semantic_artifacts,
)
from .workspace import (
    APIWorkspace,
    APIWorkspaceSnapshot,
)

ApiDependencyGraphMode = Literal["meta_runtime"]
_API_COMPILE_META_RUNTIME_PACKAGE_NAMES = ("meta-ontology",)


@dataclass(frozen=True, slots=True)
class APICompileResult:
    snapshot: APIWorkspaceSnapshot
    compile_plan: APICompilePlan | None = None
    runtime_artifacts: APIRuntimeArtifacts | None = None
    public_package_materialization: ApiPublicPackageMaterializationResult | None = None
    service_protocol_materialization: ApiServiceProtocolMaterializationResult | None = (
        None
    )
    api_dto_package_materializations: tuple[
        ApiDtoPackageMaterializationResult, ...
    ] = ()
    dependency_graph_mode: str = "meta_runtime"
    accessible_dependency_graph_count: int = 0


def resolve_api_runtime_package_dir(*, snapshot: APIWorkspaceSnapshot) -> Path:
    package_name = (snapshot.spec.api.package_name or "").strip()
    if not package_name:
        raise ValueError(
            "API package_name must be non-empty for runtime artifact persistence"
        )
    return (snapshot.repo_root / ".aware" / "api" / "runtime" / package_name).resolve()


def emit_api_runtime_manifest(
    *,
    snapshot: APIWorkspaceSnapshot,
    compile_plan_artifact: APICompilePlanArtifact,
    runtime_package_dir: Path,
    source_api_toml_path: str | Path | None = None,
    public_package_root: Path | None = None,
    service_protocol_package_root: Path | None = None,
    dependency_graph_mode: str = "meta_runtime",
    accessible_dependency_graph_count: int = 0,
) -> Path:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = snapshot.repo_root.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)
    runtime_manifest_path = (runtime_package_dir / "api.manifest.json").resolve()
    runtime_manifest_relpath = runtime_manifest_path.relative_to(repo_root).as_posix()
    manifest_source_path = _resolve_runtime_manifest_api_toml_path(
        snapshot=snapshot,
        source_api_toml_path=source_api_toml_path,
    )

    payload: dict[str, object] = {
        "status": "ok",
        "compile_target": "api",
        "api_toml_path": str(manifest_source_path),
        "api_toml_relpath": manifest_source_path.relative_to(repo_root).as_posix(),
        "api_package_root_relpath": snapshot.package_root.resolve()
        .relative_to(repo_root)
        .as_posix(),
        "api_package_name": snapshot.spec.api.package_name,
        "api_fqn_prefix": snapshot.spec.api.fqn_prefix,
        "public_package_materialized": public_package_root is not None,
        "service_protocol_materialized": service_protocol_package_root is not None,
        "dependency_graph_mode": dependency_graph_mode,
        "accessible_dependency_graph_count": accessible_dependency_graph_count,
        "source_files": [path.as_posix() for path in snapshot.source_files],
        "runtime_artifact_relpath": runtime_manifest_relpath,
        "compile_plan_artifact_relpath": compile_plan_artifact.relpath,
        "compile_plan_artifact_hash": compile_plan_artifact.hash_sha256,
        "compile_plan_api_count": 0,
    }
    compile_plan_payload = json.loads(
        compile_plan_artifact.path.read_text(encoding="utf-8")
    )
    payload["compile_plan_api_count"] = len(
        compile_plan_payload.get("api_ownership", ())
    )

    if public_package_root is not None:
        payload["public_package_package_root_relpath"] = (
            public_package_root.resolve().relative_to(repo_root).as_posix()
        )
    if service_protocol_package_root is not None:
        payload["service_protocol_package_root_relpath"] = (
            service_protocol_package_root.resolve().relative_to(repo_root).as_posix()
        )

    runtime_manifest_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return runtime_manifest_path


def _resolve_runtime_manifest_api_toml_path(
    *,
    snapshot: APIWorkspaceSnapshot,
    source_api_toml_path: str | Path | None,
) -> Path:
    if source_api_toml_path is None:
        return snapshot.spec_path.resolve()
    raw_path = Path(source_api_toml_path)
    if raw_path.is_absolute():
        return raw_path.resolve()
    return (snapshot.repo_root / raw_path).resolve()


def compile_api_workspace(
    *,
    toml_path: str | Path,
    repo_root: str | Path | None = None,
    materialize_public_package: bool = False,
    materialize_service_protocol: bool = False,
    public_package_target_language: CodeLanguage = CodeLanguage.python,
    dependency_graph_mode: ApiDependencyGraphMode = "meta_runtime",
    accessible_graphs: Sequence[ObjectConfigGraph] | None = None,
    kernel_repo_root: str | Path | None = None,
    dependency_repo_roots: Sequence[str | Path] = (),
    execute_language_post_steps: bool = False,
    post_step_tool_env_by_tool_id: Mapping[str, Mapping[str, str]] | None = None,
    post_step_executable_overrides_by_tool_id: (
        Mapping[str, Mapping[str, str]] | None
    ) = None,
) -> APICompileResult:
    workspace = APIWorkspace.from_toml(toml_path=toml_path, repo_root=repo_root)
    snapshot = workspace.build_snapshot()
    resolved_dependency_graph_mode = _normalize_dependency_graph_mode(
        dependency_graph_mode
    )
    effective_dependency_graph_mode = (
        "semantic_contract"
        if accessible_graphs is not None
        else resolved_dependency_graph_mode
    )
    if (
        snapshot.spec.build.compilation_mode != AwareApiCompilationMode.api_ontology
        or (not materialize_public_package and not materialize_service_protocol)
    ):
        return APICompileResult(
            snapshot=snapshot,
            dependency_graph_mode=resolved_dependency_graph_mode,
        )

    package_name = (snapshot.spec.api.package_name or "").strip()
    if not package_name:
        raise ValueError(
            "API package_name must be non-empty for ontology-mode compilation"
        )
    if (
        materialize_service_protocol
        and public_package_target_language != CodeLanguage.python
    ):
        raise ValueError(
            "API service-protocol materialization requires public API package target language=python"
        )
    logger.info(
        "API compile dependency graph mode selected: package=%s mode=%s dependency_count=%d "
        "materialize_public_package=%s materialize_service_protocol=%s",
        package_name,
        effective_dependency_graph_mode,
        len(snapshot.spec.dependencies),
        materialize_public_package,
        materialize_service_protocol,
    )
    accessible_dependency_graphs: tuple[ObjectConfigGraph, ...] | None = None
    dependency_class_config_ids = None
    if accessible_graphs is not None:
        accessible_dependency_graphs = canonicalize_api_accessible_dependency_graphs(
            accessible_graphs=tuple(accessible_graphs)
        )
        dependency_class_config_ids = (
            collect_api_dependency_class_config_ids_from_graphs(
                accessible_graphs=accessible_dependency_graphs,
            )
        )
    else:
        accessible_dependency_graphs = canonicalize_api_accessible_dependency_graphs(
            accessible_graphs=compile_api_accessible_dependency_graphs_via_meta_runtime(
                snapshot=snapshot,
                kernel_repo_root=kernel_repo_root,
                dependency_repo_roots=dependency_repo_roots,
            )
        )
        dependency_class_config_ids = (
            collect_api_dependency_class_config_ids_from_graphs(
                accessible_graphs=accessible_dependency_graphs,
            )
        )

    compile_plan = build_api_compile_plan(
        snapshot=snapshot,
        dependency_class_config_ids=dependency_class_config_ids,
        dependency_repo_roots=dependency_repo_roots,
    )
    runtime_package_dir = resolve_api_runtime_package_dir(snapshot=snapshot)
    public_package_materialization: ApiPublicPackageMaterializationResult | None = None
    service_protocol_materialization: ApiServiceProtocolMaterializationResult | None = (
        None
    )
    api_dto_package_materializations: tuple[
        ApiDtoPackageMaterializationResult, ...
    ] = ()
    runtime_artifacts: APIRuntimeArtifacts | None = None

    if public_package_target_language == CodeLanguage.python and (
        materialize_service_protocol or materialize_public_package
    ):
        api_dto_package_materializations = materialize_api_dto_packages(
            snapshot=snapshot,
            runtime_package_dir=runtime_package_dir,
            repo_root=snapshot.repo_root,
            accessible_graphs=accessible_dependency_graphs,
            dependency_repo_roots=dependency_repo_roots,
        )

    if materialize_service_protocol:
        service_protocol_materialization = materialize_api_service_protocol(
            snapshot=snapshot,
            plan=compile_plan,
            runtime_package_dir=runtime_package_dir,
            repo_root=snapshot.repo_root,
            accessible_graphs=accessible_dependency_graphs,
            dependency_repo_roots=dependency_repo_roots,
        )
        public_package_materialization = (
            service_protocol_materialization.public_package_materialization
        )
        runtime_artifacts = service_protocol_materialization.runtime_artifacts
    elif materialize_public_package:
        public_package_materialization = materialize_api_public_package(
            snapshot=snapshot,
            plan=compile_plan,
            runtime_package_dir=runtime_package_dir,
            repo_root=snapshot.repo_root,
            public_package_target_language=public_package_target_language,
            accessible_graphs=accessible_dependency_graphs,
            dependency_repo_roots=dependency_repo_roots,
            execute_language_post_steps=execute_language_post_steps,
            post_step_tool_env_by_tool_id=post_step_tool_env_by_tool_id,
            post_step_executable_overrides_by_tool_id=(
                post_step_executable_overrides_by_tool_id
            ),
        )
        runtime_artifacts = public_package_materialization.runtime_artifacts

    if runtime_artifacts is not None:
        emit_api_runtime_manifest(
            snapshot=snapshot,
            compile_plan_artifact=runtime_artifacts.compile_plan,
            runtime_package_dir=runtime_package_dir,
            public_package_root=(
                public_package_materialization.render_job.target.package_root
                if public_package_materialization is not None
                else None
            ),
            service_protocol_package_root=(
                service_protocol_materialization.render_job.target.package_root
                if service_protocol_materialization is not None
                else None
            ),
            dependency_graph_mode=effective_dependency_graph_mode,
            accessible_dependency_graph_count=(
                len(accessible_dependency_graphs)
                if accessible_dependency_graphs is not None
                else 0
            ),
        )
        resolve_api_runtime_semantic_artifacts(
            snapshot=snapshot,
            register_class_configs=False,
            dependency_repo_roots=dependency_repo_roots,
        )

    return APICompileResult(
        snapshot=snapshot,
        compile_plan=compile_plan,
        runtime_artifacts=runtime_artifacts,
        public_package_materialization=public_package_materialization,
        service_protocol_materialization=service_protocol_materialization,
        api_dto_package_materializations=api_dto_package_materializations,
        dependency_graph_mode=effective_dependency_graph_mode,
        accessible_dependency_graph_count=(
            len(accessible_dependency_graphs)
            if accessible_dependency_graphs is not None
            else 0
        ),
    )


def compile_api_product_runtime_from_compile_plan_payload(
    *,
    compile_plan_payload: Mapping[str, object],
    repo_root: str | Path,
    compile_plan_path: str | Path | None = None,
    source_api_toml_path: str | Path | None = None,
    accessible_graphs: tuple[ObjectConfigGraph, ...] = (),
    dependency_repo_roots: Sequence[str | Path] = (),
) -> APICompileResult:
    plan = decode_api_compile_plan_payload(payload=compile_plan_payload)
    resolved_repo_root = Path(repo_root).resolve()
    runtime_package_dir = (
        resolved_repo_root / ".aware" / "api" / "runtime" / plan.package_name
    ).resolve()
    resolved_compile_plan_path = (
        Path(compile_plan_path).resolve()
        if compile_plan_path is not None
        else (runtime_package_dir / "api.compile_plan.json").resolve()
    )
    snapshot = _compile_plan_input_snapshot(
        plan=plan,
        repo_root=resolved_repo_root,
        runtime_package_dir=runtime_package_dir,
        compile_plan_path=resolved_compile_plan_path,
        source_api_toml_path=source_api_toml_path,
    )
    service_protocol_materialization = materialize_api_service_protocol(
        snapshot=snapshot,
        plan=plan,
        runtime_package_dir=runtime_package_dir,
        repo_root=resolved_repo_root,
        accessible_graphs=accessible_graphs,
        dependency_repo_roots=dependency_repo_roots,
    )
    public_package_materialization = (
        service_protocol_materialization.public_package_materialization
    )
    runtime_artifacts = service_protocol_materialization.runtime_artifacts
    api_dto_package_materializations = materialize_api_dto_packages(
        snapshot=snapshot,
        runtime_package_dir=runtime_package_dir,
        repo_root=resolved_repo_root,
        accessible_graphs=accessible_graphs,
        dependency_repo_roots=dependency_repo_roots,
    )
    emit_api_runtime_manifest(
        snapshot=snapshot,
        compile_plan_artifact=runtime_artifacts.compile_plan,
        runtime_package_dir=runtime_package_dir,
        source_api_toml_path=source_api_toml_path,
        public_package_root=public_package_materialization.render_job.target.package_root,
        service_protocol_package_root=(
            service_protocol_materialization.render_job.target.package_root
        ),
        dependency_graph_mode="semantic_contract",
        accessible_dependency_graph_count=len(accessible_graphs),
    )
    resolve_api_runtime_semantic_artifacts(
        snapshot=snapshot,
        register_class_configs=False,
        dependency_repo_roots=dependency_repo_roots,
    )
    return APICompileResult(
        snapshot=snapshot,
        compile_plan=plan,
        runtime_artifacts=runtime_artifacts,
        public_package_materialization=public_package_materialization,
        service_protocol_materialization=service_protocol_materialization,
        api_dto_package_materializations=api_dto_package_materializations,
        dependency_graph_mode="semantic_contract",
        accessible_dependency_graph_count=len(accessible_graphs),
    )


def _compile_plan_input_snapshot(
    *,
    plan: APICompilePlan,
    repo_root: Path,
    runtime_package_dir: Path,
    compile_plan_path: Path,
    source_api_toml_path: str | Path | None = None,
) -> APIWorkspaceSnapshot:
    if source_api_toml_path is not None:
        source_snapshot = APIWorkspace.from_toml(
            toml_path=source_api_toml_path,
            repo_root=repo_root,
        ).build_snapshot()
        source_package_name = (source_snapshot.spec.api.package_name or "").strip()
        source_fqn_prefix = (source_snapshot.spec.api.fqn_prefix or "").strip()
        if source_package_name and source_package_name != plan.package_name:
            raise ValueError(
                "API compile-plan source aware.api.toml package_name mismatch: "
                f"source={source_package_name!r} plan={plan.package_name!r}"
            )
        if source_fqn_prefix and source_fqn_prefix != plan.fqn_prefix:
            raise ValueError(
                "API compile-plan source aware.api.toml fqn_prefix mismatch: "
                f"source={source_fqn_prefix!r} plan={plan.fqn_prefix!r}"
            )
        return APIWorkspaceSnapshot(
            repo_root=source_snapshot.repo_root,
            package_root=source_snapshot.package_root,
            spec_path=source_snapshot.spec_path,
            spec=source_snapshot.spec,
            source_files=tuple(Path(source_file) for source_file in plan.source_files),
        )

    return APIWorkspaceSnapshot(
        repo_root=repo_root.resolve(),
        package_root=runtime_package_dir.resolve(),
        spec_path=compile_plan_path.resolve(),
        spec=AwareApiTomlSpec(
            aware_api=1,
            api=AwareApiTomlPackageSpec(
                package_name=plan.package_name,
                fqn_prefix=plan.fqn_prefix,
            ),
            build=AwareApiTomlBuildSpec(
                sources_dir=".",
                include_paths=["api.compile_plan.json"],
                exclude_paths=[],
                force_fresh_scan=False,
                compilation_mode=AwareApiCompilationMode.api_ontology,
            ),
            dependencies=[],
            targets=AwareApiTomlTargetsSpec(),
        ),
        source_files=tuple(Path(source_file) for source_file in plan.source_files),
    )


def compile_api_accessible_dependency_graphs_via_meta_runtime(
    *,
    snapshot: APIWorkspaceSnapshot,
    kernel_repo_root: str | Path | None = None,
    dependency_repo_roots: Iterable[str | Path] = (),
) -> tuple[ObjectConfigGraph, ...]:
    has_api_dto_exports = any(
        getattr(getattr(export, "kind", None), "value", getattr(export, "kind", None))
        == "api_dto"
        for export in snapshot.spec.semantic_package_exports
    )
    if not snapshot.spec.dependencies and not has_api_dto_exports:
        return ()
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(
            _compile_api_accessible_dependency_graphs_via_meta_runtime(
                snapshot=snapshot,
                kernel_repo_root=kernel_repo_root,
                dependency_repo_roots=dependency_repo_roots,
            )
        )
    raise RuntimeError(
        "API compile dependency_graph_mode='meta_runtime' requires a synchronous "
        "compile thread. Call compile_api_workspace from a worker thread or use "
        "runtime API materialization when already inside an event loop."
    )


async def _compile_api_accessible_dependency_graphs_via_meta_runtime(
    *,
    snapshot: APIWorkspaceSnapshot,
    kernel_repo_root: str | Path | None,
    dependency_repo_roots: Iterable[str | Path],
) -> tuple[ObjectConfigGraph, ...]:
    from .compile_materialization.service import (
        build_api_accessible_dependency_graphs_via_meta_runtime,
    )

    resolved_kernel_repo_root = (
        Path(kernel_repo_root).expanduser().resolve()
        if kernel_repo_root is not None
        else snapshot.repo_root.resolve()
    )
    meta_runtime_package_manifest_paths = (
        _api_compile_meta_runtime_package_manifest_paths(
            repo_root=resolved_kernel_repo_root,
        )
    )
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=meta_runtime_package_manifest_paths,
        workspace_root=resolved_kernel_repo_root,
        composite_name="API Compile Meta Runtime Context",
    )
    runtime_context = getattr(runtime, "context", None)
    if runtime_context is None:
        raise RuntimeError(
            "API compile Meta runtime did not expose Meta graph context."
        )
    index = runtime_context.index
    object_config_graph_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ObjectConfigGraph",
    )
    object_config_graph_package_projection_hash = (
        find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="ObjectConfigGraphPackage",
        )
    )
    branch_id = _stable_api_compile_dependency_parent_branch_id(snapshot=snapshot)
    return await build_api_accessible_dependency_graphs_via_meta_runtime(
        snapshot=snapshot,
        runtime=runtime,
        index=index,
        actor_id=None,
        branch_id=branch_id,
        target_projection_hash=object_config_graph_package_projection_hash,
        object_config_graph_projection_hash=object_config_graph_projection_hash,
        dependency_repo_roots=tuple(dependency_repo_roots),
    )


def _api_compile_meta_runtime_package_manifest_paths(
    *,
    repo_root: Path,
) -> tuple[Path, ...]:
    manifest_paths = resolve_meta_runtime_package_manifest_closure_for_package_names(
        repo_root=repo_root,
        package_names=_API_COMPILE_META_RUNTIME_PACKAGE_NAMES,
    )
    if manifest_paths:
        return manifest_paths
    package_names = ", ".join(_API_COMPILE_META_RUNTIME_PACKAGE_NAMES)
    raise RuntimeError(
        "API compile meta_runtime mode requires Meta package manifests for "
        f"{package_names}. Provide a kernel repo root with the Meta ontology "
        "package catalog; environment runtime manifests are not accepted."
    )


def _normalize_dependency_graph_mode(
    mode: ApiDependencyGraphMode | str,
) -> ApiDependencyGraphMode:
    normalized = str(mode).strip().replace("-", "_")
    if normalized in {"meta", "meta_runtime"}:
        return "meta_runtime"
    raise ValueError(
        "Unsupported API dependency graph mode: " f"{mode!r}. Expected 'meta_runtime'."
    )


def _stable_api_compile_dependency_parent_branch_id(
    *,
    snapshot: APIWorkspaceSnapshot,
):
    return uuid5(
        NAMESPACE_URL,
        "aware://api/compile/meta-dependency-parent:"
        f"{_api_compile_stable_token(snapshot=snapshot)}",
    )


def _api_compile_stable_token(*, snapshot: APIWorkspaceSnapshot) -> str:
    repo_root = snapshot.repo_root.resolve()
    try:
        api_toml_token = snapshot.spec_path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        api_toml_token = snapshot.spec_path.resolve().as_posix()
    package_name = (snapshot.spec.api.package_name or "").strip().casefold()
    fqn_prefix = (snapshot.spec.api.fqn_prefix or "").strip().casefold()
    return f"{repo_root.as_posix()}:{api_toml_token}:{package_name}:{fqn_prefix}"


def refresh_api_workspace_from_runtime_artifacts(
    *,
    toml_path: str | Path,
    repo_root: str | Path | None = None,
    refresh_public_package: bool = False,
    refresh_service_protocol: bool = False,
    public_package_target_language: CodeLanguage = CodeLanguage.python,
    public_package_candidate_paths: tuple[Path, ...] = (),
    service_protocol_candidate_paths: tuple[Path, ...] = (),
    public_package_render_input_class_refs: tuple[str, ...] | None = None,
    accessible_graphs: tuple[ObjectConfigGraph, ...] | None = None,
    dependency_repo_roots: Sequence[str | Path] = (),
    execute_language_post_steps: bool = False,
    post_step_tool_env_by_tool_id: Mapping[str, Mapping[str, str]] | None = None,
    post_step_executable_overrides_by_tool_id: (
        Mapping[str, Mapping[str, str]] | None
    ) = None,
) -> APICompileResult:
    workspace = APIWorkspace.from_toml(toml_path=toml_path, repo_root=repo_root)
    snapshot = workspace.build_snapshot()
    if not refresh_public_package and not refresh_service_protocol:
        return APICompileResult(snapshot=snapshot)

    runtime_package_dir = resolve_api_runtime_package_dir(snapshot=snapshot)
    if (
        refresh_service_protocol
        and public_package_target_language != CodeLanguage.python
    ):
        raise ValueError(
            "API service-protocol refresh requires public API package target language=python"
        )
    public_package_materialization: ApiPublicPackageMaterializationResult | None = None
    service_protocol_materialization: ApiServiceProtocolMaterializationResult | None = (
        None
    )
    runtime_artifacts: APIRuntimeArtifacts | None = None

    if refresh_service_protocol:
        service_protocol_materialization = refresh_api_service_protocol_from_runtime_artifacts(
            snapshot=snapshot,
            runtime_package_dir=runtime_package_dir,
            repo_root=snapshot.repo_root,
            public_package_candidate_paths=public_package_candidate_paths,
            service_protocol_candidate_paths=service_protocol_candidate_paths,
            public_package_render_input_class_refs=public_package_render_input_class_refs,
            accessible_graphs=accessible_graphs,
            dependency_repo_roots=dependency_repo_roots,
        )
        public_package_materialization = (
            service_protocol_materialization.public_package_materialization
        )
        runtime_artifacts = service_protocol_materialization.runtime_artifacts
    elif refresh_public_package:
        public_package_materialization = (
            refresh_api_public_package_from_runtime_artifacts(
                snapshot=snapshot,
                runtime_package_dir=runtime_package_dir,
                repo_root=snapshot.repo_root,
                public_package_target_language=public_package_target_language,
                candidate_paths=public_package_candidate_paths,
                render_input_class_refs=public_package_render_input_class_refs,
                accessible_graphs=accessible_graphs,
                dependency_repo_roots=dependency_repo_roots,
                execute_language_post_steps=execute_language_post_steps,
                post_step_tool_env_by_tool_id=post_step_tool_env_by_tool_id,
                post_step_executable_overrides_by_tool_id=(
                    post_step_executable_overrides_by_tool_id
                ),
            )
        )
        runtime_artifacts = public_package_materialization.runtime_artifacts

    if runtime_artifacts is not None and (
        refresh_service_protocol
        or public_package_target_language == CodeLanguage.python
    ):
        emit_api_runtime_manifest(
            snapshot=snapshot,
            compile_plan_artifact=runtime_artifacts.compile_plan,
            runtime_package_dir=runtime_package_dir,
            public_package_root=(
                public_package_materialization.render_job.target.package_root
                if public_package_materialization is not None
                else None
            ),
            service_protocol_package_root=(
                service_protocol_materialization.render_job.target.package_root
                if service_protocol_materialization is not None
                else None
            ),
        )

    return APICompileResult(
        snapshot=snapshot,
        runtime_artifacts=runtime_artifacts,
        public_package_materialization=public_package_materialization,
        service_protocol_materialization=service_protocol_materialization,
    )


__all__ = [
    "APICompileResult",
    "ApiDependencyGraphMode",
    "compile_api_accessible_dependency_graphs_via_meta_runtime",
    "compile_api_product_runtime_from_compile_plan_payload",
    "compile_api_workspace",
    "emit_api_runtime_manifest",
    "refresh_api_workspace_from_runtime_artifacts",
    "resolve_api_runtime_package_dir",
]
