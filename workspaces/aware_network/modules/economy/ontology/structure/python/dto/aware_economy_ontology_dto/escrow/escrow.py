from __future__ import annotations

# Standard
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology Dto
from aware_economy_ontology_dto.escrow.escrow_enums import EscrowStatus

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology_dto.coin.coin import Coin


class Escrow(BaseModel):
    # Relationships
    coin: Coin | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
    escrow_hash: str
    locked_amount: Annotated[Decimal, DecimalWire()]
    op_nonce: int
    signature: str
    smart_contract_reservation_id: UUID
    status: EscrowStatus = Field(default=EscrowStatus.locked)
