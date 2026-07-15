from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Service Ontology Orm Models
from aware_service_ontology_orm_models.service.service_enums import (
    ServiceContractKind,
    ServiceContractStatus,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.finance.finance_entity import FinanceEntity
    from aware_economy_ontology_orm_models.smart_contract.smart_contract import SmartContract
    from aware_service_ontology_orm_models.service.service_commercial_profile import ServiceCommercialProfile
    from aware_service_ontology_orm_models.service.service_contract_config import ServiceContractConfig
    from aware_service_ontology_orm_models.service.service_contract_economy_settlement import (
        ServiceContractEconomySettlement,
    )


class ServiceContract(ORMModel):
    # Relationships
    commercial_profile: ServiceCommercialProfile | None = Field(default=None, exclude=True)
    consumer_finance_entity: FinanceEntity | None = Field(default=None, exclude=True)
    economy_settlement: ServiceContractEconomySettlement | None = Field(default=None, exclude=True)
    producer_finance_entity: FinanceEntity | None = Field(default=None, exclude=True)
    service_contract_config: ServiceContractConfig | None = Field(default=None, exclude=True)
    smart_contract: SmartContract | None = Field(default=None, exclude=True)

    # Attributes
    effective_from: datetime
    effective_until: datetime | None = Field(default=None)
    kind: ServiceContractKind
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
    status: ServiceContractStatus = Field(default=ServiceContractStatus.pending)

    # Foreign Keys
    service_id: UUID = Field(description="Foreign key for Service.contracts")
    commercial_profile_id: UUID = Field(description="Foreign key for ServiceContract.commercial_profile")
    consumer_finance_entity_id: UUID = Field(description="Foreign key for ServiceContract.consumer_finance_entity")
    producer_finance_entity_id: UUID = Field(description="Foreign key for ServiceContract.producer_finance_entity")
    service_contract_config_id: UUID = Field(description="Foreign key for ServiceContract.service_contract_config")
    smart_contract_id: UUID = Field(description="Foreign key for ServiceContract.smart_contract")
