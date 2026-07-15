from __future__ import annotations

from uuid import UUID

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.namespace.layout_contract import (
    NAMESPACE_LAYOUT_DERIVATION_POLICY,
    NAMESPACE_LAYOUT_OVERLAY_RECOMPUTE_POLICY,
    NAMESPACE_LAYOUT_TYPED_OPERATION_POLICY,
    meta_ocg_namespace_layout_contract_payload,
    meta_ocg_namespace_layout_recompute_evidence,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)


def test_namespace_layout_contract_is_deterministic_recompute_policy() -> None:
    payload = meta_ocg_namespace_layout_contract_payload()

    assert payload["capability_key"] == "ocg.namespace_layout"
    assert payload["derivation_policy"] == NAMESPACE_LAYOUT_DERIVATION_POLICY
    assert payload["typed_operation_policy"] == NAMESPACE_LAYOUT_TYPED_OPERATION_POLICY
    assert payload["overlay_recompute_policy"] == (
        NAMESPACE_LAYOUT_OVERLAY_RECOMPUTE_POLICY
    )
    assert payload["source_code_provenance_required"] is False
    assert payload["persisted_semantic_object_required"] is False
    assert payload["required_topology_fields"] == (
        "ObjectConfigGraph.fqn_prefix",
        "ObjectConfigGraphNode.type",
        "ClassConfig.class_fqn",
        "EnumConfig.enum_fqn",
        "FunctionConfig.owner_key",
        "ClassConfigRelationship.class_config_id",
    )


def test_namespace_layout_evidence_uses_committed_ocg_topology_without_code_ids() -> (
    None
):
    graph = _demo_graph()

    evidence = meta_ocg_namespace_layout_recompute_evidence(
        object_config_graph=graph,
    )

    assert evidence["status"] == "namespace_layout_recompute_ready"
    assert evidence["source_code_provenance_required"] is False
    assert evidence["object_config_graph_fqn_prefix"] == "aware_demo"
    assert evidence["node_namespace_count"] == 2
    assert evidence["class_namespace_count"] == 1
    assert evidence["enum_namespace_count"] == 1
    assert evidence["function_namespace_count"] == 0
    assert str(evidence["namespace_layout_hash"]).startswith("sha256:")

    bundle_entries = evidence["namespace_bundle_entries"]
    assert isinstance(bundle_entries, dict)
    assert bundle_entries["class"] == (
        {
            "id": str(_CLASS_ID),
            "package": "aware_demo",
            "namespace": "default.home",
            "prefix": "aware_demo.default.home",
        },
    )
    assert bundle_entries["enum"] == (
        {
            "id": str(_ENUM_ID),
            "package": "aware_demo",
            "namespace": "enums",
            "prefix": "aware_demo.enums",
        },
    )


_GRAPH_ID = UUID("10000000-0000-5000-8000-000000000001")
_CLASS_NODE_ID = UUID("10000000-0000-5000-8000-000000000002")
_ENUM_NODE_ID = UUID("10000000-0000-5000-8000-000000000003")
_CLASS_ID = UUID("10000000-0000-5000-8000-000000000004")
_ENUM_ID = UUID("10000000-0000-5000-8000-000000000005")


def _demo_graph() -> ObjectConfigGraph:
    class_fqn = "aware_demo.default.home.Device"
    enum_fqn = "aware_demo.enums.DeviceKind"
    return ObjectConfigGraph(
        id=_GRAPH_ID,
        name="demo",
        hash="sha256:demo",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                id=_CLASS_NODE_ID,
                type=ObjectConfigGraphNodeType.class_,
                node_key=class_fqn,
                class_config=ClassConfig(
                    id=_CLASS_ID,
                    class_fqn=class_fqn,
                    name="Device",
                    is_base=True,
                ),
                object_config_graph_id=_GRAPH_ID,
            ),
            ObjectConfigGraphNode(
                id=_ENUM_NODE_ID,
                type=ObjectConfigGraphNodeType.enum,
                node_key=enum_fqn,
                enum_config=EnumConfig(
                    id=_ENUM_ID,
                    enum_fqn=enum_fqn,
                    name="DeviceKind",
                    object_config_graph_node_id=_ENUM_NODE_ID,
                ),
                object_config_graph_id=_GRAPH_ID,
            ),
        ],
    )
