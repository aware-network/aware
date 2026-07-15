from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Api Ontology Orm Models
from aware_api_ontology_orm_models.api.api_call_enums import ApiCallOutcomeStatus

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.inline_value_instance import InlineValueInstance


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
