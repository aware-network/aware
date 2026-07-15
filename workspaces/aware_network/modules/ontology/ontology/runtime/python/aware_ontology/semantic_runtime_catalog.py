from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from aware_code.semantic_materialization import (
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY,
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
)


ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY = "ontology_runtime_artifact_set"
ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY = "ontology_runtime_artifact_set"
ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_ROLE = "runtime_artifact_set"
ONTOLOGY_RUNTIME_ARTIFACT_SET_CONTRACT_VERSION = (
    "aware.ontology.runtime_artifact_set.v1"
)
ONTOLOGY_RUNTIME_BUNDLE_MANIFEST_ARTIFACT_ROLE = "runtime_bundle_manifest"
ONTOLOGY_RUNTIME_BUNDLE_MANIFEST_CONTRACT_VERSION = (
    "aware.ontology.runtime_bundle_manifest.v1"
)
ONTOLOGY_RUNTIME_BUNDLE_MANIFEST_REQUIRED_FOR = (
    "workspace_revision",
    "node_deployment",
    "service_boot",
    "projection_runtime",
    "db_schema",
)
ONTOLOGY_RUNTIME_DB_SCHEMA_REGISTRY_ARTIFACT_ROLE = "db_schema_registry"
ONTOLOGY_RUNTIME_DB_SCHEMA_REGISTRY_CONTRACT_VERSION = (
    "aware.ontology.db_schema_registry.v1"
)
ONTOLOGY_RUNTIME_DB_SCHEMA_REGISTRY_REQUIRED_FOR = (
    "workspace_revision",
    "node_deployment",
    "service_boot",
    "ontology_persistence",
    "db_schema",
)
ONTOLOGY_RUNTIME_PYTHON_MODELS_MANIFEST_ARTIFACT_ROLE = "python_models_manifest"
ONTOLOGY_RUNTIME_PYTHON_MODELS_MANIFEST_CONTRACT_VERSION = (
    "aware.ontology.python_models_manifest.v1"
)
ONTOLOGY_RUNTIME_PYTHON_MODELS_MANIFEST_REQUIRED_FOR = (
    "workspace_revision",
    "api_runtime",
    "sdk_runtime",
    "model_bootstrap",
)
ONTOLOGY_RUNTIME_ARTIFACT_SET_ACTIVATION_POLICY = (
    "workspace_revision_or_service_lifecycle_required"
)
ONTOLOGY_RUNTIME_ARTIFACT_SET_PRODUCER_PROVIDER_KEY = "aware_ontology"
ONTOLOGY_RUNTIME_ARTIFACT_SET_PRODUCER_KEY = ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY
ONTOLOGY_RUNTIME_ARTIFACT_SET_SEMANTIC_OWNER = "aware_ontology.provider"
ONTOLOGY_RUNTIME_ARTIFACT_SET_REQUIRED_FOR = (
    "workspace_revision",
    "runtime_index",
    "service_boot",
)


@dataclass(frozen=True, slots=True)
class SemanticOntologyPackageCatalogEntry:
    module_id: str
    package_name: str
    fqn_prefix: str
    manifest_path: Path
    dependency_package_names: tuple[str, ...]
    projection_names: tuple[str, ...]


def resolve_semantic_ontology_package_manifest_closure(
    *,
    context: Mapping[str, object],
    repo_root: Path,
    package_names: Iterable[str] = (),
    required_projection_names: Iterable[str] = (),
) -> tuple[Path, ...]:
    """Resolve dependency-ordered ontology structure manifests from catalog truth."""

    entries_by_package_name = semantic_ontology_package_catalog_entries_by_name(
        context=context,
        repo_root=repo_root,
    )
    seed_package_names = tuple(
        dict.fromkeys(
            (
                *_clean_string_tuple(package_names),
                *semantic_ontology_package_names_for_projection_names(
                    entries_by_package_name=entries_by_package_name,
                    required_projection_names=required_projection_names,
                ),
            )
        )
    )
    return _topological_manifest_closure(
        entries_by_package_name=entries_by_package_name,
        seed_package_names=seed_package_names,
    )


def semantic_ontology_package_catalog_entries_by_name(
    *,
    context: Mapping[str, object],
    repo_root: Path,
) -> dict[str, SemanticOntologyPackageCatalogEntry]:
    raw_catalog = context.get(SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY)
    if not isinstance(raw_catalog, Mapping):
        raise ValueError(
            "Semantic ontology package catalog is required for runtime resolution."
        )
    if raw_catalog.get("schema") != SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA:
        raise ValueError("Semantic ontology package catalog has an unsupported schema.")
    raw_entries = raw_catalog.get("entries")
    if not isinstance(raw_entries, list):
        raise ValueError("Semantic ontology package catalog must include entries.")

    entries_by_package_name: dict[str, SemanticOntologyPackageCatalogEntry] = {}
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, Mapping):
            raise ValueError(
                "Semantic ontology package catalog entries must be mappings."
            )
        entry = _entry_from_payload(payload=raw_entry, repo_root=repo_root)
        entries_by_package_name[entry.package_name] = entry
    return entries_by_package_name


def semantic_ontology_package_names_for_projection_names(
    *,
    entries_by_package_name: Mapping[str, SemanticOntologyPackageCatalogEntry],
    required_projection_names: Iterable[str],
) -> tuple[str, ...]:
    required = frozenset(_clean_string_tuple(required_projection_names))
    if not required:
        return ()
    package_names: list[str] = []
    for package_name, entry in entries_by_package_name.items():
        if required.intersection(entry.projection_names):
            package_names.append(package_name)
    return tuple(dict.fromkeys(package_names))


