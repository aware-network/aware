from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
import hashlib
import json
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from aware_meta.package_graph_reuse_cache import (
    OBJECT_CONFIG_GRAPH_PACKAGE_CONTEXT_GRAPHS_DERIVATION_SIGNATURE,
    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS,
    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_MATERIALIZED_PACKAGE,
    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_VERSION,
    read_object_config_graph_package_context_reuse_cache_payload,
    read_object_config_graph_package_reuse_cache_payload,
)
from aware_meta_ontology.stable_ids import (
    stable_object_config_graph_package_id,
)


META_RUNTIME_PACKAGE_PROJECTION_INDEX_SCHEMA = (
    "aware.meta.runtime.package_projection_index.v1"
)
META_RUNTIME_PACKAGE_PROJECTION_INDEX_VERSION = 1
META_RUNTIME_PACKAGE_PROJECTION_LOOKUP_SCHEMA = (
    "aware.meta.runtime.package_projection_lookup.v1"
)
META_RUNTIME_PACKAGE_PROJECTION_LOOKUP_VERSION = 1
META_RUNTIME_SEMANTIC_OBJECT_PAYLOAD_STORAGE = "compact_baseline_fields"
META_RUNTIME_SEMANTIC_OBJECT_SOURCE_REF_STORAGE = "catalog"

_SEMANTIC_OBJECT_COMPACT_PAYLOAD_KEYS = frozenset(
    {
        "attribute_config_id",
        "attribute_membership_owner_kind",
        "attribute_membership_semantic_key",
        "attribute_membership_signature",
        "attribute_name",
        "attribute_signature",
        "class_config_attribute_config_id",
        "class_config_function_config_id",
        "class_config_id",
        "class_config_relationship_id",
        "class_fqn",
        "class_instance_id",
        "class_signature",
        "description",
        "entity_name",
        "function_attribute_type",
        "function_config_attribute_config_id",
        "function_config_id",
        "function_impl_key",
        "function_impl_kind",
        "function_impl_signature",
        "function_membership_semantic_key",
        "function_membership_signature",
        "function_name",
        "function_semantic_key",
        "function_signature",
        "graph_semantic_key",
        "id",
        "identity_mode",
        "is_base",
        "is_edge",
        "kind",
        "name",
        "node_key",
        "node_type",
        "object_id",
        "object_instance_graph_commit_id",
        "object_kind",
        "ontology_subject_kind",
        "operation_family",
        "operation_key",
        "owner_object_id",
        "owner_semantic_key",
        "parent_semantic_key",
        "provider_operation_type",
        "relationship_key",
        "relationship_signature",
        "relationship_type",
        "runtime_delta_fingerprint",
        "semantic_fingerprint",
        "semantic_object_id",
        "semantic_object_instance_graph_commit_id",
        "semantic_object_kind",
        "semantic_subject_type",
        "source",
        "source_class_instance_id",
        "source_object_id",
        "target_class_instance_id",
        "value_mode",
    }
)


@dataclass(frozen=True, slots=True)
class MetaRuntimePackageIndexEntry:
    module_id: str
    package_name: str
    fqn_prefix: str
    manifest_path: Path
    dependency_package_names: tuple[str, ...] = ()
    projection_names: tuple[str, ...] = ()
    runtime_handler_provider_import_root: str | None = None


@dataclass(frozen=True, slots=True)
class MetaRuntimeProjectionIndexEntry:
    projection_name: str
    package_name: str
    fqn_prefix: str
    manifest_path: Path
    projection_hash: str | None = None
    object_config_graph_id: UUID | None = None
    object_config_graph_hash: str | None = None
    object_projection_graph_id: UUID | None = None
    object_projection_graph_identity_id: UUID | None = None
    object_config_graph_identity_id: UUID | None = None
    is_branchable: bool | None = None
    observable_keys: tuple[str, ...] = ()
    source_manifest_hash: str | None = None
    dependency_signature: str | None = None
    semantic_root_object_instance_graph_commit_id: UUID | None = None
    semantic_package_object_instance_graph_commit_id: UUID | None = None
    source_object_instance_graph_commit_id: UUID | None = None
    evidence_source: str = "package_graph_cache"


@dataclass(frozen=True, slots=True)
class MetaRuntimeSemanticObjectIndexEntry:
    semantic_key: str
    object_kind: str
    package_name: str
    fqn_prefix: str
    manifest_path: Path
    object_id: UUID | None = None
    entity_id: str | None = None
    graph_semantic_key: str | None = None
    parent_semantic_key: str | None = None
    owner_semantic_key: str | None = None
    node_key: str | None = None
    attribute_name: str | None = None
    source_refs: tuple[str, ...] = ()
    object_config_graph_id: UUID | None = None
    object_config_graph_hash: str | None = None
    semantic_root_object_instance_graph_commit_id: UUID | None = None
    semantic_package_object_instance_graph_commit_id: UUID | None = None
    semantic_root_head_commit_id: UUID | None = None
    semantic_package_head_commit_id: UUID | None = None
    source_head_commit_id: UUID | None = None
    source_object_instance_graph_commit_id: UUID | None = None
    runtime_delta_fingerprint: str | None = None
    evidence_source: str = "materialization_index_receipt"
    payload: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MetaRuntimePackageProjectionIndex:
    catalog_signature: str
    packages_by_name: Mapping[str, MetaRuntimePackageIndexEntry]
    projections_by_name: Mapping[str, MetaRuntimeProjectionIndexEntry] = field(
        default_factory=dict
    )
    semantic_objects_by_key: Mapping[str, MetaRuntimeSemanticObjectIndexEntry] = field(
        default_factory=dict
    )

    def package_names_for_projection_names(
        self,
        projection_names: Iterable[str],
    ) -> tuple[str, ...]:
        package_names: list[str] = []
        seen: set[str] = set()
        for projection_name in _clean_string_tuple(projection_names):
            projection = self.projections_by_name.get(projection_name)
            if projection is None or projection.package_name in seen:
                continue
            seen.add(projection.package_name)
            package_names.append(projection.package_name)
        return tuple(package_names)

    def missing_projection_names(
        self,
        projection_names: Iterable[str],
    ) -> tuple[str, ...]:
        return tuple(
            projection_name
            for projection_name in _clean_string_tuple(projection_names)
            if projection_name not in self.projections_by_name
        )


@dataclass(frozen=True, slots=True)
class MetaRuntimePackageIndexPatch:
    package_upserts: tuple[MetaRuntimePackageIndexEntry, ...] = ()
    projection_upserts: tuple[MetaRuntimeProjectionIndexEntry, ...] = ()
    projection_deletes: tuple[str, ...] = ()
    semantic_object_upserts: tuple[MetaRuntimeSemanticObjectIndexEntry, ...] = ()
    semantic_object_deletes: tuple[str, ...] = ()
    runtime_delta_fingerprint: str | None = None


@dataclass(frozen=True, slots=True)
class _PackageProjectionIndexReadCache:
    path: Path
    file_witness: tuple[int, int, int, int]
    index: MetaRuntimePackageProjectionIndex


@dataclass(frozen=True, slots=True)
class _PackageProjectionLookupReadCache:
    path: Path
    file_witness: tuple[int, int, int, int]
    index: MetaRuntimePackageProjectionIndex


_package_projection_index_read_cache: _PackageProjectionIndexReadCache | None = None
_package_projection_lookup_read_cache: _PackageProjectionLookupReadCache | None = None


def meta_runtime_package_projection_index_path(*, aware_root: Path) -> Path:
    return (
        aware_root.expanduser().resolve()
        / ".aware"
        / "meta"
        / "runtime"
        / "package_projection_index.v1.json"
    )


def meta_runtime_package_projection_lookup_path(*, aware_root: Path) -> Path:
    return (
        aware_root.expanduser().resolve()
        / ".aware"
        / "meta"
        / "runtime"
        / "package_projection_lookup.v1.json"
    )


def load_meta_runtime_package_projection_index(
    *,
    aware_root: Path,
) -> MetaRuntimePackageProjectionIndex | None:
    return _read_any_package_projection_index(aware_root=aware_root)


def load_meta_runtime_package_projection_lookup(
    *,
    repo_root: Path,
    aware_root: Path,
    package_entries: Iterable[MetaRuntimePackageIndexEntry],
) -> MetaRuntimePackageProjectionIndex | None:
    """Read package/projection ownership without hydrating semantic objects."""

    global _package_projection_lookup_read_cache

    entries = _sorted_package_entries(package_entries)
    catalog_signature = _package_catalog_signature(
        repo_root=repo_root,
        package_entries=entries,
    )
    path = meta_runtime_package_projection_lookup_path(aware_root=aware_root)
    file_witness = _package_projection_index_file_witness(path)
    if file_witness is None:
        return _load_package_projection_lookup_from_full_index(
            aware_root=aware_root,
            catalog_signature=catalog_signature,
        )
    full_cache = _package_projection_index_read_cache
    if (
        full_cache is not None
        and full_cache.path == path
        and full_cache.file_witness == file_witness
        and full_cache.index.catalog_signature == catalog_signature
    ):
        return full_cache.index
    cached = _package_projection_lookup_read_cache
    if (
        cached is not None
        and cached.path == path
        and cached.file_witness == file_witness
        and cached.index.catalog_signature == catalog_signature
    ):
        return cached.index
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, Mapping):
        return None
    if (
        payload.get("schema") != META_RUNTIME_PACKAGE_PROJECTION_LOOKUP_SCHEMA
        or payload.get("version") != META_RUNTIME_PACKAGE_PROJECTION_LOOKUP_VERSION
        or _string_value(payload.get("catalog_signature")) != catalog_signature
    ):
        return _load_package_projection_lookup_from_full_index(
            aware_root=aware_root,
            catalog_signature=catalog_signature,
        )
    packages = _package_entries_from_payload(payload.get("packages"))
    projections = _projection_entries_from_payload(payload.get("projections"))
    if not packages:
        return None
    index = MetaRuntimePackageProjectionIndex(
        catalog_signature=catalog_signature,
        packages_by_name=packages,
        projections_by_name=projections,
    )
    _package_projection_lookup_read_cache = _PackageProjectionLookupReadCache(
        path=path,
        file_witness=file_witness,
        index=index,
    )
    return index


