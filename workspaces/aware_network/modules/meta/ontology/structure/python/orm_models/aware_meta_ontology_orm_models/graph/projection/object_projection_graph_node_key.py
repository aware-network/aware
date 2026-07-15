from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.config.object_config_graph_binding_class import (
        ObjectConfigGraphBindingClass,
    )


class ObjectProjectionGraphNodeKey(ORMModel):
    """
    Canonical ProjectionKey owner rail under one ObjectProjectionGraphNode.
    Contract:
    - Binds one projected node to one canonical OCG binding-class anchor.
    - Consumes binding + formula semantics without reintroducing encode logic here.
    - Must fail closed if the binding-class target class/attr is incompatible with the projected node.
    """

    # Relationships
    object_config_graph_binding_class: ObjectConfigGraphBindingClass

    # Attributes
    key: str
    position: int | None = Field(default=None)
    required: bool = Field(default=True)

    # Foreign Keys
    object_projection_graph_node_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphNode.object_projection_graph_node_keys"
    )
    object_config_graph_binding_class_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectProjectionGraphNodeKey.object_config_graph_binding_class"
    )
