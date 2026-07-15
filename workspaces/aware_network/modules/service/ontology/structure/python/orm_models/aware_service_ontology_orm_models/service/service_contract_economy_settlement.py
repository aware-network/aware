from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.coin.coin import Coin
    from aware_economy_ontology_orm_models.smart_contract.smart_contract_permit import SmartContractPermit
    from aware_economy_ontology_orm_models.wallet.wallet import Wallet
    from aware_economy_ontology_orm_models.wallet.wallet_public import WalletPublic


class ServiceContractEconomySettlement(ORMModel):
    # Relationships
    coin: Coin | None = Field(default=None, exclude=True)
    payer_wallet: Wallet | None = Field(default=None, exclude=True)
    payer_wallet_public: WalletPublic | None = Field(default=None, exclude=True)
    permit: SmartContractPermit | None = Field(default=None, exclude=True)
    receiver_wallet: Wallet | None = Field(default=None, exclude=True)
    receiver_wallet_public: WalletPublic | None = Field(default=None, exclude=True)

    # Attributes
    deadline: datetime
    permit_nonce: int

    # Foreign Keys
    service_contract_id: UUID | None = Field(
        default=None, description="Foreign key for ServiceContract.economy_settlement"
    )
    coin_id: UUID = Field(description="Foreign key for ServiceContractEconomySettlement.coin")
    payer_wallet_id: UUID = Field(description="Foreign key for ServiceContractEconomySettlement.payer_wallet")
    payer_wallet_public_id: UUID = Field(
        description="Foreign key for ServiceContractEconomySettlement.payer_wallet_public"
    )
    permit_id: UUID = Field(description="Foreign key for ServiceContractEconomySettlement.permit")
    receiver_wallet_id: UUID = Field(description="Foreign key for ServiceContractEconomySettlement.receiver_wallet")
    receiver_wallet_public_id: UUID = Field(
        description="Foreign key for ServiceContractEconomySettlement.receiver_wallet_public"
    )
