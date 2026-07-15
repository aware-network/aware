from __future__ import annotations

from dataclasses import dataclass

from aware_service_service_dto.comms.models.service import (
    ServiceOperationRequest,
    ServiceOperationResponse,
)

from .app import ServiceHostApp


def build_aware_service_service_protocol_handler(
    *,
    app: ServiceHostApp | None = None,
) -> AwareServiceServiceProtocolHandler:
    return AwareServiceServiceProtocolHandler(app=app or ServiceHostApp())


@dataclass(frozen=True, slots=True)
class AwareServiceServiceProtocolHandler:
    service: ServiceApiProtocolHandler

    def __init__(self, *, app: ServiceHostApp) -> None:
        object.__setattr__(
            self,
            "service",
            ServiceApiProtocolHandler(
                operation=ServiceOperationCapabilityProtocolHandler(app=app)
            ),
        )


@dataclass(frozen=True, slots=True)
class ServiceApiProtocolHandler:
    operation: ServiceOperationCapabilityProtocolHandler


@dataclass(frozen=True, slots=True)
class ServiceOperationCapabilityProtocolHandler:
    app: ServiceHostApp

    async def invoke(
        self,
        request: ServiceOperationRequest,
    ) -> ServiceOperationResponse:
        return await self.app.handle_request(request=request)


__all__ = [
    "AwareServiceServiceProtocolHandler",
    "ServiceApiProtocolHandler",
    "ServiceOperationCapabilityProtocolHandler",
    "build_aware_service_service_protocol_handler",
]
