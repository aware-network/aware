from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Api Ontology
from aware_api_ontology.api.api_view_stream_enums import ApiViewStreamMode

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class ApiViewStreamPolicy(ORMModel):
    """Optional stream policy for one readable API view contract."""

    # Attributes
    stream_mode: ApiViewStreamMode
    description: str | None = Field(default=None)

    # Foreign Keys
    api_view_id: UUID | None = Field(default=None, description="Foreign key for ApiView.stream_policy")

    @classmethod
    async def build_via_api_view(
        cls, api_view_id: UUID, stream_mode: ApiViewStreamMode, description: str | None = None
    ) -> ApiViewStreamPolicy:
        """Create one API view stream policy beneath ApiView."""

        payload = {"api_view_id": api_view_id, "stream_mode": stream_mode, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_api_view", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiViewStreamPolicy):
            return value
        return ApiViewStreamPolicy.validate_invocation_value(value)


class ApiViewStreamPolicyBuildViaApiViewInput(BaseModel):
    api_view_id: UUID = Field(description="Foreign key for ApiView.stream_policy")
    stream_mode: ApiViewStreamMode
    description: str | None = Field(default=None)


class ApiViewStreamPolicyBuildViaApiViewOutput(BaseModel):
    value: ApiViewStreamPolicy


FUNCTIONS = {
    "ApiViewStreamPolicy": {
        "build_via_api_view": {
            "canonical": {
                "name": "build_via_api_view",
                "description": "Create one API view stream policy beneath ApiView.",
                "is_constructor": True,
            },
            "input": ApiViewStreamPolicyBuildViaApiViewInput,
            "output": ApiViewStreamPolicyBuildViaApiViewOutput,
        },
    },
}

__all__ = [
    "ApiViewStreamPolicy",
    "ApiViewStreamPolicyBuildViaApiViewInput",
    "ApiViewStreamPolicyBuildViaApiViewOutput",
    "FUNCTIONS",
]
