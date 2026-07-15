from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Economy Ontology
from aware_economy_ontology.smart_contract.smart_contract_enums import (
    SmartContractMemberType,
    SmartContractStatus,
)
from aware_economy_ontology.smart_contract.smart_contract_reservation_enums import ReservationStatus
from aware_economy_ontology.smart_contract.smart_contract import SmartContract
from aware_economy_ontology.smart_contract.smart_contract_member import SmartContractMember
from aware_economy_ontology.smart_contract.smart_contract_permit import SmartContractPermit
from aware_economy_ontology.smart_contract.smart_contract_reservation import SmartContractReservation
from aware_economy_ontology.smart_contract.smart_contract_settlement import SmartContractSettlement

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Economy Ontology
from aware_economy_ontology.escrow.escrow_enums import EscrowStatus
from aware_economy_ontology.smart_contract.smart_contract_permit_enums import (
    SmartContractPermitStatus,
)
from aware_economy_ontology.smart_contract.smart_contract_settlement_enums import (
    SmartContractSettlementStatus,
)

# Economy Runtime
from aware_economy.capital_amount import (
    ZERO_AMOUNT,
    amount_equal,
    non_negative_amount,
    positive_amount,
)
from aware_economy.stable_ids import stable_smart_contract_id

# Economy Ontology
from aware_economy_ontology.stable_ids import (
    stable_escrow_id,
    stable_smart_contract_permit_id,
    stable_smart_contract_reservation_id,
    stable_smart_contract_settlement_id,
    stable_transaction_id,
)

# --- AWARE: USER_IMPORTS END


async def add_member(
    smart_contract: SmartContract, finance_entity_id: UUID, type: SmartContractMemberType
) -> SmartContractMember:
    """
    Adds a finance entity member to the contract.
    """

    # --- AWARE: LOGIC START add_member
    member = await SmartContractMember.create_via_smart_contract(
        smart_contract_id=smart_contract.id,
        finance_entity_id=finance_entity_id,
        type=type,
    )
    smart_contract.smart_contract_members.append(member)
    return member
    # --- AWARE: LOGIC END add_member


async def open_session_permit(
    smart_contract: SmartContract,
    finance_entity_id: UUID,
    permit_nonce: int,
    cap_amount: Annotated[Decimal, DecimalWire()],
    expires_at: datetime,
    price_schedule_id: UUID,
    coin_id: UUID,
    parent_id: UUID | None = None,
) -> SmartContractPermit:
    """
    Opens a session permit for a finance entity under this contract.

    Returns: the created SmartContractPermit.
    """

    # --- AWARE: LOGIC START open_session_permit
    from aware_economy.canonical.price import ensure_price_schedule_lane_via_permit

    cap_amount = positive_amount(
        cap_amount,
        field_name="smart contract permit cap_amount",
    )
    permit = await SmartContractPermit.create_via_smart_contract(
        smart_contract_id=smart_contract.id,
        finance_entity_id=finance_entity_id,
        permit_nonce=permit_nonce,
        cap_amount=cap_amount,
        expires_at=expires_at,
        price_schedule_id=price_schedule_id,
        parent_id=parent_id,
        coin_id=coin_id,
    )
    await ensure_price_schedule_lane_via_permit(
        smart_contract_permit=permit,
    )
    smart_contract.smart_contract_permits.append(permit)
    return permit
    # --- AWARE: LOGIC END open_session_permit


