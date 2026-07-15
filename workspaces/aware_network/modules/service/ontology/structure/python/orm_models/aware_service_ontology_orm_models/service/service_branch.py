from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_service_ontology_orm_models.service.service_config_api_projection import ServiceConfigApiProjection


class ServiceBranch(ORMModel):
    # Relationships
    service_config_api_projection: ServiceConfigApiProjection | None = Field(default=None, exclude=True)
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    service_id: UUID = Field(description="Foreign key for Service.branches")
    service_config_api_projection_id: UUID = Field(
        description="Foreign key for ServiceBranch.service_config_api_projection"
    )
    object_instance_graph_branch_id: UUID = Field(
        description="Foreign key for ServiceBranch.object_instance_graph_branch"
    )
