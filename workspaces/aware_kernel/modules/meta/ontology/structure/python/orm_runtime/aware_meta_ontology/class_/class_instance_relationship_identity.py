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
    from aware_meta_ontology.class_.class_instance_relationship import ClassInstanceRelationship


class ClassInstanceRelationshipIdentity(ORMModel):
    """
    Stable identity rail for ClassInstanceRelationship truth.
    Contract:
    - One identity id maps to one logical class-instance relationship worldline.
    - Commits/receipts should reference this id for parent-chain attribution truth.
    """

    # Relationships
    class_instance_relationship: ClassInstanceRelationship | None = Field(default=None, exclude=True)

    # Attributes
    label: str | None = Field(default=None)

    # Foreign Keys
    object_instance_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphIdentity.class_instance_relationship_identities"
    )
    class_instance_relationship_id: UUID = Field(
        description="Foreign key for ClassInstanceRelationshipIdentity.class_instance_relationship"
    )

    @classmethod
    async def create_via_object_instance_graph_identity(
        cls, object_instance_graph_identity_id: UUID, class_instance_relationship_id: UUID, label: str | None = None
    ) -> ClassInstanceRelationshipIdentity:
        """Create a deterministic ClassInstanceRelationshipIdentity worldline row."""

        payload = {
            "object_instance_graph_identity_id": object_instance_graph_identity_id,
            "class_instance_relationship_id": class_instance_relationship_id,
            "label": label,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_object_instance_graph_identity", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ClassInstanceRelationshipIdentity):
            return value
        return ClassInstanceRelationshipIdentity.validate_invocation_value(value)


class ClassInstanceRelationshipIdentityCreateViaObjectInstanceGraphIdentityInput(BaseModel):
    object_instance_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphIdentity.class_instance_relationship_identities"
    )
    class_instance_relationship_id: UUID
    label: str | None = Field(default=None)


class ClassInstanceRelationshipIdentityCreateViaObjectInstanceGraphIdentityOutput(BaseModel):
    value: ClassInstanceRelationshipIdentity


FUNCTIONS = {
    "ClassInstanceRelationshipIdentity": {
        "create_via_object_instance_graph_identity": {
            "canonical": {
                "name": "create_via_object_instance_graph_identity",
                "description": "Create a deterministic ClassInstanceRelationshipIdentity worldline row.",
                "is_constructor": True,
            },
            "input": ClassInstanceRelationshipIdentityCreateViaObjectInstanceGraphIdentityInput,
            "output": ClassInstanceRelationshipIdentityCreateViaObjectInstanceGraphIdentityOutput,
        },
    },
}

__all__ = [
    "ClassInstanceRelationshipIdentity",
    "ClassInstanceRelationshipIdentityCreateViaObjectInstanceGraphIdentityInput",
    "ClassInstanceRelationshipIdentityCreateViaObjectInstanceGraphIdentityOutput",
    "FUNCTIONS",
]
