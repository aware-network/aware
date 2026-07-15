from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Network Ontology
from aware_network_ontology.network.network_enums import NetworkRequestStatus

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_network_ontology.network.network_request import NetworkRequest


class NetworkResponse(ORMModel):
    # Relationships
    network_request: NetworkRequest | None = Field(default=None, exclude=True)

    # Attributes
    error: str | None = Field(default=None)
    status: NetworkRequestStatus

    # Foreign Keys
    network_request_id: UUID = Field(description="Foreign key for NetworkResponse.network_request")


FUNCTIONS = {
    "NetworkResponse": {},
}

__all__ = [
    "NetworkResponse",
    "FUNCTIONS",
]
