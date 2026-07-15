from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_economy_ontology_dto.transaction.transaction import Transaction
    from aware_economy_ontology_dto.wallet.wallet_balance import WalletBalance
    from aware_economy_ontology_dto.wallet.wallet_external_ingress_application import WalletExternalIngressApplication
    from aware_economy_ontology_dto.wallet.wallet_private import WalletPrivate
    from aware_economy_ontology_dto.wallet.wallet_public import WalletPublic


class Wallet(BaseModel):
    # Relationships
    wallet_balances: list[WalletBalance] = Field(default_factory=list)
    external_ingress_applications: list[WalletExternalIngressApplication] = Field(default_factory=list)
    wallet_private: WalletPrivate | None = Field(default=None)
    wallet_public: WalletPublic | None = Field(default=None)
    transactions: list[Transaction] = Field(default_factory=list)

    # Attributes
    private_key_encrypted: str
    public_key: str
