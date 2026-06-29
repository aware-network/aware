from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.code.code_enums import CodeLanguage

# Meta Ontology Dto
from aware_meta_ontology_dto.annotation.code_section_annotation_overlay_enums import CodeSectionAnnotationOverlayEntity

if TYPE_CHECKING:
    from aware_code_ontology_dto.annotation.code_section_annotation import CodeSectionAnnotation


class CodeSectionAnnotationOverlay(BaseModel):
    """
    Ontology-level view of a `overlay` ANN.
    This sits on top of the generic CodeSectionAnnotation and captures
    the resolved, object-centric semantics used by overlays.
    It is intentionally grammar-agnostic: the compiler only knows about
    CodeSectionAnnotation entries where `verb == \"overlay\"`.
    """

    # Relationships
    code_section_annotation: CodeSectionAnnotation | None = Field(default=None)

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
