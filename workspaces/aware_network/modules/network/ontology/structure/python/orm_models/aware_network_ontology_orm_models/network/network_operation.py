from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Network Ontology Orm Models
from aware_network_ontology_orm_models.network.network_enums import (
    NetworkOperationMessageType,
    NetworkOperationType,
)

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_network_ontology_orm_models.network.network_operation_hop import NetworkOperationHop
    from aware_network_ontology_orm_models.network.network_request import NetworkRequest
    from aware_network_ontology_orm_models.network.network_response import NetworkResponse
    from aware_network_ontology_orm_models.network.network_stream import NetworkStream
    from aware_network_ontology_orm_models.network.network_stream_frame import NetworkStreamFrame


class NetworkOperation(ORMModel):
    # Relationships
    network_operation_hops: list[NetworkOperationHop] = Field(default_factory=list, exclude=True)
    network_request: NetworkRequest | None = Field(default=None, exclude=True)
    network_response: NetworkResponse | None = Field(default=None, exclude=True)
    network_stream: NetworkStream | None = Field(default=None, exclude=True)
    network_stream_frame: NetworkStreamFrame | None = Field(default=None, exclude=True)

    # Attributes
    message_type: NetworkOperationMessageType
    type: NetworkOperationType

    # Foreign Keys
    network_request_id: UUID | None = Field(
        default=None, description="Foreign key for NetworkOperation.network_request"
    )
    network_response_id: UUID | None = Field(
        default=None, description="Foreign key for NetworkOperation.network_response"
    )
    network_stream_id: UUID | None = Field(default=None, description="Foreign key for NetworkOperation.network_stream")
    network_stream_frame_id: UUID | None = Field(
        default=None, description="Foreign key for NetworkOperation.network_stream_frame"
    )
