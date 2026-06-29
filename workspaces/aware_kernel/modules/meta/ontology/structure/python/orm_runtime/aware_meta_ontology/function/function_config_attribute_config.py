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
from aware_meta_ontology.function.function_config_enums import (
    FunctionAttributeType,
    FunctionIdentityKeyOrigin,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.attribute.attribute_config import AttributeConfig


class FunctionConfigAttributeConfig(ORMModel):
    # Relationships
    attribute_config: AttributeConfig

    # Attributes
    name: str
    position: int = Field(default=0)
    type: FunctionAttributeType
    is_identity_key: bool = Field(default=False)
    identity_key_origin: FunctionIdentityKeyOrigin = Field(default=FunctionIdentityKeyOrigin.standalone)

    # Foreign Keys
    function_config_id: UUID = Field(description="Foreign key for FunctionConfig.function_config_attribute_configs")
    attribute_config_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionConfigAttributeConfig.attribute_config"
    )

    async def update_config(
        self,
        position: int = 0,
        is_identity_key: bool = False,
        identity_key_origin: FunctionIdentityKeyOrigin = FunctionIdentityKeyOrigin.standalone,
    ) -> None:
        """
        Update mutable function-attribute membership metadata.

        Contract:
        - `function_config_id`, `attribute_config_id`, `name`, and `type` are identity keys and are not
        mutable here.
        - Attribute scalar/type descriptor metadata lives on AttributeConfig.update_*.
        - This full-payload update treats position and identity-key membership metadata as current semantic
        truth.
        """

        payload = {"position": position, "is_identity_key": is_identity_key, "identity_key_origin": identity_key_origin}
        await invoke_instance(orm_model=self, function_name="update_config", payload=payload)
        return None

    @classmethod
    async def create_class_via_function_config(
        cls,
        function_config_id: UUID,
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
        type: FunctionAttributeType = FunctionAttributeType.input,
        position: int = 0,
        is_identity_key: bool = False,
        identity_key_origin: FunctionIdentityKeyOrigin = FunctionIdentityKeyOrigin.standalone,
    ) -> FunctionConfigAttributeConfig:
        """Create deterministic FunctionConfigAttributeConfig association edge for a class attribute."""

        payload = {
            "function_config_id": function_config_id,
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
            "type": type,
            "position": position,
            "is_identity_key": is_identity_key,
            "identity_key_origin": identity_key_origin,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_class_via_function_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionConfigAttributeConfig):
            return value
        return FunctionConfigAttributeConfig.validate_invocation_value(value)

    @classmethod
    async def create_enum_via_function_config(
        cls,
        function_config_id: UUID,
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
        type: FunctionAttributeType = FunctionAttributeType.input,
        position: int = 0,
        is_identity_key: bool = False,
        identity_key_origin: FunctionIdentityKeyOrigin = FunctionIdentityKeyOrigin.standalone,
    ) -> FunctionConfigAttributeConfig:
        """Create deterministic FunctionConfigAttributeConfig association edge for an enum attribute."""

        payload = {
            "function_config_id": function_config_id,
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
            "type": type,
            "position": position,
            "is_identity_key": is_identity_key,
            "identity_key_origin": identity_key_origin,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_enum_via_function_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionConfigAttributeConfig):
            return value
        return FunctionConfigAttributeConfig.validate_invocation_value(value)

    @classmethod
    async def create_primitive_via_function_config(
        cls,
        function_config_id: UUID,
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
        type: FunctionAttributeType = FunctionAttributeType.input,
        position: int = 0,
        is_identity_key: bool = False,
        identity_key_origin: FunctionIdentityKeyOrigin = FunctionIdentityKeyOrigin.standalone,
    ) -> FunctionConfigAttributeConfig:
        """Create deterministic FunctionConfigAttributeConfig association edge."""

        payload = {
            "function_config_id": function_config_id,
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
            "type": type,
            "position": position,
            "is_identity_key": is_identity_key,
            "identity_key_origin": identity_key_origin,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_primitive_via_function_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionConfigAttributeConfig):
            return value
        return FunctionConfigAttributeConfig.validate_invocation_value(value)


class FunctionConfigAttributeConfigUpdateConfigInput(BaseModel):
    position: int = Field(default=0)
    is_identity_key: bool = Field(default=False)
    identity_key_origin: FunctionIdentityKeyOrigin = Field(default=FunctionIdentityKeyOrigin.standalone)


class FunctionConfigAttributeConfigUpdateConfigOutput(BaseModel):
    pass


