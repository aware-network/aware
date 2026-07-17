from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from aware_interface.manifest import AwareInterfaceCompilationMode
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

from .builder import (
    InterfaceCompilePlan,
    InterfaceCompilePlanArtifact,
    InterfaceConfigBundleArtifact,
    InterfaceDartPaneRegistrarBundleArtifact,
    InterfacePaneRenderSpecMaterializationArtifact,
    ProjectionIdentityTruth,
    ApiViewStateTruth,
    build_projection_identity_catalog_from_ocg,
    build_state_attribute_catalog_from_ocg,
    build_state_model_catalog_from_ocg,
    build_interface_compile_plan,
    build_interface_config_bundle,
    emit_interface_dart_pane_registrar_bundle_artifact,
    emit_interface_compile_plan_artifact,
    emit_interface_config_bundle_artifact,
    emit_interface_pane_render_spec_materialization_artifact,
)
from .workspace import InterfaceWorkspace, InterfaceWorkspaceSnapshot


@dataclass(frozen=True, slots=True)
class InterfaceCompileResult:
    snapshot: InterfaceWorkspaceSnapshot
    compile_plan: InterfaceCompilePlan | None = None
    compile_plan_artifact: InterfaceCompilePlanArtifact | None = None
    render_spec_materialization_artifact: InterfacePaneRenderSpecMaterializationArtifact | None = None
    config_bundle_artifact: InterfaceConfigBundleArtifact | None = None
    dart_registrar_bundle_artifact: InterfaceDartPaneRegistrarBundleArtifact | None = None


def resolve_interface_runtime_package_dir(
    *, snapshot: InterfaceWorkspaceSnapshot, artifact_root: Path | None = None
) -> Path:
    package_name = (snapshot.spec.interface.package_name or "").strip()
    if not package_name:
        raise ValueError("Interface package_name must be non-empty for runtime artifact persistence")
    resolved_artifact_root = artifact_root.resolve() if artifact_root is not None else snapshot.repo_root
    return (resolved_artifact_root / ".aware" / "interface" / "runtime" / package_name).resolve()


def resolve_interface_dart_package_dir(*, snapshot: InterfaceWorkspaceSnapshot) -> Path | None:
    dart_spec = snapshot.spec.dart
    if dart_spec is None:
        return None
    dart_package_dir = (snapshot.package_root / dart_spec.package_path).resolve()
    package_root = snapshot.package_root.resolve()
    if dart_package_dir != package_root and package_root not in dart_package_dir.parents:
        raise ValueError(
            "Interface dart.package_path resolved outside interface package root: "
            + f"base={package_root} candidate={dart_package_dir}"
        )
    return dart_package_dir


