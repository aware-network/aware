from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.finance.finance_entity import FinanceEntity
    from aware_economy_ontology_orm_models.smart_contract.smart_contract_config import SmartContractConfig


class ServiceCommercialProfile(ORMModel):
    # Relationships
    default_smart_contract_config: SmartContractConfig | None = Field(default=None, exclude=True)
    producer_finance_entity: FinanceEntity | None = Field(default=None, exclude=True)

    # Attributes
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    service_id: UUID | None = Field(default=None, description="Foreign key for Service.commercial_profile")
    default_smart_contract_config_id: UUID | None = Field(
        default=None, description="Foreign key for ServiceCommercialProfile.default_smart_contract_config"
    )
    producer_finance_entity_id: UUID = Field(
        description="Foreign key for ServiceCommercialProfile.producer_finance_entity"
    )
