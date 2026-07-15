from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.impl.program_impl_instruction_invoke_attribute_config import (
        ProgramImplInstructionInvokeAttributeConfig,
    )


class ProgramTurnInstructionInvokeAttributeConfig(ORMModel):
    """
    Canonical invoke-argument execution receipt under one ProgramTurnInstructionInvoke.
    Contract:
    - Captures one executed invoke argument contract row.
    - Enables replay parity checks for invoke argument coverage.
    """

    # Relationships
    program_impl_instruction_invoke_attribute_config: ProgramImplInstructionInvokeAttributeConfig | None = Field(
        default=None, exclude=True
    )

    # Foreign Keys
    program_turn_instruction_invoke_id: UUID = Field(
        description="Foreign key for ProgramTurnInstructionInvoke.attribute_config_receipts"
    )
    program_impl_instruction_invoke_attribute_config_id: UUID = Field(
        description="Foreign key for ProgramTurnInstructionInvokeAttributeConfig.program_impl_instruction_invoke_attribute_config"
    )
