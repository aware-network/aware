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
    from aware_meta_ontology.class_.class_instance import ClassInstance


class ClassInstanceIdentity(ORMModel):
    """
    Stable identity rail for ClassInstance truth.
    Contract:
    - One identity id maps to one logical class-instance worldline.
    - Commits/receipts should reference this id for attribution truth.
    """

    # Relationships
    class_instance: ClassInstance | None = Field(default=None, exclude=True)

    # Attributes
    label: str | None = Field(default=None)

    # Foreign Keys
    object_instance_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphIdentity.class_instance_identities"
    )
    class_instance_id: UUID = Field(description="Foreign key for ClassInstanceIdentity.class_instance")

    @classmethod
    async def create_via_object_instance_graph_identity(
        cls, object_instance_graph_identity_id: UUID, class_instance_id: UUID, label: str | None = None
    ) -> ClassInstanceIdentity:
        """Create a deterministic ClassInstanceIdentity worldline row."""

        payload = {
            "object_instance_graph_identity_id": object_instance_graph_identity_id,
            "class_instance_id": class_instance_id,
            "label": label,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_object_instance_graph_identity", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ClassInstanceIdentity):
            return value
        return ClassInstanceIdentity.validate_invocation_value(value)


class ClassInstanceIdentityCreateViaObjectInstanceGraphIdentityInput(BaseModel):
    object_instance_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphIdentity.class_instance_identities"
    )
    class_instance_id: UUID
    label: str | None = Field(default=None)


class ClassInstanceIdentityCreateViaObjectInstanceGraphIdentityOutput(BaseModel):
    value: ClassInstanceIdentity


FUNCTIONS = {
    "ClassInstanceIdentity": {
        "create_via_object_instance_graph_identity": {
            "canonical": {
                "name": "create_via_object_instance_graph_identity",
                "description": "Create a deterministic ClassInstanceIdentity worldline row.",
                "is_constructor": True,
            },
            "input": ClassInstanceIdentityCreateViaObjectInstanceGraphIdentityInput,
            "output": ClassInstanceIdentityCreateViaObjectInstanceGraphIdentityOutput,
        },
    },
}

__all__ = [
    "ClassInstanceIdentity",
    "ClassInstanceIdentityCreateViaObjectInstanceGraphIdentityInput",
    "ClassInstanceIdentityCreateViaObjectInstanceGraphIdentityOutput",
    "FUNCTIONS",
]
