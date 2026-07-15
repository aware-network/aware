from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

# Economy Ontology
from aware_economy_ontology.smart_contract.smart_contract_permit import SmartContractPermit
from aware_economy_ontology.smart_contract.smart_contract_reservation import SmartContractReservation

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Economy Ontology
from aware_economy_ontology.escrow.escrow import Escrow
from aware_economy_ontology.smart_contract.smart_contract_permit_enums import (
    SmartContractPermitStatus,
)
from aware_economy_ontology.smart_contract.smart_contract_reservation_enums import (
    ReservationStatus,
)

# Economy Ontology
from aware_economy_ontology.stable_ids import (
    stable_escrow_id,
    stable_smart_contract_reservation_id,
)
from aware_economy.canonical.price import (
    resolve_rate_snapshot_quote_via_permit,
)
from aware_economy.capital_amount import positive_amount
from aware_economy.ontology.materialization import (
    materialize_smart_contract_permit,
)

# --- AWARE: USER_IMPORTS END


async def note_operation(smart_contract_permit: SmartContractPermit, op_nonce: int) -> SmartContractPermit:
    """
    Advances permit operation nonce monotonically after a successful reservation.

    Receipt: SmartContractPermit.nonce updated to `op_nonce`.
    """

    # --- AWARE: LOGIC START note_operation
    if op_nonce <= 0:
        raise ValueError("smart_contract_permit.note_operation requires op_nonce > 0")

    current_nonce = int(getattr(smart_contract_permit, "nonce", 0))
    if op_nonce == current_nonce:
        return smart_contract_permit
    if op_nonce != current_nonce + 1:
        raise ValueError(
            "smart_contract_permit.note_operation requires contiguous nonce progression: "
            f"current={current_nonce} requested={op_nonce}"
        )

    smart_contract_permit.nonce = op_nonce
    return smart_contract_permit
    # --- AWARE: LOGIC END note_operation


async def revoke(smart_contract_permit: SmartContractPermit) -> SmartContractPermit:
    """
    Revokes this permit so no new operation reservation may consume its cap.

    Receipt: SmartContractPermit.status is revoked; repeated revocation is idempotent.
    """

    # --- AWARE: LOGIC START revoke
    if smart_contract_permit.status == SmartContractPermitStatus.revoked:
        return smart_contract_permit
    smart_contract_permit.status = SmartContractPermitStatus.revoked
    return smart_contract_permit
    # --- AWARE: LOGIC END revoke


