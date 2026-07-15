from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from .test_wallet_funding_runtime_e2e import (
    _WalletRef,
    _build_economy_meta_runtime,
    _commit_wallet_lane,
)
from aware_economy.provider_lifecycle import (
    EconomyProviderLifecycleOperationContext,
    record_provider_lifecycle_event,
    resolve_economy_provider_lifecycle_runtime_context,
)
from aware_economy.wallet_funding import (
    EconomyWalletFundingOperationContext,
    WalletFundingRecordReceipt,
    describe_wallet_balance,
    prepare_wallet_funding,
    record_verified_wallet_funding,
    resolve_economy_wallet_funding_runtime_context,
)
from aware_economy_ontology.external_capital.external_capital_enums import (
    ExternalCapitalConversionMode,
)
from aware_economy_ontology.stable_ids import stable_coin_id
from aware_meta.runtime.testing import IsolatedMetaAwareRoot as IsolatedAwareRoot


async def _fund_wallet(
    *,
    runtime,
    actor_id: UUID,
    wallet_ref: _WalletRef,
    coin_id: UUID,
    amount: Decimal,
) -> WalletFundingRecordReceipt:
    assert runtime.context is not None
    runtime_context = resolve_economy_wallet_funding_runtime_context(
        lane_binder=runtime,
        index=runtime.context.index,
    )
    operation_context = EconomyWalletFundingOperationContext(actor_id=actor_id)
    provider_config_id = uuid4()
    provider_route_id = uuid4()
    provider_finance_entity_id = uuid4()
    recipient_finance_entity_id = uuid4()
    created_at = datetime(2026, 7, 10, 8, 30, tzinfo=UTC)

    prepared = await prepare_wallet_funding(
        runtime_context=runtime_context,
        operation_context=operation_context,
        provider_config_id=provider_config_id,
        provider_route_id=provider_route_id,
        provider_finance_entity_id=provider_finance_entity_id,
        recipient_finance_entity_id=recipient_finance_entity_id,
        recipient_wallet_id=wallet_ref.wallet_id,
        recipient_wallet_public_id=wallet_ref.wallet_public_id,
        coin_id=coin_id,
        amount=amount,
        funding_intent_key=f"provider-lifecycle-funding-{uuid4()}",
        idempotency_key=f"idem-prepare-{uuid4()}",
        provider_key="external-provider-test",
        external_currency="USD",
        external_minor_unit_exponent=2,
        conversion_mode=ExternalCapitalConversionMode.direct_denomination,
        created_at=created_at,
        commit=True,
        publish=False,
    )
    return await record_verified_wallet_funding(
        runtime_context=runtime_context,
        operation_context=operation_context,
        transaction_intent_id=prepared.transaction_intent_id,
        transaction_intent_commit_id=prepared.transaction_intent_commit_id,
        provider_config_id=provider_config_id,
        provider_finance_entity_id=provider_finance_entity_id,
        provider_key="external-provider-test",
        provider_event_id=f"provider-lifecycle-funding-{uuid4()}",
        idempotency_key=f"idem-record-{uuid4()}",
        capital_conversion_quote_id=prepared.capital_conversion_quote_id,
        quote_hash=prepared.quote_hash,
        external_amount_minor=prepared.external_amount_minor,
        external_currency=prepared.external_currency,
        provider_public_reference="provider-payment-evidence",
        provider_payload_hash="sha256:" + "a" * 64,
        external_created_at=created_at + timedelta(minutes=1),
        commit=True,
        publish=False,
    )


async def _record_lifecycle(
    *,
    lifecycle_context,
    actor_id: UUID,
    wallet_ref: _WalletRef,
    funding: WalletFundingRecordReceipt,
    coin_id: UUID,
    provider_event_id: str,
    provider_lifecycle_object_id: str,
    event_kind: str,
    amount: Decimal,
    provider_payload_hash: str = "sha256:lifecycle-event",
):
    return await record_provider_lifecycle_event(
        runtime_context=lifecycle_context,
        operation_context=EconomyProviderLifecycleOperationContext(
            actor_id=actor_id,
        ),
        provider_finance_entity_id=funding.provider_finance_entity_id,
        provider_key="external-provider-test",
        provider_event_id=provider_event_id,
        provider_lifecycle_object_id=provider_lifecycle_object_id,
        provider_lifecycle_effect_key=event_kind,
        wallet_finance_entity_id=funding.recipient_finance_entity_id,
        wallet_id=wallet_ref.wallet_id,
        wallet_public_id=wallet_ref.wallet_public_id,
        coin_id=coin_id,
        amount=amount,
        event_kind=event_kind,
        provider_payment_reference="provider-payment-evidence",
        provider_payload_hash=provider_payload_hash,
        external_created_at=datetime(2026, 7, 10, 9, 0, tzinfo=UTC),
        metadata_json={"source": "provider-lifecycle-e2e"},
        transaction_id=funding.transaction_id,
        transaction_external_id=funding.transaction_external_id,
        commit=True,
        publish=False,
    )


async def _funded_context(tmp_path, *, amount: Decimal):
    aware_root_context = IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    )
    aware_root = aware_root_context.__enter__()
    runtime = _build_economy_meta_runtime(aware_root=aware_root)
    assert runtime.context is not None
    wallet_funding_context = resolve_economy_wallet_funding_runtime_context(
        lane_binder=runtime,
        index=runtime.context.index,
    )
    lifecycle_context = resolve_economy_provider_lifecycle_runtime_context(
        lane_binder=runtime,
        index=runtime.context.index,
    )
    actor_id = uuid4()
    wallet_ref = await _commit_wallet_lane(
        runtime=runtime,
        projection_hash=wallet_funding_context.lanes.wallet_projection_hash,
        actor_id=actor_id,
    )
    coin_id = stable_coin_id(symbol="USD")
    funding = await _fund_wallet(
        runtime=runtime,
        actor_id=actor_id,
        wallet_ref=wallet_ref,
        coin_id=coin_id,
        amount=amount,
    )
    return (
        aware_root_context,
        wallet_funding_context,
        lifecycle_context,
        actor_id,
        wallet_ref,
        coin_id,
        funding,
    )


