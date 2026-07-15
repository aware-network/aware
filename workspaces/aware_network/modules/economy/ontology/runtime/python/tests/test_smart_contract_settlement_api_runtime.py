from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from ._economy_runtime_test_paths import REPO_ROOT, economy_package_manifest_paths
from aware_economy.handlers._generated import meta_handlers as economy_meta_handlers
from aware_economy.smart_contract_settlement import (
    EconomySmartContractSettlementOperationContext,
    finalize_smart_contract_settlement,
    prepare_smart_contract_reservation,
    release_smart_contract_reservation,
    resolve_economy_smart_contract_settlement_runtime_context,
)
from aware_economy.wallet_funding import (
    describe_wallet_balance,
    resolve_economy_wallet_funding_runtime_context,
)
from aware_economy.wallet_custody import derive_wallet_custody_material
from aware_economy_ontology.price.price import Price
from aware_economy_ontology.price.price_enums import PriceType
from aware_economy_ontology.smart_contract.smart_contract import SmartContract
from aware_economy_ontology.smart_contract.smart_contract_enums import (
    SmartContractMemberType,
    SmartContractType,
)
from aware_economy_ontology.smart_contract.smart_contract_reservation_enums import (
    ReservationStatus,
)
from aware_economy_ontology.stable_ids import (
    stable_price_id,
    stable_price_schedule_id,
    stable_pricing_policy_id,
    stable_rate_snapshot_id,
    stable_smart_contract_config_id,
    stable_smart_contract_id,
    stable_smart_contract_permit_id,
    stable_smart_contract_reservation_id,
    stable_smart_contract_settlement_id,
    stable_transaction_id,
    stable_wallet_id,
    stable_wallet_public_id,
)
from aware_economy_ontology.wallet.wallet import Wallet
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
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


@dataclass(frozen=True, slots=True)
class _SettlementFixture:
    actor_id: UUID
    smart_contract_id: UUID
    permit_id: UUID
    payer_finance_entity_id: UUID
    payer_wallet_id: UUID
    payer_wallet_public_id: UUID
    receiver_finance_entity_id: UUID
    receiver_wallet_id: UUID
    receiver_wallet_public_id: UUID
    coin_id: UUID
    rate_snapshot_id: UUID


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
    coin_id: UUID,
    initial_balance: Decimal,
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
        await wallet.set_coin_balance(
            coin_id=coin_id,
            balance=initial_balance,
        )

    return _WalletRef(wallet_id=wallet_id, wallet_public_id=wallet_public_id)


async def _commit_price_lane(
    *,
    runtime: MetaGraphRuntime,
    projection_hash: str,
    actor_id: UUID,
    branch_id: UUID,
    coin_id: UUID,
) -> UUID:
    pricing_policy_id = stable_pricing_policy_id(
        name="api-settlement-policy",
        version=1,
    )
    price_id = stable_price_id(
        coin_id=coin_id,
        name="api-settlement-price",
        type=PriceType.fixed.value,
    )
    price_schedule_id = stable_price_schedule_id(
        price_id=price_id,
        pricing_policy_id=pricing_policy_id,
        name="default",
        version=1,
    )
    rate_snapshot_id = stable_rate_snapshot_id(
        price_schedule_id=price_schedule_id,
        snapshot_key="api-settlement-v1",
    )

    lane = runtime.bind(
        branch_id=branch_id,
        projection=projection_hash,
        actor_id=actor_id,
    )
    with lane.activate(commit=True, publish=False):
        price = await Price.build(
            coin_id=coin_id,
            name="api-settlement-price",
            type=PriceType.fixed,
        )
        schedule = await price.create_price_schedule(
            pricing_policy_id=pricing_policy_id,
            name="default",
            effective_from=datetime(2026, 1, 1, tzinfo=UTC),
            version=1,
            fixed_amount=Decimal("10.0"),
        )
        await schedule.capture_rate_snapshot(
            snapshot_key="api-settlement-v1",
            quoted_amount=Decimal("10.0"),
            captured_at=datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC),
        )

    return rate_snapshot_id


