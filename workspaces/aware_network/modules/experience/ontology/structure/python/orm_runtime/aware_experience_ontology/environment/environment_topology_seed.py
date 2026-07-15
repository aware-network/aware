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
    from aware_experience_ontology.environment.environment_experience_profile_config import (
        EnvironmentExperienceProfileConfig,
    )
    from aware_experience_ontology.environment.environment_topology_process_seed import EnvironmentTopologyProcessSeed


class EnvironmentTopologySeed(ORMModel):
    """
    Experience-owned runtime topology seed.
    Purpose:
    - Keep reusable Environment topology config separate from concrete runtime topology.
    - Provide named genesis/entrypoint recipes that can be selected explicitly.
    """

    # Relationships
    environment_experience_profile_config: EnvironmentExperienceProfileConfig | None = Field(default=None, exclude=True)
    process_seeds: list[EnvironmentTopologyProcessSeed] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    key: str
    narrative: str | None = Field(default=None)
    title: str | None = Field(default=None)

    # Foreign Keys
    environment_experience_id: UUID = Field(description="Foreign key for EnvironmentExperience.topology_seeds")
    environment_experience_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentTopologySeed.environment_experience_profile_config"
    )

    async def add_process_seed(
        self,
        process_config_id: UUID,
        process_key: str,
        key: str | None = None,
        title: str | None = None,
        description: str | None = None,
        position: int | None = None,
        narrative: str | None = None,
        intent: str | None = None,
    ) -> EnvironmentTopologyProcessSeed:
        """Add one runtime Process seed referencing a reusable Environment ProcessConfig."""

        payload = {
            "process_config_id": process_config_id,
            "process_key": process_key,
            "key": key,
            "title": title,
            "description": description,
            "position": position,
            "narrative": narrative,
            "intent": intent,
        }
        result = await invoke_instance(orm_model=self, function_name="add_process_seed", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.environment_topology_process_seed import (
            EnvironmentTopologyProcessSeed,
        )

        if isinstance(value, EnvironmentTopologyProcessSeed):
            return value
        return EnvironmentTopologyProcessSeed.validate_invocation_value(value)

    @classmethod
    async def build_via_environment_experience(
        cls,
        environment_experience_id: UUID,
        environment_experience_profile_config_id: UUID,
        key: str,
        title: str | None = None,
        description: str | None = None,
        narrative: str | None = None,
    ) -> EnvironmentTopologySeed:
        """
        Construct one topology seed under an EnvironmentExperience.

        Contract:
        - Identity is scoped by EnvironmentExperience and seed key.
        - The referenced profile config supplies Experience config over Environment
          ProcessConfig/ThreadConfig contracts.
        - This seed supplies runtime process/thread/layout keys.
        """

        payload = {
            "environment_experience_id": environment_experience_id,
            "environment_experience_profile_config_id": environment_experience_profile_config_id,
            "key": key,
            "title": title,
            "description": description,
            "narrative": narrative,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_experience", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentTopologySeed):
            return value
        return EnvironmentTopologySeed.validate_invocation_value(value)


class EnvironmentTopologySeedAddProcessSeedInput(BaseModel):
    process_config_id: UUID
    process_key: str
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class EnvironmentTopologySeedAddProcessSeedOutput(BaseModel):
    value: EnvironmentTopologyProcessSeed


class EnvironmentTopologySeedBuildViaEnvironmentExperienceInput(BaseModel):
    environment_experience_id: UUID = Field(description="Foreign key for EnvironmentExperience.topology_seeds")
    environment_experience_profile_config_id: UUID
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    narrative: str | None = Field(default=None)


class EnvironmentTopologySeedBuildViaEnvironmentExperienceOutput(BaseModel):
    value: EnvironmentTopologySeed


FUNCTIONS = {
    "EnvironmentTopologySeed": {
        "add_process_seed": {
            "canonical": {
                "name": "add_process_seed",
                "description": "Add one runtime Process seed referencing a reusable Environment ProcessConfig.",
                "is_constructor": False,
            },
            "input": EnvironmentTopologySeedAddProcessSeedInput,
            "output": EnvironmentTopologySeedAddProcessSeedOutput,
        },
        "build_via_environment_experience": {
            "canonical": {
                "name": "build_via_environment_experience",
                "description": "Construct one topology seed under an EnvironmentExperience.\n\nContract:\n- Identity is scoped by EnvironmentExperience and seed key.\n- The referenced profile config supplies Experience config over Environment\n  ProcessConfig/ThreadConfig contracts.\n- This seed supplies runtime process/thread/layout keys.",
                "is_constructor": True,
            },
            "input": EnvironmentTopologySeedBuildViaEnvironmentExperienceInput,
            "output": EnvironmentTopologySeedBuildViaEnvironmentExperienceOutput,
        },
    },
}

__all__ = [
    "EnvironmentTopologySeed",
    "EnvironmentTopologySeedAddProcessSeedInput",
    "EnvironmentTopologySeedAddProcessSeedOutput",
    "EnvironmentTopologySeedBuildViaEnvironmentExperienceInput",
    "EnvironmentTopologySeedBuildViaEnvironmentExperienceOutput",
    "FUNCTIONS",
]
