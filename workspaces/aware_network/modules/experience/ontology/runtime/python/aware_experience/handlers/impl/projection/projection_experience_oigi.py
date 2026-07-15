from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_node_class_identity import (
    ProjectionExperienceNodeClassIdentity,
)
from aware_experience_ontology.projection.projection_experience_node_class_identity_edge import (
    ProjectionExperienceNodeClassIdentityEdge,
)
from aware_experience_ontology.projection.projection_experience_oigi import ProjectionExperienceOIGI

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Runtime
from aware_experience.stable_ids import stable_projection_experience_oigi_id
from aware_experience.graph.resolver import (
    object_instance_graph_identity_owns_class_instance_identity_via_lane,
    object_instance_graph_identity_owns_class_instance_relationship_identity_via_lane,
    projection_experience_owns_node_identity_via_lane,
)

# Meta Ontology
from aware_meta_ontology.graph.instance.object_instance_graph_identity import (
    ObjectInstanceGraphIdentity,
)

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_node_class_identity(
    projection_experience_oigi: ProjectionExperienceOIGI,
    projection_experience_node_identity_id: UUID,
    class_instance_identity_id: UUID,
    key: str,
) -> ProjectionExperienceNodeClassIdentity:
    """
    Attach one semantic ProjectionExperienceNodeIdentity -> ClassInstanceIdentity anchor.
    """

    # --- AWARE: LOGIC START create_node_class_identity
    projection_experience_oigi_id = projection_experience_oigi.id
    object_instance_graph_identity_id = projection_experience_oigi.object_instance_graph_identity_id

    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("ProjectionExperienceOIGI.create_node_class_identity requires non-empty key")

    session = current_handler_session()
    if not await projection_experience_owns_node_identity_via_lane(
        projection_experience_node_identity_id=projection_experience_node_identity_id,
    ):
        raise RuntimeError(
            "ProjectionExperienceOIGI.create_node_class_identity requires known "
            + "ProjectionExperienceNodeIdentity: projection_experience_node_identity_id="
            + f"{projection_experience_node_identity_id}"
        )

    object_instance_graph_identity = projection_experience_oigi.object_instance_graph_identity
    if object_instance_graph_identity is None:
        object_instance_graph_identity = session.imap_get(
            ObjectInstanceGraphIdentity, object_instance_graph_identity_id
        )
    if object_instance_graph_identity is None:
        known_identity = await object_instance_graph_identity_owns_class_instance_identity_via_lane(
            class_instance_identity_id=class_instance_identity_id
        )
        if not known_identity:
            raise RuntimeError(
                "ProjectionExperienceOIGI.create_node_class_identity requires known ClassInstanceIdentity: "
                + f"class_instance_identity_id={class_instance_identity_id}"
            )
        created = await ProjectionExperienceNodeClassIdentity.build_via_projection_experience_oigi(
            projection_experience_oigi_id=projection_experience_oigi_id,
            projection_experience_node_identity_id=projection_experience_node_identity_id,
            class_instance_identity_id=class_instance_identity_id,
            key=normalized_key,
        )
        for existing in projection_experience_oigi.node_class_identities:
            if existing.id == created.id:
                return existing
        projection_experience_oigi.node_class_identities.append(created)
        return created

    class_instance_identity = next(
        (
            existing
            for existing in object_instance_graph_identity.class_instance_identities
            if existing.id == class_instance_identity_id
        ),
        None,
    )
    if class_instance_identity is None:
        raise RuntimeError(
            "ProjectionExperienceOIGI.create_node_class_identity requires known ClassInstanceIdentity: "
            + f"class_instance_identity_id={class_instance_identity_id}"
        )
    if class_instance_identity.object_instance_graph_identity_id != object_instance_graph_identity_id:
        raise RuntimeError(
            "ProjectionExperienceOIGI.create_node_class_identity OIGI mismatch: "
            + f"oigi={object_instance_graph_identity_id} "
            + "class_instance_identity.object_instance_graph_identity_id="
            + f"{class_instance_identity.object_instance_graph_identity_id}"
        )

    for existing in projection_experience_oigi.node_class_identities:
        if (
            existing.projection_experience_node_identity_id == projection_experience_node_identity_id
            and existing.class_instance_identity_id != class_instance_identity_id
        ):
            raise RuntimeError(
                "ProjectionExperienceOIGI.create_node_class_identity requires one class identity per "
                + "projection node identity within one OIGI"
            )

    created = await ProjectionExperienceNodeClassIdentity.build_via_projection_experience_oigi(
        projection_experience_oigi_id=projection_experience_oigi_id,
        projection_experience_node_identity_id=projection_experience_node_identity_id,
        class_instance_identity_id=class_instance_identity_id,
        key=normalized_key,
    )
    for existing in projection_experience_oigi.node_class_identities:
        if existing.id == created.id:
            return existing
    projection_experience_oigi.node_class_identities.append(created)
    return created
    # --- AWARE: LOGIC END create_node_class_identity


