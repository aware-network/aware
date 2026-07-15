from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_economy_ontology_dto.coin.coin import Coin
    from aware_economy_ontology_dto.smart_contract.smart_contract_permit import SmartContractPermit
    from aware_economy_ontology_dto.wallet.wallet import Wallet
    from aware_economy_ontology_dto.wallet.wallet_public import WalletPublic


class ServiceContractEconomySettlement(BaseModel):
    # Relationships
    coin: Coin | None = Field(default=None)
    payer_wallet: Wallet | None = Field(default=None)
    payer_wallet_public: WalletPublic | None = Field(default=None)
    permit: SmartContractPermit | None = Field(default=None)
    receiver_wallet: Wallet | None = Field(default=None)
    receiver_wallet_public: WalletPublic | None = Field(default=None)

    # Attributes
    deadline: datetime
    permit_nonce: int
