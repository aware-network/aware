from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.graph.config.object_config_graph_annotation_enums import ObjectConfigGraphAnnotationKind

if TYPE_CHECKING:
    from aware_meta_ontology_dto.annotation.code_section_annotation_discriminate import (
        CodeSectionAnnotationDiscriminate,
    )
    from aware_meta_ontology_dto.annotation.code_section_annotation_identity import CodeSectionAnnotationIdentity
    from aware_meta_ontology_dto.annotation.code_section_annotation_index import CodeSectionAnnotationIndex
    from aware_meta_ontology_dto.annotation.code_section_annotation_load import CodeSectionAnnotationLoad
    from aware_meta_ontology_dto.annotation.code_section_annotation_oneof import CodeSectionAnnotationOneOf
    from aware_meta_ontology_dto.annotation.code_section_annotation_overlay import CodeSectionAnnotationOverlay
    from aware_meta_ontology_dto.annotation.code_section_annotation_override import CodeSectionAnnotationOverride
    from aware_meta_ontology_dto.annotation.code_section_annotation_reference import CodeSectionAnnotationReference
    from aware_meta_ontology_dto.annotation.code_section_annotation_storage import CodeSectionAnnotationStorage


class ObjectConfigGraphAnnotation(BaseModel):
    """
    Single annotation instance attached to an ObjectConfigGraph
    This provides a polymorphic wrapper around verb-specific views such as
    CodeSectionAnnotationLoad / CodeSectionAnnotationOverlay, while keeping
    primitive models free of meta dependencies.
    """

    # Relationships
    code_section_annotation_discriminate: CodeSectionAnnotationDiscriminate | None = Field(default=None)
    code_section_annotation_load: CodeSectionAnnotationLoad | None = Field(default=None)
    code_section_annotation_overlay: CodeSectionAnnotationOverlay | None = Field(default=None)
    code_section_annotation_override: CodeSectionAnnotationOverride | None = Field(default=None)
    code_section_annotation_oneof: CodeSectionAnnotationOneOf | None = Field(default=None)
    code_section_annotation_identity: CodeSectionAnnotationIdentity | None = Field(default=None)
    code_section_annotation_reference: CodeSectionAnnotationReference | None = Field(default=None)
    code_section_annotation_index: CodeSectionAnnotationIndex | None = Field(default=None)
    code_section_annotation_storage: CodeSectionAnnotationStorage | None = Field(default=None)

    # Attributes
    kind: ObjectConfigGraphAnnotationKind
