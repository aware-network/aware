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
    from aware_identity_ontology.role.role import Role


class ActorRole(ORMModel):
    # Relationships
    role: Role | None = Field(default=None, exclude=True)

    # Foreign Keys
    actor_id: UUID = Field(description="Foreign key for Actor.actor_roles")
    role_id: UUID = Field(description="Foreign key for ActorRole.role")

    async def delete(self) -> None:
        """Delete this ActorRole assignment edge."""

        payload = {}
        await invoke_instance(orm_model=self, function_name="delete", payload=payload)
        return None

    @classmethod
    async def create_via_actor(cls, actor_id: UUID, role_id: UUID) -> ActorRole:
        """
        Create an ActorRole assignment row.

        Contract (v0):
        - Deterministic id from (actor_id, role_id).
        - Idempotent assignment edge between Actor and Role.
        """

        payload = {"actor_id": actor_id, "role_id": role_id}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_actor", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActorRole):
            return value
        return ActorRole.validate_invocation_value(value)


class ActorRoleDeleteInput(BaseModel):
    pass


class ActorRoleDeleteOutput(BaseModel):
    pass


class ActorRoleCreateViaActorInput(BaseModel):
    actor_id: UUID = Field(description="Foreign key for Actor.actor_roles")
    role_id: UUID


class ActorRoleCreateViaActorOutput(BaseModel):
    value: ActorRole


FUNCTIONS = {
    "ActorRole": {
        "delete": {
            "canonical": {
                "name": "delete",
                "description": "Delete this ActorRole assignment edge.",
                "is_constructor": False,
            },
            "input": ActorRoleDeleteInput,
            "output": ActorRoleDeleteOutput,
        },
        "create_via_actor": {
            "canonical": {
                "name": "create_via_actor",
                "description": "Create an ActorRole assignment row.\n\nContract (v0):\n- Deterministic id from (actor_id, role_id).\n- Idempotent assignment edge between Actor and Role.",
                "is_constructor": True,
            },
            "input": ActorRoleCreateViaActorInput,
            "output": ActorRoleCreateViaActorOutput,
        },
    },
}

__all__ = [
    "ActorRole",
    "ActorRoleDeleteInput",
    "ActorRoleDeleteOutput",
    "ActorRoleCreateViaActorInput",
    "ActorRoleCreateViaActorOutput",
    "FUNCTIONS",
]
