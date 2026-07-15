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
from aware_economy_ontology_dto.smart_contract.smart_contract_reservation_enums import ReservationStatus

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology_dto.escrow.escrow import Escrow
    from aware_economy_ontology_dto.price.rate_snapshot import RateSnapshot
    from aware_economy_ontology_dto.smart_contract.smart_contract_settlement import SmartContractSettlement


class SmartContractReservation(BaseModel):
    # Relationships
    escrow: Escrow | None = Field(default=None)
    rate_snapshot: RateSnapshot | None = Field(default=None)
    smart_contract_settlements: list[SmartContractSettlement] = Field(default_factory=list)

    # Attributes
    args_hash: str
    deadline: datetime
    final_cost: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    max_cost: Annotated[Decimal, DecimalWire()]
    op_nonce: int
    reservation_signature: str | None = Field(default=None)
    status: ReservationStatus = Field(default=ReservationStatus.pending)
