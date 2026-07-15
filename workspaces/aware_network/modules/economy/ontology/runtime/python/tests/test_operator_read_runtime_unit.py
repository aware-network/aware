from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from aware_economy.operator_read import (
    EconomyOperatorReplicaReadModels,
    resolve_wallet_capital_frame_from_economy_replica,
    resolve_wallet_capital_view_state_from_economy_replica,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalFrameResolveRequest,
)


class _FakeReplicaModel:
    def __init__(self, rows: list[object]) -> None:
        self.rows = rows

    async def by_id(self, object_id: UUID) -> object | None:
        for row in self.rows:
            if getattr(row, "id") == object_id:
                return row
        return None

    async def many(self, **filters: object) -> list[object]:
        return [
            row
            for row in self.rows
            if all(getattr(row, key, None) == value for key, value in filters.items())
        ]


@pytest.mark.asyncio
async def test_wallet_capital_frame_assembles_wallet_rooted_replica_truth() -> None:
    wallet_id = uuid4()
    wallet_public_id = uuid4()
    finance_entity_id = uuid4()
    provider_finance_entity_id = uuid4()
    provider_config_id = uuid4()
    provider_route_id = uuid4()
    capital_conversion_quote_id = uuid4()
    coin_id = uuid4()
    other_coin_id = uuid4()
    transaction_id = uuid4()
    transaction_external_id = uuid4()
    transaction_intent_id = uuid4()
    escrow_id = uuid4()
    reservation_id = uuid4()
    settlement_id = uuid4()
    provider_lifecycle_receipt_id = uuid4()
    models = _read_models(
        wallets=[
            SimpleNamespace(
                id=wallet_id,
                wallet_public_id=wallet_public_id,
            )
        ],
        wallet_balances=[
            SimpleNamespace(
                id=uuid4(),
                wallet_id=wallet_id,
                coin_id=other_coin_id,
                balance=Decimal("99"),
                held_balance=Decimal("0"),
            ),
            SimpleNamespace(
                id=uuid4(),
                wallet_id=wallet_id,
                coin_id=coin_id,
                balance=Decimal("30"),
                held_balance=Decimal("10"),
            ),
        ],
        finance_entities=[
            SimpleNamespace(
                id=finance_entity_id,
                wallet_id=wallet_id,
                role_key="primary",
            )
        ],
        provider_configs=[
            SimpleNamespace(
                id=provider_config_id,
                provider_finance_entity_id=provider_finance_entity_id,
                provider_key="stripe",
                label="Stripe wallet funding",
                status="active",
            )
        ],
        provider_routes=[
            SimpleNamespace(
                id=provider_route_id,
                external_capital_provider_config_id=provider_config_id,
                target_coin_id=coin_id,
                route_key="stripe-usd-direct",
                external_currency="USD",
                external_minor_unit_exponent=2,
                conversion_mode="direct_denomination",
                min_external_amount_minor=500,
                max_external_amount_minor=500_000,
                status="active",
            )
        ],
        capital_conversion_quotes=[
            SimpleNamespace(
                id=capital_conversion_quote_id,
                provider_route_id=provider_route_id,
                target_coin_id=coin_id,
                external_amount_minor=2500,
                external_currency="USD",
                target_amount=Decimal("25"),
                conversion_mode="direct_denomination",
                source="external_capital_provider_route",
                quote_hash="a" * 64,
                captured_at=datetime(2026, 7, 8, 7, 58, 0),
                expires_at=datetime(2026, 7, 8, 8, 28, 0),
            )
        ],
        transaction_intents=[
            SimpleNamespace(
                id=transaction_intent_id,
                provider_config_id=provider_config_id,
                recipient_finance_entity_id=finance_entity_id,
                recipient_wallet_id=wallet_id,
                recipient_wallet_public_id=wallet_public_id,
                coin_id=coin_id,
                amount=Decimal("25"),
                funding_intent_key="wallet-topup-1",
                idempotency_key="prepare-wallet-topup-1",
                provider_key="stripe",
                status="created",
                created_at=datetime(2026, 7, 8, 7, 58, 0),
                updated_at=None,
                capital_conversion_quote_id=capital_conversion_quote_id,
            )
        ],
        transactions=[
            SimpleNamespace(
                id=transaction_id,
                source_wallet_public_id=uuid4(),
                target_wallet_public_id=wallet_public_id,
                coin_id=coin_id,
                coin_amount=Decimal("25"),
                gas_price=Decimal("0"),
                nonce=4,
                status="confirmed",
                transaction_hash="tx-hash-1",
                idempotency_key="idem-record-1",
                description="wallet funding",
                confirmed_at=datetime(2026, 7, 8, 8, 0, 0),
                source_previous_coin_balance=Decimal("0"),
                target_previous_coin_balance=Decimal("5"),
            )
        ],
        transaction_externals=[
            SimpleNamespace(
                id=transaction_external_id,
                transaction_id=transaction_id,
                transaction_intent_id=transaction_intent_id,
                provider_config_id=provider_config_id,
                capital_conversion_quote_id=capital_conversion_quote_id,
                provider_finance_entity_id=provider_finance_entity_id,
                provider_key="stripe",
                provider_event_id="evt_wallet_1",
                provider_public_reference="pi_wallet_1",
                provider_payload_hash="payload-hash",
                external_amount_minor=2500,
                external_currency="USD",
                quote_hash="a" * 64,
                idempotency_key="idem-record-1",
                status="processed",
                processed_at=datetime(2026, 7, 8, 8, 1, 0),
                external_created_at=datetime(2026, 7, 8, 7, 59, 0),
                metadata_json={"provider": "stripe"},
            )
        ],
        escrows=[
            SimpleNamespace(
                id=escrow_id,
                wallet_public_id=wallet_public_id,
                coin_id=coin_id,
                locked_amount=Decimal("7"),
                op_nonce=9,
                escrow_hash="escrow-hash-1",
                smart_contract_reservation_id=reservation_id,
                status="locked",
                description="service hold",
            )
        ],
        reservations=[
            SimpleNamespace(
                id=reservation_id,
                smart_contract_permit_id=uuid4(),
                escrow_id=escrow_id,
                rate_snapshot_id=uuid4(),
                op_nonce=9,
                args_hash="args-hash-1",
                max_cost=Decimal("7"),
                final_cost=None,
                status="pending",
                deadline=datetime(2026, 7, 9, 8, 0, 0),
            )
        ],
        settlements=[
            SimpleNamespace(
                id=settlement_id,
                smart_contract_reservation_id=reservation_id,
                payer_finance_entity_id=finance_entity_id,
                payer_wallet_public_id=wallet_public_id,
                receiver_finance_entity_id=uuid4(),
                receiver_wallet_public_id=uuid4(),
                coin_id=coin_id,
                final_cost=Decimal("7"),
                status="settled",
            )
        ],
        provider_lifecycle_receipts=[
            SimpleNamespace(
                id=provider_lifecycle_receipt_id,
                provider_finance_entity_id=provider_finance_entity_id,
                provider_key="stripe",
                provider_event_id="evt_refund_1",
                provider_lifecycle_object_id="re_wallet_1",
                provider_lifecycle_effect_key="refund",
                idempotency_key="stripe:lifecycle:re_wallet_1:refund",
                wallet_finance_entity_id=finance_entity_id,
                wallet_id=wallet_id,
                wallet_public_id=wallet_public_id,
                coin_id=coin_id,
                amount=Decimal("5"),
                event_kind="refund",
                status="applied",
                previous_balance=Decimal("30"),
                new_balance=Decimal("25"),
                previous_held_balance=Decimal("10"),
                new_held_balance=Decimal("10"),
                previous_available_balance=Decimal("20"),
                new_available_balance=Decimal("15"),
                provider_payment_reference="pi_wallet_1",
                provider_payload_hash="payload-hash",
                transaction_id=transaction_id,
                transaction_external_id=transaction_external_id,
                processed_at=datetime(2026, 7, 8, 8, 2, 0),
                external_created_at=datetime(2026, 7, 8, 8, 1, 30),
                metadata_json={"kind": "refund"},
            )
        ],
    )

    frame = await resolve_wallet_capital_frame_from_economy_replica(
        request=EconomyWalletCapitalFrameResolveRequest(
            actor_id=str(uuid4()),
            wallet_id=str(wallet_id),
            coin_id=str(coin_id),
            limit=50,
        ),
        models=models,
    )

    assert frame.ready is True
    assert frame.wallet_id == str(wallet_id)
    assert frame.wallet_public_id == str(wallet_public_id)
    assert frame.finance_entity_id == str(finance_entity_id)
    assert frame.coin_id == str(coin_id)
    assert len(frame.balances) == 1
    assert frame.balances[0].available_balance == Decimal("20")
    assert [item.funding_intent_key for item in frame.transaction_intents] == [
        "wallet-topup-1"
    ]
    assert frame.funding_providers[0].provider_route_id == str(provider_route_id)
    assert frame.transaction_intents[0].capital_conversion_quote.quote_hash == "a" * 64
    assert [item.transaction_id for item in frame.transactions] == [str(transaction_id)]
    assert [item.transaction_external_id for item in frame.transaction_externals] == [
        str(transaction_external_id)
    ]
    assert [item.escrow_id for item in frame.escrows] == [str(escrow_id)]
    assert [item.reservation_id for item in frame.reservations] == [str(reservation_id)]
    assert [item.settlement_id for item in frame.settlements] == [str(settlement_id)]
    assert [
        item.provider_lifecycle_receipt_id for item in frame.provider_lifecycle_receipts
    ] == [str(provider_lifecycle_receipt_id)]
    assert frame.activity_count == 7
    assert frame.info == "economy wallet capital frame resolved"


