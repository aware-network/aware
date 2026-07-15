from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_view_capability_endpoint import ApiViewCapabilityEndpoint
    from aware_api_ontology_orm_models.api.api_view_stream_policy import ApiViewStreamPolicy
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph_observable import (
        ObjectProjectionGraphObservable,
    )


class ApiView(ORMModel):
    """
    API-owned readable view-state contract.
    Contract:
    - `ApiCapabilityEndpoint` is for doing.
    - `ApiView` is for seeing.
    - The observable remains Meta-owned.
    - The state model is the exact DTO/ClassConfig a service must fulfill.
    """

    # Relationships
    object_projection_graph_observable: ObjectProjectionGraphObservable | None = Field(default=None, exclude=True)
    state_model: ClassConfig | None = Field(default=None, exclude=True)
    stream_policy: ApiViewStreamPolicy | None = Field(default=None)
    capability_endpoints: list[ApiViewCapabilityEndpoint] = Field(default_factory=list)

    # Attributes
    name: str
    view_ref: str
    view_key: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    api_id: UUID = Field(description="Foreign key for Api.api_views")
    object_projection_graph_observable_id: UUID = Field(
        description="Foreign key for ApiView.object_projection_graph_observable"
    )
    state_model_id: UUID = Field(description="Foreign key for ApiView.state_model")
