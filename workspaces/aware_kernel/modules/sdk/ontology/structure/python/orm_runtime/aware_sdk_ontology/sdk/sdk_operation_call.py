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
    from aware_api_ontology.api.api_call import ApiCall


class SdkOperationCall(ORMModel):
    """
    SDK-owned operation invocation receipt.
    Contract:
    - `SdkOperation` is reusable configuration.
    - `SdkOperationCall` is one concrete SDK dispatch attempt.
    - API ingress remains API-owned; `api_call` only links to the API receipt
    emitted by this SDK dispatch when the operation crosses the API boundary.
    """

    # Relationships
    api_call: ApiCall | None = Field(default=None)

    # Attributes
    call_key: UUID = Field(description="Stable external/request identity for one SDK dispatch attempt.")
    description: str | None = Field(default=None)
    request_hash: str
    context_hash: str | None = Field(default=None)
    status: str = Field(default="pending")

    # Foreign Keys
    sdk_operation_id: UUID = Field(description="Foreign key for SdkOperation.sdk_operation_calls")
    api_call_id: UUID | None = Field(default=None, description="Foreign key for SdkOperationCall.api_call")

    @classmethod
    async def create_via_sdk_operation(
        cls,
        sdk_operation_id: UUID,
        call_key: UUID,
        request_hash: str,
        description: str | None = None,
        context_hash: str | None = None,
        status: str = "pending",
        api_call_id: UUID | None = None,
    ) -> SdkOperationCall:
        """
        Create one SDK operation call receipt under SdkOperation.

        Contract:
        - Parent `SdkOperation` scope is propagated by constructor lowering.
        - `request_hash` is the durable payload fingerprint until typed SDK request
          value instances are introduced.
        - `api_call_id` links to API ingress provenance without making API own SDK
          dispatch truth.
        """

        payload = {
            "sdk_operation_id": sdk_operation_id,
            "call_key": call_key,
            "request_hash": request_hash,
            "description": description,
            "context_hash": context_hash,
            "status": status,
            "api_call_id": api_call_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_sdk_operation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SdkOperationCall):
            return value
        return SdkOperationCall.validate_invocation_value(value)


class SdkOperationCallCreateViaSdkOperationInput(BaseModel):
    sdk_operation_id: UUID = Field(description="Foreign key for SdkOperation.sdk_operation_calls")
    call_key: UUID
    request_hash: str
    description: str | None = Field(default=None)
    context_hash: str | None = Field(default=None)
    status: str = Field(default="pending")
    api_call_id: UUID | None = Field(default=None)


class SdkOperationCallCreateViaSdkOperationOutput(BaseModel):
    value: SdkOperationCall


FUNCTIONS = {
    "SdkOperationCall": {
        "create_via_sdk_operation": {
            "canonical": {
                "name": "create_via_sdk_operation",
                "description": "Create one SDK operation call receipt under SdkOperation.\n\nContract:\n- Parent `SdkOperation` scope is propagated by constructor lowering.\n- `request_hash` is the durable payload fingerprint until typed SDK request\n  value instances are introduced.\n- `api_call_id` links to API ingress provenance without making API own SDK\n  dispatch truth.",
                "is_constructor": True,
            },
            "input": SdkOperationCallCreateViaSdkOperationInput,
            "output": SdkOperationCallCreateViaSdkOperationOutput,
        },
    },
}

__all__ = [
    "SdkOperationCall",
    "SdkOperationCallCreateViaSdkOperationInput",
    "SdkOperationCallCreateViaSdkOperationOutput",
    "FUNCTIONS",
]
