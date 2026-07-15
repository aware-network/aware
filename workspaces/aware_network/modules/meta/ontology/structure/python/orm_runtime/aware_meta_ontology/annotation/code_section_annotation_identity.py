from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology
from aware_meta_ontology.class_.class_config_enums import ClassIdentityMode

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology.annotation.code_section_annotation import CodeSectionAnnotation


class CodeSectionAnnotationIdentity(ORMModel):
    """
    Ontology-level view of an `identity` ANN.
    This declares class-level stable-id scope semantics.
    Canonical forms:
    - ann <TypeRef> identity contained
    - ann <TypeRef> identity standalone
    - ann <TypeRef> identity contained structural <relation_name>
    - ann <TypeRef> identity standalone structural <relation_name>
    Contract:
    - `contained` (default) means parent-path propagation may participate in stable-id derivation.
    - `standalone` means the class remains constructible via parent paths, but parent traversal
    must not enter the class stable-id formula.
    - `structural_relation_name` declares a canonical relation whose ordered payload contributes a
    compiler-derived structural fingerprint to the stable-id formula.
    """

    # Relationships
    code_section_annotation: CodeSectionAnnotation | None = Field(default=None, exclude=True)

    # Attributes
    fqn_prefix: str = Field(description="Location within the canonical graph")
    namespace: str
    class_name: str
    mode: ClassIdentityMode = Field(
        default=ClassIdentityMode.contained, description="Class-level identity scope semantics"
    )
    structural_relation_name: str | None = Field(
        default=None, description="Optional structural relation rail that contributes a compiler-derived fingerprint."
    )

    # Foreign Keys
    code_section_annotation_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionAnnotationIdentity.code_section_annotation"
    )


FUNCTIONS = {
    "CodeSectionAnnotationIdentity": {},
}

__all__ = [
    "CodeSectionAnnotationIdentity",
    "FUNCTIONS",
]