async def create_node_class_identity_edge(
    projection_experience_oigi: ProjectionExperienceOIGI,
    parent_node_class_identity_id: UUID,
    child_node_class_identity_id: UUID,
    class_instance_relationship_identity_id: UUID,
    key: str | None = None,
) -> ProjectionExperienceNodeClassIdentityEdge:
    """
    Attach one explicit parent->child edge under this ProjectionExperienceOIGI.
    """

    # --- AWARE: LOGIC START create_node_class_identity_edge
    projection_experience_oigi_id = projection_experience_oigi.id
    object_instance_graph_identity_id = projection_experience_oigi.object_instance_graph_identity_id
    if parent_node_class_identity_id == child_node_class_identity_id:
        raise RuntimeError(
            "ProjectionExperienceOIGI.create_node_class_identity_edge requires distinct "
            + "parent_node_class_identity_id and child_node_class_identity_id"
        )

    session = current_handler_session()
    parent = session.imap_get(ProjectionExperienceNodeClassIdentity, parent_node_class_identity_id)
    if parent is None:
        raise RuntimeError(
            "ProjectionExperienceOIGI.create_node_class_identity_edge requires known parent "
            + "ProjectionExperienceNodeClassIdentity: parent_node_class_identity_id="
            + f"{parent_node_class_identity_id}"
        )
    child = session.imap_get(ProjectionExperienceNodeClassIdentity, child_node_class_identity_id)
    if child is None:
        raise RuntimeError(
            "ProjectionExperienceOIGI.create_node_class_identity_edge requires known child "
            + "ProjectionExperienceNodeClassIdentity: child_node_class_identity_id="
            + f"{child_node_class_identity_id}"
        )
    if parent.projection_experience_oigi_id != projection_experience_oigi_id:
        raise RuntimeError(
            "ProjectionExperienceOIGI.create_node_class_identity_edge parent does not belong to this OIGI: "
            + f"parent.projection_experience_oigi_id={parent.projection_experience_oigi_id} "
            + "oigi={projection_experience_oigi_id}"
        )
    if child.projection_experience_oigi_id != projection_experience_oigi_id:
        raise RuntimeError(
            "ProjectionExperienceOIGI.create_node_class_identity_edge child does not belong to this OIGI: "
            + f"child.projection_experience_oigi_id={child.projection_experience_oigi_id} "
            + f"oigi={projection_experience_oigi_id}"
        )

    object_instance_graph_identity = projection_experience_oigi.object_instance_graph_identity
    if object_instance_graph_identity is None:
        object_instance_graph_identity = session.imap_get(
            ObjectInstanceGraphIdentity, object_instance_graph_identity_id
        )
    if object_instance_graph_identity is None:
        known_relationship = await object_instance_graph_identity_owns_class_instance_relationship_identity_via_lane(
            class_instance_relationship_identity_id=class_instance_relationship_identity_id
        )
        if not known_relationship:
            raise RuntimeError(
                "ProjectionExperienceOIGI.create_node_class_identity_edge requires known "
                + "ClassInstanceRelationshipIdentity: class_instance_relationship_identity_id="
                + f"{class_instance_relationship_identity_id}"
            )
        created = await ProjectionExperienceNodeClassIdentityEdge.build_via_projection_experience_oigi(
            projection_experience_oigi_id=projection_experience_oigi_id,
            parent_node_class_identity_id=parent_node_class_identity_id,
            child_node_class_identity_id=child_node_class_identity_id,
            class_instance_relationship_identity_id=class_instance_relationship_identity_id,
            key=(key or "").strip() or None,
        )
        for existing in projection_experience_oigi.node_class_identity_edges:
            if existing.id == created.id:
                return existing
        projection_experience_oigi.node_class_identity_edges.append(created)
        return created

    relationship_identity = next(
        (
            existing
            for existing in object_instance_graph_identity.class_instance_relationship_identities
            if existing.id == class_instance_relationship_identity_id
        ),
        None,
    )
    if relationship_identity is None:
        raise RuntimeError(
            "ProjectionExperienceOIGI.create_node_class_identity_edge requires known "
            + "ClassInstanceRelationshipIdentity: class_instance_relationship_identity_id="
            + f"{class_instance_relationship_identity_id}"
        )

    known_class_instance_identity_ids = {
        existing.id for existing in object_instance_graph_identity.class_instance_identities
    }
    if parent.class_instance_identity_id not in known_class_instance_identity_ids:
        raise RuntimeError(
            "ProjectionExperienceOIGI.create_node_class_identity_edge requires known parent "
            + "ClassInstanceIdentity within this OIGI: class_instance_identity_id="
            + f"{parent.class_instance_identity_id}"
        )
    if child.class_instance_identity_id not in known_class_instance_identity_ids:
        raise RuntimeError(
            "ProjectionExperienceOIGI.create_node_class_identity_edge requires known child "
            + "ClassInstanceIdentity within this OIGI: class_instance_identity_id="
            + f"{child.class_instance_identity_id}"
        )

    normalized_key = (key or "").strip() or None
    for existing in projection_experience_oigi.node_class_identity_edges:
        if (
            existing.child_node_class_identity_id == child_node_class_identity_id
            and existing.parent_node_class_identity_id != parent_node_class_identity_id
        ):
            raise RuntimeError(
                "ProjectionExperienceOIGI.create_node_class_identity_edge enforces a single parent per child "
                + "node_class_identity within one OIGI"
            )

    created = await ProjectionExperienceNodeClassIdentityEdge.build_via_projection_experience_oigi(
        projection_experience_oigi_id=projection_experience_oigi_id,
        parent_node_class_identity_id=parent_node_class_identity_id,
        child_node_class_identity_id=child_node_class_identity_id,
        class_instance_relationship_identity_id=class_instance_relationship_identity_id,
        key=normalized_key,
    )
    for existing in projection_experience_oigi.node_class_identity_edges:
        if existing.id == created.id:
            return existing
    projection_experience_oigi.node_class_identity_edges.append(created)
    return created
    # --- AWARE: LOGIC END create_node_class_identity_edge


async def build_via_projection_experience(
    projection_experience_id: UUID, object_instance_graph_identity_id: UUID, key: str | None = None
) -> ProjectionExperienceOIGI:
    """
    Create deterministic ProjectionExperienceOIGI.
    """

    # --- AWARE: LOGIC START build_via_projection_experience
    normalized_key = (key or "").strip() or None
    projection_experience_oigi_id = stable_projection_experience_oigi_id(
        projection_experience_id=projection_experience_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
    )
    session = current_handler_session()
    existing = session.imap_get(ProjectionExperienceOIGI, projection_experience_oigi_id)
    if existing is not None:
        existing_key = (existing.key or "").strip() or None
        if (
            existing.projection_experience_id != projection_experience_id
            or existing.object_instance_graph_identity_id != object_instance_graph_identity_id
            or existing_key != normalized_key
        ):
            raise RuntimeError(
                "ProjectionExperienceOIGI.build_via_projection payload mismatch for existing association: "
                + f"projection_experience_oigi_id={projection_experience_oigi_id}"
            )
        return existing

    return ProjectionExperienceOIGI(
        id=projection_experience_oigi_id,
        projection_experience_id=projection_experience_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        key=normalized_key,
    )
    # --- AWARE: LOGIC END build_via_projection_experience
