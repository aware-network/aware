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
    from aware_identity_ontology.actor.actor import Actor


class Human(ORMModel):
    # Relationships
    actor: Actor | None = Field(default=None, exclude=True)

    # Foreign Keys
    actor_id: UUID = Field(description="Foreign key for Human.actor")

    @classmethod
    async def create_human(cls, actor_id: UUID) -> Human:
        """
        Create a human bound to an actor.

        v0: used by `Identity.signup` to build the minimal Identity→Human graph
        while preserving the hard mutation boundary (mutate-self-only).
        """

        payload = {"actor_id": actor_id}
        result = await invoke_constructor(orm_class=cls, function_name="create_human", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Human):
            return value
        return Human.validate_invocation_value(value)

    async def get_display_name(self, p_human_id: UUID) -> str:
        """
        Gets the display name for a human.
        Parameters: p_human_id: The UUID of the human.
        Returns: The human''s display name from their profile
        """

        payload = {"p_human_id": p_human_id}
        result = await invoke_instance(orm_model=self, function_name="get_display_name", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        return value


class HumanCreateHumanInput(BaseModel):
    actor_id: UUID


class HumanCreateHumanOutput(BaseModel):
    value: Human


class HumanGetDisplayNameInput(BaseModel):
    p_human_id: UUID


class HumanGetDisplayNameOutput(BaseModel):
    value: str


FUNCTIONS = {
    "Human": {
        "create_human": {
            "canonical": {
                "name": "create_human",
                "description": "Create a human bound to an actor.\n\nv0: used by `Identity.signup` to build the minimal Identity→Human graph\nwhile preserving the hard mutation boundary (mutate-self-only).",
                "is_constructor": True,
            },
            "input": HumanCreateHumanInput,
            "output": HumanCreateHumanOutput,
        },
        "get_display_name": {
            "canonical": {
                "name": "get_display_name",
                "description": "Gets the display name for a human.\nParameters: p_human_id: The UUID of the human.\nReturns: The human''s display name from their profile",
                "is_constructor": False,
            },
            "input": HumanGetDisplayNameInput,
            "output": HumanGetDisplayNameOutput,
        },
    },
}

__all__ = [
    "Human",
    "HumanCreateHumanInput",
    "HumanCreateHumanOutput",
    "HumanGetDisplayNameInput",
    "HumanGetDisplayNameOutput",
    "FUNCTIONS",
]
