from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology
from aware_meta_ontology.annotation.code_section_annotation_storage_enums import CodeSectionAnnotationStorageOperation

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology.annotation.code_section_annotation import CodeSectionAnnotation


class CodeSectionAnnotationStorage(ORMModel):
    """
    Ontology-level view of a `storage` ANN.
    Purpose:
    - Declare SQL/storage-specific table-level indexes and uniqueness constraints.
    - Keep semantic identity (`key`) separate from physical storage constraints.
    Canonical surface (v0):
    - Storage index:  `ann schema.Class storage index by_name member1 member2 ...`
    - Storage unique: `ann schema.Class storage unique by_name member1 member2 ...`
    Notes:
    - `operation = index` declares a non-unique table-level index.
    - `operation = unique` declares table-level tuple uniqueness over `member_names`.
    - Attribute-level `unique` remains unary; class-attribute `key` remains semantic identity.
    - `member_names` are canonical class members (attributes / relationship pointers).
    - SQL lowering determines physical columns:
    - primitives/enums -> column name
    - relationship pointers -> FK column (`<member>_id`)
    - Collections/JSON/expression indexes are out of scope for v0.
    """

    # Relationships
    code_section_annotation: CodeSectionAnnotation | None = Field(default=None, exclude=True)

    # Attributes
    fqn_prefix: str = Field(description="Location within the canonical graph")
    namespace: str
    class_name: str
    name: str = Field(description="Operator-facing stable storage name.")
    operation: CodeSectionAnnotationStorageOperation = Field(
        description="Storage operation over the ordered member tuple."
    )
    member_names: list[str] = Field(
        default_factory=list, description="Canonical member names forming the storage key (order matters)."
    )

    # Foreign Keys
    code_section_annotation_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionAnnotationStorage.code_section_annotation"
    )


FUNCTIONS = {
    "CodeSectionAnnotationStorage": {},
}

__all__ = [
    "CodeSectionAnnotationStorage",
    "FUNCTIONS",
]
