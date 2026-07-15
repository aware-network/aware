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
    from aware_identity_ontology.actor.actor import Actor
    from aware_identity_ontology.session.session_member import SessionMember
    from aware_identity_ontology.session.session_provider_session import SessionProviderSession


class Session(ORMModel):
    """
    Identity-owned concrete actor-session container.
    Contract:
    - Parent constructor is SessionConfig.
    - Session is generic actor participation state, not Environment,
    Experience, or Attention topology.
    - Domains wrap/bridge to this object when they need domain-specific
    session meaning.
    """

    # Relationships
    parent_session: Session | None = Field(default=None)
    created_by_actor: Actor | None = Field(default=None)
    members: list[SessionMember] = Field(default_factory=list)
    provider_sessions: list[SessionProviderSession] = Field(default_factory=list)

    # Attributes
    key: str
    parent_session_scope_key: str = Field(default="root")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    session_config_id: UUID = Field(description="Foreign key for SessionConfig.sessions")
    parent_session_id: UUID | None = Field(default=None, description="Foreign key for Session.parent_session")
    created_by_actor_id: UUID | None = Field(default=None, description="Foreign key for Session.created_by_actor")

    async def join_actor(
        self,
        actor_id: UUID,
        session_actor_config_id: UUID,
        status: str = "active",
        joined_at_unix_ms: int | None = None,
        left_at_unix_ms: int | None = None,
        metadata_json: JsonObject | None = {},
    ) -> SessionMember:
        """
        Join one Actor to this Session under a SessionConfigActorConfig.

        Contract:
        - `session_actor_config_id` is required and points to session policy.
        - Stable identity is `(session_id, actor_id)`.
        - Member ActorRole evidence is added through SessionMemberActorRole.
        """

        payload = {
            "actor_id": actor_id,
            "session_actor_config_id": session_actor_config_id,
            "status": status,
            "joined_at_unix_ms": joined_at_unix_ms,
            "left_at_unix_ms": left_at_unix_ms,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="join_actor", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.session.session_member import SessionMember

        if isinstance(value, SessionMember):
            return value
        return SessionMember.validate_invocation_value(value)

    async def attach_provider_session(
        self,
        provider_session_config_id: UUID,
        provider_session_key: str,
        provider_session_ref: str | None = None,
        provider_object_instance_graph_identity_id: UUID | None = None,
        provider_class_instance_identity_id: UUID | None = None,
        provider_object_instance_graph_branch_id: UUID | None = None,
        status: str = "active",
        metadata_json: JsonObject | None = {},
    ) -> SessionProviderSession:
        """
        Attach one provider-owned domain session/capability to this shared
        Identity Session.

        Contract:
        - Session remains the actor participation envelope.
        - Provider attachment is many-per-Session, not a singular owner.
        - Provider-specific detail is referenced through generic Meta graph
          portals or an opaque bridge ref; Identity does not import provider
          domain ontology.
        """

        payload = {
            "provider_session_config_id": provider_session_config_id,
            "provider_session_key": provider_session_key,
            "provider_session_ref": provider_session_ref,
            "provider_object_instance_graph_identity_id": provider_object_instance_graph_identity_id,
            "provider_class_instance_identity_id": provider_class_instance_identity_id,
            "provider_object_instance_graph_branch_id": provider_object_instance_graph_branch_id,
            "status": status,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_provider_session", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.session.session_provider_session import SessionProviderSession

        if isinstance(value, SessionProviderSession):
            return value
        return SessionProviderSession.validate_invocation_value(value)

    @classmethod
    async def build_via_session_config(
        cls,
        session_config_id: UUID,
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
        Construct one Session under a SessionConfig.

        Contract:
        - Stable identity is SessionConfig path + `key` + `parent_session_scope_key`.
        - Root sessions use `parent_session_scope_key = "root"` and
          `parent_session_id = null`.
        - Child sessions use `parent_session_scope_key = parent_session_id`.
        - The relationship is parent-only. Do not add a reverse child-session
          ownership rail.
        - Does not resolve Process/Thread/Layout/Attention.
        - Does not grant roles; Identity ActorRole truth remains separate.
        """

        payload = {
            "session_config_id": session_config_id,
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
        result = await invoke_constructor(orm_class=cls, function_name="build_via_session_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Session):
            return value
        return Session.validate_invocation_value(value)


class SessionJoinActorInput(BaseModel):
    actor_id: UUID
    session_actor_config_id: UUID
    status: str = Field(default="active")
    joined_at_unix_ms: int | None = Field(default=None)
    left_at_unix_ms: int | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class SessionJoinActorOutput(BaseModel):
    value: SessionMember


class SessionAttachProviderSessionInput(BaseModel):
    provider_session_config_id: UUID
    provider_session_key: str
    provider_session_ref: str | None = Field(default=None)
    provider_object_instance_graph_identity_id: UUID | None = Field(default=None)
    provider_class_instance_identity_id: UUID | None = Field(default=None)
    provider_object_instance_graph_branch_id: UUID | None = Field(default=None)
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class SessionAttachProviderSessionOutput(BaseModel):
    value: SessionProviderSession


class SessionBuildViaSessionConfigInput(BaseModel):
    session_config_id: UUID = Field(description="Foreign key for SessionConfig.sessions")
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


class SessionBuildViaSessionConfigOutput(BaseModel):
    value: Session


FUNCTIONS = {
    "Session": {
        "join_actor": {
            "canonical": {
                "name": "join_actor",
                "description": "Join one Actor to this Session under a SessionConfigActorConfig.\n\nContract:\n- `session_actor_config_id` is required and points to session policy.\n- Stable identity is `(session_id, actor_id)`.\n- Member ActorRole evidence is added through SessionMemberActorRole.",
                "is_constructor": False,
            },
            "input": SessionJoinActorInput,
            "output": SessionJoinActorOutput,
        },
        "attach_provider_session": {
            "canonical": {
                "name": "attach_provider_session",
                "description": "Attach one provider-owned domain session/capability to this shared\nIdentity Session.\n\nContract:\n- Session remains the actor participation envelope.\n- Provider attachment is many-per-Session, not a singular owner.\n- Provider-specific detail is referenced through generic Meta graph\n  portals or an opaque bridge ref; Identity does not import provider\n  domain ontology.",
                "is_constructor": False,
            },
            "input": SessionAttachProviderSessionInput,
            "output": SessionAttachProviderSessionOutput,
        },
        "build_via_session_config": {
            "canonical": {
                "name": "build_via_session_config",
                "description": 'Construct one Session under a SessionConfig.\n\nContract:\n- Stable identity is SessionConfig path + `key` + `parent_session_scope_key`.\n- Root sessions use `parent_session_scope_key = "root"` and\n  `parent_session_id = null`.\n- Child sessions use `parent_session_scope_key = parent_session_id`.\n- The relationship is parent-only. Do not add a reverse child-session\n  ownership rail.\n- Does not resolve Process/Thread/Layout/Attention.\n- Does not grant roles; Identity ActorRole truth remains separate.',
                "is_constructor": True,
            },
            "input": SessionBuildViaSessionConfigInput,
            "output": SessionBuildViaSessionConfigOutput,
        },
    },
}

__all__ = [
    "Session",
    "SessionJoinActorInput",
    "SessionJoinActorOutput",
    "SessionAttachProviderSessionInput",
    "SessionAttachProviderSessionOutput",
    "SessionBuildViaSessionConfigInput",
    "SessionBuildViaSessionConfigOutput",
    "FUNCTIONS",
]
