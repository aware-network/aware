from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class FocusScopeRequestResponse(ORMModel):
    # Attributes
    success: bool
    message: str | None = Field(default=None)

    # Foreign Keys
    focus_scope_request_id: UUID | None = Field(default=None, description="Foreign key for FocusScopeRequest.response")

    @classmethod
    async def build_via_focus_scope_request(
        cls, focus_scope_request_id: UUID, success: bool, message: str | None = None
    ) -> FocusScopeRequestResponse:
        """Builds a new FocusScopeRequestResponse"""

        payload = {"focus_scope_request_id": focus_scope_request_id, "success": success, "message": message}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_focus_scope_request", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FocusScopeRequestResponse):
            return value
        return FocusScopeRequestResponse.validate_invocation_value(value)


class FocusScopeRequestResponseBuildViaFocusScopeRequestInput(BaseModel):
    focus_scope_request_id: UUID = Field(description="Foreign key for FocusScopeRequest.response")
    success: bool
    message: str | None = Field(default=None)


class FocusScopeRequestResponseBuildViaFocusScopeRequestOutput(BaseModel):
    value: FocusScopeRequestResponse


FUNCTIONS = {
    "FocusScopeRequestResponse": {
        "build_via_focus_scope_request": {
            "canonical": {
                "name": "build_via_focus_scope_request",
                "description": "Builds a new FocusScopeRequestResponse",
                "is_constructor": True,
            },
            "input": FocusScopeRequestResponseBuildViaFocusScopeRequestInput,
            "output": FocusScopeRequestResponseBuildViaFocusScopeRequestOutput,
        },
    },
}

__all__ = [
    "FocusScopeRequestResponse",
    "FocusScopeRequestResponseBuildViaFocusScopeRequestInput",
    "FocusScopeRequestResponseBuildViaFocusScopeRequestOutput",
    "FUNCTIONS",
]
