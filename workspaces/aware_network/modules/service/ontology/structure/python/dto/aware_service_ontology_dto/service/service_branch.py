from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_service_ontology_dto.service.service_config_api_projection import ServiceConfigApiProjection


class ServiceBranch(BaseModel):
    # Relationships
    service_config_api_projection: ServiceConfigApiProjection | None = Field(default=None)
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
