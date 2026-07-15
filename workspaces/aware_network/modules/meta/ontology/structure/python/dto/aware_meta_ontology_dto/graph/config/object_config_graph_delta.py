from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.code.code_enums import CodeLanguage

# History Ontology Dto
from aware_history_ontology_dto.change.change_enums import ChangeType

# Meta Ontology Dto
from aware_meta_ontology_dto.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType

# Types
from aware_types import JsonObject


class ObjectConfigGraphDelta(BaseModel):
    """
    DTO-only representation of "what changed" in an ObjectConfigGraph.
    Invariants:
    - This is NOT a commit envelope (no who/when, no parent pointers).
    - This is delta-only: for CREATE/UPDATE, `payload` holds the post-state snapshot; for DELETE, it is null.
    - Consumers may enforce `graph_hash_pre` as a precondition, but hashes are optional so deltas can be produced
    before a full post-hash is computed (e.g. during interactive compilation).
    """

    # Attributes
    object_config_graph_id: UUID
    language: CodeLanguage
    graph_hash_pre: str | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    node_deltas: list[ObjectConfigGraphNodeDelta] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ObjectConfigGraphNodeDelta(BaseModel):
    # Attributes
    change_type: ChangeType
    node_type: ObjectConfigGraphNodeType
    node_id: UUID | None = Field(default=None)
    entity_id: UUID
    payload: JsonObject | None = Field(default=None)
    entity_fqn: str | None = Field(default=None)
    source_relative_path: str | None = Field(default=None)
    notes: str | None = Field(default=None)
