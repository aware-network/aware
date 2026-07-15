from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_contract_economy_settlement import ServiceContractEconomySettlement

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_economy_ontology.coin.coin import Coin
from aware_economy_ontology.smart_contract.smart_contract_permit import (
    SmartContractPermit,
)
from aware_economy_ontology.wallet.wallet import Wallet
from aware_economy_ontology.wallet.wallet_public import WalletPublic
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.service.service_contract import ServiceContract
from aware_service_ontology.stable_ids import (
    stable_service_contract_economy_settlement_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_service_contract(
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

    # --- AWARE: LOGIC START build_via_service_contract
    if permit_nonce <= 0:
        raise RuntimeError("ServiceContractEconomySettlement.permit_nonce must be > 0")

    settlement_id = stable_service_contract_economy_settlement_id(service_contract_id=service_contract_id)
    session = current_handler_session()
    service_contract = session.imap_get(ServiceContract, service_contract_id)
    if service_contract is None:
        raise RuntimeError(
            "ServiceContractEconomySettlement requires committed ServiceContract: "
            f"service_contract_id={service_contract_id}"
        )

    permit = session.imap_get(SmartContractPermit, permit_id)
    if permit is not None:
        if permit.smart_contract_id != service_contract.smart_contract_id:
            raise RuntimeError("ServiceContractEconomySettlement permit smart_contract_id mismatch.")
        if permit.finance_entity_id != service_contract.consumer_finance_entity_id:
            raise RuntimeError(
                "ServiceContractEconomySettlement permit finance_entity_id must match "
                "ServiceContract.consumer_finance_entity_id."
            )
        if permit.permit_nonce != permit_nonce:
            raise RuntimeError(
                "ServiceContractEconomySettlement permit_nonce must match SmartContractPermit.permit_nonce."
            )
        if permit.coin_id != coin_id:
            raise RuntimeError("ServiceContractEconomySettlement coin_id must match SmartContractPermit.coin_id.")

    payer_wallet = session.imap_get(Wallet, payer_wallet_id)
    if payer_wallet is not None and payer_wallet.wallet_public_id != payer_wallet_public_id:
        raise RuntimeError(
            "ServiceContractEconomySettlement payer_wallet_public_id must match " "payer Wallet.wallet_public_id."
        )

    receiver_wallet = session.imap_get(Wallet, receiver_wallet_id)
    if receiver_wallet is not None and receiver_wallet.wallet_public_id != receiver_wallet_public_id:
        raise RuntimeError(
            "ServiceContractEconomySettlement receiver_wallet_public_id must match " "receiver Wallet.wallet_public_id."
        )

    _ = session.imap_get(WalletPublic, payer_wallet_public_id)
    _ = session.imap_get(WalletPublic, receiver_wallet_public_id)
    _ = session.imap_get(Coin, coin_id)

    existing = session.imap_get(ServiceContractEconomySettlement, settlement_id)
    if existing is not None:
        if (
            existing.service_contract_id != service_contract_id
            or existing.permit_id != permit_id
            or existing.permit_nonce != permit_nonce
            or existing.payer_wallet_id != payer_wallet_id
            or existing.payer_wallet_public_id != payer_wallet_public_id
            or existing.receiver_wallet_id != receiver_wallet_id
            or existing.receiver_wallet_public_id != receiver_wallet_public_id
            or existing.coin_id != coin_id
            or existing.deadline != deadline
        ):
            raise RuntimeError(
                "ServiceContractEconomySettlement payload mismatch for existing "
                f"settlement coordinates: service_contract_id={service_contract_id}"
            )
        service_contract.economy_settlement = existing
        return existing

    created = ServiceContractEconomySettlement(
        id=settlement_id,
        service_contract_id=service_contract_id,
        permit_id=permit_id,
        permit_nonce=permit_nonce,
        payer_wallet_id=payer_wallet_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_wallet_id=receiver_wallet_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
        deadline=deadline,
    )
    session.imap_add(created)
    service_contract.economy_settlement = created
    return created
    # --- AWARE: LOGIC END build_via_service_contract
