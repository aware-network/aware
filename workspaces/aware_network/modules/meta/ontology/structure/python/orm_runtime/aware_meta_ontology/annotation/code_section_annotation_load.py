from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology
from aware_meta_ontology.class_.class_config_relationship_enums import ClassConfigRelationshipSideLoadingStrategy

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology.annotation.code_section_annotation import CodeSectionAnnotation


class CodeSectionAnnotationLoad(ORMModel):
    """
    Ontology-level view of a `load` ANN.
    This sits on top of the generic CodeSectionAnnotation and captures
    the resolved, object-centric semantics used by loaders and renderers.
    It is intentionally grammar-agnostic: the compiler only knows about
    CodeSectionAnnotation entries where `verb == \"load\"`.
    Contract (current canonical representation):
    - `load` annotations are the SSOT for relationship pointer semantics on the canonical model.
    - Loading semantics == serialization semantics for the canonical model (round-trippable always).
    - Import strategy is a language concern and MUST NOT be derived from `load`.
    """

    # Relationships
    code_section_annotation: CodeSectionAnnotation | None = Field(default=None, exclude=True)

    # Attributes
    fqn_prefix: str = Field(description="Location within the canonical graph")
    namespace: str
    class_name: str
    attribute_name: str
    edge_name: str | None = Field(default=None)
    forward_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(
        default=None, description="Loading semantics derived from ANN arguments"
    )
    reverse_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)

    # Foreign Keys
    code_section_annotation_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionAnnotationLoad.code_section_annotation"
    )


FUNCTIONS = {
    "CodeSectionAnnotationLoad": {},
}

__all__ = [
    "CodeSectionAnnotationLoad",
    "FUNCTIONS",
]
