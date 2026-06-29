from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorRole

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor


class AttributeTypeDescriptorLink(ORMModel):
    # Relationships
    child: AttributeTypeDescriptor

    # Attributes
    role: AttributeTypeDescriptorRole
    position: int = Field(default=0)

    # Foreign Keys
    attribute_type_descriptor_id: UUID = Field(description="Foreign key for AttributeTypeDescriptor.child_links")
    child_id: UUID | None = Field(default=None, description="Foreign key for AttributeTypeDescriptorLink.child")

    @classmethod
    async def build_via_attribute_type_descriptor(
        cls, attribute_type_descriptor_id: UUID, child_id: UUID, role: AttributeTypeDescriptorRole, position: int = 0
    ) -> AttributeTypeDescriptorLink:
        """
        Create deterministic descriptor child link under one AttributeTypeDescriptor.

        Contract:
        - Parent `attribute_type_descriptor_id` is propagated by constructor lowering.
        - Identity resolves from `(attribute_type_descriptor_id via path, child_id, role, position)`.
        """

        payload = {
            "attribute_type_descriptor_id": attribute_type_descriptor_id,
            "child_id": child_id,
            "role": role,
            "position": position,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_attribute_type_descriptor", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AttributeTypeDescriptorLink):
            return value
        return AttributeTypeDescriptorLink.validate_invocation_value(value)


class AttributeTypeDescriptorLinkBuildViaAttributeTypeDescriptorInput(BaseModel):
    attribute_type_descriptor_id: UUID = Field(description="Foreign key for AttributeTypeDescriptor.child_links")
    child_id: UUID
    role: AttributeTypeDescriptorRole
    position: int = Field(default=0)


class AttributeTypeDescriptorLinkBuildViaAttributeTypeDescriptorOutput(BaseModel):
    value: AttributeTypeDescriptorLink


FUNCTIONS = {
    "AttributeTypeDescriptorLink": {
        "build_via_attribute_type_descriptor": {
            "canonical": {
                "name": "build_via_attribute_type_descriptor",
                "description": "Create deterministic descriptor child link under one AttributeTypeDescriptor.\n\nContract:\n- Parent `attribute_type_descriptor_id` is propagated by constructor lowering.\n- Identity resolves from `(attribute_type_descriptor_id via path, child_id, role, position)`.",
                "is_constructor": True,
            },
            "input": AttributeTypeDescriptorLinkBuildViaAttributeTypeDescriptorInput,
            "output": AttributeTypeDescriptorLinkBuildViaAttributeTypeDescriptorOutput,
        },
    },
}

__all__ = [
    "AttributeTypeDescriptorLink",
    "AttributeTypeDescriptorLinkBuildViaAttributeTypeDescriptorInput",
    "AttributeTypeDescriptorLinkBuildViaAttributeTypeDescriptorOutput",
    "FUNCTIONS",
]
