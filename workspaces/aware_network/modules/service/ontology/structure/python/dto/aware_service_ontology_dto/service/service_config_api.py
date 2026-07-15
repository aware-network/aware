from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api import Api
    from aware_service_ontology_dto.service.service_config_api_projection import ServiceConfigApiProjection


class ServiceConfigApi(BaseModel):
    # Relationships
    api: Api | None = Field(default=None)
    api_projections: list[ServiceConfigApiProjection] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
