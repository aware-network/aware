from __future__ import annotations

from aware_meta.graph.config.binding_mirror_contract import (
    BINDING_SEMANTIC_POLICY,
    META_OCG_BINDING_MIRROR_CAPABILITY_KEY,
    META_OCG_BINDING_MIRROR_CONTRACT_VERSION,
    META_OCG_BINDING_SURFACE_KEY,
    META_OCG_MIRROR_SURFACE_KEY,
    MIRROR_SEMANTIC_POLICY,
    SURFACE_STATUS_BLOCKED,
    SURFACE_STATUS_READY,
    meta_ocg_binding_mirror_contract_payload,
)


def test_binding_mirror_contract_splits_binding_from_mirror_rewrite() -> None:
    payload = meta_ocg_binding_mirror_contract_payload()
    binding_surface = payload["binding_surface"]
    mirror_surface = payload["mirror_surface"]

    assert payload["contract_version"] == META_OCG_BINDING_MIRROR_CONTRACT_VERSION
    assert payload["capability_key"] == META_OCG_BINDING_MIRROR_CAPABILITY_KEY
    assert payload["status"] == "partial"
    assert payload["code_owns_meta_mutation"] is False

    assert isinstance(binding_surface, dict)
    assert binding_surface["surface_key"] == META_OCG_BINDING_SURFACE_KEY
    assert binding_surface["semantic_policy"] == BINDING_SEMANTIC_POLICY
    assert binding_surface["status"] == SURFACE_STATUS_READY
    assert binding_surface["blockers"] == ()
    assert binding_surface["required_ontology_functions"] == (
        "ObjectConfigGraph.create_object_config_graph_binding",
        "ObjectConfigGraphBinding.create_class",
        "ObjectProjectionGraphNode.create_key",
        "ObjectProjectionGraphNodeKey.build_via_object_projection_graph_node",
    )

    assert isinstance(mirror_surface, dict)
    assert mirror_surface["surface_key"] == META_OCG_MIRROR_SURFACE_KEY
    assert mirror_surface["semantic_policy"] == MIRROR_SEMANTIC_POLICY
    assert mirror_surface["status"] == SURFACE_STATUS_BLOCKED
    assert mirror_surface["blockers"] == ("mirror_rewrite_typed_operations_missing",)
    assert payload["blockers"] == ("mirror_rewrite_typed_operations_missing",)
