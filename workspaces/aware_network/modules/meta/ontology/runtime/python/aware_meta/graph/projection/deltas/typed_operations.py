from __future__ import annotations

from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)


OBJECT_PROJECTION_GRAPH_SUBJECT_KIND = "object_projection_graph"
OBJECT_PROJECTION_GRAPH_SUBJECT_TYPE = "aware_meta.ObjectProjectionGraph"
OBJECT_PROJECTION_GRAPH_NODE_SUBJECT_KIND = "object_projection_graph_node"
OBJECT_PROJECTION_GRAPH_NODE_SUBJECT_TYPE = "aware_meta.ObjectProjectionGraphNode"
OBJECT_PROJECTION_GRAPH_EDGE_SUBJECT_KIND = "object_projection_graph_edge"
OBJECT_PROJECTION_GRAPH_EDGE_SUBJECT_TYPE = "aware_meta.ObjectProjectionGraphEdge"
OBJECT_PROJECTION_GRAPH_CONSTRUCTOR_SUBJECT_KIND = "object_projection_graph_constructor"
OBJECT_PROJECTION_GRAPH_CONSTRUCTOR_SUBJECT_TYPE = (
    "aware_meta.ObjectProjectionGraphConstructor"
)
OBJECT_PROJECTION_GRAPH_RELATIONSHIP_SUBJECT_KIND = (
    "object_projection_graph_relationship"
)
OBJECT_PROJECTION_GRAPH_RELATIONSHIP_SUBJECT_TYPE = (
    "aware_meta.ObjectProjectionGraphRelationship"
)
OBJECT_PROJECTION_GRAPH_DECLARATION_SUBJECT_KIND = "object_projection_graph_declaration"
OBJECT_PROJECTION_GRAPH_DECLARATION_SUBJECT_TYPE = (
    "aware_meta.ObjectProjectionGraphDeclaration"
)
OBJECT_PROJECTION_GRAPH_BINDING_SUBJECT_KIND = "object_projection_graph_binding"
OBJECT_PROJECTION_GRAPH_BINDING_SUBJECT_TYPE = "aware_meta.ObjectProjectionGraphBinding"
OBJECT_INSTANCE_GRAPH_SUBJECT_KIND = "object_instance_graph"
OBJECT_INSTANCE_GRAPH_SUBJECT_TYPE = "aware_meta.ObjectInstanceGraph"
OBJECT_PROJECTION_GRAPH_BUILD_FUNCTION = (
    "ObjectProjectionGraph.build_via_object_config_graph"
)
OBJECT_PROJECTION_GRAPH_CREATE_NODE_FUNCTION = "ObjectProjectionGraph.create_node"
OBJECT_PROJECTION_GRAPH_CREATE_EDGE_FUNCTION = "ObjectProjectionGraph.create_edge"
OBJECT_PROJECTION_GRAPH_CREATE_CONSTRUCTOR_FUNCTION = (
    "ObjectProjectionGraph.create_constructor"
)
OBJECT_PROJECTION_GRAPH_CREATE_RELATIONSHIP_FUNCTION = (
    "ObjectProjectionGraph.create_relationship"
)
OBJECT_PROJECTION_GRAPH_CREATE_OBJECT_INSTANCE_GRAPH_FUNCTION = (
    "ObjectProjectionGraph.create_object_instance_graph"
)
OBJECT_CONFIG_GRAPH_CREATE_PROJECTION_DECLARATION_FUNCTION = (
    "ObjectConfigGraph.create_object_projection_graph_declaration"
)
OBJECT_PROJECTION_GRAPH_DECLARATION_CREATE_BINDING_FUNCTION = (
    "ObjectProjectionGraphDeclaration.create_binding"
)


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
            "required_ontology_function": (OBJECT_PROJECTION_GRAPH_BUILD_FUNCTION),
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
            "meta_ocg.object_projection_graph_node.create:" f"{semantic_key}"
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


