from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.config.object_config_graph import ObjectConfigGraph


class ProgramConfigGraphObjectConfigGraph(ORMModel):
    """Bridge between Experience-Structure via ProgramConfigGraph-ObjectConfigGraph."""

    # Relationships
    object_config_graph: ObjectConfigGraph | None = Field(default=None, exclude=True)

    # Attributes
    key: str | None = Field(default=None)

    # Foreign Keys
    program_config_graph_id: UUID = Field(description="Foreign key for ProgramConfigGraph.object_config_graphs")
    object_config_graph_id: UUID = Field(
        description="Foreign key for ProgramConfigGraphObjectConfigGraph.object_config_graph"
    )