async def reserve_operation(
    smart_contract: SmartContract,
    permit_id: UUID,
    permit_nonce: int,
    finance_entity_id: UUID,
    payer_wallet_public_id: UUID,
    op_nonce: int,
    args_hash: str,
    max_cost: Annotated[Decimal, DecimalWire()],
    rate_snapshot_id: UUID,
    deadline: datetime,
    coin_id: UUID,
) -> SmartContractReservation:
    """
    Reserves up to max_cost by creating a deterministic reservation + escrow under this contract.

    Permit-local price schedule authority must match the referenced rate snapshot.

    Returns: the created SmartContractReservation receipt.
    """

    # --- AWARE: LOGIC START reserve_operation
    if permit_nonce <= 0:
        raise ValueError("smart_contract.reserve_operation requires permit_nonce > 0")
    if op_nonce <= 0:
        raise ValueError("smart_contract.reserve_operation requires op_nonce > 0")
    max_cost = positive_amount(max_cost, field_name="reservation max_cost")
    if not (args_hash or "").strip():
        raise ValueError("smart_contract.reserve_operation requires args_hash")

    expected_permit_id = stable_smart_contract_permit_id(
        smart_contract_id=smart_contract.id,
        finance_entity_id=finance_entity_id,
        permit_nonce=permit_nonce,
    )
    if str(permit_id) != str(expected_permit_id):
        raise ValueError("reserve_operation permit_id mismatch: " f"provided={permit_id} expected={expected_permit_id}")

    payer_members = [
        member
        for member in smart_contract.smart_contract_members
        if member.type == SmartContractMemberType.payer and str(member.finance_entity_id) == str(finance_entity_id)
    ]
    if not payer_members:
        raise ValueError("reserve_operation requires finance_entity_id to be a payer member")

    permit = None
    for candidate in smart_contract.smart_contract_permits:
        if str(candidate.id) == str(permit_id):
            permit = candidate
            break
    if permit is None:
        raise ValueError(f"smart_contract.reserve_operation permit not found: {permit_id}")
    if permit.smart_contract_id != smart_contract.id:
        raise ValueError("permit does not belong to this smart_contract")
    if str(permit.finance_entity_id) != str(finance_entity_id):
        raise ValueError("permit finance_entity_id mismatch")
    if permit.status != SmartContractPermitStatus.active:
        raise ValueError(f"permit is not active: {permit.status}")

    permit_now = datetime.now(permit.expires_at.tzinfo) if permit.expires_at.tzinfo is not None else datetime.utcnow()
    if permit.expires_at <= permit_now:
        raise ValueError("permit is expired")

    deadline_now = datetime.now(deadline.tzinfo) if deadline.tzinfo is not None else datetime.utcnow()
    if deadline <= deadline_now:
        raise ValueError("reservation deadline must be in the future")

    if permit.coin_id != coin_id:
        raise ValueError("reservation coin_id must match permit coin_id")
    permit_cap_amount = positive_amount(
        permit.cap_amount,
        field_name="smart contract permit cap_amount",
    )
    if max_cost > permit_cap_amount:
        raise ValueError("reservation max_cost exceeds permit cap_amount")

    expected_reservation_id = stable_smart_contract_reservation_id(
        smart_contract_permit_id=permit_id,
        op_nonce=op_nonce,
    )
    reservation = await permit.reserve_operation(
        payer_wallet_public_id=payer_wallet_public_id,
        op_nonce=op_nonce,
        args_hash=args_hash.strip(),
        max_cost=max_cost,
        rate_snapshot_id=rate_snapshot_id,
        deadline=deadline,
        coin_id=coin_id,
    )
    if str(reservation.id) != str(expected_reservation_id):
        raise ValueError(
            "reserve_operation reservation_id mismatch: " f"actual={reservation.id} expected={expected_reservation_id}"
        )
    return reservation
    # --- AWARE: LOGIC END reserve_operation


