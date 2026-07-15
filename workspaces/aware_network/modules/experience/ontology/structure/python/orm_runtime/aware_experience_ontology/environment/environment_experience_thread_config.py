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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_environment_ontology.thread.thread_config import ThreadConfig
    from aware_experience_ontology.environment.environment_experience_program import EnvironmentExperienceProgram
    from aware_experience_ontology.environment.environment_experience_program_apply import (
        EnvironmentExperienceProgramApply,
    )


class EnvironmentExperienceThreadConfig(ORMModel):
    """
    Experience config bridge for one Environment ThreadConfig.
    Contract:
    - Environment owns ThreadConfig topology and hosted projection/layout
    availability.
    - Experience owns thread-scoped programs, program apply declarations, and
    later action/event participation over that stable ThreadConfig.
    - This class never constructs ThreadConfig or runtime Thread instances.
    """

    # Relationships
    thread_config: ThreadConfig | None = Field(default=None)
    programs: list[EnvironmentExperienceProgram] = Field(default_factory=list)
    program_applies: list[EnvironmentExperienceProgramApply] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    key: str
    narrative: str | None = Field(default=None)
    position: int | None = Field(default=None)
    title: str | None = Field(default=None)

    # Foreign Keys
    environment_experience_process_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProcessConfig.thread_configs"
    )
    thread_config_id: UUID = Field(description="Foreign key for EnvironmentExperienceThreadConfig.thread_config")

    async def add_program(self, program_config_id: UUID) -> EnvironmentExperienceProgram:
        """Attach one ProgramConfig association edge under this thread config bridge."""

        payload = {"program_config_id": program_config_id}
        result = await invoke_instance(orm_model=self, function_name="add_program", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.environment_experience_program import EnvironmentExperienceProgram

        if isinstance(value, EnvironmentExperienceProgram):
            return value
        return EnvironmentExperienceProgram.validate_invocation_value(value)

    async def add_program_apply(
        self,
        program_config_id: UUID,
        key: str,
        phase: str = "bootstrap",
        position: int | None = None,
        message: str | None = None,
        symbols: JsonObject = {},
    ) -> EnvironmentExperienceProgramApply:
        """
        Attach one thread-scoped seed/apply declaration.

        Contract:
        - `program_config_id` should already be installed in `programs`.
        - Represents config-only apply intent; it does not execute the program.
        - Experience runtime later maps this declaration to `run_program`.
        """

        payload = {
            "program_config_id": program_config_id,
            "key": key,
            "phase": phase,
            "position": position,
            "message": message,
            "symbols": symbols,
        }
        result = await invoke_instance(orm_model=self, function_name="add_program_apply", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.environment_experience_program_apply import (
            EnvironmentExperienceProgramApply,
        )

        if isinstance(value, EnvironmentExperienceProgramApply):
            return value
        return EnvironmentExperienceProgramApply.validate_invocation_value(value)

    @classmethod
    async def build_via_environment_experience_process_config(
        cls,
        environment_experience_process_config_id: UUID,
        thread_config_id: UUID,
        key: str,
        title: str | None = None,
        description: str | None = None,
        position: int | None = None,
        narrative: str | None = None,
        intent: str | None = None,
    ) -> EnvironmentExperienceThreadConfig:
        """
        Construct one Experience thread config bridge.

        Contract:
        - Identity is derived from parent process bridge plus `(thread_config_id, key)`.
        - `thread_config_id` references Environment ThreadConfig topology truth.
        """

        payload = {
            "environment_experience_process_config_id": environment_experience_process_config_id,
            "thread_config_id": thread_config_id,
            "key": key,
            "title": title,
            "description": description,
            "position": position,
            "narrative": narrative,
            "intent": intent,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_experience_process_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentExperienceThreadConfig):
            return value
        return EnvironmentExperienceThreadConfig.validate_invocation_value(value)


class EnvironmentExperienceThreadConfigAddProgramInput(BaseModel):
    program_config_id: UUID


class EnvironmentExperienceThreadConfigAddProgramOutput(BaseModel):
    value: EnvironmentExperienceProgram


class EnvironmentExperienceThreadConfigAddProgramApplyInput(BaseModel):
    program_config_id: UUID
    key: str
    phase: str = Field(default="bootstrap")
    position: int | None = Field(default=None)
    message: str | None = Field(default=None)
    symbols: JsonObject = Field(default_factory=JsonObject)


class EnvironmentExperienceThreadConfigAddProgramApplyOutput(BaseModel):
    value: EnvironmentExperienceProgramApply


class EnvironmentExperienceThreadConfigBuildViaEnvironmentExperienceProcessConfigInput(BaseModel):
    environment_experience_process_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProcessConfig.thread_configs"
    )
    thread_config_id: UUID
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class EnvironmentExperienceThreadConfigBuildViaEnvironmentExperienceProcessConfigOutput(BaseModel):
    value: EnvironmentExperienceThreadConfig


FUNCTIONS = {
    "EnvironmentExperienceThreadConfig": {
        "add_program": {
            "canonical": {
                "name": "add_program",
                "description": "Attach one ProgramConfig association edge under this thread config bridge.",
                "is_constructor": False,
            },
            "input": EnvironmentExperienceThreadConfigAddProgramInput,
            "output": EnvironmentExperienceThreadConfigAddProgramOutput,
        },
        "add_program_apply": {
            "canonical": {
                "name": "add_program_apply",
                "description": "Attach one thread-scoped seed/apply declaration.\n\nContract:\n- `program_config_id` should already be installed in `programs`.\n- Represents config-only apply intent; it does not execute the program.\n- Experience runtime later maps this declaration to `run_program`.",
                "is_constructor": False,
            },
            "input": EnvironmentExperienceThreadConfigAddProgramApplyInput,
            "output": EnvironmentExperienceThreadConfigAddProgramApplyOutput,
        },
        "build_via_environment_experience_process_config": {
            "canonical": {
                "name": "build_via_environment_experience_process_config",
                "description": "Construct one Experience thread config bridge.\n\nContract:\n- Identity is derived from parent process bridge plus `(thread_config_id, key)`.\n- `thread_config_id` references Environment ThreadConfig topology truth.",
                "is_constructor": True,
            },
            "input": EnvironmentExperienceThreadConfigBuildViaEnvironmentExperienceProcessConfigInput,
            "output": EnvironmentExperienceThreadConfigBuildViaEnvironmentExperienceProcessConfigOutput,
        },
    },
}

__all__ = [
    "EnvironmentExperienceThreadConfig",
    "EnvironmentExperienceThreadConfigAddProgramInput",
    "EnvironmentExperienceThreadConfigAddProgramOutput",
    "EnvironmentExperienceThreadConfigAddProgramApplyInput",
    "EnvironmentExperienceThreadConfigAddProgramApplyOutput",
    "EnvironmentExperienceThreadConfigBuildViaEnvironmentExperienceProcessConfigInput",
    "EnvironmentExperienceThreadConfigBuildViaEnvironmentExperienceProcessConfigOutput",
    "FUNCTIONS",
]
