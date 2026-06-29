from __future__ import annotations

from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)


OBJECT_PROJECTION_GRAPH_SUBJECT_KIND = "object_projection_graph"
OBJECT_PROJECTION_GRAPH_SUBJECT_TYPE = "aware_meta.ObjectProjectionGraph"
OBJECT_PROJECTION_GRAPH_NODE_SUBJECT_KIND = "object_projection_graph_node"
OBJECT_PROJECTION_GRAPH_NODE_SUBJECT_TYPE = (
    "aware_meta.ObjectProjectionGraphNode"
)
OBJECT_PROJECTION_GRAPH_BUILD_FUNCTION = (
    "ObjectProjectionGraph.build_via_object_config_graph"
)
OBJECT_PROJECTION_GRAPH_CREATE_NODE_FUNCTION = "ObjectProjectionGraph.create_node"


def object_projection_graph_create_typed_operation(
    *,
    semantic_key: str,
    graph_semantic_key: str,
    object_config_graph_id: str,
    object_projection_graph_id: str,
    name: str,
    projection_hash: str,
    source_refs: tuple[str, ...],
    language: str = "aware",
    description: str | None = None,
    supports_virtual_build: bool = True,
) -> MetaProviderDeltaTypedOperation:
    return MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        operation_key=f"meta_ocg.object_projection_graph.create:{semantic_key}",
        operation_family="create",
        provider_operation_type="meta_ocg.object_projection_graph.create",
        semantic_key=semantic_key,
        ontology_subject_kind=OBJECT_PROJECTION_GRAPH_SUBJECT_KIND,
        semantic_subject_type=OBJECT_PROJECTION_GRAPH_SUBJECT_TYPE,
        source_refs=source_refs,
        baseline={},
        current={
            "semantic_key": semantic_key,
            "object_kind": OBJECT_PROJECTION_GRAPH_SUBJECT_KIND,
            "entity_id": object_projection_graph_id,
            "object_projection_graph_id": object_projection_graph_id,
            "object_config_graph_id": object_config_graph_id,
            "graph_semantic_key": graph_semantic_key,
            "name": name,
            "projection_hash": projection_hash,
            "language": language,
            "description": description,
            "supports_virtual_build": supports_virtual_build,
            "required_ontology_function": (
                OBJECT_PROJECTION_GRAPH_BUILD_FUNCTION
            ),
            "payload": {
                "entity_id": object_projection_graph_id,
                "object_projection_graph_id": object_projection_graph_id,
                "object_config_graph_id": object_config_graph_id,
                "graph_semantic_key": graph_semantic_key,
                "name": name,
                "projection_hash": projection_hash,
                "language": language,
                "description": description,
                "supports_virtual_build": supports_virtual_build,
            },
        },
        would_execute=True,
        would_persist=True,
    )


def object_projection_graph_node_create_typed_operation(
    *,
    semantic_key: str,
    object_projection_graph_semantic_key: str,
    object_projection_graph_id: str,
    object_projection_graph_node_id: str,
    class_config_id: str,
    source_refs: tuple[str, ...],
    is_root: bool = False,
    required_for_validity: bool = False,
    selection: str = "all",
    top_n: int | None = None,
    selector_condition_id: str | None = None,
    policy_refs: tuple[str, ...] = (),
) -> MetaProviderDeltaTypedOperation:
    return MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        operation_key=(
            "meta_ocg.object_projection_graph_node.create:"
            f"{semantic_key}"
        ),
        operation_family="create",
        provider_operation_type="meta_ocg.object_projection_graph_node.create",
        semantic_key=semantic_key,
        ontology_subject_kind=OBJECT_PROJECTION_GRAPH_NODE_SUBJECT_KIND,
        semantic_subject_type=OBJECT_PROJECTION_GRAPH_NODE_SUBJECT_TYPE,
        source_refs=source_refs,
        baseline={},
        current={
            "semantic_key": semantic_key,
            "object_kind": OBJECT_PROJECTION_GRAPH_NODE_SUBJECT_KIND,
            "entity_id": object_projection_graph_node_id,
            "object_projection_graph_node_id": object_projection_graph_node_id,
            "object_projection_graph_id": object_projection_graph_id,
            "object_projection_graph_semantic_key": (
                object_projection_graph_semantic_key
            ),
            "class_config_id": class_config_id,
            "is_root": is_root,
            "required_for_validity": required_for_validity,
            "selection": selection,
            "top_n": top_n,
            "selector_condition_id": selector_condition_id,
            "policy_refs": policy_refs,
            "required_ontology_function": (
                OBJECT_PROJECTION_GRAPH_CREATE_NODE_FUNCTION
            ),
            "payload": {
                "entity_id": object_projection_graph_node_id,
                "object_projection_graph_node_id": object_projection_graph_node_id,
                "object_projection_graph_id": object_projection_graph_id,
                "object_projection_graph_semantic_key": (
                    object_projection_graph_semantic_key
                ),
                "class_config_id": class_config_id,
                "is_root": is_root,
                "required_for_validity": required_for_validity,
                "selection": selection,
                "top_n": top_n,
                "selector_condition_id": selector_condition_id,
                "policy_refs": policy_refs,
            },
        },
        would_execute=True,
        would_persist=True,
    )


__all__ = [
    "OBJECT_PROJECTION_GRAPH_BUILD_FUNCTION",
    "OBJECT_PROJECTION_GRAPH_CREATE_NODE_FUNCTION",
    "OBJECT_PROJECTION_GRAPH_NODE_SUBJECT_KIND",
    "OBJECT_PROJECTION_GRAPH_NODE_SUBJECT_TYPE",
    "OBJECT_PROJECTION_GRAPH_SUBJECT_KIND",
    "OBJECT_PROJECTION_GRAPH_SUBJECT_TYPE",
    "object_projection_graph_create_typed_operation",
    "object_projection_graph_node_create_typed_operation",
]
