from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_environment_ontology_dto.process.process_config import ProcessConfig
    from aware_environment_ontology_dto.thread.thread_config import ThreadConfig
    from aware_meta_ontology_dto.graph.projection.object_projection_graph import ObjectProjectionGraph


class EnvironmentProviderGrant(BaseModel):
    """
    Provider-neutral grant over an EnvironmentProfileConfig scope.
    Contract:
    - Environment owns the grant contract.
    - Experience may bind to the grant, but Environment never references Experience.
    - Service/provider fulfillment remains outside this ontology.
    """

    # Relationships
    process_config: ProcessConfig | None = Field(default=None)
    thread_config: ThreadConfig | None = Field(default=None)
    object_projection_graph: ObjectProjectionGraph | None = Field(default=None)

    # Attributes
    action_scope: str | None = Field(default=None)
    description: str | None = Field(default=None)
    grant_key: str
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
    scope_kind: str = Field(default="profile")
    status: str = Field(default="active")