@pytest.mark.asyncio
async def test_wallet_capital_view_state_resolves_from_replica_frame() -> None:
    wallet_id = uuid4()
    wallet_public_id = uuid4()
    finance_entity_id = uuid4()
    provider_finance_entity_id = uuid4()
    provider_config_id = uuid4()
    provider_route_id = uuid4()
    capital_conversion_quote_id = uuid4()
    coin_id = uuid4()
    provider_lifecycle_receipt_id = uuid4()
    models = _read_models(
        wallets=[SimpleNamespace(id=wallet_id, wallet_public_id=wallet_public_id)],
        wallet_balances=[
            SimpleNamespace(
                id=uuid4(),
                wallet_id=wallet_id,
                coin_id=coin_id,
                balance=Decimal("30"),
                held_balance=Decimal("10"),
            )
        ],
        finance_entities=[
            SimpleNamespace(
                id=finance_entity_id,
                wallet_id=wallet_id,
                role_key="primary",
            )
        ],
        provider_configs=[
            SimpleNamespace(
                id=provider_config_id,
                provider_finance_entity_id=provider_finance_entity_id,
                provider_key="external_provider",
                label="External provider",
                status="active",
            )
        ],
        provider_routes=[
            SimpleNamespace(
                id=provider_route_id,
                external_capital_provider_config_id=provider_config_id,
                target_coin_id=coin_id,
                route_key="external-provider-usd",
                external_currency="USD",
                external_minor_unit_exponent=2,
                conversion_mode="direct_denomination",
                min_external_amount_minor=None,
                max_external_amount_minor=None,
                status="active",
            )
        ],
        capital_conversion_quotes=[
            SimpleNamespace(
                id=capital_conversion_quote_id,
                provider_route_id=provider_route_id,
                target_coin_id=coin_id,
                external_amount_minor=2500,
                external_currency="USD",
                target_amount=Decimal("25"),
                conversion_mode="direct_denomination",
                source="external_capital_provider_route",
                quote_hash="b" * 64,
                captured_at=datetime(2026, 7, 8, 8, 0, 0),
                expires_at=None,
            )
        ],
        transaction_intents=[
            SimpleNamespace(
                id=uuid4(),
                provider_config_id=provider_config_id,
                recipient_finance_entity_id=finance_entity_id,
                recipient_wallet_id=wallet_id,
                recipient_wallet_public_id=wallet_public_id,
                coin_id=coin_id,
                amount=Decimal("25"),
                funding_intent_key="wallet-topup-1",
                idempotency_key="prepare-wallet-topup-1",
                provider_key="external_provider",
                status="created",
                created_at=datetime(2026, 7, 8, 8, 0, 0),
                updated_at=None,
                capital_conversion_quote_id=capital_conversion_quote_id,
            )
        ],
        provider_lifecycle_receipts=[
            SimpleNamespace(
                id=provider_lifecycle_receipt_id,
                provider_finance_entity_id=provider_finance_entity_id,
                provider_key="external_provider",
                provider_event_id="evt_wallet_1",
                provider_lifecycle_object_id="re_wallet_1",
                provider_lifecycle_effect_key="refund",
                idempotency_key="external_provider:lifecycle:re_wallet_1:refund",
                wallet_finance_entity_id=finance_entity_id,
                wallet_id=wallet_id,
                wallet_public_id=wallet_public_id,
                coin_id=coin_id,
                amount=Decimal("25"),
                event_kind="refund",
                status="applied",
                previous_balance=Decimal("5"),
                new_balance=Decimal("30"),
                previous_held_balance=Decimal("0"),
                new_held_balance=Decimal("10"),
                previous_available_balance=Decimal("5"),
                new_available_balance=Decimal("20"),
                provider_payment_reference="pi_wallet_1",
                provider_payload_hash="payload-hash",
                transaction_id=uuid4(),
                transaction_external_id=uuid4(),
                processed_at=datetime(2026, 7, 8, 8, 2, 0),
                external_created_at=datetime(2026, 7, 8, 8, 1, 30),
                metadata_json={"kind": "wallet_funding"},
            )
        ],
    )

    state = await resolve_wallet_capital_view_state_from_economy_replica(
        request=EconomyWalletCapitalFrameResolveRequest(
            actor_id=str(uuid4()),
            wallet_id=str(wallet_id),
            coin_id=str(coin_id),
        ),
        models=models,
    )

    assert state.view_ref == "economy.wallet_capital"
    assert state.root_projection_ref == "Wallet.home"
    assert state.operation == "refresh_wallet_capital"
    assert state.status == "ready"
    assert state.status_tone == "success"
    assert state.wallet_id == str(wallet_id)
    assert state.wallet_public_id == str(wallet_public_id)
    assert state.finance_entity_id == str(finance_entity_id)
    assert state.coin_id == str(coin_id)
    assert state.balances[0].available_balance == Decimal("20")
    assert state.action_keys == ["refresh_wallet_capital", "fund_wallet"]
    assert state.can_fund_wallet is True
    assert state.pending_funding_intents[0].funding_intent_ref == "wallet-topup-1"
    assert state.pending_funding_intents[0].quote_hash == "b" * 64
    assert state.funding_providers[0].provider_key == "external_provider"
    assert state.activity_count == 2
    assert state.provenance["source_kind"] == "ontology_replica"
    fund_action = next(
        action for action in state.actions if action.action_key == "fund_wallet"
    )
    assert fund_action.input_hints["derived_fields"] == {
        "target_wallet_id": str(wallet_id),
        "coin_id": str(coin_id),
    }