def _load_package_projection_lookup_from_full_index(
    *,
    aware_root: Path,
    catalog_signature: str,
) -> MetaRuntimePackageProjectionIndex | None:
    index = _read_any_package_projection_index(aware_root=aware_root)
    if index is None or index.catalog_signature != catalog_signature:
        return None
    lookup = MetaRuntimePackageProjectionIndex(
        catalog_signature=index.catalog_signature,
        packages_by_name=index.packages_by_name,
        projections_by_name=index.projections_by_name,
    )
    _write_package_projection_lookup(aware_root=aware_root, index=lookup)
    return lookup


def build_meta_runtime_package_projection_index(
    *,
    repo_root: Path,
    aware_root: Path,
    package_entries: Iterable[MetaRuntimePackageIndexEntry],
    required_projection_names: Iterable[str] = (),
) -> MetaRuntimePackageProjectionIndex:
    entries = _sorted_package_entries(package_entries)
    catalog_signature = _package_catalog_signature(
        repo_root=repo_root,
        package_entries=entries,
    )
    required_names = _clean_string_tuple(required_projection_names)
    cached = _read_package_projection_index(
        aware_root=aware_root,
        catalog_signature=catalog_signature,
    )
    if cached is not None and not cached.missing_projection_names(required_names):
        return cached

    previous = _read_any_package_projection_index(aware_root=aware_root)
    index = _build_package_projection_index_from_cached_graphs(
        aware_root=aware_root,
        catalog_signature=catalog_signature,
        package_entries=entries,
    )
    index = _with_external_owner_projection_index_entries(
        aware_root=aware_root,
        index=index,
        package_entries=entries,
        required_projection_names=required_names,
    )
    index = _with_preserved_compatible_index_entries(
        index=index,
        previous_index=previous,
        package_entries=entries,
    )
    index = _with_semantic_contract_projection_catalog_entries(
        index=index,
        package_entries=entries,
    )
    _write_package_projection_index(aware_root=aware_root, index=index)
    return index


def record_full_package_materialization_index(
    *,
    repo_root: Path,
    aware_root: Path,
    materialized_package_name: str,
    package_entries: Iterable[MetaRuntimePackageIndexEntry],
    object_config_graph_payload: Mapping[str, object],
    materialization_index_receipt: Mapping[str, object] | None,
    source_manifest_hash: str | None = None,
    dependency_signature: str | None = None,
    object_config_graph_payload_is_runtime: bool = False,
) -> MetaRuntimePackageProjectionIndex:
    entries = _sorted_package_entries(package_entries)
    package_entry = next(
        (entry for entry in entries if entry.package_name == materialized_package_name),
        None,
    )
    if package_entry is None:
        raise ValueError(
            "Meta runtime package index writer requires the materialized package "
            f"entry: {materialized_package_name!r}"
        )
    existing = _read_any_package_projection_index(aware_root=aware_root)
    if existing is None:
        existing = MetaRuntimePackageProjectionIndex(
            catalog_signature=_package_catalog_signature(
                repo_root=repo_root,
                package_entries=entries,
            ),
            packages_by_name={entry.package_name: entry for entry in entries},
        )

    payload = {
        "cache_kind": "full_materialization_index_receipt",
        "source_manifest_hash": source_manifest_hash,
        "dependency_signature": dependency_signature,
        "object_config_graph": dict(object_config_graph_payload),
        "materialization_index_receipt": (
            None
            if materialization_index_receipt is None
            else dict(materialization_index_receipt)
        ),
    }
    projection_upserts = _projection_entries_from_cache_payload(
        payload=payload,
        package_entry=package_entry,
    )
    semantic_object_upserts = _semantic_object_entries_from_full_materialization(
        payload=payload,
        package_entry=package_entry,
        derive_runtime_graph_from_payload=not object_config_graph_payload_is_runtime,
    )
    projection_names = tuple(
        sorted(
            {
                *package_entry.projection_names,
                *(entry.projection_name for entry in projection_upserts),
            }
        )
    )
    package_upsert = replace(package_entry, projection_names=projection_names)
    index = apply_meta_runtime_package_index_patch(
        index=existing,
        patch=MetaRuntimePackageIndexPatch(
            package_upserts=(package_upsert,),
            projection_deletes=_projection_names_owned_by_package(
                index=existing,
                package_name=materialized_package_name,
            ),
            projection_upserts=projection_upserts,
            semantic_object_upserts=semantic_object_upserts,
        ),
    )
    index = replace(
        index,
        catalog_signature=_package_catalog_signature(
            repo_root=repo_root,
            package_entries=entries,
        ),
    )
    _write_package_projection_index(aware_root=aware_root, index=index)
    return index


def record_meta_runtime_package_index_patch(
    *,
    aware_root: Path,
    patch: MetaRuntimePackageIndexPatch,
) -> MetaRuntimePackageProjectionIndex | None:
    existing = _read_any_package_projection_index(aware_root=aware_root)
    if existing is None:
        return None
    patched = apply_meta_runtime_package_index_patch(
        index=existing,
        patch=patch,
    )
    _write_package_projection_index(aware_root=aware_root, index=patched)
    return patched


def apply_meta_runtime_package_index_patch(
    *,
    index: MetaRuntimePackageProjectionIndex,
    patch: MetaRuntimePackageIndexPatch,
) -> MetaRuntimePackageProjectionIndex:
    packages_by_name = dict(index.packages_by_name)
    projections_by_name = dict(index.projections_by_name)
    semantic_objects_by_key = dict(index.semantic_objects_by_key)

    for package_entry in patch.package_upserts:
        packages_by_name[package_entry.package_name] = package_entry
    for projection_name in patch.projection_deletes:
        projections_by_name.pop(projection_name, None)
    for semantic_key in patch.semantic_object_deletes:
        semantic_objects_by_key.pop(semantic_key, None)
    for projection_entry in patch.projection_upserts:
        _remember_projection_entry(
            projections_by_name=projections_by_name,
            projection_entry=projection_entry,
        )
    for semantic_object_entry in patch.semantic_object_upserts:
        semantic_objects_by_key[semantic_object_entry.semantic_key] = (
            _semantic_object_entry_with_delta_fingerprint(
                entry=semantic_object_entry,
                runtime_delta_fingerprint=patch.runtime_delta_fingerprint,
            )
        )

    return MetaRuntimePackageProjectionIndex(
        catalog_signature=index.catalog_signature,
        packages_by_name=dict(sorted(packages_by_name.items())),
        projections_by_name=dict(sorted(projections_by_name.items())),
        semantic_objects_by_key=dict(sorted(semantic_objects_by_key.items())),
    )


def stable_meta_runtime_package_branch_id(
    *,
    workspace_root: Path,
    aware_toml_path: Path,
    package_name: str,
    fqn_prefix: str,
) -> UUID:
    workspace_root_path = workspace_root.expanduser().resolve()
    manifest_path = aware_toml_path.expanduser().resolve()
    try:
        manifest_key = manifest_path.relative_to(workspace_root_path).as_posix()
    except ValueError:
        manifest_key = manifest_path.as_posix()
    return uuid5(
        NAMESPACE_URL,
        "aware://meta/materialization/object-config-graph-package-branch:v1:"
        f"{manifest_key.strip().casefold()}:"
        f"{(package_name or '').strip().casefold()}:"
        f"{(fqn_prefix or '').strip().casefold()}",
    )


def _build_package_projection_index_from_cached_graphs(
    *,
    aware_root: Path,
    catalog_signature: str,
    package_entries: tuple[MetaRuntimePackageIndexEntry, ...],
) -> MetaRuntimePackageProjectionIndex:
    packages_by_name: dict[str, MetaRuntimePackageIndexEntry] = {
        entry.package_name: entry for entry in package_entries
    }
    projections_by_name: dict[str, MetaRuntimeProjectionIndexEntry] = {}
    semantic_objects_by_key: dict[str, MetaRuntimeSemanticObjectIndexEntry] = {}
    for entry in package_entries:
        payload = _cached_package_graph_payload(aware_root=aware_root, entry=entry)
        if payload is None:
            continue
        projection_entries = _projection_entries_from_cache_payload(
            payload=payload,
            package_entry=entry,
        )
        if projection_entries:
            packages_by_name[entry.package_name] = replace(
                entry,
                projection_names=tuple(
                    sorted({item.projection_name for item in projection_entries})
                ),
            )
        for projection_entry in projection_entries:
            _remember_projection_entry(
                projections_by_name=projections_by_name,
                projection_entry=projection_entry,
            )
        semantic_objects_by_key.update(
            {
                semantic_entry.semantic_key: semantic_entry
                for semantic_entry in _semantic_object_entries_from_full_materialization(
                    payload=payload,
                    package_entry=entry,
                )
            }
        )
    return MetaRuntimePackageProjectionIndex(
        catalog_signature=catalog_signature,
        packages_by_name=packages_by_name,
        projections_by_name=dict(sorted(projections_by_name.items())),
        semantic_objects_by_key=dict(sorted(semantic_objects_by_key.items())),
    )


