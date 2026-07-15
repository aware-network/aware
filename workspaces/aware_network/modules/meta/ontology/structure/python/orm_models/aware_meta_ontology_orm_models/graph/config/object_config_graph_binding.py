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
    from aware_meta_ontology_orm_models.graph.config.object_config_graph_binding_class import (
        ObjectConfigGraphBindingClass,
    )


class ObjectConfigGraphBinding(ORMModel):
    """
    Entry linking one source ObjectConfigGraph scope to one target ObjectConfigGraph
    through cross-layer zoom/binding semantics.
    """

    # Relationships
    target_object_config_graph: ObjectConfigGraph | None = Field(
        default=None, description="Target OCG for this binding. Source OCG scope is propagated by parent containment."
    )
    object_config_graph_binding_classes: list[ObjectConfigGraphBindingClass] = Field(default_factory=list)

    # Foreign Keys
    object_config_graph_id: UUID = Field(description="Foreign key for ObjectConfigGraph.object_config_graph_bindings")
    target_object_config_graph_id: UUID = Field(
        description="Foreign key for ObjectConfigGraphBinding.target_object_config_graph"
    )
