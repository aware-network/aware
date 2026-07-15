from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology
from aware_identity_ontology.actor.actor_enums import ActorType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_identity_ontology.actor.actor_config_role_config import ActorConfigRoleConfig


class ActorConfig(ORMModel):
    """
    Identity-owned ActorConfig policy archetype.
    Contract:
    - ActorConfig is reusable admission vocabulary, not Experience-local truth.
    - Environment and Experience consume ActorConfig to describe which actor
    archetypes may enter a scope.
    - Identity owns the RoleConfig bundle and later resolves concrete ActorRole
    truth through admission services.
    """

    # Relationships
    role_configs: list[ActorConfigRoleConfig] = Field(default_factory=list)

    # Attributes
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    type: ActorType | None = Field(default=None)

    @classmethod
    async def create(
        cls, key: str, title: str | None = None, description: str | None = None, type: ActorType | None = None
    ) -> ActorConfig:
        """
        Create one deterministic Identity-owned ActorConfig.

        Contract:
        - Stable identity is derived from `key`.
        - The object is pure policy vocabulary; it does not grant access by itself.
        - Concrete grants are Identity Role / ActorRole materialization.
        """

        payload = {"key": key, "title": title, "description": description, "type": type}
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActorConfig):
            return value
        return ActorConfig.validate_invocation_value(value)

    async def add_role_config(self, role_config_id: UUID) -> ActorConfigRoleConfig:
        """
        Attach one RoleConfig to this ActorConfig archetype.

        Contract:
        - The edge is eligibility vocabulary only.
        - Admission scopes consume this bundle and delegate concrete role
          assignment back to Identity.
        """

        payload = {"role_config_id": role_config_id}
        result = await invoke_instance(orm_model=self, function_name="add_role_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.actor.actor_config_role_config import ActorConfigRoleConfig

        if isinstance(value, ActorConfigRoleConfig):
            return value
        return ActorConfigRoleConfig.validate_invocation_value(value)


class ActorConfigCreateInput(BaseModel):
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    type: ActorType | None = Field(default=None)


class ActorConfigCreateOutput(BaseModel):
    value: ActorConfig


class ActorConfigAddRoleConfigInput(BaseModel):
    role_config_id: UUID


class ActorConfigAddRoleConfigOutput(BaseModel):
    value: ActorConfigRoleConfig


FUNCTIONS = {
    "ActorConfig": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Create one deterministic Identity-owned ActorConfig.\n\nContract:\n- Stable identity is derived from `key`.\n- The object is pure policy vocabulary; it does not grant access by itself.\n- Concrete grants are Identity Role / ActorRole materialization.",
                "is_constructor": True,
            },
            "input": ActorConfigCreateInput,
            "output": ActorConfigCreateOutput,
        },
        "add_role_config": {
            "canonical": {
                "name": "add_role_config",
                "description": "Attach one RoleConfig to this ActorConfig archetype.\n\nContract:\n- The edge is eligibility vocabulary only.\n- Admission scopes consume this bundle and delegate concrete role\n  assignment back to Identity.",
                "is_constructor": False,
            },
            "input": ActorConfigAddRoleConfigInput,
            "output": ActorConfigAddRoleConfigOutput,
        },
    },
}

__all__ = [
    "ActorConfig",
    "ActorConfigCreateInput",
    "ActorConfigCreateOutput",
    "ActorConfigAddRoleConfigInput",
    "ActorConfigAddRoleConfigOutput",
    "FUNCTIONS",
]
