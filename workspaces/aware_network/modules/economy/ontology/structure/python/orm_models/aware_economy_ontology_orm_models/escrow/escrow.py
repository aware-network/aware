from __future__ import annotations

# Standard
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)
from uuid import UUID

# Third-party
from pydantic import Field

# Economy Ontology Orm Models
from aware_economy_ontology_orm_models.escrow.escrow_enums import EscrowStatus

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.coin.coin import Coin


class Escrow(ORMModel):
    # Relationships
    coin: Coin | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    escrow_hash: str
    locked_amount: Annotated[Decimal, DecimalWire()]
    op_nonce: int
    signature: str
    smart_contract_reservation_id: UUID
    status: EscrowStatus = Field(default=EscrowStatus.locked)

    # Foreign Keys
    wallet_public_id: UUID = Field(description="Foreign key for WalletPublic.escrows")
    coin_id: UUID = Field(description="Foreign key for Escrow.coin")
