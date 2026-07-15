from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.program_config_port import ProgramConfigPort


class ProgramImplInstructionBind(ORMModel):
    """
    Program branch+view context selection step.
    Contract:
    - `program_config_port` selects branch connectivity contract.
    - `view_key` selects representation contract.
    - No stable-id resolution occurs in config; runtime resolves at turn execution.
    """

    # Relationships
    program_config_port: ProgramConfigPort | None = Field(default=None, exclude=True)

    # Attributes
    is_active: bool = Field(default=True)
    view_key: str

    # Foreign Keys
    program_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for ProgramImplInstruction.instruction_bind"
    )
    program_config_port_id: UUID = Field(description="Foreign key for ProgramImplInstructionBind.program_config_port")
