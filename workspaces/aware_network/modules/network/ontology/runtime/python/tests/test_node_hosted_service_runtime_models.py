from __future__ import annotations

from aware_network.node_hosted_services import (
    HostedServiceRuntimeServiceStatusSnapshot,
    HostedServiceRuntimeStatusSnapshot,
)


def test_hosted_service_runtime_status_snapshot_converts_to_api_model() -> None:
    snapshot = HostedServiceRuntimeStatusSnapshot(
        host_id="aware_service_service",
        host_version="1.0.0",
        protocol_version="1",
        readiness_status="ready",
        is_ready=True,
        is_alive=True,
        supports_stream_events=True,
        summary="Hosted Service ready.",
        services=(
            HostedServiceRuntimeServiceStatusSnapshot(
                service_name="aware_home_devices",
                endpoint_refs=("home_devices.open_door.open_door",),
                stream_endpoint_refs=("home_devices.stream.home_stream",),
            ),
        ),
    )

    model = snapshot.to_api_model()

    assert model.host_id == "aware_service_service"
    assert model.readiness_status == "ready"
    assert model.is_ready is True
    assert model.is_alive is True
    assert model.supports_stream_events is True
    assert model.summary == "Hosted Service ready."
    assert model.updated_at is not None
    assert len(model.services) == 1
    assert model.services[0].service_name == "aware_home_devices"
    assert model.services[0].endpoint_refs == ["home_devices.open_door.open_door"]
    assert model.services[0].stream_endpoint_refs == ["home_devices.stream.home_stream"]
