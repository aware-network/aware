from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.annotation.code_section_annotation_storage_enums import (
    CodeSectionAnnotationStorageOperation,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.annotation.code_section_annotation import CodeSectionAnnotation


class CodeSectionAnnotationStorage(BaseModel):
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
    code_section_annotation: CodeSectionAnnotation | None = Field(default=None)

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
