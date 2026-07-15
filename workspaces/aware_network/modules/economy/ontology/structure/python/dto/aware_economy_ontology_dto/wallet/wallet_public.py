from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_economy_ontology_dto.escrow.escrow import Escrow


class WalletPublic(BaseModel):
    # Relationships
    escrows: list[Escrow] = Field(default_factory=list)

    # Attributes
    address: str
    nonce_counter: int = Field(default=0)
    public_key: str