async def prepare_settlement(
    smart_contract: SmartContract,
    permit_id: UUID,
    reservation_id: UUID,
    final_cost: Annotated[Decimal, DecimalWire()],
    payer_finance_entity_id: UUID,
    payer_wallet_public_id: UUID,
    receiver_finance_entity_id: UUID,
    receiver_wallet_public_id: UUID,
    coin_id: UUID,
) -> SmartContractSettlement:
    """
    Builds a prepared smart-contract settlement receipt without finalizing reservation.

    Returns: the prepared SmartContractSettlement receipt.
    """

    # --- AWARE: LOGIC START prepare_settlement
    final_cost = non_negative_amount(
        final_cost,
        field_name="smart contract settlement final_cost",
    )

    permit = None
    reservation = None
    for candidate_permit in smart_contract.smart_contract_permits:
        for candidate_reservation in candidate_permit.smart_contract_reservations:
            if str(candidate_reservation.id) == str(reservation_id):
                permit = candidate_permit
                reservation = candidate_reservation
                break
        if reservation is not None:
            break

    if permit is None or reservation is None:
        raise ValueError(f"reservation not found: {reservation_id}")
    if str(permit.id) != str(permit_id):
        raise ValueError(
            "prepare_settlement permit_id mismatch for reservation: " f"provided={permit_id} actual={permit.id}"
        )
    if permit.smart_contract_id != smart_contract.id:
        raise ValueError("reservation permit does not belong to this smart_contract")
    if str(permit.finance_entity_id) != str(payer_finance_entity_id):
        raise ValueError("prepare_settlement payer_finance_entity_id does not match permit owner")
    if permit.coin_id != coin_id:
        raise ValueError("prepare_settlement coin_id must match permit coin_id")
    expected_reservation_id = stable_smart_contract_reservation_id(
        smart_contract_permit_id=permit.id,
        op_nonce=reservation.op_nonce,
    )
    if str(reservation_id) != str(expected_reservation_id):
        raise ValueError(
            "prepare_settlement reservation_id mismatch: "
            f"provided={reservation_id} expected={expected_reservation_id}"
        )

    payer_members = [
        member
        for member in smart_contract.smart_contract_members
        if member.type == SmartContractMemberType.payer
        and str(member.finance_entity_id) == str(payer_finance_entity_id)
    ]
    if not payer_members:
        raise ValueError("prepare_settlement payer_finance_entity_id is not a payer member of smart_contract")

    receiver_members = [
        member
        for member in smart_contract.smart_contract_members
        if member.type == SmartContractMemberType.receiver
        and str(member.finance_entity_id) == str(receiver_finance_entity_id)
    ]
    if not receiver_members:
        raise ValueError("prepare_settlement receiver_finance_entity_id is not a receiver member of smart_contract")
    if str(payer_finance_entity_id) == str(receiver_finance_entity_id):
        raise ValueError("prepare_settlement payer and receiver finance entities must differ")

    if reservation.status in {ReservationStatus.cancelled, ReservationStatus.expired}:
        raise ValueError(f"reservation is terminal and cannot prepare settlement: {reservation.status}")
    reservation_max_cost = positive_amount(
        reservation.max_cost,
        field_name="reservation max_cost",
    )
    if final_cost > reservation_max_cost:
        raise ValueError(
            "prepare_settlement final_cost exceeds reserved max_cost: " f"final={final_cost} max={reservation.max_cost}"
        )

    deadline_now = (
        datetime.now(reservation.deadline.tzinfo) if reservation.deadline.tzinfo is not None else datetime.utcnow()
    )
    if reservation.deadline <= deadline_now:
        raise ValueError("reservation deadline already passed")
    settlement_id = stable_smart_contract_settlement_id(
        smart_contract_reservation_id=reservation.id,
    )

    existing_final_cost = reservation.final_cost
    if reservation.status in {
        ReservationStatus.executed,
        ReservationStatus.settled,
    }:
        if existing_final_cost is not None and not amount_equal(
            existing_final_cost,
            final_cost,
        ):
            raise ValueError(
                "prepare_settlement final_cost mismatch for existing reservation state: "
                f"existing={existing_final_cost} requested={final_cost}"
            )
        existing_settlement = next(
            (
                candidate
                for candidate in reservation.smart_contract_settlements
                if str(candidate.id) == str(settlement_id)
            ),
            None,
        )
        if existing_settlement is None:
            raise ValueError("prepare_settlement requires linked smart_contract settlement receipt")
        return existing_settlement

    if reservation.status != ReservationStatus.pending:
        raise ValueError(
            "prepare_settlement requires reservation status pending/executed/settled: " f"current={reservation.status}"
        )

    settlement = await reservation.prepare_settlement(
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
        final_cost=final_cost,
    )
    if str(settlement.id) != str(settlement_id):
        raise ValueError(
            "prepare_settlement settlement.id mismatch: " f"actual={settlement.id} expected={settlement_id}"
        )

    await reservation.set_status(
        status=ReservationStatus.executed,
        final_cost=final_cost,
    )
    return settlement
    # --- AWARE: LOGIC END prepare_settlement


