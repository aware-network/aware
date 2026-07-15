from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.program_config import ProgramConfig


class EnvironmentExperienceProgramApply(ORMModel):
    """
    Canonical thread-config-owned seed/apply declaration for an installed program.
    Purpose:
    - Declare that one installed program should later be auto-applied by an
    Experience runtime profile-apply phase.
    - Keep execution arguments configuration-owned while leaving actual
    `run_program` invocation to Experience runtime policy.
    """

    # Relationships
    program_config: ProgramConfig | None = Field(default=None, exclude=True)

    # Attributes
    key: str
    phase: str = Field(
        default="bootstrap", description="Execution phase bucket later interpreted by runtime/environment."
    )
    position: int | None = Field(default=None)
    message: str | None = Field(default=None)
    symbols: JsonObject = Field(default_factory=JsonObject)

    # Foreign Keys
    environment_experience_thread_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceThreadConfig.program_applies"
    )
    program_config_id: UUID = Field(description="Foreign key for EnvironmentExperienceProgramApply.program_config")
