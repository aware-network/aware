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

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology.actor.actor_config import ActorConfig


class SessionConfigActorConfig(ORMModel):
    """
    ActorConfig participation policy edge under a SessionConfig.
    Contract:
    - Parent constructor is SessionConfig.
    - Points to Identity ActorConfig vocabulary.
    - Does not grant access or create a concrete member.
    """

    # Relationships
    actor_config: ActorConfig | None = Field(default=None)

    # Attributes
    status: str = Field(default="active")
    purpose: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    session_config_id: UUID = Field(description="Foreign key for SessionConfig.actor_configs")
    actor_config_id: UUID = Field(description="Foreign key for SessionConfigActorConfig.actor_config")

    @classmethod
    async def create_via_session_config(
        cls,
        session_config_id: UUID,
        actor_config_id: UUID,
        status: str = "active",
        purpose: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> SessionConfigActorConfig:
        """
        Create one deterministic SessionConfig -> ActorConfig policy edge.

        Contract:
        - Stable identity is `(session_config_id, actor_config_id)`.
        - This is eligibility vocabulary only.
        """

        payload = {
            "session_config_id": session_config_id,
            "actor_config_id": actor_config_id,
            "status": status,
            "purpose": purpose,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_session_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SessionConfigActorConfig):
            return value
        return SessionConfigActorConfig.validate_invocation_value(value)


class SessionConfigActorConfigCreateViaSessionConfigInput(BaseModel):
    session_config_id: UUID = Field(description="Foreign key for SessionConfig.actor_configs")
    actor_config_id: UUID
    status: str = Field(default="active")
    purpose: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class SessionConfigActorConfigCreateViaSessionConfigOutput(BaseModel):
    value: SessionConfigActorConfig


FUNCTIONS = {
    "SessionConfigActorConfig": {
        "create_via_session_config": {
            "canonical": {
                "name": "create_via_session_config",
                "description": "Create one deterministic SessionConfig -> ActorConfig policy edge.\n\nContract:\n- Stable identity is `(session_config_id, actor_config_id)`.\n- This is eligibility vocabulary only.",
                "is_constructor": True,
            },
            "input": SessionConfigActorConfigCreateViaSessionConfigInput,
            "output": SessionConfigActorConfigCreateViaSessionConfigOutput,
        },
    },
}

__all__ = [
    "SessionConfigActorConfig",
    "SessionConfigActorConfigCreateViaSessionConfigInput",
    "SessionConfigActorConfigCreateViaSessionConfigOutput",
    "FUNCTIONS",
]