async def finalize_settlement(
    smart_contract: SmartContract,
    permit_id: UUID,
    reservation_id: UUID,
    final_cost: Annotated[Decimal, DecimalWire()],
    payer_finance_entity_id: UUID,
    payer_wallet_public_id: UUID,
    receiver_finance_entity_id: UUID,
    receiver_wallet_public_id: UUID,
    coin_id: UUID,
) -> SmartContractSettlement:
    """
    Finalizes a prepared settlement receipt and closes reservation lifecycle.

    Returns: the finalized SmartContractSettlement receipt.
    """

    # --- AWARE: LOGIC START finalize_settlement
    final_cost = non_negative_amount(
        final_cost,
        field_name="smart contract settlement final_cost",
    )

    permit = None
    reservation = None
    for candidate_permit in smart_contract.smart_contract_permits:
        for candidate_reservation in candidate_permit.smart_contract_reservations:
            if str(candidate_reservation.id) == str(reservation_id):
                permit = candidate_permit
                reservation = candidate_reservation
                break
        if reservation is not None:
            break

    if permit is None or reservation is None:
        raise ValueError(f"reservation not found: {reservation_id}")
    if str(permit.id) != str(permit_id):
        raise ValueError(
            "finalize_settlement permit_id mismatch for reservation: " f"provided={permit_id} actual={permit.id}"
        )
    if permit.smart_contract_id != smart_contract.id:
        raise ValueError("reservation permit does not belong to this smart_contract")
    if str(permit.finance_entity_id) != str(payer_finance_entity_id):
        raise ValueError("finalize_settlement payer_finance_entity_id does not match permit owner")
    if permit.coin_id != coin_id:
        raise ValueError("finalize_settlement coin_id must match permit coin_id")
    expected_reservation_id = stable_smart_contract_reservation_id(
        smart_contract_permit_id=permit.id,
        op_nonce=reservation.op_nonce,
    )
    if str(reservation_id) != str(expected_reservation_id):
        raise ValueError(
            "finalize_settlement reservation_id mismatch: "
            f"provided={reservation_id} expected={expected_reservation_id}"
        )

    payer_members = [
        member
        for member in smart_contract.smart_contract_members
        if member.type == SmartContractMemberType.payer
        and str(member.finance_entity_id) == str(payer_finance_entity_id)
    ]
    if not payer_members:
        raise ValueError("finalize_settlement payer_finance_entity_id is not a payer member of smart_contract")

    receiver_members = [
        member
        for member in smart_contract.smart_contract_members
        if member.type == SmartContractMemberType.receiver
        and str(member.finance_entity_id) == str(receiver_finance_entity_id)
    ]
    if not receiver_members:
        raise ValueError("finalize_settlement receiver_finance_entity_id is not a receiver member of smart_contract")
    if str(payer_finance_entity_id) == str(receiver_finance_entity_id):
        raise ValueError("finalize_settlement payer and receiver finance entities must differ")

    if reservation.status in {ReservationStatus.cancelled, ReservationStatus.expired}:
        raise ValueError(f"reservation is terminal and cannot finalize settlement: {reservation.status}")
    reservation_max_cost = positive_amount(
        reservation.max_cost,
        field_name="reservation max_cost",
    )
    if final_cost > reservation_max_cost:
        raise ValueError(
            "finalize_settlement final_cost exceeds reserved max_cost: "
            f"final={final_cost} max={reservation.max_cost}"
        )

    settlement_id = stable_smart_contract_settlement_id(
        smart_contract_reservation_id=reservation.id,
    )
    settlement = next(
        (candidate for candidate in reservation.smart_contract_settlements if str(candidate.id) == str(settlement_id)),
        None,
    )
    if settlement is None:
        raise ValueError("finalize_settlement requires prepared smart_contract settlement receipt")
    if str(settlement.payer_finance_entity_id) != str(payer_finance_entity_id):
        raise ValueError("finalize_settlement payer_finance_entity_id mismatch on settlement")
    if str(settlement.payer_wallet_public_id) != str(payer_wallet_public_id):
        raise ValueError("finalize_settlement payer_wallet_public_id mismatch on settlement")
    if str(settlement.receiver_finance_entity_id) != str(receiver_finance_entity_id):
        raise ValueError("finalize_settlement receiver_finance_entity_id mismatch on settlement")
    if str(settlement.receiver_wallet_public_id) != str(receiver_wallet_public_id):
        raise ValueError("finalize_settlement receiver_wallet_public_id mismatch on settlement")
    if str(settlement.coin_id) != str(coin_id):
        raise ValueError("finalize_settlement coin_id mismatch on settlement")
    if not amount_equal(settlement.final_cost, final_cost):
        raise ValueError(
            "finalize_settlement final_cost mismatch on settlement: "
            f"settlement={settlement.final_cost} requested={final_cost}"
        )

    existing_final_cost = reservation.final_cost
    if reservation.status == ReservationStatus.settled:
        if existing_final_cost is not None and not amount_equal(
            existing_final_cost,
            final_cost,
        ):
            raise ValueError(
                "finalize_settlement final_cost mismatch for settled reservation: "
                f"existing={existing_final_cost} requested={final_cost}"
            )
        if final_cost > ZERO_AMOUNT:
            expected_transaction_id = stable_transaction_id(
                capital_origin_id=payer_wallet_public_id,
                target_wallet_public_id=receiver_wallet_public_id,
                coin_id=coin_id,
                nonce=reservation.op_nonce,
            )
            transaction = next(
                (
                    candidate
                    for candidate in settlement.transactions
                    if str(candidate.id) == str(expected_transaction_id)
                ),
                None,
            )
            if transaction is None:
                transaction = await settlement.create_transaction(
                    nonce=reservation.op_nonce,
                    description=f"smart_contract_settlement:{settlement.id}",
                    idempotency_key=str(settlement.id),
                )
            if str(transaction.id) != str(expected_transaction_id):
                raise ValueError(
                    "finalize_settlement settled transaction.id mismatch: "
                    f"actual={transaction.id} expected={expected_transaction_id}"
                )
            if not amount_equal(transaction.coin_amount, final_cost):
                raise ValueError(
                    "finalize_settlement settled transaction coin_amount mismatch: "
                    f"actual={transaction.coin_amount} expected={final_cost}"
                )
        if settlement.status != SmartContractSettlementStatus.settled:
            await settlement.set_status(status=SmartContractSettlementStatus.settled)
        return settlement

    if reservation.status != ReservationStatus.executed:
        raise ValueError("finalize_settlement requires reservation status executed: " f"current={reservation.status}")

    if existing_final_cost is not None and not amount_equal(
        existing_final_cost,
        final_cost,
    ):
        raise ValueError(
            "finalize_settlement final_cost mismatch for prepared reservation: "
            f"existing={existing_final_cost} requested={final_cost}"
        )

    expected_escrow_id = stable_escrow_id(
        wallet_public_id=payer_wallet_public_id,
        op_nonce=reservation.op_nonce,
    )
    if reservation.escrow is None:
        if reservation.escrow_id is None:
            raise ValueError("reservation escrow_id is required for finalize_settlement")
        if str(reservation.escrow_id) != str(expected_escrow_id):
            raise ValueError(
                "finalize_settlement escrow_id mismatch: "
                f"reservation={reservation.escrow_id} expected={expected_escrow_id}"
            )
        raise ValueError("finalize_settlement requires linked escrow relationship to be loaded")
    actual_escrow_id = reservation.escrow.id
    if str(actual_escrow_id) != str(expected_escrow_id):
        raise ValueError(
            "finalize_settlement escrow relation mismatch: "
            f"reservation={actual_escrow_id} expected={expected_escrow_id}"
        )
    if reservation.escrow.status != EscrowStatus.completed:
        await reservation.escrow.release()
        if reservation.escrow.status != EscrowStatus.completed:
            raise ValueError(
                "finalize_settlement failed to release escrow to completed status: "
                f"current={reservation.escrow.status}"
            )

    if final_cost > ZERO_AMOUNT:
        expected_transaction_id = stable_transaction_id(
            capital_origin_id=payer_wallet_public_id,
            target_wallet_public_id=receiver_wallet_public_id,
            coin_id=coin_id,
            nonce=reservation.op_nonce,
        )
        transaction = await settlement.create_transaction(
            nonce=reservation.op_nonce,
            description=f"smart_contract_settlement:{settlement.id}",
            idempotency_key=str(settlement.id),
        )
        if str(transaction.id) != str(expected_transaction_id):
            raise ValueError(
                "finalize_settlement transaction.id mismatch: "
                f"actual={transaction.id} expected={expected_transaction_id}"
            )
        if not amount_equal(transaction.coin_amount, final_cost):
            raise ValueError(
                "finalize_settlement transaction coin_amount mismatch: "
                f"actual={transaction.coin_amount} expected={final_cost}"
            )

    if settlement.status != SmartContractSettlementStatus.settled:
        await settlement.set_status(status=SmartContractSettlementStatus.settled)

    await reservation.set_status(
        status=ReservationStatus.settled,
        final_cost=final_cost,
    )
    return settlement
    # --- AWARE: LOGIC END finalize_settlement


