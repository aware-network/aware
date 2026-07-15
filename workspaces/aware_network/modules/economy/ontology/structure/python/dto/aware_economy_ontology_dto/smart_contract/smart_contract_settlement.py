from __future__ import annotations

# Standard
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology Dto
from aware_economy_ontology_dto.smart_contract.smart_contract_settlement_enums import SmartContractSettlementStatus

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology_dto.coin.coin import Coin
    from aware_economy_ontology_dto.finance.finance_entity import FinanceEntity
    from aware_economy_ontology_dto.transaction.transaction import Transaction
    from aware_economy_ontology_dto.wallet.wallet_public import WalletPublic


class SmartContractSettlement(BaseModel):
    # Relationships
    coin: Coin | None = Field(default=None)
    payer_finance_entity: FinanceEntity | None = Field(default=None)
    payer_wallet_public: WalletPublic | None = Field(default=None)
    receiver_finance_entity: FinanceEntity | None = Field(default=None)
    receiver_wallet_public: WalletPublic | None = Field(default=None)
    transactions: list[Transaction] = Field(default_factory=list)

    # Attributes
    final_cost: Annotated[Decimal, DecimalWire()]
    status: SmartContractSettlementStatus = Field(default=SmartContractSettlementStatus.prepared)
