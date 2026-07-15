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
    from aware_experience_ontology.environment.environment_topology_thread_seed import EnvironmentTopologyThreadSeed


class EnvironmentTopologyProcessSeed(ORMModel):
    """Runtime Process seed inside an EnvironmentTopologySeed."""

    # Relationships
    process_config: ProcessConfig | None = Field(default=None, exclude=True)
    thread_seeds: list[EnvironmentTopologyThreadSeed] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    key: str | None = Field(
        default=None, description="Optional seed-local key; defaults to `process_key` in runtime handlers."
    )
    process_key: str = Field(description="Runtime Process.key to create or resolve under Environment.")
    position: int | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    title: str | None = Field(default=None)

    # Foreign Keys
    environment_topology_seed_id: UUID = Field(description="Foreign key for EnvironmentTopologySeed.process_seeds")
    process_config_id: UUID = Field(description="Foreign key for EnvironmentTopologyProcessSeed.process_config")

    async def add_thread_seed(
        self,
        thread_config_id: UUID,
        thread_key: str,
        key: str | None = None,
        title: str | None = None,
        description: str | None = None,
        position: int | None = None,
        is_main: bool = False,
        narrative: str | None = None,
        intent: str | None = None,
    ) -> EnvironmentTopologyThreadSeed:
        """Add one runtime Thread seed referencing a reusable Environment ThreadConfig."""

        payload = {
            "thread_config_id": thread_config_id,
            "thread_key": thread_key,
            "key": key,
            "title": title,
            "description": description,
            "position": position,
            "is_main": is_main,
            "narrative": narrative,
            "intent": intent,
        }
        result = await invoke_instance(orm_model=self, function_name="add_thread_seed", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.environment_topology_thread_seed import EnvironmentTopologyThreadSeed

        if isinstance(value, EnvironmentTopologyThreadSeed):
            return value
        return EnvironmentTopologyThreadSeed.validate_invocation_value(value)

    @classmethod
    async def build_via_environment_topology_seed(
        cls,
        environment_topology_seed_id: UUID,
        process_config_id: UUID,
        process_key: str,
        key: str | None = None,
        title: str | None = None,
        description: str | None = None,
        position: int | None = None,
        narrative: str | None = None,
        intent: str | None = None,
    ) -> EnvironmentTopologyProcessSeed:
        """
        Construct one process seed.

        Contract:
        - `process_config_id` is reusable Environment ProcessConfig truth.
        - `process_key` is runtime instance identity.
        """

        payload = {
            "environment_topology_seed_id": environment_topology_seed_id,
            "process_config_id": process_config_id,
            "process_key": process_key,
            "key": key,
            "title": title,
            "description": description,
            "position": position,
            "narrative": narrative,
            "intent": intent,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_topology_seed", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentTopologyProcessSeed):
            return value
        return EnvironmentTopologyProcessSeed.validate_invocation_value(value)


class EnvironmentTopologyProcessSeedAddThreadSeedInput(BaseModel):
    thread_config_id: UUID
    thread_key: str
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_main: bool = Field(default=False)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class EnvironmentTopologyProcessSeedAddThreadSeedOutput(BaseModel):
    value: EnvironmentTopologyThreadSeed


class EnvironmentTopologyProcessSeedBuildViaEnvironmentTopologySeedInput(BaseModel):
    environment_topology_seed_id: UUID = Field(description="Foreign key for EnvironmentTopologySeed.process_seeds")
    process_config_id: UUID
    process_key: str
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class EnvironmentTopologyProcessSeedBuildViaEnvironmentTopologySeedOutput(BaseModel):
    value: EnvironmentTopologyProcessSeed


FUNCTIONS = {
    "EnvironmentTopologyProcessSeed": {
        "add_thread_seed": {
            "canonical": {
                "name": "add_thread_seed",
                "description": "Add one runtime Thread seed referencing a reusable Environment ThreadConfig.",
                "is_constructor": False,
            },
            "input": EnvironmentTopologyProcessSeedAddThreadSeedInput,
            "output": EnvironmentTopologyProcessSeedAddThreadSeedOutput,
        },
        "build_via_environment_topology_seed": {
            "canonical": {
                "name": "build_via_environment_topology_seed",
                "description": "Construct one process seed.\n\nContract:\n- `process_config_id` is reusable Environment ProcessConfig truth.\n- `process_key` is runtime instance identity.",
                "is_constructor": True,
            },
            "input": EnvironmentTopologyProcessSeedBuildViaEnvironmentTopologySeedInput,
            "output": EnvironmentTopologyProcessSeedBuildViaEnvironmentTopologySeedOutput,
        },
    },
}

__all__ = [
    "EnvironmentTopologyProcessSeed",
    "EnvironmentTopologyProcessSeedAddThreadSeedInput",
    "EnvironmentTopologyProcessSeedAddThreadSeedOutput",
    "EnvironmentTopologyProcessSeedBuildViaEnvironmentTopologySeedInput",
    "EnvironmentTopologyProcessSeedBuildViaEnvironmentTopologySeedOutput",
    "FUNCTIONS",
]
