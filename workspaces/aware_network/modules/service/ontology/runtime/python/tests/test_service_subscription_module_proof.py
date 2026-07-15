from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_economy.handlers._generated import meta_handlers as economy_meta_handlers
from aware_economy.wallet_custody import derive_wallet_custody_material
from aware_economy.stable_ids import (
    stable_coin_id,
    stable_finance_entity_id,
    stable_smart_contract_config_id,
    stable_smart_contract_id,
    stable_wallet_id,
)
from aware_economy_ontology.coin.coin_enums import CoinType
from aware_economy_ontology.smart_contract.smart_contract_enums import (
    SmartContractType,
)
from aware_meta.runtime import (
    MetaGraphFunctionImplOwnership,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationPolicy,
    MetaGraphRuntime,
    MetaGraphRuntimeIndex,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot,
    LaneIds,
    ProofCall,
    ROOT_OBJECT_ID,
    run_meta_runtime_proof,
)
from aware_service_ontology.service.service_enums import (
    ServicePlanCycle,
    ServiceSubscriptionCycleStatus,
    ServiceSubscriptionInvoiceStatus,
    ServiceSubscriptionStatus,
)
from aware_service_ontology.stable_ids import (
    stable_service_config_id,
    stable_service_id,
    stable_service_plan_id,
    stable_service_subscription_cycle_id,
    stable_service_subscription_id,
    stable_service_subscription_invoice_id,
)
from aware_service_runtime.handlers._generated import (
    meta_handlers as service_meta_handlers,
)
from _service_runtime_test_paths import REPO_ROOT

_SERVICE_CONFIG_ROOT_CLASS_FQN = "aware_service.service.ServiceConfig"
_ECONOMY_COIN_CLASS_FQN = "aware_economy.coin.Coin"
_ECONOMY_WALLET_CLASS_FQN = "aware_economy.wallet.Wallet"
_ECONOMY_FINANCE_ENTITY_CLASS_FQN = "aware_economy.finance.FinanceEntity"
_ECONOMY_SMART_CONTRACT_CLASS_FQN = "aware_economy.smart_contract.SmartContract"
_ECONOMY_SMART_CONTRACT_CONFIG_CLASS_FQN = "aware_economy.smart_contract.SmartContractConfig"
_SERVICE_CLASS_FQN = "aware_service.service.Service"
_SERVICE_SUBSCRIPTION_CLASS_FQN = "aware_service.service.ServiceSubscription"

_ECONOMY_META_HANDLERS_ANY: Any = economy_meta_handlers
_ECONOMY_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _ECONOMY_META_HANDLERS_ANY,
)
_ECONOMY_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _ECONOMY_META_HANDLERS_ANY,
)
_SERVICE_META_HANDLERS_ANY: Any = service_meta_handlers
_SERVICE_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _SERVICE_META_HANDLERS_ANY,
)
_SERVICE_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _SERVICE_META_HANDLERS_ANY,
)


def _wallet_inputs(*, identity_id: UUID) -> tuple[str, str, str]:
    custody = derive_wallet_custody_material(identity_id=identity_id)
    return custody.address, custody.public_key, custody.private_key_encrypted


def _service_subscription_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return (
        repo_root / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_network/modules/economy/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/sdk/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_network/modules/service/ontology/structure/aware.toml",
    )


def _build_service_subscription_meta_runtime(
    repo_root: Path,
    *,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_service_subscription_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(
            _ECONOMY_META_HANDLER_MODULE,
            _SERVICE_META_HANDLER_MODULE,
        ),
        bootstrap_modules=(
            _ECONOMY_META_BOOTSTRAP_MODULE,
            _SERVICE_META_BOOTSTRAP_MODULE,
        ),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=(MetaGraphFunctionImplOwnership.authored),
        ),
    )
    assert runtime.context is not None
    return runtime


def _runtime_index(runtime: MetaGraphRuntime) -> MetaGraphRuntimeIndex:
    assert runtime.context is not None
    return runtime.context.index


def _seed_boot_environment(*, environment_id: UUID) -> tuple[UUID, UUID]:
    process_id = uuid4()
    thread_id = uuid4()
    return process_id, thread_id