def object_projection_graph_edge_create_typed_operation(
    *,
    semantic_key: str,
    object_projection_graph_semantic_key: str,
    object_projection_graph_id: str,
    object_projection_graph_edge_id: str,
    class_config_relationship_id: str,
    source_refs: tuple[str, ...],
    include: str = "required",
    multiplicity: str = "many",
    traversal_direction: str = "forward",
    depth_limit: int | None = None,
    attribute_role: str = "reference",
    loading_override: str | None = None,
) -> MetaProviderDeltaTypedOperation:
    return MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        operation_key=(
            "meta_ocg.object_projection_graph_edge.create:" f"{semantic_key}"
        ),
        operation_family="create",
        provider_operation_type="meta_ocg.object_projection_graph_edge.create",
        semantic_key=semantic_key,
        ontology_subject_kind=OBJECT_PROJECTION_GRAPH_EDGE_SUBJECT_KIND,
        semantic_subject_type=OBJECT_PROJECTION_GRAPH_EDGE_SUBJECT_TYPE,
        source_refs=source_refs,
        baseline={},
        current={
            "semantic_key": semantic_key,
            "object_kind": OBJECT_PROJECTION_GRAPH_EDGE_SUBJECT_KIND,
            "entity_id": object_projection_graph_edge_id,
            "object_projection_graph_edge_id": object_projection_graph_edge_id,
            "object_projection_graph_id": object_projection_graph_id,
            "object_projection_graph_semantic_key": (
                object_projection_graph_semantic_key
            ),
            "class_config_relationship_id": class_config_relationship_id,
            "include": include,
            "multiplicity": multiplicity,
            "traversal_direction": traversal_direction,
            "depth_limit": depth_limit,
            "attribute_role": attribute_role,
            "loading_override": loading_override,
            "required_ontology_function": (
                OBJECT_PROJECTION_GRAPH_CREATE_EDGE_FUNCTION
            ),
            "payload": {
                "entity_id": object_projection_graph_edge_id,
                "object_projection_graph_edge_id": object_projection_graph_edge_id,
                "object_projection_graph_id": object_projection_graph_id,
                "object_projection_graph_semantic_key": (
                    object_projection_graph_semantic_key
                ),
                "class_config_relationship_id": class_config_relationship_id,
                "include": include,
                "multiplicity": multiplicity,
                "traversal_direction": traversal_direction,
                "depth_limit": depth_limit,
                "attribute_role": attribute_role,
                "loading_override": loading_override,
            },
        },
        would_execute=True,
        would_persist=True,
    )


def object_projection_graph_constructor_create_typed_operation(
    *,
    semantic_key: str,
    object_projection_graph_semantic_key: str,
    object_projection_graph_id: str,
    object_projection_graph_constructor_id: str,
    root_node_id: str,
    function_constructor_id: str,
    source_refs: tuple[str, ...],
) -> MetaProviderDeltaTypedOperation:
    return MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        operation_key=(
            "meta_ocg.object_projection_graph_constructor.create:" f"{semantic_key}"
        ),
        operation_family="create",
        provider_operation_type=("meta_ocg.object_projection_graph_constructor.create"),
        semantic_key=semantic_key,
        ontology_subject_kind=OBJECT_PROJECTION_GRAPH_CONSTRUCTOR_SUBJECT_KIND,
        semantic_subject_type=OBJECT_PROJECTION_GRAPH_CONSTRUCTOR_SUBJECT_TYPE,
        source_refs=source_refs,
        baseline={},
        current={
            "semantic_key": semantic_key,
            "object_kind": OBJECT_PROJECTION_GRAPH_CONSTRUCTOR_SUBJECT_KIND,
            "entity_id": object_projection_graph_constructor_id,
            "object_projection_graph_constructor_id": (
                object_projection_graph_constructor_id
            ),
            "object_projection_graph_id": object_projection_graph_id,
            "object_projection_graph_semantic_key": (
                object_projection_graph_semantic_key
            ),
            "root_node_id": root_node_id,
            "function_constructor_id": function_constructor_id,
            "required_ontology_function": (
                OBJECT_PROJECTION_GRAPH_CREATE_CONSTRUCTOR_FUNCTION
            ),
            "payload": {
                "entity_id": object_projection_graph_constructor_id,
                "object_projection_graph_constructor_id": (
                    object_projection_graph_constructor_id
                ),
                "object_projection_graph_id": object_projection_graph_id,
                "object_projection_graph_semantic_key": (
                    object_projection_graph_semantic_key
                ),
                "root_node_id": root_node_id,
                "function_constructor_id": function_constructor_id,
            },
        },
        would_execute=True,
        would_persist=True,
    )


