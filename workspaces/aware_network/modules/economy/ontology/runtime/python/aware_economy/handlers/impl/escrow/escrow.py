from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from decimal import Decimal
from typing import Annotated
from uuid import UUID

# Economy Ontology
from aware_economy_ontology.escrow.escrow import Escrow

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Standard
from hashlib import sha256

# Economy Runtime
from aware_economy.capital_amount import canonical_amount_text, positive_amount

# Economy Ontology
from aware_economy_ontology.escrow.escrow_enums import EscrowStatus
from aware_economy_ontology.smart_contract.smart_contract_reservation import (
    SmartContractReservation,
)
from aware_economy_ontology.smart_contract.smart_contract_reservation_enums import (
    ReservationStatus,
)
from aware_economy_ontology.stable_ids import stable_escrow_id

# --- AWARE: USER_IMPORTS END


async def release(escrow: Escrow) -> Escrow:
    """
    Releases a locked escrow after reservation settlement/cancelation.

    Receipt: Escrow(status=completed).
    """

    # --- AWARE: LOGIC START release
    if escrow.status == EscrowStatus.completed:
        return escrow
    if escrow.status != EscrowStatus.locked:
        raise ValueError(f"escrow.release invalid status transition: {escrow.status} -> {EscrowStatus.completed}")

    locked_amount = positive_amount(
        escrow.locked_amount,
        field_name="escrow locked_amount",
    )
    if escrow.op_nonce <= 0:
        raise ValueError("escrow.release requires op_nonce > 0")

    amount_key = canonical_amount_text(
        locked_amount,
        field_name="escrow locked_amount",
    )
    expected_hash_payload = (
        f"{escrow.wallet_public_id}:{escrow.coin_id}:{amount_key}:{escrow.op_nonce}:"
        f"{escrow.description or ''}:{escrow.smart_contract_reservation_id}"
    )
    expected_escrow_hash = sha256(expected_hash_payload.encode()).hexdigest()
    if escrow.escrow_hash != expected_escrow_hash:
        raise ValueError("escrow.release integrity check failed: escrow_hash mismatch")

    expected_signature = sha256(f"escrow:{expected_escrow_hash}:{escrow.wallet_public_id}".encode()).hexdigest()
    if escrow.signature != expected_signature:
        raise ValueError("escrow.release integrity check failed: signature mismatch")

    session = escrow.bound_session
    if session is None:
        raise ValueError("escrow.release requires bound session context")

    linked_reservations: list[SmartContractReservation] = []
    for obj in session.imap_all_objects():
        if not isinstance(obj, SmartContractReservation):
            continue

        linked_by_id = obj.escrow_id is not None and str(obj.escrow_id) == str(escrow.id)
        linked_by_relation = obj.escrow is not None and str(obj.escrow.id) == str(escrow.id)
        if not linked_by_id and not linked_by_relation:
            continue

        linked_reservations.append(obj)

    if not linked_reservations:
        raise ValueError("escrow.release requires linked smart_contract reservation in active lane context")

    unique_linked_reservation_ids = sorted({str(item.id) for item in linked_reservations})
    if len(unique_linked_reservation_ids) != 1:
        raise ValueError(
            "escrow.release requires exactly one linked reservation: " f"count={len(unique_linked_reservation_ids)}"
        )

    releasable_statuses = {
        ReservationStatus.cancelled,
        ReservationStatus.executed,
        ReservationStatus.expired,
        ReservationStatus.settled,
    }
    if not any(item.status in releasable_statuses for item in linked_reservations):
        status_values = sorted({str(getattr(item.status, "value", item.status)) for item in linked_reservations})
        raise ValueError(
            "escrow.release requires linked reservation status cancelled/executed/expired/settled: "
            f"statuses={status_values}"
        )

    escrow.status = EscrowStatus.completed
    return escrow
    # --- AWARE: LOGIC END release