def resolve_ontology_runtime_artifact_set_payload(
    *,
    source_payload: Mapping[str, object] | None = None,
    package_name: str | None = None,
    fqn_prefix: str | None = None,
    artifact_set_id: str | None = None,
    workspace_revision_id: str | None = None,
    materialization_ref: str | None = None,
    include_artifacts: bool = True,
) -> dict[str, object]:
    """Resolve the ontology-owned runtime artifact-set descriptor payload."""

    payload = dict(source_payload or {})
    existing = payload.get(ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY)
    if isinstance(existing, Mapping):
        resolved = dict(_jsonish(existing))
        if (
            artifact_set_id is not None
            and resolved.get("artifact_set_id") != artifact_set_id
        ):
            raise ValueError(
                "Ontology runtime artifact-set id mismatch: "
                f"expected={artifact_set_id!r} actual={resolved.get('artifact_set_id')!r}."
            )
        if package_name is not None and resolved.get("package_name") != package_name:
            raise ValueError(
                "Ontology runtime artifact-set package mismatch: "
                f"expected={package_name!r} actual={resolved.get('package_name')!r}."
            )
        if fqn_prefix is not None and resolved.get("fqn_prefix") != fqn_prefix:
            raise ValueError(
                "Ontology runtime artifact-set fqn_prefix mismatch: "
                f"expected={fqn_prefix!r} actual={resolved.get('fqn_prefix')!r}."
            )
        if not include_artifacts:
            resolved["artifacts"] = []
        return resolved

    return build_ontology_runtime_artifact_set_from_materialization_details(
        details=payload,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        artifact_set_id=artifact_set_id,
        workspace_revision_id=workspace_revision_id,
        materialization_ref=materialization_ref,
        include_artifacts=include_artifacts,
    )


def resolve_local_ontology_runtime_artifact_set_payload(
    *,
    package_name: str,
    fqn_prefix: str,
    source_manifest_path: str | Path,
    ontology_manifest_path: str | Path | None = None,
    workspace_root: str | Path | None = None,
    include_artifacts: bool = True,
) -> dict[str, object]:
    """Resolve local package-owned ontology runtime artifacts as an artifact set.

    This is the local Workspace materialization counterpart to the service/SDK
    `resolve_runtime_artifact_set` operation. Callers consume artifact refs by
    role; they must not encode ontology package filesystem conventions.
    """

    source_manifest = Path(source_manifest_path).expanduser().resolve()
    source_root = source_manifest.parent
    runtime_root = source_root / ".aware" / "ontology" / "runtime"
    runtime_manifest = runtime_root / "ontology.runtime.manifest.json"
    db_schema_registry = runtime_root / "db.schema.registry.json"
    resolved_python_models = _resolve_local_python_models_manifest_path(
        source_root=source_root,
    )
    expected_python_models = _default_local_python_models_manifest_path(
        source_root=source_root,
    )
    python_models = resolved_python_models or expected_python_models
    details: dict[str, object] = {
        "schema": "aware_ontology.local_runtime_artifact_set.v1",
        "provider_key": ONTOLOGY_RUNTIME_ARTIFACT_SET_PRODUCER_PROVIDER_KEY,
        "semantic_owner": ONTOLOGY_RUNTIME_ARTIFACT_SET_SEMANTIC_OWNER,
        "manifest_path": _path_text(ontology_manifest_path),
        "source_manifest_path": source_manifest.as_posix(),
        "package_name": package_name,
        "fqn_prefix": fqn_prefix,
        "runtime_bundle_manifest_path": runtime_manifest.as_posix(),
        "runtime_bundle_manifest_workspace_relative_path": (
            _workspace_relative_path(runtime_manifest, workspace_root=workspace_root)
        ),
        "runtime_bundle_manifest_status": (
            "available" if runtime_manifest.is_file() else "missing"
        ),
        "runtime_bundle_manifest_error": (
            None if runtime_manifest.is_file() else "ontology runtime manifest missing"
        ),
        "runtime_bundle_db_schema_registry_path": (
            db_schema_registry.as_posix() if db_schema_registry.is_file() else None
        ),
        "runtime_bundle_db_schema_registry_workspace_relative_path": (
            _workspace_relative_path(db_schema_registry, workspace_root=workspace_root)
            if db_schema_registry.is_file()
            else None
        ),
        "python_models_manifest_path": (
            python_models.as_posix() if python_models is not None else None
        ),
        "python_models_manifest_workspace_relative_path": (
            _workspace_relative_path(python_models, workspace_root=workspace_root)
            if python_models is not None
            else None
        ),
    }
    if runtime_manifest.is_file():
        runtime_manifest_payload = runtime_manifest.read_bytes()
        details["runtime_bundle_manifest_digest"] = (
            "sha256:" + hashlib.sha256(runtime_manifest_payload).hexdigest()
        )
        details["runtime_bundle_manifest_size_bytes"] = len(runtime_manifest_payload)
    if db_schema_registry.is_file():
        db_schema_payload = db_schema_registry.read_bytes()
        details["runtime_bundle_db_schema_registry_digest"] = (
            "sha256:" + hashlib.sha256(db_schema_payload).hexdigest()
        )
        details["runtime_bundle_db_schema_registry_sql_roots"] = (
            _db_schema_registry_sql_roots(db_schema_registry)
        )
    if resolved_python_models is not None:
        python_models_payload = python_models.read_bytes()
        details["python_models_manifest_status"] = "available"
        details["python_models_manifest_digest"] = (
            "sha256:" + hashlib.sha256(python_models_payload).hexdigest()
        )
        details["python_models_manifest_size_bytes"] = len(python_models_payload)
    else:
        details["python_models_manifest_status"] = "missing"
        details["python_models_manifest_error"] = "python models manifest missing"
    return build_ontology_runtime_artifact_set_from_materialization_details(
        details=details,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        include_artifacts=include_artifacts,
    )


def find_ontology_runtime_artifact_ref(
    *,
    artifact_set: Mapping[str, object],
    artifact_role: str,
    output_key: str | None = None,
    require_available: bool = True,
) -> Mapping[str, object] | None:
    artifacts = artifact_set.get("artifacts")
    if not isinstance(artifacts, list):
        return None
    for artifact in artifacts:
        if not isinstance(artifact, Mapping):
            continue
        if _non_empty_text(artifact.get("artifact_role")) != artifact_role:
            continue
        if (
            output_key is not None
            and _non_empty_text(artifact.get("output_key")) != output_key
        ):
            continue
        if require_available and _non_empty_text(artifact.get("status")) != "available":
            continue
        return artifact
    return None


