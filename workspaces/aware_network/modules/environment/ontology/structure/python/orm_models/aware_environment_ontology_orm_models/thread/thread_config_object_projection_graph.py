from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph import ObjectProjectionGraph


class ThreadConfigObjectProjectionGraph(ORMModel):
    """
    Environment ThreadConfig -> Meta ObjectProjectionGraph authority edge.
    Contract:
    - Declares which projection graphs a thread config can host.
    - Does not identify an Experience or view implementation.
    """

    # Relationships
    object_projection_graph: ObjectProjectionGraph | None = Field(default=None)

    # Attributes
    narrative: str | None = Field(
        default=None, description="Narrative text for why this projection graph is part of the thread context."
    )
    intent: str | None = Field(default=None, description="Short canonical intent for this projection graph landing.")
    view_key: str | None = Field(
        default=None, description="Optional canonical view key under the target projection identity."
    )
    position: int | None = Field(default=None, description="Ordering hint for projection clusters.")
    is_default: bool = Field(
        default=False, description="Marks preferred/default projection graph for this thread config."
    )

    # Foreign Keys
    thread_config_id: UUID = Field(description="Foreign key for ThreadConfig.object_projection_graphs")
    object_projection_graph_id: UUID = Field(
        description="Foreign key for ThreadConfigObjectProjectionGraph.object_projection_graph"
    )
