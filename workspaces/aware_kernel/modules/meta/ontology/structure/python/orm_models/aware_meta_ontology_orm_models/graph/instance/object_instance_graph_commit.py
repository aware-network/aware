from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.code.code_enums import CodeLanguage

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_history_ontology_orm_models.commit.commit import Commit
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph import ObjectInstanceGraph
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_change import ObjectInstanceGraphChange


class ObjectInstanceGraphCommit(ORMModel):
    # Relationships
    object_instance_graph: ObjectInstanceGraph | None = Field(default=None, exclude=True)
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

    # Foreign Keys
    object_instance_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphIdentity.object_instance_graph_commits"
    )
    object_instance_graph_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphCommit.object_instance_graph"
    )
    commit_id: UUID | None = Field(default=None, description="Foreign key for ObjectInstanceGraphCommit.commit")
