from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path

from aware_code.semantic_materialization import (
    SEMANTIC_MATERIALIZATION_TARGET_MANIFEST_PATHS_CONTEXT_KEY,
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY,
    SemanticPackageMaterializationRuntimeContextRequest,
)
from aware_experience.manifest.loader import load_aware_experience_toml_spec
from aware_experience.manifest.spec import AwareExperienceDependencyKind
from aware_experience.materialization.source_module_ontology import (
    nearest_module_toml_path,
    source_module_ontology_manifest_paths_for_manifest,
    source_module_ontology_package_names_for_manifest,
    source_module_ontology_package_ref_from_manifest,
)
from aware_experience.program.loader import load_aware_programs_toml_spec
from aware_meta.runtime.factory import (
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.graph_context import MetaWorkspaceMaterializationRuntimeContext
from aware_meta.runtime.package_index import MetaRuntimePackageIndexEntry
from aware_ontology.semantic_runtime_catalog import (
    resolve_semantic_ontology_package_manifest_closure,
    semantic_ontology_package_catalog_entries_by_name,
)


def build_experience_workspace_materialization_runtime_context(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> MetaWorkspaceMaterializationRuntimeContext | None:
    """Build Experience's Workspace context from ontology package manifest truth."""

    manifest_paths = _experience_workspace_materialization_manifest_paths(request)
    if not manifest_paths:
        return None
    source_module_ontology_manifest_paths = _source_module_ontology_manifest_paths(
        request
    )
    package_cache_owner_roots_by_manifest_path = (
        _package_cache_owner_roots_by_manifest_path_for_request(
            request=request,
            manifest_paths=manifest_paths,
            source_module_ontology_manifest_paths=(
                source_module_ontology_manifest_paths
            ),
        )
    )

    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=manifest_paths,
        workspace_root=request.workspace_root,
        composite_name="Aware Experience Workspace Materialization Context",
        strict_package_graph_cache=_has_explicit_semantic_ontology_package_catalog(
            request.context
        ),
        package_entries_by_manifest_path=(
            _package_entries_by_manifest_path_for_request(
                request=request,
                manifest_paths=manifest_paths,
                source_module_ontology_manifest_paths=(
                    source_module_ontology_manifest_paths
                ),
            )
        ),
        package_cache_owner_roots_by_manifest_path=(
            package_cache_owner_roots_by_manifest_path
        ),
    )
    meta_context = runtime.context
    if meta_context is None:
        raise RuntimeError(
            "Experience Meta graph runtime did not expose its graph context."
        )
    return MetaWorkspaceMaterializationRuntimeContext(
        meta_context=meta_context,
        runtime=runtime,
        actor_id=request.actor_id,
    )


def _experience_workspace_materialization_manifest_paths(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> tuple[Path, ...]:
    runtime_package_names = _runtime_context_ontology_package_names(request)
    dependency_package_names = _declared_experience_ontology_dependency_package_names(
        request
    )
    source_module_package_names = _source_module_ontology_package_names(request)
    source_module_manifest_paths = _source_module_ontology_manifest_paths(request)
    program_dependency_package_names = _declared_program_dependency_package_names(
        request
    )
    required_projection_names = _clean_string_tuple(
        request.context.get("required_projection_names")
    )
    if (
        not runtime_package_names
        and not dependency_package_names
        and not source_module_package_names
        and not program_dependency_package_names
        and not required_projection_names
    ):
        return ()
    catalog_source_module_package_names = source_module_package_names
    if _has_explicit_semantic_ontology_package_catalog(request.context):
        entries_by_name = semantic_ontology_package_catalog_entries_by_name(
            context=request.context,
            repo_root=request.repo_root,
        )
        catalog_source_module_package_names = tuple(
            package_name
            for package_name in source_module_package_names
            if package_name in entries_by_name
        )

    catalog_manifest_paths = resolve_semantic_ontology_package_manifest_closure(
        context=request.context,
        repo_root=request.repo_root,
        package_names=(
            *runtime_package_names,
            *dependency_package_names,
            *catalog_source_module_package_names,
            *program_dependency_package_names,
        ),
        required_projection_names=required_projection_names,
    )
    return tuple(
        dict.fromkeys((*catalog_manifest_paths, *source_module_manifest_paths))
    )


def _runtime_context_ontology_package_names(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> tuple[str, ...]:
    context_package_names = _clean_string_tuple(
        request.context.get("runtime_ontology_package_names")
    )
    provider_package_names = _clean_string_tuple(
        request.provider_payload.get("runtime_ontology_package_names")
    )
    return tuple(dict.fromkeys((*context_package_names, *provider_package_names)))


def _declared_experience_ontology_dependency_package_names(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> tuple[str, ...]:
    if request.manifest_path is None:
        return ()
    manifest_path = request.manifest_path.expanduser()
    if not manifest_path.is_absolute():
        manifest_path = request.workspace_root / manifest_path
    if not manifest_path.exists():
        return ()
    spec = load_aware_experience_toml_spec(toml_path=manifest_path)
    package_names = tuple(
        dict.fromkeys(
            dependency.package_name
            for dependency in spec.dependencies
            if dependency.package_name
            and dependency.kind is AwareExperienceDependencyKind.ontology_package
        )
    )
    if not package_names or not _has_explicit_semantic_ontology_package_catalog(
        request.context
    ):
        return package_names
    entries_by_name = semantic_ontology_package_catalog_entries_by_name(
        context=request.context,
        repo_root=request.repo_root,
    )
    return tuple(
        package_name
        for package_name in package_names
        if package_name in entries_by_name
    )


def _source_module_ontology_package_names(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> tuple[str, ...]:
    package_names: list[str] = []
    for manifest_path in _source_experience_manifest_paths(request):
        package_names.extend(
            source_module_ontology_package_names_for_manifest(manifest_path)
        )
    resolved_names = tuple(dict.fromkeys(package_names))
    if not resolved_names or not _has_explicit_semantic_ontology_package_catalog(
        request.context
    ):
        return resolved_names
    entries_by_name = semantic_ontology_package_catalog_entries_by_name(
        context=request.context,
        repo_root=request.repo_root,
    )
    return tuple(
        package_name
        for package_name in resolved_names
        if package_name in entries_by_name
    )


def _source_module_ontology_manifest_paths(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> tuple[Path, ...]:
    manifest_paths: list[Path] = []
    for manifest_path in _source_experience_manifest_paths(request):
        manifest_paths.extend(
            source_module_ontology_manifest_paths_for_manifest(manifest_path)
        )
    return tuple(dict.fromkeys(manifest_paths))


def _source_experience_manifest_paths(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> tuple[Path, ...]:
    paths: list[Path] = []
    for path in _context_manifest_paths(
        value=request.context.get(
            SEMANTIC_MATERIALIZATION_TARGET_MANIFEST_PATHS_CONTEXT_KEY
        ),
        workspace_root=request.workspace_root,
    ):
        paths.append(path)
    manifest_path = _resolved_manifest_path(request)
    if manifest_path is not None:
        paths.append(manifest_path)
    return tuple(dict.fromkeys(path.expanduser().resolve() for path in paths))


def _context_manifest_paths(
    *,
    value: object,
    workspace_root: Path,
) -> tuple[Path, ...]:
    paths: list[Path] = []
    for raw_path in _clean_string_tuple(value):
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = workspace_root / path
        paths.append(path.resolve())
    return tuple(dict.fromkeys(paths))


def _declared_program_dependency_package_names(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> tuple[str, ...]:
    manifest_path = _resolved_manifest_path(request)
    if manifest_path is None:
        return ()
    programs_manifest_path = manifest_path.parent / "aware.programs.toml"
    if not programs_manifest_path.is_file():
        return ()
    spec = load_aware_programs_toml_spec(toml_path=programs_manifest_path)
    return tuple(
        dict.fromkeys(
            dependency
            for program in spec.programs
            for dependency in program.dependencies
            if dependency
        )
    )


def _resolved_manifest_path(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> Path | None:
    if request.manifest_path is None:
        return None
    manifest_path = request.manifest_path.expanduser()
    if not manifest_path.is_absolute():
        manifest_path = request.workspace_root / manifest_path
    return manifest_path.resolve()


def _has_explicit_semantic_ontology_package_catalog(
    context: Mapping[str, object],
) -> bool:
    return SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY in context


def _package_entries_by_manifest_path_for_request(
    *,
    request: SemanticPackageMaterializationRuntimeContextRequest,
    manifest_paths: tuple[Path, ...],
    source_module_ontology_manifest_paths: tuple[Path, ...],
) -> dict[Path, MetaRuntimePackageIndexEntry] | None:
    if not _has_explicit_semantic_ontology_package_catalog(request.context):
        return None
    entries_by_name = semantic_ontology_package_catalog_entries_by_name(
        context=request.context,
        repo_root=request.repo_root,
    )
    selected_paths = {path.expanduser().resolve() for path in manifest_paths}
    entries = {
        entry.manifest_path.expanduser().resolve(): MetaRuntimePackageIndexEntry(
            module_id=entry.module_id,
            package_name=entry.package_name,
            fqn_prefix=entry.fqn_prefix,
            manifest_path=entry.manifest_path.expanduser().resolve(),
            dependency_package_names=entry.dependency_package_names,
            projection_names=entry.projection_names,
        )
        for entry in entries_by_name.values()
        if entry.manifest_path.expanduser().resolve() in selected_paths
    }
    source_module_ontology_paths = {
        path.expanduser().resolve() for path in source_module_ontology_manifest_paths
    }
    for manifest_path in selected_paths.intersection(source_module_ontology_paths):
        if manifest_path in entries:
            continue
        local_entry = _local_ontology_package_index_entry(
            manifest_path=manifest_path,
        )
        if local_entry is not None:
            entries[manifest_path] = local_entry
    return entries


def _package_cache_owner_roots_by_manifest_path_for_request(
    *,
    request: SemanticPackageMaterializationRuntimeContextRequest,
    manifest_paths: tuple[Path, ...],
    source_module_ontology_manifest_paths: tuple[Path, ...],
) -> dict[Path, Path]:
    if not _has_explicit_semantic_ontology_package_catalog(request.context):
        return {}
    raw_catalog = request.context.get(SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY)
    if not isinstance(raw_catalog, Mapping):
        return {}
    raw_entries = raw_catalog.get("entries")
    if not isinstance(raw_entries, list):
        return {}
    selected_paths = {path.expanduser().resolve() for path in manifest_paths}
    owner_roots: dict[Path, Path] = {}
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, Mapping):
            continue
        manifest_path = _catalog_path(
            value=raw_entry.get("manifest_path"),
            default_root=request.repo_root,
        )
        if manifest_path is None or manifest_path not in selected_paths:
            continue
        owner_root = _catalog_path(
            value=raw_entry.get("owner_root"),
            default_root=request.repo_root,
        )
        owner_roots[manifest_path] = owner_root or request.repo_root.resolve()
    source_module_ontology_paths = {
        path.expanduser().resolve() for path in source_module_ontology_manifest_paths
    }
    for manifest_path in selected_paths.intersection(source_module_ontology_paths):
        if manifest_path in owner_roots:
            continue
        module_toml_path = nearest_module_toml_path(manifest_path)
        owner_roots[manifest_path] = (
            module_toml_path.parent.resolve()
            if module_toml_path is not None
            else request.workspace_root.resolve()
        )
    return owner_roots


def _local_ontology_package_index_entry(
    *,
    manifest_path: Path,
) -> MetaRuntimePackageIndexEntry | None:
    package_ref = source_module_ontology_package_ref_from_manifest(manifest_path)
    if package_ref is None:
        return None
    return MetaRuntimePackageIndexEntry(
        module_id=package_ref.module_id,
        package_name=package_ref.package_name,
        fqn_prefix=package_ref.fqn_prefix,
        manifest_path=package_ref.manifest_path,
        dependency_package_names=package_ref.dependency_package_names,
    )


def _catalog_path(*, value: object, default_root: Path) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value.strip()).expanduser()
    if not path.is_absolute():
        path = default_root / path
    return path.resolve()


def _clean_string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    if not isinstance(value, Iterable):
        return ()
    return tuple(
        dict.fromkeys(
            item for raw_item in value for item in (str(raw_item).strip(),) if item
        )
    )


__all__ = ["build_experience_workspace_materialization_runtime_context"]
