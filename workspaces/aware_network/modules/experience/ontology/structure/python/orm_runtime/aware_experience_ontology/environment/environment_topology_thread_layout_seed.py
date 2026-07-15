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
    from aware_attention_ontology.layout.layout_config import LayoutConfig


class EnvironmentTopologyThreadLayoutSeed(ORMModel):
    """Runtime ThreadLayout seed inside an EnvironmentTopologyThreadSeed."""

    # Relationships
    layout_config: LayoutConfig | None = Field(default=None, exclude=True)

    # Attributes
    key: str | None = Field(
        default=None, description="Optional layout seed key; defaults to the LayoutConfig key when omitted."
    )
    position: int | None = Field(default=None)
    activate_on_seed: bool = Field(
        default=False, description="Whether provisioning should set this layout active for the runtime Thread."
    )
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)

    # Foreign Keys
    environment_topology_thread_seed_id: UUID = Field(
        description="Foreign key for EnvironmentTopologyThreadSeed.layout_seeds"
    )
    layout_config_id: UUID = Field(description="Foreign key for EnvironmentTopologyThreadLayoutSeed.layout_config")

    @classmethod
    async def build_via_environment_topology_thread_seed(
        cls,
        environment_topology_thread_seed_id: UUID,
        layout_config_id: UUID,
        key: str | None = None,
        position: int | None = None,
        activate_on_seed: bool = False,
        narrative: str | None = None,
        intent: str | None = None,
    ) -> EnvironmentTopologyThreadLayoutSeed:
        """
        Construct one thread-layout seed.

        Contract:
        - `layout_config_id` must be allowed by the referenced ThreadConfig candidate set.
        - Attention still owns the LayoutConfig/SectionConfig topology.
        """

        payload = {
            "environment_topology_thread_seed_id": environment_topology_thread_seed_id,
            "layout_config_id": layout_config_id,
            "key": key,
            "position": position,
            "activate_on_seed": activate_on_seed,
            "narrative": narrative,
            "intent": intent,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_topology_thread_seed", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentTopologyThreadLayoutSeed):
            return value
        return EnvironmentTopologyThreadLayoutSeed.validate_invocation_value(value)


class EnvironmentTopologyThreadLayoutSeedBuildViaEnvironmentTopologyThreadSeedInput(BaseModel):
    environment_topology_thread_seed_id: UUID = Field(
        description="Foreign key for EnvironmentTopologyThreadSeed.layout_seeds"
    )
    layout_config_id: UUID
    key: str | None = Field(default=None)
    position: int | None = Field(default=None)
    activate_on_seed: bool = Field(default=False)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class EnvironmentTopologyThreadLayoutSeedBuildViaEnvironmentTopologyThreadSeedOutput(BaseModel):
    value: EnvironmentTopologyThreadLayoutSeed


FUNCTIONS = {
    "EnvironmentTopologyThreadLayoutSeed": {
        "build_via_environment_topology_thread_seed": {
            "canonical": {
                "name": "build_via_environment_topology_thread_seed",
                "description": "Construct one thread-layout seed.\n\nContract:\n- `layout_config_id` must be allowed by the referenced ThreadConfig candidate set.\n- Attention still owns the LayoutConfig/SectionConfig topology.",
                "is_constructor": True,
            },
            "input": EnvironmentTopologyThreadLayoutSeedBuildViaEnvironmentTopologyThreadSeedInput,
            "output": EnvironmentTopologyThreadLayoutSeedBuildViaEnvironmentTopologyThreadSeedOutput,
        },
    },
}

__all__ = [
    "EnvironmentTopologyThreadLayoutSeed",
    "EnvironmentTopologyThreadLayoutSeedBuildViaEnvironmentTopologyThreadSeedInput",
    "EnvironmentTopologyThreadLayoutSeedBuildViaEnvironmentTopologyThreadSeedOutput",
    "FUNCTIONS",
]