async def settle_operation(
    smart_contract: SmartContract,
    permit_id: UUID,
    reservation_id: UUID,
    final_cost: Annotated[Decimal, DecimalWire()],
    payer_finance_entity_id: UUID,
    payer_wallet_public_id: UUID,
    receiver_finance_entity_id: UUID,
    receiver_wallet_public_id: UUID,
    coin_id: UUID,
) -> SmartContractSettlement:
    """
    Compatibility settlement entrypoint that runs prepare/finalize on reservation lifecycle receipts.

    Note: escrow release is orchestrated by canonical settlement programs/service choreography.

    Returns: the finalized SmartContractSettlement receipt.
    """

    # --- AWARE: LOGIC START settle_operation
    prepared_settlement = await prepare_settlement(
        smart_contract=smart_contract,
        permit_id=permit_id,
        reservation_id=reservation_id,
        final_cost=final_cost,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
    )
    finalized_settlement = await finalize_settlement(
        smart_contract=smart_contract,
        permit_id=permit_id,
        reservation_id=reservation_id,
        final_cost=final_cost,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
    )
    if str(finalized_settlement.id) != str(prepared_settlement.id):
        raise ValueError(
            "settle_operation settlement_id mismatch between prepare/finalize: "
            f"prepare={prepared_settlement.id} finalize={finalized_settlement.id}"
        )
    return finalized_settlement
    # --- AWARE: LOGIC END settle_operation


