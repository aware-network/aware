from __future__ import annotations

# Standard
from datetime import datetime
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)
from uuid import UUID

# Third-party
from pydantic import Field

# Economy Ontology Orm Models
from aware_economy_ontology_orm_models.smart_contract.smart_contract_permit_enums import SmartContractPermitStatus

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.coin.coin import Coin
    from aware_economy_ontology_orm_models.finance.finance_entity import FinanceEntity
    from aware_economy_ontology_orm_models.price.price_schedule import PriceSchedule
    from aware_economy_ontology_orm_models.smart_contract.smart_contract_reservation import SmartContractReservation


class SmartContractPermit(ORMModel):
    # Relationships
    coin: Coin | None = Field(default=None, exclude=True)
    finance_entity: FinanceEntity | None = Field(default=None, exclude=True)
    parents: list[SmartContractPermit] = Field(default_factory=list, exclude=True)
    price_schedule: PriceSchedule | None = Field(default=None, exclude=True)
    smart_contract_reservations: list[SmartContractReservation] = Field(default_factory=list, exclude=True)

    # Attributes
    cap_amount: Annotated[Decimal, DecimalWire()]
    expires_at: datetime
    nonce: int = Field(default=0)
    permit_nonce: int
    status: SmartContractPermitStatus = Field(default=SmartContractPermitStatus.active)

    # Foreign Keys
    smart_contract_id: UUID = Field(description="Foreign key for SmartContract.smart_contract_permits")
    smart_contract_permit_id: UUID | None = Field(
        default=None, description="Foreign key for SmartContractPermit.parents"
    )
    coin_id: UUID = Field(description="Foreign key for SmartContractPermit.coin")
    finance_entity_id: UUID = Field(description="Foreign key for SmartContractPermit.finance_entity")
    price_schedule_id: UUID = Field(description="Foreign key for SmartContractPermit.price_schedule")
