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
    from aware_experience_ontology.invocation.experience_invocation_action import ExperienceInvocationAction


class ActionExperienceInvocationAction(ORMModel):
    """
    ActionExperience-owned provenance bridge for one invocation action.
    Contract:
    - Parent `ActionExperienceInvocation` scope is provided only by
    `ActionExperienceInvocation::invocation_actions` traversal.
    - `ExperienceInvocationAction` is the actual generic invocation receipt.
    - This bridge records that the dispatch happened through one
    ActionExperience invocation binding without making the binding a receipt
    identity owner.
    """

    # Relationships
    experience_invocation_action: ExperienceInvocationAction | None = Field(default=None)

    # Foreign Keys
    action_experience_invocation_id: UUID = Field(
        description="Foreign key for ActionExperienceInvocation.invocation_actions"
    )
    experience_invocation_action_id: UUID = Field(
        description="Foreign key for ActionExperienceInvocationAction.experience_invocation_action"
    )

    @classmethod
    async def build_via_action_experience_invocation(
        cls,
        action_experience_invocation_id: UUID,
        experience_invocation_action_config_id: UUID,
        invocation_key: UUID,
        actor_id: UUID | None = None,
        api_call_id: UUID | None = None,
        sdk_operation_call_id: UUID | None = None,
        request_ref: str | None = None,
        receipt_ref: str | None = None,
        status: str = "pending",
    ) -> ActionExperienceInvocationAction:
        """
        Create one deterministic action-experience provenance bridge.

        Contract:
        - Parent `ActionExperienceInvocation` scope is propagated by traversal
          lowering from `ActionExperienceInvocation::invocation_actions`; the
          child must not declare a parent reference or parent-id input.
        - `ExperienceInvocationAction` is ensured by standalone semantic keys
          `(experience_invocation_action_config, invocation_key)`.
        """

        payload = {
            "action_experience_invocation_id": action_experience_invocation_id,
            "experience_invocation_action_config_id": experience_invocation_action_config_id,
            "invocation_key": invocation_key,
            "actor_id": actor_id,
            "api_call_id": api_call_id,
            "sdk_operation_call_id": sdk_operation_call_id,
            "request_ref": request_ref,
            "receipt_ref": receipt_ref,
            "status": status,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_action_experience_invocation", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActionExperienceInvocationAction):
            return value
        return ActionExperienceInvocationAction.validate_invocation_value(value)


class ActionExperienceInvocationActionBuildViaActionExperienceInvocationInput(BaseModel):
    action_experience_invocation_id: UUID = Field(
        description="Foreign key for ActionExperienceInvocation.invocation_actions"
    )
    experience_invocation_action_config_id: UUID
    invocation_key: UUID
    actor_id: UUID | None = Field(default=None)
    api_call_id: UUID | None = Field(default=None)
    sdk_operation_call_id: UUID | None = Field(default=None)
    request_ref: str | None = Field(default=None)
    receipt_ref: str | None = Field(default=None)
    status: str = Field(default="pending")


class ActionExperienceInvocationActionBuildViaActionExperienceInvocationOutput(BaseModel):
    value: ActionExperienceInvocationAction


FUNCTIONS = {
    "ActionExperienceInvocationAction": {
        "build_via_action_experience_invocation": {
            "canonical": {
                "name": "build_via_action_experience_invocation",
                "description": "Create one deterministic action-experience provenance bridge.\n\nContract:\n- Parent `ActionExperienceInvocation` scope is propagated by traversal\n  lowering from `ActionExperienceInvocation::invocation_actions`; the\n  child must not declare a parent reference or parent-id input.\n- `ExperienceInvocationAction` is ensured by standalone semantic keys\n  `(experience_invocation_action_config, invocation_key)`.",
                "is_constructor": True,
            },
            "input": ActionExperienceInvocationActionBuildViaActionExperienceInvocationInput,
            "output": ActionExperienceInvocationActionBuildViaActionExperienceInvocationOutput,
        },
    },
}

__all__ = [
    "ActionExperienceInvocationAction",
    "ActionExperienceInvocationActionBuildViaActionExperienceInvocationInput",
    "ActionExperienceInvocationActionBuildViaActionExperienceInvocationOutput",
    "FUNCTIONS",
]
