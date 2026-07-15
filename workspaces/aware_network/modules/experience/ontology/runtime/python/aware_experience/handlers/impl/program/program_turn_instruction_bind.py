from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_turn_instruction_bind import ProgramTurnInstructionBind
from aware_experience_ontology.program.program_turn_instruction_bind_identity import ProgramTurnInstructionBindIdentity

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Standard
from uuid import NAMESPACE_URL, uuid5

# Experience Ontology
from aware_experience_ontology.program.impl.program_impl_instruction_bind import (
    ProgramImplInstructionBind,
)
from aware_experience_ontology.program.program_config_port import (
    ProgramConfigPort,
)
from aware_experience_ontology.program.program_config_port_projection_experience_node import (
    ProgramConfigPortProjectionExperienceNode,
)
from aware_experience_ontology.projection.projection_experience_node_identity import (
    ProjectionExperienceNodeIdentity,
)
from aware_experience_ontology.projection.projection_experience_node_class_identity import (
    ProjectionExperienceNodeClassIdentity,
)
from aware_experience_ontology.projection.projection_experience_view import (
    ProjectionExperienceView,
)

# Meta Ontology
from aware_meta_ontology.graph.instance.object_instance_graph_branch import (
    ObjectInstanceGraphBranch,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def add_resolved_node_identity(
    program_turn_instruction_bind: ProgramTurnInstructionBind,
    program_config_port_projection_experience_node_id: UUID,
    projection_experience_node_class_identity_id: UUID,
) -> ProgramTurnInstructionBindIdentity:
    """
    Record one deterministic alias->ClassInstanceIdentity resolution receipt.
    """

    # --- AWARE: LOGIC START add_resolved_node_identity
    program_turn_instruction_bind_id = program_turn_instruction_bind.id
    if program_turn_instruction_bind_id is None:
        raise RuntimeError(
            "ProgramTurnInstructionBind.add_resolved_node_identity requires ProgramTurnInstructionBind.id"
        )

    session = current_handler_session()
    bind_instruction = session.imap_get(
        ProgramImplInstructionBind,
        program_turn_instruction_bind.program_impl_instruction_bind_id,
    )
    if bind_instruction is None:
        raise RuntimeError(
            "ProgramTurnInstructionBind.add_resolved_node_identity requires ProgramImplInstructionBind in session: "
            + f"{program_turn_instruction_bind.program_impl_instruction_bind_id}"
        )

    node_contract = session.imap_get(
        ProgramConfigPortProjectionExperienceNode,
        program_config_port_projection_experience_node_id,
    )
    if node_contract is None:
        raise RuntimeError(
            "ProgramTurnInstructionBind.add_resolved_node_identity references unknown "
            + "ProgramConfigPortProjectionExperienceNode: "
            + f"{program_config_port_projection_experience_node_id}"
        )

    node_class_identity = session.imap_get(
        ProjectionExperienceNodeClassIdentity,
        projection_experience_node_class_identity_id,
    )
    if node_class_identity is None:
        raise RuntimeError(
            "ProgramTurnInstructionBind.add_resolved_node_identity references unknown "
            + "ProjectionExperienceNodeClassIdentity: "
            + f"{projection_experience_node_class_identity_id}"
        )

    if bind_instruction.program_config_port_id != node_contract.program_config_port_id:
        raise RuntimeError(
            "ProgramTurnInstructionBind.add_resolved_node_identity port-node mismatch for bind instruction: "
            + f"instruction_port_id={bind_instruction.program_config_port_id} "
            + f"node_port_id={node_contract.program_config_port_id}"
        )

    node_contract_identity = node_contract.projection_node_identity
    node_contract_identity_id = (
        node_contract_identity.projection_experience_node_identity_id if node_contract_identity is not None else None
    )
    if node_contract_identity_id is not None:
        if node_class_identity.projection_experience_node_identity_id != node_contract_identity_id:
            raise RuntimeError(
                "ProgramTurnInstructionBind.add_resolved_node_identity identity mismatch for fixed port-node identity: "
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
                "ProgramTurnInstructionBind.add_resolved_node_identity requires ProjectionExperienceNodeIdentity in session: "
                + f"{node_class_identity.projection_experience_node_identity_id}"
            )
        if projection_identity.projection_experience_node_id != node_contract.projection_experience_node_id:
            raise RuntimeError(
                "ProgramTurnInstructionBind.add_resolved_node_identity node mismatch for dynamic port-node resolution: "
                + f"port_node_id={node_contract.projection_experience_node_id} "
                + f"resolved_identity_node_id={projection_identity.projection_experience_node_id}"
            )

    created_receipt = await ProgramTurnInstructionBindIdentity.build_via_program_turn_instruction_bind(
        program_turn_instruction_bind_id=program_turn_instruction_bind_id,
        program_config_port_projection_experience_node_id=program_config_port_projection_experience_node_id,
        projection_experience_node_class_identity_id=projection_experience_node_class_identity_id,
    )

    if created_receipt.program_config_port_projection_experience_node is None and node_contract is not None:
        created_receipt.program_config_port_projection_experience_node = node_contract
    if created_receipt.projection_experience_node_class_identity is None and node_class_identity is not None:
        created_receipt.projection_experience_node_class_identity = node_class_identity

    if not any(
        existing.id == created_receipt.id for existing in program_turn_instruction_bind.resolved_node_identities
    ):
        program_turn_instruction_bind.resolved_node_identities.append(created_receipt)
    return created_receipt
    # --- AWARE: LOGIC END add_resolved_node_identity


async def build_via_program_turn_instruction(
    program_turn_instruction_id: UUID,
    program_impl_instruction_bind_id: UUID,
    object_instance_graph_branch_id: UUID,
    projection_experience_view_id: UUID,
) -> ProgramTurnInstructionBind:
    """
    Create deterministic ProgramTurnInstructionBind under ProgramTurnInstruction.
    """

    # --- AWARE: LOGIC START build_via_program_turn_instruction
    bind_receipt_id = uuid5(
        NAMESPACE_URL,
        "aware:program_turn_instruction_bind:"
        f"{program_turn_instruction_id}:{program_impl_instruction_bind_id}:"
        f"{object_instance_graph_branch_id}:{projection_experience_view_id}",
    )

    session = current_handler_session()
    bind_instruction = session.imap_get(ProgramImplInstructionBind, program_impl_instruction_bind_id)
    if bind_instruction is None:
        raise RuntimeError(
            "ProgramTurnInstructionBind.build_via_program_turn_instruction requires ProgramImplInstructionBind in session: "
            + f"{program_impl_instruction_bind_id}"
        )

    program_config_port = session.imap_get(ProgramConfigPort, bind_instruction.program_config_port_id)
    if program_config_port is None:
        raise RuntimeError(
            "ProgramTurnInstructionBind.build_via_program_turn_instruction requires ProgramConfigPort in session: "
            + f"{bind_instruction.program_config_port_id}"
        )

    object_instance_graph_branch = session.imap_get(ObjectInstanceGraphBranch, object_instance_graph_branch_id)
    if object_instance_graph_branch is None:
        raise RuntimeError(
            "ProgramTurnInstructionBind.build_via_program_turn_instruction requires ObjectInstanceGraphBranch in session: "
            + f"{object_instance_graph_branch_id}"
        )

    projection_experience_view = session.imap_get(ProjectionExperienceView, projection_experience_view_id)
    if projection_experience_view is None:
        raise RuntimeError(
            "ProgramTurnInstructionBind.build_via_program_turn_instruction requires ProjectionExperienceView in session: "
            + f"{projection_experience_view_id}"
        )

    if projection_experience_view.projection_experience_id != program_config_port.projection_id:
        raise RuntimeError(
            "ProgramTurnInstructionBind.build_via_program_turn_instruction view/projection mismatch for bind instruction: "
            + f"bind_port_projection_id={program_config_port.projection_id} "
            + f"view_projection_id={projection_experience_view.projection_experience_id}"
        )

    existing = session.imap_get(ProgramTurnInstructionBind, bind_receipt_id)
    if existing is not None:
        if (
            existing.program_turn_instruction_id != program_turn_instruction_id
            or existing.program_impl_instruction_bind_id != program_impl_instruction_bind_id
            or existing.object_instance_graph_branch_id != object_instance_graph_branch_id
            or existing.projection_experience_view_id != projection_experience_view_id
        ):
            raise RuntimeError(
                "ProgramTurnInstructionBind.build_via_program_turn_instruction payload mismatch "
                f"for existing receipt: program_turn_instruction_bind_id={bind_receipt_id}"
            )
        if existing.program_impl_instruction_bind is None and bind_instruction is not None:
            existing.program_impl_instruction_bind = bind_instruction
        if existing.object_instance_graph_branch is None and object_instance_graph_branch is not None:
            existing.object_instance_graph_branch = object_instance_graph_branch
        if existing.projection_experience_view is None and projection_experience_view is not None:
            existing.projection_experience_view = projection_experience_view
        return existing

    return ProgramTurnInstructionBind(
        id=bind_receipt_id,
        program_turn_instruction_id=program_turn_instruction_id,
        program_impl_instruction_bind_id=program_impl_instruction_bind_id,
        program_impl_instruction_bind=bind_instruction,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        object_instance_graph_branch=object_instance_graph_branch,
        projection_experience_view_id=projection_experience_view_id,
        projection_experience_view=projection_experience_view,
    )
    # --- AWARE: LOGIC END build_via_program_turn_instruction
