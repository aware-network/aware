from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Interface Ontology Dto
from aware_interface_ontology_dto.interface.interface_enums import InterfaceOs

if TYPE_CHECKING:
    from aware_identity_ontology_dto.actor.actor import Actor
    from aware_interface_ontology_dto.interface.interface_environment import InterfaceEnvironment
    from aware_interface_ontology_dto.interface.interface_identity import InterfaceIdentity
    from aware_interface_ontology_dto.interface.interface_session import InterfaceSession
    from aware_interface_ontology_dto.interface.interface_window import InterfaceWindow
    from aware_network_ontology_dto.network.network_operation_hop import NetworkOperationHop


class Interface(BaseModel):
    # Relationships
    system_actor: Actor | None = Field(
        default=None,
        description="Interface-owned system Actor used for pre-operator provenance.\nContract:\n- Interface bootstrap/admission actions are never actorless.\n- The human/operator Actor is bound later by Identity admission.\n- This portal points at Identity's canonical system Actor for this Interface.",
    )
    interface_sessions: list[InterfaceSession] = Field(default_factory=list)
    interface_identities: list[InterfaceIdentity] = Field(default_factory=list)
    environments: list[InterfaceEnvironment] = Field(default_factory=list)
    interface_windows: list[InterfaceWindow] = Field(default_factory=list)
    source_network_operation_hops: list[NetworkOperationHop] = Field(default_factory=list)
    target_network_operation_hops: list[NetworkOperationHop] = Field(default_factory=list)

    # Attributes
    os: InterfaceOs
    version: str
