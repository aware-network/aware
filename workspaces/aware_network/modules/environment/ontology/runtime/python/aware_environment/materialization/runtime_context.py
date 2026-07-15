from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from aware_code.semantic_materialization import (
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY,
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
    SemanticPackageMaterializationRuntimeContextRequest,
)
from aware_meta.runtime.graph_context import (
    MetaGraphRuntimeContext,
    build_meta_graph_runtime_context_for_aware_package_manifests,
    resolve_workspace_required_projection_package_manifest_paths,
)
from aware_meta.runtime.graph_lane import bind_meta_graph_runtime_lane
from aware_meta.runtime.invocation_engine import (
    MetaGraphCommitReceipt,
    MetaGraphInvokeFunctionInput,
)
from aware_environment.materialization.service import (
    _DiscoveredEnvironmentSemanticPackageSpec,
    _discover_environment_semantic_package_specs,
    _environment_semantic_package_selector_names,
    _filter_environment_semantic_package_specs,
    _semantic_catalog_external_dependency_package_names,
)


@dataclass(frozen=True, slots=True)
class EnvironmentWorkspaceMaterializationRuntimeContext:
    """Environment-owned runtime context backed by Meta graph runtime truth."""

    meta_context: MetaGraphRuntimeContext
    runtime: "EnvironmentWorkspaceSemanticRuntime"
    actor_id: UUID | None = None

    @property
    def index(self) -> object:
        return self.meta_context.index

    @property
    def phase_timings_s(self) -> Mapping[str, float]:
        return self.meta_context.phase_timings_s

    @property
    def package_timings(self) -> object:
        return self.meta_context.package_timings

    @property
    def runtime_object_config_graphs(self) -> tuple[object, ...]:
        return tuple(self.meta_context.runtime_graphs)

    @property
    def semantic_object_config_graphs(self) -> tuple[object, ...]:
        return tuple(self.meta_context.source_graphs)

    @property
    def runtime_object_config_graphs_by_package_name(self) -> Mapping[str, object]:
        return self.meta_context.runtime_graph_by_package_name

    @property
    def semantic_object_config_graphs_by_package_name(self) -> Mapping[str, object]:
        return self.meta_context.source_graph_by_package_name

    def projection_hash_for_name(self, projection_name: str) -> str:
        return self.meta_context.projection_hash_for_name(projection_name)

    def bind_lane(
        self,
        *,
        projection: str,
        branch_id: UUID,
    ) -> object:
        return bind_meta_graph_runtime_lane(
            runtime=self.runtime,
            context=self.meta_context,
            branch_id=branch_id,
            projection=projection,
            actor_id=self.actor_id,
        )


@dataclass(frozen=True, slots=True)
class EnvironmentWorkspaceSemanticRuntime:
    """Fail-closed Meta graph runtime boundary for direct materialization providers."""

    async def invoke_function(
        self,
        request: MetaGraphInvokeFunctionInput,
    ) -> MetaGraphCommitReceipt:
        _ = request
        raise RuntimeError(
            "Workspace semantic materialization is using the Environment/Meta graph "
            "runtime context. Function-call invocation is unavailable on this "
            "rail; the provider must use direct snapshot materialization or the "
            "Meta graph executor."
        )


@dataclass(frozen=True, slots=True)
class _EnvironmentSemanticCatalog:
    module_names: tuple[str, ...]
    ontology_manifest_paths: tuple[str, ...]


async def build_environment_workspace_materialization_runtime_context(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> EnvironmentWorkspaceMaterializationRuntimeContext | None:
    """Build the Workspace materialization runtime context under Environment ownership."""

    runtime_package_names = _runtime_context_ontology_package_names(request)
    if not runtime_package_names:
        return None
    package_manifest_paths = _semantic_package_manifest_paths_for_request(
        request=request,
        runtime_package_names=runtime_package_names,
    )
    if not package_manifest_paths:
        return None

    meta_context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=package_manifest_paths,
        workspace_root=request.workspace_root,
        composite_name="Aware Workspace Semantic Materialization Context",
    )
    return EnvironmentWorkspaceMaterializationRuntimeContext(
        meta_context=meta_context,
        runtime=EnvironmentWorkspaceSemanticRuntime(),
        actor_id=request.actor_id,
    )


