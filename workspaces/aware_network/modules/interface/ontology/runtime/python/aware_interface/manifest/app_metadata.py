from __future__ import annotations

from collections.abc import Mapping
from fnmatch import fnmatch
from pathlib import Path
from uuid import UUID

from aware_code.module_semantic_contract import (
    ModuleSemanticManifestResolutionDescriptor,
)
from aware_experience_ontology.stable_ids import stable_experience_package_id
from aware_interface.manifest.app_launch_selection import (
    build_aware_app_launch_selection_payload,
)
from aware_interface.manifest.app_source_loader import load_aware_app_source_specs
from aware_interface.manifest.app_spec import (
    AwareAppSourceSpec,
    AwareAppTomlInterfaceSpec,
    AwareAppTomlSpec,
)
from aware_interface_ontology.stable_ids import (
    stable_app_config_id,
    stable_app_package_experience_package_id,
    stable_app_package_id,
    stable_app_package_interface_package_id,
    stable_interface_package_id,
)


def resolve_aware_app_manifest_metadata(
    *,
    workspace_root: Path,
    package_root: Path,
    manifest_path: Path,
    manifest_spec: object,
    descriptor: ModuleSemanticManifestResolutionDescriptor,
    metadata: Mapping[str, object],
) -> dict[str, object]:
    del workspace_root, package_root, manifest_path, descriptor
    if not isinstance(manifest_spec, AwareAppTomlSpec):
        return {}
    app_package_id = stable_app_package_id(
        name=manifest_spec.app.package_name,
    )
    app_sources = _load_app_sources(
        package_root=package_root,
        manifest_spec=manifest_spec,
    )
    app_config = _single_app_source(
        package_name=manifest_spec.app.package_name,
        app_sources=app_sources,
    )
    app_config_id = stable_app_config_id(name=app_config.name)
    interface_package_targets = _interface_package_targets_metadata(
        manifest_spec=manifest_spec,
        app_package_id=app_package_id,
    )
    experience_package_targets = _experience_package_targets_metadata(
        manifest_spec=manifest_spec,
        app_package_id=app_package_id,
    )
    return {
        "app_name": manifest_spec.app.app_name,
        "app_title": manifest_spec.app.title,
        "app_description": manifest_spec.app.description,
        "app_package": {
            "app_package_id": str(app_package_id),
            "package_name": manifest_spec.app.package_name,
            "name": manifest_spec.app.package_name,
            "semantic_kind": "app_package",
            "semantic_projection_name": "AppPackage",
            "semantic_root_kind": "app_package",
            "app_config_id": str(app_config_id),
            "app_config_object_instance_graph_commit_id": None,
            "aware_app_version": manifest_spec.aware_app,
            "version_number": manifest_spec.app.version_number,
            "title": manifest_spec.app.title,
            "description": manifest_spec.app.description,
        },
        "app_package_id": str(app_package_id),
        "app_configs": _app_config_metadata(
            app_config=app_config,
            app_config_id=app_config_id,
        ),
        "interface_package_targets": interface_package_targets,
        "experience_package_targets": experience_package_targets,
        "environment_targets": (),
        "dart_package_name": manifest_spec.dart.package_name,
        "dart_package_path": manifest_spec.dart.package_path,
        "dart_entrypoint": manifest_spec.dart.entrypoint,
        "factory_package_name": manifest_spec.factory.package_name,
        "factory_package_path": manifest_spec.factory.package_path,
        "requires_actor_control": manifest_spec.control.requires_actor,
        "default_screen": manifest_spec.control.default_screen,
        "admitted_screen": manifest_spec.control.admitted_screen,
        "app_dependencies": tuple(
            {
                "package_name": dependency.package_name,
                "kind": dependency.kind,
                "role": dependency.role,
            }
            for dependency in manifest_spec.dependencies
        ),
        "platforms": tuple(platform.target for platform in manifest_spec.platforms if platform.enabled),
        "platform_runners": tuple(
            {
                "target": platform.target,
                "runner_path": platform.runner_path,
                "materializer": platform.materializer,
                "binary_name": platform.binary_name,
                "application_id": platform.application_id,
                "enabled": platform.enabled,
            }
            for platform in manifest_spec.platforms
        ),
        "interface_package_names": tuple(interface.package_name for interface in manifest_spec.interfaces),
        "launch_selection": build_aware_app_launch_selection_payload(spec=manifest_spec),
        "package_dependencies": _dedupe(
            (
                manifest_spec.factory.package_name,
                *(interface.package_name for interface in manifest_spec.interfaces),
                *(dependency.package_name for dependency in manifest_spec.dependencies),
                *_string_sequence(metadata.get("package_dependencies")),
            )
        ),
    }


