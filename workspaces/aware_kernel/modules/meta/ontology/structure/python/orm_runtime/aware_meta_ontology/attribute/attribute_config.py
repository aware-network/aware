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

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute
    from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor


class AttributeConfig(ORMModel):
    # Relationships
    type_descriptor: AttributeTypeDescriptor
    code_section_attribute: CodeSectionAttribute | None = Field(default=None, exclude=True)

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

    # Foreign Keys
    type_descriptor_id: UUID | None = Field(default=None, description="Foreign key for AttributeConfig.type_descriptor")
    code_section_attribute_id: UUID | None = Field(
        default=None, description="Foreign key for AttributeConfig.code_section_attribute"
    )

    @classmethod
    async def create_primitive(
        cls,
        owner_key: str,
        name: str,
        primitive_base_type: CodePrimitiveBaseType = CodePrimitiveBaseType.any,
        description: str | None = None,
        default_value: str | None = None,
        is_primary: bool = False,
        is_public: bool = True,
        is_required: bool = False,
        is_unique: bool = False,
        is_virtual: bool = False,
    ) -> AttributeConfig:
        """
        Create deterministic primitive AttributeConfig and materialize descriptor chain.

        Contract:
        - Primitive descriptors are materialized from canonical primitive type semantics.
        - Parent traversal may materialize this standalone primitive, but parent propagation
          must not enter the AttributeConfig stable-id formula.
        """

        payload = {
            "owner_key": owner_key,
            "name": name,
            "primitive_base_type": primitive_base_type,
            "description": description,
            "default_value": default_value,
            "is_primary": is_primary,
            "is_public": is_public,
            "is_required": is_required,
            "is_unique": is_unique,
            "is_virtual": is_virtual,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_primitive", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AttributeConfig):
            return value
        return AttributeConfig.validate_invocation_value(value)

    @classmethod
    async def create_enum(
        cls,
        owner_key: str,
        name: str,
        enum_config_id: UUID,
        description: str | None = None,
        default_value: str | None = None,
        is_primary: bool = False,
        is_public: bool = True,
        is_required: bool = False,
        is_unique: bool = False,
        is_virtual: bool = False,
    ) -> AttributeConfig:
        """Create deterministic enum AttributeConfig and materialize descriptor chain."""

        payload = {
            "owner_key": owner_key,
            "name": name,
            "enum_config_id": enum_config_id,
            "description": description,
            "default_value": default_value,
            "is_primary": is_primary,
            "is_public": is_public,
            "is_required": is_required,
            "is_unique": is_unique,
            "is_virtual": is_virtual,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_enum", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AttributeConfig):
            return value
        return AttributeConfig.validate_invocation_value(value)

    @classmethod
    async def create_class(
        cls,
        owner_key: str,
        name: str,
        type_class_config_id: UUID,
        description: str | None = None,
        default_value: str | None = None,
        is_primary: bool = False,
        is_public: bool = True,
        is_required: bool = False,
        is_unique: bool = False,
        is_virtual: bool = False,
    ) -> AttributeConfig:
        """Create deterministic class AttributeConfig and materialize descriptor chain."""

        payload = {
            "owner_key": owner_key,
            "name": name,
            "type_class_config_id": type_class_config_id,
            "description": description,
            "default_value": default_value,
            "is_primary": is_primary,
            "is_public": is_public,
            "is_required": is_required,
            "is_unique": is_unique,
            "is_virtual": is_virtual,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_class", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AttributeConfig):
            return value
        return AttributeConfig.validate_invocation_value(value)

    async def update_primitive(
        self,
        primitive_base_type: CodePrimitiveBaseType = CodePrimitiveBaseType.any,
        description: str | None = None,
        default_value: str | None = None,
        is_primary: bool = False,
        is_public: bool = True,
        is_required: bool = False,
        is_unique: bool = False,
        is_virtual: bool = False,
        exclude_serialization: bool = False,
    ) -> None:
        """
        Update the mutable scalar contract for an existing primitive AttributeConfig.

        Contract:
        - `owner_key` and `name` are identity keys and are not mutable here.
        - The descriptor is replaced through ontology runtime semantics, never by raw OIG patching.
        - Owner-edge fields such as position/function I/O type are updated on their edge objects.
        """

        payload = {
            "primitive_base_type": primitive_base_type,
            "description": description,
            "default_value": default_value,
            "is_primary": is_primary,
            "is_public": is_public,
            "is_required": is_required,
            "is_unique": is_unique,
            "is_virtual": is_virtual,
            "exclude_serialization": exclude_serialization,
        }
        await invoke_instance(orm_model=self, function_name="update_primitive", payload=payload)
        return None

    async def update_enum(
        self,
        enum_config_id: UUID,
        description: str | None = None,
        default_value: str | None = None,
        is_primary: bool = False,
        is_public: bool = True,
        is_required: bool = False,
        is_unique: bool = False,
        is_virtual: bool = False,
        exclude_serialization: bool = False,
    ) -> None:
        """
        Update the mutable scalar contract for an existing enum AttributeConfig.

        Contract:
        - `owner_key` and `name` are identity keys and are not mutable here.
        - The enum target must already exist as committed ontology truth.
        - Owner-edge fields such as position/function I/O type are updated on their edge objects.
        """

        payload = {
            "enum_config_id": enum_config_id,
            "description": description,
            "default_value": default_value,
            "is_primary": is_primary,
            "is_public": is_public,
            "is_required": is_required,
            "is_unique": is_unique,
            "is_virtual": is_virtual,
            "exclude_serialization": exclude_serialization,
        }
        await invoke_instance(orm_model=self, function_name="update_enum", payload=payload)
        return None

    async def update_class(
        self,
        type_class_config_id: UUID,
        description: str | None = None,
        default_value: str | None = None,
        is_primary: bool = False,
        is_public: bool = True,
        is_required: bool = False,
        is_unique: bool = False,
        is_virtual: bool = False,
        exclude_serialization: bool = False,
    ) -> None:
        """
        Update the mutable scalar contract for an existing class AttributeConfig.

        Contract:
        - `owner_key` and `name` are identity keys and are not mutable here.
        - The class target must already exist as committed ontology truth.
        - Owner-edge fields such as position/function I/O type are updated on their edge objects.
        """

        payload = {
            "type_class_config_id": type_class_config_id,
            "description": description,
            "default_value": default_value,
            "is_primary": is_primary,
            "is_public": is_public,
            "is_required": is_required,
            "is_unique": is_unique,
            "is_virtual": is_virtual,
            "exclude_serialization": exclude_serialization,
        }
        await invoke_instance(orm_model=self, function_name="update_class", payload=payload)
        return None


class AttributeConfigCreatePrimitiveInput(BaseModel):
    owner_key: str
    name: str
    primitive_base_type: CodePrimitiveBaseType = Field(default=CodePrimitiveBaseType.any)
    description: str | None = Field(default=None)
    default_value: str | None = Field(default=None)
    is_primary: bool = Field(default=False)
    is_public: bool = Field(default=True)
    is_required: bool = Field(default=False)
    is_unique: bool = Field(default=False)
    is_virtual: bool = Field(default=False)


class AttributeConfigCreatePrimitiveOutput(BaseModel):
    value: AttributeConfig


class AttributeConfigCreateEnumInput(BaseModel):
    owner_key: str
    name: str
    enum_config_id: UUID
    description: str | None = Field(default=None)
    default_value: str | None = Field(default=None)
    is_primary: bool = Field(default=False)
    is_public: bool = Field(default=True)
    is_required: bool = Field(default=False)
    is_unique: bool = Field(default=False)
    is_virtual: bool = Field(default=False)


class AttributeConfigCreateEnumOutput(BaseModel):
    value: AttributeConfig


class AttributeConfigCreateClassInput(BaseModel):
    owner_key: str
    name: str
    type_class_config_id: UUID
    description: str | None = Field(default=None)
    default_value: str | None = Field(default=None)
    is_primary: bool = Field(default=False)
    is_public: bool = Field(default=True)
    is_required: bool = Field(default=False)
    is_unique: bool = Field(default=False)
    is_virtual: bool = Field(default=False)


class AttributeConfigCreateClassOutput(BaseModel):
    value: AttributeConfig


class AttributeConfigUpdatePrimitiveInput(BaseModel):
    primitive_base_type: CodePrimitiveBaseType = Field(default=CodePrimitiveBaseType.any)
    description: str | None = Field(default=None)
    default_value: str | None = Field(default=None)
    is_primary: bool = Field(default=False)
    is_public: bool = Field(default=True)
    is_required: bool = Field(default=False)
    is_unique: bool = Field(default=False)
    is_virtual: bool = Field(default=False)
    exclude_serialization: bool = Field(default=False)


class AttributeConfigUpdatePrimitiveOutput(BaseModel):
    pass


class AttributeConfigUpdateEnumInput(BaseModel):
    enum_config_id: UUID
    description: str | None = Field(default=None)
    default_value: str | None = Field(default=None)
    is_primary: bool = Field(default=False)
    is_public: bool = Field(default=True)
    is_required: bool = Field(default=False)
    is_unique: bool = Field(default=False)
    is_virtual: bool = Field(default=False)
    exclude_serialization: bool = Field(default=False)


class AttributeConfigUpdateEnumOutput(BaseModel):
    pass


class AttributeConfigUpdateClassInput(BaseModel):
    type_class_config_id: UUID
    description: str | None = Field(default=None)
    default_value: str | None = Field(default=None)
    is_primary: bool = Field(default=False)
    is_public: bool = Field(default=True)
    is_required: bool = Field(default=False)
    is_unique: bool = Field(default=False)
    is_virtual: bool = Field(default=False)
    exclude_serialization: bool = Field(default=False)


class AttributeConfigUpdateClassOutput(BaseModel):
    pass


FUNCTIONS = {
    "AttributeConfig": {
        "create_primitive": {
            "canonical": {
                "name": "create_primitive",
                "description": "Create deterministic primitive AttributeConfig and materialize descriptor chain.\n\nContract:\n- Primitive descriptors are materialized from canonical primitive type semantics.\n- Parent traversal may materialize this standalone primitive, but parent propagation\n  must not enter the AttributeConfig stable-id formula.",
                "is_constructor": True,
            },
            "input": AttributeConfigCreatePrimitiveInput,
            "output": AttributeConfigCreatePrimitiveOutput,
        },
        "create_enum": {
            "canonical": {
                "name": "create_enum",
                "description": "Create deterministic enum AttributeConfig and materialize descriptor chain.",
                "is_constructor": True,
            },
            "input": AttributeConfigCreateEnumInput,
            "output": AttributeConfigCreateEnumOutput,
        },
        "create_class": {
            "canonical": {
                "name": "create_class",
                "description": "Create deterministic class AttributeConfig and materialize descriptor chain.",
                "is_constructor": True,
            },
            "input": AttributeConfigCreateClassInput,
            "output": AttributeConfigCreateClassOutput,
        },
        "update_primitive": {
            "canonical": {
                "name": "update_primitive",
                "description": "Update the mutable scalar contract for an existing primitive AttributeConfig.\n\nContract:\n- `owner_key` and `name` are identity keys and are not mutable here.\n- The descriptor is replaced through ontology runtime semantics, never by raw OIG patching.\n- Owner-edge fields such as position/function I/O type are updated on their edge objects.",
                "is_constructor": False,
            },
            "input": AttributeConfigUpdatePrimitiveInput,
            "output": AttributeConfigUpdatePrimitiveOutput,
        },
        "update_enum": {
            "canonical": {
                "name": "update_enum",
                "description": "Update the mutable scalar contract for an existing enum AttributeConfig.\n\nContract:\n- `owner_key` and `name` are identity keys and are not mutable here.\n- The enum target must already exist as committed ontology truth.\n- Owner-edge fields such as position/function I/O type are updated on their edge objects.",
                "is_constructor": False,
            },
            "input": AttributeConfigUpdateEnumInput,
            "output": AttributeConfigUpdateEnumOutput,
        },
        "update_class": {
            "canonical": {
                "name": "update_class",
                "description": "Update the mutable scalar contract for an existing class AttributeConfig.\n\nContract:\n- `owner_key` and `name` are identity keys and are not mutable here.\n- The class target must already exist as committed ontology truth.\n- Owner-edge fields such as position/function I/O type are updated on their edge objects.",
                "is_constructor": False,
            },
            "input": AttributeConfigUpdateClassInput,
            "output": AttributeConfigUpdateClassOutput,
        },
    },
}

__all__ = [
    "AttributeConfig",
    "AttributeConfigCreatePrimitiveInput",
    "AttributeConfigCreatePrimitiveOutput",
    "AttributeConfigCreateEnumInput",
    "AttributeConfigCreateEnumOutput",
    "AttributeConfigCreateClassInput",
    "AttributeConfigCreateClassOutput",
    "AttributeConfigUpdatePrimitiveInput",
    "AttributeConfigUpdatePrimitiveOutput",
    "AttributeConfigUpdateEnumInput",
    "AttributeConfigUpdateEnumOutput",
    "AttributeConfigUpdateClassInput",
    "AttributeConfigUpdateClassOutput",
    "FUNCTIONS",
]
