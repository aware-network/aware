from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_network_ontology_dto.network.network_node import NetworkNode


class InterfaceIdentityNetworkNode(BaseModel):
    # Relationships
    network_node: NetworkNode | None = Field(default=None)

    # Attributes
    connected_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_ack_at: datetime | None = Field(default=None)
    disconnected_at: datetime | None = Field(default=None)
    last_delivery_offset: int = Field(default=0)
