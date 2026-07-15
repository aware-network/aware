from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Interface Ontology Orm Models
from aware_interface_ontology_orm_models.interface.interface_enums import InterfaceOs

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.actor.actor import Actor
    from aware_interface_ontology_orm_models.interface.interface_environment import InterfaceEnvironment
    from aware_interface_ontology_orm_models.interface.interface_identity import InterfaceIdentity
    from aware_interface_ontology_orm_models.interface.interface_session import InterfaceSession
    from aware_interface_ontology_orm_models.interface.interface_window import InterfaceWindow
    from aware_network_ontology_orm_models.network.network_operation_hop import NetworkOperationHop


class Interface(ORMModel):
    # Relationships
    system_actor: Actor | None = Field(
        default=None,
        exclude=True,
        description="Interface-owned system Actor used for pre-operator provenance.\nContract:\n- Interface bootstrap/admission actions are never actorless.\n- The human/operator Actor is bound later by Identity admission.\n- This portal points at Identity's canonical system Actor for this Interface.",
    )
    interface_sessions: list[InterfaceSession] = Field(default_factory=list, exclude=True)
    interface_identities: list[InterfaceIdentity] = Field(default_factory=list, exclude=True)
    environments: list[InterfaceEnvironment] = Field(default_factory=list, exclude=True)
    interface_windows: list[InterfaceWindow] = Field(default_factory=list, exclude=True)
    source_network_operation_hops: list[NetworkOperationHop] = Field(default_factory=list, exclude=True)
    target_network_operation_hops: list[NetworkOperationHop] = Field(default_factory=list, exclude=True)

    # Attributes
    os: InterfaceOs
    version: str

    # Foreign Keys
    interface_config_id: UUID = Field(description="Foreign key for InterfaceConfig.interfaces")
    system_actor_id: UUID | None = Field(default=None, description="Foreign key for Interface.system_actor")
