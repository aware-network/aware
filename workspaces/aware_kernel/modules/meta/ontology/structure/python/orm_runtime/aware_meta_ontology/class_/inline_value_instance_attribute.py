from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.attribute.attribute import Attribute


class InlineValueInstanceAttribute(ORMModel):
    # Relationships
    attribute: Attribute = Field(description="Association target reference to Attribute")

    # Foreign Keys
    attribute_id: UUID | None = Field(default=None, description="Join FK to Attribute")
    inline_value_instance_id: UUID = Field(description="Join FK to InlineValueInstance")

    @classmethod
    async def create_via_inline_value_instance(
        cls,
        inline_value_instance_id: UUID,
        owner_key: UUID,
        attribute_config_id: UUID,
        value_root_id: UUID | None = None,
    ) -> InlineValueInstanceAttribute:
        """
        Create one deterministic Attribute membership edge under an InlineValueInstance.

        Contract:
        - Parent `InlineValueInstance` scope is propagated by traversal lowering.
        - Edge identity derives from propagated inline-value-instance scope + constructed Attribute
        identity.
        - The edge owns topology only and must lower through `Attribute.create(...)` for target identity.
        """

        payload = {
            "inline_value_instance_id": inline_value_instance_id,
            "owner_key": owner_key,
            "attribute_config_id": attribute_config_id,
            "value_root_id": value_root_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_inline_value_instance", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, InlineValueInstanceAttribute):
            return value
        return InlineValueInstanceAttribute.validate_invocation_value(value)


class InlineValueInstanceAttributeCreateViaInlineValueInstanceInput(BaseModel):
    inline_value_instance_id: UUID = Field(description="Join FK to InlineValueInstance")
    owner_key: UUID
    attribute_config_id: UUID
    value_root_id: UUID | None = Field(default=None)


class InlineValueInstanceAttributeCreateViaInlineValueInstanceOutput(BaseModel):
    value: InlineValueInstanceAttribute


FUNCTIONS = {
    "InlineValueInstanceAttribute": {
        "create_via_inline_value_instance": {
            "canonical": {
                "name": "create_via_inline_value_instance",
                "description": "Create one deterministic Attribute membership edge under an InlineValueInstance.\n\nContract:\n- Parent `InlineValueInstance` scope is propagated by traversal lowering.\n- Edge identity derives from propagated inline-value-instance scope + constructed Attribute identity.\n- The edge owns topology only and must lower through `Attribute.create(...)` for target identity.",
                "is_constructor": True,
            },
            "input": InlineValueInstanceAttributeCreateViaInlineValueInstanceInput,
            "output": InlineValueInstanceAttributeCreateViaInlineValueInstanceOutput,
        },
    },
}

__all__ = [
    "InlineValueInstanceAttribute",
    "InlineValueInstanceAttributeCreateViaInlineValueInstanceInput",
    "InlineValueInstanceAttributeCreateViaInlineValueInstanceOutput",
    "FUNCTIONS",
]
