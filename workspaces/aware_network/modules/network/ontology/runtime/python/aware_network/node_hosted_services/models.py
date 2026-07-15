from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from aware_network_service_dto.comms.models.network_node import (
    HostedServiceRuntimeServiceStatus,
    HostedServiceRuntimeStatus,
)


def utc_now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True, slots=True)
class HostedServiceRuntimeServiceStatusSnapshot:
    service_name: str
    endpoint_refs: tuple[str, ...] = ()
    stream_endpoint_refs: tuple[str, ...] = ()

    def to_api_model(self) -> HostedServiceRuntimeServiceStatus:
        return HostedServiceRuntimeServiceStatus(
            service_name=self.service_name,
            endpoint_refs=list(self.endpoint_refs),
            stream_endpoint_refs=list(self.stream_endpoint_refs),
        )


@dataclass(frozen=True, slots=True)
class HostedServiceRuntimeStatusSnapshot:
    host_id: str
    host_version: str | None = None
    protocol_version: str = ""
    readiness_status: str = "unknown"
    is_ready: bool = False
    is_alive: bool = False
    supports_stream_events: bool = False
    summary: str | None = None
    error: str | None = None
    updated_at: str | None = None
    services: tuple[HostedServiceRuntimeServiceStatusSnapshot, ...] = ()

    def to_api_model(self) -> HostedServiceRuntimeStatus:
        return HostedServiceRuntimeStatus(
            host_id=self.host_id,
            host_version=self.host_version,
            protocol_version=self.protocol_version,
            readiness_status=self.readiness_status,
            is_ready=self.is_ready,
            is_alive=self.is_alive,
            supports_stream_events=self.supports_stream_events,
            summary=self.summary,
            error=self.error,
            updated_at=self.updated_at or utc_now_iso(),
            services=[item.to_api_model() for item in self.services],
        )
