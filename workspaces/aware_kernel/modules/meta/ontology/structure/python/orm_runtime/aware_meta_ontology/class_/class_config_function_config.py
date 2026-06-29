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
from aware_meta_ontology.function.function_config_enums import FunctionKind

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.function.function_config import FunctionConfig


class ClassConfigFunctionConfig(ORMModel):
    # Relationships
    function_config: FunctionConfig

    # Attributes
    is_public: bool = Field(default=True)
    is_constructor: bool = Field(default=False)
    position: int = Field(default=0)

    # Foreign Keys
    class_config_id: UUID = Field(description="Foreign key for ClassConfig.class_config_function_configs")
    function_config_id: UUID | None = Field(
        default=None, description="Foreign key for ClassConfigFunctionConfig.function_config"
    )

    async def update_config(self, is_public: bool = True, is_constructor: bool = False, position: int = 0) -> None:
        """
        Update mutable class-function membership metadata.

        Contract:
        - `class_config_id` and `function_config_id` are identity keys and are not mutable here.
        - Function scalar metadata lives on FunctionConfig.update_config.
        - This full-payload update treats booleans and position as current semantic truth.
        """

        payload = {"is_public": is_public, "is_constructor": is_constructor, "position": position}
        await invoke_instance(orm_model=self, function_name="update_config", payload=payload)
        return None

    @classmethod
    async def create_via_class_config(
        cls,
        class_config_id: UUID,
        owner_key: str,
        name: str,
        description: str | None = None,
        verb: str | None = None,
        is_async: bool = False,
        kind: FunctionKind = FunctionKind.instance,
        is_public: bool = True,
        is_constructor: bool = False,
        position: int = 0,
    ) -> ClassConfigFunctionConfig:
        """
        Create deterministic ClassConfigFunctionConfig link.

        Contract:
        - Parent `ClassConfig` scope is propagated by traversal lowering.
        - FunctionConfig is ensured via semantic standalone keys (`owner_key`, `name`, `kind`).
        - Deterministic edge identity derives from parent scope + `function_config_id`.
        """

        payload = {
            "class_config_id": class_config_id,
            "owner_key": owner_key,
            "name": name,
            "description": description,
            "verb": verb,
            "is_async": is_async,
            "kind": kind,
            "is_public": is_public,
            "is_constructor": is_constructor,
            "position": position,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_class_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ClassConfigFunctionConfig):
            return value
        return ClassConfigFunctionConfig.validate_invocation_value(value)


class ClassConfigFunctionConfigUpdateConfigInput(BaseModel):
    is_public: bool = Field(default=True)
    is_constructor: bool = Field(default=False)
    position: int = Field(default=0)


class ClassConfigFunctionConfigUpdateConfigOutput(BaseModel):
    pass


class ClassConfigFunctionConfigCreateViaClassConfigInput(BaseModel):
    class_config_id: UUID = Field(description="Foreign key for ClassConfig.class_config_function_configs")
    owner_key: str
    name: str
    description: str | None = Field(default=None)
    verb: str | None = Field(default=None)
    is_async: bool = Field(default=False)
    kind: FunctionKind = Field(default=FunctionKind.instance)
    is_public: bool = Field(default=True)
    is_constructor: bool = Field(default=False)
    position: int = Field(default=0)


class ClassConfigFunctionConfigCreateViaClassConfigOutput(BaseModel):
    value: ClassConfigFunctionConfig


FUNCTIONS = {
    "ClassConfigFunctionConfig": {
        "update_config": {
            "canonical": {
                "name": "update_config",
                "description": "Update mutable class-function membership metadata.\n\nContract:\n- `class_config_id` and `function_config_id` are identity keys and are not mutable here.\n- Function scalar metadata lives on FunctionConfig.update_config.\n- This full-payload update treats booleans and position as current semantic truth.",
                "is_constructor": False,
            },
            "input": ClassConfigFunctionConfigUpdateConfigInput,
            "output": ClassConfigFunctionConfigUpdateConfigOutput,
        },
        "create_via_class_config": {
            "canonical": {
                "name": "create_via_class_config",
                "description": "Create deterministic ClassConfigFunctionConfig link.\n\nContract:\n- Parent `ClassConfig` scope is propagated by traversal lowering.\n- FunctionConfig is ensured via semantic standalone keys (`owner_key`, `name`, `kind`).\n- Deterministic edge identity derives from parent scope + `function_config_id`.",
                "is_constructor": True,
            },
            "input": ClassConfigFunctionConfigCreateViaClassConfigInput,
            "output": ClassConfigFunctionConfigCreateViaClassConfigOutput,
        },
    },
}

__all__ = [
    "ClassConfigFunctionConfig",
    "ClassConfigFunctionConfigUpdateConfigInput",
    "ClassConfigFunctionConfigUpdateConfigOutput",
    "ClassConfigFunctionConfigCreateViaClassConfigInput",
    "ClassConfigFunctionConfigCreateViaClassConfigOutput",
    "FUNCTIONS",
]