async def release_reservation(
    smart_contract: SmartContract, permit_id: UUID, reservation_id: UUID, status: ReservationStatus
) -> SmartContractReservation:
    """
    Releases a pending smart-contract reservation as cancelled or expired.

    Receipt: SmartContractReservation(status=cancelled/expired) and Escrow(status=completed).
    """

    # --- AWARE: LOGIC START release_reservation
    if status not in {ReservationStatus.cancelled, ReservationStatus.expired}:
        raise ValueError("release_reservation status must be cancelled or expired: " f"status={status}")

    permit = None
    reservation = None
    for candidate_permit in smart_contract.smart_contract_permits:
        for candidate_reservation in candidate_permit.smart_contract_reservations:
            if str(candidate_reservation.id) == str(reservation_id):
                permit = candidate_permit
                reservation = candidate_reservation
                break
        if reservation is not None:
            break

    if permit is None or reservation is None:
        raise ValueError(f"reservation not found: {reservation_id}")
    if str(permit.id) != str(permit_id):
        raise ValueError(
            "release_reservation permit_id mismatch for reservation: " f"provided={permit_id} actual={permit.id}"
        )
    if permit.smart_contract_id != smart_contract.id:
        raise ValueError("reservation permit does not belong to this smart_contract")

    expected_reservation_id = stable_smart_contract_reservation_id(
        smart_contract_permit_id=permit.id,
        op_nonce=reservation.op_nonce,
    )
    if str(reservation_id) != str(expected_reservation_id):
        raise ValueError(
            "release_reservation reservation_id mismatch: "
            f"provided={reservation_id} expected={expected_reservation_id}"
        )

    terminal = {
        ReservationStatus.cancelled,
        ReservationStatus.expired,
        ReservationStatus.settled,
    }
    if reservation.status in terminal:
        if reservation.status != status:
            raise ValueError(
                "release_reservation terminal status mismatch: " f"current={reservation.status} requested={status}"
            )
    elif reservation.status != ReservationStatus.pending:
        raise ValueError("release_reservation requires pending reservation: " f"current={reservation.status}")
    else:
        if status == ReservationStatus.expired:
            deadline_now = (
                datetime.now(reservation.deadline.tzinfo)
                if reservation.deadline.tzinfo is not None
                else datetime.utcnow()
            )
            if reservation.deadline > deadline_now:
                raise ValueError("release_reservation cannot expire before deadline")
        reservation = await reservation.set_status(status=status)

    if reservation.escrow is None:
        raise ValueError("release_reservation requires linked escrow relationship")
    if reservation.escrow.status != EscrowStatus.completed:
        await reservation.escrow.release_for_reservation_status(
            reservation_id=reservation.id,
            reservation_status=str(getattr(status, "value", status)),
        )
    return reservation
    # --- AWARE: LOGIC END release_reservation


