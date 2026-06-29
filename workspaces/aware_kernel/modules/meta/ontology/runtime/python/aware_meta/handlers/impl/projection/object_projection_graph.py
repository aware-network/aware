from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta Ontology
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipSideLoadingStrategy,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphAttributeRole,
    ObjectProjectionGraphEdgeInclude,
    ObjectProjectionGraphEdgeMultiplicity,
    ObjectProjectionGraphNodeSelection,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.projection.object_projection_graph import ObjectProjectionGraph
from aware_meta_ontology.graph.projection.object_projection_graph_constructor import ObjectProjectionGraphConstructor
from aware_meta_ontology.graph.projection.object_projection_graph_edge import ObjectProjectionGraphEdge
from aware_meta_ontology.graph.projection.object_projection_graph_node import ObjectProjectionGraphNode
from aware_meta_ontology.graph.projection.object_projection_graph_relationship import ObjectProjectionGraphRelationship

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.stable_ids import stable_object_projection_graph_id

# Meta Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_node(
    object_projection_graph: ObjectProjectionGraph,
    class_config_id: UUID,
    is_root: bool = False,
    required_for_validity: bool = False,
    selection: ObjectProjectionGraphNodeSelection = ObjectProjectionGraphNodeSelection.all,
    top_n: int | None = None,
    selector_condition_id: UUID | None = None,
    policy_refs: list[str] = [],
) -> ObjectProjectionGraphNode:
    """
    Create deterministic ObjectProjectionGraphNode under this ObjectProjectionGraph.
    """

    # --- AWARE: LOGIC START create_node
    created = await ObjectProjectionGraphNode.build_via_object_projection_graph(
        object_projection_graph_id=object_projection_graph.id,
        class_config_id=class_config_id,
        is_root=is_root,
        required_for_validity=required_for_validity,
        selection=selection,
        top_n=top_n,
        selector_condition_id=selector_condition_id,
        policy_refs=policy_refs,
    )
    for existing in object_projection_graph.object_projection_graph_nodes:
        if existing.id != created.id:
            continue
        if (
            existing.object_projection_graph_id != object_projection_graph.id
            or existing.class_config_id != class_config_id
            or existing.is_root != is_root
            or existing.required_for_validity != required_for_validity
            or existing.selection != selection
            or existing.top_n != top_n
            or existing.selector_condition_id != selector_condition_id
            or existing.policy_refs != policy_refs
        ):
            raise RuntimeError(
                "ObjectProjectionGraph.create_node payload mismatch for existing "
                f"ObjectProjectionGraphNode: object_projection_graph_node_id={created.id}"
            )
        return existing
    object_projection_graph.object_projection_graph_nodes.append(created)
    return created
    # --- AWARE: LOGIC END create_node


async def create_edge(
    object_projection_graph: ObjectProjectionGraph,
    class_config_relationship_id: UUID,
    include: ObjectProjectionGraphEdgeInclude = ObjectProjectionGraphEdgeInclude.required,
    multiplicity: ObjectProjectionGraphEdgeMultiplicity = ObjectProjectionGraphEdgeMultiplicity.many,
    traversal_direction: ClassConfigRelationshipDirection = ClassConfigRelationshipDirection.forward,
    depth_limit: int | None = None,
    attribute_role: ObjectProjectionGraphAttributeRole = ObjectProjectionGraphAttributeRole.reference,
    loading_override: ClassConfigRelationshipSideLoadingStrategy | None = None,
) -> ObjectProjectionGraphEdge:
    """
    Create deterministic ObjectProjectionGraphEdge under this ObjectProjectionGraph.
    """

    # --- AWARE: LOGIC START create_edge
    created = await ObjectProjectionGraphEdge.build_via_object_projection_graph(
        object_projection_graph_id=object_projection_graph.id,
        class_config_relationship_id=class_config_relationship_id,
        include=include,
        multiplicity=multiplicity,
        traversal_direction=traversal_direction,
        depth_limit=depth_limit,
        attribute_role=attribute_role,
        loading_override=loading_override,
    )
    for existing in object_projection_graph.object_projection_graph_edges:
        if existing.id != created.id:
            continue
        if (
            existing.object_projection_graph_id != object_projection_graph.id
            or existing.class_config_relationship_id != class_config_relationship_id
            or existing.include != include
            or existing.multiplicity != multiplicity
            or existing.traversal_direction != traversal_direction
            or existing.depth_limit != depth_limit
            or existing.attribute_role != attribute_role
            or existing.loading_override != loading_override
        ):
            raise RuntimeError(
                "ObjectProjectionGraph.create_edge payload mismatch for existing "
                f"ObjectProjectionGraphEdge: object_projection_graph_edge_id={created.id}"
            )
        return existing
    object_projection_graph.object_projection_graph_edges.append(created)
    return created
    # --- AWARE: LOGIC END create_edge


