from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Api Ontology
from aware_api_ontology.api.api_call_enums import ApiCallOutcomeStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance


class ApiCallOutcome(ORMModel):
    """
    Terminal API-owned response receipt for one committed ApiCall.
    Contract:
    - API owns normalized response payload truth when an endpoint declares a response contract
    - `status` + `error` capture terminal completion independently from Service execution receipts
    - absence of `response_model` is valid for failures or no-content responses
    """

    # Relationships
    response_model: InlineValueInstance | None = Field(default=None)

    # Attributes
    error: str | None = Field(default=None)
    status: ApiCallOutcomeStatus = Field(default=ApiCallOutcomeStatus.succeeded)

    # Foreign Keys
    api_call_id: UUID | None = Field(default=None, description="Foreign key for ApiCall.outcome")
    response_model_id: UUID | None = Field(default=None, description="Foreign key for ApiCallOutcome.response_model")

    @classmethod
    async def build_via_api_call(
        cls, api_call_id: UUID, status: ApiCallOutcomeStatus = ApiCallOutcomeStatus.succeeded, error: str | None = None
    ) -> ApiCallOutcome:
        """Create one terminal response receipt under ApiCall."""

        payload = {"api_call_id": api_call_id, "status": status, "error": error}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_api_call", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiCallOutcome):
            return value
        return ApiCallOutcome.validate_invocation_value(value)


class ApiCallOutcomeBuildViaApiCallInput(BaseModel):
    api_call_id: UUID = Field(description="Foreign key for ApiCall.outcome")
    status: ApiCallOutcomeStatus = Field(default=ApiCallOutcomeStatus.succeeded)
    error: str | None = Field(default=None)


class ApiCallOutcomeBuildViaApiCallOutput(BaseModel):
    value: ApiCallOutcome


FUNCTIONS = {
    "ApiCallOutcome": {
        "build_via_api_call": {
            "canonical": {
                "name": "build_via_api_call",
                "description": "Create one terminal response receipt under ApiCall.",
                "is_constructor": True,
            },
            "input": ApiCallOutcomeBuildViaApiCallInput,
            "output": ApiCallOutcomeBuildViaApiCallOutput,
        },
    },
}

__all__ = [
    "ApiCallOutcome",
    "ApiCallOutcomeBuildViaApiCallInput",
    "ApiCallOutcomeBuildViaApiCallOutput",
    "FUNCTIONS",
]
