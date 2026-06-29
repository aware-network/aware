from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.annotation.code_section_annotation import CodeSectionAnnotation


class CodeSectionAnnotationDiscriminate(ORMModel):
    """
    Ontology-level view of a `discriminate` ANN.
    This represents discrimination union semantics for DTO/wire projections.
    It is produced from CodeSectionAnnotation entries where `verb == "discriminate"`.
    Canonical forms (path + args):
    - Base key:    ann <TypeRef>::<attribute> discriminate key
    - Variant tag: ann <TypeRef>::<attribute> discriminate tag <tag_value>
    """

    # Relationships
    code_section_annotation: CodeSectionAnnotation | None = Field(default=None, exclude=True)

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

    # Foreign Keys
    code_section_annotation_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionAnnotationDiscriminate.code_section_annotation"
    )
