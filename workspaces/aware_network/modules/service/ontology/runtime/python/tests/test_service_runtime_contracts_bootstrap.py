from __future__ import annotations

from _service_runtime_test_paths import REPO_ROOT

from aware_service_service_dto.comms.models.service import (
    RequestStatus as CommsRequestStatus,
    ServiceOperationContext as CommsServiceOperationContext,
    ServiceOperationRequest as CommsServiceOperationRequest,
    ServiceOperationResponse as CommsServiceOperationResponse,
    StreamLifecycle as CommsStreamLifecycle,
)
from aware_service_service_dto.comms.models.service import (
    RequestStatus as ApiRequestStatus,
    ServiceOperationContext as ApiServiceOperationContext,
    ServiceOperationRequest as ApiServiceOperationRequest,
    ServiceOperationResponse as ApiServiceOperationResponse,
    StreamLifecycle as ApiStreamLifecycle,
)
from aware_service_runtime.contracts import (
    RequestStatus,
    ServiceOperationContext,
    ServiceOperationRequest,
    ServiceOperationResponse,
    StreamLifecycle,
)


def test_service_runtime_contracts_use_api_owned_remote_models() -> None:
    assert RequestStatus is ApiRequestStatus
    assert StreamLifecycle is ApiStreamLifecycle
    assert ServiceOperationContext is ApiServiceOperationContext
    assert ServiceOperationRequest is ApiServiceOperationRequest
    assert ServiceOperationResponse is ApiServiceOperationResponse
    assert CommsRequestStatus is ApiRequestStatus
    assert CommsStreamLifecycle is ApiStreamLifecycle
    assert CommsServiceOperationContext is ApiServiceOperationContext
    assert CommsServiceOperationRequest is ApiServiceOperationRequest
    assert CommsServiceOperationResponse is ApiServiceOperationResponse


def test_network_operation_carries_service_payload_family() -> None:
    network_enum_source = (
        REPO_ROOT
        / "workspaces/aware_network/modules/network/ontology/structure/aware/network/network_enums.aware"
    ).read_text()
    network_operation_source = (
        REPO_ROOT
        / "workspaces/aware_network/modules/network/apis/network/dto/aware/comms/models/network.aware"
    ).read_text()

    assert "service" in network_enum_source
    assert (
        "service_operation aware_service_service_dto.comms.models.ServiceOperation?"
        in network_operation_source
    )
