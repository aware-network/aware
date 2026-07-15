from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.program_config import ProgramConfig


class EnvironmentExperienceProgramApply(BaseModel):
    """
    Canonical thread-config-owned seed/apply declaration for an installed program.
    Purpose:
    - Declare that one installed program should later be auto-applied by an
    Experience runtime profile-apply phase.
    - Keep execution arguments configuration-owned while leaving actual
    `run_program` invocation to Experience runtime policy.
    """

    # Relationships
    program_config: ProgramConfig | None = Field(default=None)

    # Attributes
    key: str
    phase: str = Field(
        default="bootstrap", description="Execution phase bucket later interpreted by runtime/environment."
    )
    position: int | None = Field(default=None)
    message: str | None = Field(default=None)
    symbols: JsonObject = Field(default_factory=JsonObject)
