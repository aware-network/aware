from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Meta Ontology
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
    AttributeTypeDescriptorRole,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.attribute.attribute_type_descriptor_link import AttributeTypeDescriptorLink
    from aware_meta_ontology.class_.class_config import ClassConfig
    from aware_meta_ontology.enum.enum_config import EnumConfig
    from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig


class AttributeTypeDescriptor(ORMModel):
    # Relationships
    class_config: ClassConfig | None = Field(default=None, exclude=True)
    enum_config: EnumConfig | None = Field(default=None)
    primitive_config: PrimitiveConfig | None = Field(default=None)
    child_links: list[AttributeTypeDescriptorLink] = Field(default_factory=list)

    # Attributes
    collection_kind: AttributeCollectionType = Field(default=AttributeCollectionType.single)
    kind: AttributeTypeDescriptorKind

    # Foreign Keys
    class_config_id: UUID | None = Field(
        default=None, description="Foreign key for AttributeTypeDescriptor.class_config"
    )
    enum_config_id: UUID | None = Field(default=None, description="Foreign key for AttributeTypeDescriptor.enum_config")
    primitive_config_id: UUID | None = Field(
        default=None, description="Foreign key for AttributeTypeDescriptor.primitive_config"
    )

    @classmethod
    async def create_primitive(cls, primitive_base_type: CodePrimitiveBaseType) -> AttributeTypeDescriptor:
        """Create deterministic primitive descriptor chain."""

        payload = {"primitive_base_type": primitive_base_type}
        result = await invoke_constructor(orm_class=cls, function_name="create_primitive", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AttributeTypeDescriptor):
            return value
        return AttributeTypeDescriptor.validate_invocation_value(value)

    @classmethod
    async def create_enum(cls, enum_config_id: UUID) -> AttributeTypeDescriptor:
        """Create deterministic enum descriptor from predeclared EnumConfig truth."""

        payload = {"enum_config_id": enum_config_id}
        result = await invoke_constructor(orm_class=cls, function_name="create_enum", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AttributeTypeDescriptor):
            return value
        return AttributeTypeDescriptor.validate_invocation_value(value)

    @classmethod
    async def create_class(cls, class_config_id: UUID) -> AttributeTypeDescriptor:
        """Create deterministic class descriptor from predeclared ClassConfig truth."""

        payload = {"class_config_id": class_config_id}
        result = await invoke_constructor(orm_class=cls, function_name="create_class", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AttributeTypeDescriptor):
            return value
        return AttributeTypeDescriptor.validate_invocation_value(value)

    async def create_child_link(
        self, child_id: UUID, role: AttributeTypeDescriptorRole, position: int = 0
    ) -> AttributeTypeDescriptorLink:
        """
        Create deterministic descriptor child link under this AttributeTypeDescriptor.

        Contract:
        - Parent `attribute_type_descriptor_id` is propagated by constructor lowering.
        - The child link stable id must resolve from
          `(attribute_type_descriptor_id via path, child_id, role, position)`.
        """

        payload = {"child_id": child_id, "role": role, "position": position}
        result = await invoke_instance(orm_model=self, function_name="create_child_link", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.attribute.attribute_type_descriptor_link import AttributeTypeDescriptorLink

        if isinstance(value, AttributeTypeDescriptorLink):
            return value
        return AttributeTypeDescriptorLink.validate_invocation_value(value)


class AttributeTypeDescriptorCreatePrimitiveInput(BaseModel):
    primitive_base_type: CodePrimitiveBaseType


class AttributeTypeDescriptorCreatePrimitiveOutput(BaseModel):
    value: AttributeTypeDescriptor


class AttributeTypeDescriptorCreateEnumInput(BaseModel):
    enum_config_id: UUID


class AttributeTypeDescriptorCreateEnumOutput(BaseModel):
    value: AttributeTypeDescriptor


class AttributeTypeDescriptorCreateClassInput(BaseModel):
    class_config_id: UUID


class AttributeTypeDescriptorCreateClassOutput(BaseModel):
    value: AttributeTypeDescriptor


class AttributeTypeDescriptorCreateChildLinkInput(BaseModel):
    child_id: UUID
    role: AttributeTypeDescriptorRole
    position: int = Field(default=0)


class AttributeTypeDescriptorCreateChildLinkOutput(BaseModel):
    value: AttributeTypeDescriptorLink


FUNCTIONS = {
    "AttributeTypeDescriptor": {
        "create_primitive": {
            "canonical": {
                "name": "create_primitive",
                "description": "Create deterministic primitive descriptor chain.",
                "is_constructor": True,
            },
            "input": AttributeTypeDescriptorCreatePrimitiveInput,
            "output": AttributeTypeDescriptorCreatePrimitiveOutput,
        },
        "create_enum": {
            "canonical": {
                "name": "create_enum",
                "description": "Create deterministic enum descriptor from predeclared EnumConfig truth.",
                "is_constructor": True,
            },
            "input": AttributeTypeDescriptorCreateEnumInput,
            "output": AttributeTypeDescriptorCreateEnumOutput,
        },
        "create_class": {
            "canonical": {
                "name": "create_class",
                "description": "Create deterministic class descriptor from predeclared ClassConfig truth.",
                "is_constructor": True,
            },
            "input": AttributeTypeDescriptorCreateClassInput,
            "output": AttributeTypeDescriptorCreateClassOutput,
        },
        "create_child_link": {
            "canonical": {
                "name": "create_child_link",
                "description": "Create deterministic descriptor child link under this AttributeTypeDescriptor.\n\nContract:\n- Parent `attribute_type_descriptor_id` is propagated by constructor lowering.\n- The child link stable id must resolve from\n  `(attribute_type_descriptor_id via path, child_id, role, position)`.",
                "is_constructor": False,
            },
            "input": AttributeTypeDescriptorCreateChildLinkInput,
            "output": AttributeTypeDescriptorCreateChildLinkOutput,
        },
    },
}

__all__ = [
    "AttributeTypeDescriptor",
    "AttributeTypeDescriptorCreatePrimitiveInput",
    "AttributeTypeDescriptorCreatePrimitiveOutput",
    "AttributeTypeDescriptorCreateEnumInput",
    "AttributeTypeDescriptorCreateEnumOutput",
    "AttributeTypeDescriptorCreateClassInput",
    "AttributeTypeDescriptorCreateClassOutput",
    "AttributeTypeDescriptorCreateChildLinkInput",
    "AttributeTypeDescriptorCreateChildLinkOutput",
    "FUNCTIONS",
]
