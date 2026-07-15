from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.annotation.code_section_annotation import CodeSectionAnnotation


class CodeSectionAnnotationDiscriminate(BaseModel):
    """
    Ontology-level view of a `discriminate` ANN.
    This represents discrimination union semantics for DTO/wire projections.
    It is produced from CodeSectionAnnotation entries where `verb == "discriminate"`.
    Canonical forms (path + args):
    - Base key:    ann <TypeRef>::<attribute> discriminate key
    - Variant tag: ann <TypeRef>::<attribute> discriminate tag <tag_value>
    """

    # Relationships
    code_section_annotation: CodeSectionAnnotation | None = Field(default=None)

    # Attributes
    fqn_prefix: str = Field(description="Location within the canonical graph")
    namespace: str
    class_name: str
    attribute_name: str
    mode: str = Field(
        description='Discrimination semantics\n- "key": declares the discriminator key field on the base type\n- "tag": declares the wire tag value for a variant type'
    )
    tag_value: str | None = Field(default=None)
    source_position: int | None = Field(
        default=None,
        description='Optional source position (byte offset) for deterministic tag ordering.\nOnly populated for mode="tag" annotations.',
    )
