from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_experience_ontology.program.impl.program_impl_instruction_invoke import ProgramImplInstructionInvoke
    from aware_experience_ontology.program.program_actor_role import ProgramActorRole
    from aware_experience_ontology.program.program_turn_instruction_invoke_attribute_config import (
        ProgramTurnInstructionInvokeAttributeConfig,
    )
    from aware_experience_ontology.projection.projection_experience_node_class_identity import (
        ProjectionExperienceNodeClassIdentity,
    )


class ProgramTurnInstructionInvoke(ORMModel):
    """
    Canonical invoke execution receipt under one ProgramTurnInstruction.
    Contract:
    - Captures one invoke execution for one program instruction.
    - Freezes actor-role attribution and optional resolved target node-class identity.
    """

    # Relationships
    program_impl_instruction_invoke: ProgramImplInstructionInvoke | None = Field(default=None, exclude=True)
    program_actor_role: ProgramActorRole | None = Field(default=None, exclude=True)
    projection_experience_node_class_identity: ProjectionExperienceNodeClassIdentity | None = Field(
        default=None, exclude=True
    )
    attribute_config_receipts: list[ProgramTurnInstructionInvokeAttributeConfig] = Field(
        default_factory=list, exclude=True
    )

    # Foreign Keys
    program_turn_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for ProgramTurnInstruction.invoke_receipt"
    )
    program_impl_instruction_invoke_id: UUID = Field(
        description="Foreign key for ProgramTurnInstructionInvoke.program_impl_instruction_invoke"
    )
    program_actor_role_id: UUID = Field(description="Foreign key for ProgramTurnInstructionInvoke.program_actor_role")
    projection_experience_node_class_identity_id: UUID = Field(
        description="Foreign key for ProgramTurnInstructionInvoke.projection_experience_node_class_identity"
    )

    async def add_attribute_config_receipt(
        self, program_impl_instruction_invoke_attribute_config_id: UUID
    ) -> ProgramTurnInstructionInvokeAttributeConfig:
        """Record one deterministic invoke-argument receipt row for this invoke execution."""

        payload = {
            "program_impl_instruction_invoke_attribute_config_id": program_impl_instruction_invoke_attribute_config_id
        }
        result = await invoke_instance(orm_model=self, function_name="add_attribute_config_receipt", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_turn_instruction_invoke_attribute_config import (
            ProgramTurnInstructionInvokeAttributeConfig,
        )

        if isinstance(value, ProgramTurnInstructionInvokeAttributeConfig):
            return value
        return ProgramTurnInstructionInvokeAttributeConfig.validate_invocation_value(value)

    @classmethod
    async def build_via_program_turn_instruction(
        cls,
        program_turn_instruction_id: UUID,
        program_impl_instruction_invoke_id: UUID,
        program_actor_role_id: UUID,
        projection_experience_node_class_identity_id: UUID,
    ) -> ProgramTurnInstructionInvoke:
        """Create deterministic ProgramTurnInstructionInvoke under ProgramTurnInstruction."""

        payload = {
            "program_turn_instruction_id": program_turn_instruction_id,
            "program_impl_instruction_invoke_id": program_impl_instruction_invoke_id,
            "program_actor_role_id": program_actor_role_id,
            "projection_experience_node_class_identity_id": projection_experience_node_class_identity_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_turn_instruction", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramTurnInstructionInvoke):
            return value
        return ProgramTurnInstructionInvoke.validate_invocation_value(value)


class ProgramTurnInstructionInvokeAddAttributeConfigReceiptInput(BaseModel):
    program_impl_instruction_invoke_attribute_config_id: UUID


class ProgramTurnInstructionInvokeAddAttributeConfigReceiptOutput(BaseModel):
    value: ProgramTurnInstructionInvokeAttributeConfig


class ProgramTurnInstructionInvokeBuildViaProgramTurnInstructionInput(BaseModel):
    program_turn_instruction_id: UUID = Field(description="Foreign key for ProgramTurnInstruction.invoke_receipt")
    program_impl_instruction_invoke_id: UUID
    program_actor_role_id: UUID
    projection_experience_node_class_identity_id: UUID


class ProgramTurnInstructionInvokeBuildViaProgramTurnInstructionOutput(BaseModel):
    value: ProgramTurnInstructionInvoke


FUNCTIONS = {
    "ProgramTurnInstructionInvoke": {
        "add_attribute_config_receipt": {
            "canonical": {
                "name": "add_attribute_config_receipt",
                "description": "Record one deterministic invoke-argument receipt row for this invoke execution.",
                "is_constructor": False,
            },
            "input": ProgramTurnInstructionInvokeAddAttributeConfigReceiptInput,
            "output": ProgramTurnInstructionInvokeAddAttributeConfigReceiptOutput,
        },
        "build_via_program_turn_instruction": {
            "canonical": {
                "name": "build_via_program_turn_instruction",
                "description": "Create deterministic ProgramTurnInstructionInvoke under ProgramTurnInstruction.",
                "is_constructor": True,
            },
            "input": ProgramTurnInstructionInvokeBuildViaProgramTurnInstructionInput,
            "output": ProgramTurnInstructionInvokeBuildViaProgramTurnInstructionOutput,
        },
    },
}

__all__ = [
    "ProgramTurnInstructionInvoke",
    "ProgramTurnInstructionInvokeAddAttributeConfigReceiptInput",
    "ProgramTurnInstructionInvokeAddAttributeConfigReceiptOutput",
    "ProgramTurnInstructionInvokeBuildViaProgramTurnInstructionInput",
    "ProgramTurnInstructionInvokeBuildViaProgramTurnInstructionOutput",
    "FUNCTIONS",
]