async def _commit_smart_contract_lane(
    *,
    runtime: MetaGraphRuntime,
    projection_hash: str,
    actor_id: UUID,
    smart_contract_id: UUID,
    payer_finance_entity_id: UUID,
    receiver_finance_entity_id: UUID,
    price_schedule_id: UUID,
    coin_id: UUID,
) -> UUID:
    permit_nonce = 1
    permit_id = stable_smart_contract_permit_id(
        smart_contract_id=smart_contract_id,
        finance_entity_id=payer_finance_entity_id,
        permit_nonce=permit_nonce,
    )
    smart_contract_config_id = stable_smart_contract_config_id(
        name="ApiSettlement",
        type=SmartContractType.utility.value,
    )

    lane = runtime.bind(
        branch_id=smart_contract_id,
        projection=projection_hash,
        actor_id=actor_id,
    )
    with lane.activate(commit=True, publish=False):
        smart_contract = await SmartContract.build_via_smart_contract_config(
            smart_contract_config_id=smart_contract_config_id,
            blockchain_address="dev:api-settlement",
        )
        assert smart_contract.id == smart_contract_id
        await smart_contract.add_member(
            finance_entity_id=payer_finance_entity_id,
            type=SmartContractMemberType.payer,
        )
        await smart_contract.add_member(
            finance_entity_id=receiver_finance_entity_id,
            type=SmartContractMemberType.receiver,
        )
        await smart_contract.open_session_permit(
            finance_entity_id=payer_finance_entity_id,
            permit_nonce=permit_nonce,
            cap_amount=Decimal("50.0"),
            expires_at=datetime.now(UTC) + timedelta(hours=2),
            price_schedule_id=price_schedule_id,
            coin_id=coin_id,
        )

    return permit_id


async def _build_settlement_fixture(
    *,
    runtime: MetaGraphRuntime,
    payer_initial_balance: Decimal,
) -> _SettlementFixture:
    assert runtime.context is not None
    opgs = {opg.name: opg for opg in runtime.context.index.opg_by_hash.values()}
    actor_id = uuid4()
    coin_id = uuid4()
    smart_contract_config_id = stable_smart_contract_config_id(
        name="ApiSettlement",
        type=SmartContractType.utility.value,
    )
    smart_contract_id = stable_smart_contract_id(
        smart_contract_config_id=smart_contract_config_id,
        blockchain_address="dev:api-settlement",
    )
    price_id = stable_price_id(
        coin_id=coin_id,
        name="api-settlement-price",
        type=PriceType.fixed.value,
    )
    pricing_policy_id = stable_pricing_policy_id(
        name="api-settlement-policy",
        version=1,
    )
    price_schedule_id = stable_price_schedule_id(
        price_id=price_id,
        pricing_policy_id=pricing_policy_id,
        name="default",
        version=1,
    )

    payer_finance_entity_id = uuid4()
    receiver_finance_entity_id = uuid4()
    payer_wallet = await _commit_wallet_lane(
        runtime=runtime,
        projection_hash=opgs["Wallet"].projection_hash,
        actor_id=actor_id,
        coin_id=coin_id,
        initial_balance=payer_initial_balance,
    )
    receiver_wallet = await _commit_wallet_lane(
        runtime=runtime,
        projection_hash=opgs["Wallet"].projection_hash,
        actor_id=actor_id,
        coin_id=coin_id,
        initial_balance=Decimal("1.0"),
    )
    rate_snapshot_id = await _commit_price_lane(
        runtime=runtime,
        projection_hash=opgs["Price"].projection_hash,
        actor_id=actor_id,
        branch_id=smart_contract_id,
        coin_id=coin_id,
    )
    permit_id = await _commit_smart_contract_lane(
        runtime=runtime,
        projection_hash=opgs["SmartContract"].projection_hash,
        actor_id=actor_id,
        smart_contract_id=smart_contract_id,
        payer_finance_entity_id=payer_finance_entity_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        price_schedule_id=price_schedule_id,
        coin_id=coin_id,
    )

    return _SettlementFixture(
        actor_id=actor_id,
        smart_contract_id=smart_contract_id,
        permit_id=permit_id,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_id=payer_wallet.wallet_id,
        payer_wallet_public_id=payer_wallet.wallet_public_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_id=receiver_wallet.wallet_id,
        receiver_wallet_public_id=receiver_wallet.wallet_public_id,
        coin_id=coin_id,
        rate_snapshot_id=rate_snapshot_id,
    )


