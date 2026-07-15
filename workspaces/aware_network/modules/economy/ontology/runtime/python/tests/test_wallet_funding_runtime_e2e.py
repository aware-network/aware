from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from ._economy_runtime_test_paths import REPO_ROOT, economy_package_manifest_paths
from aware_economy.handlers._generated import meta_handlers as economy_meta_handlers
from aware_economy.wallet_funding import (
    EconomyWalletFundingOperationContext,
    describe_wallet_balance,
    prepare_wallet_funding,
    record_verified_wallet_funding,
    record_wallet_funding_expiration,
    resolve_economy_wallet_funding_runtime_context,
)
from aware_economy.wallet_custody import derive_wallet_custody_material
from aware_economy_ontology.stable_ids import (
    stable_coin_id,
    stable_wallet_id,
    stable_wallet_public_id,
)
from aware_economy_ontology.external_capital.external_capital_enums import (
    ExternalCapitalConversionMode,
)
from aware_economy_ontology.wallet.wallet import Wallet
from aware_economy_ontology.transaction.transaction_external import TransactionExternal
from aware_economy_ontology.transaction.transaction_intent import TransactionIntent
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import IsolatedMetaAwareRoot as IsolatedAwareRoot


_ECONOMY_META_HANDLERS_ANY: Any = economy_meta_handlers
_ECONOMY_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _ECONOMY_META_HANDLERS_ANY,
)
_ECONOMY_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _ECONOMY_META_HANDLERS_ANY,
)


@dataclass(frozen=True, slots=True)
class _WalletRef:
    wallet_id: UUID
    wallet_public_id: UUID


def _build_economy_meta_runtime(
    *,
    aware_root,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=economy_package_manifest_paths(REPO_ROOT),
        workspace_root=REPO_ROOT,
        aware_root=aware_root,
        handler_modules=(_ECONOMY_META_HANDLER_MODULE,),
        bootstrap_modules=(_ECONOMY_META_BOOTSTRAP_MODULE,),
    )
    assert runtime.context is not None
    return runtime


async def _commit_wallet_lane(
    *,
    runtime: MetaGraphRuntime,
    projection_hash: str,
    actor_id: UUID,
) -> _WalletRef:
    custody = derive_wallet_custody_material(
        identity_id=uuid4(),
        role_key="primary",
    )
    public_key = custody.public_key
    private_key_encrypted = custody.private_key_encrypted
    wallet_id = stable_wallet_id(
        public_key=public_key,
        private_key_encrypted=private_key_encrypted,
    )
    wallet_public_id = stable_wallet_public_id(public_key=public_key)

    lane = runtime.bind(
        branch_id=wallet_id,
        projection=projection_hash,
        actor_id=actor_id,
    )
    with lane.activate(commit=True, publish=False):
        wallet = await Wallet.build(
            address=custody.address,
            public_key=public_key,
            private_key_encrypted=private_key_encrypted,
        )

    assert wallet.id == wallet_id
    assert wallet.wallet_public_id == wallet_public_id
    return _WalletRef(wallet_id=wallet_id, wallet_public_id=wallet_public_id)


@pytest.mark.asyncio
async def test_wallet_funding_prepare_requires_committed_recipient_wallet(
    tmp_path,
) -> None:
    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_economy_meta_runtime(aware_root=aware_root)
        assert runtime.context is not None
        runtime_context = resolve_economy_wallet_funding_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )

        with pytest.raises(RuntimeError, match="missing Wallet"):
            await prepare_wallet_funding(
                runtime_context=runtime_context,
                operation_context=EconomyWalletFundingOperationContext(
                    actor_id=uuid4(),
                ),
                provider_config_id=uuid4(),
                provider_route_id=uuid4(),
                provider_finance_entity_id=uuid4(),
                recipient_finance_entity_id=uuid4(),
                recipient_wallet_id=uuid4(),
                recipient_wallet_public_id=uuid4(),
                coin_id=uuid4(),
                amount=Decimal("10.0"),
                funding_intent_key="funding-missing-wallet",
                idempotency_key="idem-missing-wallet",
                provider_key="external-provider-test",
                external_currency="USD",
                external_minor_unit_exponent=2,
                conversion_mode=ExternalCapitalConversionMode.direct_denomination,
                created_at=datetime(2026, 7, 10, 8, 30, tzinfo=UTC),
                commit=True,
                publish=False,
            )


