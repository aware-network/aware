from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_service_ontology_dto.service.service import Service
    from aware_service_ontology_dto.service.service_package import ServicePackage


class NetworkNodeService(BaseModel):
    # Relationships
    service: Service | None = Field(default=None)
    service_package: ServicePackage | None = Field(default=None)

    # Attributes
    endpoint_refs: list[str] = Field(default_factory=list)
    host_id: str
    host_version: str | None = Field(default=None)
    protocol_version: str
    service_name: str
    stream_endpoint_refs: list[str] = Field(default_factory=list)
    supports_stream_events: bool = Field(default=False)
