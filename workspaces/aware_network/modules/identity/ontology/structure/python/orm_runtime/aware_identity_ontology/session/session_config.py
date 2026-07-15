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

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology.session.session import Session
    from aware_identity_ontology.session.session_config_actor_config import SessionConfigActorConfig


class SessionConfig(ORMModel):
    """
    Identity-owned reusable actor-session policy.
    Contract:
    - SessionConfig is domain-neutral participation vocabulary.
    - Environment, Experience, Attention, and other providers bridge to it
    instead of owning separate actor-session role lifecycles.
    - ActorConfig remains the reusable actor archetype vocabulary.
    - Concrete sessions and member ActorRole evidence stay Identity-owned.
    """

    # Relationships
    actor_configs: list[SessionConfigActorConfig] = Field(default_factory=list)
    sessions: list[Session] = Field(default_factory=list)

    # Attributes
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    @classmethod
    async def create(
        cls,
        key: str,
        title: str | None = None,
        description: str | None = None,
        purpose: str | None = None,
        status: str = "active",
        metadata_json: JsonObject | None = {},
    ) -> SessionConfig:
        """
        Create one deterministic Identity SessionConfig.

        Contract:
        - Stable identity is derived from `key`.
        - This is policy vocabulary only; it does not admit or grant an actor.
        """

        payload = {
            "key": key,
            "title": title,
            "description": description,
            "purpose": purpose,
            "status": status,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SessionConfig):
            return value
        return SessionConfig.validate_invocation_value(value)

    async def add_actor_config(
        self,
        actor_config_id: UUID,
        status: str = "active",
        purpose: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> SessionConfigActorConfig:
        """
        Attach one ActorConfig as eligible for this SessionConfig.

        Contract:
        - The edge is session participation policy only.
        - Concrete membership is SessionMember.
        - Concrete permission evidence is SessionMemberActorRole.
        """

        payload = {
            "actor_config_id": actor_config_id,
            "status": status,
            "purpose": purpose,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="add_actor_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.session.session_config_actor_config import SessionConfigActorConfig

        if isinstance(value, SessionConfigActorConfig):
            return value
        return SessionConfigActorConfig.validate_invocation_value(value)

    async def start_session(
        self,
        key: str,
        parent_session_scope_key: str = "root",
        parent_session_id: UUID | None = None,
        title: str | None = None,
        description: str | None = None,
        purpose: str | None = None,
        status: str = "active",
        created_by_actor_id: UUID | None = None,
        source_kind: str | None = None,
        source_ref: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> Session:
        """
        Start one concrete Session under this SessionConfig.

        Contract:
        - Stable identity is SessionConfig path + `key` + `parent_session_scope_key`.
        - Root sessions use `parent_session_scope_key = "root"` and
          `parent_session_id = null`.
        - Child sessions use `parent_session_scope_key = parent_session_id`.
        - Domains may reference this Session, but Identity owns membership.
        """

        payload = {
            "key": key,
            "parent_session_scope_key": parent_session_scope_key,
            "parent_session_id": parent_session_id,
            "title": title,
            "description": description,
            "purpose": purpose,
            "status": status,
            "created_by_actor_id": created_by_actor_id,
            "source_kind": source_kind,
            "source_ref": source_ref,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="start_session", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.session.session import Session

        if isinstance(value, Session):
            return value
        return Session.validate_invocation_value(value)


class SessionConfigCreateInput(BaseModel):
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class SessionConfigCreateOutput(BaseModel):
    value: SessionConfig


class SessionConfigAddActorConfigInput(BaseModel):
    actor_config_id: UUID
    status: str = Field(default="active")
    purpose: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class SessionConfigAddActorConfigOutput(BaseModel):
    value: SessionConfigActorConfig


class SessionConfigStartSessionInput(BaseModel):
    key: str
    parent_session_scope_key: str = Field(default="root")
    parent_session_id: UUID | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    created_by_actor_id: UUID | None = Field(default=None)
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class SessionConfigStartSessionOutput(BaseModel):
    value: Session


FUNCTIONS = {
    "SessionConfig": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Create one deterministic Identity SessionConfig.\n\nContract:\n- Stable identity is derived from `key`.\n- This is policy vocabulary only; it does not admit or grant an actor.",
                "is_constructor": True,
            },
            "input": SessionConfigCreateInput,
            "output": SessionConfigCreateOutput,
        },
        "add_actor_config": {
            "canonical": {
                "name": "add_actor_config",
                "description": "Attach one ActorConfig as eligible for this SessionConfig.\n\nContract:\n- The edge is session participation policy only.\n- Concrete membership is SessionMember.\n- Concrete permission evidence is SessionMemberActorRole.",
                "is_constructor": False,
            },
            "input": SessionConfigAddActorConfigInput,
            "output": SessionConfigAddActorConfigOutput,
        },
        "start_session": {
            "canonical": {
                "name": "start_session",
                "description": 'Start one concrete Session under this SessionConfig.\n\nContract:\n- Stable identity is SessionConfig path + `key` + `parent_session_scope_key`.\n- Root sessions use `parent_session_scope_key = "root"` and\n  `parent_session_id = null`.\n- Child sessions use `parent_session_scope_key = parent_session_id`.\n- Domains may reference this Session, but Identity owns membership.',
                "is_constructor": False,
            },
            "input": SessionConfigStartSessionInput,
            "output": SessionConfigStartSessionOutput,
        },
    },
}

__all__ = [
    "SessionConfig",
    "SessionConfigCreateInput",
    "SessionConfigCreateOutput",
    "SessionConfigAddActorConfigInput",
    "SessionConfigAddActorConfigOutput",
    "SessionConfigStartSessionInput",
    "SessionConfigStartSessionOutput",
    "FUNCTIONS",
]
