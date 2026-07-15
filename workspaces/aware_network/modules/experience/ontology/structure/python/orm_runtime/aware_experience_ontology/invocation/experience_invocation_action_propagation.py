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


class ExperienceInvocationActionPropagation(ORMModel):
    """
    Causal propagation edge between two Experience invocation actions.
    Contract:
    - Actions can invoke or delegate to other actions without collapsing their
    receipts.
    - Each action owns its own API/SDK/service call, actor, commit, and event
    provenance.
    """

    # Relationships
    target_invocation_action: ExperienceInvocationAction | None = Field(default=None)

    # Attributes
    propagation_kind: str = Field(default="invokes")
    description: str | None = Field(default=None)

    # Foreign Keys
    experience_invocation_action_id: UUID = Field(description="Foreign key for ExperienceInvocationAction.propagations")
    target_invocation_action_id: UUID = Field(
        description="Foreign key for ExperienceInvocationActionPropagation.target_invocation_action"
    )

    @classmethod
    async def build_via_experience_invocation_action(
        cls,
        experience_invocation_action_id: UUID,
        target_invocation_action_id: UUID,
        propagation_kind: str = "invokes",
        description: str | None = None,
    ) -> ExperienceInvocationActionPropagation:
        """
        Link this invocation action to a target invocation action it caused.

        Contract:
        - Parent `ExperienceInvocationAction` is the source action.
        - Target action keeps its own receipts and graph/event provenance.
        """

        payload = {
            "experience_invocation_action_id": experience_invocation_action_id,
            "target_invocation_action_id": target_invocation_action_id,
            "propagation_kind": propagation_kind,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_experience_invocation_action", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ExperienceInvocationActionPropagation):
            return value
        return ExperienceInvocationActionPropagation.validate_invocation_value(value)


class ExperienceInvocationActionPropagationBuildViaExperienceInvocationActionInput(BaseModel):
    experience_invocation_action_id: UUID = Field(description="Foreign key for ExperienceInvocationAction.propagations")
    target_invocation_action_id: UUID
    propagation_kind: str = Field(default="invokes")
    description: str | None = Field(default=None)


class ExperienceInvocationActionPropagationBuildViaExperienceInvocationActionOutput(BaseModel):
    value: ExperienceInvocationActionPropagation


FUNCTIONS = {
    "ExperienceInvocationActionPropagation": {
        "build_via_experience_invocation_action": {
            "canonical": {
                "name": "build_via_experience_invocation_action",
                "description": "Link this invocation action to a target invocation action it caused.\n\nContract:\n- Parent `ExperienceInvocationAction` is the source action.\n- Target action keeps its own receipts and graph/event provenance.",
                "is_constructor": True,
            },
            "input": ExperienceInvocationActionPropagationBuildViaExperienceInvocationActionInput,
            "output": ExperienceInvocationActionPropagationBuildViaExperienceInvocationActionOutput,
        },
    },
}

__all__ = [
    "ExperienceInvocationActionPropagation",
    "ExperienceInvocationActionPropagationBuildViaExperienceInvocationActionInput",
    "ExperienceInvocationActionPropagationBuildViaExperienceInvocationActionOutput",
    "FUNCTIONS",
]
