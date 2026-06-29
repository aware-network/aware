from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from uuid import UUID

from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta.graph.config.namespace.membership import (
    object_config_graph_payload_has_exported_namespace_evidence,
)


OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_VERSION = 9
OBJECT_CONFIG_GRAPH_SOURCE_TO_RUNTIME_LOWERING_SIGNATURE = (
    "aware-meta-source-to-ocg-lowering-v6:function-body-source-section-sidecar:"
    "function-impl-body-invocations:edge-path-constructor-invocations:"
    "edge-path-runtime-constructor-surface"
)
OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS = (
    "meta_graph_context_package_graphs"
)
OBJECT_CONFIG_GRAPH_PACKAGE_CONTEXT_GRAPHS_DERIVATION_SIGNATURE = (
    "aware-meta-context-package-graphs-runtime-derivation-v2"
)
OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_SOURCE_GRAPH = (
    "meta_graph_context_source_graph"
)
OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_MATERIALIZED_PACKAGE = (
    "object_config_graph_package_leaf"
)


def source_text_manifest_hash(
    *,
    source_text_by_relative_path: Mapping[str, str],
) -> str:
    hasher = hashlib.sha256()
    hasher.update(b"aware-meta-package-source-manifest-v1\n")
    for relative_path, content_text in sorted(source_text_by_relative_path.items()):
        encoded_path = relative_path.encode("utf-8")
        encoded_text = content_text.encode("utf-8")
        hasher.update(str(len(encoded_path)).encode("ascii"))
        hasher.update(b":")
        hasher.update(encoded_path)
        hasher.update(b"\n")
        hasher.update(str(len(encoded_text)).encode("ascii"))
        hasher.update(b":")
        hasher.update(encoded_text)
        hasher.update(b"\n")
    return hasher.hexdigest()


def external_graph_signature(
    *,
    external_graphs: tuple[ObjectConfigGraph, ...],
) -> str:
    hasher = hashlib.sha256()
    hasher.update(b"aware-meta-package-external-graphs-v1\n")
    for graph in sorted(external_graphs, key=lambda item: str(item.id)):
        hasher.update(str(graph.id).encode("ascii"))
        hasher.update(b":")
        hasher.update(str(graph.hash or "").encode("utf-8"))
        hasher.update(b"\n")
    return hasher.hexdigest()


def object_config_graph_package_reuse_cache_path(
    *,
    aware_root: Path,
    branch_id: UUID,
    object_config_graph_package_id: UUID,
) -> Path:
    return (
        aware_root
        / ".aware"
        / "meta"
        / "object_config_graph_package_reuse"
        / str(branch_id)
        / f"{object_config_graph_package_id}.json"
    )


def object_config_graph_package_context_reuse_cache_path(
    *,
    aware_root: Path,
    branch_id: UUID,
    object_config_graph_package_id: UUID,
) -> Path:
    base_path = object_config_graph_package_reuse_cache_path(
        aware_root=aware_root,
        branch_id=branch_id,
        object_config_graph_package_id=object_config_graph_package_id,
    )
    return base_path.with_name(f"{base_path.stem}.runtime_context{base_path.suffix}")


def read_object_config_graph_package_reuse_cache_payload(
    *,
    aware_root: Path,
    branch_id: UUID,
    object_config_graph_package_id: UUID,
) -> dict[str, object] | None:
    path = object_config_graph_package_reuse_cache_path(
        aware_root=aware_root,
        branch_id=branch_id,
        object_config_graph_package_id=object_config_graph_package_id,
    )
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return {str(key): value for key, value in payload.items()}


def read_object_config_graph_package_context_reuse_cache_payload(
    *,
    aware_root: Path,
    branch_id: UUID,
    object_config_graph_package_id: UUID,
) -> dict[str, object] | None:
    path = object_config_graph_package_context_reuse_cache_path(
        aware_root=aware_root,
        branch_id=branch_id,
        object_config_graph_package_id=object_config_graph_package_id,
    )
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return {str(key): value for key, value in payload.items()}


def write_object_config_graph_package_reuse_cache_payload(
    *,
    aware_root: Path,
    branch_id: UUID,
    object_config_graph_package_id: UUID,
    payload: Mapping[str, object],
) -> None:
    path = object_config_graph_package_reuse_cache_path(
        aware_root=aware_root,
        branch_id=branch_id,
        object_config_graph_package_id=object_config_graph_package_id,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(dict(payload), separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )
    tmp.replace(path)


def write_object_config_graph_package_context_reuse_cache_payload(
    *,
    aware_root: Path,
    branch_id: UUID,
    object_config_graph_package_id: UUID,
    payload: Mapping[str, object],
) -> None:
    path = object_config_graph_package_context_reuse_cache_path(
        aware_root=aware_root,
        branch_id=branch_id,
        object_config_graph_package_id=object_config_graph_package_id,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(dict(payload), separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )
    tmp.replace(path)


def object_config_graph_payload_has_materialized_body(
    payload: Mapping[str, object],
) -> bool:
    for key in (
        "object_config_graph_nodes",
        "object_config_graph_relationships",
        "object_projection_graphs",
        "domains",
    ):
        value = payload.get(key)
        if isinstance(value, list) and value:
            return True
    return False


def object_config_graph_payload_has_namespace_evidence(
    payload: Mapping[str, object],
) -> bool:
    return object_config_graph_payload_has_exported_namespace_evidence(payload)


__all__ = [
    "OBJECT_CONFIG_GRAPH_PACKAGE_CONTEXT_GRAPHS_DERIVATION_SIGNATURE",
    "OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS",
    "OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_SOURCE_GRAPH",
    "OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_MATERIALIZED_PACKAGE",
    "OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_VERSION",
    "OBJECT_CONFIG_GRAPH_SOURCE_TO_RUNTIME_LOWERING_SIGNATURE",
    "external_graph_signature",
    "object_config_graph_package_context_reuse_cache_path",
    "object_config_graph_package_reuse_cache_path",
    "object_config_graph_payload_has_namespace_evidence",
    "object_config_graph_payload_has_materialized_body",
    "read_object_config_graph_package_context_reuse_cache_payload",
    "read_object_config_graph_package_reuse_cache_payload",
    "source_text_manifest_hash",
    "write_object_config_graph_package_context_reuse_cache_payload",
    "write_object_config_graph_package_reuse_cache_payload",
]
