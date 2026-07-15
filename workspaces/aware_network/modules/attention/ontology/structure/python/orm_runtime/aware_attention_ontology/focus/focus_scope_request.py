from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Attention Ontology
from aware_attention_ontology.focus.focus_enums import FocusScopeRequestStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_attention_ontology.focus.focus import Focus
    from aware_attention_ontology.focus.focus_scope_request_response import FocusScopeRequestResponse


class FocusScopeRequest(ORMModel):
    # Relationships
    focus: Focus | None = Field(default=None, exclude=True)
    response: FocusScopeRequestResponse | None = Field(default=None, exclude=True)

    # Attributes
    rationale: str | None = Field(default=None)
    state: FocusScopeRequestStatus = Field(default=FocusScopeRequestStatus.pending)
    response_rationale: str | None = Field(default=None, description="Response")

    # Foreign Keys
    focus_scope_id: UUID = Field(description="Foreign key for FocusScope.requests")
    focus_id: UUID = Field(description="Foreign key for FocusScopeRequest.focus")

    async def accept(self, decided_by_id: UUID, message: str | None = None) -> FocusScopeRequestResponse:
        """Accepts the request if it is pending and has not expired."""

        payload = {"decided_by_id": decided_by_id, "message": message}
        result = await invoke_instance(orm_model=self, function_name="accept", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.focus.focus_scope_request_response import FocusScopeRequestResponse

        if isinstance(value, FocusScopeRequestResponse):
            return value
        return FocusScopeRequestResponse.validate_invocation_value(value)

    async def expire(self) -> int:
        """Expires the request if it has expired."""

        payload = {}
        result = await invoke_instance(orm_model=self, function_name="expire", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        return value

    async def reject(self, decided_by_id: UUID, message: str | None = None) -> FocusScopeRequestResponse:
        """Rejects the request if it is pending and has not expired."""

        payload = {"decided_by_id": decided_by_id, "message": message}
        result = await invoke_instance(orm_model=self, function_name="reject", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.focus.focus_scope_request_response import FocusScopeRequestResponse

        if isinstance(value, FocusScopeRequestResponse):
            return value
        return FocusScopeRequestResponse.validate_invocation_value(value)

    @classmethod
    async def create_via_focus_scope(
        cls, focus_scope_id: UUID, focus_id: UUID, rationale: str | None = None
    ) -> FocusScopeRequest:
        """Builds a new FocusScopeRequest"""

        payload = {"focus_scope_id": focus_scope_id, "focus_id": focus_id, "rationale": rationale}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_focus_scope", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FocusScopeRequest):
            return value
        return FocusScopeRequest.validate_invocation_value(value)


class FocusScopeRequestAcceptInput(BaseModel):
    decided_by_id: UUID
    message: str | None = Field(default=None)


class FocusScopeRequestAcceptOutput(BaseModel):
    value: FocusScopeRequestResponse


class FocusScopeRequestExpireInput(BaseModel):
    pass


class FocusScopeRequestExpireOutput(BaseModel):
    value: int


class FocusScopeRequestRejectInput(BaseModel):
    decided_by_id: UUID
    message: str | None = Field(default=None)


class FocusScopeRequestRejectOutput(BaseModel):
    value: FocusScopeRequestResponse


class FocusScopeRequestCreateViaFocusScopeInput(BaseModel):
    focus_scope_id: UUID = Field(description="Foreign key for FocusScope.requests")
    focus_id: UUID
    rationale: str | None = Field(default=None)


class FocusScopeRequestCreateViaFocusScopeOutput(BaseModel):
    value: FocusScopeRequest


FUNCTIONS = {
    "FocusScopeRequest": {
        "accept": {
            "canonical": {
                "name": "accept",
                "description": "Accepts the request if it is pending and has not expired.",
                "is_constructor": False,
            },
            "input": FocusScopeRequestAcceptInput,
            "output": FocusScopeRequestAcceptOutput,
        },
        "expire": {
            "canonical": {
                "name": "expire",
                "description": "Expires the request if it has expired.",
                "is_constructor": False,
            },
            "input": FocusScopeRequestExpireInput,
            "output": FocusScopeRequestExpireOutput,
        },
        "reject": {
            "canonical": {
                "name": "reject",
                "description": "Rejects the request if it is pending and has not expired.",
                "is_constructor": False,
            },
            "input": FocusScopeRequestRejectInput,
            "output": FocusScopeRequestRejectOutput,
        },
        "create_via_focus_scope": {
            "canonical": {
                "name": "create_via_focus_scope",
                "description": "Builds a new FocusScopeRequest",
                "is_constructor": True,
            },
            "input": FocusScopeRequestCreateViaFocusScopeInput,
            "output": FocusScopeRequestCreateViaFocusScopeOutput,
        },
    },
}

__all__ = [
    "FocusScopeRequest",
    "FocusScopeRequestAcceptInput",
    "FocusScopeRequestAcceptOutput",
    "FocusScopeRequestExpireInput",
    "FocusScopeRequestExpireOutput",
    "FocusScopeRequestRejectInput",
    "FocusScopeRequestRejectOutput",
    "FocusScopeRequestCreateViaFocusScopeInput",
    "FocusScopeRequestCreateViaFocusScopeOutput",
    "FUNCTIONS",
]
