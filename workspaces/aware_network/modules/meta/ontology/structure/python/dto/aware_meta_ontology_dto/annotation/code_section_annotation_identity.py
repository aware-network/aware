from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.class_.class_config_enums import ClassIdentityMode

if TYPE_CHECKING:
    from aware_code_ontology_dto.annotation.code_section_annotation import CodeSectionAnnotation


class CodeSectionAnnotationIdentity(BaseModel):
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
    code_section_annotation: CodeSectionAnnotation | None = Field(default=None)

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
