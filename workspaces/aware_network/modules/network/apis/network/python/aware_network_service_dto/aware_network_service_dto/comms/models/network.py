from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Api Service Dto
from aware_api_service_dto.comms.models.api import ApiOperation

# Network Service Dto
from aware_network_service_dto.network.network_enums import (
    NetworkAppType,
    NetworkOperationMessageType,
    NetworkOperationType,
    NetworkRequestStatus,
)

# Service Service Dto
from aware_service_service_dto.comms.models.service import ServiceOperation

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_network_service_dto.comms.models.network_node import NetworkNodeOperation


class NetworkRequest(BaseModel):
    """Wire DTOs for NetworkOperation envelopes (graph/ORM agnostic)."""

    # Attributes
    id: UUID | None = Field(default=None)
    status: NetworkRequestStatus = Field(default=NetworkRequestStatus.pending)
    requester_id: UUID | None = Field(default=None)
    requester: JsonObject | None = Field(default=None)


class NetworkResponse(BaseModel):
    # Attributes
    id: UUID | None = Field(default=None)
    status: NetworkRequestStatus = Field(default=NetworkRequestStatus.pending)
    error: str | None = Field(default=None)
    network_request_id: UUID | None = Field(default=None)


class NetworkOperationHop(BaseModel):
    # Attributes
    source_app_type: NetworkAppType
    target_app_type: NetworkAppType
    source_node_id: UUID | None = Field(default=None)
    source_interface_id: UUID | None = Field(default=None)
    source_environment_id: UUID | None = Field(default=None)
    target_node_id: UUID | None = Field(default=None)
    target_interface_id: UUID | None = Field(default=None)
    target_environment_id: UUID | None = Field(default=None)


class NetworkOperation(BaseModel):
    # Attributes
    id: UUID
    message_type: NetworkOperationMessageType = Field(default=NetworkOperationMessageType.notification)
    type: NetworkOperationType = Field(default=NetworkOperationType.api)
    network_operation_hop_list: list[NetworkOperationHop] = Field(default_factory=list)
    network_request: NetworkRequest | None = Field(default=None)
    network_response: NetworkResponse | None = Field(default=None)
    api_operation: ApiOperation | None = Field(default=None)
    service_operation: ServiceOperation | None = Field(default=None)
    network_node_operation: NetworkNodeOperation | None = Field(default=None)
