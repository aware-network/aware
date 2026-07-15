from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
)

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.annotation.code_section_annotation_discriminate import (
        CodeSectionAnnotationDiscriminate,
    )
    from aware_meta_ontology_orm_models.annotation.code_section_annotation_identity import CodeSectionAnnotationIdentity
    from aware_meta_ontology_orm_models.annotation.code_section_annotation_index import CodeSectionAnnotationIndex
    from aware_meta_ontology_orm_models.annotation.code_section_annotation_load import CodeSectionAnnotationLoad
    from aware_meta_ontology_orm_models.annotation.code_section_annotation_oneof import CodeSectionAnnotationOneOf
    from aware_meta_ontology_orm_models.annotation.code_section_annotation_overlay import CodeSectionAnnotationOverlay
    from aware_meta_ontology_orm_models.annotation.code_section_annotation_override import CodeSectionAnnotationOverride
    from aware_meta_ontology_orm_models.annotation.code_section_annotation_reference import (
        CodeSectionAnnotationReference,
    )
    from aware_meta_ontology_orm_models.annotation.code_section_annotation_storage import CodeSectionAnnotationStorage


class ObjectConfigGraphAnnotation(ORMModel):
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

    # Foreign Keys
    object_config_graph_id: UUID = Field(
        description="Foreign key for ObjectConfigGraph.object_config_graph_annotations"
    )
    code_section_annotation_discriminate_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphAnnotation.code_section_annotation_discriminate"
    )
    code_section_annotation_load_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphAnnotation.code_section_annotation_load"
    )
    code_section_annotation_overlay_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphAnnotation.code_section_annotation_overlay"
    )
    code_section_annotation_override_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphAnnotation.code_section_annotation_override"
    )
    code_section_annotation_oneof_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphAnnotation.code_section_annotation_oneof"
    )
    code_section_annotation_identity_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphAnnotation.code_section_annotation_identity"
    )
    code_section_annotation_reference_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphAnnotation.code_section_annotation_reference"
    )
    code_section_annotation_index_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphAnnotation.code_section_annotation_index"
    )
    code_section_annotation_storage_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphAnnotation.code_section_annotation_storage"
    )
