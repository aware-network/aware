from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_graph import ProjectionExperienceGraph
from aware_experience_ontology.projection.projection_experience_graph_identity import ProjectionExperienceGraphIdentity
from aware_experience_ontology.projection.projection_experience_graph_identity_edge import (
    ProjectionExperienceGraphIdentityEdge,
)
from aware_experience_ontology.projection.projection_experience_node_identity_edge import (
    ProjectionExperienceNodeIdentityEdge,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Runtime
from aware_experience.stable_ids import stable_projection_experience_graph_id
from aware_experience.graph.resolver import (
    projection_experience_exists_via_lane,
    projection_experience_owns_node_identity_via_lane,
)

# Experience Ontology

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_identity(
    projection_experience_graph: ProjectionExperienceGraph,
    projection_experience_node_identity_id: UUID,
    key: str,
    is_root: bool = False,
) -> ProjectionExperienceGraphIdentity:
    """
    Attach one graph occurrence identity bound to one ProjectionExperienceNodeIdentity.
    """

    # --- AWARE: LOGIC START create_identity
    projection_experience_graph_id = projection_experience_graph.id
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("ProjectionExperienceGraph.create_identity requires non-empty key")

    node_identity_belongs_to_projection = await projection_experience_owns_node_identity_via_lane(
        projection_experience_node_identity_id=projection_experience_node_identity_id,
    )
    if not node_identity_belongs_to_projection:
        raise RuntimeError(
            "ProjectionExperienceGraph.create_identity requires known ProjectionExperienceNodeIdentity: "
            + f"projection_experience_node_identity_id={projection_experience_node_identity_id}"
        )

    key_norm_folded = normalized_key.casefold()
    for existing in projection_experience_graph.projection_experience_graph_identities:
        if (
            existing.projection_experience_node_identity_id == projection_experience_node_identity_id
            and (existing.key or "").strip() != normalized_key
        ):
            raise RuntimeError(
                "ProjectionExperienceGraph.create_identity requires one key per "
                + "ProjectionExperienceNodeIdentity within one graph"
            )
        if (existing.key or "").strip().casefold() == key_norm_folded and (
            existing.projection_experience_node_identity_id != projection_experience_node_identity_id
        ):
            raise RuntimeError(
                "ProjectionExperienceGraph.create_identity key collision within graph: " + f"key={normalized_key}"
            )

    if is_root:
        for existing in projection_experience_graph.projection_experience_graph_identities:
            if (
                existing.is_root
                and existing.projection_experience_node_identity_id != projection_experience_node_identity_id
            ):
                raise RuntimeError("ProjectionExperienceGraph.create_identity allows only one root identity per graph")

    created = await ProjectionExperienceGraphIdentity.build_via_projection_experience_graph(
        projection_experience_graph_id=projection_experience_graph_id,
        projection_experience_node_identity_id=projection_experience_node_identity_id,
        key=normalized_key,
        is_root=is_root,
    )

    for existing in projection_experience_graph.projection_experience_graph_identities:
        if existing.id == created.id:
            return existing
    projection_experience_graph.projection_experience_graph_identities.append(created)
    return created
    # --- AWARE: LOGIC END create_identity


async def create_node_identity_edge(
    projection_experience_graph: ProjectionExperienceGraph,
    parent_projection_experience_node_identity_id: UUID,
    child_projection_experience_node_identity_id: UUID,
    key: str | None = None,
) -> ProjectionExperienceNodeIdentityEdge:
    """
    Attach one semantic parent->child node identity edge contract.
    """

    # --- AWARE: LOGIC START create_node_identity_edge
    if parent_projection_experience_node_identity_id == child_projection_experience_node_identity_id:
        raise RuntimeError("ProjectionExperienceGraph.create_node_identity_edge requires distinct parent and child ids")

    projection_experience_graph_id = projection_experience_graph.id
    if not await projection_experience_owns_node_identity_via_lane(
        projection_experience_node_identity_id=parent_projection_experience_node_identity_id,
    ):
        raise RuntimeError(
            "ProjectionExperienceGraph.create_node_identity_edge requires known parent "
            + "ProjectionExperienceNodeIdentity: "
            + f"parent_projection_experience_node_identity_id={parent_projection_experience_node_identity_id}"
        )
    if not await projection_experience_owns_node_identity_via_lane(
        projection_experience_node_identity_id=child_projection_experience_node_identity_id,
    ):
        raise RuntimeError(
            "ProjectionExperienceGraph.create_node_identity_edge requires known child "
            + "ProjectionExperienceNodeIdentity: "
            + f"child_projection_experience_node_identity_id={child_projection_experience_node_identity_id}"
        )
    for existing in projection_experience_graph.projection_experience_node_identity_edges:
        if (
            existing.child_projection_experience_node_identity_id == child_projection_experience_node_identity_id
            and existing.parent_projection_experience_node_identity_id != parent_projection_experience_node_identity_id
        ):
            raise RuntimeError(
                "ProjectionExperienceGraph.create_node_identity_edge enforces a single parent per child "
                + "ProjectionExperienceNodeIdentity within one graph"
            )

    normalized_key = (key or "").strip() or None
    created = await ProjectionExperienceNodeIdentityEdge.build_via_projection_experience_graph(
        projection_experience_graph_id=projection_experience_graph_id,
        parent_projection_experience_node_identity_id=parent_projection_experience_node_identity_id,
        child_projection_experience_node_identity_id=child_projection_experience_node_identity_id,
        key=normalized_key,
    )
    for existing in projection_experience_graph.projection_experience_node_identity_edges:
        if existing.id == created.id:
            return existing
    projection_experience_graph.projection_experience_node_identity_edges.append(created)
    return created
    # --- AWARE: LOGIC END create_node_identity_edge


async def create_graph_identity_edge(
    projection_experience_graph: ProjectionExperienceGraph,
    parent_projection_experience_graph_identity_id: UUID,
    child_projection_experience_graph_identity_id: UUID,
    projection_experience_node_identity_edge_id: UUID,
    key: str | None = None,
) -> ProjectionExperienceGraphIdentityEdge:
    """
    Attach one graph occurrence edge bound to one semantic node identity edge contract.
    """

    # --- AWARE: LOGIC START create_graph_identity_edge
    if parent_projection_experience_graph_identity_id == child_projection_experience_graph_identity_id:
        raise RuntimeError(
            "ProjectionExperienceGraph.create_graph_identity_edge requires distinct parent and child ids"
        )

    projection_experience_graph_id = projection_experience_graph.id
    session = current_handler_session()
    parent_graph_identity = session.imap_get(
        ProjectionExperienceGraphIdentity,
        parent_projection_experience_graph_identity_id,
    )
    if parent_graph_identity is None:
        raise RuntimeError(
            "ProjectionExperienceGraph.create_graph_identity_edge requires known parent "
            + "ProjectionExperienceGraphIdentity: "
            + f"parent_projection_experience_graph_identity_id={parent_projection_experience_graph_identity_id}"
        )
    child_graph_identity = session.imap_get(
        ProjectionExperienceGraphIdentity,
        child_projection_experience_graph_identity_id,
    )
    if child_graph_identity is None:
        raise RuntimeError(
            "ProjectionExperienceGraph.create_graph_identity_edge requires known child "
            + "ProjectionExperienceGraphIdentity: "
            + f"child_projection_experience_graph_identity_id={child_projection_experience_graph_identity_id}"
        )
    if parent_graph_identity.projection_experience_graph_id != projection_experience_graph_id:
        raise RuntimeError(
            "ProjectionExperienceGraph.create_graph_identity_edge parent graph mismatch: "
            + f"parent.projection_experience_graph_id={parent_graph_identity.projection_experience_graph_id} "
            + f"graph={projection_experience_graph_id}"
        )
    if child_graph_identity.projection_experience_graph_id != projection_experience_graph_id:
        raise RuntimeError(
            "ProjectionExperienceGraph.create_graph_identity_edge child graph mismatch: "
            + f"child.projection_experience_graph_id={child_graph_identity.projection_experience_graph_id} "
            + f"graph={projection_experience_graph_id}"
        )

    node_identity_edge = session.imap_get(
        ProjectionExperienceNodeIdentityEdge,
        projection_experience_node_identity_edge_id,
    )
    if node_identity_edge is None:
        raise RuntimeError(
            "ProjectionExperienceGraph.create_graph_identity_edge requires known "
            + "ProjectionExperienceNodeIdentityEdge: "
            + f"projection_experience_node_identity_edge_id={projection_experience_node_identity_edge_id}"
        )
    if node_identity_edge.projection_experience_graph_id != projection_experience_graph_id:
        raise RuntimeError(
            "ProjectionExperienceGraph.create_graph_identity_edge node-identity-edge graph mismatch: "
            + f"node_identity_edge.projection_experience_graph_id={node_identity_edge.projection_experience_graph_id} "
            + f"graph={projection_experience_graph_id}"
        )
    if (
        parent_graph_identity.projection_experience_node_identity_id
        != node_identity_edge.parent_projection_experience_node_identity_id
        or child_graph_identity.projection_experience_node_identity_id
        != node_identity_edge.child_projection_experience_node_identity_id
    ):
        raise RuntimeError(
            "ProjectionExperienceGraph.create_graph_identity_edge requires graph identities to match "
            + "the semantic ProjectionExperienceNodeIdentityEdge endpoints"
        )

    for existing in projection_experience_graph.projection_experience_graph_identity_edges:
        if (
            existing.child_projection_experience_graph_identity_id == child_projection_experience_graph_identity_id
            and existing.parent_projection_experience_graph_identity_id
            != parent_projection_experience_graph_identity_id
        ):
            raise RuntimeError(
                "ProjectionExperienceGraph.create_graph_identity_edge enforces a single parent per child "
                + "ProjectionExperienceGraphIdentity within one graph"
            )

    normalized_key = (key or "").strip() or None
    created = await ProjectionExperienceGraphIdentityEdge.build_via_projection_experience_graph(
        projection_experience_graph_id=projection_experience_graph_id,
        parent_projection_experience_graph_identity_id=parent_projection_experience_graph_identity_id,
        child_projection_experience_graph_identity_id=child_projection_experience_graph_identity_id,
        projection_experience_node_identity_edge_id=projection_experience_node_identity_edge_id,
        key=normalized_key,
    )
    for existing in projection_experience_graph.projection_experience_graph_identity_edges:
        if existing.id == created.id:
            return existing
    projection_experience_graph.projection_experience_graph_identity_edges.append(created)
    return created
    # --- AWARE: LOGIC END create_graph_identity_edge


async def create_via_projection_experience(projection_experience_id: UUID, name: str) -> ProjectionExperienceGraph:
    """
    Create deterministic ProjectionExperienceGraph under one ProjectionExperience.
    """

    # --- AWARE: LOGIC START create_via_projection_experience
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ProjectionExperienceGraph.create_via_projection requires non-empty name")

    if not await projection_experience_exists_via_lane(projection_experience_id=projection_experience_id):
        raise RuntimeError(
            "ProjectionExperienceGraph.create_via_projection requires known ProjectionExperience: "
            + f"projection_experience_id={projection_experience_id}"
        )

    session = current_handler_session()
    projection_experience_graph_id = stable_projection_experience_graph_id(
        projection_experience_id=projection_experience_id,
        name=normalized_name,
    )
    existing = session.imap_get(ProjectionExperienceGraph, projection_experience_graph_id)
    if existing is not None:
        if existing.projection_experience_id != projection_experience_id or existing.name != normalized_name:
            raise RuntimeError(
                "ProjectionExperienceGraph.create_via_projection payload mismatch for existing graph: "
                + f"projection_experience_graph_id={projection_experience_graph_id}"
            )
        return existing

    return ProjectionExperienceGraph(
        id=projection_experience_graph_id,
        projection_experience_id=projection_experience_id,
        name=normalized_name,
    )
    # --- AWARE: LOGIC END create_via_projection_experience
