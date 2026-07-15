from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Interface Ontology
from aware_interface_ontology.interface.interface_enums import InterfaceSessionState

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
    from aware_interface_ontology.interface.interface_session_experience_session import (
        InterfaceSessionExperienceSession,
    )


class InterfaceSession(ORMModel):
    """
    Per-actor/client Interface attachment to one canonical Identity Session.
    Contract:
    - Identity Session owns participation, membership, ActorRole evidence,
    lifecycle, and provider-session attachments.
    - InterfaceSession owns only renderer/device attachment state.
    - Many InterfaceSessions may attach to the same Identity Session.
    - The Identity Session must be supplied explicitly; it is never inferred
    from InterfaceIdentity, actor, name, or transport bindings.
    """

    # Relationships
    identity_session: Session | None = Field(default=None)
    experience_sessions: list[InterfaceSessionExperienceSession] = Field(
        default_factory=list,
        description="Interface-owned portals to committed ExperienceSession authorities.\nContract:\n- One InterfaceSession may mount many ExperienceSessions.\n- Experience owns every ExperienceSession and its downstream state.\n- This collection does not select one globally active ExperienceSession.",
    )

    # Attributes
    name: str
    state: InterfaceSessionState

    # Foreign Keys
    interface_id: UUID = Field(description="Foreign key for Interface.interface_sessions")
    identity_session_id: UUID = Field(description="Foreign key for InterfaceSession.identity_session")

    async def mount_experience_session(
        self, experience_session_id: UUID, status: str = "active", metadata_json: JsonObject | None = {}
    ) -> InterfaceSessionExperienceSession:
        """
        Mount one committed ExperienceSession through this InterfaceSession.

        Contract:
        - Stable identity is InterfaceSession plus ExperienceSession.
        - ExperienceSession is an Experience-owned projection portal target.
        - Mounting records provenance only; it does not activate a profile,
          lens, Environment, AttentionSession, or ExperienceSession globally.
        """

        payload = {"experience_session_id": experience_session_id, "status": status, "metadata_json": metadata_json}
        result = await invoke_instance(orm_model=self, function_name="mount_experience_session", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.interface_session_experience_session import (
            InterfaceSessionExperienceSession,
        )

        if isinstance(value, InterfaceSessionExperienceSession):
            return value
        return InterfaceSessionExperienceSession.validate_invocation_value(value)

    @classmethod
    async def build_via_interface(
        cls,
        interface_id: UUID,
        identity_session_id: UUID,
        name: str,
        state: InterfaceSessionState = InterfaceSessionState.active,
    ) -> InterfaceSession:
        """
        Construct one commit-backed client attachment under Interface and
        Interface parent scope.

        Contract:
        - Stable identity is Interface + Identity Session + normalized name.
        - Interface identifies the concrete shared door/client attachment.
        - Identity Session owns all participating actors; this durable session
          is not parented by one InterfaceIdentity.
        - This constructor does not register a transport connection or mint a
          bearer token.
        - Identity owns membership, roles, lifecycle, and provider sessions.
        """

        payload = {
            "interface_id": interface_id,
            "identity_session_id": identity_session_id,
            "name": name,
            "state": state,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_interface", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, InterfaceSession):
            return value
        return InterfaceSession.validate_invocation_value(value)


class InterfaceSessionMountExperienceSessionInput(BaseModel):
    experience_session_id: UUID
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class InterfaceSessionMountExperienceSessionOutput(BaseModel):
    value: InterfaceSessionExperienceSession


class InterfaceSessionBuildViaInterfaceInput(BaseModel):
    interface_id: UUID = Field(description="Foreign key for Interface.interface_sessions")
    identity_session_id: UUID
    name: str
    state: InterfaceSessionState = Field(default=InterfaceSessionState.active)


class InterfaceSessionBuildViaInterfaceOutput(BaseModel):
    value: InterfaceSession


FUNCTIONS = {
    "InterfaceSession": {
        "mount_experience_session": {
            "canonical": {
                "name": "mount_experience_session",
                "description": "Mount one committed ExperienceSession through this InterfaceSession.\n\nContract:\n- Stable identity is InterfaceSession plus ExperienceSession.\n- ExperienceSession is an Experience-owned projection portal target.\n- Mounting records provenance only; it does not activate a profile,\n  lens, Environment, AttentionSession, or ExperienceSession globally.",
                "is_constructor": False,
            },
            "input": InterfaceSessionMountExperienceSessionInput,
            "output": InterfaceSessionMountExperienceSessionOutput,
        },
        "build_via_interface": {
            "canonical": {
                "name": "build_via_interface",
                "description": "Construct one commit-backed client attachment under Interface and\nInterface parent scope.\n\nContract:\n- Stable identity is Interface + Identity Session + normalized name.\n- Interface identifies the concrete shared door/client attachment.\n- Identity Session owns all participating actors; this durable session\n  is not parented by one InterfaceIdentity.\n- This constructor does not register a transport connection or mint a\n  bearer token.\n- Identity owns membership, roles, lifecycle, and provider sessions.",
                "is_constructor": True,
            },
            "input": InterfaceSessionBuildViaInterfaceInput,
            "output": InterfaceSessionBuildViaInterfaceOutput,
        },
    },
}

__all__ = [
    "InterfaceSession",
    "InterfaceSessionMountExperienceSessionInput",
    "InterfaceSessionMountExperienceSessionOutput",
    "InterfaceSessionBuildViaInterfaceInput",
    "InterfaceSessionBuildViaInterfaceOutput",
    "FUNCTIONS",
]