def _semantic_package_manifest_paths_for_request(
    *,
    request: SemanticPackageMaterializationRuntimeContextRequest,
    runtime_package_names: tuple[str, ...],
) -> tuple[Path, ...]:
    runtime_package_names = _clean_string_tuple(runtime_package_names)
    required_projection_manifest_paths = (
        resolve_workspace_required_projection_package_manifest_paths(request)
    )
    environment_catalog = _environment_semantic_catalog_from_request(request)
    explicit_catalog_specs = _semantic_package_specs_from_explicit_catalog(
        request=request,
    )
    if explicit_catalog_specs is not None:
        return _semantic_package_manifest_paths_from_specs(
            required_projection_manifest_paths=required_projection_manifest_paths,
            specs=explicit_catalog_specs,
            environment_catalog=environment_catalog,
            runtime_package_names=runtime_package_names,
        )
    selector_module_names = _clean_string_tuple(
        (
            *environment_catalog.module_names,
            *_compatibility_module_names_from_ontology_package_names(
                runtime_package_names
            ),
        )
    )
    if not selector_module_names and not environment_catalog.ontology_manifest_paths:
        return required_projection_manifest_paths

    specs = _discover_environment_semantic_package_specs(
        workspace_root=request.workspace_root,
        module_names=selector_module_names,
        ontology_manifest_paths=environment_catalog.ontology_manifest_paths,
        available_dependency_package_names=(
            _semantic_catalog_external_dependency_package_names(
                workspace_root=request.workspace_root,
                semantic_ontology_package_catalog=request.context.get(
                    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY
                ),
            )
        ),
    )
    return _semantic_package_manifest_paths_from_specs(
        required_projection_manifest_paths=required_projection_manifest_paths,
        specs=specs,
        environment_catalog=environment_catalog,
        runtime_package_names=runtime_package_names,
    )


def _semantic_package_manifest_paths_from_specs(
    *,
    required_projection_manifest_paths: tuple[Path, ...],
    specs: tuple[_DiscoveredEnvironmentSemanticPackageSpec, ...],
    environment_catalog: _EnvironmentSemanticCatalog,
    runtime_package_names: tuple[str, ...],
) -> tuple[Path, ...]:
    selected_package_names = _selected_runtime_package_names(
        specs=specs,
        environment_catalog=environment_catalog,
        runtime_package_names=runtime_package_names,
    )
    specs = _filter_environment_semantic_package_specs(
        semantic_package_specs=specs,
        selected_package_names=selected_package_names,
    )
    return _dedupe_manifest_paths(
        (
            *required_projection_manifest_paths,
            *(spec.aware_toml_path for spec in specs),
        )
    )