def _load_app_sources(
    *,
    package_root: Path,
    manifest_spec: AwareAppTomlSpec,
) -> tuple[AwareAppSourceSpec, ...]:
    source_files = _discover_app_source_files(
        package_root=package_root,
        manifest_spec=manifest_spec,
    )
    return load_aware_app_source_specs(
        package_root=package_root,
        source_files=source_files,
    )


def _discover_app_source_files(
    *,
    package_root: Path,
    manifest_spec: AwareAppTomlSpec,
) -> tuple[Path, ...]:
    source_root = (package_root / manifest_spec.build.sources_dir).resolve()
    _assert_inside(root=package_root, candidate=source_root)
    if not source_root.is_dir():
        raise ValueError(f"App source directory does not exist: {source_root}")
    candidates: dict[str, Path] = {}
    for pattern in manifest_spec.build.include_paths:
        for path in source_root.glob(pattern):
            if not path.is_file():
                continue
            _assert_inside(root=package_root, candidate=path)
            rel_to_source = path.relative_to(source_root).as_posix()
            if any(fnmatch(rel_to_source, exclude) for exclude in manifest_spec.build.exclude_paths):
                continue
            rel_to_package = path.relative_to(package_root).as_posix()
            candidates[rel_to_package] = Path(rel_to_package)
    if not candidates:
        raise ValueError(f"App package {manifest_spec.app.package_name!r} did not match any app .aware sources")
    return tuple(candidates[key] for key in sorted(candidates))


def _single_app_source(
    *,
    package_name: str,
    app_sources: tuple[AwareAppSourceSpec, ...],
) -> AwareAppSourceSpec:
    if len(app_sources) != 1:
        raise ValueError(f"App package {package_name!r} must lower exactly one app config; got {len(app_sources)}")
    return app_sources[0]


def _app_config_metadata(
    *,
    app_config: AwareAppSourceSpec,
    app_config_id: UUID,
) -> tuple[dict[str, object], ...]:
    return (
        {
            "app_config_id": str(app_config_id),
            "name": app_config.name,
            "title": app_config.title,
            "description": app_config.description,
            "source_path": app_config.source_path,
            "screen_configs": tuple(
                {
                    "app_config_screen_config_id": None,
                    "screen_key": screen.screen_key,
                    "projection_experience": screen.projection_experience,
                    "projection_experience_id": None,
                    "projection_experience_layout": screen.projection_experience_layout,
                    "projection_experience_layout_graph_binding_id": None,
                    "resolution_status": "declared",
                    "source_path": screen.source_path,
                }
                for screen in app_config.screens
            ),
        },
    )


def _assert_inside(*, root: Path, candidate: Path) -> None:
    root_resolved = root.resolve()
    candidate_resolved = candidate.resolve()
    if candidate_resolved == root_resolved or root_resolved in candidate_resolved.parents:
        return
    raise ValueError(
        f"App source resolved outside package boundary: root={root_resolved} candidate={candidate_resolved}"
    )


def _interface_package_targets_metadata(
    *,
    manifest_spec: AwareAppTomlSpec,
    app_package_id: UUID,
) -> tuple[dict[str, object], ...]:
    return tuple(
        _interface_package_target_metadata(
            interface_spec=interface_spec,
            app_package_id=app_package_id,
        )
        for interface_spec in manifest_spec.interfaces
    )


def _interface_package_target_metadata(
    *,
    interface_spec: AwareAppTomlInterfaceSpec,
    app_package_id: UUID,
) -> dict[str, object]:
    interface_package_id = stable_interface_package_id(
        name=interface_spec.package_name,
    )
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
        "resolution_status": "declared",
    }


def _experience_package_targets_metadata(
    *,
    manifest_spec: AwareAppTomlSpec,
    app_package_id: UUID,
) -> tuple[dict[str, object], ...]:
    return tuple(
        _experience_package_target_metadata(
            app_package_id=app_package_id,
            package_name=dependency.package_name,
            role=dependency.role,
        )
        for dependency in manifest_spec.dependencies
        if dependency.kind == "experience_package"
    )


def _experience_package_target_metadata(
    *,
    app_package_id: UUID,
    package_name: str,
    role: str,
) -> dict[str, object]:
    experience_package_id = stable_experience_package_id(name=package_name)
    edge_id = stable_app_package_experience_package_id(
        app_package_id=app_package_id,
        experience_package_id=experience_package_id,
    )
    return {
        "app_package_experience_package_id": str(edge_id),
        "experience_package_id": str(experience_package_id),
        "experience_package_name": package_name,
        "role": role,
        "description": None,
        "experience_package_object_instance_graph_commit_id": None,
        "resolution_status": "declared",
    }


def _string_sequence(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    return ()


def _dedupe(values: tuple[object, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return tuple(out)


__all__ = ["resolve_aware_app_manifest_metadata"]
