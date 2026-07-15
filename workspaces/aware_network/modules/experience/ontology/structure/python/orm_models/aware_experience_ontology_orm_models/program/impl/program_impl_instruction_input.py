from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.program_config_input_config import ProgramConfigInputConfig


class ProgramImplInstructionInput(ORMModel):
    """Program input as instruction"""

    # Relationships
    program_config_input_config: ProgramConfigInputConfig | None = Field(default=None, exclude=True)

    # Foreign Keys
    program_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for ProgramImplInstruction.instruction_input"
    )
    program_config_input_config_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionInput.program_config_input_config"
    )