@pytest.mark.asyncio
async def test_service_plan_and_subscription_module_proof(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    from aware_history.stable_ids import stable_branch_id

    with IsolatedMetaAwareRoot(tmp_path / "aware_root", persistence_backend="fs"):
        runtime = _build_service_subscription_meta_runtime(
            repo_root,
            aware_root=tmp_path / "aware_root",
        )
        idx = _runtime_index(runtime)
        required_opgs = {
            "Coin",
            "Wallet",
            "FinanceEntity",
            "SmartContract",
            "SmartContractConfig",
            "Service",
            "ServiceConfig",
            "ServicePlan",
            "ServiceSubscription",
        }
        assert required_opgs.issubset({(opg.name or "").strip() for opg in idx.opg_by_hash.values()})

        environment_id = uuid4()
        process_id, thread_id = _seed_boot_environment(
            environment_id=environment_id,
        )
        _ = process_id
        provider_lane = LaneIds(
            branch_id=stable_branch_id(environment_id=environment_id, thread_id=thread_id, key="provider"),
            actor_id=uuid4(),
        )
        consumer_lane = LaneIds(
            branch_id=stable_branch_id(environment_id=environment_id, thread_id=thread_id, key="consumer"),
            actor_id=uuid4(),
        )

        provider_identity_id = uuid4()
        provider_address, provider_public_key, provider_private_key_encrypted = _wallet_inputs(
            identity_id=provider_identity_id
        )
        provider_wallet_id = stable_wallet_id(
            public_key=provider_public_key,
            private_key_encrypted=provider_private_key_encrypted,
        )
        provider_finance_entity_id = stable_finance_entity_id(identity_id=provider_identity_id)

        consumer_identity_id = uuid4()
        consumer_address, consumer_public_key, consumer_private_key_encrypted = _wallet_inputs(
            identity_id=consumer_identity_id
        )
        consumer_wallet_id = stable_wallet_id(
            public_key=consumer_public_key,
            private_key_encrypted=consumer_private_key_encrypted,
        )
        consumer_finance_entity_id = stable_finance_entity_id(identity_id=consumer_identity_id)

        await run_meta_runtime_proof(
            runtime=runtime,
            lane=provider_lane,
            opg_name="Wallet",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_ECONOMY_WALLET_CLASS_FQN,
                    function_name="build",
                    args=[
                        provider_address,
                        provider_public_key,
                        provider_private_key_encrypted,
                    ],
                    expected_root_object_id=provider_wallet_id,
                ),
            ],
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=consumer_lane,
            opg_name="Wallet",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_ECONOMY_WALLET_CLASS_FQN,
                    function_name="build",
                    args=[
                        consumer_address,
                        consumer_public_key,
                        consumer_private_key_encrypted,
                    ],
                    expected_root_object_id=consumer_wallet_id,
                ),
            ],
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=provider_lane,
            opg_name="FinanceEntity",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_ECONOMY_FINANCE_ENTITY_CLASS_FQN,
                    function_name="build",
                    args=[provider_identity_id, provider_wallet_id],
                    expected_root_object_id=provider_finance_entity_id,
                ),
            ],
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=consumer_lane,
            opg_name="FinanceEntity",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_ECONOMY_FINANCE_ENTITY_CLASS_FQN,
                    function_name="build",
                    args=[consumer_identity_id, consumer_wallet_id],
                    expected_root_object_id=consumer_finance_entity_id,
                ),
            ],
        )

        coin_id = stable_coin_id(symbol="USD")
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=provider_lane,
            opg_name="Coin",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_ECONOMY_COIN_CLASS_FQN,
                    function_name="build",
                    args=["USD", "US Dollar", CoinType.fiat.value],
                    kwargs={"decimals": 2},
                    expected_root_object_id=coin_id,
                ),
            ],
        )

        smart_contract_config_name = "AwareMembership"
        smart_contract_config_id = stable_smart_contract_config_id(
            name=smart_contract_config_name,
            type=SmartContractType.utility.value,
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=provider_lane,
            opg_name="SmartContractConfig",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_ECONOMY_SMART_CONTRACT_CONFIG_CLASS_FQN,
                    function_name="build",
                    args=[
                        smart_contract_config_name,
                        "Membership smart contract template (v0)",
                        SmartContractType.utility.value,
                    ],
                    expected_root_object_id=smart_contract_config_id,
                ),
            ],
        )

        blockchain_address = "dev:membership"
        smart_contract_id = stable_smart_contract_id(
            smart_contract_config_id=smart_contract_config_id,
            blockchain_address=blockchain_address,
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=provider_lane,
            opg_name="SmartContract",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_ECONOMY_SMART_CONTRACT_CLASS_FQN,
                    function_name="build_via_smart_contract_config",
                    args=[smart_contract_config_id, blockchain_address],
                    expected_root_object_id=smart_contract_id,
                ),
            ],
        )

        service_config_name = "Aware Catalog"
        service_config_id = stable_service_config_id(name=service_config_name)
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=provider_lane,
            opg_name="ServiceConfig",
            root_class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                    function_name="build",
                    args=[service_config_name],
                    kwargs={"description": "Provider catalog for paid service plans"},
                    expected_root_object_id=service_config_id,
                ),
            ],
        )

        service_name = "Aware Membership"
        service_id = stable_service_id(service_config_id=service_config_id, name=service_name)
        plan_id = stable_service_plan_id(
            service_id=service_id,
            coin_id=coin_id,
            smart_contract_config_id=smart_contract_config_id,
            cycle=ServicePlanCycle.monthly.value,
            price_amount=Decimal("20"),
        )
        _, service_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=provider_lane,
            opg_name="Service",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_SERVICE_CLASS_FQN,
                    function_name="build_via_service_config",
                    kwargs={
                        "service_config_id": service_config_id,
                        "name": service_name,
                        "description": "Paid membership service",
                    },
                    expected_root_object_id=service_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_SERVICE_CLASS_FQN,
                    function_name="create_plan",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "cycle": ServicePlanCycle.monthly.value,
                        "price_amount": Decimal("20"),
                        "coin_id": coin_id,
                        "smart_contract_config_id": smart_contract_config_id,
                        "external_price_handle": "price_test_membership_monthly",
                        "policy_json": {"contract_version": "v0", "tier": "membership"},
                    },
                ),
            ],
        )
        service_assertions.expect_root(service_id)
        service_assertions.expect_instance(plan_id)
        service_assertions.expect_edge(source_id=service_id, target_id=plan_id, relationship_name="plans")
        assert service_assertions.primitive(instance_id=plan_id, field_name="cycle") == ServicePlanCycle.monthly.value
        assert service_assertions.primitive(instance_id=plan_id, field_name="price_amount") == "20"
        assert UUID(str(service_assertions.primitive(instance_id=plan_id, field_name="coin_id"))) == coin_id
        assert (
            UUID(str(service_assertions.primitive(instance_id=plan_id, field_name="smart_contract_config_id")))
            == smart_contract_config_id
        )
        assert (
            service_assertions.primitive(instance_id=plan_id, field_name="external_price_handle")
            == "price_test_membership_monthly"
        )

        subscription_id = stable_service_subscription_id(
            consumer_finance_entity_id=consumer_finance_entity_id,
            service_id=service_id,
        )
        invoice_id = stable_service_subscription_invoice_id(
            service_subscription_id=subscription_id,
            coin_id=coin_id,
            amount=Decimal("20"),
        )
        cycle_id = stable_service_subscription_cycle_id(
            service_subscription_id=subscription_id,
            cycle_number=1,
        )
        period_start = datetime(2026, 4, 1, tzinfo=UTC)
        period_end = period_start + timedelta(days=30)
        period_start_input = period_start.isoformat()
        period_end_input = period_end.isoformat()

        _, subscription_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=consumer_lane,
            opg_name="ServiceSubscription",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_SERVICE_SUBSCRIPTION_CLASS_FQN,
                    function_name="build",
                    args=[
                        consumer_finance_entity_id,
                        service_id,
                        plan_id,
                        smart_contract_id,
                    ],
                    kwargs={
                        "external_subscription_handle": "sub_test_membership_1",
                        "status": ServiceSubscriptionStatus.active.value,
                        "current_period_start": period_start_input,
                        "current_period_end": period_end_input,
                        "metadata_json": {"provider": "aware"},
                    },
                    expected_root_object_id=subscription_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_SERVICE_SUBSCRIPTION_CLASS_FQN,
                    function_name="create_invoice",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "amount": Decimal("20"),
                        "coin_id": coin_id,
                        "external_invoice_handle": "inv_test_membership_1",
                        "status": ServiceSubscriptionInvoiceStatus.open.value,
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_SERVICE_SUBSCRIPTION_CLASS_FQN,
                    function_name="create_cycle",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "cycle_number": 1,
                        "period_start": period_start_input,
                        "period_end": period_end_input,
                        "status": ServiceSubscriptionCycleStatus.pending.value,
                        "invoice_id": invoice_id,
                    },
                ),
            ],
        )

        subscription_assertions.expect_root(subscription_id)
        subscription_assertions.expect_instance(invoice_id)
        subscription_assertions.expect_instance(cycle_id)
        subscription_assertions.expect_edge(
            source_id=subscription_id,
            target_id=invoice_id,
            relationship_name="invoices",
        )
        subscription_assertions.expect_edge(
            source_id=subscription_id,
            target_id=cycle_id,
            relationship_name="cycles",
        )
        subscription_assertions.expect_edge(
            source_id=cycle_id,
            target_id=invoice_id,
            relationship_name="invoice",
        )
        assert (
            UUID(
                str(
                    subscription_assertions.primitive(
                        instance_id=subscription_id,
                        field_name="consumer_finance_entity_id",
                    )
                )
            )
            == consumer_finance_entity_id
        )
        assert UUID(str(subscription_assertions.primitive(instance_id=subscription_id, field_name="service_id"))) == (
            service_id
        )
        assert (
            UUID(str(subscription_assertions.primitive(instance_id=subscription_id, field_name="plan_id"))) == plan_id
        )
        assert (
            UUID(str(subscription_assertions.primitive(instance_id=subscription_id, field_name="contract_id")))
            == smart_contract_id
        )
        assert (
            subscription_assertions.primitive(instance_id=subscription_id, field_name="status")
            == ServiceSubscriptionStatus.active.value
        )
        assert (
            subscription_assertions.primitive(instance_id=invoice_id, field_name="status")
            == ServiceSubscriptionInvoiceStatus.open.value
        )
        assert subscription_assertions.primitive(instance_id=invoice_id, field_name="amount") == "20"
        assert UUID(str(subscription_assertions.primitive(instance_id=invoice_id, field_name="coin_id"))) == coin_id
        assert (
            subscription_assertions.primitive(instance_id=cycle_id, field_name="status")
            == ServiceSubscriptionCycleStatus.pending.value
        )