def compile_interface_workspace(
    *,
    toml_path: str | Path,
    repo_root: str | Path | None = None,
    emit_compile_plan: bool = False,
    emit_config_bundle: bool = False,
    projection_identity_ocg: ObjectConfigGraph | None = None,
    projection_identity_ocgs: Iterable[ObjectConfigGraph] | None = None,
    state_model_catalog: Mapping[str, UUID] | None = None,
    state_attribute_catalog: Mapping[str, Mapping[str, UUID]] | None = None,
    api_view_catalog: Mapping[str, ApiViewStateTruth] | None = None,
    artifact_root: str | Path | None = None,
) -> InterfaceCompileResult:
    workspace = InterfaceWorkspace.from_toml(toml_path=toml_path, repo_root=repo_root)
    snapshot = workspace.build_snapshot()
    if snapshot.spec.build.compilation_mode != AwareInterfaceCompilationMode.interface_ontology or (
        not emit_compile_plan and not emit_config_bundle
    ):
        return InterfaceCompileResult(snapshot=snapshot)

    compile_plan = build_interface_compile_plan(snapshot=snapshot)
    projection_identity_graphs = tuple(projection_identity_ocgs or ())
    projection_catalog: dict[str, ProjectionIdentityTruth] = {}
    for ocg in projection_identity_graphs:
        projection_catalog.update(build_projection_identity_catalog_from_ocg(ocg=ocg))
    if projection_identity_ocg is not None:
        projection_catalog.update(build_projection_identity_catalog_from_ocg(ocg=projection_identity_ocg))
    resolved_projection_catalog = projection_catalog or None
    merged_state_model_catalog = dict(state_model_catalog or {})
    for ocg in projection_identity_graphs:
        for key, value in build_state_model_catalog_from_ocg(ocg=ocg).items():
            merged_state_model_catalog.setdefault(key, value)
    if projection_identity_ocg is not None:
        for key, value in build_state_model_catalog_from_ocg(
            ocg=projection_identity_ocg,
        ).items():
            merged_state_model_catalog.setdefault(key, value)
    resolved_state_model_catalog = merged_state_model_catalog or None
    merged_state_attribute_catalog = dict(state_attribute_catalog or {})
    for ocg in projection_identity_graphs:
        for key, value in build_state_attribute_catalog_from_ocg(ocg=ocg).items():
            merged_state_attribute_catalog.setdefault(key, value)
    if projection_identity_ocg is not None:
        for key, value in build_state_attribute_catalog_from_ocg(
            ocg=projection_identity_ocg,
        ).items():
            merged_state_attribute_catalog.setdefault(key, value)
    resolved_state_attribute_catalog = merged_state_attribute_catalog or None
    resolved_artifact_root = Path(artifact_root).resolve() if artifact_root is not None else snapshot.repo_root
    runtime_package_dir = resolve_interface_runtime_package_dir(
        snapshot=snapshot,
        artifact_root=resolved_artifact_root,
    )
    dart_package_dir = resolve_interface_dart_package_dir(snapshot=snapshot)
    compile_plan_artifact = (
        emit_interface_compile_plan_artifact(
            plan=compile_plan,
            runtime_package_dir=runtime_package_dir,
            repo_root=resolved_artifact_root,
        )
        if emit_compile_plan
        else None
    )
    render_spec_materialization_artifact = emit_interface_pane_render_spec_materialization_artifact(
        snapshot=snapshot,
        plan=compile_plan,
        runtime_package_dir=runtime_package_dir,
        repo_root=resolved_artifact_root,
        projection_catalog=resolved_projection_catalog,
        state_model_catalog=resolved_state_model_catalog,
        state_attribute_catalog=resolved_state_attribute_catalog,
        api_view_catalog=api_view_catalog,
    )
    dart_registrar_bundle_artifact = (
        emit_interface_dart_pane_registrar_bundle_artifact(
            snapshot=snapshot,
            plan=compile_plan,
            dart_package_dir=dart_package_dir,
            repo_root=resolved_artifact_root,
            projection_catalog=resolved_projection_catalog,
            state_model_catalog=resolved_state_model_catalog,
            state_attribute_catalog=resolved_state_attribute_catalog,
            api_view_catalog=api_view_catalog,
            render_spec_materialization_path=render_spec_materialization_artifact.path,
        )
        if (emit_compile_plan or emit_config_bundle) and dart_package_dir is not None
        else None
    )
    config_bundle_artifact = None
    if emit_config_bundle:
        config_bundle = build_interface_config_bundle(
            snapshot=snapshot,
            plan=compile_plan,
            projection_catalog=resolved_projection_catalog,
            state_model_catalog=resolved_state_model_catalog,
            state_attribute_catalog=resolved_state_attribute_catalog,
            api_view_catalog=api_view_catalog,
        )
        config_bundle_artifact = emit_interface_config_bundle_artifact(
            bundle=config_bundle,
            config_bundle_path=snapshot.config_bundle_path,
            repo_root=resolved_artifact_root,
        )
    return InterfaceCompileResult(
        snapshot=snapshot,
        compile_plan=compile_plan,
        compile_plan_artifact=compile_plan_artifact,
        render_spec_materialization_artifact=render_spec_materialization_artifact,
        config_bundle_artifact=config_bundle_artifact,
        dart_registrar_bundle_artifact=dart_registrar_bundle_artifact,
    )


__all__ = [
    "InterfaceCompileResult",
    "compile_interface_workspace",
    "resolve_interface_dart_package_dir",
    "resolve_interface_runtime_package_dir",
]
