from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Interface Ontology Orm Models
from aware_interface_ontology_orm_models.interface.interface_enums import InterfaceSessionState

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.session.session import Session
    from aware_interface_ontology_orm_models.interface.interface_session_experience_session import (
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