@pytest.mark.asyncio
async def test_smart_contract_settlement_reconciles_aware_wallet_balances(
    tmp_path,
) -> None:
    import aware_economy_ontology  # noqa: F401

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_economy_meta_runtime(aware_root=aware_root)
        assert runtime.context is not None
        runtime_context = resolve_economy_smart_contract_settlement_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )
        wallet_context = resolve_economy_wallet_funding_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )
        fixture = await _build_settlement_fixture(
            runtime=runtime,
            payer_initial_balance=Decimal("30.0"),
        )
        operation_context = EconomySmartContractSettlementOperationContext(
            actor_id=fixture.actor_id,
        )
        reservation_id = stable_smart_contract_reservation_id(
            smart_contract_permit_id=fixture.permit_id,
            op_nonce=1,
        )
        settlement_id = stable_smart_contract_settlement_id(
            smart_contract_reservation_id=reservation_id,
        )
        transaction_id = stable_transaction_id(
            capital_origin_id=fixture.payer_wallet_public_id,
            target_wallet_public_id=fixture.receiver_wallet_public_id,
            coin_id=fixture.coin_id,
            nonce=1,
        )

        prepare = await prepare_smart_contract_reservation(
            runtime_context=runtime_context,
            operation_context=operation_context,
            smart_contract_id=fixture.smart_contract_id,
            permit_id=fixture.permit_id,
            permit_nonce=1,
            payer_finance_entity_id=fixture.payer_finance_entity_id,
            payer_wallet_id=fixture.payer_wallet_id,
            payer_wallet_public_id=fixture.payer_wallet_public_id,
            args_hash="args-hash-1",
            max_cost=Decimal("10.0"),
            rate_snapshot_id=fixture.rate_snapshot_id,
            deadline=datetime.now(UTC) + timedelta(minutes=30),
            coin_id=fixture.coin_id,
            commit=True,
            publish=False,
        )
        assert prepare.op_nonce == 1
        assert prepare.reservation_id == reservation_id
        assert prepare.payer_balance == Decimal("30.0")
        assert prepare.payer_held_balance == Decimal("10.0")
        assert prepare.payer_available_balance == Decimal("20.0")
        assert prepare.status == "pending"
        assert prepare.idempotent_replay is False

        finalize = await finalize_smart_contract_settlement(
            runtime_context=runtime_context,
            operation_context=operation_context,
            smart_contract_id=fixture.smart_contract_id,
            permit_id=fixture.permit_id,
            reservation_id=reservation_id,
            payer_finance_entity_id=fixture.payer_finance_entity_id,
            payer_wallet_id=fixture.payer_wallet_id,
            payer_wallet_public_id=fixture.payer_wallet_public_id,
            receiver_finance_entity_id=fixture.receiver_finance_entity_id,
            receiver_wallet_id=fixture.receiver_wallet_id,
            receiver_wallet_public_id=fixture.receiver_wallet_public_id,
            coin_id=fixture.coin_id,
            final_cost=Decimal("7.0"),
            commit=True,
            publish=False,
        )
        assert finalize.settlement_id == settlement_id
        assert finalize.transaction_id == transaction_id
        assert finalize.payer_previous_balance == Decimal("30.0")
        assert finalize.payer_new_balance == Decimal("23.0")
        assert finalize.payer_previous_held_balance == Decimal("10.0")
        assert finalize.payer_new_held_balance == Decimal("0.0")
        assert finalize.payer_previous_available_balance == Decimal("20.0")
        assert finalize.payer_new_available_balance == Decimal("23.0")
        assert finalize.receiver_previous_balance == Decimal("1.0")
        assert finalize.receiver_new_balance == Decimal("8.0")
        assert finalize.status == "settled"
        assert finalize.idempotent_replay is False

        payer_balance = await describe_wallet_balance(
            runtime_context=wallet_context,
            wallet_id=fixture.payer_wallet_id,
            coin_id=fixture.coin_id,
        )
        receiver_balance = await describe_wallet_balance(
            runtime_context=wallet_context,
            wallet_id=fixture.receiver_wallet_id,
            coin_id=fixture.coin_id,
        )
        assert payer_balance.ready is True
        assert payer_balance.balance == Decimal("23.0")
        assert payer_balance.held_balance == Decimal("0.0")
        assert payer_balance.available_balance == Decimal("23.0")
        assert receiver_balance.ready is True
        assert receiver_balance.balance == Decimal("8.0")

        replay = await finalize_smart_contract_settlement(
            runtime_context=runtime_context,
            operation_context=operation_context,
            smart_contract_id=fixture.smart_contract_id,
            permit_id=fixture.permit_id,
            reservation_id=reservation_id,
            payer_finance_entity_id=fixture.payer_finance_entity_id,
            payer_wallet_id=fixture.payer_wallet_id,
            payer_wallet_public_id=fixture.payer_wallet_public_id,
            receiver_finance_entity_id=fixture.receiver_finance_entity_id,
            receiver_wallet_id=fixture.receiver_wallet_id,
            receiver_wallet_public_id=fixture.receiver_wallet_public_id,
            coin_id=fixture.coin_id,
            final_cost=Decimal("7.0"),
            commit=True,
            publish=False,
        )
        assert replay.idempotent_replay is True
        assert replay.payer_previous_balance == Decimal("23.0")
        assert replay.payer_new_balance == Decimal("23.0")
        assert replay.payer_previous_held_balance == Decimal("0.0")
        assert replay.payer_new_held_balance == Decimal("0.0")
        assert replay.payer_previous_available_balance == Decimal("23.0")
        assert replay.payer_new_available_balance == Decimal("23.0")
        assert replay.receiver_previous_balance == Decimal("8.0")
        assert replay.receiver_new_balance == Decimal("8.0")


