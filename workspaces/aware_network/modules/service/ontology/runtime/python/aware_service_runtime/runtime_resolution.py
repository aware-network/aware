from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
from time import perf_counter
from typing import cast
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_api_runtime.packages.materialization import (
    build_api_accessible_dependency_graphs,
)
from aware_api_runtime.ontology_graph.ontology import (
    APIOntologyPlan,
    decode_api_ontology_plan_payload,
    encode_api_ontology_plan_payload,
)
from aware_api_runtime.dependencies.runtime_resolution import (
    API_ACCESSIBLE_DEPENDENCY_GRAPHS_FILENAME,
    API_RUNTIME_SEMANTICS_FILENAME,
    RuntimeImportActivationPlan as APIRuntimeImportActivationPlan,
    RuntimeManifestResolution as APIRuntimeManifestResolution,
    load_api_accessible_dependency_graphs_from_runtime_artifact,
)
from aware_api_runtime.workspace import APIWorkspace
from aware_service_runtime.manifest.loader import load_aware_service_toml_spec
from aware_service_runtime.workspace_dependency_roots import (
    api_service_protocol_dependency_roots,
    declared_workspace_dependency_roots,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_orm.db.schema_registry import (
    compute_sql_root_source_hash,
    load_db_schema_registry,
)
from aware_utils.logging import logger


@dataclass(frozen=True, slots=True)
class RuntimeImportActivationPlan:
    roots: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class RuntimeManifestResolution:
    manifest_path: Path
    module_ids: tuple[str, ...]
    module_manifest_paths: tuple[Path, ...]
    python_roots: tuple[Path, ...]
    import_activation: RuntimeImportActivationPlan
    environment_handle: str
    runtime_bundle_manifest_paths: tuple[Path, ...] = ()
    environment_config_id: UUID | None = None

    @property
    def import_roots(self) -> tuple[Path, ...]:
        return self.import_activation.roots


def build_runtime_import_activation_plan(
    *,
    roots: Iterable[Path],
) -> RuntimeImportActivationPlan:
    normalized: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        resolved = root.resolve()
        if not resolved.exists():
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        normalized.append(resolved)
    return RuntimeImportActivationPlan(roots=tuple(normalized))


class RuntimeRequirementsError(RuntimeError):
    """Raised when Service runtime manifest resolution cannot compose requirements."""


def service_protocol_api_reference_branch_id(branch_key: str) -> UUID:
    return uuid5(
        NAMESPACE_URL,
        f"aware-service-host:service-protocol-api-reference:{branch_key}",
    )


def resolve_module_runtime_manifest(**kwargs: object) -> RuntimeManifestResolution:
    """Resolve core module runtime sources through ontology-owned artifacts.

    The old implementation wrote a Structure-composed Environment manifest as a
    convenience side effect. Service runtime consumers now receive the same
    shaped resolution object, but its manifests are ontology runtime bundle
    manifests instead of composed Environment manifests.
    """

    return resolve_module_runtime_artifact_sources(**kwargs)


def resolve_module_runtime_artifact_sources(
    **kwargs: object,
) -> RuntimeManifestResolution:
    """Resolve prepared module runtime artifacts without scanning Structure topology."""

    raw_manifest_paths = kwargs.get("runtime_bundle_manifest_paths")
    if raw_manifest_paths is None:
        raw_manifest_paths = kwargs.get("module_manifest_paths")
    if raw_manifest_paths is None:
        raise RuntimeRequirementsError(
            "Service runtime module closure through Structure topology is retired. "
            "Pass prepared runtime_bundle_manifest_paths/import_roots from a "
            "WorkspaceRevision or consume service-protocol API runtime artifacts."
        )

    runtime_bundle_manifest_paths = _coerce_path_tuple(
        raw_manifest_paths,
        field_name="runtime_bundle_manifest_paths",
    )
    _require_module_manifests(runtime_bundle_manifest_paths)

    raw_module_ids = kwargs.get("module_ids", ())
    module_ids = tuple(_normalize_text_items(raw_module_ids, field_name="module_ids"))
    environment_handle = kwargs.get("environment_handle")
    env_handle = (
        str(environment_handle).strip()
        if environment_handle is not None
        else "prepared-runtime-artifacts"
    )
    if not env_handle:
        env_handle = "prepared-runtime-artifacts"
    output_path = kwargs.get("output_path")
    manifest_path = (
        Path(output_path).expanduser().resolve()
        if output_path is not None
        else runtime_bundle_manifest_paths[0]
    )
    python_roots = _coerce_path_tuple(
        kwargs.get("python_roots", ()),
        field_name="python_roots",
        require_exists=False,
    )
    import_roots = _coerce_path_tuple(
        kwargs.get("import_roots", python_roots),
        field_name="import_roots",
        require_exists=False,
    )
    import_activation = build_runtime_import_activation_plan(roots=import_roots)
    return RuntimeManifestResolution(
        manifest_path=manifest_path,
        module_ids=module_ids,
        module_manifest_paths=tuple(runtime_bundle_manifest_paths),
        python_roots=tuple(python_roots),
        import_activation=import_activation,
        environment_handle=env_handle,
        runtime_bundle_manifest_paths=tuple(runtime_bundle_manifest_paths),
        environment_config_id=_stable_runtime_source_environment_config_id(
            environment_handle=env_handle,
            runtime_bundle_manifest_paths=runtime_bundle_manifest_paths,
        ),
    )


@dataclass(frozen=True, slots=True)
class ServiceProtocolApiDependencyRuntime:
    package_name: str
    repo_root: Path
    api_manifest_path: Path
    api_toml_path: Path
    service_protocol_plan_path: Path
    service_protocol_plan_hash_sha256: str
    api_compile_plan_path: Path
    api_toml_relpath: str | None = None


@dataclass(frozen=True, slots=True)
class ServiceProtocolRuntimeResolution:
    manifest_path: Path
    runtime_resolution: RuntimeManifestResolution
    api_dependencies: tuple[ServiceProtocolApiDependencyRuntime, ...]
    cache_status: str = "disabled"
    cache_metadata_path: Path | None = None
    cache_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ServiceProtocolApiReferenceMaterializationInput:
    package_name: str
    api_toml_path: Path
    api_compile_plan_path: Path
    compile_plan_payload: dict[str, object]
    accessible_graphs: tuple[ObjectConfigGraph, ...]
    accessible_graphs_hash: str | None = None


@dataclass(frozen=True, slots=True)
class ServiceProtocolApiReferenceLaneInput:
    package_name: str
    api_name: str
    api_source_path: str
    branch_key: str
    compile_plan_payload: dict[str, object]
    accessible_graphs: tuple[ObjectConfigGraph, ...]
    projection_refs: frozenset[str]
    endpoint_refs: frozenset[str]
    endpoint_function_refs: frozenset[str]


@dataclass(frozen=True, slots=True)
class _APIRuntimeResolutionResult:
    resolution: APIRuntimeManifestResolution
    source: str
    reason: str | None = None


def resolve_service_protocol_runtime_manifest(
    *,
    toml_paths: Sequence[str | Path],
    dependency_payloads: Sequence[Mapping[str, object]] | None = None,
    repo_root: str | Path | None = None,
    kernel_repo_root: str | Path | None = None,
    output_path: str | Path | None = None,
    use_cache: bool = True,
) -> ServiceProtocolRuntimeResolution | None:
    """Resolve the runtime needed to serve pinned API service-protocol dependencies."""

    resolved_toml_paths = tuple(
        Path(path).expanduser().resolve() for path in toml_paths
    )
    if not resolved_toml_paths:
        return None

    resolved_repo_root = _resolve_repo_root(
        toml_paths=resolved_toml_paths,
        repo_root=repo_root,
    )
    resolved_kernel_repo_root = (
        Path(kernel_repo_root).expanduser().resolve()
        if kernel_repo_root is not None
        else resolved_repo_root
    )
    dependencies = (
        _resolve_api_service_protocol_dependency_payloads(
            dependencies=dependency_payloads,
            repo_root=resolved_repo_root,
            additional_repo_roots=(
                resolved_kernel_repo_root,
                *(
                    tuple(
                        _resolve_repo_root(
                            toml_paths=(toml_path,),
                            repo_root=None,
                        )
                        for toml_path in resolved_toml_paths
                    )
                    if repo_root is None
                    else ()
                ),
            ),
        )
        if dependency_payloads is not None
        else _resolve_api_service_protocol_dependencies(
            toml_paths=resolved_toml_paths,
            repo_root=resolved_repo_root,
            kernel_repo_root=resolved_kernel_repo_root,
            use_explicit_repo_root=repo_root is not None,
        )
    )
    if not dependencies:
        return None

    manifest_repo_root = (
        resolved_kernel_repo_root
        if resolved_repo_root.resolve() != resolved_kernel_repo_root.resolve()
        else resolved_repo_root
    )
    manifest_path = (
        Path(output_path).expanduser().resolve()
        if output_path is not None
        else _default_runtime_manifest_output_path(
            repo_root=manifest_repo_root,
            dependencies=dependencies,
        )
    )
    cache_metadata_path = _runtime_manifest_cache_metadata_path(manifest_path)
    fast_cache_key = _service_protocol_runtime_fast_cache_key(
        toml_paths=resolved_toml_paths,
        repo_root=resolved_repo_root,
        kernel_repo_root=resolved_kernel_repo_root,
        manifest_repo_root=manifest_repo_root,
        dependencies=dependencies,
    )
    if use_cache:
        cached_runtime_resolution, cache_reason = (
            _load_cached_service_protocol_runtime_resolution_fast(
                cache_metadata_path=cache_metadata_path,
                fast_cache_key=fast_cache_key,
                manifest_path=manifest_path,
            )
        )
        if cached_runtime_resolution is not None:
            return ServiceProtocolRuntimeResolution(
                manifest_path=manifest_path,
                runtime_resolution=cached_runtime_resolution,
                api_dependencies=dependencies,
                cache_status="hit",
                cache_metadata_path=cache_metadata_path,
                cache_reason=cache_reason,
            )

    api_resolution_results = tuple(
        _resolve_api_dependency_runtime_resolution(
            dependency=dependency,
            allowed_runtime_roots=_service_runtime_allowed_roots(
                service_repo_root=resolved_repo_root,
                kernel_repo_root=resolved_kernel_repo_root,
            ),
        )
        for dependency in dependencies
    )
    api_resolutions = tuple(result.resolution for result in api_resolution_results)
    logger.info(
        "Service protocol API runtime resolutions loaded: %s",
        tuple(
            {
                "package": dependency.package_name,
                "source": result.source,
                "reason": result.reason,
                "manifest": result.resolution.manifest_path.as_posix(),
            }
            for dependency, result in zip(dependencies, api_resolution_results)
        ),
    )

    cache_key = _service_protocol_runtime_cache_key(
        toml_paths=resolved_toml_paths,
        repo_root=resolved_repo_root,
        kernel_repo_root=resolved_kernel_repo_root,
        manifest_repo_root=manifest_repo_root,
        dependencies=dependencies,
        api_resolutions=api_resolutions,
    )
    if use_cache:
        cached_runtime_resolution, cache_reason = (
            _load_cached_service_protocol_runtime_resolution(
                cache_metadata_path=cache_metadata_path,
                cache_key=cache_key,
                manifest_path=manifest_path,
            )
        )
        if cached_runtime_resolution is not None:
            return ServiceProtocolRuntimeResolution(
                manifest_path=manifest_path,
                runtime_resolution=cached_runtime_resolution,
                api_dependencies=dependencies,
                cache_status="hit",
                cache_metadata_path=cache_metadata_path,
                cache_reason=cache_reason,
            )
    else:
        cache_reason = "cache_disabled"

    combined_runtime_bundle_manifest_paths: tuple[Path, ...] = ()
    combined_python_roots = _dedupe_paths(
        [
            *(
                python_root
                for api_resolution in api_resolutions
                for python_root in api_resolution.python_roots
            ),
        ]
    )
    import_activation = build_runtime_import_activation_plan(
        roots=_dedupe_paths(
            [
                *(
                    root
                    for api_resolution in api_resolutions
                    for root in api_resolution.import_activation.roots
                ),
            ]
        )
    )
    environment_handle = _environment_handle(dependencies=dependencies)
    environment_config_id = _stable_runtime_source_environment_config_id(
        environment_handle=environment_handle,
        runtime_bundle_manifest_paths=combined_runtime_bundle_manifest_paths,
    )
    runtime_resolution = RuntimeManifestResolution(
        manifest_path=manifest_path,
        module_ids=(),
        module_manifest_paths=tuple(combined_runtime_bundle_manifest_paths),
        python_roots=tuple(combined_python_roots),
        import_activation=import_activation,
        environment_handle=environment_handle,
        runtime_bundle_manifest_paths=tuple(combined_runtime_bundle_manifest_paths),
        environment_config_id=environment_config_id,
    )
    _write_service_protocol_runtime_source_descriptor(
        path=manifest_path,
        runtime_resolution=runtime_resolution,
        dependencies=dependencies,
    )
    if use_cache:
        _write_service_protocol_runtime_manifest_cache(
            cache_metadata_path=cache_metadata_path,
            cache_key=cache_key,
            runtime_resolution=runtime_resolution,
        )
    return ServiceProtocolRuntimeResolution(
        manifest_path=manifest_path,
        runtime_resolution=runtime_resolution,
        api_dependencies=dependencies,
        cache_status="miss" if use_cache else "disabled",
        cache_metadata_path=cache_metadata_path if use_cache else None,
        cache_reason=cache_reason,
    )


def load_service_protocol_api_compile_plan_payloads(
    *,
    toml_paths: Sequence[str | Path],
    repo_root: str | Path | None = None,
) -> tuple[dict[str, object], ...]:
    resolved_toml_paths = tuple(
        Path(path).expanduser().resolve() for path in toml_paths
    )
    if not resolved_toml_paths:
        return ()
    resolved_repo_root = _resolve_repo_root(
        toml_paths=resolved_toml_paths,
        repo_root=repo_root,
    )
    return tuple(
        _load_json_mapping(dependency.api_compile_plan_path)
        for dependency in _resolve_api_service_protocol_dependencies(
            toml_paths=resolved_toml_paths,
            repo_root=resolved_repo_root,
        )
    )


def _resolve_api_dependency_runtime_resolution(
    *,
    dependency: ServiceProtocolApiDependencyRuntime,
    allowed_runtime_roots: tuple[Path, ...],
) -> _APIRuntimeResolutionResult:
    started_at = perf_counter()
    artifact_resolution, artifact_reason = (
        _load_api_dependency_runtime_resolution_from_artifact(
            dependency=dependency,
            allowed_runtime_roots=allowed_runtime_roots,
        )
    )
    if artifact_resolution is not None:
        duration_s = max(perf_counter() - started_at, 0.0)
        logger.info(
            "Service protocol API runtime resolution loaded from artifact: "
            "package=%s manifest=%s python_roots=%d import_roots=%d duration=%.6fs",
            dependency.package_name,
            artifact_resolution.manifest_path,
            len(artifact_resolution.python_roots),
            len(artifact_resolution.import_activation.roots),
            duration_s,
        )
        return _APIRuntimeResolutionResult(
            resolution=artifact_resolution,
            source="runtime_semantics_artifact",
        )

    raise RuntimeRequirementsError(
        "Service protocol API runtime resolution requires a prepared "
        f"{API_RUNTIME_SEMANTICS_FILENAME} artifact for dependency "
        f"{dependency.package_name!r}: "
        f"{dependency.api_manifest_path.parent / API_RUNTIME_SEMANTICS_FILENAME} "
        f"(reason={artifact_reason})"
    )


def _load_api_dependency_runtime_resolution_from_artifact(
    *,
    dependency: ServiceProtocolApiDependencyRuntime,
    allowed_runtime_roots: tuple[Path, ...],
) -> tuple[APIRuntimeManifestResolution | None, str | None]:
    runtime_semantics_path = (
        dependency.api_manifest_path.parent / API_RUNTIME_SEMANTICS_FILENAME
    ).resolve()
    if not runtime_semantics_path.is_file():
        return None, "runtime_semantics_missing"
    try:
        payload = _load_json_mapping(runtime_semantics_path)
        if payload.get("kind") != "api.runtime_semantics":
            return None, "runtime_semantics_kind_mismatch"
        package_name = str(payload.get("api_package_name") or "").strip()
        if package_name != dependency.package_name:
            return None, "runtime_semantics_package_mismatch"
        api_toml_relpath = _require_runtime_semantics_relpath_field(
            payload,
            key="api_toml_relpath",
            manifest_path=runtime_semantics_path,
        )
        if dependency.api_toml_relpath is not None:
            if api_toml_relpath != dependency.api_toml_relpath:
                return None, "runtime_semantics_api_toml_mismatch"
        else:
            api_toml_path = _resolve_runtime_semantics_path_field(
                payload,
                key="api_toml_relpath",
                repo_root=dependency.repo_root,
                manifest_path=runtime_semantics_path,
            )
            if api_toml_path != dependency.api_toml_path.resolve():
                return None, "runtime_semantics_api_toml_mismatch"
        raw_dependency_packages = payload.get("dependency_packages")
        if not isinstance(raw_dependency_packages, list):
            return None, "runtime_semantics_dependency_packages_invalid"

        python_roots: list[Path] = []
        runtime_roots: list[Path] = []
        for raw_package in raw_dependency_packages:
            if not isinstance(raw_package, Mapping):
                return None, "runtime_semantics_dependency_package_invalid"
            package_payload = cast(Mapping[str, object], raw_package)
            python_roots.append(
                _require_runtime_semantics_path_within_allowed_roots(
                    _resolve_runtime_semantics_path_field(
                        package_payload,
                        key="python_root_relpath",
                        repo_root=dependency.repo_root,
                        manifest_path=runtime_semantics_path,
                    ),
                    key="python_root_relpath",
                    manifest_path=runtime_semantics_path,
                    allowed_roots=allowed_runtime_roots,
                )
            )
            runtime_roots.append(
                _require_runtime_semantics_path_within_allowed_roots(
                    _resolve_runtime_semantics_path_field(
                        package_payload,
                        key="runtime_root_relpath",
                        repo_root=dependency.repo_root,
                        manifest_path=runtime_semantics_path,
                    ),
                    key="runtime_root_relpath",
                    manifest_path=runtime_semantics_path,
                    allowed_roots=allowed_runtime_roots,
                )
            )
            _require_runtime_semantics_path_within_allowed_roots(
                _resolve_runtime_semantics_path_field(
                    package_payload,
                    key="aware_toml_relpath",
                    repo_root=dependency.repo_root,
                    manifest_path=runtime_semantics_path,
                ),
                key="aware_toml_relpath",
                manifest_path=runtime_semantics_path,
                allowed_roots=allowed_runtime_roots,
            )
        resolved_python_roots = tuple(_dedupe_paths(python_roots))
        import_activation = APIRuntimeImportActivationPlan(
            roots=tuple(
                path
                for path in _dedupe_paths([*python_roots, *runtime_roots])
                if path.exists()
            )
        )
    except Exception as exc:
        return None, f"runtime_semantics_invalid:{exc}"
    return (
        APIRuntimeManifestResolution(
            manifest_path=runtime_semantics_path,
            module_ids=(),
            module_manifest_paths=(),
            python_roots=resolved_python_roots,
            import_activation=import_activation,
            environment_handle=f"{dependency.package_name}-runtime",
        ),
        None,
    )


def _resolve_runtime_semantics_path_field(
    payload: Mapping[str, object],
    *,
    key: str,
    repo_root: Path,
    manifest_path: Path,
) -> Path:
    raw_value = payload.get(key)
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise RuntimeError(
            f"API runtime semantics manifest requires non-empty string field "
            f"{key!r}: {manifest_path}"
        )
    path = Path(raw_value).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def _require_runtime_semantics_relpath_field(
    payload: Mapping[str, object],
    *,
    key: str,
    manifest_path: Path,
) -> str:
    raw_value = payload.get(key)
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise RuntimeError(
            f"API runtime semantics manifest requires non-empty string field "
            f"{key!r}: {manifest_path}"
        )
    return _normalize_portable_manifest_relpath(
        value=raw_value,
        key=key,
        manifest_path=manifest_path,
    )


def _require_runtime_semantics_path_within_allowed_roots(
    path: Path,
    *,
    key: str,
    manifest_path: Path,
    allowed_roots: tuple[Path, ...],
) -> Path:
    resolved = path.resolve()
    normalized_roots = tuple(
        dict.fromkeys(root.expanduser().resolve() for root in allowed_roots)
    )
    for root in normalized_roots:
        if _path_is_relative_to(resolved, root):
            return resolved
    roots = ", ".join(root.as_posix() for root in normalized_roots)
    raise RuntimeError(
        "API runtime semantics path escapes declared service runtime authority: "
        f"field={key!r} path={resolved.as_posix()} manifest={manifest_path} "
        f"allowed_roots=[{roots}]"
    )


def _path_is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def load_service_protocol_api_reference_materialization_inputs(
    *,
    toml_paths: Sequence[str | Path],
    repo_root: str | Path | None = None,
    kernel_repo_root: str | Path | None = None,
    hydrate_accessible_graphs: bool = True,
    package_names: Iterable[str] | None = None,
) -> tuple[ServiceProtocolApiReferenceMaterializationInput, ...]:
    resolved_toml_paths = tuple(
        Path(path).expanduser().resolve() for path in toml_paths
    )
    if not resolved_toml_paths:
        return ()
    resolved_repo_root = _resolve_repo_root(
        toml_paths=resolved_toml_paths,
        repo_root=repo_root,
    )
    resolved_kernel_repo_root = (
        Path(kernel_repo_root).expanduser().resolve()
        if kernel_repo_root is not None
        else None
    )
    return _load_service_protocol_api_reference_materialization_inputs_from_runtimes(
        dependencies=_resolve_api_service_protocol_dependencies(
            toml_paths=resolved_toml_paths,
            repo_root=resolved_repo_root,
            kernel_repo_root=resolved_kernel_repo_root,
        ),
        repo_root=resolved_repo_root,
        accessible_graph_source="runtime_artifact",
        hydrate_accessible_graphs=hydrate_accessible_graphs,
        package_names=package_names,
    )


def load_service_protocol_api_reference_materialization_inputs_from_dependencies(
    *,
    dependencies: Sequence[Mapping[str, object]],
    repo_root: str | Path,
    additional_repo_roots: Sequence[str | Path] = (),
    hydrate_accessible_graphs: bool = True,
    package_names: Iterable[str] | None = None,
    require_relational_lock: bool = True,
) -> tuple[ServiceProtocolApiReferenceMaterializationInput, ...]:
    resolved_repo_root = Path(repo_root).expanduser().resolve()
    return _load_service_protocol_api_reference_materialization_inputs_from_runtimes(
        dependencies=_resolve_api_service_protocol_dependency_payloads(
            dependencies=dependencies,
            repo_root=resolved_repo_root,
            additional_repo_roots=tuple(
                Path(root).expanduser().resolve() for root in additional_repo_roots
            ),
            require_relational_lock=require_relational_lock,
        ),
        repo_root=resolved_repo_root,
        accessible_graph_source="runtime_artifact",
        hydrate_accessible_graphs=hydrate_accessible_graphs,
        package_names=package_names,
    )


def load_service_protocol_api_reference_lane_inputs(
    *,
    toml_paths: Sequence[str | Path],
    repo_root: str | Path | None = None,
    kernel_repo_root: str | Path | None = None,
    hydrate_accessible_graphs: bool = True,
    package_names: Iterable[str] | None = None,
) -> tuple[ServiceProtocolApiReferenceLaneInput, ...]:
    return split_service_protocol_api_reference_lane_inputs(
        load_service_protocol_api_reference_materialization_inputs(
            toml_paths=toml_paths,
            repo_root=repo_root,
            kernel_repo_root=kernel_repo_root,
            hydrate_accessible_graphs=hydrate_accessible_graphs,
            package_names=package_names,
        )
    )


def load_service_protocol_api_reference_lane_inputs_from_dependencies(
    *,
    dependencies: Sequence[Mapping[str, object]],
    repo_root: str | Path,
    additional_repo_roots: Sequence[str | Path] = (),
    hydrate_accessible_graphs: bool = True,
    package_names: Iterable[str] | None = None,
    require_relational_lock: bool = True,
) -> tuple[ServiceProtocolApiReferenceLaneInput, ...]:
    return split_service_protocol_api_reference_lane_inputs(
        load_service_protocol_api_reference_materialization_inputs_from_dependencies(
            dependencies=dependencies,
            repo_root=repo_root,
            additional_repo_roots=additional_repo_roots,
            hydrate_accessible_graphs=hydrate_accessible_graphs,
            package_names=package_names,
            require_relational_lock=require_relational_lock,
        )
    )


def split_service_protocol_api_reference_lane_inputs(
    materialization_inputs: Iterable[ServiceProtocolApiReferenceMaterializationInput],
) -> tuple[ServiceProtocolApiReferenceLaneInput, ...]:
    references: list[ServiceProtocolApiReferenceLaneInput] = []
    for materialization_input in materialization_inputs:
        references.extend(
            _split_service_protocol_api_reference_lane_input(
                materialization_input=materialization_input
            )
        )
    return tuple(
        sorted(
            references,
            key=lambda item: (
                item.api_name.casefold(),
                item.branch_key.casefold(),
            ),
        )
    )


def _split_service_protocol_api_reference_lane_input(
    *,
    materialization_input: ServiceProtocolApiReferenceMaterializationInput,
) -> tuple[ServiceProtocolApiReferenceLaneInput, ...]:
    raw_api_ontology = materialization_input.compile_plan_payload.get("api_ontology")
    if not isinstance(raw_api_ontology, Sequence) or isinstance(
        raw_api_ontology, (str, bytes)
    ):
        return ()
    plans = decode_api_ontology_plan_payload(payload=raw_api_ontology)
    graph_hash = (
        materialization_input.accessible_graphs_hash
        or _accessible_graphs_hash(materialization_input.accessible_graphs)
    )
    references: list[ServiceProtocolApiReferenceLaneInput] = []
    for plan in plans:
        single_payload = _single_api_compile_plan_payload(
            payload=materialization_input.compile_plan_payload,
            plan=plan,
        )
        payload_hash = _canonical_json_sha256(single_payload)
        references.append(
            ServiceProtocolApiReferenceLaneInput(
                package_name=materialization_input.package_name,
                api_name=plan.api.name,
                api_source_path=plan.api.source_path,
                branch_key=(
                    "service-protocol-api:boot-v3:"
                    f"{materialization_input.package_name}:"
                    f"{plan.api.name}:{plan.api.source_path}:"
                    f"sha256:{payload_hash}:graphs:{graph_hash}"
                ),
                compile_plan_payload=single_payload,
                accessible_graphs=materialization_input.accessible_graphs,
                projection_refs=frozenset(row.target for row in plan.graph_projections),
                endpoint_refs=frozenset(
                    f"{row.api_name}.{row.capability_name}.{row.endpoint_name}"
                    for row in plan.capability_endpoint_request_configs
                ),
                endpoint_function_refs=frozenset(
                    f"{row.api_name}.{row.capability_name}."
                    f"{row.endpoint_name}.{row.name}"
                    for row in plan.capability_endpoint_functions
                ),
            )
        )
    return tuple(references)


def _single_api_compile_plan_payload(
    *,
    payload: Mapping[str, object],
    plan: APIOntologyPlan,
) -> dict[str, object]:
    single_payload = dict(payload)
    encoded_plans = encode_api_ontology_plan_payload(plans=(plan,))
    single_payload["api_ontology"] = [encoded_plans[0]]
    return single_payload


def _load_service_protocol_api_reference_materialization_inputs_from_runtimes(
    *,
    dependencies: tuple[ServiceProtocolApiDependencyRuntime, ...],
    repo_root: Path,
    dependency_repo_roots: Iterable[str | Path] = (),
    accessible_graph_source: str,
    hydrate_accessible_graphs: bool = True,
    package_names: Iterable[str] | None = None,
) -> tuple[ServiceProtocolApiReferenceMaterializationInput, ...]:
    inputs: list[ServiceProtocolApiReferenceMaterializationInput] = []
    requested_package_names = (
        frozenset(name.strip() for name in package_names if name.strip())
        if package_names is not None
        else None
    )
    for dependency in dependencies:
        if (
            requested_package_names is not None
            and dependency.package_name not in requested_package_names
        ):
            continue
        started_at = perf_counter()
        logger.info(
            "Service protocol API reference input loading started: "
            "package=%s api_toml=%s compile_plan=%s",
            dependency.package_name,
            dependency.api_toml_path,
            dependency.api_compile_plan_path,
        )
        compile_plan_payload = _load_json_mapping(dependency.api_compile_plan_path)
        accessible_graphs_hash: str | None = None
        if accessible_graph_source == "runtime_artifact":
            accessible_graphs_hash = _hash_api_accessible_dependency_graphs_artifact(
                runtime_package_dir=dependency.api_manifest_path.parent,
            )
            accessible_graphs = (
                load_api_accessible_dependency_graphs_from_runtime_artifact(
                    runtime_package_dir=dependency.api_manifest_path.parent,
                )
                if hydrate_accessible_graphs
                else ()
            )
        elif accessible_graph_source == "source":
            snapshot = APIWorkspace.from_toml(
                toml_path=dependency.api_toml_path,
                repo_root=repo_root,
            ).build_snapshot()
            accessible_graphs = build_api_accessible_dependency_graphs(
                snapshot=snapshot,
                dependency_repo_roots=dependency_repo_roots,
            )
        else:
            raise RuntimeError(
                "Invalid service protocol API reference accessible graph source: "
                f"{accessible_graph_source!r}"
            )
        duration_s = max(perf_counter() - started_at, 0.0)
        logger.info(
            "Service protocol API reference input loaded: package=%s "
            "accessible_graphs=%s accessible_graphs_hash=%s duration=%.6fs",
            dependency.package_name,
            _object_config_graph_names(accessible_graphs),
            accessible_graphs_hash,
            duration_s,
        )
        inputs.append(
            ServiceProtocolApiReferenceMaterializationInput(
                package_name=dependency.package_name,
                api_toml_path=dependency.api_toml_path,
                api_compile_plan_path=dependency.api_compile_plan_path,
                compile_plan_payload=compile_plan_payload,
                accessible_graphs=accessible_graphs,
                accessible_graphs_hash=accessible_graphs_hash,
            )
        )
    return tuple(inputs)


def _hash_api_accessible_dependency_graphs_artifact(
    *,
    runtime_package_dir: str | Path,
) -> str:
    artifact_path = (
        Path(runtime_package_dir).expanduser().resolve()
        / API_ACCESSIBLE_DEPENDENCY_GRAPHS_FILENAME
    )
    if not artifact_path.is_file():
        raise FileNotFoundError(
            "API runtime accessible dependency graph artifact is missing. "
            "Committed deployment activation cannot rebuild API dependency graphs "
            "from source TOML; compile the API service-protocol runtime artifact first: "
            f"{artifact_path}"
        )
    return _hash_json_artifact(artifact_path)


def _resolve_api_service_protocol_dependency_payloads(
    *,
    dependencies: Sequence[Mapping[str, object]],
    repo_root: Path,
    additional_repo_roots: Sequence[Path] = (),
    require_relational_lock: bool = True,
) -> tuple[ServiceProtocolApiDependencyRuntime, ...]:
    dependencies_by_package_name: dict[str, ServiceProtocolApiDependencyRuntime] = {}
    for dependency in dependencies:
        if str(dependency.get("kind") or "").strip() != "api_service_protocol":
            continue
        package_name = str(dependency.get("package_name") or "").strip()
        if not package_name:
            continue
        protocol_digest = str(
            dependency.get("service_protocol_plan_hash_sha256") or ""
        ).strip()
        if not protocol_digest:
            raise RuntimeError(
                "Service protocol runtime resolution requires a committed "
                "service_protocol_plan_hash_sha256 for api_service_protocol "
                f"dependency {package_name!r}."
            )
        if require_relational_lock:
            _validate_service_protocol_dependency_lock_coordinates(
                dependency=dependency,
                package_name=package_name,
            )
        resolved = _resolve_api_service_protocol_dependency_from_roots(
            repo_roots=tuple(
                dict.fromkeys(
                    (
                        *api_service_protocol_dependency_roots(repo_root),
                        *(root.resolve() for root in additional_repo_roots),
                    )
                )
            ),
            package_name=package_name,
            pinned_protocol_digest_sha256=protocol_digest,
            require_api_toml=False,
        )
        existing = dependencies_by_package_name.get(package_name)
        if existing is not None and existing != resolved:
            raise RuntimeError(
                "Conflicting api_service_protocol dependency resolution for "
                f"{package_name!r}."
            )
        dependencies_by_package_name[package_name] = resolved
    return tuple(
        dependencies_by_package_name[key]
        for key in sorted(dependencies_by_package_name, key=str.casefold)
    )


def _resolve_api_service_protocol_dependencies(
    *,
    toml_paths: tuple[Path, ...],
    repo_root: Path,
    kernel_repo_root: Path | None = None,
    use_explicit_repo_root: bool = True,
) -> tuple[ServiceProtocolApiDependencyRuntime, ...]:
    dependency_payloads = load_committed_service_activation_dependency_payloads(
        toml_paths=toml_paths,
    )
    additional_roots = (
        kernel_repo_root,
        *(
            tuple(
                _resolve_repo_root(toml_paths=(path,), repo_root=None)
                for path in toml_paths
            )
        ),
    )
    return _resolve_api_service_protocol_dependency_payloads(
        dependencies=dependency_payloads,
        repo_root=repo_root,
        additional_repo_roots=tuple(
            root.resolve() for root in additional_roots if root is not None
        ),
    )


def load_committed_service_activation_dependency_payloads(
    *,
    toml_paths: tuple[Path, ...],
) -> tuple[dict[str, object], ...]:
    payloads: list[dict[str, object]] = []
    for toml_path in toml_paths:
        spec = load_aware_service_toml_spec(toml_path=toml_path)
        workspace_root = _resolve_repo_root(toml_paths=(toml_path,), repo_root=None)
        package_name = spec.service.package_name.strip()
        lock_path = (
            workspace_root
            / ".aware"
            / "service"
            / "runtime"
            / package_name
            / "service.activation_plan.json"
        ).resolve()
        if not lock_path.is_file():
            raise RuntimeError(
                "Service protocol runtime resolution requires a materialized "
                "service.activation_plan.json relational lock: "
                f"service_package={package_name!r} path={lock_path}"
            )
        raw_payload = json.loads(lock_path.read_text(encoding="utf-8"))
        if not isinstance(raw_payload, Mapping):
            raise RuntimeError(
                f"Service activation lock must be a JSON object: {lock_path}"
            )
        if raw_payload.get("schema_version") != 2:
            raise RuntimeError(
                "Service protocol runtime resolution requires version-2 committed "
                f"activation lock truth: service_package={package_name!r} path={lock_path}"
            )
        if str(raw_payload.get("package_name") or "").strip() != package_name:
            raise RuntimeError(
                "Service activation lock package_name does not match manifest intent: "
                f"service_package={package_name!r} path={lock_path}"
            )
        compile_plan_artifact = raw_payload.get("compile_plan_artifact")
        if not isinstance(compile_plan_artifact, Mapping):
            raise RuntimeError(
                f"Service activation lock has no compile_plan_artifact: {lock_path}"
            )
        compile_plan_relpath = str(compile_plan_artifact.get("relpath") or "").strip()
        compile_plan_digest = str(
            compile_plan_artifact.get("hash_sha256") or ""
        ).strip()
        compile_plan_path = (workspace_root / compile_plan_relpath).resolve()
        if not compile_plan_relpath or not compile_plan_path.is_file():
            raise RuntimeError(
                "Service activation lock compile-plan artifact is missing: "
                f"service_package={package_name!r} path={compile_plan_path}"
            )
        actual_compile_plan_digest = _hash_json_artifact(compile_plan_path)
        if compile_plan_digest != actual_compile_plan_digest:
            raise RuntimeError(
                "Service activation lock is stale for the current compile plan: "
                f"service_package={package_name!r} expected={compile_plan_digest!r} "
                f"actual={actual_compile_plan_digest!r} path={lock_path}"
            )
        service_package_lock = raw_payload.get("service_package_lock")
        if not isinstance(service_package_lock, Mapping):
            raise RuntimeError(
                "Service activation lock has no committed ServicePackage coordinates: "
                f"service_package={package_name!r} path={lock_path}"
            )
        for field_name in (
            "service_package_id",
            "service_package_object_instance_graph_commit_id",
        ):
            _required_lock_uuid(
                service_package_lock.get(field_name),
                label=f"service_package_lock.{field_name}",
                lock_path=lock_path,
            )

        raw_dependencies = raw_payload.get("dependency_pins")
        if not isinstance(raw_dependencies, list):
            raise RuntimeError(
                f"Service activation lock dependency_pins must be an array: {lock_path}"
            )
        protocol_intents = {
            dependency.package_name.strip()
            for dependency in spec.dependencies
            if dependency.kind.value == "api_service_protocol"
        }
        protocol_locks: dict[str, dict[str, object]] = {}
        for raw_dependency in raw_dependencies:
            if not isinstance(raw_dependency, Mapping):
                raise RuntimeError(
                    f"Service activation lock dependency rows must be objects: {lock_path}"
                )
            if str(raw_dependency.get("kind") or "").strip() != "api_service_protocol":
                continue
            dependency_package_name = str(
                raw_dependency.get("package_name") or ""
            ).strip()
            if not dependency_package_name:
                raise RuntimeError(
                    f"Service activation lock protocol dependency has no package_name: {lock_path}"
                )
            if dependency_package_name in protocol_locks:
                raise RuntimeError(
                    "Service activation lock contains duplicate protocol dependency: "
                    f"package_name={dependency_package_name!r} path={lock_path}"
                )
            dependency_payload = dict(raw_dependency)
            dependency_payload.update(
                {
                    "service_package_id": service_package_lock["service_package_id"],
                    "service_package_object_instance_graph_commit_id": (
                        service_package_lock[
                            "service_package_object_instance_graph_commit_id"
                        ]
                    ),
                }
            )
            _validate_service_protocol_dependency_lock_coordinates(
                dependency=dependency_payload,
                package_name=dependency_package_name,
                lock_path=lock_path,
            )
            protocol_locks[dependency_package_name] = dependency_payload
        if set(protocol_locks) != protocol_intents:
            raise RuntimeError(
                "Service activation protocol locks do not match manifest dependency "
                f"intent: service_package={package_name!r} "
                f"intent={sorted(protocol_intents)!r} "
                f"locks={sorted(protocol_locks)!r} path={lock_path}"
            )
        payloads.extend(
            protocol_locks[key] for key in sorted(protocol_locks, key=str.casefold)
        )
    return tuple(payloads)


def _validate_service_protocol_dependency_lock_coordinates(
    *,
    dependency: Mapping[str, object],
    package_name: str,
    lock_path: Path | None = None,
) -> None:
    for field_name in (
        "service_package_provided_api_package_id",
        "api_package_id",
        "api_package_object_instance_graph_commit_id",
        "service_protocol_package_id",
        "service_protocol_code_package_id",
        "service_protocol_code_package_object_instance_graph_commit_id",
    ):
        _required_lock_uuid(
            dependency.get(field_name),
            label=f"api_service_protocol.{field_name}",
            lock_path=lock_path,
        )
    digest = str(dependency.get("service_protocol_plan_hash_sha256") or "").strip()
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        location = f" path={lock_path}" if lock_path is not None else ""
        raise RuntimeError(
            "Service protocol dependency lock has invalid plan digest: "
            f"package_name={package_name!r}{location}"
        )


def _required_lock_uuid(
    value: object,
    *,
    label: str,
    lock_path: Path | None,
) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        location = f" path={lock_path}" if lock_path is not None else ""
        raise RuntimeError(
            f"Service activation lock requires UUID {label}.{location}"
        ) from exc


def _resolve_api_service_protocol_dependency_from_roots(
    *,
    repo_roots: tuple[Path, ...],
    package_name: str,
    pinned_protocol_digest_sha256: str,
    require_api_toml: bool,
) -> ServiceProtocolApiDependencyRuntime:
    roots = tuple(dict.fromkeys(root.resolve() for root in repo_roots))
    for root in roots:
        runtime_package_dir = root / ".aware" / "api" / "runtime" / package_name
        if not runtime_package_dir.exists():
            continue
        return _resolve_api_service_protocol_dependency(
            repo_root=root,
            package_name=package_name,
            pinned_protocol_digest_sha256=pinned_protocol_digest_sha256,
            require_api_toml=require_api_toml,
        )
    first_root = roots[0] if roots else Path.cwd().resolve()
    return _resolve_api_service_protocol_dependency(
        repo_root=first_root,
        package_name=package_name,
        pinned_protocol_digest_sha256=pinned_protocol_digest_sha256,
        require_api_toml=require_api_toml,
    )


def _resolve_api_service_protocol_dependency(
    *,
    repo_root: Path,
    package_name: str,
    pinned_protocol_digest_sha256: str,
    require_api_toml: bool = True,
) -> ServiceProtocolApiDependencyRuntime:
    runtime_package_dir = (
        repo_root / ".aware" / "api" / "runtime" / package_name
    ).resolve()
    api_manifest_path = (runtime_package_dir / "api.manifest.json").resolve()
    service_protocol_plan_path = (
        runtime_package_dir / "api.service_protocol_plan.json"
    ).resolve()
    api_compile_plan_path = (runtime_package_dir / "api.compile_plan.json").resolve()
    for path, label in (
        (api_manifest_path, "api.manifest.json"),
        (service_protocol_plan_path, "api.service_protocol_plan.json"),
        (api_compile_plan_path, "api.compile_plan.json"),
    ):
        if not path.is_file():
            raise FileNotFoundError(
                "Service protocol runtime resolution requires compiled API artifact "
                f"{label} for dependency {package_name!r}: {path}"
            )
    actual_hash_sha256 = _hash_json_artifact(service_protocol_plan_path)
    if actual_hash_sha256 != pinned_protocol_digest_sha256:
        raise RuntimeError(
            "Service protocol runtime resolution API dispatch pin mismatch: "
            f"package_name={package_name!r} expected={pinned_protocol_digest_sha256} "
            f"actual={actual_hash_sha256}"
        )
    api_manifest = _load_json_mapping(api_manifest_path)
    api_toml_path = _resolve_manifest_path_field(
        payload=api_manifest,
        key="api_toml_path",
        repo_root=repo_root,
        manifest_path=api_manifest_path,
    )
    api_toml_relpath = _optional_manifest_relpath_field(
        payload=api_manifest,
        key="api_toml_relpath",
        manifest_path=api_manifest_path,
    )
    if require_api_toml and not api_toml_path.is_file():
        raise FileNotFoundError(
            "Service protocol runtime resolution could not find API TOML for "
            f"dependency {package_name!r}: {api_toml_path}"
        )
    return ServiceProtocolApiDependencyRuntime(
        package_name=package_name,
        repo_root=repo_root,
        api_manifest_path=api_manifest_path,
        api_toml_path=api_toml_path,
        service_protocol_plan_path=service_protocol_plan_path,
        service_protocol_plan_hash_sha256=actual_hash_sha256,
        api_compile_plan_path=api_compile_plan_path,
        api_toml_relpath=api_toml_relpath,
    )


def _resolve_repo_root(
    *,
    toml_paths: tuple[Path, ...],
    repo_root: str | Path | None,
) -> Path:
    if repo_root is not None:
        return Path(repo_root).expanduser().resolve()
    for toml_path in toml_paths:
        for candidate in (toml_path.parent, *toml_path.parents):
            if (candidate / "aware.workspace.toml").is_file():
                return candidate.resolve()
    for toml_path in toml_paths:
        for candidate in (toml_path.parent, *toml_path.parents):
            if _revision_filesystem_manifest_path(candidate).is_file():
                return candidate.resolve()
    raise RuntimeRequirementsError(
        "Service runtime resolution requires an explicit repo_root or a service "
        "TOML contained by aware.workspace.toml / a WorkspaceRevision filesystem "
        "manifest. Repository-root discovery fallback is retired."
    )


def _service_runtime_allowed_roots(
    *,
    service_repo_root: Path,
    kernel_repo_root: Path,
) -> tuple[Path, ...]:
    roots: list[Path] = [service_repo_root.resolve()]
    resolved_kernel_root = kernel_repo_root.resolve()
    if (
        resolved_kernel_root != roots[0]
        and (
            (resolved_kernel_root / "aware.workspace.toml").is_file()
            or _revision_filesystem_manifest_path(resolved_kernel_root).is_file()
        )
        and not _is_workspace_container_root(
            container_root=resolved_kernel_root,
            workspace_root=service_repo_root,
        )
    ):
        roots.append(resolved_kernel_root)
    roots.extend(declared_workspace_dependency_roots(workspace_root=service_repo_root))
    return tuple(dict.fromkeys(roots))


def _is_workspace_container_root(*, container_root: Path, workspace_root: Path) -> bool:
    try:
        relative = workspace_root.resolve().relative_to(container_root.resolve())
    except ValueError:
        return False
    return len(relative.parts) >= 2 and relative.parts[0] == "workspaces"


def _revision_filesystem_manifest_path(workspace_root: Path) -> Path:
    return (
        workspace_root / ".aware" / "workspace" / "revision-filesystem.manifest.json"
    ).resolve()


def _default_runtime_manifest_output_path(
    *,
    repo_root: Path,
    dependencies: tuple[ServiceProtocolApiDependencyRuntime, ...],
) -> Path:
    digest = sha256(
        "\n".join(dependency.package_name for dependency in dependencies).encode(
            "utf-8"
        )
    ).hexdigest()[:16]
    return (
        repo_root
        / ".aware"
        / "service"
        / "runtime"
        / f"service-protocol-{digest}"
        / "runtime.sources.json"
    ).resolve()


def _runtime_manifest_cache_metadata_path(manifest_path: Path) -> Path:
    return manifest_path.with_name(f"{manifest_path.stem}.cache.json")


def _service_protocol_runtime_cache_key(
    *,
    toml_paths: tuple[Path, ...],
    repo_root: Path,
    kernel_repo_root: Path,
    manifest_repo_root: Path,
    dependencies: tuple[ServiceProtocolApiDependencyRuntime, ...],
    api_resolutions: tuple[APIRuntimeManifestResolution, ...],
) -> dict[str, object]:
    cache_key = _service_protocol_runtime_fast_cache_key(
        toml_paths=toml_paths,
        repo_root=repo_root,
        kernel_repo_root=kernel_repo_root,
        manifest_repo_root=manifest_repo_root,
        dependencies=dependencies,
    )
    cache_key["api_runtime_resolutions"] = [
        _runtime_resolution_cache_key_payload(api_resolution)
        for api_resolution in api_resolutions
    ]
    return cache_key


def _service_protocol_runtime_fast_cache_key(
    *,
    toml_paths: tuple[Path, ...],
    repo_root: Path,
    kernel_repo_root: Path,
    manifest_repo_root: Path,
    dependencies: tuple[ServiceProtocolApiDependencyRuntime, ...],
) -> dict[str, object]:
    return {
        "schema": "aware.service_protocol.runtime_manifest_cache_key.v2",
        "repo_root": repo_root.as_posix(),
        "kernel_repo_root": kernel_repo_root.as_posix(),
        "manifest_repo_root": manifest_repo_root.as_posix(),
        "service_tomls": [
            {
                "path": path.as_posix(),
                "sha256": _hash_file(path),
            }
            for path in toml_paths
        ],
        "api_dependencies": [
            {
                "package_name": dependency.package_name,
                "repo_root": dependency.repo_root.as_posix(),
                "api_manifest_path": dependency.api_manifest_path.as_posix(),
                "api_manifest_sha256": _hash_file(dependency.api_manifest_path),
                "api_toml_path": dependency.api_toml_path.as_posix(),
                "service_protocol_plan_path": (
                    dependency.service_protocol_plan_path.as_posix()
                ),
                "service_protocol_plan_hash_sha256": (
                    dependency.service_protocol_plan_hash_sha256
                ),
                "service_protocol_plan_file_sha256": (
                    _hash_file(dependency.service_protocol_plan_path)
                ),
                "api_compile_plan_path": dependency.api_compile_plan_path.as_posix(),
                "api_compile_plan_sha256": _hash_file(dependency.api_compile_plan_path),
            }
            for dependency in dependencies
        ],
    }


def _runtime_resolution_cache_key_payload(
    resolution: RuntimeManifestResolution | APIRuntimeManifestResolution | None,
) -> dict[str, object] | None:
    if resolution is None:
        return None
    runtime_bundle_manifest_paths = _runtime_bundle_manifest_paths_for_cache_key(
        resolution
    )
    environment_config_id = _runtime_environment_config_id_for_cache_key(resolution)
    return {
        "manifest_path": {
            "path": resolution.manifest_path.as_posix(),
            "sha256": _hash_file(resolution.manifest_path),
        },
        "module_ids": list(resolution.module_ids),
        "module_manifest_paths": [
            {
                "path": path.as_posix(),
                "sha256": _hash_file(path),
            }
            for path in resolution.module_manifest_paths
        ],
        "runtime_bundle_manifest_paths": [
            {
                "path": path.as_posix(),
                "sha256": _hash_file(path),
            }
            for path in runtime_bundle_manifest_paths
        ],
        "python_roots": [path.as_posix() for path in resolution.python_roots],
        "import_activation_roots": [
            path.as_posix() for path in resolution.import_activation.roots
        ],
        "environment_config_id": (
            str(environment_config_id) if environment_config_id is not None else None
        ),
    }


def _runtime_bundle_manifest_paths_for_cache_key(
    resolution: RuntimeManifestResolution | APIRuntimeManifestResolution,
) -> tuple[Path, ...]:
    if isinstance(resolution, RuntimeManifestResolution):
        return resolution.runtime_bundle_manifest_paths
    return ()


def _runtime_environment_config_id_for_cache_key(
    resolution: RuntimeManifestResolution | APIRuntimeManifestResolution,
) -> UUID | None:
    if isinstance(resolution, RuntimeManifestResolution):
        return resolution.environment_config_id
    return None


def _load_cached_service_protocol_runtime_resolution(
    *,
    cache_metadata_path: Path,
    cache_key: Mapping[str, object],
    manifest_path: Path,
) -> tuple[RuntimeManifestResolution | None, str]:
    if not manifest_path.is_file():
        return None, "manifest_missing"
    if not cache_metadata_path.is_file():
        return None, "cache_metadata_missing"
    try:
        payload = _load_json_mapping(cache_metadata_path)
    except Exception as exc:
        return None, f"cache_metadata_invalid:{exc.__class__.__name__}"
    if payload.get("schema") != "aware.service_protocol.runtime_manifest_cache.v0":
        return None, "cache_schema_mismatch"
    if payload.get("cache_key") != cache_key:
        return None, "cache_key_mismatch"
    return _load_cached_runtime_resolution_payload(
        payload=payload,
        manifest_path=manifest_path,
    )


def _load_cached_service_protocol_runtime_resolution_fast(
    *,
    cache_metadata_path: Path,
    fast_cache_key: Mapping[str, object],
    manifest_path: Path,
) -> tuple[RuntimeManifestResolution | None, str]:
    if not manifest_path.is_file():
        return None, "manifest_missing"
    if not cache_metadata_path.is_file():
        return None, "cache_metadata_missing"
    try:
        payload = _load_json_mapping(cache_metadata_path)
    except Exception as exc:
        return None, f"cache_metadata_invalid:{exc.__class__.__name__}"
    if payload.get("schema") != "aware.service_protocol.runtime_manifest_cache.v0":
        return None, "cache_schema_mismatch"
    cached_key = payload.get("cache_key")
    if not isinstance(cached_key, Mapping):
        return None, "cache_key_missing"
    invalid_reason = _fast_service_protocol_cache_invalid_reason(
        cached_key=cached_key,
        fast_cache_key=fast_cache_key,
    )
    if invalid_reason is not None:
        return None, invalid_reason
    cached_runtime_resolution, cache_reason = _load_cached_runtime_resolution_payload(
        payload=payload,
        manifest_path=manifest_path,
    )
    if cached_runtime_resolution is None:
        return None, cache_reason
    return cached_runtime_resolution, "cache_valid"


def _fast_service_protocol_cache_invalid_reason(
    *,
    cached_key: Mapping[str, object],
    fast_cache_key: Mapping[str, object],
) -> str | None:
    for key in (
        "schema",
        "repo_root",
        "kernel_repo_root",
        "manifest_repo_root",
        "service_tomls",
        "api_dependencies",
    ):
        if cached_key.get(key) != fast_cache_key.get(key):
            return f"cache_fast_key_mismatch:{key}"
    for label, payload in (
        (f"api_runtime_resolutions[{index}]", item)
        for index, item in enumerate(
            _cached_key_runtime_resolution_payloads(
                cached_key.get("api_runtime_resolutions")
            )
        )
    ):
        invalid_reason = _cached_runtime_resolution_key_payload_invalid_reason(
            payload=payload,
        )
        if invalid_reason is not None:
            return f"cache_fast_key_invalid:{label}:{invalid_reason}"
    return None


def _cached_key_runtime_resolution_payloads(raw: object) -> tuple[object, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        return ({"invalid": "api_runtime_resolutions_not_list"},)
    return tuple(raw)


def _cached_runtime_resolution_key_payload_invalid_reason(
    *,
    payload: object,
) -> str | None:
    if payload is None:
        return None
    if not isinstance(payload, Mapping):
        return "not_mapping"
    raw_manifest_path = payload.get("manifest_path")
    if not isinstance(raw_manifest_path, Mapping):
        return "manifest_path_missing"
    raw_path = raw_manifest_path.get("path")
    raw_sha = raw_manifest_path.get("sha256")
    if not isinstance(raw_path, str) or not raw_path.strip():
        return "manifest_path_invalid"
    if not isinstance(raw_sha, str) or not raw_sha.strip():
        return "manifest_sha_invalid"
    manifest_path = Path(raw_path).expanduser().resolve()
    if not manifest_path.is_file():
        return "manifest_file_missing"
    if _hash_file(manifest_path) != raw_sha:
        return "manifest_sha_mismatch"
    raw_module_manifest_paths = payload.get("module_manifest_paths")
    if not isinstance(raw_module_manifest_paths, list):
        return "module_manifest_paths_invalid"
    for raw_item in raw_module_manifest_paths:
        if not isinstance(raw_item, Mapping):
            return "module_manifest_path_invalid"
        raw_item_path = raw_item.get("path")
        raw_item_sha = raw_item.get("sha256")
        if not isinstance(raw_item_path, str) or not raw_item_path.strip():
            return "module_manifest_path_invalid"
        if not isinstance(raw_item_sha, str) or not raw_item_sha.strip():
            return "module_manifest_sha_invalid"
        path = Path(raw_item_path).expanduser().resolve()
        if not path.is_file():
            return "module_manifest_file_missing"
        if _hash_file(path) != raw_item_sha:
            return "module_manifest_sha_mismatch"
    raw_bundle_manifest_paths = payload.get("runtime_bundle_manifest_paths")
    if raw_bundle_manifest_paths is not None:
        if not isinstance(raw_bundle_manifest_paths, list):
            return "runtime_bundle_manifest_paths_invalid"
        for raw_item in raw_bundle_manifest_paths:
            if not isinstance(raw_item, Mapping):
                return "runtime_bundle_manifest_path_invalid"
            raw_item_path = raw_item.get("path")
            raw_item_sha = raw_item.get("sha256")
            if not isinstance(raw_item_path, str) or not raw_item_path.strip():
                return "runtime_bundle_manifest_path_invalid"
            if not isinstance(raw_item_sha, str) or not raw_item_sha.strip():
                return "runtime_bundle_manifest_sha_invalid"
            path = Path(raw_item_path).expanduser().resolve()
            if not path.is_file():
                return "runtime_bundle_manifest_file_missing"
            if _hash_file(path) != raw_item_sha:
                return "runtime_bundle_manifest_sha_mismatch"
    return None


def _load_cached_runtime_resolution_payload(
    *,
    payload: Mapping[str, object],
    manifest_path: Path,
) -> tuple[RuntimeManifestResolution | None, str]:
    runtime_payload = payload.get("runtime_resolution")
    if not isinstance(runtime_payload, dict):
        return None, "cache_runtime_resolution_missing"
    raw_bundle_manifest_paths = runtime_payload.get("runtime_bundle_manifest_paths")
    has_bundle_manifest_paths = isinstance(raw_bundle_manifest_paths, list) and bool(
        raw_bundle_manifest_paths
    )
    raw_module_manifest_paths = runtime_payload.get("module_manifest_paths")
    has_module_manifest_paths = isinstance(raw_module_manifest_paths, list) and bool(
        raw_module_manifest_paths
    )
    if not has_bundle_manifest_paths and has_module_manifest_paths:
        registry_invalid_reason = _cached_db_schema_registry_invalid_reason(
            manifest_path=manifest_path
        )
        if registry_invalid_reason is not None:
            return None, registry_invalid_reason
    try:
        module_manifest_paths = _cached_path_tuple(
            runtime_payload,
            key="module_manifest_paths",
            require_files=True,
        )
        runtime_bundle_manifest_paths = _cached_path_tuple(
            runtime_payload,
            key="runtime_bundle_manifest_paths",
            require_files=True,
        )
        python_roots = _cached_path_tuple(runtime_payload, key="python_roots")
        _validate_cached_path_states(
            runtime_payload,
            key="python_root_states",
            expected_paths=python_roots,
            require_dirs=True,
        )
        import_activation_roots = _cached_path_tuple(
            runtime_payload,
            key="import_activation_roots",
            require_dirs=True,
        )
        module_ids = _cached_str_tuple(runtime_payload, key="module_ids")
        environment_handle = str(runtime_payload["environment_handle"])
        raw_environment_config_id = runtime_payload.get("environment_config_id")
        environment_config_id = (
            UUID(raw_environment_config_id)
            if isinstance(raw_environment_config_id, str)
            and raw_environment_config_id.strip()
            else None
        )
    except (KeyError, TypeError, ValueError, FileNotFoundError) as exc:
        return None, f"cache_runtime_resolution_invalid:{exc}"
    return (
        RuntimeManifestResolution(
            manifest_path=manifest_path,
            module_ids=module_ids,
            module_manifest_paths=module_manifest_paths,
            python_roots=python_roots,
            import_activation=RuntimeImportActivationPlan(
                roots=import_activation_roots,
            ),
            environment_handle=environment_handle,
            runtime_bundle_manifest_paths=runtime_bundle_manifest_paths,
            environment_config_id=environment_config_id,
        ),
        "cache_valid",
    )


def _cached_db_schema_registry_invalid_reason(*, manifest_path: Path) -> str | None:
    registry_path = manifest_path.with_name("db.schema.registry.json")
    if not registry_path.is_file():
        return "db_schema_registry_missing"
    try:
        registry = load_db_schema_registry(path=registry_path)
    except Exception as exc:
        return f"db_schema_registry_invalid:{exc.__class__.__name__}"
    registry_dir = registry_path.parent
    for entry in registry.entries:
        sql_root_token = Path(entry.sql_root)
        sql_root = (
            (registry_dir / sql_root_token).resolve()
            if not sql_root_token.is_absolute()
            else sql_root_token.resolve()
        )
        if not sql_root.is_dir():
            return "db_schema_registry_sql_root_missing"
        actual_hash = compute_sql_root_source_hash(sql_root=sql_root)
        if actual_hash != entry.source_hash:
            label = entry.source_label or sql_root.as_posix()
            return f"db_schema_registry_source_hash_mismatch:{label}"
    return None


def _write_service_protocol_runtime_manifest_cache(
    *,
    cache_metadata_path: Path,
    cache_key: Mapping[str, object],
    runtime_resolution: RuntimeManifestResolution,
) -> None:
    cache_metadata_path.parent.mkdir(parents=True, exist_ok=True)
    cache_metadata_path.write_text(
        json.dumps(
            {
                "schema": "aware.service_protocol.runtime_manifest_cache.v0",
                "cache_key": cache_key,
                "runtime_resolution": {
                    "manifest_path": runtime_resolution.manifest_path.as_posix(),
                    "module_ids": list(runtime_resolution.module_ids),
                    "module_manifest_paths": [
                        path.as_posix()
                        for path in runtime_resolution.module_manifest_paths
                    ],
                    "runtime_bundle_manifest_paths": [
                        path.as_posix()
                        for path in runtime_resolution.runtime_bundle_manifest_paths
                    ],
                    "python_roots": [
                        path.as_posix() for path in runtime_resolution.python_roots
                    ],
                    "python_root_states": [
                        {"path": path.as_posix(), "exists": path.is_dir()}
                        for path in runtime_resolution.python_roots
                    ],
                    "import_activation_roots": [
                        path.as_posix()
                        for path in runtime_resolution.import_activation.roots
                    ],
                    "environment_handle": runtime_resolution.environment_handle,
                    "environment_config_id": (
                        str(runtime_resolution.environment_config_id)
                        if runtime_resolution.environment_config_id is not None
                        else None
                    ),
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _cached_path_tuple(
    payload: Mapping[str, object],
    *,
    key: str,
    require_files: bool = False,
    require_dirs: bool = False,
) -> tuple[Path, ...]:
    raw_items = payload[key]
    if not isinstance(raw_items, list):
        raise TypeError(f"{key} must be a list")
    paths: list[Path] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, str) or not raw_item.strip():
            raise TypeError(f"{key} must contain non-empty strings")
        path = Path(raw_item).expanduser().resolve()
        if require_files and not path.is_file():
            raise FileNotFoundError(path.as_posix())
        if require_dirs and not path.is_dir():
            raise FileNotFoundError(path.as_posix())
        paths.append(path)
    return tuple(paths)


def _validate_cached_path_states(
    payload: Mapping[str, object],
    *,
    key: str,
    expected_paths: tuple[Path, ...],
    require_dirs: bool = False,
) -> None:
    raw_items = payload[key]
    if not isinstance(raw_items, list):
        raise TypeError(f"{key} must be a list")
    if len(raw_items) != len(expected_paths):
        raise ValueError(f"{key} path count mismatch")
    for raw_item, expected_path in zip(raw_items, expected_paths, strict=True):
        if not isinstance(raw_item, dict):
            raise TypeError(f"{key} must contain objects")
        raw_path = raw_item.get("path")
        raw_exists = raw_item.get("exists")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise TypeError(f"{key} path must be a non-empty string")
        if not isinstance(raw_exists, bool):
            raise TypeError(f"{key} exists must be a boolean")
        path = Path(raw_path).expanduser().resolve()
        if path != expected_path:
            raise ValueError(f"{key} path mismatch: {path.as_posix()}")
        current_exists = path.is_dir() if require_dirs else path.exists()
        if current_exists != raw_exists:
            raise FileNotFoundError(
                f"{path.as_posix()} existence changed "
                f"(cached={raw_exists!r}, current={current_exists!r})"
            )


def _cached_str_tuple(
    payload: Mapping[str, object],
    *,
    key: str,
) -> tuple[str, ...]:
    raw_items = payload[key]
    if not isinstance(raw_items, list):
        raise TypeError(f"{key} must be a list")
    values: list[str] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, str):
            raise TypeError(f"{key} must contain strings")
        values.append(raw_item)
    return tuple(values)


def _normalize_text_items(items: object, *, field_name: str) -> list[str]:
    if isinstance(items, str):
        raw_items = [items]
    elif isinstance(items, Iterable):
        raw_items = list(items)
    else:
        raise RuntimeRequirementsError(f"{field_name} must be a string or iterable")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        if item is None:
            continue
        value = str(item).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized


def _coerce_path_tuple(
    items: object,
    *,
    field_name: str,
    require_exists: bool = True,
) -> tuple[Path, ...]:
    if isinstance(items, (str, Path)):
        raw_items = [items]
    elif isinstance(items, Iterable):
        raw_items = list(items)
    else:
        raise RuntimeRequirementsError(f"{field_name} must be a path or iterable")
    paths: list[Path] = []
    seen: set[Path] = set()
    for item in raw_items:
        if item is None:
            continue
        path = Path(item).expanduser().resolve()
        if require_exists and not path.exists():
            raise RuntimeRequirementsError(f"{field_name} path does not exist: {path}")
        if path in seen:
            continue
        seen.add(path)
        paths.append(path)
    return tuple(paths)


def _require_module_manifests(manifest_paths: Iterable[Path]) -> None:
    for manifest_path in manifest_paths:
        if manifest_path.exists():
            continue
        raise RuntimeRequirementsError(
            "Module runtime manifest missing for package "
            f"{manifest_path}. Materialize the owning workspace package with "
            "`uv run aware-cli workspace materialize --workspace-toml "
            "<aware.workspace.toml> --package <package_name> --plan`, then "
            "run the approved execute mode or record the blocker."
        )


def _stable_runtime_source_environment_config_id(
    *,
    environment_handle: str,
    runtime_bundle_manifest_paths: Iterable[Path],
) -> UUID:
    payload = {
        "environment_handle": environment_handle,
        "runtime_bundle_manifest_paths": [
            path.expanduser().resolve().as_posix()
            for path in runtime_bundle_manifest_paths
        ],
    }
    digest = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return uuid5(NAMESPACE_URL, f"aware-service-runtime-source:{digest}")


def _write_service_protocol_runtime_source_descriptor(
    *,
    path: Path,
    runtime_resolution: RuntimeManifestResolution,
    dependencies: tuple[ServiceProtocolApiDependencyRuntime, ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": "aware.service_protocol.runtime_sources.v1",
                "source": "ontology_runtime_artifacts",
                "environment_handle": runtime_resolution.environment_handle,
                "environment_config_id": (
                    str(runtime_resolution.environment_config_id)
                    if runtime_resolution.environment_config_id is not None
                    else None
                ),
                "module_ids": list(runtime_resolution.module_ids),
                "runtime_bundle_manifest_paths": [
                    item.as_posix()
                    for item in runtime_resolution.runtime_bundle_manifest_paths
                ],
                "api_dependencies": [
                    {
                        "package_name": dependency.package_name,
                        "api_manifest_path": dependency.api_manifest_path.as_posix(),
                        "service_protocol_plan_path": (
                            dependency.service_protocol_plan_path.as_posix()
                        ),
                        "service_protocol_plan_hash_sha256": (
                            dependency.service_protocol_plan_hash_sha256
                        ),
                    }
                    for dependency in dependencies
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _environment_handle(
    *,
    dependencies: tuple[ServiceProtocolApiDependencyRuntime, ...],
) -> str:
    if len(dependencies) == 1:
        return f"service-protocol-{dependencies[0].package_name}"
    digest = sha256(
        "\n".join(dependency.package_name for dependency in dependencies).encode(
            "utf-8"
        )
    ).hexdigest()[:16]
    return f"service-protocol-{digest}"


def _resolve_manifest_path_field(
    *,
    payload: dict[str, object],
    key: str,
    repo_root: Path,
    manifest_path: Path,
) -> Path:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(
            f"API runtime manifest requires non-empty string field {key!r}: "
            f"{manifest_path}"
        )
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def _optional_manifest_relpath_field(
    *,
    payload: Mapping[str, object],
    key: str,
    manifest_path: Path,
) -> str | None:
    raw_value = payload.get(key)
    if raw_value is None:
        return None
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise RuntimeError(
            f"API runtime manifest requires string field {key!r} when present: "
            f"{manifest_path}"
        )
    return _normalize_portable_manifest_relpath(
        value=raw_value,
        key=key,
        manifest_path=manifest_path,
    )


def _normalize_portable_manifest_relpath(
    *,
    value: str,
    key: str,
    manifest_path: Path,
) -> str:
    path = PurePosixPath(value.strip())
    if path.is_absolute() or ".." in path.parts:
        raise RuntimeError(
            f"API runtime manifest field {key!r} must be a portable relative "
            f"path: {manifest_path}"
        )
    return path.as_posix()


def _load_json_mapping(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8") or "{}")
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected JSON object at {path}")
    return dict(payload)


def _canonical_json_sha256(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(
        dict(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


def _hash_json_artifact(path: Path) -> str:
    payload = _load_json_mapping(path)
    return _canonical_json_sha256(payload)


def _hash_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _object_config_graph_names(graphs: Sequence[ObjectConfigGraph]) -> tuple[str, ...]:
    return tuple(str(graph.name) for graph in graphs)


def _accessible_graphs_hash(accessible_graphs: Sequence[ObjectConfigGraph]) -> str:
    payloads = [
        _accessible_graph_hash_payload(graph)
        for graph in sorted(
            accessible_graphs,
            key=lambda item: str(getattr(item, "name", "") or ""),
        )
    ]
    return _canonical_json_sha256({"accessible_graphs": payloads})


def _accessible_graph_hash_payload(graph: object) -> object:
    model_dump = getattr(graph, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json", exclude_none=True)
    return {"name": str(getattr(graph, "name", "") or "")}


def _dedupe_paths(paths: Sequence[Path]) -> list[Path]:
    out: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        resolved = path.expanduser().resolve()
        key = resolved.as_posix()
        if key in seen:
            continue
        out.append(resolved)
        seen.add(key)
    return out


__all__ = [
    "RuntimeImportActivationPlan",
    "RuntimeManifestResolution",
    "ServiceProtocolApiReferenceMaterializationInput",
    "ServiceProtocolApiReferenceLaneInput",
    "ServiceProtocolApiDependencyRuntime",
    "ServiceProtocolRuntimeResolution",
    "load_committed_service_activation_dependency_payloads",
    "load_service_protocol_api_compile_plan_payloads",
    "load_service_protocol_api_reference_lane_inputs",
    "load_service_protocol_api_reference_lane_inputs_from_dependencies",
    "load_service_protocol_api_reference_materialization_inputs",
    "load_service_protocol_api_reference_materialization_inputs_from_dependencies",
    "service_protocol_api_reference_branch_id",
    "resolve_service_protocol_runtime_manifest",
    "split_service_protocol_api_reference_lane_inputs",
]
