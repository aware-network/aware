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
from aware_economy_ontology_orm_models.smart_contract.smart_contract_reservation_enums import ReservationStatus

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.escrow.escrow import Escrow
    from aware_economy_ontology_orm_models.price.rate_snapshot import RateSnapshot
    from aware_economy_ontology_orm_models.smart_contract.smart_contract_settlement import SmartContractSettlement


class SmartContractReservation(ORMModel):
    # Relationships
    escrow: Escrow | None = Field(default=None, exclude=True)
    rate_snapshot: RateSnapshot | None = Field(default=None, exclude=True)
    smart_contract_settlements: list[SmartContractSettlement] = Field(default_factory=list, exclude=True)

    # Attributes
    args_hash: str
    deadline: datetime
    final_cost: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    max_cost: Annotated[Decimal, DecimalWire()]
    op_nonce: int
    reservation_signature: str | None = Field(default=None)
    status: ReservationStatus = Field(default=ReservationStatus.pending)

    # Foreign Keys
    smart_contract_permit_id: UUID = Field(
        description="Foreign key for SmartContractPermit.smart_contract_reservations"
    )
    escrow_id: UUID | None = Field(default=None, description="Foreign key for SmartContractReservation.escrow")
    rate_snapshot_id: UUID = Field(description="Foreign key for SmartContractReservation.rate_snapshot")
