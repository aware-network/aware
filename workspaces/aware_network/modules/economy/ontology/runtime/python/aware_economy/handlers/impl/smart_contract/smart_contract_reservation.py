from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

# Economy Ontology
from aware_economy_ontology.smart_contract.smart_contract_reservation_enums import ReservationStatus
from aware_economy_ontology.escrow.escrow import Escrow
from aware_economy_ontology.smart_contract.smart_contract_reservation import SmartContractReservation
from aware_economy_ontology.smart_contract.smart_contract_settlement import SmartContractSettlement

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Economy Ontology
from aware_economy_ontology.stable_ids import stable_smart_contract_settlement_id
from aware_economy_ontology.smart_contract.smart_contract_settlement_enums import (
    SmartContractSettlementStatus,
)
from aware_economy.capital_amount import (
    amount_equal,
    non_negative_amount,
    positive_amount,
)
from aware_economy.ontology.materialization import (
    materialize_smart_contract_reservation,
)

# --- AWARE: USER_IMPORTS END


async def set_status(
    smart_contract_reservation: SmartContractReservation,
    status: ReservationStatus,
    final_cost: Annotated[Decimal, DecimalWire()] | None = None,
) -> SmartContractReservation:
    """
    Updates reservation lifecycle status (and optional final cost on settlement paths).

    Receipt: SmartContractReservation status/final_cost transition.
    """

    # --- AWARE: LOGIC START set_status
    current = smart_contract_reservation.status
    if final_cost is not None:
        final_cost = non_negative_amount(
            final_cost,
            field_name="reservation final_cost",
        )

    terminal = {
        ReservationStatus.settled,
        ReservationStatus.cancelled,
        ReservationStatus.expired,
    }
    if current in terminal and status != current:
        raise ValueError(f"reservation status is terminal and cannot transition: {current} -> {status}")

    if status == ReservationStatus.settled:
        if final_cost is None and smart_contract_reservation.final_cost is None:
            raise ValueError("reservation.set_status(settled) requires final_cost when unset")

    if final_cost is not None:
        smart_contract_reservation.final_cost = final_cost
    smart_contract_reservation.status = status
    return smart_contract_reservation
    # --- AWARE: LOGIC END set_status


async def prepare_settlement(
    smart_contract_reservation: SmartContractReservation,
    payer_finance_entity_id: UUID,
    payer_wallet_public_id: UUID,
    receiver_finance_entity_id: UUID,
    receiver_wallet_public_id: UUID,
    coin_id: UUID,
    final_cost: Annotated[Decimal, DecimalWire()],
) -> SmartContractSettlement:
    """
    Creates or reuses the deterministic settlement receipt under this reservation.

    Receipt: SmartContractSettlement(status=prepared) linked under this reservation.
    """

    # --- AWARE: LOGIC START prepare_settlement
    final_cost = non_negative_amount(
        final_cost,
        field_name="reservation final_cost",
    )

    settlement_id = stable_smart_contract_settlement_id(
        smart_contract_reservation_id=smart_contract_reservation.id,
    )
    for existing in smart_contract_reservation.smart_contract_settlements:
        if str(existing.id) != str(settlement_id):
            continue
        if not amount_equal(existing.final_cost, final_cost):
            raise ValueError(
                "reservation.prepare_settlement final_cost mismatch for existing settlement: "
                f"existing={existing.final_cost} requested={final_cost}"
            )
        return existing

    settlement = await SmartContractSettlement.create_via_smart_contract_reservation(
        smart_contract_reservation_id=smart_contract_reservation.id,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
        final_cost=final_cost,
        status=SmartContractSettlementStatus.prepared,
    )
    smart_contract_reservation.smart_contract_settlements.append(settlement)
    return settlement
    # --- AWARE: LOGIC END prepare_settlement


async def create_via_smart_contract_permit(
    smart_contract_permit_id: UUID,
    op_nonce: int,
    args_hash: str,
    max_cost: Annotated[Decimal, DecimalWire()],
    rate_snapshot_id: UUID,
    deadline: datetime,
    reservation_signature: str | None = None,
    escrow: Escrow | None = None,
    status: ReservationStatus = ReservationStatus.pending,
) -> SmartContractReservation:
    """
    Creates a reservation under a permit.

    Receipt: SmartContractReservation(status=pending) linked to permit (+ optional escrow).
    """

    # --- AWARE: LOGIC START create_via_smart_contract_permit
    max_cost = positive_amount(max_cost, field_name="reservation max_cost")
    return materialize_smart_contract_reservation(
        smart_contract_permit_id=smart_contract_permit_id,
        op_nonce=op_nonce,
        args_hash=args_hash,
        max_cost=max_cost,
        rate_snapshot_id=rate_snapshot_id,
        deadline=deadline,
        reservation_signature=reservation_signature,
        escrow=escrow,
        status=status,
    )
    # --- AWARE: LOGIC END create_via_smart_contract_permit