@pytest.mark.asyncio
async def test_smart_contract_reservation_requires_committed_contract_rate_snapshot(
    tmp_path,
) -> None:
    import aware_economy_ontology  # noqa: F401

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_economy_meta_runtime(aware_root=aware_root)
        assert runtime.context is not None
        runtime_context = resolve_economy_smart_contract_settlement_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )
        wallet_context = resolve_economy_wallet_funding_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )
        fixture = await _build_settlement_fixture(
            runtime=runtime,
            payer_initial_balance=Decimal("30.0"),
        )
        uncommitted_rate_snapshot_id = stable_rate_snapshot_id(
            price_schedule_id=uuid4(),
            snapshot_key="api-settlement-uncommitted-v1",
        )

        with pytest.raises(RuntimeError, match="RateSnapshot"):
            await prepare_smart_contract_reservation(
                runtime_context=runtime_context,
                operation_context=EconomySmartContractSettlementOperationContext(
                    actor_id=fixture.actor_id,
                ),
                smart_contract_id=fixture.smart_contract_id,
                permit_id=fixture.permit_id,
                permit_nonce=1,
                payer_finance_entity_id=fixture.payer_finance_entity_id,
                payer_wallet_id=fixture.payer_wallet_id,
                payer_wallet_public_id=fixture.payer_wallet_public_id,
                args_hash="args-hash-mismatched-schedule",
                max_cost=Decimal("10.0"),
                rate_snapshot_id=uncommitted_rate_snapshot_id,
                deadline=datetime.now(UTC) + timedelta(minutes=30),
                coin_id=fixture.coin_id,
                commit=True,
                publish=False,
            )

        payer_balance = await describe_wallet_balance(
            runtime_context=wallet_context,
            wallet_id=fixture.payer_wallet_id,
            coin_id=fixture.coin_id,
        )
        assert payer_balance.ready is True
        assert payer_balance.balance == Decimal("30.0")
        assert payer_balance.held_balance == Decimal("0")
        assert payer_balance.available_balance == Decimal("30.0")


@pytest.mark.asyncio
async def test_smart_contract_settlement_zero_cost_closes_without_wallet_delta(
    tmp_path,
) -> None:
    import aware_economy_ontology  # noqa: F401

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_economy_meta_runtime(aware_root=aware_root)
        assert runtime.context is not None
        runtime_context = resolve_economy_smart_contract_settlement_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )
        wallet_context = resolve_economy_wallet_funding_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )
        fixture = await _build_settlement_fixture(
            runtime=runtime,
            payer_initial_balance=Decimal("30.0"),
        )
        operation_context = EconomySmartContractSettlementOperationContext(
            actor_id=fixture.actor_id,
        )
        reservation_id = stable_smart_contract_reservation_id(
            smart_contract_permit_id=fixture.permit_id,
            op_nonce=1,
        )

        prepare = await prepare_smart_contract_reservation(
            runtime_context=runtime_context,
            operation_context=operation_context,
            smart_contract_id=fixture.smart_contract_id,
            permit_id=fixture.permit_id,
            permit_nonce=1,
            payer_finance_entity_id=fixture.payer_finance_entity_id,
            payer_wallet_id=fixture.payer_wallet_id,
            payer_wallet_public_id=fixture.payer_wallet_public_id,
            args_hash="args-hash-zero-cost",
            max_cost=Decimal("10.0"),
            rate_snapshot_id=fixture.rate_snapshot_id,
            deadline=datetime.now(UTC) + timedelta(minutes=30),
            coin_id=fixture.coin_id,
            commit=True,
            publish=False,
        )
        assert prepare.status == "pending"
        assert prepare.payer_held_balance == Decimal("10.0")
        assert prepare.payer_available_balance == Decimal("20.0")

        finalize = await finalize_smart_contract_settlement(
            runtime_context=runtime_context,
            operation_context=operation_context,
            smart_contract_id=fixture.smart_contract_id,
            permit_id=fixture.permit_id,
            reservation_id=reservation_id,
            payer_finance_entity_id=fixture.payer_finance_entity_id,
            payer_wallet_id=fixture.payer_wallet_id,
            payer_wallet_public_id=fixture.payer_wallet_public_id,
            receiver_finance_entity_id=fixture.receiver_finance_entity_id,
            receiver_wallet_id=fixture.receiver_wallet_id,
            receiver_wallet_public_id=fixture.receiver_wallet_public_id,
            coin_id=fixture.coin_id,
            final_cost=Decimal("0"),
            commit=True,
            publish=False,
        )
        assert finalize.transaction_id is None
        assert finalize.payer_previous_balance == Decimal("30.0")
        assert finalize.payer_new_balance == Decimal("30.0")
        assert finalize.payer_previous_held_balance == Decimal("10.0")
        assert finalize.payer_new_held_balance == Decimal("0.0")
        assert finalize.payer_previous_available_balance == Decimal("20.0")
        assert finalize.payer_new_available_balance == Decimal("30.0")
        assert finalize.receiver_previous_balance == Decimal("1.0")
        assert finalize.receiver_new_balance == Decimal("1.0")
        assert finalize.status == "settled"

        payer_balance = await describe_wallet_balance(
            runtime_context=wallet_context,
            wallet_id=fixture.payer_wallet_id,
            coin_id=fixture.coin_id,
        )
        receiver_balance = await describe_wallet_balance(
            runtime_context=wallet_context,
            wallet_id=fixture.receiver_wallet_id,
            coin_id=fixture.coin_id,
        )
        assert payer_balance.balance == Decimal("30.0")
        assert payer_balance.held_balance == Decimal("0.0")
        assert payer_balance.available_balance == Decimal("30.0")
        assert receiver_balance.balance == Decimal("1.0")


