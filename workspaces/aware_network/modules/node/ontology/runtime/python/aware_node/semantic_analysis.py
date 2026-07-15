from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aware_code.semantic_capability import (
    SemanticAnalysisCapabilityRequest,
    SemanticAnalysisCapabilityResult,
    SemanticCapabilityChangePreview,
    SemanticCapabilityDelta,
    SemanticCapabilityDependencyRequirement,
    SemanticCapabilityDiagnostic,
    SemanticCapabilityEvent,
)
from aware_code_ontology.code.code_plan import CodePackageDelta
from aware_node.manifest.spec import AwareNodeDependencyKind, AwareNodeTomlSpec

from .compile import NodeCompilePlan, compile_node_workspace
from .semantic_contract import NODE_PROVIDER_OWNER

_NODE_REQUIRED_MATERIALIZATIONS = (
    "node_compile_plan",
    "node_package_plan",
)


@dataclass(frozen=True, slots=True)
class NodeSemanticDiagnostic:
    severity: str
    code: str
    message: str
    source_path: str | None = None


@dataclass(frozen=True, slots=True)
class NodeSemanticChangePreview:
    changed_source_files: tuple[str, ...]
    affected_node_package_keys: tuple[str, ...]
    affected_node_config_keys: tuple[str, ...]
    affected_target_keys: tuple[str, ...]
    semantic_deltas: tuple[SemanticCapabilityDelta, ...]
    semantic_events: tuple[SemanticCapabilityEvent, ...]
    required_materializations: tuple[str, ...]
    required_semantic_dependencies: tuple[
        SemanticCapabilityDependencyRequirement, ...
    ] = ()


@dataclass(frozen=True, slots=True)
class NodeSemanticAnalysisResult:
    schema_version: int
    package_root: str
    manifest_path: str
    source_files: tuple[str, ...]
    compile_plan: NodeCompilePlan | None
    diagnostics: tuple[NodeSemanticDiagnostic, ...]
    change_preview: NodeSemanticChangePreview
    code_package_delta: CodePackageDelta | None = None


def analyze_node_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    manifest_path: Path | None = None,
    workspace_root: Path | None = None,
    code_package_delta: CodePackageDelta | None = None,
    fail_on_error: bool = True,
) -> NodeSemanticAnalysisResult:
    resolved_package_root = package_root.expanduser().resolve()
    resolved_manifest_path = _resolve_manifest_path(
        package_root=resolved_package_root,
        manifest_path=manifest_path,
    )
    resolved_workspace_root = (
        workspace_root.expanduser().resolve()
        if workspace_root is not None
        else resolved_package_root
    )
    try:
        compile_result = compile_node_workspace(
            toml_path=resolved_manifest_path,
            repo_root=resolved_workspace_root,
            emit_compile_plan=False,
        )
        if compile_result.compile_plan is None:
            raise ValueError(
                "Node semantic analysis requires [build].compilation_mode = "
                '"node_ontology" in aware.node.toml.'
            )
        compile_plan = compile_result.compile_plan
        manifest_spec = compile_result.snapshot.spec
        source_file_names = compile_plan.source_files
        diagnostics: tuple[NodeSemanticDiagnostic, ...] = ()
        preview = _build_change_preview(
            compile_plan=compile_plan,
            manifest_spec=manifest_spec,
            manifest_path=resolved_manifest_path,
            workspace_root=resolved_workspace_root,
            source_files=source_file_names,
            code_package_delta=code_package_delta,
        )
    except Exception as exc:
        if fail_on_error:
            raise
        compile_plan = None
        source_file_names = _source_file_names(source_files=source_files)
        diagnostics = (
            NodeSemanticDiagnostic(
                severity="error",
                code="aware_node.semantic_analysis.invalid_node_source",
                message=str(exc),
                source_path=_relative_to_optional(
                    path=resolved_manifest_path,
                    root=resolved_workspace_root,
                ),
            ),
        )
        preview = NodeSemanticChangePreview(
            changed_source_files=_changed_source_files(
                source_files=source_file_names,
                manifest_path=resolved_manifest_path,
                workspace_root=resolved_workspace_root,
                code_package_delta=code_package_delta,
            ),
            affected_node_package_keys=(),
            affected_node_config_keys=(),
            affected_target_keys=(),
            semantic_deltas=(),
            semantic_events=(),
            required_materializations=(),
            required_semantic_dependencies=(),
        )

    return NodeSemanticAnalysisResult(
        schema_version=1,
        package_root=resolved_package_root.as_posix(),
        manifest_path=resolved_manifest_path.as_posix(),
        source_files=source_file_names,
        compile_plan=compile_plan,
        diagnostics=diagnostics,
        change_preview=preview,
        code_package_delta=code_package_delta,
    )


