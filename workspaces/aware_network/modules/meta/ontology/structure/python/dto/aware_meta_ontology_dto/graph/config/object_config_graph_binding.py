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
    from aware_meta_ontology_dto.graph.config.object_config_graph_binding_class import ObjectConfigGraphBindingClass


class ObjectConfigGraphBinding(BaseModel):
    """
    Entry linking one source ObjectConfigGraph scope to one target ObjectConfigGraph
    through cross-layer zoom/binding semantics.
    """

    # Relationships
    target_object_config_graph: ObjectConfigGraph | None = Field(
        default=None, description="Target OCG for this binding. Source OCG scope is propagated by parent containment."
    )
    object_config_graph_binding_classes: list[ObjectConfigGraphBindingClass] = Field(default_factory=list)