@pytest.mark.asyncio
async def test_smart_contract_reservation_prepare_fails_before_contract_mutation_when_wallet_underfunded(
    tmp_path,
) -> None:
    import aware_economy_ontology  # noqa: F401

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_economy_meta_runtime(aware_root=aware_root)
        assert runtime.context is not None
        runtime_context = resolve_economy_smart_contract_settlement_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )
        fixture = await _build_settlement_fixture(
            runtime=runtime,
            payer_initial_balance=Decimal("5.0"),
        )
        store = FSCommitStore()
        head_before = await store.head(
            branch_id=fixture.smart_contract_id,
            projection_hash=runtime_context.lanes.smart_contract_projection_hash,
        )

        with pytest.raises(
            ValueError,
            match="insufficient payer wallet available balance",
        ):
            await prepare_smart_contract_reservation(
                runtime_context=runtime_context,
                operation_context=EconomySmartContractSettlementOperationContext(
                    actor_id=fixture.actor_id,
                ),
                smart_contract_id=fixture.smart_contract_id,
                permit_id=fixture.permit_id,
                permit_nonce=1,
                payer_finance_entity_id=fixture.payer_finance_entity_id,
                payer_wallet_id=fixture.payer_wallet_id,
                payer_wallet_public_id=fixture.payer_wallet_public_id,
                args_hash="args-hash-1",
                max_cost=Decimal("10.0"),
                rate_snapshot_id=fixture.rate_snapshot_id,
                deadline=datetime.now(UTC) + timedelta(minutes=30),
                coin_id=fixture.coin_id,
                commit=True,
                publish=False,
            )

        head_after = await store.head(
            branch_id=fixture.smart_contract_id,
            projection_hash=runtime_context.lanes.smart_contract_projection_hash,
        )
        assert head_after == head_before


@pytest.mark.asyncio
async def test_smart_contract_reservation_prepare_rejects_oversubscription_after_hold(
    tmp_path,
) -> None:
    import aware_economy_ontology  # noqa: F401

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_economy_meta_runtime(aware_root=aware_root)
        assert runtime.context is not None
        runtime_context = resolve_economy_smart_contract_settlement_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )
        wallet_context = resolve_economy_wallet_funding_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )
        fixture = await _build_settlement_fixture(
            runtime=runtime,
            payer_initial_balance=Decimal("15.0"),
        )
        operation_context = EconomySmartContractSettlementOperationContext(
            actor_id=fixture.actor_id,
        )

        first = await prepare_smart_contract_reservation(
            runtime_context=runtime_context,
            operation_context=operation_context,
            smart_contract_id=fixture.smart_contract_id,
            permit_id=fixture.permit_id,
            permit_nonce=1,
            payer_finance_entity_id=fixture.payer_finance_entity_id,
            payer_wallet_id=fixture.payer_wallet_id,
            payer_wallet_public_id=fixture.payer_wallet_public_id,
            args_hash="args-hash-oversub-1",
            max_cost=Decimal("10.0"),
            rate_snapshot_id=fixture.rate_snapshot_id,
            deadline=datetime.now(UTC) + timedelta(minutes=30),
            coin_id=fixture.coin_id,
            commit=True,
            publish=False,
        )
        assert first.op_nonce == 1
        assert first.payer_balance == Decimal("15.0")
        assert first.payer_held_balance == Decimal("10.0")
        assert first.payer_available_balance == Decimal("5.0")

        with pytest.raises(
            ValueError,
            match="insufficient payer wallet available balance",
        ):
            await prepare_smart_contract_reservation(
                runtime_context=runtime_context,
                operation_context=operation_context,
                smart_contract_id=fixture.smart_contract_id,
                permit_id=fixture.permit_id,
                permit_nonce=1,
                payer_finance_entity_id=fixture.payer_finance_entity_id,
                payer_wallet_id=fixture.payer_wallet_id,
                payer_wallet_public_id=fixture.payer_wallet_public_id,
                args_hash="args-hash-oversub-2",
                max_cost=Decimal("10.0"),
                rate_snapshot_id=fixture.rate_snapshot_id,
                deadline=datetime.now(UTC) + timedelta(minutes=30),
                coin_id=fixture.coin_id,
                commit=True,
                publish=False,
            )

        payer_balance = await describe_wallet_balance(
            runtime_context=wallet_context,
            wallet_id=fixture.payer_wallet_id,
            coin_id=fixture.coin_id,
        )
        assert payer_balance.balance == Decimal("15.0")
        assert payer_balance.held_balance == Decimal("10.0")
        assert payer_balance.available_balance == Decimal("5.0")