@pytest.mark.asyncio
async def test_wallet_funding_records_external_capital_into_wallet_balance(
    tmp_path,
) -> None:
    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_economy_meta_runtime(aware_root=aware_root)
        assert runtime.context is not None
        runtime_context = resolve_economy_wallet_funding_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )
        actor_id = uuid4()
        wallet_ref = await _commit_wallet_lane(
            runtime=runtime,
            projection_hash=runtime_context.lanes.wallet_projection_hash,
            actor_id=actor_id,
        )
        operation_context = EconomyWalletFundingOperationContext(actor_id=actor_id)

        provider_finance_entity_id = uuid4()
        provider_config_id = uuid4()
        provider_route_id = uuid4()
        recipient_finance_entity_id = uuid4()
        coin_id = stable_coin_id(symbol="USD")
        amount = Decimal("12.25")
        funding_intent_key = "funding-runtime-e2e"
        quote_captured_at = datetime(2026, 7, 10, 8, 30, tzinfo=UTC)

        prepare_receipt = await prepare_wallet_funding(
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
            funding_intent_key=funding_intent_key,
            idempotency_key="idem-prepare-runtime-e2e",
            provider_key="external-provider-test",
            external_currency="USD",
            external_minor_unit_exponent=2,
            conversion_mode=ExternalCapitalConversionMode.direct_denomination,
            created_at=quote_captured_at,
            commit=True,
            publish=True,
        )
        assert prepare_receipt.idempotent_replay is False
        assert prepare_receipt.external_amount_minor == 1225
        assert prepare_receipt.external_currency == "USD"

        replay_prepare = await prepare_wallet_funding(
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
            funding_intent_key=funding_intent_key,
            idempotency_key="idem-prepare-runtime-e2e",
            provider_key="external-provider-test",
            external_currency="USD",
            external_minor_unit_exponent=2,
            conversion_mode=ExternalCapitalConversionMode.direct_denomination,
            created_at=quote_captured_at,
            commit=True,
            publish=True,
        )
        assert replay_prepare.transaction_intent_id == prepare_receipt.transaction_intent_id
        assert replay_prepare.idempotent_replay is True

        record_receipt = await record_verified_wallet_funding(
            runtime_context=runtime_context,
            operation_context=operation_context,
            transaction_intent_id=prepare_receipt.transaction_intent_id,
            transaction_intent_commit_id=(prepare_receipt.transaction_intent_commit_id),
            provider_config_id=provider_config_id,
            provider_finance_entity_id=provider_finance_entity_id,
            provider_key="external-provider-test",
            provider_event_id="provider-event-runtime-e2e",
            idempotency_key="idem-record-runtime-e2e",
            capital_conversion_quote_id=(prepare_receipt.capital_conversion_quote_id),
            quote_hash=prepare_receipt.quote_hash,
            external_amount_minor=prepare_receipt.external_amount_minor,
            external_currency=prepare_receipt.external_currency,
            provider_public_reference="provider-intent-evidence",
            provider_payload_hash="sha256:" + "a" * 64,
            external_created_at=quote_captured_at + timedelta(minutes=1),
            commit=True,
            publish=True,
        )
        assert record_receipt.previous_balance == Decimal("0")
        assert record_receipt.new_balance == amount
        assert record_receipt.capital_conversion_quote_id == prepare_receipt.capital_conversion_quote_id
        assert record_receipt.idempotent_replay is False

        balance = await describe_wallet_balance(
            runtime_context=runtime_context,
            wallet_id=wallet_ref.wallet_id,
            coin_id=coin_id,
        )
        assert balance.ready is True
        assert balance.balance == amount

        replay_record = await record_verified_wallet_funding(
            runtime_context=runtime_context,
            operation_context=operation_context,
            transaction_intent_id=prepare_receipt.transaction_intent_id,
            transaction_intent_commit_id=(prepare_receipt.transaction_intent_commit_id),
            provider_config_id=provider_config_id,
            provider_finance_entity_id=provider_finance_entity_id,
            provider_key="external-provider-test",
            provider_event_id="provider-event-runtime-e2e",
            idempotency_key="idem-record-runtime-e2e",
            capital_conversion_quote_id=(prepare_receipt.capital_conversion_quote_id),
            quote_hash=prepare_receipt.quote_hash,
            external_amount_minor=prepare_receipt.external_amount_minor,
            external_currency=prepare_receipt.external_currency,
            provider_public_reference="provider-intent-evidence",
            provider_payload_hash="sha256:" + "a" * 64,
            external_created_at=quote_captured_at + timedelta(minutes=1),
            commit=True,
            publish=True,
        )
        assert replay_record.idempotent_replay is True
        assert replay_record.new_balance == amount