def object_projection_graph_relationship_create_typed_operation(
    *,
    semantic_key: str,
    object_projection_graph_semantic_key: str,
    object_projection_graph_id: str,
    object_projection_graph_relationship_id: str,
    target_object_projection_graph_id: str,
    class_config_relationship_id: str,
    source_object_projection_graph_node_id: str,
    target_object_projection_graph_node_id: str,
    source_refs: tuple[str, ...],
) -> MetaProviderDeltaTypedOperation:
    return MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        operation_key=(
            "meta_ocg.object_projection_graph_relationship.create:" f"{semantic_key}"
        ),
        operation_family="create",
        provider_operation_type=(
            "meta_ocg.object_projection_graph_relationship.create"
        ),
        semantic_key=semantic_key,
        ontology_subject_kind=OBJECT_PROJECTION_GRAPH_RELATIONSHIP_SUBJECT_KIND,
        semantic_subject_type=OBJECT_PROJECTION_GRAPH_RELATIONSHIP_SUBJECT_TYPE,
        source_refs=source_refs,
        baseline={},
        current={
            "semantic_key": semantic_key,
            "object_kind": OBJECT_PROJECTION_GRAPH_RELATIONSHIP_SUBJECT_KIND,
            "entity_id": object_projection_graph_relationship_id,
            "object_projection_graph_relationship_id": (
                object_projection_graph_relationship_id
            ),
            "object_projection_graph_id": object_projection_graph_id,
            "object_projection_graph_semantic_key": (
                object_projection_graph_semantic_key
            ),
            "target_object_projection_graph_id": target_object_projection_graph_id,
            "class_config_relationship_id": class_config_relationship_id,
            "source_object_projection_graph_node_id": (
                source_object_projection_graph_node_id
            ),
            "target_object_projection_graph_node_id": (
                target_object_projection_graph_node_id
            ),
            "required_ontology_function": (
                OBJECT_PROJECTION_GRAPH_CREATE_RELATIONSHIP_FUNCTION
            ),
            "payload": {
                "entity_id": object_projection_graph_relationship_id,
                "object_projection_graph_relationship_id": (
                    object_projection_graph_relationship_id
                ),
                "object_projection_graph_id": object_projection_graph_id,
                "object_projection_graph_semantic_key": (
                    object_projection_graph_semantic_key
                ),
                "target_object_projection_graph_id": (
                    target_object_projection_graph_id
                ),
                "class_config_relationship_id": class_config_relationship_id,
                "source_object_projection_graph_node_id": (
                    source_object_projection_graph_node_id
                ),
                "target_object_projection_graph_node_id": (
                    target_object_projection_graph_node_id
                ),
            },
        },
        would_execute=True,
        would_persist=True,
    )


def object_instance_graph_create_typed_operation(
    *,
    semantic_key: str,
    object_projection_graph_semantic_key: str,
    object_projection_graph_id: str,
    object_instance_graph_id: str,
    key: str,
    root_class_config_id: str,
    root_source_object_id: str,
    name: str,
    source_refs: tuple[str, ...],
    description: str | None = None,
    hash: str = "",
) -> MetaProviderDeltaTypedOperation:
    return MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        operation_key=("meta_ocg.object_instance_graph.create:" f"{semantic_key}"),
        operation_family="create",
        provider_operation_type="meta_ocg.object_instance_graph.create",
        semantic_key=semantic_key,
        ontology_subject_kind=OBJECT_INSTANCE_GRAPH_SUBJECT_KIND,
        semantic_subject_type=OBJECT_INSTANCE_GRAPH_SUBJECT_TYPE,
        source_refs=source_refs,
        baseline={},
        current={
            "semantic_key": semantic_key,
            "object_kind": OBJECT_INSTANCE_GRAPH_SUBJECT_KIND,
            "entity_id": object_instance_graph_id,
            "object_instance_graph_id": object_instance_graph_id,
            "object_projection_graph_id": object_projection_graph_id,
            "object_projection_graph_semantic_key": (
                object_projection_graph_semantic_key
            ),
            "key": key,
            "root_class_config_id": root_class_config_id,
            "root_source_object_id": root_source_object_id,
            "name": name,
            "description": description,
            "hash": hash,
            "required_ontology_function": (
                OBJECT_PROJECTION_GRAPH_CREATE_OBJECT_INSTANCE_GRAPH_FUNCTION
            ),
            "payload": {
                "entity_id": object_instance_graph_id,
                "object_instance_graph_id": object_instance_graph_id,
                "object_projection_graph_id": object_projection_graph_id,
                "object_projection_graph_semantic_key": (
                    object_projection_graph_semantic_key
                ),
                "key": key,
                "root_class_config_id": root_class_config_id,
                "root_source_object_id": root_source_object_id,
                "name": name,
                "description": description,
                "hash": hash,
            },
        },
        would_execute=True,
        would_persist=True,
    )