@pytest.mark.asyncio
async def test_smart_contract_reservation_prepare_enforces_cumulative_permit_cap(
    tmp_path,
) -> None:
    import aware_economy_ontology  # noqa: F401

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_economy_meta_runtime(aware_root=aware_root)
        assert runtime.context is not None
        runtime_context = resolve_economy_smart_contract_settlement_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )
        wallet_context = resolve_economy_wallet_funding_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )
        fixture = await _build_settlement_fixture(
            runtime=runtime,
            payer_initial_balance=Decimal("100.0"),
        )
        operation_context = EconomySmartContractSettlementOperationContext(
            actor_id=fixture.actor_id,
        )

        first = await prepare_smart_contract_reservation(
            runtime_context=runtime_context,
            operation_context=operation_context,
            smart_contract_id=fixture.smart_contract_id,
            permit_id=fixture.permit_id,
            permit_nonce=1,
            payer_finance_entity_id=fixture.payer_finance_entity_id,
            payer_wallet_id=fixture.payer_wallet_id,
            payer_wallet_public_id=fixture.payer_wallet_public_id,
            args_hash="args-hash-envelope-cap-1",
            max_cost=Decimal("40.0"),
            rate_snapshot_id=fixture.rate_snapshot_id,
            deadline=datetime.now(UTC) + timedelta(minutes=30),
            coin_id=fixture.coin_id,
            commit=True,
            publish=False,
        )
        assert first.op_nonce == 1
        assert first.payer_held_balance == Decimal("40.0")
        assert first.payer_available_balance == Decimal("60.0")

        with pytest.raises(ValueError, match="spend envelope cap exceeded"):
            await prepare_smart_contract_reservation(
                runtime_context=runtime_context,
                operation_context=operation_context,
                smart_contract_id=fixture.smart_contract_id,
                permit_id=fixture.permit_id,
                permit_nonce=1,
                payer_finance_entity_id=fixture.payer_finance_entity_id,
                payer_wallet_id=fixture.payer_wallet_id,
                payer_wallet_public_id=fixture.payer_wallet_public_id,
                args_hash="args-hash-envelope-cap-2",
                max_cost=Decimal("15.0"),
                rate_snapshot_id=fixture.rate_snapshot_id,
                deadline=datetime.now(UTC) + timedelta(minutes=30),
                coin_id=fixture.coin_id,
                commit=True,
                publish=False,
            )

        payer_balance = await describe_wallet_balance(
            runtime_context=wallet_context,
            wallet_id=fixture.payer_wallet_id,
            coin_id=fixture.coin_id,
        )
        assert payer_balance.balance == Decimal("100.0")
        assert payer_balance.held_balance == Decimal("40.0")
        assert payer_balance.available_balance == Decimal("60.0")


