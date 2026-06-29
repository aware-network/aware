from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)


class EnumOption(ORMModel):
    # Attributes
    value: str
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int = Field(default=0)

    # Foreign Keys
    enum_config_id: UUID = Field(description="Foreign key for EnumConfig.enum_options")

    async def update_config(self, label: str | None = None, description: str | None = None, position: int = 0) -> None:
        """
        Update mutable EnumOption metadata.

        Contract:
        - `value` is identity and is not mutable here.
        - Moving an option to another EnumConfig is replacement semantics.
        - This full-payload update treats nullable arguments as current
          semantic truth.
        """

        payload = {"label": label, "description": description, "position": position}
        await invoke_instance(orm_model=self, function_name="update_config", payload=payload)
        return None

    @classmethod
    async def create_via_enum_config(
        cls,
        enum_config_id: UUID,
        value: str,
        label: str | None = None,
        description: str | None = None,
        position: int = 0,
    ) -> EnumOption:
        """
        Create deterministic EnumOption under one EnumConfig.

        Contract:
        - Parent `EnumConfig` scope is propagated by traversal lowering.
        - Deterministic identity derives from parent scope + `(value)`.
        """

        payload = {
            "enum_config_id": enum_config_id,
            "value": value,
            "label": label,
            "description": description,
            "position": position,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_enum_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnumOption):
            return value
        return EnumOption.validate_invocation_value(value)


class EnumOptionUpdateConfigInput(BaseModel):
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int = Field(default=0)


class EnumOptionUpdateConfigOutput(BaseModel):
    pass


class EnumOptionCreateViaEnumConfigInput(BaseModel):
    enum_config_id: UUID = Field(description="Foreign key for EnumConfig.enum_options")
    value: str
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int = Field(default=0)


class EnumOptionCreateViaEnumConfigOutput(BaseModel):
    value: EnumOption


FUNCTIONS = {
    "EnumOption": {
        "update_config": {
            "canonical": {
                "name": "update_config",
                "description": "Update mutable EnumOption metadata.\n\nContract:\n- `value` is identity and is not mutable here.\n- Moving an option to another EnumConfig is replacement semantics.\n- This full-payload update treats nullable arguments as current\n  semantic truth.",
                "is_constructor": False,
            },
            "input": EnumOptionUpdateConfigInput,
            "output": EnumOptionUpdateConfigOutput,
        },
        "create_via_enum_config": {
            "canonical": {
                "name": "create_via_enum_config",
                "description": "Create deterministic EnumOption under one EnumConfig.\n\nContract:\n- Parent `EnumConfig` scope is propagated by traversal lowering.\n- Deterministic identity derives from parent scope + `(value)`.",
                "is_constructor": True,
            },
            "input": EnumOptionCreateViaEnumConfigInput,
            "output": EnumOptionCreateViaEnumConfigOutput,
        },
    },
}

__all__ = [
    "EnumOption",
    "EnumOptionUpdateConfigInput",
    "EnumOptionUpdateConfigOutput",
    "EnumOptionCreateViaEnumConfigInput",
    "EnumOptionCreateViaEnumConfigOutput",
    "FUNCTIONS",
]
