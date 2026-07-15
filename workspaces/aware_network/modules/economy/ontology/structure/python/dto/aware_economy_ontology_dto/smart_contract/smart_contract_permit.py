from __future__ import annotations

# Standard
from datetime import datetime
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology Dto
from aware_economy_ontology_dto.smart_contract.smart_contract_permit_enums import SmartContractPermitStatus

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology_dto.coin.coin import Coin
    from aware_economy_ontology_dto.finance.finance_entity import FinanceEntity
    from aware_economy_ontology_dto.price.price_schedule import PriceSchedule
    from aware_economy_ontology_dto.smart_contract.smart_contract_reservation import SmartContractReservation


class SmartContractPermit(BaseModel):
    # Relationships
    coin: Coin | None = Field(default=None)
    finance_entity: FinanceEntity | None = Field(default=None)
    parents: list[SmartContractPermit] = Field(default_factory=list)
    price_schedule: PriceSchedule | None = Field(default=None)
    smart_contract_reservations: list[SmartContractReservation] = Field(default_factory=list)

    # Attributes
    cap_amount: Annotated[Decimal, DecimalWire()]
    expires_at: datetime
    nonce: int = Field(default=0)
    permit_nonce: int
    status: SmartContractPermitStatus = Field(default=SmartContractPermitStatus.active)
