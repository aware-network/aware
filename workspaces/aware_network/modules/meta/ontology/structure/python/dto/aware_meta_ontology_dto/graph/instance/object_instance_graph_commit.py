from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.code.code_enums import CodeLanguage

if TYPE_CHECKING:
    from aware_history_ontology_dto.commit.commit import Commit
    from aware_meta_ontology_dto.graph.instance.object_instance_graph import ObjectInstanceGraph
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_change import ObjectInstanceGraphChange


class ObjectInstanceGraphCommit(BaseModel):
    # Relationships
    object_instance_graph: ObjectInstanceGraph | None = Field(default=None)
    commit: Commit
    object_instance_graph_changes: list[ObjectInstanceGraphChange] = Field(default_factory=list)

    # Attributes
    object_instance_graph_key: str
    object_instance_graph_name: str
    object_instance_graph_description: str | None = Field(default=None)
    root_class_config_id: UUID
    root_source_object_id: UUID
    graph_hash_post: str
    graph_hash_pre: str
    projection_hash: str | None = Field(default=None)
    source_language: CodeLanguage
