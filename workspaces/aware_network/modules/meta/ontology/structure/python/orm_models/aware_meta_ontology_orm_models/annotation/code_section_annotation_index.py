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


class CodeSectionAnnotationIndex(ORMModel):
    """
    Ontology-level view of an `index` ANN.
    Purpose:
    - Declare compiler-owned SQL indexes as part of the canonical OCG.
    - Keep DB indexes aligned with commit-keyed migrations (`AWARE_DB_BOOT_POLICY=migrate`).
    Canonical surface (v0):
    - Single-column: `ann schema.Class::member index`
    - Composite:     `ann schema.Class index member1 member2 ...`
    Notes:
    - `member_names` are canonical class members (attributes / relationship pointers).
    - SQL lowering determines the physical columns:
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
    member_names: list[str] = Field(
        default_factory=list, description="Canonical member names forming the index key (order matters)."
    )

    # Foreign Keys
    code_section_annotation_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionAnnotationIndex.code_section_annotation"
    )