async def reserve_operation(
    smart_contract_permit: SmartContractPermit,
    payer_wallet_public_id: UUID,
    op_nonce: int,
    args_hash: str,
    max_cost: Annotated[Decimal, DecimalWire()],
    rate_snapshot_id: UUID,
    deadline: datetime,
    coin_id: UUID,
) -> SmartContractReservation:
    """
    Creates a reservation + escrow under this permit and links it canonically.

    Receipt: SmartContractReservation(status=pending) linked under this permit with deterministic escrow
    id.
    """

    # --- AWARE: LOGIC START reserve_operation
    if op_nonce <= 0:
        raise ValueError("smart_contract_permit.reserve_operation requires op_nonce > 0")
    max_cost = positive_amount(max_cost, field_name="reservation max_cost")
    if not (args_hash or "").strip():
        raise ValueError("smart_contract_permit.reserve_operation requires args_hash")
    if smart_contract_permit.status != SmartContractPermitStatus.active:
        raise ValueError(f"permit is not active: {smart_contract_permit.status}")
    if smart_contract_permit.coin_id != coin_id:
        raise ValueError("reservation coin_id must match permit coin_id")
    cap_amount = positive_amount(
        smart_contract_permit.cap_amount,
        field_name="smart contract permit cap_amount",
    )
    if max_cost > cap_amount:
        raise ValueError("reservation max_cost exceeds permit cap_amount")

    permit_now = (
        datetime.now(smart_contract_permit.expires_at.tzinfo)
        if smart_contract_permit.expires_at.tzinfo is not None
        else datetime.utcnow()
    )
    if smart_contract_permit.expires_at <= permit_now:
        raise ValueError("permit is expired")

    deadline_now = datetime.now(deadline.tzinfo) if deadline.tzinfo is not None else datetime.utcnow()
    if deadline <= deadline_now:
        raise ValueError("reservation deadline must be in the future")

    current_nonce = int(getattr(smart_contract_permit, "nonce", 0))
    if op_nonce != current_nonce + 1:
        raise ValueError(
            "reservation op_nonce must be contiguous with permit nonce: "
            f"current={current_nonce} requested={op_nonce}"
        )

    await resolve_rate_snapshot_quote_via_permit(
        smart_contract_permit=smart_contract_permit,
        rate_snapshot_id=rate_snapshot_id,
        expected_coin_id=coin_id,
    )

    reservation_id = stable_smart_contract_reservation_id(
        smart_contract_permit_id=smart_contract_permit.id,
        op_nonce=op_nonce,
    )
    for existing in smart_contract_permit.smart_contract_reservations:
        if str(existing.id) == str(reservation_id):
            return existing

    escrow = await Escrow.create_via_wallet_public(
        smart_contract_reservation_id=reservation_id,
        wallet_public_id=payer_wallet_public_id,
        op_nonce=op_nonce,
        coin_id=coin_id,
        locked_amount=max_cost,
        description=f"reservation:{reservation_id}:{op_nonce}",
    )
    expected_escrow_id = stable_escrow_id(
        wallet_public_id=payer_wallet_public_id,
        op_nonce=op_nonce,
    )
    if str(escrow.id) != str(expected_escrow_id):
        raise ValueError("reserve_operation escrow.id mismatch: " f"actual={escrow.id} expected={expected_escrow_id}")

    reservation = await SmartContractReservation.create_via_smart_contract_permit(
        smart_contract_permit_id=smart_contract_permit.id,
        op_nonce=op_nonce,
        args_hash=args_hash.strip(),
        max_cost=max_cost,
        rate_snapshot_id=rate_snapshot_id,
        deadline=deadline,
        reservation_signature=None,
        escrow=escrow,
        status=ReservationStatus.pending,
    )
    if str(reservation.id) != str(reservation_id):
        raise ValueError(
            "reserve_operation reservation.id mismatch: " f"actual={reservation.id} expected={reservation_id}"
        )

    if all(str(existing.id) != str(reservation.id) for existing in smart_contract_permit.smart_contract_reservations):
        smart_contract_permit.smart_contract_reservations.append(reservation)
    smart_contract_permit.nonce = op_nonce
    return reservation
    # --- AWARE: LOGIC END reserve_operation


async def create_via_smart_contract(
    smart_contract_id: UUID,
    finance_entity_id: UUID,
    permit_nonce: int,
    cap_amount: Annotated[Decimal, DecimalWire()],
    expires_at: datetime,
    price_schedule_id: UUID,
    coin_id: UUID,
    parent_id: UUID | None = None,
) -> SmartContractPermit:
    """
    Creates a SmartContractPermit under a contract.

    Receipt: SmartContractPermit linked to SmartContract + FinanceEntity.
    """

    # --- AWARE: LOGIC START create_via_smart_contract
    if permit_nonce <= 0:
        raise ValueError("smart_contract_permit.create_via_smart_contract requires permit_nonce > 0")
    cap_amount = positive_amount(
        cap_amount,
        field_name="smart contract permit cap_amount",
    )

    return materialize_smart_contract_permit(
        smart_contract_id=smart_contract_id,
        finance_entity_id=finance_entity_id,
        permit_nonce=permit_nonce,
        cap_amount=cap_amount,
        expires_at=expires_at,
        price_schedule_id=price_schedule_id,
        coin_id=coin_id,
        parent_id=parent_id,
    )
    # --- AWARE: LOGIC END create_via_smart_contract
