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
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.attribute.attribute_config import AttributeConfig


class ClassConfigRelationshipAttribute(ORMModel):
    """
    Relationship attribute representation.
    This models how a `ClassConfigRelationship` is represented via one or more
    `AttributeConfig`s (e.g. REFERENCE attribute, FOREIGN_KEY attribute, AUXILIARY).
    NOTE: OCG is general-purpose. Canonical constraints (e.g. emitting exactly one
    REFERENCE+FORWARD attribute) are enforced by builders/transformers, not the schema.
    """

    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None, exclude=True)

    # Attributes
    direction: ClassConfigRelationshipDirection
    role: ClassConfigRelationshipAttributeRole

    # Foreign Keys
    class_config_relationship_id: UUID = Field(
        description="Foreign key for ClassConfigRelationship.class_config_relationship_attributes"
    )
    attribute_config_id: UUID = Field(description="Foreign key for ClassConfigRelationshipAttribute.attribute_config")

    @classmethod
    async def create_via_class_config_relationship(
        cls,
        class_config_relationship_id: UUID,
        attribute_config_id: UUID,
        direction: ClassConfigRelationshipDirection,
        role: ClassConfigRelationshipAttributeRole,
    ) -> ClassConfigRelationshipAttribute:
        """
        Create deterministic ClassConfigRelationshipAttribute under a parent relationship scope.

        Contract:
        - Parent `ClassConfigRelationship` scope is propagated by traversal lowering.
        - Stable identity derives from parent scope + `(attribute_config_id, direction, role)`.
        """

        payload = {
            "class_config_relationship_id": class_config_relationship_id,
            "attribute_config_id": attribute_config_id,
            "direction": direction,
            "role": role,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_class_config_relationship", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ClassConfigRelationshipAttribute):
            return value
        return ClassConfigRelationshipAttribute.validate_invocation_value(value)


class ClassConfigRelationshipAttributeCreateViaClassConfigRelationshipInput(BaseModel):
    class_config_relationship_id: UUID = Field(
        description="Foreign key for ClassConfigRelationship.class_config_relationship_attributes"
    )
    attribute_config_id: UUID
    direction: ClassConfigRelationshipDirection
    role: ClassConfigRelationshipAttributeRole


class ClassConfigRelationshipAttributeCreateViaClassConfigRelationshipOutput(BaseModel):
    value: ClassConfigRelationshipAttribute


FUNCTIONS = {
    "ClassConfigRelationshipAttribute": {
        "create_via_class_config_relationship": {
            "canonical": {
                "name": "create_via_class_config_relationship",
                "description": "Create deterministic ClassConfigRelationshipAttribute under a parent relationship scope.\n\nContract:\n- Parent `ClassConfigRelationship` scope is propagated by traversal lowering.\n- Stable identity derives from parent scope + `(attribute_config_id, direction, role)`.",
                "is_constructor": True,
            },
            "input": ClassConfigRelationshipAttributeCreateViaClassConfigRelationshipInput,
            "output": ClassConfigRelationshipAttributeCreateViaClassConfigRelationshipOutput,
        },
    },
}

__all__ = [
    "ClassConfigRelationshipAttribute",
    "ClassConfigRelationshipAttributeCreateViaClassConfigRelationshipInput",
    "ClassConfigRelationshipAttributeCreateViaClassConfigRelationshipOutput",
    "FUNCTIONS",
]
