from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_graph_projection import ApiGraphProjection


class ServiceConfigApiProjection(ORMModel):
    # Relationships
    api_graph_projection: ApiGraphProjection | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    service_config_api_id: UUID = Field(description="Foreign key for ServiceConfigApi.api_projections")
    api_graph_projection_id: UUID = Field(description="Foreign key for ServiceConfigApiProjection.api_graph_projection")
