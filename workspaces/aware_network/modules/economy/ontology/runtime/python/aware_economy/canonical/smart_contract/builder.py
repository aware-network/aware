"""SmartContract domain builders (canonical ORM).

These functions are intended to be called by runtime handlers. They must not
invoke the environment call-chain.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from aware_orm.session.session import Session

from aware_economy_ontology.smart_contract.smart_contract import SmartContract
from aware_economy_ontology.smart_contract.smart_contract_enums import (
    SmartContractMemberType,
)
from aware_economy_ontology.smart_contract.smart_contract_member import (
    SmartContractMember,
)
from aware_economy_ontology.smart_contract.smart_contract_permit import (
    SmartContractPermit,
)
from aware_economy.ontology.materialization import (
    materialize_smart_contract_member,
    materialize_smart_contract_permit,
)


async def add_smart_contract_member(
    *,
    session: Session | None = None,
    contract: SmartContract,
    finance_entity_id: UUID,
    member_type: SmartContractMemberType,
) -> SmartContractMember:
    _ = session
    member = materialize_smart_contract_member(
        smart_contract_id=contract.id,
        finance_entity_id=finance_entity_id,
        type=member_type,
    )
    contract.smart_contract_members.append(member)
    return member


async def open_smart_contract_session_permit(
    *,
    session: Session | None = None,
    contract: SmartContract,
    finance_entity_id: UUID,
    permit_nonce: int,
    price_schedule_id: UUID,
    cap_amount: Decimal,
    expires_at: datetime,
    parent_id: UUID | None,
    coin_id: UUID,
) -> SmartContractPermit:
    _ = session
    permit = materialize_smart_contract_permit(
        smart_contract_id=contract.id,
        finance_entity_id=finance_entity_id,
        permit_nonce=permit_nonce,
        cap_amount=cap_amount,
        expires_at=expires_at,
        price_schedule_id=price_schedule_id,
        parent_id=parent_id,
        coin_id=coin_id,
    )
    contract.smart_contract_permits.append(permit)
    return permit


__all__ = ["add_smart_contract_member", "open_smart_contract_session_permit"]
