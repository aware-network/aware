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
    from aware_identity_ontology.role.role_config import RoleConfig


class ActorConfigRoleConfig(ORMModel):
    """RoleConfig eligibility edge under an Identity ActorConfig."""

    # Relationships
    role_config: RoleConfig | None = Field(default=None)

    # Foreign Keys
    actor_config_id: UUID = Field(description="Foreign key for ActorConfig.role_configs")
    role_config_id: UUID = Field(description="Foreign key for ActorConfigRoleConfig.role_config")

    @classmethod
    async def create_via_actor_config(cls, actor_config_id: UUID, role_config_id: UUID) -> ActorConfigRoleConfig:
        """
        Create a deterministic ActorConfigRoleConfig association edge.

        Contract:
        - Parent ActorConfig scope is propagated by constructor lowering.
        - Stable identity is `(actor_config_id, role_config_id)`.
        - This is policy vocabulary only; it is not an ActorRole grant.
        """

        payload = {"actor_config_id": actor_config_id, "role_config_id": role_config_id}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_actor_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActorConfigRoleConfig):
            return value
        return ActorConfigRoleConfig.validate_invocation_value(value)


class ActorConfigRoleConfigCreateViaActorConfigInput(BaseModel):
    actor_config_id: UUID = Field(description="Foreign key for ActorConfig.role_configs")
    role_config_id: UUID


class ActorConfigRoleConfigCreateViaActorConfigOutput(BaseModel):
    value: ActorConfigRoleConfig


FUNCTIONS = {
    "ActorConfigRoleConfig": {
        "create_via_actor_config": {
            "canonical": {
                "name": "create_via_actor_config",
                "description": "Create a deterministic ActorConfigRoleConfig association edge.\n\nContract:\n- Parent ActorConfig scope is propagated by constructor lowering.\n- Stable identity is `(actor_config_id, role_config_id)`.\n- This is policy vocabulary only; it is not an ActorRole grant.",
                "is_constructor": True,
            },
            "input": ActorConfigRoleConfigCreateViaActorConfigInput,
            "output": ActorConfigRoleConfigCreateViaActorConfigOutput,
        },
    },
}

__all__ = [
    "ActorConfigRoleConfig",
    "ActorConfigRoleConfigCreateViaActorConfigInput",
    "ActorConfigRoleConfigCreateViaActorConfigOutput",
    "FUNCTIONS",
]
