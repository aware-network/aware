from datetime import UTC as UTC_TZ, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from aware_orm.session.session import create_session

from aware_economy.canonical.smart_contract.builder import (
    add_smart_contract_member,
    open_smart_contract_session_permit,
)
from aware_economy_ontology.smart_contract.smart_contract import SmartContract
from aware_economy_ontology.smart_contract.smart_contract_enums import (
    SmartContractMemberType,
    SmartContractStatus,
)


@pytest.mark.asyncio
async def test_build_member_and_permit_in_contract_lane() -> None:
    contract = SmartContract(
        blockchain_address="0x",
        status=SmartContractStatus.active,
        smart_contract_config_id=uuid4(),
    )

    finance_entity_id = uuid4()
    permit_nonce = 1
    price_schedule_id = uuid4()
    coin_id = uuid4()

    async with create_session(skip_db=True) as session:
        member = await add_smart_contract_member(
            session=session,
            contract=contract,
            finance_entity_id=finance_entity_id,
            member_type=SmartContractMemberType.payer,
        )
        permit = await open_smart_contract_session_permit(
            session=session,
            contract=contract,
            finance_entity_id=finance_entity_id,
            permit_nonce=permit_nonce,
            price_schedule_id=price_schedule_id,
            cap_amount=Decimal("1.5"),
            expires_at=datetime.now(UTC_TZ) + timedelta(minutes=5),
            parent_id=None,
            coin_id=coin_id,
        )

    assert member.smart_contract_id == contract.id
    assert member.finance_entity_id == finance_entity_id
    assert member in contract.smart_contract_members

    assert permit.smart_contract_id == contract.id
    assert permit.finance_entity_id == finance_entity_id
    assert permit.permit_nonce == permit_nonce
    assert permit.price_schedule_id == price_schedule_id
    assert permit.coin_id == coin_id
    assert permit in contract.smart_contract_permits
