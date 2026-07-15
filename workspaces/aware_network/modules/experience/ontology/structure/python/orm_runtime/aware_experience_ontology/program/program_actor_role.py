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
    from aware_identity_ontology.actor.actor_config_role_config import ActorConfigRoleConfig
    from aware_identity_ontology.actor.actor_role import ActorRole


class ProgramActorRole(ORMModel):
    """
    Runtime role attribution edge under one ProgramActor.
    Contract:
    - Stores the role snapshot used by runtime invoke attribution.
    - Links role eligibility provenance through Identity ActorConfigRoleConfig.
    """

    # Relationships
    actor_role: ActorRole | None = Field(default=None, exclude=True)
    actor_config_role_config: ActorConfigRoleConfig | None = Field(default=None, exclude=True)

    # Foreign Keys
    program_actor_id: UUID = Field(description="Foreign key for ProgramActor.program_actor_roles")
    actor_role_id: UUID = Field(description="Foreign key for ProgramActorRole.actor_role")
    actor_config_role_config_id: UUID = Field(description="Foreign key for ProgramActorRole.actor_config_role_config")

    @classmethod
    async def build_via_program_actor(
        cls, program_actor_id: UUID, actor_role_id: UUID, actor_config_role_config_id: UUID
    ) -> ProgramActorRole:
        """Create deterministic ProgramActorRole under ProgramActor."""

        payload = {
            "program_actor_id": program_actor_id,
            "actor_role_id": actor_role_id,
            "actor_config_role_config_id": actor_config_role_config_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_program_actor", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramActorRole):
            return value
        return ProgramActorRole.validate_invocation_value(value)


class ProgramActorRoleBuildViaProgramActorInput(BaseModel):
    program_actor_id: UUID = Field(description="Foreign key for ProgramActor.program_actor_roles")
    actor_role_id: UUID
    actor_config_role_config_id: UUID


class ProgramActorRoleBuildViaProgramActorOutput(BaseModel):
    value: ProgramActorRole


FUNCTIONS = {
    "ProgramActorRole": {
        "build_via_program_actor": {
            "canonical": {
                "name": "build_via_program_actor",
                "description": "Create deterministic ProgramActorRole under ProgramActor.",
                "is_constructor": True,
            },
            "input": ProgramActorRoleBuildViaProgramActorInput,
            "output": ProgramActorRoleBuildViaProgramActorOutput,
        },
    },
}

__all__ = [
    "ProgramActorRole",
    "ProgramActorRoleBuildViaProgramActorInput",
    "ProgramActorRoleBuildViaProgramActorOutput",
    "FUNCTIONS",
]
