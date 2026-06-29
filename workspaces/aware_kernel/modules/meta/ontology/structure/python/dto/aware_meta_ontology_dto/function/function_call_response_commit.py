from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class FunctionCallResponseCommit(BaseModel):
    # Relationships
    object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(
        default=None, description="Association target reference to ObjectInstanceGraphCommit"
    )

    # Attributes
    position: int