def _with_external_owner_projection_index_entries(
    *,
    aware_root: Path,
    index: MetaRuntimePackageProjectionIndex,
    package_entries: tuple[MetaRuntimePackageIndexEntry, ...],
    required_projection_names: tuple[str, ...],
) -> MetaRuntimePackageProjectionIndex:
    requested_entries_by_package_name = {
        entry.package_name: entry for entry in package_entries
    }
    owner_indexes = _external_owner_projection_indexes(
        aware_root=aware_root,
        package_entries=package_entries,
    )
    if not owner_indexes:
        return index

    packages_by_name = dict(index.packages_by_name)
    projections_by_name = dict(index.projections_by_name)
    semantic_objects_by_key = dict(index.semantic_objects_by_key)
    required_names = set(required_projection_names)
    for owner_index in owner_indexes:
        allowed_projection_names_by_package: dict[str, set[str]] = {}
        for package_name, owner_package in owner_index.packages_by_name.items():
            requested_entry = requested_entries_by_package_name.get(package_name)
            if requested_entry is None or not _package_index_entries_match(
                requested_entry=requested_entry,
                indexed_entry=owner_package,
            ):
                continue
            allowed_projection_names = _external_owner_projection_names_to_import(
                package_name=package_name,
                owner_index=owner_index,
                projections_by_name=projections_by_name,
                required_projection_names=required_names,
            )
            if not allowed_projection_names:
                continue
            current_entry = packages_by_name.get(package_name, requested_entry)
            packages_by_name[package_name] = replace(
                current_entry,
                projection_names=tuple(
                    sorted(
                        {
                            *current_entry.projection_names,
                            *allowed_projection_names,
                        }
                    )
                ),
            )
            allowed_projection_names_by_package[package_name] = set(
                allowed_projection_names
            )
        if not allowed_projection_names_by_package:
            continue
        for projection_entry in owner_index.projections_by_name.values():
            requested_entry = requested_entries_by_package_name.get(
                projection_entry.package_name,
            )
            allowed_projection_names = allowed_projection_names_by_package.get(
                projection_entry.package_name
            )
            if (
                allowed_projection_names is None
                or projection_entry.projection_name not in allowed_projection_names
                or requested_entry is None
                or not _manifest_paths_match(
                    requested_entry.manifest_path,
                    projection_entry.manifest_path,
                )
            ):
                continue
            existing_projection = projections_by_name.get(
                projection_entry.projection_name
            )
            if existing_projection is not None and _same_package_projection_entry(
                existing=existing_projection,
                projection_entry=projection_entry,
            ):
                continue
            _remember_projection_entry(
                projections_by_name=projections_by_name,
                projection_entry=projection_entry,
            )
        for semantic_object_entry in owner_index.semantic_objects_by_key.values():
            requested_entry = requested_entries_by_package_name.get(
                semantic_object_entry.package_name,
            )
            if (
                semantic_object_entry.package_name
                not in allowed_projection_names_by_package
                or requested_entry is None
                or not _manifest_paths_match(
                    requested_entry.manifest_path,
                    semantic_object_entry.manifest_path,
                )
            ):
                continue
            if (
                _is_provider_delta_overlay_entry(semantic_object_entry)
                or semantic_object_entry.semantic_key not in semantic_objects_by_key
            ):
                semantic_objects_by_key[semantic_object_entry.semantic_key] = (
                    semantic_object_entry
                )

    return MetaRuntimePackageProjectionIndex(
        catalog_signature=index.catalog_signature,
        packages_by_name=dict(sorted(packages_by_name.items())),
        projections_by_name=dict(sorted(projections_by_name.items())),
        semantic_objects_by_key=dict(sorted(semantic_objects_by_key.items())),
    )


def _external_owner_projection_names_to_import(
    *,
    package_name: str,
    owner_index: MetaRuntimePackageProjectionIndex,
    projections_by_name: Mapping[str, MetaRuntimeProjectionIndexEntry],
    required_projection_names: set[str],
) -> tuple[str, ...]:
    owner_projection_names = {
        projection_entry.projection_name
        for projection_entry in owner_index.projections_by_name.values()
        if projection_entry.package_name == package_name
    }
    if not owner_projection_names:
        owner_package = owner_index.packages_by_name.get(package_name)
        owner_projection_names = (
            set(owner_package.projection_names) if owner_package is not None else set()
        )
    if not owner_projection_names:
        return ()
    current_fingerprints = _projection_fingerprints_for_package(
        projections_by_name.values(),
        package_name=package_name,
    )
    if not current_fingerprints:
        return tuple(sorted(owner_projection_names))
    owner_fingerprints = _projection_fingerprints_for_package(
        owner_index.projections_by_name.values(),
        package_name=package_name,
    )
    if owner_fingerprints and current_fingerprints.intersection(owner_fingerprints):
        return tuple(sorted(owner_projection_names))
    return tuple(
        sorted(
            projection_name
            for projection_name in owner_projection_names
            if projection_name in required_projection_names
            and projection_name not in projections_by_name
        )
    )


def _projection_fingerprints_for_package(
    projection_entries: Iterable[MetaRuntimeProjectionIndexEntry],
    *,
    package_name: str,
) -> set[tuple[str, str]]:
    fingerprints: set[tuple[str, str]] = set()
    for projection_entry in projection_entries:
        if projection_entry.package_name != package_name:
            continue
        source_manifest_hash = str(projection_entry.source_manifest_hash or "").strip()
        dependency_signature = str(projection_entry.dependency_signature or "").strip()
        if source_manifest_hash and dependency_signature:
            fingerprints.add((source_manifest_hash, dependency_signature))
    return fingerprints


def _with_preserved_compatible_index_entries(
    *,
    index: MetaRuntimePackageProjectionIndex,
    previous_index: MetaRuntimePackageProjectionIndex | None,
    package_entries: tuple[MetaRuntimePackageIndexEntry, ...],
) -> MetaRuntimePackageProjectionIndex:
    if previous_index is None:
        return index
    requested_entries_by_package_name = {
        entry.package_name: entry for entry in package_entries
    }
    packages_by_name = dict(index.packages_by_name)
    projections_by_name = dict(index.projections_by_name)
    semantic_objects_by_key = dict(index.semantic_objects_by_key)

    for previous_package in previous_index.packages_by_name.values():
        requested_entry = requested_entries_by_package_name.get(
            previous_package.package_name
        )
        if requested_entry is None or not _package_index_entries_match(
            requested_entry=requested_entry,
            indexed_entry=previous_package,
        ):
            continue
        current_package = packages_by_name.get(
            previous_package.package_name,
            requested_entry,
        )
        preservable_projection_names = _preservable_previous_projection_names(
            current_projections_by_name=projections_by_name,
            previous_package=previous_package,
        )
        packages_by_name[previous_package.package_name] = replace(
            current_package,
            projection_names=tuple(
                sorted(
                    {
                        *current_package.projection_names,
                        *preservable_projection_names,
                    }
                )
            ),
        )

    for projection_entry in previous_index.projections_by_name.values():
        requested_entry = requested_entries_by_package_name.get(
            projection_entry.package_name
        )
        if requested_entry is None or not _package_index_entries_match(
            requested_entry=requested_entry,
            indexed_entry=MetaRuntimePackageIndexEntry(
                module_id=requested_entry.module_id,
                package_name=projection_entry.package_name,
                fqn_prefix=projection_entry.fqn_prefix,
                manifest_path=projection_entry.manifest_path,
                runtime_handler_provider_import_root=(
                    requested_entry.runtime_handler_provider_import_root
                ),
            ),
        ):
            continue
        existing_projection = projections_by_name.get(projection_entry.projection_name)
        if existing_projection is not None and _same_package_projection_entry(
            existing=existing_projection,
            projection_entry=projection_entry,
        ):
            current_package = packages_by_name.get(
                projection_entry.package_name,
                requested_entry,
            )
            packages_by_name[projection_entry.package_name] = replace(
                current_package,
                projection_names=tuple(
                    sorted(
                        {
                            *current_package.projection_names,
                            projection_entry.projection_name,
                        }
                    )
                ),
            )
            continue
        if (
            existing_projection is not None
            and existing_projection.package_name != projection_entry.package_name
        ):
            continue
        _remember_projection_entry(
            projections_by_name=projections_by_name,
            projection_entry=projection_entry,
        )
        current_package = packages_by_name.get(
            projection_entry.package_name,
            requested_entry,
        )
        packages_by_name[projection_entry.package_name] = replace(
            current_package,
            projection_names=tuple(
                sorted(
                    {
                        *current_package.projection_names,
                        projection_entry.projection_name,
                    }
                )
            ),
        )

    for semantic_object_entry in previous_index.semantic_objects_by_key.values():
        requested_entry = requested_entries_by_package_name.get(
            semantic_object_entry.package_name
        )
        if (
            requested_entry is None
            or requested_entry.fqn_prefix != semantic_object_entry.fqn_prefix
            or not _manifest_paths_match(
                requested_entry.manifest_path,
                semantic_object_entry.manifest_path,
            )
        ):
            continue
        if (
            _is_provider_delta_overlay_entry(semantic_object_entry)
            or semantic_object_entry.semantic_key not in semantic_objects_by_key
        ):
            semantic_objects_by_key[semantic_object_entry.semantic_key] = (
                semantic_object_entry
            )
    if (
        packages_by_name == dict(index.packages_by_name)
        and projections_by_name == dict(index.projections_by_name)
        and semantic_objects_by_key == dict(index.semantic_objects_by_key)
    ):
        return index
    return MetaRuntimePackageProjectionIndex(
        catalog_signature=index.catalog_signature,
        packages_by_name=dict(sorted(packages_by_name.items())),
        projections_by_name=dict(sorted(projections_by_name.items())),
        semantic_objects_by_key=dict(sorted(semantic_objects_by_key.items())),
    )


def _preservable_previous_projection_names(
    *,
    current_projections_by_name: Mapping[str, MetaRuntimeProjectionIndexEntry],
    previous_package: MetaRuntimePackageIndexEntry,
) -> tuple[str, ...]:
    names: list[str] = []
    for projection_name in previous_package.projection_names:
        current_projection = current_projections_by_name.get(projection_name)
        if (
            current_projection is not None
            and current_projection.package_name != previous_package.package_name
        ):
            continue
        names.append(projection_name)
    return tuple(names)


