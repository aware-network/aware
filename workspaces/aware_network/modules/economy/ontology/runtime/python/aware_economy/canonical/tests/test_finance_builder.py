import pytest
from uuid import uuid4

from aware_orm.session.session import create_session

from aware_economy.canonical.finance.builder import build_finance_entity
from aware_economy.wallet_custody import WALLET_CUSTODY_PREFIX


@pytest.mark.asyncio
async def test_build_finance_entity_creates_wallet_components() -> None:
    identity_id = uuid4()
    async with create_session(skip_db=True) as session:
        finance_entity = await build_finance_entity(
            session=session,
            identity_id=identity_id,
        )

    assert finance_entity.identity_id == identity_id
    assert finance_entity.role_key == "primary"
    assert finance_entity.wallet is not None
    assert finance_entity.wallet.wallet_public is not None
    assert finance_entity.wallet.wallet_private is not None
    assert finance_entity.wallet.wallet_public.address.startswith("0x")
    assert finance_entity.wallet.wallet_private.private_key_encrypted.startswith(
        f"{WALLET_CUSTODY_PREFIX}:"
    )
