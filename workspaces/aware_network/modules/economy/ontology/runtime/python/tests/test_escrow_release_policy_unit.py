from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from aware_economy.handlers.impl.escrow.escrow import (
    create_via_wallet_public,
    release,
)
from aware_economy_ontology.escrow.escrow_enums import EscrowStatus
from aware_economy_ontology.smart_contract.smart_contract_reservation import (
    SmartContractReservation,
)
from aware_economy_ontology.smart_contract.smart_contract_reservation_enums import (
    ReservationStatus,
)
from aware_orm.session.session import Session


def _reservation(*, reservation_id, escrow_id, status: ReservationStatus) -> SmartContractReservation:  # noqa: ANN001
    return SmartContractReservation(
        id=reservation_id,
        smart_contract_permit_id=uuid4(),
        escrow_id=escrow_id,
        args_hash="args:hash",
        deadline=datetime.now(UTC) + timedelta(minutes=30),
        max_cost="10",
        op_nonce=1,
        rate_snapshot_id=uuid4(),
        status=status,
    )


@pytest.mark.asyncio
async def test_escrow_release_requires_executed_or_settled_reservation() -> None:
    reservation_id = uuid4()
    escrow = await create_via_wallet_public(
        smart_contract_reservation_id=reservation_id,
        wallet_public_id=uuid4(),
        op_nonce=1,
        coin_id=uuid4(),
        locked_amount=Decimal("10.0"),
        description="unit-test",
    )
    reservation = _reservation(
        reservation_id=reservation_id,
        escrow_id=escrow.id,
        status=ReservationStatus.pending,
    )
    session = Session(branch_id=uuid4(), skip_db=True)
    session.imap_add(escrow)
    session.imap_add(reservation)

    with pytest.raises(
        ValueError,
        match="requires linked reservation status cancelled/executed/expired/settled",
    ):
        await release(escrow)

    assert escrow.status == EscrowStatus.locked


@pytest.mark.asyncio
async def test_escrow_release_succeeds_for_executed_reservation() -> None:
    reservation_id = uuid4()
    escrow = await create_via_wallet_public(
        smart_contract_reservation_id=reservation_id,
        wallet_public_id=uuid4(),
        op_nonce=1,
        coin_id=uuid4(),
        locked_amount=Decimal("10.0"),
        description="unit-test",
    )
    reservation = _reservation(
        reservation_id=reservation_id,
        escrow_id=escrow.id,
        status=ReservationStatus.executed,
    )
    session = Session(branch_id=uuid4(), skip_db=True)
    session.imap_add(escrow)
    session.imap_add(reservation)

    released = await release(escrow)
    assert released.status == EscrowStatus.completed


@pytest.mark.asyncio
async def test_escrow_release_honors_relation_link_when_fk_mirror_is_missing() -> None:
    reservation_id = uuid4()
    escrow = await create_via_wallet_public(
        smart_contract_reservation_id=reservation_id,
        wallet_public_id=uuid4(),
        op_nonce=1,
        coin_id=uuid4(),
        locked_amount=Decimal("10.0"),
        description="unit-test",
    )
    reservation = _reservation(
        reservation_id=reservation_id,
        escrow_id=None,
        status=ReservationStatus.executed,
    )
    reservation.escrow = escrow

    session = Session(branch_id=uuid4(), skip_db=True)
    session.imap_add(escrow)
    session.imap_add(reservation)

    released = await release(escrow)
    assert released.status == EscrowStatus.completed


@pytest.mark.asyncio
async def test_escrow_release_rejects_tampered_integrity_fields() -> None:
    reservation_id = uuid4()
    escrow = await create_via_wallet_public(
        smart_contract_reservation_id=reservation_id,
        wallet_public_id=uuid4(),
        op_nonce=1,
        coin_id=uuid4(),
        locked_amount=Decimal("10.0"),
        description="unit-test",
    )
    reservation = _reservation(
        reservation_id=reservation_id,
        escrow_id=escrow.id,
        status=ReservationStatus.executed,
    )
    session = Session(branch_id=uuid4(), skip_db=True)
    session.imap_add(escrow)
    session.imap_add(reservation)

    escrow.signature = "tampered"
    with pytest.raises(ValueError, match="integrity check failed: signature mismatch"):
        await release(escrow)

    assert escrow.status == EscrowStatus.locked
