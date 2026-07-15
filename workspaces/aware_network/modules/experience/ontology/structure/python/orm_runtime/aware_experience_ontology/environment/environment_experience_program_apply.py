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

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology.program.program_config import ProgramConfig


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

    @classmethod
    async def build_via_environment_experience_thread_config(
        cls,
        environment_experience_thread_config_id: UUID,
        program_config_id: UUID,
        key: str,
        phase: str = "bootstrap",
        position: int | None = None,
        message: str | None = None,
        symbols: JsonObject = {},
    ) -> EnvironmentExperienceProgramApply:
        """
        Construct the canonical EnvironmentExperienceProgramApply declaration.

        Contract:
        - Identity is derived from `(environment_experience_thread_config_id, key)`.
        - `program_config_id` should reference one installed thread config program.
        - This class is configuration-only; actual execution happens later via
          Experience-owned `run_program`.
        """

        payload = {
            "environment_experience_thread_config_id": environment_experience_thread_config_id,
            "program_config_id": program_config_id,
            "key": key,
            "phase": phase,
            "position": position,
            "message": message,
            "symbols": symbols,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_experience_thread_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentExperienceProgramApply):
            return value
        return EnvironmentExperienceProgramApply.validate_invocation_value(value)


class EnvironmentExperienceProgramApplyBuildViaEnvironmentExperienceThreadConfigInput(BaseModel):
    environment_experience_thread_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceThreadConfig.program_applies"
    )
    program_config_id: UUID
    key: str
    phase: str = Field(default="bootstrap")
    position: int | None = Field(default=None)
    message: str | None = Field(default=None)
    symbols: JsonObject = Field(default_factory=JsonObject)


class EnvironmentExperienceProgramApplyBuildViaEnvironmentExperienceThreadConfigOutput(BaseModel):
    value: EnvironmentExperienceProgramApply


FUNCTIONS = {
    "EnvironmentExperienceProgramApply": {
        "build_via_environment_experience_thread_config": {
            "canonical": {
                "name": "build_via_environment_experience_thread_config",
                "description": "Construct the canonical EnvironmentExperienceProgramApply declaration.\n\nContract:\n- Identity is derived from `(environment_experience_thread_config_id, key)`.\n- `program_config_id` should reference one installed thread config program.\n- This class is configuration-only; actual execution happens later via\n  Experience-owned `run_program`.",
                "is_constructor": True,
            },
            "input": EnvironmentExperienceProgramApplyBuildViaEnvironmentExperienceThreadConfigInput,
            "output": EnvironmentExperienceProgramApplyBuildViaEnvironmentExperienceThreadConfigOutput,
        },
    },
}

__all__ = [
    "EnvironmentExperienceProgramApply",
    "EnvironmentExperienceProgramApplyBuildViaEnvironmentExperienceThreadConfigInput",
    "EnvironmentExperienceProgramApplyBuildViaEnvironmentExperienceThreadConfigOutput",
    "FUNCTIONS",
]
