from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import pickle
from time import perf_counter
from uuid import UUID

from aware_meta.manifest.loader import load_aware_toml_spec
from aware_meta.package_graph_reuse_cache import source_text_manifest_hash
from aware_meta.runtime.handler_executor.index import (
    MetaGraphFunctionImplOwnership,
    MetaGraphImplementationPolicy,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.projection.portal_index import ObjectProjectionGraphPortalIndex
from aware_meta.runtime.graph_context import (
    MetaGraphRuntimeContext,
    MetaGraphRuntimeIndexSnapshot,
    MetaGraphRuntimePackageTiming,
    build_meta_graph_runtime_context,
    build_meta_graph_runtime_index_snapshot,
    build_meta_graph_runtime_context_for_workspace_required_projections,
    resolve_meta_runtime_package_manifest_closure_for_workspace_read_model,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)


_META_RUNTIME_READ_MODEL_VERSION = "aware.meta.runtime.read_model.v1"
_META_RUNTIME_READ_MODEL_CACHE_SCHEMA_V1 = "aware.meta.runtime.read_model.cache.v1"
_META_RUNTIME_READ_MODEL_CACHE_SCHEMA = "aware.meta.runtime.read_model.cache.v2"
_META_RUNTIME_READ_MODEL_CONTEXT_PICKLE_SCHEMA = (
    "aware.meta.runtime.read_model.context_pickle.v1"
)
_META_API_ACTIVATION_READ_MODEL_VERSION = "aware.meta.api_activation.read_model.v1"
_META_API_ACTIVATION_READ_MODEL_SIDECAR_SCHEMA = (
    "aware.meta.api_activation.read_model.sidecar.v2"
)
_META_RUNTIME_READ_MODEL_SOURCE_FINGERPRINT_SCHEMA = (
    "aware.meta.runtime.read_model.source_fingerprint.v1"
)
_META_RUNTIME_READ_MODEL_FAST_SOURCE_FINGERPRINT_SCHEMA = (
    "aware.meta.runtime.read_model.fast_source_fingerprint.v1"
)
_META_RUNTIME_READ_MODEL_PICKLE_SIDECAR_ENV = (
    "AWARE_META_READ_MODEL_PICKLE_SIDECAR_ENABLED"
)


@dataclass(frozen=True, slots=True)
class MetaRuntimeReadModelRequest:
    repo_root: Path
    required_projection_names: tuple[str, ...]
    required_package_names: tuple[str, ...] = ()
    aware_root: Path | None = None
    composition_context_id: UUID | None = None
    semantic_ontology_package_catalog: Mapping[str, object] | None = None
    composite_name: str = "Aware Workspace Runtime Read Model"
    force_refresh: bool = False
    include_workspace_commit_truth: bool = False
    workspace_commit_truth: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class MetaRuntimeReadModel:
    read_model_version: str
    repo_root: Path
    aware_root: Path
    required_projection_names: tuple[str, ...]
    required_package_names: tuple[str, ...]
    context: MetaGraphRuntimeContext
    projection_hash_by_name: Mapping[str, str]
    runtime_graph_ids: tuple[UUID, ...]
    source_graph_ids: tuple[UUID, ...]
    phase_timings_s: Mapping[str, float]
    package_timings: tuple[MetaGraphRuntimePackageTiming, ...]
    cache_status: str
    provider_duration_s: float
    workspace_commit_truth: Mapping[str, object] | None = None

    @property
    def index(self) -> MetaGraphRuntimeIndexSnapshot:
        return self.context.index

    @property
    def runtime_handler_provider_import_roots(self) -> tuple[str, ...]:
        return self.context.runtime_handler_provider_import_roots

    def projection_hash_for_name(self, projection_name: str) -> str:
        return self.context.projection_hash_for_name(projection_name)


@dataclass(frozen=True, slots=True)
class MetaApiActivationReadModel:
    read_model_version: str
    repo_root: Path
    aware_root: Path
    required_projection_names: tuple[str, ...]
    required_package_names: tuple[str, ...]
    index: MetaGraphRuntimeIndexSnapshot
    projection_hash_by_name: Mapping[str, str]
    runtime_graph_ids: tuple[UUID, ...]
    source_graph_ids: tuple[UUID, ...]
    runtime_handler_provider_import_roots: tuple[str, ...]
    phase_timings_s: Mapping[str, float]
    package_timings: tuple[MetaGraphRuntimePackageTiming, ...]
    cache_status: str
    provider_duration_s: float

    def projection_hash_for_name(self, projection_name: str) -> str:
        target = projection_name.strip()
        if not target:
            raise ValueError("Projection name is required.")
        projection_hash = self.projection_hash_by_name.get(target)
        if projection_hash is None:
            raise ValueError(
                f"Projection {projection_name!r} was not found in Meta API activation read model."
            )
        return projection_hash


@dataclass(frozen=True, slots=True)
class _MetaRuntimeReadModelCacheKey:
    repo_root: str
    aware_root: str
    semantic_ontology_package_catalog_signature: str
    source_fingerprint_signature: str
    composition_context_id: UUID | None
    required_projection_names: tuple[str, ...]
    required_package_names: tuple[str, ...]
    composite_name: str


@dataclass(frozen=True, slots=True)
class _MetaRuntimeReadModelCacheLocator:
    repo_root: str
    aware_root: str
    semantic_ontology_package_catalog_signature: str
    composition_context_id: UUID | None
    required_projection_names: tuple[str, ...]
    required_package_names: tuple[str, ...]
    composite_name: str


@dataclass(frozen=True, slots=True)
class _PersistentReadModelCandidate:
    source_fingerprint: Mapping[str, object]
    context_payload: Mapping[str, object]
    context: MetaGraphRuntimeContext | None = None


class MetaRuntimeReadModelProvider:
    """Meta-owned runtime/index read-model provider for Workspace consumers.

    Workspace asks for read truth by projection name. Meta owns the package closure,
    graph context, index construction, and cache policy behind this boundary.
    """

    def __init__(self) -> None:
        self._workspace_required_projection_cache: dict[
            _MetaRuntimeReadModelCacheKey,
            MetaGraphRuntimeContext,
        ] = {}
        self._api_activation_cache: dict[
            _MetaRuntimeReadModelCacheKey,
            MetaApiActivationReadModel,
        ] = {}

    def read_workspace_required_projections(
        self,
        request: MetaRuntimeReadModelRequest,
    ) -> MetaRuntimeReadModel:
        started_at = perf_counter()
        projection_names = _clean_required_projection_names(
            request.required_projection_names
        )
        package_names = _clean_required_package_names(request.required_package_names)
        if not projection_names and not package_names:
            raise ValueError(
                "Meta runtime read model requires at least one projection or "
                "package name."
            )
        repo_root = request.repo_root.expanduser().resolve()
        aware_root = (
            request.aware_root.expanduser().resolve()
            if request.aware_root is not None
            else repo_root
        )
        catalog_signature = _semantic_ontology_package_catalog_signature(
            request.semantic_ontology_package_catalog
        )
        locator = _MetaRuntimeReadModelCacheLocator(
            repo_root=repo_root.as_posix(),
            aware_root=aware_root.as_posix(),
            semantic_ontology_package_catalog_signature=catalog_signature,
            composition_context_id=request.composition_context_id,
            required_projection_names=tuple(sorted(projection_names)),
            required_package_names=tuple(sorted(package_names)),
            composite_name=request.composite_name,
        )
        source_fingerprint: Mapping[str, object] | None = None
        cache_key: _MetaRuntimeReadModelCacheKey | None = None
        context: MetaGraphRuntimeContext | None = None
        cache_status = "miss"

        if not request.force_refresh:
            candidate = _try_read_persistent_read_model_candidate(
                aware_root=aware_root,
                repo_root=repo_root,
                locator=locator,
            )
            if candidate is not None:
                source_fingerprint = candidate.source_fingerprint
                cache_key = _cache_key_for_locator(
                    locator=locator,
                    source_fingerprint=source_fingerprint,
                )
                context = self._workspace_required_projection_cache.get(cache_key)
                if context is not None:
                    cache_status = "hit"
                elif candidate.context is not None:
                    context = candidate.context
                    cache_status = "persistent_hit"
                    self._workspace_required_projection_cache[cache_key] = context
                else:
                    context = _context_from_persistent_payload(
                        candidate.context_payload
                    )
                    _try_write_persistent_read_model_context_sidecar(
                        aware_root=aware_root,
                        locator=locator,
                        source_fingerprint=source_fingerprint,
                        context=context,
                    )
                    cache_status = "persistent_hit"
                    self._workspace_required_projection_cache[cache_key] = context

        if context is None:
            if source_fingerprint is None:
                source_fingerprint = _read_model_source_fingerprint(
                    repo_root=repo_root,
                    aware_root=aware_root,
                    required_projection_names=projection_names,
                    required_package_names=package_names,
                    semantic_ontology_package_catalog=(
                        request.semantic_ontology_package_catalog
                    ),
                )
            cache_key = _cache_key_for_locator(
                locator=locator,
                source_fingerprint=source_fingerprint,
            )
            if not request.force_refresh:
                context = self._workspace_required_projection_cache.get(cache_key)
                cache_status = "hit" if context is not None else "miss"
            if context is None and not request.force_refresh:
                context = _try_read_legacy_persistent_read_model_context(
                    aware_root=aware_root,
                    cache_key=cache_key,
                    source_fingerprint=source_fingerprint,
                )
                if context is not None:
                    cache_status = "persistent_hit"
                    self._workspace_required_projection_cache[cache_key] = context
                    _try_write_persistent_read_model_context(
                        aware_root=aware_root,
                        locator=locator,
                        source_fingerprint=source_fingerprint,
                        context=context,
                    )

        if context is None:
            context = (
                build_meta_graph_runtime_context_for_workspace_required_projections(
                    repo_root=repo_root,
                    aware_root=aware_root,
                    required_projection_names=projection_names,
                    required_package_names=package_names,
                    composition_context_id=request.composition_context_id,
                    semantic_ontology_package_catalog=(
                        request.semantic_ontology_package_catalog
                    ),
                    composite_name=request.composite_name,
                )
            )
            if cache_key is None:
                cache_key = _cache_key_for_locator(
                    locator=locator,
                    source_fingerprint=source_fingerprint,
                )
            self._workspace_required_projection_cache[cache_key] = context
            _try_write_persistent_read_model_context(
                aware_root=aware_root,
                locator=locator,
                source_fingerprint=source_fingerprint,
                context=context,
            )

        return MetaRuntimeReadModel(
            read_model_version=_META_RUNTIME_READ_MODEL_VERSION,
            repo_root=repo_root,
            aware_root=aware_root,
            required_projection_names=projection_names,
            required_package_names=package_names,
            context=context,
            projection_hash_by_name=context.projection_hash_by_name,
            runtime_graph_ids=context.runtime_graph_ids,
            source_graph_ids=context.source_graph_ids,
            phase_timings_s=context.phase_timings_s,
            package_timings=context.package_timings,
            cache_status=cache_status,
            provider_duration_s=_round_duration_s(perf_counter() - started_at),
            workspace_commit_truth=(
                request.workspace_commit_truth
                if request.include_workspace_commit_truth
                else None
            ),
        )

    def read_api_activation(
        self,
        request: MetaRuntimeReadModelRequest,
    ) -> MetaApiActivationReadModel:
        started_at = perf_counter()
        projection_names = _clean_required_projection_names(
            request.required_projection_names
        )
        package_names = _clean_required_package_names(request.required_package_names)
        if not projection_names and not package_names:
            raise ValueError(
                "Meta API activation read model requires at least one projection "
                "or package name."
            )
        repo_root = request.repo_root.expanduser().resolve()
        aware_root = (
            request.aware_root.expanduser().resolve()
            if request.aware_root is not None
            else repo_root
        )
        catalog_signature = _semantic_ontology_package_catalog_signature(
            request.semantic_ontology_package_catalog
        )
        locator = _MetaRuntimeReadModelCacheLocator(
            repo_root=repo_root.as_posix(),
            aware_root=aware_root.as_posix(),
            semantic_ontology_package_catalog_signature=catalog_signature,
            composition_context_id=request.composition_context_id,
            required_projection_names=tuple(sorted(projection_names)),
            required_package_names=tuple(sorted(package_names)),
            composite_name=request.composite_name,
        )
        source_fingerprint: Mapping[str, object] | None = None
        cache_key: _MetaRuntimeReadModelCacheKey | None = None
        read_model: MetaApiActivationReadModel | None = None
        cache_status = "miss"

        if not request.force_refresh:
            sidecar = _try_read_persistent_api_activation_read_model_sidecar(
                aware_root=aware_root,
                repo_root=repo_root,
                locator=locator,
                required_projection_names=projection_names,
                required_package_names=package_names,
            )
            if sidecar is not None:
                source_fingerprint, read_model = sidecar
                cache_key = _cache_key_for_locator(
                    locator=locator,
                    source_fingerprint=source_fingerprint,
                )
                cached = self._api_activation_cache.get(cache_key)
                if cached is not None:
                    read_model = cached
                    cache_status = "hit"
                else:
                    cache_status = "persistent_hit"
                    self._api_activation_cache[cache_key] = read_model

        if read_model is None and not request.force_refresh:
            candidate = _try_read_persistent_read_model_candidate(
                aware_root=aware_root,
                repo_root=repo_root,
                locator=locator,
            )
            if candidate is not None:
                source_fingerprint = candidate.source_fingerprint
                cache_key = _cache_key_for_locator(
                    locator=locator,
                    source_fingerprint=source_fingerprint,
                )
                cached = self._api_activation_cache.get(cache_key)
                if cached is not None:
                    read_model = cached
                    cache_status = "hit"
                else:
                    read_model = _api_activation_read_model_from_context_payload(
                        repo_root=repo_root,
                        aware_root=aware_root,
                        required_projection_names=projection_names,
                        required_package_names=package_names,
                        payload=candidate.context_payload,
                        cache_status="persistent_hit",
                        provider_duration_s=0.0,
                    )
                    cache_status = "persistent_hit"
                    self._api_activation_cache[cache_key] = read_model
                    _try_write_persistent_api_activation_read_model_sidecar(
                        aware_root=aware_root,
                        repo_root=repo_root,
                        locator=locator,
                        source_fingerprint=source_fingerprint,
                        read_model=read_model,
                    )

        if read_model is None:
            full_read_model = self.read_workspace_required_projections(
                MetaRuntimeReadModelRequest(
                    repo_root=repo_root,
                    aware_root=aware_root,
                    required_projection_names=projection_names,
                    required_package_names=package_names,
                    composition_context_id=request.composition_context_id,
                    semantic_ontology_package_catalog=(
                        request.semantic_ontology_package_catalog
                    ),
                    composite_name=request.composite_name,
                    force_refresh=request.force_refresh,
                )
            )
            source_fingerprint = _read_model_source_fingerprint(
                repo_root=repo_root,
                aware_root=aware_root,
                required_projection_names=projection_names,
                required_package_names=package_names,
                semantic_ontology_package_catalog=(
                    request.semantic_ontology_package_catalog
                ),
            )
            cache_key = _cache_key_for_locator(
                locator=locator,
                source_fingerprint=source_fingerprint,
            )
            read_model = _api_activation_read_model_from_context(
                repo_root=repo_root,
                aware_root=aware_root,
                required_projection_names=projection_names,
                required_package_names=package_names,
                context=full_read_model.context,
                cache_status=full_read_model.cache_status,
                provider_duration_s=0.0,
            )
            cache_status = full_read_model.cache_status
            self._api_activation_cache[cache_key] = read_model
            _try_write_persistent_api_activation_read_model_sidecar(
                aware_root=aware_root,
                repo_root=repo_root,
                locator=locator,
                source_fingerprint=source_fingerprint,
                read_model=read_model,
            )

        return replace(
            read_model,
            cache_status=cache_status,
            provider_duration_s=_round_duration_s(perf_counter() - started_at),
        )

    def invalidate_workspace(self, *, repo_root: Path) -> None:
        resolved_repo_root = repo_root.expanduser().resolve().as_posix()
        for cache_key in tuple(self._workspace_required_projection_cache):
            if cache_key.repo_root == resolved_repo_root:
                self._workspace_required_projection_cache.pop(cache_key, None)
        for cache_key in tuple(self._api_activation_cache):
            if cache_key.repo_root == resolved_repo_root:
                self._api_activation_cache.pop(cache_key, None)
        _delete_persistent_read_model_cache(repo_root=repo_root)


_DEFAULT_META_RUNTIME_READ_MODEL_PROVIDER = MetaRuntimeReadModelProvider()


def read_workspace_meta_runtime_read_model(
    *,
    repo_root: Path,
    required_projection_names: Iterable[str],
    required_package_names: Iterable[str] = (),
    aware_root: Path | None = None,
    composition_context_id: UUID | None = None,
    semantic_ontology_package_catalog: Mapping[str, object] | None = None,
    composite_name: str = "Aware Workspace Runtime Read Model",
    force_refresh: bool = False,
    include_workspace_commit_truth: bool = False,
    workspace_commit_truth: Mapping[str, object] | None = None,
) -> MetaRuntimeReadModel:
    return (
        _DEFAULT_META_RUNTIME_READ_MODEL_PROVIDER.read_workspace_required_projections(
            MetaRuntimeReadModelRequest(
                repo_root=repo_root,
                aware_root=aware_root,
                required_projection_names=tuple(required_projection_names),
                required_package_names=tuple(required_package_names),
                composition_context_id=composition_context_id,
                semantic_ontology_package_catalog=semantic_ontology_package_catalog,
                composite_name=composite_name,
                force_refresh=force_refresh,
                include_workspace_commit_truth=include_workspace_commit_truth,
                workspace_commit_truth=workspace_commit_truth,
            )
        )
    )


def read_workspace_meta_api_activation_read_model(
    *,
    repo_root: Path,
    required_projection_names: Iterable[str],
    required_package_names: Iterable[str] = (),
    aware_root: Path | None = None,
    composition_context_id: UUID | None = None,
    semantic_ontology_package_catalog: Mapping[str, object] | None = None,
    composite_name: str = "Aware Workspace API Activation Read Model",
    force_refresh: bool = False,
) -> MetaApiActivationReadModel:
    return _DEFAULT_META_RUNTIME_READ_MODEL_PROVIDER.read_api_activation(
        MetaRuntimeReadModelRequest(
            repo_root=repo_root,
            aware_root=aware_root,
            required_projection_names=tuple(required_projection_names),
            required_package_names=tuple(required_package_names),
            composition_context_id=composition_context_id,
            semantic_ontology_package_catalog=semantic_ontology_package_catalog,
            composite_name=composite_name,
            force_refresh=force_refresh,
        )
    )


def _clean_required_projection_names(
    values: Iterable[str],
) -> tuple[str, ...]:
    return _clean_required_strings(values)


def _clean_required_package_names(
    values: Iterable[str],
) -> tuple[str, ...]:
    return _clean_required_strings(values)


def _clean_required_strings(values: Iterable[str]) -> tuple[str, ...]:
    names: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        names.append(text)
    return tuple(names)


def _semantic_ontology_package_catalog_signature(
    catalog: Mapping[str, object] | None,
) -> str:
    if catalog is None:
        return ""
    payload = json.dumps(
        _cache_json_value(catalog),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(
        b"aware-meta-runtime-read-model-catalog-v1\n" + payload
    ).hexdigest()


def _read_model_source_fingerprint(
    *,
    repo_root: Path,
    aware_root: Path,
    required_projection_names: tuple[str, ...],
    required_package_names: tuple[str, ...],
    semantic_ontology_package_catalog: Mapping[str, object] | None,
) -> Mapping[str, object]:
    try:
        manifest_paths = (
            resolve_meta_runtime_package_manifest_closure_for_workspace_read_model(
                repo_root=repo_root,
                aware_root=aware_root,
                required_projection_names=required_projection_names,
                required_package_names=required_package_names,
                semantic_ontology_package_catalog=semantic_ontology_package_catalog,
            )
        )
        return {
            "schema": _META_RUNTIME_READ_MODEL_SOURCE_FINGERPRINT_SCHEMA,
            "status": "ok",
            "packages": [
                _package_manifest_fingerprint(
                    repo_root=repo_root,
                    manifest_path=manifest_path,
                )
                for manifest_path in manifest_paths
            ],
        }
    except Exception as exc:
        return {
            "schema": _META_RUNTIME_READ_MODEL_SOURCE_FINGERPRINT_SCHEMA,
            "status": "unavailable",
            "reason": f"{exc.__class__.__name__}: {exc}",
        }


def _read_model_source_fingerprint_for_manifest_paths(
    *,
    repo_root: Path,
    source_fingerprint: Mapping[str, object],
) -> Mapping[str, object]:
    try:
        packages = _payload_list(source_fingerprint.get("packages"))
        if source_fingerprint.get("status") != "ok" or not packages:
            return {
                "schema": _META_RUNTIME_READ_MODEL_SOURCE_FINGERPRINT_SCHEMA,
                "status": "unavailable",
                "reason": "stored source fingerprint has no package manifest paths",
            }
        manifest_paths = tuple(
            _manifest_path_from_fingerprint_package(
                repo_root=repo_root,
                package_payload=package_payload,
            )
            for package_payload in packages
            if isinstance(package_payload, Mapping)
        )
        if len(manifest_paths) != len(packages):
            return {
                "schema": _META_RUNTIME_READ_MODEL_SOURCE_FINGERPRINT_SCHEMA,
                "status": "unavailable",
                "reason": "stored source fingerprint contains invalid package entries",
            }
        return {
            "schema": _META_RUNTIME_READ_MODEL_SOURCE_FINGERPRINT_SCHEMA,
            "status": "ok",
            "packages": [
                _package_manifest_fingerprint(
                    repo_root=repo_root,
                    manifest_path=manifest_path,
                )
                for manifest_path in manifest_paths
            ],
        }
    except Exception as exc:
        return {
            "schema": _META_RUNTIME_READ_MODEL_SOURCE_FINGERPRINT_SCHEMA,
            "status": "unavailable",
            "reason": f"{exc.__class__.__name__}: {exc}",
        }


def _read_model_fast_source_fingerprint_for_manifest_paths(
    *,
    repo_root: Path,
    source_fingerprint: Mapping[str, object],
) -> Mapping[str, object]:
    try:
        packages = _payload_list(source_fingerprint.get("packages"))
        if source_fingerprint.get("status") != "ok" or not packages:
            return {
                "schema": _META_RUNTIME_READ_MODEL_FAST_SOURCE_FINGERPRINT_SCHEMA,
                "status": "unavailable",
                "reason": "stored source fingerprint has no package manifest paths",
            }
        fast_packages: list[Mapping[str, object]] = []
        for package_payload in packages:
            if not isinstance(package_payload, Mapping):
                return {
                    "schema": _META_RUNTIME_READ_MODEL_FAST_SOURCE_FINGERPRINT_SCHEMA,
                    "status": "unavailable",
                    "reason": "stored source fingerprint contains invalid package entries",
                }
            manifest_path = _manifest_path_from_fingerprint_package(
                repo_root=repo_root,
                package_payload=package_payload,
            )
            spec = load_aware_toml_spec(toml_path=manifest_path)
            build = getattr(spec, "build", None)
            sources_dir = (
                str(
                    package_payload.get("sources_dir")
                    or getattr(build, "sources_dir", "aware")
                    or "aware"
                ).strip()
                or "aware"
            )
            sources_root = (manifest_path.parent / sources_dir).resolve()
            fast_packages.append(
                {
                    "manifest_path": _path_payload(
                        root=repo_root,
                        path=manifest_path,
                    ),
                    "manifest_sha256": _hash_file(manifest_path),
                    "source_stat_signature": _source_tree_stat_signature(
                        sources_root=sources_root,
                        include_paths=_clean_path_patterns(
                            getattr(build, "include_paths", None)
                        ),
                        exclude_paths=_clean_path_patterns(
                            getattr(build, "exclude_paths", None)
                        ),
                    ),
                }
            )
        return {
            "schema": _META_RUNTIME_READ_MODEL_FAST_SOURCE_FINGERPRINT_SCHEMA,
            "status": "ok",
            "packages": fast_packages,
        }
    except Exception as exc:
        return {
            "schema": _META_RUNTIME_READ_MODEL_FAST_SOURCE_FINGERPRINT_SCHEMA,
            "status": "unavailable",
            "reason": f"{exc.__class__.__name__}: {exc}",
        }


def _manifest_path_from_fingerprint_package(
    *,
    repo_root: Path,
    package_payload: Mapping[str, object],
) -> Path:
    value = package_payload.get("manifest_path")
    if value is None:
        raise ValueError("Source fingerprint package has no manifest_path.")
    path = Path(str(value))
    if path.is_absolute():
        return path.expanduser().resolve()
    return (repo_root / path).expanduser().resolve()


def _package_manifest_fingerprint(
    *,
    repo_root: Path,
    manifest_path: Path,
) -> Mapping[str, object]:
    resolved_manifest_path = manifest_path.expanduser().resolve()
    payload: dict[str, object] = {
        "manifest_path": _path_payload(root=repo_root, path=resolved_manifest_path),
        "manifest_sha256": _hash_file(resolved_manifest_path),
    }
    try:
        spec = load_aware_toml_spec(toml_path=resolved_manifest_path)
        package = getattr(spec, "package", None)
        build = getattr(spec, "build", None)
        package_name = str(getattr(package, "package_name", "") or "").strip()
        fqn_prefix = str(getattr(package, "fqn_prefix", "") or "").strip()
        sources_dir = (
            str(getattr(build, "sources_dir", "aware") or "aware").strip() or "aware"
        )
        sources_root = (resolved_manifest_path.parent / sources_dir).resolve()
        payload.update(
            {
                "package_name": package_name,
                "fqn_prefix": fqn_prefix,
                "sources_dir": sources_dir,
                "source_manifest_hash": _source_tree_hash(
                    sources_root=sources_root,
                    include_paths=_clean_path_patterns(
                        getattr(build, "include_paths", None)
                    ),
                    exclude_paths=_clean_path_patterns(
                        getattr(build, "exclude_paths", None)
                    ),
                ),
            }
        )
    except Exception as exc:
        payload.update(
            {
                "status": "unavailable",
                "reason": f"{exc.__class__.__name__}: {exc}",
            }
        )
    return payload


def _source_tree_hash(
    *,
    sources_root: Path,
    include_paths: tuple[str, ...],
    exclude_paths: tuple[str, ...],
) -> str:
    if not sources_root.is_dir():
        return "missing"
    included: set[Path] = set()
    for pattern in include_paths or ("**/*.aware",):
        for candidate in sources_root.glob(pattern):
            if not candidate.is_file() or candidate.suffix != ".aware":
                continue
            resolved = candidate.resolve()
            try:
                resolved.relative_to(sources_root)
            except ValueError:
                continue
            if _has_ignored_segment(resolved.relative_to(sources_root).parts):
                continue
            included.add(resolved)
    for pattern in exclude_paths:
        for candidate in sources_root.glob(pattern):
            if candidate.is_file():
                included.discard(candidate.resolve())
    source_text_by_relative_path = {
        path.relative_to(sources_root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(included)
    }
    return source_text_manifest_hash(
        source_text_by_relative_path=source_text_by_relative_path,
    )


def _source_tree_stat_signature(
    *,
    sources_root: Path,
    include_paths: tuple[str, ...],
    exclude_paths: tuple[str, ...],
) -> str:
    if not sources_root.is_dir():
        return "missing"
    included: set[Path] = set()
    for pattern in include_paths or ("**/*.aware",):
        for candidate in sources_root.glob(pattern):
            if not candidate.is_file() or candidate.suffix != ".aware":
                continue
            resolved = candidate.resolve()
            try:
                resolved.relative_to(sources_root)
            except ValueError:
                continue
            if _has_ignored_segment(resolved.relative_to(sources_root).parts):
                continue
            included.add(resolved)
    for pattern in exclude_paths:
        for candidate in sources_root.glob(pattern):
            if candidate.is_file():
                included.discard(candidate.resolve())
    stat_payload = []
    for path in sorted(included):
        stat = path.stat()
        stat_payload.append(
            (
                path.relative_to(sources_root).as_posix(),
                stat.st_size,
                stat.st_mtime_ns,
            )
        )
    return _stable_json_sha256(stat_payload)


def _has_ignored_segment(parts: Iterable[str]) -> bool:
    return any(
        part in {".aware", ".git", "__pycache__", "node_modules", ".venv", "venv"}
        for part in parts
    )


def _clean_path_patterns(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def _try_read_persistent_api_activation_read_model_sidecar(
    *,
    aware_root: Path,
    repo_root: Path,
    locator: _MetaRuntimeReadModelCacheLocator,
    required_projection_names: tuple[str, ...],
    required_package_names: tuple[str, ...],
) -> tuple[Mapping[str, object], MetaApiActivationReadModel] | None:
    path = _persistent_api_activation_read_model_sidecar_path(
        aware_root=aware_root,
        locator=locator,
    )
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, Mapping):
        return None
    if payload.get("schema") != _META_API_ACTIVATION_READ_MODEL_SIDECAR_SCHEMA:
        return None
    if payload.get("cache_locator") != _read_model_cache_locator_payload(locator):
        return None
    stored_fingerprint = payload.get("source_fingerprint")
    if not isinstance(stored_fingerprint, Mapping):
        return None
    stored_fast_fingerprint = payload.get("source_fast_fingerprint")
    if not isinstance(stored_fast_fingerprint, Mapping):
        return None
    source_fast_fingerprint = _read_model_fast_source_fingerprint_for_manifest_paths(
        repo_root=repo_root,
        source_fingerprint=stored_fingerprint,
    )
    if source_fast_fingerprint.get("status") != "ok":
        return None
    if _cache_json_value(source_fast_fingerprint) != _cache_json_value(
        stored_fast_fingerprint
    ):
        return None
    compact_payload = payload.get("api_activation")
    if not isinstance(compact_payload, Mapping):
        return None
    try:
        read_model = _api_activation_read_model_from_compact_payload(
            repo_root=repo_root,
            aware_root=aware_root,
            required_projection_names=required_projection_names,
            required_package_names=required_package_names,
            payload=compact_payload,
            cache_status="persistent_hit",
            provider_duration_s=0.0,
        )
    except Exception:
        return None
    return stored_fingerprint, read_model


def _try_write_persistent_api_activation_read_model_sidecar(
    *,
    aware_root: Path,
    repo_root: Path,
    locator: _MetaRuntimeReadModelCacheLocator,
    source_fingerprint: Mapping[str, object],
    read_model: MetaApiActivationReadModel,
) -> bool:
    if source_fingerprint.get("status") != "ok":
        return False
    path = _persistent_api_activation_read_model_sidecar_path(
        aware_root=aware_root,
        locator=locator,
    )
    payload = {
        "schema": _META_API_ACTIVATION_READ_MODEL_SIDECAR_SCHEMA,
        "cache_locator": _read_model_cache_locator_payload(locator),
        "source_fingerprint": _cache_json_value(source_fingerprint),
        "source_fast_fingerprint": _cache_json_value(
            _read_model_fast_source_fingerprint_for_manifest_paths(
                repo_root=repo_root,
                source_fingerprint=source_fingerprint,
            )
        ),
        "api_activation": _api_activation_persistent_payload_from_read_model(
            read_model
        ),
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(
                payload,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        tmp.replace(path)
        return True
    except Exception:
        return False


def _try_read_persistent_read_model_candidate(
    *,
    aware_root: Path,
    repo_root: Path,
    locator: _MetaRuntimeReadModelCacheLocator,
) -> _PersistentReadModelCandidate | None:
    path = _persistent_read_model_locator_cache_path(
        aware_root=aware_root,
        locator=locator,
    )
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, Mapping):
        return None
    if payload.get("schema") != _META_RUNTIME_READ_MODEL_CACHE_SCHEMA:
        return None
    locator_payload = _read_model_cache_locator_payload(locator)
    if payload.get("cache_locator") != locator_payload:
        return None
    stored_fingerprint = payload.get("source_fingerprint")
    if not isinstance(stored_fingerprint, Mapping):
        return None
    source_fingerprint = _read_model_source_fingerprint_for_manifest_paths(
        repo_root=repo_root,
        source_fingerprint=stored_fingerprint,
    )
    if source_fingerprint.get("status") != "ok":
        return None
    if _cache_json_value(source_fingerprint) != _cache_json_value(stored_fingerprint):
        return None
    context_payload = payload.get("context")
    if not isinstance(context_payload, Mapping):
        return None
    context = _try_read_persistent_read_model_context_sidecar(
        aware_root=aware_root,
        locator=locator,
        source_fingerprint=source_fingerprint,
    )
    return _PersistentReadModelCandidate(
        source_fingerprint=source_fingerprint,
        context_payload=context_payload,
        context=context,
    )


def _try_read_legacy_persistent_read_model_context(
    *,
    aware_root: Path,
    cache_key: _MetaRuntimeReadModelCacheKey,
    source_fingerprint: Mapping[str, object],
) -> MetaGraphRuntimeContext | None:
    if source_fingerprint.get("status") != "ok":
        return None
    path = _persistent_read_model_cache_path(
        aware_root=aware_root,
        cache_key=cache_key,
    )
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, Mapping):
        return None
    if payload.get("schema") != _META_RUNTIME_READ_MODEL_CACHE_SCHEMA_V1:
        return None
    cache_key_payload = _read_model_cache_key_payload(cache_key)
    if payload.get("cache_key") != cache_key_payload:
        return None
    if payload.get("source_fingerprint") != _cache_json_value(source_fingerprint):
        return None
    context_payload = payload.get("context")
    if not isinstance(context_payload, Mapping):
        return None
    try:
        return _context_from_persistent_payload(context_payload)
    except Exception:
        return None


def _try_write_persistent_read_model_context(
    *,
    aware_root: Path,
    locator: _MetaRuntimeReadModelCacheLocator,
    source_fingerprint: Mapping[str, object],
    context: MetaGraphRuntimeContext,
) -> None:
    if source_fingerprint.get("status") != "ok":
        return
    path = _persistent_read_model_locator_cache_path(
        aware_root=aware_root,
        locator=locator,
    )
    payload = {
        "schema": _META_RUNTIME_READ_MODEL_CACHE_SCHEMA,
        "cache_locator": _read_model_cache_locator_payload(locator),
        "source_fingerprint": _cache_json_value(source_fingerprint),
        "context": _persistent_payload_from_context(context),
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(
                payload,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        tmp.replace(path)
    except Exception:
        return


def _persistent_payload_from_context(
    context: MetaGraphRuntimeContext,
) -> Mapping[str, object]:
    return {
        "composite_name": str(getattr(context.index.ocg, "name", "") or ""),
        "composition_context_id": (
            str(context.composition_context_id)
            if context.composition_context_id is not None
            else None
        ),
        "implementation_policy": _implementation_policy_payload(
            context.implementation_policy
        ),
        "runtime_handler_provider_import_roots": list(
            context.runtime_handler_provider_import_roots
        ),
        "runtime_graphs": [
            _object_config_graph_payload(graph) for graph in context.runtime_graphs
        ],
        "source_graph_ids": [str(graph_id) for graph_id in context.source_graph_ids],
        "runtime_graph_by_package_name": {
            package_name: str(graph.id)
            for package_name, graph in context.runtime_graph_by_package_name.items()
            if graph.id is not None
        },
        "package_timings": [
            _package_timing_payload(timing) for timing in context.package_timings
        ],
    }


def _api_activation_read_model_from_context(
    *,
    repo_root: Path,
    aware_root: Path,
    required_projection_names: tuple[str, ...],
    required_package_names: tuple[str, ...],
    context: MetaGraphRuntimeContext,
    cache_status: str,
    provider_duration_s: float,
) -> MetaApiActivationReadModel:
    return _api_activation_read_model_from_compact_payload(
        repo_root=repo_root,
        aware_root=aware_root,
        required_projection_names=required_projection_names,
        required_package_names=required_package_names,
        payload=_api_activation_persistent_payload_from_context(context),
        cache_status=cache_status,
        provider_duration_s=provider_duration_s,
    )


def _api_activation_read_model_from_context_payload(
    *,
    repo_root: Path,
    aware_root: Path,
    required_projection_names: tuple[str, ...],
    required_package_names: tuple[str, ...],
    payload: Mapping[str, object],
    cache_status: str,
    provider_duration_s: float,
) -> MetaApiActivationReadModel:
    return _api_activation_read_model_from_compact_payload(
        repo_root=repo_root,
        aware_root=aware_root,
        required_projection_names=required_projection_names,
        required_package_names=required_package_names,
        payload=_api_activation_persistent_payload_from_context_payload(payload),
        cache_status=cache_status,
        provider_duration_s=provider_duration_s,
    )


def _api_activation_persistent_payload_from_context(
    context: MetaGraphRuntimeContext,
) -> Mapping[str, object]:
    return {
        "projection_hash_by_name": dict(context.projection_hash_by_name),
        "runtime_graph_ids": [str(graph_id) for graph_id in context.runtime_graph_ids],
        "source_graph_ids": [str(graph_id) for graph_id in context.source_graph_ids],
        "runtime_handler_provider_import_roots": list(
            context.runtime_handler_provider_import_roots
        ),
        "object_projection_graphs": [
            _minimal_object_projection_graph_payload(opg)
            for opg in context.index.opg_by_hash.values()
        ],
        "class_configs": [
            _minimal_class_config_payload(class_config)
            for class_config in context.index.class_configs_by_id.values()
        ],
        "composition_context_id": (
            str(context.composition_context_id)
            if context.composition_context_id is not None
            else None
        ),
        "package_timings": [
            _package_timing_payload(timing) for timing in context.package_timings
        ],
        "phase_timings_s": dict(context.phase_timings_s),
    }


def _api_activation_persistent_payload_from_context_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    projection_hash_by_name: dict[str, str] = {}
    runtime_graph_ids: list[str] = []
    class_config_by_id: dict[str, Mapping[str, object]] = {}
    opg_by_hash: dict[str, Mapping[str, object]] = {}

    for graph_payload in _payload_list(payload.get("runtime_graphs")):
        if not isinstance(graph_payload, Mapping):
            continue
        graph_id = _optional_uuid(graph_payload.get("id"))
        if graph_id is not None:
            runtime_graph_ids.append(str(graph_id))
        for node_payload in _payload_list(
            graph_payload.get("object_config_graph_nodes")
        ):
            if not isinstance(node_payload, Mapping):
                continue
            class_payload = node_payload.get("class_config")
            if not isinstance(class_payload, Mapping):
                continue
            class_id = _optional_uuid(class_payload.get("id"))
            if class_id is not None:
                class_config_by_id[str(class_id)] = _minimal_class_config_payload(
                    class_payload
                )
        for opg_payload in _payload_list(graph_payload.get("object_projection_graphs")):
            if not isinstance(opg_payload, Mapping):
                continue
            name = str(opg_payload.get("name") or "").strip()
            projection_hash = str(opg_payload.get("projection_hash") or "").strip()
            if not name or not projection_hash:
                continue
            projection_hash_by_name.setdefault(name, projection_hash)
            opg_by_hash[projection_hash] = _minimal_object_projection_graph_payload(
                opg_payload
            )

    return {
        "projection_hash_by_name": projection_hash_by_name,
        "runtime_graph_ids": runtime_graph_ids,
        "source_graph_ids": [
            str(graph_id) for graph_id in _source_graph_ids_from_payload(payload)
        ],
        "runtime_handler_provider_import_roots": [
            str(value)
            for value in _payload_list(
                payload.get("runtime_handler_provider_import_roots")
            )
            if str(value).strip()
        ],
        "object_projection_graphs": list(opg_by_hash.values()),
        "class_configs": list(class_config_by_id.values()),
        "composition_context_id": (
            str(payload.get("composition_context_id"))
            if payload.get("composition_context_id") is not None
            else None
        ),
        "package_timings": _cache_json_value(payload.get("package_timings") or []),
        "phase_timings_s": {},
    }


def _api_activation_persistent_payload_from_read_model(
    read_model: MetaApiActivationReadModel,
) -> Mapping[str, object]:
    return {
        "projection_hash_by_name": dict(read_model.projection_hash_by_name),
        "runtime_graph_ids": [
            str(graph_id) for graph_id in read_model.runtime_graph_ids
        ],
        "source_graph_ids": [str(graph_id) for graph_id in read_model.source_graph_ids],
        "runtime_handler_provider_import_roots": list(
            read_model.runtime_handler_provider_import_roots
        ),
        "object_projection_graphs": [
            _minimal_object_projection_graph_payload(opg)
            for opg in read_model.index.opg_by_hash.values()
        ],
        "class_configs": [
            _minimal_class_config_payload(class_config)
            for class_config in read_model.index.class_configs_by_id.values()
        ],
        "composition_context_id": (
            str(read_model.index.composition_context_id)
            if read_model.index.composition_context_id is not None
            else None
        ),
        "package_timings": [
            _package_timing_payload(timing) for timing in read_model.package_timings
        ],
        "phase_timings_s": dict(read_model.phase_timings_s),
    }


def _minimal_object_projection_graph_payload(
    value: ObjectProjectionGraph | Mapping[str, object],
) -> Mapping[str, object]:
    if isinstance(value, ObjectProjectionGraph):
        raw = value.model_dump(mode="json", by_alias=True, exclude_none=True)
    else:
        raw = value
    payload: dict[str, object] = {}
    for key in (
        "id",
        "object_config_graph_id",
        "language",
        "name",
        "projection_hash",
        "supports_virtual_build",
    ):
        item = raw.get(key)
        if item is not None:
            payload[key] = item
    nodes: list[Mapping[str, object]] = []
    for node in _payload_list(raw.get("object_projection_graph_nodes")):
        if not isinstance(node, Mapping):
            continue
        node_payload: dict[str, object] = {}
        for key in (
            "id",
            "object_projection_graph_id",
            "class_config_id",
            "is_root",
            "policy_refs",
            "required_for_validity",
            "selection",
            "selector_condition_id",
            "top_n",
        ):
            item = node.get(key)
            if item is not None:
                node_payload[key] = item
        nodes.append(node_payload)
    if nodes:
        payload["object_projection_graph_nodes"] = nodes
    return payload


def _minimal_class_config_payload(
    value: ClassConfig | Mapping[str, object],
) -> Mapping[str, object]:
    if isinstance(value, ClassConfig):
        raw = value.model_dump(mode="json", by_alias=True, exclude_none=True)
    else:
        raw = value
    payload: dict[str, object] = {}
    for key in (
        "id",
        "class_fqn",
        "name",
        "description",
        "is_base",
        "is_edge",
        "value_mode",
        "identity_mode",
        "object_config_graph_node_id",
        "parent_class_id",
        "code_section_class_id",
    ):
        item = raw.get(key)
        if item is not None:
            payload[key] = item
    return payload


def _api_activation_read_model_from_compact_payload(
    *,
    repo_root: Path,
    aware_root: Path,
    required_projection_names: tuple[str, ...],
    required_package_names: tuple[str, ...],
    payload: Mapping[str, object],
    cache_status: str,
    provider_duration_s: float,
) -> MetaApiActivationReadModel:
    opgs = tuple(
        ObjectProjectionGraph.model_validate(opg_payload)
        for opg_payload in _payload_list(payload.get("object_projection_graphs"))
        if isinstance(opg_payload, Mapping)
    )
    class_configs = tuple(
        ClassConfig.model_validate(class_payload)
        for class_payload in _payload_list(payload.get("class_configs"))
        if isinstance(class_payload, Mapping)
    )
    class_configs_by_id = {
        class_config.id: class_config
        for class_config in class_configs
        if class_config.id is not None
    }
    composition_context_id = _optional_uuid(payload.get("composition_context_id"))
    compact_ocg = ObjectConfigGraph(
        id=_api_activation_compact_ocg_id(payload),
        name="Meta API Activation Runtime Index",
        hash=_stable_json_sha256(payload),
        fqn_prefix="aware_meta.api_activation",
        language=CodeLanguage.aware,
        object_projection_graphs=list(opgs),
    )
    index = MetaGraphRuntimeIndexSnapshot(
        ocg=compact_ocg,
        class_configs_by_id=class_configs_by_id,
        attribute_configs_by_id={},
        relationships_by_id={},
        opg_by_id={opg.id: opg for opg in opgs if opg.id is not None},
        opg_by_hash={
            str(opg.projection_hash): opg
            for opg in opgs
            if str(opg.projection_hash or "").strip()
        },
        portal_index=ObjectProjectionGraphPortalIndex(),
        composition_context_id=composition_context_id,
        runtime_handler_provider_import_roots=tuple(
            str(value)
            for value in _payload_list(
                payload.get("runtime_handler_provider_import_roots")
            )
            if str(value).strip()
        ),
    )
    projection_hash_by_name = {
        str(key): str(value)
        for key, value in _mapping_payload(
            payload.get("projection_hash_by_name")
        ).items()
        if str(key).strip() and str(value).strip()
    }
    return MetaApiActivationReadModel(
        read_model_version=_META_API_ACTIVATION_READ_MODEL_VERSION,
        repo_root=repo_root,
        aware_root=aware_root,
        required_projection_names=required_projection_names,
        required_package_names=required_package_names,
        index=index,
        projection_hash_by_name=projection_hash_by_name,
        runtime_graph_ids=tuple(
            graph_id
            for value in _payload_list(payload.get("runtime_graph_ids"))
            for graph_id in (_optional_uuid(value),)
            if graph_id is not None
        ),
        source_graph_ids=tuple(
            graph_id
            for value in _payload_list(payload.get("source_graph_ids"))
            for graph_id in (_optional_uuid(value),)
            if graph_id is not None
        ),
        runtime_handler_provider_import_roots=(
            index.runtime_handler_provider_import_roots
        ),
        phase_timings_s=_float_mapping(payload.get("phase_timings_s")),
        package_timings=_package_timings_from_payload(payload.get("package_timings")),
        cache_status=cache_status,
        provider_duration_s=provider_duration_s,
    )


def _api_activation_compact_ocg_id(payload: Mapping[str, object]) -> UUID:
    return UUID(
        _stable_json_sha256(
            {
                "kind": "aware.meta.api_activation.compact_ocg",
                "object_projection_graphs": payload.get("object_projection_graphs"),
                "class_configs": payload.get("class_configs"),
            }
        )[:32]
    )


def _context_from_persistent_payload(
    payload: Mapping[str, object],
) -> MetaGraphRuntimeContext:
    with _meta_read_model_cache_load_context():
        runtime_graphs = tuple(
            ObjectConfigGraph.model_validate(graph_payload)
            for graph_payload in _payload_list(payload.get("runtime_graphs"))
            if isinstance(graph_payload, Mapping)
        )
        if not runtime_graphs:
            raise ValueError("Persistent Meta read-model cache has no runtime graphs.")
        runtime_graph_by_id = {
            str(graph.id): graph for graph in runtime_graphs if graph.id is not None
        }
        composition_context_id = _optional_uuid(payload.get("composition_context_id"))
        source_graph_ids = _source_graph_ids_from_payload(payload)
        context = build_meta_graph_runtime_context(
            runtime_graphs=runtime_graphs,
            runtime_graph_by_package_name=_package_graph_mapping_from_payload(
                payload.get("runtime_graph_by_package_name"),
                graphs_by_id=runtime_graph_by_id,
            ),
            composition_context_id=composition_context_id,
            composite_name=str(
                payload.get("composite_name") or "Meta Read Model Cache"
            ),
            implementation_policy=_implementation_policy_from_payload(
                payload.get("implementation_policy")
            ),
            package_timings=_package_timings_from_payload(
                payload.get("package_timings")
            ),
            runtime_handler_provider_import_roots=tuple(
                str(value)
                for value in _payload_list(
                    payload.get("runtime_handler_provider_import_roots")
                )
                if str(value).strip()
            ),
        )
    phase_timings = dict(context.phase_timings_s)
    phase_timings["persistent_read_model_cache"] = 1.0
    return replace(
        context,
        source_graph_ids=source_graph_ids,
        source_graphs=(),
        source_graph_by_package_name={},
        phase_timings_s=phase_timings,
    )


@contextmanager
def _meta_read_model_cache_load_context() -> Iterator[None]:
    with ExitStack() as stack:
        try:
            from aware_orm.session.autobind import disable_autobind

            stack.enter_context(disable_autobind())
        except Exception:
            pass
        try:
            from aware_orm.session.change_collector import disable_tracked_list_wrapping

            stack.enter_context(disable_tracked_list_wrapping())
        except Exception:
            pass
        yield


def _bool_env_default_true(name: str) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    return True


def _meta_read_model_pickle_sidecar_enabled() -> bool:
    return _bool_env_default_true(_META_RUNTIME_READ_MODEL_PICKLE_SIDECAR_ENV)


def _try_read_persistent_read_model_context_sidecar(
    *,
    aware_root: Path,
    locator: _MetaRuntimeReadModelCacheLocator,
    source_fingerprint: Mapping[str, object],
) -> MetaGraphRuntimeContext | None:
    if not _meta_read_model_pickle_sidecar_enabled():
        return None
    path = _persistent_read_model_context_sidecar_path(
        aware_root=aware_root,
        locator=locator,
    )
    if not path.is_file():
        return None
    try:
        with _meta_read_model_cache_load_context():
            payload = pickle.loads(path.read_bytes())
    except Exception:
        return None
    if not isinstance(payload, Mapping):
        return None
    if payload.get("schema") != _META_RUNTIME_READ_MODEL_CONTEXT_PICKLE_SCHEMA:
        return None
    if payload.get("cache_locator") != _read_model_cache_locator_payload(locator):
        return None
    if payload.get("source_fingerprint") != _cache_json_value(source_fingerprint):
        return None
    context = payload.get("context")
    if not isinstance(context, MetaGraphRuntimeContext):
        return None
    return context


def _try_write_persistent_read_model_context_sidecar(
    *,
    aware_root: Path,
    locator: _MetaRuntimeReadModelCacheLocator,
    source_fingerprint: Mapping[str, object],
    context: MetaGraphRuntimeContext,
) -> bool:
    if not _meta_read_model_pickle_sidecar_enabled():
        return False
    payload_bytes = _persistent_read_model_context_sidecar_bytes(
        locator=locator,
        source_fingerprint=source_fingerprint,
        context=context,
    )
    if payload_bytes is None:
        try:
            sidecar_context = _sidecar_safe_context(context)
        except Exception:
            return False
        payload_bytes = _persistent_read_model_context_sidecar_bytes(
            locator=locator,
            source_fingerprint=source_fingerprint,
            context=sidecar_context,
        )
    if payload_bytes is None:
        return False
    path = _persistent_read_model_context_sidecar_path(
        aware_root=aware_root,
        locator=locator,
    )
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_bytes(payload_bytes)
        tmp.replace(path)
        return True
    except Exception:
        return False


def _persistent_read_model_context_sidecar_bytes(
    *,
    locator: _MetaRuntimeReadModelCacheLocator,
    source_fingerprint: Mapping[str, object],
    context: MetaGraphRuntimeContext,
) -> bytes | None:
    payload = {
        "schema": _META_RUNTIME_READ_MODEL_CONTEXT_PICKLE_SCHEMA,
        "cache_locator": _read_model_cache_locator_payload(locator),
        "source_fingerprint": _cache_json_value(source_fingerprint),
        "context": context,
    }
    try:
        with _meta_read_model_cache_load_context():
            payload_bytes = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
            roundtrip_payload = pickle.loads(payload_bytes)
        if not isinstance(roundtrip_payload, Mapping):
            return None
        if not isinstance(roundtrip_payload.get("context"), MetaGraphRuntimeContext):
            return None
        return payload_bytes
    except Exception:
        return None


def _sidecar_safe_context(context: MetaGraphRuntimeContext) -> MetaGraphRuntimeContext:
    with _meta_read_model_cache_load_context():
        runtime_graphs = tuple(
            ObjectConfigGraph.model_validate(_object_config_graph_payload(graph))
            for graph in context.runtime_graphs
        )
        source_graphs = tuple(
            ObjectConfigGraph.model_validate(_object_config_graph_payload(graph))
            for graph in context.source_graphs
        )
        index_ocg = ObjectConfigGraph.model_validate(
            _object_config_graph_payload(context.index.ocg)
        )
        index = build_meta_graph_runtime_index_snapshot(
            ocg=index_ocg,
            composition_context_id=context.index.composition_context_id,
        )
    if context.index.runtime_handler_provider_import_roots:
        index = replace(
            index,
            runtime_handler_provider_import_roots=(
                context.index.runtime_handler_provider_import_roots
            ),
        )
    runtime_graphs_by_id = {
        str(graph.id): graph for graph in runtime_graphs if graph.id is not None
    }
    source_graphs_by_id = {
        str(graph.id): graph for graph in source_graphs if graph.id is not None
    }
    return replace(
        context,
        index=index,
        runtime_graphs=runtime_graphs,
        source_graphs=source_graphs,
        runtime_graph_by_package_name=_sidecar_graph_mapping(
            context.runtime_graph_by_package_name,
            graphs_by_id=runtime_graphs_by_id,
        ),
        source_graph_by_package_name=_sidecar_graph_mapping(
            context.source_graph_by_package_name,
            graphs_by_id=source_graphs_by_id,
        ),
    )


def _sidecar_graph_mapping(
    value: Mapping[str, ObjectConfigGraph],
    *,
    graphs_by_id: Mapping[str, ObjectConfigGraph],
) -> Mapping[str, ObjectConfigGraph]:
    result: dict[str, ObjectConfigGraph] = {}
    with _meta_read_model_cache_load_context():
        for package_name, graph in value.items():
            normalized_graph = graphs_by_id.get(str(graph.id))
            if normalized_graph is None:
                normalized_graph = ObjectConfigGraph.model_validate(
                    _object_config_graph_payload(graph)
                )
            result[str(package_name)] = normalized_graph
    return result


def _object_config_graph_payload(graph: ObjectConfigGraph) -> Mapping[str, object]:
    return graph.model_dump(mode="json", by_alias=True, exclude_none=True)


def _source_graph_ids_from_payload(payload: Mapping[str, object]) -> tuple[UUID, ...]:
    explicit_ids = tuple(
        uuid
        for value in _payload_list(payload.get("source_graph_ids"))
        for uuid in (_optional_uuid(value),)
        if uuid is not None
    )
    if explicit_ids:
        return explicit_ids
    return tuple(
        uuid
        for graph_payload in _payload_list(payload.get("source_graphs"))
        if isinstance(graph_payload, Mapping)
        for uuid in (_optional_uuid(graph_payload.get("id")),)
        if uuid is not None
    )


def _implementation_policy_payload(
    policy: MetaGraphImplementationPolicy,
) -> Mapping[str, object]:
    return {
        "default_function_impl_ownership": (
            policy.default_function_impl_ownership.value
        ),
        "function_impl_ownership_by_owner_key": {
            key: value.value
            for key, value in policy.function_impl_ownership_by_owner_key.items()
        },
        "function_impl_ownership_by_owner_prefix": {
            key: value.value
            for key, value in policy.function_impl_ownership_by_owner_prefix.items()
        },
    }


def _implementation_policy_from_payload(value: object) -> MetaGraphImplementationPolicy:
    if not isinstance(value, Mapping):
        return MetaGraphImplementationPolicy()
    return MetaGraphImplementationPolicy(
        default_function_impl_ownership=_ownership_from_value(
            value.get("default_function_impl_ownership")
        ),
        function_impl_ownership_by_owner_key=_ownership_mapping_from_payload(
            value.get("function_impl_ownership_by_owner_key")
        ),
        function_impl_ownership_by_owner_prefix=_ownership_mapping_from_payload(
            value.get("function_impl_ownership_by_owner_prefix")
        ),
    )


def _ownership_mapping_from_payload(
    value: object,
) -> Mapping[str, MetaGraphFunctionImplOwnership]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(key): _ownership_from_value(item)
        for key, item in value.items()
        if str(key).strip()
    }


def _ownership_from_value(value: object) -> MetaGraphFunctionImplOwnership:
    try:
        return MetaGraphFunctionImplOwnership(str(value))
    except Exception:
        return MetaGraphFunctionImplOwnership.authored


def _package_timing_payload(
    timing: MetaGraphRuntimePackageTiming,
) -> Mapping[str, object]:
    return {
        "package_name": timing.package_name,
        "manifest_path": timing.manifest_path,
        "cache_status": timing.cache_status,
        "cache_source": timing.cache_source,
        "cache_miss_reason": timing.cache_miss_reason,
        "phase_timings_s": dict(timing.phase_timings_s),
    }


def _package_timings_from_payload(
    value: object,
) -> tuple[MetaGraphRuntimePackageTiming, ...]:
    timings: list[MetaGraphRuntimePackageTiming] = []
    for item in _payload_list(value):
        if not isinstance(item, Mapping):
            continue
        timings.append(
            MetaGraphRuntimePackageTiming(
                package_name=str(item.get("package_name") or ""),
                manifest_path=str(item.get("manifest_path") or ""),
                cache_status=str(item.get("cache_status") or "persistent_hit"),
                cache_source=_optional_string(item.get("cache_source")),
                cache_miss_reason=_optional_string(item.get("cache_miss_reason")),
                phase_timings_s=_float_mapping(item.get("phase_timings_s")),
            )
        )
    return tuple(timings)


def _package_graph_mapping_from_payload(
    value: object,
    *,
    graphs_by_id: Mapping[str, ObjectConfigGraph],
) -> Mapping[str, ObjectConfigGraph]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(package_name): graph
        for package_name, graph_id in value.items()
        for graph in (graphs_by_id.get(str(graph_id)),)
        if str(package_name).strip() and graph is not None
    }


def _cache_key_for_locator(
    *,
    locator: _MetaRuntimeReadModelCacheLocator,
    source_fingerprint: Mapping[str, object],
) -> _MetaRuntimeReadModelCacheKey:
    return _MetaRuntimeReadModelCacheKey(
        repo_root=locator.repo_root,
        aware_root=locator.aware_root,
        semantic_ontology_package_catalog_signature=(
            locator.semantic_ontology_package_catalog_signature
        ),
        source_fingerprint_signature=_stable_json_sha256(source_fingerprint),
        composition_context_id=locator.composition_context_id,
        required_projection_names=locator.required_projection_names,
        required_package_names=locator.required_package_names,
        composite_name=locator.composite_name,
    )


def _payload_list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _mapping_payload(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def _optional_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(str(value))
    except Exception:
        return None


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _float_mapping(value: object) -> Mapping[str, float]:
    if not isinstance(value, Mapping):
        return {}
    result: dict[str, float] = {}
    for key, item in value.items():
        try:
            result[str(key)] = float(item)
        except Exception:
            continue
    return result


def _persistent_read_model_cache_path(
    *,
    aware_root: Path,
    cache_key: _MetaRuntimeReadModelCacheKey,
) -> Path:
    digest = _stable_json_sha256(_read_model_cache_key_payload(cache_key))
    return (
        aware_root.expanduser().resolve()
        / ".aware"
        / "meta"
        / "runtime"
        / "read_model"
        / f"{digest}.json"
    )


def _persistent_read_model_locator_cache_path(
    *,
    aware_root: Path,
    locator: _MetaRuntimeReadModelCacheLocator,
) -> Path:
    digest = _stable_json_sha256(_read_model_cache_locator_payload(locator))
    return (
        aware_root.expanduser().resolve()
        / ".aware"
        / "meta"
        / "runtime"
        / "read_model"
        / f"{digest}.json"
    )


def _persistent_read_model_context_sidecar_path(
    *,
    aware_root: Path,
    locator: _MetaRuntimeReadModelCacheLocator,
) -> Path:
    return _persistent_read_model_locator_cache_path(
        aware_root=aware_root,
        locator=locator,
    ).with_suffix(".context.pickle")


def _persistent_api_activation_read_model_sidecar_path(
    *,
    aware_root: Path,
    locator: _MetaRuntimeReadModelCacheLocator,
) -> Path:
    return _persistent_read_model_locator_cache_path(
        aware_root=aware_root,
        locator=locator,
    ).with_suffix(".api_activation.json")


def _delete_persistent_read_model_cache(*, repo_root: Path) -> None:
    cache_dir = (
        repo_root.expanduser().resolve() / ".aware" / "meta" / "runtime" / "read_model"
    )
    if not cache_dir.is_dir():
        return
    for pattern in ("*.json", "*.context.pickle", "*.api_activation.json"):
        for path in cache_dir.glob(pattern):
            try:
                path.unlink()
            except Exception:
                continue
    for path in cache_dir.glob("*.tmp"):
        try:
            path.unlink()
        except Exception:
            continue


def _read_model_cache_key_payload(
    cache_key: _MetaRuntimeReadModelCacheKey,
) -> Mapping[str, object]:
    return {
        "read_model_version": _META_RUNTIME_READ_MODEL_VERSION,
        "repo_root": cache_key.repo_root,
        "aware_root": cache_key.aware_root,
        "semantic_ontology_package_catalog_signature": (
            cache_key.semantic_ontology_package_catalog_signature
        ),
        "source_fingerprint_signature": cache_key.source_fingerprint_signature,
        "composition_context_id": (
            str(cache_key.composition_context_id)
            if cache_key.composition_context_id is not None
            else None
        ),
        "required_projection_names": list(cache_key.required_projection_names),
        "required_package_names": list(cache_key.required_package_names),
        "composite_name": cache_key.composite_name,
    }


def _read_model_cache_locator_payload(
    locator: _MetaRuntimeReadModelCacheLocator,
) -> Mapping[str, object]:
    return {
        "read_model_version": _META_RUNTIME_READ_MODEL_VERSION,
        "repo_root": locator.repo_root,
        "aware_root": locator.aware_root,
        "semantic_ontology_package_catalog_signature": (
            locator.semantic_ontology_package_catalog_signature
        ),
        "composition_context_id": (
            str(locator.composition_context_id)
            if locator.composition_context_id is not None
            else None
        ),
        "required_projection_names": list(locator.required_projection_names),
        "required_package_names": list(locator.required_package_names),
        "composite_name": locator.composite_name,
    }


def _stable_json_sha256(value: object) -> str:
    payload = json.dumps(
        _cache_json_value(value),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _path_payload(*, root: Path, path: Path) -> str:
    resolved_root = root.expanduser().resolve()
    resolved_path = path.expanduser().resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError:
        return resolved_path.as_posix()


def _cache_json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _cache_json_value(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }
    if isinstance(value, (list, tuple)):
        return [_cache_json_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _round_duration_s(duration_s: float) -> float:
    return round(duration_s, 6)


__all__ = [
    "MetaApiActivationReadModel",
    "MetaRuntimeReadModel",
    "MetaRuntimeReadModelProvider",
    "MetaRuntimeReadModelRequest",
    "read_workspace_meta_api_activation_read_model",
    "read_workspace_meta_runtime_read_model",
]
