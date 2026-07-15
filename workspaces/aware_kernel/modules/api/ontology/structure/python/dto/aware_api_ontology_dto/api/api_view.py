from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_view_capability_endpoint import ApiViewCapabilityEndpoint
    from aware_api_ontology_dto.api.api_view_stream_policy import ApiViewStreamPolicy
    from aware_meta_ontology_dto.class_.class_config import ClassConfig
    from aware_meta_ontology_dto.graph.projection.object_projection_graph_observable import (
        ObjectProjectionGraphObservable,
    )


class ApiView(BaseModel):
    """
    API-owned readable view-state contract.
    Contract:
    - `ApiCapabilityEndpoint` is for doing.
    - `ApiView` is for seeing.
    - The observable remains Meta-owned.
    - The state model is the exact DTO/ClassConfig a service must fulfill.
    """

    # Relationships
    object_projection_graph_observable: ObjectProjectionGraphObservable | None = Field(default=None)
    state_model: ClassConfig | None = Field(default=None)
    stream_policy: ApiViewStreamPolicy | None = Field(default=None)
    capability_endpoints: list[ApiViewCapabilityEndpoint] = Field(default_factory=list)

    # Attributes
    name: str
    view_ref: str
    view_key: str | None = Field(default=None)
    description: str | None = Field(default=None)
