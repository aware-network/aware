from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.config.object_config_graph_binding_class import ObjectConfigGraphBindingClass


class ObjectProjectionGraphNodeKey(BaseModel):
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
