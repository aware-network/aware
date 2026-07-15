from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Network Ontology Dto
from aware_network_ontology_dto.network.network_enums import NetworkRequestStatus

if TYPE_CHECKING:
    from aware_network_ontology_dto.network.network_request import NetworkRequest


class NetworkResponse(BaseModel):
    # Relationships
    network_request: NetworkRequest | None = Field(default=None)

    # Attributes
    error: str | None = Field(default=None)
    status: NetworkRequestStatus