async def create_constructor(
    object_projection_graph: ObjectProjectionGraph, root_node_id: UUID, function_constructor_id: UUID
) -> ObjectProjectionGraphConstructor:
    """
    Create deterministic ObjectProjectionGraphConstructor under this ObjectProjectionGraph.
    """

    # --- AWARE: LOGIC START create_constructor
    created = await ObjectProjectionGraphConstructor.build_via_object_projection_graph(
        object_projection_graph_id=object_projection_graph.id,
        root_node_id=root_node_id,
        function_constructor_id=function_constructor_id,
    )
    for existing in object_projection_graph.object_projection_graph_constructors:
        if existing.id != created.id:
            continue
        if (
            existing.object_projection_graph_id != object_projection_graph.id
            or existing.root_node_id != root_node_id
            or existing.function_constructor_id != function_constructor_id
        ):
            raise RuntimeError(
                "ObjectProjectionGraph.create_constructor payload mismatch for existing "
                f"ObjectProjectionGraphConstructor: object_projection_graph_constructor_id={created.id}"
            )
        return existing
    object_projection_graph.object_projection_graph_constructors.append(created)
    return created
    # --- AWARE: LOGIC END create_constructor


async def create_relationship(
    object_projection_graph: ObjectProjectionGraph,
    target_object_projection_graph_id: UUID,
    class_config_relationship_id: UUID,
    source_object_projection_graph_node_id: UUID,
    target_object_projection_graph_node_id: UUID,
) -> ObjectProjectionGraphRelationship:
    """
    Create deterministic ObjectProjectionGraphRelationship under this ObjectProjectionGraph.
    """

    # --- AWARE: LOGIC START create_relationship
    created = await ObjectProjectionGraphRelationship.build_via_object_projection_graph(
        object_projection_graph_id=object_projection_graph.id,
        target_object_projection_graph_id=target_object_projection_graph_id,
        class_config_relationship_id=class_config_relationship_id,
        source_object_projection_graph_node_id=source_object_projection_graph_node_id,
        target_object_projection_graph_node_id=target_object_projection_graph_node_id,
    )
    for existing in object_projection_graph.object_projection_graph_relationships:
        if existing.id != created.id:
            continue
        if (
            existing.object_projection_graph_id != object_projection_graph.id
            or existing.target_object_projection_graph_id != target_object_projection_graph_id
            or existing.class_config_relationship_id != class_config_relationship_id
            or existing.source_object_projection_graph_node_id != source_object_projection_graph_node_id
            or existing.target_object_projection_graph_node_id != target_object_projection_graph_node_id
        ):
            raise RuntimeError(
                "ObjectProjectionGraph.create_relationship payload mismatch for existing "
                "ObjectProjectionGraphRelationship: "
                f"object_projection_graph_relationship_id={created.id}"
            )
        return existing
    object_projection_graph.object_projection_graph_relationships.append(created)
    return created
    # --- AWARE: LOGIC END create_relationship


async def create_object_instance_graph(
    object_projection_graph: ObjectProjectionGraph,
    key: str,
    root_class_config_id: UUID,
    root_source_object_id: UUID,
    name: str,
    description: str | None = None,
    hash: str = "",
) -> ObjectInstanceGraph:
    """
    Create deterministic ObjectInstanceGraph under this ObjectProjectionGraph.

    Contract:
    - Parent `object_projection_graph_id` is propagated by constructor lowering.
    - Child identity resolves from `(object_projection_graph_id via path, key)`.
    - Root ClassInstance is created eagerly at construction time; empty OIGs are not allowed.
    - `name` is mutable payload metadata; `hash` is snapshot metadata only.
    """

    # --- AWARE: LOGIC START create_object_instance_graph
    created = await ObjectInstanceGraph.build_via_object_projection_graph(
        object_projection_graph_id=object_projection_graph.id,
        key=key,
        root_class_config_id=root_class_config_id,
        root_source_object_id=root_source_object_id,
        name=name,
        description=description,
        hash=hash,
    )
    if all(existing.id != created.id for existing in object_projection_graph.object_instance_graphs):
        object_projection_graph.object_instance_graphs.append(created)
    return created
    # --- AWARE: LOGIC END create_object_instance_graph


async def build_via_object_config_graph(
    object_config_graph_id: UUID,
    name: str,
    projection_hash: str,
    language: CodeLanguage = CodeLanguage.aware,
    description: str | None = None,
    supports_virtual_build: bool = True,
) -> ObjectProjectionGraph:
    """
    Create deterministic ObjectProjectionGraph root for runtime proof composition.

    Contract:
    - Parent `object_config_graph_id` is propagated by constructor lowering.
    - Identity resolves from `(object_config_graph_id via path, name)`.
    - `projection_hash` is snapshot metadata and must not participate in stable identity.
    """

    # --- AWARE: LOGIC START build_via_object_config_graph
    object_projection_graph_id = stable_object_projection_graph_id(
        object_config_graph_id=object_config_graph_id,
        name=name,
    )
    session = current_handler_session()
    existing = session.imap_get(ObjectProjectionGraph, object_projection_graph_id)
    if existing is not None:
        if (
            existing.object_config_graph_id != object_config_graph_id
            or existing.name != name
            or existing.projection_hash != projection_hash
            or existing.language != language
            or (existing.description or None) != (description or None)
            or existing.supports_virtual_build != supports_virtual_build
        ):
            raise RuntimeError(
                "ObjectProjectionGraph.build_via_object_config_graph payload mismatch for existing "
                f"ObjectProjectionGraph: object_projection_graph_id={object_projection_graph_id}"
            )
        return existing

    return ObjectProjectionGraph(
        id=object_projection_graph_id,
        object_config_graph_id=object_config_graph_id,
        name=name,
        projection_hash=projection_hash,
        language=language,
        description=description,
        supports_virtual_build=supports_virtual_build,
    )
    # --- AWARE: LOGIC END build_via_object_config_graph
