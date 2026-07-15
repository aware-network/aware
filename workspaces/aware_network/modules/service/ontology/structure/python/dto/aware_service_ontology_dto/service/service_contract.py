from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Service Ontology Dto
from aware_service_ontology_dto.service.service_enums import (
    ServiceContractKind,
    ServiceContractStatus,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology_dto.finance.finance_entity import FinanceEntity
    from aware_economy_ontology_dto.smart_contract.smart_contract import SmartContract
    from aware_service_ontology_dto.service.service_commercial_profile import ServiceCommercialProfile
    from aware_service_ontology_dto.service.service_contract_config import ServiceContractConfig
    from aware_service_ontology_dto.service.service_contract_economy_settlement import ServiceContractEconomySettlement


class ServiceContract(BaseModel):
    # Relationships
    commercial_profile: ServiceCommercialProfile | None = Field(default=None)
    consumer_finance_entity: FinanceEntity | None = Field(default=None)
    economy_settlement: ServiceContractEconomySettlement | None = Field(default=None)
    producer_finance_entity: FinanceEntity | None = Field(default=None)
    service_contract_config: ServiceContractConfig | None = Field(default=None)
    smart_contract: SmartContract | None = Field(default=None)

    # Attributes
    effective_from: datetime
    effective_until: datetime | None = Field(default=None)
    kind: ServiceContractKind
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
    status: ServiceContractStatus = Field(default=ServiceContractStatus.pending)
