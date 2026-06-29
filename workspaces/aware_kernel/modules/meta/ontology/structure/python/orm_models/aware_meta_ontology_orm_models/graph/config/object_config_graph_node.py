from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig
    from aware_meta_ontology_orm_models.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology_orm_models.enum.enum_config import EnumConfig
    from aware_meta_ontology_orm_models.graph.config.object_config_graph_node_layout import ObjectConfigGraphNodeLayout


class ObjectConfigGraphNode(ORMModel):
    # Relationships
    enum_config: EnumConfig | None = Field(default=None)
    class_config: ClassConfig | None = Field(default=None)
    class_config_relationship: ClassConfigRelationship | None = Field(default=None)
    layouts: list[ObjectConfigGraphNodeLayout] = Field(default_factory=list)

    # Attributes
    type: ObjectConfigGraphNodeType
    node_key: str = Field(
        description="Canonical semantic identity for this node lane.\nExamples:\n- class node: class FQN\n- enum node: enum FQN\n- relationship node: canonical relationship fingerprint"
    )

    # Foreign Keys
    object_config_graph_id: UUID = Field(description="Foreign key for ObjectConfigGraph.object_config_graph_nodes")
    class_config_relationship_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphNode.class_config_relationship"
    )
