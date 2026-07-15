from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_service_ontology_orm_models.service.service import Service
    from aware_service_ontology_orm_models.service.service_package import ServicePackage


class NetworkNodeService(ORMModel):
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

    # Foreign Keys
    network_node_id: UUID = Field(description="Foreign key for NetworkNode.services")
    service_id: UUID = Field(description="Foreign key for NetworkNodeService.service")
    service_package_id: UUID = Field(description="Foreign key for NetworkNodeService.service_package")
