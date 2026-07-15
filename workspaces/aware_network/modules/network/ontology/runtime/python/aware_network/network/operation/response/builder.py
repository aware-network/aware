from uuid import UUID

from aware_network_service_dto.comms.models.network import NetworkRequestStatus
from aware_network_ontology.network.network_response import NetworkResponse


def build_network_response(
    network_request_id: UUID, status: NetworkRequestStatus, error: str | None = None
) -> NetworkResponse:
    return NetworkResponse(status=status, error=error, network_request_id=network_request_id)