async def prepare_settlement_canonical(
    smart_contract: SmartContract,
    permit_id: UUID,
    reservation_id: UUID,
    payer_finance_entity_id: UUID,
    payer_wallet_public_id: UUID,
    receiver_finance_entity_id: UUID,
    receiver_wallet_public_id: UUID,
    coin_id: UUID,
) -> SmartContractSettlement:
    """
    Canonical prepare path that derives final_cost from reservation state (no caller-provided
    final_cost).

    v1 policy: final_cost is derived as reservation.max_cost.
    """

    # --- AWARE: LOGIC START prepare_settlement_canonical
    permit = None
    reservation = None
    for candidate_permit in smart_contract.smart_contract_permits:
        for candidate_reservation in candidate_permit.smart_contract_reservations:
            if str(candidate_reservation.id) == str(reservation_id):
                permit = candidate_permit
                reservation = candidate_reservation
                break
        if reservation is not None:
            break
    if permit is None or reservation is None:
        raise ValueError(f"reservation not found: {reservation_id}")
    if str(permit.id) != str(permit_id):
        raise ValueError(
            "prepare_settlement_canonical permit_id mismatch for reservation: "
            f"provided={permit_id} actual={permit.id}"
        )
    derived_final_cost = positive_amount(
        reservation.max_cost,
        field_name="reservation max_cost",
    )
    return await prepare_settlement(
        smart_contract=smart_contract,
        permit_id=permit_id,
        reservation_id=reservation_id,
        final_cost=derived_final_cost,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
    )
    # --- AWARE: LOGIC END prepare_settlement_canonical


async def finalize_settlement_canonical(
    smart_contract: SmartContract,
    permit_id: UUID,
    reservation_id: UUID,
    payer_finance_entity_id: UUID,
    payer_wallet_public_id: UUID,
    receiver_finance_entity_id: UUID,
    receiver_wallet_public_id: UUID,
    coin_id: UUID,
) -> SmartContractSettlement:
    """
    Canonical finalize path that derives final_cost from reservation state (no caller-provided
    final_cost).

    v1 policy: final_cost is derived as reservation.max_cost.
    """

    # --- AWARE: LOGIC START finalize_settlement_canonical
    permit = None
    reservation = None
    for candidate_permit in smart_contract.smart_contract_permits:
        for candidate_reservation in candidate_permit.smart_contract_reservations:
            if str(candidate_reservation.id) == str(reservation_id):
                permit = candidate_permit
                reservation = candidate_reservation
                break
        if reservation is not None:
            break
    if permit is None or reservation is None:
        raise ValueError(f"reservation not found: {reservation_id}")
    if str(permit.id) != str(permit_id):
        raise ValueError(
            "finalize_settlement_canonical permit_id mismatch for reservation: "
            f"provided={permit_id} actual={permit.id}"
        )
    derived_final_cost = positive_amount(
        reservation.max_cost,
        field_name="reservation max_cost",
    )
    return await finalize_settlement(
        smart_contract=smart_contract,
        permit_id=permit_id,
        reservation_id=reservation_id,
        final_cost=derived_final_cost,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
    )
    # --- AWARE: LOGIC END finalize_settlement_canonical


