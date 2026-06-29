from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_call_outcome import ApiCallOutcome
    from aware_meta_ontology_dto.class_.inline_value_instance import InlineValueInstance


class ApiCall(BaseModel):
    """
    Stage-one API-owned ingress/provenance receipt.
    Contract:
    - one `ApiCall` means one caller hit on one `ApiCapabilityEndpoint`
    - normalized request-model truth is one `InlineValueInstance`
    - this object is ingress truth only and must not collapse into endpoint-function or Service fulfillment rails
    """

    # Relationships
    outcome: ApiCallOutcome | None = Field(default=None)
    request_model: InlineValueInstance

    # Attributes
    call_key: UUID = Field(description="Stable external/request identity for one endpoint hit.")
    description: str | None = Field(default=None)
    request_hash: str
