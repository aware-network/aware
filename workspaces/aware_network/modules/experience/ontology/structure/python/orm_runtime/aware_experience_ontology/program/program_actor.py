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
    from aware_experience_ontology.program.program_actor_role import ProgramActorRole
    from aware_experience_ontology.program.program_config_actor_config import ProgramConfigActorConfig
    from aware_identity_ontology.actor.actor import Actor


class ProgramActor(ORMModel):
    """
    Runtime actor binding for one Program actor alias.
    Contract:
    - Binds one ProgramConfigActorConfig alias contract to one concrete Actor.
    - Identity is deterministic under Program for `(program_config_actor_config_id, actor_id)`.
    """

    # Relationships
    program_config_actor_config: ProgramConfigActorConfig | None = Field(default=None, exclude=True)
    actor: Actor | None = Field(default=None, exclude=True)
    program_actor_roles: list[ProgramActorRole] = Field(default_factory=list, exclude=True)

    # Foreign Keys
    program_id: UUID = Field(description="Foreign key for Program.program_actors")
    program_config_actor_config_id: UUID = Field(description="Foreign key for ProgramActor.program_config_actor_config")
    actor_id: UUID = Field(description="Foreign key for ProgramActor.actor")

    async def add_actor_role(self, actor_role_id: UUID, actor_config_role_config_id: UUID) -> ProgramActorRole:
        """
        Bind one ActorRole that is eligible for this ProgramActor via ActorConfigRoleConfig.

        Contract:
        - Mutates only ProgramActor membership (`program_actor_roles`).
        - Program run attribution must resolve invoke actor context via ProgramActorRole.
        """

        payload = {"actor_role_id": actor_role_id, "actor_config_role_config_id": actor_config_role_config_id}
        result = await invoke_instance(orm_model=self, function_name="add_actor_role", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_actor_role import ProgramActorRole

        if isinstance(value, ProgramActorRole):
            return value
        return ProgramActorRole.validate_invocation_value(value)

    @classmethod
    async def build_via_program(
        cls, program_id: UUID, program_config_actor_config_id: UUID, actor_id: UUID
    ) -> ProgramActor:
        """Create deterministic ProgramActor binding under Program."""

        payload = {
            "program_id": program_id,
            "program_config_actor_config_id": program_config_actor_config_id,
            "actor_id": actor_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_program", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramActor):
            return value
        return ProgramActor.validate_invocation_value(value)


class ProgramActorAddActorRoleInput(BaseModel):
    actor_role_id: UUID
    actor_config_role_config_id: UUID


class ProgramActorAddActorRoleOutput(BaseModel):
    value: ProgramActorRole


class ProgramActorBuildViaProgramInput(BaseModel):
    program_id: UUID = Field(description="Foreign key for Program.program_actors")
    program_config_actor_config_id: UUID
    actor_id: UUID


class ProgramActorBuildViaProgramOutput(BaseModel):
    value: ProgramActor


FUNCTIONS = {
    "ProgramActor": {
        "add_actor_role": {
            "canonical": {
                "name": "add_actor_role",
                "description": "Bind one ActorRole that is eligible for this ProgramActor via ActorConfigRoleConfig.\n\nContract:\n- Mutates only ProgramActor membership (`program_actor_roles`).\n- Program run attribution must resolve invoke actor context via ProgramActorRole.",
                "is_constructor": False,
            },
            "input": ProgramActorAddActorRoleInput,
            "output": ProgramActorAddActorRoleOutput,
        },
        "build_via_program": {
            "canonical": {
                "name": "build_via_program",
                "description": "Create deterministic ProgramActor binding under Program.",
                "is_constructor": True,
            },
            "input": ProgramActorBuildViaProgramInput,
            "output": ProgramActorBuildViaProgramOutput,
        },
    },
}

__all__ = [
    "ProgramActor",
    "ProgramActorAddActorRoleInput",
    "ProgramActorAddActorRoleOutput",
    "ProgramActorBuildViaProgramInput",
    "ProgramActorBuildViaProgramOutput",
    "FUNCTIONS",
]
