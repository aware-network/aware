from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.config.object_config_graph import ObjectConfigGraph


class ProgramConfigGraphObjectConfigGraph(BaseModel):
    """Bridge between Experience-Structure via ProgramConfigGraph-ObjectConfigGraph."""

    # Relationships
    object_config_graph: ObjectConfigGraph | None = Field(default=None)

    # Attributes
    key: str | None = Field(default=None)
