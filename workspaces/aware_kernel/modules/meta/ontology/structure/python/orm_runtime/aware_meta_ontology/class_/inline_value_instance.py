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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.attribute.attribute import Attribute
    from aware_meta_ontology.class_.class_config import ClassConfig
    from aware_meta_ontology.class_.inline_value_instance_attribute import InlineValueInstanceAttribute


class InlineValueInstance(ORMModel):
    # Relationships
    class_config: ClassConfig | None = Field(default=None, exclude=True)

    # Attributes
    owner_key: UUID = Field(
        description="Stable owner anchor for this value-world instance within one enclosing payload tree."
    )

    # Foreign Keys
    class_config_id: UUID = Field(description="Foreign key for InlineValueInstance.class_config")

    # Edges
    inline_value_instance_attributes: list[InlineValueInstanceAttribute] = Field(
        default_factory=list, description="Edge association helper for attributes"
    )

    @property
    def attributes(self) -> list[Attribute]:
        return [edge.attribute for edge in self.inline_value_instance_attributes if edge.attribute is not None]

    @classmethod
    async def build(cls, owner_key: UUID, class_config_id: UUID) -> InlineValueInstance:
        """
        Build deterministic InlineValueInstance from a caller-owned value anchor.

        Contract:
        - Identity resolves from `(owner_key, class_config_id)`.
        - `owner_key` is a semantic owner anchor, not an implicit parent-propagated FK.
        - InlineValueInstance is value-world truth only: no OIG scope, no source_object_id,
          no relationships, and no commit/change rails.
        """

        payload = {"owner_key": owner_key, "class_config_id": class_config_id}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, InlineValueInstance):
            return value
        return InlineValueInstance.validate_invocation_value(value)

    async def create_attribute(
        self, attribute_config_id: UUID, value_root_id: UUID | None = None
    ) -> InlineValueInstanceAttribute:
        """
        Create deterministic Attribute membership under this InlineValueInstance.

        Contract:
        - InlineValueInstance owns membership and topology only.
        - Attribute identity resolves from `(owner_key, attribute_config_id)` via shared owner key.
        - The returned edge is the honest containment rail for value-world Attribute membership.
        """

        payload = {"attribute_config_id": attribute_config_id, "value_root_id": value_root_id}
        result = await invoke_instance(orm_model=self, function_name="create_attribute", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.class_.inline_value_instance_attribute import InlineValueInstanceAttribute

        if isinstance(value, InlineValueInstanceAttribute):
            return value
        return InlineValueInstanceAttribute.validate_invocation_value(value)


class InlineValueInstanceBuildInput(BaseModel):
    owner_key: UUID
    class_config_id: UUID


class InlineValueInstanceBuildOutput(BaseModel):
    value: InlineValueInstance


class InlineValueInstanceCreateAttributeInput(BaseModel):
    attribute_config_id: UUID
    value_root_id: UUID | None = Field(default=None)


class InlineValueInstanceCreateAttributeOutput(BaseModel):
    value: InlineValueInstanceAttribute


FUNCTIONS = {
    "InlineValueInstance": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Build deterministic InlineValueInstance from a caller-owned value anchor.\n\nContract:\n- Identity resolves from `(owner_key, class_config_id)`.\n- `owner_key` is a semantic owner anchor, not an implicit parent-propagated FK.\n- InlineValueInstance is value-world truth only: no OIG scope, no source_object_id,\n  no relationships, and no commit/change rails.",
                "is_constructor": True,
            },
            "input": InlineValueInstanceBuildInput,
            "output": InlineValueInstanceBuildOutput,
        },
        "create_attribute": {
            "canonical": {
                "name": "create_attribute",
                "description": "Create deterministic Attribute membership under this InlineValueInstance.\n\nContract:\n- InlineValueInstance owns membership and topology only.\n- Attribute identity resolves from `(owner_key, attribute_config_id)` via shared owner key.\n- The returned edge is the honest containment rail for value-world Attribute membership.",
                "is_constructor": False,
            },
            "input": InlineValueInstanceCreateAttributeInput,
            "output": InlineValueInstanceCreateAttributeOutput,
        },
    },
}

__all__ = [
    "InlineValueInstance",
    "InlineValueInstanceBuildInput",
    "InlineValueInstanceBuildOutput",
    "InlineValueInstanceCreateAttributeInput",
    "InlineValueInstanceCreateAttributeOutput",
    "FUNCTIONS",
]