@pytest.mark.asyncio
async def test_provider_lifecycle_debits_wallet_and_replays_by_effect_identity(
    tmp_path,
) -> None:
    (
        aware_root,
        wallet_funding_context,
        lifecycle_context,
        actor_id,
        wallet_ref,
        coin_id,
        funding,
    ) = await _funded_context(tmp_path, amount=Decimal("30"))
    try:
        receipt = await _record_lifecycle(
            lifecycle_context=lifecycle_context,
            actor_id=actor_id,
            wallet_ref=wallet_ref,
            funding=funding,
            coin_id=coin_id,
            provider_event_id="evt_refund_created",
            provider_lifecycle_object_id="re_wallet_1",
            event_kind="refund",
            amount=Decimal("5"),
        )
        assert receipt.status == "applied"
        assert receipt.previous_balance == Decimal("30")
        assert receipt.new_balance == Decimal("25")
        assert receipt.idempotency_key == ("external-provider-test:lifecycle:re_wallet_1:refund")

        replay = await _record_lifecycle(
            lifecycle_context=lifecycle_context,
            actor_id=actor_id,
            wallet_ref=wallet_ref,
            funding=funding,
            coin_id=coin_id,
            provider_event_id="evt_refund_updated",
            provider_lifecycle_object_id="re_wallet_1",
            event_kind="refund",
            amount=Decimal("5"),
            provider_payload_hash="sha256:updated-delivery",
        )
        assert replay.provider_lifecycle_receipt_id == (receipt.provider_lifecycle_receipt_id)
        assert replay.provider_event_id == "evt_refund_created"
        assert replay.new_balance == Decimal("25")
        assert replay.idempotent_replay is True

        balance = await describe_wallet_balance(
            runtime_context=wallet_funding_context,
            wallet_id=wallet_ref.wallet_id,
            coin_id=coin_id,
        )
        assert balance.balance == Decimal("25")
    finally:
        aware_root.__exit__(None, None, None)


@pytest.mark.asyncio
async def test_provider_lifecycle_dispute_chargeback_settles_held_balance(
    tmp_path,
) -> None:
    (
        aware_root,
        _,
        lifecycle_context,
        actor_id,
        wallet_ref,
        coin_id,
        funding,
    ) = await _funded_context(tmp_path, amount=Decimal("30"))
    try:
        dispute = await _record_lifecycle(
            lifecycle_context=lifecycle_context,
            actor_id=actor_id,
            wallet_ref=wallet_ref,
            funding=funding,
            coin_id=coin_id,
            provider_event_id="evt_dispute_created",
            provider_lifecycle_object_id="du_wallet_1",
            event_kind="dispute",
            amount=Decimal("10"),
        )
        assert dispute.status == "held"
        assert dispute.new_balance == Decimal("30")
        assert dispute.new_held_balance == Decimal("10")
        assert dispute.new_available_balance == Decimal("20")

        chargeback = await _record_lifecycle(
            lifecycle_context=lifecycle_context,
            actor_id=actor_id,
            wallet_ref=wallet_ref,
            funding=funding,
            coin_id=coin_id,
            provider_event_id="evt_dispute_closed",
            provider_lifecycle_object_id="du_wallet_1",
            event_kind="chargeback",
            amount=Decimal("10"),
        )
        assert chargeback.status == "applied"
        assert chargeback.new_balance == Decimal("20")
        assert chargeback.new_held_balance == Decimal("0")
        assert chargeback.new_available_balance == Decimal("20")
    finally:
        aware_root.__exit__(None, None, None)


@pytest.mark.asyncio
async def test_provider_lifecycle_rejects_insufficient_available_balance(
    tmp_path,
) -> None:
    (
        aware_root,
        _,
        lifecycle_context,
        actor_id,
        wallet_ref,
        coin_id,
        funding,
    ) = await _funded_context(tmp_path, amount=Decimal("5"))
    try:
        with pytest.raises(ValueError, match="insufficient wallet available balance"):
            await _record_lifecycle(
                lifecycle_context=lifecycle_context,
                actor_id=actor_id,
                wallet_ref=wallet_ref,
                funding=funding,
                coin_id=coin_id,
                provider_event_id="evt_refund_too_large",
                provider_lifecycle_object_id="re_wallet_too_large",
                event_kind="refund",
                amount=Decimal("6"),
            )
    finally:
        aware_root.__exit__(None, None, None)


@pytest.mark.asyncio
async def test_provider_lifecycle_chargeback_requires_held_balance(tmp_path) -> None:
    (
        aware_root,
        _,
        lifecycle_context,
        actor_id,
        wallet_ref,
        coin_id,
        funding,
    ) = await _funded_context(tmp_path, amount=Decimal("30"))
    try:
        with pytest.raises(ValueError, match="insufficient held balance"):
            await _record_lifecycle(
                lifecycle_context=lifecycle_context,
                actor_id=actor_id,
                wallet_ref=wallet_ref,
                funding=funding,
                coin_id=coin_id,
                provider_event_id="evt_chargeback_without_dispute",
                provider_lifecycle_object_id="du_missing_open",
                event_kind="chargeback",
                amount=Decimal("10"),
            )
    finally:
        aware_root.__exit__(None, None, None)