def analyze_node_code_package_delta(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    code_package_delta: CodePackageDelta,
    manifest_path: Path | None = None,
    workspace_root: Path | None = None,
    fail_on_error: bool = False,
) -> NodeSemanticAnalysisResult:
    return analyze_node_sources(
        package_root=package_root,
        source_files=source_files,
        manifest_path=manifest_path,
        workspace_root=workspace_root,
        code_package_delta=code_package_delta,
        fail_on_error=fail_on_error,
    )


def analyze_node_semantic_capability(
    request: SemanticAnalysisCapabilityRequest,
) -> SemanticAnalysisCapabilityResult:
    analysis = analyze_node_sources(
        package_root=request.package_root,
        source_files=request.source_files,
        manifest_path=request.manifest_path,
        workspace_root=request.workspace_root,
        code_package_delta=request.code_package_delta,
        fail_on_error=False,
    )
    preview = analysis.change_preview
    return SemanticAnalysisCapabilityResult(
        provider_key="aware_node",
        semantic_owner=NODE_PROVIDER_OWNER,
        package_root=analysis.package_root,
        source_files=analysis.source_files,
        diagnostics=tuple(
            SemanticCapabilityDiagnostic(
                severity=diagnostic.severity,
                code=diagnostic.code,
                message=diagnostic.message,
                source_path=diagnostic.source_path,
            )
            for diagnostic in analysis.diagnostics
        ),
        change_preview=SemanticCapabilityChangePreview(
            changed_source_files=preview.changed_source_files,
            affected_semantic_keys=preview.affected_node_package_keys,
            required_materializations=preview.required_materializations,
            required_semantic_dependencies=preview.required_semantic_dependencies,
            semantic_deltas=preview.semantic_deltas,
            semantic_events=preview.semantic_events,
            metadata={
                "affected_node_config_keys": preview.affected_node_config_keys,
                "affected_target_keys": preview.affected_target_keys,
                "node_config_count": 1 if analysis.compile_plan is not None else 0,
                "environment_target_count": (
                    len(analysis.compile_plan.node_ownership.environment_targets)
                    if analysis.compile_plan is not None
                    else 0
                ),
                "ontology_target_count": (
                    len(analysis.compile_plan.node_ownership.ontology_targets)
                    if analysis.compile_plan is not None
                    else 0
                ),
                "service_target_count": (
                    len(analysis.compile_plan.node_ownership.service_targets)
                    if analysis.compile_plan is not None
                    else 0
                ),
                "interface_target_count": (
                    len(analysis.compile_plan.node_ownership.interface_targets)
                    if analysis.compile_plan is not None
                    else 0
                ),
            },
        ),
        payload=analysis,
        code_package_delta=request.code_package_delta,
    )


