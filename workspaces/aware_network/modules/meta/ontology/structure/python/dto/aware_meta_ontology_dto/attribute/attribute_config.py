from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.attribute.code_section_attribute import CodeSectionAttribute
    from aware_meta_ontology_dto.attribute.attribute_type_descriptor import AttributeTypeDescriptor


class AttributeConfig(BaseModel):
    # Relationships
    type_descriptor: AttributeTypeDescriptor
    code_section_attribute: CodeSectionAttribute | None = Field(default=None)

    # Attributes
    owner_key: str
    name: str
    description: str | None = Field(default=None)
    default_value: str | None = Field(default=None)
    is_primary: bool = Field(default=False)
    is_public: bool = Field(default=True)
    is_required: bool = Field(default=False)
    is_unique: bool = Field(default=False)
    is_virtual: bool = Field(default=False)
    exclude_serialization: bool = Field(
        default=False,
        description="When true, this attribute is excluded from the canonical representation's serialization\n(Pydantic `Field(..., exclude=True)` in Python).\nContract (current):\n- This flag is set by transformers when applying canonical loading semantics to relationship pointers.\n- Renderers must be emit-only: they read this flag and do not re-derive it from loading strategy.\n- Round-trippability is mandatory: load semantics == serialization semantics for the canonical model.",
    )
