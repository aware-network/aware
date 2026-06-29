from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.graph.config.object_config_graph_mirror_enums import (
    ObjectConfigGraphMirrorTargetKind,
)

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.mirror.code_section_mirror import CodeSectionMirror
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig
    from aware_meta_ontology_orm_models.enum.enum_config import EnumConfig
    from aware_meta_ontology_orm_models.graph.config.object_config_graph import ObjectConfigGraph


class ObjectConfigGraphMirror(ORMModel):
    """
    Ontology-level view of a `mirror` statement.
    Mirrors declare an explicit allowlist of types that will be copied
    into the API DTO graph. This stays self-contained and avoids runtime
    ontology dependencies.
    """

    # Relationships
    source_object_config_graph: ObjectConfigGraph | None = Field(default=None, exclude=True)
    class_config: ClassConfig | None = Field(default=None, exclude=True)
    enum_config: EnumConfig | None = Field(default=None, exclude=True)
    code_section_mirror: CodeSectionMirror | None = Field(default=None, exclude=True)

    # Attributes
    fqn_prefix: str = Field(description="Location within the canonical graph")
    namespace: str
    target_text: str = Field(description="Mirror target text as written in source (fully-qualified symbol).")
    layout_kind: str = Field(
        default="aware", description="Layout metadata for deterministic placement in generated DTO packages."
    )
    relative_path: str
    source_position: int | None = Field(default=None)
    target_kind: ObjectConfigGraphMirrorTargetKind = Field(
        description="Target identity (exactly one of class_name/enum_name is set)"
    )

    # Foreign Keys
    object_config_graph_id: UUID = Field(description="Foreign key for ObjectConfigGraph.object_config_graph_mirrors")
    source_object_config_graph_id: UUID = Field(
        description="Foreign key for ObjectConfigGraphMirror.source_object_config_graph"
    )
    class_config_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphMirror.class_config"
    )
    enum_config_id: UUID | None = Field(default=None, description="Foreign key for ObjectConfigGraphMirror.enum_config")
    code_section_mirror_id: UUID = Field(description="Foreign key for ObjectConfigGraphMirror.code_section_mirror")
