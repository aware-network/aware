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
    from aware_meta_ontology.attribute.attribute_change import AttributeChange
    from aware_meta_ontology.attribute.attribute_config import AttributeConfig
    from aware_meta_ontology.attribute.attribute_value import AttributeValue


class Attribute(ORMModel):
    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None, exclude=True)
    attribute_changes: list[AttributeChange] = Field(default_factory=list, exclude=True)
    value_root: AttributeValue = Field(description="Canonical value representation (descriptor-driven value tree).")

    # Attributes
    owner_key: UUID = Field(description="Stable owner anchor for shared contained structural Attribute identity.")

    # Foreign Keys
    attribute_config_id: UUID = Field(description="Foreign key for Attribute.attribute_config")
    value_root_id: UUID | None = Field(default=None, description="Foreign key for Attribute.value_root")

    @classmethod
    async def create(cls, owner_key: UUID, attribute_config_id: UUID, value_root_id: UUID | None = None) -> Attribute:
        """
        Create deterministic Attribute identity from caller-owned `owner_key` + `attribute_config_id`.

        Contract:
        - `owner_key` is the owner-scoped semantic anchor for shared structural Attribute identity.
        - Parent containment / edge routing must not enter the Attribute stable-id formula.
        - Direct owner foreign keys remain topology truth only.
        """

        payload = {"owner_key": owner_key, "attribute_config_id": attribute_config_id, "value_root_id": value_root_id}
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Attribute):
            return value
        return Attribute.validate_invocation_value(value)


class AttributeCreateInput(BaseModel):
    owner_key: UUID
    attribute_config_id: UUID
    value_root_id: UUID | None = Field(default=None)


class AttributeCreateOutput(BaseModel):
    value: Attribute


FUNCTIONS = {
    "Attribute": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Create deterministic Attribute identity from caller-owned `owner_key` + `attribute_config_id`.\n\nContract:\n- `owner_key` is the owner-scoped semantic anchor for shared structural Attribute identity.\n- Parent containment / edge routing must not enter the Attribute stable-id formula.\n- Direct owner foreign keys remain topology truth only.",
                "is_constructor": True,
            },
            "input": AttributeCreateInput,
            "output": AttributeCreateOutput,
        },
    },
}

__all__ = [
    "Attribute",
    "AttributeCreateInput",
    "AttributeCreateOutput",
    "FUNCTIONS",
]
