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

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology.transaction.transaction import Transaction
    from aware_economy_ontology.wallet.wallet_balance import WalletBalance
    from aware_economy_ontology.wallet.wallet_external_ingress_application import WalletExternalIngressApplication
    from aware_economy_ontology.wallet.wallet_private import WalletPrivate
    from aware_economy_ontology.wallet.wallet_public import WalletPublic


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

    @classmethod
    async def build(cls, address: str, public_key: str, private_key_encrypted: str) -> Wallet:
        """
        Creates a wallet + custody/key records in a single commit (wallet lane bootstrap).

        Receipt: Wallet + WalletPublic + WalletPrivate linked together.

        Fail-closed:
        - private_key_encrypted must be an opaque custody handle or encrypted key reference.
        - production-visible `dev:` private-key material is rejected.
        """

        payload = {"address": address, "public_key": public_key, "private_key_encrypted": private_key_encrypted}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Wallet):
            return value
        return Wallet.validate_invocation_value(value)

    async def initiate_transaction(
        self,
        target_wallet_public_id: UUID,
        coin_id: UUID,
        coin_amount: Annotated[Decimal, DecimalWire()],
        nonce: int,
        description: str | None = None,
        idempotency_key: str | None = None,
    ) -> Transaction:
        """
        Creates and signs a transaction from this wallet.

        Receipt: Transaction + Wallet.transactions link (commit-backed).
        """

        payload = {
            "target_wallet_public_id": target_wallet_public_id,
            "coin_id": coin_id,
            "coin_amount": coin_amount,
            "nonce": nonce,
            "description": description,
            "idempotency_key": idempotency_key,
        }
        result = await invoke_instance(orm_model=self, function_name="initiate_transaction", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.transaction.transaction import Transaction

        if isinstance(value, Transaction):
            return value
        return Transaction.validate_invocation_value(value)

    async def set_coin_balance(self, coin_id: UUID, balance: Annotated[Decimal, DecimalWire()]) -> WalletBalance:
        """
        Sets absolute balance for a coin in this wallet.

        Receipt: WalletBalance(updated/created) linked under Wallet.wallet_balances.
        """

        payload = {"coin_id": coin_id, "balance": balance}
        result = await invoke_instance(orm_model=self, function_name="set_coin_balance", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.wallet.wallet_balance import WalletBalance

        if isinstance(value, WalletBalance):
            return value
        return WalletBalance.validate_invocation_value(value)

    async def apply_coin_delta(self, coin_id: UUID, delta: Annotated[Decimal, DecimalWire()]) -> WalletBalance:
        """
        Applies a signed delta to this wallet coin balance.

        Receipt: WalletBalance(updated/created) linked under Wallet.wallet_balances.

        Fail-closed:
        - Rejects zero delta.
        - Rejects negative resulting balance.
        """

        payload = {"coin_id": coin_id, "delta": delta}
        result = await invoke_instance(orm_model=self, function_name="apply_coin_delta", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.wallet.wallet_balance import WalletBalance

        if isinstance(value, WalletBalance):
            return value
        return WalletBalance.validate_invocation_value(value)

    async def apply_external_ingress(
        self, transaction_id: UUID, coin_id: UUID, amount: Annotated[Decimal, DecimalWire()]
    ) -> WalletExternalIngressApplication:
        """
        Applies one verified external-ingress Transaction to this wallet exactly once.

        Receipt: contained WalletExternalIngressApplication plus updated WalletBalance.
        """

        payload = {"transaction_id": transaction_id, "coin_id": coin_id, "amount": amount}
        result = await invoke_instance(orm_model=self, function_name="apply_external_ingress", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.wallet.wallet_external_ingress_application import WalletExternalIngressApplication

        if isinstance(value, WalletExternalIngressApplication):
            return value
        return WalletExternalIngressApplication.validate_invocation_value(value)

    async def reconcile_coin_balance(
        self,
        coin_id: UUID,
        expected_balance: Annotated[Decimal, DecimalWire()],
        new_balance: Annotated[Decimal, DecimalWire()],
    ) -> WalletBalance:
        """
        Applies an idempotent absolute balance transition for a coin.

        Receipt: WalletBalance(updated/created) linked under Wallet.wallet_balances.

        Fail-closed:
        - Rejects negative `new_balance`.
        - Allows no-op when current balance is already `new_balance`.
        - Otherwise requires current balance to match `expected_balance`.
        """

        payload = {"coin_id": coin_id, "expected_balance": expected_balance, "new_balance": new_balance}
        result = await invoke_instance(orm_model=self, function_name="reconcile_coin_balance", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.wallet.wallet_balance import WalletBalance

        if isinstance(value, WalletBalance):
            return value
        return WalletBalance.validate_invocation_value(value)

    async def reserve_coin_hold(self, coin_id: UUID, amount: Annotated[Decimal, DecimalWire()]) -> WalletBalance:
        """
        Moves available wallet capital into held capital for a reservation.

        Receipt: WalletBalance(held_balance increased, available_balance reduced).

        Fail-closed:
        - Rejects non-positive amount.
        - Rejects amount greater than current available balance.
        """

        payload = {"coin_id": coin_id, "amount": amount}
        result = await invoke_instance(orm_model=self, function_name="reserve_coin_hold", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.wallet.wallet_balance import WalletBalance

        if isinstance(value, WalletBalance):
            return value
        return WalletBalance.validate_invocation_value(value)

    async def release_coin_hold(self, coin_id: UUID, amount: Annotated[Decimal, DecimalWire()]) -> WalletBalance:
        """
        Releases held wallet capital back to available balance.

        Receipt: WalletBalance(held_balance reduced, total balance unchanged).

        Fail-closed:
        - Rejects non-positive amount.
        - Rejects amount greater than current held balance.
        """

        payload = {"coin_id": coin_id, "amount": amount}
        result = await invoke_instance(orm_model=self, function_name="release_coin_hold", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.wallet.wallet_balance import WalletBalance

        if isinstance(value, WalletBalance):
            return value
        return WalletBalance.validate_invocation_value(value)

    async def settle_coin_hold(
        self,
        coin_id: UUID,
        reserved_amount: Annotated[Decimal, DecimalWire()],
        final_cost: Annotated[Decimal, DecimalWire()],
    ) -> WalletBalance:
        """
        Consumes a reservation hold and debits the settled final cost from total balance.

        Receipt: WalletBalance(held_balance reduced by reserved_amount, balance reduced by final_cost).

        Fail-closed:
        - Rejects non-positive reserved_amount.
        - Rejects final_cost greater than reserved_amount.
        - Rejects reserved_amount greater than current held balance.
        """

        payload = {"coin_id": coin_id, "reserved_amount": reserved_amount, "final_cost": final_cost}
        result = await invoke_instance(orm_model=self, function_name="settle_coin_hold", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.wallet.wallet_balance import WalletBalance

        if isinstance(value, WalletBalance):
            return value
        return WalletBalance.validate_invocation_value(value)


class WalletBuildInput(BaseModel):
    address: str
    public_key: str
    private_key_encrypted: str


class WalletBuildOutput(BaseModel):
    value: Wallet


class WalletInitiateTransactionInput(BaseModel):
    target_wallet_public_id: UUID
    coin_id: UUID
    coin_amount: Annotated[Decimal, DecimalWire()]
    nonce: int
    description: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)


class WalletInitiateTransactionOutput(BaseModel):
    value: Transaction


class WalletSetCoinBalanceInput(BaseModel):
    coin_id: UUID
    balance: Annotated[Decimal, DecimalWire()]


class WalletSetCoinBalanceOutput(BaseModel):
    value: WalletBalance


class WalletApplyCoinDeltaInput(BaseModel):
    coin_id: UUID
    delta: Annotated[Decimal, DecimalWire()]


class WalletApplyCoinDeltaOutput(BaseModel):
    value: WalletBalance


class WalletApplyExternalIngressInput(BaseModel):
    transaction_id: UUID
    coin_id: UUID
    amount: Annotated[Decimal, DecimalWire()]


class WalletApplyExternalIngressOutput(BaseModel):
    value: WalletExternalIngressApplication


class WalletReconcileCoinBalanceInput(BaseModel):
    coin_id: UUID
    expected_balance: Annotated[Decimal, DecimalWire()]
    new_balance: Annotated[Decimal, DecimalWire()]


class WalletReconcileCoinBalanceOutput(BaseModel):
    value: WalletBalance


class WalletReserveCoinHoldInput(BaseModel):
    coin_id: UUID
    amount: Annotated[Decimal, DecimalWire()]


class WalletReserveCoinHoldOutput(BaseModel):
    value: WalletBalance


class WalletReleaseCoinHoldInput(BaseModel):
    coin_id: UUID
    amount: Annotated[Decimal, DecimalWire()]


class WalletReleaseCoinHoldOutput(BaseModel):
    value: WalletBalance


class WalletSettleCoinHoldInput(BaseModel):
    coin_id: UUID
    reserved_amount: Annotated[Decimal, DecimalWire()]
    final_cost: Annotated[Decimal, DecimalWire()]


class WalletSettleCoinHoldOutput(BaseModel):
    value: WalletBalance


FUNCTIONS = {
    "Wallet": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Creates a wallet + custody/key records in a single commit (wallet lane bootstrap).\n\nReceipt: Wallet + WalletPublic + WalletPrivate linked together.\n\nFail-closed:\n- private_key_encrypted must be an opaque custody handle or encrypted key reference.\n- production-visible `dev:` private-key material is rejected.",
                "is_constructor": True,
            },
            "input": WalletBuildInput,
            "output": WalletBuildOutput,
        },
        "initiate_transaction": {
            "canonical": {
                "name": "initiate_transaction",
                "description": "Creates and signs a transaction from this wallet.\n\nReceipt: Transaction + Wallet.transactions link (commit-backed).",
                "is_constructor": False,
            },
            "input": WalletInitiateTransactionInput,
            "output": WalletInitiateTransactionOutput,
        },
        "set_coin_balance": {
            "canonical": {
                "name": "set_coin_balance",
                "description": "Sets absolute balance for a coin in this wallet.\n\nReceipt: WalletBalance(updated/created) linked under Wallet.wallet_balances.",
                "is_constructor": False,
            },
            "input": WalletSetCoinBalanceInput,
            "output": WalletSetCoinBalanceOutput,
        },
        "apply_coin_delta": {
            "canonical": {
                "name": "apply_coin_delta",
                "description": "Applies a signed delta to this wallet coin balance.\n\nReceipt: WalletBalance(updated/created) linked under Wallet.wallet_balances.\n\nFail-closed:\n- Rejects zero delta.\n- Rejects negative resulting balance.",
                "is_constructor": False,
            },
            "input": WalletApplyCoinDeltaInput,
            "output": WalletApplyCoinDeltaOutput,
        },
        "apply_external_ingress": {
            "canonical": {
                "name": "apply_external_ingress",
                "description": "Applies one verified external-ingress Transaction to this wallet exactly once.\n\nReceipt: contained WalletExternalIngressApplication plus updated WalletBalance.",
                "is_constructor": False,
            },
            "input": WalletApplyExternalIngressInput,
            "output": WalletApplyExternalIngressOutput,
        },
        "reconcile_coin_balance": {
            "canonical": {
                "name": "reconcile_coin_balance",
                "description": "Applies an idempotent absolute balance transition for a coin.\n\nReceipt: WalletBalance(updated/created) linked under Wallet.wallet_balances.\n\nFail-closed:\n- Rejects negative `new_balance`.\n- Allows no-op when current balance is already `new_balance`.\n- Otherwise requires current balance to match `expected_balance`.",
                "is_constructor": False,
            },
            "input": WalletReconcileCoinBalanceInput,
            "output": WalletReconcileCoinBalanceOutput,
        },
        "reserve_coin_hold": {
            "canonical": {
                "name": "reserve_coin_hold",
                "description": "Moves available wallet capital into held capital for a reservation.\n\nReceipt: WalletBalance(held_balance increased, available_balance reduced).\n\nFail-closed:\n- Rejects non-positive amount.\n- Rejects amount greater than current available balance.",
                "is_constructor": False,
            },
            "input": WalletReserveCoinHoldInput,
            "output": WalletReserveCoinHoldOutput,
        },
        "release_coin_hold": {
            "canonical": {
                "name": "release_coin_hold",
                "description": "Releases held wallet capital back to available balance.\n\nReceipt: WalletBalance(held_balance reduced, total balance unchanged).\n\nFail-closed:\n- Rejects non-positive amount.\n- Rejects amount greater than current held balance.",
                "is_constructor": False,
            },
            "input": WalletReleaseCoinHoldInput,
            "output": WalletReleaseCoinHoldOutput,
        },
        "settle_coin_hold": {
            "canonical": {
                "name": "settle_coin_hold",
                "description": "Consumes a reservation hold and debits the settled final cost from total balance.\n\nReceipt: WalletBalance(held_balance reduced by reserved_amount, balance reduced by final_cost).\n\nFail-closed:\n- Rejects non-positive reserved_amount.\n- Rejects final_cost greater than reserved_amount.\n- Rejects reserved_amount greater than current held balance.",
                "is_constructor": False,
            },
            "input": WalletSettleCoinHoldInput,
            "output": WalletSettleCoinHoldOutput,
        },
    },
}

__all__ = [
    "Wallet",
    "WalletBuildInput",
    "WalletBuildOutput",
    "WalletInitiateTransactionInput",
    "WalletInitiateTransactionOutput",
    "WalletSetCoinBalanceInput",
    "WalletSetCoinBalanceOutput",
    "WalletApplyCoinDeltaInput",
    "WalletApplyCoinDeltaOutput",
    "WalletApplyExternalIngressInput",
    "WalletApplyExternalIngressOutput",
    "WalletReconcileCoinBalanceInput",
    "WalletReconcileCoinBalanceOutput",
    "WalletReserveCoinHoldInput",
    "WalletReserveCoinHoldOutput",
    "WalletReleaseCoinHoldInput",
    "WalletReleaseCoinHoldOutput",
    "WalletSettleCoinHoldInput",
    "WalletSettleCoinHoldOutput",
    "FUNCTIONS",
]
