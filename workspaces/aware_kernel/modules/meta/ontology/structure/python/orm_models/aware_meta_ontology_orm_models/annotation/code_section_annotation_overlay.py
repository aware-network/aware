from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.code.code_enums import CodeLanguage

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.annotation.code_section_annotation import CodeSectionAnnotation


class CodeSectionAnnotationOverlay(ORMModel):
    """
    Ontology-level view of a `overlay` ANN.
    This sits on top of the generic CodeSectionAnnotation and captures
    the resolved, object-centric semantics used by overlays.
    It is intentionally grammar-agnostic: the compiler only knows about
    CodeSectionAnnotation entries where `verb == \"overlay\"`.
    """

    # Relationships
    code_section_annotation: CodeSectionAnnotation | None = Field(default=None, exclude=True)

    # Attributes
    source_path: str = Field(
        description='Original raw ANN path (e.g. "pkg.namespace.Class::attribute").\nStored here so overlay application can reason about edge-endpoint overlays\nwithout depending on the primitive CodeSectionAnnotation graph.'
    )
    language: CodeLanguage
    entity: CodeSectionAnnotationOverlayEntity
    fqn_prefix: str = Field(description="Location within the canonical graph")
    namespace: str
    class_name: str | None = Field(default=None)
    attribute_name: str | None = Field(default=None)
    enum_name: str | None = Field(default=None)
    enum_option_name: str | None = Field(default=None)
    function_name: str | None = Field(default=None)
    rename: str | None = Field(default=None, description="Per-language identifier")
    wire_name: str | None = Field(
        default=None, description="Serialized name/value when different from rename/canonical."
    )

    # Foreign Keys
    code_section_annotation_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionAnnotationOverlay.code_section_annotation"
    )
