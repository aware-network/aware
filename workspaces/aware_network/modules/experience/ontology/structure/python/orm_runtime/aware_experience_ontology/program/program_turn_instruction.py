from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology
from aware_experience_ontology.program.program_enums import (
    ProgramTurnDecisionReason,
    ProgramTurnTransition,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_experience_ontology.program.impl.program_impl_instruction import ProgramImplInstruction
    from aware_experience_ontology.program.program_turn_decision import ProgramTurnInstructionDecision
    from aware_experience_ontology.program.program_turn_instruction_action import ProgramTurnInstructionAction
    from aware_experience_ontology.program.program_turn_instruction_bind import ProgramTurnInstructionBind
    from aware_experience_ontology.program.program_turn_instruction_invoke import ProgramTurnInstructionInvoke


class ProgramTurnInstruction(ORMModel):
    """
    Canonical per-turn executed instruction receipt.
    Contract:
    - Anchors one executed `ProgramImplInstruction` under one `ProgramTurn`.
    - Owns decision receipts as child membership (`decisions`).
    """

    # Relationships
    program_instruction: ProgramImplInstruction | None = Field(default=None, exclude=True)
    bind_receipt: ProgramTurnInstructionBind | None = Field(default=None, exclude=True)
    invoke_receipt: ProgramTurnInstructionInvoke | None = Field(default=None, exclude=True)
    action_receipt: ProgramTurnInstructionAction | None = Field(default=None, exclude=True)
    decisions: list[ProgramTurnInstructionDecision] = Field(default_factory=list, exclude=True)

    # Attributes
    sequence: int

    # Foreign Keys
    program_turn_id: UUID = Field(description="Foreign key for ProgramTurn.instructions")
    program_instruction_id: UUID = Field(description="Foreign key for ProgramTurnInstruction.program_instruction")

    async def record_decision(
        self,
        transition: ProgramTurnTransition,
        reason: ProgramTurnDecisionReason,
        step_index: int,
        total_steps: int,
        invokes_in_turn: int = 0,
        elapsed_ms_in_turn: int = 0,
        awaiting_external_signal: bool = False,
        instruction_failed: bool = False,
    ) -> ProgramTurnInstructionDecision:
        """Record one typed decision checkpoint for this instruction execution."""

        payload = {
            "transition": transition,
            "reason": reason,
            "step_index": step_index,
            "total_steps": total_steps,
            "invokes_in_turn": invokes_in_turn,
            "elapsed_ms_in_turn": elapsed_ms_in_turn,
            "awaiting_external_signal": awaiting_external_signal,
            "instruction_failed": instruction_failed,
        }
        result = await invoke_instance(orm_model=self, function_name="record_decision", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_turn_decision import ProgramTurnInstructionDecision

        if isinstance(value, ProgramTurnInstructionDecision):
            return value
        return ProgramTurnInstructionDecision.validate_invocation_value(value)

    async def record_bind(
        self,
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

        payload = {
            "program_impl_instruction_bind_id": program_impl_instruction_bind_id,
            "object_instance_graph_branch_id": object_instance_graph_branch_id,
            "projection_experience_view_id": projection_experience_view_id,
        }
        result = await invoke_instance(orm_model=self, function_name="record_bind", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_turn_instruction_bind import ProgramTurnInstructionBind

        if isinstance(value, ProgramTurnInstructionBind):
            return value
        return ProgramTurnInstructionBind.validate_invocation_value(value)

    async def record_invoke(
        self,
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

        payload = {
            "program_impl_instruction_invoke_id": program_impl_instruction_invoke_id,
            "program_actor_role_id": program_actor_role_id,
            "projection_experience_node_class_identity_id": projection_experience_node_class_identity_id,
        }
        result = await invoke_instance(orm_model=self, function_name="record_invoke", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_turn_instruction_invoke import ProgramTurnInstructionInvoke

        if isinstance(value, ProgramTurnInstructionInvoke):
            return value
        return ProgramTurnInstructionInvoke.validate_invocation_value(value)

    async def record_action(
        self,
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

        payload = {
            "program_impl_instruction_intent_id": program_impl_instruction_intent_id,
            "action_config_id": action_config_id,
            "event_config_id": event_config_id,
            "action_intent_id": action_intent_id,
            "intent_key": intent_key,
        }
        result = await invoke_instance(orm_model=self, function_name="record_action", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_turn_instruction_action import ProgramTurnInstructionAction

        if isinstance(value, ProgramTurnInstructionAction):
            return value
        return ProgramTurnInstructionAction.validate_invocation_value(value)

    @classmethod
    async def build_via_program_turn(
        cls, program_turn_id: UUID, program_instruction_id: UUID, sequence: int
    ) -> ProgramTurnInstruction:
        """Create a deterministic ProgramTurnInstruction for `(program_instruction_id, sequence)`."""

        payload = {
            "program_turn_id": program_turn_id,
            "program_instruction_id": program_instruction_id,
            "sequence": sequence,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_program_turn", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramTurnInstruction):
            return value
        return ProgramTurnInstruction.validate_invocation_value(value)


class ProgramTurnInstructionRecordDecisionInput(BaseModel):
    transition: ProgramTurnTransition
    reason: ProgramTurnDecisionReason
    step_index: int
    total_steps: int
    invokes_in_turn: int = Field(default=0)
    elapsed_ms_in_turn: int = Field(default=0)
    awaiting_external_signal: bool = Field(default=False)
    instruction_failed: bool = Field(default=False)


class ProgramTurnInstructionRecordDecisionOutput(BaseModel):
    value: ProgramTurnInstructionDecision


class ProgramTurnInstructionRecordBindInput(BaseModel):
    program_impl_instruction_bind_id: UUID
    object_instance_graph_branch_id: UUID
    projection_experience_view_id: UUID


class ProgramTurnInstructionRecordBindOutput(BaseModel):
    value: ProgramTurnInstructionBind


class ProgramTurnInstructionRecordInvokeInput(BaseModel):
    program_impl_instruction_invoke_id: UUID
    program_actor_role_id: UUID
    projection_experience_node_class_identity_id: UUID


class ProgramTurnInstructionRecordInvokeOutput(BaseModel):
    value: ProgramTurnInstructionInvoke


class ProgramTurnInstructionRecordActionInput(BaseModel):
    program_impl_instruction_intent_id: UUID
    action_config_id: UUID
    event_config_id: UUID
    action_intent_id: UUID
    intent_key: str


class ProgramTurnInstructionRecordActionOutput(BaseModel):
    value: ProgramTurnInstructionAction


class ProgramTurnInstructionBuildViaProgramTurnInput(BaseModel):
    program_turn_id: UUID = Field(description="Foreign key for ProgramTurn.instructions")
    program_instruction_id: UUID
    sequence: int


class ProgramTurnInstructionBuildViaProgramTurnOutput(BaseModel):
    value: ProgramTurnInstruction


FUNCTIONS = {
    "ProgramTurnInstruction": {
        "record_decision": {
            "canonical": {
                "name": "record_decision",
                "description": "Record one typed decision checkpoint for this instruction execution.",
                "is_constructor": False,
            },
            "input": ProgramTurnInstructionRecordDecisionInput,
            "output": ProgramTurnInstructionRecordDecisionOutput,
        },
        "record_bind": {
            "canonical": {
                "name": "record_bind",
                "description": "Record one bind execution receipt for this instruction.\n\nContract:\n- Captures resolved branch/view runtime bindings as commit-backed facts.\n- Node alias resolution receipts are attached under ProgramTurnInstructionBind.",
                "is_constructor": False,
            },
            "input": ProgramTurnInstructionRecordBindInput,
            "output": ProgramTurnInstructionRecordBindOutput,
        },
        "record_invoke": {
            "canonical": {
                "name": "record_invoke",
                "description": "Record one invoke execution receipt for this instruction.\n\nContract:\n- Captures resolved actor-role attribution and target identity context.\n- Invoke argument/value receipts remain child rails under ProgramTurnInstructionInvoke.",
                "is_constructor": False,
            },
            "input": ProgramTurnInstructionRecordInvokeInput,
            "output": ProgramTurnInstructionRecordInvokeOutput,
        },
        "record_action": {
            "canonical": {
                "name": "record_action",
                "description": "Record one program-declared ActionIntent receipt for this instruction.\n\nContract:\n- Captures program provenance above Reactivity's actor-free\n  ActionIntent primitive.\n- Does not dispatch or fulfill the action.",
                "is_constructor": False,
            },
            "input": ProgramTurnInstructionRecordActionInput,
            "output": ProgramTurnInstructionRecordActionOutput,
        },
        "build_via_program_turn": {
            "canonical": {
                "name": "build_via_program_turn",
                "description": "Create a deterministic ProgramTurnInstruction for `(program_instruction_id, sequence)`.",
                "is_constructor": True,
            },
            "input": ProgramTurnInstructionBuildViaProgramTurnInput,
            "output": ProgramTurnInstructionBuildViaProgramTurnOutput,
        },
    },
}

__all__ = [
    "ProgramTurnInstruction",
    "ProgramTurnInstructionRecordDecisionInput",
    "ProgramTurnInstructionRecordDecisionOutput",
    "ProgramTurnInstructionRecordBindInput",
    "ProgramTurnInstructionRecordBindOutput",
    "ProgramTurnInstructionRecordInvokeInput",
    "ProgramTurnInstructionRecordInvokeOutput",
    "ProgramTurnInstructionRecordActionInput",
    "ProgramTurnInstructionRecordActionOutput",
    "ProgramTurnInstructionBuildViaProgramTurnInput",
    "ProgramTurnInstructionBuildViaProgramTurnOutput",
    "FUNCTIONS",
]