class FunctionConfigAttributeConfigCreateClassViaFunctionConfigInput(BaseModel):
    function_config_id: UUID = Field(description="Foreign key for FunctionConfig.function_config_attribute_configs")
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
    type: FunctionAttributeType = Field(default=FunctionAttributeType.input)
    position: int = Field(default=0)
    is_identity_key: bool = Field(default=False)
    identity_key_origin: FunctionIdentityKeyOrigin = Field(default=FunctionIdentityKeyOrigin.standalone)


class FunctionConfigAttributeConfigCreateClassViaFunctionConfigOutput(BaseModel):
    value: FunctionConfigAttributeConfig


class FunctionConfigAttributeConfigCreateEnumViaFunctionConfigInput(BaseModel):
    function_config_id: UUID = Field(description="Foreign key for FunctionConfig.function_config_attribute_configs")
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
    type: FunctionAttributeType = Field(default=FunctionAttributeType.input)
    position: int = Field(default=0)
    is_identity_key: bool = Field(default=False)
    identity_key_origin: FunctionIdentityKeyOrigin = Field(default=FunctionIdentityKeyOrigin.standalone)


class FunctionConfigAttributeConfigCreateEnumViaFunctionConfigOutput(BaseModel):
    value: FunctionConfigAttributeConfig


class FunctionConfigAttributeConfigCreatePrimitiveViaFunctionConfigInput(BaseModel):
    function_config_id: UUID = Field(description="Foreign key for FunctionConfig.function_config_attribute_configs")
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
    type: FunctionAttributeType = Field(default=FunctionAttributeType.input)
    position: int = Field(default=0)
    is_identity_key: bool = Field(default=False)
    identity_key_origin: FunctionIdentityKeyOrigin = Field(default=FunctionIdentityKeyOrigin.standalone)


class FunctionConfigAttributeConfigCreatePrimitiveViaFunctionConfigOutput(BaseModel):
    value: FunctionConfigAttributeConfig


FUNCTIONS = {
    "FunctionConfigAttributeConfig": {
        "update_config": {
            "canonical": {
                "name": "update_config",
                "description": "Update mutable function-attribute membership metadata.\n\nContract:\n- `function_config_id`, `attribute_config_id`, `name`, and `type` are identity keys and are not mutable here.\n- Attribute scalar/type descriptor metadata lives on AttributeConfig.update_*.\n- This full-payload update treats position and identity-key membership metadata as current semantic truth.",
                "is_constructor": False,
            },
            "input": FunctionConfigAttributeConfigUpdateConfigInput,
            "output": FunctionConfigAttributeConfigUpdateConfigOutput,
        },
        "create_class_via_function_config": {
            "canonical": {
                "name": "create_class_via_function_config",
                "description": "Create deterministic FunctionConfigAttributeConfig association edge for a class attribute.",
                "is_constructor": True,
            },
            "input": FunctionConfigAttributeConfigCreateClassViaFunctionConfigInput,
            "output": FunctionConfigAttributeConfigCreateClassViaFunctionConfigOutput,
        },
        "create_enum_via_function_config": {
            "canonical": {
                "name": "create_enum_via_function_config",
                "description": "Create deterministic FunctionConfigAttributeConfig association edge for an enum attribute.",
                "is_constructor": True,
            },
            "input": FunctionConfigAttributeConfigCreateEnumViaFunctionConfigInput,
            "output": FunctionConfigAttributeConfigCreateEnumViaFunctionConfigOutput,
        },
        "create_primitive_via_function_config": {
            "canonical": {
                "name": "create_primitive_via_function_config",
                "description": "Create deterministic FunctionConfigAttributeConfig association edge.",
                "is_constructor": True,
            },
            "input": FunctionConfigAttributeConfigCreatePrimitiveViaFunctionConfigInput,
            "output": FunctionConfigAttributeConfigCreatePrimitiveViaFunctionConfigOutput,
        },
    },
}

__all__ = [
    "FunctionConfigAttributeConfig",
    "FunctionConfigAttributeConfigUpdateConfigInput",
    "FunctionConfigAttributeConfigUpdateConfigOutput",
    "FunctionConfigAttributeConfigCreateClassViaFunctionConfigInput",
    "FunctionConfigAttributeConfigCreateClassViaFunctionConfigOutput",
    "FunctionConfigAttributeConfigCreateEnumViaFunctionConfigInput",
    "FunctionConfigAttributeConfigCreateEnumViaFunctionConfigOutput",
    "FunctionConfigAttributeConfigCreatePrimitiveViaFunctionConfigInput",
    "FunctionConfigAttributeConfigCreatePrimitiveViaFunctionConfigOutput",
    "FUNCTIONS",
]
