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
from aware_economy_ontology_orm_models.smart_contract.smart_contract_settlement_enums import (
    SmartContractSettlementStatus,
)

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.coin.coin import Coin
    from aware_economy_ontology_orm_models.finance.finance_entity import FinanceEntity
    from aware_economy_ontology_orm_models.transaction.transaction import Transaction
    from aware_economy_ontology_orm_models.wallet.wallet_public import WalletPublic


class SmartContractSettlement(ORMModel):
    # Relationships
    coin: Coin | None = Field(default=None, exclude=True)
    payer_finance_entity: FinanceEntity | None = Field(default=None, exclude=True)
    payer_wallet_public: WalletPublic | None = Field(default=None, exclude=True)
    receiver_finance_entity: FinanceEntity | None = Field(default=None, exclude=True)
    receiver_wallet_public: WalletPublic | None = Field(default=None, exclude=True)
    transactions: list[Transaction] = Field(default_factory=list, exclude=True)

    # Attributes
    final_cost: Annotated[Decimal, DecimalWire()]
    status: SmartContractSettlementStatus = Field(default=SmartContractSettlementStatus.prepared)

    # Foreign Keys
    smart_contract_reservation_id: UUID = Field(
        description="Foreign key for SmartContractReservation.smart_contract_settlements"
    )
    coin_id: UUID = Field(description="Foreign key for SmartContractSettlement.coin")
    payer_finance_entity_id: UUID = Field(description="Foreign key for SmartContractSettlement.payer_finance_entity")
    payer_wallet_public_id: UUID = Field(description="Foreign key for SmartContractSettlement.payer_wallet_public")
    receiver_finance_entity_id: UUID = Field(
        description="Foreign key for SmartContractSettlement.receiver_finance_entity"
    )
    receiver_wallet_public_id: UUID = Field(
        description="Foreign key for SmartContractSettlement.receiver_wallet_public"
    )
