from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_view import ApiView
    from aware_service_ontology_dto.service.service_config_api import ServiceConfigApi


class ServiceOperationConfigApiView(BaseModel):
    # Relationships
    api_view: ApiView | None = Field(default=None)
    service_config_api: ServiceConfigApi | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