def _build_change_preview(
    *,
    compile_plan: NodeCompilePlan,
    manifest_spec: AwareNodeTomlSpec,
    manifest_path: Path,
    workspace_root: Path,
    source_files: tuple[str, ...],
    code_package_delta: CodePackageDelta | None,
) -> NodeSemanticChangePreview:
    changed_source_files = _changed_source_files(
        source_files=source_files,
        manifest_path=manifest_path,
        workspace_root=workspace_root,
        code_package_delta=code_package_delta,
    )
    semantic_deltas = _semantic_deltas_for_node(
        compile_plan=compile_plan,
        manifest_spec=manifest_spec,
        manifest_path=manifest_path,
        workspace_root=workspace_root,
    )
    semantic_events = _semantic_events_for_deltas(semantic_deltas=semantic_deltas)
    return NodeSemanticChangePreview(
        changed_source_files=changed_source_files,
        affected_node_package_keys=(f"node_package:{compile_plan.package_name}",),
        affected_node_config_keys=(f"node_config:{compile_plan.node_ownership.name}",),
        affected_target_keys=tuple(
            delta.semantic_key
            for delta in semantic_deltas
            if delta.subject_type
            in {
                "aware_node.NodeConfigEnvironmentTarget",
                "aware_node.NodeConfigOntologyTarget",
                "aware_node.NodeConfigServiceTarget",
                "aware_node.NodeConfigInterfaceTarget",
            }
        ),
        semantic_deltas=semantic_deltas,
        semantic_events=semantic_events,
        required_materializations=_NODE_REQUIRED_MATERIALIZATIONS,
        required_semantic_dependencies=_dependency_requirements(
            manifest_spec=manifest_spec,
            manifest_path=manifest_path,
            workspace_root=workspace_root,
        ),
    )


