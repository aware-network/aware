from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_config_function_config import ClassConfigFunctionConfig
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph import ObjectProjectionGraph
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph_node import ObjectProjectionGraphNode


class ObjectProjectionGraphConstructor(ORMModel):
    # Relationships
    root_node: ObjectProjectionGraphNode | None = Field(default=None, exclude=True)
    function_constructor: ClassConfigFunctionConfig | None = Field(default=None, exclude=True)
    object_projection_graph: ObjectProjectionGraph | None = Field(
        default=None,
        exclude=True,
        description="Reverse view for ObjectProjectionGraph.object_projection_graph_constructors",
    )

    # Foreign Keys
    object_projection_graph_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraph.object_projection_graph_constructors"
    )
    root_node_id: UUID = Field(description="Foreign key for ObjectProjectionGraphConstructor.root_node")
    function_constructor_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphConstructor.function_constructor"
    )
