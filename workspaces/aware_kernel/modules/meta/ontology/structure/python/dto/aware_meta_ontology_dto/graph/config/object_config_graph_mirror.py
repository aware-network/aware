from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.graph.config.object_config_graph_mirror_enums import ObjectConfigGraphMirrorTargetKind

if TYPE_CHECKING:
    from aware_code_ontology_dto.mirror.code_section_mirror import CodeSectionMirror
    from aware_meta_ontology_dto.class_.class_config import ClassConfig
    from aware_meta_ontology_dto.enum.enum_config import EnumConfig
    from aware_meta_ontology_dto.graph.config.object_config_graph import ObjectConfigGraph


class ObjectConfigGraphMirror(BaseModel):
    """
    Ontology-level view of a `mirror` statement.
    Mirrors declare an explicit allowlist of types that will be copied
    into the API DTO graph. This stays self-contained and avoids runtime
    ontology dependencies.
    """

    # Relationships
    source_object_config_graph: ObjectConfigGraph | None = Field(default=None)
    class_config: ClassConfig | None = Field(default=None)
    enum_config: EnumConfig | None = Field(default=None)
    code_section_mirror: CodeSectionMirror | None = Field(default=None)

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