def _with_semantic_contract_projection_catalog_entries(
    *,
    index: MetaRuntimePackageProjectionIndex,
    package_entries: tuple[MetaRuntimePackageIndexEntry, ...],
) -> MetaRuntimePackageProjectionIndex:
    packages_by_name = dict(index.packages_by_name)
    projections_by_name = dict(index.projections_by_name)

    for package_entry in package_entries:
        projection_names = _clean_string_tuple(package_entry.projection_names)
        if not projection_names:
            continue
        current_package = packages_by_name.get(
            package_entry.package_name,
            package_entry,
        )
        packages_by_name[package_entry.package_name] = replace(
            current_package,
            projection_names=tuple(
                sorted(
                    {
                        *current_package.projection_names,
                        *projection_names,
                    }
                )
            ),
        )
        for projection_name in projection_names:
            _remember_projection_entry(
                projections_by_name=projections_by_name,
                projection_entry=MetaRuntimeProjectionIndexEntry(
                    projection_name=projection_name,
                    package_name=package_entry.package_name,
                    fqn_prefix=package_entry.fqn_prefix,
                    manifest_path=package_entry.manifest_path,
                    evidence_source="semantic_contract_projection_catalog",
                ),
            )

    return MetaRuntimePackageProjectionIndex(
        catalog_signature=index.catalog_signature,
        packages_by_name=dict(sorted(packages_by_name.items())),
        projections_by_name=dict(sorted(projections_by_name.items())),
        semantic_objects_by_key=index.semantic_objects_by_key,
    )


def _is_provider_delta_overlay_entry(
    entry: MetaRuntimeSemanticObjectIndexEntry,
) -> bool:
    return entry.evidence_source == "provider_delta_index_patch"


def _external_owner_projection_indexes(
    *,
    aware_root: Path,
    package_entries: tuple[MetaRuntimePackageIndexEntry, ...],
) -> tuple[MetaRuntimePackageProjectionIndex, ...]:
    resolved_aware_root = aware_root.expanduser().resolve()
    indexes: list[MetaRuntimePackageProjectionIndex] = []
    seen_roots: set[Path] = set()
    for package_entry in package_entries:
        owner_root = _projection_index_owner_root_for_manifest(
            aware_root=resolved_aware_root,
            manifest_path=package_entry.manifest_path,
        )
        if owner_root is None or owner_root in seen_roots:
            continue
        seen_roots.add(owner_root)
        owner_index = _read_any_package_projection_index(aware_root=owner_root)
        if owner_index is not None:
            indexes.append(owner_index)
    return tuple(indexes)


def _projection_index_owner_root_for_manifest(
    *,
    aware_root: Path,
    manifest_path: Path,
) -> Path | None:
    resolved_aware_root = aware_root.expanduser().resolve()
    resolved_manifest_path = manifest_path.expanduser().resolve()
    search_roots = (
        resolved_manifest_path.parent,
        *resolved_manifest_path.parents,
    )
    for candidate_root in search_roots:
        if candidate_root == resolved_aware_root:
            return None
        if meta_runtime_package_projection_index_path(
            aware_root=candidate_root,
        ).is_file():
            return candidate_root
    return None


def _package_index_entries_match(
    *,
    requested_entry: MetaRuntimePackageIndexEntry,
    indexed_entry: MetaRuntimePackageIndexEntry,
) -> bool:
    return (
        requested_entry.package_name == indexed_entry.package_name
        and requested_entry.fqn_prefix == indexed_entry.fqn_prefix
        and _manifest_paths_match(
            requested_entry.manifest_path,
            indexed_entry.manifest_path,
        )
    )


def _manifest_paths_match(left: Path, right: Path) -> bool:
    return left.expanduser().resolve() == right.expanduser().resolve()


def _cached_package_graph_payload(
    *,
    aware_root: Path,
    entry: MetaRuntimePackageIndexEntry,
) -> Mapping[str, object] | None:
    branch_id = stable_meta_runtime_package_branch_id(
        workspace_root=aware_root,
        aware_toml_path=entry.manifest_path,
        package_name=entry.package_name,
        fqn_prefix=entry.fqn_prefix,
    )
    object_config_graph_package_id = stable_object_config_graph_package_id(
        package_name=entry.package_name,
        fqn_prefix=entry.fqn_prefix,
    )
    materialized_payload = read_object_config_graph_package_reuse_cache_payload(
        aware_root=aware_root,
        branch_id=branch_id,
        object_config_graph_package_id=object_config_graph_package_id,
    )
    if (
        materialized_payload is not None
        and _valid_cache_payload(
            materialized_payload,
            cache_kind=OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_MATERIALIZED_PACKAGE,
        )
        and isinstance(
            materialized_payload.get("materialization_index_receipt"),
            Mapping,
        )
    ):
        return materialized_payload
    context_payload = read_object_config_graph_package_context_reuse_cache_payload(
        aware_root=aware_root,
        branch_id=branch_id,
        object_config_graph_package_id=object_config_graph_package_id,
    )
    if _valid_cache_payload(
        context_payload,
        cache_kind=OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS,
    ):
        return context_payload
    if materialized_payload is not None and _valid_cache_payload(
        materialized_payload,
        cache_kind=OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_MATERIALIZED_PACKAGE,
    ):
        return materialized_payload
    return None


def _valid_cache_payload(
    payload: Mapping[str, object] | None,
    *,
    cache_kind: str,
) -> bool:
    if payload is None:
        return False
    valid = (
        payload.get("v") == OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_VERSION
        and payload.get("cache_kind") == cache_kind
    )
    if not valid:
        return False
    if cache_kind == OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS:
        return (
            payload.get("runtime_graph_derivation_signature")
            == OBJECT_CONFIG_GRAPH_PACKAGE_CONTEXT_GRAPHS_DERIVATION_SIGNATURE
        )
    return True


def _projection_entries_from_cache_payload(
    *,
    payload: Mapping[str, object],
    package_entry: MetaRuntimePackageIndexEntry,
) -> tuple[MetaRuntimeProjectionIndexEntry, ...]:
    entries_by_name: dict[str, MetaRuntimeProjectionIndexEntry] = {}
    graph_entries = _projection_entries_from_graph_payload(
        payload=payload,
        package_entry=package_entry,
    )
    receipt_entries = _projection_entries_from_materialization_receipt(
        payload=payload,
        package_entry=package_entry,
    )
    receipt_projection_names = {
        projection_entry.projection_name for projection_entry in receipt_entries
    }
    for projection_entry in graph_entries:
        if projection_entry.projection_name in receipt_projection_names:
            continue
        _remember_projection_entry(
            projections_by_name=entries_by_name,
            projection_entry=projection_entry,
        )
    for projection_entry in receipt_entries:
        _remember_projection_entry(
            projections_by_name=entries_by_name,
            projection_entry=projection_entry,
        )
    return tuple(entries_by_name.values())


def _projection_entries_from_graph_payload(
    *,
    payload: Mapping[str, object],
    package_entry: MetaRuntimePackageIndexEntry,
) -> tuple[MetaRuntimeProjectionIndexEntry, ...]:
    graph_payload, graph_hash = _graph_payload_for_projection_index(payload)
    if graph_payload is None:
        return ()
    raw_projections = graph_payload.get("object_projection_graphs")
    if not isinstance(raw_projections, list):
        return ()
    object_config_graph_id = _uuid_value(
        graph_payload.get("id") or payload.get("object_config_graph_id")
    )
    entries: list[MetaRuntimeProjectionIndexEntry] = []
    for raw_projection in raw_projections:
        if not isinstance(raw_projection, Mapping):
            continue
        projection_name = _string_value(raw_projection.get("name"))
        if projection_name is None:
            continue
        entries.append(
            MetaRuntimeProjectionIndexEntry(
                projection_name=projection_name,
                package_name=package_entry.package_name,
                fqn_prefix=package_entry.fqn_prefix,
                manifest_path=package_entry.manifest_path,
                projection_hash=_string_value(raw_projection.get("projection_hash")),
                object_config_graph_id=object_config_graph_id,
                object_config_graph_hash=graph_hash,
                object_projection_graph_id=_uuid_value(raw_projection.get("id")),
                source_manifest_hash=_string_value(payload.get("source_manifest_hash")),
                dependency_signature=_string_value(payload.get("dependency_signature")),
                semantic_root_object_instance_graph_commit_id=_uuid_value(
                    payload.get("object_config_graph_object_instance_graph_commit_id")
                ),
                semantic_package_object_instance_graph_commit_id=_uuid_value(
                    payload.get(
                        "object_config_graph_package_object_instance_graph_commit_id"
                    )
                ),
                source_object_instance_graph_commit_id=_uuid_value(
                    payload.get("code_package_object_instance_graph_commit_id")
                ),
                evidence_source=str(payload.get("cache_kind") or "package_graph_cache"),
            )
        )
    return tuple(entries)


