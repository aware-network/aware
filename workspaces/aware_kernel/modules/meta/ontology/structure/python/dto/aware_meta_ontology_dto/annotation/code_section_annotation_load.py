from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.class_.class_config_relationship_enums import ClassConfigRelationshipSideLoadingStrategy

if TYPE_CHECKING:
    from aware_code_ontology_dto.annotation.code_section_annotation import CodeSectionAnnotation


class CodeSectionAnnotationLoad(BaseModel):
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
    code_section_annotation: CodeSectionAnnotation | None = Field(default=None)

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
