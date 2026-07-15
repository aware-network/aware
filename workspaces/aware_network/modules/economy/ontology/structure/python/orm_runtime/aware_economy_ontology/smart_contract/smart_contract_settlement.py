from __future__ import annotations

# Standard
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology
from aware_economy_ontology.smart_contract.smart_contract_settlement_enums import SmartContractSettlementStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology.coin.coin import Coin
    from aware_economy_ontology.finance.finance_entity import FinanceEntity
    from aware_economy_ontology.transaction.transaction import Transaction
    from aware_economy_ontology.wallet.wallet_public import WalletPublic


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

    async def set_status(self, status: SmartContractSettlementStatus) -> SmartContractSettlement:
        """
        Updates smart-contract settlement lifecycle status.

        Receipt: SmartContractSettlement status transition.
        """

        payload = {"status": status}
        result = await invoke_instance(orm_model=self, function_name="set_status", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SmartContractSettlement):
            return value
        return SmartContractSettlement.validate_invocation_value(value)

    async def create_transaction(
        self, nonce: int, description: str | None = None, idempotency_key: str | None = None
    ) -> Transaction:
        """
        Creates or reuses the canonical capital-transfer receipt for this settlement.

        Receipt: Transaction(status=created) referenced by this settlement.
        """

        payload = {"nonce": nonce, "description": description, "idempotency_key": idempotency_key}
        result = await invoke_instance(orm_model=self, function_name="create_transaction", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.transaction.transaction import Transaction

        if isinstance(value, Transaction):
            return value
        return Transaction.validate_invocation_value(value)

    @classmethod
    async def create_via_smart_contract_reservation(
        cls,
        smart_contract_reservation_id: UUID,
        payer_finance_entity_id: UUID,
        payer_wallet_public_id: UUID,
        receiver_finance_entity_id: UUID,
        receiver_wallet_public_id: UUID,
        coin_id: UUID,
        final_cost: Annotated[Decimal, DecimalWire()],
        status: SmartContractSettlementStatus = SmartContractSettlementStatus.prepared,
    ) -> SmartContractSettlement:
        """
        Creates a settlement receipt under a smart-contract reservation.

        Receipt: SmartContractSettlement(status=prepared).
        """

        payload = {
            "smart_contract_reservation_id": smart_contract_reservation_id,
            "payer_finance_entity_id": payer_finance_entity_id,
            "payer_wallet_public_id": payer_wallet_public_id,
            "receiver_finance_entity_id": receiver_finance_entity_id,
            "receiver_wallet_public_id": receiver_wallet_public_id,
            "coin_id": coin_id,
            "final_cost": final_cost,
            "status": status,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_smart_contract_reservation", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SmartContractSettlement):
            return value
        return SmartContractSettlement.validate_invocation_value(value)


class SmartContractSettlementSetStatusInput(BaseModel):
    status: SmartContractSettlementStatus


class SmartContractSettlementSetStatusOutput(BaseModel):
    value: SmartContractSettlement


class SmartContractSettlementCreateTransactionInput(BaseModel):
    nonce: int
    description: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)


class SmartContractSettlementCreateTransactionOutput(BaseModel):
    value: Transaction


class SmartContractSettlementCreateViaSmartContractReservationInput(BaseModel):
    smart_contract_reservation_id: UUID = Field(
        description="Foreign key for SmartContractReservation.smart_contract_settlements"
    )
    payer_finance_entity_id: UUID
    payer_wallet_public_id: UUID
    receiver_finance_entity_id: UUID
    receiver_wallet_public_id: UUID
    coin_id: UUID
    final_cost: Annotated[Decimal, DecimalWire()]
    status: SmartContractSettlementStatus = Field(default=SmartContractSettlementStatus.prepared)


class SmartContractSettlementCreateViaSmartContractReservationOutput(BaseModel):
    value: SmartContractSettlement


FUNCTIONS = {
    "SmartContractSettlement": {
        "set_status": {
            "canonical": {
                "name": "set_status",
                "description": "Updates smart-contract settlement lifecycle status.\n\nReceipt: SmartContractSettlement status transition.",
                "is_constructor": False,
            },
            "input": SmartContractSettlementSetStatusInput,
            "output": SmartContractSettlementSetStatusOutput,
        },
        "create_transaction": {
            "canonical": {
                "name": "create_transaction",
                "description": "Creates or reuses the canonical capital-transfer receipt for this settlement.\n\nReceipt: Transaction(status=created) referenced by this settlement.",
                "is_constructor": False,
            },
            "input": SmartContractSettlementCreateTransactionInput,
            "output": SmartContractSettlementCreateTransactionOutput,
        },
        "create_via_smart_contract_reservation": {
            "canonical": {
                "name": "create_via_smart_contract_reservation",
                "description": "Creates a settlement receipt under a smart-contract reservation.\n\nReceipt: SmartContractSettlement(status=prepared).",
                "is_constructor": True,
            },
            "input": SmartContractSettlementCreateViaSmartContractReservationInput,
            "output": SmartContractSettlementCreateViaSmartContractReservationOutput,
        },
    },
}

__all__ = [
    "SmartContractSettlement",
    "SmartContractSettlementSetStatusInput",
    "SmartContractSettlementSetStatusOutput",
    "SmartContractSettlementCreateTransactionInput",
    "SmartContractSettlementCreateTransactionOutput",
    "SmartContractSettlementCreateViaSmartContractReservationInput",
    "SmartContractSettlementCreateViaSmartContractReservationOutput",
    "FUNCTIONS",
]
