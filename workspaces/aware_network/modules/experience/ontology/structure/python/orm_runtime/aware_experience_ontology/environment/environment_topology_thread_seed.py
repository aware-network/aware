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
    from aware_environment_ontology.thread.thread_config import ThreadConfig
    from aware_experience_ontology.environment.environment_topology_thread_layout_seed import (
        EnvironmentTopologyThreadLayoutSeed,
    )


class EnvironmentTopologyThreadSeed(ORMModel):
    """Runtime Thread seed inside an EnvironmentTopologyProcessSeed."""

    # Relationships
    thread_config: ThreadConfig | None = Field(default=None, exclude=True)
    layout_seeds: list[EnvironmentTopologyThreadLayoutSeed] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    is_main: bool = Field(default=False)
    key: str | None = Field(
        default=None, description="Optional seed-local key; defaults to `thread_key` in runtime handlers."
    )
    thread_key: str = Field(description="Runtime Thread.key to create or resolve under Environment.")
    position: int | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    title: str | None = Field(default=None)

    # Foreign Keys
    environment_topology_process_seed_id: UUID = Field(
        description="Foreign key for EnvironmentTopologyProcessSeed.thread_seeds"
    )
    thread_config_id: UUID = Field(description="Foreign key for EnvironmentTopologyThreadSeed.thread_config")

    async def add_layout_seed(
        self,
        layout_config_id: UUID,
        key: str | None = None,
        position: int | None = None,
        activate_on_seed: bool = False,
        narrative: str | None = None,
        intent: str | None = None,
    ) -> EnvironmentTopologyThreadLayoutSeed:
        """Add one layout activation seed referencing a ThreadConfig layout candidate."""

        payload = {
            "layout_config_id": layout_config_id,
            "key": key,
            "position": position,
            "activate_on_seed": activate_on_seed,
            "narrative": narrative,
            "intent": intent,
        }
        result = await invoke_instance(orm_model=self, function_name="add_layout_seed", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.environment_topology_thread_layout_seed import (
            EnvironmentTopologyThreadLayoutSeed,
        )

        if isinstance(value, EnvironmentTopologyThreadLayoutSeed):
            return value
        return EnvironmentTopologyThreadLayoutSeed.validate_invocation_value(value)

    @classmethod
    async def build_via_environment_topology_process_seed(
        cls,
        environment_topology_process_seed_id: UUID,
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
        """
        Construct one thread seed.

        Contract:
        - `thread_config_id` is reusable Environment ThreadConfig truth.
        - `thread_key` is runtime instance identity.
        """

        payload = {
            "environment_topology_process_seed_id": environment_topology_process_seed_id,
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
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_topology_process_seed", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentTopologyThreadSeed):
            return value
        return EnvironmentTopologyThreadSeed.validate_invocation_value(value)


class EnvironmentTopologyThreadSeedAddLayoutSeedInput(BaseModel):
    layout_config_id: UUID
    key: str | None = Field(default=None)
    position: int | None = Field(default=None)
    activate_on_seed: bool = Field(default=False)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class EnvironmentTopologyThreadSeedAddLayoutSeedOutput(BaseModel):
    value: EnvironmentTopologyThreadLayoutSeed


class EnvironmentTopologyThreadSeedBuildViaEnvironmentTopologyProcessSeedInput(BaseModel):
    environment_topology_process_seed_id: UUID = Field(
        description="Foreign key for EnvironmentTopologyProcessSeed.thread_seeds"
    )
    thread_config_id: UUID
    thread_key: str
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_main: bool = Field(default=False)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class EnvironmentTopologyThreadSeedBuildViaEnvironmentTopologyProcessSeedOutput(BaseModel):
    value: EnvironmentTopologyThreadSeed


FUNCTIONS = {
    "EnvironmentTopologyThreadSeed": {
        "add_layout_seed": {
            "canonical": {
                "name": "add_layout_seed",
                "description": "Add one layout activation seed referencing a ThreadConfig layout candidate.",
                "is_constructor": False,
            },
            "input": EnvironmentTopologyThreadSeedAddLayoutSeedInput,
            "output": EnvironmentTopologyThreadSeedAddLayoutSeedOutput,
        },
        "build_via_environment_topology_process_seed": {
            "canonical": {
                "name": "build_via_environment_topology_process_seed",
                "description": "Construct one thread seed.\n\nContract:\n- `thread_config_id` is reusable Environment ThreadConfig truth.\n- `thread_key` is runtime instance identity.",
                "is_constructor": True,
            },
            "input": EnvironmentTopologyThreadSeedBuildViaEnvironmentTopologyProcessSeedInput,
            "output": EnvironmentTopologyThreadSeedBuildViaEnvironmentTopologyProcessSeedOutput,
        },
    },
}

__all__ = [
    "EnvironmentTopologyThreadSeed",
    "EnvironmentTopologyThreadSeedAddLayoutSeedInput",
    "EnvironmentTopologyThreadSeedAddLayoutSeedOutput",
    "EnvironmentTopologyThreadSeedBuildViaEnvironmentTopologyProcessSeedInput",
    "EnvironmentTopologyThreadSeedBuildViaEnvironmentTopologyProcessSeedOutput",
    "FUNCTIONS",
]