def _projection_entries_from_materialization_receipt(
    *,
    payload: Mapping[str, object],
    package_entry: MetaRuntimePackageIndexEntry,
) -> tuple[MetaRuntimeProjectionIndexEntry, ...]:
    receipt = payload.get("materialization_index_receipt")
    if not isinstance(receipt, Mapping):
        return ()
    identity_plane = receipt.get("identity_plane")
    if not isinstance(identity_plane, Mapping):
        return ()
    projection_identities = identity_plane.get("projection_identities")
    if not isinstance(projection_identities, list):
        return ()
    semantic = receipt.get("semantic")
    semantic_payload = semantic if isinstance(semantic, Mapping) else {}
    cache_key = receipt.get("cache_key")
    cache_payload = cache_key if isinstance(cache_key, Mapping) else {}
    entries: list[MetaRuntimeProjectionIndexEntry] = []
    for raw_identity in projection_identities:
        if not isinstance(raw_identity, Mapping):
            continue
        projection_name = _string_value(raw_identity.get("projection_name"))
        if projection_name is None:
            continue
        entries.append(
            MetaRuntimeProjectionIndexEntry(
                projection_name=projection_name,
                package_name=package_entry.package_name,
                fqn_prefix=package_entry.fqn_prefix,
                manifest_path=package_entry.manifest_path,
                projection_hash=_string_value(raw_identity.get("projection_hash")),
                object_config_graph_id=_uuid_value(
                    semantic_payload.get("object_config_graph_id")
                ),
                object_config_graph_hash=_string_value(
                    semantic_payload.get("object_config_graph_hash")
                    or cache_payload.get("object_config_graph_hash")
                ),
                object_projection_graph_id=_uuid_value(
                    raw_identity.get("object_projection_graph_id")
                ),
                object_projection_graph_identity_id=_uuid_value(
                    raw_identity.get("object_projection_graph_identity_id")
                ),
                object_config_graph_identity_id=_uuid_value(
                    raw_identity.get("object_config_graph_identity_id")
                    or identity_plane.get("object_config_graph_identity_id")
                ),
                is_branchable=_bool_value(raw_identity.get("is_branchable")),
                observable_keys=_clean_string_tuple(
                    raw_identity.get("observable_keys")
                ),
                source_manifest_hash=_string_value(
                    cache_payload.get("source_manifest_hash")
                    or payload.get("source_manifest_hash")
                ),
                dependency_signature=_string_value(
                    cache_payload.get("dependency_signature")
                    or payload.get("dependency_signature")
                ),
                semantic_root_object_instance_graph_commit_id=_uuid_value(
                    semantic_payload.get(
                        "object_config_graph_object_instance_graph_commit_id"
                    )
                    or payload.get(
                        "object_config_graph_object_instance_graph_commit_id"
                    )
                ),
                semantic_package_object_instance_graph_commit_id=_uuid_value(
                    semantic_payload.get(
                        "object_config_graph_package_object_instance_graph_commit_id"
                    )
                    or payload.get(
                        "object_config_graph_package_object_instance_graph_commit_id"
                    )
                ),
                source_object_instance_graph_commit_id=_uuid_value(
                    payload.get("code_package_object_instance_graph_commit_id")
                ),
                evidence_source="materialization_index_receipt",
            )
        )
    return tuple(entries)


def _semantic_object_entries_from_full_materialization(
    *,
    payload: Mapping[str, object],
    package_entry: MetaRuntimePackageIndexEntry,
    derive_runtime_graph_from_payload: bool = True,
) -> tuple[MetaRuntimeSemanticObjectIndexEntry, ...]:
    graph_payload, graph_hash = _graph_payload_for_projection_index(payload)
    if graph_payload is None:
        return ()
    fqn_prefix = (
        _string_value(graph_payload.get("fqn_prefix")) or package_entry.fqn_prefix
    )
    object_config_graph_id = _uuid_value(
        graph_payload.get("id") or payload.get("object_config_graph_id")
    )
    source_refs = _source_refs_from_materialization_payload(
        payload=payload,
        package_entry=package_entry,
    )
    semantic_root_commit_id = _semantic_root_commit_id(payload=payload)
    semantic_package_commit_id = _semantic_package_commit_id(payload=payload)
    semantic_root_head_commit_id = _semantic_root_head_commit_id(payload=payload)
    semantic_package_head_commit_id = _semantic_package_head_commit_id(payload=payload)
    source_head_commit_id = _source_head_commit_id(payload=payload)
    source_commit_id = _source_commit_id(payload=payload)
    semantic_package_object_id = _semantic_package_object_id(payload=payload)
    from aware_meta.materialization.runtime_delta import (  # noqa: WPS433
        build_meta_ocg_runtime_semantic_object_index_from_payload,
    )

    runtime_index = build_meta_ocg_runtime_semantic_object_index_from_payload(
        package_name=package_entry.package_name,
        object_config_graph_payload=graph_payload,
        source_paths=source_refs,
        derive_runtime_graph_from_payload=derive_runtime_graph_from_payload,
    )
    entries = tuple(
        _semantic_object_entry_from_runtime_delta_index_payload(
            raw_entry=raw_entry,
            package_entry=package_entry,
            fqn_prefix=fqn_prefix,
            object_config_graph_id=object_config_graph_id,
            object_config_graph_hash=graph_hash,
            semantic_root_commit_id=semantic_root_commit_id,
            semantic_package_commit_id=semantic_package_commit_id,
            semantic_root_head_commit_id=semantic_root_head_commit_id,
            semantic_package_head_commit_id=semantic_package_head_commit_id,
            source_head_commit_id=source_head_commit_id,
            source_commit_id=source_commit_id,
            semantic_package_object_id=semantic_package_object_id,
        )
        for _semantic_key, raw_entry in sorted(runtime_index.items())
    )
    return tuple(
        sorted(
            entries,
            key=lambda item: (item.semantic_key, item.package_name),
        )
    )


def _semantic_object_entry_from_runtime_delta_index_payload(
    *,
    raw_entry: Mapping[str, object],
    package_entry: MetaRuntimePackageIndexEntry,
    fqn_prefix: str,
    object_config_graph_id: UUID | None,
    object_config_graph_hash: str | None,
    semantic_root_commit_id: UUID | None,
    semantic_package_commit_id: UUID | None,
    semantic_root_head_commit_id: UUID | None,
    semantic_package_head_commit_id: UUID | None,
    source_head_commit_id: UUID | None,
    source_commit_id: UUID | None,
    semantic_package_object_id: UUID | None,
) -> MetaRuntimeSemanticObjectIndexEntry:
    semantic_key = _string_value(raw_entry.get("semantic_key"))
    object_kind = _string_value(
        raw_entry.get("object_kind")
        or raw_entry.get("ontology_subject_kind")
        or raw_entry.get("kind")
    )
    if semantic_key is None or object_kind is None:
        raise ValueError("Meta runtime semantic object index entry missing identity.")
    object_id = _runtime_delta_entry_object_id(
        raw_entry=raw_entry,
        object_kind=object_kind,
        object_config_graph_id=object_config_graph_id,
        semantic_package_object_id=semantic_package_object_id,
    )
    return MetaRuntimeSemanticObjectIndexEntry(
        semantic_key=semantic_key,
        object_kind=object_kind,
        package_name=package_entry.package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=package_entry.manifest_path,
        object_id=object_id,
        entity_id=_string_value(raw_entry.get("entity_id")),
        graph_semantic_key=_string_value(raw_entry.get("graph_semantic_key")),
        parent_semantic_key=_string_value(raw_entry.get("parent_semantic_key")),
        owner_semantic_key=_string_value(raw_entry.get("owner_semantic_key")),
        node_key=_string_value(raw_entry.get("node_key")),
        attribute_name=_string_value(raw_entry.get("attribute_name")),
        source_refs=_clean_string_tuple(raw_entry.get("source_refs")),
        object_config_graph_id=object_config_graph_id,
        object_config_graph_hash=(
            _string_value(raw_entry.get("hash")) or object_config_graph_hash
        ),
        semantic_root_object_instance_graph_commit_id=semantic_root_commit_id,
        semantic_package_object_instance_graph_commit_id=semantic_package_commit_id,
        semantic_root_head_commit_id=semantic_root_head_commit_id,
        semantic_package_head_commit_id=semantic_package_head_commit_id,
        source_head_commit_id=source_head_commit_id,
        source_object_instance_graph_commit_id=source_commit_id,
        runtime_delta_fingerprint=_string_value(
            raw_entry.get("semantic_fingerprint")
            or raw_entry.get("runtime_delta_fingerprint")
        ),
        evidence_source="full_materialization_runtime_delta_index",
        payload=dict(raw_entry),
    )


def _runtime_delta_entry_object_id(
    *,
    raw_entry: Mapping[str, object],
    object_kind: str,
    object_config_graph_id: UUID | None,
    semantic_package_object_id: UUID | None,
) -> UUID | None:
    if object_kind == "object_config_graph_package":
        return semantic_package_object_id
    if object_kind == "object_config_graph":
        return object_config_graph_id
    for value in (
        raw_entry.get("object_id"),
        raw_entry.get("node_id"),
        raw_entry.get("attribute_config_id"),
        raw_entry.get("entity_id"),
    ):
        object_id = _uuid_value(value)
        if object_id is not None:
            return object_id
    return None


def _graph_payload_for_projection_index(
    payload: Mapping[str, object],
) -> tuple[Mapping[str, object] | None, str | None]:
    for payload_key, hash_key in (
        ("runtime_object_config_graph", "runtime_object_config_graph_hash"),
        ("object_config_graph", "object_config_graph_hash"),
        ("source_object_config_graph", "source_object_config_graph_hash"),
    ):
        graph_payload = payload.get(payload_key)
        if isinstance(graph_payload, Mapping):
            return graph_payload, _string_value(payload.get(hash_key))
    return None, None


def _read_package_projection_index(
    *,
    aware_root: Path,
    catalog_signature: str,
) -> MetaRuntimePackageProjectionIndex | None:
    index = _read_any_package_projection_index(aware_root=aware_root)
    if index is None or index.catalog_signature != catalog_signature:
        return None
    return index