def _semantic_package_specs_from_explicit_catalog(
    *,
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> tuple[_DiscoveredEnvironmentSemanticPackageSpec, ...] | None:
    raw_catalog = request.context.get(SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY)
    if raw_catalog is None:
        return None
    if not isinstance(raw_catalog, Mapping):
        raise ValueError(
            "Environment runtime ontology package catalog must be a mapping."
        )
    if raw_catalog.get("schema") != SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA:
        raise ValueError(
            "Environment runtime ontology package catalog has an unsupported schema."
        )
    raw_entries = raw_catalog.get("entries")
    if not isinstance(raw_entries, list):
        raise ValueError(
            "Environment runtime ontology package catalog must include an entries list."
        )
    specs = tuple(
        _semantic_package_spec_from_catalog_entry(
            request=request,
            payload=raw_entry,
        )
        for raw_entry in raw_entries
        if isinstance(raw_entry, Mapping)
    )
    if len(specs) != len(raw_entries):
        raise ValueError(
            "Environment runtime ontology package catalog entries must be mappings."
        )
    return tuple(
        sorted(
            specs,
            key=lambda spec: (
                spec.module_name.casefold(),
                spec.manifest_relative_path,
                spec.package_name.casefold(),
            ),
        )
    )


def _semantic_package_spec_from_catalog_entry(
    *,
    request: SemanticPackageMaterializationRuntimeContextRequest,
    payload: Mapping[str, object],
) -> _DiscoveredEnvironmentSemanticPackageSpec:
    module_id = _required_catalog_string(payload=payload, key="module_id")
    package_name = _required_catalog_string(payload=payload, key="package_name")
    fqn_prefix = _required_catalog_string(payload=payload, key="fqn_prefix")
    manifest_path = _catalog_manifest_path(request=request, payload=payload)
    owner_root = _catalog_owner_root(request=request, payload=payload)
    manifest_relative_path = _catalog_manifest_relative_path(
        owner_root=owner_root,
        manifest_path=manifest_path,
    )
    package_root = manifest_path.parent.as_posix()
    return _DiscoveredEnvironmentSemanticPackageSpec(
        module_name=_catalog_module_name(
            module_id=module_id,
            package_name=package_name,
        ),
        aware_toml_path=manifest_path,
        ontology_manifest_path=None,
        source_manifest_path=manifest_relative_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        dependency_package_names=_clean_string_tuple(
            payload.get("dependency_package_names")
        ),
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        workspace_package_root=package_root,
        sources_root=None,
        surface="structure",
    )


def _catalog_manifest_path(
    *,
    request: SemanticPackageMaterializationRuntimeContextRequest,
    payload: Mapping[str, object],
) -> Path:
    manifest_path_text = _required_catalog_string(
        payload=payload,
        key="manifest_path",
    )
    manifest_path = Path(manifest_path_text).expanduser()
    if manifest_path.is_absolute():
        return manifest_path.resolve()
    return (
        _catalog_owner_root(request=request, payload=payload) / manifest_path
    ).resolve()


def _catalog_owner_root(
    *,
    request: SemanticPackageMaterializationRuntimeContextRequest,
    payload: Mapping[str, object],
) -> Path:
    owner_root_text = _optional_catalog_string(payload=payload, key="owner_root")
    if owner_root_text is None:
        return request.repo_root.expanduser().resolve()
    return Path(owner_root_text).expanduser().resolve()


def _catalog_manifest_relative_path(
    *,
    owner_root: Path,
    manifest_path: Path,
) -> str:
    try:
        return manifest_path.resolve().relative_to(owner_root.resolve()).as_posix()
    except ValueError:
        return manifest_path.resolve().as_posix()


def _catalog_module_name(*, module_id: str, package_name: str) -> str:
    if ":" not in module_id and module_id.strip():
        return module_id.strip()
    compatibility_names = _compatibility_module_names_from_ontology_package_names(
        (package_name,),
    )
    return compatibility_names[0] if compatibility_names else module_id.strip()


def _required_catalog_string(*, payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Environment runtime ontology package catalog entry missing {key!r}."
        )
    return value.strip()


def _optional_catalog_string(*, payload: Mapping[str, object], key: str) -> str | None:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _selected_runtime_package_names(
    *,
    specs: tuple[object, ...],
    environment_catalog: _EnvironmentSemanticCatalog,
    runtime_package_names: tuple[str, ...],
) -> tuple[str, ...]:
    environment_module_names = set(environment_catalog.module_names)
    environment_package_names = tuple(
        str(getattr(spec, "package_name", "")).strip()
        for spec in specs
        if (
            environment_catalog.ontology_manifest_paths
            or str(getattr(spec, "module_name", "")).strip() in environment_module_names
        )
        if str(getattr(spec, "package_name", "")).strip()
    )
    return tuple(dict.fromkeys((*runtime_package_names, *environment_package_names)))


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


def _environment_semantic_catalog_from_request(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> _EnvironmentSemanticCatalog:
    manifest_path = request.manifest_path
    if manifest_path is None or not manifest_path.is_file():
        return _EnvironmentSemanticCatalog(module_names=(), ontology_manifest_paths=())
    from aware_environment.manifest import (  # noqa: WPS433
        load_aware_environment_spec,
    )

    spec = load_aware_environment_spec(toml_path=manifest_path)
    return _EnvironmentSemanticCatalog(
        module_names=_environment_semantic_package_selector_names(
            workspace_root=request.workspace_root,
            spec=spec,
        ),
        ontology_manifest_paths=_clean_string_tuple(spec.ontologies),
    )


def _compatibility_module_names_from_ontology_package_names(
    package_names: Iterable[str],
) -> tuple[str, ...]:
    module_names: list[str] = []
    for package_name in _clean_string_tuple(package_names):
        if not package_name.endswith("-ontology"):
            continue
        module_name = package_name[: -len("-ontology")].strip()
        if module_name:
            module_names.append(module_name)
    return tuple(dict.fromkeys(module_names))


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


def _dedupe_manifest_paths(paths: Iterable[Path]) -> tuple[Path, ...]:
    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.expanduser().resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(resolved)
    return tuple(deduped)


__all__ = [
    "EnvironmentWorkspaceMaterializationRuntimeContext",
    "EnvironmentWorkspaceSemanticRuntime",
    "build_environment_workspace_materialization_runtime_context",
]
