from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.wallet.wallet import Wallet
    from aware_identity_ontology_orm_models.identity.identity import Identity


class FinanceEntity(ORMModel):
    # Relationships
    identity: Identity | None = Field(default=None, exclude=True)
    wallet: Wallet | None = Field(default=None, exclude=True)

    # Attributes
    role_key: str = Field(default="primary")

    # Foreign Keys
    identity_id: UUID = Field(description="Foreign key for FinanceEntity.identity")
    wallet_id: UUID | None = Field(default=None, description="Foreign key for FinanceEntity.wallet")
