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


class ClassInstanceAttribute(ORMModel):
    # Relationships
    attribute: Attribute = Field(description="Association target reference to Attribute")

    # Foreign Keys
    attribute_id: UUID | None = Field(default=None, description="Join FK to Attribute")
    class_instance_id: UUID = Field(description="Join FK to ClassInstance")

    @classmethod
    async def create_via_class_instance(
        cls, class_instance_id: UUID, owner_key: UUID, attribute_config_id: UUID, value_root_id: UUID | None = None
    ) -> ClassInstanceAttribute:
        """
        Create one deterministic Attribute membership edge under a ClassInstance.

        Contract:
        - Parent `ClassInstance` scope is propagated by traversal lowering.
        - Edge identity derives from propagated class-instance scope + constructed Attribute identity.
        - The edge owns topology only and must lower through `Attribute.create(...)` for target identity.
        """

        payload = {
            "class_instance_id": class_instance_id,
            "owner_key": owner_key,
            "attribute_config_id": attribute_config_id,
            "value_root_id": value_root_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_class_instance", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ClassInstanceAttribute):
            return value
        return ClassInstanceAttribute.validate_invocation_value(value)


class ClassInstanceAttributeCreateViaClassInstanceInput(BaseModel):
    class_instance_id: UUID = Field(description="Join FK to ClassInstance")
    owner_key: UUID
    attribute_config_id: UUID
    value_root_id: UUID | None = Field(default=None)


class ClassInstanceAttributeCreateViaClassInstanceOutput(BaseModel):
    value: ClassInstanceAttribute


FUNCTIONS = {
    "ClassInstanceAttribute": {
        "create_via_class_instance": {
            "canonical": {
                "name": "create_via_class_instance",
                "description": "Create one deterministic Attribute membership edge under a ClassInstance.\n\nContract:\n- Parent `ClassInstance` scope is propagated by traversal lowering.\n- Edge identity derives from propagated class-instance scope + constructed Attribute identity.\n- The edge owns topology only and must lower through `Attribute.create(...)` for target identity.",
                "is_constructor": True,
            },
            "input": ClassInstanceAttributeCreateViaClassInstanceInput,
            "output": ClassInstanceAttributeCreateViaClassInstanceOutput,
        },
    },
}

__all__ = [
    "ClassInstanceAttribute",
    "ClassInstanceAttributeCreateViaClassInstanceInput",
    "ClassInstanceAttributeCreateViaClassInstanceOutput",
    "FUNCTIONS",
]
