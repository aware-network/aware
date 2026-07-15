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
    from aware_attention_ontology.focus.focus_scope_request import FocusScopeRequest


class ActorFocusScopeRequest(ORMModel):
    # Relationships
    focus_scope_request: FocusScopeRequest | None = Field(default=None, exclude=True)

    # Foreign Keys
    actor_focus_scope_id: UUID = Field(description="Foreign key for ActorFocusScope.requests")
    focus_scope_request_id: UUID = Field(description="Foreign key for ActorFocusScopeRequest.focus_scope_request")

    @classmethod
    async def create_via_actor_focus_scope(
        cls, actor_focus_scope_id: UUID, focus_scope_request_id: UUID
    ) -> ActorFocusScopeRequest:
        """Builds a new ActorFocusScopeRequest by linking ActorFocusScope to FocusScopeRequest."""

        payload = {"actor_focus_scope_id": actor_focus_scope_id, "focus_scope_request_id": focus_scope_request_id}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_actor_focus_scope", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActorFocusScopeRequest):
            return value
        return ActorFocusScopeRequest.validate_invocation_value(value)


class ActorFocusScopeRequestCreateViaActorFocusScopeInput(BaseModel):
    actor_focus_scope_id: UUID = Field(description="Foreign key for ActorFocusScope.requests")
    focus_scope_request_id: UUID


class ActorFocusScopeRequestCreateViaActorFocusScopeOutput(BaseModel):
    value: ActorFocusScopeRequest


FUNCTIONS = {
    "ActorFocusScopeRequest": {
        "create_via_actor_focus_scope": {
            "canonical": {
                "name": "create_via_actor_focus_scope",
                "description": "Builds a new ActorFocusScopeRequest by linking ActorFocusScope to FocusScopeRequest.",
                "is_constructor": True,
            },
            "input": ActorFocusScopeRequestCreateViaActorFocusScopeInput,
            "output": ActorFocusScopeRequestCreateViaActorFocusScopeOutput,
        },
    },
}

__all__ = [
    "ActorFocusScopeRequest",
    "ActorFocusScopeRequestCreateViaActorFocusScopeInput",
    "ActorFocusScopeRequestCreateViaActorFocusScopeOutput",
    "FUNCTIONS",
]
