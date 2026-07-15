from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.annotation.code_section_annotation_oneof_enums import CodeSectionAnnotationOneOfMode

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.annotation.code_section_annotation import CodeSectionAnnotation


class CodeSectionAnnotationOneOf(ORMModel):
    """
    Ontology-level view of a `oneof` ANN.
    This encodes explicit XOR ("exactly one") group semantics for a class, without
    relying on naming conventions.
    Canonical forms:
    - ann <TypeRef> oneof <attribute_name_1> <attribute_name_2> ...
    - ann <TypeRef> oneof identity <attribute_name_1> <attribute_name_2> ...
    - ann <TypeRef> oneof identity <member_attr_1> ... discriminator <disc_attr> <variant> <member_attr> ...
    Example:
    - ann comms.models.NetworkNodeOperation oneof request response
    """

    # Relationships
    code_section_annotation: CodeSectionAnnotation | None = Field(default=None, exclude=True)

    # Attributes
    fqn_prefix: str = Field(description="Location within the canonical graph")
    namespace: str
    class_name: str
    mode: CodeSectionAnnotationOneOfMode = Field(
        default=CodeSectionAnnotationOneOfMode.validation,
        description="Oneof semantic rail:\n- validation (default): payload XOR validation.\n- identity: stable-id polymorphic identity rail.",
    )
    attribute_names: list[str] = Field(
        default_factory=list, description="Attribute names that form the oneof group (XOR: exactly one must be set)."
    )
    discriminator_attribute_name: str | None = Field(
        default=None,
        description="Optional discriminator attribute for identity-mode oneof rails (for example `type`).\nWhen set, `discriminator_cases` must map discriminator variants to oneof members.",
    )
    discriminator_cases: list[str] = Field(
        default_factory=list,
        description="Discriminator mappings encoded as `<variant>=<member_attr>` in canonical metadata.\nAuthoring syntax uses token pairs `<variant> <member_attr>`.\nExample authoring: `... discriminator type enum enum_config class class_config`.",
    )

    # Foreign Keys
    code_section_annotation_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionAnnotationOneOf.code_section_annotation"
    )
