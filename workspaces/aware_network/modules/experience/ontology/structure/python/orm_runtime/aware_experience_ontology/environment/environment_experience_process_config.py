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

if TYPE_CHECKING:
    from aware_environment_ontology.process.process_config import ProcessConfig
    from aware_experience_ontology.environment.environment_experience_thread_config import (
        EnvironmentExperienceThreadConfig,
    )


class EnvironmentExperienceProcessConfig(ORMModel):
    """
    Experience config bridge for one Environment ProcessConfig.
    Contract:
    - Environment owns the ProcessConfig topology object.
    - Experience owns only the process-level participation config over that
    Environment object.
    - This class never constructs ProcessConfig or runtime Process instances.
    """

    # Relationships
    process_config: ProcessConfig | None = Field(default=None)
    thread_configs: list[EnvironmentExperienceThreadConfig] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    key: str
    narrative: str | None = Field(default=None)
    position: int | None = Field(default=None)
    title: str | None = Field(default=None)

    # Foreign Keys
    environment_experience_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProfileConfig.process_configs"
    )
    process_config_id: UUID = Field(description="Foreign key for EnvironmentExperienceProcessConfig.process_config")

    async def add_thread_config(
        self,
        thread_config_id: UUID,
        key: str,
        title: str | None = None,
        description: str | None = None,
        position: int | None = None,
        narrative: str | None = None,
        intent: str | None = None,
    ) -> EnvironmentExperienceThreadConfig:
        """
        Attach one Experience config bridge for an Environment ThreadConfig.

        Contract:
        - `thread_config_id` references Environment-owned topology.
        - This function never constructs ThreadConfig.
        - Program and action semantics are attached under the thread config bridge.
        """

        payload = {
            "thread_config_id": thread_config_id,
            "key": key,
            "title": title,
            "description": description,
            "position": position,
            "narrative": narrative,
            "intent": intent,
        }
        result = await invoke_instance(orm_model=self, function_name="add_thread_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.environment_experience_thread_config import (
            EnvironmentExperienceThreadConfig,
        )

        if isinstance(value, EnvironmentExperienceThreadConfig):
            return value
        return EnvironmentExperienceThreadConfig.validate_invocation_value(value)

    @classmethod
    async def build_via_environment_experience_profile_config(
        cls,
        environment_experience_profile_config_id: UUID,
        process_config_id: UUID,
        key: str,
        title: str | None = None,
        description: str | None = None,
        position: int | None = None,
        narrative: str | None = None,
        intent: str | None = None,
    ) -> EnvironmentExperienceProcessConfig:
        """
        Construct one Experience process config bridge.

        Contract:
        - Identity is derived from parent profile plus `(process_config_id, key)`.
        - `process_config_id` references Environment ProcessConfig topology truth.
        """

        payload = {
            "environment_experience_profile_config_id": environment_experience_profile_config_id,
            "process_config_id": process_config_id,
            "key": key,
            "title": title,
            "description": description,
            "position": position,
            "narrative": narrative,
            "intent": intent,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_experience_profile_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentExperienceProcessConfig):
            return value
        return EnvironmentExperienceProcessConfig.validate_invocation_value(value)


class EnvironmentExperienceProcessConfigAddThreadConfigInput(BaseModel):
    thread_config_id: UUID
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class EnvironmentExperienceProcessConfigAddThreadConfigOutput(BaseModel):
    value: EnvironmentExperienceThreadConfig


class EnvironmentExperienceProcessConfigBuildViaEnvironmentExperienceProfileConfigInput(BaseModel):
    environment_experience_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProfileConfig.process_configs"
    )
    process_config_id: UUID
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class EnvironmentExperienceProcessConfigBuildViaEnvironmentExperienceProfileConfigOutput(BaseModel):
    value: EnvironmentExperienceProcessConfig


FUNCTIONS = {
    "EnvironmentExperienceProcessConfig": {
        "add_thread_config": {
            "canonical": {
                "name": "add_thread_config",
                "description": "Attach one Experience config bridge for an Environment ThreadConfig.\n\nContract:\n- `thread_config_id` references Environment-owned topology.\n- This function never constructs ThreadConfig.\n- Program and action semantics are attached under the thread config bridge.",
                "is_constructor": False,
            },
            "input": EnvironmentExperienceProcessConfigAddThreadConfigInput,
            "output": EnvironmentExperienceProcessConfigAddThreadConfigOutput,
        },
        "build_via_environment_experience_profile_config": {
            "canonical": {
                "name": "build_via_environment_experience_profile_config",
                "description": "Construct one Experience process config bridge.\n\nContract:\n- Identity is derived from parent profile plus `(process_config_id, key)`.\n- `process_config_id` references Environment ProcessConfig topology truth.",
                "is_constructor": True,
            },
            "input": EnvironmentExperienceProcessConfigBuildViaEnvironmentExperienceProfileConfigInput,
            "output": EnvironmentExperienceProcessConfigBuildViaEnvironmentExperienceProfileConfigOutput,
        },
    },
}

__all__ = [
    "EnvironmentExperienceProcessConfig",
    "EnvironmentExperienceProcessConfigAddThreadConfigInput",
    "EnvironmentExperienceProcessConfigAddThreadConfigOutput",
    "EnvironmentExperienceProcessConfigBuildViaEnvironmentExperienceProfileConfigInput",
    "EnvironmentExperienceProcessConfigBuildViaEnvironmentExperienceProfileConfigOutput",
    "FUNCTIONS",
]