def _read_any_package_projection_index(
    *,
    aware_root: Path,
) -> MetaRuntimePackageProjectionIndex | None:
    global _package_projection_index_read_cache

    path = meta_runtime_package_projection_index_path(aware_root=aware_root)
    file_witness = _package_projection_index_file_witness(path)
    if file_witness is None:
        return None
    cached = _package_projection_index_read_cache
    if (
        cached is not None
        and cached.path == path
        and cached.file_witness == file_witness
    ):
        return cached.index
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, Mapping):
        return None
    if payload.get("schema") != META_RUNTIME_PACKAGE_PROJECTION_INDEX_SCHEMA:
        return None
    if payload.get("version") != META_RUNTIME_PACKAGE_PROJECTION_INDEX_VERSION:
        return None
    catalog_signature = _string_value(payload.get("catalog_signature"))
    if catalog_signature is None:
        return None
    packages = _package_entries_from_payload(payload.get("packages"))
    if not packages:
        return None
    source_ref_sets_by_key = _source_ref_sets_from_payload(
        payload.get("source_ref_sets")
    )
    index = MetaRuntimePackageProjectionIndex(
        catalog_signature=catalog_signature,
        packages_by_name=packages,
        projections_by_name=_projection_entries_from_payload(
            payload.get("projections")
        ),
        semantic_objects_by_key=_semantic_object_entries_from_payload(
            payload.get("semantic_objects"),
            source_ref_sets_by_key=source_ref_sets_by_key,
        ),
    )
    _package_projection_index_read_cache = _PackageProjectionIndexReadCache(
        path=path,
        file_witness=file_witness,
        index=index,
    )
    return index


def _write_package_projection_index(
    *,
    aware_root: Path,
    index: MetaRuntimePackageProjectionIndex,
) -> None:
    global _package_projection_index_read_cache

    path = meta_runtime_package_projection_index_path(aware_root=aware_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    cached = _package_projection_index_read_cache
    current_file_witness = _package_projection_index_file_witness(path)
    if (
        cached is not None
        and cached.path == path
        and cached.file_witness == current_file_witness
        and (cached.index is index or cached.index == index)
    ):
        _write_package_projection_lookup(aware_root=aware_root, index=index)
        return
    semantic_object_entries = tuple(
        sorted(
            index.semantic_objects_by_key.values(),
            key=lambda item: (item.semantic_key, item.package_name),
        )
    )
    source_ref_set_keys_by_refs = _source_ref_set_keys_by_refs(semantic_object_entries)
    payload = {
        "schema": META_RUNTIME_PACKAGE_PROJECTION_INDEX_SCHEMA,
        "version": META_RUNTIME_PACKAGE_PROJECTION_INDEX_VERSION,
        "semantic_object_payload_storage": (
            META_RUNTIME_SEMANTIC_OBJECT_PAYLOAD_STORAGE
        ),
        "semantic_object_source_ref_storage": (
            META_RUNTIME_SEMANTIC_OBJECT_SOURCE_REF_STORAGE
        ),
        "catalog_signature": index.catalog_signature,
        "packages": [
            _package_entry_payload(entry)
            for entry in _sorted_package_entries(index.packages_by_name.values())
        ],
        "projections": [
            _projection_entry_payload(entry)
            for entry in sorted(
                index.projections_by_name.values(),
                key=lambda item: (item.projection_name, item.package_name),
            )
        ],
        "source_ref_sets": _source_ref_set_payloads(source_ref_set_keys_by_refs),
        "semantic_objects": [
            _semantic_object_entry_payload(
                entry,
                source_ref_set_keys_by_refs=source_ref_set_keys_by_refs,
            )
            for entry in semantic_object_entries
        ],
    }
    tmp_path = path.with_name(f"{path.name}.{uuid4().hex}.tmp")
    try:
        tmp_path.write_text(
            json.dumps(payload, separators=(",", ":"), sort_keys=True),
            encoding="utf-8",
        )
        tmp_path.replace(path)
        file_witness = _package_projection_index_file_witness(path)
        if file_witness is not None:
            _package_projection_index_read_cache = _PackageProjectionIndexReadCache(
                path=path,
                file_witness=file_witness,
                index=index,
            )
        _write_package_projection_lookup(aware_root=aware_root, index=index)
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass


def _write_package_projection_lookup(
    *,
    aware_root: Path,
    index: MetaRuntimePackageProjectionIndex,
) -> None:
    global _package_projection_lookup_read_cache

    path = meta_runtime_package_projection_lookup_path(aware_root=aware_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    lookup = MetaRuntimePackageProjectionIndex(
        catalog_signature=index.catalog_signature,
        packages_by_name=index.packages_by_name,
        projections_by_name=index.projections_by_name,
    )
    cached = _package_projection_lookup_read_cache
    current_file_witness = _package_projection_index_file_witness(path)
    if (
        cached is not None
        and cached.path == path
        and cached.file_witness == current_file_witness
        and (cached.index is lookup or cached.index == lookup)
    ):
        return
    payload = {
        "schema": META_RUNTIME_PACKAGE_PROJECTION_LOOKUP_SCHEMA,
        "version": META_RUNTIME_PACKAGE_PROJECTION_LOOKUP_VERSION,
        "catalog_signature": lookup.catalog_signature,
        "packages": [
            _package_entry_payload(entry)
            for entry in _sorted_package_entries(lookup.packages_by_name.values())
        ],
        "projections": [
            _projection_entry_payload(entry)
            for entry in sorted(
                lookup.projections_by_name.values(),
                key=lambda item: (item.projection_name, item.package_name),
            )
        ],
    }
    tmp_path = path.with_name(f"{path.name}.{uuid4().hex}.tmp")
    try:
        tmp_path.write_text(
            json.dumps(payload, separators=(",", ":"), sort_keys=True),
            encoding="utf-8",
        )
        tmp_path.replace(path)
        file_witness = _package_projection_index_file_witness(path)
        if file_witness is not None:
            _package_projection_lookup_read_cache = _PackageProjectionLookupReadCache(
                path=path,
                file_witness=file_witness,
                index=lookup,
            )
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass


def _package_projection_index_file_witness(
    path: Path,
) -> tuple[int, int, int, int] | None:
    try:
        stat = path.stat()
    except FileNotFoundError:
        return None
    if not path.is_file():
        return None
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)


def _projection_names_owned_by_package(
    *,
    index: MetaRuntimePackageProjectionIndex,
    package_name: str,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            projection_name
            for projection_name, projection_entry in index.projections_by_name.items()
            if projection_entry.package_name == package_name
        )
    )


def _package_entries_from_payload(
    value: object,
) -> dict[str, MetaRuntimePackageIndexEntry]:
    if not isinstance(value, list):
        return {}
    entries: dict[str, MetaRuntimePackageIndexEntry] = {}
    for raw_entry in value:
        if not isinstance(raw_entry, Mapping):
            continue
        package_name = _string_value(raw_entry.get("package_name"))
        module_id = _string_value(raw_entry.get("module_id"))
        fqn_prefix = _string_value(raw_entry.get("fqn_prefix"))
        manifest_path = _path_value(raw_entry.get("manifest_path"))
        if (
            package_name is None
            or module_id is None
            or fqn_prefix is None
            or manifest_path is None
        ):
            continue
        entries[package_name] = MetaRuntimePackageIndexEntry(
            module_id=module_id,
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            manifest_path=manifest_path,
            dependency_package_names=_clean_string_tuple(
                raw_entry.get("dependency_package_names")
            ),
            projection_names=_clean_string_tuple(raw_entry.get("projection_names")),
            runtime_handler_provider_import_root=_string_value(
                raw_entry.get("runtime_handler_provider_import_root")
            ),
        )
    return dict(sorted(entries.items()))


def _projection_entries_from_payload(
    value: object,
) -> dict[str, MetaRuntimeProjectionIndexEntry]:
    if not isinstance(value, list):
        return {}
    entries: dict[str, MetaRuntimeProjectionIndexEntry] = {}
    for raw_entry in value:
        if not isinstance(raw_entry, Mapping):
            continue
        projection_name = _string_value(raw_entry.get("projection_name"))
        package_name = _string_value(raw_entry.get("package_name"))
        fqn_prefix = _string_value(raw_entry.get("fqn_prefix"))
        manifest_path = _path_value(raw_entry.get("manifest_path"))
        if (
            projection_name is None
            or package_name is None
            or fqn_prefix is None
            or manifest_path is None
        ):
            continue
        entries[projection_name] = MetaRuntimeProjectionIndexEntry(
            projection_name=projection_name,
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            manifest_path=manifest_path,
            projection_hash=_string_value(raw_entry.get("projection_hash")),
            object_config_graph_id=_uuid_value(raw_entry.get("object_config_graph_id")),
            object_config_graph_hash=_string_value(
                raw_entry.get("object_config_graph_hash")
            ),
            object_projection_graph_id=_uuid_value(
                raw_entry.get("object_projection_graph_id")
            ),
            object_projection_graph_identity_id=_uuid_value(
                raw_entry.get("object_projection_graph_identity_id")
            ),
            object_config_graph_identity_id=_uuid_value(
                raw_entry.get("object_config_graph_identity_id")
            ),
            is_branchable=_bool_value(raw_entry.get("is_branchable")),
            observable_keys=_clean_string_tuple(raw_entry.get("observable_keys")),
            source_manifest_hash=_string_value(raw_entry.get("source_manifest_hash")),
            dependency_signature=_string_value(raw_entry.get("dependency_signature")),
            semantic_root_object_instance_graph_commit_id=_uuid_value(
                raw_entry.get("semantic_root_object_instance_graph_commit_id")
            ),
            semantic_package_object_instance_graph_commit_id=_uuid_value(
                raw_entry.get("semantic_package_object_instance_graph_commit_id")
            ),
            source_object_instance_graph_commit_id=_uuid_value(
                raw_entry.get("source_object_instance_graph_commit_id")
            ),
            evidence_source=_string_value(raw_entry.get("evidence_source"))
            or "package_projection_index",
        )
    return dict(sorted(entries.items()))


