from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_binding import ObjectConfigGraphBinding
from aware_meta_ontology.graph.config.object_config_graph_node import ObjectConfigGraphNode
from aware_meta_ontology.graph.config.object_config_graph_relationship import ObjectConfigGraphRelationship
from aware_meta_ontology.graph.projection.object_projection_graph import ObjectProjectionGraph

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph_identity import (
    ObjectConfigGraphIdentity,
)

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# Meta
from aware_meta.graph.config.model_bootstrap import (
    get_object_config_graph_node_key,
)
from aware_meta.graph.config.stable_ids import (
    stable_object_config_graph_id,
    stable_object_config_graph_binding_id,
    stable_object_config_graph_node_id,
)

# --- AWARE: USER_IMPORTS END


async def build(
    name: str,
    hash: str,
    fqn_prefix: str,
    language: CodeLanguage = CodeLanguage.aware,
    object_config_graph_id: UUID | None = None,
    object_config_graph_identity_id: UUID | None = None,
    description: str | None = None,
    layout_hash: str | None = None,
) -> ObjectConfigGraph:
    """
    Create deterministic ObjectConfigGraph root for runtime proof composition.

    Contract:
    - Identity contract is keyed by `(fqn_prefix, language)`.
    - `object_config_graph_id` is optional compatibility input; when provided it must match
      compiler/runtime deterministic derivation for `(fqn_prefix, language)`.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    normalized_hash = (hash or "").strip()
    normalized_fqn_prefix = (fqn_prefix or "").strip()
    if not normalized_name:
        raise RuntimeError("ObjectConfigGraph.build requires non-empty name")
    if not normalized_hash:
        raise RuntimeError("ObjectConfigGraph.build requires non-empty hash")
    if not normalized_fqn_prefix:
        raise RuntimeError("ObjectConfigGraph.build requires non-empty fqn_prefix")
    language_value = str(getattr(language, "value", language))
    expected_graph_id = stable_object_config_graph_id(
        fqn_prefix=normalized_fqn_prefix,
        language=language_value,
    )
    if object_config_graph_id is not None and object_config_graph_id != expected_graph_id:
        raise RuntimeError(
            "ObjectConfigGraph.build object_config_graph_id does not match deterministic "
            "stable-id for (fqn_prefix, language): "
            f"provided={object_config_graph_id} expected={expected_graph_id} "
            f"fqn_prefix={normalized_fqn_prefix!r} language={language_value!r}"
        )
    resolved_graph_id = expected_graph_id

    session = current_handler_session()
    identity = None
    if object_config_graph_identity_id is not None:
        identity = session.imap_get(
            ObjectConfigGraphIdentity,
            object_config_graph_identity_id,
        )
        if identity is None:
            raise RuntimeError(
                "ObjectConfigGraph.build requires existing ObjectConfigGraphIdentity: "
                f"object_config_graph_identity_id={object_config_graph_identity_id}"
            )

    existing = session.imap_get(ObjectConfigGraph, resolved_graph_id)
    if existing is not None:
        hydrated_fields = set(existing.model_fields_set)
        required_fields = {"name", "hash", "fqn_prefix", "language"}
        if not required_fields.issubset(hydrated_fields):
            existing = None
    if existing is not None:
        if (
            (existing.name or "").strip() != normalized_name
            or (existing.hash or "").strip() != normalized_hash
            or (existing.fqn_prefix or "").strip() != normalized_fqn_prefix
            or existing.language != language
            or existing.object_config_graph_identity_id != object_config_graph_identity_id
        ):
            raise RuntimeError(
                "ObjectConfigGraph.build payload mismatch for existing graph: "
                f"object_config_graph_id={resolved_graph_id}"
            )
        return existing

    return ObjectConfigGraph(
        id=resolved_graph_id,
        name=normalized_name,
        hash=normalized_hash,
        fqn_prefix=normalized_fqn_prefix,
        language=language,
        object_config_graph_identity=identity,
        object_config_graph_identity_id=object_config_graph_identity_id,
        description=description,
        layout_hash=layout_hash,
    )
    # --- AWARE: LOGIC END build


async def create_node(
    object_config_graph: ObjectConfigGraph, type: ObjectConfigGraphNodeType, node_key: str
) -> ObjectConfigGraphNode:
    """
    Create one node under this ObjectConfigGraph.
    """

    # --- AWARE: LOGIC START create_node
    object_config_graph_id = object_config_graph.id
    if object_config_graph_id is None:
        raise RuntimeError("ObjectConfigGraph.create_node requires graph id")
    normalized_node_key = (node_key or "").strip()
    if not normalized_node_key:
        raise RuntimeError("ObjectConfigGraph.create_node requires non-empty node_key")
    object_config_graph_node_id = stable_object_config_graph_node_id(
        object_config_graph_id=object_config_graph_id,
        type=str(getattr(type, "value", type)),
        node_key=normalized_node_key,
    )
    for existing in object_config_graph.object_config_graph_nodes:
        if existing.id == object_config_graph_node_id:
            existing_node_key = get_object_config_graph_node_key(existing)
            if (
                existing.object_config_graph_id != object_config_graph_id
                or existing.type != type
                or (existing_node_key is not None and existing_node_key != normalized_node_key)
            ):
                raise RuntimeError(
                    "ObjectConfigGraph.create_node payload mismatch for existing node: "
                    f"object_config_graph_node_id={object_config_graph_node_id}"
                )
            return existing
    created = await ObjectConfigGraphNode.create_via_object_config_graph(
        object_config_graph_id=object_config_graph_id,
        type=type,
        node_key=normalized_node_key,
    )
    object_config_graph.object_config_graph_nodes.append(created)
    return created
    # --- AWARE: LOGIC END create_node


async def delete_node(
    object_config_graph: ObjectConfigGraph,
    type: ObjectConfigGraphNodeType,
    node_key: str,
    object_config_graph_node_id: UUID | None = None,
) -> None:
    """
    Remove one node from this ObjectConfigGraph.

    Contract:
    - The target node identity must match `(type, node_key)` inside this graph.
    - `object_config_graph_node_id` is optional identity evidence for delete deltas.
    - Delete mutates only this graph's `object_config_graph_nodes` membership.
    """

    # --- AWARE: LOGIC START delete_node
    object_config_graph_id = object_config_graph.id
    if object_config_graph_id is None:
        raise RuntimeError("ObjectConfigGraph.delete_node requires graph id")
    normalized_node_key = (node_key or "").strip()
    if not normalized_node_key:
        raise RuntimeError("ObjectConfigGraph.delete_node requires non-empty node_key")
    expected_node_id = stable_object_config_graph_node_id(
        object_config_graph_id=object_config_graph_id,
        type=str(getattr(type, "value", type)),
        node_key=normalized_node_key,
    )
    if (
        object_config_graph_node_id is not None
        and object_config_graph_node_id != expected_node_id
    ):
        raise RuntimeError(
            "ObjectConfigGraph.delete_node object_config_graph_node_id does not "
            "match deterministic stable-id for (graph, type, node_key): "
            f"provided={object_config_graph_node_id} expected={expected_node_id}"
        )

    retained_nodes: list[ObjectConfigGraphNode] = []
    removed = False
    for existing in object_config_graph.object_config_graph_nodes:
        existing_node_key = get_object_config_graph_node_key(existing)
        if existing.id != expected_node_id:
            retained_nodes.append(existing)
            continue
        if (
            existing.object_config_graph_id != object_config_graph_id
            or existing.type != type
            or (
                existing_node_key is not None
                and existing_node_key != normalized_node_key
            )
        ):
            raise RuntimeError(
                "ObjectConfigGraph.delete_node payload mismatch for existing node: "
                f"object_config_graph_node_id={existing.id}"
            )
        removed = True

    if not removed:
        return None
    object_config_graph.object_config_graph_nodes = retained_nodes
    return None
    # --- AWARE: LOGIC END delete_node


async def create_object_projection_graph(
    object_config_graph: ObjectConfigGraph,
    name: str,
    projection_hash: str,
    language: CodeLanguage = CodeLanguage.aware,
    description: str | None = None,
    supports_virtual_build: bool = True,
) -> ObjectProjectionGraph:
    """
    Create deterministic ObjectProjectionGraph under this ObjectConfigGraph.

    Contract:
    - Parent `object_config_graph_id` is propagated by constructor lowering.
    - Child identity resolves from `(object_config_graph_id via path, name)`.
    - `projection_hash` is snapshot metadata and must not participate in stable identity.
    """

    # --- AWARE: LOGIC START create_object_projection_graph
    object_config_graph_id = object_config_graph.id
    if object_config_graph_id is None:
        raise RuntimeError("ObjectConfigGraph.create_object_projection_graph requires graph id")

    created = await ObjectProjectionGraph.build_via_object_config_graph(
        object_config_graph_id=object_config_graph_id,
        name=name,
        projection_hash=projection_hash,
        language=language,
        description=description,
        supports_virtual_build=supports_virtual_build,
    )
    for existing in object_config_graph.object_projection_graphs:
        if existing.id != created.id:
            continue
        if (
            existing.object_config_graph_id != object_config_graph_id
            or existing.name != name
            or existing.projection_hash != projection_hash
            or existing.language != language
            or (existing.description or None) != (description or None)
            or existing.supports_virtual_build != supports_virtual_build
        ):
            raise RuntimeError(
                "ObjectConfigGraph.create_object_projection_graph payload mismatch for existing "
                f"ObjectProjectionGraph: object_projection_graph_id={created.id}"
            )
        return existing

    object_config_graph.object_projection_graphs.append(created)
    return created
    # --- AWARE: LOGIC END create_object_projection_graph


async def get_topology_description(object_config_graph: ObjectConfigGraph) -> str:
    """
    Returns a description of the ObjectConfigGraph topology.
    """

    # --- AWARE: LOGIC START get_topology_description
    return (
        "ObjectConfigGraph("
        f"name={(object_config_graph.name or '').strip()}, "
        f"nodes={len(object_config_graph.object_config_graph_nodes)}, "
        f"relationships={len(object_config_graph.object_config_graph_relationships)}"
        ")"
    )
    # --- AWARE: LOGIC END get_topology_description


async def create_object_config_graph_relationship(
    object_config_graph: ObjectConfigGraph, target_object_config_graph_id: UUID
) -> ObjectConfigGraphRelationship:
    """
    Create deterministic ObjectConfigGraphRelationship under this ObjectConfigGraph.
    """

    # --- AWARE: LOGIC START create_object_config_graph_relationship
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_object_config_graph_relationship


async def create_object_config_graph_binding(
    object_config_graph: ObjectConfigGraph, target_object_config_graph_id: UUID
) -> ObjectConfigGraphBinding:
    """
    Create deterministic ObjectConfigGraphBinding under this ObjectConfigGraph.

    Contract:
    - Source OCG scope is propagated through parent containment.
    - Child identity resolves from `(object_config_graph_id via path, target_object_config_graph_id)`.
    """

    # --- AWARE: LOGIC START create_object_config_graph_binding
    object_config_graph_id = object_config_graph.id
    if object_config_graph_id is None:
        raise RuntimeError("ObjectConfigGraph.create_object_config_graph_binding requires graph id")

    expected_binding_id = stable_object_config_graph_binding_id(
        object_config_graph_id=object_config_graph_id,
        target_object_config_graph_id=target_object_config_graph_id,
    )
    for existing in object_config_graph.object_config_graph_bindings:
        if existing.id != expected_binding_id:
            continue
        if (
            existing.object_config_graph_id != object_config_graph_id
            or existing.target_object_config_graph_id != target_object_config_graph_id
        ):
            raise RuntimeError(
                "ObjectConfigGraph.create_object_config_graph_binding payload mismatch for existing "
                f"ObjectConfigGraphBinding: object_config_graph_binding_id={expected_binding_id}"
            )
        return existing

    created = await ObjectConfigGraphBinding.build_via_object_config_graph(
        object_config_graph_id=object_config_graph_id,
        target_object_config_graph_id=target_object_config_graph_id,
    )
    object_config_graph.object_config_graph_bindings.append(created)
    return created
    # --- AWARE: LOGIC END create_object_config_graph_binding