def ontology_runtime_artifact_ref_path(
    *,
    artifact_ref: Mapping[str, object],
    workspace_root: str | Path | None = None,
) -> Path | None:
    workspace_relative_path = _non_empty_text(
        artifact_ref.get("workspace_relative_path")
    )
    if workspace_relative_path is not None and workspace_root is not None:
        return (
            Path(workspace_root).expanduser().resolve() / workspace_relative_path
        ).resolve()
    manifest_path = _non_empty_text(artifact_ref.get("manifest_path"))
    if manifest_path is not None:
        return Path(manifest_path).expanduser().resolve()
    uri = _non_empty_text(artifact_ref.get("uri"))
    if uri is not None and not uri.startswith(("http://", "https://")):
        return Path(uri).expanduser().resolve()
    return None


def build_ontology_runtime_artifact_set_from_materialization_details(
    *,
    details: Mapping[str, object],
    package_name: str | None = None,
    fqn_prefix: str | None = None,
    artifact_set_id: str | None = None,
    workspace_revision_id: str | None = None,
    materialization_ref: str | None = None,
    include_artifacts: bool = True,
) -> dict[str, object]:
    """Build the DTO payload emitted by Ontology semantic materialization."""

    package_name = _required_payload_text(
        package_name if package_name is not None else details.get("package_name"),
        "package_name",
    )
    fqn_prefix = _required_payload_text(
        fqn_prefix if fqn_prefix is not None else details.get("fqn_prefix"),
        "fqn_prefix",
    )
    provenance = _runtime_artifact_set_provenance(
        details=details,
        workspace_revision_id=workspace_revision_id,
        materialization_ref=materialization_ref,
    )
    artifacts = _runtime_artifact_refs_from_details(
        details=details,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    runtime_projection_descriptors = _runtime_projection_descriptors_from_details(
        details=details,
    )
    materialized_semantic_roots = _materialized_semantic_root_refs_from_details(
        details=details,
    )
    required_roles = _required_artifact_roles(artifacts)
    resolved_artifact_set_id = artifact_set_id or _runtime_artifact_set_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        provenance=provenance,
        artifacts=artifacts,
        runtime_projection_descriptors=runtime_projection_descriptors,
    )
    return {
        "schema_version": 1,
        "artifact_set_id": resolved_artifact_set_id,
        "package_name": package_name,
        "fqn_prefix": fqn_prefix,
        "runtime_contract_version": ONTOLOGY_RUNTIME_ARTIFACT_SET_CONTRACT_VERSION,
        "lifecycle_state": "produced",
        "activation_allowed": False,
        "activation_policy": ONTOLOGY_RUNTIME_ARTIFACT_SET_ACTIVATION_POLICY,
        "artifacts": artifacts if include_artifacts else [],
        "required_artifact_roles": required_roles,
        "runtime_projection_descriptors": runtime_projection_descriptors,
        "materialized_semantic_roots": materialized_semantic_roots,
        "provenance": provenance,
        "metadata": {
            "provider_key": "aware_ontology",
            "semantic_owner": "aware_ontology.provider",
            "source_schema": _jsonish(details.get("schema")),
            "object_config_graph_hash": _non_empty_text(
                details.get("object_config_graph_hash")
            ),
            "semantic_commit_strategy": _jsonish(
                details.get("semantic_commit_strategy")
            ),
            "materialized_semantic_roots": _jsonish(
                details.get("materialized_semantic_roots") or ()
            ),
            "meta_language_materialization_bridge": _jsonish(
                details.get("meta_language_materialization_bridge") or {}
            ),
        },
    }


def build_ontology_runtime_artifact_set_ownership_receipt(
    *,
    artifact_set: Mapping[str, object],
) -> dict[str, object]:
    """Build the Workspace artifact-ref receipt for the runtime artifact set."""

    payload = dict(_jsonish(artifact_set))
    package_name = _required_payload_text(payload.get("package_name"), "package_name")
    fqn_prefix = _required_payload_text(payload.get("fqn_prefix"), "fqn_prefix")
    artifact_set_id = _required_payload_text(
        payload.get("artifact_set_id"),
        "artifact_set_id",
    )
    activation_allowed = bool(payload.get("activation_allowed") is True)
    lifecycle_state = _non_empty_text(payload.get("lifecycle_state")) or "produced"
    activation_policy = (
        _non_empty_text(payload.get("activation_policy"))
        or ONTOLOGY_RUNTIME_ARTIFACT_SET_ACTIVATION_POLICY
    )
    runtime_contract_version = (
        _non_empty_text(payload.get("runtime_contract_version"))
        or ONTOLOGY_RUNTIME_ARTIFACT_SET_CONTRACT_VERSION
    )
    required_artifact_roles = _clean_string_tuple(
        payload.get("required_artifact_roles")
    )
    artifacts = tuple(_mapping_items(payload.get("artifacts")))
    runtime_projection_descriptors = tuple(
        _mapping_items(payload.get("runtime_projection_descriptors"))
    )
    return {
        "producer_provider_key": ONTOLOGY_RUNTIME_ARTIFACT_SET_PRODUCER_PROVIDER_KEY,
        "semantic_owner": ONTOLOGY_RUNTIME_ARTIFACT_SET_SEMANTIC_OWNER,
        "producer_key": ONTOLOGY_RUNTIME_ARTIFACT_SET_PRODUCER_KEY,
        "producer_kind": "ontology_runtime_artifact_set",
        "output_key": ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY,
        "output_kind": "materialization_detail",
        "artifact_family": ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY,
        "artifact_role": ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_ROLE,
        "artifact_key": artifact_set_id,
        "package_name": package_name,
        "fqn_prefix": fqn_prefix,
        "status": "available",
        "required_for": list(ONTOLOGY_RUNTIME_ARTIFACT_SET_REQUIRED_FOR),
        "media_type": "application/json",
        "runtime_contract_version": runtime_contract_version,
        "digest": _stable_json_sha256(payload),
        "digest_algorithm": "sha256",
        "provider_payload": {
            "package_name": package_name,
            "fqn_prefix": fqn_prefix,
            "artifact_set_id": artifact_set_id,
            "lifecycle_state": lifecycle_state,
            "activation_allowed": activation_allowed,
            "activation_policy": activation_policy,
            "artifact_count": len(artifacts),
            "required_artifact_roles": list(required_artifact_roles),
            "runtime_projection_descriptor_count": len(runtime_projection_descriptors),
        },
        ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY: payload,
    }


