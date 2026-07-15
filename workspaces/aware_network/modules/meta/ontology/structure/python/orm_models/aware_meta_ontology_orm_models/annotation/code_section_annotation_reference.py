from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.annotation.code_section_annotation_reference_enums import (
    CodeSectionAnnotationReferenceMode,
)

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.annotation.code_section_annotation import CodeSectionAnnotation


class CodeSectionAnnotationReference(ORMModel):
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
    code_section_annotation: CodeSectionAnnotation | None = Field(default=None, exclude=True)

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

    # Foreign Keys
    code_section_annotation_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionAnnotationReference.code_section_annotation"
    )