@pytest.mark.asyncio
async def test_smart_contract_reservation_cancel_releases_hold_and_blocks_settlement(
    tmp_path,
) -> None:
    import aware_economy_ontology  # noqa: F401

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_economy_meta_runtime(aware_root=aware_root)
        assert runtime.context is not None
        runtime_context = resolve_economy_smart_contract_settlement_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )
        wallet_context = resolve_economy_wallet_funding_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )
        fixture = await _build_settlement_fixture(
            runtime=runtime,
            payer_initial_balance=Decimal("30.0"),
        )
        operation_context = EconomySmartContractSettlementOperationContext(
            actor_id=fixture.actor_id,
        )
        reservation_id = stable_smart_contract_reservation_id(
            smart_contract_permit_id=fixture.permit_id,
            op_nonce=1,
        )

        prepare = await prepare_smart_contract_reservation(
            runtime_context=runtime_context,
            operation_context=operation_context,
            smart_contract_id=fixture.smart_contract_id,
            permit_id=fixture.permit_id,
            permit_nonce=1,
            payer_finance_entity_id=fixture.payer_finance_entity_id,
            payer_wallet_id=fixture.payer_wallet_id,
            payer_wallet_public_id=fixture.payer_wallet_public_id,
            args_hash="args-hash-cancel",
            max_cost=Decimal("10.0"),
            rate_snapshot_id=fixture.rate_snapshot_id,
            deadline=datetime.now(UTC) + timedelta(minutes=30),
            coin_id=fixture.coin_id,
            commit=True,
            publish=False,
        )
        assert prepare.payer_held_balance == Decimal("10.0")

        release = await release_smart_contract_reservation(
            runtime_context=runtime_context,
            operation_context=operation_context,
            smart_contract_id=fixture.smart_contract_id,
            permit_id=fixture.permit_id,
            reservation_id=reservation_id,
            payer_finance_entity_id=fixture.payer_finance_entity_id,
            payer_wallet_id=fixture.payer_wallet_id,
            payer_wallet_public_id=fixture.payer_wallet_public_id,
            coin_id=fixture.coin_id,
            status=ReservationStatus.cancelled,
            commit=True,
            publish=False,
        )
        assert release.status == "cancelled"
        assert release.released_amount == Decimal("10.0")
        assert release.payer_previous_held_balance == Decimal("10.0")
        assert release.payer_new_held_balance == Decimal("0.0")
        assert release.payer_previous_available_balance == Decimal("20.0")
        assert release.payer_new_available_balance == Decimal("30.0")
        assert release.idempotent_replay is False

        replay = await release_smart_contract_reservation(
            runtime_context=runtime_context,
            operation_context=operation_context,
            smart_contract_id=fixture.smart_contract_id,
            permit_id=fixture.permit_id,
            reservation_id=reservation_id,
            payer_finance_entity_id=fixture.payer_finance_entity_id,
            payer_wallet_id=fixture.payer_wallet_id,
            payer_wallet_public_id=fixture.payer_wallet_public_id,
            coin_id=fixture.coin_id,
            status=ReservationStatus.cancelled,
            commit=True,
            publish=False,
        )
        assert replay.idempotent_replay is True
        assert replay.payer_new_held_balance == Decimal("0.0")
        assert replay.payer_new_available_balance == Decimal("30.0")

        payer_balance = await describe_wallet_balance(
            runtime_context=wallet_context,
            wallet_id=fixture.payer_wallet_id,
            coin_id=fixture.coin_id,
        )
        assert payer_balance.balance == Decimal("30.0")
        assert payer_balance.held_balance == Decimal("0.0")
        assert payer_balance.available_balance == Decimal("30.0")

        with pytest.raises(ValueError, match="terminal and cannot prepare settlement"):
            await finalize_smart_contract_settlement(
                runtime_context=runtime_context,
                operation_context=operation_context,
                smart_contract_id=fixture.smart_contract_id,
                permit_id=fixture.permit_id,
                reservation_id=reservation_id,
                payer_finance_entity_id=fixture.payer_finance_entity_id,
                payer_wallet_id=fixture.payer_wallet_id,
                payer_wallet_public_id=fixture.payer_wallet_public_id,
                receiver_finance_entity_id=fixture.receiver_finance_entity_id,
                receiver_wallet_id=fixture.receiver_wallet_id,
                receiver_wallet_public_id=fixture.receiver_wallet_public_id,
                coin_id=fixture.coin_id,
                final_cost=Decimal("7.0"),
                commit=True,
                publish=False,
            )


