from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.impl.program_impl_instruction_invoke import (
        ProgramImplInstructionInvoke,
    )
    from aware_experience_ontology_orm_models.program.program_actor_role import ProgramActorRole
    from aware_experience_ontology_orm_models.program.program_turn_instruction_invoke_attribute_config import (
        ProgramTurnInstructionInvokeAttributeConfig,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_node_class_identity import (
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
