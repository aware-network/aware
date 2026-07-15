from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.impl.program_impl_instruction_invoke import ProgramImplInstructionInvoke
    from aware_experience_ontology_dto.program.program_actor_role import ProgramActorRole
    from aware_experience_ontology_dto.program.program_turn_instruction_invoke_attribute_config import (
        ProgramTurnInstructionInvokeAttributeConfig,
    )
    from aware_experience_ontology_dto.projection.projection_experience_node_class_identity import (
        ProjectionExperienceNodeClassIdentity,
    )


class ProgramTurnInstructionInvoke(BaseModel):
    """
    Canonical invoke execution receipt under one ProgramTurnInstruction.
    Contract:
    - Captures one invoke execution for one program instruction.
    - Freezes actor-role attribution and optional resolved target node-class identity.
    """

    # Relationships
    program_impl_instruction_invoke: ProgramImplInstructionInvoke | None = Field(default=None)
    program_actor_role: ProgramActorRole | None = Field(default=None)
    projection_experience_node_class_identity: ProjectionExperienceNodeClassIdentity | None = Field(default=None)
    attribute_config_receipts: list[ProgramTurnInstructionInvokeAttributeConfig] = Field(default_factory=list)
