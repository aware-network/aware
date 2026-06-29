from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.annotation.code_section_annotation_reference_enums import (
    CodeSectionAnnotationReferenceMode,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.annotation.code_section_annotation import CodeSectionAnnotation


class CodeSectionAnnotationReference(BaseModel):
    """
    Ontology-level view of a `reference` ANN.
    This supports deterministic "port + bind" references across ObjectConfigGraphs,
    allowing ontology cycles without requiring package-manager dependency cycles.
    Canonical forms (path + args):
    - Port: ann <TypeRef>::<attribute> reference port
    - Bind: ann <TypeRef>::<relationship_attribute> reference bind <TargetTypeRef>::<target_attribute>
    Invariants:
    - `port` declares that an attribute is a canonical reference target (no guessing).
    - `bind` declares that a relationship must reuse an existing FK attribute (no synthetic FK).
    """

    # Relationships
    code_section_annotation: CodeSectionAnnotation | None = Field(default=None)

    # Attributes
    fqn_prefix: str = Field(description="Location within the canonical graph (bind owner / port owner)")
    namespace: str
    class_name: str
    attribute_name: str
    mode: CodeSectionAnnotationReferenceMode = Field(description="Reference semantics")
    target_fqn_prefix: str | None = Field(default=None, description="Bind target (only when mode=BIND)")
    target_namespace: str | None = Field(default=None)
    target_class_name: str | None = Field(default=None)
    target_attribute_name: str | None = Field(default=None)
