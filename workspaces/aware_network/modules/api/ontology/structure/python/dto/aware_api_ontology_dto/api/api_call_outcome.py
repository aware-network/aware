from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Api Ontology Dto
from aware_api_ontology_dto.api.api_call_enums import ApiCallOutcomeStatus

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.inline_value_instance import InlineValueInstance


class ApiCallOutcome(BaseModel):
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