@pytest.mark.asyncio
async def test_smart_contract_reservation_expiry_releases_only_after_deadline(
    tmp_path,
) -> None:
    import aware_economy_ontology  # noqa: F401

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_economy_meta_runtime(aware_root=aware_root)
        assert runtime.context is not None
        runtime_context = resolve_economy_smart_contract_settlement_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )
        wallet_context = resolve_economy_wallet_funding_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )
        fixture = await _build_settlement_fixture(
            runtime=runtime,
            payer_initial_balance=Decimal("40.0"),
        )
        operation_context = EconomySmartContractSettlementOperationContext(
            actor_id=fixture.actor_id,
        )

        future_reservation_id = stable_smart_contract_reservation_id(
            smart_contract_permit_id=fixture.permit_id,
            op_nonce=1,
        )
        await prepare_smart_contract_reservation(
            runtime_context=runtime_context,
            operation_context=operation_context,
            smart_contract_id=fixture.smart_contract_id,
            permit_id=fixture.permit_id,
            permit_nonce=1,
            payer_finance_entity_id=fixture.payer_finance_entity_id,
            payer_wallet_id=fixture.payer_wallet_id,
            payer_wallet_public_id=fixture.payer_wallet_public_id,
            args_hash="args-hash-expiry-future",
            max_cost=Decimal("10.0"),
            rate_snapshot_id=fixture.rate_snapshot_id,
            deadline=datetime.now(UTC) + timedelta(hours=1),
            coin_id=fixture.coin_id,
            commit=True,
            publish=False,
        )

        with pytest.raises(ValueError, match="cannot expire before deadline"):
            await release_smart_contract_reservation(
                runtime_context=runtime_context,
                operation_context=operation_context,
                smart_contract_id=fixture.smart_contract_id,
                permit_id=fixture.permit_id,
                reservation_id=future_reservation_id,
                payer_finance_entity_id=fixture.payer_finance_entity_id,
                payer_wallet_id=fixture.payer_wallet_id,
                payer_wallet_public_id=fixture.payer_wallet_public_id,
                coin_id=fixture.coin_id,
                status=ReservationStatus.expired,
                commit=True,
                publish=False,
            )

        payer_balance = await describe_wallet_balance(
            runtime_context=wallet_context,
            wallet_id=fixture.payer_wallet_id,
            coin_id=fixture.coin_id,
        )
        assert payer_balance.balance == Decimal("40.0")
        assert payer_balance.held_balance == Decimal("10.0")
        assert payer_balance.available_balance == Decimal("30.0")

        expired_reservation_id = stable_smart_contract_reservation_id(
            smart_contract_permit_id=fixture.permit_id,
            op_nonce=2,
        )
        expiry_deadline = datetime.now(UTC) + timedelta(seconds=1)
        await prepare_smart_contract_reservation(
            runtime_context=runtime_context,
            operation_context=operation_context,
            smart_contract_id=fixture.smart_contract_id,
            permit_id=fixture.permit_id,
            permit_nonce=1,
            payer_finance_entity_id=fixture.payer_finance_entity_id,
            payer_wallet_id=fixture.payer_wallet_id,
            payer_wallet_public_id=fixture.payer_wallet_public_id,
            args_hash="args-hash-expiry-past",
            max_cost=Decimal("10.0"),
            rate_snapshot_id=fixture.rate_snapshot_id,
            deadline=expiry_deadline,
            coin_id=fixture.coin_id,
            commit=True,
            publish=False,
        )

        remaining_seconds = (expiry_deadline - datetime.now(UTC)).total_seconds()
        if remaining_seconds > 0:
            await asyncio.sleep(remaining_seconds + 0.05)

        release = await release_smart_contract_reservation(
            runtime_context=runtime_context,
            operation_context=operation_context,
            smart_contract_id=fixture.smart_contract_id,
            permit_id=fixture.permit_id,
            reservation_id=expired_reservation_id,
            payer_finance_entity_id=fixture.payer_finance_entity_id,
            payer_wallet_id=fixture.payer_wallet_id,
            payer_wallet_public_id=fixture.payer_wallet_public_id,
            coin_id=fixture.coin_id,
            status=ReservationStatus.expired,
            commit=True,
            publish=False,
        )
        assert release.status == "expired"
        assert release.released_amount == Decimal("10.0")
        assert release.payer_previous_held_balance == Decimal("20.0")
        assert release.payer_new_held_balance == Decimal("10.0")
        assert release.payer_previous_available_balance == Decimal("20.0")
        assert release.payer_new_available_balance == Decimal("30.0")
        assert release.idempotent_replay is False

        replay = await release_smart_contract_reservation(
            runtime_context=runtime_context,
            operation_context=operation_context,
            smart_contract_id=fixture.smart_contract_id,
            permit_id=fixture.permit_id,
            reservation_id=expired_reservation_id,
            payer_finance_entity_id=fixture.payer_finance_entity_id,
            payer_wallet_id=fixture.payer_wallet_id,
            payer_wallet_public_id=fixture.payer_wallet_public_id,
            coin_id=fixture.coin_id,
            status=ReservationStatus.expired,
            commit=True,
            publish=False,
        )
        assert replay.idempotent_replay is True
        assert replay.payer_new_held_balance == Decimal("10.0")
        assert replay.payer_new_available_balance == Decimal("30.0")

        payer_balance = await describe_wallet_balance(
            runtime_context=wallet_context,
            wallet_id=fixture.payer_wallet_id,
            coin_id=fixture.coin_id,
        )
        assert payer_balance.balance == Decimal("40.0")
        assert payer_balance.held_balance == Decimal("10.0")
        assert payer_balance.available_balance == Decimal("30.0")

        with pytest.raises(ValueError, match="terminal and cannot prepare settlement"):
            await finalize_smart_contract_settlement(
                runtime_context=runtime_context,
                operation_context=operation_context,
                smart_contract_id=fixture.smart_contract_id,
                permit_id=fixture.permit_id,
                reservation_id=expired_reservation_id,
                payer_finance_entity_id=fixture.payer_finance_entity_id,
                payer_wallet_id=fixture.payer_wallet_id,
                payer_wallet_public_id=fixture.payer_wallet_public_id,
                receiver_finance_entity_id=fixture.receiver_finance_entity_id,
                receiver_wallet_id=fixture.receiver_wallet_id,
                receiver_wallet_public_id=fixture.receiver_wallet_public_id,
                coin_id=fixture.coin_id,
                final_cost=Decimal("7.0"),
                commit=True,
                publish=False,
            )