@pytest.mark.asyncio
async def test_wallet_capital_frame_is_not_ready_when_wallet_is_missing() -> None:
    wallet_id = uuid4()

    frame = await resolve_wallet_capital_frame_from_economy_replica(
        request=EconomyWalletCapitalFrameResolveRequest(
            wallet_id=str(wallet_id),
            limit=50,
        ),
        models=_read_models(wallets=[]),
    )

    assert frame.ready is False
    assert frame.wallet_id == str(wallet_id)
    assert frame.activity_count == 0
    assert frame.info == "economy wallet not found"


@pytest.mark.asyncio
async def test_wallet_capital_frame_bounds_each_activity_list() -> None:
    wallet_id = uuid4()
    wallet_public_id = uuid4()
    coin_id = uuid4()
    first_transaction_id = uuid4()
    second_transaction_id = uuid4()
    models = _read_models(
        wallets=[SimpleNamespace(id=wallet_id, wallet_public_id=wallet_public_id)],
        wallet_balances=[
            SimpleNamespace(
                id=uuid4(),
                wallet_id=wallet_id,
                coin_id=coin_id,
                balance=Decimal("10"),
                held_balance=Decimal("0"),
            ),
            SimpleNamespace(
                id=uuid4(),
                wallet_id=wallet_id,
                coin_id=uuid4(),
                balance=Decimal("20"),
                held_balance=Decimal("0"),
            ),
        ],
        transactions=[
            SimpleNamespace(
                id=second_transaction_id,
                source_wallet_public_id=wallet_public_id,
                target_wallet_public_id=uuid4(),
                coin_id=coin_id,
                coin_amount=Decimal("2"),
                gas_price=Decimal("0"),
                nonce=2,
                status="confirmed",
                transaction_hash="tx-2",
            ),
            SimpleNamespace(
                id=first_transaction_id,
                source_wallet_public_id=wallet_public_id,
                target_wallet_public_id=uuid4(),
                coin_id=coin_id,
                coin_amount=Decimal("1"),
                gas_price=Decimal("0"),
                nonce=1,
                status="confirmed",
                transaction_hash="tx-1",
            ),
        ],
    )

    frame = await resolve_wallet_capital_frame_from_economy_replica(
        request=EconomyWalletCapitalFrameResolveRequest(
            wallet_id=str(wallet_id),
            limit=1,
            include_transaction_externals=False,
        ),
        models=models,
    )

    assert len(frame.balances) == 1
    assert [item.transaction_id for item in frame.transactions] == [
        str(first_transaction_id)
    ]


