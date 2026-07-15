from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology Dto
from aware_economy_ontology_dto.external_capital.external_capital_enums import ExternalCapitalProviderStatus

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology_dto.external_capital.external_capital_provider_route import ExternalCapitalProviderRoute
    from aware_economy_ontology_dto.finance.finance_entity import FinanceEntity


class ExternalCapitalProviderConfig(BaseModel):
    # Relationships
    provider_finance_entity: FinanceEntity | None = Field(default=None)
    routes: list[ExternalCapitalProviderRoute] = Field(default_factory=list)

    # Attributes
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    label: str | None = Field(default=None)
    provider_key: str
    status: ExternalCapitalProviderStatus = Field(default=ExternalCapitalProviderStatus.active)
