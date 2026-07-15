from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Economy Ontology Orm Models
from aware_economy_ontology_orm_models.external_capital.external_capital_enums import ExternalCapitalProviderStatus

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.external_capital.external_capital_provider_route import (
        ExternalCapitalProviderRoute,
    )
    from aware_economy_ontology_orm_models.finance.finance_entity import FinanceEntity


class ExternalCapitalProviderConfig(ORMModel):
    # Relationships
    provider_finance_entity: FinanceEntity | None = Field(default=None, exclude=True)
    routes: list[ExternalCapitalProviderRoute] = Field(default_factory=list, exclude=True)

    # Attributes
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    label: str | None = Field(default=None)
    provider_key: str
    status: ExternalCapitalProviderStatus = Field(default=ExternalCapitalProviderStatus.active)

    # Foreign Keys
    provider_finance_entity_id: UUID = Field(
        description="Foreign key for ExternalCapitalProviderConfig.provider_finance_entity"
    )