@pytest.mark.asyncio
async def test_wallet_funding_expiration_cancels_without_credit_and_replays(
    tmp_path,
) -> None:
    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_economy_meta_runtime(aware_root=aware_root)
        assert runtime.context is not None
        runtime_context = resolve_economy_wallet_funding_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )
        actor_id = uuid4()
        wallet_ref = await _commit_wallet_lane(
            runtime=runtime,
            projection_hash=runtime_context.lanes.wallet_projection_hash,
            actor_id=actor_id,
        )
        operation_context = EconomyWalletFundingOperationContext(actor_id=actor_id)
        provider_config_id = uuid4()
        provider_finance_entity_id = uuid4()
        coin_id = stable_coin_id(symbol="USD")
        quote_captured_at = datetime(2026, 7, 10, 8, 30, tzinfo=UTC)
        prepare_receipt = await prepare_wallet_funding(
            runtime_context=runtime_context,
            operation_context=operation_context,
            provider_config_id=provider_config_id,
            provider_route_id=uuid4(),
            provider_finance_entity_id=provider_finance_entity_id,
            recipient_finance_entity_id=uuid4(),
            recipient_wallet_id=wallet_ref.wallet_id,
            recipient_wallet_public_id=wallet_ref.wallet_public_id,
            coin_id=coin_id,
            amount=Decimal("19.75"),
            funding_intent_key="funding-expiration-e2e",
            idempotency_key="idem-prepare-expiration-e2e",
            provider_key="external-provider-test",
            external_currency="USD",
            external_minor_unit_exponent=2,
            conversion_mode=ExternalCapitalConversionMode.direct_denomination,
            created_at=quote_captured_at,
            commit=True,
            publish=False,
        )
        cancel_kwargs = {
            "runtime_context": runtime_context,
            "operation_context": operation_context,
            "transaction_intent_id": prepare_receipt.transaction_intent_id,
            "transaction_intent_commit_id": (prepare_receipt.transaction_intent_commit_id),
            "provider_config_id": provider_config_id,
            "provider_key": "external-provider-test",
            "provider_event_id": "provider-event-expiration-e2e",
            "idempotency_key": "idem-expiration-e2e",
            "capital_conversion_quote_id": (prepare_receipt.capital_conversion_quote_id),
            "quote_hash": prepare_receipt.quote_hash,
            "provider_public_reference": "provider-session-expired-e2e",
            "provider_payload_hash": "sha256:" + "c" * 64,
            "external_created_at": quote_captured_at + timedelta(minutes=30),
            "commit": True,
            "publish": False,
        }

        canceled = await record_wallet_funding_expiration(**cancel_kwargs)  # type: ignore[arg-type]
        replay = await record_wallet_funding_expiration(**cancel_kwargs)  # type: ignore[arg-type]
        balance = await describe_wallet_balance(
            runtime_context=runtime_context,
            wallet_id=wallet_ref.wallet_id,
            coin_id=coin_id,
        )

        assert canceled.status == "canceled"
        assert canceled.idempotent_replay is False
        assert replay.idempotent_replay is True
        assert replay.transaction_intent_external_expiration_id == (canceled.transaction_intent_external_expiration_id)
        assert balance.balance == Decimal("0")

        with pytest.raises(ValueError, match="committed context mismatch"):
            await record_wallet_funding_expiration(
                **{**cancel_kwargs, "quote_hash": "d" * 64}  # type: ignore[arg-type]
            )