@pytest.mark.asyncio
async def test_wallet_capital_frame_rejects_text_money_from_replica() -> None:
    wallet_id = uuid4()
    models = _read_models(
        wallets=[SimpleNamespace(id=wallet_id, wallet_public_id=uuid4())],
        wallet_balances=[
            SimpleNamespace(
                id=uuid4(),
                wallet_id=wallet_id,
                coin_id=uuid4(),
                balance="10",
                held_balance=Decimal("0"),
            )
        ],
    )

    with pytest.raises(TypeError, match="balance must be materialized as Decimal"):
        await resolve_wallet_capital_frame_from_economy_replica(
            request=EconomyWalletCapitalFrameResolveRequest(wallet_id=str(wallet_id)),
            models=models,
        )


def _read_models(
    *,
    wallets: list[object] | None = None,
    wallet_balances: list[object] | None = None,
    finance_entities: list[object] | None = None,
    provider_configs: list[object] | None = None,
    provider_routes: list[object] | None = None,
    capital_conversion_quotes: list[object] | None = None,
    transaction_intents: list[object] | None = None,
    transaction_externals: list[object] | None = None,
    transactions: list[object] | None = None,
    provider_lifecycle_receipts: list[object] | None = None,
    escrows: list[object] | None = None,
    reservations: list[object] | None = None,
    settlements: list[object] | None = None,
) -> EconomyOperatorReplicaReadModels:
    return EconomyOperatorReplicaReadModels(
        wallet_model=_FakeReplicaModel(wallets or []),
        wallet_balance_model=_FakeReplicaModel(wallet_balances or []),
        finance_entity_model=_FakeReplicaModel(finance_entities or []),
        external_capital_provider_config_model=_FakeReplicaModel(
            provider_configs or []
        ),
        external_capital_provider_route_model=_FakeReplicaModel(provider_routes or []),
        capital_conversion_quote_model=_FakeReplicaModel(
            capital_conversion_quotes or []
        ),
        transaction_intent_model=_FakeReplicaModel(transaction_intents or []),
        transaction_external_model=_FakeReplicaModel(transaction_externals or []),
        transaction_model=_FakeReplicaModel(transactions or []),
        provider_lifecycle_receipt_model=_FakeReplicaModel(
            provider_lifecycle_receipts or []
        ),
        escrow_model=_FakeReplicaModel(escrows or []),
        smart_contract_reservation_model=_FakeReplicaModel(reservations or []),
        smart_contract_settlement_model=_FakeReplicaModel(settlements or []),
    )