async def validate_settlement_wallet_transitions_canonical(
    smart_contract: SmartContract,
    permit_id: UUID,
    reservation_id: UUID,
    payer_expected_coin_balance: Annotated[Decimal, DecimalWire()],
    payer_new_coin_balance: Annotated[Decimal, DecimalWire()],
    receiver_expected_coin_balance: Annotated[Decimal, DecimalWire()],
    receiver_new_coin_balance: Annotated[Decimal, DecimalWire()],
    coin_id: UUID,
) -> Annotated[Decimal, DecimalWire()]:
    """
    Validates v2 wallet transitions against reservation economics.

    Fail-closed:
    - Enforces payer debit == receiver credit (conservation).
    - Enforces transfer amount == reservation.max_cost (canonical final cost).
    - Enforces non-negative debit/credit deltas.

    Returns: the canonical transfer amount derived from reservation state.
    """

    # --- AWARE: LOGIC START validate_settlement_wallet_transitions_canonical
    permit = None
    reservation = None
    for candidate_permit in smart_contract.smart_contract_permits:
        for candidate_reservation in candidate_permit.smart_contract_reservations:
            if str(candidate_reservation.id) == str(reservation_id):
                permit = candidate_permit
                reservation = candidate_reservation
                break
        if reservation is not None:
            break
    if permit is None or reservation is None:
        raise ValueError(f"reservation not found: {reservation_id}")
    if str(permit.id) != str(permit_id):
        raise ValueError(
            "validate_settlement_wallet_transitions_canonical permit_id mismatch for reservation: "
            f"provided={permit_id} actual={permit.id}"
        )
    if permit.smart_contract_id != smart_contract.id:
        raise ValueError("validate_settlement_wallet_transitions_canonical permit smart_contract mismatch")
    if permit.coin_id != coin_id:
        raise ValueError("validate_settlement_wallet_transitions_canonical coin_id mismatch")
    if reservation.status not in {
        ReservationStatus.pending,
        ReservationStatus.executed,
        ReservationStatus.settled,
    }:
        raise ValueError(
            "validate_settlement_wallet_transitions_canonical unsupported reservation status: " f"{reservation.status}"
        )

    canonical_amount = positive_amount(
        reservation.max_cost,
        field_name="reservation max_cost",
    )
    payer_expected = non_negative_amount(
        payer_expected_coin_balance,
        field_name="payer_expected_coin_balance",
    )
    payer_new = non_negative_amount(
        payer_new_coin_balance,
        field_name="payer_new_coin_balance",
    )
    receiver_expected = non_negative_amount(
        receiver_expected_coin_balance,
        field_name="receiver_expected_coin_balance",
    )
    receiver_new = non_negative_amount(
        receiver_new_coin_balance,
        field_name="receiver_new_coin_balance",
    )
    payer_delta = payer_expected - payer_new
    receiver_delta = receiver_new - receiver_expected

    if payer_delta < ZERO_AMOUNT:
        raise ValueError("validate_settlement_wallet_transitions_canonical payer delta must be >= 0")
    if receiver_delta < ZERO_AMOUNT:
        raise ValueError("validate_settlement_wallet_transitions_canonical receiver delta must be >= 0")
    if payer_delta != receiver_delta:
        raise ValueError(
            "validate_settlement_wallet_transitions_canonical conservation mismatch: "
            f"payer_delta={payer_delta} receiver_delta={receiver_delta}"
        )
    if payer_delta != canonical_amount:
        raise ValueError(
            "validate_settlement_wallet_transitions_canonical amount mismatch with reservation.max_cost: "
            f"delta={payer_delta} canonical_amount={canonical_amount}"
        )
    return canonical_amount
    # --- AWARE: LOGIC END validate_settlement_wallet_transitions_canonical


async def settle_operation_canonical(
    smart_contract: SmartContract,
    permit_id: UUID,
    reservation_id: UUID,
    payer_finance_entity_id: UUID,
    payer_wallet_public_id: UUID,
    receiver_finance_entity_id: UUID,
    receiver_wallet_public_id: UUID,
    coin_id: UUID,
) -> SmartContractSettlement:
    """
    Canonical compatibility wrapper over prepare/finalize canonical settlement functions.

    Note: escrow release is orchestrated by canonical settlement programs/service choreography.
    """

    # --- AWARE: LOGIC START settle_operation_canonical
    prepared_settlement = await prepare_settlement_canonical(
        smart_contract=smart_contract,
        permit_id=permit_id,
        reservation_id=reservation_id,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
    )
    finalized_settlement = await finalize_settlement_canonical(
        smart_contract=smart_contract,
        permit_id=permit_id,
        reservation_id=reservation_id,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
    )
    if str(finalized_settlement.id) != str(prepared_settlement.id):
        raise ValueError(
            "settle_operation_canonical settlement_id mismatch between prepare/finalize: "
            f"prepare={prepared_settlement.id} finalize={finalized_settlement.id}"
        )
    return finalized_settlement
    # --- AWARE: LOGIC END settle_operation_canonical


async def build_via_smart_contract_config(
    smart_contract_config_id: UUID,
    blockchain_address: str,
    status: SmartContractStatus = SmartContractStatus.active,
    arguments: JsonObject | None = None,
) -> SmartContract:
    """
    Creates a SmartContract instance.

    Receipt: SmartContract instance.
    """

    # --- AWARE: LOGIC START build_via_smart_contract_config
    blockchain_address_norm = blockchain_address.strip()
    arguments_json = arguments if arguments is not None else JsonObject({})
    smart_contract_id = stable_smart_contract_id(
        smart_contract_config_id=smart_contract_config_id,
        blockchain_address=blockchain_address_norm,
    )
    return SmartContract(
        id=smart_contract_id,
        smart_contract_config_id=smart_contract_config_id,
        blockchain_address=blockchain_address_norm,
        status=status,
        arguments=arguments_json,
    )
    # --- AWARE: LOGIC END build_via_smart_contract_config