def _semantic_deltas_for_node(
    *,
    compile_plan: NodeCompilePlan,
    manifest_spec: AwareNodeTomlSpec,
    manifest_path: Path,
    workspace_root: Path,
) -> tuple[SemanticCapabilityDelta, ...]:
    node_package_key = f"node_package:{compile_plan.package_name}"
    node_config_key = f"node_config:{compile_plan.node_ownership.name}"
    manifest_ref = _relative_to(path=manifest_path, root=workspace_root)
    deltas: list[SemanticCapabilityDelta] = [
        SemanticCapabilityDelta(
            delta_key=f"aware_node.node_package.upsert:{node_package_key}",
            semantic_key=node_package_key,
            verb="upsert",
            subject_type="aware_node.NodePackage",
            source="aware_node.semantic_analysis",
            source_refs=(manifest_ref,),
            after_payload={
                "package_name": compile_plan.package_name,
                "fqn_prefix": compile_plan.fqn_prefix,
                "node_config_semantic_key": node_config_key,
                "version_number": manifest_spec.node.version_number,
                "title": manifest_spec.node.title,
                "description": manifest_spec.node.description,
                "dependency_count": len(manifest_spec.dependencies),
            },
        ),
        SemanticCapabilityDelta(
            delta_key=f"aware_node.node_config.upsert:{node_config_key}",
            semantic_key=node_config_key,
            verb="upsert",
            subject_type="aware_node.NodeConfig",
            source="aware_node.semantic_analysis",
            source_refs=(compile_plan.node_ownership.source_path,),
            after_payload={
                "name": compile_plan.node_ownership.name,
                "description": manifest_spec.node.description,
                "environment_target_count": len(
                    compile_plan.node_ownership.environment_targets
                ),
                "ontology_target_count": len(
                    compile_plan.node_ownership.ontology_targets
                ),
                "service_target_count": len(
                    compile_plan.node_ownership.service_targets
                ),
                "interface_target_count": len(
                    compile_plan.node_ownership.interface_targets
                ),
            },
        ),
    ]
    for target in compile_plan.node_ownership.environment_targets:
        semantic_key = f"{node_config_key}/environment:{target.environment_handle}"
        deltas.append(
            SemanticCapabilityDelta(
                delta_key=(
                    "aware_node.node_config_environment_target.upsert:"
                    f"{semantic_key}"
                ),
                semantic_key=semantic_key,
                verb="upsert",
                subject_type="aware_node.NodeConfigEnvironmentTarget",
                source="aware_node.semantic_analysis",
                source_refs=(target.source_path,),
                after_payload={
                    "node_config_semantic_key": node_config_key,
                    "environment_handle": target.environment_handle,
                    "profile_mounts": [
                        {
                            "package_name": mount.package_name,
                            "profile_key": mount.profile_key,
                            "mount_key": mount.mount_key,
                            "mode": mount.mode,
                            "position": mount.position,
                        }
                        for mount in target.profile_mounts
                    ],
                },
            )
        )
    for target in compile_plan.node_ownership.ontology_targets:
        semantic_key = f"{node_config_key}/ontology:{target.package_name}"
        deltas.append(
            SemanticCapabilityDelta(
                delta_key=(
                    "aware_node.node_config_ontology_target.upsert:" f"{semantic_key}"
                ),
                semantic_key=semantic_key,
                verb="upsert",
                subject_type="aware_node.NodeConfigOntologyTarget",
                source="aware_node.semantic_analysis",
                source_refs=(target.source_path,),
                after_payload={
                    "node_config_semantic_key": node_config_key,
                    "package_name": target.package_name,
                },
            )
        )
    for target in compile_plan.node_ownership.service_targets:
        semantic_key = f"{node_config_key}/service:{target.service_name}"
        deltas.append(
            SemanticCapabilityDelta(
                delta_key=(
                    "aware_node.node_config_service_target.upsert:" f"{semantic_key}"
                ),
                semantic_key=semantic_key,
                verb="upsert",
                subject_type="aware_node.NodeConfigServiceTarget",
                source="aware_node.semantic_analysis",
                source_refs=(target.source_path,),
                after_payload={
                    "node_config_semantic_key": node_config_key,
                    "service_name": target.service_name,
                },
            )
        )
    for target in compile_plan.node_ownership.interface_targets:
        semantic_key = f"{node_config_key}/interface:{target.interface_name}"
        deltas.append(
            SemanticCapabilityDelta(
                delta_key=(
                    "aware_node.node_config_interface_target.upsert:" f"{semantic_key}"
                ),
                semantic_key=semantic_key,
                verb="upsert",
                subject_type="aware_node.NodeConfigInterfaceTarget",
                source="aware_node.semantic_analysis",
                source_refs=(target.source_path,),
                after_payload={
                    "node_config_semantic_key": node_config_key,
                    "interface_name": target.interface_name,
                },
            )
        )
    return tuple(deltas)


def _semantic_events_for_deltas(
    *,
    semantic_deltas: tuple[SemanticCapabilityDelta, ...],
) -> tuple[SemanticCapabilityEvent, ...]:
    return tuple(
        SemanticCapabilityEvent(
            event_key=_event_key_for_delta(delta),
            semantic_key=delta.semantic_key,
            verb=delta.verb,
            subject_type=delta.subject_type,
            source=delta.source,
            source_refs=delta.source_refs,
            delta_keys=(delta.delta_key,),
            payload=dict(delta.after_payload or {}),
        )
        for delta in semantic_deltas
    )


def _event_key_for_delta(delta: SemanticCapabilityDelta) -> str:
    return delta.delta_key.replace(".upsert:", ".event.upsert:", 1)