def _source_ref_sets_from_payload(
    value: object,
) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, list):
        return {}
    entries: dict[str, tuple[str, ...]] = {}
    for raw_entry in value:
        if not isinstance(raw_entry, Mapping):
            continue
        source_ref_set_key = _string_value(raw_entry.get("source_ref_set_key"))
        if source_ref_set_key is None:
            continue
        entries[source_ref_set_key] = _clean_string_tuple(raw_entry.get("source_refs"))
    return dict(sorted(entries.items()))


def _semantic_object_entries_from_payload(
    value: object,
    *,
    source_ref_sets_by_key: Mapping[str, tuple[str, ...]] | None = None,
) -> dict[str, MetaRuntimeSemanticObjectIndexEntry]:
    if not isinstance(value, list):
        return {}
    entries: dict[str, MetaRuntimeSemanticObjectIndexEntry] = {}
    for raw_entry in value:
        if not isinstance(raw_entry, Mapping):
            continue
        semantic_key = _string_value(raw_entry.get("semantic_key"))
        object_kind = _string_value(raw_entry.get("object_kind"))
        package_name = _string_value(raw_entry.get("package_name"))
        fqn_prefix = _string_value(raw_entry.get("fqn_prefix"))
        manifest_path = _path_value(raw_entry.get("manifest_path"))
        if (
            semantic_key is None
            or object_kind is None
            or package_name is None
            or fqn_prefix is None
            or manifest_path is None
        ):
            continue
        payload = raw_entry.get("payload")
        source_ref_set_key = _string_value(raw_entry.get("source_ref_set_key"))
        entries[semantic_key] = MetaRuntimeSemanticObjectIndexEntry(
            semantic_key=semantic_key,
            object_kind=object_kind,
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            manifest_path=manifest_path,
            object_id=_uuid_value(raw_entry.get("object_id")),
            entity_id=_string_value(raw_entry.get("entity_id")),
            graph_semantic_key=_string_value(raw_entry.get("graph_semantic_key")),
            parent_semantic_key=_string_value(raw_entry.get("parent_semantic_key")),
            owner_semantic_key=_string_value(raw_entry.get("owner_semantic_key")),
            node_key=_string_value(raw_entry.get("node_key")),
            attribute_name=_string_value(raw_entry.get("attribute_name")),
            source_refs=(
                (source_ref_sets_by_key or {}).get(source_ref_set_key, ())
                if source_ref_set_key is not None
                else _clean_string_tuple(raw_entry.get("source_refs"))
            ),
            object_config_graph_id=_uuid_value(raw_entry.get("object_config_graph_id")),
            object_config_graph_hash=_string_value(
                raw_entry.get("object_config_graph_hash")
            ),
            semantic_root_object_instance_graph_commit_id=_uuid_value(
                raw_entry.get("semantic_root_object_instance_graph_commit_id")
            ),
            semantic_package_object_instance_graph_commit_id=_uuid_value(
                raw_entry.get("semantic_package_object_instance_graph_commit_id")
            ),
            semantic_root_head_commit_id=_uuid_value(
                raw_entry.get("semantic_root_head_commit_id")
            ),
            semantic_package_head_commit_id=_uuid_value(
                raw_entry.get("semantic_package_head_commit_id")
            ),
            source_head_commit_id=_uuid_value(raw_entry.get("source_head_commit_id")),
            source_object_instance_graph_commit_id=_uuid_value(
                raw_entry.get("source_object_instance_graph_commit_id")
            ),
            runtime_delta_fingerprint=_string_value(
                raw_entry.get("runtime_delta_fingerprint")
            ),
            evidence_source=_string_value(raw_entry.get("evidence_source"))
            or "package_projection_index",
            payload=payload if isinstance(payload, Mapping) else {},
        )
    return dict(sorted(entries.items()))


def _package_entry_payload(entry: MetaRuntimePackageIndexEntry) -> dict[str, object]:
    payload: dict[str, object] = {
        "module_id": entry.module_id,
        "package_name": entry.package_name,
        "fqn_prefix": entry.fqn_prefix,
        "manifest_path": entry.manifest_path.as_posix(),
        "dependency_package_names": list(entry.dependency_package_names),
        "projection_names": list(entry.projection_names),
    }
    if entry.runtime_handler_provider_import_root:
        payload["runtime_handler_provider_import_root"] = (
            entry.runtime_handler_provider_import_root
        )
    return payload


def _projection_entry_payload(
    entry: MetaRuntimeProjectionIndexEntry,
) -> dict[str, object]:
    return {
        "projection_name": entry.projection_name,
        "package_name": entry.package_name,
        "fqn_prefix": entry.fqn_prefix,
        "manifest_path": entry.manifest_path.as_posix(),
        "projection_hash": entry.projection_hash,
        "object_config_graph_id": _uuid_text(entry.object_config_graph_id),
        "object_config_graph_hash": entry.object_config_graph_hash,
        "object_projection_graph_id": _uuid_text(entry.object_projection_graph_id),
        "object_projection_graph_identity_id": _uuid_text(
            entry.object_projection_graph_identity_id
        ),
        "object_config_graph_identity_id": _uuid_text(
            entry.object_config_graph_identity_id
        ),
        "is_branchable": entry.is_branchable,
        "observable_keys": list(entry.observable_keys),
        "source_manifest_hash": entry.source_manifest_hash,
        "dependency_signature": entry.dependency_signature,
        "semantic_root_object_instance_graph_commit_id": _uuid_text(
            entry.semantic_root_object_instance_graph_commit_id
        ),
        "semantic_package_object_instance_graph_commit_id": _uuid_text(
            entry.semantic_package_object_instance_graph_commit_id
        ),
        "source_object_instance_graph_commit_id": _uuid_text(
            entry.source_object_instance_graph_commit_id
        ),
        "evidence_source": entry.evidence_source,
    }


def _semantic_object_entry_payload(
    entry: MetaRuntimeSemanticObjectIndexEntry,
    *,
    source_ref_set_keys_by_refs: Mapping[tuple[str, ...], str] | None = None,
) -> dict[str, object]:
    source_ref_set_key = (source_ref_set_keys_by_refs or {}).get(entry.source_refs)
    payload = {
        "semantic_key": entry.semantic_key,
        "object_kind": entry.object_kind,
        "package_name": entry.package_name,
        "fqn_prefix": entry.fqn_prefix,
        "manifest_path": entry.manifest_path.as_posix(),
        "object_id": _uuid_text(entry.object_id),
        "entity_id": entry.entity_id,
        "graph_semantic_key": entry.graph_semantic_key,
        "parent_semantic_key": entry.parent_semantic_key,
        "owner_semantic_key": entry.owner_semantic_key,
        "node_key": entry.node_key,
        "attribute_name": entry.attribute_name,
        "object_config_graph_id": _uuid_text(entry.object_config_graph_id),
        "object_config_graph_hash": entry.object_config_graph_hash,
        "semantic_root_object_instance_graph_commit_id": _uuid_text(
            entry.semantic_root_object_instance_graph_commit_id
        ),
        "semantic_package_object_instance_graph_commit_id": _uuid_text(
            entry.semantic_package_object_instance_graph_commit_id
        ),
        "semantic_root_head_commit_id": _uuid_text(entry.semantic_root_head_commit_id),
        "semantic_package_head_commit_id": _uuid_text(
            entry.semantic_package_head_commit_id
        ),
        "source_head_commit_id": _uuid_text(entry.source_head_commit_id),
        "source_object_instance_graph_commit_id": _uuid_text(
            entry.source_object_instance_graph_commit_id
        ),
        "runtime_delta_fingerprint": entry.runtime_delta_fingerprint,
        "evidence_source": entry.evidence_source,
    }
    if source_ref_set_key is not None:
        payload["source_ref_set_key"] = source_ref_set_key
    elif entry.source_refs:
        payload["source_refs"] = list(entry.source_refs)
    compact_payload = _compact_semantic_object_payload(entry.payload)
    if compact_payload:
        payload["payload"] = compact_payload
    return payload


def _source_ref_set_keys_by_refs(
    entries: Iterable[MetaRuntimeSemanticObjectIndexEntry],
) -> dict[tuple[str, ...], str]:
    return {
        source_refs: _source_ref_set_key(source_refs)
        for source_refs in sorted(
            {entry.source_refs for entry in entries if entry.source_refs}
        )
    }


