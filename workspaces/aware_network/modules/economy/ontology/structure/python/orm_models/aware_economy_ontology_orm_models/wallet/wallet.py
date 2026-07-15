from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.transaction.transaction import Transaction
    from aware_economy_ontology_orm_models.wallet.wallet_balance import WalletBalance
    from aware_economy_ontology_orm_models.wallet.wallet_external_ingress_application import (
        WalletExternalIngressApplication,
    )
    from aware_economy_ontology_orm_models.wallet.wallet_private import WalletPrivate
    from aware_economy_ontology_orm_models.wallet.wallet_public import WalletPublic


class Wallet(ORMModel):
    # Relationships
    wallet_balances: list[WalletBalance] = Field(default_factory=list, exclude=True)
    external_ingress_applications: list[WalletExternalIngressApplication] = Field(default_factory=list, exclude=True)
    wallet_private: WalletPrivate | None = Field(default=None, exclude=True)
    wallet_public: WalletPublic | None = Field(default=None, exclude=True)
    transactions: list[Transaction] = Field(default_factory=list, exclude=True)

    # Attributes
    private_key_encrypted: str
    public_key: str

    # Foreign Keys
    wallet_private_id: UUID | None = Field(default=None, description="Foreign key for Wallet.wallet_private")
    wallet_public_id: UUID | None = Field(default=None, description="Foreign key for Wallet.wallet_public")