def object_projection_graph_declaration_create_typed_operation(
    *,
    semantic_key: str,
    graph_semantic_key: str,
    object_config_graph_id: str,
    object_projection_graph_declaration_id: str,
    key: str,
    projection_name: str,
    source_refs: tuple[str, ...],
    label: str | None = None,
    description: str | None = None,
    is_branchable: bool = False,
) -> MetaProviderDeltaTypedOperation:
    return MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        operation_key=(
            "meta_ocg.object_projection_graph_declaration.create:" f"{semantic_key}"
        ),
        operation_family="create",
        provider_operation_type=("meta_ocg.object_projection_graph_declaration.create"),
        semantic_key=semantic_key,
        ontology_subject_kind=OBJECT_PROJECTION_GRAPH_DECLARATION_SUBJECT_KIND,
        semantic_subject_type=OBJECT_PROJECTION_GRAPH_DECLARATION_SUBJECT_TYPE,
        source_refs=source_refs,
        baseline={},
        current={
            "semantic_key": semantic_key,
            "object_kind": OBJECT_PROJECTION_GRAPH_DECLARATION_SUBJECT_KIND,
            "entity_id": object_projection_graph_declaration_id,
            "object_projection_graph_declaration_id": (
                object_projection_graph_declaration_id
            ),
            "object_config_graph_id": object_config_graph_id,
            "graph_semantic_key": graph_semantic_key,
            "key": key,
            "projection_name": projection_name,
            "label": label,
            "description": description,
            "is_branchable": is_branchable,
            "required_ontology_function": (
                OBJECT_CONFIG_GRAPH_CREATE_PROJECTION_DECLARATION_FUNCTION
            ),
            "payload": {
                "entity_id": object_projection_graph_declaration_id,
                "object_projection_graph_declaration_id": (
                    object_projection_graph_declaration_id
                ),
                "object_config_graph_id": object_config_graph_id,
                "graph_semantic_key": graph_semantic_key,
                "key": key,
                "projection_name": projection_name,
                "label": label,
                "description": description,
                "is_branchable": is_branchable,
            },
        },
        would_execute=True,
        would_persist=True,
    )


