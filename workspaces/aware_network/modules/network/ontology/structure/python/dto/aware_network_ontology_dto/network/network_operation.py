from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Network Ontology Dto
from aware_network_ontology_dto.network.network_enums import (
    NetworkOperationMessageType,
    NetworkOperationType,
)

if TYPE_CHECKING:
    from aware_network_ontology_dto.network.network_operation_hop import NetworkOperationHop
    from aware_network_ontology_dto.network.network_request import NetworkRequest
    from aware_network_ontology_dto.network.network_response import NetworkResponse
    from aware_network_ontology_dto.network.network_stream import NetworkStream
    from aware_network_ontology_dto.network.network_stream_frame import NetworkStreamFrame


class NetworkOperation(BaseModel):
    # Relationships
    network_operation_hops: list[NetworkOperationHop] = Field(default_factory=list)
    network_request: NetworkRequest | None = Field(default=None)
    network_response: NetworkResponse | None = Field(default=None)
    network_stream: NetworkStream | None = Field(default=None)
    network_stream_frame: NetworkStreamFrame | None = Field(default=None)

    # Attributes
    message_type: NetworkOperationMessageType
    type: NetworkOperationType
