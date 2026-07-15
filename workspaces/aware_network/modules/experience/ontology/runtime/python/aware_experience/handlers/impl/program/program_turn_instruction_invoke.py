from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_turn_instruction_invoke import ProgramTurnInstructionInvoke
from aware_experience_ontology.program.program_turn_instruction_invoke_attribute_config import (
    ProgramTurnInstructionInvokeAttributeConfig,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Ontology
from aware_experience_ontology.program.impl.program_impl_instruction_invoke import (
    ProgramImplInstructionInvoke,
)
from aware_experience_ontology.program.impl.program_impl_instruction_invoke_attribute_config import (
    ProgramImplInstructionInvokeAttributeConfig,
)
from aware_experience_ontology.projection.projection_experience_node_class_identity import (
    ProjectionExperienceNodeClassIdentity,
)

# Environment Ontology
from aware_experience_ontology.program.program_actor_role import (
    ProgramActorRole,
)
from aware_experience_ontology.stable_ids import (
    stable_program_turn_instruction_invoke_id,
    stable_program_turn_instruction_invoke_attribute_config_id,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def add_attribute_config_receipt(
    program_turn_instruction_invoke: ProgramTurnInstructionInvoke,
    program_impl_instruction_invoke_attribute_config_id: UUID,
) -> ProgramTurnInstructionInvokeAttributeConfig:
    """
    Record one deterministic invoke-argument receipt row for this invoke execution.
    """

    # --- AWARE: LOGIC START add_attribute_config_receipt
    invoke_receipt_id = program_turn_instruction_invoke.id
    if invoke_receipt_id is None:
        raise RuntimeError(
            "ProgramTurnInstructionInvoke.add_attribute_config_receipt requires ProgramTurnInstructionInvoke.id"
        )

    session = current_handler_session()
    invoke_instruction = session.imap_get(
        ProgramImplInstructionInvoke,
        program_turn_instruction_invoke.program_impl_instruction_invoke_id,
    )
    if invoke_instruction is None:
        raise RuntimeError(
            "ProgramTurnInstructionInvoke.add_attribute_config_receipt requires ProgramImplInstructionInvoke in session: "
            + f"{program_turn_instruction_invoke.program_impl_instruction_invoke_id}"
        )
    invoke_attribute_config = session.imap_get(
        ProgramImplInstructionInvokeAttributeConfig,
        program_impl_instruction_invoke_attribute_config_id,
    )
    if invoke_attribute_config is None:
        raise RuntimeError(
            "ProgramTurnInstructionInvoke.add_attribute_config_receipt requires "
            + "ProgramImplInstructionInvokeAttributeConfig in session: "
            + f"{program_impl_instruction_invoke_attribute_config_id}"
        )
    if invoke_attribute_config.program_impl_instruction_invoke_id != invoke_instruction.id:
        raise RuntimeError(
            "ProgramTurnInstructionInvoke.add_attribute_config_receipt invoke-attribute mismatch for receipt: "
            + f"invoke_id={invoke_instruction.id} "
            + "invoke_attribute_program_impl_instruction_invoke_id="
            + f"{invoke_attribute_config.program_impl_instruction_invoke_id}"
        )

    created_receipt_id = stable_program_turn_instruction_invoke_attribute_config_id(
        program_turn_instruction_invoke_id=invoke_receipt_id,
        program_impl_instruction_invoke_attribute_config_id=program_impl_instruction_invoke_attribute_config_id,
    )
    created_receipt = session.imap_get(ProgramTurnInstructionInvokeAttributeConfig, created_receipt_id)
    if created_receipt is not None:
        if (
            created_receipt.program_turn_instruction_invoke_id != invoke_receipt_id
            or created_receipt.program_impl_instruction_invoke_attribute_config_id
            != program_impl_instruction_invoke_attribute_config_id
        ):
            raise RuntimeError(
                "ProgramTurnInstructionInvoke.add_attribute_config_receipt payload mismatch for existing receipt: "
                + f"program_turn_instruction_invoke_attribute_config_id={created_receipt_id}"
            )
        if created_receipt.program_impl_instruction_invoke_attribute_config is None:
            created_receipt.program_impl_instruction_invoke_attribute_config = invoke_attribute_config
    else:
        created_receipt = ProgramTurnInstructionInvokeAttributeConfig(
            id=created_receipt_id,
            program_turn_instruction_invoke_id=invoke_receipt_id,
            program_impl_instruction_invoke_attribute_config_id=program_impl_instruction_invoke_attribute_config_id,
            program_impl_instruction_invoke_attribute_config=invoke_attribute_config,
        )
    if created_receipt.program_impl_instruction_invoke_attribute_config is None and invoke_attribute_config is not None:
        created_receipt.program_impl_instruction_invoke_attribute_config = invoke_attribute_config
    if not any(
        existing.id == created_receipt.id for existing in program_turn_instruction_invoke.attribute_config_receipts
    ):
        program_turn_instruction_invoke.attribute_config_receipts.append(created_receipt)
    return created_receipt
    # --- AWARE: LOGIC END add_attribute_config_receipt


async def build_via_program_turn_instruction(
    program_turn_instruction_id: UUID,
    program_impl_instruction_invoke_id: UUID,
    program_actor_role_id: UUID,
    projection_experience_node_class_identity_id: UUID,
) -> ProgramTurnInstructionInvoke:
    """
    Create deterministic ProgramTurnInstructionInvoke under ProgramTurnInstruction.
    """

    # --- AWARE: LOGIC START build_via_program_turn_instruction
    invoke_receipt_id = stable_program_turn_instruction_invoke_id(
        program_turn_instruction_id=program_turn_instruction_id,
        program_impl_instruction_invoke_id=program_impl_instruction_invoke_id,
        program_actor_role_id=program_actor_role_id,
        projection_experience_node_class_identity_id=projection_experience_node_class_identity_id,
    )

    session = current_handler_session()
    invoke_instruction = session.imap_get(ProgramImplInstructionInvoke, program_impl_instruction_invoke_id)
    program_actor_role = session.imap_get(ProgramActorRole, program_actor_role_id)
    projection_experience_node_class_identity = session.imap_get(
        ProjectionExperienceNodeClassIdentity,
        projection_experience_node_class_identity_id,
    )

    existing = session.imap_get(ProgramTurnInstructionInvoke, invoke_receipt_id)
    if existing is not None:
        if (
            existing.program_impl_instruction_invoke_id != program_impl_instruction_invoke_id
            or existing.program_actor_role_id != program_actor_role_id
            or existing.projection_experience_node_class_identity_id != projection_experience_node_class_identity_id
        ):
            raise RuntimeError(
                "ProgramTurnInstructionInvoke.build_via_program_turn_instruction payload mismatch "
                f"for existing receipt: program_turn_instruction_invoke_id={invoke_receipt_id}"
            )
        if existing.program_impl_instruction_invoke is None and invoke_instruction is not None:
            existing.program_impl_instruction_invoke = invoke_instruction
        if existing.program_actor_role is None and program_actor_role is not None:
            existing.program_actor_role = program_actor_role
        if (
            existing.projection_experience_node_class_identity is None
            and projection_experience_node_class_identity is not None
        ):
            existing.projection_experience_node_class_identity = projection_experience_node_class_identity
        return existing

    return ProgramTurnInstructionInvoke(
        id=invoke_receipt_id,
        program_impl_instruction_invoke_id=program_impl_instruction_invoke_id,
        program_impl_instruction_invoke=invoke_instruction,
        program_actor_role_id=program_actor_role_id,
        program_actor_role=program_actor_role,
        projection_experience_node_class_identity_id=projection_experience_node_class_identity_id,
        projection_experience_node_class_identity=projection_experience_node_class_identity,
    )
    # --- AWARE: LOGIC END build_via_program_turn_instruction
