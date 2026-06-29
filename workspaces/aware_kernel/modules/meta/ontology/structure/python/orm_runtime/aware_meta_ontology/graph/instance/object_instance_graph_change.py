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
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import ObjectInstanceGraphChangeType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_history_ontology.change.change import Change
    from aware_meta_ontology.class_.class_instance_change import ClassInstanceChange
    from aware_meta_ontology.class_.class_instance_relationship_change import ClassInstanceRelationshipChange
    from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph


class ObjectInstanceGraphChange(ORMModel):
    # Relationships
    object_instance_graph: ObjectInstanceGraph | None = Field(
        default=None, exclude=True, description="Explicit payload worldline target for this change tree."
    )
    change: Change
    class_instance_changes: list[ClassInstanceChange] = Field(default_factory=list)
    class_instance_relationship_changes: list[ClassInstanceRelationshipChange] = Field(default_factory=list)

    # Attributes
    type: ObjectInstanceGraphChangeType

    # Foreign Keys
    object_instance_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphIdentity.object_instance_graph_changes"
    )
    object_instance_graph_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphChange.object_instance_graph"
    )
    change_id: UUID | None = Field(default=None, description="Foreign key for ObjectInstanceGraphChange.change")

    @classmethod
    async def create_via_object_instance_graph_identity(
        cls, object_instance_graph_identity_id: UUID, change_id: UUID, type: ObjectInstanceGraphChangeType
    ) -> ObjectInstanceGraphChange:
        """
        Create one deterministic ObjectInstanceGraphChange under this ObjectInstanceGraphIdentity.

        Contract:
        - Parent `object_instance_graph_identity_id` is propagated by traversal lowering.
        - The payload `object_instance_graph` is copied from the parent OIGI boundary pointer.
        - Deterministic identity resolves from `(object_instance_graph_identity_id via path, change_id)`.
        """

        payload = {
            "object_instance_graph_identity_id": object_instance_graph_identity_id,
            "change_id": change_id,
            "type": type,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_object_instance_graph_identity", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectInstanceGraphChange):
            return value
        return ObjectInstanceGraphChange.validate_invocation_value(value)


class ObjectInstanceGraphChangeCreateViaObjectInstanceGraphIdentityInput(BaseModel):
    object_instance_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphIdentity.object_instance_graph_changes"
    )
    change_id: UUID
    type: ObjectInstanceGraphChangeType


class ObjectInstanceGraphChangeCreateViaObjectInstanceGraphIdentityOutput(BaseModel):
    value: ObjectInstanceGraphChange


FUNCTIONS = {
    "ObjectInstanceGraphChange": {
        "create_via_object_instance_graph_identity": {
            "canonical": {
                "name": "create_via_object_instance_graph_identity",
                "description": "Create one deterministic ObjectInstanceGraphChange under this ObjectInstanceGraphIdentity.\n\nContract:\n- Parent `object_instance_graph_identity_id` is propagated by traversal lowering.\n- The payload `object_instance_graph` is copied from the parent OIGI boundary pointer.\n- Deterministic identity resolves from `(object_instance_graph_identity_id via path, change_id)`.",
                "is_constructor": True,
            },
            "input": ObjectInstanceGraphChangeCreateViaObjectInstanceGraphIdentityInput,
            "output": ObjectInstanceGraphChangeCreateViaObjectInstanceGraphIdentityOutput,
        },
    },
}

__all__ = [
    "ObjectInstanceGraphChange",
    "ObjectInstanceGraphChangeCreateViaObjectInstanceGraphIdentityInput",
    "ObjectInstanceGraphChangeCreateViaObjectInstanceGraphIdentityOutput",
    "FUNCTIONS",
]
