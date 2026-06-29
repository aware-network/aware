from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_config import ClassConfig
    from aware_meta_ontology_dto.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology_dto.enum.enum_config import EnumConfig
    from aware_meta_ontology_dto.graph.config.object_config_graph_node_layout import ObjectConfigGraphNodeLayout


class ObjectConfigGraphNode(BaseModel):
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
