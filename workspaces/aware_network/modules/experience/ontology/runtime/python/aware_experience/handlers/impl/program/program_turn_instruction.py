from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_enums import (
    ProgramTurnDecisionReason,
    ProgramTurnTransition,
)
from aware_experience_ontology.program.program_turn_decision import ProgramTurnInstructionDecision
from aware_experience_ontology.program.program_turn_instruction import ProgramTurnInstruction
from aware_experience_ontology.program.program_turn_instruction_action import ProgramTurnInstructionAction
from aware_experience_ontology.program.program_turn_instruction_bind import ProgramTurnInstructionBind
from aware_experience_ontology.program.program_turn_instruction_invoke import ProgramTurnInstructionInvoke

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Standard
from uuid import NAMESPACE_URL, uuid5

# Experience Ontology
from aware_experience_ontology.program.impl.program_impl_instruction_bind import (
    ProgramImplInstructionBind,
)
from aware_experience_ontology.program.impl.program_impl_instruction_invoke import (
    ProgramImplInstructionInvoke,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent import (
    ProgramImplInstructionIntent,
)
from aware_identity_ontology.actor.actor_config_role_config import (
    ActorConfigRoleConfig,
)
from aware_experience_ontology.program.program_config_actor_config import (
    ProgramConfigActorConfig,
)
from aware_experience_ontology.program.program_config_port_projection_experience_node import (
    ProgramConfigPortProjectionExperienceNode,
)
from aware_experience_ontology.projection.projection_experience_node_identity import (
    ProjectionExperienceNodeIdentity,
)
from aware_experience_ontology.program.impl.program_impl_instruction import (
    ProgramImplInstruction,
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

from aware_experience_ontology.program.program_actor import (
    ProgramActor,
)
from aware_experience_ontology.program.program_actor_role import (
    ProgramActorRole,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def record_decision(
    program_turn_instruction: ProgramTurnInstruction,
    transition: ProgramTurnTransition,
    reason: ProgramTurnDecisionReason,
    step_index: int,
    total_steps: int,
    invokes_in_turn: int = 0,
    elapsed_ms_in_turn: int = 0,
    awaiting_external_signal: bool = False,
    instruction_failed: bool = False,
) -> ProgramTurnInstructionDecision:
    """
    Record one typed decision checkpoint for this instruction execution.
    """

    # --- AWARE: LOGIC START record_decision
    program_turn_instruction_id = program_turn_instruction.id
    if program_turn_instruction_id is None:
        raise RuntimeError("ProgramTurnInstruction.record_decision requires ProgramTurnInstruction.id")

    created_decision = await ProgramTurnInstructionDecision.build_via_program_turn_instruction(
        program_turn_instruction_id=program_turn_instruction_id,
        transition=transition,
        reason=reason,
        step_index=step_index,
        total_steps=total_steps,
        invokes_in_turn=invokes_in_turn,
        elapsed_ms_in_turn=elapsed_ms_in_turn,
        awaiting_external_signal=awaiting_external_signal,
        instruction_failed=instruction_failed,
    )

    if not any(existing.id == created_decision.id for existing in program_turn_instruction.decisions):
        program_turn_instruction.decisions.append(created_decision)

    return created_decision
    # --- AWARE: LOGIC END record_decision


async def record_bind(
    program_turn_instruction: ProgramTurnInstruction,
    program_impl_instruction_bind_id: UUID,
    object_instance_graph_branch_id: UUID,
    projection_experience_view_id: UUID,
) -> ProgramTurnInstructionBind:
    """
    Record one bind execution receipt for this instruction.

    Contract:
    - Captures resolved branch/view runtime bindings as commit-backed facts.
    - Node alias resolution receipts are attached under ProgramTurnInstructionBind.
    """

    # --- AWARE: LOGIC START record_bind
    program_turn_instruction_id = program_turn_instruction.id
    if program_turn_instruction_id is None:
        raise RuntimeError("ProgramTurnInstruction.record_bind requires ProgramTurnInstruction.id")

    session = current_handler_session()
    existing = program_turn_instruction.bind_receipt
    bind_instruction = session.imap_get(ProgramImplInstructionBind, program_impl_instruction_bind_id)
    object_instance_graph_branch = session.imap_get(ObjectInstanceGraphBranch, object_instance_graph_branch_id)
    projection_experience_view = session.imap_get(ProjectionExperienceView, projection_experience_view_id)
    if existing is not None:
        if (
            existing.program_impl_instruction_bind_id != program_impl_instruction_bind_id
            or existing.object_instance_graph_branch_id != object_instance_graph_branch_id
            or existing.projection_experience_view_id != projection_experience_view_id
        ):
            raise RuntimeError(
                "ProgramTurnInstruction.record_bind payload mismatch for existing bind receipt: "
                f"program_turn_instruction_id={program_turn_instruction_id}"
            )
        if existing.program_impl_instruction_bind is None and bind_instruction is not None:
            existing.program_impl_instruction_bind = bind_instruction
        if existing.object_instance_graph_branch is None and object_instance_graph_branch is not None:
            existing.object_instance_graph_branch = object_instance_graph_branch
        if existing.projection_experience_view is None and projection_experience_view is not None:
            existing.projection_experience_view = projection_experience_view
        return existing

    created_bind_receipt = await ProgramTurnInstructionBind.build_via_program_turn_instruction(
        program_turn_instruction_id=program_turn_instruction_id,
        program_impl_instruction_bind_id=program_impl_instruction_bind_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        projection_experience_view_id=projection_experience_view_id,
    )

    if created_bind_receipt.program_impl_instruction_bind is None and bind_instruction is not None:
        created_bind_receipt.program_impl_instruction_bind = bind_instruction
    if created_bind_receipt.object_instance_graph_branch is None and object_instance_graph_branch is not None:
        created_bind_receipt.object_instance_graph_branch = object_instance_graph_branch
    if created_bind_receipt.projection_experience_view is None and projection_experience_view is not None:
        created_bind_receipt.projection_experience_view = projection_experience_view

    if (
        program_turn_instruction.bind_receipt is not None
        and program_turn_instruction.bind_receipt.id != created_bind_receipt.id
    ):
        raise RuntimeError(
            "ProgramTurnInstruction.record_bind receipt mismatch for existing slot: "
            f"program_turn_instruction_id={program_turn_instruction_id}"
        )
    program_turn_instruction.bind_receipt = created_bind_receipt
    return created_bind_receipt
    # --- AWARE: LOGIC END record_bind


async def record_invoke(
    program_turn_instruction: ProgramTurnInstruction,
    program_impl_instruction_invoke_id: UUID,
    program_actor_role_id: UUID,
    projection_experience_node_class_identity_id: UUID,
) -> ProgramTurnInstructionInvoke:
    """
    Record one invoke execution receipt for this instruction.

    Contract:
    - Captures resolved actor-role attribution and target identity context.
    - Invoke argument/value receipts remain child rails under ProgramTurnInstructionInvoke.
    """

    # --- AWARE: LOGIC START record_invoke
    program_turn_instruction_id = program_turn_instruction.id
    if program_turn_instruction_id is None:
        raise RuntimeError("ProgramTurnInstruction.record_invoke requires ProgramTurnInstruction.id")

    session = current_handler_session()
    existing = program_turn_instruction.invoke_receipt
    invoke_instruction = session.imap_get(ProgramImplInstructionInvoke, program_impl_instruction_invoke_id)
    if invoke_instruction is None:
        raise RuntimeError(
            "ProgramTurnInstruction.record_invoke requires ProgramImplInstructionInvoke in session: "
            + f"{program_impl_instruction_invoke_id}"
        )

    program_actor_role = session.imap_get(ProgramActorRole, program_actor_role_id)
    if program_actor_role is None:
        raise RuntimeError(
            "ProgramTurnInstruction.record_invoke requires ProgramActorRole in session: " + f"{program_actor_role_id}"
        )

    program_actor = session.imap_get(ProgramActor, program_actor_role.program_actor_id)
    if program_actor is None:
        raise RuntimeError(
            "ProgramTurnInstruction.record_invoke requires ProgramActor in session: "
            + f"{program_actor_role.program_actor_id}"
        )

    invoke_actor_contract = session.imap_get(
        ProgramConfigActorConfig,
        invoke_instruction.program_config_actor_config_id,
    )
    if invoke_actor_contract is None:
        raise RuntimeError(
            "ProgramTurnInstruction.record_invoke requires ProgramConfigActorConfig in session: "
            + f"{invoke_instruction.program_config_actor_config_id}"
        )

    actor_config_role_config = session.imap_get(
        ActorConfigRoleConfig,
        program_actor_role.actor_config_role_config_id,
    )
    if actor_config_role_config is None:
        raise RuntimeError(
            "ProgramTurnInstruction.record_invoke requires ActorConfigRoleConfig in session: "
            + f"{program_actor_role.actor_config_role_config_id}"
        )

    if program_actor.program_config_actor_config_id != invoke_instruction.program_config_actor_config_id:
        raise RuntimeError(
            "ProgramTurnInstruction.record_invoke actor alias mismatch between ProgramActor and invoke contract: "
            + f"program_actor.program_config_actor_config_id={program_actor.program_config_actor_config_id} "
            + f"invoke.program_config_actor_config_id={invoke_instruction.program_config_actor_config_id}"
        )

    if actor_config_role_config.actor_config_id != invoke_actor_contract.actor_config_id:
        raise RuntimeError(
            "ProgramTurnInstruction.record_invoke actor-role mismatch for invoke contract: "
            + f"actor_config_role_config.actor_config_id={actor_config_role_config.actor_config_id} "
            + f"invoke_actor_config_id={invoke_actor_contract.actor_config_id}"
        )

    invoke_node_contract = session.imap_get(
        ProgramConfigPortProjectionExperienceNode,
        invoke_instruction.program_config_port_projection_experience_node_id,
    )
    if invoke_node_contract is None:
        raise RuntimeError(
            "ProgramTurnInstruction.record_invoke requires ProgramConfigPortProjectionExperienceNode in session: "
            + f"{invoke_instruction.program_config_port_projection_experience_node_id}"
        )

    projection_experience_node_class_identity = session.imap_get(
        ProjectionExperienceNodeClassIdentity,
        projection_experience_node_class_identity_id,
    )
    if projection_experience_node_class_identity is None:
        raise RuntimeError(
            "ProgramTurnInstruction.record_invoke requires ProjectionExperienceNodeClassIdentity in session: "
            + f"{projection_experience_node_class_identity_id}"
        )

    invoke_node_contract_identity = invoke_node_contract.projection_node_identity
    invoke_node_contract_identity_id = (
        invoke_node_contract_identity.projection_experience_node_identity_id
        if invoke_node_contract_identity is not None
        else None
    )
    if invoke_node_contract_identity_id is not None:
        if (
            projection_experience_node_class_identity.projection_experience_node_identity_id
            != invoke_node_contract_identity_id
        ):
            raise RuntimeError(
                "ProgramTurnInstruction.record_invoke identity mismatch for fixed invoke node identity: "
                + f"invoke_node_identity_id={invoke_node_contract_identity_id} "
                + "resolved_identity_id="
                + f"{projection_experience_node_class_identity.projection_experience_node_identity_id}"
            )
    else:
        resolved_projection_identity = session.imap_get(
            ProjectionExperienceNodeIdentity,
            projection_experience_node_class_identity.projection_experience_node_identity_id,
        )
        if resolved_projection_identity is None:
            raise RuntimeError(
                "ProgramTurnInstruction.record_invoke requires ProjectionExperienceNodeIdentity in session: "
                + f"{projection_experience_node_class_identity.projection_experience_node_identity_id}"
            )
        if (
            resolved_projection_identity.projection_experience_node_id
            != invoke_node_contract.projection_experience_node_id
        ):
            raise RuntimeError(
                "ProgramTurnInstruction.record_invoke node mismatch for dynamic invoke node resolution: "
                + f"invoke_node_id={invoke_node_contract.projection_experience_node_id} "
                + f"resolved_identity_node_id={resolved_projection_identity.projection_experience_node_id}"
            )

    if existing is not None:
        if (
            existing.program_impl_instruction_invoke_id != program_impl_instruction_invoke_id
            or existing.program_actor_role_id != program_actor_role_id
            or existing.projection_experience_node_class_identity_id != projection_experience_node_class_identity_id
        ):
            raise RuntimeError(
                "ProgramTurnInstruction.record_invoke payload mismatch for existing invoke receipt: "
                f"program_turn_instruction_id={program_turn_instruction_id}"
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

    created_invoke_receipt = await ProgramTurnInstructionInvoke.build_via_program_turn_instruction(
        program_turn_instruction_id=program_turn_instruction_id,
        program_impl_instruction_invoke_id=program_impl_instruction_invoke_id,
        program_actor_role_id=program_actor_role_id,
        projection_experience_node_class_identity_id=projection_experience_node_class_identity_id,
    )

    if created_invoke_receipt.program_impl_instruction_invoke is None and invoke_instruction is not None:
        created_invoke_receipt.program_impl_instruction_invoke = invoke_instruction
    if created_invoke_receipt.program_actor_role is None and program_actor_role is not None:
        created_invoke_receipt.program_actor_role = program_actor_role
    if (
        created_invoke_receipt.projection_experience_node_class_identity is None
        and projection_experience_node_class_identity is not None
    ):
        created_invoke_receipt.projection_experience_node_class_identity = projection_experience_node_class_identity
    expected_invoke_attribute_ids = {attribute.id for attribute in invoke_instruction.attribute_configs}
    for invoke_attribute_id in sorted(expected_invoke_attribute_ids, key=str):
        await created_invoke_receipt.add_attribute_config_receipt(
            program_impl_instruction_invoke_attribute_config_id=invoke_attribute_id,
        )
    receipt_invoke_attribute_ids = {
        receipt.program_impl_instruction_invoke_attribute_config_id
        for receipt in created_invoke_receipt.attribute_config_receipts
    }
    if receipt_invoke_attribute_ids != expected_invoke_attribute_ids:
        raise RuntimeError(
            "ProgramTurnInstruction.record_invoke invoke-argument receipt mismatch for invoke contract: "
            + f"expected={sorted(str(i) for i in expected_invoke_attribute_ids)} "
            + f"actual={sorted(str(i) for i in receipt_invoke_attribute_ids)}"
        )

    if (
        program_turn_instruction.invoke_receipt is not None
        and program_turn_instruction.invoke_receipt.id != created_invoke_receipt.id
    ):
        raise RuntimeError(
            "ProgramTurnInstruction.record_invoke receipt mismatch for existing slot: "
            f"program_turn_instruction_id={program_turn_instruction_id}"
        )
    program_turn_instruction.invoke_receipt = created_invoke_receipt
    return created_invoke_receipt
    # --- AWARE: LOGIC END record_invoke


async def record_action(
    program_turn_instruction: ProgramTurnInstruction,
    program_impl_instruction_intent_id: UUID,
    action_config_id: UUID,
    event_config_id: UUID,
    action_intent_id: UUID,
    intent_key: str,
) -> ProgramTurnInstructionAction:
    """
    Record one program-declared ActionIntent receipt for this instruction.

    Contract:
    - Captures program provenance above Reactivity's actor-free
      ActionIntent primitive.
    - Does not dispatch or fulfill the action.
    """

    # --- AWARE: LOGIC START record_action
    program_turn_instruction_id = program_turn_instruction.id
    if program_turn_instruction_id is None:
        raise RuntimeError("ProgramTurnInstruction.record_action requires ProgramTurnInstruction.id")

    normalized_intent_key = str(intent_key or "").strip()
    if not normalized_intent_key:
        raise RuntimeError("ProgramTurnInstruction.record_action requires non-empty intent_key")

    session = current_handler_session()
    existing = program_turn_instruction.action_receipt
    intent_instruction = session.imap_get(ProgramImplInstructionIntent, program_impl_instruction_intent_id)
    if intent_instruction is None:
        raise RuntimeError(
            "ProgramTurnInstruction.record_action requires ProgramImplInstructionIntent in session: "
            + f"{program_impl_instruction_intent_id}"
        )

    if intent_instruction.action_config_id != action_config_id:
        raise RuntimeError(
            "ProgramTurnInstruction.record_action action_config mismatch for intent instruction: "
            + f"instruction_action_config_id={intent_instruction.action_config_id} "
            + f"action_config_id={action_config_id}"
        )
    if intent_instruction.event_config_id != event_config_id:
        raise RuntimeError(
            "ProgramTurnInstruction.record_action event_config mismatch for intent instruction: "
            + f"instruction_event_config_id={intent_instruction.event_config_id} "
            + f"event_config_id={event_config_id}"
        )

    if existing is not None:
        if (
            existing.program_impl_instruction_intent_id != program_impl_instruction_intent_id
            or existing.action_config_id != action_config_id
            or existing.event_config_id != event_config_id
            or existing.action_intent_id != action_intent_id
            or existing.intent_key != normalized_intent_key
        ):
            raise RuntimeError(
                "ProgramTurnInstruction.record_action payload mismatch for existing action receipt: "
                f"program_turn_instruction_id={program_turn_instruction_id}"
            )
        if existing.program_impl_instruction_intent is None:
            existing.program_impl_instruction_intent = intent_instruction
        return existing

    created_action_receipt = await ProgramTurnInstructionAction.build_via_program_turn_instruction(
        program_turn_instruction_id=program_turn_instruction_id,
        program_impl_instruction_intent_id=program_impl_instruction_intent_id,
        action_config_id=action_config_id,
        event_config_id=event_config_id,
        action_intent_id=action_intent_id,
        intent_key=normalized_intent_key,
    )

    if created_action_receipt.program_impl_instruction_intent is None:
        created_action_receipt.program_impl_instruction_intent = intent_instruction

    if (
        program_turn_instruction.action_receipt is not None
        and program_turn_instruction.action_receipt.id != created_action_receipt.id
    ):
        raise RuntimeError(
            "ProgramTurnInstruction.record_action receipt mismatch for existing slot: "
            f"program_turn_instruction_id={program_turn_instruction_id}"
        )
    program_turn_instruction.action_receipt = created_action_receipt
    return created_action_receipt
    # --- AWARE: LOGIC END record_action


async def build_via_program_turn(
    program_turn_id: UUID, program_instruction_id: UUID, sequence: int
) -> ProgramTurnInstruction:
    """
    Create a deterministic ProgramTurnInstruction for `(program_instruction_id, sequence)`.
    """

    # --- AWARE: LOGIC START build_via_program_turn
    if sequence < 0:
        raise RuntimeError("ProgramTurnInstruction.build_via_program_turn requires sequence >= 0")

    instruction_assoc_id = uuid5(
        NAMESPACE_URL,
        "aware:program_turn_instruction:" f"{program_turn_id}:{program_instruction_id}:{int(sequence)}",
    )

    session = current_handler_session()
    program_instruction = session.imap_get(ProgramImplInstruction, program_instruction_id)
    existing = session.imap_get(ProgramTurnInstruction, instruction_assoc_id)
    if existing is not None:
        if (
            existing.program_turn_id != program_turn_id
            or existing.program_instruction_id != program_instruction_id
            or existing.sequence != int(sequence)
        ):
            raise RuntimeError(
                "ProgramTurnInstruction.build_via_program_turn payload mismatch for existing association: "
                f"program_turn_instruction_id={instruction_assoc_id}"
            )
        if existing.program_instruction is None and program_instruction is not None:
            existing.program_instruction = program_instruction
        return existing

    return ProgramTurnInstruction(
        id=instruction_assoc_id,
        program_turn_id=program_turn_id,
        program_instruction_id=program_instruction_id,
        program_instruction=program_instruction,
        sequence=int(sequence),
    )
    # --- AWARE: LOGIC END build_via_program_turn
