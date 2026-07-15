from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from uuid import UUID

from aware_meta.graph.config.namespace.builder import (
    build_namespace_bundle_from_ocg_topology,
)
from aware_meta.graph.config.namespace.bundle import ObjectConfigGraphNamespaceBundle
from aware_meta.graph.config.namespace_index import build_namespace_index
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph


META_OCG_NAMESPACE_LAYOUT_RECOMPUTE_CONTRACT_VERSION = (
    "aware.meta.ocg-namespace-layout-recompute.v0"
)
META_OCG_NAMESPACE_LAYOUT_CAPABILITY_KEY = "ocg.namespace_layout"
NAMESPACE_LAYOUT_DERIVATION_POLICY = (
    "deterministic_recompute_from_committed_ocg_topology"
)
NAMESPACE_LAYOUT_TYPED_OPERATION_POLICY = "derived_recompute_not_persisted"
NAMESPACE_LAYOUT_OVERLAY_RECOMPUTE_POLICY = (
    "recompute_overlays_from_annotations_and_reserved_keyword_policies"
)


@dataclass(frozen=True, slots=True)
class MetaOcgNamespaceLayoutRecomputeContract:
    capability_key: str
    derivation_policy: str
    typed_operation_policy: str
    overlay_recompute_policy: str
    required_topology_fields: tuple[str, ...]
    derived_outputs: tuple[str, ...]
    source_code_provenance_required: bool
    persisted_semantic_object_required: bool
    contract_version: str = META_OCG_NAMESPACE_LAYOUT_RECOMPUTE_CONTRACT_VERSION

    def evidence_payload(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "capability_key": self.capability_key,
            "derivation_policy": self.derivation_policy,
            "typed_operation_policy": self.typed_operation_policy,
            "overlay_recompute_policy": self.overlay_recompute_policy,
            "required_topology_fields": self.required_topology_fields,
            "derived_outputs": self.derived_outputs,
            "source_code_provenance_required": self.source_code_provenance_required,
            "persisted_semantic_object_required": (
                self.persisted_semantic_object_required
            ),
        }


def meta_ocg_namespace_layout_recompute_contract() -> (
    MetaOcgNamespaceLayoutRecomputeContract
):
    return MetaOcgNamespaceLayoutRecomputeContract(
        capability_key=META_OCG_NAMESPACE_LAYOUT_CAPABILITY_KEY,
        derivation_policy=NAMESPACE_LAYOUT_DERIVATION_POLICY,
        typed_operation_policy=NAMESPACE_LAYOUT_TYPED_OPERATION_POLICY,
        overlay_recompute_policy=NAMESPACE_LAYOUT_OVERLAY_RECOMPUTE_POLICY,
        required_topology_fields=(
            "ObjectConfigGraph.fqn_prefix",
            "ObjectConfigGraphNode.type",
            "ClassConfig.class_fqn",
            "EnumConfig.enum_fqn",
            "FunctionConfig.owner_key",
            "ClassConfigRelationship.class_config_id",
        ),
        derived_outputs=(
            "ObjectConfigGraphNamespaceIndex.node_namespace_by_node_id",
            "ObjectConfigGraphNamespaceBundle.namespace_by_class_config_id",
            "ObjectConfigGraphNamespaceBundle.namespace_by_enum_config_id",
            "ObjectConfigGraphNamespaceBundle.namespace_by_function_config_id",
            "ObjectConfigGraphOverlay",
        ),
        source_code_provenance_required=False,
        persisted_semantic_object_required=False,
    )


def meta_ocg_namespace_layout_contract_payload() -> dict[str, object]:
    return meta_ocg_namespace_layout_recompute_contract().evidence_payload()


def meta_ocg_namespace_layout_recompute_evidence(
    *,
    object_config_graph: ObjectConfigGraph,
) -> dict[str, object]:
    namespace_index = build_namespace_index(object_config_graph)
    namespace_bundle = build_namespace_bundle_from_ocg_topology(
        ocg=object_config_graph,
    )
    bundle_entries = _namespace_bundle_entries(namespace_bundle)
    node_entries = _namespace_mapping_entries(namespace_index.node_namespace_by_node_id)
    return {
        **meta_ocg_namespace_layout_contract_payload(),
        "object_config_graph_id": str(object_config_graph.id),
        "object_config_graph_fqn_prefix": object_config_graph.fqn_prefix,
        "node_namespace_count": len(node_entries),
        "class_namespace_count": len(bundle_entries["class"]),
        "enum_namespace_count": len(bundle_entries["enum"]),
        "function_namespace_count": len(bundle_entries["function"]),
        "node_namespace_entries": node_entries,
        "namespace_bundle_entries": bundle_entries,
        "namespace_layout_hash": _namespace_layout_hash(
            node_entries=node_entries,
            bundle_entries=bundle_entries,
        ),
        "status": "namespace_layout_recompute_ready",
    }


def _namespace_bundle_entries(
    namespace_bundle: ObjectConfigGraphNamespaceBundle,
) -> dict[str, tuple[dict[str, str], ...]]:
    return {
        "class": _namespace_mapping_entries(
            namespace_bundle.namespace_by_class_config_id,
        ),
        "enum": _namespace_mapping_entries(
            namespace_bundle.namespace_by_enum_config_id,
        ),
        "function": _namespace_mapping_entries(
            namespace_bundle.namespace_by_function_config_id,
        ),
    }


def _namespace_mapping_entries(
    namespace_by_id: Mapping[UUID, object],
) -> tuple[dict[str, str], ...]:
    entries: list[dict[str, str]] = []
    for item_id, namespace in namespace_by_id.items():
        namespace_package = str(getattr(namespace, "package"))
        namespace_path = str(getattr(namespace, "namespace"))
        entries.append(
            {
                "id": str(item_id),
                "package": namespace_package,
                "namespace": namespace_path,
                "prefix": (
                    namespace_package
                    if not namespace_path
                    else f"{namespace_package}.{namespace_path}"
                ),
            }
        )
    return tuple(sorted(entries, key=lambda entry: entry["id"]))


def _namespace_layout_hash(
    *,
    node_entries: tuple[dict[str, str], ...],
    bundle_entries: dict[str, tuple[dict[str, str], ...]],
) -> str:
    payload = {
        "node_namespace_entries": node_entries,
        "namespace_bundle_entries": bundle_entries,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8",
    )
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


__all__ = [
    "META_OCG_NAMESPACE_LAYOUT_CAPABILITY_KEY",
    "META_OCG_NAMESPACE_LAYOUT_RECOMPUTE_CONTRACT_VERSION",
    "NAMESPACE_LAYOUT_DERIVATION_POLICY",
    "NAMESPACE_LAYOUT_OVERLAY_RECOMPUTE_POLICY",
    "NAMESPACE_LAYOUT_TYPED_OPERATION_POLICY",
    "MetaOcgNamespaceLayoutRecomputeContract",
    "meta_ocg_namespace_layout_contract_payload",
    "meta_ocg_namespace_layout_recompute_contract",
    "meta_ocg_namespace_layout_recompute_evidence",
]