@pytest.mark.parametrize(
    "failure_stage",
    ("external_provenance", "wallet_application", "intent_confirmation"),
)
@pytest.mark.asyncio
async def test_wallet_funding_recovers_each_partial_commit_without_double_credit(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    failure_stage: str,
) -> None:
    with IsolatedAwareRoot(
        tmp_path / failure_stage,
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_economy_meta_runtime(aware_root=aware_root)
        assert runtime.context is not None
        runtime_context = resolve_economy_wallet_funding_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )
        actor_id = uuid4()
        wallet_ref = await _commit_wallet_lane(
            runtime=runtime,
            projection_hash=runtime_context.lanes.wallet_projection_hash,
            actor_id=actor_id,
        )
        operation_context = EconomyWalletFundingOperationContext(actor_id=actor_id)
        provider_config_id = uuid4()
        provider_finance_entity_id = uuid4()
        coin_id = stable_coin_id(symbol="USD")
        amount = Decimal("7.50")
        quote_captured_at = datetime(2026, 7, 10, 9, 0, tzinfo=UTC)
        prepare_receipt = await prepare_wallet_funding(
            runtime_context=runtime_context,
            operation_context=operation_context,
            provider_config_id=provider_config_id,
            provider_route_id=uuid4(),
            provider_finance_entity_id=provider_finance_entity_id,
            recipient_finance_entity_id=uuid4(),
            recipient_wallet_id=wallet_ref.wallet_id,
            recipient_wallet_public_id=wallet_ref.wallet_public_id,
            coin_id=coin_id,
            amount=amount,
            funding_intent_key=f"partial-{failure_stage}",
            idempotency_key=f"idem-prepare-{failure_stage}",
            provider_key="external-provider-test",
            external_currency="USD",
            external_minor_unit_exponent=2,
            conversion_mode=ExternalCapitalConversionMode.direct_denomination,
            created_at=quote_captured_at,
            commit=True,
            publish=False,
        )
        record_kwargs = {
            "runtime_context": runtime_context,
            "operation_context": operation_context,
            "transaction_intent_id": prepare_receipt.transaction_intent_id,
            "transaction_intent_commit_id": (prepare_receipt.transaction_intent_commit_id),
            "provider_config_id": provider_config_id,
            "provider_finance_entity_id": provider_finance_entity_id,
            "provider_key": "external-provider-test",
            "provider_event_id": f"provider-event-{failure_stage}",
            "idempotency_key": f"idem-record-{failure_stage}",
            "capital_conversion_quote_id": (prepare_receipt.capital_conversion_quote_id),
            "quote_hash": prepare_receipt.quote_hash,
            "external_amount_minor": prepare_receipt.external_amount_minor,
            "external_currency": prepare_receipt.external_currency,
            "provider_public_reference": f"provider-reference-{failure_stage}",
            "provider_payload_hash": "sha256:" + "b" * 64,
            "external_created_at": quote_captured_at + timedelta(minutes=1),
            "commit": True,
            "publish": False,
        }

        async def _fail_external_provenance(**_kwargs: object) -> object:
            raise RuntimeError("injected failure after ingress transaction")

        async def _fail_wallet_application(
            _wallet: Wallet,
            **_kwargs: object,
        ) -> object:
            raise RuntimeError("injected failure after external provenance")

        async def _fail_intent_confirmation(
            _intent: TransactionIntent,
            **_kwargs: object,
        ) -> object:
            raise RuntimeError("injected failure after wallet application")

        with monkeypatch.context() as scoped:
            if failure_stage == "external_provenance":
                scoped.setattr(
                    TransactionExternal,
                    "record",
                    staticmethod(_fail_external_provenance),
                )
            elif failure_stage == "wallet_application":
                scoped.setattr(
                    Wallet,
                    "apply_external_ingress",
                    _fail_wallet_application,
                )
            else:
                scoped.setattr(
                    TransactionIntent,
                    "confirm",
                    _fail_intent_confirmation,
                )
            with pytest.raises(RuntimeError, match="injected failure"):
                await record_verified_wallet_funding(**record_kwargs)  # type: ignore[arg-type]

        balance_after_failure = await describe_wallet_balance(
            runtime_context=runtime_context,
            wallet_id=wallet_ref.wallet_id,
            coin_id=coin_id,
        )
        if failure_stage == "intent_confirmation":
            assert balance_after_failure.balance == amount
        else:
            assert balance_after_failure.balance == Decimal("0")

        recovered = await record_verified_wallet_funding(**record_kwargs)  # type: ignore[arg-type]
        replay = await record_verified_wallet_funding(**record_kwargs)  # type: ignore[arg-type]
        final_balance = await describe_wallet_balance(
            runtime_context=runtime_context,
            wallet_id=wallet_ref.wallet_id,
            coin_id=coin_id,
        )

        assert recovered.idempotent_replay is False
        assert replay.idempotent_replay is True
        assert recovered.wallet_external_ingress_application_id == (replay.wallet_external_ingress_application_id)
        assert final_balance.balance == amount
