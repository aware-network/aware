from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.impl.program_impl_instruction_invoke_attribute_config import (
        ProgramImplInstructionInvokeAttributeConfig,
    )


class ProgramTurnInstructionInvokeAttributeConfig(BaseModel):
    """
    Canonical invoke-argument execution receipt under one ProgramTurnInstructionInvoke.
    Contract:
    - Captures one executed invoke argument contract row.
    - Enables replay parity checks for invoke argument coverage.
    """

    # Relationships
    program_impl_instruction_invoke_attribute_config: ProgramImplInstructionInvokeAttributeConfig | None = Field(
        default=None
    )
