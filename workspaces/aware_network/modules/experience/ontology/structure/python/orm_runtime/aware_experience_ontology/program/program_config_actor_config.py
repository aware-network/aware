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
    from aware_identity_ontology.actor.actor_config import ActorConfig


class ProgramConfigActorConfig(ORMModel):
    """
    ProgramConfig actor alias contract.
    Contract:
    - Binds one ProgramConfig alias to one Identity ActorConfig.
    - Alias identity is parent-path scoped under ProgramConfig.
    - Multiple aliases may reference the same ActorConfig.
    """

    # Relationships
    actor_config: ActorConfig | None = Field(default=None, exclude=True)

    # Attributes
    alias: str

    # Foreign Keys
    program_config_id: UUID = Field(description="Foreign key for ProgramConfig.actor_configs")
    actor_config_id: UUID = Field(description="Foreign key for ProgramConfigActorConfig.actor_config")

    @classmethod
    async def build_via_program_config(
        cls, program_config_id: UUID, actor_config_id: UUID, alias: str
    ) -> ProgramConfigActorConfig:
        """Create deterministic ProgramConfig actor alias association."""

        payload = {"program_config_id": program_config_id, "actor_config_id": actor_config_id, "alias": alias}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_program_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramConfigActorConfig):
            return value
        return ProgramConfigActorConfig.validate_invocation_value(value)


class ProgramConfigActorConfigBuildViaProgramConfigInput(BaseModel):
    program_config_id: UUID = Field(description="Foreign key for ProgramConfig.actor_configs")
    actor_config_id: UUID
    alias: str


class ProgramConfigActorConfigBuildViaProgramConfigOutput(BaseModel):
    value: ProgramConfigActorConfig


FUNCTIONS = {
    "ProgramConfigActorConfig": {
        "build_via_program_config": {
            "canonical": {
                "name": "build_via_program_config",
                "description": "Create deterministic ProgramConfig actor alias association.",
                "is_constructor": True,
            },
            "input": ProgramConfigActorConfigBuildViaProgramConfigInput,
            "output": ProgramConfigActorConfigBuildViaProgramConfigOutput,
        },
    },
}

__all__ = [
    "ProgramConfigActorConfig",
    "ProgramConfigActorConfigBuildViaProgramConfigInput",
    "ProgramConfigActorConfigBuildViaProgramConfigOutput",
    "FUNCTIONS",
]