async def release_for_reservation_status(escrow: Escrow, reservation_id: UUID, reservation_status: str) -> Escrow:
    """
    Releases a locked escrow using a smart-contract reservation lifecycle receipt.

    Receipt: Escrow(status=completed) when reservation_id matches and reservation_status is
    terminal/releasable.
    """

    # --- AWARE: LOGIC START release_for_reservation_status
    if str(reservation_id) != str(escrow.smart_contract_reservation_id):
        raise ValueError(
            "escrow.release_for_reservation_status reservation_id mismatch: "
            f"provided={reservation_id} actual={escrow.smart_contract_reservation_id}"
        )

    status_value = str(getattr(reservation_status, "value", reservation_status))
    if status_value.startswith("ReservationStatus."):
        status_value = status_value.split(".", 1)[1]
    releasable_status_values = {
        ReservationStatus.cancelled.value,
        ReservationStatus.executed.value,
        ReservationStatus.expired.value,
        ReservationStatus.settled.value,
    }
    if status_value not in releasable_status_values:
        raise ValueError(
            "escrow.release_for_reservation_status requires status "
            "cancelled/executed/expired/settled: "
            f"status={reservation_status}"
        )

    if escrow.status == EscrowStatus.completed:
        return escrow
    if escrow.status != EscrowStatus.locked:
        raise ValueError(
            "escrow.release_for_reservation_status invalid status transition: "
            f"{escrow.status} -> {EscrowStatus.completed}"
        )

    locked_amount = positive_amount(
        escrow.locked_amount,
        field_name="escrow locked_amount",
    )
    if escrow.op_nonce <= 0:
        raise ValueError("escrow.release_for_reservation_status requires op_nonce > 0")

    amount_key = canonical_amount_text(
        locked_amount,
        field_name="escrow locked_amount",
    )
    expected_hash_payload = (
        f"{escrow.wallet_public_id}:{escrow.coin_id}:{amount_key}:{escrow.op_nonce}:"
        f"{escrow.description or ''}:{escrow.smart_contract_reservation_id}"
    )
    expected_escrow_hash = sha256(expected_hash_payload.encode()).hexdigest()
    if escrow.escrow_hash != expected_escrow_hash:
        raise ValueError("escrow.release_for_reservation_status integrity check failed: " "escrow_hash mismatch")

    expected_signature = sha256(f"escrow:{expected_escrow_hash}:{escrow.wallet_public_id}".encode()).hexdigest()
    if escrow.signature != expected_signature:
        raise ValueError("escrow.release_for_reservation_status integrity check failed: " "signature mismatch")

    escrow.status = EscrowStatus.completed
    return escrow
    # --- AWARE: LOGIC END release_for_reservation_status


async def create_via_wallet_public(
    wallet_public_id: UUID,
    smart_contract_reservation_id: UUID,
    op_nonce: int,
    coin_id: UUID,
    locked_amount: Annotated[Decimal, DecimalWire()],
    description: str | None = None,
) -> Escrow:
    """
    Creates a new escrow record.

    Receipt: Escrow(status=locked) linked to SmartContractReservation + WalletPublic, with
    hash/signature computed by handler.
    """

    # --- AWARE: LOGIC START create_via_wallet_public
    if op_nonce <= 0:
        raise ValueError("escrow.create requires op_nonce > 0")
    locked_amount = positive_amount(
        locked_amount,
        field_name="escrow locked_amount",
    )

    escrow_id = stable_escrow_id(
        wallet_public_id=wallet_public_id,
        op_nonce=op_nonce,
    )

    amount_key = canonical_amount_text(
        locked_amount,
        field_name="escrow locked_amount",
    )
    hash_payload = (
        f"{wallet_public_id}:{coin_id}:{amount_key}:{op_nonce}:" f"{description or ''}:{smart_contract_reservation_id}"
    )
    escrow_hash = sha256(hash_payload.encode()).hexdigest()
    signature = sha256(f"escrow:{escrow_hash}:{wallet_public_id}".encode()).hexdigest()

    return Escrow(
        id=escrow_id,
        smart_contract_reservation_id=smart_contract_reservation_id,
        wallet_public_id=wallet_public_id,
        coin_id=coin_id,
        locked_amount=locked_amount,
        description=description,
        op_nonce=op_nonce,
        escrow_hash=escrow_hash,
        signature=signature,
        status=EscrowStatus.locked,
    )
    # --- AWARE: LOGIC END create_via_wallet_public
