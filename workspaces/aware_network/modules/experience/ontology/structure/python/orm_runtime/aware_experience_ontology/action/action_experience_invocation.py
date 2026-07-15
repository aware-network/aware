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
    from aware_experience_ontology.action.action_experience_invocation_action import ActionExperienceInvocationAction
    from aware_experience_ontology.action.action_experience_invocation_request_field import (
        ActionExperienceInvocationRequestField,
    )
    from aware_experience_ontology.invocation.experience_invocation_action import ExperienceInvocationAction
    from aware_experience_ontology.invocation.experience_invocation_action_config import (
        ExperienceInvocationActionConfig,
    )


class ActionExperienceInvocation(ORMModel):
    """
    ActionExperience-owned binding to a reusable invocation action config.
    Contract:
    - `ActionExperience` remains environment-scoped policy for Reactivity
    action vocabulary.
    - `ExperienceInvocationActionConfig` remains the shared API/SDK target and
    typed contract binding.
    - Many invocation configs may bind to one action experience; later dispatch
    lanes choose among them.
    """

    # Relationships
    experience_invocation_action_config: ExperienceInvocationActionConfig | None = Field(default=None)
    invocation_actions: list[ActionExperienceInvocationAction] = Field(default_factory=list)
    request_fields: list[ActionExperienceInvocationRequestField] = Field(default_factory=list)

    # Foreign Keys
    action_experience_id: UUID = Field(description="Foreign key for ActionExperience.action_experience_invocations")
    experience_invocation_action_config_id: UUID = Field(
        description="Foreign key for ActionExperienceInvocation.experience_invocation_action_config"
    )

    async def record_invocation(
        self,
        invocation_key: UUID,
        actor_id: UUID | None = None,
        api_call_id: UUID | None = None,
        sdk_operation_call_id: UUID | None = None,
        request_ref: str | None = None,
        receipt_ref: str | None = None,
        status: str = "pending",
    ) -> ExperienceInvocationAction:
        """
        Record one actual invocation handled through this action experience binding.

        Contract:
        - Parentage is `ActionExperience -> ActionExperienceInvocation`.
        - `ExperienceInvocationActionConfig` remains target metadata only.
        - `ExperienceInvocationAction` is the single standalone invocation
          receipt for one action crossing.
        - The action-experience surface records provenance through
          `ActionExperienceInvocationAction`; it does not own receipt identity.
        - Concrete actuator/sensor/view provenance must attach to this same
          receipt through their provenance bridge objects; it must not create
          another invocation receipt for the same crossing.
        """

        payload = {
            "invocation_key": invocation_key,
            "actor_id": actor_id,
            "api_call_id": api_call_id,
            "sdk_operation_call_id": sdk_operation_call_id,
            "request_ref": request_ref,
            "receipt_ref": receipt_ref,
            "status": status,
        }
        result = await invoke_instance(orm_model=self, function_name="record_invocation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.invocation.experience_invocation_action import ExperienceInvocationAction

        if isinstance(value, ExperienceInvocationAction):
            return value
        return ExperienceInvocationAction.validate_invocation_value(value)

    async def add_request_field(
        self, attribute_config_id: UUID, source_ref: str, required: bool = True, position: int | None = None
    ) -> ActionExperienceInvocationRequestField:
        """
        Declare how this action activation composes one endpoint request field.

        Contract:
        - Parentage is `ActionExperience -> ActionExperienceInvocation`.
        - `attribute_config` must belong to the anchored endpoint request
          ClassConfig; runtime dispatch and materialization fail closed if it
          does not.
        - `source_ref` is a closed dispatch-context vocabulary entry:
          event.*, commit.*, intent.*, execution.*, api_call.key, binding.*,
          binding.node.<alias>.class_instance_identity_id,
          binding.node.<alias>.class_config_id, actor.id, or
          subscription.id. No payload paths and no graph reads.
        - This is Tier 1 composition only: declarative field copy from context
          to endpoint request payload. Domain enrichment belongs to the target
          service or to a prior Program step.
        """

        payload = {
            "attribute_config_id": attribute_config_id,
            "source_ref": source_ref,
            "required": required,
            "position": position,
        }
        result = await invoke_instance(orm_model=self, function_name="add_request_field", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.action.action_experience_invocation_request_field import (
            ActionExperienceInvocationRequestField,
        )

        if isinstance(value, ActionExperienceInvocationRequestField):
            return value
        return ActionExperienceInvocationRequestField.validate_invocation_value(value)

    @classmethod
    async def build_via_action_experience(
        cls, action_experience_id: UUID, experience_invocation_action_config_id: UUID
    ) -> ActionExperienceInvocation:
        """Create a deterministic ActionExperience invocation binding edge."""

        payload = {
            "action_experience_id": action_experience_id,
            "experience_invocation_action_config_id": experience_invocation_action_config_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_action_experience", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActionExperienceInvocation):
            return value
        return ActionExperienceInvocation.validate_invocation_value(value)


class ActionExperienceInvocationRecordInvocationInput(BaseModel):
    invocation_key: UUID
    actor_id: UUID | None = Field(default=None)
    api_call_id: UUID | None = Field(default=None)
    sdk_operation_call_id: UUID | None = Field(default=None)
    request_ref: str | None = Field(default=None)
    receipt_ref: str | None = Field(default=None)
    status: str = Field(default="pending")


class ActionExperienceInvocationRecordInvocationOutput(BaseModel):
    value: ExperienceInvocationAction


class ActionExperienceInvocationAddRequestFieldInput(BaseModel):
    attribute_config_id: UUID
    source_ref: str
    required: bool = Field(default=True)
    position: int | None = Field(default=None)


class ActionExperienceInvocationAddRequestFieldOutput(BaseModel):
    value: ActionExperienceInvocationRequestField


class ActionExperienceInvocationBuildViaActionExperienceInput(BaseModel):
    action_experience_id: UUID = Field(description="Foreign key for ActionExperience.action_experience_invocations")
    experience_invocation_action_config_id: UUID


class ActionExperienceInvocationBuildViaActionExperienceOutput(BaseModel):
    value: ActionExperienceInvocation


FUNCTIONS = {
    "ActionExperienceInvocation": {
        "record_invocation": {
            "canonical": {
                "name": "record_invocation",
                "description": "Record one actual invocation handled through this action experience binding.\n\nContract:\n- Parentage is `ActionExperience -> ActionExperienceInvocation`.\n- `ExperienceInvocationActionConfig` remains target metadata only.\n- `ExperienceInvocationAction` is the single standalone invocation\n  receipt for one action crossing.\n- The action-experience surface records provenance through\n  `ActionExperienceInvocationAction`; it does not own receipt identity.\n- Concrete actuator/sensor/view provenance must attach to this same\n  receipt through their provenance bridge objects; it must not create\n  another invocation receipt for the same crossing.",
                "is_constructor": False,
            },
            "input": ActionExperienceInvocationRecordInvocationInput,
            "output": ActionExperienceInvocationRecordInvocationOutput,
        },
        "add_request_field": {
            "canonical": {
                "name": "add_request_field",
                "description": "Declare how this action activation composes one endpoint request field.\n\nContract:\n- Parentage is `ActionExperience -> ActionExperienceInvocation`.\n- `attribute_config` must belong to the anchored endpoint request\n  ClassConfig; runtime dispatch and materialization fail closed if it\n  does not.\n- `source_ref` is a closed dispatch-context vocabulary entry:\n  event.*, commit.*, intent.*, execution.*, api_call.key, binding.*,\n  binding.node.<alias>.class_instance_identity_id,\n  binding.node.<alias>.class_config_id, actor.id, or\n  subscription.id. No payload paths and no graph reads.\n- This is Tier 1 composition only: declarative field copy from context\n  to endpoint request payload. Domain enrichment belongs to the target\n  service or to a prior Program step.",
                "is_constructor": False,
            },
            "input": ActionExperienceInvocationAddRequestFieldInput,
            "output": ActionExperienceInvocationAddRequestFieldOutput,
        },
        "build_via_action_experience": {
            "canonical": {
                "name": "build_via_action_experience",
                "description": "Create a deterministic ActionExperience invocation binding edge.",
                "is_constructor": True,
            },
            "input": ActionExperienceInvocationBuildViaActionExperienceInput,
            "output": ActionExperienceInvocationBuildViaActionExperienceOutput,
        },
    },
}

__all__ = [
    "ActionExperienceInvocation",
    "ActionExperienceInvocationRecordInvocationInput",
    "ActionExperienceInvocationRecordInvocationOutput",
    "ActionExperienceInvocationAddRequestFieldInput",
    "ActionExperienceInvocationAddRequestFieldOutput",
    "ActionExperienceInvocationBuildViaActionExperienceInput",
    "ActionExperienceInvocationBuildViaActionExperienceOutput",
    "FUNCTIONS",
]
