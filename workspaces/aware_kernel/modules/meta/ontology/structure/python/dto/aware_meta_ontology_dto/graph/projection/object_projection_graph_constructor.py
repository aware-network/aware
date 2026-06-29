from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_config_function_config import ClassConfigFunctionConfig
    from aware_meta_ontology_dto.graph.projection.object_projection_graph import ObjectProjectionGraph
    from aware_meta_ontology_dto.graph.projection.object_projection_graph_node import ObjectProjectionGraphNode


class ObjectProjectionGraphConstructor(BaseModel):
    # Relationships
    root_node: ObjectProjectionGraphNode | None = Field(default=None)
    function_constructor: ClassConfigFunctionConfig | None = Field(default=None)
    object_projection_graph: ObjectProjectionGraph | None = Field(
        default=None, description="Reverse view for ObjectProjectionGraph.object_projection_graph_constructors"
    )
