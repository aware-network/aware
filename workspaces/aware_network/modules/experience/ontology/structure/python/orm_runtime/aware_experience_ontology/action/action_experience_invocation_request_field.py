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
    from aware_meta_ontology.attribute.attribute_config import AttributeConfig


class ActionExperienceInvocationRequestField(ORMModel):
    """
    Declared request-field composition for one action invocation binding.
    Contract:
    - Parent scope is `ActionExperienceInvocation::request_fields`.
    - The target request field is relational: `attribute_config` points to the
    endpoint request ClassConfig attribute, not a string field name.
    - `source_ref` is the closed Experience dispatch-context vocabulary:
    `event.*`, `commit.*`, `intent.*`, `execution.*`, `api_call.key`,
    `binding.*`, `binding.node.<alias>.class_instance_identity_id`,
    `binding.node.<alias>.class_config_id`, `actor.id`, and
    `subscription.id`.
    - The composer is a pure projection of dispatch context into the endpoint
    request payload. It must not read graph state, call services, or evaluate
    arbitrary expressions.
    """

    # Relationships
    attribute_config: AttributeConfig

    # Attributes
    source_ref: str
    required: bool = Field(default=True)
    position: int | None = Field(default=None)

    # Foreign Keys
    action_experience_invocation_id: UUID = Field(
        description="Foreign key for ActionExperienceInvocation.request_fields"
    )
    attribute_config_id: UUID | None = Field(
        default=None, description="Foreign key for ActionExperienceInvocationRequestField.attribute_config"
    )

    @classmethod
    async def build_via_action_experience_invocation(
        cls,
        action_experience_invocation_id: UUID,
        attribute_config_id: UUID,
        source_ref: str,
        required: bool = True,
        position: int | None = None,
    ) -> ActionExperienceInvocationRequestField:
        """
        Create deterministic request-field composition under one action
        invocation binding.
        """

        payload = {
            "action_experience_invocation_id": action_experience_invocation_id,
            "attribute_config_id": attribute_config_id,
            "source_ref": source_ref,
            "required": required,
            "position": position,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_action_experience_invocation", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActionExperienceInvocationRequestField):
            return value
        return ActionExperienceInvocationRequestField.validate_invocation_value(value)


class ActionExperienceInvocationRequestFieldBuildViaActionExperienceInvocationInput(BaseModel):
    action_experience_invocation_id: UUID = Field(
        description="Foreign key for ActionExperienceInvocation.request_fields"
    )
    attribute_config_id: UUID
    source_ref: str
    required: bool = Field(default=True)
    position: int | None = Field(default=None)


class ActionExperienceInvocationRequestFieldBuildViaActionExperienceInvocationOutput(BaseModel):
    value: ActionExperienceInvocationRequestField


FUNCTIONS = {
    "ActionExperienceInvocationRequestField": {
        "build_via_action_experience_invocation": {
            "canonical": {
                "name": "build_via_action_experience_invocation",
                "description": "Create deterministic request-field composition under one action\ninvocation binding.",
                "is_constructor": True,
            },
            "input": ActionExperienceInvocationRequestFieldBuildViaActionExperienceInvocationInput,
            "output": ActionExperienceInvocationRequestFieldBuildViaActionExperienceInvocationOutput,
        },
    },
}

__all__ = [
    "ActionExperienceInvocationRequestField",
    "ActionExperienceInvocationRequestFieldBuildViaActionExperienceInvocationInput",
    "ActionExperienceInvocationRequestFieldBuildViaActionExperienceInvocationOutput",
    "FUNCTIONS",
]