def _dependency_requirements(
    *,
    manifest_spec: AwareNodeTomlSpec,
    manifest_path: Path,
    workspace_root: Path,
) -> tuple[SemanticCapabilityDependencyRequirement, ...]:
    source_ref = _relative_to(path=manifest_path, root=workspace_root)
    requirements: list[SemanticCapabilityDependencyRequirement] = []
    seen: set[str] = set()
    for dependency in manifest_spec.dependencies:
        package_name = dependency.package_name.strip()
        if not package_name:
            continue
        dependency_shape = _dependency_shape(dependency.kind)
        if dependency_shape is None:
            continue
        provider_key, manifest_kind, semantic_owner, family, semantic_kind = (
            dependency_shape
        )
        key = f"aware_node.{dependency.kind.value}:{package_name}"
        if key in seen:
            continue
        seen.add(key)
        requirements.append(
            SemanticCapabilityDependencyRequirement(
                dependency_key=key,
                provider_key=provider_key,
                package_name=package_name,
                required_state="materialized",
                dependency_kind=semantic_kind,
                semantic_owner=semantic_owner,
                manifest_kind=manifest_kind,
                package_selector={
                    "semantic_package_family": family,
                    "semantic_package_name": package_name,
                },
                reason=(
                    "NodePackage materialization requires hosted target "
                    "semantic packages before NodeConfig can be consumed by "
                    "deploy/runtime aggregation."
                ),
                source_refs=(source_ref,),
                metadata={
                    "version_number": dependency.version_number,
                    "node_dependency_kind": dependency.kind.value,
                },
            )
        )
    return tuple(requirements)


def _dependency_shape(
    kind: AwareNodeDependencyKind,
) -> tuple[str, str, str, str, str] | None:
    if kind is AwareNodeDependencyKind.environment_package:
        return (
            "aware_environment",
            "aware_environment_toml",
            "aware_environment.environment_config.provider",
            "environment",
            "environment_config_package",
        )
    if kind is AwareNodeDependencyKind.experience_package:
        return (
            "aware_experience",
            "aware_experience_toml",
            "aware_experience.provider",
            "experience",
            "experience_package",
        )
    if kind is AwareNodeDependencyKind.service_package:
        return (
            "aware_service",
            "aware_service_toml",
            "aware_service.provider",
            "service",
            "service_package",
        )
    if kind is AwareNodeDependencyKind.interface_package:
        return (
            "aware_interface",
            "aware_interface_toml",
            "aware_interface.provider",
            "interface",
            "interface_package",
        )
    if kind is AwareNodeDependencyKind.ontology_package:
        return (
            "aware_ontology",
            "aware_ontology_toml",
            "aware_ontology.provider",
            "ontology",
            "ontology_package",
        )
    return None


def _resolve_manifest_path(
    *,
    package_root: Path,
    manifest_path: Path | None,
) -> Path:
    if manifest_path is None:
        return (package_root / "aware.node.toml").resolve()
    resolved = manifest_path.expanduser().resolve()
    if resolved.is_absolute():
        return resolved
    return (package_root / resolved).resolve()


def _source_file_names(*, source_files: tuple[Path, ...]) -> tuple[str, ...]:
    return tuple(path.as_posix() for path in source_files)


def _changed_source_files(
    *,
    source_files: tuple[str, ...],
    manifest_path: Path,
    workspace_root: Path,
    code_package_delta: CodePackageDelta | None,
) -> tuple[str, ...]:
    if code_package_delta is None:
        return source_files
    manifest_ref = _relative_to_optional(path=manifest_path, root=workspace_root)
    source_file_set = set(source_files)
    selected: list[str] = []
    for delta_path in code_package_delta.paths:
        relative_path = delta_path.relative_path
        if not relative_path:
            continue
        if relative_path in source_file_set or relative_path == manifest_ref:
            selected.append(relative_path)
    return tuple(dict.fromkeys(selected)) or source_files


def _relative_to(*, path: Path, root: Path) -> str:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix() or "."
    except ValueError:
        return resolved_path.as_posix()


def _relative_to_optional(*, path: Path, root: Path) -> str | None:
    return _relative_to(path=path, root=root) if path.exists() else None


__all__ = [
    "NodeSemanticAnalysisResult",
    "NodeSemanticChangePreview",
    "NodeSemanticDiagnostic",
    "analyze_node_code_package_delta",
    "analyze_node_semantic_capability",
    "analyze_node_sources",
]