def _entry_from_payload(
    *,
    payload: Mapping[str, object],
    repo_root: Path,
) -> SemanticOntologyPackageCatalogEntry:
    module_id = _required_text(payload, "module_id")
    package_name = _required_text(payload, "package_name")
    fqn_prefix = _required_text(payload, "fqn_prefix")
    manifest_path = _catalog_manifest_path(payload=payload, repo_root=repo_root)
    return SemanticOntologyPackageCatalogEntry(
        module_id=module_id,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=manifest_path,
        dependency_package_names=_clean_string_tuple(
            payload.get("dependency_package_names")
        ),
        projection_names=_clean_string_tuple(payload.get("projection_names")),
    )


def _catalog_manifest_path(*, payload: Mapping[str, object], repo_root: Path) -> Path:
    raw_path = Path(_required_text(payload, "manifest_path")).expanduser()
    if raw_path.is_absolute():
        return raw_path.resolve()
    owner_root = _catalog_owner_root(payload=payload, repo_root=repo_root)
    return (owner_root / raw_path).resolve()


def _catalog_owner_root(*, payload: Mapping[str, object], repo_root: Path) -> Path:
    raw_owner_root = payload.get("owner_root")
    if not isinstance(raw_owner_root, str) or not raw_owner_root.strip():
        return repo_root.expanduser().resolve()
    owner_root = Path(raw_owner_root.strip()).expanduser()
    if owner_root.is_absolute():
        return owner_root.resolve()
    return (repo_root / owner_root).resolve()


def _topological_manifest_closure(
    *,
    entries_by_package_name: Mapping[str, SemanticOntologyPackageCatalogEntry],
    seed_package_names: tuple[str, ...],
) -> tuple[Path, ...]:
    ordered_paths: list[Path] = []
    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(package_name: str) -> None:
        if package_name in visited:
            return
        if package_name in visiting:
            raise ValueError(
                "Cyclic semantic ontology package dependency: "
                + " -> ".join((*sorted(visiting), package_name))
            )
        entry = entries_by_package_name.get(package_name)
        if entry is None:
            raise ValueError(
                "Missing semantic ontology package dependency for runtime "
                f"context: {package_name!r}"
            )
        visiting.add(package_name)
        for dependency_package_name in entry.dependency_package_names:
            visit(dependency_package_name)
        visiting.remove(package_name)
        visited.add(package_name)
        ordered_paths.append(entry.manifest_path)

    for package_name in seed_package_names:
        visit(package_name)
    return _dedupe_paths(ordered_paths)


