from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_economy_ontology.coin.coin import Coin
    from aware_economy_ontology.smart_contract.smart_contract_permit import SmartContractPermit
    from aware_economy_ontology.wallet.wallet import Wallet
    from aware_economy_ontology.wallet.wallet_public import WalletPublic


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

    @classmethod
    async def build_via_service_contract(
        cls,
        service_contract_id: UUID,
        permit_id: UUID,
        permit_nonce: int,
        payer_wallet_id: UUID,
        payer_wallet_public_id: UUID,
        receiver_wallet_id: UUID,
        receiver_wallet_public_id: UUID,
        coin_id: UUID,
        deadline: datetime,
    ) -> ServiceContractEconomySettlement:
        """
        Creates the typed Economy settlement coordinate state for one ServiceContract.

        Contract:
        - Parent ServiceContract scope is propagated by constructor lowering.
        - Stable identity is one Economy settlement coordinate object per ServiceContract.
        - The object names Economy permit/wallet/coin coordinates; it does not mutate money.
        - Economy owns per-reservation operation nonce allocation.
        """

        payload = {
            "service_contract_id": service_contract_id,
            "permit_id": permit_id,
            "permit_nonce": permit_nonce,
            "payer_wallet_id": payer_wallet_id,
            "payer_wallet_public_id": payer_wallet_public_id,
            "receiver_wallet_id": receiver_wallet_id,
            "receiver_wallet_public_id": receiver_wallet_public_id,
            "coin_id": coin_id,
            "deadline": deadline,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_service_contract", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceContractEconomySettlement):
            return value
        return ServiceContractEconomySettlement.validate_invocation_value(value)


class ServiceContractEconomySettlementBuildViaServiceContractInput(BaseModel):
    service_contract_id: UUID = Field(description="Foreign key for ServiceContract.economy_settlement")
    permit_id: UUID
    permit_nonce: int
    payer_wallet_id: UUID
    payer_wallet_public_id: UUID
    receiver_wallet_id: UUID
    receiver_wallet_public_id: UUID
    coin_id: UUID
    deadline: datetime


class ServiceContractEconomySettlementBuildViaServiceContractOutput(BaseModel):
    value: ServiceContractEconomySettlement


FUNCTIONS = {
    "ServiceContractEconomySettlement": {
        "build_via_service_contract": {
            "canonical": {
                "name": "build_via_service_contract",
                "description": "Creates the typed Economy settlement coordinate state for one ServiceContract.\n\nContract:\n- Parent ServiceContract scope is propagated by constructor lowering.\n- Stable identity is one Economy settlement coordinate object per ServiceContract.\n- The object names Economy permit/wallet/coin coordinates; it does not mutate money.\n- Economy owns per-reservation operation nonce allocation.",
                "is_constructor": True,
            },
            "input": ServiceContractEconomySettlementBuildViaServiceContractInput,
            "output": ServiceContractEconomySettlementBuildViaServiceContractOutput,
        },
    },
}

__all__ = [
    "ServiceContractEconomySettlement",
    "ServiceContractEconomySettlementBuildViaServiceContractInput",
    "ServiceContractEconomySettlementBuildViaServiceContractOutput",
    "FUNCTIONS",
]
