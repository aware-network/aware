from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Attention Ontology
from aware_attention_ontology.actor.actor_focus_enums import (
    ActorFocusLevelType,
    ActorFocusRequestStatus,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_attention_ontology.actor.actor_focus_request_response import ActorFocusRequestResponse
    from aware_attention_ontology.focus.focus import Focus
    from aware_identity_ontology.actor.actor import Actor


class ActorFocusRequest(ORMModel):
    """A focus request actor to actor"""

    # Relationships
    sender: Actor | None = Field(default=None, exclude=True)
    receiver: Actor | None = Field(default=None, exclude=True)
    focus: Focus | None = Field(default=None, exclude=True)
    response: ActorFocusRequestResponse | None = Field(default=None, exclude=True)

    # Attributes
    suggested_level: ActorFocusLevelType
    rationale: str
    status: ActorFocusRequestStatus = Field(default=ActorFocusRequestStatus.pending)
    confidence: float | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    response_message: str | None = Field(default=None)

    # Foreign Keys
    sender_id: UUID = Field(description="Foreign key for ActorFocusRequest.sender")
    receiver_id: UUID = Field(description="Foreign key for ActorFocusRequest.receiver")
    focus_id: UUID = Field(description="Foreign key for ActorFocusRequest.focus")
    response_id: UUID | None = Field(default=None, description="Foreign key for ActorFocusRequest.response")

    @classmethod
    async def build(
        cls,
        sender_id: UUID,
        receiver_id: UUID,
        focus_id: UUID,
        suggested_level: ActorFocusLevelType,
        rationale: str,
        confidence: float | None = None,
        expires_at: datetime | None = None,
    ) -> ActorFocusRequest:
        """Builds a new ActorFocusRequest."""

        payload = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "focus_id": focus_id,
            "suggested_level": suggested_level,
            "rationale": rationale,
            "confidence": confidence,
            "expires_at": expires_at,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActorFocusRequest):
            return value
        return ActorFocusRequest.validate_invocation_value(value)

    async def accept(self, decided_by_id: UUID) -> ActorFocusRequestResponse:
        """Accepts the request if it is pending and has not expired."""

        payload = {"decided_by_id": decided_by_id}
        result = await invoke_instance(orm_model=self, function_name="accept", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.actor.actor_focus_request_response import ActorFocusRequestResponse

        if isinstance(value, ActorFocusRequestResponse):
            return value
        return ActorFocusRequestResponse.validate_invocation_value(value)

    async def expire(self) -> int:
        """Expires the request if it has expired."""

        payload = {}
        result = await invoke_instance(orm_model=self, function_name="expire", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        return value

    async def reject(self, decided_by_id: UUID) -> ActorFocusRequestResponse:
        """Rejects the request if it is pending and has not expired."""

        payload = {"decided_by_id": decided_by_id}
        result = await invoke_instance(orm_model=self, function_name="reject", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.actor.actor_focus_request_response import ActorFocusRequestResponse

        if isinstance(value, ActorFocusRequestResponse):
            return value
        return ActorFocusRequestResponse.validate_invocation_value(value)


class ActorFocusRequestBuildInput(BaseModel):
    sender_id: UUID
    receiver_id: UUID
    focus_id: UUID
    suggested_level: ActorFocusLevelType
    rationale: str
    confidence: float | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)


class ActorFocusRequestBuildOutput(BaseModel):
    value: ActorFocusRequest


class ActorFocusRequestAcceptInput(BaseModel):
    decided_by_id: UUID


class ActorFocusRequestAcceptOutput(BaseModel):
    value: ActorFocusRequestResponse


class ActorFocusRequestExpireInput(BaseModel):
    pass


class ActorFocusRequestExpireOutput(BaseModel):
    value: int


class ActorFocusRequestRejectInput(BaseModel):
    decided_by_id: UUID


class ActorFocusRequestRejectOutput(BaseModel):
    value: ActorFocusRequestResponse


FUNCTIONS = {
    "ActorFocusRequest": {
        "build": {
            "canonical": {"name": "build", "description": "Builds a new ActorFocusRequest.", "is_constructor": True},
            "input": ActorFocusRequestBuildInput,
            "output": ActorFocusRequestBuildOutput,
        },
        "accept": {
            "canonical": {
                "name": "accept",
                "description": "Accepts the request if it is pending and has not expired.",
                "is_constructor": False,
            },
            "input": ActorFocusRequestAcceptInput,
            "output": ActorFocusRequestAcceptOutput,
        },
        "expire": {
            "canonical": {
                "name": "expire",
                "description": "Expires the request if it has expired.",
                "is_constructor": False,
            },
            "input": ActorFocusRequestExpireInput,
            "output": ActorFocusRequestExpireOutput,
        },
        "reject": {
            "canonical": {
                "name": "reject",
                "description": "Rejects the request if it is pending and has not expired.",
                "is_constructor": False,
            },
            "input": ActorFocusRequestRejectInput,
            "output": ActorFocusRequestRejectOutput,
        },
    },
}

__all__ = [
    "ActorFocusRequest",
    "ActorFocusRequestBuildInput",
    "ActorFocusRequestBuildOutput",
    "ActorFocusRequestAcceptInput",
    "ActorFocusRequestAcceptOutput",
    "ActorFocusRequestExpireInput",
    "ActorFocusRequestExpireOutput",
    "ActorFocusRequestRejectInput",
    "ActorFocusRequestRejectOutput",
    "FUNCTIONS",
]