def _source_ref_set_key(source_refs: tuple[str, ...]) -> str:
    payload = json.dumps(list(source_refs), separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _source_ref_set_payloads(
    source_ref_set_keys_by_refs: Mapping[tuple[str, ...], str],
) -> list[dict[str, object]]:
    return [
        {
            "source_ref_set_key": source_ref_set_key,
            "source_refs": list(source_refs),
        }
        for source_refs, source_ref_set_key in sorted(
            source_ref_set_keys_by_refs.items(),
            key=lambda item: item[1],
        )
    ]


def _compact_semantic_object_payload(
    value: Mapping[str, object],
) -> dict[str, object]:
    return {
        key: _json_payload_value(raw_value)
        for key in sorted(_SEMANTIC_OBJECT_COMPACT_PAYLOAD_KEYS)
        if (raw_value := value.get(key)) is not None
    }


def _semantic_object_entry_with_delta_fingerprint(
    *,
    entry: MetaRuntimeSemanticObjectIndexEntry,
    runtime_delta_fingerprint: str | None,
) -> MetaRuntimeSemanticObjectIndexEntry:
    if runtime_delta_fingerprint is None:
        return entry
    return replace(entry, runtime_delta_fingerprint=runtime_delta_fingerprint)


def _source_refs_from_materialization_payload(
    *,
    payload: Mapping[str, object],
    package_entry: MetaRuntimePackageIndexEntry,
) -> tuple[str, ...]:
    receipt = payload.get("materialization_index_receipt")
    receipt_payload = receipt if isinstance(receipt, Mapping) else {}
    source = receipt_payload.get("source")
    source_payload = source if isinstance(source, Mapping) else {}
    owned_file_paths = _clean_string_tuple(source_payload.get("owned_file_paths"))
    if not owned_file_paths:
        return ()
    return tuple(
        dict.fromkeys(
            _source_ref_from_owned_file_path(
                owned_file_path=owned_file_path,
                package_entry=package_entry,
            )
            for owned_file_path in owned_file_paths
        )
    )


def _source_ref_from_owned_file_path(
    *,
    owned_file_path: str,
    package_entry: MetaRuntimePackageIndexEntry,
) -> str:
    normalized = owned_file_path.strip().strip("/")
    source_root = (package_entry.manifest_path.parent / "aware").as_posix().strip("/")
    source_prefix = f"{source_root}/"
    if normalized.startswith(source_prefix):
        return normalized.removeprefix(source_prefix)
    marker = "/aware/"
    if marker in normalized:
        return normalized.split(marker, 1)[1]
    return normalized


def _semantic_package_object_id(*, payload: Mapping[str, object]) -> UUID | None:
    receipt = payload.get("materialization_index_receipt")
    receipt_payload = receipt if isinstance(receipt, Mapping) else {}
    semantic = receipt_payload.get("semantic")
    semantic_payload = semantic if isinstance(semantic, Mapping) else {}
    return _uuid_value(
        semantic_payload.get("object_config_graph_package_id")
        or payload.get("object_config_graph_package_id")
    )


def _semantic_root_commit_id(*, payload: Mapping[str, object]) -> UUID | None:
    receipt = payload.get("materialization_index_receipt")
    receipt_payload = receipt if isinstance(receipt, Mapping) else {}
    semantic = receipt_payload.get("semantic")
    semantic_payload = semantic if isinstance(semantic, Mapping) else {}
    return _uuid_value(
        semantic_payload.get("object_config_graph_object_instance_graph_commit_id")
        or payload.get("object_config_graph_object_instance_graph_commit_id")
    )


def _semantic_package_commit_id(*, payload: Mapping[str, object]) -> UUID | None:
    receipt = payload.get("materialization_index_receipt")
    receipt_payload = receipt if isinstance(receipt, Mapping) else {}
    semantic = receipt_payload.get("semantic")
    semantic_payload = semantic if isinstance(semantic, Mapping) else {}
    return _uuid_value(
        semantic_payload.get(
            "object_config_graph_package_object_instance_graph_commit_id"
        )
        or payload.get("object_config_graph_package_object_instance_graph_commit_id")
    )


def _semantic_root_head_commit_id(*, payload: Mapping[str, object]) -> UUID | None:
    receipt = payload.get("materialization_index_receipt")
    receipt_payload = receipt if isinstance(receipt, Mapping) else {}
    semantic = receipt_payload.get("semantic")
    semantic_payload = semantic if isinstance(semantic, Mapping) else {}
    return _uuid_value(
        semantic_payload.get("object_config_graph_head_commit_id")
        or payload.get("object_config_graph_head_commit_id")
    )


def _semantic_package_head_commit_id(*, payload: Mapping[str, object]) -> UUID | None:
    receipt = payload.get("materialization_index_receipt")
    receipt_payload = receipt if isinstance(receipt, Mapping) else {}
    semantic = receipt_payload.get("semantic")
    semantic_payload = semantic if isinstance(semantic, Mapping) else {}
    return _uuid_value(
        semantic_payload.get("object_config_graph_package_head_commit_id")
        or payload.get("object_config_graph_package_head_commit_id")
    )


def _source_head_commit_id(*, payload: Mapping[str, object]) -> UUID | None:
    receipt = payload.get("materialization_index_receipt")
    receipt_payload = receipt if isinstance(receipt, Mapping) else {}
    source = receipt_payload.get("source")
    source_payload = source if isinstance(source, Mapping) else {}
    return _uuid_value(
        source_payload.get("code_package_head_commit_id")
        or payload.get("code_package_head_commit_id")
    )


def _source_commit_id(*, payload: Mapping[str, object]) -> UUID | None:
    receipt = payload.get("materialization_index_receipt")
    receipt_payload = receipt if isinstance(receipt, Mapping) else {}
    source = receipt_payload.get("source")
    source_payload = source if isinstance(source, Mapping) else {}
    return _uuid_value(
        source_payload.get("code_package_object_instance_graph_commit_id")
        or payload.get("code_package_object_instance_graph_commit_id")
    )


def _remember_projection_entry(
    *,
    projections_by_name: dict[str, MetaRuntimeProjectionIndexEntry],
    projection_entry: MetaRuntimeProjectionIndexEntry,
) -> None:
    existing = projections_by_name.get(projection_entry.projection_name)
    if existing is not None and _projection_entries_conflict(
        existing=existing,
        projection_entry=projection_entry,
    ):
        raise ValueError(
            "Conflicting Meta runtime projection index entries for projection "
            f"{projection_entry.projection_name!r}: "
            f"{existing.package_name!r}/{existing.projection_hash!r} != "
            f"{projection_entry.package_name!r}/{projection_entry.projection_hash!r}"
        )
    if existing is None or _projection_entry_should_replace_existing(
        existing=existing,
        projection_entry=projection_entry,
    ):
        projections_by_name[projection_entry.projection_name] = projection_entry


def _projection_entries_conflict(
    *,
    existing: MetaRuntimeProjectionIndexEntry,
    projection_entry: MetaRuntimeProjectionIndexEntry,
) -> bool:
    if existing.package_name != projection_entry.package_name:
        return True
    if (
        existing.projection_hash is None
        or projection_entry.projection_hash is None
        or existing.projection_hash == projection_entry.projection_hash
    ):
        return False
    return not _receipt_projection_precedence_applies(
        existing=existing,
        projection_entry=projection_entry,
    )


def _same_package_projection_entry(
    *,
    existing: MetaRuntimeProjectionIndexEntry,
    projection_entry: MetaRuntimeProjectionIndexEntry,
) -> bool:
    return (
        existing.package_name == projection_entry.package_name
        and existing.fqn_prefix == projection_entry.fqn_prefix
        and _manifest_paths_match(
            existing.manifest_path, projection_entry.manifest_path
        )
    )


def _receipt_projection_precedence_applies(
    *,
    existing: MetaRuntimeProjectionIndexEntry,
    projection_entry: MetaRuntimeProjectionIndexEntry,
) -> bool:
    existing_receipt = existing.evidence_source == "materialization_index_receipt"
    incoming_receipt = (
        projection_entry.evidence_source == "materialization_index_receipt"
    )
    return existing_receipt != incoming_receipt


def _projection_entry_should_replace_existing(
    *,
    existing: MetaRuntimeProjectionIndexEntry,
    projection_entry: MetaRuntimeProjectionIndexEntry,
) -> bool:
    if (
        existing.projection_hash is None
        and projection_entry.projection_hash is not None
    ):
        return True
    return (
        projection_entry.evidence_source == "materialization_index_receipt"
        and existing.evidence_source != "materialization_index_receipt"
    )


def _package_catalog_signature(
    *,
    repo_root: Path,
    package_entries: tuple[MetaRuntimePackageIndexEntry, ...],
) -> str:
    root = repo_root.expanduser().resolve()
    hasher = hashlib.sha256()
    hasher.update(b"aware-meta-runtime-package-catalog-v2\n")
    for entry in package_entries:
        try:
            manifest_key = entry.manifest_path.resolve().relative_to(root).as_posix()
        except ValueError:
            manifest_key = entry.manifest_path.resolve().as_posix()
        parts = (
            entry.module_id,
            entry.package_name,
            entry.fqn_prefix,
            manifest_key,
            ",".join(entry.dependency_package_names),
            entry.runtime_handler_provider_import_root or "",
        )
        hasher.update("|".join(parts).encode("utf-8"))
        hasher.update(b"\n")
    return hasher.hexdigest()


def _sorted_package_entries(
    entries: Iterable[MetaRuntimePackageIndexEntry],
) -> tuple[MetaRuntimePackageIndexEntry, ...]:
    return tuple(
        sorted(
            entries,
            key=lambda item: (
                item.module_id,
                item.package_name,
                item.manifest_path.as_posix(),
            ),
        )
    )


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


def _string_value(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _path_value(value: object) -> Path | None:
    text = _string_value(value)
    return Path(text) if text is not None else None


def _uuid_value(value: object) -> UUID | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return UUID(value)
    except ValueError:
        return None


def _uuid_text(value: UUID | None) -> str | None:
    return str(value) if value is not None else None


def _bool_value(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _json_payload_mapping(value: Mapping[str, object]) -> dict[str, object]:
    return {
        str(key): _json_payload_value(raw_value)
        for key, raw_value in sorted(value.items(), key=lambda item: str(item[0]))
    }


def _json_payload_value(value: object) -> object:
    if isinstance(value, Mapping):
        return _json_payload_mapping(value)
    if isinstance(value, tuple | list):
        return [_json_payload_value(item) for item in value]
    if isinstance(value, UUID):
        return str(value)
    return value


__all__ = [
    "META_RUNTIME_PACKAGE_PROJECTION_INDEX_SCHEMA",
    "META_RUNTIME_PACKAGE_PROJECTION_INDEX_VERSION",
    "MetaRuntimePackageIndexPatch",
    "MetaRuntimePackageIndexEntry",
    "MetaRuntimePackageProjectionIndex",
    "MetaRuntimeProjectionIndexEntry",
    "MetaRuntimeSemanticObjectIndexEntry",
    "apply_meta_runtime_package_index_patch",
    "build_meta_runtime_package_projection_index",
    "load_meta_runtime_package_projection_index",
    "load_meta_runtime_package_projection_lookup",
    "meta_runtime_package_projection_index_path",
    "meta_runtime_package_projection_lookup_path",
    "record_full_package_materialization_index",
    "record_meta_runtime_package_index_patch",
    "stable_meta_runtime_package_branch_id",
]
