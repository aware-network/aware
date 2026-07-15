from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Interface Ontology Dto
from aware_interface_ontology_dto.interface.interface_enums import InterfaceSessionState

if TYPE_CHECKING:
    from aware_identity_ontology_dto.session.session import Session
    from aware_interface_ontology_dto.interface.interface_session_experience_session import (
        InterfaceSessionExperienceSession,
    )


class InterfaceSession(BaseModel):
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
