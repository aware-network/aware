from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, Iterator, cast
from uuid import UUID, uuid4

import pytest

import aware_economy.smart_contract_settlement as permit_runtime
from aware_economy.finance_readiness import FinanceEntityReadinessReceipt
from aware_economy.handlers.impl.smart_contract.smart_contract_permit import (
    revoke as revoke_permit,
)
from aware_economy.smart_contract_settlement import (
    EconomySmartContractSettlementOperationContext,
    ensure_service_operation_permit,
)
from aware_economy_ontology.smart_contract.smart_contract_enums import (
    SmartContractMemberType,
    SmartContractStatus,
)
from aware_economy_ontology.smart_contract.smart_contract_permit_enums import (
    SmartContractPermitStatus,
)
from aware_economy_ontology.smart_contract.smart_contract_permit import (
    SmartContractPermit,
)
from aware_economy_ontology.stable_ids import stable_smart_contract_permit_id


class _Lane:
    @contextmanager
    def activate(self, *, commit: bool, publish: bool) -> Iterator[None]:
        assert commit is True
        assert publish is False
        yield


class _LaneBinder:
    def bind(self, **kwargs: object) -> _Lane:
        assert kwargs["actor_id"] is not None
        return _Lane()


class _Permit(SimpleNamespace):
    async def revoke(self) -> _Permit:
        self.status = SmartContractPermitStatus.revoked
        return self


class _Contract:
    def __init__(
        self,
        *,
        contract_id: UUID,
        finance_entity_id: UUID,
        permits: list[_Permit],
    ) -> None:
        self.id = contract_id
        self.status = SmartContractStatus.active
        self.smart_contract_members = [
            SimpleNamespace(
                type=SmartContractMemberType.payer,
                finance_entity_id=finance_entity_id,
            )
        ]
        self.smart_contract_permits = permits

    async def open_session_permit(self, **kwargs: Any) -> _Permit:
        permit = _permit(
            smart_contract_id=self.id,
            finance_entity_id=kwargs["finance_entity_id"],
            permit_nonce=kwargs["permit_nonce"],
            price_schedule_id=kwargs["price_schedule_id"],
            coin_id=kwargs["coin_id"],
            cap_amount=kwargs["cap_amount"],
            expires_at=kwargs["expires_at"],
            parent_id=kwargs["parent_id"],
        )
        self.smart_contract_permits.append(permit)
        return permit


def _permit(
    *,
    smart_contract_id: UUID,
    finance_entity_id: UUID,
    permit_nonce: int,
    price_schedule_id: UUID,
    coin_id: UUID,
    cap_amount: Decimal,
    expires_at: datetime,
    parent_id: UUID | None = None,
) -> _Permit:
    return _Permit(
        id=stable_smart_contract_permit_id(
            smart_contract_id=smart_contract_id,
            finance_entity_id=finance_entity_id,
            permit_nonce=permit_nonce,
        ),
        smart_contract_id=smart_contract_id,
        smart_contract_permit_id=parent_id,
        finance_entity_id=finance_entity_id,
        permit_nonce=permit_nonce,
        price_schedule_id=price_schedule_id,
        coin_id=coin_id,
        cap_amount=cap_amount,
        expires_at=expires_at,
        status=SmartContractPermitStatus.active,
    )


@pytest.mark.asyncio
async def test_permit_revoke_is_idempotent() -> None:
    permit = SmartContractPermit(
        smart_contract_id=uuid4(),
        finance_entity_id=uuid4(),
        permit_nonce=1,
        cap_amount=Decimal("10"),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        price_schedule_id=uuid4(),
        coin_id=uuid4(),
        status=SmartContractPermitStatus.active,
    )

    first = await revoke_permit(permit)
    second = await revoke_permit(permit)

    assert first is permit
    assert second is permit
    assert permit.status == SmartContractPermitStatus.revoked


