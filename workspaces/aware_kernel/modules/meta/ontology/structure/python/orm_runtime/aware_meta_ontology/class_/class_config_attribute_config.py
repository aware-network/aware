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
    from aware_meta_ontology.attribute.attribute_config import AttributeConfig


class ClassConfigAttributeConfig(ORMModel):
    # Relationships
    attribute_config: AttributeConfig

    # Attributes
    position: int = Field(default=0)
    is_identity_key: bool = Field(default=False)

    # Foreign Keys
    class_config_id: UUID = Field(description="Foreign key for ClassConfig.class_config_attribute_configs")
    attribute_config_id: UUID | None = Field(
        default=None, description="Foreign key for ClassConfigAttributeConfig.attribute_config"
    )

    async def update_config(self, position: int = 0, is_identity_key: bool = False) -> None:
        """
        Update mutable class-attribute membership metadata.

        Contract:
        - `class_config_id` and `attribute_config_id` are identity keys and are not mutable here.
        - Attribute scalar/type descriptor metadata lives on AttributeConfig.update_*.
        - This full-payload update treats position and identity-key membership metadata as current semantic
        truth.
        """

        payload = {"position": position, "is_identity_key": is_identity_key}
        await invoke_instance(orm_model=self, function_name="update_config", payload=payload)
        return None

    @classmethod
    async def create_class_via_class_config(
        cls,
        class_config_id: UUID,
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
        position: int = 0,
        is_identity_key: bool = False,
    ) -> ClassConfigAttributeConfig:
        """Create deterministic ClassConfigAttributeConfig link for a class attribute."""

        payload = {
            "class_config_id": class_config_id,
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
            "position": position,
            "is_identity_key": is_identity_key,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_class_via_class_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ClassConfigAttributeConfig):
            return value
        return ClassConfigAttributeConfig.validate_invocation_value(value)

    @classmethod
    async def create_enum_via_class_config(
        cls,
        class_config_id: UUID,
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
        position: int = 0,
        is_identity_key: bool = False,
    ) -> ClassConfigAttributeConfig:
        """Create deterministic ClassConfigAttributeConfig link for an enum attribute."""

        payload = {
            "class_config_id": class_config_id,
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
            "position": position,
            "is_identity_key": is_identity_key,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_enum_via_class_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ClassConfigAttributeConfig):
            return value
        return ClassConfigAttributeConfig.validate_invocation_value(value)

    @classmethod
    async def create_primitive_via_class_config(
        cls,
        class_config_id: UUID,
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
        position: int = 0,
        is_identity_key: bool = False,
    ) -> ClassConfigAttributeConfig:
        """
        Create deterministic ClassConfigAttributeConfig link.

        Contract:
        - Parent `ClassConfig` scope is propagated by traversal lowering.
        - AttributeConfig is ensured via semantic standalone keys derived from the parent class context.
        - Deterministic edge identity derives from parent scope + `attribute_config_id`.
        """

        payload = {
            "class_config_id": class_config_id,
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
            "position": position,
            "is_identity_key": is_identity_key,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_primitive_via_class_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ClassConfigAttributeConfig):
            return value
        return ClassConfigAttributeConfig.validate_invocation_value(value)


class ClassConfigAttributeConfigUpdateConfigInput(BaseModel):
    position: int = Field(default=0)
    is_identity_key: bool = Field(default=False)


class ClassConfigAttributeConfigUpdateConfigOutput(BaseModel):
    pass


class ClassConfigAttributeConfigCreateClassViaClassConfigInput(BaseModel):
    class_config_id: UUID = Field(description="Foreign key for ClassConfig.class_config_attribute_configs")
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
    position: int = Field(default=0)
    is_identity_key: bool = Field(default=False)


class ClassConfigAttributeConfigCreateClassViaClassConfigOutput(BaseModel):
    value: ClassConfigAttributeConfig


class ClassConfigAttributeConfigCreateEnumViaClassConfigInput(BaseModel):
    class_config_id: UUID = Field(description="Foreign key for ClassConfig.class_config_attribute_configs")
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
    position: int = Field(default=0)
    is_identity_key: bool = Field(default=False)


class ClassConfigAttributeConfigCreateEnumViaClassConfigOutput(BaseModel):
    value: ClassConfigAttributeConfig


class ClassConfigAttributeConfigCreatePrimitiveViaClassConfigInput(BaseModel):
    class_config_id: UUID = Field(description="Foreign key for ClassConfig.class_config_attribute_configs")
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
    position: int = Field(default=0)
    is_identity_key: bool = Field(default=False)


class ClassConfigAttributeConfigCreatePrimitiveViaClassConfigOutput(BaseModel):
    value: ClassConfigAttributeConfig


FUNCTIONS = {
    "ClassConfigAttributeConfig": {
        "update_config": {
            "canonical": {
                "name": "update_config",
                "description": "Update mutable class-attribute membership metadata.\n\nContract:\n- `class_config_id` and `attribute_config_id` are identity keys and are not mutable here.\n- Attribute scalar/type descriptor metadata lives on AttributeConfig.update_*.\n- This full-payload update treats position and identity-key membership metadata as current semantic truth.",
                "is_constructor": False,
            },
            "input": ClassConfigAttributeConfigUpdateConfigInput,
            "output": ClassConfigAttributeConfigUpdateConfigOutput,
        },
        "create_class_via_class_config": {
            "canonical": {
                "name": "create_class_via_class_config",
                "description": "Create deterministic ClassConfigAttributeConfig link for a class attribute.",
                "is_constructor": True,
            },
            "input": ClassConfigAttributeConfigCreateClassViaClassConfigInput,
            "output": ClassConfigAttributeConfigCreateClassViaClassConfigOutput,
        },
        "create_enum_via_class_config": {
            "canonical": {
                "name": "create_enum_via_class_config",
                "description": "Create deterministic ClassConfigAttributeConfig link for an enum attribute.",
                "is_constructor": True,
            },
            "input": ClassConfigAttributeConfigCreateEnumViaClassConfigInput,
            "output": ClassConfigAttributeConfigCreateEnumViaClassConfigOutput,
        },
        "create_primitive_via_class_config": {
            "canonical": {
                "name": "create_primitive_via_class_config",
                "description": "Create deterministic ClassConfigAttributeConfig link.\n\nContract:\n- Parent `ClassConfig` scope is propagated by traversal lowering.\n- AttributeConfig is ensured via semantic standalone keys derived from the parent class context.\n- Deterministic edge identity derives from parent scope + `attribute_config_id`.",
                "is_constructor": True,
            },
            "input": ClassConfigAttributeConfigCreatePrimitiveViaClassConfigInput,
            "output": ClassConfigAttributeConfigCreatePrimitiveViaClassConfigOutput,
        },
    },
}

__all__ = [
    "ClassConfigAttributeConfig",
    "ClassConfigAttributeConfigUpdateConfigInput",
    "ClassConfigAttributeConfigUpdateConfigOutput",
    "ClassConfigAttributeConfigCreateClassViaClassConfigInput",
    "ClassConfigAttributeConfigCreateClassViaClassConfigOutput",
    "ClassConfigAttributeConfigCreateEnumViaClassConfigInput",
    "ClassConfigAttributeConfigCreateEnumViaClassConfigOutput",
    "ClassConfigAttributeConfigCreatePrimitiveViaClassConfigInput",
    "ClassConfigAttributeConfigCreatePrimitiveViaClassConfigOutput",
    "FUNCTIONS",
]
