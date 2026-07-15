from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_turn_instruction_bind_identity import ProgramTurnInstructionBindIdentity

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Standard
from uuid import NAMESPACE_URL, uuid5

# Experience Ontology
from aware_experience_ontology.program.program_config_port_projection_experience_node import (
    ProgramConfigPortProjectionExperienceNode,
)
from aware_experience_ontology.projection.projection_experience_node_identity import (
    ProjectionExperienceNodeIdentity,
)
from aware_experience_ontology.projection.projection_experience_node_class_identity import (
    ProjectionExperienceNodeClassIdentity,
)
from aware_experience_ontology.program.program_turn_instruction_bind import (
    ProgramTurnInstructionBind,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_program_turn_instruction_bind(
    program_turn_instruction_bind_id: UUID,
    program_config_port_projection_experience_node_id: UUID,
    projection_experience_node_class_identity_id: UUID,
) -> ProgramTurnInstructionBindIdentity:
    """
    Create deterministic ProgramTurnInstructionBindIdentity under ProgramTurnInstructionBind.
    """

    # --- AWARE: LOGIC START build_via_program_turn_instruction_bind
    bind_identity_receipt_id = uuid5(
        NAMESPACE_URL,
        "aware:program_turn_instruction_bind_identity:"
        f"{program_turn_instruction_bind_id}:{program_config_port_projection_experience_node_id}:"
        f"{projection_experience_node_class_identity_id}",
    )

    session = current_handler_session()
    bind_receipt = session.imap_get(ProgramTurnInstructionBind, program_turn_instruction_bind_id)
    if bind_receipt is None:
        raise RuntimeError(
            "ProgramTurnInstructionBindIdentity.build_via_program_turn_instruction_bind requires "
            + "ProgramTurnInstructionBind in session: "
            + f"{program_turn_instruction_bind_id}"
        )

    node_contract = session.imap_get(
        ProgramConfigPortProjectionExperienceNode,
        program_config_port_projection_experience_node_id,
    )
    if node_contract is None:
        raise RuntimeError(
            "ProgramTurnInstructionBindIdentity.build_via_program_turn_instruction_bind references "
            + "unknown ProgramConfigPortProjectionExperienceNode: "
            + f"{program_config_port_projection_experience_node_id}"
        )

    if bind_receipt.program_impl_instruction_bind is None:
        raise RuntimeError(
            "ProgramTurnInstructionBindIdentity.build_via_program_turn_instruction_bind requires "
            + "bind receipt ProgramImplInstructionBind relation"
        )
    bind_instruction = bind_receipt.program_impl_instruction_bind
    if bind_instruction.program_config_port_id != node_contract.program_config_port_id:
        raise RuntimeError(
            "ProgramTurnInstructionBindIdentity.build_via_program_turn_instruction_bind port-node mismatch for "
            + "bind receipt instruction: "
            + f"instruction_port_id={bind_instruction.program_config_port_id} "
            + f"node_port_id={node_contract.program_config_port_id}"
        )

    node_class_identity = session.imap_get(
        ProjectionExperienceNodeClassIdentity,
        projection_experience_node_class_identity_id,
    )
    if node_class_identity is None:
        raise RuntimeError(
            "ProgramTurnInstructionBindIdentity.build_via_program_turn_instruction_bind references "
            + "unknown ProjectionExperienceNodeClassIdentity: "
            + f"{projection_experience_node_class_identity_id}"
        )

    node_contract_identity = node_contract.projection_node_identity
    node_contract_identity_id = (
        node_contract_identity.projection_experience_node_identity_id if node_contract_identity is not None else None
    )
    if node_contract_identity_id is not None:
        if node_class_identity.projection_experience_node_identity_id != node_contract_identity_id:
            raise RuntimeError(
                "ProgramTurnInstructionBindIdentity.build_via_program_turn_instruction_bind identity mismatch for "
                + "fixed port-node identity: "
                + f"port_node_identity_id={node_contract_identity_id} "
                + f"resolved_identity_id={node_class_identity.projection_experience_node_identity_id}"
            )
    else:
        projection_identity = session.imap_get(
            ProjectionExperienceNodeIdentity,
            node_class_identity.projection_experience_node_identity_id,
        )
        if projection_identity is None:
            raise RuntimeError(
                "ProgramTurnInstructionBindIdentity.build_via_program_turn_instruction_bind requires "
                + "ProjectionExperienceNodeIdentity in session: "
                + f"{node_class_identity.projection_experience_node_identity_id}"
            )
        if projection_identity.projection_experience_node_id != node_contract.projection_experience_node_id:
            raise RuntimeError(
                "ProgramTurnInstructionBindIdentity.build_via_program_turn_instruction_bind node mismatch for "
                + "dynamic port-node resolution: "
                + f"port_node_id={node_contract.projection_experience_node_id} "
                + f"resolved_identity_node_id={projection_identity.projection_experience_node_id}"
            )

    existing = session.imap_get(ProgramTurnInstructionBindIdentity, bind_identity_receipt_id)
    if existing is not None:
        if (
            existing.program_turn_instruction_bind_id != program_turn_instruction_bind_id
            or existing.program_config_port_projection_experience_node_id
            != program_config_port_projection_experience_node_id
            or existing.projection_experience_node_class_identity_id != projection_experience_node_class_identity_id
        ):
            raise RuntimeError(
                "ProgramTurnInstructionBindIdentity.build_via_program_turn_instruction_bind payload "
                f"mismatch for existing receipt: program_turn_instruction_bind_identity_id={bind_identity_receipt_id}"
            )
        if existing.program_config_port_projection_experience_node is None and node_contract is not None:
            existing.program_config_port_projection_experience_node = node_contract
        if existing.projection_experience_node_class_identity is None and node_class_identity is not None:
            existing.projection_experience_node_class_identity = node_class_identity
        return existing

    return ProgramTurnInstructionBindIdentity(
        id=bind_identity_receipt_id,
        program_turn_instruction_bind_id=program_turn_instruction_bind_id,
        program_config_port_projection_experience_node_id=program_config_port_projection_experience_node_id,
        program_config_port_projection_experience_node=node_contract,
        projection_experience_node_class_identity_id=projection_experience_node_class_identity_id,
        projection_experience_node_class_identity=node_class_identity,
    )
    # --- AWARE: LOGIC END build_via_program_turn_instruction_bind
