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

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_reactivity_ontology.condition.condition_config import ConditionConfig


class Condition(ORMModel):
    # Relationships
    config: ConditionConfig | None = Field(default=None, exclude=True)
    trigger_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None, exclude=True)

    # Attributes
    activation_id: UUID
    arguments: JsonObject = Field(default_factory=JsonObject)

    # Foreign Keys
    config_id: UUID = Field(description="Foreign key for Condition.config")
    trigger_object_instance_graph_commit_id: UUID = Field(
        description="Foreign key for Condition.trigger_object_instance_graph_commit"
    )

    @classmethod
    async def create(
        cls,
        config_id: UUID,
        activation_id: UUID,
        trigger_object_instance_graph_commit_id: UUID,
        arguments: JsonObject = {},
    ) -> Condition:
        """Create runtime condition evidence anchored to one activation."""

        payload = {
            "config_id": config_id,
            "activation_id": activation_id,
            "trigger_object_instance_graph_commit_id": trigger_object_instance_graph_commit_id,
            "arguments": arguments,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Condition):
            return value
        return Condition.validate_invocation_value(value)


class ConditionCreateInput(BaseModel):
    config_id: UUID
    activation_id: UUID
    trigger_object_instance_graph_commit_id: UUID
    arguments: JsonObject = Field(default_factory=JsonObject)


class ConditionCreateOutput(BaseModel):
    value: Condition


FUNCTIONS = {
    "Condition": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Create runtime condition evidence anchored to one activation.",
                "is_constructor": True,
            },
            "input": ConditionCreateInput,
            "output": ConditionCreateOutput,
        },
    },
}

__all__ = [
    "Condition",
    "ConditionCreateInput",
    "ConditionCreateOutput",
    "FUNCTIONS",
]
