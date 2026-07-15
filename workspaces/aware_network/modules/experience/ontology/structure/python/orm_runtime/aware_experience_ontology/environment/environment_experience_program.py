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
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_experience_ontology.program.program_config import ProgramConfig


class EnvironmentExperienceProgram(ORMModel):
    """
    Canonical installed program contract for an EnvironmentExperienceThreadConfig.
    Purpose:
    - Declare which ProgramConfig contracts are available under one experience
    thread config bridge.
    - Keep install/availability separate from later seed/apply execution declarations.
    """

    # Relationships
    program_config: ProgramConfig | None = Field(default=None, exclude=True)

    # Foreign Keys
    environment_experience_thread_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceThreadConfig.programs"
    )
    program_config_id: UUID = Field(description="Foreign key for EnvironmentExperienceProgram.program_config")

    @classmethod
    async def build_via_environment_experience_thread_config(
        cls, environment_experience_thread_config_id: UUID, program_config_id: UUID
    ) -> EnvironmentExperienceProgram:
        """
        Construct the canonical EnvironmentExperienceProgram for an environment territory.

        Contract:
        - Identity is derived from `(environment_experience_thread_config_id, program_config_id)`.
        - Constructor does not mutate EnvironmentExperienceThreadConfig directly.
        """

        payload = {
            "environment_experience_thread_config_id": environment_experience_thread_config_id,
            "program_config_id": program_config_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_experience_thread_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentExperienceProgram):
            return value
        return EnvironmentExperienceProgram.validate_invocation_value(value)


class EnvironmentExperienceProgramBuildViaEnvironmentExperienceThreadConfigInput(BaseModel):
    environment_experience_thread_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceThreadConfig.programs"
    )
    program_config_id: UUID


class EnvironmentExperienceProgramBuildViaEnvironmentExperienceThreadConfigOutput(BaseModel):
    value: EnvironmentExperienceProgram


FUNCTIONS = {
    "EnvironmentExperienceProgram": {
        "build_via_environment_experience_thread_config": {
            "canonical": {
                "name": "build_via_environment_experience_thread_config",
                "description": "Construct the canonical EnvironmentExperienceProgram for an environment territory.\n\nContract:\n- Identity is derived from `(environment_experience_thread_config_id, program_config_id)`.\n- Constructor does not mutate EnvironmentExperienceThreadConfig directly.",
                "is_constructor": True,
            },
            "input": EnvironmentExperienceProgramBuildViaEnvironmentExperienceThreadConfigInput,
            "output": EnvironmentExperienceProgramBuildViaEnvironmentExperienceThreadConfigOutput,
        },
    },
}

__all__ = [
    "EnvironmentExperienceProgram",
    "EnvironmentExperienceProgramBuildViaEnvironmentExperienceThreadConfigInput",
    "EnvironmentExperienceProgramBuildViaEnvironmentExperienceThreadConfigOutput",
    "FUNCTIONS",
]
