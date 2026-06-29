from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_call import ApiCall


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
