from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.\
    program_config_graph_program_config_port_projection_experience_node_class import (
        ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass,
    )

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Runtime
from aware_experience.stable_ids import (
    stable_program_config_graph_program_config_port_projection_experience_node_class_id,
)

# Experience Ontology
from aware_experience_ontology.program.program_config_graph_program_config import (
    ProgramConfigGraphProgramConfig,
)
from aware_experience_ontology.program.program_config_port import ProgramConfigPort
from aware_experience_ontology.program.program_config_port_projection_experience_node import (
    ProgramConfigPortProjectionExperienceNode,
)
from aware_experience_ontology.program.program_config_port_projection_experience_node_identity import (
    ProgramConfigPortProjectionExperienceNodeIdentity,
)
from aware_experience_ontology.projection.projection_experience_node_class_identity import (
    ProjectionExperienceNodeClassIdentity,
)
from aware_experience_ontology.projection.projection_experience_node_identity import (
    ProjectionExperienceNodeIdentity,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_program_config_graph_program_config(
    program_config_graph_program_config_id: UUID,
    program_config_port_projection_experience_node_id: UUID,
    projection_experience_node_class_identity_id: UUID,
    key: str | None = None,
) -> ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass:
    """
    Create deterministic ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass
    under ProgramConfigGraphProgramConfig.
    """

    # --- AWARE: LOGIC START build_via_program_config_graph_program_config
    normalized_key = (key or "").strip() or None

    session = current_handler_session()
    graph_program_config = session.imap_get(
        ProgramConfigGraphProgramConfig,
        program_config_graph_program_config_id,
    )
    if graph_program_config is None:
        raise RuntimeError(
            "ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass.build_via_program_config_graph_program_config "
            + "requires known ProgramConfigGraphProgramConfig: "
            + "program_config_graph_program_config_id="
            + f"{program_config_graph_program_config_id}"
        )
    port_node = session.imap_get(
        ProgramConfigPortProjectionExperienceNode,
        program_config_port_projection_experience_node_id,
    )
    if port_node is None:
        raise RuntimeError(
            "ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass.build_via_program_config_graph_program_config "
            + "requires known ProgramConfigPortProjectionExperienceNode: "
            + "program_config_port_projection_experience_node_id="
            + f"{program_config_port_projection_experience_node_id}"
        )
    port = session.imap_get(ProgramConfigPort, port_node.program_config_port_id)
    if port is None:
        raise RuntimeError(
            "ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass.build_via_program_config_graph_program_config "
            + "requires known ProgramConfigPort for port node: "
            + f"program_config_port_id={port_node.program_config_port_id}"
        )
    if graph_program_config.program_config_id != port.program_config_id:
        raise RuntimeError(
            "ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass.build_via_program_config_graph_program_config "
            + "program mismatch: "
            + f"graph_program_config.program_config_id={graph_program_config.program_config_id} "
            + f"port.program_config_id={port.program_config_id}"
        )

    node_class_identity = session.imap_get(
        ProjectionExperienceNodeClassIdentity,
        projection_experience_node_class_identity_id,
    )
    if node_class_identity is None:
        raise RuntimeError(
            "ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass.build_via_program_config_graph_program_config "
            + "requires known ProjectionExperienceNodeClassIdentity: "
            + "projection_experience_node_class_identity_id="
            + f"{projection_experience_node_class_identity_id}"
        )

    projection_node_identity_id = None
    port_node_identity_edge = port_node.projection_node_identity
    if port_node_identity_edge is not None:
        port_node_identity = session.imap_get(
            ProgramConfigPortProjectionExperienceNodeIdentity,
            port_node_identity_edge.id,
        )
        if port_node_identity is None:
            raise RuntimeError(
                "ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass.build_via_program_config_graph_program_config "
                + "references missing ProgramConfigPortProjectionExperienceNodeIdentity: "
                + f"{port_node_identity_edge.id}"
            )
        projection_node_identity_id = port_node_identity.projection_experience_node_identity_id
    else:
        projection_node_identity = session.imap_get(
            ProjectionExperienceNodeIdentity,
            node_class_identity.projection_experience_node_identity_id,
        )
        if projection_node_identity is None:
            raise RuntimeError(
                "ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass.build_via_program_config_graph_program_config "
                + "requires known ProjectionExperienceNodeIdentity for node-class identity: "
                + f"{node_class_identity.projection_experience_node_identity_id}"
            )
        if projection_node_identity.projection_experience_node_id != port_node.projection_experience_node_id:
            raise RuntimeError(
                "ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass.build_via_program_config_graph_program_config "
                + "node mismatch without explicit port-node identity: "
                + f"projection_experience_node_id={port_node.projection_experience_node_id} "
                + "node_class_identity.projection_experience_node_identity_id="
                + f"{node_class_identity.projection_experience_node_identity_id}"
            )
    if projection_node_identity_id is not None and (
        projection_node_identity_id != node_class_identity.projection_experience_node_identity_id
    ):
        raise RuntimeError(
            "ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass.build_via_program_config_graph_program_config "
            + "identity mismatch: "
            + f"port_node.projection_experience_node_identity_id={projection_node_identity_id} "
            + "node_class_identity.projection_experience_node_identity_id="
            + f"{node_class_identity.projection_experience_node_identity_id}"
        )

    association_id = stable_program_config_graph_program_config_port_projection_experience_node_class_id(
        program_config_graph_program_config_id=program_config_graph_program_config_id,
        program_config_port_projection_experience_node_id=program_config_port_projection_experience_node_id,
        projection_experience_node_class_identity_id=projection_experience_node_class_identity_id,
    )
    existing = session.imap_get(
        ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass,
        association_id,
    )
    if existing is not None:
        existing_key = (existing.key or "").strip() or None
        if (
            existing.program_config_graph_program_config_id != program_config_graph_program_config_id
            or existing.program_config_port_projection_experience_node_id
            != program_config_port_projection_experience_node_id
            or existing.projection_experience_node_class_identity_id != projection_experience_node_class_identity_id
            or existing_key != normalized_key
        ):
            raise RuntimeError(
                "ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass.build_via_program_config_graph_program_config "
                + "payload mismatch for existing association: association_id="
                + f"{association_id}"
            )
        existing.program_config_port_projection_experience_node = port_node
        existing.projection_experience_node_class_identity = node_class_identity
        return existing

    return ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass(
        id=association_id,
        program_config_graph_program_config_id=program_config_graph_program_config_id,
        program_config_port_projection_experience_node_id=program_config_port_projection_experience_node_id,
        projection_experience_node_class_identity_id=projection_experience_node_class_identity_id,
        program_config_port_projection_experience_node=port_node,
        projection_experience_node_class_identity=node_class_identity,
        key=normalized_key,
    )
    # --- AWARE: LOGIC END build_via_program_config_graph_program_config