def object_projection_graph_binding_create_typed_operation(
    *,
    semantic_key: str,
    object_projection_graph_declaration_semantic_key: str,
    object_projection_graph_declaration_id: str,
    object_projection_graph_binding_id: str,
    fqn_prefix: str,
    namespace: str,
    class_name: str,
    source_refs: tuple[str, ...],
    attribute_name: str | None = None,
    target_projection_name: str | None = None,
    side: str | None = None,
) -> MetaProviderDeltaTypedOperation:
    return MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        operation_key=(
            "meta_ocg.object_projection_graph_binding.create:" f"{semantic_key}"
        ),
        operation_family="create",
        provider_operation_type="meta_ocg.object_projection_graph_binding.create",
        semantic_key=semantic_key,
        ontology_subject_kind=OBJECT_PROJECTION_GRAPH_BINDING_SUBJECT_KIND,
        semantic_subject_type=OBJECT_PROJECTION_GRAPH_BINDING_SUBJECT_TYPE,
        source_refs=source_refs,
        baseline={},
        current={
            "semantic_key": semantic_key,
            "object_kind": OBJECT_PROJECTION_GRAPH_BINDING_SUBJECT_KIND,
            "entity_id": object_projection_graph_binding_id,
            "object_projection_graph_binding_id": object_projection_graph_binding_id,
            "object_projection_graph_declaration_id": (
                object_projection_graph_declaration_id
            ),
            "object_projection_graph_declaration_semantic_key": (
                object_projection_graph_declaration_semantic_key
            ),
            "fqn_prefix": fqn_prefix,
            "namespace": namespace,
            "class_name": class_name,
            "attribute_name": attribute_name,
            "target_projection_name": target_projection_name,
            "side": side,
            "required_ontology_function": (
                OBJECT_PROJECTION_GRAPH_DECLARATION_CREATE_BINDING_FUNCTION
            ),
            "payload": {
                "entity_id": object_projection_graph_binding_id,
                "object_projection_graph_binding_id": object_projection_graph_binding_id,
                "object_projection_graph_declaration_id": (
                    object_projection_graph_declaration_id
                ),
                "object_projection_graph_declaration_semantic_key": (
                    object_projection_graph_declaration_semantic_key
                ),
                "fqn_prefix": fqn_prefix,
                "namespace": namespace,
                "class_name": class_name,
                "attribute_name": attribute_name,
                "target_projection_name": target_projection_name,
                "side": side,
            },
        },
        would_execute=True,
        would_persist=True,
    )


__all__ = [
    "OBJECT_INSTANCE_GRAPH_SUBJECT_KIND",
    "OBJECT_INSTANCE_GRAPH_SUBJECT_TYPE",
    "OBJECT_CONFIG_GRAPH_CREATE_PROJECTION_DECLARATION_FUNCTION",
    "OBJECT_PROJECTION_GRAPH_BINDING_SUBJECT_KIND",
    "OBJECT_PROJECTION_GRAPH_BINDING_SUBJECT_TYPE",
    "OBJECT_PROJECTION_GRAPH_BUILD_FUNCTION",
    "OBJECT_PROJECTION_GRAPH_CONSTRUCTOR_SUBJECT_KIND",
    "OBJECT_PROJECTION_GRAPH_CONSTRUCTOR_SUBJECT_TYPE",
    "OBJECT_PROJECTION_GRAPH_CREATE_OBJECT_INSTANCE_GRAPH_FUNCTION",
    "OBJECT_PROJECTION_GRAPH_CREATE_CONSTRUCTOR_FUNCTION",
    "OBJECT_PROJECTION_GRAPH_CREATE_EDGE_FUNCTION",
    "OBJECT_PROJECTION_GRAPH_CREATE_NODE_FUNCTION",
    "OBJECT_PROJECTION_GRAPH_CREATE_RELATIONSHIP_FUNCTION",
    "OBJECT_PROJECTION_GRAPH_DECLARATION_CREATE_BINDING_FUNCTION",
    "OBJECT_PROJECTION_GRAPH_DECLARATION_SUBJECT_KIND",
    "OBJECT_PROJECTION_GRAPH_DECLARATION_SUBJECT_TYPE",
    "OBJECT_PROJECTION_GRAPH_EDGE_SUBJECT_KIND",
    "OBJECT_PROJECTION_GRAPH_EDGE_SUBJECT_TYPE",
    "OBJECT_PROJECTION_GRAPH_NODE_SUBJECT_KIND",
    "OBJECT_PROJECTION_GRAPH_NODE_SUBJECT_TYPE",
    "OBJECT_PROJECTION_GRAPH_RELATIONSHIP_SUBJECT_KIND",
    "OBJECT_PROJECTION_GRAPH_RELATIONSHIP_SUBJECT_TYPE",
    "OBJECT_PROJECTION_GRAPH_SUBJECT_KIND",
    "OBJECT_PROJECTION_GRAPH_SUBJECT_TYPE",
    "object_instance_graph_create_typed_operation",
    "object_projection_graph_binding_create_typed_operation",
    "object_projection_graph_constructor_create_typed_operation",
    "object_projection_graph_create_typed_operation",
    "object_projection_graph_declaration_create_typed_operation",
    "object_projection_graph_edge_create_typed_operation",
    "object_projection_graph_node_create_typed_operation",
    "object_projection_graph_relationship_create_typed_operation",
]