@pytest.mark.asyncio
async def test_service_operation_permit_reuses_sufficient_active_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor_id = uuid4()
    finance_entity_id = uuid4()
    contract_id = uuid4()
    schedule_id = uuid4()
    coin_id = uuid4()
    requested_expiry = datetime.now(UTC) + timedelta(hours=1)
    existing = _permit(
        smart_contract_id=contract_id,
        finance_entity_id=finance_entity_id,
        permit_nonce=3,
        price_schedule_id=schedule_id,
        coin_id=coin_id,
        cap_amount=Decimal("20"),
        expires_at=requested_expiry + timedelta(hours=1),
    )
    contract = _Contract(
        contract_id=contract_id,
        finance_entity_id=finance_entity_id,
        permits=[existing],
    )
    readiness = FinanceEntityReadinessReceipt(
        actor_id=actor_id,
        finance_role_key="primary",
        finance_entity_id=finance_entity_id,
        wallet_id=uuid4(),
        wallet_public_id=uuid4(),
        finance_entity_ready=True,
        wallet_ready=True,
        idempotent_replay=True,
    )

    async def _readiness(**kwargs: object) -> FinanceEntityReadinessReceipt:
        return readiness

    async def _contract(**kwargs: object) -> object:
        return contract

    monkeypatch.setattr(permit_runtime, "resolve_finance_entity_readiness", _readiness)
    monkeypatch.setattr(permit_runtime, "_hydrate_smart_contract", _contract)
    monkeypatch.setattr(
        permit_runtime,
        "resolve_economy_finance_readiness_runtime_context",
        lambda **kwargs: object(),
    )

    receipt = await ensure_service_operation_permit(
        runtime_context=cast(
            Any,
            SimpleNamespace(
                lane_binder=_LaneBinder(),
                index=object(),
                lanes=SimpleNamespace(smart_contract_projection_hash="projection"),
            ),
        ),
        operation_context=EconomySmartContractSettlementOperationContext(
            actor_id=actor_id
        ),
        actor_id=actor_id,
        finance_role_key="primary",
        smart_contract_id=contract_id,
        price_schedule_id=schedule_id,
        coin_id=coin_id,
        cap_amount=Decimal("10"),
        expires_at=requested_expiry,
        commit=True,
        publish=False,
    )

    assert receipt.permit_id == existing.id
    assert receipt.permit_nonce == 3
    assert receipt.cap_amount == Decimal("20")
    assert receipt.idempotent_replay is True
    assert receipt.refreshed is False
    assert len(contract.smart_contract_permits) == 1


@pytest.mark.asyncio
async def test_service_operation_permit_refreshes_with_next_nonce(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor_id = uuid4()
    finance_entity_id = uuid4()
    contract_id = uuid4()
    schedule_id = uuid4()
    coin_id = uuid4()
    requested_expiry = datetime.now(UTC) + timedelta(hours=2)
    insufficient = _permit(
        smart_contract_id=contract_id,
        finance_entity_id=finance_entity_id,
        permit_nonce=4,
        price_schedule_id=schedule_id,
        coin_id=coin_id,
        cap_amount=Decimal("5"),
        expires_at=requested_expiry + timedelta(hours=1),
    )
    contract = _Contract(
        contract_id=contract_id,
        finance_entity_id=finance_entity_id,
        permits=[insufficient],
    )
    readiness = FinanceEntityReadinessReceipt(
        actor_id=actor_id,
        finance_role_key="primary",
        finance_entity_id=finance_entity_id,
        wallet_id=uuid4(),
        wallet_public_id=uuid4(),
        finance_entity_ready=True,
        wallet_ready=True,
        idempotent_replay=True,
    )

    async def _readiness(**kwargs: object) -> FinanceEntityReadinessReceipt:
        return readiness

    async def _contract(**kwargs: object) -> object:
        return contract

    monkeypatch.setattr(permit_runtime, "resolve_finance_entity_readiness", _readiness)
    monkeypatch.setattr(permit_runtime, "_hydrate_smart_contract", _contract)
    monkeypatch.setattr(
        permit_runtime,
        "resolve_economy_finance_readiness_runtime_context",
        lambda **kwargs: object(),
    )

    receipt = await ensure_service_operation_permit(
        runtime_context=cast(
            Any,
            SimpleNamespace(
                lane_binder=_LaneBinder(),
                index=object(),
                lanes=SimpleNamespace(smart_contract_projection_hash="projection"),
            ),
        ),
        operation_context=EconomySmartContractSettlementOperationContext(
            actor_id=actor_id
        ),
        actor_id=actor_id,
        finance_role_key="primary",
        smart_contract_id=contract_id,
        price_schedule_id=schedule_id,
        coin_id=coin_id,
        cap_amount=Decimal("25"),
        expires_at=requested_expiry,
        commit=True,
        publish=False,
    )

    assert receipt.permit_nonce == 5
    assert receipt.cap_amount == Decimal("25")
    assert receipt.idempotent_replay is False
    assert receipt.refreshed is True
    assert len(contract.smart_contract_permits) == 2
    assert insufficient.status == SmartContractPermitStatus.revoked
    assert (
        contract.smart_contract_permits[-1].status == SmartContractPermitStatus.active
    )
    assert (
        contract.smart_contract_permits[-1].smart_contract_permit_id == insufficient.id
    )