def _required_text(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Semantic ontology package catalog entry missing {key!r}.")
    return value.strip()


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


def _dedupe_paths(paths: Iterable[Path]) -> tuple[Path, ...]:
    deduped: list[Path] = []
    seen: set[Path] = set()
    for raw_path in paths:
        path = raw_path.expanduser().resolve()
        if path in seen:
            continue
        seen.add(path)
        deduped.append(path)
    return tuple(deduped)


def _runtime_artifact_set_provenance(
    *,
    details: Mapping[str, object],
    workspace_revision_id: str | None,
    materialization_ref: str | None,
) -> dict[str, object]:
    return {
        "source_kind": (
            "workspace_revision"
            if _non_empty_text(workspace_revision_id) is not None
            else "ontology_materialization"
        ),
        "workspace_revision_id": _non_empty_text(workspace_revision_id),
        "materialization_ref": _non_empty_text(materialization_ref)
        or _non_empty_text(details.get("manifest_path")),
        "ontology_config_id": _jsonish(details.get("ontology_config_id")),
        "ontology_config_commit_id": _jsonish(details.get("ontology_config_commit_id")),
        "ontology_config_head_commit_id": _jsonish(
            details.get("ontology_config_head_commit_id")
        ),
        "ontology_config_object_instance_graph_commit_id": _jsonish(
            details.get("ontology_config_object_instance_graph_commit_id")
        ),
        "ontology_package_id": _jsonish(details.get("ontology_package_id")),
        "ontology_package_commit_id": _jsonish(
            details.get("ontology_package_commit_id")
        ),
        "ontology_package_head_commit_id": _jsonish(
            details.get("ontology_package_head_commit_id")
        ),
        "ontology_package_object_instance_graph_commit_id": _jsonish(
            details.get("ontology_package_object_instance_graph_commit_id")
        ),
        "object_config_graph_id": _jsonish(details.get("object_config_graph_id")),
        "object_config_graph_commit_id": _jsonish(
            details.get("object_config_graph_commit_id")
        ),
        "object_config_graph_package_id": _jsonish(
            details.get("object_config_graph_package_id")
        ),
        "source_code_package_id": _jsonish(details.get("source_code_package_id")),
        "source_code_package_commit_id": _jsonish(
            details.get("source_code_package_commit_id")
        ),
        "source_manifest_path": _non_empty_text(details.get("source_manifest_path")),
        "ontology_manifest_path": _non_empty_text(details.get("manifest_path")),
        "producer_receipt": {
            "schema": _jsonish(details.get("schema")),
            "provider_key": _jsonish(details.get("provider_key")),
            "semantic_owner": _jsonish(details.get("semantic_owner")),
        },
    }


def _runtime_artifact_refs_from_details(
    *,
    details: Mapping[str, object],
    package_name: str,
    fqn_prefix: str,
) -> list[dict[str, object]]:
    artifacts: list[dict[str, object]] = []
    _append_manifest_artifact_refs(
        artifacts=artifacts,
        details=details,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    _append_runtime_bundle_manifest_artifact_ref(
        artifacts=artifacts,
        details=details,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    _append_db_schema_registry_artifact_ref(
        artifacts=artifacts,
        details=details,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    _append_python_models_manifest_artifact_ref(
        artifacts=artifacts,
        details=details,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    _append_identity_artifact_refs(
        artifacts=artifacts,
        details=details,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    _append_receipt_artifact_refs(
        artifacts=artifacts,
        details=details,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    return artifacts


def _append_manifest_artifact_refs(
    *,
    artifacts: list[dict[str, object]],
    details: Mapping[str, object],
    package_name: str,
    fqn_prefix: str,
) -> None:
    manifest_path = _non_empty_text(details.get("manifest_path"))
    if manifest_path is not None:
        artifacts.append(
            _runtime_artifact_ref(
                artifact_family="ontology_manifest",
                artifact_key=f"{package_name}:ontology_manifest",
                artifact_role="ontology_manifest",
                package_name=package_name,
                fqn_prefix=fqn_prefix,
                manifest_path=manifest_path,
                workspace_relative_path=manifest_path,
                runtime_contract_version="aware.ontology.manifest.v1",
            )
        )
    source_manifest_path = _non_empty_text(details.get("source_manifest_path"))
    if source_manifest_path is not None:
        artifacts.append(
            _runtime_artifact_ref(
                artifact_family="ontology_manifest",
                artifact_key=f"{package_name}:source_manifest",
                artifact_role="source_manifest",
                package_name=package_name,
                fqn_prefix=fqn_prefix,
                manifest_path=source_manifest_path,
                workspace_relative_path=source_manifest_path,
                runtime_contract_version="aware.package.manifest.v1",
            )
        )


def _append_runtime_bundle_manifest_artifact_ref(
    *,
    artifacts: list[dict[str, object]],
    details: Mapping[str, object],
    package_name: str,
    fqn_prefix: str,
) -> None:
    manifest_path = _non_empty_text(details.get("runtime_bundle_manifest_path"))
    workspace_relative_path = _non_empty_text(
        details.get("runtime_bundle_manifest_workspace_relative_path")
    )
    status = _non_empty_text(details.get("runtime_bundle_manifest_status"))
    if manifest_path is None and workspace_relative_path is None and status is None:
        return

    status = status or "available"
    path_key = workspace_relative_path or manifest_path or "unavailable"
    artifacts.append(
        _runtime_artifact_ref(
            artifact_family="ontology_runtime_bundle",
            artifact_key=f"{package_name}:runtime_bundle_manifest:{path_key}",
            artifact_role=ONTOLOGY_RUNTIME_BUNDLE_MANIFEST_ARTIFACT_ROLE,
            output_key="runtime_bundle_manifest",
            output_kind="runtime_manifest",
            required_for=ONTOLOGY_RUNTIME_BUNDLE_MANIFEST_REQUIRED_FOR,
            status=status,
            producer_provider_key=ONTOLOGY_RUNTIME_ARTIFACT_SET_PRODUCER_PROVIDER_KEY,
            producer_key="aware_ontology.runtime_bundle_manifest",
            producer_kind="OntologyRuntimeBundleManifest",
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            digest=_non_empty_text(details.get("runtime_bundle_manifest_digest")),
            workspace_relative_path=workspace_relative_path,
            manifest_path=manifest_path,
            media_type="application/json",
            runtime_contract_version=(
                ONTOLOGY_RUNTIME_BUNDLE_MANIFEST_CONTRACT_VERSION
            ),
            provider_payload={
                "manifest_role": "ontology_runtime_bundle_manifest",
                "manifest_path": manifest_path,
                "workspace_relative_path": workspace_relative_path,
                "status": status,
                "size_bytes": details.get("runtime_bundle_manifest_size_bytes"),
                "contains": [
                    "object_config_graph",
                    "graphsql_plans",
                    "projection_plans",
                    "orm_binding_snapshot",
                    "db_schema_registry",
                ],
            },
            receipt={
                "error": _non_empty_text(details.get("runtime_bundle_manifest_error")),
            },
            error=_non_empty_text(details.get("runtime_bundle_manifest_error")),
        )
    )


def _append_db_schema_registry_artifact_ref(
    *,
    artifacts: list[dict[str, object]],
    details: Mapping[str, object],
    package_name: str,
    fqn_prefix: str,
) -> None:
    path = _non_empty_text(details.get("runtime_bundle_db_schema_registry_path"))
    workspace_relative_path = _non_empty_text(
        details.get("runtime_bundle_db_schema_registry_workspace_relative_path")
    )
    if path is None and workspace_relative_path is None:
        return
    digest = _non_empty_text(details.get("runtime_bundle_db_schema_registry_digest"))
    sql_roots = _clean_string_tuple(
        details.get("runtime_bundle_db_schema_registry_sql_roots")
    )
    path_key = workspace_relative_path or path or "unavailable"
    artifacts.append(
        _runtime_artifact_ref(
            artifact_family="ontology_db_schema_registry",
            artifact_key=f"{package_name}:db_schema_registry:{path_key}",
            artifact_role=ONTOLOGY_RUNTIME_DB_SCHEMA_REGISTRY_ARTIFACT_ROLE,
            output_key="db_schema_registry",
            output_kind="db_schema_registry",
            required_for=ONTOLOGY_RUNTIME_DB_SCHEMA_REGISTRY_REQUIRED_FOR,
            status="available",
            producer_provider_key=ONTOLOGY_RUNTIME_ARTIFACT_SET_PRODUCER_PROVIDER_KEY,
            producer_key="aware_ontology.db_schema_registry",
            producer_kind="OntologyDatabaseSchemaRegistry",
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            digest=digest,
            workspace_relative_path=workspace_relative_path,
            manifest_path=path,
            media_type="application/json",
            runtime_contract_version=(
                ONTOLOGY_RUNTIME_DB_SCHEMA_REGISTRY_CONTRACT_VERSION
            ),
            provider_payload={
                "package_kind": "ontology",
                "backend_targets": ["postgres"],
                "sql_roots": list(sql_roots),
            },
            receipt={
                "sql_roots": list(sql_roots),
            },
        )
    )


def _append_python_models_manifest_artifact_ref(
    *,
    artifacts: list[dict[str, object]],
    details: Mapping[str, object],
    package_name: str,
    fqn_prefix: str,
) -> None:
    path = _non_empty_text(details.get("python_models_manifest_path"))
    workspace_relative_path = _non_empty_text(
        details.get("python_models_manifest_workspace_relative_path")
    )
    status = _non_empty_text(details.get("python_models_manifest_status"))
    if path is None and workspace_relative_path is None and status is None:
        return

    status = status or "available"
    path_key = workspace_relative_path or path or "unavailable"
    artifacts.append(
        _runtime_artifact_ref(
            artifact_family="ontology_model_bootstrap",
            artifact_key=f"{package_name}:python_models_manifest:{path_key}",
            artifact_role=ONTOLOGY_RUNTIME_PYTHON_MODELS_MANIFEST_ARTIFACT_ROLE,
            output_key="python_models_manifest",
            output_kind="model_bootstrap_manifest",
            required_for=ONTOLOGY_RUNTIME_PYTHON_MODELS_MANIFEST_REQUIRED_FOR,
            status=status,
            producer_provider_key=ONTOLOGY_RUNTIME_ARTIFACT_SET_PRODUCER_PROVIDER_KEY,
            producer_key="aware_ontology.python_models_manifest",
            producer_kind="OntologyPythonModelsManifest",
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            digest=_non_empty_text(details.get("python_models_manifest_digest")),
            workspace_relative_path=workspace_relative_path,
            manifest_path=path,
            media_type="application/json",
            runtime_contract_version=(
                ONTOLOGY_RUNTIME_PYTHON_MODELS_MANIFEST_CONTRACT_VERSION
            ),
            provider_payload={
                "manifest_role": "ontology_python_models_manifest",
                "manifest_path": path,
                "workspace_relative_path": workspace_relative_path,
                "status": status,
                "size_bytes": details.get("python_models_manifest_size_bytes"),
            },
            receipt={
                "error": _non_empty_text(details.get("python_models_manifest_error")),
            },
            error=_non_empty_text(details.get("python_models_manifest_error")),
        )
    )


def _append_identity_artifact_refs(
    *,
    artifacts: list[dict[str, object]],
    details: Mapping[str, object],
    package_name: str,
    fqn_prefix: str,
) -> None:
    identity_specs = (
        ("ontology_config", "ontology_config_id", "OntologyConfig"),
        ("ontology_package", "ontology_package_id", "OntologyPackage"),
        ("source_code_package", "source_code_package_id", "CodePackage"),
        ("object_config_graph", "object_config_graph_id", "ObjectConfigGraph"),
        (
            "object_config_graph_package",
            "object_config_graph_package_id",
            "ObjectConfigGraphPackage",
        ),
    )
    for artifact_role, id_key, producer_kind in identity_specs:
        identity = _non_empty_text(details.get(id_key))
        if identity is None:
            continue
        artifacts.append(
            _runtime_artifact_ref(
                artifact_family="ontology_runtime_identity",
                artifact_key=f"{package_name}:{artifact_role}:{identity}",
                artifact_role=artifact_role,
                package_name=package_name,
                fqn_prefix=fqn_prefix,
                producer_kind=producer_kind,
                receipt={id_key: identity},
            )
        )


def _append_receipt_artifact_refs(
    *,
    artifacts: list[dict[str, object]],
    details: Mapping[str, object],
    package_name: str,
    fqn_prefix: str,
) -> None:
    receipt_specs = (
        (
            "materialization_index_receipts",
            "materialization_index",
            "materialization_index",
        ),
        ("artifact_ownership_receipts", "artifact_ownership", "artifact_ownership"),
        ("lifecycle_receipts", "lifecycle_receipt", "lifecycle_receipt"),
        (
            "language_post_step_receipts",
            "language_post_step_receipt",
            "language_post_step_receipt",
        ),
        (
            "language_materialization_tool_step_receipts",
            "language_tool_step_receipt",
            "language_tool_step_receipt",
        ),
        (
            "language_materialization_code_package_refs",
            "language_code_package",
            "language_code_package_ref",
        ),
        ("materialized_language_packages", "language_package", "language_package"),
        ("compile_parity_receipts", "compile_parity", "compile_parity_receipt"),
    )
    for field_name, artifact_role, artifact_family in receipt_specs:
        for index, receipt in enumerate(_mapping_items(details.get(field_name))):
            artifacts.append(
                _runtime_artifact_ref_from_receipt(
                    receipt=receipt,
                    field_name=field_name,
                    index=index,
                    artifact_role=artifact_role,
                    artifact_family=artifact_family,
                    package_name=package_name,
                    fqn_prefix=fqn_prefix,
                )
            )


def _runtime_artifact_ref_from_receipt(
    *,
    receipt: Mapping[str, object],
    field_name: str,
    index: int,
    artifact_role: str,
    artifact_family: str,
    package_name: str,
    fqn_prefix: str,
) -> dict[str, object]:
    output_key = _non_empty_text(receipt.get("output_key"))
    output_kind = _non_empty_text(receipt.get("output_kind"))
    path = (
        _non_empty_text(receipt.get("workspace_relative_path"))
        or _non_empty_text(receipt.get("relative_path"))
        or _non_empty_text(receipt.get("path"))
        or _non_empty_text(receipt.get("receipt_path"))
    )
    artifact_key = (
        _non_empty_text(receipt.get("artifact_key"))
        or _non_empty_text(receipt.get("key"))
        or path
        or _non_empty_text(receipt.get("code_package_id"))
        or f"{field_name}:{index}"
    )
    return _runtime_artifact_ref(
        artifact_family=_non_empty_text(receipt.get("artifact_family"))
        or artifact_family,
        artifact_key=f"{package_name}:{artifact_key}",
        artifact_role=_non_empty_text(receipt.get("artifact_role")) or artifact_role,
        output_key=output_key,
        output_kind=output_kind,
        required_for=_clean_string_tuple(receipt.get("required_for")),
        status=_non_empty_text(receipt.get("status")) or "available",
        producer_provider_key=_non_empty_text(receipt.get("producer_provider_key"))
        or _non_empty_text(receipt.get("provider_key")),
        producer_key=_non_empty_text(receipt.get("producer_key")),
        producer_kind=_non_empty_text(receipt.get("producer_kind")),
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        digest=_non_empty_text(receipt.get("digest"))
        or _non_empty_text(receipt.get("hash")),
        uri=_non_empty_text(receipt.get("uri")),
        workspace_relative_path=path,
        manifest_path=_non_empty_text(receipt.get("manifest_path")),
        media_type=_non_empty_text(receipt.get("media_type")),
        runtime_contract_version=_non_empty_text(
            receipt.get("runtime_contract_version")
        ),
        provider_payload=_mapping_payload(receipt.get("provider_payload")),
        receipt=dict(_jsonish(receipt)),
        error=_non_empty_text(receipt.get("error")),
    )


def _runtime_artifact_ref(
    *,
    artifact_family: str,
    artifact_key: str,
    artifact_role: str,
    package_name: str,
    fqn_prefix: str,
    output_key: str | None = None,
    output_kind: str | None = None,
    required_for: Iterable[str] = (),
    status: str = "available",
    producer_provider_key: str | None = None,
    producer_key: str | None = None,
    producer_kind: str | None = None,
    digest: str | None = None,
    uri: str | None = None,
    workspace_relative_path: str | None = None,
    manifest_path: str | None = None,
    media_type: str | None = None,
    runtime_contract_version: str | None = None,
    provider_payload: Mapping[str, object] | None = None,
    receipt: Mapping[str, object] | None = None,
    error: str | None = None,
) -> dict[str, object]:
    return {
        "artifact_family": artifact_family,
        "artifact_key": artifact_key,
        "artifact_role": artifact_role,
        "output_key": output_key,
        "output_kind": output_kind,
        "required_for": list(_clean_string_tuple(required_for)),
        "status": status,
        "producer_provider_key": producer_provider_key,
        "producer_key": producer_key,
        "producer_kind": producer_kind,
        "package_name": package_name,
        "fqn_prefix": fqn_prefix,
        "digest": digest,
        "digest_algorithm": "sha256",
        "uri": uri,
        "workspace_relative_path": workspace_relative_path,
        "manifest_path": manifest_path,
        "media_type": media_type,
        "runtime_contract_version": runtime_contract_version,
        "provider_payload": dict(_jsonish(provider_payload or {})),
        "receipt": dict(_jsonish(receipt or {})),
        "error": error,
    }


def _required_artifact_roles(
    artifacts: Iterable[Mapping[str, object]],
) -> list[str]:
    roles = [
        "ontology_manifest",
        "source_manifest",
        "ontology_config",
        "ontology_package",
        "source_code_package",
        "object_config_graph",
        "object_config_graph_package",
    ]
    for artifact in artifacts:
        role = _non_empty_text(artifact.get("artifact_role"))
        if role is not None:
            roles.append(role)
    return list(dict.fromkeys(roles))


def _runtime_projection_descriptors_from_details(
    *,
    details: Mapping[str, object],
) -> list[dict[str, object]]:
    descriptors: list[dict[str, object]] = []
    default_ocg_id = _non_empty_text(details.get("object_config_graph_id"))
    default_opg_hashes = _clean_string_tuple(details.get("opg_hashes"))
    for item in _mapping_items(details.get("runtime_projection_descriptors")):
        projection_name = _non_empty_text(
            item.get("projection_name") or item.get("name")
        )
        if projection_name is None:
            continue
        projection_hash = _non_empty_text(
            item.get("projection_hash") or item.get("hash")
        )
        opg_hashes = _clean_string_tuple(item.get("opg_hashes")) or (
            default_opg_hashes
            if default_opg_hashes
            else ((projection_hash,) if projection_hash is not None else ())
        )
        descriptors.append(
            {
                "projection_name": projection_name,
                "projection_hash": projection_hash,
                "object_projection_graph_id": _non_empty_text(
                    item.get("object_projection_graph_id")
                    or item.get("object_projection_graph")
                    or item.get("opg_id")
                ),
                "constructor_function_id": _non_empty_text(
                    item.get("constructor_function_id")
                    or item.get("function_id")
                    or item.get("constructor_id")
                ),
                "object_config_graph_id": _non_empty_text(
                    item.get("object_config_graph_id") or default_ocg_id
                ),
                "opg_hashes": list(opg_hashes),
                "required_for": list(
                    _clean_string_tuple(item.get("required_for"))
                    or ("runtime_index", "service_boot")
                ),
                "metadata": _mapping_payload(item.get("metadata")),
            }
        )
    return sorted(
        descriptors,
        key=lambda descriptor: (
            str(descriptor.get("projection_name") or ""),
            str(descriptor.get("projection_hash") or ""),
            str(descriptor.get("object_projection_graph_id") or ""),
        ),
    )


def _materialized_semantic_root_refs_from_details(
    *,
    details: Mapping[str, object],
) -> list[dict[str, object]]:
    roots: list[dict[str, object]] = []
    for item in _mapping_items(details.get("materialized_semantic_roots")):
        root_kind = _non_empty_text(item.get("semantic_root_kind"))
        projection_name = _non_empty_text(item.get("semantic_projection_name"))
        if root_kind is None or projection_name is None:
            continue
        roots.append(
            {
                "semantic_root_kind": root_kind,
                "semantic_projection_name": projection_name,
                "semantic_projection_hash": _non_empty_text(
                    item.get("semantic_projection_hash")
                ),
                "semantic_package_id": _non_empty_text(item.get("semantic_package_id")),
                "semantic_root_id": _non_empty_text(item.get("semantic_root_id")),
                "semantic_head_commit_id": _non_empty_text(
                    item.get("semantic_head_commit_id")
                ),
                "semantic_object_instance_graph_commit_id": _non_empty_text(
                    item.get("semantic_object_instance_graph_commit_id")
                ),
                "semantic_root_object_instance_graph_commit_id": _non_empty_text(
                    item.get("semantic_root_object_instance_graph_commit_id")
                ),
            }
        )
    return roots


def _runtime_artifact_set_id(
    *,
    package_name: str,
    fqn_prefix: str,
    provenance: Mapping[str, object],
    artifacts: Iterable[Mapping[str, object]],
    runtime_projection_descriptors: Iterable[Mapping[str, object]],
) -> str:
    fingerprint = {
        "package_name": package_name,
        "fqn_prefix": fqn_prefix,
        "runtime_contract_version": ONTOLOGY_RUNTIME_ARTIFACT_SET_CONTRACT_VERSION,
        "provenance": _jsonish(provenance),
        "artifacts": [
            {
                "artifact_key": artifact.get("artifact_key"),
                "artifact_role": artifact.get("artifact_role"),
                "digest": artifact.get("digest"),
            }
            for artifact in artifacts
        ],
        "runtime_projection_descriptors": [
            {
                "projection_name": descriptor.get("projection_name"),
                "projection_hash": descriptor.get("projection_hash"),
                "object_projection_graph_id": descriptor.get(
                    "object_projection_graph_id"
                ),
                "constructor_function_id": descriptor.get("constructor_function_id"),
            }
            for descriptor in runtime_projection_descriptors
        ],
    }
    digest = hashlib.sha256(
        json.dumps(fingerprint, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"ontology-runtime-artifact-set:{digest}"


def _stable_json_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            _jsonish(value),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _mapping_items(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _mapping_payload(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return dict(_jsonish(value))


def _required_payload_text(value: object, field_name: str) -> str:
    text = _non_empty_text(value)
    if text is None:
        raise ValueError(
            f"Ontology runtime artifact-set resolution requires {field_name}."
        )
    return text


def _resolve_local_python_models_manifest_path(
    *,
    source_root: Path,
) -> Path | None:
    for candidate in _local_python_models_manifest_candidates(source_root=source_root):
        if candidate.is_file():
            return candidate.resolve()
    return None


def _local_python_models_manifest_candidates(
    *,
    source_root: Path,
) -> tuple[Path, ...]:
    return (
        source_root / ".aware" / "materializations" / "python.models.json",
        source_root
        / "python"
        / "orm_runtime"
        / ".aware"
        / "materializations"
        / "python.models.json",
        source_root / "python" / ".aware" / "materializations" / "python.models.json",
    )


def _default_local_python_models_manifest_path(
    *,
    source_root: Path,
) -> Path:
    return (
        source_root
        / "python"
        / "orm_runtime"
        / ".aware"
        / "materializations"
        / "python.models.json"
    ).resolve()


def _workspace_relative_path(
    path: Path,
    *,
    workspace_root: str | Path | None,
) -> str | None:
    if workspace_root is None:
        return None
    root = Path(workspace_root).expanduser().resolve()
    try:
        return path.expanduser().resolve().relative_to(root).as_posix()
    except ValueError:
        return None


def _path_text(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return Path(path).expanduser().resolve().as_posix()


def _db_schema_registry_sql_roots(path: Path) -> tuple[str, ...]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    entries = payload.get("entries") if isinstance(payload, Mapping) else None
    if not isinstance(entries, list):
        return ()
    sql_roots: list[str] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        root = _non_empty_text(entry.get("sql_root") or entry.get("sql_root_path"))
        if root is not None:
            sql_roots.append(root)
    return tuple(dict.fromkeys(sql_roots))


def _non_empty_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _jsonish(value: object) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _jsonish(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_jsonish(item) for item in value]
    if isinstance(value, list):
        return [_jsonish(item) for item in value]
    if isinstance(value, set):
        return [_jsonish(item) for item in sorted(value, key=str)]
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


__all__ = [
    "ONTOLOGY_RUNTIME_ARTIFACT_SET_ACTIVATION_POLICY",
    "ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY",
    "ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_ROLE",
    "ONTOLOGY_RUNTIME_ARTIFACT_SET_CONTRACT_VERSION",
    "ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY",
    "ONTOLOGY_RUNTIME_ARTIFACT_SET_PRODUCER_KEY",
    "ONTOLOGY_RUNTIME_ARTIFACT_SET_PRODUCER_PROVIDER_KEY",
    "ONTOLOGY_RUNTIME_ARTIFACT_SET_REQUIRED_FOR",
    "ONTOLOGY_RUNTIME_ARTIFACT_SET_SEMANTIC_OWNER",
    "ONTOLOGY_RUNTIME_BUNDLE_MANIFEST_ARTIFACT_ROLE",
    "ONTOLOGY_RUNTIME_BUNDLE_MANIFEST_CONTRACT_VERSION",
    "ONTOLOGY_RUNTIME_BUNDLE_MANIFEST_REQUIRED_FOR",
    "ONTOLOGY_RUNTIME_DB_SCHEMA_REGISTRY_ARTIFACT_ROLE",
    "ONTOLOGY_RUNTIME_DB_SCHEMA_REGISTRY_CONTRACT_VERSION",
    "ONTOLOGY_RUNTIME_DB_SCHEMA_REGISTRY_REQUIRED_FOR",
    "ONTOLOGY_RUNTIME_PYTHON_MODELS_MANIFEST_ARTIFACT_ROLE",
    "ONTOLOGY_RUNTIME_PYTHON_MODELS_MANIFEST_CONTRACT_VERSION",
    "ONTOLOGY_RUNTIME_PYTHON_MODELS_MANIFEST_REQUIRED_FOR",
    "SemanticOntologyPackageCatalogEntry",
    "build_ontology_runtime_artifact_set_ownership_receipt",
    "build_ontology_runtime_artifact_set_from_materialization_details",
    "find_ontology_runtime_artifact_ref",
    "ontology_runtime_artifact_ref_path",
    "resolve_local_ontology_runtime_artifact_set_payload",
    "resolve_semantic_ontology_package_manifest_closure",
    "resolve_ontology_runtime_artifact_set_payload",
    "semantic_ontology_package_catalog_entries_by_name",
    "semantic_ontology_package_names_for_projection_names",
]
