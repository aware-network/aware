from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from aware_economy.capital_amount import positive_amount
from aware_economy_ontology.escrow.escrow import Escrow
from aware_economy_ontology.smart_contract.smart_contract_enums import (
    SmartContractMemberType,
)
from aware_economy_ontology.smart_contract.smart_contract_member import (
    SmartContractMember,
)
from aware_economy_ontology.smart_contract.smart_contract_permit import (
    SmartContractPermit,
)
from aware_economy_ontology.smart_contract.smart_contract_permit_enums import (
    SmartContractPermitStatus,
)
from aware_economy_ontology.smart_contract.smart_contract_reservation import (
    SmartContractReservation,
)
from aware_economy_ontology.smart_contract.smart_contract_reservation_enums import (
    ReservationStatus,
)
from aware_economy_ontology.stable_ids import (
    stable_smart_contract_member_id,
    stable_smart_contract_permit_id,
    stable_smart_contract_reservation_id,
)


def materialize_smart_contract_member(
    *,
    smart_contract_id: UUID,
    finance_entity_id: UUID,
    type: SmartContractMemberType,
) -> SmartContractMember:
    member_type = getattr(type, "value", str(type))
    smart_contract_member_id = stable_smart_contract_member_id(
        smart_contract_id=smart_contract_id,
        finance_entity_id=finance_entity_id,
        type=str(member_type),
    )
    return SmartContractMember(
        id=smart_contract_member_id,
        smart_contract_id=smart_contract_id,
        finance_entity_id=finance_entity_id,
        type=type,
    )


def materialize_smart_contract_permit(
    *,
    smart_contract_id: UUID,
    finance_entity_id: UUID,
    permit_nonce: int,
    cap_amount: Decimal,
    expires_at: datetime,
    price_schedule_id: UUID,
    coin_id: UUID,
    parent_id: UUID | None = None,
    nonce: int = 0,
    status: SmartContractPermitStatus = SmartContractPermitStatus.active,
) -> SmartContractPermit:
    if permit_nonce <= 0:
        raise ValueError(
            "smart_contract_permit.create_via_smart_contract requires permit_nonce > 0"
        )
    cap_amount = positive_amount(
        cap_amount,
        field_name="smart contract permit cap_amount",
    )

    permit_id = stable_smart_contract_permit_id(
        smart_contract_id=smart_contract_id,
        finance_entity_id=finance_entity_id,
        permit_nonce=permit_nonce,
    )
    return SmartContractPermit(
        id=permit_id,
        smart_contract_id=smart_contract_id,
        smart_contract_permit_id=parent_id,
        finance_entity_id=finance_entity_id,
        permit_nonce=permit_nonce,
        nonce=nonce,
        cap_amount=cap_amount,
        expires_at=expires_at,
        price_schedule_id=price_schedule_id,
        coin_id=coin_id,
        status=status,
    )


def materialize_smart_contract_reservation(
    *,
    smart_contract_permit_id: UUID,
    op_nonce: int,
    args_hash: str,
    max_cost: Decimal,
    rate_snapshot_id: UUID,
    deadline: datetime,
    reservation_signature: str | None = None,
    escrow: Escrow | None = None,
    status: ReservationStatus = ReservationStatus.pending,
) -> SmartContractReservation:
    max_cost = positive_amount(max_cost, field_name="reservation max_cost")

    reservation_id = stable_smart_contract_reservation_id(
        smart_contract_permit_id=smart_contract_permit_id,
        op_nonce=op_nonce,
    )
    escrow_id = escrow.id if escrow is not None else None
    return SmartContractReservation(
        id=reservation_id,
        smart_contract_permit_id=smart_contract_permit_id,
        op_nonce=op_nonce,
        args_hash=args_hash,
        max_cost=max_cost,
        rate_snapshot_id=rate_snapshot_id,
        deadline=deadline,
        reservation_signature=reservation_signature,
        escrow=escrow,
        escrow_id=escrow_id,
        status=status,
    )


__all__ = [
    "materialize_smart_contract_member",
    "materialize_smart_contract_permit",
    "materialize_smart_contract_reservation",
]
