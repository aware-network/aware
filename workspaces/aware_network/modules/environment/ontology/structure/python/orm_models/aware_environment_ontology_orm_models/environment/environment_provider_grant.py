from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.process.process_config import ProcessConfig
    from aware_environment_ontology_orm_models.thread.thread_config import ThreadConfig
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph import ObjectProjectionGraph


class EnvironmentProviderGrant(ORMModel):
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

    # Foreign Keys
    environment_provider_id: UUID = Field(description="Foreign key for EnvironmentProvider.grants")
    process_config_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentProviderGrant.process_config"
    )
    thread_config_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentProviderGrant.thread_config"
    )
    object_projection_graph_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentProviderGrant.object_projection_graph"
    )
