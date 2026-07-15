from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.escrow.escrow import Escrow


class WalletPublic(ORMModel):
    # Relationships
    escrows: list[Escrow] = Field(default_factory=list, exclude=True)

    # Attributes
    address: str
    nonce_counter: int = Field(default=0)
    public_key: str
