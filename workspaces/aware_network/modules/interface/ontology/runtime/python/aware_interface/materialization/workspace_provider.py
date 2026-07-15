from __future__ import annotations

from collections.abc import Mapping
from fnmatch import fnmatch
from hashlib import sha256
from pathlib import Path
from typing import cast
from uuid import UUID

from aware_code.semantic_materialization import (
    SemanticPackageMaterializationBundle,
    SemanticPackageMaterializationRequest,
    SemanticPackageMaterializationResult,
)
from aware_interface.materialization.currentness_replay import (
    resolve_currentness_replay as resolve_currentness_replay,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_interface.builder import (
    ApiViewActionTruth,
    ApiViewStateTruth,
    build_state_attribute_catalog_from_ocg,
    build_state_model_catalog_from_ocg,
)
from aware_interface.manifest import (
    AwarePaneDependencyKind,
    AwareAppSourceSpec,
    load_aware_app_source_specs,
    load_aware_pane_toml_spec,
    load_aware_app_toml_spec,
    load_aware_render_component_toml_spec,
)
from aware_interface.manifest.app_launch_selection import (
    AwareAppCommittedScreenEvidence,
    AwareAppLaunchDescriptor,
    AwareAppPackageLaunchEvidence,
    build_aware_app_launch_selection_payload,
    render_aware_app_launch_descriptor_json,
    render_aware_app_launch_manifest_dart,
)
from aware_interface.manifest.app_spec import (
    AwareAppTomlInterfaceSpec,
    AwareAppTomlPlatformSpec,
    AwareAppTomlSpec,
)
from aware_interface.materialization import (
    InterfacePackageMaterializationResult,
    materialize_interface_package_from_manifest,
)
from aware_interface.materialization.app_package import (
    AppExperiencePackageReference,
    materialize_app_package_snapshot,
)
from aware_interface_ontology.stable_ids import (
    stable_app_package_id,
    stable_app_package_interface_package_id,
    stable_interface_package_id,
    stable_pane_package_id,
    stable_render_component_package_id,
)

_INTERFACE_FULL_REBUILD_FALLBACK_REASON = (
    "Interface provider has not implemented delta materialization yet; " "replayed the full Interface package manifest."
)
_PANE_PACKAGE_FALLBACK_REASON = (
    "Pane package provider currently emits stable package evidence only; "
    "delta ontology materialization is not implemented yet."
)
_RENDER_COMPONENT_PACKAGE_FALLBACK_REASON = (
    "Render component package provider currently emits stable package evidence only; "
    "delta ontology materialization is not implemented yet."
)
_APP_PACKAGE_FALLBACK_REASON = (
    "Interface app provider replays the full committed AppConfig/AppPackage "
    "snapshot; delta materialization is not implemented yet."
)
_WORKSPACE_EXPERIENCE_PACKAGE_REFERENCES_CONTEXT_KEY = "workspace_experience_package_references"
_LINUX_FLUTTER_TOOLCHAIN_REQUIREMENTS = (
    "flutter",
    "cmake>=3.13",
    "pkg-config",
    "gtk+-3.0",
)
_LINUX_PLATFORM_REQUIRED_FILES = (
    "CMakeLists.txt",
    "flutter/CMakeLists.txt",
    "flutter/generated_plugin_registrant.cc",
    "flutter/generated_plugin_registrant.h",
    "flutter/generated_plugins.cmake",
    "runner/CMakeLists.txt",
    "runner/main.cc",
    "runner/my_application.cc",
    "runner/my_application.h",
)


class AwareAppPlatformMaterializationError(RuntimeError):
    """Raised when an aware.app.toml platform runner is not materialization-ready."""


class AwareAppSourceMaterializationError(RuntimeError):
    """Raised when an aware.app.toml source plan cannot produce one AppConfig."""


async def materialize(
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    workspace_manifest_kind = str(request.context.get("workspace_manifest_kind") or "").strip()
    if workspace_manifest_kind == "pane":
        return _materialize_pane_package(request)
    if workspace_manifest_kind == "render_component":
        return _materialize_render_component_package(request)
    if workspace_manifest_kind == "app":
        return await _materialize_app_package(request)
    return await _materialize_interface_package(request)


def _materialize_pane_package(
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    spec = load_aware_pane_toml_spec(toml_path=request.manifest_path)
    metadata = request.context.get("semantic_package_metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    package_name = (spec.pane.package_name or "").strip()
    if not package_name:
        package_name = str(request.context.get("semantic_package_name") or "").strip()
    if not package_name:
        package_name = request.manifest_path.parent.name
    pane_package_id = stable_pane_package_id(name=package_name)
    experience_dependencies = tuple(
        {
            "package_name": dependency.package_name,
            "version_number": dependency.version_number,
            "kind": dependency.kind.value,
            "description": dependency.description,
        }
        for dependency in spec.dependencies
        if dependency.kind == AwarePaneDependencyKind.experience_package
    )
    return SemanticPackageMaterializationResult(
        details={
            "pane_toml_path": request.manifest_path.as_posix(),
            "pane_name": spec.pane.pane_name or _string_or_none(metadata.get("pane_name")) or package_name,
            "pane_package_name": package_name,
            "pane_package_id": str(pane_package_id),
            "experience_package_dependencies": experience_dependencies,
            "source_code_package_id": _string_or_none(request.context.get("source_code_package_id")),
        },
        bundle_packages=(
            SemanticPackageMaterializationBundle(
                package_key=package_name,
                manifest_toml_path=request.manifest_path,
                semantic_package_id=pane_package_id,
                semantic_root_id=pane_package_id,
                source_code_package_id=_uuid_or_none(request.context.get("source_code_package_id")),
            ),
        ),
        mode="full_rebuild",
        affected_semantic_keys=_semantic_keys_from_request(request),
        applied_semantic_keys=_semantic_keys_from_request(request),
        fallback_reason=_PANE_PACKAGE_FALLBACK_REASON,
    )


def _materialize_render_component_package(
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    spec = load_aware_render_component_toml_spec(toml_path=request.manifest_path)
    package_name = (spec.render_component.package_name or "").strip()
    if not package_name:
        package_name = str(request.context.get("semantic_package_name") or "").strip()
    if not package_name:
        package_name = request.manifest_path.parent.name
    render_component_package_id = stable_render_component_package_id(name=package_name)
    return SemanticPackageMaterializationResult(
        details={
            "render_component_toml_path": request.manifest_path.as_posix(),
            "render_component_package_name": package_name,
            "render_component_package_id": str(render_component_package_id),
            "render_component_fqn_prefix": spec.render_component.fqn_prefix,
            "source_code_package_id": _string_or_none(request.context.get("source_code_package_id")),
        },
        bundle_packages=(
            SemanticPackageMaterializationBundle(
                package_key=package_name,
                manifest_toml_path=request.manifest_path,
                semantic_package_id=render_component_package_id,
                semantic_root_id=render_component_package_id,
                source_code_package_id=_uuid_or_none(request.context.get("source_code_package_id")),
            ),
        ),
        mode="full_rebuild",
        affected_semantic_keys=_semantic_keys_from_request(request),
        applied_semantic_keys=_semantic_keys_from_request(request),
        fallback_reason=_RENDER_COMPONENT_PACKAGE_FALLBACK_REASON,
    )


async def _materialize_app_package(
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    spec = load_aware_app_toml_spec(toml_path=request.manifest_path)
    package_name = (spec.app.package_name or "").strip()
    if not package_name:
        package_name = str(request.context.get("semantic_package_name") or "").strip()
    if not package_name:
        package_name = request.manifest_path.parent.name
    source_code_package_id = _uuid_or_none(request.context.get("source_code_package_id"))
    app_package_id = stable_app_package_id(name=package_name)
    app_sources = _load_app_sources_for_manifest(
        manifest_path=request.manifest_path,
        spec=spec,
    )
    app_config = _single_app_source_for_package(
        package_name=package_name,
        app_sources=app_sources,
    )
    platform_readiness = _materialize_app_platforms(
        request=request,
        spec=spec,
    )
    materialized = await materialize_app_package_snapshot(
        index=request.index,
        actor_id=request.actor_id,
        branch_id=request.branch_id,
        workspace_root=request.workspace_root,
        manifest_path=request.manifest_path,
        spec=spec,
        app_source=app_config,
        source_code_package_id=source_code_package_id,
        experience_package_references=(_app_experience_package_references(request=request)),
    )
    app_config_snapshot = materialized.app_config_snapshot
    app_package_snapshot = materialized.app_package_snapshot
    app_package_id = app_package_snapshot.app_package.id
    app_config_id = app_config_snapshot.app_config.id
    launch_descriptor = AwareAppLaunchDescriptor(
        app_id=spec.app.app_name,
        display_name=spec.app.title or spec.app.app_name,
        app_package=AwareAppPackageLaunchEvidence(
            package_name=package_name,
            app_package_id=app_package_id,
            branch_id=request.branch_id,
            object_instance_graph_commit_id=(app_package_snapshot.object_instance_graph_commit_id),
        ),
        default_screen_key=spec.control.default_screen,
        screens=tuple(
            AwareAppCommittedScreenEvidence(
                app_config_screen_config_id=screen.id,
                screen_key=screen.screen_key,
                projection_experience_id=screen.projection_experience_id,
                projection_experience_layout_graph_binding_id=(screen.projection_experience_layout_graph_binding_id),
            )
            for screen in app_config_snapshot.screen_configs
        ),
    )
    generated_manifest_path, generated_descriptor_path = _write_app_launch_artifacts(
        request=request,
        spec=spec,
        descriptor=launch_descriptor,
    )
    enabled_platforms = tuple(platform.target for platform in spec.platforms if platform.enabled)
    launch_selection = build_aware_app_launch_selection_payload(spec=spec)
    interface_package_targets = _app_interface_package_targets(
        spec=spec,
        app_package_id=app_package_id,
    )
    experience_package_targets = tuple(
        {
            "app_package_experience_package_id": str(edge.id),
            "experience_package_id": str(edge.experience_package_id),
            "role": edge.role,
            "description": edge.description,
            "experience_package_object_instance_graph_commit_id": str(
                edge.experience_package_object_instance_graph_commit_id
            ),
            "resolution_status": "committed",
        }
        for edge in app_package_snapshot.experience_packages
    )
    app_config_details = (
        {
            "app_config_id": str(app_config_id),
            "name": app_config_snapshot.app_config.name,
            "title": app_config_snapshot.app_config.title,
            "description": app_config_snapshot.app_config.description,
            "source_path": app_config.source_path,
            "commit_id": str(app_config_snapshot.commit_id),
            "head_commit_id": str(app_config_snapshot.head_commit_id),
            "object_instance_graph_commit_id": str(app_config_snapshot.object_instance_graph_commit_id),
            "screen_configs": tuple(
                {
                    "app_config_screen_config_id": str(screen.id),
                    "screen_key": screen.screen_key,
                    "projection_experience_id": str(screen.projection_experience_id),
                    "projection_experience_layout_graph_binding_id": str(
                        screen.projection_experience_layout_graph_binding_id
                    ),
                    "resolution_status": "committed",
                }
                for screen in app_config_snapshot.screen_configs
            ),
        },
    )
    return SemanticPackageMaterializationResult(
        details={
            "app_toml_path": request.manifest_path.as_posix(),
            "app_package_name": package_name,
            "app_package_id": str(app_package_id),
            "semantic_package_kind": "app_package",
            "semantic_projection_name": "AppPackage",
            "semantic_root_kind": "app_package",
            "app_package": {
                "app_package_id": str(app_package_id),
                "package_name": package_name,
                "name": package_name,
                "semantic_kind": "app_package",
                "semantic_projection_name": "AppPackage",
                "semantic_root_kind": "app_package",
                "app_config_id": str(app_config_id),
                "app_config_object_instance_graph_commit_id": str(app_config_snapshot.object_instance_graph_commit_id),
                "aware_app_version": spec.aware_app,
                "version_number": spec.app.version_number,
                "title": spec.app.title,
                "description": spec.app.description,
                "manifest_relative_path": _relative_path(
                    path=request.manifest_path,
                    root=_module_root_for_manifest(request.manifest_path),
                ),
            },
            "app_name": spec.app.app_name,
            "dart_package_name": spec.dart.package_name,
            "dart_package_path": spec.dart.package_path,
            "dart_entrypoint": spec.dart.entrypoint,
            "factory_package_name": spec.factory.package_name,
            "factory_package_path": spec.factory.package_path,
            "build": {
                "sources_dir": spec.build.sources_dir,
                "include_paths": spec.build.include_paths,
                "exclude_paths": spec.build.exclude_paths,
            },
            "app_sources": tuple(
                {
                    "name": app.name,
                    "title": app.title,
                    "description": app.description,
                    "source_path": app.source_path,
                    "screens": tuple(
                        {
                            "screen_key": screen.screen_key,
                            "projection_experience": screen.projection_experience,
                            "projection_experience_layout": screen.projection_experience_layout,
                            "source_path": screen.source_path,
                        }
                        for screen in app.screens
                    ),
                }
                for app in app_sources
            ),
            "app_configs": app_config_details,
            "app_config_commit_id": str(app_config_snapshot.commit_id),
            "app_config_head_commit_id": str(app_config_snapshot.head_commit_id),
            "app_config_object_instance_graph_commit_id": str(app_config_snapshot.object_instance_graph_commit_id),
            "app_package_commit_id": str(app_package_snapshot.commit_id),
            "app_package_head_commit_id": str(app_package_snapshot.head_commit_id),
            "app_package_object_instance_graph_commit_id": str(app_package_snapshot.object_instance_graph_commit_id),
            "generated_launch_manifest_path": generated_manifest_path.as_posix(),
            "generated_launch_descriptor_path": generated_descriptor_path.as_posix(),
            "launch_descriptor": launch_descriptor.to_payload(),
            "launch_selection": launch_selection,
            "platforms": enabled_platforms,
            "platform_runners": tuple(
                {
                    "target": platform.target,
                    "runner_path": platform.runner_path,
                    "materializer": platform.materializer,
                    "binary_name": platform.binary_name,
                    "application_id": platform.application_id,
                    "enabled": platform.enabled,
                }
                for platform in spec.platforms
            ),
            "platform_readiness": platform_readiness,
            "requires_actor_control": spec.control.requires_actor,
            "default_screen": spec.control.default_screen,
            "admitted_screen": spec.control.admitted_screen,
            "interface_package_targets": interface_package_targets,
            "experience_package_targets": experience_package_targets,
            "environment_targets": (),
            "app_dependencies": tuple(
                {
                    "package_name": dependency.package_name,
                    "kind": dependency.kind,
                    "role": dependency.role,
                }
                for dependency in spec.dependencies
            ),
            "package_dependencies": _app_package_dependencies(spec),
            "source_code_package_id": (str(source_code_package_id) if source_code_package_id is not None else None),
        },
        bundle_packages=(
            SemanticPackageMaterializationBundle(
                package_key=package_name,
                manifest_toml_path=request.manifest_path,
                semantic_package_id=app_package_id,
                semantic_root_id=app_package_id,
                semantic_branch_id=request.branch_id,
                semantic_head_commit_id=app_package_snapshot.head_commit_id,
                semantic_object_instance_graph_commit_id=(app_package_snapshot.object_instance_graph_commit_id),
                semantic_root_object_instance_graph_commit_id=(app_package_snapshot.object_instance_graph_commit_id),
                semantic_root_kind="app_package",
                semantic_projection_name="AppPackage",
                source_code_package_id=source_code_package_id,
            ),
        ),
        mode="full_rebuild",
        affected_semantic_keys=_semantic_keys_from_request(request),
        applied_semantic_keys=_semantic_keys_from_request(request),
        fallback_reason=_APP_PACKAGE_FALLBACK_REASON,
        commit_id=app_package_snapshot.commit_id,
        head_commit_id=app_package_snapshot.head_commit_id,
    )


def _app_experience_package_references(
    *,
    request: SemanticPackageMaterializationRequest,
) -> tuple[AppExperiencePackageReference, ...]:
    raw_references = request.context.get(_WORKSPACE_EXPERIENCE_PACKAGE_REFERENCES_CONTEXT_KEY)
    if not isinstance(raw_references, (list, tuple)):
        return ()
    references: list[AppExperiencePackageReference] = []
    for raw_reference in raw_references:
        if not isinstance(raw_reference, Mapping):
            raise RuntimeError("Workspace ExperiencePackage reference must be a mapping.")
        package_name = _required_text(
            raw_reference.get("package_name"),
            label="workspace ExperiencePackage package_name",
        )
        references.append(
            AppExperiencePackageReference(
                package_name=package_name,
                experience_package_id=_required_uuid(
                    raw_reference.get("experience_package_id"),
                    label=(f"workspace ExperiencePackage {package_name!r} " "experience_package_id"),
                ),
                semantic_branch_id=_required_uuid(
                    raw_reference.get("semantic_branch_id"),
                    label=(f"workspace ExperiencePackage {package_name!r} " "semantic_branch_id"),
                ),
                semantic_head_commit_id=_required_uuid(
                    raw_reference.get("semantic_head_commit_id"),
                    label=(f"workspace ExperiencePackage {package_name!r} " "semantic_head_commit_id"),
                ),
                aware_root=Path(
                    _required_text(
                        raw_reference.get("aware_root"),
                        label=(f"workspace ExperiencePackage {package_name!r} " "aware_root"),
                    )
                )
                .expanduser()
                .resolve(),
                experience_package_object_instance_graph_commit_id=(
                    _uuid_or_none(raw_reference.get("experience_package_object_instance_graph_commit_id"))
                ),
            )
        )
    return tuple(references)


def _load_app_sources_for_manifest(
    *,
    manifest_path: Path,
    spec: AwareAppTomlSpec,
) -> tuple[AwareAppSourceSpec, ...]:
    package_root = manifest_path.parent.resolve()
    source_files = _discover_app_source_files(
        package_root=package_root,
        spec=spec,
    )
    if not source_files:
        raise AwareAppSourceMaterializationError(
            f"App package {spec.app.package_name!r} did not match any app .aware sources "
            + f"under [build].sources_dir={spec.build.sources_dir!r}"
        )
    return load_aware_app_source_specs(
        package_root=package_root,
        source_files=source_files,
    )


def _discover_app_source_files(
    *,
    package_root: Path,
    spec: AwareAppTomlSpec,
) -> tuple[Path, ...]:
    source_root = (package_root / spec.build.sources_dir).resolve()
    _assert_inside(
        root=package_root,
        candidate=source_root,
        label="[build].sources_dir",
    )
    if not source_root.exists() or not source_root.is_dir():
        raise AwareAppSourceMaterializationError(f"App source directory does not exist: {source_root}")
    candidates: dict[str, Path] = {}
    for pattern in spec.build.include_paths:
        for path in source_root.glob(pattern):
            if not path.is_file():
                continue
            _assert_inside(root=package_root, candidate=path, label="app source")
            rel_to_source = path.relative_to(source_root).as_posix()
            if _is_excluded_app_source(
                rel_to_source=rel_to_source,
                exclude_paths=spec.build.exclude_paths,
            ):
                continue
            rel_to_package = path.relative_to(package_root).as_posix()
            candidates[rel_to_package] = Path(rel_to_package)
    return tuple(candidates[key] for key in sorted(candidates))


def _is_excluded_app_source(
    *,
    rel_to_source: str,
    exclude_paths: tuple[str, ...],
) -> bool:
    return any(fnmatch(rel_to_source, pattern) for pattern in exclude_paths)


def _single_app_source_for_package(
    *,
    package_name: str,
    app_sources: tuple[AwareAppSourceSpec, ...],
) -> AwareAppSourceSpec:
    if len(app_sources) != 1:
        raise AwareAppSourceMaterializationError(
            f"App package {package_name!r} must lower exactly one app config; got {len(app_sources)}"
        )
    return app_sources[0]


def _assert_inside(*, root: Path, candidate: Path, label: str) -> None:
    root_resolved = root.resolve()
    candidate_resolved = candidate.resolve()
    if candidate_resolved == root_resolved or root_resolved in candidate_resolved.parents:
        return
    raise AwareAppSourceMaterializationError(
        f"{label} resolved outside app package boundary: root={root_resolved} candidate={candidate_resolved}"
    )


def _materialize_app_platforms(
    *,
    request: SemanticPackageMaterializationRequest,
    spec: AwareAppTomlSpec,
) -> tuple[dict[str, object], ...]:
    module_root = _module_root_for_manifest(request.manifest_path)
    dart_package_root = module_root / spec.dart.package_path
    return tuple(
        _materialize_app_platform(
            module_root=module_root,
            dart_package_root=dart_package_root,
            spec=spec,
            platform=platform,
        )
        for platform in spec.platforms
    )


def _app_interface_package_targets(
    *,
    spec: AwareAppTomlSpec,
    app_package_id: UUID,
) -> tuple[dict[str, object], ...]:
    return tuple(
        _app_interface_package_target(
            interface_spec=interface_spec,
            app_package_id=app_package_id,
        )
        for interface_spec in spec.interfaces
    )


def _app_interface_package_target(
    *,
    interface_spec: AwareAppTomlInterfaceSpec,
    app_package_id: UUID,
) -> dict[str, object]:
    interface_package_id = stable_interface_package_id(name=interface_spec.package_name)
    edge_id = stable_app_package_interface_package_id(
        app_package_id=app_package_id,
        interface_package_id=interface_package_id,
    )
    return {
        "app_package_interface_package_id": str(edge_id),
        "interface_package_id": str(interface_package_id),
        "interface_package_name": interface_spec.package_name,
        "role": interface_spec.role,
        "title": None,
        "description": None,
        "interface_package_object_instance_graph_commit_id": None,
        "resolution_status": "committed",
    }


def _app_package_dependencies(spec: AwareAppTomlSpec) -> tuple[str, ...]:
    values = (
        spec.factory.package_name,
        *(interface.package_name for interface in spec.interfaces),
        *(dependency.package_name for dependency in spec.dependencies),
    )
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return tuple(out)


def _materialize_app_platform(
    *,
    module_root: Path,
    dart_package_root: Path,
    spec: AwareAppTomlSpec,
    platform: AwareAppTomlPlatformSpec,
) -> dict[str, object]:
    if not platform.enabled:
        return {
            "target": platform.target,
            "status": "disabled",
            "runner_path": platform.runner_path,
            "materializer": platform.materializer,
            "enabled": False,
        }
    if platform.target == "linux" and platform.materializer == "flutter_create":
        return _verify_linux_flutter_platform(
            module_root=module_root,
            dart_package_root=dart_package_root,
            spec=spec,
            platform=platform,
        )
    return _verify_generic_platform_runner(
        module_root=module_root,
        platform=platform,
    )


def _verify_generic_platform_runner(
    *,
    module_root: Path,
    platform: AwareAppTomlPlatformSpec,
) -> dict[str, object]:
    runner_root = module_root / platform.runner_path
    if not runner_root.exists():
        raise AwareAppPlatformMaterializationError(
            f"Platform runner {platform.target!r} is missing at {platform.runner_path!r}"
        )
    return {
        "target": platform.target,
        "status": "ready",
        "runner_path": platform.runner_path,
        "materializer": platform.materializer,
        "enabled": True,
        "verified_files": (),
        "toolchain_requirements": (),
        "flutter_run_command": f"flutter run -d {platform.target}",
    }


def _verify_linux_flutter_platform(
    *,
    module_root: Path,
    dart_package_root: Path,
    spec: AwareAppTomlSpec,
    platform: AwareAppTomlPlatformSpec,
) -> dict[str, object]:
    runner_root = module_root / platform.runner_path
    binary_name = platform.binary_name or spec.dart.package_name
    required_paths = (
        dart_package_root / "pubspec.yaml",
        dart_package_root / spec.dart.entrypoint,
        dart_package_root / ".metadata",
        *(runner_root / relative_path for relative_path in _LINUX_PLATFORM_REQUIRED_FILES),
    )
    missing = tuple(_relative_path(path=path, root=module_root) for path in required_paths if not path.is_file())
    if missing:
        raise AwareAppPlatformMaterializationError(
            "Linux platform runner is not materialization-ready; " f"missing required files: {', '.join(missing)}"
        )

    marker_errors = _linux_platform_marker_errors(
        dart_package_root=dart_package_root,
        runner_root=runner_root,
        spec=spec,
        platform=platform,
        binary_name=binary_name,
    )
    if marker_errors:
        raise AwareAppPlatformMaterializationError(
            "Linux platform runner is not materialization-ready; " f"failed marker checks: {'; '.join(marker_errors)}"
        )

    return {
        "target": "linux",
        "status": "ready",
        "runner_path": platform.runner_path,
        "materializer": platform.materializer,
        "enabled": True,
        "binary_name": binary_name,
        "application_id": platform.application_id,
        "required_files": tuple(_relative_path(path=path, root=module_root) for path in required_paths),
        "verified_files": tuple(_relative_path(path=path, root=module_root) for path in required_paths),
        "toolchain_requirements": _LINUX_FLUTTER_TOOLCHAIN_REQUIREMENTS,
        "flutter_run_command": "flutter run -d linux",
    }


def _linux_platform_marker_errors(
    *,
    dart_package_root: Path,
    runner_root: Path,
    spec: AwareAppTomlSpec,
    platform: AwareAppTomlPlatformSpec,
    binary_name: str,
) -> tuple[str, ...]:
    errors: list[str] = []
    pubspec_text = (dart_package_root / "pubspec.yaml").read_text(encoding="utf-8")
    if f"name: {spec.dart.package_name}" not in pubspec_text:
        errors.append(f"pubspec.yaml must declare name: {spec.dart.package_name}")

    metadata_text = (dart_package_root / ".metadata").read_text(encoding="utf-8")
    if "platform: linux" not in metadata_text:
        errors.append(".metadata must include linux platform migration metadata")

    linux_cmake_text = (runner_root / "CMakeLists.txt").read_text(encoding="utf-8")
    if f'set(BINARY_NAME "{binary_name}")' not in linux_cmake_text:
        errors.append(f"linux/CMakeLists.txt must set BINARY_NAME {binary_name!r}")
    if (
        platform.application_id is not None
        and f'set(APPLICATION_ID "{platform.application_id}")' not in linux_cmake_text
    ):
        errors.append(f"linux/CMakeLists.txt must set APPLICATION_ID {platform.application_id!r}")
    for marker in (
        'add_subdirectory("runner")',
        "include(flutter/generated_plugins.cmake)",
        "add_dependencies(${BINARY_NAME} flutter_assemble)",
    ):
        if marker not in linux_cmake_text:
            errors.append(f"linux/CMakeLists.txt missing marker {marker!r}")

    runner_cmake_text = (runner_root / "runner" / "CMakeLists.txt").read_text(encoding="utf-8")
    for marker in (
        "add_executable(${BINARY_NAME}",
        "apply_standard_settings(${BINARY_NAME})",
        "target_link_libraries(${BINARY_NAME} PRIVATE flutter)",
        "target_link_libraries(${BINARY_NAME} PRIVATE PkgConfig::GTK)",
    ):
        if marker not in runner_cmake_text:
            errors.append(f"linux/runner/CMakeLists.txt missing marker {marker!r}")
    return tuple(errors)


def _relative_path(*, path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _write_app_launch_artifacts(
    *,
    request: SemanticPackageMaterializationRequest,
    spec: AwareAppTomlSpec,
    descriptor: AwareAppLaunchDescriptor,
) -> tuple[Path, Path]:
    module_root = _module_root_for_manifest(request.manifest_path)
    dart_package_root = module_root / spec.dart.package_path
    generated_manifest_path = dart_package_root / spec.launch.generated_manifest_path
    generated_descriptor_path = request.manifest_path.parent / "aware.app.launch.json"
    generated_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    generated_manifest_path.write_text(
        render_aware_app_launch_manifest_dart(
            spec=spec,
            source_manifest_path=request.manifest_path.relative_to(module_root),
            descriptor=descriptor,
        ),
        encoding="utf-8",
    )
    generated_descriptor_path.write_text(
        render_aware_app_launch_descriptor_json(descriptor),
        encoding="utf-8",
    )
    return generated_manifest_path, generated_descriptor_path


def _module_root_for_manifest(manifest_path: Path) -> Path:
    path = Path(manifest_path)
    for parent in (path.parent, *path.parents):
        if (parent / "aware.module.toml").exists():
            return parent
    if path.parent.parent.name == "apps":
        return path.parent.parent.parent
    return path.parent


async def _materialize_interface_package(
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    semantic_object_config_graphs = _semantic_object_config_graphs_from_context(request)
    result = await materialize_interface_package_from_manifest(
        runtime=request.runtime,
        index=request.index,
        actor_id=request.actor_id,
        branch_id=request.branch_id,
        workspace_root=request.workspace_root,
        interface_toml_path=request.manifest_path,
        projection_identity_ocg=cast(
            ObjectConfigGraph | None,
            request.context.get("projection_identity_ocg"),
        ),
        projection_identity_ocgs=semantic_object_config_graphs,
        state_model_catalog=_state_model_catalog_from_context(
            request,
            semantic_object_config_graphs=semantic_object_config_graphs,
        ),
        state_attribute_catalog=_state_attribute_catalog_from_context(
            request,
            semantic_object_config_graphs=semantic_object_config_graphs,
        ),
        api_view_catalog=_api_view_catalog_from_context(request),
        prefer_snapshot_materialization=True,
    )
    pane_render_spec_result = getattr(
        result,
        "pane_render_spec_materialization_result",
        None,
    )
    return SemanticPackageMaterializationResult(
        details={
            "interface_toml_path": result.interface_toml_path.as_posix(),
            "interface_config_bundle_path": result.config_bundle_path.as_posix(),
            "interface_name": result.interface_config.name,
            "interface_config_id": str(result.interface_config.id),
            "interface_package_name": result.interface_package.name,
            "interface_package_id": str(result.interface_package.id),
            "semantic_branch_id": str(request.branch_id),
            "source_code_package_id": (
                str(result.source_code_package_id) if result.source_code_package_id is not None else None
            ),
            "interface_config_commit_id": (
                str(result.interface_config_commit_id) if result.interface_config_commit_id is not None else None
            ),
            "interface_config_object_instance_graph_commit_id": (
                str(result.interface_config_object_instance_graph_commit_id)
                if result.interface_config_object_instance_graph_commit_id is not None
                else None
            ),
            "interface_package_commit_id": (
                str(result.package_commit_id) if result.package_commit_id is not None else None
            ),
            "interface_package_head_commit_id": (
                str(result.package_head_commit_id) if result.package_head_commit_id is not None else None
            ),
            "pane_render_spec_materialization_path": (
                pane_render_spec_result.materialization_path.as_posix() if pane_render_spec_result is not None else None
            ),
            "pane_render_spec_materialization_commit_id": (
                str(pane_render_spec_result.materialization_commit_id) if pane_render_spec_result is not None else None
            ),
            "pane_render_spec_commit_id": (
                str(pane_render_spec_result.last_commit_id)
                if pane_render_spec_result is not None and pane_render_spec_result.last_commit_id is not None
                else None
            ),
            "pane_render_spec_head_commit_id": (
                str(pane_render_spec_result.last_head_commit_id)
                if pane_render_spec_result is not None and pane_render_spec_result.last_head_commit_id is not None
                else None
            ),
            "pane_render_spec_object_instance_graph_commit_id": (
                str(pane_render_spec_result.object_instance_graph_commit_id)
                if pane_render_spec_result is not None
                and pane_render_spec_result.object_instance_graph_commit_id is not None
                else None
            ),
            "pane_render_spec_count": (
                len(pane_render_spec_result.pane_render_specs) if pane_render_spec_result is not None else 0
            ),
            "phase_timings_s": dict(result.phase_timings_s),
        },
        bundle_packages=(
            SemanticPackageMaterializationBundle(
                package_key=result.interface_package.name,
                manifest_toml_path=result.interface_toml_path,
                semantic_package_id=result.interface_package.id,
                semantic_root_id=result.interface_config.id,
                semantic_branch_id=request.branch_id,
                semantic_head_commit_id=result.package_head_commit_id,
                semantic_object_instance_graph_commit_id=(result.package_object_instance_graph_commit_id),
                semantic_root_object_instance_graph_commit_id=(result.interface_config_object_instance_graph_commit_id),
                semantic_root_kind="interface_config",
                semantic_projection_name="InterfacePackage",
                semantic_projection_hash=result.package_projection_hash,
                source_code_package_id=result.source_code_package_id,
                source_object_instance_graph_commit_id=(result.source_object_instance_graph_commit_id),
                provider_replay_evidence={
                    "semantic_outputs": _interface_replay_semantic_package_evidence(
                        request=request,
                        result=result,
                    )
                },
            ),
        ),
        mode="full_rebuild",
        affected_semantic_keys=_semantic_keys_from_request(request),
        applied_semantic_keys=_semantic_keys_from_request(request),
        fallback_reason=_INTERFACE_FULL_REBUILD_FALLBACK_REASON,
        commit_id=result.package_commit_id,
        head_commit_id=result.package_head_commit_id,
    )


def _interface_replay_semantic_package_evidence(
    *,
    request: SemanticPackageMaterializationRequest,
    result: InterfacePackageMaterializationResult,
) -> tuple[dict[str, object], ...]:
    source_evidence = _interface_semantic_output_evidence(
        role="source_code_package",
        branch_id=request.branch_id,
        projection_hash=result.source_projection_hash,
        object_instance_graph_commit_id=(result.source_object_instance_graph_commit_id),
    )
    config_evidence = _interface_semantic_output_evidence(
        role="interface_config",
        branch_id=request.branch_id,
        projection_hash=result.interface_config_projection_hash,
        object_instance_graph_commit_id=(result.interface_config_object_instance_graph_commit_id),
        artifact_refs=(
            _interface_artifact_witness(
                workspace_root=request.workspace_root,
                path=result.config_bundle_path,
            ),
        ),
    )
    evidence = [source_evidence, config_evidence]
    pane_result = result.pane_render_spec_materialization_result
    if pane_result is not None:
        artifact_ref = _interface_artifact_witness(
            workspace_root=request.workspace_root,
            path=pane_result.materialization_path,
        )
        for index, materialized_pane in enumerate(pane_result.pane_render_specs):
            evidence.append(
                _interface_semantic_output_evidence(
                    role="pane_render_spec",
                    branch_id=materialized_pane.branch_id,
                    projection_hash=pane_result.projection_hash,
                    object_instance_graph_commit_id=(materialized_pane.object_instance_graph_commit_id),
                    artifact_refs=(artifact_ref,) if index == 0 else (),
                )
            )
    return tuple(evidence)


def _interface_semantic_output_evidence(
    *,
    role: str,
    branch_id: UUID | None,
    projection_hash: str | None,
    object_instance_graph_commit_id: UUID | None,
    artifact_refs: tuple[Mapping[str, object], ...] = (),
) -> dict[str, object]:
    return {
        "role": role,
        "branch_id": branch_id,
        "projection_hash": projection_hash,
        "object_instance_graph_commit_id": object_instance_graph_commit_id,
        "artifact_refs": artifact_refs,
    }


def _interface_artifact_witness(
    *,
    workspace_root: Path,
    path: Path,
) -> dict[str, object]:
    resolved_workspace_root = workspace_root.resolve()
    resolved_path = path.resolve()
    relative_path = resolved_path.relative_to(resolved_workspace_root)
    return {
        "path": relative_path.as_posix(),
        "digest_algorithm": "sha256",
        "digest": f"sha256:{sha256(resolved_path.read_bytes()).hexdigest()}",
    }


def _state_model_catalog_from_context(
    request: SemanticPackageMaterializationRequest,
    *,
    semantic_object_config_graphs: tuple[ObjectConfigGraph, ...] | None = None,
) -> dict[str, UUID]:
    catalog: dict[str, UUID] = {}
    for key, value in _state_model_catalog_from_runtime_index(request).items():
        catalog.setdefault(key, value)
    for ocg in (
        semantic_object_config_graphs
        if semantic_object_config_graphs is not None
        else _semantic_object_config_graphs_from_context(request)
    ):
        for key, value in build_state_model_catalog_from_ocg(ocg=ocg).items():
            catalog.setdefault(key, value)
    projection_identity_ocg = request.context.get("projection_identity_ocg")
    if isinstance(projection_identity_ocg, ObjectConfigGraph):
        for key, value in build_state_model_catalog_from_ocg(
            ocg=projection_identity_ocg,
        ).items():
            catalog.setdefault(key, value)
    return catalog


def _state_attribute_catalog_from_context(
    request: SemanticPackageMaterializationRequest,
    *,
    semantic_object_config_graphs: tuple[ObjectConfigGraph, ...] | None = None,
) -> dict[str, Mapping[str, UUID]]:
    catalog: dict[str, Mapping[str, UUID]] = {}
    for key, value in _state_attribute_catalog_from_runtime_index(request).items():
        catalog.setdefault(key, value)
    for ocg in (
        semantic_object_config_graphs
        if semantic_object_config_graphs is not None
        else _semantic_object_config_graphs_from_context(request)
    ):
        for key, value in build_state_attribute_catalog_from_ocg(ocg=ocg).items():
            catalog.setdefault(key, value)
    projection_identity_ocg = request.context.get("projection_identity_ocg")
    if isinstance(projection_identity_ocg, ObjectConfigGraph):
        for key, value in build_state_attribute_catalog_from_ocg(
            ocg=projection_identity_ocg,
        ).items():
            catalog.setdefault(key, value)
    return catalog


def _state_model_catalog_from_runtime_index(
    request: SemanticPackageMaterializationRequest,
) -> dict[str, UUID]:
    raw_class_configs_by_id = getattr(request.index, "class_configs_by_id", {})
    if not isinstance(raw_class_configs_by_id, Mapping):
        return {}
    catalog: dict[str, UUID] = {}
    for class_config in raw_class_configs_by_id.values():
        class_fqn = (getattr(class_config, "class_fqn", "") or "").strip()
        class_config_id = getattr(class_config, "id", None)
        if not class_fqn or not isinstance(class_config_id, UUID):
            continue
        catalog.setdefault(class_fqn.casefold(), class_config_id)
    return catalog


def _state_attribute_catalog_from_runtime_index(
    request: SemanticPackageMaterializationRequest,
) -> dict[str, Mapping[str, UUID]]:
    raw_class_configs_by_id = getattr(request.index, "class_configs_by_id", {})
    if not isinstance(raw_class_configs_by_id, Mapping):
        return {}
    catalog: dict[str, Mapping[str, UUID]] = {}
    for class_config in raw_class_configs_by_id.values():
        class_fqn = (getattr(class_config, "class_fqn", "") or "").strip()
        if not class_fqn:
            continue
        attribute_ids = _state_attribute_ids_from_class_config(
            class_config=class_config,
        )
        if attribute_ids:
            catalog.setdefault(class_fqn.casefold(), attribute_ids)
    return catalog


def _state_attribute_ids_from_class_config(*, class_config: object) -> Mapping[str, UUID]:
    attribute_ids: dict[str, UUID] = {}
    class_attribute_edges = getattr(class_config, "class_config_attribute_configs", ())
    for edge in class_attribute_edges:
        attribute_config = getattr(edge, "attribute_config", None)
        attribute_name = (getattr(attribute_config, "name", "") or "").strip()
        attribute_config_id = getattr(attribute_config, "id", None)
        if not attribute_name or not isinstance(attribute_config_id, UUID):
            continue
        attribute_ids[attribute_name.casefold()] = attribute_config_id
        owner_key = (getattr(attribute_config, "owner_key", "") or "").strip()
        if owner_key:
            attribute_ids[f"{owner_key}.{attribute_name}".casefold()] = attribute_config_id
    return attribute_ids


def _api_view_catalog_from_context(
    request: SemanticPackageMaterializationRequest,
) -> dict[str, ApiViewStateTruth]:
    catalog: dict[str, ApiViewStateTruth] = {}
    runtime_objects = _runtime_index_objects(request.index)
    api_view_refs_by_id: dict[UUID, str] = {}
    for api_view in runtime_objects:
        api_view_id = getattr(api_view, "id", None)
        view_ref = (getattr(api_view, "view_ref", "") or "").strip()
        if isinstance(api_view_id, UUID) and view_ref:
            api_view_refs_by_id[api_view_id] = view_ref
    action_endpoints_by_view_ref = _api_view_action_endpoints_by_view_ref(
        runtime_objects=runtime_objects,
        api_view_refs_by_id=api_view_refs_by_id,
    )
    for api_view in runtime_objects:
        view_ref = (getattr(api_view, "view_ref", "") or "").strip()
        state_model_id = getattr(api_view, "state_model_id", None)
        if not view_ref or not isinstance(state_model_id, UUID):
            continue
        state_model_ref = _api_view_state_model_ref(
            api_view=api_view,
            request=request,
        )
        if state_model_ref is None:
            continue
        catalog[view_ref.casefold()] = ApiViewStateTruth(
            view_ref=view_ref,
            state_model_ref=state_model_ref,
            state_model_id=state_model_id,
            action_endpoints_by_key=action_endpoints_by_view_ref.get(
                view_ref.casefold(),
                {},
            ),
        )
    return catalog


def _api_view_action_endpoints_by_view_ref(
    *,
    runtime_objects: tuple[object, ...],
    api_view_refs_by_id: Mapping[UUID, str],
) -> dict[str, Mapping[str, ApiViewActionTruth]]:
    actions_by_view_ref: dict[str, dict[str, ApiViewActionTruth]] = {}
    for item in runtime_objects:
        api_view_id = getattr(item, "api_view_id", None)
        api_view_capability_endpoint_id = getattr(item, "id", None)
        action_key = (getattr(item, "action_key", "") or "").strip()
        endpoint_ref = (getattr(item, "endpoint_ref", "") or "").strip()
        if (
            not isinstance(api_view_id, UUID)
            or not isinstance(api_view_capability_endpoint_id, UUID)
            or not action_key
            or not endpoint_ref
        ):
            continue
        view_ref = api_view_refs_by_id.get(api_view_id)
        if view_ref is None:
            continue
        actions_by_view_ref.setdefault(view_ref.casefold(), {})[action_key.casefold()] = ApiViewActionTruth(
            action_key=action_key,
            endpoint_ref=endpoint_ref,
            api_view_capability_endpoint_id=api_view_capability_endpoint_id,
            api_capability_endpoint_id=_uuid_or_none(getattr(item, "api_capability_endpoint_id", None)),
            sdk_operation_api_view_capability_endpoint_id=_uuid_or_none(
                getattr(item, "sdk_operation_api_view_capability_endpoint_id", None)
            ),
            sdk_operation_id=_uuid_or_none(getattr(item, "sdk_operation_id", None)),
        )
    return {view_ref: dict(actions_by_key) for view_ref, actions_by_key in actions_by_view_ref.items()}


def _runtime_index_objects(index: object) -> tuple[object, ...]:
    objects: list[object] = []
    seen: set[int] = set()
    for attr_name in (
        "api_views_by_id",
        "objects_by_id",
        "object_instances_by_id",
        "instances_by_id",
    ):
        raw = getattr(index, attr_name, None)
        if isinstance(raw, Mapping):
            for item in raw.values():
                item_id = id(item)
                if item_id not in seen:
                    seen.add(item_id)
                    objects.append(item)
    imap_all_objects = getattr(index, "imap_all_objects", None)
    if callable(imap_all_objects):
        for item in imap_all_objects():
            item_id = id(item)
            if item_id not in seen:
                seen.add(item_id)
                objects.append(item)
    return tuple(objects)


def _api_view_state_model_ref(
    *,
    api_view: object,
    request: SemanticPackageMaterializationRequest,
) -> str | None:
    state_model = getattr(api_view, "state_model", None)
    state_model_ref = (getattr(state_model, "class_fqn", "") or "").strip()
    if state_model_ref:
        return state_model_ref
    state_model_id = getattr(api_view, "state_model_id", None)
    if not isinstance(state_model_id, UUID):
        return None
    raw_class_configs_by_id = getattr(request.index, "class_configs_by_id", {})
    if not isinstance(raw_class_configs_by_id, Mapping):
        return None
    class_config = raw_class_configs_by_id.get(state_model_id)
    state_model_ref = (getattr(class_config, "class_fqn", "") or "").strip()
    return state_model_ref or None


def _semantic_object_config_graphs_from_context(
    request: SemanticPackageMaterializationRequest,
) -> tuple[ObjectConfigGraph, ...]:
    raw_graphs = request.context.get("semantic_object_config_graphs")
    if not isinstance(raw_graphs, (tuple, list)):
        return ()
    return tuple(graph for graph in raw_graphs if isinstance(graph, ObjectConfigGraph))


def _string_or_none(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _uuid_or_none(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    raw = _string_or_none(value)
    if raw is None:
        return None
    return UUID(raw)


def _required_text(value: object, *, label: str) -> str:
    resolved = _string_or_none(value)
    if resolved is None:
        raise RuntimeError(f"Missing {label}.")
    return resolved


def _required_uuid(value: object, *, label: str) -> UUID:
    resolved = _uuid_or_none(value)
    if resolved is None:
        raise RuntimeError(f"Missing {label}.")
    return resolved


def _semantic_keys_from_request(
    request: SemanticPackageMaterializationRequest,
) -> tuple[str, ...]:
    raw_keys = request.change_preview.get("affected_semantic_keys")
    if not isinstance(raw_keys, (list, tuple, set)):
        return ()
    return tuple(sorted({str(key).strip() for key in raw_keys if str(key).strip()}))


__all__ = ["materialize", "resolve_currentness_replay"]
