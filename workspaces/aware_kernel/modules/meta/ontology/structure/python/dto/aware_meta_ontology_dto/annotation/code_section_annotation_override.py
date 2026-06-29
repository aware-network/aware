from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.annotation.code_section_annotation_override_enums import (
    CodeSectionAnnotationOverrideTarget,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.annotation.code_section_annotation import CodeSectionAnnotation


class CodeSectionAnnotationOverride(BaseModel):
    """
    Ontology-level view of an `override` ANN.
    This sits on top of the generic CodeSectionAnnotation and captures
    deterministic overrides without requiring the grammar/user to reason about "sides".
    It is intentionally grammar-agnostic: the compiler only knows about
    CodeSectionAnnotation entries where `verb == "override"`.
    """

    # Relationships
    code_section_annotation: CodeSectionAnnotation | None = Field(default=None)

    # Attributes
    fqn_prefix: str = Field(description="Location within the canonical graph")
    namespace: str
    class_name: str
    attribute_name: str
    edge_name: str | None = Field(default=None)
    target: CodeSectionAnnotationOverrideTarget = Field(description="Override target (first arg), currently FK.")
    nullable: bool = Field(
        default=False,
        description="Override semantics (apply to the target that is materialized for this relationship).\nCanonical default is required FK truth from relationship semantics.\nFor required `one_to_many`, reverse-owned FK is required by default.\n`nullable = true` is the explicit opt-out (`ann ... override fk nullable`).\nLoad strategy (`load eager|lazy`) does not change this requiredness truth.",
    )
    name: str | None = Field(default=None)
